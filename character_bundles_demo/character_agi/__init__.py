"""
AGI Character Branch
Exports all AGI-related engines:
- AGI emergence tracking
- AGI score computation
- AGI promoter system
- AGI feedback loop scaffolding
"""

from .agi_emergence_tracker import track_agi_emergence
from .agi_engine import (
    compute_agi_progress,
    compute_agi_progress_advanced,
    update_agi_state_on_character
)
from .agi_feedback_scaffolding import update_self_world_loop
from .agi_promoter import promote_markers_to_traits

__all__ = [
    "track_agi_emergence",
    "compute_agi_progress",
    "compute_agi_progress_advanced",
    "update_agi_state_on_character",
    "update_self_world_loop",
    "promote_markers_to_traits",
]
