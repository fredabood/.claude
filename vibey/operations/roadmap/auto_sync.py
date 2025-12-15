"""Auto-sync functionality for YAML-SQLite synchronization.

Provides lazy sync - checks if YAML files have been modified since last
database rebuild and triggers a rebuild if needed.
"""

from pathlib import Path
from typing import Optional
import os


def check_sync_needed(root_dir: Path, verbose: bool = False) -> bool:
    """Check if any YAML files are newer than the database.

    Compares modification times of YAML files in .vibey/roadmap/ with
    the database file modification time.

    Args:
        root_dir: Project root directory
        verbose: Print debug information

    Returns:
        True if sync is needed, False otherwise
    """
    db_path = root_dir / ".vibey" / "roadmap.db"
    yaml_dir = root_dir / ".vibey" / "roadmap"

    # If no database exists, sync is needed
    if not db_path.exists():
        if verbose:
            print("  Database does not exist, sync needed")
        return True

    # If no YAML directory exists, no sync needed
    if not yaml_dir.exists():
        if verbose:
            print("  No roadmap directory, sync not needed")
        return False

    db_mtime = db_path.stat().st_mtime

    # Check modification times of YAML files in key directories
    yaml_dirs = ['tracks', 'sprints', 'tasks']
    for subdir in yaml_dirs:
        subdir_path = yaml_dir / subdir
        if not subdir_path.exists():
            continue

        for yaml_file in subdir_path.glob("*.yaml"):
            file_mtime = yaml_file.stat().st_mtime
            if file_mtime > db_mtime:
                if verbose:
                    print(f"  Modified: {yaml_file.name} ({file_mtime:.0f} > {db_mtime:.0f})")
                return True

    if verbose:
        print("  All YAML files older than database, no sync needed")
    return False


def ensure_synced(root_dir: Path, verbose: bool = False, quiet: bool = False) -> bool:
    """Ensure database is synced with YAML files.

    Checks if sync is needed and triggers rebuild if so.

    Args:
        root_dir: Project root directory
        verbose: Print debug information
        quiet: Suppress output messages

    Returns:
        True if sync was performed, False if not needed
    """
    if not check_sync_needed(root_dir, verbose=verbose):
        return False

    if not quiet:
        print("🔄 Syncing database with YAML changes...")

    # Import here to avoid circular imports
    from vibey.cli.commands import db_rebuild_cmd

    try:
        # Run rebuild silently
        db_rebuild_cmd(force=True)
        if not quiet:
            print("✅ Database synced")
        return True
    except Exception as e:
        if not quiet:
            print(f"⚠️  Sync warning: {e}")
        return False


def get_sync_status(root_dir: Path) -> dict:
    """Get detailed sync status information.

    Args:
        root_dir: Project root directory

    Returns:
        Dictionary with sync status details
    """
    db_path = root_dir / ".vibey" / "roadmap.db"
    yaml_dir = root_dir / ".vibey" / "roadmap"

    result = {
        'database_exists': db_path.exists(),
        'yaml_dir_exists': yaml_dir.exists(),
        'sync_needed': False,
        'db_mtime': None,
        'newest_yaml': None,
        'newest_yaml_mtime': None,
        'modified_files': [],
    }

    if not db_path.exists() or not yaml_dir.exists():
        result['sync_needed'] = db_path.exists() != yaml_dir.exists()
        return result

    db_mtime = db_path.stat().st_mtime
    result['db_mtime'] = db_mtime

    yaml_dirs = ['tracks', 'sprints', 'tasks']
    newest_mtime = 0
    newest_file = None

    for subdir in yaml_dirs:
        subdir_path = yaml_dir / subdir
        if not subdir_path.exists():
            continue

        for yaml_file in subdir_path.glob("*.yaml"):
            file_mtime = yaml_file.stat().st_mtime
            if file_mtime > newest_mtime:
                newest_mtime = file_mtime
                newest_file = yaml_file.name
            if file_mtime > db_mtime:
                result['modified_files'].append(yaml_file.name)
                result['sync_needed'] = True

    result['newest_yaml'] = newest_file
    result['newest_yaml_mtime'] = newest_mtime if newest_file else None

    return result
