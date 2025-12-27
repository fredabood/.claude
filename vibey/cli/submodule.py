"""
Submodule CLI commands.

Provides CLI interface for git submodule integration with vibey roadmaps.

Commands are organized into categories:
- Discovery & Registry: list, discover, show
- Push-down: push, requirements, link, unlink
- Pull-up / Aggregation: status, aggregate, blockers, refresh
- Cross-repo Dependencies: add-dep, deps, validate-deps, dep-graph
- Config: config

Design reference: SUBMODULE_ISOLATION_AND_PUSHDOWN.md
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


# ============================================================================
# Discovery & Registry Commands
# ============================================================================


def submodule_list_cmd(show_all: bool) -> int:
    """List all detected submodules with Vibey status."""
    from vibey.operations.submodule import SubmoduleDiscovery
    from vibey.config import load_submodule_config

    try:
        discovery = SubmoduleDiscovery()
        config = load_submodule_config()

        # Get submodules from git
        git_submodules = discovery.parse_gitmodules()

        if not git_submodules and not config.submodules:
            console.print("[yellow]No submodules found.[/yellow]")
            console.print("Run 'vibey submodule discover' to detect submodules.")
            return 0

        table = Table(title="Git Submodules")
        table.add_column("Path", style="cyan")
        table.add_column("Has Vibey", style="green")
        table.add_column("Registered", style="blue")
        table.add_column("Sync Status", style="yellow")

        # Combine git submodules with registered ones
        all_paths = set(git_submodules)
        all_paths.update(s.path for s in config.submodules)

        for path in sorted(all_paths):
            has_vibey = discovery.has_vibey_roadmap(path)
            registered = config.get_submodule(path) is not None

            if not show_all and not has_vibey:
                continue

            sub_ref = config.get_submodule(path)
            sync_status = sub_ref.sync_status.value if sub_ref else "not registered"

            table.add_row(
                path,
                "✓" if has_vibey else "✗",
                "✓" if registered else "✗",
                sync_status,
            )

        console.print(table)
        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def submodule_discover_cmd(auto_register: bool) -> int:
    """Auto-discover submodules from .gitmodules and optionally register."""
    from vibey.operations.submodule import SubmoduleDiscovery
    from vibey.config import load_submodule_config, save_submodule_config
    from vibey.roadmap.models.submodule import SubmoduleReference, DetectionSource

    try:
        discovery = SubmoduleDiscovery()
        config = load_submodule_config()

        # Parse .gitmodules
        submodule_paths = discovery.parse_gitmodules()

        if not submodule_paths:
            console.print("[yellow]No submodules found in .gitmodules[/yellow]")
            return 0

        console.print(f"[green]Found {len(submodule_paths)} submodule(s)[/green]")

        vibey_submodules = []
        for path in submodule_paths:
            has_vibey = discovery.has_vibey_roadmap(path)
            status = "[green]✓ Has Vibey[/green]" if has_vibey else "[dim]No Vibey[/dim]"
            console.print(f"  {path}: {status}")

            if has_vibey:
                vibey_submodules.append(path)

        if auto_register and vibey_submodules:
            console.print()
            console.print("[blue]Registering Vibey-enabled submodules...[/blue]")

            for path in vibey_submodules:
                if config.get_submodule(path) is None:
                    ref = SubmoduleReference(
                        path=path,
                        aggregate=True,
                        detection_source=DetectionSource.GITMODULES,
                    )
                    config.add_submodule(ref)
                    console.print(f"  [green]Registered: {path}[/green]")
                else:
                    console.print(f"  [dim]Already registered: {path}[/dim]")

            save_submodule_config(config)
            console.print(f"[green]Saved to .vibey/config/submodules.yaml[/green]")

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def submodule_show_cmd(path: str) -> int:
    """Show details for a specific submodule."""
    from vibey.operations.submodule import SubmoduleDiscovery, ProgressAggregator
    from vibey.config import load_submodule_config

    try:
        discovery = SubmoduleDiscovery()
        config = load_submodule_config()

        # Normalize path
        path = path.replace("\\", "/").strip("/")

        # Check if submodule exists
        if not (Path.cwd() / path).exists():
            console.print(f"[red]Submodule not found: {path}[/red]")
            return 1

        # Get registration info
        sub_ref = config.get_submodule(path)
        has_vibey = discovery.has_vibey_roadmap(path)

        console.print(Panel(f"[bold]{path}[/bold]", title="Submodule Details"))

        console.print(f"  Has Vibey Roadmap: {'[green]Yes[/green]' if has_vibey else '[red]No[/red]'}")
        console.print(f"  Registered: {'[green]Yes[/green]' if sub_ref else '[yellow]No[/yellow]'}")

        if sub_ref:
            console.print(f"  Aggregate: {sub_ref.aggregate}")
            console.print(f"  Detection Source: {sub_ref.detection_source.value}")
            console.print(f"  Sync Status: {sub_ref.sync_status.value}")
            if sub_ref.last_synced:
                console.print(f"  Last Synced: {sub_ref.last_synced}")
            if sub_ref.track_filter:
                console.print(f"  Track Filter: {', '.join(sub_ref.track_filter)}")

        if has_vibey:
            console.print()
            console.print("[bold]Progress:[/bold]")

            try:
                aggregator = ProgressAggregator()
                progress = aggregator.aggregate_submodule(path)

                console.print(f"  Tracks: {progress.tracks_completed}/{progress.tracks_total}")
                console.print(f"  Sprints: {progress.sprints_completed}/{progress.sprints_total}")
                console.print(f"  Tasks: {progress.tasks_completed}/{progress.tasks_total}")
                console.print(f"  Completion: {progress.completion_percent:.1f}%")
            except Exception as e:
                console.print(f"  [yellow]Could not load progress: {e}[/yellow]")

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


# ============================================================================
# Aggregation Commands
# ============================================================================


def submodule_status_cmd() -> int:
    """Show aggregated progress across all submodules."""
    from vibey.operations.submodule import ProgressAggregator
    from vibey.config import load_submodule_config

    try:
        config = load_submodule_config()

        if not config.submodules:
            console.print("[yellow]No submodules registered.[/yellow]")
            console.print("Run 'vibey submodule discover --register' to register submodules.")
            return 0

        aggregator = ProgressAggregator()
        result = aggregator.aggregate_all()

        console.print(Panel("[bold]Submodule Progress Summary[/bold]"))

        # Overall stats
        console.print(f"  Submodules: {len(result.submodule_progress)}")
        console.print(f"  Total Tracks: {result.total_tracks}")
        console.print(f"  Completed Tracks: {result.completed_tracks}")
        console.print(f"  Total Tasks: {result.total_tasks}")
        console.print(f"  Completed Tasks: {result.completed_tasks}")
        console.print(f"  Overall Completion: {result.overall_completion_percent:.1f}%")

        if result.active_blockers:
            console.print()
            console.print(f"[red]Active Blockers: {len(result.active_blockers)}[/red]")
            console.print(f"  Critical: {result.critical_blocker_count}")

        # Per-submodule breakdown
        if result.submodule_progress:
            console.print()
            table = Table(title="Per-Submodule Progress")
            table.add_column("Submodule", style="cyan")
            table.add_column("Tasks", style="green")
            table.add_column("Completion", style="yellow")

            for prog in result.submodule_progress:
                table.add_row(
                    prog.submodule_path,
                    f"{prog.tasks_completed}/{prog.tasks_total}",
                    f"{prog.completion_percent:.1f}%",
                )

            console.print(table)

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def submodule_aggregate_cmd() -> int:
    """Pull progress from all submodules and update blocked_by statuses."""
    from vibey.operations.submodule import ProgressAggregator
    from vibey.config import load_submodule_config, save_submodule_config
    from datetime import datetime, timezone

    try:
        config = load_submodule_config()

        if not config.submodules:
            console.print("[yellow]No submodules registered.[/yellow]")
            return 0

        aggregator = ProgressAggregator()

        console.print("[blue]Aggregating progress from submodules...[/blue]")

        # Aggregate all
        result = aggregator.aggregate_all()

        console.print(f"  [green]Aggregated {len(result.submodule_progress)} submodule(s)[/green]")

        # Sync blocked_by statuses
        console.print("[blue]Syncing blocked_by statuses...[/blue]")
        sync_results = aggregator.sync_blocked_by_status()

        total_synced = sum(r.tasks_synced for r in sync_results)
        total_resolved = sum(r.blockers_resolved for r in sync_results)

        console.print(f"  [green]Synced {total_synced} task(s)[/green]")
        console.print(f"  [green]Resolved {total_resolved} blocker(s)[/green]")

        # Update last_synced for submodules
        for sub in config.submodules:
            sub.last_synced = datetime.now(timezone.utc)

        save_submodule_config(config)

        console.print()
        console.print(f"[green]Overall completion: {result.overall_completion_percent:.1f}%[/green]")

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


# ============================================================================
# Config Command
# ============================================================================


def submodule_config_cmd(show: bool, edit: bool) -> int:
    """View or edit submodule configuration."""
    from vibey.config import load_submodule_config, get_submodule_config_path

    try:
        config_path = get_submodule_config_path()

        if edit:
            import subprocess
            import os

            editor = os.environ.get("EDITOR", "vim")

            if not config_path.exists():
                # Create default config
                from vibey.config import save_submodule_config, get_default_submodule_config
                save_submodule_config(get_default_submodule_config())
                console.print(f"[green]Created default config at {config_path}[/green]")

            subprocess.run([editor, str(config_path)])
            return 0

        # Show config
        if not config_path.exists():
            console.print("[yellow]No config file found.[/yellow]")
            console.print(f"Run 'vibey submodule config --edit' to create one.")
            return 0

        config = load_submodule_config()

        console.print(Panel("[bold]Submodule Configuration[/bold]"))
        console.print(f"  Config file: {config_path}")
        console.print(f"  Default push mode: {config.default_push_mode.value}")
        console.print(f"  Aggregate on status: {config.aggregate_on_status}")
        console.print(f"  Stale threshold: {config.stale_threshold_minutes} minutes")

        if config.submodules:
            console.print()
            console.print("[bold]Registered Submodules:[/bold]")
            for sub in config.submodules:
                console.print(f"  - {sub.path}")
                console.print(f"      aggregate: {sub.aggregate}")
                if sub.track_filter:
                    console.print(f"      track_filter: {sub.track_filter}")
        else:
            console.print()
            console.print("[dim]No submodules registered.[/dim]")

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1
