"""
File check validator for standards.

Validates that required files were modified in a task.
"""

from pathlib import Path
from fnmatch import fnmatch
from typing import List

from ..validator_base import ValidatorBase, ValidationResult, ValidationIssue
from ...models import Standard, StandardType
from ...serialization import load_tasks


class FileCheckValidator(ValidatorBase):
    """
    Validator for file_check standards.

    Checks if required files were modified as part of a task's deliverables.

    Configuration:
        - pattern: str - Glob pattern to match files (e.g., "**/*.md", "docs/*.py")
        - min_files: int - Minimum number of files that must match (default: 1)
        OR
        - paths: List[str] - Specific file paths that must be present

    Examples:
        # Check for any markdown file
        {"pattern": "**/*.md", "min_files": 1}

        # Check for specific files
        {"paths": ["README.md", "docs/API.md"]}

        # Check for multiple test files
        {"pattern": "tests/**/*.py", "min_files": 2}
    """

    def can_validate(self, standard: Standard) -> bool:
        """Check if this validator can validate the given standard."""
        return standard.type == StandardType.FILE_CHECK

    def validate(self, standard: Standard, item_id: str) -> ValidationResult:
        """
        Validate that required files were modified.

        Args:
            standard: Standard to validate
            item_id: Task ID to validate

        Returns:
            ValidationResult with pass/fail status
        """
        try:
            # Load the task
            task = self._load_task(item_id)
            if not task:
                return self._create_error_result(
                    standard.id,
                    f"Task not found: {item_id}"
                )

            # Get configuration
            config = standard.validation
            pattern = config.get("pattern")
            paths = config.get("paths", [])
            min_files = config.get("min_files", 1)

            # Collect all deliverable paths
            deliverable_paths = []
            for deliverable in task.deliverables:
                deliverable_paths.extend(deliverable.paths)

            # Determine validation mode
            if pattern:
                return self._validate_pattern(
                    standard.id,
                    pattern,
                    min_files,
                    deliverable_paths
                )
            elif paths:
                return self._validate_paths(
                    standard.id,
                    paths,
                    deliverable_paths
                )
            else:
                return self._create_error_result(
                    standard.id,
                    "Invalid configuration: must specify 'pattern' or 'paths'"
                )

        except Exception as e:
            return self._create_error_result(
                standard.id,
                f"Error validating file check: {str(e)}",
                error=e
            )

    def _load_task(self, task_id: str):
        """
        Load a task from the hierarchical directory structure.

        Args:
            task_id: Task ID (e.g., "core-framework-1-task-1")

        Returns:
            Task object or None if not found
        """
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        # Initialize filesystem manager
        fs = FileSystemManager(Path(self.root_dir))

        # Parse task ID to extract sprint and task components
        # Format: {sprint-id}-{task-slug}
        # Example: "core-framework-1-task-1"
        parts = task_id.split('-')
        if len(parts) < 4:
            return None

        # Try to find the task by reconstructing the path
        # This is a simplified approach - in production, you'd use DirectoryManager
        try:
            # Search for task in all sprints
            for sprint_id in fs.list_sprints():
                sprint_dir = fs.get_tasks_path(sprint_id)
                if sprint_dir.exists():
                    tasks = load_tasks(sprint_dir)
                    for task in tasks:
                        if task.id == task_id:
                            return task
        except Exception:
            pass

        return None

    def _validate_pattern(
        self,
        standard_id: str,
        pattern: str,
        min_files: int,
        deliverable_paths: List[str]
    ) -> ValidationResult:
        """
        Validate using glob pattern matching.

        Args:
            standard_id: Standard ID
            pattern: Glob pattern to match
            min_files: Minimum number of files that must match
            deliverable_paths: List of deliverable file paths

        Returns:
            ValidationResult
        """
        # Match files against pattern
        matched_files = []
        for path in deliverable_paths:
            if fnmatch(path, pattern):
                matched_files.append(path)

        # Check if threshold is met
        if len(matched_files) >= min_files:
            return self._create_passed_result(
                standard_id,
                f"Found {len(matched_files)} file(s) matching pattern '{pattern}' (required: {min_files})",
                metadata={
                    "pattern": pattern,
                    "min_files": min_files,
                    "matched_files": matched_files,
                    "match_count": len(matched_files)
                }
            )
        else:
            issues = [
                ValidationIssue(
                    severity="error",
                    message=f"Only {len(matched_files)} file(s) matching pattern '{pattern}', required: {min_files}",
                    details={
                        "pattern": pattern,
                        "min_files": min_files,
                        "matched_files": matched_files,
                        "match_count": len(matched_files)
                    }
                )
            ]
            return self._create_failed_result(
                standard_id,
                f"Insufficient files matching pattern '{pattern}'",
                issues=issues,
                metadata={
                    "pattern": pattern,
                    "min_files": min_files,
                    "matched_files": matched_files,
                    "match_count": len(matched_files)
                }
            )

    def _validate_paths(
        self,
        standard_id: str,
        required_paths: List[str],
        deliverable_paths: List[str]
    ) -> ValidationResult:
        """
        Validate using specific file paths.

        Args:
            standard_id: Standard ID
            required_paths: List of required file paths
            deliverable_paths: List of deliverable file paths

        Returns:
            ValidationResult
        """
        # Check which required paths are present
        missing_paths = []
        found_paths = []

        for required_path in required_paths:
            if required_path in deliverable_paths:
                found_paths.append(required_path)
            else:
                missing_paths.append(required_path)

        # Check if all required paths are present
        if not missing_paths:
            return self._create_passed_result(
                standard_id,
                f"All {len(required_paths)} required file(s) found",
                metadata={
                    "required_paths": required_paths,
                    "found_paths": found_paths,
                    "missing_paths": missing_paths
                }
            )
        else:
            issues = [
                ValidationIssue(
                    severity="error",
                    message=f"Missing required file: {path}",
                    details={"required_path": path}
                )
                for path in missing_paths
            ]
            return self._create_failed_result(
                standard_id,
                f"Missing {len(missing_paths)} required file(s)",
                issues=issues,
                metadata={
                    "required_paths": required_paths,
                    "found_paths": found_paths,
                    "missing_paths": missing_paths
                }
            )
