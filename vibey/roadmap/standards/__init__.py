"""
Standards system for roadmap quality policy enforcement.

This module provides the standards resolution engine that determines
which standards apply to any roadmap item through hierarchical inheritance,
plus validators that check if standards are satisfied.
"""

from .resolver import StandardsResolver, ResolvedStandard
from .validator_base import ValidatorBase, ValidationResult, ValidationIssue, ValidationStatus
from .validators import (
    ValidatorRegistry,
    validate_standards,
    create_default_registry,
    CommitCheckValidator,
    FileCheckValidator,
    TestRunValidator,
    CustomScriptValidator,
)

__all__ = [
    # Resolution
    "StandardsResolver",
    "ResolvedStandard",
    # Validation framework
    "ValidatorBase",
    "ValidationResult",
    "ValidationIssue",
    "ValidationStatus",
    # Validators
    "ValidatorRegistry",
    "validate_standards",
    "create_default_registry",
    "CommitCheckValidator",
    "FileCheckValidator",
    "TestRunValidator",
    "CustomScriptValidator",
]
