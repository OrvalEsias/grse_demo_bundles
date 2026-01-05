import random
from typing import Dict, Any, Tuple

def expand_world(world_state: Dict[str, Any],
                 *,
                 zone_period: int = 5,
                 density_step_range: Tuple[float, float] = (0.01, 0.03),
                 energy_step_range: Tuple[float, float] = (0.01, 0.03),
                 max_density: float = 12.0,
                 max_zone_density: float = 10.5) -> Dict[str, Any]:
    """
    Expand world state one 'tick':
      - Increments age, density, and symbolic energy (scalar or componentized).
      - Periodically adds a new zone with defaults and links.
      - Maintains density_log, active_markers, pending_prompts.
      - Records machine-readable 'world_effects' for agency tracking.

    Compatible with:
      - world['zones'] as dict-of-zones (preferred) OR as list of zone dicts (legacy).
      - world['symbolic_energy'] as float OR dict of components.

    Returns:
      Updated world_state (mutated in place).
    """
    # ---------- helpers ----------
    def _clamp(x: float, lo: float, hi: float) -> float:
        return lo if x < lo else hi if x > hi else x

    def _zones_as_dict(ws: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """Return (zones_dict, was_list). If the world uses a list, convert it to dict keyed by 'name'."""
        zones = ws.get("zones", {})
        if isinstance(zones, dict):
            return zones, False
        if isinstance(zones, list):
            zdict = {}
            for z in zones:
                name = (z or {}).get("name")
                if not name:
                    # synthesize a name if missing
                    name = f"zone_{len(zdict)}"
                    z["name"] = name
                zdict[name] = z
            ws["zones"] = zdict
            return zdict, True
        # initialize empty dict
        ws["zones"] = {}
        return ws["zones"], False

    def _symbolic_energy_scalar(ws: Dict[str, Any]) -> float:
        se = ws.get("symbolic_energy", 0.0)
        if isinstance(se, (int, float)):
            return float(se)
        if isinstance(se, dict):
            # derive a scalar proxy: baseline*amplifier + mean of extra weights
            baseline = float(se.get("baseline", 0.0))
            amp = float(se.get("amplifier", 1.0))
            extras = [v for k, v in se.items() if k not in ("baseline", "amplifier")]
            extra_mean = (sum(float(x) for x in extras) / max(1, len(extras))) if extras else 0.0
            return baseline * amp + extra_mean
        return 0.0

    def _bump_symbolic_energy(ws: Dict[str, Any], lo: float, hi: float) -> Tuple[float, float]:
        """Mutate ws['symbolic_energy'] (float or dict). Return (before, after) scalar proxy."""
        before = _symbolic_energy_scalar(ws)
        step = random.uniform(lo, hi)
        se = ws.get("symbolic_energy", 0.0)
        if isinstance(se, (int, float)):
            ws["symbolic_energy"] = round(float(se) + step, 6)
        elif isinstance(se, dict):
            # nudge baseline; keep components intact
            base = float(se.get("baseline", before))
            se["baseline"] = round(base + step, 6)
            ws["symbolic_energy"] = se
        else:
            ws["symbolic_energy"] = round(before + step, 6)
        after = _symbolic_energy_scalar(ws)
        return before, after

    def _seed_default_intent(name: str) -> str:
        # simple mapping to keep the world lively
        name_l = name.lower()
        if "signal" in name_l:
            return "signal_broadcast"
        if "mirror" in name_l or "reflect" in name_l:
            return "activate_glyph"
        if "market" in name_l or "bazaar" in name_l or "ruin" in name_l:
            return "bind_true_name"
        if "memory" in name_l or "archive" in name_l or "library" in name_l:
            return "focus_ritual"
        return "attune_self"

    # ---------- start expansion ----------
    ws = world_state
    ws.setdefault("pending_prompts", [])
    ws.setdefault("active_markers", {})
    ws.setdefault("density_log", [])
    features = ws.setdefault("features", {})

    # Age
    world_age = int(ws.get("world_age", 0))
    ws["world_age"] = world_age + 1

    # Zones as dict (normalize)
    zones, was_list = _zones_as_dict(ws)

    # Global symbolic density bump (smooth, then clamp)
    base_density = float(ws.get("symbolic_density", 0.0))
    dens_step = random.uniform(*density_step_range)
    new_density = _clamp(base_density + dens_step, 0.0, max_density)
    ws["symbolic_density"] = round(new_density, 6)
    # log it
    dlog = ws.get("density_log", [])
    if isinstance(dlog, list):
        dlog.append(ws["symbolic_density"])
        ws["density_log"] = dlog[-300:]

    # Symbolic energy bump (scalar or components)
    e_before, e_after = _bump_symbolic_energy(ws, *energy_step_range)

    # Periodic zone creation
    effects = {"added_zones": [], "density_delta": round(new_density - base_density, 6),
               "energy_delta": round(e_after - e_before, 6), "pending_prompts_added": 0, "markers_bumped": []}

    if (world_age + 1) % max(1, zone_period) == 0:
        # Make a unique zone key
        zkey = f"mythic_zone_{world_age + 1}"
        label = "Mythic Zone"
        # derive zone density from energy proxy with a small bias
        z_density = _clamp(e_after + random.uniform(0.02, 0.18), 0.0, max_zone_density)
        zones[zkey] = {
            "label": label,
            "name": zkey,
            "description": "An emergent stratum where symbols accrete into navigable shapes.",
            "energy": round(z_density, 6),
            "symbolic_density": round(z_density, 6),
            "soft_cap": float(min(max_zone_density, 10.5)),
            "default_intent": _seed_default_intent(zkey),
            "links": _suggest_links(list(zones.keys()), zkey),
            "items": [],
            "narrative": [],
            "features": {
                "ambient_markers": ["echo_marker", "emergence_marker"]
            }
        }
        effects["added_zones"].append(zkey)

        # seed a prompt to encourage exploration
        prompt = f"bind true_name and step to zone:{zkey}"
        ws["pending_prompts"].append(prompt)
        effects["pending_prompts_added"] += 1

    # Light environmental features based on symbolic energy proxy
    se_proxy = e_after
    if se_proxy > 1.0:
        features["sky_event"] = "fracture"
    if se_proxy > 2.0:
        features["sea_behavior"] = "inversion_tide"

    # Ambient markers nudge: pick a couple to keep the meter lively
    for mk in random.sample(["echo_marker", "glyph_touched", "memory_link", "signal_carrier",
                             "broadcast_signal", "mirror_trace", "recursion_loop"], k=2):
        rec = ws["active_markers"].get(mk, {"count": 0})
        rec["count"] = int(rec.get("count", 0)) + 1
        ws["active_markers"][mk] = rec
        effects["markers_bumped"].append(mk)

    # Expose machine-readable effects for your agency tracker
    ws["world_effects"] = effects
    return ws


def _suggest_links(existing_keys: list, new_key: str, max_links: int = 3) -> list:
    """
    Pick up to max_links existing zones to link with the new zone.
    Bias toward earlier (hub-like) zones if available.
    """
    if not existing_keys:
        return []
    pool = [k for k in existing_keys if k != new_key]
    if not pool:
        return []
    # bias: earlier keys are more hub-like; sample without replacement
    pool = sorted(pool)[:8]
    n = min(len(pool), max_links)
    return random.sample(pool, k=n)
