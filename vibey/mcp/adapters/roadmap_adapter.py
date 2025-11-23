"""
Roadmap Adapter Layer.

Adapter that bridges the MCP server with Vibey's existing roadmap system.
This adapter delegates to vibey.operations.roadmap to ensure CLI <-> MCP parity.

IMPORTANT: This adapter does NOT implement business logic. It delegates to
the operations library, which is the single source of truth for roadmap
operations shared by both CLI and MCP server.
"""

import sys
from io import StringIO
from pathlib import Path
from typing import Dict, Any, Optional

# Import shared operations library - SINGLE SOURCE OF TRUTH
from vibey.operations.roadmap import (
    # Query operations
    query_roadmap_summary,
    query_track_details,
    query_sprint_details,
    query_task_details,
    query_blockers,
    query_dependencies,
    # Update operations
    complete_task as ops_complete_task,
    start_task as ops_start_task,
    assign_task as ops_assign_task,
    start_sprint as ops_start_sprint,
    complete_sprint as ops_complete_sprint,
    complete_track as ops_complete_track,
    refresh_progress as ops_refresh_progress,
    recalculate_all as ops_recalculate_all,
)

from ..utils.errors import (
    TaskNotFoundError,
    SprintNotFoundError,
    TrackNotFoundError,
    InvalidStateTransitionError,
    VibeyMCPError,
)


class RoadmapAdapter:
    """
    Adapter between MCP server and Vibey roadmap system.

    This adapter delegates all operations to vibey.operations.roadmap,
    ensuring that CLI and MCP server use identical business logic.

    The adapter's role is purely to:
    1. Convert MCP inputs to operations inputs
    2. Capture operation outputs (stdout, return codes)
    3. Convert outputs to MCP response format
    """

    def __init__(self, roadmap_root: str = ".vibey/roadmap"):
        """
        Initialize roadmap adapter.

        Args:
            roadmap_root: Path to roadmap root directory (default: .vibey/roadmap)
                         Note: Operations expect the PROJECT root, so we go up one level
        """
        # Operations expect project root (containing .vibey/), not .vibey/roadmap
        roadmap_path = Path(roadmap_root)
        if roadmap_path.name == "roadmap" and roadmap_path.parent.name == ".vibey":
            # .vibey/roadmap -> go up two levels to project root
            self.root = roadmap_path.parent.parent
        elif roadmap_path.name == ".vibey":
            # .vibey -> go up one level
            self.root = roadmap_path.parent
        else:
            # Assume it's already the project root
            self.root = roadmap_path

    def _capture_output(self, func, *args, **kwargs) -> tuple[Any, str]:
        """
        Capture stdout from an operation.

        Operations print messages directly. This wrapper captures them
        for inclusion in MCP responses.

        Returns:
            Tuple of (return_value, captured_output)
        """
        old_stdout = sys.stdout
        sys.stdout = captured = StringIO()
        try:
            result = func(*args, **kwargs)
            return result, captured.getvalue()
        finally:
            sys.stdout = old_stdout

    # =========================================================================
    # Query Operations - Delegate to vibey.operations.roadmap.query
    # =========================================================================

    def get_roadmap_status(self) -> Dict[str, Any]:
        """
        Get overall roadmap status summary.

        Delegates to: query_roadmap_summary()

        Returns:
            Dict with roadmap status information
        """
        result = query_roadmap_summary(self.root)

        if "error" in result:
            raise VibeyMCPError(result["error"])

        return result

    def query_task(self, task_id: str) -> Dict[str, Any]:
        """
        Query task details.

        Delegates to: query_task_details()

        Args:
            task_id: Task ID

        Returns:
            Dict with task information
        """
        result = query_task_details(self.root, task_id)

        if "error" in result:
            raise TaskNotFoundError(task_id)

        return result

    def query_sprint(self, sprint_id: str) -> Dict[str, Any]:
        """
        Query sprint details.

        Delegates to: query_sprint_details()

        Args:
            sprint_id: Sprint ID

        Returns:
            Dict with sprint information
        """
        result = query_sprint_details(self.root, sprint_id)

        if "error" in result:
            raise SprintNotFoundError(sprint_id)

        return result

    def query_track(self, track_id: str) -> Dict[str, Any]:
        """
        Query track details.

        Delegates to: query_track_details()

        Args:
            track_id: Track ID

        Returns:
            Dict with track information
        """
        result = query_track_details(self.root, track_id)

        if "error" in result:
            raise TrackNotFoundError(track_id)

        return result

    def list_blockers(self, object_id: Optional[str] = None) -> Dict[str, Any]:
        """
        List blockers for a specific object or entire roadmap.

        Delegates to: query_blockers()

        Args:
            object_id: Optional filter by specific object ID

        Returns:
            Dict with blocker information
        """
        return query_blockers(self.root, object_id)

    def list_dependencies(self, object_id: Optional[str] = None) -> Dict[str, Any]:
        """
        List dependency graph information.

        Delegates to: query_dependencies()

        Args:
            object_id: Optional filter by specific object ID (unused currently)

        Returns:
            Dict with dependency information
        """
        return query_dependencies(self.root)

    # =========================================================================
    # Update Operations - Delegate to vibey.operations.roadmap.update
    # =========================================================================

    def start_task(self, task_id: str) -> Dict[str, Any]:
        """
        Start a task (mark as in_progress).

        Delegates to: start_task()

        Args:
            task_id: Task ID (e.g., 'mcp-server-1-task-001')

        Returns:
            Dict with success status and task info
        """
        exit_code, output = self._capture_output(
            ops_start_task, self.root, task_id
        )

        if exit_code != 0:
            # Parse error message from output
            error_msg = output.strip().replace("❌ ", "")
            if "not found" in error_msg.lower():
                raise TaskNotFoundError(task_id)
            raise InvalidStateTransitionError("task", task_id, "unknown", "in_progress")

        return {
            "success": True,
            "task_id": task_id,
            "status": "in_progress",
            "message": output.strip()
        }

    def complete_task(
        self,
        task_id: str,
        actual_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Complete a task (mark as completed).

        Delegates to: complete_task()

        Args:
            task_id: Task ID
            actual_tokens: Actual tokens used (optional, not currently passed to ops)

        Returns:
            Dict with success status and task info
        """
        exit_code, output = self._capture_output(
            ops_complete_task, self.root, task_id
        )

        if exit_code != 0:
            error_msg = output.strip().replace("❌ ", "")
            if "not found" in error_msg.lower():
                raise TaskNotFoundError(task_id)
            if "cannot complete" in error_msg.lower():
                raise InvalidStateTransitionError("task", task_id, "unknown", "completed")
            raise VibeyMCPError(error_msg)

        return {
            "success": True,
            "task_id": task_id,
            "status": "completed",
            "message": output.strip(),
            "actual_tokens": actual_tokens
        }

    def assign_task(self, task_id: str, agent: str) -> Dict[str, Any]:
        """
        Assign a task to an agent.

        Delegates to: assign_task()

        Args:
            task_id: Task ID
            agent: Agent name to assign

        Returns:
            Dict with success status
        """
        exit_code, output = self._capture_output(
            ops_assign_task, self.root, task_id, agent
        )

        if exit_code != 0:
            error_msg = output.strip().replace("❌ ", "")
            if "not found" in error_msg.lower():
                raise TaskNotFoundError(task_id)
            raise VibeyMCPError(error_msg)

        return {
            "success": True,
            "task_id": task_id,
            "assigned_agent": agent,
            "message": output.strip()
        }

    def start_sprint(self, sprint_id: str) -> Dict[str, Any]:
        """
        Start a sprint (mark as in_progress).

        Delegates to: start_sprint()

        Args:
            sprint_id: Sprint ID (e.g., 'mcp-server-1')

        Returns:
            Dict with success status and sprint info
        """
        exit_code, output = self._capture_output(
            ops_start_sprint, self.root, sprint_id
        )

        if exit_code != 0:
            error_msg = output.strip().replace("❌ ", "")
            if "not found" in error_msg.lower():
                raise SprintNotFoundError(sprint_id)
            raise InvalidStateTransitionError("sprint", sprint_id, "unknown", "in_progress")

        return {
            "success": True,
            "sprint_id": sprint_id,
            "status": "in_progress",
            "message": output.strip()
        }

    def complete_sprint(self, sprint_id: str) -> Dict[str, Any]:
        """
        Complete a sprint (mark as completed).

        Delegates to: complete_sprint()

        Args:
            sprint_id: Sprint ID

        Returns:
            Dict with success status and sprint info
        """
        exit_code, output = self._capture_output(
            ops_complete_sprint, self.root, sprint_id
        )

        if exit_code != 0:
            error_msg = output.strip().replace("❌ ", "")
            if "not found" in error_msg.lower():
                raise SprintNotFoundError(sprint_id)
            raise InvalidStateTransitionError("sprint", sprint_id, "unknown", "completed")

        return {
            "success": True,
            "sprint_id": sprint_id,
            "status": "completed",
            "message": output.strip()
        }

    def complete_track(self, track_id: str) -> Dict[str, Any]:
        """
        Complete a track (mark as completed).

        Delegates to: complete_track()

        Args:
            track_id: Track ID

        Returns:
            Dict with success status and track info
        """
        exit_code, output = self._capture_output(
            ops_complete_track, self.root, track_id
        )

        if exit_code != 0:
            error_msg = output.strip().replace("❌ ", "")
            if "not found" in error_msg.lower():
                raise TrackNotFoundError(track_id)
            raise InvalidStateTransitionError("track", track_id, "unknown", "completed")

        return {
            "success": True,
            "track_id": track_id,
            "status": "completed",
            "message": output.strip()
        }

    def refresh_progress(self) -> Dict[str, Any]:
        """
        Refresh all progress calculations.

        Delegates to: refresh_progress() or recalculate_all()

        Returns:
            Dict with refresh results
        """
        exit_code, output = self._capture_output(
            ops_recalculate_all, self.root
        )

        return {
            "success": exit_code == 0,
            "message": output.strip() if output else "Progress refreshed"
        }
