"""
Migration: Add token tracking columns to tickets table.

This migration adds columns for the Robust Token Estimation System:
- Input token fields (estimate min/max/target, budget, usage, enforcement)
- Output token fields (estimate min/max/target, budget, usage, enforcement)
- Total/combined token fields (budget, enforcement)

Design reference: Token Estimation Track Sprint 1 - Data Model Updates

Usage:
    python -m vibey.roadmap.database.migrations.add_token_columns [--db-path PATH]

Or programmatically:
    from vibey.roadmap.database.migrations.add_token_columns import migrate
    migrate(conn)
"""

import sqlite3
from pathlib import Path
from typing import Optional


MIGRATION_NAME = "add_token_columns"
MIGRATION_VERSION = "1.2.0"  # Schema version after migration


def get_token_columns_ddl() -> str:
    """Get DDL for adding token columns to tickets table."""
    return """
-- Token Tracking columns for tickets table (v2 - Robust Token Estimation System)

-- Input token fields
ALTER TABLE tickets ADD COLUMN input_tokens_estimate_min INTEGER;
ALTER TABLE tickets ADD COLUMN input_tokens_estimate_max INTEGER;
ALTER TABLE tickets ADD COLUMN input_tokens_estimate_target INTEGER;
ALTER TABLE tickets ADD COLUMN input_tokens_budget INTEGER;
ALTER TABLE tickets ADD COLUMN input_tokens_usage INTEGER;
ALTER TABLE tickets ADD COLUMN input_tokens_enforcement TEXT;  -- JSON for TokenEnforcement

-- Output token fields
ALTER TABLE tickets ADD COLUMN output_tokens_estimate_min INTEGER;
ALTER TABLE tickets ADD COLUMN output_tokens_estimate_max INTEGER;
ALTER TABLE tickets ADD COLUMN output_tokens_estimate_target INTEGER;
ALTER TABLE tickets ADD COLUMN output_tokens_budget INTEGER;
ALTER TABLE tickets ADD COLUMN output_tokens_usage INTEGER;
ALTER TABLE tickets ADD COLUMN output_tokens_enforcement TEXT;  -- JSON for TokenEnforcement

-- Combined/total token fields
ALTER TABLE tickets ADD COLUMN total_token_budget INTEGER;
ALTER TABLE tickets ADD COLUMN total_token_enforcement TEXT;  -- JSON for TokenEnforcement
"""


def column_exists(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    result = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()
    column_names = [row[1] for row in result]
    return column_name in column_names


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
) -> dict:
    """
    Run the migration to add token columns to tickets table.

    Args:
        conn: Existing database connection.
        db_path: Path to database file (used if conn not provided).

    Returns:
        dict with migration results:
        - success: True if migration succeeded
        - already_exists: True if columns already existed
        - columns_added: List of columns added
        - error: Error message if any
    """
    result = {
        "success": False,
        "already_exists": False,
        "columns_added": [],
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
        # Check if tickets table exists
        if not table_exists(conn, "tickets"):
            result["error"] = "tickets table does not exist"
            return result

        # Define the columns to add
        columns = [
            ("input_tokens_estimate_min", "INTEGER"),
            ("input_tokens_estimate_max", "INTEGER"),
            ("input_tokens_estimate_target", "INTEGER"),
            ("input_tokens_budget", "INTEGER"),
            ("input_tokens_usage", "INTEGER"),
            ("input_tokens_enforcement", "TEXT"),
            ("output_tokens_estimate_min", "INTEGER"),
            ("output_tokens_estimate_max", "INTEGER"),
            ("output_tokens_estimate_target", "INTEGER"),
            ("output_tokens_budget", "INTEGER"),
            ("output_tokens_usage", "INTEGER"),
            ("output_tokens_enforcement", "TEXT"),
            ("total_token_budget", "INTEGER"),
            ("total_token_enforcement", "TEXT"),
        ]

        # Check if first column already exists (indicates migration already ran)
        if column_exists(conn, "tickets", "input_tokens_estimate_min"):
            result["already_exists"] = True
            result["success"] = True
            return result

        # Add each column
        for col_name, col_type in columns:
            if not column_exists(conn, "tickets", col_name):
                conn.execute(f"ALTER TABLE tickets ADD COLUMN {col_name} {col_type}")
                result["columns_added"].append(col_name)

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
    Roll back the migration.

    Note: SQLite does not support DROP COLUMN in older versions.
    This rollback creates a new table without the token columns.

    WARNING: This will recreate the tickets table without token data.

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
        "error": "Rollback not supported for ADD COLUMN migration. "
                 "Token columns are nullable and do not affect existing functionality.",
    }

    return result


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Add token tracking columns to tickets table"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        help="Path to database file",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Roll back the migration (not supported for this migration)",
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
        result = migrate(db_path=args.db_path)
        action = "Migration"

    if result["success"]:
        print(f"{action} successful!")
        if result.get("already_exists"):
            print("  - Columns already existed")
        if result.get("columns_added"):
            print(f"  - Added {len(result['columns_added'])} columns")
            for col in result["columns_added"]:
                print(f"    - {col}")
    else:
        print(f"{action} failed: {result['error']}", file=sys.stderr)
        sys.exit(1)
