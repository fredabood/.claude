"""
Migration tool for audit-trail.yaml → JSONL activity log.

Usage:
    from vibey.operations.roadmap.migrate_activity_log import ActivityLogMigrator

    migrator = ActivityLogMigrator(Path.cwd())
    report = migrator.migrate(dry_run=True)  # Preview
    report = migrator.migrate(dry_run=False) # Execute
"""

import shutil
import yaml
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class MigrationReport:
    """Report of migration results."""
    total_entries: int
    migrated_entries: int
    skipped_entries: int
    files_created: List[str]
    errors: List[str]
    dry_run: bool

    def is_success(self) -> bool:
        return len(self.errors) == 0 and self.migrated_entries == self.total_entries


class ActivityLogMigrator:
    """
    Migrates audit-trail.yaml to JSONL activity log format.
    """

    def __init__(self, root_dir: Path):
        """
        Initialize migrator.

        Args:
            root_dir: Project root directory
        """
        self.root_dir = Path(root_dir)
        self.vibey_dir = self.root_dir / ".vibey"
        self.roadmap_dir = self.vibey_dir / "roadmap"

        # Source and destination
        self.yaml_file = self.roadmap_dir / "audit-trail.yaml"
        self.activity_log_dir = self.roadmap_dir / "activity_log"

        # Backup location
        self.backup_dir = self.vibey_dir / "backups" / "activity_log_migration"

    def _load_yaml_entries(self) -> List[Dict]:
        """Load entries from audit-trail.yaml."""
        if not self.yaml_file.exists():
            return []

        with open(self.yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data:
            return []

        # Support both "entries" (legacy) and "audit_log" (current) keys
        return data.get("entries", data.get("audit_log", []))

    def _backup_yaml_file(self) -> Path:
        """Create backup of original YAML file."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"audit-trail_{timestamp}.yaml"

        shutil.copy2(self.yaml_file, backup_path)
        return backup_path

    def _validate_entry(self, entry: Dict) -> Optional[str]:
        """
        Validate an entry has required fields.

        Returns error message or None if valid.
        """
        required = ["timestamp", "object_type", "object_id", "field"]
        for field in required:
            if field not in entry:
                return f"Missing required field: {field}"

        # Validate timestamp format
        try:
            ts = entry["timestamp"]
            if isinstance(ts, str):
                datetime.fromisoformat(ts.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return f"Invalid timestamp format: {entry.get('timestamp')}"

        return None

    def _convert_entry(self, entry: Dict) -> 'ActivityEvent':
        """Convert YAML entry to ActivityEvent."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityEvent

        # Handle timestamp conversion
        timestamp = entry.get("timestamp", "")
        if isinstance(timestamp, datetime):
            timestamp = timestamp.isoformat()

        return ActivityEvent(
            timestamp=timestamp,
            object_type=entry.get("object_type", "unknown"),
            object_id=entry.get("object_id", "unknown"),
            field=entry.get("field", "unknown"),
            old_value=entry.get("old_value"),
            new_value=entry.get("new_value"),
            changed_by=entry.get("changed_by", "unknown"),
            reason=entry.get("reason"),
            commit=entry.get("commit"),
            source=entry.get("source", "migrated"),
        )

    def analyze(self) -> Dict:
        """
        Analyze the source YAML file.

        Returns:
            Analysis report including entry count, date range, issues
        """
        entries = self._load_yaml_entries()

        if not entries:
            return {
                "total_entries": 0,
                "valid_entries": 0,
                "invalid_entries": 0,
                "date_range": None,
                "issues": [],
            }

        valid = 0
        invalid = 0
        issues = []
        timestamps = []

        for i, entry in enumerate(entries):
            error = self._validate_entry(entry)
            if error:
                invalid += 1
                issues.append(f"Entry {i}: {error}")
            else:
                valid += 1
                try:
                    ts = entry["timestamp"]
                    if isinstance(ts, str):
                        timestamps.append(datetime.fromisoformat(ts.replace('Z', '+00:00')))
                    elif isinstance(ts, datetime):
                        timestamps.append(ts)
                except:
                    pass

        date_range = None
        if timestamps:
            date_range = {
                "earliest": min(timestamps).isoformat(),
                "latest": max(timestamps).isoformat(),
            }

        return {
            "total_entries": len(entries),
            "valid_entries": valid,
            "invalid_entries": invalid,
            "date_range": date_range,
            "issues": issues[:10],  # First 10 issues
        }

    def migrate(
        self,
        dry_run: bool = True,
        backup: bool = True,
        delete_source: bool = False,
    ) -> MigrationReport:
        """
        Migrate audit-trail.yaml to JSONL format.

        Args:
            dry_run: If True, report what would happen without writing
            backup: If True, backup YAML file before migration
            delete_source: If True, delete YAML file after successful migration

        Returns:
            MigrationReport with results
        """
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogWriter

        entries = self._load_yaml_entries()

        if not entries:
            return MigrationReport(
                total_entries=0,
                migrated_entries=0,
                skipped_entries=0,
                files_created=[],
                errors=["No entries found in audit-trail.yaml"],
                dry_run=dry_run,
            )

        # Validate and convert entries
        events = []
        errors = []
        skipped = 0

        for i, entry in enumerate(entries):
            error = self._validate_entry(entry)
            if error:
                errors.append(f"Entry {i}: {error}")
                skipped += 1
                continue

            try:
                event = self._convert_entry(entry)
                events.append(event)
            except Exception as e:
                errors.append(f"Entry {i}: Conversion error - {e}")
                skipped += 1

        if dry_run:
            # Calculate what files would be created
            files_by_month = defaultdict(int)
            for event in events:
                try:
                    dt = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
                    key = f"{dt.year}-{dt.month:02d}.jsonl"
                    files_by_month[key] += 1
                except:
                    pass

            return MigrationReport(
                total_entries=len(entries),
                migrated_entries=len(events),
                skipped_entries=skipped,
                files_created=sorted(files_by_month.keys()),
                errors=errors[:20],  # First 20 errors
                dry_run=True,
            )

        # Actual migration
        if backup:
            backup_path = self._backup_yaml_file()
            print(f"Backup created: {backup_path}")

        # Write to JSONL
        self.activity_log_dir.mkdir(parents=True, exist_ok=True)
        writer = ActivityLogWriter(self.activity_log_dir)
        writer.write_events(events)

        # Determine files created
        files_created = sorted([f.name for f in self.activity_log_dir.glob("*.jsonl")])

        # Optionally delete source
        if delete_source and not errors:
            self.yaml_file.unlink()

        return MigrationReport(
            total_entries=len(entries),
            migrated_entries=len(events),
            skipped_entries=skipped,
            files_created=files_created,
            errors=errors[:20],
            dry_run=False,
        )

    def verify(self) -> Dict:
        """
        Verify migration by comparing entry counts.

        Returns:
            Verification report
        """
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        # Count YAML entries
        yaml_entries = self._load_yaml_entries()
        yaml_count = len(yaml_entries)

        # Count JSONL entries
        reader = ActivityLogReader(self.activity_log_dir)
        jsonl_count = reader.count_events()

        return {
            "yaml_entries": yaml_count,
            "jsonl_entries": jsonl_count,
            "match": yaml_count == jsonl_count,
            "difference": yaml_count - jsonl_count,
        }

    def rollback(self) -> bool:
        """
        Rollback migration by restoring from backup.

        Returns:
            True if rollback successful
        """
        # Find most recent backup
        if not self.backup_dir.exists():
            print("No backup directory found")
            return False

        backups = sorted(self.backup_dir.glob("audit-trail_*.yaml"))
        if not backups:
            print("No backups found")
            return False

        latest_backup = backups[-1]

        # Restore
        shutil.copy2(latest_backup, self.yaml_file)

        # Remove JSONL files
        if self.activity_log_dir.exists():
            for f in self.activity_log_dir.glob("*.jsonl"):
                f.unlink()

        print(f"Restored from: {latest_backup}")
        return True
