# 🔴 Polarix — Team Proboticists | IRC 2026

> **Polarix** is our Martian rover prototype, built and competed at the **International Rover Challenge (IRC) 2026** by **Team Proboticists**.

This repository is the **living knowledge base** of the entire project — containing all source code, CAD/URDF files, assembly guides, how-to documentation, and lessons learned across every technical subsystem. It is structured to ensure **full knowledge transfer** to future team members.

---

## 🧭 Repository Philosophy

> *"The knowledge gained must not be lost."*

Every subsystem has authored a comprehensive guide for their domain. The goal is that a **new member with the right background** should be able to:
1. Understand what was built and why
2. Replicate the setup from scratch
3. Avoid the mistakes we already made
4. Extend and improve the system

---

## 🗂️ Repository Structure

```
polarix/
├── README.md                        ← You are here
│
├── suspension/                      ← Rocker-bogie suspension system
│   ├── README.md
│   └── [SolidWorks parts & assemblies]
│
├── chassis/                         ← Rover frame, embedded housing, full assembly
│   ├── README.md
│   └── [SolidWorks parts & assemblies]
│
├── communication/                   ← RF/wireless communication stack
│   ├── README.md
│   └── [source code]
│
├── embedded/                        ← All embedded electronics
│   ├── README.md
│   ├── HV_system/                   ← High-voltage battery & power system
│   │   └── README.md
│   └── LV_system/                   ← Low-voltage microcontroller subsystems
│       ├── README.md
│       ├── arm_embedded/
│       ├── wheels_embedded/
│       ├── extraterrestrial_embedded/
│       ├── communication_embedded/
│       └── autonomous_embedded/
│
├── extraterrestrial/                ← Science / life-detection module
│   ├── README.md
│   └── [SolidWorks parts, assemblies, data]
│
├── autonomous/                      ← Navigation & autonomy stack
│   ├── README.md
│   └── [source code]
│
└── adaptive_payload/                ← Robotic arm system
    ├── README.md
    └── [SolidWorks parts & assemblies]
```
---

## 📌 For New Members

Start by reading this root README, then navigate to the subsystem you are joining and read its `README.md` thoroughly before touching any code or hardware. Each README will tell you what tools you need, what to set up, and what traps to avoid.

---

*Maintained by Team Proboticists.*
