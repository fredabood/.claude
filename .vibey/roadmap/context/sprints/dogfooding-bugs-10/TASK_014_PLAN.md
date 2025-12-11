# Task 014: Update Test Files for Flat Structure

**Task ID:** `01KC6WAAM87S5VVJ1JBN29PBX4`
**Bug Addressed:** #19
**Complexity:** Medium
**Priority:** Low
**Type:** Testing

## Problem Statement

3 test files create hierarchical structures for testing. These need to be updated to test flat structure behavior.

## Current State (from HIERARCHICAL_AUDIT.md)

| File | Notes |
|------|-------|
| `test_hierarchical_integration.py` | Tests hierarchical DirectoryManager |
| `test_toc_generator.py` | Creates temp hierarchical structures |
| `test_directory_manager.py` | Tests DirectoryManager (slug-based) |

## Implementation Plan

### File 1: test_hierarchical_integration.py

Location: `vibey/roadmap/test_hierarchical_integration.py`

**Options:**
1. **Delete**: If testing obsolete functionality
2. **Rename & Update**: To `test_flat_structure_integration.py`
3. **Keep as Legacy**: Mark as testing deprecated behavior

**Recommended: Update to test flat structure**

```python
class TestFlatStructureIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.roadmap_dir = Path(self.temp_dir) / ".vibey" / "roadmap"
        # Create flat structure
        (self.roadmap_dir / "tracks").mkdir(parents=True)
        (self.roadmap_dir / "sprints").mkdir(parents=True)
        (self.roadmap_dir / "tasks").mkdir(parents=True)

    def test_track_loading_from_flat_structure(self):
        # Create track file
        track_file = self.roadmap_dir / "tracks" / "01ABCD.yaml"
        # ... test loading

    def test_sprint_loading_from_flat_structure(self):
        # Create sprint file
        sprint_file = self.roadmap_dir / "sprints" / "01EFGH.yaml"
        # ... test loading
```

### File 2: test_toc_generator.py

Location: `vibey/roadmap/test_toc_generator.py`

Update test fixtures to create flat structure:

```python
def setUp(self):
    # BEFORE: Created nested directories
    # track_dir = self.temp_dir / "track-slug"
    # sprint_dir = track_dir / "sprint-slug"

    # AFTER: Create flat structure
    self.tracks_dir = self.temp_dir / "tracks"
    self.sprints_dir = self.temp_dir / "sprints"
    self.tasks_dir = self.temp_dir / "tasks"
    self.tracks_dir.mkdir()
    self.sprints_dir.mkdir()
    self.tasks_dir.mkdir()
```

Update test methods to use flat paths.

### File 3: test_directory_manager.py

Location: `vibey/roadmap/test_directory_manager.py`

**Note:** DirectoryManager uses slugs for context directories, which may still be valid.

Review each test:
1. Tests for slug-based context directories: KEEP (context uses slugs)
2. Tests for ULID-based entity directories: UPDATE or REMOVE

```python
# Tests that should remain (context directories use slugs):
def test_context_directory_creation(self):
    dm.create_track_context("my-track-slug")
    # Context at: .vibey/roadmap/context/tracks/my-track-slug/

# Tests that should be updated (entity files use flat structure):
def test_track_file_path(self):
    # BEFORE: Expected .vibey/roadmap/my-track/track.yaml
    # AFTER: Expected .vibey/roadmap/tracks/{ulid}.yaml
    path = dm.get_track_path(track_id)
    self.assertEqual(path, roadmap_dir / "tracks" / f"{track_id}.yaml")
```

## Files to Modify

| File | Action |
|------|--------|
| `vibey/roadmap/test_hierarchical_integration.py` | Update or delete |
| `vibey/roadmap/test_toc_generator.py` | Update fixtures |
| `vibey/roadmap/test_directory_manager.py` | Update entity path tests |

## Testing

1. Run updated tests: `.venv/bin/pytest vibey/roadmap/test_*.py -v`
2. Verify all tests pass
3. Verify test coverage for flat structure

## Success Criteria

- [ ] `test_hierarchical_integration.py` updated or deleted
- [ ] `test_toc_generator.py` uses flat structure fixtures
- [ ] `test_directory_manager.py` tests updated for flat entity paths
- [ ] All tests pass
- [ ] Good test coverage for flat structure behavior

## Dependencies

- Tasks 002-012: Production code must be migrated first
- This is the final cleanup task
