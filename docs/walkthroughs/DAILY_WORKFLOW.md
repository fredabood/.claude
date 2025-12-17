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
vibey roadmap db query progress --by status
```

Shows progress breakdown by status (not_started, in_progress, completed).

---

## Phase 2: Task Selection (5 minutes)

**Goal:** Decide what to work on.

### View Available Tasks

```bash
# Show your current sprint with its tasks
vibey roadmap show <sprint-id>

# Or view overall status to find sprints
vibey roadmap status
```

### Check for Blockers

Review the sprint to identify tasks with dependencies:

```bash
vibey roadmap show <sprint-id>
```

Tasks with unfinished dependencies will show as blocked.

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
vibey roadmap show <task-id>
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

> **How Progress Works:** When you complete a task, Vibey automatically recomputes sprint and
> track progress. Completion percentages are calculated as `completed_tasks / total_tasks × 100`.
> Sprint status flows through: `not_started` → `in_progress` → `completion_gate_check` →
> `production_ready` → `deployed`. See [Architecture Overview](../architecture/ARCHITECTURE_OVERVIEW.md)
> for the full status flow diagram.

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
# Add context about what's blocking
vibey roadmap add-context <task-id> --message "Blocked on: API spec from team X"
```

Note: Use `vibey roadmap show <task-id>` to check current status.

### Sprint Completed

When all tasks in a sprint are done:

```bash
# Sprint status updates automatically
vibey roadmap status

# View completed sprint
vibey roadmap show <sprint-id>
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
vibey roadmap db query progress --by status  # Progress by status
```

### Task Management
```bash
vibey roadmap start <task-id>           # Start working
vibey roadmap complete <task-id>        # Finish task
vibey roadmap show <task-id>            # View details
vibey roadmap add-context <id> -m "..." # Add notes
```

### Viewing Work
```bash
vibey roadmap status                    # All items
vibey roadmap show <sprint-id>          # Sprint with tasks
vibey roadmap show <task-id>            # Task details
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

## Git Integration

Vibey integrates with git to track commits and branches:

### Link Commits to Tasks

```bash
vibey git link-commit --task <task-id> --commit <commit-sha>
```

### View Git History for Roadmap

```bash
vibey git history
```

### Check Git Progress

```bash
vibey git progress
```

### Analyze Git State

```bash
vibey git analyze
```

### Branch Management

```bash
# Create branch linked to task
vibey git branch create --task <task-id> --name "feature/task-name"

# List linked branches
vibey git branch list

# Check branch status
vibey git branch status
```

### Sync Git and Roadmap

```bash
vibey git sync
```

Synchronizes git state with roadmap records.

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
| List blockers | `vibey roadmap db query blocked` | `vibey_list_blockers` |
| Refresh progress | - | `vibey_refresh_progress` |

The AI assistant uses MCP tools for the same operations.

### MCP Workflow Tools

AI assistants can use workflow handoff tools for task transitions:

| Tool | Purpose |
|------|---------|
| `vibey_handoff_initial_analysis` | Begin task analysis |
| `vibey_handoff_planning_complete` | Planning phase done |
| `vibey_handoff_implementation_complete` | Code complete |
| `vibey_handoff_code_review` | Request code review |
| `vibey_handoff_testing_complete` | Testing done |
| `vibey_handoff_ai_to_human` | Escalate to human |

---

## See Also

- [Getting Started](./GETTING_STARTED.md) - First-time setup
- [Roadmap Management](./ROADMAP_MANAGEMENT.md) - Creating tracks/sprints/tasks
- [Reporting & Status](./REPORTING_AND_STATUS.md) - Progress reports and exports
- [CLI Reference](../reference/CLI_REFERENCE.md) - All commands
