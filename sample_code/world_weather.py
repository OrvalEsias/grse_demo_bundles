from __future__ import annotations
from typing import Dict, Any, List, Tuple

def _distance_vals(a: Dict[str,float], b: Dict[str,float]) -> float:
    keys = set(a)|set(b)
    if not keys: return 0.0
    return sum(abs(a.get(k,0.0)-b.get(k,0.0)) for k in keys) / len(keys)

def aggregate_world(characters: List[Dict[str,Any]]) -> Dict[str,float]:
    if not characters:
        return {"coherence":0.0, "dispersion":0.0}
    coh = [c["weather"]["coherence"] for c in characters]
    mean = sum(coh)/len(coh)
    var  = sum((x-mean)**2 for x in coh)/len(coh)
    return {"coherence": mean, "dispersion": var}

def front_intensity(a: Dict[str,Any], b: Dict[str,Any]) -> float:
    dv   = _distance_vals(a.get("values",{}), b.get("values",{}))     # 0..1
    need = 0.5*(a["weather"]["pressure"] + b["weather"]["pressure"])
    trust= 0.5*(a.get("trust",0.5) + b.get("trust",0.5))
    x = dv*0.6 + need*0.5 - trust*0.4
    return max(0.0, min(1.0, x))

def update_world_weather(world: Dict[str,Any],
                         characters: List[Dict[str,Any]],
                         edges: List[Tuple[int,int]]) -> None:
    ww = world["world_weather"]
    agg = aggregate_world(characters)
    ww.update(agg)
    hot_fronts = 0
    for i,j in edges:
        if 0<=i<len(characters) and 0<=j<len(characters):
            if front_intensity(characters[i], characters[j]) > 0.6:
                hot_fronts += 1
    ww["fronts_active"] = hot_fronts
    if hot_fronts >= 3 and ww["dispersion"] > 0.25:
        ww["storm"]["active"] = True
        ww["storm"]["intensity"] = min(1.0, ww["storm"]["intensity"] + 0.30)
    else:
        ww["storm"]["intensity"] *= 0.92
        if ww["storm"]["intensity"] < 0.12:
            ww["storm"]["active"] = False