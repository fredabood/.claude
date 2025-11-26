"""
Tests for computed SQL views.

Tests verify that views correctly compute progress aggregations
and replace the 24 manually-maintained counter fields.
"""

import pytest
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import os

from .connection import get_connection, close_connection
from .schema import create_schema
from .views import (
    VIEW_DEFINITIONS,
    VIEW_ORDER,
    create_views,
    drop_views,
    view_exists,
    get_view_names,
    get_sprint_progress,
    get_track_progress,
    get_roadmap_progress,
    get_blocked_entities,
    get_unblocked_tasks,
    get_dependency_chain,
    get_quality_gate_summary,
    get_failing_quality_gates,
    get_recent_activity,
    get_velocity_metrics,
    get_all_progress,
)
from .crud import (
    create_roadmap,
    create_track,
    create_sprint,
    create_task,
    add_blocker,
    add_dependency,
    add_quality_gate,
    update_quality_gate,
)


@pytest.fixture
def db_path():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield Path(path)
    close_connection(Path(path))
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def conn(db_path):
    """Create a connection with schema and views initialized."""
    connection = get_connection(db_path=db_path)
    create_schema(conn=connection)
    create_views(conn=connection)
    connection.commit()
    return connection


@pytest.fixture
def sample_data(conn):
    """Create sample roadmap with tracks, sprints, and tasks."""
    now = datetime.now(timezone.utc)

    # Create roadmap
    create_roadmap(
        id="test-roadmap",
        name="Test Roadmap",
        version="1.0.0",
        status="in_progress",
        created=now,
        conn=conn,
    )

    # Create tracks
    create_track(
        id="track-1",
        roadmap_id="test-roadmap",
        name="Track 1",
        status="in_progress",
        created=now,
        conn=conn,
    )
    create_track(
        id="track-2",
        roadmap_id="test-roadmap",
        name="Track 2",
        status="not_started",
        created=now,
        conn=conn,
    )

    # Create sprints for track-1
    create_sprint(
        id="sprint-1",
        track_id="track-1",
        roadmap_id="test-roadmap",
        name="Sprint 1",
        status="in_progress",
        created=now,
        conn=conn,
    )
    create_sprint(
        id="sprint-2",
        track_id="track-1",
        roadmap_id="test-roadmap",
        name="Sprint 2",
        status="not_started",
        created=now,
        conn=conn,
    )

    # Create tasks for sprint-1 (3 dev, 1 completion gate, 1 production gate)
    for i in range(3):
        status = "completed" if i < 2 else "in_progress"
        create_task(
            id=f"task-dev-{i+1}",
            sprint_id="sprint-1",
            track_id="track-1",
            roadmap_id="test-roadmap",
            task_type="development",
            title=f"Development Task {i+1}",
            status=status,
            created=now,
            completed=now if status == "completed" else None,
            conn=conn,
        )

    create_task(
        id="task-cg-1",
        sprint_id="sprint-1",
        track_id="track-1",
        roadmap_id="test-roadmap",
        task_type="completion_gate",
        title="Completion Gate Task",
        status="not_started",
        created=now,
        conn=conn,
    )

    create_task(
        id="task-pg-1",
        sprint_id="sprint-1",
        track_id="track-1",
        roadmap_id="test-roadmap",
        task_type="production_gate",
        title="Production Gate Task",
        status="not_started",
        created=now,
        conn=conn,
    )

    # Create tasks for sprint-2
    for i in range(2):
        create_task(
            id=f"task-s2-{i+1}",
            sprint_id="sprint-2",
            track_id="track-1",
            roadmap_id="test-roadmap",
            task_type="development",
            title=f"Sprint 2 Task {i+1}",
            status="not_started",
            created=now,
            conn=conn,
        )

    conn.commit()
    return conn


# =============================================================================
# VIEW MANAGEMENT TESTS
# =============================================================================

class TestViewManagement:
    """Tests for view creation and management."""

    def test_create_views(self, db_path):
        """Test creating all views."""
        conn = get_connection(db_path=db_path)
        create_schema(conn=conn)
        create_views(conn=conn)
        conn.commit()

        view_names = get_view_names(conn=conn)
        assert len(view_names) == 13

        for view_name in VIEW_ORDER:
            assert view_name in view_names

    def test_drop_views(self, conn):
        """Test dropping all views."""
        # Views already created by fixture
        assert len(get_view_names(conn=conn)) == 13

        drop_views(conn=conn)
        conn.commit()

        assert len(get_view_names(conn=conn)) == 0

    def test_view_exists(self, conn):
        """Test checking if a view exists."""
        assert view_exists("v_sprint_progress", conn=conn)
        assert view_exists("v_track_progress", conn=conn)
        assert not view_exists("nonexistent_view", conn=conn)

    def test_view_definitions_complete(self):
        """Test that all views in ORDER are in DEFINITIONS."""
        for view_name in VIEW_ORDER:
            assert view_name in VIEW_DEFINITIONS


# =============================================================================
# PROGRESS VIEW TESTS
# =============================================================================

class TestSprintProgress:
    """Tests for v_sprint_progress view."""

    def test_sprint_progress_task_counts(self, sample_data):
        """Test sprint progress computes task counts correctly."""
        conn = sample_data

        progress = get_sprint_progress("sprint-1", conn=conn)

        assert progress is not None
        assert progress["sprint_id"] == "sprint-1"
        assert progress["tasks_total"] == 5
        assert progress["tasks_completed"] == 2
        assert progress["development_tasks_total"] == 3
        assert progress["development_tasks_completed"] == 2
        assert progress["completion_gate_tasks_total"] == 1
        assert progress["completion_gate_tasks_completed"] == 0
        assert progress["production_gate_tasks_total"] == 1
        assert progress["production_gate_tasks_completed"] == 0

    def test_sprint_progress_completion_percent(self, sample_data):
        """Test sprint progress computes completion percentage."""
        conn = sample_data

        progress = get_sprint_progress("sprint-1", conn=conn)

        # 2 completed out of 5 = 40%
        assert progress["completion_percent"] == 40

    def test_sprint_progress_empty_sprint(self, sample_data):
        """Test sprint progress for sprint with no tasks."""
        conn = sample_data

        # sprint-2 has 2 not_started tasks
        progress = get_sprint_progress("sprint-2", conn=conn)

        assert progress["tasks_total"] == 2
        assert progress["tasks_completed"] == 0
        assert progress["completion_percent"] == 0

    def test_sprint_progress_nonexistent(self, sample_data):
        """Test sprint progress returns None for nonexistent sprint."""
        conn = sample_data

        progress = get_sprint_progress("nonexistent", conn=conn)
        assert progress is None


class TestTrackProgress:
    """Tests for v_track_progress view."""

    def test_track_progress_sprint_counts(self, sample_data):
        """Test track progress computes sprint counts."""
        conn = sample_data

        progress = get_track_progress("track-1", conn=conn)

        assert progress is not None
        assert progress["track_id"] == "track-1"
        assert progress["sprints_total"] == 2
        assert progress["sprints_completed"] == 0  # No completed sprints

    def test_track_progress_task_aggregation(self, sample_data):
        """Test track progress aggregates task counts from sprints."""
        conn = sample_data

        progress = get_track_progress("track-1", conn=conn)

        # sprint-1 has 5 tasks (2 completed), sprint-2 has 2 tasks (0 completed)
        assert progress["tasks_total"] == 7
        assert progress["tasks_completed"] == 2

    def test_track_progress_completion_percent(self, sample_data):
        """Test track progress completion percentage."""
        conn = sample_data

        progress = get_track_progress("track-1", conn=conn)

        # 2 completed out of 7 ≈ 29%
        assert progress["completion_percent"] == 29

    def test_track_progress_empty_track(self, sample_data):
        """Test track progress for track with no sprints."""
        conn = sample_data

        progress = get_track_progress("track-2", conn=conn)

        assert progress["sprints_total"] == 0
        assert progress["tasks_total"] == 0
        assert progress["completion_percent"] == 0


class TestRoadmapProgress:
    """Tests for v_roadmap_progress view."""

    def test_roadmap_progress_track_counts(self, sample_data):
        """Test roadmap progress computes track counts."""
        conn = sample_data

        progress = get_roadmap_progress("test-roadmap", conn=conn)

        assert progress is not None
        assert progress["roadmap_id"] == "test-roadmap"
        assert progress["tracks_total"] == 2
        assert progress["tracks_completed"] == 0

    def test_roadmap_progress_aggregation(self, sample_data):
        """Test roadmap progress aggregates from tracks."""
        conn = sample_data

        progress = get_roadmap_progress("test-roadmap", conn=conn)

        assert progress["sprints_total"] == 2
        assert progress["sprints_completed"] == 0
        assert progress["tasks_total"] == 7
        assert progress["tasks_completed"] == 2

    def test_roadmap_progress_completion_percent(self, sample_data):
        """Test roadmap progress completion percentage."""
        conn = sample_data

        progress = get_roadmap_progress("test-roadmap", conn=conn)

        # 2 completed out of 7 ≈ 29%
        assert progress["completion_percent"] == 29


# =============================================================================
# BLOCKING VIEW TESTS
# =============================================================================

class TestBlockedEntities:
    """Tests for v_blocked_entities view."""

    def test_blocked_entities_empty(self, sample_data):
        """Test no blocked entities initially."""
        conn = sample_data

        blocked = get_blocked_entities(conn=conn)
        assert len(blocked) == 0

    def test_blocked_entities_with_blocker(self, sample_data):
        """Test blocked entities shows blockers."""
        conn = sample_data

        # Add a blocking relationship
        add_blocker(
            blocker_type="task",
            blocker_id="task-dev-1",
            blocked_type="task",
            blocked_id="task-cg-1",
            reason="Must complete dev first",
            conn=conn,
        )
        conn.commit()

        blocked = get_blocked_entities(conn=conn)

        assert len(blocked) == 1
        assert blocked[0]["blocked_id"] == "task-cg-1"
        assert blocked[0]["blocker_id"] == "task-dev-1"
        # task-dev-1 is completed, so blocker_completed should be True
        assert blocked[0]["blocker_completed"] == 1

    def test_blocked_entities_filter_by_type(self, sample_data):
        """Test filtering blocked entities by type."""
        conn = sample_data

        add_blocker("task", "task-dev-1", "task", "task-cg-1", conn=conn)
        add_blocker("sprint", "sprint-1", "sprint", "sprint-2", conn=conn)
        conn.commit()

        task_blocked = get_blocked_entities(entity_type="task", conn=conn)
        sprint_blocked = get_blocked_entities(entity_type="sprint", conn=conn)

        assert len(task_blocked) == 1
        assert len(sprint_blocked) == 1


class TestUnblockedTasks:
    """Tests for v_unblocked_tasks view."""

    def test_unblocked_tasks_all_ready(self, sample_data):
        """Test all not_started tasks are unblocked initially."""
        conn = sample_data

        unblocked = get_unblocked_tasks(conn=conn)

        # Should include all not_started tasks
        # Note: task-dev-3 is in_progress, not not_started
        unblocked_ids = {t["id"] for t in unblocked}
        expected = {"task-cg-1", "task-pg-1", "task-s2-1", "task-s2-2"}
        assert unblocked_ids == expected

    def test_unblocked_tasks_with_blocker(self, sample_data):
        """Test blocked tasks are excluded."""
        conn = sample_data

        # Block task-cg-1
        add_blocker("task", "task-dev-3", "task", "task-cg-1", conn=conn)
        conn.commit()

        unblocked = get_unblocked_tasks(conn=conn)
        unblocked_ids = {t["id"] for t in unblocked}

        # task-cg-1 is blocked by incomplete task-dev-3
        assert "task-cg-1" not in unblocked_ids


# =============================================================================
# DEPENDENCY VIEW TESTS
# =============================================================================

class TestDependencyChain:
    """Tests for v_dependency_chain view."""

    def test_dependency_chain_empty(self, sample_data):
        """Test no dependencies initially."""
        conn = sample_data

        chain = get_dependency_chain("task", "task-dev-1", conn=conn)
        assert len(chain) == 0

    def test_dependency_chain_simple(self, sample_data):
        """Test simple dependency chain."""
        conn = sample_data

        add_dependency("task", "task-cg-1", "task", "task-dev-3", conn=conn)
        conn.commit()

        chain = get_dependency_chain("task", "task-cg-1", conn=conn)

        assert len(chain) == 1
        assert chain[0]["dependency_id"] == "task-dev-3"
        assert chain[0]["depth"] == 1

    def test_dependency_chain_transitive(self, sample_data):
        """Test transitive dependency chain."""
        conn = sample_data

        # task-pg-1 -> task-cg-1 -> task-dev-3
        add_dependency("task", "task-cg-1", "task", "task-dev-3", conn=conn)
        add_dependency("task", "task-pg-1", "task", "task-cg-1", conn=conn)
        conn.commit()

        chain = get_dependency_chain("task", "task-pg-1", conn=conn)

        assert len(chain) == 2
        # Direct dependency at depth 1
        assert any(d["dependency_id"] == "task-cg-1" and d["depth"] == 1 for d in chain)
        # Transitive dependency at depth 2
        assert any(d["dependency_id"] == "task-dev-3" and d["depth"] == 2 for d in chain)


# =============================================================================
# QUALITY GATE VIEW TESTS
# =============================================================================

class TestQualityGateSummary:
    """Tests for v_quality_gate_summary view."""

    def test_quality_gate_summary_empty(self, sample_data):
        """Test no gates initially."""
        conn = sample_data

        summary = get_quality_gate_summary("track", "track-1", conn=conn)
        assert summary is None

    def test_quality_gate_summary_with_gates(self, sample_data):
        """Test gate summary with multiple gates."""
        conn = sample_data

        add_quality_gate("track", "track-1", "test_gate_1", status="passed", conn=conn)
        add_quality_gate("track", "track-1", "test_gate_2", status="failed", blocking=True, conn=conn)
        add_quality_gate("track", "track-1", "test_gate_3", status="not_run", conn=conn)
        conn.commit()

        summary = get_quality_gate_summary("track", "track-1", conn=conn)

        assert summary is not None
        assert summary["gates_total"] == 3
        assert summary["gates_passed"] == 1
        assert summary["gates_failed"] == 1
        assert summary["gates_pending"] == 1
        assert summary["blocking_failures"] == 1
        assert summary["pass_rate"] == 33  # 1 out of 3


class TestFailingQualityGates:
    """Tests for v_failing_quality_gates view."""

    def test_failing_gates_empty(self, sample_data):
        """Test no failing gates initially."""
        conn = sample_data

        failing = get_failing_quality_gates(conn=conn)
        assert len(failing) == 0

    def test_failing_gates_shows_failures(self, sample_data):
        """Test failing gates are returned."""
        conn = sample_data

        add_quality_gate("track", "track-1", "passing_gate", status="passed", conn=conn)
        add_quality_gate("track", "track-1", "failing_gate", status="failed", blocking=True, conn=conn)
        conn.commit()

        failing = get_failing_quality_gates(conn=conn)

        assert len(failing) == 1
        assert failing[0]["gate_name"] == "failing_gate"
        assert failing[0]["blocking"] == 1


# =============================================================================
# ACTIVITY VIEW TESTS
# =============================================================================

class TestRecentActivity:
    """Tests for v_recent_activity view."""

    def test_recent_activity_empty(self, sample_data):
        """Test no activity initially."""
        conn = sample_data

        activity = get_recent_activity(conn=conn)
        assert len(activity) == 0

    def test_recent_activity_with_entries(self, sample_data):
        """Test activity with entries."""
        conn = sample_data

        # Insert activity directly (no CRUD function for this)
        conn.execute(
            """INSERT INTO activity_log
               (roadmap_id, event_type, event_description, occurred_at, entity_type, entity_id, actor)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("test-roadmap", "task_completed", "Task completed", datetime.now(timezone.utc).isoformat(),
             "task", "task-dev-1", "test-agent"),
        )
        conn.commit()

        activity = get_recent_activity(conn=conn)

        assert len(activity) == 1
        assert activity[0]["event_type"] == "task_completed"
        assert activity[0]["entity_name"] == "Development Task 1"


# =============================================================================
# VELOCITY VIEW TESTS
# =============================================================================

class TestVelocityMetrics:
    """Tests for v_velocity_metrics view."""

    def test_velocity_metrics_with_completed_tasks(self, sample_data):
        """Test velocity metrics for completed tasks."""
        conn = sample_data

        # Update tasks with completion times
        now = datetime.now(timezone.utc)
        conn.execute(
            "UPDATE tasks SET started = ?, completed = ?, actual_tokens = ? WHERE id = ?",
            (now.isoformat(), now.isoformat(), 1000, "task-dev-1"),
        )
        conn.execute(
            "UPDATE tasks SET started = ?, completed = ?, actual_tokens = ? WHERE id = ?",
            (now.isoformat(), now.isoformat(), 1500, "task-dev-2"),
        )
        conn.commit()

        metrics = get_velocity_metrics(track_id="track-1", conn=conn)

        assert len(metrics) >= 1
        # Both tasks completed today
        assert metrics[0]["tasks_completed"] == 2
        assert metrics[0]["tokens_used"] == 2500


# =============================================================================
# COMBINED PROGRESS TESTS
# =============================================================================

class TestAllProgress:
    """Tests for combined progress report."""

    def test_get_all_progress(self, sample_data):
        """Test getting complete progress report."""
        conn = sample_data

        progress = get_all_progress("test-roadmap", conn=conn)

        assert "roadmap" in progress
        assert "tracks" in progress
        assert "sprints" in progress

        assert progress["roadmap"]["tasks_total"] == 7
        assert len(progress["tracks"]) == 2
        assert len(progress["sprints"]) == 2


# =============================================================================
# VIEW ACCURACY TESTS
# =============================================================================

class TestViewAccuracy:
    """Tests verifying views compute correct values vs manual calculation."""

    def test_sprint_progress_accuracy(self, sample_data):
        """Verify sprint progress matches manual calculation."""
        conn = sample_data

        # Manual count
        manual_total = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE sprint_id = ?",
            ("sprint-1",),
        ).fetchone()[0]

        manual_completed = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE sprint_id = ? AND status = 'completed'",
            ("sprint-1",),
        ).fetchone()[0]

        # View calculation
        progress = get_sprint_progress("sprint-1", conn=conn)

        assert progress["tasks_total"] == manual_total
        assert progress["tasks_completed"] == manual_completed

    def test_track_progress_accuracy(self, sample_data):
        """Verify track progress matches sum of sprint progress."""
        conn = sample_data

        # Sum from sprints
        sprint_1 = get_sprint_progress("sprint-1", conn=conn)
        sprint_2 = get_sprint_progress("sprint-2", conn=conn)
        expected_total = sprint_1["tasks_total"] + sprint_2["tasks_total"]
        expected_completed = sprint_1["tasks_completed"] + sprint_2["tasks_completed"]

        # Track view
        track = get_track_progress("track-1", conn=conn)

        assert track["tasks_total"] == expected_total
        assert track["tasks_completed"] == expected_completed

    def test_roadmap_progress_accuracy(self, sample_data):
        """Verify roadmap progress matches sum of track progress."""
        conn = sample_data

        # Sum from tracks
        track_1 = get_track_progress("track-1", conn=conn)
        track_2 = get_track_progress("track-2", conn=conn)
        expected_total = track_1["tasks_total"] + track_2["tasks_total"]
        expected_completed = track_1["tasks_completed"] + track_2["tasks_completed"]

        # Roadmap view
        roadmap = get_roadmap_progress("test-roadmap", conn=conn)

        assert roadmap["tasks_total"] == expected_total
        assert roadmap["tasks_completed"] == expected_completed


# =============================================================================
# DB_PATH PARAMETER TESTS
# =============================================================================

class TestDbPathParameter:
    """Tests for using db_path parameter instead of conn."""

    def test_create_views_with_db_path(self, db_path):
        """create_views works with db_path parameter."""
        conn = get_connection(db_path=db_path)
        create_schema(conn=conn)
        conn.commit()

        # Drop and recreate with db_path
        drop_views(conn=conn)
        create_views(db_path=db_path)

        assert view_exists("v_sprint_progress", conn=conn)

    def test_drop_views_with_db_path(self, db_path):
        """drop_views works with db_path parameter."""
        conn = get_connection(db_path=db_path)
        create_schema(conn=conn)
        create_views(conn=conn)
        conn.commit()

        drop_views(db_path=db_path)

        assert not view_exists("v_sprint_progress", conn=conn)

    def test_view_exists_with_db_path(self, conn, db_path):
        """view_exists works with db_path parameter."""
        assert view_exists("v_sprint_progress", db_path=db_path)
        assert not view_exists("nonexistent_view", db_path=db_path)

    def test_get_view_names_with_db_path(self, conn, db_path):
        """get_view_names works with db_path parameter."""
        names = get_view_names(db_path=db_path)
        assert "v_sprint_progress" in names

    def test_get_sprint_progress_with_db_path(self, sample_data, db_path):
        """get_sprint_progress works with db_path parameter."""
        progress = get_sprint_progress("sprint-1", db_path=db_path)
        assert progress is not None
        assert "tasks_total" in progress

    def test_get_track_progress_with_db_path(self, sample_data, db_path):
        """get_track_progress works with db_path parameter."""
        progress = get_track_progress("track-1", db_path=db_path)
        assert progress is not None
        assert "sprints_total" in progress

    def test_get_roadmap_progress_with_db_path(self, sample_data, db_path):
        """get_roadmap_progress works with db_path parameter."""
        progress = get_roadmap_progress("test-roadmap", db_path=db_path)
        assert progress is not None
        assert "tracks_total" in progress

    def test_get_blocked_entities_with_db_path(self, sample_data, db_path):
        """get_blocked_entities works with db_path parameter."""
        blocked = get_blocked_entities(db_path=db_path)
        assert isinstance(blocked, list)

    def test_get_unblocked_tasks_with_db_path(self, sample_data, db_path):
        """get_unblocked_tasks works with db_path parameter."""
        tasks = get_unblocked_tasks(db_path=db_path)
        assert isinstance(tasks, list)

    def test_get_dependency_chain_with_db_path(self, sample_data, db_path):
        """get_dependency_chain works with db_path parameter."""
        chain = get_dependency_chain("task", "task-1", db_path=db_path)
        assert isinstance(chain, list)

    def test_get_quality_gate_summary_with_db_path(self, sample_data, db_path):
        """get_quality_gate_summary works with db_path parameter."""
        summary = get_quality_gate_summary("track", "track-1", db_path=db_path)
        # Returns None if no quality gates exist
        assert summary is None or isinstance(summary, dict)

    def test_get_failing_quality_gates_with_db_path(self, sample_data, db_path):
        """get_failing_quality_gates works with db_path parameter."""
        failing = get_failing_quality_gates(db_path=db_path)
        assert isinstance(failing, list)

    def test_get_recent_activity_with_db_path(self, sample_data, db_path):
        """get_recent_activity works with db_path parameter."""
        activity = get_recent_activity(db_path=db_path)
        assert isinstance(activity, list)

    def test_get_velocity_metrics_with_db_path(self, sample_data, db_path):
        """get_velocity_metrics works with db_path parameter."""
        metrics = get_velocity_metrics(db_path=db_path)
        assert isinstance(metrics, list)

    def test_get_all_progress_with_db_path(self, sample_data, db_path):
        """get_all_progress works with db_path parameter."""
        progress = get_all_progress("test-roadmap", db_path=db_path)
        assert isinstance(progress, dict)


class TestEdgeCases:
    """Test edge cases and additional filter branches."""

    def test_get_track_progress_nonexistent(self, conn):
        """get_track_progress returns None for nonexistent track."""
        result = get_track_progress("nonexistent-track", conn=conn)
        assert result is None

    def test_get_roadmap_progress_nonexistent(self, conn):
        """get_roadmap_progress returns None for nonexistent roadmap."""
        result = get_roadmap_progress("nonexistent-roadmap", conn=conn)
        assert result is None

    def test_get_failing_quality_gates_with_owner_type_and_id(self, sample_data, conn):
        """get_failing_quality_gates filters by owner_type and owner_id."""
        result = get_failing_quality_gates(
            owner_type="track", owner_id="track-1", conn=conn
        )
        assert isinstance(result, list)

    def test_get_failing_quality_gates_with_owner_type_only(self, sample_data, conn):
        """get_failing_quality_gates filters by owner_type only."""
        result = get_failing_quality_gates(owner_type="track", conn=conn)
        assert isinstance(result, list)

    def test_get_recent_activity_with_roadmap_id(self, sample_data, conn):
        """get_recent_activity filters by roadmap_id."""
        result = get_recent_activity(roadmap_id="test-roadmap", conn=conn)
        assert isinstance(result, list)
