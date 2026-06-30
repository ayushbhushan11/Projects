# 📡 Communication Subsystem — Polarix

---

## 📋 Overview

The communication subsystem handles all wireless data exchange between Polarix and the base station operator console. It carries joystick/command data **to** the rover and video/telemetry data **from** the rover in real time, and it handles all the logic of interconnecting different systems, dashboard design, and its code. 

I'D LIKE YOU TO SEE THAT THERE ARE MULTIPLE VERSIONS OF SAME FILE, THE MOST RECENT ONE WILL BE OF HIGHEST NUMBER AS SUFFIX, EG. INDEX7.HTML IS RECENT WJILE INDEX5.HTML IS PREVIOUS ITERATION.
THE POINT OF KEEPING ALL IS FOR DIFFRENT TASK REQUIREMENTS WHICH WILL BE MENTIONED IN THE FOLLOWING READ

| Parameter | Value |
|-----------|-------|
| Communication type | 5.8GHz primary with 865MHz secondary|
| Effective range (open field) |  1km/2km |
| Tested range at competition | 300m(maximun at udupi we got to test) |
| Latency (command → execution) | <15ms |
| Video stream resolution | radxa load and temp dependent 720p @20fps was default |
| Video stream latency | *[X] ms* |
| Telemetry data rate | *[X] Hz* |

---

## 🔧 Hardware Used

| Component | Model / Part | Quantity | Purpose |
|-----------|-------------|----------|---------|
| rover_RADXA5C | *[model]* | 1 | Main brain of coms at rover |
| *[e.g., Video RX]* | *[model]* | 1 | Receive video at base station |
| *[e.g., Telemetry radio]* | *[model]* | 2 (pair) | Bidirectional data link |
| *[e.g., Antenna, rover]* | *[model]* | *[X]* | *[type, gain]* |
| *[e.g., Antenna, base]* | *[model]* | *[X]* | *[type, gain]* |
| *[e.g., Router / AP]* | *[model]* | 1 | *[if WiFi-based]* |

---

## 💻 Software Stack

| Component | Technology |
|-----------|-----------|
| OS (rover) | Ubuntu *[version, e.g., 22.04 LTS]* |
| OS (base station) | Ubuntu *[version]* |
| Middleware | *[e.g., ROS2 Humble / custom Python / MAVLink]* |
| Video streaming | *[e.g., GStreamer / v4l2 / ffmpeg]* |
| Telemetry protocol | *[e.g., MAVLink / custom UDP / ROS2 topics]* |

---

## 🖥️ Ubuntu Setup — Rover Side

### 1. Flash Ubuntu

```bash
# Flash Ubuntu 22.04 Server to your SBC (e.g., RPi/Jetson)
# Use Raspberry Pi Imager or Balena Etcher
# Image: https://ubuntu.com/download/server/arm
```

### 2. Initial System Config

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y net-tools openssh-server git curl
sudo systemctl enable ssh
```

### 3. Install Required Packages

```bash
# Example — replace with your actual stack
sudo apt install -y python3-pip
pip3 install pyserial numpy

# If using ROS2 Humble:
sudo apt install -y ros-humble-ros-base
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### 4. Network Configuration

```bash
# Set static IP for the rover (edit netplan)
sudo nano /etc/netplan/01-network-manager-all.yaml
```

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false
      addresses: [192.168.1.10/24]   # rover IP
      gateway4: 192.168.1.1
```

```bash
sudo netplan apply
```

### 5. Configure the Radio/AP

*[Describe your specific radio configuration: channel, frequency, transmit power, SSID, etc.]*

---

## 🖥️ Base Station Setup

```bash
# Install ground control / joystick interface
sudo apt install -y joystick jstest-gtk
pip3 install pygame inputs

# If using QGroundControl or Mission Planner:
# [link and install instructions]
```

---

## 📂 Code Structure

```
communication/
├── rover_side/
│   ├── receiver.py          ← Receives commands from base station, forwards to embedded
│   ├── telemetry_sender.py  ← Sends rover status back to base station
│   └── video_stream.py      ← Starts GStreamer / video pipeline
├── base_station/
│   ├── controller.py        ← Reads joystick, sends commands to rover
│   ├── telemetry_display.py ← Receives and displays rover telemetry
│   └── video_receiver.py    ← Receives and displays video feed
└── shared/
    ├── protocol.py          ← Packet format definitions
    └── config.py            ← IP addresses, ports, constants
```

### How the Code Works

1. **Base station** reads joystick axes/buttons via `controller.py` at `[X] Hz`.
2. Commands are serialized as `[e.g., JSON / struct bytes / MAVLink packets]` and sent over UDP to `[rover IP]:[port]`.
3. **Rover's** `receiver.py` listens on that port, deserializes the command, and forwards it to the embedded system over `[e.g., serial / ROS2 topic / CAN bus]`.
4. Rover telemetry (battery %, IMU data, GPS if equipped) is sent back via `telemetry_sender.py` and displayed on the base station.
5. Video is streamed independently via `[GStreamer pipeline / FPV hardware link]`.

---

## ▶️ Running the System

### On the Rover (SSH in first)

```bash
cd ~/polarix/communication/rover_side
python3 receiver.py &
python3 telemetry_sender.py &
python3 video_stream.py &
```

### On the Base Station

```bash
cd ~/polarix/communication/base_station
python3 video_receiver.py &
python3 telemetry_display.py &
python3 controller.py   # Run this last — starts command sending
```

---

## ⚠️ Things to Keep in Mind

- **Frequency interference:** At competition sites, 5.8 GHz is often congested. Always scan the spectrum before the run. *[Tool used: e.g., `iwlist scan` or WiFi analyzer app]*
- **Antenna orientation:** Keep rover and base station antennas aligned (or use omni on rover, directional on base). Misaligned patch antennas can drop range by 80%.
- **Latency spikes:** If you see latency spikes, check for packet loss first (`ping -i 0.1 [rover_ip]`). Interference is the most common cause.
- **Firewall:** Ubuntu's UFW may block UDP. Run `sudo ufw allow [port]/udp` or disable with `sudo ufw disable` for testing.
- **Video and data on the same radio:** Can cause contention. We run video and telemetry on separate radios/channels.
- **Power:** Radio hardware is sensitive to voltage dips — always power from a clean, regulated rail. A shared rail with motors caused resets during our first test.
- **Latency budget:** Total command-to-execution latency should be under *[X] ms* for safe driving. Break it down: controller poll → network → embedded execution.

---

## 🐛 Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| No video feed | GStreamer pipeline not started / wrong IP | Check `video_stream.py` is running; verify IP in `config.py` |
| Commands not received | Firewall / wrong port | `sudo ufw allow [port]/udp`; check `config.py` on both ends |
| High latency / stuttering | RF interference or packet loss | Change channel; move antennas away from ESCs/motors |
| Radio module not detected | USB device not recognized | `dmesg | grep tty`; check `/dev/ttyUSB*` permissions |
| Rover reboots on motor start | Shared power rail noise | Separate radio power supply; add bulk capacitor |

---

## 📝 Lessons Learned

- *[e.g., UDP is fine for control; do NOT use TCP — retransmission adds unacceptable latency under interference.]*
- *[e.g., Always have a hardware kill switch on the base station that cuts power to drive motors — a lost connection while driving at full speed will damage the rover.]*
- *[e.g., Test range the day before competition, not the day of.]*

---

## 🔗 Related Subsystems

- **Embedded (Communication)** — The low-level UART/serial interface that bridges this subsystem to the motor controllers. See `/embedded/LV_system/communication_embedded/README.md`.
