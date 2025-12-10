# Bug #10: CLI Reads from Monolithic roadmap.yaml

**Date:** 2025-12-09
**Severity:** CRITICAL
**Status:** DOCUMENTED

---

## Description

CLI reads from monolithic file instead of ULID files.

---

## Root Cause

load_roadmap reads from monolithic file which only has TrackSummary.

---

## Files Affected

- `vibey/roadmap/serialization/yaml_loader.py`
- `vibey/operations/roadmap/query.py`

---

## Tasks

1. **Design new loading strategy for ULID files** (research, medium complexity)
2. **Update load_roadmap to discover tracks from tracks/*.yaml** (development, high complexity)
3. **Implement lazy loading for track details** (development, medium complexity)
4. **Update query.py to use new loading strategy** (development, medium complexity)
5. **Add integration tests for ULID file loading** (testing, medium complexity)

---

## Sprint Plan

### Goal
Fix Bug #10: CLI Reads from Monolithic roadmap.yaml

### Success Criteria
1. Root cause addressed: load_roadmap reads from monolithic file which only has TrackSummary.
2. All affected files updated
3. Unit tests pass
4. Integration tests pass

### Approach
1. Research and understand the bug
2. Implement the fix
3. Add/update tests
4. Verify fix works
