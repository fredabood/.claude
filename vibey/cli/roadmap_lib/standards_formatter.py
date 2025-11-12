"""
Standards formatting utilities for CLI display.

Provides functions to format and display standards compliance information
with color coding and progress indicators.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

# Import standards models
from vibey.roadmap.models import Standard, EnforcementMode
from vibey.roadmap.standards import StandardsResolver
from vibey.roadmap.standards.validators import ValidationStatus


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


def get_standards_for_item(root_dir: Path, item_id: str) -> List[Standard]:
    """
    Get all standards that apply to an item.

    Args:
        root_dir: Root directory containing .vibey/
        item_id: Task, sprint, or track ID

    Returns:
        List of resolved standards
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


def format_standards_summary(standards: List[Standard], compact: bool = False) -> str:
    """
    Format standards as a summary string.

    Args:
        standards: List of standards
        compact: If True, use compact single-line format

    Returns:
        Formatted string
    """
    if not standards:
        return "No standards"

    # Count by enforcement mode
    blocking = sum(1 for s in standards if s.enforcement == EnforcementMode.BLOCKING)
    warning = sum(1 for s in standards if s.enforcement == EnforcementMode.WARNING)
    audit = sum(1 for s in standards if s.enforcement == EnforcementMode.AUDIT)

    parts = []
    if blocking > 0:
        parts.append(f"🔴 {blocking} blocking")
    if warning > 0:
        parts.append(f"🟡 {warning} warning")
    if audit > 0:
        parts.append(f"🟢 {audit} audit")

    if compact:
        return f"{len(standards)} standards ({', '.join(parts)})"
    else:
        return f"{len(standards)} standards: {', '.join(parts)}"


def print_standards_list(standards: List[Standard], indent: str = ""):
    """
    Print a detailed list of standards.

    Args:
        standards: List of standards to display
        indent: Indentation string for each line
    """
    if not standards:
        print(f"{indent}No standards applied")
        return

    # Group by source level
    by_source = {
        'roadmap': [],
        'track': [],
        'sprint': [],
    }

    for standard in standards:
        # Heuristic: standards without parent info are assumed roadmap-level
        # This is simplified - in reality we'd track the source
        by_source['roadmap'].append(standard)

    for source in ['roadmap', 'track', 'sprint']:
        source_standards = by_source[source]
        if not source_standards:
            continue

        for standard in source_standards:
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
    indent: str = ""
):
    """
    Print standards section for an item.

    Args:
        root_dir: Root directory containing .vibey/
        item_id: Task, sprint, or track ID
        show_details: If True, show detailed standards list
        indent: Indentation string
    """
    standards = get_standards_for_item(root_dir, item_id)

    if not standards:
        print(f"{indent}📋 Standards: None")
        return

    summary = format_standards_summary(standards, compact=True)
    print(f"{indent}📋 Standards: {summary}")

    if show_details:
        print(f"{indent}   Standards Applied:")
        print_standards_list(standards, indent=f"{indent}   ")


def get_standards_compliance_data(
    root_dir: Path,
    item_id: str
) -> Dict[str, Any]:
    """
    Get standards compliance data for an item.

    Returns dict with:
    - total: Total standards
    - passed: Standards passed
    - failed: Standards failed
    - warnings: Standards with warnings
    - blocking_failures: Blocking failures
    - standards: List of standards with details

    Note: This is a simplified version - full validation requires
    running the validators which we don't do here for performance.
    This just returns the standards that apply.
    """
    standards = get_standards_for_item(root_dir, item_id)

    # Count by enforcement
    blocking = sum(1 for s in standards if s.enforcement == EnforcementMode.BLOCKING)
    warning = sum(1 for s in standards if s.enforcement == EnforcementMode.WARNING)
    audit = sum(1 for s in standards if s.enforcement == EnforcementMode.AUDIT)

    return {
        "total": len(standards),
        "blocking_count": blocking,
        "warning_count": warning,
        "audit_count": audit,
        "standards": [
            {
                "id": s.id,
                "name": s.name,
                "type": s.type.value,
                "enforcement": s.enforcement.value,
                "has_overrides": s.has_overrides(),
            }
            for s in standards
        ],
    }
