from narrative_branch.loaders.system_loader import load_system
from narrative_branch.engines import track_narrative_symbols, apply_quest_hooks

def demo():
    sys = load_system()
    world = {"symbolic_density":3.0,"world_events":[]}
    char = {"name":"Demo","traits":[],"symbolic_markers":[]}
    prompt="A mirror cracks in the dream-gate."
    track_narrative_symbols(char,prompt)
    world = apply_quest_hooks(world)
    print("Demo Complete.")
