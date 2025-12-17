"""
Audit trail and activity commands.

Commands for viewing, querying, and reporting on audit trail entries
and detecting suspicious changes.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional


def audit_log_cmd(limit: int = 20) -> int:
    """Show recent audit trail entries."""
    from vibey.operations.roadmap.audit_trail import AuditTrailManager

    manager = AuditTrailManager(Path.cwd())
    entries = manager.get_recent_changes(limit=limit)

    if not entries:
        print("No audit trail entries found.")
        return 0

    print(f"\nRecent Audit Trail Entries (last {limit})")
    print("=" * 80)

    for entry in entries:
        timestamp = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{timestamp} - {entry.object_type.upper()}: {entry.object_id}")
        print(f"  Field: {entry.field}")
        print(f"  Change: {entry.old_value} -> {entry.new_value}")
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

    manager = AuditTrailManager(Path.cwd())
    entries = manager.get_object_history(object_id)

    if not entries:
        print(f"No audit trail entries found for object '{object_id}'.")
        return 0

    print(f"\nAudit Trail for {object_id}")
    print("=" * 80)

    for entry in entries:
        timestamp = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{timestamp}")
        print(f"  Field: {entry.field}")
        print(f"  Change: {entry.old_value} -> {entry.new_value}")
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

    manager = AuditTrailManager(Path.cwd())
    suspicious = manager.detect_suspicious_changes()

    if not suspicious:
        print("\nNo suspicious changes detected in audit trail.\n")
        return 0

    print(f"\nSuspicious Changes Detected: {len(suspicious)}")
    print("=" * 80)

    for entry, reason in suspicious:
        timestamp = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"\nWarning: {reason}")
        print(f"  Object: {entry.object_type.upper()} {entry.object_id}")
        print(f"  Field: {entry.field}")
        print(f"  Change: {entry.old_value} -> {entry.new_value}")
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

    manager = AuditTrailManager(Path.cwd())

    # Parse dates if provided
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            print(f"Invalid start date format: {start_date}")
            print("   Expected format: YYYY-MM-DD")
            return 1

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            print(f"Invalid end date format: {end_date}")
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
    formatted as:
    2025-12-06 14:30  TASK_COMPLETED   task-123  claude-code
    2025-12-06 14:29  CRITERION_MET    task-123  Tests passed
    """
    from vibey.operations.roadmap.audit_trail import AuditTrailManager

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
    print(f"\nRecent Activity (last {len(entries)})")
    print("-" * 70)

    # Print entries in compact format
    for entry in entries:
        try:
            timestamp = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            timestamp = str(entry.timestamp)[:16]

        # Determine activity type from field or new_value
        if entry.field == "status":
            event = f"{entry.old_value} -> {entry.new_value}".upper()
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


def auto_progress_cmd(
    mode: str = "check",
    ticket_id: Optional[str] = None,
    enable: bool = False,
    disable: bool = False
) -> int:
    """Check or apply automatic status progressions.

    Args:
        mode: 'check' for dry-run, 'apply' to actually change status
        ticket_id: Optional specific ticket to check/apply
        enable: Enable auto-progression in config
        disable: Disable auto-progression in config

    Returns:
        Exit code (0 for success)
    """
    import yaml

    config_path = Path.cwd() / ".vibey" / "config" / "roadmap.yaml"

    # Handle enable/disable first
    if enable or disable:
        if not config_path.exists():
            print("Config file not found: .vibey/config/roadmap.yaml")
            return 1

        try:
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}

            if "auto_progression" not in config:
                config["auto_progression"] = {}

            config["auto_progression"]["enabled"] = enable

            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            status = "enabled" if enable else "disabled"
            print(f"Auto-progression {status} in .vibey/config/roadmap.yaml")
            return 0
        except Exception as e:
            print(f"Failed to update config: {e}")
            return 1

    # Import status manager
    from vibey.operations.roadmap.status_manager import (
        StatusManager,
        check_auto_progressions,
        apply_auto_progressions,
    )

    manager = StatusManager(Path.cwd())

    if not manager.is_enabled():
        print("Auto-progression is disabled.")
        print("  Enable with: vibey roadmap auto-progress --enable")
        print("  Or set auto_progression.enabled: true in .vibey/config/roadmap.yaml")
        return 0

    ticket_ids = [ticket_id] if ticket_id else None

    if mode == "check":
        print("\nChecking for eligible auto-progressions...")
        results = check_auto_progressions(Path.cwd(), ticket_ids)

        if not results:
            print("No tickets eligible for auto-progression.")
            return 0

        print(f"\n{len(results)} ticket(s) can be auto-progressed:\n")
        print("-" * 70)

        for r in results:
            print(f"  {r.ticket_type.upper()}: {r.ticket_name}")
            print(f"    ID: {r.ticket_id}")
            print(f"    {r.old_status} -> {r.new_status}")
            print(f"    Reason: {r.reason}")
            print()

        print("-" * 70)
        print("Run with --apply to execute these progressions.")
        return 0

    elif mode == "apply":
        print("\nApplying auto-progressions...")
        results = apply_auto_progressions(Path.cwd(), ticket_ids)

        if not results:
            print("No progressions applied.")
            return 0

        print(f"\n{len(results)} progression(s) applied:\n")
        print("-" * 70)

        for r in results:
            print(f"  {r.ticket_type.upper()}: {r.ticket_name}")
            print(f"    ID: {r.ticket_id}")
            print(f"    {r.old_status} -> {r.new_status}")
            print(f"    Reason: {r.reason}")
            print()

        print("-" * 70)
        return 0

    return 0
