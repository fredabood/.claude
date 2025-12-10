# Task 004: Migrate Existing audit-trail.yaml to JSONL

**Task ID:** dogfooding-bugs-07-task-004
**Bug Addressed:** #13 (Activity Log Not Migrated to JSONL Format)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

The existing `audit-trail.yaml` file (1,684 lines) contains valuable historical data that must be migrated to the new JSONL format. The migration must:

1. Read all entries from the YAML file
2. Convert each entry to ActivityEvent format
3. Write to appropriate time-bucketed JSONL files
4. Provide verification and rollback options
5. Handle edge cases (duplicates, invalid data)

---

## Current State

**Current File:**
```
.vibey/roadmap/audit-trail.yaml   # 1,684 lines, monolithic YAML
```

**Target Format:**
```
.vibey/roadmap/activity_log/
├── 2025-10.jsonl    # October 2025 events (if any)
├── 2025-11.jsonl    # November 2025 events
├── 2025-12.jsonl    # December 2025 events
└── ...
```

**Current Data Structure (audit_trail.py):**
```yaml
entries:
  - timestamp: "2025-11-15T10:30:00+00:00"
    object_type: "task"
    object_id: "task_123"
    field: "status"
    old_value: "not_started"
    new_value: "in_progress"
    changed_by: "cli"
    reason: null
    commit: null
    source: "manual"
  - ...
```

---

## Implementation

### 1. Create Migration Module

```python
# vibey/operations/roadmap/migrate_activity_log.py

"""
Migration tool for audit-trail.yaml → JSONL activity log.

Usage:
    from vibey.operations.roadmap.migrate_activity_log import ActivityLogMigrator

    migrator = ActivityLogMigrator(Path.cwd())
    report = migrator.migrate(dry_run=True)  # Preview
    report = migrator.migrate(dry_run=False) # Execute
"""

import yaml
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional
import shutil


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
        self.root_dir = root_dir
        self.vibey_dir = root_dir / ".vibey"
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

        return data.get("entries", [])

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
            from collections import defaultdict
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
```

### 2. Add CLI Command

```python
# vibey/cli/commands.py (add to roadmap commands)

@roadmap.command()
@click.option('--dry-run', is_flag=True, help='Preview migration without writing')
@click.option('--no-backup', is_flag=True, help='Skip backup creation')
@click.option('--delete-source', is_flag=True, help='Delete YAML after migration')
def migrate_activity_log(dry_run: bool, no_backup: bool, delete_source: bool):
    """Migrate audit-trail.yaml to JSONL activity log format."""
    from vibey.operations.roadmap.migrate_activity_log import ActivityLogMigrator

    migrator = ActivityLogMigrator(Path.cwd())

    # Show analysis first
    analysis = migrator.analyze()
    click.echo(f"Source file: {migrator.yaml_file}")
    click.echo(f"Total entries: {analysis['total_entries']}")
    click.echo(f"Valid entries: {analysis['valid_entries']}")
    click.echo(f"Invalid entries: {analysis['invalid_entries']}")

    if analysis['date_range']:
        click.echo(f"Date range: {analysis['date_range']['earliest']} to {analysis['date_range']['latest']}")

    if analysis['issues']:
        click.echo(f"\nIssues found:")
        for issue in analysis['issues']:
            click.echo(f"  - {issue}")

    click.echo("")

    # Run migration
    report = migrator.migrate(
        dry_run=dry_run,
        backup=not no_backup,
        delete_source=delete_source,
    )

    if dry_run:
        click.echo("DRY RUN - No changes made")

    click.echo(f"\nMigration {'would create' if dry_run else 'created'}:")
    click.echo(f"  Entries migrated: {report.migrated_entries}")
    click.echo(f"  Entries skipped: {report.skipped_entries}")
    click.echo(f"  Files: {', '.join(report.files_created)}")

    if report.errors:
        click.echo(f"\nErrors:")
        for error in report.errors:
            click.echo(f"  - {error}")

    if report.is_success():
        click.echo("\n✅ Migration successful")
    else:
        click.echo("\n⚠️  Migration completed with issues")
```

---

## Files to Create/Modify

| File | Changes |
|------|---------|
| `vibey/operations/roadmap/migrate_activity_log.py` | NEW: Migration module |
| `vibey/cli/commands.py` | Add `migrate-activity-log` command |

---

## Testing Strategy

```python
# tests/operations/roadmap/test_migrate_activity_log.py

import pytest
import yaml
from pathlib import Path


class TestActivityLogMigrator:
    """Tests for ActivityLogMigrator."""

    @pytest.fixture
    def project_with_yaml(self, tmp_path):
        """Create project with audit-trail.yaml."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)

        yaml_data = {
            "entries": [
                {
                    "timestamp": "2025-11-15T10:00:00+00:00",
                    "object_type": "task",
                    "object_id": "task_001",
                    "field": "status",
                    "old_value": "not_started",
                    "new_value": "in_progress",
                    "changed_by": "cli",
                    "reason": None,
                    "commit": None,
                    "source": "manual",
                },
                {
                    "timestamp": "2025-12-01T10:00:00+00:00",
                    "object_type": "sprint",
                    "object_id": "sprint_001",
                    "field": "status",
                    "old_value": "not_started",
                    "new_value": "completed",
                    "changed_by": "cli",
                    "reason": "Work done",
                    "commit": "abc123",
                    "source": "manual",
                },
            ]
        }

        yaml_file = roadmap_dir / "audit-trail.yaml"
        with open(yaml_file, 'w') as f:
            yaml.safe_dump(yaml_data, f)

        return tmp_path

    def test_analyze_reports_entries(self, project_with_yaml):
        """analyze() reports entry statistics."""
        from vibey.operations.roadmap.migrate_activity_log import ActivityLogMigrator

        migrator = ActivityLogMigrator(project_with_yaml)
        analysis = migrator.analyze()

        assert analysis["total_entries"] == 2
        assert analysis["valid_entries"] == 2
        assert analysis["invalid_entries"] == 0

    def test_dry_run_no_files_created(self, project_with_yaml):
        """Dry run doesn't create files."""
        from vibey.operations.roadmap.migrate_activity_log import ActivityLogMigrator

        migrator = ActivityLogMigrator(project_with_yaml)
        report = migrator.migrate(dry_run=True)

        assert report.dry_run is True
        assert report.migrated_entries == 2
        assert len(report.files_created) == 2  # Nov and Dec
        assert not migrator.activity_log_dir.exists()

    def test_migrate_creates_jsonl_files(self, project_with_yaml):
        """Migration creates JSONL files."""
        from vibey.operations.roadmap.migrate_activity_log import ActivityLogMigrator

        migrator = ActivityLogMigrator(project_with_yaml)
        report = migrator.migrate(dry_run=False)

        assert report.dry_run is False
        assert migrator.activity_log_dir.exists()
        assert (migrator.activity_log_dir / "2025-11.jsonl").exists()
        assert (migrator.activity_log_dir / "2025-12.jsonl").exists()

    def test_migrate_creates_backup(self, project_with_yaml):
        """Migration creates backup of YAML file."""
        from vibey.operations.roadmap.migrate_activity_log import ActivityLogMigrator

        migrator = ActivityLogMigrator(project_with_yaml)
        migrator.migrate(dry_run=False, backup=True)

        backups = list(migrator.backup_dir.glob("audit-trail_*.yaml"))
        assert len(backups) == 1

    def test_verify_compares_counts(self, project_with_yaml):
        """verify() compares YAML and JSONL entry counts."""
        from vibey.operations.roadmap.migrate_activity_log import ActivityLogMigrator

        migrator = ActivityLogMigrator(project_with_yaml)
        migrator.migrate(dry_run=False)

        result = migrator.verify()

        assert result["yaml_entries"] == 2
        assert result["jsonl_entries"] == 2
        assert result["match"] is True

    def test_rollback_restores_yaml(self, project_with_yaml):
        """rollback() restores from backup."""
        from vibey.operations.roadmap.migrate_activity_log import ActivityLogMigrator

        migrator = ActivityLogMigrator(project_with_yaml)
        migrator.migrate(dry_run=False, backup=True, delete_source=True)

        # YAML should be deleted
        assert not migrator.yaml_file.exists()

        # Rollback
        success = migrator.rollback()

        assert success
        assert migrator.yaml_file.exists()

    def test_handles_invalid_entries(self, tmp_path):
        """Migration handles invalid entries gracefully."""
        from vibey.operations.roadmap.migrate_activity_log import ActivityLogMigrator

        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)

        yaml_data = {
            "entries": [
                {"timestamp": "2025-11-15T10:00:00+00:00", "object_type": "task"},  # Missing fields
                {
                    "timestamp": "2025-11-15T10:00:00+00:00",
                    "object_type": "task",
                    "object_id": "task_001",
                    "field": "status",
                    "old_value": "a",
                    "new_value": "b",
                    "changed_by": "cli",
                },
            ]
        }

        with open(roadmap_dir / "audit-trail.yaml", 'w') as f:
            yaml.safe_dump(yaml_data, f)

        migrator = ActivityLogMigrator(tmp_path)
        report = migrator.migrate(dry_run=False)

        assert report.total_entries == 2
        assert report.migrated_entries == 1
        assert report.skipped_entries == 1
        assert len(report.errors) >= 1
```

---

## Success Criteria

- [ ] `ActivityLogMigrator` class created
- [ ] `analyze()` reports entry statistics
- [ ] `migrate(dry_run=True)` previews without changes
- [ ] `migrate(dry_run=False)` creates JSONL files
- [ ] Backup created before migration
- [ ] Invalid entries skipped with errors reported
- [ ] `verify()` compares entry counts
- [ ] `rollback()` restores from backup
- [ ] CLI command `vibey roadmap migrate-activity-log` works
- [ ] All tests pass

---

## Dependencies

- Task 001 (directory structure)
- Task 002 (JSONL writer)
- Task 003 (JSONL reader for verification)

---

## Notes

### Migration Safety

1. **Dry run first** - Always preview with `--dry-run`
2. **Automatic backup** - YAML file backed up before changes
3. **Verification** - Entry counts compared after migration
4. **Rollback available** - Can restore from backup if needed

### Example Migration Session

```bash
# 1. Analyze source file
vibey roadmap migrate-activity-log --dry-run

# Output:
# Source file: .vibey/roadmap/audit-trail.yaml
# Total entries: 1684
# Valid entries: 1680
# Invalid entries: 4
# Date range: 2025-10-01T... to 2025-12-10T...
#
# DRY RUN - No changes made
# Migration would create:
#   Entries migrated: 1680
#   Entries skipped: 4
#   Files: 2025-10.jsonl, 2025-11.jsonl, 2025-12.jsonl

# 2. Run actual migration
vibey roadmap migrate-activity-log

# 3. Verify
vibey roadmap migrate-activity-log --verify

# 4. If needed, rollback
vibey roadmap migrate-activity-log --rollback
```
