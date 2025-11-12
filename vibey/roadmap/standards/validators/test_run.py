"""
Test run validator for roadmap standards.

Executes test commands and validates coverage thresholds.
"""

import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from ..validator_base import ValidatorBase, ValidationResult, ValidationIssue, ValidationStatus
from ...models import Standard, StandardType


class TestRunValidator(ValidatorBase):
    """
    Validator that executes test commands and validates coverage.

    Configuration format in standard.validation:
    {
        "command": str,          # Test command to execute (e.g., "pytest --cov")
        "threshold": float,      # Minimum coverage percentage (0-100)
        "working_dir": str       # Optional working directory (relative to root_dir)
    }

    The validator executes the test command and parses the output for coverage
    information. It supports multiple coverage formats:
    - pytest-cov: "coverage: 85%", "TOTAL ... 85%"
    - Jest: "All files | 85.5"
    - Generic: "coverage: 85%", "Coverage: 85.5%"

    Example:
        Standard(
            id="test-coverage",
            type=StandardType.TEST_RUN,
            validation={
                "command": "pytest --cov --cov-report=term",
                "threshold": 80.0
            }
        )
    """

    # Coverage parsing patterns (order matters - more specific first)
    COVERAGE_PATTERNS = [
        # pytest-cov TOTAL line: "TOTAL                    142     18    87%"
        re.compile(r'TOTAL\s+\d+\s+\d+\s+(\d+(?:\.\d+)?)%'),
        # Generic coverage percentage: "coverage: 85%", "Coverage: 85.5%"
        re.compile(r'[Cc]overage[:\s]+(\d+(?:\.\d+)?)%'),
        # Jest: "All files | 85.5"
        re.compile(r'All files\s*\|\s*(\d+(?:\.\d+)?)'),
    ]

    def can_validate(self, standard: Standard) -> bool:
        """Check if this validator can validate the given standard."""
        return standard.type == StandardType.TEST_RUN

    def validate(self, standard: Standard, item_id: str) -> ValidationResult:
        """
        Execute test command and validate coverage threshold.

        Args:
            standard: Standard configuration
            item_id: ID of item being validated

        Returns:
            ValidationResult with pass/fail based on coverage threshold
        """
        # Get configuration
        command = standard.validation.get("command")
        if not command:
            return self._create_error_result(
                standard.id,
                "Test command not specified in validation config"
            )

        threshold = standard.validation.get("threshold", 0.0)
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 100:
            return self._create_error_result(
                standard.id,
                f"Invalid threshold: {threshold} (must be 0-100)"
            )

        # Determine working directory
        working_dir = standard.validation.get("working_dir")
        if working_dir:
            cwd = Path(self.root_dir) / working_dir
            if not cwd.exists():
                return self._create_error_result(
                    standard.id,
                    f"Working directory does not exist: {working_dir}"
                )
        else:
            cwd = Path(self.root_dir)

        # Execute test command
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(cwd)
            )
        except subprocess.TimeoutExpired:
            return self._create_error_result(
                standard.id,
                "Test execution timed out (5 minute limit)"
            )
        except Exception as e:
            return self._create_error_result(
                standard.id,
                f"Failed to execute test command: {e}",
                error=e
            )

        # Parse coverage from output
        coverage, pattern_used = self._parse_coverage(result.stdout, result.stderr)

        if coverage is None:
            # Could not parse coverage
            issues = [
                ValidationIssue(
                    severity="error",
                    message="Could not parse coverage from test output",
                    details={
                        "command": command,
                        "exit_code": result.returncode,
                        "stdout_preview": result.stdout[:500] if result.stdout else None,
                        "stderr_preview": result.stderr[:500] if result.stderr else None
                    }
                )
            ]
            return self._create_failed_result(
                standard.id,
                "Failed to parse coverage from test output",
                issues=issues,
                metadata={
                    "command": command,
                    "threshold": threshold,
                    "exit_code": result.returncode
                }
            )

        # Check if coverage meets threshold
        if coverage >= threshold:
            return self._create_passed_result(
                standard.id,
                f"Test coverage {coverage:.1f}% meets threshold {threshold:.1f}%",
                metadata={
                    "command": command,
                    "coverage": coverage,
                    "threshold": threshold,
                    "pattern_used": pattern_used,
                    "exit_code": result.returncode,
                    "item_id": item_id
                }
            )
        else:
            issues = [
                ValidationIssue(
                    severity="error",
                    message=f"Coverage {coverage:.1f}% below threshold {threshold:.1f}%",
                    details={
                        "coverage": coverage,
                        "threshold": threshold,
                        "deficit": threshold - coverage
                    }
                )
            ]
            return self._create_failed_result(
                standard.id,
                f"Test coverage insufficient: {coverage:.1f}% < {threshold:.1f}%",
                issues=issues,
                metadata={
                    "command": command,
                    "coverage": coverage,
                    "threshold": threshold,
                    "pattern_used": pattern_used,
                    "exit_code": result.returncode,
                    "item_id": item_id
                }
            )

    def _parse_coverage(self, stdout: str, stderr: str) -> Tuple[Optional[float], Optional[str]]:
        """
        Parse coverage percentage from test output.

        Tries multiple patterns to extract coverage from different test runners.

        Args:
            stdout: Standard output from test command
            stderr: Standard error from test command

        Returns:
            Tuple of (coverage_percentage, pattern_name) or (None, None) if not found
        """
        # Try parsing stdout first
        for pattern in self.COVERAGE_PATTERNS:
            match = pattern.search(stdout)
            if match:
                coverage = float(match.group(1))
                return coverage, pattern.pattern

        # Try stderr if stdout didn't match
        for pattern in self.COVERAGE_PATTERNS:
            match = pattern.search(stderr)
            if match:
                coverage = float(match.group(1))
                return coverage, pattern.pattern

        # No match found
        return None, None
