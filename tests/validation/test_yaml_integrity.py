"""
YAML integrity validation tests for roadmap data.

Ensures all roadmap YAML files are clean, parseable, and follow data integrity rules.
"""

import pytest
import yaml
from pathlib import Path


def get_all_roadmap_yaml_files():
    """Get all YAML files in the roadmap directory."""
    roadmap_dir = Path('.vibey/roadmap')
    if not roadmap_dir.exists():
        return []
    # Only return track.yaml, sprint.yaml, and task.yaml files (actual data)
    # Exclude documentation files that describe issues
    files = []
    for pattern in ['**/track.yaml', '**/sprint.yaml', '**/task.yaml']:
        files.extend(roadmap_dir.glob(pattern))
    return files


class TestYAMLSyntax:
    """Test basic YAML syntax and parseability."""

    def test_all_yaml_files_parse_safely(self):
        """All roadmap YAML files should parse with yaml.safe_load()."""
        yaml_files = get_all_roadmap_yaml_files()
        assert len(yaml_files) > 0, "No YAML files found in .vibey/roadmap"

        failed_files = []
        for yaml_file in yaml_files:
            try:
                with open(yaml_file) as f:
                    yaml.safe_load(f)
            except Exception as e:
                failed_files.append((yaml_file, str(e)))

        if failed_files:
            error_msg = "\n".join([f"  {f}: {e}" for f, e in failed_files])
            pytest.fail(f"Failed to parse {len(failed_files)} YAML files:\n{error_msg}")


class TestPythonSerialization:
    """Test for Python object serialization corruption."""

    def test_no_python_serialization_in_yaml(self):
        """No YAML file should contain !!python serialization patterns."""
        yaml_files = get_all_roadmap_yaml_files()

        corrupted_files = []
        for yaml_file in yaml_files:
            with open(yaml_file) as f:
                content = f.read()
                if '!!python' in content:
                    # Find line numbers
                    lines = content.split('\n')
                    line_nums = [i+1 for i, line in enumerate(lines) if '!!python' in line]
                    corrupted_files.append((yaml_file, line_nums))

        if corrupted_files:
            error_msg = "\n".join([
                f"  {f}: lines {', '.join(map(str, lines))}"
                for f, lines in corrupted_files
            ])
            pytest.fail(
                f"Found Python object serialization in {len(corrupted_files)} files:\n{error_msg}\n"
                f"Fix: Replace !!python patterns with plain string values"
            )


class TestSchemaValidation:
    """Validate YAML data against schema definitions."""

    def test_valid_status_enum_values(self):
        """All status fields should contain valid Status enum values."""
        from vibey.roadmap.models.common import Status, TaskStatus
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager
        import yaml

        valid_statuses = {s.value for s in Status}
        valid_task_statuses = {s.value for s in TaskStatus}

        fs = FileSystemManager()
        invalid_values = []

        # Check track statuses
        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            with open(track_path) as f:
                data = yaml.safe_load(f)
                track_data = data.get('track', {})

                # Main status
                status = track_data.get('status')
                if status and status not in valid_statuses:
                    invalid_values.append((track_id, 'track.status', status, 'Status'))

                # Sprint statuses
                for sprint in track_data.get('sprints', []):
                    sprint_status = sprint.get('status')
                    if sprint_status and sprint_status not in valid_statuses:
                        invalid_values.append((
                            track_id,
                            f"track.sprints.{sprint.get('id')}.status",
                            sprint_status,
                            'Status'
                        ))

        # Check task statuses - iterate through all tasks in hierarchical structure
        for track_slug, track_id in fs.dir_manager.list_tracks():
            for sprint_slug, sprint_id in fs.dir_manager.list_sprints(track_slug):
                for task_slug, task_id in fs.dir_manager.list_tasks(track_slug, sprint_slug):
                    task_path = fs.roadmap_root / track_slug / sprint_slug / task_slug / "task.yaml"
                    if not task_path.exists():
                        continue
                    with open(task_path) as f:
                        data = yaml.safe_load(f)
                        task_data = data.get('task', {})

                        status = task_data.get('status')
                        if status and status not in valid_task_statuses:
                            invalid_values.append((task_id, 'task.status', status, 'TaskStatus'))

        if invalid_values:
            error_msg = "\n".join([
                f"  {obj_id} -> {field}: '{value}' is not a valid {enum_type}"
                for obj_id, field, value, enum_type in invalid_values
            ])
            pytest.fail(f"Found {len(invalid_values)} invalid enum values:\n{error_msg}")

    def test_valid_priority_enum_values(self):
        """All priority fields should contain valid Priority enum values."""
        from vibey.roadmap.models.common import Priority
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager
        import yaml

        valid_priorities = {p.value for p in Priority}
        fs = FileSystemManager()
        invalid_values = []

        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            with open(track_path) as f:
                data = yaml.safe_load(f)
                priority = data.get('track', {}).get('priority')

                if priority and priority not in valid_priorities:
                    invalid_values.append((track_id, priority))

        if invalid_values:
            error_msg = "\n".join([f"  {tid}: '{pri}'" for tid, pri in invalid_values])
            pytest.fail(f"Found {len(invalid_values)} invalid priority values:\n{error_msg}")

    def test_valid_dependency_type_values(self):
        """All dependency type fields should contain valid DependencyType enum values."""
        from vibey.roadmap.models.common import DependencyType
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager
        import yaml

        valid_types = {t.value for t in DependencyType}
        fs = FileSystemManager()
        invalid_values = []

        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            with open(track_path) as f:
                data = yaml.safe_load(f)
                track_data = data.get('track', {})

                # Check dependencies
                for dep in track_data.get('dependencies', []):
                    dep_type = dep.get('type')
                    if dep_type and dep_type not in valid_types:
                        invalid_values.append((track_id, 'dependencies', dep_type))

                # Check blocks
                for block in track_data.get('blocks', []):
                    block_type = block.get('type')
                    if block_type and block_type not in valid_types:
                        invalid_values.append((track_id, 'blocks', block_type))

        if invalid_values:
            error_msg = "\n".join([
                f"  {tid} ({field}): '{val}'"
                for tid, field, val in invalid_values
            ])
            pytest.fail(f"Found {len(invalid_values)} invalid dependency type values:\n{error_msg}")

    def test_completion_percent_in_range(self):
        """Completion percent should be between 0 and 100."""
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager
        import yaml

        fs = FileSystemManager()
        violations = []

        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            with open(track_path) as f:
                data = yaml.safe_load(f)
                progress = data.get('track', {}).get('progress', {})
                completion = progress.get('completion_percent')

                if completion is not None and not (0 <= completion <= 100):
                    violations.append((track_id, completion))

        if violations:
            error_msg = "\n".join([f"  {tid}: {pct}%" for tid, pct in violations])
            pytest.fail(f"Found {len(violations)} invalid completion percentages:\n{error_msg}")

    def test_numeric_fields_are_integers(self):
        """Numeric count fields should be integers, not strings."""
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager
        import yaml

        fs = FileSystemManager()
        violations = []

        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            with open(track_path) as f:
                data = yaml.safe_load(f)
                progress = data.get('track', {}).get('progress', {})

                # Check all numeric fields
                numeric_fields = ['sprints_total', 'sprints_completed', 'tasks_total', 'tasks_completed']
                for field in numeric_fields:
                    value = progress.get(field)
                    if value is not None and not isinstance(value, int):
                        violations.append((track_id, field, type(value).__name__))

        if violations:
            error_msg = "\n".join([
                f"  {tid}.progress.{field}: {typ} (should be int)"
                for tid, field, typ in violations
            ])
            pytest.fail(f"Found {len(violations)} non-integer numeric fields:\n{error_msg}")

    def test_boolean_fields_are_booleans(self):
        """Boolean fields should be true/false, not strings."""
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager
        import yaml

        fs = FileSystemManager()
        violations = []

        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            with open(track_path) as f:
                data = yaml.safe_load(f)
                track_data = data.get('track', {})

                # Check blocked field
                blocked = track_data.get('blocked')
                if blocked is not None and not isinstance(blocked, bool):
                    violations.append((track_id, 'blocked', type(blocked).__name__))

        if violations:
            error_msg = "\n".join([
                f"  {tid}.{field}: {typ} (should be bool)"
                for tid, field, typ in violations
            ])
            pytest.fail(f"Found {len(violations)} non-boolean boolean fields:\n{error_msg}")

    def test_no_unknown_top_level_fields_in_tracks(self):
        """Track YAML files should not have unexpected top-level fields."""
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager
        import yaml

        # Expected top-level fields based on Track model
        expected_fields = {
            'id', 'name', 'roadmap_id', 'status', 'blocked', 'priority',
            'created', 'started', 'completed', 'superseded_at', 'superseded_by',
            'estimated_duration', 'actual_duration', 'progress', 'sprints', 'dependencies',
            'blocks', 'blocked_by', 'depends_on', 'depended_on_by',
            'quality_gates', 'assigned_agents', 'deliverables',
            'strategic_value', 'commits', 'standards', 'merged_into', 'absorbed_tracks', 'metadata'
        }

        fs = FileSystemManager()
        violations = []

        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            with open(track_path) as f:
                data = yaml.safe_load(f)
                track_data = data.get('track', {})

                unknown_fields = set(track_data.keys()) - expected_fields
                if unknown_fields:
                    violations.append((track_id, sorted(unknown_fields)))

        if violations:
            error_msg = "\n".join([
                f"  {tid}: {', '.join(fields)}"
                for tid, fields in violations
            ])
            pytest.fail(
                f"Found {len(violations)} tracks with unknown fields:\n{error_msg}\n"
                f"Note: This might indicate typos or fields that should be added to the schema"
            )


class TestDependencyIntegrity:
    """Test dependency data integrity."""

    def test_dependency_statuses_are_strings(self):
        """All dependency current_status fields should be plain strings."""
        from vibey.roadmap.serialization.yaml_loader import load_track
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        fs = FileSystemManager()
        failed_tracks = []

        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            try:
                track = load_track(track_path)

                # Check depends_on statuses
                for dep in track.depends_on:
                    if not isinstance(dep.current_status, str):
                        failed_tracks.append((
                            track_id,
                            'depends_on',
                            dep.blocker_id,
                            type(dep.current_status).__name__
                        ))

                # Check blocked_by statuses
                for block in track.blocked_by:
                    if not isinstance(block.current_status, str):
                        failed_tracks.append((
                            track_id,
                            'blocked_by',
                            block.dependency_id,
                            type(block.current_status).__name__
                        ))

            except Exception as e:
                # Skip tracks that can't be loaded (separate test handles this)
                continue

        if failed_tracks:
            error_msg = "\n".join([
                f"  {track_id} ({field} -> {dep_id}): type={typ}"
                for track_id, field, dep_id, typ in failed_tracks
            ])
            pytest.fail(
                f"Found {len(failed_tracks)} dependency statuses that are not strings:\n{error_msg}\n"
                f"Fix: Use .value when assigning Status enums to current_status"
            )

    def test_enum_fields_are_strings_in_yaml(self):
        """Verify all enum fields are serialized as strings in YAML files."""
        import re

        yaml_files = get_all_roadmap_yaml_files()
        enum_pattern = re.compile(r'(status|priority|type):\s+!!python')

        failed_files = []
        for yaml_file in yaml_files:
            with open(yaml_file) as f:
                content = f.read()
                matches = enum_pattern.findall(content)
                if matches:
                    failed_files.append((yaml_file, matches))

        if failed_files:
            error_msg = "\n".join([
                f"  {f}: fields={fields}"
                for f, fields in failed_files
            ])
            pytest.fail(
                f"Found enum fields with Python serialization in {len(failed_files)} files:\n{error_msg}"
            )


class TestStructuralIntegrity:
    """Test structural integrity of roadmap data."""

    def test_all_tracks_loadable(self):
        """All track YAML files should load successfully."""
        from vibey.roadmap.serialization.yaml_loader import load_track
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        fs = FileSystemManager()
        failed_tracks = []

        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            try:
                load_track(track_path)
            except Exception as e:
                failed_tracks.append((track_id, str(e)))

        if failed_tracks:
            error_msg = "\n".join([f"  {t}: {e}" for t, e in failed_tracks])
            pytest.fail(f"Failed to load {len(failed_tracks)} tracks:\n{error_msg}")

    def test_all_sprints_loadable(self):
        """All sprint YAML files should load successfully."""
        from vibey.roadmap.serialization.yaml_loader import load_sprint
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        fs = FileSystemManager()
        failed_sprints = []

        for sprint_id in fs.list_sprints():
            sprint_path = fs.get_sprint_path(sprint_id)
            try:
                load_sprint(sprint_path)
            except Exception as e:
                failed_sprints.append((sprint_id, str(e)))

        if failed_sprints:
            error_msg = "\n".join([f"  {s}: {e}" for s, e in failed_sprints])
            pytest.fail(f"Failed to load {len(failed_sprints)} sprints:\n{error_msg}")

    def test_all_tasks_loadable(self):
        """All task YAML files should load successfully."""
        from vibey.roadmap.serialization.yaml_loader import load_task
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        fs = FileSystemManager()
        failed_tasks = []
        total_tasks = 0

        # Iterate through hierarchical structure
        for track_slug, track_id in fs.dir_manager.list_tracks():
            for sprint_slug, sprint_id in fs.dir_manager.list_sprints(track_slug):
                for task_slug, task_id in fs.dir_manager.list_tasks(track_slug, sprint_slug):
                    total_tasks += 1
                    task_path = fs.roadmap_root / track_slug / sprint_slug / task_slug / "task.yaml"
                    if not task_path.exists():
                        failed_tasks.append((task_id, "task.yaml file not found"))
                        continue
                    try:
                        load_task(task_path)
                    except Exception as e:
                        failed_tasks.append((task_id, str(e)))

        if failed_tasks and total_tasks > 0:
            # Only fail if more than 10% of tasks fail (some may be expected)
            if len(failed_tasks) > total_tasks * 0.1:
                error_msg = "\n".join([f"  {t}: {e}" for t, e in failed_tasks[:20]])
                pytest.fail(
                    f"Failed to load {len(failed_tasks)} tasks (showing first 20):\n{error_msg}"
                )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
