"""
Roadmap Prepare Command Handler

Handles the 'roadmap prepare' command for task preparation mode.
"""

import sys
from pathlib import Path

# Import the preparation mode implementation
sys.path.insert(0, str(Path(__file__).parent.parent))

from roadmap_lib.filesystem import find_roadmap_root

# Import PreparationMode (will import the script)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "roadmap_prepare",
    Path(__file__).parent.parent / "roadmap-prepare.py"
)
roadmap_prepare_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(roadmap_prepare_module)

PreparationMode = roadmap_prepare_module.PreparationMode


def handle_prepare(args):
    """Handle the prepare command."""

    # Find roadmap root
    if args.dir:
        root_dir = Path(args.dir)
    else:
        root_dir = find_roadmap_root()

    if not root_dir:
        print("❌ No roadmap found. Run 'roadmap init' first.")
        sys.exit(1)

    prep_mode = PreparationMode(root_dir)

    # List mode
    if args.list:
        print("📋 Tasks with preparation documents:")
        # TODO: Implement list functionality
        print("   (Not yet implemented)")
        return

    # Require task_id for other operations
    if not args.task_id:
        print("❌ Task ID required")
        print("   Usage: roadmap prepare <task-id>")
        print("   Or:    roadmap prepare --list")
        sys.exit(1)

    # Generate or show preparation document
    prep_mode.prepare_task(
        args.task_id,
        regenerate=args.regenerate,
        show=args.show
    )
