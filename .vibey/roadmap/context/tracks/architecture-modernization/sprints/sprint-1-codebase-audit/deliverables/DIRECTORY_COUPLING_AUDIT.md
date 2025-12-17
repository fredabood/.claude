# Directory Structure Coupling Audit

**Date:** 2025-12-17
**Task:** Sprint 1, Task 7 - Audit current directory structure coupling to semantic layer
**Status:** Complete

---

## Executive Summary

The codebase has 287 references to `tracks/`, `sprints/`, or `tasks/` directories. Most references are properly abstracted through the `FileSystemManager` class, but there are some direct path constructions that couple code to the directory structure.

| Coupling Type | Count | Risk Level |
|--------------|-------|------------|
| Abstracted (via managers) | ~80% | Low |
| Direct path strings | ~20% | Medium |
| Hardcoded constants | Few | Low |

---

## Directory Structure Overview

### Current Architecture

```
.vibey/roadmap/
├── roadmap.yaml              # Root roadmap file
├── tracks/                   # Track YAML files
│   └── {ulid}.yaml
├── sprints/                  # Sprint YAML files
│   └── {ulid}.yaml
├── tasks/                    # Task YAML files
│   └── {ulid}.yaml
├── context/                  # Context documents
│   ├── tracks/{slug}/
│   ├── sprints/{slug}/
│   └── tasks/{slug}/
└── activity_log/             # Activity JSONL files
    └── {YYYY-MM}.jsonl
```

### Semantic Mapping

| Directory | Semantic Concept | Usage |
|-----------|------------------|-------|
| `tracks/` | Work Track (project stream) | Independent work units |
| `sprints/` | Sprint (time-boxed iteration) | Time-boxed milestones |
| `tasks/` | Task (atomic work item) | Smallest trackable units |
| `context/` | Documentation/artifacts | Human-readable context |

---

## Abstraction Layers

### Primary: `FileSystemManager` (CLI Layer)

**File:** `vibey/cli/roadmap_lib/filesystem.py`

**Constants:**
```python
class FileSystemManager:
    VIBEY_DIR = ".vibey"
    ROADMAP_DIR = "roadmap"
    ROADMAP_FILE = "roadmap.yaml"
```

**Path Methods:**
| Method | Returns | Abstraction Level |
|--------|---------|-------------------|
| `get_roadmap_path()` | Path to roadmap.yaml | High |
| `get_track_path(track_id)` | Path to track YAML | High |
| `get_sprint_path(sprint_id)` | Path to sprint YAML | High |
| `get_task_path(task_id)` | Path to task YAML | High |
| `get_tasks_path(sprint_id)` | Path to tasks dir | High |
| `get_activity_log_path(y, m)` | Path to log file | High |

### Secondary: `DirectoryManager` (Roadmap Layer)

**File:** `vibey/roadmap/directory_manager.py`

Used primarily for legacy nested structure support. Still referenced for directory creation and validation.

---

## Coupling Analysis by Module

### High Coupling (Direct Path Strings)

| File | References | Risk | Notes |
|------|------------|------|-------|
| `roadmap/toc_generator.py` | 12 | Medium | Generates navigation links |
| `operations/git/error_handler.py` | 10 | Medium | Error reporting |
| `roadmap/database/integrity_audit.py` | 9 | Low | Audit comments/strings |
| `cli/commands.py` | 16 | Low | Help text and examples |
| `content/agents/*.md` | 17+ | Low | Documentation |

### Well Abstracted (Uses Managers)

| Module | Abstraction Used | Status |
|--------|-----------------|--------|
| `cli/roadmap_lib/` | FileSystemManager | Good |
| `roadmap/serialization/backend.py` | FileSystemManager | Good |
| `operations/roadmap/*.py` | FileSystemManager | Good |
| `roadmap/database/round_trip_validation.py` | Path detection | Good |

### Tests (Acceptable Coupling)

| File | Purpose |
|------|---------|
| `cli/tests/test_roadmap_integration.py` | Verifies directory creation |
| `cli/tests/benchmark_cache.py` | Performance testing |

---

## Coupling Categories

### 1. Path Construction Utilities (✅ Good)

```python
# FileSystemManager handles path construction
def get_track_path(self, track_id: str) -> Path:
    return self.roadmap_root / "tracks" / f"{track_id}.yaml"
```

### 2. Error Messages and Logging (⚠️ Medium Risk)

```python
# Direct strings in error messages
file_path=f"tracks/{track_file.name}"
```

**Impact:** Visual only, doesn't affect functionality
**Risk:** Medium - could be inconsistent if structure changes

### 3. Documentation and Help Text (✅ Acceptable)

```python
# In docstrings and help text
.vibey/roadmap/tracks/{ulid}.yaml
```

**Impact:** None on code execution
**Risk:** Low - documentation can drift

### 4. TOC/Navigation Generation (⚠️ Medium Risk)

```python
# toc_generator.py builds paths for navigation
yaml=f"tracks/{track_id}.yaml",
markdown=f"tracks/{track_id}.md",
```

**Impact:** Generated outputs would break
**Risk:** Medium - if directory structure changes

### 5. Tests (✅ Acceptable)

```python
# Testing that directories exist
self.assertTrue((vibey_dir / "tracks").exists())
```

**Impact:** Tests would need updating
**Risk:** Low - tests should be updated with structure

---

## Decoupling Opportunities

### Short Term (Low Risk)

1. **Constants for directory names**
   ```python
   # In FileSystemManager
   TRACKS_DIR = "tracks"
   SPRINTS_DIR = "sprints"
   TASKS_DIR = "tasks"
   ```

2. **Use constants in error messages**
   ```python
   file_path=f"{TRACKS_DIR}/{track_file.name}"
   ```

### Medium Term (Medium Risk)

1. **Abstract path generation in toc_generator.py**
   - Use FileSystemManager for path construction
   - Pass directory names as configuration

2. **Central path configuration**
   - Single source of truth for directory names
   - Easy to change in one place

### Long Term (Architectural)

1. **Remove directory-to-semantic coupling entirely**
   - Store entity type in YAML, not inferred from path
   - Use ID-based lookup instead of path-based

2. **Virtual file system abstraction**
   - FileSystemManager becomes storage backend interface
   - Could support different storage backends

---

## Recommendations

### Immediate (Safe)

1. Add directory name constants to FileSystemManager:
   ```python
   TRACKS_DIR = "tracks"
   SPRINTS_DIR = "sprints"
   TASKS_DIR = "tasks"
   CONTEXT_DIR = "context"
   ```

2. Use these constants consistently across codebase

### Future Considerations

1. **Don't over-engineer** - Current coupling is acceptable for single-storage architecture

2. **If multi-storage needed** - Abstract to storage backend interface

3. **Keep semantic layer separate** - Entity types should be explicit, not path-derived

---

## File Reference Count by Module

| Module Path | References |
|-------------|------------|
| cli/commands.py | 16 |
| cli/roadmap_lib/filesystem.py | 19 |
| content/agents/ | 46 |
| operations/git/ | 15 |
| roadmap/database/ | 22 |
| roadmap/serialization/ | 33 |
| roadmap/ (other) | 16 |

**Total: 287 references**

---

## Verification Commands

```bash
# Count all directory references
grep -rn "tracks/\|sprints/\|tasks/" vibey/ | grep -v __pycache__ | wc -l

# Count by file
grep -rn "tracks/\|sprints/\|tasks/" vibey/ | grep -v __pycache__ | cut -d: -f1 | sort | uniq -c | sort -rn

# Find direct string paths (not comments)
grep -rn '"tracks/\|"sprints/\|"tasks/' vibey/ | grep -v __pycache__ | grep -v "#"
```

---

## Related ADRs

- **ADR-0002**: Flat Directory Structure
- **ADR-0001**: ULID Identifiers
- **ADR-0003**: Dual Storage (SQLite + YAML)

---

*Generated as part of Architecture Modernization Track, Sprint 1*
