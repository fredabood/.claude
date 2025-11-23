"""
MCP Server Error Classes.

Custom exceptions for Vibey MCP server operations.
"""


class VibeyMCPError(Exception):
    """Base exception for Vibey MCP server errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class TaskNotFoundError(VibeyMCPError):
    """Task not found in roadmap."""

    def __init__(self, task_id: str):
        super().__init__(
            f"Task not found: {task_id}",
            details={"task_id": task_id}
        )
        self.task_id = task_id


class SprintNotFoundError(VibeyMCPError):
    """Sprint not found in roadmap."""

    def __init__(self, sprint_id: str):
        super().__init__(
            f"Sprint not found: {sprint_id}",
            details={"sprint_id": sprint_id}
        )
        self.sprint_id = sprint_id


class TrackNotFoundError(VibeyMCPError):
    """Track not found in roadmap."""

    def __init__(self, track_id: str):
        super().__init__(
            f"Track not found: {track_id}",
            details={"track_id": track_id}
        )
        self.track_id = track_id


class InvalidStateTransitionError(VibeyMCPError):
    """Invalid state transition attempted."""

    def __init__(self, object_type: str, object_id: str, from_status: str, to_status: str):
        super().__init__(
            f"Invalid {object_type} transition: {from_status} → {to_status}",
            details={
                "object_type": object_type,
                "object_id": object_id,
                "from_status": from_status,
                "to_status": to_status
            }
        )
        self.object_type = object_type
        self.object_id = object_id
        self.from_status = from_status
        self.to_status = to_status


class ValidationError(VibeyMCPError):
    """Tool input validation failed."""

    def __init__(self, tool_name: str, field: str, error: str):
        super().__init__(
            f"Validation error in {tool_name}.{field}: {error}",
            details={
                "tool_name": tool_name,
                "field": field,
                "error": error
            }
        )
        self.tool_name = tool_name
        self.field = field
        self.error = error
