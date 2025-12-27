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
# Push-down Commands
# ============================================================================


def submodule_push_cmd(
    submodule_path: str,
    title: str,
    description: Optional[str],
    mode: str,
    sprint: Optional[str],
) -> int:
    """Push a task to a submodule.

    Modes:
    - linked: Creates task in BOTH parent and submodule, stores ULID mapping
    - parent_only: Creates external dependency in parent only
    - submodule_only: Creates task in submodule only
    """
    from vibey.operations.submodule import TaskPusher
    from vibey.config import load_submodule_config

    try:
        config = load_submodule_config()

        # Normalize path
        submodule_path = submodule_path.replace("\\", "/").strip("/")

        # Check if submodule is registered
        sub_ref = config.get_submodule(submodule_path)
        if sub_ref is None:
            console.print(f"[yellow]Submodule not registered: {submodule_path}[/yellow]")
            console.print("Run 'vibey submodule discover --register' first.")
            return 1

        pusher = TaskPusher()

        console.print(f"[blue]Pushing task to {submodule_path} (mode: {mode})...[/blue]")

        result = pusher.push_task(
            submodule_path=submodule_path,
            title=title,
            description=description or "",
            mode=mode,
            sprint_id=sprint,
        )

        if result.success:
            console.print(f"[green]Task created successfully[/green]")
            if result.parent_task_id:
                console.print(f"  Parent Task ID: {result.parent_task_id}")
            if result.submodule_task_id:
                console.print(f"  Submodule Task ID: {result.submodule_task_id}")
            if result.linked:
                console.print(f"  [blue]Tasks are linked[/blue]")
        else:
            console.print(f"[red]Failed: {result.error}[/red]")
            return 1

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def submodule_requirements_cmd(
    direction: str,
    status: Optional[str],
) -> int:
    """List cross-repo requirements.

    Direction:
    - outgoing: Requirements pushed FROM this repo TO submodules
    - incoming: Requirements pushed TO this repo FROM parent
    """
    from vibey.operations.submodule import RequirementTracker
    from vibey.config import load_submodule_config

    try:
        config = load_submodule_config()
        tracker = RequirementTracker()

        requirements = tracker.list_requirements(
            direction=direction,
            status_filter=status,
        )

        if not requirements:
            console.print(f"[dim]No {direction} requirements found.[/dim]")
            return 0

        table = Table(title=f"{direction.title()} Requirements")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Submodule", style="blue")
        table.add_column("Status", style="yellow")
        table.add_column("Linked", style="green")

        for req in requirements:
            table.add_row(
                req.id[:12] + "...",
                req.title[:40] + ("..." if len(req.title) > 40 else ""),
                req.submodule_path,
                req.status,
                "✓" if req.linked else "✗",
            )

        console.print(table)
        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def submodule_link_cmd(parent_task_id: str, submodule_task_id: str) -> int:
    """Manually link an existing parent task to a submodule task."""
    from vibey.operations.submodule import TaskPusher

    try:
        pusher = TaskPusher()

        console.print(f"[blue]Linking tasks...[/blue]")
        console.print(f"  Parent: {parent_task_id}")
        console.print(f"  Submodule: {submodule_task_id}")

        result = pusher.link_existing(
            parent_task_id=parent_task_id,
            submodule_task_id=submodule_task_id,
        )

        if result.success:
            console.print(f"[green]Tasks linked successfully[/green]")
        else:
            console.print(f"[red]Failed: {result.error}[/red]")
            return 1

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def submodule_unlink_cmd(parent_task_id: str) -> int:
    """Remove link between a parent task and its submodule task.

    Note: This does NOT delete the submodule task, only removes the link.
    """
    from vibey.operations.submodule import TaskPusher

    try:
        pusher = TaskPusher()

        console.print(f"[blue]Unlinking task: {parent_task_id}[/blue]")

        result = pusher.unlink(parent_task_id=parent_task_id)

        if result.success:
            console.print(f"[green]Link removed successfully[/green]")
            if result.submodule_task_id:
                console.print(f"  Submodule task preserved: {result.submodule_task_id}")
        else:
            console.print(f"[red]Failed: {result.error}[/red]")
            return 1

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


def submodule_blockers_cmd(severity: Optional[str], submodule: Optional[str]) -> int:
    """List blockers from submodules.

    Severity levels: critical, high, medium, low
    """
    from vibey.operations.submodule import ProgressAggregator
    from vibey.config import load_submodule_config

    try:
        config = load_submodule_config()

        if not config.submodules:
            console.print("[yellow]No submodules registered.[/yellow]")
            return 0

        aggregator = ProgressAggregator()
        result = aggregator.aggregate_all()

        blockers = result.active_blockers

        # Filter by severity
        if severity:
            blockers = [b for b in blockers if b.severity == severity]

        # Filter by submodule
        if submodule:
            submodule = submodule.replace("\\", "/").strip("/")
            blockers = [b for b in blockers if b.submodule_path == submodule]

        if not blockers:
            console.print("[green]No active blockers found.[/green]")
            return 0

        table = Table(title="Submodule Blockers")
        table.add_column("Submodule", style="cyan")
        table.add_column("Task", style="white")
        table.add_column("Blocker", style="yellow")
        table.add_column("Severity", style="red")

        for blocker in blockers:
            severity_color = {
                "critical": "red bold",
                "high": "red",
                "medium": "yellow",
                "low": "dim",
            }.get(blocker.severity, "white")

            table.add_row(
                blocker.submodule_path,
                blocker.task_id[:12] + "...",
                blocker.blocker_description[:40] + ("..." if len(blocker.blocker_description) > 40 else ""),
                f"[{severity_color}]{blocker.severity}[/{severity_color}]",
            )

        console.print(table)
        console.print()
        console.print(f"Total blockers: {len(blockers)}")

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def submodule_refresh_cmd(path: str) -> int:
    """Force refresh progress data for a single submodule."""
    from vibey.operations.submodule import ProgressAggregator
    from vibey.config import load_submodule_config, save_submodule_config
    from datetime import datetime, timezone

    try:
        config = load_submodule_config()

        # Normalize path
        path = path.replace("\\", "/").strip("/")

        # Check if submodule is registered
        sub_ref = config.get_submodule(path)
        if sub_ref is None:
            console.print(f"[yellow]Submodule not registered: {path}[/yellow]")
            return 1

        aggregator = ProgressAggregator()

        console.print(f"[blue]Refreshing progress for: {path}[/blue]")

        progress = aggregator.aggregate_submodule(path)

        console.print(f"[green]Progress refreshed:[/green]")
        console.print(f"  Tracks: {progress.tracks_completed}/{progress.tracks_total}")
        console.print(f"  Sprints: {progress.sprints_completed}/{progress.sprints_total}")
        console.print(f"  Tasks: {progress.tasks_completed}/{progress.tasks_total}")
        console.print(f"  Completion: {progress.completion_percent:.1f}%")

        # Update last_synced
        sub_ref.last_synced = datetime.now(timezone.utc)
        save_submodule_config(config)

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


# ============================================================================
# Cross-repo Dependency Commands
# ============================================================================


def submodule_add_dep_cmd(
    ticket_id: str,
    dependency_ref: str,
    dep_type: str,
    blocking: bool,
    reason: Optional[str],
) -> int:
    """Add a cross-repo dependency to a ticket.

    dependency_ref format: submodule_path:task_id
    Example: libs/core:01KC2D0JK7READW9KAK1HBX4B8
    """
    from vibey.operations.submodule import DependencyResolver

    try:
        # Parse dependency reference
        if ":" not in dependency_ref:
            console.print("[red]Invalid dependency_ref format. Use: submodule_path:task_id[/red]")
            return 1

        submodule_path, target_task_id = dependency_ref.split(":", 1)

        resolver = DependencyResolver()

        console.print(f"[blue]Adding cross-repo dependency...[/blue]")
        console.print(f"  From: {ticket_id}")
        console.print(f"  To: {dependency_ref}")
        console.print(f"  Type: {dep_type}")
        console.print(f"  Blocking: {blocking}")

        result = resolver.add_dependency(
            ticket_id=ticket_id,
            submodule_path=submodule_path,
            target_task_id=target_task_id,
            dependency_type=dep_type,
            blocking=blocking,
            reason=reason,
        )

        if result.success:
            console.print(f"[green]Dependency added successfully[/green]")
        else:
            console.print(f"[red]Failed: {result.error}[/red]")
            return 1

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def submodule_deps_cmd(ticket_id: str, direction: str) -> int:
    """List cross-repo dependencies for a ticket.

    Direction:
    - outgoing: Dependencies this ticket has on submodule tasks
    - incoming: Tasks in submodules that depend on this ticket
    - both: Show all dependencies
    """
    from vibey.operations.submodule import DependencyResolver

    try:
        resolver = DependencyResolver()

        deps = resolver.get_dependencies(
            ticket_id=ticket_id,
            direction=direction,
        )

        if not deps:
            console.print(f"[dim]No {direction} cross-repo dependencies found.[/dim]")
            return 0

        table = Table(title=f"Cross-repo Dependencies for {ticket_id}")
        table.add_column("Direction", style="blue")
        table.add_column("Submodule", style="cyan")
        table.add_column("Task ID", style="white")
        table.add_column("Type", style="yellow")
        table.add_column("Blocking", style="red")
        table.add_column("Status", style="green")

        for dep in deps:
            table.add_row(
                dep.direction,
                dep.submodule_path,
                dep.task_id[:12] + "...",
                dep.dependency_type,
                "Yes" if dep.blocking else "No",
                dep.status,
            )

        console.print(table)
        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def submodule_validate_deps_cmd() -> int:
    """Validate cross-repo dependencies.

    Checks for:
    - Circular dependencies (cycles)
    - Missing targets (broken links)
    - Stale references
    """
    from vibey.operations.submodule import DependencyResolver

    try:
        resolver = DependencyResolver()

        console.print("[blue]Validating cross-repo dependencies...[/blue]")

        result = resolver.validate_all()

        if result.is_valid:
            console.print("[green]All dependencies are valid![/green]")
        else:
            console.print("[red]Dependency issues found:[/red]")

            if result.cycles:
                console.print()
                console.print("[bold red]Circular Dependencies:[/bold red]")
                for cycle in result.cycles:
                    console.print(f"  {' -> '.join(cycle)}")

            if result.missing_targets:
                console.print()
                console.print("[bold yellow]Missing Targets:[/bold yellow]")
                for missing in result.missing_targets:
                    console.print(f"  {missing.source} -> {missing.target} (not found)")

            if result.stale_references:
                console.print()
                console.print("[bold dim]Stale References:[/bold dim]")
                for stale in result.stale_references:
                    console.print(f"  {stale.source} -> {stale.target}")

            return 1

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def submodule_dep_graph_cmd(output_format: str) -> int:
    """Visualize cross-repo dependency graph.

    Output formats:
    - text: ASCII tree visualization
    - dot: Graphviz DOT format
    - json: JSON representation
    """
    from vibey.operations.submodule import DependencyResolver

    try:
        resolver = DependencyResolver()

        console.print("[blue]Building dependency graph...[/blue]")

        graph = resolver.build_graph()

        if not graph.nodes:
            console.print("[dim]No cross-repo dependencies found.[/dim]")
            return 0

        if output_format == "text":
            console.print()
            console.print(Panel("[bold]Cross-repo Dependency Graph[/bold]"))
            console.print()

            for node in graph.nodes:
                deps = graph.get_dependencies(node)
                if deps:
                    console.print(f"[cyan]{node}[/cyan]")
                    for dep in deps:
                        arrow = "[red]──▶[/red]" if dep.blocking else "──>"
                        console.print(f"  {arrow} {dep.target} ({dep.submodule_path})")
                    console.print()

        elif output_format == "dot":
            dot_output = graph.to_dot()
            console.print(dot_output)

        elif output_format == "json":
            import json
            json_output = graph.to_json()
            console.print(json.dumps(json_output, indent=2))

        else:
            console.print(f"[red]Unknown format: {output_format}[/red]")
            return 1

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
