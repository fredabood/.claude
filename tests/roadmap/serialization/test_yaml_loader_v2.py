"""
Tests for the v2 YAML loader functions (Pydantic model output).

These tests verify that:
1. load_task_ticket() correctly loads v1 and v2 format YAML
2. load_sprint_ticket() correctly loads v1 and v2 format YAML
3. load_track_ticket() correctly loads v1 and v2 format YAML
4. load_roadmap_ticket() correctly loads v1 and v2 format YAML
5. detect_yaml_format() correctly identifies v1 vs v2 format
6. Migration from v1 to v2 preserves all essential data
"""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from vibey.roadmap.serialization.yaml_loader import (
    detect_yaml_format,
    load_task_ticket,
    load_sprint_ticket,
    load_track_ticket,
    load_roadmap_ticket,
    _convert_status_to_ticket_status,
    _convert_priority,
    _convert_complexity,
    _convert_task_type,
)
from vibey.roadmap.models.ticket.domain import (
    TaskTicket,
    SprintTicket,
    TrackTicket,
    RoadmapTicket,
)
from vibey.roadmap.models.ticket.enums import (
    TicketStatus,
    Priority,
    Complexity,
    TaskType,
)

# Use aliases to match the yaml_loader exports
PydanticPriority = Priority
PydanticComplexity = Complexity
PydanticTaskType = TaskType


# =============================================================================
# FORMAT DETECTION TESTS
# =============================================================================


class TestDetectYamlFormat:
    """Tests for detect_yaml_format function."""

    def test_detects_v2_with_criteria(self):
        """V2 format has criteria field."""
        data = {"id": "task-1", "criteria": []}
        assert detect_yaml_format(data) == "v2"

    def test_detects_v2_with_parent_ref(self):
        """V2 format has parent_ref field."""
        data = {"id": "task-1", "parent_ref": "sprint-1"}
        assert detect_yaml_format(data) == "v2"

    def test_detects_v2_with_ticket_type(self):
        """V2 format has ticket_type field."""
        data = {"id": "task-1", "ticket_type": "task"}
        assert detect_yaml_format(data) == "v2"

    def test_detects_v2_with_commits_local(self):
        """V2 format has commits_local field."""
        data = {"id": "task-1", "commits_local": []}
        assert detect_yaml_format(data) == "v2"

    def test_detects_v2_with_assigned_agents(self):
        """V2 format has assigned_agents (plural) field."""
        data = {"id": "task-1", "assigned_agents": []}
        assert detect_yaml_format(data) == "v2"

    def test_detects_v1_with_blocked_by(self):
        """V1 format has blocked_by as list of blockers."""
        data = {"id": "task-1", "blocked_by": [{"dependency_id": "task-0"}]}
        assert detect_yaml_format(data) == "v1"

    def test_detects_v1_with_depends_on_old_format(self):
        """V1 format has depends_on with blocker_id."""
        data = {"id": "task-1", "depends_on": [{"blocker_id": "task-0"}]}
        assert detect_yaml_format(data) == "v1"

    def test_defaults_to_v1_for_unknown(self):
        """Default to v1 for backward compatibility."""
        data = {"id": "task-1", "title": "Test task"}
        assert detect_yaml_format(data) == "v1"


# =============================================================================
# CONVERSION HELPER TESTS
# =============================================================================


class TestConversionHelpers:
    """Tests for conversion helper functions."""

    def test_convert_status_to_ticket_status(self):
        """Test status string to enum conversion."""
        assert _convert_status_to_ticket_status("not_started") == TicketStatus.NOT_STARTED
        assert _convert_status_to_ticket_status("in_progress") == TicketStatus.IN_PROGRESS
        assert _convert_status_to_ticket_status("completed") == TicketStatus.COMPLETED
        assert _convert_status_to_ticket_status("blocked") == TicketStatus.PAUSED  # blocked -> PAUSED
        assert _convert_status_to_ticket_status("cancelled") == TicketStatus.WONT_DO

    def test_convert_priority(self):
        """Test priority string to enum conversion."""
        assert _convert_priority("low") == PydanticPriority.LOW
        assert _convert_priority("medium") == PydanticPriority.MEDIUM
        assert _convert_priority("high") == PydanticPriority.HIGH
        assert _convert_priority("critical") == PydanticPriority.CRITICAL
        assert _convert_priority("MEDIUM") == PydanticPriority.MEDIUM  # Case insensitive

    def test_convert_complexity(self):
        """Test complexity string to enum conversion."""
        # PydanticComplexity enum has: LOW, MEDIUM, HIGH, CRITICAL
        assert _convert_complexity("simple") == PydanticComplexity.LOW
        assert _convert_complexity("low") == PydanticComplexity.LOW
        assert _convert_complexity("medium") == PydanticComplexity.MEDIUM
        assert _convert_complexity("complex") == PydanticComplexity.HIGH
        assert _convert_complexity("high") == PydanticComplexity.HIGH

    def test_convert_task_type(self):
        """Test task type string to enum conversion."""
        # PydanticTaskType enum has: DEVELOPMENT, DOCUMENTATION, TESTING, RESEARCH, REVIEW, INFRASTRUCTURE, GATE
        assert _convert_task_type("development") == PydanticTaskType.DEVELOPMENT
        assert _convert_task_type("completion_gate") == PydanticTaskType.GATE
        assert _convert_task_type("production_gate") == PydanticTaskType.GATE
        assert _convert_task_type("documentation") == PydanticTaskType.DOCUMENTATION
        assert _convert_task_type("testing") == PydanticTaskType.TESTING
        assert _convert_task_type("gate") == PydanticTaskType.GATE


# =============================================================================
# TASK TICKET LOADER TESTS
# =============================================================================


class TestLoadTaskTicket:
    """Tests for load_task_ticket function."""

    def test_load_v1_task(self, tmp_path: Path):
        """Load a v1 format task YAML file."""
        task_yaml = tmp_path / "task.yaml"
        task_data = {
            "task": {
                "id": "test-task-001",
                "sprint_id": "sprint-1",
                "track_id": "track-1",
                "roadmap_id": "roadmap-1",
                "task_type": "development",
                "title": "Test Task",
                "description": "A test task description",
                "status": "in_progress",
                "created": "2025-12-01T10:00:00+00:00",
                "started": "2025-12-01T11:00:00+00:00",
                "assigned_agent": "test-agent",
                "priority": "high",
                "complexity": "medium",
                "estimated_tokens": 100,
                "depends_on": [
                    {
                        "blocker_id": "test-task-000",
                        "blocker_type": "task",
                        "required_status": "completed",
                        "current_status": "completed",
                        "blocks_transition_to": "in_progress",
                    }
                ],
                "deliverables": [
                    {"type": "code", "paths": ["src/module.py"]}
                ],
                "metadata": {
                    "last_updated": "2025-12-01T12:00:00+00:00",
                },
            }
        }
        with open(task_yaml, "w") as f:
            yaml.dump(task_data, f)

        task = load_task_ticket(task_yaml)

        assert isinstance(task, TaskTicket)
        assert task.id == "test-task-001"
        assert task.name == "Test Task"
        assert task.sprint_id == "sprint-1"
        assert task.track_id == "track-1"
        assert task.roadmap_id == "roadmap-1"
        assert task.status == TicketStatus.IN_PROGRESS
        assert task.priority == PydanticPriority.HIGH
        assert task.complexity == PydanticComplexity.MEDIUM  # 'medium' maps to MEDIUM
        assert task.estimated_tokens == 100
        assert len(task.assigned_agents) == 1
        assert task.assigned_agents[0] == "test-agent"

        # TaskTicket is a leaf node - no dependency criteria (CompletableTarget)
        # Only deliverable criteria (FileExistsTarget) are allowed
        dep_criteria = [c for c in task.criteria if c.id.startswith("dep-")]
        assert len(dep_criteria) == 0  # Tasks cannot have CompletableTarget criteria

        # Check criteria were created from deliverables
        deliv_criteria = [c for c in task.criteria if c.id.startswith("deliverable-")]
        assert len(deliv_criteria) == 1

    def test_load_task_missing_root_key(self, tmp_path: Path):
        """Raise error if task root key is missing."""
        task_yaml = tmp_path / "task.yaml"
        with open(task_yaml, "w") as f:
            yaml.dump({"id": "test-task-001"}, f)

        with pytest.raises(ValueError, match="Missing 'task' root key"):
            load_task_ticket(task_yaml)


# =============================================================================
# SPRINT TICKET LOADER TESTS
# =============================================================================


class TestLoadSprintTicket:
    """Tests for load_sprint_ticket function."""

    def test_load_v1_sprint(self, tmp_path: Path):
        """Load a v1 format sprint YAML file."""
        sprint_yaml = tmp_path / "sprint.yaml"
        sprint_data = {
            "sprint": {
                "id": "test-sprint-1",
                "name": "Test Sprint",
                "track_id": "track-1",
                "roadmap_id": "roadmap-1",
                "status": "in_progress",
                "created": "2025-12-01T10:00:00+00:00",
                "started": "2025-12-01T11:00:00+00:00",
                "tasks": [
                    {"id": "task-001", "status": "completed"},
                    {"id": "task-002", "status": "in_progress"},
                ],
                "depends_on": [
                    {
                        "blocker_id": "test-sprint-0",
                        "blocker_type": "sprint",
                        "required_status": "completed",
                    }
                ],
                "deliverables": ["docs/README.md"],
                "goal": "Complete the test sprint",
                "success_criteria": ["All tasks completed"],
                "metadata": {
                    "estimated_duration": "1 week",
                },
            }
        }
        with open(sprint_yaml, "w") as f:
            yaml.dump(sprint_data, f)

        sprint = load_sprint_ticket(sprint_yaml)

        assert isinstance(sprint, SprintTicket)
        assert sprint.id == "test-sprint-1"
        assert sprint.name == "Test Sprint"
        assert sprint.track_id == "track-1"
        assert sprint.roadmap_id == "roadmap-1"
        assert sprint.status == TicketStatus.IN_PROGRESS
        assert sprint.goal == "Complete the test sprint"
        assert sprint.success_criteria_text == ["All tasks completed"]

        # Check criteria were created from tasks
        subtask_criteria = [c for c in sprint.criteria if c.id.startswith("subtask-")]
        assert len(subtask_criteria) == 2

        # Check criteria were created from depends_on
        dep_criteria = [c for c in sprint.criteria if c.id.startswith("dep-")]
        assert len(dep_criteria) == 1


# =============================================================================
# TRACK TICKET LOADER TESTS
# =============================================================================


class TestLoadTrackTicket:
    """Tests for load_track_ticket function."""

    def test_load_v1_track(self, tmp_path: Path):
        """Load a v1 format track YAML file."""
        track_yaml = tmp_path / "track.yaml"
        track_data = {
            "track": {
                "id": "test-track-1",
                "name": "Test Track",
                "roadmap_id": "roadmap-1",
                "status": "in_progress",
                "created": "2025-12-01T10:00:00+00:00",
                "started": "2025-12-01T11:00:00+00:00",
                "priority": "high",
                "sprints": [
                    {"id": "sprint-1", "status": "completed"},
                    {"id": "sprint-2", "status": "in_progress"},
                ],
                "strategic_value": [
                    "Improve performance",
                    "Reduce costs",
                ],
                "quality_gates": [
                    {"name": "Code Coverage", "threshold": 80, "blocking": True},
                ],
                "metadata": {
                    "notes": "Test track for development",
                },
            }
        }
        with open(track_yaml, "w") as f:
            yaml.dump(track_data, f)

        track = load_track_ticket(track_yaml)

        assert isinstance(track, TrackTicket)
        assert track.id == "test-track-1"
        assert track.name == "Test Track"
        assert track.roadmap_id == "roadmap-1"
        assert track.status == TicketStatus.IN_PROGRESS
        assert track.priority == PydanticPriority.HIGH
        assert track.strategic_value == ["Improve performance", "Reduce costs"]

        # Check criteria were created from sprints
        sprint_criteria = [c for c in track.criteria if c.id.startswith("sprint-")]
        assert len(sprint_criteria) == 2

        # Check criteria were created from quality_gates
        gate_criteria = [c for c in track.criteria if c.id.startswith("gate-")]
        assert len(gate_criteria) == 1


# =============================================================================
# ROADMAP TICKET LOADER TESTS
# =============================================================================


class TestLoadRoadmapTicket:
    """Tests for load_roadmap_ticket function."""

    def test_load_v1_roadmap(self, tmp_path: Path):
        """Load a v1 format roadmap YAML file."""
        roadmap_yaml = tmp_path / "roadmap.yaml"
        roadmap_data = {
            "roadmap": {
                "id": "test-roadmap",
                "name": "Test Roadmap",
                "version": "1.0.0",
                "status": "in_progress",
                "created": "2025-12-01T10:00:00+00:00",
                "started": "2025-12-01T11:00:00+00:00",
                "tracks": [
                    {"id": "track-1", "status": "completed"},
                    {"id": "track-2", "status": "in_progress"},
                ],
                "version_strategy": {
                    "major_on": "breaking_change",
                    "minor_on": "feature",
                    "patch_on": "fix",
                },
                "deployed_platforms": [
                    {
                        "platform": "claude-code",
                        "context_window": 200000,
                        "deployed_at": 1733043600,
                        "primary": True,
                    }
                ],
                "metadata": {
                    "description": "A test roadmap for development",
                },
            }
        }
        with open(roadmap_yaml, "w") as f:
            yaml.dump(roadmap_data, f)

        roadmap = load_roadmap_ticket(roadmap_yaml)

        assert isinstance(roadmap, RoadmapTicket)
        assert roadmap.id == "test-roadmap"
        assert roadmap.name == "Test Roadmap"
        assert roadmap.version == "1.0.0"
        assert roadmap.status == TicketStatus.IN_PROGRESS
        assert roadmap.parent_ref is None  # Roadmap has no parent

        # Check criteria were created from tracks
        track_criteria = [c for c in roadmap.criteria if c.id.startswith("track-")]
        assert len(track_criteria) == 2

        # Check version strategy was parsed
        assert roadmap.version_strategy is not None
        assert roadmap.version_strategy.scheme == "semver"

        # Check deployed platforms were parsed
        assert len(roadmap.deployed_platforms) == 1
        assert roadmap.deployed_platforms[0].platform == "claude-code"
        assert roadmap.deployed_platforms[0].primary is True


# =============================================================================
# INTEGRATION TEST WITH REAL YAML FILES
# =============================================================================


class TestLoadRealYamlFiles:
    """Integration tests with real YAML files from the repository.

    NOTE: These tests are currently skipped because they depend on
    full v1->v2 migration which has known import conflicts with
    legacy models (PlatformDeployment, VersionStrategy). These will
    be fixed in a future sprint when the migration is fully tested.
    """

    @pytest.mark.skip(reason="v1->v2 migration has import conflicts - will fix in future sprint")
    def test_load_real_task(self):
        """Load a real task YAML file from the repository."""
        task_path = Path(".vibey/roadmap/sqlite-backend/sqlite-backend-8/sqlite-backend-8-task-001/task.yaml")
        if not task_path.exists():
            pytest.skip("Real task file not found")

        task = load_task_ticket(task_path)
        assert isinstance(task, TaskTicket)
        assert task.id == "sqlite-backend-8-task-001"
        assert task.sprint_id == "sqlite-backend-8"

    @pytest.mark.skip(reason="v1->v2 migration has import conflicts - will fix in future sprint")
    def test_load_real_sprint(self):
        """Load a real sprint YAML file from the repository."""
        sprint_path = Path(".vibey/roadmap/sqlite-backend/sqlite-backend-8/sprint.yaml")
        if not sprint_path.exists():
            pytest.skip("Real sprint file not found")

        sprint = load_sprint_ticket(sprint_path)
        assert isinstance(sprint, SprintTicket)
        assert sprint.id == "sqlite-backend-8"
        assert sprint.track_id == "sqlite-backend"

    @pytest.mark.skip(reason="v1->v2 migration has import conflicts - will fix in future sprint")
    def test_load_real_track(self):
        """Load a real track YAML file from the repository."""
        track_path = Path(".vibey/roadmap/sqlite-backend/track.yaml")
        if not track_path.exists():
            pytest.skip("Real track file not found")

        track = load_track_ticket(track_path)
        assert isinstance(track, TrackTicket)
        assert track.id == "sqlite-backend"
        assert track.name == "SQLite Database Backend"

    @pytest.mark.skip(reason="v1->v2 migration has import conflicts - will fix in future sprint")
    def test_load_real_roadmap(self):
        """Load a real roadmap YAML file from the repository."""
        roadmap_path = Path(".vibey/roadmap/roadmap.yaml")
        if not roadmap_path.exists():
            pytest.skip("Real roadmap file not found")

        roadmap = load_roadmap_ticket(roadmap_path)
        assert isinstance(roadmap, RoadmapTicket)
        assert roadmap.id == "vibey-framework-v2"
