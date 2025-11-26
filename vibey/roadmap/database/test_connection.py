"""
Unit tests for database connection management.

Tests:
- Connection creation and configuration
- WAL mode and foreign keys
- Transaction context manager
- Thread-local connection reuse
- Error handling
"""

import os
import sqlite3
import tempfile
import threading
import pytest
from pathlib import Path
from unittest.mock import patch

from vibey.roadmap.database.connection import (
    get_db_path,
    get_connection,
    close_connection,
    close_all_connections,
    transaction,
    temporary_connection,
    database_exists,
    get_database_info,
    DatabaseError,
    ConnectionError,
    TransactionError,
    DEFAULT_DB_FILENAME,
    DEFAULT_VIBEY_DIR,
    _local,
)


@pytest.fixture
def temp_db_dir():
    """Create a temporary directory for test databases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vibey_dir = Path(tmpdir) / DEFAULT_VIBEY_DIR
        vibey_dir.mkdir()
        yield Path(tmpdir)
        # Clean up connections
        close_all_connections()


class TestGetDbPath:
    """Tests for get_db_path function."""

    def test_default_path_uses_cwd(self):
        """get_db_path with no args uses current working directory."""
        expected = Path.cwd() / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        assert get_db_path() == expected

    def test_custom_base_dir(self, temp_db_dir):
        """get_db_path with base_dir uses that directory."""
        expected = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        assert get_db_path(base_dir=temp_db_dir) == expected


class TestGetConnection:
    """Tests for get_connection function."""

    def test_creates_connection(self, temp_db_dir):
        """get_connection creates a new connection."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        conn = get_connection(db_path=db_path)

        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)

    def test_creates_parent_directory(self, temp_db_dir):
        """get_connection creates parent directory if needed."""
        # Remove the .vibey directory
        vibey_dir = temp_db_dir / DEFAULT_VIBEY_DIR
        vibey_dir.rmdir()

        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        conn = get_connection(db_path=db_path)

        assert vibey_dir.exists()
        assert conn is not None

    def test_reuses_connection(self, temp_db_dir):
        """get_connection returns same connection for same path."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        conn1 = get_connection(db_path=db_path)
        conn2 = get_connection(db_path=db_path)

        assert conn1 is conn2

    def test_different_paths_different_connections(self, temp_db_dir):
        """get_connection returns different connections for different paths."""
        db_path1 = temp_db_dir / DEFAULT_VIBEY_DIR / "db1.db"
        db_path2 = temp_db_dir / DEFAULT_VIBEY_DIR / "db2.db"

        conn1 = get_connection(db_path=db_path1)
        conn2 = get_connection(db_path=db_path2)

        assert conn1 is not conn2

    def test_configures_wal_mode(self, temp_db_dir):
        """Connection is configured with WAL journal mode."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        conn = get_connection(db_path=db_path)

        result = conn.execute("PRAGMA journal_mode").fetchone()
        assert result[0] == "wal"

    def test_configures_foreign_keys(self, temp_db_dir):
        """Connection has foreign keys enabled."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        conn = get_connection(db_path=db_path)

        result = conn.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1

    def test_row_factory_returns_row(self, temp_db_dir):
        """Connection row factory returns sqlite3.Row objects."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        conn = get_connection(db_path=db_path)

        conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO test VALUES (1, 'foo')")
        row = conn.execute("SELECT * FROM test").fetchone()

        assert row["id"] == 1
        assert row["name"] == "foo"


class TestCloseConnection:
    """Tests for close_connection function."""

    def test_closes_connection(self, temp_db_dir):
        """close_connection closes the connection."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        conn = get_connection(db_path=db_path)

        close_connection(db_path=db_path)

        # Connection should be removed from thread-local
        assert str(db_path) not in getattr(_local, 'connections', {})

    def test_new_connection_after_close(self, temp_db_dir):
        """get_connection returns new connection after close."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        conn1 = get_connection(db_path=db_path)
        close_connection(db_path=db_path)
        conn2 = get_connection(db_path=db_path)

        assert conn1 is not conn2


class TestTransaction:
    """Tests for transaction context manager."""

    def test_commits_on_success(self, temp_db_dir):
        """Transaction commits on successful exit."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        conn = get_connection(db_path=db_path)
        conn.execute("CREATE TABLE test (id INTEGER)")

        with transaction(conn) as txn:
            txn.execute("INSERT INTO test VALUES (1)")

        # Data should be persisted
        result = conn.execute("SELECT COUNT(*) FROM test").fetchone()
        assert result[0] == 1

    def test_rolls_back_on_exception(self, temp_db_dir):
        """Transaction rolls back on exception."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        conn = get_connection(db_path=db_path)
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.execute("INSERT INTO test VALUES (0)")  # Pre-existing row

        with pytest.raises(ValueError):
            with transaction(conn) as txn:
                txn.execute("INSERT INTO test VALUES (1)")
                raise ValueError("Test error")

        # Only pre-existing row should exist
        result = conn.execute("SELECT COUNT(*) FROM test").fetchone()
        assert result[0] == 1

    def test_creates_connection_if_none(self, temp_db_dir):
        """Transaction creates connection if not provided."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME

        with transaction(db_path=db_path) as conn:
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.execute("INSERT INTO test VALUES (1)")

        # Verify data persisted
        conn = get_connection(db_path=db_path)
        result = conn.execute("SELECT COUNT(*) FROM test").fetchone()
        assert result[0] == 1

    def test_wraps_sqlite_error(self, temp_db_dir):
        """TransactionError wraps sqlite3.Error."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME

        with pytest.raises(TransactionError):
            with transaction(db_path=db_path) as conn:
                # This will fail - table doesn't exist
                conn.execute("INSERT INTO nonexistent VALUES (1)")


class TestTemporaryConnection:
    """Tests for temporary_connection context manager."""

    def test_creates_new_connection(self, temp_db_dir):
        """temporary_connection creates a new connection."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME

        with temporary_connection(db_path=db_path) as conn:
            assert conn is not None
            conn.execute("SELECT 1")

    def test_closes_on_exit(self, temp_db_dir):
        """temporary_connection closes connection on exit."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME

        with temporary_connection(db_path=db_path) as conn:
            pass

        # Connection should be closed (can't execute)
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")

    def test_different_from_reused_connection(self, temp_db_dir):
        """temporary_connection is different from get_connection."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        reused = get_connection(db_path=db_path)

        with temporary_connection(db_path=db_path) as temp:
            assert temp is not reused


class TestDatabaseExists:
    """Tests for database_exists function."""

    def test_returns_false_when_not_exists(self, temp_db_dir):
        """database_exists returns False when file doesn't exist."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / "nonexistent.db"
        assert database_exists(db_path=db_path) is False

    def test_returns_true_when_exists(self, temp_db_dir):
        """database_exists returns True when file exists."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        # Create the database by connecting
        get_connection(db_path=db_path)

        assert database_exists(db_path=db_path) is True


class TestGetDatabaseInfo:
    """Tests for get_database_info function."""

    def test_returns_info_dict(self, temp_db_dir):
        """get_database_info returns dictionary with expected keys."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        conn = get_connection(db_path=db_path)

        info = get_database_info(conn=conn)

        assert "path" in info
        assert "size_bytes" in info
        assert "journal_mode" in info
        assert "foreign_keys" in info
        assert "table_count" in info

    def test_journal_mode_is_wal(self, temp_db_dir):
        """get_database_info shows WAL journal mode."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        conn = get_connection(db_path=db_path)

        info = get_database_info(conn=conn)

        assert info["journal_mode"] == "wal"

    def test_counts_tables(self, temp_db_dir):
        """get_database_info counts user tables."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        conn = get_connection(db_path=db_path)
        conn.execute("CREATE TABLE test1 (id INTEGER)")
        conn.execute("CREATE TABLE test2 (id INTEGER)")

        info = get_database_info(conn=conn)

        assert info["table_count"] == 2


class TestThreadSafety:
    """Tests for thread safety of connections."""

    def test_different_threads_different_connections(self, temp_db_dir):
        """Different threads get different connections."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        connections = []

        def get_conn():
            conn = get_connection(db_path=db_path)
            connections.append(id(conn))
            close_connection(db_path=db_path)

        threads = [threading.Thread(target=get_conn) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Each thread should have gotten a different connection
        assert len(set(connections)) == 3


class TestDbPathFromBaseDir:
    """Tests for using base_dir to derive db_path."""

    def test_get_connection_with_base_dir(self, temp_db_dir):
        """get_connection resolves db_path from base_dir."""
        conn = get_connection(base_dir=temp_db_dir)
        assert conn is not None
        expected_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        assert expected_path.exists()

    def test_close_connection_with_base_dir(self, temp_db_dir):
        """close_connection resolves db_path from base_dir."""
        get_connection(base_dir=temp_db_dir)
        close_connection(base_dir=temp_db_dir)
        expected_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        assert str(expected_path) not in getattr(_local, 'connections', {})

    def test_temporary_connection_with_base_dir(self, temp_db_dir):
        """temporary_connection resolves db_path from base_dir."""
        with temporary_connection(base_dir=temp_db_dir) as conn:
            assert conn is not None
            conn.execute("SELECT 1")

    def test_database_exists_with_base_dir(self, temp_db_dir):
        """database_exists resolves db_path from base_dir."""
        assert database_exists(base_dir=temp_db_dir) is False
        get_connection(base_dir=temp_db_dir)
        assert database_exists(base_dir=temp_db_dir) is True

    def test_get_database_info_creates_connection(self, temp_db_dir):
        """get_database_info creates connection when not provided."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        # Create the database first
        get_connection(db_path=db_path)
        close_connection(db_path=db_path)

        # Call without conn, should create connection
        info = get_database_info(db_path=db_path)
        assert info is not None
        assert info["path"] == str(db_path)

    def test_get_database_info_with_base_dir(self, temp_db_dir):
        """get_database_info resolves db_path from base_dir."""
        # Create database first
        get_connection(base_dir=temp_db_dir)

        info = get_database_info(base_dir=temp_db_dir)
        expected_path = str(temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME)
        assert info["path"] == expected_path


class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_close_connection_handles_close_error(self, temp_db_dir):
        """close_connection handles errors during close gracefully."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        conn = get_connection(db_path=db_path)

        # Close the connection manually to cause an error
        conn.close()

        # This should not raise an error
        close_connection(db_path=db_path)

    def test_close_all_connections_handles_errors(self, temp_db_dir):
        """close_all_connections handles errors during close gracefully."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        conn = get_connection(db_path=db_path)

        # Close the connection manually to cause an error
        conn.close()

        # This should not raise an error
        close_all_connections()

    def test_transaction_rollback_handles_errors(self, temp_db_dir):
        """Transaction handles rollback errors gracefully."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME

        # We can't easily trigger a rollback error, but we can verify
        # that non-sqlite errors are re-raised
        with pytest.raises(ValueError, match="Test error"):
            with transaction(db_path=db_path) as conn:
                conn.execute("CREATE TABLE test (id INTEGER)")
                raise ValueError("Test error")

    def test_temporary_connection_handles_close_error(self, temp_db_dir):
        """temporary_connection handles close errors gracefully."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME

        # Create a connection that will be closed
        with temporary_connection(db_path=db_path) as conn:
            # Manually close to cause error on context exit
            conn.close()
        # Should not raise

    def test_get_connection_stale_connection_recovery(self, temp_db_dir):
        """get_connection recovers from stale connections."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME
        conn1 = get_connection(db_path=db_path)

        # Close the connection manually, making it stale
        conn1.close()

        # Getting connection again should create a new one
        conn2 = get_connection(db_path=db_path)
        assert conn2 is not conn1
        # Verify new connection works
        conn2.execute("SELECT 1")
