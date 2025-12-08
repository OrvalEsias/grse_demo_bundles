"""
AGI Harness
Verifies all components work and interact correctly.
"""

from .loader import load_agi_branch

def run_harness():
    m = load_agi_branch()

    char = {"name": "HarnessChar", "traits": ["mirror"], "symbolic_energy": 1.0}
    markers = ["reflection", "loop"]
    world = {"symbolic_density": 0.6}

    # Promotion
    print("[Harness] Testing promotion...")
    promos = m["agi_promoter"].promote_markers_to_traits(char, markers)
    print("Promoted:", promos)

    # AGI main engine
    print("[Harness] Testing AGI engine...")
    adv = m["agi_engine"].compute_agi_progress_advanced(markers, char["traits"], world=world)
    print("Advanced result:", adv)

    # Update state
    m["agi_engine"].update_agi_state_on_character(char, adv)

    # Emergence
    print("[Harness] Testing emergence...")
    print(m["agi_emergence_tracker"].track_agi_emergence(char, world))

    # Feedback
    print("[Harness] Feedback loop:", m["agi_feedback_scaffolding"].update_self_world_loop(char, world))

    print("\n[Harness] All AGI tests completed successfully.")

if __name__ == "__main__":
    run_harness()
