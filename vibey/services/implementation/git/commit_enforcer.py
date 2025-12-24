"""
Commit frequency enforcement for disciplined git workflow.

This module provides the CommitFrequencyEnforcer class that helps maintain
disciplined commit practices during task execution by:
- Tracking time since last commit
- Counting files and lines changed
- Generating WIP commits with progress info
- Supporting conventional commit types

Usage:
    from vibey.services.implementation.git import CommitFrequencyEnforcer
    from vibey.services.implementation import ImplementConfig
    from pathlib import Path

    config = ImplementConfig()
    enforcer = CommitFrequencyEnforcer(config, Path("."))

    # Check if commit is needed
    check = enforcer.check_commit_needed()
    if check.result in (CommitCheckResult.REQUIRED, CommitCheckResult.OVERDUE):
        enforcer.create_wip_commit("TASK-123", progress_percent=50)

    # Or create logical commits at breakpoints
    enforcer.create_logical_commit(
        ticket_id="TASK-123",
        description="Add user authentication endpoint",
        commit_type="feat"
    )
"""

import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from vibey.services.implementation.config import ImplementConfig

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_MAX_MINUTES_BETWEEN_COMMITS = 15
"""Default maximum minutes between commits."""

DEFAULT_MAX_FILES_CHANGED = 10
"""Default maximum files changed before commit recommended."""

DEFAULT_MAX_LINES_CHANGED = 500
"""Default maximum lines changed before commit recommended."""

CONVENTIONAL_COMMIT_TYPES = (
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
    "wip",
)
"""Valid conventional commit types."""


# =============================================================================
# ENUMS
# =============================================================================


class CommitCheckResult(Enum):
    """Result of commit frequency check."""

    NOT_NEEDED = "not_needed"
    """No changes to commit."""

    RECOMMENDED = "recommended"
    """Commit is recommended but not required."""

    REQUIRED = "required"
    """Commit should be made soon."""

    OVERDUE = "overdue"
    """Commit is overdue and should be made immediately."""


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class CommitStats:
    """
    Statistics about commits in the current session.

    Attributes:
        commit_count: Number of commits made in this session
        total_files_changed: Total files changed across all commits
        total_lines_added: Total lines added across all commits
        total_lines_deleted: Total lines deleted across all commits
        first_commit_at: Timestamp of first commit in session
        last_commit_at: Timestamp of most recent commit
        avg_time_between_commits: Average time between commits
    """

    commit_count: int = 0
    total_files_changed: int = 0
    total_lines_added: int = 0
    total_lines_deleted: int = 0
    first_commit_at: Optional[datetime] = None
    last_commit_at: Optional[datetime] = None
    avg_time_between_commits: Optional[timedelta] = None


@dataclass
class CommitCheck:
    """
    Result of checking if commit is needed.

    Attributes:
        result: The check result (NOT_NEEDED, RECOMMENDED, REQUIRED, OVERDUE)
        reason: Human-readable explanation for the result
        minutes_since_last: Minutes since last commit (if applicable)
        files_changed: Number of files with uncommitted changes
        lines_changed: Total lines changed (added + deleted)
    """

    result: CommitCheckResult
    reason: str
    minutes_since_last: Optional[float] = None
    files_changed: int = 0
    lines_changed: int = 0


@dataclass
class DiffStats:
    """
    Statistics from git diff.

    Attributes:
        files_changed: Number of files changed
        lines_added: Number of lines added
        lines_deleted: Number of lines deleted
    """

    files_changed: int = 0
    lines_added: int = 0
    lines_deleted: int = 0

    @property
    def total_lines_changed(self) -> int:
        """Total lines changed (added + deleted)."""
        return self.lines_added + self.lines_deleted


# =============================================================================
# EXCEPTIONS
# =============================================================================


class CommitEnforcerError(Exception):
    """Base exception for commit enforcer operations."""

    pass


class NotAGitRepositoryError(CommitEnforcerError):
    """Raised when trying to operate on a non-git directory."""

    pass


class GitOperationError(CommitEnforcerError):
    """Raised when a git operation fails."""

    pass


class CommitError(CommitEnforcerError):
    """Raised when creating a commit fails."""

    pass


# =============================================================================
# COMMIT FREQUENCY ENFORCER
# =============================================================================


class CommitFrequencyEnforcer:
    """
    Enforces regular commits during task execution.

    This class helps maintain disciplined commit practices by tracking time
    since the last commit, counting changes, and providing methods to create
    both WIP (work-in-progress) and logical commits.

    Attributes:
        config: Implementation configuration
        repo_root: Path to the git repository root
        last_commit_at: Timestamp of last commit made through this enforcer
        uncommitted_changes: List of files with uncommitted changes
        commit_count: Number of commits made in this session

    Example:
        >>> config = ImplementConfig()
        >>> enforcer = CommitFrequencyEnforcer(config, Path("."))
        >>> check = enforcer.check_commit_needed()
        >>> if check.result == CommitCheckResult.REQUIRED:
        ...     enforcer.create_wip_commit("TASK-123", progress_percent=50)
    """

    def __init__(self, config: "ImplementConfig", repo_root: Path):
        """
        Initialize the commit frequency enforcer.

        Args:
            config: Implementation configuration
            repo_root: Path to the git repository root

        Raises:
            NotAGitRepositoryError: If repo_root is not a git repository
        """
        self.config = config
        self.repo_root = Path(repo_root).resolve()
        self.last_commit_at: Optional[datetime] = None
        self.uncommitted_changes: List[Path] = []
        self.commit_count: int = 0
        self._commit_times: List[datetime] = []  # Track all commit times for stats

        # Extract thresholds from config with defaults
        self.max_minutes_between = getattr(
            config, "max_minutes_between_commits", DEFAULT_MAX_MINUTES_BETWEEN_COMMITS
        )
        self.max_files_changed = getattr(
            config, "max_files_changed", DEFAULT_MAX_FILES_CHANGED
        )
        self.max_lines_changed = getattr(
            config, "max_lines_changed", DEFAULT_MAX_LINES_CHANGED
        )

        # Verify this is a git repository
        if not self._is_git_repo():
            raise NotAGitRepositoryError(f"Not a git repository: {self.repo_root}")

        # Initialize last commit time from git history
        self._initialize_last_commit_time()

    # =========================================================================
    # PUBLIC API - CHECK COMMIT NEEDED
    # =========================================================================

    def check_commit_needed(self) -> CommitCheck:
        """
        Check if a commit is needed based on time, files, and lines changed.

        Evaluates multiple factors to determine if a commit should be made:
        1. Time since last commit
        2. Number of files changed
        3. Number of lines changed

        Returns:
            CommitCheck with result and explanation

        Example:
            >>> check = enforcer.check_commit_needed()
            >>> if check.result == CommitCheckResult.OVERDUE:
            ...     print(f"Commit overdue: {check.reason}")
        """
        # Get uncommitted changes
        uncommitted = self.get_uncommitted_changes()
        if not uncommitted:
            return CommitCheck(
                result=CommitCheckResult.NOT_NEEDED,
                reason="No uncommitted changes",
                files_changed=0,
                lines_changed=0,
            )

        # Get diff stats
        diff_stats = self._get_diff_stats()
        files_changed = diff_stats.files_changed
        lines_changed = diff_stats.total_lines_changed

        # Calculate minutes since last commit
        minutes_since_last: Optional[float] = None
        if self.last_commit_at:
            delta = datetime.now(timezone.utc) - self.last_commit_at
            minutes_since_last = delta.total_seconds() / 60

        # Determine result based on thresholds
        reasons: List[str] = []
        severity = 0  # 0=NOT_NEEDED, 1=RECOMMENDED, 2=REQUIRED, 3=OVERDUE

        # Check time threshold
        if minutes_since_last is not None:
            if minutes_since_last > self.max_minutes_between * 2:
                reasons.append(
                    f"Time since last commit ({minutes_since_last:.0f}m) "
                    f"exceeds 2x threshold ({self.max_minutes_between * 2}m)"
                )
                severity = max(severity, 3)
            elif minutes_since_last > self.max_minutes_between:
                reasons.append(
                    f"Time since last commit ({minutes_since_last:.0f}m) "
                    f"exceeds threshold ({self.max_minutes_between}m)"
                )
                severity = max(severity, 2)
            elif minutes_since_last > self.max_minutes_between * 0.75:
                reasons.append(
                    f"Time since last commit ({minutes_since_last:.0f}m) "
                    f"approaching threshold ({self.max_minutes_between}m)"
                )
                severity = max(severity, 1)

        # Check files threshold
        if files_changed > self.max_files_changed * 2:
            reasons.append(
                f"Files changed ({files_changed}) "
                f"exceeds 2x threshold ({self.max_files_changed * 2})"
            )
            severity = max(severity, 3)
        elif files_changed > self.max_files_changed:
            reasons.append(
                f"Files changed ({files_changed}) "
                f"exceeds threshold ({self.max_files_changed})"
            )
            severity = max(severity, 2)
        elif files_changed > self.max_files_changed * 0.75:
            reasons.append(
                f"Files changed ({files_changed}) "
                f"approaching threshold ({self.max_files_changed})"
            )
            severity = max(severity, 1)

        # Check lines threshold
        if lines_changed > self.max_lines_changed * 2:
            reasons.append(
                f"Lines changed ({lines_changed}) "
                f"exceeds 2x threshold ({self.max_lines_changed * 2})"
            )
            severity = max(severity, 3)
        elif lines_changed > self.max_lines_changed:
            reasons.append(
                f"Lines changed ({lines_changed}) "
                f"exceeds threshold ({self.max_lines_changed})"
            )
            severity = max(severity, 2)
        elif lines_changed > self.max_lines_changed * 0.75:
            reasons.append(
                f"Lines changed ({lines_changed}) "
                f"approaching threshold ({self.max_lines_changed})"
            )
            severity = max(severity, 1)

        # Map severity to result
        result_map = {
            0: CommitCheckResult.NOT_NEEDED,
            1: CommitCheckResult.RECOMMENDED,
            2: CommitCheckResult.REQUIRED,
            3: CommitCheckResult.OVERDUE,
        }

        # Default reason if changes exist but no thresholds triggered
        if not reasons and uncommitted:
            reasons = ["Uncommitted changes present"]

        return CommitCheck(
            result=result_map.get(severity, CommitCheckResult.NOT_NEEDED),
            reason="; ".join(reasons) if reasons else "No action needed",
            minutes_since_last=minutes_since_last,
            files_changed=files_changed,
            lines_changed=lines_changed,
        )

    def get_uncommitted_changes(self) -> List[Path]:
        """
        Get list of files with uncommitted changes.

        Returns both staged and unstaged changes, as well as untracked files.

        Returns:
            List of Path objects for files with uncommitted changes
        """
        uncommitted: List[Path] = []

        try:
            # Get modified/staged files
            result = self._run_git(
                ["status", "--porcelain"],
                "Failed to get git status",
                capture_output=True,
            )

            if result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    if line and len(line) > 3:
                        # Status is first 2 chars, then space, then filename
                        file_path = line[3:].strip()
                        # Handle renamed files (old -> new)
                        if " -> " in file_path:
                            file_path = file_path.split(" -> ")[1]
                        uncommitted.append(self.repo_root / file_path)

        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to get uncommitted changes: {e}")

        self.uncommitted_changes = uncommitted
        return uncommitted

    def should_commit_now(self) -> bool:
        """
        Determine if commit needed now.

        A convenience method that returns True if the check result
        is REQUIRED or OVERDUE.

        Returns:
            True if commit is required or overdue
        """
        check = self.check_commit_needed()
        return check.result in (CommitCheckResult.REQUIRED, CommitCheckResult.OVERDUE)

    # =========================================================================
    # PUBLIC API - CREATE COMMITS
    # =========================================================================

    def create_wip_commit(
        self, ticket_id: str, progress_percent: Optional[int] = None
    ) -> str:
        """
        Create work-in-progress commit.

        Creates a WIP commit with a standardized message format that includes
        the ticket ID and optional progress percentage.

        Args:
            ticket_id: The ticket/task ID (e.g., "TASK-123" or ULID)
            progress_percent: Optional progress percentage (0-100)

        Returns:
            The commit hash

        Raises:
            CommitError: If there are no changes to commit or commit fails

        Example:
            >>> commit_hash = enforcer.create_wip_commit("01KC2D0...", 50)
            >>> print(f"Created WIP commit: {commit_hash}")
        """
        # Verify there are changes to commit
        uncommitted = self.get_uncommitted_changes()
        if not uncommitted:
            raise CommitError("No changes to commit")

        # Build commit message
        progress_str = ""
        if progress_percent is not None:
            progress_percent = max(0, min(100, progress_percent))
            progress_str = f" [{progress_percent}%]"

        message = f"wip({ticket_id}): Work in progress{progress_str}"

        # Get diff stats for extended message
        diff_stats = self._get_diff_stats()
        extended_msg = (
            f"\n\nFiles changed: {diff_stats.files_changed}\n"
            f"Lines added: {diff_stats.lines_added}\n"
            f"Lines deleted: {diff_stats.lines_deleted}"
        )

        full_message = message + extended_msg

        # Stage and commit
        return self._create_commit(full_message)

    def create_logical_commit(
        self,
        ticket_id: str,
        description: str,
        files: Optional[List[Path]] = None,
        commit_type: str = "feat",
    ) -> str:
        """
        Create commit at logical breakpoint.

        Creates a conventional commit with proper type, scope (ticket ID),
        and description. Optionally stages only specific files.

        Args:
            ticket_id: The ticket/task ID for the scope
            description: Brief description of the change
            files: Optional list of specific files to stage (default: all)
            commit_type: Conventional commit type (feat, fix, etc.)

        Returns:
            The commit hash

        Raises:
            CommitError: If commit fails
            ValueError: If commit_type is not valid

        Example:
            >>> commit_hash = enforcer.create_logical_commit(
            ...     ticket_id="01KC2D0...",
            ...     description="Add user authentication endpoint",
            ...     commit_type="feat"
            ... )
        """
        # Validate commit type
        if commit_type not in CONVENTIONAL_COMMIT_TYPES:
            raise ValueError(
                f"Invalid commit type '{commit_type}'. "
                f"Valid types: {', '.join(CONVENTIONAL_COMMIT_TYPES)}"
            )

        # Build commit message (conventional format)
        message = f"{commit_type}({ticket_id}): {description}"

        # Stage files
        if files:
            self._stage_files(files)
        else:
            self._stage_all_changes()

        # Verify there are staged changes
        if not self._has_staged_changes():
            raise CommitError("No changes to commit after staging")

        return self._create_commit(message, skip_stage=True)

    # =========================================================================
    # PUBLIC API - STATISTICS
    # =========================================================================

    def get_commit_stats(self) -> CommitStats:
        """
        Get statistics about commits this session.

        Returns:
            CommitStats with session statistics
        """
        stats = CommitStats(
            commit_count=self.commit_count,
            first_commit_at=self._commit_times[0] if self._commit_times else None,
            last_commit_at=self._commit_times[-1] if self._commit_times else None,
        )

        # Calculate average time between commits
        if len(self._commit_times) > 1:
            deltas = [
                self._commit_times[i + 1] - self._commit_times[i]
                for i in range(len(self._commit_times) - 1)
            ]
            total_seconds = sum(d.total_seconds() for d in deltas)
            stats.avg_time_between_commits = timedelta(
                seconds=total_seconds / len(deltas)
            )

        return stats

    def on_commit_complete(self, commit_hash: str) -> None:
        """
        Called after successful commit to update tracking.

        This method should be called after a commit is successfully created
        (either through this class or externally) to update internal tracking.

        Args:
            commit_hash: The SHA of the created commit
        """
        now = datetime.now(timezone.utc)
        self.last_commit_at = now
        self.commit_count += 1
        self._commit_times.append(now)
        self.uncommitted_changes.clear()
        logger.debug(f"Recorded commit: {commit_hash[:8]}")

    # =========================================================================
    # HELPER METHODS - GIT OPERATIONS
    # =========================================================================

    def _run_git(
        self,
        args: List[str],
        error_message: str,
        capture_output: bool = False,
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
            capture_output=True,
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

    def _initialize_last_commit_time(self) -> None:
        """Initialize last commit time from git history."""
        try:
            result = self._run_git(
                ["log", "-1", "--format=%aI"],
                "Failed to get last commit time",
                capture_output=True,
            )
            if result.stdout.strip():
                timestamp_str = result.stdout.strip()
                self.last_commit_at = datetime.fromisoformat(
                    timestamp_str.replace("Z", "+00:00")
                )
                logger.debug(f"Initialized last commit time: {self.last_commit_at}")
        except subprocess.CalledProcessError:
            # No commits in repo yet
            self.last_commit_at = None
            logger.debug("No previous commits found")

    def _get_diff_stats(self) -> DiffStats:
        """
        Get statistics from git diff.

        Returns:
            DiffStats with files changed, lines added/deleted
        """
        stats = DiffStats()

        try:
            # Get diff stats for staged and unstaged changes
            result = self._run_git(
                ["diff", "--stat", "--stat-count=10000", "HEAD"],
                "Failed to get diff stats",
                capture_output=True,
            )

            if result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                # Last line contains summary: "X files changed, Y insertions(+), Z deletions(-)"
                if lines:
                    summary_line = lines[-1].strip()
                    stats = self._parse_diff_summary(summary_line)

        except subprocess.CalledProcessError:
            # May fail if there's no HEAD (first commit)
            # Try with unstaged only
            try:
                result = self._run_git(
                    ["diff", "--stat", "--stat-count=10000"],
                    "Failed to get unstaged diff stats",
                    capture_output=True,
                )
                if result.stdout.strip():
                    lines = result.stdout.strip().split("\n")
                    if lines:
                        summary_line = lines[-1].strip()
                        stats = self._parse_diff_summary(summary_line)
            except subprocess.CalledProcessError:
                pass

        return stats

    def _parse_diff_summary(self, summary_line: str) -> DiffStats:
        """
        Parse git diff --stat summary line.

        Args:
            summary_line: The summary line from git diff --stat

        Returns:
            DiffStats with parsed values
        """
        stats = DiffStats()

        # Example: "5 files changed, 120 insertions(+), 30 deletions(-)"
        import re

        files_match = re.search(r"(\d+)\s+files?\s+changed", summary_line)
        insertions_match = re.search(r"(\d+)\s+insertions?", summary_line)
        deletions_match = re.search(r"(\d+)\s+deletions?", summary_line)

        if files_match:
            stats.files_changed = int(files_match.group(1))
        if insertions_match:
            stats.lines_added = int(insertions_match.group(1))
        if deletions_match:
            stats.lines_deleted = int(deletions_match.group(1))

        return stats

    def _stage_all_changes(self) -> None:
        """Stage all changes (modified, deleted, new files)."""
        try:
            self._run_git(["add", "-A"], "Failed to stage changes")
        except subprocess.CalledProcessError:
            # May fail if nothing to add
            pass

    def _stage_files(self, files: List[Path]) -> None:
        """
        Stage specific files.

        Args:
            files: List of file paths to stage
        """
        for file_path in files:
            try:
                # Use relative path from repo root
                if file_path.is_absolute():
                    rel_path = file_path.relative_to(self.repo_root)
                else:
                    rel_path = file_path

                self._run_git(["add", str(rel_path)], f"Failed to stage {rel_path}")
            except (subprocess.CalledProcessError, ValueError) as e:
                logger.warning(f"Failed to stage {file_path}: {e}")

    def _has_staged_changes(self) -> bool:
        """Check if there are staged changes to commit."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=self.repo_root,
                capture_output=True,
            )
            # Return code 0 means no changes, 1 means changes exist
            return result.returncode == 1
        except Exception:
            return False

    def _create_commit(self, message: str, skip_stage: bool = False) -> str:
        """
        Create a git commit.

        Args:
            message: Commit message
            skip_stage: If True, skip staging (assume already staged)

        Returns:
            Commit hash

        Raises:
            CommitError: If commit fails
        """
        try:
            # Stage all changes unless skipped
            if not skip_stage:
                self._stage_all_changes()

            # Verify there are staged changes
            if not self._has_staged_changes():
                raise CommitError("No changes to commit")

            # Create commit
            self._run_git(["commit", "-m", message], "Failed to create commit")

            # Get the commit hash
            result = self._run_git(
                ["rev-parse", "HEAD"],
                "Failed to get commit hash",
                capture_output=True,
            )
            commit_hash = result.stdout.strip()

            # Update tracking
            self.on_commit_complete(commit_hash)

            logger.info(f"Created commit: {commit_hash[:8]}")
            return commit_hash

        except subprocess.CalledProcessError as e:
            raise CommitError(f"Failed to create commit: {e}") from e


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Main class
    "CommitFrequencyEnforcer",
    # Enums
    "CommitCheckResult",
    # Data models
    "CommitStats",
    "CommitCheck",
    "DiffStats",
    # Exceptions
    "CommitEnforcerError",
    "NotAGitRepositoryError",
    "GitOperationError",
    "CommitError",
    # Constants
    "DEFAULT_MAX_MINUTES_BETWEEN_COMMITS",
    "DEFAULT_MAX_FILES_CHANGED",
    "DEFAULT_MAX_LINES_CHANGED",
    "CONVENTIONAL_COMMIT_TYPES",
]
