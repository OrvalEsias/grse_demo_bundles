"""
Demo script for Core Character Branch.
Runs trait fusion, observer cycle, perception pass, and prophecy logic.
"""

from .loader import load_core_character_branch

def run_demo():
    modules = load_core_character_branch()

    char = {
        "name": "DemoCharacter",
        "traits": ["echo_sensitive", "silent"],
        "emotion": {"valence": 0.1},
        "zone": "dream_gate",
    }

    prev_world = {
        "zones": {"dream_gate": {"energy": 0.2}},
        "features": {"spiritual_noise": 0.05, "media_signal": 0.01}
    }

    new_world = {
        "zones": {"dream_gate": {"energy": 0.35}},
        "features": {"spiritual_noise": 0.07, "media_signal": 0.02}
    }

    print("\n=== Trait Interaction ===")
    fused, conflict = modules["character_feature_engine"].evaluate_trait_interaction(char, char)
    print("Fused:", fused)
    print("Conflicts:", conflict)

    print("\n=== Observer Cycle ===")
    obs_out, obs_summary = modules["observer_engine"].run_observer_cycle(char, new_world)
    print(obs_out)

    print("\n=== Perception ===")
    percept = modules["perception_engine"].perceive(prev_world, new_world, char, weights={"*": 1.0})
    print("Focus:", percept["focus"])
    print("Salience:", percept["salience"][:5])

    print("\n=== Prophecy ===")
    prophecy = modules["prophecy_engine"].generate_prophecy(char, new_world)
    print("Prophecy:", prophecy)
    result = modules["prophecy_engine"].apply_prophecy(prophecy, char)
    print(result)

if __name__ == "__main__":
    run_demo()
