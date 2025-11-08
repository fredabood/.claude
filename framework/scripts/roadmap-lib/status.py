"""
Status progression utilities for roadmap state.

Handles automatic status progression based on completion conditions.
"""

from typing import Optional
from pathlib import Path
from datetime import datetime
import sys

# Add framework to path
framework_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_root))

from roadmap.models import (
    Roadmap, Track, Sprint, Task,
    Status, TaskStatus,
)
from roadmap.serialization import load_roadmap, load_track, load_sprint, load_tasks, save_sprint
from filesystem import FileSystemManager


class StatusManager:
    """Manages automatic status progression."""

    def __init__(self, root_dir: Optional[Path] = None):
        """
        Initialize status manager.

        Args:
            root_dir: Root directory (defaults to current working directory)
        """
        self.fs = FileSystemManager(root_dir)

    def can_progress_sprint(self, sprint: Sprint, target_status: Status) -> tuple[bool, str]:
        """
        Check if sprint can progress to target status.

        Args:
            sprint: Sprint object
            target_status: Target status to check

        Returns:
            Tuple of (can_progress: bool, reason: str)
        """
        if target_status == Status.COMPLETION_GATE_CHECK:
            # Can progress if all development tasks are completed
            if sprint.all_development_tasks_completed():
                return True, "All development tasks completed"
            else:
                return False, "Not all development tasks completed"

        elif target_status == Status.COMPLETED:
            # Can progress if in completion_gate_check and all completion gates passed
            if sprint.status != Status.COMPLETION_GATE_CHECK:
                return False, "Sprint must be in completion_gate_check status first"

            if sprint.all_completion_gates_passed():
                return True, "All completion gates passed"
            else:
                return False, "Not all completion gates passed"

        elif target_status == Status.PRODUCTION_GATE_CHECK:
            # Can progress if completed
            if sprint.status != Status.COMPLETED:
                return False, "Sprint must be completed first"

            return True, "Sprint is completed, ready for production gates"

        elif target_status == Status.PRODUCTION_READY:
            # Can progress if in production_gate_check and all production gates passed
            if sprint.status != Status.PRODUCTION_GATE_CHECK:
                return False, "Sprint must be in production_gate_check status first"

            if sprint.all_production_gates_passed():
                return True, "All production gates passed"
            else:
                return False, "Not all production gates passed"

        elif target_status == Status.DEPLOYED:
            # Can progress if production ready
            if sprint.status != Status.PRODUCTION_READY:
                return False, "Sprint must be production_ready first"

            return True, "Sprint is production ready, can be deployed"

        else:
            return False, f"Invalid target status: {target_status}"

    def progress_sprint_status(self, sprint: Sprint) -> tuple[bool, Optional[Status], str]:
        """
        Automatically progress sprint status if conditions are met.

        Args:
            sprint: Sprint object

        Returns:
            Tuple of (progressed: bool, new_status: Optional[Status], message: str)
        """
        current_status = sprint.status

        # Define progression path
        if current_status == Status.IN_PROGRESS:
            can_progress, reason = self.can_progress_sprint(sprint, Status.COMPLETION_GATE_CHECK)
            if can_progress:
                return True, Status.COMPLETION_GATE_CHECK, reason
            else:
                return False, None, f"Cannot progress: {reason}"

        elif current_status == Status.COMPLETION_GATE_CHECK:
            can_progress, reason = self.can_progress_sprint(sprint, Status.COMPLETED)
            if can_progress:
                # Also move to production_gate_check immediately
                return True, Status.PRODUCTION_GATE_CHECK, "Completed and ready for production gates"
            else:
                return False, None, f"Cannot progress: {reason}"

        elif current_status == Status.COMPLETED:
            # Should not normally be in this state (should go directly to production_gate_check)
            can_progress, reason = self.can_progress_sprint(sprint, Status.PRODUCTION_GATE_CHECK)
            if can_progress:
                return True, Status.PRODUCTION_GATE_CHECK, reason
            else:
                return False, None, f"Cannot progress: {reason}"

        elif current_status == Status.PRODUCTION_GATE_CHECK:
            can_progress, reason = self.can_progress_sprint(sprint, Status.PRODUCTION_READY)
            if can_progress:
                return True, Status.PRODUCTION_READY, reason
            else:
                return False, None, f"Cannot progress: {reason}"

        else:
            return False, None, f"No automatic progression from status: {current_status}"

    def can_progress_track(self, track: Track, target_status: Status) -> tuple[bool, str]:
        """
        Check if track can progress to target status.

        Args:
            track: Track object
            target_status: Target status to check

        Returns:
            Tuple of (can_progress: bool, reason: str)
        """
        if target_status == Status.COMPLETED:
            # All sprints must be completed
            incomplete = [s for s in track.sprints if s.status not in [Status.COMPLETED, Status.PRODUCTION_GATE_CHECK, Status.PRODUCTION_READY, Status.DEPLOYED]]
            if len(incomplete) == 0:
                return True, "All sprints completed or beyond"
            else:
                return False, f"{len(incomplete)} sprints not completed"

        elif target_status == Status.PRODUCTION_READY:
            # All sprints must be production_ready or deployed
            not_ready = [s for s in track.sprints if s.status not in [Status.PRODUCTION_READY, Status.DEPLOYED]]
            if len(not_ready) == 0:
                return True, "All sprints production ready or deployed"
            else:
                return False, f"{len(not_ready)} sprints not production ready"

        else:
            return False, f"Invalid target status: {target_status}"

    def progress_track_status(self, track: Track) -> tuple[bool, Optional[Status], str]:
        """
        Automatically progress track status if conditions are met.

        Args:
            track: Track object

        Returns:
            Tuple of (progressed: bool, new_status: Optional[Status], message: str)
        """
        current_status = track.status

        if current_status == Status.IN_PROGRESS:
            can_progress, reason = self.can_progress_track(track, Status.COMPLETED)
            if can_progress:
                return True, Status.COMPLETED, reason
            else:
                return False, None, f"Cannot progress: {reason}"

        elif current_status == Status.COMPLETED:
            can_progress, reason = self.can_progress_track(track, Status.PRODUCTION_READY)
            if can_progress:
                return True, Status.PRODUCTION_READY, reason
            else:
                return False, None, f"Cannot progress: {reason}"

        else:
            return False, None, f"No automatic progression from status: {current_status}"

    def progress_roadmap_status(self, roadmap: Roadmap) -> tuple[bool, Optional[Status], str]:
        """
        Automatically progress roadmap status if conditions are met.

        Args:
            roadmap: Roadmap object

        Returns:
            Tuple of (progressed: bool, new_status: Optional[Status], message: str)
        """
        current_status = roadmap.status

        if current_status == Status.IN_PROGRESS:
            # Check if all tracks are completed
            incomplete = [t for t in roadmap.tracks if t.status != Status.COMPLETED and t.status != Status.PRODUCTION_READY and t.status != Status.DEPLOYED]
            if len(incomplete) == 0:
                return True, Status.COMPLETED, "All tracks completed"
            else:
                return False, None, f"{len(incomplete)} tracks not completed"

        elif current_status == Status.COMPLETED:
            # Check if all tracks are production ready
            not_ready = [t for t in roadmap.tracks if t.status != Status.PRODUCTION_READY and t.status != Status.DEPLOYED]
            if len(not_ready) == 0:
                return True, Status.PRODUCTION_READY, "All tracks production ready"
            else:
                return False, None, f"{len(not_ready)} tracks not production ready"

        else:
            return False, None, f"No automatic progression from status: {current_status}"


def can_progress_status(
    obj: any,
    target_status: Status,
    root_dir: Optional[Path] = None
) -> tuple[bool, str]:
    """
    Check if object can progress to target status (convenience function).

    Args:
        obj: Sprint, Track, or Roadmap object
        target_status: Target status to check
        root_dir: Root directory (defaults to current working directory)

    Returns:
        Tuple of (can_progress: bool, reason: str)
    """
    manager = StatusManager(root_dir)

    if isinstance(obj, Sprint):
        return manager.can_progress_sprint(obj, target_status)
    elif isinstance(obj, Track):
        return manager.can_progress_track(obj, target_status)
    elif isinstance(obj, Roadmap):
        # Roadmap doesn't have granular can_progress checks
        return False, "Use progress_status_if_ready for roadmap"
    else:
        return False, "Unknown object type"


def progress_status_if_ready(
    obj: any,
    root_dir: Optional[Path] = None
) -> tuple[bool, Optional[Status], str]:
    """
    Automatically progress status if conditions are met (convenience function).

    Args:
        obj: Sprint, Track, or Roadmap object
        root_dir: Root directory (defaults to current working directory)

    Returns:
        Tuple of (progressed: bool, new_status: Optional[Status], message: str)
    """
    manager = StatusManager(root_dir)

    if isinstance(obj, Sprint):
        return manager.progress_sprint_status(obj)
    elif isinstance(obj, Track):
        return manager.progress_track_status(obj)
    elif isinstance(obj, Roadmap):
        return manager.progress_roadmap_status(obj)
    else:
        return False, None, "Unknown object type"
