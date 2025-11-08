"""
'roadmap list' command - List objects (tracks, sprints, tasks).
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add framework to path
framework_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_root))

# Add roadmap-lib to path
roadmap_lib_path = Path(__file__).parent.parent / "roadmap-lib"
sys.path.insert(0, str(roadmap_lib_path))

from roadmap.models import Status
from roadmap.serialization import load_roadmap, load_track, load_sprint, load_tasks
from filesystem import FileSystemManager, find_roadmap_root


def format_status(status: Status) -> str:
    """Format status with emoji."""
    status_map = {
        Status.NOT_STARTED: "⚪",
        Status.IN_PROGRESS: "🔵",
        Status.PAUSED: "⏸️",
        Status.COMPLETION_GATE_CHECK: "🚧",
        Status.COMPLETED: "✅",
        Status.PRODUCTION_GATE_CHECK: "🔍",
        Status.PRODUCTION_READY: "🚀",
        Status.DEPLOYED: "🌟",
        Status.WONT_DO: "❌",
    }
    emoji = status_map.get(status, "❓")
    return f"{emoji} {status.value}"


def list_tracks(fs: FileSystemManager, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all tracks."""
    roadmap_path = fs.get_roadmap_path()
    if not roadmap_path.exists():
        return []

    roadmap = load_roadmap(roadmap_path)
    tracks = []

    for track_summary in roadmap.tracks:
        track_path = fs.get_track_path(track_summary.id)
        if track_path.exists():
            track = load_track(track_path)

            # Apply status filter
            if status_filter and track.status.value != status_filter:
                continue

            tracks.append({
                "id": track.id,
                "name": track.name,
                "status": track.status.value,
                "blocked": track.blocked,
                "progress": {
                    "sprints": f"{track.progress.sprints_completed}/{track.progress.sprints_total}",
                    "completion": f"{track.progress.completion_percent}%",
                },
            })

    return tracks


def list_sprints(fs: FileSystemManager, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all sprints."""
    roadmap_path = fs.get_roadmap_path()
    if not roadmap_path.exists():
        return []

    roadmap = load_roadmap(roadmap_path)
    sprints = []

    for track_summary in roadmap.tracks:
        track_path = fs.get_track_path(track_summary.id)
        if track_path.exists():
            track = load_track(track_path)

            for sprint_summary in track.sprints:
                sprint_path = fs.get_sprint_path(sprint_summary.id)
                if sprint_path.exists():
                    sprint = load_sprint(sprint_path)

                    # Apply status filter
                    if status_filter and sprint.status.value != status_filter:
                        continue

                    sprints.append({
                        "id": sprint.id,
                        "name": sprint.name,
                        "track_id": track.id,
                        "track_name": track.name,
                        "status": sprint.status.value,
                        "blocked": sprint.blocked,
                        "progress": {
                            "tasks": f"{sprint.progress.tasks_completed}/{sprint.progress.tasks_total}",
                            "completion": f"{sprint.progress.completion_percent}%",
                        },
                    })

    return sprints


def list_tasks(fs: FileSystemManager, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all tasks."""
    roadmap_path = fs.get_roadmap_path()
    if not roadmap_path.exists():
        return []

    roadmap = load_roadmap(roadmap_path)
    tasks = []

    for track_summary in roadmap.tracks:
        track_path = fs.get_track_path(track_summary.id)
        if track_path.exists():
            track = load_track(track_path)

            for sprint_summary in track.sprints:
                tasks_path = fs.get_tasks_path(sprint_summary.id)
                if tasks_path.exists():
                    sprint_tasks = load_tasks(tasks_path)

                    for task in sprint_tasks:
                        # Apply status filter
                        if status_filter and task.status.value != status_filter:
                            continue

                        tasks.append({
                            "id": task.id,
                            "name": task.name,
                            "sprint_id": sprint_summary.id,
                            "sprint_name": sprint_summary.name,
                            "track_id": track.id,
                            "track_name": track.name,
                            "task_type": task.task_type,
                            "status": task.status.value,
                            "blocked": task.blocked,
                            "assigned_agent": task.assigned_agent,
                        })

    return tasks


def print_tracks(tracks: List[Dict[str, Any]]):
    """Pretty print tracks list."""
    print(f"\n🛤️  Tracks ({len(tracks)})")
    print("="*80)

    if not tracks:
        print("  No tracks found.")
    else:
        for track in tracks:
            blocked = " ⚠️" if track['blocked'] else ""
            print(f"\n{format_status(Status(track['status']))} {track['name']}{blocked}")
            print(f"   ID: {track['id']}")
            print(f"   Progress: {track['progress']['sprints']} sprints, {track['progress']['completion']} complete")

    print("="*80 + "\n")


def print_sprints(sprints: List[Dict[str, Any]]):
    """Pretty print sprints list."""
    print(f"\n🏃 Sprints ({len(sprints)})")
    print("="*80)

    if not sprints:
        print("  No sprints found.")
    else:
        current_track = None
        for sprint in sprints:
            # Print track header if changed
            if sprint['track_id'] != current_track:
                current_track = sprint['track_id']
                print(f"\n  Track: {sprint['track_name']} ({sprint['track_id']})")

            blocked = " ⚠️" if sprint['blocked'] else ""
            print(f"    {format_status(Status(sprint['status']))} {sprint['name']}{blocked}")
            print(f"       ID: {sprint['id']}")
            print(f"       Progress: {sprint['progress']['tasks']} tasks, {sprint['progress']['completion']} complete")

    print("="*80 + "\n")


def print_tasks(tasks: List[Dict[str, Any]]):
    """Pretty print tasks list."""
    print(f"\n✅ Tasks ({len(tasks)})")
    print("="*80)

    if not tasks:
        print("  No tasks found.")
    else:
        current_sprint = None
        for task in tasks:
            # Print sprint header if changed
            if task['sprint_id'] != current_sprint:
                current_sprint = task['sprint_id']
                print(f"\n  Track: {task['track_name']} → Sprint: {task['sprint_name']} ({task['sprint_id']})")

            blocked = " ⚠️" if task['blocked'] else ""
            agent = f" (assigned: {task['assigned_agent']})" if task['assigned_agent'] else " (unassigned)"
            type_marker = f" [{task['task_type']}]" if task['task_type'] != "development" else ""

            print(f"    {format_status(Status(task['status']) if task['task_type'] == 'development' else task['status'])} {task['name']}{type_marker}{agent}{blocked}")
            print(f"       ID: {task['id']}")

    print("="*80 + "\n")


def handle_list(args):
    """Handle 'roadmap list' command."""
    # Find root directory
    if args.dir:
        root_dir = args.dir
    else:
        root_dir = find_roadmap_root()
        if not root_dir:
            print("❌ No roadmap found. Run 'roadmap init' first.")
            sys.exit(1)

    fs = FileSystemManager(root_dir)

    # Determine what to list
    list_type = args.type

    if not list_type or list_type == 'tracks':
        tracks = list_tracks(fs, args.status)

        if args.json:
            print(json.dumps({"tracks": tracks}, indent=2))
        else:
            print_tracks(tracks)

    if not list_type or list_type == 'sprints':
        sprints = list_sprints(fs, args.status)

        if args.json:
            print(json.dumps({"sprints": sprints}, indent=2))
        else:
            print_sprints(sprints)

    if not list_type or list_type == 'tasks':
        tasks = list_tasks(fs, args.status)

        if args.json:
            print(json.dumps({"tasks": tasks}, indent=2))
        else:
            print_tasks(tasks)
