# engine/weather_engine.py
# Regional weather drift across linked zones; nudges markers & energy.
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone
import random

# ---------------- Tunables ----------------
BASE_DRIFT      = 0.08   # toward local “baseline” (from micro + type)
LINK_PULL       = 0.22   # how much neighbors affect intensity
FRONT_SPAWN_P   = 0.08   # chance per tick to seed a front in a random zone
FRONT_PUSH      = 0.28   # push when a front exists
INTENSITY_DECAY = 0.06   # decay toward 0 if no drivers
PROMPT_COUPLING = 0.12   # (optional) prompt mentions rain/storm/… (world_util passes prompt)

# Energy coupling (tiny, bounded) — harmonized to world range [-1.0, 12.0]
ENERGY_WET_COOL   = -0.03
ENERGY_STORM_PUMP = +0.04
ENERGY_CLEAR_WARM = +0.02

# States we support (feel free to add more)
WEATHER_STATES = ("clear", "soft_light", "prismatic", "mist", "haze", "dust", "rain", "storm", "gloom", "shimmer")

# Map “type” to a gentle baseline (ruin/market/gate get different flavors)
TYPE_BASELINES = {
    "ruin":     ("mist", "gloom", "rain"),
    "market":   ("haze", "dust", "clear"),
    "gate":     ("soft_light", "shimmer", "prismatic"),
    "generic":  ("clear", "mist", "haze"),
}

# Marker hooks
MARKER_RULES = [
    ("rain",  0.6, "waterlogged"),
    ("storm", 0.6, "storm_channel"),
    ("gloom", 0.6, "veil_light", False),  # remove (False) if present
    ("soft_light", 0.6, "veil_light", True),
]

# ---------------- Public API ----------------
def step(world: Dict[str, Any], prompt: str = "") -> Dict[str, Any]:
    """
    Updates each zone's weather: {'state': str, 'intensity': 0..1}
      - Baseline per zone type + micro features
      - Diffusion along links (regional behavior)
      - Occasional fronts that travel for a few hops
      - Optional prompt coupling ("rain", "storm", "fog", "sun", "clear")
    Side effects:
      - Adds/removes a few markers based on thresholds
      - Slightly nudges zone['energy'] (tiny, bounded) and mirrors into symbolic_density
      - world['weather'] summary written + last_weather_update stamped
    Deterministic per (session_seed, time, zone_id).
    """
    w = world or {}
    zones: Dict[str, Dict[str, Any]] = _zones_as_dict(w)
    if not zones:
        _ensure_world_weather(w, fronts=[])
        return w

    t = int(w.get("time", 0))
    seed = int(w.get("session_seed", 0))
    links = {zid: list((z or {}).get("links", []) or []) for zid, z in zones.items()}
    prev_summary = (w.get("weather") or {})
    fronts = list(prev_summary.get("fronts") or [])

    # Prompt coupling (very light)
    p_bias = _prompt_bias((prompt or "").lower())

    # maybe start a new front
    rng_global = _rng(seed, t, "weather", "global")
    if rng_global.random() < FRONT_SPAWN_P or not fronts:
        origin = _pick_any_zone(zones, rng_global)
        if origin:
            fronts = [{"origin": origin, "age": 0, "kind": _pick_front_kind(rng_global)}]

    # compute one step per zone
    new_fronts: List[Dict[str, Any]] = []
    for zid, z in zones.items():
        if not isinstance(z, dict):
            z = {}
            zones[zid] = z
        state, inten = _current(z)

        # 1) type+micro baseline
        target_state, target_bias = _type_micro_baseline(z)

        # 2) neighbor pull
        neigh_state, neigh_inten = _neighbor_weather(zid, zones, links)

        # 3) fronts push if nearby
        front_push = 0.0
        front_kind: Optional[str] = None
        for fr in fronts:
            dist = _hop_distance(zid, fr.get("origin", ""), links, limit=3)
            if dist is None:
                continue
            strength = max(0.0, (3 - dist) / 3) * FRONT_PUSH
            if strength > front_push:
                front_push = strength
                front_kind = fr.get("kind")

        # 4) prompt bias
        if p_bias:
            target_state = p_bias[0]
            target_bias = max(target_bias, p_bias[1] * PROMPT_COUPLING)

        # State choice (simple vote)
        cand_states = [state, target_state, neigh_state, front_kind]
        state = _vote_state(cand_states, default=state or target_state)

        # Intensity blend + tiny jitter
        inten = (1 - INTENSITY_DECAY) * inten
        inten = inten + BASE_DRIFT * target_bias
        inten = inten + LINK_PULL * neigh_inten
        inten = inten + front_push
        inten = max(0.0, min(1.0, inten + (_rng(seed, t, "jit", zid).random() - 0.5) * 0.02))

        # Side-effects
        _apply_markers(z, state, inten)
        e = _apply_energy_nudge(float(z.get("energy", 0.0)), state, inten)
        z["energy"] = e
        z["symbolic_density"] = e
        zw = _ensure_zone_weather(z)
        zw["state"] = state
        zw["intensity"] = round(inten, 3)
        z["weather"] = zw
        zones[zid] = z

    # Age fronts (short-lived)
    for fr in fronts:
        try:
            fr["age"] = int(fr.get("age", 0)) + 1
        except Exception:
            fr["age"] = 1
        if fr["age"] <= 6:
            new_fronts.append(fr)

    # Summarize world
    summary = _summarize_world(zones, new_fronts)
    w["zones"] = zones
    w["weather"] = summary
    w["last_weather_update"] = _utcnow_iso()
    return w

# ---------------- Internals ----------------
def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _rng(seed: int, t: int, *salt_parts: str) -> random.Random:
    return random.Random(seed ^ hash((seed, t) + tuple(salt_parts)))

def _zones_as_dict(w: Dict[str, Any]) -> Dict[str, Any]:
    z = w.get("zones")
    if isinstance(z, dict):
        return z
    w["zones"] = {}
    return w["zones"]

def _ensure_world_weather(w: Dict[str, Any], fronts: List[Dict[str, Any]]) -> Dict[str, Any]:
    wx = w.get("weather")
    if not isinstance(wx, dict):
        wx = {"dominant": "clear", "avg_intensity": 0.0, "fronts": []}
    wx.setdefault("dominant", "clear")
    wx.setdefault("avg_intensity", 0.0)
    wx["fronts"] = list(fronts[:4])
    w["weather"] = wx
    return wx

def _ensure_zone_weather(z: Dict[str, Any]) -> Dict[str, Any]:
    wz = z.get("weather")
    if not isinstance(wz, dict):
        wz = {"state": "clear", "intensity": 0.0}
    wz.setdefault("state", "clear")
    wz.setdefault("intensity", 0.0)
    z["weather"] = wz
    return wz

def _current(z: Dict[str, Any]) -> Tuple[str, float]:
    w = (z.get("weather") or {})
    return str(w.get("state", "clear")).lower(), float(w.get("intensity", 0.0))

def _type_micro_baseline(z: Dict[str, Any]) -> Tuple[str, float]:
    ztype = str(z.get("type", "generic")).lower()
    micro = (z.get("micro") or {})
    damp = float(micro.get("dampness", 0.0))
    rough = float(micro.get("roughness", 0.0))

    pool = TYPE_BASELINES.get(ztype, TYPE_BASELINES["generic"])
    score = {pool[0]: 0.6, pool[1]: 0.5, pool[2]: 0.4}
    score["mist"] = score.get("mist", 0.0) + 0.6 * damp
    score["rain"] = score.get("rain", 0.0) + 0.4 * max(0.0, damp - 0.4)
    score["dust"] = score.get("dust", 0.0) + 0.5 * max(0.0, rough - 0.5)
    score["haze"] = score.get("haze", 0.0) + 0.3 * rough

    state = max(score.items(), key=lambda kv: kv[1])[0]
    bias = min(1.0, max(0.0, score[state] / 1.6))
    return state, bias

def _neighbor_weather(zid: str, zones: Dict[str, Any], links: Dict[str, List[str]]) -> Tuple[str, float]:
    neigh = links.get(zid, []) or []
    if not neigh:
        return _current(zones.get(zid, {}))
    tally: Dict[str, int] = {}
    acc_i = 0.0
    n = 0
    for lid in neigh:
        s, i = _current(zones.get(lid, {}))
        if not s:
            continue
        tally[s] = tally.get(s, 0) + 1
        acc_i += i; n += 1
    if not tally:
        return _current(zones.get(zid, {}))
    state = max(tally.items(), key=lambda kv: kv[1])[0]
    return state, (acc_i / n if n else 0.0)

def _pick_any_zone(zones: Dict[str, Any], rng: random.Random) -> Optional[str]:
    if not zones:
        return None
    return rng.choice(list(zones.keys()))

def _pick_front_kind(rng: random.Random) -> str:
    choices = ["rain", "storm", "haze", "dust", "gloom", "soft_light"]
    weights = [2, 2, 1, 1, 1, 1]
    return rng.choices(choices, weights=weights, k=1)[0]

def _vote_state(candidates: List[Optional[str]], default: str) -> str:
    tally: Dict[str, int] = {}
    for s in candidates:
        if not s:
            continue
        ss = str(s)
        tally[ss] = tally.get(ss, 0) + 1
    if not tally:
        return default
    return max(tally.items(), key=lambda kv: kv[1])[0]

def _hop_distance(src: str, dst: str, links: Dict[str, List[str]], limit: int = 3) -> Optional[int]:
    if not dst:
        return None
    if src == dst:
        return 0
    q = [(src, 0)]
    seen = {src}
    while q:
        at, d = q.pop(0)
        if d >= limit:
            continue
        for n in links.get(at, []) or []:
            if n in seen:
                continue
            if n == dst:
                return d + 1
            seen.add(n); q.append((n, d + 1))
    return None

def _apply_markers(z: Dict[str, Any], state: str, inten: float) -> None:
    ms = set((z.get("markers") or []))
    for rule in MARKER_RULES:
        kind, th, marker, add = (rule + (True,))[:4]
        if state == kind and inten >= float(th):
            if add:
                ms.add(marker)
            else:
                ms.discard(marker)
    z["markers"] = _preserve_order(ms, (z.get("markers") or []))

def _apply_energy_nudge(energy: float, state: str, inten: float) -> float:
    e = float(energy)
    if state in ("rain", "mist"):
        e += ENERGY_WET_COOL * inten
    elif state in ("storm", "gloom"):
        e += ENERGY_STORM_PUMP * inten
    elif state in ("clear", "soft_light", "prismatic"):
        e += ENERGY_CLEAR_WARM * inten
    # Harmonize to world range and precision
    e = max(-1.0, min(12.0, e))
    return round(e, 4)

def _preserve_order(new_set, old_list):
    seen = set()
    out = []
    for v in (old_list or []) + list(new_set or []):
        if v not in seen:
            out.append(v); seen.add(v)
    return out

def _prompt_bias(p: str) -> Tuple[str, float] | None:
    if not p:
        return None
    pairs = [
        (("rain", "downpour", "wet"), "rain"),
        (("storm", "thunder", "lightning"), "storm"),
        (("fog", "mist"), "mist"),
        (("sun", "clear", "bright"), "clear"),
        (("haze", "smog", "dust"), "haze"),
        (("gloom", "dark"), "gloom"),
        (("prism", "rainbow", "veil"), "prismatic"),
    ]
    for keys, label in pairs:
        if any(k in p for k in keys):
            return (label, 1.0)
    return None

def _summarize_world(zones: Dict[str, Any], fronts: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    total_i = 0.0
    for z in zones.values():
        w = (z.get("weather") or {})
        st = str(w.get("state", "clear"))
        counts[st] = counts.get(st, 0) + 1
        total_i += float(w.get("intensity", 0.0))
    top = max(counts.items(), key=lambda kv: kv[1])[0] if counts else "clear"
    return {
        "dominant": top,
        "avg_intensity": round((total_i / max(1, len(zones))), 3),
        "fronts": list(fronts[:8]),  # leave a few more for UI if you like
    }