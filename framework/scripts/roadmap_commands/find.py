"""
'roadmap find' command - Search for objects by name/description.
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


def format_status(status) -> str:
    """Format status with emoji."""
    status_map = {
        "not_started": "⚪",
        "in_progress": "🔵",
        "paused": "⏸️",
        "completion_gate_check": "🚧",
        "completed": "✅",
        "production_gate_check": "🔍",
        "production_ready": "🚀",
        "deployed": "🌟",
        "won't_do": "❌",
    }

    status_value = status.value if hasattr(status, 'value') else str(status)
    emoji = status_map.get(status_value, "❓")
    return f"{emoji} {status_value}"


def search_objects(
    fs: FileSystemManager,
    query: str,
    type_filter: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """Search for objects matching query."""
    query_lower = query.lower()
    results = {
        "tracks": [],
        "sprints": [],
        "tasks": [],
    }

    roadmap_path = fs.get_roadmap_path()
    if not roadmap_path.exists():
        return results

    roadmap = load_roadmap(roadmap_path)

    # Search tracks
    if not type_filter or type_filter == "track":
        for track_summary in roadmap.tracks:
            track_path = fs.get_track_path(track_summary.id)
            if track_path.exists():
                track = load_track(track_path)

                # Search in name, description, ID
                if (query_lower in track.name.lower() or
                    query_lower in track.description.lower() or
                    query_lower in track.id.lower()):

                    results["tracks"].append({
                        "id": track.id,
                        "name": track.name,
                        "description": track.description[:100] + "..." if len(track.description) > 100 else track.description,
                        "status": track.status.value,
                    })

    # Search sprints
    if not type_filter or type_filter == "sprint":
        for track_summary in roadmap.tracks:
            track_path = fs.get_track_path(track_summary.id)
            if track_path.exists():
                track = load_track(track_path)

                for sprint_summary in track.sprints:
                    sprint_path = fs.get_sprint_path(sprint_summary.id)
                    if sprint_path.exists():
                        sprint = load_sprint(sprint_path)

                        # Search in name, description, ID
                        if (query_lower in sprint.name.lower() or
                            query_lower in sprint.description.lower() or
                            query_lower in sprint.id.lower()):

                            results["sprints"].append({
                                "id": sprint.id,
                                "name": sprint.name,
                                "description": sprint.description[:100] + "..." if len(sprint.description) > 100 else sprint.description,
                                "track_id": track.id,
                                "track_name": track.name,
                                "status": sprint.status.value,
                            })

    # Search tasks
    if not type_filter or type_filter == "task":
        for track_summary in roadmap.tracks:
            track_path = fs.get_track_path(track_summary.id)
            if track_path.exists():
                track = load_track(track_path)

                for sprint_summary in track.sprints:
                    tasks_path = fs.get_tasks_path(sprint_summary.id)
                    if tasks_path.exists():
                        sprint_tasks = load_tasks(tasks_path)

                        for task in sprint_tasks:
                            # Search in name, description, ID
                            if (query_lower in task.name.lower() or
                                query_lower in task.description.lower() or
                                query_lower in task.id.lower()):

                                results["tasks"].append({
                                    "id": task.id,
                                    "name": task.name,
                                    "description": task.description[:100] + "..." if len(task.description) > 100 else task.description,
                                    "sprint_id": sprint_summary.id,
                                    "sprint_name": sprint_summary.name,
                                    "track_id": track.id,
                                    "track_name": track.name,
                                    "task_type": task.task_type,
                                    "status": task.status.value,
                                })

    return results


def print_results(query: str, results: Dict[str, List[Dict[str, Any]]]):
    """Pretty print search results."""
    total = len(results["tracks"]) + len(results["sprints"]) + len(results["tasks"])

    print(f"\n🔍 Search results for: \"{query}\"")
    print("="*80)

    if total == 0:
        print("\n  No results found.")
        print("\n💡 Tip: Try different search terms or use 'roadmap list' to see all objects")
    else:
        print(f"\n  Found {total} matching object(s)\n")

        # Print tracks
        if results["tracks"]:
            print(f"\n🛤️  Tracks ({len(results['tracks'])})")
            print("-" * 80)
            for track in results["tracks"]:
                print(f"\n  {format_status(track['status'])} {track['name']}")
                print(f"     ID: {track['id']}")
                print(f"     {track['description']}")

        # Print sprints
        if results["sprints"]:
            print(f"\n🏃 Sprints ({len(results['sprints'])})")
            print("-" * 80)
            for sprint in results["sprints"]:
                print(f"\n  {format_status(sprint['status'])} {sprint['name']}")
                print(f"     ID: {sprint['id']}")
                print(f"     Track: {sprint['track_name']} ({sprint['track_id']})")
                print(f"     {sprint['description']}")

        # Print tasks
        if results["tasks"]:
            print(f"\n✅ Tasks ({len(results['tasks'])})")
            print("-" * 80)
            for task in results["tasks"]:
                type_marker = f" [{task['task_type']}]" if task['task_type'] != "development" else ""
                print(f"\n  {format_status(task['status'])} {task['name']}{type_marker}")
                print(f"     ID: {task['id']}")
                print(f"     Sprint: {task['sprint_name']} ({task['sprint_id']})")
                print(f"     Track: {task['track_name']} ({task['track_id']})")
                print(f"     {task['description']}")

        print("\n💡 Use 'roadmap show <id>' to see full details")

    print("="*80 + "\n")


def handle_find(args):
    """Handle 'roadmap find' command."""
    # Find root directory
    if args.dir:
        root_dir = args.dir
    else:
        root_dir = find_roadmap_root()
        if not root_dir:
            print("❌ No roadmap found. Run 'roadmap init' first.")
            sys.exit(1)

    fs = FileSystemManager(root_dir)

    # Search
    results = search_objects(fs, args.query, args.type)

    # Output
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_results(args.query, results)
