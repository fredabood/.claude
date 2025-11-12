"""
Validator registry for roadmap standards.

This module provides a registry of validators that can validate different
types of standards (commit_check, file_check, test_run, custom_script).
"""

from pathlib import Path
from typing import List, Dict, Optional

from ..validator_base import ValidatorBase, ValidationResult
from ..resolver import StandardsResolver, ResolvedStandard
from ...models import Standard

from .commit_check import CommitCheckValidator
from .custom_script import CustomScriptValidator
from .file_check import FileCheckValidator
from .test_run import TestRunValidator


class ValidatorRegistry:
    """
    Registry of validators for different standard types.

    The registry maintains a list of validators and routes validation
    requests to the appropriate validator based on the standard type.

    Example:
        registry = ValidatorRegistry()
        registry.register(CommitCheckValidator(root_dir))
        registry.register(FileCheckValidator(root_dir))

        # Validate a specific standard
        validator = registry.get_validator(standard)
        result = validator.validate(standard, item_id)

        # Validate all standards for an item
        results = registry.validate_all(standards, item_id)
    """

    def __init__(self):
        """Initialize empty validator registry."""
        self.validators: List[ValidatorBase] = []

    def register(self, validator: ValidatorBase):
        """
        Register a validator.

        Args:
            validator: Validator instance to register
        """
        self.validators.append(validator)

    def get_validator(self, standard: Standard) -> ValidatorBase:
        """
        Get the appropriate validator for a standard.

        Args:
            standard: Standard to get validator for

        Returns:
            ValidatorBase instance that can validate this standard

        Raises:
            ValueError: If no validator can validate this standard type
        """
        for validator in self.validators:
            if validator.can_validate(standard):
                return validator

        raise ValueError(
            f"No validator registered for standard type: {standard.type}. "
            f"Standard ID: {standard.id}"
        )

    def validate_all(
        self,
        standards: List[ResolvedStandard],
        item_id: str
    ) -> List[ValidationResult]:
        """
        Validate all standards for an item.

        Args:
            standards: List of resolved standards to validate
            item_id: ID of item being validated

        Returns:
            List of ValidationResult objects (one per standard)
        """
        results = []

        for resolved_standard in standards:
            standard = resolved_standard.standard

            # Skip overridden standards
            if resolved_standard.is_overridden:
                # Create a skipped result for overridden standards
                from ..validator_base import ValidationStatus
                result = ValidationResult(
                    standard_id=standard.id,
                    status=ValidationStatus.SKIPPED,
                    message=f"Standard overridden: {resolved_standard.override_reason}",
                    metadata={
                        "overridden": True,
                        "override_reason": resolved_standard.override_reason,
                        "item_id": item_id
                    }
                )
                results.append(result)
                continue

            # Get appropriate validator
            try:
                validator = self.get_validator(standard)
            except ValueError as e:
                # No validator found - create error result
                from ..validator_base import ValidationStatus, ValidationIssue
                result = ValidationResult(
                    standard_id=standard.id,
                    status=ValidationStatus.ERROR,
                    message=str(e),
                    issues=[
                        ValidationIssue(
                            severity="error",
                            message=str(e),
                            details={"standard_type": standard.type}
                        )
                    ]
                )
                results.append(result)
                continue

            # Validate the standard
            result = validator.validate(standard, item_id)
            results.append(result)

        return results


def create_default_registry(root_dir: str) -> ValidatorRegistry:
    """
    Create a validator registry with all available validators pre-registered.

    Args:
        root_dir: Root directory containing .vibey/

    Returns:
        ValidatorRegistry with all validators registered
    """
    registry = ValidatorRegistry()

    # Register all validators
    registry.register(CommitCheckValidator(root_dir))
    registry.register(CustomScriptValidator(root_dir))
    registry.register(FileCheckValidator(root_dir))
    registry.register(TestRunValidator(root_dir))

    return registry


def validate_standards(item_id: str, root_dir: str) -> List[ValidationResult]:
    """
    Validate all standards that apply to a roadmap item.

    This is a convenience function that:
    1. Resolves which standards apply to the item
    2. Creates a validator registry
    3. Validates each standard
    4. Returns all results

    Args:
        item_id: ID of item to validate (task/sprint/track)
        root_dir: Root directory containing .vibey/

    Returns:
        List of ValidationResult objects

    Example:
        # Validate all standards for a task
        results = validate_standards("backend-1-task-001", "/path/to/project")

        # Check if all standards passed
        all_passed = all(r.is_passed() for r in results)

        # Get failed standards
        failed = [r for r in results if r.is_failed()]
    """
    # Resolve standards for item
    resolver = StandardsResolver(Path(root_dir))

    # Determine item type and resolve standards
    if '-task-' in item_id:
        resolved_standards = resolver.resolve_for_task(item_id)
    elif item_id.count('-') >= 1:
        # Sprint format: "track-N"
        resolved_standards = resolver.resolve_for_sprint(item_id)
    else:
        # Track format: "track-name"
        resolved_standards = resolver.resolve_for_track(item_id)

    # Create validator registry
    registry = create_default_registry(root_dir)

    # Validate all standards
    results = registry.validate_all(resolved_standards, item_id)

    return results


__all__ = [
    "ValidatorRegistry",
    "validate_standards",
    "create_default_registry",
    "CommitCheckValidator",
    "CustomScriptValidator",
    "FileCheckValidator",
    "TestRunValidator",
]
