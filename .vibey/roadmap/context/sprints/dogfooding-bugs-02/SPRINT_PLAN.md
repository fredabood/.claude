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

1. **Update FileSystemManager.get_roadmap_path() to use roadmap_root** (development, low complexity)
2. **Update all callers to use correct path** (development, low complexity)
3. **Add unit test for path resolution** (testing, low complexity)
4. **Design new loading strategy for ULID files** (research, medium complexity)
5. **Update load_roadmap to discover tracks from tracks/*.yaml** (development, high complexity)
6. **Implement lazy loading for track details** (development, medium complexity)
7. **Update query.py to use new loading strategy** (development, medium complexity)
8. **Add integration tests for ULID file loading** (testing, medium complexity)
9. **Debug track discovery in FileSystemManager.list_tracks()** (research, low complexity)
10. **Fix track filtering/discovery logic** (development, medium complexity)
11. **Add integration test for track listing** (testing, low complexity)
12. **Implement sync mechanism ULID files to roadmap.yaml** (development, medium complexity)
13. **Add CLI command to sync roadmap.yaml** (development, medium complexity)
14. **Add validation to detect sync discrepancies** (development, medium complexity)
15. **Update validation to accept ULID-based sprint IDs** (development, medium complexity)
16. **Add backward compatibility for slug-based IDs** (development, low complexity)
17. **Add unit tests for both ID formats** (testing, medium complexity)

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
