"""
Status Manager for auto-progression of roadmap tickets.

Provides optional automatic status advancement when criteria are met.
This is a configuration-driven feature that can be enabled/disabled.

Configuration is read from .vibey/config/roadmap.yaml:
    auto_progression:
      enabled: true/false
      mode: check/apply
      transitions:
        - from: not_started
          to: in_progress
          when: all_start_criteria_met
      propagate_up: true
      log_to_audit: true

Design Reference: sqlite-backend-13-task-011
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


@dataclass
class TransitionConfig:
    """Configuration for a single auto-transition."""
    from_status: str
    to_status: str
    when: str  # Condition: all_start_criteria_met, all_completion_criteria_met


@dataclass
class AutoProgressionConfig:
    """Configuration for auto-progression feature."""
    enabled: bool = False
    mode: str = "check"  # check or apply
    transitions: List[TransitionConfig] = field(default_factory=list)
    propagate_up: bool = True
    log_to_audit: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutoProgressionConfig":
        """Create config from dictionary."""
        transitions = []
        for t in data.get("transitions", []):
            transitions.append(TransitionConfig(
                from_status=t.get("from", ""),
                to_status=t.get("to", ""),
                when=t.get("when", ""),
            ))

        return cls(
            enabled=data.get("enabled", False),
            mode=data.get("mode", "check"),
            transitions=transitions,
            propagate_up=data.get("propagate_up", True),
            log_to_audit=data.get("log_to_audit", True),
        )


@dataclass
class ProgressionResult:
    """Result of an auto-progression check or application."""
    ticket_id: str
    ticket_type: str  # task, sprint, track
    old_status: str
    new_status: str
    applied: bool  # True if status was actually changed
    reason: str  # Why progression was triggered


class StatusManager:
    """
    Manages automatic status progression for roadmap tickets.

    Key Features:
    - Config-driven: enabled/disabled via .vibey/config/roadmap.yaml
    - Two modes: check (dry-run) or apply (actually change status)
    - Parent chain propagation: automatically advance parents when children complete
    - Audit logging: optional logging of all auto-progressions

    Usage:
        manager = StatusManager(root_dir)

        # Check what would advance (dry-run)
        results = manager.check_progressions()

        # Actually apply progressions
        results = manager.apply_progressions()
    """

    def __init__(self, root_dir: Path):
        """
        Initialize status manager.

        Args:
            root_dir: Project root directory containing .vibey/
        """
        self.root_dir = Path(root_dir)
        self.config = self._load_config()

    def _load_config(self) -> AutoProgressionConfig:
        """Load auto-progression configuration."""
        config_path = self.root_dir / ".vibey" / "config" / "roadmap.yaml"

        if not config_path.exists():
            return AutoProgressionConfig()  # Defaults (disabled)

        try:
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}

            auto_prog = data.get("auto_progression", {})
            return AutoProgressionConfig.from_dict(auto_prog)
        except Exception:
            return AutoProgressionConfig()

    def is_enabled(self) -> bool:
        """Check if auto-progression is enabled."""
        return self.config.enabled

    def get_mode(self) -> str:
        """Get current mode (check or apply)."""
        return self.config.mode

    def check_progressions(
        self,
        ticket_ids: Optional[List[str]] = None
    ) -> List[ProgressionResult]:
        """
        Check which tickets can be auto-progressed.

        This is a dry-run that doesn't actually change any status.

        Args:
            ticket_ids: Optional list of specific ticket IDs to check.
                       If None, checks all eligible tickets.

        Returns:
            List of ProgressionResult showing what would change.
        """
        if not self.config.enabled:
            return []

        results = []

        # Import here to avoid circular imports
        from vibey.operations.roadmap.query import query_task_details, query_sprint_details

        # Get tickets to check
        if ticket_ids:
            tickets = []
            for tid in ticket_ids:
                try:
                    ticket = self._load_ticket(tid)
                    if ticket:
                        tickets.append(ticket)
                except Exception:
                    pass
        else:
            # Get all in-progress and not-started tickets
            tickets = self._get_eligible_tickets()

        # Check each ticket against configured transitions
        for ticket in tickets:
            for transition in self.config.transitions:
                if str(ticket.get("status", "")).lower() == transition.from_status:
                    can_advance, reason = self._can_advance(ticket, transition)
                    if can_advance:
                        results.append(ProgressionResult(
                            ticket_id=ticket.get("id", ""),
                            ticket_type=self._get_ticket_type(ticket),
                            old_status=transition.from_status,
                            new_status=transition.to_status,
                            applied=False,
                            reason=reason,
                        ))

        return results

    def apply_progressions(
        self,
        ticket_ids: Optional[List[str]] = None
    ) -> List[ProgressionResult]:
        """
        Apply auto-progressions to eligible tickets.

        This actually changes ticket status.

        Args:
            ticket_ids: Optional list of specific ticket IDs to progress.
                       If None, processes all eligible tickets.

        Returns:
            List of ProgressionResult showing what was changed.
        """
        if not self.config.enabled:
            return []

        results = []
        processed = set()

        # Get candidates first
        candidates = self.check_progressions(ticket_ids)

        # Apply each progression
        for candidate in candidates:
            if candidate.ticket_id in processed:
                continue

            success = self._apply_progression(candidate)
            if success:
                results.append(ProgressionResult(
                    ticket_id=candidate.ticket_id,
                    ticket_type=candidate.ticket_type,
                    old_status=candidate.old_status,
                    new_status=candidate.new_status,
                    applied=True,
                    reason=candidate.reason,
                ))
                processed.add(candidate.ticket_id)

                # Propagate up if configured
                if self.config.propagate_up:
                    parent_results = self._propagate_up(candidate.ticket_id)
                    results.extend(parent_results)
                    for r in parent_results:
                        processed.add(r.ticket_id)

        # Log to audit trail if configured
        if self.config.log_to_audit and results:
            self._log_to_audit(results)

        return results

    def _load_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Load a single ticket by ID."""
        try:
            from vibey.operations.roadmap.query import (
                query_task_details,
                query_sprint_details,
                query_track_details,
            )

            # Try task first
            if "task" in ticket_id.lower():
                result = query_task_details(self.root_dir, ticket_id)
                if result and "error" not in result:
                    return result

            # Try sprint
            if "task" not in ticket_id.lower():
                result = query_sprint_details(self.root_dir, ticket_id)
                if result and "error" not in result:
                    return result

            # Try track
            result = query_track_details(self.root_dir, ticket_id)
            if result and "error" not in result:
                return result

            return None
        except Exception:
            return None

    def _get_eligible_tickets(self) -> List[Dict[str, Any]]:
        """Get all tickets eligible for auto-progression."""
        eligible = []

        try:
            from vibey.operations.roadmap.query import query_roadmap_summary

            # Get roadmap summary to find all not_started items
            summary = query_roadmap_summary(self.root_dir)

            if not summary or "tracks" not in summary:
                return eligible

            # Look for not_started tasks that have no blocking dependencies
            for track in summary.get("tracks", []):
                track_status = track.get("status", "")
                if track_status in ["not_started", "in_progress"]:
                    track_data = self._load_ticket(track.get("id", ""))
                    if track_data:
                        eligible.append(track_data)

        except Exception:
            pass

        return eligible

    def _can_advance(
        self,
        ticket: Dict[str, Any],
        transition: TransitionConfig
    ) -> Tuple[bool, str]:
        """
        Check if a ticket can advance based on transition criteria.

        Args:
            ticket: Ticket data dictionary
            transition: Transition configuration

        Returns:
            Tuple of (can_advance: bool, reason: str)
        """
        condition = transition.when

        if condition == "all_start_criteria_met":
            # Check if ticket has no blocking dependencies
            blocked_by = ticket.get("blocked_by", [])
            if blocked_by:
                return False, f"Blocked by: {', '.join(blocked_by)}"
            return True, "No blocking dependencies"

        elif condition == "all_completion_criteria_met":
            # Check if all subtasks/children are completed
            ticket_type = self._get_ticket_type(ticket)

            if ticket_type == "task":
                # Tasks complete when work is done (no auto-check)
                return False, "Task completion requires manual mark"

            elif ticket_type == "sprint":
                # Sprints complete when all tasks are completed
                # This would require checking child tasks
                return False, "Sprint completion requires all tasks complete"

            elif ticket_type == "track":
                # Tracks complete when all sprints are completed
                return False, "Track completion requires all sprints complete"

        return False, "Unknown condition"

    def _apply_progression(self, result: ProgressionResult) -> bool:
        """
        Apply a single status progression.

        Args:
            result: ProgressionResult to apply

        Returns:
            True if successfully applied
        """
        try:
            from vibey.operations.roadmap.update import RoadmapUpdate

            update = RoadmapUpdate(self.root_dir)

            # Use the appropriate update method based on ticket type
            if result.ticket_type == "task":
                update.update_task_status(result.ticket_id, result.new_status)
            elif result.ticket_type == "sprint":
                update.update_sprint_status(result.ticket_id, result.new_status)
            elif result.ticket_type == "track":
                update.update_track_status(result.ticket_id, result.new_status)
            else:
                return False

            return True
        except Exception:
            return False

    def _propagate_up(self, ticket_id: str) -> List[ProgressionResult]:
        """
        Propagate completion up the hierarchy.

        When a child ticket completes, check if parent can now advance.

        Args:
            ticket_id: ID of ticket that just completed

        Returns:
            List of additional progressions that occurred
        """
        results = []

        try:
            ticket = self._load_ticket(ticket_id)

            if not ticket:
                return results

            # Get parent reference
            parent_id = ticket.get("sprint_id") or ticket.get("track_id")
            if not parent_id or parent_id == ticket_id:
                return results

            parent = self._load_ticket(parent_id)
            if not parent:
                return results

            # Check if parent can now advance
            for transition in self.config.transitions:
                if str(parent.get("status", "")).lower() == transition.from_status:
                    can_advance, reason = self._can_advance(parent, transition)
                    if can_advance:
                        success = self._apply_progression(ProgressionResult(
                            ticket_id=parent_id,
                            ticket_type=self._get_ticket_type(parent),
                            old_status=transition.from_status,
                            new_status=transition.to_status,
                            applied=False,
                            reason=reason,
                        ))
                        if success:
                            results.append(ProgressionResult(
                                ticket_id=parent_id,
                                ticket_type=self._get_ticket_type(parent),
                                old_status=transition.from_status,
                                new_status=transition.to_status,
                                applied=True,
                                reason=f"Auto-propagated from {ticket_id}",
                            ))
                            # Recurse up the chain
                            results.extend(self._propagate_up(parent_id))

        except Exception:
            pass

        return results

    def _get_ticket_type(self, ticket: Dict[str, Any]) -> str:
        """Determine ticket type from data."""
        if "task_type" in ticket:
            return "task"
        elif "sprint_id" in ticket and "track_id" in ticket and "task_type" not in ticket:
            return "sprint"
        elif "track_id" in ticket and "sprint_id" not in ticket:
            return "track"
        elif "roadmap" in ticket.get("id", "").lower():
            return "roadmap"
        return "unknown"

    def _log_to_audit(self, results: List[ProgressionResult]) -> None:
        """Log progressions to audit trail."""
        try:
            from vibey.operations.roadmap.activity_log import (
                UnifiedActivityLog,
                log_auto_progression,
            )

            for result in results:
                if result.applied:
                    log_auto_progression(
                        root_dir=self.root_dir,
                        object_type=result.ticket_type,
                        object_id=result.ticket_id,
                        old_status=result.old_status,
                        new_status=result.new_status,
                        reason=result.reason,
                    )
        except Exception:
            pass  # Don't fail if audit logging fails


# =============================================================================
# Convenience Functions
# =============================================================================


def get_status_manager(root_dir: Path) -> StatusManager:
    """Get a StatusManager instance for the given root directory."""
    return StatusManager(root_dir)


def check_auto_progressions(
    root_dir: Path,
    ticket_ids: Optional[List[str]] = None
) -> List[ProgressionResult]:
    """
    Check which tickets can be auto-progressed.

    Args:
        root_dir: Project root directory
        ticket_ids: Optional specific tickets to check

    Returns:
        List of potential progressions
    """
    return get_status_manager(root_dir).check_progressions(ticket_ids)


def apply_auto_progressions(
    root_dir: Path,
    ticket_ids: Optional[List[str]] = None
) -> List[ProgressionResult]:
    """
    Apply auto-progressions to eligible tickets.

    Args:
        root_dir: Project root directory
        ticket_ids: Optional specific tickets to progress

    Returns:
        List of applied progressions
    """
    return get_status_manager(root_dir).apply_progressions(ticket_ids)


def is_auto_progression_enabled(root_dir: Path) -> bool:
    """Check if auto-progression is enabled."""
    return get_status_manager(root_dir).is_enabled()
