# core_world/ — README

## Purpose

The **core_world** bundle is the central coordination and execution engine of the World Branch. It defines how the world initializes, updates, stores state, communicates between subsystems, and applies recursive symbolic logic during each simulation tick.

This bundle forms the *architectural backbone* of the entire world system. All other bundles ultimately depend on `core_world` to orchestrate their behavior.

## Core Responsibilities

* Initialize world state and maintain its lifecycle
* Execute world tick cycles
* Manage communication across bundles (symbolic_physics, topology, zone_sim, effects, evolution, arcs, agency)
* Aggregate and apply symbolic results
* Store and retrieve long-term world data and memory
* Apply recursion loops and update ordering
* Provide a stable API for other systems to query or modify the world

## Included Concepts

* World manager
* State orchestration and scheduling
* Tick-based recursion controller
* World memory integration
* Transition handling and zone routing
* Global event aggregation
* Error handling and validation

## Architectural Role

`core_world` is the *root orchestrator* of the symbolic world engine. Each tick follows a defined sequence:

### 1. Pre-Update Preparation

* Load or restore world state
* Prepare zone and symbolic context
* Validate structural integrity

### 2. Symbolic Physics Evaluation

* Query **symbolic_physics** for density, resonance, noise, mirrors
* Collect symbolic conditions that affect global or zone-level change

### 3. Zone Simulation

* Dispatch local updates to **zone_sim**
* Receive micro-level transformations
* Handle boundary-crossing signals

### 4. Evolution Process

* Forward zone and symbolic results to **evolution**
* Apply long-form environmental shifts

### 5. Arcs and Agency

* Modify world direction based on:

  * **arcs** (long-term narrative/energetic forces)
  * **agency** (autonomous world-level forces)

### 6. Effects Application

* Trigger or resolve **effects** such as anomalies, pulses, or weather-like behavior

### 7. State Consolidation

* Merge all changes into unified world state
* Update world memory

### 8. Output

* Return final world state for external systems, characters, or simulations

## Integration Map

`core_world` integrates with every major world subsystem:

| Subsystem        | Purpose                                                     |
| ---------------- | ----------------------------------------------------------- |
| symbolic_physics | Supplies symbolic rules governing global and local behavior |
| topology         | Provides spatial and structural constraints                 |
| zone_sim         | Executes localized environment logic                        |
| evolution        | Applies long-term world transformations                     |
| arcs             | Provides macro-scale symbolic direction                     |
| agency           | Injects autonomous environmental forces                     |
| effects          | Handles micro-scale phenomena                               |
| tools            | Assists with debugging, validation, and introspection       |

## Typical Use Cases

* Running a full symbolic world simulation
* Coordinating multiple symbolic systems in a unified environment
* Providing world-state context to characters, narrative engines, or AI researchers
* Driving long-term environmental storytelling or symbolic ecosystems
* Serving as the heart of a recursive AGI-safe simulation framework

## Licensing

This bundle is independently licensable and governed by the **World Branch License**. All research or commercial use requires explicit written permission.

## Contact

For licensing, integration consultation, or technical support:
**[ientoptic1@gmail.com](mailto:ientoptic1@gmail.com)**
