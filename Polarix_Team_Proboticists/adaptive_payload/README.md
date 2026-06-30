# 🦾 Adaptive Payload — Robotic Arm | Documentation

## ⚠️ Disclaimer
> The contents of this file describe the development lifecycle and the final manufactured adaptive payload subsystem for IRC 2026. It is important to note that this is not an optimal design. Major constraints were faced due to tight deadlines (~4 months of development time) and manufacturing limitations. This documentation details how the system was built under pressure and is meant to act more as a "dos and don'ts" guide rather than a strict baseline for future development.

## 📋 Overview
A 5-DOF robotic arm was developed to manipulate a wide range of objects for the RADO and IDMO missions of IRC 2026. To manage constraints and facilitate rapid maintenance, a modular and quick-swap design was prioritized, dividing the arm into three roughly independent subsystems: the End Effector, the Linkages, and the Base.

### 🎯 Problem Statement
The primary objective was to develop a control pipeline for a 5-DOF robotic arm that can execute safe and reliable motions, with collision avoidance, using a ROS2-based framework.

## 🎨 Design Philosophy
Manufacturing constraints forced us to make several suboptimal decisions. Without access to CNC machining for over 75% of the development period (and only limited aluminum CNC available late in the cycle), we could not manufacture custom metal gears or gearboxes.

### Actuation & Weight
To compensate for the lack of custom gearboxes, we resorted to using heavy motors with higher native torques. This added significant weight to the system, forcing us to aggressively manage mass and introduce remote transmission steps to keep the center of gravity low.

### Manufacturing & Materials
The use of 3D printing was maximized to bypass machining bottlenecks. All custom gears were 3D printed. For load-bearing linkage connectors, stronger filaments like PA-CF were utilized (though they came with their own limitations).

### Modularity
The arm was divided into the End Effector, Linkages, and Base to ensure that if a 3D printed part failed, it could be swapped out quickly without tearing down the entire arm.

## 📐 Key Specifications & Features

| Subsystem / Parameter | Details |
|----------------------|--------|
| Degrees of Freedom | 5 DOF |
| Maximum Reach | ~1.3 m (from shoulder to end-effector tip) |
| Shoulder Actuation | NEMA34 motor with a 10:1 planetary gearbox |
| Elbow Actuation | Rhino motor with encoder (380 kg-cm). <br> Remote-driven via a chain-sprocket mechanism. (The elbow motor was bulky, so placing it at the joint would drastically increase base torque requirements. It was moved to the base; an earlier belt-pulley design was replaced by the chain drive). |
| Base Rotation | Driven by a Johnson 60 RPM motor utilizing a worm drive mechanism to provide a high reduction ratio and prevent back-drivability. |
| Wrist Joints | Roll: Johnson 60 RPM motor<br>Pitch: Johnson 20 RPM motor |
| End Effector | Parallel claw mechanism driven by a Johnson 60 RPM motor with a worm gear drive (prevents back-drivability). Equipped with TPU pads to allow deformation for enhanced grip across varied objects. |
| Auxiliary Actuation | Provision for a solenoid actuator at the tip for pushing buttons (designed for the URC keyboard mission, though unused in IRC). |
| Vision System | Two cameras mounted: one directly on the end effector, and one on the linkage connecting the elbow and wrist joints. |

---

## 💻 Software Stack & Control Pipeline

### Control Architecture
We built a control stack using **ROS2** with `ros2_control` for low-level joint actuation and **MoveIt** for collision checking. Motion commands were generated externally in joint space and passed through MoveIt to validate safety before execution. 

### Simulation & Visualization
The robot model was defined using **URDF/Xacro**, and testing and visualization were performed in **RViz** and **Gazebo Classic**. This allowed us to verify joint limits and visual integrity before physical deployment.

### Software Constraints
Due to time and implementation complexity, inverse kinematics (IK) and full motion planning were not used in the final mission. This limited the system to joint-level control only. However, since the stack is modular, IK control can be integrated into the existing stack without requiring major architectural changes.

---

## 🛠️ Mechanical Conventions & Guidelines

### Implemented Conventions

- **Fasteners:** Allen socket head screws were used universally across the assembly to maintain uniformity and speed up tooling during maintenance.
- **Base Support:** A Lazy Susan bearing was implemented to handle the axial loads and provide smooth base rotation.
- **Shaft Anchoring:** Initially, grub screws were used to hold shafts in place within 3D printed parts, but this proved highly prone to slipping under load. The design was updated to use rigid through-holes in shafts wherever they needed to be anchored to other components.
- **Custom Gears:** All gears used in the drive systems were 3D printed in-house.

### Guidelines for Future Development

- **Fastening to 3D Prints:** When screwing directly through or into a 3D printed part, keep the applied torque low. Excessive force will easily crush the plastic infill/walls. Consider alternative methods for high-torque areas in the future.
- **Drive Tensioning:** Always ensure a dedicated tensioning mechanism is included in the design when utilizing chain drives or belt drives to account for slack and stretch over time.
- **ROS2 Distribution:** Use stable and well-documented ROS2 distributions (e.g., Humble) to avoid compatibility issues.
- **URDF Validation:** Validate URDF models thoroughly, as small inaccuracies in joint offsets or orientations can cause major execution errors during hardware-in-the-loop testing.
- **Controller Tuning:** Tune controllers early in the development cycle to avoid instability or oscillations during mission-critical testing.

## 🛠️ CAD & Development

### ⚠️ SolidWorks Version
SolidWorks 2024

---

### 📁 File System Architecture

To manage the complexity of the design, a strict hierarchical folder and naming convention was followed for all subassemblies and individual parts:

    04_AdaptivePayload/
    │
    ├── MR25_V01_AP_00_AdaptivePayloadAssembly.SLDASM
    │
    ├── 04_01_EndEffector/
    │   ├── MR25_V01_AP_EE_00_EndEffectorAssembly.SLDASM
    │   ├── MR25_V01_AP_EE_01.SLDPRT
    │   ├── MR25_V01_AP_EE_02.SLDPRT
    │   └── ... (further individual parts)
    │
    ├── 04_02_Base/
    │   ├── MR25_V01_AP_BA_00_BaseAssembly.SLDASM
    │   ├── MR25_V01_AP_BA_01.SLDPRT
    │   ├── MR25_V01_AP_BA_02.SLDPRT
    │   └── ... (further individual parts)
    │
    └── 04_03_Links/
        ├── MR25_V01_AP_LK_00_LinkAssembly.SLDASM
        ├── MR25_V01_AP_LK_01.SLDPRT
        ├── MR25_V01_AP_LK_02.SLDPRT
        └── ... (further individual parts)

---

### ⚠️ Challenges & Shortcomings

- **Late Integration:** The complete assembly could not be finalized until the day of the competition due to last-minute changes. Consequently, proper testing could not be conducted, and we were unable to identify critical pain points in advance.
- **Lack of Simulation:** Due to severe time constraints, extensive structural analysis and motion studies could not be performed prior to manufacturing.
- **Gear Reliability:** 3D printed gears, even when printed with stronger filaments, introduced significant points of failure and were prone to breaking or wearing out under load.
- **Material Flex:** While PA-CF is strong, it is flexible rather than completely rigid. Additionally, the surface finish of printed PA-CF parts was suboptimal for precision mechanical interfaces.
- **Transmission Redesign:** Initially, a belt drive was chosen for transmission. However, it was determined that the belt would snap under the required tension, forcing a shift to a chain drive just one day before the mission.
- **Chain Derailment:** The metalwork for the chain drive lacked precision, leading to alignment and orientation issues that caused the chain to frequently derail.
- **Shear Failures:** During dynamic load testing, the NEMA34 output shaft key tore directly through its mating 3D printed part (even when printed in PA-CF). This explicitly highlighted the need for machined metal parts in high-torque areas.
- **Software Integration:** URDF creation proved difficult and time-consuming due to the highly complex nature of the final CAD assembly.
- **Control Limitations:** The lack of Inverse Kinematics (IK) made operation less intuitive and more time-consuming for the operator, restricting the arm to joint-by-joint movement.

---

### 🚀 Suggestions & Ideas for Next Iteration

#### Mechanical Improvements
- **Machined Gears:** Transitioning to fully machined metal gears is an absolute necessity.
- **Custom Gearboxes:** Reduce the dependency on heavy off-the-shelf motors. Explore custom manufacturing of cycloidal gearboxes. Entirely eliminate the chain transmission system.
- **Wrist Articulation:** Implement a differential mechanism for wrist motion to improve compactness, control, and weight distribution.
- **Mass Reduction:** Aggressively reduce the overall weight of the end effector.
- **Base Actuation:** Utilize a heavy-duty turret mechanism for base rotation (this will require the use of large metal gears).
- **Claw Redesign:** Explore better claw designs using solid pads without cutouts (5-10% infill) or flexible TPU ribbed structures for passive compliance.
- **Linkage Material:** Replace heavy aluminum extrusions with carbon fiber rods to improve the strength-to-weight ratio.
- **Elbow Drive:** A worm drive can be utilized for the elbow by placing the motor directly along the link if using CNC-machined linkages.

#### Software & Control Enhancements
- **Inverse Kinematics:** Integrating IK would allow more flexible and goal-driven operation. Implement full motion planning using **MoveIt** and explore execution via **MoveIt Servo** for real-time teleoperation.
- **Improved Collision Avoidance:** Upgrade collision checking from a "full stop" approach to dynamic velocity scaling (slowing down as the arm nears self-collision).
- **Feedback Loops:** Incorporate hardware feedback mechanisms and improve controller tuning to enhance positional accuracy.
- **Real-world Robustness:** Focus on improving the system's ability to handle sensor noise, network delays, and environmental uncertainties.
- **Vision Mounting:** Use a flexible goose-neck mount for the camera to allow for easily adjustable viewing angles.
