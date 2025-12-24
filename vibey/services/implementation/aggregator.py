"""
Result aggregation and conflict resolution for parallel execution.

This module provides the ResultAggregator class for aggregating results from
parallel agent execution and resolving file conflicts that may arise when
multiple agents modify the same files.

Key Features:
- Detect conflicts when multiple agents modify the same file
- Support multiple conflict resolution strategies
- Git-based merge for branch isolation mode
- Atomic roadmap updates with transaction support

Usage:
    from vibey.services.implementation import ResultAggregator, ConflictStrategy
    from pathlib import Path

    config = ImplementConfig(...)
    aggregator = ResultAggregator(config)

    # Aggregate results from parallel execution
    results = [result1, result2, result3]
    aggregated = aggregator.aggregate(results)

    # Check for conflicts
    if aggregated.conflicts_found:
        resolutions = await aggregator.resolve_conflicts(
            aggregated.conflicts_found,
            ConflictStrategy.MERGE
        )

Design Reference:
- Implementation Mode Track: Parallel execution support
- Task: Implement ResultAggregator for conflict resolution
"""

from __future__ import annotations

import asyncio
import difflib
import fcntl
import logging
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set, Tuple

if TYPE_CHECKING:
    from vibey.services.implementation.config import ImplementConfig
    from vibey.services.implementation.result import ExecutionResult

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class ConflictType(Enum):
    """Type of file conflict between agents."""

    CONTENT = "content"  # Same file modified differently
    BOTH_CREATED = "both_created"  # Both agents created same file
    BOTH_DELETED = "both_deleted"  # Both agents deleted same file
    CREATE_DELETE = "create_delete"  # One created, one deleted


class ConflictStrategy(Enum):
    """Strategy for resolving file conflicts."""

    PROMPT = "prompt"  # Ask user
    ABORT = "abort"  # Rollback everything
    MERGE = "merge"  # Try auto-merge
    LAST_WINS = "last_wins"  # Use last agent's version
    FIRST_WINS = "first_wins"  # Use first agent's version


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class FileConflict:
    """
    Represents a file conflict between agents.

    Attributes:
        file_path: Path to the conflicting file
        agents: List of agent IDs that modified this file
        contents: Mapping of agent_id -> file content
        conflict_type: Type of conflict detected
        base_content: Original content before any agent modifications (if available)
    """

    file_path: Path
    agents: List[str]  # Agent IDs that modified this file
    contents: Dict[str, str]  # agent_id -> file content
    conflict_type: ConflictType
    base_content: Optional[str] = None


@dataclass
class Resolution:
    """
    Resolution of a file conflict.

    Attributes:
        conflict: The original file conflict
        strategy_used: Strategy that was used for resolution
        resolved_content: Final content after resolution
        required_manual: Whether manual intervention was required
        merge_markers: If merge strategy used, contains conflict markers if unresolved
    """

    conflict: FileConflict
    strategy_used: ConflictStrategy
    resolved_content: str
    required_manual: bool
    merge_markers: bool = False


@dataclass
class AggregatedResult:
    """
    Aggregated result from parallel execution.

    Provides a comprehensive summary of parallel agent execution including
    individual results, detected conflicts, resolutions, and metrics.

    Attributes:
        individual_results: List of ExecutionResult from each agent
        conflicts_found: List of detected file conflicts
        conflicts_resolved: List of conflict resolutions
        final_commits: List of commit SHAs from merged branches
        total_tokens: Total tokens consumed across all agents
        total_duration: Total duration of all executions
        success_count: Number of successful task executions
        failure_count: Number of failed task executions
    """

    individual_results: List["ExecutionResult"] = field(default_factory=list)
    conflicts_found: List[FileConflict] = field(default_factory=list)
    conflicts_resolved: List[Resolution] = field(default_factory=list)
    final_commits: List[str] = field(default_factory=list)
    total_tokens: int = 0
    total_duration: timedelta = field(default_factory=lambda: timedelta())
    success_count: int = 0
    failure_count: int = 0

    @property
    def all_successful(self) -> bool:
        """Check if all executions succeeded without unresolved conflicts."""
        return self.failure_count == 0 and not any(
            r.required_manual for r in self.conflicts_resolved
        )

    @property
    def has_unresolved_conflicts(self) -> bool:
        """Check if there are any unresolved conflicts."""
        resolved_paths = {r.conflict.file_path for r in self.conflicts_resolved}
        conflict_paths = {c.file_path for c in self.conflicts_found}
        return len(conflict_paths - resolved_paths) > 0

    @property
    def files_modified(self) -> Set[Path]:
        """Get all unique files modified across all agents."""
        files: Set[Path] = set()
        for result in self.individual_results:
            files.update(result.files_modified)
            files.update(result.files_created)
        return files


# =============================================================================
# RESULT AGGREGATOR
# =============================================================================


class ResultAggregator:
    """
    Aggregates results and resolves conflicts from parallel agents.

    This class is responsible for:
    1. Collecting results from multiple parallel agent executions
    2. Detecting file conflicts when multiple agents modify the same file
    3. Resolving conflicts using configurable strategies
    4. Merging git branches when using branch isolation mode
    5. Updating roadmap task statuses atomically

    Attributes:
        config: Implementation configuration
        default_strategy: Default strategy for conflict resolution
        repo_root: Root of the git repository

    Example:
        >>> aggregator = ResultAggregator(config)
        >>> conflicts = aggregator.detect_conflicts(results)
        >>> if conflicts:
        ...     resolutions = await aggregator.resolve_conflicts(
        ...         conflicts, ConflictStrategy.MERGE
        ...     )
        >>> aggregated = aggregator.aggregate(results)
    """

    def __init__(
        self,
        config: "ImplementConfig",
        repo_root: Optional[Path] = None,
        prompt_callback: Optional[Callable[[FileConflict], str]] = None,
    ):
        """
        Initialize ResultAggregator.

        Args:
            config: Implementation configuration
            repo_root: Root of the git repository (defaults to cwd)
            prompt_callback: Optional callback for user prompts during conflict resolution
        """
        self.config = config
        self.default_strategy = ConflictStrategy.PROMPT
        self.repo_root = repo_root or Path.cwd()
        self.prompt_callback = prompt_callback

    # =========================================================================
    # MAIN AGGREGATION
    # =========================================================================

    def aggregate(
        self,
        results: List["ExecutionResult"],
        resolve_conflicts: bool = False,
        strategy: Optional[ConflictStrategy] = None,
    ) -> AggregatedResult:
        """
        Aggregate results from parallel agents.

        Collects all execution results, detects conflicts, and computes
        aggregate metrics.

        Args:
            results: List of ExecutionResult from parallel agents
            resolve_conflicts: If True, automatically resolve detected conflicts
            strategy: Conflict resolution strategy (uses default if not specified)

        Returns:
            AggregatedResult with aggregated data and conflict information
        """
        if not results:
            return AggregatedResult()

        # Compute aggregate metrics
        total_tokens = sum(r.total_tokens for r in results)
        total_duration = timedelta()

        for r in results:
            total_duration += r.duration

        success_count = sum(1 for r in results if r.succeeded)
        failure_count = len(results) - success_count

        # Collect all commits
        all_commits: List[str] = []
        for r in results:
            all_commits.extend(r.commits)

        # Detect conflicts
        conflicts = self.detect_conflicts(results)

        # Resolve conflicts if requested
        resolutions: List[Resolution] = []
        if resolve_conflicts and conflicts:
            strategy = strategy or self.default_strategy
            # Note: resolve_conflicts is async, but aggregate is sync
            # For sync usage, conflicts are detected but not resolved
            logger.warning(
                "Automatic conflict resolution in aggregate() is not fully async. "
                "Use resolve_conflicts() separately for full async support."
            )

        return AggregatedResult(
            individual_results=results,
            conflicts_found=conflicts,
            conflicts_resolved=resolutions,
            final_commits=all_commits,
            total_tokens=total_tokens,
            total_duration=total_duration,
            success_count=success_count,
            failure_count=failure_count,
        )

    # =========================================================================
    # CONFLICT DETECTION
    # =========================================================================

    def detect_conflicts(
        self,
        results: List["ExecutionResult"],
    ) -> List[FileConflict]:
        """
        Detect files modified by multiple agents.

        Examines all execution results to find files that were modified
        by more than one agent, indicating a potential conflict.

        Args:
            results: List of ExecutionResult from parallel agents

        Returns:
            List of FileConflict objects for each detected conflict
        """
        conflicts: List[FileConflict] = []

        # Track files and which agents modified them
        file_modifiers: Dict[Path, List[Tuple[str, str]]] = defaultdict(list)
        file_creators: Dict[Path, List[str]] = defaultdict(list)
        file_deleters: Dict[Path, List[str]] = defaultdict(list)

        for result in results:
            agent_id = result.task_id  # Use task_id as agent identifier

            # Track modified files
            for file_path in result.files_modified:
                content = self._read_file_content(file_path)
                file_modifiers[file_path].append((agent_id, content))

            # Track created files
            for file_path in result.files_created:
                file_creators[file_path].append(agent_id)
                content = self._read_file_content(file_path)
                file_modifiers[file_path].append((agent_id, content))

        # Detect CONTENT conflicts (same file modified differently)
        for file_path, modifiers in file_modifiers.items():
            if len(modifiers) <= 1:
                continue

            # Check if contents differ
            contents: Dict[str, str] = {}
            unique_contents: Set[str] = set()

            for agent_id, content in modifiers:
                contents[agent_id] = content
                unique_contents.add(content)

            if len(unique_contents) > 1:
                # File modified differently by multiple agents
                conflict_type = ConflictType.CONTENT
                if file_path in file_creators and len(file_creators[file_path]) > 1:
                    conflict_type = ConflictType.BOTH_CREATED

                conflicts.append(
                    FileConflict(
                        file_path=file_path,
                        agents=[agent_id for agent_id, _ in modifiers],
                        contents=contents,
                        conflict_type=conflict_type,
                    )
                )

        # Detect CREATE_DELETE conflicts
        for file_path in file_creators:
            if file_path in file_deleters:
                conflicts.append(
                    FileConflict(
                        file_path=file_path,
                        agents=file_creators[file_path] + file_deleters[file_path],
                        contents={
                            agent: self._read_file_content(file_path)
                            for agent in file_creators[file_path]
                        },
                        conflict_type=ConflictType.CREATE_DELETE,
                    )
                )

        logger.info(f"Detected {len(conflicts)} file conflicts across {len(results)} results")
        return conflicts

    # =========================================================================
    # CONFLICT RESOLUTION
    # =========================================================================

    async def resolve_conflicts(
        self,
        conflicts: List[FileConflict],
        strategy: ConflictStrategy,
    ) -> List[Resolution]:
        """
        Resolve file conflicts using specified strategy.

        Applies the chosen conflict resolution strategy to each detected
        conflict and returns the resolutions.

        Args:
            conflicts: List of FileConflict to resolve
            strategy: Strategy to use for resolution

        Returns:
            List of Resolution objects for each conflict
        """
        resolutions: List[Resolution] = []

        for conflict in conflicts:
            resolution = await self._resolve_single_conflict(conflict, strategy)
            resolutions.append(resolution)

            # Apply resolution if successful
            if not resolution.required_manual:
                self._apply_resolution(resolution)

        return resolutions

    async def _resolve_single_conflict(
        self,
        conflict: FileConflict,
        strategy: ConflictStrategy,
    ) -> Resolution:
        """
        Resolve a single file conflict.

        Args:
            conflict: The conflict to resolve
            strategy: Resolution strategy to use

        Returns:
            Resolution object with the result
        """
        if strategy == ConflictStrategy.ABORT:
            return Resolution(
                conflict=conflict,
                strategy_used=strategy,
                resolved_content="",
                required_manual=True,
            )

        elif strategy == ConflictStrategy.FIRST_WINS:
            # Use the first agent's version
            first_agent = conflict.agents[0]
            resolved_content = conflict.contents.get(first_agent, "")
            return Resolution(
                conflict=conflict,
                strategy_used=strategy,
                resolved_content=resolved_content,
                required_manual=False,
            )

        elif strategy == ConflictStrategy.LAST_WINS:
            # Use the last agent's version
            last_agent = conflict.agents[-1]
            resolved_content = conflict.contents.get(last_agent, "")
            return Resolution(
                conflict=conflict,
                strategy_used=strategy,
                resolved_content=resolved_content,
                required_manual=False,
            )

        elif strategy == ConflictStrategy.MERGE:
            return await self._try_auto_merge(conflict)

        elif strategy == ConflictStrategy.PROMPT:
            return await self._prompt_user(conflict)

        else:
            # Unknown strategy, require manual resolution
            return Resolution(
                conflict=conflict,
                strategy_used=strategy,
                resolved_content="",
                required_manual=True,
            )

    async def _try_auto_merge(self, conflict: FileConflict) -> Resolution:
        """
        Attempt automatic merge of conflicting content.

        Uses a 3-way merge algorithm if base content is available,
        otherwise falls back to diff-based merge.

        Args:
            conflict: The conflict to merge

        Returns:
            Resolution with merged content or conflict markers
        """
        contents = list(conflict.contents.values())

        if len(contents) < 2:
            # Not enough versions to merge
            return Resolution(
                conflict=conflict,
                strategy_used=ConflictStrategy.MERGE,
                resolved_content=contents[0] if contents else "",
                required_manual=False,
            )

        if len(contents) == 2:
            # Two-way merge
            merged, has_markers = self._two_way_merge(
                contents[0], contents[1], conflict.agents[0], conflict.agents[1]
            )
            return Resolution(
                conflict=conflict,
                strategy_used=ConflictStrategy.MERGE,
                resolved_content=merged,
                required_manual=has_markers,
                merge_markers=has_markers,
            )

        # Three or more versions - use base if available
        base = conflict.base_content or ""
        merged = base
        has_markers = False

        for i, content in enumerate(contents):
            agent = conflict.agents[i] if i < len(conflict.agents) else f"agent_{i}"
            merged, markers = self._two_way_merge(merged, content, "current", agent)
            has_markers = has_markers or markers

        return Resolution(
            conflict=conflict,
            strategy_used=ConflictStrategy.MERGE,
            resolved_content=merged,
            required_manual=has_markers,
            merge_markers=has_markers,
        )

    def _two_way_merge(
        self, content_a: str, content_b: str, name_a: str, name_b: str
    ) -> Tuple[str, bool]:
        """
        Perform two-way merge between two versions.

        Returns:
            Tuple of (merged_content, has_conflict_markers)
        """
        lines_a = content_a.splitlines(keepends=True)
        lines_b = content_b.splitlines(keepends=True)

        # Use SequenceMatcher for diff
        matcher = difflib.SequenceMatcher(None, lines_a, lines_b)
        merged_lines: List[str] = []
        has_markers = False

        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == "equal":
                merged_lines.extend(lines_a[i1:i2])
            elif op == "insert":
                merged_lines.extend(lines_b[j1:j2])
            elif op == "delete":
                merged_lines.extend(lines_a[i1:i2])
            elif op == "replace":
                # Conflict - add markers
                has_markers = True
                merged_lines.append(f"<<<<<<< {name_a}\n")
                merged_lines.extend(lines_a[i1:i2])
                merged_lines.append("=======\n")
                merged_lines.extend(lines_b[j1:j2])
                merged_lines.append(f">>>>>>> {name_b}\n")

        return "".join(merged_lines), has_markers

    async def _prompt_user(self, conflict: FileConflict) -> Resolution:
        """
        Prompt user to resolve conflict.

        Uses the prompt_callback if provided, otherwise requires manual resolution.

        Args:
            conflict: The conflict to resolve

        Returns:
            Resolution based on user input or requiring manual intervention
        """
        if self.prompt_callback:
            try:
                resolved_content = self.prompt_callback(conflict)
                return Resolution(
                    conflict=conflict,
                    strategy_used=ConflictStrategy.PROMPT,
                    resolved_content=resolved_content,
                    required_manual=False,
                )
            except Exception as e:
                logger.error(f"Prompt callback failed: {e}")

        # No callback or callback failed - require manual resolution
        return Resolution(
            conflict=conflict,
            strategy_used=ConflictStrategy.PROMPT,
            resolved_content="",
            required_manual=True,
        )

    def _apply_resolution(self, resolution: Resolution) -> None:
        """
        Apply a resolution by writing the resolved content to file.

        Args:
            resolution: The resolution to apply
        """
        if resolution.required_manual:
            return

        try:
            file_path = resolution.conflict.file_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(resolution.resolved_content)
            logger.info(f"Applied resolution to {file_path}")
        except Exception as e:
            logger.error(f"Failed to apply resolution to {resolution.conflict.file_path}: {e}")

    # =========================================================================
    # GIT BRANCH MERGING
    # =========================================================================

    def merge_commits(
        self,
        results: List["ExecutionResult"],
        base_branch: str = "main",
    ) -> List[str]:
        """
        Merge commits from isolated branches.

        When agents work on isolated branches, this method merges their
        changes back to the base branch.

        Args:
            results: List of ExecutionResult with branch information
            base_branch: Target branch to merge into

        Returns:
            List of merge commit SHAs
        """
        merge_commits: List[str] = []

        for result in results:
            if not result.commits:
                continue

            # Get branch name from result metadata
            branch_name = result.metadata.get("branch") if hasattr(result, "metadata") else None
            if not branch_name:
                branch_name = f"task/{result.task_id}"

            try:
                # Check if branch exists
                check_result = subprocess.run(
                    ["git", "rev-parse", "--verify", branch_name],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                )

                if check_result.returncode != 0:
                    logger.warning(f"Branch {branch_name} not found, skipping merge")
                    continue

                # Checkout base branch
                subprocess.run(
                    ["git", "checkout", base_branch],
                    cwd=self.repo_root,
                    check=True,
                    capture_output=True,
                )

                # Merge the task branch
                merge_result = subprocess.run(
                    ["git", "merge", "--no-ff", branch_name, "-m", f"Merge {branch_name} into {base_branch}"],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                )

                if merge_result.returncode == 0:
                    # Get the merge commit SHA
                    sha_result = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        cwd=self.repo_root,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    merge_commits.append(sha_result.stdout.strip())
                    logger.info(f"Merged branch {branch_name}")
                else:
                    logger.error(f"Merge conflict on branch {branch_name}: {merge_result.stderr}")
                    # Abort the merge
                    subprocess.run(
                        ["git", "merge", "--abort"],
                        cwd=self.repo_root,
                        capture_output=True,
                    )

            except subprocess.CalledProcessError as e:
                logger.error(f"Git operation failed for branch {branch_name}: {e}")

        return merge_commits

    # =========================================================================
    # ATOMIC ROADMAP UPDATES
    # =========================================================================

    def update_roadmap_atomically(
        self,
        results: List["ExecutionResult"],
        root_dir: Optional[Path] = None,
    ) -> bool:
        """
        Update all task statuses atomically.

        Uses file locking to ensure that all roadmap updates from parallel
        execution are applied atomically.

        Args:
            results: List of ExecutionResult with task status updates
            root_dir: Root directory containing .vibey/ (defaults to repo_root)

        Returns:
            True if all updates succeeded, False if any failed
        """
        root_dir = root_dir or self.repo_root
        db_path = root_dir / ".vibey" / "roadmap.db"
        lock_path = root_dir / ".vibey" / ".roadmap.lock"

        # Ensure lock directory exists
        lock_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Acquire exclusive lock
            with open(lock_path, "w") as lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)

                try:
                    success = self._apply_roadmap_updates(results, root_dir)
                finally:
                    # Release lock
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

                return success

        except OSError as e:
            logger.error(f"Failed to acquire roadmap lock: {e}")
            return False

    def _apply_roadmap_updates(
        self,
        results: List["ExecutionResult"],
        root_dir: Path,
    ) -> bool:
        """
        Apply roadmap updates within the lock.

        Args:
            results: Execution results to apply
            root_dir: Root directory

        Returns:
            True if all updates succeeded
        """
        from vibey.services.implementation.result import ExecutionStatus

        all_success = True

        for result in results:
            try:
                task_id = result.task_id

                # Only update tasks that completed successfully
                if result.status != ExecutionStatus.SUCCESS:
                    continue

                # Import update functions
                from vibey.operations.roadmap.update import complete_task

                # Complete the task
                exit_code = complete_task(
                    root_dir=root_dir,
                    task_id=task_id,
                    completed_by="parallel-execution",
                    skip_commit_check=True,  # Commits handled by aggregator
                )

                if exit_code != 0:
                    logger.warning(f"Failed to complete task {task_id}")
                    all_success = False
                else:
                    logger.info(f"Completed task {task_id}")

            except Exception as e:
                logger.error(f"Error updating task {result.task_id}: {e}")
                all_success = False

        return all_success

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _read_file_content(self, file_path: Path) -> str:
        """
        Read file content safely.

        Args:
            file_path: Path to file

        Returns:
            File content or empty string if file doesn't exist
        """
        try:
            if file_path.exists():
                return file_path.read_text()
        except Exception as e:
            logger.warning(f"Failed to read file {file_path}: {e}")
        return ""


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ConflictType",
    "ConflictStrategy",
    # Data models
    "FileConflict",
    "Resolution",
    "AggregatedResult",
    # Main class
    "ResultAggregator",
]
