"""
Operations for planned status management.

Provides the business logic layer for planned status checking,
approval, and querying.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from vibey.roadmap.criteria.planned import (
    check_planned_status,
    get_planning_work_needed,
)


@dataclass
class PlannedCheckResult:
    """Result of checking planned status."""
    ticket_id: str
    ticket_type: str
    is_planned: bool
    criteria_total: int
    criteria_met: int
    unmet_criteria: List[str]
    unplanned_children: List[str]


@dataclass
class PlanningWorkItem:
    """A work item needed for planning."""
    ticket_id: str
    ticket_type: str
    ticket_title: str
    criterion: str
    action: str
    required: bool


def check_planned(
    root_dir: Path,
    item_id: str,
) -> PlannedCheckResult:
    """
    Check planned status of a ticket.

    Args:
        root_dir: Project root
        item_id: Ticket ULID

    Returns:
        PlannedCheckResult with status details
    """
    from vibey.roadmap.criteria.planned import (
        create_planned_criteria,
        DEFAULT_PLANNED_CONFIG,
    )

    roadmap_root = root_dir / ".vibey" / "roadmap"

    # Detect type
    ticket_type = _detect_type(item_id, roadmap_root)

    # Check planned status using criteria directly (no full ticket load needed)
    is_planned, unmet = check_planned_status(
        item_id, ticket_type, roadmap_root
    )

    # Compute progress from criteria directly
    criteria = create_planned_criteria(
        item_id, ticket_type, roadmap_root, DEFAULT_PLANNED_CONFIG
    )
    for c in criteria:
        c.target.refresh()

    criteria_total = len([c for c in criteria if c.required])
    criteria_met = len([c for c in criteria if c.required and c.is_met])

    # For unplanned children, we need to query the database instead of loading ticket
    unplanned_children = _get_unplanned_children(item_id, ticket_type, roadmap_root)

    return PlannedCheckResult(
        ticket_id=item_id,
        ticket_type=ticket_type,
        is_planned=is_planned,
        criteria_total=criteria_total,
        criteria_met=criteria_met,
        unmet_criteria=unmet,
        unplanned_children=unplanned_children,
    )


def _get_unplanned_children(
    item_id: str,
    ticket_type: str,
    roadmap_root: Path,
) -> List[str]:
    """Get list of unplanned child ticket IDs."""
    db_path = roadmap_root / "roadmap.db"
    if not db_path.exists():
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    unplanned = []

    try:
        if ticket_type == 'track':
            # Get unplanned sprints in this track
            for row in conn.execute(
                "SELECT id FROM sprints WHERE track_id = ?", (item_id,)
            ):
                is_planned, _ = check_planned_status(
                    row['id'], 'sprint', roadmap_root
                )
                if not is_planned:
                    unplanned.append(row['id'])
        elif ticket_type == 'sprint':
            # Get unplanned tasks in this sprint
            for row in conn.execute(
                "SELECT id FROM tasks WHERE sprint_id = ?", (item_id,)
            ):
                is_planned, _ = check_planned_status(
                    row['id'], 'task', roadmap_root
                )
                if not is_planned:
                    unplanned.append(row['id'])
        # Tasks have no children
    finally:
        conn.close()

    return unplanned


def approve_planned(
    root_dir: Path,
    item_id: str,
    approver: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """
    Manually approve planned status for a ticket.

    Updates the ticket's metadata to mark planning as approved.

    Args:
        root_dir: Project root
        item_id: Ticket ULID
        approver: Who approved (optional)
        notes: Approval notes (optional)

    Returns:
        Dict with approval details
    """
    import yaml

    roadmap_root = root_dir / ".vibey" / "roadmap"
    ticket_type = _detect_type(item_id, roadmap_root)

    # Get the YAML file path
    yaml_path = roadmap_root / f"{ticket_type}s" / f"{item_id}.yaml"

    # Read existing YAML
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    # Update metadata
    if data is None:
        data = {}

    # Find the ticket data (may be under 'task', 'sprint', or 'track' key)
    ticket_data = data.get(ticket_type, data)

    if 'metadata' not in ticket_data:
        ticket_data['metadata'] = {}

    approval_time = datetime.now(timezone.utc).isoformat()
    ticket_data['metadata']['planned_approved'] = True
    ticket_data['metadata']['planned_approved_at'] = approval_time
    if approver:
        ticket_data['metadata']['planned_approved_by'] = approver
    if notes:
        ticket_data['metadata']['planned_approval_notes'] = notes

    # Write back
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    return {
        'ticket_id': item_id,
        'approved': True,
        'approved_at': approval_time,
        'approver': approver,
    }


def list_unplanned(
    root_dir: Path,
    scope: str = "all",
    track_id: Optional[str] = None,
    sprint_id: Optional[str] = None,
) -> List[dict]:
    """
    List tickets that are not yet planned.

    Args:
        root_dir: Project root
        scope: 'all', 'tracks', 'sprints', 'tasks'
        track_id: Filter by track (optional)
        sprint_id: Filter by sprint (optional)

    Returns:
        List of unplanned ticket dicts
    """
    roadmap_root = root_dir / ".vibey" / "roadmap"
    db_path = roadmap_root / "roadmap.db"

    if not db_path.exists():
        return []

    unplanned = []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        # Query tasks (most common case)
        if scope in ('all', 'tasks'):
            query = "SELECT id, title, sprint_id FROM tasks"
            params = []

            if sprint_id:
                query += " WHERE sprint_id = ?"
                params.append(sprint_id)
            elif track_id:
                query += " WHERE sprint_id IN (SELECT id FROM sprints WHERE track_id = ?)"
                params.append(track_id)

            for row in conn.execute(query, params):
                is_planned, _ = check_planned_status(
                    row['id'], 'task', roadmap_root
                )
                if not is_planned:
                    unplanned.append({
                        'id': row['id'],
                        'title': row['title'],
                        'type': 'task',
                        'parent_id': row['sprint_id'],
                    })

        # Query sprints
        if scope in ('all', 'sprints'):
            query = "SELECT id, name, track_id FROM sprints"
            params = []

            if track_id:
                query += " WHERE track_id = ?"
                params.append(track_id)

            for row in conn.execute(query, params):
                is_planned, _ = check_planned_status(
                    row['id'], 'sprint', roadmap_root
                )
                if not is_planned:
                    unplanned.append({
                        'id': row['id'],
                        'title': row['name'],
                        'type': 'sprint',
                        'parent_id': row['track_id'],
                    })

        # Query tracks
        if scope in ('all', 'tracks'):
            query = "SELECT id, name FROM tracks"

            for row in conn.execute(query):
                is_planned, _ = check_planned_status(
                    row['id'], 'track', roadmap_root
                )
                if not is_planned:
                    unplanned.append({
                        'id': row['id'],
                        'title': row['name'],
                        'type': 'track',
                        'parent_id': None,
                    })

    finally:
        conn.close()

    return unplanned


def get_next_planning_work(
    root_dir: Path,
    track_id: str,
) -> Optional[PlanningWorkItem]:
    """
    Get the next planning work item for a track.

    Finds the first unplanned ticket and returns what work is needed.

    Args:
        root_dir: Project root
        track_id: Track to check

    Returns:
        PlanningWorkItem or None if fully planned
    """
    roadmap_root = root_dir / ".vibey" / "roadmap"

    # Get unplanned tasks in this track
    unplanned = list_unplanned(root_dir, scope='tasks', track_id=track_id)

    if not unplanned:
        return None

    # Get first unplanned task
    first = unplanned[0]

    # Get work needed
    work_items = get_planning_work_needed(
        first['id'], 'task', roadmap_root
    )

    if not work_items:
        return None

    # Return first work item
    item = work_items[0]
    return PlanningWorkItem(
        ticket_id=first['id'],
        ticket_type='task',
        ticket_title=first['title'],
        criterion=item['criterion'],
        action=item['action'],
        required=item['required'],
    )


def _detect_type(item_id: str, roadmap_root: Path) -> str:
    """Detect ticket type from filesystem."""
    if (roadmap_root / "tasks" / f"{item_id}.yaml").exists():
        return "task"
    elif (roadmap_root / "sprints" / f"{item_id}.yaml").exists():
        return "sprint"
    elif (roadmap_root / "tracks" / f"{item_id}.yaml").exists():
        return "track"
    raise FileNotFoundError(f"Ticket not found: {item_id}")


__all__ = [
    'PlannedCheckResult',
    'PlanningWorkItem',
    'check_planned',
    'approve_planned',
    'list_unplanned',
    'get_next_planning_work',
]
