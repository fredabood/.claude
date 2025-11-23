"""
Input Validation Utilities.

Utilities for validating MCP tool inputs against JSON schemas.
"""

from typing import Any, Dict
from jsonschema import validate as jsonschema_validate
from jsonschema import ValidationError as JSONSchemaValidationError

from .errors import ValidationError


def validate_tool_input(tool_name: str, arguments: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate tool input arguments against JSON schema.

    Args:
        tool_name: Name of the tool being validated
        arguments: Input arguments to validate
        schema: JSON schema to validate against

    Raises:
        ValidationError: If validation fails

    Example:
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "task_id": {"type": "string"}
        ...     },
        ...     "required": ["task_id"]
        ... }
        >>> validate_tool_input("vibey_start_task", {"task_id": "task-001"}, schema)
    """
    try:
        jsonschema_validate(instance=arguments, schema=schema)
    except JSONSchemaValidationError as e:
        # Extract field name from JSON path
        field = e.path[0] if e.path else "arguments"
        raise ValidationError(tool_name, str(field), e.message)


def validate_task_id(task_id: str) -> None:
    """
    Validate task ID format.

    Task IDs should follow the pattern: {sprint-id}-task-{number}

    Args:
        task_id: Task ID to validate

    Raises:
        ValidationError: If task ID format is invalid

    Example:
        >>> validate_task_id("mcp-server-1-task-001")
        >>> validate_task_id("invalid")  # Raises ValidationError
    """
    if not task_id:
        raise ValidationError("task_id", "task_id", "Task ID cannot be empty")

    if "-task-" not in task_id:
        raise ValidationError(
            "task_id",
            "task_id",
            "Task ID must contain '-task-' (e.g., 'sprint-1-task-001')"
        )

    parts = task_id.split("-task-")
    if len(parts) != 2:
        raise ValidationError(
            "task_id",
            "task_id",
            "Task ID must have format: {sprint-id}-task-{number}"
        )

    sprint_id, task_num = parts
    if not sprint_id:
        raise ValidationError(
            "task_id",
            "task_id",
            "Task ID sprint portion cannot be empty"
        )

    if not task_num:
        raise ValidationError(
            "task_id",
            "task_id",
            "Task ID number portion cannot be empty"
        )


def validate_sprint_id(sprint_id: str) -> None:
    """
    Validate sprint ID format.

    Sprint IDs should follow the pattern: {track-id}-{number}

    Args:
        sprint_id: Sprint ID to validate

    Raises:
        ValidationError: If sprint ID format is invalid
    """
    if not sprint_id:
        raise ValidationError("sprint_id", "sprint_id", "Sprint ID cannot be empty")

    # Sprint IDs should contain at least one hyphen
    if "-" not in sprint_id:
        raise ValidationError(
            "sprint_id",
            "sprint_id",
            "Sprint ID must contain hyphen (e.g., 'mcp-server-1')"
        )


def validate_track_id(track_id: str) -> None:
    """
    Validate track ID format.

    Args:
        track_id: Track ID to validate

    Raises:
        ValidationError: If track ID format is invalid
    """
    if not track_id:
        raise ValidationError("track_id", "track_id", "Track ID cannot be empty")

    # Track IDs should be lowercase with hyphens
    if track_id != track_id.lower():
        raise ValidationError(
            "track_id",
            "track_id",
            "Track ID must be lowercase"
        )

    if " " in track_id:
        raise ValidationError(
            "track_id",
            "track_id",
            "Track ID cannot contain spaces (use hyphens)"
        )
