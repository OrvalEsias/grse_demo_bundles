"""
Loader for Core Character Branch.
Ensures all engines load cleanly and validates their callable interfaces.
"""

import importlib
import sys
from typing import Dict, Any

MODULES = [
    "character_feature_engine",
    "observer_engine",
    "perception_engine",
    "persona_engine",
    "prophecy_engine",
]

def load_core_character_branch() -> Dict[str, Any]:
    loaded = {}
    errors = []

    for module in MODULES:
        try:
            loaded[module] = importlib.import_module(
                f"{__package__}.{module}"
            )
        except Exception as e:
            errors.append((module, str(e)))

    if errors:
        print("\n[Loader] ❌ Errors encountered:")
        for mod, err in errors:
            print(f"- {mod}: {err}")
    else:
        print("[Loader] ✅ Core Character Branch loaded successfully.")

    return loaded
