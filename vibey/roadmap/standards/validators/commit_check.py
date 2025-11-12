"""
CommitCheckValidator - Validates git commit requirements for tasks.

Ensures that tasks have the required minimum number of git commits before
they can be marked as completed.
"""

from pathlib import Path
from typing import Optional

from ..validator_base import ValidatorBase, ValidationResult, ValidationIssue, ValidationStatus
from ...models import Standard, StandardType
from ...serialization import load_tasks


class CommitCheckValidator(ValidatorBase):
    """
    Validator for commit_check standards.

    Validates that tasks have the required minimum number of git commits.

    Configuration (standard.validation):
        min_commits: int - Minimum number of commits required (default: 1)

    Example:
        standard = Standard(
            id="commit-required",
            name="Commit Required",
            description="All tasks must have at least one git commit",
            type=StandardType.COMMIT_CHECK,
            enforcement=EnforcementMode.BLOCKING,
            validation={"min_commits": 1}
        )
    """

    def can_validate(self, standard: Standard) -> bool:
        """
        Check if this validator can validate the given standard.

        Args:
            standard: Standard to check

        Returns:
            True if standard type is COMMIT_CHECK
        """
        return standard.type == StandardType.COMMIT_CHECK

    def validate(self, standard: Standard, item_id: str) -> ValidationResult:
        """
        Validate that a task has the required minimum number of commits.

        Args:
            standard: Standard to validate
            item_id: Task ID to validate

        Returns:
            ValidationResult with pass/fail status
        """
        # Extract configuration
        min_commits = standard.validation.get("min_commits", 1)

        # Extract sprint_id from task_id
        # Task IDs follow format: {sprint-id}-{task-slug}
        # We need to find the sprint directory to load tasks
        sprint_id = self._extract_sprint_id(item_id)
        if not sprint_id:
            return self._create_error_result(
                standard.id,
                f"Cannot extract sprint ID from task ID: {item_id}"
            )

        # Load tasks from filesystem
        try:
            tasks = self._load_tasks_for_sprint(sprint_id)
        except Exception as e:
            return self._create_error_result(
                standard.id,
                f"Failed to load tasks for sprint {sprint_id}",
                error=e
            )

        # Find the specific task
        task = None
        for t in tasks:
            if t.id == item_id:
                task = t
                break

        if not task:
            return self._create_error_result(
                standard.id,
                f"Task not found: {item_id}"
            )

        # Check number of commits
        commit_count = len(task.commits)

        if commit_count >= min_commits:
            return self._create_passed_result(
                standard.id,
                f"Task has {commit_count} commit(s) (required: {min_commits})",
                metadata={
                    "commit_count": commit_count,
                    "min_commits": min_commits,
                    "task_id": item_id
                }
            )
        else:
            issues = [
                ValidationIssue(
                    severity="error",
                    message=f"Task has only {commit_count} commit(s), but {min_commits} required",
                    details={
                        "commit_count": commit_count,
                        "min_commits": min_commits,
                        "missing_commits": min_commits - commit_count
                    }
                )
            ]

            return self._create_failed_result(
                standard.id,
                f"Task does not meet minimum commit requirement",
                issues=issues,
                metadata={
                    "commit_count": commit_count,
                    "min_commits": min_commits,
                    "task_id": item_id
                }
            )

    def _extract_sprint_id(self, task_id: str) -> Optional[str]:
        """
        Extract sprint ID from task ID.

        Task IDs follow format: {sprint-id}-task-{task-num}
        Sprint IDs follow format: {track-id}-{sprint-num} (e.g., "core-framework-1")

        We need to find where the sprint ID ends. Sprint IDs end with a number,
        and are followed by "-task-" in task IDs.

        Args:
            task_id: Task ID

        Returns:
            Sprint ID or None if extraction fails
        """
        parts = task_id.split('-')

        # Find the first numeric part (sprint number)
        # This should be before "-task-"
        sprint_number_idx = -1
        for i, part in enumerate(parts):
            if part.isdigit():
                sprint_number_idx = i
                break  # Take the FIRST numeric part, not the last

        if sprint_number_idx == -1:
            # No numeric part found
            return None

        # Sprint ID is everything up to and including the sprint number
        sprint_id = '-'.join(parts[:sprint_number_idx + 1])
        return sprint_id

    def _load_tasks_for_sprint(self, sprint_id: str):
        """
        Load tasks for a sprint from the filesystem.

        Args:
            sprint_id: Sprint ID

        Returns:
            List of Task objects

        Raises:
            FileNotFoundError: If sprint directory not found
            ValueError: If tasks cannot be loaded
        """
        from ....cli.roadmap_lib.filesystem import FileSystemManager

        # Create filesystem manager
        fs = FileSystemManager(Path(self.root_dir))

        # Get sprint directory (contains task subdirectories)
        sprint_dir = fs.get_tasks_path(sprint_id)

        if not sprint_dir.exists():
            raise FileNotFoundError(f"Sprint directory not found: {sprint_dir}")

        # Load tasks using serialization module
        tasks = load_tasks(sprint_dir)

        return tasks
