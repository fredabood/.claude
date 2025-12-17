"""
JSONL-based activity log for roadmap state changes.

Provides time-bucketed activity logging with efficient append-only writes.
Each month's events are stored in a separate JSONL file.

File format: .vibey/roadmap/activity_log/YYYY-MM.jsonl
Each line is a complete JSON object representing one event.

V2 Schema (2025-12): Command-level granularity
- One CLI command = one activity log entry
- Includes file hashes for verification
- Includes signature fields for Phase 4
"""

import hashlib
import json
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Iterator, List, Dict


# Cross-platform file locking
if sys.platform == 'win32':
    import msvcrt

    def _lock_file(f):
        """Lock file on Windows."""
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)

    def _unlock_file(f):
        """Unlock file on Windows."""
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl

    def _lock_file(f):
        """Lock file on Unix."""
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)

    def _unlock_file(f):
        """Unlock file on Unix."""
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def _generate_ulid() -> str:
    """Generate a ULID for event IDs."""
    try:
        from ulid import ULID
        return str(ULID())
    except ImportError:
        # Fallback: timestamp-based ID
        import uuid
        return f"evt_{uuid.uuid4().hex[:20]}"


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of file contents.

    Args:
        file_path: Path to file

    Returns:
        64-character lowercase hex hash
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


# =============================================================================
# V2 Schema: Command-Level Granularity
# =============================================================================

@dataclass
class FieldChange:
    """
    Single field change within a command.

    Part of V2 schema - tracks individual field changes within a command.
    """
    field: str       # Field name
    old: Any         # Previous value (None for new fields)
    new: Any         # New value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {"field": self.field, "old": self.old, "new": self.new}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FieldChange':
        """Create from dictionary."""
        return cls(field=data["field"], old=data.get("old"), new=data.get("new"))


@dataclass
class CommandActivityEvent:
    """
    Single activity event representing one CLI command.

    V2 schema: Command-level granularity - one CLI command = one entry.
    Includes file hashes for verification and signature fields for Phase 4.
    """
    # Identity
    id: str                                      # Unique event ID (ULID)
    timestamp: str                               # ISO8601 with timezone

    # Command info
    command: str                                 # Full CLI command string

    # Target object
    object_type: str                             # "track", "sprint", "task", "roadmap"
    object_id: str                               # ULID of modified object

    # Changes (array of field changes)
    changes: List[FieldChange] = field(default_factory=list)

    # File verification
    file_path: str = ""                          # Relative path to YAML file
    file_hash_before: Optional[str] = None       # SHA256 before change
    file_hash_after: Optional[str] = None        # SHA256 after change

    # Attribution
    changed_by: str = "cli"                      # Source of change
    reason: Optional[str] = None                 # User-provided reason

    # Signing (Phase 4)
    signature: Optional[str] = None              # Ed25519 signature (base64)
    signer: Optional[str] = None                 # Signer identity

    def to_json_line(self) -> str:
        """Convert to JSON line (without trailing newline)."""
        data = {
            "id": self.id,
            "timestamp": self.timestamp,
            "command": self.command,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "changes": [c.to_dict() for c in self.changes],
            "file_path": self.file_path,
            "file_hash_before": self.file_hash_before,
            "file_hash_after": self.file_hash_after,
            "changed_by": self.changed_by,
            "reason": self.reason,
            "signature": self.signature,
            "signer": self.signer,
        }
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))

    @classmethod
    def from_json_line(cls, line: str) -> 'CommandActivityEvent':
        """Parse from JSON line (handles both V1 and V2 formats)."""
        data = json.loads(line.strip())

        # V1 format detection: has 'field' but not 'changes'
        if 'field' in data and 'changes' not in data:
            return cls._from_v1_data(data)

        # V2 format
        changes = [FieldChange.from_dict(c) for c in data.get("changes", [])]
        return cls(
            id=data.get("id", _generate_ulid()),
            timestamp=data["timestamp"],
            command=data.get("command", "[legacy]"),
            object_type=data["object_type"],
            object_id=data["object_id"],
            changes=changes,
            file_path=data.get("file_path", ""),
            file_hash_before=data.get("file_hash_before"),
            file_hash_after=data.get("file_hash_after"),
            changed_by=data.get("changed_by", "cli"),
            reason=data.get("reason"),
            signature=data.get("signature"),
            signer=data.get("signer"),
        )

    @classmethod
    def _from_v1_data(cls, data: Dict[str, Any]) -> 'CommandActivityEvent':
        """Convert V1 field-level data to V2 command-level format."""
        return cls(
            id=data.get("id", _generate_ulid()),
            timestamp=data["timestamp"],
            command=f"[v1-{data.get('source', 'manual')}]",
            object_type=data["object_type"],
            object_id=data["object_id"],
            changes=[FieldChange(
                field=data["field"],
                old=data.get("old_value"),
                new=data.get("new_value"),
            )],
            file_path="",
            file_hash_before=None,
            file_hash_after=None,
            changed_by=data.get("changed_by", "cli"),
            reason=data.get("reason"),
            signature=None,
            signer=None,
        )

    def canonical_bytes(self) -> bytes:
        """
        Deterministic serialization for signing.

        Only specific fields are included to ensure reproducible signatures.
        """
        # Sort changes by field name for determinism
        sorted_changes = sorted(
            [{"field": c.field, "old": c.old, "new": c.new} for c in self.changes],
            key=lambda c: c["field"]
        )

        data = {
            "id": self.id,
            "timestamp": self.timestamp,
            "command": self.command,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "changes": sorted_changes,
            "file_hash_before": self.file_hash_before,
            "file_hash_after": self.file_hash_after,
        }

        return json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')

    def to_v1_events(self) -> List['ActivityEvent']:
        """Convert to list of V1 ActivityEvent objects (for backward compat)."""
        events = []
        for change in self.changes:
            events.append(ActivityEvent(
                timestamp=self.timestamp,
                object_type=self.object_type,
                object_id=self.object_id,
                field=change.field,
                old_value=change.old,
                new_value=change.new,
                changed_by=self.changed_by,
                reason=self.reason,
                commit=None,
                source="v2",
            ))
        return events


# =============================================================================
# V1 Schema: Field-Level Granularity (Legacy, kept for backward compatibility)
# =============================================================================

@dataclass
class ActivityEvent:
    """
    Single activity event for JSONL storage.

    Mirrors AuditEntry but optimized for JSONL format.
    """
    timestamp: str
    object_type: str  # "track", "sprint", "task", "roadmap"
    object_id: str
    field: str
    old_value: Any
    new_value: Any
    changed_by: str
    reason: Optional[str] = None
    commit: Optional[str] = None
    source: str = "manual"

    def to_json_line(self) -> str:
        """Convert to JSON line (without trailing newline)."""
        return json.dumps(asdict(self), ensure_ascii=False, separators=(',', ':'))

    @classmethod
    def from_json_line(cls, line: str) -> 'ActivityEvent':
        """Parse from JSON line."""
        data = json.loads(line.strip())
        return cls(**data)

    @classmethod
    def from_audit_entry(cls, entry) -> 'ActivityEvent':
        """
        Convert from legacy AuditEntry.

        Args:
            entry: AuditEntry instance from audit_trail.py

        Returns:
            ActivityEvent with same data
        """
        return cls(
            timestamp=entry.timestamp,
            object_type=entry.object_type,
            object_id=entry.object_id,
            field=entry.field,
            old_value=entry.old_value,
            new_value=entry.new_value,
            changed_by=entry.changed_by,
            reason=entry.reason,
            commit=entry.commit,
            source=entry.source,
        )


class ActivityLogWriter:
    """
    Writes activity events to time-bucketed JSONL files.

    File format: .vibey/roadmap/activity_log/YYYY-MM.jsonl
    Each line is a complete JSON object representing one event.
    """

    def __init__(self, activity_log_dir: Path):
        """
        Initialize writer.

        Args:
            activity_log_dir: Path to activity_log directory
        """
        self.activity_log_dir = Path(activity_log_dir)
        self.activity_log_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_for_timestamp(self, timestamp: str) -> Path:
        """
        Get JSONL file path for a given timestamp.

        Args:
            timestamp: ISO format timestamp (e.g., "2025-11-15T10:30:00+00:00")

        Returns:
            Path to JSONL file for that month
        """
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            # Fallback to current time if timestamp is invalid
            dt = datetime.now(timezone.utc)

        filename = f"{dt.year}-{dt.month:02d}.jsonl"
        return self.activity_log_dir / filename

    def _get_current_file(self) -> Path:
        """Get JSONL file for current month."""
        now = datetime.now(timezone.utc)
        filename = f"{now.year}-{now.month:02d}.jsonl"
        return self.activity_log_dir / filename

    def write_event(self, event: ActivityEvent) -> None:
        """
        Write a single event to the appropriate JSONL file.

        Uses file locking for concurrent write safety.

        Args:
            event: ActivityEvent to write
        """
        file_path = self._get_file_for_timestamp(event.timestamp)
        json_line = event.to_json_line()

        # Append with file locking
        with open(file_path, 'a', encoding='utf-8') as f:
            try:
                _lock_file(f)
                f.write(json_line + '\n')
            finally:
                _unlock_file(f)

    def write_events(self, events: list[ActivityEvent]) -> None:
        """
        Write multiple events to appropriate JSONL files.

        Events are grouped by month for efficient writes.

        Args:
            events: List of ActivityEvents to write
        """
        # Group events by target file
        events_by_file: dict[Path, list[ActivityEvent]] = {}
        for event in events:
            file_path = self._get_file_for_timestamp(event.timestamp)
            if file_path not in events_by_file:
                events_by_file[file_path] = []
            events_by_file[file_path].append(event)

        # Write each group
        for file_path, file_events in events_by_file.items():
            lines = [e.to_json_line() + '\n' for e in file_events]

            with open(file_path, 'a', encoding='utf-8') as f:
                try:
                    _lock_file(f)
                    f.writelines(lines)
                finally:
                    _unlock_file(f)

    def log_change(
        self,
        object_type: str,
        object_id: str,
        field: str,
        old_value: Any,
        new_value: Any,
        changed_by: str = "cli",
        reason: Optional[str] = None,
        commit: Optional[str] = None,
        source: str = "manual",
    ) -> ActivityEvent:
        """
        Log a change event (convenience method matching AuditTrailManager API).

        Args:
            object_type: Type of object changed (track, sprint, task, roadmap)
            object_id: ID of the object
            field: Field that was changed
            old_value: Previous value
            new_value: New value
            changed_by: Who made the change
            reason: Optional reason for change
            commit: Optional git commit hash
            source: Source of change (manual, cli, api, etc.)

        Returns:
            The created ActivityEvent
        """
        event = ActivityEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
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

        self.write_event(event)
        return event

    # =========================================================================
    # V2 Methods: Command-Level Logging
    # =========================================================================

    def write_command_event(self, event: CommandActivityEvent) -> None:
        """
        Write a V2 command-level event to the appropriate JSONL file.

        Uses file locking for concurrent write safety.

        Args:
            event: CommandActivityEvent to write
        """
        file_path = self._get_file_for_timestamp(event.timestamp)
        json_line = event.to_json_line()

        # Append with file locking
        with open(file_path, 'a', encoding='utf-8') as f:
            try:
                _lock_file(f)
                f.write(json_line + '\n')
            finally:
                _unlock_file(f)

    def log_command(
        self,
        command: str,
        object_type: str,
        object_id: str,
        changes: List[FieldChange],
        file_path: Path,
        file_hash_before: Optional[str] = None,
        changed_by: str = "cli",
        reason: Optional[str] = None,
    ) -> CommandActivityEvent:
        """
        Log a command-level event (V2 schema).

        Automatically computes file_hash_after from the current file state.
        Signs the event if signing is enabled (user has keypair).

        Args:
            command: Full CLI command string
            object_type: Type of object changed (track, sprint, task, roadmap)
            object_id: ID of the object
            changes: List of field changes
            file_path: Path to the modified YAML file
            file_hash_before: SHA256 hash before change (None for create)
            changed_by: Who made the change (default: "cli")
            reason: Optional reason for change

        Returns:
            The created CommandActivityEvent
        """
        # Compute file hash after the change
        file_hash_after = None
        if file_path.exists():
            file_hash_after = compute_file_hash(file_path)

        # Generate event (without signature first)
        event = CommandActivityEvent(
            id=_generate_ulid(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            command=command,
            object_type=object_type,
            object_id=object_id,
            changes=changes,
            file_path=str(file_path),
            file_hash_before=file_hash_before,
            file_hash_after=file_hash_after,
            changed_by=changed_by,
            reason=reason,
            signature=None,
            signer=None,
        )

        # Try to sign the event (graceful degradation if signing unavailable)
        try:
            from vibey.operations.auth import sign_activity_entry, signing_enabled
            if signing_enabled():
                # Build entry dict for signing (same fields as canonical)
                entry_dict = {
                    'id': event.id,
                    'timestamp': event.timestamp,
                    'command': event.command,
                    'object_type': event.object_type,
                    'object_id': event.object_id,
                    'changes': [c.to_dict() for c in event.changes],
                    'file_path': event.file_path,
                    'file_hash_after': event.file_hash_after,
                }
                result = sign_activity_entry(entry_dict)
                if result.signed:
                    event.signature = result.signature
                    event.signer = result.signer
        except ImportError:
            # Signing module not available, continue without signing
            pass
        except Exception:
            # Any signing error, continue without signing
            pass

        self.write_command_event(event)
        return event


class ActivityLogReader:
    """
    Reads activity events from time-bucketed JSONL files.

    Supports streaming reads and filtering.

    Performance characteristics:
    - Hash index provides O(1) lookups for verification
    - Index is cached after first build (cleared on invalidate)
    - Time-bucketed files allow efficient date range queries
    - Streaming API for memory-efficient large log processing
    """

    def __init__(self, activity_log_dir: Path):
        """
        Initialize reader.

        Args:
            activity_log_dir: Path to activity_log directory
        """
        self.activity_log_dir = Path(activity_log_dir)
        # Cached hash index for fast repeated lookups
        self._hash_index_cache: Optional[Dict[str, 'CommandActivityEvent']] = None
        self._hash_index_timestamp: Optional[float] = None

    def _get_log_files(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Path]:
        """
        Get list of JSONL files in date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            List of JSONL file paths, sorted by date
        """
        if not self.activity_log_dir.exists():
            return []

        files = list(self.activity_log_dir.glob("*.jsonl"))

        # Parse dates from filenames
        dated_files = []
        for f in files:
            try:
                # Parse YYYY-MM.jsonl
                year, month = f.stem.split('-')
                file_date = datetime(int(year), int(month), 1, tzinfo=timezone.utc)
                dated_files.append((file_date, f))
            except (ValueError, IndexError):
                continue  # Skip malformed filenames

        # Filter by date range
        if start_date:
            start_month = datetime(start_date.year, start_date.month, 1, tzinfo=timezone.utc)
            dated_files = [(d, f) for d, f in dated_files if d >= start_month]

        if end_date:
            end_month = datetime(end_date.year, end_date.month, 1, tzinfo=timezone.utc)
            dated_files = [(d, f) for d, f in dated_files if d <= end_month]

        # Sort by date
        dated_files.sort(key=lambda x: x[0])

        return [f for _, f in dated_files]

    def _read_file(self, file_path: Path) -> Iterator[ActivityEvent]:
        """
        Stream V1 events from a single JSONL file.

        Args:
            file_path: Path to JSONL file

        Yields:
            ActivityEvent objects (V1 format)
        """
        if not file_path.exists():
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    event = ActivityEvent.from_json_line(line)
                    yield event
                except json.JSONDecodeError as e:
                    # Log warning but continue
                    print(f"Warning: Invalid JSON at {file_path}:{line_num}: {e}",
                          file=sys.stderr)
                    continue

    def _read_file_v2(self, file_path: Path) -> Iterator[CommandActivityEvent]:
        """
        Stream V2 command events from a single JSONL file.

        Handles both V1 and V2 formats, converting V1 to V2 on the fly.

        Args:
            file_path: Path to JSONL file

        Yields:
            CommandActivityEvent objects
        """
        if not file_path.exists():
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    event = CommandActivityEvent.from_json_line(line)
                    yield event
                except json.JSONDecodeError as e:
                    print(f"Warning: Invalid JSON at {file_path}:{line_num}: {e}",
                          file=sys.stderr)
                    continue

    def stream_command_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        object_type: Optional[str] = None,
        object_id: Optional[str] = None,
    ) -> Iterator[CommandActivityEvent]:
        """
        Stream V2 command events matching filters.

        Args:
            start_date: Start of date range
            end_date: End of date range
            object_type: Filter by object type
            object_id: Filter by object ID

        Yields:
            Matching CommandActivityEvent objects
        """
        files = self._get_log_files(start_date, end_date)

        for file_path in files:
            for event in self._read_file_v2(file_path):
                # Apply filters
                if object_type and event.object_type != object_type:
                    continue
                if object_id and event.object_id != object_id:
                    continue

                # Check timestamp range
                if start_date or end_date:
                    try:
                        event_time = datetime.fromisoformat(
                            event.timestamp.replace('Z', '+00:00')
                        )
                        if start_date and event_time < start_date:
                            continue
                        if end_date and event_time > end_date:
                            continue
                    except ValueError:
                        continue

                yield event

    def find_by_hash(self, file_hash: str) -> Optional[CommandActivityEvent]:
        """
        Find a command event by file_hash_after.

        Used for verification: checks if a file's current state
        has a corresponding activity log entry.

        Args:
            file_hash: SHA256 hash to search for

        Returns:
            CommandActivityEvent if found, None otherwise
        """
        # Search through all files (most recent first for efficiency)
        files = self._get_log_files()
        files.reverse()  # Most recent first

        for file_path in files:
            for event in self._read_file_v2(file_path):
                if event.file_hash_after == file_hash:
                    return event

        return None

    def build_hash_index(self, use_cache: bool = True) -> Dict[str, CommandActivityEvent]:
        """
        Build an index of file_hash_after -> event for fast lookups.

        Useful for batch verification operations. The index is cached
        after first build and reused for subsequent calls.

        Args:
            use_cache: Whether to use cached index if available

        Returns:
            Dictionary mapping file hashes to events

        Performance:
        - First call: O(n) where n is total events
        - Subsequent calls: O(1) if cached
        - Cache is auto-invalidated when log files change
        """
        # Check cache validity
        if use_cache and self._hash_index_cache is not None:
            # Check if any log files have been modified
            current_mtime = self._get_latest_log_mtime()
            if current_mtime == self._hash_index_timestamp:
                return self._hash_index_cache

        # Build fresh index
        index: Dict[str, CommandActivityEvent] = {}

        for file_path in self._get_log_files():
            for event in self._read_file_v2(file_path):
                if event.file_hash_after:
                    index[event.file_hash_after] = event

        # Cache the result
        self._hash_index_cache = index
        self._hash_index_timestamp = self._get_latest_log_mtime()

        return index

    def _get_latest_log_mtime(self) -> Optional[float]:
        """Get modification time of most recent log file."""
        files = self._get_log_files()
        if not files:
            return None
        # Get the mtime of the most recent file
        return max(f.stat().st_mtime for f in files)

    def invalidate_cache(self) -> None:
        """Invalidate the hash index cache."""
        self._hash_index_cache = None
        self._hash_index_timestamp = None

    def stream_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        object_type: Optional[str] = None,
        object_id: Optional[str] = None,
        field: Optional[str] = None,
    ) -> Iterator[ActivityEvent]:
        """
        Stream events matching filters.

        Args:
            start_date: Start of date range
            end_date: End of date range
            object_type: Filter by object type (track, sprint, task, roadmap)
            object_id: Filter by object ID
            field: Filter by field name

        Yields:
            Matching ActivityEvent objects
        """
        files = self._get_log_files(start_date, end_date)

        for file_path in files:
            for event in self._read_file(file_path):
                # Apply filters
                if object_type and event.object_type != object_type:
                    continue
                if object_id and event.object_id != object_id:
                    continue
                if field and event.field != field:
                    continue

                # Check timestamp range
                if start_date or end_date:
                    try:
                        event_time = datetime.fromisoformat(
                            event.timestamp.replace('Z', '+00:00')
                        )
                        if start_date and event_time < start_date:
                            continue
                        if end_date and event_time > end_date:
                            continue
                    except ValueError:
                        continue  # Skip events with invalid timestamps

                yield event

    def get_history(
        self,
        object_type: Optional[str] = None,
        object_id: Optional[str] = None,
        limit: int = 50,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ActivityEvent]:
        """
        Get activity history with filters (matches AuditTrailManager API).

        Args:
            object_type: Filter by object type
            object_id: Filter by object ID
            limit: Maximum events to return
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of ActivityEvent objects, newest first
        """
        events = list(self.stream_events(
            start_date=start_date,
            end_date=end_date,
            object_type=object_type,
            object_id=object_id,
        ))

        # Sort by timestamp descending (newest first)
        events.sort(key=lambda e: e.timestamp, reverse=True)

        return events[:limit]

    def get_object_history(
        self,
        object_type: str,
        object_id: str,
        limit: int = 50,
    ) -> List[ActivityEvent]:
        """
        Get history for a specific object.

        Args:
            object_type: Object type (track, sprint, task, roadmap)
            object_id: Object ID
            limit: Maximum events to return

        Returns:
            List of ActivityEvent objects, newest first
        """
        return self.get_history(
            object_type=object_type,
            object_id=object_id,
            limit=limit,
        )

    def get_recent_activity(
        self,
        limit: int = 50,
        days: int = 30,
    ) -> List[ActivityEvent]:
        """
        Get recent activity across all objects.

        Args:
            limit: Maximum events to return
            days: Number of days to look back

        Returns:
            List of ActivityEvent objects, newest first
        """
        from datetime import timedelta

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        return self.get_history(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

    def count_events(
        self,
        object_type: Optional[str] = None,
        object_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Count events matching filters (without loading all into memory).

        Args:
            object_type: Filter by object type
            object_id: Filter by object ID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Count of matching events
        """
        count = 0
        for _ in self.stream_events(
            start_date=start_date,
            end_date=end_date,
            object_type=object_type,
            object_id=object_id,
        ):
            count += 1
        return count
