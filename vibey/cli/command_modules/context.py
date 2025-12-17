"""
Context management commands.

Commands for managing context files - initialization, listing, showing,
archiving, cleaning, exporting, and searching.
"""

from pathlib import Path
from typing import Optional


def context_init_cmd() -> int:
    """Initialize context directory structure."""
    from vibey.cli.commands import context_init_cmd as impl
    return impl()


def context_list_cmd(
    context_type: Optional[str] = None,
    status: Optional[str] = None,
    verbose: bool = False,
) -> int:
    """List context files."""
    from vibey.cli.commands import context_list_cmd as impl
    return impl(context_type=context_type, status=status, verbose=verbose)


def context_show_cmd(
    context_id: str,
    context_type: Optional[str] = None,
) -> int:
    """Show context details."""
    from vibey.cli.commands import context_show_cmd as impl
    return impl(context_id=context_id, context_type=context_type)


def context_archive_cmd(context_id: str, context_type: str = None) -> int:
    """Archive a context file."""
    from vibey.cli.commands import context_archive_cmd as impl
    return impl(context_id, context_type=context_type)


def context_clean_cmd(
    context_type: Optional[str] = None,
    older_than_days: int = 30,
    dry_run: bool = True,
) -> int:
    """Clean old context files."""
    from vibey.cli.commands import context_clean_cmd as impl
    return impl(context_type=context_type, older_than_days=older_than_days, dry_run=dry_run)


def context_export_cmd(
    context_id: str,
    output: Optional[str] = None,
    format: str = "yaml",
) -> int:
    """Export context to file."""
    from vibey.cli.commands import context_export_cmd as impl
    return impl(context_id=context_id, output=output, format=format)


def context_search_cmd(
    query: str,
    context_type: Optional[str] = None,
    limit: int = 10,
) -> int:
    """Search context files."""
    from vibey.cli.commands import context_search_cmd as impl
    return impl(query=query, context_type=context_type, limit=limit)
