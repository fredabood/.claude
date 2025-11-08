"""
Plan Command Handler

Manages sprint plan creation from markdown files.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import yaml

# Add roadmap-lib to path
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir / "roadmap-lib"))

from filesystem import find_roadmap_root
from plan_parser import SprintPlanParser


def handle_plan(args):
    """Handle plan command."""
    if args.plan_action == 'create':
        create_sprint_from_plan(args)
    else:
        print(f"❌ Unknown plan action: {args.plan_action}")
        sys.exit(1)


def create_sprint_from_plan(args):
    """
    Create sprint and tasks from plan markdown file.

    Args:
        args: Command-line arguments
            - track_id: Track to add sprint to
            - from_plan: Path to plan markdown file
            - sprint_id: Optional sprint ID (auto-generated if not provided)
            - start: Whether to start sprint immediately
    """
    # Find roadmap root
    root_dir = find_roadmap_root()
    if not root_dir:
        print("❌ No roadmap found. Run 'roadmap init' first.")
        sys.exit(1)

    vibey_dir = root_dir / ".vibey"

    # Validate plan file exists
    plan_file = Path(args.from_plan)
    if not plan_file.exists():
        print(f"❌ Plan file not found: {plan_file}")
        sys.exit(1)

    print(f"📄 Parsing sprint plan: {plan_file.name}")

    # Parse plan file
    parser = SprintPlanParser(plan_file)
    plan_data = parser.parse()
    tasks_data = parser.extract_tasks()

    print(f"✓ Parsed plan:")
    print(f"  Name: {plan_data['name']}")
    print(f"  Goal: {plan_data['goal'][:60]}...")
    print(f"  Features: {len(plan_data['features'])}")
    print(f"  Tasks: {len(tasks_data)}")

    # Generate sprint ID if not provided
    sprint_id = args.sprint_id
    if not sprint_id:
        # Auto-generate from plan name
        name_slug = plan_data['name'].lower().replace(' ', '-')[:30]
        # Find next sprint number for this track
        sprint_dir = vibey_dir / "sprints"
        existing_sprints = list(sprint_dir.glob(f"{args.track_id}-*.yaml")) if sprint_dir.exists() else []
        sprint_number = len(existing_sprints) + 1
        sprint_id = f"{args.track_id}-{sprint_number}"

    print(f"\n📊 Creating sprint: {sprint_id}")

    # Create sprint YAML
    sprint = {
        'sprint': {
            'id': sprint_id,
            'track_id': args.track_id,
            'roadmap_id': 'vibey-framework-v2',  # TODO: Get from roadmap.yaml
            'name': plan_data['name'],
            'goal': plan_data['goal'],
            'status': 'in_progress' if args.start else 'not_started',
            'estimated_duration': f"{sum(t['estimated_hours'] for t in tasks_data)} hours",
            'created': datetime.now(timezone.utc).isoformat(),
            'started': datetime.now(timezone.utc).isoformat() if args.start else None,
            'completed': None,
            'plan_file': str(plan_file),
            'deliverables': plan_data.get('deliverables', []),
            'quality_gates': plan_data.get('quality_gates', []),
            'dependencies': [],
            'blocks': [],
            'blocked': False,
            'progress': {
                'tasks_total': len(tasks_data),
                'tasks_completed': 0,
                'completion_percent': 0
            }
        }
    }

    # Save sprint YAML
    sprint_file = vibey_dir / "sprints" / f"{sprint_id}.yaml"
    sprint_file.parent.mkdir(parents=True, exist_ok=True)

    with open(sprint_file, 'w') as f:
        yaml.dump(sprint, f, default_flow_style=False, sort_keys=False)

    print(f"✓ Created sprint file: {sprint_file.relative_to(root_dir)}")

    # Create tasks YAML
    task_counter = 1
    tasks = []

    for task_data in tasks_data:
        task_id = f"{sprint_id}-task-{task_counter:03d}"

        task = {
            'id': task_id,
            'sprint_id': sprint_id,
            'track_id': args.track_id,
            'roadmap_id': 'vibey-framework-v2',
            'title': task_data['name'],
            'description': task_data['description'],
            'what': task_data.get('what', ''),
            'why': task_data.get('why', ''),
            'how': task_data.get('how', ''),
            'status': 'not_started',
            'estimated_hours': task_data['estimated_hours'],
            'created': datetime.now(timezone.utc).isoformat(),
            'dependencies': [],
            'blocks': [],
            'blocked': False,
            'assigned_agents': [],
        }

        tasks.append(task)
        task_counter += 1

    # Save tasks YAML
    tasks_file = vibey_dir / "tasks" / f"{sprint_id}-tasks.yaml"
    tasks_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tasks_file, 'w') as f:
        yaml.dump({'tasks': tasks}, f, default_flow_style=False, sort_keys=False)

    print(f"✓ Created {len(tasks)} tasks: {tasks_file.relative_to(root_dir)}")

    # Update track to reference sprint
    track_file = vibey_dir / "tracks" / f"{args.track_id}.yaml"
    if track_file.exists():
        with open(track_file) as f:
            track_data = yaml.safe_load(f)

        if 'track' in track_data:
            # Add sprint to track's sprint list
            if 'sprints' not in track_data['track']:
                track_data['track']['sprints'] = []

            # Check if already in list
            sprint_entry = {
                'id': sprint_id,
                'name': plan_data['name'],
                'status': 'in_progress' if args.start else 'not_started',
                'estimated_duration': sprint['sprint']['estimated_duration'],
                'tasks_count': len(tasks),
                'started': sprint['sprint']['started']
            }

            # Update or append
            existing = [s for s in track_data['track']['sprints'] if s['id'] == sprint_id]
            if existing:
                existing[0].update(sprint_entry)
            else:
                track_data['track']['sprints'].append(sprint_entry)

            # Save updated track
            with open(track_file, 'w') as f:
                yaml.dump(track_data, f, default_flow_style=False, sort_keys=False)

            print(f"✓ Updated track: {track_file.relative_to(root_dir)}")

    print(f"\n✅ Sprint {sprint_id} created successfully!")
    print(f"   Name: {plan_data['name']}")
    print(f"   Tasks: {len(tasks)}")
    print(f"   Status: {'in_progress' if args.start else 'not_started'}")
    print(f"\nNext steps:")
    if not args.start:
        print(f"   Start sprint: roadmap start {sprint_id}")
    print(f"   View tasks: roadmap list tasks --sprint {sprint_id}")
    print(f"   Show details: roadmap show {sprint_id}")
