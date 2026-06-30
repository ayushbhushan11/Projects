# 🏗️ Chassis Subsystem — Polarix

---

## 📋 Overview

The chassis is the structural backbone of Polarix. It provides mounting points for all six subsystems — suspension, electronics, science module, arm, and communication hardware — while keeping total rover weight within IRC regulations. The design prioritises rigidity, low centre of gravity, and easy access to internal electronics for maintenance.

---

## 🎨 Design Philosophy

- **Low CG:** Battery and heavy components placed as low as possible in the chassis bay to improve tipping stability.
- **Modular access panels:** Side and top panels made of acrylic and polyvinyl are screwed with the panel holders— allowing electronic components and trays to be swapped without disassembly.
- **Embedded housing integration:** All PCBs, wiring harnesses, and compute units have dedicated mounting trays modelled in CAD — no "improvised" cable management.
- **Material:** The chassis is fabricated using Aluminium 6061–T6 extrusions, selected for their strength, durability, and ease of manufacturing. With a yield strength of approximately 275 MPa, 6061–T6 provides an excellent strength-to-weight ratio, allowing the structure to support loads without adding unnecessary mass. Its natural corrosion resistance ensures reliable performance in outdoor conditions, while its good machinability allows the extrusions to be easily cut, drilled, and assembled with precise tolerances. The use of standardized extrusion profiles also supports modular construction, enabling quick subsystem integration and easier repairs during testing. Additionally, the stiffness and vibration resistance of 6061–T6 help protect sensitive electronics and payloads mounted on the rover, making it a lightweight yet robust choice for the chassis.

---

## 📐 Dimensions

| Parameter | Value |
|-----------|-------|
| Overall length | *890 mm* |
| Overall width | *750 mm* |
| Overall height (chassis body only) | *200 mm* |
| Overall height (with suspension, no antennas) | *[X] mm* |
| Ground clearance | *[X] mm* |

---

## 🛠️ CAD Files

| File | Description |
|------|-------------|
| `chassis_full_assembly.SLDASM` | Complete chassis assembly including embedded housing and panel covers |
| `main_frame.SLDPRT` | Primary structural frame |
| `top_panel.SLDPRT` | Removable top access panel |
| `side_panel_L.SLDPRT` | Left side panel |
| `side_panel_R.SLDPRT` | Right side panel |
| `base_plate.SLDPRT` | Floor plate with battery tray cutouts |
| `suspension_mount_bracket.SLDPRT` | Suspension attachment interface (see suspension subsystem for mating dimensions) |
| `embedded_tray_main.SLDPRT` | Embedded electronics mounting tray — main compute |
| `embedded_tray_motor_drivers.SLDPRT` | Motor driver mounting tray |
| `embedded_tray_comms.SLDPRT` | Communication hardware mounting tray |
| `arm_base_interface.SLDPRT` | Robotic arm mounting plate |
| `science_module_bay.SLDPRT` | Science module bay cutout and mounting points |
| `antenna_mast_base.SLDPRT` | Antenna mast mount |

> ⚠️ **SolidWorks Version Used:** 2019

---

## ⚖️ Weight

| Component | Mass (g) |
|-----------|----------|
| Main frame | *[X]* |
| All panels | *[X]* |
| All embedded trays & hardware | *[X]* |
| Fasteners | *[X]* |
| **Total chassis assembly** | **[X] g** |

---

## 🔌 Embedded Housing Layout

The embedded electronics are organized into **zones** inside the chassis bay. Refer to `embedded_tray_*.SLDPRT` files for exact positions.

```
┌─────────────────────────────────────────────┐
│  [FRONT]                                    │
│  ┌─────────────┐   ┌────────────────────┐  │
│  │ Compute SBC │   │ Communication HW   │  │
│  │ (e.g. RPi5) │   │ (RF modules, etc.) │  │
│  └─────────────┘   └────────────────────┘  │
│  ┌─────────────────────────────────────┐   │
│  │      Motor Drivers (6×)             │   │
│  └─────────────────────────────────────┘   │
│  ┌────────────┐ ┌───────────────────────┐  │
│  │  HV System │ │ LV Power Distribution │  │
│  │ (battery)  │ │ (BEC, regulators)     │  │
│  └────────────┘ └───────────────────────┘  │
│  [REAR]                                     │
└─────────────────────────────────────────────┘
```

---

## 🧪 Simulative Analysis

### What Was Analysed

**Static load test** — full rover weight distributed across suspension mounting points


### Software Used

- **SolidWorks Simulation** (FEA — Static Study)

### How to Replicate

1. Open `chassis_full_assembly.SLDASM` in SolidWorks `[version]`
2. **Simulation → New Study → Static**
3. Apply material: *6061-T6 Alloy (in this case)*
4. Fix the 6 wheel-ground contact points
5. Apply **[X] N** downward load at CG location (use remote load/mass)
6. Mesh: Curvature-based, max element `[X] mm`
7. Run and inspect Von Mises stress + displacement

### Results

| Scenario | Max Stress (MPa) | Max Deflection (mm) | Min FoS |
|----------|-----------------|---------------------|---------|
| Static full load | *38.77* | *0.4126* | *7* |


<img width="1280" height="679" alt="image" src="https://github.com/user-attachments/assets/2c279639-f207-4dc3-8167-092198add815" /> <img width="1280" height="676" alt="image" src="https://github.com/user-attachments/assets/09d99d0c-d98a-4226-a180-fcd632a12166" />



---

## 🎥 Reference Tutorials

| Topic | Link |
|-------|------|
| SolidWorks Weldments & Frame Design | *https://www.youtube.com/watch?v=4W9mKf3DaQE&list=PLRhna5_X7uWuNR4bC0suezLHJtaHnvMfj* |
| SolidWorks FEA on Structural Frames | *https://www.youtube.com/watch?v=EeFhmiaRYLA&list=PL9-f9hWLZS60k6hX8oQucPlYgXzfFNHpK* |

> 📹 **Team walkthrough video:** *[link]*

---

## 📝 Lessons Learned

The fabrication journey involved several practical challenges, from machining inaccuracies to electronics integration issues, but each iteration provided valuable lessons in manufacturing precision, tolerance selection, and efficient subsystem packaging. 

**Challenges Faced During Fabrication:** 

- **Improper cutting setup:** Initially, only a Bosch cutter was available without a proper fixture for cutting aluminium extrusions. A custom plywood jig had to be built to perform the cuts.

- **Uneven cut surfaces:** The initial cuts were not perfectly flat or dimensionally accurate, requiring re-machining of the extrusions using a milling machine at CWISS with 0.01 mm tolerance.

- **Multiple screw sizes in electronics mounts:** Different embedded components required screw sizes such as M3, M2.5, M2, and 1.8 mm, which complicated tray design and mounting standardization.

- **Access requirements for certain components:** Modules like the STM32 Blackpill required access to pins from both the top and bottom sides, requiring redesign of the mounting structure.

- **Improper tolerance in mounts:** Some components were either too loose or too tight due to incorrect tolerances. Through iteration, 0.4 mm clearance for M3 screw holes and 0.2 mm tolerance for snug-fit mounts were adopted.

- **Inefficient component placement:** The initial electronics layout did not utilize space effectively, leading to redesign and implementation of vertical stacking for modules like the boost converter and Cytron driver.

- **Offset errors in tray mounting holes:** Some tray holes had incorrect offsets due to measurement errors, which required redesign and re-alignment.

- **Battery tray design error:** Incorrect battery tray dimensions affected the placement of other trays, forcing redesign of multiple electronics trays.

- **Time constraint workaround:** Due to the tight competition timeline, the battery tray alignment was corrected by adding new holes using a soldering iron instead of remanufacturing the tray.

---

## 🔗 Related Subsystems

- **Suspension** — Mounting interface defined in `suspension_mount_bracket.SLDPRT`. Cross-reference with `/suspension/README.md`.
- **Embedded (HV + LV)** — All embedded trays map to `/embedded/README.md`.
- **Adaptive Payload** — Arm mounts to `arm_base_interface.SLDPRT`.
