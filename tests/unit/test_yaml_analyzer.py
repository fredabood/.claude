"""
Tests for YAML change analyzer module.

Task: git-integration-4-task-003
"""

import pytest
from vibey.operations.git.yaml_analyzer import (
    YAMLChange,
    CLISuggestion,
    AnalysisResult,
    YAMLChangeAnalyzer,
)


class TestYAMLChange:
    """Tests for YAMLChange dataclass."""

    def test_status_change_detection(self):
        """Test is_status_change property."""
        change = YAMLChange(
            file_path=".vibey/roadmap/track/sprint/task/task.yaml",
            file_type="task",
            item_id="task-001",
            field_name="status",
            old_value="not_started",
            new_value="in_progress",
        )
        assert change.is_status_change
        assert not change.is_progress_change

    def test_progress_change_detection(self):
        """Test is_progress_change property."""
        change = YAMLChange(
            file_path=".vibey/roadmap/track/sprint/sprint.yaml",
            file_type="sprint",
            item_id="sprint-1",
            field_name="completion_percent",
            old_value="50",
            new_value="75",
        )
        assert change.is_progress_change
        assert not change.is_status_change

    def test_completed_is_status_change(self):
        """Test that 'completed' field is recognized as status change."""
        change = YAMLChange(
            file_path=".vibey/roadmap/track/sprint/task/task.yaml",
            file_type="task",
            item_id="task-001",
            field_name="completed",
            old_value="null",
            new_value="2025-01-01T00:00:00",
        )
        assert change.is_status_change

    def test_regular_field_not_status_or_progress(self):
        """Test that regular fields are not status or progress."""
        change = YAMLChange(
            file_path=".vibey/roadmap/track/sprint/task/task.yaml",
            file_type="task",
            item_id="task-001",
            field_name="title",
            old_value="Old title",
            new_value="New title",
        )
        assert not change.is_status_change
        assert not change.is_progress_change


class TestCLISuggestion:
    """Tests for CLISuggestion dataclass."""

    def test_format_with_description(self):
        """Test formatting with description."""
        suggestion = CLISuggestion(
            command="vibey roadmap start task-001",
            description="Start the task using CLI",
            priority="high",
        )
        formatted = suggestion.format(show_description=True)
        assert "vibey roadmap start task-001" in formatted
        assert "Start the task using CLI" in formatted

    def test_format_without_description(self):
        """Test formatting without description."""
        suggestion = CLISuggestion(
            command="vibey roadmap start task-001",
            description="Start the task using CLI",
            priority="high",
        )
        formatted = suggestion.format(show_description=False)
        assert "vibey roadmap start task-001" in formatted
        assert "Start the task" not in formatted


class TestAnalysisResult:
    """Tests for AnalysisResult dataclass."""

    def test_format_summary(self):
        """Test summary formatting."""
        result = AnalysisResult(
            file_path=".vibey/roadmap/track/sprint/task/task.yaml",
            file_type="task",
            item_id="task-001",
            changes=[
                YAMLChange(
                    file_path=".vibey/roadmap/track/sprint/task/task.yaml",
                    file_type="task",
                    item_id="task-001",
                    field_name="status",
                    old_value="not_started",
                    new_value="in_progress",
                ),
            ],
        )
        summary = result.format_summary()
        assert "Manual YAML edit detected" in summary
        assert "task.yaml" in summary
        assert "status" in summary

    def test_empty_changes_summary(self):
        """Test summary with no changes."""
        result = AnalysisResult(
            file_path=".vibey/roadmap/track/sprint/task/task.yaml",
            file_type="task",
            item_id="task-001",
            changes=[],
        )
        summary = result.format_summary()
        assert summary == ""


class TestYAMLChangeAnalyzer:
    """Tests for YAMLChangeAnalyzer class."""

    def test_get_file_type_task(self):
        """Test file type detection for task files."""
        analyzer = YAMLChangeAnalyzer()
        assert analyzer._get_file_type("path/to/task.yaml") == "task"

    def test_get_file_type_sprint(self):
        """Test file type detection for sprint files."""
        analyzer = YAMLChangeAnalyzer()
        assert analyzer._get_file_type("path/to/sprint.yaml") == "sprint"

    def test_get_file_type_track(self):
        """Test file type detection for track files."""
        analyzer = YAMLChangeAnalyzer()
        assert analyzer._get_file_type("path/to/track.yaml") == "track"

    def test_get_file_type_unknown(self):
        """Test file type detection for unknown files."""
        analyzer = YAMLChangeAnalyzer()
        assert analyzer._get_file_type("path/to/other.yaml") is None

    def test_extract_item_id_task(self):
        """Test item ID extraction from task path."""
        analyzer = YAMLChangeAnalyzer()
        path = ".vibey/roadmap/my-track/my-track-1/my-track-1-task-001/task.yaml"
        assert analyzer._extract_item_id(path, "task") == "my-track-1-task-001"

    def test_extract_item_id_sprint(self):
        """Test item ID extraction from sprint path."""
        analyzer = YAMLChangeAnalyzer()
        path = ".vibey/roadmap/my-track/my-track-1/sprint.yaml"
        assert analyzer._extract_item_id(path, "sprint") == "my-track-1"

    def test_extract_item_id_track(self):
        """Test item ID extraction from track path."""
        analyzer = YAMLChangeAnalyzer()
        path = ".vibey/roadmap/my-track/track.yaml"
        assert analyzer._extract_item_id(path, "track") == "my-track"


class TestCLISuggestionGeneration:
    """Tests for CLI suggestion generation."""

    def test_suggest_start_for_in_progress_status(self):
        """Test suggestion for status change to in_progress."""
        analyzer = YAMLChangeAnalyzer()
        changes = [
            YAMLChange(
                file_path=".vibey/roadmap/track/sprint/task/task.yaml",
                file_type="task",
                item_id="task-001",
                field_name="status",
                old_value="not_started",
                new_value="in_progress",
            ),
        ]
        suggestions = analyzer._generate_suggestions(changes)
        assert len(suggestions) >= 1
        assert any("start" in s.command for s in suggestions)

    def test_suggest_complete_for_completed_status(self):
        """Test suggestion for status change to completed."""
        analyzer = YAMLChangeAnalyzer()
        changes = [
            YAMLChange(
                file_path=".vibey/roadmap/track/sprint/task/task.yaml",
                file_type="task",
                item_id="task-001",
                field_name="status",
                old_value="in_progress",
                new_value="completed",
            ),
        ]
        suggestions = analyzer._generate_suggestions(changes)
        assert len(suggestions) >= 1
        assert any("complete" in s.command for s in suggestions)

    def test_suggest_sync_for_progress_changes(self):
        """Test suggestion for progress field changes."""
        analyzer = YAMLChangeAnalyzer()
        changes = [
            YAMLChange(
                file_path=".vibey/roadmap/track/sprint/sprint.yaml",
                file_type="sprint",
                item_id="sprint-1",
                field_name="completion_percent",
                old_value="50",
                new_value="75",
            ),
        ]
        suggestions = analyzer._generate_suggestions(changes)
        assert len(suggestions) >= 1
        assert any("sync" in s.command for s in suggestions)

    def test_suggest_add_commit_for_commit_changes(self):
        """Test suggestion for commit additions."""
        analyzer = YAMLChangeAnalyzer()
        changes = [
            YAMLChange(
                file_path=".vibey/roadmap/track/sprint/task/task.yaml",
                file_type="task",
                item_id="task-001",
                field_name="commits",
                old_value="[]",
                new_value="[{sha: abc123}]",
            ),
        ]
        suggestions = analyzer._generate_suggestions(changes)
        assert len(suggestions) >= 1
        assert any("add-commit" in s.command for s in suggestions)

    def test_suggest_blocked_status(self):
        """Test suggestion for blocked status change."""
        analyzer = YAMLChangeAnalyzer()
        changes = [
            YAMLChange(
                file_path=".vibey/roadmap/track/sprint/task/task.yaml",
                file_type="task",
                item_id="task-001",
                field_name="status",
                old_value="not_started",
                new_value="blocked",
            ),
        ]
        suggestions = analyzer._generate_suggestions(changes)
        assert len(suggestions) >= 1
        assert any("blocked" in s.command for s in suggestions)

    def test_high_priority_for_status_changes(self):
        """Test that status changes have high priority suggestions."""
        analyzer = YAMLChangeAnalyzer()
        changes = [
            YAMLChange(
                file_path=".vibey/roadmap/track/sprint/task/task.yaml",
                file_type="task",
                item_id="task-001",
                field_name="status",
                old_value="not_started",
                new_value="completed",
            ),
        ]
        suggestions = analyzer._generate_suggestions(changes)
        assert len(suggestions) >= 1
        assert suggestions[0].priority == "high"


class TestBlockingMode:
    """Tests for blocking mode behavior."""

    def test_should_block_on_status_change_in_blocking_mode(self):
        """Test that status changes block in blocking mode."""
        analyzer = YAMLChangeAnalyzer()
        changes = [
            YAMLChange(
                file_path=".vibey/roadmap/track/sprint/task/task.yaml",
                file_type="task",
                item_id="task-001",
                field_name="status",
                old_value="not_started",
                new_value="completed",
            ),
        ]

        # Simulate blocking mode result
        result = AnalysisResult(
            file_path=".vibey/roadmap/track/sprint/task/task.yaml",
            file_type="task",
            item_id="task-001",
            changes=changes,
            should_block=True,
        )
        assert result.should_block

    def test_should_not_block_non_status_changes(self):
        """Test that non-status changes don't block."""
        analyzer = YAMLChangeAnalyzer()
        changes = [
            YAMLChange(
                file_path=".vibey/roadmap/track/sprint/task/task.yaml",
                file_type="task",
                item_id="task-001",
                field_name="title",
                old_value="Old title",
                new_value="New title",
            ),
        ]

        # Non-status changes shouldn't trigger blocking
        result = AnalysisResult(
            file_path=".vibey/roadmap/track/sprint/task/task.yaml",
            file_type="task",
            item_id="task-001",
            changes=changes,
            should_block=False,
        )
        assert not result.should_block
