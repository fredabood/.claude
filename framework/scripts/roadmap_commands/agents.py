"""
'roadmap agents' command - View agent workload and capabilities.
"""

import sys
import json
from pathlib import Path

# Add framework to path
framework_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_root))

# Add roadmap-lib to path
roadmap_lib_path = Path(__file__).parent.parent / "roadmap-lib"
sys.path.insert(0, str(roadmap_lib_path))

from filesystem import FileSystemManager, find_roadmap_root
from agents import AgentRouter, AGENT_CAPABILITIES


def print_agent_capabilities():
    """Print all available agents and their capabilities."""
    print("\n🤖 Available Agents")
    print("="*80)

    for agent_name, capabilities in AGENT_CAPABILITIES.items():
        print(f"\n{agent_name}")
        print(f"  Specialties: {', '.join(capabilities['specialties'])}")
        print(f"  Task types: {', '.join(capabilities['task_types'])}")
        print(f"  Keywords: {', '.join(capabilities['keywords'][:8])}...")

    print("="*80 + "\n")


def print_workload(workload):
    """Pretty print agent workload."""
    print("\n📊 Agent Workload")
    print("="*80)

    if not workload:
        print("\n  No agents currently assigned to tasks.")
        print("\n💡 Tip: Use 'roadmap recommend' to get task recommendations")
        print("="*80 + "\n")
        return

    # Sort by total tasks (descending)
    sorted_agents = sorted(
        workload.items(),
        key=lambda x: x[1]["total_tasks"],
        reverse=True
    )

    for agent, stats in sorted_agents:
        print(f"\n{agent}")
        print(f"  Total tasks:   {stats['total_tasks']}")
        print(f"  In progress:   {stats['in_progress']}")
        print(f"  Not started:   {stats['not_started']}")
        print(f"  Completed:     {stats['completed']}")

        # Calculate completion rate
        if stats['total_tasks'] > 0:
            completion_rate = stats['completed'] / stats['total_tasks']
            bar_length = int(completion_rate * 40)
            bar = "█" * bar_length + "░" * (40 - bar_length)
            print(f"  Completion:    {bar} {completion_rate:.0%}")

        # Show active tasks
        active_tasks = [
            t for t in stats['tasks']
            if t['status'] in ['not_started', 'in_progress']
        ]

        if active_tasks:
            print(f"  Active tasks:")
            for task in active_tasks[:3]:  # Show up to 3
                status_icon = "🔵" if task['status'] == 'in_progress' else "⚪"
                print(f"    {status_icon} {task['name']} ({task['id']})")

            if len(active_tasks) > 3:
                print(f"    ... and {len(active_tasks) - 3} more")

    print("\n💡 Tips:")
    print("  - Use 'roadmap recommend --agent <name>' to get recommendations for a specific agent")
    print("  - Use 'roadmap list tasks --json | jq' to query task assignments")
    print("="*80 + "\n")


def handle_agents(args):
    """Handle 'roadmap agents' command."""
    # Show capabilities (no roadmap needed)
    if args.capabilities:
        if args.json:
            print(json.dumps(AGENT_CAPABILITIES, indent=2))
        else:
            print_agent_capabilities()
        return

    # Find root directory for workload
    if args.dir:
        root_dir = args.dir
    else:
        root_dir = find_roadmap_root()
        if not root_dir:
            print("❌ No roadmap found. Run 'roadmap init' first.")
            sys.exit(1)

    router = AgentRouter(root_dir)

    # Show workload
    if args.workload or not args.capabilities:
        workload = router.get_agent_workload()

        if args.json:
            print(json.dumps(workload, indent=2))
        else:
            print_workload(workload)

    # Show specific agent details
    if args.agent:
        workload = router.get_agent_workload()

        if args.agent not in workload:
            print(f"❌ Agent '{args.agent}' has no assigned tasks")
            sys.exit(1)

        agent_stats = workload[args.agent]

        if args.json:
            print(json.dumps({args.agent: agent_stats}, indent=2))
        else:
            print(f"\n🤖 Agent: {args.agent}")
            print("="*80)

            print(f"\n📊 Statistics:")
            print(f"  Total tasks:   {agent_stats['total_tasks']}")
            print(f"  In progress:   {agent_stats['in_progress']}")
            print(f"  Not started:   {agent_stats['not_started']}")
            print(f"  Completed:     {agent_stats['completed']}")

            if agent_stats['total_tasks'] > 0:
                completion_rate = agent_stats['completed'] / agent_stats['total_tasks']
                print(f"  Completion:    {completion_rate:.0%}")

            print(f"\n📋 All Tasks:")
            for task in agent_stats['tasks']:
                status_icons = {
                    'not_started': '⚪',
                    'in_progress': '🔵',
                    'completed': '✅',
                }
                icon = status_icons.get(task['status'], '❓')
                print(f"  {icon} {task['name']}")
                print(f"     ID: {task['id']}")
                print(f"     Sprint: {task['sprint_id']}")
                print(f"     Track: {task['track_id']}")

            print("="*80 + "\n")
