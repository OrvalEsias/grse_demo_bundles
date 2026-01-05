# engine/world_delta_map.py
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple, Union, Optional

Number = Union[int, float]
DeltaMap = Dict[str, float]

__all__ = [
    "map_world_deltas",
    "filter_deltas",
    "summarize_numeric_deltas",
    "aggregate_by_top_level",
    "aggregate_by_zone",
]

# ---------------------- Path formatting ----------------------

def _fmt_path(parent: str, key: Union[str, int], style: str = "pointer") -> str:
    """
    Build a nested path in either:
      - 'pointer'  : /zones/dream_gate/energy
      - 'dotted'   : zones.dream_gate.energy
      - 'brackets' : zones["dream_gate"].energy  (dict keys quoted, lists as [i])
    """
    if style not in ("pointer", "dotted", "brackets"):
        style = "pointer"

    if style == "pointer":
        # JSON Pointer-ish
        esc = str(key).replace("~", "~0").replace("/", "~1")
        return f"{parent}/{esc}" if parent else f"/{esc}"

    if style == "dotted":
        if isinstance(key, int):
            # Use [i] for arrays to avoid ambiguity in dotted style
            return f"{parent}[{key}]" if parent else f"[{key}]"
        return f"{parent}.{key}" if parent else f"{key}"

    # brackets
    if isinstance(key, int):
        return f"{parent}[{key}]" if parent else f"[{key}]"
    # quote dict keys for clarity
    k = str(key).replace('"', '\\"')
    return f'{parent}["{k}"]' if parent else f'["{k}"]'


# ---------------------- Core traversal ----------------------

def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def _num_delta(a: Any, b: Any) -> Optional[float]:
    if _is_num(a) and _is_num(b):
        return float(b) - float(a)
    return None

def _walk_numeric_deltas(
    old: Any,
    new: Any,
    path: str,
    out: DeltaMap,
    *,
    epsilon: float,
    path_style: str
) -> None:
    # If both numeric → compute
    d = _num_delta(old, new)
    if d is not None:
        if abs(d) > epsilon:
            out[path or "/"] = d
        return

    # Dict ↔ Dict
    if isinstance(old, dict) and isinstance(new, dict):
        old_keys = set(old.keys())
        new_keys = set(new.keys())
        # Shared keys
        for k in sorted(old_keys & new_keys):
            _walk_numeric_deltas(
                old[k], new[k],
                _fmt_path(path, k, path_style),
                out, epsilon=epsilon, path_style=path_style
            )
        # Added/Removed keys that are numeric at top level:
        # (We ignore non-shared keys by default; enable if you want deltas when a numeric appears/disappears.)
        return

    # List ↔ List (index-wise comparison)
    if isinstance(old, list) and isinstance(new, list):
        n = min(len(old), len(new))
        for i in range(n):
            _walk_numeric_deltas(
                old[i], new[i],
                _fmt_path(path, i, path_style),
                out, epsilon=epsilon, path_style=path_style
            )
        # By default we ignore tail adds/removes for numeric deltas.
        return

    # Mismatched / non-numeric leaves: nothing to do
    return


# ---------------------- Public API ----------------------

def map_world_deltas(
    old_world: Dict[str, Any],
    new_world: Dict[str, Any],
    *,
    epsilon: float = 1e-3,
    path_style: str = "pointer",
    include_top_level_only: bool = False
) -> DeltaMap:
    """
    Return a path->delta map (floats) across the entire world structure.

    Args:
        old_world: previous world state
        new_world: new world state
        epsilon: minimum absolute change to record
        path_style: 'pointer' (default), 'dotted', or 'brackets'
        include_top_level_only: if True, only compute deltas on top-level numeric fields

    Notes:
        - By default we only compute deltas where both old and new are numeric at the same path.
        - Added/removed keys are ignored in this mapping (since there is no old or new numeric to subtract against).
          If you need structural ops, pair this with your deep diff module.
    """
    out: DeltaMap = {}

    if include_top_level_only:
        for k in new_world.keys() & old_world.keys():
            if _is_num(new_world[k]) and _is_num(old_world[k]):
                d = float(new_world[k]) - float(old_world[k])
                if abs(d) > epsilon:
                    out[_fmt_path("", k, path_style)] = d
        return out

    # Full deep walk
    # Prime traversal from the root: treat root as dict
    shared = (old_world.keys() & new_world.keys())
    for k in sorted(shared):
        _walk_numeric_deltas(
            old_world[k], new_world[k],
            _fmt_path("", k, path_style),
            out, epsilon=epsilon, path_style=path_style
        )
    return out


def filter_deltas(delta_map: DeltaMap, *, min_abs: float = 1e-3) -> DeltaMap:
    """Return a new map with only entries whose |delta| >= min_abs."""
    return {k: v for k, v in delta_map.items() if abs(v) >= min_abs}


def summarize_numeric_deltas(delta_map: DeltaMap, *, precision: int = 4) -> List[str]:
    """
    Make human-friendly lines, e.g.:
      '/symbolic_density: +0.0520'
      '/zones/dream_gate/energy: -0.1000'
    """
    lines: List[str] = []
    for path, d in sorted(delta_map.items()):
        sign = "+" if d >= 0 else ""
        lines.append(f"{path}: {sign}{round(d, precision):.{precision}f}")
    return lines


# ---------------------- Rollups ----------------------

def _top_key_of_pointer_path(path: str) -> str:
    # '/zones/dream_gate/energy' -> 'zones'
    if not path:
        return ""
    if path[0] == "/":
        parts = path.split("/")
        return parts[1] if len(parts) > 1 else ""
    # dotted or brackets: take segment before first '.' or '['
    p = path
    # find first . or [
    idx_dot = p.find(".")
    idx_brk = p.find("[")
    idx = min([i for i in (idx_dot, idx_brk) if i != -1], default=-1)
    return p if idx == -1 else p[:idx]

def aggregate_by_top_level(delta_map: DeltaMap) -> Dict[str, float]:
    """
    Sum deltas by their top-level container.
    Example:
      '/symbolic_density' -> bucket 'symbolic_density'
      '/zones/dream_gate/energy' -> bucket 'zones'
    """
    agg: Dict[str, float] = {}
    for path, d in delta_map.items():
        bucket = _top_key_of_pointer_path(path)
        agg[bucket] = agg.get(bucket, 0.0) + d
    return agg

def aggregate_by_zone(delta_map: DeltaMap) -> Dict[str, float]:
    """
    Sum deltas per zone name for paths under '/zones/<zone>/*'
    Works for 'pointer' style paths. For other styles, result may be empty.
    """
    out: Dict[str, float] = {}
    for path, d in delta_map.items():
        if not path.startswith("/zones/"):
            continue
        parts = path.split("/")
        if len(parts) >= 4:
            zone = parts[2]
            out[zone] = out.get(zone, 0.0) + d
    return out


# ---------------------- Quick self-test ----------------------
if __name__ == "__main__":
    old = {
        "symbolic_density": 0.30,
        "spiritual_noise": 0.10,
        "media_signal": 0.20,
        "zones": {
            "dream_gate": {"energy": 0.20, "symbolic_density": 0.20},
            "signal_vault": {"energy": 0.30}
        },
        "density_log": [0.28, 0.30, 0.33]
    }
    new = {
        "symbolic_density": 0.35,
        "spiritual_noise": 0.12,
        "media_signal": 0.10,
        "zones": {
            "dream_gate": {"energy": 0.25, "symbolic_density": 0.22},
            "signal_vault": {"energy": 0.30}  # unchanged
        },
        "density_log": [0.28, 0.31, 0.34]
    }

    deltas = map_world_deltas(old, new, epsilon=1e-3, path_style="pointer")
    print("DELTAS:", summarize_numeric_deltas(deltas))
    print("ROLLUP (top):", aggregate_by_top_level(deltas))
    print("ROLLUP (zones):", aggregate_by_zone(deltas))
