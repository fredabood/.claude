"""
Roadmap query operations.

Provides read operations for roadmap, tracks, sprints, and tasks.
Supports both YAML and SQLite backends with automatic detection.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from vibey.roadmap.models import Roadmap, Track, Sprint, Task, Status
from vibey.roadmap.serialization import load_roadmap as yaml_load_roadmap
from vibey.roadmap.serialization import load_track as yaml_load_track
from vibey.roadmap.serialization import load_sprint as yaml_load_sprint
from vibey.roadmap.serialization import load_tasks as yaml_load_tasks
from vibey.cli.roadmap_lib.filesystem import FileSystemManager, find_roadmap_root
from vibey.cli.roadmap_lib.dependencies import DependencyResolver
from vibey.cli.roadmap_lib.blockers import BlockerComputer


def _use_sqlite_backend(root_dir: Path) -> bool:
    """
    Determine whether to use SQLite backend.

    Uses SQLite if:
    1. Database file exists at .vibey/roadmap.db
    2. Database has valid schema (can query database_state)

    Args:
        root_dir: Root directory containing .vibey/

    Returns:
        True if SQLite backend should be used, False for YAML
    """
    db_path = root_dir / ".vibey" / "roadmap.db"
    if not db_path.exists():
        return False

    try:
        from vibey.roadmap.database import get_connection
        conn = get_connection(db_path=db_path)
        # Verify database is initialized
        row = conn.execute("SELECT schema_version FROM database_state WHERE id = 1").fetchone()
        return row is not None
    except Exception:
        return False


def _get_sql_loaders():
    """Import SQL loaders lazily to avoid circular imports."""
    from vibey.roadmap.serialization.sql_loader import (
        load_roadmap as sql_load_roadmap,
        load_track as sql_load_track,
        load_sprint as sql_load_sprint,
        load_tasks_by_sprint as sql_load_tasks,
    )
    return sql_load_roadmap, sql_load_track, sql_load_sprint, sql_load_tasks


def load_roadmap(file_path_or_id, root_dir: Optional[Path] = None):
    """
    Load roadmap from appropriate backend.

    Args:
        file_path_or_id: Path to YAML file or roadmap ID for SQLite
        root_dir: Root directory for backend detection

    Returns:
        Roadmap object
    """
    if root_dir and _use_sqlite_backend(root_dir):
        sql_load_roadmap, _, _, _ = _get_sql_loaders()
        roadmap_id = file_path_or_id if isinstance(file_path_or_id, str) and not file_path_or_id.endswith('.yaml') else 'vibey-framework-v2'
        return sql_load_roadmap(roadmap_id)
    return yaml_load_roadmap(file_path_or_id)


def load_track(file_path_or_id, root_dir: Optional[Path] = None):
    """
    Load track from appropriate backend.

    Args:
        file_path_or_id: Path to YAML file or track ID for SQLite
        root_dir: Root directory for backend detection

    Returns:
        Track object
    """
    if root_dir and _use_sqlite_backend(root_dir):
        _, sql_load_track, _, _ = _get_sql_loaders()
        # Extract track ID from path if needed
        if isinstance(file_path_or_id, Path):
            track_id = file_path_or_id.parent.name
        else:
            track_id = file_path_or_id
        return sql_load_track(track_id)
    return yaml_load_track(file_path_or_id)


def load_sprint(file_path_or_id, root_dir: Optional[Path] = None):
    """
    Load sprint from appropriate backend.

    Args:
        file_path_or_id: Path to YAML file or sprint ID for SQLite
        root_dir: Root directory for backend detection

    Returns:
        Sprint object
    """
    if root_dir and _use_sqlite_backend(root_dir):
        _, _, sql_load_sprint, _ = _get_sql_loaders()
        # Extract sprint ID from path if needed
        if isinstance(file_path_or_id, Path):
            sprint_id = file_path_or_id.parent.name
        else:
            sprint_id = file_path_or_id
        return sql_load_sprint(sprint_id)
    return yaml_load_sprint(file_path_or_id)


def load_tasks(file_path_or_sprint_id, root_dir: Optional[Path] = None):
    """
    Load tasks from appropriate backend.

    Args:
        file_path_or_sprint_id: Path to tasks YAML or sprint ID for SQLite
        root_dir: Root directory for backend detection

    Returns:
        List of Task objects
    """
    if root_dir and _use_sqlite_backend(root_dir):
        _, _, _, sql_load_tasks = _get_sql_loaders()
        # Extract sprint ID from path if needed
        if isinstance(file_path_or_sprint_id, Path):
            sprint_id = file_path_or_sprint_id.parent.name
        else:
            sprint_id = file_path_or_sprint_id
        return sql_load_tasks(sprint_id)
    return yaml_load_tasks(file_path_or_sprint_id)


def query_roadmap_summary(root_dir: Path) -> Dict[str, Any]:
    """
    Get roadmap summary with high-level overview.

    Args:
        root_dir: Root directory containing .vibey/

    Returns:
        Dictionary with roadmap summary data
    """
    fs = FileSystemManager(root_dir)
    roadmap_path = fs.get_roadmap_path()
    use_sqlite = _use_sqlite_backend(root_dir)

    if not use_sqlite and not roadmap_path.exists():
        return {"error": "Roadmap not found"}

    roadmap = load_roadmap(roadmap_path, root_dir=root_dir)

    return {
        "id": roadmap.id,
        "name": roadmap.name,
        "version": roadmap.version,
        "status": roadmap.status.value,
        "blocked": roadmap.blocked,
        "created": _format_datetime(roadmap.created),
        "progress": {
            "tracks": f"{roadmap.progress.tracks_completed}/{roadmap.progress.tracks_total}",
            "sprints": f"{roadmap.progress.sprints_completed}/{roadmap.progress.sprints_total}",
            "tasks": f"{roadmap.progress.tasks_completed}/{roadmap.progress.tasks_total}",
            "completion": f"{roadmap.progress.completion_percent}%",
        },
        "tracks": _get_tracks_with_progress(fs, roadmap.tracks, root_dir),
        "backend": "sqlite" if use_sqlite else "yaml",
    }


def query_track_details(root_dir: Path, track_id: str) -> Dict[str, Any]:
    """
    Get detailed track information.

    Args:
        root_dir: Root directory containing .vibey/
        track_id: ID of the track to query

    Returns:
        Dictionary with track details
    """
    fs = FileSystemManager(root_dir)
    track_path = fs.get_track_path(track_id)
    use_sqlite = _use_sqlite_backend(root_dir)

    if not use_sqlite and not track_path.exists():
        return {"error": f"Track '{track_id}' not found"}

    try:
        track = load_track(track_path if not use_sqlite else track_id, root_dir=root_dir)
    except (ValueError, FileNotFoundError) as e:
        return {"error": f"Track '{track_id}' not found"}

    # Build sprints list with error handling
    sprints_list = []
    if track.sprints:
        for sprint in track.sprints:
            try:
                sprints_list.append({
                    "id": sprint.id if hasattr(sprint, 'id') else sprint.get('id', 'unknown'),
                    "name": sprint.name if hasattr(sprint, 'name') else sprint.get('name', 'Unknown'),
                    "status": sprint.status.value if hasattr(sprint, 'status') and hasattr(sprint.status, 'value') else sprint.get('status', 'unknown'),
                })
            except (AttributeError, TypeError) as e:
                # Sprint might be a string or dict, handle gracefully
                if isinstance(sprint, str):
                    sprints_list.append({"id": sprint, "name": sprint, "status": "unknown"})
                elif isinstance(sprint, dict):
                    sprints_list.append({
                        "id": sprint.get('id', 'unknown'),
                        "name": sprint.get('name', 'Unknown'),
                        "status": sprint.get('status', 'unknown'),
                    })

    # Build dependencies list with error handling
    deps_list = []
    if track.dependencies:
        for dep in track.dependencies:
            try:
                deps_list.append({
                    "target_id": dep.target_id if hasattr(dep, 'target_id') else dep.get('target_id', dep if isinstance(dep, str) else 'unknown'),
                    "type": dep.type.value if hasattr(dep, 'type') and hasattr(dep.type, 'value') else dep.get('type', 'track'),
                    "target_status": dep.target_status if hasattr(dep, 'target_status') else dep.get('target_status', 'any'),
                })
            except (AttributeError, TypeError) as e:
                # Dependency might be a string, handle gracefully
                if isinstance(dep, str):
                    deps_list.append({"target_id": dep, "type": "track", "target_status": "any"})
                elif isinstance(dep, dict):
                    deps_list.append({
                        "target_id": dep.get('target_id', 'unknown'),
                        "type": dep.get('type', 'track'),
                        "target_status": dep.get('target_status', 'any'),
                    })

    return {
        "id": track.id,
        "name": track.name,
        "status": track.status.value,
        "blocked": track.blocked,
        "started": _format_datetime(track.started) if track.started else None,
        "completed": _format_datetime(track.completed) if track.completed else None,
        "estimated_duration": track.estimated_duration,
        "progress": {
            "sprints": f"{track.progress.sprints_completed}/{track.progress.sprints_total}",
            "tasks": f"{track.progress.tasks_completed}/{track.progress.tasks_total}",
            "completion": f"{track.progress.completion_percent}%",
        },
        "sprints": sprints_list,
        "dependencies": deps_list,
    }


def query_sprint_details(root_dir: Path, sprint_id: str) -> Dict[str, Any]:
    """
    Get detailed sprint information including tasks.

    Args:
        root_dir: Root directory containing .vibey/
        sprint_id: ID of the sprint to query

    Returns:
        Dictionary with sprint details
    """
    fs = FileSystemManager(root_dir)
    sprint_path = fs.get_sprint_path(sprint_id)
    use_sqlite = _use_sqlite_backend(root_dir)

    if not use_sqlite and not sprint_path.exists():
        return {"error": f"Sprint '{sprint_id}' not found"}

    try:
        sprint = load_sprint(sprint_path if not use_sqlite else sprint_id, root_dir=root_dir)
    except (ValueError, FileNotFoundError) as e:
        return {"error": f"Sprint '{sprint_id}' not found"}

    # Load tasks
    tasks_path = fs.get_tasks_path(sprint_id)
    if use_sqlite:
        tasks = load_tasks(sprint_id, root_dir=root_dir)
    else:
        tasks = load_tasks(tasks_path, root_dir=root_dir) if tasks_path.exists() else []

    # Categorize tasks
    dev_tasks = [t for t in tasks if not t.is_quality_gate()]
    completion_gates = [t for t in tasks if t.is_quality_gate() and t.task_type == "completion_gate"]
    production_gates = [t for t in tasks if t.is_quality_gate() and t.task_type == "production_gate"]

    return {
        "id": sprint.id,
        "name": sprint.name,
        "status": sprint.status.value,
        "blocked": sprint.blocked,
        "started": _format_datetime(sprint.started) if sprint.started else None,
        "completed": _format_datetime(sprint.completed) if sprint.completed else None,
        "estimated_duration": sprint.metadata.estimated_duration,
        "progress": {
            "tasks": f"{sprint.progress.tasks_completed}/{sprint.progress.tasks_total}",
            "completion": f"{sprint.progress.completion_percent}%",
        },
        "development_gates": [
            {
                "target_id": gate.target_id,
                "type": gate.type.value,
                "target_status": gate.target_status,
            }
            for gate in sprint.development_gates
        ],
        "tasks": {
            "development": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "blocked": task.blocked,
                }
                for task in dev_tasks
            ],
            "completion_gates": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "gate_type": task.gate_info.gate_type if task.gate_info else None,
                }
                for task in completion_gates
            ],
            "production_gates": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "gate_type": task.gate_info.gate_type if task.gate_info else None,
                }
                for task in production_gates
            ],
        },
    }


def query_task_details(root_dir: Path, task_id: str) -> Dict[str, Any]:
    """
    Get detailed task information.

    Args:
        root_dir: Root directory containing .vibey/
        task_id: ID of the task to query (format: track-sprint-task-nnn)

    Returns:
        Dictionary with task details
    """
    fs = FileSystemManager(root_dir)
    use_sqlite = _use_sqlite_backend(root_dir)

    # For SQLite, we can load task directly by ID
    if use_sqlite:
        try:
            from vibey.roadmap.serialization.sql_loader import load_task as sql_load_task
            task = sql_load_task(task_id)
        except (ValueError, ImportError) as e:
            return {"error": f"Task '{task_id}' not found"}
    else:
        # Extract sprint ID from task ID (e.g., track-1-task-001 -> track-1)
        # Task IDs are: track_id-sprint_num-task-nnn
        parts = task_id.split('-')
        if len(parts) < 4:
            return {"error": f"Invalid task ID format: {task_id}"}

        # Find sprint_id by looking for the pattern with -task-
        task_idx = task_id.rfind('-task-')
        if task_idx == -1:
            return {"error": f"Invalid task ID format: {task_id}"}
        sprint_id = task_id[:task_idx]
        tasks_path = fs.get_tasks_path(sprint_id)

        if not tasks_path.exists():
            return {"error": f"Tasks file not found for sprint '{sprint_id}'"}

        all_tasks = load_tasks(tasks_path, root_dir=root_dir)

        # Find task
        task = None
        for t in all_tasks:
            if t.id == task_id:
                task = t
                break

        if not task:
            return {"error": f"Task '{task_id}' not found"}

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "task_type": task.task_type.value,
        "status": task.status.value,
        "blocked": task.blocked,
        "estimated_tokens": task.estimated_tokens,
        "started": _format_datetime(task.started) if task.started else None,
        "completed": _format_datetime(task.completed) if task.completed else None,
        "assigned_agent": task.assigned_agent,
        "dependencies": [
            {
                "target_id": dep.target_id,
                "type": dep.type.value,
                "target_status": dep.target_status,
            }
            for dep in task.dependencies
        ],
        "gate_info": {
            "gate_type": task.gate_info.gate_type,
            "criteria": task.gate_info.criteria,
            "audit_script": task.gate_info.audit_script,
        } if task.gate_info else None,
    }


def query_blockers(root_dir: Path, object_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get blockers for a specific object or entire roadmap.

    Args:
        root_dir: Root directory containing .vibey/
        object_id: Optional ID of track/sprint/task to check blockers for

    Returns:
        Dictionary with blocker information
    """
    fs = FileSystemManager(root_dir)
    computer = BlockerComputer(root_dir)

    if object_id:
        # Determine object type and load
        if fs.track_exists(object_id):
            obj = load_track(fs.get_track_path(object_id))
            blockers = computer.compute_track_blockers(obj)
        elif fs.sprint_exists(object_id):
            obj = load_sprint(fs.get_sprint_path(object_id))
            blockers = computer.compute_sprint_blockers(obj)
        else:
            # Try as task
            parts = object_id.split('-')
            if len(parts) >= 3:
                sprint_id = '-'.join(parts[:2])
                tasks_path = fs.get_tasks_path(sprint_id)
                if tasks_path.exists():
                    tasks = load_tasks(tasks_path)
                    task = next((t for t in tasks if t.id == object_id), None)
                    if task:
                        blockers = computer.compute_task_blockers(task)
                    else:
                        return {"error": f"Object '{object_id}' not found"}
                else:
                    return {"error": f"Object '{object_id}' not found"}
            else:
                return {"error": f"Object '{object_id}' not found"}

        return {
            "object_id": object_id,
            "blocked": len(blockers) > 0,
            "blockers": [
                {
                    "dependency_id": b.dependency_id,
                    "dependency_type": b.dependency_type,
                    "current_status": b.current_status,
                    "required_status": b.required_status,
                    "blocking_since": _format_datetime(b.blocking_since),
                }
                for b in blockers
            ],
        }
    else:
        # Get all blockers in roadmap
        roadmap = load_roadmap(fs.get_roadmap_path())
        all_blockers = {}

        for track in roadmap.tracks:
            track_obj = load_track(fs.get_track_path(track.id))
            blockers = computer.compute_track_blockers(track_obj)
            if blockers:
                all_blockers[track.id] = [
                    {
                        "dependency_id": b.dependency_id,
                        "dependency_type": b.dependency_type,
                        "current_status": b.current_status,
                        "required_status": b.required_status,
                    }
                    for b in blockers
                ]

        return {"blockers": all_blockers}


def query_dependencies(root_dir: Path) -> Dict[str, Any]:
    """
    Get dependency graph information.

    Args:
        root_dir: Root directory containing .vibey/

    Returns:
        Dictionary with dependency graph analysis
    """
    resolver = DependencyResolver(root_dir)
    resolver.build_dependency_graph()

    # Detect circular dependencies
    cycles = resolver.detect_circular_dependencies()

    return {
        "nodes": len(resolver.dependency_graph),
        "has_circular_dependencies": len(cycles) > 0,
        "circular_dependencies": cycles,
    }


def _format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _get_tracks_with_progress(fs: FileSystemManager, track_summaries, root_dir: Optional[Path] = None) -> list:
    """
    Load track details including progress for each track summary.

    Args:
        fs: FileSystemManager instance
        track_summaries: List of TrackSummary from roadmap
        root_dir: Root directory for backend detection

    Returns:
        List of track dicts with progress data
    """
    use_sqlite = root_dir and _use_sqlite_backend(root_dir)
    tracks_data = []
    for track_summary in track_summaries:
        track_path = fs.get_track_path(track_summary.id)
        if use_sqlite or track_path.exists():
            try:
                track = load_track(track_summary.id if use_sqlite else track_path, root_dir=root_dir)
                tracks_data.append({
                    "id": track.id,
                    "name": track.name,
                    "status": track.status.value,
                    "progress": {
                        "tasks_completed": track.progress.tasks_completed,
                        "tasks_total": track.progress.tasks_total,
                        "sprints_completed": track.progress.sprints_completed,
                        "sprints_total": track.progress.sprints_total,
                        "completion_percent": track.progress.completion_percent,
                    },
                })
            except Exception:
                # Fall back to summary data if track can't be loaded
                tracks_data.append({
                    "id": track_summary.id,
                    "name": track_summary.name,
                    "status": track_summary.status.value,
                    "progress": {
                        "tasks_completed": 0,
                        "tasks_total": 0,
                        "sprints_completed": 0,
                        "sprints_total": 0,
                        "completion_percent": 0,
                    },
                })
        else:
            # Track file doesn't exist, use summary
            tracks_data.append({
                "id": track_summary.id,
                "name": track_summary.name,
                "status": track_summary.status.value,
                "progress": {
                    "tasks_completed": 0,
                    "tasks_total": 0,
                    "sprints_completed": 0,
                    "sprints_total": 0,
                    "completion_percent": 0,
                },
            })
    return tracks_data
