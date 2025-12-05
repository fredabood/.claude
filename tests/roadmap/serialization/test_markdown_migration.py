"""
Tests for markdown migration from YAML fields.

Tests the migration of documentation-like fields from YAML to markdown:
- version_strategy → VERSIONING_POLICY.md
- version_history → CHANGELOG.md
- metadata.notes → NOTES.md
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from vibey.roadmap.serialization.markdown_migration import (
    migrate_version_strategy,
    migrate_version_history,
    migrate_metadata_notes,
    merge_metadata_description,
    migrate_roadmap_docs,
    format_migration_report,
    MigrationResult,
)


class TestMigrateVersionStrategy:
    """Tests for version_strategy migration to VERSIONING_POLICY.md."""

    def test_creates_versioning_policy_file(self, tmp_path):
        """Test that VERSIONING_POLICY.md is created."""
        legacy_data = {
            'version': '1.2.3',
            'version_strategy': {
                'major_on': 'roadmap_milestone',
                'minor_on': 'track_completion',
                'patch_on': 'sprint_production_ready',
            }
        }

        migrated, path = migrate_version_strategy(legacy_data, tmp_path)

        assert migrated is True
        assert path is not None
        assert Path(path).exists()
        assert Path(path).name == 'VERSIONING_POLICY.md'

    def test_file_contains_version_strategy_content(self, tmp_path):
        """Test that the file contains version strategy details."""
        legacy_data = {
            'version': '2.0.0',
            'version_strategy': {
                'major_on': 'roadmap_milestone',
                'minor_on': 'track_completion',
                'patch_on': 'sprint_production_ready',
            }
        }

        migrate_version_strategy(legacy_data, tmp_path)
        content = (tmp_path / 'VERSIONING_POLICY.md').read_text()

        assert 'Versioning Policy' in content
        assert '2.0.0' in content
        assert 'Roadmap milestone completion' in content
        assert 'Track completion' in content
        assert 'Sprint marked production ready' in content

    def test_skips_if_no_version_strategy(self, tmp_path):
        """Test that migration is skipped if no version_strategy."""
        legacy_data = {'version': '1.0.0'}

        migrated, path = migrate_version_strategy(legacy_data, tmp_path)

        assert migrated is False
        assert path is None

    def test_skips_if_file_already_exists(self, tmp_path):
        """Test that existing file is not overwritten."""
        existing_file = tmp_path / 'VERSIONING_POLICY.md'
        existing_file.write_text('# Existing Policy')

        legacy_data = {
            'version_strategy': {'major_on': 'roadmap_milestone'}
        }

        migrated, path = migrate_version_strategy(legacy_data, tmp_path)

        assert migrated is False
        assert path is None
        assert existing_file.read_text() == '# Existing Policy'

    def test_dry_run_does_not_create_file(self, tmp_path):
        """Test that dry run mode doesn't create files."""
        legacy_data = {
            'version_strategy': {'major_on': 'roadmap_milestone'}
        }

        migrated, path = migrate_version_strategy(legacy_data, tmp_path, dry_run=True)

        assert migrated is True
        assert path is not None
        assert not Path(path).exists()


class TestMigrateVersionHistory:
    """Tests for version_history migration to CHANGELOG.md."""

    def test_creates_changelog_file(self, tmp_path):
        """Test that CHANGELOG.md is created."""
        legacy_data = {
            'version_history': [
                {
                    'version': '1.0.0',
                    'date': '2024-01-15',
                    'changes': ['Initial release'],
                    'summary': 'First public version',
                }
            ]
        }

        migrated, path = migrate_version_history(legacy_data, tmp_path)

        assert migrated is True
        assert path is not None
        assert Path(path).exists()
        assert Path(path).name == 'CHANGELOG.md'

    def test_file_contains_changelog_entries(self, tmp_path):
        """Test that the file contains changelog entries."""
        legacy_data = {
            'version_history': [
                {
                    'version': '2.0.0',
                    'date': '2024-06-01',
                    'changes': ['Major refactor', 'New features'],
                    'summary': 'Version 2 release',
                }
            ]
        }

        migrate_version_history(legacy_data, tmp_path)
        content = (tmp_path / 'CHANGELOG.md').read_text()

        assert 'Changelog' in content
        assert '[2.0.0]' in content
        assert '2024-06-01' in content
        assert 'Major refactor' in content
        assert 'New features' in content
        assert 'Version 2 release' in content

    def test_skips_if_no_version_history(self, tmp_path):
        """Test that migration is skipped if no version_history."""
        legacy_data = {'version': '1.0.0'}

        migrated, path = migrate_version_history(legacy_data, tmp_path)

        assert migrated is False
        assert path is None

    def test_skips_empty_version_history(self, tmp_path):
        """Test that empty version_history is skipped."""
        legacy_data = {'version_history': []}

        migrated, path = migrate_version_history(legacy_data, tmp_path)

        assert migrated is False
        assert path is None

    def test_skips_if_file_already_exists(self, tmp_path):
        """Test that existing file is not overwritten."""
        existing_file = tmp_path / 'CHANGELOG.md'
        existing_file.write_text('# Existing Changelog')

        legacy_data = {
            'version_history': [{'version': '1.0.0'}]
        }

        migrated, path = migrate_version_history(legacy_data, tmp_path)

        assert migrated is False
        assert path is None
        assert existing_file.read_text() == '# Existing Changelog'


class TestMigrateMetadataNotes:
    """Tests for metadata.notes migration to NOTES.md."""

    def test_creates_notes_file(self, tmp_path):
        """Test that NOTES.md is created."""
        legacy_data = {
            'metadata': {
                'notes': 'These are implementation notes.'
            }
        }

        migrated, path = migrate_metadata_notes(legacy_data, tmp_path)

        assert migrated is True
        assert path is not None
        assert Path(path).exists()
        assert Path(path).name == 'NOTES.md'

    def test_file_contains_notes_content(self, tmp_path):
        """Test that the file contains notes content."""
        legacy_data = {
            'metadata': {
                'notes': 'Important implementation detail:\n- Point 1\n- Point 2'
            }
        }

        migrate_metadata_notes(legacy_data, tmp_path)
        content = (tmp_path / 'NOTES.md').read_text()

        assert 'Implementation Notes' in content
        assert 'Important implementation detail' in content
        assert 'Point 1' in content
        assert 'Point 2' in content

    def test_skips_if_no_metadata(self, tmp_path):
        """Test that migration is skipped if no metadata."""
        legacy_data = {'id': 'test'}

        migrated, path = migrate_metadata_notes(legacy_data, tmp_path)

        assert migrated is False
        assert path is None

    def test_skips_if_no_notes(self, tmp_path):
        """Test that migration is skipped if metadata has no notes."""
        legacy_data = {
            'metadata': {'created_by': 'user'}
        }

        migrated, path = migrate_metadata_notes(legacy_data, tmp_path)

        assert migrated is False
        assert path is None

    def test_skips_if_file_already_exists(self, tmp_path):
        """Test that existing file is not overwritten."""
        existing_file = tmp_path / 'NOTES.md'
        existing_file.write_text('# Existing Notes')

        legacy_data = {
            'metadata': {'notes': 'New notes'}
        }

        migrated, path = migrate_metadata_notes(legacy_data, tmp_path)

        assert migrated is False
        assert path is None
        assert existing_file.read_text() == '# Existing Notes'


class TestMergeMetadataDescription:
    """Tests for merging metadata.purpose and metadata.description."""

    def test_returns_description_if_present(self):
        """Test that description takes priority."""
        legacy_data = {
            'metadata': {
                'purpose': 'The purpose',
                'description': 'The description',
            }
        }

        result = merge_metadata_description(legacy_data)

        assert result == 'The description'

    def test_returns_purpose_if_no_description(self):
        """Test that purpose is used as fallback."""
        legacy_data = {
            'metadata': {
                'purpose': 'The purpose',
            }
        }

        result = merge_metadata_description(legacy_data)

        assert result == 'The purpose'

    def test_returns_none_if_neither(self):
        """Test that None is returned if neither present."""
        legacy_data = {
            'metadata': {}
        }

        result = merge_metadata_description(legacy_data)

        assert result is None

    def test_returns_none_if_no_metadata(self):
        """Test that None is returned if no metadata."""
        legacy_data = {}

        result = merge_metadata_description(legacy_data)

        assert result is None


class TestMigrationResult:
    """Tests for MigrationResult class."""

    def test_initial_state(self):
        """Test initial state of MigrationResult."""
        result = MigrationResult()

        assert result.total_migrated == 0
        assert result.total_skipped == 0
        assert result.total_errors == 0

    def test_add_migrated(self):
        """Test adding migrated files."""
        result = MigrationResult()
        result.add_migrated('/path/to/file1.md')
        result.add_migrated('/path/to/file2.md')

        assert result.total_migrated == 2
        assert '/path/to/file1.md' in result.migrated_files

    def test_add_skipped(self):
        """Test adding skipped files."""
        result = MigrationResult()
        result.add_skipped('/path/to/existing.md')

        assert result.total_skipped == 1

    def test_add_error(self):
        """Test adding errors."""
        result = MigrationResult()
        result.add_error('/path/to/bad.yaml', 'Parse error')

        assert result.total_errors == 1
        assert result.errors[0] == ('/path/to/bad.yaml', 'Parse error')


class TestMigrateRoadmapDocs:
    """Tests for batch migration of roadmap docs."""

    def test_migrates_version_strategy(self, tmp_path):
        """Test that version_strategy is migrated from roadmap.yaml."""
        # Create roadmap directory structure
        roadmap_dir = tmp_path / '.vibey' / 'roadmap'
        roadmap_dir.mkdir(parents=True)

        # Create roadmap.yaml with version_strategy
        roadmap_yaml = roadmap_dir / 'roadmap.yaml'
        roadmap_yaml.write_text("""
roadmap:
  id: test-roadmap
  version: 1.0.0
  version_strategy:
    major_on: roadmap_milestone
    minor_on: track_completion
    patch_on: sprint_production_ready
""")

        result = migrate_roadmap_docs(roadmap_dir, tmp_path)

        assert result.total_migrated >= 1
        assert (roadmap_dir / 'VERSIONING_POLICY.md').exists()

    def test_migrates_track_notes(self, tmp_path):
        """Test that track metadata.notes is migrated."""
        # Create track directory
        roadmap_dir = tmp_path / '.vibey' / 'roadmap'
        track_dir = roadmap_dir / 'my-track'
        track_dir.mkdir(parents=True)

        # Create track.yaml with metadata.notes
        track_yaml = track_dir / 'track.yaml'
        track_yaml.write_text("""
track:
  id: my-track
  name: My Track
  metadata:
    notes: |
      Important implementation notes here.
      Multiple lines of content.
""")

        result = migrate_roadmap_docs(roadmap_dir, tmp_path)

        assert result.total_migrated >= 1
        assert (track_dir / 'NOTES.md').exists()
        assert 'Important implementation notes' in (track_dir / 'NOTES.md').read_text()

    def test_migrates_task_notes(self, tmp_path):
        """Test that task metadata.notes is migrated."""
        # Create task directory
        roadmap_dir = tmp_path / '.vibey' / 'roadmap'
        task_dir = roadmap_dir / 'track' / 'sprint' / 'task-001'
        task_dir.mkdir(parents=True)

        # Create task.yaml with metadata.notes
        task_yaml = task_dir / 'task.yaml'
        task_yaml.write_text("""
task:
  id: task-001
  title: Test Task
  metadata:
    notes: Task implementation notes
""")

        result = migrate_roadmap_docs(roadmap_dir, tmp_path)

        assert result.total_migrated >= 1
        assert (task_dir / 'NOTES.md').exists()

    def test_dry_run_no_files_created(self, tmp_path):
        """Test that dry run doesn't create any files."""
        # Create roadmap structure
        roadmap_dir = tmp_path / '.vibey' / 'roadmap'
        roadmap_dir.mkdir(parents=True)

        roadmap_yaml = roadmap_dir / 'roadmap.yaml'
        roadmap_yaml.write_text("""
roadmap:
  id: test
  version_strategy:
    major_on: roadmap_milestone
""")

        result = migrate_roadmap_docs(roadmap_dir, tmp_path, dry_run=True)

        assert result.total_migrated >= 1
        assert not (roadmap_dir / 'VERSIONING_POLICY.md').exists()

    def test_handles_parse_errors(self, tmp_path):
        """Test that parse errors are captured."""
        roadmap_dir = tmp_path / '.vibey' / 'roadmap'
        track_dir = roadmap_dir / 'bad-track'
        track_dir.mkdir(parents=True)

        # Create invalid YAML
        bad_yaml = track_dir / 'track.yaml'
        bad_yaml.write_text('invalid: yaml: content:')

        result = migrate_roadmap_docs(roadmap_dir, tmp_path)

        assert result.total_errors >= 1


class TestFormatMigrationReport:
    """Tests for migration report formatting."""

    def test_shows_summary(self):
        """Test that summary is shown."""
        result = MigrationResult()
        result.add_migrated('/path/to/file.md')

        report = format_migration_report(result)

        assert 'Migration Summary' in report
        assert 'Files migrated: 1' in report

    def test_shows_files_in_verbose(self):
        """Test that files are listed in verbose mode."""
        result = MigrationResult()
        result.add_migrated('/path/to/NOTES.md')

        report = format_migration_report(result, verbose=True)

        assert 'Migrated Files:' in report
        assert '/path/to/NOTES.md' in report

    def test_shows_errors(self):
        """Test that errors are always shown."""
        result = MigrationResult()
        result.add_error('/path/to/bad.yaml', 'Parse error')

        report = format_migration_report(result)

        assert 'Errors:' in report
        assert 'Parse error' in report
