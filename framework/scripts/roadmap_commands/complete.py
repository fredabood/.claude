"""
'roadmap complete' command - Mark a sprint or task as complete.
"""

import sys
import subprocess
from pathlib import Path

def handle_complete(args):
    """Handle 'roadmap complete' command by calling roadmap-update.py."""
    script_path = Path(__file__).parent.parent / "roadmap-update.py"

    # Determine if it's a sprint or task
    if '-task-' in args.id:
        cmd = ["python3", str(script_path), "--complete-task", args.id]
    else:
        cmd = ["python3", str(script_path), "--complete-sprint", args.id]

    if args.dir:
        cmd.extend(["--dir", str(args.dir)])

    # Run script
    result = subprocess.run(cmd)
    sys.exit(result.returncode)
