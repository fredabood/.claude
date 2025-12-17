"""
Criterion composition utilities.

This module provides factory functions for creating common criterion patterns,
such as "planned" criteria that determine if a ticket is ready for work.

The key innovation is that all criteria are built from existing target types
(FileExistsTarget, ManualTarget, CompletableTarget) - no new abstractions needed.
"""

from .planned import (
    create_planned_criteria,
    check_planned_status,
    get_planning_work_needed,
    PlannedCriteriaConfig,
    DEFAULT_PLANNED_CONFIG,
)

__all__ = [
    "create_planned_criteria",
    "check_planned_status",
    "get_planning_work_needed",
    "PlannedCriteriaConfig",
    "DEFAULT_PLANNED_CONFIG",
]
