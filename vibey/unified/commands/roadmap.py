"""
Unified roadmap commands.

These commands are available in both CLI and MCP interfaces via the
@unified_command decorator. They call the existing operations layer.

Migration Note: This file demonstrates the migration pattern. As commands
are migrated, they should be added here and the old CLI/MCP implementations
should be deprecated.
"""

from pathlib import Path
from typing import Optional, TYPE_CHECKING

from vibey.unified import (
    unified_command,
    param,
    ParamType,
    CommandResult,
)

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket import HierarchicalTicket


def format_criteria_status(ticket: "HierarchicalTicket") -> str:
    """
    Format criteria status for CLI output.

    Displays criteria grouped by which transition they block.
    """
    from vibey.roadmap.models.ticket.enums import TicketStatus

    lines = []

    # Group by transition target
    for target_status in [TicketStatus.IN_PROGRESS, TicketStatus.COMPLETED]:
        criteria = ticket.criteria_for_transition(target_status)
        if not criteria:
            continue

        status_label = target_status.value.upper().replace('_', ' ')
        lines.append(f"\nCriteria for {status_label}:")
        for c in criteria:
            icon = "✓" if c.is_met else "○"
            req = "" if c.required else " (optional)"
            lines.append(f"  {icon} {c.description}{req}")

    if not lines:
        lines.append("\n(No criteria defined)")

    return "\n".join(lines)


@unified_command(
    name="roadmap_status",
    description="Show roadmap status - tracks, sprints, and overall progress",
    cli_group="roadmap",
    cli_name="status",
    mcp_name="vibey_roadmap_status",
    mcp_category="roadmap",
)
@param(
    "track",
    type=ParamType.STRING,
    required=False,
    default=None,
    help="Show status for specific track only",
)
@param(
    "sprint",
    type=ParamType.STRING,
    required=False,
    default=None,
    help="Show status for specific sprint only",
)
def roadmap_status(
    track: Optional[str] = None,
    sprint: Optional[str] = None,
    root_dir: Optional[Path] = None,
) -> CommandResult:
    """
    Show roadmap status.

    Returns summary of all tracks, or details for a specific track/sprint.
    """
    from vibey.operations.roadmap.query import (
        query_roadmap_summary,
        query_track_details,
        query_sprint_details,
    )
    from vibey.cli.roadmap_lib.formatting import (
        format_roadmap_summary,
        format_track_details,
        format_sprint_details,
    )

    root_dir = root_dir or Path.cwd()

    try:
        if sprint:
            result = query_sprint_details(root_dir, sprint)
            formatted = format_sprint_details(result)
            return CommandResult.ok(data=result, message=formatted)
        elif track:
            result = query_track_details(root_dir, track)
            formatted = format_track_details(result)
            return CommandResult.ok(data=result, message=formatted)
        else:
            result = query_roadmap_summary(root_dir)
            formatted = format_roadmap_summary(result)
            return CommandResult.ok(data=result, message=formatted)
    except Exception as e:
        return CommandResult.fail(error=str(e))


@unified_command(
    name="roadmap_show",
    description="Show details for a specific track, sprint, or task",
    cli_group="roadmap",
    cli_name="show",
    mcp_name="vibey_roadmap_show",
    mcp_category="roadmap",
)
@param(
    "item_id",
    type=ParamType.STRING,
    required=True,
    help="ID of track, sprint, or task to show",
    cli_option=False,  # Positional argument in CLI
)
@param(
    "format",
    type=ParamType.CHOICE,
    required=False,
    default="text",
    choices=["text", "yaml", "json"],
    help="Output format",
    cli_short="-f",
)
def roadmap_show(
    item_id: str,
    format: str = "text",
    root_dir: Optional[Path] = None,
) -> CommandResult:
    """
    Show details for a roadmap item.

    Auto-detects item type (track, sprint, or task) based on ID format.
    """
    from vibey.operations.roadmap.query import (
        query_track_details,
        query_sprint_details,
        query_task_details,
    )
    from vibey.cli.roadmap_lib.formatting import (
        format_track_details,
        format_sprint_details,
        format_task_details,
    )

    root_dir = root_dir or Path.cwd()

    try:
        # Try to detect item type and query appropriate details
        # ULIDs are 26 chars, check track/sprint/task files
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager
        fs = FileSystemManager(root_dir)

        # Check if it's a track
        track_path = fs.get_track_path(item_id)
        if track_path.exists():
            result = query_track_details(root_dir, item_id)
            if format == "yaml":
                import yaml
                return CommandResult.ok(data=result, message=yaml.dump(result, default_flow_style=False))
            elif format == "json":
                import json
                return CommandResult.ok(data=result, message=json.dumps(result, indent=2, default=str))
            else:
                formatted = format_track_details(result)
                return CommandResult.ok(data=result, message=formatted)

        # Check if it's a sprint
        sprint_path = fs.get_sprint_path(item_id)
        if sprint_path.exists():
            result = query_sprint_details(root_dir, item_id)
            if format == "yaml":
                import yaml
                return CommandResult.ok(data=result, message=yaml.dump(result, default_flow_style=False))
            elif format == "json":
                import json
                return CommandResult.ok(data=result, message=json.dumps(result, indent=2, default=str))
            else:
                formatted = format_sprint_details(result)
                return CommandResult.ok(data=result, message=formatted)

        # Check if it's a task
        task_path = fs.get_task_path(item_id)
        if task_path.exists():
            result = query_task_details(root_dir, item_id)
            if format == "yaml":
                import yaml
                return CommandResult.ok(data=result, message=yaml.dump(result, default_flow_style=False))
            elif format == "json":
                import json
                return CommandResult.ok(data=result, message=json.dumps(result, indent=2, default=str))
            else:
                formatted = format_task_details(result)
                # Add criteria status for text format
                try:
                    from vibey.operations.roadmap.query import load_task_ticket
                    ticket = load_task_ticket(root_dir, item_id)
                    criteria_text = format_criteria_status(ticket)
                    formatted += criteria_text
                except Exception:
                    # If ticket loading fails, continue without criteria
                    pass
                return CommandResult.ok(data=result, message=formatted)

        return CommandResult.fail(error=f"Item not found: {item_id}")

    except Exception as e:
        return CommandResult.fail(error=str(e))


@unified_command(
    name="roadmap_start",
    description="Start a task or sprint - mark as in_progress with timestamp",
    cli_group="roadmap",
    cli_name="start",
    mcp_name="vibey_start_task",
    mcp_category="task",
)
@param(
    "item_id",
    type=ParamType.STRING,
    required=True,
    help="ID of task or sprint to start",
    cli_option=False,
)
@param(
    "force",
    type=ParamType.BOOLEAN,
    required=False,
    default=False,
    help="Force start even if blocked by dependencies",
    cli_short="-f",
    cli_is_flag=True,
)
def roadmap_start(
    item_id: str,
    force: bool = False,
    root_dir: Optional[Path] = None,
) -> CommandResult:
    """
    Start a task or sprint.

    Sets status to 'in_progress' and records start timestamp.
    Uses criteria-based validation via the unified ticket architecture.
    """
    from vibey.operations.roadmap.transitions import start_item, TransitionBlockedError

    root_dir = root_dir or Path.cwd()

    try:
        result = start_item(root_dir, item_id, force=force)
        return CommandResult.ok(
            data=result,
            message=f"Started {result.get('type', 'item')} '{item_id}'. Status: {result.get('status', 'in_progress')}"
        )
    except TransitionBlockedError as e:
        # Return structured error with blocking reasons
        return CommandResult.fail(
            error=f"Cannot start {item_id}: {'; '.join(e.reasons)}"
        )
    except FileNotFoundError as e:
        return CommandResult.fail(error=str(e))
    except Exception as e:
        return CommandResult.fail(error=f"Unexpected error: {str(e)}")


@unified_command(
    name="roadmap_complete",
    description="Complete a task or sprint - mark as completed with timestamp",
    cli_group="roadmap",
    cli_name="complete",
    mcp_name="vibey_complete_task",
    mcp_category="task",
)
@param(
    "item_id",
    type=ParamType.STRING,
    required=True,
    help="ID of task or sprint to complete",
    cli_option=False,
)
@param(
    "notes",
    type=ParamType.STRING,
    required=False,
    default=None,
    help="Completion notes or summary",
)
def roadmap_complete(
    item_id: str,
    notes: Optional[str] = None,
    root_dir: Optional[Path] = None,
) -> CommandResult:
    """
    Complete a task or sprint.

    Sets status to 'completed' and records completion timestamp.
    Uses criteria-based validation via the unified ticket architecture.
    """
    from vibey.operations.roadmap.transitions import complete_item, TransitionBlockedError

    root_dir = root_dir or Path.cwd()

    try:
        result = complete_item(root_dir, item_id, notes=notes)
        return CommandResult.ok(
            data=result,
            message=f"Completed {result.get('type', 'item')} '{item_id}'. Status: {result.get('status', 'completed')}"
        )
    except TransitionBlockedError as e:
        # Return structured error with blocking reasons
        return CommandResult.fail(
            error=f"Cannot complete {item_id}: {'; '.join(e.reasons)}"
        )
    except FileNotFoundError as e:
        return CommandResult.fail(error=str(e))
    except Exception as e:
        return CommandResult.fail(error=f"Unexpected error: {str(e)}")


# =============================================================================
# List Commands
# =============================================================================

@unified_command(
    name="roadmap_list_tracks",
    description="List all tracks in the roadmap",
    cli_group="roadmap",
    cli_name="list-tracks",
    mcp_name="vibey_list_tracks",
    mcp_category="roadmap",
)
@param(
    "status",
    type=ParamType.CHOICE,
    required=False,
    default=None,
    choices=["pending", "in_progress", "completed", "blocked"],
    help="Filter by status",
    cli_short="-s",
)
@param(
    "format",
    type=ParamType.CHOICE,
    required=False,
    default="table",
    choices=["table", "json", "yaml"],
    help="Output format",
    cli_short="-f",
)
def roadmap_list_tracks(
    status: Optional[str] = None,
    format: str = "table",
    root_dir: Optional[Path] = None,
) -> CommandResult:
    """List all tracks in the roadmap."""
    from vibey.operations.roadmap.query import query_tracks

    root_dir = root_dir or Path.cwd()

    try:
        tracks = query_tracks(root_dir, status=status)

        if format == "json":
            import json
            return CommandResult.ok(data=tracks, message=json.dumps(tracks, indent=2, default=str))
        elif format == "yaml":
            import yaml
            return CommandResult.ok(data=tracks, message=yaml.dump(tracks, default_flow_style=False))
        else:
            # Table format
            lines = ["Tracks:", "=" * 60]
            for t in tracks:
                status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "blocked": "🚫"}.get(t.get("status", ""), "")
                lines.append(f"  {status_icon} {t.get('id', '')} - {t.get('name', 'Unknown')}")
                lines.append(f"     Status: {t.get('status', 'unknown')} | Sprints: {t.get('sprint_count', 0)}")
            return CommandResult.ok(data=tracks, message="\n".join(lines))
    except Exception as e:
        return CommandResult.fail(error=str(e))


@unified_command(
    name="roadmap_list_sprints",
    description="List sprints, optionally filtered by track",
    cli_group="roadmap",
    cli_name="list-sprints",
    mcp_name="vibey_list_sprints",
    mcp_category="roadmap",
)
@param(
    "track",
    type=ParamType.STRING,
    required=False,
    default=None,
    help="Filter by track ID",
    cli_short="-t",
)
@param(
    "status",
    type=ParamType.CHOICE,
    required=False,
    default=None,
    choices=["pending", "in_progress", "completed", "blocked"],
    help="Filter by status",
    cli_short="-s",
)
@param(
    "format",
    type=ParamType.CHOICE,
    required=False,
    default="table",
    choices=["table", "json", "yaml"],
    help="Output format",
    cli_short="-f",
)
def roadmap_list_sprints(
    track: Optional[str] = None,
    status: Optional[str] = None,
    format: str = "table",
    root_dir: Optional[Path] = None,
) -> CommandResult:
    """List sprints in the roadmap."""
    from vibey.operations.roadmap.query import query_sprints

    root_dir = root_dir or Path.cwd()

    try:
        sprints = query_sprints(root_dir, track_id=track, status=status)

        if format == "json":
            import json
            return CommandResult.ok(data=sprints, message=json.dumps(sprints, indent=2, default=str))
        elif format == "yaml":
            import yaml
            return CommandResult.ok(data=sprints, message=yaml.dump(sprints, default_flow_style=False))
        else:
            lines = ["Sprints:", "=" * 60]
            for s in sprints:
                status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "blocked": "🚫"}.get(s.get("status", ""), "")
                lines.append(f"  {status_icon} {s.get('id', '')} - {s.get('name', 'Unknown')}")
                lines.append(f"     Status: {s.get('status', 'unknown')} | Tasks: {s.get('task_count', 0)}")
            return CommandResult.ok(data=sprints, message="\n".join(lines))
    except Exception as e:
        return CommandResult.fail(error=str(e))


@unified_command(
    name="roadmap_list_tasks",
    description="List tasks, optionally filtered by sprint",
    cli_group="roadmap",
    cli_name="list-tasks",
    mcp_name="vibey_list_tasks",
    mcp_category="task",
)
@param(
    "sprint",
    type=ParamType.STRING,
    required=False,
    default=None,
    help="Filter by sprint ID",
    cli_short="-s",
)
@param(
    "status",
    type=ParamType.CHOICE,
    required=False,
    default=None,
    choices=["pending", "in_progress", "completed", "blocked"],
    help="Filter by status",
)
@param(
    "format",
    type=ParamType.CHOICE,
    required=False,
    default="table",
    choices=["table", "json", "yaml"],
    help="Output format",
    cli_short="-f",
)
def roadmap_list_tasks(
    sprint: Optional[str] = None,
    status: Optional[str] = None,
    format: str = "table",
    root_dir: Optional[Path] = None,
) -> CommandResult:
    """List tasks in the roadmap."""
    from vibey.operations.roadmap.query import query_tasks

    root_dir = root_dir or Path.cwd()

    try:
        tasks = query_tasks(root_dir, sprint_id=sprint, status=status)

        if format == "json":
            import json
            return CommandResult.ok(data=tasks, message=json.dumps(tasks, indent=2, default=str))
        elif format == "yaml":
            import yaml
            return CommandResult.ok(data=tasks, message=yaml.dump(tasks, default_flow_style=False))
        else:
            lines = ["Tasks:", "=" * 60]
            for t in tasks:
                status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "blocked": "🚫"}.get(t.get("status", ""), "")
                lines.append(f"  {status_icon} {t.get('id', '')} - {t.get('title', 'Unknown')}")
                lines.append(f"     Status: {t.get('status', 'unknown')}")
            return CommandResult.ok(data=tasks, message="\n".join(lines))
    except Exception as e:
        return CommandResult.fail(error=str(e))


# =============================================================================
# Database Commands
# =============================================================================

@unified_command(
    name="roadmap_db_status",
    description="Show database sync status",
    cli_group="roadmap",
    cli_name="db-status",
    mcp_name="vibey_db_status",
    mcp_category="database",
)
def roadmap_db_status(root_dir: Optional[Path] = None) -> CommandResult:
    """Show database sync status."""
    from vibey.operations.roadmap.db_operations import get_db_status

    root_dir = root_dir or Path.cwd()

    try:
        status = get_db_status(root_dir)
        lines = [
            "Database Status:",
            "=" * 40,
            f"  Database exists: {status.get('exists', False)}",
            f"  Last sync: {status.get('last_sync', 'Never')}",
            f"  Tracks: {status.get('track_count', 0)}",
            f"  Sprints: {status.get('sprint_count', 0)}",
            f"  Tasks: {status.get('task_count', 0)}",
            f"  Sync needed: {status.get('sync_needed', 'Unknown')}",
        ]
        return CommandResult.ok(data=status, message="\n".join(lines))
    except Exception as e:
        return CommandResult.fail(error=str(e))


@unified_command(
    name="roadmap_db_rebuild",
    description="Rebuild database from YAML files",
    cli_group="roadmap",
    cli_name="db-rebuild",
    mcp_name="vibey_db_rebuild",
    mcp_category="database",
)
@param(
    "force",
    type=ParamType.BOOLEAN,
    required=False,
    default=False,
    help="Force rebuild even if database is current",
    cli_short="-f",
    cli_is_flag=True,
)
def roadmap_db_rebuild(
    force: bool = False,
    root_dir: Optional[Path] = None,
) -> CommandResult:
    """Rebuild database from YAML files."""
    from vibey.operations.roadmap.db_operations import rebuild_database

    root_dir = root_dir or Path.cwd()

    try:
        result = rebuild_database(root_dir, force=force)
        return CommandResult.ok(
            data=result,
            message=f"Database rebuilt: {result.get('track_count', 0)} tracks, {result.get('sprint_count', 0)} sprints, {result.get('task_count', 0)} tasks"
        )
    except Exception as e:
        return CommandResult.fail(error=str(e))


@unified_command(
    name="roadmap_db_validate",
    description="Validate database integrity",
    cli_group="roadmap",
    cli_name="db-validate",
    mcp_name="vibey_db_validate",
    mcp_category="database",
)
def roadmap_db_validate(root_dir: Optional[Path] = None) -> CommandResult:
    """Validate database integrity."""
    from vibey.operations.roadmap.db_operations import validate_database

    root_dir = root_dir or Path.cwd()

    try:
        result = validate_database(root_dir)
        if result.get("valid", False):
            return CommandResult.ok(
                data=result,
                message=f"Database valid: {result.get('check_count', 0)} checks passed"
            )
        else:
            errors = result.get("errors", [])
            return CommandResult.fail(
                error=f"Database invalid: {len(errors)} errors found\n" + "\n".join(f"  - {e}" for e in errors[:5])
            )
    except Exception as e:
        return CommandResult.fail(error=str(e))
