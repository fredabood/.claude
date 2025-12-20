"""
TicketAdapter Base Class - Abstract interface for PM tool adapters.

This module defines the abstract base class that all PM tool adapters must
implement. It defines the contract for read, write, and sync operations.

Each adapter translates between their tool's data model and the generic
Ticket model, enabling tool-agnostic operations at the CLI/MCP layer.

Adapter Implementations:
- VibeyAdapter: Native Vibey roadmap storage (YAML + SQLite)
- JiraAdapter: Atlassian Jira integration
- GitHubAdapter: GitHub Issues integration
- TrelloAdapter: Trello boards integration
- AsanaAdapter: Asana projects integration

Reference: UNIFIED_ADAPTER_ARCHITECTURE.md Part 3.2
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from vibey.core.ticket import HierarchyType, Ticket, TicketStatus

from vibey.adapters.pm.types import (
    PMCapabilities,
    SyncDirection,
    SyncResult,
)


class TicketAdapter(ABC):
    """
    Abstract base class for all PM tool adapters.

    Each adapter translates between their tool's data model and the generic
    Ticket model. This enables the CLI and MCP server to work with any PM
    tool through a unified interface.

    Implementation Requirements:
    1. All abstract methods must be implemented
    2. Capability properties should be overridden if defaults don't apply
    3. Sync operations are optional (raise NotImplementedError if unsupported)
    4. map_to_generic and map_from_generic handle data conversion

    Example Implementation:
        class JiraAdapter(TicketAdapter):
            @property
            def adapter_name(self) -> str:
                return "jira"

            @property
            def display_name(self) -> str:
                return "Atlassian Jira"

            def list_projects(self) -> List[Ticket]:
                # Call Jira API, convert to Ticket objects
                jira_projects = self._client.get_projects()
                return [self.map_to_generic(p) for p in jira_projects]

            # ... implement other abstract methods
    """

    # =========================================================================
    # IDENTITY (Abstract - Must Override)
    # =========================================================================

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        """
        Unique adapter identifier.

        Used as the source_adapter value in Ticket objects and for
        configuration keys. Should be lowercase, no spaces.

        Examples: 'vibey', 'jira', 'github', 'trello', 'asana'
        """
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """
        Human-readable name for UI display.

        Examples: 'Vibey Roadmap', 'Atlassian Jira', 'GitHub Issues'
        """
        pass

    # =========================================================================
    # CAPABILITIES (Override if needed)
    # =========================================================================

    @property
    def capabilities(self) -> PMCapabilities:
        """
        Get adapter capabilities.

        Override this to declare specific capabilities.
        Default returns a PMCapabilities with standard defaults.
        """
        return PMCapabilities(
            supported_hierarchy_types=self.supported_hierarchy_types,
            supports_sprints=self.supports_sprints,
            supports_bidirectional_sync=self.supports_bidirectional_sync,
            supports_webhooks=self.supports_webhooks,
        )

    @property
    def supported_hierarchy_types(self) -> List[HierarchyType]:
        """
        Which hierarchy types this adapter supports.

        Override if adapter doesn't support all types.
        Example: GitHub doesn't have ITERATION (sprints).
        """
        return list(HierarchyType)

    @property
    def supports_sprints(self) -> bool:
        """
        Whether adapter supports sprint/iteration concept.

        Override to False for tools without sprint support (e.g., GitHub).
        """
        return True

    @property
    def supports_bidirectional_sync(self) -> bool:
        """
        Whether adapter supports two-way sync with external system.

        Override to True if adapter can both import and export changes.
        """
        return False

    @property
    def supports_webhooks(self) -> bool:
        """
        Whether adapter supports real-time webhooks for updates.

        Override to True if adapter can receive push notifications.
        """
        return False

    # =========================================================================
    # READ OPERATIONS (Abstract - Must Implement)
    # =========================================================================

    @abstractmethod
    def list_projects(self) -> List[Ticket]:
        """
        List all top-level projects/roadmaps.

        Returns:
            List of Ticket objects with hierarchy_type=PROJECT
        """
        pass

    @abstractmethod
    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """
        Get a single ticket by ID.

        Args:
            ticket_id: The ticket identifier (format depends on adapter)

        Returns:
            Ticket object if found, None otherwise
        """
        pass

    @abstractmethod
    def list_children(self, parent_id: str) -> List[Ticket]:
        """
        List direct children of a ticket.

        Args:
            parent_id: ID of the parent ticket

        Returns:
            List of child Ticket objects
        """
        pass

    @abstractmethod
    def search_tickets(
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
        Search tickets with filters.

        All filter parameters are optional and should be combined with AND logic.

        Args:
            query: Free-text search in name/description
            hierarchy_type: Filter by hierarchy level
            status: Filter by ticket status
            assignee: Filter by assigned user
            labels: Filter by labels (tickets must have ALL specified labels)
            parent_id: Filter by parent ticket
            limit: Maximum results to return
            offset: Number of results to skip (for pagination)

        Returns:
            List of matching Ticket objects
        """
        pass

    # =========================================================================
    # WRITE OPERATIONS (Abstract - Must Implement)
    # =========================================================================

    @abstractmethod
    def create_ticket(self, ticket: Ticket) -> Ticket:
        """
        Create a new ticket.

        Args:
            ticket: Ticket object with data for the new ticket
                   (id may be None, adapter will assign)

        Returns:
            Created Ticket object with assigned ID and any defaults
        """
        pass

    @abstractmethod
    def update_ticket(self, ticket: Ticket) -> Ticket:
        """
        Update an existing ticket.

        Args:
            ticket: Ticket object with updated data
                   (id must be set to existing ticket)

        Returns:
            Updated Ticket object
        """
        pass

    @abstractmethod
    def update_status(self, ticket_id: str, status: TicketStatus) -> Ticket:
        """
        Update ticket status.

        This is a convenience method for the common operation of changing
        only the status. Adapters should also update related timestamps
        (started_at, completed_at).

        Args:
            ticket_id: ID of ticket to update
            status: New status value

        Returns:
            Updated Ticket object
        """
        pass

    @abstractmethod
    def delete_ticket(self, ticket_id: str) -> bool:
        """
        Delete a ticket.

        Args:
            ticket_id: ID of ticket to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    # =========================================================================
    # SYNC OPERATIONS (Optional - Override if supported)
    # =========================================================================

    def sync(
        self,
        direction: SyncDirection = SyncDirection.IMPORT,
        conflict_resolution: str = "manual",
    ) -> SyncResult:
        """
        Synchronize with external system.

        Override in adapters that support sync. The default implementation
        raises NotImplementedError.

        Args:
            direction: Direction of sync (import, export, or bidirectional)
            conflict_resolution: How to resolve conflicts
                                ('local_wins', 'remote_wins', 'manual', 'merge')

        Returns:
            SyncResult with details of the sync operation

        Raises:
            NotImplementedError: If adapter doesn't support sync
        """
        raise NotImplementedError(f"{self.adapter_name} does not support sync")

    def detect_conflicts(self, other_adapter: "TicketAdapter") -> List[Dict[str, Any]]:
        """
        Detect conflicts between this adapter and another.

        Override in adapters that support bidirectional sync.
        The default implementation returns an empty list.

        Args:
            other_adapter: The adapter to compare against

        Returns:
            List of conflict dictionaries with details
        """
        return []

    # =========================================================================
    # MAPPING (Abstract - Must Implement)
    # =========================================================================

    @abstractmethod
    def map_to_generic(self, native_item: Any) -> Ticket:
        """
        Convert adapter's native model to generic Ticket.

        This is the core conversion logic that transforms tool-specific
        data into the universal Ticket format.

        Args:
            native_item: Native model object from this adapter's tool

        Returns:
            Ticket object with data mapped from native model
        """
        pass

    @abstractmethod
    def map_from_generic(self, ticket: Ticket) -> Any:
        """
        Convert generic Ticket to adapter's native model.

        This is the reverse of map_to_generic, used when writing
        data back to the tool.

        Args:
            ticket: Generic Ticket object

        Returns:
            Native model object for this adapter's tool
        """
        pass

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def is_available(self) -> bool:
        """
        Check if the adapter is available and properly configured.

        Override to add configuration checks (e.g., API credentials).
        Default returns True.
        """
        return True

    def validate_config(self) -> List[str]:
        """
        Validate adapter configuration.

        Override to check required configuration settings.
        Returns list of error messages (empty if valid).
        """
        return []

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.adapter_name})>"
