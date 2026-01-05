# engine/zone_viewer.py
from __future__ import annotations
from typing import Dict, Any, Optional, List

def _fmt_zone_line(zid: str, z: Dict[str, Any]) -> str:
    """Format one zone entry for display."""
    name = z.get("name", zid)
    ztype = z.get("type", "unknown")
    energy = f"{z.get('energy', 0.0):.2f}"
    status = z.get("status", "unknown")
    traits = ", ".join(z.get("traits", [])) if z.get("traits") else "-"
    return f"{name} [{ztype}] | Energy: {energy} | Status: {status} | Traits: {traits}"

def list_zones(world_data: Dict[str, Any], *, summary: bool = False) -> str:
    """
    Return a readable list of zones in the world.
    - summary=True: just the IDs/names
    - summary=False: full info per zone
    """
    zones: Dict[str, Dict[str, Any]] = world_data.get("zones", {})
    if not zones:
        return "No zones defined."

    # sort by zone name for deterministic output
    sorted_zones: List[tuple[str, Dict[str, Any]]] = sorted(zones.items(), key=lambda x: x[0])

    if summary:
        return "\n".join(z.get("name", zid) for zid, z in sorted_zones)

    lines = [_fmt_zone_line(zid, z) for zid, z in sorted_zones]
    return "\n".join(lines)
