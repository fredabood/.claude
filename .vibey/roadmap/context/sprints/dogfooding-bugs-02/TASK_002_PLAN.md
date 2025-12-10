# Task 002: Update All Callers to Use Correct Path

**Task ID:** dogfooding-bugs-02-task-002
**Bug Addressed:** #3 (Wrong path resolution)
**Complexity:** Low
**Type:** Development

---

## Problem Statement

Multiple code paths may be constructing roadmap.yaml paths independently rather than using `FileSystemManager.get_roadmap_path()`. This leads to inconsistent path resolution.

---

## Audit Locations

### 1. vibey/roadmap/serialization/backend.py

```python
class YAMLBackend(StorageBackend):
    def load_roadmap(self, roadmap_id: str = "vibey-framework-v2") -> Roadmap:
        """Load a roadmap from YAML."""
        from .yaml_loader import load_roadmap
        return load_roadmap(self.roadmap_dir / "roadmap.yaml")  # Correct?
```

### 2. vibey/operations/roadmap/query.py

```python
def load_roadmap(file_path_or_id, root_dir: Optional[Path] = None):
    ...
    return yaml_load_roadmap(file_path_or_id)  # How is file_path_or_id constructed?
```

### 3. vibey/cli/roadmap_commands/list_cmd.py

```python
def list_tracks(fs: FileSystemManager, status_filter: Optional[str] = None):
    roadmap_path = fs.get_roadmap_path()  # CORRECT - uses FileSystemManager
```

### 4. Direct yaml_loader imports

Search for files that import `load_roadmap` from `yaml_loader` and construct paths manually.

---

## Implementation Steps

1. **Search** for all roadmap.yaml path constructions:
   ```bash
   grep -r "roadmap\.yaml" vibey/
   grep -r "load_roadmap(" vibey/
   ```

2. **Identify** callers not using `FileSystemManager`

3. **Refactor** to use `FileSystemManager.get_roadmap_path()`:
   ```python
   # Before
   roadmap_path = Path(".vibey/roadmap.yaml")

   # After
   fs = FileSystemManager(root_dir)
   roadmap_path = fs.get_roadmap_path()
   ```

4. **Update** backend.py if needed:
   ```python
   class YAMLBackend(StorageBackend):
       def __init__(self, roadmap_dir: Path):
           self.roadmap_dir = roadmap_dir
           self.fs = FileSystemManager(roadmap_dir.parent.parent)  # .vibey parent

       def load_roadmap(self, roadmap_id: str = "vibey-framework-v2") -> Roadmap:
           return load_roadmap(self.fs.get_roadmap_path())
   ```

---

## Files to Modify

| File | Current | Fix |
|------|---------|-----|
| `vibey/roadmap/serialization/backend.py` | `self.roadmap_dir / "roadmap.yaml"` | Use FileSystemManager |
| `vibey/operations/roadmap/query.py` | May construct paths manually | Use FileSystemManager |
| Any other direct path users | - | Refactor to FileSystemManager |

---

## Testing Strategy

1. Add integration test that verifies path resolution end-to-end
2. Run CLI commands with flat structure and verify they find roadmap.yaml
3. Check that no "File not found" errors occur for roadmap.yaml

---

## Success Criteria

- [ ] All roadmap.yaml path construction uses `FileSystemManager`
- [ ] No hardcoded `.vibey/roadmap.yaml` paths remain
- [ ] CLI commands work with flat directory structure
- [ ] Path resolution is consistent across all code paths

---

## Dependencies

- Task 001 (verify get_roadmap_path is correct)

---

## Notes

This task standardizes path resolution. After completion, there should be exactly ONE place where the roadmap.yaml path pattern is defined: `FileSystemManager.get_roadmap_path()`.
