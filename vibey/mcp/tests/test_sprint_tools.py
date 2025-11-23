"""
Integration tests for sprint management tools.

Tests the complete flow: tool handler → adapter → roadmap system.
"""

import pytest
from unittest.mock import Mock

from vibey.mcp.tools.sprint_tools import (
    handle_start_sprint,
    handle_complete_sprint,
    handle_refresh_progress,
    handle_query_sprint,
)
from vibey.mcp.adapters.roadmap_adapter import RoadmapAdapter
from vibey.mcp.utils.errors import (
    SprintNotFoundError,
    InvalidStateTransitionError,
)


@pytest.fixture
def mock_adapter():
    """Create a mock roadmap adapter for testing."""
    return Mock(spec=RoadmapAdapter)


@pytest.mark.asyncio
class TestStartSprint:
    """Test vibey_start_sprint tool."""

    async def test_start_sprint_success(self, mock_adapter):
        """Test successful sprint start."""
        mock_adapter.start_sprint.return_value = {
            "success": True,
            "sprint_id": "test-sprint-1",
            "status": "in_progress",
            "started": "2025-11-10T12:00:00+00:00"
        }

        result = await handle_start_sprint(
            {"sprint_id": "test-sprint-1"},
            mock_adapter
        )

        assert result["isError"] is False
        assert "started successfully" in result["content"][0]["text"]
        mock_adapter.start_sprint.assert_called_once_with("test-sprint-1")

    async def test_start_sprint_not_found(self, mock_adapter):
        """Test starting a sprint that doesn't exist."""
        mock_adapter.start_sprint.side_effect = SprintNotFoundError("test-sprint-999")

        result = await handle_start_sprint(
            {"sprint_id": "test-sprint-999"},
            mock_adapter
        )

        assert result["isError"] is True
        assert "not found" in result["content"][0]["text"].lower()

    async def test_start_sprint_already_started(self, mock_adapter):
        """Test starting a sprint that's already in progress."""
        mock_adapter.start_sprint.side_effect = InvalidStateTransitionError(
            "sprint", "test-sprint-1", "in_progress", "in_progress"
        )

        result = await handle_start_sprint(
            {"sprint_id": "test-sprint-1"},
            mock_adapter
        )

        assert result["isError"] is True


@pytest.mark.asyncio
class TestCompleteSprint:
    """Test vibey_complete_sprint tool."""

    async def test_complete_sprint_success(self, mock_adapter):
        """Test successful sprint completion."""
        mock_adapter.complete_sprint.return_value = {
            "success": True,
            "sprint_id": "test-sprint-1",
            "status": "completed",
            "completed": "2025-11-10T14:00:00+00:00",
            "tasks_completed": 8,
            "tasks_total": 8
        }

        result = await handle_complete_sprint(
            {"sprint_id": "test-sprint-1"},
            mock_adapter
        )

        assert result["isError"] is False
        assert "completed successfully" in result["content"][0]["text"]
        assert "8/8" in result["content"][0]["text"]
        mock_adapter.complete_sprint.assert_called_once_with("test-sprint-1")

    async def test_complete_sprint_invalid_state(self, mock_adapter):
        """Test completing a sprint from invalid state."""
        mock_adapter.complete_sprint.side_effect = InvalidStateTransitionError(
            "sprint", "test-sprint-1", "not_started", "completed"
        )

        result = await handle_complete_sprint(
            {"sprint_id": "test-sprint-1"},
            mock_adapter
        )

        assert result["isError"] is True
        assert "transition" in result["content"][0]["text"].lower()


@pytest.mark.asyncio
class TestRefreshProgress:
    """Test vibey_refresh_progress tool."""

    async def test_refresh_progress_success(self, mock_adapter):
        """Test successful progress refresh."""
        mock_adapter.refresh_progress.return_value = {
            "success": True,
            "progressions": [
                {
                    "object_id": "test-sprint-1",
                    "from_status": "in_progress",
                    "to_status": "completion_gate_check"
                },
                {
                    "object_id": "test-sprint-2",
                    "from_status": "completion_gate_check",
                    "to_status": "production_ready"
                }
            ],
            "updates": {
                "sprints": 2,
                "tracks": 1
            }
        }

        result = await handle_refresh_progress({}, mock_adapter)

        assert result["isError"] is False
        text = result["content"][0]["text"]
        assert "refreshed successfully" in text.lower()
        assert "test-sprint-1" in text
        assert "test-sprint-2" in text
        mock_adapter.refresh_progress.assert_called_once()

    async def test_refresh_progress_no_changes(self, mock_adapter):
        """Test refresh when no progressions occur."""
        mock_adapter.refresh_progress.return_value = {
            "success": True,
            "progressions": [],
            "updates": {
                "sprints": 0,
                "tracks": 0
            }
        }

        result = await handle_refresh_progress({}, mock_adapter)

        assert result["isError"] is False
        assert "refreshed successfully" in result["content"][0]["text"].lower()

    async def test_refresh_progress_failure(self, mock_adapter):
        """Test refresh progress failure."""
        mock_adapter.refresh_progress.side_effect = Exception("Script execution failed")

        result = await handle_refresh_progress({}, mock_adapter)

        assert result["isError"] is True


@pytest.mark.asyncio
class TestQuerySprint:
    """Test vibey_query_sprint tool."""

    async def test_query_sprint_success(self, mock_adapter):
        """Test successful sprint query."""
        mock_adapter.query_sprint.return_value = {
            "id": "test-sprint-1",
            "name": "Test Sprint",
            "track_id": "test-track",
            "roadmap_id": "test-roadmap",
            "status": "in_progress",
            "blocked": False,
            "created": "2025-11-10T10:00:00+00:00",
            "started": "2025-11-10T11:00:00+00:00",
            "completed": None,
            "progress": {
                "development_tasks_total": 8,
                "development_tasks_completed": 6,
                "completion_gate_tasks_total": 0,
                "completion_gate_tasks_completed": 0,
                "production_gate_tasks_total": 0,
                "production_gate_tasks_completed": 0,
                "tasks_total": 8,
                "tasks_completed": 6,
                "completion_percent": 75
            }
        }

        result = await handle_query_sprint(
            {"sprint_id": "test-sprint-1"},
            mock_adapter
        )

        assert result["isError"] is False
        text = result["content"][0]["text"]
        assert "Test Sprint" in text
        assert "test-track" in text
        assert "in_progress" in text
        assert "75%" in text
        assert "6/8" in text
        mock_adapter.query_sprint.assert_called_once_with("test-sprint-1")

    async def test_query_sprint_with_gates(self, mock_adapter):
        """Test querying sprint with completion gates."""
        mock_adapter.query_sprint.return_value = {
            "id": "test-sprint-1",
            "name": "Test Sprint",
            "track_id": "test-track",
            "roadmap_id": "test-roadmap",
            "status": "completion_gate_check",
            "blocked": False,
            "created": "2025-11-10T10:00:00+00:00",
            "started": "2025-11-10T11:00:00+00:00",
            "completed": None,
            "progress": {
                "development_tasks_total": 8,
                "development_tasks_completed": 8,
                "completion_gate_tasks_total": 3,
                "completion_gate_tasks_completed": 2,
                "production_gate_tasks_total": 2,
                "production_gate_tasks_completed": 0,
                "tasks_total": 13,
                "tasks_completed": 10,
                "completion_percent": 77
            }
        }

        result = await handle_query_sprint(
            {"sprint_id": "test-sprint-1"},
            mock_adapter
        )

        assert result["isError"] is False
        text = result["content"][0]["text"]
        assert "Completion Gates: 2/3" in text
        assert "Production Gates: 0/2" in text

    async def test_query_sprint_not_found(self, mock_adapter):
        """Test querying a sprint that doesn't exist."""
        mock_adapter.query_sprint.side_effect = SprintNotFoundError("test-sprint-999")

        result = await handle_query_sprint(
            {"sprint_id": "test-sprint-999"},
            mock_adapter
        )

        assert result["isError"] is True
        assert "not found" in result["content"][0]["text"].lower()


@pytest.mark.asyncio
class TestSprintToolsValidation:
    """Test input validation for sprint tools."""

    async def test_start_sprint_invalid_id(self, mock_adapter):
        """Test starting sprint with invalid ID format."""
        result = await handle_start_sprint(
            {"sprint_id": "invalid"},
            mock_adapter
        )

        # Validation should catch this
        assert result["isError"] is True
        mock_adapter.start_sprint.assert_not_called()

    async def test_refresh_progress_no_args(self, mock_adapter):
        """Test refresh progress with empty arguments."""
        mock_adapter.refresh_progress.return_value = {
            "success": True,
            "progressions": [],
            "updates": {"sprints": "calculated", "tracks": "calculated"}
        }

        result = await handle_refresh_progress({}, mock_adapter)

        assert result["isError"] is False
        mock_adapter.refresh_progress.assert_called_once()
