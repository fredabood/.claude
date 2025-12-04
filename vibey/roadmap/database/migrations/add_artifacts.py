"""
Migration: Add artifacts table to database schema.

This migration adds the artifacts table and related indexes to support
the artifact system for tracking code, documentation, and other files.

Design reference: UNIFIED_TICKET_ARCHITECTURE.md Part 13.9

Usage:
    python -m vibey.roadmap.database.migrations.add_artifacts [--db-path PATH]

Or programmatically:
    from vibey.roadmap.database.migrations.add_artifacts import migrate
    migrate(conn)
"""

import sqlite3
from pathlib import Path
from typing import Optional


MIGRATION_NAME = "add_artifacts"
MIGRATION_VERSION = "1.1.0"  # Schema version after migration


def get_artifacts_table_ddl() -> str:
    """Get DDL for the artifacts table."""
    return """
-- 27. artifacts
-- First-class artifact entities for tracking code, docs, configs, etc.
-- Design reference: UNIFIED_TICKET_ARCHITECTURE.md Part 13.9
CREATE TABLE IF NOT EXISTS artifacts (
    -- Identity
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,

    -- File Location
    paths TEXT NOT NULL,  -- JSON array of file paths
    content_hash TEXT,
    last_verified TEXT,  -- ISO timestamp

    -- Classification
    artifact_type TEXT NOT NULL CHECK (artifact_type IN (
        'code', 'test', 'config', 'documentation', 'context',
        'agent', 'workflow', 'template', 'data', 'asset', 'schema', 'other'
    )),
    artifact_subtype TEXT,

    -- Provenance (JSON object with provenance_type and related fields)
    provenance TEXT NOT NULL,

    -- Relationships
    documents_artifact_id TEXT,  -- FK to artifact this documents
    depends_on_artifact_ids TEXT,  -- JSON array of artifact IDs

    -- State
    file_exists INTEGER NOT NULL DEFAULT 1,
    is_stale INTEGER NOT NULL DEFAULT 0,

    -- Staleness tracking (for documentation artifacts)
    documented_source_hash TEXT,

    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    -- Foreign keys
    FOREIGN KEY (documents_artifact_id) REFERENCES artifacts(id)
);
"""


def get_artifacts_indexes_ddl() -> str:
    """Get DDL for artifacts indexes."""
    return """
-- Artifact type for filtering by category
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(artifact_type);

-- Documentation relationships (documents_artifact_id)
CREATE INDEX IF NOT EXISTS idx_artifacts_documents ON artifacts(documents_artifact_id);

-- Stale artifacts (partial index for efficient staleness queries)
CREATE INDEX IF NOT EXISTS idx_artifacts_stale ON artifacts(is_stale) WHERE is_stale = 1;

-- Artifact existence (for filtering existing vs deleted)
CREATE INDEX IF NOT EXISTS idx_artifacts_exists ON artifacts(file_exists) WHERE file_exists = 1;
"""


def get_artifacts_views_ddl() -> str:
    """
    Get DDL for artifact views.

    Note: Views v_orphan_artifacts and v_artifact_criteria require the
    criteria table from the unified ticket schema. They will fail to
    create if that table doesn't exist.
    """
    return """
-- 1. v_orphan_artifacts
-- Artifacts that exist but are not referenced by any criterion
-- Note: Requires criteria table from unified ticket schema
CREATE VIEW IF NOT EXISTS v_orphan_artifacts AS
SELECT a.*
FROM artifacts a
WHERE a.file_exists = 1
  AND NOT EXISTS (
    SELECT 1 FROM criteria c
    WHERE c.target_type = 'artifact'
      AND json_extract(c.target_data, '$.artifact_id') = a.id
  );

-- 2. v_documentation_graph
-- Links between documentation artifacts and their source artifacts
CREATE VIEW IF NOT EXISTS v_documentation_graph AS
SELECT
    doc.id AS doc_id,
    doc.name AS doc_name,
    doc.artifact_type AS doc_type,
    doc.is_stale,
    src.id AS source_id,
    src.name AS source_name,
    src.artifact_type AS source_type,
    src.content_hash AS source_hash,
    doc.documented_source_hash AS documented_hash,
    CASE
        WHEN src.content_hash IS NOT NULL
             AND doc.documented_source_hash IS NOT NULL
             AND src.content_hash != doc.documented_source_hash THEN 1
        ELSE 0
    END AS needs_update
FROM artifacts doc
JOIN artifacts src ON doc.documents_artifact_id = src.id
WHERE doc.documents_artifact_id IS NOT NULL;

-- 3. v_stale_documentation
-- Documentation artifacts that need updating
CREATE VIEW IF NOT EXISTS v_stale_documentation AS
SELECT * FROM v_documentation_graph
WHERE needs_update = 1 OR is_stale = 1;

-- 4. v_artifact_criteria
-- Which criteria reference each artifact
-- Note: Requires criteria table from unified ticket schema
CREATE VIEW IF NOT EXISTS v_artifact_criteria AS
SELECT
    a.id AS artifact_id,
    a.name AS artifact_name,
    a.artifact_type,
    c.id AS criterion_id,
    c.description AS criterion_description,
    c.ticket_id,
    c.blocks_transition_to
FROM artifacts a
JOIN criteria c ON json_extract(c.target_data, '$.artifact_id') = a.id
WHERE c.target_type = 'artifact'
  AND a.file_exists = 1;
"""


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """Check if a table exists in the database."""
    result = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    ).fetchone()
    return result is not None


def migrate(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    create_views: bool = False,
) -> dict:
    """
    Run the migration to add the artifacts table.

    Args:
        conn: Existing database connection.
        db_path: Path to database file (used if conn not provided).
        create_views: Whether to create artifact views. Views that reference
            the criteria table will fail if that table doesn't exist.

    Returns:
        dict with migration results:
        - success: True if migration succeeded
        - already_exists: True if table already existed
        - table_created: True if table was created
        - indexes_created: True if indexes were created
        - views_created: True if views were created (only if create_views=True)
        - error: Error message if any
    """
    result = {
        "success": False,
        "already_exists": False,
        "table_created": False,
        "indexes_created": False,
        "views_created": False,
        "error": None,
    }

    close_conn = False
    if conn is None:
        if db_path is None:
            result["error"] = "Either conn or db_path must be provided"
            return result
        conn = sqlite3.connect(db_path)
        close_conn = True

    try:
        # Check if table already exists
        if table_exists(conn, "artifacts"):
            result["already_exists"] = True
            result["success"] = True
            return result

        # Create the table
        conn.executescript(get_artifacts_table_ddl())
        result["table_created"] = True

        # Create indexes
        conn.executescript(get_artifacts_indexes_ddl())
        result["indexes_created"] = True

        # Optionally create views
        if create_views:
            try:
                # Try self-contained views first
                conn.execute("""
                    CREATE VIEW IF NOT EXISTS v_documentation_graph AS
                    SELECT
                        doc.id AS doc_id,
                        doc.name AS doc_name,
                        doc.artifact_type AS doc_type,
                        doc.is_stale,
                        src.id AS source_id,
                        src.name AS source_name,
                        src.artifact_type AS source_type,
                        src.content_hash AS source_hash,
                        doc.documented_source_hash AS documented_hash,
                        CASE
                            WHEN src.content_hash IS NOT NULL
                                 AND doc.documented_source_hash IS NOT NULL
                                 AND src.content_hash != doc.documented_source_hash THEN 1
                            ELSE 0
                        END AS needs_update
                    FROM artifacts doc
                    JOIN artifacts src ON doc.documents_artifact_id = src.id
                    WHERE doc.documents_artifact_id IS NOT NULL
                """)
                conn.execute("""
                    CREATE VIEW IF NOT EXISTS v_stale_documentation AS
                    SELECT * FROM v_documentation_graph
                    WHERE needs_update = 1 OR is_stale = 1
                """)
                result["views_created"] = True

                # Try views that need criteria table
                if table_exists(conn, "criteria"):
                    conn.executescript(get_artifacts_views_ddl())
            except sqlite3.OperationalError as e:
                # Views that require criteria table may fail - that's ok
                result["error"] = f"Some views not created: {e}"

        conn.commit()
        result["success"] = True

    except sqlite3.Error as e:
        result["error"] = str(e)
        if not close_conn:
            conn.rollback()

    finally:
        if close_conn:
            conn.close()

    return result


def rollback(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> dict:
    """
    Roll back the migration by dropping the artifacts table.

    WARNING: This will delete all artifact data.

    Args:
        conn: Existing database connection.
        db_path: Path to database file (used if conn not provided).

    Returns:
        dict with rollback results:
        - success: True if rollback succeeded
        - error: Error message if any
    """
    result = {
        "success": False,
        "error": None,
    }

    close_conn = False
    if conn is None:
        if db_path is None:
            result["error"] = "Either conn or db_path must be provided"
            return result
        conn = sqlite3.connect(db_path)
        close_conn = True

    try:
        # Drop views first (they depend on the table)
        conn.execute("DROP VIEW IF EXISTS v_artifact_criteria")
        conn.execute("DROP VIEW IF EXISTS v_stale_documentation")
        conn.execute("DROP VIEW IF EXISTS v_documentation_graph")
        conn.execute("DROP VIEW IF EXISTS v_orphan_artifacts")

        # Drop the table (indexes are dropped automatically)
        conn.execute("DROP TABLE IF EXISTS artifacts")

        conn.commit()
        result["success"] = True

    except sqlite3.Error as e:
        result["error"] = str(e)
        if not close_conn:
            conn.rollback()

    finally:
        if close_conn:
            conn.close()

    return result


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Add artifacts table to roadmap database"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        help="Path to database file",
    )
    parser.add_argument(
        "--create-views",
        action="store_true",
        help="Create artifact views (requires criteria table for some views)",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Roll back the migration (drop artifacts table)",
    )

    args = parser.parse_args()

    if args.db_path is None:
        # Try default location
        default_path = Path(".vibey/roadmap/roadmap.db")
        if default_path.exists():
            args.db_path = default_path
        else:
            print("Error: --db-path required (no default found)", file=sys.stderr)
            sys.exit(1)

    if args.rollback:
        result = rollback(db_path=args.db_path)
        action = "Rollback"
    else:
        result = migrate(db_path=args.db_path, create_views=args.create_views)
        action = "Migration"

    if result["success"]:
        print(f"{action} successful!")
        if result.get("already_exists"):
            print("  - Table already existed")
        if result.get("table_created"):
            print("  - Table created")
        if result.get("indexes_created"):
            print("  - Indexes created")
        if result.get("views_created"):
            print("  - Views created")
        if result.get("error"):
            print(f"  - Warning: {result['error']}")
    else:
        print(f"{action} failed: {result['error']}", file=sys.stderr)
        sys.exit(1)
