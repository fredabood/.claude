# Task 004: Verify Single roadmap.yaml Exists at Correct Location

**Task ID:** dogfooding-bugs-06-task-004
**Bug Addressed:** #14 (Duplicate roadmap.yaml Files Existed at Two Locations)
**Complexity:** Low
**Type:** Testing

---

## Problem Statement

Bug #14 documented that two `roadmap.yaml` files existed with different data:
- `.vibey/roadmap.yaml` (108 KB, old location, stale data)
- `.vibey/roadmap/roadmap.yaml` (5 KB, correct location, updated data)

The duplicate was deleted, but we need verification tests to ensure:
1. Only one roadmap.yaml exists at the correct location
2. The file contains valid roadmap data
3. CLI commands use the correct location

---

## Current State

**Bug #14 Status:** Fixed - Duplicate deleted

**Canonical Location:** `.vibey/roadmap/roadmap.yaml`

**Old Location (DELETED):** `.vibey/roadmap.yaml`

---

## Implementation

### Verification Test Script

```python
# tests/operations/roadmap/test_roadmap_location.py

import pytest
from pathlib import Path


class TestRoadmapLocation:
    """Verify roadmap.yaml exists only at correct location."""

    @pytest.fixture
    def project_root(self):
        """Get actual project root."""
        # Find repository root by looking for .vibey
        root = Path.cwd()
        while root != root.parent:
            if (root / ".vibey").exists():
                return root
            root = root.parent
        pytest.skip("Not in a Vibey project")

    def test_roadmap_at_correct_location(self, project_root):
        """roadmap.yaml exists at .vibey/roadmap/roadmap.yaml."""
        correct_path = project_root / ".vibey" / "roadmap" / "roadmap.yaml"
        assert correct_path.exists(), f"roadmap.yaml not found at {correct_path}"

    def test_no_duplicate_at_old_location(self, project_root):
        """No roadmap.yaml at old .vibey/roadmap.yaml location."""
        old_path = project_root / ".vibey" / "roadmap.yaml"
        assert not old_path.exists(), f"Duplicate roadmap.yaml found at old location: {old_path}"

    def test_roadmap_is_valid_yaml(self, project_root):
        """roadmap.yaml is valid YAML."""
        import yaml

        roadmap_path = project_root / ".vibey" / "roadmap" / "roadmap.yaml"
        with open(roadmap_path) as f:
            data = yaml.safe_load(f)

        assert data is not None, "roadmap.yaml is empty"
        assert isinstance(data, dict), "roadmap.yaml root is not a dictionary"

    def test_roadmap_has_required_fields(self, project_root):
        """roadmap.yaml has required fields."""
        import yaml

        roadmap_path = project_root / ".vibey" / "roadmap" / "roadmap.yaml"
        with open(roadmap_path) as f:
            data = yaml.safe_load(f)

        assert 'roadmap' in data, "Missing 'roadmap' root key"

        roadmap = data['roadmap']
        required = ['id', 'name', 'status']
        for field in required:
            assert field in roadmap, f"Missing required field: roadmap.{field}"

    def test_filesystem_manager_uses_correct_path(self, project_root):
        """FileSystemManager.get_roadmap_path() returns correct location."""
        import sys
        sys.path.insert(0, str(project_root))

        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        fs = FileSystemManager(project_root)
        roadmap_path = fs.get_roadmap_path()

        expected = project_root / ".vibey" / "roadmap" / "roadmap.yaml"
        assert roadmap_path == expected, f"Wrong path: {roadmap_path}, expected: {expected}"
```

### Manual Verification Commands

```bash
# Run these commands to verify Bug #14 is fixed

# 1. Check correct location exists
ls -la .vibey/roadmap/roadmap.yaml

# 2. Check old location does NOT exist
ls -la .vibey/roadmap.yaml  # Should fail with "No such file"

# 3. Verify content is valid
python3 -c "
import yaml
with open('.vibey/roadmap/roadmap.yaml') as f:
    data = yaml.safe_load(f)
    print(f'ID: {data[\"roadmap\"][\"id\"]}')
    print(f'Name: {data[\"roadmap\"][\"name\"]}')
    print(f'Tracks: {len(data[\"roadmap\"].get(\"tracks\", []))}')
"

# 4. Verify CLI uses correct path
vibey roadmap status  # Should work without errors
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `tests/operations/roadmap/test_roadmap_location.py` | Location verification tests |

---

## Success Criteria

- [ ] Test confirms `.vibey/roadmap/roadmap.yaml` exists
- [ ] Test confirms `.vibey/roadmap.yaml` does NOT exist
- [ ] Test confirms roadmap.yaml is valid YAML
- [ ] Test confirms roadmap has required fields
- [ ] Test confirms FileSystemManager uses correct path
- [ ] Manual verification commands all pass
- [ ] CLI commands work without "roadmap not found" errors

---

## Dependencies

- Bug #14 already fixed (duplicate deleted)

---

## Notes

This is a verification task to confirm the fix is complete and add regression tests.

The canonical location per the unified architecture design is:
```
.vibey/roadmap/roadmap.yaml
```

The old location was:
```
.vibey/roadmap.yaml
```

This task provides the safety net to ensure the duplicate issue doesn't recur.
