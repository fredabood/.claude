"""
Centralized status transition logic for roadmap entities.

Sprint 5 (unified-arch-5-task-003): All status transitions go through this module.

## Design

This module provides the single source of truth for status transitions:

1. **TransitionBlockedError**: Exception with structured blocking reasons
2. **transition_ticket()**: Generic transition function for any HierarchicalTicket
3. **transition_*()**: Type-specific transition functions with proper loading/saving

## Usage

```python
from vibey.operations.roadmap.transitions import (
    TransitionBlockedError,
    transition_task,
    transition_sprint,
    transition_track,
)

# Transition a task
try:
    updated_task = transition_task(task_id, TicketStatus.COMPLETED, root_dir)
    print(f"Task transitioned to {updated_task.status}")
except TransitionBlockedError as e:
    print(f"Blocked: {e.reasons}")
```

## Architecture

All transitions use the unified ticket architecture:
1. Load entity as Pydantic ticket model
2. Validate via can_transition_to() (criteria-based)
3. Apply change via immutable start()/complete() methods
4. Save via v2 yaml_dumper functions
"""

from pathlib import Path
from typing import List, Tuple

from vibey.roadmap.models.ticket import (
    TicketStatus,
    TaskTicket,
    SprintTicket,
    TrackTicket,
    RoadmapTicket,
    HierarchicalTicket,
)
from vibey.operations.roadmap.query import (
    load_task_ticket,
    load_sprint_ticket,
    load_track_ticket,
    load_roadmap_ticket,
)
from vibey.roadmap.serialization.yaml_dumper import (
    save_task_ticket as save_task_ticket_yaml,
    save_sprint_ticket as save_sprint_ticket_yaml,
    save_track_ticket as save_track_ticket_yaml,
    save_roadmap_ticket as save_roadmap_ticket_yaml,
)
from vibey.cli.roadmap_lib.filesystem import FileSystemManager


class TransitionBlockedError(Exception):
    """
    Raised when a status transition is blocked by criteria.

    Attributes:
        entity_id: ID of the entity that couldn't transition
        target_status: The target status that was blocked
        reasons: List of human-readable reasons why transition was blocked
    """

    def __init__(self, entity_id: str, target_status: TicketStatus, reasons: List[str]):
        self.entity_id = entity_id
        self.target_status = target_status
        self.reasons = reasons
        message = f"Cannot transition {entity_id} to {target_status.value}"
        if reasons:
            message += f": {'; '.join(reasons)}"
        super().__init__(message)


def transition_ticket(
    ticket: HierarchicalTicket,
    target_status: TicketStatus,
) -> HierarchicalTicket:
    """
    Transition a ticket to a new status.

    This is the core transition function that validates and applies status changes.
    It does NOT save the ticket - callers are responsible for persistence.

    Args:
        ticket: The ticket to transition (TaskTicket, SprintTicket, etc.)
        target_status: The target TicketStatus

    Returns:
        New ticket instance with updated status (immutable pattern)

    Raises:
        TransitionBlockedError: If transition is blocked by criteria
        ValueError: If target_status is not a valid transition target
    """
    # Validate transition
    can_transition, blockers = ticket.can_transition_to(target_status)
    if not can_transition:
        raise TransitionBlockedError(ticket.id, target_status, blockers)

    # Apply transition using immutable methods
    if target_status == TicketStatus.NOT_STARTED:
        # Reset to not started - rare but possible
        return ticket.model_copy(update={'status': TicketStatus.NOT_STARTED})
    elif target_status == TicketStatus.IN_PROGRESS:
        return ticket.start()
    elif target_status == TicketStatus.COMPLETED:
        return ticket.complete()
    elif target_status == TicketStatus.BLOCKED:
        # Manual blocking - update status only
        return ticket.model_copy(update={'status': TicketStatus.BLOCKED})
    elif target_status == TicketStatus.DEFERRED:
        return ticket.model_copy(update={'status': TicketStatus.DEFERRED})
    else:
        raise ValueError(f"Unsupported target status: {target_status}")


def transition_task(
    task_id: str,
    target_status: TicketStatus,
    root_dir: Path,
    save: bool = True,
) -> TaskTicket:
    """
    Transition a task to a new status.

    Loads the task as a ticket model, validates the transition, applies it,
    and optionally saves to YAML.

    Args:
        task_id: ID of the task to transition
        target_status: Target TicketStatus
        root_dir: Root directory containing .vibey/
        save: If True, save the updated task to YAML

    Returns:
        Updated TaskTicket with new status

    Raises:
        TransitionBlockedError: If transition is blocked by criteria
        FileNotFoundError: If task file not found
    """
    # Load task as ticket model
    task_ticket = load_task_ticket(root_dir, task_id)

    # Transition
    updated_ticket = transition_ticket(task_ticket, target_status)

    if save:
        # Get task file path
        fs = FileSystemManager(root_dir)
        task_path = fs.get_task_path(task_id)
        if not task_path:
            # Try flat structure
            task_path = fs.roadmap_root / "tasks" / f"{task_id}.yaml"
            if not task_path.exists():
                # Try with .id lookup
                id_file = fs.roadmap_root / "tasks" / ".id"
                if id_file.exists():
                    import yaml
                    with open(id_file) as f:
                        id_map = yaml.safe_load(f) or {}
                    if task_id in id_map:
                        ulid = id_map[task_id]
                        task_path = fs.roadmap_root / "tasks" / f"{ulid}.yaml"

        if task_path and task_path.exists():
            save_task_ticket_yaml(updated_ticket, task_path)
        else:
            raise FileNotFoundError(f"Task file not found for {task_id}")

    return updated_ticket


def transition_sprint(
    sprint_id: str,
    target_status: TicketStatus,
    root_dir: Path,
    save: bool = True,
) -> SprintTicket:
    """
    Transition a sprint to a new status.

    Args:
        sprint_id: ID of the sprint to transition
        target_status: Target TicketStatus
        root_dir: Root directory containing .vibey/
        save: If True, save the updated sprint to YAML

    Returns:
        Updated SprintTicket with new status

    Raises:
        TransitionBlockedError: If transition is blocked by criteria
        FileNotFoundError: If sprint file not found
    """
    # Load sprint as ticket model
    sprint_ticket = load_sprint_ticket(root_dir, sprint_id)

    # Transition
    updated_ticket = transition_ticket(sprint_ticket, target_status)

    if save:
        fs = FileSystemManager(root_dir)
        sprint_path = fs.get_sprint_path(sprint_id)

        if sprint_path and sprint_path.exists():
            save_sprint_ticket_yaml(updated_ticket, sprint_path)
        else:
            raise FileNotFoundError(f"Sprint file not found for {sprint_id}")

    return updated_ticket


def transition_track(
    track_id: str,
    target_status: TicketStatus,
    root_dir: Path,
    save: bool = True,
) -> TrackTicket:
    """
    Transition a track to a new status.

    Args:
        track_id: ID of the track to transition
        target_status: Target TicketStatus
        root_dir: Root directory containing .vibey/
        save: If True, save the updated track to YAML

    Returns:
        Updated TrackTicket with new status

    Raises:
        TransitionBlockedError: If transition is blocked by criteria
        FileNotFoundError: If track file not found
    """
    # Load track as ticket model
    track_ticket = load_track_ticket(root_dir, track_id)

    # Transition
    updated_ticket = transition_ticket(track_ticket, target_status)

    if save:
        fs = FileSystemManager(root_dir)
        track_path = fs.get_track_path(track_id)

        if track_path and track_path.exists():
            save_track_ticket_yaml(updated_ticket, track_path)
        else:
            raise FileNotFoundError(f"Track file not found for {track_id}")

    return updated_ticket


def transition_roadmap(
    root_dir: Path,
    target_status: TicketStatus,
    save: bool = True,
) -> RoadmapTicket:
    """
    Transition the roadmap to a new status.

    Args:
        root_dir: Root directory containing .vibey/
        target_status: Target TicketStatus
        save: If True, save the updated roadmap to YAML

    Returns:
        Updated RoadmapTicket with new status

    Raises:
        TransitionBlockedError: If transition is blocked by criteria
        FileNotFoundError: If roadmap file not found
    """
    # Load roadmap as ticket model
    roadmap_ticket = load_roadmap_ticket(root_dir)

    # Transition
    updated_ticket = transition_ticket(roadmap_ticket, target_status)

    if save:
        fs = FileSystemManager(root_dir)
        roadmap_path = fs.get_roadmap_path()

        if roadmap_path and roadmap_path.exists():
            save_roadmap_ticket_yaml(updated_ticket, roadmap_path)
        else:
            raise FileNotFoundError(f"Roadmap file not found")

    return updated_ticket


def can_transition(
    entity_id: str,
    entity_type: str,
    target_status: TicketStatus,
    root_dir: Path,
) -> Tuple[bool, List[str]]:
    """
    Check if an entity can transition to a target status.

    This is a read-only check that doesn't modify any files.

    Args:
        entity_id: ID of the entity
        entity_type: One of 'task', 'sprint', 'track', 'roadmap'
        target_status: Target TicketStatus
        root_dir: Root directory containing .vibey/

    Returns:
        Tuple of (can_transition, list_of_blocking_reasons)
    """
    try:
        if entity_type == 'task':
            ticket = load_task_ticket(root_dir, entity_id)
        elif entity_type == 'sprint':
            ticket = load_sprint_ticket(root_dir, entity_id)
        elif entity_type == 'track':
            ticket = load_track_ticket(root_dir, entity_id)
        elif entity_type == 'roadmap':
            ticket = load_roadmap_ticket(root_dir)
        else:
            return False, [f"Unknown entity type: {entity_type}"]

        return ticket.can_transition_to(target_status)
    except Exception as e:
        return False, [f"Failed to load {entity_type}: {str(e)}"]


def start_item(
    root_dir: Path,
    item_id: str,
    force: bool = False,
) -> dict:
    """
    Start a task, sprint, or track.

    Auto-detects item type from filesystem and delegates to appropriate
    transition function. This is the primary entry point for the unified
    commands layer.

    Supports both ULID and slug-based IDs through FileSystemManager resolution.

    Args:
        root_dir: Project root directory
        item_id: ULID or slug of item to start
        force: If True, bypass blocking criteria (not yet implemented)

    Returns:
        Dict with updated item info: {'id': str, 'status': str, 'type': str}

    Raises:
        TransitionBlockedError: If blocked and force=False
        FileNotFoundError: If item doesn't exist
        Exception: If ticket loader encounters validation errors (e.g., roadmap validation)
    """
    fs = FileSystemManager(root_dir)

    # Determine item type from filesystem first, then attempt transition
    # This ensures we raise the right errors for the right situations

    item_type = None
    item_path = None

    # Check for task
    try:
        task_path = fs.get_task_path(item_id)
        if task_path.exists():
            item_type = 'task'
            item_path = task_path
    except (ValueError, AttributeError):
        pass

    # Check for sprint if not a task
    if item_type is None:
        try:
            sprint_path = fs.get_sprint_path(item_id)
            if sprint_path.exists():
                item_type = 'sprint'
                item_path = sprint_path
        except (ValueError, AttributeError):
            pass

    # Check for track if not a task or sprint
    if item_type is None:
        try:
            track_path = fs.get_track_path(item_id)
            if track_path.exists():
                item_type = 'track'
                item_path = track_path
        except (ValueError, AttributeError):
            pass

    # If no item found, raise FileNotFoundError
    if item_type is None:
        raise FileNotFoundError(f"Item not found: {item_id}")

    # Now attempt the transition - any errors here should propagate
    ulid = item_path.stem

    if item_type == 'task':
        ticket = transition_task(ulid, TicketStatus.IN_PROGRESS, root_dir)
    elif item_type == 'sprint':
        ticket = transition_sprint(ulid, TicketStatus.IN_PROGRESS, root_dir)
    else:  # track
        ticket = transition_track(ulid, TicketStatus.IN_PROGRESS, root_dir)

    return {'id': ticket.id, 'status': ticket.status.value, 'type': item_type}


def complete_item(
    root_dir: Path,
    item_id: str,
    notes: str = None,
) -> dict:
    """
    Complete a task, sprint, or track.

    Auto-detects item type from filesystem and delegates to appropriate
    transition function. This is the primary entry point for the unified
    commands layer.

    Supports both ULID and slug-based IDs through FileSystemManager resolution.

    Args:
        root_dir: Project root directory
        item_id: ULID or slug of item to complete
        notes: Optional completion notes (stored in metadata)

    Returns:
        Dict with updated item info: {'id': str, 'status': str, 'type': str}

    Raises:
        TransitionBlockedError: If blocked by criteria
        FileNotFoundError: If item doesn't exist
        Exception: If ticket loader encounters validation errors (e.g., roadmap validation)
    """
    fs = FileSystemManager(root_dir)

    # Determine item type from filesystem first, then attempt transition
    # This ensures we raise the right errors for the right situations

    item_type = None
    item_path = None

    # Check for task
    try:
        task_path = fs.get_task_path(item_id)
        if task_path.exists():
            item_type = 'task'
            item_path = task_path
    except (ValueError, AttributeError):
        pass

    # Check for sprint if not a task
    if item_type is None:
        try:
            sprint_path = fs.get_sprint_path(item_id)
            if sprint_path.exists():
                item_type = 'sprint'
                item_path = sprint_path
        except (ValueError, AttributeError):
            pass

    # Check for track if not a task or sprint
    if item_type is None:
        try:
            track_path = fs.get_track_path(item_id)
            if track_path.exists():
                item_type = 'track'
                item_path = track_path
        except (ValueError, AttributeError):
            pass

    # If no item found, raise FileNotFoundError
    if item_type is None:
        raise FileNotFoundError(f"Item not found: {item_id}")

    # Now attempt the transition - any errors here should propagate
    ulid = item_path.stem

    if item_type == 'task':
        ticket = transition_task(ulid, TicketStatus.COMPLETED, root_dir)
    elif item_type == 'sprint':
        ticket = transition_sprint(ulid, TicketStatus.COMPLETED, root_dir)
    else:  # track
        ticket = transition_track(ulid, TicketStatus.COMPLETED, root_dir)

    return {'id': ticket.id, 'status': ticket.status.value, 'type': item_type, 'notes': notes}


# Export for convenient importing
__all__ = [
    'TransitionBlockedError',
    'transition_ticket',
    'transition_task',
    'transition_sprint',
    'transition_track',
    'transition_roadmap',
    'can_transition',
    'start_item',
    'complete_item',
]
