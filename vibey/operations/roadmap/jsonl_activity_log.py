"""
JSONL-based activity log for roadmap state changes.

Provides time-bucketed activity logging with efficient append-only writes.
Each month's events are stored in a separate JSONL file.

File format: .vibey/roadmap/activity_log/YYYY-MM.jsonl
Each line is a complete JSON object representing one event.
"""

import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Iterator, List


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


class ActivityLogReader:
    """
    Reads activity events from time-bucketed JSONL files.

    Supports streaming reads and filtering.
    """

    def __init__(self, activity_log_dir: Path):
        """
        Initialize reader.

        Args:
            activity_log_dir: Path to activity_log directory
        """
        self.activity_log_dir = Path(activity_log_dir)

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
        Stream events from a single JSONL file.

        Args:
            file_path: Path to JSONL file

        Yields:
            ActivityEvent objects
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
