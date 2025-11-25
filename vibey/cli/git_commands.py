"""
Git Analysis CLI Commands

Provides CLI commands for analyzing Git history and extracting roadmap references.

Task: git-integration-1-task-005
Task: git-integration-2-task-003 (git hooks management)
"""

import sys
import json
import shutil
from typing import Optional
from pathlib import Path
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from vibey.operations.git import (
    GitLogAnalyzer,
    VelocityCalculator,
    analyze_repository,
    quick_sprint_velocity,
    ParserConfig,
    TagParser,
    TagType,
    StateReconstructor,
    PreCommitHook,
    CommitMsgHook,
    TaskStatusUpdater,
    update_from_commit,
    update_from_recent_commits,
    BranchLinker,
    create_task_branch,
    PRDescriptionGenerator,
    generate_pr_description,
    SprintTagger,
    create_sprint_start_tag,
    create_sprint_end_tag,
    list_all_sprint_tags,
    GitPrimarySync,
    sync_from_git,
    TaskStateChange,
    SprintStateChange,
    SyncResult,
    ModeDetector,
    SourceOfTruthMode,
    detect_source_of_truth_mode,
    validate_git_strategy,
    get_mode_configuration,
    ErrorHandler,
    validate_roadmap,
    repair_roadmap,
    rollback_roadmap,
    TagRepairer,
    find_dangling_tags,
    repair_all_tags,
    move_tag,
)

console = Console()


def format_date(dt):
    """Format datetime for display."""
    if dt is None:
        return "N/A"
    return dt.strftime("%Y-%m-%d")


def format_percent(value, total):
    """Format percentage."""
    if total == 0:
        return "0%"
    return f"{(value / total * 100):.1f}%"


@click.group('git')
@click.pass_context
def git_group(ctx):
    """
    Analyze Git history for roadmap references.

    Extract task, sprint, and track references from commit messages,
    calculate velocity metrics, and analyze contributor activity.

    Examples:

      vibey git analyze                      # Analyze last 100 commits
      vibey git analyze --max 500            # Analyze last 500 commits
      vibey git analyze --since "2 weeks ago"
      vibey git tasks git-integration-1-task-001
      vibey git velocity git-integration-1
      vibey git contributors
    """
    pass


@git_group.command('analyze')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--max', 'max_count', type=int, default=100, help='Maximum commits to analyze')
@click.option('--since', help='Analyze commits after date (e.g., "2 weeks ago")')
@click.option('--until', help='Analyze commits before date')
@click.option('--ref-range', help='Commit range (e.g., "v1.0..v2.0")')
@click.option('--format', 'output_format', type=click.Choice(['summary', 'detailed', 'json']), default='summary',
              help='Output format')
@click.pass_context
def analyze_cmd(ctx, repo: str, max_count: int, since: Optional[str], until: Optional[str],
                ref_range: Optional[str], output_format: str):
    """
    Analyze Git history for roadmap references.

    Parses commit messages to extract task, sprint, and track references,
    and provides statistics on commit message formats and reference usage.

    Examples:

      vibey git analyze                     # Analyze last 100 commits
      vibey git analyze --max 500           # Analyze 500 commits
      vibey git analyze --since "1 month ago"
      vibey git analyze --ref-range "main..develop"
      vibey git analyze --format json      # JSON output
    """
    try:
        analyzer = GitLogAnalyzer(repo_path=repo)

        if not analyzer.is_git_repo():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        # Analyze commits
        result = analyzer.analyze(
            ref_range=ref_range,
            max_count=max_count,
            since=since,
            until=until,
        )

        if output_format == 'json':
            # JSON output
            print(json.dumps(result.to_dict(), indent=2))
            return

        # Summary output
        console.print()
        console.print(Panel(
            Text("Git History Analysis", style="bold blue"),
            border_style="blue"
        ))
        console.print()

        # Basic statistics
        table = Table(title="Commit Statistics", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Commits", str(result.parse_result.total_commits))
        table.add_row("Date Range", f"{format_date(result.start_date)} to {format_date(result.end_date)}")
        table.add_row("With Task References", f"{result.parse_result.commits_with_tasks} ({format_percent(result.parse_result.commits_with_tasks, result.parse_result.total_commits)})")
        table.add_row("Without References", f"{result.parse_result.commits_without_tasks} ({format_percent(result.parse_result.commits_without_tasks, result.parse_result.total_commits)})")
        table.add_row("Contributors", str(result.total_contributors))

        console.print(table)
        console.print()

        # Task references
        if result.parse_result.unique_tasks:
            console.print(f"[bold]Unique Tasks ({len(result.parse_result.unique_tasks)}):[/bold]")
            for task_id in sorted(result.parse_result.unique_tasks)[:20]:
                console.print(f"  • {task_id}")
            if len(result.parse_result.unique_tasks) > 20:
                console.print(f"  ... and {len(result.parse_result.unique_tasks) - 20} more")
            console.print()

        # Sprint references
        if result.parse_result.unique_sprints:
            console.print(f"[bold]Unique Sprints ({len(result.parse_result.unique_sprints)}):[/bold]")
            for sprint_id in sorted(result.parse_result.unique_sprints):
                console.print(f"  • {sprint_id}")
            console.print()

        # Format usage
        if result.parse_result.format_usage:
            console.print("[bold]Commit Message Formats:[/bold]")
            for format_name, count in sorted(result.parse_result.format_usage.items(), key=lambda x: x[1], reverse=True):
                pct = format_percent(count, result.parse_result.total_commits)
                console.print(f"  {format_name:15s}: {count:4d} ({pct})")
            console.print()

        # Detailed output
        if output_format == 'detailed':
            console.print("[bold]Recent Commits:[/bold]")
            for commit in result.commits[:10]:
                console.print(f"\n  {commit.sha[:7]} - {commit.author_name} ({format_date(commit.date)})")
                console.print(f"    {commit.message.splitlines()[0]}")
                if commit.parsed and commit.parsed.tasks:
                    for task in commit.parsed.tasks:
                        status_str = f"[{task.status.value}]" if task.status else ""
                        console.print(f"      → {task.task_id} {status_str}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@git_group.command('tasks')
@click.argument('task_id')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
@click.pass_context
def tasks_cmd(ctx, task_id: str, repo: str, output_format: str):
    """
    Show commits for a specific task.

    Lists all commits that reference the specified task ID, including
    commit details, contributors, and status changes.

    Examples:

      vibey git tasks git-integration-1-task-001
      vibey git tasks task-001 --format json
    """
    try:
        analyzer = GitLogAnalyzer(repo_path=repo)

        if not analyzer.is_git_repo():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        # Find commits for task
        commits = analyzer.find_commits_for_task(task_id)

        if output_format == 'json':
            data = [c.to_dict() for c in commits]
            print(json.dumps(data, indent=2))
            return

        if not commits:
            console.print(f"[yellow]No commits found for task:[/yellow] {task_id}")
            return

        # Sort by date
        commits.sort(key=lambda c: c.date)

        console.print()
        console.print(f"[bold]Commits for Task:[/bold] {task_id}")
        console.print(f"Total: {len(commits)} commits\n")

        # Create table
        table = Table(show_header=True)
        table.add_column("Date", style="cyan")
        table.add_column("SHA", style="yellow")
        table.add_column("Author", style="green")
        table.add_column("Message", style="white")
        table.add_column("Status", style="magenta")

        for commit in commits:
            # Get status from parsed commit
            status = ""
            if commit.parsed:
                for task_ref in commit.parsed.tasks:
                    if task_ref.task_id == task_id and task_ref.status:
                        status = task_ref.status.value
                        break

            message = commit.message.splitlines()[0]
            if len(message) > 50:
                message = message[:47] + "..."

            table.add_row(
                format_date(commit.date),
                commit.sha[:7],
                commit.author_name,
                message,
                status
            )

        console.print(table)

        # Summary
        contributors = set(c.author_name for c in commits)
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Contributors: {len(contributors)}")
        console.print(f"  First commit: {format_date(commits[0].date)}")
        console.print(f"  Last commit: {format_date(commits[-1].date)}")
        console.print(f"  Duration: {(commits[-1].date - commits[0].date).days + 1} days")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@git_group.command('velocity')
@click.argument('sprint_id')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--start-ref', help='Starting ref (e.g., tag or commit)')
@click.option('--end-ref', help='Ending ref')
@click.option('--start-date', help='Starting date')
@click.option('--end-date', help='Ending date')
@click.option('--format', 'output_format', type=click.Choice(['summary', 'detailed', 'json']), default='summary',
              help='Output format')
@click.pass_context
def velocity_cmd(ctx, sprint_id: str, repo: str, start_ref: Optional[str], end_ref: Optional[str],
                 start_date: Optional[str], end_date: Optional[str], output_format: str):
    """
    Calculate sprint velocity metrics.

    Analyzes commits for a sprint and calculates velocity metrics including
    commit frequency, task completion rate, contributor activity, and code volume.

    Examples:

      vibey git velocity git-integration-1
      vibey git velocity sprint-1 --start-ref sprint-1/start --end-ref sprint-1/end
      vibey git velocity sprint-2 --start-date "2024-01-01" --end-date "2024-01-15"
      vibey git velocity sprint-3 --format json
    """
    try:
        calculator = VelocityCalculator(repo_path=repo)

        if not calculator.analyzer.is_git_repo():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        # Calculate velocity
        velocity = calculator.calculate_sprint_velocity(
            sprint_id=sprint_id,
            start_ref=start_ref,
            end_ref=end_ref,
            start_date=start_date,
            end_date=end_date,
        )

        if output_format == 'json':
            print(json.dumps(velocity.to_dict(), indent=2))
            return

        if velocity.total_commits == 0:
            console.print(f"[yellow]No commits found for sprint:[/yellow] {sprint_id}")
            return

        console.print()
        console.print(Panel(
            Text(f"Sprint Velocity: {sprint_id}", style="bold blue"),
            border_style="blue"
        ))
        console.print()

        # Time period
        table1 = Table(title="Time Period", show_header=False)
        table1.add_column("Metric", style="cyan")
        table1.add_column("Value", style="green")

        table1.add_row("Start Date", format_date(velocity.start_date))
        table1.add_row("End Date", format_date(velocity.end_date))
        table1.add_row("Duration", f"{velocity.duration_days:.1f} days")

        console.print(table1)
        console.print()

        # Commit metrics
        table2 = Table(title="Commit Metrics", show_header=False)
        table2.add_column("Metric", style="cyan")
        table2.add_column("Value", style="green")

        table2.add_row("Total Commits", str(velocity.total_commits))
        table2.add_row("Commits/Day", f"{velocity.commits_per_day:.2f}")

        console.print(table2)
        console.print()

        # Task metrics
        table3 = Table(title="Task Metrics", show_header=False)
        table3.add_column("Metric", style="cyan")
        table3.add_column("Value", style="green")

        table3.add_row("Tasks Worked", str(velocity.tasks_worked))
        table3.add_row("Tasks Completed", str(velocity.tasks_completed))
        table3.add_row("Completion Rate", format_percent(velocity.tasks_completed, velocity.tasks_worked))

        console.print(table3)
        console.print()

        # Contributor metrics
        table4 = Table(title="Contributor Metrics", show_header=False)
        table4.add_column("Metric", style="cyan")
        table4.add_column("Value", style="green")

        table4.add_row("Total Contributors", str(velocity.total_contributors))
        table4.add_row("Avg Commits/Contributor", f"{velocity.avg_commits_per_contributor:.2f}")

        console.print(table4)
        console.print()

        # Code metrics
        table5 = Table(title="Code Metrics", show_header=False)
        table5.add_column("Metric", style="cyan")
        table5.add_column("Value", style="green")

        table5.add_row("Files Changed", str(velocity.total_files_changed))
        table5.add_row("Insertions", f"+{velocity.total_insertions}")
        table5.add_row("Deletions", f"-{velocity.total_deletions}")
        table5.add_row("Net Lines", f"{velocity.net_lines:+d}")

        console.print(table5)
        console.print()

        # Detailed output
        if output_format == 'detailed' and velocity.task_metrics:
            console.print("[bold]Per-Task Breakdown:[/bold]\n")

            task_table = Table(show_header=True)
            task_table.add_column("Task ID", style="cyan")
            task_table.add_column("Commits", style="yellow", justify="right")
            task_table.add_column("Contributors", style="green", justify="right")
            task_table.add_column("Duration", style="blue", justify="right")
            task_table.add_column("Status", style="magenta")

            for task in velocity.task_metrics:
                status_icon = "✓" if task.completed else "○"
                duration = f"{task.duration_days:.0f}d" if task.duration_days else "N/A"

                task_table.add_row(
                    task.task_id,
                    str(task.commits),
                    str(task.contributors),
                    duration,
                    status_icon
                )

            console.print(task_table)
            console.print()

        # Top contributors
        if velocity.contributor_commits:
            console.print("[bold]Top Contributors:[/bold]")
            sorted_contributors = sorted(
                velocity.contributor_commits.items(),
                key=lambda x: x[1],
                reverse=True
            )
            for contributor, count in sorted_contributors[:5]:
                console.print(f"  {contributor}: {count} commits")
            if len(sorted_contributors) > 5:
                console.print(f"  ... and {len(sorted_contributors) - 5} more")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@git_group.command('contributors')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--since', help='Show contributions after date')
@click.option('--until', help='Show contributions before date')
@click.option('--max', 'max_count', type=int, default=500, help='Maximum commits to analyze')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
@click.pass_context
def contributors_cmd(ctx, repo: str, since: Optional[str], until: Optional[str],
                     max_count: int, output_format: str):
    """
    Show contributor activity and statistics.

    Analyzes contributor activity including commit counts, tasks worked,
    and code contribution volume.

    Examples:

      vibey git contributors
      vibey git contributors --since "1 month ago"
      vibey git contributors --format json
    """
    try:
        analyzer = GitLogAnalyzer(repo_path=repo)

        if not analyzer.is_git_repo():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        # Get commits
        commits = analyzer.get_commits(
            max_count=max_count,
            since=since,
            until=until
        )

        # Parse commits
        for commit in commits:
            commit.parsed = analyzer.parser.parse(commit.message, commit.sha)

        # Collect contributor statistics
        from collections import defaultdict

        contributor_stats = defaultdict(lambda: {
            'commits': 0,
            'tasks': set(),
            'insertions': 0,
            'deletions': 0,
        })

        for commit in commits:
            contributor = f"{commit.author_name} <{commit.author_email}>"
            contributor_stats[contributor]['commits'] += 1
            contributor_stats[contributor]['insertions'] += commit.insertions
            contributor_stats[contributor]['deletions'] += commit.deletions

            for task_ref in commit.parsed.tasks:
                contributor_stats[contributor]['tasks'].add(task_ref.task_id)

        if output_format == 'json':
            data = {
                contributor: {
                    'commits': stats['commits'],
                    'tasks': list(stats['tasks']),
                    'insertions': stats['insertions'],
                    'deletions': stats['deletions'],
                }
                for contributor, stats in contributor_stats.items()
            }
            print(json.dumps(data, indent=2))
            return

        console.print()
        console.print(f"[bold]Contributor Activity[/bold]")
        console.print(f"Period: {since or 'all time'} to {until or 'now'}")
        console.print()

        # Create table
        table = Table(show_header=True)
        table.add_column("Contributor", style="cyan")
        table.add_column("Commits", style="yellow", justify="right")
        table.add_column("Tasks", style="green", justify="right")
        table.add_column("Insertions", style="blue", justify="right")
        table.add_column("Deletions", style="red", justify="right")

        # Sort by commit count
        sorted_contributors = sorted(
            contributor_stats.items(),
            key=lambda x: x[1]['commits'],
            reverse=True
        )

        for contributor, stats in sorted_contributors:
            table.add_row(
                contributor,
                str(stats['commits']),
                str(len(stats['tasks'])),
                f"+{stats['insertions']}",
                f"-{stats['deletions']}"
            )

        console.print(table)
        console.print(f"\n[dim]Total contributors: {len(contributor_stats)}[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@git_group.command('tags')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--sprint', 'sprint_id', help='Show tags for specific sprint')
@click.option('--task', 'task_id', help='Show tags for specific task')
@click.option('--track', 'track_id', help='Show tags for specific track')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
@click.pass_context
def tags_cmd(ctx, repo: str, sprint_id: Optional[str], task_id: Optional[str],
             track_id: Optional[str], output_format: str):
    """
    List Vibey roadmap tags.

    Shows all Vibey tags (sprint boundaries, task markers) with filtering options.

    Examples:

      vibey git tags                                # List all Vibey tags
      vibey git tags --sprint git-integration-1     # Sprint tags
      vibey git tags --task git-integration-1-task-001  # Task tags
      vibey git tags --format json
    """
    try:
        parser = TagParser(repo_path=repo)

        if not parser.analyzer.is_git_repo():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        # Get tags based on filters
        if sprint_id:
            tags = parser.get_sprint_tags(sprint_id)
        elif task_id:
            tags = parser.get_task_tags(task_id)
        elif track_id:
            all_tags = parser.get_vibey_tags()
            tags = [t for t in all_tags if t.track_id == track_id]
        else:
            tags = parser.get_vibey_tags()

        if output_format == 'json':
            data = [t.to_dict() for t in tags]
            print(json.dumps(data, indent=2))
            return

        if not tags:
            console.print("[yellow]No Vibey tags found[/yellow]")
            if sprint_id:
                console.print(f"\nSuggested tags for sprint '{sprint_id}':")
                start, end = parser.suggest_sprint_tags(sprint_id)
                console.print(f"  Start: {start}")
                console.print(f"  End:   {end}")
            return

        console.print()
        console.print(f"[bold]Vibey Tags ({len(tags)})[/bold]\n")

        # Group by type
        by_type = {}
        for tag in tags:
            tag_type = tag.tag_type.value
            if tag_type not in by_type:
                by_type[tag_type] = []
            by_type[tag_type].append(tag)

        # Display by type
        for tag_type, tag_list in sorted(by_type.items()):
            console.print(f"[bold cyan]{tag_type.replace('_', ' ').title()}:[/bold cyan]")

            table = Table(show_header=True, show_lines=False)
            table.add_column("Tag Name", style="yellow")
            table.add_column("SHA", style="green")
            table.add_column("ID", style="cyan")

            for tag in sorted(tag_list, key=lambda t: t.tag_info.name):
                id_str = tag.sprint_id or tag.task_id or tag.track_id or ""
                table.add_row(
                    tag.tag_info.name,
                    tag.tag_info.sha[:7],
                    id_str
                )

            console.print(table)
            console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@git_group.command('tag-range')
@click.argument('item_id')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--type', 'item_type', type=click.Choice(['sprint', 'task']), default='sprint',
              help='Type of item (sprint or task)')
@click.option('--format', 'output_format', type=click.Choice(['summary', 'detailed', 'json']), default='summary',
              help='Output format')
@click.pass_context
def tag_range_cmd(ctx, item_id: str, repo: str, item_type: str, output_format: str):
    """
    Get commits between boundary tags.

    Retrieves commits between start/end tags for a sprint or task.
    This is more efficient than parsing all commit messages.

    Examples:

      vibey git tag-range git-integration-1 --type sprint
      vibey git tag-range git-integration-1-task-001 --type task
      vibey git tag-range sprint-1 --format detailed
    """
    try:
        parser = TagParser(repo_path=repo)

        if not parser.analyzer.is_git_repo():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        # Get commits based on type
        if item_type == 'sprint':
            start_tag, end_tag = parser.get_sprint_boundary_tags(item_id)
            commits = parser.get_commits_for_sprint_by_tags(item_id)
        else:  # task
            start_tag, end_tag = parser.get_task_boundary_tags(item_id)
            commits = parser.get_commits_for_task_by_tags(item_id)

        if not start_tag or not end_tag:
            console.print(f"[yellow]No boundary tags found for {item_type}:[/yellow] {item_id}")

            if item_type == 'sprint':
                console.print(f"\nSuggested tags:")
                start_name, end_name = parser.suggest_sprint_tags(item_id)
                console.print(f"  Start: {start_name}")
                console.print(f"  End:   {end_name}")
            return

        if not commits:
            console.print(f"[yellow]No commits found between tags[/yellow]")
            return

        if output_format == 'json':
            data = [c.to_dict() for c in commits]
            print(json.dumps(data, indent=2))
            return

        console.print()
        console.print(f"[bold]Commits for {item_type}:[/bold] {item_id}")
        console.print(f"Range: {start_tag.tag_info.name} .. {end_tag.tag_info.name}")
        console.print(f"Total: {len(commits)} commits\n")

        if output_format == 'summary':
            # Summary table
            table = Table(show_header=True)
            table.add_column("Date", style="cyan")
            table.add_column("SHA", style="yellow")
            table.add_column("Author", style="green")
            table.add_column("Message", style="white")

            for commit in commits[:20]:  # Limit to 20
                message = commit.message.splitlines()[0]
                if len(message) > 60:
                    message = message[:57] + "..."

                table.add_row(
                    format_date(commit.date),
                    commit.sha[:7],
                    commit.author_name,
                    message
                )

            console.print(table)

            if len(commits) > 20:
                console.print(f"\n[dim]... and {len(commits) - 20} more commits[/dim]")

        else:  # detailed
            for commit in commits:
                console.print(f"[yellow]{commit.sha[:7]}[/yellow] - {commit.author_name} ({format_date(commit.date)})")
                console.print(f"  {commit.message.splitlines()[0]}")
                if commit.files_changed > 0:
                    console.print(f"  Files: {commit.files_changed}, +{commit.insertions}, -{commit.deletions}")
                console.print()

        # Summary
        console.print(f"[bold]Summary:[/bold]")
        console.print(f"  Period: {format_date(commits[0].date)} to {format_date(commits[-1].date)}")
        console.print(f"  Duration: {(commits[-1].date - commits[0].date).days + 1} days")
        console.print(f"  Contributors: {len(set(c.author_name for c in commits))}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@git_group.command('state-at')
@click.argument('ref')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--item', help='Show specific item (task/sprint/track ID)')
@click.option('--format', 'output_format', type=click.Choice(['summary', 'detailed', 'json']), default='summary',
              help='Output format')
@click.pass_context
def state_at_cmd(ctx, ref: str, repo: str, item: Optional[str], output_format: str):
    """
    Show roadmap state at a specific ref.

    Reconstructs the roadmap state at any point in history by reading
    YAML files at that commit. Supports commits, tags, branches, and dates.

    Examples:

      vibey git state-at HEAD~10                # 10 commits ago
      vibey git state-at v1.0.0                 # At tag
      vibey git state-at 2024-01-15             # At date
      vibey git state-at abc1234 --item task-001  # Specific task
      vibey git state-at main --format json
    """
    try:
        reconstructor = StateReconstructor(repo_path=repo)

        if not reconstructor.analyzer.is_git_repo():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        # Get state at ref
        state = reconstructor.get_state_at(ref)

        if output_format == 'json':
            if item:
                # Show specific item
                item_data = (state.tasks.get(item) or
                           state.sprints.get(item) or
                           state.tracks.get(item))
                print(json.dumps(item_data, indent=2))
            else:
                print(json.dumps(state.to_dict(), indent=2))
            return

        console.print()
        console.print(Panel(
            Text(f"State at {ref}", style="bold blue"),
            subtitle=f"{state.sha[:7]} - {format_date(state.date)}",
            border_style="blue"
        ))
        console.print()

        if item:
            # Show specific item
            item_data = (state.tasks.get(item) or
                        state.sprints.get(item) or
                        state.tracks.get(item))

            if not item_data:
                console.print(f"[yellow]Item not found:[/yellow] {item}")
                return

            console.print(f"[bold]{item}[/bold]\n")
            for key, value in item_data.items():
                if key != 'id':
                    console.print(f"  {key}: {value}")

        else:
            # Show summary
            console.print(f"[bold]Tracks:[/bold] {len(state.tracks)}")
            for track_id in sorted(state.tracks.keys())[:10]:
                console.print(f"  • {track_id}")
            if len(state.tracks) > 10:
                console.print(f"  ... and {len(state.tracks) - 10} more")

            console.print()
            console.print(f"[bold]Sprints:[/bold] {len(state.sprints)}")
            for sprint_id in sorted(state.sprints.keys())[:10]:
                sprint = state.sprints[sprint_id]
                status = sprint.get('status', 'unknown')
                console.print(f"  • {sprint_id} ({status})")
            if len(state.sprints) > 10:
                console.print(f"  ... and {len(state.sprints) - 10} more")

            console.print()
            console.print(f"[bold]Tasks:[/bold] {len(state.tasks)}")

            # Group by status
            by_status = {}
            for task_id, task in state.tasks.items():
                status = task.get('status', 'unknown')
                if status not in by_status:
                    by_status[status] = []
                by_status[status].append(task_id)

            for status, task_list in sorted(by_status.items()):
                console.print(f"  {status}: {len(task_list)}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@git_group.command('history')
@click.argument('item_id')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--type', 'item_type', type=click.Choice(['task', 'sprint', 'track']), default='task',
              help='Type of item')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
@click.pass_context
def history_cmd(ctx, item_id: str, repo: str, item_type: str, output_format: str):
    """
    Show change history for an item.

    Tracks how a task, sprint, or track changed over time by analyzing
    all commits and reconstructing state at each point.

    Examples:

      vibey git history git-integration-1-task-001
      vibey git history sprint-1 --type sprint
      vibey git history my-track --type track --format json
    """
    try:
        reconstructor = StateReconstructor(repo_path=repo)

        if not reconstructor.analyzer.is_git_repo():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        # Get history
        changes = reconstructor.get_history(item_id, item_type)

        if output_format == 'json':
            data = [c.to_dict() for c in changes]
            print(json.dumps(data, indent=2))
            return

        if not changes:
            console.print(f"[yellow]No history found for {item_type}:[/yellow] {item_id}")
            return

        console.print()
        console.print(f"[bold]Change History for {item_type}:[/bold] {item_id}")
        console.print(f"Total changes: {len(changes)}\n")

        # Create table
        table = Table(show_header=True)
        table.add_column("Date", style="cyan")
        table.add_column("SHA", style="yellow")
        table.add_column("Field", style="green")
        table.add_column("Old Value", style="red")
        table.add_column("New Value", style="blue")

        for change in changes:
            table.add_row(
                format_date(change.commit_date),
                change.commit_sha[:7],
                change.field,
                str(change.old_value),
                str(change.new_value)
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@git_group.command('progress')
@click.argument('sprint_id')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--interval', type=int, default=10, help='Sample every N commits')
@click.option('--format', 'output_format', type=click.Choice(['chart', 'table', 'json']), default='chart',
              help='Output format')
@click.pass_context
def progress_cmd(ctx, sprint_id: str, repo: str, interval: int, output_format: str):
    """
    Show sprint progress over time (burndown chart).

    Samples the sprint state at regular intervals to show how progress
    evolved over time. Useful for generating burndown charts.

    Examples:

      vibey git progress git-integration-1
      vibey git progress sprint-1 --interval 5  # Sample every 5 commits
      vibey git progress sprint-2 --format table
      vibey git progress sprint-3 --format json
    """
    try:
        reconstructor = StateReconstructor(repo_path=repo)

        if not reconstructor.analyzer.is_git_repo():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        # Get progress timeline
        timeline = reconstructor.get_progress_timeline(sprint_id, sample_interval=interval)

        if output_format == 'json':
            data = [p.to_dict() for p in timeline]
            print(json.dumps(data, indent=2))
            return

        if not timeline:
            console.print(f"[yellow]No progress data found for sprint:[/yellow] {sprint_id}")
            return

        console.print()
        console.print(f"[bold]Progress Timeline for Sprint:[/bold] {sprint_id}")
        console.print(f"Sample points: {len(timeline)}\n")

        if output_format == 'chart':
            # ASCII bar chart
            max_width = 50
            for point in timeline:
                pct = point.completion_percent
                bar_width = int((pct / 100) * max_width)
                bar = "█" * bar_width + "░" * (max_width - bar_width)
                console.print(f"{format_date(point.date)}  {bar}  {pct:.0f}% ({point.tasks_completed}/{point.tasks_total})")

        else:  # table
            table = Table(show_header=True)
            table.add_column("Date", style="cyan")
            table.add_column("SHA", style="yellow")
            table.add_column("Completed", style="green", justify="right")
            table.add_column("Total", style="blue", justify="right")
            table.add_column("Progress", style="magenta", justify="right")

            for point in timeline:
                table.add_row(
                    format_date(point.date),
                    point.sha[:7],
                    str(point.tasks_completed),
                    str(point.tasks_total),
                    f"{point.completion_percent:.0f}%"
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@git_group.command('rollback')
@click.argument('ref')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--dry-run', is_flag=True, default=True, help='Show what would be restored (default)')
@click.option('--execute', is_flag=True, help='Actually perform the rollback')
@click.pass_context
def rollback_cmd(ctx, ref: str, repo: str, dry_run: bool, execute: bool):
    """
    Rollback roadmap to state at ref.

    Restores all roadmap YAML files to their state at a specific commit.
    By default runs in dry-run mode to show what would change.

    Examples:

      vibey git rollback HEAD~5                 # Dry-run (default)
      vibey git rollback v1.0.0 --execute       # Actually rollback
      vibey git rollback abc1234 --execute
    """
    try:
        reconstructor = StateReconstructor(repo_path=repo)

        if not reconstructor.analyzer.is_git_repo():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        # Override dry_run if execute is specified
        if execute:
            dry_run = False

        # Perform rollback
        restore_status = reconstructor.rollback(ref, dry_run=dry_run)

        console.print()
        if dry_run:
            console.print(Panel(
                Text(f"Dry Run: Rollback to {ref}", style="bold yellow"),
                subtitle="Use --execute to actually perform rollback",
                border_style="yellow"
            ))
        else:
            console.print(Panel(
                Text(f"Rollback to {ref}", style="bold green"),
                border_style="green"
            ))
        console.print()

        # Show results
        console.print(f"[bold]Files to restore:[/bold] {len(restore_status)}\n")

        for file_path, status in sorted(restore_status.items())[:20]:
            if "error" in status:
                console.print(f"  [red]✗[/red] {file_path}: {status}")
            else:
                console.print(f"  [green]✓[/green] {file_path}: {status}")

        if len(restore_status) > 20:
            console.print(f"\n  ... and {len(restore_status) - 20} more files")

        if dry_run:
            console.print(f"\n[yellow]This was a dry run. Use --execute to actually rollback.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@git_group.command('update-status')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--commit', 'commit_sha', help='Process specific commit SHA')
@click.option('--message', 'commit_message', help='Commit message (with --commit)')
@click.option('--recent', type=int, default=10, help='Process N recent commits')
@click.option('--dry-run', is_flag=True, help='Show what would be updated without making changes')
@click.option('--force', is_flag=True, help='Allow updates even if task already in target status')
@click.pass_context
def update_status_cmd(ctx, repo: str, commit_sha: Optional[str], commit_message: Optional[str],
                      recent: int, dry_run: bool, force: bool):
    """
    Update task status based on commit messages.

    Parses commit messages for status indicators (completes, starts, blocks)
    and automatically updates task status in roadmap YAML files.

    Status Keywords:
      - "completes task-id" → mark task completed
      - "starts task-id" → mark task in_progress
      - "blocks task-id" → mark task blocked

    Examples:

      vibey git update-status                    # Process last 10 commits
      vibey git update-status --recent 50         # Process last 50 commits
      vibey git update-status --commit abc1234 --message "completes task-001"
      vibey git update-status --dry-run           # Preview changes
      vibey git update-status --force             # Update even if already at status
    """
    try:
        updater = TaskStatusUpdater(repo_path=repo)

        # Process specific commit or recent commits
        if commit_sha:
            if not commit_message:
                console.print("[red]Error:[/red] --message required when using --commit")
                sys.exit(1)

            result = updater.process_commit(commit_sha, commit_message, dry_run=dry_run, force=force)
        else:
            result = updater.process_recent_commits(max_count=recent, dry_run=dry_run, force=force)

        console.print()
        mode_text = "Dry Run: " if dry_run else ""
        console.print(Panel(
            Text(f"{mode_text}Task Status Updates", style="bold blue"),
            border_style="blue"
        ))
        console.print()

        # Summary
        table = Table(title="Summary", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")

        table.add_row("Total Updates", str(result.total_updates))
        table.add_row("Successful", str(result.successful_updates))
        table.add_row("Failed", str(result.failed_updates))
        table.add_row("Skipped", str(result.skipped_updates))

        console.print(table)
        console.print()

        # Show updates
        if result.updates:
            updates_table = Table(show_header=True)
            updates_table.add_column("Task ID", style="cyan")
            updates_table.add_column("Status", style="yellow")
            updates_table.add_column("Sprint", style="blue")
            updates_table.add_column("Result", style="green")

            for update in result.updates:
                status_str = f"{update.old_status} → {update.new_status}"

                if update.applied:
                    result_str = "[green]✓ Applied[/green]"
                elif update.error:
                    result_str = f"[yellow]⚠ {update.error}[/yellow]"
                else:
                    result_str = "[dim]○ Skipped[/dim]"

                updates_table.add_row(
                    update.task_id,
                    status_str,
                    update.sprint_id,
                    result_str
                )

            console.print(updates_table)
            console.print()

        # Show errors
        if result.errors:
            console.print("[bold red]Errors:[/bold red]")
            for error in result.errors:
                console.print(f"  [red]✗[/red] {error}")
            console.print()

        if dry_run and result.successful_updates > 0:
            console.print("[yellow]This was a dry run. Use without --dry-run to apply changes.[/yellow]")

        if result.failed_updates > 0:
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@git_group.command('link-commit')
@click.argument('task_id')
@click.argument('commit_sha')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--status', type=click.Choice(['completed', 'in_progress', 'blocked']),
              help='Update task status')
@click.option('--dry-run', is_flag=True, help='Show what would be updated')
@click.pass_context
def link_commit_cmd(ctx, task_id: str, commit_sha: str, repo: str,
                    status: Optional[str], dry_run: bool):
    """
    Link a commit to a task and optionally update status.

    Manually records a commit SHA in a task's commits list and
    optionally updates the task status.

    Examples:

      vibey git link-commit task-001 abc1234
      vibey git link-commit task-001 abc1234 --status completed
      vibey git link-commit task-001 abc1234 --dry-run
    """
    try:
        updater = TaskStatusUpdater(repo_path=repo)

        # Find task file
        task_file = updater.find_task_file(task_id)

        if not task_file:
            console.print(f"[red]Error:[/red] Task {task_id} not found in roadmap")
            sys.exit(1)

        # Load task
        task = updater.get_task_from_file(task_file, task_id)

        if not task:
            console.print(f"[red]Error:[/red] Could not load task {task_id}")
            sys.exit(1)

        old_status = task.get("status", "not_started")
        new_status = status or old_status

        console.print()
        mode_text = "Dry Run: " if dry_run else ""
        console.print(Panel(
            Text(f"{mode_text}Link Commit to Task", style="bold blue"),
            border_style="blue"
        ))
        console.print()

        console.print(f"[bold]Task:[/bold] {task_id}")
        console.print(f"[bold]Commit:[/bold] {commit_sha}")
        console.print(f"[bold]Status:[/bold] {old_status} → {new_status}")
        console.print()

        if not dry_run:
            # Apply update
            success, error = updater.update_task_in_file(
                task_file,
                task_id,
                new_status,
                commit_sha,
                dry_run=False
            )

            if success:
                console.print("[green]✓ Successfully linked commit to task[/green]")
                if status:
                    console.print(f"[green]✓ Updated task status to {status}[/green]")
            else:
                console.print(f"[red]✗ Failed:[/red] {error}")
                sys.exit(1)
        else:
            console.print("[yellow]Dry run - no changes made[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@git_group.command('pr-description')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--task', 'task_id', help='Task ID (auto-detects from branch if not provided)')
@click.option('--output', type=click.Path(), help='Output file (prints to stdout if not provided)')
@click.option('--copy', is_flag=True, help='Copy to clipboard')
@click.pass_context
def pr_description_cmd(ctx, repo: str, task_id: Optional[str], output: Optional[str], copy: bool):
    """
    Generate PR description from task context.

    Reads task information from roadmap and generates a formatted
    PR description including task details, checklist, related tasks,
    and quality gates.

    Auto-detects task from current branch name if --task not provided.

    Examples:

      vibey git pr-description                           # Auto-detect from branch
      vibey git pr-description --task git-integration-2-task-006
      vibey git pr-description --output pr-body.md       # Save to file
      vibey git pr-description --copy                    # Copy to clipboard
      gh pr create --body "$(vibey git pr-description)"  # Use with GitHub CLI
    """
    try:
        generator = PRDescriptionGenerator(repo_path=repo)

        # Auto-detect task from branch if not provided
        if not task_id:
            task_id = generator.detect_task_from_branch()

            if not task_id:
                console.print("[red]Error:[/red] Could not detect task from branch name")
                console.print("[yellow]Tip:[/yellow] Use --task <task-id> to specify manually")
                console.print("[dim]Branch naming convention: task/<task-id>[/dim]")
                sys.exit(1)

            console.print(f"[dim]Detected task from branch: {task_id}[/dim]\n")

        # Generate description
        description = generator.generate_description(task_id)

        if not description:
            console.print(f"[red]Error:[/red] Task {task_id} not found in roadmap")
            sys.exit(1)

        # Output description
        if output:
            # Write to file
            output_path = Path(output)
            output_path.write_text(description)
            console.print(f"[green]✓[/green] PR description saved to: {output}")
        else:
            # Print to stdout
            console.print(description)

        # Copy to clipboard if requested
        if copy:
            try:
                import pyperclip
                pyperclip.copy(description)
                console.print("\n[green]✓ Copied to clipboard[/green]")
            except ImportError:
                console.print("\n[yellow]Warning:[/yellow] pyperclip not installed")
                console.print("[dim]Install with: pip install pyperclip[/dim]")
            except Exception as e:
                console.print(f"\n[yellow]Warning:[/yellow] Could not copy to clipboard: {e}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@git_group.group('branch')
@click.pass_context
def branch_group(ctx):
    """
    Manage task-branch linking.

    Create branches with proper naming conventions, link branches to tasks,
    and track branch lifecycle in roadmap YAML.

    Branch Naming Conventions:
      - task/<task-id>       # For task branches
      - sprint/<sprint-id>   # For sprint branches
      - track/<track-id>     # For track branches

    Examples:

      vibey git branch create git-integration-2-task-005
      vibey git branch link my-feature git-integration-2-task-005
      vibey git branch status
      vibey git branch list
    """
    pass


@branch_group.command('create')
@click.argument('task_id')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--from', 'start_point', help='Starting point (branch/commit)')
@click.option('--no-link', is_flag=True, help='Do not link branch to task in YAML')
@click.option('--dry-run', is_flag=True, help='Show what would be created')
@click.pass_context
def branch_create_cmd(ctx, task_id: str, repo: str, start_point: Optional[str], no_link: bool, dry_run: bool):
    """
    Create a branch for a task with proper naming.

    Creates a branch following the naming convention task/<task-id>
    and optionally links it to the task in roadmap YAML.

    Examples:

      vibey git branch create git-integration-2-task-005
      vibey git branch create task-001 --from main
      vibey git branch create task-001 --no-link
      vibey git branch create task-001 --dry-run
    """
    try:
        linker = BranchLinker(repo_path=repo)

        if not linker.is_git_repo():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        branch_name = linker.suggest_branch_name(task_id)

        console.print()
        mode_text = "Dry Run: " if dry_run else ""
        console.print(Panel(
            Text(f"{mode_text}Create Task Branch", style="bold blue"),
            border_style="blue"
        ))
        console.print()

        console.print(f"[bold]Task:[/bold] {task_id}")
        console.print(f"[bold]Branch:[/bold] {branch_name}")
        if start_point:
            console.print(f"[bold]From:[/bold] {start_point}")
        console.print()

        if not dry_run:
            # Check if branch already exists
            if linker.branch_exists(branch_name):
                console.print(f"[red]Error:[/red] Branch '{branch_name}' already exists")
                sys.exit(1)

            # Create branch
            success, error = linker.create_branch(branch_name, start_point)

            if not success:
                console.print(f"[red]Error creating branch:[/red] {error}")
                sys.exit(1)

            console.print(f"[green]✓[/green] Created branch '{branch_name}'")

            # Link to task
            if not no_link:
                success, error = linker.link_branch_to_task(task_id, branch_name)

                if success:
                    console.print(f"[green]✓[/green] Linked branch to task in roadmap")
                else:
                    console.print(f"[yellow]⚠[/yellow] Branch created but linking failed: {error}")
        else:
            console.print("[yellow]Dry run - no changes made[/yellow]")
            if not no_link:
                console.print("[dim]Would link branch to task in roadmap[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@branch_group.command('link')
@click.argument('branch_name')
@click.argument('task_id')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--dry-run', is_flag=True, help='Show what would be linked')
@click.pass_context
def branch_link_cmd(ctx, branch_name: str, task_id: str, repo: str, dry_run: bool):
    """
    Link an existing branch to a task.

    Records branch information in task metadata, including creation time,
    merge status, and current status.

    Examples:

      vibey git branch link my-feature git-integration-2-task-005
      vibey git branch link feature/new-api task-001 --dry-run
    """
    try:
        linker = BranchLinker(repo_path=repo)

        if not linker.is_git_repo():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        # Check if branch exists
        if not linker.branch_exists(branch_name):
            console.print(f"[yellow]Warning:[/yellow] Branch '{branch_name}' does not exist")

        console.print()
        mode_text = "Dry Run: " if dry_run else ""
        console.print(Panel(
            Text(f"{mode_text}Link Branch to Task", style="bold blue"),
            border_style="blue"
        ))
        console.print()

        console.print(f"[bold]Branch:[/bold] {branch_name}")
        console.print(f"[bold]Task:[/bold] {task_id}")
        console.print()

        if not dry_run:
            success, error = linker.link_branch_to_task(task_id, branch_name)

            if success:
                console.print("[green]✓ Successfully linked branch to task[/green]")
            else:
                console.print(f"[red]✗ Failed:[/red] {error}")
                sys.exit(1)
        else:
            console.print("[yellow]Dry run - no changes made[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@branch_group.command('unlink')
@click.argument('task_id')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--dry-run', is_flag=True, help='Show what would be unlinked')
@click.pass_context
def branch_unlink_cmd(ctx, task_id: str, repo: str, dry_run: bool):
    """
    Unlink a branch from a task.

    Removes branch metadata from the task in roadmap YAML.

    Examples:

      vibey git branch unlink git-integration-2-task-005
      vibey git branch unlink task-001 --dry-run
    """
    try:
        linker = BranchLinker(repo_path=repo)

        console.print()
        mode_text = "Dry Run: " if dry_run else ""
        console.print(Panel(
            Text(f"{mode_text}Unlink Branch from Task", style="bold blue"),
            border_style="blue"
        ))
        console.print()

        console.print(f"[bold]Task:[/bold] {task_id}")
        console.print()

        if not dry_run:
            success, error = linker.unlink_branch_from_task(task_id)

            if success:
                console.print("[green]✓ Successfully unlinked branch from task[/green]")
            else:
                console.print(f"[red]✗ Failed:[/red] {error}")
                sys.exit(1)
        else:
            console.print("[yellow]Dry run - no changes made[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@branch_group.command('status')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--task', 'task_id', help='Show status for specific task')
@click.pass_context
def branch_status_cmd(ctx, repo: str, task_id: Optional[str]):
    """
    Show branch-task linkage status.

    Displays which tasks have linked branches, their status (current, merged),
    and whether the branch still exists.

    Examples:

      vibey git branch status
      vibey git branch status --task git-integration-2-task-005
    """
    try:
        linker = BranchLinker(repo_path=repo)

        if not linker.is_git_repo():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        console.print()
        console.print(Panel(
            Text("Branch-Task Links", style="bold blue"),
            border_style="blue"
        ))
        console.print()

        if task_id:
            # Show single task
            link = linker.get_task_branch(task_id)

            if not link:
                console.print(f"[yellow]No branch linked to task {task_id}[/yellow]")
                return

            console.print(f"[bold]Task:[/bold] {link.task_id}")
            console.print(f"[bold]Branch:[/bold] {link.branch_name}")
            console.print(f"[bold]Current:[/bold] {'Yes' if link.current else 'No'}")
            console.print(f"[bold]Exists:[/bold] {'Yes' if link.exists else 'No (deleted)'}")
            console.print(f"[bold]Merged:[/bold] {'Yes' if link.merged else 'No'}")

            if link.created:
                created_date = datetime.fromisoformat(link.created).strftime("%Y-%m-%d %H:%M")
                console.print(f"[bold]Created:[/bold] {created_date}")

            if link.merge_commit:
                console.print(f"[bold]Merge Commit:[/bold] {link.merge_commit}")

        else:
            # Show all links
            links = linker.get_all_branch_links()

            if not links:
                console.print("[yellow]No branch-task links found[/yellow]")
                return

            table = Table(show_header=True)
            table.add_column("Task ID", style="cyan")
            table.add_column("Branch", style="yellow")
            table.add_column("Status", style="green")

            for link in links:
                status_parts = []

                if link.current:
                    status_parts.append("[bold green]*current[/bold green]")
                if link.merged:
                    status_parts.append("[blue]merged[/blue]")
                if not link.exists:
                    status_parts.append("[red]deleted[/red]")

                if not status_parts:
                    status_parts.append("[dim]active[/dim]")

                status = " ".join(status_parts)

                table.add_row(
                    link.task_id,
                    link.branch_name,
                    status
                )

            console.print(table)
            console.print(f"\n[dim]Total links: {len(links)}[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@branch_group.command('list')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--type', 'branch_type', type=click.Choice(['task', 'sprint', 'track', 'all']), default='all',
              help='Filter by branch type')
@click.pass_context
def branch_list_cmd(ctx, repo: str, branch_type: str):
    """
    List all branches following Vibey naming conventions.

    Shows branches that follow the task/*, sprint/*, or track/* naming pattern.

    Examples:

      vibey git branch list
      vibey git branch list --type task
      vibey git branch list --type sprint
    """
    try:
        linker = BranchLinker(repo_path=repo)

        if not linker.is_git_repo():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        console.print()
        console.print(Panel(
            Text("Vibey Branches", style="bold blue"),
            border_style="blue"
        ))
        console.print()

        all_branches = linker.get_all_branches()
        current_branch = linker.get_current_branch()

        # Filter and categorize branches
        filtered_branches = []

        for branch in all_branches:
            br_type, item_id = linker.parse_branch_name(branch)

            if branch_type == 'all' or br_type.value == branch_type:
                if br_type != linker.BranchLinker.__dict__.get('BranchType', type('', (), {})).OTHER:
                    is_current = (branch == current_branch)
                    is_merged = linker.is_branch_merged(branch)

                    filtered_branches.append({
                        'name': branch,
                        'type': br_type.value,
                        'item_id': item_id,
                        'current': is_current,
                        'merged': is_merged
                    })

        if not filtered_branches:
            console.print("[yellow]No Vibey branches found[/yellow]")
            return

        table = Table(show_header=True)
        table.add_column("Branch Name", style="yellow")
        table.add_column("Type", style="cyan")
        table.add_column("Item ID", style="blue")
        table.add_column("Status", style="green")

        for branch in filtered_branches:
            status_parts = []

            if branch['current']:
                status_parts.append("[bold green]*current[/bold green]")
            if branch['merged']:
                status_parts.append("[blue]merged[/blue]")

            if not status_parts:
                status_parts.append("[dim]active[/dim]")

            status = " ".join(status_parts)

            table.add_row(
                branch['name'],
                branch['type'],
                branch['item_id'] or '-',
                status
            )

        console.print(table)
        console.print(f"\n[dim]Total branches: {len(filtered_branches)}[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@git_group.group('hooks')
@click.pass_context
def hooks_group(ctx):
    """
    Manage Git hooks for Vibey roadmap integration.

    Install, uninstall, and check status of pre-commit and commit-msg hooks
    that validate roadmap integration and enforce quality standards.

    Examples:

      vibey git hooks install           # Install all hooks
      vibey git hooks uninstall         # Remove all hooks
      vibey git hooks status            # Check installation status
      vibey git hooks update            # Update existing hooks
    """
    pass


@hooks_group.command('install')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--force', is_flag=True, help='Overwrite existing hooks')
@click.option('--pre-commit-only', is_flag=True, help='Install only pre-commit hook')
@click.option('--commit-msg-only', is_flag=True, help='Install only commit-msg hook')
@click.pass_context
def hooks_install_cmd(ctx, repo: str, force: bool, pre_commit_only: bool, commit_msg_only: bool):
    """
    Install Git hooks for Vibey roadmap integration.

    Installs pre-commit and commit-msg hooks that validate:
    - YAML syntax in roadmap files
    - Commit message format and task references
    - Task existence in roadmap

    By default, existing hooks are preserved and backed up.

    Examples:

      vibey git hooks install                    # Install all hooks
      vibey git hooks install --force            # Overwrite existing
      vibey git hooks install --pre-commit-only  # Only pre-commit
    """
    try:
        repo_path = Path(repo).resolve()
        git_dir = repo_path / ".git"
        hooks_dir = git_dir / "hooks"

        if not git_dir.exists():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        vibey_dir = repo_path / ".vibey"
        if not vibey_dir.exists():
            console.print(f"[yellow]Warning:[/yellow] No .vibey directory found. Initialize with 'vibey roadmap init' first.")

        # Ensure hooks directory exists
        hooks_dir.mkdir(exist_ok=True)

        # Get hook source files from package
        import vibey.operations.git.hooks as hooks_module
        hooks_module_path = Path(hooks_module.__file__).parent

        # Determine which hooks to install
        install_hooks = []
        if not commit_msg_only:
            install_hooks.append(('pre-commit', hooks_module_path / 'pre-commit.sh'))
        if not pre_commit_only:
            install_hooks.append(('commit-msg', hooks_module_path / 'commit-msg.sh'))

        console.print()
        console.print(Panel(
            Text("Installing Vibey Git Hooks", style="bold blue"),
            border_style="blue"
        ))
        console.print()

        installed = []
        backed_up = []
        skipped = []

        for hook_name, source_path in install_hooks:
            dest_path = hooks_dir / hook_name

            # Check if hook exists
            if dest_path.exists():
                if not force:
                    # Back up existing hook
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = hooks_dir / f"{hook_name}.backup-{timestamp}"
                    shutil.copy2(dest_path, backup_path)
                    backed_up.append((hook_name, backup_path))
                    console.print(f"[yellow]Backed up existing {hook_name} hook to:[/yellow] {backup_path.name}")

            # Install hook
            try:
                shutil.copy2(source_path, dest_path)
                dest_path.chmod(0o755)  # Make executable
                installed.append(hook_name)
                console.print(f"[green]✓[/green] Installed {hook_name} hook")
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to install {hook_name}: {e}")
                skipped.append(hook_name)

        console.print()

        # Summary
        if installed:
            console.print(f"[bold green]Successfully installed {len(installed)} hook(s)[/bold green]")

            console.print()
            console.print("[bold]What's Next:[/bold]")
            console.print("  1. Hooks will run automatically on commits")
            console.print("  2. Configure enforcement mode in .vibey/config/git.yaml")
            console.print("  3. Use 'git commit --no-verify' to bypass hooks temporarily")
            console.print("  4. Run 'vibey git hooks status' to verify installation")
            console.print()
            console.print("[dim]To uninstall: vibey git hooks uninstall[/dim]")

        if skipped:
            console.print(f"[yellow]Skipped {len(skipped)} hook(s)[/yellow]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@hooks_group.command('uninstall')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--keep-backups', is_flag=True, help='Keep backup files')
@click.pass_context
def hooks_uninstall_cmd(ctx, repo: str, keep_backups: bool):
    """
    Uninstall Vibey Git hooks.

    Removes pre-commit and commit-msg hooks installed by Vibey.
    Optionally removes backup files created during installation.

    Examples:

      vibey git hooks uninstall                # Remove hooks
      vibey git hooks uninstall --keep-backups # Keep backups
    """
    try:
        repo_path = Path(repo).resolve()
        git_dir = repo_path / ".git"
        hooks_dir = git_dir / "hooks"

        if not git_dir.exists():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        console.print()
        console.print(Panel(
            Text("Uninstalling Vibey Git Hooks", style="bold yellow"),
            border_style="yellow"
        ))
        console.print()

        removed = []
        not_found = []

        # Remove hooks
        for hook_name in ['pre-commit', 'commit-msg']:
            hook_path = hooks_dir / hook_name

            if hook_path.exists():
                # Verify it's a Vibey hook by checking for marker
                try:
                    content = hook_path.read_text()
                    if 'vibey' in content.lower() or 'Vibey' in content:
                        hook_path.unlink()
                        removed.append(hook_name)
                        console.print(f"[green]✓[/green] Removed {hook_name} hook")
                    else:
                        console.print(f"[yellow]⚠[/yellow] {hook_name} hook exists but doesn't appear to be a Vibey hook (skipped)")
                        not_found.append(hook_name)
                except Exception as e:
                    console.print(f"[red]✗[/red] Failed to remove {hook_name}: {e}")
            else:
                not_found.append(hook_name)
                console.print(f"[dim]○[/dim] {hook_name} hook not installed")

        # Handle backups
        if not keep_backups:
            backup_files = list(hooks_dir.glob("*.backup-*"))
            if backup_files:
                console.print()
                console.print(f"[bold]Removing {len(backup_files)} backup file(s):[/bold]")
                for backup_file in backup_files:
                    backup_file.unlink()
                    console.print(f"  [dim]✓ Removed {backup_file.name}[/dim]")

        console.print()
        if removed:
            console.print(f"[bold green]Successfully removed {len(removed)} hook(s)[/bold green]")
        else:
            console.print("[yellow]No Vibey hooks were installed[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@hooks_group.command('status')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.pass_context
def hooks_status_cmd(ctx, repo: str):
    """
    Show Git hooks installation status.

    Displays which Vibey hooks are installed, their versions,
    and configuration settings.

    Examples:

      vibey git hooks status
    """
    try:
        repo_path = Path(repo).resolve()
        git_dir = repo_path / ".git"
        hooks_dir = git_dir / "hooks"
        vibey_dir = repo_path / ".vibey"

        if not git_dir.exists():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        console.print()
        console.print(Panel(
            Text("Vibey Git Hooks Status", style="bold blue"),
            border_style="blue"
        ))
        console.print()

        # Check each hook
        table = Table(show_header=True)
        table.add_column("Hook", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Executable", style="yellow")
        table.add_column("Location", style="dim")

        for hook_name in ['pre-commit', 'commit-msg']:
            hook_path = hooks_dir / hook_name

            if hook_path.exists():
                # Check if executable
                is_executable = hook_path.stat().st_mode & 0o111 != 0

                # Check if it's a Vibey hook
                content = hook_path.read_text()
                is_vibey = 'vibey' in content.lower() or 'Vibey' in content

                if is_vibey:
                    status = "[green]✓ Installed[/green]"
                else:
                    status = "[yellow]⚠ Non-Vibey[/yellow]"

                executable = "[green]Yes[/green]" if is_executable else "[red]No[/red]"

                table.add_row(
                    hook_name,
                    status,
                    executable,
                    str(hook_path.relative_to(repo_path))
                )
            else:
                table.add_row(
                    hook_name,
                    "[red]✗ Not installed[/red]",
                    "-",
                    "-"
                )

        console.print(table)
        console.print()

        # Check configuration
        config_path = vibey_dir / "config" / "git.yaml"
        if config_path.exists():
            console.print("[bold]Configuration:[/bold]")
            console.print(f"  Location: {config_path.relative_to(repo_path)}")

            # Load and show enforcement mode
            try:
                import yaml
                with open(config_path) as f:
                    config = yaml.safe_load(f)

                git_config = config.get('git', {})
                enforcement = git_config.get('enforcement', {})
                mode = enforcement.get('mode', 'advisory')

                mode_color = {
                    'off': 'dim',
                    'advisory': 'yellow',
                    'blocking': 'red',
                    'audit': 'blue',
                }.get(mode, 'white')

                console.print(f"  Enforcement mode: [{mode_color}]{mode}[/{mode_color}]")

                # Show audit log if enabled
                audit = enforcement.get('audit', {})
                if audit.get('enabled'):
                    audit_file = audit.get('file', '.vibey/git-audit.log')
                    console.print(f"  Audit log: {audit_file}")

            except Exception as e:
                console.print(f"  [yellow]Could not read config: {e}[/yellow]")
        else:
            console.print("[yellow]No configuration file found[/yellow]")
            console.print(f"  Expected: {config_path.relative_to(repo_path)}")

        console.print()

        # Check for backups
        backup_files = list(hooks_dir.glob("*.backup-*"))
        if backup_files:
            console.print(f"[bold]Backup Files:[/bold] {len(backup_files)}")
            for backup_file in backup_files[:5]:
                console.print(f"  {backup_file.name}")
            if len(backup_files) > 5:
                console.print(f"  ... and {len(backup_files) - 5} more")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@hooks_group.command('update')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.pass_context
def hooks_update_cmd(ctx, repo: str):
    """
    Update installed Git hooks to latest version.

    Reinstalls hooks while preserving configuration.
    Existing hooks are backed up before updating.

    Examples:

      vibey git hooks update
    """
    try:
        repo_path = Path(repo).resolve()
        git_dir = repo_path / ".git"
        hooks_dir = git_dir / "hooks"

        if not git_dir.exists():
            console.print(f"[red]Error:[/red] Not a git repository: {repo}")
            sys.exit(1)

        console.print()
        console.print(Panel(
            Text("Updating Vibey Git Hooks", style="bold blue"),
            border_style="blue"
        ))
        console.print()

        # Check which hooks are installed
        installed_hooks = []
        for hook_name in ['pre-commit', 'commit-msg']:
            hook_path = hooks_dir / hook_name
            if hook_path.exists():
                content = hook_path.read_text()
                if 'vibey' in content.lower() or 'Vibey' in content:
                    installed_hooks.append(hook_name)

        if not installed_hooks:
            console.print("[yellow]No Vibey hooks currently installed[/yellow]")
            console.print("Use 'vibey git hooks install' to install hooks")
            return

        console.print(f"Found {len(installed_hooks)} installed hook(s)")
        console.print()

        # Get hook source files
        import vibey.operations.git.hooks as hooks_module
        hooks_module_path = Path(hooks_module.__file__).parent

        updated = []
        failed = []

        for hook_name in installed_hooks:
            source_path = hooks_module_path / f"{hook_name}.sh"
            dest_path = hooks_dir / hook_name

            # Create backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = hooks_dir / f"{hook_name}.backup-{timestamp}"

            try:
                shutil.copy2(dest_path, backup_path)
                console.print(f"[dim]Created backup: {backup_path.name}[/dim]")

                # Update hook
                shutil.copy2(source_path, dest_path)
                dest_path.chmod(0o755)

                updated.append(hook_name)
                console.print(f"[green]✓[/green] Updated {hook_name} hook")

            except Exception as e:
                console.print(f"[red]✗[/red] Failed to update {hook_name}: {e}")
                failed.append(hook_name)

        console.print()
        if updated:
            console.print(f"[bold green]Successfully updated {len(updated)} hook(s)[/bold green]")
        if failed:
            console.print(f"[bold red]Failed to update {len(failed)} hook(s)[/bold red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@git_group.group('sprint')
@click.pass_context
def sprint_group(ctx):
    """
    Manage sprint boundary tags.

    Create and manage git tags that mark sprint start and end points,
    enabling velocity calculations and state reconstruction queries.

    Examples:

      vibey git sprint start git-integration-2         # Tag sprint start at HEAD
      vibey git sprint end git-integration-2           # Tag sprint end at HEAD
      vibey git sprint list                            # List all sprint tags
      vibey git sprint list git-integration-2          # List tags for specific sprint
      vibey git sprint range git-integration-2         # Show commit range for sprint
    """
    pass


@sprint_group.command('start')
@click.argument('sprint_id')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--commit', help='Commit SHA to tag (default: HEAD)')
@click.option('--force', is_flag=True, help='Overwrite existing tag')
@click.option('--push', is_flag=True, help='Push tag to remote')
@click.option('--remote', default='origin', help='Remote name (default: origin)')
@click.pass_context
def sprint_start_cmd(ctx, sprint_id: str, repo: str, commit: Optional[str], force: bool, push: bool, remote: str):
    """
    Create sprint start tag at current or specified commit.

    Marks the beginning of a sprint in git history with an annotated tag
    containing sprint metadata from the roadmap.

    Examples:

      vibey git sprint start git-integration-2
      vibey git sprint start git-integration-2 --commit abc1234
      vibey git sprint start git-integration-2 --force --push
    """
    try:
        tagger = SprintTagger(repo_path=repo)
        success, error = tagger.create_sprint_tag(sprint_id, 'start', commit, force, push, remote)

        if success:
            tag_name = f"sprint/{sprint_id}/start"
            commit_sha = commit if commit else tagger._get_current_commit()[:8]

            console.print()
            console.print(Panel(
                f"[bold green]Sprint start tag created[/bold green]\n\n"
                f"[cyan]Tag:[/cyan] {tag_name}\n"
                f"[cyan]Commit:[/cyan] {commit_sha}\n"
                f"[cyan]Sprint:[/cyan] {sprint_id}",
                title="✓ Sprint Tagged",
                border_style="green"
            ))

            if push:
                console.print(f"[dim]Pushed to remote: {remote}[/dim]")
        else:
            console.print(f"[red]Error:[/red] {error}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@sprint_group.command('end')
@click.argument('sprint_id')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--commit', help='Commit SHA to tag (default: HEAD)')
@click.option('--force', is_flag=True, help='Overwrite existing tag')
@click.option('--push', is_flag=True, help='Push tag to remote')
@click.option('--remote', default='origin', help='Remote name (default: origin)')
@click.pass_context
def sprint_end_cmd(ctx, sprint_id: str, repo: str, commit: Optional[str], force: bool, push: bool, remote: str):
    """
    Create sprint end tag at current or specified commit.

    Marks the completion of a sprint in git history with an annotated tag
    containing sprint completion metrics from the roadmap.

    Examples:

      vibey git sprint end git-integration-2
      vibey git sprint end git-integration-2 --commit abc1234
      vibey git sprint end git-integration-2 --force --push
    """
    try:
        tagger = SprintTagger(repo_path=repo)
        success, error = tagger.create_sprint_tag(sprint_id, 'end', commit, force, push, remote)

        if success:
            tag_name = f"sprint/{sprint_id}/end"
            commit_sha = commit if commit else tagger._get_current_commit()[:8]

            console.print()
            console.print(Panel(
                f"[bold green]Sprint end tag created[/bold green]\n\n"
                f"[cyan]Tag:[/cyan] {tag_name}\n"
                f"[cyan]Commit:[/cyan] {commit_sha}\n"
                f"[cyan]Sprint:[/cyan] {sprint_id}",
                title="✓ Sprint Complete",
                border_style="green"
            ))

            if push:
                console.print(f"[dim]Pushed to remote: {remote}[/dim]")
        else:
            console.print(f"[red]Error:[/red] {error}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@sprint_group.command('list')
@click.argument('sprint_id', required=False)
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
@click.pass_context
def sprint_list_cmd(ctx, sprint_id: Optional[str], repo: str, output_format: str):
    """
    List sprint tags, optionally filtered by sprint ID.

    Shows all sprint start/end tags with commit info and dates.

    Examples:

      vibey git sprint list                      # List all sprint tags
      vibey git sprint list git-integration-2    # List tags for specific sprint
      vibey git sprint list --format json        # JSON output
    """
    try:
        tagger = SprintTagger(repo_path=repo)
        tags = tagger.list_sprint_tags(sprint_id)

        if not tags:
            if sprint_id:
                console.print(f"[yellow]No tags found for sprint: {sprint_id}[/yellow]")
            else:
                console.print("[yellow]No sprint tags found[/yellow]")
            return

        if output_format == 'json':
            tags_data = [
                {
                    'tag_name': tag.tag_name,
                    'sprint_id': tag.sprint_id,
                    'tag_type': tag.tag_type,
                    'commit_sha': tag.commit_sha,
                    'tagger_name': tag.tagger_name,
                    'tagger_email': tag.tagger_email,
                    'tag_date': tag.tag_date.isoformat(),
                }
                for tag in tags
            ]
            console.print(json.dumps(tags_data, indent=2))
        else:
            table = Table(title=f"Sprint Tags{f' for {sprint_id}' if sprint_id else ''}")
            table.add_column("Sprint ID", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Commit", style="yellow")
            table.add_column("Date", style="green")
            table.add_column("Tagger", style="dim")

            for tag in tags:
                table.add_row(
                    tag.sprint_id,
                    tag.tag_type,
                    tag.commit_sha[:8],
                    format_date(tag.tag_date),
                    tag.tagger_name
                )

            console.print()
            console.print(table)
            console.print(f"\n[dim]Total: {len(tags)} tag(s)[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@sprint_group.command('range')
@click.argument('sprint_id')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--commits', is_flag=True, help='Show commit list')
@click.pass_context
def sprint_range_cmd(ctx, sprint_id: str, repo: str, commits: bool):
    """
    Show commit range for a sprint (start tag to end tag).

    Displays the start and end commits for a sprint, and optionally
    lists all commits in the sprint range.

    Examples:

      vibey git sprint range git-integration-2             # Show range endpoints
      vibey git sprint range git-integration-2 --commits   # Show all commits
    """
    try:
        tagger = SprintTagger(repo_path=repo)

        # Get commit range
        start_commit, end_commit, error = tagger.get_sprint_commit_range(sprint_id)

        if error:
            console.print(f"[red]Error:[/red] {error}")
            sys.exit(1)

        # Display range
        console.print()
        console.print(Panel(
            f"[bold]Sprint Commit Range[/bold]\n\n"
            f"[cyan]Sprint:[/cyan] {sprint_id}\n"
            f"[cyan]Start:[/cyan] {start_commit[:8] if start_commit else 'N/A'}\n"
            f"[cyan]End:[/cyan] {end_commit[:8] if end_commit else 'HEAD'}",
            title=f"Sprint: {sprint_id}",
            border_style="cyan"
        ))

        # Show commits if requested
        if commits:
            commit_list, error = tagger.get_sprint_commits(sprint_id)

            if error:
                console.print(f"[red]Error:[/red] {error}")
                sys.exit(1)

            if commit_list:
                console.print(f"\n[bold]Commits in range:[/bold] {len(commit_list)}\n")
                for commit_sha in commit_list[:20]:  # Limit to 20
                    console.print(f"  {commit_sha[:8]}")

                if len(commit_list) > 20:
                    console.print(f"  [dim]... and {len(commit_list) - 20} more[/dim]")
            else:
                console.print("\n[yellow]No commits in range[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@sprint_group.command('delete')
@click.argument('sprint_id')
@click.argument('tag_type', type=click.Choice(['start', 'end']))
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--push', is_flag=True, help='Delete tag from remote')
@click.option('--remote', default='origin', help='Remote name (default: origin)')
@click.pass_context
def sprint_delete_cmd(ctx, sprint_id: str, tag_type: str, repo: str, push: bool, remote: str):
    """
    Delete a sprint boundary tag.

    Removes a sprint start or end tag from the local repository,
    and optionally from the remote.

    Examples:

      vibey git sprint delete git-integration-2 start
      vibey git sprint delete git-integration-2 end --push
    """
    try:
        tagger = SprintTagger(repo_path=repo)
        success, error = tagger.delete_sprint_tag(sprint_id, tag_type, push, remote)

        if success:
            tag_name = f"sprint/{sprint_id}/{tag_type}"
            console.print(f"[green]✓[/green] Deleted tag: {tag_name}")

            if push:
                console.print(f"[dim]Deleted from remote: {remote}[/dim]")
        else:
            console.print(f"[red]Error:[/red] {error}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@git_group.command('sync')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--task', 'task_id', help='Sync specific task')
@click.option('--sprint', 'sprint_id', help='Sync specific sprint')
@click.option('--track', 'track_id', help='Sync specific track')
@click.option('--dry-run', is_flag=True, help='Show changes without applying')
@click.option('--format', 'output_format', type=click.Choice(['summary', 'detailed', 'json']), default='summary',
              help='Output format')
@click.pass_context
def sync_cmd(ctx, repo: str, task_id: Optional[str], sprint_id: Optional[str], track_id: Optional[str],
             dry_run: bool, output_format: str):
    """
    Sync roadmap YAML from Git state (Git-primary mode).

    Derives task and sprint status from git branches, tags, and commits.
    In Git-primary mode, Git is the source of truth.

    DERIVATION RULES:

    Task Status:
      - not_started: no branch AND no commits
      - in_progress: branch exists OR commits exist
      - completed: branch merged with commits

    Sprint Status:
      - not_started: no start tag
      - in_progress: start tag exists, no end tag
      - completed: end tag exists

    Examples:

      vibey git sync                         # Sync all tracks
      vibey git sync --task task-001         # Sync specific task
      vibey git sync --sprint sprint-2       # Sync specific sprint
      vibey git sync --track git-integration # Sync specific track
      vibey git sync --dry-run               # Preview changes
    """
    try:
        # Run sync
        result = sync_from_git(
            repo_path=repo,
            task_id=task_id,
            sprint_id=sprint_id,
            track_id=track_id,
            dry_run=dry_run
        )

        # Display results
        if output_format == 'json':
            output = {
                'dry_run': result.dry_run,
                'task_changes': [
                    {
                        'task_id': c.task_id,
                        'field': c.field,
                        'old_value': c.old_value,
                        'new_value': c.new_value,
                        'reason': c.reason
                    }
                    for c in result.task_changes
                ],
                'sprint_changes': [
                    {
                        'sprint_id': c.sprint_id,
                        'field': c.field,
                        'old_value': c.old_value,
                        'new_value': c.new_value,
                        'reason': c.reason
                    }
                    for c in result.sprint_changes
                ],
                'conflicts': result.conflicts,
                'warnings': result.warnings
            }
            console.print(json.dumps(output, indent=2))

        elif output_format == 'detailed':
            console.print()
            console.print(Panel(
                f"[bold]Git Sync {'(Dry Run)' if dry_run else 'Results'}[/bold]\n\n"
                f"[cyan]Task Changes:[/cyan] {len(result.task_changes)}\n"
                f"[cyan]Sprint Changes:[/cyan] {len(result.sprint_changes)}\n"
                f"[cyan]Conflicts:[/cyan] {len(result.conflicts)}\n"
                f"[cyan]Warnings:[/cyan] {len(result.warnings)}",
                title="Git Sync Summary",
                border_style="cyan"
            ))

            # Task changes
            if result.task_changes:
                console.print("\n[bold]Task Changes:[/bold]\n")
                for change in result.task_changes:
                    status_color = {
                        'completed': 'green',
                        'in_progress': 'yellow',
                        'not_started': 'dim'
                    }.get(change.new_value, 'white')

                    console.print(f"  [{status_color}]•[/{status_color}] {change.task_id}")
                    console.print(f"    {change.field}: {change.old_value} → {change.new_value}")
                    console.print(f"    [dim]Reason: {change.reason}[/dim]\n")

            # Sprint changes
            if result.sprint_changes:
                console.print("\n[bold]Sprint Changes:[/bold]\n")
                for change in result.sprint_changes:
                    status_color = {
                        'completed': 'green',
                        'in_progress': 'yellow',
                        'not_started': 'dim'
                    }.get(change.new_value, 'white')

                    console.print(f"  [{status_color}]•[/{status_color}] {change.sprint_id}")
                    console.print(f"    {change.field}: {change.old_value} → {change.new_value}")
                    console.print(f"    [dim]Reason: {change.reason}[/dim]\n")

            # Conflicts
            if result.conflicts:
                console.print("\n[bold red]Conflicts:[/bold red]\n")
                for conflict in result.conflicts:
                    console.print(f"  [red]⚠[/red] {conflict}")

            # Warnings
            if result.warnings:
                console.print("\n[bold yellow]Warnings:[/bold yellow]\n")
                for warning in result.warnings:
                    console.print(f"  [yellow]![/yellow] {warning}")

        else:  # summary
            console.print()

            # Summary table
            table = Table(title=f"Git Sync {'(Dry Run)' if dry_run else 'Results'}")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", style="bold")

            table.add_row("Task Changes", str(len(result.task_changes)))
            table.add_row("Sprint Changes", str(len(result.sprint_changes)))
            table.add_row("Conflicts", str(len(result.conflicts)))
            table.add_row("Warnings", str(len(result.warnings)))

            console.print(table)

            # Quick summary of changes
            if result.task_changes:
                console.print(f"\n[bold]Task Status Changes:[/bold]")
                status_counts = {}
                for change in result.task_changes:
                    new_status = change.new_value
                    status_counts[new_status] = status_counts.get(new_status, 0) + 1

                for status, count in status_counts.items():
                    status_color = {
                        'completed': 'green',
                        'in_progress': 'yellow',
                        'not_started': 'dim'
                    }.get(status, 'white')
                    console.print(f"  [{status_color}]{count} → {status}[/{status_color}]")

            if result.sprint_changes:
                console.print(f"\n[bold]Sprint Status Changes:[/bold]")
                for change in result.sprint_changes:
                    status_color = {
                        'completed': 'green',
                        'in_progress': 'yellow',
                        'not_started': 'dim'
                    }.get(change.new_value, 'white')
                    console.print(f"  [{status_color}]{change.sprint_id} → {change.new_value}[/{status_color}]")

            if result.warnings:
                console.print(f"\n[yellow]Warnings: {len(result.warnings)}[/yellow]")
                console.print("[dim]Use --format detailed to see all warnings[/dim]")

            if dry_run and (result.task_changes or result.sprint_changes):
                console.print(f"\n[bold cyan]Run without --dry-run to apply changes[/bold cyan]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@git_group.command('mode')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--format', 'output_format', type=click.Choice(['summary', 'detailed', 'json']), default='summary',
              help='Output format')
@click.pass_context
def mode_cmd(ctx, repo: str, output_format: str):
    """
    Show current source-of-truth mode and reasoning.

    Displays which mode is active (yaml-only, hybrid, git-primary)
    and explains why that mode was chosen.

    MODES:
      - yaml-only: YAML files are source of truth, no git integration
      - hybrid: YAML primary, git provides supplementary data
      - git-primary: Git is source of truth, YAML derived from git

    Examples:

      vibey git mode                    # Show current mode
      vibey git mode --format detailed  # Show with requirements
      vibey git mode --format json      # JSON output
    """
    try:
        detector = ModeDetector(repo_path=repo)
        result = detector.detect_mode()

        if output_format == 'json':
            output = {
                'mode': result.mode.value,
                'reason': result.reason,
                'requirements_met': result.requirements_met,
                'warnings': result.warnings
            }
            console.print(json.dumps(output, indent=2))

        elif output_format == 'detailed':
            console.print()

            # Mode badge
            mode_colors = {
                SourceOfTruthMode.YAML_ONLY: 'blue',
                SourceOfTruthMode.HYBRID: 'yellow',
                SourceOfTruthMode.GIT_PRIMARY: 'green'
            }
            mode_color = mode_colors.get(result.mode, 'white')

            console.print(Panel(
                f"[bold {mode_color}]{result.mode.value.upper()}[/bold {mode_color}]\n\n"
                f"[cyan]Reason:[/cyan] {result.reason}",
                title="Source of Truth Mode",
                border_style=mode_color
            ))

            # Requirements
            if result.requirements_met:
                console.print("\n[bold]Requirements:[/bold]\n")
                for req, met in result.requirements_met.items():
                    status = "[green]✓[/green]" if met else "[red]✗[/red]"
                    console.print(f"  {status} {req}")

            # Warnings
            if result.warnings:
                console.print("\n[bold yellow]Warnings:[/bold yellow]\n")
                for warning in result.warnings:
                    console.print(f"  [yellow]![/yellow] {warning}")

            # Mode descriptions
            console.print("\n[bold]Mode Descriptions:[/bold]\n")
            console.print("  [blue]yaml-only[/blue]:    YAML files are source of truth, no git integration")
            console.print("  [yellow]hybrid[/yellow]:       YAML primary, git provides supplementary data")
            console.print("  [green]git-primary[/green]:  Git is source of truth, YAML derived from git")

        else:  # summary
            mode_colors = {
                SourceOfTruthMode.YAML_ONLY: 'blue',
                SourceOfTruthMode.HYBRID: 'yellow',
                SourceOfTruthMode.GIT_PRIMARY: 'green'
            }
            mode_color = mode_colors.get(result.mode, 'white')

            console.print()
            console.print(f"[bold]Source of Truth Mode:[/bold] [{mode_color}]{result.mode.value}[/{mode_color}]")
            console.print(f"[dim]Reason: {result.reason}[/dim]")

            if result.warnings:
                console.print(f"\n[yellow]Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"  • {warning}")

            console.print(f"\n[dim]Use --format detailed for more information[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@git_group.command('validate')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--format', 'output_format', type=click.Choice(['summary', 'detailed', 'json']), default='summary',
              help='Output format')
@click.pass_context
def validate_cmd(ctx, repo: str, output_format: str):
    """
    Validate git strategy requirements.

    Checks that all strategy requirements are satisfied for the current mode.
    This includes branch naming conventions, required branches, tags, etc.

    Examples:

      vibey git validate                    # Validate strategy
      vibey git validate --format detailed  # Show all violations
      vibey git validate --format json      # JSON output
    """
    try:
        validation = validate_git_strategy(repo_path=repo)

        if output_format == 'json':
            output = {
                'valid': validation.valid,
                'mode': validation.mode.value,
                'violations': validation.violations,
                'warnings': validation.warnings,
                'requirements': validation.requirements
            }
            console.print(json.dumps(output, indent=2))

        elif output_format == 'detailed':
            console.print()

            # Status panel
            status = "VALID" if validation.valid else "INVALID"
            status_color = "green" if validation.valid else "red"
            status_icon = "✓" if validation.valid else "✗"

            console.print(Panel(
                f"[bold {status_color}]{status_icon} {status}[/bold {status_color}]\n\n"
                f"[cyan]Mode:[/cyan] {validation.mode.value}\n"
                f"[cyan]Violations:[/cyan] {len(validation.violations)}\n"
                f"[cyan]Warnings:[/cyan] {len(validation.warnings)}",
                title="Strategy Validation",
                border_style=status_color
            ))

            # Violations
            if validation.violations:
                console.print("\n[bold red]Violations:[/bold red]\n")
                for violation in validation.violations:
                    console.print(f"  [red]✗[/red] {violation}")

            # Warnings
            if validation.warnings:
                console.print("\n[bold yellow]Warnings:[/bold yellow]\n")
                for warning in validation.warnings:
                    console.print(f"  [yellow]![/yellow] {warning}")

            # Requirements
            if validation.requirements:
                console.print("\n[bold]Requirements:[/bold]\n")
                for req, met in validation.requirements.items():
                    status = "[green]✓[/green]" if met else "[red]✗[/red]"
                    console.print(f"  {status} {req}")

        else:  # summary
            status_icon = "[green]✓[/green]" if validation.valid else "[red]✗[/red]"
            status_text = "Valid" if validation.valid else "Invalid"

            console.print()
            console.print(f"{status_icon} [bold]Strategy Validation:[/bold] {status_text}")
            console.print(f"[dim]Mode: {validation.mode.value}[/dim]")

            if validation.violations:
                console.print(f"\n[red]Violations: {len(validation.violations)}[/red]")
                for violation in validation.violations[:3]:
                    console.print(f"  • {violation}")
                if len(validation.violations) > 3:
                    console.print(f"  [dim]... and {len(validation.violations) - 3} more[/dim]")

            if validation.warnings:
                console.print(f"\n[yellow]Warnings: {len(validation.warnings)}[/yellow]")
                for warning in validation.warnings[:3]:
                    console.print(f"  • {warning}")
                if len(validation.warnings) > 3:
                    console.print(f"  [dim]... and {len(validation.warnings) - 3} more[/dim]")

            if not validation.valid or validation.warnings:
                console.print(f"\n[dim]Use --format detailed for more information[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@git_group.command('validate-roadmap')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--format', 'output_format', type=click.Choice(['summary', 'detailed', 'json']), default='summary',
              help='Output format')
@click.pass_context
def validate_roadmap_cmd(ctx, repo: str, output_format: str):
    """
    Validate roadmap YAML files and consistency.

    Checks for:
    - YAML syntax errors
    - Invalid task/sprint references
    - Git-roadmap consistency
    - Orphaned files

    Examples:

      vibey git validate-roadmap                    # Validate roadmap
      vibey git validate-roadmap --format detailed  # Show all issues
      vibey git validate-roadmap --format json      # JSON output
    """
    try:
        issues, error = validate_roadmap(repo_path=repo)

        if error:
            console.print(f"[red]Error:[/red] {error}")
            sys.exit(1)

        if output_format == 'json':
            output = {
                'valid': len([i for i in issues if i.severity == 'error']) == 0,
                'issues': [
                    {
                        'severity': issue.severity,
                        'category': issue.category,
                        'file_path': issue.file_path,
                        'issue': issue.issue,
                        'suggestion': issue.suggestion
                    }
                    for issue in issues
                ]
            }
            console.print(json.dumps(output, indent=2))

        elif output_format == 'detailed':
            console.print()

            errors = [i for i in issues if i.severity == 'error']
            warnings = [i for i in issues if i.severity == 'warning']
            info = [i for i in issues if i.severity == 'info']

            # Status panel
            status = "VALID" if len(errors) == 0 else "INVALID"
            status_color = "green" if len(errors) == 0 else "red"
            status_icon = "✓" if len(errors) == 0 else "✗"

            console.print(Panel(
                f"[bold {status_color}]{status_icon} {status}[/bold {status_color}]\n\n"
                f"[cyan]Errors:[/cyan] {len(errors)}\n"
                f"[cyan]Warnings:[/cyan] {len(warnings)}\n"
                f"[cyan]Info:[/cyan] {len(info)}",
                title="Roadmap Validation",
                border_style=status_color
            ))

            # Errors
            if errors:
                console.print("\n[bold red]Errors:[/bold red]\n")
                for issue in errors:
                    file_part = f" ({issue.file_path})" if issue.file_path else ""
                    console.print(f"  [red]✗[/red] [{issue.category}] {issue.issue}{file_part}")
                    if issue.suggestion:
                        console.print(f"    [dim]→ {issue.suggestion}[/dim]")

            # Warnings
            if warnings:
                console.print("\n[bold yellow]Warnings:[/bold yellow]\n")
                for issue in warnings:
                    file_part = f" ({issue.file_path})" if issue.file_path else ""
                    console.print(f"  [yellow]![/yellow] [{issue.category}] {issue.issue}{file_part}")
                    if issue.suggestion:
                        console.print(f"    [dim]→ {issue.suggestion}[/dim]")

            # Info
            if info:
                console.print("\n[bold]Info:[/bold]\n")
                for issue in info:
                    file_part = f" ({issue.file_path})" if issue.file_path else ""
                    console.print(f"  [blue]ℹ[/blue] [{issue.category}] {issue.issue}{file_part}")

        else:  # summary
            errors = [i for i in issues if i.severity == 'error']
            warnings = [i for i in issues if i.severity == 'warning']

            status_icon = "[green]✓[/green]" if len(errors) == 0 else "[red]✗[/red]"
            status_text = "Valid" if len(errors) == 0 else "Invalid"

            console.print()
            console.print(f"{status_icon} [bold]Roadmap Validation:[/bold] {status_text}")

            if errors:
                console.print(f"\n[red]Errors: {len(errors)}[/red]")
                for issue in errors[:3]:
                    file_part = f" ({issue.file_path})" if issue.file_path else ""
                    console.print(f"  • {issue.issue}{file_part}")
                if len(errors) > 3:
                    console.print(f"  [dim]... and {len(errors) - 3} more[/dim]")

            if warnings:
                console.print(f"\n[yellow]Warnings: {len(warnings)}[/yellow]")
                for issue in warnings[:3]:
                    file_part = f" ({issue.file_path})" if issue.file_path else ""
                    console.print(f"  • {issue.issue}{file_part}")
                if len(warnings) > 3:
                    console.print(f"  [dim]... and {len(warnings) - 3} more[/dim]")

            if errors or warnings:
                console.print(f"\n[dim]Use --format detailed for more information[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@git_group.command('repair')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--dry-run', is_flag=True, default=False, help='Show what would be fixed without making changes')
@click.option('--format', 'output_format', type=click.Choice(['summary', 'detailed', 'json']), default='summary',
              help='Output format')
@click.pass_context
def repair_cmd(ctx, repo: str, dry_run: bool, output_format: str):
    """
    Detect and repair roadmap inconsistencies.

    Attempts to fix common issues like:
    - YAML syntax errors (restore from git)
    - Invalid references
    - Orphaned files

    Examples:

      vibey git repair --dry-run          # Show what would be fixed
      vibey git repair                    # Actually perform repairs
      vibey git repair --format detailed  # Verbose output
    """
    try:
        result, error = repair_roadmap(repo_path=repo, dry_run=dry_run)

        if error:
            console.print(f"[red]Error:[/red] {error}")
            sys.exit(1)

        if output_format == 'json':
            output = {
                'success': result.success,
                'issues_found': result.issues_found,
                'issues_fixed': result.issues_fixed,
                'issues_remaining': result.issues_remaining,
                'fixes_applied': result.fixes_applied,
                'errors': result.errors,
                'dry_run': dry_run
            }
            console.print(json.dumps(output, indent=2))

        elif output_format == 'detailed':
            console.print()

            # Status panel
            if dry_run:
                status_text = "DRY RUN"
                status_color = "yellow"
                status_icon = "ℹ"
            else:
                status_text = "REPAIRED" if result.success else "FAILED"
                status_color = "green" if result.success else "red"
                status_icon = "✓" if result.success else "✗"

            console.print(Panel(
                f"[bold {status_color}]{status_icon} {status_text}[/bold {status_color}]\n\n"
                f"[cyan]Issues Found:[/cyan] {result.issues_found}\n"
                f"[cyan]Issues Fixed:[/cyan] {result.issues_fixed}\n"
                f"[cyan]Issues Remaining:[/cyan] {result.issues_remaining}",
                title="Roadmap Repair",
                border_style=status_color
            ))

            # Fixes applied
            if result.fixes_applied:
                action = "Would apply" if dry_run else "Applied"
                console.print(f"\n[bold green]{action} Fixes:[/bold green]\n")
                for fix in result.fixes_applied:
                    console.print(f"  [green]✓[/green] {fix}")

            # Errors
            if result.errors:
                console.print("\n[bold red]Errors:[/bold red]\n")
                for err in result.errors:
                    console.print(f"  [red]✗[/red] {err}")

            if dry_run and result.fixes_applied:
                console.print(f"\n[yellow]This was a dry run. Remove --dry-run to apply fixes.[/yellow]")

        else:  # summary
            if dry_run:
                console.print()
                console.print(f"[yellow]ℹ[/yellow] [bold]Dry Run - Roadmap Repair[/bold]")
            else:
                status_icon = "[green]✓[/green]" if result.success else "[red]✗[/red]"
                console.print()
                console.print(f"{status_icon} [bold]Roadmap Repair[/bold]")

            console.print(f"\n[cyan]Issues found:[/cyan] {result.issues_found}")
            console.print(f"[cyan]Issues fixed:[/cyan] {result.issues_fixed}")
            console.print(f"[cyan]Issues remaining:[/cyan] {result.issues_remaining}")

            if result.fixes_applied:
                action = "Would apply" if dry_run else "Applied"
                console.print(f"\n[bold]{action} fixes:[/bold]")
                for fix in result.fixes_applied[:5]:
                    console.print(f"  • {fix}")
                if len(result.fixes_applied) > 5:
                    console.print(f"  [dim]... and {len(result.fixes_applied) - 5} more[/dim]")

            if result.errors:
                console.print(f"\n[red]Errors: {len(result.errors)}[/red]")
                for err in result.errors[:3]:
                    console.print(f"  • {err}")

            if dry_run and result.fixes_applied:
                console.print(f"\n[yellow]This was a dry run. Remove --dry-run to apply fixes.[/yellow]")

            if result.issues_found > 0:
                console.print(f"\n[dim]Use --format detailed for more information[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@git_group.command('validate-tags')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--format', 'output_format', type=click.Choice(['summary', 'detailed', 'json']), default='summary',
              help='Output format')
@click.pass_context
def validate_tags_cmd(ctx, repo: str, output_format: str):
    """
    Detect dangling tags (pointing to missing commits).

    After rebase/squash operations, tags may point to commits that
    no longer exist. This command detects such tags.

    Examples:

      vibey git validate-tags                    # Check for dangling tags
      vibey git validate-tags --format detailed  # Show all details
      vibey git validate-tags --format json      # JSON output
    """
    try:
        dangling_tags, error = find_dangling_tags(repo_path=repo)

        if error:
            console.print(f"[red]Error:[/red] {error}")
            sys.exit(1)

        if output_format == 'json':
            output = {
                'dangling_count': len(dangling_tags),
                'tags': [
                    {
                        'tag_name': tag.tag_name,
                        'commit_sha': tag.commit_sha,
                        'tag_type': tag.tag_type,
                        'entity_id': tag.entity_id,
                        'has_message': tag.message is not None
                    }
                    for tag in dangling_tags
                ]
            }
            console.print(json.dumps(output, indent=2))

        elif output_format == 'detailed':
            console.print()

            # Status panel
            status_text = "ISSUES FOUND" if dangling_tags else "ALL TAGS VALID"
            status_color = "yellow" if dangling_tags else "green"
            status_icon = "!" if dangling_tags else "✓"

            console.print(Panel(
                f"[bold {status_color}]{status_icon} {status_text}[/bold {status_color}]\n\n"
                f"[cyan]Dangling Tags:[/cyan] {len(dangling_tags)}",
                title="Tag Validation",
                border_style=status_color
            ))

            if dangling_tags:
                # Group by type
                roadmap_tags = [t for t in dangling_tags if t.tag_type in ('sprint', 'task')]
                other_tags = [t for t in dangling_tags if t.tag_type not in ('sprint', 'task')]

                if roadmap_tags:
                    console.print("\n[bold yellow]Roadmap Tags (Sprint/Task):[/bold yellow]\n")
                    for tag in roadmap_tags:
                        entity_part = f" ({tag.entity_id})" if tag.entity_id else ""
                        console.print(f"  [yellow]![/yellow] {tag.tag_name}{entity_part}")
                        console.print(f"    [dim]→ Points to: {tag.commit_sha[:8]}[/dim]")
                        if tag.message:
                            msg_preview = tag.message.split('\n')[0][:60]
                            console.print(f"    [dim]→ Message: {msg_preview}...[/dim]")

                if other_tags:
                    console.print("\n[bold]Other Tags:[/bold]\n")
                    for tag in other_tags:
                        console.print(f"  [yellow]![/yellow] {tag.tag_name}")
                        console.print(f"    [dim]→ Points to: {tag.commit_sha[:8]}[/dim]")

                console.print(f"\n[dim]Use 'vibey git repair-tags' to attempt automatic repair[/dim]")

        else:  # summary
            status_icon = "[green]✓[/green]" if not dangling_tags else "[yellow]![/yellow]"
            status_text = "All tags valid" if not dangling_tags else f"{len(dangling_tags)} dangling tags found"

            console.print()
            console.print(f"{status_icon} [bold]Tag Validation:[/bold] {status_text}")

            if dangling_tags:
                roadmap_tags = [t for t in dangling_tags if t.tag_type in ('sprint', 'task')]
                other_tags = [t for t in dangling_tags if t.tag_type not in ('sprint', 'task')]

                if roadmap_tags:
                    console.print(f"\n[yellow]Roadmap tags (sprint/task): {len(roadmap_tags)}[/yellow]")
                    for tag in roadmap_tags[:3]:
                        entity_part = f" ({tag.entity_id})" if tag.entity_id else ""
                        console.print(f"  • {tag.tag_name}{entity_part}")
                    if len(roadmap_tags) > 3:
                        console.print(f"  [dim]... and {len(roadmap_tags) - 3} more[/dim]")

                if other_tags:
                    console.print(f"\n[dim]Other tags: {len(other_tags)}[/dim]")

                console.print(f"\n[dim]Use --format detailed for more information[/dim]")
                console.print(f"[dim]Use 'vibey git repair-tags' to attempt automatic repair[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@git_group.command('repair-tags')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--strategy', type=click.Choice(['message_match']), default='message_match',
              help='Repair strategy (default: message_match)')
@click.option('--dry-run', is_flag=True, default=False, help='Show what would be repaired without making changes')
@click.option('--all-tags', is_flag=True, default=False, help='Repair all tags, not just roadmap tags')
@click.option('--format', 'output_format', type=click.Choice(['summary', 'detailed', 'json']), default='summary',
              help='Output format')
@click.pass_context
def repair_tags_cmd(ctx, repo: str, strategy: str, dry_run: bool, all_tags: bool, output_format: str):
    """
    Automatically repair dangling tags.

    Searches for commits matching the original tag and recreates
    the tags on the new commits. By default only repairs roadmap
    tags (sprint/task tags).

    Examples:

      vibey git repair-tags --dry-run      # Preview repairs
      vibey git repair-tags                # Repair roadmap tags
      vibey git repair-tags --all-tags     # Repair all dangling tags
    """
    try:
        only_roadmap = not all_tags
        summary, error = repair_all_tags(
            repo_path=repo,
            strategy=strategy,
            dry_run=dry_run,
            only_roadmap=only_roadmap
        )

        if error:
            console.print(f"[red]Error:[/red] {error}")
            sys.exit(1)

        if output_format == 'json':
            output = {
                'dangling_found': summary.dangling_found,
                'repaired': summary.repaired,
                'unfixable': summary.unfixable,
                'dry_run': dry_run,
                'repairs': [
                    {
                        'tag_name': r.tag_name,
                        'old_sha': r.old_sha,
                        'new_sha': r.new_sha,
                        'success': r.success,
                        'reason': r.reason
                    }
                    for r in summary.repairs
                ],
                'errors': summary.errors
            }
            console.print(json.dumps(output, indent=2))

        elif output_format == 'detailed':
            console.print()

            # Status panel
            if dry_run:
                status_text = "DRY RUN"
                status_color = "yellow"
                status_icon = "ℹ"
            else:
                status_text = "REPAIR COMPLETE"
                status_color = "green" if summary.unfixable == 0 else "yellow"
                status_icon = "✓" if summary.unfixable == 0 else "!"

            console.print(Panel(
                f"[bold {status_color}]{status_icon} {status_text}[/bold {status_color}]\n\n"
                f"[cyan]Dangling Found:[/cyan] {summary.dangling_found}\n"
                f"[cyan]Repaired:[/cyan] {summary.repaired}\n"
                f"[cyan]Unfixable:[/cyan] {summary.unfixable}",
                title="Tag Repair",
                border_style=status_color
            ))

            # Successful repairs
            successful = [r for r in summary.repairs if r.success]
            if successful:
                action = "Would repair" if dry_run else "Repaired"
                console.print(f"\n[bold green]{action}:[/bold green]\n")
                for repair in successful:
                    console.print(f"  [green]✓[/green] {repair.tag_name}")
                    console.print(f"    [dim]→ {repair.old_sha[:8]} → {repair.new_sha[:8]}[/dim]")

            # Failed repairs
            failed = [r for r in summary.repairs if not r.success]
            if failed:
                console.print("\n[bold red]Unfixable:[/bold red]\n")
                for repair in failed:
                    console.print(f"  [red]✗[/red] {repair.tag_name}")
                    console.print(f"    [dim]→ {repair.reason}[/dim]")

            if summary.errors:
                console.print("\n[bold red]Errors:[/bold red]\n")
                for err in summary.errors:
                    console.print(f"  [red]✗[/red] {err}")

            if dry_run and successful:
                console.print(f"\n[yellow]This was a dry run. Remove --dry-run to apply repairs.[/yellow]")

        else:  # summary
            if dry_run:
                console.print()
                console.print(f"[yellow]ℹ[/yellow] [bold]Dry Run - Tag Repair[/bold]")
            else:
                status_icon = "[green]✓[/green]" if summary.unfixable == 0 else "[yellow]![/yellow]"
                console.print()
                console.print(f"{status_icon} [bold]Tag Repair[/bold]")

            console.print(f"\n[cyan]Dangling found:[/cyan] {summary.dangling_found}")
            console.print(f"[cyan]Repaired:[/cyan] {summary.repaired}")
            console.print(f"[cyan]Unfixable:[/cyan] {summary.unfixable}")

            if summary.repaired > 0:
                action = "Would repair" if dry_run else "Repaired"
                console.print(f"\n[bold]{action} tags:[/bold]")
                successful = [r for r in summary.repairs if r.success]
                for repair in successful[:5]:
                    console.print(f"  • {repair.tag_name} ({repair.old_sha[:8]} → {repair.new_sha[:8]})")
                if len(successful) > 5:
                    console.print(f"  [dim]... and {len(successful) - 5} more[/dim]")

            if summary.unfixable > 0:
                console.print(f"\n[yellow]Unfixable: {summary.unfixable} tags[/yellow]")
                failed = [r for r in summary.repairs if not r.success]
                for repair in failed[:3]:
                    console.print(f"  • {repair.tag_name}: {repair.reason}")
                if len(failed) > 3:
                    console.print(f"  [dim]... and {len(failed) - 3} more[/dim]")

            if dry_run and summary.repaired > 0:
                console.print(f"\n[yellow]This was a dry run. Remove --dry-run to apply repairs.[/yellow]")

            if summary.dangling_found > 0:
                console.print(f"\n[dim]Use --format detailed for more information[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@git_group.command('tag-move')
@click.argument('tag_name')
@click.argument('new_sha')
@click.option('--repo', type=click.Path(exists=True), default=".", help='Path to git repository')
@click.option('--force', is_flag=True, default=False, help='Force move even if tag exists')
@click.pass_context
def tag_move_cmd(ctx, tag_name: str, new_sha: str, repo: str, force: bool):
    """
    Manually move a tag to a different commit.

    Deletes the tag from its current location and recreates it
    on the specified commit. Preserves annotation messages.

    Examples:

      vibey git tag-move sprint/my-sprint/start abc1234 --force
      vibey git tag-move task/my-task-1 def5678
    """
    try:
        success, error = move_tag(tag_name, new_sha, repo_path=repo, force=force)

        if not success:
            console.print(f"[red]Error:[/red] {error}")
            sys.exit(1)

        console.print()
        console.print(f"[green]✓[/green] [bold]Tag moved successfully[/bold]")
        console.print(f"\n[cyan]Tag:[/cyan] {tag_name}")
        console.print(f"[cyan]New commit:[/cyan] {new_sha}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# Export the group for registration in main.py
__all__ = ['git_group']
