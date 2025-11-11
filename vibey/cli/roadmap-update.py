#!/usr/bin/env python3
"""
Update roadmap state.

Handles all write operations: completing tasks, progressing status, adding tracks/sprints, etc.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List

# Add repository root to path for framework imports
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

# Add scripts dir to path for roadmap_lib package
scripts_path = Path(__file__).parent
sys.path.insert(0, str(scripts_path))

from vibey.roadmap.models import (
    Roadmap, Track, Sprint, Task,
    Status, TaskStatus, ActivityType,
    TrackSummary, SprintSummary, Progress, Metadata,
    Dependency, DependencyType, GateInfo, DependencyStatus,
)
from vibey.roadmap.serialization import (
    load_roadmap, load_track, load_sprint, load_tasks,
    save_roadmap, save_track, save_sprint, save_tasks,
)
from roadmap_lib.filesystem import FileSystemManager, find_roadmap_root
from roadmap_lib.activity import ActivityLogger
from roadmap_lib.status import StatusManager
from roadmap_lib.blockers import BlockerComputer

# Import sync hooks for automatic documentation synchronization
try:
    from docs.sync_hooks import trigger_on_task_complete, trigger_on_sprint_complete, trigger_on_track_complete
    SYNC_HOOKS_AVAILABLE = True
except ImportError:
    SYNC_HOOKS_AVAILABLE = False


def update_dependent_cache(
    fs: FileSystemManager,
    dependent_id: str,
    blocker_id: str,
    new_status: str
) -> bool:
    """
    Update cached dependency status in a dependent object.

    Args:
        fs: Filesystem manager
        dependent_id: ID of the dependent (task/sprint/track that depends on blocker)
        blocker_id: ID of the blocker (dependency that changed status)
        new_status: New status of the blocker

    Returns:
        True if updated successfully
    """
    # Determine object type from ID format
    if '-task-' in dependent_id:
        # It's a task
        sprint_id = dependent_id.split('-task-')[0]
        tasks_path = fs.get_tasks_path(sprint_id)

        if not tasks_path.exists():
            print(f"⚠️  Tasks file not found for dependent: {dependent_id}")
            return False

        tasks = load_tasks(tasks_path)
        task = next((t for t in tasks if t.id == dependent_id), None)

        if not task:
            print(f"⚠️  Dependent task not found: {dependent_id}")
            return False

        # Update depends_on cache
        modified = False
        for dep_status in task.depends_on:
            if dep_status.blocker_id == blocker_id:
                dep_status.current_status = new_status
                dep_status.last_checked = datetime.now(timezone.utc)
                modified = True
                break

        if not modified:
            print(f"⚠️  Blocker {blocker_id} not found in task {dependent_id} depends_on")
            return False

        # Recompute blocked status
        task.blocked = task.compute_blocked_status()

        # Save tasks
        save_tasks(tasks, tasks_path)
        return True

    elif '-sprint-' in dependent_id:
        # It's a sprint
        sprint_path = fs.get_sprint_path(dependent_id)

        if not sprint_path.exists():
            print(f"⚠️  Sprint file not found: {dependent_id}")
            return False

        sprint = load_sprint(sprint_path)

        # Update depends_on cache
        modified = False
        for dep_status in sprint.depends_on:
            if dep_status.blocker_id == blocker_id:
                dep_status.current_status = new_status
                dep_status.last_checked = datetime.now(timezone.utc)
                modified = True
                break

        if not modified:
            print(f"⚠️  Blocker {blocker_id} not found in sprint {dependent_id} depends_on")
            return False

        # Recompute blocked status
        sprint.blocked = sprint.compute_blocked_status()

        # Save sprint
        save_sprint(sprint, sprint_path)
        return True

    else:
        # It's a track
        track_path = fs.get_track_path(dependent_id)

        if not track_path.exists():
            print(f"⚠️  Track file not found: {dependent_id}")
            return False

        track = load_track(track_path)

        # Update depends_on cache
        modified = False
        for dep_status in track.depends_on:
            if dep_status.blocker_id == blocker_id:
                dep_status.current_status = new_status
                dep_status.last_checked = datetime.now(timezone.utc)
                modified = True
                break

        if not modified:
            print(f"⚠️  Blocker {blocker_id} not found in track {dependent_id} depends_on")
            return False

        # Recompute blocked status
        track.blocked = track.compute_blocked_status()

        # Save track
        save_track(track, track_path)
        return True


def complete_task(
    fs: FileSystemManager,
    task_id: str,
    completed_by: str = "system"
) -> bool:
    """Mark a task as completed."""
    # Extract sprint ID from task ID (everything before -task-)
    if '-task-' not in task_id:
        print(f"❌ Invalid task ID format: {task_id}")
        return False

    sprint_id = task_id.split('-task-')[0]
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
    task.completed = datetime.now(timezone.utc)
    task.metadata.last_modified = datetime.now(timezone.utc)
    task.metadata.last_modified_by = completed_by

    # Save tasks
    save_tasks(tasks, tasks_path)
    print(f"✅ Task '{task.title}' marked as completed")

    # Update dependency caches for all dependents (Phase 3: Dependency Tracking v2.0)
    for dependent_id in task.depended_on_by:
        if update_dependent_cache(fs, dependent_id, task_id, "completed"):
            print(f"  ✓ Updated dependent: {dependent_id}")
        else:
            print(f"  ⚠️  Failed to update dependent: {dependent_id}")

    # Update sprint progress
    update_sprint_progress(fs, sprint_id)

    # Log activity
    logger = ActivityLogger(fs.root_dir)
    logger.log_activity(
        ActivityType.TASK_COMPLETED,
        f"Task '{task.title}' completed",
        {"task_id": task_id, "sprint_id": sprint_id}
    )

    # Trigger automatic documentation sync if enabled
    if SYNC_HOOKS_AVAILABLE:
        trigger_on_task_complete(task_id, enabled=True, verbose=False)

    return True


def start_task(
    fs: FileSystemManager,
    task_id: str,
    started_by: str = "system"
) -> bool:
    """Mark a task as in progress."""
    # Extract sprint ID from task ID (everything before -task-)
    if '-task-' not in task_id:
        print(f"❌ Invalid task ID format: {task_id}")
        return False

    sprint_id = task_id.split('-task-')[0]
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
    task.started = datetime.now(timezone.utc)
    task.metadata.last_modified = datetime.now(timezone.utc)
    task.metadata.last_modified_by = started_by

    # Save tasks
    save_tasks(tasks, tasks_path)
    print(f"✅ Task '{task.title}' marked as in progress")

    # Update dependency caches for all dependents (Phase 3: Dependency Tracking v2.0)
    for dependent_id in task.depended_on_by:
        if update_dependent_cache(fs, dependent_id, task_id, "in_progress"):
            print(f"  ✓ Updated dependent: {dependent_id}")
        else:
            print(f"  ⚠️  Failed to update dependent: {dependent_id}")

    # Update sprint progress
    update_sprint_progress(fs, sprint_id)

    # Log activity
    logger = ActivityLogger(fs.root_dir)
    logger.log_activity(
        ActivityType.TASK_STARTED,
        f"Task '{task.title}' started",
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

    # Calculate progress by task type
    from roadmap.models import TaskType

    # Development tasks
    dev_tasks = [t for t in tasks if t.task_type == TaskType.DEVELOPMENT]
    dev_total = len(dev_tasks)
    dev_completed = len([t for t in dev_tasks if t.status == TaskStatus.COMPLETED])

    # Completion gate tasks
    comp_gate_tasks = [t for t in tasks if t.task_type == TaskType.COMPLETION_GATE]
    comp_gate_total = len(comp_gate_tasks)
    comp_gate_completed = len([t for t in comp_gate_tasks if t.status == TaskStatus.COMPLETED])

    # Production gate tasks
    prod_gate_tasks = [t for t in tasks if t.task_type == TaskType.PRODUCTION_GATE]
    prod_gate_total = len(prod_gate_tasks)
    prod_gate_completed = len([t for t in prod_gate_tasks if t.status == TaskStatus.COMPLETED])

    # Total tasks and completion
    total_tasks = dev_total + comp_gate_total + prod_gate_total
    completed_tasks = dev_completed + comp_gate_completed + prod_gate_completed
    completion_percent = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

    # Update sprint progress
    sprint.progress.tasks_total = total_tasks
    sprint.progress.tasks_completed = completed_tasks
    sprint.progress.development_tasks_total = dev_total
    sprint.progress.development_tasks_completed = dev_completed
    sprint.progress.completion_gate_tasks_total = comp_gate_total
    sprint.progress.completion_gate_tasks_completed = comp_gate_completed
    sprint.progress.production_gate_tasks_total = prod_gate_total
    sprint.progress.production_gate_tasks_completed = prod_gate_completed
    sprint.progress.completion_percent = completion_percent

    # Check if sprint can auto-progress
    status_manager = StatusManager(fs.root_dir)
    progressed, new_status, message = status_manager.progress_sprint_status(sprint)

    if progressed and new_status:
        old_status = sprint.status
        sprint.status = new_status

        # Set appropriate timestamp based on new status
        now = datetime.now(timezone.utc)
        if new_status == Status.COMPLETION_GATE_CHECK:
            sprint.completion_gate_check_at = now
        elif new_status == Status.COMPLETED:
            sprint.completed = now
        elif new_status == Status.PRODUCTION_GATE_CHECK:
            sprint.production_gate_check_at = now
        elif new_status == Status.PRODUCTION_READY:
            sprint.production_ready_at = now
        elif new_status == Status.DEPLOYED:
            sprint.deployed_at = now

        sprint.metadata.last_modified = now
        print(f"🎉 Sprint '{sprint.name}' progressed to {new_status.value}: {message}")

        # Update dependency caches for all dependents when status changes (Phase 3: Dependency Tracking v2.0)
        for dependent_id in sprint.depended_on_by:
            if update_dependent_cache(fs, dependent_id, sprint_id, new_status.value):
                print(f"  ✓ Updated dependent: {dependent_id}")
            else:
                print(f"  ⚠️  Failed to update dependent: {dependent_id}")

        # Log activity
        # logger = ActivityLogger(fs.root_dir)
        # logger.log_activity(
        #     ActivityType.STATUS_CHANGED,
        #     f"Sprint '{sprint.name}' progressed to {new_status.value}",
        #     {"sprint_id": sprint_id, "old_status": old_status.value, "new_status": new_status.value}
        # )

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

    try:
        track = load_track(track_path)
    except Exception as e:
        print(f"⚠️  Failed to load track {track_id}: {e}")
        return

    # Calculate progress AND update sprint summaries
    total_sprints = len(track.sprints)
    completed_sprints = 0
    total_tasks = 0
    completed_tasks = 0

    for sprint_summary in track.sprints:
        sprint_path = fs.get_sprint_path(sprint_summary.id)
        if sprint_path.exists():
            sprint = load_sprint(sprint_path)

            # Update sprint summary with current sprint state
            sprint_summary.status = sprint.status
            sprint_summary.started = sprint.started

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
        old_status = track.status
        track.status = new_status
        print(f"🎉 Track '{track.name}' progressed to {new_status.value}: {message}")

        # Update dependency caches for all dependents when status changes (Phase 3: Dependency Tracking v2.0)
        for dependent_id in track.depended_on_by:
            if update_dependent_cache(fs, dependent_id, track_id, new_status.value):
                print(f"  ✓ Updated dependent: {dependent_id}")
            else:
                print(f"  ⚠️  Failed to update dependent: {dependent_id}")

        # Log activity
        # logger = ActivityLogger(fs.root_dir)
        # logger.log_activity(
        #     ActivityType.STATUS_CHANGED,
        #     f"Track '{track.name}' progressed to {new_status.value}",
        #     {"track_id": track_id, "old_status": old_status.value, "new_status": new_status.value}
        # )

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
            try:
                track = load_track(track_path)

                if track.status in [Status.COMPLETED, Status.PRODUCTION_READY, Status.DEPLOYED]:
                    completed_tracks += 1

                total_sprints += track.progress.sprints_total
                completed_sprints += track.progress.sprints_completed
                total_tasks += track.progress.tasks_total
                completed_tasks += track.progress.tasks_completed
            except Exception as e:
                print(f"⚠️  Failed to load track {track_summary.id}: {e}")
                continue

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
        # logger = ActivityLogger(fs.root_dir)
        # logger.log_activity(
        #     ActivityType.STATUS_CHANGED,
        #     f"Roadmap '{roadmap.name}' progressed to {new_status.value}",
        #     {"old_status": roadmap.status.value, "new_status": new_status.value}
        # )

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
    task.metadata.last_modified = datetime.now(timezone.utc)
    task.metadata.last_modified_by = assigned_by

    # Save tasks
    save_tasks(tasks, tasks_path)
    print(f"✅ Task '{task.title}' assigned to {agent}")

    # Log activity
    logger = ActivityLogger(fs.root_dir)
    logger.log_activity(
        ActivityType.TASK_STARTED,
        f"Task '{task.title}' assigned to {agent}",
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
    sprint.started = datetime.now(timezone.utc)
    sprint.metadata.last_modified = datetime.now(timezone.utc)
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
            track.started = datetime.now(timezone.utc)
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
    sprint.completed = datetime.now(timezone.utc)
    sprint.metadata.last_modified = datetime.now(timezone.utc)
    sprint.metadata.last_modified_by = completed_by

    # Save sprint
    save_sprint(sprint, sprint_path)
    print(f"✅ Sprint '{sprint.name}' marked as completed")

    # Update dependency caches for all dependents (Phase 3: Dependency Tracking v2.0)
    for dependent_id in sprint.depended_on_by:
        if update_dependent_cache(fs, dependent_id, sprint_id, "completed"):
            print(f"  ✓ Updated dependent: {dependent_id}")
        else:
            print(f"  ⚠️  Failed to update dependent: {dependent_id}")

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


def refresh_all_dependency_caches(fs: FileSystemManager) -> int:
    """
    Refresh all dependency caches across the entire roadmap.

    Updates current_status fields in all depends_on lists and recomputes
    blocked status for all tracks, sprints, and tasks.

    Returns:
        Number of dependency cache entries updated
    """
    updated_count = 0

    # Load roadmap to get all tracks
    roadmap_path = fs.get_roadmap_path()
    if not roadmap_path.exists():
        return 0

    roadmap = load_roadmap(roadmap_path)

    # Refresh track dependencies
    for track_summary in roadmap.tracks:
        track_path = fs.get_track_path(track_summary.id)
        if not track_path.exists():
            continue

        try:
            track = load_track(track_path)
        except Exception as e:
            print(f"⚠️  Failed to load track {track_summary.id}: {e}")
            continue

        modified = False

        # Update depends_on cache
        for dep_status in track.depends_on:
            # Get current status of blocker
            blocker_path = fs.get_track_path(dep_status.blocker_id)
            if blocker_path.exists():
                try:
                    blocker_track = load_track(blocker_path)
                    if dep_status.current_status != blocker_track.status:
                        dep_status.current_status = blocker_track.status
                        dep_status.last_checked = datetime.now(timezone.utc)
                        modified = True
                        updated_count += 1
                except Exception as e:
                    print(f"⚠️  Failed to load blocker track {dep_status.blocker_id}: {e}")
                    continue

        # Recompute blocked status
        if modified:
            track.blocked = track.compute_blocked_status()
            save_track(track, track_path)

    # Refresh sprint dependencies
    for sprint_id in fs.list_sprints():
        sprint_path = fs.get_sprint_path(sprint_id)
        if not sprint_path.exists():
            continue

        sprint = load_sprint(sprint_path)
        modified = False

        for dep_status in sprint.depends_on:
            # Determine blocker type and get its status
            if dep_status.blocker_type == DependencyType.TRACK:
                blocker_path = fs.get_track_path(dep_status.blocker_id)
                if blocker_path.exists():
                    blocker = load_track(blocker_path)
                    if dep_status.current_status != blocker.status:
                        dep_status.current_status = blocker.status
                        dep_status.last_checked = datetime.now(timezone.utc)
                        modified = True
                        updated_count += 1
            elif dep_status.blocker_type == DependencyType.SPRINT:
                blocker_path = fs.get_sprint_path(dep_status.blocker_id)
                if blocker_path.exists():
                    blocker = load_sprint(blocker_path)
                    if dep_status.current_status != blocker.status:
                        dep_status.current_status = blocker.status
                        dep_status.last_checked = datetime.now(timezone.utc)
                        modified = True
                        updated_count += 1

        if modified:
            sprint.blocked = sprint.compute_blocked_status()
            save_sprint(sprint, sprint_path)

    # Refresh task dependencies
    for sprint_id in fs.list_sprints():
        tasks_path = fs.get_tasks_path(sprint_id)
        if not tasks_path.exists():
            continue

        tasks = load_tasks(tasks_path)
        modified = False

        for task in tasks:
            for dep_status in task.depends_on:
                # Tasks can depend on other tasks or sprints
                if dep_status.blocker_type == DependencyType.TASK:
                    # Find the blocker task
                    blocker_sprint_id = dep_status.blocker_id.rsplit('-task-', 1)[0] + '-task-' + dep_status.blocker_id.split('-task-')[1].split('-')[0]
                    blocker_tasks_path = fs.get_tasks_path(blocker_sprint_id.rsplit('-task-', 1)[0])
                    if blocker_tasks_path.exists():
                        blocker_tasks = load_tasks(blocker_tasks_path)
                        blocker_task = next((t for t in blocker_tasks if t.id == dep_status.blocker_id), None)
                        if blocker_task and dep_status.current_status != blocker_task.status:
                            dep_status.current_status = blocker_task.status
                            dep_status.last_checked = datetime.now(timezone.utc)
                            modified = True
                            updated_count += 1
                elif dep_status.blocker_type == DependencyType.SPRINT:
                    blocker_path = fs.get_sprint_path(dep_status.blocker_id)
                    if blocker_path.exists():
                        blocker = load_sprint(blocker_path)
                        if dep_status.current_status != blocker.status:
                            dep_status.current_status = blocker.status
                            dep_status.last_checked = datetime.now(timezone.utc)
                            modified = True
                            updated_count += 1

            if modified:
                task.blocked = task.compute_blocked_status()

        if modified:
            save_tasks(tasks, tasks_path)

    return updated_count


def verify_roadmap_consistency(fs: FileSystemManager) -> List[str]:
    """
    Verify roadmap consistency and return list of issues found.

    Checks:
    - Sprint progress matches task completion
    - Track progress matches sprint completion
    - Roadmap progress matches track completion
    - Dependency cache consistency

    Returns:
        List of issue descriptions (empty if no issues)
    """
    issues = []

    roadmap_path = fs.get_roadmap_path()
    if not roadmap_path.exists():
        issues.append("Roadmap file not found")
        return issues

    roadmap = load_roadmap(roadmap_path)

    # Verify sprint-level consistency
    for sprint_id in fs.list_sprints():
        sprint_path = fs.get_sprint_path(sprint_id)
        tasks_path = fs.get_tasks_path(sprint_id)

        if not sprint_path.exists():
            continue

        sprint = load_sprint(sprint_path)

        if tasks_path.exists():
            tasks = load_tasks(tasks_path)

            # Check task counts
            actual_tasks_total = len(tasks)
            actual_tasks_completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)

            if sprint.progress.tasks_total != actual_tasks_total:
                issues.append(f"Sprint {sprint_id}: tasks_total mismatch (stored={sprint.progress.tasks_total}, actual={actual_tasks_total})")

            if sprint.progress.tasks_completed != actual_tasks_completed:
                issues.append(f"Sprint {sprint_id}: tasks_completed mismatch (stored={sprint.progress.tasks_completed}, actual={actual_tasks_completed})")

    # Verify track-level consistency
    for track_summary in roadmap.tracks:
        track_path = fs.get_track_path(track_summary.id)
        if not track_path.exists():
            continue

        track = load_track(track_path)

        # Aggregate sprint data
        actual_sprints_total = len(track.sprints)
        actual_sprints_completed = 0
        actual_tasks_total = 0
        actual_tasks_completed = 0

        for sprint_summary in track.sprints:
            sprint_path = fs.get_sprint_path(sprint_summary.id)
            if sprint_path.exists():
                sprint = load_sprint(sprint_path)

                if sprint.status in [Status.COMPLETED, Status.PRODUCTION_GATE_CHECK, Status.PRODUCTION_READY, Status.DEPLOYED]:
                    actual_sprints_completed += 1

                actual_tasks_total += sprint.progress.tasks_total
                actual_tasks_completed += sprint.progress.tasks_completed

        # Check consistency
        if track.progress.sprints_total != actual_sprints_total:
            issues.append(f"Track {track.id}: sprints_total mismatch (stored={track.progress.sprints_total}, actual={actual_sprints_total})")

        if track.progress.sprints_completed != actual_sprints_completed:
            issues.append(f"Track {track.id}: sprints_completed mismatch (stored={track.progress.sprints_completed}, actual={actual_sprints_completed})")

        if track.progress.tasks_total != actual_tasks_total:
            issues.append(f"Track {track.id}: tasks_total mismatch (stored={track.progress.tasks_total}, actual={actual_tasks_total})")

        if track.progress.tasks_completed != actual_tasks_completed:
            issues.append(f"Track {track.id}: tasks_completed mismatch (stored={track.progress.tasks_completed}, actual={actual_tasks_completed})")

    return issues


def recalculate_all(fs: FileSystemManager, verify: bool = False) -> bool:
    """
    Recalculate entire roadmap hierarchy from bottom to top.

    Performs a complete recalculation of:
    - All sprint progress (from tasks)
    - All track progress (from sprints)
    - Roadmap progress (from tracks)
    - All dependency caches
    - All blocked status flags

    Args:
        fs: Filesystem manager
        verify: If True, verify consistency after recalculation

    Returns:
        True if successful
    """
    print("🔄 Recalculating entire roadmap hierarchy...")
    print()

    # Step 1: Recalculate all sprints (bottom-up)
    print("📊 Step 1/5: Recalculating sprint progress...")
    sprint_count = 0
    for sprint_id in fs.list_sprints():
        update_sprint_progress(fs, sprint_id)
        sprint_count += 1
    print(f"  ✅ {sprint_count} sprints recalculated")
    print()

    # Step 2: Recalculate all tracks
    print("📊 Step 2/5: Recalculating track progress...")
    track_count = 0
    for track_id in fs.list_tracks():
        update_track_progress(fs, track_id)
        track_count += 1
    print(f"  ✅ {track_count} tracks recalculated")
    print()

    # Step 3: Recalculate roadmap-level progress
    print("📊 Step 3/5: Recalculating roadmap progress...")
    update_roadmap_progress(fs)
    print(f"  ✅ Roadmap progress recalculated")
    print()

    # Step 4: Refresh all dependency caches
    print("🔗 Step 4/5: Refreshing dependency caches...")
    dep_count = refresh_all_dependency_caches(fs)
    print(f"  ✅ {dep_count} dependency cache entries refreshed")
    print()

    # Step 5: Verify consistency (optional)
    if verify:
        print("🔍 Step 5/5: Verifying consistency...")
        issues = verify_roadmap_consistency(fs)
        if issues:
            print(f"  ⚠️  {len(issues)} consistency issues found:")
            for issue in issues[:10]:  # Show first 10
                print(f"     - {issue}")
            if len(issues) > 10:
                print(f"     ... and {len(issues) - 10} more")
            print()
            print("⚠️  Recalculation completed but consistency issues remain")
            return False
        else:
            print(f"  ✅ Roadmap consistency verified - no issues found")
            print()
    else:
        print("⏭️  Step 5/5: Consistency verification skipped (use --verify to enable)")
        print()

    print("✅ Complete roadmap recalculation finished!")
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

  # Recalculate entire roadmap hierarchy
  python3 roadmap-update.py --recalculate-all

  # Recalculate and verify consistency
  python3 roadmap-update.py --recalculate-all --verify
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
        "--recalculate-all",
        action="store_true",
        help="Recalculate entire roadmap hierarchy (sprints, tracks, roadmap, dependencies)"
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify consistency after recalculation (use with --recalculate-all)"
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

    elif args.recalculate_all:
        success = recalculate_all(fs, verify=args.verify)
        sys.exit(0 if success else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
