from anti_stall import AntiStall

char = {
    "zone": "dream_gate",
    "inventory": []
}

world = {
    "zones": {
        "dream_gate": {"energy": 0.1},
        "market_ruins": {"energy": 0.9}
    }
}

engine = AntiStall(window=4, min_repeats=2)
engine.seed(1)

markers = []

for i in range(6):
    intent = "wait"
    char, world, markers, queued, note = engine.assess_and_intervene(
        char, world, markers, intent
    )
    print(f"Tick {i} | zone={char['zone']} | note={note} | queued={queued}")
