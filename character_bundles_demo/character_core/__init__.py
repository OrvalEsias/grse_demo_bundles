"""
Core Character Branch
Exports all major engines for symbolic character processing.
"""

from .character_feature_engine import (
    resolve_trait_fusion,
    resolve_trait_conflict,
    inherit_traits,
    evaluate_trait_interaction,
)

from .observer_engine import (
    run_observer_cycle,
    generate_observer_summary,
)

from .perception_engine import perceive

from .persona_engine import (
    generate_persona_layer,
    update_persona_after_event,
)

from .prophecy_engine import (
    generate_prophecy,
    apply_prophecy,
)

__all__ = [
    "resolve_trait_fusion",
    "resolve_trait_conflict",
    "inherit_traits",
    "evaluate_trait_interaction",
    "run_observer_cycle",
    "generate_observer_summary",
    "perceive",
    "generate_persona_layer",
    "update_persona_after_event",
    "generate_prophecy",
    "apply_prophecy",
]
