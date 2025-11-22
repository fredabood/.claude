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


@roadmap.command('show')
@click.argument('item_id')
@click.pass_context
def roadmap_show(ctx, item_id: str):
    """Show details for a track, sprint, or task"""
    from vibey.cli.commands import roadmap_show_cmd

    exit_code = roadmap_show_cmd(item_id)
    sys.exit(exit_code)


@roadmap.command('start')
@click.argument('item_id')
@click.pass_context
def roadmap_start(ctx, item_id: str):
    """Start a sprint or task"""
    from vibey.cli.commands import roadmap_start_cmd

    exit_code = roadmap_start_cmd(item_id)
    sys.exit(exit_code)


@roadmap.command('complete')
@click.argument('item_id')
@click.pass_context
def roadmap_complete(ctx, item_id: str):
    """Complete a sprint or task"""
    from vibey.cli.commands import roadmap_complete_cmd

    exit_code = roadmap_complete_cmd(item_id)
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
    - cursor (Cursor IDE)
    - aider (Aider CLI)
    - continue (Continue.dev)

    Examples:

      vibey deploy --platform claude-code
      vibey deploy --platform goose --clean
      vibey deploy --list-platforms
    """
    pass


@deploy.command('run')
@click.option('--platform', type=click.Choice(['claude-code', 'goose', 'all']),
              required=True, help='Target platform (or "all" for all platforms)')
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
