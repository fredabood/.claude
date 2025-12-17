"""
Tests for planned status operations.

Tests the planned_ops module which provides business logic for
checking and managing planned status of tickets.
"""

import pytest
import sqlite3
from pathlib import Path

from vibey.operations.roadmap.planned_ops import (
    PlannedCheckResult,
    PlanningWorkItem,
    check_planned,
    list_unplanned,
    get_next_planning_work,
    _detect_type,
    _get_unplanned_children,
)


@pytest.fixture
def roadmap_env(tmp_path):
    """Create a minimal roadmap environment for testing."""
    roadmap_root = tmp_path / ".vibey" / "roadmap"
    (roadmap_root / "tasks").mkdir(parents=True)
    (roadmap_root / "sprints").mkdir(parents=True)
    (roadmap_root / "tracks").mkdir(parents=True)

    # Create a minimal SQLite database
    db_path = roadmap_root / "roadmap.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE tracks (
            id TEXT PRIMARY KEY,
            name TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE sprints (
            id TEXT PRIMARY KEY,
            name TEXT,
            track_id TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE tasks (
            id TEXT PRIMARY KEY,
            title TEXT,
            sprint_id TEXT
        )
    """)
    conn.commit()
    conn.close()

    return {'root': tmp_path, 'roadmap': roadmap_root, 'db': db_path}


class TestDetectType:
    """Tests for _detect_type function."""

    def test_detect_task_type(self, roadmap_env):
        """Detect task type from YAML file."""
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01TEST.yaml"
        yaml_path.write_text("task:\n  id: 01TEST\n  title: Test Task")

        ticket_type = _detect_type("01TEST", roadmap_env['roadmap'])
        assert ticket_type == "task"

    def test_detect_sprint_type(self, roadmap_env):
        """Detect sprint type from YAML file."""
        yaml_path = roadmap_env['roadmap'] / "sprints" / "01SPRINT.yaml"
        yaml_path.write_text("sprint:\n  id: 01SPRINT\n  name: Test Sprint")

        ticket_type = _detect_type("01SPRINT", roadmap_env['roadmap'])
        assert ticket_type == "sprint"

    def test_detect_track_type(self, roadmap_env):
        """Detect track type from YAML file."""
        yaml_path = roadmap_env['roadmap'] / "tracks" / "01TRACK.yaml"
        yaml_path.write_text("track:\n  id: 01TRACK\n  name: Test Track")

        ticket_type = _detect_type("01TRACK", roadmap_env['roadmap'])
        assert ticket_type == "track"

    def test_detect_type_not_found(self, roadmap_env):
        """Raise FileNotFoundError when ticket doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Ticket not found"):
            _detect_type("01MISSING", roadmap_env['roadmap'])


class TestCheckPlanned:
    """Tests for check_planned function."""

    def test_task_planned_when_yaml_exists(self, roadmap_env):
        """Task is planned when YAML file exists."""
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01TEST.yaml"
        yaml_path.write_text("task:\n  id: 01TEST\n  title: Test Task")

        result = check_planned(roadmap_env['root'], "01TEST")

        assert isinstance(result, PlannedCheckResult)
        assert result.ticket_id == "01TEST"
        assert result.ticket_type == "task"
        assert result.is_planned is True
        assert result.criteria_met > 0

    def test_task_not_found(self, roadmap_env):
        """Raise FileNotFoundError when task doesn't exist."""
        with pytest.raises(FileNotFoundError):
            check_planned(roadmap_env['root'], "01MISSING")

    def test_result_has_required_fields(self, roadmap_env):
        """PlannedCheckResult has all required fields."""
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01TEST.yaml"
        yaml_path.write_text("task:\n  id: 01TEST\n  title: Test Task")

        result = check_planned(roadmap_env['root'], "01TEST")

        assert hasattr(result, 'ticket_id')
        assert hasattr(result, 'ticket_type')
        assert hasattr(result, 'is_planned')
        assert hasattr(result, 'criteria_total')
        assert hasattr(result, 'criteria_met')
        assert hasattr(result, 'unmet_criteria')
        assert hasattr(result, 'unplanned_children')


class TestListUnplanned:
    """Tests for list_unplanned function."""

    def test_returns_empty_when_no_db(self, tmp_path):
        """Return empty list when database doesn't exist."""
        results = list_unplanned(tmp_path)
        assert results == []

    def test_returns_empty_when_all_planned(self, roadmap_env):
        """Return empty list when all tickets are planned."""
        # Create YAML files for all tasks
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01TEST.yaml"
        yaml_path.write_text("task:\n  id: 01TEST\n  title: Test Task")

        # Add task to database
        conn = sqlite3.connect(roadmap_env['db'])
        conn.execute("INSERT INTO tasks VALUES (?, ?, ?)",
                     ("01TEST", "Test Task", "01SPRINT"))
        conn.commit()
        conn.close()

        results = list_unplanned(roadmap_env['root'], scope='tasks')

        assert results == []

    def test_returns_unplanned_tasks(self, roadmap_env):
        """Return unplanned tasks when YAML is missing."""
        # Add task to database but don't create YAML
        conn = sqlite3.connect(roadmap_env['db'])
        conn.execute("INSERT INTO tasks VALUES (?, ?, ?)",
                     ("01NOTYAML", "Missing YAML Task", "01SPRINT"))
        conn.commit()
        conn.close()

        results = list_unplanned(roadmap_env['root'], scope='tasks')

        assert len(results) == 1
        assert results[0]['id'] == "01NOTYAML"
        assert results[0]['type'] == "task"

    def test_filters_by_track(self, roadmap_env):
        """Filter unplanned tasks by track."""
        conn = sqlite3.connect(roadmap_env['db'])
        # Add sprint for track
        conn.execute("INSERT INTO sprints VALUES (?, ?, ?)",
                     ("01SPRINT", "Test Sprint", "01TRACK"))
        # Add task for sprint
        conn.execute("INSERT INTO tasks VALUES (?, ?, ?)",
                     ("01TASK", "Test Task", "01SPRINT"))
        # Add another sprint for different track
        conn.execute("INSERT INTO sprints VALUES (?, ?, ?)",
                     ("02SPRINT", "Other Sprint", "02TRACK"))
        # Add task for other sprint
        conn.execute("INSERT INTO tasks VALUES (?, ?, ?)",
                     ("02TASK", "Other Task", "02SPRINT"))
        conn.commit()
        conn.close()

        results = list_unplanned(roadmap_env['root'], scope='tasks', track_id='01TRACK')

        # Only task from 01TRACK should be returned
        assert len(results) == 1
        assert results[0]['id'] == "01TASK"

    def test_filters_by_sprint(self, roadmap_env):
        """Filter unplanned tasks by sprint."""
        conn = sqlite3.connect(roadmap_env['db'])
        conn.execute("INSERT INTO tasks VALUES (?, ?, ?)",
                     ("01TASK", "Test Task", "01SPRINT"))
        conn.execute("INSERT INTO tasks VALUES (?, ?, ?)",
                     ("02TASK", "Other Task", "02SPRINT"))
        conn.commit()
        conn.close()

        results = list_unplanned(roadmap_env['root'], scope='tasks', sprint_id='01SPRINT')

        assert len(results) == 1
        assert results[0]['id'] == "01TASK"


class TestGetNextPlanningWork:
    """Tests for get_next_planning_work function."""

    def test_returns_none_when_all_planned(self, roadmap_env):
        """Return None when track is fully planned."""
        # Create YAML for all tasks
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01TEST.yaml"
        yaml_path.write_text("task:\n  id: 01TEST\n  title: Test Task")

        conn = sqlite3.connect(roadmap_env['db'])
        conn.execute("INSERT INTO sprints VALUES (?, ?, ?)",
                     ("01SPRINT", "Test Sprint", "01TRACK"))
        conn.execute("INSERT INTO tasks VALUES (?, ?, ?)",
                     ("01TEST", "Test Task", "01SPRINT"))
        conn.commit()
        conn.close()

        result = get_next_planning_work(roadmap_env['root'], "01TRACK")

        assert result is None

    def test_returns_work_item_when_unplanned(self, roadmap_env):
        """Return work item when tasks are unplanned."""
        conn = sqlite3.connect(roadmap_env['db'])
        conn.execute("INSERT INTO sprints VALUES (?, ?, ?)",
                     ("01SPRINT", "Test Sprint", "01TRACK"))
        conn.execute("INSERT INTO tasks VALUES (?, ?, ?)",
                     ("01NOTYAML", "Missing YAML Task", "01SPRINT"))
        conn.commit()
        conn.close()

        result = get_next_planning_work(roadmap_env['root'], "01TRACK")

        assert isinstance(result, PlanningWorkItem)
        assert result.ticket_id == "01NOTYAML"
        assert result.ticket_type == "task"
        assert result.ticket_title == "Missing YAML Task"
        assert result.criterion is not None
        assert result.action is not None


class TestGetUnplannedChildren:
    """Tests for _get_unplanned_children function."""

    def test_returns_empty_for_tasks(self, roadmap_env):
        """Tasks have no children, return empty list."""
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01TEST.yaml"
        yaml_path.write_text("task:\n  id: 01TEST\n  title: Test Task")

        result = _get_unplanned_children("01TEST", "task", roadmap_env['roadmap'])

        assert result == []

    def test_returns_unplanned_tasks_for_sprint(self, roadmap_env):
        """Return unplanned tasks for a sprint."""
        # Create one planned task and one unplanned
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01PLANNED.yaml"
        yaml_path.write_text("task:\n  id: 01PLANNED\n  title: Planned Task")

        conn = sqlite3.connect(roadmap_env['db'])
        conn.execute("INSERT INTO tasks VALUES (?, ?, ?)",
                     ("01PLANNED", "Planned Task", "01SPRINT"))
        conn.execute("INSERT INTO tasks VALUES (?, ?, ?)",
                     ("01UNPLANNED", "Unplanned Task", "01SPRINT"))
        conn.commit()
        conn.close()

        result = _get_unplanned_children("01SPRINT", "sprint", roadmap_env['roadmap'])

        assert "01UNPLANNED" in result
        assert "01PLANNED" not in result

    def test_returns_unplanned_sprints_for_track(self, roadmap_env):
        """Return unplanned sprints for a track."""
        # Create one planned sprint and one unplanned
        yaml_path = roadmap_env['roadmap'] / "sprints" / "01PLANNED.yaml"
        yaml_path.write_text("sprint:\n  id: 01PLANNED\n  name: Planned Sprint")

        conn = sqlite3.connect(roadmap_env['db'])
        conn.execute("INSERT INTO sprints VALUES (?, ?, ?)",
                     ("01PLANNED", "Planned Sprint", "01TRACK"))
        conn.execute("INSERT INTO sprints VALUES (?, ?, ?)",
                     ("01UNPLANNED", "Unplanned Sprint", "01TRACK"))
        conn.commit()
        conn.close()

        result = _get_unplanned_children("01TRACK", "track", roadmap_env['roadmap'])

        assert "01UNPLANNED" in result
        assert "01PLANNED" not in result

    def test_returns_empty_when_no_db(self, tmp_path):
        """Return empty when database doesn't exist."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        roadmap_root.mkdir(parents=True)

        result = _get_unplanned_children("01TRACK", "track", roadmap_root)

        assert result == []


class TestPlannedCheckResultDataclass:
    """Tests for PlannedCheckResult dataclass."""

    def test_create_result(self):
        """Can create PlannedCheckResult with all fields."""
        result = PlannedCheckResult(
            ticket_id="01TEST",
            ticket_type="task",
            is_planned=True,
            criteria_total=2,
            criteria_met=2,
            unmet_criteria=[],
            unplanned_children=[],
        )

        assert result.ticket_id == "01TEST"
        assert result.is_planned is True
        assert result.criteria_total == 2

    def test_unplanned_result(self):
        """Can create unplanned result with unmet criteria."""
        result = PlannedCheckResult(
            ticket_id="01TEST",
            ticket_type="task",
            is_planned=False,
            criteria_total=2,
            criteria_met=1,
            unmet_criteria=["YAML file missing"],
            unplanned_children=[],
        )

        assert result.is_planned is False
        assert len(result.unmet_criteria) == 1


class TestPlanningWorkItemDataclass:
    """Tests for PlanningWorkItem dataclass."""

    def test_create_work_item(self):
        """Can create PlanningWorkItem with all fields."""
        item = PlanningWorkItem(
            ticket_id="01TEST",
            ticket_type="task",
            ticket_title="Test Task",
            criterion="yaml-exists",
            action="Create file: tasks/01TEST.yaml",
            required=True,
        )

        assert item.ticket_id == "01TEST"
        assert item.required is True
        assert "Create file" in item.action
