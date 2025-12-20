"""
Roadmap update operations.

Handles all write operations: completing tasks, progressing status, adding tracks/sprints, etc.
Supports both YAML and SQLite backends with automatic detection.

## Sprint 5 (unified-arch-5): Unified Architecture Migration

This module has been migrated to use the unified ticket architecture:

1. **Ticket-Based Status Transitions**: New helper functions provide clean interface:
   - `_transition_task_status()` - Task status changes via ticket model
   - `_transition_sprint_status()` - Sprint status changes via ticket model
   - `_transition_track_status()` - Track status changes via ticket model

   These functions:
   - Load entity as Pydantic ticket model
   - Validate via `can_transition_to()` (criteria-based)
   - Apply change via immutable `start()`/`complete()` methods
   - Save via v2 yaml_dumper functions

2. **TransitionBlockedError**: New exception type for blocked transitions,
   providing structured access to blocking reasons.

3. **Dual Path (Transition Period)**: Main functions (complete_task, start_task,
   start_sprint, complete_sprint, complete_track) still use legacy models for
   additional operations (progress updates, audit logging, activity logging).
   The ticket-based helpers can be used directly for pure status transitions.

4. **Immutable Update Pattern**: Ticket models use immutable patterns -
   `start()` and `complete()` return new instances rather than mutating.

## Previous Architecture (sqlite-backend sprints 6-9)

- Criteria-based validation via `can_transition_to()`
- Ticket model loaders (`load_task_ticket()`, etc.)
- Smart accessor pattern for computed vs stored progress
- Dual YAML/SQLite backend support
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Tuple

from vibey.roadmap.models import (
    Roadmap, Track, Sprint, Task,
    Status, TaskStatus, ActivityType,
    DependencyType,
)
from vibey.roadmap.serialization import (
    load_roadmap, load_track, load_sprint, load_task, load_tasks,
    save_roadmap, save_track, save_sprint, save_task, save_tasks,
)
from vibey.cli.roadmap_lib.filesystem import FileSystemManager
from vibey.cli.roadmap_lib.activity import ActivityLogger
from vibey.cli.roadmap_lib.status import StatusManager
from vibey.cli.roadmap_lib.blockers import BlockerComputer
from vibey.operations.roadmap.audit_trail import log_status_change, log_command_change

# Import ticket models and loaders for criteria-based validation
from vibey.roadmap.models.ticket import TicketStatus
from vibey.operations.roadmap.query import (
    load_task_ticket,
    load_sprint_ticket,
    load_track_ticket,
)

# Note: Ticket save functions are now in transitions.py module
# The yaml_dumper functions are imported there for centralized use


def _use_sqlite_backend(root_dir: Path) -> bool:
    """
    Determine whether to use SQLite backend for updates.

    Uses SQLite if:
    1. Database file exists at .vibey/roadmap.db
    2. Database has valid schema (can query database_state)

    Args:
        root_dir: Root directory containing .vibey/

    Returns:
        True if SQLite backend should be used, False for YAML-only
    """
    db_path = root_dir / ".vibey" / "roadmap.db"
    if not db_path.exists():
        return False

    try:
        from vibey.roadmap.database import get_connection
        conn = get_connection(db_path=db_path)
        row = conn.execute("SELECT schema_version FROM database_state WHERE id = 1").fetchone()
        return row is not None
    except Exception:
        return False


def _mark_db_dirty(root_dir: Path) -> None:
    """Mark the database as dirty (has uncommitted changes)."""
    if not _use_sqlite_backend(root_dir):
        return
    try:
        from vibey.roadmap.database import get_connection
        db_path = root_dir / ".vibey" / "roadmap.db"
        conn = get_connection(db_path=db_path)
        conn.execute("UPDATE database_state SET is_dirty = 1 WHERE id = 1")
        conn.commit()
    except Exception:
        pass  # Silently ignore DB errors for dirty flag


def _sync_task_to_db(task: Task, root_dir: Path) -> None:
    """Sync task changes to SQLite database if backend is enabled."""
    if not _use_sqlite_backend(root_dir):
        return
    try:
        from vibey.roadmap.database.crud import update_task
        update_task(
            task.id,  # First positional arg is 'id'
            status=task.status.value if hasattr(task.status, 'value') else str(task.status),
            started=task.started,
            completed=task.completed,
            blocked=task.blocked,
            assigned_agent=task.assigned_agent,
        )
        _mark_db_dirty(root_dir)
    except Exception as e:
        print(f"  ⚠️  Failed to sync task to database: {e}")


def _sync_sprint_to_db(sprint: Sprint, root_dir: Path) -> None:
    """Sync sprint changes to SQLite database if backend is enabled."""
    if not _use_sqlite_backend(root_dir):
        return
    try:
        from vibey.roadmap.database.crud import update_sprint
        update_sprint(
            sprint.id,  # First positional arg is 'id'
            status=sprint.status.value if hasattr(sprint.status, 'value') else str(sprint.status),
            started=sprint.started,
            completed=sprint.completed,
            blocked=sprint.blocked,
            production_ready_at=sprint.production_ready_at,
            deployed_at=sprint.deployed_at,
        )
        _mark_db_dirty(root_dir)
    except Exception as e:
        print(f"  ⚠️  Failed to sync sprint to database: {e}")


def _sync_track_to_db(track: Track, root_dir: Path) -> None:
    """Sync track changes to SQLite database if backend is enabled."""
    if not _use_sqlite_backend(root_dir):
        return
    try:
        from vibey.roadmap.database.crud import update_track
        update_track(
            track.id,  # First positional arg is 'id'
            status=track.status.value if hasattr(track.status, 'value') else str(track.status),
            started=track.started,
            completed=track.completed,
            blocked=track.blocked,
        )
        _mark_db_dirty(root_dir)
    except Exception as e:
        print(f"  ⚠️  Failed to sync track to database: {e}")


def _sync_roadmap_to_db(roadmap: Roadmap, root_dir: Path) -> None:
    """Sync roadmap changes to SQLite database if backend is enabled."""
    if not _use_sqlite_backend(root_dir):
        return
    try:
        from vibey.roadmap.database.crud import update_roadmap
        update_roadmap(
            roadmap.id,  # First positional arg is 'id'
            status=roadmap.status.value if hasattr(roadmap.status, 'value') else str(roadmap.status),
            started=roadmap.started,
            completed=roadmap.completed,
            blocked=roadmap.blocked,
        )
        _mark_db_dirty(root_dir)
    except Exception as e:
        print(f"  ⚠️  Failed to sync roadmap to database: {e}")

# Import CLI change tracker for pre-commit hook compatibility
try:
    from vibey.operations.git.cli_change_tracker import record_cli_change
    CLI_CHANGE_TRACKER_AVAILABLE = True
except ImportError:
    CLI_CHANGE_TRACKER_AVAILABLE = False

def _record_cli_changes(file_path: Path, root_dir: Path) -> None:
    """Record that a file was modified by CLI."""
    if CLI_CHANGE_TRACKER_AVAILABLE:
        try:
            # If it's a directory (tasks are in hierarchical structure), find all task.yaml files
            if file_path.is_dir():
                for task_yaml in file_path.rglob("task.yaml"):
                    rel_path = str(task_yaml.relative_to(root_dir))
                    record_cli_change(rel_path, root_dir)
            else:
                # It's a file, record it directly
                rel_path = str(file_path.relative_to(root_dir))
                record_cli_change(rel_path, root_dir)
        except ValueError:
            pass  # File not under root_dir

# Import sync hooks for automatic documentation synchronization
try:
    import sys
    from pathlib import Path as _Path
    _framework_root = _Path(__file__).parent.parent.parent.parent
    if str(_framework_root) not in sys.path:
        sys.path.insert(0, str(_framework_root))
    from vibey.operations.docs.sync_hooks import trigger_on_task_complete, trigger_on_sprint_complete, trigger_on_track_complete
    SYNC_HOOKS_AVAILABLE = True
except ImportError:
    SYNC_HOOKS_AVAILABLE = False

# Import post-mortem auto-generation hook
try:
    from vibey.operations.context.post_mortem import auto_generate_on_complete as generate_post_mortem_on_complete
    POST_MORTEM_AVAILABLE = True
except ImportError:
    POST_MORTEM_AVAILABLE = False


# ============================================================================
# Centralized Status Transitions (Sprint 5 - Task 003)
# ============================================================================
# Import from the centralized transitions module for consistency.
# The transitions module is the single source of truth for status transitions.
# ============================================================================

from vibey.operations.roadmap.transitions import (
    transition_task,
    transition_sprint,
    transition_track,
)


def _transition_task_status(
    task_id: str,
    target_status: TicketStatus,
    root_dir: Path,
    changed_by: str = "system",
) -> Tuple[bool, str]:
    """
    Transition a task to a new status using centralized transitions module.

    This is a convenience wrapper that returns (success, message) tuple
    and records CLI changes.

    Args:
        task_id: ID of the task to transition
        target_status: Target TicketStatus
        root_dir: Root directory containing .vibey/
        changed_by: Name of user/agent making the change

    Returns:
        Tuple of (success, message)

    Raises:
        TransitionBlockedError: If transition is blocked by criteria
    """
    fs = FileSystemManager(root_dir)
    updated_ticket = transition_task(task_id, target_status, root_dir, save=True)

    # Record CLI changes for pre-commit hook
    task_path = fs.get_task_path(task_id)
    if not task_path:
        task_path = fs.roadmap_root / "tasks" / f"{task_id}.yaml"
    if task_path and task_path.exists():
        _record_cli_changes(task_path, root_dir)

    return True, f"Task transitioned to {target_status.value}"


def _transition_sprint_status(
    sprint_id: str,
    target_status: TicketStatus,
    root_dir: Path,
    changed_by: str = "system",
) -> Tuple[bool, str]:
    """
    Transition a sprint to a new status using centralized transitions module.

    Args:
        sprint_id: ID of the sprint to transition
        target_status: Target TicketStatus
        root_dir: Root directory containing .vibey/
        changed_by: Name of user/agent making the change

    Returns:
        Tuple of (success, message)

    Raises:
        TransitionBlockedError: If transition is blocked by criteria
    """
    fs = FileSystemManager(root_dir)
    updated_ticket = transition_sprint(sprint_id, target_status, root_dir, save=True)

    # Record CLI changes for pre-commit hook
    sprint_path = fs.get_sprint_path(sprint_id)
    if sprint_path and sprint_path.exists():
        _record_cli_changes(sprint_path, root_dir)

    return True, f"Sprint transitioned to {target_status.value}"


def _transition_track_status(
    track_id: str,
    target_status: TicketStatus,
    root_dir: Path,
    changed_by: str = "system",
) -> Tuple[bool, str]:
    """
    Transition a track to a new status using centralized transitions module.

    Args:
        track_id: ID of the track to transition
        target_status: Target TicketStatus
        root_dir: Root directory containing .vibey/
        changed_by: Name of user/agent making the change

    Returns:
        Tuple of (success, message)

    Raises:
        TransitionBlockedError: If transition is blocked by criteria
    """
    fs = FileSystemManager(root_dir)
    updated_ticket = transition_track(track_id, target_status, root_dir, save=True)

    # Record CLI changes for pre-commit hook
    track_path = fs.get_track_path(track_id)
    if track_path and track_path.exists():
        _record_cli_changes(track_path, root_dir)

    return True, f"Track transitioned to {target_status.value}"


def complete_task(
    root_dir: Path,
    task_id: str,
    completed_by: str = "system",
    skip_commit_check: bool = False
) -> int:
    """
    Mark a task as completed.

    Uses criteria-based validation via can_transition_to() to check if task
    can be completed. This enforces criteria and blocking dependencies.

    Args:
        root_dir: Root directory containing .vibey/
        task_id: ID of the task to complete (format: sprint-id-task-nnn)
        completed_by: Name of the user completing the task
        skip_commit_check: If True, skip commit evidence validation

    Returns:
        Exit code: 0 for success, 1 for error
    """
    fs = FileSystemManager(root_dir)
    roadmap_root = root_dir / ".vibey" / "roadmap"

    # Check if task_id is a ULID (26 alphanumeric chars starting with 01)
    is_ulid = len(task_id) == 26 and task_id.isalnum() and task_id.startswith('01')

    if is_ulid:
        # For ULIDs, load task directly from tasks/ directory
        task_path = roadmap_root / "tasks" / f"{task_id}.yaml"
        if not task_path.exists():
            print(f"❌ Task file not found: {task_path}")
            return 1
        # Get sprint_id from task YAML (v1) or parent_ref (v2)
        import yaml
        with open(task_path) as f:
            task_data = yaml.safe_load(f)
        # Try v1 format first (sprint_id), then v2 format (parent_ref)
        sprint_id = task_data.get('task', {}).get('sprint_id')
        if not sprint_id:
            sprint_id = task_data.get('task', {}).get('parent_ref')
        if not sprint_id:
            # For v2 format tasks without dependencies, sprint_id is optional
            # The task can still be completed via the unified ticket path below
            sprint_id = None
        tasks_path = task_path  # For ULID, the task_path is the file itself
    else:
        # Legacy format: extract sprint ID from task ID (everything before -task-)
        if '-task-' not in task_id:
            print(f"❌ Invalid task ID format: {task_id}")
            print("  Expected: <sprint-id>-task-<num> or 26-char ULID")
            return 1
        sprint_id = task_id.split('-task-')[0]
        tasks_path = fs.get_tasks_path(sprint_id)
        if not tasks_path.exists():
            print(f"❌ Tasks file not found for sprint '{sprint_id}'")
            return 1

    # ==========================================================================
    # CRITERIA-BASED VALIDATION (Sprint 9 - Smart Accessor Pattern)
    # Load task as ticket model and validate transition via can_transition_to()
    # ==========================================================================
    try:
        task_ticket = load_task_ticket(root_dir, task_id)
        can_complete, blockers = task_ticket.can_transition_to(TicketStatus.COMPLETED)

        if not can_complete:
            print(f"❌ Cannot complete task: criteria not met")
            for blocker in blockers:
                print(f"   • {blocker}")
            return 1
    except Exception as e:
        # Ticket model validation not available, continue with legacy checks
        pass

    # ==========================================================================
    # LEGACY VALIDATION (kept for backward compatibility)
    # These checks will be consolidated into criteria in future sprints
    # ==========================================================================

    # Load task(s) based on ID format
    if is_ulid:
        # For ULID, check the format version and load appropriately
        format_version = task_data.get('task', {}).get('format_version', 'v1')
        if format_version == 'v2':
            # v2 format: use unified ticket loader, then convert to legacy Task
            from vibey.roadmap.serialization.yaml_loader import load_task_ticket as yaml_load_task_ticket
            task_ticket = yaml_load_task_ticket(tasks_path)
            # Convert TaskTicket to legacy Task for downstream compatibility
            from vibey.roadmap.models.task import Task, TaskStatus as LegacyTaskStatus, TaskType, TaskMetadata
            task = Task(
                id=task_ticket.id,
                sprint_id=task_ticket.sprint_id or '',
                track_id=task_ticket.track_id or '',
                roadmap_id=task_ticket.roadmap_id or 'vibey-framework-v2',
                task_type=TaskType.DEVELOPMENT,
                title=task_ticket.name,
                description=task_ticket.description or '',
                status=LegacyTaskStatus(task_ticket.status.value),
                priority=task_ticket.priority.value if hasattr(task_ticket.priority, 'value') else 'medium',
                created=task_ticket.created_at,
                started=task_ticket.started_at,
                completed=task_ticket.completed_at,
                metadata=TaskMetadata(
                    last_updated=task_ticket.updated_at,
                ),
                depends_on=[],
                blocked_by=[],
                depended_on_by=[],
                deliverables=[],
            )
        else:
            # v1 format: use legacy loader
            task = load_task(tasks_path)  # tasks_path is the individual task file for ULIDs
    else:
        # For legacy format, load all tasks from sprint and find matching one
        tasks = load_tasks(tasks_path)
        task = None
        for t in tasks:
            if t.id == task_id:
                task = t
                break

    if not task:
        print(f"❌ Task '{task_id}' not found")
        return 1

    # Check commit evidence before completion (unless skipped)
    if not skip_commit_check:
        try:
            from vibey.operations.git.commit_evidence import check_commit_evidence
            evidence_result = check_commit_evidence(task_id, root_dir)

            if not evidence_result.can_complete:
                print(f"❌ Cannot complete task: {evidence_result.message}")
                return 1

            if evidence_result.message and not evidence_result.has_evidence:
                # Advisory warning
                print(evidence_result.message)
        except ImportError:
            pass  # Module not available, skip check

    # Enforce standards before completion
    from .standards_enforcement import enforce_standards, print_enforcement_results, get_failure_summary

    enforcement_result = enforce_standards(task_id, root_dir, operation="complete")
    print_enforcement_results(enforcement_result, task_id, verbose=False)

    if not enforcement_result.can_proceed:
        failure_summary = get_failure_summary(enforcement_result)
        print(f"\n❌ Cannot complete task: {failure_summary}")
        print(f"   Use 'vibey roadmap override-standard' to override blocking standards")
        return 1

    # Show warnings if any
    if enforcement_result.warnings:
        print(f"\n⚠️  Task has warnings but will proceed with completion")

    # Capture old status for audit trail
    old_status = task.status.value if hasattr(task.status, 'value') else str(task.status)

    # Update task
    task.status = TaskStatus.COMPLETED
    task.completed = datetime.now(timezone.utc)
    task.metadata.last_modified = datetime.now(timezone.utc)
    task.metadata.last_modified_by = completed_by

    # Log status change to audit trail
    log_status_change(
        root_dir=root_dir,
        object_type="task",
        object_id=task_id,
        old_status=old_status,
        new_status="completed",
        reason=f"Task completed via CLI by {completed_by}",
        changed_by=completed_by
    )

    # Save only the modified task (not all sibling tasks)
    save_task(task, tasks_path)
    _record_cli_changes(tasks_path, root_dir)
    _sync_task_to_db(task, root_dir)
    print(f"✅ Task '{task.title}' marked as completed")

    # Update dependency caches for all dependents
    for dependent_id in task.depended_on_by:
        if _update_dependent_cache(fs, dependent_id, task_id, "completed"):
            print(f"  ✓ Updated dependent: {dependent_id}")
        else:
            print(f"  ⚠️  Failed to update dependent: {dependent_id}")

    # Update sprint progress (if sprint_id is known)
    if sprint_id:
        _update_sprint_progress(fs, sprint_id)

    # Log activity
    logger = ActivityLogger(root_dir)
    logger.log_activity(
        ActivityType.TASK_COMPLETED,
        f"Task '{task.title}' completed",
        {"task_id": task_id, "sprint_id": sprint_id or "unknown"}
    )

    # Trigger automatic documentation sync if enabled
    if SYNC_HOOKS_AVAILABLE:
        trigger_on_task_complete(task_id, enabled=True, verbose=False)

    # Generate post-mortem for completed task
    if POST_MORTEM_AVAILABLE:
        post_mortem_path = generate_post_mortem_on_complete(task_id)
        if post_mortem_path:
            print(f"  Post-mortem saved: {post_mortem_path.name}")

    return 0


def start_task(
    root_dir: Path,
    task_id: str,
    started_by: str = "system"
) -> int:
    """
    Mark a task as in progress.

    Uses criteria-based validation via can_transition_to() to check if task
    can be started. This enforces blocking dependencies and criteria.

    Args:
        root_dir: Root directory containing .vibey/
        task_id: ID of the task to start (format: sprint-id-task-nnn or 26-char ULID)
        started_by: Name of the user starting the task

    Returns:
        Exit code: 0 for success, 1 for error
    """
    import yaml as yaml_mod
    fs = FileSystemManager(root_dir)
    roadmap_root = root_dir / ".vibey" / "roadmap"

    # Check if task_id is a ULID (26 alphanumeric chars starting with 01)
    is_ulid = len(task_id) == 26 and task_id.isalnum() and task_id.startswith('01')

    if is_ulid:
        # For ULIDs, load task directly from tasks/ directory
        task_path = roadmap_root / "tasks" / f"{task_id}.yaml"
        if not task_path.exists():
            print(f"❌ Task file not found: {task_path}")
            return 1
        # Get sprint_id from task YAML (v1) or parent_ref (v2)
        with open(task_path) as f:
            task_data = yaml_mod.safe_load(f)
        # Try v1 format first (sprint_id), then v2 format (parent_ref)
        sprint_id = task_data.get('task', {}).get('sprint_id')
        if not sprint_id:
            sprint_id = task_data.get('task', {}).get('parent_ref')
        if not sprint_id:
            # For v2 format tasks without dependencies, sprint_id is optional
            sprint_id = None
        tasks_path = task_path  # For ULID, the task_path is the file itself
    else:
        # Legacy format: extract sprint ID from task ID (everything before -task-)
        if '-task-' not in task_id:
            print(f"❌ Invalid task ID format: {task_id}")
            print("  Expected: <sprint-id>-task-<num> or 26-char ULID")
            return 1
        sprint_id = task_id.split('-task-')[0]
        tasks_path = fs.get_tasks_path(sprint_id)
        if not tasks_path.exists():
            print(f"❌ Tasks file not found for sprint '{sprint_id}'")
            return 1

    # ==========================================================================
    # CRITERIA-BASED VALIDATION (Sprint 9 - Smart Accessor Pattern)
    # Load task as ticket model and validate transition via can_transition_to()
    # ==========================================================================
    try:
        task_ticket = load_task_ticket(root_dir, task_id)
        can_start, blockers = task_ticket.can_transition_to(TicketStatus.IN_PROGRESS)

        if not can_start:
            print(f"❌ Cannot start task: criteria not met")
            for blocker in blockers:
                print(f"   • {blocker}")
            return 1
    except Exception as e:
        # Ticket model validation not available, continue with legacy checks
        pass

    # Load task(s) based on ID format
    if is_ulid:
        # For ULID, check the format version and load appropriately
        format_version = task_data.get('task', {}).get('format_version', 'v1')
        if format_version == 'v2':
            # v2 format: use unified ticket loader, then convert to legacy Task
            from vibey.roadmap.serialization.yaml_loader import load_task_ticket as yaml_load_task_ticket
            task_ticket = yaml_load_task_ticket(tasks_path)
            # Convert TaskTicket to legacy Task for downstream compatibility
            from vibey.roadmap.models.task import Task, TaskStatus as LegacyTaskStatus, TaskType, TaskMetadata
            task = Task(
                id=task_ticket.id,
                sprint_id=task_ticket.sprint_id or '',
                track_id=task_ticket.track_id or '',
                roadmap_id=task_ticket.roadmap_id or 'vibey-framework-v2',
                task_type=TaskType.DEVELOPMENT,
                title=task_ticket.name,
                description=task_ticket.description or '',
                status=LegacyTaskStatus(task_ticket.status.value),
                priority=task_ticket.priority.value if hasattr(task_ticket.priority, 'value') else 'medium',
                created=task_ticket.created_at,
                started=task_ticket.started_at,
                completed=task_ticket.completed_at,
                metadata=TaskMetadata(
                    last_updated=task_ticket.updated_at,
                ),
                depends_on=[],
                blocked_by=[],
                depended_on_by=[],
                deliverables=[],
            )
        else:
            # v1 format: use legacy loader
            task = load_task(tasks_path)  # tasks_path is the individual task file for ULIDs
    else:
        # For legacy format, load all tasks from sprint and find matching one
        tasks = load_tasks(tasks_path)
        task = None
        for t in tasks:
            if t.id == task_id:
                task = t
                break

    if not task:
        print(f"❌ Task '{task_id}' not found")
        return 1

    # Capture old status for audit trail
    old_status = task.status.value if hasattr(task.status, 'value') else str(task.status)

    # Update task
    task.status = TaskStatus.IN_PROGRESS
    task.started = datetime.now(timezone.utc)
    task.metadata.last_modified = datetime.now(timezone.utc)
    task.metadata.last_modified_by = started_by

    # Log status change to audit trail (V1 format - backward compat)
    log_status_change(
        root_dir=root_dir,
        object_type="task",
        object_id=task_id,
        old_status=old_status,
        new_status="in_progress",
        reason=f"Task started via CLI by {started_by}",
        changed_by=started_by
    )

    # Save only the modified task (not all sibling tasks)
    save_task(task, tasks_path)

    # Log command-level change (V2 format) - includes file hash for verification
    task_path = fs.get_task_path(task_id)
    log_command_change(
        root_dir=root_dir,
        command=f"vibey roadmap start {task_id}",
        object_type="task",
        object_id=task_id,
        changes=[
            ("status", old_status, "in_progress"),
            ("started", None, task.started.isoformat() if task.started else None),
        ],
        file_path=task_path,
        reason=f"Task started via CLI by {started_by}",
        changed_by=started_by,
    )
    _record_cli_changes(tasks_path, root_dir)
    _sync_task_to_db(task, root_dir)
    print(f"✅ Task '{task.title}' marked as in progress")

    # Update dependency caches for all dependents
    for dependent_id in task.depended_on_by:
        if _update_dependent_cache(fs, dependent_id, task_id, "in_progress"):
            print(f"  ✓ Updated dependent: {dependent_id}")
        else:
            print(f"  ⚠️  Failed to update dependent: {dependent_id}")

    # Update sprint progress (if sprint_id is known)
    if sprint_id:
        _update_sprint_progress(fs, sprint_id)

    # Log activity
    logger = ActivityLogger(root_dir)
    logger.log_activity(
        ActivityType.TASK_STARTED,
        f"Task '{task.title}' started",
        {"task_id": task_id, "sprint_id": sprint_id or "unknown"}
    )

    return 0


def assign_task(
    root_dir: Path,
    task_id: str,
    agent: str,
    assigned_by: str = "system"
) -> int:
    """
    Assign a task to an agent.

    Args:
        root_dir: Root directory containing .vibey/
        task_id: ID of the task to assign
        agent: Name of the agent to assign the task to
        assigned_by: Name of the user making the assignment

    Returns:
        Exit code: 0 for success, 1 for error
    """
    fs = FileSystemManager(root_dir)

    # Extract sprint ID from task ID
    parts = task_id.split('-')
    if len(parts) < 3:
        print(f"❌ Invalid task ID format: {task_id}")
        return 1

    sprint_id = '-'.join(parts[:2])
    tasks_path = fs.get_tasks_path(sprint_id)

    if not tasks_path.exists():
        print(f"❌ Tasks file not found for sprint '{sprint_id}'")
        return 1

    # Load tasks
    tasks = load_tasks(tasks_path)

    # Find and update task
    task = None
    for t in tasks:
        if t.id == task_id:
            task = t
            break

    if not task:
        print(f"❌ Task '{task_id}' not found")
        return 1

    # Update task
    task.assigned_agent = agent
    task.metadata.last_modified = datetime.now(timezone.utc)
    task.metadata.last_modified_by = assigned_by

    # Save only the modified task (not all sibling tasks)
    save_task(task, tasks_path)
    _sync_task_to_db(task, root_dir)
    print(f"✅ Task '{task.title}' assigned to {agent}")

    # Log activity
    logger = ActivityLogger(root_dir)
    logger.log_activity(
        ActivityType.TASK_STARTED,
        f"Task '{task.title}' assigned to {agent}",
        {"task_id": task_id, "agent": agent}
    )

    return 0


def add_commit_to_task(
    root_dir: Path,
    task_id: str,
    sha: str,
    message: str,
    author: str,
    platform: str,
    submitted_at: Optional[int] = None,
    commit_date: Optional[datetime] = None,
) -> int:
    """
    Add a git commit to a task.

    Uses immutable update pattern - creates new commit object and appends to
    task's commits list.

    Args:
        root_dir: Root directory containing .vibey/
        task_id: ID of the task to add commit to
        sha: Git commit SHA (7-40 hex characters)
        message: Commit message
        author: Commit author
        platform: Platform used (e.g., "claude-code", "goose", "cursor")
        submitted_at: Unix timestamp when commit was submitted (defaults to now)
        commit_date: Git commit date (defaults to now)

    Returns:
        Exit code: 0 for success, 1 for error
    """
    from vibey.roadmap.models.task import GitCommit as LegacyGitCommit
    import time

    fs = FileSystemManager(root_dir)

    # Extract sprint ID from task ID
    if '-task-' not in task_id:
        print(f"❌ Invalid task ID format: {task_id}")
        return 1

    sprint_id = task_id.split('-task-')[0]
    tasks_path = fs.get_tasks_path(sprint_id)

    if not tasks_path.exists():
        print(f"❌ Tasks file not found for sprint '{sprint_id}'")
        return 1

    # Load tasks
    tasks = load_tasks(tasks_path)

    # Find task
    task = None
    for t in tasks:
        if t.id == task_id:
            task = t
            break

    if not task:
        print(f"❌ Task '{task_id}' not found")
        return 1

    # Create commit object with defaults
    now = datetime.now(timezone.utc)
    if submitted_at is None:
        submitted_at = int(time.time())
    if commit_date is None:
        commit_date = now

    # Validate SHA
    if not (7 <= len(sha) <= 40):
        print(f"❌ Invalid SHA length: {sha}")
        return 1
    try:
        int(sha, 16)
    except ValueError:
        print(f"❌ Invalid SHA format (must be hex): {sha}")
        return 1

    # Create new commit using immutable pattern
    new_commit = LegacyGitCommit(
        sha=sha,
        message=message,
        date=commit_date,
        author=author,
        platform=platform,
        submitted_at=submitted_at,
    )

    # Append to commits list (immutable: creates new list)
    task.commits = list(task.commits) + [new_commit]
    task.metadata.last_modified = now

    # Save only the modified task (not all sibling tasks)
    save_task(task, tasks_path)
    _record_cli_changes(tasks_path, root_dir)
    _sync_task_to_db(task, root_dir)
    print(f"✅ Commit {sha[:7]} added to task '{task.title}'")

    # Note: Activity logging for commits would require adding COMMIT_ADDED to ActivityType
    # For now, commit addition is tracked via the audit trail and task metadata

    return 0


def start_sprint(
    root_dir: Path,
    sprint_id: str,
    started_by: str = "system"
) -> int:
    """
    Start a sprint.

    Uses criteria-based validation via can_transition_to() to check if sprint
    can be started. This enforces blocking dependencies and criteria.

    Args:
        root_dir: Root directory containing .vibey/
        sprint_id: ID of the sprint to start
        started_by: Name of the user starting the sprint

    Returns:
        Exit code: 0 for success, 1 for error
    """
    fs = FileSystemManager(root_dir)
    sprint_path = fs.get_sprint_path(sprint_id)

    if not sprint_path.exists():
        print(f"❌ Sprint '{sprint_id}' not found")
        return 1

    # ==========================================================================
    # CRITERIA-BASED VALIDATION (Sprint 9 - Smart Accessor Pattern)
    # Load sprint as ticket model and validate transition via can_transition_to()
    # ==========================================================================
    try:
        sprint_ticket = load_sprint_ticket(root_dir, sprint_id)
        can_start, blockers = sprint_ticket.can_transition_to(TicketStatus.IN_PROGRESS)

        if not can_start:
            print(f"❌ Cannot start sprint: criteria not met")
            for blocker in blockers:
                print(f"   • {blocker}")
            return 1
    except Exception as e:
        # Ticket model validation not available, continue with legacy checks
        pass

    sprint = load_sprint(sprint_path)

    # Check current status - idempotent behavior
    if sprint.status == Status.IN_PROGRESS:
        print(f"ℹ️  Sprint already in progress")
        return 0  # Idempotent: already in desired state

    if sprint.status != Status.NOT_STARTED:
        print(f"❌ Cannot start sprint (current status: {sprint.status.value})")
        return 1

    # Capture old status for audit trail
    old_sprint_status = sprint.status.value

    # Update sprint
    sprint.status = Status.IN_PROGRESS
    sprint.started = datetime.now(timezone.utc)
    sprint.metadata.last_modified = datetime.now(timezone.utc)
    sprint.metadata.last_modified_by = started_by

    # Log status change to audit trail
    log_status_change(
        root_dir=root_dir,
        object_type="sprint",
        object_id=sprint_id,
        old_status=old_sprint_status,
        new_status="in_progress",
        reason=f"Sprint started via CLI by {started_by}",
        changed_by=started_by
    )

    # Save sprint
    save_sprint(sprint, sprint_path)
    _sync_sprint_to_db(sprint, root_dir)
    print(f"✅ Sprint '{sprint.name}' started")

    # Update track
    track_id = sprint_id.rsplit('-', 1)[0]
    track_path = fs.get_track_path(track_id)
    if track_path.exists():
        track = load_track(track_path)

        # If track not started, start it
        if track.status == Status.NOT_STARTED:
            old_track_status = track.status.value
            track.status = Status.IN_PROGRESS
            track.started = datetime.now(timezone.utc)

            # Log track status change to audit trail
            log_status_change(
                root_dir=root_dir,
                object_type="track",
                object_id=track_id,
                old_status=old_track_status,
                new_status="in_progress",
                reason=f"Track auto-started when sprint {sprint_id} started",
                changed_by=started_by
            )

            save_track(track, track_path)
            _sync_track_to_db(track, root_dir)
            print(f"✅ Track '{track.name}' started")

    # Update roadmap
    roadmap_path = fs.get_roadmap_path()
    if roadmap_path.exists():
        roadmap = load_roadmap(roadmap_path)

        # If roadmap not started, start it
        if roadmap.status == Status.NOT_STARTED:
            roadmap.status = Status.IN_PROGRESS
            save_roadmap(roadmap, roadmap_path)
            _sync_roadmap_to_db(roadmap, root_dir)
            print(f"✅ Roadmap '{roadmap.name}' started")

    # Log activity
    logger = ActivityLogger(root_dir)
    logger.log_activity(
        ActivityType.SPRINT_STARTED,
        f"Sprint '{sprint.name}' started",
        {"sprint_id": sprint_id}
    )

    return 0


def complete_sprint(
    root_dir: Path,
    sprint_id: str,
    completed_by: str = "system",
    force: bool = False
) -> int:
    """
    Mark a sprint as completed.

    Uses criteria-based validation via can_transition_to() to check if sprint
    can be completed. All child tasks must be completed (CompletableTarget criteria).

    Args:
        root_dir: Root directory containing .vibey/
        sprint_id: ID of the sprint to complete
        completed_by: Name of the user completing the sprint
        force: Force completion even with incomplete tasks (with warning)

    Returns:
        Exit code: 0 for success, 1 for error
    """
    import yaml

    fs = FileSystemManager(root_dir)
    sprint_path = fs.get_sprint_path(sprint_id)
    roadmap_root = root_dir / ".vibey" / "roadmap"

    if not sprint_path.exists():
        print(f"❌ Sprint '{sprint_id}' not found")
        return 1

    # ==========================================================================
    # TASK COMPLETION VALIDATION
    # Check if all tasks in the sprint are completed before allowing completion
    # ==========================================================================

    # Determine sprint ULID for task lookup
    is_ulid = len(sprint_id) == 26 and sprint_id.isalnum() and sprint_id.startswith('01')
    sprint_ulid = sprint_id

    if not is_ulid:
        # Load sprint to get its ULID
        with open(sprint_path) as f:
            sprint_data = yaml.safe_load(f)
        sprint_ulid = sprint_data.get('sprint', {}).get('id', sprint_id)

    # Find incomplete tasks for this sprint
    incomplete_tasks = []
    for task_file in (roadmap_root / "tasks").glob("*.yaml"):
        with open(task_file) as f:
            task_data = yaml.safe_load(f)
        task = task_data.get('task', {})
        if task.get('sprint_id') == sprint_ulid and task.get('status') != 'completed':
            incomplete_tasks.append({
                'id': task.get('id'),
                'title': task.get('title', 'Untitled'),
                'status': task.get('status', 'not_started'),
            })

    if incomplete_tasks and not force:
        print(f"❌ Cannot complete sprint: {len(incomplete_tasks)} task(s) incomplete")
        for task in incomplete_tasks:
            print(f"   • {task['title']} ({task['status']})")
        print(f"\n   Use --force to complete anyway.")
        return 1

    if incomplete_tasks and force:
        print(f"⚠️  Force completing sprint with {len(incomplete_tasks)} incomplete task(s):")
        for task in incomplete_tasks:
            print(f"   • {task['title']} ({task['status']})")
        print()

    # ==========================================================================
    # CRITERIA-BASED VALIDATION (Sprint 9 - Smart Accessor Pattern)
    # Load sprint as ticket model and validate transition via can_transition_to()
    # This automatically checks all child task criteria
    # ==========================================================================
    try:
        sprint_ticket = load_sprint_ticket(root_dir, sprint_id)
        can_complete, blockers = sprint_ticket.can_transition_to(TicketStatus.COMPLETED)

        if not can_complete and not force:
            print(f"❌ Cannot complete sprint: criteria not met")
            for blocker in blockers:
                print(f"   • {blocker}")
            print(f"\n   Use --force to complete anyway.")
            return 1
    except FileNotFoundError:
        # Ticket model files not available, continue with legacy checks
        pass
    except Exception as e:
        # Log error but continue with legacy checks
        print(f"⚠️  Criteria validation warning: {e}")

    # ==========================================================================
    # LEGACY VALIDATION (kept for backward compatibility)
    # ==========================================================================

    sprint = load_sprint(sprint_path)

    # Check if can progress to completed
    status_manager = StatusManager(root_dir)
    can_progress, reason = status_manager.can_progress_sprint(sprint, Status.COMPLETED)

    if not can_progress:
        print(f"❌ Cannot complete sprint: {reason}")
        return 1

    # Enforce standards before completion
    from .standards_enforcement import enforce_standards, print_enforcement_results, get_failure_summary

    enforcement_result = enforce_standards(sprint_id, root_dir, operation="complete")
    print_enforcement_results(enforcement_result, sprint_id, verbose=False)

    if not enforcement_result.can_proceed:
        failure_summary = get_failure_summary(enforcement_result)
        print(f"\n❌ Cannot complete sprint: {failure_summary}")
        print(f"   Use 'vibey roadmap override-standard' to override blocking standards")
        return 1

    # Show warnings if any
    if enforcement_result.warnings:
        print(f"\n⚠️  Sprint has warnings but will proceed with completion")

    # Capture old status for audit trail
    old_status = sprint.status.value

    # Update sprint
    sprint.status = Status.COMPLETED
    sprint.completed = datetime.now(timezone.utc)
    sprint.metadata.last_modified = datetime.now(timezone.utc)
    sprint.metadata.last_modified_by = completed_by

    # Log status change to audit trail
    log_status_change(
        root_dir=root_dir,
        object_type="sprint",
        object_id=sprint_id,
        old_status=old_status,
        new_status="completed",
        reason=f"Sprint completed via CLI by {completed_by}",
        changed_by=completed_by
    )

    # Save sprint
    save_sprint(sprint, sprint_path)
    _sync_sprint_to_db(sprint, root_dir)
    print(f"✅ Sprint '{sprint.name}' marked as completed")

    # Update dependency caches for all dependents
    for dependent_id in sprint.depended_on_by:
        if _update_dependent_cache(fs, dependent_id, sprint_id, "completed"):
            print(f"  ✓ Updated dependent: {dependent_id}")
        else:
            print(f"  ⚠️  Failed to update dependent: {dependent_id}")

    # Update track progress
    track_id = sprint_id.rsplit('-', 1)[0]
    _update_track_progress(fs, track_id)

    # Log activity
    logger = ActivityLogger(root_dir)
    logger.log_activity(
        ActivityType.SPRINT_COMPLETED,
        f"Sprint '{sprint.name}' completed",
        {"sprint_id": sprint_id}
    )

    # Trigger automatic documentation sync if enabled
    if SYNC_HOOKS_AVAILABLE:
        trigger_on_sprint_complete(sprint_id, enabled=True, verbose=False)

    return 0


def complete_track(
    root_dir: Path,
    track_id: str,
    completed_by: str = "system"
) -> int:
    """
    Mark a track as completed.

    Uses criteria-based validation via can_transition_to() to check if track
    can be completed. All child sprints must be completed (CompletableTarget criteria).

    Args:
        root_dir: Root directory containing .vibey/
        track_id: ID of the track to complete
        completed_by: Name of the user completing the track

    Returns:
        Exit code: 0 for success, 1 for error
    """
    fs = FileSystemManager(root_dir)
    track_path = fs.get_track_path(track_id)

    if not track_path.exists():
        print(f"❌ Track '{track_id}' not found")
        return 1

    # ==========================================================================
    # CRITERIA-BASED VALIDATION (Sprint 9 - Smart Accessor Pattern)
    # Load track as ticket model and validate transition via can_transition_to()
    # This automatically checks all child sprint criteria
    # ==========================================================================
    try:
        track_ticket = load_track_ticket(root_dir, track_id)
        can_complete, blockers = track_ticket.can_transition_to(TicketStatus.COMPLETED)

        if not can_complete:
            print(f"❌ Cannot complete track: criteria not met")
            for blocker in blockers:
                print(f"   • {blocker}")
            return 1
    except Exception as e:
        # Ticket model validation not available, continue with legacy checks
        pass

    track = load_track(track_path)

    # Check if can progress to completed
    status_manager = StatusManager(root_dir)
    can_progress, reason = status_manager.can_progress_track(track, Status.COMPLETED)

    if not can_progress:
        print(f"❌ Cannot complete track: {reason}")
        return 1

    # Capture old status for audit trail
    old_status = track.status.value

    # Update track
    track.status = Status.COMPLETED
    track.completed = datetime.now(timezone.utc)

    # Log status change to audit trail
    log_status_change(
        root_dir=root_dir,
        object_type="track",
        object_id=track_id,
        old_status=old_status,
        new_status="completed",
        reason=f"Track completed via CLI by {completed_by}",
        changed_by=completed_by
    )

    # Save track
    save_track(track, track_path)
    _sync_track_to_db(track, root_dir)
    print(f"✅ Track '{track.name}' marked as completed")

    # Update dependency caches for all dependents
    for dependent_id in track.depended_on_by:
        if _update_dependent_cache(fs, dependent_id, track_id, "completed"):
            print(f"  ✓ Updated dependent: {dependent_id}")
        else:
            print(f"  ⚠️  Failed to update dependent: {dependent_id}")

    # Update roadmap progress (this also syncs track status to roadmap.yaml)
    _update_roadmap_progress(fs)

    # Log activity
    logger = ActivityLogger(root_dir)
    logger.log_activity(
        ActivityType.TRACK_COMPLETED,
        f"Track '{track.name}' completed",
        {"track_id": track_id}
    )

    return 0


def refresh_progress(root_dir: Path) -> int:
    """
    Refresh all progress calculations.

    Args:
        root_dir: Root directory containing .vibey/

    Returns:
        Exit code: 0 for success, 1 for error
    """
    fs = FileSystemManager(root_dir)
    print("🔄 Refreshing progress calculations...")

    # Refresh all sprints
    for sprint_id in fs.list_sprints():
        _update_sprint_progress(fs, sprint_id)

    print("✅ Progress refreshed")
    return 0


def recalculate_all(root_dir: Path, verify: bool = False) -> int:
    """
    Recalculate entire roadmap hierarchy from bottom to top.

    Performs a complete recalculation of:
    - All sprint progress (from tasks)
    - All track progress (from sprints)
    - Roadmap progress (from tracks)
    - All dependency caches
    - All blocked status flags

    Args:
        root_dir: Root directory containing .vibey/
        verify: If True, verify consistency after recalculation

    Returns:
        Exit code: 0 for success, 1 for error
    """
    fs = FileSystemManager(root_dir)
    print("🔄 Recalculating entire roadmap hierarchy...")
    print()

    # Step 1: Recalculate all sprints (bottom-up)
    print("📊 Step 1/5: Recalculating sprint progress...")
    sprint_count = 0
    for sprint_id in fs.list_sprints():
        _update_sprint_progress(fs, sprint_id)
        sprint_count += 1
    print(f"  ✅ {sprint_count} sprints recalculated")
    print()

    # Step 2: Recalculate all tracks
    print("📊 Step 2/5: Recalculating track progress...")
    track_count = 0
    for track_id in fs.list_tracks():
        _update_track_progress(fs, track_id)
        track_count += 1
    print(f"  ✅ {track_count} tracks recalculated")
    print()

    # Step 3: Recalculate roadmap-level progress
    print("📊 Step 3/5: Recalculating roadmap progress...")
    _update_roadmap_progress(fs)
    print(f"  ✅ Roadmap progress recalculated")
    print()

    # Step 4: Refresh all dependency caches
    print("🔗 Step 4/5: Refreshing dependency caches...")
    dep_count = _refresh_all_dependency_caches(fs)
    print(f"  ✅ {dep_count} dependency cache entries refreshed")
    print()

    # Step 5: Verify consistency (optional)
    if verify:
        print("🔍 Step 5/5: Verifying consistency...")
        issues = _verify_roadmap_consistency(fs)
        if issues:
            print(f"  ⚠️  {len(issues)} consistency issues found:")
            for issue in issues[:10]:  # Show first 10
                print(f"     - {issue}")
            if len(issues) > 10:
                print(f"     ... and {len(issues) - 10} more")
            print()
            print("⚠️  Recalculation completed but consistency issues remain")
            return 1
        else:
            print(f"  ✅ Roadmap consistency verified - no issues found")
            print()
    else:
        print("⏭️  Step 5/5: Consistency verification skipped (use verify=True to enable)")
        print()

    print("✅ Complete roadmap recalculation finished!")
    return 0


# Private helper functions

def _update_dependent_cache(
    fs: FileSystemManager,
    dependent_id: str,
    blocker_id: str,
    new_status: str
) -> bool:
    """
    Update cached dependency status in a dependent object.

    Args:
        fs: Filesystem manager
        dependent_id: ID of the dependent (task/sprint/track that depends on blocker)
        blocker_id: ID of the blocker (dependency that changed status)
        new_status: New status of the blocker

    Returns:
        True if updated successfully
    """
    # Determine object type from ID format
    if '-task-' in dependent_id:
        # It's a task
        sprint_id = dependent_id.split('-task-')[0]
        tasks_path = fs.get_tasks_path(sprint_id)

        if not tasks_path.exists():
            print(f"⚠️  Tasks file not found for dependent: {dependent_id}")
            return False

        tasks = load_tasks(tasks_path)
        task = next((t for t in tasks if t.id == dependent_id), None)

        if not task:
            print(f"⚠️  Dependent task not found: {dependent_id}")
            return False

        # Update depends_on cache
        modified = False
        for dep_status in task.depends_on:
            if dep_status.blocker_id == blocker_id:
                dep_status.current_status = new_status
                dep_status.last_checked = datetime.now(timezone.utc)
                modified = True
                break

        if not modified:
            print(f"⚠️  Blocker {blocker_id} not found in task {dependent_id} depends_on")
            return False

        # Recompute blocked status
        task.blocked = task.compute_blocked_status()

        # Save only the modified task (not all sibling tasks)
        save_task(task, tasks_path)
        return True

    elif '-sprint-' in dependent_id:
        # It's a sprint
        sprint_path = fs.get_sprint_path(dependent_id)

        if not sprint_path.exists():
            print(f"⚠️  Sprint file not found: {dependent_id}")
            return False

        sprint = load_sprint(sprint_path)

        # Update depends_on cache
        modified = False
        for dep_status in sprint.depends_on:
            if dep_status.blocker_id == blocker_id:
                dep_status.current_status = new_status
                dep_status.last_checked = datetime.now(timezone.utc)
                modified = True
                break

        if not modified:
            print(f"⚠️  Blocker {blocker_id} not found in sprint {dependent_id} depends_on")
            return False

        # Recompute blocked status
        sprint.blocked = sprint.compute_blocked_status()

        # Save sprint
        save_sprint(sprint, sprint_path)
        return True

    else:
        # It's a track
        track_path = fs.get_track_path(dependent_id)

        if not track_path.exists():
            print(f"⚠️  Track file not found: {dependent_id}")
            return False

        track = load_track(track_path)

        # Update depends_on cache
        modified = False
        for dep_status in track.depends_on:
            if dep_status.blocker_id == blocker_id:
                dep_status.current_status = new_status
                dep_status.last_checked = datetime.now(timezone.utc)
                modified = True
                break

        if not modified:
            print(f"⚠️  Blocker {blocker_id} not found in track {dependent_id} depends_on")
            return False

        # Recompute blocked status
        track.blocked = track.compute_blocked_status()

        # Save track
        save_track(track, track_path)
        return True


def _update_sprint_progress(fs: FileSystemManager, sprint_id: str):
    """Update sprint progress based on task completion."""
    sprint_path = fs.get_sprint_path(sprint_id)
    if not sprint_path.exists():
        return

    sprint = load_sprint(sprint_path)

    # Get tasks for this sprint - method depends on structure
    if fs.structure_format == "flat":
        # In flat structure, load tasks from database or filter from all tasks
        tasks_dir = fs.roadmap_root / "tasks"
        if tasks_dir.exists():
            tasks = []
            # Load all task files and filter by sprint_id (slug)
            # Sprint has both ULID (sprint.id) and slug (from parent_ref or derived)
            sprint_slug = getattr(sprint, 'slug', None)
            sprint_ulid = sprint.id
            for task_file in tasks_dir.glob("*.yaml"):
                try:
                    task = load_task(task_file)
                    # Match by sprint slug or ULID
                    # Support both v1 (sprint_id) and v2 (parent_ref) formats
                    task_sprint_id = getattr(task, 'sprint_id', None)
                    if task_sprint_id and (task_sprint_id == sprint_slug or task_sprint_id == sprint_ulid):
                        tasks.append(task)
                except Exception as e:
                    # Try raw YAML parse for v2 format tasks that fail load_task
                    try:
                        import yaml
                        with open(task_file) as f:
                            raw_data = yaml.safe_load(f)
                        task_data = raw_data.get('task', raw_data)
                        # Check v2 parent_ref field
                        parent_ref = task_data.get('parent_ref', '')
                        if parent_ref == sprint_ulid:
                            # This is a v2 format task for this sprint
                            # Create minimal task object for progress counting
                            from vibey.roadmap.models import TaskType
                            task_type_str = task_data.get('task_type_detail', task_data.get('task_type', 'development'))
                            task_status_str = task_data.get('status', 'not_started')

                            # Map task type string to enum
                            task_type_map = {
                                'development': TaskType.DEVELOPMENT,
                                'completion_gate': TaskType.COMPLETION_GATE,
                                'production_gate': TaskType.PRODUCTION_GATE,
                            }
                            task_type = task_type_map.get(task_type_str, TaskType.DEVELOPMENT)

                            # Create a simple mock task for progress counting
                            class MockTask:
                                pass
                            mock_task = MockTask()
                            mock_task.task_type = task_type
                            mock_task.status = TaskStatus(task_status_str)
                            tasks.append(mock_task)
                    except Exception:
                        continue
        else:
            tasks = []
    else:
        # Nested structure: tasks are in sprint directory
        tasks_path = fs.get_tasks_path(sprint_id)
        if not tasks_path.exists():
            return
        tasks = load_tasks(tasks_path)

    # Calculate progress by task type
    from vibey.roadmap.models import TaskType

    # Development tasks
    dev_tasks = [t for t in tasks if t.task_type == TaskType.DEVELOPMENT]
    dev_total = len(dev_tasks)
    dev_completed = len([t for t in dev_tasks if t.status == TaskStatus.COMPLETED])

    # Completion gate tasks
    comp_gate_tasks = [t for t in tasks if t.task_type == TaskType.COMPLETION_GATE]
    comp_gate_total = len(comp_gate_tasks)
    comp_gate_completed = len([t for t in comp_gate_tasks if t.status == TaskStatus.COMPLETED])

    # Production gate tasks
    prod_gate_tasks = [t for t in tasks if t.task_type == TaskType.PRODUCTION_GATE]
    prod_gate_total = len(prod_gate_tasks)
    prod_gate_completed = len([t for t in prod_gate_tasks if t.status == TaskStatus.COMPLETED])

    # Total tasks and completion
    total_tasks = dev_total + comp_gate_total + prod_gate_total
    completed_tasks = dev_completed + comp_gate_completed + prod_gate_completed
    completion_percent = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

    # Update sprint progress
    sprint.progress.tasks_total = total_tasks
    sprint.progress.tasks_completed = completed_tasks
    sprint.progress.development_tasks_total = dev_total
    sprint.progress.development_tasks_completed = dev_completed
    sprint.progress.completion_gate_tasks_total = comp_gate_total
    sprint.progress.completion_gate_tasks_completed = comp_gate_completed
    sprint.progress.production_gate_tasks_total = prod_gate_total
    sprint.progress.production_gate_tasks_completed = prod_gate_completed
    sprint.progress.completion_percent = completion_percent

    # Check if sprint can auto-progress
    status_manager = StatusManager(fs.root_dir)
    progressed, new_status, message = status_manager.progress_sprint_status(sprint)

    if progressed and new_status:
        old_status = sprint.status
        sprint.status = new_status

        # Set appropriate timestamp based on new status
        now = datetime.now(timezone.utc)
        if new_status == Status.IN_PROGRESS:
            sprint.started = now
        elif new_status == Status.COMPLETION_GATE_CHECK:
            sprint.completion_gate_check_at = now
        elif new_status == Status.COMPLETED:
            sprint.completed = now
        elif new_status == Status.PRODUCTION_GATE_CHECK:
            sprint.production_gate_check_at = now
        elif new_status == Status.PRODUCTION_READY:
            sprint.production_ready_at = now
        elif new_status == Status.DEPLOYED:
            sprint.deployed_at = now

        sprint.metadata.last_modified = now
        print(f"🎉 Sprint '{sprint.name}' progressed to {new_status.value}: {message}")

        # Update dependency caches for all dependents when status changes
        for dependent_id in sprint.depended_on_by:
            if _update_dependent_cache(fs, dependent_id, sprint_id, new_status.value):
                print(f"  ✓ Updated dependent: {dependent_id}")
            else:
                print(f"  ⚠️  Failed to update dependent: {dependent_id}")

    # Compute blockers
    computer = BlockerComputer(fs.root_dir)
    blockers = computer.compute_sprint_blockers(sprint)
    sprint.blocked = len(blockers) > 0

    # Save sprint
    save_sprint(sprint, sprint_path)
    _record_cli_changes(sprint_path, fs.root_dir)
    _sync_sprint_to_db(sprint, fs.root_dir)

    # Update track progress (use sprint.track_id for ULID compatibility)
    parent_track_id = getattr(sprint, 'track_id', None) or sprint_id.rsplit('-', 1)[0]
    _update_track_progress(fs, parent_track_id)


def _update_track_progress(fs: FileSystemManager, track_id: str):
    """Update track progress based on sprint completion."""
    track_path = fs.get_track_path(track_id)
    if not track_path.exists():
        return

    try:
        track = load_track(track_path)
    except Exception as e:
        print(f"⚠️  Failed to load track {track_id}: {e}")
        return

    # Calculate progress AND update sprint summaries
    total_sprints = len(track.sprints)
    completed_sprints = 0
    total_tasks = 0
    completed_tasks = 0

    for sprint_summary in track.sprints:
        sprint_path = fs.get_sprint_path(sprint_summary.id)
        if sprint_path.exists():
            sprint = load_sprint(sprint_path)

            # Update sprint summary with current sprint state
            sprint_summary.status = sprint.status
            sprint_summary.started = sprint.started

            if sprint.status in [Status.COMPLETED, Status.PRODUCTION_GATE_CHECK, Status.PRODUCTION_READY, Status.DEPLOYED]:
                completed_sprints += 1

            total_tasks += sprint.progress.tasks_total
            completed_tasks += sprint.progress.tasks_completed

    completion_percent = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

    # Update track progress
    track.progress.sprints_total = total_sprints
    track.progress.sprints_completed = completed_sprints
    track.progress.tasks_total = total_tasks
    track.progress.tasks_completed = completed_tasks
    track.progress.completion_percent = completion_percent

    # Check if track can auto-progress
    status_manager = StatusManager(fs.root_dir)
    progressed, new_status, message = status_manager.progress_track_status(track)

    if progressed and new_status:
        old_status = track.status
        track.status = new_status

        # Set appropriate timestamp based on new status
        # Note: Tracks only support started and completed timestamps
        # (unlike tasks which also have production_ready_at)
        now = datetime.now(timezone.utc)
        if new_status == Status.IN_PROGRESS and not track.started:
            track.started = now
        elif new_status == Status.COMPLETED and not track.completed:
            track.completed = now

        track.metadata.last_modified = now
        print(f"🎉 Track '{track.name}' progressed to {new_status.value}: {message}")

        # Update dependency caches for all dependents when status changes
        for dependent_id in track.depended_on_by:
            if _update_dependent_cache(fs, dependent_id, track_id, new_status.value):
                print(f"  ✓ Updated dependent: {dependent_id}")
            else:
                print(f"  ⚠️  Failed to update dependent: {dependent_id}")

    # Compute blockers
    computer = BlockerComputer(fs.root_dir)
    blockers = computer.compute_track_blockers(track)
    track.blocked = len(blockers) > 0

    # Save track
    save_track(track, track_path)
    _record_cli_changes(track_path, fs.root_dir)
    _sync_track_to_db(track, fs.root_dir)

    # Update roadmap progress
    _update_roadmap_progress(fs)


def _update_roadmap_progress(fs: FileSystemManager):
    """Update roadmap progress based on track completion."""
    roadmap_path = fs.get_roadmap_path()
    if not roadmap_path.exists():
        return

    roadmap = load_roadmap(roadmap_path)

    # Calculate progress
    total_tracks = len(roadmap.tracks)
    completed_tracks = 0
    total_sprints = 0
    completed_sprints = 0
    total_tasks = 0
    completed_tasks = 0

    for track_summary in roadmap.tracks:
        track_path = fs.get_track_path(track_summary.id)
        if track_path.exists():
            try:
                track = load_track(track_path)

                # Sync track status from track.yaml to roadmap.yaml
                track_summary.status = track.status

                if track.status in [Status.COMPLETED, Status.PRODUCTION_READY, Status.DEPLOYED]:
                    completed_tracks += 1

                total_sprints += track.progress.sprints_total
                completed_sprints += track.progress.sprints_completed
                total_tasks += track.progress.tasks_total
                completed_tasks += track.progress.tasks_completed
            except Exception as e:
                print(f"⚠️  Failed to load track {track_summary.id}: {e}")
                continue

    completion_percent = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

    # Update roadmap progress
    roadmap.progress.tracks_total = total_tracks
    roadmap.progress.tracks_completed = completed_tracks
    roadmap.progress.sprints_total = total_sprints
    roadmap.progress.sprints_completed = completed_sprints
    roadmap.progress.tasks_total = total_tasks
    roadmap.progress.tasks_completed = completed_tasks
    roadmap.progress.completion_percent = completion_percent

    # Check if roadmap can auto-progress
    status_manager = StatusManager(fs.root_dir)
    progressed, new_status, message = status_manager.progress_roadmap_status(roadmap)

    if progressed and new_status:
        roadmap.status = new_status
        print(f"🎉 Roadmap '{roadmap.name}' progressed to {new_status.value}: {message}")

    # Save roadmap
    save_roadmap(roadmap, roadmap_path)
    _record_cli_changes(roadmap_path, fs.root_dir)
    _sync_roadmap_to_db(roadmap, fs.root_dir)


def _refresh_all_dependency_caches(fs: FileSystemManager) -> int:
    """
    Refresh all dependency caches across the entire roadmap.

    Returns:
        Number of dependency cache entries updated
    """
    updated_count = 0

    # Load roadmap to get all tracks
    roadmap_path = fs.get_roadmap_path()
    if not roadmap_path.exists():
        return 0

    roadmap = load_roadmap(roadmap_path)

    # Refresh track dependencies
    for track_summary in roadmap.tracks:
        track_path = fs.get_track_path(track_summary.id)
        if not track_path.exists():
            continue

        try:
            track = load_track(track_path)
        except Exception as e:
            print(f"⚠️  Failed to load track {track_summary.id}: {e}")
            continue

        modified = False

        # Update depends_on cache
        for dep_status in track.depends_on:
            # Get current status of blocker
            blocker_path = fs.get_track_path(dep_status.blocker_id)
            if blocker_path.exists():
                try:
                    blocker_track = load_track(blocker_path)
                    if dep_status.current_status != blocker_track.status.value:
                        dep_status.current_status = blocker_track.status.value
                        dep_status.last_checked = datetime.now(timezone.utc)
                        modified = True
                        updated_count += 1
                except Exception as e:
                    print(f"⚠️  Failed to load blocker track {dep_status.blocker_id}: {e}")
                    continue

        # Recompute blocked status
        if modified:
            track.blocked = track.compute_blocked_status()
            save_track(track, track_path)

    # Refresh sprint dependencies
    for sprint_id in fs.list_sprints():
        sprint_path = fs.get_sprint_path(sprint_id)
        if not sprint_path.exists():
            continue

        sprint = load_sprint(sprint_path)
        modified = False

        for dep_status in sprint.depends_on:
            # Determine blocker type and get its status
            if dep_status.blocker_type == DependencyType.TRACK:
                blocker_path = fs.get_track_path(dep_status.blocker_id)
                if blocker_path.exists():
                    blocker = load_track(blocker_path)
                    if dep_status.current_status != blocker.status.value:
                        dep_status.current_status = blocker.status.value
                        dep_status.last_checked = datetime.now(timezone.utc)
                        modified = True
                        updated_count += 1
            elif dep_status.blocker_type == DependencyType.SPRINT:
                blocker_path = fs.get_sprint_path(dep_status.blocker_id)
                if blocker_path.exists():
                    blocker = load_sprint(blocker_path)
                    if dep_status.current_status != blocker.status.value:
                        dep_status.current_status = blocker.status.value
                        dep_status.last_checked = datetime.now(timezone.utc)
                        modified = True
                        updated_count += 1

        if modified:
            sprint.blocked = sprint.compute_blocked_status()
            save_sprint(sprint, sprint_path)

    # Refresh task dependencies
    for sprint_id in fs.list_sprints():
        tasks_path = fs.get_tasks_path(sprint_id)
        if not tasks_path.exists():
            continue

        tasks = load_tasks(tasks_path)
        modified = False

        for task in tasks:
            for dep_status in task.depends_on:
                # Tasks can depend on other tasks or sprints
                if dep_status.blocker_type == DependencyType.TASK:
                    # Find the blocker task
                    blocker_sprint_id = dep_status.blocker_id.rsplit('-task-', 1)[0] + '-task-' + dep_status.blocker_id.split('-task-')[1].split('-')[0]
                    blocker_tasks_path = fs.get_tasks_path(blocker_sprint_id.rsplit('-task-', 1)[0])
                    if blocker_tasks_path.exists():
                        blocker_tasks = load_tasks(blocker_tasks_path)
                        blocker_task = next((t for t in blocker_tasks if t.id == dep_status.blocker_id), None)
                        if blocker_task and dep_status.current_status != blocker_task.status.value:
                            dep_status.current_status = blocker_task.status.value
                            dep_status.last_checked = datetime.now(timezone.utc)
                            modified = True
                            updated_count += 1
                elif dep_status.blocker_type == DependencyType.SPRINT:
                    blocker_path = fs.get_sprint_path(dep_status.blocker_id)
                    if blocker_path.exists():
                        blocker = load_sprint(blocker_path)
                        if dep_status.current_status != blocker.status.value:
                            dep_status.current_status = blocker.status.value
                            dep_status.last_checked = datetime.now(timezone.utc)
                            modified = True
                            updated_count += 1

            if modified:
                task.blocked = task.compute_blocked_status()

        if modified:
            save_tasks(tasks, tasks_path)

    return updated_count


def _verify_roadmap_consistency(fs: FileSystemManager) -> List[str]:
    """
    Verify roadmap consistency and return list of issues found.

    Returns:
        List of issue descriptions (empty if no issues)
    """
    issues = []

    roadmap_path = fs.get_roadmap_path()
    if not roadmap_path.exists():
        issues.append("Roadmap file not found")
        return issues

    roadmap = load_roadmap(roadmap_path)

    # Verify sprint-level consistency
    for sprint_id in fs.list_sprints():
        sprint_path = fs.get_sprint_path(sprint_id)
        tasks_path = fs.get_tasks_path(sprint_id)

        if not sprint_path.exists():
            continue

        sprint = load_sprint(sprint_path)

        if tasks_path.exists():
            tasks = load_tasks(tasks_path)

            # Check task counts
            actual_tasks_total = len(tasks)
            actual_tasks_completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)

            if sprint.progress.tasks_total != actual_tasks_total:
                issues.append(f"Sprint {sprint_id}: tasks_total mismatch (stored={sprint.progress.tasks_total}, actual={actual_tasks_total})")

            if sprint.progress.tasks_completed != actual_tasks_completed:
                issues.append(f"Sprint {sprint_id}: tasks_completed mismatch (stored={sprint.progress.tasks_completed}, actual={actual_tasks_completed})")

    # Verify track-level consistency
    for track_summary in roadmap.tracks:
        track_path = fs.get_track_path(track_summary.id)
        if not track_path.exists():
            continue

        track = load_track(track_path)

        # Aggregate sprint data
        actual_sprints_total = len(track.sprints)
        actual_sprints_completed = 0
        actual_tasks_total = 0
        actual_tasks_completed = 0

        for sprint_summary in track.sprints:
            sprint_path = fs.get_sprint_path(sprint_summary.id)
            if sprint_path.exists():
                sprint = load_sprint(sprint_path)

                if sprint.status in [Status.COMPLETED, Status.PRODUCTION_GATE_CHECK, Status.PRODUCTION_READY, Status.DEPLOYED]:
                    actual_sprints_completed += 1

                actual_tasks_total += sprint.progress.tasks_total
                actual_tasks_completed += sprint.progress.tasks_completed

        # Check consistency
        if track.progress.sprints_total != actual_sprints_total:
            issues.append(f"Track {track.id}: sprints_total mismatch (stored={track.progress.sprints_total}, actual={actual_sprints_total})")

        if track.progress.sprints_completed != actual_sprints_completed:
            issues.append(f"Track {track.id}: sprints_completed mismatch (stored={track.progress.sprints_completed}, actual={actual_sprints_completed})")

        if track.progress.tasks_total != actual_tasks_total:
            issues.append(f"Track {track.id}: tasks_total mismatch (stored={track.progress.tasks_total}, actual={actual_tasks_total})")

        if track.progress.tasks_completed != actual_tasks_completed:
            issues.append(f"Track {track.id}: tasks_completed mismatch (stored={track.progress.tasks_completed}, actual={actual_tasks_completed})")

    return issues
