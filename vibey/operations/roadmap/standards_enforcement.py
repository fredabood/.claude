"""
Standards enforcement for roadmap operations.

Provides functions for validating standards during roadmap lifecycle operations
like task/sprint completion.

## Sprint 9: Inheritance Pattern Integration

Standards cascade through the hierarchy: roadmap → track → sprint → task
Lower-level standards override higher-level ones (most specific wins).

### Effective Standards Pattern

The `StandardsResolver` handles the full inheritance chain:
```python
# OLD - manual traversal (avoided)
def check_standards(task_id):
    task = load_task(task_id)
    sprint = load_sprint(task.sprint_id)
    track = load_track(sprint.track_id)
    roadmap = load_roadmap()
    violations = []
    violations.extend(check_against(task, roadmap.standards))
    violations.extend(check_against(task, track.standards))
    violations.extend(check_against(task, sprint.standards))
    return violations

# NEW - effective standards includes full chain
def check_standards(task_id):
    resolver = StandardsResolver(root_dir)
    resolved = resolver.resolve_for_task(task_id)  # Inherited chain
    return validate_all(resolved, task_id)
```

### Helper Functions

- `get_effective_standards(item_id)`: All standards with inheritance resolved
- `get_inherited_standards(item_id)`: Standards from ancestor levels only
- `get_local_standards(item_id)`: Standards defined at this level only
- `get_blocking_standards(item_id)`: Standards that block completion
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


def _is_ulid(item_id: str) -> bool:
    """Check if item_id is a ULID (26 alphanumeric chars starting with 01)."""
    return len(item_id) == 26 and item_id.isalnum() and item_id.startswith('01')


def _determine_item_type(item_id: str, root_dir: Path) -> str:
    """
    Determine item type from ID format or filesystem.

    For legacy IDs, uses pattern matching:
    - Contains '-task-' → task
    - Contains '-' but not '-task-' → sprint
    - Otherwise → track

    For ULIDs, checks filesystem to find which directory contains the file.

    Returns: "task", "sprint", or "track"
    """
    # Check if ULID format
    if _is_ulid(item_id):
        roadmap_root = root_dir / ".vibey" / "roadmap"
        # Check which directory contains this ULID
        if (roadmap_root / "tasks" / f"{item_id}.yaml").exists():
            return "task"
        elif (roadmap_root / "sprints" / f"{item_id}.yaml").exists():
            return "sprint"
        elif (roadmap_root / "tracks" / f"{item_id}.yaml").exists():
            return "track"
        # If file not found, try to infer from database or default to task
        # (most common case for ULID lookups)
        return "task"

    # Legacy pattern-based detection
    if '-task-' in item_id:
        return "task"
    elif item_id.count('-') >= 1:
        return "sprint"
    else:
        return "track"


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

        # Determine item type (handles both legacy slugs and ULIDs)
        item_type = _determine_item_type(item_id, root_dir)

        if item_type == "task":
            resolved_standards = resolver.resolve_for_task(item_id)
        elif item_type == "sprint":
            resolved_standards = resolver.resolve_for_sprint(item_id)
        else:
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


# ===========================================================================
# HELPER FUNCTIONS - Standards Inheritance (Sprint 9)
# ===========================================================================


def get_effective_standards(
    item_id: str,
    root_dir: Path,
) -> List["ResolvedStandard"]:
    """
    Get all effective standards for an item with inheritance resolved.

    Returns the full inheritance chain: roadmap → track → sprint standards,
    with more specific standards overriding less specific ones.

    Args:
        item_id: ID of task/sprint/track
        root_dir: Root directory containing .vibey/

    Returns:
        List of ResolvedStandard objects with inheritance applied
    """
    resolver = StandardsResolver(root_dir)

    # Determine item type (handles both legacy slugs and ULIDs)
    item_type = _determine_item_type(item_id, root_dir)

    if item_type == "task":
        return resolver.resolve_for_task(item_id)
    elif item_type == "sprint":
        return resolver.resolve_for_sprint(item_id)
    else:
        return resolver.resolve_for_track(item_id)


def get_inherited_standards(
    item_id: str,
    root_dir: Path,
) -> List["ResolvedStandard"]:
    """
    Get standards inherited from ancestor levels only.

    Excludes standards defined at the item's own level.

    Args:
        item_id: ID of task/sprint/track
        root_dir: Root directory containing .vibey/

    Returns:
        List of ResolvedStandard objects from ancestors only
    """
    all_standards = get_effective_standards(item_id, root_dir)

    # Determine the item's level (handles both legacy slugs and ULIDs)
    item_type = _determine_item_type(item_id, root_dir)

    if item_type == "task":
        # Tasks don't have standards, all are inherited
        return all_standards
    elif item_type == "sprint":
        # Filter out sprint-level standards
        return [s for s in all_standards if s.source_level != "sprint"]
    else:
        # Filter out track-level standards
        return [s for s in all_standards if s.source_level != "track"]


def get_local_standards(
    item_id: str,
    root_dir: Path,
) -> List["ResolvedStandard"]:
    """
    Get standards defined at this item's level only.

    Excludes inherited standards from ancestor levels.

    Args:
        item_id: ID of sprint/track (tasks don't have local standards)
        root_dir: Root directory containing .vibey/

    Returns:
        List of ResolvedStandard objects from this level only
    """
    all_standards = get_effective_standards(item_id, root_dir)

    # Determine the item's level (handles both legacy slugs and ULIDs)
    item_type = _determine_item_type(item_id, root_dir)

    if item_type == "task":
        return []  # Tasks don't have local standards
    elif item_type == "sprint":
        # Sprint-level standards only
        return [s for s in all_standards if s.source_level == "sprint"]
    else:
        # Track-level standards only
        return [s for s in all_standards if s.source_level == "track"]


def get_blocking_standards(
    item_id: str,
    root_dir: Path,
) -> List["ResolvedStandard"]:
    """
    Get all blocking standards that prevent completion.

    Returns standards with BLOCKING enforcement mode that are not overridden.

    Args:
        item_id: ID of task/sprint/track
        root_dir: Root directory containing .vibey/

    Returns:
        List of blocking ResolvedStandard objects
    """
    resolver = StandardsResolver(root_dir)
    return resolver.get_blocking_standards(item_id)


def is_blocked_by_standards(
    item_id: str,
    root_dir: Path,
) -> Tuple[bool, List[str]]:
    """
    Check if item is blocked from completion by standards.

    Args:
        item_id: ID of task/sprint/track
        root_dir: Root directory containing .vibey/

    Returns:
        Tuple of (is_blocked, list_of_blocking_standard_ids)
    """
    blocking = get_blocking_standards(item_id, root_dir)

    if not blocking:
        return False, []

    blocking_ids = [s.standard.id for s in blocking]
    return True, blocking_ids


# Import for type hints
from ...roadmap.standards import ResolvedStandard
