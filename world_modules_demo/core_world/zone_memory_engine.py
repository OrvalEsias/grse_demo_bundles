# engine/zone_memory_engine.py
from __future__ import annotations
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timezone

# --- Tunables (safe defaults) ---
MAX_TRACE_LEN: int = 64          # hard cap to prevent unbounded growth
DEFAULT_DECAY: float = 0.05      # linear decay per tick
MERGE_WINDOW_SEC: int = 60       # merge same event if within this window
STRENGTH_MIN: float = 0.0
STRENGTH_MAX: float = 1.0

def _utc_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())

def _clamp(x: float, lo: float = STRENGTH_MIN, hi: float = STRENGTH_MAX) -> float:
    return lo if x < lo else hi if x > hi else x

def _maybe_merge(trace: List[Dict], event: str, ts: int, add_strength: float) -> bool:
    """
    If the same event occurred within MERGE_WINDOW_SEC, reinforce it instead of appending.
    Returns True if merged.
    """
    if not trace:
        return False
    cutoff = ts - MERGE_WINDOW_SEC
    for m in reversed(trace):  # scan recent first
        if m.get("event") == event and m.get("ts", 0) >= cutoff:
            m["strength"] = _clamp(m.get("strength", 1.0) + add_strength)
            m["count"] = int(m.get("count", 1)) + 1
            m["ts"] = ts
            return True
    return False

def update_zone_memory(
    zone: Dict,
    event: str,
    strength: float = 1.0,
    *,
    tags: Optional[List[str]] = None,
    ts: Optional[int] = None
) -> Dict:
    """
    Add (or reinforce) a memory event to the zone.
    - strength is clamped into [0,1]
    - recent duplicate events are merged (reinforced) instead of appended
    - maintains MAX_TRACE_LEN cap (drops weakest)
    """
    zone.setdefault("memory_trace", [])
    trace = zone["memory_trace"]
    ts = ts or _utc_ts()
    strength = _clamp(strength)

    # Merge with a very recent identical event (keeps noise down)
    if not _maybe_merge(trace, event, ts, add_strength=strength * 0.5):
        trace.append({
            "event": event,
            "strength": strength,
            "ts": ts,
            "tags": list(tags) if tags else [],
            "count": 1
        })

    # Enforce cap by dropping weakest memories first
    if len(trace) > MAX_TRACE_LEN:
        trace.sort(key=lambda m: (m.get("strength", 0.0), m.get("ts", 0)), reverse=True)
        del trace[MAX_TRACE_LEN:]

    return zone

def decay_zone_memory(
    zone: Dict,
    decay_rate: float = DEFAULT_DECAY,
    *,
    mode: str = "linear"  # "linear" or "exp"
) -> Dict:
    """
    Decay all memory strengths.
    - linear: strength -= decay_rate
    - exp:    strength *= (1 - decay_rate)
    Removes entries that fall to 0.
    """
    trace = zone.get("memory_trace", [])
    if not trace:
        return zone

    updated: List[Dict] = []
    for m in trace:
        s = float(m.get("strength", 0.0))
        if mode == "exp":
            s = s * (1.0 - decay_rate)
        else:
            s = s - decay_rate
        s = _clamp(round(s, 4))
        if s > STRENGTH_MIN:
            m["strength"] = s
            updated.append(m)
    zone["memory_trace"] = updated
    return zone

def summarize_memory(
    zone: Dict,
    *,
    top_n: Optional[int] = None,
    order: str = "strength"  # "strength" | "recent"
) -> List[str]:
    """
    Return human-readable summaries of memory events.
    order:
      - "strength": strongest first
      - "recent":   newest first
    """
    trace = zone.get("memory_trace", [])
    if not trace:
        return []

    if order == "recent":
        sorted_trace = sorted(trace, key=lambda m: m.get("ts", 0), reverse=True)
    else:
        sorted_trace = sorted(trace, key=lambda m: (m.get("strength", 0.0), m.get("ts", 0)), reverse=True)

    if top_n is not None:
        sorted_trace = sorted_trace[:top_n]

    out: List[str] = []
    for m in sorted_trace:
        tags = f" tags={m.get('tags', [])}" if m.get("tags") else ""
        cnt  = f" x{m.get('count', 1)}" if m.get("count", 1) > 1 else ""
        out.append(f"{m.get('event','?')}{cnt} ({m.get('strength',0.0):.2f}){tags}")
    return out

# Convenience: clear or trim APIs

def trim_zone_memory(zone: Dict, max_len: int = MAX_TRACE_LEN) -> Dict:
    """
    Keep only the strongest/recent up to max_len.
    """
    trace = zone.get("memory_trace", [])
    if not trace:
        return zone
    trace.sort(key=lambda m: (m.get("strength", 0.0), m.get("ts", 0)), reverse=True)
    zone["memory_trace"] = trace[:max_len]
    return zone

def clear_zone_memory(zone: Dict) -> Dict:
    zone["memory_trace"] = []
    return zone
