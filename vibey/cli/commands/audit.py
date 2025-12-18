"""
Audit and activity commands.

Provides audit trail viewing, suspicious change detection, and activity reporting.
"""

from pathlib import Path
from typing import Optional


def audit_log_cmd(limit: int = 20) -> int:
    """Show recent audit trail entries."""
    from vibey.operations.roadmap.audit_trail import AuditTrailManager
    from datetime import datetime

    manager = AuditTrailManager(Path.cwd())
    entries = manager.get_recent_changes(limit=limit)

    if not entries:
        print("No audit trail entries found.")
        return 0

    print(f"\n📋 Recent Audit Trail Entries (last {limit})")
    print("=" * 80)

    for entry in entries:
        timestamp = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{timestamp} - {entry.object_type.upper()}: {entry.object_id}")
        print(f"  Field: {entry.field}")
        print(f"  Change: {entry.old_value} → {entry.new_value}")
        print(f"  By: {entry.changed_by} ({entry.source})")
        print(f"  Reason: {entry.reason}")
        if entry.commit:
            print(f"  Commit: {entry.commit}")

    print("\n" + "=" * 80)
    print(f"Total entries shown: {len(entries)}\n")
    return 0


def audit_show_cmd(object_id: str) -> int:
    """Show change history for a specific object."""
    from vibey.operations.roadmap.audit_trail import AuditTrailManager
    from datetime import datetime

    manager = AuditTrailManager(Path.cwd())
    entries = manager.get_object_history(object_id)

    if not entries:
        print(f"No audit trail entries found for object '{object_id}'.")
        return 0

    print(f"\n📋 Audit Trail for {object_id}")
    print("=" * 80)

    for entry in entries:
        timestamp = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{timestamp}")
        print(f"  Field: {entry.field}")
        print(f"  Change: {entry.old_value} → {entry.new_value}")
        print(f"  By: {entry.changed_by} ({entry.source})")
        print(f"  Reason: {entry.reason}")
        if entry.commit:
            print(f"  Commit: {entry.commit}")

    print("\n" + "=" * 80)
    print(f"Total changes: {len(entries)}\n")
    return 0


def audit_suspicious_cmd() -> int:
    """Detect suspicious changes in audit trail."""
    from vibey.operations.roadmap.audit_trail import AuditTrailManager
    from datetime import datetime

    manager = AuditTrailManager(Path.cwd())
    suspicious = manager.detect_suspicious_changes()

    if not suspicious:
        print("\n✅ No suspicious changes detected in audit trail.\n")
        return 0

    print(f"\n⚠️  Suspicious Changes Detected: {len(suspicious)}")
    print("=" * 80)

    for entry, reason in suspicious:
        timestamp = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n⚠️  {reason}")
        print(f"  Object: {entry.object_type.upper()} {entry.object_id}")
        print(f"  Field: {entry.field}")
        print(f"  Change: {entry.old_value} → {entry.new_value}")
        print(f"  When: {timestamp}")
        print(f"  By: {entry.changed_by} ({entry.source})")
        print(f"  Reason: {entry.reason}")
        if entry.commit:
            print(f"  Commit: {entry.commit}")

    print("\n" + "=" * 80)
    print(f"Total suspicious changes: {len(suspicious)}\n")
    return 1  # Return error code to indicate issues found


def audit_report_cmd(
    object_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> int:
    """Generate detailed audit report."""
    from vibey.operations.roadmap.audit_trail import AuditTrailManager
    from datetime import datetime

    manager = AuditTrailManager(Path.cwd())

    # Parse dates if provided
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            print(f"❌ Invalid start date format: {start_date}")
            print("   Expected format: YYYY-MM-DD")
            return 1

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            print(f"❌ Invalid end date format: {end_date}")
            print("   Expected format: YYYY-MM-DD")
            return 1

    # Generate report
    report = manager.generate_report(
        object_id=object_id,
        start_date=start_dt,
        end_date=end_dt
    )

    print(report)
    return 0


def activity_cmd(
    limit: int = 10,
    object_id: Optional[str] = None,
    activity_type: Optional[str] = None
) -> int:
    """Show recent activity in compact format.

    This provides a user-friendly view of recent roadmap activities,
    formatted as requested in the task description:
    2025-12-06 14:30  TASK_COMPLETED   task-123  claude-code
    2025-12-06 14:29  CRITERION_MET    task-123  Tests passed
    """
    from vibey.operations.roadmap.audit_trail import AuditTrailManager
    from datetime import datetime

    manager = AuditTrailManager(Path.cwd())

    # Get entries, either for a specific object or all
    if object_id:
        entries = manager.get_object_history(object_id)
        entries = entries[:limit] if limit else entries
    else:
        entries = manager.get_recent_changes(limit=limit)

    # Filter by activity type if specified
    if activity_type and entries:
        activity_type_lower = activity_type.lower()
        entries = [
            e for e in entries
            if activity_type_lower in e.field.lower()
            or activity_type_lower in str(e.new_value).lower()
        ]

    if not entries:
        print("No recent activity found.")
        return 0

    # Print header
    print(f"\n📊 Recent Activity (last {len(entries)})")
    print("-" * 70)

    # Print entries in compact format
    for entry in entries:
        try:
            timestamp = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            timestamp = str(entry.timestamp)[:16]

        # Determine activity type from field or new_value
        if entry.field == "status":
            event = f"{entry.old_value} → {entry.new_value}".upper()
        elif entry.field == "activity":
            event = str(entry.new_value).upper()
        elif entry.field.startswith("quality_gate."):
            event = f"GATE_{entry.new_value}".upper()
        elif entry.field.startswith("criterion."):
            event = f"CRITERION_{entry.new_value}".upper()
        elif entry.field == "transition_blocked":
            event = "BLOCKED"
        else:
            event = entry.field.upper()

        # Truncate event and ID for display
        event = event[:20].ljust(20)
        obj_id = entry.object_id[:25] if len(entry.object_id) > 25 else entry.object_id.ljust(25)

        # Actor (from source or changed_by)
        actor = entry.changed_by if entry.changed_by != "system" else entry.source

        print(f"{timestamp}  {event}  {obj_id}  {actor}")

    print("-" * 70)
    return 0
