"""
Base classes for standard validators.

Validators check if standards are satisfied for roadmap items.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any

from ..models import Standard


class ValidationStatus(str, Enum):
    """Status of a validation check."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class ValidationIssue:
    """A specific issue found during validation."""

    severity: str  # "error", "warning", "info"
    message: str
    details: Optional[Dict[str, Any]] = None

    def __str__(self):
        return f"[{self.severity.upper()}] {self.message}"


@dataclass
class ValidationResult:
    """
    Result of validating a standard.

    Contains pass/fail status, issues found, and detailed information.
    """

    standard_id: str
    status: ValidationStatus
    message: str
    issues: List[ValidationIssue] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_passed(self) -> bool:
        """Check if validation passed."""
        return self.status == ValidationStatus.PASSED

    def is_failed(self) -> bool:
        """Check if validation failed."""
        return self.status == ValidationStatus.FAILED

    def is_warning(self) -> bool:
        """Check if validation returned warning."""
        return self.status == ValidationStatus.WARNING

    def has_errors(self) -> bool:
        """Check if validation had errors."""
        return any(issue.severity == "error" for issue in self.issues)

    def get_error_count(self) -> int:
        """Get count of error-level issues."""
        return sum(1 for issue in self.issues if issue.severity == "error")

    def get_warning_count(self) -> int:
        """Get count of warning-level issues."""
        return sum(1 for issue in self.issues if issue.severity == "warning")


class ValidatorBase(ABC):
    """
    Base class for all standard validators.

    Subclasses must implement validate() method.
    """

    def __init__(self, root_dir: str):
        """
        Initialize validator.

        Args:
            root_dir: Root directory containing .vibey/
        """
        self.root_dir = root_dir

    @abstractmethod
    def validate(self, standard: Standard, item_id: str) -> ValidationResult:
        """
        Validate a standard for a specific item.

        Args:
            standard: Standard to validate
            item_id: ID of item being validated (task/sprint/track)

        Returns:
            ValidationResult indicating pass/fail and issues
        """
        pass

    @abstractmethod
    def can_validate(self, standard: Standard) -> bool:
        """
        Check if this validator can validate the given standard.

        Args:
            standard: Standard to check

        Returns:
            True if this validator can validate this standard type
        """
        pass

    def _create_passed_result(
        self,
        standard_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Helper to create a passed result."""
        return ValidationResult(
            standard_id=standard_id,
            status=ValidationStatus.PASSED,
            message=message,
            metadata=metadata or {},
        )

    def _create_failed_result(
        self,
        standard_id: str,
        message: str,
        issues: Optional[List[ValidationIssue]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Helper to create a failed result."""
        return ValidationResult(
            standard_id=standard_id,
            status=ValidationStatus.FAILED,
            message=message,
            issues=issues or [],
            metadata=metadata or {},
        )

    def _create_error_result(
        self,
        standard_id: str,
        message: str,
        error: Optional[Exception] = None
    ) -> ValidationResult:
        """Helper to create an error result."""
        issues = []
        if error:
            issues.append(ValidationIssue(
                severity="error",
                message=str(error),
                details={"exception_type": type(error).__name__}
            ))

        return ValidationResult(
            standard_id=standard_id,
            status=ValidationStatus.ERROR,
            message=message,
            issues=issues,
        )
