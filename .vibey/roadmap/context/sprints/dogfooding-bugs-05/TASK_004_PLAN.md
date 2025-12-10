# Task 004: Update create-from-plan to Use ULID Flat Structure

**Task ID:** dogfooding-bugs-05-task-004
**Bug Addressed:** #15 (No CLI Commands to Create Tracks, Sprints, or Tasks in ULID Structure)
**Complexity:** High
**Type:** Development

---

## Problem Statement

The existing `create-from-plan` command uses `DirectoryManager` which creates hierarchical nested directory structures:
```
.vibey/roadmap/{track-slug}/{sprint-slug}/
├── sprint.yaml
├── {task-slug}/
│   └── task.yaml
```

This is incompatible with the new ULID-based flat structure:
```
.vibey/roadmap/
├── tracks/{ulid}.yaml
├── sprints/{ulid}.yaml
└── tasks/{ulid}.yaml
```

---

## Current Implementation Analysis

**File:** `vibey/cli/roadmap_create_from_plan.py`

```python
# Line 28 - Uses DirectoryManager (hierarchical only)
from vibey.roadmap.directory_manager import DirectoryManager

# Line 237 - Creates hierarchical structure
dir_manager = DirectoryManager(str(roadmap_root))

# Line 241 - Creates nested sprint directory
sprint_dir = dir_manager.create_sprint_directory(
    track_slug=track_id,
    sprint_id=sprint_id,
    sprint_slug=sprint_id,
    create_context=True
)

# Line 283 - Creates sprint.yaml in nested directory
sprint_yaml = sprint_dir / "sprint.yaml"

# Line 317 - Saves tasks to sprint directory
save_tasks(task_objects, sprint_dir)
```

---

## Implementation

### Strategy: Refactor to Use FileSystemManager

Replace `DirectoryManager` with `FileSystemManager` which supports both structures.

### Updated Implementation

```python
# vibey/cli/roadmap_create_from_plan.py

#!/usr/bin/env python3
"""
Create Roadmap Sprint from Plan - ULID Flat Structure Edition

Parses a sprint plan markdown file and creates:
- Sprint YAML in flat ULID structure
- Task YAMLs in flat ULID structure
- Updates track to reference the sprint

Usage:
    roadmap-create-from-plan.py --plan sprint-plan.md --track track_01JB3...
    roadmap-create-from-plan.py --plan sprint-plan.md --track my-track --start
"""

import sys
import re
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# Add framework to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

from vibey.roadmap.models import (
    Sprint, SprintProgress, SprintMetadata, SprintSummary,
    Task, TaskMetadata, TaskSummary, TaskStatus, TaskType,
    Priority, Complexity
)
from vibey.roadmap.serialization import (
    save_sprint, save_task, load_track, save_track
)
from vibey.roadmap.id_generator import generate_sprint_id, generate_task_id
from vibey.cli.roadmap_lib.filesystem import FileSystemManager


class SprintPlanParser:
    """Parse sprint plan markdown to extract structure."""
    # ... (unchanged - keep existing parser implementation)


def create_sprint_from_plan(
    plan_path: Path,
    track_id_or_slug: str,
    sprint_name: Optional[str] = None,
    start: bool = False,
    dry_run: bool = False
) -> bool:
    """
    Create sprint and tasks from plan file using ULID flat structure.

    Args:
        plan_path: Path to sprint plan markdown
        track_id_or_slug: Track ID (ULID) or slug to add sprint to
        sprint_name: Override sprint name from plan
        start: Mark sprint as started
        dry_run: Show what would be created without creating

    Returns:
        Success status
    """
    if not plan_path.exists():
        print(f"❌ Plan file not found: {plan_path}")
        return False

    print(f"📋 Parsing sprint plan: {plan_path}")

    # Parse plan
    parser = SprintPlanParser(plan_path)
    metadata = parser.parse_metadata()
    tasks = parser.parse_tasks()

    # Find repository root
    root = Path.cwd()
    while root != root.parent:
        if (root / ".vibey").exists():
            break
        root = root.parent
    else:
        print("❌ No .vibey/ directory found in current or parent directories")
        return False

    # Initialize FileSystemManager (supports flat structure)
    fs = FileSystemManager(root)

    # Resolve track
    track_id, track = _resolve_track(fs, track_id_or_slug)
    if not track:
        print(f"❌ Track not found: {track_id_or_slug}")
        return False

    # Generate sprint ID (ULID format)
    sprint_id = generate_sprint_id()

    # Use sprint name from argument or metadata
    sprint_name = sprint_name or metadata.get('name', f"Sprint {len(track.sprints) + 1}")

    print(f"\n📊 Sprint: {sprint_name}")
    print(f"   ID: {sprint_id}")
    print(f"   Track: {track.name} ({track_id})")
    print(f"   Tasks: {len(tasks)}")

    if dry_run:
        print("\n🔍 DRY RUN - Tasks to be created:")
        for i, task in enumerate(tasks, 1):
            print(f"   {i}. {task['title']}")
        return True

    # Create sprint object
    now = datetime.now(timezone.utc)
    sprint_data = Sprint(
        id=sprint_id,
        name=sprint_name,
        track_id=track_id,
        roadmap_id=track.roadmap_id,
        status=TaskStatus.IN_PROGRESS if start else TaskStatus.NOT_STARTED,
        blocked=False,
        created=now,
        progress=SprintProgress(
            development_tasks_total=len(tasks),
            development_tasks_completed=0,
            completion_gate_tasks_total=0,
            completion_gate_tasks_completed=0,
            production_gate_tasks_total=0,
            production_gate_tasks_completed=0,
            tasks_total=len(tasks),
            tasks_completed=0,
            completion_percent=0,
        ),
        tasks=[],  # Will be populated with TaskSummaries
        development_gates=[],
        blocks=[],
        blocked_by=[],
        depends_on=[],
        depended_on_by=[],
        metadata=SprintMetadata(
            last_updated=now,
            estimated_duration=metadata.get('estimated_duration', '2 weeks'),
        ),
        started=now if start else None,
        plan_file=str(plan_path),
    )

    # Save sprint YAML file (flat structure)
    sprint_path = fs.roadmap_root / "sprints" / f"{sprint_id}.yaml"
    save_sprint(sprint_data, sprint_path)
    print(f"✓ Created: {sprint_path.relative_to(root)}")

    # Create task objects with ULID IDs
    print(f"\n📝 Creating {len(tasks)} tasks...")
    task_summaries = []

    for task_data in tasks:
        task_now = datetime.now(timezone.utc)
        task_id = generate_task_id()  # ULID for each task

        task = Task(
            id=task_id,
            sprint_id=sprint_id,
            track_id=track_id,
            roadmap_id=track.roadmap_id,
            task_type=TaskType.DEVELOPMENT,
            title=task_data['title'],
            description=task_data.get('description', ''),
            status=TaskStatus.NOT_STARTED,
            blocked=False,
            created=task_now,
            assigned_agent=task_data.get('assigned_agent', 'backend-engineer'),
            priority=Priority(task_data.get('priority', 'medium')),
            complexity=Complexity(task_data.get('complexity', 'medium')),
            estimated_tokens=task_data.get('estimated_tokens', 5000),
            dependencies=[],
            blocks=[],
            blocked_by=[],
            depends_on=[],
            depended_on_by=[],
            metadata=TaskMetadata(last_updated=task_now),
        )

        # Save task to flat structure
        task_path = fs.roadmap_root / "tasks" / f"{task_id}.yaml"
        save_task(task, task_path)

        # Add task summary for sprint
        task_summaries.append(TaskSummary(
            id=task_id,
            title=task.title,
            status=task.status,
            task_type=task.task_type,
            priority=task.priority,
        ))

    print(f"✓ Created {len(tasks)} task files in .vibey/roadmap/tasks/")

    # Update sprint with task summaries
    sprint_data.tasks = task_summaries
    save_sprint(sprint_data, sprint_path)

    # Update track with sprint reference
    sprint_summary = SprintSummary(
        id=sprint_id,
        name=sprint_name,
        status=sprint_data.status,
        priority=Priority(metadata.get('priority', 'medium')),
    )
    track.sprints.append(sprint_summary)
    track.progress.sprints_total += 1
    track.progress.tasks_total += len(tasks)

    track_path = fs.roadmap_root / "tracks" / f"{track_id}.yaml"
    save_track(track, track_path)
    print(f"✓ Updated track: {track_path.relative_to(root)}")

    print(f"\n✅ Sprint {sprint_name} created successfully!")
    print(f"   Sprint: {sprint_path.relative_to(root)}")
    print(f"   Tasks: {len(tasks)}")

    if start:
        print(f"   Status: Started")

    return True


def _resolve_track(fs, track_id_or_slug):
    """Resolve track by ID or slug."""
    from vibey.roadmap.serialization import load_track

    # First, try as direct ULID
    if track_id_or_slug.startswith('track_'):
        track_path = fs.roadmap_root / "tracks" / f"{track_id_or_slug}.yaml"
        if track_path.exists():
            return track_id_or_slug, load_track(track_path)

    # Search by slug or name
    tracks_dir = fs.roadmap_root / "tracks"
    for track_file in tracks_dir.glob("*.yaml"):
        try:
            track = load_track(track_file)
            if (hasattr(track, 'slug') and track.slug == track_id_or_slug) or \
               track.name.lower() == track_id_or_slug.lower():
                return track.id, track
        except Exception:
            continue

    return None, None


def main():
    parser = argparse.ArgumentParser(
        description='Create roadmap sprint from plan file (ULID flat structure)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--plan',
        required=True,
        help='Path to sprint plan markdown file'
    )

    parser.add_argument(
        '--track',
        required=True,
        help='Track ID (ULID) or slug to add sprint to'
    )

    parser.add_argument(
        '--name',
        help='Override sprint name (uses name from plan if not specified)'
    )

    parser.add_argument(
        '--start',
        action='store_true',
        help='Mark sprint as started'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be created without creating'
    )

    args = parser.parse_args()

    plan_path = Path(args.plan)
    success = create_sprint_from_plan(
        plan_path=plan_path,
        track_id_or_slug=args.track,
        sprint_name=args.name,
        start=args.start,
        dry_run=args.dry_run
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
```

---

## Key Changes

| Old (DirectoryManager) | New (FileSystemManager) |
|------------------------|-------------------------|
| `DirectoryManager` import | `FileSystemManager` import |
| `sprint_id` from plan | `generate_sprint_id()` ULID |
| `task['id']` from plan | `generate_task_id()` ULID |
| Nested `{track}/{sprint}/sprint.yaml` | Flat `sprints/{ulid}.yaml` |
| Nested `{track}/{sprint}/{task}/task.yaml` | Flat `tasks/{ulid}.yaml` |
| `save_tasks(tasks, sprint_dir)` | Individual `save_task(task, path)` |
| No track update | Update track with sprint summary |

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/roadmap_create_from_plan.py` | Replace DirectoryManager, use ULIDs |
| `vibey/cli/main.py` | Update command help text (optional) |

---

## Migration Considerations

### Backward Compatibility

The old hierarchical structure is no longer supported in this command. Users who need hierarchical structure should use the legacy version or manually create files.

### Plan File Format

The plan file format remains unchanged. The only difference is:
- Old: Task IDs specified in plan are used directly
- New: Task IDs in plan are ignored; ULIDs are generated

---

## Testing Strategy

```python
def test_create_from_plan_flat_structure(flat_roadmap_env, tmp_path):
    """create-from-plan uses flat ULID structure."""
    # Create plan file
    plan_content = '''
# Sprint Plan: Test Sprint

**Sprint Name:** Test Sprint
**Track:** test-track
**Duration:** 1 week

## Tasks

#### Task 1: Implement feature
**ID:** task-001
**Priority:** high
**Estimated:** 4 hours
**Agents:** backend-engineer

**Description:**
Implement the feature.

#### Task 2: Add tests
**ID:** task-002
**Priority:** medium
**Estimated:** 2 hours
**Agents:** qa-engineer

**Description:**
Add unit tests.
'''
    plan_file = tmp_path / "sprint-plan.md"
    plan_file.write_text(plan_content)

    # Create track first
    runner = CliRunner()
    runner.invoke(cli, ['roadmap', 'create-track', '-n', 'test-track'])

    # Run create-from-plan
    result = runner.invoke(cli, [
        'roadmap', 'create-from-plan',
        '--plan', str(plan_file),
        '--track', 'test-track',
    ])

    assert result.exit_code == 0

    # Verify flat structure used
    sprints_dir = flat_roadmap_env / ".vibey" / "roadmap" / "sprints"
    tasks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tasks"

    sprint_files = list(sprints_dir.glob("sprint_*.yaml"))
    task_files = list(tasks_dir.glob("task_*.yaml"))

    assert len(sprint_files) == 1
    assert len(task_files) == 2

    # Verify ULIDs used (not plan IDs)
    assert "task-001" not in [f.stem for f in task_files]
    assert all(f.stem.startswith("task_") for f in task_files)


def test_create_from_plan_updates_track(flat_roadmap_env, tmp_path):
    """create-from-plan updates track with sprint reference."""
    # Setup plan and track
    plan_file = tmp_path / "sprint-plan.md"
    plan_file.write_text("# Sprint\n**Sprint Name:** S1\n## Tasks\n#### Task 1: T\n**ID:** t1")

    runner = CliRunner()
    runner.invoke(cli, ['roadmap', 'create-track', '-n', 'test-track'])

    # Create sprint from plan
    runner.invoke(cli, [
        'roadmap', 'create-from-plan',
        '--plan', str(plan_file),
        '--track', 'test-track',
    ])

    # Verify track updated
    tracks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tracks"
    track_file = list(tracks_dir.glob("track_*.yaml"))[0]
    track = load_track(track_file)

    assert len(track.sprints) == 1
    assert track.sprints[0].name == "S1"
    assert track.progress.sprints_total == 1
```

---

## Success Criteria

- [ ] create-from-plan creates files in flat structure
- [ ] Sprint YAML at `.vibey/roadmap/sprints/{ulid}.yaml`
- [ ] Task YAMLs at `.vibey/roadmap/tasks/{ulid}.yaml`
- [ ] ULID IDs generated (ignores plan IDs)
- [ ] Track updated with sprint summary
- [ ] Track progress counters updated
- [ ] No nested directories created
- [ ] Existing plan file format still works

---

## Dependencies

- Task 001 (create track) - For track resolution
- Task 005 (ULIDManager) - Already exists in id_generator.py

---

## Notes

This is the highest complexity task because it requires:
1. Understanding existing SprintPlanParser
2. Replacing directory structure paradigm
3. Updating ID generation strategy
4. Ensuring track linkage works
5. Maintaining plan file compatibility
