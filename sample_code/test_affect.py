from affect_engine import default_affect, appraise, affect_bias, after_action

state = {
    "affect": default_affect()
}

utilities = {
    "explore": 0.2,
    "create": 0.1,
    "defend": 0.1
}

option_ctx = {
    "explore": {"is_new": True},
    "create": {"is_new": False},
    "defend": {"is_new": False}
}

print("Initial affect:", state["affect"])

# simulate an event
event = {"tag": "threat"}
appraise(event, state)

biased = affect_bias(utilities, state, option_ctx)
choice = max(biased, key=biased.get)

after_action(state, choice)

print("Biased utilities:", biased)
print("Chosen intent:", choice)
print("Affect after action:", state["affect"])
