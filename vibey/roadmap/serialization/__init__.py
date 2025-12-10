"""
Serialization module for roadmap objects.

Handles YAML and SQLite I/O and conversion between storage formats and Python objects.

Backends:
- YAMLBackend: Traditional file-based storage (read/write YAML files)
- SQLiteBackend: Database-based storage (read/write SQLite database)
- SyncManager: Bidirectional sync between YAML and SQLite

Usage:
    # Use default backend (YAML for now, SQLite when available)
    from vibey.roadmap.serialization import get_default_backend

    backend = get_default_backend()
    roadmap = backend.load_roadmap()
    backend.save_roadmap(roadmap)

    # Use specific backend
    from vibey.roadmap.serialization import YAMLBackend, SQLiteBackend

    yaml_backend = YAMLBackend(".vibey/roadmap")
    sqlite_backend = SQLiteBackend(".vibey/roadmap.db")

    # Sync between backends
    from vibey.roadmap.serialization import SyncManager

    sync = SyncManager()
    sync.rebuild()  # YAML → SQLite
    sync.dump()     # SQLite → YAML
"""

# YAML serialization (traditional)
from .yaml_loader import (
    load_roadmap,
    load_track,
    load_sprint,
    load_tasks,
    load_task,
)

from .yaml_dumper import (
    save_roadmap,
    save_track,
    save_sprint,
    save_task,
    save_tasks,
)

# SQL serialization - optional (requires SQLAlchemy)
_SQL_AVAILABLE = False
try:
    from .sql_loader import (
        load_roadmap as sql_load_roadmap,
        load_track as sql_load_track,
        load_sprint as sql_load_sprint,
        load_task as sql_load_task,
        load_tasks_by_sprint as sql_load_tasks_by_sprint,
        load_tasks_by_track as sql_load_tasks_by_track,
        load_all_tasks as sql_load_all_tasks,
    )

    from .sql_dumper import (
        save_roadmap as sql_save_roadmap,
        save_track as sql_save_track,
        save_sprint as sql_save_sprint,
        save_task as sql_save_task,
        save_tasks as sql_save_tasks,
        save_full_roadmap as sql_save_full_roadmap,
    )

    from .backend import (
        # Protocol and backends
        RoadmapBackend,
        YAMLBackend,
        SQLiteBackend,
        SyncManager,
        get_default_backend,
        # Exceptions
        BackendError,
        YAMLModifiedError,
        DirtyDatabaseError,
        SchemaMismatchError,
    )
    _SQL_AVAILABLE = True
except ImportError:
    # SQLAlchemy not installed - SQL features unavailable
    sql_load_roadmap = None
    sql_load_track = None
    sql_load_sprint = None
    sql_load_task = None
    sql_load_tasks_by_sprint = None
    sql_load_tasks_by_track = None
    sql_load_all_tasks = None
    sql_save_roadmap = None
    sql_save_track = None
    sql_save_sprint = None
    sql_save_task = None
    sql_save_tasks = None
    sql_save_full_roadmap = None
    RoadmapBackend = None
    YAMLBackend = None
    SQLiteBackend = None
    SyncManager = None
    get_default_backend = None
    BackendError = None
    YAMLModifiedError = None
    DirtyDatabaseError = None
    SchemaMismatchError = None


def require_sql_backend():
    """Raise ImportError with helpful message if SQL backend is not available."""
    if not _SQL_AVAILABLE:
        raise ImportError(
            "SQLAlchemy is required for SQL/database functionality. "
            "Install with: pip install sqlalchemy"
        )

__all__ = [
    # SQL availability check
    "_SQL_AVAILABLE",
    "require_sql_backend",
    # YAML Loaders (default)
    "load_roadmap",
    "load_track",
    "load_sprint",
    "load_tasks",
    "load_task",
    # YAML Dumpers (default)
    "save_roadmap",
    "save_track",
    "save_sprint",
    "save_tasks",
    # SQL Loaders (prefixed)
    "sql_load_roadmap",
    "sql_load_track",
    "sql_load_sprint",
    "sql_load_task",
    "sql_load_tasks_by_sprint",
    "sql_load_tasks_by_track",
    "sql_load_all_tasks",
    # SQL Dumpers (prefixed)
    "sql_save_roadmap",
    "sql_save_track",
    "sql_save_sprint",
    "sql_save_task",
    "sql_save_tasks",
    "sql_save_full_roadmap",
    # Backend abstraction
    "RoadmapBackend",
    "YAMLBackend",
    "SQLiteBackend",
    "SyncManager",
    "get_default_backend",
    # Exceptions
    "BackendError",
    "YAMLModifiedError",
    "DirtyDatabaseError",
    "SchemaMismatchError",
]
