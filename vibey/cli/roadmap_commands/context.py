"""
Roadmap Context Command Handler

Handles the 'roadmap context' command for loading and analyzing task context.
"""

import sys
from pathlib import Path

# Import the context loader implementation
sys.path.insert(0, str(Path(__file__).parent.parent))

from roadmap_lib.filesystem import find_roadmap_root

# Import ContextLoader
import importlib.util
spec = importlib.util.spec_from_file_location(
    "roadmap_context",
    Path(__file__).parent.parent / "roadmap-context.py"
)
roadmap_context_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(roadmap_context_module)

ContextLoader = roadmap_context_module.ContextLoader


def handle_context(args):
    """Handle the context command."""

    # Find roadmap root
    if args.dir:
        root_dir = Path(args.dir)
    else:
        root_dir = find_roadmap_root()

    if not root_dir:
        print("❌ No roadmap found. Run 'roadmap init' first.")
        sys.exit(1)

    # Pass cache to context loader (if available from args)
    cache = getattr(args, 'cache', None)
    loader = ContextLoader(root_dir, max_distance=args.max_distance, cache=cache)
    context = loader.load_context_for_task(args.task_id, show_full=args.show_full)
