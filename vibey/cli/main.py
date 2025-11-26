"""
Vibey CLI - Main entry point for the Vibey Agent Framework.

This module provides the main CLI interface using Click, organizing all
framework commands into logical groups.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Version
__version__ = "2.5.0"

# Console for rich output
console = Console()


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
@click.pass_context
def roadmap(ctx):
    """
    Manage roadmap system - tracks, sprints, tasks, and dependencies.

    The roadmap system provides hierarchical project planning with:
    - Tracks: Major feature areas or work streams
    - Sprints: Time-boxed iterations within tracks
    - Tasks: Specific work items within sprints
    - Dependencies: Blocker relationships between items

    Examples:

      vibey roadmap init           # Initialize new roadmap
      vibey roadmap status         # Show current status
      vibey roadmap show sprint-1  # Show sprint details
      vibey roadmap start task-001 # Start a task
    """
    pass


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
@click.pass_context
def roadmap_status(ctx, track: Optional[str], sprint: Optional[str]):
    """Show roadmap status - tracks, sprints, and tasks"""
    from vibey.cli.commands import roadmap_status_cmd

    exit_code = roadmap_status_cmd(track, sprint)
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
@click.pass_context
def roadmap_complete(ctx, item_id: str, no_commits: bool):
    """Complete a track, sprint, or task

    Examples:
      vibey roadmap complete my-track                    # Complete a track
      vibey roadmap complete my-track-1                  # Complete a sprint
      vibey roadmap complete my-track-1-task-001        # Complete a task
      vibey roadmap complete task-001 --no-commits      # Skip commit check
    """
    from vibey.cli.commands import roadmap_complete_cmd

    exit_code = roadmap_complete_cmd(item_id, skip_commit_check=no_commits)
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
        load_roadmap, save_roadmap, load_track, save_track, load_sprint, save_sprint
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
@click.pass_context
def db_rebuild(ctx, force: bool):
    """Rebuild database from YAML files.

    Drops all tables and reloads from YAML. Use after pulling changes
    or to fix database corruption.

    WARNING: Uncommitted database changes will be lost!

    Examples:
      vibey roadmap db rebuild
      vibey roadmap db rebuild --force  # Skip dirty check
    """
    from vibey.cli.commands import db_rebuild_cmd

    exit_code = db_rebuild_cmd(force=force)
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
