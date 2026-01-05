"""
world_schema.py
Formal world validation layer for the Erbe System.

Ensures:
- completeness
- consistency
- correct data types
- missing required fields are detected
- correct adjacency structure
- symbolic fields are well-formed

Used by:
- world_generator_v2
- future world loaders
- world expansion
- topology generator
- balance engine
"""

REQUIRED_WORLD_KEYS = [
    "WORLD_NAME",
    "CREATED_AT",
    "ZONES",
    "ZONE_ORDER",
    "WORLD_MEMORY",
    "TICK",
]

OPTIONAL_WORLD_KEYS = [
    "SYMBOLIC_SEED",
    "METADATA",
    "GENERATED_FILE",
]

REQUIRED_ZONE_KEYS = [
    "ZONE_NAME",
    "ZONE_TYPE",
    "BASE_FEATURES",
    "MICROFEATURES",
    "WEATHER_PROFILE",
    "SYMBOLIC_FIELDS",
    "ZONE_MEMORY",
    "ADJACENT",
]

OPTIONAL_ZONE_KEYS = [
    "CREATED_AT",
    "METADATA",
    "GENERATED_FILE",
]


# ---------------------------------------------------------
# WORLD VALIDATION
# ---------------------------------------------------------

def validate_world(world):
    errors = []
    warnings = []

    # Check required keys
    for key in REQUIRED_WORLD_KEYS:
        if key not in world:
            errors.append(f"Missing required world key: {key}")

    # Check ZONES exists and is dict
    if "ZONES" in world:
        if not isinstance(world["ZONES"], dict):
            errors.append("ZONES must be a dict of zone_name -> zone_dict")
    else:
        return False, ["World missing ZONES entirely"]

    # Validate each zone
    for zname, zdata in world["ZONES"].items():
        ok, zone_errors, zone_warnings = validate_zone(zname, zdata)
        if not ok:
            errors.extend([f"[{zname}] {e}" for e in zone_errors])
        warnings.extend([f"[{zname}] {w}" for w in zone_warnings])

    # Check adjacency integrity
    ok_adj, adj_errors = validate_adjacency(world)
    if not ok_adj:
        errors.extend(adj_errors)

    # World is invalid if any errors exist
    if errors:
        return False, errors

    # Warnings do not break world generation
    return True, warnings



# ---------------------------------------------------------
# ZONE VALIDATION
# ---------------------------------------------------------

def validate_zone(zone_name, zone):
    errors = []
    warnings = []

    # Check required zone keys
    for key in REQUIRED_ZONE_KEYS:
        if key not in zone:
            errors.append(f"Missing required zone key: {key}")

    # Type checks
    if "ADJACENT" in zone and not isinstance(zone["ADJACENT"], list):
        errors.append(f"ADJACENT in {zone_name} must be a list")

    if "BASE_FEATURES" in zone and not isinstance(zone["BASE_FEATURES"], list):
        errors.append(f"BASE_FEATURES in {zone_name} must be a list")

    if "MICROFEATURES" in zone and not isinstance(zone["MICROFEATURES"], list):
        errors.append(f"MICROFEATURES in {zone_name} must be a list")

    if "SYMBOLIC_FIELDS" in zone and not isinstance(zone["SYMBOLIC_FIELDS"], dict):
        errors.append(f"SYMBOLIC_FIELDS in {zone_name} must be a dict")

    # Encourage weather usage
    if "WEATHER_PROFILE" in zone and not zone["WEATHER_PROFILE"]:
        warnings.append("WEATHER_PROFILE empty or missing")

    # This zone is invalid if any errors
    return (len(errors) == 0), errors, warnings



# ---------------------------------------------------------
# ADJACENCY / TOPOLOGY CHECK
# ---------------------------------------------------------

def validate_adjacency(world):
    """
    Verifies:
    - Every zone in ZONE_ORDER exists
    - ADJACENT only refers to valid zones
    - No missing references
    """

    errors = []
    zones = world.get("ZONES", {})
    zone_names = set(zones.keys())

    # ZONE_ORDER must exist
    if "ZONE_ORDER" not in world:
        errors.append("Missing ZONE_ORDER in world")
        return False, errors

    # Check all items in ZONE_ORDER exist in ZONES
    for z in world["ZONE_ORDER"]:
        if z not in zones:
            errors.append(f"ZONE_ORDER references missing zone: {z}")

    # Check adjacency references
    for zname, zdata in zones.items():
        adj = zdata.get("ADJACENT", [])
        for other in adj:
            if other not in zone_names:
                errors.append(f"{zname} has invalid adjacency reference: {other}")

    return (len(errors) == 0), errors
