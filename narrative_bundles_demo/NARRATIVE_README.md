
# Narrative Branch — Full Real Version

This branch contains the complete narrative system for the ErbeSystem, including
mythic structure, quest orchestration, narrative progression engines, arc management,
symbolic overlays, and runtime orchestration.

The modules are organized into **four major components**:

---

## 1. Engines (`engines/`)

These are the core narrative engines that drive symbolic storytelling,
mythic resonance, and structural progression:

### Narrative Engines
- **narrative_arc_engine.py** — Builds and updates multi-phase narrative arcs.
- **narrative_phase_engine.py** — Controls transitions between arc phases.
- **narrative_resolution_engine.py** — Handles resolution states and endings.
- **narrative_symbol_tracker.py** — Tracks symbolic elements entering the narrative.
- **narrative_blackboard.py** — Shared state system for narrative AI and event routing.
- **narrative_event_bus.py** — Lightweight publish/subscribe event system.
- **narrative_delta_tracker.py** — Logs changes in narrative beats and arc state.

### Mythic Engines
- **mythic_framework_engine.py** — Core mythic logic & resonance profiles.
- **mythic_overlay_engine.py** — Applies mythic overlays onto active story states.
- **mythic_cycle_engine.py** — Drives mythic recurrences and symbolic cycles.
- **mythic_archetype_inferencer.py** — Infers archetypal patterns from story data.

### Quest & Cutscene Systems
- **quest_manager.py** — Manages active quests and branching results.
- **quest_hooks.py** — Connects narrative triggers to world/character events.
- **arc_manager.py** — Oversees progression of simultaneous narrative arcs.
- **cutscene_engine.py** — Handles symbolic, generative, or scripted cutscenes.

### Special Engine
- **sophia_engine.py**
  High-level narrative synthesis engine: integrates symbolism, mythic cycles,
  thematic continuity, and global meaning formation.

---

## 2. Loaders (`loaders/`)

These modules initialize, configure, and assemble narrative subsystems:

- **narrative_loader.py** — Full system bootstrap for all narrative engines.
- **mythic_loader.py** — Initializes mythic framework and archetype mappings.
- **quest_loader.py** — Loads quest definitions and callback bindings.
- **arc_loader.py** — Builds initial arc structures from data.
- **system_loader.py** — Top-level orchestrator that ties all loaders together.

---

## 3. Runtime (`run/`)

Tools for executing and testing the narrative branch:

- **narrative_demo.py**
  Demonstrates symbolic narrative progression with sample steps.

- **narrative_run_all.py**
  Automated runner that invokes all narrative engines and loaders in sequence.

---

## 4. Data (`data/`)

Narrative configuration files and symbolic logs:

- **narrative.json** — Base story structure and arc definitions.
- **symbolic_steps.json** — Symbolic narrative step patterns.
- **symbolic_step_log.json** — Logging output of symbolic narrative evolution.
- **rules.json** — Story rules, mythic overlays, and symbolic event mappings.

---

## Summary

This branch provides:

- Full symbolic narrative generation
- Mythic pattern integration
- Dynamic quest and arc progression
- Narrative AI infrastructure
- Symbolic cycle and archetype modeling
- Data-driven storytelling structure
- Runtime orchestration tools

It is ready for licensing, packaging, or direct integration into the ErbeSystem.

---

## Version

**Narrative Branch (Full Real Version)**
Automatically generated README based on the actual contents of the branch.
