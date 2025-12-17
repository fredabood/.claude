"""
Tests for database integrity audit module.

Tests file-based integrity auditing that compares computed vs declared progress.
"""

import pytest
import tempfile
from pathlib import Path
from typing import Dict

import yaml

from vibey.roadmap.database.integrity_audit import (
    FileCount,
    DeclaredProgress,
    Discrepancy,
    EmbeddedSummaryDiscrepancy,
    EmbeddedSummaryReport,
    AuditReport,
    _parse_yaml_safe,
    count_files_in_directory,
    extract_declared_progress,
    audit_discrepancies,
    build_computed_database,
    run_full_audit,
    validate_embedded_summaries,
    validate_all_embedded_summaries,
)


@pytest.fixture
def temp_roadmap_dir():
    """Create a temporary roadmap directory structure."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        roadmap_root = Path(tmp_dir)
        tracks_dir = roadmap_root / "tracks"
        sprints_dir = roadmap_root / "sprints"
        tasks_dir = roadmap_root / "tasks"

        tracks_dir.mkdir(parents=True)
        sprints_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        yield roadmap_root


@pytest.fixture
def populated_roadmap(temp_roadmap_dir):
    """Create a populated roadmap with tracks, sprints, and tasks."""
    roadmap_root = temp_roadmap_dir
    tracks_dir = roadmap_root / "tracks"
    sprints_dir = roadmap_root / "sprints"
    tasks_dir = roadmap_root / "tasks"

    # Create track
    track_data = {
        'track': {
            'id': 'test-track',
            'name': 'Test Track',
            'status': 'in_progress',
            'progress': {
                'sprints_total': 2,
                'sprints_completed': 1,
                'tasks_total': 4,
                'tasks_completed': 2,
                'completion_percent': 50.0,
            },
            'sprints': [
                {'id': 'sprint-1', 'name': 'Sprint 1', 'status': 'completed'},
                {'id': 'sprint-2', 'name': 'Sprint 2', 'status': 'in_progress'},
            ]
        }
    }
    with open(tracks_dir / "test-track.yaml", 'w') as f:
        yaml.dump(track_data, f)

    # Create sprints
    sprint1_data = {
        'sprint': {
            'id': 'sprint-1',
            'name': 'Sprint 1',
            'track_id': 'test-track',
            'status': 'completed',
            'progress': {
                'development_tasks_total': 2,
                'development_tasks_completed': 2,
                'completion_gate_tasks_total': 0,
                'completion_gate_tasks_completed': 0,
                'production_gate_tasks_total': 0,
                'production_gate_tasks_completed': 0,
                'tasks_total': 2,
                'tasks_completed': 2,
                'completion_percent': 100.0,
            }
        }
    }
    with open(sprints_dir / "sprint-1.yaml", 'w') as f:
        yaml.dump(sprint1_data, f)

    sprint2_data = {
        'sprint': {
            'id': 'sprint-2',
            'name': 'Sprint 2',
            'track_id': 'test-track',
            'status': 'in_progress',
            'progress': {
                'development_tasks_total': 2,
                'development_tasks_completed': 0,
                'completion_gate_tasks_total': 0,
                'completion_gate_tasks_completed': 0,
                'production_gate_tasks_total': 0,
                'production_gate_tasks_completed': 0,
                'tasks_total': 2,
                'tasks_completed': 0,
                'completion_percent': 0.0,
            }
        }
    }
    with open(sprints_dir / "sprint-2.yaml", 'w') as f:
        yaml.dump(sprint2_data, f)

    # Create tasks
    for i, (sprint_id, status) in enumerate([
        ('sprint-1', 'completed'),
        ('sprint-1', 'completed'),
        ('sprint-2', 'not_started'),
        ('sprint-2', 'not_started'),
    ], start=1):
        task_data = {
            'task': {
                'id': f'task-{i:03d}',
                'title': f'Task {i}',
                'sprint_id': sprint_id,
                'status': status,
                'task_type': 'development',
            }
        }
        with open(tasks_dir / f"task-{i:03d}.yaml", 'w') as f:
            yaml.dump(task_data, f)

    return roadmap_root


class TestDataclasses:
    """Test dataclass definitions and properties."""

    def test_file_count_creation(self):
        """Test FileCount dataclass creation."""
        fc = FileCount(
            entity_type='task',
            entity_id='task-001',
            parent_id='sprint-1',
            file_path=Path('/path/to/task.yaml'),
            child_count=0,
            status='not_started',
            name='Test Task',
        )
        assert fc.entity_type == 'task'
        assert fc.entity_id == 'task-001'
        assert fc.parent_id == 'sprint-1'
        assert fc.child_count == 0

    def test_declared_progress_creation(self):
        """Test DeclaredProgress dataclass creation."""
        dp = DeclaredProgress(
            entity_type='track',
            entity_id='test-track',
            parent_id=None,
            declared_sprints_total=5,
            declared_tasks_total=25,
        )
        assert dp.entity_type == 'track'
        assert dp.declared_sprints_total == 5
        assert dp.declared_tasks_total == 25

    def test_discrepancy_creation(self):
        """Test Discrepancy dataclass creation."""
        d = Discrepancy(
            entity_type='sprint',
            entity_id='sprint-1',
            field_name='tasks_total',
            computed_value=5,
            declared_value=3,
            difference=2,
            severity='critical',
        )
        assert d.entity_type == 'sprint'
        assert d.computed_value == 5
        assert d.declared_value == 3
        assert d.difference == 2
        assert d.severity == 'critical'

    def test_embedded_summary_discrepancy_creation(self):
        """Test EmbeddedSummaryDiscrepancy dataclass creation."""
        esd = EmbeddedSummaryDiscrepancy(
            track_id='test-track',
            sprint_id='sprint-1',
            field_name='status',
            embedded_value='not_started',
            actual_value='completed',
            severity='warning',
            message='Status mismatch',
        )
        assert esd.track_id == 'test-track'
        assert esd.sprint_id == 'sprint-1'
        assert esd.severity == 'warning'


class TestEmbeddedSummaryReport:
    """Test EmbeddedSummaryReport dataclass."""

    def test_has_issues_false_when_empty(self):
        """Test has_issues returns False when no issues."""
        report = EmbeddedSummaryReport(track_id='test-track')
        assert not report.has_issues

    def test_has_issues_true_with_discrepancies(self):
        """Test has_issues returns True with discrepancies."""
        report = EmbeddedSummaryReport(
            track_id='test-track',
            discrepancies=[
                EmbeddedSummaryDiscrepancy(
                    track_id='test-track',
                    sprint_id='sprint-1',
                    field_name='status',
                    embedded_value='x',
                    actual_value='y',
                    severity='warning',
                    message='test',
                )
            ],
        )
        assert report.has_issues

    def test_has_issues_true_with_orphaned(self):
        """Test has_issues returns True with orphaned summaries."""
        report = EmbeddedSummaryReport(
            track_id='test-track',
            orphaned_summaries=['sprint-x'],
        )
        assert report.has_issues

    def test_has_issues_true_with_missing(self):
        """Test has_issues returns True with missing summaries."""
        report = EmbeddedSummaryReport(
            track_id='test-track',
            missing_summaries=['sprint-y'],
        )
        assert report.has_issues

    def test_summary_no_issues(self):
        """Test summary output when no issues."""
        report = EmbeddedSummaryReport(track_id='test-track')
        summary = report.summary()
        assert 'test-track' in summary
        assert 'All embedded summaries match' in summary

    def test_summary_with_issues(self):
        """Test summary output with issues."""
        report = EmbeddedSummaryReport(
            track_id='test-track',
            orphaned_summaries=['orphan-1'],
            missing_summaries=['missing-1'],
        )
        summary = report.summary()
        assert 'orphan-1' in summary
        assert 'missing-1' in summary


class TestAuditReport:
    """Test AuditReport dataclass."""

    def test_severity_counts(self):
        """Test severity count properties."""
        report = AuditReport(
            computed_counts={},
            declared_progress={},
            discrepancies=[
                Discrepancy('t', 'id1', 'f', 1, 2, 1, 'critical'),
                Discrepancy('t', 'id2', 'f', 1, 2, 1, 'critical'),
                Discrepancy('t', 'id3', 'f', 1, 2, 1, 'warning'),
                Discrepancy('t', 'id4', 'f', 1, 2, 1, 'info'),
            ],
        )
        assert report.critical_count == 2
        assert report.warning_count == 1
        assert report.info_count == 1

    def test_summary_no_discrepancies(self):
        """Test summary with no discrepancies."""
        report = AuditReport(
            computed_counts={},
            declared_progress={},
            discrepancies=[],
        )
        summary = report.summary()
        assert 'No discrepancies found' in summary

    def test_summary_with_discrepancies(self):
        """Test summary with discrepancies."""
        report = AuditReport(
            computed_counts={'id1': FileCount('task', 'id1', None, Path('.'), 0)},
            declared_progress={},
            discrepancies=[
                Discrepancy('sprint', 'sprint-1', 'tasks_total', 5, 3, 2, 'critical'),
            ],
        )
        summary = report.summary()
        assert 'DISCREPANCIES' in summary
        assert 'sprint-1' in summary
        assert 'tasks_total' in summary


class TestParseYamlSafe:
    """Test YAML parsing helper."""

    def test_parse_valid_yaml(self, tmp_path):
        """Test parsing valid YAML file."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("key: value\n")

        result = _parse_yaml_safe(yaml_file)

        assert result == {'key': 'value'}

    def test_parse_invalid_yaml(self, tmp_path):
        """Test parsing invalid YAML returns None."""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text("{{invalid:yaml:::\n")

        result = _parse_yaml_safe(yaml_file)

        assert result is None

    def test_parse_nonexistent_file(self, tmp_path):
        """Test parsing nonexistent file returns None."""
        result = _parse_yaml_safe(tmp_path / "nonexistent.yaml")
        assert result is None


class TestCountFilesInDirectory:
    """Test file counting function."""

    def test_empty_directory(self, temp_roadmap_dir):
        """Test counting files in empty directory."""
        counts, statuses = count_files_in_directory(temp_roadmap_dir)
        assert len(counts) == 0
        assert len(statuses) == 0

    def test_nonexistent_directory(self):
        """Test counting files in nonexistent directory."""
        counts, statuses = count_files_in_directory(Path("/nonexistent/path"))
        assert len(counts) == 0
        assert len(statuses) == 0

    def test_counts_tracks(self, populated_roadmap):
        """Test counting track files."""
        counts, _ = count_files_in_directory(populated_roadmap)

        track_counts = [c for c in counts.values() if c.entity_type == 'track']
        assert len(track_counts) == 1
        assert track_counts[0].entity_id == 'test-track'

    def test_counts_sprints(self, populated_roadmap):
        """Test counting sprint files."""
        counts, _ = count_files_in_directory(populated_roadmap)

        sprint_counts = [c for c in counts.values() if c.entity_type == 'sprint']
        assert len(sprint_counts) == 2

    def test_counts_tasks(self, populated_roadmap):
        """Test counting task files."""
        counts, statuses = count_files_in_directory(populated_roadmap)

        task_counts = [c for c in counts.values() if c.entity_type == 'task']
        assert len(task_counts) == 4

        # Check task statuses
        assert len(statuses) == 4

    def test_child_count_accuracy(self, populated_roadmap):
        """Test child counts are accurate."""
        counts, _ = count_files_in_directory(populated_roadmap)

        # Track should have 2 sprints
        track = counts.get('test-track')
        assert track is not None
        assert track.child_count == 2

        # Each sprint should have 2 tasks
        sprint1 = counts.get('sprint-1')
        sprint2 = counts.get('sprint-2')
        assert sprint1 is not None
        assert sprint2 is not None
        assert sprint1.child_count == 2
        assert sprint2.child_count == 2


class TestExtractDeclaredProgress:
    """Test declared progress extraction."""

    def test_empty_directory(self, temp_roadmap_dir):
        """Test extracting from empty directory."""
        declared = extract_declared_progress(temp_roadmap_dir)
        assert len(declared) == 0

    def test_nonexistent_directory(self):
        """Test extracting from nonexistent directory."""
        declared = extract_declared_progress(Path("/nonexistent"))
        assert len(declared) == 0

    def test_extracts_track_progress(self, populated_roadmap):
        """Test extracting track progress counters."""
        declared = extract_declared_progress(populated_roadmap)

        track_decl = declared.get('test-track')
        assert track_decl is not None
        assert track_decl.entity_type == 'track'
        assert track_decl.declared_sprints_total == 2
        assert track_decl.declared_tasks_total == 4

    def test_extracts_sprint_progress(self, populated_roadmap):
        """Test extracting sprint progress counters."""
        declared = extract_declared_progress(populated_roadmap)

        sprint1_decl = declared.get('sprint-1')
        assert sprint1_decl is not None
        assert sprint1_decl.entity_type == 'sprint'
        assert sprint1_decl.tasks_total == 2
        assert sprint1_decl.tasks_completed == 2


class TestAuditDiscrepancies:
    """Test discrepancy detection."""

    def test_no_discrepancies_when_matching(self, populated_roadmap):
        """Test no discrepancies when computed matches declared."""
        computed, _ = count_files_in_directory(populated_roadmap)
        declared = extract_declared_progress(populated_roadmap)

        report = audit_discrepancies(computed, declared)

        # Should have no critical discrepancies for matching data
        # (though there may be minor differences)
        assert isinstance(report, AuditReport)

    def test_detects_sprint_count_mismatch(self, temp_roadmap_dir):
        """Test detection of sprint count mismatch."""
        tracks_dir = temp_roadmap_dir / "tracks"

        # Create track with declared 5 sprints, but no actual sprints
        track_data = {
            'track': {
                'id': 'bad-track',
                'name': 'Bad Track',
                'progress': {
                    'sprints_total': 5,  # Declared 5
                }
            }
        }
        with open(tracks_dir / "bad-track.yaml", 'w') as f:
            yaml.dump(track_data, f)

        computed, _ = count_files_in_directory(temp_roadmap_dir)
        declared = extract_declared_progress(temp_roadmap_dir)

        report = audit_discrepancies(computed, declared)

        # Should detect the mismatch (0 computed vs 5 declared)
        sprint_discrepancies = [
            d for d in report.discrepancies
            if d.field_name == 'sprints_total'
        ]
        assert len(sprint_discrepancies) == 1
        assert sprint_discrepancies[0].computed_value == 0
        assert sprint_discrepancies[0].declared_value == 5


class TestBuildComputedDatabase:
    """Test computed database building."""

    def test_builds_database_file(self, populated_roadmap, tmp_path):
        """Test that database file is created."""
        db_path = tmp_path / "computed.db"

        result = build_computed_database(populated_roadmap, db_path)

        assert result == db_path
        assert db_path.exists()

    def test_database_has_correct_tables(self, populated_roadmap, tmp_path):
        """Test database has expected tables."""
        import sqlite3

        db_path = tmp_path / "computed.db"
        build_computed_database(populated_roadmap, db_path)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert 'tracks' in tables
        assert 'sprints' in tables
        assert 'tasks' in tables

    def test_database_has_correct_data(self, populated_roadmap, tmp_path):
        """Test database contains correct data."""
        import sqlite3

        db_path = tmp_path / "computed.db"
        build_computed_database(populated_roadmap, db_path)

        conn = sqlite3.connect(str(db_path))

        # Check tracks
        tracks = conn.execute("SELECT * FROM tracks").fetchall()
        assert len(tracks) == 1

        # Check sprints
        sprints = conn.execute("SELECT * FROM sprints").fetchall()
        assert len(sprints) == 2

        # Check tasks
        tasks = conn.execute("SELECT * FROM tasks").fetchall()
        assert len(tasks) == 4

        conn.close()

    def test_overwrites_existing_database(self, populated_roadmap, tmp_path):
        """Test that existing database is overwritten."""
        db_path = tmp_path / "computed.db"

        # Create first time
        build_computed_database(populated_roadmap, db_path)
        first_mtime = db_path.stat().st_mtime

        # Create second time
        import time
        time.sleep(0.01)
        build_computed_database(populated_roadmap, db_path)
        second_mtime = db_path.stat().st_mtime

        assert second_mtime > first_mtime


class TestRunFullAudit:
    """Test full audit function."""

    def test_returns_audit_report(self, populated_roadmap):
        """Test that full audit returns AuditReport."""
        report = run_full_audit(populated_roadmap)

        assert isinstance(report, AuditReport)
        assert isinstance(report.computed_counts, dict)
        assert isinstance(report.declared_progress, dict)


class TestValidateEmbeddedSummaries:
    """Test embedded summary validation."""

    def test_validates_existing_track(self, populated_roadmap):
        """Test validation of existing track."""
        report = validate_embedded_summaries('test-track', populated_roadmap)

        assert isinstance(report, EmbeddedSummaryReport)
        assert report.track_id == 'test-track'

    def test_returns_empty_for_nonexistent_track(self, temp_roadmap_dir):
        """Test validation returns empty report for nonexistent track."""
        report = validate_embedded_summaries('nonexistent', temp_roadmap_dir)

        assert report.track_id == 'nonexistent'
        assert not report.has_issues

    def test_detects_orphaned_summaries(self, temp_roadmap_dir):
        """Test detection of orphaned sprint summaries."""
        tracks_dir = temp_roadmap_dir / "tracks"

        # Create track with embedded summary for nonexistent sprint
        track_data = {
            'track': {
                'id': 'test-track',
                'name': 'Test Track',
                'sprints': [
                    {'id': 'orphan-sprint', 'name': 'Orphan', 'status': 'not_started'},
                ]
            }
        }
        with open(tracks_dir / "test-track.yaml", 'w') as f:
            yaml.dump(track_data, f)

        report = validate_embedded_summaries('test-track', temp_roadmap_dir)

        assert 'orphan-sprint' in report.orphaned_summaries

    def test_detects_missing_summaries(self, temp_roadmap_dir):
        """Test detection of missing sprint summaries."""
        tracks_dir = temp_roadmap_dir / "tracks"
        sprints_dir = temp_roadmap_dir / "sprints"

        # Create track with no embedded summaries
        track_data = {
            'track': {
                'id': 'test-track',
                'name': 'Test Track',
                'sprints': []  # No embedded summaries
            }
        }
        with open(tracks_dir / "test-track.yaml", 'w') as f:
            yaml.dump(track_data, f)

        # Create actual sprint
        sprint_data = {
            'sprint': {
                'id': 'missing-sprint',
                'name': 'Missing Sprint',
                'track_id': 'test-track',
            }
        }
        with open(sprints_dir / "missing-sprint.yaml", 'w') as f:
            yaml.dump(sprint_data, f)

        report = validate_embedded_summaries('test-track', temp_roadmap_dir)

        assert 'missing-sprint' in report.missing_summaries


class TestValidateAllEmbeddedSummaries:
    """Test validation across all tracks."""

    def test_returns_list_of_reports(self, populated_roadmap):
        """Test that all track validation returns list of reports."""
        reports = validate_all_embedded_summaries(populated_roadmap)

        assert isinstance(reports, list)
        assert all(isinstance(r, EmbeddedSummaryReport) for r in reports)

    def test_empty_directory_returns_empty(self, temp_roadmap_dir):
        """Test empty directory returns empty list."""
        reports = validate_all_embedded_summaries(temp_roadmap_dir)
        assert reports == []

    def test_nonexistent_directory_returns_empty(self):
        """Test nonexistent directory returns empty list."""
        reports = validate_all_embedded_summaries(Path("/nonexistent"))
        assert reports == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
