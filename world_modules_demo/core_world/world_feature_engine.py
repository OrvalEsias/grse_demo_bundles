# engine/world_feature_engine.py
from __future__ import annotations
import random
import re
from typing import Dict, Any
from datetime import datetime

def update_world_features(
    world_state: Dict[str, Any],
    prompt: str,
    *,
    decay: float = 0.05,
    boost: float = 0.2,
    max_value: float = 1.0
) -> Dict[str, Any]:
    """
    Detects symbolic triggers from prompt and updates world_state['features'].
    
    Args:
        world_state: Dict with optional 'features' dict.
        prompt: input string to search for triggers.
        decay: per-call decay for non-hit features (0-1 scale).
        boost: amount to add when a keyword is hit.
        max_value: cap for feature 'value'.

    Returns:
        Updated world_state with features dict and features_history log.
    """
    features = world_state.setdefault("features", {})
    features_history = world_state.setdefault("features_history", {})

    symbolic_triggers = {
        "fracture": "sky_fracture",
        "flood": "oceanic_memory_surge",
        "inversion": "inverted_sun",
        "spiral": "vortex_gate",
        "glyph": "engraved_land",
        "mirror": "reflection_veil",
        "echo": "resonant_valley",
        "seed": "axis_bloom"
    }

    prompt_lc = prompt.lower()

    # 1. Decay all existing features
    for fname, fdata in list(features.items()):
        if isinstance(fdata, dict) and "value" in fdata:
            new_val = max(0.0, fdata["value"] - decay)
            fdata["value"] = round(new_val, 3)
            if new_val <= 0.0:
                # feature fades completely
                features.pop(fname, None)
        else:
            # upgrade boolean -> dict
            features[fname] = {
                "value": max(0.0, 1.0 - decay),
                "first_seen": datetime.utcnow().isoformat(),
                "hit_count": 1
            }

    # 2. Check for trigger hits
    for keyword, feature in symbolic_triggers.items():
        if re.search(rf"\b{re.escape(keyword)}", prompt_lc):
            fdata = features.setdefault(feature, {
                "value": 0.0,
                "first_seen": datetime.utcnow().isoformat(),
                "hit_count": 0
            })
            # boost value
            fdata["value"] = min(max_value, fdata["value"] + boost)
            fdata["hit_count"] += 1

            # record history
            hist_list = features_history.setdefault(feature, [])
            hist_list.append({
                "t": datetime.utcnow().isoformat(),
                "prompt": prompt,
                "value": round(fdata["value"], 3),
                "hit_count": fdata["hit_count"]
            })

    return world_state
