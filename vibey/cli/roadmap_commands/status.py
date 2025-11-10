"""
'roadmap status' command - Show roadmap status overview.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add framework to path
framework_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_root))

# Add roadmap-lib to path
roadmap_lib_path = Path(__file__).parent.parent / "roadmap-lib"
sys.path.insert(0, str(roadmap_lib_path))

from roadmap.models import Status
from roadmap.serialization import load_roadmap, load_track
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


def get_status_data(fs: FileSystemManager) -> Dict[str, Any]:
    """Get status data for roadmap."""
    roadmap_path = fs.get_roadmap_path()
    if not roadmap_path.exists():
        return {"error": "Roadmap not found"}

    roadmap = load_roadmap(roadmap_path)

    # Load track details
    tracks_data = []
    for track_summary in roadmap.tracks:
        track_path = fs.get_track_path(track_summary.id)
        if track_path.exists():
            track = load_track(track_path)
            tracks_data.append({
                "id": track.id,
                "name": track.name,
                "status": track.status.value,
                "blocked": track.blocked,
                "progress": {
                    "sprints": f"{track.progress.sprints_completed}/{track.progress.sprints_total}",
                    "tasks": f"{track.progress.tasks_completed}/{track.progress.tasks_total}",
                    "completion": f"{track.progress.completion_percent}%",
                },
                "sprints": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "status": s.status.value,
                    }
                    for s in track.sprints
                ],
            })

    return {
        "id": roadmap.id,
        "name": roadmap.name,
        "version": roadmap.version,
        "status": roadmap.status.value,
        "blocked": roadmap.blocked,
        "progress": {
            "tracks": f"{roadmap.progress.tracks_completed}/{roadmap.progress.tracks_total}",
            "sprints": f"{roadmap.progress.sprints_completed}/{roadmap.progress.sprints_total}",
            "tasks": f"{roadmap.progress.tasks_completed}/{roadmap.progress.tasks_total}",
            "completion": f"{roadmap.progress.completion_percent}%",
        },
        "tracks": tracks_data,
    }


def print_status(data: Dict[str, Any]):
    """Pretty print status."""
    print("\n" + "="*80)
    print(f"🗺️  {data['name']}")
    print("="*80)
    print(f"ID:      {data['id']}")
    print(f"Version: {data['version']}")
    print(f"Status:  {format_status(Status(data['status']))}")
    if data['blocked']:
        print(f"Blocked: Yes ⚠️")

    print(f"\n📊 Overall Progress")
    print(f"  Tracks:  {data['progress']['tracks']:>10}  ({data['progress']['completion']} complete)")
    print(f"  Sprints: {data['progress']['sprints']:>10}")
    print(f"  Tasks:   {data['progress']['tasks']:>10}")

    print(f"\n🛤️  Tracks")
    print("-" * 80)

    for track in data['tracks']:
        status_icon = "⚠️" if track['blocked'] else ""
        print(f"\n{format_status(Status(track['status']))} {track['name']} {status_icon}")
        print(f"   ID: {track['id']}")
        print(f"   Progress: {track['progress']['tasks']} tasks, {track['progress']['sprints']} sprints ({track['progress']['completion']} complete)")

        if track['sprints']:
            print(f"   Sprints:")
            for sprint in track['sprints']:
                print(f"     {format_status(Status(sprint['status']))} {sprint['name']} ({sprint['id']})")

    print("\n" + "="*80)
    print(f"💡 Tip: Use 'roadmap show <id>' for detailed information")
    print("="*80 + "\n")


def handle_status(args):
    """Handle 'roadmap status' command."""
    # Find root directory
    if args.dir:
        root_dir = args.dir
    else:
        root_dir = find_roadmap_root()
        if not root_dir:
            print("❌ No roadmap found. Run 'roadmap init' first.")
            sys.exit(1)

    fs = FileSystemManager(root_dir)

    # Get status data
    data = get_status_data(fs)

    if "error" in data:
        print(f"❌ {data['error']}")
        sys.exit(1)

    # Output
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print_status(data)
