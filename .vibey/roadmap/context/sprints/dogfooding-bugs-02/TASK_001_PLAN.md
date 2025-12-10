# Task 001: Update FileSystemManager.get_roadmap_path() to use roadmap_root

**Task ID:** dogfooding-bugs-02-task-001
**Bug Addressed:** #3 (Wrong path resolution)
**Complexity:** Low
**Type:** Development

---

## Problem Statement

After migrating to flat directory structure, the CLI looks for `roadmap.yaml` at `.vibey/roadmap.yaml` (old location) instead of `.vibey/roadmap/roadmap.yaml` (correct location).

### Current Code (filesystem.py:197-199)

```python
def get_roadmap_path(self) -> Path:
    """Get path to roadmap.yaml (in roadmap root directory)."""
    return self.roadmap_root / self.ROADMAP_FILE
```

Wait - looking at the code, it already uses `roadmap_root`. Let me check the actual bug...

The issue is that `roadmap_root` is set to `.vibey/roadmap` but some callers may be using different paths.

---

## Root Cause Analysis

The `FileSystemManager` has:
- `self.vibey_dir = self.root_dir / ".vibey"`
- `self.roadmap_root = self.vibey_dir / "roadmap"`
- `get_roadmap_path()` returns `self.roadmap_root / "roadmap.yaml"`

This should return `.vibey/roadmap/roadmap.yaml` which is correct. The bug may be:
1. Callers not using `FileSystemManager`
2. Other code paths using hardcoded paths
3. Initialization issues

---

## Investigation Steps

1. Search for hardcoded paths to `roadmap.yaml`
2. Check all callers of `get_roadmap_path()`
3. Verify `roadmap_root` is correctly set in all cases
4. Check `YAMLBackend.load_roadmap()` in backend.py

---

## Files to Audit

| File | Function | Check |
|------|----------|-------|
| `vibey/cli/roadmap_lib/filesystem.py` | `get_roadmap_path()` | Verify returns roadmap_root path |
| `vibey/operations/roadmap/query.py` | Uses FileSystemManager? | Check path construction |
| `vibey/roadmap/serialization/backend.py` | `YAMLBackend.load_roadmap()` | Uses correct path? |
| `vibey/cli/commands.py` | All roadmap commands | Uses FileSystemManager? |

---

## Implementation

If the current implementation is correct, verify and document. If issues found:

```python
def get_roadmap_path(self) -> Path:
    """
    Get path to roadmap.yaml.

    Returns:
        Path to .vibey/roadmap/roadmap.yaml
    """
    # Ensure we always use the roadmap subdirectory, not .vibey directly
    return self.roadmap_root / self.ROADMAP_FILE
```

---

## Testing Strategy

```python
def test_get_roadmap_path():
    """Verify roadmap path is in roadmap/ subdirectory."""
    fs = FileSystemManager(Path("/project"))
    path = fs.get_roadmap_path()

    assert str(path).endswith(".vibey/roadmap/roadmap.yaml")
    assert ".vibey/roadmap.yaml" not in str(path)  # Old wrong path
```

---

## Success Criteria

- [ ] `get_roadmap_path()` returns `.vibey/roadmap/roadmap.yaml`
- [ ] All callers use `FileSystemManager` for path resolution
- [ ] No hardcoded roadmap.yaml paths outside of FileSystemManager
- [ ] Unit test verifies correct path

---

## Dependencies

None - this is a foundational fix.

---

## Notes

This task may reveal that the method is already correct and the bug is elsewhere. Document findings either way.
