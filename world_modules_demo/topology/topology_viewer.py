# engine/topology_viewer.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

WORLD_FILE = Path("world_state/world.json")


def _safe_list(x: Any) -> List[Any]:
    return x if isinstance(x, list) else []


def _safe_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _load_world_from_disk() -> Dict[str, Any]:
    if not WORLD_FILE.exists() or WORLD_FILE.is_dir():
        return {}
    try:
        with WORLD_FILE.open("r", encoding="utf-8") as f:
            return _safe_dict(json.load(f))
    except Exception:
        return {}


def get_topological_summary(world_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Summarize symbolic topology from the provided world dict (preferred),
    or from world_state/world.json if not provided.

    Returns at least these keys for backward-compat with app.py:
      - active_markers: Dict[str, Any]
      - clusters: Dict[str, Any]
      - density_log: List[float]

    Also includes a small 'stats' block with latest density & simple trend.
    """
    world = _safe_dict(world_data) or _load_world_from_disk()

    active_markers = _safe_dict(world.get("active_markers"))
    clusters = _safe_dict(world.get("clusters"))
    density_log_full = _safe_list(world.get("density_log"))

    # keep it light: just the last 20 values
    density_log = density_log_full[-20:] if density_log_full else []

    # tiny stats helper
    latest = float(density_log[-1]) if density_log else 0.0
    trend = "flat"
    if len(density_log) >= 2:
        delta = density_log[-1] - density_log[-2]
        if delta > 1e-9:
            trend = "up"
        elif delta < -1e-9:
            trend = "down"

    summary = {
        "active_markers": active_markers,
        "clusters": clusters,
        "density_log": density_log,
        "stats": {
            "count": len(density_log_full),
            "latest": latest,
            "trend": trend,
        },
    }
    return summary
