# 🔩 Suspension Subsystem — Polarix

---

## 📋 Overview

Polarix uses a **[e.g. rocker-bogie / modified rocker-bogie]** suspension system designed for traversal over simulated Martian terrain including rocks, slopes, and loose soil. The system was fully designed in-house using SolidWorks, with structural analysis performed to validate load bearing under expected operating conditions.

The suspension maintains ground contact for all six wheels on uneven terrain without the need for active control, enabling passive articulation across obstacles up to **[X] cm** in height.

---

## 🎨 Design Philosophy

- **Passive articulation:** No actuators in the suspension linkages — simplicity and reliability over complexity.
- **Weight distribution:** Symmetric left-right rocker arrangement ensures the rover body stays level within **±[X]°** on terrain with up to **[Y]°** cross-slope.
- **Material choice:** *[e.g., 6061-T6 aluminium / 3D-printed PETG / mild steel]* was selected for *[reason: weight, machinability, cost]*.
- **Scalability:** Joint dimensions are parametric in the SolidWorks model — easy to resize for future iterations.

---

## 🛠️ CAD Files

| File | Description |
|------|-------------|
| `suspension_full_assembly.SLDASM` | Top-level assembly of the complete suspension system |
| `rocker_link_L.SLDPRT` | Left rocker arm |
| `rocker_link_R.SLDPRT` | Right rocker arm |
| `bogie_link_L.SLDPRT` | Left bogie |
| `bogie_link_R.SLDPRT` | Right bogie |
| `differential_bar.SLDPRT` | Differential/averaging bar |
| `pivot_bracket.SLDPRT` | Central pivot mount to chassis |
| `wheel_hub_interface.SLDPRT` | Wheel attachment interface |

> ⚠️ **SolidWorks Version:** `[e.g., SolidWorks 2023 SP4]`
> Files may not open correctly in older versions. Do not save in compatibility mode unless you are sure — it strips features.

---

## ⚖️ Weight

| Component | Mass (g) |
|-----------|----------|
| Full suspension assembly (excl. wheels) | *[X]* |
| Single rocker arm | *[X]* |
| Single bogie | *[X]* |
| Differential bar | *[X]* |
| **Total** | **[X] g** |

---

## 📐 Key Dimensions

| Parameter | Value |
|-----------|-------|
| Wheelbase | *[X] mm* |
| Track width | *[X] mm* |
| Ground clearance | *[X] mm* |
| Max obstacle height (theoretical) | *[X] mm* |
| Rocker arm length | *[X] mm* |
| Bogie arm length | *[X] mm* |

---

## 🧪 Simulative Analysis

### What Was Analysed

1. **Static structural analysis** — rover at rest on flat ground, full payload
2. **Worst-case load scenario** — front wheels lifted over a rock (load concentrated on rear 4 wheels)
3. **Tipping stability analysis** — CG location vs. tipping axis

### Software Used

- **SolidWorks Simulation** (FEA — Static Study)
- **SolidWorks Motion** (kinematic analysis of articulation)

### How to Replicate the Analysis

#### Step 1 — Open the Assembly
Open `suspension_full_assembly.SLDASM` in SolidWorks `[version]`.

#### Step 2 — Set Up the Static Study
1. Go to **Simulation** tab → **New Study** → **Static**
2. Apply material to all parts: *[e.g., Alloy Steel / AISI 6061-T6]*
3. Apply fixtures: Fix the chassis mounting holes (right-click → **Fixed Geometry**)
4. Apply loads:
   - Total rover weight: **[X] N** distributed across the 6 wheel contact points
   - Factor of safety: **[X]** applied (so use **[X × weight] N**)

#### Step 3 — Mesh & Run
- Mesh: **Curvature-based mesh**, max element size `[X] mm`, min `[X] mm`
- Run the study (**Run All Studies**)

#### Step 4 — Interpret Results
- **Von Mises stress plot** — check no region exceeds material yield strength (*[X] MPa*)
- **Displacement plot** — check maximum deflection is within tolerance (*[X] mm*)
- **Factor of Safety plot** — minimum FoS should be ≥ *[X]*

### Results Summary

| Analysis | Max Stress (MPa) | Max Deflection (mm) | Min FoS |
|----------|-----------------|---------------------|---------|
| Static flat ground | *[X]* | *[X]* | *[X]* |
| Front wheels lifted | *[X]* | *[X]* | *[X]* |

> 📷 Screenshots of stress and displacement plots are in the `/analysis_results/` folder.

---

## 🎥 Reference Tutorials

These YouTube tutorials were used by the team and are recommended for anyone new to SolidWorks Simulation:

| Topic | Link |
|-------|------|
| SolidWorks FEA — Static Analysis Basics | *[YouTube URL]* |
| Rocker-Bogie Suspension Design Overview | *[YouTube URL]* |
| SolidWorks Motion — Mechanism Simulation | *[YouTube URL]* |
| Mars Rover Suspension Explained (conceptual) | *[YouTube URL]* |

> 📹 **Team-recorded walkthrough video** of the full analysis process: *[Google Drive / YouTube link]*

---

## 📝 Lessons Learned

- *[e.g., Initial pivot bracket failed FEA — resolved by adding gussets and increasing wall thickness from 2mm to 4mm.]*
- *[e.g., Differential bar geometry needs to be exactly centred — even 1mm offset caused unequal load distribution in simulation.]*
- *[e.g., Printing bogie arms in PETG failed under load — switched to aluminium.]*

---

## 🔗 Related Subsystems

- **Chassis** — The suspension mounts directly to the chassis frame. See `/chassis/README.md` for interface dimensions.
- **Wheels Embedded** — Wheel motors attach at the hub interface. See `/embedded/LV_system/wheels_embedded/README.md`.
