"""
Migration commands.

Commands for migrating legacy sprint files, embedded tasks, and format versions.
"""

from pathlib import Path
from typing import Optional


def migrate_to_roadmap_cmd() -> int:
    """DEPRECATED: Migrate legacy sprint files to roadmap.
    
    This function is deprecated per ADR-0002. The roadmap system now uses
    flat ULID-based directory structure exclusively. Legacy hierarchical
    migration is no longer supported.
    """
    print("This migration command has been deprecated.")
    print("The roadmap system now uses flat ULID-based structure per ADR-0002.")
    print("Legacy hierarchical directory migration is no longer supported.")
    return 1


def migrate_embedded_tasks_cmd() -> int:
    """Migrate embedded tasks to separate files."""
    from vibey.operations.migrations import migrate_embedded_tasks

    return migrate_embedded_tasks(
        root_dir=Path.cwd() / ".vibey",  # Migration expects .vibey/ path
        dry_run=False
    )


def extract_embedded_cmd(dry_run: bool = True, verbose: bool = True) -> int:
    """Extract embedded tasks from sprint files to standalone task files.

    Scans all sprint YAML files for embedded tasks[] arrays and creates
    individual task files in the flat .vibey/roadmap/tasks/ directory.

    Args:
        dry_run: If True, only show what would be extracted without creating files
        verbose: If True, print detailed output

    Returns:
        0 if successful, 1 if errors occurred
    """
    from vibey.operations.migrations.extract_embedded_tasks import (
        extract_embedded_tasks,
    )

    root_dir = Path.cwd()
    roadmap_dir = root_dir / ".vibey" / "roadmap"

    if not roadmap_dir.exists():
        print("Roadmap directory not found")
        print("   Run 'vibey roadmap init' first")
        return 1

    stats = extract_embedded_tasks(
        roadmap_dir=roadmap_dir,
        dry_run=dry_run,
        verbose=verbose,
    )

    if stats.get("errors"):
        return 1

    return 0


def migrate_format_cmd(
    dry_run: bool = False,
    backup: bool = True,
    path: Optional[str] = None,
    force: bool = False,
    verbose: bool = False,
) -> int:
    """
    Migrate YAML files from v1 format to v2 format.

    V1 format uses legacy field names like created, started, completed.
    V2 format uses created_at, started_at, completed_at, etc.
    """
    # Import the full implementation from commands.py for now
    # This will be fully extracted in a later phase
    from vibey.cli.commands import migrate_format_cmd as impl
    return impl(dry_run=dry_run, backup=backup, path=path, force=force, verbose=verbose)


def migrate_docs_cmd(
    docs_dir: Optional[str] = None,
    dry_run: bool = False,
    backup: bool = True,
    verbose: bool = False,
) -> int:
    """Migrate documentation files to new format."""
    # Import the full implementation from commands.py for now
    # This will be fully extracted in a later phase
    from vibey.cli.commands import migrate_docs_cmd as impl
    return impl(docs_dir=docs_dir, dry_run=dry_run, backup=backup, verbose=verbose)
