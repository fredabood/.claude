"""
'roadmap batch' command - Batch update operations.
"""

import sys
from pathlib import Path
from typing import List

# Add framework to path
framework_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_root))

# Add roadmap-lib to path
roadmap_lib_path = Path(__file__).parent.parent / "roadmap-lib"
sys.path.insert(0, str(roadmap_lib_path))

from roadmap.models import TaskStatus
from roadmap.serialization import load_roadmap, load_track, load_sprint, load_tasks, save_tasks
from filesystem import FileSystemManager, find_roadmap_root
from datetime import datetime, timezone


def batch_complete_tasks(
    fs: FileSystemManager,
    sprint_id: str,
    task_filter: str = None
) -> int:
    """
    Complete all tasks in a sprint (optionally filtered).

    Args:
        fs: FileSystemManager
        sprint_id: Sprint ID
        task_filter: Optional filter (e.g., "dev" for development tasks only)

    Returns:
        Number of tasks completed
    """
    tasks_path = fs.get_tasks_path(sprint_id)
    if not tasks_path.exists():
        return 0

    tasks = load_tasks(tasks_path)
    count = 0

    for task in tasks:
        # Skip if already completed
        if task.status == TaskStatus.COMPLETED:
            continue

        # Apply filter
        if task_filter == "dev" and task.is_quality_gate():
            continue
        if task_filter == "gates" and not task.is_quality_gate():
            continue

        # Complete task
        task.status = TaskStatus.COMPLETED
        task.completed = datetime.now(timezone.utc)
        task.metadata.last_modified = datetime.now(timezone.utc)
        count += 1

    if count > 0:
        save_tasks(tasks, tasks_path)

    return count


def batch_assign_tasks(
    fs: FileSystemManager,
    sprint_id: str,
    agent: str,
    status_filter: str = None
) -> int:
    """
    Assign all tasks in a sprint to an agent.

    Args:
        fs: FileSystemManager
        sprint_id: Sprint ID
        agent: Agent name
        status_filter: Optional status filter (e.g., "not_started")

    Returns:
        Number of tasks assigned
    """
    tasks_path = fs.get_tasks_path(sprint_id)
    if not tasks_path.exists():
        return 0

    tasks = load_tasks(tasks_path)
    count = 0

    for task in tasks:
        # Skip quality gates
        if task.is_quality_gate():
            continue

        # Apply status filter
        if status_filter and task.status.value != status_filter:
            continue

        # Assign task
        task.assigned_agent = agent
        task.metadata.last_modified = datetime.now(timezone.utc)
        count += 1

    if count > 0:
        save_tasks(tasks, tasks_path)

    return count


def batch_update_track_tasks(
    fs: FileSystemManager,
    track_id: str,
    operation: str,
    **kwargs
) -> int:
    """
    Apply batch operation to all tasks in a track.

    Args:
        fs: FileSystemManager
        track_id: Track ID
        operation: Operation to perform (complete, assign)
        **kwargs: Operation-specific arguments

    Returns:
        Total number of tasks updated
    """
    track_path = fs.get_track_path(track_id)
    if not track_path.exists():
        return 0

    track = load_track(track_path)
    total = 0

    for sprint_summary in track.sprints:
        if operation == "complete":
            count = batch_complete_tasks(
                fs,
                sprint_summary.id,
                task_filter=kwargs.get("task_filter")
            )
        elif operation == "assign":
            count = batch_assign_tasks(
                fs,
                sprint_summary.id,
                agent=kwargs.get("agent"),
                status_filter=kwargs.get("status_filter")
            )
        else:
            continue

        total += count

    return total


def handle_batch(args):
    """Handle 'roadmap batch' command."""
    # Find root directory
    if args.dir:
        root_dir = args.dir
    else:
        root_dir = find_roadmap_root()
        if not root_dir:
            print("❌ No roadmap found. Run 'roadmap init' first.")
            sys.exit(1)

    fs = FileSystemManager(root_dir)

    # Determine scope
    scope = args.scope  # sprint, track, or roadmap
    scope_id = args.id

    # Perform operation
    if args.operation == "complete":
        if scope == "sprint":
            count = batch_complete_tasks(fs, scope_id, task_filter=args.filter)
            print(f"✅ Completed {count} task(s) in sprint {scope_id}")

        elif scope == "track":
            count = batch_update_track_tasks(
                fs, scope_id, "complete",
                task_filter=args.filter
            )
            print(f"✅ Completed {count} task(s) in track {scope_id}")

        elif scope == "roadmap":
            # Complete all tasks in roadmap
            roadmap = load_roadmap(fs.get_roadmap_path())
            total = 0

            for track_summary in roadmap.tracks:
                count = batch_update_track_tasks(
                    fs, track_summary.id, "complete",
                    task_filter=args.filter
                )
                total += count

            print(f"✅ Completed {total} task(s) across roadmap")

    elif args.operation == "assign":
        if not args.agent:
            print("❌ --agent required for assign operation")
            sys.exit(1)

        if scope == "sprint":
            count = batch_assign_tasks(
                fs, scope_id,
                agent=args.agent,
                status_filter=args.status
            )
            print(f"✅ Assigned {count} task(s) to {args.agent} in sprint {scope_id}")

        elif scope == "track":
            count = batch_update_track_tasks(
                fs, scope_id, "assign",
                agent=args.agent,
                status_filter=args.status
            )
            print(f"✅ Assigned {count} task(s) to {args.agent} in track {scope_id}")

        elif scope == "roadmap":
            # Assign all tasks in roadmap
            roadmap = load_roadmap(fs.get_roadmap_path())
            total = 0

            for track_summary in roadmap.tracks:
                count = batch_update_track_tasks(
                    fs, track_summary.id, "assign",
                    agent=args.agent,
                    status_filter=args.status
                )
                total += count

            print(f"✅ Assigned {total} task(s) to {args.agent} across roadmap")

    # Refresh progress if significant changes
    if count > 0 or (scope == "roadmap" and total > 0):
        print("\n🔄 Refreshing progress...")
        import subprocess
        subprocess.run([
            "python3",
            str(Path(__file__).parent.parent / "roadmap-update.py"),
            "--dir", str(root_dir),
            "--refresh-progress"
        ], capture_output=True)
        print("✅ Progress refreshed")
