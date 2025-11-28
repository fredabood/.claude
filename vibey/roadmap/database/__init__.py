"""
SQLite database backend for Vibey roadmap system.

This module provides a SQLite-based storage backend for the roadmap system,
replacing YAML as the working state while maintaining YAML as the version-
controlled artifact.

Key Benefits:
- Automatic consistency via computed views (no manual counter updates)
- Referential integrity via foreign keys
- Atomic operations via transactions
- Fast queries via indexes
- Validation enforcement via triggers

Architecture:
- SQLite is the source of truth for all writes
- YAML is a read-only artifact for git versioning
- Pre-commit hook dumps DB to YAML
- Post-merge hook rebuilds DB from YAML

Database Location:
- Default: .vibey/roadmap.db

Usage:
    from vibey.roadmap.database import get_connection, transaction

    # Get a connection (reuses thread-local connection)
    conn = get_connection()

    # Use transactions for writes
    with transaction() as conn:
        conn.execute("INSERT INTO tasks ...")

    # Check database info
    info = get_database_info()
    print(f"Tables: {info['table_count']}")

Modules:
- connection: Connection management with WAL mode
- schema: Schema DDL and creation
- crud/: CRUD operations for entities
- views: Computed views for automatic aggregations
- sync/: YAML synchronization

Schema Version: 1.0.0
"""

from .connection import (
    # Connection management
    get_connection,
    close_connection,
    close_all_connections,
    get_db_path,
    database_exists,
    get_database_info,
    # Context managers
    transaction,
    temporary_connection,
    # Exceptions
    DatabaseError,
    ConnectionError,
    TransactionError,
    # Constants
    DEFAULT_DB_FILENAME,
    DEFAULT_VIBEY_DIR,
    DEFAULT_BUSY_TIMEOUT_MS,
)

from .schema import (
    SCHEMA_VERSION,
    EXPECTED_TABLES,
    create_schema,
    schema_exists,
    get_schema_version,
    drop_all_tables,
    get_schema_ddl,
    get_index_ddl,
    get_table_names,
    get_index_names,
    validate_schema,
)

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

from .triggers import (
    TRIGGER_DEFINITIONS,
    TRIGGER_ORDER,
    TRIGGER_CATEGORIES,
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

from .compare_databases import (
    compare_databases,
    compare_declared_counters,
    compare_relationships,
    compare_json_columns,
    find_true_gaps,
    ComparisonReport,
    CategoryReport,
    ComparisonResult,
    ColumnMapping,
)

__all__ = [
    # Connection management
    "get_connection",
    "close_connection",
    "close_all_connections",
    "get_db_path",
    "database_exists",
    "get_database_info",
    # Context managers
    "transaction",
    "temporary_connection",
    # Exceptions
    "DatabaseError",
    "ConnectionError",
    "TransactionError",
    # Schema
    "SCHEMA_VERSION",
    "EXPECTED_TABLES",
    "create_schema",
    "schema_exists",
    "get_schema_version",
    "drop_all_tables",
    "get_schema_ddl",
    "get_index_ddl",
    "get_table_names",
    "get_index_names",
    "validate_schema",
    # Views
    "VIEW_DEFINITIONS",
    "VIEW_ORDER",
    "create_views",
    "drop_views",
    "view_exists",
    "get_view_names",
    "get_sprint_progress",
    "get_track_progress",
    "get_roadmap_progress",
    "get_blocked_entities",
    "get_unblocked_tasks",
    "get_dependency_chain",
    "get_quality_gate_summary",
    "get_failing_quality_gates",
    "get_recent_activity",
    "get_velocity_metrics",
    "get_all_progress",
    # Triggers
    "TRIGGER_DEFINITIONS",
    "TRIGGER_ORDER",
    "TRIGGER_CATEGORIES",
    "create_triggers",
    "drop_triggers",
    "trigger_exists",
    "get_trigger_names",
    "get_triggers_by_category",
    "validate_triggers",
    "disable_triggers_for_bulk_operations",
    "enable_triggers_for_bulk_operations",
    "rebuild_summary_tables",
    # Constants
    "DEFAULT_DB_FILENAME",
    "DEFAULT_VIBEY_DIR",
    "DEFAULT_BUSY_TIMEOUT_MS",
    # Comparison
    "compare_databases",
    "compare_declared_counters",
    "compare_relationships",
    "compare_json_columns",
    "find_true_gaps",
    "ComparisonReport",
    "CategoryReport",
    "ComparisonResult",
    "ColumnMapping",
]
