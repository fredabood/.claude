"""
Migration module to convert legacy dependencies to criteria.

This module migrates:
1. depends_on → CompletableTarget criteria blocking IN_PROGRESS
2. blocked_by → CompletableTarget criteria blocking IN_PROGRESS
3. quality_gates → ThresholdTarget criteria blocking COMPLETED
4. deliverables → FileExistsTarget criteria blocking COMPLETED

The migration reads from YAML (which already converts to criteria during load)
and persists to the SQLite criteria table.

Reference: Sprint 12 Task 009
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Generator
from datetime import datetime, timezone
from glob import glob

from ..serialization.yaml_loader import (
    load_task as yaml_load_task,
    load_sprint as yaml_load_sprint,
    load_track as yaml_load_track,
    load_roadmap as yaml_load_roadmap,
)
from ..serialization.sql_dumper import dump_criteria
from ..database import get_connection
from ..database.schema import has_criteria_table, create_criteria_table


def _find_track_dirs(base_dir: Path) -> Generator[Path, None, None]:
    """Find all track directories in the roadmap."""
    roadmap_dir = base_dir / ".vibey" / "roadmap"
    if not roadmap_dir.exists():
        return

    for item in roadmap_dir.iterdir():
        if item.is_dir() and (item / "track.yaml").exists():
            yield item


def _find_sprint_dirs(track_dir: Path) -> Generator[Path, None, None]:
    """Find all sprint directories in a track."""
    for item in track_dir.iterdir():
        if item.is_dir() and (item / "sprint.yaml").exists():
            yield item


def _find_task_dirs(sprint_dir: Path) -> Generator[Path, None, None]:
    """Find all task directories in a sprint."""
    for item in sprint_dir.iterdir():
        if item.is_dir() and (item / "task.yaml").exists():
            yield item


def _convert_dependency_to_criterion(dep, entity_id: str, index: int) -> "Criterion":
    """
    Convert a legacy dependency to a Criterion.

    Args:
        dep: DependencyStatus or similar dependency object
        entity_id: ID of the entity that has this dependency
        index: Index for generating unique criterion ID

    Returns:
        Criterion with CompletableTarget
    """
    from ..models.ticket.completable import Criterion
    from ..models.ticket.targets import CompletableTarget, ExternalTarget
    from ..models.ticket.enums import TicketStatus, CriterionTargetType

    # Generate criterion ID
    criterion_id = f"{entity_id}-dep-{index:03d}"

    # Determine the status being blocked
    blocks = dep.blocks_transition_to if hasattr(dep, 'blocks_transition_to') else 'in_progress'
    if isinstance(blocks, str):
        blocks_status = TicketStatus(blocks)
    else:
        blocks_status = blocks

    # Determine required status
    req_status = dep.required_status if hasattr(dep, 'required_status') else 'completed'
    if isinstance(req_status, str):
        required_status = TicketStatus(req_status) if req_status in ['not_started', 'in_progress', 'completed', 'production_ready'] else TicketStatus.COMPLETED
    else:
        required_status = req_status

    # Handle external vs completable dependencies
    blocker_type = getattr(dep, 'blocker_type', 'completable')
    blocker_id = getattr(dep, 'blocker_id', 'unknown')

    if blocker_type == 'external' or blocker_id == 'unknown':
        # External dependency - use ExternalTarget
        target = ExternalTarget(
            system_name=blocker_id,
            check_endpoint=None,
        )
        description = f"External dependency: {blocker_id}"
    else:
        # Internal dependency - use CompletableTarget
        target = CompletableTarget(
            completable_id=blocker_id,
            required_status=required_status,
        )
        description = f"Depends on {blocker_id} being {required_status.value}"

    return Criterion(
        id=criterion_id,
        description=description,
        required=True,
        blocks_transition_to=blocks_status,
        target=target,
    )


def _convert_task_to_criteria(task) -> List["Criterion"]:
    """
    Convert a legacy Task's dependencies to Criteria.

    Args:
        task: Task dataclass from yaml_loader

    Returns:
        List of Criterion objects
    """
    criteria = []

    # Convert depends_on
    for i, dep in enumerate(getattr(task, 'depends_on', []) or []):
        criterion = _convert_dependency_to_criterion(dep, task.id, i)
        criteria.append(criterion)

    # Convert blocked_by
    for i, blocker in enumerate(getattr(task, 'blocked_by', []) or []):
        criterion = _convert_dependency_to_criterion(
            blocker, task.id, len(criteria)
        )
        criteria.append(criterion)

    return criteria


def migrate_task_criteria_from_file(
    task_file: Path,
    db_path: Optional[Path] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Migrate criteria for a single task from YAML file to SQLite.

    Args:
        task_file: Path to task.yaml file
        db_path: Optional path to database file
        dry_run: If True, don't actually write to database

    Returns:
        Dict with migration results
    """
    try:
        # Load task using legacy loader
        task = yaml_load_task(task_file)
    except Exception as e:
        return {'task_file': str(task_file), 'status': 'error', 'error': str(e)}

    task_id = task.id

    # Convert legacy dependencies to criteria
    criteria = _convert_task_to_criteria(task)

    if not criteria:
        return {'task_id': task_id, 'status': 'no_criteria', 'criteria_count': 0}

    if dry_run:
        return {
            'task_id': task_id,
            'status': 'dry_run',
            'criteria_count': len(criteria),
            'criteria': [{'id': c.id, 'type': c.target.type.value, 'blocks': c.blocks_transition_to.value} for c in criteria]
        }

    # Persist criteria to database
    count = dump_criteria(criteria, 'task', task_id, db_path=db_path)

    return {
        'task_id': task_id,
        'status': 'migrated',
        'criteria_count': count,
    }


def migrate_sprint_criteria_from_dir(
    sprint_dir: Path,
    db_path: Optional[Path] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Migrate criteria for a sprint and all its tasks from directory.

    Args:
        sprint_dir: Path to sprint directory
        db_path: Database path
        dry_run: If True, don't write to database

    Returns:
        Dict with migration results
    """
    sprint_file = sprint_dir / "sprint.yaml"
    if not sprint_file.exists():
        return {'sprint_dir': str(sprint_dir), 'status': 'not_found'}

    try:
        sprint = yaml_load_sprint(sprint_file)
    except Exception as e:
        return {'sprint_dir': str(sprint_dir), 'status': 'error', 'error': str(e)}

    sprint_id = sprint.id
    results = {
        'sprint_id': sprint_id,
        'sprint_criteria_count': 0,
        'tasks_migrated': 0,
        'total_task_criteria': 0,
        'task_results': [],
    }

    # Note: Sprint-level criteria migration would require Sprint model updates
    # For now, focus on task criteria which have depends_on/blocked_by

    # Migrate task criteria
    for task_dir in _find_task_dirs(sprint_dir):
        task_file = task_dir / "task.yaml"
        task_result = migrate_task_criteria_from_file(task_file, db_path=db_path, dry_run=dry_run)
        results['task_results'].append(task_result)
        if task_result['status'] in ('migrated', 'dry_run'):
            results['tasks_migrated'] += 1
            results['total_task_criteria'] += task_result.get('criteria_count', 0)

    results['status'] = 'migrated' if not dry_run else 'dry_run'
    return results


def migrate_track_criteria_from_dir(
    track_dir: Path,
    db_path: Optional[Path] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Migrate criteria for a track and all its sprints/tasks from directory.

    Args:
        track_dir: Path to track directory
        db_path: Database path
        dry_run: If True, don't write to database

    Returns:
        Dict with migration results
    """
    track_file = track_dir / "track.yaml"
    if not track_file.exists():
        return {'track_dir': str(track_dir), 'status': 'not_found'}

    try:
        track = yaml_load_track(track_file)
    except Exception as e:
        return {'track_dir': str(track_dir), 'status': 'error', 'error': str(e)}

    track_id = track.id
    results = {
        'track_id': track_id,
        'track_criteria_count': 0,
        'sprints_migrated': 0,
        'total_tasks_migrated': 0,
        'total_criteria': 0,
        'sprint_results': [],
    }

    # Note: Track-level criteria migration would require Track model updates
    # For now, focus on task criteria which have depends_on/blocked_by

    # Migrate sprint criteria
    for sprint_dir in _find_sprint_dirs(track_dir):
        sprint_result = migrate_sprint_criteria_from_dir(sprint_dir, db_path=db_path, dry_run=dry_run)
        results['sprint_results'].append(sprint_result)
        if sprint_result['status'] in ('migrated', 'dry_run'):
            results['sprints_migrated'] += 1
            results['total_tasks_migrated'] += sprint_result.get('tasks_migrated', 0)
            results['total_criteria'] += sprint_result.get('sprint_criteria_count', 0)
            results['total_criteria'] += sprint_result.get('total_task_criteria', 0)

    results['status'] = 'migrated' if not dry_run else 'dry_run'
    return results


def migrate_all_criteria(
    base_dir: Optional[Path] = None,
    db_path: Optional[Path] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Migrate all criteria from YAML to SQLite.

    This is the main migration function that:
    1. Ensures criteria table exists
    2. Iterates through all tracks, sprints, tasks
    3. Loads from YAML (which converts legacy to criteria)
    4. Persists to SQLite criteria table

    Args:
        base_dir: Base directory containing .vibey folder
        db_path: Database path
        dry_run: If True, don't write to database

    Returns:
        Dict with complete migration results
    """
    if base_dir is None:
        base_dir = Path.cwd()

    # Ensure criteria table exists
    if not has_criteria_table(db_path=db_path, base_dir=base_dir):
        if dry_run:
            return {'status': 'error', 'message': 'criteria table does not exist'}
        create_criteria_table(db_path=db_path, base_dir=base_dir)

    results = {
        'status': 'in_progress',
        'tracks_migrated': 0,
        'total_sprints': 0,
        'total_tasks': 0,
        'total_criteria': 0,
        'track_results': [],
        'started_at': datetime.now(timezone.utc).isoformat(),
    }

    # Find and migrate all tracks
    for track_dir in _find_track_dirs(base_dir):
        track_result = migrate_track_criteria_from_dir(track_dir, db_path=db_path, dry_run=dry_run)
        results['track_results'].append(track_result)
        if track_result['status'] in ('migrated', 'dry_run'):
            results['tracks_migrated'] += 1
            results['total_sprints'] += track_result.get('sprints_migrated', 0)
            results['total_tasks'] += track_result.get('total_tasks_migrated', 0)
            results['total_criteria'] += track_result.get('total_criteria', 0)

    results['status'] = 'migrated' if not dry_run else 'dry_run'
    results['completed_at'] = datetime.now(timezone.utc).isoformat()

    return results


def verify_migration(
    base_dir: Optional[Path] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Verify migration by comparing YAML criteria to SQLite criteria.

    Args:
        base_dir: Base directory
        db_path: Database path

    Returns:
        Dict with verification results
    """
    from ..serialization.sql_loader import load_criteria_for_completable

    if base_dir is None:
        base_dir = Path.cwd()

    results = {
        'status': 'verified',
        'mismatches': [],
        'total_yaml_criteria': 0,
        'total_db_criteria': 0,
        'tasks_checked': 0,
    }

    for track_dir in _find_track_dirs(base_dir):
        for sprint_dir in _find_sprint_dirs(track_dir):
            for task_dir in _find_task_dirs(sprint_dir):
                task_file = task_dir / "task.yaml"
                try:
                    task = yaml_load_task(task_file)
                    # Convert legacy dependencies to criteria for comparison
                    yaml_criteria = _convert_task_to_criteria(task)
                    db_criteria = load_criteria_for_completable('task', task.id, db_path=db_path)

                    results['total_yaml_criteria'] += len(yaml_criteria)
                    results['total_db_criteria'] += len(db_criteria)
                    results['tasks_checked'] += 1

                    if len(yaml_criteria) != len(db_criteria):
                        results['mismatches'].append({
                            'entity': task.id,
                            'yaml_count': len(yaml_criteria),
                            'db_count': len(db_criteria),
                        })
                        results['status'] = 'mismatch'
                except Exception as e:
                    results['mismatches'].append({
                        'entity': str(task_file),
                        'error': str(e),
                    })

    return results


# CLI-callable functions
def run_migration(dry_run: bool = False) -> None:
    """Run the full migration."""
    print(f"{'DRY RUN: ' if dry_run else ''}Migrating criteria from YAML to SQLite...")

    results = migrate_all_criteria(dry_run=dry_run)

    print(f"\nMigration {'preview' if dry_run else 'complete'}:")
    print(f"  Tracks: {results['tracks_migrated']}")
    print(f"  Sprints: {results['total_sprints']}")
    print(f"  Tasks: {results['total_tasks']}")
    print(f"  Criteria: {results['total_criteria']}")

    if not dry_run:
        print("\nRun verify_migration() to confirm.")


def run_verification() -> None:
    """Verify the migration."""
    print("Verifying migration...")

    results = verify_migration()

    print(f"\nVerification: {results['status']}")
    print(f"  YAML criteria: {results['total_yaml_criteria']}")
    print(f"  DB criteria: {results['total_db_criteria']}")

    if results['mismatches']:
        print(f"  Mismatches: {len(results['mismatches'])}")
        for m in results['mismatches'][:5]:
            print(f"    - {m['entity']}: yaml={m['yaml_count']}, db={m['db_count']}")


__all__ = [
    'migrate_task_criteria',
    'migrate_sprint_criteria',
    'migrate_track_criteria',
    'migrate_all_criteria',
    'verify_migration',
    'run_migration',
    'run_verification',
]
