# engine/world_template_engine.py
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import math
import random
import time

__all__ = ["generate_world", "generate_zone", "ZONE_TEMPLATES"]

# -------------------- Templates --------------------

# Baseline zone archetypes; values are default seeds that will be scaled.
ZONE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "cradle_of_light": {
        "label": "Cradle of Light",
        "description": "A warm basin where symbols condense like dew on glass.",
        "symbolic_density": 0.12,
        "energy": 0.12,
        "spiritual_noise": 0.05,
        "media_signal": 0.10,
        "symbolic_tags": ["origin", "illumination"],
        "default_intent": "attune_self",
        "items": ["glyph_of_insight", "light_fragment"],
        "soft_cap": 3.0,
    },
    "echo_forest": {
        "label": "Echo Forest",
        "description": "A thicket of murmuring boughs; footsteps return as memories.",
        "symbolic_density": 0.25,
        "energy": 0.25,
        "spiritual_noise": 0.20,
        "media_signal": 0.05,
        "symbolic_tags": ["memory", "sound", "repetition"],
        "default_intent": "focus_ritual",
        "items": ["mirror_fragment", "seed_pattern"],
        "soft_cap": 4.5,
    },
    "fracture_mirror": {
        "label": "Fracture Mirror",
        "description": "A plaza of broken panes reflecting possible selves.",
        "symbolic_density": 0.50,
        "energy": 0.50,
        "spiritual_noise": 0.30,
        "media_signal": 0.25,
        "symbolic_tags": ["duality", "reflection", "rupture"],
        "default_intent": "activate_glyph",
        "items": ["rupture_glyph", "mirror_wand"],
        "soft_cap": 6.0,
    },
    # Optional familiar archetypes so worlds feel consistent with your other modules:
    "signal_vault": {
        "label": "Signal Vault",
        "description": "A chamber of archived frequencies and sleeping channels.",
        "symbolic_density": 0.30,
        "energy": 0.30,
        "spiritual_noise": 0.10,
        "media_signal": 0.35,
        "symbolic_tags": ["archive", "broadcast"],
        "default_intent": "signal_broadcast",
        "items": ["amplifier_node", "signal_scroll"],
        "soft_cap": 6.5,
    },
    "reflected_chamber": {
        "label": "Reflected Chamber",
        "description": "A long hall of calm mirrors, each slightly delayed.",
        "symbolic_density": 0.26,
        "energy": 0.26,
        "spiritual_noise": 0.12,
        "media_signal": 0.18,
        "symbolic_tags": ["mirror", "self_model"],
        "default_intent": "activate_glyph",
        "items": ["mirror_fragment", "crystal_orb"],
        "soft_cap": 5.0,
    },
    "market_ruins": {
        "label": "Market Ruins",
        "description": "Crumbling stalls where trades echo as vows.",
        "symbolic_density": 0.22,
        "energy": 0.22,
        "spiritual_noise": 0.18,
        "media_signal": 0.14,
        "symbolic_tags": ["trade", "bargain", "trace"],
        "default_intent": "bind_true_name",
        "items": ["symbolic_coin", "rusted_key"],
        "soft_cap": 4.0,
    },
}

# -------------------- Helpers --------------------

def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x

def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if isinstance(x, bool):
            return float(int(x))
        return float(x)
    except Exception:
        return default

def _zones_as_dict(world: Dict[str, Any]) -> Dict[str, Any]:
    z = world.get("zones")
    if isinstance(z, dict):
        return z
    if isinstance(z, list):
        out: Dict[str, Any] = {}
        for i, entry in enumerate(z):
            if not isinstance(entry, dict):
                continue
            name = entry.get("name") or f"zone_{i}"
            entry["name"] = name
            out[name] = entry
        world["zones"] = out
        return out
    world["zones"] = {}
    return world["zones"]

def _scale_from_world(world_state: Optional[Dict[str, Any]]) -> float:
    """
    Produce a gentle scale factor from current world conditions:
      - higher global symbolic_density pushes zones up a bit
      - features with 'value' also nudge upwards
    """
    if not isinstance(world_state, dict):
        return 1.0
    d = _safe_float(world_state.get("symbolic_density", 0.0), 0.0)
    feats = world_state.get("features") or {}
    feat_sum = 0.0
    if isinstance(feats, dict):
        for v in feats.values():
            if isinstance(v, dict) and "value" in v:
                feat_sum += _safe_float(v.get("value", 0.0), 0.0)
            elif isinstance(v, (int, float)):
                feat_sum += _safe_float(v, 0.0)
    # Normalize gently
    f = 1.0 + 0.35 * _clamp(d / 2.0, 0.0, 1.0) + 0.25 * _clamp(feat_sum / 3.0, 0.0, 1.0)
    return _clamp(f, 1.0, 2.0)

def _materialize_zone(
    key: str,
    seed_scale: float,
    rnd: random.Random
) -> Dict[str, Any]:
    base = ZONE_TEMPLATES[key].copy()
    # Apply mild randomization around the seed scale
    jitter = 0.85 + 0.30 * rnd.random()   # 0.85 .. 1.15
    s = _clamp(seed_scale * jitter, 0.7, 2.2)

    # Derive fields
    sd0 = _safe_float(base.get("symbolic_density", 0.2), 0.2)
    en0 = _safe_float(base.get("energy", sd0), sd0)
    sn0 = _safe_float(base.get("spiritual_noise", 0.1), 0.1)
    ms0 = _safe_float(base.get("media_signal", 0.1), 0.1)
    cap = _safe_float(base.get("soft_cap", 5.0), 5.0)

    z = {
        "label": base.get("label", key.replace("_", " ").title()),
        "name": key,
        "description": base.get("description", ""),
        "symbolic_density": round(_clamp(sd0 * s, 0.0, cap), 6),
        "energy": round(_clamp(en0 * s, 0.0, cap), 6),
        "spiritual_noise": round(_clamp(sn0 * (0.9 + 0.2 * rnd.random()), 0.0, 5.0), 6),
        "media_signal": round(_clamp(ms0 * (0.9 + 0.2 * rnd.random()), 0.0, 5.0), 6),
        "symbolic_tags": list(base.get("symbolic_tags", [])),
        "default_intent": base.get("default_intent", "attune_self"),
        "items": list(base.get("items", [])),
        "links": [],               # filled later
        "narrative": [],
        "soft_cap": cap,
        "features": {},            # per-zone features if needed later
    }
    return z

def _link_ring(zone_keys: List[str]) -> Dict[str, List[str]]:
    """
    Create simple ring links between zones, plus a few cross chords for navigability.
    """
    n = len(zone_keys)
    adj = {k: [] for k in zone_keys}
    if n <= 1:
        return adj
    for i, k in enumerate(zone_keys):
        adj[k].append(zone_keys[(i + 1) % n])
        adj[k].append(zone_keys[(i - 1) % n])
    if n >= 4:
        # add chords
        adj[zone_keys[0]].append(zone_keys[2 % n])
        adj[zone_keys[1]].append(zone_keys[3 % n])
    # dedupe
    for k in adj:
        seen = set()
        uniq = []
        for x in adj[k]:
            if x not in seen and x != k:
                seen.add(x)
                uniq.append(x)
        adj[k] = uniq
    return adj

# -------------------- Public API --------------------

def generate_zone(template_name: str) -> Dict[str, Any]:
    """
    Backwards-compatible: returns a *template copy* only.
    (materialization with scaling happens inside generate_world)
    """
    return ZONE_TEMPLATES.get(template_name, {}).copy()

def generate_world(
    world_state: Optional[Dict[str, Any]] = None,
    *,
    seed: Optional[int] = None,
    n_zones: int = 3,
    include_keys: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Build a complete world from zone templates.
    - Scales zone intensities based on current world_state.
    - Produces a dict with fields your app expects.

    Args:
        world_state: optional current world, used for scaling.
        seed: RNG seed for reproducibility.
        n_zones: number of zones to emit (ignored if include_keys provided).
        include_keys: explicit list of template keys to use.

    Returns:
        dict world with normalized shape.
    """
    rnd = random.Random(seed if seed is not None else time.time_ns())
    scale = _scale_from_world(world_state)

    # Choose which templates
    keys = list(ZONE_TEMPLATES.keys())
    if include_keys:
        chosen = [k for k in include_keys if k in ZONE_TEMPLATES]
    else:
        # bias: always try to include at least one familiar anchor
        anchors = ["cradle_of_light", "echo_forest", "fracture_mirror"]
        pool = anchors + [k for k in keys if k not in anchors]
        rnd.shuffle(pool)
        chosen = pool[:max(1, n_zones)]

    # Materialize zones
    zones: Dict[str, Any] = {}
    for k in chosen:
        zones[k] = _materialize_zone(k, seed_scale=scale, rnd=rnd)

    # Link them
    adj = _link_ring(chosen)
    for k, links in adj.items():
        zones[k]["links"] = links

    # Aggregate some global stats (lightweight)
    if zones:
        sden = sum(zones[k]["symbolic_density"] for k in zones) / len(zones)
        sne  = sum(zones[k]["spiritual_noise"] for k in zones) / len(zones)
        ms   = sum(zones[k]["media_signal"]      for k in zones) / len(zones)
    else:
        sden, sne, ms = 0.0, 0.0, 0.0

    world: Dict[str, Any] = {
        "symbolic_density": round(sden, 6),
        "spiritual_noise": round(sne, 6),
        "media_signal": round(ms, 6),
        "zones": zones,                # dict-of-zones
        "active_markers": {},
        "features": {},
        "density_log": [round(max(0.0, sden - 0.02), 6), round(sden, 6)],
        "world_age": 0,
        "pending_prompts": [],
    }

    # Convenience: set a default active zone if missing
    if chosen:
        world["active_zone"] = chosen[0]

    return world
