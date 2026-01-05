from __future__ import annotations
from typing import Dict, Any

def _clamp(x, lo, hi): return max(lo, min(hi, x))

def default_affect() -> Dict[str, Any]:
    return {
        "valence": 0.0, "arousal": 0.2, "dominance": 0.5,
        "tags": {"interest":0.35, "calm":0.30, "fear":0.05, "anger":0.0, "sadness":0.0},
        "curiosity_floor": 0.12
    }

def appraise(event: Any, state: Dict[str,Any]) -> None:
    af = state["affect"]; t = af["tags"]; tag = event.get("tag")
    if tag == "novel_reward":
        af["valence"] += 0.25; af["arousal"] += 0.15; t["interest"] = min(1.0, t["interest"]+0.30); t["calm"] += 0.05
    elif tag == "success":
        af["valence"] += 0.20; af["dominance"] += 0.10
    elif tag == "threat":
        af["arousal"] += 0.25; t["fear"] = min(1.0, t["fear"]+0.35); t["calm"] = max(0.0, t["calm"]-0.15)
    elif tag == "frustration":
        t["anger"] = min(1.0, t["anger"]+0.25)
    elif tag == "loss":
        af["valence"] -= 0.25; t["sadness"] = min(1.0, t["sadness"]+0.30)
    elif tag == "social_join":
        t["calm"] = min(1.0, t["calm"]+0.25); af["valence"] += 0.15
    af["valence"]  = _clamp(af["valence"], -1, 1)
    af["arousal"]  = _clamp(af["arousal"], 0, 1)
    af["dominance"]= _clamp(af["dominance"], 0, 1)

def exploration_bonus(state: Dict[str,Any], intent: str, is_new: bool) -> float:
    floor = state["affect"]["curiosity_floor"]
    novelty = 0.35 if is_new else 0.0
    streak = state.setdefault("counters",{}).setdefault("intent_streak",{}).get(intent,0)
    anti_repeat = 0.05 * max(0, streak - 2)
    return floor + novelty + anti_repeat

def affect_bias(utilities: Dict[str,float], state: Dict[str,Any],
                option_ctx: Dict[str,Dict[str,Any]]) -> Dict[str,float]:
    af, t = state["affect"], state["affect"]["tags"]
    v, a, d = af["valence"], af["arousal"], af["dominance"]
    U = dict(utilities)
    U["explore"] = U.get("explore",0.0) + 0.6*t["interest"] - 0.3*t["fear"]
    U["create"]  = U.get("create",0.0)  + 0.4*((v+1)/2) + 0.2*d
    U["bond"]    = U.get("bond",0.0)    + 0.5*t["calm"] + 0.2*((v+1)/2)
    U["defend"]  = U.get("defend",0.0)  + 0.5*t["anger"] + 0.2*a
    U["repair"]  = U.get("repair",0.0)  + 0.6*t["sadness"]
    for intent, ctx in option_ctx.items():
        U[intent] = U.get(intent, 0.0) + exploration_bonus(state, intent, ctx.get("is_new", False))
    return U

def after_action(state: Dict[str,Any], chosen_intent: str) -> None:
    af = state["affect"]; t = af["tags"]
    for k in t: t[k] *= 0.95
    af["valence"]   = _clamp(af["valence"], -1, 1)
    af["arousal"]   = _clamp(af["arousal"], 0, 1)
    af["dominance"] = _clamp(af["dominance"], 0, 1)
    streaks = state.setdefault("counters",{}).setdefault("intent_streak",{})
    streaks[chosen_intent] = streaks.get(chosen_intent,0) + 1
    for k in list(streaks.keys()):
        if k != chosen_intent: streaks[k] = 0