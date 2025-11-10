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
from formatting import (
    table, header, status_indicator, progress_bar,
    colorize, bold, dim, Color, warning
)


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
                            "name": task.title,  # Task model uses 'title' not 'name'
                            "sprint_id": sprint_summary.id,
                            "sprint_name": sprint_summary.name,
                            "track_id": track.id,
                            "track_name": track.name,
                            "task_type": task.task_type.value if hasattr(task.task_type, 'value') else task.task_type,
                            "status": task.status.value if hasattr(task.status, 'value') else task.status,
                            "blocked": task.blocked,
                            "assigned_agent": task.assigned_agent,
                        })

    return tasks


def print_tracks(tracks: List[Dict[str, Any]]):
    """Pretty print tracks list."""
    print(header(f"Tracks ({len(tracks)})", level=1))

    if not tracks:
        print("  No tracks found.\n")
        return

    # Build table rows
    headers = ["Status", "Track Name", "ID", "Sprints", "Completion", "Progress"]
    rows = []

    for track in tracks:
        status_str = status_indicator(track['status'])
        name = track['name']
        if track['blocked']:
            name = f"{name} {colorize('⚠️ BLOCKED', Color.RED)}"

        # Parse progress for progress bar
        sprints_parts = track['progress']['sprints'].split('/')
        sprints_completed = int(sprints_parts[0])
        sprints_total = int(sprints_parts[1])
        completion_pct = int(track['progress']['completion'].replace('%', ''))

        rows.append([
            status_str,
            name,
            dim(track['id']),
            track['progress']['sprints'],
            track['progress']['completion'],
            progress_bar(sprints_completed, sprints_total, width=20, show_percentage=False)
        ])

    print(table(headers, rows))
    print()


def print_sprints(sprints: List[Dict[str, Any]]):
    """Pretty print sprints list."""
    print(header(f"Sprints ({len(sprints)})", level=1))

    if not sprints:
        print("  No sprints found.\n")
        return

    # Group sprints by track
    from itertools import groupby
    sprints_sorted = sorted(sprints, key=lambda s: s['track_id'])

    for track_id, track_sprints_iter in groupby(sprints_sorted, key=lambda s: s['track_id']):
        track_sprints = list(track_sprints_iter)
        first_sprint = track_sprints[0]

        # Print track header
        track_header = f"Track: {first_sprint['track_name']}"
        print(f"\n{bold(colorize(track_header, Color.CYAN))} {dim(f'({track_id})')}")
        print()

        # Build table rows for this track's sprints
        headers = ["Status", "Sprint Name", "ID", "Tasks", "Completion", "Progress"]
        rows = []

        for sprint in track_sprints:
            status_str = status_indicator(sprint['status'])
            name = sprint['name']
            if sprint['blocked']:
                name = f"{name} {colorize('⚠️ BLOCKED', Color.RED)}"

            # Parse progress for progress bar
            tasks_parts = sprint['progress']['tasks'].split('/')
            tasks_completed = int(tasks_parts[0])
            tasks_total = int(tasks_parts[1])

            rows.append([
                status_str,
                name,
                dim(sprint['id']),
                sprint['progress']['tasks'],
                sprint['progress']['completion'],
                progress_bar(tasks_completed, tasks_total, width=20, show_percentage=False)
            ])

        print(table(headers, rows))
        print()


def print_tasks(tasks: List[Dict[str, Any]]):
    """Pretty print tasks list."""
    print(header(f"Tasks ({len(tasks)})", level=1))

    if not tasks:
        print("  No tasks found.\n")
        return

    # Group tasks by sprint
    from itertools import groupby
    tasks_sorted = sorted(tasks, key=lambda t: (t['track_id'], t['sprint_id']))

    for (track_id, sprint_id), sprint_tasks_iter in groupby(tasks_sorted, key=lambda t: (t['track_id'], t['sprint_id'])):
        sprint_tasks = list(sprint_tasks_iter)
        first_task = sprint_tasks[0]

        # Print sprint header
        track_label = f"Track: {first_task['track_name']}"
        sprint_label = f"Sprint: {first_task['sprint_name']}"
        print(f"\n{bold(colorize(track_label, Color.CYAN))} → {bold(colorize(sprint_label, Color.BLUE))} {dim(f'({sprint_id})')}")
        print()

        # Build table rows for this sprint's tasks
        headers = ["Status", "Task Name", "ID", "Type", "Agent"]
        rows = []

        for task in sprint_tasks:
            status_str = status_indicator(task['status'])
            name = task['name']
            if task['blocked']:
                name = f"{name} {colorize('⚠️ BLOCKED', Color.RED)}"

            task_type = task['task_type'] if task['task_type'] != 'development' else ''
            agent = task['assigned_agent'] if task['assigned_agent'] else colorize('unassigned', Color.YELLOW)

            rows.append([
                status_str,
                name,
                dim(task['id']),
                task_type,
                agent
            ])

        print(table(headers, rows))
        print()


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
