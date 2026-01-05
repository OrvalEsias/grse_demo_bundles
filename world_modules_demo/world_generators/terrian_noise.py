# engine/terrain_noise.py
# Seeded, deterministic micro-features per zone (no external deps).
from __future__ import annotations
from typing import Dict, Any, Tuple

# Public API ---------------------------------------------------------------

def step(world: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute stable micro-features for every zone based on zone id+seed.
    Writes to zone['micro'] and may add lightweight markers when thresholds cross.
    Pure & deterministic: same world/zones -> same outputs.
    """
    zones = world.get("zones", {}) or {}
    if not isinstance(zones, dict):
        return world

    for zid, z in zones.items():
        z.setdefault("seed", _fallback_seed(world, zid))
        cx, cy = _zone_coords_from_id(zid)
        s = int(z.get("seed", 0)) ^ _hash32(zid)

        # Multi-octave value noise in 0..1
        elev = _fbm(cx, cy, s ^ 0xE1, octaves=4, base_freq=0.015)  # elevation
        damp = _fbm(cx, cy, s ^ 0xA5, octaves=3, base_freq=0.022)  # dampness
        rough = _fbm(cx, cy, s ^ 0xC3, octaves=3, base_freq=0.035) # surface roughness
        anomaly_raw = _fbm(cx+77.0, cy-33.0, s ^ 0x5B, octaves=2, base_freq=0.045)
        anomaly = max(0.0, min(1.0, (anomaly_raw * 1.15) - 0.075))

        # Normalize a touch for nicer spreads
        elev = _remap(elev, 0.05, 0.95, clamp=True)
        damp = _remap(damp, 0.05, 0.95, clamp=True)
        rough = _remap(rough, 0.05, 0.95, clamp=True)
        anomaly = _remap(anomaly, 0.00, 0.98, clamp=True)

        micro = {
            "elevation": round(elev, 3),
            "dampness": round(damp, 3),
            "roughness": round(rough, 3),
            "anomaly": round(anomaly, 3),
        }
        z["micro"] = micro

        # Optional: tag markers based on thresholds (non-destructive)
        markers = set(z.get("markers", []) or [])
        if micro["dampness"] >= 0.75:
            markers.add("sodden_floor")
        if micro["elevation"] <= 0.15 and micro["dampness"] >= 0.6:
            markers.add("standing_pools")
        if micro["roughness"] >= 0.8:
            markers.add("jagged_passage")
        if micro["anomaly"] >= 0.85:
            markers.add("echo_pockets")
        if markers:
            z["markers"] = _dedup_preserve_order(list(markers), keep_order_from=z.get("markers", []))

        # Optional: nudge zone 'energy' slightly but deterministically
        # (kept tiny so it won't fight your main engines)
        base_energy = float(z.get("energy", 0.0))
        z["energy"] = round(_soft_energy_adjust(base_energy, micro), 3)

        zones[zid] = z

    world["zones"] = zones
    return world

# Internals ----------------------------------------------------------------

def _fallback_seed(world: Dict[str, Any], zid: str) -> int:
    """Use world['session_seed'] and zone id hash when zone.seed is missing."""
    return int(world.get("session_seed", 0)) ^ _hash32(zid)

def _zone_coords_from_id(zid: str) -> Tuple[float, float]:
    """
    Derive pseudo 2D coords from zone id so noise fields vary across zones
    even without explicit coordinates.
    """
    h = _hash64(zid)
    # Spread zones on a large ring-ish pattern for nice variation
    x = ((h & 0xFFFFFFFF) / 0xFFFFFFFF) * 1000.0
    y = (((h >> 32) & 0xFFFFFFFF) / 0xFFFFFFFF) * 1000.0
    return (x, y)

def _soft_energy_adjust(e: float, micro: Dict[str, float]) -> float:
    """
    Tiny, bounded adjustment from micro-features:
    - high dampness & low elevation cool energy slightly
    - anomaly & roughness give a small boost
    Net in [-0.03, +0.04] range.
    """
    delta = 0.0
    delta -= 0.03 * _sat01(micro.get("dampness", 0.0) * (1.0 - micro.get("elevation", 0.0)))
    delta += 0.02 * micro.get("roughness", 0.0)
    delta += 0.02 * micro.get("anomaly", 0.0)
    out = e + delta
    # keep within sensible bounds
    return max(0.0, min(1.0, out))

def _dedup_preserve_order(values, keep_order_from=None):
    keep_order_from = keep_order_from or []
    seen = set()
    out = []
    for v in keep_order_from + values:
        if v not in seen:
            out.append(v); seen.add(v)
    return out

# --- Noise utilities (fast value noise; no external libs) -----------------

def _remap(x: float, lo: float, hi: float, *, clamp: bool = False) -> float:
    if hi == lo:
        return 0.0
    t = (x - 0.0) / 1.0  # x already in 0..1
    y = lo + t * (hi - lo)
    if clamp:
        y = max(min(y, hi), lo)
    return y

def _sat01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x

def _hash32(x: str | int) -> int:
    if isinstance(x, int):
        v = x & 0xFFFFFFFF
    else:
        v = 2166136261
        for ch in x.encode("utf-8"):
            v ^= ch
            v = (v * 16777619) & 0xFFFFFFFF
    # final avalanche
    v ^= (v >> 16); v = (v * 0x7feb352d) & 0xFFFFFFFF
    v ^= (v >> 15); v = (v * 0x846ca68b) & 0xFFFFFFFF
    v ^= (v >> 16)
    return v & 0xFFFFFFFF

def _hash64(x: str) -> int:
    # simple 64-bit mix from two 32-bit hashes (string doubled)
    a = _hash32(x)
    b = _hash32(x + "#")
    return ((a << 32) ^ b) & 0xFFFFFFFFFFFFFFFF

def _rand_grad(ix: int, iy: int, seed: int) -> float:
    """Deterministic pseudo-random in [0,1) for integer grid point."""
    h = (seed + 374761393*ix + 668265263*iy) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFFFF) / 0x100000000

def _smoothstep(t: float) -> float:
    return t * t * (3 - 2 * t)

def _value_noise(x: float, y: float, seed: int) -> float:
    """Value noise in [0,1] using 2D grid interpolation."""
    x0 = int(x); y0 = int(y)
    xf = x - x0; yf = y - y0
    v00 = _rand_grad(x0,   y0,   seed)
    v10 = _rand_grad(x0+1, y0,   seed)
    v01 = _rand_grad(x0,   y0+1, seed)
    v11 = _rand_grad(x0+1, y0+1, seed)
    u = _smoothstep(xf); v = _smoothstep(yf)
    a = v00 + (v10 - v00) * u
    b = v01 + (v11 - v01) * u
    return a + (b - a) * v  # already ~[0,1]

def _fbm(x: float, y: float, seed: int, *, octaves: int = 4, base_freq: float = 0.02, lacunarity: float = 2.0, gain: float = 0.5) -> float:
    """
    Fractal Brownian Motion over value noise → smoother terrain-like signals.
    Returns 0..1.
    """
    amp = 1.0
    freq = base_freq
    sumv = 0.0
    norm = 0.0
    for _ in range(max(1, int(octaves))):
        sumv += amp * _value_noise(x * freq * 100.0, y * freq * 100.0, seed)
        norm += amp
        amp *= gain
        freq *= lacunarity
    if norm <= 0: 
        return 0.0
    v = sumv / norm
    return max(0.0, min(1.0, v))
