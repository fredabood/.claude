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
    """Manages audit trail storage and operations."""

    def __init__(self, root_dir: Path):
        """
        Initialize audit trail manager.

        Args:
            root_dir: Project root directory containing .vibey/
        """
        self.root_dir = Path(root_dir)
        self.audit_file = self.root_dir / ".vibey" / "roadmap" / "audit-trail.yaml"
        self._ensure_audit_file()

    def _ensure_audit_file(self):
        """Ensure audit trail file exists."""
        if not self.audit_file.exists():
            self.audit_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_trail(AuditTrail())

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
        """Load audit trail from disk."""
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

        # Create audit entry
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            object_type=object_type,
            object_id=object_id,
            field=field,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            reason=reason,
            commit=self._get_current_commit(),
            source=source
        )

        # Add to trail and save
        trail = self.load_trail()
        trail.add_entry(entry)
        self._save_trail(trail)

        return entry

    def get_recent_changes(self, limit: int = 20) -> List[AuditEntry]:
        """Get recent audit entries."""
        trail = self.load_trail()
        return trail.get_recent(limit)

    def get_object_history(self, object_id: str) -> List[AuditEntry]:
        """Get all changes for a specific object."""
        trail = self.load_trail()
        return trail.get_for_object(object_id)

    def get_field_history(self, object_id: str, field: str) -> List[AuditEntry]:
        """Get history of changes to a specific field."""
        trail = self.load_trail()
        return trail.get_field_history(object_id, field)

    def detect_suspicious_changes(self) -> List[Tuple[AuditEntry, str]]:
        """
        Detect suspicious changes in the audit trail.

        Returns:
            List of (entry, reason) tuples for suspicious changes
        """
        trail = self.load_trail()
        suspicious = []

        for entry in trail.entries:
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
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Generate a human-readable audit report.

        Args:
            object_id: Filter by object ID (None = all)
            start_date: Filter by start date (None = no start filter)
            end_date: Filter by end date (None = no end filter)

        Returns:
            Formatted report string
        """
        trail = self.load_trail()
        entries = trail.entries

        # Apply filters
        if object_id:
            entries = [e for e in entries if e.object_id == object_id]

        if start_date:
            entries = [e for e in entries if datetime.fromisoformat(e.timestamp) >= start_date]

        if end_date:
            entries = [e for e in entries if datetime.fromisoformat(e.timestamp) <= end_date]

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
