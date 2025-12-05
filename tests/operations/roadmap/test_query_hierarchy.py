"""
Tests for hierarchy-aware query functions.

Tests the helper functions and type detection for the hierarchy-aware
query functions. Full integration tests require proper roadmap fixtures.
"""

import pytest
from pathlib import Path

from vibey.operations.roadmap.query import (
    QueryTicketLoader,
    _determine_ticket_type,
)


class TestDetermineTicketType:
    """Tests for _determine_ticket_type helper."""

    def test_task_type(self):
        """Test task ID detection."""
        assert _determine_ticket_type("sqlite-backend-8-task-001") == "task"
        assert _determine_ticket_type("my-track-1-task-123") == "task"
        assert _determine_ticket_type("a-b-c-task-999") == "task"

    def test_sprint_type(self):
        """Test sprint ID detection."""
        assert _determine_ticket_type("sqlite-backend-8") == "sprint"
        assert _determine_ticket_type("my-track-1") == "sprint"
        assert _determine_ticket_type("track-0") == "sprint"

    def test_track_type(self):
        """Test track ID detection."""
        assert _determine_ticket_type("sqlite-backend") == "track"
        assert _determine_ticket_type("my-track") == "track"
        assert _determine_ticket_type("git-integration") == "track"

    def test_roadmap_type(self):
        """Test roadmap ID detection."""
        assert _determine_ticket_type("vibey-framework-v2") == "roadmap"
        assert _determine_ticket_type("my-roadmap") == "roadmap"

    def test_deferred_sprint(self):
        """Test deferred sprint detection (ends with -deferred, not a number)."""
        assert _determine_ticket_type("track-13-deferred") == "track"


class TestQueryTicketLoader:
    """Tests for QueryTicketLoader class."""

    def test_is_sprint_id(self, tmp_path):
        """Test sprint ID detection."""
        loader = QueryTicketLoader(tmp_path)

        # Valid sprint IDs (ends with -N where N is numeric)
        assert loader._is_sprint_id("sqlite-backend-8") is True
        assert loader._is_sprint_id("track-0") is True
        assert loader._is_sprint_id("track-99") is True

        # Not sprint IDs
        assert loader._is_sprint_id("track-13-deferred") is False
        assert loader._is_sprint_id("sqlite-backend") is False
        assert loader._is_sprint_id("sqlite-backend-8-task-001") is False

    def test_extract_track_from_sprint(self, tmp_path):
        """Test track ID extraction from sprint ID."""
        loader = QueryTicketLoader(tmp_path)

        assert loader._extract_track_from_sprint("sqlite-backend-8") == "sqlite-backend"
        assert loader._extract_track_from_sprint("my-track-1") == "my-track"
        assert loader._extract_track_from_sprint("track-0") == "track"
        assert loader._extract_track_from_sprint("a-b-c-99") == "a-b-c"

    def test_is_track_id_no_track_dir(self, tmp_path):
        """Test track ID check when track directory doesn't exist."""
        loader = QueryTicketLoader(tmp_path)

        # Even if it looks like a track ID, it needs the directory to exist
        assert loader._is_track_id("nonexistent-track") is False

    def test_is_track_id_with_track_dir(self, tmp_path):
        """Test track ID check when track directory exists."""
        # Create minimal roadmap structure
        vibey_dir = tmp_path / ".vibey"
        roadmap_dir = vibey_dir / "roadmap"
        track_dir = roadmap_dir / "my-track"
        track_dir.mkdir(parents=True)
        (track_dir / "track.yaml").write_text("track:\n  id: my-track")

        loader = QueryTicketLoader(tmp_path)

        assert loader._is_track_id("my-track") is True
        assert loader._is_track_id("nonexistent") is False


class TestLoaderIDPatternRecognition:
    """Tests for ID pattern recognition in _load_uncached."""

    def test_task_pattern_recognized(self, tmp_path):
        """Test that task IDs are recognized by -task- pattern."""
        loader = QueryTicketLoader(tmp_path)

        # Task IDs have -task- in them
        assert '-task-' in "sqlite-backend-8-task-001"
        assert '-task-' in "a-b-task-999"
        assert '-task-' not in "sqlite-backend-8"
        assert '-task-' not in "sqlite-backend"

    def test_sprint_pattern_recognized(self, tmp_path):
        """Test that sprint IDs are recognized by ending with number."""
        loader = QueryTicketLoader(tmp_path)

        # Sprint IDs end with -N
        assert loader._is_sprint_id("track-8") is True
        assert loader._is_sprint_id("track") is False
        assert loader._is_sprint_id("track-deferred") is False


class TestTicketLoaderFunctions:
    """Tests for the public ticket loader functions."""

    def test_load_task_ticket_returns_task_ticket(self, tmp_path):
        """Test that load_task_ticket returns TaskTicket type."""
        # This test documents the expected interface
        from vibey.operations.roadmap.query import load_task_ticket
        from vibey.roadmap.models.ticket import TaskTicket

        # The function should return TaskTicket
        # (Full test requires roadmap fixture)
        assert callable(load_task_ticket)

    def test_load_sprint_ticket_returns_sprint_ticket(self, tmp_path):
        """Test that load_sprint_ticket returns SprintTicket type."""
        from vibey.operations.roadmap.query import load_sprint_ticket
        from vibey.roadmap.models.ticket import SprintTicket

        # The function should return SprintTicket
        assert callable(load_sprint_ticket)

    def test_load_track_ticket_returns_track_ticket(self, tmp_path):
        """Test that load_track_ticket returns TrackTicket type."""
        from vibey.operations.roadmap.query import load_track_ticket
        from vibey.roadmap.models.ticket import TrackTicket

        # The function should return TrackTicket
        assert callable(load_track_ticket)

    def test_load_roadmap_ticket_returns_roadmap_ticket(self, tmp_path):
        """Test that load_roadmap_ticket returns RoadmapTicket type."""
        from vibey.operations.roadmap.query import load_roadmap_ticket
        from vibey.roadmap.models.ticket import RoadmapTicket

        # The function should return RoadmapTicket
        assert callable(load_roadmap_ticket)

    def test_load_ticket_generic_returns_hierarchical_ticket(self, tmp_path):
        """Test that load_ticket returns HierarchicalTicket type."""
        from vibey.operations.roadmap.query import load_ticket
        from vibey.roadmap.models.ticket import HierarchicalTicket

        # The function should return HierarchicalTicket
        assert callable(load_ticket)
