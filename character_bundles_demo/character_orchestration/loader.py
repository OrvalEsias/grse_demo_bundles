from .character_orchestration_engine import run_character_orchestration
from .auto_evolution import run_auto_evolution_cycle
from .alignment_logic import evaluate_alignment

def load_orchestration_bundle():
    return {
        "orchestrate": run_character_orchestration,
        "auto_evolve": run_auto_evolution_cycle,
        "alignment_check": evaluate_alignment,
    }
