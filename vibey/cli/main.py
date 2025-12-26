"""
Vibey CLI - Main entry point for the Vibey Agent Framework.

This module provides the main CLI interface using Click, organizing all
framework commands into logical groups.
"""

import sys
from typing import Optional, Tuple

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Version
__version__ = "2.5.0"

# Console for rich output
console = Console()

# Load unified commands to register them in the command registry
# This import triggers command registration via @unified_command decorators
try:
    from vibey.unified import commands as unified_commands  # noqa: F401
except ImportError:
    # Unified commands module not available (e.g., during packaging)
    pass


def print_banner():
    """Print the Vibey CLI banner."""
    title = Text("Vibey Agent Framework", style="bold green")
    subtitle = Text(f"Version {__version__} - Platform-Agnostic CLI", style="dim")

    panel = Panel(
        Text.assemble(title, "\n", subtitle),
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)


@click.group()
@click.version_option(version=__version__, prog_name="vibey")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress non-essential output')
@click.pass_context
def cli(ctx, verbose: bool, quiet: bool):
    """
    Vibey Agent Framework - Platform-agnostic agentic orchestration.

    The Vibey CLI provides unified access to all framework functionality:
    roadmap management, deployment, configuration, and documentation.

    Examples:

      # Initialize a new roadmap
      vibey roadmap init

      # Deploy to Claude Code
      vibey deploy --platform claude-code

      # Generate documentation
      vibey docs generate

      # Show roadmap status
      vibey roadmap status

    For command-specific help:

      vibey roadmap --help
      vibey deploy --help
    """
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose
    ctx.obj['QUIET'] = quiet

    if not quiet and ctx.invoked_subcommand is None:
        print_banner()


# ============================================================================
# Roadmap Command Group
# ============================================================================

@cli.group()
@click.option(
    '--backend', '-b',
    type=click.Choice(['auto', 'sqlite', 'yaml'], case_sensitive=False),
    default=None,
    help='Storage backend: auto (default), sqlite, or yaml'
)
@click.option(
    '--no-sync', is_flag=True,
    help='Skip auto-sync check (faster for batch operations)'
)
@click.pass_context
def roadmap(ctx, backend: Optional[str], no_sync: bool):
    """
    Manage roadmap system - tracks, sprints, tasks, and dependencies.

    The roadmap system provides hierarchical project planning with:
    - Tracks: Major feature areas or work streams
    - Sprints: Time-boxed iterations within tracks
    - Tasks: Specific work items within sprints
    - Dependencies: Blocker relationships between items

    Auto-sync: Database is automatically synced when YAML files are edited
    directly. Use --no-sync to skip this check for faster operations.

    Examples:

      vibey roadmap init           # Initialize new roadmap
      vibey roadmap status         # Show current status
      vibey roadmap show sprint-1  # Show sprint details
      vibey roadmap start task-001 # Start a task
      vibey roadmap --no-sync list # Skip sync check

    Backend modes:
      auto   - Use SQLite if available, else YAML (default)
      sqlite - Force SQLite, error if unavailable
      yaml   - Force YAML, ignore database
    """
    ctx.ensure_object(dict)
    ctx.obj['BACKEND'] = backend
    ctx.obj['NO_SYNC'] = no_sync

    # Auto-sync: check if YAML files have been modified and rebuild if needed
    if not no_sync and backend != 'yaml':
        from pathlib import Path
        from vibey.operations.roadmap.auto_sync import ensure_synced
        root_dir = Path.cwd()
        ensure_synced(root_dir, verbose=False, quiet=False)


@roadmap.command('init')
@click.option('--name', prompt='Roadmap name', help='Name of the roadmap')
@click.option('--version', default='1.0.0', help='Initial version')
@click.pass_context
def roadmap_init(ctx, name: str, version: str):
    """Initialize a new roadmap in .vibey/roadmap.yaml"""
    from vibey.cli.commands import roadmap_init_cmd

    exit_code = roadmap_init_cmd(name, version)
    sys.exit(exit_code)


@roadmap.command('status')
@click.option('--track', help='Show status for specific track')
@click.option('--sprint', help='Show status for specific sprint')
@click.option('--include-wont-do', '-w', is_flag=True, help='Include wont_do items (hidden by default)')
@click.pass_context
def roadmap_status(ctx, track: Optional[str], sprint: Optional[str], include_wont_do: bool):
    """Show roadmap status - tracks, sprints, and tasks"""
    from vibey.cli.commands import roadmap_status_cmd

    exit_code = roadmap_status_cmd(track, sprint, include_wont_do=include_wont_do)
    sys.exit(exit_code)


@roadmap.command('sync')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed sync information')
@click.pass_context
def roadmap_sync(ctx, verbose: bool):
    """Sync status from individual files to main roadmap.yaml

    Reconciles track/sprint/task status from individual YAML files
    back to the main .vibey/roadmap.yaml file. Use this after manual
    YAML edits or to fix status inconsistencies.

    Examples:
      vibey roadmap sync           # Sync all status
      vibey roadmap sync -v        # Sync with verbose output
    """
    from vibey.cli.commands import roadmap_sync_cmd

    exit_code = roadmap_sync_cmd(verbose)
    sys.exit(exit_code)


@roadmap.command('create-track')
@click.option('--name', '-n', required=True, help='Track name')
@click.option('--slug', '-s', help='URL-friendly slug (generated from name if not provided)')
@click.option('--description', '-d', default='', help='Track description')
@click.option('--priority', '-p',
              type=click.Choice(['critical', 'high', 'medium', 'low']),
              default='medium', help='Track priority')
@click.option('--start', is_flag=True, help='Mark track as started immediately')
@click.pass_context
def roadmap_create_track(ctx, name: str, slug: str, description: str,
                         priority: str, start: bool):
    """Create a new track in the roadmap.

    Creates a new track YAML file using ULID-based naming in the flat structure.
    The track is automatically added to roadmap.yaml's track list.

    Examples:
      vibey roadmap create-track --name "Authentication System"
      vibey roadmap create-track -n "Performance Optimization" -p high
      vibey roadmap create-track --name "Bug Fixes" --slug bug-fixes --start
    """
    from vibey.cli.commands import create_track_cmd

    exit_code = create_track_cmd(
        name=name,
        slug=slug,
        description=description,
        priority=priority,
        start=start
    )
    sys.exit(exit_code)


@roadmap.command('create-sprint')
@click.option('--track', '-t', required=True, help='Track ID or slug to add sprint to')
@click.option('--name', '-n', required=True, help='Sprint name')
@click.option('--goal', '-g', default='', help='Sprint goal')
@click.option('--description', '-d', default='', help='Sprint description')
@click.option('--start', is_flag=True, help='Mark sprint as started immediately')
@click.pass_context
def roadmap_create_sprint(ctx, track: str, name: str, goal: str,
                          description: str, start: bool):
    """Create a new sprint in a track.

    Creates a new sprint YAML file using ULID-based naming in the flat structure.
    The sprint is automatically linked to the parent track.

    Examples:
      vibey roadmap create-sprint --track my-track --name "Sprint 1"
      vibey roadmap create-sprint -t auth-system -n "Authentication MVP" -g "Basic login working"
      vibey roadmap create-sprint --track 01KC2D0JK06MN77ZHAGAHF5VKD --name "Sprint 1" --start
    """
    from vibey.cli.commands import create_sprint_cmd

    exit_code = create_sprint_cmd(
        track_id=track,
        name=name,
        goal=goal,
        description=description,
        start=start
    )
    sys.exit(exit_code)


@roadmap.command('create-task')
@click.option('--sprint', '-s', required=True, help='Sprint ID or slug to add task to')
@click.option('--title', '-t', required=True, help='Task title')
@click.option('--description', '-d', default='', help='Task description')
@click.option('--type', 'task_type', default='development',
              type=click.Choice(['development', 'testing', 'documentation', 'research',
                               'review', 'infrastructure', 'design']),
              help='Task type')
@click.option('--priority', '-p',
              type=click.Choice(['critical', 'high', 'medium', 'low']),
              default='medium', help='Task priority')
@click.option('--complexity', '-c',
              type=click.Choice(['simple', 'medium', 'complex']),
              default='medium', help='Task complexity (simple/medium/complex)')
@click.pass_context
def roadmap_create_task(ctx, sprint: str, title: str, description: str,
                        task_type: str, priority: str, complexity: str):
    """Create a new task in a sprint.

    Creates a new task YAML file using ULID-based naming in the flat structure.
    The task is automatically linked to the parent sprint.

    Examples:
      vibey roadmap create-task --sprint sprint-1 --title "Add login form"
      vibey roadmap create-task -s 01KC2D0JKM9HQR5VHRQ5SX5EQY -t "Write unit tests" --type testing
      vibey roadmap create-task --sprint auth-sprint-1 --title "Design auth flow" -p high -c medium
    """
    from vibey.cli.commands import create_task_cmd

    exit_code = create_task_cmd(
        sprint_id=sprint,
        title=title,
        description=description,
        task_type=task_type,
        priority=priority,
        complexity=complexity
    )
    sys.exit(exit_code)


@roadmap.command('show')
@click.argument('item_id')
@click.option('--no-compatibility', is_flag=True, help='Skip compatibility status display')
@click.pass_context
def roadmap_show(ctx, item_id: str, no_compatibility: bool):
    """Show details for a track, sprint, or task

    For sprints, also shows platform compatibility status to help
    you understand if tasks fit in your context window.

    Examples:
      vibey roadmap show sprint-1
      vibey roadmap show task-001
      vibey roadmap show my-track
    """
    from pathlib import Path
    from vibey.cli.commands import roadmap_show_cmd

    exit_code = roadmap_show_cmd(item_id)

    # Show compatibility status for sprints
    is_sprint = '-task-' not in item_id and item_id.count('-') >= 1 and not item_id.endswith('-track')

    # Heuristic: sprints have format like "track-name-N" or "something-sprint-N"
    # More reliable: check if it's not a track (no tasks) and not a task
    if not no_compatibility and is_sprint:
        try:
            from vibey.roadmap.prompts import show_compatibility_status_brief
            show_compatibility_status_brief(item_id, Path.cwd())
        except Exception:
            pass  # Silent fail - don't break show command

    sys.exit(exit_code)


@roadmap.command('start')
@click.argument('item_id')
@click.option('--skip-compatibility', is_flag=True, help='Skip compatibility check (not recommended)')
@click.option('--force', '-f', is_flag=True, help='Force start without prompts')
@click.pass_context
def roadmap_start(ctx, item_id: str, skip_compatibility: bool, force: bool):
    """Start a sprint or task

    When starting a sprint, checks if tasks fit in your platform's context
    window. If compatibility issues are found, you'll be prompted to
    recalculate before proceeding.

    Examples:
      vibey roadmap start sprint-1
      vibey roadmap start task-001
      vibey roadmap start sprint-1 --skip-compatibility
    """
    from pathlib import Path
    from vibey.cli.commands import roadmap_start_cmd

    # Check if this is a sprint (contains no '-task-')
    is_sprint = '-task-' not in item_id

    # Run compatibility check for sprints
    if is_sprint and not skip_compatibility:
        from vibey.roadmap.prompts import check_and_prompt_compatibility, PromptAction

        result = check_and_prompt_compatibility(
            sprint_id=item_id,
            project_root=Path.cwd(),
            skip_prompt=force,
        )

        if not result.should_proceed:
            console.print("[yellow]Operation cancelled[/yellow]")
            sys.exit(0)

        if result.action == PromptAction.RECALCULATE:
            console.print("[blue]Please run the recalculate command first, then try starting again.[/blue]")
            sys.exit(0)

    exit_code = roadmap_start_cmd(item_id)
    sys.exit(exit_code)


@roadmap.command('complete')
@click.argument('item_id')
@click.option('--no-commits', is_flag=True, help='Skip commit evidence check (for non-code tasks)')
@click.option('--force', '-f', is_flag=True, help='Force completion even with incomplete tasks (sprints only)')
@click.pass_context
def roadmap_complete(ctx, item_id: str, no_commits: bool, force: bool):
    """Complete a track, sprint, or task

    For sprints, validates that all tasks are completed before allowing completion.
    Use --force to override this check (with warning).

    Examples:
      vibey roadmap complete my-track                    # Complete a track
      vibey roadmap complete my-track-1                  # Complete a sprint
      vibey roadmap complete my-track-1-task-001        # Complete a task
      vibey roadmap complete task-001 --no-commits      # Skip commit check
      vibey roadmap complete sprint-1 --force           # Force complete with incomplete tasks
    """
    from vibey.cli.commands import roadmap_complete_cmd

    exit_code = roadmap_complete_cmd(item_id, skip_commit_check=no_commits, force=force)
    sys.exit(exit_code)


@roadmap.command('revert')
@click.argument('item_id')
@click.option('--to', 'target_status', required=True,
              type=click.Choice(['not_started', 'in_progress', 'completed', 'production_ready']),
              help='Target status to revert to')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def roadmap_revert(ctx, item_id: str, target_status: str, yes: bool):
    """Revert a track, sprint, or task to a previous status

    Allows undoing premature completions or status changes.
    Only backward transitions are allowed (completed → in_progress → not_started).

    Examples:
      vibey roadmap revert my-sprint --to in_progress     # Revert completed sprint
      vibey roadmap revert my-task --to not_started       # Reset task to not started
      vibey roadmap revert my-track --to in_progress -y   # Skip confirmation
    """
    from vibey.cli.commands import roadmap_revert_cmd

    exit_code = roadmap_revert_cmd(item_id, target_status, skip_confirm=yes)
    sys.exit(exit_code)


@roadmap.command('reconcile')
@click.option('--fix', is_flag=True, help='Auto-fix detected issues')
@click.option('--dry-run', is_flag=True, help='Show issues without fixing (default)')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
@click.pass_context
def roadmap_reconcile(ctx, fix: bool, dry_run: bool, verbose: bool):
    """Detect and fix status inconsistencies in roadmap data.

    Checks for status mismatches between parent/child objects:
    - Sprints marked completed but with incomplete tasks
    - Tracks marked completed but with incomplete sprints
    - Tasks marked completed but with null dates
    - Progress counts that don't match actual task counts

    By default, runs in dry-run mode (report only). Use --fix to apply corrections.

    Examples:
      vibey roadmap reconcile                  # Report issues (dry-run)
      vibey roadmap reconcile --fix            # Fix detected issues
      vibey roadmap reconcile --verbose        # Detailed report
    """
    from vibey.cli.commands import reconcile_cmd

    exit_code = reconcile_cmd(fix=fix, dry_run=dry_run, verbose=verbose)
    sys.exit(exit_code)


@roadmap.command('context')
@click.argument('task_id')
@click.pass_context
def roadmap_context(ctx, task_id: str):
    """Get AI-optimized context for a task"""
    from vibey.cli.commands import roadmap_context_cmd

    exit_code = roadmap_context_cmd(task_id)
    sys.exit(exit_code)


@roadmap.command('summarize')
@click.argument('item_type', type=click.Choice(['sprint', 'task', 'track']))
@click.argument('item_id')
@click.pass_context
def roadmap_summarize(ctx, item_type: str, item_id: str):
    """Summarize a sprint, task, or track"""
    from vibey.cli.commands import roadmap_summarize_cmd

    exit_code = roadmap_summarize_cmd(item_type, item_id)
    sys.exit(exit_code)


# ============================================================================
# Tokens Subcommand Group
# ============================================================================

@roadmap.group('tokens')
@click.pass_context
def roadmap_tokens(ctx):
    """
    Token metrics and usage reporting.

    View token estimates, budgets, usage, enforcement settings,
    and generate comprehensive usage reports.

    Examples:

      vibey roadmap tokens show 01KC2D0JK7READW9KAK1HBX4B8  # View task tokens
      vibey roadmap tokens report                           # Generate usage report
      vibey roadmap tokens budget                           # Budget utilization
      vibey roadmap tokens report --format json             # Export as JSON
    """
    pass


@roadmap_tokens.command('show')
@click.argument('item_id', required=False)
@click.option('--track', 'track_id', help='View token summary for a track')
@click.option('--sprint', 'sprint_id', help='View token summary for a sprint')
@click.option('--show-enforcement', is_flag=True, help='Show detailed enforcement settings')
@click.pass_context
def tokens_show(ctx, item_id: Optional[str], track_id: Optional[str],
                sprint_id: Optional[str], show_enforcement: bool):
    """View token metrics for a task, sprint, or track

    Displays token estimates, budgets, usage, and enforcement settings
    from the Tokens model (estimate/budget/usage/enforcement).

    Examples:
      vibey roadmap tokens show 01KC2D0JK7READW9KAK1HBX4B8   # View task tokens
      vibey roadmap tokens show --sprint 01KC2D0JKVT80AFQ6C1 # View sprint token summary
      vibey roadmap tokens show --track 01KCYA0G5135Z8B8ENFD # View track token summary
      vibey roadmap tokens show <task-id> --show-enforcement # Show enforcement details
    """
    from vibey.cli.commands import roadmap_tokens_cmd

    exit_code = roadmap_tokens_cmd(
        item_id=item_id,
        track_id=track_id,
        sprint_id=sprint_id,
        show_enforcement=show_enforcement,
    )
    sys.exit(exit_code)


@roadmap_tokens.command('report')
@click.option('--format', 'output_format', type=click.Choice(['text', 'csv', 'json']),
              default='text', help='Output format')
@click.option('--track', 'track_id', help='Filter to specific track')
@click.option('--include-empty', is_flag=True, help='Include tracks with no tasks')
@click.pass_context
def tokens_report(ctx, output_format: str, track_id: Optional[str], include_empty: bool):
    """Generate token usage report.

    Shows token usage aggregated by track and by task type, with
    estimates and actual usage compared.

    Examples:
      vibey roadmap tokens report                     # Summary report
      vibey roadmap tokens report --format json       # Export as JSON
      vibey roadmap tokens report --format csv        # Export as CSV
      vibey roadmap tokens report --track <ULID>      # Filter to track
    """
    from vibey.cli.commands import tokens_report_cmd

    exit_code = tokens_report_cmd(
        output_format=output_format,
        track_id=track_id,
        include_empty=include_empty,
    )
    sys.exit(exit_code)


@roadmap_tokens.command('budget')
@click.option('--format', 'output_format', type=click.Choice(['text', 'csv', 'json']),
              default='text', help='Output format')
@click.option('--all', 'show_all', is_flag=True, help='Show all items including those without budgets')
@click.pass_context
def tokens_budget(ctx, output_format: str, show_all: bool):
    """Show budget utilization report.

    Displays items with configured budgets and their utilization status.
    Highlights items approaching or exceeding their budgets.

    Examples:
      vibey roadmap tokens budget                     # Budget overview
      vibey roadmap tokens budget --format json       # Export as JSON
      vibey roadmap tokens budget --format csv        # Export as CSV
    """
    from vibey.cli.commands import tokens_budget_cmd

    exit_code = tokens_budget_cmd(
        output_format=output_format,
        show_all=show_all,
    )
    sys.exit(exit_code)


@roadmap.command('estimate')
@click.argument('item_id')
@click.pass_context
def roadmap_estimate(ctx, item_id: str):
    """Run token estimation for a task, sprint, or track

    Uses the TokenEstimator to set estimate.min/max/target values.
    Does not set budgets or enforcement (those are manual).

    Examples:
      vibey roadmap estimate 01KC2D0JK7READW9KAK1HBX4B8  # Estimate single task
      vibey roadmap estimate 01KC2D0JKVT80AFQ6C1PA8CKJD  # Estimate all tasks in sprint
      vibey roadmap estimate 01KCYA0G5135Z8B8ENFD841B0Q  # Estimate all tasks in track
    """
    from vibey.cli.commands import roadmap_estimate_cmd

    exit_code = roadmap_estimate_cmd(item_id)
    sys.exit(exit_code)


@roadmap.command('add-commit')
@click.argument('task_id')
@click.argument('commit_sha', required=False)
@click.option('--auto', is_flag=True, help='Use current HEAD commit')
@click.pass_context
def roadmap_add_commit(ctx, task_id: str, commit_sha: Optional[str], auto: bool):
    """Add a git commit to a task

    Examples:
      vibey roadmap add-commit task-001 4367bc8
      vibey roadmap add-commit task-001 --auto
    """
    from vibey.cli.commands import roadmap_add_commit_cmd

    exit_code = roadmap_add_commit_cmd(task_id, commit_sha, auto)
    sys.exit(exit_code)


@roadmap.command('sync-commits')
@click.option('--dry-run', is_flag=True, help='Show what would be linked without making changes')
@click.pass_context
def roadmap_sync_commits(ctx, dry_run: bool):
    """Scan git history and link commits to tasks based on commit messages

    Automatically finds commits that reference task IDs and links them
    to the corresponding tasks in the roadmap.

    Examples:
      vibey roadmap sync-commits
      vibey roadmap sync-commits --dry-run
    """
    from vibey.cli.commands import roadmap_sync_commits_cmd

    exit_code = roadmap_sync_commits_cmd(dry_run)
    sys.exit(exit_code)


@roadmap.command('validate-commits')
@click.pass_context
def roadmap_validate_commits(ctx):
    """Validate that all completed tasks have commit evidence

    Checks all completed tasks and reports any that are missing commits.

    Examples:
      vibey roadmap validate-commits
    """
    from vibey.cli.commands import roadmap_validate_commits_cmd

    exit_code = roadmap_validate_commits_cmd()
    sys.exit(exit_code)


@roadmap.command('verify-change')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--json', 'json_output', is_flag=True, help='Output JSON format')
@click.pass_context
def roadmap_verify_change(ctx, file_path: str, json_output: bool):
    """Verify a roadmap file change has a matching activity log entry

    Checks if the file's current content hash matches a file_hash_after
    in the activity log. This proves the change was made through the CLI.

    Exit codes:
      0 - File is verified (has matching activity log entry)
      1 - File is unverified (no matching entry found)
      2 - Error occurred

    Examples:
      vibey roadmap verify-change .vibey/roadmap/tasks/01KC...yaml
      vibey roadmap verify-change .vibey/roadmap/sprints/01KC...yaml --json
    """
    from pathlib import Path
    from vibey.operations.roadmap.verification import verify_change

    exit_code = verify_change(Path.cwd(), Path(file_path), json_output)
    sys.exit(exit_code)


@roadmap.command('verify-commits')
@click.argument('commit_range')
@click.option('--json', 'json_output', is_flag=True, help='Output JSON format for CI parsing')
@click.pass_context
def roadmap_verify_commits(ctx, commit_range: str, json_output: bool):
    """Verify roadmap changes in a commit range have activity log entries.

    Verifies all roadmap file changes in the specified commit range.
    Designed for CI/CD pipelines to enforce roadmap integrity.

    COMMIT_RANGE: Git revision range (e.g., main..HEAD, abc123..def456)

    Exit codes:
      0 - All commits verified
      1 - Some commits have unverified changes
      2 - Error occurred

    Examples:
      vibey roadmap verify-commits main..HEAD
      vibey roadmap verify-commits origin/main..HEAD --json
      vibey roadmap verify-commits abc123..def456

    Task: git-integration-5-task-011
    """
    from pathlib import Path
    from vibey.operations.roadmap.verification import verify_commits

    exit_code = verify_commits(Path.cwd(), commit_range, json_output)
    sys.exit(exit_code)


@roadmap.command('validate-fast')
@click.option('--profile', type=click.Choice(['quick', 'standard', 'thorough']),
              default='standard', help='Validation profile (default: standard)')
@click.option('--incremental', is_flag=True, help='Only validate changed files (requires git)')
@click.option('--verbose', '-v', is_flag=True, help='Show all errors')
@click.option('--benchmark', is_flag=True, help='Run performance benchmark')
@click.pass_context
def roadmap_validate_fast(ctx, profile: str, incremental: bool, verbose: bool, benchmark: bool):
    """Fast roadmap validation with caching and parallel loading

    Validation profiles:
      quick: <3s - Syntax only
      standard: <10s - Full validation (default)
      thorough: <20s - With git integration

    Examples:
      vibey roadmap validate-fast
      vibey roadmap validate-fast --profile quick
      vibey roadmap validate-fast --incremental
      vibey roadmap validate-fast --benchmark
    """
    from vibey.cli.commands import roadmap_validate_fast_cmd

    exit_code = roadmap_validate_fast_cmd(profile, incremental, verbose, benchmark)
    sys.exit(exit_code)


@roadmap.command('validate-advanced')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
@click.option('--check', type=click.Choice(['all', 'circular', 'orphans', 'references', 'progress']),
              default='all', help='Type of check to run')
@click.pass_context
def roadmap_validate_advanced(ctx, verbose: bool, check: str):
    """Advanced validation for complex integrity issues

    Detects:
      - Circular dependencies between tasks
      - Orphaned tasks (missing sprint references)
      - Broken task references
      - Progress counter mismatches

    Examples:
      vibey roadmap validate-advanced
      vibey roadmap validate-advanced --verbose
      vibey roadmap validate-advanced --check circular
      vibey roadmap validate-advanced --check orphans
    """
    from vibey.cli.commands import roadmap_validate_advanced_cmd

    exit_code = roadmap_validate_advanced_cmd(verbose, check)
    sys.exit(exit_code)


@roadmap.command('repair')
@click.option('--progress', 'fix_progress', is_flag=True, help='Fix progress counter mismatches (safe)')
@click.option('--references', 'fix_references', is_flag=True, help='Remove broken references (requires caution)')
@click.option('--all', 'fix_all', is_flag=True, help='Fix all auto-repairable issues')
@click.option('--dry-run', is_flag=True, help='Preview repairs without applying changes')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed repair information')
@click.pass_context
def roadmap_repair(ctx, fix_progress: bool, fix_references: bool, fix_all: bool, dry_run: bool, verbose: bool):
    """Auto-repair common roadmap integrity issues

    Repairs:
      - Progress counter mismatches (safe, auto-fixable)
      - Broken task references (removes invalid references)

    Examples:
      vibey roadmap repair --all --dry-run          # Preview all repairs
      vibey roadmap repair --progress               # Fix progress counters only
      vibey roadmap repair --all                    # Apply all repairs
      vibey roadmap repair --references --verbose   # Remove broken refs (verbose)
    """
    from vibey.cli.commands import roadmap_repair_cmd

    exit_code = roadmap_repair_cmd(fix_progress, fix_references, fix_all, dry_run, verbose)
    sys.exit(exit_code)


@roadmap.command('validate-structure')
@click.option('--fix', is_flag=True, help='Automatically delete hierarchical ULID directories')
@click.pass_context
def roadmap_validate_structure(ctx, fix: bool):
    """Validate roadmap directory structure is flat (no ULID directories).

    Ensures the roadmap uses the flat ULID-based structure:
      .vibey/roadmap/tracks/{ulid}.yaml
      .vibey/roadmap/sprints/{ulid}.yaml
      .vibey/roadmap/tasks/{ulid}.yaml

    Fails if legacy hierarchical directories exist (01KC.../01KC.../...).

    Use --fix to automatically delete hierarchical directories after
    verifying data exists in the flat structure.

    Examples:
      vibey roadmap validate-structure         # Check structure
      vibey roadmap validate-structure --fix   # Auto-fix issues
    """
    from vibey.cli.commands import validate_structure_cmd

    exit_code = validate_structure_cmd(fix)
    sys.exit(exit_code)


@roadmap.command('extract-embedded')
@click.option('--execute', is_flag=True, help='Execute extraction (default is dry-run)')
@click.option('--quiet', is_flag=True, help='Reduce output verbosity')
@click.pass_context
def roadmap_extract_embedded(ctx, execute: bool, quiet: bool):
    """Extract embedded tasks from sprint files to standalone task files.

    Scans all sprint YAML files for embedded tasks[] arrays and creates
    individual task files in the flat .vibey/roadmap/tasks/ directory.

    By default, runs in dry-run mode to show what would be extracted.
    Use --execute to actually create the task files.

    Examples:
      vibey roadmap extract-embedded            # Dry run (show what would be extracted)
      vibey roadmap extract-embedded --execute  # Create task files
      vibey roadmap extract-embedded --quiet    # Less verbose output
    """
    from vibey.cli.commands import extract_embedded_cmd

    dry_run = not execute
    verbose = not quiet

    exit_code = extract_embedded_cmd(dry_run=dry_run, verbose=verbose)
    sys.exit(exit_code)


@roadmap.command('install-hooks')
@click.option('--force', is_flag=True, help='Overwrite existing pre-commit hook')
@click.pass_context
def roadmap_install_hooks(ctx, force: bool):
    """Install git pre-commit hook for roadmap validation

    The pre-commit hook automatically validates roadmap data before
    allowing commits. This prevents corrupted or invalid data from
    being committed.

    The hook runs when .vibey/roadmap/ files are modified and:
      - Validates YAML syntax
      - Checks data integrity
      - Verifies schema compliance

    Bypass (emergency only):
      git commit --no-verify

    Examples:
      vibey roadmap install-hooks           # Install hook
      vibey roadmap install-hooks --force   # Overwrite existing hook
    """
    from vibey.cli.commands import install_hooks_cmd

    exit_code = install_hooks_cmd(force)
    sys.exit(exit_code)


@roadmap.command('uninstall-hooks')
@click.pass_context
def roadmap_uninstall_hooks(ctx):
    """Uninstall git pre-commit hook

    Removes the Vibey pre-commit validation hook from the repository.
    Only removes Vibey hooks - other hooks are left untouched.

    Examples:
      vibey roadmap uninstall-hooks
    """
    from vibey.cli.commands import uninstall_hooks_cmd

    exit_code = uninstall_hooks_cmd()
    sys.exit(exit_code)


@roadmap.command('check-hooks')
@click.pass_context
def roadmap_check_hooks(ctx):
    """Check git hook installation status

    Shows whether the Vibey pre-commit hook is installed and active.

    Examples:
      vibey roadmap check-hooks
    """
    from vibey.cli.commands import check_hooks_cmd

    exit_code = check_hooks_cmd()
    sys.exit(exit_code)


@roadmap.command('create-from-plan')
@click.argument('plan_file', type=click.Path(exists=True))
@click.option('--track', required=True, help='Track ID to add sprint to')
@click.option('--sprint', help='Override sprint ID (uses ID from plan if not specified)')
@click.option('--start', is_flag=True, help='Mark sprint as started')
@click.option('--dry-run', is_flag=True, help='Show what would be created without creating')
@click.pass_context
def roadmap_create_from_plan(ctx, plan_file: str, track: str, sprint: str, start: bool, dry_run: bool):
    """Create roadmap sprint from a plan markdown file

    Parses a sprint plan markdown file and creates:
    - Sprint YAML in hierarchical structure
    - Task YAMLs in hierarchical structure
    - Updates track to reference the sprint

    The plan file should have a standard format with:
    - Header with Sprint ID, Name, Track, Duration
    - ## Tasks section with #### Task N: Title blocks
    - Each task block can have: Description, Acceptance Criteria, Dependencies

    Examples:
      vibey roadmap create-from-plan sprint-plan.md --track main
      vibey roadmap create-from-plan sprint-plan.md --track backend --start
      vibey roadmap create-from-plan sprint-plan.md --track api --sprint sprint-5 --dry-run
    """
    from pathlib import Path
    from vibey.cli.roadmap_create_from_plan import create_sprint_from_plan

    success = create_sprint_from_plan(
        plan_path=Path(plan_file),
        track_id=track,
        sprint_id=sprint,
        start=start,
        dry_run=dry_run,
    )

    sys.exit(0 if success else 1)


@roadmap.command('sync-docs')
@click.option('--all', 'sync_all', is_flag=True, help='Sync all documentation')
@click.option('--track', help='Sync specific track only')
@click.option('--sprint', help='Sync specific sprint only')
@click.option('--summaries-only', is_flag=True, help='Only sync summary/completion files')
@click.option('--dry-run', is_flag=True, help='Preview changes without syncing')
@click.option('--delete-orphaned', is_flag=True, help='Delete files in target not in source')
@click.pass_context
def roadmap_sync_docs(ctx, sync_all: bool, track: Optional[str], sprint: Optional[str],
                       summaries_only: bool, dry_run: bool, delete_orphaned: bool):
    """Synchronize documentation from .vibey/roadmap/ to docs/roadmap/

    Copies markdown documentation from the roadmap source of truth to the
    user-facing docs directory, respecting include/exclude patterns.

    Examples:
      vibey roadmap sync-docs --all              # Sync all documentation
      vibey roadmap sync-docs --track my-track   # Sync specific track
      vibey roadmap sync-docs --dry-run          # Preview changes
      vibey roadmap sync-docs --delete-orphaned  # Clean up old files
    """
    from vibey.cli.commands import roadmap_sync_docs_cmd

    exit_code = roadmap_sync_docs_cmd(
        sync_all=sync_all,
        track=track,
        sprint=sprint,
        summaries_only=summaries_only,
        dry_run=dry_run,
        delete_orphaned=delete_orphaned
    )
    sys.exit(exit_code)


@roadmap.command('add-context')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--track', help='Add context to track')
@click.option('--sprint', help='Add context to sprint')
@click.option('--task', help='Add context to task')
@click.pass_context
def roadmap_add_context(ctx, file_path: str, track: Optional[str], sprint: Optional[str], task: Optional[str]):
    """Add a context file to a roadmap object

    Context files are stored in /context/ directories alongside roadmap objects
    and are used to preserve research, analyses, and decisions.

    Examples:
      vibey roadmap add-context design.md --track my-track
      vibey roadmap add-context analysis.md --sprint sprint-1
      vibey roadmap add-context notes.md --task task-001
    """
    from vibey.cli.commands import roadmap_add_context_cmd

    exit_code = roadmap_add_context_cmd(
        file_path=file_path,
        track=track,
        sprint=sprint,
        task=task
    )
    sys.exit(exit_code)


@roadmap.command('link-doc')
@click.argument('doc_path')
@click.argument('roadmap_object_id')
@click.option('--change-type', '-t', default='updated',
              type=click.Choice(['created', 'added_section', 'updated', 'refactored', 'removed', 'fixed']),
              help='Type of documentation change')
@click.option('--section', '-s', help='Specific section that was changed')
@click.option('--description', '-d', help='Description of the change')
@click.pass_context
def roadmap_link_doc(ctx, doc_path: str, roadmap_object_id: str,
                      change_type: str, section: Optional[str], description: Optional[str]):
    """Link a documentation file to a roadmap object

    Creates or updates a .meta.json sidecar file that tracks which roadmap
    objects have impacted this documentation.

    Examples:
      vibey roadmap link-doc docs/API.md feature-1-task-003 -t added_section -s "Authentication"
      vibey roadmap link-doc README.md infrastructure-fixes -t updated -d "Updated install steps"
    """
    from vibey.operations.roadmap.doc_tracking import link_doc_cmd

    exit_code = link_doc_cmd(doc_path, roadmap_object_id, change_type, section, description)
    sys.exit(exit_code)


@roadmap.command('list-docs')
@click.option('--object', 'roadmap_object_id', help='Filter to docs linked to this roadmap object')
@click.pass_context
def roadmap_list_docs(ctx, roadmap_object_id: Optional[str]):
    """List all tracked documentation files

    Shows all documentation files that have .meta.json tracking files,
    along with their recent impacts.

    Examples:
      vibey roadmap list-docs                    # List all tracked docs
      vibey roadmap list-docs --object task-001  # List docs linked to task-001
    """
    from vibey.operations.roadmap.doc_tracking import list_docs_cmd

    exit_code = list_docs_cmd(roadmap_object_id)
    sys.exit(exit_code)


@roadmap.command('doc-changelog')
@click.option('--object', 'filter_object_id', help='Filter to specific roadmap object')
@click.option('--start-date', help='Start date filter (YYYY-MM-DD)')
@click.option('--end-date', help='End date filter (YYYY-MM-DD)')
@click.option('--group-by', type=click.Choice(['object', 'time']), default='object',
              help='How to group changes')
@click.option('--output', '-o', 'output_file', help='Output file path (default: stdout)')
@click.pass_context
def roadmap_doc_changelog(ctx, filter_object_id: Optional[str], start_date: Optional[str],
                           end_date: Optional[str], group_by: str, output_file: Optional[str]):
    """Generate a documentation changelog

    Generates a markdown changelog showing which roadmap objects have
    impacted which documentation files.

    Examples:
      vibey roadmap doc-changelog                        # Full changelog
      vibey roadmap doc-changelog --object feature-1    # Filter to feature
      vibey roadmap doc-changelog --group-by time       # Group by date
      vibey roadmap doc-changelog -o CHANGELOG.md       # Write to file
    """
    from vibey.operations.roadmap.doc_tracking import doc_changelog_cmd

    exit_code = doc_changelog_cmd(filter_object_id, start_date, end_date, group_by, output_file)
    sys.exit(exit_code)


@roadmap.command('check-compatibility')
@click.argument('sprint_id')
@click.option('--platform', '-p', help='Override platform (auto-detect if not specified)')
@click.option('--context-window', '-c', type=int, help='Override context window size (tokens)')
@click.option('--include-completed', is_flag=True, help='Include completed tasks in analysis')
@click.option('--verbose', '-v', is_flag=True, help='Show all tasks, not just problematic ones')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.pass_context
def roadmap_check_compatibility(ctx, sprint_id: str, platform: Optional[str],
                                  context_window: Optional[int], include_completed: bool,
                                  verbose: bool, output_json: bool):
    """Check if sprint tasks fit in your platform's context window

    Analyzes all incomplete tasks in a sprint and checks if they fit
    within your current platform's context window. Oversized tasks
    need to be recalculated before starting.

    Examples:
      vibey roadmap check-compatibility auth-sprint-1
      vibey roadmap check-compatibility sprint-1 --platform goose
      vibey roadmap check-compatibility sprint-1 --context-window 128000
      vibey roadmap check-compatibility sprint-1 --verbose
      vibey roadmap check-compatibility sprint-1 --json
    """
    from pathlib import Path
    import json
    from vibey.roadmap.compatibility import (
        check_sprint_compatibility,
        format_compatibility_result,
    )

    try:
        result = check_sprint_compatibility(
            sprint_id=sprint_id,
            project_root=Path.cwd(),
            platform=platform,
            context_window=context_window,
            include_completed=include_completed,
        )

        if output_json:
            console.print(json.dumps(result.to_dict(), indent=2))
        else:
            console.print(format_compatibility_result(result, verbose=verbose))

        # Exit code based on result
        if result.needs_recalculation:
            sys.exit(1)  # Needs attention
        else:
            sys.exit(0)  # Good to go

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error checking compatibility:[/red] {e}")
        sys.exit(1)


@roadmap.command('recalculate')
@click.argument('sprint_id')
@click.option('--platform', '-p', help='Target platform (auto-detect if not specified)')
@click.option('--context-window', '-c', type=int, help='Target context window size (tokens)')
@click.option('--dry-run', is_flag=True, help='Show plan without applying changes')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def roadmap_recalculate(ctx, sprint_id: str, platform: Optional[str],
                         context_window: Optional[int], dry_run: bool,
                         verbose: bool, yes: bool):
    """Recalculate sprint tasks for a different platform

    Splits oversized tasks into subtasks that fit within the target
    platform's context window. Preserves dependencies, success criteria,
    and agent assignments.

    Examples:
      vibey roadmap recalculate auth-sprint-1
      vibey roadmap recalculate sprint-1 --platform goose
      vibey roadmap recalculate sprint-1 --context-window 128000
      vibey roadmap recalculate sprint-1 --dry-run
    """
    from pathlib import Path
    from rich.prompt import Confirm
    from vibey.roadmap.recalculator import (
        create_recalculation_plan,
        apply_recalculation,
        format_recalculation_plan,
    )

    try:
        # Create plan
        plan = create_recalculation_plan(
            sprint_id=sprint_id,
            project_root=Path.cwd(),
            target_platform=platform,
            target_context=context_window,
        )

        # Show plan
        console.print(format_recalculation_plan(plan, verbose=verbose))

        if not plan.tasks_to_split:
            console.print("\n[green]✅ No tasks need recalculation[/green]")
            sys.exit(0)

        if dry_run:
            console.print("\n[yellow]Dry run - no changes made[/yellow]")
            sys.exit(0)

        # Confirm
        if not yes:
            console.print("")
            if not Confirm.ask("Apply this recalculation?"):
                console.print("[yellow]Cancelled[/yellow]")
                sys.exit(0)

        # Apply
        result = apply_recalculation(plan, Path.cwd())

        if result.success:
            console.print(f"\n[green]✅ {result.message}[/green]")
            console.print(f"\nFiles modified: {len(result.files_modified)}")
            if verbose:
                for f in result.files_modified:
                    console.print(f"  • {f}")
            sys.exit(0)
        else:
            console.print(f"\n[red]❌ {result.message}[/red]")
            for e in result.errors:
                console.print(f"  • {e}")
            sys.exit(1)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error during recalculation:[/red] {e}")
        sys.exit(1)


@roadmap.command('sync-progress')
@click.option('--verify', is_flag=True, help='Verify consistency after recalculation')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@click.pass_context
def roadmap_sync_progress(ctx, verify: bool, verbose: bool):
    """Recalculate all progress counters from task statuses.

    When tasks are completed by directly editing YAML files (instead of using
    'vibey roadmap complete'), the parent sprint and track progress counters
    become stale. This command recalculates all progress from actual task
    statuses.

    This is useful after:
    - Manually editing task YAML files
    - Pulling changes from git that include completed tasks
    - Any situation where progress counters seem incorrect

    Examples:
      vibey roadmap sync-progress
      vibey roadmap sync-progress --verify
      vibey roadmap sync-progress -v
    """
    from pathlib import Path
    from vibey.operations.roadmap import recalculate_all

    root_dir = Path.cwd()

    if verbose:
        console.print("[blue]Recalculating all progress counters from task statuses...[/blue]")

    exit_code = recalculate_all(root_dir, verify=verify)

    if exit_code == 0:
        console.print("[green]Progress counters synchronized successfully.[/green]")
    else:
        console.print("[yellow]Progress synchronized with some issues (see above).[/yellow]")

    sys.exit(exit_code)


@roadmap.command('check-standards')
@click.argument('item_id')
@click.option('--verbose', '-v', is_flag=True, help='Show all standards including passed ones')
@click.pass_context
def roadmap_check_standards(ctx, item_id: str, verbose: bool):
    """Check which standards apply to an item

    Validates all standards that apply to a roadmap item (task/sprint/track)
    and displays the results without taking any action.

    Examples:
      vibey roadmap check-standards task-001
      vibey roadmap check-standards sprint-1 --verbose
      vibey roadmap check-standards my-track
    """
    from vibey.operations.roadmap import enforce_standards, print_enforcement_results

    # Determine item type for display
    if '-task-' in item_id:
        item_type = "Task"
    elif item_id.count('-') >= 1:
        item_type = "Sprint"
    else:
        item_type = "Track"

    console.print(f"\n[bold]🔍 Checking standards for {item_type}: {item_id}[/bold]")
    console.print("=" * 80)

    try:
        from pathlib import Path
        enforcement_result = enforce_standards(item_id, Path.cwd(), operation="check")
    except Exception as e:
        console.print(f"\n[red]❌ Failed to check standards: {e}[/red]")
        sys.exit(1)

    print_enforcement_results(enforcement_result, item_id, verbose=verbose)

    if enforcement_result.can_proceed:
        if enforcement_result.warnings:
            console.print(f"[green]✅ Item can proceed with {len(enforcement_result.warnings)} warning(s)[/green]")
        else:
            console.print("[green]✅ All standards passed - item can be completed[/green]")
        sys.exit(0)
    else:
        console.print(f"[red]❌ Item cannot proceed - {len(enforcement_result.blocking_failures)} blocking failure(s)[/red]")
        console.print("   Use 'vibey roadmap override-standard' to override specific standards")
        sys.exit(1)


@roadmap.command('add-standard')
@click.argument('level', type=click.Choice(['roadmap', 'track', 'sprint']))
@click.argument('standard_id')
@click.argument('name')
@click.argument('description')
@click.argument('type', type=click.Choice(['commit_check', 'file_check', 'test_run', 'custom_script']))
@click.argument('enforcement', type=click.Choice(['blocking', 'warning', 'audit']))
@click.argument('validation')
@click.option('--target-id', help='Track/sprint ID (required for track/sprint level)')
@click.pass_context
def roadmap_add_standard(ctx, level: str, standard_id: str, name: str, description: str,
                          type: str, enforcement: str, validation: str, target_id: Optional[str]):
    """Add a new standard to roadmap/track/sprint

    Creates a new standard that enforces a policy at the specified level.
    Standards cascade down the hierarchy (roadmap → track → sprint → task).

    VALIDATION is a JSON string with validation config, e.g. '{"min_commits": 1}'

    Examples:
      vibey roadmap add-standard roadmap commit-req "Commit Required" \\
        "All tasks must have commits" commit_check blocking '{"min_commits": 1}'

      vibey roadmap add-standard track test-cov "Test Coverage" \\
        "Must have 80% coverage" test_run warning '{"threshold": 80}' \\
        --target-id my-track
    """
    import json
    from pathlib import Path
    from datetime import datetime, timezone
    from vibey.roadmap.models import Standard, StandardType, EnforcementMode
    from vibey.roadmap.serialization import (
        load_roadmap, save_roadmap, load_track, save_track, load_sprint, save_sprint
    )
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager

    # Parse validation JSON
    try:
        validation_config = json.loads(validation)
    except json.JSONDecodeError as e:
        console.print(f"[red]❌ Invalid validation JSON: {e}[/red]")
        console.print('   Example: {"min_commits": 1}')
        sys.exit(1)

    # Create standard
    try:
        standard = Standard(
            id=standard_id,
            name=name,
            description=description,
            type=StandardType(type),
            enforcement=EnforcementMode(enforcement),
            validation=validation_config,
            created=datetime.now(timezone.utc),
            overrides=[]
        )
    except Exception as e:
        console.print(f"[red]❌ Failed to create standard: {e}[/red]")
        sys.exit(1)

    root_dir = Path.cwd()
    fs = FileSystemManager(root_dir)

    try:
        if level == 'roadmap':
            roadmap_obj = load_roadmap(root_dir)
            roadmap_obj.standards.append(standard)
            save_roadmap(roadmap_obj, root_dir)
            console.print(f"[green]✅ Added standard '{standard_id}' to roadmap[/green]")
        elif level == 'track':
            if not target_id:
                console.print("[red]❌ --target-id required for track level[/red]")
                sys.exit(1)
            track = load_track(target_id, root_dir)
            track.standards.append(standard)
            save_track(track, root_dir)
            console.print(f"[green]✅ Added standard '{standard_id}' to track '{target_id}'[/green]")
        elif level == 'sprint':
            if not target_id:
                console.print("[red]❌ --target-id required for sprint level[/red]")
                sys.exit(1)
            sprint = load_sprint(target_id, root_dir)
            sprint.standards.append(standard)
            save_sprint(sprint, root_dir)
            console.print(f"[green]✅ Added standard '{standard_id}' to sprint '{target_id}'[/green]")
    except Exception as e:
        console.print(f"[red]❌ Failed to add standard: {e}[/red]")
        sys.exit(1)

    sys.exit(0)


@roadmap.command('override-standard')
@click.argument('standard_id')
@click.argument('item_id')
@click.argument('reason')
@click.option('--overridden-by', default='system', help='Who is overriding (default: system)')
@click.pass_context
def roadmap_override_standard(ctx, standard_id: str, item_id: str, reason: str, overridden_by: str):
    """Override a standard for a specific item

    Adds an override to a standard, allowing completion even if the standard
    would normally block it. The override is tracked with reason and author.

    Examples:
      vibey roadmap override-standard commit-required task-001 \\
        "Emergency hotfix - commit to follow"

      vibey roadmap override-standard test-coverage sprint-1 \\
        "Legacy code - tests deferred" --overridden-by "tech-lead"
    """
    from pathlib import Path
    from datetime import datetime, timezone
    from vibey.roadmap.models import StandardOverride
    from vibey.roadmap.serialization import (
        load_roadmap, save_roadmap, load_track, save_track
    )
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager

    console.print(f"\n[bold]🔓 Creating override for standard '{standard_id}' on item '{item_id}'[/bold]")
    console.print(f"   Reason: {reason}")
    console.print(f"   By: {overridden_by}")

    root_dir = Path.cwd()
    fs = FileSystemManager(root_dir)

    override = StandardOverride(
        item_id=item_id,
        reason=reason,
        overridden_by=overridden_by,
        overridden_at=datetime.now(timezone.utc),
        expires_at=None
    )

    # Search for the standard in roadmap, track, sprint order
    found = False

    try:
        # Check roadmap
        roadmap_obj = load_roadmap(root_dir)
        for std in roadmap_obj.standards:
            if std.id == standard_id:
                std.overrides.append(override)
                save_roadmap(roadmap_obj, root_dir)
                console.print(f"\n[green]✅ Override added to roadmap standard[/green]")
                found = True
                break

        if not found:
            # Check all tracks
            for track_dir in fs.get_track_dirs():
                track = load_track(track_dir.name, root_dir)
                for std in track.standards:
                    if std.id == standard_id:
                        std.overrides.append(override)
                        save_track(track, root_dir)
                        console.print(f"\n[green]✅ Override added to track '{track.id}' standard[/green]")
                        found = True
                        break
                if found:
                    break

        if not found:
            console.print(f"\n[red]❌ Standard '{standard_id}' not found in roadmap hierarchy[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"\n[red]❌ Failed to add override: {e}[/red]")
        sys.exit(1)

    console.print(f"   Applies to: {item_id}")
    console.print(f"   Status: Active (no expiration)")
    sys.exit(0)


# ============================================================================
# Roadmap Audit Subgroup
# ============================================================================

@roadmap.group('audit')
@click.pass_context
def audit(ctx):
    """
    View and analyze roadmap change audit trail.

    Track all status changes with who/when/why for accountability.
    Detect suspicious changes and generate audit reports.

    Examples:

      vibey roadmap audit log                  # Show recent changes
      vibey roadmap audit show track-123       # Show object history
      vibey roadmap audit suspicious           # Find suspicious changes
      vibey roadmap audit report               # Generate detailed report
    """
    pass


@audit.command('log')
@click.option('--limit', '-n', default=20, help='Number of entries to show')
@click.pass_context
def audit_log(ctx, limit: int):
    """Show recent audit trail entries

    Display the most recent status changes across all roadmap objects.

    Examples:
      vibey roadmap audit log              # Show last 20 changes
      vibey roadmap audit log --limit 50   # Show last 50 changes
    """
    from vibey.cli.commands import audit_log_cmd

    exit_code = audit_log_cmd(limit=limit)
    sys.exit(exit_code)


@audit.command('show')
@click.argument('object_id')
@click.pass_context
def audit_show(ctx, object_id: str):
    """Show change history for a specific object

    Display all status changes for a track, sprint, or task.

    Examples:
      vibey roadmap audit show roadmap-system
      vibey roadmap audit show roadmap-system-1
      vibey roadmap audit show roadmap-system-1-task-001
    """
    from vibey.cli.commands import audit_show_cmd

    exit_code = audit_show_cmd(object_id=object_id)
    sys.exit(exit_code)


@audit.command('suspicious')
@click.pass_context
def audit_suspicious(ctx):
    """Detect suspicious changes in audit trail

    Find potentially problematic changes like:
    - Status rollbacks (completed → not_started)
    - Progress decreases
    - Manual YAML edits without git commits

    Examples:
      vibey roadmap audit suspicious
    """
    from vibey.cli.commands import audit_suspicious_cmd

    exit_code = audit_suspicious_cmd()
    sys.exit(exit_code)


@audit.command('report')
@click.option('--object-id', help='Filter by object ID')
@click.option('--start', help='Start date (YYYY-MM-DD)')
@click.option('--end', help='End date (YYYY-MM-DD)')
@click.pass_context
def audit_report(ctx, object_id: Optional[str], start: Optional[str], end: Optional[str]):
    """Generate detailed audit report

    Create a comprehensive report of audit trail entries with filters.

    Examples:
      vibey roadmap audit report                           # Full report
      vibey roadmap audit report --object-id track-123     # For one object
      vibey roadmap audit report --start 2025-01-01        # From date
    """
    from vibey.cli.commands import audit_report_cmd

    exit_code = audit_report_cmd(
        object_id=object_id,
        start_date=start,
        end_date=end
    )
    sys.exit(exit_code)


# ============================================================================
# Roadmap Activity Command (Convenience alias for audit log)
# ============================================================================

@roadmap.command('activity')
@click.option('--last', '-n', default=10, help='Number of recent activities to show')
@click.option('--object', '-o', 'object_id', default=None, help='Filter by object ID')
@click.option('--type', '-t', 'activity_type', default=None, help='Filter by activity type')
@click.pass_context
def roadmap_activity(ctx, last: int, object_id: Optional[str], activity_type: Optional[str]):
    """Show recent roadmap activity in a compact format.

    Display recent status changes, completions, and lifecycle events.
    This is a convenience command that wraps the audit log.

    Examples:
      vibey roadmap activity                   # Show last 10 activities
      vibey roadmap activity --last 20         # Show last 20 activities
      vibey roadmap activity -o sqlite-backend # Filter by object
    """
    from vibey.cli.commands import activity_cmd

    exit_code = activity_cmd(limit=last, object_id=object_id, activity_type=activity_type)
    sys.exit(exit_code)


# ============================================================================
# Roadmap Auto-Progress Command
# ============================================================================

@roadmap.command('auto-progress')
@click.option('--check', 'mode', flag_value='check', default=True,
              help='Show what would advance (dry-run mode)')
@click.option('--apply', 'mode', flag_value='apply',
              help='Actually advance eligible tickets')
@click.option('--ticket', '-t', 'ticket_id', default=None,
              help='Check/apply to specific ticket only')
@click.option('--enable', is_flag=True, help='Enable auto-progression in config')
@click.option('--disable', is_flag=True, help='Disable auto-progression in config')
@click.pass_context
def roadmap_auto_progress(ctx, mode: str, ticket_id: Optional[str],
                          enable: bool, disable: bool):
    """Check or apply automatic status progressions.

    Auto-progression advances ticket status when criteria are met.
    This feature must be enabled in .vibey/config/roadmap.yaml.

    Examples:
      vibey roadmap auto-progress --check     # Show what would advance
      vibey roadmap auto-progress --apply     # Actually advance tickets
      vibey roadmap auto-progress --enable    # Enable auto-progression
      vibey roadmap auto-progress --disable   # Disable auto-progression
    """
    from vibey.cli.commands import auto_progress_cmd

    exit_code = auto_progress_cmd(
        mode=mode,
        ticket_id=ticket_id,
        enable=enable,
        disable=disable
    )
    sys.exit(exit_code)


# ============================================================================
# Roadmap Checkpoint Subgroup
# ============================================================================

@roadmap.group('checkpoint')
@click.pass_context
def checkpoint(ctx):
    """
    Manage roadmap integrity checkpoints.

    Create, restore, verify, and compare backups of the .vibey/ directory
    with SHA-256 checksum verification and YAML validation.

    Examples:

      vibey roadmap checkpoint create              # Create timestamped checkpoint
      vibey roadmap checkpoint create my-backup    # Create named checkpoint
      vibey roadmap checkpoint list                # List all checkpoints
      vibey roadmap checkpoint verify my-backup    # Verify checkpoint integrity
      vibey roadmap checkpoint restore my-backup   # Restore from checkpoint
      vibey roadmap checkpoint compare cp1 cp2     # Compare two checkpoints
    """
    pass


@checkpoint.command('create')
@click.argument('name', required=False)
@click.pass_context
def checkpoint_create(ctx, name: Optional[str]):
    """Create a new integrity checkpoint

    Creates a timestamped backup of .vibey/ directory with SHA-256 checksums,
    manifest generation, and integrity verification.

    Examples:
      vibey roadmap checkpoint create
      vibey roadmap checkpoint create pre-refactor
    """
    from vibey.cli.commands import checkpoint_create_cmd

    exit_code = checkpoint_create_cmd(name)
    sys.exit(exit_code)


@checkpoint.command('list')
@click.pass_context
def checkpoint_list(ctx):
    """List all available checkpoints

    Shows checkpoint name, size, creation date, and validation status.
    """
    from vibey.cli.commands import checkpoint_list_cmd

    exit_code = checkpoint_list_cmd()
    sys.exit(exit_code)


@checkpoint.command('verify')
@click.argument('name')
@click.pass_context
def checkpoint_verify(ctx, name: str):
    """Verify checkpoint integrity

    Validates all files match SHA-256 checksums in manifest and
    verifies YAML syntax in all .yaml files.

    Examples:
      vibey roadmap checkpoint verify my-backup
    """
    from vibey.cli.commands import checkpoint_verify_cmd

    exit_code = checkpoint_verify_cmd(name)
    sys.exit(exit_code)


@checkpoint.command('restore')
@click.argument('name')
@click.option('--verify-only', is_flag=True, help='Verify without restoring')
@click.pass_context
def checkpoint_restore(ctx, name: str, verify_only: bool):
    """Restore from a checkpoint

    Restores .vibey/ directory from checkpoint with automatic pre-rollback
    backup and verification. Use --verify-only to test without restoring.

    Examples:
      vibey roadmap checkpoint restore my-backup --verify-only
      vibey roadmap checkpoint restore my-backup
    """
    from vibey.cli.commands import checkpoint_restore_cmd

    exit_code = checkpoint_restore_cmd(name, verify_only)
    sys.exit(exit_code)


@checkpoint.command('clean')
@click.option('--keep', type=int, default=5, help='Number of checkpoints to keep (default: 5)')
@click.pass_context
def checkpoint_clean(ctx, keep: int):
    """Clean old checkpoints

    Removes old checkpoints while keeping the N most recent.
    Interactive confirmation required before deletion.

    Examples:
      vibey roadmap checkpoint clean            # Keep last 5
      vibey roadmap checkpoint clean --keep 10  # Keep last 10
    """
    from vibey.cli.commands import checkpoint_clean_cmd

    exit_code = checkpoint_clean_cmd(keep)
    sys.exit(exit_code)


@checkpoint.command('compare')
@click.argument('checkpoint1')
@click.argument('checkpoint2')
@click.pass_context
def checkpoint_compare(ctx, checkpoint1: str, checkpoint2: str):
    """Compare two checkpoints

    Shows files added, removed, and modified between two checkpoints
    using SHA-256 checksum comparison.

    Examples:
      vibey roadmap checkpoint compare old-backup new-backup
    """
    from vibey.cli.commands import checkpoint_compare_cmd

    exit_code = checkpoint_compare_cmd(checkpoint1, checkpoint2)
    sys.exit(exit_code)


# ============================================================================
# Roadmap Edit Subgroup (Safe YAML Editing)
# ============================================================================

@roadmap.group('edit')
@click.pass_context
def edit(ctx):
    """
    Safe YAML editing with automatic validation and backups.

    All edit commands create automatic backups before modifying files and
    validate YAML syntax and schema. Bulk edits use transaction semantics
    (all-or-nothing).

    Examples:

      vibey roadmap edit file task.yaml --set status=completed
      vibey roadmap edit bulk "**/task.yaml" --set status=completed
      vibey roadmap edit validate task.yaml
      vibey roadmap edit rollback
    """
    pass


@edit.command('file')
@click.argument('file_path')
@click.option('--set', 'modifications', multiple=True, help='Field=value pairs to modify')
@click.option('--dry-run', is_flag=True, help='Preview changes without applying')
@click.pass_context
def edit_file(ctx, file_path: str, modifications: Tuple[str, ...], dry_run: bool):
    """Edit a single YAML file safely

    Modifies fields using dot notation (e.g., task.status, task.priority).
    Creates automatic backup before editing.

    Examples:
      vibey roadmap edit file task.yaml --set status=completed
      vibey roadmap edit file task.yaml --set task.priority=high --dry-run
      vibey roadmap edit file sprint.yaml --set sprint.status=completed
    """
    from vibey.cli.commands import edit_file_cmd

    exit_code = edit_file_cmd(file_path, list(modifications), dry_run)
    sys.exit(exit_code)


@edit.command('bulk')
@click.argument('file_pattern')
@click.option('--set', 'modifications', multiple=True, help='Field=value pairs to modify')
@click.option('--dry-run', is_flag=True, help='Preview changes without applying')
@click.pass_context
def edit_bulk(ctx, file_pattern: str, modifications: Tuple[str, ...], dry_run: bool):
    """Bulk edit multiple YAML files with transaction semantics

    Uses all-or-nothing transaction: if ANY file fails validation,
    ALL changes are rolled back.

    Examples:
      vibey roadmap edit bulk "sprint-2/**/task.yaml" --set status=completed
      vibey roadmap edit bulk "**/sprint.yaml" --set sprint.status=in_progress --dry-run
    """
    from vibey.cli.commands import edit_bulk_cmd

    exit_code = edit_bulk_cmd(file_pattern, list(modifications), dry_run)
    sys.exit(exit_code)


@edit.command('validate')
@click.argument('file_path', required=False)
@click.option('--all', 'validate_all', is_flag=True, help='Validate all YAML files in roadmap')
@click.pass_context
def edit_validate(ctx, file_path: Optional[str], validate_all: bool):
    """Validate YAML file(s)

    Validates YAML syntax, schema, and business logic.

    Examples:
      vibey roadmap edit validate task.yaml
      vibey roadmap edit validate --all
    """
    from vibey.cli.commands import edit_validate_cmd

    exit_code = edit_validate_cmd(file_path, validate_all)
    sys.exit(exit_code)


@edit.command('rollback')
@click.option('--last-n', type=int, default=1, help='Number of edits to rollback (default: 1)')
@click.pass_context
def edit_rollback(ctx, last_n: int):
    """Rollback recent edit operations

    Restores files from automatic backups.

    Examples:
      vibey roadmap edit rollback
      vibey roadmap edit rollback --last-n 3
    """
    from vibey.cli.commands import edit_rollback_cmd

    exit_code = edit_rollback_cmd(last_n)
    sys.exit(exit_code)


# ============================================================================
# Deploy Command Group
# ============================================================================

@cli.group()
@click.pass_context
def deploy(ctx):
    """
    Deploy framework to target platforms.

    Supports multiple AI coding assistant platforms:
    - claude-code (Claude Code)
    - goose (Goose by Block)
    - gemini (Google Gemini Code Assist)
    - aider (Aider CLI)
    - continue (Continue.dev)
    - windsurf (Windsurf/Codeium)
    - vscode (VS Code native MCP)
    - cursor (Cursor IDE)
    - copilot (GitHub Copilot)

    Examples:

      vibey deploy run --platform claude-code
      vibey deploy run --platform cursor --clean
      vibey deploy run --platform copilot
      vibey deploy list
    """
    pass


@deploy.command('run')
@click.option('--platform', type=click.Choice([
    'claude-code', 'goose', 'aider', 'gemini',
    'continue', 'windsurf', 'vscode', 'cursor', 'copilot',
    'jetbrains', 'amazonq', 'replit', 'cody', 'all'
]), required=True, help='Target platform (or "all" for all platforms)')
@click.option('--clean', is_flag=True, help='Remove existing deployment first')
@click.option('--no-validate', is_flag=True, help='Skip post-deployment validation')
@click.option('--no-roadmap-init', is_flag=True, help='Skip roadmap initialization after deployment')
@click.pass_context
def deploy_run(ctx, platform: str, clean: bool, no_validate: bool, no_roadmap_init: bool):
    """Deploy framework to specified platform"""
    from vibey.cli.deploy import deploy_cmd

    exit_code = deploy_cmd(
        platform=platform,
        clean=clean,
        validate=not no_validate,
        init_roadmap=not no_roadmap_init,
    )
    sys.exit(exit_code)


@deploy.command('list')
@click.pass_context
def deploy_list_platforms(ctx):
    """List available deployment platforms"""
    from vibey.cli.deploy import list_platforms
    list_platforms()


# ============================================================================
# Docs Command Group
# ============================================================================

@cli.group()
@click.pass_context
def docs(ctx):
    """
    Generate and manage documentation.

    Examples:

      vibey docs generate           # Generate all docs
      vibey docs generate --overwrite
      vibey docs context            # Generate context docs
    """
    pass


@docs.command('generate')
@click.option('--overwrite', is_flag=True, help='Overwrite existing docs')
@click.pass_context
def docs_generate(ctx, overwrite: bool):
    """Generate documentation from configuration"""
    from vibey.cli.commands import docs_generate_cmd

    exit_code = docs_generate_cmd(overwrite)
    sys.exit(exit_code)


@docs.command('generate-cli')
@click.option('--output', '-o', type=click.Path(),
              default='docs/reference/CLI_REFERENCE.md',
              help='Output file path')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json']),
              default='markdown', help='Output format')
@click.option('--include-hidden', is_flag=True, help='Include hidden commands')
@click.pass_context
def docs_generate_cli(ctx, output: str, format: str, include_hidden: bool):
    """
    Auto-generate CLI reference documentation from code.

    Introspects the Click command tree and generates comprehensive
    reference documentation. Output cannot drift from implementation.

    Examples:
      vibey docs generate-cli                    # Generate CLI_REFERENCE.md
      vibey docs generate-cli -o docs/cli.md    # Custom output path
      vibey docs generate-cli -f json           # Output as JSON
      vibey docs generate-cli --include-hidden  # Include hidden commands
    """
    from pathlib import Path
    from vibey.operations.docs.cli_introspector import introspect_cli
    from vibey.operations.docs.cli_reference_generator import (
        generate_cli_reference,
        GeneratorConfig,
    )

    try:
        if format == 'json':
            structure = introspect_cli()
            content = structure.to_json()
        else:
            config = GeneratorConfig(include_hidden=include_hidden)
            content = generate_cli_reference(config=config)

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)

        if not ctx.obj.get('QUIET'):
            click.echo(f"Generated: {output_path}")
            click.echo(f"Size: {output_path.stat().st_size:,} bytes")

        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@docs.command('check-drift')
@click.option('--path', '-p', type=click.Path(exists=True),
              default='docs/reference/CLI_REFERENCE.md',
              help='Path to existing CLI reference')
@click.option('--fix', is_flag=True, help='Regenerate if drift detected')
@click.option('--quiet', '-q', is_flag=True, help='Only output on drift')
@click.pass_context
def docs_check_drift(ctx, path: str, fix: bool, quiet: bool):
    """
    Check if CLI documentation has drifted from implementation.

    Compares the committed CLI reference with freshly generated output.
    Use in CI to prevent documentation drift. Returns exit code 1 if
    drift is detected (unless --fix is used).

    Examples:
      vibey docs check-drift                     # Check default path
      vibey docs check-drift -p docs/cli.md     # Check specific file
      vibey docs check-drift --fix              # Auto-fix if drifted
      vibey docs check-drift -q                 # Quiet mode for CI
    """
    from pathlib import Path
    from vibey.operations.docs.cli_reference_generator import generate_cli_reference

    try:
        doc_path = Path(path)

        if not doc_path.exists():
            if not quiet:
                click.echo(f"Documentation not found: {path}")
                click.echo("Run 'vibey docs generate-cli' to create it.")
            sys.exit(1)

        # Read existing documentation
        existing = doc_path.read_text()

        # Generate fresh documentation
        fresh = generate_cli_reference()

        # Compare (ignoring timestamps)
        def normalize(text: str) -> str:
            """Remove timestamps for comparison."""
            import re
            # Remove generated timestamp lines
            text = re.sub(r'\*\*Generated:\*\* [^\n]+', '**Generated:** <timestamp>', text)
            text = re.sub(r'\*Generated at: [^\*]+\*', '*Generated at: <timestamp>*', text)
            return text

        existing_normalized = normalize(existing)
        fresh_normalized = normalize(fresh)

        if existing_normalized == fresh_normalized:
            if not quiet:
                click.echo(f"No drift detected in {path}")
            sys.exit(0)
        else:
            if fix:
                doc_path.write_text(fresh)
                if not quiet:
                    click.echo(f"Documentation updated: {path}")
                sys.exit(0)
            else:
                click.echo(f"Drift detected in {path}!")
                click.echo("")
                click.echo("The committed CLI reference differs from the implementation.")
                click.echo("")
                click.echo("To fix this, run:")
                click.echo(f"  vibey docs generate-cli -o {path}")
                click.echo("")
                click.echo("Or use --fix flag:")
                click.echo(f"  vibey docs check-drift --fix")
                sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@docs.command('introspect')
@click.option('--format', '-f', type=click.Choice(['json', 'yaml']),
              default='json', help='Output format')
@click.option('--output', '-o', type=click.Path(), help='Output file (stdout if not specified)')
@click.pass_context
def docs_introspect(ctx, format: str, output: str):
    """
    Introspect CLI structure and output documentation data.

    Extracts structured data from the Click command tree for use in
    documentation generation, tooling, or drift detection.

    Examples:
      vibey docs introspect                  # JSON to stdout
      vibey docs introspect -f yaml          # YAML to stdout
      vibey docs introspect -o cli.json     # Save to file
    """
    from pathlib import Path
    from vibey.operations.docs.cli_introspector import introspect_cli

    try:
        structure = introspect_cli()

        if format == 'yaml':
            content = structure.to_yaml()
        else:
            content = structure.to_json()

        if output:
            Path(output).write_text(content)
            if not ctx.obj.get('QUIET'):
                click.echo(f"Written to: {output}")
        else:
            click.echo(content)

        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@docs.command('generate-mcp')
@click.option('--output', '-o', type=click.Path(),
              default='docs/reference/MCP_REFERENCE.md',
              help='Output file path')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json']),
              default='markdown', help='Output format')
@click.pass_context
def docs_generate_mcp(ctx, output: str, format: str):
    """
    Auto-generate MCP server reference documentation from code.

    Introspects the MCP server tools, resources, and prompts to generate
    comprehensive reference documentation. Output cannot drift from
    implementation.

    Examples:
      vibey docs generate-mcp                    # Generate MCP_REFERENCE.md
      vibey docs generate-mcp -o docs/mcp.md    # Custom output path
      vibey docs generate-mcp -f json           # Output as JSON
    """
    from pathlib import Path
    from vibey.operations.docs.mcp_introspector import introspect_mcp
    from vibey.operations.docs.mcp_reference_generator import generate_mcp_reference

    try:
        structure = introspect_mcp()

        if format == 'json':
            content = structure.to_json()
        else:
            content = generate_mcp_reference(structure)

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)

        if not ctx.obj.get('QUIET'):
            click.echo(f"Generated: {output_path}")
            click.echo(f"Tools: {len(structure.tools)}")
            click.echo(f"Resources: {len(structure.resources)}")
            click.echo(f"Prompts: {len(structure.prompts)}")
            click.echo(f"Size: {output_path.stat().st_size:,} bytes")

        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@docs.command('check-mcp-drift')
@click.option('--path', '-p', type=click.Path(exists=True),
              default='docs/reference/MCP_REFERENCE.md',
              help='Path to existing MCP reference')
@click.option('--fix', is_flag=True, help='Regenerate if drift detected')
@click.option('--quiet', '-q', is_flag=True, help='Only output on drift')
@click.pass_context
def docs_check_mcp_drift(ctx, path: str, fix: bool, quiet: bool):
    """
    Check if MCP documentation has drifted from implementation.

    Compares the committed MCP reference with freshly generated output.
    Use in CI to prevent documentation drift. Returns exit code 1 if
    drift is detected (unless --fix is used).

    Examples:
      vibey docs check-mcp-drift                 # Check default path
      vibey docs check-mcp-drift -p docs/mcp.md  # Check specific file
      vibey docs check-mcp-drift --fix           # Auto-fix if drifted
      vibey docs check-mcp-drift -q              # Quiet mode for CI
    """
    from pathlib import Path
    from vibey.operations.docs.mcp_reference_generator import generate_mcp_reference

    try:
        doc_path = Path(path)

        if not doc_path.exists():
            if not quiet:
                click.echo(f"Documentation not found: {path}")
                click.echo("Run 'vibey docs generate-mcp' to create it.")
            sys.exit(1)

        # Read existing documentation
        existing = doc_path.read_text()

        # Generate fresh documentation
        fresh = generate_mcp_reference()

        # Compare (ignoring timestamps)
        def normalize(text: str) -> str:
            """Remove timestamps for comparison."""
            import re
            # Remove generated timestamp lines
            text = re.sub(r'\*\*Generated:\*\* [^\n]+', '**Generated:** <timestamp>', text)
            return text

        existing_normalized = normalize(existing)
        fresh_normalized = normalize(fresh)

        if existing_normalized == fresh_normalized:
            if not quiet:
                click.echo(f"No drift detected in {path}")
            sys.exit(0)
        else:
            if fix:
                doc_path.write_text(fresh)
                if not quiet:
                    click.echo(f"Documentation updated: {path}")
                sys.exit(0)
            else:
                if not quiet:
                    click.echo(f"Drift detected in {path}")
                    click.echo("")
                    click.echo("MCP implementation has changed. Regenerate with:")
                    click.echo(f"  vibey docs generate-mcp -o {path}")
                    click.echo("")
                    click.echo("Or use --fix flag:")
                    click.echo(f"  vibey docs check-mcp-drift --fix")
                sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@docs.command('introspect-mcp')
@click.option('--format', '-f', type=click.Choice(['json']),
              default='json', help='Output format')
@click.option('--output', '-o', type=click.Path(), help='Output file (stdout if not specified)')
@click.pass_context
def docs_introspect_mcp(ctx, format: str, output: str):
    """
    Introspect MCP server structure and output documentation data.

    Extracts structured data from the MCP server for use in
    documentation generation, tooling, or drift detection.

    Examples:
      vibey docs introspect-mcp                  # JSON to stdout
      vibey docs introspect-mcp -o mcp.json      # Save to file
    """
    from pathlib import Path
    from vibey.operations.docs.mcp_introspector import introspect_mcp

    try:
        structure = introspect_mcp()
        content = structure.to_json()

        if output:
            Path(output).write_text(content)
            if not ctx.obj.get('QUIET'):
                click.echo(f"Written to: {output}")
        else:
            click.echo(content)

        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# ============================================================================
# Config Command Group
# ============================================================================

@cli.group()
@click.pass_context
def config(ctx):
    """
    Manage framework configuration.

    Examples:

      vibey config show             # Show current config
      vibey config validate         # Validate config files
      vibey config migrate          # Migrate old config format
    """
    pass


@config.command('show')
@click.pass_context
def config_show(ctx):
    """Show current configuration"""
    from vibey.cli.commands import config_show_cmd

    exit_code = config_show_cmd()
    sys.exit(exit_code)


@config.command('validate')
@click.pass_context
def config_validate(ctx):
    """Validate configuration files"""
    from vibey.cli.commands import config_validate_cmd

    exit_code = config_validate_cmd()
    sys.exit(exit_code)


@config.command('migrate')
@click.option('--backup/--no-backup', default=True, help='Create backup before migration (default: yes)')
@click.option('--dry-run', is_flag=True, help='Show what would be migrated without making changes')
@click.option('--force', is_flag=True, help='Overwrite existing modular config if present')
@click.pass_context
def config_migrate(ctx, backup: bool, dry_run: bool, force: bool):
    """Migrate legacy config to modular format"""
    from vibey.cli.commands import config_migrate_cmd

    exit_code = config_migrate_cmd(backup=backup, dry_run=dry_run, force=force)
    sys.exit(exit_code)


@config.command('rollback')
@click.option('--backup-id', help='Specific backup timestamp to restore (default: latest)')
@click.option('--list', 'list_backups', is_flag=True, help='List available backups')
@click.pass_context
def config_rollback(ctx, backup_id: str, list_backups: bool):
    """Rollback to a previous config backup"""
    from vibey.cli.commands import config_rollback_cmd

    exit_code = config_rollback_cmd(backup_id=backup_id, list_backups=list_backups)
    sys.exit(exit_code)


# ----------------------------------------------------------------------------
# Platform Configuration Commands
# ----------------------------------------------------------------------------

@config.group('platform')
@click.pass_context
def config_platform(ctx):
    """
    Manage platform detection and configuration.

    The platform system automatically detects your AI coding platform
    (Claude Code, Goose, Cursor, etc.) and its context window size.

    Examples:

      vibey config platform show            # Show current platform
      vibey config platform detect          # Force re-detection
      vibey config platform set goose       # Set platform manually
      vibey config platform set goose --context-window 100000
    """
    pass


@config_platform.command('show')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.pass_context
def config_platform_show(ctx, output_json: bool):
    """Show current platform configuration

    Displays the detected platform, configured overrides, and effective
    platform settings that will be used for compatibility checking.

    Examples:
      vibey config platform show           # Human-readable output
      vibey config platform show --json    # JSON output for scripting
    """
    from pathlib import Path
    import json
    from vibey.platform.config import get_platform_config_status
    from vibey.platform.context import format_token_count

    status = get_platform_config_status(Path.cwd())

    if output_json:
        console.print(json.dumps(status, indent=2))
        sys.exit(0)

    # Human-readable output
    effective = status['effective']
    detected = status['detected']
    configured = status['configured']

    console.print("\n[bold]Platform Configuration[/bold]")
    console.print("=" * 60)

    # Effective platform (what will be used)
    console.print(f"\n[bold green]Effective Platform:[/bold green]")
    console.print(f"  Platform:       {effective['display_name']} ({effective['name']})")
    console.print(f"  Context Window: {format_token_count(effective['context_window'])} tokens")
    console.print(f"  Vendor:         {effective['vendor']}")
    console.print(f"  Detected By:    {effective['detected_by']}")
    if effective['confidence'] > 0:
        console.print(f"  Confidence:     {effective['confidence']:.0%}")

    # Detected platform
    console.print(f"\n[bold blue]Auto-Detected:[/bold blue]")
    if detected['name'] != 'unknown':
        console.print(f"  Platform:       {detected['display_name']}")
        console.print(f"  Method:         {detected['detected_by']}")
        console.print(f"  Confidence:     {detected['confidence']:.0%}")
    else:
        console.print("  [dim]No platform detected[/dim]")

    # User configuration
    console.print(f"\n[bold yellow]User Configuration:[/bold yellow]")
    if configured['platform']:
        console.print(f"  Platform:       {configured['platform']}")
    else:
        console.print("  Platform:       [dim]Not set (using auto-detect)[/dim]")

    if configured['context_window']:
        console.print(f"  Context Window: {format_token_count(configured['context_window'])} tokens")
    else:
        console.print("  Context Window: [dim]Using platform default[/dim]")

    console.print(f"  Auto-Detect:    {'Yes' if configured['auto_detect'] else 'No'}")

    # Config file status
    console.print(f"\n[bold]Config File:[/bold]")
    console.print(f"  Path:   {status['config_file']}")
    console.print(f"  Exists: {'Yes' if status['config_exists'] else 'No'}")

    sys.exit(0)


@config_platform.command('detect')
@click.option('--verbose', '-v', is_flag=True, help='Show detection details')
@click.pass_context
def config_platform_detect(ctx, verbose: bool):
    """Force platform re-detection

    Runs platform detection and shows results without changing configuration.
    Useful for debugging detection issues.

    Examples:
      vibey config platform detect           # Run detection
      vibey config platform detect --verbose # Show all detection methods tried
    """
    from pathlib import Path
    from vibey.platform.detector import detect_platform, KNOWN_PLATFORMS
    from vibey.platform.context import format_token_count

    console.print("\n[bold]Platform Detection[/bold]")
    console.print("=" * 60)

    result = detect_platform(Path.cwd())

    if result.name != 'unknown':
        console.print(f"\n[green]✓ Detected: {result.display_name}[/green]")
        console.print(f"  Platform ID:    {result.name}")
        console.print(f"  Vendor:         {result.vendor}")
        console.print(f"  Context Window: {format_token_count(result.context_window)} tokens")
        console.print(f"  Detection:      {result.detected_by.value}")
        console.print(f"  Confidence:     {result.confidence:.0%}")

        if verbose and result.detection_details:
            console.print(f"\n[bold]Detection Details:[/bold]")
            for key, value in result.detection_details.items():
                console.print(f"  {key}: {value}")
    else:
        console.print("\n[yellow]⚠ No platform detected[/yellow]")
        console.print("  Using default context window: 128K tokens")

    if verbose:
        console.print(f"\n[bold]Known Platforms:[/bold]")
        for pid, info in KNOWN_PLATFORMS.items():
            console.print(f"  {pid}: {info['name']} ({format_token_count(info['context_window'])})")

    sys.exit(0)


@config_platform.command('set')
@click.argument('platform_name')
@click.option('--context-window', '-c', type=int, help='Override context window size (tokens)')
@click.pass_context
def config_platform_set(ctx, platform_name: str, context_window: Optional[int]):
    """Set platform configuration manually

    Override auto-detection by setting the platform manually.
    Useful when detection fails or when using a non-standard configuration.

    Examples:
      vibey config platform set claude-code       # Set to Claude Code
      vibey config platform set goose             # Set to Goose
      vibey config platform set goose --context-window 100000
    """
    from pathlib import Path
    from vibey.platform.config import set_platform, get_config_path
    from vibey.platform.validation import validate_platform_name, format_validation_result
    from vibey.platform.context import format_token_count

    # Validate platform name
    validation = validate_platform_name(platform_name)
    if validation.has_warnings():
        console.print(format_validation_result(validation, show_info=False))
        console.print("")

    # Set the platform
    config = set_platform(platform_name, context_window, Path.cwd())

    console.print(f"\n[green]✓ Platform configuration saved[/green]")
    console.print(f"  Platform:       {config.platform}")
    if config.context_window:
        console.print(f"  Context Window: {format_token_count(config.context_window)} tokens")
    console.print(f"  Config File:    {get_config_path(Path.cwd())}")

    sys.exit(0)


@config_platform.command('clear')
@click.pass_context
def config_platform_clear(ctx):
    """Clear platform configuration

    Removes manual platform configuration, reverting to auto-detection.

    Examples:
      vibey config platform clear
    """
    from pathlib import Path
    from vibey.platform.config import clear_platform_config, get_config_path

    config_path = get_config_path(Path.cwd())

    if clear_platform_config(Path.cwd()):
        console.print(f"\n[green]✓ Platform configuration cleared[/green]")
        console.print(f"  Deleted: {config_path}")
        console.print("  Platform will now use auto-detection")
    else:
        console.print(f"\n[yellow]No configuration file found at {config_path}[/yellow]")

    sys.exit(0)


@config_platform.command('list')
@click.pass_context
def config_platform_list(ctx):
    """List known platforms

    Shows all platforms that Vibey can detect and their default context windows.

    Examples:
      vibey config platform list
    """
    from vibey.platform.detector import list_known_platforms
    from vibey.platform.context import format_token_count

    platforms = list_known_platforms()

    console.print("\n[bold]Known Platforms[/bold]")
    console.print("=" * 70)
    console.print(f"{'ID':<15} {'Name':<20} {'Vendor':<15} {'Context':<10}")
    console.print("-" * 70)

    for p in platforms:
        console.print(f"{p['id']:<15} {p['name']:<20} {p['vendor']:<15} {format_token_count(p['context_window']):<10}")

    console.print("")
    console.print("Use 'vibey config platform set <id>' to configure manually")

    sys.exit(0)


# ----------------------------------------------------------------------------
# Token Estimation Configuration Commands
# ----------------------------------------------------------------------------

@config.group('estimation')
@click.pass_context
def config_estimation(ctx):
    """
    Manage automatic token estimation settings.

    Configure when and how token estimation is automatically triggered
    for tasks. Available trigger modes:
    - disabled: No automatic estimation (manual only)
    - on_creation: Auto-estimate when task is created
    - on_start_warn: Warn when starting a task without an estimate
    - on_calibration_update: Re-estimate when calibration changes

    Examples:

      vibey config estimation show            # Show current settings
      vibey config estimation set trigger on_creation
      vibey config estimation set warn_on_start_missing true
    """
    pass


@config_estimation.command('show')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.pass_context
def config_estimation_show(ctx, output_json: bool):
    """Show current auto-estimation configuration.

    Examples:
      vibey config estimation show           # Human-readable output
      vibey config estimation show --json    # JSON output for scripting
    """
    from pathlib import Path
    import json as json_module
    from vibey.services.auto_estimation import load_auto_estimation_config

    root_dir = Path.cwd()
    config = load_auto_estimation_config(root_dir)

    if output_json:
        print(json_module.dumps(config.to_dict(), indent=2))
    else:
        console.print("\n[bold]Auto-Estimation Configuration[/bold]\n")
        console.print(f"  Trigger Mode:        {config.trigger.value}")
        console.print(f"  Require Task Type:   {config.require_task_type}")
        console.print(f"  Require Complexity:  {config.require_complexity}")
        console.print(f"  Warn on Start:       {config.warn_on_start_missing}")
        console.print(f"  Re-estimate Threshold: {config.re_estimate_threshold * 100:.0f}%")
        if config.exclude_task_types:
            console.print(f"  Excluded Types:      {', '.join(config.exclude_task_types)}")
        else:
            console.print("  Excluded Types:      (none)")
        console.print("")

    sys.exit(0)


@config_estimation.command('set')
@click.argument('key')
@click.argument('value')
@click.pass_context
def config_estimation_set(ctx, key: str, value: str):
    """Set an auto-estimation configuration value.

    Available keys:
      trigger - Mode: disabled, on_creation, on_start_warn, on_calibration_update
      require_task_type - Require task type for estimation (true/false)
      require_complexity - Require complexity for estimation (true/false)
      warn_on_start_missing - Warn on start without estimate (true/false)
      re_estimate_threshold - Re-estimate threshold as decimal (e.g., 0.2 for 20%)

    Examples:
      vibey config estimation set trigger on_creation
      vibey config estimation set warn_on_start_missing false
      vibey config estimation set re_estimate_threshold 0.3
    """
    from pathlib import Path
    from vibey.services.auto_estimation import (
        load_auto_estimation_config,
        save_auto_estimation_config,
        AutoEstimationTrigger,
    )

    root_dir = Path.cwd()
    config = load_auto_estimation_config(root_dir)

    # Normalize key
    key_lower = key.lower().replace('-', '_')

    try:
        if key_lower == 'trigger':
            try:
                config.trigger = AutoEstimationTrigger(value.lower())
            except ValueError:
                valid_values = [t.value for t in AutoEstimationTrigger]
                console.print(f"[red]Error:[/red] Invalid trigger value '{value}'")
                console.print(f"Valid values: {', '.join(valid_values)}")
                sys.exit(1)
        elif key_lower == 'require_task_type':
            config.require_task_type = value.lower() in ('true', 'yes', '1')
        elif key_lower == 'require_complexity':
            config.require_complexity = value.lower() in ('true', 'yes', '1')
        elif key_lower == 'warn_on_start_missing':
            config.warn_on_start_missing = value.lower() in ('true', 'yes', '1')
        elif key_lower == 're_estimate_threshold':
            try:
                threshold = float(value)
                if not 0 <= threshold <= 1:
                    console.print("[red]Error:[/red] Threshold must be between 0 and 1")
                    sys.exit(1)
                config.re_estimate_threshold = threshold
            except ValueError:
                console.print(f"[red]Error:[/red] Invalid number '{value}'")
                sys.exit(1)
        else:
            console.print(f"[red]Error:[/red] Unknown key '{key}'")
            console.print("Valid keys: trigger, require_task_type, require_complexity, "
                         "warn_on_start_missing, re_estimate_threshold")
            sys.exit(1)

        # Save updated config
        save_auto_estimation_config(config, root_dir)
        console.print(f"[green]Updated[/green] {key} = {value}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    sys.exit(0)


@config_estimation.command('add-exclusion')
@click.argument('task_type')
@click.pass_context
def config_estimation_add_exclusion(ctx, task_type: str):
    """Add a task type to the exclusion list.

    Excluded task types will never be automatically estimated.

    Examples:
      vibey config estimation add-exclusion documentation
      vibey config estimation add-exclusion research
    """
    from pathlib import Path
    from vibey.services.auto_estimation import (
        load_auto_estimation_config,
        save_auto_estimation_config,
    )

    root_dir = Path.cwd()
    config = load_auto_estimation_config(root_dir)

    task_type_lower = task_type.lower()
    if task_type_lower not in [t.lower() for t in config.exclude_task_types]:
        config.exclude_task_types.append(task_type_lower)
        save_auto_estimation_config(config, root_dir)
        console.print(f"[green]Added[/green] '{task_type}' to exclusion list")
    else:
        console.print(f"'{task_type}' is already in the exclusion list")

    sys.exit(0)


@config_estimation.command('remove-exclusion')
@click.argument('task_type')
@click.pass_context
def config_estimation_remove_exclusion(ctx, task_type: str):
    """Remove a task type from the exclusion list.

    Examples:
      vibey config estimation remove-exclusion documentation
    """
    from pathlib import Path
    from vibey.services.auto_estimation import (
        load_auto_estimation_config,
        save_auto_estimation_config,
    )

    root_dir = Path.cwd()
    config = load_auto_estimation_config(root_dir)

    task_type_lower = task_type.lower()
    original_length = len(config.exclude_task_types)
    config.exclude_task_types = [t for t in config.exclude_task_types if t.lower() != task_type_lower]

    if len(config.exclude_task_types) < original_length:
        save_auto_estimation_config(config, root_dir)
        console.print(f"[green]Removed[/green] '{task_type}' from exclusion list")
    else:
        console.print(f"'{task_type}' was not in the exclusion list")

    sys.exit(0)


# ============================================================================
# Validate Command Group
# ============================================================================

@cli.group()
@click.pass_context
def validate(ctx):
    """
    Validate framework assets and documentation.

    Run validation checks on roadmap documentation organization
    and asset frontmatter (agents, workflows, handoffs).

    Examples:

      vibey validate docs       # Validate roadmap doc organization
      vibey validate assets     # Validate all asset frontmatter
      vibey validate assets --type agents  # Validate only agents
    """
    pass


@validate.command('docs')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@click.pass_context
def validate_docs(ctx, verbose: bool):
    """Validate documentation organization in roadmap

    Ensures all documentation follows organization standards:
    - Only core files (track.yaml, sprint.yaml, task.yaml) at their levels
    - Analysis files must be in context/ subdirectories
    - No loose files at track or sprint levels

    Examples:
      vibey validate docs
      vibey validate docs --verbose
    """
    from vibey.cli.commands import validate_docs_cmd

    exit_code = validate_docs_cmd(verbose)
    sys.exit(exit_code)


@validate.command('assets')
@click.option('--type', 'asset_type', type=click.Choice(['all', 'agents', 'workflows', 'handoffs']),
              default='all', help='Type of assets to validate')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@click.pass_context
def validate_assets(ctx, asset_type: str, verbose: bool):
    """Validate asset frontmatter (agents, workflows, handoffs)

    Checks that all markdown assets have valid YAML frontmatter
    required for MCP server dynamic tool discovery.

    Validates:
    - Required fields (id, name, type, version)
    - Valid enum values (agent types, priorities)
    - Input/output definitions
    - Step definitions for workflows

    Examples:
      vibey validate assets
      vibey validate assets --type agents
      vibey validate assets --type workflows --verbose
    """
    from vibey.cli.commands import validate_assets_cmd

    exit_code = validate_assets_cmd(asset_type, verbose)
    sys.exit(exit_code)


# ============================================================================
# Export Command Group
# ============================================================================

@cli.group()
@click.pass_context
def export(ctx):
    """
    Export Vibey assets to platform-specific formats.

    The export system translates Vibey agents, workflows, and handoffs
    to platform-native formats using the adapter architecture.

    Supported platforms:
    - mcp: MCP tools (Claude Code, JetBrains AI)
    - goose: Goose recipes + extension manifest

    Examples:

      vibey export --platform goose    # Export to Goose format
      vibey export --platform all      # Export to all platforms
      vibey export --list              # List available platforms
    """
    pass


@export.command('run')
@click.option('--platform', '-p', default='all', help='Platform to export to (mcp, goose, all)')
@click.option('--output', '-o', type=click.Path(), default='./exports', help='Output directory')
@click.option('--dry-run', is_flag=True, help='Show what would be exported without writing')
@click.pass_context
def export_run(ctx, platform: str, output: str, dry_run: bool):
    """Export assets to platform format

    Generates platform-specific files from Vibey assets (agents, workflows).

    Examples:
      vibey export run --platform goose           # Export to Goose
      vibey export run --platform mcp             # Export MCP tools
      vibey export run --platform all             # Export to all platforms
      vibey export run --platform goose --dry-run # Preview export
    """
    from pathlib import Path
    from vibey.adapters import create_default_registry

    output_dir = Path(output)
    registry = create_default_registry()

    if dry_run:
        console.print(f"\n[yellow]Dry run - no files will be written[/yellow]")

    if platform == 'all':
        platforms = registry.list_platforms()
    else:
        platforms = [platform]

    for plat in platforms:
        adapter = registry.get(plat)
        if not adapter:
            console.print(f"[red]Unknown platform: {plat}[/red]")
            console.print(f"Available: {', '.join(registry.list_platforms())}")
            sys.exit(1)

        info = adapter.get_info()
        console.print(f"\n[bold]{info.display_name}[/bold] ({info.platform_name})")

        if dry_run:
            # Show what would be exported
            if hasattr(adapter, 'get_tools'):
                tools = adapter.get_tools()
                console.print(f"  Would export {len(tools)} MCP tools")
            if hasattr(adapter, 'get_recipes'):
                recipes = adapter.get_recipes()
                console.print(f"  Would export {len(recipes)} recipes")
            if hasattr(adapter, 'get_extension_manifest'):
                console.print(f"  Would export extension manifest")
        else:
            # Actually export
            plat_dir = output_dir / plat if platform == 'all' else output_dir
            result = adapter.export(plat_dir)

            if result.success:
                console.print(f"  [green]✓ Exported {result.file_count} files to {plat_dir}[/green]")
                for f in result.files[:5]:
                    console.print(f"    - {f.name}")
                if result.file_count > 5:
                    console.print(f"    ... and {result.file_count - 5} more")
            else:
                console.print(f"  [red]✗ Export failed: {result.errors}[/red]")

    sys.exit(0)


@export.command('list')
@click.pass_context
def export_list(ctx):
    """List available export platforms

    Shows all platforms that Vibey can export to, with their capabilities.

    Examples:
      vibey export list
    """
    from vibey.adapters import create_default_registry

    registry = create_default_registry()
    adapters = registry.list_adapters()

    console.print("\n[bold]Available Export Platforms[/bold]")
    console.print("=" * 70)

    for info in adapters:
        type_badge = "[cyan]base[/cyan]" if info.adapter_type == "base" else "[magenta]composite[/magenta]"
        console.print(f"\n{info.platform_name} - {info.display_name} {type_badge}")
        if info.base_platform:
            console.print(f"  Uses: {info.base_platform}")
        console.print(f"  {info.description}")

        caps = info.capabilities
        cap_list = []
        if caps.agents:
            cap_list.append("agents")
        if caps.workflows:
            cap_list.append("workflows")
        if caps.recipes:
            cap_list.append("recipes")
        if caps.extension_manifest:
            cap_list.append("manifest")
        console.print(f"  Capabilities: {', '.join(cap_list)}")

    console.print("")
    sys.exit(0)


@export.command('gemini')
@click.option('--output', '-o', type=click.Path(), default='./vibey-gemini-extension',
              help='Output directory for extension package')
@click.option('--no-install-script', is_flag=True, help='Skip generating install.sh')
@click.option('--no-readme', is_flag=True, help='Skip generating README.md')
@click.option('--validate', is_flag=True, help='Validate existing export for drift')
@click.option('--dry-run', is_flag=True, help='Show what would be generated without writing')
@click.pass_context
def export_gemini(ctx, output: str, no_install_script: bool, no_readme: bool,
                   validate: bool, dry_run: bool):
    """Export Vibey to Gemini Code Assist extension format

    Generates a complete Gemini extension package with:
    - GEMINI.md context file (from agent frontmatter)
    - TOML custom commands (from workflow frontmatter)
    - MCP server configuration
    - Extension manifest

    ZERO-DRIFT: All artifacts are generated from frontmatter.
    If source agents/workflows change, re-run export to update.

    Examples:
      vibey export gemini                            # Export to ./vibey-gemini-extension/
      vibey export gemini -o ./dist/gemini           # Custom output directory
      vibey export gemini --validate                 # Check for manual edits
      vibey export gemini --dry-run                  # Preview without writing
    """
    from pathlib import Path
    from vibey.adapters.gemini import GeminiAdapter

    output_dir = Path(output)
    vibey_root = Path.cwd()

    # Initialize adapter
    adapter = GeminiAdapter(vibey_root)

    # Validate mode
    if validate:
        if not output_dir.exists():
            console.print(f"[red]Export directory not found: {output_dir}[/red]")
            console.print("Run 'vibey export gemini' first to create the export.")
            sys.exit(1)

        console.print(f"\n[bold]Validating Gemini export: {output_dir}[/bold]")
        is_valid, errors = adapter.validate_export(output_dir)

        if is_valid:
            console.print("[green]✓ No drift detected - export matches source[/green]")
            sys.exit(0)
        else:
            console.print("[red]✗ Drift detected![/red]")
            for error in errors:
                console.print(f"  • {error}")
            console.print("\nRun 'vibey export gemini' to regenerate.")
            sys.exit(1)

    # Dry run mode
    if dry_run:
        console.print(f"\n[yellow]Dry run - no files will be written[/yellow]")
        console.print(f"Would export to: {output_dir}\n")

        # Show what would be generated
        from vibey.mcp.discovery.agents import AgentDiscovery
        from vibey.mcp.discovery.workflows import WorkflowDiscovery

        agents = AgentDiscovery(vibey_root).discover()
        workflows = WorkflowDiscovery(vibey_root).discover()

        console.print(f"[bold]Would generate:[/bold]")
        console.print(f"  • GEMINI.md (context from {len(agents)} agents)")
        console.print(f"  • {len(workflows)} workflow commands (TOML)")
        console.print(f"  • {len(agents)} agent shortcut commands (TOML)")
        console.print(f"  • 3 utility commands (status, sprint, task)")
        console.print(f"  • gemini-extension.json (manifest)")
        console.print(f"  • settings.json (MCP config)")
        if not no_install_script:
            console.print(f"  • install.sh")
        if not no_readme:
            console.print(f"  • README.md")
        console.print(f"  • .checksums.json (drift detection)")

        sys.exit(0)

    # Full export
    console.print(f"\n[bold]Exporting to Gemini extension format[/bold]")
    console.print(f"Output: {output_dir}\n")

    result = adapter.export(
        output_dir=output_dir,
        include_install_script=not no_install_script,
        include_readme=not no_readme,
    )

    if result.success:
        console.print(f"[green]✓ Export complete![/green]")
        console.print(f"\n[bold]Generated files:[/bold]")
        for f in result.files_created:
            rel_path = f.relative_to(output_dir) if f.is_relative_to(output_dir) else f
            console.print(f"  • {rel_path}")

        console.print(f"\n[bold]Summary:[/bold]")
        if result.context:
            console.print(f"  Agents:    {result.context.agents_count}")
            console.print(f"  Workflows: {result.context.workflows_count}")
        if result.commands:
            console.print(f"  Commands:  {len(result.commands.commands)}")
        console.print(f"  Duration:  {result.duration_seconds:.2f}s")

        console.print(f"\n[bold]Checksums (for drift detection):[/bold]")
        for name, checksum in result.checksums.items():
            console.print(f"  {name}: {checksum}")

        console.print(f"\n[bold]Next steps:[/bold]")
        console.print(f"  1. Install extension: gemini extensions install {output_dir}")
        console.print(f"  2. Or run: {output_dir}/install.sh")
        console.print(f"  3. Verify with: /mcp in Gemini CLI")

        sys.exit(0)
    else:
        console.print(f"[red]✗ Export failed[/red]")
        for error in result.errors:
            console.print(f"  • {error}")
        sys.exit(1)


@export.command('stats')
@click.option('--platform', '-p', default='mcp', help='Platform to show stats for')
@click.pass_context
def export_stats(ctx, platform: str):
    """Show export statistics

    Displays counts of tools, recipes, and other assets for a platform.

    Examples:
      vibey export stats                 # Show MCP stats
      vibey export stats --platform goose
    """
    from vibey.adapters import create_default_registry

    registry = create_default_registry()
    adapter = registry.get(platform)

    if not adapter:
        console.print(f"[red]Unknown platform: {platform}[/red]")
        sys.exit(1)

    info = adapter.get_info()
    console.print(f"\n[bold]{info.display_name} Statistics[/bold]")
    console.print("=" * 50)

    if hasattr(adapter, 'get_stats'):
        stats = adapter.get_stats()
        for key, value in stats.items():
            console.print(f"  {key}: {value}")
    else:
        if hasattr(adapter, 'get_tools'):
            tools = adapter.get_tools()
            agents = [t for t in tools if t.get('_metadata', {}).get('asset_type') == 'agent']
            workflows = [t for t in tools if t.get('_metadata', {}).get('asset_type') == 'workflow']
            console.print(f"  Total tools: {len(tools)}")
            console.print(f"  Agent tools: {len(agents)}")
            console.print(f"  Workflow tools: {len(workflows)}")

        if hasattr(adapter, 'get_recipes'):
            recipes = adapter.get_recipes()
            console.print(f"  Recipes: {len(recipes)}")

    console.print("")
    sys.exit(0)


# ============================================================================
# Git Command Group
# ============================================================================

from vibey.cli.git_commands import git_group
cli.add_command(git_group, name='git')


# ============================================================================
# Implement Command Group (Implementation Mode)
# ============================================================================

from vibey.cli.implement import implement
cli.add_command(implement, name='implement')


# ============================================================================
# Content Command Group
# ============================================================================

@cli.group()
@click.pass_context
def content(ctx):
    """
    Manage framework content (agents, workflows, templates, handoffs).

    Provides CRUD operations for content management with validation,
    backups, and search capabilities.

    Examples:

      vibey content list                  # List all content
      vibey content list --type agent     # List only agents
      vibey content show coordinator      # Show content details
      vibey content search "database"     # Search content
      vibey content create agent          # Create new agent
      vibey content edit coordinator      # Edit existing content
      vibey content delete my-agent       # Delete content
      vibey content validate              # Validate all content
    """
    pass


@content.command('list')
@click.option('--type', 'content_type', type=click.Choice(['agent', 'workflow', 'template', 'handoff', 'schema', 'example']),
              help='Filter by content type')
@click.option('--category', help='Filter by category (subdirectory)')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json', 'simple']), default='table',
              help='Output format')
@click.pass_context
def content_list(ctx, content_type: Optional[str], category: Optional[str], output_format: str):
    """List all content items

    Shows all agents, workflows, templates, and other content with
    optional filtering by type and category.

    Examples:
      vibey content list                    # List all content
      vibey content list --type agent       # List only agents
      vibey content list --type workflow --category planning
      vibey content list --format json      # JSON output
    """
    import json
    from rich.table import Table
    from vibey.operations.content import list_content, ContentType

    ctype = ContentType(content_type) if content_type else None
    items = list_content(ctype, category)

    if not items:
        console.print("[yellow]No content found[/yellow]")
        sys.exit(0)

    if output_format == 'json':
        data = [item.to_dict() for item in items]
        console.print(json.dumps(data, indent=2))
    elif output_format == 'simple':
        for item in items:
            console.print(f"{item.content_type.value}/{item.category or 'root'}/{item.id}")
    else:
        # Table format
        table = Table(title=f"Content ({len(items)} items)")
        table.add_column("Type", style="cyan")
        table.add_column("Category", style="dim")
        table.add_column("ID", style="green")
        table.add_column("Name")
        table.add_column("Version", style="dim")

        for item in sorted(items, key=lambda x: (x.content_type.value, x.category or '', x.id)):
            table.add_row(
                item.content_type.value,
                item.category or "-",
                item.id,
                item.name,
                item.metadata.version
            )

        console.print(table)

    sys.exit(0)


@content.command('show')
@click.argument('content_id')
@click.option('--type', 'content_type', type=click.Choice(['agent', 'workflow', 'template', 'handoff', 'schema', 'example']),
              help='Content type (speeds up lookup)')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--body', is_flag=True, help='Include full body text')
@click.pass_context
def content_show(ctx, content_id: str, content_type: Optional[str], output_json: bool, body: bool):
    """Show content details

    Displays metadata and optionally the full body of a content item.

    Examples:
      vibey content show coordinator
      vibey content show sprint-planning --type workflow
      vibey content show coordinator --body
      vibey content show coordinator --json
    """
    import json
    from vibey.operations.content import load_content, ContentType

    ctype = ContentType(content_type) if content_type else None
    item = load_content(content_id, ctype)

    if item is None:
        console.print(f"[red]Content not found: {content_id}[/red]")
        sys.exit(1)

    if output_json:
        data = item.to_dict()
        if body:
            data['body'] = item.body
        console.print(json.dumps(data, indent=2))
    else:
        console.print(f"\n[bold]{item.name}[/bold] ({item.id})")
        console.print("=" * 60)
        console.print(f"Type:     {item.content_type.value}")
        console.print(f"Category: {item.category or 'root'}")
        console.print(f"Version:  {item.metadata.version}")
        console.print(f"Path:     {item.relative_path}")

        if item.metadata.description:
            console.print(f"\n[bold]Description:[/bold]\n{item.metadata.description}")

        if item.metadata.tags:
            console.print(f"\n[bold]Tags:[/bold] {', '.join(item.metadata.tags)}")

        # Show type-specific extra fields
        if item.metadata.extra:
            console.print(f"\n[bold]Metadata:[/bold]")
            for key, value in item.metadata.extra.items():
                if isinstance(value, (list, dict)):
                    console.print(f"  {key}: {json.dumps(value, indent=4)}")
                else:
                    console.print(f"  {key}: {value}")

        if body:
            console.print(f"\n[bold]Body:[/bold]")
            console.print(item.body)

    sys.exit(0)


@content.command('search')
@click.argument('query')
@click.option('--type', 'content_type', type=click.Choice(['agent', 'workflow', 'template', 'handoff', 'schema', 'example']),
              help='Filter by content type')
@click.option('--category', help='Filter by category')
@click.option('--limit', default=20, help='Maximum results')
@click.pass_context
def content_search(ctx, query: str, content_type: Optional[str], category: Optional[str], limit: int):
    """Search content by keywords

    Searches content by name, description, tags, and body text.
    Results are ranked by relevance.

    Examples:
      vibey content search "database"
      vibey content search "api" --type agent
      vibey content search "test" --limit 50
    """
    from rich.table import Table
    from vibey.operations.content import search_content, ContentType

    ctype = ContentType(content_type) if content_type else None
    results = search_content(query, ctype, category, limit=limit)

    if not results:
        console.print(f"[yellow]No results for '{query}'[/yellow]")
        sys.exit(0)

    table = Table(title=f"Search Results for '{query}' ({len(results)} matches)")
    table.add_column("Score", style="dim", width=6)
    table.add_column("Type", style="cyan")
    table.add_column("ID", style="green")
    table.add_column("Name")
    table.add_column("Matched", style="dim")

    for result in results:
        table.add_row(
            f"{result.score:.0f}",
            result.item.content_type.value,
            result.item.id,
            result.item.name,
            ", ".join(result.matched_fields[:3])
        )

    console.print(table)
    sys.exit(0)


@content.command('create')
@click.argument('content_type', type=click.Choice(['agent', 'workflow', 'template', 'handoff']))
@click.option('--id', 'content_id', required=True, help='Content ID (e.g., my-agent)')
@click.option('--name', required=True, help='Display name')
@click.option('--category', help='Category (subdirectory, e.g., core, planning)')
@click.option('--subtype', help='Subtype (e.g., core, planning, development for agents)')
@click.option('--description', default='', help='Description')
@click.option('--version', default='1.0.0', help='Version')
@click.pass_context
def content_create(ctx, content_type: str, content_id: str, name: str,
                   category: Optional[str], subtype: Optional[str],
                   description: str, version: str):
    """Create new content

    Creates a new agent, workflow, template, or handoff with
    validated frontmatter and a starter body.

    Examples:
      vibey content create agent --id my-agent --name "My Agent" --category core --subtype core
      vibey content create workflow --id my-flow --name "My Workflow" --subtype planning
      vibey content create template --id my-template --name "My Template"
    """
    from vibey.operations.content import create_content, ContentType

    ctype = ContentType(content_type)

    frontmatter = {
        'id': content_id,
        'name': name,
        'version': version,
    }

    if subtype:
        frontmatter['type'] = subtype
    elif ctype == ContentType.AGENT:
        frontmatter['type'] = 'development'  # Default agent type
    elif ctype == ContentType.WORKFLOW:
        frontmatter['type'] = 'development'  # Default workflow type

    if description:
        frontmatter['description'] = description

    # Default body based on content type
    if ctype == ContentType.AGENT:
        body = f"""# {name}

**Role:** [Describe the agent's role]

## Purpose

[Describe what this agent does]

## Trigger Patterns

- keyword1
- keyword2

## Required Inputs

- Input 1
- Input 2

## Outputs

- Output 1
- Output 2

## Quality Criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Handoffs

- Hands off to: [agent-id]
"""
    elif ctype == ContentType.WORKFLOW:
        body = f"""# {name}

## Overview

[Describe the workflow]

## Steps

1. **Step 1**: [Description]
2. **Step 2**: [Description]
3. **Step 3**: [Description]

## Prerequisites

- Prerequisite 1
- Prerequisite 2

## Expected Outputs

- Output 1
- Output 2
"""
    else:
        body = f"""# {name}

[Content here]
"""

    result = create_content(ctype, frontmatter, body, category)

    if result.success:
        console.print(f"[green]✓ Created {content_type}: {content_id}[/green]")
        if result.content:
            console.print(f"  Path: {result.content.filepath}")
    else:
        console.print(f"[red]✗ Failed to create {content_type}[/red]")
        for error in result.errors:
            console.print(f"  • {error}")
        sys.exit(1)

    sys.exit(0)


@content.command('edit')
@click.argument('content_id')
@click.option('--set', 'updates', multiple=True, help='Field=value pairs to update')
@click.option('--type', 'content_type', type=click.Choice(['agent', 'workflow', 'template', 'handoff']),
              help='Content type')
@click.pass_context
def content_edit(ctx, content_id: str, updates: tuple, content_type: Optional[str]):
    """Edit existing content

    Updates frontmatter fields in existing content.
    Creates a backup before making changes.

    Examples:
      vibey content edit coordinator --set version=1.1.0
      vibey content edit my-agent --set type=core --set "description=New description"
    """
    from vibey.operations.content import update_content, ContentType

    if not updates:
        console.print("[yellow]No updates specified. Use --set field=value[/yellow]")
        sys.exit(1)

    # Parse updates into dict
    update_dict = {}
    for update in updates:
        if '=' not in update:
            console.print(f"[red]Invalid update format: {update}[/red]")
            console.print("Use: --set field=value")
            sys.exit(1)
        key, value = update.split('=', 1)
        update_dict[key] = value

    ctype = ContentType(content_type) if content_type else None
    result = update_content(content_id, update_dict, ctype)

    if result.success:
        console.print(f"[green]✓ Updated {content_id}[/green]")
        if result.backup_path:
            console.print(f"  Backup: {result.backup_path}")
    else:
        console.print(f"[red]✗ Failed to update {content_id}[/red]")
        for error in result.errors:
            console.print(f"  • {error}")
        sys.exit(1)

    sys.exit(0)


@content.command('delete')
@click.argument('content_id')
@click.option('--type', 'content_type', type=click.Choice(['agent', 'workflow', 'template', 'handoff']),
              help='Content type')
@click.option('--force', is_flag=True, help='Delete even if referenced by other content')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def content_delete(ctx, content_id: str, content_type: Optional[str], force: bool, yes: bool):
    """Delete content (moves to trash)

    Removes content by moving it to .vibey/trash/.
    Can be restored later if needed.

    Examples:
      vibey content delete my-agent
      vibey content delete my-agent --force
      vibey content delete my-agent -y
    """
    from rich.prompt import Confirm
    from vibey.operations.content import delete_content, load_content, ContentType

    ctype = ContentType(content_type) if content_type else None

    # First verify content exists
    item = load_content(content_id, ctype)
    if item is None:
        console.print(f"[red]Content not found: {content_id}[/red]")
        sys.exit(1)

    # Confirm deletion
    if not yes:
        console.print(f"\n[yellow]About to delete: {item.name} ({item.id})[/yellow]")
        console.print(f"  Type: {item.content_type.value}")
        console.print(f"  Path: {item.filepath}")
        console.print("")
        if not Confirm.ask("Delete this content?"):
            console.print("[dim]Cancelled[/dim]")
            sys.exit(0)

    result = delete_content(content_id, ctype, force)

    if result.success:
        console.print(f"[green]✓ Deleted {content_id}[/green]")
        if result.backup_path:
            console.print(f"  Moved to: {result.backup_path}")
    else:
        console.print(f"[red]✗ Failed to delete {content_id}[/red]")
        for error in result.errors:
            console.print(f"  • {error}")
        sys.exit(1)

    sys.exit(0)


@content.command('validate')
@click.argument('content_id', required=False)
@click.option('--type', 'content_type', type=click.Choice(['agent', 'workflow', 'template', 'handoff']),
              help='Content type to validate')
@click.option('--all', 'validate_all', is_flag=True, help='Validate all content')
@click.pass_context
def content_validate_cmd(ctx, content_id: Optional[str], content_type: Optional[str], validate_all: bool):
    """Validate content frontmatter

    Checks content for required fields and valid values.

    Examples:
      vibey content validate coordinator
      vibey content validate --type agent --all
      vibey content validate --all
    """
    from vibey.operations.content import list_content, load_content, ContentType
    from vibey.operations.content.writer import ContentValidator

    validator = ContentValidator()

    if content_id:
        # Validate single content
        ctype = ContentType(content_type) if content_type else None
        item = load_content(content_id, ctype)

        if item is None:
            console.print(f"[red]Content not found: {content_id}[/red]")
            sys.exit(1)

        result = validator.validate(item.content_type, item._raw_frontmatter, item.body)

        if result.is_valid:
            console.print(f"[green]✓ {content_id} is valid[/green]")
            if result.warnings:
                for warning in result.warnings:
                    console.print(f"  [yellow]Warning: {warning}[/yellow]")
            sys.exit(0)
        else:
            console.print(f"[red]✗ {content_id} has errors[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
            sys.exit(1)
    else:
        # Validate multiple content
        ctype = ContentType(content_type) if content_type else None
        items = list_content(ctype)

        if not items:
            console.print("[yellow]No content to validate[/yellow]")
            sys.exit(0)

        valid_count = 0
        invalid_count = 0
        errors_by_item = {}

        for item in items:
            result = validator.validate(item.content_type, item._raw_frontmatter, item.body)
            if result.is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                errors_by_item[item.id] = result.errors

        console.print(f"\n[bold]Validation Results[/bold]")
        console.print(f"  Valid:   {valid_count}")
        console.print(f"  Invalid: {invalid_count}")
        console.print(f"  Total:   {len(items)}")

        if errors_by_item:
            console.print(f"\n[red]Items with errors:[/red]")
            for item_id, errors in list(errors_by_item.items())[:10]:
                console.print(f"\n  {item_id}:")
                for error in errors[:3]:
                    console.print(f"    • {error}")
                if len(errors) > 3:
                    console.print(f"    ... and {len(errors) - 3} more")

            if len(errors_by_item) > 10:
                console.print(f"\n  ... and {len(errors_by_item) - 10} more items with errors")

        sys.exit(0 if invalid_count == 0 else 1)


# ============================================================================
# Database Subcommand Group
# ============================================================================

@roadmap.group('db')
@click.pass_context
def roadmap_db(ctx):
    """
    Database operations for roadmap state management.

    The database backend provides faster queries and automatic integrity
    enforcement via SQLite. Use these commands to manage the database.

    Examples:

      vibey roadmap db init       # Initialize database from YAML
      vibey roadmap db status     # Show database status
      vibey roadmap db rebuild    # Rebuild database from YAML
      vibey roadmap db backup     # Create database backup
    """
    pass


@roadmap_db.command('init')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing database')
@click.pass_context
def db_init(ctx, force: bool):
    """Initialize SQLite database from YAML files.

    Creates .vibey/roadmap.db with all roadmap data loaded from YAML.
    Computes checksums for change detection and sets up triggers.

    Examples:
      vibey roadmap db init
      vibey roadmap db init --force  # Overwrite existing
    """
    from vibey.cli.commands import db_init_cmd

    exit_code = db_init_cmd(force=force)
    sys.exit(exit_code)


@roadmap_db.command('rebuild')
@click.option('--force', '-f', is_flag=True, help='Force rebuild even with uncommitted changes')
@click.option('--strict', is_flag=True, help='Abort on first validation error')
@click.option('--verbose', '-v', is_flag=True, help='Show each file as it is processed')
@click.pass_context
def db_rebuild(ctx, force: bool, strict: bool, verbose: bool):
    """Rebuild database from YAML files.

    Drops all tables and reloads from YAML. Use after pulling changes
    or to fix database corruption.

    WARNING: Uncommitted database changes will be lost!

    Examples:
      vibey roadmap db rebuild
      vibey roadmap db rebuild --force    # Skip dirty check
      vibey roadmap db rebuild --verbose  # Show progress
      vibey roadmap db rebuild --strict   # Abort on first error
    """
    from vibey.cli.commands import db_rebuild_cmd

    exit_code = db_rebuild_cmd(force=force, strict=strict, verbose=verbose)
    sys.exit(exit_code)


@roadmap_db.command('status')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
@click.pass_context
def db_status(ctx, verbose: bool):
    """Show database status and health.

    Displays:
    - Database existence and location
    - Dirty flag (uncommitted changes)
    - Row counts vs YAML file counts
    - Schema version and integrity
    - Checksum mismatches (if any)

    Examples:
      vibey roadmap db status
      vibey roadmap db status -v  # Detailed view
    """
    from vibey.cli.commands import db_status_cmd

    exit_code = db_status_cmd(verbose=verbose)
    sys.exit(exit_code)


@roadmap_db.command('backup')
@click.option('--output', '-o', type=click.Path(), help='Custom backup path')
@click.pass_context
def db_backup(ctx, output: Optional[str]):
    """Create a backup of the database.

    Creates a timestamped copy of .vibey/roadmap.db for safekeeping.

    Examples:
      vibey roadmap db backup
      vibey roadmap db backup -o ./my-backup.db
    """
    from vibey.cli.commands import db_backup_cmd

    exit_code = db_backup_cmd(output_path=output)
    sys.exit(exit_code)


@roadmap_db.command('cleanup-legacy')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.option('--delete', is_flag=True, help='Delete legacy files (moves to backup first)')
@click.option('--backup-dir', type=click.Path(), help='Custom backup directory')
@click.pass_context
def db_cleanup_legacy(ctx, dry_run: bool, delete: bool, backup_dir: Optional[str]):
    """Find and handle legacy v2 format YAML files.

    Scans for YAML files using the old v2 format (with parent_ref, created_at, etc.)
    and reports or removes them.

    Examples:
      vibey roadmap db cleanup-legacy              # List legacy files
      vibey roadmap db cleanup-legacy --dry-run    # Show what would be deleted
      vibey roadmap db cleanup-legacy --delete     # Move to backup and remove
    """
    from vibey.cli.commands import db_cleanup_legacy_cmd

    exit_code = db_cleanup_legacy_cmd(dry_run=dry_run, delete=delete, backup_dir=backup_dir)
    sys.exit(exit_code)


@roadmap_db.command('dump')
@click.option('--force', '-f', is_flag=True, help='Overwrite YAML even if modified externally')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@click.pass_context
def db_dump(ctx, force: bool, verbose: bool):
    """Dump database state to YAML files.

    Exports the current database state to hierarchical YAML files
    for version control. This is the reverse of 'db rebuild'.

    Safety checks:
    - Detects if YAML files were modified externally since last load
    - Use --force to overwrite external changes

    After dump:
    - YAML files updated with database state
    - Database marked as clean (is_dirty = 0)
    - Checksums stored for change detection

    Examples:
      vibey roadmap db dump
      vibey roadmap db dump --force  # Overwrite external changes
      vibey roadmap db dump -v       # Verbose output
    """
    from vibey.cli.commands import db_dump_cmd

    exit_code = db_dump_cmd(force=force, verbose=verbose)
    sys.exit(exit_code)


# ============================================================================
# Database Query Commands (vibey roadmap db query)
# ============================================================================

@roadmap_db.group('query')
@click.pass_context
def db_query(ctx):
    """Query the database for roadmap insights.

    These commands leverage SQLite's power to provide
    fast queries that would be expensive with YAML parsing.
    """
    pass


@db_query.command('blocked')
@click.option('--track', '-t', help='Filter by track ID')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed blocker info')
@click.pass_context
def query_blocked(ctx, track: Optional[str], verbose: bool):
    """List all blocked tasks with blocker information.

    Shows tasks that are blocked by dependencies and what they're waiting for.

    Examples:
      vibey roadmap db query blocked
      vibey roadmap db query blocked -t sqlite-backend
      vibey roadmap db query blocked -v
    """
    from vibey.cli.commands import db_query_blocked_cmd

    exit_code = db_query_blocked_cmd(track_filter=track, verbose=verbose)
    sys.exit(exit_code)


@db_query.command('progress')
@click.option('--by', type=click.Choice(['track', 'sprint', 'status']), default='track',
              help='Group progress by')
@click.pass_context
def query_progress(ctx, by: str):
    """Show progress summary grouped by track, sprint, or status.

    Examples:
      vibey roadmap db query progress
      vibey roadmap db query progress --by sprint
      vibey roadmap db query progress --by status
    """
    from vibey.cli.commands import db_query_progress_cmd

    exit_code = db_query_progress_cmd(group_by=by)
    sys.exit(exit_code)


@db_query.command('deps')
@click.argument('entity_id')
@click.option('--direction', type=click.Choice(['up', 'down', 'both']), default='both',
              help='Show dependencies (up), dependents (down), or both')
@click.pass_context
def query_deps(ctx, entity_id: str, direction: str):
    """Show dependency chain for a task, sprint, or track.

    Examples:
      vibey roadmap db query deps sqlite-backend-2-task-001
      vibey roadmap db query deps sqlite-backend --direction up
    """
    from vibey.cli.commands import db_query_deps_cmd

    exit_code = db_query_deps_cmd(entity_id=entity_id, direction=direction)
    sys.exit(exit_code)


@db_query.command('stats')
@click.pass_context
def query_stats(ctx):
    """Show overall roadmap statistics.

    Displays completion rates, task counts by status, and other metrics.

    Examples:
      vibey roadmap db query stats
    """
    from vibey.cli.commands import db_query_stats_cmd

    exit_code = db_query_stats_cmd()
    sys.exit(exit_code)


@roadmap_db.command('config')
@click.pass_context
def db_config(ctx):
    """Show current backend configuration.

    Displays the effective backend mode, database path, and validation settings.

    Examples:
      vibey roadmap db config
    """
    from vibey.cli.commands import db_config_cmd

    exit_code = db_config_cmd()
    sys.exit(exit_code)


@roadmap_db.command('validate')
@click.option('--level', type=click.Choice(['schema', 'references', 'computed', 'full']),
              default='full', help='Validation level')
@click.option('--compare', is_flag=True, help='Compare database with YAML files')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@click.pass_context
def db_validate(ctx, level: str, compare: bool, verbose: bool):
    """Validate database integrity and consistency.

    Validation levels:
      schema     - Check tables, indexes, and constraints exist
      references - Check foreign key relationships are valid
      computed   - Verify computed values match (progress, counts)
      full       - Run all validation checks (default)

    The --compare flag adds DB vs YAML comparison to detect drift.

    Examples:
      vibey roadmap db validate
      vibey roadmap db validate --level schema
      vibey roadmap db validate --compare
      vibey roadmap db validate --compare --verbose
    """
    from vibey.cli.commands import db_validate_cmd

    exit_code = db_validate_cmd(level=level, compare=compare, verbose=verbose)
    sys.exit(exit_code)


# ============================================================================
# Bulk Operations Subcommand Group
# ============================================================================

@roadmap.group('bulk')
@click.pass_context
def roadmap_bulk(ctx):
    """
    Bulk operations on roadmap items.

    Commands for performing operations across multiple items at once,
    such as completing all tasks in a sprint.

    Examples:

      vibey roadmap bulk complete-sprint <sprint-id>  # Complete all tasks in sprint
      vibey roadmap bulk complete-sprint <id> --yes   # Skip confirmation
    """
    pass


@roadmap_bulk.command('complete-sprint')
@click.argument('sprint_id')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def bulk_complete_sprint(ctx, sprint_id: str, yes: bool):
    """Mark all tasks in a sprint as completed.

    Completes all non-completed tasks in the specified sprint at once.
    Updates sprint progress and creates activity log entries for each task.

    Examples:
      vibey roadmap bulk complete-sprint 01KC7TNS0SC0FX8TPGN9SG4J1B
      vibey roadmap bulk complete-sprint dogfooding-bugs-10 --yes
    """
    from vibey.cli.commands import bulk_complete_sprint_cmd

    exit_code = bulk_complete_sprint_cmd(sprint_id, skip_confirm=yes)
    sys.exit(exit_code)


@roadmap.command('migrate-format')
@click.option('--dry-run', is_flag=True, help='Show what would change without modifying files')
@click.option('--backup/--no-backup', default=True, help='Create .v1.bak backup files (default: yes)')
@click.option('--path', '-p', type=click.Path(exists=True), help='Path to roadmap directory')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompt')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed progress')
@click.pass_context
def migrate_format(ctx, dry_run: bool, backup: bool, path: Optional[str], force: bool, verbose: bool):
    """Migrate YAML files from v1 format to v2 format.

    V1 format uses legacy field names (created, assigned_agent, title).
    V2 format uses unified ticket architecture (created_at, assigned_agents, name).

    This command:
    - Scans all YAML files in the roadmap directory
    - Detects which files are v1 format
    - Transforms v1 fields to v2 format
    - Creates backups before modification (unless --no-backup)
    - Validates migrated files

    Examples:

      # Preview changes
      vibey roadmap migrate-format --dry-run

      # Migrate with backups (interactive)
      vibey roadmap migrate-format

      # Force migrate without confirmation
      vibey roadmap migrate-format --force

      # Verbose output
      vibey roadmap migrate-format --verbose --dry-run
    """
    from vibey.cli.commands import migrate_format_cmd

    exit_code = migrate_format_cmd(
        dry_run=dry_run,
        backup=backup,
        path=path,
        force=force,
        verbose=verbose,
    )
    sys.exit(exit_code)


@roadmap.command('migrate-docs')
@click.option('--dry-run', is_flag=True, help='Show what would be created without making changes')
@click.option('--path', '-p', type=click.Path(exists=True), help='Path to roadmap directory')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed progress')
@click.pass_context
def migrate_docs(ctx, dry_run: bool, path: Optional[str], verbose: bool):
    """Migrate documentation fields from YAML to markdown files.

    This command migrates documentation-like fields from YAML to markdown:

    \b
    - version_strategy → VERSIONING_POLICY.md (roadmap directory)
    - version_history → CHANGELOG.md (repository root)
    - metadata.notes → NOTES.md (per-entity directories)

    Benefits of markdown:
    - Rich formatting (headings, tables, code blocks)
    - Git-diffable content
    - Searchable with grep/ripgrep
    - Human readable without tooling

    Examples:

      # Preview changes
      vibey roadmap migrate-docs --dry-run

      # Run migration
      vibey roadmap migrate-docs

      # Verbose output
      vibey roadmap migrate-docs --verbose
    """
    from vibey.cli.commands import migrate_docs_cmd

    exit_code = migrate_docs_cmd(
        dry_run=dry_run,
        path=path,
        verbose=verbose,
    )
    sys.exit(exit_code)


# ============================================================================
# Artifact Command Group (Sprint 5 - Task 005)
# ============================================================================

@cli.group()
@click.pass_context
def artifact(ctx):
    """
    Manage artifacts - first-class file-based entities.

    Artifacts are registered files that can be tracked, linked to tickets,
    and monitored for staleness. Use these commands to manage the artifact
    registry.

    Examples:

      vibey artifact list              # List all artifacts
      vibey artifact show <id>         # Show artifact details
      vibey artifact adopt <path>      # Register a file as artifact
      vibey artifact orphans           # Show unreferenced artifacts
      vibey artifact stale             # Show stale documentation
      vibey artifact impact <files>    # Show affected tickets
    """
    ctx.ensure_object(dict)


@artifact.command('list')
@click.option('--type', '-t', 'artifact_type', help='Filter by artifact type (code, documentation, test, etc.)')
@click.option('--format', '-f', 'output_format', type=click.Choice(['table', 'json', 'simple']),
              default='table', help='Output format')
@click.pass_context
def artifact_list(ctx, artifact_type: Optional[str], output_format: str):
    """List all registered artifacts."""
    from vibey.operations.roadmap.artifacts import list_artifacts
    from vibey.roadmap.models.ticket import ArtifactType
    from vibey.cli.roadmap_lib.filesystem import find_roadmap_root
    import json

    root_dir = find_roadmap_root()
    if not root_dir:
        console.print("[red]Error:[/red] No roadmap found. Run 'vibey roadmap init' first.")
        sys.exit(1)

    artifacts = list_artifacts(root_dir)

    # Filter by type if specified
    if artifact_type:
        try:
            filter_type = ArtifactType(artifact_type)
            artifacts = [a for a in artifacts if a.artifact_type == filter_type]
        except ValueError:
            console.print(f"[red]Error:[/red] Unknown artifact type: {artifact_type}")
            console.print(f"Valid types: {', '.join(t.value for t in ArtifactType)}")
            sys.exit(1)

    if output_format == 'json':
        data = [{'id': a.id, 'name': a.name, 'type': a.artifact_type.value, 'paths': a.paths} for a in artifacts]
        console.print(json.dumps(data, indent=2))
    elif output_format == 'simple':
        for a in artifacts:
            console.print(f"{a.id}\t{a.artifact_type.value}\t{a.name}")
    else:
        # Table format
        if not artifacts:
            console.print("[dim]No artifacts registered[/dim]")
        else:
            from rich.table import Table
            table = Table(title="Artifacts")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Type", style="yellow")
            table.add_column("Paths")
            table.add_column("Refs", justify="right")

            for a in artifacts:
                table.add_row(
                    a.id[:12] + "...",
                    a.name,
                    a.artifact_type.value,
                    ", ".join(a.paths[:2]) + ("..." if len(a.paths) > 2 else ""),
                    str(len(a.referenced_by))
                )
            console.print(table)


@artifact.command('show')
@click.argument('artifact_id')
@click.pass_context
def artifact_show(ctx, artifact_id: str):
    """Show details of a specific artifact."""
    from vibey.operations.roadmap.artifacts import show_artifact
    from vibey.cli.roadmap_lib.filesystem import find_roadmap_root

    root_dir = find_roadmap_root()
    if not root_dir:
        console.print("[red]Error:[/red] No roadmap found.")
        sys.exit(1)

    artifact = show_artifact(artifact_id, root_dir)
    if not artifact:
        console.print(f"[red]Error:[/red] Artifact not found: {artifact_id}")
        sys.exit(1)

    from rich.panel import Panel
    from rich.text import Text

    # Build details
    details = Text()
    details.append(f"ID: ", style="bold")
    details.append(f"{artifact.id}\n")
    details.append(f"Name: ", style="bold")
    details.append(f"{artifact.name}\n")
    details.append(f"Type: ", style="bold")
    details.append(f"{artifact.artifact_type.value}\n")
    if artifact.artifact_subtype:
        details.append(f"Subtype: ", style="bold")
        details.append(f"{artifact.artifact_subtype}\n")
    details.append(f"\nPaths:\n", style="bold")
    for path in artifact.paths:
        details.append(f"  - {path}\n")
    details.append(f"\nProvenance: ", style="bold")
    details.append(f"{artifact.provenance.provenance_type.value}\n")
    if artifact.referenced_by:
        details.append(f"\nReferenced by:\n", style="bold")
        for ref in sorted(artifact.referenced_by):
            details.append(f"  - {ref}\n")
    else:
        details.append(f"\n[dim]Not referenced by any ticket[/dim]\n")
    if artifact.content_hash:
        details.append(f"\nHash: ", style="bold")
        details.append(f"{artifact.content_hash[:16]}...\n", style="dim")

    console.print(Panel(details, title=f"Artifact: {artifact.name}", border_style="blue"))


@artifact.command('adopt')
@click.argument('file_path')
@click.option('--type', '-t', 'artifact_type', required=True,
              type=click.Choice(['code', 'documentation', 'test', 'context', 'agent', 'workflow', 'template', 'config', 'data', 'media']),
              help='Artifact type classification')
@click.option('--name', '-n', help='Optional name (defaults to filename)')
@click.option('--subtype', '-s', help='Optional subtype for more specific classification')
@click.pass_context
def artifact_adopt(ctx, file_path: str, artifact_type: str, name: Optional[str], subtype: Optional[str]):
    """Register an existing file as an artifact."""
    from vibey.operations.roadmap.artifacts import adopt_artifact
    from vibey.roadmap.models.ticket import ArtifactType
    from vibey.cli.roadmap_lib.filesystem import find_roadmap_root

    root_dir = find_roadmap_root()
    if not root_dir:
        console.print("[red]Error:[/red] No roadmap found.")
        sys.exit(1)

    try:
        a_type = ArtifactType(artifact_type)
        artifact = adopt_artifact(file_path, a_type, root_dir, name=name, artifact_subtype=subtype)
        console.print(f"[green]✓[/green] Artifact registered: {artifact.id}")
        console.print(f"  Name: {artifact.name}")
        console.print(f"  Type: {artifact.artifact_type.value}")
        console.print(f"  Path: {', '.join(artifact.paths)}")
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@artifact.command('orphans')
@click.option('--format', '-f', 'output_format', type=click.Choice(['table', 'simple']),
              default='table', help='Output format')
@click.pass_context
def artifact_orphans(ctx, output_format: str):
    """Show artifacts not referenced by any ticket."""
    from vibey.operations.roadmap.artifacts import orphan_artifacts
    from vibey.cli.roadmap_lib.filesystem import find_roadmap_root

    root_dir = find_roadmap_root()
    if not root_dir:
        console.print("[red]Error:[/red] No roadmap found.")
        sys.exit(1)

    orphans = orphan_artifacts(root_dir)

    if not orphans:
        console.print("[green]✓[/green] No orphan artifacts found")
        return

    if output_format == 'simple':
        for a in orphans:
            console.print(f"{a.id}\t{a.artifact_type.value}\t{a.name}")
    else:
        from rich.table import Table
        table = Table(title="Orphan Artifacts (not referenced by any ticket)")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Paths")

        for a in orphans:
            table.add_row(
                a.id[:12] + "...",
                a.name,
                a.artifact_type.value,
                ", ".join(a.paths[:2])
            )
        console.print(table)
        console.print(f"\n[dim]Found {len(orphans)} orphan artifact(s)[/dim]")


@artifact.command('stale')
@click.option('--format', '-f', 'output_format', type=click.Choice(['table', 'simple']),
              default='table', help='Output format')
@click.pass_context
def artifact_stale(ctx, output_format: str):
    """Show stale documentation artifacts."""
    from vibey.operations.roadmap.artifacts import stale_artifacts
    from vibey.cli.roadmap_lib.filesystem import find_roadmap_root

    root_dir = find_roadmap_root()
    if not root_dir:
        console.print("[red]Error:[/red] No roadmap found.")
        sys.exit(1)

    stale = stale_artifacts(root_dir)

    if not stale:
        console.print("[green]✓[/green] No stale documentation artifacts")
        return

    if output_format == 'simple':
        for a in stale:
            console.print(f"{a.id}\t{a.name}")
    else:
        from rich.table import Table
        table = Table(title="Stale Documentation Artifacts")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Paths")
        table.add_column("Status", style="yellow")

        for a in stale:
            table.add_row(
                a.id[:12] + "...",
                a.name,
                ", ".join(a.paths[:2]),
                "Content changed" if a.content_hash else "Unknown"
            )
        console.print(table)
        console.print(f"\n[yellow]⚠[/yellow] {len(stale)} artifact(s) need refresh")


@artifact.command('impact')
@click.argument('files', nargs=-1)
@click.option('--format', '-f', 'output_format', type=click.Choice(['table', 'json', 'simple']),
              default='table', help='Output format')
@click.pass_context
def artifact_impact(ctx, files, output_format: str):
    """Show tickets affected by changes to given files."""
    from vibey.operations.roadmap.artifacts import impact_analysis
    from vibey.cli.roadmap_lib.filesystem import find_roadmap_root
    import json

    root_dir = find_roadmap_root()
    if not root_dir:
        console.print("[red]Error:[/red] No roadmap found.")
        sys.exit(1)

    if not files:
        console.print("[yellow]Warning:[/yellow] No files specified")
        return

    result = impact_analysis(list(files), root_dir)

    if output_format == 'json':
        console.print(json.dumps(result, indent=2))
    elif output_format == 'simple':
        for file_path, tickets in result.items():
            if tickets:
                console.print(f"{file_path}: {', '.join(tickets)}")
    else:
        from rich.table import Table
        table = Table(title="Impact Analysis")
        table.add_column("File", style="cyan")
        table.add_column("Affected Tickets", style="yellow")

        for file_path, tickets in result.items():
            table.add_row(
                file_path,
                ", ".join(tickets) if tickets else "[dim]none[/dim]"
            )
        console.print(table)


@artifact.command('refresh')
@click.pass_context
def artifact_refresh(ctx):
    """Refresh content hashes for all artifacts."""
    from vibey.operations.roadmap.artifacts import refresh_artifact_hashes
    from vibey.cli.roadmap_lib.filesystem import find_roadmap_root

    root_dir = find_roadmap_root()
    if not root_dir:
        console.print("[red]Error:[/red] No roadmap found.")
        sys.exit(1)

    count = refresh_artifact_hashes(root_dir)
    if count > 0:
        console.print(f"[green]✓[/green] Refreshed {count} artifact hash(es)")
    else:
        console.print("[dim]All hashes up to date[/dim]")


@artifact.command('delete')
@click.argument('artifact_id')
@click.option('--force', '-f', is_flag=True, help='Delete without confirmation')
@click.pass_context
def artifact_delete(ctx, artifact_id: str, force: bool):
    """Delete an artifact from the registry (does not delete files)."""
    from vibey.operations.roadmap.artifacts import delete_artifact, show_artifact
    from vibey.cli.roadmap_lib.filesystem import find_roadmap_root

    root_dir = find_roadmap_root()
    if not root_dir:
        console.print("[red]Error:[/red] No roadmap found.")
        sys.exit(1)

    # Show artifact details
    artifact = show_artifact(artifact_id, root_dir)
    if not artifact:
        console.print(f"[red]Error:[/red] Artifact not found: {artifact_id}")
        sys.exit(1)

    if not force:
        console.print(f"About to delete artifact: [cyan]{artifact.name}[/cyan]")
        console.print(f"  Type: {artifact.artifact_type.value}")
        console.print(f"  Paths: {', '.join(artifact.paths)}")
        if artifact.referenced_by:
            console.print(f"  [yellow]Warning:[/yellow] Referenced by {len(artifact.referenced_by)} ticket(s)")
        if not click.confirm("Proceed?"):
            console.print("[dim]Cancelled[/dim]")
            return

    if delete_artifact(artifact_id, root_dir):
        console.print(f"[green]✓[/green] Artifact deleted: {artifact_id}")
    else:
        console.print(f"[red]Error:[/red] Failed to delete artifact")
        sys.exit(1)


@artifact.command('link')
@click.argument('artifact_id')
@click.option('--task', '-t', 'task_id', required=True, help='Task ID to link artifact to')
@click.pass_context
def artifact_link(ctx, artifact_id: str, task_id: str):
    """Link an artifact to a task.

    Associates the artifact with the specified task, enabling
    tracking of which artifacts are relevant to each task.

    Examples:
      vibey artifact link 01KC2D0JK9JKQXGQW6 --task 01KC2D0JK7READW9KAK1
      vibey artifact link artifact-id -t task-id
    """
    from vibey.operations.roadmap.artifacts import link_artifact_to_ticket, show_artifact
    from vibey.cli.roadmap_lib.filesystem import find_roadmap_root

    root_dir = find_roadmap_root()
    if not root_dir:
        console.print("[red]Error:[/red] No roadmap found.")
        sys.exit(1)

    # Verify artifact exists
    artifact = show_artifact(artifact_id, root_dir)
    if not artifact:
        console.print(f"[red]Error:[/red] Artifact not found: {artifact_id}")
        sys.exit(1)

    if link_artifact_to_ticket(artifact_id, task_id, root_dir):
        console.print(f"[green]✓[/green] Linked artifact [cyan]{artifact.name}[/cyan] to task [cyan]{task_id}[/cyan]")
    else:
        console.print(f"[red]Error:[/red] Failed to link artifact")
        sys.exit(1)


@artifact.command('unlink')
@click.argument('artifact_id')
@click.option('--task', '-t', 'task_id', required=True, help='Task ID to unlink artifact from')
@click.pass_context
def artifact_unlink(ctx, artifact_id: str, task_id: str):
    """Unlink an artifact from a task.

    Removes the association between the artifact and the specified task.

    Examples:
      vibey artifact unlink 01KC2D0JK9JKQXGQW6 --task 01KC2D0JK7READW9KAK1
      vibey artifact unlink artifact-id -t task-id
    """
    from vibey.operations.roadmap.artifacts import unlink_artifact_from_ticket, show_artifact
    from vibey.cli.roadmap_lib.filesystem import find_roadmap_root

    root_dir = find_roadmap_root()
    if not root_dir:
        console.print("[red]Error:[/red] No roadmap found.")
        sys.exit(1)

    # Verify artifact exists
    artifact = show_artifact(artifact_id, root_dir)
    if not artifact:
        console.print(f"[red]Error:[/red] Artifact not found: {artifact_id}")
        sys.exit(1)

    if unlink_artifact_from_ticket(artifact_id, task_id, root_dir):
        console.print(f"[green]✓[/green] Unlinked artifact [cyan]{artifact.name}[/cyan] from task [cyan]{task_id}[/cyan]")
    else:
        console.print(f"[red]Error:[/red] Artifact not linked to task or not found")
        sys.exit(1)


@artifact.command('for-task')
@click.argument('task_id')
@click.option('--format', '-f', 'output_format', type=click.Choice(['table', 'json', 'simple']),
              default='table', help='Output format')
@click.pass_context
def artifact_for_task(ctx, task_id: str, output_format: str):
    """List artifacts linked to a specific task.

    Shows all artifacts that have been associated with the given task ID.

    Examples:
      vibey artifact for-task 01KC2D0JK7READW9KAK1
      vibey artifact for-task task-id --format json
    """
    from vibey.operations.roadmap.artifacts import artifacts_for_ticket
    from vibey.cli.roadmap_lib.filesystem import find_roadmap_root
    import json

    root_dir = find_roadmap_root()
    if not root_dir:
        console.print("[red]Error:[/red] No roadmap found.")
        sys.exit(1)

    artifacts = artifacts_for_ticket(task_id, root_dir)

    if output_format == 'json':
        data = [{'id': a.id, 'name': a.name, 'type': a.artifact_type.value, 'paths': a.paths} for a in artifacts]
        console.print(json.dumps(data, indent=2))
    elif output_format == 'simple':
        for a in artifacts:
            console.print(f"{a.id}\t{a.artifact_type.value}\t{a.name}")
    else:
        # Table format
        if not artifacts:
            console.print(f"[dim]No artifacts linked to task {task_id}[/dim]")
        else:
            from rich.table import Table
            table = Table(title=f"Artifacts for Task {task_id}")
            table.add_column("ID", style="dim")
            table.add_column("Name", style="cyan")
            table.add_column("Type")
            table.add_column("Paths")

            for a in artifacts:
                table.add_row(
                    a.id[:12] + "...",
                    a.name,
                    a.artifact_type.value,
                    ", ".join(a.paths[:2]) + ("..." if len(a.paths) > 2 else "")
                )
            console.print(table)


# ============================================================================
# Artifact History Command (Context System V2)
# ============================================================================

@artifact.command('history')
@click.argument('artifact_path')
@click.option('--format', '-f', 'output_format', type=click.Choice(['table', 'json']),
              default='table', help='Output format')
@click.pass_context
def artifact_history(ctx, artifact_path: str, output_format: str):
    """Show all commits that changed an artifact.

    Uses CommitArtifactChange records from the Context System V2 to show
    the complete commit history for a file.

    Examples:
      vibey artifact history vibey/cli/main.py
      vibey artifact history src/models.py --format json
    """
    from vibey.cli.commands.relationship import artifact_history_cmd

    exit_code = artifact_history_cmd(artifact_path, output_format)
    sys.exit(exit_code)


# ============================================================================
# Task Relationship Commands (Context System V2)
# ============================================================================

@roadmap.group('task')
@click.pass_context
def roadmap_task(ctx):
    """
    Manage task relationships with artifacts and commits.

    Commands for linking tasks to artifacts and commits, viewing
    relationships, and managing the triangle model.

    The Triangle Model links:
    - Tickets (tasks) <-> Artifacts (files)
    - Tickets (tasks) <-> Commits (git)
    - Commits <-> Artifacts

    Examples:

      vibey roadmap task add-artifact <task-id> <path>  # Associate artifact
      vibey roadmap task artifacts <task-id>            # List artifacts
      vibey roadmap task commits <task-id>              # List commits
      vibey roadmap task link-commit <task-id> <sha>    # Link commit
    """
    pass


@roadmap_task.command('add-artifact')
@click.argument('task_id')
@click.argument('artifact_path')
@click.option('--no-create', is_flag=True, help='Do not create artifact if missing')
@click.pass_context
def task_add_artifact(ctx, task_id: str, artifact_path: str, no_create: bool):
    """Associate an artifact with a task.

    Creates a TicketArtifactAssociation with source=manual.
    If the artifact doesn't exist in the registry, it will be created
    unless --no-create is specified.

    Examples:
      vibey roadmap task add-artifact 01KC2D0JK7READW9KAK1HBX4B8 vibey/cli/main.py
      vibey roadmap task add-artifact task-id src/models.py --no-create
    """
    from vibey.cli.commands.relationship import task_add_artifact_cmd

    exit_code = task_add_artifact_cmd(task_id, artifact_path, create_if_missing=not no_create)
    sys.exit(exit_code)


@roadmap_task.command('artifacts')
@click.argument('task_id')
@click.option('--format', '-f', 'output_format', type=click.Choice(['table', 'json']),
              default='table', help='Output format')
@click.pass_context
def task_artifacts(ctx, task_id: str, output_format: str):
    """List all artifacts associated with a task.

    Shows artifact details, association source, and when the
    association was created.

    Examples:
      vibey roadmap task artifacts 01KC2D0JK7READW9KAK1HBX4B8
      vibey roadmap task artifacts task-id --format json
    """
    from vibey.cli.commands.relationship import task_artifacts_cmd

    exit_code = task_artifacts_cmd(task_id, output_format)
    sys.exit(exit_code)


@roadmap_task.command('commits')
@click.argument('task_id')
@click.option('--format', '-f', 'output_format', type=click.Choice(['table', 'json']),
              default='table', help='Output format')
@click.pass_context
def task_commits(ctx, task_id: str, output_format: str):
    """List all commits linked to a task.

    Shows reference type (task_reference or completion_claim),
    confidence score, link source, and commit details.

    Examples:
      vibey roadmap task commits 01KC2D0JK7READW9KAK1HBX4B8
      vibey roadmap task commits task-id --format json
    """
    from vibey.cli.commands.relationship import task_commits_cmd

    exit_code = task_commits_cmd(task_id, output_format)
    sys.exit(exit_code)


@roadmap_task.command('link-commit')
@click.argument('task_id')
@click.argument('commit_sha')
@click.option('--type', '-t', 'reference_type',
              type=click.Choice(['task_reference', 'completion_claim']),
              default='task_reference', help='Type of reference')
@click.pass_context
def task_link_commit(ctx, task_id: str, commit_sha: str, reference_type: str):
    """Manually link a commit to a task.

    Creates a TicketCommitLink with source=manual and confidence=1.0.

    Reference types:
      task_reference   - Commit is related work on the task
      completion_claim - Commit claims to complete the task

    Examples:
      vibey roadmap task link-commit 01KC2D0JK7READW9KAK1HBX4B8 abc123
      vibey roadmap task link-commit task-id def456 --type completion_claim
    """
    from vibey.cli.commands.relationship import task_link_commit_cmd

    exit_code = task_link_commit_cmd(task_id, commit_sha, reference_type)
    sys.exit(exit_code)


# ============================================================================
# Validate Triangle Command (Context System V2)
# ============================================================================

@roadmap.command('validate-triangle')
@click.option('--task-id', '-t', help='Validate specific task (default: all tasks)')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed validation output')
@click.pass_context
def validate_triangle(ctx, task_id: Optional[str], verbose: bool):
    """Validate consistency across all three relationship edges.

    The Triangle Model connects:
    - Tickets <-> Artifacts (TicketArtifactAssociation)
    - Tickets <-> Commits (TicketCommitLink)
    - Commits <-> Artifacts (CommitArtifactChange)

    This command checks for:
    - Orphaned associations (artifacts associated but never touched by commits)
    - Undocumented changes (artifacts changed but not associated)
    - Empty commits (commits with no artifact changes recorded)

    Examples:
      vibey roadmap validate-triangle                    # Validate all tasks
      vibey roadmap validate-triangle -t 01KC2D0JK7READW9 # Validate one task
      vibey roadmap validate-triangle --verbose           # Detailed output
    """
    from vibey.cli.commands.relationship import validate_triangle_cmd

    exit_code = validate_triangle_cmd(task_id, verbose)
    sys.exit(exit_code)


# ============================================================================
# Auth Commands (vibey auth)
# ============================================================================

@cli.group('auth')
@click.pass_context
def auth(ctx):
    """
    Manage authentication keys for roadmap signing.

    Set up Ed25519 keypairs for signing activity log entries,
    register authorized signers for your project, and manage
    signing identity.

    Get started:
      vibey auth setup           # Generate your keypair
      vibey auth init-project    # Initialize signing for project
      vibey auth add-signer      # Add team members

    Examples:
      vibey auth setup --email alice@example.com --name "Alice Smith"
      vibey auth list            # List authorized signers
      vibey auth export          # Share your public key
    """
    pass


@auth.command('setup')
@click.option('--email', prompt='Your email address', help='Email for identity')
@click.option('--name', prompt='Your name', help='Full name for identity')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing keys')
@click.pass_context
def auth_setup(ctx, email: str, name: str, force: bool):
    """Generate Ed25519 keypair for signing roadmap changes.

    Creates a keypair in ~/.vibey/ for signing activity log entries.
    Your private key never leaves your machine.

    Examples:
      vibey auth setup
      vibey auth setup --email alice@example.com --name "Alice Smith"
      vibey auth setup --force  # Regenerate keys
    """
    try:
        from vibey.operations.auth import KeyManager, setup_user_keys
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\nInstall required dependency:")
        console.print("  pip install cryptography")
        sys.exit(1)

    manager = KeyManager()

    # Check for existing keys
    if manager.has_keypair() and not force:
        console.print("[yellow]Warning:[/yellow] Keypair already exists at ~/.vibey/")
        console.print("Use --force to regenerate (this will overwrite existing keys)")
        sys.exit(1)

    console.print("\n[bold]Generating Ed25519 keypair...[/bold]\n")

    try:
        public_key_str, private_path, public_path = setup_user_keys(email, name)
    except Exception as e:
        console.print(f"[red]Error generating keys:[/red] {e}")
        sys.exit(1)

    console.print(f"[green]✓[/green] Private key saved to: [cyan]{private_path}[/cyan] (mode 0600)")
    console.print(f"[green]✓[/green] Public key saved to: [cyan]{public_path}[/cyan]")
    console.print(f"[green]✓[/green] Identity saved: [cyan]{name} <{email}>[/cyan]")
    console.print()
    console.print("[bold]Your public key (share this for authorization):[/bold]")
    console.print(f"[dim]{public_key_str}[/dim]")
    console.print()
    console.print("Next steps:")
    console.print("  1. Run [cyan]vibey auth init-project[/cyan] to enable signing for this project")
    console.print("  2. Or share your public key with a project owner to be authorized")


@auth.command('export')
@click.pass_context
def auth_export(ctx):
    """Export your public key for sharing with project owners.

    Displays your public key in a format that can be shared
    with project owners for authorization.

    Example:
      vibey auth export | pbcopy  # Copy to clipboard on macOS
    """
    try:
        from vibey.operations.auth import KeyManager
    except ImportError:
        console.print("[red]Error:[/red] Cryptography library not installed")
        sys.exit(1)

    manager = KeyManager()

    if not manager.has_keypair():
        console.print("[red]Error:[/red] No keypair found")
        console.print("Run [cyan]vibey auth setup[/cyan] to generate keys")
        sys.exit(1)

    public_key_str = manager.get_public_key_string()
    if not public_key_str:
        console.print("[red]Error:[/red] Could not load public key")
        sys.exit(1)

    identity = manager.load_identity()
    console.print(f"Public key for [cyan]{identity.email if identity else 'unknown'}[/cyan]:")
    console.print()
    console.print(public_key_str)
    console.print()
    console.print("Share this key with a project owner to be authorized.")


@auth.command('status')
@click.pass_context
def auth_status(ctx):
    """Show current authentication status.

    Displays whether you have keys configured and whether
    signing is enabled for the current project.
    """
    try:
        from vibey.operations.auth import KeyManager, list_authorized_signers
    except ImportError:
        console.print("[red]Error:[/red] Cryptography library not installed")
        sys.exit(1)

    manager = KeyManager()

    console.print("[bold]Authentication Status[/bold]\n")

    # User keys
    if manager.has_keypair():
        identity = manager.load_identity()
        console.print(f"[green]✓[/green] Keypair: configured")
        if identity:
            console.print(f"  Identity: {identity.name} <{identity.email}>")
    else:
        console.print("[yellow]○[/yellow] Keypair: not configured")
        console.print("  Run [cyan]vibey auth setup[/cyan] to generate keys")

    # Project signing
    from pathlib import Path
    signers_dir = Path.cwd() / ".vibey" / "authorized-signers"
    if signers_dir.exists():
        manifest = signers_dir / "manifest.yaml"
        if manifest.exists():
            console.print(f"[green]✓[/green] Project signing: enabled")
            signers = list_authorized_signers()
            active = [s for s in signers if s.active]
            console.print(f"  Authorized signers: {len(active)}")
        else:
            console.print("[yellow]○[/yellow] Project signing: partially configured")
    else:
        console.print("[yellow]○[/yellow] Project signing: not configured")
        console.print("  Run [cyan]vibey auth init-project[/cyan] to enable")


@auth.command('init-project')
@click.option('--force', '-f', is_flag=True, help='Reinitialize even if already configured')
@click.pass_context
def auth_init_project(ctx, force: bool):
    """Initialize signing for this project.

    Sets you up as the first authorized signer (owner).
    Requires running 'vibey auth setup' first.

    Creates:
      .vibey/authorized-signers/manifest.yaml
      .vibey/authorized-signers/{your-email}.pub

    Example:
      vibey auth init-project
    """
    try:
        from vibey.operations.auth import SignerManager
    except ImportError:
        console.print("[red]Error:[/red] Cryptography library not installed")
        sys.exit(1)

    manager = SignerManager()

    if manager.is_initialized() and not force:
        console.print("[yellow]Warning:[/yellow] Project signing already initialized")
        console.print("Use --force to reinitialize")
        sys.exit(1)

    console.print("\n[bold]Initializing project signing...[/bold]\n")

    try:
        owner = manager.initialize_project()
    except RuntimeError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    console.print(f"[green]✓[/green] Created .vibey/authorized-signers/")
    console.print(f"[green]✓[/green] Added [cyan]{owner.identity}[/cyan] as owner")
    console.print()
    console.print("Commit and push to enable signed changes:")
    console.print("  [dim]git add .vibey/authorized-signers/[/dim]")
    console.print("  [dim]git commit -m 'Enable roadmap signing'[/dim]")


@auth.command('add-signer')
@click.argument('email')
@click.argument('name')
@click.argument('public_key')
@click.option('--role', type=click.Choice(['developer', 'admin', 'owner']),
              default='developer', help='Signer role')
@click.pass_context
def auth_add_signer(ctx, email: str, name: str, public_key: str, role: str):
    """Add an authorized signer to this project.

    Registers a team member's public key so their changes
    can be verified.

    Arguments:
      EMAIL       Signer's email address
      NAME        Signer's full name (use quotes)
      PUBLIC_KEY  Public key string (vibey-ed25519 ...)

    Example:
      vibey auth add-signer bob@example.com "Bob Jones" "vibey-ed25519 AAAA..."
    """
    try:
        from vibey.operations.auth import SignerManager
    except ImportError:
        console.print("[red]Error:[/red] Cryptography library not installed")
        sys.exit(1)

    manager = SignerManager()

    console.print(f"\n[bold]Adding authorized signer...[/bold]\n")

    try:
        signer = manager.add_signer(email, name, public_key, role)
    except RuntimeError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    console.print(f"[green]✓[/green] Added signer: [cyan]{signer.name} <{signer.identity}>[/cyan]")
    console.print(f"  Role: {signer.role}")
    console.print()
    console.print("Commit and push to authorize this signer:")
    console.print("  [dim]git add .vibey/authorized-signers/[/dim]")
    console.print("  [dim]git commit -m 'Add authorized signer: {}'[/dim]".format(email))


@auth.command('list')
@click.option('--all', 'show_all', is_flag=True, help='Include inactive signers')
@click.pass_context
def auth_list(ctx, show_all: bool):
    """List authorized signers for this project.

    Shows all team members who can make signed roadmap changes.

    Example:
      vibey auth list
      vibey auth list --all  # Include revoked signers
    """
    try:
        from vibey.operations.auth import list_authorized_signers, is_signing_enabled
    except ImportError:
        console.print("[red]Error:[/red] Cryptography library not installed")
        sys.exit(1)

    if not is_signing_enabled():
        console.print("[yellow]Project signing not configured[/yellow]")
        console.print("Run [cyan]vibey auth init-project[/cyan] to enable")
        return

    signers = list_authorized_signers()

    if not show_all:
        signers = [s for s in signers if s.active]

    if not signers:
        console.print("No authorized signers found")
        return

    console.print("[bold]Authorized Signers[/bold]\n")

    for signer in signers:
        status = "[green]active[/green]" if signer.active else "[red]revoked[/red]"
        role_color = {
            "owner": "yellow",
            "admin": "cyan",
            "developer": "white",
        }.get(signer.role, "white")

        console.print(f"  {signer.identity}")
        console.print(f"    Name: {signer.name}")
        console.print(f"    Role: [{role_color}]{signer.role}[/{role_color}]")
        console.print(f"    Status: {status}")
        console.print(f"    Added: {signer.added[:10]} by {signer.added_by}")
        console.print()


@auth.command('revoke')
@click.argument('email')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def auth_revoke(ctx, email: str, yes: bool):
    """Revoke a signer's authorization.

    Marks a signer as inactive. Their existing signed changes
    remain valid, but new changes won't be accepted.

    Example:
      vibey auth revoke bob@example.com
    """
    try:
        from vibey.operations.auth import SignerManager
    except ImportError:
        console.print("[red]Error:[/red] Cryptography library not installed")
        sys.exit(1)

    manager = SignerManager()

    if not manager.is_initialized():
        console.print("[red]Error:[/red] Project signing not configured")
        sys.exit(1)

    signer = manager.get_signer(email)
    if not signer:
        console.print(f"[red]Error:[/red] Signer not found: {email}")
        sys.exit(1)

    if not signer.active:
        console.print(f"[yellow]Signer already revoked:[/yellow] {email}")
        return

    if not yes:
        console.print(f"About to revoke: [cyan]{signer.name} <{email}>[/cyan]")
        console.print(f"  Role: {signer.role}")
        if not click.confirm("Proceed?"):
            console.print("[dim]Cancelled[/dim]")
            return

    if manager.revoke_signer(email):
        console.print(f"[green]✓[/green] Revoked: {email}")
        console.print()
        console.print("Commit and push to apply revocation:")
        console.print("  [dim]git add .vibey/authorized-signers/manifest.yaml[/dim]")
    else:
        console.print(f"[red]Error:[/red] Failed to revoke signer")


# ============================================================================
# Audit Command Group
# ============================================================================

@cli.group()
@click.pass_context
def audit(ctx):
    """
    Audit and analyze codebase structure, documentation coverage, and file classification.

    The audit system provides tools for:
    - File inventory generation
    - File classification by purpose and type
    - Dependency analysis
    - Documentation coverage analysis
    - Test coverage mapping

    Examples:

      vibey audit inventory             # Generate file inventory
      vibey audit inventory --output FILE  # Save to specific file
    """
    ctx.ensure_object(dict)


@audit.command('inventory')
@click.option('--output', '-o', type=click.Path(), default=None,
              help='Output file path (default: .vibey/roadmap/context/.../FILE_INVENTORY.yaml)')
@click.option('--directories', '-d', multiple=True, default=None,
              help='Directories to scan (can specify multiple)')
@click.option('--format', '-f', 'output_format', type=click.Choice(['yaml', 'json']),
              default='yaml', help='Output format')
@click.pass_context
def audit_inventory(ctx, output: Optional[str], directories: tuple, output_format: str):
    """Generate file inventory for codebase audit.

    Scans specified directories and generates a structured inventory
    of all files with metadata (path, type, size, lines, modified time).

    Examples:
      vibey audit inventory                          # Default directories
      vibey audit inventory -d vibey/ -d docs/       # Custom directories
      vibey audit inventory --output inventory.yaml  # Custom output path
      vibey audit inventory --format json            # JSON output
    """
    from pathlib import Path
    from vibey.operations.audit.file_inventory import (
        generate_file_inventory,
        FileInventoryConfig,
        save_inventory,
    )
    import json as json_mod

    # Set up configuration
    config = FileInventoryConfig()
    if directories:
        config.directories = list(directories)

    # Generate inventory
    console.print(f"[blue]Scanning directories:[/blue] {', '.join(config.directories)}")
    inventory = generate_file_inventory(config)

    summary = inventory["inventory"]["summary"]
    console.print(f"[green]Found {summary['total_files']} files in {summary['total_directories']} directories[/green]")

    # Show extension breakdown
    console.print("\n[bold]Files by extension:[/bold]")
    for ext, count in list(summary['by_extension'].items())[:10]:
        console.print(f"  {ext}: {count}")
    if len(summary['by_extension']) > 10:
        console.print(f"  ... and {len(summary['by_extension']) - 10} more extensions")

    # Determine output path
    if output:
        output_path = Path(output)
    else:
        output_path = Path(".vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/FILE_INVENTORY.yaml")

    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_format == 'json':
        with open(output_path.with_suffix('.json'), 'w') as f:
            json_mod.dump(inventory, f, indent=2)
        console.print(f"\n[green]Inventory saved to:[/green] {output_path.with_suffix('.json')}")
    else:
        save_inventory(inventory, output_path)
        console.print(f"\n[green]Inventory saved to:[/green] {output_path}")


@audit.command('classify')
@click.option('--directory', '-d', type=click.Choice(['vibey', 'docs', 'tests', 'all']),
              default='vibey', help='Directory to classify')
@click.option('--output', '-o', type=click.Path(), default=None,
              help='Output file path')
@click.pass_context
def audit_classify(ctx, directory: str, output: Optional[str]):
    """Classify files according to taxonomy.

    Analyzes files in specified directory and generates a classification
    YAML file with category, purpose, dependencies, and coverage info.

    Examples:
      vibey audit classify                      # Classify vibey/ (default)
      vibey audit classify -d docs              # Classify docs/
      vibey audit classify -d vibey -o out.yaml # Custom output
    """
    from pathlib import Path
    from vibey.operations.audit.file_classifier import (
        classify_vibey_files,
        save_classification,
    )

    root_path = Path.cwd()

    if directory == 'vibey':
        console.print("[blue]Classifying vibey/ package files...[/blue]")
        classification = classify_vibey_files(root_path)

        if output:
            output_path = Path(output)
        else:
            output_path = Path(".vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/VIBEY_FILE_CLASSIFICATION.yaml")

        summary = classification["classification"]["summary"]
        console.print(f"[green]Classified {summary['total_files']} files[/green]")

        console.print("\n[bold]Files by subcategory:[/bold]")
        for subcat, count in summary['by_subcategory'].items():
            console.print(f"  {subcat}: {count}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_classification(classification, output_path)
        console.print(f"\n[green]Classification saved to:[/green] {output_path}")

    elif directory in ('docs', 'tests'):
        console.print(f"[yellow]Classification for {directory}/ not yet implemented[/yellow]")
        console.print("Use vibey audit classify -d vibey for now")

    else:
        console.print("[yellow]Classification for all directories not yet implemented[/yellow]")


# ============================================================================
# Session Command Group
# ============================================================================

@cli.group()
@click.pass_context
def session(ctx):
    """
    Manage AI-assisted coding sessions.

    Track session lifecycle, log events and decisions, associate commits,
    and maintain context for session reconstruction.

    Examples:

      vibey session start                        # Start new session
      vibey session start "Feature work"         # Start with name
      vibey session status                       # Show active session
      vibey session end --summary "Completed X"  # End session
      vibey session list                         # List all sessions
    """
    ctx.ensure_object(dict)


@session.command('start')
@click.argument('name', required=False)
@click.option('--goal', '-g', multiple=True, help='Session goal (can specify multiple)')
@click.option('--track', '-t', help='Associate with track ID')
@click.option('--sprint', '-s', help='Associate with sprint ID')
@click.option('--task', '-T', multiple=True, help='Associate with task ID (can specify multiple)')
@click.pass_context
def session_start(ctx, name: Optional[str], goal: tuple, track: Optional[str],
                  sprint: Optional[str], task: tuple):
    """Start a new coding session.

    Creates a new session to track work, decisions, and commits. Only one
    session can be active at a time.

    Examples:
      vibey session start                              # Auto-generated name
      vibey session start "Implement auth"             # Custom name
      vibey session start -g "Fix login bug" -g "Add tests"  # With goals
      vibey session start --track my-track --sprint sprint-1  # With associations
    """
    from vibey.cli.commands import session_start_cmd

    exit_code = session_start_cmd(
        name=name,
        goals=list(goal) if goal else None,
        track_id=track,
        sprint_id=sprint,
        task_ids=list(task) if task else None,
    )
    sys.exit(exit_code)


@session.command('end')
@click.option('--summary', '-s', help='Session summary')
@click.option('--status', type=click.Choice(['completed', 'abandoned']),
              default='completed', help='End status')
@click.option('--session-id', help='Specific session ID to end (default: active)')
@click.pass_context
def session_end(ctx, summary: Optional[str], status: str, session_id: Optional[str]):
    """End the current or specified session.

    Marks the session as completed or abandoned, captures final git state,
    and calculates session statistics.

    Examples:
      vibey session end                                    # End active session
      vibey session end --summary "Completed feature X"    # With summary
      vibey session end --status abandoned                 # Mark as abandoned
      vibey session end --session-id 01ABC123...          # End specific session
    """
    from vibey.cli.commands import session_end_cmd

    exit_code = session_end_cmd(
        session_id=session_id,
        summary=summary,
        status=status,
    )
    sys.exit(exit_code)


@session.command('pause')
@click.option('--session-id', help='Specific session ID to pause (default: active)')
@click.pass_context
def session_pause(ctx, session_id: Optional[str]):
    """Pause the current or specified session.

    Temporarily stops tracking while preserving state. Use 'resume' to continue.

    Examples:
      vibey session pause                       # Pause active session
      vibey session pause --session-id 01ABC... # Pause specific session
    """
    from vibey.cli.commands import session_pause_cmd

    exit_code = session_pause_cmd(session_id=session_id)
    sys.exit(exit_code)


@session.command('resume')
@click.argument('session_id')
@click.pass_context
def session_resume(ctx, session_id: str):
    """Resume a paused session.

    Continues a previously paused session, restoring it as the active session.

    Examples:
      vibey session resume 01ABC123DEF456GHI789JKL012
    """
    from vibey.cli.commands import session_resume_cmd

    exit_code = session_resume_cmd(session_id=session_id)
    sys.exit(exit_code)


@session.command('status')
@click.pass_context
def session_status(ctx):
    """Show the current active session status.

    Displays information about the currently active session, including
    goals, associations, and event/decision counts.

    Examples:
      vibey session status
    """
    from vibey.cli.commands import session_status_cmd

    exit_code = session_status_cmd()
    sys.exit(exit_code)


@session.command('show')
@click.argument('session_id')
@click.pass_context
def session_show(ctx, session_id: str):
    """Show detailed information about a specific session.

    Displays comprehensive session details including events, decisions,
    commits, and statistics.

    Examples:
      vibey session show 01ABC123DEF456GHI789JKL012
    """
    from vibey.cli.commands import session_show_cmd

    exit_code = session_show_cmd(session_id=session_id)
    sys.exit(exit_code)


@session.command('list')
@click.option('--status', type=click.Choice(['active', 'paused', 'completed', 'abandoned']),
              help='Filter by status')
@click.option('--track', '-t', help='Filter by track ID')
@click.option('--sprint', '-s', help='Filter by sprint ID')
@click.option('--since', help='Filter by date (ISO format or relative: 7d, 2w, 1m)')
@click.option('--limit', '-n', default=20, help='Maximum sessions to show')
@click.pass_context
def session_list(ctx, status: Optional[str], track: Optional[str],
                 sprint: Optional[str], since: Optional[str], limit: int):
    """List sessions with optional filters.

    Shows all sessions matching the specified filters, sorted by creation date.

    Examples:
      vibey session list                      # List all sessions
      vibey session list --status completed   # Only completed sessions
      vibey session list --track my-track     # Filter by track
      vibey session list --since 7d -n 10     # Last 7 days, max 10
    """
    from vibey.cli.commands import session_list_cmd

    exit_code = session_list_cmd(
        status=status,
        track_id=track,
        sprint_id=sprint,
        since=since,
        limit=limit,
    )
    sys.exit(exit_code)


@session.command('report')
@click.argument('session_id')
@click.option('--format', '-f', type=click.Choice(['markdown', 'text']),
              default='markdown', help='Output format')
@click.option('--output', '-o', type=click.Path(), help='Write report to file')
@click.pass_context
def session_report(ctx, session_id: str, format: str, output: Optional[str]):
    """Generate a session report.

    Creates a human-readable report of the session including summary,
    goals, tasks, commits, decisions, and timeline.

    Examples:
      vibey session report 01ABC123...              # Print to console
      vibey session report 01ABC123... -o report.md # Save to file
      vibey session report 01ABC123... -f text      # Plain text format
    """
    from vibey.cli.commands import session_report_cmd

    exit_code = session_report_cmd(
        session_id=session_id,
        format=format,
        output=output,
    )
    sys.exit(exit_code)


@session.command('timeline')
@click.argument('session_id')
@click.pass_context
def session_timeline(ctx, session_id: str):
    """Show session timeline of events.

    Displays a chronological list of all events that occurred during
    the session with timestamps and details.

    Examples:
      vibey session timeline 01ABC123...
    """
    from vibey.cli.commands import session_timeline_cmd

    exit_code = session_timeline_cmd(session_id=session_id)
    sys.exit(exit_code)


@session.command('export')
@click.argument('session_id')
@click.option('--output', '-o', type=click.Path(), help='Write export to file')
@click.pass_context
def session_export(ctx, session_id: str, output: Optional[str]):
    """Export session for continuation.

    Exports session state including incomplete tasks, goals, and decisions
    that need revisiting. Useful for resuming work in a new session.

    Examples:
      vibey session export 01ABC123...               # Print to console
      vibey session export 01ABC123... -o state.json # Save to file
    """
    from vibey.cli.commands import session_export_cmd

    exit_code = session_export_cmd(
        session_id=session_id,
        output=output,
    )
    sys.exit(exit_code)


@session.command('decisions')
@click.argument('session_id')
@click.pass_context
def session_decisions(ctx, session_id: str):
    """Show decisions made during a session.

    Lists all decisions recorded during the session with their rationale,
    alternatives considered, and whether they need revisiting.

    Examples:
      vibey session decisions 01ABC123...
    """
    from vibey.cli.commands import session_decisions_cmd

    exit_code = session_decisions_cmd(session_id=session_id)
    sys.exit(exit_code)


# ============================================================================
# Discover Command Group
# ============================================================================

@cli.group()
@click.pass_context
def discover(ctx):
    """
    Project discovery - analyze structure, dependencies, and patterns.

    The discover command analyzes your project and generates structured
    output about its characteristics. Discovery results are versioned
    and can be used for context management and change tracking.

    Examples:

      vibey discover run              # Run discovery
      vibey discover show             # Show current discovery
      vibey discover status           # Check if discovery is stale
      vibey discover history          # List discovery versions
      vibey discover diff             # Compare versions

    Discovery outputs include:
      - Project type and languages
      - Directory structure and key files
      - Dependencies (runtime and dev)
      - Code patterns and conventions
      - Quality metrics and recommendations
    """
    ctx.ensure_object(dict)


@discover.command('run')
@click.option('--output', '-o', type=click.Choice(['yaml', 'json', 'text']),
              default='yaml', help='Output format')
@click.option('--save/--no-save', default=True,
              help='Save discovery to history')
@click.option('--project', '-p', default='.',
              help='Project root directory')
@click.pass_context
def discover_run(ctx, output: str, save: bool, project: str):
    """Run project discovery and analyze the codebase.

    Analyzes the project structure, dependencies, patterns, and conventions.
    Results are saved to .vibey/discovery/ by default.

    Examples:
      vibey discover run
      vibey discover run --output json
      vibey discover run --no-save
      vibey discover run -p /path/to/project
    """
    from vibey.cli.commands import discover_run_cmd

    exit_code = discover_run_cmd(
        output_format=output,
        save=save,
        project_root=project,
    )
    sys.exit(exit_code)


@discover.command('show')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['yaml', 'json', 'text']),
              default='text', help='Output format')
@click.option('--section', '-s',
              type=click.Choice(['all', 'project', 'structure', 'dependencies',
                                'patterns', 'conventions', 'quality', 'recommendations']),
              default='all', help='Section to display')
@click.pass_context
def discover_show(ctx, output_format: str, section: str):
    """Show current discovery output.

    Displays the most recent discovery analysis. Use --section to
    show only specific parts of the discovery.

    Examples:
      vibey discover show
      vibey discover show --format yaml
      vibey discover show --section dependencies
    """
    from vibey.cli.commands import discover_show_cmd

    exit_code = discover_show_cmd(
        output_format=output_format,
        section=section,
    )
    sys.exit(exit_code)


@discover.command('status')
@click.option('--max-age', '-a', default=24, type=int,
              help='Hours before discovery is considered stale')
@click.pass_context
def discover_status(ctx, max_age: int):
    """Check if current discovery is stale.

    Reports whether the discovery should be refreshed based on:
    - Age of the discovery
    - Git commit changes
    - File system changes

    Examples:
      vibey discover status
      vibey discover status --max-age 48
    """
    from vibey.cli.commands import discover_status_cmd

    exit_code = discover_status_cmd(max_age_hours=max_age)
    sys.exit(exit_code)


@discover.command('history')
@click.option('--limit', '-n', default=10, type=int,
              help='Maximum number of versions to show')
@click.pass_context
def discover_history(ctx, limit: int):
    """List discovery version history.

    Shows previous discovery runs with timestamps and git commits.

    Examples:
      vibey discover history
      vibey discover history --limit 5
    """
    from vibey.cli.commands import discover_history_cmd

    exit_code = discover_history_cmd(limit=limit)
    sys.exit(exit_code)


@discover.command('diff')
@click.argument('from_version', required=False)
@click.argument('to_version', default='current')
@click.pass_context
def discover_diff(ctx, from_version: Optional[str], to_version: str):
    """Compare two discovery versions.

    Shows differences between discovery outputs. By default, compares
    the current discovery with the previous version.

    Examples:
      vibey discover diff
      vibey discover diff 2025-12-13T10-00-00
      vibey discover diff 2025-12-13T10-00-00 2025-12-14T10-00-00
    """
    from vibey.cli.commands import discover_diff_cmd

    exit_code = discover_diff_cmd(
        from_version=from_version,
        to_version=to_version,
    )
    sys.exit(exit_code)


@discover.command('refresh')
@click.option('--force', '-f', is_flag=True,
              help='Force refresh even if not stale')
@click.pass_context
def discover_refresh(ctx, force: bool):
    """Refresh discovery if stale.

    Re-runs discovery only if the current discovery is stale,
    unless --force is specified.

    Examples:
      vibey discover refresh
      vibey discover refresh --force
    """
    from vibey.cli.commands import discover_refresh_cmd

    exit_code = discover_refresh_cmd(force=force)
    sys.exit(exit_code)


# ============================================================================
# Context Commands
# ============================================================================

@cli.group()
@click.pass_context
def context(ctx):
    """Context management - manage session, task, and decision context.

    Context provides structured storage for AI-assisted development work:
    - Sessions: Track work sessions with goals and artifacts
    - Tasks: Capture task execution context with commands and files
    - Decisions: Record architectural decisions (ADRs)
    - Sprints: Store sprint planning documents and artifacts
    """
    ctx.ensure_object(dict)


@context.command('list')
@click.option('--type', '-t', 'context_type',
              type=click.Choice(['session', 'task', 'decision', 'sprint', 'all']),
              default='all', help='Context type to list')
@click.option('--status', '-s', type=str, help='Filter by status')
@click.option('--limit', '-n', type=int, default=20, help='Maximum items to show')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['table', 'yaml', 'json']),
              default='table', help='Output format')
@click.pass_context
def context_list(ctx, context_type: str, status: str, limit: int, output_format: str):
    """List context items.

    Examples:
      vibey context list
      vibey context list --type session --status active
      vibey context list --type decision --limit 10
      vibey context list --format json
    """
    from vibey.cli.commands import context_list_cmd

    exit_code = context_list_cmd(
        context_type=context_type,
        status=status,
        limit=limit,
        output_format=output_format,
    )
    sys.exit(exit_code)


@context.command('show')
@click.argument('context_id')
@click.option('--type', '-t', 'context_type',
              type=click.Choice(['session', 'task', 'decision', 'sprint']),
              help='Context type (auto-detected if not specified)')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['yaml', 'json', 'text']),
              default='yaml', help='Output format')
@click.pass_context
def context_show(ctx, context_id: str, context_type: str, output_format: str):
    """Show context details.

    Examples:
      vibey context show 01KC7MN54VXRB3APC5FV5XBDXX
      vibey context show 0001-adopt-ulid-naming --type decision
      vibey context show user-journey-phase-4-4 --type sprint
    """
    from vibey.cli.commands import context_show_cmd

    exit_code = context_show_cmd(
        context_id=context_id,
        context_type=context_type,
        output_format=output_format,
    )
    sys.exit(exit_code)


@context.command('archive')
@click.argument('context_id')
@click.option('--type', '-t', 'context_type',
              type=click.Choice(['session', 'task']),
              help='Context type (required)')
@click.pass_context
def context_archive(ctx, context_id: str, context_type: str):
    """Archive context to history.

    Moves context from current/active to history directory.

    Examples:
      vibey context archive 01KC7MN54VXRB3APC5FV5XBDXX --type session
      vibey context archive 01KC81GRE7HFXA9J6FYFM7H3BR --type task
    """
    from vibey.cli.commands import context_archive_cmd

    exit_code = context_archive_cmd(
        context_id=context_id,
        context_type=context_type,
    )
    sys.exit(exit_code)


@context.command('clean')
@click.option('--type', '-t', 'context_type',
              type=click.Choice(['session', 'task', 'all']),
              default='all', help='Context type to clean')
@click.option('--older-than', '-d', type=int, default=90,
              help='Delete items older than N days')
@click.option('--dry-run', is_flag=True,
              help='Show what would be deleted without deleting')
@click.pass_context
def context_clean(ctx, context_type: str, older_than: int, dry_run: bool):
    """Clean old archived context.

    Removes archived context older than the specified number of days.
    Uses --dry-run to preview before deleting.

    Examples:
      vibey context clean --older-than 90 --dry-run
      vibey context clean --type session --older-than 30
    """
    from vibey.cli.commands import context_clean_cmd

    exit_code = context_clean_cmd(
        context_type=context_type,
        older_than_days=older_than,
        dry_run=dry_run,
    )
    sys.exit(exit_code)


@context.command('export')
@click.argument('context_id')
@click.option('--type', '-t', 'context_type',
              type=click.Choice(['session', 'task', 'decision', 'sprint']),
              help='Context type')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.pass_context
def context_export(ctx, context_id: str, context_type: str, output: str):
    """Export context to file.

    Examples:
      vibey context export 01KC7MN54VXRB3APC5FV5XBDXX --type session -o session.yaml
      vibey context export user-journey-phase-4-4 --type sprint -o sprint-context.tar.gz
    """
    from vibey.cli.commands import context_export_cmd

    exit_code = context_export_cmd(
        context_id=context_id,
        context_type=context_type,
        output_path=output,
    )
    sys.exit(exit_code)


@context.command('search')
@click.argument('query')
@click.option('--type', '-t', 'context_type',
              type=click.Choice(['session', 'task', 'decision', 'sprint', 'all']),
              default='all', help='Context type to search')
@click.option('--limit', '-n', type=int, default=20, help='Maximum results')
@click.pass_context
def context_search(ctx, query: str, context_type: str, limit: int):
    """Search context by content.

    Examples:
      vibey context search "ULID naming" --type decision
      vibey context search "phase 4" --limit 10
    """
    from vibey.cli.commands import context_search_cmd

    exit_code = context_search_cmd(
        query=query,
        context_type=context_type,
        limit=limit,
    )
    sys.exit(exit_code)


@context.command('init')
@click.pass_context
def context_init(ctx):
    """Initialize context directory structure.

    Creates the .vibey/context/ directory with proper subdirectories
    and initial configuration files.

    Examples:
      vibey context init
    """
    from vibey.cli.commands import context_init_cmd

    exit_code = context_init_cmd()
    sys.exit(exit_code)


@context.command('freshness')
@click.argument('ticket_id')
@click.option('--fresh-hours', type=int, default=24,
              help='Hours within which context is considered fresh (default: 24)')
@click.option('--stale-hours', type=int, default=72,
              help='Hours within which context is considered stale (default: 72)')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['text', 'json', 'yaml']),
              default='text', help='Output format')
@click.pass_context
def context_freshness(ctx, ticket_id: str, fresh_hours: int, stale_hours: int, output_format: str):
    """Check freshness of context files for a ticket.

    Shows how recently context files (plan, runtime, post-mortem) have been
    modified to help determine if context data may be stale.

    Examples:
      vibey context freshness 01KCMGXCCH84MG5BWK8MY8ZT83
      vibey context freshness 01KCMGXCCH84MG5BWK8MY8ZT83 --fresh-hours 12
      vibey context freshness 01KCMGXCCH84MG5BWK8MY8ZT83 --format json
    """
    from vibey.cli.commands import context_freshness_cmd

    exit_code = context_freshness_cmd(
        ticket_id=ticket_id,
        fresh_hours=fresh_hours,
        stale_hours=stale_hours,
        output_format=output_format,
    )
    sys.exit(exit_code)


@context.command('budget')
@click.option('--ticket', '-t', 'ticket_id', type=str,
              help='Ticket ID to analyze context budget for')
@click.option('--max-tokens', '-m', type=int, default=100000,
              help='Maximum token budget (default: 100000)')
@click.option('--show-artifacts', '-a', is_flag=True,
              help='Show individual artifact token counts')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['text', 'json', 'yaml']),
              default='text', help='Output format')
@click.pass_context
def context_budget(ctx, ticket_id: str, max_tokens: int, show_artifacts: bool, output_format: str):
    """Show token budget status for context loading.

    Displays current token usage and remaining budget to prevent
    overloading AI context windows when loading plan, runtime,
    and artifact context.

    Examples:
      vibey context budget
      vibey context budget --ticket 01KCMGXCCH84MG5BWK8MY8ZT83
      vibey context budget --max-tokens 50000 --show-artifacts
      vibey context budget --format json
    """
    from vibey.cli.commands import context_budget_cmd

    exit_code = context_budget_cmd(
        ticket_id=ticket_id,
        max_tokens=max_tokens,
        show_artifacts=show_artifacts,
        output_format=output_format,
    )
    sys.exit(exit_code)


# ============================================================================
# Parity Commands - CLI/MCP Interface Parity Checking
# ============================================================================

@cli.group()
@click.pass_context
def parity(ctx):
    """CLI/MCP parity checking - verify command interface consistency.

    The parity system ensures that commands defined with @unified_command
    are consistently available in both CLI and MCP interfaces as intended.

    Commands can be:
    - Both interfaces (default): Available in CLI and MCP
    - CLI only: Available only in CLI (e.g., interactive features)
    - MCP only: Available only in MCP (e.g., agent-specific operations)

    Examples:

      vibey parity check         # Run parity check
      vibey parity check -v      # Verbose output with command lists
      vibey parity report        # Generate detailed report
    """
    ctx.ensure_object(dict)


@parity.command('check')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed command lists')
@click.option('--strict', is_flag=True, help='Treat warnings as errors')
@click.pass_context
def parity_check(ctx, verbose: bool, strict: bool):
    """Check CLI/MCP parity for unified commands.

    Verifies that all commands registered with @unified_command are
    properly available in the interfaces they're configured for.

    Returns exit code 0 if parity check passes, 1 if violations found.

    Examples:
      vibey parity check
      vibey parity check --verbose
      vibey parity check --strict
    """
    from vibey.unified import check_parity

    report = check_parity()

    # Print report
    click.echo(report.format_report(verbose=verbose))

    # Determine exit code
    if strict:
        # In strict mode, warnings also cause failure
        if report.violations:
            sys.exit(1)
    else:
        # Normal mode: only errors cause failure
        if not report.is_passing:
            sys.exit(1)

    sys.exit(0)


@parity.command('report')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['text', 'json', 'yaml']),
              default='text', help='Output format')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.pass_context
def parity_report(ctx, output_format: str, output: str):
    """Generate detailed parity report.

    Creates a comprehensive report of CLI/MCP command parity including:
    - Command counts by interface
    - List of commands in each category
    - Any parity violations
    - Exclusion reasons for single-interface commands

    Examples:
      vibey parity report
      vibey parity report --format json
      vibey parity report --format yaml -o parity-report.yaml
    """
    from vibey.unified import check_parity
    import json

    report = check_parity()

    if output_format == 'text':
        content = report.format_report(verbose=True)
    elif output_format == 'json':
        content = json.dumps({
            'total_commands': report.total_commands,
            'cli_only_commands': report.cli_only_commands,
            'mcp_only_commands': report.mcp_only_commands,
            'both_interfaces_commands': report.both_interfaces_commands,
            'excluded_commands': report.excluded_commands,
            'violations': [
                {
                    'command_name': v.command_name,
                    'violation_type': v.violation_type,
                    'description': v.description,
                    'severity': v.severity,
                }
                for v in report.violations
            ],
            'is_passing': report.is_passing,
        }, indent=2)
    elif output_format == 'yaml':
        import yaml
        content = yaml.dump({
            'total_commands': report.total_commands,
            'cli_only_commands': report.cli_only_commands,
            'mcp_only_commands': report.mcp_only_commands,
            'both_interfaces_commands': report.both_interfaces_commands,
            'excluded_commands': report.excluded_commands,
            'violations': [
                {
                    'command_name': v.command_name,
                    'violation_type': v.violation_type,
                    'description': v.description,
                    'severity': v.severity,
                }
                for v in report.violations
            ],
            'is_passing': report.is_passing,
        }, default_flow_style=False)

    if output:
        with open(output, 'w') as f:
            f.write(content)
        click.echo(f"Report written to {output}")
    else:
        click.echo(content)


# ============================================================================
# Planned Status Commands - Planning workflow management
# ============================================================================

@cli.group()
@click.pass_context
def planned(ctx):
    """Planned status workflow - check and approve planning criteria.

    The planned status system helps ensure tickets have proper planning
    before work begins. A ticket is "planned" when required criteria are met:
    - YAML file exists (required)
    - Context files exist (optional)
    - Manual approval (optional, if configured)

    Workflow:
    1. Check if ticket is planned: vibey planned check <id>
    2. List unplanned tickets: vibey planned list-unplanned
    3. Get next work item: vibey planned next <track-id>
    4. Approve planning: vibey planned approve <id>

    Examples:

      vibey planned check 01KC7MN54VXRB3APC5FV5XBDXX
      vibey planned list-unplanned --scope tasks
      vibey planned next 01KC2D0JK9JKQXGQW6MQEB0JZP
      vibey planned approve 01KC7MN54VXRB3APC5FV5XBDXX
    """
    ctx.ensure_object(dict)


@planned.command('check')
@click.argument('ticket_id')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed criteria status')
@click.pass_context
def planned_check(ctx, ticket_id: str, verbose: bool):
    """Check if a ticket is fully planned and ready for implementation.

    Evaluates all planning criteria for the ticket and reports status.
    A ticket is planned when all required criteria are met.

    Examples:
      vibey planned check 01KC7MN54VXRB3APC5FV5XBDXX
      vibey planned check 01KC7MN54VXRB3APC5FV5XBDXX --verbose
    """
    from pathlib import Path
    from vibey.operations.roadmap.planned_ops import check_planned

    root_dir = Path.cwd()

    try:
        result = check_planned(root_dir, ticket_id)

        # Format output
        if result.is_planned:
            icon = "✓"
            status_msg = "fully planned"
            style = "green"
        else:
            icon = "○"
            status_msg = "not planned"
            style = "yellow"

        console.print(f"[{style}]{icon}[/{style}] {result.ticket_type.title()} {ticket_id} is {status_msg}")
        console.print(f"  Progress: {result.criteria_met}/{result.criteria_total} criteria met")

        if verbose and result.unmet_criteria:
            console.print("\n  [bold]Unmet criteria:[/bold]")
            for criterion in result.unmet_criteria:
                console.print(f"    - {criterion}")

        if result.unplanned_children:
            console.print(f"\n  [bold]Unplanned children:[/bold] {len(result.unplanned_children)}")
            if verbose:
                for child_id in result.unplanned_children[:5]:
                    console.print(f"    - {child_id}")
                if len(result.unplanned_children) > 5:
                    console.print(f"    ... and {len(result.unplanned_children) - 5} more")

        sys.exit(0 if result.is_planned else 1)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error checking planned status:[/red] {e}")
        sys.exit(1)


@planned.command('approve')
@click.argument('ticket_id')
@click.option('--approver', help='Name of approver')
@click.option('--notes', help='Approval notes')
@click.pass_context
def planned_approve(ctx, ticket_id: str, approver: Optional[str], notes: Optional[str]):
    """Manually approve a ticket's planning.

    Sets a metadata flag indicating planning has been reviewed and approved.
    Useful when automated criteria can't capture all planning requirements.

    Examples:
      vibey planned approve 01KC7MN54VXRB3APC5FV5XBDXX
      vibey planned approve 01KC7MN54VXRB3APC5FV5XBDXX --approver "alice"
      vibey planned approve 01KC7MN54VXRB3APC5FV5XBDXX --notes "Reviewed in planning meeting"
    """
    from pathlib import Path
    from vibey.operations.roadmap.planned_ops import approve_planned

    root_dir = Path.cwd()

    try:
        result = approve_planned(root_dir, ticket_id, approver, notes)
        console.print(f"[green]✓[/green] Approved planning for {ticket_id}")
        if approver:
            console.print(f"  Approved by: {approver}")
        console.print(f"  Timestamp: {result['approved_at']}")
        sys.exit(0)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error approving:[/red] {e}")
        sys.exit(1)


@planned.command('list-unplanned')
@click.option('--scope', type=click.Choice(['all', 'tracks', 'sprints', 'tasks']),
              default='tasks', help='What to list')
@click.option('--track', '-t', help='Filter by track ID')
@click.option('--sprint', '-s', help='Filter by sprint ID')
@click.option('--limit', '-n', default=20, help='Maximum results')
@click.pass_context
def planned_list_unplanned(ctx, scope: str, track: Optional[str],
                           sprint: Optional[str], limit: int):
    """List tickets that are not yet planned.

    Shows tickets missing required planning criteria. Use filters to
    narrow down the scope.

    Examples:
      vibey planned list-unplanned
      vibey planned list-unplanned --scope sprints
      vibey planned list-unplanned --track 01KC2D0JK9JKQXGQW6MQEB0JZP
      vibey planned list-unplanned --limit 50
    """
    from pathlib import Path
    from vibey.operations.roadmap.planned_ops import list_unplanned

    root_dir = Path.cwd()

    try:
        results = list_unplanned(
            root_dir,
            scope=scope,
            track_id=track,
            sprint_id=sprint,
        )

        # Apply limit
        results = results[:limit]

        if not results:
            console.print(f"[green]✓[/green] All {scope} are planned!")
            sys.exit(0)

        console.print(f"[bold]Unplanned {scope} ({len(results)}):[/bold]")
        for item in results:
            console.print(f"  ○ {item['id']} - {item['title']}")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error listing unplanned:[/red] {e}")
        sys.exit(1)


@planned.command('next')
@click.argument('track_id')
@click.pass_context
def planned_next(ctx, track_id: str):
    """Get the next planning work item for a track.

    Returns what needs to be done to plan the next unplanned ticket
    in the specified track. Useful for systematic planning workflow.

    Examples:
      vibey planned next 01KC2D0JK9JKQXGQW6MQEB0JZP
    """
    from pathlib import Path
    from vibey.operations.roadmap.planned_ops import get_next_planning_work

    root_dir = Path.cwd()

    try:
        item = get_next_planning_work(root_dir, track_id)

        if item is None:
            console.print(f"[green]✓[/green] Track {track_id} is fully planned!")
            sys.exit(0)

        console.print(f"[bold]Next planning work for {track_id}:[/bold]")
        console.print(f"  Ticket: {item.ticket_id}")
        console.print(f"  Title: {item.ticket_title}")
        console.print(f"  Criterion: {item.criterion}")
        console.print(f"  Action: {item.action}")
        console.print(f"  Required: {'Yes' if item.required else 'No'}")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error getting next work:[/red] {e}")
        sys.exit(1)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for the vibey CLI."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
