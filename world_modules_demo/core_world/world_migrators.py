# engine/world_migrators.py

from __future__ import annotations
from typing import Dict, List, Tuple

__all__ = ["migrate_world"]

# Map version string -> migration function
_MIGRATIONS: Dict[str, callable] = {}

def migrate_world(world: dict, target: str = "1.0.0") -> Tuple[dict, List[str]]:
    """
    Upgrade a world dict to the target schema version.

    Parameters
    ----------
    world : dict
        The game world state to migrate (mutated in place).
    target : str
        Target version string, default "1.0.0".

    Returns
    -------
    Tuple[dict, list[str]]
        The migrated world dict and a list of human-readable migration notes.
    """
    if not isinstance(world, dict):
        raise TypeError("world must be a dict")

    current_version = str(world.get("_schema_version", "0.0.0"))
    notes: List[str] = []

    if current_version == target:
        notes.append(f"World already at target version {target}")
        return world, notes

    # Step through known migrations in sorted order
    for ver, func in sorted(_MIGRATIONS.items()):
        if _version_lt(current_version, ver) and _version_le(ver, target):
            try:
                world, msg = func(world)
                if msg:
                    notes.append(f"[{ver}] {msg}")
                world["_schema_version"] = ver
                current_version = ver
            except Exception as e:
                notes.append(f"[{ver}] Migration failed: {e}")
                break

    # Ensure final version matches target
    if current_version != target:
        notes.append(f"Reached version {current_version}, not target {target}")
    else:
        notes.append(f"Migration complete to {target}")

    return world, notes


# ===== Helpers =====
def _version_tuple(v: str) -> tuple[int, int, int]:
    try:
        return tuple(int(x) for x in v.split("."))
    except Exception:
        return (0, 0, 0)

def _version_lt(a: str, b: str) -> bool:
    return _version_tuple(a) < _version_tuple(b)

def _version_le(a: str, b: str) -> bool:
    return _version_tuple(a) <= _version_tuple(b)


# ===== Example migration registrations =====
def _migrate_to_1_0_0(world: dict) -> Tuple[dict, str]:
    """
    Example migration: ensure faction_presence exists, add default rules key to zones.
    """
    world.setdefault("faction_presence", {})
    for z in (world.get("zones") or {}).values():
        z.setdefault("rules", {})
    return world, "Initialized faction_presence and ensured zone.rules."

_MIGRATIONS["1.0.0"] = _migrate_to_1_0_0
