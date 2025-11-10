"""
'roadmap deps' command - Show dependencies and blockers.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add framework to path
framework_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_root))

# Add roadmap-lib to path
roadmap_lib_path = Path(__file__).parent.parent / "roadmap-lib"
sys.path.insert(0, str(roadmap_lib_path))

from roadmap.serialization import load_roadmap, load_track, load_sprint, load_tasks
from filesystem import FileSystemManager, find_roadmap_root
from dependencies import DependencyResolver
from blockers import BlockerComputer


def get_dependency_info(fs: FileSystemManager, object_id: Optional[str] = None) -> Dict[str, Any]:
    """Get dependency and blocker information."""
    resolver = DependencyResolver(fs.root_dir)
    resolver.build_dependency_graph()

    computer = BlockerComputer(fs.root_dir)

    if object_id:
        # Get info for specific object
        dependencies = resolver.get_dependencies(object_id)
        dependents = resolver.get_dependents(object_id)
        transitive_deps = list(resolver.get_transitive_dependencies(object_id))

        # Get blockers
        blockers = []
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

        return {
            "object_id": object_id,
            "direct_dependencies": dependencies,
            "transitive_dependencies": transitive_deps,
            "dependents": dependents,
            "blocked": len(blockers) > 0,
            "blockers": [
                {
                    "dependency_id": b.dependency_id,
                    "dependency_type": b.dependency_type,
                    "current_status": b.current_status,
                    "required_status": b.required_status,
                }
                for b in blockers
            ],
        }
    else:
        # Get overall dependency graph info
        cycles = resolver.detect_circular_dependencies()

        # Get all blocked objects
        roadmap = load_roadmap(fs.get_roadmap_path())
        blocked_objects = {}

        for track_summary in roadmap.tracks:
            track = load_track(fs.get_track_path(track_summary.id))
            blockers = computer.compute_track_blockers(track)
            if blockers:
                blocked_objects[track.id] = {
                    "name": track.name,
                    "type": "track",
                    "blockers": [
                        {
                            "dependency_id": b.dependency_id,
                            "current_status": b.current_status,
                            "required_status": b.required_status,
                        }
                        for b in blockers
                    ],
                }

            for sprint_summary in track.sprints:
                sprint = load_sprint(fs.get_sprint_path(sprint_summary.id))
                blockers = computer.compute_sprint_blockers(sprint)
                if blockers:
                    blocked_objects[sprint.id] = {
                        "name": sprint.name,
                        "type": "sprint",
                        "track": track.name,
                        "blockers": [
                            {
                                "dependency_id": b.dependency_id,
                                "current_status": b.current_status,
                                "required_status": b.required_status,
                            }
                            for b in blockers
                        ],
                    }

        return {
            "graph_nodes": len(resolver.dependency_graph),
            "has_circular_dependencies": len(cycles) > 0,
            "circular_dependencies": cycles,
            "blocked_objects": blocked_objects,
        }


def print_single_object_deps(data: Dict[str, Any]):
    """Pretty print dependencies for a single object."""
    print(f"\n🔗 Dependencies for: {data['object_id']}")
    print("="*80)

    # Direct dependencies
    if data['direct_dependencies']:
        print(f"\n📌 Direct Dependencies ({len(data['direct_dependencies'])}):")
        for dep_id in data['direct_dependencies']:
            print(f"  - {dep_id}")
    else:
        print("\n📌 Direct Dependencies: None")

    # Transitive dependencies
    if data['transitive_dependencies']:
        print(f"\n🔄 All Dependencies (Transitive) ({len(data['transitive_dependencies'])}):")
        for dep_id in data['transitive_dependencies']:
            print(f"  - {dep_id}")

    # Dependents
    if data['dependents']:
        print(f"\n⬆️  Depended On By ({len(data['dependents'])}):")
        for dep_id in data['dependents']:
            print(f"  - {dep_id}")
    else:
        print("\n⬆️  Depended On By: None")

    # Blockers
    if data['blocked']:
        print(f"\n⚠️  BLOCKED - {len(data['blockers'])} blocker(s):")
        for blocker in data['blockers']:
            print(f"\n  Blocker: {blocker['dependency_id']}")
            print(f"    Current Status:  {blocker['current_status']}")
            print(f"    Required Status: {blocker['required_status']}")
    else:
        print("\n✅ Not Blocked")

    print("="*80 + "\n")


def print_overall_deps(data: Dict[str, Any]):
    """Pretty print overall dependency information."""
    print(f"\n🔗 Dependency Graph Overview")
    print("="*80)

    print(f"\n📊 Graph Statistics:")
    print(f"  Total Nodes: {data['graph_nodes']}")

    # Circular dependencies
    if data['has_circular_dependencies']:
        print(f"\n⚠️  CIRCULAR DEPENDENCIES DETECTED:")
        for cycle in data['circular_dependencies']:
            print(f"    {' → '.join(cycle)}")
        print(f"\n💡 Fix: Break one of the circular dependencies to unblock the graph")
    else:
        print(f"\n✅ No Circular Dependencies")

    # Blocked objects
    blocked_count = len(data['blocked_objects'])
    if blocked_count > 0:
        print(f"\n⚠️  Blocked Objects ({blocked_count}):")

        for obj_id, obj_data in data['blocked_objects'].items():
            track_info = f" (Track: {obj_data['track']})" if 'track' in obj_data else ""
            print(f"\n  {obj_data['type'].upper()}: {obj_data['name']}{track_info}")
            print(f"    ID: {obj_id}")
            print(f"    Blocked by {len(obj_data['blockers'])} dependency(ies):")

            for blocker in obj_data['blockers']:
                print(f"      - {blocker['dependency_id']}")
                print(f"        Current: {blocker['current_status']}, Required: {blocker['required_status']}")

        print(f"\n💡 Use 'roadmap show <id>' to see details and 'roadmap deps <id>' for specific dependency info")
    else:
        print(f"\n✅ No Blocked Objects")

    print("="*80 + "\n")


def handle_deps(args):
    """Handle 'roadmap deps' command."""
    # Find root directory
    if args.dir:
        root_dir = args.dir
    else:
        root_dir = find_roadmap_root()
        if not root_dir:
            print("❌ No roadmap found. Run 'roadmap init' first.")
            sys.exit(1)

    fs = FileSystemManager(root_dir)

    # Get dependency info
    data = get_dependency_info(fs, args.id)

    # Output
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        if args.id:
            print_single_object_deps(data)
        else:
            print_overall_deps(data)
