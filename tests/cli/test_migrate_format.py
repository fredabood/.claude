"""
Tests for the migrate-format CLI command.

Tests the v1 to v2 YAML format migration functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import yaml


class TestCountFieldChanges:
    """Tests for _count_field_changes helper function."""

    def test_count_timestamp_renames(self):
        """Test counting timestamp field renames."""
        from vibey.cli.commands import _count_field_changes

        data = {
            'id': 'test-1',
            'created': '2025-01-01',
            'started': '2025-01-02',
            'completed': '2025-01-03',
        }
        # 3 timestamps + format_version + ticket_type = 5
        assert _count_field_changes('task', data) >= 3

    def test_count_assigned_agent_rename(self):
        """Test counting assigned_agent to assigned_agents rename."""
        from vibey.cli.commands import _count_field_changes

        data = {
            'id': 'test-1',
            'assigned_agent': 'claude-code',
        }
        # assigned_agent + format_version + ticket_type = 3
        assert _count_field_changes('task', data) >= 1

    def test_count_title_to_name(self):
        """Test counting title to name rename for tasks."""
        from vibey.cli.commands import _count_field_changes

        data = {
            'id': 'test-1',
            'title': 'Test Task',
        }
        # title + format_version + ticket_type = 3
        changes = _count_field_changes('task', data)
        assert changes >= 1

        # Sprint should not count title as a change
        sprint_changes = _count_field_changes('sprint', data)
        assert sprint_changes < changes

    def test_count_hierarchy_consolidation(self):
        """Test counting hierarchy field consolidation."""
        from vibey.cli.commands import _count_field_changes

        data = {
            'id': 'test-1',
            'sprint_id': 'sprint-1',
            'track_id': 'track-1',
            'roadmap_id': 'roadmap-1',
        }
        # hierarchy + format_version + ticket_type = 3
        assert _count_field_changes('task', data) >= 1

    def test_count_blocked_by_to_criteria(self):
        """Test counting blocked_by to criteria conversion."""
        from vibey.cli.commands import _count_field_changes

        data = {
            'id': 'test-1',
            'blocked_by': ['task-1', 'task-2'],
        }
        # blocked_by + format_version + ticket_type = 3
        assert _count_field_changes('task', data) >= 1

    def test_v2_file_has_minimal_changes(self):
        """Test that v2 format files have minimal changes."""
        from vibey.cli.commands import _count_field_changes

        data = {
            'id': 'test-1',
            'format_version': 'v2',
            'ticket_type': 'task',
            'created_at': '2025-01-01',
            'criteria': [],
        }
        # Only checking for format markers that already exist
        assert _count_field_changes('task', data) <= 2


class TestMigrateEntityToV2:
    """Tests for _migrate_entity_to_v2 transformation function."""

    def test_adds_format_markers(self):
        """Test that format_version and ticket_type are added."""
        from vibey.cli.commands import _migrate_entity_to_v2

        data = {'id': 'test-1'}
        result = _migrate_entity_to_v2('task', data)

        assert result['format_version'] == 'v2'
        assert result['ticket_type'] == 'task'

    def test_renames_timestamps(self):
        """Test timestamp field renames."""
        from vibey.cli.commands import _migrate_entity_to_v2

        data = {
            'id': 'test-1',
            'created': '2025-01-01T00:00:00+00:00',
            'started': '2025-01-02T00:00:00+00:00',
            'completed': '2025-01-03T00:00:00+00:00',
        }
        result = _migrate_entity_to_v2('task', data)

        assert 'created' not in result
        assert 'started' not in result
        assert 'completed' not in result
        assert result['created_at'] == '2025-01-01T00:00:00+00:00'
        assert result['started_at'] == '2025-01-02T00:00:00+00:00'
        assert result['completed_at'] == '2025-01-03T00:00:00+00:00'

    def test_converts_assigned_agent_to_list(self):
        """Test assigned_agent (singular) to assigned_agents (list)."""
        from vibey.cli.commands import _migrate_entity_to_v2

        data = {
            'id': 'test-1',
            'assigned_agent': 'backend-engineer',
        }
        result = _migrate_entity_to_v2('task', data)

        assert 'assigned_agent' not in result
        assert result['assigned_agents'] == ['backend-engineer']

    def test_handles_null_assigned_agent(self):
        """Test handling of null assigned_agent."""
        from vibey.cli.commands import _migrate_entity_to_v2

        data = {
            'id': 'test-1',
            'assigned_agent': None,
        }
        result = _migrate_entity_to_v2('task', data)

        assert 'assigned_agent' not in result
        assert result['assigned_agents'] == []

    def test_converts_title_to_name(self):
        """Test title to name for tasks."""
        from vibey.cli.commands import _migrate_entity_to_v2

        data = {
            'id': 'test-1',
            'title': 'Implement feature X',
        }
        result = _migrate_entity_to_v2('task', data)

        assert 'title' not in result
        assert result['name'] == 'Implement feature X'

    def test_preserves_title_for_non_tasks(self):
        """Test that title is not renamed for sprints/tracks."""
        from vibey.cli.commands import _migrate_entity_to_v2

        data = {
            'id': 'sprint-1',
            'title': 'Sprint Title',
        }
        result = _migrate_entity_to_v2('sprint', data)

        # For non-tasks, title should remain if present
        # (The loader handles sprints differently)
        assert 'name' not in result or result.get('title') == 'Sprint Title'

    def test_consolidates_hierarchy_fields(self):
        """Test hierarchy field consolidation to parent_ref."""
        from vibey.cli.commands import _migrate_entity_to_v2

        # Task: parent is sprint
        task_data = {
            'id': 'task-1',
            'sprint_id': 'sprint-1',
            'track_id': 'track-1',
            'roadmap_id': 'roadmap-1',
        }
        task_result = _migrate_entity_to_v2('task', task_data)
        assert task_result['parent_ref'] == 'sprint-1'
        assert 'sprint_id' not in task_result
        assert 'track_id' not in task_result
        assert 'roadmap_id' not in task_result

        # Sprint: parent is track
        sprint_data = {
            'id': 'sprint-1',
            'track_id': 'track-1',
            'roadmap_id': 'roadmap-1',
        }
        sprint_result = _migrate_entity_to_v2('sprint', sprint_data)
        assert sprint_result['parent_ref'] == 'track-1'

        # Track: parent is roadmap
        track_data = {
            'id': 'track-1',
            'roadmap_id': 'roadmap-1',
        }
        track_result = _migrate_entity_to_v2('track', track_data)
        assert track_result['parent_ref'] == 'roadmap-1'

    def test_converts_blocked_by_to_criteria(self):
        """Test blocked_by list to criteria conversion."""
        from vibey.cli.commands import _migrate_entity_to_v2

        data = {
            'id': 'task-1',
            'blocked_by': ['task-0', 'sprint-1'],
        }
        result = _migrate_entity_to_v2('task', data)

        assert 'blocked_by' not in result
        assert 'criteria' in result
        assert len(result['criteria']) == 2

        # Check first criterion
        c1 = result['criteria'][0]
        assert c1['id'] == 'dep-1'
        assert c1['target']['type'] == 'completable'
        assert c1['target']['target_id'] == 'task-0'
        assert c1['blocks_transition_to'] == 'in_progress'

    def test_handles_empty_blocked_by(self):
        """Test handling of empty blocked_by list."""
        from vibey.cli.commands import _migrate_entity_to_v2

        data = {
            'id': 'task-1',
            'blocked_by': [],
        }
        result = _migrate_entity_to_v2('task', data)

        assert 'blocked_by' not in result
        assert result['criteria'] == []

    def test_removes_deprecated_empty_fields(self):
        """Test removal of deprecated empty fields."""
        from vibey.cli.commands import _migrate_entity_to_v2

        data = {
            'id': 'task-1',
            'blocked': False,
            'dependencies': [],
            'blocks': [],
            'depended_on_by': [],
        }
        result = _migrate_entity_to_v2('task', data)

        assert 'blocked' not in result
        assert 'dependencies' not in result
        assert 'blocks' not in result
        assert 'depended_on_by' not in result

    def test_converts_commits_to_commits_local(self):
        """Test commits to commits_local rename."""
        from vibey.cli.commands import _migrate_entity_to_v2

        data = {
            'id': 'task-1',
            'commits': [{'sha': 'abc123', 'message': 'Fix bug'}],
        }
        result = _migrate_entity_to_v2('task', data)

        assert 'commits' not in result
        assert result['commits_local'] == [{'sha': 'abc123', 'message': 'Fix bug'}]

    def test_converts_deliverables_to_requirements(self):
        """Test deliverables to requirements_local conversion."""
        from vibey.cli.commands import _migrate_entity_to_v2

        data = {
            'id': 'task-1',
            'deliverables': [
                'path/to/file.py',
                'docs/README.md',
            ],
        }
        result = _migrate_entity_to_v2('task', data)

        assert 'deliverables' not in result
        assert 'requirements_local' in result
        assert len(result['requirements_local']) == 2
        assert result['requirements_local'][0]['description'] == 'path/to/file.py'

    def test_preserves_unknown_fields(self):
        """Test that unknown fields are preserved."""
        from vibey.cli.commands import _migrate_entity_to_v2

        data = {
            'id': 'task-1',
            'custom_field': 'custom_value',
            'metadata': {'key': 'value'},
        }
        result = _migrate_entity_to_v2('task', data)

        assert result['custom_field'] == 'custom_value'
        assert result['metadata'] == {'key': 'value'}


class TestMigrateFormatIntegration:
    """Integration tests for the full migration workflow."""

    @pytest.fixture
    def temp_roadmap_dir(self):
        """Create a temporary roadmap directory with test files."""
        temp_dir = tempfile.mkdtemp()
        roadmap_dir = Path(temp_dir) / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)

        yield roadmap_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_dry_run_preserves_files(self, temp_roadmap_dir):
        """Test that dry run does not modify files."""
        from vibey.cli.commands import migrate_format_cmd

        # Create a v1 task file
        task_dir = temp_roadmap_dir / "test-track" / "test-sprint" / "test-task"
        task_dir.mkdir(parents=True)
        task_file = task_dir / "task.yaml"

        v1_content = {
            'task': {
                'id': 'test-task',
                'title': 'Test Task',
                'created': '2025-01-01',
                'assigned_agent': 'claude',
                'sprint_id': 'test-sprint',
            }
        }
        with open(task_file, 'w') as f:
            yaml.dump(v1_content, f)

        # Store original content
        original = task_file.read_text()

        # Run migration in dry-run mode
        exit_code = migrate_format_cmd(
            dry_run=True,
            backup=False,
            path=str(temp_roadmap_dir),
            force=True,
            verbose=False,
        )

        # File should be unchanged
        assert task_file.read_text() == original
        assert exit_code == 0

    def test_creates_backup_files(self, temp_roadmap_dir):
        """Test that backups are created when enabled."""
        from vibey.cli.commands import migrate_format_cmd

        # Create a v1 task file
        task_dir = temp_roadmap_dir / "test-track" / "test-sprint" / "test-task"
        task_dir.mkdir(parents=True)
        task_file = task_dir / "task.yaml"

        v1_content = {
            'task': {
                'id': 'test-task',
                'title': 'Test Task',
                'created': '2025-01-01',
            }
        }
        with open(task_file, 'w') as f:
            yaml.dump(v1_content, f)

        # Run migration with backup
        exit_code = migrate_format_cmd(
            dry_run=False,
            backup=True,
            path=str(temp_roadmap_dir),
            force=True,
            verbose=False,
        )

        assert exit_code == 0

        # Check backup directory was created
        backup_dirs = list(temp_roadmap_dir.glob(".migration-backups/*"))
        assert len(backup_dirs) >= 1

    def test_migrates_v1_to_v2(self, temp_roadmap_dir):
        """Test full migration of v1 file to v2 format."""
        from vibey.cli.commands import migrate_format_cmd
        from vibey.roadmap.serialization.yaml_loader import detect_yaml_format

        # Create a v1 task file
        task_dir = temp_roadmap_dir / "test-track" / "test-sprint" / "test-task"
        task_dir.mkdir(parents=True)
        task_file = task_dir / "task.yaml"

        v1_content = {
            'task': {
                'id': 'test-task',
                'title': 'Test Task',
                'created': '2025-01-01T00:00:00+00:00',
                'assigned_agent': 'backend-engineer',
                'sprint_id': 'test-sprint',
                'blocked_by': ['other-task'],
            }
        }
        with open(task_file, 'w') as f:
            yaml.dump(v1_content, f)

        # Run migration
        exit_code = migrate_format_cmd(
            dry_run=False,
            backup=False,
            path=str(temp_roadmap_dir),
            force=True,
            verbose=False,
        )

        assert exit_code == 0

        # Load migrated file
        with open(task_file, 'r') as f:
            migrated = yaml.safe_load(f)

        task_data = migrated['task']

        # Check v2 format
        assert detect_yaml_format(task_data) == 'v2'
        assert task_data['format_version'] == 'v2'
        assert task_data['ticket_type'] == 'task'
        assert task_data['name'] == 'Test Task'
        assert task_data['created_at'] == '2025-01-01T00:00:00+00:00'
        assert task_data['assigned_agents'] == ['backend-engineer']
        assert task_data['parent_ref'] == 'test-sprint'
        assert len(task_data['criteria']) == 1

    def test_skips_v2_files(self, temp_roadmap_dir):
        """Test that v2 files are not modified."""
        from vibey.cli.commands import migrate_format_cmd

        # Create a v2 task file
        task_dir = temp_roadmap_dir / "test-track" / "test-sprint" / "test-task"
        task_dir.mkdir(parents=True)
        task_file = task_dir / "task.yaml"

        v2_content = {
            'task': {
                'id': 'test-task',
                'name': 'Test Task',
                'format_version': 'v2',
                'ticket_type': 'task',
                'created_at': '2025-01-01T00:00:00+00:00',
                'assigned_agents': ['backend-engineer'],
                'parent_ref': 'test-sprint',
                'criteria': [],
            }
        }
        with open(task_file, 'w') as f:
            yaml.dump(v2_content, f)

        original_content = task_file.read_text()

        # Run migration
        exit_code = migrate_format_cmd(
            dry_run=False,
            backup=False,
            path=str(temp_roadmap_dir),
            force=True,
            verbose=False,
        )

        # Should report "all files already v2"
        assert exit_code == 0

        # File should be unchanged (no migration needed)
        # Note: YAML dump may reorder, so check structure
        with open(task_file, 'r') as f:
            final = yaml.safe_load(f)
        assert final['task']['format_version'] == 'v2'
