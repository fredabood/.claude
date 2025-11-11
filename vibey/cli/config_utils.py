"""
Config utilities for CLI scripts.

This module provides helper functions for loading configuration
in CLI scripts, with automatic fallback to legacy format.
"""

from pathlib import Path
from typing import Optional

from vibey.config import (
    load_config,
    VibeyConfig,
    ConfigNotFoundError,
    ConfigValidationError,
    ConfigLoader,
    ConfigLocation,
)


def load_project_config(project_root: Optional[Path] = None, quiet: bool = False) -> Optional[VibeyConfig]:
    """
    Load project configuration with error handling.

    This is a convenience wrapper for CLI scripts that:
    - Loads from either .vibey/config/ or .claude/project-config.yaml
    - Handles errors gracefully
    - Optionally suppresses output

    Args:
        project_root: Project root directory (default: current directory)
        quiet: Suppress error messages (default: False)

    Returns:
        VibeyConfig if loaded successfully, None if failed

    Example:
        config = load_project_config()
        if config:
            print(f"Project: {config.project.project.name}")
        else:
            print("No config found")
    """
    try:
        return load_config(project_root)
    except ConfigNotFoundError as e:
        if not quiet:
            print(f"Error: No configuration found")
            print(f"  {e}")
        return None
    except ConfigValidationError as e:
        if not quiet:
            print(f"Error: Invalid configuration")
            print(f"  {e}")
        return None
    except Exception as e:
        if not quiet:
            print(f"Error loading configuration: {e}")
        return None


def get_config_value(key_path: str, project_root: Optional[Path] = None, default=None):
    """
    Get a specific config value using dot notation.

    Args:
        key_path: Dot notation path (e.g., "project.name" or "framework.version")
        project_root: Project root directory
        default: Default value if not found

    Returns:
        Config value or default

    Example:
        project_name = get_config_value("project.project.name")
        orchestration = get_config_value("framework.framework.orchestration_mode")
    """
    config = load_project_config(project_root, quiet=True)
    if not config:
        return default

    # Navigate the config object using dot notation
    keys = key_path.split('.')
    value = config

    for key in keys:
        if hasattr(value, key):
            value = getattr(value, key)
        elif isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default

    # Handle enum values
    if hasattr(value, 'value'):
        return value.value

    return value


def config_exists(project_root: Optional[Path] = None) -> bool:
    """
    Check if a valid config exists.

    Args:
        project_root: Project root directory

    Returns:
        bool: True if config exists and is valid
    """
    return load_project_config(project_root, quiet=True) is not None


def should_prompt_migration(project_root: Optional[Path] = None) -> bool:
    """
    Check if migration prompt should be shown.

    This checks if:
    1. Legacy config exists
    2. Modular config does NOT exist
    3. User hasn't been prompted before (check for marker file)

    Args:
        project_root: Project root directory

    Returns:
        bool: True if migration prompt should be shown
    """
    if project_root is None:
        project_root = Path.cwd()

    loader = ConfigLoader(warn_on_legacy=False)
    location = loader.detect_config_location(project_root)

    # Only prompt if using legacy format exclusively
    if location != ConfigLocation.LEGACY:
        return False

    # Check if user already declined migration (marker file exists)
    marker_file = project_root / ".vibey" / ".migration-declined"
    if marker_file.exists():
        return False

    return True


def mark_migration_declined(project_root: Optional[Path] = None) -> None:
    """
    Mark that user declined migration.

    Creates a marker file so we don't keep prompting.

    Args:
        project_root: Project root directory
    """
    if project_root is None:
        project_root = Path.cwd()

    marker_dir = project_root / ".vibey"
    marker_dir.mkdir(exist_ok=True)

    marker_file = marker_dir / ".migration-declined"
    marker_file.write_text(
        "User declined config migration.\n"
        "To migrate later, run: vibey config migrate\n"
        "To remove this file and see the prompt again: rm .vibey/.migration-declined\n"
    )


def prompt_migration(project_root: Optional[Path] = None) -> bool:
    """
    Prompt user to migrate legacy config.

    Shows a friendly prompt asking if they want to migrate now.

    Args:
        project_root: Project root directory

    Returns:
        bool: True if user wants to migrate, False if declined
    """
    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    console.print()
    console.print(Panel.fit(
        "[yellow]⚠ Legacy Config Detected[/yellow]\n\n"
        "You're using the old config format (.claude/project-config.yaml).\n"
        "The new modular format (.vibey/config/) is recommended.\n\n"
        "[bold]Benefits of migrating:[/bold]\n"
        "  • Easier to understand and edit\n"
        "  • Better validation\n"
        "  • Clearer organization\n\n"
        "Would you like to migrate now? (Backup will be created)",
        border_style="yellow"
    ))

    try:
        import click
        if click.confirm("\nMigrate to modular config?", default=True):
            return True
        else:
            console.print("[dim]You can migrate later with: vibey config migrate[/dim]")
            mark_migration_declined(project_root)
            return False
    except ImportError:
        # If click not available, just inform
        console.print("[yellow]Run 'vibey config migrate' to upgrade your config.[/yellow]")
        return False


def check_and_offer_migration(project_root: Optional[Path] = None) -> None:
    """
    Check if migration is needed and offer to migrate.

    This is a convenience function for CLI commands to call at startup.

    Args:
        project_root: Project root directory
    """
    if not should_prompt_migration(project_root):
        return

    if prompt_migration(project_root):
        # Run migration
        from vibey.cli.config_migrate import config_migrate_cmd
        exit_code = config_migrate_cmd(backup=True, dry_run=False, force=False)

        if exit_code == 0:
            from rich.console import Console
            console = Console()
            console.print("\n[green]✓ Migration complete! Continuing with command...[/green]\n")
        else:
            from rich.console import Console
            console = Console()
            console.print("\n[red]Migration failed. Continuing with legacy config.[/red]\n")


__all__ = [
    'load_project_config',
    'get_config_value',
    'config_exists',
    'should_prompt_migration',
    'mark_migration_declined',
    'prompt_migration',
    'check_and_offer_migration',
]
