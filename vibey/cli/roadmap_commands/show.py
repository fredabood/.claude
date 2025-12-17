"""
'roadmap show' command - Show details for a specific object.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add framework to path
framework_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_root))

# Add roadmap-lib to path
roadmap_lib_path = Path(__file__).parent.parent / "roadmap-lib"
sys.path.insert(0, str(roadmap_lib_path))

from roadmap.serialization import load_track, load_sprint, load_tasks
from filesystem import FileSystemManager, find_roadmap_root
from standards_formatter import (
    print_standards_section,
)


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
        "wont_do": "❌",
    }

    status_value = status.value if hasattr(status, 'value') else str(status)
    emoji = status_map.get(status_value, "❓")
    return f"{emoji} {status_value}"


def format_datetime(dt: Optional[datetime]) -> str:
    """Format datetime for display."""
    if not dt:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_object_data(fs: FileSystemManager, object_id: str) -> Dict[str, Any]:
    """Get data for an object (track, sprint, or task)."""
    # Try track first
    track_path = fs.get_track_path(object_id)
    if track_path.exists():
        track = load_track(track_path)
        return {
            "type": "track",
            "id": track.id,
            "name": track.name,
            "description": track.description,
            "status": track.status.value,
            "blocked": track.blocked,
            "started": format_datetime(track.started),
            "completed": format_datetime(track.completed),
            "estimated_duration": track.estimated_duration,
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
                    "estimated_duration": s.estimated_duration,
                }
                for s in track.sprints
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

    # Try sprint
    sprint_path = fs.get_sprint_path(object_id)
    if sprint_path.exists():
        sprint = load_sprint(sprint_path)

        # Load tasks
        tasks_path = fs.get_tasks_path(object_id)
        tasks = load_tasks(tasks_path) if tasks_path.exists() else []

        # Categorize tasks
        dev_tasks = [t for t in tasks if not t.is_quality_gate()]
        completion_gates = [t for t in tasks if t.is_quality_gate() and t.task_type == "completion_gate"]
        production_gates = [t for t in tasks if t.is_quality_gate() and t.task_type == "production_gate"]

        # Safe attribute access with fallbacks
        metadata = getattr(sprint, 'metadata', {})
        estimated_duration = metadata.get('estimated_duration') if isinstance(metadata, dict) else getattr(sprint, 'estimated_duration', None)

        return {
            "type": "sprint",
            "id": sprint.id,
            "name": sprint.name,
            "goal": getattr(sprint, 'goal', ''),
            "status": sprint.status.value if hasattr(sprint.status, 'value') else str(sprint.status),
            "blocked": sprint.blocked,
            "started": format_datetime(sprint.started),
            "completed": format_datetime(sprint.completed),
            "estimated_duration": estimated_duration,
            "progress": {
                "tasks": f"{sprint.progress.tasks_completed}/{sprint.progress.tasks_total}",
                "completion": f"{sprint.progress.completion_percent}%",
            },
            "development_gates": [
                {
                    "target_id": getattr(gate, 'target_id', ''),
                    "type": gate.type.value if hasattr(gate, 'type') else str(getattr(gate, 'type', '')),
                    "target_status": getattr(gate, 'target_status', ''),
                }
                for gate in (sprint.development_gates if hasattr(sprint, 'development_gates') else [])
            ],
            "tasks": {
                "development": [
                    {
                        "id": task.id,
                        "name": getattr(task, 'name', getattr(task, 'title', task.id)),
                        "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                        "blocked": task.blocked,
                        "assigned_agent": getattr(task, 'assigned_agent', None),
                    }
                    for task in dev_tasks
                ],
                "completion_gates": [
                    {
                        "id": task.id,
                        "name": getattr(task, 'name', getattr(task, 'title', task.id)),
                        "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                        "gate_type": getattr(task.gate_info, 'blocks_status', None) if hasattr(task, 'gate_info') and task.gate_info else None,
                    }
                    for task in completion_gates
                ],
                "production_gates": [
                    {
                        "id": task.id,
                        "name": getattr(task, 'name', getattr(task, 'title', task.id)),
                        "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                        "gate_type": getattr(task.gate_info, 'blocks_status', None) if hasattr(task, 'gate_info') and task.gate_info else None,
                    }
                    for task in production_gates
                ],
            },
        }

    # Try task
    parts = object_id.split('-')
    if len(parts) >= 3:
        sprint_id = '-'.join(parts[:2])
        tasks_path = fs.get_tasks_path(sprint_id)

        if tasks_path.exists():
            tasks = load_tasks(tasks_path)
            task = next((t for t in tasks if t.id == object_id), None)

            if task:
                return {
                    "type": "task",
                    "id": task.id,
                    "name": task.title,
                    "description": task.description,
                    "task_type": task.task_type,
                    "status": task.status.value,
                    "blocked": task.blocked,
                    "started": format_datetime(task.started),
                    "completed": format_datetime(task.completed),
                    "estimated_duration": task.estimated_duration,
                    "assigned_agent": task.assigned_agent or "Unassigned",
                    "dependencies": [
                        {
                            "target_id": dep.target_id,
                            "type": dep.type.value,
                            "target_status": dep.target_status,
                        }
                        for dep in task.dependencies
                    ],
                    "gate_info": {
                        "gate_type": getattr(task.gate_info, 'blocks_status', None),
                        "threshold": getattr(task.gate_info, 'threshold', None),
                        "is_blocking": getattr(task.gate_info, 'is_blocking', None),
                    } if task.gate_info else None,
                }

    return {"error": f"Object '{object_id}' not found"}


def print_track(data: Dict[str, Any], root_dir: Path = None):
    """Pretty print track details."""
    print("\n" + "="*80)
    print(f"🛤️  Track: {data['name']}")
    print("="*80)
    print(f"ID:          {data['id']}")
    print(f"Status:      {format_status(data['status'])}")
    if data['blocked']:
        print(f"Blocked:     Yes ⚠️")
    print(f"Started:     {data['started']}")
    print(f"Completed:   {data['completed']}")
    print(f"Duration:    {data['estimated_duration']}")

    print(f"\n📄 Description:")
    print(f"  {data['description']}")

    print(f"\n📊 Progress:")
    print(f"  Sprints: {data['progress']['sprints']}")
    print(f"  Tasks:   {data['progress']['tasks']}")
    print(f"  Overall: {data['progress']['completion']}")

    # Show standards if root_dir provided
    if root_dir:
        print(f"\n")
        print_standards_section(root_dir, data['id'], show_details=True)

    if data['dependencies']:
        print(f"\n🔗 Dependencies:")
        for dep in data['dependencies']:
            print(f"  - {dep['target_id']} ({dep['type']}) must be {dep['target_status']}")

    print(f"\n🏃 Sprints ({len(data['sprints'])}):")
    for sprint in data['sprints']:
        print(f"  {format_status(sprint['status'])} {sprint['name']}")
        print(f"     ID: {sprint['id']}, Duration: {sprint['estimated_duration']}")

    print("="*80 + "\n")


def print_sprint(data: Dict[str, Any], root_dir: Path = None):
    """Pretty print sprint details."""
    print("\n" + "="*80)
    print(f"🏃 Sprint: {data['name']}")
    print("="*80)
    print(f"ID:          {data['id']}")
    print(f"Status:      {format_status(data['status'])}")
    if data['blocked']:
        print(f"Blocked:     Yes ⚠️")
    print(f"Started:     {data['started']}")
    print(f"Completed:   {data['completed']}")
    print(f"Duration:    {data['estimated_duration']}")

    # Show goal if available
    if data.get('goal'):
        print(f"\n🎯 Goal:")
        print(f"  {data['goal']}")

    print(f"\n📊 Progress:")
    print(f"  Tasks:   {data['progress']['tasks']}")
    print(f"  Overall: {data['progress']['completion']}")

    # Show standards if root_dir provided
    if root_dir:
        print(f"\n")
        print_standards_section(root_dir, data['id'], show_details=True)

    if data['development_gates']:
        print(f"\n🚪 Development Gates:")
        for gate in data['development_gates']:
            print(f"  - {gate['target_id']} ({gate['type']}) must be {gate['target_status']}")

    dev_tasks = data['tasks']['development']
    if dev_tasks:
        print(f"\n✅ Development Tasks ({len(dev_tasks)}):")
        for task in dev_tasks:
            blocked = " ⚠️" if task['blocked'] else ""
            agent = f" (assigned: {task['assigned_agent']})" if task['assigned_agent'] else " (unassigned)"
            print(f"  {format_status(task['status'])} {task['name']}{agent}{blocked}")
            print(f"     ID: {task['id']}")

    completion_gates = data['tasks']['completion_gates']
    if completion_gates:
        print(f"\n🚧 Completion Gates ({len(completion_gates)}):")
        for task in completion_gates:
            print(f"  {format_status(task['status'])} {task['name']} ({task['gate_type']})")
            print(f"     ID: {task['id']}")

    production_gates = data['tasks']['production_gates']
    if production_gates:
        print(f"\n🔍 Production Gates ({len(production_gates)}):")
        for task in production_gates:
            print(f"  {format_status(task['status'])} {task['name']} ({task['gate_type']})")
            print(f"     ID: {task['id']}")

    print("="*80 + "\n")


def print_task(data: Dict[str, Any], root_dir: Path = None):
    """Pretty print task details."""
    print("\n" + "="*80)
    print(f"✅ Task: {data['name']}")
    print("="*80)
    print(f"ID:          {data['id']}")
    print(f"Type:        {data['task_type']}")
    print(f"Status:      {format_status(data['status'])}")
    if data['blocked']:
        print(f"Blocked:     Yes ⚠️")
    print(f"Agent:       {data['assigned_agent']}")
    print(f"Started:     {data['started']}")
    print(f"Completed:   {data['completed']}")
    print(f"Duration:    {data['estimated_duration']}")

    print(f"\n📄 Description:")
    print(f"  {data['description']}")

    # Show standards if root_dir provided
    if root_dir:
        print(f"\n")
        print_standards_section(root_dir, data['id'], show_details=True)

    if data['dependencies']:
        print(f"\n🔗 Dependencies:")
        for dep in data['dependencies']:
            print(f"  - {dep['target_id']} ({dep['type']}) must be {dep['target_status']}")

    if data['gate_info']:
        print(f"\n🚪 Gate Information:")
        print(f"  Blocks: {data['gate_info']['gate_type']}")
        print(f"  Threshold: {data['gate_info']['threshold']}")
        print(f"  Is Blocking: {data['gate_info']['is_blocking']}")

    print("="*80 + "\n")


def handle_show(args):
    """Handle 'roadmap show' command."""
    # Find root directory
    if args.dir:
        root_dir = args.dir
    else:
        root_dir = find_roadmap_root()
        if not root_dir:
            print("❌ No roadmap found. Run 'roadmap init' first.")
            sys.exit(1)

    fs = FileSystemManager(root_dir)

    # Get object data
    data = get_object_data(fs, args.id)

    if "error" in data:
        print(f"❌ {data['error']}")
        sys.exit(1)

    # Output
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        # Pass root_dir to print functions for standards display
        root_path = Path(root_dir)
        if data['type'] == 'track':
            print_track(data, root_path)
        elif data['type'] == 'sprint':
            print_sprint(data, root_path)
        elif data['type'] == 'task':
            print_task(data, root_path)
