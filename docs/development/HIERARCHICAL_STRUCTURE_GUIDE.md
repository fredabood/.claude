# Hierarchical Documentation Structure Guide

**Created**: 2025-11-09
**Sprint**: documentation-system-1
**Task**: documentation-system-1-task-007
**Status**: Production Ready

## Overview

The Vibey Agent Framework uses a hierarchical directory structure to organize roadmap data, documentation, and context. This guide explains the structure, conventions, and usage patterns.

## Table of Contents

1. [Directory Structure](#directory-structure)
2. [File Naming Conventions](#file-naming-conventions)
3. [ID System (ULID-based)](#id-system-ulid-based)
4. [Table of Contents (JSON)](#table-of-contents-json)
5. [Context Directories](#context-directories)
6. [CLI Commands](#cli-commands)
7. [Migration from Flat Structure](#migration-from-flat-structure)
8. [Best Practices](#best-practices)

---

## Directory Structure

### Complete Hierarchy

```
.vibey/
├── roadmap.yaml                      # Master roadmap (source of truth)
├── roadmap/                          # Hierarchical structure root
│   ├── table_of_contents.json       # Roadmap-level navigation
│   ├── roadmap.md                   # Generated roadmap view
│   │
│   └── {track-slug}/                # Track directory
│       ├── .id                      # Track ULID (immutable)
│       ├── track.yaml               # Track definition (source)
│       ├── track.md                 # Generated track view
│       ├── table_of_contents.json   # Track-level navigation
│       │
│       ├── context/                 # Track-level research
│       │   ├── design.md
│       │   ├── architecture.md
│       │   └── implementation-plan.md
│       │
│       └── {sprint-slug}/           # Sprint directory
│           ├── .id                  # Sprint ULID (immutable)
│           ├── sprint.yaml          # Sprint definition (source)
│           ├── sprint.md            # Generated sprint view
│           ├── table_of_contents.json  # Sprint-level navigation
│           │
│           ├── context/             # Sprint-level research
│           │   ├── planning.md
│           │   └── design.md
│           │
│           └── {task-slug}/         # Task directory
│               ├── .id              # Task ULID (immutable)
│               ├── task.yaml        # Task definition (source)
│               ├── task.md          # Generated task view
│               │
│               └── context/         # Task execution artifacts
│                   ├── analysis.md
│                   ├── research.md
│                   └── decisions.md
```

### Example: documentation-system Track

```
.vibey/roadmap/
└── documentation-system/
    ├── .id → track_01JB3QVDZ8TRK9XN1FJFHGWPRM
    ├── track.yaml
    ├── track.md
    ├── table_of_contents.json
    ├── context/
    │   └── design.md
    │
    ├── documentation-system-1/
    │   ├── .id → sprint_01JB3QVE2CTYPXM2NKQR5HWVJT
    │   ├── sprint.yaml
    │   ├── sprint.md
    │   ├── table_of_contents.json
    │   ├── context/
    │   │
    │   ├── documentation-system-1-task-000/
    │   │   ├── .id → task_01JB3QVEKR9XPWJ4VFZN8TGYHM
    │   │   ├── task.yaml
    │   │   └── context/
    │   │
    │   └── documentation-system-1-task-001/
    │       ├── .id → task_01JB3QVEMN5RTZCW8KPHX7YBQA
    │       ├── task.yaml
    │       └── context/
    │
    └── documentation-system-2/
        └── ...
```

---

## File Naming Conventions

### Slugs (Directory Names)

**Format**: `lowercase-with-hyphens`

**Rules**:
- Lowercase letters and numbers only
- Hyphens for separation (no underscores, spaces)
- Must start with letter or number (not hyphen)
- Cannot end with hyphen
- No consecutive hyphens (`--`)
- Maximum 100 characters

**Valid Examples**:
```
documentation-system
core-framework-2
task-001
sprint-1
my-awesome-feature
```

**Invalid Examples**:
```
Documentation-System  ❌ (uppercase)
core_framework        ❌ (underscore)
-task-001             ❌ (starts with hyphen)
task-001-             ❌ (ends with hyphen)
task--001             ❌ (consecutive hyphens)
```

### File Names

| File | Purpose | Format |
|------|---------|--------|
| `.id` | Immutable ULID reference | Plain text, one line |
| `track.yaml` | Track source data | YAML with `track:` root |
| `sprint.yaml` | Sprint source data | YAML with `sprint:` root |
| `task.yaml` | Task source data | YAML with `task:` root |
| `table_of_contents.json` | Navigation manifest | JSON |
| `*.md` | Generated markdown views | Markdown |

---

## ID System (ULID-based)

### ULID Format

**Structure**: `{type}_{ulid}`

Examples:
```
track_01JB3QVDZ8TRK9XN1FJFHGWPRM
sprint_01JB3QVE2CTYPXM2NKQR5HWVJT
task_01JB3QVEKR9XPWJ4VFZN8TGYHM
```

### ULID Properties

1. **Immutable**: Never changes, even if directory is renamed
2. **Sortable**: Lexicographically sorted by creation time
3. **Unique**: Collision-free (128-bit entropy)
4. **Timestamped**: Encodes creation time in first 48 bits
5. **URL-safe**: No special characters

### Hybrid Approach

The system uses **both** IDs and slugs:

- **IDs** (in `.id` files): Immutable references for data integrity
- **Slugs** (directory names): Human-readable for browsing

**Benefits**:
- Stable references across renames
- Browse-friendly directory structure
- Fast ID-based lookups
- Human-readable organization

### ID Generation

```python
from framework.roadmap.id_generator import (
    generate_track_id,
    generate_sprint_id,
    generate_task_id,
    extract_timestamp,
)

# Generate IDs
track_id = generate_track_id()      # track_01JB3QV...
sprint_id = generate_sprint_id()    # sprint_01JB3QV...
task_id = generate_task_id()        # task_01JB3QV...

# Extract creation time
timestamp = extract_timestamp(track_id)  # datetime object
print(timestamp)  # 2025-11-09 14:30:45+00:00
```

### ID Validation

The `.id` file ensures slug ↔ ID mapping integrity:

```python
from framework.roadmap.directory_manager import DirectoryManager

dm = DirectoryManager()

# Validate directory has correct ID
is_valid = dm.validate_directory(track_dir, expected_id)

# Find directory by ID
track_dir = dm.find_directory_by_id("track_01JB3QV...")
```

---

## Table of Contents (JSON)

Each level (roadmap, track, sprint) has a `table_of_contents.json` file for programmatic navigation.

### Roadmap TOC

```json
{
  "object_type": "roadmap",
  "object_id": "vibey-framework-v2",
  "parent": null,
  "current": {
    "id": "vibey-framework-v2",
    "name": "Vibey Multi-Platform Agent Framework",
    "status": "in_progress",
    "progress": {
      "tracks_total": 11,
      "tracks_completed": 3,
      "completion_percent": 27
    }
  },
  "children": [
    {
      "id": "core-framework",
      "slug": "core-framework",
      "name": "Core Framework Enhancements",
      "type": "track",
      "status": "completed"
    },
    {
      "id": "documentation-system",
      "slug": "documentation-system",
      "name": "Hierarchical Documentation System",
      "type": "track",
      "status": "in_progress"
    }
  ],
  "metadata": {
    "generated_at": "2025-11-09T22:30:00Z",
    "generator_version": "1.0.0"
  }
}
```

### Track TOC

```json
{
  "object_type": "track",
  "object_id": "documentation-system",
  "parent": {
    "id": "vibey-framework-v2",
    "type": "roadmap",
    "name": "Vibey Multi-Platform Agent Framework"
  },
  "current": {
    "id": "documentation-system",
    "name": "Hierarchical Documentation System",
    "status": "in_progress",
    "progress": {
      "sprints_total": 3,
      "sprints_completed": 1,
      "completion_percent": 33
    }
  },
  "children": [
    {
      "id": "documentation-system-1",
      "slug": "documentation-system-1",
      "name": "Hierarchical Structure & Core Generation",
      "type": "sprint",
      "status": "production_ready"
    }
  ]
}
```

### Sprint TOC

```json
{
  "object_type": "sprint",
  "object_id": "documentation-system-1",
  "parent": {
    "id": "documentation-system",
    "type": "track",
    "name": "Hierarchical Documentation System"
  },
  "current": {
    "id": "documentation-system-1",
    "name": "Hierarchical Structure & Core Generation",
    "status": "production_ready",
    "progress": {
      "tasks_total": 8,
      "tasks_completed": 7,
      "completion_percent": 87
    }
  },
  "children": [
    {
      "id": "documentation-system-1-task-000",
      "slug": "documentation-system-1-task-000",
      "title": "Implement ULID-based ID generation",
      "type": "task",
      "status": "completed"
    }
  ]
}
```

### TOC Generation

```python
from framework.roadmap.toc_generator import TOCGenerator

toc_gen = TOCGenerator()

# Generate TOCs
toc_gen.generate_roadmap_toc()
toc_gen.generate_track_toc("documentation-system")
toc_gen.generate_sprint_toc("documentation-system", "documentation-system-1")
```

---

## Context Directories

Each level has a `/context/` directory for storing related documentation, research, and artifacts.

### Context Organization

```
{level}/context/
├── {filename}.md       # Context files (flat structure)
├── {filename}.json     # Data artifacts
└── {filename}.png      # Diagrams, screenshots
```

**Important**: Context directories are **flat** (no subdirectories).

### Context at Each Level

#### Track-Level Context

**Purpose**: Strategic analyses, architectural decisions affecting entire track

**Examples**:
```
.vibey/roadmap/documentation-system/context/
├── design.md                    # Design specification
├── architecture.md              # Architectural decisions
├── implementation-plan.md       # Implementation strategy
└── requirements.md              # Requirements analysis
```

#### Sprint-Level Context

**Purpose**: Sprint planning, sprint-wide design decisions

**Examples**:
```
.vibey/roadmap/documentation-system/documentation-system-1/context/
├── planning.md                  # Sprint planning notes
├── design.md                    # Sprint design decisions
├── blockers.md                  # Blockers and resolutions
└── retrospective.md             # Sprint retrospective
```

#### Task-Level Context

**Purpose**: Task execution artifacts, research findings, technical decisions

**Examples**:
```
.vibey/roadmap/.../task-001/context/
├── analysis.md                  # Problem analysis
├── research.md                  # Research findings
├── decisions.md                 # Technical decisions
├── api-design.json              # API contracts
└── architecture-diagram.png     # Architecture diagrams
```

### Context Management

```python
from framework.roadmap.directory_manager import DirectoryManager

dm = DirectoryManager()

# Context directories created automatically
track_dir = dm.create_track_directory(
    track_id="track_01...",
    slug="my-track",
    create_context=True  # Creates context/ directory
)

# Access context directories
track_context = track_dir / "context"
sprint_context = sprint_dir / "context"
task_context = task_dir / "context"
```

---

## CLI Commands

### Directory Management

```bash
# Create track (Python API)
python3 -c "
from framework.roadmap.directory_manager import DirectoryManager
from framework.roadmap.id_generator import generate_track_id

dm = DirectoryManager()
track_id = generate_track_id()
dm.create_track_directory(track_id, 'my-track')
"

# List tracks
python3 -c "
from framework.roadmap.directory_manager import DirectoryManager
dm = DirectoryManager()
tracks = dm.list_tracks()
for slug, track_id in tracks:
    print(f'{slug}: {track_id}')
"

# Find directory by ID
python3 -c "
from framework.roadmap.directory_manager import DirectoryManager
dm = DirectoryManager()
dir = dm.find_directory_by_id('track_01JB...')
print(dir)
"
```

### TOC Generation

```bash
# Generate all TOCs
python3 -c "
from framework.roadmap.toc_generator import TOCGenerator
toc = TOCGenerator()
toc.generate_roadmap_toc()
"

# Generate track TOC
python3 -c "
from framework.roadmap.toc_generator import TOCGenerator
toc = TOCGenerator()
toc.generate_track_toc('documentation-system')
"
```

### Roadmap State Management

```bash
# Query roadmap
python3 framework/scripts/roadmap-query.py --track documentation-system

# Update task status
python3 framework/scripts/roadmap-update.py \
  --complete-task documentation-system-1-task-007

# Start task
python3 framework/scripts/roadmap-update.py \
  --start-task documentation-system-1-task-006
```

---

## Migration from Flat Structure

### Old Structure (Deprecated)

```
.vibey/
├── roadmap.yaml
├── tracks/
│   ├── core-framework.yaml
│   └── documentation-system.yaml
├── sprints/
│   ├── core-framework-1.yaml
│   └── documentation-system-1.yaml
└── tasks/
    ├── core-framework-1-tasks.yaml
    └── documentation-system-1-tasks.yaml
```

### New Structure

```
.vibey/
├── roadmap.yaml
└── roadmap/
    ├── core-framework/
    │   ├── track.yaml
    │   └── core-framework-1/
    │       ├── sprint.yaml
    │       └── task-001/
    │           └── task.yaml
    └── documentation-system/
        └── ...
```

### Migration Script

```bash
# Dry run (preview changes)
python3 framework/scripts/migrate-to-hierarchical.py

# Execute migration
python3 framework/scripts/migrate-to-hierarchical.py --execute

# Verify migration
python3 framework/scripts/validate-roadmap-format.py
```

### Backward Compatibility

The FileSystemManager, cache, and serialization layers support **both formats** during the transition:

- `load_tasks()`: Detects directory vs file, loads accordingly
- `save_tasks()`: Saves to hierarchical structure when path is a directory
- `get_tasks_path()`: Returns directory for hierarchical, file for legacy

This allows gradual migration without breaking existing scripts.

---

## Best Practices

### 1. Use IDs for References

**Do**:
```yaml
dependencies:
  - type: task
    target_id: documentation-system-1-task-001  # ✅ Use ID
```

**Don't**:
```yaml
dependencies:
  - type: task
    target_id: ../task-001  # ❌ Don't use paths
```

### 2. Keep Context Flat

**Do**:
```
context/
├── design.md
├── api-spec.json
└── diagram.png
```

**Don't**:
```
context/
└── designs/          # ❌ No subdirectories
    └── v1/
        └── design.md
```

### 3. Use Descriptive Slugs

**Do**:
```
hierarchical-structure-implementation
ulid-id-generation
context-directory-management
```

**Don't**:
```
task1
impl
x
```

### 4. Commit Generated Files

All generated files (`.md`, `.json`) should be committed to git:
- Enables GitHub browsing without build step
- Preserves history
- No additional tooling required

### 5. Validate Regularly

```bash
# Run validation after changes
python3 framework/scripts/validate-roadmap-format.py

# Run tests
python3 -m framework.roadmap.test_hierarchical_integration
```

### 6. Use TOC for Navigation

Instead of hardcoding paths, use `table_of_contents.json`:

```python
import json

# Load TOC
with open('.vibey/roadmap/track/table_of_contents.json') as f:
    toc = json.load(f)

# Navigate programmatically
for child in toc['children']:
    print(f"Sprint: {child['name']} ({child['status']})")
```

---

## Examples

### Create New Track

```python
from framework.roadmap.directory_manager import DirectoryManager
from framework.roadmap.id_generator import generate_track_id
from framework.roadmap.toc_generator import TOCGenerator

# Initialize managers
dm = DirectoryManager()
toc_gen = TOCGenerator()

# Generate ID
track_id = generate_track_id()

# Create directory
track_dir = dm.create_track_directory(
    track_id=track_id,
    slug="my-awesome-feature",
    create_context=True
)

# Create track.yaml (manually or via save_track())
# ...

# Generate TOC
toc_gen.generate_track_toc("my-awesome-feature")

print(f"Created track: {track_dir}")
print(f"Track ID: {track_id}")
```

### Load Task Context Hierarchically

```python
from pathlib import Path

def load_task_context(track_slug, sprint_slug, task_slug):
    """Load context from task, sprint, and track levels."""
    base = Path(".vibey/roadmap")

    contexts = []

    # Task-level context
    task_context = base / track_slug / sprint_slug / task_slug / "context"
    if task_context.exists():
        for file in task_context.glob("*.md"):
            contexts.append(file.read_text())

    # Sprint-level context
    sprint_context = base / track_slug / sprint_slug / "context"
    if sprint_context.exists():
        for file in sprint_context.glob("*.md"):
            contexts.append(file.read_text())

    # Track-level context
    track_context = base / track_slug / "context"
    if track_context.exists():
        for file in track_context.glob("*.md"):
            contexts.append(file.read_text())

    return "\n\n---\n\n".join(contexts)

# Usage
context = load_task_context(
    "documentation-system",
    "documentation-system-1",
    "documentation-system-1-task-001"
)
print(context)
```

---

## FAQ

### Q: Can I rename directories?

**A**: Yes, but update the slug references. The ID in `.id` file remains unchanged, ensuring data integrity.

### Q: What if `.id` file is missing?

**A**: The DirectoryManager will raise a `ValueError`. Always create directories using `create_*_directory()` methods.

### Q: Can I manually create directories?

**A**: Not recommended. Use DirectoryManager to ensure `.id` files and structure are correct.

### Q: How do I migrate from legacy structure?

**A**: Use `migrate-to-hierarchical.py`. It creates backups and validates the migration.

### Q: Are subdirectories allowed in context/?

**A**: No. Context directories must be flat. Use descriptive filenames instead.

### Q: Can I use uppercase in slugs?

**A**: No. Slugs must be lowercase. Use hyphens for word separation.

---

## Summary

The hierarchical structure provides:

✅ **Scalability**: Naturally scales to 100+ tracks
✅ **Discoverability**: Related docs co-located
✅ **Immutability**: ULID IDs never change
✅ **Human-Readable**: Slug-based directory names
✅ **Context Management**: Hierarchical context loading
✅ **Programmatic Access**: JSON TOCs for navigation
✅ **Git-Friendly**: All files committed, no build step

---

**Last Updated**: 2025-11-09
**Version**: 1.0.0
**Maintainer**: Vibey Framework Team
