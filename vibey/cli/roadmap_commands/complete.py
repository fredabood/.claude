"""
'roadmap complete' command - Mark a sprint or task as complete.
"""

import sys
import subprocess
from pathlib import Path

from vibey.roadmap.id_generator import is_raw_ulid as is_ulid
from vibey.cli.roadmap_lib.filesystem import FileSystemManager


def handle_complete(args):
    """Handle 'roadmap complete' command by calling roadmap-update.py."""
    script_path = Path(__file__).parent.parent / "roadmap-update.py"
    root_dir = Path(args.dir) if args.dir else Path.cwd()

    # Determine item type
    if is_ulid(args.id):
        fs = FileSystemManager(root_dir)
        item_type = fs.detect_entity_type(args.id)
        if not item_type:
            print(f"Error: Cannot find item with ID: {args.id}")
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
