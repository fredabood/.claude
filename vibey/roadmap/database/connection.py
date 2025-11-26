"""
Database connection management for roadmap SQLite backend.

Provides connection management with:
- WAL mode for better concurrency
- Transaction context managers
- Busy timeout configuration
- Connection pooling (single connection per process)

The database file is stored at .vibey/roadmap.db
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Generator, Any

# Thread-local storage for connections
_local = threading.local()

# Default configuration
DEFAULT_DB_FILENAME = "roadmap.db"
DEFAULT_VIBEY_DIR = ".vibey"
DEFAULT_BUSY_TIMEOUT_MS = 5000  # 5 seconds
DEFAULT_CACHE_SIZE_KB = 2000  # 2MB cache


class DatabaseError(Exception):
    """Base exception for database errors."""
    pass


class ConnectionError(DatabaseError):
    """Error establishing database connection."""
    pass


class TransactionError(DatabaseError):
    """Error during database transaction."""
    pass


def get_db_path(base_dir: Optional[Path] = None) -> Path:
    """
    Get the path to the roadmap database file.

    Args:
        base_dir: Base directory containing .vibey folder.
                  If None, uses current working directory.

    Returns:
        Path to roadmap.db file
    """
    if base_dir is None:
        base_dir = Path.cwd()
    return base_dir / DEFAULT_VIBEY_DIR / DEFAULT_DB_FILENAME


def _configure_connection(conn: sqlite3.Connection) -> None:
    """
    Configure SQLite connection with optimal settings.

    Settings applied:
    - WAL mode for better read concurrency
    - Foreign keys enabled for referential integrity
    - Busy timeout to handle lock contention
    - Cache size for performance
    """
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")

    # Use WAL mode for better concurrency
    # WAL allows readers to not block writers and vice versa
    conn.execute("PRAGMA journal_mode = WAL")

    # Set busy timeout (milliseconds)
    conn.execute(f"PRAGMA busy_timeout = {DEFAULT_BUSY_TIMEOUT_MS}")

    # Set cache size (negative = KB, positive = pages)
    conn.execute(f"PRAGMA cache_size = -{DEFAULT_CACHE_SIZE_KB}")

    # Use normal synchronous mode (good balance of safety vs speed)
    conn.execute("PRAGMA synchronous = NORMAL")

    # Store temp tables in memory
    conn.execute("PRAGMA temp_store = MEMORY")


def get_connection(
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
    isolation_level: Optional[str] = None,
) -> sqlite3.Connection:
    """
    Get a database connection, creating one if needed.

    Uses thread-local storage to maintain one connection per thread.

    Args:
        db_path: Direct path to database file. If provided, base_dir is ignored.
        base_dir: Base directory containing .vibey folder.
        isolation_level: SQLite isolation level. None means autocommit,
                        'DEFERRED', 'IMMEDIATE', or 'EXCLUSIVE' for transactions.

    Returns:
        Configured SQLite connection

    Raises:
        ConnectionError: If database file doesn't exist and cannot be created
    """
    if db_path is None:
        db_path = get_db_path(base_dir)

    # Check if we already have a connection for this thread and path
    conn_key = str(db_path)
    if not hasattr(_local, 'connections'):
        _local.connections = {}

    if conn_key in _local.connections:
        conn = _local.connections[conn_key]
        # Verify connection is still valid
        try:
            conn.execute("SELECT 1")
            return conn
        except sqlite3.Error:
            # Connection is stale, remove it
            del _local.connections[conn_key]

    # Create new connection
    try:
        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.Connection(
            str(db_path),
            isolation_level=isolation_level,
            check_same_thread=False,  # We handle thread safety ourselves
        )

        # Enable row factory for dict-like access
        conn.row_factory = sqlite3.Row

        # Configure connection
        _configure_connection(conn)

        # Store in thread-local
        _local.connections[conn_key] = conn

        return conn

    except sqlite3.Error as e:
        raise ConnectionError(f"Failed to connect to database at {db_path}: {e}") from e


def close_connection(
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
) -> None:
    """
    Close the database connection for the current thread.

    Args:
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.
    """
    if db_path is None:
        db_path = get_db_path(base_dir)

    conn_key = str(db_path)
    if hasattr(_local, 'connections') and conn_key in _local.connections:
        try:
            _local.connections[conn_key].close()
        except sqlite3.Error:
            pass  # Ignore close errors
        del _local.connections[conn_key]


def close_all_connections() -> None:
    """Close all database connections for the current thread."""
    if hasattr(_local, 'connections'):
        for conn in _local.connections.values():
            try:
                conn.close()
            except sqlite3.Error:
                pass
        _local.connections.clear()


@contextmanager
def transaction(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
    isolation: str = "DEFERRED",
) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database transactions.

    Automatically commits on success, rolls back on exception.

    Args:
        conn: Existing connection to use. If None, gets/creates one.
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.
        isolation: Transaction isolation level ('DEFERRED', 'IMMEDIATE', 'EXCLUSIVE')

    Yields:
        Database connection within transaction

    Raises:
        TransactionError: If transaction fails

    Example:
        with transaction() as conn:
            conn.execute("INSERT INTO tasks ...")
            conn.execute("UPDATE sprints ...")
            # Commits automatically on exit
    """
    if conn is None:
        conn = get_connection(db_path=db_path, base_dir=base_dir)

    try:
        conn.execute(f"BEGIN {isolation}")
        yield conn
        conn.execute("COMMIT")
    except Exception as e:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass  # Ignore rollback errors

        if isinstance(e, sqlite3.Error):
            raise TransactionError(f"Transaction failed: {e}") from e
        raise


@contextmanager
def temporary_connection(
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for a temporary database connection.

    Unlike get_connection(), this creates a new connection that is
    automatically closed when the context exits. Useful for one-off
    operations that shouldn't reuse the thread-local connection.

    Args:
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.

    Yields:
        Configured SQLite connection
    """
    if db_path is None:
        db_path = get_db_path(base_dir)

    conn = None
    try:
        conn = sqlite3.Connection(str(db_path))
        conn.row_factory = sqlite3.Row
        _configure_connection(conn)
        yield conn
    finally:
        if conn:
            try:
                conn.close()
            except sqlite3.Error:
                pass


def database_exists(
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
) -> bool:
    """
    Check if the database file exists.

    Args:
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.

    Returns:
        True if database file exists
    """
    if db_path is None:
        db_path = get_db_path(base_dir)
    return db_path.exists()


def get_database_info(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
) -> dict[str, Any]:
    """
    Get information about the database.

    Args:
        conn: Existing connection to use.
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.

    Returns:
        Dictionary with database info:
        - path: Path to database file
        - size_bytes: File size
        - journal_mode: Current journal mode
        - foreign_keys: Foreign keys enabled
        - schema_version: Schema version (if set)
        - table_count: Number of tables
    """
    if db_path is None:
        db_path = get_db_path(base_dir)

    if conn is None:
        conn = get_connection(db_path=db_path)

    info: dict[str, Any] = {
        "path": str(db_path),
        "size_bytes": db_path.stat().st_size if db_path.exists() else 0,
    }

    # Get pragma values
    for pragma in ["journal_mode", "foreign_keys"]:
        result = conn.execute(f"PRAGMA {pragma}").fetchone()
        info[pragma] = result[0] if result else None

    # Get table count
    result = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchone()
    info["table_count"] = result[0] if result else 0

    # Try to get schema version from database_state table
    try:
        result = conn.execute(
            "SELECT schema_version FROM database_state WHERE id = 1"
        ).fetchone()
        info["schema_version"] = result[0] if result else None
    except sqlite3.Error:
        info["schema_version"] = None

    return info
