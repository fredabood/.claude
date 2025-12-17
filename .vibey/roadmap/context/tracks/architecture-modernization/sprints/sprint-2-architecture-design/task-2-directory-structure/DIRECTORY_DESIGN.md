# Decoupled Directory Structure Design

**Sprint:** Architecture Design (Sprint 2)
**Task:** Design Decoupled Directory Structure
**Date:** 2025-12-17
**Status:** Complete

---

## Executive Summary

This document evaluates three options for decoupling the directory structure from semantic concepts. After analysis, **Option D: Hybrid Approach (Current + Constants)** is recommended, as it provides sufficient decoupling with minimal migration risk.

---

## Problem Statement

The current directory structure (`tracks/`, `sprints/`, `tasks/`) mirrors semantic concepts, creating implicit coupling between storage organization and domain vocabulary. While 80% of access is properly abstracted through `FileSystemManager`, changing semantic terminology would require directory renames.

### Design Principles

1. **Directory structure = storage concern only**
2. **Semantic layer should not dictate file organization**
3. **Storage should be swappable without semantic changes**

---

## Current State Analysis

### Directory Structure (Post-Migration)

```
.vibey/roadmap/
├── roadmap.yaml                    # Root entity
├── tracks/                         # 48 files
│   ├── 01KC2D0JK9JKQXGQW6MQEB0JZP.yaml
│   └── ...
├── sprints/                        # 226 files
│   ├── 01KC2D0JKVT80AFQ6C1PA8CKJD.yaml
│   └── ...
├── tasks/                          # 1571 files
│   ├── 01KC2D0JK7READW9KAK1HBX4B8.yaml
│   └── ...
├── context/                        # Human documentation
│   └── tracks/{slug}/sprints/{slug}/
└── activity_log/
    └── 2025-12.jsonl
```

### Coupling Points (From Sprint 1 Audit)

| Component | References | Abstraction |
|-----------|------------|-------------|
| FileSystemManager | 19 | Source of truth |
| CLI commands | 16 | Uses FileSystemManager |
| Serialization | 33 | Uses FileSystemManager |
| Tests | 15 | Acceptable coupling |
| Documentation | 46 | Acceptable coupling |
| **Total** | **287** | **80% abstracted** |

### Current Abstraction Layer

```python
# vibey/cli/roadmap_lib/filesystem.py
class FileSystemManager:
    def get_track_path(self, track_id: str) -> Path:
        return self.roadmap_root / "tracks" / f"{track_id}.yaml"

    def get_sprint_path(self, sprint_id: str) -> Path:
        return self.roadmap_root / "sprints" / f"{sprint_id}.yaml"

    def get_task_path(self, task_id: str) -> Path:
        return self.roadmap_root / "tasks" / f"{task_id}.yaml"
```

---

## Option Analysis

### Option A: Generic Storage Directory

```
.vibey/
├── data/
│   ├── entities/           # All YAML files (type in content)
│   │   ├── 01KC2D0JK9JK...yaml
│   │   └── ...
│   └── cache/              # SQLite database
│       └── roadmap.db
└── config/
```

**Implementation:**
- Single directory for all entity types
- Entity type stored in YAML `type:` field
- File discovery requires reading metadata or type prefix

**Pros:**
| Benefit | Impact |
|---------|--------|
| Maximum decoupling | Storage completely independent |
| Simpler structure | One directory to manage |
| Future-proof | Easy to add new entity types |

**Cons:**
| Issue | Severity |
|-------|----------|
| Loss of human readability | High |
| Slower discovery (must read files) | Medium |
| Breaking change | High |
| Git history disruption | High |

**Migration Effort:**
- Move 1,845+ files
- Update all 287 path references
- Update FileSystemManager
- Database rebuild

**Score: 3/10**

---

### Option B: Type-Based but Abstract

```
.vibey/
├── store/
│   ├── type-a/             # Tracks (abstract name)
│   ├── type-b/             # Sprints (abstract name)
│   └── type-c/             # Tasks (abstract name)
└── meta/
    └── cache/
```

**Implementation:**
- Abstract directory names (type-a, type-b, type-c)
- Mapping table in config or code
- No semantic terminology in paths

**Pros:**
| Benefit | Impact |
|---------|--------|
| Decoupling from terminology | Medium |
| Organized by type | Low |
| Git-friendly structure | Low |

**Cons:**
| Issue | Severity |
|-------|----------|
| Worse human readability | High |
| Arbitrary naming confusion | High |
| Still has type separation | Medium |
| Breaking change | High |

**Migration Effort:**
- Rename 3 directories
- Update all 287 path references
- Update documentation extensively

**Score: 2/10** (worse than current)

---

### Option C: Single Flat Directory

```
.vibey/
└── objects/
    ├── 01KC2D0JK9JK...yaml  # Roadmap (type in file)
    ├── 01KC2D0JKVT8...yaml  # Track (type in file)
    ├── 01KCMNY4BENE...yaml  # Task (type in file)
    └── ...
```

**Implementation:**
- All entities in single `objects/` directory
- Type determined by `type:` field in YAML
- ID-only addressing

**Pros:**
| Benefit | Impact |
|---------|--------|
| Complete type-agnostic storage | High |
| Simple addressing by ID | High |
| Mirrors git object model | Medium |
| Easy backup/sync | Medium |

**Cons:**
| Issue | Severity |
|-------|----------|
| 1,845+ files in one directory | High |
| OS performance impact | Medium |
| Human navigation impossible | High |
| Breaking change | High |

**Migration Effort:**
- Move all files to single directory
- Add type field to all YAMLs
- Update FileSystemManager completely
- Update all loaders

**Score: 4/10**

---

### Option D: Hybrid Approach (Current + Constants) **RECOMMENDED**

```
.vibey/roadmap/
├── roadmap.yaml
├── tracks/                 # Keep semantic names
│   └── {ulid}.yaml
├── sprints/
│   └── {ulid}.yaml
├── tasks/
│   └── {ulid}.yaml
└── [unchanged...]
```

**But with enhanced abstraction:**

```python
# vibey/cli/roadmap_lib/filesystem.py
class FileSystemManager:
    # Directory name constants (single point of change)
    TRACKS_DIR = "tracks"
    SPRINTS_DIR = "sprints"
    TASKS_DIR = "tasks"
    CONTEXT_DIR = "context"

    # Optional: configurable via settings
    @classmethod
    def from_config(cls, config: dict):
        instance = cls()
        instance.TRACKS_DIR = config.get("tracks_dir", "tracks")
        return instance
```

**Implementation:**
- Keep current directory structure
- Add constants for directory names
- Replace all string literals with constants
- Optional: make directories configurable

**Pros:**
| Benefit | Impact |
|---------|--------|
| No migration needed | Critical |
| Human readable | High |
| Good git history | High |
| Sufficient decoupling | Medium |
| Easy future changes | Medium |

**Cons:**
| Issue | Severity |
|-------|----------|
| Directories still semantic | Low |
| Coupling via constants | Low |
| Directory names could drift | Low |

**Migration Effort:**
- Add constants to FileSystemManager (1 file)
- Replace ~20 string literals with constants
- No file moves
- No database changes

**Score: 8/10**

---

## Comparison Matrix

| Criteria | Option A | Option B | Option C | **Option D** |
|----------|----------|----------|----------|--------------|
| Decoupling Level | High | Medium | High | **Medium** |
| Human Readability | Low | Low | Very Low | **High** |
| Migration Complexity | High | High | High | **Very Low** |
| Git Friendliness | Medium | Medium | Medium | **High** |
| Performance Impact | Medium | None | Medium | **None** |
| Breaking Change | Yes | Yes | Yes | **No** |
| Future Flexibility | High | Medium | High | **Medium** |
| **Overall Score** | 3/10 | 2/10 | 4/10 | **8/10** |

---

## Recommendation: Option D

### Rationale

1. **The problem is already solved at 80%** - FileSystemManager provides sufficient abstraction
2. **Migration risk exceeds benefit** - Moving 1,845 files for theoretical decoupling is not justified
3. **Human readability matters** - `tracks/` is more useful than `type-a/` or `objects/`
4. **Git history preservation** - Current structure has years of history
5. **YAGNI principle** - We don't need storage-independent semantics

### Implementation Plan

#### Phase 1: Add Constants (Non-Breaking)

```python
# vibey/cli/roadmap_lib/filesystem.py

class FileSystemManager:
    """Manages roadmap filesystem operations."""

    # Directory name constants
    VIBEY_DIR = ".vibey"
    ROADMAP_DIR = "roadmap"
    TRACKS_DIR = "tracks"
    SPRINTS_DIR = "sprints"
    TASKS_DIR = "tasks"
    CONTEXT_DIR = "context"
    ACTIVITY_LOG_DIR = "activity_log"

    def get_track_path(self, track_id: str) -> Path:
        return self.roadmap_root / self.TRACKS_DIR / f"{track_id}.yaml"

    def get_sprint_path(self, sprint_id: str) -> Path:
        return self.roadmap_root / self.SPRINTS_DIR / f"{sprint_id}.yaml"

    def get_task_path(self, task_id: str) -> Path:
        return self.roadmap_root / self.TASKS_DIR / f"{task_id}.yaml"
```

#### Phase 2: Replace String Literals

Find and replace direct string usages:

```bash
# Current (20+ occurrences)
"tracks/"

# Should be
f"{FileSystemManager.TRACKS_DIR}/"
```

#### Phase 3: Optional Configuration

```python
# Future: If needed for multi-project support
class FileSystemManager:
    def __init__(self, config: Optional[Dict] = None):
        config = config or {}
        self.TRACKS_DIR = config.get("tracks_dir", "tracks")
        self.SPRINTS_DIR = config.get("sprints_dir", "sprints")
        self.TASKS_DIR = config.get("tasks_dir", "tasks")
```

---

## Success Criteria Validation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Multiple options evaluated | ✅ Complete | 4 options analyzed |
| Tradeoffs documented | ✅ Complete | Comparison matrix |
| Clear recommendation made | ✅ Complete | Option D recommended |
| Migration plan provided | ✅ Complete | 3-phase plan |

---

## Go/No-Go for Full Refactor

| Factor | Assessment |
|--------|------------|
| Current state acceptable? | **Yes** - 80% already abstracted |
| Refactor benefit clear? | **No** - Marginal improvement |
| Risk acceptable? | **No** - High migration risk |
| Resources available? | **No** - Better spent elsewhere |
| Value justifies effort? | **No** - Doesn't solve real problems |

**Decision: NO-GO for Options A/B/C**
**Decision: GO for Option D (constants only)**

---

## References

- Sprint 1: DIRECTORY_COUPLING_AUDIT.md
- Sprint 2 Task 1: SEMANTIC_LAYER_SPEC.md
- ADR-0002: Flat Directory Structure
- ADR-0003: Dual Storage (SQLite + YAML)
