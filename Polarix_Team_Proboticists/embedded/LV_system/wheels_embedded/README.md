# 🛞 Wheels Embedded — Drive System | Polarix

---

## 📋 Overview

This subsystem handles low-level control of all six drive wheels. It receives velocity commands from the communication stack and outputs PWM / motor signals to the drive motors through their drivers.

---

## 🔧 Hardware

| Component | Model | Quantity | Notes |
|-----------|-------|----------|-------|
| Drive motor | *[e.g., MY1016 250W BLDC / Pololu 37D gearmotor]* | 6 | *[one per wheel]* |
| Motor driver / ESC | *[e.g., Cytron MDD10A / VESC 4.12 / custom]* | 6 | *[one per motor]* |
| Microcontroller (wheels MCU) | *[e.g., STM32F446 / Arduino Mega]* | 1 | Generates PWM, reads encoders |
| Encoder (if used) | *[e.g., AS5600 / quadrature encoder on motor shaft]* | *[X]* | Optional — for closed-loop speed |
| Current sensor | *[e.g., ACS712 / INA226]* | *[X]* | Per-motor current monitoring |

### Why These Motors?

*[e.g., "MY1016 chosen for its high torque-to-weight ratio at 24V, gearbox reduction of 17:1 allowed direct wheel attachment without additional gearing. Considered brushless outrunners but maintenance/complexity was a concern for a 2-day competition."]*

### Why These Drivers?

*[e.g., "Cytron MDD10A used because it is a dual H-bridge, handles regenerative braking, and has a clear PWM+DIR interface compatible with STM32 timers. Rejected L298N due to voltage drop at high current."]*

---

## 🖥️ Platform & Setup

**MCU:** `[e.g., STM32F446RE on Nucleo board]`
**IDE:** `[e.g., STM32CubeIDE 1.14 / PlatformIO + VSCode]`
**Language:** `[C / C++ / MicroPython]`
**Toolchain:** `[e.g., arm-none-eabi-gcc 12.2]`

### Environment Setup

```bash
# Install PlatformIO (if used)
pip install platformio --break-system-packages

# Or install STM32CubeIDE from:
# https://www.st.com/en/development-tools/stm32cubeide.html

# Clone the repo and navigate here
cd polarix/embedded/LV_system/wheels_embedded

# Build
pio run

# Flash
pio run --target upload
```

---

## 📂 Code Structure

```
wheels_embedded/
├── src/
│   ├── main.c / main.cpp         ← Entry point, init, main loop
│   ├── motor_control.c           ← PWM generation, direction logic
│   ├── encoder.c                 ← Encoder reading, velocity estimation
│   └── serial_comm.c             ← Receives commands from RPi / comms stack
├── include/
│   └── config.h                  ← Pin definitions, constants
└── platformio.ini / .ioc file    ← Project config
```

---

## ⚙️ How the Code Works

1. The wheels MCU listens for velocity commands on its serial/UART interface from the main compute unit.
2. Commands arrive as `[e.g., JSON / raw struct / custom packet]` at `[X] Hz`.
3. Each wheel velocity (range: `[e.g., -100 to +100]`) is mapped to a PWM duty cycle and direction signal.
4. PWM is generated via hardware timers at `[X] kHz` to avoid audible motor whine.
5. If encoders are fitted, a PID loop runs at `[X] Hz` to maintain target wheel speed.

### Command Packet Format

```c
// Example custom packet
typedef struct {
    int8_t wheel[6];   // velocity: -100 = full reverse, +100 = full forward
    uint8_t checksum;
} WheelCommand_t;
```

---

## 🐛 Common Errors & Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| Motor spins in wrong direction | Motor wiring phase reversed | Swap any two motor wires (for brushless), or swap DIR signal polarity in code |
| MCU resets when motor starts | LV rail voltage drop | Add bulk capacitor (470µF–1000µF) at MCU VCC; separate motor driver logic supply |
| Encoder reads erratic values | Noise on encoder lines | Add 100nF capacitor between encoder signal and GND; shorten/shield encoder cables |
| One wheel unresponsive | PWM channel misconfigured | Check timer channel mapping in `config.h` and CubeMX pin assignment |
| Motors jitter at zero command | Zero-dead-zone not set | Apply a software dead-band: ignore commands in range `[-5, +5]` |
| Serial command drop-out | Baud rate mismatch / buffer overflow | Check baud rate on both sides; increase UART RX buffer in MCU config |

---

## 📝 Learnings

- *[e.g., Motor direction is not always consistent between units from the same batch — test each motor-driver pair individually and note corrections in config.h.]*
- *[e.g., Never send a sudden full-reverse command from full-forward — the current spike will reset the MCU. Implement a slew rate limiter in software.]*
- *[e.g., PID tuning: start with only P gain, then add D. I gain caused integral windup on slope climbs.]*

---

## 🔗 Related

- **HV System** — Motor drivers receive HV power from the battery. See `/embedded/HV_system/README.md`.
- **Suspension** — Wheel-motor interface geometry in `/suspension/README.md` and `/chassis/README.md`.
- **Communication Embedded** — The upstream source of wheel velocity commands.
