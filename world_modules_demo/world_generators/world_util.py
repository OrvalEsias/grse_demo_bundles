# engine/world_util.py
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
from datetime import datetime, timezone

# ---- Time/clock integration (safe import) ----
try:
    from engine.world_clock import init_clock as _time_init, advance_time as _time_advance
    _CLOCK_OK = True
except Exception:
    _CLOCK_OK = False

# ---- Optional autonomy (safe import) ----
try:
    from autonomy_engine import update_character_goal as _autonomy_update
    _AUTO_OK = True
except Exception:
    _AUTO_OK = False

# ---- Optional AGI progress (safe import) ----
try:
    from engine.character_util import update_agi_progress as _update_agi_progress
    _AGI_OK = True
except Exception:
    _AGI_OK = False

# ---- UI/Panel memory + timeseries metrics (safe import) ----
try:
    from engine.memory_util import ensure_memory as _ensure_memory  # no-op if already present
except Exception:
    def _ensure_memory(world):  # fallback no-op
        return world

try:
    from engine.metrics_util import (
        ensure_metrics as _ensure_metrics,
        update_density as _metrics_update_density,
    )
except Exception:
    def _ensure_metrics(world):
        return world
    def _metrics_update_density(world, v):
        return world

# Optional validator hook (no-op if not present)
try:
    from engine.validator.world_validator import validate_world_data  # type: ignore
except Exception:
    def validate_world_data(data: Dict[str, Any]) -> list[str]:  # type: ignore
        return []

Number = Union[int, float]

WORLD_DIR = Path("world_state")
WORLD_FILE = WORLD_DIR / "world.json"
ZONES_DIR = Path("zones")  # folder with standalone zone JSONs

# Process-wide lock to serialize world reads/writes across timers/threads
_WORLD_LOCK = threading.Lock()

# ---------- Resonance (shared overlay) tunables ----------
RESONANCE_DECAY_LAM: float = 0.93     # per-tick decay (0.90–0.96 good)
RESONANCE_MAX_MARKERS: int = 50       # cap to keep JSON small
RESONANCE_VIS_THRESH: float = 0.5     # visibility threshold for viewer helpers
RESONANCE_DEFAULT_W: float = 1.0      # default weight bump per call
RESONANCE_DEFAULT_D: float = 0.02     # default density bump per call

# -------- Optional world-step modules (safe fallbacks) --------
def _noop_world(w: Dict[str, Any], *a, **k) -> Dict[str, Any]:
    return w

# Terrain micro-features
try:
    from engine.terrain_noise import step as _terrain_step
except Exception:
    _terrain_step = _noop_world

# Weather (zone→regional drift); accepts prompt
try:
    from engine.weather_engine import step as _weather_step
except Exception:
    _weather_step = _noop_world

# Symbolic diffusion across links; accepts prompt
try:
    from engine.symbolic_diffusion import step as _diffuse_step
except Exception:
    _diffuse_step = _noop_world

# Factions (presence per zone; affinity)
try:
    from engine.faction_engine import step as _faction_step
except Exception:
    _faction_step = _noop_world

# Economy (scarcity & prices)
try:
    from engine.economy_engine import step as _economy_step
except Exception:
    _economy_step = _noop_world

# Quest/event hooks
try:
    from engine.quest_hooks import apply_quest_hooks as _quest_hooks_apply
except Exception:
    _quest_hooks_apply = _noop_world

# Spawn/apply (if you have a spawn pipeline)
try:
    from engine.spawn_engine import apply_spawns as _spawn_apply
except Exception:
    _spawn_apply = _noop_world

# Zone updaters / traits (if present elsewhere)
try:
    from engine.zone_engine import update_zones as _update_zones
except Exception:
    def _update_zones(w: Dict[str, Any], prompt: str = "") -> Dict[str, Any]:
        return w

try:
    from engine.feature_engine import update_features as _update_features
except Exception:
    def _update_features(w: Dict[str, Any], prompt: str = "") -> Dict[str, Any]:
        return w

try:
    from engine.expansion_engine import expand_world as _expand_world
except Exception:
    def _expand_world(w: Dict[str, Any], prompt: str = "") -> Dict[str, Any]:
        return w

# ---------- Time & small helpers ----------
def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _as_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}

def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if isinstance(x, bool):
            return float(int(x))
        return float(x)
    except Exception:
        return default

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

# ---------- Normalizers ----------
def _zones_as_dict(w: Dict[str, Any]) -> Dict[str, Any]:
    z = w.get("zones")
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
        w["zones"] = out
        return out
    w["zones"] = {}
    return w["zones"]

def _features_as_dict(w: Dict[str, Any]) -> Dict[str, Any]:
    feats = w.get("features")
    if not isinstance(feats, dict):
        feats = {}
    # legacy carry-over of top-level individualism
    if "individualism" not in feats and isinstance(w.get("individualism"), (int, float)):
        feats["individualism"] = _safe_float(w["individualism"], 0.0)
    w["features"] = feats
    return feats

def _weather_as_dict(w: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize world['weather'] to a dict summary."""
    wx = w.get("weather")
    if isinstance(wx, dict):
        return wx
    # legacy: string -> dict summary
    if isinstance(wx, str):
        w["weather"] = {"dominant": wx, "avg_intensity": 0.0, "fronts": []}
        return w["weather"]
    w["weather"] = {"dominant": "clear", "avg_intensity": 0.0, "fronts": []}
    return w["weather"]

# ---------- Resonance helpers ----------
def _resonance_bucket() -> Dict[str, Any]:
    # marker weights in "m", overlay density, timestamp counter, provenance
    return {"m": {}, "density": 0.0, "t": 0, "prov": []}

def _resonance_as_dict(w: Dict[str, Any]) -> Dict[str, Any]:
    r = w.get("resonance")
    if not isinstance(r, dict):
        r = {"global": _resonance_bucket(), "zones": {}}
        w["resonance"] = r
        return r
    if "global" not in r or not isinstance(r["global"], dict):
        r["global"] = _resonance_bucket()
    if "zones" not in r or not isinstance(r["zones"], dict):
        r["zones"] = {}
    return r

def add_resonance(
    world: Dict[str, Any],
    scope: str = "global",
    zone: Optional[str] = None,
    markers: Optional[List[str]] = None,
    w: float = RESONANCE_DEFAULT_W,
    d: float = RESONANCE_DEFAULT_D,
    provenance: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Bump shared resonance (global or per-zone).
    - markers: list of marker names (weights accumulate)
    - w: weight added to each marker
    - d: density bump
    - provenance: optional {actor,item,zone,extra...} (kept compact & decayed)
    """
    r = _resonance_as_dict(world)
    bucket: Dict[str, Any]
    if scope == "zone" and zone:
        bucket = r["zones"].setdefault(zone, _resonance_bucket())
    else:
        bucket = r["global"]

    for k in (markers or []):
        bucket["m"][k] = bucket["m"].get(k, 0.0) + float(w)

    bucket["density"] = float(bucket.get("density", 0.0) + float(d))
    bucket["t"] = int(bucket.get("t", 0)) + 1

    if provenance:
        prov = bucket.setdefault("prov", [])
        prov.append({k: provenance[k] for k in list(provenance.keys())[:6]})
        if len(prov) > 32:
            del prov[:-32]  # cap provenance list

    # Trim least-significant markers if over cap
    if len(bucket["m"]) > RESONANCE_MAX_MARKERS:
        for k, _ in sorted(bucket["m"].items(), key=lambda kv: kv[1])[: len(bucket["m"]) - RESONANCE_MAX_MARKERS]:
            bucket["m"].pop(k, None)

def decay_resonance(world: Dict[str, Any], lam: float = RESONANCE_DECAY_LAM) -> None:
    """Exponential decay of resonance weights/density across all buckets."""
    r = _resonance_as_dict(world)
    def _decay_bucket(b: Dict[str, Any]) -> None:
        b["density"] = float(_safe_float(b.get("density", 0.0), 0.0) * lam)
        b["m"] = {k: float(v * lam) for k, v in b.get("m", {}).items() if v * lam > 1e-3}
    _decay_bucket(r["global"])
    for zname, zb in list(r["zones"].items()):
        _decay_bucket(zb)
        if zb["density"] < 1e-5 and not zb["m"]:
            r["zones"].pop(zname, None)

def clear_resonance(world: Dict[str, Any], scope: Optional[str] = None, zone: Optional[str] = None) -> None:
    """Clear overlay (all, global, or specific zone)."""
    r = _resonance_as_dict(world)
    if scope == "zone" and zone:
        r["zones"].pop(zone, None)
        return
    if scope == "global":
        r["global"] = _resonance_bucket()
        return
    world["resonance"] = {"global": _resonance_bucket(), "zones": {}}

def resonance_overlay(world: Dict[str, Any], zone: Optional[str] = None, beta: float = 0.15, gamma: float = 0.35) -> Dict[str, Any]:
    """
    Viewer helper: return overlay markers (thresholded) and combined density
    for a given zone, without mutating world.
    """
    r = _resonance_as_dict(world)
    G = r.get("global", _resonance_bucket())
    Z = r.get("zones", {}).get(zone or "", _resonance_bucket())
    overlay: Dict[str, float] = {}
    for k, v in G["m"].items(): overlay[k] = overlay.get(k, 0.0) + beta * v
    for k, v in Z["m"].items(): overlay[k] = overlay.get(k, 0.0) + gamma * v
    markers = [k for k, v in overlay.items() if v >= RESONANCE_VIS_THRESH]
    density = beta * _safe_float(G.get("density", 0.0), 0.0) + gamma * _safe_float(Z.get("density", 0.0), 0.0)
    return {"markers": markers, "density": float(density)}

# ---------- Defaults & hydration ----------
def get_default_world() -> Dict[str, Any]:
    """Safe default world structure."""
    return {
        "session_seed": int(time.time()) & 0xFFFFFFFF,
        "time": 0,  # integer tick counter (back-compat; clock will upgrade to dict)
        "zones": {},
        "symbolic_density": 0.0,     # global index (smoothed)
        "symbolic_flux": {"rising": [], "falling": []},
        "symbolic_energy": {},
        "features": {"individualism": 0.0},
        "events": [],                # lightweight UI feed
        "world_events": [],
        "quest_events": [],
        "symbolic_energy_history": [],
        "world_age": 0,
        "spiritual_noise": 0.0,
        "media_signal": 0.0,
        "density_log": [],           # legacy graph support
        "active_markers": {},
        "clusters": {},
        "weather": {"dominant": "clear", "avg_intensity": 0.0, "fronts": []},
        "economy": {"zones": {}, "global_index": 0.0, "history": []},
        "factions": {},
        "faction_presence": {},
        "faction_affinity": {},
        "resonance": {"global": _resonance_bucket(), "zones": {}},
        "memory": {"events": [], "max_len": 200},                      # NEW
        "metrics": {                                                   # NEW
            "symbolic_density_history": [],
            "agi_index_history": [],    # optional; harmless to keep
            "tick_index": 0,
            "max_history": 800,
        },
        "last_update": _utcnow_iso(),
    }

def _ensure_paths() -> bool:
    """Ensure world_state/ exists and world.json is not a directory."""
    WORLD_DIR.mkdir(parents=True, exist_ok=True)
    if WORLD_FILE.is_dir():
        print(f"[ERROR] Expected file but found directory: {WORLD_FILE}")
        return False
    return True

def _hydrate_world(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Ensure required keys exist without clobbering existing ones."""
    w = _as_dict(data)
    _zones_as_dict(w)
    _features_as_dict(w)
    _weather_as_dict(w)
    _resonance_as_dict(w)

    w.setdefault("session_seed", int(time.time()) & 0xFFFFFFFF)
    w.setdefault("time", 0)
    w.setdefault("symbolic_density", 0.0)
    w.setdefault("symbolic_flux", {"rising": [], "falling": []})
    w.setdefault("symbolic_energy", {})
    w.setdefault("events", [])
    w.setdefault("world_events", [])
    w.setdefault("quest_events", [])
    w.setdefault("symbolic_energy_history", [])
    w.setdefault("world_age", 0)
    w.setdefault("spiritual_noise", 0.0)
    w.setdefault("media_signal", 0.0)
    w.setdefault("density_log", [])
    w.setdefault("active_markers", {})
    w.setdefault("clusters", {})
    w.setdefault("economy", {"zones": {}, "global_index": 0.0, "history": []})
    w.setdefault("factions", {})
    w.setdefault("faction_presence", {})
    w.setdefault("faction_affinity", {})

    # NEW: ensure memory + metrics structures exist without overwriting
    mem = w.setdefault("memory", {})
    mem.setdefault("events", [])
    mem.setdefault("max_len", 200)

    m = w.setdefault("metrics", {})
    m.setdefault("symbolic_density_history", [])
    m.setdefault("agi_index_history", [])
    m.setdefault("tick_index", 0)
    m.setdefault("max_history", 800)

    w["last_update"] = _utcnow_iso()
    return w

# ---------- Salvage / atomic I/O ----------
def _salvage_first_json(text: str) -> Optional[Dict[str, Any]]:
    """Keep the first valid top-level JSON object; drop trailing garbage if present."""
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        pass
    try:
        dec = json.JSONDecoder()
        obj, _ = dec.raw_decode(text.strip())
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return None

def _atomic_write_json(path: Path, data: Dict[str, Any], *, retries: int = 2, delay_s: float = 0.01) -> None:
    """Atomic JSON write with small retry loop."""
    attempt = 0
    last_err: Optional[Exception] = None
    while attempt <= retries:
        tmp_fd, tmp_path = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, path)
            return
        except Exception as e:
            last_err = e
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            attempt += 1
            time.sleep(delay_s)
    if last_err:
        raise last_err

def _rotate_corrupt_backup(src: Path) -> None:
    """Keep a single .corrupt backup; if exists, add timestamped one."""
    corrupt = src.with_suffix(".corrupt")
    try:
        if not corrupt.exists():
            os.replace(src, corrupt)
            return
        ts = time.strftime("%Y%m%d-%H%M%S")
        os.replace(src, src.with_name(f"{src.stem}.{ts}.corrupt"))
    except Exception:
        pass

# ---------- Standalone zone loader ----------
def _zone_defaults(z: Dict[str, Any], fallback_name: str) -> Dict[str, Any]:
    # Ensure minimal shape and sensible defaults
    name = str(z.get("name") or z.get("id") or fallback_name)
    z["name"] = name
    z.setdefault("label", name.replace("_", " ").title())
    z.setdefault("type", "wild")  # gate | market | ruin | archive | wild | generic
    en = _safe_float(z.get("energy", z.get("symbolic_density", 0.0)), 0.0)
    z["energy"] = float(en)
    z["symbolic_density"] = float(_safe_float(z.get("symbolic_density", en), en))
    z.setdefault("spiritual_noise", 0.0)
    z.setdefault("media_signal", 0.0)
    z.setdefault("items", [])
    z.setdefault("traits", [])
    z.setdefault("markers", [])
    z.setdefault("links", [])
    z.setdefault("rules", {})
    z.setdefault("weather", {})
    z.setdefault("history", [])
    z.setdefault("timers", {})
    z.setdefault("version", "1.0.0")
    return z

def _load_zones_from_dir(directory: Path) -> Dict[str, Dict[str, Any]]:
    """
    Reads *.json from `directory` and returns {zone_name: zone_dict}.
    Non-crashing: skips files that aren’t valid dicts.
    """
    out: Dict[str, Dict[str, Any]] = {}
    if not directory.exists() or not directory.is_dir():
        return out
    for p in sorted(directory.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                name = (data.get("name") or data.get("id") or p.stem)
                out[name] = _zone_defaults(data, fallback_name=p.stem)
        except Exception as e:
            print(f"[WARN] Could not load zone '{p}': {e}")
    return out

def _autolink_ring(zones: Dict[str, Dict[str, Any]]) -> None:
    """
    Create a simple ring of links among all zones that currently have none.
    Leaves existing links intact.
    """
    keys = [k for k, _ in zones.items()]
    n = len(keys)
    if n <= 1:
        return
    for i, k in enumerate(keys):
        z = zones[k]
        z.setdefault("links", [])
        if z["links"]:
            continue
        a = keys[(i - 1) % n]
        b = keys[(i + 1) % n]
        for t in (a, b):
            if t != k and t not in z["links"]:
                z["links"].append(t)

def _merge_loaded_zones(world: Dict[str, Any], loaded: Dict[str, Dict[str, Any]], *, overwrite: bool = False) -> None:
    """
    Merge loaded zones into world['zones'].
    - overwrite=False keeps existing zones and only adds new ones
    """
    zones = _zones_as_dict(world)
    for name, z in loaded.items():
        if name in zones and not overwrite:
            continue
        zones[name] = z

# ---------- Persistence ----------
def save_world(world_data: Dict[str, Any]) -> None:
    """Atomic write with locking to avoid races between timers."""
    if not _ensure_paths():
        return
    hydrated = _hydrate_world(world_data)
    with _WORLD_LOCK:
        _atomic_write_json(WORLD_FILE, hydrated)

def load_world() -> Dict[str, Any]:
    """
    Load, salvage if needed, hydrate, validate, and (if needed) auto-save world data.
    Guarantees presence of density_log and other required keys.
    """
    if not _ensure_paths():
        print("[WARN] Using default world due to path issue.")
        return get_default_world()

    with _WORLD_LOCK:
        if not WORLD_FILE.exists():
            print(f"[WARN] {WORLD_FILE} not found. Creating default world.")
            w = get_default_world()
            _atomic_write_json(WORLD_FILE, w)

        # Load JSON (with salvage)
        try:
            raw = WORLD_FILE.read_text(encoding="utf-8")
            data = _salvage_first_json(raw)
            if data is None:
                _rotate_corrupt_backup(WORLD_FILE)
                data = get_default_world()
                _atomic_write_json(WORLD_FILE, data)
        except Exception as e:
            print(f"[ERROR] Failed to read {WORLD_FILE}: {e}")
            data = get_default_world()
            _atomic_write_json(WORLD_FILE, data)

    if not isinstance(data, dict):
        print("[WARNING] world.json is not a dict. Resetting to default.")
        w = get_default_world()
        save_world(w)
        return w

    # Preserve legacy density_log across hydration/validation
    orig_dl = data.get("density_log", [])
    if not isinstance(orig_dl, list):
        orig_dl = []

    # Hydrate required keys
    w = _hydrate_world(data)

    # Validate (some validators strip unknown keys)
    try:
        corrections = validate_world_data(w)
    except Exception as e:
        print(f"[WARN] validate_world_data failed: {e}")
        corrections = []

    # Ensure density_log wasn't dropped/shortened by hydration/validation
    if not isinstance(w.get("density_log"), list) or len(w["density_log"]) < len(orig_dl):
        w["density_log"] = orig_dl
        corrections = corrections or ["restored density_log from disk"]

    if corrections:
        print("[WorldValidator] Corrections made:")
        for fix in corrections:
            print(" -", fix)
        try:
            save_world(w)  # persist corrected/hydrated/restored data
        except Exception as e:
            print(f"[ERROR] Could not save corrected world: {e}")

    # ---- Load standalone zones (./zones/*.json) and merge (no overwrite by default) ----
    try:
        loaded = _load_zones_from_dir(ZONES_DIR)
        if loaded:
            _merge_loaded_zones(w, loaded, overwrite=False)
            _autolink_ring(_zones_as_dict(w))
    except Exception as e:
        print(f"[WARN] load_world: could not load zones from {ZONES_DIR}: {e}")

    # Ensure panel memory + metrics exist (no reinit)
    _ensure_memory(w)
    _ensure_metrics(w)

    # Trim noisy arrays to keep JSON small
    _compact_world_inplace(w)
    return w

# ---------- Feature helpers ----------
def _feature_add(world_features: Dict[str, Any], key: str, amount: Number) -> None:
    """Support both numeric features and dict features with 'value'."""
    cur = world_features.get(key)
    if isinstance(cur, dict) and "value" in cur:
        cur_val = _safe_float(cur.get("value", 0.0), 0.0)
        cur["value"] = float(cur_val + float(amount))
        world_features[key] = cur
    else:
        world_features[key] = float(_safe_float(cur, 0.0) + float(amount))

# ---------- World mutation helpers (public API kept) ----------
def update_zone_density(world_data: Dict[str, Any], zone_name: str, delta: float) -> None:
    """Adjusts the symbolic density of a given zone (kept for backward compat)."""
    zones = _zones_as_dict(world_data)
    zone = zones.setdefault(zone_name, {})
    sd = _safe_float(zone.get("symbolic_density", zone.get("density", 0.0)), 0.0)
    zone["symbolic_density"] = float(sd + float(delta))
    if "density" in zone:
        zone["density"] = zone["symbolic_density"]

def modify_symbolic_energy(world_data: Dict[str, Any], key: str, amount: float) -> None:
    """Modifies the symbolic energy value for a specific key."""
    se = world_data.setdefault("symbolic_energy", {})
    se[key] = float(_safe_float(se.get(key, 0.0), 0.0) + float(amount))

# ---------- Delta calculation (compat) ----------
def calculate_world_delta(character: Dict[str, Any], world: Dict[str, Any], interpretation: Dict[str, Any]) -> Dict[str, Any]:
    """Compute world delta from interpretation (same signature as before)."""
    delta: Dict[str, Any] = {}

    zone = character.get("zone", world.get("active_zone", "dream_gate"))
    zone_data = _as_dict(_zones_as_dict(world).get(zone, {}))
    current_energy = _safe_float(zone_data.get("energy", 0.0), 0.0)

    num_markers = len(interpretation.get("detected_markers", [])) if isinstance(interpretation, dict) else 0
    intent = (interpretation.get("intent", "") if isinstance(interpretation, dict) else "") or ""

    spiritual_noise = _safe_float(world.get("spiritual_noise", 0.0), 0.0)
    media_signal = _safe_float(world.get("media_signal", 0.0), 0.0)

    energy_boost = 0.1 * num_markers
    if intent == "transform":
        energy_boost += 0.2
    updated_energy = _clamp(current_energy + energy_boost, -1.0, 12.0)

    delta["zones"] = {
        zone: {
            "energy": updated_energy,
            "symbolic_density": updated_energy,  # keep them aligned for UI
            "last_update": interpretation.get("summary", "unknown effect") if isinstance(interpretation, dict) else "unknown"
        }
    }

    if num_markers > 0:
        delta["spiritual_noise"] = spiritual_noise + 0.05 * num_markers
        # hint resonance overlay from markers detected
        delta.setdefault("resonance", {}).setdefault("zones", {}).setdefault(zone, {})["markers"] = interpretation.get("detected_markers", [])
        delta["resonance"]["zones"][zone]["w"] = 1.0
        delta["resonance"]["zones"][zone]["d"] = 0.02

    if intent == "broadcast":
        delta["media_signal"] = media_signal + 0.1
        # broadcast tends to be global resonance too
        delta.setdefault("resonance", {}).setdefault("global", {})["markers"] = ["broadcast_signal"]
        delta["resonance"]["global"]["w"] = 0.7
        delta["resonance"]["global"]["d"] = 0.02

    # Optional: mirror into features
    feats = world.get("features") or {}
    if "spiritual_noise" in feats and num_markers > 0:
        delta.setdefault("features", {})["spiritual_noise"] = 0.05 * num_markers
    if "media_signal" in feats and intent == "broadcast":
        delta.setdefault("features", {})["media_signal"] = 0.1

    return delta

# ---------- Delta apply ----------
def apply_world_delta(world: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply symbolic deltas to the world state.
    - merges zones entries
    - adds to numeric features or to 'value' if feature is a dict
    - writes a lightweight snapshot into symbolic_energy_history
    - updates last_update
    - integrates shared resonance overlay if present
    """
    _features_as_dict(world)
    _zones_as_dict(world)
    _weather_as_dict(world)
    _resonance_as_dict(world)

    for key, change in (delta or {}).items():
        # Features delta (additive)
        if key == "features" and isinstance(change, dict):
            for f_key, f_val in change.items():
                _feature_add(world["features"], f_key, _safe_float(f_val, 0.0))
            continue

        # Zones merge (+ pick up marker hints for resonance)
        if key == "zones" and isinstance(change, dict):
            for zone_name, zone_data in change.items():
                z = world["zones"].setdefault(zone_name, {})
                if isinstance(zone_data, dict):
                    for k, v in zone_data.items():
                        if isinstance(v, (int, float)):
                            z[k] = float(v)
                        else:
                            z[k] = v
                    # if caller included markers/marker_add, feed resonance
                    markers = []
                    if isinstance(zone_data.get("markers"), list):
                        markers += [str(m) for m in zone_data["markers"]]
                    if isinstance(zone_data.get("markers_added"), list):
                        markers += [str(m) for m in zone_data["markers_added"]]
                    if markers:
                        add_resonance(world, scope="zone", zone=zone_name, markers=markers, w=1.0, d=0.02)
                else:
                    world["zones"][zone_name] = zone_data
            continue

        # Global scalar fields we know
        if key in ("spiritual_noise", "media_signal", "world_age", "symbolic_density"):
            world[key] = float(_safe_float(change, 0.0))
            continue

        # Direct resonance delta
        if key == "resonance" and isinstance(change, dict):
            g = change.get("global")
            if isinstance(g, dict):
                add_resonance(
                    world,
                    scope="global",
                    markers=[str(m) for m in g.get("markers", [])],
                    w=_safe_float(g.get("w", RESONANCE_DEFAULT_W), RESONANCE_DEFAULT_W),
                    d=_safe_float(g.get("d", RESONANCE_DEFAULT_D), RESONANCE_DEFAULT_D),
                )
            zs = change.get("zones", {})
            if isinstance(zs, dict):
                for zn, zc in zs.items():
                    if not isinstance(zc, dict):
                        continue
                    add_resonance(
                        world,
                        scope="zone",
                        zone=str(zn),
                        markers=[str(m) for m in zc.get("markers", [])],
                        w=_safe_float(zc.get("w", RESONANCE_DEFAULT_W), RESONANCE_DEFAULT_W),
                        d=_safe_float(zc.get("d", RESONANCE_DEFAULT_D), RESONANCE_DEFAULT_D),
                    )
            continue

        # Fallback: treat as symbolic_energy component bump
        modify_symbolic_energy(world, key, _safe_float(change, 0.0))

    # Maintain legacy density_log (only if global density present)
    if isinstance(world.get("symbolic_density"), (int, float)):
        dl = world.setdefault("density_log", [])
        if isinstance(dl, list):
            dl.append(float(world["symbolic_density"]))
            world["density_log"] = dl[-300:]

    # Append a compact history entry
    se_hist = world.setdefault("symbolic_energy_history", [])
    try:
        se_hist.append({
            "timestamp": _utcnow_iso(),
            "zones": {k: {"energy": _safe_float(v.get("energy", 0.0), 0.0)}
                      for k, v in _zones_as_dict(world).items() if isinstance(v, dict)},
            "features": world.get("features", {}),
        })
        if len(se_hist) > 300:
            del se_hist[:-300]
    except Exception:
        pass

    # Bubble up an agency log if delta had a machine-readable world_effects hint
    if "world_effects" in delta:
        _record_agency(world, delta.get("world_effects"))

    world["last_update"] = _utcnow_iso()
    _compact_world_inplace(world)
    return world

# ---------- Agency log ----------
def _record_agency(world: Dict[str, Any], effects: Any) -> None:
    if not effects:
        return
    log = world.setdefault("agency_log", [])
    log.append({"t": _utcnow_iso(), "effects": effects})
    if len(log) > 300:
        del log[:-300]

# ---------- Compaction (keep world.json small) ----------
def _compact_world_inplace(world: Dict[str, Any]) -> None:
    try:
        # Cap sizes to keep disk small and UI snappy
        for k, cap in (("events", 400), ("world_events", 800), ("quest_events", 400)):
            if isinstance(world.get(k), list) and len(world[k]) > cap:
                del world[k][:-cap]
        if isinstance(world.get("density_log"), list) and len(world["density_log"]) > 300:
            del world["density_log"][:-300]
        if isinstance(world.get("symbolic_energy_history"), list) and len(world["symbolic_energy_history"]) > 300:
            del world["symbolic_energy_history"][:-300]
        if isinstance(world.get("agency_log"), list) and len(world["agency_log"]) > 300:
            del world["agency_log"][:-300]

        # NEW: cap metrics histories
        if isinstance(world.get("metrics"), dict):
            mh = int(world["metrics"].get("max_history", 800) or 800)
            if isinstance(world["metrics"].get("symbolic_density_history"), list):
                if len(world["metrics"]["symbolic_density_history"]) > mh:
                    del world["metrics"]["symbolic_density_history"][:-mh]
            if isinstance(world["metrics"].get("agi_index_history"), list):
                if len(world["metrics"]["agi_index_history"]) > mh:
                    del world["metrics"]["agi_index_history"][:-mh]
    except Exception:
        pass

# ---------- Tick helpers & autorun pipeline ----------
def _tick(world: Dict[str, Any]) -> Dict[str, Any]:
    """Advance world time via the clock and ensure structure."""
    w = _hydrate_world(world)
    if _CLOCK_OK:
        try:
            w = _time_init(w)
            w = _time_advance(w, steps=1.0)
        except Exception:
            # fall back to legacy integer tick if clock fails
            w["time"] = int(w.get("time", 0)) + 1
    else:
        w["time"] = int(w.get("time", 0)) + 1
    w["last_update"] = _utcnow_iso()
    return w

def autorun_world_tick(world_state: Dict[str, Any], prompt: str = "") -> Dict[str, Any]:
    """
    One full world tick with safe fallbacks.
    Order matters (early signals feed later systems):
      1) _tick (time/structure)
      2) terrain micro-features
      3) weather (prompt-coupled)
      4) symbolic diffusion (prompt-coupled)
      5) factions
      6) economy
      7) spawns (optional)
      8) zone updates / feature updates / expansion
      9) quest hooks (after most fields stabilized)
      10) autonomy refresh (optional)
      11) AGI progress update (optional)
      12) resonance decay
      13) metrics heartbeat (append density)
    """
    with _WORLD_LOCK:
        w = _tick(world_state)

        # Early passes
        w = _terrain_step(w)
        w = _weather_step(w, prompt=prompt) if _weather_step is not _noop_world else _weather_step(w)
        w = _diffuse_step(w, prompt=prompt) if _diffuse_step is not _noop_world else _diffuse_step(w)

        # Mid passes
        w = _faction_step(w)
        w = _economy_step(w)
        w = _spawn_apply(w)

        # Late passes (react to most-updated fields)
        w = _update_zones(w, prompt)
        w = _update_features(w, prompt)
        w = _expand_world(w, prompt)

        # Quest/event hooks
        w = _quest_hooks_apply(w)

        # Optional autonomy: refresh character goal each tick
        if _AUTO_OK:
            try:
                pc = w.get("primary_character") or w.get("character")
                if isinstance(pc, dict):
                    _autonomy_update(pc, w)
            except Exception:
                pass

        # Optional AGI progress: update momentum/streak
        if _AGI_OK:
            try:
                pc = w.get("primary_character") or w.get("character")
                if isinstance(pc, dict):
                    _update_agi_progress(pc, w)
            except Exception:
                pass

        # Resonance decay heartbeat
        try:
            decay_resonance(w, lam=RESONANCE_DECAY_LAM)
        except Exception as e:
            print("[WARN] autorun_world_tick: resonance decay failed:", e)

        # Persist legacy density_log heartbeat for graphs if global index present
        try:
            dl = w.setdefault("density_log", [])
            dl.append(float(w.get("symbolic_density", 0.0)))
            w["density_log"] = dl[-300:]
        except Exception:
            pass

        # NEW: metrics heartbeat for Symbolic Density Graph
        try:
            _ensure_metrics(w)  # ensure exists without reinit
            _metrics_update_density(w, float(w.get("symbolic_density", 0.0)))
        except Exception as e:
            print("[WARN] autorun_world_tick: metrics update failed:", e)

        # Save-on-tick (optional—comment out if you prefer external control)
        try:
            _atomic_write_json(WORLD_FILE, _hydrate_world(w))
        except Exception as e:
            print("[WARN] autorun_world_tick: could not save world:", e)

        _compact_world_inplace(w)
        return w
