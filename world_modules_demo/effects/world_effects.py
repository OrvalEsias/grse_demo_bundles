# engine/world_effects.py
from __future__ import annotations

from typing import Any, Dict, Tuple, List, Optional, Union
from datetime import datetime

Number = Union[int, float]
EffectSpec = Union[Number, Dict[str, Any]]

__all__ = [
    "apply_character_effect_to_world",
    "apply_effects_batch",
]

# ------------------------- path helpers -------------------------

def _path_tokens(path: str) -> List[str]:
    """Accepts dotted 'a.b.c' or pointer '/a/b/c' paths."""
    if not path:
        return []
    if path.startswith("/"):
        parts = path.split("/")[1:]
        return [p.replace("~1", "/").replace("~0", "~") for p in parts if p]
    return [p for p in path.split(".") if p]

def _get_in(root: Dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = root
    for tok in _path_tokens(path):
        if isinstance(cur, dict) and tok in cur:
            cur = cur[tok]
        else:
            return default
    return cur

def _ensure_path(root: Dict[str, Any], path: str) -> Tuple[Dict[str, Any], str]:
    """
    Ensure all parents exist; return (parent_dict, last_key).
    Creates intermediate dicts if missing.
    """
    tokens = _path_tokens(path)
    if not tokens:
        raise ValueError("Empty trait path.")
    cur = root
    for tok in tokens[:-1]:
        if tok not in cur or not isinstance(cur[tok], dict):
            cur[tok] = {}
        cur = cur[tok]
    return cur, tokens[-1]

def _set_in(root: Dict[str, Any], path: str, value: Any) -> None:
    parent, last = _ensure_path(root, path)
    parent[last] = value

# ------------------------- numeric helpers -------------------------

def _to_float(x: Any, default: float = 0.0) -> float:
    try:
        if isinstance(x, bool):
            return float(int(x))
        return float(x)
    except Exception:
        return default

def _clamp(x: float, lo: Optional[float], hi: Optional[float]) -> float:
    if lo is not None and x < lo:
        x = lo
    if hi is not None and x > hi:
        x = hi
    return x

# ------------------------- effect core -------------------------

def _resolve_trait_path(trait: str) -> str:
    """
    Map plain trait names into storage paths.
    If user passes a nested path, keep it.
    """
    if "/" in trait or "." in trait:
        return trait  # already a path
    # default bucket: world_traits.<trait>
    return f"world_traits.{trait}"

def _read_value(world: Dict[str, Any], path: str) -> float:
    val = _get_in(world, path, None)
    if val is None and path.startswith("world_traits."):
        # Fallback to features.*.value if present (legacy worlds)
        candidate = path.replace("world_traits.", "features.")
        # common pattern: features.<name>.value
        v = _get_in(world, candidate + ".value", None)
        if v is not None:
            return _to_float(v, 0.0)
    return _to_float(val, 0.0)

def _caps_for_path(world: Dict[str, Any], path: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Per-trait caps stored in world['world_trait_caps'] as:
      { "<path>": {"min": 0.0, "max": 1.0 }, "world_traits.spiritual_noise": {...} }
    Fallback commonsense caps for a few known traits if not specified.
    """
    caps = world.get("world_trait_caps", {})
    c = {}
    if isinstance(caps, dict):
        c = caps.get(path) or caps.get(path.replace("/", ".")) or {}
    tmin = c.get("min")
    tmax = c.get("max")

    if tmin is None and tmax is None:
        # lightweight defaults for typical fields
        if path.endswith(("spiritual_noise", "media_signal")):
            tmin, tmax = 0.0, 5.0
        elif path.endswith(("symbolic_density", "energy")):
            tmin, tmax = 0.0, 12.0
    return (None if tmin is None else float(tmin),
            None if tmax is None else float(tmax))

def _apply_one_numeric(old: float, spec: EffectSpec) -> Tuple[float, str]:
    """
    Compute new value from an EffectSpec.
    Spec forms:
      - number: treated as {"op":"add","value":number}
      - {"op":"add"|"mul"|"set"|"lerp", "value":x, "alpha":a, "min":m, "max":M}
    Returns (new_value, op_used)
    """
    if not isinstance(spec, dict):
        spec = {"op": "add", "value": spec}

    op = str(spec.get("op", "add")).lower()
    v = _to_float(spec.get("value", 0.0), 0.0)
    if op == "add":
        new = old + v
    elif op == "mul":
        new = old * (v if v != 0 else 1.0)
    elif op == "set":
        new = v
    elif op == "lerp":
        # EMA-style smoothing: new = old + alpha*(target - old)
        alpha = float(spec.get("alpha", 0.3))
        new = old + alpha * (v - old)
    else:
        # default to add
        new = old + v
        op = "add"

    # Optional min/max clamp within the spec
    new = _clamp(new, spec.get("min"), spec.get("max"))
    return new, op

def _record_history(world: Dict[str, Any], path: str, value: float) -> None:
    hist = world.setdefault("world_traits_history", {})
    lst = hist.setdefault(path, [])
    lst.append({"t": datetime.utcnow().isoformat(), "v": float(value)})
    # keep it lean
    if len(lst) > 300:
        del lst[:-300]

# ------------------------- public API -------------------------

def apply_character_effect_to_world(
    world_data: Dict[str, Any],
    effect_dict: Dict[str, EffectSpec],
    *,
    default_min: Optional[float] = None,
    default_max: Optional[float] = None,
    record_history: bool = True
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """
    Apply symbolic effects from a character (or any source) to world traits.

    Args:
        world_data: world state (mutated in place)
        effect_dict: mapping from trait name or path -> EffectSpec
            EffectSpec can be a number (add) or dict:
              {"op":"add|mul|set|lerp", "value":x, "alpha":0.3, "min":m, "max":M}
        default_min/default_max: global clamp if no per-trait cap is set
        record_history: append (timestamp, value) to world_traits_history[path]

    Returns:
        (world_data, effects_applied) where effects_applied[path] = {
            "old": <float>, "new": <float>, "op": <str>, "clamped": bool
        }
    """
    if world_data is None:
        raise ValueError("world_data is None — cannot apply effects.")

    # Ensure base containers exist
    world_data.setdefault("world_traits", {})
    world_data.setdefault("features", {})

    applied: Dict[str, Dict[str, Any]] = {}

    for trait_key, spec in (effect_dict or {}).items():
        path = _resolve_trait_path(trait_key)
        old = _read_value(world_data, path)
        new, op_used = _apply_one_numeric(old, spec)

        # Apply caps: per-path caps override defaults
        cap_min, cap_max = _caps_for_path(world_data, path)
        if cap_min is None: cap_min = default_min
        if cap_max is None: cap_max = default_max

        clamped_before = new
        new = _clamp(new, cap_min, cap_max)
        was_clamped = (new != clamped_before)

        # Write back
        _set_in(world_data, path, float(new))
        if record_history:
            _record_history(world_data, path, new)

        applied[path] = {
            "old": float(old),
            "new": float(new),
            "op": op_used,
            "clamped": bool(was_clamped),
            "min": cap_min,
            "max": cap_max
        }

        # Optional: lightweight console line (keep quiet in prod)
        # print(f"[WorldEffects] {path}: {old:.4f} --{op_used}--> {new:.4f}" + (" (clamped)" if was_clamped else ""))

    return world_data, applied


def apply_effects_batch(
    world_data: Dict[str, Any],
    effects: List[Dict[str, EffectSpec]],
    *,
    default_min: Optional[float] = None,
    default_max: Optional[float] = None,
    record_history: bool = True
) -> Tuple[Dict[str, Any], List[Dict[str, Dict[str, Any]]]]:
    """
    Apply a list of effect dicts (useful when multiple characters emit effects).
    Returns per-batch applied reports for downstream logging.
    """
    reports: List[Dict[str, Dict[str, Any]]] = []
    for eff in effects or []:
        world_data, applied = apply_character_effect_to_world(
            world_data, eff, default_min=default_min, default_max=default_max, record_history=record_history
        )
        reports.append(applied)
    return world_data, reports
