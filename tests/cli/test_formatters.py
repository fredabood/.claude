"""
Tests for vibey.cli.formatters module.

Tests the CLI output formatting functions that convert data
to human-readable display formats.
"""

import pytest

from vibey.cli.formatters import (
    format_roadmap_summary,
    format_track_details,
    format_sprint_details,
    format_task_details,
    format_error,
    format_success,
    _get_status_icon,
    _render_progress_bar,
)


class TestStatusIcons:
    """Test status icon helper function."""

    def test_not_started_icon(self):
        """Test not_started status icon."""
        assert _get_status_icon('not_started') == '⚪'

    def test_in_progress_icon(self):
        """Test in_progress status icon."""
        assert _get_status_icon('in_progress') == '🔵'

    def test_completed_icon(self):
        """Test completed status icon."""
        assert _get_status_icon('completed') == '✅'

    def test_blocked_icon(self):
        """Test blocked status icon."""
        assert _get_status_icon('blocked') == '🔴'

    def test_paused_icon(self):
        """Test paused status icon."""
        assert _get_status_icon('paused') == '⏸️'

    def test_unknown_status_icon(self):
        """Test unknown status returns question mark."""
        assert _get_status_icon('unknown') == '❓'
        assert _get_status_icon('invalid') == '❓'
        assert _get_status_icon('') == '❓'


class TestProgressBar:
    """Test progress bar rendering."""

    def test_zero_percent(self):
        """Test 0% progress bar."""
        bar = _render_progress_bar(0)
        assert '[' in bar and ']' in bar
        assert '0%' in bar
        assert '░' * 30 in bar

    def test_fifty_percent(self):
        """Test 50% progress bar."""
        bar = _render_progress_bar(50)
        assert '50%' in bar
        assert '█' * 15 in bar

    def test_hundred_percent(self):
        """Test 100% progress bar."""
        bar = _render_progress_bar(100)
        assert '100%' in bar
        assert '█' * 30 in bar

    def test_custom_width(self):
        """Test custom progress bar width."""
        bar = _render_progress_bar(50, width=20)
        # Should have 10 filled + 10 empty = 20 total
        assert '█' * 10 in bar
        assert '░' * 10 in bar

    def test_fractional_percentage(self):
        """Test fractional percentage rounds correctly."""
        bar = _render_progress_bar(33.33)
        assert '33%' in bar


class TestFormatError:
    """Test error message formatting."""

    def test_simple_error(self):
        """Test simple error formatting."""
        result = format_error("Something went wrong")
        assert "❌" in result
        assert "Error" in result
        assert "Something went wrong" in result

    def test_empty_error(self):
        """Test empty error message."""
        result = format_error("")
        assert "❌" in result
        assert "Error" in result


class TestFormatSuccess:
    """Test success message formatting."""

    def test_simple_success(self):
        """Test simple success formatting."""
        result = format_success("Task completed")
        assert "✅" in result
        assert "Task completed" in result

    def test_empty_success(self):
        """Test empty success message."""
        result = format_success("")
        assert "✅" in result


class TestFormatRoadmapSummary:
    """Test roadmap summary formatting."""

    def test_error_response(self):
        """Test error in response is formatted."""
        data = {"error": "Roadmap not found"}
        result = format_roadmap_summary(data)
        assert "❌" in result
        assert "Roadmap not found" in result

    def test_empty_roadmap(self):
        """Test empty roadmap with no tracks."""
        data = {
            "name": "Test Roadmap",
            "version": "1.0.0",
            "tracks": []
        }
        result = format_roadmap_summary(data)
        assert "Test Roadmap" in result
        assert "1.0.0" in result
        assert "No tracks found" in result

    def test_roadmap_with_tracks(self):
        """Test roadmap with multiple tracks."""
        data = {
            "name": "My Roadmap",
            "version": "2.0.0",
            "tracks": [
                {
                    "id": "backend",
                    "name": "Backend Track",
                    "status": "in_progress",
                    "progress": {
                        "tasks_completed": 5,
                        "tasks_total": 10
                    }
                },
                {
                    "id": "frontend",
                    "name": "Frontend Track",
                    "status": "completed",
                    "progress": {
                        "tasks_completed": 10,
                        "tasks_total": 10
                    }
                }
            ]
        }
        result = format_roadmap_summary(data)
        assert "My Roadmap" in result
        assert "backend" in result
        assert "frontend" in result
        assert "50%" in result  # 5/10 = 50%
        assert "100%" in result  # 10/10 = 100%

    def test_missing_fields_use_defaults(self):
        """Test missing fields use default values."""
        data = {}
        result = format_roadmap_summary(data)
        assert "Unknown" in result
        assert "No tracks found" in result


class TestFormatTrackDetails:
    """Test track details formatting."""

    def test_error_response(self):
        """Test error in response is formatted."""
        data = {"error": "Track not found"}
        result = format_track_details(data)
        assert "❌" in result
        assert "Track not found" in result

    def test_track_with_sprints(self):
        """Test track with sprints."""
        data = {
            "id": "backend",
            "name": "Backend Track",
            "status": "in_progress",
            "description": "Backend development work",
            "sprints": [
                {
                    "id": "backend-1",
                    "name": "Sprint 1",
                    "status": "completed",
                    "tasks": [1, 2, 3]
                },
                {
                    "id": "backend-2",
                    "name": "Sprint 2",
                    "status": "in_progress",
                    "tasks": [4, 5]
                }
            ]
        }
        result = format_track_details(data)
        assert "Backend Track" in result
        assert "backend" in result
        assert "in_progress" in result
        assert "Backend development work" in result
        assert "Sprint 1" in result
        assert "Sprint 2" in result
        assert "Sprints: 2" in result

    def test_track_without_sprints(self):
        """Test track with no sprints."""
        data = {
            "id": "empty-track",
            "name": "Empty Track",
            "status": "not_started",
            "sprints": []
        }
        result = format_track_details(data)
        assert "Empty Track" in result
        assert "No sprints found" in result


class TestFormatSprintDetails:
    """Test sprint details formatting."""

    def test_error_response(self):
        """Test error in response is formatted."""
        data = {"error": "Sprint not found"}
        result = format_sprint_details(data)
        assert "❌" in result
        assert "Sprint not found" in result

    def test_sprint_with_tasks_dict(self):
        """Test sprint with categorized tasks dict."""
        data = {
            "id": "backend-1",
            "name": "Sprint 1",
            "status": "in_progress",
            "description": "First sprint",
            "tasks": {
                "development": [
                    {"id": "task-001", "title": "Dev Task 1", "status": "completed"},
                    {"id": "task-002", "title": "Dev Task 2", "status": "in_progress"}
                ],
                "completion_gates": [
                    {"id": "gate-001", "title": "Code Review", "status": "not_started"}
                ],
                "production_gates": []
            }
        }
        result = format_sprint_details(data)
        assert "Sprint 1" in result
        assert "backend-1" in result
        assert "Development Tasks: 2" in result
        assert "Dev Task 1" in result
        assert "Completion Gates: 1" in result
        assert "Code Review" in result
        assert "Production Gates: 0" in result

    def test_sprint_with_tasks_list(self):
        """Test sprint with tasks as list (old format)."""
        data = {
            "id": "backend-1",
            "name": "Sprint 1",
            "status": "in_progress",
            "tasks": [
                {"id": "task-001", "title": "Task 1", "status": "completed"},
                {"id": "task-002", "title": "Task 2", "status": "in_progress", "assigned_to": "agent-1"}
            ]
        }
        result = format_sprint_details(data)
        assert "Sprint 1" in result
        assert "Task 1" in result
        assert "Task 2" in result
        assert "agent-1" in result

    def test_sprint_no_tasks(self):
        """Test sprint with no tasks."""
        data = {
            "id": "empty-sprint",
            "name": "Empty Sprint",
            "status": "not_started",
            "tasks": {}
        }
        result = format_sprint_details(data)
        assert "Empty Sprint" in result
        assert "No tasks found" in result


class TestFormatTaskDetails:
    """Test task details formatting."""

    def test_error_response(self):
        """Test error in response is formatted."""
        data = {"error": "Task not found"}
        result = format_task_details(data)
        assert "❌" in result
        assert "Task not found" in result

    def test_task_basic_info(self):
        """Test task with basic info."""
        data = {
            "id": "task-001",
            "title": "Implement feature",
            "status": "in_progress",
            "description": "Add new feature to API"
        }
        result = format_task_details(data)
        assert "Implement feature" in result
        assert "task-001" in result
        assert "in_progress" in result
        assert "Add new feature to API" in result

    def test_task_with_assignment(self):
        """Test task with assignment."""
        data = {
            "id": "task-001",
            "title": "Test Task",
            "status": "in_progress",
            "assigned_to": "dev-agent"
        }
        result = format_task_details(data)
        assert "Assigned to: dev-agent" in result

    def test_task_with_files(self):
        """Test task with files to modify."""
        data = {
            "id": "task-001",
            "title": "Test Task",
            "status": "not_started",
            "files_to_modify": [
                "src/api.py",
                "tests/test_api.py"
            ]
        }
        result = format_task_details(data)
        assert "Files to modify" in result
        assert "src/api.py" in result
        assert "tests/test_api.py" in result

    def test_task_with_dependencies(self):
        """Test task with dependencies."""
        data = {
            "id": "task-002",
            "title": "Dependent Task",
            "status": "blocked",
            "dependencies": ["task-001", "task-000"]
        }
        result = format_task_details(data)
        assert "Dependencies" in result
        assert "task-001" in result
        assert "task-000" in result

    def test_task_missing_fields(self):
        """Test task with missing fields uses defaults."""
        data = {}
        result = format_task_details(data)
        assert "Unknown" in result
        assert "unknown" in result  # status default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
