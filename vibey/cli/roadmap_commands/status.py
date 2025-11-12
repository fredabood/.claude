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
from standards_formatter import (
    get_standards_for_item,
    format_standards_summary,
    get_standards_compliance_data,
)


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


def get_status_data(fs: FileSystemManager, show_standards: bool = True) -> Dict[str, Any]:
    """Get status data for roadmap."""
    roadmap_path = fs.get_roadmap_path()
    if not roadmap_path.exists():
        return {"error": "Roadmap not found"}

    roadmap = load_roadmap(roadmap_path)
    root_dir = fs.root_dir

    # Get roadmap-level standards
    roadmap_standards_data = None
    if show_standards:
        roadmap_standards = get_standards_for_item(root_dir, roadmap.id)
        if roadmap_standards:
            roadmap_standards_data = {
                "count": len(roadmap_standards),
                "summary": format_standards_summary(roadmap_standards, compact=True),
            }

    # Load track details
    tracks_data = []
    for track_summary in roadmap.tracks:
        track_path = fs.get_track_path(track_summary.id)
        if track_path.exists():
            track = load_track(track_path)

            # Get standards for track
            track_standards_data = None
            if show_standards:
                standards_data = get_standards_compliance_data(root_dir, track.id)
                if standards_data['total'] > 0:
                    track_standards_data = standards_data

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
                "standards": track_standards_data,
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
        "standards": roadmap_standards_data,
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

    # Show roadmap-level standards if any
    if data.get('standards'):
        print(f"📋 Standards: {data['standards']['summary']}")

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

        # Show track standards if any
        if track.get('standards'):
            std_data = track['standards']
            std_counts = []
            if std_data['blocking_count'] > 0:
                std_counts.append(f"🔴 {std_data['blocking_count']} blocking")
            if std_data['warning_count'] > 0:
                std_counts.append(f"🟡 {std_data['warning_count']} warning")
            if std_data['audit_count'] > 0:
                std_counts.append(f"🟢 {std_data['audit_count']} audit")
            print(f"   📋 Standards: {std_data['total']} ({', '.join(std_counts)})")

        if track['sprints']:
            print(f"   Sprints:")
            for sprint in track['sprints']:
                print(f"     {format_status(Status(sprint['status']))} {sprint['name']} ({sprint['id']})")

    print("\n" + "="*80)
    print(f"💡 Tip: Use 'roadmap show <id>' for detailed information")
    print(f"💡 Tip: Use 'roadmap check-standards <id>' to validate standards")
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

    # Check if standards should be shown
    show_standards = not getattr(args, 'no_standards', False)

    # Get status data
    data = get_status_data(fs, show_standards=show_standards)

    if "error" in data:
        print(f"❌ {data['error']}")
        sys.exit(1)

    # Output
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print_status(data)
