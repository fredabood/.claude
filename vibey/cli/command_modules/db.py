"""
Database commands.

Commands for initializing, rebuilding, querying, and validating the SQLite database.
"""

from pathlib import Path
from typing import Optional


def db_init_cmd(force: bool = False) -> int:
    """Initialize the SQLite database."""
    from vibey.cli.commands import db_init_cmd as impl
    return impl(force=force)


def db_rebuild_cmd(force: bool = False) -> int:
    """Rebuild the database from YAML files."""
    from vibey.cli.commands import db_rebuild_cmd as impl
    return impl(force=force)


def db_dump_cmd(force: bool = False, verbose: bool = False) -> int:
    """Dump database contents to YAML files."""
    from vibey.cli.commands import db_dump_cmd as impl
    return impl(force=force, verbose=verbose)


def db_status_cmd(verbose: bool = False) -> int:
    """Show database status."""
    from vibey.cli.commands import db_status_cmd as impl
    return impl(verbose=verbose)


def db_backup_cmd(output_path: Optional[str] = None) -> int:
    """Backup the database."""
    from vibey.cli.commands import db_backup_cmd as impl
    return impl(output_path=output_path)


def db_query_blocked_cmd(track_filter: Optional[str] = None, verbose: bool = False) -> int:
    """Query blocked tasks."""
    from vibey.cli.commands import db_query_blocked_cmd as impl
    return impl(track_filter=track_filter, verbose=verbose)


def db_query_progress_cmd(group_by: str = 'track') -> int:
    """Query progress by track or sprint."""
    from vibey.cli.commands import db_query_progress_cmd as impl
    return impl(group_by=group_by)


def db_query_deps_cmd(entity_id: str, direction: str = 'both') -> int:
    """Query entity dependencies."""
    from vibey.cli.commands import db_query_deps_cmd as impl
    return impl(entity_id=entity_id, direction=direction)


def db_query_stats_cmd() -> int:
    """Query database statistics."""
    from vibey.cli.commands import db_query_stats_cmd as impl
    return impl()


def db_validate_cmd(level: str = 'full', compare: bool = False, verbose: bool = False) -> int:
    """Validate database integrity."""
    from vibey.cli.commands import db_validate_cmd as impl
    return impl(level=level, compare=compare, verbose=verbose)


def db_config_cmd() -> int:
    """Show database configuration."""
    from vibey.cli.commands import db_config_cmd as impl
    return impl()
