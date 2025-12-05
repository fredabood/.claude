"""
Roadmap query operations.

Provides read operations for roadmap, tracks, sprints, and tasks.
Supports both YAML and SQLite backends with automatic detection.

Includes hierarchy-aware query functions that use smart accessors:
- get_hierarchy_path(): Path from root to ticket
- get_aggregated_commits(): Commits from ticket and descendants
- get_effective_requirements(): Inherited requirements chain
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from vibey.roadmap.models import Roadmap, Track, Sprint, Task, Status
# Import ticket models for hierarchy-aware queries
from vibey.roadmap.models.ticket import (
    HierarchicalTicket,
    RoadmapTicket,
    TrackTicket,
    SprintTicket,
    TaskTicket,
    GitCommit as TicketGitCommit,
    TicketLoader,
)
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


# =============================================================================
# HIERARCHY-AWARE QUERY FUNCTIONS
# =============================================================================


class QueryTicketLoader:
    """
    TicketLoader implementation for query operations.

    Loads tickets by ID using the appropriate backend (YAML or SQLite).
    Configures HierarchicalTicket with this loader for hierarchy traversal.
    """

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.fs = FileSystemManager(root_dir)
        self.use_sqlite = _use_sqlite_backend(root_dir)
        self._cache: Dict[str, HierarchicalTicket] = {}

    def load(self, ticket_id: str) -> HierarchicalTicket:
        """Load a ticket by its ID."""
        if ticket_id in self._cache:
            return self._cache[ticket_id]

        ticket = self._load_uncached(ticket_id)
        self._cache[ticket_id] = ticket
        return ticket

    def _load_uncached(self, ticket_id: str) -> HierarchicalTicket:
        """Load ticket without caching."""
        # Determine ticket type from ID pattern
        if '-task-' in ticket_id:
            return self._load_task_as_ticket(ticket_id)
        elif self._is_sprint_id(ticket_id):
            return self._load_sprint_as_ticket(ticket_id)
        elif self._is_track_id(ticket_id):
            return self._load_track_as_ticket(ticket_id)
        else:
            return self._load_roadmap_as_ticket(ticket_id)

    def _is_sprint_id(self, ticket_id: str) -> bool:
        """Check if ID looks like a sprint ID."""
        # Task IDs contain -task-, so exclude them
        if '-task-' in ticket_id:
            return False
        # Sprint IDs: track-N where N is a number
        parts = ticket_id.rsplit('-', 1)
        if len(parts) == 2:
            try:
                int(parts[1])
                return True
            except ValueError:
                pass
        return False

    def _is_track_id(self, ticket_id: str) -> bool:
        """Check if ID looks like a track ID."""
        # Track IDs don't have numbers at the end (unless it's a sprint)
        if self._is_sprint_id(ticket_id):
            return False
        # Check if track directory exists
        track_path = self.fs.get_track_path(ticket_id)
        return track_path.exists()

    def _load_task_as_ticket(self, task_id: str) -> TaskTicket:
        """Load a task and convert to TaskTicket."""
        # Extract sprint_id from task_id
        task_idx = task_id.rfind('-task-')
        sprint_id = task_id[:task_idx]

        if self.use_sqlite:
            from vibey.roadmap.serialization.sql_loader import load_task as sql_load_task
            task = sql_load_task(task_id)
        else:
            tasks_path = self.fs.get_tasks_path(sprint_id)
            all_tasks = yaml_load_tasks(tasks_path)
            task = next((t for t in all_tasks if t.id == task_id), None)
            if task is None:
                raise ValueError(f"Task not found: {task_id}")

        # Convert to TaskTicket
        return self._task_to_ticket(task, sprint_id)

    def _load_sprint_as_ticket(self, sprint_id: str) -> SprintTicket:
        """Load a sprint and convert to SprintTicket."""
        sprint_path = self.fs.get_sprint_path(sprint_id)

        if self.use_sqlite:
            sprint = load_sprint(sprint_id, root_dir=self.root_dir)
        else:
            sprint = yaml_load_sprint(sprint_path)

        # Extract track_id from sprint_id
        track_id = self._extract_track_from_sprint(sprint_id)

        return self._sprint_to_ticket(sprint, track_id)

    def _load_track_as_ticket(self, track_id: str) -> TrackTicket:
        """Load a track and convert to TrackTicket."""
        track_path = self.fs.get_track_path(track_id)

        if self.use_sqlite:
            track = load_track(track_id, root_dir=self.root_dir)
        else:
            track = yaml_load_track(track_path)

        return self._track_to_ticket(track)

    def _load_roadmap_as_ticket(self, roadmap_id: str) -> RoadmapTicket:
        """Load roadmap and convert to RoadmapTicket."""
        roadmap_path = self.fs.get_roadmap_path()
        roadmap = load_roadmap(roadmap_path, root_dir=self.root_dir)
        return self._roadmap_to_ticket(roadmap)

    def _extract_track_from_sprint(self, sprint_id: str) -> str:
        """Extract track ID from sprint ID."""
        # Sprint IDs: track-N -> track
        parts = sprint_id.rsplit('-', 1)
        return parts[0] if len(parts) == 2 else sprint_id

    def _task_to_ticket(self, task: Task, sprint_id: str) -> TaskTicket:
        """Convert legacy Task to TaskTicket."""
        from vibey.roadmap.models.ticket import TicketStatus, TaskType as TicketTaskType

        # Map status
        status_map = {
            'not_started': TicketStatus.NOT_STARTED,
            'in_progress': TicketStatus.IN_PROGRESS,
            'completed': TicketStatus.COMPLETED,
            'blocked': TicketStatus.NOT_STARTED,  # Blocked maps to NOT_STARTED
        }
        status = status_map.get(task.status.value, TicketStatus.NOT_STARTED)

        # Convert commits
        commits = []
        for c in (task.commits or []):
            commits.append(TicketGitCommit(
                sha=c.sha,
                message=c.message,
                author=c.author,
                date=c.date,
            ))

        # Extract track_id from sprint_id
        track_id = self._extract_track_from_sprint(sprint_id)

        # Get roadmap_id from task or use default
        roadmap_id = getattr(task, 'roadmap_id', 'vibey-framework-v2')

        return TaskTicket(
            id=task.id,
            name=task.title,
            title=task.title,
            status=status,
            parent_ref=sprint_id,
            sprint_id=sprint_id,
            track_id=track_id,
            roadmap_id=roadmap_id,
            children=[],
            commits=commits,
            description=task.description or "",
            blocked=task.blocked,
            created_at=task.created,
            started_at=task.started,
            completed_at=task.completed,
            estimated_tokens=task.estimated_tokens or 1000,
        )

    def _sprint_to_ticket(self, sprint: Sprint, track_id: str) -> SprintTicket:
        """Convert legacy Sprint to SprintTicket."""
        from vibey.roadmap.models.ticket import TicketStatus

        status_map = {
            'not_started': TicketStatus.NOT_STARTED,
            'in_progress': TicketStatus.IN_PROGRESS,
            'completed': TicketStatus.COMPLETED,
            'blocked': TicketStatus.NOT_STARTED,
        }
        status = status_map.get(sprint.status.value, TicketStatus.NOT_STARTED)

        # Get child task IDs
        children = [t.id for t in (sprint.tasks or [])]

        # Get roadmap_id from sprint or use default
        roadmap_id = getattr(sprint, 'roadmap_id', 'vibey-framework-v2')

        return SprintTicket(
            id=sprint.id,
            name=sprint.name,
            status=status,
            parent_ref=track_id,
            track_id=track_id,
            roadmap_id=roadmap_id,
            children=children,
            blocked=sprint.blocked,
            created_at=sprint.created,
            started_at=sprint.started,
            completed_at=sprint.completed,
        )

    def _track_to_ticket(self, track: Track) -> TrackTicket:
        """Convert legacy Track to TrackTicket."""
        from vibey.roadmap.models.ticket import TicketStatus

        status_map = {
            'not_started': TicketStatus.NOT_STARTED,
            'in_progress': TicketStatus.IN_PROGRESS,
            'completed': TicketStatus.COMPLETED,
            'blocked': TicketStatus.NOT_STARTED,
        }
        status = status_map.get(track.status.value, TicketStatus.NOT_STARTED)

        # Get child sprint IDs
        children = [s.id for s in (track.sprints or [])]

        # Get roadmap_id from track
        roadmap_id = track.roadmap_id or 'vibey-framework-v2'

        return TrackTicket(
            id=track.id,
            name=track.name,
            status=status,
            parent_ref=roadmap_id,
            roadmap_id=roadmap_id,
            children=children,
            blocked=track.blocked,
            created_at=track.created,
            started_at=track.started,
            completed_at=track.completed,
        )

    def _roadmap_to_ticket(self, roadmap: Roadmap) -> RoadmapTicket:
        """Convert legacy Roadmap to RoadmapTicket."""
        from vibey.roadmap.models.ticket import TicketStatus

        status_map = {
            'not_started': TicketStatus.NOT_STARTED,
            'in_progress': TicketStatus.IN_PROGRESS,
            'completed': TicketStatus.COMPLETED,
            'blocked': TicketStatus.NOT_STARTED,
        }
        status = status_map.get(roadmap.status.value, TicketStatus.NOT_STARTED)

        # Get child track IDs
        children = [t.id for t in (roadmap.tracks or [])]

        return RoadmapTicket(
            id=roadmap.id,
            name=roadmap.name,
            status=status,
            parent_ref=None,
            children=children,
            blocked=roadmap.blocked,
            created_at=roadmap.created,
        )


def get_hierarchy_path(root_dir: Path, ticket_id: str) -> List[Dict[str, Any]]:
    """
    Get the hierarchy path from root to ticket.

    Returns a list of dictionaries from roadmap down to the specified ticket,
    each containing id, name, type, and status.

    Args:
        root_dir: Root directory containing .vibey/
        ticket_id: ID of the ticket to get path for

    Returns:
        List of dicts with id, name, type, status for each level

    Example:
        >>> get_hierarchy_path(root, "sqlite-backend-8-task-001")
        [
            {"id": "vibey-framework-v2", "name": "Vibey Framework", "type": "roadmap", "status": "in_progress"},
            {"id": "sqlite-backend", "name": "SQLite Backend", "type": "track", "status": "in_progress"},
            {"id": "sqlite-backend-8", "name": "Serialization Migration", "type": "sprint", "status": "completed"},
            {"id": "sqlite-backend-8-task-001", "name": "Update yaml_loader.py", "type": "task", "status": "completed"},
        ]
    """
    loader = QueryTicketLoader(root_dir)
    HierarchicalTicket.set_loader(loader)

    try:
        ticket = loader.load(ticket_id)
        path_ids = ticket.get_path()

        result = []
        for tid in path_ids:
            t = loader.load(tid)
            ticket_type = _determine_ticket_type(tid)
            result.append({
                "id": t.id,
                "name": t.name,
                "type": ticket_type,
                "status": t.status.value,
            })

        return result
    finally:
        HierarchicalTicket.clear_loaders()


def get_aggregated_commits(root_dir: Path, ticket_id: str) -> List[Dict[str, Any]]:
    """
    Get commits aggregated from ticket and all descendants.

    For parent tickets (roadmap, track, sprint), this aggregates commits
    from all child tickets recursively. For tasks, returns local commits.

    Args:
        root_dir: Root directory containing .vibey/
        ticket_id: ID of the ticket to get commits for

    Returns:
        List of commit dicts with sha, message, author, date

    Example:
        >>> get_aggregated_commits(root, "sqlite-backend-8")
        [
            {"sha": "abc123", "message": "feat: add loader", "author": "dev", "date": "2025-12-01T10:00:00"},
            {"sha": "def456", "message": "feat: add dumper", "author": "dev", "date": "2025-12-02T14:00:00"},
        ]
    """
    loader = QueryTicketLoader(root_dir)
    HierarchicalTicket.set_loader(loader)

    try:
        ticket = loader.load(ticket_id)
        commits = ticket.commits_aggregated

        return [
            {
                "sha": c.sha,
                "message": c.message,
                "author": c.author,
                "date": c.date.isoformat() if c.date else None,
            }
            for c in commits
        ]
    finally:
        HierarchicalTicket.clear_loaders()


def get_effective_requirements(root_dir: Path, ticket_id: str) -> List[Dict[str, Any]]:
    """
    Get effective requirements for a ticket (inherited from ancestors).

    Uses the requirements inheritance system to resolve which requirements
    apply to this ticket based on inheritance modes (INHERIT, OVERRIDE, SKIP).

    Args:
        root_dir: Root directory containing .vibey/
        ticket_id: ID of the ticket to get requirements for

    Returns:
        List of requirement dicts with id, name, type, enforcement_mode

    Example:
        >>> get_effective_requirements(root, "sqlite-backend-8-task-001")
        [
            {"id": "code-review", "name": "Code Review Required", "type": "quality_gate", "enforcement_mode": "mandatory"},
            {"id": "test-coverage", "name": "Test Coverage > 80%", "type": "threshold", "enforcement_mode": "recommended"},
        ]
    """
    loader = QueryTicketLoader(root_dir)
    HierarchicalTicket.set_loader(loader)

    try:
        ticket = loader.load(ticket_id)
        requirements = ticket.requirements_effective

        return [
            {
                "id": getattr(r, 'id', str(i)),
                "name": getattr(r, 'name', str(r)),
                "type": getattr(r, 'type', 'unknown'),
                "enforcement_mode": getattr(r, 'enforcement_mode', 'optional'),
                "enforceable": getattr(r, 'enforceable', False),
            }
            for i, r in enumerate(requirements)
        ]
    finally:
        HierarchicalTicket.clear_loaders()


def query_ticket(root_dir: Path, ticket_id: str) -> Dict[str, Any]:
    """
    Query any ticket by ID with hierarchy-aware details.

    This is a unified query function that works with any ticket type
    (roadmap, track, sprint, task) and includes hierarchy information.

    Args:
        root_dir: Root directory containing .vibey/
        ticket_id: ID of the ticket to query

    Returns:
        Dictionary with ticket details including hierarchy info
    """
    loader = QueryTicketLoader(root_dir)
    HierarchicalTicket.set_loader(loader)

    try:
        ticket = loader.load(ticket_id)
        ticket_type = _determine_ticket_type(ticket_id)

        result = {
            "id": ticket.id,
            "name": ticket.name,
            "type": ticket_type,
            "status": ticket.status.value,
            "blocked": ticket.blocked,
            "parent_ref": ticket.parent_ref,
            "children": ticket.children,
            "hierarchy": {
                "depth": ticket.depth,
                "is_root": ticket.is_ultimate_parent,
                "is_leaf": ticket.is_ultimate_child,
                "path": ticket.get_path(),
            },
            "aggregated": {
                "commits_count": len(ticket.commits_aggregated),
                "requirements_count": len(ticket.requirements_effective),
            },
        }

        # Add timing info if available
        if hasattr(ticket, 'started_at') and ticket.started_at:
            result["started"] = _format_datetime(ticket.started_at)
        if hasattr(ticket, 'completed_at') and ticket.completed_at:
            result["completed"] = _format_datetime(ticket.completed_at)

        return result
    finally:
        HierarchicalTicket.clear_loaders()


def _determine_ticket_type(ticket_id: str) -> str:
    """Determine ticket type from ID pattern."""
    if '-task-' in ticket_id:
        return 'task'
    # Check for sprint pattern (ends with -N where N is number)
    parts = ticket_id.rsplit('-', 1)
    if len(parts) == 2:
        try:
            int(parts[1])
            return 'sprint'
        except ValueError:
            pass
    # Check common roadmap ID patterns
    if 'framework' in ticket_id.lower() or 'roadmap' in ticket_id.lower():
        return 'roadmap'
    return 'track'
