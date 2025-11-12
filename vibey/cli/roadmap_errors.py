"""
Roadmap CLI error handling using unified error system.

This module provides functions that raise unified VibeyError exceptions
for roadmap operations.

Usage:
    from vibey.cli.roadmap_errors import raise_roadmap_not_found, render_cli_error

    # Raise errors when problems occur
    if not roadmap_exists(directory):
        raise_roadmap_not_found(directory)

    # Catch and render at entry point
    try:
        operation()
    except VibeyError as e:
        print(render_cli_error(e))
        sys.exit(1)
"""

from typing import List, Optional
from vibey.common import (
    VibeyError,
    RoadmapNotFoundError,
    TrackNotFoundError,
    SprintNotFoundError,
    TaskNotFoundError,
    DependencyBlockedError,
    CircularDependencyError,
    InvalidStateTransitionError,
    QualityGateNotPassedError,
    ValidationError,
    FileNotFoundError as VibeyFileNotFoundError,
    ConcurrentModificationError,
)
from vibey.common.renderers import CLIErrorRenderer


# ============================================================================
# Global CLI Error Renderer
# ============================================================================

_cli_renderer = CLIErrorRenderer(use_colors=True)


def render_cli_error(error: VibeyError) -> str:
    """
    Render a VibeyError for CLI output.

    Args:
        error: VibeyError instance to render

    Returns:
        Formatted string ready for terminal output
    """
    return _cli_renderer.render(error)


def render_cli_errors(errors: List[VibeyError]) -> str:
    """
    Render multiple VibeyErrors for CLI output.

    Args:
        errors: List of VibeyError instances

    Returns:
        Formatted string with all errors
    """
    return _cli_renderer.render_multiple(errors)


# ============================================================================
# Roadmap Error Helpers
# ============================================================================

def raise_roadmap_not_found(searched_dir: str) -> None:
    """
    Raise RoadmapNotFoundError.

    Args:
        searched_dir: Directory that was searched

    Raises:
        RoadmapNotFoundError
    """
    raise RoadmapNotFoundError(searched_dir=searched_dir)


def raise_track_not_found(
    track_id: str,
    available_tracks: Optional[List[str]] = None
) -> None:
    """
    Raise TrackNotFoundError.

    Args:
        track_id: ID of track that wasn't found
        available_tracks: List of available track IDs

    Raises:
        TrackNotFoundError
    """
    raise TrackNotFoundError(
        track_id=track_id,
        available_tracks=available_tracks
    )


def raise_sprint_not_found(
    sprint_id: str,
    track_id: Optional[str] = None
) -> None:
    """
    Raise SprintNotFoundError.

    Args:
        sprint_id: ID of sprint that wasn't found
        track_id: ID of parent track (if known)

    Raises:
        SprintNotFoundError
    """
    raise SprintNotFoundError(
        sprint_id=sprint_id,
        track_id=track_id
    )


def raise_task_not_found(
    task_id: str,
    sprint_id: Optional[str] = None
) -> None:
    """
    Raise TaskNotFoundError.

    Args:
        task_id: ID of task that wasn't found
        sprint_id: ID of parent sprint (if known)

    Raises:
        TaskNotFoundError
    """
    raise TaskNotFoundError(
        task_id=task_id,
        sprint_id=sprint_id
    )


# ============================================================================
# Dependency Error Helpers
# ============================================================================

def raise_dependency_blocked(
    object_id: str,
    object_type: str,
    blocker_id: str,
    blocker_type: str,
    required_status: str,
    current_status: str,
) -> None:
    """
    Raise DependencyBlockedError.

    Args:
        object_id: ID of blocked object
        object_type: Type of blocked object (sprint, task, etc.)
        blocker_id: ID of blocking object
        blocker_type: Type of blocking object
        required_status: Required status of blocker
        current_status: Current status of blocker

    Raises:
        DependencyBlockedError
    """
    raise DependencyBlockedError(
        object_id=object_id,
        object_type=object_type,
        blocker_id=blocker_id,
        blocker_type=blocker_type,
        required_status=required_status,
        current_status=current_status,
    )


def raise_circular_dependency(
    object_id: str,
    dependency_chain: List[str]
) -> None:
    """
    Raise CircularDependencyError.

    Args:
        object_id: ID of object in circular dependency
        dependency_chain: List of IDs forming the cycle

    Raises:
        CircularDependencyError
    """
    raise CircularDependencyError(dependency_chain=dependency_chain)


# ============================================================================
# State Error Helpers
# ============================================================================

def raise_invalid_status_transition(
    object_id: str,
    current_status: str,
    attempted_status: str,
    valid_transitions: List[str]
) -> None:
    """
    Raise InvalidStateTransitionError.

    Args:
        object_id: ID of object
        current_status: Current status
        attempted_status: Status user tried to transition to
        valid_transitions: List of valid next statuses

    Raises:
        InvalidStateTransitionError
    """
    raise InvalidStateTransitionError(
        object_id=object_id,
        current_status=current_status,
        attempted_status=attempted_status,
        valid_transitions=valid_transitions,
    )


def raise_completion_gate_not_passed(
    sprint_id: str,
    incomplete_gates: List[str]
) -> None:
    """
    Raise QualityGateNotPassedError for completion gates.

    Args:
        sprint_id: ID of sprint
        incomplete_gates: List of incomplete gate names

    Raises:
        QualityGateNotPassedError
    """
    raise QualityGateNotPassedError(
        object_id=sprint_id,
        gate_type="completion",
        incomplete_gates=incomplete_gates,
    )


def raise_production_gate_not_passed(
    sprint_id: str,
    incomplete_gates: List[str]
) -> None:
    """
    Raise QualityGateNotPassedError for production gates.

    Args:
        sprint_id: ID of sprint
        incomplete_gates: List of incomplete gate names

    Raises:
        QualityGateNotPassedError
    """
    raise QualityGateNotPassedError(
        object_id=sprint_id,
        gate_type="production",
        incomplete_gates=incomplete_gates,
    )


# ============================================================================
# Validation Error Helpers
# ============================================================================

def raise_validation_failed(
    object_type: str,
    object_id: str,
    errors: List[str]
) -> None:
    """
    Raise ValidationError.

    Args:
        object_type: Type of object (sprint, task, track, etc.)
        object_id: ID of object
        errors: List of validation error messages

    Raises:
        ValidationError
    """
    raise ValidationError(
        object_type=object_type,
        object_id=object_id,
        errors=errors,
    )


# ============================================================================
# File System Error Helpers
# ============================================================================

def raise_file_not_found(file_path: str, file_type: str) -> None:
    """
    Raise FileNotFoundError.

    Args:
        file_path: Path to missing file
        file_type: Type of file (e.g., "Sprint", "Task", "Roadmap")

    Raises:
        VibeyFileNotFoundError
    """
    raise VibeyFileNotFoundError(
        file_path=file_path,
        file_type=file_type,
    )


# ============================================================================
# Concurrency Error Helpers
# ============================================================================

def raise_concurrent_modification(
    object_id: str,
    expected_version: str,
    actual_version: str
) -> None:
    """
    Raise ConcurrentModificationError.

    Args:
        object_id: ID of modified object
        expected_version: Expected version/timestamp
        actual_version: Actual version/timestamp

    Raises:
        ConcurrentModificationError
    """
    raise ConcurrentModificationError(
        object_id=object_id,
        expected_version=expected_version,
        actual_version=actual_version,
    )
