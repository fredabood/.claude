"""
Backend abstraction layer for roadmap storage.

Provides a unified interface for switching between YAML and SQLite backends.
This allows the CLI and operations layer to work with either backend transparently.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Protocol, Union, runtime_checkable
import hashlib
import os

from ..models import (
    Roadmap,
    Track,
    Sprint,
    Task,
)


class BackendError(Exception):
    """Base exception for backend errors."""
    pass


class YAMLModifiedError(BackendError):
    """Raised when YAML files have been modified outside the database."""

    def __init__(self, modified_files: List[str]):
        self.modified_files = modified_files
        message = (
            f"YAML files modified outside database:\n"
            f"{chr(10).join('  - ' + f for f in modified_files)}\n\n"
            f"Options:\n"
            f"  vibey roadmap rebuild    # Load YAML changes into DB\n"
            f"  vibey roadmap dump --force  # Overwrite YAML with DB state"
        )
        super().__init__(message)


class DirtyDatabaseError(BackendError):
    """Raised when trying to rebuild with uncommitted database changes."""

    def __init__(self):
        message = (
            "Database has uncommitted changes that would be lost.\n\n"
            "Options:\n"
            "  vibey roadmap dump       # Save changes to YAML first\n"
            "  vibey roadmap rebuild --force  # Discard local changes\n\n"
            "Safe workflow:\n"
            "  1. vibey roadmap dump\n"
            "  2. git add .vibey/ && git commit\n"
            "  3. git pull"
        )
        super().__init__(message)


class SchemaMismatchError(BackendError):
    """Raised when database schema version doesn't match expected version."""

    def __init__(self, db_version: str, expected_version: str):
        self.db_version = db_version
        self.expected_version = expected_version
        message = (
            f"Database schema version mismatch.\n"
            f"Database version: {db_version}\n"
            f"Expected version: {expected_version}\n\n"
            f"Run 'vibey roadmap migrate' to upgrade database schema."
        )
        super().__init__(message)


@runtime_checkable
class RoadmapBackend(Protocol):
    """
    Protocol defining the interface for roadmap storage backends.

    Both YAML and SQLite backends implement this interface, allowing
    the application to work with either backend transparently.
    """

    # Read operations
    def load_roadmap(self, roadmap_id: str = "vibey-framework-v2") -> Roadmap:
        """Load a roadmap by ID."""
        ...

    def load_track(self, track_id: str) -> Track:
        """Load a track by ID."""
        ...

    def load_sprint(self, sprint_id: str) -> Sprint:
        """Load a sprint by ID."""
        ...

    def load_task(self, task_id: str) -> Task:
        """Load a task by ID."""
        ...

    def load_tasks_by_sprint(self, sprint_id: str) -> List[Task]:
        """Load all tasks for a sprint."""
        ...

    def load_tasks_by_track(self, track_id: str) -> List[Task]:
        """Load all tasks for a track."""
        ...

    def load_all_tasks(self, roadmap_id: str = "vibey-framework-v2") -> List[Task]:
        """Load all tasks for a roadmap."""
        ...

    # Write operations
    def save_roadmap(self, roadmap: Roadmap) -> None:
        """Save a roadmap."""
        ...

    def save_track(self, track: Track) -> None:
        """Save a track."""
        ...

    def save_sprint(self, sprint: Sprint) -> None:
        """Save a sprint."""
        ...

    def save_task(self, task: Task) -> None:
        """Save a task."""
        ...

    def save_tasks(self, tasks: List[Task]) -> None:
        """Save multiple tasks."""
        ...


class YAMLBackend:
    """
    YAML-based storage backend.

    Reads and writes roadmap data directly to/from YAML files.
    This is the traditional backend that stores data in the file system.
    """

    def __init__(self, roadmap_dir: Union[str, Path] = ".vibey/roadmap"):
        """
        Initialize YAML backend.

        Args:
            roadmap_dir: Path to the roadmap directory
        """
        self.roadmap_dir = Path(roadmap_dir)

    def load_roadmap(self, roadmap_id: str = "vibey-framework-v2") -> Roadmap:
        """Load a roadmap from YAML."""
        from .yaml_loader import load_roadmap
        return load_roadmap(self.roadmap_dir / "roadmap.yaml")

    def load_track(self, track_id: str) -> Track:
        """Load a track from YAML (flat structure)."""
        from .yaml_loader import load_track
        return load_track(self.roadmap_dir / "tracks" / f"{track_id}.yaml")

    def load_sprint(self, sprint_id: str) -> Sprint:
        """Load a sprint from YAML (flat structure)."""
        from .yaml_loader import load_sprint
        sprint_path = self.roadmap_dir / "sprints" / f"{sprint_id}.yaml"
        if sprint_path.exists():
            return load_sprint(sprint_path)
        raise ValueError(f"Sprint '{sprint_id}' not found")

    def load_task(self, task_id: str) -> Task:
        """Load a task from YAML (flat structure)."""
        from .yaml_loader import load_task
        task_path = self.roadmap_dir / "tasks" / f"{task_id}.yaml"
        if task_path.exists():
            return load_task(task_path)
        raise ValueError(f"Task '{task_id}' not found")

    def load_tasks_by_sprint(self, sprint_id: str) -> List[Task]:
        """Load all tasks for a sprint from YAML (flat structure)."""
        from .yaml_loader import load_task
        tasks_dir = self.roadmap_dir / "tasks"
        tasks = []
        if tasks_dir.exists():
            for task_file in tasks_dir.glob("*.yaml"):
                if task_file.name.startswith('.'):
                    continue
                task = load_task(task_file)
                if task.sprint_id == sprint_id:
                    tasks.append(task)
        return tasks

    def load_tasks_by_track(self, track_id: str) -> List[Task]:
        """Load all tasks for a track from YAML (flat structure)."""
        from .yaml_loader import load_task
        tasks_dir = self.roadmap_dir / "tasks"
        tasks = []
        if tasks_dir.exists():
            for task_file in tasks_dir.glob("*.yaml"):
                if task_file.name.startswith('.'):
                    continue
                task = load_task(task_file)
                if task.track_id == track_id:
                    tasks.append(task)
        return tasks

    def load_all_tasks(self, roadmap_id: str = "vibey-framework-v2") -> List[Task]:
        """Load all tasks from YAML (flat structure)."""
        from .yaml_loader import load_task
        tasks_dir = self.roadmap_dir / "tasks"
        tasks = []
        if tasks_dir.exists():
            for task_file in tasks_dir.glob("*.yaml"):
                if task_file.name.startswith('.'):
                    continue
                try:
                    task = load_task(task_file)
                    tasks.append(task)
                except Exception:
                    pass
        return tasks

    def save_roadmap(self, roadmap: Roadmap) -> None:
        """Save a roadmap to YAML."""
        from .yaml_dumper import save_roadmap
        save_roadmap(roadmap, self.roadmap_dir / "roadmap.yaml")

    def save_track(self, track: Track) -> None:
        """Save a track to YAML (flat structure)."""
        from .yaml_dumper import save_track
        tracks_dir = self.roadmap_dir / "tracks"
        tracks_dir.mkdir(parents=True, exist_ok=True)
        save_track(track, tracks_dir / f"{track.id}.yaml")

    def save_sprint(self, sprint: Sprint) -> None:
        """Save a sprint to YAML (flat structure)."""
        from .yaml_dumper import save_sprint
        sprints_dir = self.roadmap_dir / "sprints"
        sprints_dir.mkdir(parents=True, exist_ok=True)
        save_sprint(sprint, sprints_dir / f"{sprint.id}.yaml")

    def save_task(self, task: Task) -> None:
        """Save a task to YAML."""
        self.save_tasks([task])

    def save_tasks(self, tasks: List[Task]) -> None:
        """Save tasks to YAML (flat structure)."""
        from .yaml_dumper import save_task
        tasks_dir = self.roadmap_dir / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)
        for task in tasks:
            save_task(task, tasks_dir / f"{task.id}.yaml")


class SQLiteBackend:
    """
    SQLite-based storage backend.

    Reads and writes roadmap data to/from a SQLite database.
    This backend provides better performance for queries and
    automatic consistency via computed views and triggers.
    """

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        """
        Initialize SQLite backend.

        Args:
            db_path: Path to the SQLite database file.
                     If not specified, uses the default location.
        """
        self.db_path = Path(db_path) if db_path else None

    def _ensure_connection(self):
        """Ensure database connection is available."""
        from ..database import get_connection, database_exists

        if not database_exists(str(self.db_path) if self.db_path else None):
            raise BackendError(
                "Database not found. Run 'vibey roadmap rebuild' to create "
                "database from YAML files."
            )

    def load_roadmap(self, roadmap_id: str = "vibey-framework-v2") -> Roadmap:
        """Load a roadmap from SQLite."""
        self._ensure_connection()
        from .sql_loader import load_roadmap
        return load_roadmap(roadmap_id)

    def load_track(self, track_id: str) -> Track:
        """Load a track from SQLite."""
        self._ensure_connection()
        from .sql_loader import load_track
        return load_track(track_id)

    def load_sprint(self, sprint_id: str) -> Sprint:
        """Load a sprint from SQLite."""
        self._ensure_connection()
        from .sql_loader import load_sprint
        return load_sprint(sprint_id)

    def load_task(self, task_id: str) -> Task:
        """Load a task from SQLite."""
        self._ensure_connection()
        from .sql_loader import load_task
        return load_task(task_id)

    def load_tasks_by_sprint(self, sprint_id: str) -> List[Task]:
        """Load all tasks for a sprint from SQLite."""
        self._ensure_connection()
        from .sql_loader import load_tasks_by_sprint
        return load_tasks_by_sprint(sprint_id)

    def load_tasks_by_track(self, track_id: str) -> List[Task]:
        """Load all tasks for a track from SQLite."""
        self._ensure_connection()
        from .sql_loader import load_tasks_by_track
        return load_tasks_by_track(track_id)

    def load_all_tasks(self, roadmap_id: str = "vibey-framework-v2") -> List[Task]:
        """Load all tasks from SQLite."""
        self._ensure_connection()
        from .sql_loader import load_all_tasks
        return load_all_tasks(roadmap_id)

    def save_roadmap(self, roadmap: Roadmap) -> None:
        """Save a roadmap to SQLite."""
        from .sql_dumper import save_roadmap
        save_roadmap(roadmap)

    def save_track(self, track: Track) -> None:
        """Save a track to SQLite."""
        from .sql_dumper import save_track
        save_track(track)

    def save_sprint(self, sprint: Sprint) -> None:
        """Save a sprint to SQLite."""
        from .sql_dumper import save_sprint
        save_sprint(sprint)

    def save_task(self, task: Task) -> None:
        """Save a task to SQLite."""
        from .sql_dumper import save_task
        save_task(task)

    def save_tasks(self, tasks: List[Task]) -> None:
        """Save tasks to SQLite."""
        from .sql_dumper import save_tasks
        save_tasks(tasks)


class SyncManager:
    """
    Manages synchronization between SQLite database and YAML files.

    Handles the bidirectional sync:
    - DB → YAML (dump): Export database state to YAML files
    - YAML → DB (rebuild): Import YAML files into database
    """

    def __init__(
        self,
        roadmap_dir: Union[str, Path] = ".vibey/roadmap",
        db_path: Optional[Union[str, Path]] = None
    ):
        """
        Initialize sync manager.

        Args:
            roadmap_dir: Path to the roadmap directory for YAML files
            db_path: Path to the SQLite database file
        """
        self.roadmap_dir = Path(roadmap_dir)
        self.db_path = Path(db_path) if db_path else Path(".vibey/roadmap.db")
        self.yaml_backend = YAMLBackend(roadmap_dir)
        self.sqlite_backend = SQLiteBackend(db_path)

    def compute_file_checksum(self, file_path: Union[str, Path]) -> str:
        """Compute SHA-256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def find_all_yaml_files(self) -> List[Path]:
        """Find all YAML files in the roadmap directory (flat structure)."""
        yaml_files = []

        # Main roadmap.yaml
        roadmap_file = self.roadmap_dir / "roadmap.yaml"
        if roadmap_file.exists():
            yaml_files.append(roadmap_file)

        # Track files (flat structure: tracks/*.yaml)
        tracks_dir = self.roadmap_dir / "tracks"
        if tracks_dir.exists():
            for track_file in tracks_dir.glob("*.yaml"):
                if not track_file.name.startswith('.'):
                    yaml_files.append(track_file)

        # Sprint files (flat structure: sprints/*.yaml)
        sprints_dir = self.roadmap_dir / "sprints"
        if sprints_dir.exists():
            for sprint_file in sprints_dir.glob("*.yaml"):
                if not sprint_file.name.startswith('.'):
                    yaml_files.append(sprint_file)

        # Task files (flat structure: tasks/*.yaml)
        tasks_dir = self.roadmap_dir / "tasks"
        if tasks_dir.exists():
            for task_file in tasks_dir.glob("*.yaml"):
                if not task_file.name.startswith('.'):
                    yaml_files.append(task_file)

        return yaml_files

    def store_yaml_checksums(self) -> None:
        """Store checksums of all YAML files in the database."""
        from ..database import get_connection, transaction

        yaml_files = self.find_all_yaml_files()

        with transaction(db_path=self.db_path) as conn:
            conn.execute("DELETE FROM yaml_checksums")
            for yaml_file in yaml_files:
                checksum = self.compute_file_checksum(yaml_file)
                conn.execute("""
                    INSERT INTO yaml_checksums (file_path, checksum, loaded_at, file_size, last_modified)
                    VALUES (?, ?, datetime('now'), ?, ?)
                """, (
                    str(yaml_file),
                    checksum,
                    os.path.getsize(yaml_file),
                    os.path.getmtime(yaml_file),
                ))

    def check_yaml_modified(self) -> List[str]:
        """
        Check if any YAML files have been modified outside the database.

        Returns:
            List of modified file paths
        """
        from ..database import get_connection

        conn = get_connection(db_path=self.db_path)
        modified_files = []

        for row in conn.execute("SELECT file_path, checksum FROM yaml_checksums").fetchall():
            file_path = Path(row['file_path'])
            if file_path.exists():
                current_checksum = self.compute_file_checksum(file_path)
                if current_checksum != row['checksum']:
                    modified_files.append(row['file_path'])
            else:
                # File was deleted
                modified_files.append(row['file_path'] + " (deleted)")

        return modified_files

    def is_db_dirty(self) -> bool:
        """Check if database has uncommitted changes."""
        from ..database import get_connection

        conn = get_connection(db_path=self.db_path)
        row = conn.execute(
            "SELECT is_dirty FROM database_state WHERE id = 1"
        ).fetchone()

        return bool(row and row['is_dirty'])

    def mark_db_dirty(self) -> None:
        """Mark database as having uncommitted changes."""
        from ..database import get_connection, transaction

        with transaction(db_path=self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO database_state (id, is_dirty, last_yaml_dump)
                VALUES (1, 1, NULL)
            """)

    def mark_db_clean(self) -> None:
        """Mark database as clean (no uncommitted changes)."""
        from ..database import get_connection, transaction

        with transaction(db_path=self.db_path) as conn:
            conn.execute("""
                UPDATE database_state
                SET is_dirty = 0, last_yaml_dump = datetime('now')
                WHERE id = 1
            """)

    def dump(self, force: bool = False) -> None:
        """
        Dump database to YAML files.

        Args:
            force: If True, overwrite YAML even if modified outside database

        Raises:
            YAMLModifiedError: If YAML files were modified and force=False
        """
        # Pre-dump safety check
        if not force:
            modified_files = self.check_yaml_modified()
            if modified_files:
                raise YAMLModifiedError(modified_files)

        # Load from SQLite
        roadmap = self.sqlite_backend.load_roadmap()
        tasks = self.sqlite_backend.load_all_tasks()

        # Group tasks by track/sprint for efficient saving
        tracks = {}
        sprints = {}

        for task in tasks:
            if task.track_id not in tracks:
                tracks[task.track_id] = self.sqlite_backend.load_track(task.track_id)
            if task.sprint_id not in sprints:
                sprints[task.sprint_id] = self.sqlite_backend.load_sprint(task.sprint_id)

        # Save to YAML
        self.yaml_backend.save_roadmap(roadmap)
        for track in tracks.values():
            self.yaml_backend.save_track(track)
        for sprint in sprints.values():
            self.yaml_backend.save_sprint(sprint)
        self.yaml_backend.save_tasks(tasks)

        # Update checksums and mark clean
        self.store_yaml_checksums()
        self.mark_db_clean()

    def rebuild(self, force: bool = False) -> None:
        """
        Rebuild database from YAML files.

        Args:
            force: If True, discard uncommitted database changes

        Raises:
            DirtyDatabaseError: If database has uncommitted changes and force=False
        """
        from ..database import (
            get_connection,
            transaction,
            create_schema,
            create_views,
            create_triggers,
            drop_all_tables,
            drop_views,
            drop_triggers,
            disable_triggers_for_bulk_operations,
            enable_triggers_for_bulk_operations,
            rebuild_summary_tables,
        )

        # Pre-rebuild safety check
        if not force and self.is_db_dirty():
            raise DirtyDatabaseError()

        # Load from YAML (flat structure)
        from .yaml_loader import load_track, load_sprint, load_task

        roadmap = self.yaml_backend.load_roadmap()

        tracks = []
        sprints = []
        tasks = []

        # Load tracks from flat structure
        tracks_dir = self.roadmap_dir / "tracks"
        if tracks_dir.exists():
            for track_file in tracks_dir.glob("*.yaml"):
                if track_file.name.startswith('.'):
                    continue
                try:
                    track = load_track(track_file)
                    tracks.append(track)
                except Exception:
                    pass

        # Load sprints from flat structure
        sprints_dir = self.roadmap_dir / "sprints"
        if sprints_dir.exists():
            for sprint_file in sprints_dir.glob("*.yaml"):
                if sprint_file.name.startswith('.'):
                    continue
                try:
                    sprint = load_sprint(sprint_file)
                    sprints.append(sprint)
                except Exception:
                    pass

        # Load tasks from flat structure
        tasks_dir = self.roadmap_dir / "tasks"
        if tasks_dir.exists():
            for task_file in tasks_dir.glob("*.yaml"):
                if task_file.name.startswith('.'):
                    continue
                try:
                    task = load_task(task_file)
                    tasks.append(task)
                except Exception:
                    pass

        # Rebuild database
        # Drop and recreate schema (each function handles its own transactions)
        # Pass db_path to ensure correct database is used
        drop_triggers(db_path=self.db_path)  # Drop triggers first to avoid errors during table drops
        drop_views(db_path=self.db_path)     # Drop views before tables
        drop_all_tables(db_path=self.db_path)
        create_schema(db_path=self.db_path)
        create_views(db_path=self.db_path)
        create_triggers(db_path=self.db_path)

        # Disable triggers during bulk load
        disable_triggers_for_bulk_operations(db_path=self.db_path)

        # Save all entities (with triggers disabled for performance)
        from .sql_dumper import save_full_roadmap
        save_full_roadmap(roadmap, tracks, sprints, tasks, db_path=self.db_path)

        # Store checksums for tracking
        self.store_yaml_checksums()

        # Mark database as clean
        self.mark_db_clean()

    def get_status(self) -> dict:
        """
        Get sync status between database and YAML.

        Returns:
            Dict with status information
        """
        from ..database import database_exists

        # Check if database exists using Path
        db_exists = self.db_path.exists() if self.db_path else database_exists()

        status = {
            'db_exists': db_exists,
            'db_path': str(self.db_path),
            'yaml_files': len(self.find_all_yaml_files()),
            'is_dirty': False,
            'modified_yaml_files': [],
            'status': 'UNKNOWN',
        }

        if status['db_exists']:
            status['is_dirty'] = self.is_db_dirty()
            status['modified_yaml_files'] = self.check_yaml_modified()

            if status['is_dirty'] and status['modified_yaml_files']:
                status['status'] = 'CONFLICT'
            elif status['is_dirty']:
                status['status'] = 'DB_AHEAD'
            elif status['modified_yaml_files']:
                status['status'] = 'YAML_AHEAD'
            else:
                status['status'] = 'IN_SYNC'
        else:
            status['status'] = 'NO_DATABASE'

        return status


# Expected database schema version - must match schema.py
EXPECTED_SCHEMA_VERSION = "1.0.0"


class DatabaseValidationError(BackendError):
    """Raised when database validation fails."""
    pass


class DatabaseCorruptedError(BackendError):
    """Raised when database fails integrity check."""

    def __init__(self, details: str = ""):
        message = (
            "Database integrity check failed.\n"
            f"{details}\n\n" if details else "\n"
            "Options:\n"
            "  vibey roadmap db rebuild --force  # Rebuild from YAML\n"
            "  rm .vibey/roadmap.db  # Delete and reinitialize"
        )
        super().__init__(message)


def load_roadmap_config(root_dir: Optional[Path] = None) -> dict:
    """
    Load roadmap configuration from .vibey/config/roadmap.yaml.

    Args:
        root_dir: Project root directory (defaults to current working directory)

    Returns:
        Configuration dict with defaults applied
    """
    import yaml

    root_dir = root_dir or Path.cwd()
    config_path = root_dir / ".vibey" / "config" / "roadmap.yaml"

    defaults = {
        "backend": "auto",  # "auto", "sqlite", "yaml"
        "database": {
            "path": ".vibey/roadmap.db",
            "validate_on_load": True,
            "fallback_to_yaml": True,
        }
    }

    if not config_path.exists():
        return defaults

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
    except Exception:
        return defaults

    # Merge with defaults
    result = defaults.copy()
    if "backend" in config:
        result["backend"] = config["backend"]
    if "database" in config:
        for key in result["database"]:
            if key in config["database"]:
                result["database"][key] = config["database"][key]

    return result


def validate_database(db_path: Path) -> tuple[bool, str]:
    """
    Validate that the database is usable.

    Checks:
    1. File exists
    2. Schema version matches expected
    3. Required tables exist
    4. Integrity check passes

    Args:
        db_path: Path to the SQLite database file

    Returns:
        Tuple of (is_valid, error_message)
    """
    import sqlite3

    # Check file exists
    if not db_path.exists():
        return False, "Database file not found"

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # Check schema version
        try:
            row = conn.execute(
                "SELECT schema_version FROM database_state WHERE id = 1"
            ).fetchone()
            if row is None:
                return False, "Database state not initialized"

            db_version = row['schema_version']
            if db_version != EXPECTED_SCHEMA_VERSION:
                return False, f"Schema version mismatch: got {db_version}, expected {EXPECTED_SCHEMA_VERSION}"
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                return False, "Database schema not initialized (missing database_state table)"
            raise

        # Check required tables exist
        required_tables = ['roadmaps', 'tracks', 'sprints', 'tasks']
        existing_tables = set()
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
            existing_tables.add(row['name'])

        missing_tables = set(required_tables) - existing_tables
        if missing_tables:
            return False, f"Missing tables: {', '.join(missing_tables)}"

        # Quick integrity check
        result = conn.execute("PRAGMA integrity_check(1)").fetchone()
        if result[0] != "ok":
            return False, f"Integrity check failed: {result[0]}"

        conn.close()
        return True, ""

    except sqlite3.DatabaseError as e:
        return False, f"Database error: {e}"
    except Exception as e:
        return False, f"Validation error: {e}"


def get_backend(
    mode: Optional[str] = None,
    root_dir: Optional[Path] = None,
    validate: bool = True,
    fallback: bool = True,
) -> RoadmapBackend:
    """
    Get the appropriate backend based on configuration and mode.

    Args:
        mode: Backend mode override ("auto", "sqlite", "yaml", or None for config)
        root_dir: Project root directory
        validate: Whether to validate database before using
        fallback: Whether to fall back to YAML on database errors

    Returns:
        RoadmapBackend instance

    Raises:
        BackendError: If requested backend is unavailable
        SchemaMismatchError: If database schema version doesn't match
        DatabaseCorruptedError: If database fails integrity check
    """
    import sys

    root_dir = root_dir or Path.cwd()
    config = load_roadmap_config(root_dir)

    # Determine effective mode
    effective_mode = mode or config["backend"]

    # Get database path
    db_path_str = config["database"]["path"]
    if not db_path_str.startswith("/"):
        db_path = root_dir / db_path_str
    else:
        db_path = Path(db_path_str)

    roadmap_dir = root_dir / ".vibey" / "roadmap"

    # Handle explicit YAML mode
    if effective_mode == "yaml":
        return YAMLBackend(roadmap_dir)

    # Handle explicit SQLite mode
    if effective_mode == "sqlite":
        if validate or config["database"]["validate_on_load"]:
            is_valid, error = validate_database(db_path)
            if not is_valid:
                if fallback and config["database"]["fallback_to_yaml"]:
                    print(f"⚠️  Database error: {error}", file=sys.stderr)
                    print("   Falling back to YAML backend", file=sys.stderr)
                    return YAMLBackend(roadmap_dir)
                else:
                    raise BackendError(f"Database unavailable: {error}")

        return SQLiteBackend(db_path)

    # Handle auto mode (default)
    if effective_mode == "auto":
        # Check if database exists and is valid
        if db_path.exists():
            if validate or config["database"]["validate_on_load"]:
                is_valid, error = validate_database(db_path)
                if is_valid:
                    return SQLiteBackend(db_path)
                else:
                    # Warn but fall back to YAML
                    if fallback and config["database"]["fallback_to_yaml"]:
                        print(f"⚠️  Database error: {error}", file=sys.stderr)
                        print("   Falling back to YAML backend", file=sys.stderr)
            else:
                # Skip validation, just use SQLite if file exists
                return SQLiteBackend(db_path)

        # Fall back to YAML
        return YAMLBackend(roadmap_dir)

    # Unknown mode
    raise BackendError(f"Unknown backend mode: {effective_mode}")


def get_default_backend() -> RoadmapBackend:
    """
    Get the default backend based on configuration.

    This is a convenience wrapper around get_backend() for backward compatibility.
    Prefer using get_backend() directly for more control.

    Returns:
        RoadmapBackend instance
    """
    return get_backend()
