"""
Command implementations for vibey CLI.

This module provides Python API for all CLI commands using direct function imports
from the operations modules (no subprocess calls).
"""

from pathlib import Path
from typing import Optional

# Import operations modules
from vibey.operations.roadmap import (
    init_roadmap,
    query_roadmap_summary,
    query_track_details,
    query_sprint_details,
    query_task_details,
    start_task,
    start_sprint,
    complete_task,
    complete_sprint,
    complete_track,
    get_task_context,
    validate_roadmap,
    add_commit_to_task,
    get_current_commit,
)
from vibey.operations.roadmap.summarize import summarize_sprint, summarize_task
from vibey.operations.deployment import deploy_framework
from vibey.operations.docs import generate_docs
from vibey.operations.config import generate_config, update_config_value
from vibey.operations.migrations import (
    migrate_to_roadmap,
    migrate_embedded_tasks,
)

# Import formatters for CLI output
from vibey.cli.formatters import (
    format_roadmap_summary,
    format_track_details,
    format_sprint_details,
    format_task_details,
    format_success,
    format_error,
)


# ============================================================================
# Roadmap Commands
# ============================================================================

def roadmap_init_cmd(name: str, version: str) -> int:
    """Initialize a new roadmap."""
    root_dir = Path.cwd()  # Project root
    return init_roadmap(
        root_dir=root_dir,  # init_roadmap expects project root (adds .vibey/ internally)
        roadmap_id=name or "default-roadmap",
        roadmap_name=name or "Default Roadmap",
        version=version or "1.0.0",
    )


def roadmap_status_cmd(track: Optional[str] = None, sprint: Optional[str] = None) -> int:
    """Show roadmap status."""
    root_dir = Path.cwd()  # Project root

    try:
        if sprint:
            result = query_sprint_details(root_dir, sprint)
            print(format_sprint_details(result))
        elif track:
            result = query_track_details(root_dir, track)
            print(format_track_details(result))
        else:
            result = query_roadmap_summary(root_dir)
            print(format_roadmap_summary(result))
        return 0
    except Exception as e:
        print(format_error(str(e)))
        return 1


def roadmap_sync_cmd(verbose: bool = False) -> int:
    """Sync status from individual files to main roadmap.yaml."""
    root_dir = Path.cwd()

    try:
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager
        from vibey.operations.roadmap.update import _update_roadmap_progress
        from vibey.roadmap.serialization.yaml_loader import load_roadmap, load_track

        fs = FileSystemManager(root_dir)
        roadmap_path = fs.get_roadmap_path()

        if not roadmap_path.exists():
            print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
            return 1

        print("🔄 Syncing roadmap status...")

        # Load roadmap to get track list
        roadmap = load_roadmap(roadmap_path)

        # Import update functions (file has hyphen, use importlib)
        import importlib
        roadmap_update = importlib.import_module('vibey.cli.roadmap-update')
        update_sprint_progress = getattr(roadmap_update, 'update_sprint_progress', None)
        update_track_progress = getattr(roadmap_update, 'update_track_progress', None)

        # Step 1: Update each sprint's progress from task files
        if update_sprint_progress:
            for track_summary in roadmap.tracks:
                track_path = fs.get_track_path(track_summary.id)
                if not track_path.exists():
                    continue
                try:
                    track = load_track(track_path)
                    for sprint_summary in track.sprints:
                        if verbose:
                            print(f"  Updating sprint: {sprint_summary.id}")
                        update_sprint_progress(fs, sprint_summary.id)
                except Exception as e:
                    if verbose:
                        print(f"  ⚠️  Error loading track {track_summary.id}: {e}")

        # Step 2: Update each track's progress from sprint files
        if update_track_progress:
            for track_summary in roadmap.tracks:
                if verbose:
                    print(f"  Updating track: {track_summary.id}")
                update_track_progress(fs, track_summary.id)

        # Step 3: Update roadmap progress from track files
        if verbose:
            print("  Updating roadmap progress...")
        _update_roadmap_progress(fs)

        print("✅ Roadmap synced successfully")

        if verbose:
            # Show summary of what was synced
            from vibey.operations.roadmap.query import query_roadmap_summary
            from vibey.cli.formatters import format_roadmap_summary
            result = query_roadmap_summary(root_dir)
            print("\nCurrent status:")
            print(format_roadmap_summary(result))

        return 0
    except Exception as e:
        print(format_error(str(e)))
        return 1


def _slugify(name: str) -> str:
    """Convert a name to a URL-friendly slug."""
    import re
    # Lowercase, replace spaces with hyphens, remove non-alphanumeric
    slug = name.lower().strip()
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug)  # Collapse multiple hyphens
    return slug.strip('-')


def _resolve_id(item_type: str, id_or_slug: str, root_dir: Path) -> str:
    """Resolve a slug or ULID to a ULID for the given item type."""
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager

    # If it looks like a ULID (26 chars, alphanumeric), return as-is
    if len(id_or_slug) == 26 and id_or_slug.isalnum() and id_or_slug.isupper():
        return id_or_slug

    # Otherwise, look up in .id file
    fs = FileSystemManager(root_dir)
    roadmap_root = fs.roadmap_root

    type_to_dir = {"track": "tracks", "sprint": "sprints", "task": "tasks"}
    id_file = roadmap_root / type_to_dir[item_type] / ".id"

    if id_file.exists():
        for line in id_file.read_text().strip().split("\n"):
            if "=" in line:
                slug, ulid = line.split("=", 1)
                if slug == id_or_slug:
                    return ulid

    # Not found, return as-is (will fail later if invalid)
    return id_or_slug


def _get_roadmap_id(root_dir: Path) -> str:
    """Get the roadmap ID from the roadmap.yaml file."""
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager
    from vibey.roadmap.serialization.yaml_loader import load_roadmap

    fs = FileSystemManager(root_dir)
    roadmap_path = fs.get_roadmap_path()

    if not roadmap_path.exists():
        raise FileNotFoundError("Roadmap not found. Run 'vibey roadmap init' first.")

    roadmap = load_roadmap(roadmap_path)
    return roadmap.id


def _update_id_mapping(item_type: str, slug: str, ulid: str, root_dir: Path):
    """Add a slug=ULID mapping to the .id file."""
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager

    fs = FileSystemManager(root_dir)
    roadmap_root = fs.roadmap_root

    type_to_dir = {"track": "tracks", "sprint": "sprints", "task": "tasks"}
    id_file = roadmap_root / type_to_dir[item_type] / ".id"

    # Read existing content
    if id_file.exists():
        content = id_file.read_text()
        if not content.endswith("\n"):
            content += "\n"
    else:
        content = ""

    # Add new mapping
    content += f"{slug}={ulid}\n"
    id_file.write_text(content)


def create_track_cmd(name: str, slug: str | None, description: str,
                     priority: str, start: bool) -> int:
    """Create a new track."""
    from datetime import datetime, timezone
    from ulid import ULID
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager
    from vibey.roadmap.models.track import Track, TrackProgress, TrackMetadata
    from vibey.roadmap.models.common import Status, Priority
    from vibey.roadmap.serialization.yaml_dumper import save_track

    root_dir = Path.cwd()

    try:
        # Get roadmap ID
        roadmap_id = _get_roadmap_id(root_dir)

        # Generate ULID and slug
        ulid = str(ULID())
        if not slug:
            slug = _slugify(name)

        # Create filesystem manager
        fs = FileSystemManager(root_dir)

        # Determine status and timestamps
        now = datetime.now(timezone.utc)
        status = Status.IN_PROGRESS if start else Status.NOT_STARTED
        started = now if start else None

        # Create track object
        track = Track(
            id=ulid,
            name=name,
            roadmap_id=roadmap_id,
            status=status,
            blocked=False,
            priority=Priority(priority),
            created=now,
            started=started,
            progress=TrackProgress(
                sprints_total=0,
                sprints_completed=0,
                tasks_total=0,
                tasks_completed=0,
                completion_percent=0
            ),
            sprints=[],
            dependencies=[],
            blocks=[],
            blocked_by=[],
            depends_on=[],
            depended_on_by=[],
            quality_gates=[],
            assigned_agents=[],
            metadata=TrackMetadata(
                created_by="vibey-cli",
                last_updated=now,
                notes=description if description else None
            )
        )

        # Save track YAML
        tracks_dir = fs.roadmap_root / "tracks"
        tracks_dir.mkdir(parents=True, exist_ok=True)
        track_path = tracks_dir / f"{ulid}.yaml"
        save_track(track, track_path)

        # Update .id mapping
        _update_id_mapping("track", slug, ulid, root_dir)

        # Update roadmap.yaml track list
        _add_track_to_roadmap(fs, ulid, name, slug)

        # Rebuild database to sync
        try:
            from vibey.cli.commands import db_rebuild_cmd
            db_rebuild_cmd(force=True)
        except Exception:
            pass  # Database rebuild is optional

        print(f"✅ Created track: {name}")
        print(f"   ID: {ulid}")
        print(f"   Slug: {slug}")
        print(f"   File: {track_path.relative_to(root_dir)}")

        return 0
    except Exception as e:
        print(format_error(f"Failed to create track: {e}"))
        return 1


def _add_track_to_roadmap(fs, track_id: str, track_name: str, track_slug: str):
    """Add a track reference to roadmap.yaml."""
    import yaml
    from vibey.roadmap.models.common import Status

    roadmap_path = fs.get_roadmap_path()

    # Read current roadmap
    with open(roadmap_path, 'r') as f:
        data = yaml.safe_load(f)

    # Add track to tracks list
    if 'roadmap' not in data:
        data['roadmap'] = {}

    if 'tracks' not in data['roadmap']:
        data['roadmap']['tracks'] = []

    # Create track summary entry
    track_entry = {
        'id': track_id,
        'name': track_name,
        'status': Status.NOT_STARTED.value,
        'sprints_total': 0,
        'tasks_total': 0,
        'completion_percent': 0
    }

    data['roadmap']['tracks'].append(track_entry)

    # Update track counts
    data['roadmap']['tracks_total'] = len(data['roadmap']['tracks'])

    # Write back
    with open(roadmap_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def create_sprint_cmd(track_id: str, name: str, goal: str,
                      description: str, start: bool) -> int:
    """Create a new sprint in a track."""
    from datetime import datetime, timezone
    from ulid import ULID
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager
    from vibey.roadmap.models.sprint import Sprint, SprintProgress, SprintMetadata
    from vibey.roadmap.models.common import Status
    from vibey.roadmap.serialization.yaml_dumper import save_sprint

    root_dir = Path.cwd()

    try:
        # Get roadmap ID
        roadmap_id = _get_roadmap_id(root_dir)

        # Resolve track ID
        resolved_track_id = _resolve_id("track", track_id, root_dir)

        # Generate ULID
        ulid = str(ULID())

        # Create filesystem manager
        fs = FileSystemManager(root_dir)

        # Get track info to determine sequence number
        track_path = fs.roadmap_root / "tracks" / f"{resolved_track_id}.yaml"
        if not track_path.exists():
            # Try slug-based lookup
            raise FileNotFoundError(f"Track not found: {track_id}")

        # Load track to get sprint count
        from vibey.roadmap.serialization.yaml_loader import load_track
        track = load_track(track_path)
        sequence = len(track.sprints) + 1

        # Generate slug
        track_slug = _get_slug_for_ulid("track", resolved_track_id, root_dir)
        sprint_slug = f"{track_slug}-{sequence:02d}" if track_slug else f"sprint-{sequence:02d}"

        # Determine status and timestamps
        now = datetime.now(timezone.utc)
        status = Status.IN_PROGRESS if start else Status.NOT_STARTED
        started = now if start else None

        # Create sprint object
        sprint = Sprint(
            id=ulid,
            name=name,
            track_id=track_slug or resolved_track_id,  # Use slug if available
            roadmap_id=roadmap_id,
            status=status,
            blocked=False,
            created=now,
            progress=SprintProgress(
                development_tasks_total=0,
                development_tasks_completed=0,
                completion_gate_tasks_total=0,
                completion_gate_tasks_completed=0,
                production_gate_tasks_total=0,
                production_gate_tasks_completed=0,
                tasks_total=0,
                tasks_completed=0,
                completion_percent=0
            ),
            tasks=[],
            development_gates=[],
            blocks=[],
            blocked_by=[],
            depends_on=[],
            depended_on_by=[],
            metadata=SprintMetadata(last_updated=now),
            started=started,
            description=description if description else None,
            goal=goal if goal else None,
            deliverables=[],
        )

        # Save sprint YAML
        sprints_dir = fs.roadmap_root / "sprints"
        sprints_dir.mkdir(parents=True, exist_ok=True)
        sprint_path = sprints_dir / f"{ulid}.yaml"
        save_sprint(sprint, sprint_path)

        # Update .id mapping
        _update_id_mapping("sprint", sprint_slug, ulid, root_dir)

        # Update track's sprint list
        _add_sprint_to_track(fs, resolved_track_id, ulid, name, sprint_slug)

        # Rebuild database to sync
        try:
            from vibey.cli.commands import db_rebuild_cmd
            db_rebuild_cmd(force=True)
        except Exception:
            pass  # Database rebuild is optional

        print(f"✅ Created sprint: {name}")
        print(f"   ID: {ulid}")
        print(f"   Slug: {sprint_slug}")
        print(f"   Track: {track_id}")
        print(f"   File: {sprint_path.relative_to(root_dir)}")

        return 0
    except Exception as e:
        print(format_error(f"Failed to create sprint: {e}"))
        return 1


def _get_slug_for_ulid(item_type: str, ulid: str, root_dir: Path) -> str | None:
    """Get the slug for a given ULID from .id file."""
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager

    fs = FileSystemManager(root_dir)
    roadmap_root = fs.roadmap_root

    type_to_dir = {"track": "tracks", "sprint": "sprints", "task": "tasks"}
    id_file = roadmap_root / type_to_dir[item_type] / ".id"

    if id_file.exists():
        for line in id_file.read_text().strip().split("\n"):
            if "=" in line:
                slug, file_ulid = line.split("=", 1)
                if file_ulid == ulid:
                    return slug
    return None


def _add_sprint_to_track(fs, track_ulid: str, sprint_ulid: str, sprint_name: str, sprint_slug: str):
    """Add a sprint reference to the track YAML file."""
    import yaml
    from vibey.roadmap.models.common import Status

    track_path = fs.roadmap_root / "tracks" / f"{track_ulid}.yaml"

    # Read current track
    with open(track_path, 'r') as f:
        data = yaml.safe_load(f)

    # Add sprint to sprints list
    if 'track' not in data:
        data['track'] = {}

    if 'sprints' not in data['track']:
        data['track']['sprints'] = []

    # Create sprint summary entry
    sprint_entry = {
        'id': sprint_slug,
        'name': sprint_name,
        'status': Status.NOT_STARTED.value,
        'tasks_count': 0
    }

    data['track']['sprints'].append(sprint_entry)

    # Update progress counts
    if 'progress' not in data['track']:
        data['track']['progress'] = {}
    data['track']['progress']['sprints_total'] = len(data['track']['sprints'])

    # Write back
    with open(track_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def create_task_cmd(sprint_id: str, title: str, description: str,
                    task_type: str, priority: str, complexity: str) -> int:
    """Create a new task in a sprint."""
    from datetime import datetime, timezone
    from ulid import ULID
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager
    from vibey.roadmap.models.task import Task, TaskMetadata
    from vibey.roadmap.models.common import Priority, TaskType, Complexity, TaskStatus
    from vibey.roadmap.serialization.yaml_dumper import save_task

    root_dir = Path.cwd()

    try:
        # Get roadmap ID
        roadmap_id = _get_roadmap_id(root_dir)

        # Resolve sprint ID
        resolved_sprint_id = _resolve_id("sprint", sprint_id, root_dir)

        # Generate ULID
        ulid = str(ULID())

        # Create filesystem manager
        fs = FileSystemManager(root_dir)

        # Get sprint info to determine sequence and track
        sprint_path = fs.roadmap_root / "sprints" / f"{resolved_sprint_id}.yaml"
        if not sprint_path.exists():
            raise FileNotFoundError(f"Sprint not found: {sprint_id}")

        # Load sprint to get track info
        from vibey.roadmap.serialization.yaml_loader import load_sprint
        sprint = load_sprint(sprint_path)
        track_id = sprint.track_id

        # Count tasks from standalone files for sequence number
        tasks_dir = fs.roadmap_root / "tasks"
        task_count = 0
        if tasks_dir.exists():
            import yaml as yaml_mod
            for task_file in tasks_dir.glob("*.yaml"):
                try:
                    with open(task_file, 'r') as tf:
                        task_data = yaml_mod.safe_load(tf)
                    task_info = task_data.get('task', {})
                    if task_info.get('sprint_id') == resolved_sprint_id:
                        task_count += 1
                except Exception:
                    continue
        sequence = task_count + 1

        # Generate slug (Sprint model doesn't have a slug attribute, so we look it up)
        sprint_slug = _get_slug_for_ulid("sprint", resolved_sprint_id, root_dir)
        task_slug = f"{sprint_slug}-task-{sequence:03d}" if sprint_slug else f"task-{sequence:03d}"

        # Determine timestamp
        now = datetime.now(timezone.utc)

        # Create task object
        task = Task(
            id=ulid,
            sprint_id=sprint_slug or resolved_sprint_id,
            track_id=track_id,
            roadmap_id=roadmap_id,
            task_type=TaskType(task_type),
            title=title,
            description=description if description else "",
            status=TaskStatus.NOT_STARTED,
            blocked=False,
            created=now,
            assigned_agent="unassigned",
            priority=Priority(priority),
            estimated_tokens=1,
            complexity=Complexity(complexity),
            dependencies=[],
            blocks=[],
            blocked_by=[],
            depends_on=[],
            depended_on_by=[],
            metadata=TaskMetadata(last_updated=now),
        )

        # Save task YAML
        tasks_dir = fs.roadmap_root / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)
        task_path = tasks_dir / f"{ulid}.yaml"
        save_task(task, task_path)

        # Update .id mapping
        _update_id_mapping("task", task_slug, ulid, root_dir)

        # Update sprint's task list
        _add_task_to_sprint(fs, resolved_sprint_id, ulid, title, task_slug)

        # Rebuild database to sync
        try:
            from vibey.cli.commands import db_rebuild_cmd
            db_rebuild_cmd(force=True)
        except Exception:
            pass  # Database rebuild is optional

        print(f"✅ Created task: {title}")
        print(f"   ID: {ulid}")
        print(f"   Slug: {task_slug}")
        print(f"   Sprint: {sprint_id}")
        print(f"   File: {task_path.relative_to(root_dir)}")

        return 0
    except Exception as e:
        print(format_error(f"Failed to create task: {e}"))
        return 1


def _add_task_to_sprint(fs, sprint_ulid: str, task_ulid: str, task_title: str, task_slug: str):
    """Update sprint progress after adding a task (standalone file).

    NOTE: Tasks are stored as standalone files in tasks/{ulid}.yaml.
    This function only updates the sprint's progress count.
    Embedded tasks in sprint.tasks[] arrays are DEPRECATED.
    """
    import yaml

    sprint_path = fs.roadmap_root / "sprints" / f"{sprint_ulid}.yaml"

    # Read current sprint
    with open(sprint_path, 'r') as f:
        data = yaml.safe_load(f)

    if 'sprint' not in data:
        data['sprint'] = {}

    # Count standalone tasks for this sprint
    tasks_dir = fs.roadmap_root / "tasks"
    task_count = 0
    if tasks_dir.exists():
        for task_file in tasks_dir.glob("*.yaml"):
            try:
                with open(task_file, 'r') as f:
                    task_data = yaml.safe_load(f)
                task_info = task_data.get('task', {})
                if task_info.get('sprint_id') == sprint_ulid:
                    task_count += 1
            except Exception:
                continue

    # Update progress counts (do NOT add embedded tasks array)
    if 'progress' not in data['sprint']:
        data['sprint']['progress'] = {}
    data['sprint']['progress']['tasks_total'] = task_count
    data['sprint']['progress']['development_tasks_total'] = task_count

    # Write back
    with open(sprint_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def _detect_ulid_type(item_id: str, root_dir: Path) -> str | None:
    """
    Detect item type from ULID by checking .id files.

    Returns: "track", "sprint", "task", or None if not found
    """
    roadmap_root = root_dir / ".vibey" / "roadmap"

    # Check each type's .id file for the ULID
    for item_type, subdir in [("task", "tasks"), ("sprint", "sprints"), ("track", "tracks")]:
        id_file = roadmap_root / subdir / ".id"
        if id_file.exists():
            content = id_file.read_text()
            # Check if ULID appears as a value (slug=ULID format)
            if f"={item_id}" in content or f"={item_id}\n" in content:
                return item_type

    return None


def roadmap_show_cmd(item_id: str) -> int:
    """Show details for an item."""
    root_dir = Path.cwd()  # Project root

    try:
        # Determine type from ID format
        item_type = None

        # Check for slug-based IDs first
        if 'task' in item_id:
            item_type = "task"
        elif item_id.count('-') >= 2:  # sprint format: track-sprint
            item_type = "sprint"
        elif '-' in item_id:  # might be a track slug
            item_type = "track"

        # For ULID IDs (no hyphens, 26 chars), look up type from .id files
        if item_type is None and len(item_id) == 26 and item_id.isalnum():
            item_type = _detect_ulid_type(item_id, root_dir)
            if item_type is None:
                # Default to track for ULIDs not found in .id files
                item_type = "track"
        elif item_type is None:
            # Default fallback
            item_type = "track"

        # Query based on detected type
        if item_type == "task":
            result = query_task_details(root_dir, item_id)
        elif item_type == "sprint":
            result = query_sprint_details(root_dir, item_id)
        else:
            result = query_track_details(root_dir, item_id)

        # Check if query returned an error
        if "error" in result:
            print(format_error(result["error"]))
            return 1

        # Format and print the result based on type
        if item_type == "task":
            print(format_task_details(result))
        elif item_type == "sprint":
            print(format_sprint_details(result))
        else:
            print(format_track_details(result))
        return 0
    except Exception as e:
        print(format_error(str(e)))
        return 1


def roadmap_start_cmd(item_id: str) -> int:
    """Start a sprint or task."""
    root_dir = Path.cwd()  # Project root

    if 'task' in item_id:
        return start_task(root_dir, item_id)
    elif 'sprint' in item_id or item_id.count('-') >= 1:
        return start_sprint(root_dir, item_id)
    else:
        print(f"Error: Cannot determine item type from ID: {item_id}")
        print("Expected format: <track>-<sprint>-task-<num> or <track>-<sprint>[-name]")
        return 1


def roadmap_complete_cmd(item_id: str, skip_commit_check: bool = False) -> int:
    """Complete a track, sprint, or task."""
    root_dir = Path.cwd()  # Project root

    # Task IDs contain '-task-'
    if '-task-' in item_id:
        return complete_task(root_dir, item_id, skip_commit_check=skip_commit_check)

    # Check if it's a sprint (ends with -N where N is a number)
    # Sprint format: track-name-N (e.g., platform-context-management-5)
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager
    fs = FileSystemManager(root_dir)

    # Try sprint first (more specific pattern)
    sprint_path = fs.get_sprint_path(item_id)
    if sprint_path.exists():
        return complete_sprint(root_dir, item_id)

    # Try track
    track_path = fs.get_track_path(item_id)
    if track_path.exists():
        return complete_track(root_dir, item_id)

    # Neither found
    print(f"Error: Cannot find track or sprint with ID: {item_id}")
    print("Expected format:")
    print("  Track:  <track-name> (e.g., platform-context-management)")
    print("  Sprint: <track-name>-<num> (e.g., platform-context-management-5)")
    print("  Task:   <sprint-id>-task-<num> (e.g., platform-context-management-5-task-001)")
    return 1


def roadmap_context_cmd(task_id: str) -> int:
    """Get context for a task."""
    return get_task_context(task_id=task_id, root_dir=Path.cwd())


def roadmap_summarize_cmd(item_type: str, item_id: str) -> int:
    """Summarize an item."""
    root_dir = Path.cwd()  # Project root

    # Determine type from ID format
    if 'task' in item_id:
        # Extract sprint_id from task_id (format: track-sprint-task-NNN)
        parts = item_id.split('-task-')
        if len(parts) != 2:
            print(f"Error: Invalid task ID format: {item_id}")
            return 1
        sprint_id = parts[0]
        return summarize_task(sprint_id=sprint_id, task_id=item_id, root_dir=root_dir)
    else:
        return summarize_sprint(sprint_id=item_id, root_dir=root_dir)


def roadmap_list_cmd() -> int:
    """List all tracks/sprints/tasks."""
    root_dir = Path.cwd()  # Project root

    try:
        result = query_roadmap_summary(root_dir)
        print(format_roadmap_summary(result))
        return 0
    except Exception as e:
        print(format_error(str(e)))
        return 1


def roadmap_validate_cmd() -> int:
    """Validate roadmap structure."""
    return validate_roadmap(root_dir=Path.cwd())


def roadmap_sync_docs_cmd(
    sync_all: bool = False,
    track: Optional[str] = None,
    sprint: Optional[str] = None,
    summaries_only: bool = False,
    dry_run: bool = False,
    delete_orphaned: bool = False
) -> int:
    """Synchronize documentation from .vibey/roadmap/ to docs/roadmap/"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from vibey.operations.docs.sync_engine import SyncEngine, SyncConfig

    root_dir = Path.cwd()
    source_dir = ".vibey/roadmap"
    target_dir = "docs/roadmap"

    # Build config
    config = SyncConfig(
        source_dir=source_dir,
        target_dir=target_dir,
        delete_orphaned=delete_orphaned
    )

    # Handle filtering by track or sprint
    if track and sprint:
        print("❌ Error: Cannot specify both --track and --sprint")
        return 1

    if track:
        config.source_dir = f"{source_dir}/{track}"
        config.target_dir = f"{target_dir}/{track}"
        print(f"🎯 Syncing track: {track}")

    elif sprint:
        # Sprint IDs are like "documentation-system-1"
        parts = sprint.rsplit('-', 1)
        if len(parts) == 2 and parts[1].isdigit():
            track_slug = parts[0]
            config.source_dir = f"{source_dir}/{track_slug}/{sprint}"
            config.target_dir = f"{target_dir}/{track_slug}/{sprint}"
            print(f"🎯 Syncing sprint: {sprint}")
        else:
            print(f"❌ Error: Invalid sprint ID format: {sprint}")
            return 1

    # Filter for summaries only
    if summaries_only:
        config.include_patterns = ["**/*-COMPLETED.md", "**/roadmap.md"]

    # Create engine and sync
    engine = SyncEngine(config)

    try:
        result = engine.sync(dry_run=dry_run)

        # Print results
        prefix = "Would sync" if dry_run else "Synced"
        print()
        print("=" * 60)
        print(f"📄 Documentation Sync {'Preview' if dry_run else 'Complete'}")
        print("=" * 60)

        if result.files_copied:
            print(f"\n✓ {prefix} {len(result.files_copied)} file(s):")
            for file in result.files_copied[:10]:
                print(f"  • {file}")
            if len(result.files_copied) > 10:
                print(f"  ... and {len(result.files_copied) - 10} more")

        if result.files_skipped:
            print(f"\n⏭️  Skipped {len(result.files_skipped)} unchanged file(s)")

        if result.files_deleted:
            print(f"\n🗑️  {'Would delete' if dry_run else 'Deleted'} {len(result.files_deleted)} orphaned file(s):")
            for file in result.files_deleted:
                print(f"  • {file}")

        if result.errors:
            print(f"\n❌ {len(result.errors)} error(s):")
            for file, error in result.errors:
                print(f"  • {file}: {error}")

        print(f"\n⏱️  Duration: {result.duration_seconds:.2f}s")

        if not dry_run and result.success:
            print("\n✅ Synchronization completed successfully")
        elif dry_run:
            print("\n💡 Run without --dry-run to perform the sync")
        else:
            print("\n⚠️  Synchronization completed with errors")

        print()
        return 0 if result.success else 1

    except Exception as e:
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def roadmap_add_context_cmd(
    file_path: str,
    track: Optional[str] = None,
    sprint: Optional[str] = None,
    task: Optional[str] = None
) -> int:
    """Add a context file to a roadmap object."""
    import shutil

    root_dir = Path.cwd()
    source = Path(file_path)

    # Validate mutually exclusive options
    options_count = sum([bool(track), bool(sprint), bool(task)])
    if options_count != 1:
        print("❌ Error: Must specify exactly one of --track, --sprint, or --task")
        return 1

    if not source.exists():
        print(f"❌ Error: File not found: {source}")
        return 1

    # Determine target directory
    if task:
        # Parse task ID to get path components
        # Format: track-sprint-task-NNN
        parts = task.split('-task-')
        if len(parts) != 2:
            print(f"❌ Error: Invalid task ID format: {task}")
            return 1
        sprint_id = parts[0]
        track_parts = sprint_id.rsplit('-', 1)
        if len(track_parts) != 2:
            print(f"❌ Error: Cannot parse track from task ID: {task}")
            return 1
        track_id = track_parts[0]
        context_dir = root_dir / ".vibey" / "roadmap" / track_id / sprint_id / task / "context"
    elif sprint:
        # Parse sprint ID
        parts = sprint.rsplit('-', 1)
        if len(parts) != 2 or not parts[1].isdigit():
            print(f"❌ Error: Invalid sprint ID format: {sprint}")
            return 1
        track_id = parts[0]
        context_dir = root_dir / ".vibey" / "roadmap" / track_id / sprint / "context"
    else:
        # Track
        context_dir = root_dir / ".vibey" / "roadmap" / track / "context"

    # Create context directory if needed
    context_dir.mkdir(parents=True, exist_ok=True)

    # Copy file to context directory
    target = context_dir / source.name

    if target.exists():
        print(f"⚠️  File already exists: {target}")
        response = input("Overwrite? [y/N]: ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return 1

    try:
        shutil.copy2(source, target)
        print(f"✅ Added context file: {target.relative_to(root_dir)}")

        # Optionally trigger sync
        from vibey.operations.docs.sync_hooks import trigger_on_context_add
        target_id = task or sprint or track
        trigger_on_context_add(target_id, str(source.name), verbose=True)

        return 0
    except Exception as e:
        print(f"❌ Error adding context: {e}")
        return 1


def roadmap_add_commit_cmd(task_id: str, commit_sha: Optional[str] = None, auto: bool = False) -> int:
    """Add a git commit to a task."""
    if auto:
        commit_sha = get_current_commit()
        if not commit_sha:
            print("Error: Could not detect current commit")
            return 1
    elif not commit_sha:
        print("Error: Either provide a commit SHA or use --auto flag")
        return 1

    return add_commit_to_task(
        task_id=task_id,
        commit_sha=commit_sha,
        vibey_path=Path.cwd() / ".vibey",  # This one expects .vibey/ path
        auto_detect=auto
    )


def roadmap_validate_advanced_cmd(verbose: bool = False, check: str = 'all') -> int:
    """Advanced roadmap validation."""
    from vibey.operations.roadmap.advanced_validator import (
        AdvancedValidator,
        AdvancedValidationReport,
        print_advanced_report
    )

    root_dir = Path.cwd()
    validator = AdvancedValidator(root_dir)

    print("Running advanced validation checks...")
    print()

    if check == 'all':
        # Run all checks
        report = validator.validate()
        print_advanced_report(report, verbose=verbose)
        return 0 if not report.has_issues else 1

    # Run specific check
    report = AdvancedValidationReport()

    if check == 'circular':
        print("Checking for circular dependencies...")
        tasks = validator._load_all_tasks()
        report.total_tasks = len(tasks)
        from vibey.operations.roadmap.advanced_validator import detect_circular_dependencies
        report.circular_dependencies = detect_circular_dependencies(tasks)

    elif check == 'orphans':
        print("Checking for orphaned tasks...")
        from vibey.operations.roadmap.advanced_validator import find_orphaned_tasks
        report.orphaned_tasks = find_orphaned_tasks(validator.roadmap_dir)

    elif check == 'references':
        print("Checking for broken references...")
        from vibey.operations.roadmap.advanced_validator import find_broken_references
        report.broken_references = find_broken_references(validator.roadmap_dir)

    elif check == 'progress':
        print("Checking progress counters...")
        from vibey.operations.roadmap.advanced_validator import validate_progress_counters
        report.progress_mismatches = validate_progress_counters(validator.roadmap_dir)

    print_advanced_report(report, verbose=verbose)
    return 0 if not report.has_issues else 1


def roadmap_repair_cmd(
    fix_progress: bool = False,
    fix_references: bool = False,
    fix_all: bool = False,
    dry_run: bool = False,
    verbose: bool = False
) -> int:
    """Auto-repair roadmap integrity issues."""
    from vibey.operations.roadmap.advanced_validator import AdvancedValidator
    from vibey.operations.roadmap.auto_repair import auto_repair_all

    root_dir = Path.cwd()

    # If no specific flags set, default to --all behavior
    if not fix_progress and not fix_references and not fix_all:
        fix_all = True

    # Run validation first to find issues
    print("🔍 Scanning for issues...")
    print()

    validator = AdvancedValidator(root_dir)
    report = validator.validate()

    if not report.has_issues:
        print("✅ No issues detected! Roadmap is healthy.")
        return 0

    # Show what was found
    total_issues = (
        len(report.circular_dependencies) +
        len(report.orphaned_tasks) +
        len(report.broken_references) +
        len(report.progress_mismatches)
    )

    print(f"⚠️  Found {total_issues} issues:\n")

    if report.progress_mismatches:
        print(f"  📊 Progress counter mismatches: {len(report.progress_mismatches)} (auto-fixable)")

    if report.broken_references:
        print(f"  🔗 Broken references: {len(report.broken_references)} (removable)")

    if report.circular_dependencies:
        print(f"  🔄 Circular dependencies: {len(report.circular_dependencies)} (manual fix required)")

    if report.orphaned_tasks:
        print(f"  👻 Orphaned tasks: {len(report.orphaned_tasks)} (manual fix required)")

    print()

    # Determine what to fix
    if fix_all:
        do_fix_progress = True
        do_fix_references = True
    else:
        do_fix_progress = fix_progress
        do_fix_references = fix_references

    # Preview mode
    if dry_run:
        print("🔍 DRY-RUN MODE: Showing what would be fixed (no changes will be made)\n")

        if do_fix_progress and report.progress_mismatches:
            print(f"Would fix {len(report.progress_mismatches)} progress counter mismatches:")
            for i, mismatch in enumerate(report.progress_mismatches[:5], 1):
                print(f"  {i}. {mismatch.entity_id}")
                print(f"     Claimed: {mismatch.claimed_completed}/{mismatch.claimed_total}")
                print(f"     Actual:  {mismatch.actual_completed}/{mismatch.actual_total}")
            if len(report.progress_mismatches) > 5:
                print(f"     ... and {len(report.progress_mismatches) - 5} more")
            print()

        if do_fix_references and report.broken_references:
            print(f"Would remove {len(report.broken_references)} broken references:")
            for i, ref in enumerate(report.broken_references[:5], 1):
                print(f"  {i}. {ref.task_id}")
                print(f"     Field: {ref.field}")
                print(f"     Missing: {ref.missing_id}")
                if ref.suggested_ids:
                    print(f"     Similar: {', '.join(ref.suggested_ids)}")
            if len(report.broken_references) > 5:
                print(f"     ... and {len(report.broken_references) - 5} more")
            print()

        print("Run without --dry-run to apply these fixes")
        return 0

    # Confirm before fixing references (destructive operation)
    if do_fix_references and report.broken_references and not dry_run:
        print("⚠️  WARNING: Removing broken references is a destructive operation!")
        print("   This will permanently delete invalid task references.")
        print()
        response = input("Continue? [y/N]: ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return 1
        print()

    # Apply repairs
    print("🔧 Applying repairs...\n")

    results = auto_repair_all(
        report=report,
        fix_progress=do_fix_progress,
        fix_references=do_fix_references,
        dry_run=dry_run
    )

    # Print summary
    print("\n" + "=" * 80)
    print("REPAIR SUMMARY")
    print("=" * 80 + "\n")

    total_fixed = results['total_fixed']
    total_failed = results['total_failed']

    if total_fixed > 0:
        print(f"✅ Successfully repaired: {total_fixed} issues")

    if total_failed > 0:
        print(f"❌ Failed to repair: {total_failed} issues")

    # Show detailed results
    if verbose or total_failed > 0:
        print()

        if results['progress_counters'] and do_fix_progress:
            prog = results['progress_counters']
            print(f"Progress counters: {prog['repaired']}/{prog['total']} repaired")
            if prog['errors']:
                print("  Errors:")
                for error in prog['errors'][:5]:
                    print(f"    • {error}")

        if results['broken_references'] and do_fix_references:
            refs = results['broken_references']
            print(f"Broken references: {refs['removed']}/{refs['total']} removed")
            if refs['errors']:
                print("  Errors:")
                for error in refs['errors'][:5]:
                    print(f"    • {error}")

    print()

    if total_fixed > 0 and total_failed == 0:
        print("✅ All repairs completed successfully!")
        return 0
    elif total_fixed > 0 and total_failed > 0:
        print("⚠️  Some repairs completed, but some failed (see above)")
        return 1
    else:
        print("❌ No repairs could be completed")
        return 1


def install_hooks_cmd(force: bool = False) -> int:
    """Install git pre-commit hook."""
    from vibey.operations.roadmap.hooks import install_hooks

    print("Installing Vibey pre-commit hook...\n")

    success, message = install_hooks(project_root=Path.cwd(), force=force)

    print(message)

    if success:
        print("\nℹ️  Configuration:")
        print("  - Hook runs when .vibey/roadmap/ files are modified")
        print("  - Set VIBEY_HOOK_ADVANCED=true to enable advanced validation")
        print("  - Bypass with: git commit --no-verify (emergency only)")
        print("\nℹ️  Test the hook:")
        print("  1. Make a change to a roadmap file")
        print("  2. Run: git add .vibey/roadmap/...")
        print("  3. Run: git commit -m 'test'")
        print("  4. Hook will validate before allowing commit")
        return 0
    else:
        return 1


def uninstall_hooks_cmd() -> int:
    """Uninstall git pre-commit hook."""
    from vibey.operations.roadmap.hooks import uninstall_hooks

    print("Uninstalling Vibey pre-commit hook...\n")

    success, message = uninstall_hooks(project_root=Path.cwd())

    print(message)

    return 0 if success else 1


def check_hooks_cmd() -> int:
    """Check git hook installation status."""
    from vibey.operations.roadmap.hooks import get_hook_status

    status = get_hook_status(project_root=Path.cwd())

    print("Git Hook Status")
    print("=" * 70)
    print()

    if not status['git_repo']:
        print("❌ Not a git repository")
        return 1

    print(f"Git directory: {status['git_dir']}")
    print(f"Hooks directory exists: {'✅' if status['hooks_dir_exists'] else '❌'}")
    print()

    if not status['pre_commit_exists']:
        print("❌ No pre-commit hook installed")
        print()
        print("Install with: vibey roadmap install-hooks")
        return 1

    print(f"Pre-commit hook: {status['hook_path']}")
    print(f"  Is Vibey hook: {'✅' if status['is_vibey_hook'] else '❌'}")
    print(f"  Is executable: {'✅' if status['is_executable'] else '❌'}")
    print()

    if status['is_vibey_hook'] and status['is_executable']:
        print("✅ Vibey pre-commit hook is installed and active")
        print()
        print("Configuration:")
        print("  - VIBEY_HOOK_ADVANCED: Set to 'true' to enable advanced validation")
        print("  - Bypass: git commit --no-verify")
        return 0
    elif status['is_vibey_hook'] and not status['is_executable']:
        print("⚠️  Vibey hook installed but not executable")
        print()
        print(f"Fix with: chmod +x {status['hook_path']}")
        return 1
    else:
        print("⚠️  A different pre-commit hook is installed")
        print()
        print("To install Vibey hook:")
        print("  1. Back up existing hook if needed")
        print("  2. Run: vibey roadmap install-hooks --force")
        return 1


def roadmap_validate_fast_cmd(
    profile: str = "standard",
    incremental: bool = False,
    verbose: bool = False,
    benchmark: bool = False
) -> int:
    """Fast roadmap validation with caching."""
    from vibey.operations.roadmap.optimized_validator import (
        OptimizedValidator,
        ValidationProfile,
        print_validation_report,
        clear_yaml_cache
    )
    import time

    root_dir = Path.cwd()

    # Convert profile string to enum
    profile_map = {
        'quick': ValidationProfile.QUICK,
        'standard': ValidationProfile.STANDARD,
        'thorough': ValidationProfile.THOROUGH
    }
    profile_enum = profile_map[profile]

    if benchmark:
        # Run performance benchmark
        print("Running performance benchmark...\n")

        # Test 1: Quick validation
        print("Test 1: Quick validation (syntax only)")
        clear_yaml_cache()
        validator = OptimizedValidator(root_dir, ValidationProfile.QUICK)
        report = validator.validate()
        print(f"  Duration: {report.duration_seconds:.2f}s")
        print(f"  Files: {report.total_files}")
        print(f"  Target: <3s")
        print(f"  Status: {'✅ PASS' if report.duration_seconds < 3.0 else '❌ FAIL'}\n")

        # Test 2: Standard validation (first run - cold cache)
        print("Test 2: Standard validation (cold cache)")
        clear_yaml_cache()
        validator = OptimizedValidator(root_dir, ValidationProfile.STANDARD)
        report = validator.validate()
        print(f"  Duration: {report.duration_seconds:.2f}s")
        print(f"  Files: {report.total_files}")
        print(f"  Cache hit rate: {report.cache_hit_rate:.1f}%")
        print(f"  Target: <10s")
        print(f"  Status: {'✅ PASS' if report.duration_seconds < 10.0 else '❌ FAIL'}\n")

        # Test 3: Standard validation (second run - warm cache)
        print("Test 3: Standard validation (warm cache)")
        validator = OptimizedValidator(root_dir, ValidationProfile.STANDARD)
        report = validator.validate()
        print(f"  Duration: {report.duration_seconds:.2f}s")
        print(f"  Files: {report.total_files}")
        print(f"  Cache hit rate: {report.cache_hit_rate:.1f}%")
        print(f"  Target: <2s")
        print(f"  Status: {'✅ PASS' if report.duration_seconds < 2.0 else '❌ FAIL'}\n")

        # Test 4: Incremental validation
        print("Test 4: Incremental validation (changed files only)")
        validator = OptimizedValidator(root_dir, ValidationProfile.STANDARD)
        report = validator.validate(incremental=True)
        print(f"  Duration: {report.duration_seconds:.2f}s")
        print(f"  Files: {report.total_files}")
        print(f"  Cache hit rate: {report.cache_hit_rate:.1f}%")
        print(f"  Target: <2s")
        print(f"  Status: {'✅ PASS' if report.duration_seconds < 2.0 else '❌ FAIL'}\n")

        # Test 5: Thorough validation
        print("Test 5: Thorough validation (with git integration)")
        clear_yaml_cache()
        validator = OptimizedValidator(root_dir, ValidationProfile.THOROUGH)
        report = validator.validate()
        print(f"  Duration: {report.duration_seconds:.2f}s")
        print(f"  Files: {report.total_files}")
        print(f"  Cache hit rate: {report.cache_hit_rate:.1f}%")
        print(f"  Target: <20s")
        print(f"  Status: {'✅ PASS' if report.duration_seconds < 20.0 else '❌ FAIL'}\n")

        print("Benchmark complete!")
        return 0

    # Normal validation
    validator = OptimizedValidator(root_dir, profile_enum)
    report = validator.validate(incremental=incremental)

    # Print report
    print_validation_report(report, verbose=verbose)

    # Return exit code
    return 0 if report.invalid_files == 0 else 1


# ============================================================================
# Roadmap Checkpoint Commands
# ============================================================================

def checkpoint_create_cmd(name: Optional[str] = None) -> int:
    """Create a new integrity checkpoint."""
    import subprocess
    from datetime import datetime

    # Default to timestamped name if not provided
    if not name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"checkpoint_{timestamp}"

    script_path = Path(__file__).parent.parent.parent / "scripts" / "create-integrity-checkpoint.sh"

    try:
        result = subprocess.run(
            [str(script_path), name],
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error creating checkpoint: {e}")
        return 1


def checkpoint_list_cmd() -> int:
    """List all available checkpoints."""
    import subprocess

    script_path = Path(__file__).parent.parent.parent / "scripts" / "manage-checkpoints.sh"

    try:
        result = subprocess.run(
            [str(script_path), "list"],
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error listing checkpoints: {e}")
        return 1


def checkpoint_verify_cmd(name: str) -> int:
    """Verify checkpoint integrity."""
    import subprocess

    script_path = Path(__file__).parent.parent.parent / "scripts" / "manage-checkpoints.sh"

    try:
        result = subprocess.run(
            [str(script_path), "verify", name],
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error verifying checkpoint: {e}")
        return 1


def checkpoint_restore_cmd(name: str, verify_only: bool = False) -> int:
    """Restore from a checkpoint."""
    import subprocess

    script_path = Path(__file__).parent.parent.parent / "scripts" / "restore-integrity-checkpoint.sh"

    args = [str(script_path), name]
    if verify_only:
        args.append("--verify-only")

    try:
        result = subprocess.run(
            args,
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error restoring checkpoint: {e}")
        return 1


def checkpoint_clean_cmd(keep: int = 5) -> int:
    """Clean old checkpoints."""
    import subprocess

    script_path = Path(__file__).parent.parent.parent / "scripts" / "manage-checkpoints.sh"

    try:
        result = subprocess.run(
            [str(script_path), "clean", str(keep)],
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error cleaning checkpoints: {e}")
        return 1


def checkpoint_compare_cmd(checkpoint1: str, checkpoint2: str) -> int:
    """Compare two checkpoints."""
    import subprocess

    script_path = Path(__file__).parent.parent.parent / "scripts" / "manage-checkpoints.sh"

    try:
        result = subprocess.run(
            [str(script_path), "compare", checkpoint1, checkpoint2],
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error comparing checkpoints: {e}")
        return 1


# ============================================================================
# Safe YAML Edit Commands
# ============================================================================

def edit_file_cmd(file_path: str, modifications: list, dry_run: bool = False) -> int:
    """Safely edit a single YAML file."""
    from vibey.operations.roadmap.safe_yaml_editor import SafeYAMLEditor

    # Parse modifications from "key=value" format
    mod_dict = {}
    for mod in modifications:
        if '=' not in mod:
            print(f"Error: Invalid modification format '{mod}' (expected key=value)")
            return 1

        key, value = mod.split('=', 1)
        mod_dict[key] = value

    if not mod_dict:
        print("Error: No modifications specified. Use --set key=value")
        return 1

    try:
        editor = SafeYAMLEditor(auto_backup=True, validate=True)

        if dry_run:
            print("🔍 Dry-run mode: Previewing changes (no files will be modified)")
            print()

        result = editor.edit_file(file_path, mod_dict, dry_run=dry_run)

        if result.success:
            print(f"✅ Successfully {'validated' if dry_run else 'edited'}: {result.file_path}")

            if result.changes_made:
                print("\nChanges:")
                for field, change in result.changes_made.items():
                    print(f"  {field}: {change['old']} → {change['new']}")

            if result.backup_path:
                print(f"\nBackup: {result.backup_path}")

            if result.warnings:
                print("\nWarnings:")
                for warning in result.warnings:
                    print(f"  ⚠️  {warning}")

            return 0
        else:
            print(f"❌ Edit failed: {result.file_path}")
            print("\nErrors:")
            for error in result.errors:
                print(f"  • {error}")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def edit_bulk_cmd(file_pattern: str, modifications: list, dry_run: bool = False) -> int:
    """Safely bulk edit multiple YAML files."""
    from vibey.operations.roadmap.safe_yaml_editor import SafeYAMLEditor

    # Parse modifications
    mod_dict = {}
    for mod in modifications:
        if '=' not in mod:
            print(f"Error: Invalid modification format '{mod}' (expected key=value)")
            return 1

        key, value = mod.split('=', 1)
        mod_dict[key] = value

    if not mod_dict:
        print("Error: No modifications specified. Use --set key=value")
        return 1

    try:
        editor = SafeYAMLEditor(auto_backup=True, validate=True)

        if dry_run:
            print("🔍 Dry-run mode: Previewing changes (no files will be modified)")
            print()

        print(f"Finding files matching: {file_pattern}")
        result = editor.bulk_edit(file_pattern, mod_dict, dry_run=dry_run, root_dir=Path.cwd())

        print(f"\nFiles found: {result.total_files}")

        if result.success:
            print(f"✅ Bulk edit {'validated' if dry_run else 'completed'} successfully")
            print(f"  Files {'would be ' if dry_run else ''}changed: {result.files_changed}")

            if result.checkpoint_path:
                print(f"  Checkpoint: {result.checkpoint_path}")

            return 0
        else:
            print(f"❌ Bulk edit failed")
            print(f"  Files changed: {result.files_changed}")
            print(f"  Files failed: {result.files_failed}")

            if result.rollback_performed:
                print(f"  ✅ All changes rolled back")

            if result.errors:
                print("\nErrors:")
                for error in result.errors[:10]:  # Limit to first 10
                    print(f"  • {error}")

                if len(result.errors) > 10:
                    print(f"  ... and {len(result.errors) - 10} more errors")

            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def edit_validate_cmd(file_path: Optional[str] = None, validate_all: bool = False) -> int:
    """Validate YAML file(s)."""
    from vibey.operations.roadmap.safe_yaml_editor import SafeYAMLEditor

    editor = SafeYAMLEditor()

    if validate_all:
        # Validate all YAML files in roadmap
        roadmap_dir = Path.cwd() / ".vibey" / "roadmap"

        if not roadmap_dir.exists():
            print("Error: Roadmap directory not found")
            return 1

        yaml_files = list(roadmap_dir.rglob("*.yaml"))
        print(f"Validating {len(yaml_files)} YAML files...")
        print()

        valid_count = 0
        invalid_count = 0
        error_files = []

        for yaml_file in yaml_files:
            result = editor.validate_yaml_file(yaml_file)

            if result.valid:
                valid_count += 1
                print(f"✅ {yaml_file.relative_to(Path.cwd())}")
            else:
                invalid_count += 1
                print(f"❌ {yaml_file.relative_to(Path.cwd())}")
                error_files.append((yaml_file, result))

                for error in result.errors[:3]:  # Show first 3 errors per file
                    print(f"   • {error}")

        print()
        print(f"Summary: {valid_count} valid, {invalid_count} invalid")

        if error_files:
            print("\nFiles with errors:")
            for yaml_file, _ in error_files:
                print(f"  • {yaml_file.relative_to(Path.cwd())}")

        return 0 if invalid_count == 0 else 1

    elif file_path:
        # Validate single file
        result = editor.validate_yaml_file(file_path)

        print(f"Validating: {file_path}")
        print()

        if result.valid:
            print("✅ Validation passed")

            if result.warnings:
                print("\nWarnings:")
                for warning in result.warnings:
                    print(f"  ⚠️  {warning}")

            return 0
        else:
            print("❌ Validation failed")
            print("\nErrors:")
            for error in result.errors:
                print(f"  • {error}")

            if result.warnings:
                print("\nWarnings:")
                for warning in result.warnings:
                    print(f"  ⚠️  {warning}")

            return 1

    else:
        print("Error: Specify --file <path> or --all")
        return 1


def edit_rollback_cmd(last_n: int = 1) -> int:
    """Rollback recent edit operations."""
    from vibey.operations.roadmap.safe_yaml_editor import SafeYAMLEditor

    editor = SafeYAMLEditor()

    print(f"Rolling back last {last_n} edit(s)...")
    print()

    success_count = 0
    for i in range(last_n):
        if editor.rollback_last_edit():
            success_count += 1
        else:
            if i == 0:
                print("No backups found to rollback")
            break

    if success_count > 0:
        print()
        print(f"✅ Rolled back {success_count} edit(s)")
        return 0
    else:
        print()
        print("❌ No edits rolled back")
        return 1


# ============================================================================
# Deploy Commands
# ============================================================================

def deploy_cmd(platform: str, clean: bool = False) -> int:
    """Deploy framework to platform."""
    return deploy_framework(
        platform=platform,
        clean=clean,
        project_root=Path.cwd()
    )


# ============================================================================
# Docs Commands
# ============================================================================

def docs_generate_cmd(overwrite: bool = False) -> int:
    """Generate documentation."""
    return generate_docs(
        vibey_dir=Path.cwd() / ".vibey",  # This expects .vibey/ path
        overwrite=overwrite,
        quiet=False
    )


# ============================================================================
# Config Commands
# ============================================================================

def config_show_cmd() -> int:
    """Show current configuration."""
    from vibey.cli.config_migrate import config_show_cmd as show_impl
    return show_impl()


def config_validate_cmd() -> int:
    """Validate configuration."""
    from vibey.cli.config_migrate import config_validate_cmd as validate_impl
    return validate_impl()


def config_generate_cmd() -> int:
    """Generate configuration."""
    # Interactive - let generate_config handle prompts
    # This would typically be called with parameters from CLI
    print("Error: config generate requires parameters (project name, type, etc.)")
    print("Use 'vibey config generate --help' for usage information")
    return 1


def config_migrate_cmd(backup: bool = True, dry_run: bool = False, force: bool = False) -> int:
    """Migrate legacy config to modular format."""
    from vibey.cli.config_migrate import config_migrate_cmd as migrate_impl
    return migrate_impl(backup=backup, dry_run=dry_run, force=force)


def config_rollback_cmd(backup_id: Optional[str] = None, list_backups: bool = False) -> int:
    """Rollback to a previous config backup."""
    from vibey.cli.config_migrate import config_rollback_cmd as rollback_impl
    return rollback_impl(backup_id=backup_id, list_backups=list_backups)


def config_update_cmd(key: str, value: str) -> int:
    """Update configuration value."""
    config_path = Path.cwd() / ".vibey" / "config" / "project.yaml"
    return update_config_value(
        config_path=config_path,
        key_path=key,
        value=value,
        create_missing=False,
        verbose=True
    )


# ============================================================================
# Migration Commands
# ============================================================================

def migrate_to_roadmap_cmd() -> int:
    """Migrate legacy sprint files to roadmap."""
    return migrate_to_roadmap(
        root_dir=Path.cwd() / ".vibey",  # Migration expects .vibey/ path
        dry_run=False,
        backup=True
    )


def migrate_embedded_tasks_cmd() -> int:
    """Migrate embedded tasks to separate files."""
    return migrate_embedded_tasks(
        root_dir=Path.cwd() / ".vibey",  # Migration expects .vibey/ path
        dry_run=False
    )


# ============================================================================
# Audit Trail Commands
# ============================================================================

def audit_log_cmd(limit: int = 20) -> int:
    """Show recent audit trail entries."""
    from vibey.operations.roadmap.audit_trail import AuditTrailManager
    from datetime import datetime

    manager = AuditTrailManager(Path.cwd())
    entries = manager.get_recent_changes(limit=limit)

    if not entries:
        print("No audit trail entries found.")
        return 0

    print(f"\n📋 Recent Audit Trail Entries (last {limit})")
    print("=" * 80)

    for entry in entries:
        timestamp = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{timestamp} - {entry.object_type.upper()}: {entry.object_id}")
        print(f"  Field: {entry.field}")
        print(f"  Change: {entry.old_value} → {entry.new_value}")
        print(f"  By: {entry.changed_by} ({entry.source})")
        print(f"  Reason: {entry.reason}")
        if entry.commit:
            print(f"  Commit: {entry.commit}")

    print("\n" + "=" * 80)
    print(f"Total entries shown: {len(entries)}\n")
    return 0


def audit_show_cmd(object_id: str) -> int:
    """Show change history for a specific object."""
    from vibey.operations.roadmap.audit_trail import AuditTrailManager
    from datetime import datetime

    manager = AuditTrailManager(Path.cwd())
    entries = manager.get_object_history(object_id)

    if not entries:
        print(f"No audit trail entries found for object '{object_id}'.")
        return 0

    print(f"\n📋 Audit Trail for {object_id}")
    print("=" * 80)

    for entry in entries:
        timestamp = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{timestamp}")
        print(f"  Field: {entry.field}")
        print(f"  Change: {entry.old_value} → {entry.new_value}")
        print(f"  By: {entry.changed_by} ({entry.source})")
        print(f"  Reason: {entry.reason}")
        if entry.commit:
            print(f"  Commit: {entry.commit}")

    print("\n" + "=" * 80)
    print(f"Total changes: {len(entries)}\n")
    return 0


def audit_suspicious_cmd() -> int:
    """Detect suspicious changes in audit trail."""
    from vibey.operations.roadmap.audit_trail import AuditTrailManager
    from datetime import datetime

    manager = AuditTrailManager(Path.cwd())
    suspicious = manager.detect_suspicious_changes()

    if not suspicious:
        print("\n✅ No suspicious changes detected in audit trail.\n")
        return 0

    print(f"\n⚠️  Suspicious Changes Detected: {len(suspicious)}")
    print("=" * 80)

    for entry, reason in suspicious:
        timestamp = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n⚠️  {reason}")
        print(f"  Object: {entry.object_type.upper()} {entry.object_id}")
        print(f"  Field: {entry.field}")
        print(f"  Change: {entry.old_value} → {entry.new_value}")
        print(f"  When: {timestamp}")
        print(f"  By: {entry.changed_by} ({entry.source})")
        print(f"  Reason: {entry.reason}")
        if entry.commit:
            print(f"  Commit: {entry.commit}")

    print("\n" + "=" * 80)
    print(f"Total suspicious changes: {len(suspicious)}\n")
    return 1  # Return error code to indicate issues found


def audit_report_cmd(
    object_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> int:
    """Generate detailed audit report."""
    from vibey.operations.roadmap.audit_trail import AuditTrailManager
    from datetime import datetime

    manager = AuditTrailManager(Path.cwd())

    # Parse dates if provided
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            print(f"❌ Invalid start date format: {start_date}")
            print("   Expected format: YYYY-MM-DD")
            return 1

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            print(f"❌ Invalid end date format: {end_date}")
            print("   Expected format: YYYY-MM-DD")
            return 1

    # Generate report
    report = manager.generate_report(
        object_id=object_id,
        start_date=start_dt,
        end_date=end_dt
    )

    print(report)
    return 0


def activity_cmd(
    limit: int = 10,
    object_id: Optional[str] = None,
    activity_type: Optional[str] = None
) -> int:
    """Show recent activity in compact format.

    This provides a user-friendly view of recent roadmap activities,
    formatted as requested in the task description:
    2025-12-06 14:30  TASK_COMPLETED   task-123  claude-code
    2025-12-06 14:29  CRITERION_MET    task-123  Tests passed
    """
    from vibey.operations.roadmap.audit_trail import AuditTrailManager
    from datetime import datetime

    manager = AuditTrailManager(Path.cwd())

    # Get entries, either for a specific object or all
    if object_id:
        entries = manager.get_object_history(object_id)
        entries = entries[:limit] if limit else entries
    else:
        entries = manager.get_recent_changes(limit=limit)

    # Filter by activity type if specified
    if activity_type and entries:
        activity_type_lower = activity_type.lower()
        entries = [
            e for e in entries
            if activity_type_lower in e.field.lower()
            or activity_type_lower in str(e.new_value).lower()
        ]

    if not entries:
        print("No recent activity found.")
        return 0

    # Print header
    print(f"\n📊 Recent Activity (last {len(entries)})")
    print("-" * 70)

    # Print entries in compact format
    for entry in entries:
        try:
            timestamp = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            timestamp = str(entry.timestamp)[:16]

        # Determine activity type from field or new_value
        if entry.field == "status":
            event = f"{entry.old_value} → {entry.new_value}".upper()
        elif entry.field == "activity":
            event = str(entry.new_value).upper()
        elif entry.field.startswith("quality_gate."):
            event = f"GATE_{entry.new_value}".upper()
        elif entry.field.startswith("criterion."):
            event = f"CRITERION_{entry.new_value}".upper()
        elif entry.field == "transition_blocked":
            event = "BLOCKED"
        else:
            event = entry.field.upper()

        # Truncate event and ID for display
        event = event[:20].ljust(20)
        obj_id = entry.object_id[:25] if len(entry.object_id) > 25 else entry.object_id.ljust(25)

        # Actor (from source or changed_by)
        actor = entry.changed_by if entry.changed_by != "system" else entry.source

        print(f"{timestamp}  {event}  {obj_id}  {actor}")

    print("-" * 70)
    return 0


def auto_progress_cmd(
    mode: str = "check",
    ticket_id: Optional[str] = None,
    enable: bool = False,
    disable: bool = False
) -> int:
    """Check or apply automatic status progressions.

    Args:
        mode: 'check' for dry-run, 'apply' to actually change status
        ticket_id: Optional specific ticket to check/apply
        enable: Enable auto-progression in config
        disable: Disable auto-progression in config

    Returns:
        Exit code (0 for success)
    """
    import yaml

    config_path = Path.cwd() / ".vibey" / "config" / "roadmap.yaml"

    # Handle enable/disable first
    if enable or disable:
        if not config_path.exists():
            print("❌ Config file not found: .vibey/config/roadmap.yaml")
            return 1

        try:
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}

            if "auto_progression" not in config:
                config["auto_progression"] = {}

            config["auto_progression"]["enabled"] = enable

            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            status = "enabled" if enable else "disabled"
            print(f"✅ Auto-progression {status} in .vibey/config/roadmap.yaml")
            return 0
        except Exception as e:
            print(f"❌ Failed to update config: {e}")
            return 1

    # Import status manager
    from vibey.operations.roadmap.status_manager import (
        StatusManager,
        check_auto_progressions,
        apply_auto_progressions,
    )

    manager = StatusManager(Path.cwd())

    if not manager.is_enabled():
        print("⚠ Auto-progression is disabled.")
        print("  Enable with: vibey roadmap auto-progress --enable")
        print("  Or set auto_progression.enabled: true in .vibey/config/roadmap.yaml")
        return 0

    ticket_ids = [ticket_id] if ticket_id else None

    if mode == "check":
        print("\n🔍 Checking for eligible auto-progressions...")
        results = check_auto_progressions(Path.cwd(), ticket_ids)

        if not results:
            print("No tickets eligible for auto-progression.")
            return 0

        print(f"\n📋 {len(results)} ticket(s) can be auto-progressed:\n")
        print("-" * 70)

        for r in results:
            print(f"  {r.ticket_type.upper()}: {r.ticket_id}")
            print(f"    {r.old_status} → {r.new_status}")
            print(f"    Reason: {r.reason}")
            print()

        print("-" * 70)
        print("Run with --apply to execute these progressions.")
        return 0

    elif mode == "apply":
        print("\n🚀 Applying auto-progressions...")
        results = apply_auto_progressions(Path.cwd(), ticket_ids)

        if not results:
            print("No progressions applied.")
            return 0

        print(f"\n✅ {len(results)} progression(s) applied:\n")
        print("-" * 70)

        for r in results:
            print(f"  {r.ticket_type.upper()}: {r.ticket_id}")
            print(f"    {r.old_status} → {r.new_status}")
            print(f"    Reason: {r.reason}")
            print()

        print("-" * 70)
        return 0

    return 0


# ============================================================================
# Validation Commands
# ============================================================================

def validate_docs_cmd(verbose: bool = False) -> int:
    """Validate documentation organization in roadmap."""
    from vibey.operations.validate.doc_organization import DocOrganizationValidator

    roadmap_dir = Path.cwd() / '.vibey' / 'roadmap'
    validator = DocOrganizationValidator(roadmap_dir, verbose)
    report = validator.validate()

    # Print summary
    print("\n" + "=" * 70)
    print("DOCUMENTATION ORGANIZATION VALIDATION")
    print("=" * 70)
    print(f"Tracks checked: {report.tracks_checked}")
    print(f"Sprints checked: {report.sprints_checked}")

    if report.warnings:
        print(f"\n⚠ Warnings: {len(report.warnings)}")
        for path, warning in report.warnings[:10]:
            print(f"  {path}")
            print(f"    {warning}")
        if len(report.warnings) > 10:
            print(f"  ... and {len(report.warnings) - 10} more warnings")

    if report.issues:
        print(f"\n✗ Issues: {len(report.issues)}")
        for path, issue in report.issues[:20]:
            print(f"  {path}")
            print(f"    {issue}")
        if len(report.issues) > 20:
            print(f"  ... and {len(report.issues) - 20} more issues")

    print("\n" + "=" * 70)
    if report.is_valid:
        print("✅ All documentation properly organized!")
    else:
        print(f"❌ {len(report.issues)} organization issues found")
    print("=" * 70)

    return 0 if report.is_valid else 1


def validate_assets_cmd(asset_type: str = 'all', verbose: bool = False) -> int:
    """Validate asset frontmatter (agents, workflows, handoffs)."""
    from vibey.operations.validate.frontmatter import FrontmatterValidator

    root_dir = Path.cwd()
    validator = FrontmatterValidator(root_dir, verbose)

    if asset_type == 'all':
        report = validator.validate_all()
    else:
        report = validator.validate_assets(asset_type)

    # Print results by type
    types_validated = set(r.asset_type for r in report.results)
    for atype in sorted(types_validated):
        type_results = [r for r in report.results if r.asset_type == atype]
        valid = sum(1 for r in type_results if r.is_valid)
        invalid = sum(1 for r in type_results if not r.is_valid)
        print(f"\n{atype.capitalize()}:")
        print(f"  ✅ {valid} valid")
        if invalid > 0:
            print(f"  ❌ {invalid} invalid")

    # Show errors
    invalid_results = [r for r in report.results if not r.is_valid]
    if invalid_results:
        print(f"\n{'=' * 60}")
        print("VALIDATION ERRORS:")
        print('=' * 60)
        for result in invalid_results:
            print(f"\n{result.filepath}:")
            for error in result.errors:
                print(f"  - {error}")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"TOTAL: {report.valid_count} valid, {report.invalid_count} invalid")
    print('=' * 60)

    return 0 if report.is_valid else 1


def roadmap_sync_commits_cmd(dry_run: bool = False) -> int:
    """Scan git history and link commits to tasks based on commit messages."""
    from vibey.operations.git.commit_evidence import sync_commits_from_git
    from vibey.operations.roadmap import add_commit_to_task

    root_dir = Path.cwd()

    print("Scanning git history for task references...")

    found_commits = sync_commits_from_git(root_dir, dry_run=dry_run)

    if not found_commits:
        print("No commits with task references found.")
        return 0

    print(f"\nFound {sum(len(commits) for commits in found_commits.values())} commits referencing {len(found_commits)} tasks:")
    print()

    linked_count = 0
    for task_id, commits in sorted(found_commits.items()):
        print(f"  {task_id}: {len(commits)} commit(s)")
        for sha in commits[:3]:  # Show first 3
            print(f"    - {sha[:8]}")
        if len(commits) > 3:
            print(f"    ... and {len(commits) - 3} more")

        if not dry_run:
            # Link each commit
            for sha in commits:
                try:
                    result = add_commit_to_task(
                        task_id=task_id,
                        commit_sha=sha,
                        vibey_path=root_dir / ".vibey",
                        auto_detect=False
                    )
                    if result == 0:
                        linked_count += 1
                except Exception:
                    pass  # Skip errors silently

    if dry_run:
        print(f"\n[DRY RUN] Would link {sum(len(c) for c in found_commits.values())} commits")
    else:
        print(f"\n✅ Linked {linked_count} commits to tasks")

    return 0


def roadmap_validate_commits_cmd() -> int:
    """Validate that all completed tasks have commit evidence."""
    from vibey.operations.git.commit_evidence import validate_all_tasks_have_commits

    root_dir = Path.cwd()

    print("Validating commit evidence for completed tasks...")
    print()

    issues = validate_all_tasks_have_commits(root_dir)

    if not issues:
        print("✅ All completed tasks have commit evidence")
        return 0

    print(f"❌ Found {len(issues)} completed task(s) without commits:")
    print()

    for result in issues:
        print(f"  • {result.task_id}")
        print(f"    {result.message}")
        print()

    print("To link commits:")
    print("  vibey roadmap add-commit <task-id> <sha>")
    print("  vibey roadmap sync-commits  # Auto-link from git history")

    return 1


# ============================================================================
# Database Commands
# ============================================================================

def db_init_cmd(force: bool = False) -> int:
    """Initialize SQLite database from YAML files."""
    from datetime import datetime, timezone
    import shutil

    root_dir = Path.cwd()
    vibey_dir = root_dir / ".vibey"
    db_path = vibey_dir / "roadmap.db"

    # Check if database already exists
    if db_path.exists() and not force:
        print(f"❌ Database already exists at {db_path}")
        print("   Use --force to overwrite")
        return 1

    # Import database modules
    try:
        from vibey.roadmap.database.connection import get_connection, close_connection
        from vibey.roadmap.database.schema import create_schema, SCHEMA_VERSION
        from vibey.roadmap.database.views import create_views
        from vibey.roadmap.database.triggers import create_triggers
        from vibey.roadmap.serialization import load_roadmap, load_track, load_sprint, load_task
    except ImportError as e:
        print(f"❌ Database module not available: {e}")
        return 1

    print("🗄️  Initializing SQLite database...")
    print(f"   Path: {db_path}")

    # Remove existing database if force
    if db_path.exists() and force:
        db_path.unlink()
        print("   Removed existing database")

    try:
        # Create schema
        print("   Creating schema (25 tables)...")
        conn = get_connection(db_path=db_path)
        create_schema(conn=conn)

        # Create views
        print("   Creating views (13 computed views)...")
        create_views(conn=conn)

        # Create triggers
        print("   Creating triggers (40 triggers)...")
        create_triggers(conn=conn)

        conn.commit()

        # Load YAML data into database
        print("   Loading roadmap data from YAML...")
        # Canonical location is .vibey/roadmap/roadmap.yaml (not .vibey/roadmap.yaml)
        roadmap_yaml = vibey_dir / "roadmap" / "roadmap.yaml"

        if not roadmap_yaml.exists():
            print("   ⚠️  No roadmap.yaml found, database initialized empty")
        else:
            roadmap = load_roadmap(roadmap_yaml)
            _load_roadmap_to_db(conn, roadmap, vibey_dir)

        # Set database state
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("""
            UPDATE database_state SET
                is_dirty = 0,
                last_yaml_load = ?,
                source_commit = NULL
            WHERE id = 1
        """, (now,))
        conn.commit()

        print(f"\n✅ Database initialized successfully")
        print(f"   Schema version: {SCHEMA_VERSION}")

        # Show counts
        counts = {}
        for table in ['roadmaps', 'tracks', 'sprints', 'tasks']:
            row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            counts[table] = row[0]

        print(f"   Roadmaps: {counts['roadmaps']}")
        print(f"   Tracks:   {counts['tracks']}")
        print(f"   Sprints:  {counts['sprints']}")
        print(f"   Tasks:    {counts['tasks']}")

        close_connection(db_path=db_path)
        return 0

    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        if db_path.exists():
            db_path.unlink()
        return 1


def _normalize_status(status_value: str) -> str:
    """Normalize status value to match database constraints."""
    # Map model values to database values
    status_map = {
        "superseded": "wont_do",  # Superseded is semantically equivalent to wont_do
    }
    return status_map.get(status_value, status_value)


def _load_roadmap_to_db_flat(conn, roadmap, vibey_dir, now, db_create_track, db_create_sprint, db_create_task, load_track, load_sprint, load_task):
    """Load roadmap data from ULID flat file structure."""
    roadmap_dir = vibey_dir / "roadmap"
    loaded_tracks = 0
    loaded_sprints = 0
    loaded_tasks = 0
    skipped_tracks = 0
    skipped_sprints = 0
    skipped_tasks = 0

    # Build slug -> ULID mappings from .id files
    def load_id_mapping(entity_dir):
        """Load slug=ULID mapping from .id file."""
        id_file = entity_dir / ".id"
        mapping = {}
        if id_file.exists():
            for line in id_file.read_text().strip().split("\n"):
                if "=" in line:
                    slug, ulid = line.split("=", 1)
                    mapping[slug] = ulid
        return mapping

    tracks_dir = roadmap_dir / "tracks"
    sprints_dir = roadmap_dir / "sprints"
    tasks_dir = roadmap_dir / "tasks"

    track_slug_to_ulid = load_id_mapping(tracks_dir)
    sprint_slug_to_ulid = load_id_mapping(sprints_dir)

    # Build reverse mapping: track ULID -> track slug (for finding sprints by track)
    track_ulid_to_slug = {v: k for k, v in track_slug_to_ulid.items()}

    # Also build a set of valid track ULIDs for validation
    valid_track_ulids = set()

    # 1. Load all tracks from tracks/*.yaml
    for track_file in sorted(tracks_dir.glob("*.yaml")):
        try:
            track = load_track(track_file)
            track_status = track.status.value if hasattr(track.status, 'value') else str(track.status)

            db_create_track(
                id=track.id,
                roadmap_id=roadmap.id,
                name=track.name,
                status=_normalize_status(track_status),
                blocked=track.blocked,
                priority=track.priority.value if hasattr(track, 'priority') and track.priority else 'medium',
                created=track.created or now,
                conn=conn,
            )
            valid_track_ulids.add(track.id)
            loaded_tracks += 1
        except Exception as e:
            skipped_tracks += 1
            continue

    # 2. Load all sprints from sprints/*.yaml
    valid_sprint_ulids = set()
    if sprints_dir.exists():
        for sprint_file in sorted(sprints_dir.glob("*.yaml")):
            try:
                sprint = load_sprint(sprint_file)
                sprint_status = sprint.status.value if hasattr(sprint.status, 'value') else str(sprint.status)

                # Get track_id from sprint and resolve slug -> ULID
                track_id = getattr(sprint, 'track_id', None)
                if not track_id:
                    skipped_sprints += 1
                    continue

                # Resolve slug to ULID if needed
                if track_id in track_slug_to_ulid:
                    track_id = track_slug_to_ulid[track_id]
                elif track_id not in valid_track_ulids:
                    # Unknown track_id, skip
                    skipped_sprints += 1
                    continue

                # Build metadata dict
                sprint_metadata = None
                if sprint.metadata:
                    sprint_metadata = {
                        'last_updated': sprint.metadata.last_updated.isoformat() if sprint.metadata.last_updated else None,
                        'estimated_duration': getattr(sprint.metadata, 'estimated_duration', None),
                        'actual_duration': getattr(sprint.metadata, 'actual_duration', None),
                        'estimated_tokens': getattr(sprint.metadata, 'estimated_tokens', None),
                        'actual_tokens': getattr(sprint.metadata, 'actual_tokens', None),
                    }

                db_create_sprint(
                    id=sprint.id,
                    track_id=track_id,
                    roadmap_id=roadmap.id,
                    name=sprint.name,
                    status=_normalize_status(sprint_status),
                    blocked=sprint.blocked,
                    created=sprint.created or now,
                    started=sprint.started,
                    completed=sprint.completed,
                    description=getattr(sprint, 'description', None),
                    goal=getattr(sprint, 'goal', None),
                    notes=getattr(sprint, 'notes', None),
                    conn=conn,
                )
                valid_sprint_ulids.add(sprint.id)
                loaded_sprints += 1
            except Exception as e:
                skipped_sprints += 1
                continue

    # 3. Load all tasks from tasks/*.yaml
    if tasks_dir.exists():
        for task_file in sorted(tasks_dir.glob("*.yaml")):
            try:
                task = load_task(task_file)
                task_status = task.status.value if hasattr(task.status, 'value') else str(task.status)

                # Get sprint_id and track_id from task and resolve slugs -> ULIDs
                sprint_id = getattr(task, 'sprint_id', None)
                track_id = getattr(task, 'track_id', None)
                if not sprint_id:
                    skipped_tasks += 1
                    continue

                # Resolve sprint slug to ULID if needed
                if sprint_id in sprint_slug_to_ulid:
                    sprint_id = sprint_slug_to_ulid[sprint_id]
                elif sprint_id not in valid_sprint_ulids:
                    skipped_tasks += 1
                    continue

                # Resolve track slug to ULID if needed
                if track_id and track_id in track_slug_to_ulid:
                    track_id = track_slug_to_ulid[track_id]
                elif track_id and track_id not in valid_track_ulids:
                    # Try to get track_id from sprint if missing
                    track_id = None

                db_create_task(
                    id=task.id,
                    sprint_id=sprint_id,
                    track_id=track_id,
                    roadmap_id=roadmap.id,
                    task_type=task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
                    title=task.title,
                    description=task.description,
                    status=_normalize_status(task_status),
                    blocked=task.blocked,
                    priority=task.priority.value if hasattr(task, 'priority') and task.priority else 'medium',
                    created=task.created or now,
                    started=task.started,
                    completed=task.completed,
                    assigned_agent=task.assigned_agent,
                    phase_label=task.phase_label,
                    estimated_tokens=task.estimated_tokens,
                    actual_tokens=task.actual_tokens,
                    complexity=task.complexity.value if hasattr(task.complexity, 'value') else None,
                    conn=conn,
                )
                loaded_tasks += 1
            except Exception as e:
                skipped_tasks += 1
                continue

    # Print summary
    total_skipped = skipped_tracks + skipped_sprints + skipped_tasks
    if total_skipped > 0:
        print(f"   Loaded {loaded_tracks} tracks, {loaded_sprints} sprints, {loaded_tasks} tasks")
        print(f"   Skipped {skipped_tracks} tracks, {skipped_sprints} sprints, {skipped_tasks} tasks (validation errors)")
    else:
        print(f"   Loaded {loaded_tracks} tracks, {loaded_sprints} sprints, {loaded_tasks} tasks")


def _load_roadmap_to_db(conn, roadmap, vibey_dir: Path):
    """Load roadmap data into database.

    Supports both:
    - ULID flat structure (tracks/, sprints/, tasks/)
    - Legacy nested structure (track-id/sprint-id/task-id/)
    """
    from datetime import datetime, timezone
    from vibey.roadmap.database.crud import (
        create_roadmap as db_create_roadmap,
        create_track as db_create_track,
        create_sprint as db_create_sprint,
        create_task as db_create_task,
    )
    from vibey.roadmap.serialization import load_track, load_sprint, load_task

    now = datetime.now(timezone.utc)
    roadmap_dir = vibey_dir / "roadmap"

    # Create roadmap record
    status_val = roadmap.status.value if hasattr(roadmap.status, 'value') else str(roadmap.status)
    db_create_roadmap(
        id=roadmap.id,
        name=roadmap.name,
        version=roadmap.version,
        status=_normalize_status(status_val),
        blocked=roadmap.blocked,
        created=roadmap.created or now,
        conn=conn,
    )

    # Flat structure is now required (tracks/, sprints/, tasks/ directories)
    tracks_dir = roadmap_dir / "tracks"
    if tracks_dir.is_dir():
        # ULID flat structure - iterate flat directories
        return _load_roadmap_to_db_flat(conn, roadmap, vibey_dir, now, db_create_track, db_create_sprint, db_create_task, load_track, load_sprint, load_task)

    # Flat structure not found - error
    raise ValueError(
        f"Flat structure directories not found at {roadmap_dir}. "
        "Expected tracks/, sprints/, tasks/ directories. "
        "Run 'vibey roadmap validate-structure' to check your roadmap structure."
    )


def db_rebuild_cmd(force: bool = False) -> int:
    """Rebuild database from YAML files."""
    root_dir = Path.cwd()
    vibey_dir = root_dir / ".vibey"
    db_path = vibey_dir / "roadmap.db"

    if not db_path.exists():
        print("❌ No database found. Run 'vibey roadmap db init' first.")
        return 1

    # Check for uncommitted changes
    if not force:
        try:
            from vibey.roadmap.database.connection import get_connection, close_all_connections

            conn = get_connection(db_path=db_path)
            row = conn.execute("SELECT is_dirty FROM database_state WHERE id = 1").fetchone()

            if row and row[0]:
                print("❌ Database has uncommitted changes!")
                print("   Use --force to discard changes and rebuild")
                print("   Or commit your changes first")
                return 1
        except Exception:
            pass  # If we can't check, proceed with caution
        finally:
            # Close all connections before deleting the database file
            # This ensures the new init gets a fresh connection
            close_all_connections()
    else:
        # Even when forcing, close any existing connections
        from vibey.roadmap.database.connection import close_all_connections
        close_all_connections()

    print("🔄 Rebuilding database from YAML...")

    # Backup current database
    backup_path = db_path.with_suffix('.db.bak')
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"   Backup created: {backup_path}")

    # Remove and reinitialize
    db_path.unlink()

    result = db_init_cmd(force=True)

    if result == 0:
        print("\n✅ Database rebuilt successfully")
        # Remove backup on success
        backup_path.unlink()
    else:
        print("\n❌ Rebuild failed, restoring backup...")
        shutil.move(backup_path, db_path)

    return result


def db_dump_cmd(force: bool = False, verbose: bool = False) -> int:
    """Dump database state to YAML files."""
    root_dir = Path.cwd()
    vibey_dir = root_dir / ".vibey"
    db_path = vibey_dir / "roadmap.db"
    roadmap_dir = vibey_dir / "roadmap"

    if not db_path.exists():
        print("❌ Database not found")
        print("   Run 'vibey roadmap db init' first")
        return 1

    print("📤 Dumping database to YAML files...")

    try:
        from vibey.roadmap.serialization.backend import SyncManager, YAMLModifiedError

        sync = SyncManager(roadmap_dir=roadmap_dir, db_path=db_path)

        # Check for external modifications
        if not force:
            modified_files = sync.check_yaml_modified()
            if modified_files:
                print("\n⚠️  YAML files were modified externally!")
                print("   Modified files:")
                for f in modified_files[:10]:
                    print(f"     - {f}")
                if len(modified_files) > 10:
                    print(f"     ... and {len(modified_files) - 10} more")
                print("\n   Options:")
                print("     vibey roadmap db dump --force  # Overwrite external changes")
                print("     vibey roadmap db rebuild       # Load external changes into DB")
                return 1

        # Perform the dump
        if verbose:
            print("\n   Loading from database...")

        # Load all data from SQLite
        roadmap = sync.sqlite_backend.load_roadmap()
        if verbose:
            print(f"   ✓ Loaded roadmap: {roadmap.name}")

        # Get all tracks
        tracks = []
        sprints = []
        tasks = []

        # Query all tracks from database
        from vibey.roadmap.database.connection import get_connection
        conn = get_connection(db_path=db_path)
        track_rows = conn.execute("SELECT id FROM tracks").fetchall()

        for track_row in track_rows:
            track = sync.sqlite_backend.load_track(track_row['id'])
            tracks.append(track)
            if verbose:
                print(f"   ✓ Loaded track: {track.id}")

            # Get sprints for this track
            sprint_rows = conn.execute(
                "SELECT id FROM sprints WHERE track_id = ?",
                (track.id,)
            ).fetchall()

            for sprint_row in sprint_rows:
                sprint = sync.sqlite_backend.load_sprint(sprint_row['id'])
                sprints.append(sprint)
                if verbose:
                    print(f"     ✓ Loaded sprint: {sprint.id}")

                # Get tasks for this sprint
                sprint_tasks = sync.sqlite_backend.load_tasks_by_sprint(sprint.id)
                tasks.extend(sprint_tasks)
                if verbose and sprint_tasks:
                    print(f"       ✓ Loaded {len(sprint_tasks)} tasks")

        if verbose:
            print(f"\n   Writing to YAML files...")

        # Save roadmap
        sync.yaml_backend.save_roadmap(roadmap)
        if verbose:
            print(f"   ✓ Saved roadmap.yaml")

        # Save tracks
        for track in tracks:
            sync.yaml_backend.save_track(track)
            if verbose:
                print(f"   ✓ Saved tracks/{track.id}.yaml")

        # Save sprints
        for sprint in sprints:
            sync.yaml_backend.save_sprint(sprint)
            if verbose:
                print(f"   ✓ Saved sprints/{sprint.id}.yaml")

        # Save tasks (grouped by sprint)
        tasks_by_sprint = {}
        for task in tasks:
            if task.sprint_id not in tasks_by_sprint:
                tasks_by_sprint[task.sprint_id] = []
            tasks_by_sprint[task.sprint_id].append(task)

        for sprint_id, sprint_tasks in tasks_by_sprint.items():
            if sprint_tasks:
                sync.yaml_backend.save_tasks(sprint_tasks)
                if verbose:
                    print(f"   ✓ Saved {len(sprint_tasks)} tasks in tasks/{sprint_id}*.yaml")

        # Update checksums and mark clean
        if verbose:
            print("\n   Updating checksums...")
        sync.store_yaml_checksums()
        sync.mark_db_clean()

        # Summary
        print(f"\n✅ Dump complete!")
        print(f"   Tracks:  {len(tracks)}")
        print(f"   Sprints: {len(sprints)}")
        print(f"   Tasks:   {len(tasks)}")
        print(f"\n   Database marked clean (is_dirty = 0)")

        return 0

    except YAMLModifiedError as e:
        print(f"\n❌ {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Dump failed: {e}")
        import traceback
        if verbose:
            traceback.print_exc()
        return 1


def db_status_cmd(verbose: bool = False) -> int:
    """Show database status."""
    root_dir = Path.cwd()
    vibey_dir = root_dir / ".vibey"
    db_path = vibey_dir / "roadmap.db"

    print("🗄️  Database Status")
    print("=" * 50)

    # Check if database exists
    if not db_path.exists():
        print(f"\n❌ Database not found")
        print(f"   Expected: {db_path}")
        print(f"\n   Run 'vibey roadmap db init' to create")
        return 1

    print(f"\n📍 Location: {db_path}")
    print(f"   Size: {db_path.stat().st_size / 1024:.1f} KB")

    try:
        from vibey.roadmap.database.connection import get_connection, get_database_info
        from vibey.roadmap.database.schema import get_schema_version, validate_schema

        conn = get_connection(db_path=db_path)

        # Schema version
        version = get_schema_version(conn=conn)
        print(f"\n📋 Schema Version: {version}")

        # Database state
        row = conn.execute("""
            SELECT is_dirty, last_yaml_load, source_commit
            FROM database_state WHERE id = 1
        """).fetchone()

        if row:
            is_dirty = row[0]
            last_load = row[1]
            source_commit = row[2]

            dirty_status = "⚠️  Yes (uncommitted changes)" if is_dirty else "✅ No"
            print(f"\n🔄 Dirty Flag: {dirty_status}")
            print(f"   Last YAML Load: {last_load or 'Never'}")
            if source_commit:
                print(f"   Source Commit: {source_commit[:8]}")

        # Row counts
        print("\n📊 Data Counts:")
        for table in ['roadmaps', 'tracks', 'sprints', 'tasks']:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"   {table.capitalize():12} {count:>6}")

        if verbose:
            # Validate schema
            print("\n🔍 Schema Validation:")
            validation = validate_schema(conn=conn)
            if validation['valid']:
                print("   ✅ Schema is valid")
            else:
                print("   ❌ Schema validation failed:")
                for issue in validation.get('missing_tables', []):
                    print(f"      Missing table: {issue}")

            # Database info
            info = get_database_info(conn=conn)
            print(f"\n⚙️  Database Info:")
            print(f"   Journal Mode: {info.get('journal_mode', 'unknown')}")
            print(f"   Page Size: {info.get('page_size', 'unknown')}")
            print(f"   Tables: {info.get('table_count', 'unknown')}")

        print()
        return 0

    except Exception as e:
        print(f"\n❌ Error reading database: {e}")
        return 1


def db_backup_cmd(output_path: Optional[str] = None) -> int:
    """Create a database backup."""
    from datetime import datetime
    import shutil

    root_dir = Path.cwd()
    vibey_dir = root_dir / ".vibey"
    db_path = vibey_dir / "roadmap.db"

    if not db_path.exists():
        print("❌ No database found to backup")
        return 1

    # Generate backup path
    if output_path:
        backup_path = Path(output_path)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = vibey_dir / f"roadmap.db.backup.{timestamp}"

    # Create backup
    try:
        shutil.copy2(db_path, backup_path)
        size_kb = backup_path.stat().st_size / 1024
        print(f"✅ Backup created: {backup_path}")
        print(f"   Size: {size_kb:.1f} KB")
        return 0
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return 1


# ============================================================================
# Database Query Commands
# ============================================================================

def db_query_blocked_cmd(track_filter: Optional[str] = None, verbose: bool = False) -> int:
    """Query all blocked tasks with blocker information."""
    root_dir = Path.cwd()
    db_path = root_dir / ".vibey" / "roadmap.db"

    if not db_path.exists():
        print("❌ No database found. Run 'vibey roadmap db init' first.")
        return 1

    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # Query blocked tasks
        query = """
            SELECT t.id, t.title, t.status, t.track_id, t.sprint_id,
                   eb.blocker_id, eb.blocker_type, eb.reason
            FROM tasks t
            JOIN entity_blocked_by eb ON eb.blocked_type = 'task' AND eb.blocked_id = t.id
            WHERE t.blocked = 1
        """
        params = []
        if track_filter:
            query += " AND t.track_id = ?"
            params.append(track_filter)
        query += " ORDER BY t.track_id, t.sprint_id, t.id"

        rows = conn.execute(query, params).fetchall()

        if not rows:
            print("✅ No blocked tasks found!")
            return 0

        print(f"🚧 Blocked Tasks ({len(rows)} blockers)")
        print("=" * 60)

        current_task = None
        for row in rows:
            if row['id'] != current_task:
                current_task = row['id']
                print(f"\n📋 {row['title']}")
                print(f"   ID: {row['id']}")
                print(f"   Status: {row['status']}")
                if verbose:
                    print(f"   Track: {row['track_id']}")
                    print(f"   Sprint: {row['sprint_id']}")
                print("   Blocked by:")

            blocker_info = f"     - {row['blocker_type']}: {row['blocker_id']}"
            if row['reason'] and verbose:
                blocker_info += f" ({row['reason']})"
            print(blocker_info)

        print()
        return 0

    except Exception as e:
        print(f"❌ Query failed: {e}")
        return 1


def db_query_progress_cmd(group_by: str = 'track') -> int:
    """Query progress grouped by track, sprint, or status."""
    root_dir = Path.cwd()
    db_path = root_dir / ".vibey" / "roadmap.db"

    if not db_path.exists():
        print("❌ No database found. Run 'vibey roadmap db init' first.")
        return 1

    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        if group_by == 'track':
            # Try computed view first, fallback to direct query
            try:
                rows = conn.execute("""
                    SELECT track_id, tasks_total, tasks_completed, completion_percent
                    FROM v_track_progress
                    ORDER BY track_id
                """).fetchall()
            except sqlite3.OperationalError:
                # Fallback query
                rows = conn.execute("""
                    SELECT track_id,
                           COUNT(*) as tasks_total,
                           SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as tasks_completed,
                           ROUND(SUM(CASE WHEN status = 'completed' THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 1) as completion_percent
                    FROM tasks
                    GROUP BY track_id
                    ORDER BY track_id
                """).fetchall()

            print("📊 Progress by Track")
            print("=" * 60)
            for row in rows:
                pct = row['completion_percent'] or 0
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                print(f"{row['track_id'][:30]:<30} [{bar}] {pct:>5.1f}% ({row['tasks_completed']}/{row['tasks_total']})")

        elif group_by == 'sprint':
            try:
                rows = conn.execute("""
                    SELECT sprint_id, track_id, tasks_total, tasks_completed, completion_percent
                    FROM v_sprint_progress
                    ORDER BY track_id, sprint_id
                """).fetchall()
            except sqlite3.OperationalError:
                rows = conn.execute("""
                    SELECT sprint_id, track_id,
                           COUNT(*) as tasks_total,
                           SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as tasks_completed,
                           ROUND(SUM(CASE WHEN status = 'completed' THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 1) as completion_percent
                    FROM tasks
                    GROUP BY sprint_id, track_id
                    ORDER BY track_id, sprint_id
                """).fetchall()

            print("📊 Progress by Sprint")
            print("=" * 70)
            current_track = None
            for row in rows:
                if row['track_id'] != current_track:
                    current_track = row['track_id']
                    print(f"\n📁 {current_track}")
                pct = row['completion_percent'] or 0
                bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
                print(f"  {row['sprint_id']:<35} [{bar}] {pct:>5.1f}% ({row['tasks_completed']}/{row['tasks_total']})")

        elif group_by == 'status':
            rows = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM tasks
                GROUP BY status
                ORDER BY
                    CASE status
                        WHEN 'not_started' THEN 1
                        WHEN 'in_progress' THEN 2
                        WHEN 'completed' THEN 3
                        ELSE 4
                    END
            """).fetchall()

            total = sum(r['count'] for r in rows)
            print("📊 Tasks by Status")
            print("=" * 40)
            for row in rows:
                pct = (row['count'] / total * 100) if total > 0 else 0
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                print(f"{row['status']:<15} [{bar}] {row['count']:>4} ({pct:.1f}%)")

        print()
        return 0

    except Exception as e:
        print(f"❌ Query failed: {e}")
        return 1


def db_query_deps_cmd(entity_id: str, direction: str = 'both') -> int:
    """Query dependency chain for an entity."""
    root_dir = Path.cwd()
    db_path = root_dir / ".vibey" / "roadmap.db"

    if not db_path.exists():
        print("❌ No database found. Run 'vibey roadmap db init' first.")
        return 1

    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # Determine entity type
        if '-task-' in entity_id:
            entity_type = 'task'
        elif any(entity_id.endswith(f'-{i}') for i in range(100)):
            entity_type = 'sprint'
        else:
            entity_type = 'track'

        print(f"🔗 Dependency Chain for {entity_type}: {entity_id}")
        print("=" * 60)

        if direction in ('up', 'both'):
            # What this entity depends on
            deps = conn.execute("""
                SELECT dependency_type, dependency_id, reason
                FROM entity_depends_on
                WHERE dependent_type = ? AND dependent_id = ?
            """, (entity_type, entity_id)).fetchall()

            print(f"\n⬆️  Dependencies ({len(deps)}):")
            if deps:
                for d in deps:
                    reason = f" - {d['reason']}" if d['reason'] else ""
                    print(f"   {d['dependency_type']}: {d['dependency_id']}{reason}")
            else:
                print("   (none)")

        if direction in ('down', 'both'):
            # What depends on this entity
            dependents = conn.execute("""
                SELECT dependent_type, dependent_id, reason
                FROM entity_depends_on
                WHERE dependency_type = ? AND dependency_id = ?
            """, (entity_type, entity_id)).fetchall()

            print(f"\n⬇️  Dependents ({len(dependents)}):")
            if dependents:
                for d in dependents:
                    reason = f" - {d['reason']}" if d['reason'] else ""
                    print(f"   {d['dependent_type']}: {d['dependent_id']}{reason}")
            else:
                print("   (none)")

        # Also show blocks/blocked_by
        if direction in ('up', 'both'):
            blockers = conn.execute("""
                SELECT blocker_type, blocker_id, reason
                FROM entity_blocked_by
                WHERE blocked_type = ? AND blocked_id = ?
            """, (entity_type, entity_id)).fetchall()

            print(f"\n🚫 Blocked by ({len(blockers)}):")
            if blockers:
                for b in blockers:
                    reason = f" - {b['reason']}" if b['reason'] else ""
                    print(f"   {b['blocker_type']}: {b['blocker_id']}{reason}")
            else:
                print("   (none)")

        if direction in ('down', 'both'):
            blocks = conn.execute("""
                SELECT blocked_type, blocked_id, reason
                FROM entity_blocks
                WHERE blocker_type = ? AND blocker_id = ?
            """, (entity_type, entity_id)).fetchall()

            print(f"\n🔒 Blocks ({len(blocks)}):")
            if blocks:
                for b in blocks:
                    reason = f" - {b['reason']}" if b['reason'] else ""
                    print(f"   {b['blocked_type']}: {b['blocked_id']}{reason}")
            else:
                print("   (none)")

        print()
        return 0

    except Exception as e:
        print(f"❌ Query failed: {e}")
        return 1


def db_query_stats_cmd() -> int:
    """Query overall roadmap statistics."""
    root_dir = Path.cwd()
    db_path = root_dir / ".vibey" / "roadmap.db"

    if not db_path.exists():
        print("❌ No database found. Run 'vibey roadmap db init' first.")
        return 1

    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        print("📊 Roadmap Statistics")
        print("=" * 50)

        # Entity counts
        tracks = conn.execute("SELECT COUNT(*) as c FROM tracks").fetchone()['c']
        sprints = conn.execute("SELECT COUNT(*) as c FROM sprints").fetchone()['c']
        tasks = conn.execute("SELECT COUNT(*) as c FROM tasks").fetchone()['c']

        print(f"\n📁 Entity Counts:")
        print(f"   Tracks:  {tracks}")
        print(f"   Sprints: {sprints}")
        print(f"   Tasks:   {tasks}")

        # Task status breakdown
        status_rows = conn.execute("""
            SELECT status, COUNT(*) as count
            FROM tasks
            GROUP BY status
            ORDER BY count DESC
        """).fetchall()

        print(f"\n📋 Tasks by Status:")
        for row in status_rows:
            pct = (row['count'] / tasks * 100) if tasks > 0 else 0
            print(f"   {row['status']:<15}: {row['count']:>4} ({pct:.1f}%)")

        # Completion rate
        completed = conn.execute(
            "SELECT COUNT(*) as c FROM tasks WHERE status = 'completed'"
        ).fetchone()['c']
        completion_rate = (completed / tasks * 100) if tasks > 0 else 0

        print(f"\n✅ Overall Completion Rate: {completion_rate:.1f}%")
        bar = "█" * int(completion_rate / 5) + "░" * (20 - int(completion_rate / 5))
        print(f"   [{bar}]")

        # Blocked items
        blocked_tasks = conn.execute(
            "SELECT COUNT(*) as c FROM tasks WHERE blocked = 1"
        ).fetchone()['c']
        blocked_sprints = conn.execute(
            "SELECT COUNT(*) as c FROM sprints WHERE blocked = 1"
        ).fetchone()['c']
        blocked_tracks = conn.execute(
            "SELECT COUNT(*) as c FROM tracks WHERE blocked = 1"
        ).fetchone()['c']

        print(f"\n🚧 Blocked Items:")
        print(f"   Tracks:  {blocked_tracks}")
        print(f"   Sprints: {blocked_sprints}")
        print(f"   Tasks:   {blocked_tasks}")

        # Tasks by priority
        priority_rows = conn.execute("""
            SELECT priority, COUNT(*) as count
            FROM tasks
            GROUP BY priority
            ORDER BY
                CASE priority
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5
                END
        """).fetchall()

        print(f"\n⚡ Tasks by Priority:")
        for row in priority_rows:
            print(f"   {row['priority']:<10}: {row['count']:>4}")

        print()
        return 0

    except Exception as e:
        print(f"❌ Query failed: {e}")
        return 1


def db_validate_cmd(level: str = 'full', compare: bool = False, verbose: bool = False) -> int:
    """Validate database integrity and consistency."""
    import sqlite3

    root_dir = Path.cwd()
    db_path = root_dir / ".vibey" / "roadmap.db"

    if not db_path.exists():
        print("❌ Database not found")
        print("   Run 'vibey roadmap db init' to create database")
        return 1

    errors = []
    warnings = []

    print("=" * 60)
    print("🔍 Database Validation")
    print("=" * 60)

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # Schema validation
        if level in ('schema', 'full'):
            print("\n📋 Schema Validation...")

            # Check required tables
            required_tables = [
                'roadmaps', 'tracks', 'sprints', 'tasks',
                'entity_depends_on', 'entity_blocked_by', 'entity_blocks',
                'deliverables', 'commits', 'quality_gates',
                'database_state', 'yaml_checksums'
            ]

            existing = {r['name'] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}

            missing = set(required_tables) - existing
            if missing:
                errors.append(f"Missing tables: {', '.join(sorted(missing))}")
                print(f"   ❌ Missing {len(missing)} tables")
            else:
                print(f"   ✅ All {len(required_tables)} required tables exist")

            # Check schema version
            try:
                row = conn.execute(
                    "SELECT schema_version FROM database_state WHERE id = 1"
                ).fetchone()
                if row:
                    print(f"   ✅ Schema version: {row['schema_version']}")
                else:
                    errors.append("Database state not initialized")
            except sqlite3.OperationalError:
                errors.append("database_state table not accessible")

            # SQLite integrity check
            result = conn.execute("PRAGMA integrity_check(100)").fetchall()
            if len(result) == 1 and result[0][0] == "ok":
                print("   ✅ SQLite integrity check passed")
            else:
                for row in result:
                    errors.append(f"Integrity issue: {row[0]}")
                print(f"   ❌ Integrity check found {len(result)} issues")

        # Reference validation
        if level in ('references', 'full'):
            print("\n🔗 Reference Validation...")

            # Enable foreign key checking
            conn.execute("PRAGMA foreign_keys = ON")

            # Check foreign key violations
            violations = conn.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                for v in violations[:10]:  # Show first 10
                    errors.append(f"FK violation in {v[0]}: rowid {v[1]} -> {v[2]}")
                if len(violations) > 10:
                    errors.append(f"... and {len(violations) - 10} more FK violations")
                print(f"   ❌ {len(violations)} foreign key violations")
            else:
                print("   ✅ All foreign key relationships valid")

            # Check orphan tasks (tasks with invalid sprint_id)
            orphan_tasks = conn.execute("""
                SELECT t.id FROM tasks t
                LEFT JOIN sprints s ON t.sprint_id = s.id
                WHERE s.id IS NULL
            """).fetchall()
            if orphan_tasks:
                for t in orphan_tasks[:5]:
                    warnings.append(f"Orphan task: {t['id']}")
                print(f"   ⚠️  {len(orphan_tasks)} orphan tasks found")
            else:
                print("   ✅ No orphan tasks")

            # Check orphan sprints
            orphan_sprints = conn.execute("""
                SELECT s.id FROM sprints s
                LEFT JOIN tracks tr ON s.track_id = tr.id
                WHERE tr.id IS NULL
            """).fetchall()
            if orphan_sprints:
                for s in orphan_sprints[:5]:
                    warnings.append(f"Orphan sprint: {s['id']}")
                print(f"   ⚠️  {len(orphan_sprints)} orphan sprints found")
            else:
                print("   ✅ No orphan sprints")

        # Computed values validation
        if level in ('computed', 'full'):
            print("\n📊 Computed Values Validation...")

            # Count entities
            roadmap_count = conn.execute("SELECT COUNT(*) as c FROM roadmaps").fetchone()['c']
            track_count = conn.execute("SELECT COUNT(*) as c FROM tracks").fetchone()['c']
            sprint_count = conn.execute("SELECT COUNT(*) as c FROM sprints").fetchone()['c']
            task_count = conn.execute("SELECT COUNT(*) as c FROM tasks").fetchone()['c']

            print(f"   📋 Roadmaps: {roadmap_count}")
            print(f"   📋 Tracks: {track_count}")
            print(f"   📋 Sprints: {sprint_count}")
            print(f"   📋 Tasks: {task_count}")

            # Task status distribution
            status_dist = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM tasks
                GROUP BY status
                ORDER BY count DESC
            """).fetchall()

            print(f"\n   📈 Task Status Distribution:")
            for row in status_dist:
                pct = 100.0 * row['count'] / task_count if task_count > 0 else 0
                print(f"      {row['status']:<15}: {row['count']:>4} ({pct:.1f}%)")

            # Count sprints with tasks
            sprints_with_tasks = conn.execute("""
                SELECT COUNT(DISTINCT sprint_id) as c FROM tasks
            """).fetchone()['c']
            sprints_without_tasks = sprint_count - sprints_with_tasks

            if sprints_without_tasks > 0:
                warnings.append(f"{sprints_without_tasks} sprints have no tasks")
                print(f"\n   ⚠️  {sprints_without_tasks} sprints have no tasks")
            else:
                print(f"\n   ✅ All sprints have at least one task")

        # Compare with YAML
        if compare:
            print("\n📄 DB vs YAML Comparison...")

            from vibey.roadmap.serialization.backend import SyncManager
            sync = SyncManager(
                roadmap_dir=root_dir / ".vibey" / "roadmap",
                db_path=db_path
            )

            modified_files = sync.check_yaml_modified()
            if modified_files:
                print(f"   ⚠️  {len(modified_files)} YAML files modified since last load:")
                for f in modified_files[:10]:
                    print(f"      - {f}")
                if len(modified_files) > 10:
                    print(f"      ... and {len(modified_files) - 10} more")
                warnings.append(f"{len(modified_files)} YAML files modified")
            else:
                print("   ✅ Database and YAML files are in sync")

            is_dirty = sync.is_db_dirty()
            if is_dirty:
                print("   ⚠️  Database has uncommitted changes")
                warnings.append("Database dirty flag set")
            else:
                print("   ✅ No uncommitted database changes")

        conn.close()

        # Summary
        print("\n" + "=" * 60)
        if errors:
            print(f"❌ Validation FAILED with {len(errors)} errors")
            if verbose:
                for e in errors:
                    print(f"   ❌ {e}")
            return 1
        elif warnings:
            print(f"⚠️  Validation PASSED with {len(warnings)} warnings")
            if verbose:
                for w in warnings:
                    print(f"   ⚠️ {w}")
            return 0
        else:
            print("✅ Validation PASSED - no issues found")
            return 0

    except Exception as e:
        print(f"\n❌ Validation error: {e}")
        return 1


def db_config_cmd() -> int:
    """Show current backend configuration."""
    from vibey.roadmap.serialization.backend import (
        load_roadmap_config,
        validate_database,
        get_backend,
        EXPECTED_SCHEMA_VERSION,
    )

    root_dir = Path.cwd()
    config = load_roadmap_config(root_dir)

    db_path_str = config["database"]["path"]
    if not db_path_str.startswith("/"):
        db_path = root_dir / db_path_str
    else:
        db_path = Path(db_path_str)

    print("=" * 60)
    print("⚙️  Backend Configuration")
    print("=" * 60)

    # Config source
    config_path = root_dir / ".vibey" / "config" / "roadmap.yaml"
    if config_path.exists():
        print(f"\n📁 Config file: {config_path}")
    else:
        print(f"\n📁 Config file: (using defaults)")

    # Mode
    print(f"\n🔧 Backend Mode: {config['backend']}")
    if config['backend'] == 'auto':
        print("   Auto mode selects SQLite if valid, else YAML")

    # Database settings
    print(f"\n📊 Database Settings:")
    print(f"   Path: {db_path}")
    print(f"   Validate on load: {config['database']['validate_on_load']}")
    print(f"   Fallback to YAML: {config['database']['fallback_to_yaml']}")
    print(f"   Expected schema: {EXPECTED_SCHEMA_VERSION}")

    # Database status
    print(f"\n🗄️  Database Status:")
    if db_path.exists():
        print(f"   File exists: ✅")
        is_valid, error = validate_database(db_path)
        if is_valid:
            print(f"   Validation: ✅ Passed")
        else:
            print(f"   Validation: ❌ {error}")
    else:
        print(f"   File exists: ❌")
        print(f"   Run 'vibey roadmap db init' to create database")

    # Effective backend
    try:
        backend = get_backend(root_dir=root_dir)
        backend_type = type(backend).__name__
        print(f"\n🎯 Effective Backend: {backend_type}")
    except Exception as e:
        print(f"\n🎯 Effective Backend: ❌ Error: {e}")

    print()
    return 0


def validate_structure_cmd(fix: bool = False) -> int:
    """Validate roadmap directory structure is flat (no ULID directories).

    Checks that:
    - No hierarchical ULID directories exist (01KC.../01KC.../...)
    - Required flat structure directories exist (tracks/, sprints/, tasks/)

    Args:
        fix: If True, automatically delete any hierarchical ULID directories

    Returns:
        0 if validation passes, 1 if issues found
    """
    import shutil

    root_dir = Path.cwd()
    roadmap_dir = root_dir / ".vibey" / "roadmap"

    if not roadmap_dir.exists():
        print("❌ Roadmap directory not found")
        print("   Run 'vibey roadmap init' first")
        return 1

    print("=" * 60)
    print("🔍 Structure Validation")
    print("=" * 60)

    issues = []
    ulid_dirs = []

    # Check for hierarchical ULID directories
    for item in roadmap_dir.iterdir():
        if item.is_dir() and item.name.startswith('01'):
            # ULID directories start with '01' (timestamp prefix)
            ulid_dirs.append(item)
            issues.append(f"Hierarchical directory found: {item.name}")

    # Verify flat structure exists
    required_dirs = ['tracks', 'sprints', 'tasks']
    print("\n📁 Checking flat structure directories...")
    for dir_name in required_dirs:
        dir_path = roadmap_dir / dir_name
        if not dir_path.exists():
            issues.append(f"Missing required directory: {dir_name}/")
            print(f"   ❌ {dir_name}/ - missing")
        else:
            count = len(list(dir_path.glob('*.yaml')))
            print(f"   ✅ {dir_name}/ - {count} files")

    # Check for hierarchical directories
    print("\n📂 Checking for hierarchical ULID directories...")
    if ulid_dirs:
        print(f"   ❌ Found {len(ulid_dirs)} hierarchical directories")
        for d in ulid_dirs[:5]:  # Show first 5
            print(f"      {d.name}/")
        if len(ulid_dirs) > 5:
            print(f"      ... and {len(ulid_dirs) - 5} more")

        if fix:
            print("\n🔧 Fixing issues...")
            for d in ulid_dirs:
                try:
                    shutil.rmtree(d)
                    print(f"   ✅ Deleted: {d.name}/")
                except Exception as e:
                    print(f"   ❌ Failed to delete {d.name}/: {e}")

            # Re-check after fix
            remaining = [d for d in roadmap_dir.iterdir() if d.is_dir() and d.name.startswith('01')]
            if not remaining:
                print("\n✅ All hierarchical directories removed")
                # Remove the hierarchical issues since they're fixed
                issues = [i for i in issues if not i.startswith("Hierarchical directory")]
    else:
        print("   ✅ No hierarchical directories found")

    # Report results
    print("\n" + "=" * 60)
    if issues:
        print("❌ Structure validation FAILED")
        for issue in issues:
            print(f"   - {issue}")
        if ulid_dirs and not fix:
            print("\n💡 Run with --fix to automatically delete hierarchical directories")
        return 1
    else:
        print("✅ Structure validation PASSED")
        print("   - No hierarchical ULID directories")
        print("   - Flat structure verified: tracks/, sprints/, tasks/")
        return 0


def extract_embedded_cmd(dry_run: bool = True, verbose: bool = True) -> int:
    """Extract embedded tasks from sprint files to standalone task files.

    Scans all sprint YAML files for embedded tasks[] arrays and creates
    individual task files in the flat .vibey/roadmap/tasks/ directory.

    Args:
        dry_run: If True, only show what would be extracted without creating files
        verbose: If True, print detailed output

    Returns:
        0 if successful, 1 if errors occurred
    """
    from vibey.operations.migrations.extract_embedded_tasks import (
        extract_embedded_tasks,
    )

    root_dir = Path.cwd()
    roadmap_dir = root_dir / ".vibey" / "roadmap"

    if not roadmap_dir.exists():
        print("❌ Roadmap directory not found")
        print("   Run 'vibey roadmap init' first")
        return 1

    stats = extract_embedded_tasks(
        roadmap_dir=roadmap_dir,
        dry_run=dry_run,
        verbose=verbose,
    )

    if stats.get("errors"):
        return 1

    return 0


# ============================================================================
# Format Migration Commands
# ============================================================================

def migrate_format_cmd(
    dry_run: bool = False,
    backup: bool = True,
    path: Optional[str] = None,
    force: bool = False,
    verbose: bool = False,
) -> int:
    """
    Migrate YAML files from v1 format to v2 format.

    V1 format uses legacy field names:
    - created, started, completed → created_at, started_at, completed_at
    - assigned_agent (singular) → assigned_agents (list)
    - title → name
    - sprint_id/track_id/roadmap_id → parent_ref
    - blocked_by (list of IDs) → criteria with CompletableTarget

    V2 format uses:
    - format_version: 'v2'
    - ticket_type field
    - parent_ref for hierarchy
    - criteria for unified blocking
    - _at suffix on timestamps
    """
    import shutil
    from datetime import datetime, timezone

    import yaml

    # Import format detection from yaml_loader
    from vibey.roadmap.serialization.yaml_loader import detect_yaml_format

    root_dir = Path.cwd()
    roadmap_dir = Path(path) if path else root_dir / ".vibey" / "roadmap"

    if not roadmap_dir.exists():
        print(f"❌ Roadmap directory not found: {roadmap_dir}")
        return 1

    print("🔄 Scanning YAML files for format migration...")
    print(f"   Directory: {roadmap_dir}")
    print()

    # Find all YAML files
    yaml_files = list(roadmap_dir.glob("**/*.yaml"))
    yaml_files = [f for f in yaml_files if f.name not in ('.sync-manifest.yaml',)]

    # Categorize files by format
    v1_files = []
    v2_files = []
    error_files = []

    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)

            if data is None:
                continue

            # Get the root key (task, sprint, track, roadmap)
            root_keys = ['task', 'sprint', 'track', 'roadmap']
            entity_data = None
            entity_type = None
            for key in root_keys:
                if key in data:
                    entity_data = data[key]
                    entity_type = key
                    break

            if entity_data is None:
                continue

            # Detect format
            format_version = detect_yaml_format(entity_data)

            if format_version == 'v1':
                v1_files.append((yaml_file, entity_type, entity_data))
            else:
                v2_files.append(yaml_file)

        except Exception as e:
            error_files.append((yaml_file, str(e)))

    # Report discovery results
    print("📊 Discovery Results:")
    print(f"   Files scanned:  {len(yaml_files)}")
    print(f"   V1 format:      {len(v1_files)} (need migration)")
    print(f"   V2 format:      {len(v2_files)} (already migrated)")
    print(f"   Parse errors:   {len(error_files)}")
    print()

    if error_files and verbose:
        print("⚠️  Files with parse errors:")
        for path, error in error_files[:5]:
            print(f"   {path.relative_to(roadmap_dir)}: {error[:50]}")
        if len(error_files) > 5:
            print(f"   ... and {len(error_files) - 5} more")
        print()

    if not v1_files:
        print("✅ All files already in v2 format. Nothing to migrate.")
        return 0

    # Show what will change
    if dry_run or verbose:
        print("📝 Migration Preview:")
        print("-" * 60)
        for yaml_file, entity_type, entity_data in v1_files[:10]:
            rel_path = yaml_file.relative_to(roadmap_dir)
            changes = _count_field_changes(entity_type, entity_data)
            print(f"   {rel_path}: {changes} field changes")
        if len(v1_files) > 10:
            print(f"   ... and {len(v1_files) - 10} more files")
        print()

    if dry_run:
        print("🔍 Dry run complete. No files were modified.")
        print(f"   Use 'vibey roadmap migrate-format' to apply changes.")
        return 0

    # Confirm if not forced
    if not force:
        print(f"⚠️  This will modify {len(v1_files)} files.")
        if backup:
            print("   Backups will be created (.v1.bak extension)")
        response = input("   Continue? [y/N]: ").strip().lower()
        if response not in ('y', 'yes'):
            print("   Aborted.")
            return 1

    # Perform migration
    print()
    print("🔄 Migrating files...")

    migrated = 0
    failed = 0
    backup_dir = roadmap_dir / ".migration-backups" / datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, (yaml_file, entity_type, entity_data) in enumerate(v1_files):
        rel_path = yaml_file.relative_to(roadmap_dir)

        try:
            # Create backup
            if backup:
                backup_path = backup_dir / rel_path.with_suffix('.yaml.v1.bak')
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(yaml_file, backup_path)

            # Transform v1 to v2
            migrated_data = _migrate_entity_to_v2(entity_type, entity_data)

            # Write back
            with open(yaml_file, 'w') as f:
                yaml.dump({entity_type: migrated_data}, f,
                         default_flow_style=False,
                         allow_unicode=True,
                         sort_keys=False)

            migrated += 1
            if verbose:
                print(f"   [{migrated}/{len(v1_files)}] ✅ {rel_path}")
            else:
                # Progress indicator every 10 files
                if (i + 1) % 10 == 0:
                    print(f"   [{i + 1}/{len(v1_files)}] files processed...")

        except Exception as e:
            failed += 1
            print(f"   ❌ {rel_path}: {e}")

    print()
    print("=" * 60)
    print("📊 Migration Summary:")
    print(f"   Migrated:  {migrated} files")
    print(f"   Failed:    {failed} files")
    if backup:
        print(f"   Backups:   {backup_dir}")
    print()

    # Validate migrated files
    print("🔍 Validating migrated files...")
    validation_errors = 0

    for yaml_file, _, _ in v1_files[:migrated]:
        try:
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)

            # Get entity data
            for key in ['task', 'sprint', 'track', 'roadmap']:
                if key in data:
                    entity_data = data[key]
                    break

            # Verify it's now v2
            if detect_yaml_format(entity_data) != 'v2':
                validation_errors += 1
                print(f"   ⚠️  {yaml_file.relative_to(roadmap_dir)}: Still shows as v1")

        except Exception as e:
            validation_errors += 1
            print(f"   ❌ {yaml_file.relative_to(roadmap_dir)}: {e}")

    if validation_errors == 0:
        print("   ✅ All migrated files validate as v2 format")
    else:
        print(f"   ⚠️  {validation_errors} files failed validation")

    print()
    if failed == 0 and validation_errors == 0:
        print("✅ Migration complete!")
        return 0
    else:
        print("⚠️  Migration completed with errors")
        return 1


def _count_field_changes(entity_type: str, data: dict) -> int:
    """Count how many fields will change during migration."""
    changes = 0

    # Timestamp renames
    for old in ['created', 'started', 'completed']:
        if old in data:
            changes += 1

    # assigned_agent → assigned_agents
    if 'assigned_agent' in data:
        changes += 1

    # title → name (for tasks)
    if 'title' in data and entity_type == 'task':
        changes += 1

    # Hierarchy fields → parent_ref
    if any(k in data for k in ['sprint_id', 'track_id', 'roadmap_id']):
        changes += 1

    # blocked_by → criteria
    if 'blocked_by' in data and data['blocked_by']:
        changes += 1

    # Add format_version and ticket_type
    if 'format_version' not in data:
        changes += 1
    if 'ticket_type' not in data:
        changes += 1

    return changes


def _migrate_entity_to_v2(entity_type: str, data: dict) -> dict:
    """
    Transform a v1 entity dict to v2 format.

    This performs in-place field migrations:
    - Timestamp renames (created → created_at, etc.)
    - Field renames (title → name, assigned_agent → assigned_agents)
    - Hierarchy consolidation (sprint_id/track_id → parent_ref)
    - blocked_by → criteria conversion
    - Add format markers
    """
    result = dict(data)  # Copy to avoid modifying original

    # Add format markers
    result['format_version'] = 'v2'
    result['ticket_type'] = entity_type

    # Rename timestamps
    timestamp_renames = [
        ('created', 'created_at'),
        ('started', 'started_at'),
        ('completed', 'completed_at'),
    ]
    for old, new in timestamp_renames:
        if old in result:
            result[new] = result.pop(old)

    # Convert assigned_agent (singular) to assigned_agents (list)
    if 'assigned_agent' in result:
        agent = result.pop('assigned_agent')
        if agent:
            result['assigned_agents'] = [agent] if isinstance(agent, str) else agent
        else:
            result['assigned_agents'] = []

    # Convert title to name (for tasks)
    if 'title' in result and entity_type == 'task':
        result['name'] = result.pop('title')

    # Consolidate hierarchy fields to parent_ref
    hierarchy_fields = {
        'task': 'sprint_id',
        'sprint': 'track_id',
        'track': 'roadmap_id',
    }
    if entity_type in hierarchy_fields:
        parent_field = hierarchy_fields[entity_type]
        if parent_field in result:
            result['parent_ref'] = result.pop(parent_field)
            # Also remove the other hierarchy fields that are redundant
            for field in ['sprint_id', 'track_id', 'roadmap_id']:
                if field != parent_field and field in result:
                    del result[field]

    # Convert blocked_by to criteria
    if 'blocked_by' in result and result['blocked_by']:
        blocked_by = result.pop('blocked_by')
        if 'criteria' not in result:
            result['criteria'] = []

        for i, blocker_id in enumerate(blocked_by):
            if isinstance(blocker_id, str):
                criterion = {
                    'id': f"dep-{i+1}",
                    'description': f"Depends on {blocker_id}",
                    'target': {
                        'type': 'completable',
                        'target_id': blocker_id,
                    },
                    'blocks_transition_to': 'in_progress',
                    'required': True,
                }
                result['criteria'].append(criterion)
    else:
        # Remove empty blocked_by
        if 'blocked_by' in result:
            del result['blocked_by']

    # Remove deprecated fields
    deprecated_fields = ['blocked', 'dependencies', 'blocks', 'depended_on_by']
    for field in deprecated_fields:
        if field in result and not result[field]:
            del result[field]

    # Ensure criteria exists
    if 'criteria' not in result:
        result['criteria'] = []

    # Rename commits to commits_local for serialization clarity
    # (keeping internal field as 'commits' but marking for v2 output)
    if 'commits' in result:
        result['commits_local'] = result.pop('commits')

    # Same for deliverables → requirements_local
    if 'deliverables' in result:
        deliverables = result.pop('deliverables')
        if deliverables and 'requirements_local' not in result:
            result['requirements_local'] = [
                {'id': f'deliverable-{i+1}', 'description': d}
                for i, d in enumerate(deliverables)
                if isinstance(d, str)
            ]

    return result


# ============================================================================
# Documentation Migration Commands
# ============================================================================

def migrate_docs_cmd(
    dry_run: bool = False,
    path: Optional[str] = None,
    verbose: bool = False,
) -> int:
    """
    Migrate documentation fields from YAML to markdown files.

    Migrates:
    - version_strategy → VERSIONING_POLICY.md (in roadmap dir)
    - version_history → CHANGELOG.md (in repo root)
    - metadata.notes → NOTES.md (per entity directory)

    Benefits of markdown:
    - Rich formatting (headings, tables, code blocks)
    - Git-diffable content
    - Searchable with grep/ripgrep
    - Human readable without tooling
    """
    from vibey.roadmap.serialization.markdown_migration import (
        migrate_roadmap_docs,
        format_migration_report,
    )

    root_dir = Path.cwd()
    roadmap_dir = Path(path) if path else root_dir / ".vibey" / "roadmap"

    if not roadmap_dir.exists():
        print(f"❌ Roadmap directory not found: {roadmap_dir}")
        return 1

    print("📝 Migrating documentation fields to markdown files...")
    print(f"   Roadmap directory: {roadmap_dir}")
    print(f"   Repository root:   {root_dir}")
    if dry_run:
        print("   Mode:              DRY RUN (no files will be created)")
    print()

    # Run migration
    result = migrate_roadmap_docs(
        roadmap_dir=roadmap_dir,
        repo_root=root_dir,
        dry_run=dry_run,
        verbose=verbose,
    )

    # Print report
    report = format_migration_report(result, verbose=verbose)
    print(report)

    if result.total_errors > 0:
        print("\n❌ Migration completed with errors")
        return 1
    elif result.total_migrated > 0:
        if dry_run:
            print("\n✅ Dry run complete. Run without --dry-run to apply changes.")
        else:
            print("\n✅ Migration complete!")
            print("\nNext steps:")
            print("  1. Review the created markdown files")
            print("  2. git add the new .md files")
            print("  3. Commit with: git commit -m 'docs: Migrate YAML docs to markdown'")
        return 0
    else:
        print("\n✅ Nothing to migrate (files already exist or no source data)")
        return 0


# ============================================================================
# Session Commands
# ============================================================================

def session_start_cmd(
    name: Optional[str] = None,
    goals: Optional[list] = None,
    track_id: Optional[str] = None,
    sprint_id: Optional[str] = None,
    task_ids: Optional[list] = None,
) -> int:
    """Start a new coding session."""
    from vibey.operations.roadmap.session_manager import SessionManager

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        manager = SessionManager(roadmap_path)
        session = manager.start_session(
            name=name,
            goals=goals,
            track_id=track_id,
            sprint_id=sprint_id,
            task_ids=task_ids,
        )

        print(format_success(f"Session started: {session.id}"))
        print(f"\n  Name: {session.name}")
        print(f"  Status: {session.status.value}")
        if session.branch:
            print(f"  Branch: {session.branch}")
        if session.goals:
            print(f"  Goals:")
            for goal in session.goals:
                print(f"    - {goal}")
        if session.track_id:
            print(f"  Track: {session.track_id}")
        if session.sprint_id:
            print(f"  Sprint: {session.sprint_id}")

        return 0
    except ValueError as e:
        print(format_error(str(e)))
        return 1
    except Exception as e:
        print(format_error(f"Failed to start session: {e}"))
        return 1


def session_end_cmd(
    session_id: Optional[str] = None,
    summary: Optional[str] = None,
    status: str = "completed",
) -> int:
    """End the current or specified session."""
    from vibey.operations.roadmap.session_manager import SessionManager
    from vibey.roadmap.models.session import SessionStatus

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        manager = SessionManager(roadmap_path)
        session_status = SessionStatus.COMPLETED if status == "completed" else SessionStatus.ABANDONED
        session = manager.end_session(
            session_id=session_id,
            summary=summary,
            status=session_status,
        )

        status_msg = "✅ completed" if session.status == SessionStatus.COMPLETED else "⚠️ abandoned"
        print(format_success(f"Session ended: {session.id}"))
        print(f"\n  Name: {session.name}")
        print(f"  Status: {status_msg}")
        if session.summary:
            print(f"  Summary: {session.summary}")
        if session.stats:
            print(f"\n  Statistics:")
            print(f"    Duration: {session.stats.duration_seconds // 60} minutes")
            print(f"    Events: {session.stats.events_count}")
            print(f"    Decisions: {session.stats.decisions_count}")
            print(f"    Commits: {session.stats.commits_count}")

        return 0
    except ValueError as e:
        print(format_error(str(e)))
        return 1
    except Exception as e:
        print(format_error(f"Failed to end session: {e}"))
        return 1


def session_pause_cmd(session_id: Optional[str] = None) -> int:
    """Pause the current or specified session."""
    from vibey.operations.roadmap.session_manager import SessionManager

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        manager = SessionManager(roadmap_path)
        session = manager.pause_session(session_id=session_id)

        print(format_success(f"Session paused: {session.id}"))
        print(f"\n  Name: {session.name}")
        print(f"  Status: {session.status.value}")
        print(f"  Paused at: {session.paused}")

        return 0
    except ValueError as e:
        print(format_error(str(e)))
        return 1
    except Exception as e:
        print(format_error(f"Failed to pause session: {e}"))
        return 1


def session_resume_cmd(session_id: str) -> int:
    """Resume a paused session."""
    from vibey.operations.roadmap.session_manager import SessionManager

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        manager = SessionManager(roadmap_path)
        session = manager.resume_session(session_id=session_id)

        print(format_success(f"Session resumed: {session.id}"))
        print(f"\n  Name: {session.name}")
        print(f"  Status: {session.status.value}")
        if session.branch:
            print(f"  Branch: {session.branch}")

        return 0
    except ValueError as e:
        print(format_error(str(e)))
        return 1
    except Exception as e:
        print(format_error(f"Failed to resume session: {e}"))
        return 1


def session_status_cmd() -> int:
    """Show the current active session status."""
    from vibey.operations.roadmap.session_manager import SessionManager

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        manager = SessionManager(roadmap_path)
        session = manager.get_active_session()

        if not session:
            print("No active session.")
            print("\nStart a new session with: vibey session start")
            return 0

        print(f"🎯 Active Session: {session.name}")
        print(f"\n  ID: {session.id}")
        print(f"  Status: {session.status.value}")
        print(f"  Started: {session.started}")
        if session.branch:
            print(f"  Branch: {session.branch}")
        if session.goals:
            print(f"  Goals:")
            for goal in session.goals:
                print(f"    - {goal}")
        if session.track_id:
            print(f"  Track: {session.track_id}")
        if session.sprint_id:
            print(f"  Sprint: {session.sprint_id}")
        if session.task_ids:
            print(f"  Tasks: {len(session.task_ids)} associated")
        if session.events:
            print(f"  Events: {len(session.events)} logged")
        if session.decisions:
            print(f"  Decisions: {len(session.decisions)} recorded")
        if session.commits:
            print(f"  Commits: {len(session.commits)} associated")

        return 0
    except Exception as e:
        print(format_error(f"Failed to get session status: {e}"))
        return 1


def session_show_cmd(session_id: str) -> int:
    """Show detailed information about a specific session."""
    from vibey.operations.roadmap.session_manager import SessionManager

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        manager = SessionManager(roadmap_path)
        session = manager.get_session(session_id)

        if not session:
            print(format_error(f"Session not found: {session_id}"))
            return 1

        status_icon = {
            "active": "🟢",
            "paused": "⏸️",
            "completed": "✅",
            "abandoned": "❌",
        }.get(session.status.value, "⚪")

        print(f"{status_icon} Session: {session.name}")
        print(f"\n  ID: {session.id}")
        print(f"  Status: {session.status.value}")
        print(f"  Created: {session.created}")
        if session.started:
            print(f"  Started: {session.started}")
        if session.paused:
            print(f"  Paused: {session.paused}")
        if session.ended:
            print(f"  Ended: {session.ended}")

        # Git info
        if session.branch or session.start_commit:
            print(f"\n  Git:")
            if session.branch:
                print(f"    Branch: {session.branch}")
            if session.start_commit:
                print(f"    Start Commit: {session.start_commit[:8]}")
            if session.end_commit:
                print(f"    End Commit: {session.end_commit[:8]}")

        # Goals
        if session.goals:
            print(f"\n  Goals:")
            for goal in session.goals:
                print(f"    - {goal}")

        # Summary
        if session.summary:
            print(f"\n  Summary: {session.summary}")

        # Associations
        if session.track_id or session.sprint_id or session.task_ids:
            print(f"\n  Roadmap:")
            if session.track_id:
                print(f"    Track: {session.track_id}")
            if session.sprint_id:
                print(f"    Sprint: {session.sprint_id}")
            if session.task_ids:
                print(f"    Tasks: {', '.join(session.task_ids)}")

        # Events summary
        if session.events:
            print(f"\n  Events ({len(session.events)} total):")
            # Show last 5 events
            for event in session.events[-5:]:
                print(f"    [{event.timestamp.strftime('%H:%M')}] {event.event_type.value}")
            if len(session.events) > 5:
                print(f"    ... and {len(session.events) - 5} more")

        # Decisions
        if session.decisions:
            print(f"\n  Decisions ({len(session.decisions)} total):")
            for decision in session.decisions[:3]:
                print(f"    - {decision.description[:60]}...")
            if len(session.decisions) > 3:
                print(f"    ... and {len(session.decisions) - 3} more")

        # Commits
        if session.commits:
            print(f"\n  Commits ({len(session.commits)} total):")
            for commit in session.commits[:5]:
                msg = commit.message[:50] if commit.message else "(no message)"
                print(f"    {commit.short_sha}: {msg}")
            if len(session.commits) > 5:
                print(f"    ... and {len(session.commits) - 5} more")

        # Stats
        if session.stats:
            print(f"\n  Statistics:")
            print(f"    Duration: {session.stats.duration_seconds // 60} minutes")
            print(f"    Events: {session.stats.events_count}")
            print(f"    Decisions: {session.stats.decisions_count}")
            print(f"    Commits: {session.stats.commits_count}")
            print(f"    Files Modified: {session.stats.files_modified}")
            print(f"    Tasks Worked: {session.stats.tasks_worked}")
            if session.stats.errors_count:
                print(f"    Errors: {session.stats.errors_count}")

        return 0
    except Exception as e:
        print(format_error(f"Failed to show session: {e}"))
        return 1


def session_list_cmd(
    status: Optional[str] = None,
    track_id: Optional[str] = None,
    sprint_id: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 20,
) -> int:
    """List sessions with optional filters."""
    from datetime import datetime, timezone
    from vibey.operations.roadmap.session_manager import SessionManager
    from vibey.roadmap.models.session import SessionStatus

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        manager = SessionManager(roadmap_path)

        # Parse filters
        status_filter = SessionStatus(status) if status else None
        since_filter = None
        if since:
            try:
                since_filter = datetime.fromisoformat(since.replace('Z', '+00:00'))
            except ValueError:
                # Try parsing as relative time (e.g., "7d", "1w")
                import re
                match = re.match(r'^(\d+)([dwmh])$', since.lower())
                if match:
                    from datetime import timedelta
                    amount = int(match.group(1))
                    unit = match.group(2)
                    delta = {
                        'h': timedelta(hours=amount),
                        'd': timedelta(days=amount),
                        'w': timedelta(weeks=amount),
                        'm': timedelta(days=amount * 30),
                    }.get(unit, timedelta(days=7))
                    since_filter = datetime.now(timezone.utc) - delta

        sessions = manager.list_sessions(
            status=status_filter,
            track_id=track_id,
            sprint_id=sprint_id,
            since=since_filter,
            limit=limit,
        )

        if not sessions:
            print("No sessions found.")
            if status or track_id or sprint_id or since:
                print("\nTry removing filters or start a new session with: vibey session start")
            return 0

        print(f"📋 Sessions ({len(sessions)} found)")
        print("=" * 70)

        status_icons = {
            "active": "🟢",
            "paused": "⏸️",
            "completed": "✅",
            "abandoned": "❌",
        }

        for session in sessions:
            icon = status_icons.get(session.status.value, "⚪")
            created = session.created.strftime("%Y-%m-%d %H:%M") if session.created else "unknown"
            print(f"\n{icon} {session.name}")
            print(f"   ID: {session.id}")
            print(f"   Created: {created} | Status: {session.status.value}")
            if session.track_id:
                print(f"   Track: {session.track_id}")
            if session.branch:
                print(f"   Branch: {session.branch}")

        return 0
    except Exception as e:
        print(format_error(f"Failed to list sessions: {e}"))
        return 1


def session_report_cmd(session_id: str, format: str = "markdown", output: Optional[str] = None) -> int:
    """Generate a session report."""
    from vibey.operations.roadmap.session_reconstruction import SessionReconstructor

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        reconstructor = SessionReconstructor(roadmap_path)
        report = reconstructor.generate_session_report(session_id, format=format)

        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            print(format_success(f"Report written to: {output}"))
        else:
            print(report)

        return 0
    except Exception as e:
        print(format_error(f"Failed to generate report: {e}"))
        return 1


def session_timeline_cmd(session_id: str) -> int:
    """Show session timeline."""
    from vibey.operations.roadmap.session_reconstruction import SessionReconstructor

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        reconstructor = SessionReconstructor(roadmap_path)
        timeline = reconstructor.get_session_timeline(session_id)

        if not timeline:
            print(format_error(f"Session not found: {session_id}"))
            return 1

        session = timeline.session
        print(f"📋 Session Timeline: {session.name}")
        print(f"   Duration: {timeline.duration_formatted}")
        print("=" * 60)

        for event in timeline.events:
            time_str = event.timestamp.strftime("%H:%M:%S")
            event_name = event.event_type.value.replace("_", " ").title()

            # Determine icon based on event type
            icons = {
                "session_start": "🟢",
                "session_end": "🔴",
                "session_pause": "⏸️",
                "session_resume": "▶️",
                "task_start": "📋",
                "task_complete": "✅",
                "commit_made": "📝",
                "decision_made": "🤔",
                "file_modified": "📄",
                "error_encountered": "❌",
            }
            icon = icons.get(event.event_type.value, "•")

            # Get detail
            detail = ""
            if event.task_id:
                detail = f" (task: {event.task_id[:8]}...)"
            elif event.commit_sha:
                detail = f" ({event.commit_sha[:8]})"
            elif event.file_path:
                detail = f" ({event.file_path})"

            print(f"  {time_str} {icon} {event_name}{detail}")

        return 0
    except Exception as e:
        print(format_error(f"Failed to show timeline: {e}"))
        return 1


def session_export_cmd(session_id: str, output: Optional[str] = None) -> int:
    """Export session for continuation."""
    import json
    from vibey.operations.roadmap.session_reconstruction import SessionReconstructor

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        reconstructor = SessionReconstructor(roadmap_path)
        export_data = reconstructor.export_for_continuation(session_id)

        if not export_data:
            print(format_error(f"Session not found: {session_id}"))
            return 1

        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(export_data, indent=2, default=str))
            print(format_success(f"Export written to: {output}"))
        else:
            print(json.dumps(export_data, indent=2, default=str))

        return 0
    except Exception as e:
        print(format_error(f"Failed to export session: {e}"))
        return 1


def session_decisions_cmd(session_id: str) -> int:
    """Show decisions made in a session."""
    from vibey.operations.roadmap.session_reconstruction import SessionReconstructor

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        reconstructor = SessionReconstructor(roadmap_path)
        decisions = reconstructor.get_decisions_made(session_id)

        if not decisions:
            print("No decisions recorded in this session.")
            return 0

        print(f"🤔 Decisions Made ({len(decisions)} total)")
        print("=" * 60)

        for i, decision in enumerate(decisions, 1):
            time_str = decision.timestamp.strftime("%Y-%m-%d %H:%M")
            print(f"\n{i}. {decision.description}")
            print(f"   Time: {time_str}")
            print(f"   Category: {decision.category.value}")
            print(f"   Confidence: {decision.confidence.value}")

            if decision.rationale:
                print(f"   Rationale: {decision.rationale}")

            if decision.alternatives:
                alts = ", ".join(
                    a.get("name", str(a)) if isinstance(a, dict) else str(a)
                    for a in decision.alternatives
                )
                print(f"   Alternatives: {alts}")

            if decision.revisit:
                print("   ⚠️  Marked for revisit")

        return 0
    except Exception as e:
        print(format_error(f"Failed to show decisions: {e}"))
        return 1
