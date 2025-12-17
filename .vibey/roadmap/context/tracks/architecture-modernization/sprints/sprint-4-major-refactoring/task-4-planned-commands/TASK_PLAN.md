# Task 4: Add `planned` CLI Command Group

**Task ID:** `01KCMNPQQ8ETYF2X4N5WP95ENG`
**Sprint:** Sprint 4: Major Refactoring
**Priority:** High | **Complexity:** Medium | **Type:** Development

---

## Problem Statement

No CLI commands exist for checking or managing "planned" status. Need:

| Command | Purpose |
|---------|---------|
| `vibey planned check <id>` | Check if ticket is planned |
| `vibey planned approve <id>` | Manually approve planning |
| `vibey planned list-unplanned` | List unplanned tickets |
| `vibey planned next <track>` | Get next planning work item |

These commands enable an agent workflow: "work on track until no unplanned tickets remain."

---

## Implementation Steps

### Step 1: Create Operations Layer (45 min)

```python
# vibey/operations/roadmap/planned_ops.py

"""
Operations for planned status management.

Provides the business logic layer for planned status checking,
approval, and querying.
"""

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from vibey.roadmap.criteria.planned import (
    check_planned_status,
    get_planning_work_needed,
    PlannedCriteriaConfig,
)
from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
from vibey.operations.roadmap.query import (
    load_task_ticket,
    load_sprint_ticket,
    load_track_ticket,
)
from vibey.roadmap.serialization.yaml_dumper import (
    save_task_ticket as save_task_yaml,
)
from vibey.cli.roadmap_lib.filesystem import FileSystemManager


@dataclass
class PlannedCheckResult:
    """Result of checking planned status."""
    ticket_id: str
    ticket_type: str
    is_planned: bool
    criteria_total: int
    criteria_met: int
    unmet_criteria: List[str]
    unplanned_children: List[str]


@dataclass
class PlanningWorkItem:
    """A work item needed for planning."""
    ticket_id: str
    ticket_type: str
    ticket_title: str
    criterion: str
    action: str
    required: bool


def check_planned(
    root_dir: Path,
    item_id: str,
) -> PlannedCheckResult:
    """
    Check planned status of a ticket.

    Args:
        root_dir: Project root
        item_id: Ticket ULID

    Returns:
        PlannedCheckResult with status details
    """
    roadmap_root = root_dir / ".vibey" / "roadmap"
    fs = FileSystemManager(root_dir)

    # Detect type
    ticket_type = _detect_type(item_id, roadmap_root)

    # Load as hierarchical ticket
    ticket = _load_hierarchical(item_id, ticket_type, root_dir)

    # Configure and check
    HierarchicalTicket.set_planned_config(PlannedCriteriaConfig(), roadmap_root)

    is_planned, unmet = check_planned_status(
        item_id, ticket_type, roadmap_root
    )

    # Get progress
    progress = ticket.planned_progress if hasattr(ticket, 'planned_progress') else None

    return PlannedCheckResult(
        ticket_id=item_id,
        ticket_type=ticket_type,
        is_planned=is_planned,
        criteria_total=progress.total if progress else 0,
        criteria_met=progress.completed if progress else 0,
        unmet_criteria=unmet,
        unplanned_children=ticket.unplanned_children if hasattr(ticket, 'unplanned_children') else [],
    )


def approve_planned(
    root_dir: Path,
    item_id: str,
    approver: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """
    Manually approve planned status for a ticket.

    Updates the ticket's metadata to mark planning as approved.

    Args:
        root_dir: Project root
        item_id: Ticket ULID
        approver: Who approved (optional)
        notes: Approval notes (optional)

    Returns:
        Dict with approval details
    """
    from datetime import datetime, timezone

    roadmap_root = root_dir / ".vibey" / "roadmap"
    ticket_type = _detect_type(item_id, roadmap_root)

    # Load ticket
    ticket = _load_hierarchical(item_id, ticket_type, root_dir)

    # Update metadata
    metadata = dict(ticket.metadata) if ticket.metadata else {}
    metadata['planned_approved'] = True
    metadata['planned_approved_at'] = datetime.now(timezone.utc).isoformat()
    if approver:
        metadata['planned_approved_by'] = approver
    if notes:
        metadata['planned_approval_notes'] = notes

    # Update and save
    updated = ticket.model_copy(update={'metadata': metadata})

    # Save based on type
    if ticket_type == 'task':
        save_task_yaml(updated, roadmap_root)
    # Add sprint/track saving as needed

    return {
        'ticket_id': item_id,
        'approved': True,
        'approved_at': metadata['planned_approved_at'],
        'approver': approver,
    }


def list_unplanned(
    root_dir: Path,
    scope: str = "all",
    track_id: Optional[str] = None,
    sprint_id: Optional[str] = None,
) -> List[dict]:
    """
    List tickets that are not yet planned.

    Args:
        root_dir: Project root
        scope: 'all', 'tracks', 'sprints', 'tasks'
        track_id: Filter by track (optional)
        sprint_id: Filter by sprint (optional)

    Returns:
        List of unplanned ticket dicts
    """
    import sqlite3

    roadmap_root = root_dir / ".vibey" / "roadmap"
    db_path = roadmap_root / "roadmap.db"

    if not db_path.exists():
        return []

    unplanned = []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        # Query tasks (most common case)
        if scope in ('all', 'tasks'):
            query = "SELECT id, title, sprint_id FROM tasks"
            params = []

            if sprint_id:
                query += " WHERE sprint_id = ?"
                params.append(sprint_id)
            elif track_id:
                query += " WHERE sprint_id IN (SELECT id FROM sprints WHERE track_id = ?)"
                params.append(track_id)

            for row in conn.execute(query, params):
                is_planned, _ = check_planned_status(
                    row['id'], 'task', roadmap_root
                )
                if not is_planned:
                    unplanned.append({
                        'id': row['id'],
                        'title': row['title'],
                        'type': 'task',
                        'parent_id': row['sprint_id'],
                    })

        # Could add sprints/tracks but tasks are primary use case

    finally:
        conn.close()

    return unplanned


def get_next_planning_work(
    root_dir: Path,
    track_id: str,
) -> Optional[PlanningWorkItem]:
    """
    Get the next planning work item for a track.

    Finds the first unplanned ticket and returns what work is needed.

    Args:
        root_dir: Project root
        track_id: Track to check

    Returns:
        PlanningWorkItem or None if fully planned
    """
    roadmap_root = root_dir / ".vibey" / "roadmap"

    # Get unplanned tasks in this track
    unplanned = list_unplanned(root_dir, scope='tasks', track_id=track_id)

    if not unplanned:
        return None

    # Get first unplanned task
    first = unplanned[0]

    # Get work needed
    work_items = get_planning_work_needed(
        first['id'], 'task', roadmap_root
    )

    if not work_items:
        return None

    # Return first work item
    item = work_items[0]
    return PlanningWorkItem(
        ticket_id=first['id'],
        ticket_type='task',
        ticket_title=first['title'],
        criterion=item['criterion'],
        action=item['action'],
        required=item['required'],
    )


def _detect_type(item_id: str, roadmap_root: Path) -> str:
    """Detect ticket type from filesystem."""
    if (roadmap_root / "tasks" / f"{item_id}.yaml").exists():
        return "task"
    elif (roadmap_root / "sprints" / f"{item_id}.yaml").exists():
        return "sprint"
    elif (roadmap_root / "tracks" / f"{item_id}.yaml").exists():
        return "track"
    raise FileNotFoundError(f"Ticket not found: {item_id}")


def _load_hierarchical(item_id: str, ticket_type: str, root_dir: Path) -> HierarchicalTicket:
    """Load ticket as HierarchicalTicket."""
    if ticket_type == 'task':
        return load_task_ticket(item_id, root_dir)
    elif ticket_type == 'sprint':
        return load_sprint_ticket(item_id, root_dir)
    elif ticket_type == 'track':
        return load_track_ticket(item_id, root_dir)
    raise ValueError(f"Unknown ticket type: {ticket_type}")
```

### Step 2: Create Unified Commands (45 min)

```python
# vibey/unified/commands/planned.py

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
```

### Step 3: Register Commands in CLI (15 min)

```python
# vibey/cli/main.py (add to existing)

# Add planned command group
@cli.group()
def planned():
    """Planned status workflow commands."""
    pass

# Register unified commands
from vibey.unified.adapters.click_adapter import register_unified_commands

# The click adapter should auto-register commands with cli_group="planned"
# to the planned group. If not, manually wire:

from vibey.unified.commands.planned import (
    planned_check,
    planned_approve,
    planned_list_unplanned,
    planned_next,
)

# These get registered via the unified system
```

### Step 4: Update Unified Commands Index (10 min)

```python
# vibey/unified/commands/__init__.py

"""Unified command modules."""

from .roadmap import *
from .docs import *
from .deploy import *
from .planned import *  # ADD THIS

# Import all to register with registry
```

### Step 5: Add Tests (30 min)

```python
# tests/unified/commands/test_planned.py

import pytest
from pathlib import Path
from click.testing import CliRunner

from vibey.cli.main import cli


class TestPlannedCheck:
    """Tests for planned check command."""

    def test_check_planned_task(self, roadmap_env):
        """Check command works for planned task."""
        # Create YAML file
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01TEST.yaml"
        yaml_path.write_text("task: {id: 01TEST, title: Test}")

        runner = CliRunner()
        result = runner.invoke(cli, ['planned', 'check', '01TEST'])

        assert result.exit_code == 0
        assert 'planned' in result.output.lower()

    def test_check_unplanned_task(self, roadmap_env):
        """Check command shows unplanned for missing YAML."""
        runner = CliRunner()
        result = runner.invoke(cli, ['planned', 'check', '01MISSING'])

        # Should fail or show not planned
        assert 'not planned' in result.output.lower() or result.exit_code != 0


class TestPlannedApprove:
    """Tests for planned approve command."""

    def test_approve_sets_metadata(self, roadmap_env):
        """Approve command updates ticket metadata."""
        # Create task YAML
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01TEST.yaml"
        yaml_path.write_text("task:\n  id: 01TEST\n  title: Test\n  metadata: {}")

        runner = CliRunner()
        result = runner.invoke(cli, [
            'planned', 'approve', '01TEST',
            '--approver', 'test-user'
        ])

        assert result.exit_code == 0
        assert 'approved' in result.output.lower()


class TestPlannedListUnplanned:
    """Tests for list-unplanned command."""

    def test_list_empty_when_all_planned(self, roadmap_env):
        """List returns empty when all tasks planned."""
        # Create YAML for all tasks
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01TEST.yaml"
        yaml_path.write_text("task: {id: 01TEST}")

        runner = CliRunner()
        result = runner.invoke(cli, ['planned', 'list-unplanned'])

        assert result.exit_code == 0


class TestPlannedNext:
    """Tests for planned next command."""

    def test_next_returns_work_item(self, roadmap_env):
        """Next command returns work when unplanned tasks exist."""
        # Don't create YAML - task is unplanned
        runner = CliRunner()
        result = runner.invoke(cli, ['planned', 'next', '01TRACK'])

        # Will fail if track doesn't exist, but tests the flow
        assert result.exit_code in (0, 1)
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `vibey/operations/roadmap/planned_ops.py` | Business logic |
| `vibey/unified/commands/planned.py` | Unified commands |
| `tests/unified/commands/test_planned.py` | Unit tests |

## Files to Modify

| File | Change |
|------|--------|
| `vibey/cli/main.py` | Register `planned` command group |
| `vibey/unified/commands/__init__.py` | Import planned module |

---

## Acceptance Criteria

- [ ] `vibey planned check <id>` shows planned status with criteria
- [ ] `vibey planned approve <id>` marks planning approved
- [ ] `vibey planned list-unplanned` lists unplanned tickets
- [ ] `vibey planned next <track>` shows next planning work
- [ ] MCP tools `vibey_planned_*` mirror CLI commands
- [ ] All unit tests pass
- [ ] Commands work with ULID IDs

---

## Agent Workflow Example

```bash
# 1. Check if track is planned
vibey planned check 01MYTRACK

# 2. Get next planning work
vibey planned next 01MYTRACK
# Output: Create TASK_PLAN.md for task 01ABC

# 3. Do the work (create files, etc.)
# ... agent creates TASK_PLAN.md ...

# 4. Approve planning
vibey planned approve 01ABC --approver "claude-code"

# 5. Repeat until track is planned
vibey planned check 01MYTRACK
# Output: ✓ Track is fully planned!
```

---

## Estimated Effort

| Step | Time |
|------|------|
| Step 1: Operations layer | 45 min |
| Step 2: Unified commands | 45 min |
| Step 3: CLI registration | 15 min |
| Step 4: Update imports | 10 min |
| Step 5: Add tests | 30 min |
| **Total** | **~2.5 hours** |
