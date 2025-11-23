"""
Integration tests for query tools.

Tests the complete flow: tool handler → adapter → roadmap system.
"""

import pytest
from unittest.mock import Mock

from vibey.mcp.tools.query_tools import (
    handle_query_track,
    handle_list_blockers,
    handle_list_dependencies,
    handle_roadmap_status,
)
from vibey.mcp.adapters.roadmap_adapter import RoadmapAdapter
from vibey.mcp.utils.errors import TrackNotFoundError


@pytest.fixture
def mock_adapter():
    """Create a mock roadmap adapter for testing."""
    return Mock(spec=RoadmapAdapter)


@pytest.mark.asyncio
class TestQueryTrack:
    """Test vibey_query_track tool."""

    async def test_query_track_success(self, mock_adapter):
        """Test successful track query."""
        mock_adapter.query_track.return_value = {
            "id": "test-track",
            "name": "Test Track",
            "roadmap_id": "test-roadmap",
            "status": "in_progress",
            "blocked": False,
            "priority": "high",
            "created": "2025-11-01T00:00:00+00:00",
            "started": "2025-11-10T00:00:00+00:00",
            "completed": None,
            "estimated_duration": "8 weeks",
            "progress": {
                "sprints_total": 4,
                "sprints_completed": 2,
                "tasks_total": 32,
                "tasks_completed": 16,
                "completion_percent": 50
            }
        }

        result = await handle_query_track(
            {"track_id": "test-track"},
            mock_adapter
        )

        assert result["isError"] is False
        text = result["content"][0]["text"]
        assert "Test Track" in text
        assert "high" in text
        assert "50%" in text
        assert "2/4" in text
        assert "8 weeks" in text
        mock_adapter.query_track.assert_called_once_with("test-track")

    async def test_query_track_not_found(self, mock_adapter):
        """Test querying a track that doesn't exist."""
        mock_adapter.query_track.side_effect = TrackNotFoundError("unknown-track")

        result = await handle_query_track(
            {"track_id": "unknown-track"},
            mock_adapter
        )

        assert result["isError"] is True
        assert "not found" in result["content"][0]["text"].lower()


@pytest.mark.asyncio
class TestListBlockers:
    """Test vibey_list_blockers tool."""

    async def test_list_blockers_found(self, mock_adapter):
        """Test listing blockers when some exist."""
        mock_adapter.list_blockers.return_value = [
            {
                "blocked_object_id": "test-sprint-3",
                "dependency_id": "test-sprint-2",
                "dependency_type": "sprint",
                "current_status": "in_progress",
                "required_status": "completed",
                "blocking_since": "2025-11-10T10:00:00+00:00"
            },
            {
                "blocked_object_id": "test-sprint-4",
                "dependency_id": "test-track-1",
                "dependency_type": "track",
                "current_status": "not_started",
                "required_status": "completed",
                "blocking_since": "2025-11-10T11:00:00+00:00"
            }
        ]

        result = await handle_list_blockers({}, mock_adapter)

        assert result["isError"] is False
        text = result["content"][0]["text"]
        assert "2 found" in text
        assert "test-sprint-3" in text
        assert "test-sprint-2" in text
        assert "test-sprint-4" in text
        mock_adapter.list_blockers.assert_called_once_with(None)

    async def test_list_blockers_none_found(self, mock_adapter):
        """Test listing blockers when none exist."""
        mock_adapter.list_blockers.return_value = []

        result = await handle_list_blockers({}, mock_adapter)

        assert result["isError"] is False
        assert "no blockers found" in result["content"][0]["text"].lower()

    async def test_list_blockers_filtered(self, mock_adapter):
        """Test listing blockers filtered by object ID."""
        mock_adapter.list_blockers.return_value = [
            {
                "blocked_object_id": "test-sprint-3",
                "dependency_id": "test-sprint-2",
                "dependency_type": "sprint",
                "current_status": "in_progress",
                "required_status": "completed",
                "blocking_since": None
            }
        ]

        result = await handle_list_blockers(
            {"object_id": "test-sprint-3"},
            mock_adapter
        )

        assert result["isError"] is False
        assert "test-sprint-3" in result["content"][0]["text"]
        mock_adapter.list_blockers.assert_called_once_with("test-sprint-3")


@pytest.mark.asyncio
class TestListDependencies:
    """Test vibey_list_dependencies tool."""

    async def test_list_dependencies_unsatisfied_only(self, mock_adapter):
        """Test listing only unsatisfied dependencies."""
        mock_adapter.list_dependencies.return_value = [
            {
                "dependency_id": "test-sprint-1",
                "dependency_type": "sprint",
                "current_status": "in_progress",
                "required_status": "completed",
                "is_satisfied": False,
                "reason": "Sequential execution"
            }
        ]

        result = await handle_list_dependencies(
            {"object_id": "test-sprint-2", "include_satisfied": False},
            mock_adapter
        )

        assert result["isError"] is False
        text = result["content"][0]["text"]
        assert "1 found" in text
        assert "test-sprint-1" in text
        assert "⏳" in text  # Unsatisfied icon
        mock_adapter.list_dependencies.assert_called_once_with("test-sprint-2", False)

    async def test_list_dependencies_include_satisfied(self, mock_adapter):
        """Test listing all dependencies including satisfied."""
        mock_adapter.list_dependencies.return_value = [
            {
                "dependency_id": "test-sprint-1",
                "dependency_type": "sprint",
                "current_status": "completed",
                "required_status": "completed",
                "is_satisfied": True,
                "reason": None
            },
            {
                "dependency_id": "test-track-1",
                "dependency_type": "track",
                "current_status": "in_progress",
                "required_status": "completed",
                "is_satisfied": False,
                "reason": "Foundation track"
            }
        ]

        result = await handle_list_dependencies(
            {"object_id": "test-sprint-3", "include_satisfied": True},
            mock_adapter
        )

        assert result["isError"] is False
        text = result["content"][0]["text"]
        assert "2 found" in text
        assert "✅" in text  # Satisfied icon
        assert "⏳" in text  # Unsatisfied icon
        mock_adapter.list_dependencies.assert_called_once_with("test-sprint-3", True)

    async def test_list_dependencies_none_found(self, mock_adapter):
        """Test listing dependencies when none exist."""
        mock_adapter.list_dependencies.return_value = []

        result = await handle_list_dependencies(
            {"object_id": "test-sprint-1"},
            mock_adapter
        )

        assert result["isError"] is False
        assert "no dependencies found" in result["content"][0]["text"].lower()


@pytest.mark.asyncio
class TestRoadmapStatus:
    """Test vibey_roadmap_status tool."""

    async def test_roadmap_status_success(self, mock_adapter):
        """Test successful roadmap status query."""
        mock_adapter.get_roadmap_status.return_value = {
            "id": "test-roadmap",
            "name": "Test Roadmap",
            "version": "1.0.0",
            "status": "in_progress",
            "blocked": False,
            "progress": {
                "tracks_total": 11,
                "tracks_completed": 4,
                "sprints_total": 37,
                "sprints_completed": 14,
                "tasks_total": 166,
                "tasks_completed": 108,
                "completion_percent": 65
            },
            "active_sprints": [
                {
                    "id": "test-sprint-1",
                    "name": "Test Sprint 1",
                    "status": "in_progress",
                    "completion_percent": 75
                },
                {
                    "id": "test-sprint-2",
                    "name": "Test Sprint 2",
                    "status": "completion_gate_check",
                    "completion_percent": 100
                }
            ],
            "blockers_count": 2
        }

        result = await handle_roadmap_status({}, mock_adapter)

        assert result["isError"] is False
        text = result["content"][0]["text"]
        assert "Test Roadmap" in text
        assert "1.0.0" in text
        assert "65%" in text
        assert "4/11" in text
        assert "14/37" in text
        assert "108/166" in text
        assert "test-sprint-1" in text
        assert "2 blocker" in text
        mock_adapter.get_roadmap_status.assert_called_once()

    async def test_roadmap_status_no_active_sprints(self, mock_adapter):
        """Test roadmap status with no active sprints."""
        mock_adapter.get_roadmap_status.return_value = {
            "id": "test-roadmap",
            "name": "Test Roadmap",
            "version": "1.0.0",
            "status": "completed",
            "blocked": False,
            "progress": {
                "tracks_total": 5,
                "tracks_completed": 5,
                "sprints_total": 20,
                "sprints_completed": 20,
                "tasks_total": 100,
                "tasks_completed": 100,
                "completion_percent": 100
            },
            "active_sprints": [],
            "blockers_count": 0
        }

        result = await handle_roadmap_status({}, mock_adapter)

        assert result["isError"] is False
        text = result["content"][0]["text"]
        assert "100%" in text
        assert "5/5" in text
        # Should handle empty active sprints gracefully


@pytest.mark.asyncio
class TestQueryToolsErrorHandling:
    """Test error handling in query tools."""

    async def test_query_track_unexpected_error(self, mock_adapter):
        """Test handling of unexpected errors in track query."""
        mock_adapter.query_track.side_effect = Exception("Database error")

        result = await handle_query_track(
            {"track_id": "test-track"},
            mock_adapter
        )

        assert result["isError"] is True
        assert "unexpected error" in result["content"][0]["text"].lower()

    async def test_list_blockers_error(self, mock_adapter):
        """Test error handling in list blockers."""
        mock_adapter.list_blockers.side_effect = Exception("Query failed")

        result = await handle_list_blockers({}, mock_adapter)

        assert result["isError"] is True

    async def test_roadmap_status_error(self, mock_adapter):
        """Test error handling in roadmap status."""
        mock_adapter.get_roadmap_status.side_effect = Exception("Roadmap not found")

        result = await handle_roadmap_status({}, mock_adapter)

        assert result["isError"] is True
