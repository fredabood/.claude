"""
Unified activity logging for roadmap operations.

Provides a single interface for logging all roadmap activities, bridging:
- Detailed audit trail (field-level changes with old/new values)
- High-level activity log (ActivityType-based events)

All operations should use this module for consistent activity tracking.
"""

from pathlib import Path
from typing import Optional, Any, Dict
from datetime import datetime, timezone

from vibey.roadmap.models.common import ActivityType
from vibey.operations.roadmap.audit_trail import (
    AuditTrailManager,
    log_status_change,
    log_progress_change,
    AuditEntry,
)


class UnifiedActivityLog:
    """
    Unified activity logging for roadmap operations.

    Provides a consistent interface for logging:
    - Status changes (task started/completed, sprint transitions, etc.)
    - Progress updates (completion percentages, task counts)
    - Quality gate results
    - Blockers added/resolved
    - General activities

    Logs to both:
    - Audit trail: Detailed, field-level changes for accountability
    - Activity log: High-level events for user visibility
    """

    def __init__(self, root_dir: Path):
        """
        Initialize unified activity log.

        Args:
            root_dir: Project root directory containing .vibey/
        """
        self.root_dir = Path(root_dir)
        self.audit_manager = AuditTrailManager(root_dir)

    # =========================================================================
    # Task Activities
    # =========================================================================

    def log_task_started(
        self,
        task_id: str,
        assigned_agent: Optional[str] = None,
        reason: str = "Task started via CLI",
    ) -> AuditEntry:
        """
        Log a task being started.

        Args:
            task_id: ID of the task
            assigned_agent: Agent assigned to the task
            reason: Reason for starting

        Returns:
            Audit entry created
        """
        return log_status_change(
            root_dir=self.root_dir,
            object_type="task",
            object_id=task_id,
            old_status="not_started",
            new_status="in_progress",
            reason=reason,
        )

    def log_task_completed(
        self,
        task_id: str,
        old_status: str = "in_progress",
        reason: str = "Task completed via CLI",
    ) -> AuditEntry:
        """
        Log a task being completed.

        Args:
            task_id: ID of the task
            old_status: Previous status
            reason: Reason for completion

        Returns:
            Audit entry created
        """
        return log_status_change(
            root_dir=self.root_dir,
            object_type="task",
            object_id=task_id,
            old_status=old_status,
            new_status="completed",
            reason=reason,
        )

    def log_task_blocked(
        self,
        task_id: str,
        blocker_id: str,
        reason: str = "Task blocked by dependency",
    ) -> AuditEntry:
        """
        Log a task being blocked.

        Args:
            task_id: ID of the task
            blocker_id: ID of the blocking item
            reason: Reason for blocking

        Returns:
            Audit entry created
        """
        return self.audit_manager.log_change(
            object_type="task",
            object_id=task_id,
            field="blocked",
            old_value=False,
            new_value=True,
            reason=f"{reason}: blocked by {blocker_id}",
        )

    def log_task_unblocked(
        self,
        task_id: str,
        reason: str = "Blocking dependency resolved",
    ) -> AuditEntry:
        """
        Log a task being unblocked.

        Args:
            task_id: ID of the task
            reason: Reason for unblocking

        Returns:
            Audit entry created
        """
        return self.audit_manager.log_change(
            object_type="task",
            object_id=task_id,
            field="blocked",
            old_value=True,
            new_value=False,
            reason=reason,
        )

    def log_task_added(
        self,
        task_id: str,
        sprint_id: str,
        title: str,
        reason: str = "Task created via CLI",
    ) -> AuditEntry:
        """
        Log a new task being created.

        Args:
            task_id: ID of the new task
            sprint_id: ID of the parent sprint
            title: Title of the task
            reason: Reason for creation

        Returns:
            Audit entry created
        """
        return self.audit_manager.log_change(
            object_type="task",
            object_id=task_id,
            field="created",
            old_value=None,
            new_value=f"Sprint: {sprint_id}, Title: {title}",
            reason=reason,
            source="cli",
        )

    # =========================================================================
    # Sprint Activities
    # =========================================================================

    def log_sprint_added(
        self,
        sprint_id: str,
        track_id: str,
        name: str,
        reason: str = "Sprint created via CLI",
    ) -> AuditEntry:
        """
        Log a new sprint being created.

        Args:
            sprint_id: ID of the new sprint
            track_id: ID of the parent track
            name: Name of the sprint
            reason: Reason for creation

        Returns:
            Audit entry created
        """
        return self.audit_manager.log_change(
            object_type="sprint",
            object_id=sprint_id,
            field="created",
            old_value=None,
            new_value=f"Track: {track_id}, Name: {name}",
            reason=reason,
            source="cli",
        )

    def log_sprint_started(
        self,
        sprint_id: str,
        reason: str = "Sprint started via CLI",
    ) -> AuditEntry:
        """
        Log a sprint being started.

        Args:
            sprint_id: ID of the sprint
            reason: Reason for starting

        Returns:
            Audit entry created
        """
        return log_status_change(
            root_dir=self.root_dir,
            object_type="sprint",
            object_id=sprint_id,
            old_status="not_started",
            new_status="in_progress",
            reason=reason,
        )

    def log_sprint_completed(
        self,
        sprint_id: str,
        old_status: str = "in_progress",
        reason: str = "Sprint completed via CLI",
    ) -> AuditEntry:
        """
        Log a sprint being completed.

        Args:
            sprint_id: ID of the sprint
            old_status: Previous status
            reason: Reason for completion

        Returns:
            Audit entry created
        """
        return log_status_change(
            root_dir=self.root_dir,
            object_type="sprint",
            object_id=sprint_id,
            old_status=old_status,
            new_status="completed",
            reason=reason,
        )

    def log_sprint_progress(
        self,
        sprint_id: str,
        old_percent: float,
        new_percent: float,
        reason: str = "Progress updated",
    ) -> AuditEntry:
        """
        Log sprint progress update.

        Args:
            sprint_id: ID of the sprint
            old_percent: Previous completion percentage
            new_percent: New completion percentage
            reason: Reason for update

        Returns:
            Audit entry created
        """
        return log_progress_change(
            root_dir=self.root_dir,
            object_type="sprint",
            object_id=sprint_id,
            field="completion_percent",
            old_value=old_percent,
            new_value=new_percent,
            reason=reason,
        )

    # =========================================================================
    # Track Activities
    # =========================================================================

    def log_track_started(
        self,
        track_id: str,
        reason: str = "Track started via CLI",
    ) -> AuditEntry:
        """
        Log a track being started.

        Args:
            track_id: ID of the track
            reason: Reason for starting

        Returns:
            Audit entry created
        """
        return log_status_change(
            root_dir=self.root_dir,
            object_type="track",
            object_id=track_id,
            old_status="not_started",
            new_status="in_progress",
            reason=reason,
        )

    def log_track_completed(
        self,
        track_id: str,
        old_status: str = "in_progress",
        reason: str = "Track completed via CLI",
    ) -> AuditEntry:
        """
        Log a track being completed.

        Args:
            track_id: ID of the track
            old_status: Previous status
            reason: Reason for completion

        Returns:
            Audit entry created
        """
        return log_status_change(
            root_dir=self.root_dir,
            object_type="track",
            object_id=track_id,
            old_status=old_status,
            new_status="completed",
            reason=reason,
        )

    def log_track_progress(
        self,
        track_id: str,
        old_percent: float,
        new_percent: float,
        reason: str = "Progress updated",
    ) -> AuditEntry:
        """
        Log track progress update.

        Args:
            track_id: ID of the track
            old_percent: Previous completion percentage
            new_percent: New completion percentage
            reason: Reason for update

        Returns:
            Audit entry created
        """
        return log_progress_change(
            root_dir=self.root_dir,
            object_type="track",
            object_id=track_id,
            field="completion_percent",
            old_value=old_percent,
            new_value=new_percent,
            reason=reason,
        )

    # =========================================================================
    # Quality Gate Activities
    # =========================================================================

    def log_quality_gate_passed(
        self,
        object_type: str,
        object_id: str,
        gate_name: str,
        reason: str = "Quality gate passed",
    ) -> AuditEntry:
        """
        Log a quality gate being passed.

        Args:
            object_type: Type of object (task, sprint, track)
            object_id: ID of the object
            gate_name: Name of the quality gate
            reason: Additional details

        Returns:
            Audit entry created
        """
        return self.audit_manager.log_change(
            object_type=object_type,
            object_id=object_id,
            field=f"quality_gate.{gate_name}",
            old_value="pending",
            new_value="passed",
            reason=reason,
            source="automated",
        )

    def log_quality_gate_failed(
        self,
        object_type: str,
        object_id: str,
        gate_name: str,
        failure_reason: str,
    ) -> AuditEntry:
        """
        Log a quality gate failure.

        Args:
            object_type: Type of object (task, sprint, track)
            object_id: ID of the object
            gate_name: Name of the quality gate
            failure_reason: Why the gate failed

        Returns:
            Audit entry created
        """
        return self.audit_manager.log_change(
            object_type=object_type,
            object_id=object_id,
            field=f"quality_gate.{gate_name}",
            old_value="pending",
            new_value="failed",
            reason=failure_reason,
            source="automated",
        )

    # =========================================================================
    # Criteria & Transition Activities
    # =========================================================================

    def log_criterion_met(
        self,
        object_type: str,
        object_id: str,
        criterion_name: str,
        reason: str = "Criterion satisfied",
    ) -> AuditEntry:
        """
        Log a criterion being met.

        Args:
            object_type: Type of object (task, sprint, track)
            object_id: ID of the object
            criterion_name: Name/description of the criterion
            reason: Additional details

        Returns:
            Audit entry created
        """
        return self.audit_manager.log_change(
            object_type=object_type,
            object_id=object_id,
            field=f"criterion.{criterion_name}",
            old_value="pending",
            new_value="met",
            reason=reason,
            source="automated",
        )

    def log_criterion_failed(
        self,
        object_type: str,
        object_id: str,
        criterion_name: str,
        failure_reason: str,
    ) -> AuditEntry:
        """
        Log a criterion failure.

        Args:
            object_type: Type of object (task, sprint, track)
            object_id: ID of the object
            criterion_name: Name/description of the criterion
            failure_reason: Why the criterion failed

        Returns:
            Audit entry created
        """
        return self.audit_manager.log_change(
            object_type=object_type,
            object_id=object_id,
            field=f"criterion.{criterion_name}",
            old_value="pending",
            new_value="failed",
            reason=failure_reason,
            source="automated",
        )

    def log_auto_progression(
        self,
        object_type: str,
        object_id: str,
        old_status: str,
        new_status: str,
        reason: str = "Auto-progressed based on criteria",
    ) -> AuditEntry:
        """
        Log an automatic status progression.

        Args:
            object_type: Type of object (task, sprint, track)
            object_id: ID of the object
            old_status: Previous status
            new_status: New status after progression
            reason: Reason for the progression

        Returns:
            Audit entry created
        """
        return self.audit_manager.log_change(
            object_type=object_type,
            object_id=object_id,
            field="status",
            old_value=old_status,
            new_value=new_status,
            reason=f"[AUTO] {reason}",
            source="automated",
        )

    def log_transition_blocked(
        self,
        object_type: str,
        object_id: str,
        target_status: str,
        blocking_reasons: list,
    ) -> AuditEntry:
        """
        Log a blocked status transition attempt.

        Args:
            object_type: Type of object (task, sprint, track)
            object_id: ID of the object
            target_status: Status that was attempted
            blocking_reasons: List of reasons blocking the transition

        Returns:
            Audit entry created
        """
        reasons_str = "; ".join(blocking_reasons) if blocking_reasons else "Unknown"
        return self.audit_manager.log_change(
            object_type=object_type,
            object_id=object_id,
            field="transition_blocked",
            old_value=target_status,
            new_value="blocked",
            reason=f"Cannot transition to {target_status}: {reasons_str}",
            source="automated",
        )

    # =========================================================================
    # Standard Activities
    # =========================================================================

    def log_standard_enforced(
        self,
        object_id: str,
        standard_id: str,
        result: bool,
        message: str,
    ) -> AuditEntry:
        """
        Log a standard being enforced.

        Args:
            object_id: ID of the object checked
            standard_id: ID of the standard
            result: True if passed, False if failed
            message: Result message

        Returns:
            Audit entry created
        """
        return self.audit_manager.log_change(
            object_type="standard",
            object_id=object_id,
            field=f"standard.{standard_id}",
            old_value="unchecked",
            new_value="passed" if result else "failed",
            reason=message,
            source="automated",
        )

    # =========================================================================
    # General Activity Logging
    # =========================================================================

    def log_activity(
        self,
        activity_type: ActivityType,
        object_type: str,
        object_id: str,
        description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """
        Log a general activity.

        This is a flexible method for logging any activity that doesn't
        fit into the specific categories above.

        Args:
            activity_type: Type of activity from ActivityType enum
            object_type: Type of object (task, sprint, track, roadmap)
            object_id: ID of the object
            description: Human-readable description
            context: Optional additional context

        Returns:
            Audit entry created
        """
        context_str = ""
        if context:
            context_str = f" | Context: {context}"

        return self.audit_manager.log_change(
            object_type=object_type,
            object_id=object_id,
            field="activity",
            old_value=None,
            new_value=activity_type.value,
            reason=f"{description}{context_str}",
            source="cli",
        )

    # =========================================================================
    # Query Methods
    # =========================================================================

    def get_recent_activities(self, limit: int = 20) -> list:
        """Get recent activity entries."""
        return self.audit_manager.get_recent_changes(limit)

    def get_object_activities(self, object_id: str) -> list:
        """Get all activities for a specific object."""
        return self.audit_manager.get_object_history(object_id)

    def get_suspicious_activities(self) -> list:
        """Get suspicious activities (status rollbacks, progress decreases)."""
        return self.audit_manager.detect_suspicious_changes()

    def generate_report(
        self,
        object_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> str:
        """Generate a human-readable activity report."""
        return self.audit_manager.generate_report(object_id, start_date, end_date)


# =============================================================================
# Convenience Functions
# =============================================================================


def get_activity_log(root_dir: Path) -> UnifiedActivityLog:
    """
    Get a UnifiedActivityLog instance for the given root directory.

    Args:
        root_dir: Project root directory

    Returns:
        UnifiedActivityLog instance
    """
    return UnifiedActivityLog(root_dir)


def log_task_started(
    root_dir: Path,
    task_id: str,
    assigned_agent: Optional[str] = None,
    reason: str = "Task started via CLI",
) -> AuditEntry:
    """Convenience function to log task started."""
    return get_activity_log(root_dir).log_task_started(task_id, assigned_agent, reason)


def log_task_completed(
    root_dir: Path,
    task_id: str,
    old_status: str = "in_progress",
    reason: str = "Task completed via CLI",
) -> AuditEntry:
    """Convenience function to log task completed."""
    return get_activity_log(root_dir).log_task_completed(task_id, old_status, reason)


def log_task_added(
    root_dir: Path,
    task_id: str,
    sprint_id: str,
    title: str,
    reason: str = "Task created via CLI",
) -> AuditEntry:
    """Convenience function to log task creation."""
    return get_activity_log(root_dir).log_task_added(task_id, sprint_id, title, reason)


def log_sprint_added(
    root_dir: Path,
    sprint_id: str,
    track_id: str,
    name: str,
    reason: str = "Sprint created via CLI",
) -> AuditEntry:
    """Convenience function to log sprint creation."""
    return get_activity_log(root_dir).log_sprint_added(sprint_id, track_id, name, reason)


def log_sprint_started(
    root_dir: Path,
    sprint_id: str,
    reason: str = "Sprint started via CLI",
) -> AuditEntry:
    """Convenience function to log sprint started."""
    return get_activity_log(root_dir).log_sprint_started(sprint_id, reason)


def log_sprint_completed(
    root_dir: Path,
    sprint_id: str,
    old_status: str = "in_progress",
    reason: str = "Sprint completed via CLI",
) -> AuditEntry:
    """Convenience function to log sprint completed."""
    return get_activity_log(root_dir).log_sprint_completed(sprint_id, old_status, reason)


def log_track_started(
    root_dir: Path,
    track_id: str,
    reason: str = "Track started via CLI",
) -> AuditEntry:
    """Convenience function to log track started."""
    return get_activity_log(root_dir).log_track_started(track_id, reason)


def log_track_completed(
    root_dir: Path,
    track_id: str,
    old_status: str = "in_progress",
    reason: str = "Track completed via CLI",
) -> AuditEntry:
    """Convenience function to log track completed."""
    return get_activity_log(root_dir).log_track_completed(track_id, old_status, reason)


def log_criterion_met(
    root_dir: Path,
    object_type: str,
    object_id: str,
    criterion_name: str,
    reason: str = "Criterion satisfied",
) -> AuditEntry:
    """Convenience function to log criterion met."""
    return get_activity_log(root_dir).log_criterion_met(
        object_type, object_id, criterion_name, reason
    )


def log_criterion_failed(
    root_dir: Path,
    object_type: str,
    object_id: str,
    criterion_name: str,
    failure_reason: str,
) -> AuditEntry:
    """Convenience function to log criterion failed."""
    return get_activity_log(root_dir).log_criterion_failed(
        object_type, object_id, criterion_name, failure_reason
    )


def log_auto_progression(
    root_dir: Path,
    object_type: str,
    object_id: str,
    old_status: str,
    new_status: str,
    reason: str = "Auto-progressed based on criteria",
) -> AuditEntry:
    """Convenience function to log auto-progression."""
    return get_activity_log(root_dir).log_auto_progression(
        object_type, object_id, old_status, new_status, reason
    )


def log_transition_blocked(
    root_dir: Path,
    object_type: str,
    object_id: str,
    target_status: str,
    blocking_reasons: list,
) -> AuditEntry:
    """Convenience function to log blocked transition."""
    return get_activity_log(root_dir).log_transition_blocked(
        object_type, object_id, target_status, blocking_reasons
    )
