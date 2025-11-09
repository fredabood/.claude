# Hierarchical Structure - Quick Reference

**Last Updated**: 2025-11-09

## Directory Structure

```
.vibey/roadmap/
└── {track-slug}/              # e.g., documentation-system/
    ├── .id                    # Track ULID
    ├── track.yaml             # Source data
    ├── table_of_contents.json # Navigation
    ├── context/               # Track research
    │
    └── {sprint-slug}/         # e.g., documentation-system-1/
        ├── .id                # Sprint ULID
        ├── sprint.yaml        # Source data
        ├── table_of_contents.json
        ├── context/           # Sprint research
        │
        └── {task-slug}/       # e.g., task-001/
            ├── .id            # Task ULID
            ├── task.yaml      # Source data
            └── context/       # Task artifacts
```

## ULID Format

```
track_01JB3QVDZ8TRK9XN1FJFHGWPRM
sprint_01JB3QVE2CTYPXM2NKQR5HWVJT
task_01JB3QVEKR9XPWJ4VFZN8TGYHM
```

- **Immutable**: Never changes
- **Sortable**: By creation time
- **Unique**: 128-bit collision-free
- **Timestamped**: Encodes creation time

## Slug Rules

Format: `lowercase-with-hyphens`

✅ Valid: `my-awesome-feature`, `task-001`, `sprint-1`
❌ Invalid: `My_Feature`, `-task`, `task-`, `task--001`

## Common Operations

### Create Track

```python
from framework.roadmap.directory_manager import DirectoryManager
from framework.roadmap.id_generator import generate_track_id

dm = DirectoryManager()
track_id = generate_track_id()
dm.create_track_directory(track_id, "my-track", create_context=True)
```

### List Tracks

```python
dm = DirectoryManager()
tracks = dm.list_tracks()
for slug, track_id in tracks:
    print(f"{slug}: {track_id}")
```

### Find by ID

```python
dm = DirectoryManager()
dir = dm.find_directory_by_id("track_01JB3QV...")
print(dir)  # Path to directory
```

### Generate TOC

```python
from framework.roadmap.toc_generator import TOCGenerator
toc = TOCGenerator()
toc.generate_track_toc("my-track")
```

### Load Task Context

```python
from pathlib import Path
base = Path(".vibey/roadmap")

# Task context
task_ctx = base / "track" / "sprint" / "task" / "context"
for file in task_ctx.glob("*.md"):
    print(file.read_text())

# Sprint context
sprint_ctx = base / "track" / "sprint" / "context"

# Track context
track_ctx = base / "track" / "context"
```

## File Types

| File | Purpose | Committed |
|------|---------|-----------|
| `.id` | Immutable ID reference | ✅ Yes |
| `*.yaml` | Source data (track/sprint/task) | ✅ Yes |
| `*.md` | Generated views | ✅ Yes |
| `*.json` | TOC navigation | ✅ Yes |
| `context/*` | Research, artifacts | ✅ Yes |

## CLI Commands

```bash
# Migrate from flat to hierarchical
python3 framework/scripts/migrate-to-hierarchical.py --execute

# Validate structure
python3 framework/scripts/validate-roadmap-format.py

# Update task status
python3 framework/scripts/roadmap-update.py --complete-task task-id

# Query roadmap
python3 framework/scripts/roadmap-query.py --track track-id
```

## Test Suite

```bash
# Run all tests (82 tests total)
python3 -m framework.roadmap.test_id_generator          # 29 tests
python3 -m framework.roadmap.test_toc_generator         # 16 tests
python3 -m framework.roadmap.test_directory_manager     # 25 tests
python3 -m framework.roadmap.test_hierarchical_integration  # 12 tests
```

## Context Organization

### Track Level
- Design specifications
- Architectural decisions
- Implementation plans

### Sprint Level
- Sprint planning
- Sprint-wide designs
- Retrospectives

### Task Level
- Analysis & research
- Technical decisions
- Execution artifacts
- API contracts
- Diagrams

## Migration

```bash
# Backup created automatically at:
.vibey/hierarchical-migration-backups/backup_TIMESTAMP/

# Legacy structure (deprecated):
.vibey/tracks/*.yaml
.vibey/sprints/*.yaml
.vibey/tasks/*-tasks.yaml

# New structure:
.vibey/roadmap/{track}/{sprint}/{task}/
```

## Best Practices

1. ✅ Use IDs for references (not paths)
2. ✅ Keep context directories flat (no subdirectories)
3. ✅ Use descriptive slugs
4. ✅ Commit generated files (.md, .json)
5. ✅ Validate after changes
6. ✅ Use TOC for programmatic navigation

## For Full Details

See: [HIERARCHICAL_STRUCTURE_GUIDE.md](./HIERARCHICAL_STRUCTURE_GUIDE.md)
