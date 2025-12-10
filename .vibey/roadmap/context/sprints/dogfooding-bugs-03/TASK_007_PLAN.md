# Task 007: Add Database Migration Script for Schema Updates

**Task ID:** dogfooding-bugs-03-task-007
**Bug Addressed:** #9 (Pre-commit Hook Database Error - Missing is_dirty Column)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

When the database schema evolves (new columns, tables), existing databases need to be migrated. A migration system ensures users don't encounter schema errors.

---

## Design

### Migration System Architecture

```
vibey/roadmap/database/migrations/
├── 001_initial_schema.sql        # Already exists via create_schema()
├── 002_add_is_dirty.sql          # Add is_dirty if missing
├── 003_add_audit_trail.sql       # Add audit_trail table
├── ...
└── migration_runner.py           # Runs pending migrations
```

### Migration Format

```sql
-- migrations/002_add_is_dirty.sql
-- Migration: Add is_dirty column to database_state
-- Version: 1.0.1

-- Check if column already exists (handled by runner)
ALTER TABLE database_state ADD COLUMN is_dirty INTEGER NOT NULL DEFAULT 0;

-- Update schema version
UPDATE database_state SET schema_version = '1.0.1' WHERE id = 1;
```

---

## Implementation

### Migration Runner

```python
# vibey/roadmap/database/migrations/migration_runner.py

from pathlib import Path
from typing import List, Tuple
import sqlite3
import re

MIGRATIONS_DIR = Path(__file__).parent


class MigrationRunner:
    """
    Run database migrations in order.

    Tracks applied migrations in database to avoid re-running.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """Create migrations tracking table if not exists."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                migration_name TEXT NOT NULL UNIQUE,
                applied_at TEXT NOT NULL DEFAULT (datetime('now')),
                checksum TEXT
            )
        """)
        self.conn.commit()

    def get_applied_migrations(self) -> List[str]:
        """Get list of already-applied migration names."""
        rows = self.conn.execute("""
            SELECT migration_name FROM schema_migrations
            ORDER BY id
        """).fetchall()
        return [row['migration_name'] for row in rows]

    def get_pending_migrations(self) -> List[Path]:
        """Get list of migration files that haven't been applied."""
        applied = set(self.get_applied_migrations())
        all_migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
        return [m for m in all_migrations if m.name not in applied]

    def run_migration(self, migration_file: Path) -> bool:
        """
        Run a single migration file.

        Args:
            migration_file: Path to .sql migration file

        Returns:
            True if successful
        """
        print(f"  Applying migration: {migration_file.name}")

        sql = migration_file.read_text()

        try:
            # Run migration in transaction
            self.conn.executescript(sql)

            # Record as applied
            self.conn.execute("""
                INSERT INTO schema_migrations (migration_name, checksum)
                VALUES (?, ?)
            """, (migration_file.name, self._checksum(sql)))

            self.conn.commit()
            return True

        except sqlite3.Error as e:
            print(f"    Migration failed: {e}")
            self.conn.rollback()
            return False

    def run_pending(self) -> Tuple[int, int]:
        """
        Run all pending migrations.

        Returns:
            Tuple of (applied_count, failed_count)
        """
        pending = self.get_pending_migrations()

        if not pending:
            print("  No pending migrations")
            return (0, 0)

        print(f"  {len(pending)} pending migrations")

        applied = 0
        failed = 0

        for migration_file in pending:
            if self.run_migration(migration_file):
                applied += 1
            else:
                failed += 1
                break  # Stop on first failure

        return (applied, failed)

    def _checksum(self, content: str) -> str:
        """Calculate checksum of migration content."""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()[:16]


def run_migrations(db_path: Path) -> Tuple[int, int]:
    """
    Run all pending database migrations.

    Args:
        db_path: Path to SQLite database

    Returns:
        Tuple of (applied_count, failed_count)
    """
    runner = MigrationRunner(db_path)
    return runner.run_pending()
```

### Migration Files

```sql
-- migrations/002_add_is_dirty.sql
-- Migration: Add is_dirty column to database_state (if missing)
-- Version: 1.0.1
-- Date: 2025-12-10

-- Add is_dirty column if it doesn't exist
-- SQLite doesn't have IF NOT EXISTS for columns, so we use a workaround

-- First check if column exists (this will fail silently if it does)
-- Actually SQLite will error if column exists, so we wrap in error handler

-- Alternative approach: just try to add, catch error in runner
ALTER TABLE database_state ADD COLUMN is_dirty INTEGER NOT NULL DEFAULT 0;

-- Update schema version
UPDATE database_state SET schema_version = '1.0.1' WHERE id = 1;
```

### CLI Command

```python
# vibey/cli/main.py

@db.command()
@click.option('--status', is_flag=True, help='Show migration status without applying')
@click.pass_context
def migrate(ctx, status: bool):
    """
    Run database migrations.

    Updates database schema to latest version.

    Examples:

        # Check migration status
        vibey roadmap db migrate --status

        # Run pending migrations
        vibey roadmap db migrate
    """
    from vibey.cli.commands import db_migrate_cmd
    ctx.exit(db_migrate_cmd(status_only=status))
```

### Command Implementation

```python
# vibey/cli/commands.py

def db_migrate_cmd(status_only: bool = False) -> int:
    """Run database migrations."""
    from vibey.roadmap.database.migrations.migration_runner import MigrationRunner

    root_dir = Path.cwd()
    db_path = root_dir / ".vibey" / "roadmap.db"

    if not db_path.exists():
        print("Error: No database found. Run 'vibey roadmap db rebuild' first.")
        return 1

    runner = MigrationRunner(db_path)

    # Show status
    applied = runner.get_applied_migrations()
    pending = runner.get_pending_migrations()

    print("\n📊 Migration Status:")
    print(f"   Applied: {len(applied)}")
    print(f"   Pending: {len(pending)}")

    if applied:
        print("\n   Applied migrations:")
        for name in applied[-5:]:  # Show last 5
            print(f"     ✓ {name}")
        if len(applied) > 5:
            print(f"     ... and {len(applied) - 5} more")

    if pending:
        print("\n   Pending migrations:")
        for path in pending[:5]:
            print(f"     ○ {path.name}")
        if len(pending) > 5:
            print(f"     ... and {len(pending) - 5} more")

    if status_only:
        return 0

    if not pending:
        print("\n✅ Database schema is up to date")
        return 0

    # Run migrations
    print("\n🔄 Running migrations...")
    applied_count, failed_count = runner.run_pending()

    if failed_count > 0:
        print(f"\n❌ Migration failed: {applied_count} applied, {failed_count} failed")
        return 1

    print(f"\n✅ Successfully applied {applied_count} migrations")
    return 0
```

---

## Files to Create/Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/database/migrations/migration_runner.py` | NEW: Migration system |
| `vibey/roadmap/database/migrations/002_add_is_dirty.sql` | NEW: Add is_dirty column |
| `vibey/cli/main.py` | Add `db migrate` command |
| `vibey/cli/commands.py` | Add `db_migrate_cmd()` |

---

## Testing Strategy

```python
def test_migration_runner_tracks_applied(tmp_path):
    """Migration runner tracks applied migrations."""
    db_path = tmp_path / "test.db"
    create_test_database(db_path)

    runner = MigrationRunner(db_path)
    runner.run_pending()

    applied = runner.get_applied_migrations()
    assert len(applied) > 0


def test_migration_not_reapplied(tmp_path):
    """Already-applied migrations are not reapplied."""
    db_path = tmp_path / "test.db"
    create_test_database(db_path)

    runner = MigrationRunner(db_path)
    first_run = runner.run_pending()
    second_run = runner.run_pending()

    assert second_run == (0, 0)  # Nothing to apply


def test_migration_adds_is_dirty_column(tmp_path):
    """002 migration adds is_dirty column."""
    db_path = tmp_path / "test.db"
    create_old_schema_database(db_path)  # Without is_dirty

    runner = MigrationRunner(db_path)
    runner.run_pending()

    conn = sqlite3.connect(db_path)
    columns = conn.execute("PRAGMA table_info(database_state)").fetchall()
    col_names = [col[1] for col in columns]
    assert 'is_dirty' in col_names
```

---

## Success Criteria

- [ ] Migration runner tracks applied migrations
- [ ] Pending migrations are detected
- [ ] Migrations run in order
- [ ] 002_add_is_dirty migration works
- [ ] CLI command shows status and runs migrations
- [ ] Migrations are idempotent (safe to re-run)

---

## Dependencies

- Task 005 (investigation identified need)
- Task 006 (defensive queries in place)

---

## Notes

The migration system provides a structured way to evolve the database schema. Each migration:
- Has a version number (001, 002, ...)
- Is tracked in `schema_migrations` table
- Runs only once
- Can be rolled back if needed (future enhancement)
