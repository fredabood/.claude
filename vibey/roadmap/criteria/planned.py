"""
Planned criterion factory.

Creates criteria that determine if a ticket is "planned" (ready for work).

A ticket is considered "planned" when certain conditions are met:
1. YAML file exists (required by default)
2. Context files exist (optional by default)
3. Manual approval given (disabled by default)

All criteria are built from existing target types - this module just
provides a convenient factory for creating the common "planned" pattern.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from vibey.roadmap.models.ticket.completable import Criterion
from vibey.roadmap.models.ticket.enums import TicketStatus
from vibey.roadmap.models.ticket.targets import FileExistsTarget, ManualTarget


@dataclass
class PlannedCriteriaConfig:
    """Configuration for planned criteria.

    Controls which checks are included and whether they're required.
    """

    # Which checks to include
    check_yaml_exists: bool = True
    check_context_exists: bool = True
    check_manual_approval: bool = False

    # Which checks are required vs optional
    yaml_required: bool = True
    context_required: bool = False
    approval_required: bool = False


DEFAULT_PLANNED_CONFIG = PlannedCriteriaConfig()


def create_planned_criteria(
    ticket_id: str,
    ticket_type: str,
    roadmap_root: Path,
    config: PlannedCriteriaConfig = DEFAULT_PLANNED_CONFIG,
) -> List[Criterion]:
    """
    Create criteria for determining if a ticket is "planned".

    Args:
        ticket_id: The ticket's ULID
        ticket_type: Type of ticket ('task', 'sprint', 'track')
        roadmap_root: Path to .vibey/roadmap directory
        config: Configuration for which checks to include

    Returns:
        List of Criterion objects that block IN_PROGRESS transition
    """
    criteria = []

    # 1. YAML file exists
    if config.check_yaml_exists:
        yaml_path = roadmap_root / f"{ticket_type}s" / f"{ticket_id}.yaml"
        criteria.append(
            Criterion(
                id=f"{ticket_id}-yaml-exists",
                description=f"YAML file exists at {ticket_type}s/{ticket_id}.yaml",
                blocks_transition_to=TicketStatus.IN_PROGRESS,
                target=FileExistsTarget(paths=[str(yaml_path)]),
                required=config.yaml_required,
            )
        )

    # 2. Context directory/files exist
    if config.check_context_exists:
        context_paths = _get_context_paths(ticket_id, ticket_type, roadmap_root)
        if context_paths:
            criteria.append(
                Criterion(
                    id=f"{ticket_id}-context-exists",
                    description="Context files exist (task plan, design docs, etc.)",
                    blocks_transition_to=TicketStatus.IN_PROGRESS,
                    target=FileExistsTarget(paths=context_paths),
                    required=config.context_required,
                )
            )

    # 3. Manual approval
    if config.check_manual_approval:
        criteria.append(
            Criterion(
                id=f"{ticket_id}-planning-approved",
                description="Planning has been reviewed and approved",
                blocks_transition_to=TicketStatus.IN_PROGRESS,
                target=ManualTarget(
                    approved=False,
                    approver=None,
                ),
                required=config.approval_required,
            )
        )

    return criteria


def _get_context_paths(
    ticket_id: str,
    ticket_type: str,
    roadmap_root: Path,
) -> List[str]:
    """
    Get expected context file paths for a ticket.

    Returns paths that SHOULD exist for planning to be complete.
    The FileExistsTarget will determine if they actually exist.

    Context can be in:
    - .vibey/roadmap/context/tasks/<id>/TASK_PLAN.md
    - .vibey/roadmap/context/sprints/<id>/SPRINT_PLAN.md
    - .vibey/roadmap/context/tracks/<id>/TRACK_PLAN.md
    """
    # Expected context file based on ticket type
    direct_path = roadmap_root / "context" / f"{ticket_type}s" / ticket_id

    # Map ticket type to expected plan file
    plan_file_map = {
        "task": "TASK_PLAN.md",
        "sprint": "SPRINT_PLAN.md",
        "track": "TRACK_PLAN.md",
    }

    plan_file = plan_file_map.get(ticket_type, "*.md")
    expected_path = direct_path / plan_file

    return [str(expected_path)]


def check_planned_status(
    ticket_id: str,
    ticket_type: str,
    roadmap_root: Path,
    config: PlannedCriteriaConfig = DEFAULT_PLANNED_CONFIG,
) -> tuple[bool, List[str]]:
    """
    Check if a ticket is planned (all planning criteria met).

    Args:
        ticket_id: The ticket's ULID
        ticket_type: Type of ticket
        roadmap_root: Path to .vibey/roadmap
        config: Criteria configuration

    Returns:
        Tuple of (is_planned: bool, unmet_criteria: List[str])
    """
    criteria = create_planned_criteria(ticket_id, ticket_type, roadmap_root, config)

    unmet = []
    for c in criteria:
        # Refresh target to get current state from filesystem/external sources
        c.target.refresh()
        if c.required and not c.is_met:
            unmet.append(c.description)

    return (len(unmet) == 0, unmet)


def get_planning_work_needed(
    ticket_id: str,
    ticket_type: str,
    roadmap_root: Path,
    config: PlannedCriteriaConfig = DEFAULT_PLANNED_CONFIG,
) -> List[dict]:
    """
    Get list of planning work items needed for a ticket.

    Returns:
        List of dicts: [{'criterion': str, 'description': str, 'required': bool, 'action': str}]
    """
    criteria = create_planned_criteria(ticket_id, ticket_type, roadmap_root, config)

    work_items = []
    for c in criteria:
        # Refresh target to get current state from filesystem/external sources
        c.target.refresh()
        if not c.is_met:
            work_items.append({
                'criterion': c.id,
                'description': c.description,
                'required': c.required,
                'action': _suggest_action(c),
            })

    return work_items


def _suggest_action(criterion: Criterion) -> str:
    """Suggest action to satisfy a criterion."""
    if isinstance(criterion.target, FileExistsTarget):
        paths = criterion.target.paths
        if paths:
            return f"Create file: {paths[0]}"
        return "Create required file"
    elif isinstance(criterion.target, ManualTarget):
        return "Get planning approval via 'vibey planned approve <id>'"
    return "Satisfy criterion"
