# Task 03: Implement --ticket ULID option for targeted execution

**Task ID**: `01KDC7N5Z2FQZEH01CCXKXQZ91`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: medium
**Estimated Tokens**: 5000

## Description

Add `--ticket` option accepting a ULID. Determine ticket type (track/sprint/task) and execute all child tickets until the specified ULID can be marked complete. This replaces `--track` and `--sprint` with a unified approach.

## Current Behavior

- `--track <ULID>` filters by track_id
- `--sprint <ULID>` filters by sprint_id
- Two separate options for hierarchical filtering

## Target Behavior

- Single `--ticket <ULID>` option that:
  1. Auto-detects ticket type (track, sprint, or task)
  2. Executes all child tasks within that scope
  3. Stops when target ticket can be marked complete

## Implementation Steps

### Step 1: Add ticket type detection function (implement.py)

```python
def _detect_ticket_type(ulid: str, roadmap_root: Path) -> Optional[str]:
    """
    Detect the type of ticket from its ULID.

    Args:
        ulid: The ticket ULID to check
        roadmap_root: Path to .vibey/roadmap

    Returns:
        'track', 'sprint', 'task', or None if not found
    """
    # Check tracks
    track_path = roadmap_root / "tracks" / f"{ulid}.yaml"
    if track_path.exists():
        return "track"

    # Check sprints
    sprint_path = roadmap_root / "sprints" / f"{ulid}.yaml"
    if sprint_path.exists():
        return "sprint"

    # Check tasks
    task_path = roadmap_root / "tasks" / f"{ulid}.yaml"
    if task_path.exists():
        return "task"

    return None
```

### Step 2: Add ticket resolution in implement() function

```python
def implement(ctx, all_tickets, yes, ticket, track, sprint, ...):
    # ... scope check ...

    # Resolve --ticket to track_id/sprint_id
    resolved_track = track
    resolved_sprint = sprint
    target_ticket_type = None

    if ticket:
        project_root = Path.cwd()
        roadmap_root = project_root / ".vibey" / "roadmap"

        target_ticket_type = _detect_ticket_type(ticket, roadmap_root)

        if target_ticket_type is None:
            console.print(f"[red]Error:[/red] Ticket not found: {ticket}")
            sys.exit(1)

        if target_ticket_type == "track":
            resolved_track = ticket
        elif target_ticket_type == "sprint":
            resolved_sprint = ticket
        # If task, we'll handle it in TaskSelector

    exit_code = run_implementation_cmd(
        track=resolved_track,
        sprint=resolved_sprint,
        target_ticket=ticket,           # Pass original ticket ULID
        target_ticket_type=target_ticket_type,  # Pass detected type
        max_tasks=max_tasks,
        ...
    )
```

### Step 3: Update run_implementation_cmd() (lines 273-294)

```python
def run_implementation_cmd(
    track: Optional[str] = None,
    sprint: Optional[str] = None,
    target_ticket: Optional[str] = None,      # NEW
    target_ticket_type: Optional[str] = None, # NEW
    max_tasks: Optional[int] = None,
    max_tokens: Optional[int] = None,
    dry_run: bool = False,
    background: bool = False,
) -> int:
    # ...

    # Create configuration with target ticket
    config = ImplementConfig(
        max_tasks=max_tasks,
        max_tokens=max_tokens,
        state_path=state_path,
        track_id=track,
        sprint_id=sprint,
        target_ticket=target_ticket,           # NEW
        target_ticket_type=target_ticket_type, # NEW
        auto_save=True,
    )
```

### Step 4: Update ImplementConfig (config.py)

Add new fields to `ImplementConfig`:

```python
@dataclass
class ImplementConfig:
    # ... existing fields ...

    # Target ticket scope
    target_ticket: Optional[str] = None
    target_ticket_type: Optional[str] = None  # 'track', 'sprint', 'task'
```

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/implement.py` | Add --ticket option, ticket type detection |
| `vibey/services/implementation/config.py` | Add target_ticket fields |

## Test Cases

1. `vibey implement --ticket <track-ulid>` → Executes all tasks in track
2. `vibey implement --ticket <sprint-ulid>` → Executes all tasks in sprint
3. `vibey implement --ticket <task-ulid>` → Executes just that task
4. `vibey implement --ticket <invalid-ulid>` → Error: "Ticket not found"
5. `vibey implement --ticket <track> --dry-run` → Shows tasks in track

## Acceptance Criteria

- [ ] `--ticket` option accepts any ULID (track/sprint/task)
- [ ] Ticket type auto-detected from filesystem
- [ ] Track ULID filters to all tasks in track
- [ ] Sprint ULID filters to all tasks in sprint
- [ ] Task ULID executes only that specific task
- [ ] Invalid ULID shows clear error message
