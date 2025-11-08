"""
'roadmap progress' command - Update progress calculations.
"""

import sys
import subprocess
from pathlib import Path

def handle_progress(args):
    """Handle 'roadmap progress' command by calling roadmap-update.py."""
    script_path = Path(__file__).parent.parent / "roadmap-update.py"

    cmd = ["python3", str(script_path), "--refresh-progress"]

    if args.dir:
        cmd.extend(["--dir", str(args.dir)])

    # Run script
    result = subprocess.run(cmd)
    sys.exit(result.returncode)
