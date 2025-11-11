"""
Config migration command implementation.

This module handles migration from legacy .claude/project-config.yaml
to the new modular .vibey/config/ structure.
"""

from pathlib import Path
from datetime import datetime
import shutil
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from vibey.config import (
    ConfigLoader,
    ConfigLocation,
    ConfigNotFoundError,
    ConfigValidationError,
)

console = Console()


def config_migrate_cmd(backup: bool = True, dry_run: bool = False, force: bool = False) -> int:
    """
    Migrate legacy config to modular format.

    Args:
        backup: Create backup before migration
        dry_run: Show what would happen without making changes
        force: Overwrite existing modular config

    Returns:
        int: Exit code (0 = success, 1 = error)
    """
    project_root = Path.cwd()

    console.print(Panel.fit(
        "[bold cyan]Vibey Config Migration Tool[/bold cyan]\n"
        "Migrating from .claude/project-config.yaml to .vibey/config/",
        border_style="blue"
    ))

    # Detect config location
    loader = ConfigLoader(warn_on_legacy=False)
    location = loader.detect_config_location(project_root)

    # Check if migration is needed/possible
    if location == ConfigLocation.NONE:
        console.print("[red]✗[/red] No configuration found")
        console.print("  Expected: .claude/project-config.yaml")
        console.print("\n[yellow]Tip:[/yellow] Nothing to migrate")
        return 1

    elif location == ConfigLocation.MODULAR:
        console.print("[yellow]ℹ[/yellow] Already using modular config (.vibey/config/)")
        console.print("  No migration needed!")
        return 0

    elif location == ConfigLocation.BOTH:
        if not force:
            console.print("[yellow]⚠[/yellow] Both configs exist:")
            console.print("  - [green].vibey/config/[/green] (modular)")
            console.print("  - [dim].claude/project-config.yaml[/dim] (legacy)")
            console.print("\n[yellow]Options:[/yellow]")
            console.print("  1. Use [green]--force[/green] to overwrite modular config with legacy")
            console.print("  2. Manually remove .claude/project-config.yaml if migrated")
            return 1
        else:
            console.print("[yellow]⚠[/yellow] Force mode: overwriting existing modular config")
            location = ConfigLocation.LEGACY  # Treat as legacy-only for migration

    # At this point, location is LEGACY
    legacy_file = project_root / ".claude" / "project-config.yaml"
    modular_dir = project_root / ".vibey" / "config"

    console.print(f"\n[bold]Source:[/bold] {legacy_file}")
    console.print(f"[bold]Target:[/bold] {modular_dir}")

    # Load and validate legacy config
    console.print("\n[bold]Step 1:[/bold] Loading legacy config...")
    try:
        config = loader.load_config(project_root)
        console.print("[green]✓[/green] Legacy config loaded and validated")
    except ConfigNotFoundError as e:
        console.print(f"[red]✗[/red] Config not found: {e}")
        return 1
    except ConfigValidationError as e:
        console.print(f"[red]✗[/red] Invalid config:\n{e}")
        return 1
    except Exception as e:
        console.print(f"[red]✗[/red] Error loading config: {e}")
        return 1

    # Show what will be migrated
    console.print("\n[bold]Step 2:[/bold] Planning migration...")
    _show_migration_preview(config)

    if dry_run:
        console.print("\n[yellow]ℹ[/yellow] Dry run mode - no changes made")
        console.print("  Remove --dry-run to perform migration")
        return 0

    # Create backup if requested
    if backup and not dry_run:
        console.print("\n[bold]Step 3:[/bold] Creating backup...")
        backup_result = _create_backup(legacy_file, project_root)
        if backup_result:
            console.print(f"[green]✓[/green] Backup created: {backup_result}")
        else:
            console.print("[red]✗[/red] Backup failed")
            return 1
    else:
        console.print("\n[bold]Step 3:[/bold] Skipping backup (--no-backup)")

    # Create modular config directory
    console.print(f"\n[bold]Step 4:[/bold] Creating {modular_dir}...")
    try:
        modular_dir.mkdir(parents=True, exist_ok=True)
        console.print("[green]✓[/green] Directory created")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create directory: {e}")
        return 1

    # Write modular config files
    console.print("\n[bold]Step 5:[/bold] Writing modular config files...")
    try:
        config.to_directory(modular_dir)

        files_created = [
            "project.yaml",
            "framework.yaml",
            "agents.yaml",
            "quality-gates.yaml"
        ]

        for filename in files_created:
            filepath = modular_dir / filename
            size = filepath.stat().st_size
            console.print(f"[green]✓[/green] {filename} ({size} bytes)")

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to write config files: {e}")
        return 1

    # Success!
    console.print("\n" + "="*60)
    console.print("[bold green]✓ Migration complete![/bold green]")
    console.print("="*60)

    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Verify config: [cyan]vibey config show[/cyan]")
    console.print("  2. Validate config: [cyan]vibey config validate[/cyan]")
    console.print("  3. Remove legacy config (optional):")
    console.print(f"     [dim]rm {legacy_file}[/dim]")

    if backup_result:
        console.print(f"\n[dim]Backup location: {backup_result}[/dim]")

    return 0


def _show_migration_preview(config) -> None:
    """Show preview of what will be migrated."""
    tree = Tree("[bold]Migration Preview[/bold]")

    # Project
    project_node = tree.add("📦 [cyan]project.yaml[/cyan]")
    project_node.add(f"name: {config.project.project.name}")
    project_node.add(f"version: {config.project.project.version}")
    project_node.add(f"type: {config.project.project.type.value}")
    project_node.add(f"languages: {', '.join(config.project.tech_stack.languages[:3])}")

    # Framework
    framework_node = tree.add("⚙️  [cyan]framework.yaml[/cyan]")
    framework_node.add(f"version: {config.framework.framework.version}")
    framework_node.add(f"orchestration: {config.framework.framework.orchestration_mode.value}")
    framework_node.add(f"platforms: {', '.join(config.framework.deployment.platforms)}")

    # Agents
    agents_node = tree.add("🤖 [cyan]agents.yaml[/cyan]")
    agents_node.add(f"enabled: {len(config.agents.agents.enabled)} agents")
    if config.agents.agent_preferences:
        agents_node.add(f"preferences: {len(config.agents.agent_preferences)} configured")

    # Quality Gates
    qg_node = tree.add("🛡️  [cyan]quality-gates.yaml[/cyan]")
    qg_node.add(f"mode: {config.quality_gates.quality_gates.mode.value}")
    qg_node.add(f"security: {config.quality_gates.gates.security.threshold}% threshold")
    qg_node.add(f"testing: {config.quality_gates.gates.testing.coverage_threshold}% coverage")

    console.print(tree)


def _create_backup(legacy_file: Path, project_root: Path) -> Optional[Path]:
    """
    Create backup of legacy config.

    Args:
        legacy_file: Path to legacy config file
        project_root: Project root directory

    Returns:
        Path to backup file, or None if failed
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = project_root / ".vibey" / "config-backups" / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_file = backup_dir / "project-config.yaml"
        shutil.copy2(legacy_file, backup_file)

        # Also create a README in backup
        readme = backup_dir / "README.md"
        readme.write_text(
            f"# Config Backup\n\n"
            f"Created: {datetime.now().isoformat()}\n"
            f"Source: {legacy_file}\n"
            f"Reason: Migration to modular config format\n\n"
            f"This is a backup of your legacy .claude/project-config.yaml before migration.\n"
            f"You can restore it by copying back to {legacy_file}\n"
        )

        return backup_file

    except Exception as e:
        console.print(f"[red]Backup error: {e}[/red]")
        return None


def config_validate_cmd() -> int:
    """Validate configuration files."""
    from vibey.config import load_config, ConfigNotFoundError, ConfigValidationError
    from vibey.cli.config_utils import check_and_offer_migration
    from pathlib import Path

    console.print(Panel.fit(
        "[bold cyan]Vibey Config Validation[/bold cyan]\n"
        "Validating configuration files",
        border_style="blue"
    ))

    project_root = Path.cwd()

    # Check if migration should be offered
    check_and_offer_migration(project_root)

    # Try to load config
    try:
        config = load_config(project_root)

        console.print("\n[bold green]✓ Configuration valid![/bold green]\n")

        # Show summary
        table = Table(title="Configuration Summary")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Project", config.project.project.name)
        table.add_row("Version", config.project.project.version)
        table.add_row("Type", config.project.project.type.value)
        table.add_row("Framework", config.framework.framework.version)
        table.add_row("Orchestration", config.framework.framework.orchestration_mode.value)
        table.add_row("Agents Enabled", str(len(config.agents.agents.enabled)))
        table.add_row("Quality Gates", config.quality_gates.quality_gates.mode.value)

        console.print(table)

        return 0

    except ConfigNotFoundError as e:
        console.print(f"\n[red]✗ No configuration found[/red]")
        console.print(f"  {e}")
        return 1

    except ConfigValidationError as e:
        console.print(f"\n[red]✗ Configuration invalid[/red]")
        console.print(f"\n{e}")
        return 1

    except Exception as e:
        console.print(f"\n[red]✗ Error:[/red] {e}")
        return 1


def config_show_cmd() -> int:
    """Show current configuration."""
    # For now, just call validate (shows summary)
    return config_validate_cmd()


def config_rollback_cmd(backup_id: Optional[str] = None, list_backups: bool = False) -> int:
    """
    Rollback to a previous config backup.

    Args:
        backup_id: Specific backup timestamp to restore (default: latest)
        list_backups: List available backups

    Returns:
        int: Exit code (0 = success, 1 = error)
    """
    project_root = Path.cwd()
    backup_dir = project_root / ".vibey" / "config-backups"

    console.print(Panel.fit(
        "[bold cyan]Vibey Config Rollback[/bold cyan]\n"
        "Restore configuration from backup",
        border_style="blue"
    ))

    # List backups if requested
    if list_backups:
        if not backup_dir.exists() or not list(backup_dir.iterdir()):
            console.print("\n[yellow]No backups found[/yellow]")
            console.print(f"  Backup directory: {backup_dir}")
            return 0

        console.print("\n[bold]Available Backups:[/bold]\n")

        backups = sorted(backup_dir.iterdir(), reverse=True)
        for backup in backups:
            if backup.is_dir():
                timestamp = backup.name
                backup_file = backup / "project-config.yaml"
                if backup_file.exists():
                    size = backup_file.stat().st_size
                    console.print(f"  [cyan]{timestamp}[/cyan] ({size} bytes)")

        console.print(f"\n[dim]To restore: vibey config rollback --backup-id <timestamp>[/dim]")
        return 0

    # Check if backups exist
    if not backup_dir.exists() or not list(backup_dir.iterdir()):
        console.print("\n[red]✗ No backups found[/red]")
        console.print(f"  Backup directory: {backup_dir}")
        console.print("\n[yellow]Tip:[/yellow] Backups are created during migration")
        return 1

    # Find backup to restore
    if backup_id:
        backup_path = backup_dir / backup_id
        if not backup_path.exists():
            console.print(f"\n[red]✗ Backup not found:[/red] {backup_id}")
            console.print("\n[yellow]Tip:[/yellow] Use --list to see available backups")
            return 1
    else:
        # Use latest backup
        backups = sorted([d for d in backup_dir.iterdir() if d.is_dir()], reverse=True)
        if not backups:
            console.print("\n[red]✗ No valid backups found[/red]")
            return 1
        backup_path = backups[0]
        backup_id = backup_path.name

    backup_file = backup_path / "project-config.yaml"
    if not backup_file.exists():
        console.print(f"\n[red]✗ Backup file missing:[/red] {backup_file}")
        return 1

    console.print(f"\n[bold]Backup:[/bold] {backup_id}")
    console.print(f"[bold]File:[/bold] {backup_file}")

    # Ask for confirmation
    console.print("\n[yellow]⚠ Warning:[/yellow] This will:")
    console.print("  1. Restore legacy config to .claude/project-config.yaml")
    console.print("  2. NOT remove modular config (you can do that manually)")

    if not click.confirm("\nContinue with rollback?", default=False):
        console.print("\n[yellow]Rollback cancelled[/yellow]")
        return 0

    # Restore backup
    try:
        # Create .claude directory if needed
        claude_dir = project_root / ".claude"
        claude_dir.mkdir(exist_ok=True)

        # Copy backup to legacy location
        legacy_file = claude_dir / "project-config.yaml"
        shutil.copy2(backup_file, legacy_file)

        console.print("\n[green]✓ Rollback complete![/green]")
        console.print(f"\nRestored to: {legacy_file}")

        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. Verify config: [cyan]cat .claude/project-config.yaml[/cyan]")
        console.print("  2. Optionally remove modular config:")
        console.print("     [dim]rm -r .vibey/config/[/dim]")

        return 0

    except Exception as e:
        console.print(f"\n[red]✗ Rollback failed:[/red] {e}")
        return 1
