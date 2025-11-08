"""
Roadmap Summarize Command Handler

Handles the 'roadmap summarize' command for generating dependency and task summaries.
"""

import sys
from pathlib import Path

# Import the summarize implementation
sys.path.insert(0, str(Path(__file__).parent.parent))

from roadmap_lib.filesystem import find_roadmap_root

# Import SummaryGenerator
import importlib.util
spec = importlib.util.spec_from_file_location(
    "roadmap_summarize",
    Path(__file__).parent.parent / "roadmap-summarize.py"
)
roadmap_summarize_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(roadmap_summarize_module)

SummaryGenerator = roadmap_summarize_module.SummaryGenerator


def handle_summarize(args):
    """Handle the summarize command."""

    # Find roadmap root
    if args.dir:
        root_dir = Path(args.dir)
    else:
        root_dir = find_roadmap_root()

    if not root_dir:
        print("❌ No roadmap found. Run 'roadmap init' first.")
        sys.exit(1)

    generator = SummaryGenerator(root_dir)

    # All sprints mode
    if args.all:
        if args.completed:
            generator.summarize_all_completed()
        else:
            print("❌ --all requires --completed flag")
            sys.exit(1)
        return

    # Require sprint_id for other operations
    if not args.sprint_id:
        print("❌ Sprint ID required")
        print("   Usage: roadmap summarize <sprint-id>")
        print("   Or:    roadmap summarize --all --completed")
        sys.exit(1)

    # Task-specific summary
    if args.task:
        generator.summarize_task(args.sprint_id, args.task, force=args.force)
    else:
        # Sprint dependency summary
        generator.summarize_sprint(args.sprint_id, force=args.force)
