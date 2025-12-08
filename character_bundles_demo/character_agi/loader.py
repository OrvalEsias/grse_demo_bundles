"""
Loader for the AGI Character Branch.
Ensures all AGI modules import successfully and returns a module dict.
"""

import importlib

MODULES = [
    "agi_emergence_tracker",
    "agi_engine",
    "agi_feedback_scaffolding",
    "agi_promoter",
]

def load_agi_branch():
    loaded = {}
    errors = []

    for module in MODULES:
        try:
            loaded[module] = importlib.import_module(f"{__package__}.{module}")
        except Exception as e:
            errors.append((module, str(e)))

    if errors:
        print("\n[AGI Loader] ❌ Errors:")
        for mod, err in errors:
            print(f"- {mod}: {err}")
    else:
        print("[AGI Loader] ✅ AGI Character Branch loaded successfully.")

    return loaded
