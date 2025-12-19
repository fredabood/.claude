"""
'roadmap complete' command - Mark a sprint or task as complete.
"""

import sys
import subprocess
from pathlib import Path

from vibey.roadmap.id_generator import is_raw_ulid as is_ulid
from vibey.cli.roadmap_lib.filesystem import FileSystemManager
from vibey.cli.error_handler import (
    item_not_found_error,
    format_cli_error,
    ExitCode,
)
from vibey.common.errors import VibeyError, ErrorCategory, ErrorSeverity


def handle_complete(args):
    """Handle 'roadmap complete' command by calling roadmap-update.py."""
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
        cmd = ["python3", str(script_path), "--complete-task", args.id]
    elif item_type == "sprint":
        cmd = ["python3", str(script_path), "--complete-sprint", args.id]
    elif item_type == "track":
        cmd = ["python3", str(script_path), "--complete-track", args.id]
    else:
        error = VibeyError(
            message=f"Unknown item type: {item_type}",
            code="UNKNOWN_ITEM_TYPE",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            suggestions=[
                f"Verify the ID '{args.id}' is correct",
                "List available items: vibey roadmap list tracks",
                "Check item details: vibey roadmap show <id>",
            ],
            hint="Item types should be 'task', 'sprint', or 'track'",
            metadata={"item_id": args.id, "item_type": item_type},
        )
        print(format_cli_error(error), file=sys.stderr)
        sys.exit(ExitCode.VALIDATION_ERROR)

    if args.dir:
        cmd.extend(["--dir", str(args.dir)])

    # Run script
    result = subprocess.run(cmd)
    sys.exit(result.returncode)
