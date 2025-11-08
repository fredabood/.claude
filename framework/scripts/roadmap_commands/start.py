"""
'roadmap start' command - Start a sprint or task.
"""

import sys
import subprocess
from pathlib import Path

def handle_start(args):
    """Handle 'roadmap start' command by calling roadmap-update.py."""
    script_path = Path(__file__).parent.parent / "roadmap-update.py"

    # Determine if it's a sprint or task
    if '-task-' in args.id:
        cmd = ["python3", str(script_path), "--start-task", args.id]
    else:
        cmd = ["python3", str(script_path), "--start-sprint", args.id]

    if args.dir:
        cmd.extend(["--dir", str(args.dir)])

    # Run script
    result = subprocess.run(cmd)
    sys.exit(result.returncode)
