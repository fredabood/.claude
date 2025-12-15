"""
Tests for vibey.operations.validate.doc_organization module.

Tests documentation organization validation in roadmap directories.
"""

import pytest
from pathlib import Path

from vibey.operations.validate.doc_organization import (
    ValidationReport,
    DocOrganizationValidator,
    ALLOWED_TRACK_FILES,
    ALLOWED_SPRINT_FILES,
    ALLOWED_TASK_FILES,
    ALLOWED_ROOT_FILES,
    SYSTEM_FILES,
    IGNORED_DIRS,
)


class TestValidationReport:
    """Test ValidationReport dataclass."""

    def test_empty_report(self):
        """Test empty report is valid."""
        report = ValidationReport()
        assert report.is_valid
        assert len(report.issues) == 0
        assert len(report.warnings) == 0

    def test_add_issue(self):
        """Test adding an issue."""
        report = ValidationReport()
        report.add_issue("path/to/file", "Issue description")
        assert not report.is_valid
        assert len(report.issues) == 1
        assert report.issues[0] == ("path/to/file", "Issue description")

    def test_add_warning(self):
        """Test adding a warning."""
        report = ValidationReport()
        report.add_warning("path/to/file", "Warning description")
        assert report.is_valid  # Warnings don't invalidate
        assert len(report.warnings) == 1
        assert report.warnings[0] == ("path/to/file", "Warning description")

    def test_multiple_issues(self):
        """Test adding multiple issues."""
        report = ValidationReport()
        report.add_issue("file1", "Issue 1")
        report.add_issue("file2", "Issue 2")
        assert not report.is_valid
        assert len(report.issues) == 2


class TestDocOrganizationValidator:
    """Test DocOrganizationValidator class."""

    @pytest.fixture
    def roadmap_dir(self, tmp_path):
        """Create a basic roadmap directory structure."""
        roadmap = tmp_path / "roadmap"
        roadmap.mkdir()
        return roadmap

    def test_missing_roadmap_dir(self, tmp_path):
        """Test validation when roadmap directory doesn't exist."""
        validator = DocOrganizationValidator(tmp_path / "nonexistent")
        report = validator.validate()
        assert not report.is_valid
        assert "Roadmap directory not found" in report.issues[0][1]

    def test_valid_root_files(self, roadmap_dir):
        """Test valid files at root level."""
        (roadmap_dir / "roadmap.yaml").write_text("test")
        (roadmap_dir / "roadmap.md").write_text("test")

        validator = DocOrganizationValidator(roadmap_dir)
        report = validator.validate()
        assert report.is_valid

    def test_invalid_root_files(self, roadmap_dir):
        """Test invalid files at root level."""
        (roadmap_dir / "random-file.md").write_text("test")

        validator = DocOrganizationValidator(roadmap_dir)
        report = validator.validate()
        assert not report.is_valid
        assert "Unexpected file at root level" in report.issues[0][1]

    def test_system_files_allowed_at_root(self, roadmap_dir):
        """Test system files are allowed at root."""
        for sysfile in SYSTEM_FILES:
            (roadmap_dir / sysfile).write_text("test")

        validator = DocOrganizationValidator(roadmap_dir)
        report = validator.validate()
        assert report.is_valid

    def test_valid_track_structure(self, roadmap_dir):
        """Test valid track structure."""
        track_dir = roadmap_dir / "my-track"
        track_dir.mkdir()
        (track_dir / "track.yaml").write_text("test")
        (track_dir / "track.md").write_text("test")
        (track_dir / "context").mkdir()

        validator = DocOrganizationValidator(roadmap_dir)
        report = validator.validate()
        assert report.is_valid
        assert report.tracks_checked == 1

    def test_invalid_file_in_track(self, roadmap_dir):
        """Test invalid file at track level."""
        track_dir = roadmap_dir / "my-track"
        track_dir.mkdir()
        (track_dir / "track.yaml").write_text("test")
        (track_dir / "analysis.md").write_text("should be in context/")

        validator = DocOrganizationValidator(roadmap_dir)
        report = validator.validate()
        assert not report.is_valid
        assert "should be in my-track/context/" in report.issues[0][1]

    def test_missing_context_dir_warning(self, roadmap_dir):
        """Test warning when context directory is missing."""
        track_dir = roadmap_dir / "my-track"
        track_dir.mkdir()
        (track_dir / "track.yaml").write_text("test")

        validator = DocOrganizationValidator(roadmap_dir)
        report = validator.validate()
        assert report.is_valid  # Still valid, just a warning
        assert len(report.warnings) == 1
        assert "Missing context/ directory" in report.warnings[0][1]

    def test_valid_sprint_structure(self, roadmap_dir):
        """Test valid sprint structure."""
        track_dir = roadmap_dir / "my-track"
        track_dir.mkdir()
        sprint_dir = track_dir / "sprint-1"
        sprint_dir.mkdir()
        (sprint_dir / "sprint.yaml").write_text("test")
        (sprint_dir / "sprint.md").write_text("test")

        validator = DocOrganizationValidator(roadmap_dir)
        report = validator.validate()
        # Has warning for missing context, but no issues from sprint
        issues_from_sprint = [i for i in report.issues if "sprint-1" in i[0]]
        assert len(issues_from_sprint) == 0
        assert report.sprints_checked == 1

    def test_invalid_file_in_sprint(self, roadmap_dir):
        """Test invalid file at sprint level."""
        track_dir = roadmap_dir / "my-track"
        track_dir.mkdir()
        sprint_dir = track_dir / "sprint-1"
        sprint_dir.mkdir()
        (sprint_dir / "sprint.yaml").write_text("test")
        (sprint_dir / "notes.md").write_text("should be in context/")

        validator = DocOrganizationValidator(roadmap_dir)
        report = validator.validate()
        assert not report.is_valid
        assert "should be in sprint-1/context/" in report.issues[0][1]

    def test_valid_task_structure(self, roadmap_dir):
        """Test valid task structure."""
        track_dir = roadmap_dir / "my-track"
        track_dir.mkdir()
        sprint_dir = track_dir / "sprint-1"
        sprint_dir.mkdir()
        task_dir = sprint_dir / "task-001"
        task_dir.mkdir()
        (task_dir / "task.yaml").write_text("test")
        (task_dir / "task.md").write_text("test")

        validator = DocOrganizationValidator(roadmap_dir)
        report = validator.validate()
        # Filter out warnings
        issues_from_task = [i for i in report.issues if "task-001" in i[0]]
        assert len(issues_from_task) == 0

    def test_invalid_file_in_task(self, roadmap_dir):
        """Test invalid file at task level."""
        track_dir = roadmap_dir / "my-track"
        track_dir.mkdir()
        sprint_dir = track_dir / "sprint-1"
        sprint_dir.mkdir()
        task_dir = sprint_dir / "task-001"
        task_dir.mkdir()
        (task_dir / "task.yaml").write_text("test")
        (task_dir / "scratch.txt").write_text("unexpected file")

        validator = DocOrganizationValidator(roadmap_dir)
        report = validator.validate()
        assert not report.is_valid
        assert "Unexpected file in task directory" in report.issues[0][1]

    def test_ignored_directories_skipped(self, roadmap_dir):
        """Test that ignored directories are skipped."""
        for ignored in IGNORED_DIRS:
            ignored_dir = roadmap_dir / ignored
            ignored_dir.mkdir()
            # Put files that would normally be invalid
            (ignored_dir / "random.txt").write_text("test")

        validator = DocOrganizationValidator(roadmap_dir)
        report = validator.validate()
        assert report.is_valid
        assert report.tracks_checked == 0

    def test_context_directory_skipped(self, roadmap_dir):
        """Test that context directory contents are not validated."""
        track_dir = roadmap_dir / "my-track"
        track_dir.mkdir()
        context_dir = track_dir / "context"
        context_dir.mkdir()
        # These files are allowed in context/
        (context_dir / "analysis.md").write_text("test")
        (context_dir / "research.yaml").write_text("test")
        (context_dir / "notes.txt").write_text("test")

        validator = DocOrganizationValidator(roadmap_dir)
        report = validator.validate()
        # Only warning for missing context should remain (there is context/)
        issues_from_context = [i for i in report.issues if "context" in i[0]]
        assert len(issues_from_context) == 0

    def test_nested_track_sprint_task(self, roadmap_dir):
        """Test complete nested structure."""
        track_dir = roadmap_dir / "my-track"
        track_dir.mkdir()
        (track_dir / "track.yaml").write_text("test")
        (track_dir / "context").mkdir()

        sprint_dir = track_dir / "sprint-1"
        sprint_dir.mkdir()
        (sprint_dir / "sprint.yaml").write_text("test")

        task_dir = sprint_dir / "task-001"
        task_dir.mkdir()
        (task_dir / "task.yaml").write_text("test")

        validator = DocOrganizationValidator(roadmap_dir)
        report = validator.validate()
        assert report.is_valid
        assert report.tracks_checked == 1
        assert report.sprints_checked == 1

    def test_system_files_allowed_everywhere(self, roadmap_dir):
        """Test system files are allowed at all levels."""
        track_dir = roadmap_dir / "my-track"
        track_dir.mkdir()
        sprint_dir = track_dir / "sprint-1"
        sprint_dir.mkdir()
        task_dir = sprint_dir / "task-001"
        task_dir.mkdir()

        # Add system files at various levels
        for sysfile in SYSTEM_FILES:
            (track_dir / sysfile).write_text("test")
            (sprint_dir / sysfile).write_text("test")
            (task_dir / sysfile).write_text("test")

        validator = DocOrganizationValidator(roadmap_dir)
        report = validator.validate()
        # Should only have warning for missing context
        assert len(report.issues) == 0

    def test_id_file_allowed(self, roadmap_dir):
        """Test .id files are allowed at all levels."""
        track_dir = roadmap_dir / "my-track"
        track_dir.mkdir()
        (track_dir / ".id").write_text("01KC...")
        (track_dir / "track.yaml").write_text("test")

        validator = DocOrganizationValidator(roadmap_dir)
        report = validator.validate()
        # Only warning for missing context
        track_issues = [i for i in report.issues if ".id" in i[0]]
        assert len(track_issues) == 0


class TestConstants:
    """Test module constants."""

    def test_allowed_track_files(self):
        """Test track allowed files constant."""
        assert "track.yaml" in ALLOWED_TRACK_FILES
        assert "track.md" in ALLOWED_TRACK_FILES
        assert ".id" in ALLOWED_TRACK_FILES

    def test_allowed_sprint_files(self):
        """Test sprint allowed files constant."""
        assert "sprint.yaml" in ALLOWED_SPRINT_FILES
        assert "sprint.md" in ALLOWED_SPRINT_FILES
        assert ".id" in ALLOWED_SPRINT_FILES

    def test_allowed_task_files(self):
        """Test task allowed files constant."""
        assert "task.yaml" in ALLOWED_TASK_FILES
        assert "task.md" in ALLOWED_TASK_FILES
        assert ".id" in ALLOWED_TASK_FILES

    def test_allowed_root_files(self):
        """Test root allowed files constant."""
        assert "roadmap.yaml" in ALLOWED_ROOT_FILES
        assert "roadmap.md" in ALLOWED_ROOT_FILES

    def test_system_files(self):
        """Test system files constant."""
        assert ".id" in SYSTEM_FILES
        assert ".sync-manifest.json" in SYSTEM_FILES
        assert "audit-trail.yaml" in SYSTEM_FILES

    def test_ignored_dirs(self):
        """Test ignored directories constant."""
        assert "archived" in IGNORED_DIRS
        assert "context" in IGNORED_DIRS
        assert "__pycache__" in IGNORED_DIRS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
