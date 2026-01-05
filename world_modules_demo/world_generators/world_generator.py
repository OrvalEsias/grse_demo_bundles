# engine/world_generator.py
from __future__ import annotations
from typing import Any, Dict, Optional, Tuple
import random
import time

# ---------- Safe imports with fallbacks ----------
def _noop_generator(*_a, **_k) -> Dict[str, Any]:
    # Minimal world skeleton used as a last resort.
    return {
        "symbolic_density": 0.0,
        "spiritual_noise": 0.0,
        "media_signal": 0.0,
        "zones": {"dream_gate": {"energy": 0.0, "links": [], "items": [], "narrative": []}},
        "active_markers": {},
        "features": {},
        "density_log": [],
        "world_age": 0,
    }

try:
    from engine.recursive_world_generator import generate_world as _gen_recursive
except Exception:
    _gen_recursive = _noop_generator

try:
    from engine.world_template_engine import generate_world as _gen_template
except Exception:
    _gen_template = _noop_generator


# ---------- Utilities ----------
def _clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v

def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if isinstance(x, bool):
            return float(int(x))
        return float(x)
    except Exception:
        return default

def _entropy_hint(world_state: Dict[str, Any]) -> float:
    """
    A tiny 'chaos' signal to bias generator choice:
    - recent |density_log| slope
    - variety of active markers
    - features intensity (sum of .value if present)
    """
    if not isinstance(world_state, dict):
        return 0.0

    dens = world_state.get("density_log") or []
    slope = 0.0
    if isinstance(dens, list) and len(dens) >= 2:
        try:
            last = dens[-5:] if len(dens) > 5 else dens
            slope = _safe_float(last[-1] - last[0]) / max(1, len(last) - 1)
        except Exception:
            slope = 0.0

    markers = world_state.get("active_markers") or {}
    marker_variety = len(markers) if isinstance(markers, dict) else 0

    feats = world_state.get("features") or {}
    feat_intensity = 0.0
    if isinstance(feats, dict):
        for v in feats.values():
            if isinstance(v, dict) and "value" in v:
                feat_intensity += _safe_float(v.get("value", 0.0), 0.0)
            elif isinstance(v, (int, float)):
                feat_intensity += _safe_float(v, 0.0)

    # normalize coarsely into 0..1
    slope_n = _clamp(slope * 5.0, -1.0, 1.0)  # modest boost
    variety_n = _clamp(marker_variety / 12.0, 0.0, 1.0)
    feats_n = _clamp(feat_intensity / 6.0, 0.0, 1.0)
    # Emphasize features & variety
    return _clamp(0.2 * (slope_n if slope_n > 0 else 0) + 0.4 * variety_n + 0.4 * feats_n, 0.0, 1.0)


def _validate_world(w: Dict[str, Any]) -> Dict[str, Any]:
    """Light normalization so downstream code is safe."""
    w = dict(w or {})
    w.setdefault("symbolic_density", 0.0)
    w.setdefault("spiritual_noise", 0.0)
    w.setdefault("media_signal", 0.0)
    w.setdefault("world_age", 0)
    w.setdefault("active_markers", {})
    w.setdefault("features", {})
    w.setdefault("density_log", [])
    # zones as dict
    zones = w.get("zones")
    if isinstance(zones, list):
        # upgrade list -> dict keyed by 'name' or index
        zdict = {}
        for i, z in enumerate(zones):
            if not isinstance(z, dict):
                continue
            name = z.get("name") or f"zone_{i}"
            z["name"] = name
            zdict[name] = z
        w["zones"] = zdict
    elif not isinstance(zones, dict):
        w["zones"] = {"dream_gate": {"energy": 0.0, "links": [], "items": [], "narrative": []}}
    return w


def _merge_carry_over(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge useful state from old world into the newly generated one
    without trampling the generator's structure.
    """
    out = _validate_world(new)

    # Carry a bounded history/log & markers to keep continuity
    old = _validate_world(old)
    # density log tail
    if isinstance(old.get("density_log"), list):
        tail = old["density_log"][-50:]
        out["density_log"] = (out.get("density_log") or [])[-150:] + tail
        out["density_log"] = out["density_log"][-200:]

    # active markers: add counts
    a_old = old.get("active_markers") or {}
    a_new = out.get("active_markers") or {}
    if isinstance(a_old, dict) and isinstance(a_new, dict):
        for k, v in a_old.items():
            if not isinstance(v, dict):
                continue
            rec = a_new.get(k, {"count": 0})
            rec["count"] = int(rec.get("count", 0)) + int(v.get("count", 0))
            a_new[k] = rec
        out["active_markers"] = a_new

    # features: if new generator didn’t set, keep old; else blend intensities
    f_old = old.get("features") or {}
    f_new = out.get("features") or {}
    if isinstance(f_old, dict) and isinstance(f_new, dict):
        for k, v in f_old.items():
            if k not in f_new:
                f_new[k] = v
            else:
                # blend numeric value if present
                vo = v.get("value") if isinstance(v, dict) else None
                vn = f_new[k].get("value") if isinstance(f_new[k], dict) else None
                if isinstance(vo, (int, float)) and isinstance(vn, (int, float)):
                    f_new[k]["value"] = round(_clamp(0.5 * vo + 0.5 * vn, 0.0, 1.0), 4)
        out["features"] = f_new

    # carry forward world_age (increment) if new didn’t set one
    out["world_age"] = int(old.get("world_age", 0)) + 1 if "world_age" not in new else int(new["world_age"])
    return out


def _choose_mode_auto(world_state: Dict[str, Any]) -> str:
    """
    Heuristic to pick generator:
      - Strong recursion signal → 'recursive'
      - High density / high entropy → 'recursive'
      - Otherwise 'template'
    """
    ws = _validate_world(world_state)
    density = _safe_float(ws.get("symbolic_density", 0.0), 0.0)
    recursion_flag = bool(ws.get("recursion_flag", False))

    # legacy tag list support
    tags = ws.get("world_traits", []) or []
    tagged_recursive = any(t in {"evolving", "mirror_phase", "echoing", "glyphic"} for t in tags)

    entropy = _entropy_hint(ws)

    if recursion_flag or tagged_recursive:
        return "recursive"
    if density >= 0.4 and entropy >= 0.25:
        return "recursive"
    return "template"


def _generate_hybrid(world_state: Dict[str, Any], *, rnd: random.Random) -> Dict[str, Any]:
    """
    Hybrid strategy:
      - Usually template, occasionally recursive bursts based on entropy & coinflip
      - Then merge/carry-over to keep continuity
    """
    ws = _validate_world(world_state)
    entropy = _entropy_hint(ws)
    # Base probability for recursive pass grows with entropy
    p_recursive = 0.20 + 0.60 * entropy  # 0.2 .. 0.8
    do_recursive = rnd.random() < p_recursive

    w_new = _gen_recursive() if do_recursive else _gen_template()
    return _merge_carry_over(ws, w_new)


# ---------- Public API ----------
def generate_world(
    mode: str = "auto",
    world_state: Optional[Dict[str, Any]] = None,
    *,
    seed: Optional[int] = None,
    merge_carryover: bool = True
) -> Dict[str, Any]:
    """
    Generate a new world using template or recursive generators (or both).

    Args:
        mode: 'template' | 'recursive' | 'auto' | 'hybrid'
        world_state: current world (used by 'auto'/'hybrid' and for carryover)
        seed: optional RNG seed for reproducibility
        merge_carryover: when True, we preserve continuity (markers, logs, features)

    Returns:
        dict: validated world dictionary
    """
    rnd = random.Random(seed if seed is not None else time.time_ns())
    ws = _validate_world(world_state or {
        "symbolic_density": 0.0,
        "spiritual_noise": 0.0,
        "media_signal": 0.0,
        "world_traits": [],
        "recursion_flag": False,
        "active_markers": {},
        "features": {},
        "density_log": [],
        "world_age": 0,
    })

    chosen = mode.lower().strip() if isinstance(mode, str) else "auto"
    if chosen == "auto":
        chosen = _choose_mode_auto(ws)

    if chosen == "template":
        w_new = _gen_template()
        return _merge_carry_over(ws, w_new) if merge_carryover else _validate_world(w_new)

    if chosen == "recursive":
        w_new = _gen_recursive()
        return _merge_carry_over(ws, w_new) if merge_carryover else _validate_world(w_new)

    if chosen == "hybrid":
        w_new = _generate_hybrid(ws, rnd=rnd)
        return _validate_world(w_new)

    # Fallback
    w_new = _gen_template() if rnd.random() < 0.5 else _gen_recursive()
    return _merge_carry_over(ws, w_new) if merge_carryover else _validate_world(w_new)
