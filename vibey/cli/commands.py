"""
Command implementations for vibey CLI.

This module provides Python API for all CLI commands using direct function imports
from the operations modules (no subprocess calls).
"""

from pathlib import Path
from typing import Optional

# Import operations modules
from vibey.operations.roadmap import (
    init_roadmap,
    query_roadmap_summary,
    query_track_details,
    query_sprint_details,
    query_task_details,
    start_task,
    start_sprint,
    complete_task,
    complete_sprint,
    get_task_context,
    validate_roadmap,
    add_commit_to_task,
    get_current_commit,
)
from vibey.operations.roadmap.summarize import summarize_sprint, summarize_task
from vibey.operations.deployment import deploy_framework
from vibey.operations.docs import generate_docs
from vibey.operations.config import generate_config, update_config_value
from vibey.operations.migrations import (
    migrate_to_roadmap,
    migrate_to_hierarchical,
    migrate_embedded_tasks,
)

# Import formatters for CLI output
from vibey.cli.formatters import (
    format_roadmap_summary,
    format_track_details,
    format_sprint_details,
    format_task_details,
    format_success,
    format_error,
)


# ============================================================================
# Roadmap Commands
# ============================================================================

def roadmap_init_cmd(name: str, version: str) -> int:
    """Initialize a new roadmap."""
    root_dir = Path.cwd()  # Project root
    return init_roadmap(
        root_dir=root_dir,  # init_roadmap expects project root (adds .vibey/ internally)
        roadmap_id=name or "default-roadmap",
        roadmap_name=name or "Default Roadmap",
        version=version or "1.0.0",
    )


def roadmap_status_cmd(track: Optional[str] = None, sprint: Optional[str] = None) -> int:
    """Show roadmap status."""
    root_dir = Path.cwd()  # Project root

    try:
        if sprint:
            result = query_sprint_details(root_dir, sprint)
            print(format_sprint_details(result))
        elif track:
            result = query_track_details(root_dir, track)
            print(format_track_details(result))
        else:
            result = query_roadmap_summary(root_dir)
            print(format_roadmap_summary(result))
        return 0
    except Exception as e:
        print(format_error(str(e)))
        return 1


def roadmap_show_cmd(item_id: str) -> int:
    """Show details for an item."""
    root_dir = Path.cwd()  # Project root

    try:
        # Determine type from ID format
        if 'task' in item_id:
            result = query_task_details(root_dir, item_id)
            print(format_task_details(result))
        elif item_id.count('-') >= 2:  # sprint format: track-sprint
            result = query_sprint_details(root_dir, item_id)
            print(format_sprint_details(result))
        else:  # track format
            result = query_track_details(root_dir, item_id)
            print(format_track_details(result))
        return 0
    except Exception as e:
        print(format_error(str(e)))
        return 1


def roadmap_start_cmd(item_id: str) -> int:
    """Start a sprint or task."""
    root_dir = Path.cwd()  # Project root

    if 'task' in item_id:
        return start_task(root_dir, item_id)
    elif 'sprint' in item_id or item_id.count('-') >= 1:
        return start_sprint(root_dir, item_id)
    else:
        print(f"Error: Cannot determine item type from ID: {item_id}")
        print("Expected format: <track>-<sprint>-task-<num> or <track>-<sprint>[-name]")
        return 1


def roadmap_complete_cmd(item_id: str) -> int:
    """Complete a sprint or task."""
    root_dir = Path.cwd()  # Project root

    if 'task' in item_id:
        return complete_task(root_dir, item_id)
    elif 'sprint' in item_id or item_id.count('-') >= 1:
        return complete_sprint(root_dir, item_id)
    else:
        print(f"Error: Cannot determine item type from ID: {item_id}")
        print("Expected format: <track>-<sprint>-task-<num> or <track>-<sprint>[-name]")
        return 1


def roadmap_context_cmd(task_id: str) -> int:
    """Get context for a task."""
    return get_task_context(task_id=task_id, root_dir=Path.cwd())


def roadmap_summarize_cmd(item_type: str, item_id: str) -> int:
    """Summarize an item."""
    root_dir = Path.cwd()  # Project root

    # Determine type from ID format
    if 'task' in item_id:
        # Extract sprint_id from task_id (format: track-sprint-task-NNN)
        parts = item_id.split('-task-')
        if len(parts) != 2:
            print(f"Error: Invalid task ID format: {item_id}")
            return 1
        sprint_id = parts[0]
        return summarize_task(sprint_id=sprint_id, task_id=item_id, root_dir=root_dir)
    else:
        return summarize_sprint(sprint_id=item_id, root_dir=root_dir)


def roadmap_list_cmd() -> int:
    """List all tracks/sprints/tasks."""
    root_dir = Path.cwd()  # Project root

    try:
        result = query_roadmap_summary(root_dir)
        print(format_roadmap_summary(result))
        return 0
    except Exception as e:
        print(format_error(str(e)))
        return 1


def roadmap_validate_cmd() -> int:
    """Validate roadmap structure."""
    return validate_roadmap(root_dir=Path.cwd())


def roadmap_add_commit_cmd(task_id: str, commit_sha: Optional[str] = None, auto: bool = False) -> int:
    """Add a git commit to a task."""
    if auto:
        commit_sha = get_current_commit()
        if not commit_sha:
            print("Error: Could not detect current commit")
            return 1
    elif not commit_sha:
        print("Error: Either provide a commit SHA or use --auto flag")
        return 1

    return add_commit_to_task(
        task_id=task_id,
        commit_sha=commit_sha,
        vibey_path=Path.cwd() / ".vibey",  # This one expects .vibey/ path
        auto_detect=auto
    )


# ============================================================================
# Deploy Commands
# ============================================================================

def deploy_cmd(platform: str, clean: bool = False) -> int:
    """Deploy framework to platform."""
    return deploy_framework(
        platform=platform,
        clean=clean,
        project_root=Path.cwd()
    )


# ============================================================================
# Docs Commands
# ============================================================================

def docs_generate_cmd(overwrite: bool = False) -> int:
    """Generate documentation."""
    return generate_docs(
        vibey_dir=Path.cwd() / ".vibey",  # This expects .vibey/ path
        overwrite=overwrite,
        quiet=False
    )


# ============================================================================
# Config Commands
# ============================================================================

def config_show_cmd() -> int:
    """Show current configuration."""
    from vibey.cli.config_migrate import config_show_cmd as show_impl
    return show_impl()


def config_validate_cmd() -> int:
    """Validate configuration."""
    from vibey.cli.config_migrate import config_validate_cmd as validate_impl
    return validate_impl()


def config_generate_cmd() -> int:
    """Generate configuration."""
    # Interactive - let generate_config handle prompts
    # This would typically be called with parameters from CLI
    print("Error: config generate requires parameters (project name, type, etc.)")
    print("Use 'vibey config generate --help' for usage information")
    return 1


def config_migrate_cmd(backup: bool = True, dry_run: bool = False, force: bool = False) -> int:
    """Migrate legacy config to modular format."""
    from vibey.cli.config_migrate import config_migrate_cmd as migrate_impl
    return migrate_impl(backup=backup, dry_run=dry_run, force=force)


def config_rollback_cmd(backup_id: Optional[str] = None, list_backups: bool = False) -> int:
    """Rollback to a previous config backup."""
    from vibey.cli.config_migrate import config_rollback_cmd as rollback_impl
    return rollback_impl(backup_id=backup_id, list_backups=list_backups)


def config_update_cmd(key: str, value: str) -> int:
    """Update configuration value."""
    config_path = Path.cwd() / ".vibey" / "config" / "project.yaml"
    return update_config_value(
        config_path=config_path,
        key_path=key,
        value=value,
        create_missing=False,
        verbose=True
    )


# ============================================================================
# Migration Commands
# ============================================================================

def migrate_to_roadmap_cmd() -> int:
    """Migrate legacy sprint files to roadmap."""
    return migrate_to_roadmap(
        root_dir=Path.cwd() / ".vibey",  # Migration expects .vibey/ path
        dry_run=False,
        backup=True
    )


def migrate_to_hierarchical_cmd() -> int:
    """Migrate flat structure to hierarchical."""
    return migrate_to_hierarchical(
        root_dir=Path.cwd() / ".vibey",  # Migration expects .vibey/ path
        dry_run=False,
        backup=True
    )


def migrate_embedded_tasks_cmd() -> int:
    """Migrate embedded tasks to separate files."""
    return migrate_embedded_tasks(
        root_dir=Path.cwd() / ".vibey",  # Migration expects .vibey/ path
        dry_run=False
    )
