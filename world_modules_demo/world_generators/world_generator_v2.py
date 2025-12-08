"""
world_generator_v2.py
Upgraded procedural world generator for the Erbe System.
Produces:
- complete world dict
- zone dictionaries via the Zone Generator
- optional saved world JSON file

Integrates with:
- topology_viewer
- terrain_noise
- zone_generator
- world_schema (future)
- balance engine (future)
"""

import os
import json
import random
from datetime import datetime

# Zone Generator
from zone_generator import generate_zone

# Optional world schema validation (future module)
try:
    from world_schema import validate_world
except:
    def validate_world(w): return True, []

# Optional terrain noise
try:
    from terrian_noise import step as terrain_step
except:
    terrain_step = None


# ---------------------------------------------------------
# WORLD TEMPLATE PRESETS
# ---------------------------------------------------------

WORLD_TEMPLATES = {
    "default": {
        "world_size": 6,
        "zone_templates": ["forest", "ruin", "city", "desert", "dream", "void"],
        "symbolic_seed": {"dream": 0.2, "memory": 0.3},
    },

    "dreamscape": {
        "world_size": 8,
        "zone_templates": ["dream", "void", "ruin"],
        "symbolic_seed": {"dream": 0.6, "symbolic_density": 0.4},
    },

    "desolation": {
        "world_size": 10,
        "zone_templates": ["desert", "void"],
        "symbolic_seed": {"erosion": 0.5, "silence": 0.4},
    },

    "urban": {
        "world_size": 7,
        "zone_templates": ["city", "ruin", "forest"],
        "symbolic_seed": {"signal": 0.5, "memory": 0.3},
    },
}


# ---------------------------------------------------------
# INTERNAL UTILS
# ---------------------------------------------------------

def _build_adjacency(zone_names):
    """Simple ring adjacency for now.
    Future: topology generator replaces this.
    """
    adjacency = {z: [] for z in zone_names}

    for i, z in enumerate(zone_names):
        left = zone_names[(i - 1) % len(zone_names)]
        right = zone_names[(i + 1) % len(zone_names)]

        adjacency[z].append(left)
        adjacency[z].append(right)

    return adjacency



# ---------------------------------------------------------
# MAIN WORLD GENERATION LOGIC
# ---------------------------------------------------------

def generate_world_dict(
    world_name,
    template="default",
    mutate_zones=True,
    seed=None,
    include_terrain=True,
    include_adjacency=True,
    metadata=None
):
    """
    Generates a full world dictionary using:
    - Procedural zones
    - Templates
    - Optional mutation
    - Optional terrain noise
    - Optional adjacency structure
    """

    if seed is not None:
        random.seed(seed)

    # Load template settings
    if template not in WORLD_TEMPLATES:
        raise ValueError(f"Unknown world template '{template}'")

    t = WORLD_TEMPLATES[template]
    world_size = t["world_size"]
    zone_templates = t["zone_templates"]
    symbolic_seed = t["symbolic_seed"]

    # ------------------------------
    # Generate Zones
    # ------------------------------
    zones = {}
    zone_names = []

    for i in range(world_size):
        zone_name = f"{world_name}_zone_{i+1}"
        zone_template = random.choice(zone_templates)

        zone_dict = generate_zone(
            name=zone_name,
            template=zone_template,
            mutate=mutate_zones,
        )

        # symbolic seed integration
        for k, v in symbolic_seed.items():
            if "SYMBOLIC_FIELDS" not in zone_dict:
                zone_dict["SYMBOLIC_FIELDS"] = {}
            zone_dict["SYMBOLIC_FIELDS"][k] = zone_dict["SYMBOLIC_FIELDS"].get(k, 0) + v

        zones[zone_name] = zone_dict
        zone_names.append(zone_name)

    # ------------------------------
    # Build World Structure
    # ------------------------------
    world = {
        "WORLD_NAME": world_name,
        "CREATED_AT": datetime.utcnow().isoformat(),
        "ZONES": zones,
        "ZONE_ORDER": zone_names,
        "SYMBOLIC_SEED": symbolic_seed,
        "METADATA": metadata or {},
        "WORLD_MEMORY": {},
        "TICK": 0,
    }

    # ------------------------------
    # Optional Adjacency
    # ------------------------------
    if include_adjacency:
        adjacency = _build_adjacency(zone_names)
        for z, neighbors in adjacency.items():
            world["ZONES"][z]["ADJACENT"] = neighbors

    # ------------------------------
    # Optional Terrain Noise
    # ------------------------------
    if include_terrain and terrain_step:
        for _ in range(3):  # 3 baseline terrain steps
            terrain_step(world)

    # ------------------------------
    # Validation
    # ------------------------------
    valid, errors = validate_world(world)
    if not valid:
        print(f"[WorldGenerator] Validation failed: {errors}")

    return world



# ---------------------------------------------------------
# SAVE TO FILE
# ---------------------------------------------------------

def write_world_file(world_dict, directory="generated_worlds"):
    os.makedirs(directory, exist_ok=True)
    name = world_dict["WORLD_NAME"].lower().replace(" ", "_")
    path = os.path.join(directory, f"{name}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(world_dict, f, indent=4)

    return path



# ---------------------------------------------------------
# UNIFIED API
# ---------------------------------------------------------

def generate_world(
    world_name,
    template="default",
    mutate_zones=True,
    seed=None,
    write_file=False,
    file_directory="generated_worlds",
    metadata=None,
):
    """
    Returns a world dict.
    Optionally saves it to a JSON file.
    """

    world_dict = generate_world_dict(
        world_name=world_name,
        template=template,
        mutate_zones=mutate_zones,
        seed=seed,
        metadata=metadata
    )

    if write_file:
        path = write_world_file(world_dict, directory=file_directory)
        world_dict["GENERATED_FILE"] = path

    return world_dict
