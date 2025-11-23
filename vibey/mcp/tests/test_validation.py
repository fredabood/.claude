"""
Test validation utilities.
"""

import pytest
from vibey.mcp.utils.validation import (
    validate_task_id,
    validate_sprint_id,
    validate_track_id,
)
from vibey.mcp.utils.errors import ValidationError


class TestTaskIDValidation:
    """Test task ID validation."""

    def test_valid_task_id(self):
        """Test valid task ID passes validation."""
        validate_task_id("mcp-server-1-task-001")
        validate_task_id("documentation-system-3-task-005")
        # Should not raise

    def test_empty_task_id(self):
        """Test empty task ID raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_task_id("")

        assert "cannot be empty" in str(exc_info.value)

    def test_missing_task_separator(self):
        """Test task ID without '-task-' raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_task_id("invalid-id-001")

        assert "-task-" in str(exc_info.value)

    def test_invalid_format(self):
        """Test task ID with wrong format raises error."""
        with pytest.raises(ValidationError):
            validate_task_id("-task-001")  # Empty sprint portion

        with pytest.raises(ValidationError):
            validate_task_id("sprint-1-task-")  # Empty task number


class TestSprintIDValidation:
    """Test sprint ID validation."""

    def test_valid_sprint_id(self):
        """Test valid sprint ID passes validation."""
        validate_sprint_id("mcp-server-1")
        validate_sprint_id("documentation-system-3")
        # Should not raise

    def test_empty_sprint_id(self):
        """Test empty sprint ID raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_sprint_id("")

        assert "cannot be empty" in str(exc_info.value)

    def test_missing_hyphen(self):
        """Test sprint ID without hyphen raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_sprint_id("sprint1")

        assert "hyphen" in str(exc_info.value)


class TestTrackIDValidation:
    """Test track ID validation."""

    def test_valid_track_id(self):
        """Test valid track ID passes validation."""
        validate_track_id("mcp-server")
        validate_track_id("documentation-system")
        validate_track_id("goose-port")
        # Should not raise

    def test_empty_track_id(self):
        """Test empty track ID raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_track_id("")

        assert "cannot be empty" in str(exc_info.value)

    def test_uppercase_track_id(self):
        """Test uppercase track ID raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_track_id("MCP-Server")

        assert "lowercase" in str(exc_info.value)

    def test_spaces_in_track_id(self):
        """Test track ID with spaces raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_track_id("mcp server")

        assert "spaces" in str(exc_info.value)
