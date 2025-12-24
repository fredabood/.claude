"""
Checkpoint and Rollback Support for Implementation Mode.

This module provides git checkpoint management for task execution, enabling
safe rollback if task implementation fails or produces undesirable results.

Key Features:
- Create git checkpoints before task execution
- Rollback to checkpoints on failure
- List and manage checkpoint tags
- Track files changed since checkpoint
- Automatic cleanup of old checkpoints

Checkpoint tags follow the pattern: checkpoint/{task_id}

Usage:
    from vibey.services.implementation import CheckpointManager
    from pathlib import Path

    # Initialize with repository root
    manager = CheckpointManager(repo_root=Path("."))

    # Create checkpoint before task
    tag = manager.create_checkpoint(task)

    # ... execute task ...

    # If task fails, rollback
    if failed:
        manager.rollback(tag)

    # Cleanup old checkpoints periodically
    manager.cleanup_old_checkpoints(keep_last=10)

Design Reference:
- Implementation Mode Track Sprint 1
- Task NE: Implement checkpoint and rollback support
"""

import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

CHECKPOINT_TAG_PREFIX = "checkpoint/"
"""Prefix for checkpoint git tags."""

DEFAULT_KEEP_CHECKPOINTS = 10
"""Default number of checkpoints to keep during cleanup."""


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class Checkpoint:
    """
    Record of a git checkpoint.

    Attributes:
        tag: Git tag name (e.g., "checkpoint/01KC...")
        task_id: ULID of the task this checkpoint is for
        commit_sha: SHA of the checkpoint commit
        created_at: When the checkpoint was created
        message: Checkpoint commit message
    """

    tag: str
    task_id: str
    commit_sha: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message: str = ""

    @property
    def tag_name(self) -> str:
        """Get just the tag name without the prefix."""
        if self.tag.startswith(CHECKPOINT_TAG_PREFIX):
            return self.tag[len(CHECKPOINT_TAG_PREFIX):]
        return self.tag


# =============================================================================
# EXCEPTIONS
# =============================================================================


class CheckpointError(Exception):
    """Base exception for checkpoint operations."""
    pass


class NotAGitRepositoryError(CheckpointError):
    """Raised when trying to operate on a non-git directory."""
    pass


class CheckpointNotFoundError(CheckpointError):
    """Raised when a checkpoint tag doesn't exist."""
    pass


class GitOperationError(CheckpointError):
    """Raised when a git operation fails."""
    pass


# =============================================================================
# CHECKPOINT MANAGER
# =============================================================================


class CheckpointManager:
    """
    Manages git checkpoints for task execution.

    Creates checkpoint commits and tags before task execution, enabling
    rollback if the task fails or produces undesirable results.

    Attributes:
        repo_root: Path to the git repository root

    Example:
        >>> manager = CheckpointManager(Path("."))
        >>> tag = manager.create_checkpoint(task)
        >>> # ... execute task ...
        >>> if failed:
        ...     manager.rollback(tag)
        >>> # Cleanup old checkpoints
        >>> manager.cleanup_old_checkpoints(keep_last=5)
    """

    def __init__(self, repo_root: Path):
        """
        Initialize checkpoint manager.

        Args:
            repo_root: Path to the git repository root

        Raises:
            NotAGitRepositoryError: If repo_root is not a git repository
        """
        self.repo_root = Path(repo_root).resolve()

        # Verify this is a git repository
        if not self._is_git_repo():
            raise NotAGitRepositoryError(
                f"Not a git repository: {self.repo_root}"
            )

    # =========================================================================
    # CHECKPOINT CREATION
    # =========================================================================

    def create_checkpoint(self, task: "HierarchicalTicket") -> str:
        """
        Create git checkpoint before task execution.

        Stages any uncommitted changes, creates a checkpoint commit,
        and tags it with the task ID.

        Args:
            task: The HierarchicalTicket being executed

        Returns:
            Checkpoint tag name (e.g., "checkpoint/01KC...")

        Raises:
            GitOperationError: If git operations fail
        """
        task_id = task.id
        tag_name = f"{CHECKPOINT_TAG_PREFIX}{task_id}"
        commit_message = f"[checkpoint] Before task: {task.name} ({task_id})"

        logger.info(f"Creating checkpoint for task {task_id}")

        try:
            # Step 1: Stage any uncommitted changes (if any)
            self._stage_all_changes()

            # Step 2: Check if there are changes to commit
            if self._has_staged_changes():
                # Create checkpoint commit
                self._run_git(
                    ["commit", "-m", commit_message],
                    "Failed to create checkpoint commit"
                )
                logger.debug(f"Created checkpoint commit for task {task_id}")
            else:
                # No changes to commit - create an empty commit as checkpoint
                self._run_git(
                    ["commit", "--allow-empty", "-m", commit_message],
                    "Failed to create empty checkpoint commit"
                )
                logger.debug(f"Created empty checkpoint commit for task {task_id}")

            # Step 3: Get the commit SHA
            commit_sha = self._get_head_sha()

            # Step 4: Create the tag
            # Delete existing tag if it exists (allow re-runs)
            self._delete_tag_if_exists(tag_name)
            self._run_git(
                ["tag", tag_name, commit_sha],
                f"Failed to create tag {tag_name}"
            )

            logger.info(f"Created checkpoint tag: {tag_name} at {commit_sha[:8]}")
            return tag_name

        except subprocess.CalledProcessError as e:
            raise GitOperationError(f"Git operation failed: {e}") from e

    # =========================================================================
    # ROLLBACK
    # =========================================================================

    def rollback(self, checkpoint_tag: str) -> None:
        """
        Rollback to checkpoint.

        Resets the repository to the checkpoint commit and removes
        the checkpoint tag.

        Args:
            checkpoint_tag: The checkpoint tag to rollback to

        Raises:
            CheckpointNotFoundError: If the checkpoint tag doesn't exist
            GitOperationError: If rollback fails
        """
        logger.info(f"Rolling back to checkpoint: {checkpoint_tag}")

        # Verify tag exists
        if not self._tag_exists(checkpoint_tag):
            raise CheckpointNotFoundError(
                f"Checkpoint tag not found: {checkpoint_tag}"
            )

        try:
            # Get the commit SHA for the tag
            commit_sha = self._get_tag_commit(checkpoint_tag)

            # Step 1: Reset to checkpoint commit (hard reset)
            self._run_git(
                ["reset", "--hard", commit_sha],
                f"Failed to reset to checkpoint {checkpoint_tag}"
            )
            logger.debug(f"Reset to commit {commit_sha[:8]}")

            # Step 2: Clean untracked files (created during task execution)
            self._run_git(
                ["clean", "-fd"],
                "Failed to clean untracked files"
            )
            logger.debug("Cleaned untracked files")

            # Step 3: Remove the checkpoint tag
            self._run_git(
                ["tag", "-d", checkpoint_tag],
                f"Failed to delete tag {checkpoint_tag}"
            )
            logger.debug(f"Deleted checkpoint tag: {checkpoint_tag}")

            # Log rollback event
            logger.info(
                f"Rollback complete: reset to {commit_sha[:8]}, "
                f"removed tag {checkpoint_tag}"
            )

        except subprocess.CalledProcessError as e:
            raise GitOperationError(f"Rollback failed: {e}") from e

    # =========================================================================
    # CHECKPOINT LISTING
    # =========================================================================

    def list_checkpoints(self) -> List[Checkpoint]:
        """
        List all checkpoint tags.

        Returns:
            List of Checkpoint objects, sorted by creation time (newest first)
        """
        checkpoints: List[Checkpoint] = []

        try:
            # Get all tags with checkpoint prefix
            result = self._run_git(
                ["tag", "-l", f"{CHECKPOINT_TAG_PREFIX}*"],
                "Failed to list checkpoint tags",
                capture_output=True
            )

            if not result.stdout.strip():
                return checkpoints

            tags = result.stdout.strip().split("\n")

            for tag in tags:
                if not tag:
                    continue

                try:
                    # Get commit info for tag
                    commit_sha = self._get_tag_commit(tag)
                    created_at, message = self._get_commit_info(commit_sha)

                    # Extract task ID from tag name
                    task_id = tag[len(CHECKPOINT_TAG_PREFIX):]

                    checkpoints.append(Checkpoint(
                        tag=tag,
                        task_id=task_id,
                        commit_sha=commit_sha,
                        created_at=created_at,
                        message=message,
                    ))
                except Exception as e:
                    logger.warning(f"Failed to get info for tag {tag}: {e}")

            # Sort by creation time, newest first
            checkpoints.sort(key=lambda c: c.created_at, reverse=True)

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list checkpoints: {e}")

        return checkpoints

    # =========================================================================
    # CLEANUP
    # =========================================================================

    def cleanup_old_checkpoints(self, keep_last: int = DEFAULT_KEEP_CHECKPOINTS) -> int:
        """
        Remove old checkpoint tags.

        Keeps the most recent checkpoints and removes older ones.

        Args:
            keep_last: Number of most recent checkpoints to keep

        Returns:
            Number of checkpoints removed
        """
        checkpoints = self.list_checkpoints()

        if len(checkpoints) <= keep_last:
            logger.debug(
                f"Only {len(checkpoints)} checkpoints exist, "
                f"keeping all (threshold: {keep_last})"
            )
            return 0

        # Checkpoints are already sorted newest-first
        to_remove = checkpoints[keep_last:]
        removed = 0

        for checkpoint in to_remove:
            try:
                self._run_git(
                    ["tag", "-d", checkpoint.tag],
                    f"Failed to delete tag {checkpoint.tag}"
                )
                removed += 1
                logger.debug(f"Removed old checkpoint: {checkpoint.tag}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to remove checkpoint {checkpoint.tag}: {e}")

        logger.info(f"Cleaned up {removed} old checkpoints (kept {keep_last})")
        return removed

    # =========================================================================
    # CHANGE TRACKING
    # =========================================================================

    def get_changes_since_checkpoint(self, tag: str) -> List[Path]:
        """
        Get files changed since checkpoint.

        Args:
            tag: Checkpoint tag to compare against

        Returns:
            List of paths to files that were modified, added, or deleted

        Raises:
            CheckpointNotFoundError: If the checkpoint tag doesn't exist
        """
        if not self._tag_exists(tag):
            raise CheckpointNotFoundError(f"Checkpoint tag not found: {tag}")

        changed_files: List[Path] = []

        try:
            # Get files changed between checkpoint and HEAD
            result = self._run_git(
                ["diff", "--name-only", tag, "HEAD"],
                f"Failed to get changes since {tag}",
                capture_output=True
            )

            if result.stdout.strip():
                for file_path in result.stdout.strip().split("\n"):
                    if file_path:
                        changed_files.append(self.repo_root / file_path)

            # Also get untracked files (new files not yet committed)
            untracked_result = self._run_git(
                ["ls-files", "--others", "--exclude-standard"],
                "Failed to get untracked files",
                capture_output=True
            )

            if untracked_result.stdout.strip():
                for file_path in untracked_result.stdout.strip().split("\n"):
                    if file_path:
                        full_path = self.repo_root / file_path
                        if full_path not in changed_files:
                            changed_files.append(full_path)

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get changes since checkpoint: {e}")

        return changed_files

    def has_changes_since_checkpoint(self, tag: str) -> bool:
        """
        Check if there are any changes since the checkpoint.

        Args:
            tag: Checkpoint tag to check against

        Returns:
            True if there are changes, False otherwise
        """
        return len(self.get_changes_since_checkpoint(tag)) > 0

    # =========================================================================
    # HELPER METHODS - GIT OPERATIONS
    # =========================================================================

    def _run_git(
        self,
        args: List[str],
        error_message: str,
        capture_output: bool = False
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

        if capture_output:
            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
        else:
            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=True
            )

        return result

    def _is_git_repo(self) -> bool:
        """Check if repo_root is a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_root,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def _stage_all_changes(self) -> None:
        """Stage all changes (modified, deleted, new files)."""
        try:
            self._run_git(
                ["add", "-A"],
                "Failed to stage changes"
            )
        except subprocess.CalledProcessError:
            # May fail if nothing to add, that's OK
            pass

    def _has_staged_changes(self) -> bool:
        """Check if there are staged changes to commit."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=self.repo_root,
                capture_output=True
            )
            # Return code 0 means no changes, 1 means changes exist
            return result.returncode == 1
        except Exception:
            return False

    def _get_head_sha(self) -> str:
        """Get the SHA of HEAD commit."""
        result = self._run_git(
            ["rev-parse", "HEAD"],
            "Failed to get HEAD SHA",
            capture_output=True
        )
        return result.stdout.strip()

    def _tag_exists(self, tag: str) -> bool:
        """Check if a tag exists."""
        try:
            result = subprocess.run(
                ["git", "tag", "-l", tag],
                cwd=self.repo_root,
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and tag in result.stdout
        except Exception:
            return False

    def _delete_tag_if_exists(self, tag: str) -> None:
        """Delete a tag if it exists."""
        if self._tag_exists(tag):
            try:
                self._run_git(
                    ["tag", "-d", tag],
                    f"Failed to delete existing tag {tag}"
                )
                logger.debug(f"Deleted existing tag: {tag}")
            except subprocess.CalledProcessError:
                pass

    def _get_tag_commit(self, tag: str) -> str:
        """Get the commit SHA for a tag."""
        result = self._run_git(
            ["rev-list", "-n", "1", tag],
            f"Failed to get commit for tag {tag}",
            capture_output=True
        )
        return result.stdout.strip()

    def _get_commit_info(self, commit_sha: str) -> tuple:
        """
        Get commit timestamp and message.

        Returns:
            Tuple of (datetime, message)
        """
        result = self._run_git(
            ["log", "-1", "--format=%aI|%s", commit_sha],
            f"Failed to get commit info for {commit_sha}",
            capture_output=True
        )

        parts = result.stdout.strip().split("|", 1)
        timestamp_str = parts[0]
        message = parts[1] if len(parts) > 1 else ""

        # Parse ISO format timestamp
        created_at = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

        return created_at, message


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def create_task_checkpoint(
    task: "HierarchicalTicket",
    repo_root: Optional[Path] = None
) -> str:
    """
    Convenience function to create a checkpoint for a task.

    Args:
        task: The HierarchicalTicket to create checkpoint for
        repo_root: Path to git repository (defaults to cwd)

    Returns:
        Checkpoint tag name
    """
    if repo_root is None:
        repo_root = Path.cwd()

    manager = CheckpointManager(repo_root)
    return manager.create_checkpoint(task)


def rollback_task_checkpoint(
    checkpoint_tag: str,
    repo_root: Optional[Path] = None
) -> None:
    """
    Convenience function to rollback to a checkpoint.

    Args:
        checkpoint_tag: The checkpoint tag to rollback to
        repo_root: Path to git repository (defaults to cwd)
    """
    if repo_root is None:
        repo_root = Path.cwd()

    manager = CheckpointManager(repo_root)
    manager.rollback(checkpoint_tag)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Main class
    "CheckpointManager",
    # Data models
    "Checkpoint",
    # Exceptions
    "CheckpointError",
    "NotAGitRepositoryError",
    "CheckpointNotFoundError",
    "GitOperationError",
    # Constants
    "CHECKPOINT_TAG_PREFIX",
    "DEFAULT_KEEP_CHECKPOINTS",
    # Convenience functions
    "create_task_checkpoint",
    "rollback_task_checkpoint",
]
