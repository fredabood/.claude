"""
Roadmap Adapter Layer.

Adapter that bridges the MCP server with Vibey's existing roadmap system.
This adapter wraps existing roadmap operations without duplicating business logic.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add framework to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from framework.roadmap.models.common import Status
from framework.roadmap.serialization.yaml_loader import load_task, load_sprint, load_track
from framework.roadmap.serialization.yaml_dumper import save_sprint, save_tasks
from framework.scripts.roadmap_lib.filesystem import FileSystemManager

from ..utils.errors import (
    TaskNotFoundError,
    SprintNotFoundError,
    TrackNotFoundError,
    InvalidStateTransitionError,
)


class RoadmapAdapter:
    """
    Adapter between MCP server and Vibey roadmap system.

    This adapter provides a clean interface for roadmap operations,
    wrapping existing functionality from roadmap-update.py and roadmap-query.py.
    """

    def __init__(self, roadmap_root: str = ".vibey/roadmap"):
        """
        Initialize roadmap adapter.

        Args:
            roadmap_root: Path to roadmap root directory (default: .vibey/roadmap)
        """
        self.root = Path(roadmap_root)
        self.fs = FileSystemManager(self.root)

    # Task Operations

    def start_task(self, task_id: str) -> Dict[str, Any]:
        """
        Start a task (mark as in_progress).

        Args:
            task_id: Task ID (e.g., 'mcp-server-1-task-001')

        Returns:
            Dict with success status and task info

        Raises:
            TaskNotFoundError: If task doesn't exist
            InvalidStateTransitionError: If task can't be started

        Example:
            >>> adapter = RoadmapAdapter()
            >>> result = adapter.start_task("mcp-server-1-task-001")
            >>> print(result)
            {'success': True, 'task_id': 'mcp-server-1-task-001', 'status': 'in_progress'}
        """
        try:
            task_path = self.fs.get_task_path(task_id)
            task = load_task(str(task_path))
        except FileNotFoundError:
            raise TaskNotFoundError(task_id)

        # Validate transition
        if task.status != Status.NOT_STARTED and task.status != Status.PENDING:
            raise InvalidStateTransitionError(
                "task",
                task_id,
                task.status.value,
                "in_progress"
            )

        # Update task
        task.status = Status.IN_PROGRESS
        task.started = datetime.now(timezone.utc)

        # Save task (save_tasks expects a list)
        save_tasks([task], str(task_path))

        # Update sprint progress (via external script)
        self._update_sprint_progress(task.sprint_id)

        return {
            "success": True,
            "task_id": task_id,
            "status": "in_progress",
            "started": task.started.isoformat()
        }

    def complete_task(
        self,
        task_id: str,
        actual_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Complete a task (mark as completed).

        Args:
            task_id: Task ID
            actual_tokens: Actual tokens used (optional)

        Returns:
            Dict with success status and task info

        Raises:
            TaskNotFoundError: If task doesn't exist
            InvalidStateTransitionError: If task can't be completed
        """
        try:
            task_path = self.fs.get_task_path(task_id)
            task = load_task(str(task_path))
        except FileNotFoundError:
            raise TaskNotFoundError(task_id)

        # Validate transition
        if task.status == Status.COMPLETED:
            # Already completed, return success
            return {
                "success": True,
                "task_id": task_id,
                "status": "completed",
                "already_completed": True
            }

        if task.status != Status.IN_PROGRESS:
            raise InvalidStateTransitionError(
                "task",
                task_id,
                task.status.value,
                "completed"
            )

        # Update task
        task.status = Status.COMPLETED
        task.completed = datetime.now(timezone.utc)

        if actual_tokens is not None:
            task.actual_tokens = actual_tokens

        # Save task (save_tasks expects a list)
        save_tasks([task], str(task_path))

        # Update sprint progress
        self._update_sprint_progress(task.sprint_id)

        return {
            "success": True,
            "task_id": task_id,
            "status": "completed",
            "completed": task.completed.isoformat(),
            "actual_tokens": task.actual_tokens
        }

    def query_task(self, task_id: str) -> Dict[str, Any]:
        """
        Query task details.

        Args:
            task_id: Task ID

        Returns:
            Dict with task information

        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        try:
            task_path = self.fs.get_task_path(task_id)
            task = load_task(str(task_path))
        except FileNotFoundError:
            raise TaskNotFoundError(task_id)

        # Convert task to dict representation
        return {
            "id": task.id,
            "sprint_id": task.sprint_id,
            "track_id": task.track_id,
            "roadmap_id": task.roadmap_id,
            "task_type": task.task_type.value,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "blocked": task.blocked,
            "created": task.created.isoformat() if task.created else None,
            "started": task.started.isoformat() if task.started else None,
            "completed": task.completed.isoformat() if task.completed else None,
            "assigned_agent": task.assigned_agent,
            "priority": task.priority.value if task.priority else None,
            "estimated_tokens": task.estimated_tokens,
            "actual_tokens": task.actual_tokens,
            "complexity": task.complexity.value if task.complexity else None,
        }

    # Sprint Operations

    def start_sprint(self, sprint_id: str) -> Dict[str, Any]:
        """
        Start a sprint (mark as in_progress).

        Args:
            sprint_id: Sprint ID (e.g., 'mcp-server-1')

        Returns:
            Dict with success status and sprint info

        Raises:
            SprintNotFoundError: If sprint doesn't exist
            InvalidStateTransitionError: If sprint can't be started
        """
        try:
            sprint_path = self.fs.get_sprint_path(sprint_id)
            sprint = load_sprint(str(sprint_path))
        except FileNotFoundError:
            raise SprintNotFoundError(sprint_id)

        # Validate transition
        if sprint.status != Status.NOT_STARTED:
            raise InvalidStateTransitionError(
                "sprint",
                sprint_id,
                sprint.status.value,
                "in_progress"
            )

        # Update sprint
        sprint.status = Status.IN_PROGRESS
        sprint.started = datetime.now(timezone.utc)

        # Save sprint
        save_sprint(sprint, str(sprint_path))

        # Update track progress
        self._update_track_progress(sprint.track_id)

        return {
            "success": True,
            "sprint_id": sprint_id,
            "status": "in_progress",
            "started": sprint.started.isoformat()
        }

    def complete_sprint(self, sprint_id: str) -> Dict[str, Any]:
        """
        Complete a sprint (mark as completed).

        Args:
            sprint_id: Sprint ID

        Returns:
            Dict with success status and sprint info

        Raises:
            SprintNotFoundError: If sprint doesn't exist
            InvalidStateTransitionError: If sprint can't be completed
        """
        try:
            sprint_path = self.fs.get_sprint_path(sprint_id)
            sprint = load_sprint(str(sprint_path))
        except FileNotFoundError:
            raise SprintNotFoundError(sprint_id)

        # Validate transition (sprint should be in completion_gate_check)
        if sprint.status == Status.COMPLETED:
            # Already completed
            return {
                "success": True,
                "sprint_id": sprint_id,
                "status": "completed",
                "already_completed": True,
                "tasks_completed": sprint.progress.tasks_completed,
                "tasks_total": sprint.progress.tasks_total
            }

        if sprint.status != Status.COMPLETION_GATE_CHECK:
            raise InvalidStateTransitionError(
                "sprint",
                sprint_id,
                sprint.status.value,
                "completed"
            )

        # Update sprint
        sprint.status = Status.COMPLETED
        sprint.completed = datetime.now(timezone.utc)

        # Save sprint
        save_sprint(sprint, str(sprint_path))

        # Update track progress
        self._update_track_progress(sprint.track_id)

        return {
            "success": True,
            "sprint_id": sprint_id,
            "status": "completed",
            "completed": sprint.completed.isoformat(),
            "tasks_completed": sprint.progress.tasks_completed,
            "tasks_total": sprint.progress.tasks_total
        }

    def query_sprint(self, sprint_id: str) -> Dict[str, Any]:
        """
        Query sprint details.

        Args:
            sprint_id: Sprint ID

        Returns:
            Dict with sprint information

        Raises:
            SprintNotFoundError: If sprint doesn't exist
        """
        try:
            sprint_path = self.fs.get_sprint_path(sprint_id)
            sprint = load_sprint(str(sprint_path))
        except FileNotFoundError:
            raise SprintNotFoundError(sprint_id)

        return {
            "id": sprint.id,
            "name": sprint.name,
            "track_id": sprint.track_id,
            "roadmap_id": sprint.roadmap_id,
            "status": sprint.status.value,
            "blocked": sprint.blocked,
            "created": sprint.created.isoformat() if sprint.created else None,
            "started": sprint.started.isoformat() if sprint.started else None,
            "completed": sprint.completed.isoformat() if sprint.completed else None,
            "progress": {
                "development_tasks_total": sprint.progress.development_tasks_total,
                "development_tasks_completed": sprint.progress.development_tasks_completed,
                "completion_gate_tasks_total": sprint.progress.completion_gate_tasks_total,
                "completion_gate_tasks_completed": sprint.progress.completion_gate_tasks_completed,
                "production_gate_tasks_total": sprint.progress.production_gate_tasks_total,
                "production_gate_tasks_completed": sprint.progress.production_gate_tasks_completed,
                "tasks_total": sprint.progress.tasks_total,
                "tasks_completed": sprint.progress.tasks_completed,
                "completion_percent": sprint.progress.completion_percent,
            }
        }

    def refresh_progress(self) -> Dict[str, Any]:
        """
        Refresh all progress calculations and trigger auto-progression.

        Returns:
            Dict with refresh results and any status progressions
        """
        import subprocess

        script_path = self.root.parent.parent / "scripts" / "roadmap-update.py"
        result = subprocess.run(
            ["python3", str(script_path), "--refresh-progress"],
            cwd=str(self.root.parent.parent.parent),
            capture_output=True,
            text=True
        )

        # Parse output for progressions
        progressions = []
        if result.returncode == 0 and result.stdout:
            # Look for progression messages
            for line in result.stdout.split('\n'):
                if "progressed to" in line.lower():
                    # Extract progression info (simple parsing)
                    progressions.append({
                        "message": line.strip()
                    })

        return {
            "success": result.returncode == 0,
            "progressions": progressions,
            "updates": {
                "sprints": "calculated",
                "tracks": "calculated"
            }
        }

    # Track Operations

    def query_track(self, track_id: str) -> Dict[str, Any]:
        """
        Query track details.

        Args:
            track_id: Track ID

        Returns:
            Dict with track information

        Raises:
            TrackNotFoundError: If track doesn't exist
        """
        try:
            track_path = self.fs.get_track_path(track_id)
            track = load_track(str(track_path))
        except FileNotFoundError:
            raise TrackNotFoundError(track_id)

        return {
            "id": track.id,
            "name": track.name,
            "roadmap_id": track.roadmap_id,
            "status": track.status.value,
            "blocked": track.blocked,
            "priority": track.priority.value if track.priority else None,
            "created": track.created.isoformat() if track.created else None,
            "started": track.started.isoformat() if track.started else None,
            "completed": track.completed.isoformat() if track.completed else None,
            "estimated_duration": track.estimated_duration,
            "progress": {
                "sprints_total": track.progress.sprints_total,
                "sprints_completed": track.progress.sprints_completed,
                "tasks_total": track.progress.tasks_total,
                "tasks_completed": track.progress.tasks_completed,
                "completion_percent": track.progress.completion_percent,
            }
        }

    # Query Operations

    def list_blockers(self, object_id: Optional[str] = None) -> list[Dict[str, Any]]:
        """
        List all current blockers across the roadmap.

        Args:
            object_id: Optional filter by specific object ID

        Returns:
            List of blocker information dicts
        """
        import subprocess

        script_path = self.root.parent.parent / "scripts" / "roadmap-query.py"
        cmd = ["python3", str(script_path), "--blockers"]

        if object_id:
            cmd.extend(["--id", object_id])

        result = subprocess.run(
            cmd,
            cwd=str(self.root.parent.parent.parent),
            capture_output=True,
            text=True
        )

        # Parse output for blockers (simplified - would need proper JSON output from script)
        blockers = []
        # This is a placeholder - the actual implementation would parse JSON output
        # from roadmap-query.py --blockers

        return blockers

    def list_dependencies(
        self,
        object_id: str,
        include_satisfied: bool = False
    ) -> list[Dict[str, Any]]:
        """
        List dependencies for a specific object.

        Args:
            object_id: Object ID to query
            include_satisfied: Include satisfied dependencies

        Returns:
            List of dependency information dicts
        """
        # Try to load the object and get its dependencies
        try:
            # Check if it's a task
            task_path = self.fs.get_task_path(object_id)
            task = load_task(str(task_path))

            dependencies = []
            for dep in task.depends_on:
                if include_satisfied or not dep.is_satisfied():
                    dependencies.append({
                        "dependency_id": dep.blocker_id,
                        "dependency_type": dep.blocker_type.value,
                        "current_status": dep.current_status.value if dep.current_status else None,
                        "required_status": dep.required_status.value if dep.required_status else None,
                        "is_satisfied": dep.is_satisfied(),
                        "reason": None  # Tasks don't have reason field
                    })

            return dependencies

        except FileNotFoundError:
            pass

        try:
            # Check if it's a sprint
            sprint_path = self.fs.get_sprint_path(object_id)
            sprint = load_sprint(str(sprint_path))

            dependencies = []
            for dep in sprint.depends_on:
                if include_satisfied or not dep.is_satisfied():
                    dependencies.append({
                        "dependency_id": dep.blocker_id,
                        "dependency_type": dep.blocker_type.value,
                        "current_status": dep.current_status.value if dep.current_status else None,
                        "required_status": dep.required_status.value if dep.required_status else None,
                        "is_satisfied": dep.is_satisfied(),
                        "reason": None
                    })

            return dependencies

        except FileNotFoundError:
            pass

        try:
            # Check if it's a track
            track_path = self.fs.get_track_path(object_id)
            track = load_track(str(track_path))

            dependencies = []
            for dep in track.depends_on:
                if include_satisfied or not dep.is_satisfied():
                    dependencies.append({
                        "dependency_id": dep.blocker_id,
                        "dependency_type": dep.blocker_type.value,
                        "current_status": dep.current_status.value if dep.current_status else None,
                        "required_status": dep.required_status.value if dep.required_status else None,
                        "is_satisfied": dep.is_satisfied(),
                        "reason": None
                    })

            return dependencies

        except FileNotFoundError:
            raise TaskNotFoundError(object_id)  # Generic "not found"

    def get_roadmap_status(self) -> Dict[str, Any]:
        """
        Get overall roadmap status summary.

        Returns:
            Dict with roadmap status information
        """
        from roadmap.serialization.yaml_loader import load_roadmap

        roadmap_path = self.root / "roadmap.yaml"
        roadmap = load_roadmap(str(roadmap_path))

        # Get active sprints
        active_sprints = []
        for track_summary in roadmap.tracks:
            # Load full track to get sprints
            try:
                track_path = self.fs.get_track_path(track_summary.id)
                track = load_track(str(track_path))

                for sprint_summary in track.sprints:
                    if sprint_summary.status in [Status.IN_PROGRESS, Status.COMPLETION_GATE_CHECK]:
                        active_sprints.append({
                            "id": sprint_summary.id,
                            "name": sprint_summary.name,
                            "status": sprint_summary.status.value,
                            "completion_percent": sprint_summary.tasks_count  # Placeholder
                        })
            except:
                pass

        # Count blockers
        blockers_count = sum(1 for t in roadmap.tracks if t.blocked)

        return {
            "id": roadmap.id,
            "name": roadmap.name,
            "version": roadmap.version,
            "status": roadmap.status.value,
            "blocked": roadmap.blocked,
            "progress": {
                "tracks_total": roadmap.progress.tracks_total,
                "tracks_completed": roadmap.progress.tracks_completed,
                "sprints_total": roadmap.progress.sprints_total,
                "sprints_completed": roadmap.progress.sprints_completed,
                "tasks_total": roadmap.progress.tasks_total,
                "tasks_completed": roadmap.progress.tasks_completed,
                "completion_percent": roadmap.progress.completion_percent,
            },
            "active_sprints": active_sprints,
            "blockers_count": blockers_count
        }

    # Helper Methods

    def _update_sprint_progress(self, sprint_id: str) -> None:
        """
        Update sprint progress by calling roadmap-update.py script.

        This leverages the existing progress calculation logic.

        Args:
            sprint_id: Sprint ID to update
        """
        # Import here to avoid circular dependencies
        import subprocess

        script_path = self.root.parent.parent / "scripts" / "roadmap-update.py"
        result = subprocess.run(
            ["python3", str(script_path), "--refresh-progress"],
            cwd=str(self.root.parent.parent.parent),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            # Log error but don't fail (progress update is best-effort)
            print(f"Warning: Progress update failed: {result.stderr}", file=sys.stderr)

    def _update_track_progress(self, track_id: str) -> None:
        """
        Update track progress by calling roadmap-update.py script.

        Args:
            track_id: Track ID to update
        """
        self._update_sprint_progress(track_id)  # Same script handles both
