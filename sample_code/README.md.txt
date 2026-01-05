# ERBE Sample Engine Modules (Commercial Pack)

*A collection of cognitive, systemic, and narrative micro-engines for AI and simulation developers*

This folder contains **five fully functional Python modules** extracted from the broader ERBE System. Each file demonstrates real architectural logic for modeling:

* Agent cognition
* Emotional/affective regulation
* Systemic world behavior
* Narrative event routing
* Utility-based item reasoning

These are **working engines**, not stubs. They are released under a commercial license and may be used in internal or commercial applications.

---

# Included Modules

## **1. affect_engine.py**

A full affect modeling engine implementing:

* Valence, arousal, dominance regulation
* Emotional tag dynamics (fear, calm, interest, anger, sadness)
* Novelty detection and curiosity floors
* Intent streak tracking
* Behavior biasing based on affective state

Useful for: adaptive agents, NPC behavior, psychological modeling, reinforcement-learning overlays.

---

## **2. anti_stall.py**

A cycle-break and stall-recovery engine for autonomous systems.
Features include:

* Loop detection
* Zone rotation based on contrastive energy
* "Jolt item" triggers
* Marker injection
* Prompt queue nudging
* Cooldown-controlled intervention

Useful for: open-ended agents, symbolic simulations, procedural storytelling, and systems that must avoid behavioral deadlocks.

---

## **3. items_recommender.py**

A utility-based item scoring engine.

* Evaluates inventory items against goal state changes
* Produces reason strings for explainability
* Ranks top items based on usefulness

Useful for: crafting AI, decision systems, resource sims, or any agent that chooses tools.

---

## **4. narrative_event_bus.py**

A lightweight pub/sub system for narrative or systemic events.

* Decouples event logic
* Allows dynamic module reactions
* Works for quests, triggers, UI updates, or simulation notifications

Useful for: games, interactive fiction engines, agent communication, and multi-system orchestration.

---

## **5. world_weather.py**

A systemic world-state modeling engine.
Features:

* Computes coherence and dispersion
* Detects faction front intensity
* Activates and decays tension "storms"
* Provides a high-level signal of world instability

Useful for: large simulations, strategy systems, emergent-story generators, or dynamic world balancing.

---

# Applications (Full List)

These five modules can be used far beyond the initial categories. Here is the full application list:

### **A. Games & Interactive Media**

* NPC emotional behavior
* Dynamic open-world tension systems
* Procedural narrative engines
* Survival or strategy game AI
* Companion/party member behavior
* Real-time event orchestration

### **B. AI Agents & Research**

* Cognitive modeling
* Emotion-conditioned reinforcement learning
* Utility-based tool selection
* Behavioral diversity & anti-looping systems
* Multi-agent world modeling
* Symbolic reasoning experiments

### **C. Simulation Platforms**

* Social simulations
* Emergent behavior studies
* Faction conflict modeling
* Autonomous agent environments
* Ecosystem or economy simulations

### **D. Storytelling & Narrative Systems**

* Storybeat triggering
* Quest systems
* Dynamic drama/tension modeling
* Agent-level emotional arcs
* Adaptive storytelling engines

### **E. Robotics & Decision Systems**

* Emotional heuristics for human-robot interaction
* Anti-stall logic for exploration
* Utility-based actuator/tool selection

### **F. Education, Prototyping, and Tooling**

* Teaching AI architecture
* Designing agent logic
* Prototyping cognition systems
* Building research tools quickly

### **G. Hybrid AI / Symbolic / ML Systems**

* Emotional modulation for LLM agents
* Symbolic overlays for decision-making
* Hybrid cognitive architectures

---

#  Integration Notes

All modules are:

* Python 3.x compatible
* Dependency-free
* Framework-agnostic
* Simple to import and extend

Example:

```python
from affect_engine import default_affect, appraise, affect_bias
```

---

#  Licensing

These modules are covered by **LICENSE_COMMERCIAL.md**, which allows:

* Use in private or commercial products
* Internal modification

and prohibits:

* Redistribution of the module code
* Publishing the code publicly
* Selling or sublicensing the modules

---

# ✉ Contact & Licensing

For support, commercial licensing, or integration help:
**Email:** [ientoptic1@gmail.com](mailto:ientoptic1@gmail.com)
**Author:** Eric M. Erbe

---

# End of README
