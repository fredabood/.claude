"""
Configuration management commands.

Commands for showing, validating, generating, migrating, and updating
configuration files.
"""

from pathlib import Path
from typing import Optional


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
    from vibey.operations.config import update_config_value

    config_path = Path.cwd() / ".vibey" / "config" / "project.yaml"
    return update_config_value(
        config_path=config_path,
        key_path=key,
        value=value,
        create_missing=False,
        verbose=True
    )
