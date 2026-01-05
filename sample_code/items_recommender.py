from typing import Dict, Any, List, Tuple

def recommend_items(goal: Dict[str, Any], char: Dict[str, Any], world: Dict[str, Any], items: Dict[str, Any]) -> List[Tuple[str, float, str]]:
    """
    Simple heuristic recommender returning [(item_name, score, reason), ...]
    Example goal: {"reduce": {"spiritual_noise": 0.03}, "zone": "dream_gate"}
    """
    inv = set(char.get("inventory", []))
    wants = (goal.get("reduce") or {}) if isinstance(goal.get("reduce"), dict) else {}
    zone = goal.get("zone")

    cand = []
    for name, it in items.items():
        if name not in inv: continue
        eff = (it.get("effects") or {}).get("self") or {}
        we = eff.get("world_effects", {})
        score = 0.0
        reasons = []
        for k, target_drop in wants.items():
            delta = float(we.get(k, 0.0))
            if target_drop < 0 and delta < 0:  # reducing stat
                score += abs(delta)
                reasons.append(f"{k}{delta:+}")
            if target_drop > 0 and delta > 0:
                score += delta
                reasons.append(f"{k}{delta:+}")
        # zone boost if item has zone effects
        if zone and "zone" in (it.get("effects") or {}):
            score += 0.01
        if score > 0:
            cand.append((name, score, " / ".join(reasons) or "matches goal"))
    return sorted(cand, key=lambda x: x[1], reverse=True)[:5]
