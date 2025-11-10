"""
State validator utility for verifying repository state.

This module provides tools for validating that repositories are in
expected states after operations.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import yaml


@dataclass
class ValidationResult:
    """Result of a validation check."""

    passed: bool
    message: str
    errors: List[str]

    def __str__(self) -> str:
        status = "✓" if self.passed else "✗"
        return f"{status} {self.message}"


class StateValidator:
    """
    Validate repository state against expectations.

    This class provides methods to validate directory structure,
    file contents, YAML schemas, and overall repository state.
    """

    def validate_directory_structure(
        self, actual_path: Path, expected: Dict
    ) -> ValidationResult:
        """
        Validate directory structure matches expectations.

        Args:
            actual_path: Path to validate
            expected: Dictionary defining expected structure

        Returns:
            ValidationResult
        """
        errors = []

        # Check expected directories exist
        for dir_name in expected.get("directories", []):
            dir_path = actual_path / dir_name
            if not dir_path.exists():
                errors.append(f"Missing directory: {dir_name}")
            elif not dir_path.is_dir():
                errors.append(f"Not a directory: {dir_name}")

        # Check expected files exist
        for file_name in expected.get("files", []):
            file_path = actual_path / file_name
            if not file_path.exists():
                errors.append(f"Missing file: {file_name}")
            elif not file_path.is_file():
                errors.append(f"Not a file: {file_name}")

        passed = len(errors) == 0
        message = "Directory structure valid" if passed else f"Directory structure invalid: {len(errors)} errors"

        return ValidationResult(passed=passed, message=message, errors=errors)

    def validate_yaml_structure(
        self, yaml_file: Path, schema: Dict
    ) -> ValidationResult:
        """
        Validate YAML file against schema.

        Args:
            yaml_file: Path to YAML file
            schema: Dictionary defining expected schema

        Returns:
            ValidationResult
        """
        errors = []

        if not yaml_file.exists():
            return ValidationResult(
                passed=False,
                message="YAML file not found",
                errors=[f"File does not exist: {yaml_file}"]
            )

        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
        except Exception as e:
            return ValidationResult(
                passed=False,
                message="YAML parse error",
                errors=[str(e)]
            )

        # Check required keys
        for key in schema.get("required_keys", []):
            if key not in data:
                errors.append(f"Missing required key: {key}")

        # Check key types
        for key, expected_type in schema.get("key_types", {}).items():
            if key in data:
                actual_type = type(data[key]).__name__
                if actual_type != expected_type:
                    errors.append(f"Key '{key}' has type {actual_type}, expected {expected_type}")

        passed = len(errors) == 0
        message = "YAML structure valid" if passed else f"YAML structure invalid: {len(errors)} errors"

        return ValidationResult(passed=passed, message=message, errors=errors)

    def validate_git_state(
        self, repo_path: Path, expected: Dict
    ) -> ValidationResult:
        """
        Validate git repository state.

        Args:
            repo_path: Path to repository
            expected: Dictionary defining expected git state

        Returns:
            ValidationResult
        """
        import subprocess

        errors = []

        # Check .git exists
        if not (repo_path / ".git").exists():
            return ValidationResult(
                passed=False,
                message="Not a git repository",
                errors=["Missing .git directory"]
            )

        # Check branch
        if "branch" in expected:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            actual_branch = result.stdout.strip()
            expected_branch = expected["branch"]
            if actual_branch != expected_branch:
                errors.append(f"On branch '{actual_branch}', expected '{expected_branch}'")

        # Check for uncommitted changes
        if expected.get("clean", False):
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                errors.append("Repository has uncommitted changes")

        passed = len(errors) == 0
        message = "Git state valid" if passed else f"Git state invalid: {len(errors)} errors"

        return ValidationResult(passed=passed, message=message, errors=errors)

    def validate_file_content(
        self, file_path: Path, expected_content: Optional[str] = None,
        contains: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Validate file content.

        Args:
            file_path: Path to file
            expected_content: Exact content expected (optional)
            contains: List of strings that should be in content (optional)

        Returns:
            ValidationResult
        """
        errors = []

        if not file_path.exists():
            return ValidationResult(
                passed=False,
                message="File not found",
                errors=[f"File does not exist: {file_path}"]
            )

        content = file_path.read_text()

        if expected_content is not None:
            if content != expected_content:
                errors.append("File content does not match expected")

        if contains:
            for search_string in contains:
                if search_string not in content:
                    errors.append(f"File does not contain: {search_string}")

        passed = len(errors) == 0
        message = "File content valid" if passed else f"File content invalid: {len(errors)} errors"

        return ValidationResult(passed=passed, message=message, errors=errors)
