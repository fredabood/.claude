"""
'roadmap check-standards' command - Check which standards apply to an item.
"""

import sys
from pathlib import Path

from ...operations.roadmap import (
    enforce_standards,
    print_enforcement_results,
)


def handle_check_standards(args):
    """
    Handle 'roadmap check-standards' command.

    Validates all standards that apply to a roadmap item (task/sprint/track)
    and displays the results without taking any action.

    Args:
        args: Parsed command-line arguments with:
            - id: Item ID to check (task/sprint/track)
            - dir: Optional root directory (defaults to current directory)
            - verbose: Show all standards including passed ones

    Returns:
        Exit code: 0 for success, 1 for error
    """
    root_dir = Path(args.dir) if args.dir else Path.cwd()
    item_id = args.id
    verbose = getattr(args, 'verbose', False)

    # Determine item type for display
    if '-task-' in item_id:
        item_type = "Task"
    elif item_id.count('-') >= 1:
        item_type = "Sprint"
    else:
        item_type = "Track"

    print(f"\n🔍 Checking standards for {item_type}: {item_id}")
    print("=" * 80)

    # Run enforcement (but don't actually enforce, just check)
    try:
        enforcement_result = enforce_standards(item_id, root_dir, operation="check")
    except Exception as e:
        print(f"\n❌ Failed to check standards: {e}")
        return 1

    # Print results
    print_enforcement_results(enforcement_result, item_id, verbose=verbose)

    # Show summary
    if enforcement_result.can_proceed:
        if enforcement_result.warnings:
            print(f"✅ Item can proceed with {len(enforcement_result.warnings)} warning(s)")
        else:
            print(f"✅ All standards passed - item can be completed")
    else:
        print(f"❌ Item cannot proceed - {len(enforcement_result.blocking_failures)} blocking failure(s)")
        print(f"   Use 'vibey roadmap override-standard' to override specific standards")

    # Return non-zero exit code if there are blocking failures
    return 0 if enforcement_result.can_proceed else 1
