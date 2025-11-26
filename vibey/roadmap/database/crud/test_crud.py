"""
Unit tests for CRUD operations.

Tests create, read, update, delete operations for:
- Roadmaps
- Tracks
- Sprints
- Tasks
"""

import sqlite3
import tempfile
import pytest
from pathlib import Path
from datetime import datetime, timezone

from vibey.roadmap.database.connection import (
    get_connection,
    close_all_connections,
    DEFAULT_VIBEY_DIR,
)
from vibey.roadmap.database.schema import create_schema

from vibey.roadmap.database.crud import (
    # Roadmap
    create_roadmap,
    get_roadmap,
    update_roadmap,
    delete_roadmap,
    list_roadmaps,
    roadmap_exists,
    count_roadmaps,
    # Track
    create_track,
    get_track,
    update_track,
    delete_track,
    list_tracks_by_roadmap,
    track_exists,
    count_tracks,
    # Sprint
    create_sprint,
    get_sprint,
    update_sprint,
    delete_sprint,
    list_sprints_by_track,
    list_sprints_by_roadmap,
    sprint_exists,
    count_sprints,
    # Task
    create_task,
    get_task,
    update_task,
    delete_task,
    list_tasks_by_sprint,
    list_tasks_by_track,
    list_tasks_by_roadmap,
    task_exists,
    count_tasks,
    get_blocked_tasks,
)
from vibey.roadmap.database.crud.task import list_tasks_by_roadmap


@pytest.fixture
def temp_db_dir():
    """Create a temporary directory for test databases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vibey_dir = Path(tmpdir) / DEFAULT_VIBEY_DIR
        vibey_dir.mkdir()
        yield Path(tmpdir)
        close_all_connections()


@pytest.fixture
def db_with_schema(temp_db_dir):
    """Create a database with the schema initialized."""
    db_path = temp_db_dir / DEFAULT_VIBEY_DIR / "roadmap.db"
    conn = get_connection(db_path=db_path)
    create_schema(conn)
    return conn, db_path


@pytest.fixture
def sample_roadmap(db_with_schema):
    """Create a sample roadmap."""
    conn, db_path = db_with_schema
    now = datetime.now(timezone.utc)
    create_roadmap(
        id="test-roadmap",
        name="Test Roadmap",
        version="1.0.0",
        status="in_progress",
        created=now,
        started=now,
        conn=conn,
    )
    return conn, db_path


@pytest.fixture
def sample_track(sample_roadmap):
    """Create a sample track."""
    conn, db_path = sample_roadmap
    now = datetime.now(timezone.utc)
    create_track(
        id="test-track",
        roadmap_id="test-roadmap",
        name="Test Track",
        status="not_started",
        created=now,
        priority="high",
        conn=conn,
    )
    return conn, db_path


@pytest.fixture
def sample_sprint(sample_track):
    """Create a sample sprint."""
    conn, db_path = sample_track
    now = datetime.now(timezone.utc)
    create_sprint(
        id="test-track-0",
        track_id="test-track",
        roadmap_id="test-roadmap",
        name="Sprint 0",
        status="not_started",
        created=now,
        conn=conn,
    )
    return conn, db_path


# =============================================================================
# ROADMAP TESTS
# =============================================================================

class TestRoadmapCRUD:
    """Tests for roadmap CRUD operations."""

    def test_create_roadmap(self, db_with_schema):
        """create_roadmap creates a new roadmap."""
        conn, db_path = db_with_schema
        now = datetime.now(timezone.utc)

        result = create_roadmap(
            id="my-roadmap",
            name="My Roadmap",
            version="1.0.0",
            status="not_started",
            created=now,
            conn=conn,
        )

        assert result == "my-roadmap"
        assert roadmap_exists("my-roadmap", conn=conn)

    def test_create_roadmap_with_all_fields(self, db_with_schema):
        """create_roadmap with all optional fields."""
        conn, db_path = db_with_schema
        now = datetime.now(timezone.utc)

        create_roadmap(
            id="full-roadmap",
            name="Full Roadmap",
            version="2.0.0",
            status="in_progress",
            created=now,
            started=now,
            target_completion=now,
            blocked=True,
            version_strategy={"major_on": "milestone"},
            metadata={"author": "test"},
            conn=conn,
        )

        roadmap = get_roadmap("full-roadmap", conn=conn)
        assert roadmap["blocked"] is True
        assert roadmap["version_strategy"] == {"major_on": "milestone"}
        assert roadmap["metadata"] == {"author": "test"}

    def test_get_roadmap(self, sample_roadmap):
        """get_roadmap returns roadmap data."""
        conn, _ = sample_roadmap
        roadmap = get_roadmap("test-roadmap", conn=conn)

        assert roadmap is not None
        assert roadmap["id"] == "test-roadmap"
        assert roadmap["name"] == "Test Roadmap"
        assert roadmap["status"] == "in_progress"

    def test_get_roadmap_not_found(self, db_with_schema):
        """get_roadmap returns None for non-existent roadmap."""
        conn, _ = db_with_schema
        assert get_roadmap("nonexistent", conn=conn) is None

    def test_update_roadmap(self, sample_roadmap):
        """update_roadmap updates roadmap fields."""
        conn, _ = sample_roadmap

        result = update_roadmap(
            "test-roadmap",
            name="Updated Name",
            status="completed",
            conn=conn,
        )

        assert result is True
        roadmap = get_roadmap("test-roadmap", conn=conn)
        assert roadmap["name"] == "Updated Name"
        assert roadmap["status"] == "completed"

    def test_update_roadmap_not_found(self, db_with_schema):
        """update_roadmap returns False for non-existent roadmap."""
        conn, _ = db_with_schema
        result = update_roadmap("nonexistent", name="test", conn=conn)
        assert result is False

    def test_update_roadmap_no_fields(self, sample_roadmap):
        """update_roadmap raises ValueError with no fields."""
        conn, _ = sample_roadmap
        with pytest.raises(ValueError, match="No update fields"):
            update_roadmap("test-roadmap", conn=conn)

    def test_delete_roadmap(self, sample_roadmap):
        """delete_roadmap removes roadmap."""
        conn, _ = sample_roadmap

        result = delete_roadmap("test-roadmap", conn=conn)

        assert result is True
        assert not roadmap_exists("test-roadmap", conn=conn)

    def test_delete_roadmap_cascades_to_tracks(self, sample_track):
        """delete_roadmap cascades to tracks."""
        conn, _ = sample_track

        delete_roadmap("test-roadmap", conn=conn)

        assert not track_exists("test-track", conn=conn)

    def test_list_roadmaps(self, db_with_schema):
        """list_roadmaps returns all roadmaps."""
        conn, _ = db_with_schema
        now = datetime.now(timezone.utc)

        create_roadmap(id="r1", name="R1", version="1.0", status="not_started", created=now, conn=conn)
        create_roadmap(id="r2", name="R2", version="1.0", status="in_progress", created=now, conn=conn)

        roadmaps = list_roadmaps(conn=conn)
        assert len(roadmaps) == 2

    def test_list_roadmaps_filter_by_status(self, db_with_schema):
        """list_roadmaps filters by status."""
        conn, _ = db_with_schema
        now = datetime.now(timezone.utc)

        create_roadmap(id="r1", name="R1", version="1.0", status="not_started", created=now, conn=conn)
        create_roadmap(id="r2", name="R2", version="1.0", status="in_progress", created=now, conn=conn)

        roadmaps = list_roadmaps(status="in_progress", conn=conn)
        assert len(roadmaps) == 1
        assert roadmaps[0]["id"] == "r2"

    def test_count_roadmaps(self, db_with_schema):
        """count_roadmaps returns correct count."""
        conn, _ = db_with_schema
        now = datetime.now(timezone.utc)

        create_roadmap(id="r1", name="R1", version="1.0", status="not_started", created=now, conn=conn)
        create_roadmap(id="r2", name="R2", version="1.0", status="in_progress", created=now, conn=conn)

        assert count_roadmaps(conn=conn) == 2
        assert count_roadmaps(status="in_progress", conn=conn) == 1


# =============================================================================
# TRACK TESTS
# =============================================================================

class TestTrackCRUD:
    """Tests for track CRUD operations."""

    def test_create_track(self, sample_roadmap):
        """create_track creates a new track."""
        conn, _ = sample_roadmap
        now = datetime.now(timezone.utc)

        result = create_track(
            id="new-track",
            roadmap_id="test-roadmap",
            name="New Track",
            status="not_started",
            created=now,
            conn=conn,
        )

        assert result == "new-track"
        assert track_exists("new-track", conn=conn)

    def test_create_track_invalid_roadmap(self, db_with_schema):
        """create_track fails for non-existent roadmap."""
        conn, _ = db_with_schema
        now = datetime.now(timezone.utc)

        with pytest.raises(sqlite3.IntegrityError):
            create_track(
                id="bad-track",
                roadmap_id="nonexistent",
                name="Bad Track",
                status="not_started",
                created=now,
                conn=conn,
            )

    def test_get_track(self, sample_track):
        """get_track returns track data."""
        conn, _ = sample_track
        track = get_track("test-track", conn=conn)

        assert track is not None
        assert track["id"] == "test-track"
        assert track["roadmap_id"] == "test-roadmap"
        assert track["priority"] == "high"

    def test_update_track(self, sample_track):
        """update_track updates track fields."""
        conn, _ = sample_track

        result = update_track(
            "test-track",
            name="Updated Track",
            priority="critical",
            conn=conn,
        )

        assert result is True
        track = get_track("test-track", conn=conn)
        assert track["name"] == "Updated Track"
        assert track["priority"] == "critical"

    def test_delete_track(self, sample_track):
        """delete_track removes track."""
        conn, _ = sample_track

        result = delete_track("test-track", conn=conn)

        assert result is True
        assert not track_exists("test-track", conn=conn)

    def test_list_tracks_by_roadmap(self, sample_roadmap):
        """list_tracks_by_roadmap returns tracks for a roadmap."""
        conn, _ = sample_roadmap
        now = datetime.now(timezone.utc)

        create_track(id="t1", roadmap_id="test-roadmap", name="T1", status="not_started", created=now, conn=conn)
        create_track(id="t2", roadmap_id="test-roadmap", name="T2", status="in_progress", created=now, conn=conn)

        tracks = list_tracks_by_roadmap("test-roadmap", conn=conn)
        assert len(tracks) == 2

    def test_count_tracks(self, sample_track):
        """count_tracks returns correct count."""
        conn, _ = sample_track
        assert count_tracks(roadmap_id="test-roadmap", conn=conn) == 1


# =============================================================================
# SPRINT TESTS
# =============================================================================

class TestSprintCRUD:
    """Tests for sprint CRUD operations."""

    def test_create_sprint(self, sample_track):
        """create_sprint creates a new sprint."""
        conn, _ = sample_track
        now = datetime.now(timezone.utc)

        result = create_sprint(
            id="test-track-1",
            track_id="test-track",
            roadmap_id="test-roadmap",
            name="Sprint 1",
            status="not_started",
            created=now,
            conn=conn,
        )

        assert result == "test-track-1"
        assert sprint_exists("test-track-1", conn=conn)

    def test_get_sprint(self, sample_sprint):
        """get_sprint returns sprint data."""
        conn, _ = sample_sprint
        sprint = get_sprint("test-track-0", conn=conn)

        assert sprint is not None
        assert sprint["id"] == "test-track-0"
        assert sprint["track_id"] == "test-track"
        assert sprint["name"] == "Sprint 0"

    def test_update_sprint(self, sample_sprint):
        """update_sprint updates sprint fields."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        result = update_sprint(
            "test-track-0",
            name="Updated Sprint",
            status="in_progress",
            started=now,
            conn=conn,
        )

        assert result is True
        sprint = get_sprint("test-track-0", conn=conn)
        assert sprint["name"] == "Updated Sprint"
        assert sprint["status"] == "in_progress"

    def test_delete_sprint(self, sample_sprint):
        """delete_sprint removes sprint."""
        conn, _ = sample_sprint

        result = delete_sprint("test-track-0", conn=conn)

        assert result is True
        assert not sprint_exists("test-track-0", conn=conn)

    def test_list_sprints_by_track(self, sample_track):
        """list_sprints_by_track returns sprints for a track."""
        conn, _ = sample_track
        now = datetime.now(timezone.utc)

        create_sprint(id="test-track-0", track_id="test-track", roadmap_id="test-roadmap",
                     name="S0", status="not_started", created=now, conn=conn)
        create_sprint(id="test-track-1", track_id="test-track", roadmap_id="test-roadmap",
                     name="S1", status="in_progress", created=now, conn=conn)

        sprints = list_sprints_by_track("test-track", conn=conn)
        assert len(sprints) == 2

    def test_list_sprints_by_roadmap(self, sample_sprint):
        """list_sprints_by_roadmap returns sprints for a roadmap."""
        conn, _ = sample_sprint
        sprints = list_sprints_by_roadmap("test-roadmap", conn=conn)
        assert len(sprints) == 1

    def test_count_sprints(self, sample_sprint):
        """count_sprints returns correct count."""
        conn, _ = sample_sprint
        assert count_sprints(track_id="test-track", conn=conn) == 1


# =============================================================================
# TASK TESTS
# =============================================================================

class TestTaskCRUD:
    """Tests for task CRUD operations."""

    def test_create_task(self, sample_sprint):
        """create_task creates a new task."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        result = create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Test Task",
            status="not_started",
            created=now,
            conn=conn,
        )

        assert result == "test-track-0-task-001"
        assert task_exists("test-track-0-task-001", conn=conn)

    def test_create_task_with_gate_info(self, sample_sprint):
        """create_task with gate_info for quality gate tasks."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-gate-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="completion_gate",
            title="Gate Task",
            status="not_started",
            created=now,
            gate_info={"blocks_status": "completed", "threshold": 90, "is_blocking": True},
            conn=conn,
        )

        task = get_task("test-track-0-gate-001", conn=conn)
        assert task["gate_info"]["threshold"] == 90

    def test_get_task(self, sample_sprint):
        """get_task returns task data."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Test Task",
            status="not_started",
            created=now,
            priority="high",
            conn=conn,
        )

        task = get_task("test-track-0-task-001", conn=conn)
        assert task is not None
        assert task["title"] == "Test Task"
        assert task["priority"] == "high"

    def test_update_task(self, sample_sprint):
        """update_task updates task fields."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Test Task",
            status="not_started",
            created=now,
            conn=conn,
        )

        result = update_task(
            "test-track-0-task-001",
            title="Updated Task",
            status="in_progress",
            started=now,
            conn=conn,
        )

        assert result is True
        task = get_task("test-track-0-task-001", conn=conn)
        assert task["title"] == "Updated Task"
        assert task["status"] == "in_progress"

    def test_delete_task(self, sample_sprint):
        """delete_task removes task."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Test Task",
            status="not_started",
            created=now,
            conn=conn,
        )

        result = delete_task("test-track-0-task-001", conn=conn)

        assert result is True
        assert not task_exists("test-track-0-task-001", conn=conn)

    def test_list_tasks_by_sprint(self, sample_sprint):
        """list_tasks_by_sprint returns tasks for a sprint."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        for i in range(3):
            create_task(
                id=f"test-track-0-task-00{i}",
                sprint_id="test-track-0",
                track_id="test-track",
                roadmap_id="test-roadmap",
                task_type="development",
                title=f"Task {i}",
                status="not_started",
                created=now,
                conn=conn,
            )

        tasks = list_tasks_by_sprint("test-track-0", conn=conn)
        assert len(tasks) == 3

    def test_list_tasks_by_track(self, sample_sprint):
        """list_tasks_by_track returns tasks for a track."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Task 1",
            status="not_started",
            created=now,
            conn=conn,
        )

        tasks = list_tasks_by_track("test-track", conn=conn)
        assert len(tasks) == 1

    def test_get_blocked_tasks(self, sample_sprint):
        """get_blocked_tasks returns only blocked tasks."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Unblocked",
            status="not_started",
            blocked=False,
            created=now,
            conn=conn,
        )
        create_task(
            id="test-track-0-task-002",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Blocked",
            status="not_started",
            blocked=True,
            created=now,
            conn=conn,
        )

        blocked = get_blocked_tasks(conn=conn)
        assert len(blocked) == 1
        assert blocked[0]["title"] == "Blocked"

    def test_count_tasks(self, sample_sprint):
        """count_tasks returns correct count."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Task 1",
            status="not_started",
            created=now,
            conn=conn,
        )

        assert count_tasks(sprint_id="test-track-0", conn=conn) == 1


# =============================================================================
# CASCADE DELETE TESTS
# =============================================================================

class TestCascadeDeletes:
    """Tests for cascade delete behavior."""

    def test_delete_roadmap_cascades_all(self, sample_sprint):
        """Deleting roadmap cascades to tracks, sprints, and tasks."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        # Add a task
        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Task",
            status="not_started",
            created=now,
            conn=conn,
        )

        # Delete roadmap
        delete_roadmap("test-roadmap", conn=conn)

        # All should be gone
        assert not roadmap_exists("test-roadmap", conn=conn)
        assert not track_exists("test-track", conn=conn)
        assert not sprint_exists("test-track-0", conn=conn)
        assert not task_exists("test-track-0-task-001", conn=conn)

    def test_delete_track_cascades_to_sprints_and_tasks(self, sample_sprint):
        """Deleting track cascades to sprints and tasks."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Task",
            status="not_started",
            created=now,
            conn=conn,
        )

        delete_track("test-track", conn=conn)

        assert roadmap_exists("test-roadmap", conn=conn)  # Roadmap still exists
        assert not track_exists("test-track", conn=conn)
        assert not sprint_exists("test-track-0", conn=conn)
        assert not task_exists("test-track-0-task-001", conn=conn)

    def test_delete_sprint_cascades_to_tasks(self, sample_sprint):
        """Deleting sprint cascades to tasks."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Task",
            status="not_started",
            created=now,
            conn=conn,
        )

        delete_sprint("test-track-0", conn=conn)

        assert track_exists("test-track", conn=conn)  # Track still exists
        assert not sprint_exists("test-track-0", conn=conn)
        assert not task_exists("test-track-0-task-001", conn=conn)


# =============================================================================
# ADDITIONAL COVERAGE TESTS
# =============================================================================

class TestDbPathParameter:
    """Tests for using db_path parameter instead of conn."""

    def test_create_task_with_db_path(self, sample_sprint):
        """create_task works with db_path parameter."""
        conn, db_path = sample_sprint
        now = datetime.now(timezone.utc)

        # Use db_path instead of conn
        create_task(
            id="test-track-0-task-dbpath",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="DbPath Task",
            status="not_started",
            created=now,
            db_path=db_path,
        )

        task = get_task("test-track-0-task-dbpath", conn=conn)
        assert task is not None
        assert task["title"] == "DbPath Task"

    def test_get_task_with_db_path(self, sample_sprint):
        """get_task works with db_path parameter."""
        conn, db_path = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Task 1",
            status="not_started",
            created=now,
            conn=conn,
        )

        task = get_task("test-track-0-task-001", db_path=db_path)
        assert task is not None
        assert task["title"] == "Task 1"

    def test_get_task_not_found_returns_none(self, db_with_schema):
        """get_task returns None for non-existent task."""
        conn, _ = db_with_schema
        task = get_task("nonexistent", conn=conn)
        assert task is None

    def test_task_exists_with_db_path(self, sample_sprint):
        """task_exists works with db_path parameter."""
        conn, db_path = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Task 1",
            status="not_started",
            created=now,
            conn=conn,
        )

        assert task_exists("test-track-0-task-001", db_path=db_path)
        assert not task_exists("nonexistent", db_path=db_path)


class TestTaskFilters:
    """Tests for task filtering functions."""

    def test_list_tasks_by_roadmap_with_filters(self, sample_sprint):
        """list_tasks_by_roadmap filters by status and task_type."""
        from vibey.roadmap.database.crud import list_tasks_by_roadmap

        conn, db_path = sample_sprint
        now = datetime.now(timezone.utc)

        # Create multiple tasks with different statuses and types
        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Dev Task",
            status="not_started",
            created=now,
            conn=conn,
        )
        create_task(
            id="test-track-0-task-002",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="completion_gate",
            title="Gate Task",
            status="completed",
            created=now,
            conn=conn,
        )

        # Test filter by status
        tasks = list_tasks_by_roadmap("test-roadmap", status="not_started", conn=conn)
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Dev Task"

        # Test filter by task_type
        tasks = list_tasks_by_roadmap("test-roadmap", task_type="completion_gate", conn=conn)
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Gate Task"

        # Test with db_path parameter
        tasks = list_tasks_by_roadmap("test-roadmap", db_path=db_path)
        assert len(tasks) == 2

    def test_count_tasks_with_all_filters(self, sample_sprint):
        """count_tasks works with various filter combinations."""
        conn, db_path = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Task 1",
            status="not_started",
            created=now,
            conn=conn,
        )
        create_task(
            id="test-track-0-task-002",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="completion_gate",
            title="Task 2",
            status="completed",
            created=now,
            conn=conn,
        )

        # Test with db_path parameter
        assert count_tasks(db_path=db_path) == 2

        # Test filter by track_id
        assert count_tasks(track_id="test-track", conn=conn) == 2
        assert count_tasks(track_id="nonexistent", conn=conn) == 0

        # Test filter by roadmap_id
        assert count_tasks(roadmap_id="test-roadmap", conn=conn) == 2

        # Test filter by status
        assert count_tasks(status="not_started", conn=conn) == 1
        assert count_tasks(status="completed", conn=conn) == 1

        # Test filter by task_type
        assert count_tasks(task_type="development", conn=conn) == 1
        assert count_tasks(task_type="completion_gate", conn=conn) == 1

    def test_get_blocked_tasks_with_filters(self, sample_sprint):
        """get_blocked_tasks filters by hierarchy levels."""
        conn, db_path = sample_sprint
        now = datetime.now(timezone.utc)

        # Create a blocked task
        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Blocked Task",
            status="not_started",
            blocked=True,
            created=now,
            conn=conn,
        )

        # Test filter by roadmap_id
        blocked = get_blocked_tasks(roadmap_id="test-roadmap", conn=conn)
        assert len(blocked) == 1

        # Test filter by track_id
        blocked = get_blocked_tasks(track_id="test-track", conn=conn)
        assert len(blocked) == 1

        # Test filter by sprint_id
        blocked = get_blocked_tasks(sprint_id="test-track-0", conn=conn)
        assert len(blocked) == 1

        # Test with db_path
        blocked = get_blocked_tasks(db_path=db_path)
        assert len(blocked) == 1

        # Test with nonexistent filters
        blocked = get_blocked_tasks(roadmap_id="nonexistent", conn=conn)
        assert len(blocked) == 0


class TestUpdateEdgeCases:
    """Tests for update function edge cases."""

    def test_update_task_not_found(self, db_with_schema):
        """update_task returns False for non-existent task."""
        conn, _ = db_with_schema
        result = update_task("nonexistent", status="completed", conn=conn)
        assert result is False

    def test_update_task_no_fields(self, sample_sprint):
        """update_task raises ValueError with no fields."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Task 1",
            status="not_started",
            created=now,
            conn=conn,
        )

        with pytest.raises(ValueError, match="No update fields"):
            update_task("test-track-0-task-001", conn=conn)

    def test_update_track_not_found(self, db_with_schema):
        """update_track returns False for non-existent track."""
        conn, _ = db_with_schema
        result = update_track("nonexistent", status="completed", conn=conn)
        assert result is False

    def test_update_sprint_not_found(self, db_with_schema):
        """update_sprint returns False for non-existent sprint."""
        conn, _ = db_with_schema
        result = update_sprint("nonexistent", status="completed", conn=conn)
        assert result is False


class TestDeleteEdgeCases:
    """Tests for delete function edge cases."""

    def test_delete_task_not_found(self, db_with_schema):
        """delete_task returns False for non-existent task."""
        conn, _ = db_with_schema
        result = delete_task("nonexistent", conn=conn)
        assert result is False

    def test_delete_track_not_found(self, db_with_schema):
        """delete_track returns False for non-existent track."""
        conn, _ = db_with_schema
        result = delete_track("nonexistent", conn=conn)
        assert result is False

    def test_delete_sprint_not_found(self, db_with_schema):
        """delete_sprint returns False for non-existent sprint."""
        conn, _ = db_with_schema
        result = delete_sprint("nonexistent", conn=conn)
        assert result is False


class TestTrackDbPathAndFilters:
    """Tests for track db_path parameter and filter functions."""

    def test_create_track_with_db_path(self, sample_roadmap):
        """create_track works with db_path parameter."""
        conn, db_path = sample_roadmap
        now = datetime.now(timezone.utc)

        create_track(
            id="test-track-dbpath",
            roadmap_id="test-roadmap",
            name="DbPath Track",
            status="not_started",
            created=now,
            db_path=db_path,
        )

        track = get_track("test-track-dbpath", conn=conn)
        assert track is not None
        assert track["name"] == "DbPath Track"

    def test_get_track_with_db_path(self, sample_track):
        """get_track works with db_path parameter."""
        conn, db_path = sample_track
        track = get_track("test-track", db_path=db_path)
        assert track is not None
        assert track["name"] == "Test Track"

    def test_get_track_not_found(self, db_with_schema):
        """get_track returns None for non-existent track."""
        conn, _ = db_with_schema
        track = get_track("nonexistent", conn=conn)
        assert track is None

    def test_track_exists_with_db_path(self, sample_track):
        """track_exists works with db_path parameter."""
        conn, db_path = sample_track
        assert track_exists("test-track", db_path=db_path)
        assert not track_exists("nonexistent", db_path=db_path)

    def test_list_tracks_with_filters(self, sample_roadmap):
        """list_tracks_by_roadmap with filter combinations."""
        conn, db_path = sample_roadmap
        now = datetime.now(timezone.utc)

        create_track(
            id="test-track-1",
            roadmap_id="test-roadmap",
            name="Track 1",
            status="not_started",
            priority="high",
            created=now,
            conn=conn,
        )
        create_track(
            id="test-track-2",
            roadmap_id="test-roadmap",
            name="Track 2",
            status="completed",
            priority="low",
            created=now,
            conn=conn,
        )

        # Test filter by status
        tracks = list_tracks_by_roadmap("test-roadmap", status="not_started", conn=conn)
        assert len(tracks) == 1
        assert tracks[0]["name"] == "Track 1"

        # Test with db_path
        tracks = list_tracks_by_roadmap("test-roadmap", db_path=db_path)
        assert len(tracks) == 2

    def test_count_tracks_with_filters(self, sample_roadmap):
        """count_tracks works with various filter combinations."""
        conn, db_path = sample_roadmap
        now = datetime.now(timezone.utc)

        create_track(
            id="test-track-1",
            roadmap_id="test-roadmap",
            name="Track 1",
            status="not_started",
            created=now,
            conn=conn,
        )

        # Test with db_path parameter
        assert count_tracks(db_path=db_path) == 1

        # Test filter by roadmap_id
        assert count_tracks(roadmap_id="test-roadmap", conn=conn) == 1
        assert count_tracks(roadmap_id="nonexistent", conn=conn) == 0

        # Test filter by status
        assert count_tracks(status="not_started", conn=conn) == 1


class TestSprintDbPathAndFilters:
    """Tests for sprint db_path parameter and filter functions."""

    def test_create_sprint_with_db_path(self, sample_track):
        """create_sprint works with db_path parameter."""
        conn, db_path = sample_track
        now = datetime.now(timezone.utc)

        create_sprint(
            id="test-track-1",
            track_id="test-track",
            roadmap_id="test-roadmap",
            name="DbPath Sprint",
            status="not_started",
            created=now,
            db_path=db_path,
        )

        sprint = get_sprint("test-track-1", conn=conn)
        assert sprint is not None
        assert sprint["name"] == "DbPath Sprint"

    def test_get_sprint_with_db_path(self, sample_sprint):
        """get_sprint works with db_path parameter."""
        conn, db_path = sample_sprint
        sprint = get_sprint("test-track-0", db_path=db_path)
        assert sprint is not None
        # sample_sprint fixture creates a sprint with id "test-track-0"
        assert "Sprint" in sprint["name"] or "sprint" in sprint["name"].lower()

    def test_get_sprint_not_found(self, db_with_schema):
        """get_sprint returns None for non-existent sprint."""
        conn, _ = db_with_schema
        sprint = get_sprint("nonexistent", conn=conn)
        assert sprint is None

    def test_sprint_exists_with_db_path(self, sample_sprint):
        """sprint_exists works with db_path parameter."""
        conn, db_path = sample_sprint
        assert sprint_exists("test-track-0", db_path=db_path)
        assert not sprint_exists("nonexistent", db_path=db_path)

    def test_list_sprints_with_filters(self, sample_track):
        """list_sprints_by_track with filter combinations."""
        conn, db_path = sample_track
        now = datetime.now(timezone.utc)

        create_sprint(
            id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            name="Sprint 0",
            status="not_started",
            created=now,
            conn=conn,
        )
        create_sprint(
            id="test-track-1",
            track_id="test-track",
            roadmap_id="test-roadmap",
            name="Sprint 1",
            status="completed",
            created=now,
            conn=conn,
        )

        # Test filter by status
        sprints = list_sprints_by_track("test-track", status="not_started", conn=conn)
        assert len(sprints) == 1
        assert sprints[0]["name"] == "Sprint 0"

        # Test with db_path
        sprints = list_sprints_by_track("test-track", db_path=db_path)
        assert len(sprints) == 2

    def test_count_sprints_with_filters(self, sample_track):
        """count_sprints works with various filter combinations."""
        conn, db_path = sample_track
        now = datetime.now(timezone.utc)

        create_sprint(
            id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            name="Sprint 0",
            status="not_started",
            created=now,
            conn=conn,
        )

        # Test with db_path parameter
        assert count_sprints(db_path=db_path) == 1

        # Test filter by track_id
        assert count_sprints(track_id="test-track", conn=conn) == 1
        assert count_sprints(track_id="nonexistent", conn=conn) == 0

        # Test filter by roadmap_id
        assert count_sprints(roadmap_id="test-roadmap", conn=conn) == 1

        # Test filter by status
        assert count_sprints(status="not_started", conn=conn) == 1


class TestTrackUpdateFields:
    """Tests for track update with different field types."""

    def test_update_track_datetime_fields(self, sample_track):
        """update_track handles datetime fields correctly."""
        conn, _ = sample_track
        now = datetime.now(timezone.utc)

        result = update_track(
            "test-track",
            started=now,
            completed=now,
            conn=conn,
        )
        assert result is True

        track = get_track("test-track", conn=conn)
        assert track["started"] is not None
        assert track["completed"] is not None

    def test_update_track_metadata_field(self, sample_track):
        """update_track handles metadata field correctly."""
        conn, _ = sample_track

        result = update_track(
            "test-track",
            metadata={"key": "value", "nested": {"a": 1}},
            conn=conn,
        )
        assert result is True

        track = get_track("test-track", conn=conn)
        assert track["metadata"]["key"] == "value"

    def test_update_track_blocked_field(self, sample_track):
        """update_track handles blocked field correctly."""
        conn, _ = sample_track

        result = update_track("test-track", blocked=True, conn=conn)
        assert result is True

        track = get_track("test-track", conn=conn)
        assert track["blocked"] is True

        result = update_track("test-track", blocked=False, conn=conn)
        assert result is True

        track = get_track("test-track", conn=conn)
        assert track["blocked"] is False

    def test_update_track_unknown_field(self, sample_track):
        """update_track raises ValueError for unknown field."""
        conn, _ = sample_track

        with pytest.raises(ValueError, match="Unknown field"):
            update_track("test-track", unknown_field="value", conn=conn)

    def test_update_track_no_fields(self, sample_track):
        """update_track raises ValueError when no fields provided."""
        conn, _ = sample_track

        with pytest.raises(ValueError, match="No update fields"):
            update_track("test-track", conn=conn)

    def test_update_track_with_db_path(self, sample_track):
        """update_track works with db_path parameter."""
        conn, db_path = sample_track

        result = update_track("test-track", status="completed", db_path=db_path)
        assert result is True

        track = get_track("test-track", conn=conn)
        assert track["status"] == "completed"

    def test_delete_track_with_db_path(self, sample_track):
        """delete_track works with db_path parameter."""
        conn, db_path = sample_track

        result = delete_track("test-track", db_path=db_path)
        assert result is True
        assert not track_exists("test-track", conn=conn)

    def test_list_tracks_with_priority_filter(self, sample_roadmap):
        """list_tracks_by_roadmap filters by priority."""
        conn, _ = sample_roadmap
        now = datetime.now(timezone.utc)

        create_track(
            id="high-priority-track",
            roadmap_id="test-roadmap",
            name="High Priority",
            status="not_started",
            priority="high",
            created=now,
            conn=conn,
        )
        create_track(
            id="low-priority-track",
            roadmap_id="test-roadmap",
            name="Low Priority",
            status="not_started",
            priority="low",
            created=now,
            conn=conn,
        )

        tracks = list_tracks_by_roadmap("test-roadmap", priority="high", conn=conn)
        assert len(tracks) == 1
        assert tracks[0]["name"] == "High Priority"


class TestSprintUpdateFields:
    """Tests for sprint update with different field types."""

    def test_update_sprint_datetime_fields(self, sample_sprint):
        """update_sprint handles datetime fields correctly."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        result = update_sprint(
            "test-track-0",
            started=now,
            completed=now,
            completion_gate_check_at=now,
            production_gate_check_at=now,
            conn=conn,
        )
        assert result is True

        sprint = get_sprint("test-track-0", conn=conn)
        assert sprint["started"] is not None
        assert sprint["completed"] is not None

    def test_update_sprint_metadata_field(self, sample_sprint):
        """update_sprint handles metadata field correctly."""
        conn, _ = sample_sprint

        result = update_sprint(
            "test-track-0",
            metadata={"key": "value", "nested": {"a": 1}},
            conn=conn,
        )
        assert result is True

        sprint = get_sprint("test-track-0", conn=conn)
        assert sprint["metadata"]["key"] == "value"

    def test_update_sprint_blocked_field(self, sample_sprint):
        """update_sprint handles blocked field correctly."""
        conn, _ = sample_sprint

        result = update_sprint("test-track-0", blocked=True, conn=conn)
        assert result is True

        sprint = get_sprint("test-track-0", conn=conn)
        assert sprint["blocked"] is True

    def test_update_sprint_unknown_field(self, sample_sprint):
        """update_sprint raises ValueError for unknown field."""
        conn, _ = sample_sprint

        with pytest.raises(ValueError, match="Unknown field"):
            update_sprint("test-track-0", unknown_field="value", conn=conn)

    def test_update_sprint_no_fields(self, sample_sprint):
        """update_sprint raises ValueError when no fields provided."""
        conn, _ = sample_sprint

        with pytest.raises(ValueError, match="No update fields"):
            update_sprint("test-track-0", conn=conn)

    def test_update_sprint_with_db_path(self, sample_sprint):
        """update_sprint works with db_path parameter."""
        conn, db_path = sample_sprint

        result = update_sprint("test-track-0", status="completed", db_path=db_path)
        assert result is True

        sprint = get_sprint("test-track-0", conn=conn)
        assert sprint["status"] == "completed"

    def test_delete_sprint_with_db_path(self, sample_sprint):
        """delete_sprint works with db_path parameter."""
        conn, db_path = sample_sprint

        result = delete_sprint("test-track-0", db_path=db_path)
        assert result is True
        assert not sprint_exists("test-track-0", conn=conn)


class TestRoadmapUpdateFields:
    """Tests for roadmap update with different field types."""

    def test_update_roadmap_datetime_fields(self, sample_roadmap):
        """update_roadmap handles datetime fields correctly."""
        conn, _ = sample_roadmap
        now = datetime.now(timezone.utc)

        result = update_roadmap(
            "test-roadmap",
            target_completion=now,
            completed=now,
            deployed=now,
            conn=conn,
        )
        assert result is True

        roadmap = get_roadmap("test-roadmap", conn=conn)
        assert roadmap["target_completion"] is not None
        assert roadmap["completed"] is not None

    def test_update_roadmap_metadata_field(self, sample_roadmap):
        """update_roadmap handles metadata field correctly."""
        conn, _ = sample_roadmap

        result = update_roadmap(
            "test-roadmap",
            metadata={"key": "value"},
            conn=conn,
        )
        assert result is True

        roadmap = get_roadmap("test-roadmap", conn=conn)
        assert roadmap["metadata"]["key"] == "value"

    def test_update_roadmap_blocked_field(self, sample_roadmap):
        """update_roadmap handles blocked field correctly."""
        conn, _ = sample_roadmap

        result = update_roadmap("test-roadmap", blocked=True, conn=conn)
        assert result is True

        roadmap = get_roadmap("test-roadmap", conn=conn)
        assert roadmap["blocked"] is True

    def test_update_roadmap_unknown_field(self, sample_roadmap):
        """update_roadmap raises ValueError for unknown field."""
        conn, _ = sample_roadmap

        with pytest.raises(ValueError, match="Unknown field"):
            update_roadmap("test-roadmap", unknown_field="value", conn=conn)

    def test_update_roadmap_no_fields(self, sample_roadmap):
        """update_roadmap raises ValueError when no fields provided."""
        conn, _ = sample_roadmap

        with pytest.raises(ValueError, match="No update fields"):
            update_roadmap("test-roadmap", conn=conn)

    def test_update_roadmap_with_db_path(self, sample_roadmap):
        """update_roadmap works with db_path parameter."""
        conn, db_path = sample_roadmap

        result = update_roadmap("test-roadmap", status="completed", db_path=db_path)
        assert result is True

        roadmap = get_roadmap("test-roadmap", conn=conn)
        assert roadmap["status"] == "completed"

    def test_delete_roadmap_with_db_path(self, sample_roadmap):
        """delete_roadmap works with db_path parameter."""
        conn, db_path = sample_roadmap

        result = delete_roadmap("test-roadmap", db_path=db_path)
        assert result is True
        assert not roadmap_exists("test-roadmap", conn=conn)


class TestTaskUpdateFields:
    """Tests for task update with different field types."""

    def test_update_task_datetime_fields(self, sample_sprint):
        """update_task handles datetime fields correctly."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Task 1",
            status="not_started",
            created=now,
            conn=conn,
        )

        result = update_task(
            "test-track-0-task-001",
            started=now,
            completed=now,
            conn=conn,
        )
        assert result is True

        task = get_task("test-track-0-task-001", conn=conn)
        assert task["started"] is not None
        assert task["completed"] is not None

    def test_update_task_json_fields(self, sample_sprint):
        """update_task handles JSON fields correctly."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Task 1",
            status="not_started",
            created=now,
            conn=conn,
        )

        result = update_task(
            "test-track-0-task-001",
            gate_info={"threshold": 80, "is_blocking": True},
            audit_results={"issues_found": 5},
            metadata={"key": "value"},
            conn=conn,
        )
        assert result is True

        task = get_task("test-track-0-task-001", conn=conn)
        assert task["gate_info"]["threshold"] == 80
        assert task["audit_results"]["issues_found"] == 5
        assert task["metadata"]["key"] == "value"

    def test_update_task_blocked_field(self, sample_sprint):
        """update_task handles blocked field correctly."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Task 1",
            status="not_started",
            created=now,
            conn=conn,
        )

        result = update_task("test-track-0-task-001", blocked=True, conn=conn)
        assert result is True

        task = get_task("test-track-0-task-001", conn=conn)
        assert task["blocked"] is True

    def test_update_task_int_fields(self, sample_sprint):
        """update_task handles integer fields correctly."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Task 1",
            status="not_started",
            created=now,
            conn=conn,
        )

        result = update_task(
            "test-track-0-task-001",
            estimated_tokens=100,
            actual_tokens=150,
            conn=conn,
        )
        assert result is True

        task = get_task("test-track-0-task-001", conn=conn)
        assert task["estimated_tokens"] == 100
        assert task["actual_tokens"] == 150

    def test_update_task_unknown_field(self, sample_sprint):
        """update_task raises ValueError for unknown field."""
        conn, _ = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Task 1",
            status="not_started",
            created=now,
            conn=conn,
        )

        with pytest.raises(ValueError, match="Unknown field"):
            update_task("test-track-0-task-001", unknown_field="value", conn=conn)

    def test_update_task_with_db_path(self, sample_sprint):
        """update_task works with db_path parameter."""
        conn, db_path = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Task 1",
            status="not_started",
            created=now,
            conn=conn,
        )

        result = update_task("test-track-0-task-001", status="completed", db_path=db_path)
        assert result is True

        task = get_task("test-track-0-task-001", conn=conn)
        assert task["status"] == "completed"

    def test_delete_task_with_db_path(self, sample_sprint):
        """delete_task works with db_path parameter."""
        conn, db_path = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Task 1",
            status="not_started",
            created=now,
            conn=conn,
        )

        result = delete_task("test-track-0-task-001", db_path=db_path)
        assert result is True
        assert not task_exists("test-track-0-task-001", conn=conn)

    def test_list_tasks_by_sprint_with_filters(self, sample_sprint):
        """list_tasks_by_sprint filters by status and task_type."""
        conn, db_path = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Dev Task",
            status="not_started",
            created=now,
            conn=conn,
        )
        create_task(
            id="test-track-0-task-002",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="completion_gate",
            title="Gate Task",
            status="completed",
            created=now,
            conn=conn,
        )

        # Test filter by status
        tasks = list_tasks_by_sprint("test-track-0", status="not_started", conn=conn)
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Dev Task"

        # Test filter by task_type
        tasks = list_tasks_by_sprint("test-track-0", task_type="completion_gate", conn=conn)
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Gate Task"

        # Test with db_path
        tasks = list_tasks_by_sprint("test-track-0", db_path=db_path)
        assert len(tasks) == 2

    def test_list_tasks_by_track_with_filters(self, sample_sprint):
        """list_tasks_by_track filters by status and task_type."""
        conn, db_path = sample_sprint
        now = datetime.now(timezone.utc)

        create_task(
            id="test-track-0-task-001",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="development",
            title="Dev Task",
            status="not_started",
            created=now,
            conn=conn,
        )
        create_task(
            id="test-track-0-task-002",
            sprint_id="test-track-0",
            track_id="test-track",
            roadmap_id="test-roadmap",
            task_type="completion_gate",
            title="Gate Task",
            status="completed",
            created=now,
            conn=conn,
        )

        # Test filter by status
        tasks = list_tasks_by_track("test-track", status="completed", conn=conn)
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Gate Task"

        # Test filter by task_type
        tasks = list_tasks_by_track("test-track", task_type="development", conn=conn)
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Dev Task"

        # Test with db_path
        tasks = list_tasks_by_track("test-track", db_path=db_path)
        assert len(tasks) == 2


class TestRoadmapDbPathAndFilters:
    """Tests for roadmap db_path parameter and filter functions."""

    def test_create_roadmap_with_db_path(self, db_with_schema):
        """create_roadmap works with db_path parameter."""
        conn, db_path = db_with_schema
        now = datetime.now(timezone.utc)

        create_roadmap(
            id="dbpath-roadmap",
            name="DbPath Roadmap",
            version="1.0.0",
            status="not_started",
            created=now,
            db_path=db_path,
        )

        roadmap = get_roadmap("dbpath-roadmap", conn=conn)
        assert roadmap is not None
        assert roadmap["name"] == "DbPath Roadmap"

    def test_get_roadmap_with_db_path(self, sample_roadmap):
        """get_roadmap works with db_path parameter."""
        conn, db_path = sample_roadmap
        roadmap = get_roadmap("test-roadmap", db_path=db_path)
        assert roadmap is not None
        assert roadmap["name"] == "Test Roadmap"

    def test_roadmap_exists_with_db_path(self, sample_roadmap):
        """roadmap_exists works with db_path parameter."""
        conn, db_path = sample_roadmap
        assert roadmap_exists("test-roadmap", db_path=db_path)
        assert not roadmap_exists("nonexistent", db_path=db_path)

    def test_count_roadmaps_with_filters(self, db_with_schema):
        """count_roadmaps works with status filter."""
        conn, db_path = db_with_schema
        now = datetime.now(timezone.utc)

        create_roadmap(
            id="roadmap-1",
            name="Roadmap 1",
            version="1.0.0",
            status="not_started",
            created=now,
            conn=conn,
        )
        create_roadmap(
            id="roadmap-2",
            name="Roadmap 2",
            version="1.0.0",
            status="in_progress",
            started=now,
            created=now,
            conn=conn,
        )

        # Test with db_path parameter
        assert count_roadmaps(db_path=db_path) == 2

        # Test filter by status
        assert count_roadmaps(status="not_started", conn=conn) == 1
        assert count_roadmaps(status="in_progress", conn=conn) == 1
