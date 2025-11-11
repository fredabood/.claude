"""
Command implementations for vibey CLI.

This module provides Python API wrappers around the existing script functionality,
allowing them to be called from the Click-based CLI without subprocess calls.
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional, List

# Get the CLI directory (where the scripts are)
CLI_DIR = Path(__file__).parent


def run_script(script_name: str, args: List[str]) -> int:
    """
    Run a Python script from vibey/cli/ directory.

    Args:
        script_name: Name of the script file (with or without .py)
        args: List of command-line arguments

    Returns:
        Exit code from the script
    """
    if not script_name.endswith('.py'):
        script_name = f"{script_name}.py"

    script_path = CLI_DIR / script_name

    if not script_path.exists():
        print(f"Error: Script not found: {script_path}")
        return 1

    # Run the script with python3
    cmd = [sys.executable, str(script_path)] + args
    result = subprocess.run(cmd, cwd=Path.cwd())
    return result.returncode


# ============================================================================
# Roadmap Commands
# ============================================================================

def roadmap_init_cmd(name: str, version: str) -> int:
    """Initialize a new roadmap."""
    # TODO: roadmap-init.py needs to be refactored to accept parameters
    # For now, just run the script
    return run_script('roadmap-init.py', [])


def roadmap_status_cmd(track: Optional[str] = None, sprint: Optional[str] = None) -> int:
    """Show roadmap status."""
    args = []
    if track:
        args.extend(['--track', track])
    if sprint:
        args.extend(['--sprint', sprint])

    # If no specific args, show overall status
    return run_script('roadmap-query.py', args)


def roadmap_show_cmd(item_id: str) -> int:
    """Show details for an item."""
    # Determine type from ID format and use appropriate flag
    if 'task' in item_id:
        return run_script('roadmap-query.py', ['--task', item_id])
    elif item_id.count('-') >= 1:  # sprint format: track-sprint
        return run_script('roadmap-query.py', ['--sprint', item_id])
    else:  # track format: single name
        return run_script('roadmap-query.py', ['--track', item_id])


def roadmap_start_cmd(item_id: str) -> int:
    """Start a sprint or task."""
    if 'task' in item_id:
        return run_script('roadmap-update.py', ['--start-task', item_id])
    elif 'sprint' in item_id:
        return run_script('roadmap-update.py', ['--start-sprint', item_id])
    else:
        print(f"Error: Cannot determine item type from ID: {item_id}")
        print("Expected format: <track>-<sprint>-task-<num> or <track>-<sprint>")
        return 1


def roadmap_complete_cmd(item_id: str) -> int:
    """Complete a sprint or task."""
    if 'task' in item_id:
        return run_script('roadmap-update.py', ['--complete-task', item_id])
    elif 'sprint' in item_id:
        return run_script('roadmap-update.py', ['--complete-sprint', item_id])
    else:
        print(f"Error: Cannot determine item type from ID: {item_id}")
        print("Expected format: <track>-<sprint>-task-<num> or <track>-<sprint>")
        return 1


def roadmap_context_cmd(task_id: str) -> int:
    """Get context for a task."""
    return run_script('roadmap-context.py', [task_id])


def roadmap_summarize_cmd(item_type: str, item_id: str) -> int:
    """Summarize an item."""
    # roadmap-summarize.py only takes the ID, not the type
    # The type is determined from the ID format
    return run_script('roadmap-summarize.py', [item_id])


def roadmap_list_cmd() -> int:
    """List all tracks/sprints/tasks."""
    return run_script('roadmap-query.py', ['--list', 'all'])


def roadmap_validate_cmd() -> int:
    """Validate roadmap structure."""
    return run_script('validate-roadmap-format.py', [])


# ============================================================================
# Deploy Commands
# ============================================================================

def deploy_cmd(platform: str, clean: bool = False) -> int:
    """Deploy framework to platform."""
    args = ['--platform', platform]
    if clean:
        args.append('--clean')

    return run_script('deploy.py', args)


# ============================================================================
# Docs Commands
# ============================================================================

def docs_generate_cmd(overwrite: bool = False) -> int:
    """Generate documentation."""
    args = ['generate']
    if overwrite:
        args.append('--overwrite')

    return run_script('docs.py', args)


# ============================================================================
# Config Commands
# ============================================================================

def config_show_cmd() -> int:
    """Show current configuration."""
    # TODO: Implement config show
    print("Configuration display not yet implemented")
    return 1


def config_validate_cmd() -> int:
    """Validate configuration."""
    return run_script('validate-config.py', [])


def config_generate_cmd() -> int:
    """Generate configuration."""
    return run_script('generate-config.py', [])


def config_update_cmd(key: str, value: str) -> int:
    """Update configuration value."""
    return run_script('update-config.py', [key, value])


# ============================================================================
# Migration Commands
# ============================================================================

def migrate_to_roadmap_cmd() -> int:
    """Migrate legacy sprint files to roadmap."""
    return run_script('migrate-to-roadmap.py', [])


def migrate_to_hierarchical_cmd() -> int:
    """Migrate flat structure to hierarchical."""
    return run_script('migrate-to-hierarchical.py', [])


def migrate_embedded_tasks_cmd() -> int:
    """Migrate embedded tasks to separate files."""
    return run_script('migrate-embedded-tasks.py', [])
