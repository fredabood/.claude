"""
Tests for YAML migration utilities.

Tests cover:
- Timestamp migration
- Criterion generation from children/dependencies/deliverables
- Task migration
- Sprint migration
- Track migration
- Roadmap migration
- YAMLMigrator class
"""

import pytest
from datetime import datetime, timezone

from vibey.roadmap.migration import (
    migrate_task_yaml,
    migrate_sprint_yaml,
    migrate_track_yaml,
    migrate_roadmap_yaml,
    YAMLMigrator,
)
from vibey.roadmap.migration.yaml_migrator import (
    migrate_timestamps,
    children_to_criteria_yaml,
    dependencies_to_criteria_yaml,
    deliverables_to_criteria_yaml,
)


# =============================================================================
# TIMESTAMP MIGRATION TESTS
# =============================================================================


class TestTimestampMigration:
    """Tests for timestamp field migration."""

    def test_migrate_created(self):
        """Test migrating created -> created_at."""
        data = {"created": "2025-01-01T00:00:00Z"}
        result = migrate_timestamps(data)
        assert "created_at" in result
        assert "created" not in result
        assert result["created_at"] == "2025-01-01T00:00:00Z"

    def test_migrate_started(self):
        """Test migrating started -> started_at."""
        data = {"started": "2025-01-02T00:00:00Z"}
        result = migrate_timestamps(data)
        assert "started_at" in result
        assert "started" not in result

    def test_migrate_completed(self):
        """Test migrating completed -> completed_at."""
        data = {"completed": "2025-01-03T00:00:00Z"}
        result = migrate_timestamps(data)
        assert "completed_at" in result
        assert "completed" not in result

    def test_adds_updated_at(self):
        """Test that updated_at is added if missing."""
        data = {}
        result = migrate_timestamps(data)
        assert "updated_at" in result

    def test_preserves_existing_updated_at(self):
        """Test that existing updated_at is preserved."""
        data = {"updated_at": "2025-01-01T00:00:00Z"}
        result = migrate_timestamps(data)
        assert result["updated_at"] == "2025-01-01T00:00:00Z"


# =============================================================================
# CRITERION YAML GENERATION TESTS
# =============================================================================


class TestChildrenToCriteriaYAML:
    """Tests for children_to_criteria_yaml function."""

    def test_empty_list(self):
        """Test empty children list."""
        criteria = children_to_criteria_yaml([])
        assert criteria == []

    def test_single_child(self):
        """Test single child conversion."""
        criteria = children_to_criteria_yaml(["task-001"])
        assert len(criteria) == 1
        assert criteria[0]["target"]["type"] == "completable"
        assert criteria[0]["target"]["completable_id"] == "task-001"
        assert criteria[0]["blocks_transition_to"] == "completed"

    def test_multiple_children(self):
        """Test multiple children conversion."""
        criteria = children_to_criteria_yaml(["task-001", "task-002"])
        assert len(criteria) == 2


class TestDependenciesToCriteriaYAML:
    """Tests for dependencies_to_criteria_yaml function."""

    def test_empty_list(self):
        """Test empty dependencies list."""
        criteria = dependencies_to_criteria_yaml([])
        assert criteria == []

    def test_single_dependency(self):
        """Test single dependency conversion."""
        criteria = dependencies_to_criteria_yaml(["dep-001"])
        assert len(criteria) == 1
        assert criteria[0]["blocks_transition_to"] == "in_progress"


class TestDeliverablesToCriteriaYAML:
    """Tests for deliverables_to_criteria_yaml function."""

    def test_empty_list(self):
        """Test empty deliverables list."""
        criteria = deliverables_to_criteria_yaml([])
        assert criteria == []

    def test_with_paths(self):
        """Test deliverable with paths."""
        deliverables = [{"paths": ["src/main.py"]}]
        criteria = deliverables_to_criteria_yaml(deliverables)
        assert len(criteria) == 1
        assert criteria[0]["target"]["type"] == "file_exists"
        assert "src/main.py" in criteria[0]["target"]["paths"]


# =============================================================================
# TASK MIGRATION TESTS
# =============================================================================


class TestMigrateTaskYAML:
    """Tests for migrate_task_yaml function."""

    def test_basic_task(self):
        """Test basic task migration."""
        task_data = {
            "task": {
                "id": "task-001",
                "title": "Test Task",
                "description": "A test task",
                "status": "not_started",
                "priority": "high",
                "task_type": "development",
                "sprint_id": "sprint-001",
                "track_id": "track-001",
                "roadmap_id": "roadmap-001",
            }
        }
        result = migrate_task_yaml(task_data)

        assert "ticket" in result
        ticket = result["ticket"]
        assert ticket["id"] == "task-001"
        assert ticket["name"] == "Test Task"
        assert ticket["ticket_type"] == "task"
        assert ticket["sprint_id"] == "sprint-001"

    def test_task_with_deliverables(self):
        """Test task migration with deliverables."""
        task_data = {
            "task": {
                "id": "task-001",
                "title": "Test Task",
                "status": "not_started",
                "task_type": "development",
                "deliverables": [
                    {"paths": ["src/main.py"]},
                    {"paths": ["src/utils.py"]},
                ],
            }
        }
        result = migrate_task_yaml(task_data)
        ticket = result["ticket"]

        # Should have criteria for deliverables
        assert len(ticket["criteria"]) == 2
        assert all(c["target"]["type"] == "file_exists" for c in ticket["criteria"])

    def test_task_with_dependencies(self):
        """Test task migration with dependencies."""
        task_data = {
            "task": {
                "id": "task-002",
                "title": "Dependent Task",
                "status": "not_started",
                "task_type": "development",
                "depends_on": [
                    {"blocker_id": "task-001"},
                ],
            }
        }
        result = migrate_task_yaml(task_data)
        ticket = result["ticket"]

        # Should have dependency criterion
        assert len(ticket["criteria"]) == 1
        assert ticket["criteria"][0]["blocks_transition_to"] == "in_progress"


# =============================================================================
# SPRINT MIGRATION TESTS
# =============================================================================


class TestMigrateSprintYAML:
    """Tests for migrate_sprint_yaml function."""

    def test_basic_sprint(self):
        """Test basic sprint migration."""
        sprint_data = {
            "sprint": {
                "id": "sprint-001",
                "name": "Sprint 1",
                "description": "First sprint",
                "status": "in_progress",
                "track_id": "track-001",
            }
        }
        result = migrate_sprint_yaml(sprint_data, task_ids=["task-001", "task-002"])
        ticket = result["ticket"]

        assert ticket["id"] == "sprint-001"
        assert ticket["ticket_type"] == "sprint"
        assert len(ticket["criteria"]) == 2  # Two task criteria


# =============================================================================
# TRACK MIGRATION TESTS
# =============================================================================


class TestMigrateTrackYAML:
    """Tests for migrate_track_yaml function."""

    def test_basic_track(self):
        """Test basic track migration."""
        track_data = {
            "track": {
                "id": "track-001",
                "name": "Track 1",
                "description": "First track",
                "status": "not_started",
                "priority": "high",
                "roadmap_id": "roadmap-001",
            }
        }
        result = migrate_track_yaml(track_data, sprint_ids=["sprint-001"])
        ticket = result["ticket"]

        assert ticket["id"] == "track-001"
        assert ticket["ticket_type"] == "track"
        assert len(ticket["criteria"]) == 1


# =============================================================================
# ROADMAP MIGRATION TESTS
# =============================================================================


class TestMigrateRoadmapYAML:
    """Tests for migrate_roadmap_yaml function."""

    def test_basic_roadmap(self):
        """Test basic roadmap migration."""
        roadmap_data = {
            "roadmap": {
                "id": "roadmap-001",
                "name": "My Roadmap",
                "description": "A test roadmap",
                "status": "in_progress",
                "version": "1.0.0",
            }
        }
        result = migrate_roadmap_yaml(roadmap_data, track_ids=["track-001", "track-002"])
        ticket = result["ticket"]

        assert ticket["id"] == "roadmap-001"
        assert ticket["ticket_type"] == "roadmap"
        assert ticket["version"] == "1.0.0"
        assert len(ticket["criteria"]) == 2


# =============================================================================
# YAML MIGRATOR CLASS TESTS
# =============================================================================


class TestYAMLMigrator:
    """Tests for YAMLMigrator class."""

    def test_detect_legacy_format(self):
        """Test detecting legacy format."""
        migrator = YAMLMigrator()
        data = {"task": {"id": "task-001"}}
        assert migrator.detect_format(data) == "legacy"

    def test_detect_unified_format(self):
        """Test detecting unified format."""
        migrator = YAMLMigrator()
        data = {"ticket": {"id": "task-001"}}
        assert migrator.detect_format(data) == "unified"

    def test_detect_task_type(self):
        """Test detecting task type."""
        migrator = YAMLMigrator()
        data = {"task": {"id": "task-001"}}
        assert migrator.detect_type(data) == "task"

    def test_detect_sprint_type(self):
        """Test detecting sprint type."""
        migrator = YAMLMigrator()
        data = {"sprint": {"id": "sprint-001"}}
        assert migrator.detect_type(data) == "sprint"

    def test_migrate_already_unified(self):
        """Test that unified format is returned unchanged."""
        migrator = YAMLMigrator()
        data = {"ticket": {"id": "task-001", "criteria": []}}
        result = migrator.migrate_data(data)
        assert result == data
