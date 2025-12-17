"""
Unified commands for planned status workflow.

These commands enable agent workflow:
1. Check track planned status
2. If not planned, get next work item
3. Do planning work
4. Approve when ready
5. Repeat until track is planned
"""

from pathlib import Path
from typing import Optional

from vibey.unified import (
    unified_command,
    param,
    ParamType,
    CommandResult,
)


@unified_command(
    name="planned_check",
    description="Check if a ticket is fully planned and ready for implementation",
    cli_group="planned",
    cli_name="check",
    mcp_name="vibey_planned_check",
    mcp_category="planning",
)
@param(
    "ticket_id",
    type=ParamType.STRING,
    required=True,
    help="ID of ticket to check",
    cli_option=False,
)
@param(
    "verbose",
    type=ParamType.BOOLEAN,
    required=False,
    default=False,
    help="Show detailed criteria status",
    cli_short="-v",
    cli_is_flag=True,
)
def planned_check(
    ticket_id: str,
    verbose: bool = False,
    root_dir: Optional[Path] = None,
) -> CommandResult:
    """
    Check planned status of a ticket.

    Returns whether ticket is planned and what criteria are unmet.
    """
    from vibey.operations.roadmap.planned_ops import check_planned

    root_dir = root_dir or Path.cwd()

    try:
        result = check_planned(root_dir, ticket_id)

        # Format output
        if result.is_planned:
            icon = "✓"
            status_msg = "fully planned"
        else:
            icon = "○"
            status_msg = "not planned"

        lines = [
            f"{icon} {result.ticket_type.title()} {ticket_id} is {status_msg}",
            f"  Progress: {result.criteria_met}/{result.criteria_total} criteria met",
        ]

        if verbose and result.unmet_criteria:
            lines.append("\n  Unmet criteria:")
            for criterion in result.unmet_criteria:
                lines.append(f"    - {criterion}")

        if result.unplanned_children:
            lines.append(f"\n  Unplanned children: {len(result.unplanned_children)}")
            if verbose:
                for child_id in result.unplanned_children[:5]:
                    lines.append(f"    - {child_id}")
                if len(result.unplanned_children) > 5:
                    lines.append(f"    ... and {len(result.unplanned_children) - 5} more")

        return CommandResult.ok(
            data={
                'ticket_id': result.ticket_id,
                'is_planned': result.is_planned,
                'criteria_total': result.criteria_total,
                'criteria_met': result.criteria_met,
                'unmet_criteria': result.unmet_criteria,
                'unplanned_children': result.unplanned_children,
            },
            message="\n".join(lines),
        )
    except FileNotFoundError as e:
        return CommandResult.fail(error=str(e))
    except Exception as e:
        return CommandResult.fail(error=f"Error checking planned status: {e}")


@unified_command(
    name="planned_approve",
    description="Manually approve a ticket's planning",
    cli_group="planned",
    cli_name="approve",
    mcp_name="vibey_planned_approve",
    mcp_category="planning",
)
@param(
    "ticket_id",
    type=ParamType.STRING,
    required=True,
    help="ID of ticket to approve",
    cli_option=False,
)
@param(
    "approver",
    type=ParamType.STRING,
    required=False,
    default=None,
    help="Name of approver",
)
@param(
    "notes",
    type=ParamType.STRING,
    required=False,
    default=None,
    help="Approval notes",
)
def planned_approve(
    ticket_id: str,
    approver: Optional[str] = None,
    notes: Optional[str] = None,
    root_dir: Optional[Path] = None,
) -> CommandResult:
    """
    Manually approve planned status for a ticket.

    Sets metadata flag indicating planning has been reviewed.
    """
    from vibey.operations.roadmap.planned_ops import approve_planned

    root_dir = root_dir or Path.cwd()

    try:
        result = approve_planned(root_dir, ticket_id, approver, notes)

        return CommandResult.ok(
            data=result,
            message=f"✓ Approved planning for {ticket_id}",
        )
    except FileNotFoundError as e:
        return CommandResult.fail(error=str(e))
    except Exception as e:
        return CommandResult.fail(error=f"Error approving: {e}")


@unified_command(
    name="planned_list_unplanned",
    description="List tickets that are not yet planned",
    cli_group="planned",
    cli_name="list-unplanned",
    mcp_name="vibey_list_unplanned",
    mcp_category="planning",
)
@param(
    "scope",
    type=ParamType.CHOICE,
    required=False,
    default="tasks",
    choices=["all", "tracks", "sprints", "tasks"],
    help="What to list",
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
    "sprint",
    type=ParamType.STRING,
    required=False,
    default=None,
    help="Filter by sprint ID",
    cli_short="-s",
)
@param(
    "limit",
    type=ParamType.INTEGER,
    required=False,
    default=20,
    help="Maximum results",
    cli_short="-n",
)
def planned_list_unplanned(
    scope: str = "tasks",
    track: Optional[str] = None,
    sprint: Optional[str] = None,
    limit: int = 20,
    root_dir: Optional[Path] = None,
) -> CommandResult:
    """
    List tickets that are not yet planned.

    Shows tickets missing required planning criteria.
    """
    from vibey.operations.roadmap.planned_ops import list_unplanned

    root_dir = root_dir or Path.cwd()

    try:
        results = list_unplanned(
            root_dir,
            scope=scope,
            track_id=track,
            sprint_id=sprint,
        )

        # Apply limit
        results = results[:limit]

        if not results:
            return CommandResult.ok(
                data=[],
                message="✓ All tickets are planned!",
            )

        lines = [f"Unplanned {scope} ({len(results)}):"]
        for item in results:
            lines.append(f"  ○ {item['id']} - {item['title']}")

        return CommandResult.ok(
            data=results,
            message="\n".join(lines),
        )
    except Exception as e:
        return CommandResult.fail(error=f"Error listing unplanned: {e}")


@unified_command(
    name="planned_next",
    description="Get next planning work item for a track",
    cli_group="planned",
    cli_name="next",
    mcp_name="vibey_planned_next",
    mcp_category="planning",
)
@param(
    "track_id",
    type=ParamType.STRING,
    required=True,
    help="Track to get next work for",
    cli_option=False,
)
def planned_next(
    track_id: str,
    root_dir: Optional[Path] = None,
) -> CommandResult:
    """
    Get the next planning work item for a track.

    Returns what needs to be done to plan the next ticket.
    """
    from vibey.operations.roadmap.planned_ops import get_next_planning_work

    root_dir = root_dir or Path.cwd()

    try:
        item = get_next_planning_work(root_dir, track_id)

        if item is None:
            return CommandResult.ok(
                data=None,
                message=f"✓ Track {track_id} is fully planned!",
            )

        lines = [
            f"Next planning work for {track_id}:",
            f"  Ticket: {item.ticket_id}",
            f"  Title: {item.ticket_title}",
            f"  Criterion: {item.criterion}",
            f"  Action: {item.action}",
            f"  Required: {'Yes' if item.required else 'No'}",
        ]

        return CommandResult.ok(
            data={
                'ticket_id': item.ticket_id,
                'ticket_type': item.ticket_type,
                'ticket_title': item.ticket_title,
                'criterion': item.criterion,
                'action': item.action,
                'required': item.required,
            },
            message="\n".join(lines),
        )
    except Exception as e:
        return CommandResult.fail(error=f"Error getting next work: {e}")


__all__ = [
    'planned_check',
    'planned_approve',
    'planned_list_unplanned',
    'planned_next',
]
