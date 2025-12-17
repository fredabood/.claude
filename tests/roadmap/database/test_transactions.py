"""
Tests for transaction rollback behavior in roadmap database.

Tests that errors during updates properly rollback to maintain state integrity.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from vibey.roadmap.database.transactions import (
    atomic_mutation,
    update_task_status,
    update_sprint_status,
    update_track_status,
    complete_task,
    start_task,
    complete_sprint,
    start_sprint,
    complete_track,
    start_track,
    _log_activity,
    _get_task_state,
    _get_sprint_state,
    _get_track_state,
)


@pytest.fixture
def test_db():
    """Create a temporary test database with sample data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # Create minimal schema for testing
    conn.execute("""
        CREATE TABLE IF NOT EXISTS roadmaps (
            id TEXT PRIMARY KEY,
            name TEXT,
            status TEXT DEFAULT 'not_started'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id TEXT PRIMARY KEY,
            roadmap_id TEXT,
            name TEXT,
            status TEXT DEFAULT 'not_started',
            blocked INTEGER DEFAULT 0,
            started TEXT,
            completed TEXT,
            FOREIGN KEY (roadmap_id) REFERENCES roadmaps(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS sprints (
            id TEXT PRIMARY KEY,
            track_id TEXT,
            roadmap_id TEXT,
            name TEXT,
            status TEXT DEFAULT 'not_started',
            blocked INTEGER DEFAULT 0,
            started TEXT,
            completed TEXT,
            FOREIGN KEY (track_id) REFERENCES tracks(id),
            FOREIGN KEY (roadmap_id) REFERENCES roadmaps(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            sprint_id TEXT,
            roadmap_id TEXT,
            title TEXT,
            status TEXT DEFAULT 'not_started',
            blocked INTEGER DEFAULT 0,
            started TEXT,
            completed TEXT,
            FOREIGN KEY (sprint_id) REFERENCES sprints(id),
            FOREIGN KEY (roadmap_id) REFERENCES roadmaps(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roadmap_id TEXT,
            event_type TEXT,
            event_description TEXT,
            occurred_at TEXT,
            entity_type TEXT,
            entity_id TEXT,
            actor TEXT,
            old_state TEXT,
            new_state TEXT,
            metadata TEXT
        )
    """)

    # Insert test data
    conn.execute("INSERT INTO roadmaps (id, name, status) VALUES ('test-roadmap', 'Test Roadmap', 'in_progress')")
    conn.execute("INSERT INTO tracks (id, roadmap_id, name, status) VALUES ('test-track', 'test-roadmap', 'Test Track', 'in_progress')")
    conn.execute("INSERT INTO sprints (id, track_id, roadmap_id, name, status) VALUES ('test-sprint', 'test-track', 'test-roadmap', 'Test Sprint', 'in_progress')")
    conn.execute("INSERT INTO tasks (id, sprint_id, roadmap_id, title, status) VALUES ('test-task', 'test-sprint', 'test-roadmap', 'Test Task', 'not_started')")

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


class TestAtomicMutation:
    """Test the atomic_mutation context manager."""

    def test_successful_transaction_commits(self, test_db):
        """Test that successful operations within atomic_mutation are committed."""
        conn = sqlite3.connect(test_db)

        with atomic_mutation(conn) as txn:
            txn.execute("UPDATE tasks SET status = 'in_progress' WHERE id = 'test-task'")

        # Verify change was committed
        result = conn.execute("SELECT status FROM tasks WHERE id = 'test-task'").fetchone()
        assert result[0] == "in_progress"
        conn.close()

    def test_exception_causes_rollback(self, test_db):
        """Test that exceptions within atomic_mutation cause rollback."""
        conn = sqlite3.connect(test_db)

        # Get initial state
        initial = conn.execute("SELECT status FROM tasks WHERE id = 'test-task'").fetchone()[0]

        try:
            with atomic_mutation(conn) as txn:
                txn.execute("UPDATE tasks SET status = 'in_progress' WHERE id = 'test-task'")
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Verify state was rolled back
        result = conn.execute("SELECT status FROM tasks WHERE id = 'test-task'").fetchone()
        assert result[0] == initial
        conn.close()

    def test_rollback_preserves_original_state(self, test_db):
        """Test that rollback preserves the exact original state."""
        conn = sqlite3.connect(test_db)

        # Set up known state
        conn.execute("UPDATE tasks SET status = 'not_started', blocked = 0 WHERE id = 'test-task'")
        conn.commit()

        try:
            with atomic_mutation(conn) as txn:
                txn.execute("UPDATE tasks SET status = 'in_progress', blocked = 1 WHERE id = 'test-task'")
                # Verify change is visible within transaction
                mid_result = txn.execute("SELECT status, blocked FROM tasks WHERE id = 'test-task'").fetchone()
                assert mid_result == ('in_progress', 1)
                raise RuntimeError("Simulated failure")
        except RuntimeError:
            pass

        # Verify state was fully rolled back
        result = conn.execute("SELECT status, blocked FROM tasks WHERE id = 'test-task'").fetchone()
        assert result == ('not_started', 0)
        conn.close()

    def test_multiple_operations_all_rollback(self, test_db):
        """Test that all operations rollback when error occurs late in transaction."""
        conn = sqlite3.connect(test_db)

        # Get initial states
        task_status = conn.execute("SELECT status FROM tasks WHERE id = 'test-task'").fetchone()[0]
        sprint_status = conn.execute("SELECT status FROM sprints WHERE id = 'test-sprint'").fetchone()[0]

        try:
            with atomic_mutation(conn) as txn:
                txn.execute("UPDATE tasks SET status = 'completed' WHERE id = 'test-task'")
                txn.execute("UPDATE sprints SET status = 'completed' WHERE id = 'test-sprint'")
                # Error after both updates
                raise Exception("Late failure")
        except Exception:
            pass

        # Verify both were rolled back
        result_task = conn.execute("SELECT status FROM tasks WHERE id = 'test-task'").fetchone()[0]
        result_sprint = conn.execute("SELECT status FROM sprints WHERE id = 'test-sprint'").fetchone()[0]
        assert result_task == task_status
        assert result_sprint == sprint_status
        conn.close()


class TestTaskTransactionRollback:
    """Test rollback behavior for task operations."""

    def test_update_task_status_rollback_on_activity_log_error(self, test_db):
        """Test that task update rolls back if activity log write fails."""
        conn = sqlite3.connect(test_db)

        initial_status = conn.execute("SELECT status FROM tasks WHERE id = 'test-task'").fetchone()[0]
        initial_log_count = conn.execute("SELECT COUNT(*) FROM activity_log").fetchone()[0]

        with patch('vibey.roadmap.database.transactions._log_activity') as mock_log:
            mock_log.side_effect = sqlite3.IntegrityError("Simulated log failure")

            with pytest.raises(sqlite3.IntegrityError):
                with patch('vibey.roadmap.database.transactions.get_connection', return_value=conn):
                    update_task_status('test-task', 'completed', 'test-actor', conn)

        # Verify task status unchanged
        result_status = conn.execute("SELECT status FROM tasks WHERE id = 'test-task'").fetchone()[0]
        assert result_status == initial_status

        # Verify no activity log entry was added
        result_log_count = conn.execute("SELECT COUNT(*) FROM activity_log").fetchone()[0]
        assert result_log_count == initial_log_count
        conn.close()

    def test_complete_task_not_found_raises_valueerror(self, test_db):
        """Test that completing nonexistent task raises ValueError."""
        conn = sqlite3.connect(test_db)

        with pytest.raises(ValueError, match="Task 'nonexistent' not found"):
            with patch('vibey.roadmap.database.transactions.get_connection', return_value=conn):
                complete_task('nonexistent', 'test-actor', conn)

        conn.close()

    def test_start_task_not_found_raises_valueerror(self, test_db):
        """Test that starting nonexistent task raises ValueError."""
        conn = sqlite3.connect(test_db)

        with pytest.raises(ValueError, match="Task 'nonexistent' not found"):
            with patch('vibey.roadmap.database.transactions.get_connection', return_value=conn):
                start_task('nonexistent', 'test-actor', conn)

        conn.close()


class TestSprintTransactionRollback:
    """Test rollback behavior for sprint operations."""

    def test_update_sprint_status_rollback_on_error(self, test_db):
        """Test that sprint update rolls back on error."""
        conn = sqlite3.connect(test_db)

        initial_status = conn.execute("SELECT status FROM sprints WHERE id = 'test-sprint'").fetchone()[0]

        with patch('vibey.roadmap.database.transactions._log_activity') as mock_log:
            mock_log.side_effect = sqlite3.IntegrityError("Simulated failure")

            with pytest.raises(sqlite3.IntegrityError):
                with patch('vibey.roadmap.database.transactions.get_connection', return_value=conn):
                    update_sprint_status('test-sprint', 'completed', 'test-actor', conn)

        result_status = conn.execute("SELECT status FROM sprints WHERE id = 'test-sprint'").fetchone()[0]
        assert result_status == initial_status
        conn.close()

    def test_complete_sprint_not_found_raises_valueerror(self, test_db):
        """Test that completing nonexistent sprint raises ValueError."""
        conn = sqlite3.connect(test_db)

        with pytest.raises(ValueError, match="Sprint 'nonexistent' not found"):
            with patch('vibey.roadmap.database.transactions.get_connection', return_value=conn):
                complete_sprint('nonexistent', 'test-actor', conn)

        conn.close()

    def test_start_sprint_not_found_raises_valueerror(self, test_db):
        """Test that starting nonexistent sprint raises ValueError."""
        conn = sqlite3.connect(test_db)

        with pytest.raises(ValueError, match="Sprint 'nonexistent' not found"):
            with patch('vibey.roadmap.database.transactions.get_connection', return_value=conn):
                start_sprint('nonexistent', 'test-actor', conn)

        conn.close()


class TestTrackTransactionRollback:
    """Test rollback behavior for track operations."""

    def test_update_track_status_rollback_on_error(self, test_db):
        """Test that track update rolls back on error."""
        conn = sqlite3.connect(test_db)

        initial_status = conn.execute("SELECT status FROM tracks WHERE id = 'test-track'").fetchone()[0]

        with patch('vibey.roadmap.database.transactions._log_activity') as mock_log:
            mock_log.side_effect = sqlite3.IntegrityError("Simulated failure")

            with pytest.raises(sqlite3.IntegrityError):
                with patch('vibey.roadmap.database.transactions.get_connection', return_value=conn):
                    update_track_status('test-track', 'completed', 'test-actor', conn)

        result_status = conn.execute("SELECT status FROM tracks WHERE id = 'test-track'").fetchone()[0]
        assert result_status == initial_status
        conn.close()

    def test_complete_track_not_found_raises_valueerror(self, test_db):
        """Test that completing nonexistent track raises ValueError."""
        conn = sqlite3.connect(test_db)

        with pytest.raises(ValueError, match="Track 'nonexistent' not found"):
            with patch('vibey.roadmap.database.transactions.get_connection', return_value=conn):
                complete_track('nonexistent', 'test-actor', conn)

        conn.close()

    def test_start_track_not_found_raises_valueerror(self, test_db):
        """Test that starting nonexistent track raises ValueError."""
        conn = sqlite3.connect(test_db)

        with pytest.raises(ValueError, match="Track 'nonexistent' not found"):
            with patch('vibey.roadmap.database.transactions.get_connection', return_value=conn):
                start_track('nonexistent', 'test-actor', conn)

        conn.close()


class TestStateHelpers:
    """Test the state retrieval helper functions."""

    def test_get_task_state_returns_dict(self, test_db):
        """Test _get_task_state returns proper dict."""
        conn = sqlite3.connect(test_db)
        state = _get_task_state(conn, 'test-task')

        assert isinstance(state, dict)
        assert 'id' in state
        assert 'status' in state
        assert 'blocked' in state
        assert state['id'] == 'test-task'
        conn.close()

    def test_get_task_state_returns_none_for_missing(self, test_db):
        """Test _get_task_state returns None for missing task."""
        conn = sqlite3.connect(test_db)
        state = _get_task_state(conn, 'nonexistent')
        assert state is None
        conn.close()

    def test_get_sprint_state_returns_dict(self, test_db):
        """Test _get_sprint_state returns proper dict."""
        conn = sqlite3.connect(test_db)
        state = _get_sprint_state(conn, 'test-sprint')

        assert isinstance(state, dict)
        assert 'id' in state
        assert 'status' in state
        assert state['id'] == 'test-sprint'
        conn.close()

    def test_get_sprint_state_returns_none_for_missing(self, test_db):
        """Test _get_sprint_state returns None for missing sprint."""
        conn = sqlite3.connect(test_db)
        state = _get_sprint_state(conn, 'nonexistent')
        assert state is None
        conn.close()

    def test_get_track_state_returns_dict(self, test_db):
        """Test _get_track_state returns proper dict."""
        conn = sqlite3.connect(test_db)
        state = _get_track_state(conn, 'test-track')

        assert isinstance(state, dict)
        assert 'id' in state
        assert 'status' in state
        assert state['id'] == 'test-track'
        conn.close()

    def test_get_track_state_returns_none_for_missing(self, test_db):
        """Test _get_track_state returns None for missing track."""
        conn = sqlite3.connect(test_db)
        state = _get_track_state(conn, 'nonexistent')
        assert state is None
        conn.close()


class TestActivityLogIntegrity:
    """Test activity log consistency during transactions."""

    def test_activity_log_entry_created_on_success(self, test_db):
        """Test that activity log entry is created when operation succeeds."""
        conn = sqlite3.connect(test_db)

        initial_count = conn.execute("SELECT COUNT(*) FROM activity_log").fetchone()[0]

        with atomic_mutation(conn) as txn:
            _log_activity(
                txn,
                roadmap_id='test-roadmap',
                event_type='test_event',
                event_description='Test event',
                entity_type='task',
                entity_id='test-task',
                actor='test',
            )

        final_count = conn.execute("SELECT COUNT(*) FROM activity_log").fetchone()[0]
        assert final_count == initial_count + 1
        conn.close()

    def test_activity_log_not_created_on_rollback(self, test_db):
        """Test that activity log entry is NOT created when transaction rolls back."""
        conn = sqlite3.connect(test_db)

        initial_count = conn.execute("SELECT COUNT(*) FROM activity_log").fetchone()[0]

        try:
            with atomic_mutation(conn) as txn:
                _log_activity(
                    txn,
                    roadmap_id='test-roadmap',
                    event_type='test_event',
                    event_description='Test event',
                    entity_type='task',
                    entity_id='test-task',
                    actor='test',
                )
                raise Exception("Force rollback")
        except Exception:
            pass

        final_count = conn.execute("SELECT COUNT(*) FROM activity_log").fetchone()[0]
        assert final_count == initial_count
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
