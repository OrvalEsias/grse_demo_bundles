ZONE_SCHEMA = {
    "id": str, "name": str, "type": str, "seed": (int | None),
    "energy": float, "markers": list, "entities": list, "items": list,
    "links": list, "traits": list, "weather": dict, "rules": dict,
    "timers": dict, "history": list, "version": str,
  }
DEFAULT_ZONE = {"energy": 0.0, "markers": [], "entities": [], "items": [],
                "links": [], "traits": [], "weather": {}, "rules": {},
                "timers": {}, "history": [], "version": "1.0.0"}