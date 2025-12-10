# Task 005: Manual Verification with Test Sprint

**Task ID:** dogfooding-bugs-04-task-005
**Bug Addressed:** #1 (Track and Sprint Progress Not Auto-Updated After Task Completion)
**Complexity:** Low
**Type:** Testing

---

## Problem Statement

After implementing and unit testing the progress propagation fixes (Tasks 001-004), manual end-to-end verification ensures the fix works in the real repository with actual roadmap data.

---

## Test Scenario

### Use the Actual Vibey Repository

The vibey repository itself is dogfooding the roadmap system. We can verify Bug #1 is fixed by:

1. Finding a sprint with incomplete tasks
2. Completing a task via CLI
3. Verifying progress updates propagate

---

## Verification Steps

### Step 1: Check Current State

```bash
# List tracks and their progress
vibey roadmap status

# Find a track with incomplete sprints
vibey roadmap show track dogfooding-bugs

# Find a sprint with incomplete tasks
vibey roadmap show sprint dogfooding-bugs-04
```

**Record initial state:**
- Track progress: ____/____ tasks completed
- Sprint progress: ____/____ tasks completed
- Track status: ____________
- Sprint status: ____________

### Step 2: Complete a Task

```bash
# Find an incomplete task
vibey roadmap show sprint dogfooding-bugs-04 --tasks

# Complete the task (e.g., this research task!)
vibey roadmap update task dogfooding-bugs-04-task-001 --status completed
```

### Step 3: Verify Propagation

```bash
# Check sprint progress updated
vibey roadmap show sprint dogfooding-bugs-04

# Expected:
# - tasks_completed should increase by 1
# - completion_percent should update
# - Sprint status may auto-progress if conditions met

# Check track progress updated
vibey roadmap show track dogfooding-bugs

# Expected:
# - tasks_completed should increase by 1
# - completion_percent should update

# Check roadmap progress updated
vibey roadmap status

# Expected:
# - Total tasks completed should increase
```

### Step 4: Verify Auto-Progression

If completing all tasks in a sprint:

```bash
# Complete remaining tasks
vibey roadmap update task dogfooding-bugs-04-task-002 --status completed
vibey roadmap update task dogfooding-bugs-04-task-003 --status completed
vibey roadmap update task dogfooding-bugs-04-task-004 --status completed
vibey roadmap update task dogfooding-bugs-04-task-005 --status completed

# Verify sprint auto-progressed
vibey roadmap show sprint dogfooding-bugs-04

# Expected:
# - Sprint status should progress to completion_gate_check or beyond
# - Track progress should reflect completed sprint
```

---

## Test Matrix

| Action | Expected Result | Actual Result | Pass/Fail |
|--------|-----------------|---------------|-----------|
| Complete 1 task | Sprint tasks_completed +1 | | |
| Complete 1 task | Track tasks_completed +1 | | |
| Complete 1 task | Roadmap tasks_completed +1 | | |
| Complete all tasks | Sprint auto-progresses | | |
| Complete sprint | Track sprints_completed +1 | | |
| Complete all sprints | Track auto-completes | | |

---

## Verification Commands

### Progress Inspection

```bash
# Sprint progress details
vibey roadmap show sprint dogfooding-bugs-04 --json | jq '.progress'

# Track progress details
vibey roadmap show track dogfooding-bugs --json | jq '.progress'

# Roadmap summary
vibey roadmap status --json | jq '.progress'
```

### Manual YAML Inspection

```bash
# Sprint YAML
cat .vibey/roadmap/sprints/01KC2D0JKVT80AFQ6C1PA8CKJD.yaml | grep -A10 progress

# Track YAML
cat .vibey/roadmap/tracks/01KC2D0FT6KF4V2R1J0HDFR1ZM.yaml | grep -A10 progress

# Roadmap YAML
cat .vibey/roadmap/roadmap.yaml | grep -A10 progress
```

### Database Verification (if SQLite enabled)

```bash
# Check database state
vibey roadmap db status

# Query progress from database
sqlite3 .vibey/roadmap.db "SELECT * FROM sprints WHERE id LIKE '%dogfooding%';"
```

---

## Edge Cases to Test

### 1. Task with No Sprint (Orphan)

```bash
# Create orphan task (should not crash progress updates)
# Manually edit YAML to have invalid sprint_id
```

### 2. Sprint with No Track

```bash
# Create sprint without track_id
# Verify progress updates handle gracefully
```

### 3. Concurrent Updates

```bash
# Open two terminal windows
# Complete different tasks simultaneously
# Verify both updates apply correctly
```

### 4. Rollback Test

```bash
# Complete a task
# Manually revert status
# Re-complete task
# Verify progress correct (no double-counting)
```

---

## Success Criteria Checklist

- [ ] Completing task updates sprint progress immediately
- [ ] Completing task updates track progress
- [ ] Completing task updates roadmap progress
- [ ] Sprint auto-progresses when all dev tasks complete
- [ ] Track auto-progresses when all sprints complete
- [ ] Progress percentages calculate correctly
- [ ] No errors or warnings during updates
- [ ] SQLite database stays in sync (if enabled)
- [ ] Works with actual dogfooding-bugs track

---

## Bug Reproduction Steps (Before Fix)

To verify the bug existed before the fix:

```bash
# 1. Check out commit before fix
git checkout <pre-fix-commit>

# 2. Complete a task
vibey roadmap update task dogfooding-bugs-04-task-001 --status completed

# 3. Check sprint progress
vibey roadmap show sprint dogfooding-bugs-04
# Expected to show: tasks_completed still 0 (BUG)

# 4. Revert to current
git checkout main
```

---

## Post-Fix Verification

After verifying the fix works:

```bash
# Update this task's status
vibey roadmap update task dogfooding-bugs-04-task-005 --status completed

# Record final state
vibey roadmap show sprint dogfooding-bugs-04 > verification_results.txt
vibey roadmap show track dogfooding-bugs >> verification_results.txt
vibey roadmap status >> verification_results.txt
```

---

## Dependencies

- Tasks 001-004 (implementation and unit tests complete)

---

## Notes

This manual verification:
1. Confirms the fix works in production environment
2. Tests with real roadmap data (not just fixtures)
3. Validates the entire stack (CLI → operations → models → serialization)
4. Provides confidence before closing Bug #1

The dogfooding-bugs track is perfect for this because:
- We're actively working on it
- Progress changes are expected
- Any issues will be immediately visible
