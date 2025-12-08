"""
Harness for Core Character Branch.
Runs minimal tests to ensure engines behave correctly.
"""

from .loader import load_core_character_branch

def run_harness():
    m = load_core_character_branch()

    assert "character_feature_engine" in m
    assert "observer_engine" in m
    assert "perception_engine" in m
    assert "persona_engine" in m
    assert "prophecy_engine" in m

    # Trait fusion smoke test
    fused, conflict = m["character_feature_engine"].evaluate_trait_interaction(
        {"traits": ["echo_sensitive"]},
        {"traits": ["symbol_bearer"]},
    )
    print("[Harness] Fusion:", fused)
    print("[Harness] Conflicts:", conflict)

    # Observer smoke test
    obs, summary = m["observer_engine"].run_observer_cycle(
        {"name": "Test", "traits": ["multi_self_aware"]},
        {"symbolic_density": 0.2}
    )
    print("[Harness] Observer OK.")

    # Perception smoke test
    percept = m["perception_engine"].perceive({}, {"a": 1}, {"emotion": {"valence": 0}}, {"*": 1.0})
    print("[Harness] Perception focus:", percept["focus"])

    print("[Harness] All tests passed.")

if __name__ == "__main__":
    run_harness()
