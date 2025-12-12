# Active Developer Walkthrough: Daily Workflow with Vibey

> **Time Required:** 20 minutes
> **Difficulty:** Intermediate
> **Prerequisites:** Vibey installed, project initialized

## Overview

This walkthrough demonstrates a typical daily development workflow using Vibey. You'll learn how to start your day, manage tasks efficiently, track progress, and maintain context across sessions.

### What You'll Learn

- How to check status at session start
- How to select and start tasks
- How to track progress and add context
- How to handle blockers
- How to end sessions cleanly

### What You'll Practice

A complete daily workflow cycle from session start to session end.

---

## Prerequisites

### Required

- [ ] Vibey installed (`vibey --version` works)
- [ ] Vibey initialized in project (`.vibey/` exists)
- [ ] At least one track with sprints and tasks

### Verify Prerequisites

```bash
vibey roadmap status
# Should show at least 1 track with tasks
```

---

## Step 1: Start Your Session

### Goal

Understand the current state before starting work.

### Instructions

1. Get overall status:

   ```bash
   vibey roadmap status
   ```

   **Expected Output:**
   ```
   Vibey Roadmap Status
   ====================

   Tracks: 2 (1 in_progress, 1 not_started)
   Sprints: 5 (2 in_progress, 2 completed, 1 not_started)
   Tasks: 23 (15 completed, 3 in_progress, 5 not_started)

   Feature Development (in_progress)
     Sprint 2 - in_progress (5/8 tasks - 62%)
   ```

2. Check what's currently in progress:

   ```bash
   vibey roadmap activity --limit 5
   ```

   **Expected Output:**
   ```
   Recent Activity
   ===============
   2025-12-12 09:30 | completed | Task: Fix login validation
   2025-12-12 09:15 | started   | Task: Add user profile page
   2025-12-11 17:00 | completed | Task: Database migration
   ```

3. Review any blocked items:

   ```bash
   vibey roadmap list-blockers
   ```

### Checkpoint

> **Verify:** You know what's in_progress and what blockers exist

---

## Step 2: Select Your Next Task

### Goal

Choose what to work on based on priorities and dependencies.

### Instructions

1. View current sprint tasks:

   ```bash
   vibey roadmap show sprint <current-sprint-id>
   ```

   **Expected Output:**
   ```
   Sprint: Sprint 2 - API Development
   Status: in_progress
   Progress: 5/8 tasks (62%)

   Tasks:
     [completed] Fix login validation
     [completed] Add user profile page
     [in_progress] Implement OAuth flow
     [not_started] Add password reset
     [not_started] Write auth tests
     [blocked] Deploy to staging (blocked by: OAuth flow)
   ```

2. Check task details before selecting:

   ```bash
   vibey roadmap show task <task-id>
   ```

3. Start the task:

   ```bash
   vibey roadmap start <task-id>
   ```

   **Expected Output:**
   ```
   Started task: Add password reset
   Status: in_progress
   Started: 2025-12-12T10:00:00Z
   ```

### Checkpoint

> **Verify:** Task status changed to `in_progress`

---

## Step 3: Work on Your Task

### Goal

Track your work and maintain context.

### Instructions

1. Reference task details while working:

   ```bash
   vibey roadmap show task <task-id>
   ```

2. Add context notes as you work:

   ```bash
   vibey roadmap add-context <task-id> --message "Using email-templates library for reset emails"
   ```

   **Expected Output:**
   ```
   Added context to task: Add password reset
   ```

3. If you discover important information:

   ```bash
   vibey roadmap add-context <task-id> --message "Note: Password validation requires 12+ chars"
   ```

### Checkpoint

> **Verify:** Context was added (check with `show task`)

---

## Step 4: Handle Blockers

### Goal

Know what to do when you're blocked.

### Instructions

1. If you hit a blocker, document it:

   ```bash
   vibey roadmap update task <task-id> \
     --blocked true \
     --blocked-by "Waiting for SMTP credentials from ops team"
   ```

2. Add context about the blocker:

   ```bash
   vibey roadmap add-context <task-id> --message "Emailed ops team, expecting response by EOD"
   ```

3. Switch to another task:

   ```bash
   # Start a different task
   vibey roadmap start <other-task-id>
   ```

4. When blocker is resolved:

   ```bash
   vibey roadmap update task <task-id> --blocked false
   vibey roadmap start <task-id>
   ```

### Checkpoint

> **Verify:** Blocked task shows in `list-blockers`

---

## Step 5: Complete Your Task

### Goal

Mark work as done and record completion.

### Instructions

1. Complete the task:

   ```bash
   vibey roadmap complete <task-id>
   ```

   **Expected Output:**
   ```
   Completed task: Add password reset
   Status: completed
   Completed: 2025-12-12T14:30:00Z
   Duration: 4h 30m
   ```

2. Verify completion:

   ```bash
   vibey roadmap status
   ```

   Progress should increase.

### Checkpoint

> **Verify:** Task shows `completed` status, progress updated

---

## Step 6: End Your Session

### Goal

Leave things in a good state for next session.

### Instructions

1. Review what was accomplished:

   ```bash
   vibey roadmap activity --today
   ```

   **Expected Output:**
   ```
   Today's Activity
   ================
   10:00 | started   | Add password reset
   14:30 | completed | Add password reset
   14:35 | started   | Write auth tests

   Summary: 1 completed, 1 in_progress
   ```

2. Create a checkpoint:

   ```bash
   vibey roadmap checkpoint --message "Completed password reset feature"
   ```

3. Final status check:

   ```bash
   vibey roadmap status
   ```

### Checkpoint

> **Verify:** You know exactly what's in progress for tomorrow

---

## Summary

### What You Accomplished

- Started a development session with context
- Selected and started appropriate tasks
- Tracked progress with context notes
- Handled a blocker appropriately
- Completed tasks and ended session cleanly

### Commands Used

| Command | Purpose |
|---------|---------|
| `vibey roadmap status` | Overall view |
| `vibey roadmap activity` | Recent changes |
| `vibey roadmap show sprint/task` | Details |
| `vibey roadmap start <id>` | Begin task |
| `vibey roadmap complete <id>` | Finish task |
| `vibey roadmap add-context` | Add notes |
| `vibey roadmap update task --blocked` | Mark blocked |
| `vibey roadmap list-blockers` | View blocked items |
| `vibey roadmap checkpoint` | Save state |

### Next Steps

1. **Project Management:** [Project Lead Walkthrough](./WALKTHROUGH_PROJECT_LEAD.md)
2. **Git Integration:** Set up git hooks for automatic task linking
3. **Deep Dive:** [CLI Reference](../reference/CLI_REFERENCE.md)

---

## Quick Reference

### Daily Workflow Commands

```bash
# Session start
vibey roadmap status
vibey roadmap activity --limit 5
vibey roadmap list-blockers

# During work
vibey roadmap start <task-id>
vibey roadmap show task <task-id>
vibey roadmap add-context <task-id> --message "Note"

# Handle blockers
vibey roadmap update task <id> --blocked true --blocked-by "reason"

# Complete work
vibey roadmap complete <task-id>

# Session end
vibey roadmap activity --today
vibey roadmap checkpoint
```

### Related Documentation

- [CLI Reference](../reference/CLI_REFERENCE.md)
- [Active Developer Journey](../journeys/JOURNEY_ACTIVE_DEVELOPER.md)
- [User Personas](../personas/USER_PERSONAS.md#alex)
