"""
Project discovery commands.

Commands for running project discovery scans, showing results, and tracking history.
"""

from pathlib import Path
from typing import Optional


def discover_run_cmd(
    scan_type: str = "full",
    output: Optional[str] = None,
    verbose: bool = False,
) -> int:
    """Run project discovery scan."""
    from vibey.cli.commands import discover_run_cmd as impl
    return impl(scan_type=scan_type, output=output, verbose=verbose)


def discover_show_cmd(
    discovery_id: Optional[str] = None,
    section: Optional[str] = None,
) -> int:
    """Show discovery results."""
    from vibey.cli.commands import discover_show_cmd as impl
    return impl(discovery_id=discovery_id, section=section)


def discover_status_cmd(max_age_hours: int = 24) -> int:
    """Show discovery status."""
    from vibey.cli.commands import discover_status_cmd as impl
    return impl(max_age_hours=max_age_hours)


def discover_history_cmd(limit: int = 10) -> int:
    """Show discovery history."""
    from vibey.cli.commands import discover_history_cmd as impl
    return impl(limit=limit)


def discover_diff_cmd(
    discovery_id1: Optional[str] = None,
    discovery_id2: Optional[str] = None,
) -> int:
    """Compare two discovery results."""
    from vibey.cli.commands import discover_diff_cmd as impl
    return impl(discovery_id1=discovery_id1, discovery_id2=discovery_id2)


def discover_refresh_cmd(force: bool = False) -> int:
    """Refresh discovery data."""
    from vibey.cli.commands import discover_refresh_cmd as impl
    return impl(force=force)
