#!/usr/bin/env python3
"""
Update roadmap state.

Handles all write operations: completing tasks, progressing status, adding tracks/sprints, etc.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Add framework to path
framework_root = Path(__file__).parent.parent
sys.path.insert(0, str(framework_root))

# Add roadmap-lib to path
roadmap_lib_path = Path(__file__).parent / "roadmap-lib"
sys.path.insert(0, str(roadmap_lib_path))

from roadmap.models import (
    Roadmap, Track, Sprint, Task,
    Status, TaskStatus, ActivityType,
    TrackSummary, SprintSummary, Progress, Metadata,
    Dependency, DependencyType, GateInfo,
)
from roadmap.serialization import (
    load_roadmap, load_track, load_sprint, load_tasks,
    save_roadmap, save_track, save_sprint, save_tasks,
)
from filesystem import FileSystemManager, find_roadmap_root
from activity import ActivityLogger
from status import StatusManager
from blockers import BlockerComputer


def complete_task(
    fs: FileSystemManager,
    task_id: str,
    completed_by: str = "system"
) -> bool:
    """Mark a task as completed."""
    # Extract sprint ID from task ID
    parts = task_id.split('-')
    if len(parts) < 3:
        print(f"❌ Invalid task ID format: {task_id}")
        return False

    sprint_id = '-'.join(parts[:2])
    tasks_path = fs.get_tasks_path(sprint_id)

    if not tasks_path.exists():
        print(f"❌ Tasks file not found for sprint '{sprint_id}'")
        return False

    # Load tasks
    tasks = load_tasks(tasks_path)

    # Find and update task
    task = None
    for t in tasks:
        if t.id == task_id:
            task = t
            break

    if not task:
        print(f"❌ Task '{task_id}' not found")
        return False

    # Update task
    task.status = TaskStatus.COMPLETED
    task.completed = datetime.utcnow()
    task.metadata.last_modified = datetime.utcnow()
    task.metadata.last_modified_by = completed_by

    # Save tasks
    save_tasks(tasks, tasks_path)
    print(f"✅ Task '{task.name}' marked as completed")

    # Update sprint progress
    update_sprint_progress(fs, sprint_id)

    # Log activity
    logger = ActivityLogger(fs.root_dir)
    logger.log_activity(
        ActivityType.TASK_COMPLETED,
        f"Task '{task.name}' completed",
        {"task_id": task_id, "sprint_id": sprint_id}
    )

    return True


def start_task(
    fs: FileSystemManager,
    task_id: str,
    started_by: str = "system"
) -> bool:
    """Mark a task as in progress."""
    # Extract sprint ID from task ID
    parts = task_id.split('-')
    if len(parts) < 3:
        print(f"❌ Invalid task ID format: {task_id}")
        return False

    sprint_id = '-'.join(parts[:2])
    tasks_path = fs.get_tasks_path(sprint_id)

    if not tasks_path.exists():
        print(f"❌ Tasks file not found for sprint '{sprint_id}'")
        return False

    # Load tasks
    tasks = load_tasks(tasks_path)

    # Find and update task
    task = None
    for t in tasks:
        if t.id == task_id:
            task = t
            break

    if not task:
        print(f"❌ Task '{task_id}' not found")
        return False

    # Update task
    task.status = TaskStatus.IN_PROGRESS
    task.started = datetime.utcnow()
    task.metadata.last_modified = datetime.utcnow()
    task.metadata.last_modified_by = started_by

    # Save tasks
    save_tasks(tasks, tasks_path)
    print(f"✅ Task '{task.name}' marked as in progress")

    # Update sprint progress
    update_sprint_progress(fs, sprint_id)

    # Log activity
    logger = ActivityLogger(fs.root_dir)
    logger.log_activity(
        ActivityType.TASK_STARTED,
        f"Task '{task.name}' started",
        {"task_id": task_id, "sprint_id": sprint_id}
    )

    return True


def update_sprint_progress(fs: FileSystemManager, sprint_id: str):
    """Update sprint progress based on task completion."""
    sprint_path = fs.get_sprint_path(sprint_id)
    if not sprint_path.exists():
        return

    sprint = load_sprint(sprint_path)
    tasks_path = fs.get_tasks_path(sprint_id)

    if not tasks_path.exists():
        return

    tasks = load_tasks(tasks_path)

    # Calculate progress
    total_tasks = len([t for t in tasks if not t.is_quality_gate()])
    completed_tasks = len([
        t for t in tasks
        if not t.is_quality_gate() and t.status == TaskStatus.COMPLETED
    ])

    completion_percent = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

    # Update sprint progress
    sprint.progress.tasks_total = total_tasks
    sprint.progress.tasks_completed = completed_tasks
    sprint.progress.completion_percent = completion_percent

    # Check if sprint can auto-progress
    status_manager = StatusManager(fs.root_dir)
    progressed, new_status, message = status_manager.progress_sprint_status(sprint)

    if progressed and new_status:
        sprint.status = new_status
        print(f"🎉 Sprint '{sprint.name}' progressed to {new_status.value}: {message}")

        # Log activity
        logger = ActivityLogger(fs.root_dir)
        logger.log_activity(
            ActivityType.STATUS_CHANGED,
            f"Sprint '{sprint.name}' progressed to {new_status.value}",
            {"sprint_id": sprint_id, "old_status": sprint.status.value, "new_status": new_status.value}
        )

    # Compute blockers
    computer = BlockerComputer(fs.root_dir)
    blockers = computer.compute_sprint_blockers(sprint)
    sprint.blocked = len(blockers) > 0

    # Save sprint
    save_sprint(sprint, sprint_path)

    # Update track progress
    track_id = sprint_id.rsplit('-', 1)[0]  # Extract track ID
    update_track_progress(fs, track_id)


def update_track_progress(fs: FileSystemManager, track_id: str):
    """Update track progress based on sprint completion."""
    track_path = fs.get_track_path(track_id)
    if not track_path.exists():
        return

    track = load_track(track_path)

    # Calculate progress
    total_sprints = len(track.sprints)
    completed_sprints = 0
    total_tasks = 0
    completed_tasks = 0

    for sprint_summary in track.sprints:
        sprint_path = fs.get_sprint_path(sprint_summary.id)
        if sprint_path.exists():
            sprint = load_sprint(sprint_path)

            if sprint.status in [Status.COMPLETED, Status.PRODUCTION_GATE_CHECK, Status.PRODUCTION_READY, Status.DEPLOYED]:
                completed_sprints += 1

            total_tasks += sprint.progress.tasks_total
            completed_tasks += sprint.progress.tasks_completed

    completion_percent = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

    # Update track progress
    track.progress.sprints_total = total_sprints
    track.progress.sprints_completed = completed_sprints
    track.progress.tasks_total = total_tasks
    track.progress.tasks_completed = completed_tasks
    track.progress.completion_percent = completion_percent

    # Check if track can auto-progress
    status_manager = StatusManager(fs.root_dir)
    progressed, new_status, message = status_manager.progress_track_status(track)

    if progressed and new_status:
        track.status = new_status
        print(f"🎉 Track '{track.name}' progressed to {new_status.value}: {message}")

        # Log activity
        logger = ActivityLogger(fs.root_dir)
        logger.log_activity(
            ActivityType.STATUS_CHANGED,
            f"Track '{track.name}' progressed to {new_status.value}",
            {"track_id": track_id, "old_status": track.status.value, "new_status": new_status.value}
        )

    # Compute blockers
    computer = BlockerComputer(fs.root_dir)
    blockers = computer.compute_track_blockers(track)
    track.blocked = len(blockers) > 0

    # Save track
    save_track(track, track_path)

    # Update roadmap progress
    update_roadmap_progress(fs)


def update_roadmap_progress(fs: FileSystemManager):
    """Update roadmap progress based on track completion."""
    roadmap_path = fs.get_roadmap_path()
    if not roadmap_path.exists():
        return

    roadmap = load_roadmap(roadmap_path)

    # Calculate progress
    total_tracks = len(roadmap.tracks)
    completed_tracks = 0
    total_sprints = 0
    completed_sprints = 0
    total_tasks = 0
    completed_tasks = 0

    for track_summary in roadmap.tracks:
        track_path = fs.get_track_path(track_summary.id)
        if track_path.exists():
            track = load_track(track_path)

            if track.status in [Status.COMPLETED, Status.PRODUCTION_READY, Status.DEPLOYED]:
                completed_tracks += 1

            total_sprints += track.progress.sprints_total
            completed_sprints += track.progress.sprints_completed
            total_tasks += track.progress.tasks_total
            completed_tasks += track.progress.tasks_completed

    completion_percent = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

    # Update roadmap progress
    roadmap.progress.tracks_total = total_tracks
    roadmap.progress.tracks_completed = completed_tracks
    roadmap.progress.sprints_total = total_sprints
    roadmap.progress.sprints_completed = completed_sprints
    roadmap.progress.tasks_total = total_tasks
    roadmap.progress.tasks_completed = completed_tasks
    roadmap.progress.completion_percent = completion_percent

    # Check if roadmap can auto-progress
    status_manager = StatusManager(fs.root_dir)
    progressed, new_status, message = status_manager.progress_roadmap_status(roadmap)

    if progressed and new_status:
        roadmap.status = new_status
        print(f"🎉 Roadmap '{roadmap.name}' progressed to {new_status.value}: {message}")

        # Log activity
        logger = ActivityLogger(fs.root_dir)
        logger.log_activity(
            ActivityType.STATUS_CHANGED,
            f"Roadmap '{roadmap.name}' progressed to {new_status.value}",
            {"old_status": roadmap.status.value, "new_status": new_status.value}
        )

    # Save roadmap
    save_roadmap(roadmap, roadmap_path)


def assign_task(
    fs: FileSystemManager,
    task_id: str,
    agent: str,
    assigned_by: str = "system"
) -> bool:
    """Assign a task to an agent."""
    # Extract sprint ID from task ID
    parts = task_id.split('-')
    if len(parts) < 3:
        print(f"❌ Invalid task ID format: {task_id}")
        return False

    sprint_id = '-'.join(parts[:2])
    tasks_path = fs.get_tasks_path(sprint_id)

    if not tasks_path.exists():
        print(f"❌ Tasks file not found for sprint '{sprint_id}'")
        return False

    # Load tasks
    tasks = load_tasks(tasks_path)

    # Find and update task
    task = None
    for t in tasks:
        if t.id == task_id:
            task = t
            break

    if not task:
        print(f"❌ Task '{task_id}' not found")
        return False

    # Update task
    task.assigned_agent = agent
    task.metadata.last_modified = datetime.utcnow()
    task.metadata.last_modified_by = assigned_by

    # Save tasks
    save_tasks(tasks, tasks_path)
    print(f"✅ Task '{task.name}' assigned to {agent}")

    # Log activity
    logger = ActivityLogger(fs.root_dir)
    logger.log_activity(
        ActivityType.TASK_STARTED,
        f"Task '{task.name}' assigned to {agent}",
        {"task_id": task_id, "agent": agent}
    )

    return True


def start_sprint(
    fs: FileSystemManager,
    sprint_id: str,
    started_by: str = "system"
) -> bool:
    """Start a sprint."""
    sprint_path = fs.get_sprint_path(sprint_id)
    if not sprint_path.exists():
        print(f"❌ Sprint '{sprint_id}' not found")
        return False

    sprint = load_sprint(sprint_path)

    if sprint.status != Status.NOT_STARTED:
        print(f"❌ Sprint already started (status: {sprint.status.value})")
        return False

    # Update sprint
    sprint.status = Status.IN_PROGRESS
    sprint.started = datetime.utcnow()
    sprint.metadata.last_modified = datetime.utcnow()
    sprint.metadata.last_modified_by = started_by

    # Save sprint
    save_sprint(sprint, sprint_path)
    print(f"✅ Sprint '{sprint.name}' started")

    # Update track
    track_id = sprint_id.rsplit('-', 1)[0]
    track_path = fs.get_track_path(track_id)
    if track_path.exists():
        track = load_track(track_path)

        # If track not started, start it
        if track.status == Status.NOT_STARTED:
            track.status = Status.IN_PROGRESS
            track.started = datetime.utcnow()
            save_track(track, track_path)
            print(f"✅ Track '{track.name}' started")

    # Update roadmap
    roadmap_path = fs.get_roadmap_path()
    if roadmap_path.exists():
        roadmap = load_roadmap(roadmap_path)

        # If roadmap not started, start it
        if roadmap.status == Status.NOT_STARTED:
            roadmap.status = Status.IN_PROGRESS
            save_roadmap(roadmap, roadmap_path)
            print(f"✅ Roadmap '{roadmap.name}' started")

    # Log activity
    logger = ActivityLogger(fs.root_dir)
    logger.log_activity(
        ActivityType.SPRINT_STARTED,
        f"Sprint '{sprint.name}' started",
        {"sprint_id": sprint_id}
    )

    return True


def complete_sprint(
    fs: FileSystemManager,
    sprint_id: str,
    completed_by: str = "system"
) -> bool:
    """Mark a sprint as completed."""
    sprint_path = fs.get_sprint_path(sprint_id)
    if not sprint_path.exists():
        print(f"❌ Sprint '{sprint_id}' not found")
        return False

    sprint = load_sprint(sprint_path)

    # Check if can progress to completed
    status_manager = StatusManager(fs.root_dir)
    can_progress, reason = status_manager.can_progress_sprint(sprint, Status.COMPLETED)

    if not can_progress:
        print(f"❌ Cannot complete sprint: {reason}")
        return False

    # Update sprint
    sprint.status = Status.COMPLETED
    sprint.completed = datetime.utcnow()
    sprint.metadata.last_modified = datetime.utcnow()
    sprint.metadata.last_modified_by = completed_by

    # Save sprint
    save_sprint(sprint, sprint_path)
    print(f"✅ Sprint '{sprint.name}' marked as completed")

    # Update track progress
    track_id = sprint_id.rsplit('-', 1)[0]
    update_track_progress(fs, track_id)

    # Log activity
    logger = ActivityLogger(fs.root_dir)
    logger.log_activity(
        ActivityType.SPRINT_COMPLETED,
        f"Sprint '{sprint.name}' completed",
        {"sprint_id": sprint_id}
    )

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Update roadmap state",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Complete a task
  python3 roadmap-update.py --complete-task backend-1-task-001

  # Start a task
  python3 roadmap-update.py --start-task backend-1-task-002

  # Assign a task
  python3 roadmap-update.py --assign-task backend-1-task-003 --agent web-developer

  # Start a sprint
  python3 roadmap-update.py --start-sprint backend-1

  # Complete a sprint
  python3 roadmap-update.py --complete-sprint backend-1

  # Refresh all progress (recompute from tasks)
  python3 roadmap-update.py --refresh-progress
        """
    )

    parser.add_argument(
        "--dir",
        type=Path,
        help="Root directory (defaults to searching upward for .vibey/)"
    )

    parser.add_argument(
        "--complete-task",
        type=str,
        help="Mark task as completed"
    )

    parser.add_argument(
        "--start-task",
        type=str,
        help="Mark task as in progress"
    )

    parser.add_argument(
        "--assign-task",
        type=str,
        help="Assign task to agent (requires --agent)"
    )

    parser.add_argument(
        "--agent",
        type=str,
        help="Agent name for task assignment"
    )

    parser.add_argument(
        "--start-sprint",
        type=str,
        help="Start a sprint"
    )

    parser.add_argument(
        "--complete-sprint",
        type=str,
        help="Mark sprint as completed"
    )

    parser.add_argument(
        "--refresh-progress",
        action="store_true",
        help="Refresh all progress calculations"
    )

    parser.add_argument(
        "--by",
        type=str,
        default="system",
        help="User making the update (default: system)"
    )

    args = parser.parse_args()

    # Find roadmap root
    if args.dir:
        root_dir = args.dir
    else:
        root_dir = find_roadmap_root()
        if not root_dir:
            print("❌ No roadmap found. Run roadmap-init.py first.")
            sys.exit(1)

    fs = FileSystemManager(root_dir)

    # Check roadmap exists
    if not fs.roadmap_exists():
        print(f"❌ No roadmap found at {fs.get_roadmap_path()}")
        sys.exit(1)

    # Execute update
    if args.complete_task:
        success = complete_task(fs, args.complete_task, args.by)
        sys.exit(0 if success else 1)

    elif args.start_task:
        success = start_task(fs, args.start_task, args.by)
        sys.exit(0 if success else 1)

    elif args.assign_task:
        if not args.agent:
            print("❌ --agent required for task assignment")
            sys.exit(1)
        success = assign_task(fs, args.assign_task, args.agent, args.by)
        sys.exit(0 if success else 1)

    elif args.start_sprint:
        success = start_sprint(fs, args.start_sprint, args.by)
        sys.exit(0 if success else 1)

    elif args.complete_sprint:
        success = complete_sprint(fs, args.complete_sprint, args.by)
        sys.exit(0 if success else 1)

    elif args.refresh_progress:
        print("🔄 Refreshing progress calculations...")

        # Refresh all sprints
        for sprint_id in fs.list_sprints():
            update_sprint_progress(fs, sprint_id)

        print("✅ Progress refreshed")
        sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
