from world_weather import update_world_weather

characters = [
    {"weather": {"coherence": 0.2, "pressure": 0.6}, "values": {"order": 0.9}, "trust": 0.3},
    {"weather": {"coherence": 0.4, "pressure": 0.7}, "values": {"order": 0.1}, "trust": 0.2},
    {"weather": {"coherence": 0.3, "pressure": 0.8}, "values": {"order": 0.5}, "trust": 0.4},
]

world = {
    "world_weather": {
        "coherence": 0.0,
        "dispersion": 0.0,
        "fronts_active": 0,
        "storm": {"active": False, "intensity": 0.0}
    }
}

edges = [(0,1), (1,2), (0,2)]

for step in range(5):
    update_world_weather(world, characters, edges)
    print(f"Step {step}:", world["world_weather"])
