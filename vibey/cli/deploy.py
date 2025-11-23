"""
Deployment command implementation.

This module handles the `vibey deploy` command for deploying Vibey
framework to different platforms.
"""

from pathlib import Path
from typing import Optional, List
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from vibey.adapters import ClaudeCodeAdapter, GooseAdapter, AiderAdapter
from vibey.adapters.base import PlatformAdapter
from vibey.config import load_config, ConfigNotFoundError

console = Console()

# Platform registry
PLATFORMS = {
    "claude-code": ClaudeCodeAdapter,
    "goose": GooseAdapter,
    "aider": AiderAdapter,
}


def get_adapter(platform: str) -> Optional[PlatformAdapter]:
    """
    Get adapter for platform.

    Args:
        platform: Platform name (e.g., "claude-code", "goose")

    Returns:
        Platform adapter instance, or None if not found
    """
    adapter_class = PLATFORMS.get(platform.lower())
    if adapter_class:
        return adapter_class()
    return None


def list_platforms() -> None:
    """List available platforms."""
    console.print("\n[bold]Available Platforms:[/bold]\n")

    table = Table()
    table.add_column("Platform", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Adapter", style="dim")

    for platform_name, adapter_class in PLATFORMS.items():
        adapter = adapter_class()
        table.add_row(
            platform_name,
            "✅ Ready",
            adapter_class.__name__
        )

    console.print(table)


def deploy_cmd(
    platform: str,
    clean: bool = False,
    validate: bool = True,
    project_root: Optional[Path] = None,
    init_roadmap: bool = True,
) -> int:
    """
    Deploy Vibey framework to specified platform.

    Args:
        platform: Target platform (claude-code, goose, or "all")
        clean: Remove existing deployment first
        validate: Validate deployment after completion
        project_root: Project root directory (default: current)
        init_roadmap: Initialize roadmap after deployment (default: True)

    Returns:
        Exit code (0 = success, 1 = error)
    """
    if project_root is None:
        project_root = Path.cwd()

    console.print(Panel.fit(
        "[bold cyan]Vibey Framework Deployment[/bold cyan]\n"
        f"Platform: {platform}",
        border_style="blue"
    ))

    # Handle "all" platforms
    if platform.lower() == "all":
        return deploy_all_platforms(clean=clean, validate=validate, project_root=project_root)

    # Get adapter
    adapter = get_adapter(platform)
    if not adapter:
        console.print(f"\n[red]✗ Unknown platform:[/red] {platform}")
        console.print("\n[yellow]Available platforms:[/yellow]")
        list_platforms()
        return 1

    # Load config
    console.print(f"\n[bold]Step 1:[/bold] Loading configuration...")
    try:
        config = load_config(project_root)
        console.print(f"[green]✓[/green] Config loaded: {config.project.project.name}")
    except ConfigNotFoundError:
        console.print("[red]✗[/red] No configuration found")
        console.print("  Run 'vibey init' to create configuration")
        return 1
    except Exception as e:
        console.print(f"[red]✗[/red] Error loading config: {e}")
        return 1

    # Deploy
    console.print(f"\n[bold]Step 2:[/bold] Deploying to {platform}...")

    source_dir = project_root / ".vibey"
    if not source_dir.exists():
        console.print(f"[red]✗[/red] Source directory not found: {source_dir}")
        console.print("  Expected .vibey/ directory with framework data")
        return 1

    result = adapter.deploy(
        source_dir=source_dir,
        config=config,
        clean=clean
    )

    # Show result
    console.print(f"\n[bold]Step 3:[/bold] Deployment result...")

    if result.success:
        console.print(f"[green]✓ Deployment successful![/green]")
    else:
        console.print(f"[red]✗ Deployment failed[/red]")

    # Show details
    tree = Tree("[bold]Deployment Details[/bold]")

    # Files
    files_node = tree.add(f"📁 Files")
    files_node.add(f"Created: {len(result.files_created)}")
    files_node.add(f"Updated: {len(result.files_updated)}")
    files_node.add(f"Deleted: {len(result.files_deleted)}")

    # Validation
    validation_node = tree.add("🔍 Validation")
    if result.validation_passed:
        validation_node.add("[green]✓ Passed[/green]")
    else:
        validation_node.add("[red]✗ Failed[/red]")

    # Duration
    tree.add(f"⏱️  Duration: {result.duration_seconds:.2f}s")

    console.print(tree)

    # Show errors
    if result.errors:
        console.print("\n[red]Errors:[/red]")
        for error in result.errors:
            console.print(f"  • {error}")

    # Show warnings
    if result.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  • {warning}")

    # Show created files
    if result.files_created:
        console.print("\n[dim]Files created:[/dim]")
        for file in result.files_created[:5]:  # Show first 5
            console.print(f"  [dim]{file}[/dim]")
        if len(result.files_created) > 5:
            console.print(f"  [dim]... and {len(result.files_created) - 5} more[/dim]")

    # Final status
    console.print()
    if result.success:
        console.print(f"[green]✓ {platform} deployment complete![/green]")
        console.print(f"[dim]Deployed to: {result.target_dir}[/dim]")

        # Initialize roadmap if requested and not already exists
        if init_roadmap:
            roadmap_file = project_root / ".vibey" / "roadmap.yaml"
            if not roadmap_file.exists():
                console.print(f"\n[bold]Step 4:[/bold] Initializing roadmap...")
                try:
                    from vibey.operations.roadmap import init_roadmap as do_init_roadmap
                    exit_code = do_init_roadmap(
                        root_dir=project_root,
                        roadmap_id=config.project.project.name.lower().replace(" ", "-"),
                        roadmap_name=config.project.project.name,
                        version=config.project.project.version or "1.0.0",
                    )
                    if exit_code == 0:
                        console.print(f"[green]✓[/green] Roadmap initialized")
                    else:
                        console.print(f"[yellow]⚠[/yellow] Roadmap initialization had issues (exit code {exit_code})")
                except Exception as e:
                    console.print(f"[yellow]⚠[/yellow] Could not initialize roadmap: {e}")
            else:
                console.print(f"\n[dim]Roadmap already exists, skipping initialization[/dim]")

        return 0
    else:
        console.print(f"[red]✗ {platform} deployment failed[/red]")
        return 1


def deploy_all_platforms(
    clean: bool = False,
    validate: bool = True,
    project_root: Optional[Path] = None
) -> int:
    """
    Deploy to all available platforms.

    Args:
        clean: Remove existing deployments first
        validate: Validate deployments after completion
        project_root: Project root directory (default: current)

    Returns:
        Exit code (0 = all succeeded, 1 = any failed)
    """
    console.print("\n[bold]Deploying to all platforms...[/bold]\n")

    results = {}
    for platform_name in PLATFORMS.keys():
        console.print(f"\n{'='*60}")
        console.print(f"[bold cyan]Platform: {platform_name}[/bold cyan]")
        console.print('='*60)

        exit_code = deploy_cmd(
            platform=platform_name,
            clean=clean,
            validate=validate,
            project_root=project_root
        )

        results[platform_name] = (exit_code == 0)

    # Summary
    console.print("\n" + "="*60)
    console.print("[bold]Deployment Summary[/bold]")
    console.print("="*60 + "\n")

    table = Table()
    table.add_column("Platform", style="cyan")
    table.add_column("Status", style="green")

    for platform_name, success in results.items():
        status = "[green]✓ Success[/green]" if success else "[red]✗ Failed[/red]"
        table.add_row(platform_name, status)

    console.print(table)

    # Return success if all succeeded
    all_succeeded = all(results.values())
    if all_succeeded:
        console.print(f"\n[green]✓ All platforms deployed successfully![/green]")
        return 0
    else:
        console.print(f"\n[yellow]⚠ Some platforms failed[/yellow]")
        return 1
