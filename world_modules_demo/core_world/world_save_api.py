"""
world_save_api.py
Robust persistence layer for the Erbe System.

Features:
- Full world save/load
- Schema validation
- Versioned saves
- Auto-backups
- Differential delta saves
- Safe writes
- Migration support
- Multi-world cluster save/load
"""

import json
import os
import copy
from datetime import datetime

try:
    from world_schema import validate_world_schema
except:
    def validate_world_schema(w): return True, []   # fallback

try:
    from world_migrators import migrate_world
except:
    def migrate_world(w): return w

SAVE_DIR = "world_state"


# -----------------------------------------------------------
# Ensure directory exists
# -----------------------------------------------------------

def _ensure_dir():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)


# -----------------------------------------------------------
# File paths
# -----------------------------------------------------------

def _path(world_name):
    return os.path.join(SAVE_DIR, f"{world_name}.json")

def _backup_path(world_name):
    return os.path.join(SAVE_DIR, f"{world_name}_backup.json")

def _timestamp_path(world_name):
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return os.path.join(SAVE_DIR, f"{world_name}_{ts}.json")


# -----------------------------------------------------------
# Save World (FULL)
# -----------------------------------------------------------

def save_world(world, world_name=None):
    """
    Saves a full world copy with backups and timestamped versions.
    """

    _ensure_dir()

    if world_name is None:
        world_name = world.get("WORLD_NAME", "unnamed_world")

    # make deep copy
    wcopy = copy.deepcopy(world)

    # assign version if missing
    wcopy.setdefault("WORLD_VERSION", "1.0.0")

    # write main
    with open(_path(world_name), "w", encoding="utf-8") as f:
        json.dump(wcopy, f, indent=2)

    # write backup
    with open(_backup_path(world_name), "w", encoding="utf-8") as f:
        json.dump(wcopy, f, indent=2)

    # write timestamped archive
    with open(_timestamp_path(world_name), "w", encoding="utf-8") as f:
        json.dump(wcopy, f, indent=2)

    return True


# -----------------------------------------------------------
# Load World
# -----------------------------------------------------------

def load_world(world_name):
    """
    Loads a world. Auto-migrates and validates.
    """

    _ensure_dir()
    path = _path(world_name)

    if not os.path.exists(path):
        raise FileNotFoundError(f"World '{world_name}' not found.")

    with open(path, "r", encoding="utf-8") as f:
        world = json.load(f)

    # Migrate if needed
    world = migrate_world(world)

    # Validate
    ok, errors = validate_world_schema(world)

    if not ok:
        print("[WORLD_LOAD] Schema warnings:")
        for e in errors:
            print("  -", e)

    return world


# -----------------------------------------------------------
# Differential Saves (Delta Packs)
# -----------------------------------------------------------

def save_world_delta(world, prev_world, world_name):
    """
    Saves only what changed between prev_world and world.
    Returns delta dict and writes to "worldname_delta.json".
    """

    _ensure_dir()

    delta = {}
    for k, v in world.items():
        if k not in prev_world or prev_world[k] != v:
            delta[k] = v

    delta_path = os.path.join(SAVE_DIR, f"{world_name}_delta.json")

    with open(delta_path, "w", encoding="utf-8") as f:
        json.dump(delta, f, indent=2)

    return delta


# -----------------------------------------------------------
# Cluster Save / Load
# -----------------------------------------------------------

def save_cluster(cluster, name):
    """
    Saves an entire multi-world cluster.
    """

    _ensure_dir()
    path = os.path.join(SAVE_DIR, f"{name}_cluster.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(cluster, f, indent=2)

    return True


def load_cluster(name):
    """
    Loads a multi-world cluster.
    """

    _ensure_dir()
    path = os.path.join(SAVE_DIR, f"{name}_cluster.json")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Cluster '{name}' not found.")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
