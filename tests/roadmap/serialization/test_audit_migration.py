"""
Tests for audit fields migration to ThresholdTarget criteria and markdown reports.

Tests the migration of:
- integrity_score → ThresholdTarget criterion
- audit_results → FileExistsTarget + markdown report
- audit_completed → completed_at timestamp
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from vibey.roadmap.serialization.audit_migration import (
    migrate_integrity_score,
    migrate_audit_results,
    migrate_audit_completed,
    render_audit_report,
    migrate_audit_fields,
    migrate_roadmap_audit_fields,
    format_audit_migration_report,
    AuditMigrationResult,
)


class TestMigrateIntegrityScore:
    """Tests for integrity_score migration to ThresholdTarget."""

    def test_creates_threshold_criterion(self):
        """Test that a ThresholdTarget criterion is created."""
        legacy_data = {'integrity_score': 92}

        criterion = migrate_integrity_score(legacy_data, 'test-entity')

        assert criterion is not None
        assert criterion['id'] == 'test-entity-integrity'
        assert criterion['target']['type'] == 'threshold'
        assert criterion['target']['metric_name'] == 'integrity_score'
        assert criterion['target']['threshold'] == 90
        assert criterion['target']['current_value'] == 92.0

    def test_score_above_threshold_is_met(self):
        """Test that score >= 90 sets met=True."""
        legacy_data = {'integrity_score': 95}

        criterion = migrate_integrity_score(legacy_data, 'test')

        assert criterion['met'] is True

    def test_score_below_threshold_is_not_met(self):
        """Test that score < 90 sets met=False."""
        legacy_data = {'integrity_score': 85}

        criterion = migrate_integrity_score(legacy_data, 'test')

        assert criterion['met'] is False

    def test_score_at_threshold_is_met(self):
        """Test that score == 90 sets met=True (gte comparison)."""
        legacy_data = {'integrity_score': 90}

        criterion = migrate_integrity_score(legacy_data, 'test')

        assert criterion['met'] is True

    def test_returns_none_if_no_score(self):
        """Test that None is returned if no integrity_score."""
        legacy_data = {}

        criterion = migrate_integrity_score(legacy_data, 'test')

        assert criterion is None

    def test_returns_none_for_null_score(self):
        """Test that None is returned if integrity_score is null."""
        legacy_data = {'integrity_score': None}

        criterion = migrate_integrity_score(legacy_data, 'test')

        assert criterion is None

    def test_handles_string_score(self):
        """Test that string scores are converted to float."""
        legacy_data = {'integrity_score': '88'}

        criterion = migrate_integrity_score(legacy_data, 'test')

        assert criterion is not None
        assert criterion['target']['current_value'] == 88.0

    def test_handles_invalid_score(self):
        """Test that invalid scores return None."""
        legacy_data = {'integrity_score': 'invalid'}

        criterion = migrate_integrity_score(legacy_data, 'test')

        assert criterion is None


class TestMigrateAuditResults:
    """Tests for audit_results migration to markdown + FileExistsTarget."""

    def test_creates_file_exists_criterion(self, tmp_path):
        """Test that a FileExistsTarget criterion is created."""
        legacy_data = {'audit_results': {'score': 95, 'summary': 'All good'}}

        criterion, path = migrate_audit_results(legacy_data, 'test-entity', tmp_path)

        assert criterion is not None
        assert criterion['id'] == 'test-entity-audit-report'
        assert criterion['target']['type'] == 'file_exists'
        assert 'test-entity-audit.md' in criterion['target']['paths'][0]

    def test_creates_audit_report_file(self, tmp_path):
        """Test that the audit report markdown file is created."""
        legacy_data = {
            'audit_results': {
                'score': 92,
                'summary': 'Audit completed successfully',
                'findings': ['Finding 1', 'Finding 2'],
            }
        }

        criterion, path = migrate_audit_results(legacy_data, 'my-task', tmp_path)

        assert path is not None
        report_file = Path(path)
        assert report_file.exists()
        content = report_file.read_text()
        assert 'Audit Report: my-task' in content
        assert '92' in content
        assert 'Finding 1' in content

    def test_creates_directory_structure(self, tmp_path):
        """Test that context/audits directory is created."""
        legacy_data = {'audit_results': 'Some results'}

        migrate_audit_results(legacy_data, 'test', tmp_path)

        assert (tmp_path / 'context' / 'audits').exists()

    def test_returns_none_if_no_results(self, tmp_path):
        """Test that None is returned if no audit_results."""
        legacy_data = {}

        criterion, path = migrate_audit_results(legacy_data, 'test', tmp_path)

        assert criterion is None
        assert path is None

    def test_dry_run_no_file_created(self, tmp_path):
        """Test that dry run doesn't create files."""
        legacy_data = {'audit_results': 'Results'}

        criterion, path = migrate_audit_results(legacy_data, 'test', tmp_path, dry_run=True)

        assert criterion is not None
        assert path is not None
        assert not Path(path).exists()


class TestRenderAuditReport:
    """Tests for audit report markdown rendering."""

    def test_renders_dict_results(self):
        """Test rendering of dict audit results."""
        results = {
            'score': 88,
            'summary': 'Partial pass',
            'findings': ['Issue found'],
            'issues': ['Critical bug'],
            'recommendations': ['Fix it'],
        }

        content = render_audit_report('test-entity', results)

        assert 'test-entity' in content
        assert '88' in content
        assert 'Partial pass' in content
        assert 'Issue found' in content
        assert 'Critical bug' in content
        assert 'Fix it' in content

    def test_renders_list_results(self):
        """Test rendering of list audit results."""
        results = ['Finding 1', 'Finding 2', 'Finding 3']

        content = render_audit_report('test', results)

        assert 'Finding 1' in content
        assert 'Finding 2' in content
        assert 'Finding 3' in content

    def test_renders_string_results(self):
        """Test rendering of string audit results."""
        results = 'Simple audit result string'

        content = render_audit_report('test', results)

        assert 'Simple audit result string' in content

    def test_renders_empty_results(self):
        """Test rendering of empty/None results."""
        content = render_audit_report('test', None)

        assert 'Audit Report: test' in content
        assert 'Audit completed.' in content


class TestMigrateAuditCompleted:
    """Tests for audit_completed timestamp migration."""

    def test_returns_datetime_object(self):
        """Test that datetime is returned as-is."""
        dt = datetime(2024, 6, 15, 10, 30, tzinfo=timezone.utc)
        legacy_data = {'audit_completed': dt}

        result = migrate_audit_completed(legacy_data)

        assert result == dt

    def test_parses_iso_string(self):
        """Test parsing of ISO format string."""
        legacy_data = {'audit_completed': '2024-06-15T10:30:00+00:00'}

        result = migrate_audit_completed(legacy_data)

        assert result is not None
        assert result.year == 2024
        assert result.month == 6
        assert result.day == 15

    def test_parses_date_only_string(self):
        """Test parsing of date-only string."""
        legacy_data = {'audit_completed': '2024-06-15'}

        result = migrate_audit_completed(legacy_data)

        assert result is not None
        assert result.year == 2024
        assert result.month == 6

    def test_returns_none_if_no_timestamp(self):
        """Test that None is returned if no audit_completed."""
        legacy_data = {}

        result = migrate_audit_completed(legacy_data)

        assert result is None

    def test_returns_none_for_invalid_string(self):
        """Test that None is returned for invalid timestamp."""
        legacy_data = {'audit_completed': 'not-a-date'}

        result = migrate_audit_completed(legacy_data)

        assert result is None


class TestMigrateAuditFields:
    """Tests for combined audit field migration."""

    def test_migrates_all_fields(self, tmp_path):
        """Test that all audit fields are migrated."""
        legacy_data = {
            'integrity_score': 95,
            'audit_results': {'score': 95, 'summary': 'All good'},
        }

        criteria, report_path = migrate_audit_fields(
            legacy_data, 'test-entity', tmp_path
        )

        assert len(criteria) == 2
        assert any(c['id'] == 'test-entity-integrity' for c in criteria)
        assert any(c['id'] == 'test-entity-audit-report' for c in criteria)
        assert report_path is not None

    def test_migrates_only_existing_fields(self, tmp_path):
        """Test that only existing fields are migrated."""
        legacy_data = {'integrity_score': 90}

        criteria, report_path = migrate_audit_fields(
            legacy_data, 'test', tmp_path
        )

        assert len(criteria) == 1
        assert criteria[0]['id'] == 'test-integrity'
        assert report_path is None

    def test_returns_empty_if_no_fields(self, tmp_path):
        """Test that empty list is returned if no audit fields."""
        legacy_data = {'id': 'test', 'status': 'completed'}

        criteria, report_path = migrate_audit_fields(
            legacy_data, 'test', tmp_path
        )

        assert criteria == []
        assert report_path is None


class TestAuditMigrationResult:
    """Tests for AuditMigrationResult class."""

    def test_initial_state(self):
        """Test initial state of result."""
        result = AuditMigrationResult()

        assert result.total_criteria == 0
        assert result.total_reports == 0
        assert result.total_timestamps == 0
        assert result.total_errors == 0

    def test_add_criterion(self):
        """Test adding criteria."""
        result = AuditMigrationResult()
        result.add_criterion({'id': 'test', 'target': {}})

        assert result.total_criteria == 1

    def test_add_report(self):
        """Test adding reports."""
        result = AuditMigrationResult()
        result.add_report('/path/to/report.md')

        assert result.total_reports == 1

    def test_add_error(self):
        """Test adding errors."""
        result = AuditMigrationResult()
        result.add_error('entity-1', 'Parse error')

        assert result.total_errors == 1
        assert result.errors[0] == ('entity-1', 'Parse error')


class TestMigrateRoadmapAuditFields:
    """Tests for batch roadmap audit migration."""

    def test_migrates_task_with_audit_fields(self, tmp_path):
        """Test migration of task with audit fields."""
        # Create task directory structure
        task_dir = tmp_path / 'track' / 'sprint' / 'task-001'
        task_dir.mkdir(parents=True)

        # Create task.yaml with audit fields
        task_yaml = task_dir / 'task.yaml'
        task_yaml.write_text("""
task:
  id: task-001
  title: Test Task
  integrity_score: 92
  audit_results:
    score: 92
    summary: Task audited
""")

        result = migrate_roadmap_audit_fields(tmp_path)

        assert result.total_criteria >= 1
        assert result.total_errors == 0

    def test_skips_tasks_without_audit_fields(self, tmp_path):
        """Test that tasks without audit fields are skipped."""
        task_dir = tmp_path / 'track' / 'sprint' / 'task-002'
        task_dir.mkdir(parents=True)

        task_yaml = task_dir / 'task.yaml'
        task_yaml.write_text("""
task:
  id: task-002
  title: Regular Task
  status: completed
""")

        result = migrate_roadmap_audit_fields(tmp_path)

        assert result.total_criteria == 0

    def test_handles_parse_errors(self, tmp_path):
        """Test that parse errors are captured."""
        task_dir = tmp_path / 'track' / 'sprint' / 'task-bad'
        task_dir.mkdir(parents=True)

        bad_yaml = task_dir / 'task.yaml'
        bad_yaml.write_text('invalid: yaml: content:')

        result = migrate_roadmap_audit_fields(tmp_path)

        assert result.total_errors >= 1


class TestFormatAuditMigrationReport:
    """Tests for audit migration report formatting."""

    def test_shows_summary(self):
        """Test that summary is shown."""
        result = AuditMigrationResult()
        result.add_criterion({'id': 'test', 'target': {}})

        report = format_audit_migration_report(result)

        assert 'Audit Migration Summary' in report
        assert 'Criteria added:      1' in report

    def test_shows_criteria_in_verbose(self):
        """Test that criteria are listed in verbose mode."""
        result = AuditMigrationResult()
        result.add_criterion({'id': 'test-integrity', 'description': 'Score check'})

        report = format_audit_migration_report(result, verbose=True)

        assert 'Criteria Added:' in report
        assert 'test-integrity' in report

    def test_shows_errors(self):
        """Test that errors are always shown."""
        result = AuditMigrationResult()
        result.add_error('bad-task', 'Parse error')

        report = format_audit_migration_report(result)

        assert 'Errors:' in report
        assert 'Parse error' in report
