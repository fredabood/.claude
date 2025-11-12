"""
Validation module for roadmap objects.

Provides YAML schema validation, data validation, and platform validation.
"""

from .validator import (
    Validator,
    ValidationError,
    ValidationResult,
    validate_roadmap,
    validate_track,
    validate_sprint,
    validate_task,
)

from .platform import (
    PlatformValidationError,
    validate_commit_platform,
    add_commit_with_validation,
    get_deployed_platforms,
    get_primary_platform,
)

__all__ = [
    "Validator",
    "ValidationError",
    "ValidationResult",
    "validate_roadmap",
    "validate_track",
    "validate_sprint",
    "validate_task",
    "PlatformValidationError",
    "validate_commit_platform",
    "add_commit_with_validation",
    "get_deployed_platforms",
    "get_primary_platform",
]
