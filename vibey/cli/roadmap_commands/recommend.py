"""
'roadmap recommend' command - Get task recommendations.
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

from roadmap.serialization import load_tasks
from filesystem import FileSystemManager, find_roadmap_root
from agents import AgentRouter


def print_recommendations(recommendations, agent=None):
    """Pretty print task recommendations."""
    if agent:
        print(f"\n🎯 Task Recommendations for {agent}")
    else:
        print(f"\n🎯 Task Recommendations")

    print("="*80)

    if not recommendations:
        print("\n  No tasks available to recommend.")
        if agent:
            print(f"\n💡 Tip: Try without --agent to see all available tasks")
        else:
            print(f"\n💡 Tip: All tasks are either assigned, in progress, or blocked")
    else:
        print(f"\n  Found {len(recommendations)} task(s) ready to work on:\n")

        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec['task_name']}")
            print(f"   ID: {rec['task_id']}")
            print(f"   Sprint: {rec['sprint_name']} ({rec['sprint_id']})")
            print(f"   Track: {rec['track_name']} ({rec['track_id']})")

            if rec['assigned_agent']:
                print(f"   Assigned: {rec['assigned_agent']}")
            else:
                print(f"   Assigned: Unassigned")

            if rec['recommended_agents']:
                agents_str = ", ".join([
                    f"{a} ({s:.0%})" for a, s in rec['recommended_agents']
                ])
                print(f"   Recommended agents: {agents_str}")

            print(f"   Priority score: {rec['priority_score']:.2f}")
            print()

        print("💡 To start working on a task:")
        print(f"   roadmap start {recommendations[0]['task_id']}")
        if not agent and recommendations[0]['recommended_agents']:
            best_agent = recommendations[0]['recommended_agents'][0][0]
            print(f"   roadmap assign {recommendations[0]['task_id']} {best_agent}")

    print("="*80 + "\n")


def handle_recommend(args):
    """Handle 'roadmap recommend' command."""
    # Find root directory
    if args.dir:
        root_dir = args.dir
    else:
        root_dir = find_roadmap_root()
        if not root_dir:
            print("❌ No roadmap found. Run 'roadmap init' first.")
            sys.exit(1)

    fs = FileSystemManager(root_dir)
    router = AgentRouter(root_dir)

    # Get recommendations
    if args.task:
        # Recommend agents for a specific task
        task_id = args.task

        # Extract sprint ID from task ID
        parts = task_id.split('-')
        if len(parts) < 3:
            print(f"❌ Invalid task ID format: {task_id}")
            sys.exit(1)

        sprint_id = '-'.join(parts[:2])
        tasks_path = fs.get_tasks_path(sprint_id)

        if not tasks_path.exists():
            print(f"❌ Task file not found for sprint '{sprint_id}'")
            sys.exit(1)

        tasks = load_tasks(tasks_path)
        task = next((t for t in tasks if t.id == task_id), None)

        if not task:
            print(f"❌ Task '{task_id}' not found")
            sys.exit(1)

        # Get agent recommendations
        recommendations = router.recommend_agent_for_task(task)

        if args.json:
            print(json.dumps({
                "task_id": task_id,
                "task_name": task.title,
                "recommendations": [
                    {"agent": agent, "confidence": score}
                    for agent, score in recommendations
                ]
            }, indent=2))
        else:
            print(f"\n🤖 Agent Recommendations for: {task.title}")
            print("="*80)

            if recommendations:
                print(f"\nRecommended agents (by confidence):\n")
                for i, (agent, score) in enumerate(recommendations, 1):
                    bar_length = int(score * 40)
                    bar = "█" * bar_length + "░" * (40 - bar_length)
                    print(f"{i}. {agent:25} {bar} {score:.0%}")

                print(f"\n💡 To assign this task:")
                print(f"   roadmap assign {task_id} {recommendations[0][0]}")
            else:
                print("\n  No agent recommendations available for this task.")

            print("="*80 + "\n")

    else:
        # Recommend tasks to work on
        max_recs = args.limit or 5
        recommendations = router.recommend_next_task(
            agent=args.agent,
            max_recommendations=max_recs
        )

        if args.json:
            print(json.dumps({"recommendations": recommendations}, indent=2))
        else:
            print_recommendations(recommendations, agent=args.agent)
