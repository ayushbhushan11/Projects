# 🧭 Autonomous — Navigation & Autonomy Stack | Polarix

---

## 📋 Overview

The autonomous subsystem enables Polarix to navigate terrain, avoid obstacles, and complete tasks without continuous human input. It uses *[e.g., ROS2 Nav2 / custom navigation / behaviour trees]* on top of sensor data from LiDAR, camera, IMU, and GPS.

---

## 🏗️ Stack Overview

| Layer | Technology |
|-------|-----------|
| OS | Ubuntu *[version]* |
| Middleware | *[e.g., ROS2 Humble]* |
| Navigation framework | *[e.g., Nav2 / custom]* |
| Localisation | *[e.g., AMCL / Cartographer SLAM / EKF]* |
| Path planning | *[e.g., Nav2 BT Navigator / A* / DWA]* |
| Obstacle avoidance | *[e.g., Nav2 local costmap / VFH]* |
| Simulation | *[e.g., Gazebo Classic / Gazebo Harmonic / Isaac Sim]* |
| Visualisation | RViz2 |

---

## 🖥️ Setting Up the Simulation

### Prerequisites

```bash
# ROS2 Humble
sudo apt install -y ros-humble-desktop
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc

# Gazebo (Classic or Harmonic — choose based on your version)
sudo apt install -y ros-humble-gazebo-ros-pkgs
# OR for Gazebo Harmonic:
# sudo apt install -y ros-humble-ros-gz

# Nav2 full stack
sudo apt install -y ros-humble-navigation2 ros-humble-nav2-bringup

# Additional dependencies
sudo apt install -y ros-humble-slam-toolbox ros-humble-robot-localization
```

### Clone and Build

```bash
cd ~/ros2_ws/src
git clone [your-repo-url] polarix
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

### Launch Simulation

```bash
# Terminal 1 — Start Gazebo with Polarix URDF
ros2 launch polarix_simulation gazebo_launch.py

# Terminal 2 — Start Nav2 + SLAM
ros2 launch polarix_navigation navigation_launch.py use_sim_time:=True

# Terminal 3 — RViz2
ros2 launch polarix_navigation rviz_launch.py
```

> In RViz2: Set a **2D Nav Goal** to command the rover to a target position. Watch Nav2 plan and execute a path.

---

## 🤖 Running on Real Hardware

### Prerequisites (Hardware)

Ensure all sensors are connected and drivers are running — see `/embedded/LV_system/autonomous_embedded/README.md`.

### Launch on Hardware

```bash
# Terminal 1 — Start all sensors
ros2 launch autonomous_embedded sensors_bringup.launch.py

# Terminal 2 — Start navigation (use_sim_time:=False for real hardware)
ros2 launch polarix_navigation navigation_launch.py use_sim_time:=False

# Terminal 3 — Start base station teleoperation / goal sender
ros2 run polarix_navigation goal_sender.py
# OR use RViz2 on base station with remote ROS_DOMAIN_ID matching rover
```

### Setting ROS_DOMAIN_ID Across WiFi

```bash
# On rover
export ROS_DOMAIN_ID=42
# On base station
export ROS_DOMAIN_ID=42
# Both on same network → topics are shared automatically
```

---

## 📂 Code Structure

```
autonomous/
├── polarix_simulation/              ← Gazebo world and URDF
│   ├── urdf/polarix.urdf.xacro
│   ├── worlds/irc_arena.world
│   └── launch/gazebo_launch.py
├── polarix_navigation/              ← Nav2 config and launch files
│   ├── params/nav2_params.yaml
│   ├── maps/                        ← Pre-built maps (if used)
│   └── launch/navigation_launch.py
├── polarix_behaviours/              ← Custom behaviour tree nodes
│   └── src/
└── scripts/
    ├── goal_sender.py               ← Send GPS/pose goals programmatically
    └── waypoint_follower.py         ← Multi-waypoint autonomous run
```

---

## 🧪 Tuning Parameters

Key parameters in `nav2_params.yaml` that we tuned for Polarix:

| Parameter | Our Value | What It Does |
|-----------|-----------|-------------|
| `robot_radius` | *[X] m* | Inflation radius for costmap — set to actual rover width + margin |
| `max_vel_x` | *[X] m/s* | Max forward speed |
| `min_vel_x` | *[X] m/s* | Min speed (too low = jerky motion) |
| `max_vel_theta` | *[X] rad/s* | Max turning rate |
| `xy_goal_tolerance` | *[X] m* | How close to goal counts as "reached" |

---

## 🐛 Common Errors & Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Failed to create bond` with lifecycle nodes | Nav2 node crashed on startup | Check sensor topics exist: `ros2 topic list` |
| Costmap stays empty | LiDAR topic mismatch | Verify topic name in `nav2_params.yaml` matches `ros2 topic list` |
| Robot not moving after goal set | Planner found no path | Check robot is not outside map; clear costmap: `ros2 service call /clear_costmaps` |
| Simulation rover spinning in place | IMU frame orientation wrong in URDF | Fix URDF `<origin>` on IMU joint — Z-up convention |
| TF tree disconnected | `robot_state_publisher` not running | `ros2 run robot_state_publisher robot_state_publisher --ros-args -p robot_description:=$(cat urdf/polarix.urdf)` |
| GPS no localization | EKF not fusing GPS | Check `robot_localization` EKF config; verify `NavSatFix` topic quality |

---

## 📝 Learnings

- *[e.g., Nav2 is powerful but the documentation assumes a differential-drive robot. Polarix's skid-steer required overriding the velocity smoother and tuning the footprint carefully.]*
- *[e.g., Always test autonomy in simulation to near-completion before touching real hardware. Bugs that take 10 seconds to find in simulation take 2 hours on hardware.]*
- *[e.g., ROS_DOMAIN_ID collisions at competition — other teams using ROS2 on the same WiFi caused our robot to receive foreign commands. Change domain ID and test before every run.]*
- *[e.g., SLAM drift is real — after ~50m of driving, our map drifted ~0.5m. We used GPS + SLAM fusion (robot_localization EKF) to correct this.]*

---

## 🎥 Reference Tutorials

| Topic | Link |
|-------|------|
| Nav2 Getting Started Guide | *[https://nav2.org/]* |
| ROS2 Humble + Gazebo Tutorial | *[YouTube URL]* |
| SLAM Toolbox Setup | *[YouTube URL]* |
| robot_localization EKF with GPS | *[YouTube URL]* |
| Behaviour Trees in Nav2 | *[YouTube URL]* |

> 📹 **Team simulation walkthrough:** *[link]*
> 📹 **Real hardware autonomous run at IRC 2026:** *[link]*

---

## 🔗 Related Subsystems

- **Autonomous Embedded** — Sensor drivers that feed this stack. See `/embedded/LV_system/autonomous_embedded/README.md`.
- **Communication** — Remote goal sending from base station uses the communication stack.
