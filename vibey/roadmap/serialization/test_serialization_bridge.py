"""
Tests for the serialization bridge (SQL loader, SQL dumper, and backend abstraction).

These tests verify:
1. SQL loader can load entities from database
2. SQL dumper can save entities to database
3. Backend abstraction works correctly
4. Roundtrip (save then load) preserves data
"""

import pytest
import tempfile
import os
from datetime import datetime, timezone
from pathlib import Path

from vibey.roadmap.models import (
    Roadmap, Track, Sprint, Task,
    Status, TaskStatus, Priority, TaskType, Complexity,
    VersionStrategy, VersionBumpTrigger,
    Progress, TrackProgress, SprintProgress,
    Metadata, TrackMetadata, SprintMetadata, TaskMetadata,
    TrackSummary, SprintSummary, TaskSummary,
    DependencyStatus,
)
from vibey.roadmap.database import (
    get_connection, close_all_connections,
    create_schema, create_views, create_triggers,
    drop_all_tables, drop_views, drop_triggers,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Close any existing connections first
    close_all_connections()

    # Create temp file
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    # Remove the file so we start fresh
    os.unlink(db_path)

    # Set environment variable to use temp db
    os.environ['VIBEY_DB_PATH'] = db_path

    # Initialize database - get fresh connection
    conn = get_connection()

    # Clean slate - drop everything first
    drop_triggers(conn)
    drop_views(conn)
    drop_all_tables(conn)
    conn.commit()

    # Now create fresh schema
    create_schema(conn)
    create_views(conn)
    create_triggers(conn)
    conn.commit()

    yield db_path

    # Cleanup
    close_all_connections()
    if 'VIBEY_DB_PATH' in os.environ:
        del os.environ['VIBEY_DB_PATH']
    try:
        os.unlink(db_path)
    except Exception:
        pass


@pytest.fixture
def sample_roadmap():
    """Create a sample roadmap for testing."""
    now = datetime.now(timezone.utc)
    return Roadmap(
        id='test-roadmap',
        name='Test Roadmap',
        version='1.0.0',
        version_strategy=VersionStrategy(
            major_on=VersionBumpTrigger.ROADMAP_MILESTONE,
            minor_on=VersionBumpTrigger.TRACK_COMPLETION,
            patch_on=VersionBumpTrigger.SPRINT_PRODUCTION_READY,
        ),
        status=Status.IN_PROGRESS,
        blocked=False,
        created=now,
        started=now,  # Required for IN_PROGRESS status
        progress=Progress(
            tracks_total=2,
            tracks_completed=0,
            sprints_total=4,
            sprints_completed=1,
            tasks_total=10,
            tasks_completed=3,
            completion_percent=30,
        ),
        tracks=[
            TrackSummary(id='track-1', name='Track 1', status=Status.IN_PROGRESS, priority=Priority.HIGH),
            TrackSummary(id='track-2', name='Track 2', status=Status.NOT_STARTED, priority=Priority.MEDIUM),
        ],
        dependencies=[],
        blocked_by=[],
        version_history=[],
        activity_log=[],
        metadata=Metadata(
            created_by='test',
            framework_version='2.0.0',
            schema_version='2.1',
            last_updated=now,
        ),
        deployed_platforms=[],
        standards=[],
    )


@pytest.fixture
def sample_track():
    """Create a sample track for testing."""
    now = datetime.now(timezone.utc)
    return Track(
        id='track-1',
        name='Track 1',
        roadmap_id='test-roadmap',
        status=Status.IN_PROGRESS,
        blocked=False,
        priority=Priority.HIGH,
        created=now,
        started=now,  # Required for IN_PROGRESS status
        progress=TrackProgress(
            sprints_total=2,
            sprints_completed=1,
            tasks_total=5,
            tasks_completed=2,
            completion_percent=40,
        ),
        sprints=[
            SprintSummary(id='track-1-0', name='Sprint 0', status=Status.COMPLETED),
            SprintSummary(id='track-1-1', name='Sprint 1', status=Status.IN_PROGRESS),
        ],
        dependencies=[],
        blocks=[],
        blocked_by=[],
        depends_on=[],
        depended_on_by=[],
        quality_gates=[],
        assigned_agents=[],
        deliverables=[],
        strategic_value=[],
        commits=[],
        metadata=TrackMetadata(
            created_by='test',
            last_updated=now,
        ),
        standards=[],
    )


@pytest.fixture
def sample_sprint():
    """Create a sample sprint for testing."""
    now = datetime.now(timezone.utc)
    return Sprint(
        id='track-1-1',
        name='Sprint 1',
        track_id='track-1',
        roadmap_id='test-roadmap',
        status=Status.IN_PROGRESS,
        blocked=False,
        created=now,
        started=now,  # Required for IN_PROGRESS status
        progress=SprintProgress(
            development_tasks_total=3,
            development_tasks_completed=1,
            completion_gate_tasks_total=1,
            completion_gate_tasks_completed=0,
            production_gate_tasks_total=1,
            production_gate_tasks_completed=0,
            tasks_total=5,
            tasks_completed=1,
            completion_percent=20,
        ),
        tasks=[
            TaskSummary(id='track-1-1-task-001', title='Task 1', status=Status.COMPLETED, task_type=TaskType.DEVELOPMENT),
            TaskSummary(id='track-1-1-task-002', title='Task 2', status=Status.IN_PROGRESS, task_type=TaskType.DEVELOPMENT),
        ],
        development_gates=[],
        blocks=[],
        blocked_by=[],
        depends_on=[],
        depended_on_by=[],
        deliverables=[],
        commits=[],
        metadata=SprintMetadata(
            last_updated=now,
        ),
        standards=[],
    )


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    now = datetime.now(timezone.utc)
    return Task(
        id='track-1-1-task-001',
        sprint_id='track-1-1',
        track_id='track-1',
        roadmap_id='test-roadmap',
        task_type=TaskType.DEVELOPMENT,
        title='Sample Task',
        description='A sample task for testing',
        status=TaskStatus.COMPLETED,
        blocked=False,
        created=now,
        completed=now,
        assigned_agent=None,
        priority=Priority.HIGH,
        estimated_tokens=100,
        complexity=Complexity.MEDIUM,
        dependencies=[],
        blocks=[],
        blocked_by=[],
        depends_on=[],
        depended_on_by=[],
        deliverables=[],
        commits=[],
        metadata=TaskMetadata(
            last_updated=now,
        ),
    )


class TestSQLDumper:
    """Tests for sql_dumper.py"""

    def test_save_roadmap(self, temp_db, sample_roadmap):
        """Test saving a roadmap to SQLite."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap

        save_roadmap(sample_roadmap)

        # Verify it was saved
        conn = get_connection()
        row = conn.execute("SELECT * FROM roadmaps WHERE id = ?", (sample_roadmap.id,)).fetchone()
        assert row is not None
        assert row['name'] == 'Test Roadmap'
        assert row['version'] == '1.0.0'
        assert row['status'] == 'in_progress'

    def test_save_track(self, temp_db, sample_roadmap, sample_track):
        """Test saving a track to SQLite."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap, save_track

        # Must save roadmap first (foreign key)
        save_roadmap(sample_roadmap)
        save_track(sample_track)

        # Verify it was saved
        conn = get_connection()
        row = conn.execute("SELECT * FROM tracks WHERE id = ?", (sample_track.id,)).fetchone()
        assert row is not None
        assert row['name'] == 'Track 1'
        assert row['roadmap_id'] == 'test-roadmap'

    def test_save_sprint(self, temp_db, sample_roadmap, sample_track, sample_sprint):
        """Test saving a sprint to SQLite."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap, save_track, save_sprint

        save_roadmap(sample_roadmap)
        save_track(sample_track)
        save_sprint(sample_sprint)

        # Verify it was saved
        conn = get_connection()
        row = conn.execute("SELECT * FROM sprints WHERE id = ?", (sample_sprint.id,)).fetchone()
        assert row is not None
        assert row['name'] == 'Sprint 1'
        assert row['track_id'] == 'track-1'

    def test_save_task(self, temp_db, sample_roadmap, sample_track, sample_sprint, sample_task):
        """Test saving a task to SQLite."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap, save_track, save_sprint, save_task

        save_roadmap(sample_roadmap)
        save_track(sample_track)
        save_sprint(sample_sprint)
        save_task(sample_task)

        # Verify it was saved
        conn = get_connection()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (sample_task.id,)).fetchone()
        assert row is not None
        assert row['title'] == 'Sample Task'
        assert row['sprint_id'] == 'track-1-1'

    def test_save_multiple_tasks(self, temp_db, sample_roadmap, sample_track, sample_sprint):
        """Test saving multiple tasks at once."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap, save_track, save_sprint, save_tasks

        save_roadmap(sample_roadmap)
        save_track(sample_track)
        save_sprint(sample_sprint)

        tasks = [
            Task(
                id=f'track-1-1-task-{i:03d}',
                sprint_id='track-1-1',
                track_id='track-1',
                roadmap_id='test-roadmap',
                task_type=TaskType.DEVELOPMENT,
                title=f'Task {i}',
                description=f'Description {i}',
                status=TaskStatus.NOT_STARTED,
                blocked=False,
                created=datetime.now(timezone.utc),
                assigned_agent=None,
                priority=Priority.MEDIUM,
                estimated_tokens=50,
                complexity=Complexity.SIMPLE,
                dependencies=[],
                blocks=[],
                blocked_by=[],
                depends_on=[],
                depended_on_by=[],
                deliverables=[],
                commits=[],
                metadata=TaskMetadata(last_updated=datetime.now(timezone.utc)),
            )
            for i in range(1, 6)
        ]

        save_tasks(tasks)

        # Verify all were saved
        conn = get_connection()
        count = conn.execute("SELECT COUNT(*) FROM tasks WHERE sprint_id = 'track-1-1'").fetchone()[0]
        assert count == 5


class TestSQLLoader:
    """Tests for sql_loader.py"""

    def test_load_roadmap(self, temp_db, sample_roadmap):
        """Test loading a roadmap from SQLite."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap
        from vibey.roadmap.serialization.sql_loader import load_roadmap

        save_roadmap(sample_roadmap)
        loaded = load_roadmap(sample_roadmap.id)

        assert loaded.id == sample_roadmap.id
        assert loaded.name == sample_roadmap.name
        assert loaded.version == sample_roadmap.version
        assert loaded.status == sample_roadmap.status

    def test_load_track(self, temp_db, sample_roadmap, sample_track):
        """Test loading a track from SQLite."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap, save_track
        from vibey.roadmap.serialization.sql_loader import load_track

        save_roadmap(sample_roadmap)
        save_track(sample_track)
        loaded = load_track(sample_track.id)

        assert loaded.id == sample_track.id
        assert loaded.name == sample_track.name
        assert loaded.roadmap_id == sample_track.roadmap_id

    def test_load_sprint(self, temp_db, sample_roadmap, sample_track, sample_sprint):
        """Test loading a sprint from SQLite."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap, save_track, save_sprint
        from vibey.roadmap.serialization.sql_loader import load_sprint

        save_roadmap(sample_roadmap)
        save_track(sample_track)
        save_sprint(sample_sprint)
        loaded = load_sprint(sample_sprint.id)

        assert loaded.id == sample_sprint.id
        assert loaded.name == sample_sprint.name
        assert loaded.track_id == sample_sprint.track_id

    def test_load_task(self, temp_db, sample_roadmap, sample_track, sample_sprint, sample_task):
        """Test loading a task from SQLite."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap, save_track, save_sprint, save_task
        from vibey.roadmap.serialization.sql_loader import load_task

        save_roadmap(sample_roadmap)
        save_track(sample_track)
        save_sprint(sample_sprint)
        save_task(sample_task)
        loaded = load_task(sample_task.id)

        assert loaded.id == sample_task.id
        assert loaded.title == sample_task.title
        assert loaded.sprint_id == sample_task.sprint_id

    def test_load_tasks_by_sprint(self, temp_db, sample_roadmap, sample_track, sample_sprint):
        """Test loading tasks by sprint."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap, save_track, save_sprint, save_tasks
        from vibey.roadmap.serialization.sql_loader import load_tasks_by_sprint

        save_roadmap(sample_roadmap)
        save_track(sample_track)
        save_sprint(sample_sprint)

        # Create and save tasks
        tasks = [
            Task(
                id=f'track-1-1-task-{i:03d}',
                sprint_id='track-1-1',
                track_id='track-1',
                roadmap_id='test-roadmap',
                task_type=TaskType.DEVELOPMENT,
                title=f'Task {i}',
                description=f'Description {i}',
                status=TaskStatus.NOT_STARTED,
                blocked=False,
                created=datetime.now(timezone.utc),
                assigned_agent=None,
                priority=Priority.MEDIUM,
                estimated_tokens=50,
                complexity=Complexity.SIMPLE,
                dependencies=[],
                blocks=[],
                blocked_by=[],
                depends_on=[],
                depended_on_by=[],
                deliverables=[],
                commits=[],
                metadata=TaskMetadata(last_updated=datetime.now(timezone.utc)),
            )
            for i in range(1, 4)
        ]
        save_tasks(tasks)

        loaded_tasks = load_tasks_by_sprint('track-1-1')
        assert len(loaded_tasks) == 3

    def test_load_nonexistent_raises_error(self, temp_db):
        """Test that loading nonexistent entities raises ValueError."""
        from vibey.roadmap.serialization.sql_loader import load_roadmap, load_track, load_sprint, load_task

        with pytest.raises(ValueError, match="not found"):
            load_roadmap('nonexistent')

        with pytest.raises(ValueError, match="not found"):
            load_track('nonexistent')

        with pytest.raises(ValueError, match="not found"):
            load_sprint('nonexistent')

        with pytest.raises(ValueError, match="not found"):
            load_task('nonexistent')


class TestRoundtrip:
    """Tests for save-then-load roundtrip."""

    def test_roadmap_roundtrip(self, temp_db, sample_roadmap):
        """Test that saving then loading a roadmap preserves data."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap
        from vibey.roadmap.serialization.sql_loader import load_roadmap

        save_roadmap(sample_roadmap)
        loaded = load_roadmap(sample_roadmap.id)

        assert loaded.id == sample_roadmap.id
        assert loaded.name == sample_roadmap.name
        assert loaded.version == sample_roadmap.version
        assert loaded.status == sample_roadmap.status
        assert loaded.blocked == sample_roadmap.blocked
        assert loaded.version_strategy.major_on == sample_roadmap.version_strategy.major_on
        assert loaded.version_strategy.minor_on == sample_roadmap.version_strategy.minor_on
        assert loaded.version_strategy.patch_on == sample_roadmap.version_strategy.patch_on

    def test_task_roundtrip(self, temp_db, sample_roadmap, sample_track, sample_sprint, sample_task):
        """Test that saving then loading a task preserves data."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap, save_track, save_sprint, save_task
        from vibey.roadmap.serialization.sql_loader import load_task

        save_roadmap(sample_roadmap)
        save_track(sample_track)
        save_sprint(sample_sprint)
        save_task(sample_task)
        loaded = load_task(sample_task.id)

        assert loaded.id == sample_task.id
        assert loaded.title == sample_task.title
        assert loaded.description == sample_task.description
        assert loaded.status == sample_task.status
        assert loaded.blocked == sample_task.blocked
        assert loaded.priority == sample_task.priority
        assert loaded.task_type == sample_task.task_type
        assert loaded.complexity == sample_task.complexity
        assert loaded.estimated_tokens == sample_task.estimated_tokens


class TestBackendAbstraction:
    """Tests for backend.py"""

    def test_sqlite_backend_implements_protocol(self):
        """Test that SQLiteBackend implements RoadmapBackend protocol."""
        from vibey.roadmap.serialization.backend import SQLiteBackend, RoadmapBackend

        assert isinstance(SQLiteBackend(), RoadmapBackend)

    def test_yaml_backend_implements_protocol(self):
        """Test that YAMLBackend implements RoadmapBackend protocol."""
        from vibey.roadmap.serialization.backend import YAMLBackend, RoadmapBackend

        assert isinstance(YAMLBackend(), RoadmapBackend)

    def test_sqlite_backend_operations(self, temp_db, sample_roadmap, sample_track, sample_sprint, sample_task):
        """Test SQLiteBackend basic operations."""
        from vibey.roadmap.serialization.backend import SQLiteBackend

        backend = SQLiteBackend()

        # Save
        backend.save_roadmap(sample_roadmap)
        backend.save_track(sample_track)
        backend.save_sprint(sample_sprint)
        backend.save_task(sample_task)

        # Load
        loaded_roadmap = backend.load_roadmap(sample_roadmap.id)
        assert loaded_roadmap.id == sample_roadmap.id

        loaded_track = backend.load_track(sample_track.id)
        assert loaded_track.id == sample_track.id

        loaded_sprint = backend.load_sprint(sample_sprint.id)
        assert loaded_sprint.id == sample_sprint.id

        loaded_task = backend.load_task(sample_task.id)
        assert loaded_task.id == sample_task.id


class TestSyncManager:
    """Tests for SyncManager."""

    def test_compute_file_checksum(self, temp_db):
        """Test file checksum computation."""
        from vibey.roadmap.serialization.backend import SyncManager
        import tempfile

        sync = SyncManager()

        # Create a temp file with known content
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            f.write("test content")
            temp_path = f.name

        try:
            checksum = sync.compute_file_checksum(temp_path)
            assert len(checksum) == 64  # SHA-256 produces 64 hex characters

            # Same content should produce same checksum
            checksum2 = sync.compute_file_checksum(temp_path)
            assert checksum == checksum2
        finally:
            os.unlink(temp_path)

    def test_get_status_no_database(self):
        """Test get_status when no database exists."""
        from vibey.roadmap.serialization.backend import SyncManager
        import tempfile

        # Use a non-existent path
        sync = SyncManager(
            roadmap_dir=tempfile.mkdtemp(),
            db_path='/nonexistent/path.db'
        )

        status = sync.get_status()
        assert status['status'] == 'NO_DATABASE'
        assert status['db_exists'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
