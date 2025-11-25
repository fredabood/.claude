"""
Command implementations for vibey CLI.

This module provides Python API for all CLI commands using direct function imports
from the operations modules (no subprocess calls).
"""

from pathlib import Path
from typing import Optional

# Import operations modules
from vibey.operations.roadmap import (
    init_roadmap,
    query_roadmap_summary,
    query_track_details,
    query_sprint_details,
    query_task_details,
    start_task,
    start_sprint,
    complete_task,
    complete_sprint,
    complete_track,
    get_task_context,
    validate_roadmap,
    add_commit_to_task,
    get_current_commit,
)
from vibey.operations.roadmap.summarize import summarize_sprint, summarize_task
from vibey.operations.deployment import deploy_framework
from vibey.operations.docs import generate_docs
from vibey.operations.config import generate_config, update_config_value
from vibey.operations.migrations import (
    migrate_to_roadmap,
    migrate_to_hierarchical,
    migrate_embedded_tasks,
)

# Import formatters for CLI output
from vibey.cli.formatters import (
    format_roadmap_summary,
    format_track_details,
    format_sprint_details,
    format_task_details,
    format_success,
    format_error,
)


# ============================================================================
# Roadmap Commands
# ============================================================================

def roadmap_init_cmd(name: str, version: str) -> int:
    """Initialize a new roadmap."""
    root_dir = Path.cwd()  # Project root
    return init_roadmap(
        root_dir=root_dir,  # init_roadmap expects project root (adds .vibey/ internally)
        roadmap_id=name or "default-roadmap",
        roadmap_name=name or "Default Roadmap",
        version=version or "1.0.0",
    )


def roadmap_status_cmd(track: Optional[str] = None, sprint: Optional[str] = None) -> int:
    """Show roadmap status."""
    root_dir = Path.cwd()  # Project root

    try:
        if sprint:
            result = query_sprint_details(root_dir, sprint)
            print(format_sprint_details(result))
        elif track:
            result = query_track_details(root_dir, track)
            print(format_track_details(result))
        else:
            result = query_roadmap_summary(root_dir)
            print(format_roadmap_summary(result))
        return 0
    except Exception as e:
        print(format_error(str(e)))
        return 1


def roadmap_sync_cmd(verbose: bool = False) -> int:
    """Sync status from individual files to main roadmap.yaml."""
    root_dir = Path.cwd()

    try:
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager
        from vibey.operations.roadmap.update import _update_roadmap_progress

        fs = FileSystemManager(root_dir)
        roadmap_path = fs.get_roadmap_path()

        if not roadmap_path.exists():
            print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
            return 1

        print("🔄 Syncing roadmap status...")

        if verbose:
            print("  Reading individual track/sprint/task files...")

        # Trigger the full sync chain
        _update_roadmap_progress(fs)

        print("✅ Roadmap synced successfully")

        if verbose:
            # Show summary of what was synced
            from vibey.operations.roadmap.query import query_roadmap_summary
            from vibey.cli.formatters import format_roadmap_summary
            result = query_roadmap_summary(root_dir)
            print("\nCurrent status:")
            print(format_roadmap_summary(result))

        return 0
    except Exception as e:
        print(format_error(str(e)))
        return 1


def roadmap_show_cmd(item_id: str) -> int:
    """Show details for an item."""
    root_dir = Path.cwd()  # Project root

    try:
        # Determine type from ID format
        if 'task' in item_id:
            result = query_task_details(root_dir, item_id)
        elif item_id.count('-') >= 2:  # sprint format: track-sprint
            result = query_sprint_details(root_dir, item_id)
        else:  # track format
            result = query_track_details(root_dir, item_id)

        # Check if query returned an error
        if "error" in result:
            print(format_error(result["error"]))
            return 1

        # Format and print the result based on type
        if 'task' in item_id:
            print(format_task_details(result))
        elif item_id.count('-') >= 2:
            print(format_sprint_details(result))
        else:
            print(format_track_details(result))
        return 0
    except Exception as e:
        print(format_error(str(e)))
        return 1


def roadmap_start_cmd(item_id: str) -> int:
    """Start a sprint or task."""
    root_dir = Path.cwd()  # Project root

    if 'task' in item_id:
        return start_task(root_dir, item_id)
    elif 'sprint' in item_id or item_id.count('-') >= 1:
        return start_sprint(root_dir, item_id)
    else:
        print(f"Error: Cannot determine item type from ID: {item_id}")
        print("Expected format: <track>-<sprint>-task-<num> or <track>-<sprint>[-name]")
        return 1


def roadmap_complete_cmd(item_id: str, skip_commit_check: bool = False) -> int:
    """Complete a track, sprint, or task."""
    root_dir = Path.cwd()  # Project root

    # Task IDs contain '-task-'
    if '-task-' in item_id:
        return complete_task(root_dir, item_id, skip_commit_check=skip_commit_check)

    # Check if it's a sprint (ends with -N where N is a number)
    # Sprint format: track-name-N (e.g., platform-context-management-5)
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager
    fs = FileSystemManager(root_dir)

    # Try sprint first (more specific pattern)
    sprint_path = fs.get_sprint_path(item_id)
    if sprint_path.exists():
        return complete_sprint(root_dir, item_id)

    # Try track
    track_path = fs.get_track_path(item_id)
    if track_path.exists():
        return complete_track(root_dir, item_id)

    # Neither found
    print(f"Error: Cannot find track or sprint with ID: {item_id}")
    print("Expected format:")
    print("  Track:  <track-name> (e.g., platform-context-management)")
    print("  Sprint: <track-name>-<num> (e.g., platform-context-management-5)")
    print("  Task:   <sprint-id>-task-<num> (e.g., platform-context-management-5-task-001)")
    return 1


def roadmap_context_cmd(task_id: str) -> int:
    """Get context for a task."""
    return get_task_context(task_id=task_id, root_dir=Path.cwd())


def roadmap_summarize_cmd(item_type: str, item_id: str) -> int:
    """Summarize an item."""
    root_dir = Path.cwd()  # Project root

    # Determine type from ID format
    if 'task' in item_id:
        # Extract sprint_id from task_id (format: track-sprint-task-NNN)
        parts = item_id.split('-task-')
        if len(parts) != 2:
            print(f"Error: Invalid task ID format: {item_id}")
            return 1
        sprint_id = parts[0]
        return summarize_task(sprint_id=sprint_id, task_id=item_id, root_dir=root_dir)
    else:
        return summarize_sprint(sprint_id=item_id, root_dir=root_dir)


def roadmap_list_cmd() -> int:
    """List all tracks/sprints/tasks."""
    root_dir = Path.cwd()  # Project root

    try:
        result = query_roadmap_summary(root_dir)
        print(format_roadmap_summary(result))
        return 0
    except Exception as e:
        print(format_error(str(e)))
        return 1


def roadmap_validate_cmd() -> int:
    """Validate roadmap structure."""
    return validate_roadmap(root_dir=Path.cwd())


def roadmap_sync_docs_cmd(
    sync_all: bool = False,
    track: Optional[str] = None,
    sprint: Optional[str] = None,
    summaries_only: bool = False,
    dry_run: bool = False,
    delete_orphaned: bool = False
) -> int:
    """Synchronize documentation from .vibey/roadmap/ to docs/roadmap/"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from vibey.operations.docs.sync_engine import SyncEngine, SyncConfig

    root_dir = Path.cwd()
    source_dir = ".vibey/roadmap"
    target_dir = "docs/roadmap"

    # Build config
    config = SyncConfig(
        source_dir=source_dir,
        target_dir=target_dir,
        delete_orphaned=delete_orphaned
    )

    # Handle filtering by track or sprint
    if track and sprint:
        print("❌ Error: Cannot specify both --track and --sprint")
        return 1

    if track:
        config.source_dir = f"{source_dir}/{track}"
        config.target_dir = f"{target_dir}/{track}"
        print(f"🎯 Syncing track: {track}")

    elif sprint:
        # Sprint IDs are like "documentation-system-1"
        parts = sprint.rsplit('-', 1)
        if len(parts) == 2 and parts[1].isdigit():
            track_slug = parts[0]
            config.source_dir = f"{source_dir}/{track_slug}/{sprint}"
            config.target_dir = f"{target_dir}/{track_slug}/{sprint}"
            print(f"🎯 Syncing sprint: {sprint}")
        else:
            print(f"❌ Error: Invalid sprint ID format: {sprint}")
            return 1

    # Filter for summaries only
    if summaries_only:
        config.include_patterns = ["**/*-COMPLETED.md", "**/roadmap.md"]

    # Create engine and sync
    engine = SyncEngine(config)

    try:
        result = engine.sync(dry_run=dry_run)

        # Print results
        prefix = "Would sync" if dry_run else "Synced"
        print()
        print("=" * 60)
        print(f"📄 Documentation Sync {'Preview' if dry_run else 'Complete'}")
        print("=" * 60)

        if result.files_copied:
            print(f"\n✓ {prefix} {len(result.files_copied)} file(s):")
            for file in result.files_copied[:10]:
                print(f"  • {file}")
            if len(result.files_copied) > 10:
                print(f"  ... and {len(result.files_copied) - 10} more")

        if result.files_skipped:
            print(f"\n⏭️  Skipped {len(result.files_skipped)} unchanged file(s)")

        if result.files_deleted:
            print(f"\n🗑️  {'Would delete' if dry_run else 'Deleted'} {len(result.files_deleted)} orphaned file(s):")
            for file in result.files_deleted:
                print(f"  • {file}")

        if result.errors:
            print(f"\n❌ {len(result.errors)} error(s):")
            for file, error in result.errors:
                print(f"  • {file}: {error}")

        print(f"\n⏱️  Duration: {result.duration_seconds:.2f}s")

        if not dry_run and result.success:
            print("\n✅ Synchronization completed successfully")
        elif dry_run:
            print("\n💡 Run without --dry-run to perform the sync")
        else:
            print("\n⚠️  Synchronization completed with errors")

        print()
        return 0 if result.success else 1

    except Exception as e:
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def roadmap_add_context_cmd(
    file_path: str,
    track: Optional[str] = None,
    sprint: Optional[str] = None,
    task: Optional[str] = None
) -> int:
    """Add a context file to a roadmap object."""
    import shutil

    root_dir = Path.cwd()
    source = Path(file_path)

    # Validate mutually exclusive options
    options_count = sum([bool(track), bool(sprint), bool(task)])
    if options_count != 1:
        print("❌ Error: Must specify exactly one of --track, --sprint, or --task")
        return 1

    if not source.exists():
        print(f"❌ Error: File not found: {source}")
        return 1

    # Determine target directory
    if task:
        # Parse task ID to get path components
        # Format: track-sprint-task-NNN
        parts = task.split('-task-')
        if len(parts) != 2:
            print(f"❌ Error: Invalid task ID format: {task}")
            return 1
        sprint_id = parts[0]
        track_parts = sprint_id.rsplit('-', 1)
        if len(track_parts) != 2:
            print(f"❌ Error: Cannot parse track from task ID: {task}")
            return 1
        track_id = track_parts[0]
        context_dir = root_dir / ".vibey" / "roadmap" / track_id / sprint_id / task / "context"
    elif sprint:
        # Parse sprint ID
        parts = sprint.rsplit('-', 1)
        if len(parts) != 2 or not parts[1].isdigit():
            print(f"❌ Error: Invalid sprint ID format: {sprint}")
            return 1
        track_id = parts[0]
        context_dir = root_dir / ".vibey" / "roadmap" / track_id / sprint / "context"
    else:
        # Track
        context_dir = root_dir / ".vibey" / "roadmap" / track / "context"

    # Create context directory if needed
    context_dir.mkdir(parents=True, exist_ok=True)

    # Copy file to context directory
    target = context_dir / source.name

    if target.exists():
        print(f"⚠️  File already exists: {target}")
        response = input("Overwrite? [y/N]: ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return 1

    try:
        shutil.copy2(source, target)
        print(f"✅ Added context file: {target.relative_to(root_dir)}")

        # Optionally trigger sync
        from vibey.operations.docs.sync_hooks import trigger_on_context_add
        target_id = task or sprint or track
        trigger_on_context_add(target_id, str(source.name), verbose=True)

        return 0
    except Exception as e:
        print(f"❌ Error adding context: {e}")
        return 1


def roadmap_add_commit_cmd(task_id: str, commit_sha: Optional[str] = None, auto: bool = False) -> int:
    """Add a git commit to a task."""
    if auto:
        commit_sha = get_current_commit()
        if not commit_sha:
            print("Error: Could not detect current commit")
            return 1
    elif not commit_sha:
        print("Error: Either provide a commit SHA or use --auto flag")
        return 1

    return add_commit_to_task(
        task_id=task_id,
        commit_sha=commit_sha,
        vibey_path=Path.cwd() / ".vibey",  # This one expects .vibey/ path
        auto_detect=auto
    )


def roadmap_validate_advanced_cmd(verbose: bool = False, check: str = 'all') -> int:
    """Advanced roadmap validation."""
    from vibey.operations.roadmap.advanced_validator import (
        AdvancedValidator,
        AdvancedValidationReport,
        print_advanced_report
    )

    root_dir = Path.cwd()
    validator = AdvancedValidator(root_dir)

    print("Running advanced validation checks...")
    print()

    if check == 'all':
        # Run all checks
        report = validator.validate()
        print_advanced_report(report, verbose=verbose)
        return 0 if not report.has_issues else 1

    # Run specific check
    report = AdvancedValidationReport()

    if check == 'circular':
        print("Checking for circular dependencies...")
        tasks = validator._load_all_tasks()
        report.total_tasks = len(tasks)
        from vibey.operations.roadmap.advanced_validator import detect_circular_dependencies
        report.circular_dependencies = detect_circular_dependencies(tasks)

    elif check == 'orphans':
        print("Checking for orphaned tasks...")
        from vibey.operations.roadmap.advanced_validator import find_orphaned_tasks
        report.orphaned_tasks = find_orphaned_tasks(validator.roadmap_dir)

    elif check == 'references':
        print("Checking for broken references...")
        from vibey.operations.roadmap.advanced_validator import find_broken_references
        report.broken_references = find_broken_references(validator.roadmap_dir)

    elif check == 'progress':
        print("Checking progress counters...")
        from vibey.operations.roadmap.advanced_validator import validate_progress_counters
        report.progress_mismatches = validate_progress_counters(validator.roadmap_dir)

    print_advanced_report(report, verbose=verbose)
    return 0 if not report.has_issues else 1


def roadmap_repair_cmd(
    fix_progress: bool = False,
    fix_references: bool = False,
    fix_all: bool = False,
    dry_run: bool = False,
    verbose: bool = False
) -> int:
    """Auto-repair roadmap integrity issues."""
    from vibey.operations.roadmap.advanced_validator import AdvancedValidator
    from vibey.operations.roadmap.auto_repair import auto_repair_all

    root_dir = Path.cwd()

    # If no specific flags set, default to --all behavior
    if not fix_progress and not fix_references and not fix_all:
        fix_all = True

    # Run validation first to find issues
    print("🔍 Scanning for issues...")
    print()

    validator = AdvancedValidator(root_dir)
    report = validator.validate()

    if not report.has_issues:
        print("✅ No issues detected! Roadmap is healthy.")
        return 0

    # Show what was found
    total_issues = (
        len(report.circular_dependencies) +
        len(report.orphaned_tasks) +
        len(report.broken_references) +
        len(report.progress_mismatches)
    )

    print(f"⚠️  Found {total_issues} issues:\n")

    if report.progress_mismatches:
        print(f"  📊 Progress counter mismatches: {len(report.progress_mismatches)} (auto-fixable)")

    if report.broken_references:
        print(f"  🔗 Broken references: {len(report.broken_references)} (removable)")

    if report.circular_dependencies:
        print(f"  🔄 Circular dependencies: {len(report.circular_dependencies)} (manual fix required)")

    if report.orphaned_tasks:
        print(f"  👻 Orphaned tasks: {len(report.orphaned_tasks)} (manual fix required)")

    print()

    # Determine what to fix
    if fix_all:
        do_fix_progress = True
        do_fix_references = True
    else:
        do_fix_progress = fix_progress
        do_fix_references = fix_references

    # Preview mode
    if dry_run:
        print("🔍 DRY-RUN MODE: Showing what would be fixed (no changes will be made)\n")

        if do_fix_progress and report.progress_mismatches:
            print(f"Would fix {len(report.progress_mismatches)} progress counter mismatches:")
            for i, mismatch in enumerate(report.progress_mismatches[:5], 1):
                print(f"  {i}. {mismatch.entity_id}")
                print(f"     Claimed: {mismatch.claimed_completed}/{mismatch.claimed_total}")
                print(f"     Actual:  {mismatch.actual_completed}/{mismatch.actual_total}")
            if len(report.progress_mismatches) > 5:
                print(f"     ... and {len(report.progress_mismatches) - 5} more")
            print()

        if do_fix_references and report.broken_references:
            print(f"Would remove {len(report.broken_references)} broken references:")
            for i, ref in enumerate(report.broken_references[:5], 1):
                print(f"  {i}. {ref.task_id}")
                print(f"     Field: {ref.field}")
                print(f"     Missing: {ref.missing_id}")
                if ref.suggested_ids:
                    print(f"     Similar: {', '.join(ref.suggested_ids)}")
            if len(report.broken_references) > 5:
                print(f"     ... and {len(report.broken_references) - 5} more")
            print()

        print("Run without --dry-run to apply these fixes")
        return 0

    # Confirm before fixing references (destructive operation)
    if do_fix_references and report.broken_references and not dry_run:
        print("⚠️  WARNING: Removing broken references is a destructive operation!")
        print("   This will permanently delete invalid task references.")
        print()
        response = input("Continue? [y/N]: ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return 1
        print()

    # Apply repairs
    print("🔧 Applying repairs...\n")

    results = auto_repair_all(
        report=report,
        fix_progress=do_fix_progress,
        fix_references=do_fix_references,
        dry_run=dry_run
    )

    # Print summary
    print("\n" + "=" * 80)
    print("REPAIR SUMMARY")
    print("=" * 80 + "\n")

    total_fixed = results['total_fixed']
    total_failed = results['total_failed']

    if total_fixed > 0:
        print(f"✅ Successfully repaired: {total_fixed} issues")

    if total_failed > 0:
        print(f"❌ Failed to repair: {total_failed} issues")

    # Show detailed results
    if verbose or total_failed > 0:
        print()

        if results['progress_counters'] and do_fix_progress:
            prog = results['progress_counters']
            print(f"Progress counters: {prog['repaired']}/{prog['total']} repaired")
            if prog['errors']:
                print("  Errors:")
                for error in prog['errors'][:5]:
                    print(f"    • {error}")

        if results['broken_references'] and do_fix_references:
            refs = results['broken_references']
            print(f"Broken references: {refs['removed']}/{refs['total']} removed")
            if refs['errors']:
                print("  Errors:")
                for error in refs['errors'][:5]:
                    print(f"    • {error}")

    print()

    if total_fixed > 0 and total_failed == 0:
        print("✅ All repairs completed successfully!")
        return 0
    elif total_fixed > 0 and total_failed > 0:
        print("⚠️  Some repairs completed, but some failed (see above)")
        return 1
    else:
        print("❌ No repairs could be completed")
        return 1


def install_hooks_cmd(force: bool = False) -> int:
    """Install git pre-commit hook."""
    from vibey.operations.roadmap.hooks import install_hooks

    print("Installing Vibey pre-commit hook...\n")

    success, message = install_hooks(project_root=Path.cwd(), force=force)

    print(message)

    if success:
        print("\nℹ️  Configuration:")
        print("  - Hook runs when .vibey/roadmap/ files are modified")
        print("  - Set VIBEY_HOOK_ADVANCED=true to enable advanced validation")
        print("  - Bypass with: git commit --no-verify (emergency only)")
        print("\nℹ️  Test the hook:")
        print("  1. Make a change to a roadmap file")
        print("  2. Run: git add .vibey/roadmap/...")
        print("  3. Run: git commit -m 'test'")
        print("  4. Hook will validate before allowing commit")
        return 0
    else:
        return 1


def uninstall_hooks_cmd() -> int:
    """Uninstall git pre-commit hook."""
    from vibey.operations.roadmap.hooks import uninstall_hooks

    print("Uninstalling Vibey pre-commit hook...\n")

    success, message = uninstall_hooks(project_root=Path.cwd())

    print(message)

    return 0 if success else 1


def check_hooks_cmd() -> int:
    """Check git hook installation status."""
    from vibey.operations.roadmap.hooks import get_hook_status

    status = get_hook_status(project_root=Path.cwd())

    print("Git Hook Status")
    print("=" * 70)
    print()

    if not status['git_repo']:
        print("❌ Not a git repository")
        return 1

    print(f"Git directory: {status['git_dir']}")
    print(f"Hooks directory exists: {'✅' if status['hooks_dir_exists'] else '❌'}")
    print()

    if not status['pre_commit_exists']:
        print("❌ No pre-commit hook installed")
        print()
        print("Install with: vibey roadmap install-hooks")
        return 1

    print(f"Pre-commit hook: {status['hook_path']}")
    print(f"  Is Vibey hook: {'✅' if status['is_vibey_hook'] else '❌'}")
    print(f"  Is executable: {'✅' if status['is_executable'] else '❌'}")
    print()

    if status['is_vibey_hook'] and status['is_executable']:
        print("✅ Vibey pre-commit hook is installed and active")
        print()
        print("Configuration:")
        print("  - VIBEY_HOOK_ADVANCED: Set to 'true' to enable advanced validation")
        print("  - Bypass: git commit --no-verify")
        return 0
    elif status['is_vibey_hook'] and not status['is_executable']:
        print("⚠️  Vibey hook installed but not executable")
        print()
        print(f"Fix with: chmod +x {status['hook_path']}")
        return 1
    else:
        print("⚠️  A different pre-commit hook is installed")
        print()
        print("To install Vibey hook:")
        print("  1. Back up existing hook if needed")
        print("  2. Run: vibey roadmap install-hooks --force")
        return 1


def roadmap_validate_fast_cmd(
    profile: str = "standard",
    incremental: bool = False,
    verbose: bool = False,
    benchmark: bool = False
) -> int:
    """Fast roadmap validation with caching."""
    from vibey.operations.roadmap.optimized_validator import (
        OptimizedValidator,
        ValidationProfile,
        print_validation_report,
        clear_yaml_cache
    )
    import time

    root_dir = Path.cwd()

    # Convert profile string to enum
    profile_map = {
        'quick': ValidationProfile.QUICK,
        'standard': ValidationProfile.STANDARD,
        'thorough': ValidationProfile.THOROUGH
    }
    profile_enum = profile_map[profile]

    if benchmark:
        # Run performance benchmark
        print("Running performance benchmark...\n")

        # Test 1: Quick validation
        print("Test 1: Quick validation (syntax only)")
        clear_yaml_cache()
        validator = OptimizedValidator(root_dir, ValidationProfile.QUICK)
        report = validator.validate()
        print(f"  Duration: {report.duration_seconds:.2f}s")
        print(f"  Files: {report.total_files}")
        print(f"  Target: <3s")
        print(f"  Status: {'✅ PASS' if report.duration_seconds < 3.0 else '❌ FAIL'}\n")

        # Test 2: Standard validation (first run - cold cache)
        print("Test 2: Standard validation (cold cache)")
        clear_yaml_cache()
        validator = OptimizedValidator(root_dir, ValidationProfile.STANDARD)
        report = validator.validate()
        print(f"  Duration: {report.duration_seconds:.2f}s")
        print(f"  Files: {report.total_files}")
        print(f"  Cache hit rate: {report.cache_hit_rate:.1f}%")
        print(f"  Target: <10s")
        print(f"  Status: {'✅ PASS' if report.duration_seconds < 10.0 else '❌ FAIL'}\n")

        # Test 3: Standard validation (second run - warm cache)
        print("Test 3: Standard validation (warm cache)")
        validator = OptimizedValidator(root_dir, ValidationProfile.STANDARD)
        report = validator.validate()
        print(f"  Duration: {report.duration_seconds:.2f}s")
        print(f"  Files: {report.total_files}")
        print(f"  Cache hit rate: {report.cache_hit_rate:.1f}%")
        print(f"  Target: <2s")
        print(f"  Status: {'✅ PASS' if report.duration_seconds < 2.0 else '❌ FAIL'}\n")

        # Test 4: Incremental validation
        print("Test 4: Incremental validation (changed files only)")
        validator = OptimizedValidator(root_dir, ValidationProfile.STANDARD)
        report = validator.validate(incremental=True)
        print(f"  Duration: {report.duration_seconds:.2f}s")
        print(f"  Files: {report.total_files}")
        print(f"  Cache hit rate: {report.cache_hit_rate:.1f}%")
        print(f"  Target: <2s")
        print(f"  Status: {'✅ PASS' if report.duration_seconds < 2.0 else '❌ FAIL'}\n")

        # Test 5: Thorough validation
        print("Test 5: Thorough validation (with git integration)")
        clear_yaml_cache()
        validator = OptimizedValidator(root_dir, ValidationProfile.THOROUGH)
        report = validator.validate()
        print(f"  Duration: {report.duration_seconds:.2f}s")
        print(f"  Files: {report.total_files}")
        print(f"  Cache hit rate: {report.cache_hit_rate:.1f}%")
        print(f"  Target: <20s")
        print(f"  Status: {'✅ PASS' if report.duration_seconds < 20.0 else '❌ FAIL'}\n")

        print("Benchmark complete!")
        return 0

    # Normal validation
    validator = OptimizedValidator(root_dir, profile_enum)
    report = validator.validate(incremental=incremental)

    # Print report
    print_validation_report(report, verbose=verbose)

    # Return exit code
    return 0 if report.invalid_files == 0 else 1


# ============================================================================
# Roadmap Checkpoint Commands
# ============================================================================

def checkpoint_create_cmd(name: Optional[str] = None) -> int:
    """Create a new integrity checkpoint."""
    import subprocess
    from datetime import datetime

    # Default to timestamped name if not provided
    if not name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"checkpoint_{timestamp}"

    script_path = Path(__file__).parent.parent.parent / "scripts" / "create-integrity-checkpoint.sh"

    try:
        result = subprocess.run(
            [str(script_path), name],
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error creating checkpoint: {e}")
        return 1


def checkpoint_list_cmd() -> int:
    """List all available checkpoints."""
    import subprocess

    script_path = Path(__file__).parent.parent.parent / "scripts" / "manage-checkpoints.sh"

    try:
        result = subprocess.run(
            [str(script_path), "list"],
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error listing checkpoints: {e}")
        return 1


def checkpoint_verify_cmd(name: str) -> int:
    """Verify checkpoint integrity."""
    import subprocess

    script_path = Path(__file__).parent.parent.parent / "scripts" / "manage-checkpoints.sh"

    try:
        result = subprocess.run(
            [str(script_path), "verify", name],
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error verifying checkpoint: {e}")
        return 1


def checkpoint_restore_cmd(name: str, verify_only: bool = False) -> int:
    """Restore from a checkpoint."""
    import subprocess

    script_path = Path(__file__).parent.parent.parent / "scripts" / "restore-integrity-checkpoint.sh"

    args = [str(script_path), name]
    if verify_only:
        args.append("--verify-only")

    try:
        result = subprocess.run(
            args,
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error restoring checkpoint: {e}")
        return 1


def checkpoint_clean_cmd(keep: int = 5) -> int:
    """Clean old checkpoints."""
    import subprocess

    script_path = Path(__file__).parent.parent.parent / "scripts" / "manage-checkpoints.sh"

    try:
        result = subprocess.run(
            [str(script_path), "clean", str(keep)],
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error cleaning checkpoints: {e}")
        return 1


def checkpoint_compare_cmd(checkpoint1: str, checkpoint2: str) -> int:
    """Compare two checkpoints."""
    import subprocess

    script_path = Path(__file__).parent.parent.parent / "scripts" / "manage-checkpoints.sh"

    try:
        result = subprocess.run(
            [str(script_path), "compare", checkpoint1, checkpoint2],
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error comparing checkpoints: {e}")
        return 1


# ============================================================================
# Safe YAML Edit Commands
# ============================================================================

def edit_file_cmd(file_path: str, modifications: list, dry_run: bool = False) -> int:
    """Safely edit a single YAML file."""
    from vibey.operations.roadmap.safe_yaml_editor import SafeYAMLEditor

    # Parse modifications from "key=value" format
    mod_dict = {}
    for mod in modifications:
        if '=' not in mod:
            print(f"Error: Invalid modification format '{mod}' (expected key=value)")
            return 1

        key, value = mod.split('=', 1)
        mod_dict[key] = value

    if not mod_dict:
        print("Error: No modifications specified. Use --set key=value")
        return 1

    try:
        editor = SafeYAMLEditor(auto_backup=True, validate=True)

        if dry_run:
            print("🔍 Dry-run mode: Previewing changes (no files will be modified)")
            print()

        result = editor.edit_file(file_path, mod_dict, dry_run=dry_run)

        if result.success:
            print(f"✅ Successfully {'validated' if dry_run else 'edited'}: {result.file_path}")

            if result.changes_made:
                print("\nChanges:")
                for field, change in result.changes_made.items():
                    print(f"  {field}: {change['old']} → {change['new']}")

            if result.backup_path:
                print(f"\nBackup: {result.backup_path}")

            if result.warnings:
                print("\nWarnings:")
                for warning in result.warnings:
                    print(f"  ⚠️  {warning}")

            return 0
        else:
            print(f"❌ Edit failed: {result.file_path}")
            print("\nErrors:")
            for error in result.errors:
                print(f"  • {error}")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def edit_bulk_cmd(file_pattern: str, modifications: list, dry_run: bool = False) -> int:
    """Safely bulk edit multiple YAML files."""
    from vibey.operations.roadmap.safe_yaml_editor import SafeYAMLEditor

    # Parse modifications
    mod_dict = {}
    for mod in modifications:
        if '=' not in mod:
            print(f"Error: Invalid modification format '{mod}' (expected key=value)")
            return 1

        key, value = mod.split('=', 1)
        mod_dict[key] = value

    if not mod_dict:
        print("Error: No modifications specified. Use --set key=value")
        return 1

    try:
        editor = SafeYAMLEditor(auto_backup=True, validate=True)

        if dry_run:
            print("🔍 Dry-run mode: Previewing changes (no files will be modified)")
            print()

        print(f"Finding files matching: {file_pattern}")
        result = editor.bulk_edit(file_pattern, mod_dict, dry_run=dry_run, root_dir=Path.cwd())

        print(f"\nFiles found: {result.total_files}")

        if result.success:
            print(f"✅ Bulk edit {'validated' if dry_run else 'completed'} successfully")
            print(f"  Files {'would be ' if dry_run else ''}changed: {result.files_changed}")

            if result.checkpoint_path:
                print(f"  Checkpoint: {result.checkpoint_path}")

            return 0
        else:
            print(f"❌ Bulk edit failed")
            print(f"  Files changed: {result.files_changed}")
            print(f"  Files failed: {result.files_failed}")

            if result.rollback_performed:
                print(f"  ✅ All changes rolled back")

            if result.errors:
                print("\nErrors:")
                for error in result.errors[:10]:  # Limit to first 10
                    print(f"  • {error}")

                if len(result.errors) > 10:
                    print(f"  ... and {len(result.errors) - 10} more errors")

            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def edit_validate_cmd(file_path: Optional[str] = None, validate_all: bool = False) -> int:
    """Validate YAML file(s)."""
    from vibey.operations.roadmap.safe_yaml_editor import SafeYAMLEditor

    editor = SafeYAMLEditor()

    if validate_all:
        # Validate all YAML files in roadmap
        roadmap_dir = Path.cwd() / ".vibey" / "roadmap"

        if not roadmap_dir.exists():
            print("Error: Roadmap directory not found")
            return 1

        yaml_files = list(roadmap_dir.rglob("*.yaml"))
        print(f"Validating {len(yaml_files)} YAML files...")
        print()

        valid_count = 0
        invalid_count = 0
        error_files = []

        for yaml_file in yaml_files:
            result = editor.validate_yaml_file(yaml_file)

            if result.valid:
                valid_count += 1
                print(f"✅ {yaml_file.relative_to(Path.cwd())}")
            else:
                invalid_count += 1
                print(f"❌ {yaml_file.relative_to(Path.cwd())}")
                error_files.append((yaml_file, result))

                for error in result.errors[:3]:  # Show first 3 errors per file
                    print(f"   • {error}")

        print()
        print(f"Summary: {valid_count} valid, {invalid_count} invalid")

        if error_files:
            print("\nFiles with errors:")
            for yaml_file, _ in error_files:
                print(f"  • {yaml_file.relative_to(Path.cwd())}")

        return 0 if invalid_count == 0 else 1

    elif file_path:
        # Validate single file
        result = editor.validate_yaml_file(file_path)

        print(f"Validating: {file_path}")
        print()

        if result.valid:
            print("✅ Validation passed")

            if result.warnings:
                print("\nWarnings:")
                for warning in result.warnings:
                    print(f"  ⚠️  {warning}")

            return 0
        else:
            print("❌ Validation failed")
            print("\nErrors:")
            for error in result.errors:
                print(f"  • {error}")

            if result.warnings:
                print("\nWarnings:")
                for warning in result.warnings:
                    print(f"  ⚠️  {warning}")

            return 1

    else:
        print("Error: Specify --file <path> or --all")
        return 1


def edit_rollback_cmd(last_n: int = 1) -> int:
    """Rollback recent edit operations."""
    from vibey.operations.roadmap.safe_yaml_editor import SafeYAMLEditor

    editor = SafeYAMLEditor()

    print(f"Rolling back last {last_n} edit(s)...")
    print()

    success_count = 0
    for i in range(last_n):
        if editor.rollback_last_edit():
            success_count += 1
        else:
            if i == 0:
                print("No backups found to rollback")
            break

    if success_count > 0:
        print()
        print(f"✅ Rolled back {success_count} edit(s)")
        return 0
    else:
        print()
        print("❌ No edits rolled back")
        return 1


# ============================================================================
# Deploy Commands
# ============================================================================

def deploy_cmd(platform: str, clean: bool = False) -> int:
    """Deploy framework to platform."""
    return deploy_framework(
        platform=platform,
        clean=clean,
        project_root=Path.cwd()
    )


# ============================================================================
# Docs Commands
# ============================================================================

def docs_generate_cmd(overwrite: bool = False) -> int:
    """Generate documentation."""
    return generate_docs(
        vibey_dir=Path.cwd() / ".vibey",  # This expects .vibey/ path
        overwrite=overwrite,
        quiet=False
    )


# ============================================================================
# Config Commands
# ============================================================================

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
    config_path = Path.cwd() / ".vibey" / "config" / "project.yaml"
    return update_config_value(
        config_path=config_path,
        key_path=key,
        value=value,
        create_missing=False,
        verbose=True
    )


# ============================================================================
# Migration Commands
# ============================================================================

def migrate_to_roadmap_cmd() -> int:
    """Migrate legacy sprint files to roadmap."""
    return migrate_to_roadmap(
        root_dir=Path.cwd() / ".vibey",  # Migration expects .vibey/ path
        dry_run=False,
        backup=True
    )


def migrate_to_hierarchical_cmd() -> int:
    """Migrate flat structure to hierarchical."""
    return migrate_to_hierarchical(
        root_dir=Path.cwd() / ".vibey",  # Migration expects .vibey/ path
        dry_run=False,
        backup=True
    )


def migrate_embedded_tasks_cmd() -> int:
    """Migrate embedded tasks to separate files."""
    return migrate_embedded_tasks(
        root_dir=Path.cwd() / ".vibey",  # Migration expects .vibey/ path
        dry_run=False
    )


# ============================================================================
# Audit Trail Commands
# ============================================================================

def audit_log_cmd(limit: int = 20) -> int:
    """Show recent audit trail entries."""
    from vibey.operations.roadmap.audit_trail import AuditTrailManager
    from datetime import datetime

    manager = AuditTrailManager(Path.cwd())
    entries = manager.get_recent_changes(limit=limit)

    if not entries:
        print("No audit trail entries found.")
        return 0

    print(f"\n📋 Recent Audit Trail Entries (last {limit})")
    print("=" * 80)

    for entry in entries:
        timestamp = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{timestamp} - {entry.object_type.upper()}: {entry.object_id}")
        print(f"  Field: {entry.field}")
        print(f"  Change: {entry.old_value} → {entry.new_value}")
        print(f"  By: {entry.changed_by} ({entry.source})")
        print(f"  Reason: {entry.reason}")
        if entry.commit:
            print(f"  Commit: {entry.commit}")

    print("\n" + "=" * 80)
    print(f"Total entries shown: {len(entries)}\n")
    return 0


def audit_show_cmd(object_id: str) -> int:
    """Show change history for a specific object."""
    from vibey.operations.roadmap.audit_trail import AuditTrailManager
    from datetime import datetime

    manager = AuditTrailManager(Path.cwd())
    entries = manager.get_object_history(object_id)

    if not entries:
        print(f"No audit trail entries found for object '{object_id}'.")
        return 0

    print(f"\n📋 Audit Trail for {object_id}")
    print("=" * 80)

    for entry in entries:
        timestamp = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{timestamp}")
        print(f"  Field: {entry.field}")
        print(f"  Change: {entry.old_value} → {entry.new_value}")
        print(f"  By: {entry.changed_by} ({entry.source})")
        print(f"  Reason: {entry.reason}")
        if entry.commit:
            print(f"  Commit: {entry.commit}")

    print("\n" + "=" * 80)
    print(f"Total changes: {len(entries)}\n")
    return 0


def audit_suspicious_cmd() -> int:
    """Detect suspicious changes in audit trail."""
    from vibey.operations.roadmap.audit_trail import AuditTrailManager
    from datetime import datetime

    manager = AuditTrailManager(Path.cwd())
    suspicious = manager.detect_suspicious_changes()

    if not suspicious:
        print("\n✅ No suspicious changes detected in audit trail.\n")
        return 0

    print(f"\n⚠️  Suspicious Changes Detected: {len(suspicious)}")
    print("=" * 80)

    for entry, reason in suspicious:
        timestamp = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n⚠️  {reason}")
        print(f"  Object: {entry.object_type.upper()} {entry.object_id}")
        print(f"  Field: {entry.field}")
        print(f"  Change: {entry.old_value} → {entry.new_value}")
        print(f"  When: {timestamp}")
        print(f"  By: {entry.changed_by} ({entry.source})")
        print(f"  Reason: {entry.reason}")
        if entry.commit:
            print(f"  Commit: {entry.commit}")

    print("\n" + "=" * 80)
    print(f"Total suspicious changes: {len(suspicious)}\n")
    return 1  # Return error code to indicate issues found


def audit_report_cmd(
    object_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> int:
    """Generate detailed audit report."""
    from vibey.operations.roadmap.audit_trail import AuditTrailManager
    from datetime import datetime

    manager = AuditTrailManager(Path.cwd())

    # Parse dates if provided
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            print(f"❌ Invalid start date format: {start_date}")
            print("   Expected format: YYYY-MM-DD")
            return 1

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            print(f"❌ Invalid end date format: {end_date}")
            print("   Expected format: YYYY-MM-DD")
            return 1

    # Generate report
    report = manager.generate_report(
        object_id=object_id,
        start_date=start_dt,
        end_date=end_dt
    )

    print(report)
    return 0


# ============================================================================
# Validation Commands
# ============================================================================

def validate_docs_cmd(verbose: bool = False) -> int:
    """Validate documentation organization in roadmap."""
    from vibey.operations.validate.doc_organization import DocOrganizationValidator

    roadmap_dir = Path.cwd() / '.vibey' / 'roadmap'
    validator = DocOrganizationValidator(roadmap_dir, verbose)
    report = validator.validate()

    # Print summary
    print("\n" + "=" * 70)
    print("DOCUMENTATION ORGANIZATION VALIDATION")
    print("=" * 70)
    print(f"Tracks checked: {report.tracks_checked}")
    print(f"Sprints checked: {report.sprints_checked}")

    if report.warnings:
        print(f"\n⚠ Warnings: {len(report.warnings)}")
        for path, warning in report.warnings[:10]:
            print(f"  {path}")
            print(f"    {warning}")
        if len(report.warnings) > 10:
            print(f"  ... and {len(report.warnings) - 10} more warnings")

    if report.issues:
        print(f"\n✗ Issues: {len(report.issues)}")
        for path, issue in report.issues[:20]:
            print(f"  {path}")
            print(f"    {issue}")
        if len(report.issues) > 20:
            print(f"  ... and {len(report.issues) - 20} more issues")

    print("\n" + "=" * 70)
    if report.is_valid:
        print("✅ All documentation properly organized!")
    else:
        print(f"❌ {len(report.issues)} organization issues found")
    print("=" * 70)

    return 0 if report.is_valid else 1


def validate_assets_cmd(asset_type: str = 'all', verbose: bool = False) -> int:
    """Validate asset frontmatter (agents, workflows, handoffs)."""
    from vibey.operations.validate.frontmatter import FrontmatterValidator

    root_dir = Path.cwd()
    validator = FrontmatterValidator(root_dir, verbose)

    if asset_type == 'all':
        report = validator.validate_all()
    else:
        report = validator.validate_assets(asset_type)

    # Print results by type
    types_validated = set(r.asset_type for r in report.results)
    for atype in sorted(types_validated):
        type_results = [r for r in report.results if r.asset_type == atype]
        valid = sum(1 for r in type_results if r.is_valid)
        invalid = sum(1 for r in type_results if not r.is_valid)
        print(f"\n{atype.capitalize()}:")
        print(f"  ✅ {valid} valid")
        if invalid > 0:
            print(f"  ❌ {invalid} invalid")

    # Show errors
    invalid_results = [r for r in report.results if not r.is_valid]
    if invalid_results:
        print(f"\n{'=' * 60}")
        print("VALIDATION ERRORS:")
        print('=' * 60)
        for result in invalid_results:
            print(f"\n{result.filepath}:")
            for error in result.errors:
                print(f"  - {error}")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"TOTAL: {report.valid_count} valid, {report.invalid_count} invalid")
    print('=' * 60)

    return 0 if report.is_valid else 1


def roadmap_sync_commits_cmd(dry_run: bool = False) -> int:
    """Scan git history and link commits to tasks based on commit messages."""
    from vibey.operations.git.commit_evidence import sync_commits_from_git
    from vibey.operations.roadmap import add_commit_to_task

    root_dir = Path.cwd()

    print("Scanning git history for task references...")

    found_commits = sync_commits_from_git(root_dir, dry_run=dry_run)

    if not found_commits:
        print("No commits with task references found.")
        return 0

    print(f"\nFound {sum(len(commits) for commits in found_commits.values())} commits referencing {len(found_commits)} tasks:")
    print()

    linked_count = 0
    for task_id, commits in sorted(found_commits.items()):
        print(f"  {task_id}: {len(commits)} commit(s)")
        for sha in commits[:3]:  # Show first 3
            print(f"    - {sha[:8]}")
        if len(commits) > 3:
            print(f"    ... and {len(commits) - 3} more")

        if not dry_run:
            # Link each commit
            for sha in commits:
                try:
                    result = add_commit_to_task(
                        task_id=task_id,
                        commit_sha=sha,
                        vibey_path=root_dir / ".vibey",
                        auto_detect=False
                    )
                    if result == 0:
                        linked_count += 1
                except Exception:
                    pass  # Skip errors silently

    if dry_run:
        print(f"\n[DRY RUN] Would link {sum(len(c) for c in found_commits.values())} commits")
    else:
        print(f"\n✅ Linked {linked_count} commits to tasks")

    return 0


def roadmap_validate_commits_cmd() -> int:
    """Validate that all completed tasks have commit evidence."""
    from vibey.operations.git.commit_evidence import validate_all_tasks_have_commits

    root_dir = Path.cwd()

    print("Validating commit evidence for completed tasks...")
    print()

    issues = validate_all_tasks_have_commits(root_dir)

    if not issues:
        print("✅ All completed tasks have commit evidence")
        return 0

    print(f"❌ Found {len(issues)} completed task(s) without commits:")
    print()

    for result in issues:
        print(f"  • {result.task_id}")
        print(f"    {result.message}")
        print()

    print("To link commits:")
    print("  vibey roadmap add-commit <task-id> <sha>")
    print("  vibey roadmap sync-commits  # Auto-link from git history")

    return 1
