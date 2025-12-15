"""
Tests for vibey.mcp.utils.errors module.

Tests MCP server error classes.
"""

import pytest

from vibey.mcp.utils.errors import (
    VibeyMCPError,
    TaskNotFoundError,
    SprintNotFoundError,
    TrackNotFoundError,
    InvalidStateTransitionError,
    ValidationError,
)


class TestVibeyMCPError:
    """Test base VibeyMCPError class."""

    def test_message_only(self):
        """Test error with message only."""
        error = VibeyMCPError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.details == {}

    def test_with_details(self):
        """Test error with details."""
        error = VibeyMCPError("Error occurred", details={"key": "value"})
        assert "Details:" in str(error)
        assert error.details == {"key": "value"}

    def test_is_exception(self):
        """Test error is an Exception."""
        error = VibeyMCPError("Test")
        assert isinstance(error, Exception)

    def test_can_be_raised(self):
        """Test error can be raised and caught."""
        with pytest.raises(VibeyMCPError) as exc_info:
            raise VibeyMCPError("Test error")
        assert "Test error" in str(exc_info.value)


class TestTaskNotFoundError:
    """Test TaskNotFoundError class."""

    def test_message(self):
        """Test error message format."""
        error = TaskNotFoundError("task-001")
        assert "task-001" in str(error)
        assert "Task not found" in str(error)

    def test_task_id_attribute(self):
        """Test task_id attribute."""
        error = TaskNotFoundError("sprint-1-task-005")
        assert error.task_id == "sprint-1-task-005"

    def test_details(self):
        """Test details dict."""
        error = TaskNotFoundError("task-123")
        assert error.details["task_id"] == "task-123"

    def test_inheritance(self):
        """Test inherits from VibeyMCPError."""
        error = TaskNotFoundError("task-001")
        assert isinstance(error, VibeyMCPError)


class TestSprintNotFoundError:
    """Test SprintNotFoundError class."""

    def test_message(self):
        """Test error message format."""
        error = SprintNotFoundError("sprint-1")
        assert "sprint-1" in str(error)
        assert "Sprint not found" in str(error)

    def test_sprint_id_attribute(self):
        """Test sprint_id attribute."""
        error = SprintNotFoundError("feature-track-3")
        assert error.sprint_id == "feature-track-3"

    def test_details(self):
        """Test details dict."""
        error = SprintNotFoundError("sprint-abc")
        assert error.details["sprint_id"] == "sprint-abc"


class TestTrackNotFoundError:
    """Test TrackNotFoundError class."""

    def test_message(self):
        """Test error message format."""
        error = TrackNotFoundError("feature-track")
        assert "feature-track" in str(error)
        assert "Track not found" in str(error)

    def test_track_id_attribute(self):
        """Test track_id attribute."""
        error = TrackNotFoundError("documentation-track")
        assert error.track_id == "documentation-track"

    def test_details(self):
        """Test details dict."""
        error = TrackNotFoundError("track-xyz")
        assert error.details["track_id"] == "track-xyz"


class TestInvalidStateTransitionError:
    """Test InvalidStateTransitionError class."""

    def test_message(self):
        """Test error message format."""
        error = InvalidStateTransitionError(
            object_type="task",
            object_id="task-001",
            from_status="not_started",
            to_status="completed",
        )
        s = str(error)
        assert "task" in s
        assert "not_started" in s
        assert "completed" in s

    def test_attributes(self):
        """Test error attributes."""
        error = InvalidStateTransitionError(
            object_type="sprint",
            object_id="sprint-5",
            from_status="in_progress",
            to_status="not_started",
        )
        assert error.object_type == "sprint"
        assert error.object_id == "sprint-5"
        assert error.from_status == "in_progress"
        assert error.to_status == "not_started"

    def test_details(self):
        """Test details dict."""
        error = InvalidStateTransitionError(
            object_type="task",
            object_id="t-1",
            from_status="a",
            to_status="b",
        )
        assert error.details["object_type"] == "task"
        assert error.details["object_id"] == "t-1"
        assert error.details["from_status"] == "a"
        assert error.details["to_status"] == "b"


class TestValidationError:
    """Test ValidationError class."""

    def test_message(self):
        """Test error message format."""
        error = ValidationError(
            tool_name="start_task",
            field="task_id",
            error="Task ID is required",
        )
        s = str(error)
        assert "start_task" in s
        assert "task_id" in s
        assert "Task ID is required" in s

    def test_attributes(self):
        """Test error attributes."""
        error = ValidationError(
            tool_name="complete_sprint",
            field="sprint_id",
            error="Invalid format",
        )
        assert error.tool_name == "complete_sprint"
        assert error.field == "sprint_id"
        assert error.error == "Invalid format"

    def test_details(self):
        """Test details dict."""
        error = ValidationError(
            tool_name="tool",
            field="field",
            error="err",
        )
        assert error.details["tool_name"] == "tool"
        assert error.details["field"] == "field"
        assert error.details["error"] == "err"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
