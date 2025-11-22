# Schema Validation Audit Report

**Date:** 2025-11-22
**Sprint:** roadmap-integrity-fixes-8 (YAML Schema Remediation)
**Auditor:** Claude Code

---

## Executive Summary

Comprehensive audit of 471 roadmap YAML files revealed **84 issues** across **30 files** that require remediation, plus **71 warnings** that should be reviewed.

| Metric | Count |
|--------|-------|
| Files checked | 471 |
| Tracks audited | 20 |
| Sprints audited | 55 |
| Tasks audited | 387 |
| Files with issues | 30 |
| Total issues | 84 |
| Total warnings | 71 |

---

## Issue Summary by Type

| Issue Type | Count | Priority |
|------------|-------|----------|
| `name` vs `title` field mismatch | 72 | **CRITICAL** |
| Task count mismatch (progress vs actual) | 6 | HIGH |
| Invalid status value | 3 | MEDIUM |
| Other | 3 | LOW |

---

## Critical Issues: `name` vs `title` Field

**Problem:** Tasks should use `title` field but are using `name` field instead.

### Affected Tracks

#### 1. claude-port (8 task files + 1 sprint)
- `claude-port/claude-port-1/sprint.yaml` - 8 tasks with `name`
- `claude-port/claude-port-1/claude-port-1-task-001/task.yaml`
- `claude-port/claude-port-1/claude-port-1-task-002/task.yaml`
- `claude-port/claude-port-1/claude-port-1-task-003/task.yaml`
- `claude-port/claude-port-1/claude-port-1-task-004/task.yaml`
- `claude-port/claude-port-1/claude-port-1-task-005/task.yaml`
- `claude-port/claude-port-1/claude-port-1-task-006/task.yaml`
- `claude-port/claude-port-1/claude-port-1-task-007/task.yaml`
- `claude-port/claude-port-1/claude-port-1-task-008/task.yaml`

#### 2. interface-unification (3 sprints, 17 tasks)
- `interface-unification/interface-unification-1/sprint.yaml` - 6 tasks
- `interface-unification/interface-unification-2/sprint.yaml` - 5 tasks
- `interface-unification/interface-unification-3/sprint.yaml` - 6 tasks

#### 3. platform-context-management (5 sprints, 29 tasks)
- `platform-context-management/platform-context-management-1/sprint.yaml` - 5 tasks
- `platform-context-management/platform-context-management-2/sprint.yaml` - 5 tasks
- `platform-context-management/platform-context-management-3/sprint.yaml` - 5 tasks
- `platform-context-management/platform-context-management-4/sprint.yaml` - 8 tasks
- `platform-context-management/platform-context-management-5/sprint.yaml` - 6 tasks

#### 4. roadmap-system (Sprint 7 only - 5 task files + 1 sprint)
- `roadmap-system/roadmap-system-7/sprint.yaml` - 5 tasks
- `roadmap-system/roadmap-system-7/roadmap-system-7-task-001/task.yaml`
- `roadmap-system/roadmap-system-7/roadmap-system-7-task-002/task.yaml`
- `roadmap-system/roadmap-system-7/roadmap-system-7-task-003/task.yaml`
- `roadmap-system/roadmap-system-7/roadmap-system-7-task-004/task.yaml`
- `roadmap-system/roadmap-system-7/roadmap-system-7-task-005/task.yaml`

**Total:** 72 instances across 4 tracks

---

## High Priority: Task Count Mismatches

Progress counters don't match actual task states:

| Sprint | Reported Completed | Actual Completed | Discrepancy |
|--------|-------------------|------------------|-------------|
| interface-unification-1 | 0 | 6 | +6 |
| interface-unification-2 | 0 | 5 | +5 |
| interface-unification-3 | 0 | 6 | +6 |
| roadmap-integrity-fixes-0 | 6 | 0 | -6 |
| roadmap-integrity-fixes-1 | 5 | 0 | -5 |
| roadmap-integrity-fixes-9 | 4 | 0 | -4 |

---

## Medium Priority: Invalid Status Values

| File | Invalid Status |
|------|----------------|
| `roadmap-integration/track.yaml` | `superseded` (in sprints array) |
| `roadmap-integration/roadmap-integration-1/sprint.yaml` | `superseded` |
| `roadmap-integration/roadmap-integration-2/sprint.yaml` | `superseded` |
| `roadmap-integration/roadmap-integration-3/sprint.yaml` | `superseded` |

**Note:** `superseded` may be a valid status for tracks but is not in the standard sprint status enum.

---

## Warnings: `type` vs `task_type` Field

**Problem:** Task files should use `task_type` but many use `type` instead.

**Affected:** 63 task files in `roadmap-system` (Sprints 1-7)

This is a lower priority since both fields may be accepted by the loader, but should be standardized.

---

## Warnings: Task Total Mismatches

Progress counters show 0 total tasks but tasks exist:

| Sprint | Reported Total | Actual Total |
|--------|---------------|--------------|
| interface-unification-1 | 0 | 6 |
| interface-unification-2 | 0 | 5 |
| interface-unification-3 | 0 | 6 |
| platform-context-management-1 | 0 | 5 |
| platform-context-management-2 | 0 | 5 |
| platform-context-management-3 | 0 | 5 |
| platform-context-management-4 | 0 | 8 |
| platform-context-management-5 | 0 | 6 |

---

## Remediation Plan

### Phase 1: Fix `name` → `title` (72 issues)
1. Create migration script to rename `name` to `title` in task objects
2. Apply to sprint.yaml task arrays
3. Apply to standalone task.yaml files
4. Validate changes

### Phase 2: Fix Task Count Mismatches (6 issues)
1. Recalculate completed task counts from actual task statuses
2. Update progress counters in sprint.yaml files
3. Propagate changes to track.yaml

### Phase 3: Standardize Status Values (3 issues)
1. Either add `superseded` to valid sprint statuses OR
2. Change roadmap-integration sprints to `completed` with supersession note

### Phase 4: Fix `type` → `task_type` (63 warnings)
1. Create migration script for `type` → `task_type`
2. Apply to all roadmap-system task files

### Phase 5: Fix Task Total Mismatches (8 warnings)
1. Update progress.tasks_total to match actual task count
2. Apply to affected sprints

---

## Files Requiring Changes

### Must Fix (30 files)
```
claude-port/claude-port-1/sprint.yaml
claude-port/claude-port-1/claude-port-1-task-001/task.yaml
claude-port/claude-port-1/claude-port-1-task-002/task.yaml
claude-port/claude-port-1/claude-port-1-task-003/task.yaml
claude-port/claude-port-1/claude-port-1-task-004/task.yaml
claude-port/claude-port-1/claude-port-1-task-005/task.yaml
claude-port/claude-port-1/claude-port-1-task-006/task.yaml
claude-port/claude-port-1/claude-port-1-task-007/task.yaml
claude-port/claude-port-1/claude-port-1-task-008/task.yaml
interface-unification/interface-unification-1/sprint.yaml
interface-unification/interface-unification-2/sprint.yaml
interface-unification/interface-unification-3/sprint.yaml
platform-context-management/platform-context-management-1/sprint.yaml
platform-context-management/platform-context-management-2/sprint.yaml
platform-context-management/platform-context-management-3/sprint.yaml
platform-context-management/platform-context-management-4/sprint.yaml
platform-context-management/platform-context-management-5/sprint.yaml
roadmap-integration/track.yaml
roadmap-integration/roadmap-integration-1/sprint.yaml
roadmap-integration/roadmap-integration-2/sprint.yaml
roadmap-integration/roadmap-integration-3/sprint.yaml
roadmap-integrity-fixes/roadmap-integrity-fixes-0/sprint.yaml
roadmap-integrity-fixes/roadmap-integrity-fixes-1/sprint.yaml
roadmap-integrity-fixes/roadmap-integrity-fixes-9/sprint.yaml
roadmap-system/roadmap-system-7/sprint.yaml
roadmap-system/roadmap-system-7/roadmap-system-7-task-001/task.yaml
roadmap-system/roadmap-system-7/roadmap-system-7-task-002/task.yaml
roadmap-system/roadmap-system-7/roadmap-system-7-task-003/task.yaml
roadmap-system/roadmap-system-7/roadmap-system-7-task-004/task.yaml
roadmap-system/roadmap-system-7/roadmap-system-7-task-005/task.yaml
```

### Should Review (63+ files)
- All task.yaml files in `roadmap-system/roadmap-system-{1-7}/` using `type` instead of `task_type`

---

## Estimated Effort

| Phase | Files | Estimated Time |
|-------|-------|----------------|
| Phase 1: name → title | ~25 | 30 minutes |
| Phase 2: Count mismatches | 6 | 15 minutes |
| Phase 3: Status values | 4 | 10 minutes |
| Phase 4: type → task_type | 63 | 20 minutes |
| Phase 5: Total mismatches | 8 | 10 minutes |
| **Total** | **~106** | **~1.5 hours** |

---

## Validation Command

After remediation, run:
```bash
python3 scripts/validate-schema-compliance.py
vibey roadmap validate-fast
```

---

**Report Generated:** 2025-11-22
**Next Action:** Begin Phase 1 remediation (name → title migration)
