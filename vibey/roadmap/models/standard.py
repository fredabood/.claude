"""
Standard data model for quality policy enforcement.

Standards are quality requirements that cascade down the roadmap hierarchy
(roadmap → track → sprint → task). They enforce organizational policies
like mandatory commits, documentation, test coverage, and multi-platform testing.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional


class StandardType(str, Enum):
    """Types of standards that can be enforced."""

    COMMIT_CHECK = "commit_check"  # Ensures tasks have git commits
    FILE_CHECK = "file_check"  # Ensures specific files are modified
    TEST_RUN = "test_run"  # Runs tests and checks results
    CUSTOM_SCRIPT = "custom_script"  # Runs custom validation script


class EnforcementMode(str, Enum):
    """How strictly a standard is enforced."""

    BLOCKING = "blocking"  # Prevents completion if standard fails
    WARNING = "warning"  # Shows warning but allows completion
    AUDIT = "audit"  # Logs violations but doesn't block


@dataclass
class StandardOverride:
    """
    Record of a standard being overridden for a specific object.

    When a standard fails but needs to be bypassed, an override can be
    created with a justification. This maintains audit trail while
    allowing flexibility.
    """

    overridden_at: datetime  # When override was created
    overridden_by: str  # Who created the override (email or username)
    reason: str  # Why this standard was overridden
    target_id: str  # ID of object this override applies to (task/sprint/track)
    expires_at: Optional[datetime] = None  # Optional expiration

    def __post_init__(self):
        """Validate override."""
        if not self.overridden_by or not self.overridden_by.strip():
            raise ValueError("overridden_by is required and cannot be empty")

        if not self.reason or not self.reason.strip():
            raise ValueError("Reason for override is required and cannot be empty")

        if not self.target_id or not self.target_id.strip():
            raise ValueError("target_id is required and cannot be empty")

        # Validate expiration is in the future
        if self.expires_at and self.expires_at <= self.overridden_at:
            raise ValueError("Expiration must be after override creation time")

    def is_expired(self) -> bool:
        """Check if this override has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


@dataclass
class Standard:
    """
    A quality standard that must be satisfied for completion.

    Standards cascade down the hierarchy:
    - Roadmap standards apply to all tracks/sprints/tasks
    - Track standards apply to that track's sprints/tasks
    - Sprint standards apply to that sprint's tasks

    Examples:
        # Commit required standard (blocking)
        Standard(
            id="commit-required",
            name="Commit Required",
            description="All tasks must have at least one git commit",
            type=StandardType.COMMIT_CHECK,
            enforcement=EnforcementMode.BLOCKING,
            validation={"min_commits": 1}
        )

        # Documentation review (warning)
        Standard(
            id="doc-review",
            name="Documentation Review",
            description="All tasks should update documentation",
            type=StandardType.FILE_CHECK,
            enforcement=EnforcementMode.WARNING,
            validation={"pattern": "**/*.md", "min_files": 1}
        )

        # Test coverage (blocking with threshold)
        Standard(
            id="test-coverage",
            name="Test Coverage Required",
            description="All code changes must include tests",
            type=StandardType.TEST_RUN,
            enforcement=EnforcementMode.BLOCKING,
            validation={
                "command": "pytest --cov",
                "threshold": 80,
                "min_test_files": 1
            }
        )
    """

    # Identity
    id: str  # Unique standard ID (e.g., "commit-required", "test-coverage")
    name: str  # Human-readable name
    description: str  # What this standard enforces

    # Classification
    type: StandardType  # Type of validation
    enforcement: EnforcementMode  # How strictly enforced

    # Validation configuration
    validation: Dict[str, Any]  # Validator-specific config

    # Status
    enabled: bool = True  # Can be temporarily disabled

    # Metadata
    created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Overrides (populated at runtime, not persisted in YAML)
    overrides: List[StandardOverride] = field(default_factory=list)

    def __post_init__(self):
        """Validate standard configuration."""
        # Validate ID format (kebab-case)
        if not self.id or not self.id.strip():
            raise ValueError("Standard ID is required and cannot be empty")

        if not all(c.isalnum() or c in ['-', '_'] for c in self.id):
            raise ValueError(f"Standard ID must be alphanumeric with hyphens/underscores: {self.id}")

        # Validate name
        if not self.name or not self.name.strip():
            raise ValueError("Standard name is required and cannot be empty")

        # Validate description
        if not self.description or not self.description.strip():
            raise ValueError("Standard description is required and cannot be empty")

        # Validate validation config is not empty
        if not self.validation:
            raise ValueError("Validation configuration is required and cannot be empty")

        # Type-specific validation
        self._validate_type_specific_config()

    def _validate_type_specific_config(self):
        """Validate type-specific validation configuration."""
        if self.type == StandardType.COMMIT_CHECK:
            # Must have min_commits
            if "min_commits" not in self.validation:
                raise ValueError("commit_check standard must specify 'min_commits'")

            min_commits = self.validation["min_commits"]
            if not isinstance(min_commits, int) or min_commits < 1:
                raise ValueError("min_commits must be a positive integer")

        elif self.type == StandardType.FILE_CHECK:
            # Must have pattern or paths
            if "pattern" not in self.validation and "paths" not in self.validation:
                raise ValueError("file_check standard must specify 'pattern' or 'paths'")

            # If min_files specified, must be positive
            if "min_files" in self.validation:
                min_files = self.validation["min_files"]
                if not isinstance(min_files, int) or min_files < 1:
                    raise ValueError("min_files must be a positive integer")

        elif self.type == StandardType.TEST_RUN:
            # Must have command
            if "command" not in self.validation:
                raise ValueError("test_run standard must specify 'command'")

            # If threshold specified, must be 0-100
            if "threshold" in self.validation:
                threshold = self.validation["threshold"]
                if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 100:
                    raise ValueError("threshold must be between 0 and 100")

        elif self.type == StandardType.CUSTOM_SCRIPT:
            # Must have script path
            if "script" not in self.validation:
                raise ValueError("custom_script standard must specify 'script'")

    def is_blocking(self) -> bool:
        """Check if this standard blocks completion."""
        return self.enforcement == EnforcementMode.BLOCKING

    def is_warning(self) -> bool:
        """Check if this standard shows warnings."""
        return self.enforcement == EnforcementMode.WARNING

    def is_audit_only(self) -> bool:
        """Check if this standard is audit-only."""
        return self.enforcement == EnforcementMode.AUDIT

    def is_active(self) -> bool:
        """Check if this standard is currently active."""
        return self.enabled

    def has_override_for(self, target_id: str) -> bool:
        """
        Check if there's a valid override for a specific target.

        Args:
            target_id: ID of task/sprint/track to check

        Returns:
            True if valid (non-expired) override exists
        """
        for override in self.overrides:
            if override.target_id == target_id and not override.is_expired():
                return True
        return False

    def add_override(
        self,
        target_id: str,
        reason: str,
        overridden_by: str,
        expires_at: Optional[datetime] = None
    ) -> StandardOverride:
        """
        Add an override for a specific target.

        Args:
            target_id: ID of task/sprint/track being overridden
            reason: Justification for override
            overridden_by: Who is creating the override
            expires_at: Optional expiration datetime

        Returns:
            The created StandardOverride
        """
        override = StandardOverride(
            overridden_at=datetime.now(timezone.utc),
            overridden_by=overridden_by,
            reason=reason,
            target_id=target_id,
            expires_at=expires_at
        )
        self.overrides.append(override)
        return override

    def get_active_overrides(self) -> List[StandardOverride]:
        """Get all non-expired overrides."""
        return [o for o in self.overrides if not o.is_expired()]

    def get_override_for(self, target_id: str) -> Optional[StandardOverride]:
        """
        Get the active override for a specific target.

        Args:
            target_id: ID of task/sprint/track

        Returns:
            StandardOverride if found and not expired, None otherwise
        """
        for override in self.overrides:
            if override.target_id == target_id and not override.is_expired():
                return override
        return None
