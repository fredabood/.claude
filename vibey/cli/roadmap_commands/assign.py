"""
'roadmap assign' command - Assign a task to an agent.
"""

import sys
import subprocess
from pathlib import Path

def handle_assign(args):
    """Handle 'roadmap assign' command by calling roadmap-update.py."""
    script_path = Path(__file__).parent.parent / "roadmap-update.py"

    cmd = [
        "python3", str(script_path),
        "--assign-task", args.task_id,
        "--agent", args.agent
    ]

    if args.dir:
        cmd.extend(["--dir", str(args.dir)])

    # Run script
    result = subprocess.run(cmd)
    sys.exit(result.returncode)
