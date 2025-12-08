# CHARACTER_PROFILES — README.md

## 1. Overview

The **character_profiles** bundle contains all baseline character configurations used throughout the Character Branch. These profiles define the initial conditions for your primary characters, including:

* psychological structures
* symbolic densities
* narrative origins
* state templates
* identity baselines
* energy and trait presets

This bundle acts as the **entry point for narrative characters**—providing a stable, structured foundation from which cognition, symbolic processing, energy systems, and evolution can begin.

Each profile is stored in JSON format, making characters portable, easy to load, and fully compatible with both simulation and narrative systems.

---

## 2. Bundle Contents

Below is the complete, verified file list for the **character_profiles** bundle:

### **Character JSON Profiles**

Each JSON file represents a full character specification.

| File            | Description             |
| --------------- | ----------------------- |
| **Amda.json**   | Profile data for Amda   |
| **Arclus.json** | Profile data for Arclus |
| **avita.json**  | Profile data for Avita  |
| **Becca.json**  | Profile data for Becca  |
| **Luvox.json**  | Profile data for Luvox  |
| **maelee.json** | Profile data for Maelee |
| **Metis.json**  | Profile data for Metis  |
| **Mirra.json**  | Profile data for Mirra  |
| **Orylex.json** | Profile data for Orylex |
| **Ulemec.json** | Profile data for Ulemec |

These JSON files typically contain:

* identity metadata
* traits
* symbolic and energetic configurations
* starting emotional or cognitive structures
* recursion seeds
* world alignment markers

---

### **Profile Management Systems**

| File                   | Description                                                         |
| ---------------------- | ------------------------------------------------------------------- |
| **state_manager.py**   | Loads, manages, updates, and applies character states               |
| **state_templates.py** | Contains reusable state templates for consistent profile generation |

These scripts allow profiles to be applied dynamically to the symbolic engine.

---

### **Execution + Packaging Files**

| File             | Description                                                |
| ---------------- | ---------------------------------------------------------- |
| **loader.py**    | Loads character profiles and prepares profile systems      |
| **harness.py**   | Provides controlled tests for profile loading and handling |
| **full_run.py**  | Executes the full profile workflow                         |
| **demo.py**      | Demonstrates profile loading and interaction               |
| **demo_init.py** | Initializes demo data for profile testing                  |
| ****init**.py**  | Makes the bundle importable                                |

---

## 3. Purpose of This Bundle

The **character_profiles** bundle defines the *starting point* for your main symbolic characters. It ensures:

* consistent initialization across simulations
* predictable structure for character identity
* compatibility with all other bundles
* a stable foundation for symbolic evolution and narrative progression

This bundle centralizes profile data, making it easy to update or expand.

---

## 4. Capabilities / Responsibilities

### **Character Initialization**

* Loads identity, cognition, symbolic structure, and baseline states from JSON
* Ensures compatibility with generators and world systems

### **State Template Application**

* Applies structured templates to unify character formatting
* Ensures consistency across characters

### **Profile Evolution**

* Profiles serve as stable roots for evolution, memory, recursion, and symbolic mutation

### **Debug + Insight Tools**

* Demo and harness scripts provide visibility into state and structure

---

## 5. Interaction with Other Bundles

This bundle interacts with:

* **character_core** → persona, observer, perception layers leverage profile data
* **character_cognition_and_traits** → traits and belief structures originate in profiles
* **character_memory** → profiles seed memory structures
* **character_symbolic** → symbolic densities and meaning fields come from profiles
* **character_evolution** → profiles define the starting point of transformation arcs

Profiles are the *root input* to almost every other system.

---

## 6. Running This Bundle

Execution tools include:

* `loader.py` — loads and initializes profile structures
* `harness.py` — tests profile validity and internal state
* `full_run.py` — executes complete profile workflows
* `demo.py` and `demo_init.py` — simple examples

Compatible with the root-level `run_all.py` orchestrator.

---

## 7. Licensing

This bundle is provided **as-is**.
Any commercial, research, or redistributive use requires written permission.

---

## 8. Intended Use Cases

* Story-driven character initialization
* Simulation agents with predefined identities
* Testing symbolic, cognitive, or energetic systems
* Large-scale character libraries

---

## 9. Ethical Use Guidance

Use only in fictional or controlled research contexts.
Do not use character profiling to analyze or simulate real individuals.

---

## 10. Contact

For licensing and inquiries:
**[ientoptic1@gmail.com](mailto:ientoptic1@gmail.com)**
