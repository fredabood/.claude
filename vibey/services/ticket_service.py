"""
TicketService - Unified ticket operations for CLI and MCP.

This service provides the adapter-agnostic interface for all ticket operations.
It delegates to the configured TicketAdapter, enabling easy switching between
PM tools (Vibey, Jira, GitHub, etc.).

Design Philosophy:
- CLI and MCP never talk directly to adapters
- Service handles adapter selection and error handling
- Convenience methods for common workflows (start, complete, block)
- Consistent logging for all operations

Usage:
    from vibey.services import TicketService

    service = TicketService()  # Uses default adapter

    # Read operations
    projects = service.list_projects()
    task = service.get_ticket("01KCWDNDQ40Y43H4ZGH9KTTBH1")
    children = service.get_children("01KCWDNDQ40Y43H4ZGH9KTTBH0")

    # Write operations
    service.start("01KCWDNDQ40Y43H4ZGH9KTTBH1")
    service.complete("01KCWDNDQ40Y43H4ZGH9KTTBH1")

    # Switch adapters
    service.set_adapter("jira")
    jira_projects = service.list_projects()

Reference: UNIFIED_ADAPTER_ARCHITECTURE.md Part 3.3
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from vibey.adapters.pm import (
    AdapterNotFoundError,
    PMAdapterRegistry,
    TicketAdapter,
)
from vibey.adapters.pm.types import (
    ConflictResolution,
    SyncDirection,
    SyncResult,
)
from vibey.core.ticket import (
    HierarchyType,
    Ticket,
    TicketPriority,
    TicketStatus,
)

logger = logging.getLogger(__name__)


class TicketServiceError(Exception):
    """Base exception for ticket service errors."""

    pass


class TicketNotFoundError(TicketServiceError):
    """Raised when a ticket is not found."""

    def __init__(self, ticket_id: str):
        self.ticket_id = ticket_id
        super().__init__(f"Ticket not found: {ticket_id}")


class InvalidOperationError(TicketServiceError):
    """Raised when an operation is invalid for the current state."""

    pass


class TicketService:
    """
    Unified service for all ticket operations.

    This class provides the adapter-agnostic interface that CLI and MCP use
    for all ticket operations. It handles adapter selection, error handling,
    and provides convenience methods for common workflows.

    Attributes:
        adapter: The current TicketAdapter being used

    Example:
        >>> service = TicketService()
        >>> projects = service.list_projects()
        >>> task = service.get_ticket("TASK-001")
        >>> service.start(task.id)
        >>> # ... do work ...
        >>> service.complete(task.id)
    """

    def __init__(self, adapter: Optional[Union[TicketAdapter, str]] = None):
        """
        Initialize the ticket service.

        Args:
            adapter: Either a TicketAdapter instance, an adapter name (string),
                    or None to use the default adapter.

        Raises:
            AdapterNotFoundError: If specified adapter name is not registered
        """
        if adapter is None:
            self._adapter = PMAdapterRegistry.get_default()
        elif isinstance(adapter, str):
            self._adapter = PMAdapterRegistry.get(adapter)
        else:
            self._adapter = adapter

        logger.debug(f"TicketService initialized with adapter: {self._adapter.adapter_name}")

    # =========================================================================
    # PROPERTIES
    # =========================================================================

    @property
    def adapter(self) -> TicketAdapter:
        """Get the current adapter."""
        return self._adapter

    @property
    def adapter_name(self) -> str:
        """Get the current adapter name."""
        return self._adapter.adapter_name

    @property
    def display_name(self) -> str:
        """Get the current adapter display name."""
        return self._adapter.display_name

    # =========================================================================
    # ADAPTER MANAGEMENT
    # =========================================================================

    def set_adapter(self, adapter: Union[TicketAdapter, str]) -> None:
        """
        Switch to a different adapter.

        Args:
            adapter: Either a TicketAdapter instance or adapter name

        Raises:
            AdapterNotFoundError: If specified adapter name is not registered
        """
        if isinstance(adapter, str):
            self._adapter = PMAdapterRegistry.get(adapter)
        else:
            self._adapter = adapter

        logger.info(f"Switched to adapter: {self._adapter.adapter_name}")

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get current adapter capabilities.

        Returns:
            Dictionary of capability flags
        """
        caps = self._adapter.capabilities
        return {
            "supported_hierarchy_types": [t.value for t in caps.supported_hierarchy_types],
            "supports_sprints": caps.supports_sprints,
            "supports_bidirectional_sync": caps.supports_bidirectional_sync,
            "supports_webhooks": caps.supports_webhooks,
            "supports_attachments": caps.supports_attachments,
            "supports_comments": caps.supports_comments,
            "max_description_length": caps.max_description_length,
        }

    # =========================================================================
    # READ OPERATIONS
    # =========================================================================

    def list_projects(self) -> List[Ticket]:
        """
        List all top-level projects.

        Returns:
            List of project-level Ticket objects
        """
        logger.debug(f"Listing projects via {self.adapter_name}")
        return self._adapter.list_projects()

    def get_ticket(self, ticket_id: str) -> Ticket:
        """
        Get a ticket by ID.

        Args:
            ticket_id: The ticket identifier

        Returns:
            Ticket object

        Raises:
            TicketNotFoundError: If ticket doesn't exist
        """
        logger.debug(f"Getting ticket {ticket_id} via {self.adapter_name}")
        ticket = self._adapter.get_ticket(ticket_id)
        if ticket is None:
            raise TicketNotFoundError(ticket_id)
        return ticket

    def get_children(self, parent_id: str) -> List[Ticket]:
        """
        Get direct children of a ticket.

        Args:
            parent_id: ID of the parent ticket

        Returns:
            List of child Ticket objects
        """
        logger.debug(f"Getting children of {parent_id} via {self.adapter_name}")
        return self._adapter.list_children(parent_id)

    def get_workstreams(self, project_id: str) -> List[Ticket]:
        """
        Get workstreams (tracks) for a project.

        Convenience method filtering children by WORKSTREAM type.

        Args:
            project_id: ID of the project

        Returns:
            List of workstream Ticket objects
        """
        children = self.get_children(project_id)
        return [c for c in children if c.hierarchy_type == HierarchyType.WORKSTREAM]

    def get_iterations(self, workstream_id: str) -> List[Ticket]:
        """
        Get iterations (sprints) for a workstream.

        Convenience method filtering children by ITERATION type.

        Args:
            workstream_id: ID of the workstream

        Returns:
            List of iteration Ticket objects
        """
        children = self.get_children(workstream_id)
        return [c for c in children if c.hierarchy_type == HierarchyType.ITERATION]

    def get_work_items(self, parent_id: str) -> List[Ticket]:
        """
        Get work items (tasks) for a parent.

        Convenience method filtering children by WORK_ITEM type.

        Args:
            parent_id: ID of the parent (iteration or workstream)

        Returns:
            List of work item Ticket objects
        """
        children = self.get_children(parent_id)
        return [c for c in children if c.hierarchy_type == HierarchyType.WORK_ITEM]

    def search(
        self,
        query: Optional[str] = None,
        hierarchy_type: Optional[HierarchyType] = None,
        status: Optional[TicketStatus] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        parent_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Ticket]:
        """
        Search for tickets with filters.

        All filter parameters are optional and combined with AND logic.

        Args:
            query: Free-text search in name/description
            hierarchy_type: Filter by hierarchy level
            status: Filter by ticket status
            assignee: Filter by assigned user
            labels: Filter by labels (tickets must have ALL labels)
            parent_id: Filter by parent ticket
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            List of matching Ticket objects
        """
        logger.debug(f"Searching tickets via {self.adapter_name}: query={query}, status={status}")
        return self._adapter.search_tickets(
            query=query,
            hierarchy_type=hierarchy_type,
            status=status,
            assignee=assignee,
            labels=labels,
            parent_id=parent_id,
            limit=limit,
            offset=offset,
        )

    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================

    def create(self, ticket: Ticket) -> Ticket:
        """
        Create a new ticket.

        Args:
            ticket: Ticket object with data for new ticket
                   (id may be None, adapter will assign)

        Returns:
            Created Ticket with assigned ID
        """
        logger.info(f"Creating ticket '{ticket.name}' via {self.adapter_name}")
        return self._adapter.create_ticket(ticket)

    def update(self, ticket: Ticket) -> Ticket:
        """
        Update an existing ticket.

        Args:
            ticket: Ticket object with updated data

        Returns:
            Updated Ticket object
        """
        logger.info(f"Updating ticket {ticket.id} via {self.adapter_name}")
        return self._adapter.update_ticket(ticket)

    def delete(self, ticket_id: str) -> bool:
        """
        Delete a ticket.

        Args:
            ticket_id: ID of ticket to delete

        Returns:
            True if deleted, False if not found
        """
        logger.info(f"Deleting ticket {ticket_id} via {self.adapter_name}")
        return self._adapter.delete_ticket(ticket_id)

    # =========================================================================
    # CONVENIENCE METHODS (Common Workflows)
    # =========================================================================

    def start(self, ticket_id: str) -> Ticket:
        """
        Start working on a ticket.

        Sets status to IN_PROGRESS and started_at timestamp.

        Args:
            ticket_id: ID of ticket to start

        Returns:
            Updated Ticket object

        Raises:
            TicketNotFoundError: If ticket doesn't exist
            InvalidOperationError: If ticket is already completed/cancelled
        """
        ticket = self.get_ticket(ticket_id)

        if ticket.status in (TicketStatus.COMPLETED, TicketStatus.CANCELLED):
            raise InvalidOperationError(
                f"Cannot start ticket with status: {ticket.status.value}"
            )

        logger.info(f"Starting ticket {ticket_id}")
        return self._adapter.update_status(ticket_id, TicketStatus.IN_PROGRESS)

    def complete(self, ticket_id: str) -> Ticket:
        """
        Mark a ticket as completed.

        Sets status to COMPLETED and completed_at timestamp.

        Args:
            ticket_id: ID of ticket to complete

        Returns:
            Updated Ticket object

        Raises:
            TicketNotFoundError: If ticket doesn't exist
            InvalidOperationError: If ticket is already cancelled
        """
        ticket = self.get_ticket(ticket_id)

        if ticket.status == TicketStatus.CANCELLED:
            raise InvalidOperationError("Cannot complete a cancelled ticket")

        logger.info(f"Completing ticket {ticket_id}")
        return self._adapter.update_status(ticket_id, TicketStatus.COMPLETED)

    def block(self, ticket_id: str, reason: Optional[str] = None) -> Ticket:
        """
        Mark a ticket as blocked.

        Sets status to BLOCKED. Optionally updates description with reason.

        Args:
            ticket_id: ID of ticket to block
            reason: Optional reason for the block

        Returns:
            Updated Ticket object

        Raises:
            TicketNotFoundError: If ticket doesn't exist
            InvalidOperationError: If ticket is already completed/cancelled
        """
        ticket = self.get_ticket(ticket_id)

        if ticket.status in (TicketStatus.COMPLETED, TicketStatus.CANCELLED):
            raise InvalidOperationError(
                f"Cannot block ticket with status: {ticket.status.value}"
            )

        logger.info(f"Blocking ticket {ticket_id}: {reason or 'no reason given'}")

        # Update status
        updated = self._adapter.update_status(ticket_id, TicketStatus.BLOCKED)

        # If reason provided, update ticket with it in metadata
        if reason:
            updated.metadata["blocked_reason"] = reason
            updated.metadata["blocked_at"] = datetime.now(timezone.utc).isoformat()
            updated = self._adapter.update_ticket(updated)

        return updated

    def unblock(self, ticket_id: str) -> Ticket:
        """
        Unblock a ticket.

        Sets status back to IN_PROGRESS.

        Args:
            ticket_id: ID of ticket to unblock

        Returns:
            Updated Ticket object

        Raises:
            TicketNotFoundError: If ticket doesn't exist
            InvalidOperationError: If ticket is not blocked
        """
        ticket = self.get_ticket(ticket_id)

        if ticket.status != TicketStatus.BLOCKED:
            raise InvalidOperationError(
                f"Cannot unblock ticket with status: {ticket.status.value}"
            )

        logger.info(f"Unblocking ticket {ticket_id}")
        return self._adapter.update_status(ticket_id, TicketStatus.IN_PROGRESS)

    def cancel(self, ticket_id: str, reason: Optional[str] = None) -> Ticket:
        """
        Cancel a ticket.

        Sets status to CANCELLED.

        Args:
            ticket_id: ID of ticket to cancel
            reason: Optional reason for cancellation

        Returns:
            Updated Ticket object

        Raises:
            TicketNotFoundError: If ticket doesn't exist
        """
        ticket = self.get_ticket(ticket_id)

        logger.info(f"Cancelling ticket {ticket_id}: {reason or 'no reason given'}")

        updated = self._adapter.update_status(ticket_id, TicketStatus.CANCELLED)

        if reason:
            updated.metadata["cancelled_reason"] = reason
            updated.metadata["cancelled_at"] = datetime.now(timezone.utc).isoformat()
            updated = self._adapter.update_ticket(updated)

        return updated

    # =========================================================================
    # SYNC OPERATIONS
    # =========================================================================

    def sync(
        self,
        direction: SyncDirection = SyncDirection.IMPORT,
        conflict_resolution: ConflictResolution = ConflictResolution.MANUAL,
    ) -> SyncResult:
        """
        Synchronize with external system.

        Args:
            direction: Direction of sync (import, export, bidirectional)
            conflict_resolution: How to resolve conflicts

        Returns:
            SyncResult with details of the sync operation

        Raises:
            NotImplementedError: If adapter doesn't support sync
        """
        logger.info(
            f"Syncing {direction.value} via {self.adapter_name} "
            f"with {conflict_resolution.value} resolution"
        )
        return self._adapter.sync(
            direction=direction,
            conflict_resolution=conflict_resolution.value,
        )

    def detect_conflicts(
        self, other_adapter: Union[TicketAdapter, str]
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts between current adapter and another.

        Args:
            other_adapter: The adapter to compare against

        Returns:
            List of conflict dictionaries
        """
        if isinstance(other_adapter, str):
            other_adapter = PMAdapterRegistry.get(other_adapter)

        logger.info(
            f"Detecting conflicts between {self.adapter_name} "
            f"and {other_adapter.adapter_name}"
        )
        return self._adapter.detect_conflicts(other_adapter)

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def is_available(self) -> bool:
        """Check if the current adapter is available and configured."""
        return self._adapter.is_available()

    def validate(self) -> List[str]:
        """
        Validate adapter configuration.

        Returns:
            List of error messages (empty if valid)
        """
        return self._adapter.validate_config()

    def __repr__(self) -> str:
        return f"<TicketService(adapter={self.adapter_name})>"
