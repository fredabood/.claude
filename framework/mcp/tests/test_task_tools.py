"""
Integration tests for task management tools.

Tests the complete flow: tool handler → adapter → roadmap system.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from framework.mcp.tools.task_tools import (
    handle_start_task,
    handle_complete_task,
    handle_query_task,
)
from framework.mcp.adapters.roadmap_adapter import RoadmapAdapter
from framework.mcp.utils.errors import (
    TaskNotFoundError,
    InvalidStateTransitionError,
)


@pytest.fixture
def mock_adapter():
    """Create a mock roadmap adapter for testing."""
    return Mock(spec=RoadmapAdapter)


@pytest.mark.asyncio
class TestStartTask:
    """Test vibey_start_task tool."""

    async def test_start_task_success(self, mock_adapter):
        """Test successful task start."""
        # Mock adapter response
        mock_adapter.start_task.return_value = {
            "success": True,
            "task_id": "test-sprint-1-task-001",
            "status": "in_progress",
            "started": "2025-11-10T12:00:00+00:00"
        }

        # Call handler
        result = await handle_start_task(
            {"task_id": "test-sprint-1-task-001"},
            mock_adapter
        )

        # Verify
        assert result["isError"] is False
        assert "started successfully" in result["content"][0]["text"]
        mock_adapter.start_task.assert_called_once_with("test-sprint-1-task-001")

    async def test_start_task_not_found(self, mock_adapter):
        """Test starting a task that doesn't exist."""
        # Mock adapter to raise error
        mock_adapter.start_task.side_effect = TaskNotFoundError("test-sprint-1-task-001")

        # Call handler
        result = await handle_start_task(
            {"task_id": "test-sprint-1-task-001"},
            mock_adapter
        )

        # Verify error response
        assert result["isError"] is True
        assert "not found" in result["content"][0]["text"].lower()

    async def test_start_task_invalid_transition(self, mock_adapter):
        """Test starting a task that's already in progress."""
        # Mock adapter to raise error
        mock_adapter.start_task.side_effect = InvalidStateTransitionError(
            "task", "test-sprint-1-task-001", "completed", "in_progress"
        )

        # Call handler
        result = await handle_start_task(
            {"task_id": "test-sprint-1-task-001"},
            mock_adapter
        )

        # Verify error response
        assert result["isError"] is True
        assert "transition" in result["content"][0]["text"].lower()


@pytest.mark.asyncio
class TestCompleteTask:
    """Test vibey_complete_task tool."""

    async def test_complete_task_success(self, mock_adapter):
        """Test successful task completion."""
        # Mock adapter response
        mock_adapter.complete_task.return_value = {
            "success": True,
            "task_id": "test-sprint-1-task-001",
            "status": "completed",
            "completed": "2025-11-10T12:00:00+00:00",
            "actual_tokens": 5000
        }

        # Call handler
        result = await handle_complete_task(
            {"task_id": "test-sprint-1-task-001", "actual_tokens": 5000},
            mock_adapter
        )

        # Verify
        assert result["isError"] is False
        assert "completed successfully" in result["content"][0]["text"]
        assert "5000" in result["content"][0]["text"]
        mock_adapter.complete_task.assert_called_once_with("test-sprint-1-task-001", 5000)

    async def test_complete_task_without_tokens(self, mock_adapter):
        """Test completing task without specifying tokens."""
        # Mock adapter response
        mock_adapter.complete_task.return_value = {
            "success": True,
            "task_id": "test-sprint-1-task-001",
            "status": "completed",
            "completed": "2025-11-10T12:00:00+00:00",
            "actual_tokens": None
        }

        # Call handler
        result = await handle_complete_task(
            {"task_id": "test-sprint-1-task-001"},
            mock_adapter
        )

        # Verify
        assert result["isError"] is False
        assert "completed successfully" in result["content"][0]["text"]
        mock_adapter.complete_task.assert_called_once_with("test-sprint-1-task-001", None)

    async def test_complete_task_already_completed(self, mock_adapter):
        """Test completing a task that's already completed."""
        # Mock adapter response
        mock_adapter.complete_task.return_value = {
            "success": True,
            "task_id": "test-sprint-1-task-001",
            "status": "completed",
            "already_completed": True
        }

        # Call handler
        result = await handle_complete_task(
            {"task_id": "test-sprint-1-task-001"},
            mock_adapter
        )

        # Verify
        assert result["isError"] is False
        assert "already completed" in result["content"][0]["text"].lower()

    async def test_complete_task_not_in_progress(self, mock_adapter):
        """Test completing a task that's not in progress."""
        # Mock adapter to raise error
        mock_adapter.complete_task.side_effect = InvalidStateTransitionError(
            "task", "test-sprint-1-task-001", "not_started", "completed"
        )

        # Call handler
        result = await handle_complete_task(
            {"task_id": "test-sprint-1-task-001"},
            mock_adapter
        )

        # Verify error response
        assert result["isError"] is True
        assert "transition" in result["content"][0]["text"].lower()


@pytest.mark.asyncio
class TestQueryTask:
    """Test vibey_query_task tool."""

    async def test_query_task_success(self, mock_adapter):
        """Test successful task query."""
        # Mock adapter response
        mock_adapter.query_task.return_value = {
            "id": "test-sprint-1-task-001",
            "title": "Test Task",
            "sprint_id": "test-sprint-1",
            "track_id": "test-track",
            "task_type": "development",
            "status": "in_progress",
            "blocked": False,
            "description": "A test task for testing",
            "created": "2025-11-10T10:00:00+00:00",
            "started": "2025-11-10T11:00:00+00:00",
            "completed": None,
            "assigned_agent": "web-developer",
            "priority": "high",
            "complexity": "medium",
            "estimated_tokens": 3000,
            "actual_tokens": None
        }

        # Call handler
        result = await handle_query_task(
            {"task_id": "test-sprint-1-task-001"},
            mock_adapter
        )

        # Verify
        assert result["isError"] is False
        text = result["content"][0]["text"]
        assert "Test Task" in text
        assert "test-sprint-1" in text
        assert "in_progress" in text
        assert "web-developer" in text
        assert "high" in text
        assert "3000" in text
        mock_adapter.query_task.assert_called_once_with("test-sprint-1-task-001")

    async def test_query_task_not_found(self, mock_adapter):
        """Test querying a task that doesn't exist."""
        # Mock adapter to raise error
        mock_adapter.query_task.side_effect = TaskNotFoundError("test-sprint-1-task-999")

        # Call handler
        result = await handle_query_task(
            {"task_id": "test-sprint-1-task-999"},
            mock_adapter
        )

        # Verify error response
        assert result["isError"] is True
        assert "not found" in result["content"][0]["text"].lower()

    async def test_query_task_minimal_data(self, mock_adapter):
        """Test querying a task with minimal data."""
        # Mock adapter response with minimal fields
        mock_adapter.query_task.return_value = {
            "id": "test-sprint-1-task-001",
            "title": "Minimal Task",
            "sprint_id": "test-sprint-1",
            "track_id": "test-track",
            "task_type": "development",
            "status": "not_started",
            "blocked": False,
            "description": None,
            "created": "2025-11-10T10:00:00+00:00",
            "started": None,
            "completed": None,
            "assigned_agent": None,
            "priority": None,
            "complexity": None,
            "estimated_tokens": None,
            "actual_tokens": None
        }

        # Call handler
        result = await handle_query_task(
            {"task_id": "test-sprint-1-task-001"},
            mock_adapter
        )

        # Verify
        assert result["isError"] is False
        text = result["content"][0]["text"]
        assert "Minimal Task" in text
        assert "not_started" in text
        # Should handle None values gracefully


@pytest.mark.asyncio
class TestTaskToolsValidation:
    """Test input validation for task tools."""

    async def test_start_task_invalid_id_format(self, mock_adapter):
        """Test starting task with invalid ID format."""
        # Call handler with invalid ID
        result = await handle_start_task(
            {"task_id": "invalid-id"},
            mock_adapter
        )

        # Should get validation error
        assert result["isError"] is True
        # Adapter should not be called
        mock_adapter.start_task.assert_not_called()

    async def test_complete_task_negative_tokens(self, mock_adapter):
        """Test completing task with negative tokens."""
        # This would be caught by JSON schema validation
        # Testing the handler's robustness
        mock_adapter.complete_task.return_value = {
            "success": True,
            "task_id": "test-sprint-1-task-001",
            "status": "completed",
            "completed": "2025-11-10T12:00:00+00:00",
            "actual_tokens": -1000  # Invalid but adapter accepts it
        }

        result = await handle_complete_task(
            {"task_id": "test-sprint-1-task-001", "actual_tokens": -1000},
            mock_adapter
        )

        # Handler should still work (validation happens at schema level)
        assert result["isError"] is False


@pytest.mark.asyncio
class TestTaskToolsErrorHandling:
    """Test error handling in task tools."""

    async def test_start_task_unexpected_error(self, mock_adapter):
        """Test handling of unexpected errors."""
        # Mock adapter to raise unexpected error
        mock_adapter.start_task.side_effect = Exception("Database connection failed")

        result = await handle_start_task(
            {"task_id": "test-sprint-1-task-001"},
            mock_adapter
        )

        # Should return error with message
        assert result["isError"] is True
        assert "unexpected error" in result["content"][0]["text"].lower()

    async def test_complete_task_file_permission_error(self, mock_adapter):
        """Test handling of file permission errors."""
        # Mock adapter to raise permission error
        mock_adapter.complete_task.side_effect = PermissionError("Cannot write to file")

        result = await handle_complete_task(
            {"task_id": "test-sprint-1-task-001"},
            mock_adapter
        )

        # Should return error
        assert result["isError"] is True
        assert "unexpected error" in result["content"][0]["text"].lower()
