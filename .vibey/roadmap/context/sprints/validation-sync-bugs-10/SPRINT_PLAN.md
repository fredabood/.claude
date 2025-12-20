# Sprint 10: Validation and Sync Bugs

**Sprint ID:** 01KCY39YJW8A3YDNTFJY5KMDGP
**Track:** CLI Dogfooding Bug Fixes
**Status:** Not Started
**Priority:** High

## Overview

This sprint addresses 5 validation and synchronization bugs discovered during the roadmap state audit. These bugs cause data to be silently skipped during database loads and create inconsistencies between YAML files and the SQLite database.

## Tasks

| # | Task | ID | Priority | Effort |
|---|------|----|---------:|-------:|
| 1 | Fix started_at before created_at causes task skip | 01KCY39YJW8A3YDNTFJY5KMDGQ | High | 1h |
| 2 | Fix blocked_by/depends_on ULID string parsing | 01KCY39YJW8A3YDNTFJY5KMDGR | High | 45m |
| 3 | Fix track status not auto-updating to in_progress | 01KCY39YJW8A3YDNTFJY5KMDGS | Medium | 1.5h |
| 4 | Fix YAML progress counters not synced | 01KCY39YJW8A3YDNTFJY5KMDGT | Low | 2h |
| 5 | Fix sync setting completed without date | 01KCY39YJW8A3YDNTFJY5KMDGV | High | 1h |

**Total Estimated Effort:** ~6.25 hours

## Recommended Order

1. **Task 5** (completed status date) - Simple fix, high impact
2. **Task 2** (blocked_by parsing) - Simple fix, unblocks Sprint 2 data
3. **Task 1** (started_at validation) - Simple fix, unblocks task data
4. **Task 3** (track status auto-update) - Medium complexity
5. **Task 4** (YAML progress sync) - Lowest priority, design decision needed

## Success Criteria

- [ ] Database rebuild shows 0 skipped files (excluding intentional validation errors)
- [ ] All track statuses reflect actual work state
- [ ] Progress counters are accurate
- [ ] No validation errors for date/status inconsistencies

## Task Plans

Detailed task plans are available in this directory:
- `TASK_01_started_at_validation.md`
- `TASK_02_blocked_by_parsing.md`
- `TASK_03_track_status_auto_update.md`
- `TASK_04_yaml_progress_sync.md`
- `TASK_05_completed_status_date.md`

## Key Files to Modify

| File | Tasks |
|------|-------|
| `vibey/roadmap/serialization/yaml_loader.py` | 1, 2 |
| `vibey/operations/roadmap/update.py` | 3, 4, 5 |
| `vibey/operations/roadmap/status_manager.py` | 3, 5 |
| `vibey/roadmap/serialization/yaml_dumper.py` | 4 |

## Testing Strategy

1. **Unit Tests:** Add tests for each fix in corresponding test files
2. **Integration Test:** Run full database rebuild and verify counts
3. **Regression Test:** Ensure existing functionality not broken
