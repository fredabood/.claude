"""
Tests for vibey/services/ticket_service.py - TicketService.

Tests cover:
- Service initialization with mock adapter
- All read operations
- All write operations
- Convenience methods (start, complete, block)
- Adapter switching
"""

import pytest
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from vibey.adapters.pm.base import TicketAdapter
from vibey.adapters.pm.registry import PMAdapterRegistry, pm_adapter
from vibey.adapters.pm.types import SyncDirection, SyncResult
from vibey.core.ticket import HierarchyType, Ticket, TicketStatus
from vibey.services.ticket_service import (
    InvalidOperationError,
    TicketNotFoundError,
    TicketService,
    TicketServiceError,
)


class MockAdapter(TicketAdapter):
    """Mock adapter for testing TicketService."""

    def __init__(self):
        self._tickets: Dict[str, Ticket] = {}
        self._projects = [
            Ticket(id="PROJ-1", name="Project 1", hierarchy_type=HierarchyType.PROJECT, source_adapter="mock"),
            Ticket(id="PROJ-2", name="Project 2", hierarchy_type=HierarchyType.PROJECT, source_adapter="mock"),
        ]
        self._children = {
            "PROJ-1": [
                Ticket(id="TRACK-1", name="Track 1", hierarchy_type=HierarchyType.WORKSTREAM, source_adapter="mock", parent_id="PROJ-1"),
                Ticket(id="SPRINT-1", name="Sprint 1", hierarchy_type=HierarchyType.ITERATION, source_adapter="mock", parent_id="PROJ-1"),
            ],
            "TRACK-1": [
                Ticket(id="TASK-1", name="Task 1", hierarchy_type=HierarchyType.WORK_ITEM, source_adapter="mock", parent_id="TRACK-1"),
            ],
        }
        # Initialize tickets dict
        for proj in self._projects:
            self._tickets[proj.id] = proj
        for children in self._children.values():
            for child in children:
                self._tickets[child.id] = child

    @property
    def adapter_name(self) -> str:
        return "mock"

    @property
    def display_name(self) -> str:
        return "Mock Adapter"

    def list_projects(self) -> List[Ticket]:
        return self._projects.copy()

    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        return self._tickets.get(ticket_id)

    def list_children(self, parent_id: str) -> List[Ticket]:
        return self._children.get(parent_id, [])

    def search_tickets(
        self,
        query: Optional[str] = None,
        hierarchy_type: Optional[HierarchyType] = None,
        status: Optional[TicketStatus] = None,
        **kwargs,
    ) -> List[Ticket]:
        results = list(self._tickets.values())
        if hierarchy_type:
            results = [t for t in results if t.hierarchy_type == hierarchy_type]
        if status:
            results = [t for t in results if t.status == status]
        if query:
            results = [t for t in results if query.lower() in t.name.lower()]
        return results

    def create_ticket(self, ticket: Ticket) -> Ticket:
        self._tickets[ticket.id] = ticket
        return ticket

    def update_ticket(self, ticket: Ticket) -> Ticket:
        self._tickets[ticket.id] = ticket
        return ticket

    def update_status(self, ticket_id: str, status: TicketStatus) -> Ticket:
        ticket = self._tickets.get(ticket_id)
        if ticket:
            ticket.status = status
            if status == TicketStatus.IN_PROGRESS and not ticket.started_at:
                ticket.started_at = datetime.now(timezone.utc)
            elif status == TicketStatus.COMPLETED:
                ticket.completed_at = datetime.now(timezone.utc)
            self._tickets[ticket_id] = ticket
            return ticket
        raise ValueError(f"Ticket not found: {ticket_id}")

    def delete_ticket(self, ticket_id: str) -> bool:
        if ticket_id in self._tickets:
            del self._tickets[ticket_id]
            return True
        return False

    def map_to_generic(self, native_item: Any) -> Ticket:
        return Ticket(id="mapped", name="Mapped", hierarchy_type=HierarchyType.WORK_ITEM, source_adapter="mock")

    def map_from_generic(self, ticket: Ticket) -> Any:
        return {"id": ticket.id}


@pytest.fixture(autouse=True)
def clean_registry():
    """Clean registry before each test."""
    PMAdapterRegistry.clear()
    PMAdapterRegistry.register("mock", MockAdapter, set_default=True)
    yield
    PMAdapterRegistry.clear()


@pytest.fixture
def adapter():
    """Get a mock adapter instance."""
    return MockAdapter()


@pytest.fixture
def service(adapter):
    """Get a ticket service with mock adapter."""
    return TicketService(adapter=adapter)


class TestServiceInitialization:
    """Test TicketService initialization."""

    def test_init_with_adapter_instance(self, adapter):
        """Test init with adapter instance."""
        service = TicketService(adapter=adapter)
        assert service.adapter is adapter

    def test_init_with_adapter_name(self):
        """Test init with adapter name string."""
        service = TicketService(adapter="mock")
        assert service.adapter_name == "mock"

    def test_init_with_default(self):
        """Test init uses default adapter."""
        service = TicketService()
        assert service.adapter_name == "mock"

    def test_init_unknown_adapter_fails(self):
        """Test init with unknown adapter name fails."""
        from vibey.adapters.pm import AdapterNotFoundError
        with pytest.raises(AdapterNotFoundError):
            TicketService(adapter="unknown")


class TestProperties:
    """Test service properties."""

    def test_adapter_property(self, service, adapter):
        """Test adapter property."""
        assert service.adapter is adapter

    def test_adapter_name(self, service):
        """Test adapter_name property."""
        assert service.adapter_name == "mock"

    def test_display_name(self, service):
        """Test display_name property."""
        assert service.display_name == "Mock Adapter"


class TestAdapterManagement:
    """Test adapter switching."""

    def test_set_adapter_by_name(self, service):
        """Test switching adapter by name."""
        # Register another adapter
        PMAdapterRegistry.register("mock2", MockAdapter)
        service.set_adapter("mock2")
        # Note: Both use MockAdapter, but this tests the switching mechanism

    def test_set_adapter_by_instance(self, service):
        """Test switching adapter by instance."""
        new_adapter = MockAdapter()
        service.set_adapter(new_adapter)
        assert service.adapter is new_adapter

    def test_get_capabilities(self, service):
        """Test getting capabilities."""
        caps = service.get_capabilities()
        assert isinstance(caps, dict)
        assert "supports_sprints" in caps


class TestReadOperations:
    """Test read operations."""

    def test_list_projects(self, service):
        """Test listing projects."""
        projects = service.list_projects()
        assert len(projects) == 2
        assert all(p.hierarchy_type == HierarchyType.PROJECT for p in projects)

    def test_get_ticket(self, service):
        """Test getting a ticket."""
        ticket = service.get_ticket("PROJ-1")
        assert ticket.id == "PROJ-1"
        assert ticket.name == "Project 1"

    def test_get_ticket_not_found(self, service):
        """Test getting nonexistent ticket raises error."""
        with pytest.raises(TicketNotFoundError) as exc_info:
            service.get_ticket("NONEXISTENT")
        assert "NONEXISTENT" in str(exc_info.value)

    def test_get_children(self, service):
        """Test getting children."""
        children = service.get_children("PROJ-1")
        assert len(children) == 2

    def test_get_workstreams(self, service):
        """Test getting workstreams (tracks)."""
        workstreams = service.get_workstreams("PROJ-1")
        assert len(workstreams) == 1
        assert workstreams[0].hierarchy_type == HierarchyType.WORKSTREAM

    def test_get_iterations(self, service):
        """Test getting iterations (sprints)."""
        # Need to set up proper hierarchy first
        service.adapter._children["TRACK-1"] = [
            Ticket(id="SPRINT-2", name="Sprint 2", hierarchy_type=HierarchyType.ITERATION, source_adapter="mock", parent_id="TRACK-1"),
            Ticket(id="TASK-1", name="Task 1", hierarchy_type=HierarchyType.WORK_ITEM, source_adapter="mock", parent_id="TRACK-1"),
        ]
        iterations = service.get_iterations("TRACK-1")
        assert len(iterations) == 1
        assert iterations[0].hierarchy_type == HierarchyType.ITERATION

    def test_get_work_items(self, service):
        """Test getting work items (tasks)."""
        work_items = service.get_work_items("TRACK-1")
        assert len(work_items) == 1
        assert work_items[0].hierarchy_type == HierarchyType.WORK_ITEM

    def test_search(self, service):
        """Test search with filters."""
        # Search by hierarchy type
        projects = service.search(hierarchy_type=HierarchyType.PROJECT)
        assert len(projects) == 2

        # Search by query
        results = service.search(query="Task")
        assert len(results) == 1
        assert results[0].name == "Task 1"


class TestWriteOperations:
    """Test write operations."""

    def test_create(self, service):
        """Test creating a ticket."""
        new_ticket = Ticket(
            id="NEW-1",
            name="New Ticket",
            hierarchy_type=HierarchyType.WORK_ITEM,
            source_adapter="mock",
        )
        created = service.create(new_ticket)
        assert created.id == "NEW-1"

        # Verify it was added
        retrieved = service.get_ticket("NEW-1")
        assert retrieved.name == "New Ticket"

    def test_update(self, service):
        """Test updating a ticket."""
        ticket = service.get_ticket("TASK-1")
        ticket.name = "Updated Task"
        updated = service.update(ticket)
        assert updated.name == "Updated Task"

    def test_delete(self, service):
        """Test deleting a ticket."""
        result = service.delete("TASK-1")
        assert result is True

        with pytest.raises(TicketNotFoundError):
            service.get_ticket("TASK-1")

    def test_delete_nonexistent(self, service):
        """Test deleting nonexistent ticket returns False."""
        result = service.delete("NONEXISTENT")
        assert result is False


class TestConvenienceMethods:
    """Test convenience methods (start, complete, block, etc.)."""

    def test_start(self, service):
        """Test starting a ticket."""
        ticket = service.start("TASK-1")
        assert ticket.status == TicketStatus.IN_PROGRESS
        assert ticket.started_at is not None

    def test_start_already_completed_fails(self, service):
        """Test starting completed ticket fails."""
        # First complete the ticket
        service.adapter._tickets["TASK-1"].status = TicketStatus.COMPLETED
        with pytest.raises(InvalidOperationError):
            service.start("TASK-1")

    def test_complete(self, service):
        """Test completing a ticket."""
        ticket = service.complete("TASK-1")
        assert ticket.status == TicketStatus.COMPLETED
        assert ticket.completed_at is not None

    def test_complete_cancelled_fails(self, service):
        """Test completing cancelled ticket fails."""
        service.adapter._tickets["TASK-1"].status = TicketStatus.CANCELLED
        with pytest.raises(InvalidOperationError):
            service.complete("TASK-1")

    def test_block(self, service):
        """Test blocking a ticket."""
        ticket = service.block("TASK-1")
        assert ticket.status == TicketStatus.BLOCKED

    def test_block_with_reason(self, service):
        """Test blocking a ticket with reason."""
        ticket = service.block("TASK-1", reason="Waiting for dependency")
        assert ticket.status == TicketStatus.BLOCKED
        assert ticket.metadata.get("blocked_reason") == "Waiting for dependency"

    def test_block_completed_fails(self, service):
        """Test blocking completed ticket fails."""
        service.adapter._tickets["TASK-1"].status = TicketStatus.COMPLETED
        with pytest.raises(InvalidOperationError):
            service.block("TASK-1")

    def test_unblock(self, service):
        """Test unblocking a ticket."""
        # First block it
        service.adapter._tickets["TASK-1"].status = TicketStatus.BLOCKED
        ticket = service.unblock("TASK-1")
        assert ticket.status == TicketStatus.IN_PROGRESS

    def test_unblock_not_blocked_fails(self, service):
        """Test unblocking non-blocked ticket fails."""
        with pytest.raises(InvalidOperationError):
            service.unblock("TASK-1")

    def test_cancel(self, service):
        """Test cancelling a ticket."""
        ticket = service.cancel("TASK-1")
        assert ticket.status == TicketStatus.CANCELLED

    def test_cancel_with_reason(self, service):
        """Test cancelling with reason."""
        ticket = service.cancel("TASK-1", reason="No longer needed")
        assert ticket.status == TicketStatus.CANCELLED
        assert ticket.metadata.get("cancelled_reason") == "No longer needed"


class TestSyncOperations:
    """Test sync operations."""

    def test_sync_not_implemented(self, service):
        """Test sync raises NotImplementedError for mock adapter."""
        with pytest.raises(NotImplementedError):
            service.sync()


class TestUtilityMethods:
    """Test utility methods."""

    def test_is_available(self, service):
        """Test is_available check."""
        assert service.is_available() is True

    def test_validate(self, service):
        """Test validate returns empty list for mock."""
        errors = service.validate()
        assert errors == []

    def test_repr(self, service):
        """Test service repr."""
        repr_str = repr(service)
        assert "TicketService" in repr_str
        assert "mock" in repr_str
