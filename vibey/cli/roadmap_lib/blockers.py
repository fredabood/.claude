"""
Blocker computation utilities for roadmap state.

Computes blockers for objects based on dependencies and their statuses.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pathlib import Path
import sys

# Add framework to path
framework_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_root))

from vibey.roadmap.models import (
    Roadmap, Track, Sprint, Task,
    Blocker, TrackBlocker, TaskBlocker,
    Status, TaskStatus,
)
from vibey.roadmap.serialization import load_roadmap, load_track, load_sprint, load_tasks
from .filesystem import FileSystemManager


class BlockerComputer:
    """Computes blockers for roadmap objects."""

    def __init__(self, root_dir: Optional[Path] = None):
        """
        Initialize blocker computer.

        Args:
            root_dir: Root directory (defaults to current working directory)
        """
        self.fs = FileSystemManager(root_dir)

    def compute_roadmap_blockers(self, roadmap: Roadmap) -> List[Blocker]:
        """
        Compute blockers for a roadmap.

        Args:
            roadmap: Roadmap object

        Returns:
            List of Blocker objects
        """
        blockers = []

        for dep in roadmap.dependencies:
            # External dependencies - check status
            if dep.status != "completed":
                blocker = Blocker(
                    dependency_id=dep.name,
                    dependency_type="external",
                    current_status=dep.status,
                    required_status="completed",
                    blocking_since=datetime.now(timezone.utc),  # Could be more precise
                )
                blockers.append(blocker)

        return blockers

    def compute_track_blockers(self, track: Track) -> List[TrackBlocker]:
        """
        Compute blockers for a track.

        Args:
            track: Track object

        Returns:
            List of TrackBlocker objects
        """
        blockers = []

        for dep in track.dependencies:
            # Load dependency and check status
            current_status = self._get_object_status(dep.target_id, dep.type.value)

            if current_status is None:
                # Dependency not found - this is a blocker
                blocker = TrackBlocker(
                    dependency_id=dep.target_id,
                    dependency_type=dep.type.value,
                    current_status="not_found",
                    required_status=dep.target_status,
                    blocking_since=datetime.now(timezone.utc),
                )
                blockers.append(blocker)
            elif not self._status_satisfied(current_status, dep.target_status):
                # Dependency not satisfied
                blocker = TrackBlocker(
                    dependency_id=dep.target_id,
                    dependency_type=dep.type.value,
                    current_status=current_status,
                    required_status=dep.target_status,
                    blocking_since=datetime.now(timezone.utc),
                )
                blockers.append(blocker)

        return blockers

    def compute_sprint_blockers(self, sprint: Sprint) -> List[SprintBlocker]:
        """
        Compute blockers for a sprint.

        Args:
            sprint: Sprint object

        Returns:
            List of SprintBlocker objects
        """
        blockers = []

        for dep in sprint.development_gates:
            # Load dependency and check status
            current_status = self._get_object_status(dep.target_id, dep.type.value)

            if current_status is None:
                blocker = SprintBlocker(
                    dependency_id=dep.target_id,
                    dependency_type=dep.type.value,
                    current_status="not_found",
                    required_status=dep.target_status,
                    blocking_since=datetime.now(timezone.utc),
                )
                blockers.append(blocker)
            elif not self._status_satisfied(current_status, dep.target_status):
                blocker = SprintBlocker(
                    dependency_id=dep.target_id,
                    dependency_type=dep.type.value,
                    current_status=current_status,
                    required_status=dep.target_status,
                    blocking_since=datetime.now(timezone.utc),
                )
                blockers.append(blocker)

        return blockers

    def compute_task_blockers(self, task: Task) -> List[TaskBlocker]:
        """
        Compute blockers for a task.

        Args:
            task: Task object

        Returns:
            List of TaskBlocker objects
        """
        blockers = []

        for dep in task.dependencies:
            # Load dependency and check status
            current_status = self._get_object_status(dep.target_id, dep.type.value)

            if current_status is None:
                blocker = TaskBlocker(
                    dependency_id=dep.target_id,
                    dependency_type=dep.type.value,
                    current_status="not_found",
                    required_status=dep.target_status,
                    blocking_since=datetime.now(timezone.utc),
                )
                blockers.append(blocker)
            elif not self._status_satisfied(current_status, dep.target_status):
                blocker = TaskBlocker(
                    dependency_id=dep.target_id,
                    dependency_type=dep.type.value,
                    current_status=current_status,
                    required_status=dep.target_status,
                    blocking_since=datetime.now(timezone.utc),
                )
                blockers.append(blocker)

        return blockers

    def _get_object_status(self, object_id: str, object_type: str) -> Optional[str]:
        """
        Get the current status of an object.

        Args:
            object_id: ID of object
            object_type: Type of object (track, sprint, task, external)

        Returns:
            Current status string, or None if not found
        """
        try:
            if object_type == "track":
                track_path = self.fs.get_track_path(object_id)
                if not track_path.exists():
                    return None
                track = load_track(track_path)
                return track.status.value

            elif object_type == "sprint":
                sprint_path = self.fs.get_sprint_path(object_id)
                if not sprint_path.exists():
                    return None
                sprint = load_sprint(sprint_path)
                return sprint.status.value

            elif object_type == "task":
                # Tasks are in batch files, need to find the sprint
                # Extract sprint ID from task ID (e.g., backend-1-task-001 -> backend-1)
                parts = object_id.split('-')
                if len(parts) < 3:
                    return None

                # Handle track-scoped sprint IDs (e.g., backend-1)
                sprint_id = '-'.join(parts[:2])

                tasks_path = self.fs.get_tasks_path(sprint_id)
                if not tasks_path.exists():
                    return None

                tasks = load_tasks(tasks_path)
                for task in tasks:
                    if task.id == object_id:
                        return task.status.value

                return None

            elif object_type == "external":
                # External dependencies need to be checked in roadmap
                roadmap_path = self.fs.get_roadmap_path()
                if not roadmap_path.exists():
                    return None
                roadmap = load_roadmap(roadmap_path)

                for dep in roadmap.dependencies:
                    if dep.name == object_id:
                        return dep.status

                return None

            else:
                return None

        except Exception:
            return None

    def _status_satisfied(self, current_status: str, required_status: str) -> bool:
        """
        Check if current status satisfies required status.

        Status progression order:
        not_started < in_progress < paused < completion_gate_check < completed <
        production_gate_check < production_ready < deployed

        Args:
            current_status: Current status
            required_status: Required status

        Returns:
            True if satisfied, False otherwise
        """
        status_order = [
            "not_started",
            "in_progress",
            "paused",
            "completion_gate_check",
            "completed",
            "production_gate_check",
            "production_ready",
            "deployed",
        ]

        try:
            current_idx = status_order.index(current_status)
            required_idx = status_order.index(required_status)
            return current_idx >= required_idx
        except ValueError:
            # Status not in list - check exact match
            return current_status == required_status


def compute_blockers(
    obj: Any,
    root_dir: Optional[Path] = None
) -> List[Any]:
    """
    Compute blockers for an object (convenience function).

    Args:
        obj: Roadmap, Track, Sprint, or Task object
        root_dir: Root directory (defaults to current working directory)

    Returns:
        List of blocker objects
    """
    computer = BlockerComputer(root_dir)

    if isinstance(obj, Roadmap):
        return computer.compute_roadmap_blockers(obj)
    elif isinstance(obj, Track):
        return computer.compute_track_blockers(obj)
    elif isinstance(obj, Sprint):
        return computer.compute_sprint_blockers(obj)
    elif isinstance(obj, Task):
        return computer.compute_task_blockers(obj)
    else:
        return []


def is_blocked(
    obj: Any,
    root_dir: Optional[Path] = None
) -> bool:
    """
    Check if an object is blocked.

    Args:
        obj: Roadmap, Track, Sprint, or Task object
        root_dir: Root directory (defaults to current working directory)

    Returns:
        True if blocked, False otherwise
    """
    blockers = compute_blockers(obj, root_dir)
    return len(blockers) > 0
