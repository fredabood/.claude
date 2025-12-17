"""
Tests for SQLite triggers.

Tests verify that triggers correctly handle:
- Timestamp auto-setting
- Blocked flag synchronization
- Auto-completion cascades
- Summary table synchronization
- Activity logging
- Validation constraints
"""

import pytest
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import os

from .connection import get_connection, close_connection
from .schema import create_schema
from .views import create_views
from .triggers import (
    TRIGGER_DEFINITIONS,
    TRIGGER_ORDER,
    create_triggers,
    drop_triggers,
    trigger_exists,
    get_trigger_names,
    get_triggers_by_category,
    validate_triggers,
    disable_triggers_for_bulk_operations,
    enable_triggers_for_bulk_operations,
    rebuild_summary_tables,
)
from .crud import (
    create_roadmap,
    create_track,
    create_sprint,
    create_task,
    update_task,
    update_sprint,
    update_track,
    add_blocker,
    remove_blocker,
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
    """Create a connection with schema, views, and triggers initialized."""
    connection = get_connection(db_path=db_path)
    create_schema(conn=connection)
    create_views(conn=connection)
    create_triggers(conn=connection)
    connection.commit()
    return connection


@pytest.fixture
def sample_data(conn):
    """Create sample roadmap with tracks, sprints, and tasks."""
    now = datetime.now(timezone.utc)

    create_roadmap(
        id="test-roadmap",
        name="Test Roadmap",
        version="1.0.0",
        status="not_started",
        created=now,
        conn=conn,
    )

    create_track(
        id="track-1",
        roadmap_id="test-roadmap",
        name="Track 1",
        status="not_started",
        created=now,
        conn=conn,
    )

    create_sprint(
        id="sprint-1",
        track_id="track-1",
        roadmap_id="test-roadmap",
        name="Sprint 1",
        status="not_started",
        created=now,
        conn=conn,
    )

    for i in range(3):
        create_task(
            id=f"task-{i+1}",
            sprint_id="sprint-1",
            track_id="track-1",
            roadmap_id="test-roadmap",
            task_type="development",
            title=f"Task {i+1}",
            status="not_started",
            created=now,
            conn=conn,
        )

    conn.commit()
    return conn


# =============================================================================
# TRIGGER MANAGEMENT TESTS
# =============================================================================

class TestTriggerManagement:
    """Tests for trigger creation and management."""

    def test_create_all_triggers(self, db_path):
        """Test creating all 40 triggers."""
        conn = get_connection(db_path=db_path)
        create_schema(conn=conn)
        create_views(conn=conn)

        count = create_triggers(conn=conn)
        conn.commit()

        assert count == 40
        assert len(get_trigger_names(conn=conn)) == 40

    def test_create_triggers_by_category(self, db_path):
        """Test creating triggers by category."""
        conn = get_connection(db_path=db_path)
        create_schema(conn=conn)
        create_views(conn=conn)

        count = create_triggers(conn=conn, categories=["timestamp"])
        conn.commit()

        assert count == 9
        trigger_names = get_trigger_names(conn=conn)
        assert "trg_task_started" in trigger_names
        assert "trg_activity_task_created" not in trigger_names

    def test_drop_triggers(self, conn):
        """Test dropping all triggers."""
        assert len(get_trigger_names(conn=conn)) == 40

        drop_triggers(conn=conn)
        conn.commit()

        assert len(get_trigger_names(conn=conn)) == 0

    def test_trigger_exists(self, conn):
        """Test checking if a trigger exists."""
        assert trigger_exists("trg_task_started", conn=conn)
        assert trigger_exists("trg_task_completed", conn=conn)
        assert not trigger_exists("nonexistent_trigger", conn=conn)

    def test_validate_triggers(self, conn):
        """Test trigger validation."""
        result = validate_triggers(conn=conn)

        assert result["valid"] is True
        assert result["expected"] == 40
        assert result["found"] == 40
        assert result["missing"] == []

    def test_validate_triggers_missing(self, conn):
        """Test trigger validation with missing triggers."""
        conn.execute("DROP TRIGGER trg_task_started")
        conn.commit()

        result = validate_triggers(conn=conn)

        assert result["valid"] is False
        assert "trg_task_started" in result["missing"]

    def test_get_triggers_by_category(self):
        """Test getting triggers by category."""
        timestamp_triggers = get_triggers_by_category("timestamp")
        assert len(timestamp_triggers) == 9

        blocked_triggers = get_triggers_by_category("blocked_flag")
        assert len(blocked_triggers) == 6

        invalid = get_triggers_by_category("invalid_category")
        assert invalid == []

    def test_trigger_definitions_complete(self):
        """Test that all triggers in ORDER are in DEFINITIONS."""
        for trigger_name in TRIGGER_ORDER:
            assert trigger_name in TRIGGER_DEFINITIONS


# =============================================================================
# TIMESTAMP TRIGGER TESTS
# =============================================================================

class TestTimestampTriggers:
    """Tests for timestamp auto-setting triggers."""

    def test_task_started_auto_set(self, sample_data):
        """Test task started timestamp is auto-set."""
        conn = sample_data

        # Verify initially null
        task = conn.execute("SELECT started FROM tasks WHERE id = 'task-1'").fetchone()
        assert task["started"] is None

        # Update status to in_progress
        update_task("task-1", status="in_progress", conn=conn)
        conn.commit()

        # Verify started is now set
        task = conn.execute("SELECT started FROM tasks WHERE id = 'task-1'").fetchone()
        assert task["started"] is not None

    def test_task_completed_auto_set(self, sample_data):
        """Test task completed timestamp is auto-set."""
        conn = sample_data

        # Start then complete the task
        update_task("task-1", status="in_progress", conn=conn)
        update_task("task-1", status="completed", conn=conn)
        conn.commit()

        task = conn.execute("SELECT completed FROM tasks WHERE id = 'task-1'").fetchone()
        assert task["completed"] is not None

    def test_sprint_started_auto_set(self, sample_data):
        """Test sprint started timestamp is auto-set."""
        conn = sample_data

        update_sprint("sprint-1", status="in_progress", conn=conn)
        conn.commit()

        sprint = conn.execute("SELECT started FROM sprints WHERE id = 'sprint-1'").fetchone()
        assert sprint["started"] is not None

    def test_track_started_auto_set(self, sample_data):
        """Test track started timestamp is auto-set."""
        conn = sample_data

        update_track("track-1", status="in_progress", conn=conn)
        conn.commit()

        track = conn.execute("SELECT started FROM tracks WHERE id = 'track-1'").fetchone()
        assert track["started"] is not None

    def test_doesnt_overwrite_existing_started(self, sample_data):
        """Test that auto-set doesn't overwrite existing timestamp."""
        conn = sample_data

        # Set a specific started time
        specific_time = "2024-01-01T00:00:00"
        conn.execute(
            "UPDATE tasks SET started = ?, status = 'in_progress' WHERE id = 'task-1'",
            (specific_time,),
        )
        conn.commit()

        # The trigger should not have overwritten it
        task = conn.execute("SELECT started FROM tasks WHERE id = 'task-1'").fetchone()
        assert task["started"] == specific_time


# =============================================================================
# BLOCKED FLAG TRIGGER TESTS
# =============================================================================

class TestBlockedFlagTriggers:
    """Tests for blocked flag synchronization triggers."""

    def test_task_blocked_on_blocker_insert(self, sample_data):
        """Test task is marked blocked when blocker added."""
        conn = sample_data

        # Initially not blocked
        task = conn.execute("SELECT blocked FROM tasks WHERE id = 'task-2'").fetchone()
        assert task["blocked"] == 0

        # Add blocker
        add_blocker("task", "task-1", "task", "task-2", conn=conn)
        conn.commit()

        # Now blocked
        task = conn.execute("SELECT blocked FROM tasks WHERE id = 'task-2'").fetchone()
        assert task["blocked"] == 1

    def test_task_unblocked_on_blocker_delete(self, sample_data):
        """Test task is unblocked when blocker removed."""
        conn = sample_data

        add_blocker("task", "task-1", "task", "task-2", conn=conn)
        conn.commit()

        assert conn.execute("SELECT blocked FROM tasks WHERE id = 'task-2'").fetchone()["blocked"] == 1

        remove_blocker("task", "task-1", "task", "task-2", conn=conn)
        conn.commit()

        assert conn.execute("SELECT blocked FROM tasks WHERE id = 'task-2'").fetchone()["blocked"] == 0

    def test_sprint_blocked_flag(self, sample_data):
        """Test sprint blocked flag synchronization."""
        conn = sample_data

        # Add sprint blocker
        add_blocker("task", "task-1", "sprint", "sprint-1", conn=conn)
        conn.commit()

        sprint = conn.execute("SELECT blocked FROM sprints WHERE id = 'sprint-1'").fetchone()
        assert sprint["blocked"] == 1


# =============================================================================
# AUTO-COMPLETION TRIGGER TESTS
# =============================================================================

class TestAutoCompletionTriggers:
    """Tests for auto-completion cascade triggers."""

    def test_clear_blocker_on_task_complete(self, sample_data):
        """Test blockers are cleared when task completes."""
        conn = sample_data

        # Set up blocker
        add_blocker("task", "task-1", "task", "task-2", conn=conn)
        conn.commit()

        assert conn.execute("SELECT blocked FROM tasks WHERE id = 'task-2'").fetchone()["blocked"] == 1

        # Complete the blocker
        update_task("task-1", status="in_progress", conn=conn)
        update_task("task-1", status="completed", conn=conn)
        conn.commit()

        # Blocking relationship should be removed
        count = conn.execute(
            "SELECT COUNT(*) FROM entity_blocked_by WHERE blocker_id = 'task-1'"
        ).fetchone()[0]
        assert count == 0

        # task-2 should be unblocked
        assert conn.execute("SELECT blocked FROM tasks WHERE id = 'task-2'").fetchone()["blocked"] == 0

    def test_auto_start_sprint_on_task_start(self, sample_data):
        """Test sprint auto-starts when first task starts."""
        conn = sample_data

        # Sprint should be not_started
        sprint = conn.execute("SELECT status, started FROM sprints WHERE id = 'sprint-1'").fetchone()
        assert sprint["status"] == "not_started"
        assert sprint["started"] is None

        # Start a task
        update_task("task-1", status="in_progress", conn=conn)
        conn.commit()

        # Sprint should now be in_progress
        sprint = conn.execute("SELECT status, started FROM sprints WHERE id = 'sprint-1'").fetchone()
        assert sprint["status"] == "in_progress"
        assert sprint["started"] is not None

    def test_auto_start_track_on_sprint_start(self, sample_data):
        """Test track auto-starts when first sprint starts."""
        conn = sample_data

        # Track should be not_started
        track = conn.execute("SELECT status, started FROM tracks WHERE id = 'track-1'").fetchone()
        assert track["status"] == "not_started"

        # Start a sprint (which will happen via task start cascade)
        update_task("task-1", status="in_progress", conn=conn)
        conn.commit()

        # Track should now be in_progress
        track = conn.execute("SELECT status, started FROM tracks WHERE id = 'track-1'").fetchone()
        assert track["status"] == "in_progress"
        assert track["started"] is not None


# =============================================================================
# SUMMARY TABLE TRIGGER TESTS
# =============================================================================

class TestSummaryTableTriggers:
    """Tests for summary table synchronization triggers."""

    def test_task_summary_created(self, sample_data):
        """Test task summary is created on task insert."""
        conn = sample_data

        # Task summaries should exist
        count = conn.execute(
            "SELECT COUNT(*) FROM task_summaries WHERE sprint_id = 'sprint-1'"
        ).fetchone()[0]
        assert count == 3

    def test_task_summary_updated(self, sample_data):
        """Test task summary is updated on task update."""
        conn = sample_data

        update_task("task-1", status="in_progress", conn=conn)
        conn.commit()

        summary = conn.execute(
            "SELECT status FROM task_summaries WHERE task_id = 'task-1'"
        ).fetchone()
        assert summary["status"] == "in_progress"

    def test_sprint_summary_created(self, sample_data):
        """Test sprint summary is created on sprint insert."""
        conn = sample_data

        summary = conn.execute(
            "SELECT * FROM sprint_summaries WHERE sprint_id = 'sprint-1'"
        ).fetchone()
        assert summary is not None
        assert summary["name"] == "Sprint 1"
        assert summary["tasks_count"] == 3

    def test_sprint_summary_task_count_updated(self, sample_data):
        """Test sprint summary task count updates."""
        conn = sample_data
        now = datetime.now(timezone.utc)

        # Add a new task
        create_task(
            id="task-4",
            sprint_id="sprint-1",
            track_id="track-1",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Task 4",
            status="not_started",
            created=now,
            conn=conn,
        )
        conn.commit()

        summary = conn.execute(
            "SELECT tasks_count FROM sprint_summaries WHERE sprint_id = 'sprint-1'"
        ).fetchone()
        assert summary["tasks_count"] == 4

    def test_track_summary_created(self, sample_data):
        """Test track summary is created on track insert."""
        conn = sample_data

        summary = conn.execute(
            "SELECT * FROM track_summaries WHERE track_id = 'track-1'"
        ).fetchone()
        assert summary is not None
        assert summary["name"] == "Track 1"


# =============================================================================
# ACTIVITY LOG TRIGGER TESTS
# =============================================================================

class TestActivityLogTriggers:
    """Tests for activity logging triggers."""

    def test_task_created_logged(self, sample_data):
        """Test task creation is logged."""
        conn = sample_data

        logs = conn.execute(
            "SELECT * FROM activity_log WHERE event_type = 'task_created'"
        ).fetchall()
        assert len(logs) == 3  # 3 tasks created in fixture

    def test_task_status_change_logged(self, sample_data):
        """Test task status change is logged."""
        conn = sample_data

        update_task("task-1", status="in_progress", conn=conn)
        conn.commit()

        logs = conn.execute(
            """SELECT * FROM activity_log
               WHERE event_type = 'task_status_change' AND entity_id = 'task-1'"""
        ).fetchall()
        assert len(logs) == 1
        assert "not_started to in_progress" in logs[0]["event_description"]

    def test_sprint_status_change_logged(self, sample_data):
        """Test sprint status change is logged."""
        conn = sample_data

        update_task("task-1", status="in_progress", conn=conn)
        conn.commit()

        logs = conn.execute(
            "SELECT * FROM activity_log WHERE event_type = 'sprint_status_change'"
        ).fetchall()
        assert len(logs) == 1

    def test_track_status_change_logged(self, sample_data):
        """Test track status change is logged."""
        conn = sample_data

        update_task("task-1", status="in_progress", conn=conn)
        conn.commit()

        logs = conn.execute(
            "SELECT * FROM activity_log WHERE event_type = 'track_status_change'"
        ).fetchall()
        assert len(logs) == 1


# =============================================================================
# VALIDATION TRIGGER TESTS
# =============================================================================

class TestValidationTriggers:
    """Tests for validation constraint triggers."""

    def test_prevent_complete_blocked_task(self, sample_data):
        """Test cannot complete a task with unresolved blockers."""
        conn = sample_data

        # Set up task-2 blocked by task-1
        add_blocker("task", "task-1", "task", "task-2", conn=conn)
        conn.commit()

        # Try to complete task-2 (blocked)
        with pytest.raises(sqlite3.IntegrityError, match="unresolved blockers"):
            update_task("task-2", status="completed", conn=conn)

    def test_can_complete_unblocked_task(self, sample_data):
        """Test can complete a task without blockers."""
        conn = sample_data

        update_task("task-1", status="in_progress", conn=conn)
        update_task("task-1", status="completed", conn=conn)
        conn.commit()

        task = conn.execute("SELECT status FROM tasks WHERE id = 'task-1'").fetchone()
        assert task["status"] == "completed"

    def test_prevent_complete_sprint_incomplete_tasks(self, sample_data):
        """Test cannot complete sprint with incomplete tasks."""
        conn = sample_data

        # Start the sprint
        update_sprint("sprint-1", status="in_progress", conn=conn)
        conn.commit()

        # Try to complete sprint (tasks are incomplete)
        with pytest.raises(sqlite3.IntegrityError, match="incomplete tasks"):
            update_sprint("sprint-1", status="completed", conn=conn)

    def test_can_complete_sprint_all_tasks_done(self, sample_data):
        """Test can complete sprint when all tasks are done."""
        conn = sample_data

        # Complete all tasks
        for i in range(1, 4):
            update_task(f"task-{i}", status="in_progress", conn=conn)
            update_task(f"task-{i}", status="completed", conn=conn)

        # Now sprint can be completed
        update_sprint("sprint-1", status="completed", conn=conn)
        conn.commit()

        sprint = conn.execute("SELECT status FROM sprints WHERE id = 'sprint-1'").fetchone()
        assert sprint["status"] == "completed"


# =============================================================================
# BULK OPERATION TESTS
# =============================================================================

class TestBulkOperations:
    """Tests for bulk operation helper functions."""

    def test_disable_triggers_for_bulk(self, conn):
        """Test disabling triggers for bulk operations."""
        initial_count = len(get_trigger_names(conn=conn))
        assert initial_count == 40

        disabled = disable_triggers_for_bulk_operations(conn=conn)
        conn.commit()

        # Should disable activity_log (6) and summary_tables (11)
        assert disabled == 17

        remaining = len(get_trigger_names(conn=conn))
        assert remaining == 40 - 17

    def test_enable_triggers_for_bulk(self, conn):
        """Test re-enabling triggers after bulk operations."""
        disable_triggers_for_bulk_operations(conn=conn)
        conn.commit()

        enabled = enable_triggers_for_bulk_operations(conn=conn)
        conn.commit()

        assert enabled == 17
        assert len(get_trigger_names(conn=conn)) == 40

    def test_rebuild_summary_tables(self, sample_data):
        """Test rebuilding summary tables from source data."""
        conn = sample_data

        # Clear summaries
        conn.execute("DELETE FROM task_summaries")
        conn.execute("DELETE FROM sprint_summaries")
        conn.execute("DELETE FROM track_summaries")
        conn.commit()

        # Verify empty
        assert conn.execute("SELECT COUNT(*) FROM task_summaries").fetchone()[0] == 0

        # Rebuild
        rebuild_summary_tables(conn=conn)
        conn.commit()

        # Verify rebuilt
        assert conn.execute("SELECT COUNT(*) FROM task_summaries").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM sprint_summaries").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM track_summaries").fetchone()[0] == 1


# =============================================================================
# CASCADE BEHAVIOR TESTS
# =============================================================================

class TestCascadeBehavior:
    """Tests for complex cascade scenarios."""

    def test_task_complete_cascade(self, sample_data):
        """Test full cascade when task completes."""
        conn = sample_data

        # Set up: task-2 blocked by task-1
        add_blocker("task", "task-1", "task", "task-2", conn=conn)
        conn.commit()

        # Complete task-1
        update_task("task-1", status="in_progress", conn=conn)
        update_task("task-1", status="completed", conn=conn)
        conn.commit()

        # Verify cascade effects:
        # 1. task-1 has completed timestamp
        task1 = conn.execute("SELECT completed FROM tasks WHERE id = 'task-1'").fetchone()
        assert task1["completed"] is not None

        # 2. task-2 is unblocked
        task2 = conn.execute("SELECT blocked FROM tasks WHERE id = 'task-2'").fetchone()
        assert task2["blocked"] == 0

        # 3. Activity was logged
        logs = conn.execute(
            "SELECT * FROM activity_log WHERE event_type = 'task_status_change' AND entity_id = 'task-1'"
        ).fetchall()
        assert len(logs) == 2  # not_started->in_progress, in_progress->completed

        # 4. Summary was updated
        summary = conn.execute(
            "SELECT status FROM task_summaries WHERE task_id = 'task-1'"
        ).fetchone()
        assert summary["status"] == "completed"

    def test_sprint_completion_cascade(self, sample_data):
        """Test full cascade when sprint completes."""
        conn = sample_data

        # Complete all tasks
        for i in range(1, 4):
            update_task(f"task-{i}", status="in_progress", conn=conn)
            update_task(f"task-{i}", status="completed", conn=conn)

        # Complete sprint
        update_sprint("sprint-1", status="completed", conn=conn)
        conn.commit()

        # Verify cascade effects:
        # 1. Sprint has completed timestamp
        sprint = conn.execute(
            "SELECT completed, status FROM sprints WHERE id = 'sprint-1'"
        ).fetchone()
        assert sprint["completed"] is not None
        assert sprint["status"] == "completed"

        # 2. Summary updated
        summary = conn.execute(
            "SELECT status FROM sprint_summaries WHERE sprint_id = 'sprint-1'"
        ).fetchone()
        assert summary["status"] == "completed"

        # 3. Activity logged
        logs = conn.execute(
            "SELECT * FROM activity_log WHERE event_type = 'sprint_status_change'"
        ).fetchall()
        assert len(logs) >= 1
