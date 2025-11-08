"""
'roadmap init' command - Initialize a new roadmap.
"""

import sys
import subprocess
from pathlib import Path

def handle_init(args):
    """Handle 'roadmap init' command by calling roadmap-init.py."""
    script_path = Path(__file__).parent.parent / "roadmap-init.py"

    # Build command
    cmd = ["python3", str(script_path)]

    if args.dir:
        cmd.extend(["--dir", str(args.dir)])

    if args.id:
        cmd.extend(["--id", args.id])

    if args.name:
        cmd.extend(["--name", args.name])

    if args.version:
        cmd.extend(["--version", args.version])

    if args.bump_on:
        cmd.extend(["--bump-on", args.bump_on])

    if args.bump_type:
        cmd.extend(["--bump-type", args.bump_type])

    if args.force:
        cmd.append("--force")

    # Run script
    result = subprocess.run(cmd)
    sys.exit(result.returncode)
