"""
Standards formatting utilities for CLI display.

Provides functions to format and display standards compliance information
with color coding, progress indicators, and inheritance chain visualization.

Sprint 10: Updated to properly display inheritance information from
ResolvedStandard objects, showing source level and override status.
"""

from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# Import standards models
from vibey.roadmap.models import Standard, EnforcementMode
from vibey.roadmap.standards import StandardsResolver
from vibey.roadmap.standards.resolver import ResolvedStandard
from vibey.roadmap.standards.validator_base import ValidationStatus


def format_enforcement(enforcement: EnforcementMode) -> str:
    """Format enforcement mode with color emoji."""
    enforcement_map = {
        EnforcementMode.BLOCKING: "🔴 BLOCKING",
        EnforcementMode.WARNING: "🟡 WARNING",
        EnforcementMode.AUDIT: "🟢 AUDIT",
    }
    return enforcement_map.get(enforcement, f"❓ {enforcement.value}")


def format_validation_status(status: ValidationStatus) -> str:
    """Format validation status with emoji."""
    status_map = {
        ValidationStatus.PASSED: "✅",
        ValidationStatus.FAILED: "❌",
        ValidationStatus.SKIPPED: "⏭️",
        ValidationStatus.ERROR: "💥",
    }
    return status_map.get(status, "❓")


def get_standards_for_item(root_dir: Path, item_id: str) -> List[ResolvedStandard]:
    """
    Get all standards that apply to an item with inheritance information.

    Args:
        root_dir: Root directory containing .vibey/
        item_id: Task, sprint, or track ID

    Returns:
        List of ResolvedStandard objects with source_level, source_id,
        is_overridden, and override_reason populated.
    """
    try:
        resolver = StandardsResolver(root_dir)

        if '-task-' in item_id:
            return resolver.resolve_for_task(item_id)
        elif item_id.count('-') >= 1 and not '-task-' in item_id:
            return resolver.resolve_for_sprint(item_id)
        else:
            return resolver.resolve_for_track(item_id)
    except Exception:
        return []


def format_source_level(level: str) -> str:
    """Format source level with emoji and color."""
    level_map = {
        'roadmap': '🗺️  roadmap',
        'track': '🛤️  track',
        'sprint': '🏃 sprint',
    }
    return level_map.get(level, f'❓ {level}')


def format_standards_summary(
    standards: List[Union[Standard, ResolvedStandard]],
    compact: bool = False,
    show_inheritance: bool = False
) -> str:
    """
    Format standards as a summary string.

    Args:
        standards: List of Standard or ResolvedStandard objects
        compact: If True, use compact single-line format
        show_inheritance: If True, include inheritance source breakdown

    Returns:
        Formatted string
    """
    if not standards:
        return "No standards"

    # Extract the actual Standard from ResolvedStandard if needed
    def get_standard(s):
        return s.standard if isinstance(s, ResolvedStandard) else s

    # Count by enforcement mode
    blocking = sum(1 for s in standards if get_standard(s).enforcement == EnforcementMode.BLOCKING)
    warning = sum(1 for s in standards if get_standard(s).enforcement == EnforcementMode.WARNING)
    audit = sum(1 for s in standards if get_standard(s).enforcement == EnforcementMode.AUDIT)

    parts = []
    if blocking > 0:
        parts.append(f"🔴 {blocking} blocking")
    if warning > 0:
        parts.append(f"🟡 {warning} warning")
    if audit > 0:
        parts.append(f"🟢 {audit} audit")

    # Add inheritance breakdown if requested
    if show_inheritance and standards and isinstance(standards[0], ResolvedStandard):
        roadmap_count = sum(1 for s in standards if s.source_level == 'roadmap')
        track_count = sum(1 for s in standards if s.source_level == 'track')
        sprint_count = sum(1 for s in standards if s.source_level == 'sprint')
        overridden_count = sum(1 for s in standards if s.is_overridden)

        inherit_parts = []
        if roadmap_count > 0:
            inherit_parts.append(f"{roadmap_count} from roadmap")
        if track_count > 0:
            inherit_parts.append(f"{track_count} from track")
        if sprint_count > 0:
            inherit_parts.append(f"{sprint_count} from sprint")
        if overridden_count > 0:
            inherit_parts.append(f"{overridden_count} overridden")

        if inherit_parts:
            parts.append(f"[{', '.join(inherit_parts)}]")

    if compact:
        return f"{len(standards)} standards ({', '.join(parts)})"
    else:
        return f"{len(standards)} standards: {', '.join(parts)}"


def print_standards_list(
    standards: List[Union[Standard, ResolvedStandard]],
    indent: str = "",
    show_inheritance: bool = True
):
    """
    Print a detailed list of standards with inheritance information.

    Args:
        standards: List of Standard or ResolvedStandard objects to display
        indent: Indentation string for each line
        show_inheritance: If True, group by source level and show inheritance chain
    """
    if not standards:
        print(f"{indent}No standards applied")
        return

    # Check if we have ResolvedStandard objects with source info
    has_resolved = standards and isinstance(standards[0], ResolvedStandard)

    if has_resolved and show_inheritance:
        # Group by source level
        by_source = {
            'roadmap': [],
            'track': [],
            'sprint': [],
        }

        for resolved in standards:
            source = resolved.source_level if hasattr(resolved, 'source_level') else 'roadmap'
            by_source[source].append(resolved)

        # Print by source level with headers
        for source in ['roadmap', 'track', 'sprint']:
            source_standards = by_source[source]
            if not source_standards:
                continue

            # Print source header
            print(f"{indent}{format_source_level(source)} (inherited from {source}):")

            for resolved in source_standards:
                standard = resolved.standard
                enforcement_display = format_enforcement(standard.enforcement)

                # Build status indicators
                status_parts = []
                if resolved.is_overridden:
                    status_parts.append(f"⚠️ OVERRIDDEN: {resolved.override_reason or 'no reason given'}")

                print(f"{indent}  • {standard.id}: {standard.name}")
                print(f"{indent}    Type: {standard.type.value} | {enforcement_display}")
                print(f"{indent}    Source: {resolved.source_id}")

                if status_parts:
                    for status in status_parts:
                        print(f"{indent}    {status}")

                if standard.has_overrides():
                    override_count = len(standard.overrides)
                    print(f"{indent}    Item overrides defined: {override_count}")

            print()  # Blank line between sources
    else:
        # Fallback: no inheritance info available, print flat list
        for item in standards:
            standard = item.standard if isinstance(item, ResolvedStandard) else item
            enforcement_display = format_enforcement(standard.enforcement)
            print(f"{indent}• {standard.id}: {standard.name}")
            print(f"{indent}  Type: {standard.type.value} | {enforcement_display}")
            if standard.has_overrides():
                override_count = len(standard.overrides)
                print(f"{indent}  Overrides: {override_count}")


def format_standards_compliance(
    passed: int,
    total: int,
    blocking_failures: int = 0,
    warnings: int = 0
) -> str:
    """
    Format standards compliance as a progress string.

    Args:
        passed: Number of standards passed
        total: Total number of standards
        blocking_failures: Number of blocking failures
        warnings: Number of warnings

    Returns:
        Formatted compliance string with emoji
    """
    if total == 0:
        return "No standards"

    percent = int((passed / total) * 100)

    # Choose emoji based on compliance
    if blocking_failures > 0:
        emoji = "❌"
    elif warnings > 0:
        emoji = "⚠️"
    else:
        emoji = "✅"

    result = f"{emoji} {passed}/{total} standards passing ({percent}%)"

    if blocking_failures > 0:
        result += f" | 🔴 {blocking_failures} blocking failures"
    if warnings > 0:
        result += f" | 🟡 {warnings} warnings"

    return result


def print_standards_section(
    root_dir: Path,
    item_id: str,
    show_details: bool = False,
    show_inheritance: bool = True,
    indent: str = ""
):
    """
    Print standards section for an item with inheritance chain.

    Args:
        root_dir: Root directory containing .vibey/
        item_id: Task, sprint, or track ID
        show_details: If True, show detailed standards list
        show_inheritance: If True, show inheritance chain (default True)
        indent: Indentation string
    """
    standards = get_standards_for_item(root_dir, item_id)

    if not standards:
        print(f"{indent}📋 Standards: None")
        return

    # Show summary with inheritance breakdown
    summary = format_standards_summary(standards, compact=True, show_inheritance=show_inheritance)
    print(f"{indent}📋 Standards: {summary}")

    if show_details:
        print(f"{indent}   Standards Applied (by inheritance level):")
        print_standards_list(standards, indent=f"{indent}   ", show_inheritance=show_inheritance)


def get_standards_compliance_data(
    root_dir: Path,
    item_id: str
) -> Dict[str, Any]:
    """
    Get standards compliance data for an item with inheritance information.

    Returns dict with:
    - total: Total standards
    - blocking_count: Number of blocking standards
    - warning_count: Number of warning standards
    - audit_count: Number of audit standards
    - inheritance: Breakdown by source level
    - standards: List of standards with details and source info

    Note: This is a simplified version - full validation requires
    running the validators which we don't do here for performance.
    This just returns the standards that apply.
    """
    resolved_standards = get_standards_for_item(root_dir, item_id)

    # Helper to get actual Standard object
    def get_std(s):
        return s.standard if isinstance(s, ResolvedStandard) else s

    # Count by enforcement
    blocking = sum(1 for s in resolved_standards if get_std(s).enforcement == EnforcementMode.BLOCKING)
    warning = sum(1 for s in resolved_standards if get_std(s).enforcement == EnforcementMode.WARNING)
    audit = sum(1 for s in resolved_standards if get_std(s).enforcement == EnforcementMode.AUDIT)

    # Count by source level (inheritance)
    inheritance = {
        "roadmap": 0,
        "track": 0,
        "sprint": 0,
        "overridden": 0,
    }
    for s in resolved_standards:
        if isinstance(s, ResolvedStandard):
            inheritance[s.source_level] = inheritance.get(s.source_level, 0) + 1
            if s.is_overridden:
                inheritance["overridden"] += 1

    return {
        "total": len(resolved_standards),
        "blocking_count": blocking,
        "warning_count": warning,
        "audit_count": audit,
        "inheritance": inheritance,
        "standards": [
            {
                "id": get_std(s).id,
                "name": get_std(s).name,
                "type": get_std(s).type.value,
                "enforcement": get_std(s).enforcement.value,
                "has_overrides": get_std(s).has_overrides(),
                # Include inheritance info if available
                "source_level": s.source_level if isinstance(s, ResolvedStandard) else None,
                "source_id": s.source_id if isinstance(s, ResolvedStandard) else None,
                "is_overridden": s.is_overridden if isinstance(s, ResolvedStandard) else False,
                "override_reason": s.override_reason if isinstance(s, ResolvedStandard) else None,
            }
            for s in resolved_standards
        ],
    }
