# 🔋 HV System — High Voltage Power Subsystem | Polarix

---

## ⚠️ SAFETY FIRST — READ THIS BEFORE ANYTHING ELSE

> 🔴 **This system operates at potentially lethal voltages. Treat all HV wiring as live at all times unless the battery is physically disconnected AND you have verified voltage is zero with a multimeter.**

Key rules:
- **Never** connect or disconnect HV wiring while motors are running or ESCs are powered.
- **Never** short the battery terminals — even momentarily. Peak current can weld metal and cause fire.
- **Always** use a pre-charge resistor or slow-blow fuse when connecting to capacitive loads.
- **Always** wear insulated gloves when handling the battery pack outside its enclosure.
- **Never** leave a LiPo charging unattended.
- **Store LiPo** at storage voltage (~3.8V/cell) if not using for more than 48 hours.

---

## 📋 System Overview

| Parameter | Value |
|-----------|-------|
| Battery chemistry | *[e.g., LiPo 4S / 6S]* |
| Nominal voltage | *[e.g., 14.8V / 22.2V]* |
| Full charge voltage | *[e.g., 16.8V / 25.2V]* |
| Capacity | *[e.g., 10,000 mAh]* |
| Peak discharge current | *[e.g., 200A (20C × 10Ah)]* |
| Continuous discharge current | *[e.g., 100A]* |
| Battery connector type | *[e.g., XT90 / AS150]* |
| BMS used | *[model, or "none — fuse only"]* |

---

## 🔌 Power Distribution Architecture

```
[Battery Pack]
     │
     ├──[Main Fuse: X A slow-blow]
     │
     ├──[Main Power Switch / Emergency Cutoff]
     │
     ├──[HV Bus Bar / Distribution Board]
     │       │
     │       ├── ESC 1 (Front-Left wheel)
     │       ├── ESC 2 (Front-Right wheel)
     │       ├── ESC 3 (Mid-Left wheel)
     │       ├── ESC 4 (Mid-Right wheel)
     │       ├── ESC 5 (Rear-Left wheel)
     │       └── ESC 6 (Rear-Right wheel)
     │
     └──[Buck Converter → LV Rail (5V/12V)]
             │
             └── All LV electronics (RPi, microcontrollers, etc.)
```

---

## ⚙️ Buck Converter Setup

| Parameter | Value |
|-----------|-------|
| Buck converter model | *[e.g., LM2596 module / Pololu D36V50F5 / custom]* |
| Input voltage range | *[X]V – *[X]V* |
| Output voltage | *[e.g., 5V / 12V]* |
| Output current (continuous) | *[X] A* |
| Output current (peak) | *[X] A* |
| Efficiency at nominal load | *[X]%* |

### How the Buck Was Set Up

1. *[e.g., Set output voltage via trim potentiometer — turn clockwise to increase, counterclockwise to decrease. Measure output with multimeter before connecting any load.]*
2. *[e.g., Add a 100µF 25V capacitor across the output terminals to smooth transient load steps from SBCs booting.]*
3. *[e.g., Heatsink is mandatory — at X A continuous the converter reaches Xˢ°C without it.]*

---

## 🏎️ ESCs (Electronic Speed Controllers)

| Parameter | Value |
|-----------|-------|
| ESC model | *[model name]* |
| Input voltage range | *[X]V – *[X]V* |
| Continuous current per ESC | *[X] A* |
| Peak current per ESC | *[X] A* |
| Communication protocol | *[e.g., PWM / UART / CAN]* |
| Motor type supported | *[BLDC / DC brushed]* |

### ESC Calibration

```
1. Power on ESC with no motor load
2. Send maximum throttle signal (2000µs PWM)
3. Wait for beep sequence
4. Send minimum throttle (1000µs PWM)
5. Wait for confirmation beep
6. ESC is calibrated
```

---

## 🔋 Runtime Estimates

| Scenario | Estimated Current Draw | Runtime |
|----------|----------------------|---------|
| Idle (stationary, electronics only) | *[X] A* | *[X] min* |
| Slow driving on flat ground | *[X] A* | *[X] min* |
| Aggressive driving, rough terrain | *[X] A* | *[X] min* |
| Peak (all wheels stalled simultaneously) | *[X] A* | *[seconds — should not sustain this]* |

> ⚠️ **Never fully discharge a LiPo.** Stop operations when cell voltage reaches **3.5V per cell** (use telemetry alert). Discharge below 3.0V/cell permanently damages cells and is a fire risk.

---

## 🧪 Measured Peaks

| Test Condition | Measured Peak Current |
|---------------|----------------------|
| Full throttle all 6 wheels on flat | *[X] A* |
| Wheels stalled against obstacle | *[X] A* |
| Single wheel stall test | *[X] A* |

> 🔬 Measurement method: *[e.g., ACS758 Hall-effect current sensor inline with main positive lead, logged via Arduino at 100Hz]*

---

## 🔧 Wiring & Assembly Notes

- All HV wiring is **10 AWG** silicone-insulated wire (orange sleeving).
- All LV wiring is **22 AWG** or thinner.
- Solder all connectors — crimped HV connections are not acceptable; they heat up and fail.
- Heatshrink all solder joints. No exposed conductors.
- Route HV and LV wiring on opposite sides of the chassis bay — do not bundle together.
- Label every wire at both ends.

---

## 📝 Lessons Learned

> These are real mistakes. Read them. They are expensive.

- *[e.g., We omitted a pre-charge circuit on first build. Connecting to capacitive ESC input caused a spark that welded the XT90 connector. Always add a pre-charge resistor (e.g., 100Ω 10W) or use an AS150 anti-spark connector.]*
- *[e.g., Running LV power from the same rail as ESC logic power caused voltage spikes when motors reversed. Separate your LV logic supply with an LC filter or dedicated isolated buck.]*
- *[e.g., Our 30A fuse was too low — it blew during a rock climb. Recalculated max current and upsized to 60A.]*
- *[e.g., LiPo bag is not optional — store and charge the pack inside a fireproof bag at all times.]*

---

## 🔗 Related Subsystems

- **LV System** — Buck converter output feeds all LV electronics. See `/embedded/LV_system/README.md`.
- **Chassis** — Battery and HV distribution hardware mounts to the base plate. See `/chassis/README.md`.
