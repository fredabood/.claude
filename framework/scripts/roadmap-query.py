#!/usr/bin/env python3
"""
Query roadmap state.

Provides read operations for roadmap, tracks, sprints, and tasks.
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add framework to path
framework_root = Path(__file__).parent.parent
sys.path.insert(0, str(framework_root))

# Add roadmap-lib to path
roadmap_lib_path = Path(__file__).parent / "roadmap-lib"
sys.path.insert(0, str(roadmap_lib_path))

from roadmap.models import Roadmap, Track, Sprint, Task, Status
from roadmap.serialization import load_roadmap, load_track, load_sprint, load_tasks
from filesystem import FileSystemManager, find_roadmap_root
from dependencies import DependencyResolver
from blockers import BlockerComputer


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


def format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def query_roadmap_summary(fs: FileSystemManager) -> Dict[str, Any]:
    """Get roadmap summary."""
    roadmap_path = fs.get_roadmap_path()
    if not roadmap_path.exists():
        return {"error": "Roadmap not found"}

    roadmap = load_roadmap(roadmap_path)

    return {
        "id": roadmap.id,
        "name": roadmap.name,
        "version": roadmap.version,
        "status": roadmap.status.value,
        "blocked": roadmap.blocked,
        "created": format_datetime(roadmap.created),
        "progress": {
            "tracks": f"{roadmap.progress.tracks_completed}/{roadmap.progress.tracks_total}",
            "sprints": f"{roadmap.progress.sprints_completed}/{roadmap.progress.sprints_total}",
            "tasks": f"{roadmap.progress.tasks_completed}/{roadmap.progress.tasks_total}",
            "completion": f"{roadmap.progress.completion_percent}%",
        },
        "tracks": [
            {
                "id": track.id,
                "name": track.name,
                "status": track.status.value,
            }
            for track in roadmap.tracks
        ],
    }


def query_track_details(fs: FileSystemManager, track_id: str) -> Dict[str, Any]:
    """Get detailed track information."""
    track_path = fs.get_track_path(track_id)
    if not track_path.exists():
        return {"error": f"Track '{track_id}' not found"}

    track = load_track(track_path)

    return {
        "id": track.id,
        "name": track.name,
        "description": track.description,
        "status": track.status.value,
        "blocked": track.blocked,
        "started": format_datetime(track.started) if track.started else None,
        "completed": format_datetime(track.completed) if track.completed else None,
        "estimated_duration": track.estimated_duration,
        "progress": {
            "sprints": f"{track.progress.sprints_completed}/{track.progress.sprints_total}",
            "tasks": f"{track.progress.tasks_completed}/{track.progress.tasks_total}",
            "completion": f"{track.progress.completion_percent}%",
        },
        "sprints": [
            {
                "id": sprint.id,
                "name": sprint.name,
                "status": sprint.status.value,
            }
            for sprint in track.sprints
        ],
        "dependencies": [
            {
                "target_id": dep.target_id,
                "type": dep.type.value,
                "target_status": dep.target_status,
            }
            for dep in track.dependencies
        ],
    }


def query_sprint_details(fs: FileSystemManager, sprint_id: str) -> Dict[str, Any]:
    """Get detailed sprint information."""
    sprint_path = fs.get_sprint_path(sprint_id)
    if not sprint_path.exists():
        return {"error": f"Sprint '{sprint_id}' not found"}

    sprint = load_sprint(sprint_path)

    # Load tasks
    tasks_path = fs.get_tasks_path(sprint_id)
    tasks = load_tasks(tasks_path) if tasks_path.exists() else []

    # Categorize tasks
    dev_tasks = [t for t in tasks if not t.is_quality_gate()]
    completion_gates = [t for t in tasks if t.is_quality_gate() and t.task_type == "completion_gate"]
    production_gates = [t for t in tasks if t.is_quality_gate() and t.task_type == "production_gate"]

    return {
        "id": sprint.id,
        "name": sprint.name,
        "description": sprint.description,
        "status": sprint.status.value,
        "blocked": sprint.blocked,
        "started": format_datetime(sprint.started) if sprint.started else None,
        "completed": format_datetime(sprint.completed) if sprint.completed else None,
        "estimated_duration": sprint.estimated_duration,
        "progress": {
            "tasks": f"{sprint.progress.tasks_completed}/{sprint.progress.tasks_total}",
            "completion": f"{sprint.progress.completion_percent}%",
        },
        "development_gates": [
            {
                "target_id": gate.target_id,
                "type": gate.type.value,
                "target_status": gate.target_status,
            }
            for gate in sprint.development_gates
        ],
        "tasks": {
            "development": [
                {
                    "id": task.id,
                    "name": task.name,
                    "status": task.status.value,
                    "blocked": task.blocked,
                }
                for task in dev_tasks
            ],
            "completion_gates": [
                {
                    "id": task.id,
                    "name": task.name,
                    "status": task.status.value,
                    "gate_type": task.gate_info.gate_type if task.gate_info else None,
                }
                for task in completion_gates
            ],
            "production_gates": [
                {
                    "id": task.id,
                    "name": task.name,
                    "status": task.status.value,
                    "gate_type": task.gate_info.gate_type if task.gate_info else None,
                }
                for task in production_gates
            ],
        },
    }


def query_task_details(fs: FileSystemManager, task_id: str) -> Dict[str, Any]:
    """Get detailed task information."""
    # Extract sprint ID from task ID (e.g., backend-1-task-001 -> backend-1)
    parts = task_id.split('-')
    if len(parts) < 3:
        return {"error": f"Invalid task ID format: {task_id}"}

    sprint_id = '-'.join(parts[:2])
    tasks_path = fs.get_tasks_path(sprint_id)

    if not tasks_path.exists():
        return {"error": f"Tasks file not found for sprint '{sprint_id}'"}

    tasks = load_tasks(tasks_path)

    # Find task
    task = None
    for t in tasks:
        if t.id == task_id:
            task = t
            break

    if not task:
        return {"error": f"Task '{task_id}' not found"}

    return {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "task_type": task.task_type,
        "status": task.status.value,
        "blocked": task.blocked,
        "estimated_duration": task.estimated_duration,
        "started": format_datetime(task.started) if task.started else None,
        "completed": format_datetime(task.completed) if task.completed else None,
        "assigned_agent": task.assigned_agent,
        "dependencies": [
            {
                "target_id": dep.target_id,
                "type": dep.type.value,
                "target_status": dep.target_status,
            }
            for dep in task.dependencies
        ],
        "gate_info": {
            "gate_type": task.gate_info.gate_type,
            "criteria": task.gate_info.criteria,
            "audit_script": task.gate_info.audit_script,
        } if task.gate_info else None,
    }


def query_blockers(fs: FileSystemManager, object_id: Optional[str] = None) -> Dict[str, Any]:
    """Get blockers for object or entire roadmap."""
    computer = BlockerComputer(fs.root_dir)

    if object_id:
        # Determine object type and load
        if fs.track_exists(object_id):
            obj = load_track(fs.get_track_path(object_id))
            blockers = computer.compute_track_blockers(obj)
        elif fs.sprint_exists(object_id):
            obj = load_sprint(fs.get_sprint_path(object_id))
            blockers = computer.compute_sprint_blockers(obj)
        else:
            # Try as task
            parts = object_id.split('-')
            if len(parts) >= 3:
                sprint_id = '-'.join(parts[:2])
                tasks_path = fs.get_tasks_path(sprint_id)
                if tasks_path.exists():
                    tasks = load_tasks(tasks_path)
                    task = next((t for t in tasks if t.id == object_id), None)
                    if task:
                        blockers = computer.compute_task_blockers(task)
                    else:
                        return {"error": f"Object '{object_id}' not found"}
                else:
                    return {"error": f"Object '{object_id}' not found"}
            else:
                return {"error": f"Object '{object_id}' not found"}

        return {
            "object_id": object_id,
            "blocked": len(blockers) > 0,
            "blockers": [
                {
                    "dependency_id": b.dependency_id,
                    "dependency_type": b.dependency_type,
                    "current_status": b.current_status,
                    "required_status": b.required_status,
                    "blocking_since": format_datetime(b.blocking_since),
                }
                for b in blockers
            ],
        }
    else:
        # Get all blockers in roadmap
        roadmap = load_roadmap(fs.get_roadmap_path())
        all_blockers = {}

        for track in roadmap.tracks:
            track_obj = load_track(fs.get_track_path(track.id))
            blockers = computer.compute_track_blockers(track_obj)
            if blockers:
                all_blockers[track.id] = [
                    {
                        "dependency_id": b.dependency_id,
                        "dependency_type": b.dependency_type,
                        "current_status": b.current_status,
                        "required_status": b.required_status,
                    }
                    for b in blockers
                ]

        return {"blockers": all_blockers}


def query_dependencies(fs: FileSystemManager) -> Dict[str, Any]:
    """Get dependency graph information."""
    resolver = DependencyResolver(fs.root_dir)
    resolver.build_dependency_graph()

    # Detect circular dependencies
    cycles = resolver.detect_circular_dependencies()

    return {
        "nodes": len(resolver.dependency_graph),
        "has_circular_dependencies": len(cycles) > 0,
        "circular_dependencies": cycles,
    }


def print_roadmap_summary(data: Dict[str, Any]):
    """Pretty print roadmap summary."""
    print("\n" + "="*60)
    print(f"Roadmap: {data['name']}")
    print("="*60)
    print(f"ID: {data['id']}")
    print(f"Version: {data['version']}")
    print(f"Status: {format_status(Status(data['status']))}")
    print(f"Blocked: {'Yes ⚠️' if data['blocked'] else 'No'}")
    print(f"Created: {data['created']}")

    print(f"\n📊 Progress:")
    print(f"  Tracks:  {data['progress']['tracks']} ({data['progress']['completion']} complete)")
    print(f"  Sprints: {data['progress']['sprints']}")
    print(f"  Tasks:   {data['progress']['tasks']}")

    print(f"\n🛤️  Tracks:")
    for track in data['tracks']:
        print(f"  {format_status(Status(track['status']))} {track['name']} ({track['id']})")


def print_track_details(data: Dict[str, Any]):
    """Pretty print track details."""
    print("\n" + "="*60)
    print(f"Track: {data['name']}")
    print("="*60)
    print(f"ID: {data['id']}")
    print(f"Status: {format_status(Status(data['status']))}")
    print(f"Blocked: {'Yes ⚠️' if data['blocked'] else 'No'}")
    print(f"Description: {data['description']}")

    if data['started']:
        print(f"Started: {data['started']}")
    if data['completed']:
        print(f"Completed: {data['completed']}")

    print(f"Estimated Duration: {data['estimated_duration']}")

    print(f"\n📊 Progress:")
    print(f"  Sprints: {data['progress']['sprints']} ({data['progress']['completion']} complete)")
    print(f"  Tasks:   {data['progress']['tasks']}")

    if data['dependencies']:
        print(f"\n🔗 Dependencies:")
        for dep in data['dependencies']:
            print(f"  - {dep['target_id']} ({dep['type']}) must be {dep['target_status']}")

    print(f"\n🏃 Sprints:")
    for sprint in data['sprints']:
        print(f"  {format_status(Status(sprint['status']))} {sprint['name']} ({sprint['id']})")


def print_sprint_details(data: Dict[str, Any]):
    """Pretty print sprint details."""
    print("\n" + "="*60)
    print(f"Sprint: {data['name']}")
    print("="*60)
    print(f"ID: {data['id']}")
    print(f"Status: {format_status(Status(data['status']))}")
    print(f"Blocked: {'Yes ⚠️' if data['blocked'] else 'No'}")
    print(f"Description: {data['description']}")

    if data['started']:
        print(f"Started: {data['started']}")
    if data['completed']:
        print(f"Completed: {data['completed']}")

    print(f"Estimated Duration: {data['estimated_duration']}")

    print(f"\n📊 Progress:")
    print(f"  Tasks: {data['progress']['tasks']} ({data['progress']['completion']} complete)")

    if data['development_gates']:
        print(f"\n🚪 Development Gates:")
        for gate in data['development_gates']:
            print(f"  - {gate['target_id']} ({gate['type']}) must be {gate['target_status']}")

    print(f"\n✅ Development Tasks ({len(data['tasks']['development'])}):")
    for task in data['tasks']['development']:
        blocked_marker = " ⚠️" if task['blocked'] else ""
        print(f"  {format_status(Status(task['status']))} {task['name']}{blocked_marker}")

    if data['tasks']['completion_gates']:
        print(f"\n🚧 Completion Gates ({len(data['tasks']['completion_gates'])}):")
        for task in data['tasks']['completion_gates']:
            print(f"  {format_status(Status(task['status']))} {task['name']} ({task['gate_type']})")

    if data['tasks']['production_gates']:
        print(f"\n🔍 Production Gates ({len(data['tasks']['production_gates'])}):")
        for task in data['tasks']['production_gates']:
            print(f"  {format_status(Status(task['status']))} {task['name']} ({task['gate_type']})")


def main():
    parser = argparse.ArgumentParser(
        description="Query roadmap state",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show roadmap summary
  python3 roadmap-query.py

  # Show track details
  python3 roadmap-query.py --track backend

  # Show sprint details
  python3 roadmap-query.py --sprint backend-1

  # Show task details
  python3 roadmap-query.py --task backend-1-task-001

  # Show blockers
  python3 roadmap-query.py --blockers
  python3 roadmap-query.py --blockers --id backend-1

  # JSON output
  python3 roadmap-query.py --json
        """
    )

    parser.add_argument(
        "--dir",
        type=Path,
        help="Root directory (defaults to searching upward for .vibey/)"
    )

    parser.add_argument(
        "--track",
        type=str,
        help="Show track details"
    )

    parser.add_argument(
        "--sprint",
        type=str,
        help="Show sprint details"
    )

    parser.add_argument(
        "--task",
        type=str,
        help="Show task details"
    )

    parser.add_argument(
        "--blockers",
        action="store_true",
        help="Show blockers"
    )

    parser.add_argument(
        "--id",
        type=str,
        help="Object ID (for --blockers)"
    )

    parser.add_argument(
        "--dependencies",
        action="store_true",
        help="Show dependency graph information"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
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

    # Execute query
    if args.track:
        data = query_track_details(fs, args.track)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            if "error" in data:
                print(f"❌ {data['error']}")
                sys.exit(1)
            print_track_details(data)

    elif args.sprint:
        data = query_sprint_details(fs, args.sprint)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            if "error" in data:
                print(f"❌ {data['error']}")
                sys.exit(1)
            print_sprint_details(data)

    elif args.task:
        data = query_task_details(fs, args.task)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            if "error" in data:
                print(f"❌ {data['error']}")
                sys.exit(1)
            print(json.dumps(data, indent=2))

    elif args.blockers:
        data = query_blockers(fs, args.id)
        print(json.dumps(data, indent=2))

    elif args.dependencies:
        data = query_dependencies(fs)
        print(json.dumps(data, indent=2))

    else:
        # Default: roadmap summary
        data = query_roadmap_summary(fs)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            if "error" in data:
                print(f"❌ {data['error']}")
                sys.exit(1)
            print_roadmap_summary(data)


if __name__ == "__main__":
    main()
