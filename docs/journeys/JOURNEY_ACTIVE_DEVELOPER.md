# Active Developer Journey

> Daily productivity with Vibey-managed tasks

**Persona:** Alex the Active Developer
**Duration:** 1-2 hours daily

---

## Journey Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ACTIVE DEVELOPER JOURNEY                              │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┤
│ Session     │ Task        │ Work        │ Progress    │ Session             │
│ Start       │ Selection   │ Execution   │ Update      │ End                 │
│ (5 min)     │ (5 min)     │ (variable)  │ (2 min)     │ (5 min)             │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ - Check     │ - Review    │ - Code      │ - Mark      │ - Checkpoint        │
│   status    │   blockers  │ - Test      │   complete  │ - Add context       │
│ - Review    │ - Pick      │ - Document  │ - Add       │ - Plan next         │
│   context   │   task      │ - Commit    │   commits   │                     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────────┘
```

---

## Daily Workflow Cycle

### Phase 1: Session Start (5 minutes)

**Goal:** Understand current state and resume work context

```bash
# Get overall status
vibey roadmap status

# See what's in progress
vibey roadmap status --filter in_progress

# Review recent activity
vibey roadmap activity --limit 10

# Load context for current work
vibey roadmap context
```

### Phase 2: Task Selection (5 minutes)

**Goal:** Decide what to work on next

```bash
# See available tasks
vibey roadmap show sprint <current-sprint>

# Check blockers
vibey roadmap list-blockers

# Start the chosen task
vibey roadmap start <task-id>
```

**Selection Criteria:**
1. Any blockers resolved?
2. What's most urgent?
3. What flows from yesterday's work?
4. Any dependencies waiting on me?

### Phase 3: Work Execution (variable)

**Goal:** Complete task work while maintaining context

```bash
# Reference task details during work
vibey roadmap show task <task-id>

# Add context as you learn
vibey roadmap add-context <task-id> --message "Found issue with..."

# View related context files
cat .vibey/roadmap/context/sprints/<sprint>/...
```

**During Coding:**
- Keep terminal with `vibey roadmap status` visible
- Reference task description for scope
- Add context notes for complex discoveries

### Phase 4: Progress Update (2 minutes)

**Goal:** Record completion and link work

```bash
# Complete the task
vibey roadmap complete <task-id>

# Link commits (if not using hooks)
vibey roadmap add-commit <task-id> <commit-sha>

# Update progress
vibey roadmap auto-progress --check
```

### Phase 5: Session End (5 minutes)

**Goal:** Prepare for next session

```bash
# Checkpoint current progress
vibey roadmap checkpoint

# Review what was accomplished
vibey roadmap activity --today

# Check remaining work
vibey roadmap status
```

---

## Common Scenarios

### Scenario 1: Picking Up Where You Left Off

```bash
# Start of day
vibey roadmap status
# Shows: "1 task in_progress: 01KC2D..."

vibey roadmap show task 01KC2D...
# Shows: Task details and last context

vibey roadmap activity --limit 5
# Shows: Recent commits and actions

# Continue working...
```

### Scenario 2: Blocked Task

```bash
# Hit a blocker during work
vibey roadmap add-context <task-id> --message "Blocked: Waiting on API docs"

# Mark task as blocked
vibey roadmap update task <task-id> --blocked true --blocked-by "Waiting for API documentation"

# Switch to different task
vibey roadmap start <other-task-id>
```

### Scenario 3: Multi-Task Day

```bash
# Complete first task
vibey roadmap complete <task-1-id>

# Start second task
vibey roadmap start <task-2-id>

# Context switch - save notes
vibey roadmap add-context <task-2-id> --message "Pausing to review PR"

# End of day
vibey roadmap checkpoint
vibey roadmap status
```

### Scenario 4: Quick Bug Fix

```bash
# Urgent bug comes in
vibey roadmap create-task --sprint <current> --title "Fix critical bug #123" --priority high

# Start immediately
vibey roadmap start <new-task-id>

# Fix and complete
vibey roadmap complete <new-task-id>

# Resume planned work
vibey roadmap start <original-task-id>
```

---

## Command Reference

### Session Management

| Command | Purpose |
|---------|---------|
| `vibey roadmap status` | Overview of all work |
| `vibey roadmap status --filter in_progress` | What's being worked on |
| `vibey roadmap activity` | Recent activity log |
| `vibey roadmap context` | Current working context |
| `vibey roadmap checkpoint` | Save session state |

### Task Operations

| Command | Purpose |
|---------|---------|
| `vibey roadmap start <id>` | Begin working on task |
| `vibey roadmap complete <id>` | Mark task done |
| `vibey roadmap show task <id>` | View task details |
| `vibey roadmap add-context <id>` | Add context/notes |
| `vibey roadmap add-commit <id> <sha>` | Link commit to task |

### Progress Tracking

| Command | Purpose |
|---------|---------|
| `vibey roadmap auto-progress` | Auto-update counters |
| `vibey roadmap list-blockers` | See blocked items |
| `vibey roadmap update task <id>` | Modify task properties |

---

## Best Practices

### Time Boxing

| Activity | Recommended Time |
|----------|------------------|
| Session start review | 5 minutes |
| Task selection | 5 minutes |
| Status update | 2-3 minutes per task |
| Session end checkpoint | 5 minutes |

### Context Hygiene

1. **Add context while fresh** - Don't wait until end of day
2. **Link commits immediately** - Use git hooks or manual linking
3. **Note blockers promptly** - Helps others understand delays
4. **Review context before diving in** - 2 minutes saves 20

### Task Flow

1. **One task at a time** - `in_progress` should usually be 1
2. **Complete before switching** - Or explicitly mark blocked
3. **Small, completable tasks** - Break big work into pieces
4. **Daily completion** - Aim for at least one task/day

---

## Integration with Git

### Pre-Commit Hook

```bash
# Install hooks
vibey git hooks install

# Now commits auto-validate task state
git commit -m "feat(task-001): Add feature

Task: 01KC2D0JK7READW9KAK1HBX4A5"
```

### Commit Message Format

```
type(scope): description

Task: <task-id>

[optional body]
```

---

## Metrics to Track

| Metric | How to Check | Goal |
|--------|--------------|------|
| Tasks completed/day | `activity --today` | 1-3 |
| Time to complete | Task timestamps | Matches estimates |
| Context added | Context files | Every task |
| Blocked time | Blocker duration | Minimize |

---

## Documentation Touchpoints

| Activity | Documents |
|----------|-----------|
| Quick command lookup | CLI_REFERENCE.md |
| Understanding status | ROADMAP_SYSTEM.md |
| Git integration | GIT_HOOKS_GUIDE.md |
| Context management | (Context docs) |

---

## Hands-On Tutorial

Practice the daily workflow with a step-by-step walkthrough:

**📚 [Active Developer Walkthrough: Daily Workflow with Vibey](../walkthroughs/WALKTHROUGH_ACTIVE_DEVELOPER.md)**

This walkthrough covers:
- Session start routines
- Task selection and execution
- Handling blockers
- End-of-day practices
