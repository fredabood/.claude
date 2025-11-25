"""
Post-Commit Hook Implementation

Clears the CLI change tracker after successful commits.

Task: git-integration-4-task-005
"""

import sys
from pathlib import Path


def main() -> int:
    """Clear CLI changes tracker after successful commit."""
    try:
        from vibey.operations.git.cli_change_tracker import clear_cli_changes

        # Get repo root
        repo_path = Path.cwd()

        # Check if we're in a Vibey project
        if not (repo_path / ".vibey").exists():
            return 0

        # Clear the tracker
        clear_cli_changes(repo_path)
        return 0

    except Exception as e:
        # Don't fail on errors in post-commit
        print(f"Warning: Could not clear CLI changes tracker: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
