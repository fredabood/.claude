"""
Token usage reporting commands.

Provides commands for generating token usage reports, budget utilization,
and exporting token data in various formats.
"""

import csv
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

console = Console()


def _format_number(n: Optional[int]) -> str:
    """Format a number with commas or return '-' if None."""
    if n is None:
        return "-"
    return f"{n:,}"


def _format_percentage(numerator: Optional[int], denominator: Optional[int]) -> str:
    """Format a percentage or return '-' if not calculable."""
    if numerator is None or denominator is None or denominator == 0:
        return "-"
    pct = (numerator / denominator) * 100
    return f"{pct:.0f}%"


def _load_all_tasks(roadmap_root: Path) -> list:
    """Load all tasks from YAML files."""
    from vibey.roadmap.serialization.yaml_loader import load_task

    tasks = []
    tasks_dir = roadmap_root / "tasks"
    if tasks_dir.exists():
        for task_file in tasks_dir.glob("*.yaml"):
            try:
                task = load_task(task_file)
                tasks.append(task)
            except Exception:
                pass  # Skip malformed files
    return tasks


def _load_all_tracks(roadmap_root: Path) -> list:
    """Load all tracks from YAML files."""
    from vibey.roadmap.serialization.yaml_loader import load_track

    tracks = []
    tracks_dir = roadmap_root / "tracks"
    if tracks_dir.exists():
        for track_file in tracks_dir.glob("*.yaml"):
            try:
                track = load_track(track_file)
                tracks.append(track)
            except Exception:
                pass  # Skip malformed files
    return tracks


def _load_all_sprints(roadmap_root: Path) -> list:
    """Load all sprints from YAML files."""
    from vibey.roadmap.serialization.yaml_loader import load_sprint

    sprints = []
    sprints_dir = roadmap_root / "sprints"
    if sprints_dir.exists():
        for sprint_file in sprints_dir.glob("*.yaml"):
            try:
                sprint = load_sprint(sprint_file)
                sprints.append(sprint)
            except Exception:
                pass  # Skip malformed files
    return sprints


def _get_track_name(track_id: str, tracks: list) -> str:
    """Get track name by ID."""
    for track in tracks:
        if track.id == track_id:
            return track.name
    return track_id[:12] + "..."


def _aggregate_track_tokens(tasks: list, tracks: list) -> List[Dict[str, Any]]:
    """Aggregate token data by track."""
    track_data = {}

    for task in tasks:
        track_id = getattr(task, 'track_id', None)
        if not track_id:
            continue

        if track_id not in track_data:
            track_data[track_id] = {
                'track_id': track_id,
                'track_name': _get_track_name(track_id, tracks),
                'estimated_in': 0,
                'estimated_out': 0,
                'actual': 0,
                'task_count': 0,
            }

        # Get input/output token estimates
        input_tokens = getattr(task, 'input_tokens', None)
        output_tokens = getattr(task, 'output_tokens', None)

        if input_tokens and input_tokens.estimate:
            track_data[track_id]['estimated_in'] += input_tokens.estimate.target or 0

        if output_tokens and output_tokens.estimate:
            track_data[track_id]['estimated_out'] += output_tokens.estimate.target or 0

        # Get actual tokens
        actual = getattr(task, 'actual_tokens', None)
        if actual:
            track_data[track_id]['actual'] += actual

        # Also use simple estimated_tokens field if input/output not available
        simple_estimated = getattr(task, 'estimated_tokens', None)
        if simple_estimated and not (input_tokens or output_tokens):
            track_data[track_id]['estimated_in'] += simple_estimated

        track_data[track_id]['task_count'] += 1

    return list(track_data.values())


def _aggregate_task_type_tokens(tasks: list) -> List[Dict[str, Any]]:
    """Aggregate token data by task type."""
    type_data = {}

    for task in tasks:
        task_type = getattr(task, 'task_type', 'development')
        if hasattr(task_type, 'value'):
            task_type = task_type.value

        if task_type not in type_data:
            type_data[task_type] = {
                'task_type': task_type,
                'task_count': 0,
                'total_in': 0,
                'total_out': 0,
            }

        input_tokens = getattr(task, 'input_tokens', None)
        output_tokens = getattr(task, 'output_tokens', None)

        if input_tokens and input_tokens.estimate:
            type_data[task_type]['total_in'] += input_tokens.estimate.target or 0

        if output_tokens and output_tokens.estimate:
            type_data[task_type]['total_out'] += output_tokens.estimate.target or 0

        # Fall back to simple estimated_tokens
        simple_estimated = getattr(task, 'estimated_tokens', None)
        if simple_estimated and not (input_tokens or output_tokens):
            type_data[task_type]['total_in'] += simple_estimated

        type_data[task_type]['task_count'] += 1

    # Calculate averages
    result = []
    for type_name, data in type_data.items():
        count = data['task_count']
        result.append({
            'task_type': type_name,
            'task_count': count,
            'avg_in': data['total_in'] // count if count > 0 else 0,
            'avg_out': data['total_out'] // count if count > 0 else 0,
        })

    return result


def _generate_report_data(roadmap_root: Path) -> Dict[str, Any]:
    """Generate comprehensive token report data."""
    tasks = _load_all_tasks(roadmap_root)
    tracks = _load_all_tracks(roadmap_root)

    by_track = _aggregate_track_tokens(tasks, tracks)
    by_type = _aggregate_task_type_tokens(tasks)

    # Calculate totals
    total_estimated_in = sum(t['estimated_in'] for t in by_track)
    total_estimated_out = sum(t['estimated_out'] for t in by_track)
    total_actual = sum(t['actual'] for t in by_track)
    total_tasks = len(tasks)

    return {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_tasks': total_tasks,
            'total_estimated_input': total_estimated_in,
            'total_estimated_output': total_estimated_out,
            'total_actual': total_actual,
        },
        'by_track': by_track,
        'by_task_type': by_type,
    }


def tokens_report_cmd(
    output_format: str = "text",
    track_id: Optional[str] = None,
    include_empty: bool = False,
) -> int:
    """
    Generate token usage report.

    Shows token usage by track and by task type with estimates vs actuals.
    """
    root_dir = Path.cwd()
    roadmap_root = root_dir / ".vibey" / "roadmap"

    if not roadmap_root.exists():
        console.print("[red]Error: No roadmap found. Run 'vibey roadmap init' first.[/red]")
        return 1

    report_data = _generate_report_data(roadmap_root)

    # Filter by track if specified
    if track_id:
        report_data['by_track'] = [
            t for t in report_data['by_track']
            if t['track_id'] == track_id
        ]

    # Filter empty tracks unless included
    if not include_empty:
        report_data['by_track'] = [
            t for t in report_data['by_track']
            if t['task_count'] > 0
        ]

    if output_format == "json":
        print(json.dumps(report_data, indent=2))
        return 0

    if output_format == "csv":
        # Output two CSV sections
        output = io.StringIO()

        # By Track section
        output.write("# Token Usage by Track\n")
        writer = csv.DictWriter(
            output,
            fieldnames=['track_name', 'estimated_in', 'estimated_out', 'actual', 'task_count']
        )
        writer.writeheader()
        for row in report_data['by_track']:
            writer.writerow({
                'track_name': row['track_name'],
                'estimated_in': row['estimated_in'],
                'estimated_out': row['estimated_out'],
                'actual': row['actual'],
                'task_count': row['task_count'],
            })

        output.write("\n# Token Usage by Task Type\n")
        writer = csv.DictWriter(
            output,
            fieldnames=['task_type', 'task_count', 'avg_in', 'avg_out']
        )
        writer.writeheader()
        for row in report_data['by_task_type']:
            writer.writerow(row)

        print(output.getvalue())
        return 0

    # Text output (default)
    console.print("\n[bold]Token Usage Report[/bold]")
    console.print("=" * 60)
    console.print(f"Generated: {report_data['generated_at']}")

    summary = report_data['summary']
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Total Tasks:          {_format_number(summary['total_tasks'])}")
    console.print(f"  Total Est. Input:     {_format_number(summary['total_estimated_input'])}")
    console.print(f"  Total Est. Output:    {_format_number(summary['total_estimated_output'])}")
    console.print(f"  Total Actual:         {_format_number(summary['total_actual'])}")

    # By Track table
    console.print(f"\n[bold]By Track:[/bold]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Track", style="cyan", width=30)
    table.add_column("Est. In", justify="right")
    table.add_column("Est. Out", justify="right")
    table.add_column("Actual", justify="right")
    table.add_column("Tasks", justify="right")

    for row in sorted(report_data['by_track'], key=lambda x: x['estimated_in'], reverse=True):
        table.add_row(
            row['track_name'][:28] + ".." if len(row['track_name']) > 30 else row['track_name'],
            _format_number(row['estimated_in']),
            _format_number(row['estimated_out']),
            _format_number(row['actual']),
            str(row['task_count']),
        )

    console.print(table)

    # By Task Type table
    console.print(f"\n[bold]By Task Type:[/bold]")
    type_table = Table(show_header=True, header_style="bold")
    type_table.add_column("Type", style="cyan", width=20)
    type_table.add_column("Tasks", justify="right")
    type_table.add_column("Avg In", justify="right")
    type_table.add_column("Avg Out", justify="right")

    for row in sorted(report_data['by_task_type'], key=lambda x: x['task_count'], reverse=True):
        type_table.add_row(
            row['task_type'],
            str(row['task_count']),
            _format_number(row['avg_in']),
            _format_number(row['avg_out']),
        )

    console.print(type_table)

    return 0


def _calculate_budget_utilization(roadmap_root: Path) -> Dict[str, Any]:
    """Calculate budget utilization across all items."""
    tasks = _load_all_tasks(roadmap_root)
    tracks = _load_all_tracks(roadmap_root)
    sprints = _load_all_sprints(roadmap_root)

    # Track-level budgets
    track_budgets = []
    for track in tracks:
        budget = getattr(track, 'token_budget', None)
        estimated = getattr(track, 'estimated_tokens', None)
        actual = getattr(track, 'actual_tokens', None)

        # Also check input/output token budgets
        input_tokens = getattr(track, 'input_tokens', None)
        output_tokens = getattr(track, 'output_tokens', None)

        input_budget = input_tokens.budget if input_tokens else None
        output_budget = output_tokens.budget if output_tokens else None
        input_usage = input_tokens.usage if input_tokens else None
        output_usage = output_tokens.usage if output_tokens else None

        if budget or input_budget or output_budget:
            track_budgets.append({
                'id': track.id,
                'name': track.name,
                'type': 'track',
                'budget': budget,
                'input_budget': input_budget,
                'output_budget': output_budget,
                'estimated': estimated,
                'actual': actual,
                'input_usage': input_usage,
                'output_usage': output_usage,
            })

    # Sprint-level budgets
    sprint_budgets = []
    for sprint in sprints:
        budget = getattr(sprint, 'token_budget', None)
        estimated = getattr(sprint, 'estimated_tokens', None)
        actual = getattr(sprint, 'actual_tokens', None)

        input_tokens = getattr(sprint, 'input_tokens', None)
        output_tokens = getattr(sprint, 'output_tokens', None)

        input_budget = input_tokens.budget if input_tokens else None
        output_budget = output_tokens.budget if output_tokens else None
        input_usage = input_tokens.usage if input_tokens else None
        output_usage = output_tokens.usage if output_tokens else None

        if budget or input_budget or output_budget:
            sprint_budgets.append({
                'id': sprint.id,
                'name': sprint.name,
                'type': 'sprint',
                'budget': budget,
                'input_budget': input_budget,
                'output_budget': output_budget,
                'estimated': estimated,
                'actual': actual,
                'input_usage': input_usage,
                'output_usage': output_usage,
            })

    # Task-level budgets
    task_budgets = []
    for task in tasks:
        input_tokens = getattr(task, 'input_tokens', None)
        output_tokens = getattr(task, 'output_tokens', None)

        input_budget = input_tokens.budget if input_tokens else None
        output_budget = output_tokens.budget if output_tokens else None
        input_usage = input_tokens.usage if input_tokens else None
        output_usage = output_tokens.usage if output_tokens else None

        if input_budget or output_budget:
            task_budgets.append({
                'id': task.id,
                'name': task.title,
                'type': 'task',
                'input_budget': input_budget,
                'output_budget': output_budget,
                'input_usage': input_usage,
                'output_usage': output_usage,
                'estimated': getattr(task, 'estimated_tokens', None),
                'actual': getattr(task, 'actual_tokens', None),
            })

    return {
        'generated_at': datetime.now().isoformat(),
        'tracks': track_budgets,
        'sprints': sprint_budgets,
        'tasks': task_budgets,
    }


def tokens_budget_cmd(
    output_format: str = "text",
    show_all: bool = False,
) -> int:
    """
    Show budget utilization report.

    Displays items with budgets and their utilization status.
    """
    root_dir = Path.cwd()
    roadmap_root = root_dir / ".vibey" / "roadmap"

    if not roadmap_root.exists():
        console.print("[red]Error: No roadmap found. Run 'vibey roadmap init' first.[/red]")
        return 1

    budget_data = _calculate_budget_utilization(roadmap_root)

    if output_format == "json":
        print(json.dumps(budget_data, indent=2))
        return 0

    if output_format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=['type', 'id', 'name', 'budget', 'input_budget', 'output_budget',
                       'actual', 'input_usage', 'output_usage', 'utilization_pct']
        )
        writer.writeheader()

        for item_list in [budget_data['tracks'], budget_data['sprints'], budget_data['tasks']]:
            for item in item_list:
                budget = item.get('budget') or (
                    (item.get('input_budget') or 0) + (item.get('output_budget') or 0)
                )
                usage = item.get('actual') or (
                    (item.get('input_usage') or 0) + (item.get('output_usage') or 0)
                )
                util_pct = (usage / budget * 100) if budget and usage else 0

                writer.writerow({
                    'type': item['type'],
                    'id': item['id'],
                    'name': item['name'],
                    'budget': item.get('budget', ''),
                    'input_budget': item.get('input_budget', ''),
                    'output_budget': item.get('output_budget', ''),
                    'actual': item.get('actual', ''),
                    'input_usage': item.get('input_usage', ''),
                    'output_usage': item.get('output_usage', ''),
                    'utilization_pct': f"{util_pct:.1f}" if util_pct else '',
                })

        print(output.getvalue())
        return 0

    # Text output
    console.print("\n[bold]Budget Utilization Report[/bold]")
    console.print("=" * 70)
    console.print(f"Generated: {budget_data['generated_at']}")

    def _print_budget_table(items: list, title: str):
        if not items:
            console.print(f"\n[dim]No {title.lower()} with budgets configured.[/dim]")
            return

        console.print(f"\n[bold]{title}:[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Name", style="cyan", width=30)
        table.add_column("Budget", justify="right")
        table.add_column("Usage", justify="right")
        table.add_column("Utilization", justify="right")
        table.add_column("Status", justify="center")

        for item in items:
            # Calculate total budget and usage
            budget = item.get('budget') or (
                (item.get('input_budget') or 0) + (item.get('output_budget') or 0)
            )
            usage = item.get('actual') or (
                (item.get('input_usage') or 0) + (item.get('output_usage') or 0)
            )

            if budget == 0:
                continue

            util_pct = (usage / budget * 100) if budget else 0

            # Status indicator
            if util_pct >= 100:
                status = "[red]OVER[/red]"
            elif util_pct >= 80:
                status = "[yellow]WARN[/yellow]"
            elif util_pct > 0:
                status = "[green]OK[/green]"
            else:
                status = "[dim]-[/dim]"

            name = item['name']
            if len(name) > 28:
                name = name[:26] + ".."

            table.add_row(
                name,
                _format_number(budget),
                _format_number(usage) if usage else "-",
                f"{util_pct:.1f}%" if usage else "-",
                status,
            )

        console.print(table)

    _print_budget_table(budget_data['tracks'], "Tracks")
    _print_budget_table(budget_data['sprints'], "Sprints")
    _print_budget_table(budget_data['tasks'], "Tasks")

    # Summary
    all_items = budget_data['tracks'] + budget_data['sprints'] + budget_data['tasks']
    over_budget = sum(
        1 for item in all_items
        if (item.get('budget') or (item.get('input_budget') or 0) + (item.get('output_budget') or 0)) > 0
        and ((item.get('actual') or (item.get('input_usage') or 0) + (item.get('output_usage') or 0)) /
             (item.get('budget') or (item.get('input_budget') or 0) + (item.get('output_budget') or 0)) >= 1)
    )
    warning = sum(
        1 for item in all_items
        if (item.get('budget') or (item.get('input_budget') or 0) + (item.get('output_budget') or 0)) > 0
        and 0.8 <= ((item.get('actual') or (item.get('input_usage') or 0) + (item.get('output_usage') or 0)) /
                    (item.get('budget') or (item.get('input_budget') or 0) + (item.get('output_budget') or 0))) < 1
    )

    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Items with budgets: {len(all_items)}")
    if over_budget > 0:
        console.print(f"  [red]Over budget: {over_budget}[/red]")
    if warning > 0:
        console.print(f"  [yellow]Warning (>80%): {warning}[/yellow]")

    return 0
