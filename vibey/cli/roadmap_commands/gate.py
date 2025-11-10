"""
Gate Command Handler

Manages quality gates in sprints.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import yaml

# Add roadmap-lib to path
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir / "roadmap-lib"))

from filesystem import find_roadmap_root


def handle_gate(args):
    """Handle gate command."""
    if args.gate_action == 'update':
        update_quality_gate(args)
    elif args.gate_action == 'list':
        list_quality_gates(args)
    else:
        print(f"❌ Unknown gate action: {args.gate_action}")
        sys.exit(1)


def update_quality_gate(args):
    """
    Update a quality gate status in a sprint.

    Args:
        args: Command-line arguments
            - sprint_id: Sprint containing the gate
            - gate: Gate name to update
            - status: New status (not_run, passed, failed)
            - score: Optional score value
    """
    # Find roadmap root
    root_dir = find_roadmap_root()
    if not root_dir:
        print("❌ No roadmap found. Run 'roadmap init' first.")
        sys.exit(1)

    vibey_dir = root_dir / ".vibey"
    sprint_file = vibey_dir / "sprints" / f"{args.sprint_id}.yaml"

    if not sprint_file.exists():
        print(f"❌ Sprint not found: {args.sprint_id}")
        sys.exit(1)

    # Load sprint
    with open(sprint_file) as f:
        sprint_data = yaml.safe_load(f)

    # Find and update gate
    gates = sprint_data.get('sprint', {}).get('quality_gates', [])
    gate_found = False

    for gate in gates:
        if gate.get('name') == args.gate:
            gate['status'] = args.status
            if args.score is not None:
                gate['score'] = args.score
            gate['updated'] = datetime.now(timezone.utc).isoformat()
            gate_found = True
            break

    if not gate_found:
        print(f"❌ Quality gate not found: {args.gate}")
        print(f"\nAvailable gates:")
        for gate in gates:
            print(f"  - {gate.get('name', 'Unknown')}")
        sys.exit(1)

    # Save updated sprint
    with open(sprint_file, 'w') as f:
        yaml.dump(sprint_data, f, default_flow_style=False, sort_keys=False)

    # Display result
    status_emoji = '✅' if args.status == 'passed' else '❌' if args.status == 'failed' else '⏸️'
    print(f"{status_emoji} Quality gate updated: {args.gate}")
    print(f"   Sprint: {args.sprint_id}")
    print(f"   Status: {args.status}")
    if args.score is not None:
        threshold = gate.get('threshold', 'N/A')
        print(f"   Score: {args.score} (threshold: {threshold})")


def list_quality_gates(args):
    """
    List all quality gates for a sprint.

    Args:
        args: Command-line arguments
            - sprint_id: Sprint to list gates for
    """
    # Find roadmap root
    root_dir = find_roadmap_root()
    if not root_dir:
        print("❌ No roadmap found. Run 'roadmap init' first.")
        sys.exit(1)

    vibey_dir = root_dir / ".vibey"
    sprint_file = vibey_dir / "sprints" / f"{args.sprint_id}.yaml"

    if not sprint_file.exists():
        print(f"❌ Sprint not found: {args.sprint_id}")
        sys.exit(1)

    # Load sprint
    with open(sprint_file) as f:
        sprint_data = yaml.safe_load(f)

    gates = sprint_data.get('sprint', {}).get('quality_gates', [])

    if not gates:
        print(f"ℹ️  No quality gates defined for sprint {args.sprint_id}")
        return

    print(f"🎯 Quality Gates for {args.sprint_id}:\n")

    for gate in gates:
        name = gate.get('name', 'Unknown')
        status = gate.get('status', 'not_run')
        threshold = gate.get('threshold', 'N/A')
        score = gate.get('score', 'N/A')
        blocking = gate.get('blocking', True)

        # Status emoji
        status_emoji = '✅' if status == 'passed' else '❌' if status == 'failed' else '⏸️'

        # Blocking indicator
        blocking_str = '🚫 BLOCKING' if blocking else '⚠️  non-blocking'

        print(f"{status_emoji} {name}")
        print(f"   Status: {status}")
        print(f"   Threshold: {threshold}")
        print(f"   Score: {score}")
        print(f"   {blocking_str}")
        print()
