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
        """Load a track from YAML."""
        from .yaml_loader import load_track
        return load_track(self.roadmap_dir / track_id / "track.yaml")

    def load_sprint(self, sprint_id: str) -> Sprint:
        """Load a sprint from YAML."""
        from .yaml_loader import load_sprint

        # Find the sprint file by searching track directories
        for track_dir in self.roadmap_dir.iterdir():
            if not track_dir.is_dir() or track_dir.name.startswith('.'):
                continue
            sprint_dir = track_dir / sprint_id
            if sprint_dir.exists():
                return load_sprint(sprint_dir / "sprint.yaml")

        raise ValueError(f"Sprint '{sprint_id}' not found")

    def load_task(self, task_id: str) -> Task:
        """Load a task from YAML."""
        from .yaml_loader import load_task

        # Find the task file by searching
        for track_dir in self.roadmap_dir.iterdir():
            if not track_dir.is_dir() or track_dir.name.startswith('.'):
                continue
            for sprint_dir in track_dir.iterdir():
                if not sprint_dir.is_dir() or sprint_dir.name.startswith('.'):
                    continue
                task_dir = sprint_dir / task_id
                task_file = task_dir / "task.yaml"
                if task_file.exists():
                    return load_task(task_file)

        raise ValueError(f"Task '{task_id}' not found")

    def load_tasks_by_sprint(self, sprint_id: str) -> List[Task]:
        """Load all tasks for a sprint from YAML."""
        from .yaml_loader import load_tasks

        # Find the sprint directory
        for track_dir in self.roadmap_dir.iterdir():
            if not track_dir.is_dir() or track_dir.name.startswith('.'):
                continue
            sprint_dir = track_dir / sprint_id
            if sprint_dir.exists():
                return load_tasks(sprint_dir)

        raise ValueError(f"Sprint '{sprint_id}' not found")

    def load_tasks_by_track(self, track_id: str) -> List[Task]:
        """Load all tasks for a track from YAML."""
        from .yaml_loader import load_tasks

        track_dir = self.roadmap_dir / track_id
        if not track_dir.exists():
            raise ValueError(f"Track '{track_id}' not found")

        tasks = []
        for sprint_dir in track_dir.iterdir():
            if not sprint_dir.is_dir() or sprint_dir.name.startswith('.') or sprint_dir.name == 'context':
                continue
            tasks.extend(load_tasks(sprint_dir))

        return tasks

    def load_all_tasks(self, roadmap_id: str = "vibey-framework-v2") -> List[Task]:
        """Load all tasks from YAML."""
        tasks = []
        for track_dir in self.roadmap_dir.iterdir():
            if not track_dir.is_dir() or track_dir.name.startswith('.'):
                continue
            try:
                tasks.extend(self.load_tasks_by_track(track_dir.name))
            except ValueError:
                pass

        return tasks

    def save_roadmap(self, roadmap: Roadmap) -> None:
        """Save a roadmap to YAML."""
        from .yaml_dumper import save_roadmap
        save_roadmap(roadmap, self.roadmap_dir / "roadmap.yaml")

    def save_track(self, track: Track) -> None:
        """Save a track to YAML."""
        from .yaml_dumper import save_track
        save_track(track, self.roadmap_dir / track.id / "track.yaml")

    def save_sprint(self, sprint: Sprint) -> None:
        """Save a sprint to YAML."""
        from .yaml_dumper import save_sprint

        # Find the track for this sprint
        track_dir = self.roadmap_dir / sprint.track_id
        sprint_dir = track_dir / sprint.id
        sprint_dir.mkdir(parents=True, exist_ok=True)
        save_sprint(sprint, sprint_dir / "sprint.yaml")

    def save_task(self, task: Task) -> None:
        """Save a task to YAML."""
        self.save_tasks([task])

    def save_tasks(self, tasks: List[Task]) -> None:
        """Save tasks to YAML."""
        from .yaml_dumper import save_tasks

        # Group tasks by sprint
        tasks_by_sprint = {}
        for task in tasks:
            if task.sprint_id not in tasks_by_sprint:
                tasks_by_sprint[task.sprint_id] = []
            tasks_by_sprint[task.sprint_id].append(task)

        # Save each group to appropriate sprint directory
        for sprint_id, sprint_tasks in tasks_by_sprint.items():
            if sprint_tasks:
                track_id = sprint_tasks[0].track_id
                sprint_dir = self.roadmap_dir / track_id / sprint_id
                sprint_dir.mkdir(parents=True, exist_ok=True)
                save_tasks(sprint_tasks, sprint_dir)


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
        """Find all YAML files in the roadmap directory."""
        yaml_files = []

        # Main roadmap.yaml
        roadmap_file = self.roadmap_dir / "roadmap.yaml"
        if roadmap_file.exists():
            yaml_files.append(roadmap_file)

        # Track, sprint, and task YAML files
        for track_dir in self.roadmap_dir.iterdir():
            if not track_dir.is_dir() or track_dir.name.startswith('.'):
                continue

            track_file = track_dir / "track.yaml"
            if track_file.exists():
                yaml_files.append(track_file)

            for sprint_dir in track_dir.iterdir():
                if not sprint_dir.is_dir() or sprint_dir.name.startswith('.') or sprint_dir.name == 'context':
                    continue

                sprint_file = sprint_dir / "sprint.yaml"
                if sprint_file.exists():
                    yaml_files.append(sprint_file)

                for task_dir in sprint_dir.iterdir():
                    if not task_dir.is_dir() or task_dir.name.startswith('.'):
                        continue

                    task_file = task_dir / "task.yaml"
                    if task_file.exists():
                        yaml_files.append(task_file)

        return yaml_files

    def store_yaml_checksums(self) -> None:
        """Store checksums of all YAML files in the database."""
        from ..database import get_connection, transaction

        yaml_files = self.find_all_yaml_files()

        with transaction() as conn:
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

        conn = get_connection()
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

        conn = get_connection()
        row = conn.execute(
            "SELECT is_dirty FROM database_state WHERE id = 1"
        ).fetchone()

        return bool(row and row['is_dirty'])

    def mark_db_dirty(self) -> None:
        """Mark database as having uncommitted changes."""
        from ..database import get_connection, transaction

        with transaction() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO database_state (id, is_dirty, last_yaml_dump)
                VALUES (1, 1, NULL)
            """)

    def mark_db_clean(self) -> None:
        """Mark database as clean (no uncommitted changes)."""
        from ..database import get_connection, transaction

        with transaction() as conn:
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
            disable_triggers_for_bulk_operations,
            enable_triggers_for_bulk_operations,
            rebuild_summary_tables,
        )

        # Pre-rebuild safety check
        if not force and self.is_db_dirty():
            raise DirtyDatabaseError()

        # Load from YAML
        roadmap = self.yaml_backend.load_roadmap()

        tracks = []
        sprints = []
        tasks = []

        for track_dir in self.roadmap_dir.iterdir():
            if not track_dir.is_dir() or track_dir.name.startswith('.'):
                continue

            try:
                track = self.yaml_backend.load_track(track_dir.name)
                tracks.append(track)

                for sprint_summary in track.sprints:
                    try:
                        sprint = self.yaml_backend.load_sprint(sprint_summary.id)
                        sprints.append(sprint)

                        sprint_tasks = self.yaml_backend.load_tasks_by_sprint(sprint_summary.id)
                        tasks.extend(sprint_tasks)
                    except (ValueError, FileNotFoundError):
                        pass
            except (ValueError, FileNotFoundError):
                pass

        # Rebuild database
        with transaction() as conn:
            # Drop and recreate schema
            drop_all_tables(conn)
            create_schema(conn)
            create_views(conn)
            create_triggers(conn)

            # Disable triggers during bulk load
            disable_triggers_for_bulk_operations(conn)

        # Save all entities (with triggers disabled for performance)
        from .sql_dumper import save_full_roadmap
        save_full_roadmap(roadmap, tracks, sprints, tasks)

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


def get_default_backend() -> RoadmapBackend:
    """
    Get the default backend based on configuration.

    Currently returns YAML backend for backward compatibility.
    Will return SQLite backend when database is available and configured.

    Returns:
        RoadmapBackend instance
    """
    from ..database import database_exists

    # Check if SQLite database exists and is preferred
    if database_exists():
        return SQLiteBackend()

    # Fall back to YAML backend
    return YAMLBackend()
