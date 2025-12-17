# Daily Workflow with Vibey

> **Time Required:** 15 minute read, ongoing daily use
> **Difficulty:** Intermediate
> **Prerequisites:** Vibey installed, project initialized

---

## Overview

This walkthrough demonstrates the daily development workflow with Vibey. You'll learn the cycle of starting your session, working on tasks, and wrapping up.

---

## The Daily Cycle

```
┌──────────────────────────────────────────────────────────────┐
│                    DAILY WORKFLOW                            │
├────────────┬────────────┬────────────┬────────────┬─────────┤
│   Session  │    Task    │    Work    │  Progress  │ Session │
│   Start    │  Selection │  Execution │   Update   │   End   │
│   (5 min)  │  (5 min)   │ (variable) │  (2 min)   │ (5 min) │
├────────────┼────────────┼────────────┼────────────┼─────────┤
│ - status   │ - review   │ - code     │ - complete │ - commit│
│ - context  │ - blockers │ - test     │ - context  │ - plan  │
│ - review   │ - pick     │ - document │ - commits  │ - next  │
└────────────┴────────────┴────────────┴────────────┴─────────┘
```

---

## Phase 1: Session Start (5 minutes)

**Goal:** Understand current state and resume work context.

### Check Overall Status

```bash
vibey roadmap status
```

This shows:
- Total tracks, sprints, tasks
- Current progress percentages
- Items in each state (not_started, in_progress, completed)

### Review Recent Activity

```bash
vibey roadmap activity --limit 10
```

See what happened recently:
- What you completed
- What others on the team did
- Any status changes

### Check In-Progress Work

```bash
vibey roadmap status --filter in_progress
```

Shows only items currently being worked on.

---

## Phase 2: Task Selection (5 minutes)

**Goal:** Decide what to work on.

### View Available Tasks

```bash
# Show your current sprint
vibey roadmap show sprint <sprint-id>

# Or list all available tasks
vibey roadmap list tasks --status not_started
```

### Check for Blockers

```bash
vibey roadmap list-blockers
```

Shows tasks that are blocked by dependencies.

### Selection Criteria

Ask yourself:
1. **Dependencies resolved?** - Check if blocked tasks are now unblocked
2. **Priority?** - What's most urgent?
3. **Flow?** - What continues from yesterday's work?
4. **Waiting on me?** - Are others blocked on my work?

### Start the Task

```bash
vibey roadmap start <task-id>
```

This:
- Sets status to `in_progress`
- Records the start timestamp
- Updates sprint/track status

---

## Phase 3: Work Execution (variable)

**Goal:** Complete task while maintaining context.

### Reference Task Details

```bash
# View task details anytime
vibey roadmap show task <task-id>
```

Shows:
- Description and acceptance criteria
- Priority and complexity
- Related artifacts
- Dependencies

### Add Context as You Learn

```bash
# Add notes or discoveries to the task
vibey roadmap add-context <task-id> --message "Found issue with X"
```

### View Sprint Context

If your sprint has context documents:

```bash
ls .vibey/roadmap/context/sprints/<sprint-name>/
```

---

## Phase 4: Progress Update (2 minutes)

**Goal:** Record completion and any learnings.

### Complete the Task

```bash
vibey roadmap complete <task-id>
```

This:
- Sets status to `completed`
- Records completion timestamp
- Updates sprint/track progress automatically

### Add Final Context (Optional)

```bash
vibey roadmap add-context <task-id> --message "Solution: Used approach Y"
```

### Verify Status

```bash
vibey roadmap status
```

Check that progress updated correctly.

---

## Phase 5: Session End (5 minutes)

**Goal:** Clean up and prepare for next session.

### Commit Your Code

Follow your normal git workflow:

```bash
git add .
git commit -m "feat: Complete task description"
```

### View Today's Activity

```bash
vibey roadmap activity --since today
```

### Plan Tomorrow

```bash
# Check what's next
vibey roadmap list tasks --status not_started --sprint <sprint-id>
```

---

## Common Scenarios

### Switching Tasks

If you need to pause one task and work on another:

```bash
# You don't need to "pause" - just start another task
vibey roadmap start <new-task-id>

# Later, return to original task
vibey roadmap start <original-task-id>
```

### Task is Blocked

```bash
# Update task status to blocked
vibey roadmap update task <task-id> --status blocked

# Add context about what's blocking
vibey roadmap add-context <task-id> --message "Blocked on: API spec from team X"
```

### Sprint Completed

When all tasks in a sprint are done:

```bash
# Sprint status updates automatically
vibey roadmap status

# View completed sprint
vibey roadmap show sprint <sprint-id>
```

### Starting a New Sprint

```bash
# Create new sprint
vibey roadmap create-sprint \
  --track <track-id> \
  --name "Sprint 3: Feature Work"

# Create tasks for the sprint
vibey roadmap create-task --sprint <sprint-id> --title "Task 1" ...
```

---

## Command Quick Reference

### Session Start
```bash
vibey roadmap status                    # Overall status
vibey roadmap activity --limit 10       # Recent activity
vibey roadmap status --filter in_progress  # In-progress items
```

### Task Management
```bash
vibey roadmap start <task-id>           # Start working
vibey roadmap complete <task-id>        # Finish task
vibey roadmap show task <task-id>       # View details
vibey roadmap add-context <id> -m "..." # Add notes
```

### Viewing Work
```bash
vibey roadmap list tasks --sprint <id>  # Tasks in sprint
vibey roadmap list-blockers             # Blocked items
vibey roadmap show sprint <id>          # Sprint details
```

---

## Best Practices

### Start Clean
Always run `vibey roadmap status` at session start.

### One Task at a Time
Mark tasks in_progress when you're actively working on them.

### Complete Promptly
Complete tasks as soon as work is done, not at end of day.

### Add Context
Use `add-context` to record decisions and discoveries.

### Commit Often
Link git commits to task completion for traceability.

---

## MCP Integration

When using Vibey with AI assistants (Claude, Cursor, etc.):

### CLI vs MCP Tools

| Action | CLI Command | MCP Tool |
|--------|-------------|----------|
| Check status | `vibey roadmap status` | `roadmap_status` |
| Start task | `vibey roadmap start <id>` | `task_start` |
| Complete task | `vibey roadmap complete <id>` | `task_complete` |
| Query task | `vibey roadmap show <id>` | `task_query` |

The AI assistant uses MCP tools for the same operations.

---

## See Also

- [Getting Started](./GETTING_STARTED.md) - First-time setup
- [Roadmap Management](./ROADMAP_MANAGEMENT.md) - Creating tracks/sprints/tasks
- [Reporting & Status](./REPORTING_AND_STATUS.md) - Progress reports and exports
- [CLI Reference](../reference/CLI_REFERENCE.md) - All commands
