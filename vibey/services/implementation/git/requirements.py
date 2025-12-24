"""
Git Requirements Enforcement for Implementation Mode.

This module provides strict validation of git repository state before and during
task execution, ensuring a clean and predictable environment for implementation.

Key Features:
- Validate clean working tree (no uncommitted changes)
- Verify correct branch state
- Check remote synchronization status
- Detect merge conflicts
- Support multiple enforcement levels (strict/standard/relaxed)
- Auto-remediation of common issues (stash, pull, checkout)

Usage:
    from vibey.services.implementation.git import GitRequirementsEnforcer
    from vibey.services.implementation.config import ImplementConfig
    from pathlib import Path

    config = ImplementConfig()
    enforcer = GitRequirementsEnforcer(config, repo_root=Path("."))

    # Validate preconditions
    result = enforcer.validate_preconditions()
    if not result.passed:
        for issue in result.issues:
            print(f"{issue.severity.value}: {issue.message}")

    # Full enforcement with remediation
    enforcement = enforcer.enforce_requirements(ticket)
    if enforcement.can_proceed:
        # Execute task...
        pass

Design Reference:
- Implementation Mode Track Sprint 2
- Task: Implement GitRequirementsEnforcer for strict validation
"""

import logging
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
    from vibey.services.implementation.config import ImplementConfig

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_STASH_MESSAGE_PREFIX = "vibey-autostash"
"""Prefix for auto-stash messages created during remediation."""

DEFAULT_MAIN_BRANCHES = ("main", "master")
"""Common names for the main branch."""


# =============================================================================
# ENUMS
# =============================================================================


class RequirementLevel(str, Enum):
    """
    Strictness level for git requirements.

    Values:
        STRICT: Block on any violation
        STANDARD: Block on major issues, warn on minor
        RELAXED: Warn only, don't block
    """

    STRICT = "strict"
    STANDARD = "standard"
    RELAXED = "relaxed"


class GitIssueType(str, Enum):
    """
    Types of git issues that can be detected.

    Values:
        DIRTY_TREE: Uncommitted changes in working tree
        WRONG_BRANCH: Not on expected branch
        BEHIND_REMOTE: Local branch is behind remote
        AHEAD_OF_REMOTE: Local branch has unpushed commits
        MERGE_CONFLICTS: Unresolved merge conflicts exist
        HOOKS_MISSING: Expected git hooks not installed
        DIVERGED: Local and remote have diverged
        NO_UPSTREAM: Branch has no upstream tracking
        DETACHED_HEAD: Repository is in detached HEAD state
    """

    DIRTY_TREE = "dirty_tree"
    WRONG_BRANCH = "wrong_branch"
    BEHIND_REMOTE = "behind_remote"
    AHEAD_OF_REMOTE = "ahead_of_remote"
    MERGE_CONFLICTS = "merge_conflicts"
    HOOKS_MISSING = "hooks_missing"
    DIVERGED = "diverged"
    NO_UPSTREAM = "no_upstream"
    DETACHED_HEAD = "detached_head"


class IssueSeverity(str, Enum):
    """
    Severity of git issues.

    Values:
        INFO: Informational only, no action needed
        WARNING: May cause problems, but can proceed
        ERROR: Should be fixed before proceeding
        CRITICAL: Must be fixed, blocks execution
    """

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class GitIssue:
    """
    A git state issue detected during validation.

    Attributes:
        type: Type of the git issue
        severity: Severity level of the issue
        message: Human-readable description of the issue
        can_auto_fix: Whether this issue can be automatically remediated
        fix_command: Git command that would fix this issue (if applicable)
        details: Additional details about the issue
    """

    type: GitIssueType
    severity: IssueSeverity
    message: str
    can_auto_fix: bool = False
    fix_command: Optional[str] = None
    details: Optional[str] = None


@dataclass
class SyncStatus:
    """
    Status of local/remote synchronization.

    Attributes:
        is_synced: True if local and remote are in sync
        ahead_by: Number of commits local is ahead of remote
        behind_by: Number of commits local is behind remote
        diverged: True if local and remote have diverged
        has_upstream: True if branch has upstream tracking configured
    """

    is_synced: bool
    ahead_by: int = 0
    behind_by: int = 0
    diverged: bool = False
    has_upstream: bool = True


@dataclass
class ValidationResult:
    """
    Result of git validation checks.

    Attributes:
        passed: True if all required checks passed
        issues: List of issues detected during validation
        warnings: List of warning messages
        current_branch: Current git branch name
        is_clean: True if working tree is clean
    """

    passed: bool
    issues: List[GitIssue] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    current_branch: Optional[str] = None
    is_clean: bool = True

    @property
    def has_blocking_issues(self) -> bool:
        """Check if there are any issues that should block execution."""
        return any(
            i.severity in (IssueSeverity.ERROR, IssueSeverity.CRITICAL)
            for i in self.issues
        )

    @property
    def error_count(self) -> int:
        """Count of error-level issues."""
        return sum(
            1 for i in self.issues
            if i.severity in (IssueSeverity.ERROR, IssueSeverity.CRITICAL)
        )

    @property
    def warning_count(self) -> int:
        """Count of warning-level issues."""
        return sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)


@dataclass
class RemediationResult:
    """
    Result of auto-remediation attempt.

    Attributes:
        success: True if all fixable issues were resolved
        fixed_issues: Issues that were successfully fixed
        unfixed_issues: Issues that could not be fixed
        stash_ref: Reference to stashed changes (if stashing was performed)
        actions_taken: List of actions performed during remediation
    """

    success: bool
    fixed_issues: List[GitIssue] = field(default_factory=list)
    unfixed_issues: List[GitIssue] = field(default_factory=list)
    stash_ref: Optional[str] = None
    actions_taken: List[str] = field(default_factory=list)


@dataclass
class EnforcementResult:
    """
    Result of enforcement including validation and remediation attempts.

    Attributes:
        validation: Initial validation result
        remediation_attempted: Whether remediation was tried
        remediation_success: Whether remediation succeeded
        can_proceed: Whether execution can proceed
        stashed_changes: Whether changes were stashed during remediation
        final_issues: Issues remaining after remediation
    """

    validation: ValidationResult
    remediation_attempted: bool = False
    remediation_success: bool = False
    can_proceed: bool = False
    stashed_changes: bool = False
    final_issues: List[GitIssue] = field(default_factory=list)


# =============================================================================
# EXCEPTIONS
# =============================================================================


class GitRequirementsError(Exception):
    """Base exception for git requirements errors."""
    pass


class NotAGitRepositoryError(GitRequirementsError):
    """Raised when trying to operate on a non-git directory."""
    pass


class GitOperationError(GitRequirementsError):
    """Raised when a git operation fails."""
    pass


# =============================================================================
# GIT REQUIREMENTS ENFORCER
# =============================================================================


class GitRequirementsEnforcer:
    """
    Enforces git requirements before and during task execution.

    Validates that the git repository is in a suitable state for implementation
    and can optionally auto-remediate common issues.

    Attributes:
        config: Implementation configuration
        repo_root: Path to the git repository root
        level: Enforcement strictness level

    Example:
        >>> enforcer = GitRequirementsEnforcer(config, Path("."))
        >>> result = enforcer.validate_preconditions()
        >>> if not result.passed:
        ...     print(f"Validation failed: {result.issues}")
        >>> # Or use full enforcement
        >>> enforcement = enforcer.enforce_requirements(ticket)
        >>> if enforcement.can_proceed:
        ...     # Safe to execute task
    """

    def __init__(
        self,
        config: "ImplementConfig",
        repo_root: Path,
        level: RequirementLevel = RequirementLevel.STRICT,
    ):
        """
        Initialize git requirements enforcer.

        Args:
            config: ImplementConfig with execution parameters
            repo_root: Path to the git repository root
            level: Enforcement strictness level

        Raises:
            NotAGitRepositoryError: If repo_root is not a git repository
        """
        self.config = config
        self.repo_root = Path(repo_root).resolve()
        self.level = level

        # Verify this is a git repository
        if not self._is_git_repo():
            raise NotAGitRepositoryError(
                f"Not a git repository: {self.repo_root}"
            )

    # =========================================================================
    # MAIN VALIDATION
    # =========================================================================

    def validate_preconditions(self) -> ValidationResult:
        """
        Validate all git preconditions before task execution.

        Performs comprehensive checks of the git repository state:
        - Clean working tree (no uncommitted changes)
        - Not in detached HEAD state
        - No merge conflicts
        - Remote synchronization status

        Returns:
            ValidationResult with all detected issues and warnings
        """
        issues: List[GitIssue] = []
        warnings: List[str] = []

        # Get current branch
        current_branch = self._get_current_branch()

        # Check for detached HEAD
        if current_branch is None:
            issues.append(GitIssue(
                type=GitIssueType.DETACHED_HEAD,
                severity=IssueSeverity.ERROR,
                message="Repository is in detached HEAD state",
                can_auto_fix=False,
            ))

        # Check for clean working tree
        is_clean = self.validate_clean_tree()
        if not is_clean:
            dirty_files = self._get_dirty_files()
            issues.append(GitIssue(
                type=GitIssueType.DIRTY_TREE,
                severity=self._get_severity_for_issue(GitIssueType.DIRTY_TREE),
                message=f"Working tree has {len(dirty_files)} uncommitted change(s)",
                can_auto_fix=True,
                fix_command="git stash push -m 'vibey-autostash'",
                details="\n".join(dirty_files[:10]),  # Limit to first 10
            ))

        # Check for merge conflicts
        if self._has_merge_conflicts():
            issues.append(GitIssue(
                type=GitIssueType.MERGE_CONFLICTS,
                severity=IssueSeverity.CRITICAL,
                message="Unresolved merge conflicts detected",
                can_auto_fix=False,
            ))

        # Check remote sync status
        if current_branch:
            sync_status = self.validate_remote_sync()
            if not sync_status.is_synced:
                if sync_status.diverged:
                    issues.append(GitIssue(
                        type=GitIssueType.DIVERGED,
                        severity=IssueSeverity.ERROR,
                        message=(
                            f"Branch has diverged from remote "
                            f"(ahead by {sync_status.ahead_by}, "
                            f"behind by {sync_status.behind_by})"
                        ),
                        can_auto_fix=False,
                    ))
                elif sync_status.behind_by > 0:
                    issues.append(GitIssue(
                        type=GitIssueType.BEHIND_REMOTE,
                        severity=self._get_severity_for_issue(GitIssueType.BEHIND_REMOTE),
                        message=f"Local branch is behind remote by {sync_status.behind_by} commit(s)",
                        can_auto_fix=True,
                        fix_command="git pull --ff-only",
                    ))
                elif sync_status.ahead_by > 0:
                    warnings.append(
                        f"Local branch is ahead of remote by {sync_status.ahead_by} commit(s)"
                    )

                if not sync_status.has_upstream:
                    issues.append(GitIssue(
                        type=GitIssueType.NO_UPSTREAM,
                        severity=IssueSeverity.WARNING,
                        message="Branch has no upstream tracking configured",
                        can_auto_fix=False,
                    ))

        # Determine if validation passed based on level
        passed = self._check_passed(issues)

        return ValidationResult(
            passed=passed,
            issues=issues,
            warnings=warnings,
            current_branch=current_branch,
            is_clean=is_clean,
        )

    def validate_clean_tree(self) -> bool:
        """
        Verify no uncommitted changes exist.

        Returns:
            True if working tree is clean (no staged or unstaged changes)
        """
        try:
            # Check for any changes (staged or unstaged)
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0 and not result.stdout.strip()
        except Exception as e:
            logger.error(f"Failed to check clean tree: {e}")
            return False

    def validate_branch_state(self, expected: str) -> bool:
        """
        Verify currently on expected branch.

        Args:
            expected: Expected branch name

        Returns:
            True if on expected branch
        """
        current = self._get_current_branch()
        return current == expected

    def validate_remote_sync(self) -> SyncStatus:
        """
        Verify local is synced with remote.

        Fetches from remote and compares commit counts to determine
        synchronization status.

        Returns:
            SyncStatus with detailed sync information
        """
        # Fetch to get latest remote state
        try:
            subprocess.run(
                ["git", "fetch", "--quiet"],
                cwd=self.repo_root,
                capture_output=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            logger.warning("Git fetch timed out")
        except Exception as e:
            logger.warning(f"Git fetch failed: {e}")

        # Check if upstream is configured
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            has_upstream = result.returncode == 0
        except Exception:
            has_upstream = False

        if not has_upstream:
            return SyncStatus(
                is_synced=True,  # No upstream to compare
                has_upstream=False,
            )

        # Get ahead/behind counts
        try:
            result = subprocess.run(
                ["git", "rev-list", "--left-right", "--count", "@{upstream}...HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    behind_by = int(parts[0])
                    ahead_by = int(parts[1])
                    diverged = behind_by > 0 and ahead_by > 0
                    is_synced = behind_by == 0 and ahead_by == 0

                    return SyncStatus(
                        is_synced=is_synced,
                        ahead_by=ahead_by,
                        behind_by=behind_by,
                        diverged=diverged,
                        has_upstream=True,
                    )
        except Exception as e:
            logger.warning(f"Failed to get sync status: {e}")

        return SyncStatus(is_synced=True, has_upstream=has_upstream)

    # =========================================================================
    # ENFORCEMENT
    # =========================================================================

    def enforce_requirements(
        self,
        ticket: "HierarchicalTicket",
        auto_remediate: bool = True,
    ) -> EnforcementResult:
        """
        Run all requirement checks and enforce them.

        Validates git state and optionally attempts auto-remediation
        of fixable issues.

        Args:
            ticket: The HierarchicalTicket to be executed
            auto_remediate: Whether to attempt auto-remediation of issues

        Returns:
            EnforcementResult with validation and remediation status
        """
        logger.info(f"Enforcing git requirements for task {ticket.id}")

        # Run validation
        validation = self.validate_preconditions()

        if validation.passed:
            return EnforcementResult(
                validation=validation,
                can_proceed=True,
            )

        # If validation failed, try remediation if enabled
        if auto_remediate:
            fixable_issues = [i for i in validation.issues if i.can_auto_fix]

            if fixable_issues:
                logger.info(
                    f"Attempting to auto-remediate {len(fixable_issues)} issue(s)"
                )
                remediation = self.auto_remediate(fixable_issues)

                # Re-validate after remediation
                final_validation = self.validate_preconditions()

                return EnforcementResult(
                    validation=validation,
                    remediation_attempted=True,
                    remediation_success=remediation.success,
                    can_proceed=final_validation.passed,
                    stashed_changes=remediation.stash_ref is not None,
                    final_issues=final_validation.issues,
                )

        return EnforcementResult(
            validation=validation,
            can_proceed=False,
            final_issues=validation.issues,
        )

    def auto_remediate(self, issues: List[GitIssue]) -> RemediationResult:
        """
        Attempt to auto-fix git issues.

        Supports remediation of:
        - DIRTY_TREE: Stash changes
        - BEHIND_REMOTE: Pull with fast-forward

        Args:
            issues: List of issues to attempt to fix

        Returns:
            RemediationResult with details of what was fixed
        """
        fixed: List[GitIssue] = []
        unfixed: List[GitIssue] = []
        actions: List[str] = []
        stash_ref: Optional[str] = None

        for issue in issues:
            if not issue.can_auto_fix:
                unfixed.append(issue)
                continue

            try:
                if issue.type == GitIssueType.DIRTY_TREE:
                    stash_ref = self._stash_changes()
                    if stash_ref:
                        fixed.append(issue)
                        actions.append(f"Stashed changes: {stash_ref}")
                    else:
                        unfixed.append(issue)

                elif issue.type == GitIssueType.BEHIND_REMOTE:
                    if self._pull_fast_forward():
                        fixed.append(issue)
                        actions.append("Pulled from remote (fast-forward)")
                    else:
                        unfixed.append(issue)

                else:
                    unfixed.append(issue)

            except Exception as e:
                logger.error(f"Failed to remediate {issue.type.value}: {e}")
                unfixed.append(issue)

        success = len(unfixed) == 0 or not any(
            i.severity in (IssueSeverity.ERROR, IssueSeverity.CRITICAL)
            for i in unfixed
        )

        return RemediationResult(
            success=success,
            fixed_issues=fixed,
            unfixed_issues=unfixed,
            stash_ref=stash_ref,
            actions_taken=actions,
        )

    # =========================================================================
    # STASH MANAGEMENT
    # =========================================================================

    def _stash_changes(self) -> Optional[str]:
        """
        Stash current changes.

        Returns:
            Stash reference if successful, None otherwise
        """
        try:
            # Check if there's anything to stash
            if self.validate_clean_tree():
                return None

            # Create stash
            message = f"{DEFAULT_STASH_MESSAGE_PREFIX}-{self._get_timestamp()}"
            result = self._run_git(
                ["stash", "push", "-m", message],
                "Failed to stash changes",
            )

            # Verify stash was created
            stash_list = self._run_git(
                ["stash", "list"],
                "Failed to list stashes",
                capture_output=True,
            )

            if message in stash_list.stdout:
                logger.info(f"Stashed changes with message: {message}")
                return message

            return None

        except Exception as e:
            logger.error(f"Failed to stash changes: {e}")
            return None

    def restore_stash(self, stash_ref: str) -> bool:
        """
        Restore previously stashed changes.

        Args:
            stash_ref: Stash reference or message to restore

        Returns:
            True if stash was successfully restored
        """
        try:
            # Find the stash by message
            stash_list = self._run_git(
                ["stash", "list"],
                "Failed to list stashes",
                capture_output=True,
            )

            stash_index = None
            for line in stash_list.stdout.strip().split("\n"):
                if stash_ref in line:
                    # Extract stash index (e.g., "stash@{0}")
                    if "stash@{" in line:
                        start = line.index("stash@{")
                        end = line.index("}", start) + 1
                        stash_index = line[start:end]
                        break

            if stash_index:
                self._run_git(
                    ["stash", "pop", stash_index],
                    f"Failed to restore stash {stash_index}",
                )
                logger.info(f"Restored stash: {stash_ref}")
                return True

            logger.warning(f"Stash not found: {stash_ref}")
            return False

        except Exception as e:
            logger.error(f"Failed to restore stash: {e}")
            return False

    # =========================================================================
    # BRANCH OPERATIONS
    # =========================================================================

    def _pull_fast_forward(self) -> bool:
        """
        Pull from remote with fast-forward only.

        Returns:
            True if pull succeeded
        """
        try:
            self._run_git(
                ["pull", "--ff-only"],
                "Failed to pull from remote",
            )
            logger.info("Pulled from remote (fast-forward)")
            return True
        except Exception as e:
            logger.error(f"Failed to pull: {e}")
            return False

    def checkout_branch(self, branch: str) -> bool:
        """
        Checkout a specific branch.

        Args:
            branch: Branch name to checkout

        Returns:
            True if checkout succeeded
        """
        try:
            self._run_git(
                ["checkout", branch],
                f"Failed to checkout branch {branch}",
            )
            logger.info(f"Checked out branch: {branch}")
            return True
        except Exception as e:
            logger.error(f"Failed to checkout {branch}: {e}")
            return False

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

    def _get_current_branch(self) -> Optional[str]:
        """Get the current branch name."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                branch = result.stdout.strip()
                # HEAD means detached state
                if branch == "HEAD":
                    return None
                return branch
        except Exception:
            pass
        return None

    def _get_dirty_files(self) -> List[str]:
        """Get list of files with uncommitted changes."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                return [
                    line.strip()
                    for line in result.stdout.strip().split("\n")
                    if line.strip()
                ]
        except Exception:
            pass
        return []

    def _has_merge_conflicts(self) -> bool:
        """Check if there are unresolved merge conflicts."""
        try:
            result = subprocess.run(
                ["git", "ls-files", "--unmerged"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0 and bool(result.stdout.strip())
        except Exception:
            return False

    def _get_timestamp(self) -> str:
        """Get current timestamp for stash messages."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    # =========================================================================
    # SEVERITY HELPERS
    # =========================================================================

    def _get_severity_for_issue(self, issue_type: GitIssueType) -> IssueSeverity:
        """
        Get severity for an issue based on enforcement level.

        Args:
            issue_type: Type of the issue

        Returns:
            Appropriate severity based on current enforcement level
        """
        if self.level == RequirementLevel.STRICT:
            # In strict mode, most issues are errors
            severity_map = {
                GitIssueType.DIRTY_TREE: IssueSeverity.ERROR,
                GitIssueType.WRONG_BRANCH: IssueSeverity.ERROR,
                GitIssueType.BEHIND_REMOTE: IssueSeverity.ERROR,
                GitIssueType.AHEAD_OF_REMOTE: IssueSeverity.WARNING,
                GitIssueType.MERGE_CONFLICTS: IssueSeverity.CRITICAL,
                GitIssueType.HOOKS_MISSING: IssueSeverity.WARNING,
                GitIssueType.DIVERGED: IssueSeverity.ERROR,
                GitIssueType.NO_UPSTREAM: IssueSeverity.INFO,
                GitIssueType.DETACHED_HEAD: IssueSeverity.ERROR,
            }
        elif self.level == RequirementLevel.STANDARD:
            # Standard mode is more lenient
            severity_map = {
                GitIssueType.DIRTY_TREE: IssueSeverity.WARNING,
                GitIssueType.WRONG_BRANCH: IssueSeverity.ERROR,
                GitIssueType.BEHIND_REMOTE: IssueSeverity.WARNING,
                GitIssueType.AHEAD_OF_REMOTE: IssueSeverity.INFO,
                GitIssueType.MERGE_CONFLICTS: IssueSeverity.CRITICAL,
                GitIssueType.HOOKS_MISSING: IssueSeverity.INFO,
                GitIssueType.DIVERGED: IssueSeverity.ERROR,
                GitIssueType.NO_UPSTREAM: IssueSeverity.INFO,
                GitIssueType.DETACHED_HEAD: IssueSeverity.WARNING,
            }
        else:  # RELAXED
            # Relaxed mode treats most as warnings/info
            severity_map = {
                GitIssueType.DIRTY_TREE: IssueSeverity.INFO,
                GitIssueType.WRONG_BRANCH: IssueSeverity.WARNING,
                GitIssueType.BEHIND_REMOTE: IssueSeverity.INFO,
                GitIssueType.AHEAD_OF_REMOTE: IssueSeverity.INFO,
                GitIssueType.MERGE_CONFLICTS: IssueSeverity.ERROR,
                GitIssueType.HOOKS_MISSING: IssueSeverity.INFO,
                GitIssueType.DIVERGED: IssueSeverity.WARNING,
                GitIssueType.NO_UPSTREAM: IssueSeverity.INFO,
                GitIssueType.DETACHED_HEAD: IssueSeverity.INFO,
            }

        return severity_map.get(issue_type, IssueSeverity.WARNING)

    def _check_passed(self, issues: List[GitIssue]) -> bool:
        """
        Check if validation should pass based on issues and level.

        Args:
            issues: List of detected issues

        Returns:
            True if validation should pass
        """
        if self.level == RequirementLevel.RELAXED:
            # Relaxed only fails on critical issues
            return not any(
                i.severity == IssueSeverity.CRITICAL for i in issues
            )
        elif self.level == RequirementLevel.STANDARD:
            # Standard fails on error or critical
            return not any(
                i.severity in (IssueSeverity.ERROR, IssueSeverity.CRITICAL)
                for i in issues
            )
        else:  # STRICT
            # Strict fails on any issue that's warning or above
            return not any(
                i.severity in (
                    IssueSeverity.WARNING,
                    IssueSeverity.ERROR,
                    IssueSeverity.CRITICAL,
                )
                for i in issues
            )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def validate_git_preconditions(
    repo_root: Optional[Path] = None,
    level: RequirementLevel = RequirementLevel.STANDARD,
) -> ValidationResult:
    """
    Convenience function to validate git preconditions.

    Args:
        repo_root: Path to git repository (defaults to cwd)
        level: Enforcement strictness level

    Returns:
        ValidationResult with all detected issues
    """
    if repo_root is None:
        repo_root = Path.cwd()

    # Create a minimal config for the enforcer
    from vibey.services.implementation.config import ImplementConfig
    config = ImplementConfig()

    enforcer = GitRequirementsEnforcer(config, repo_root, level)
    return enforcer.validate_preconditions()


def is_git_clean(repo_root: Optional[Path] = None) -> bool:
    """
    Quick check if git working tree is clean.

    Args:
        repo_root: Path to git repository (defaults to cwd)

    Returns:
        True if working tree has no uncommitted changes
    """
    if repo_root is None:
        repo_root = Path.cwd()

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0 and not result.stdout.strip()
    except Exception:
        return False


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Main class
    "GitRequirementsEnforcer",
    # Enums
    "RequirementLevel",
    "GitIssueType",
    "IssueSeverity",
    # Data models
    "GitIssue",
    "SyncStatus",
    "ValidationResult",
    "RemediationResult",
    "EnforcementResult",
    # Exceptions
    "GitRequirementsError",
    "NotAGitRepositoryError",
    "GitOperationError",
    # Constants
    "DEFAULT_STASH_MESSAGE_PREFIX",
    "DEFAULT_MAIN_BRANCHES",
    # Convenience functions
    "validate_git_preconditions",
    "is_git_clean",
]
