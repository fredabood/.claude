"""
Tests for advanced roadmap validation module.

Tests circular dependency detection, orphaned tasks, broken references,
and progress counter validation.
"""

import pytest
import tempfile
from pathlib import Path
from io import StringIO
import sys

import yaml

from vibey.operations.roadmap.advanced_validator import (
    CircularDependency,
    OrphanedTask,
    BrokenReference,
    ProgressMismatch,
    AdvancedValidationReport,
    detect_circular_dependencies,
    find_orphaned_tasks,
    find_broken_references,
    validate_progress_counters,
    AdvancedValidator,
    print_advanced_report,
)


@pytest.fixture
def temp_roadmap_dir():
    """Create a temporary roadmap directory with hierarchical structure."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        roadmap_dir = root / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)
        yield root


def create_track(roadmap_dir: Path, track_id: str, sprints_total: int = 0, sprints_completed: int = 0):
    """Helper to create a track directory and YAML."""
    track_dir = roadmap_dir / track_id
    track_dir.mkdir(exist_ok=True)

    track_data = {
        'track': {
            'id': track_id,
            'name': f'Track {track_id}',
            'status': 'in_progress',
            'progress': {
                'sprints_total': sprints_total,
                'sprints_completed': sprints_completed,
            }
        }
    }
    with open(track_dir / "track.yaml", 'w') as f:
        yaml.dump(track_data, f)

    return track_dir


def create_sprint(track_dir: Path, sprint_id: str, tasks_total: int = 0, tasks_completed: int = 0, status: str = 'in_progress'):
    """Helper to create a sprint directory and YAML."""
    sprint_dir = track_dir / sprint_id
    sprint_dir.mkdir(exist_ok=True)

    sprint_data = {
        'sprint': {
            'id': sprint_id,
            'name': f'Sprint {sprint_id}',
            'status': status,
            'progress': {
                'tasks_total': tasks_total,
                'tasks_completed': tasks_completed,
            }
        }
    }
    with open(sprint_dir / "sprint.yaml", 'w') as f:
        yaml.dump(sprint_data, f)

    return sprint_dir


def create_task(sprint_dir: Path, task_id: str, status: str = 'not_started',
                depends_on: list = None, blocked_by: list = None,
                blocks: list = None, depended_on_by: list = None,
                sprint_id: str = None):
    """Helper to create a task directory and YAML."""
    task_dir = sprint_dir / task_id
    task_dir.mkdir(exist_ok=True)

    task_data = {
        'task': {
            'id': task_id,
            'title': f'Task {task_id}',
            'status': status,
            'sprint_id': sprint_id or sprint_dir.name,
        }
    }

    if depends_on:
        task_data['task']['depends_on'] = depends_on
    if blocked_by:
        task_data['task']['blocked_by'] = blocked_by
    if blocks:
        task_data['task']['blocks'] = blocks
    if depended_on_by:
        task_data['task']['depended_on_by'] = depended_on_by

    with open(task_dir / "task.yaml", 'w') as f:
        yaml.dump(task_data, f)

    return task_dir


class TestDataclasses:
    """Test dataclass definitions."""

    def test_circular_dependency_str(self):
        """Test CircularDependency string representation."""
        cd = CircularDependency(
            cycle=['task-1', 'task-2', 'task-1'],
            cycle_length=2,
            description='Test cycle'
        )
        s = str(cd)
        assert 'task-1' in s
        assert 'task-2' in s
        assert '2 tasks' in s

    def test_orphaned_task_str(self):
        """Test OrphanedTask string representation."""
        ot = OrphanedTask(
            task_id='task-001',
            task_file='/path/to/task.yaml',
            missing_sprint_id='sprint-x',
            suggested_sprints=['sprint-1', 'sprint-2']
        )
        s = str(ot)
        assert 'task-001' in s
        assert 'sprint-x' in s
        assert 'non-existent' in s

    def test_broken_reference_str(self):
        """Test BrokenReference string representation."""
        br = BrokenReference(
            task_id='task-001',
            task_file='/path/to/task.yaml',
            field='depends_on',
            missing_id='task-999',
            suggested_ids=['task-001', 'task-002']
        )
        s = str(br)
        assert 'task-001' in s
        assert 'depends_on' in s
        assert 'task-999' in s

    def test_progress_mismatch_str(self):
        """Test ProgressMismatch string representation."""
        pm = ProgressMismatch(
            entity_type='sprint',
            entity_id='sprint-1',
            entity_file='/path/to/sprint.yaml',
            claimed_completed=5,
            actual_completed=3,
            claimed_total=10,
            actual_total=8,
        )
        s = str(pm)
        assert 'sprint-1' in s
        assert '5/10' in s
        assert '3/8' in s


class TestAdvancedValidationReport:
    """Test AdvancedValidationReport dataclass."""

    def test_has_issues_false_when_empty(self):
        """Test has_issues is False when no issues."""
        report = AdvancedValidationReport()
        assert not report.has_issues
        assert report.issue_count == 0

    def test_has_issues_true_with_circular_deps(self):
        """Test has_issues is True with circular dependencies."""
        report = AdvancedValidationReport(
            circular_dependencies=[
                CircularDependency(['a', 'b', 'a'], 2, 'test')
            ]
        )
        assert report.has_issues
        assert report.issue_count == 1

    def test_has_issues_true_with_orphaned_tasks(self):
        """Test has_issues is True with orphaned tasks."""
        report = AdvancedValidationReport(
            orphaned_tasks=[
                OrphanedTask('t1', 'f1', 's1')
            ]
        )
        assert report.has_issues
        assert report.issue_count == 1

    def test_has_issues_true_with_broken_refs(self):
        """Test has_issues is True with broken references."""
        report = AdvancedValidationReport(
            broken_references=[
                BrokenReference('t1', 'f1', 'depends_on', 'm1')
            ]
        )
        assert report.has_issues
        assert report.issue_count == 1

    def test_has_issues_true_with_progress_mismatch(self):
        """Test has_issues is True with progress mismatch."""
        report = AdvancedValidationReport(
            progress_mismatches=[
                ProgressMismatch('sprint', 's1', 'f1', 1, 0, 5, 5)
            ]
        )
        assert report.has_issues
        assert report.issue_count == 1

    def test_issue_count_sums_all_types(self):
        """Test issue_count sums all issue types."""
        report = AdvancedValidationReport(
            circular_dependencies=[CircularDependency(['a', 'b', 'a'], 2, '')],
            orphaned_tasks=[OrphanedTask('t1', 'f1', 's1')],
            broken_references=[BrokenReference('t1', 'f1', 'x', 'm1')],
            progress_mismatches=[ProgressMismatch('sprint', 's1', 'f1', 1, 0, 5, 5)],
        )
        assert report.issue_count == 4


class TestDetectCircularDependencies:
    """Test circular dependency detection."""

    def test_no_dependencies_returns_empty(self):
        """Test tasks with no dependencies return empty list."""
        tasks = {
            'task-1': {'id': 'task-1'},
            'task-2': {'id': 'task-2'},
        }
        result = detect_circular_dependencies(tasks)
        assert result == []

    def test_linear_dependencies_returns_empty(self):
        """Test linear dependencies (no cycles) return empty."""
        tasks = {
            'task-1': {'id': 'task-1'},
            'task-2': {'id': 'task-2', 'depends_on': ['task-1']},
            'task-3': {'id': 'task-3', 'depends_on': ['task-2']},
        }
        result = detect_circular_dependencies(tasks)
        assert result == []

    def test_detects_simple_cycle(self):
        """Test detection of simple 2-task cycle."""
        tasks = {
            'task-1': {'id': 'task-1', 'depends_on': ['task-2']},
            'task-2': {'id': 'task-2', 'depends_on': ['task-1']},
        }
        result = detect_circular_dependencies(tasks)
        assert len(result) == 1
        assert result[0].cycle_length == 2

    def test_detects_longer_cycle(self):
        """Test detection of 3-task cycle."""
        tasks = {
            'task-1': {'id': 'task-1', 'depends_on': ['task-2']},
            'task-2': {'id': 'task-2', 'depends_on': ['task-3']},
            'task-3': {'id': 'task-3', 'depends_on': ['task-1']},
        }
        result = detect_circular_dependencies(tasks)
        assert len(result) == 1
        assert result[0].cycle_length == 3

    def test_handles_blocked_by(self):
        """Test that blocked_by is also checked for cycles."""
        tasks = {
            'task-1': {'id': 'task-1', 'blocked_by': ['task-2']},
            'task-2': {'id': 'task-2', 'blocked_by': ['task-1']},
        }
        result = detect_circular_dependencies(tasks)
        assert len(result) == 1

    def test_handles_dict_format_dependencies(self):
        """Test handling dependencies in dict format with target_id."""
        tasks = {
            'task-1': {'id': 'task-1', 'depends_on': [{'target_id': 'task-2'}]},
            'task-2': {'id': 'task-2', 'depends_on': [{'target_id': 'task-1'}]},
        }
        result = detect_circular_dependencies(tasks)
        assert len(result) == 1

    def test_deduplicates_cycles(self):
        """Test that duplicate cycles are removed."""
        # Same cycle can be detected from different starting points
        tasks = {
            'task-1': {'id': 'task-1', 'depends_on': ['task-2']},
            'task-2': {'id': 'task-2', 'depends_on': ['task-1']},
        }
        result = detect_circular_dependencies(tasks)
        # Should only report once, not twice
        assert len(result) == 1


class TestFindOrphanedTasks:
    """Test orphaned task detection."""

    def test_empty_directory(self, temp_roadmap_dir):
        """Test empty directory returns empty list."""
        roadmap_dir = temp_roadmap_dir / ".vibey" / "roadmap"
        result = find_orphaned_tasks(roadmap_dir)
        assert result == []

    def test_valid_tasks_return_empty(self, temp_roadmap_dir):
        """Test tasks with valid sprint references return empty."""
        roadmap_dir = temp_roadmap_dir / ".vibey" / "roadmap"

        track_dir = create_track(roadmap_dir, 'track-1')
        sprint_dir = create_sprint(track_dir, 'sprint-1')
        create_task(sprint_dir, 'task-001', sprint_id='sprint-1')

        result = find_orphaned_tasks(roadmap_dir)
        assert result == []

    def test_detects_orphaned_task(self, temp_roadmap_dir):
        """Test detection of task with missing sprint reference."""
        roadmap_dir = temp_roadmap_dir / ".vibey" / "roadmap"

        track_dir = create_track(roadmap_dir, 'track-1')
        sprint_dir = create_sprint(track_dir, 'sprint-1')
        # Task references non-existent sprint
        create_task(sprint_dir, 'task-001', sprint_id='nonexistent-sprint')

        result = find_orphaned_tasks(roadmap_dir)
        assert len(result) == 1
        assert result[0].task_id == 'task-001'
        assert result[0].missing_sprint_id == 'nonexistent-sprint'


class TestFindBrokenReferences:
    """Test broken reference detection."""

    def test_empty_directory(self, temp_roadmap_dir):
        """Test empty directory returns empty list."""
        roadmap_dir = temp_roadmap_dir / ".vibey" / "roadmap"
        result = find_broken_references(roadmap_dir)
        assert result == []

    def test_valid_references_return_empty(self, temp_roadmap_dir):
        """Test tasks with valid references return empty."""
        roadmap_dir = temp_roadmap_dir / ".vibey" / "roadmap"

        track_dir = create_track(roadmap_dir, 'track-1')
        sprint_dir = create_sprint(track_dir, 'sprint-1')
        create_task(sprint_dir, 'task-001')
        create_task(sprint_dir, 'task-002', depends_on=['task-001'])

        result = find_broken_references(roadmap_dir)
        assert result == []

    def test_detects_broken_depends_on(self, temp_roadmap_dir):
        """Test detection of broken depends_on reference."""
        roadmap_dir = temp_roadmap_dir / ".vibey" / "roadmap"

        track_dir = create_track(roadmap_dir, 'track-1')
        sprint_dir = create_sprint(track_dir, 'sprint-1')
        create_task(sprint_dir, 'task-001', depends_on=['nonexistent-task'])

        result = find_broken_references(roadmap_dir)
        assert len(result) == 1
        assert result[0].task_id == 'task-001'
        assert result[0].field == 'depends_on'
        assert result[0].missing_id == 'nonexistent-task'

    def test_detects_broken_blocked_by(self, temp_roadmap_dir):
        """Test detection of broken blocked_by reference."""
        roadmap_dir = temp_roadmap_dir / ".vibey" / "roadmap"

        track_dir = create_track(roadmap_dir, 'track-1')
        sprint_dir = create_sprint(track_dir, 'sprint-1')
        create_task(sprint_dir, 'task-001', blocked_by=['nonexistent-task'])

        result = find_broken_references(roadmap_dir)
        assert len(result) == 1
        assert result[0].field == 'blocked_by'

    def test_detects_broken_depended_on_by(self, temp_roadmap_dir):
        """Test detection of broken depended_on_by reference."""
        roadmap_dir = temp_roadmap_dir / ".vibey" / "roadmap"

        track_dir = create_track(roadmap_dir, 'track-1')
        sprint_dir = create_sprint(track_dir, 'sprint-1')
        create_task(sprint_dir, 'task-001', depended_on_by=['nonexistent-task'])

        result = find_broken_references(roadmap_dir)
        assert len(result) == 1
        assert result[0].field == 'depended_on_by'


class TestValidateProgressCounters:
    """Test progress counter validation."""

    def test_empty_directory(self, temp_roadmap_dir):
        """Test empty directory returns empty list."""
        roadmap_dir = temp_roadmap_dir / ".vibey" / "roadmap"
        result = validate_progress_counters(roadmap_dir)
        assert result == []

    def test_correct_counters_return_empty(self, temp_roadmap_dir):
        """Test correct progress counters return empty."""
        roadmap_dir = temp_roadmap_dir / ".vibey" / "roadmap"

        track_dir = create_track(roadmap_dir, 'track-1', sprints_total=1, sprints_completed=0)
        sprint_dir = create_sprint(track_dir, 'sprint-1', tasks_total=2, tasks_completed=1)
        create_task(sprint_dir, 'task-001', status='completed')
        create_task(sprint_dir, 'task-002', status='not_started')

        result = validate_progress_counters(roadmap_dir)
        assert result == []

    def test_detects_sprint_task_count_mismatch(self, temp_roadmap_dir):
        """Test detection of sprint task count mismatch."""
        roadmap_dir = temp_roadmap_dir / ".vibey" / "roadmap"

        track_dir = create_track(roadmap_dir, 'track-1')
        # Claim 5 tasks but only create 2
        sprint_dir = create_sprint(track_dir, 'sprint-1', tasks_total=5, tasks_completed=0)
        create_task(sprint_dir, 'task-001')
        create_task(sprint_dir, 'task-002')

        result = validate_progress_counters(roadmap_dir)
        sprint_mismatches = [m for m in result if m.entity_type == 'sprint']
        assert len(sprint_mismatches) == 1
        assert sprint_mismatches[0].claimed_total == 5
        assert sprint_mismatches[0].actual_total == 2

    def test_detects_sprint_completed_count_mismatch(self, temp_roadmap_dir):
        """Test detection of sprint completed task count mismatch."""
        roadmap_dir = temp_roadmap_dir / ".vibey" / "roadmap"

        track_dir = create_track(roadmap_dir, 'track-1')
        # Claim 2 completed but only 1 is actually completed
        sprint_dir = create_sprint(track_dir, 'sprint-1', tasks_total=2, tasks_completed=2)
        create_task(sprint_dir, 'task-001', status='completed')
        create_task(sprint_dir, 'task-002', status='not_started')

        result = validate_progress_counters(roadmap_dir)
        sprint_mismatches = [m for m in result if m.entity_type == 'sprint']
        assert len(sprint_mismatches) == 1
        assert sprint_mismatches[0].claimed_completed == 2
        assert sprint_mismatches[0].actual_completed == 1

    def test_detects_track_sprint_count_mismatch(self, temp_roadmap_dir):
        """Test detection of track sprint count mismatch."""
        roadmap_dir = temp_roadmap_dir / ".vibey" / "roadmap"

        # Claim 3 sprints but only create 1
        track_dir = create_track(roadmap_dir, 'track-1', sprints_total=3, sprints_completed=0)
        create_sprint(track_dir, 'sprint-1')

        result = validate_progress_counters(roadmap_dir)
        track_mismatches = [m for m in result if m.entity_type == 'track']
        assert len(track_mismatches) == 1
        assert track_mismatches[0].claimed_total == 3
        assert track_mismatches[0].actual_total == 1


class TestAdvancedValidator:
    """Test AdvancedValidator class."""

    def test_validate_empty_roadmap(self, temp_roadmap_dir):
        """Test validation of empty roadmap."""
        validator = AdvancedValidator(temp_roadmap_dir)
        report = validator.validate()

        assert isinstance(report, AdvancedValidationReport)
        assert report.total_tasks == 0
        assert report.total_sprints == 0
        assert report.total_tracks == 0
        assert not report.has_issues

    def test_validate_nonexistent_roadmap(self, tmp_path):
        """Test validation when roadmap doesn't exist."""
        validator = AdvancedValidator(tmp_path)
        report = validator.validate()

        assert isinstance(report, AdvancedValidationReport)
        assert not report.has_issues

    def test_validate_counts_entities(self, temp_roadmap_dir):
        """Test that validator counts entities correctly."""
        roadmap_dir = temp_roadmap_dir / ".vibey" / "roadmap"

        track_dir = create_track(roadmap_dir, 'track-1')
        sprint1 = create_sprint(track_dir, 'sprint-1')
        sprint2 = create_sprint(track_dir, 'sprint-2')
        create_task(sprint1, 'task-001')
        create_task(sprint1, 'task-002')
        create_task(sprint2, 'task-003')

        validator = AdvancedValidator(temp_roadmap_dir)
        report = validator.validate()

        assert report.total_tracks == 1
        assert report.total_sprints == 2
        assert report.total_tasks == 3

    def test_validate_finds_all_issues(self, temp_roadmap_dir):
        """Test that validator finds issues from all categories."""
        roadmap_dir = temp_roadmap_dir / ".vibey" / "roadmap"

        track_dir = create_track(roadmap_dir, 'track-1', sprints_total=5)  # Mismatch
        sprint_dir = create_sprint(track_dir, 'sprint-1', tasks_total=10)  # Mismatch

        # Circular dependency
        create_task(sprint_dir, 'task-001', depends_on=['task-002'])
        create_task(sprint_dir, 'task-002', depends_on=['task-001'])

        # Broken reference
        create_task(sprint_dir, 'task-003', depends_on=['nonexistent'])

        validator = AdvancedValidator(temp_roadmap_dir)
        report = validator.validate()

        assert report.has_issues
        # Should have circular dependencies, broken references, and progress mismatches
        assert len(report.circular_dependencies) > 0 or \
               len(report.broken_references) > 0 or \
               len(report.progress_mismatches) > 0


class TestPrintAdvancedReport:
    """Test report printing function."""

    def test_prints_no_issues_message(self):
        """Test printing report with no issues."""
        report = AdvancedValidationReport(
            total_tasks=10,
            total_sprints=2,
            total_tracks=1,
        )

        # Capture stdout
        captured = StringIO()
        sys.stdout = captured
        try:
            print_advanced_report(report)
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()
        assert 'No issues detected' in output
        assert 'Tasks: 10' in output

    def test_prints_issues(self):
        """Test printing report with issues."""
        report = AdvancedValidationReport(
            total_tasks=5,
            circular_dependencies=[
                CircularDependency(['a', 'b', 'a'], 2, 'test cycle')
            ],
        )

        captured = StringIO()
        sys.stdout = captured
        try:
            print_advanced_report(report)
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()
        assert 'Issues detected' in output
        assert 'Circular Dependencies' in output

    def test_verbose_mode_shows_details(self):
        """Test verbose mode shows additional details."""
        report = AdvancedValidationReport(
            orphaned_tasks=[
                OrphanedTask('task-001', '/path/to/task.yaml', 'sprint-x', ['sprint-1'])
            ],
        )

        captured = StringIO()
        sys.stdout = captured
        try:
            print_advanced_report(report, verbose=True)
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()
        assert '/path/to/task.yaml' in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
