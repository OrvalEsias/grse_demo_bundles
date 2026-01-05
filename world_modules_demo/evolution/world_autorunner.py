# engine/autorun_world_tick.py
from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import time

# --- Import the three stage engines (with soft fallbacks) ---
try:
    from engine.world_expansion_engine import expand_world as _expand_world
except Exception:
    def _expand_world(world_state: Dict[str, Any], *_, **__) -> Dict[str, Any]:
        return world_state

try:
    from engine.world_feature_engine import update_world_features as _update_world_features
except Exception:
    def _update_world_features(world_state: Dict[str, Any], *_a, **_k) -> Dict[str, Any]:
        return world_state

try:
    from engine.zone_engine import update_zones as _update_zones
except Exception:
    def _update_zones(world_state: Dict[str, Any], *_a, **_k) -> Dict[str, Any]:
        return world_state

# --- Optional world util hooks (safe to miss) ---
try:
    from engine.world_util import _safe_float as _wf_safe_float  # type: ignore
    from engine.world_util import _zones_as_dict as _wf_zones_as_dict  # type: ignore
    from engine.world_util import apply_world_logic as _apply_world_logic  # type: ignore
except Exception:
    def _wf_safe_float(x, d=0.0):
        try:
            return float(x)
        except Exception:
            return d
    def _wf_zones_as_dict(w: Dict[str, Any]) -> Dict[str, Any]:
        z = w.get("zones")
        if isinstance(z, dict):
            return z
        w["zones"] = {}
        return w["zones"]
    def _apply_world_logic(world: Dict[str, Any], *_a, **_k) -> Dict[str, Any]:
        world["world_age"] = int(world.get("world_age", 0)) + 1
        world["last_update"] = datetime.now(timezone.utc).isoformat()
        return world

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _append_event(world: Dict[str, Any], msg: str) -> None:
    world.setdefault("world_events", []).append({
        "timestamp": _utcnow_iso(),
        "event": msg
    })
    # keep lean
    if len(world["world_events"]) > 500:
        del world["world_events"][:-500]

def _smooth_symbolic_density(world: Dict[str, Any], alpha: float = 0.33) -> None:
    """
    Recompute global symbolic_density from zones, then EMA-smooth with current value.
    Also appends to density_log.
    """
    zones = _wf_zones_as_dict(world)
    if not zones:
        # still log something for continuity
        sd = _wf_safe_float(world.get("symbolic_density", 0.0), 0.0)
        dl = world.setdefault("density_log", [])
        dl.append(float(sd))
        world["density_log"] = dl[-300:]
        return

    vals = []
    for z in zones.values():
        if not isinstance(z, dict):
            continue
        # prefer per-zone symbolic_density; fallback to energy
        zv = z.get("symbolic_density", z.get("energy", 0.0))
        vals.append(_wf_safe_float(zv, 0.0))
    avg = (sum(vals) / len(vals)) if vals else 0.0

    current = _wf_safe_float(world.get("symbolic_density", 0.0), 0.0)
    new_sd = (1.0 - alpha) * current + alpha * avg
    world["symbolic_density"] = float(new_sd)

    dl = world.setdefault("density_log", [])
    dl.append(float(new_sd))
    world["density_log"] = dl[-300:]

def autorun_world_tick(world_state: Dict[str, Any], prompt: str = "") -> Dict[str, Any]:
    """
    Single autorun tick for the world:
      1) expand_world         (topology/new content)
      2) update_world_features(prompt)  (feature intensities, flags)
      3) update_zones(prompt) (per-zone adjustments)
      4) recompute+smooth global symbolic_density; log to density_log
      5) increment world_age and update last_update (via world_util if available)
      6) record lightweight audit events on errors
    """
    world = world_state if isinstance(world_state, dict) else {}

    t0 = time.perf_counter()
    try:
        world = _expand_world(world)
    except Exception as e:
        _append_event(world, f"[expand_world] error: {e!r}")

    try:
        world = _update_world_features(world, prompt)
    except Exception as e:
        _append_event(world, f"[update_world_features] error: {e!r}")

    try:
        world = _update_zones(world, prompt)
    except Exception as e:
        _append_event(world, f"[update_zones] error: {e!r}")

    # Recompute global symbolic density & log history
    try:
        _smooth_symbolic_density(world, alpha=0.33)
    except Exception as e:
        _append_event(world, f"[symbolic_density] error: {e!r}")

    # Age tick + last_update + optional non-neutral intent logging
    try:
        world = _apply_world_logic(world, {"name": "(system)"}, {"intent": "neutral"})
    except Exception as e:
        # Fallback if world_util is unavailable
        world["world_age"] = int(world.get("world_age", 0)) + 1
        world["last_update"] = _utcnow_iso()
        _append_event(world, f"[apply_world_logic] error: {e!r}")

    # Perf note
    dt = time.perf_counter() - t0
    world["last_tick_ms"] = int(dt * 1000)

    return world
