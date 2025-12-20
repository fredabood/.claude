# Task Plan: Fix started_at before created_at causes task to be silently skipped

**Task ID:** 01KCY39YJW8A3YDNTFJY5KMDGQ
**Priority:** High
**Complexity:** Simple

## Problem Statement

Tasks with `started_at` timestamp before `created_at` are silently skipped during database load. This caused the PM Tool design doc task to be missing from the database entirely, with no user-visible error during normal operations.

### Root Cause

In `vibey/roadmap/serialization/yaml_loader.py`, the V2 format date fields (`created_at`, `started_at`, `completed_at`) are mapped to internal fields (`created`, `started`, `completed`). When the task model is created, validation rejects tasks where `started < created`, but this error is only logged and not surfaced to the user.

### Affected Code Locations

| File | Lines | Description |
|------|-------|-------------|
| `vibey/roadmap/serialization/yaml_loader.py` | 1554-1560 | V2 date field mapping |
| `vibey/roadmap/serialization/yaml_loader.py` | 1809-1811 | Task creation with datetime parsing |
| `vibey/roadmap/models/` | Various | Task model validation |

## Implementation Plan

### Step 1: Analyze Current Validation Logic
- [ ] Read yaml_loader.py lines 1554-1560 and 1809-1811
- [ ] Find where validation error is raised/caught
- [ ] Understand why error is silently swallowed

### Step 2: Decide on Fix Strategy

**Option A: Relax Validation (Recommended)**
- Allow `started_at` to precede `created_at`
- Rationale: Tasks can be created retroactively after work has begun
- This is a data modeling issue, not a data integrity issue

**Option B: Surface Error Clearly**
- Keep validation but show clear error message
- Include task ID and file path in error
- Optionally: auto-fix by setting `created_at = started_at`

### Step 3: Implement Fix
- [ ] If Option A: Remove or relax the validation check
- [ ] If Option B: Add user-visible error message with auto-fix option
- [ ] Ensure the error count is shown in database init/rebuild summary

### Step 4: Add Regression Test
- [ ] Create test task YAML with started_at < created_at
- [ ] Verify task loads successfully (Option A) or shows clear error (Option B)
- [ ] Add test to `tests/roadmap/serialization/test_yaml_loader.py`

### Step 5: Verify Fix
- [ ] Run `vibey roadmap db rebuild`
- [ ] Confirm PM Tool design doc task now loads
- [ ] Check no tasks are silently skipped

## Acceptance Criteria

- [ ] Tasks with `started_at < created_at` either load successfully OR show clear error
- [ ] No tasks are silently skipped without user awareness
- [ ] Regression test added and passing
- [ ] Database rebuild shows accurate skip count

## Estimated Effort

- Analysis: 15 minutes
- Implementation: 30 minutes
- Testing: 15 minutes
- **Total: ~1 hour**
