"""
Git branch management for ticket implementation.

This module provides git branch lifecycle management tied to tickets,
enabling isolated development on feature branches with structured
merge strategies.

Key Features:
- Create feature branches for tickets with consistent naming
- Track branch status (ahead/behind, conflicts)
- Merge back to main with squash, merge, or rebase strategies
- Cleanup feature branches after successful merge

Branch naming convention: {prefix}/{ticket_id}
Example: implement/01KC2D0JK9JKQXGQW6MQEB0JZP

Usage:
    from vibey.services.implementation.git import TicketBranchManager
    from pathlib import Path

    # Initialize with repository root and config
    manager = TicketBranchManager(repo_root=Path("."), config=config)

    # Create and checkout branch for ticket
    branch_name = manager.create_ticket_branch(ticket)
    manager.checkout_ticket_branch(ticket)

    # ... implement task ...

    # Merge back to main with squash
    result = manager.merge_to_main(ticket, strategy=MergeStrategy.SQUASH)
    if result.success:
        manager.cleanup_branch(ticket)

Design Reference:
- Unified Ticket Architecture (UTA) v2.0
- Implementation Mode Track Sprint 2
"""

import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
    from vibey.services.implementation.config import ImplementConfig

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_BRANCH_PREFIX = "implement"
"""Default prefix for ticket feature branches."""


# =============================================================================
# ENUMS
# =============================================================================


class MergeStrategy(Enum):
    """Strategy for merging feature branches back to main."""

    SQUASH = "squash"
    """Squash all commits into a single commit on main."""

    MERGE = "merge"
    """Create a merge commit preserving full history."""

    REBASE = "rebase"
    """Rebase commits onto main for linear history."""


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class BranchStatus:
    """
    Status of a ticket branch.

    Attributes:
        exists: Whether the branch exists
        is_current: Whether this branch is currently checked out
        commits_ahead: Number of commits ahead of main
        commits_behind: Number of commits behind main
        has_conflicts: Whether merging would cause conflicts
        last_commit: Timestamp of the last commit on this branch
        last_commit_message: Message of the last commit
    """

    exists: bool
    is_current: bool
    commits_ahead: int = 0
    commits_behind: int = 0
    has_conflicts: bool = False
    last_commit: Optional[datetime] = None
    last_commit_message: Optional[str] = None


@dataclass
class MergeResult:
    """
    Result of a branch merge operation.

    Attributes:
        success: Whether the merge succeeded
        commit_hash: SHA of the merge commit (if successful)
        conflicts: List of conflicting file paths (if any)
        error_message: Error description (if failed)
    """

    success: bool
    commit_hash: Optional[str] = None
    conflicts: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


# =============================================================================
# EXCEPTIONS
# =============================================================================


class BranchError(Exception):
    """Base exception for branch operations."""

    pass


class NotAGitRepositoryError(BranchError):
    """Raised when trying to operate on a non-git directory."""

    pass


class BranchNotFoundError(BranchError):
    """Raised when a branch doesn't exist."""

    pass


class BranchConflictError(BranchError):
    """Raised when merge conflicts occur."""

    def __init__(self, conflicts: List[str], message: str = "Merge conflicts detected"):
        self.conflicts = conflicts
        super().__init__(f"{message}: {', '.join(conflicts)}")


# =============================================================================
# TICKET BRANCH MANAGER
# =============================================================================


class TicketBranchManager:
    """
    Manages git branches tied to tickets.

    Creates isolated feature branches for ticket implementation with
    structured merge strategies and cleanup support.

    Attributes:
        repo_root: Path to the git repository root
        config: Implementation configuration
        branch_prefix: Prefix for branch names (default: "implement")

    Example:
        >>> manager = TicketBranchManager(Path("."), config)
        >>> branch = manager.create_ticket_branch(ticket)
        >>> manager.checkout_ticket_branch(ticket)
        >>> # ... work on ticket ...
        >>> result = manager.merge_to_main(ticket, MergeStrategy.SQUASH)
        >>> if result.success:
        ...     manager.cleanup_branch(ticket)
    """

    def __init__(self, repo_root: Path, config: "ImplementConfig"):
        """
        Initialize the branch manager.

        Args:
            repo_root: Path to the git repository root
            config: Implementation configuration

        Raises:
            NotAGitRepositoryError: If repo_root is not a git repository
        """
        self.repo_root = Path(repo_root).resolve()
        self.config = config
        self.branch_prefix = getattr(config, "branch_prefix", DEFAULT_BRANCH_PREFIX)

        # Verify this is a git repository
        if not self._is_git_repo():
            raise NotAGitRepositoryError(f"Not a git repository: {self.repo_root}")

    # =========================================================================
    # BRANCH CREATION
    # =========================================================================

    def create_ticket_branch(self, ticket: "HierarchicalTicket") -> str:
        """
        Create feature branch for ticket.

        Creates a new branch from the main branch with a name based on
        the ticket ID. If the branch already exists, returns the existing
        branch name.

        Args:
            ticket: The HierarchicalTicket to create a branch for

        Returns:
            Branch name (e.g., "implement/01KC...")

        Raises:
            BranchError: If branch creation fails
        """
        branch_name = self.get_ticket_branch_name(ticket)

        # Check if branch already exists
        if self.branch_exists(ticket):
            logger.info(f"Branch {branch_name} already exists")
            return branch_name

        logger.info(f"Creating branch {branch_name} for ticket {ticket.id}")

        try:
            # Get the main branch name
            main_branch = self._get_main_branch()

            # Fetch latest from remote (if available)
            self._fetch_remote()

            # Create branch from main
            self._run_git(
                ["branch", branch_name, main_branch],
                f"Failed to create branch {branch_name}",
            )

            logger.info(f"Created branch {branch_name} from {main_branch}")
            return branch_name

        except subprocess.CalledProcessError as e:
            raise BranchError(f"Failed to create branch: {e}") from e

    def checkout_ticket_branch(self, ticket: "HierarchicalTicket") -> bool:
        """
        Switch to ticket's feature branch.

        Creates the branch if it doesn't exist, then checks it out.

        Args:
            ticket: The HierarchicalTicket whose branch to checkout

        Returns:
            True if checkout succeeded

        Raises:
            BranchError: If checkout fails
        """
        branch_name = self.get_ticket_branch_name(ticket)

        # Create branch if it doesn't exist
        if not self.branch_exists(ticket):
            self.create_ticket_branch(ticket)

        logger.info(f"Checking out branch {branch_name}")

        try:
            # Stash any uncommitted changes first
            self._stash_changes()

            # Checkout the branch
            self._run_git(
                ["checkout", branch_name],
                f"Failed to checkout branch {branch_name}",
            )

            # Pop stashed changes if any
            self._pop_stash()

            logger.info(f"Checked out branch {branch_name}")
            return True

        except subprocess.CalledProcessError as e:
            raise BranchError(f"Failed to checkout branch: {e}") from e

    # =========================================================================
    # BRANCH MERGING
    # =========================================================================

    def merge_to_main(
        self,
        ticket: "HierarchicalTicket",
        strategy: MergeStrategy = MergeStrategy.SQUASH,
    ) -> MergeResult:
        """
        Merge feature branch back to main.

        Supports three merge strategies:
        - SQUASH: Combine all commits into a single commit
        - MERGE: Create a merge commit preserving history
        - REBASE: Rebase onto main for linear history

        Args:
            ticket: The HierarchicalTicket whose branch to merge
            strategy: The merge strategy to use

        Returns:
            MergeResult with success status and details

        Raises:
            BranchNotFoundError: If the ticket branch doesn't exist
        """
        branch_name = self.get_ticket_branch_name(ticket)

        if not self.branch_exists(ticket):
            raise BranchNotFoundError(f"Branch not found: {branch_name}")

        main_branch = self._get_main_branch()
        logger.info(f"Merging {branch_name} to {main_branch} with strategy {strategy.value}")

        try:
            # First, check for conflicts
            conflicts = self._check_merge_conflicts(branch_name, main_branch)
            if conflicts:
                return MergeResult(
                    success=False,
                    conflicts=conflicts,
                    error_message="Merge would cause conflicts",
                )

            # Checkout main branch
            self._run_git(
                ["checkout", main_branch],
                f"Failed to checkout {main_branch}",
            )

            # Perform merge based on strategy
            if strategy == MergeStrategy.SQUASH:
                result = self._merge_squash(branch_name, ticket)
            elif strategy == MergeStrategy.MERGE:
                result = self._merge_regular(branch_name, ticket)
            elif strategy == MergeStrategy.REBASE:
                result = self._merge_rebase(branch_name, ticket)
            else:
                raise ValueError(f"Unknown merge strategy: {strategy}")

            return result

        except subprocess.CalledProcessError as e:
            # Abort any in-progress merge
            self._abort_merge()
            return MergeResult(
                success=False,
                error_message=str(e),
            )

    def _merge_squash(
        self, branch_name: str, ticket: "HierarchicalTicket"
    ) -> MergeResult:
        """Perform squash merge."""
        try:
            # Squash merge (stages changes but doesn't commit)
            self._run_git(
                ["merge", "--squash", branch_name],
                f"Failed to squash merge {branch_name}",
            )

            # Create the squash commit
            commit_message = self._build_merge_commit_message(ticket, "squash")
            self._run_git(
                ["commit", "-m", commit_message],
                "Failed to create squash commit",
            )

            commit_hash = self._get_head_sha()
            logger.info(f"Squash merged {branch_name}: {commit_hash[:8]}")

            return MergeResult(success=True, commit_hash=commit_hash)

        except subprocess.CalledProcessError as e:
            return MergeResult(success=False, error_message=str(e))

    def _merge_regular(
        self, branch_name: str, ticket: "HierarchicalTicket"
    ) -> MergeResult:
        """Perform regular merge with merge commit."""
        try:
            commit_message = self._build_merge_commit_message(ticket, "merge")
            self._run_git(
                ["merge", "--no-ff", "-m", commit_message, branch_name],
                f"Failed to merge {branch_name}",
            )

            commit_hash = self._get_head_sha()
            logger.info(f"Merged {branch_name}: {commit_hash[:8]}")

            return MergeResult(success=True, commit_hash=commit_hash)

        except subprocess.CalledProcessError as e:
            return MergeResult(success=False, error_message=str(e))

    def _merge_rebase(
        self, branch_name: str, ticket: "HierarchicalTicket"
    ) -> MergeResult:
        """Perform rebase and fast-forward merge."""
        main_branch = self._get_main_branch()

        try:
            # Checkout the feature branch
            self._run_git(
                ["checkout", branch_name],
                f"Failed to checkout {branch_name}",
            )

            # Rebase onto main
            self._run_git(
                ["rebase", main_branch],
                f"Failed to rebase {branch_name} onto {main_branch}",
            )

            # Checkout main and fast-forward
            self._run_git(
                ["checkout", main_branch],
                f"Failed to checkout {main_branch}",
            )
            self._run_git(
                ["merge", "--ff-only", branch_name],
                f"Failed to fast-forward merge {branch_name}",
            )

            commit_hash = self._get_head_sha()
            logger.info(f"Rebased and merged {branch_name}: {commit_hash[:8]}")

            return MergeResult(success=True, commit_hash=commit_hash)

        except subprocess.CalledProcessError as e:
            # Abort any in-progress rebase
            self._abort_rebase()
            return MergeResult(success=False, error_message=str(e))

    # =========================================================================
    # BRANCH CLEANUP
    # =========================================================================

    def cleanup_branch(self, ticket: "HierarchicalTicket") -> None:
        """
        Delete feature branch after successful merge.

        Should only be called after the branch has been successfully merged.

        Args:
            ticket: The HierarchicalTicket whose branch to delete

        Raises:
            BranchError: If deletion fails
        """
        branch_name = self.get_ticket_branch_name(ticket)

        if not self.branch_exists(ticket):
            logger.debug(f"Branch {branch_name} doesn't exist, nothing to clean up")
            return

        # Don't delete if currently checked out
        current_branch = self._get_current_branch()
        if current_branch == branch_name:
            main_branch = self._get_main_branch()
            self._run_git(
                ["checkout", main_branch],
                f"Failed to checkout {main_branch}",
            )

        logger.info(f"Deleting branch {branch_name}")

        try:
            # Delete local branch
            self._run_git(
                ["branch", "-D", branch_name],
                f"Failed to delete branch {branch_name}",
            )
            logger.info(f"Deleted branch {branch_name}")

        except subprocess.CalledProcessError as e:
            raise BranchError(f"Failed to delete branch: {e}") from e

    # =========================================================================
    # BRANCH STATUS
    # =========================================================================

    def get_ticket_branch_name(self, ticket: "HierarchicalTicket") -> str:
        """
        Generate branch name for ticket.

        Args:
            ticket: The HierarchicalTicket

        Returns:
            Branch name (e.g., "implement/01KC...")
        """
        return f"{self.branch_prefix}/{ticket.id}"

    def branch_exists(self, ticket: "HierarchicalTicket") -> bool:
        """
        Check if ticket branch already exists.

        Args:
            ticket: The HierarchicalTicket to check

        Returns:
            True if the branch exists
        """
        branch_name = self.get_ticket_branch_name(ticket)
        return self._branch_exists(branch_name)

    def get_branch_status(self, ticket: "HierarchicalTicket") -> BranchStatus:
        """
        Get status of ticket branch.

        Returns detailed status including commits ahead/behind main
        and potential merge conflicts.

        Args:
            ticket: The HierarchicalTicket to check

        Returns:
            BranchStatus with full status information
        """
        branch_name = self.get_ticket_branch_name(ticket)

        # Check if branch exists
        if not self._branch_exists(branch_name):
            return BranchStatus(exists=False, is_current=False)

        # Check if currently checked out
        current_branch = self._get_current_branch()
        is_current = current_branch == branch_name

        # Get commits ahead/behind
        commits_ahead, commits_behind = self._get_branch_distance(branch_name)

        # Check for potential conflicts
        main_branch = self._get_main_branch()
        conflicts = self._check_merge_conflicts(branch_name, main_branch)
        has_conflicts = len(conflicts) > 0

        # Get last commit info
        last_commit, last_commit_message = self._get_last_commit_info(branch_name)

        return BranchStatus(
            exists=True,
            is_current=is_current,
            commits_ahead=commits_ahead,
            commits_behind=commits_behind,
            has_conflicts=has_conflicts,
            last_commit=last_commit,
            last_commit_message=last_commit_message,
        )

    # =========================================================================
    # HELPER METHODS - GIT OPERATIONS
    # =========================================================================

    def _run_git(
        self,
        args: List[str],
        error_message: str,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """
        Run a git command.

        Args:
            args: Git command arguments (without 'git')
            error_message: Message for errors
            capture_output: Whether to capture stdout/stderr

        Returns:
            CompletedProcess result

        Raises:
            subprocess.CalledProcessError: If command fails
        """
        cmd = ["git"] + args

        result = subprocess.run(
            cmd,
            cwd=self.repo_root,
            capture_output=capture_output,
            text=True,
            check=True,
        )

        return result

    def _is_git_repo(self) -> bool:
        """Check if repo_root is a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_main_branch(self) -> str:
        """
        Get the main branch name (main or master).

        Returns:
            Name of the main branch
        """
        # Try 'main' first
        try:
            result = self._run_git(
                ["rev-parse", "--verify", "main"],
                "Checking for main branch",
            )
            return "main"
        except subprocess.CalledProcessError:
            pass

        # Fall back to 'master'
        try:
            result = self._run_git(
                ["rev-parse", "--verify", "master"],
                "Checking for master branch",
            )
            return "master"
        except subprocess.CalledProcessError:
            pass

        # Default to 'main' if neither exists
        return "main"

    def _get_current_branch(self) -> str:
        """Get the name of the currently checked out branch."""
        result = self._run_git(
            ["rev-parse", "--abbrev-ref", "HEAD"],
            "Failed to get current branch",
        )
        return result.stdout.strip()

    def _get_head_sha(self) -> str:
        """Get the SHA of HEAD commit."""
        result = self._run_git(
            ["rev-parse", "HEAD"],
            "Failed to get HEAD SHA",
        )
        return result.stdout.strip()

    def _branch_exists(self, branch_name: str) -> bool:
        """Check if a branch exists."""
        try:
            self._run_git(
                ["rev-parse", "--verify", branch_name],
                f"Checking for branch {branch_name}",
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def _fetch_remote(self) -> None:
        """Fetch latest from remote origin (if available)."""
        try:
            self._run_git(["fetch", "origin"], "Fetching from origin")
        except subprocess.CalledProcessError:
            # Remote may not exist, that's OK
            pass

    def _stash_changes(self) -> None:
        """Stash any uncommitted changes."""
        try:
            # Check if there are changes to stash
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():
                self._run_git(["stash", "push", "-m", "auto-stash"], "Stashing changes")
                logger.debug("Stashed uncommitted changes")
        except subprocess.CalledProcessError:
            pass

    def _pop_stash(self) -> None:
        """Pop stashed changes if any exist."""
        try:
            # Check if there are stashes
            result = self._run_git(["stash", "list"], "Listing stashes")
            if "auto-stash" in result.stdout:
                self._run_git(["stash", "pop"], "Popping stash")
                logger.debug("Popped stashed changes")
        except subprocess.CalledProcessError:
            pass

    def _get_branch_distance(self, branch_name: str) -> tuple:
        """
        Get commits ahead/behind main.

        Returns:
            Tuple of (ahead, behind)
        """
        main_branch = self._get_main_branch()

        try:
            result = self._run_git(
                ["rev-list", "--left-right", "--count", f"{main_branch}...{branch_name}"],
                f"Getting distance for {branch_name}",
            )
            parts = result.stdout.strip().split()
            behind = int(parts[0]) if len(parts) > 0 else 0
            ahead = int(parts[1]) if len(parts) > 1 else 0
            return (ahead, behind)
        except (subprocess.CalledProcessError, ValueError, IndexError):
            return (0, 0)

    def _check_merge_conflicts(self, source_branch: str, target_branch: str) -> List[str]:
        """
        Check if merging would cause conflicts.

        Uses git merge-tree to detect conflicts without actually merging.

        Returns:
            List of conflicting file paths
        """
        conflicts: List[str] = []

        try:
            # Get merge base
            base_result = self._run_git(
                ["merge-base", target_branch, source_branch],
                "Getting merge base",
            )
            merge_base = base_result.stdout.strip()

            # Use merge-tree to check for conflicts
            result = subprocess.run(
                ["git", "merge-tree", merge_base, target_branch, source_branch],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )

            # Parse output for conflict markers
            if result.stdout:
                lines = result.stdout.split("\n")
                for i, line in enumerate(lines):
                    # Look for merge conflict markers in output
                    if line.startswith("changed in both"):
                        # Next line should have the filename
                        if i + 1 < len(lines):
                            parts = lines[i + 1].strip().split()
                            if parts:
                                conflicts.append(parts[-1])

        except subprocess.CalledProcessError:
            pass

        return list(set(conflicts))

    def _get_last_commit_info(self, branch_name: str) -> tuple:
        """
        Get last commit timestamp and message for a branch.

        Returns:
            Tuple of (datetime, message)
        """
        try:
            result = self._run_git(
                ["log", "-1", "--format=%aI|%s", branch_name],
                f"Getting last commit for {branch_name}",
            )
            parts = result.stdout.strip().split("|", 1)
            timestamp_str = parts[0]
            message = parts[1] if len(parts) > 1 else ""

            # Parse ISO format timestamp
            created_at = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return (created_at, message)
        except (subprocess.CalledProcessError, ValueError):
            return (None, None)

    def _build_merge_commit_message(
        self, ticket: "HierarchicalTicket", strategy: str
    ) -> str:
        """Build commit message for merge."""
        ticket_name = getattr(ticket, "name", "Unknown task")
        ticket_id = ticket.id

        return (
            f"feat: Complete ticket {ticket_id}\n\n"
            f"Task: {ticket_name}\n"
            f"Merge strategy: {strategy}\n"
            f"Ticket ID: {ticket_id}"
        )

    def _abort_merge(self) -> None:
        """Abort any in-progress merge."""
        try:
            self._run_git(["merge", "--abort"], "Aborting merge")
        except subprocess.CalledProcessError:
            pass

    def _abort_rebase(self) -> None:
        """Abort any in-progress rebase."""
        try:
            self._run_git(["rebase", "--abort"], "Aborting rebase")
        except subprocess.CalledProcessError:
            pass


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Main class
    "TicketBranchManager",
    # Data models
    "BranchStatus",
    "MergeResult",
    # Enums
    "MergeStrategy",
    # Exceptions
    "BranchError",
    "BranchConflictError",
    "BranchNotFoundError",
    "NotAGitRepositoryError",
    # Constants
    "DEFAULT_BRANCH_PREFIX",
]
