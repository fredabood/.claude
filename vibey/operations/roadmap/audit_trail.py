"""
Audit trail system for roadmap status changes.

Tracks all changes to roadmap data for accountability, transparency, and debugging.
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
import subprocess
import getpass

import yaml


@dataclass
class AuditEntry:
    """Single audit trail entry."""

    timestamp: str
    object_type: str  # "track", "sprint", "task"
    object_id: str
    field: str
    old_value: Any
    new_value: Any
    changed_by: str
    reason: str
    commit: Optional[str] = None
    source: str = "cli"  # "cli", "manual", "automated", "system"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AuditTrail:
    """Complete audit trail."""

    entries: List[AuditEntry] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_entry(self, entry: AuditEntry):
        """Add an audit entry."""
        self.entries.append(entry)
        self.metadata['last_updated'] = datetime.now(timezone.utc).isoformat()
        self.metadata['total_entries'] = len(self.entries)

    def get_recent(self, limit: int = 20) -> List[AuditEntry]:
        """Get recent entries."""
        return self.entries[-limit:]

    def get_for_object(self, object_id: str) -> List[AuditEntry]:
        """Get all entries for a specific object."""
        return [e for e in self.entries if e.object_id == object_id]

    def get_field_history(self, object_id: str, field: str) -> List[AuditEntry]:
        """Get history of changes to a specific field."""
        return [e for e in self.entries if e.object_id == object_id and e.field == field]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            'audit_log': [e.to_dict() for e in self.entries],
            'metadata': self.metadata
        }


class AuditTrailManager:
    """Manages audit trail storage and operations.

    Now uses JSONL format for storage (time-bucketed files).
    Also supports legacy YAML file and SQLite database for backward compatibility.

    Default behavior:
    - Writes to JSONL (primary) and optionally SQLite
    - Reads from JSONL
    - Legacy YAML file is deprecated but can still be read
    """

    def __init__(self, root_dir: Path, use_sqlite: bool = False):
        """
        Initialize audit trail manager.

        Args:
            root_dir: Project root directory containing .vibey/
            use_sqlite: If True, also read from SQLite for queries (writes to both)
        """
        self.root_dir = Path(root_dir)
        self.roadmap_dir = self.root_dir / ".vibey" / "roadmap"
        self.activity_log_dir = self.roadmap_dir / "activity_log"

        # DEPRECATED: Legacy YAML file path (kept for migration support)
        self.audit_file = self.roadmap_dir / "audit-trail.yaml"

        self.use_sqlite = use_sqlite
        self._db_available = None  # Lazy-check

        # Initialize JSONL writer/reader
        from vibey.operations.roadmap.jsonl_activity_log import (
            ActivityLogWriter,
            ActivityLogReader,
        )
        self._jsonl_writer = ActivityLogWriter(self.activity_log_dir)
        self._jsonl_reader = ActivityLogReader(self.activity_log_dir)

    def _ensure_audit_file(self):
        """DEPRECATED: Ensure audit trail file exists.

        This is kept for backward compatibility but no longer actively used.
        New entries are written to JSONL format.
        """
        # Ensure activity_log directory exists instead
        self.activity_log_dir.mkdir(parents=True, exist_ok=True)

    def _is_db_available(self) -> bool:
        """Check if SQLite database is available."""
        if self._db_available is None:
            try:
                from vibey.roadmap.database import database_exists
                self._db_available = database_exists(base_dir=self.root_dir)
            except ImportError:
                self._db_available = False
        return self._db_available

    def _save_to_db(self, entry: 'AuditEntry'):
        """Save a single entry to SQLite database."""
        if not self._is_db_available():
            return

        try:
            from vibey.roadmap.serialization.sql_dumper import save_audit_trail_entry
            save_audit_trail_entry(entry.to_dict())
        except Exception:
            # Don't fail if DB write fails - YAML is the source of truth
            pass

    def _get_current_user(self) -> str:
        """Get current user name."""
        try:
            return getpass.getuser()
        except Exception:
            return "unknown"

    def _get_current_commit(self) -> Optional[str]:
        """Get current git commit SHA."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return result.stdout.strip()[:7]  # Short SHA
        except Exception:
            pass
        return None

    def load_trail(self) -> AuditTrail:
        """Load audit trail from storage.

        By default loads from YAML (source of truth).
        If use_sqlite=True, loads from SQLite for better query performance.
        """
        if self.use_sqlite and self._is_db_available():
            return self._load_trail_from_db()
        return self._load_trail_from_yaml()

    def _load_trail_from_yaml(self) -> AuditTrail:
        """Load audit trail from YAML file."""
        if not self.audit_file.exists():
            return AuditTrail()

        with open(self.audit_file, 'r') as f:
            data = yaml.safe_load(f) or {}

        entries = []
        for entry_dict in data.get('audit_log', []):
            entries.append(AuditEntry(**entry_dict))

        trail = AuditTrail(entries=entries)
        trail.metadata = data.get('metadata', {})
        return trail

    def _load_trail_from_db(self) -> AuditTrail:
        """Load audit trail from SQLite database."""
        try:
            from vibey.roadmap.serialization.sql_loader import load_audit_trail
            entry_dicts = load_audit_trail()

            entries = []
            for entry_dict in entry_dicts:
                entries.append(AuditEntry(**entry_dict))

            trail = AuditTrail(entries=entries)
            trail.metadata = {
                'total_entries': len(entries),
                'source': 'sqlite',
            }
            return trail
        except Exception:
            # Fall back to YAML if DB read fails
            return self._load_trail_from_yaml()

    def _save_trail(self, trail: AuditTrail):
        """Save audit trail to disk."""
        with open(self.audit_file, 'w') as f:
            yaml.safe_dump(trail.to_dict(), f, sort_keys=False, default_flow_style=False)

    def log_change(
        self,
        object_type: str,
        object_id: str,
        field: str,
        old_value: Any,
        new_value: Any,
        reason: str,
        changed_by: Optional[str] = None,
        source: str = "cli",
    ) -> AuditEntry:
        """
        Log a status change to the audit trail.

        Now writes to JSONL format (primary) and optionally SQLite.

        Args:
            object_type: Type of object ("track", "sprint", "task")
            object_id: ID of the object
            field: Field that changed (e.g., "status", "progress")
            old_value: Previous value
            new_value: New value
            reason: Reason for the change
            changed_by: User making the change (auto-detected if None)
            source: Source of change ("cli", "manual", "automated", "system")

        Returns:
            The created audit entry
        """
        # Auto-detect user if not provided
        if changed_by is None:
            changed_by = self._get_current_user()

        commit = self._get_current_commit()

        # Write to JSONL (primary storage)
        event = self._jsonl_writer.log_change(
            object_type=object_type,
            object_id=object_id,
            field=field,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            reason=reason,
            commit=commit,
            source=source,
        )

        # Create AuditEntry for backward compatibility
        entry = AuditEntry(
            timestamp=event.timestamp,
            object_type=event.object_type,
            object_id=event.object_id,
            field=event.field,
            old_value=event.old_value,
            new_value=event.new_value,
            changed_by=event.changed_by,
            reason=event.reason,
            commit=event.commit,
            source=event.source,
        )

        # Also save to SQLite if available
        self._save_to_db(entry)

        return entry

    def get_recent_changes(self, limit: int = 20) -> List[AuditEntry]:
        """Get recent audit entries from JSONL."""
        events = self._jsonl_reader.get_history(limit=limit)
        return [self._event_to_entry(e) for e in events]

    def get_object_history(self, object_id: str, limit: int = 50) -> List[AuditEntry]:
        """Get all changes for a specific object from JSONL."""
        events = self._jsonl_reader.get_history(object_id=object_id, limit=limit)
        return [self._event_to_entry(e) for e in events]

    def get_field_history(self, object_id: str, field: str, limit: int = 50) -> List[AuditEntry]:
        """Get history of changes to a specific field from JSONL."""
        events = list(self._jsonl_reader.stream_events(object_id=object_id, field=field))
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return [self._event_to_entry(e) for e in events[:limit]]

    def _event_to_entry(self, event) -> AuditEntry:
        """Convert ActivityEvent to AuditEntry for backward compatibility."""
        return AuditEntry(
            timestamp=event.timestamp,
            object_type=event.object_type,
            object_id=event.object_id,
            field=event.field,
            old_value=event.old_value,
            new_value=event.new_value,
            changed_by=event.changed_by,
            reason=event.reason,
            commit=event.commit,
            source=event.source,
        )

    def detect_suspicious_changes(self, limit: int = 1000) -> List[Tuple[AuditEntry, str]]:
        """
        Detect suspicious changes in the audit trail.

        Returns:
            List of (entry, reason) tuples for suspicious changes
        """
        entries = self.get_recent_changes(limit=limit)
        suspicious = []

        for entry in entries:
            # Check for status rollbacks
            if entry.field == "status":
                if (entry.old_value in ["completed", "production_ready"] and
                    entry.new_value in ["not_started", "in_progress"]):
                    suspicious.append((entry, f"Status rollback: {entry.old_value} → {entry.new_value}"))

            # Check for progress decreases
            if entry.field in ["tasks_completed", "sprints_completed", "completion_percent"]:
                try:
                    if float(entry.new_value) < float(entry.old_value):
                        suspicious.append((entry, f"Progress decrease: {entry.old_value} → {entry.new_value}"))
                except (ValueError, TypeError):
                    pass

            # Check for manual YAML edits (no commit)
            if entry.source == "manual" and entry.commit is None:
                suspicious.append((entry, "Manual YAML edit without git commit"))

        return suspicious

    def generate_report(
        self,
        object_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 500,
    ) -> str:
        """
        Generate a human-readable audit report.

        Args:
            object_id: Filter by object ID (None = all)
            start_date: Filter by start date (None = no start filter)
            end_date: Filter by end date (None = no end filter)
            limit: Maximum number of entries to include

        Returns:
            Formatted report string
        """
        # Read from JSONL with filters
        events = list(self._jsonl_reader.stream_events(
            object_id=object_id,
            start_date=start_date,
            end_date=end_date,
        ))
        events.sort(key=lambda e: e.timestamp, reverse=True)
        entries = [self._event_to_entry(e) for e in events[:limit]]

        # Build report
        lines = []
        lines.append("=" * 80)
        lines.append("Audit Trail Report")
        lines.append("=" * 80)
        lines.append(f"Total entries: {len(entries)}")

        if object_id:
            lines.append(f"Filtered to object: {object_id}")
        if start_date or end_date:
            lines.append(f"Date range: {start_date or 'start'} to {end_date or 'now'}")

        lines.append("")
        lines.append("Recent Changes:")
        lines.append("-" * 80)

        for entry in entries[-50:]:  # Last 50 entries
            timestamp = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"\n{timestamp} - {entry.object_type.upper()}: {entry.object_id}")
            lines.append(f"  Field: {entry.field}")
            lines.append(f"  Change: {entry.old_value} → {entry.new_value}")
            lines.append(f"  By: {entry.changed_by} ({entry.source})")
            lines.append(f"  Reason: {entry.reason}")
            if entry.commit:
                lines.append(f"  Commit: {entry.commit}")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def sync_to_database(self) -> int:
        """
        Sync all YAML audit trail entries to SQLite database.

        This is useful for initial population or after manual YAML edits.

        Returns:
            Number of entries synced
        """
        if not self._is_db_available():
            return 0

        try:
            from vibey.roadmap.serialization.sql_dumper import save_audit_trail

            # Load from YAML
            trail = self._load_trail_from_yaml()

            # Save all entries to DB (clearing existing)
            entry_dicts = [e.to_dict() for e in trail.entries]
            save_audit_trail(entry_dicts, clear_existing=True)

            return len(entry_dicts)
        except Exception as e:
            raise RuntimeError(f"Failed to sync audit trail to database: {e}") from e

    def sync_from_database(self) -> int:
        """
        Sync all SQLite audit trail entries to YAML file.

        This overwrites the YAML file with database contents.
        Use with caution - this makes the database the source of truth.

        Returns:
            Number of entries synced
        """
        if not self._is_db_available():
            return 0

        try:
            from vibey.roadmap.serialization.sql_loader import load_audit_trail

            # Load from database
            entry_dicts = load_audit_trail()

            # Convert to AuditEntry objects
            entries = [AuditEntry(**e) for e in entry_dicts]

            # Create trail and save to YAML
            trail = AuditTrail(entries=entries)
            trail.metadata['last_updated'] = datetime.now(timezone.utc).isoformat()
            trail.metadata['total_entries'] = len(entries)
            trail.metadata['synced_from'] = 'sqlite'
            self._save_trail(trail)

            return len(entries)
        except Exception as e:
            raise RuntimeError(f"Failed to sync audit trail from database: {e}") from e


def log_status_change(
    root_dir: Path,
    object_type: str,
    object_id: str,
    old_status: str,
    new_status: str,
    reason: str,
    changed_by: Optional[str] = None
) -> AuditEntry:
    """
    Convenience function to log a status change.

    Args:
        root_dir: Project root directory
        object_type: Type of object ("track", "sprint", "task")
        object_id: ID of the object
        old_status: Previous status
        new_status: New status
        reason: Reason for the change
        changed_by: User making the change (auto-detected if None)

    Returns:
        The created audit entry
    """
    manager = AuditTrailManager(root_dir)
    return manager.log_change(
        object_type=object_type,
        object_id=object_id,
        field="status",
        old_value=old_status,
        new_value=new_status,
        reason=reason,
        changed_by=changed_by
    )


def log_progress_change(
    root_dir: Path,
    object_type: str,
    object_id: str,
    field: str,
    old_value: Any,
    new_value: Any,
    reason: str,
    changed_by: Optional[str] = None
) -> AuditEntry:
    """
    Convenience function to log a progress change.

    Args:
        root_dir: Project root directory
        object_type: Type of object ("track", "sprint", "task")
        object_id: ID of the object
        field: Progress field (e.g., "tasks_completed", "completion_percent")
        old_value: Previous value
        new_value: New value
        reason: Reason for the change
        changed_by: User making the change (auto-detected if None)

    Returns:
        The created audit entry
    """
    manager = AuditTrailManager(root_dir)
    return manager.log_change(
        object_type=object_type,
        object_id=object_id,
        field=field,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
        changed_by=changed_by
    )


# =============================================================================
# V2 Command-Level Logging Functions
# =============================================================================

def log_command_change(
    root_dir: Path,
    command: str,
    object_type: str,
    object_id: str,
    changes: List[Tuple[str, Any, Any]],
    file_path: Path,
    reason: Optional[str] = None,
    changed_by: Optional[str] = None,
):
    """
    Log a command-level change (V2 schema).

    One CLI command = one log entry, regardless of how many fields changed.

    Args:
        root_dir: Project root directory
        command: Full CLI command string (e.g., "vibey roadmap start task-001")
        object_type: Type of object ("track", "sprint", "task", "roadmap")
        object_id: ID of the object
        changes: List of (field, old_value, new_value) tuples
        file_path: Path to the modified YAML file (relative to root_dir)
        reason: Optional reason for the change
        changed_by: User making the change (auto-detected if None)

    Returns:
        The created CommandActivityEvent

    Example:
        log_command_change(
            root_dir=Path.cwd(),
            command="vibey roadmap start task-001",
            object_type="task",
            object_id="01KC2D0JK7READW9KAK1HBX4B3",
            changes=[
                ("status", "not_started", "in_progress"),
                ("started", None, "2025-12-10T17:00:00+00:00"),
            ],
            file_path=Path(".vibey/roadmap/tasks/01KC...yaml"),
        )
    """
    from vibey.operations.roadmap.jsonl_activity_log import (
        ActivityLogWriter,
        FieldChange,
        CommandActivityEvent,
        compute_file_hash,
    )
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager

    # Auto-detect user
    if changed_by is None:
        try:
            changed_by = getpass.getuser()
        except Exception:
            changed_by = "unknown"

    # Get activity log directory
    fs = FileSystemManager(root_dir)
    activity_log_dir = fs.roadmap_root / "activity_log"

    # Convert changes to FieldChange objects
    field_changes = [
        FieldChange(field=f, old=old, new=new)
        for f, old, new in changes
    ]

    # Compute file hash (file should already be updated)
    file_hash_after = None
    full_path = root_dir / file_path if not file_path.is_absolute() else file_path
    if full_path.exists():
        file_hash_after = compute_file_hash(full_path)

    # Write V2 event
    writer = ActivityLogWriter(activity_log_dir)
    event = writer.log_command(
        command=command,
        object_type=object_type,
        object_id=object_id,
        changes=field_changes,
        file_path=full_path,
        file_hash_before=None,  # TODO: Capture before hash in caller
        changed_by=changed_by,
        reason=reason,
    )

    return event
