"""
zone_generator.py
Unified Zone Generator
Supports BOTH:
1. Dynamic zone dictionaries (for runtime world expansion)
2. Static .py zone module generation (for modding/release packs)
"""

import os
import json
import random
from datetime import datetime

# If zone_schema exists, we use it for validation.
try:
    from zone_schema import validate_zone
except:
    def validate_zone(z): 
        return True, []


# -------------------------------------------------------
# ZONE TEMPLATES
# -------------------------------------------------------

ZONE_TEMPLATES = {
    "forest": {
        "ZONE_TYPE": "wild",
        "BASE_FEATURES": ["trees", "canopy", "wildlife"],
        "MICROFEATURES": ["roots", "ferns", "fallen_logs"],
        "WEATHER_PROFILE": {"humidity": 0.7, "wind": 0.3, "heat": 0.4},
        "SYMBOLIC_FIELDS": {"dream": 0.1, "memory": 0.2},
    },

    "ruin": {
        "ZONE_TYPE": "ruins",
        "BASE_FEATURES": ["broken_stone", "moss", "collapsed_arch"],
        "MICROFEATURES": ["dust", "shards", "dripping_water"],
        "WEATHER_PROFILE": {"humidity": 0.4, "wind": 0.5, "heat": 0.2},
        "SYMBOLIC_FIELDS": {"loss": 0.3, "echo": 0.4},
    },

    "desert": {
        "ZONE_TYPE": "desert",
        "BASE_FEATURES": ["sand_dunes", "sun_bleach", "dry_wind"],
        "MICROFEATURES": ["ripples", "glass_pebbles", "bone_shards"],
        "WEATHER_PROFILE": {"humidity": 0.1, "wind": 0.6, "heat": 0.9},
        "SYMBOLIC_FIELDS": {"silence": 0.5, "erosion": 0.3},
    },

    "dream": {
        "ZONE_TYPE": "liminal",
        "BASE_FEATURES": ["shifting_light", "echo_steps", "soft_shapes"],
        "MICROFEATURES": ["mist_threads", "glyph_particles", "folds"],
        "WEATHER_PROFILE": {"humidity": 0.5, "wind": 0.1, "heat": 0.2},
        "SYMBOLIC_FIELDS": {"dream": 0.9, "symbolic_density": 0.6},
    },

    "city": {
        "ZONE_TYPE": "urban",
        "BASE_FEATURES": ["towers", "lanes", "humming_grid"],
        "MICROFEATURES": ["trash", "ads", "cables"],
        "WEATHER_PROFILE": {"humidity": 0.6, "wind": 0.4, "heat": 0.5},
        "SYMBOLIC_FIELDS": {"memory": 0.4, "signal": 0.3},
    },

    "void": {
        "ZONE_TYPE": "void",
        "BASE_FEATURES": ["absence", "null_flow", "stillness"],
        "MICROFEATURES": ["static", "hollow", "faint_glow"],
        "WEATHER_PROFILE": {"humidity": 0.0, "wind": 0.0, "heat": 0.0},
        "SYMBOLIC_FIELDS": {"emptiness": 1.0, "rupture": 0.3},
    }
}


# -------------------------------------------------------
# CORE GENERATE FUNCTIONS
# -------------------------------------------------------

def create_zone_dict(
    zone_name,
    template=None,
    mutate=False,
    seed=None,
    metadata=None
):
    """
    Create a dynamic zone dict.
    - template: key in ZONE_TEMPLATES
    - mutate: adds random symbolic/microfeature variation
    - seed: for reproducibility
    """

    if seed is not None:
        random.seed(seed)

    if template and template in ZONE_TEMPLATES:
        base = dict(ZONE_TEMPLATES[template])
    else:
        # Default: neutral liminal zone
        base = {
            "ZONE_TYPE": "neutral",
            "BASE_FEATURES": [],
            "MICROFEATURES": [],
            "WEATHER_PROFILE": {},
            "SYMBOLIC_FIELDS": {},
        }

    # Apply mutation
    if mutate:
        if random.random() < 0.5:
            base["MICROFEATURES"].append("anomaly_" + str(random.randint(0, 999)))
        if "SYMBOLIC_FIELDS" in base:
            base["SYMBOLIC_FIELDS"]["mutation"] = random.random() * 0.3

    zone = {
        "ZONE_NAME": zone_name,
        "ZONE_TYPE": base["ZONE_TYPE"],
        "BASE_FEATURES": base["BASE_FEATURES"],
        "MICROFEATURES": base["MICROFEATURES"],
        "WEATHER_PROFILE": base["WEATHER_PROFILE"],
        "SYMBOLIC_FIELDS": base["SYMBOLIC_FIELDS"],
        "ZONE_MEMORY": {},
        "ADJACENT": [],
        "CREATED_AT": datetime.utcnow().isoformat(),
    }

    if metadata:
        zone["METADATA"] = metadata

    # Validate
    valid, errors = validate_zone(zone)
    if not valid:
        print(f"[ZoneGenerator] Validation failed for {zone_name}: {errors}")

    return zone



# -------------------------------------------------------
# WRITE A NEW .PY ZONE FILE
# -------------------------------------------------------

def write_zone_file(zone_dict, directory="generated_zones"):
    """
    Writes a zone .py file with the same format as your existing zone modules.
    """

    os.makedirs(directory, exist_ok=True)
    name = zone_dict["ZONE_NAME"].lower().replace(" ", "_")
    filepath = os.path.join(directory, f"{name}.py")

    template = f'''
# Auto-generated zone module

ZONE_NAME = "{zone_dict["ZONE_NAME"]}"
ZONE_TYPE = "{zone_dict["ZONE_TYPE"]}"

BASE_FEATURES = {json.dumps(zone_dict["BASE_FEATURES"], indent=4)}
MICROFEATURES = {json.dumps(zone_dict["MICROFEATURES"], indent=4)}
WEATHER_PROFILE = {json.dumps(zone_dict["WEATHER_PROFILE"], indent=4)}
SYMBOLIC_FIELDS = {json.dumps(zone_dict["SYMBOLIC_FIELDS"], indent=4)}

ZONE_MEMORY = {json.dumps(zone_dict.get("ZONE_MEMORY", {}), indent=4)}
ADJACENT = {json.dumps(zone_dict.get("ADJACENT", []), indent=4)}

def step(world):
    # Placeholder: zones may override runtime behavior.
    return
'''

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(template)

    return filepath



# -------------------------------------------------------
# UNIFIED API — CAN DO DICT, PY FILE, OR BOTH
# -------------------------------------------------------

def generate_zone(
    name,
    template=None,
    mutate=False,
    seed=None,
    write_file=False,
    file_directory="generated_zones",
    metadata=None
):
    """
    Unified API:
    - Always returns a zone dict.
    - Optionally creates a .py zone module.
    """

    zone_dict = create_zone_dict(
        zone_name=name,
        template=template,
        mutate=mutate,
        seed=seed,
        metadata=metadata
    )

    if write_file:
        path = write_zone_file(zone_dict, directory=file_directory)
        zone_dict["GENERATED_FILE"] = path

    return zone_dict
