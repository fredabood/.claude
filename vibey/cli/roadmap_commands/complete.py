"""
'roadmap complete' command - Mark a sprint or task as complete.
"""

import sys
import subprocess
from pathlib import Path


def is_ulid(id_str: str) -> bool:
    """Check if string is a ULID (26 alphanumeric chars starting with 01)."""
    return len(id_str) == 26 and id_str.isalnum() and id_str.startswith('01')


def get_item_type_from_ulid(root_dir: Path, ulid: str) -> str:
    """Determine if ULID is a task, sprint, or track by checking filesystem."""
    roadmap_root = root_dir / ".vibey" / "roadmap"

    # Check tasks directory
    if (roadmap_root / "tasks" / f"{ulid}.yaml").exists():
        return "task"
    # Check sprints directory
    if (roadmap_root / "sprints" / f"{ulid}.yaml").exists():
        return "sprint"
    # Check tracks directory
    if (roadmap_root / "tracks" / f"{ulid}.yaml").exists():
        return "track"

    raise ValueError(f"Cannot find item with ID: {ulid}")


def handle_complete(args):
    """Handle 'roadmap complete' command by calling roadmap-update.py."""
    script_path = Path(__file__).parent.parent / "roadmap-update.py"
    root_dir = Path(args.dir) if args.dir else Path.cwd()

    # Determine item type
    if is_ulid(args.id):
        try:
            item_type = get_item_type_from_ulid(root_dir, args.id)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
    elif '-task-' in args.id:
        item_type = "task"
    else:
        item_type = "sprint"

    # Build command based on item type
    if item_type == "task":
        cmd = ["python3", str(script_path), "--complete-task", args.id]
    elif item_type == "sprint":
        cmd = ["python3", str(script_path), "--complete-sprint", args.id]
    elif item_type == "track":
        cmd = ["python3", str(script_path), "--complete-track", args.id]
    else:
        print(f"Error: Unknown item type: {item_type}")
        sys.exit(1)

    if args.dir:
        cmd.extend(["--dir", str(args.dir)])

    # Run script
    result = subprocess.run(cmd)
    sys.exit(result.returncode)
