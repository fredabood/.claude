"""
Core roadmap commands.

Commands for managing roadmaps, tracks, sprints, and tasks - including
initialization, status, CRUD operations, and validation.
"""

from pathlib import Path
from typing import Optional


def roadmap_init_cmd(name: str, version: str) -> int:
    """Initialize a new roadmap."""
    from vibey.cli.commands import roadmap_init_cmd as impl
    return impl(name=name, version=version)


def roadmap_status_cmd(track: Optional[str] = None, sprint: Optional[str] = None) -> int:
    """Show roadmap status."""
    from vibey.cli.commands import roadmap_status_cmd as impl
    return impl(track=track, sprint=sprint)


def roadmap_sync_cmd(verbose: bool = False) -> int:
    """Sync status from individual files to main roadmap."""
    from vibey.cli.commands import roadmap_sync_cmd as impl
    return impl(verbose=verbose)


def roadmap_show_cmd(item_id: str) -> int:
    """Show details for an item."""
    from vibey.cli.commands import roadmap_show_cmd as impl
    return impl(item_id=item_id)


def roadmap_start_cmd(item_id: str) -> int:
    """Start a task or sprint."""
    from vibey.cli.commands import roadmap_start_cmd as impl
    return impl(item_id=item_id)


def roadmap_complete_cmd(item_id: str, skip_commit_check: bool = False, force: bool = False) -> int:
    """Complete a task or sprint."""
    from vibey.cli.commands import roadmap_complete_cmd as impl
    return impl(item_id=item_id, skip_commit_check=skip_commit_check, force=force)


def roadmap_revert_cmd(item_id: str, target_status: str, skip_confirm: bool = False) -> int:
    """Revert an item to a previous status."""
    from vibey.cli.commands import roadmap_revert_cmd as impl
    return impl(item_id=item_id, target_status=target_status, skip_confirm=skip_confirm)


def roadmap_context_cmd(task_id: str) -> int:
    """Get context for a task."""
    from vibey.cli.commands import roadmap_context_cmd as impl
    return impl(task_id=task_id)


def roadmap_summarize_cmd(item_type: str, item_id: str) -> int:
    """Summarize a track, sprint, or task."""
    from vibey.cli.commands import roadmap_summarize_cmd as impl
    return impl(item_type=item_type, item_id=item_id)


def roadmap_list_cmd() -> int:
    """List roadmap items."""
    from vibey.cli.commands import roadmap_list_cmd as impl
    return impl()


def roadmap_validate_cmd() -> int:
    """Validate roadmap structure."""
    from vibey.cli.commands import roadmap_validate_cmd as impl
    return impl()


def roadmap_validate_fast_cmd(
    profile: str = "standard",
    incremental: bool = False,
    verbose: bool = False,
    benchmark: bool = False
) -> int:
    """Fast roadmap validation with caching."""
    from vibey.cli.commands import roadmap_validate_fast_cmd as impl
    return impl(profile=profile, incremental=incremental, verbose=verbose, benchmark=benchmark)


def roadmap_validate_advanced_cmd(verbose: bool = False, check: str = 'all') -> int:
    """Advanced roadmap validation."""
    from vibey.cli.commands import roadmap_validate_advanced_cmd as impl
    return impl(verbose=verbose, check=check)


def roadmap_repair_cmd(
    fix_type: str = "all",
    dry_run: bool = True,
    verbose: bool = False
) -> int:
    """Repair roadmap issues."""
    from vibey.cli.commands import roadmap_repair_cmd as impl
    return impl(fix_type=fix_type, dry_run=dry_run, verbose=verbose)


def roadmap_sync_docs_cmd(
    track_id: Optional[str] = None,
    sprint_id: Optional[str] = None,
    dry_run: bool = False,
) -> int:
    """Sync documentation for roadmap items."""
    from vibey.cli.commands import roadmap_sync_docs_cmd as impl
    return impl(track_id=track_id, sprint_id=sprint_id, dry_run=dry_run)


def roadmap_add_context_cmd(
    item_id: str,
    content: str,
    context_type: str = "note",
    source: Optional[str] = None,
) -> int:
    """Add context to an item."""
    from vibey.cli.commands import roadmap_add_context_cmd as impl
    return impl(item_id=item_id, content=content, context_type=context_type, source=source)


def roadmap_add_commit_cmd(task_id: str, commit_sha: Optional[str] = None, auto: bool = False) -> int:
    """Add commit evidence to a task."""
    from vibey.cli.commands import roadmap_add_commit_cmd as impl
    return impl(task_id=task_id, commit_sha=commit_sha, auto=auto)


def roadmap_sync_commits_cmd(dry_run: bool = False) -> int:
    """Sync commits from git history."""
    from vibey.cli.commands import roadmap_sync_commits_cmd as impl
    return impl(dry_run=dry_run)


def roadmap_validate_commits_cmd() -> int:
    """Validate commit evidence for completed tasks."""
    from vibey.cli.commands import roadmap_validate_commits_cmd as impl
    return impl()


# Create commands
def create_track_cmd(name: str, slug: str | None, description: str,
                     priority: str, start: bool) -> int:
    """Create a new track."""
    from vibey.cli.commands import create_track_cmd as impl
    return impl(name=name, slug=slug, description=description, priority=priority, start=start)


def create_sprint_cmd(track_id: str, name: str, goal: str,
                      description: str, priority: str, start: bool) -> int:
    """Create a new sprint."""
    from vibey.cli.commands import create_sprint_cmd as impl
    return impl(track_id=track_id, name=name, goal=goal,
                description=description, priority=priority, start=start)


def create_task_cmd(sprint_id: str, title: str, description: str,
                    task_type: str, priority: str, complexity: str) -> int:
    """Create a new task."""
    from vibey.cli.commands import create_task_cmd as impl
    return impl(sprint_id=sprint_id, title=title, description=description,
                task_type=task_type, priority=priority, complexity=complexity)


# Bulk operations
def bulk_complete_sprint_cmd(sprint_id: str, skip_confirm: bool = False) -> int:
    """Complete all tasks in a sprint."""
    from vibey.cli.commands import bulk_complete_sprint_cmd as impl
    return impl(sprint_id=sprint_id, skip_confirm=skip_confirm)


def reconcile_cmd(fix: bool = False, dry_run: bool = False, verbose: bool = False) -> int:
    """Reconcile roadmap state."""
    from vibey.cli.commands import reconcile_cmd as impl
    return impl(fix=fix, dry_run=dry_run, verbose=verbose)
