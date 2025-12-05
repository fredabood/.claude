"""
Tests for directory structure migration.

Tests the migration from hierarchical to flat directory structure:
- Structure detection (hierarchical vs flat)
- Path resolution for both structures
- Migration from old to new structure
"""

import pytest
from pathlib import Path

from vibey.roadmap.serialization.directory_migration import (
    detect_directory_structure,
    PathResolver,
    migrate_to_flat_structure,
    format_migration_result,
    compare_structures,
    estimate_flat_structure,
    MigrationResult,
)


class TestDetectDirectoryStructure:
    """Tests for directory structure detection."""

    def test_detects_hierarchical_structure(self, tmp_path):
        """Test detection of hierarchical structure."""
        # Create hierarchical structure
        track_dir = tmp_path / 'my-track'
        track_dir.mkdir()
        (track_dir / 'track.yaml').write_text('track:\n  id: my-track')

        result = detect_directory_structure(tmp_path)

        assert result == "hierarchical"

    def test_detects_flat_structure(self, tmp_path):
        """Test detection of flat structure."""
        # Create flat structure
        (tmp_path / 'tracks').mkdir()
        (tmp_path / 'sprints').mkdir()
        (tmp_path / 'tasks').mkdir()

        result = detect_directory_structure(tmp_path)

        assert result == "flat"

    def test_returns_unknown_for_empty_dir(self, tmp_path):
        """Test that empty directory returns unknown."""
        result = detect_directory_structure(tmp_path)

        assert result == "unknown"

    def test_returns_unknown_for_roadmap_only(self, tmp_path):
        """Test that directory with only roadmap.yaml returns unknown."""
        (tmp_path / 'roadmap.yaml').write_text('roadmap:\n  id: test')

        result = detect_directory_structure(tmp_path)

        assert result == "unknown"


class TestPathResolver:
    """Tests for PathResolver class."""

    def test_roadmap_file_path(self, tmp_path):
        """Test roadmap file path resolution."""
        resolver = PathResolver(tmp_path)

        path = resolver.roadmap_file()

        assert path == tmp_path / 'roadmap.yaml'

    def test_track_file_hierarchical(self, tmp_path):
        """Test track file path in hierarchical structure."""
        # Create hierarchical structure
        track_dir = tmp_path / 'sqlite-backend'
        track_dir.mkdir()
        (track_dir / 'track.yaml').write_text('track:\n  id: sqlite-backend')

        resolver = PathResolver(tmp_path)

        path = resolver.track_file('sqlite-backend')

        assert path == tmp_path / 'sqlite-backend' / 'track.yaml'

    def test_track_file_flat(self, tmp_path):
        """Test track file path in flat structure."""
        # Create flat structure
        (tmp_path / 'tracks').mkdir()
        (tmp_path / 'sprints').mkdir()
        (tmp_path / 'tasks').mkdir()

        resolver = PathResolver(tmp_path)

        path = resolver.track_file('sqlite-backend')

        assert path == tmp_path / 'tracks' / 'sqlite-backend.yaml'

    def test_sprint_file_hierarchical(self, tmp_path):
        """Test sprint file path in hierarchical structure."""
        # Create hierarchical structure
        track_dir = tmp_path / 'sqlite-backend'
        sprint_dir = track_dir / 'sqlite-backend-8'
        sprint_dir.mkdir(parents=True)
        (track_dir / 'track.yaml').write_text('track:\n  id: sqlite-backend')

        resolver = PathResolver(tmp_path)

        path = resolver.sprint_file('sqlite-backend-8', 'sqlite-backend')

        assert path == tmp_path / 'sqlite-backend' / 'sqlite-backend-8' / 'sprint.yaml'

    def test_sprint_file_flat(self, tmp_path):
        """Test sprint file path in flat structure."""
        # Create flat structure
        (tmp_path / 'tracks').mkdir()
        (tmp_path / 'sprints').mkdir()
        (tmp_path / 'tasks').mkdir()

        resolver = PathResolver(tmp_path)

        path = resolver.sprint_file('sqlite-backend-8')

        assert path == tmp_path / 'sprints' / 'sqlite-backend-8.yaml'

    def test_task_file_hierarchical(self, tmp_path):
        """Test task file path in hierarchical structure."""
        # Create hierarchical structure
        task_dir = tmp_path / 'sqlite-backend' / 'sqlite-backend-8' / 'sqlite-backend-8-task-001'
        task_dir.mkdir(parents=True)
        (tmp_path / 'sqlite-backend' / 'track.yaml').write_text('track:\n  id: sqlite-backend')

        resolver = PathResolver(tmp_path)

        path = resolver.task_file('sqlite-backend-8-task-001', 'sqlite-backend-8', 'sqlite-backend')

        assert path == tmp_path / 'sqlite-backend' / 'sqlite-backend-8' / 'sqlite-backend-8-task-001' / 'task.yaml'

    def test_task_file_flat(self, tmp_path):
        """Test task file path in flat structure."""
        # Create flat structure
        (tmp_path / 'tracks').mkdir()
        (tmp_path / 'sprints').mkdir()
        (tmp_path / 'tasks').mkdir()

        resolver = PathResolver(tmp_path)

        path = resolver.task_file('sqlite-backend-8-task-001')

        assert path == tmp_path / 'tasks' / 'sqlite-backend-8-task-001.yaml'

    def test_context_dir_hierarchical(self, tmp_path):
        """Test context directory path in hierarchical structure."""
        # Create hierarchical structure
        track_dir = tmp_path / 'sqlite-backend'
        track_dir.mkdir()
        (track_dir / 'track.yaml').write_text('track:\n  id: sqlite-backend')

        resolver = PathResolver(tmp_path)

        path = resolver.context_dir('track', 'sqlite-backend')

        assert path == tmp_path / 'sqlite-backend' / 'context'

    def test_context_dir_flat(self, tmp_path):
        """Test context directory path in flat structure."""
        # Create flat structure
        (tmp_path / 'tracks').mkdir()
        (tmp_path / 'sprints').mkdir()
        (tmp_path / 'tasks').mkdir()

        resolver = PathResolver(tmp_path)

        path = resolver.context_dir('track', 'sqlite-backend')

        assert path == tmp_path / 'context' / 'tracks' / 'sqlite-backend'

    def test_infer_track_from_sprint(self, tmp_path):
        """Test track ID inference from sprint ID."""
        resolver = PathResolver(tmp_path)

        track = resolver._infer_track_from_sprint('sqlite-backend-8')

        assert track == 'sqlite-backend'

    def test_infer_sprint_from_task(self, tmp_path):
        """Test sprint ID inference from task ID."""
        resolver = PathResolver(tmp_path)

        sprint = resolver._infer_sprint_from_task('sqlite-backend-8-task-001')

        assert sprint == 'sqlite-backend-8'

    def test_all_track_files_hierarchical(self, tmp_path):
        """Test listing all track files in hierarchical structure."""
        # Create tracks
        for track_id in ['track-a', 'track-b']:
            track_dir = tmp_path / track_id
            track_dir.mkdir()
            (track_dir / 'track.yaml').write_text(f'track:\n  id: {track_id}')

        resolver = PathResolver(tmp_path)

        files = resolver.all_track_files()

        assert len(files) == 2

    def test_all_track_files_flat(self, tmp_path):
        """Test listing all track files in flat structure."""
        # Create flat structure
        tracks_dir = tmp_path / 'tracks'
        tracks_dir.mkdir()
        (tmp_path / 'sprints').mkdir()
        (tmp_path / 'tasks').mkdir()

        (tracks_dir / 'track-a.yaml').write_text('track:\n  id: track-a')
        (tracks_dir / 'track-b.yaml').write_text('track:\n  id: track-b')

        resolver = PathResolver(tmp_path)

        files = resolver.all_track_files()

        assert len(files) == 2


class TestMigrateToFlatStructure:
    """Tests for migration to flat structure."""

    def test_creates_flat_directories(self, tmp_path):
        """Test that flat directories are created."""
        # Create minimal hierarchical structure
        track_dir = tmp_path / 'my-track'
        track_dir.mkdir()
        (track_dir / 'track.yaml').write_text('track:\n  id: my-track')

        migrate_to_flat_structure(tmp_path)

        assert (tmp_path / 'tracks').is_dir()
        assert (tmp_path / 'sprints').is_dir()
        assert (tmp_path / 'tasks').is_dir()
        assert (tmp_path / 'context' / 'tracks').is_dir()

    def test_migrates_track_files(self, tmp_path):
        """Test that track files are migrated."""
        # Create hierarchical track
        track_dir = tmp_path / 'my-track'
        track_dir.mkdir()
        (track_dir / 'track.yaml').write_text('track:\n  id: my-track\n  name: My Track')

        result = migrate_to_flat_structure(tmp_path)

        assert result.tracks_migrated == 1
        assert (tmp_path / 'tracks' / 'my-track.yaml').exists()

    def test_migrates_sprint_files(self, tmp_path):
        """Test that sprint files are migrated."""
        # Create hierarchical sprint
        sprint_dir = tmp_path / 'track' / 'sprint-1'
        sprint_dir.mkdir(parents=True)
        (tmp_path / 'track' / 'track.yaml').write_text('track:\n  id: track')
        (sprint_dir / 'sprint.yaml').write_text('sprint:\n  id: sprint-1')

        result = migrate_to_flat_structure(tmp_path)

        assert result.sprints_migrated == 1
        assert (tmp_path / 'sprints' / 'sprint-1.yaml').exists()

    def test_migrates_task_files(self, tmp_path):
        """Test that task files are migrated."""
        # Create hierarchical task
        task_dir = tmp_path / 'track' / 'sprint-1' / 'task-001'
        task_dir.mkdir(parents=True)
        (tmp_path / 'track' / 'track.yaml').write_text('track:\n  id: track')
        (task_dir / 'task.yaml').write_text('task:\n  id: task-001')

        result = migrate_to_flat_structure(tmp_path)

        assert result.tasks_migrated == 1
        assert (tmp_path / 'tasks' / 'task-001.yaml').exists()

    def test_migrates_context_files(self, tmp_path):
        """Test that context files are migrated."""
        # Create track with context
        track_dir = tmp_path / 'my-track'
        context_dir = track_dir / 'context'
        context_dir.mkdir(parents=True)
        (track_dir / 'track.yaml').write_text('track:\n  id: my-track')
        (context_dir / 'NOTES.md').write_text('# Notes')

        result = migrate_to_flat_structure(tmp_path)

        assert result.context_files_migrated >= 1
        assert (tmp_path / 'context' / 'tracks' / 'my-track' / 'NOTES.md').exists()

    def test_dry_run_no_changes(self, tmp_path):
        """Test that dry run doesn't create files."""
        # Create hierarchical structure
        track_dir = tmp_path / 'my-track'
        track_dir.mkdir()
        (track_dir / 'track.yaml').write_text('track:\n  id: my-track')

        result = migrate_to_flat_structure(tmp_path, dry_run=True)

        assert result.tracks_migrated == 1
        assert not (tmp_path / 'tracks').exists()

    def test_skips_already_flat(self, tmp_path):
        """Test that flat structure is skipped."""
        # Create flat structure
        (tmp_path / 'tracks').mkdir()
        (tmp_path / 'sprints').mkdir()
        (tmp_path / 'tasks').mkdir()

        result = migrate_to_flat_structure(tmp_path)

        assert result.total_migrated == 0


class TestMigrationResult:
    """Tests for MigrationResult class."""

    def test_initial_state(self):
        """Test initial state of result."""
        result = MigrationResult()

        assert result.tracks_migrated == 0
        assert result.sprints_migrated == 0
        assert result.tasks_migrated == 0
        assert result.total_migrated == 0
        assert not result.has_errors

    def test_total_migrated(self):
        """Test total_migrated calculation."""
        result = MigrationResult()
        result.tracks_migrated = 5
        result.sprints_migrated = 10
        result.tasks_migrated = 50

        assert result.total_migrated == 65

    def test_has_errors(self):
        """Test has_errors property."""
        result = MigrationResult()
        result.errors.append(("entity", "error"))

        assert result.has_errors


class TestFormatMigrationResult:
    """Tests for migration result formatting."""

    def test_shows_summary(self):
        """Test that summary is shown."""
        result = MigrationResult()
        result.tracks_migrated = 5
        result.tasks_migrated = 50

        report = format_migration_result(result)

        assert 'Directory Migration Summary' in report
        assert 'Tracks migrated:  5' in report
        assert 'Tasks migrated:   50' in report

    def test_shows_errors(self):
        """Test that errors are shown."""
        result = MigrationResult()
        result.errors.append(("track:bad", "Parse error"))

        report = format_migration_result(result)

        assert 'Errors:' in report
        assert 'Parse error' in report


class TestCompareStructures:
    """Tests for structure comparison."""

    def test_returns_metrics(self, tmp_path):
        """Test that metrics are returned."""
        # Create minimal structure
        track_dir = tmp_path / 'track'
        track_dir.mkdir()
        (track_dir / 'track.yaml').write_text('track:\n  id: track')

        metrics = compare_structures(tmp_path)

        assert 'structure' in metrics
        assert 'directory_count' in metrics
        assert 'max_depth' in metrics
        assert 'yaml_file_count' in metrics

    def test_detects_structure_type(self, tmp_path):
        """Test that structure type is detected."""
        # Create hierarchical structure
        track_dir = tmp_path / 'track'
        track_dir.mkdir()
        (track_dir / 'track.yaml').write_text('track:\n  id: track')

        metrics = compare_structures(tmp_path)

        assert metrics['structure'] == 'hierarchical'


class TestEstimateFlatStructure:
    """Tests for flat structure estimation."""

    def test_estimates_directories(self, tmp_path):
        """Test directory count estimation."""
        # Create hierarchical structure
        track_dir = tmp_path / 'track'
        sprint_dir = track_dir / 'sprint-1'
        task_dir = sprint_dir / 'task-001'
        task_dir.mkdir(parents=True)

        (track_dir / 'track.yaml').write_text('track:\n  id: track')
        (sprint_dir / 'sprint.yaml').write_text('sprint:\n  id: sprint-1')
        (task_dir / 'task.yaml').write_text('task:\n  id: task-001')

        estimate = estimate_flat_structure(tmp_path)

        assert estimate['structure'] == 'flat'
        assert estimate['max_depth'] == 4
        assert estimate['track_count'] == 1
        assert estimate['sprint_count'] == 1
        assert estimate['task_count'] == 1
