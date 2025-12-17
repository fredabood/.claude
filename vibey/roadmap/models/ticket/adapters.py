"""
Adapter classes for converting between legacy dataclass models and unified Pydantic ticket models.

This module provides bidirectional conversion between:
- Roadmap <-> RoadmapTicket
- Track <-> TrackTicket
- Sprint <-> SprintTicket
- Task <-> TaskTicket

Key Conversions:
- Children lists (tracks/sprints/tasks) → CompletableTarget criteria
- Dependencies (blocked_by/depends_on) → CompletableTarget criteria with blocks_transition_to=IN_PROGRESS
- Deliverables → FileExistsTarget criteria
- Status enum mapping → TicketStatus enum

Design Reference: sqlite-backend-6-task-013 (Migration Task)
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, TYPE_CHECKING
import uuid

from vibey.roadmap.models.ticket.completable import Criterion
from vibey.roadmap.models.ticket.enums import (
    TicketStatus,
    TaskType,
    Priority,
)
from vibey.roadmap.models.ticket.targets import (
    CompletableTarget,
    FileExistsTarget,
)

if TYPE_CHECKING:
    from vibey.roadmap.models.roadmap import Roadmap
    from vibey.roadmap.models.track import Track
    from vibey.roadmap.models.sprint import Sprint
    from vibey.roadmap.models.task import Task


# =============================================================================
# STATUS MAPPING
# =============================================================================


def map_status_to_ticket_status(status_value: str) -> TicketStatus:
    """
    Map legacy Status enum value to TicketStatus.

    Args:
        status_value: String value from legacy Status enum

    Returns:
        Corresponding TicketStatus value
    """
    mapping = {
        "not_started": TicketStatus.NOT_STARTED,
        "in_progress": TicketStatus.IN_PROGRESS,
        "paused": TicketStatus.PAUSED,
        "completed": TicketStatus.COMPLETED,
        "production_ready": TicketStatus.PRODUCTION_READY,
        "deployed": TicketStatus.DEPLOYED,
        "blocked": TicketStatus.NOT_STARTED,  # Map blocked to not_started
        "wont_do": TicketStatus.WONT_DO,
        "superseded": TicketStatus.SUPERSEDED,
    }
    return mapping.get(status_value.lower(), TicketStatus.NOT_STARTED)


def map_ticket_status_to_status(status: TicketStatus) -> str:
    """
    Map TicketStatus to legacy Status string value.

    Args:
        status: TicketStatus enum value

    Returns:
        String value for legacy Status enum
    """
    mapping = {
        TicketStatus.NOT_STARTED: "not_started",
        TicketStatus.IN_PROGRESS: "in_progress",
        TicketStatus.PAUSED: "paused",
        TicketStatus.COMPLETION_GATE_CHECK: "in_progress",  # No direct equivalent
        TicketStatus.COMPLETED: "completed",
        TicketStatus.PRODUCTION_GATE_CHECK: "completed",  # No direct equivalent
        TicketStatus.PRODUCTION_READY: "production_ready",
        TicketStatus.DEPLOYED: "deployed",
        TicketStatus.WONT_DO: "wont_do",
        TicketStatus.SUPERSEDED: "superseded",
    }
    return mapping.get(status, "not_started")


def map_priority(priority_value: str) -> Priority:
    """Map legacy Priority to ticket Priority."""
    mapping = {
        "critical": Priority.CRITICAL,
        "high": Priority.HIGH,
        "medium": Priority.MEDIUM,
        "low": Priority.LOW,
    }
    return mapping.get(priority_value.lower(), Priority.MEDIUM)


def map_task_type(task_type_value: str) -> TaskType:
    """Map legacy TaskType to ticket TaskType."""
    mapping = {
        "development": TaskType.DEVELOPMENT,
        "documentation": TaskType.DOCUMENTATION,
        "testing": TaskType.TESTING,
        "research": TaskType.RESEARCH,
        "review": TaskType.REVIEW,
        "infrastructure": TaskType.INFRASTRUCTURE,
        "gate": TaskType.GATE,
    }
    return mapping.get(task_type_value.lower(), TaskType.DEVELOPMENT)


# =============================================================================
# CRITERION GENERATION HELPERS
# =============================================================================


def generate_criterion_id() -> str:
    """Generate a unique criterion ID."""
    return f"crit-{uuid.uuid4().hex[:8]}"


def children_to_criteria(
    child_ids: List[str],
    description_template: str = "Child {} complete",
) -> List[Criterion]:
    """
    Convert a list of child IDs to CompletableTarget criteria.

    These criteria block COMPLETED status (children must complete before parent).

    Args:
        child_ids: List of child ticket IDs
        description_template: Template for criterion description (use {} for ID)

    Returns:
        List of Criterion objects with CompletableTarget
    """
    return [
        Criterion(
            id=generate_criterion_id(),
            description=description_template.format(child_id),
            target=CompletableTarget(
                completable_id=child_id,
                required_status=TicketStatus.COMPLETED,
            ),
            blocks_transition_to=TicketStatus.COMPLETED,
        )
        for child_id in child_ids
    ]


def dependencies_to_criteria(
    dependency_ids: List[str],
    description_template: str = "Dependency {} must complete",
) -> List[Criterion]:
    """
    Convert a list of dependency IDs to CompletableTarget criteria.

    These criteria block IN_PROGRESS status (dependencies must complete before starting).

    Args:
        dependency_ids: List of dependency ticket IDs
        description_template: Template for criterion description

    Returns:
        List of Criterion objects with CompletableTarget blocking IN_PROGRESS
    """
    return [
        Criterion(
            id=generate_criterion_id(),
            description=description_template.format(dep_id),
            target=CompletableTarget(
                completable_id=dep_id,
                required_status=TicketStatus.COMPLETED,
            ),
            blocks_transition_to=TicketStatus.IN_PROGRESS,
        )
        for dep_id in dependency_ids
    ]


def deliverables_to_criteria(
    deliverable_paths: List[str],
) -> List[Criterion]:
    """
    Convert deliverable paths to FileExistsTarget criteria.

    These criteria block COMPLETED status (files must exist for completion).

    Args:
        deliverable_paths: List of file paths

    Returns:
        List of Criterion objects with FileExistsTarget
    """
    if not deliverable_paths:
        return []

    return [
        Criterion(
            id=generate_criterion_id(),
            description=f"Deliverable exists: {path}",
            target=FileExistsTarget(paths=[path]),
            blocks_transition_to=TicketStatus.COMPLETED,
        )
        for path in deliverable_paths
    ]


# =============================================================================
# CRITERIA EXTRACTION HELPERS
# =============================================================================


def extract_child_ids(criteria: List[Criterion]) -> List[str]:
    """
    Extract child IDs from CompletableTarget criteria that block COMPLETED.

    Args:
        criteria: List of Criterion objects

    Returns:
        List of child ticket IDs
    """
    return [
        c.target.completable_id
        for c in criteria
        if isinstance(c.target, CompletableTarget)
        and c.blocks_transition_to == TicketStatus.COMPLETED
    ]


def extract_dependency_ids(criteria: List[Criterion]) -> List[str]:
    """
    Extract dependency IDs from CompletableTarget criteria that block IN_PROGRESS.

    Args:
        criteria: List of Criterion objects

    Returns:
        List of dependency ticket IDs
    """
    return [
        c.target.completable_id
        for c in criteria
        if isinstance(c.target, CompletableTarget)
        and c.blocks_transition_to == TicketStatus.IN_PROGRESS
    ]


def extract_deliverable_paths(criteria: List[Criterion]) -> List[str]:
    """
    Extract deliverable paths from FileExistsTarget criteria.

    Args:
        criteria: List of Criterion objects

    Returns:
        List of file paths
    """
    paths = []
    for c in criteria:
        if isinstance(c.target, FileExistsTarget):
            paths.extend(c.target.paths)
    return paths


# =============================================================================
# MODEL ADAPTER CLASS
# =============================================================================


class ModelAdapter:
    """
    Adapter for converting between legacy dataclass models and unified Pydantic ticket models.

    This class provides static methods for bidirectional conversion between:
    - Roadmap <-> RoadmapTicket
    - Track <-> TrackTicket
    - Sprint <-> SprintTicket
    - Task <-> TaskTicket

    Usage:
        # Convert legacy to ticket
        roadmap_ticket = ModelAdapter.roadmap_to_ticket(legacy_roadmap)

        # Convert ticket to legacy
        legacy_roadmap = ModelAdapter.ticket_to_roadmap(roadmap_ticket)
    """

    # =========================================================================
    # TASK CONVERSIONS
    # =========================================================================

    @staticmethod
    def task_to_ticket(task: "Task") -> Dict[str, Any]:
        """
        Convert a legacy Task dataclass to TaskTicket construction dict.

        Args:
            task: Legacy Task dataclass instance

        Returns:
            Dictionary suitable for constructing TaskTicket

        Note:
            Returns a dict rather than TaskTicket to avoid circular imports.
            Use: TaskTicket(**ModelAdapter.task_to_ticket(task))
        """
        now = datetime.now(timezone.utc)

        # Extract deliverable paths
        deliverable_paths = []
        if hasattr(task, 'deliverables') and task.deliverables:
            for d in task.deliverables:
                if hasattr(d, 'paths'):
                    deliverable_paths.extend(d.paths)

        # Extract dependency IDs
        dependency_ids = []
        if hasattr(task, 'depends_on') and task.depends_on:
            for dep in task.depends_on:
                if hasattr(dep, 'blocker_id'):
                    dependency_ids.append(dep.blocker_id)
                elif hasattr(dep, 'target_id'):
                    dependency_ids.append(dep.target_id)

        # Build criteria
        criteria = []
        criteria.extend(deliverables_to_criteria(deliverable_paths))
        criteria.extend(dependencies_to_criteria(dependency_ids))

        # Map status
        status_value = task.status.value if hasattr(task.status, 'value') else str(task.status)
        status = map_status_to_ticket_status(status_value)

        # Map priority
        priority_value = task.priority.value if hasattr(task.priority, 'value') else str(task.priority)
        priority = map_priority(priority_value)

        # Map task type
        task_type_value = task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type)
        task_type_detail = map_task_type(task_type_value)

        return {
            "id": task.id,
            "name": getattr(task, 'title', task.id),
            "description": getattr(task, 'description', ''),
            "status": status,
            "created_at": getattr(task, 'created', now),
            "updated_at": now,
            "started_at": getattr(task, 'started', None),
            "completed_at": getattr(task, 'completed', None),
            "priority": priority,
            "parent_ref": getattr(task, 'sprint_id', None),
            "criteria": criteria,
            # TaskTicket specific
            "task_type_detail": task_type_detail,
            "estimated_tokens": getattr(task, 'estimated_tokens', 0) or 0,
            "sprint_id": getattr(task, 'sprint_id', ''),
            "track_id": getattr(task, 'track_id', ''),
            "roadmap_id": getattr(task, 'roadmap_id', ''),
            "deferred": False,
        }

    @staticmethod
    def ticket_to_task_dict(ticket: Any) -> Dict[str, Any]:
        """
        Convert a TaskTicket to legacy Task construction dict.

        Args:
            ticket: TaskTicket Pydantic model instance

        Returns:
            Dictionary suitable for constructing legacy Task dataclass
        """
        # Extract deliverables and dependencies from criteria
        deliverable_paths = extract_deliverable_paths(ticket.criteria)
        dependency_ids = extract_dependency_ids(ticket.criteria)

        return {
            "id": ticket.id,
            "sprint_id": getattr(ticket, 'sprint_id', ''),
            "track_id": getattr(ticket, 'track_id', ''),
            "roadmap_id": getattr(ticket, 'roadmap_id', ''),
            "task_type": map_ticket_status_to_status(ticket.status),
            "title": ticket.name,
            "description": ticket.description or '',
            "status": map_ticket_status_to_status(ticket.status),
            "created": ticket.created_at,
            "started": ticket.started_at,
            "completed": ticket.completed_at,
            "priority": ticket.priority.value if ticket.priority else "medium",
            "estimated_tokens": getattr(ticket, 'estimated_tokens', 0),
            # These need to be constructed as proper objects
            "deliverable_paths": deliverable_paths,
            "dependency_ids": dependency_ids,
        }

    # =========================================================================
    # SPRINT CONVERSIONS
    # =========================================================================

    @staticmethod
    def sprint_to_ticket(sprint: "Sprint", task_ids: List[str]) -> Dict[str, Any]:
        """
        Convert a legacy Sprint dataclass to SprintTicket construction dict.

        Args:
            sprint: Legacy Sprint dataclass instance
            task_ids: List of task IDs belonging to this sprint

        Returns:
            Dictionary suitable for constructing SprintTicket
        """
        now = datetime.now(timezone.utc)

        # Build criteria from tasks (children)
        criteria = children_to_criteria(task_ids, "Task {} complete")

        # Add dependency criteria
        dependency_ids = []
        if hasattr(sprint, 'depends_on') and sprint.depends_on:
            for dep in sprint.depends_on:
                if hasattr(dep, 'blocker_id'):
                    dependency_ids.append(dep.blocker_id)
                elif hasattr(dep, 'target_id'):
                    dependency_ids.append(dep.target_id)
        criteria.extend(dependencies_to_criteria(dependency_ids))

        # Map status
        status_value = sprint.status.value if hasattr(sprint.status, 'value') else str(sprint.status)
        status = map_status_to_ticket_status(status_value)

        return {
            "id": sprint.id,
            "name": getattr(sprint, 'name', sprint.id),
            "description": getattr(sprint, 'description', ''),
            "status": status,
            "created_at": getattr(sprint, 'created', now),
            "updated_at": now,
            "started_at": getattr(sprint, 'started', None),
            "completed_at": getattr(sprint, 'completed', None),
            "parent_ref": getattr(sprint, 'track_id', None),
            "criteria": criteria,
            # SprintTicket specific
            "track_id": getattr(sprint, 'track_id', ''),
            "roadmap_id": getattr(sprint, 'roadmap_id', ''),
            "estimated_duration": getattr(sprint, 'metadata', {}).get('estimated_duration') if hasattr(sprint, 'metadata') else None,
        }

    @staticmethod
    def ticket_to_sprint_dict(ticket: Any) -> Dict[str, Any]:
        """
        Convert a SprintTicket to legacy Sprint construction dict.

        Args:
            ticket: SprintTicket Pydantic model instance

        Returns:
            Dictionary suitable for constructing legacy Sprint dataclass
        """
        task_ids = extract_child_ids(ticket.criteria)
        dependency_ids = extract_dependency_ids(ticket.criteria)

        return {
            "id": ticket.id,
            "track_id": getattr(ticket, 'track_id', ''),
            "roadmap_id": getattr(ticket, 'roadmap_id', ''),
            "name": ticket.name,
            "description": ticket.description or '',
            "status": map_ticket_status_to_status(ticket.status),
            "created": ticket.created_at,
            "started": ticket.started_at,
            "completed": ticket.completed_at,
            "task_ids": task_ids,
            "dependency_ids": dependency_ids,
        }

    # =========================================================================
    # TRACK CONVERSIONS
    # =========================================================================

    @staticmethod
    def track_to_ticket(track: "Track", sprint_ids: List[str]) -> Dict[str, Any]:
        """
        Convert a legacy Track dataclass to TrackTicket construction dict.

        Args:
            track: Legacy Track dataclass instance
            sprint_ids: List of sprint IDs belonging to this track

        Returns:
            Dictionary suitable for constructing TrackTicket
        """
        now = datetime.now(timezone.utc)

        # Build criteria from sprints (children)
        criteria = children_to_criteria(sprint_ids, "Sprint {} complete")

        # Add dependency criteria
        dependency_ids = []
        if hasattr(track, 'depends_on') and track.depends_on:
            for dep in track.depends_on:
                if hasattr(dep, 'blocker_id'):
                    dependency_ids.append(dep.blocker_id)
                elif hasattr(dep, 'target_id'):
                    dependency_ids.append(dep.target_id)
        criteria.extend(dependencies_to_criteria(dependency_ids))

        # Map status
        status_value = track.status.value if hasattr(track.status, 'value') else str(track.status)
        status = map_status_to_ticket_status(status_value)

        # Map priority
        priority_value = track.priority.value if hasattr(track.priority, 'value') else str(track.priority)
        priority = map_priority(priority_value)

        return {
            "id": track.id,
            "name": getattr(track, 'name', track.id),
            "description": getattr(track, 'description', ''),
            "status": status,
            "created_at": getattr(track, 'created', now),
            "updated_at": now,
            "started_at": getattr(track, 'started', None),
            "completed_at": getattr(track, 'completed', None),
            "priority": priority,
            "parent_ref": getattr(track, 'roadmap_id', None),
            "criteria": criteria,
            # TrackTicket specific
            "roadmap_id": getattr(track, 'roadmap_id', ''),
        }

    @staticmethod
    def ticket_to_track_dict(ticket: Any) -> Dict[str, Any]:
        """
        Convert a TrackTicket to legacy Track construction dict.

        Args:
            ticket: TrackTicket Pydantic model instance

        Returns:
            Dictionary suitable for constructing legacy Track dataclass
        """
        sprint_ids = extract_child_ids(ticket.criteria)
        dependency_ids = extract_dependency_ids(ticket.criteria)

        return {
            "id": ticket.id,
            "roadmap_id": getattr(ticket, 'roadmap_id', ''),
            "name": ticket.name,
            "description": ticket.description or '',
            "status": map_ticket_status_to_status(ticket.status),
            "priority": ticket.priority.value if ticket.priority else "medium",
            "created": ticket.created_at,
            "started": ticket.started_at,
            "completed": ticket.completed_at,
            "sprint_ids": sprint_ids,
            "dependency_ids": dependency_ids,
        }

    # =========================================================================
    # ROADMAP CONVERSIONS
    # =========================================================================

    @staticmethod
    def roadmap_to_ticket(roadmap: "Roadmap", track_ids: List[str]) -> Dict[str, Any]:
        """
        Convert a legacy Roadmap dataclass to RoadmapTicket construction dict.

        Args:
            roadmap: Legacy Roadmap dataclass instance
            track_ids: List of track IDs belonging to this roadmap

        Returns:
            Dictionary suitable for constructing RoadmapTicket
        """
        now = datetime.now(timezone.utc)

        # Build criteria from tracks (children)
        criteria = children_to_criteria(track_ids, "Track {} complete")

        # Map status
        status_value = roadmap.status.value if hasattr(roadmap.status, 'value') else str(roadmap.status)
        status = map_status_to_ticket_status(status_value)

        return {
            "id": roadmap.id,
            "name": getattr(roadmap, 'name', roadmap.id),
            "description": getattr(roadmap, 'description', ''),
            "status": status,
            "created_at": getattr(roadmap, 'created', now),
            "updated_at": now,
            "started_at": getattr(roadmap, 'started', None),
            "completed_at": getattr(roadmap, 'completed', None),
            "criteria": criteria,
            # RoadmapTicket specific
            "version": getattr(roadmap, 'version', '0.0.0'),
        }

    @staticmethod
    def ticket_to_roadmap_dict(ticket: Any) -> Dict[str, Any]:
        """
        Convert a RoadmapTicket to legacy Roadmap construction dict.

        Args:
            ticket: RoadmapTicket Pydantic model instance

        Returns:
            Dictionary suitable for constructing legacy Roadmap dataclass
        """
        track_ids = extract_child_ids(ticket.criteria)

        return {
            "id": ticket.id,
            "name": ticket.name,
            "description": ticket.description or '',
            "version": getattr(ticket, 'version', '0.0.0'),
            "status": map_ticket_status_to_status(ticket.status),
            "created": ticket.created_at,
            "started": ticket.started_at,
            "completed": ticket.completed_at,
            "track_ids": track_ids,
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Status mapping
    "map_status_to_ticket_status",
    "map_ticket_status_to_status",
    "map_priority",
    "map_task_type",
    # Criterion generation
    "generate_criterion_id",
    "children_to_criteria",
    "dependencies_to_criteria",
    "deliverables_to_criteria",
    # Criterion extraction
    "extract_child_ids",
    "extract_dependency_ids",
    "extract_deliverable_paths",
    # Main adapter
    "ModelAdapter",
]
