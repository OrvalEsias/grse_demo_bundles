# engine/world_clock.py

from __future__ import annotations
from typing import Dict, Any
import math

# Defaults
DEFAULT_HOURS_PER_TICK: float = 1.0  # how many in-world hours pass per tick
NIGHT_HOURS = (20, 5)                # 20:00..23:59 and 00:00..04:59 considered "night"

def _emit(evt: Dict[str, Any], world: Dict[str, Any]) -> None:
    """Best-effort event emission (optional)."""
    try:
        from engine.event_bus import emit  # type: ignore
        emit(evt, world)
    except Exception:
        pass

def init_clock(world: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure world['time'] is initialized."""
    t = world.setdefault("time", {})
    t.setdefault("tick", 0)                      # integer tick counter
    t.setdefault("hours_per_tick", DEFAULT_HOURS_PER_TICK)
    t.setdefault("total_hours", 0.0)             # running fractional hour counter
    # Derive day/hour from total_hours
    day = int(t.get("total_hours", 0.0) // 24)
    hour = int(t.get("total_hours", 0.0) % 24)
    t["day"] = day
    t["hour"] = hour
    return world

def set_time_scale(world: Dict[str, Any], hours_per_tick: float) -> Dict[str, Any]:
    """Change simulation time scale (hours progressed per tick)."""
    world = init_clock(world)
    world["time"]["hours_per_tick"] = max(0.0, float(hours_per_tick))
    return world

def is_night(world: Dict[str, Any]) -> bool:
    """True if current hour is considered night."""
    world = init_clock(world)
    h = int(world["time"]["hour"])
    start, end = NIGHT_HOURS
    return (h >= start) or (h < end)

def get_time(world: Dict[str, Any]) -> Dict[str, Any]:
    """Small summary of time state."""
    world = init_clock(world)
    t = world["time"]
    return {
        "tick": int(t["tick"]),
        "day": int(t["day"]),
        "hour": int(t["hour"]),
        "is_night": is_night(world),
        "hours_per_tick": float(t["hours_per_tick"]),
        "total_hours": float(t["total_hours"]),
    }

def advance_time(world: Dict[str, Any], steps: float = 1.0) -> Dict[str, Any]:
    """
    Advance simulation time by `steps` ticks (can be fractional).
    Updates tick, total_hours, day, hour. Emits WorldTimeAdvanced.
    """
    world = init_clock(world)
    t = world["time"]

    steps = float(steps)
    if steps <= 0:
        return world

    # Advance counters
    t["tick"] = int(t["tick"]) + int(math.floor(steps))
    add_hours = steps * float(t["hours_per_tick"])
    t["total_hours"] = float(t["total_hours"]) + add_hours
    t["day"] = int(t["total_hours"] // 24)
    t["hour"] = int(t["total_hours"] % 24)

    _emit({
        "type": "WorldTimeAdvanced",
        "tick": int(t["tick"]),
        "day": int(t["day"]),
        "hour": int(t["hour"]),
        "added_hours": float(add_hours),
        "hours_per_tick": float(t["hours_per_tick"]),
    }, world)

    return world

# Compatibility shim (your original signature)
def tick(world: Dict[str, Any], dt: float = 1.0) -> Dict[str, Any]:
    """
    Compatibility wrapper: advances time by dt ticks (dt may be fractional).
    """
    return advance_time(world, steps=float(dt))
