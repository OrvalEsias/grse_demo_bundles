# WORLD BRANCH — README.md

*ErbeSystem World Simulation & Symbolic Environmental Engine*

---

## 1. Overview

The **World Branch** of the ErbeSystem provides a complete symbolic–recursive simulation framework for environments, zones, topology, symbolic physics, and world evolution. It governs **world-state transformation**, **symbolic density**, **recursive environmental feedback**, and **multi-zone simulation**, serving as the foundation for symbolic worlds across the system.

This branch is divided into **12 independently licensable bundles**, each representing a major subsystem.

---

## 2. Bundle Structure (12 Bundles)

```
world/
│
├── agency/
├── arcs/
├── core_world/
├── effects/
├── evolution/
├── multiverse/
├── symbolic_physics/
├── tools/
├── topology/
├── unassigned/
├── world_generators/
└── zone_sim/
```

Each folder is treated as its **own bundle**, with its own README and license.

---

## 3. Purpose of the World Branch

The World Branch governs:

* World-state initialization and evolution
* Symbolic densities and world topology
* Recursive environmental logic
* Temporal and physical symbolic systems
* Multi-zone simulation and transitions
* World-level memory, resonance, and symbolic overlays
* Environment-aware narrative and character interaction hooks

---

## 4. High-Level Responsibilities of Each Bundle

| Bundle                | Purpose                                                 |
| --------------------- | ------------------------------------------------------- |
| **agency/**           | Governs autonomous world-level agents and forces.       |
| **arcs/**             | Controls world-scale narrative or energy arcs.          |
| **core_world/**       | Core world state, update cycle, world manager.          |
| **effects/**          | Local effects: weather, anomalies, resonance events.    |
| **evolution/**        | World growth, decay, recursion, and transformation.     |
| **multiverse/**       | Parallel world layers, overlays, dimensional variants.  |
| **symbolic_physics/** | Symbolic time, density, resonance, mirror engines.      |
| **tools/**            | Utility scripts, diagnostics, world runners.            |
| **topology/**         | Spatial structure, adjacency, world graph and surfaces. |
| **unassigned/**       | Modules awaiting classification or reuse.               |
| **world_generators/** | Procedural world/zone generation.                       |
| **zone_sim/**         | Simulation of individual zones/regions.                 |

---

## 5. How These Bundles Work Together

1. **world_generators** initialize symbolic zones.
2. **topology** defines adjacency, structure, and symbolic spatial rules.
3. **symbolic_physics** applies density, resonance, mirrors, and symbolic laws.
4. **core_world** orchestrates world tick cycles and recursive updates.
5. **evolution** transforms the world over time.
6. **arcs** apply macro-scale world narrative or energy arcs.
7. **agency** handles non-character autonomous forces.
8. **effects** create local or emergent phenomena.
9. **zone_sim** handles zone-level updates.
10. **multiverse** layers alternate world states.

Together, they form a **recursive symbolic world engine**.

---

## 6. Running the World Branch

**loader.py** — Loads and validates world modules.
**harness.py** — Runs testing cycles or controlled world updates.
**demo.py / demo_init.py** — Minimal demonstrations.
**full_run.py** — Full recursive world simulation.

---

## 7. Licensing

Each bundle in this branch is independently licensable. The branch is governed by the **World Branch License** (LICENSE_WORLD.txt). The Root ErbeSystem License also applies.

---

## 8. Intended Use Cases

* Symbolic AI research
* Game world simulation
* Multi-agent symbolic worlds
* AGI simulation sandboxes
* Recursive storytelling systems
* Complex dynamical systems exploration

---

## 9. Ethical Use Guidance

This system is intended to:

* Encourage symbolic creativity and exploration
* Model symbolic relationships responsibly
* Support research that enriches human understanding

Not intended for surveillance or harmful real-world prediction.

---

## 10. Versioning & Support

Contact for licensing, research permission, or integration:
**Eric M. Erbe — [emerbe3@gmail.com](mailto:emerbe3@gmail.com)**
