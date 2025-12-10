# Sprint 2: ULID File Loading System

**Bugs Addressed:** #3, #10, #2, #12, #4
**Priority:** CRITICAL
**Status:** NOT_STARTED

---

## Description

Complete the ULID migration by updating CLI to read from individual ULID files instead of monolithic roadmap.yaml. Fix path resolution, track discovery, and model validation.

---

## Goal

CLI correctly reads all data from ULID flat file structure

---

## Success Criteria

- FileSystemManager uses correct roadmap.yaml location
- load_roadmap discovers tracks from tracks/*.yaml
- All 39 tracks visible in 'roadmap status'
- Track model validates ULID-based sprint IDs
- New tracks sync back to roadmap.yaml

---

## Dependencies

- dogfooding-bugs-01

---

## Tasks (17 total)

### Bug #3: Wrong Path Resolution (Tasks 001-003)

| Task | Title | Type | Complexity | Plan |
|------|-------|------|------------|------|
| 001 | Update FileSystemManager.get_roadmap_path() to use roadmap_root | development | low | [TASK_001_PLAN.md](TASK_001_PLAN.md) |
| 002 | Update all callers to use correct path | development | low | [TASK_002_PLAN.md](TASK_002_PLAN.md) |
| 003 | Add unit test for path resolution | testing | low | [TASK_003_PLAN.md](TASK_003_PLAN.md) |

### Bug #10: Monolithic roadmap.yaml Read (Tasks 004-008)

| Task | Title | Type | Complexity | Plan |
|------|-------|------|------------|------|
| 004 | Design new loading strategy for ULID files | research | medium | [TASK_004_PLAN.md](TASK_004_PLAN.md) |
| 005 | Update load_roadmap to discover tracks from tracks/*.yaml | development | high | [TASK_005_PLAN.md](TASK_005_PLAN.md) |
| 006 | Implement lazy loading for track details | development | medium | [TASK_006_PLAN.md](TASK_006_PLAN.md) |
| 007 | Update query.py to use new loading strategy | development | medium | [TASK_007_PLAN.md](TASK_007_PLAN.md) |
| 008 | Add integration tests for ULID file loading | testing | medium | [TASK_008_PLAN.md](TASK_008_PLAN.md) |

### Bug #2: Tracks Not Showing (Tasks 009-011)

| Task | Title | Type | Complexity | Plan |
|------|-------|------|------------|------|
| 009 | Debug track discovery in FileSystemManager.list_tracks() | research | low | [TASK_009_PLAN.md](TASK_009_PLAN.md) |
| 010 | Fix track filtering/discovery logic | development | medium | [TASK_010_PLAN.md](TASK_010_PLAN.md) |
| 011 | Add integration test for track listing | testing | low | [TASK_011_PLAN.md](TASK_011_PLAN.md) |

### Bug #12: New Tracks Not Syncing (Tasks 012-014)

| Task | Title | Type | Complexity | Plan |
|------|-------|------|------------|------|
| 012 | Implement sync mechanism ULID files to roadmap.yaml | development | medium | [TASK_012_PLAN.md](TASK_012_PLAN.md) |
| 013 | Add CLI command to sync roadmap.yaml | development | medium | [TASK_013_PLAN.md](TASK_013_PLAN.md) |
| 014 | Add validation to detect sync discrepancies | development | medium | [TASK_014_PLAN.md](TASK_014_PLAN.md) |

### Bug #4: ULID Sprint ID Validation (Tasks 015-017)

| Task | Title | Type | Complexity | Plan |
|------|-------|------|------------|------|
| 015 | Update validation to accept ULID-based sprint IDs | development | medium | [TASK_015_PLAN.md](TASK_015_PLAN.md) |
| 016 | Add backward compatibility for slug-based IDs | development | medium | [TASK_016_PLAN.md](TASK_016_PLAN.md) |
| 017 | Add unit tests for both ID formats | testing | medium | [TASK_017_PLAN.md](TASK_017_PLAN.md) |

---

## Sprint Plan

### Approach
1. Review affected code and understand current behavior
2. Design solution that maintains backward compatibility
3. Implement changes with comprehensive tests
4. Verify all success criteria are met
5. Update documentation as needed

### Risks
- Changes may affect other parts of the system
- Backward compatibility must be maintained
- Tests must cover edge cases

### Notes
This sprint consolidates the following original bugs:
- Bug #3
- Bug #10
- Bug #2
- Bug #12
- Bug #4
