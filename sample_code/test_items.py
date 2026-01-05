from items_recommender import recommend_items

char = {
    "inventory": ["calming_stone", "noise_emitter"]
}

world = {}

items = {
    "calming_stone": {
        "effects": {
            "self": {
                "world_effects": {"spiritual_noise": -0.2}
            }
        }
    },
    "noise_emitter": {
        "effects": {
            "self": {
                "world_effects": {"spiritual_noise": 0.3}
            }
        }
    }
}

goal = {
    "reduce": {"spiritual_noise": -1},
    "zone": "dream_gate"
}

results = recommend_items(goal, char, world, items)

for r in results:
    print(r)
