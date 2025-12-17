"""
CLI Change Tracker

Tracks which YAML files were modified by CLI commands so the pre-commit
hook can distinguish CLI-made changes from manual edits.

Task: git-integration-4-task-005 (dogfooding fix)
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Set, Optional


# Marker file location (relative to repo root)
MARKER_FILE = ".vibey/.cli-changes.json"


def _get_marker_path(repo_path: Optional[Path] = None) -> Path:
    """Get the path to the CLI changes marker file."""
    if repo_path is None:
        repo_path = Path.cwd()
    return repo_path / MARKER_FILE


def record_cli_change(file_path: str, repo_path: Optional[Path] = None) -> None:
    """
    Record that a file was modified by a CLI command.

    Args:
        file_path: Path to the file that was modified (relative to repo root)
        repo_path: Repository root path
    """
    marker_path = _get_marker_path(repo_path)

    # Load existing changes
    changes = load_cli_changes(repo_path)

    # Add this file
    changes.add(file_path)

    # Save changes
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    with open(marker_path, 'w') as f:
        json.dump({
            "files": sorted(changes),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }, f, indent=2)


def load_cli_changes(repo_path: Optional[Path] = None) -> Set[str]:
    """
    Load the set of files modified by CLI commands.

    Args:
        repo_path: Repository root path

    Returns:
        Set of file paths that were modified by CLI
    """
    marker_path = _get_marker_path(repo_path)

    if not marker_path.exists():
        return set()

    try:
        with open(marker_path) as f:
            data = json.load(f)
        return set(data.get("files", []))
    except (json.JSONDecodeError, IOError):
        return set()


def clear_cli_changes(repo_path: Optional[Path] = None) -> None:
    """
    Clear all recorded CLI changes (call after successful commit).

    Args:
        repo_path: Repository root path
    """
    marker_path = _get_marker_path(repo_path)

    if marker_path.exists():
        marker_path.unlink()


def is_cli_change(file_path: str, repo_path: Optional[Path] = None) -> bool:
    """
    Check if a file was modified by a CLI command.

    Args:
        file_path: Path to check (relative to repo root)
        repo_path: Repository root path

    Returns:
        True if file was modified by CLI, False otherwise
    """
    changes = load_cli_changes(repo_path)
    return file_path in changes


def get_manual_changes(staged_files: Set[str], repo_path: Optional[Path] = None) -> Set[str]:
    """
    Filter staged files to only those that were NOT modified by CLI.

    Args:
        staged_files: Set of staged file paths
        repo_path: Repository root path

    Returns:
        Set of files that were manually edited (not by CLI)
    """
    cli_changes = load_cli_changes(repo_path)
    return staged_files - cli_changes
