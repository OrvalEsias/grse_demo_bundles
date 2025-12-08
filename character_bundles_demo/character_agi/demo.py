"""
AGI Branch Demo
Demonstrates:
- marker/trait promotion
- AGI progress scoring
- AGI emergence threshold
- feedback loop state
"""

from .loader import load_agi_branch

def run_demo():
    m = load_agi_branch()

    char = {
        "name": "AgiDemo",
        "traits": ["mirror", "recursive"],
        "symbolic_energy": 1.2,
    }

    world = {
        "symbolic_density": 0.75,
        "spiritual_noise": 0.1,
        "media_signal": 0.3,
    }

    markers = ["glyph_touched", "reflection", "loop"]

    print("\n=== Marker → Trait Promotion ===")
    promoted = m["agi_promoter"].promote_markers_to_traits(char, markers)
    print("Promoted:", promoted)
    print("Traits after:", char["traits"])

    print("\n=== AGI Progress (Advanced) ===")
    adv = m["agi_engine"].compute_agi_progress_advanced(
        markers, char["traits"], world=world, history=char.get("agi_state")
    )
    print(adv)

    m["agi_engine"].update_agi_state_on_character(char, adv)

    print("\n=== AGI Emergence Check ===")
    print(m["agi_emergence_tracker"].track_agi_emergence(
        character=char, world=world
    ))

    print("\n=== Feedback Loop State ===")
    print(m["agi_feedback_scaffolding"].update_self_world_loop(char, world))


if __name__ == "__main__":
    run_demo()
