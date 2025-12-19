"""
'roadmap start' command - Start a sprint or task.
"""

import sys
import subprocess
from pathlib import Path

from vibey.roadmap.id_generator import is_raw_ulid as is_ulid
from vibey.cli.roadmap_lib.filesystem import FileSystemManager
from vibey.cli.error_handler import (
    cli_error,
    item_not_found_error,
    invalid_item_type_error,
    format_cli_error,
    ExitCode,
)


def handle_start(args):
    """Handle 'roadmap start' command by calling roadmap-update.py."""
    script_path = Path(__file__).parent.parent / "roadmap-update.py"
    root_dir = Path(args.dir) if args.dir else Path.cwd()

    # Determine item type
    if is_ulid(args.id):
        fs = FileSystemManager(root_dir)
        item_type = fs.detect_entity_type(args.id)
        if not item_type:
            error = item_not_found_error(args.id)
            print(format_cli_error(error), file=sys.stderr)
            sys.exit(ExitCode.NOT_FOUND_ERROR)
    elif '-task-' in args.id:
        item_type = "task"
    else:
        item_type = "sprint"

    # Build command based on item type
    if item_type == "task":
        cmd = ["python3", str(script_path), "--start-task", args.id]
    elif item_type == "sprint":
        cmd = ["python3", str(script_path), "--start-sprint", args.id]
    else:
        error = invalid_item_type_error(args.id, item_type, "start")
        print(format_cli_error(error), file=sys.stderr)
        sys.exit(ExitCode.VALIDATION_ERROR)

    if args.dir:
        cmd.extend(["--dir", str(args.dir)])

    # Run script
    result = subprocess.run(cmd)
    sys.exit(result.returncode)
