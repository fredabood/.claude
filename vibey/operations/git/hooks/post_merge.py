"""
Post-merge and Post-checkout Hook Implementation

Rebuilds SQLite database from YAML files when roadmap files are updated.

Task: sqlite-backend-3-task-004
Status: In Progress
"""

import sys
from pathlib import Path
from typing import List


class PostMergeHook:
    """
    Post-merge hook for Vibey roadmap database sync.

    Rebuilds the SQLite database when YAML roadmap files have changed
    during a merge/pull operation.
    """

    # Terminal colors
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    RED = "\033[91m"
    RESET = "\033[0m"

    def __init__(self, repo_path: str = "."):
        """
        Initialize post-merge hook.

        Args:
            repo_path: Path to git repository root
        """
        self.repo_path = Path(repo_path).resolve()

    def _get_changed_files(self, ref: str = "HEAD@{1}") -> List[str]:
        """
        Get list of files changed in the merge.

        Args:
            ref: Git reference to compare against (default: previous HEAD)

        Returns:
            List of changed file paths
        """
        import subprocess

        result = subprocess.run(
            ["git", "-C", str(self.repo_path), "diff", "--name-only", ref, "HEAD"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return []

        return [f for f in result.stdout.strip().split("\n") if f]

    def _roadmap_files_changed(self, changed_files: List[str]) -> bool:
        """Check if any roadmap YAML files changed."""
        return any(
            f.startswith(".vibey/roadmap/") and f.endswith(".yaml")
            for f in changed_files
        )

    def _should_rebuild(self) -> bool:
        """
        Determine if database should be rebuilt.

        Returns:
            True if YAML files changed and database exists
        """
        try:
            from vibey.roadmap.database.connection import database_exists, get_db_path

            db_path = get_db_path(self.repo_path)

            # Only rebuild if database exists
            if not database_exists(db_path=db_path):
                return False

            # Check if roadmap YAML files changed
            changed_files = self._get_changed_files()
            return self._roadmap_files_changed(changed_files)

        except ImportError:
            return False

    def _rebuild_database(self) -> bool:
        """
        Rebuild database from YAML files.

        Returns:
            True if rebuild succeeded, False otherwise
        """
        try:
            from vibey.roadmap.database.connection import get_db_path
            from vibey.roadmap.serialization.backend import SyncManager

            db_path = get_db_path(self.repo_path)
            roadmap_dir = self.repo_path / ".vibey" / "roadmap"

            sync = SyncManager(roadmap_dir=roadmap_dir, db_path=db_path)

            # Force rebuild - incoming changes override local database
            sync.rebuild(force=True)

            return True

        except Exception as e:
            print(f"{self.RED}[vibey]{self.RESET} Failed to rebuild database: {e}")
            return False

    def run(self) -> int:
        """
        Run post-merge hook.

        Returns:
            Exit code: 0 for success, non-zero for failure
        """
        # Check if rebuild is needed
        if not self._should_rebuild():
            return 0

        print(f"{self.BLUE}[vibey]{self.RESET} Roadmap files updated, rebuilding database...")

        if self._rebuild_database():
            print(f"{self.GREEN}[vibey]{self.RESET} ✓ Database rebuilt from YAML")
            return 0
        else:
            print(f"{self.YELLOW}[vibey]{self.RESET} Database rebuild failed, run 'vibey roadmap db rebuild' manually")
            # Don't block on rebuild failure (fail open)
            return 0


class PostCheckoutHook(PostMergeHook):
    """
    Post-checkout hook for Vibey roadmap database sync.

    Inherits from PostMergeHook since the behavior is nearly identical.
    """

    def _get_changed_files(self, ref: str = "HEAD@{1}") -> List[str]:
        """
        Get list of files changed in the checkout.

        For checkouts, we compare the previous HEAD to current HEAD.
        """
        return super()._get_changed_files(ref)


def main(hook_type: str = "post-merge") -> int:
    """Main entry point for post-merge/checkout hooks."""
    try:
        if hook_type == "post-checkout":
            hook = PostCheckoutHook()
        else:
            hook = PostMergeHook()
        return hook.run()
    except Exception as e:
        print(f"Error running {hook_type} hook: {e}", file=sys.stderr)
        # Don't block on hook errors (fail open)
        return 0


if __name__ == "__main__":
    sys.exit(main())
