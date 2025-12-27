"""
Scope completion checking for Implementation Mode.

This module provides completion detection using HierarchicalTicket's built-in
methods, following the Unified Ticket Architecture principles.

Key Methods Used:
- can_transition_to(status) - Check if ticket can transition to a status
- progress_for_transition(status) - Get progress toward a status transition
- auto_progress(context) - Automatically progress ticket when criteria met

Design Reference:
- Sprint 12: Explicit Scope Requirements
- Task 05: Add completion detection using HierarchicalTicket
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
from vibey.roadmap.models.ticket.enums import TicketStatus

logger = logging.getLogger(__name__)


# =============================================================================
# SCOPE TICKET LOADING
# =============================================================================


def load_scope_ticket(
    scope_ulid: str,
    roadmap_root: Union[str, Path],
) -> Optional[HierarchicalTicket]:
    """
    Load a ticket by ULID, detecting type from file location.

    Searches for the ULID in tracks/, sprints/, and tasks/ directories
    and loads the first match as a HierarchicalTicket.

    Args:
        scope_ulid: The ULID of the ticket to load
        roadmap_root: Path to .vibey/roadmap directory

    Returns:
        HierarchicalTicket if found, None otherwise

    Example:
        >>> ticket = load_scope_ticket("01KC...", Path(".vibey/roadmap"))
        >>> if ticket:
        ...     print(f"Loaded {ticket.ticket_type}: {ticket.name}")
    """
    roadmap_root = Path(roadmap_root)

    # Import loaders lazily to avoid circular imports
    from vibey.roadmap.serialization.yaml_loader import (
        load_track_ticket,
        load_sprint_ticket,
        load_task_ticket,
    )

    # Try each ticket type in order: track, sprint, task
    type_configs = [
        ("tracks", load_track_ticket),
        ("sprints", load_sprint_ticket),
        ("tasks", load_task_ticket),
    ]

    for dir_name, loader in type_configs:
        file_path = roadmap_root / dir_name / f"{scope_ulid}.yaml"
        if file_path.exists():
            try:
                ticket = loader(file_path)
                logger.debug(f"Loaded scope ticket {scope_ulid} from {dir_name}/")
                return ticket
            except Exception as e:
                logger.warning(
                    f"Failed to load {scope_ulid} from {dir_name}: {e}"
                )

    logger.warning(f"Scope ticket {scope_ulid} not found in any directory")
    return None


def reload_scope_ticket(
    scope_ticket: HierarchicalTicket,
    roadmap_root: Union[str, Path],
) -> Optional[HierarchicalTicket]:
    """
    Reload a scope ticket to get fresh state from disk.

    After tasks complete, the scope ticket's children may have updated status.
    This function reloads the ticket to get current state.

    Args:
        scope_ticket: The ticket to reload
        roadmap_root: Path to .vibey/roadmap directory

    Returns:
        Fresh HierarchicalTicket, or original if reload fails
    """
    reloaded = load_scope_ticket(scope_ticket.id, roadmap_root)
    if reloaded is None:
        logger.warning(f"Failed to reload {scope_ticket.id}, using stale data")
        return scope_ticket
    return reloaded


class ScopeCompletionChecker:
    """
    Check and update completion status using HierarchicalTicket methods.

    Uses the unified ticket architecture's built-in completion logic:
    - can_transition_to() for checking if completion is possible
    - progress_for_transition() for progress tracking

    NO type-specific logic (track/sprint/task) - all handled by HierarchicalTicket.

    Example:
        >>> checker = ScopeCompletionChecker()
        >>> is_complete, message = checker.check_scope_completion(scope_ticket)
        >>> if is_complete:
        ...     print("Scope is ready to complete!")
    """

    def check_scope_completion(
        self,
        scope_ticket: HierarchicalTicket,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if scope ticket can be completed.

        Uses HierarchicalTicket.can_transition_to() which:
        - Checks all criteria (including child completion via CompletableTarget)
        - Excludes deferred children automatically
        - Handles all hierarchy levels uniformly

        Args:
            scope_ticket: The ticket defining execution scope

        Returns:
            Tuple of (can_complete, message)
        """
        can_complete, blocking_reasons = scope_ticket.can_transition_to(
            TicketStatus.COMPLETED
        )

        if can_complete:
            return True, f"Ticket {scope_ticket.id} ready to complete"

        # Get progress for informative message
        progress = scope_ticket.progress_for_transition(TicketStatus.COMPLETED)
        remaining = progress.total - progress.completed

        reason_summary = "; ".join(blocking_reasons[:3]) if blocking_reasons else ""
        return False, f"{remaining} criteria remaining: {reason_summary}"

    def get_completion_progress(
        self,
        scope_ticket: HierarchicalTicket,
    ) -> Dict:
        """
        Get detailed progress toward scope completion.

        Args:
            scope_ticket: The ticket to check progress for

        Returns:
            Dict with progress details including:
            - total_criteria: Total criteria to satisfy
            - completed_criteria: Criteria already satisfied
            - remaining: Criteria still to complete
            - percentage: Completion percentage (0-100)
            - can_complete: Whether all criteria are met
        """
        progress = scope_ticket.progress_for_transition(TicketStatus.COMPLETED)

        return {
            "total_criteria": progress.total,
            "completed_criteria": progress.completed,
            "remaining": progress.total - progress.completed,
            "percentage": (
                (progress.completed / progress.total * 100)
                if progress.total > 0
                else 100
            ),
            "can_complete": progress.completed >= progress.total,
        }

    def is_scope_complete(
        self,
        scope_ticket: HierarchicalTicket,
    ) -> bool:
        """
        Simple check if scope ticket is already in a completed state.

        Args:
            scope_ticket: The ticket to check

        Returns:
            True if ticket is in COMPLETED, PRODUCTION_READY, or DEPLOYED status
        """
        return scope_ticket.status in (
            TicketStatus.COMPLETED,
            TicketStatus.PRODUCTION_READY,
            TicketStatus.DEPLOYED,
        )


# Convenience function for one-off checks
def check_scope_complete(scope_ticket: HierarchicalTicket) -> Tuple[bool, str]:
    """
    Convenience function to check if a scope ticket can be completed.

    Args:
        scope_ticket: The HierarchicalTicket to check

    Returns:
        Tuple of (can_complete, message)
    """
    checker = ScopeCompletionChecker()
    return checker.check_scope_completion(scope_ticket)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ScopeCompletionChecker",
    "load_scope_ticket",
    "reload_scope_ticket",
    "check_scope_complete",
]
