"""
Standards enforcement for roadmap operations.

Provides functions for validating standards during roadmap lifecycle operations
like task/sprint completion.
"""

from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime, timezone

from ...roadmap.standards import (
    StandardsResolver,
    ValidatorRegistry,
    create_default_registry,
    ValidationResult,
    ValidationStatus,
)
from ...roadmap.models import EnforcementMode


class EnforcementResult:
    """Result of enforcing standards on an item."""

    def __init__(
        self,
        can_proceed: bool,
        blocking_failures: List[ValidationResult],
        warnings: List[ValidationResult],
        passed: List[ValidationResult],
        skipped: List[ValidationResult],
    ):
        self.can_proceed = can_proceed
        self.blocking_failures = blocking_failures
        self.warnings = warnings
        self.passed = passed
        self.skipped = skipped

    @property
    def has_issues(self) -> bool:
        """Check if there are any failures or warnings."""
        return len(self.blocking_failures) > 0 or len(self.warnings) > 0

    @property
    def total_standards(self) -> int:
        """Get total number of standards checked."""
        return (
            len(self.blocking_failures) +
            len(self.warnings) +
            len(self.passed) +
            len(self.skipped)
        )


def enforce_standards(
    item_id: str,
    root_dir: Path,
    operation: str = "complete"
) -> EnforcementResult:
    """
    Enforce standards for a roadmap item.

    Validates all standards that apply to the item and categorizes results:
    - Blocking failures: BLOCKING standards that failed
    - Warnings: WARNING standards that failed (or AUDIT standards)
    - Passed: Standards that passed
    - Skipped: Standards that were skipped (overridden or disabled)

    Args:
        item_id: ID of item to validate (task/sprint/track)
        root_dir: Root directory containing .vibey/
        operation: Operation being performed (for context messages)

    Returns:
        EnforcementResult with validation results and proceed decision
    """
    # Resolve standards for this item
    try:
        resolver = StandardsResolver(root_dir)

        # Determine item type and resolve
        if '-task-' in item_id:
            resolved_standards = resolver.resolve_for_task(item_id)
        elif item_id.count('-') >= 1 and not '-task-' in item_id:
            # Sprint format: "track-N"
            resolved_standards = resolver.resolve_for_sprint(item_id)
        else:
            # Track format: "track-name"
            resolved_standards = resolver.resolve_for_track(item_id)

    except Exception as e:
        # If resolution fails, treat as blocking error
        print(f"❌ Standards resolution failed: {e}")
        return EnforcementResult(
            can_proceed=False,
            blocking_failures=[],
            warnings=[],
            passed=[],
            skipped=[],
        )

    # Create validator registry
    try:
        registry = create_default_registry(str(root_dir))
    except Exception as e:
        print(f"❌ Failed to create validator registry: {e}")
        return EnforcementResult(
            can_proceed=False,
            blocking_failures=[],
            warnings=[],
            passed=[],
            skipped=[],
        )

    # Validate all standards
    try:
        results = registry.validate_all(resolved_standards, item_id)
    except Exception as e:
        print(f"❌ Standards validation failed: {e}")
        return EnforcementResult(
            can_proceed=False,
            blocking_failures=[],
            warnings=[],
            passed=[],
            skipped=[],
        )

    # Categorize results by enforcement mode
    blocking_failures = []
    warnings = []
    passed = []
    skipped = []

    # Create a map of standard_id to enforcement mode
    enforcement_map = {
        rs.standard.id: rs.standard.enforcement
        for rs in resolved_standards
    }

    for result in results:
        enforcement = enforcement_map.get(result.standard_id, EnforcementMode.BLOCKING)

        if result.status == ValidationStatus.PASSED:
            passed.append(result)
        elif result.status == ValidationStatus.SKIPPED:
            skipped.append(result)
        elif result.status in (ValidationStatus.FAILED, ValidationStatus.ERROR):
            # Categorize based on enforcement mode
            if enforcement == EnforcementMode.BLOCKING:
                blocking_failures.append(result)
            else:  # WARNING or AUDIT
                warnings.append(result)
        elif result.status == ValidationStatus.WARNING:
            warnings.append(result)

    # Determine if can proceed (only blocking failures prevent proceeding)
    can_proceed = len(blocking_failures) == 0

    return EnforcementResult(
        can_proceed=can_proceed,
        blocking_failures=blocking_failures,
        warnings=warnings,
        passed=passed,
        skipped=skipped,
    )


def print_enforcement_results(
    result: EnforcementResult,
    item_id: str,
    verbose: bool = True
) -> None:
    """
    Print formatted enforcement results.

    Args:
        result: EnforcementResult to display
        item_id: ID of item being validated
        verbose: If True, show detailed results. If False, only show failures/warnings
    """
    if result.total_standards == 0:
        if verbose:
            print(f"ℹ️  No standards defined for {item_id}")
        return

    # Print summary header
    print(f"\n📋 Standards Validation for {item_id}:")
    print(f"   Total: {result.total_standards} | "
          f"✅ Passed: {len(result.passed)} | "
          f"⚠️  Warnings: {len(result.warnings)} | "
          f"❌ Failed: {len(result.blocking_failures)} | "
          f"⏭️  Skipped: {len(result.skipped)}")

    # Show blocking failures (always)
    if result.blocking_failures:
        print(f"\n❌ Blocking Failures ({len(result.blocking_failures)}):")
        for validation_result in result.blocking_failures:
            print(f"   • {validation_result.standard_id}: {validation_result.message}")
            if validation_result.issues:
                for issue in validation_result.issues:
                    print(f"     - [{issue.severity.upper()}] {issue.message}")

    # Show warnings (always)
    if result.warnings:
        print(f"\n⚠️  Warnings ({len(result.warnings)}):")
        for validation_result in result.warnings:
            print(f"   • {validation_result.standard_id}: {validation_result.message}")
            if validation_result.issues:
                for issue in validation_result.issues:
                    print(f"     - [{issue.severity.upper()}] {issue.message}")

    # Show passed (only in verbose mode)
    if verbose and result.passed:
        print(f"\n✅ Passed ({len(result.passed)}):")
        for validation_result in result.passed:
            print(f"   • {validation_result.standard_id}: {validation_result.message}")

    # Show skipped (only in verbose mode)
    if verbose and result.skipped:
        print(f"\n⏭️  Skipped ({len(result.skipped)}):")
        for validation_result in result.skipped:
            reason = validation_result.message
            print(f"   • {validation_result.standard_id}: {reason}")

    print()  # Blank line for separation


def get_failure_summary(result: EnforcementResult) -> str:
    """
    Get a concise summary of failures.

    Args:
        result: EnforcementResult to summarize

    Returns:
        Summary string (e.g., "2 standards failed, 1 warning")
    """
    parts = []

    if result.blocking_failures:
        count = len(result.blocking_failures)
        parts.append(f"{count} standard{'s' if count != 1 else ''} failed")

    if result.warnings:
        count = len(result.warnings)
        parts.append(f"{count} warning{'s' if count != 1 else ''}")

    if not parts:
        return "All standards passed"

    return ", ".join(parts)
