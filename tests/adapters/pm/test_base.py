"""
Tests for vibey/adapters/pm/base.py - TicketAdapter ABC.

Tests cover:
- TicketAdapter cannot be instantiated directly
- Subclasses must implement abstract methods
- Capability property defaults
- Default sync behavior
"""

import pytest
from typing import Any, Dict, List, Optional

from vibey.adapters.pm.base import TicketAdapter
from vibey.adapters.pm.types import PMCapabilities, SyncDirection, SyncResult
from vibey.core.ticket import HierarchyType, Ticket, TicketStatus


class TestTicketAdapterABC:
    """Test TicketAdapter abstract base class."""

    def test_cannot_instantiate_directly(self):
        """Verify TicketAdapter cannot be instantiated."""
        with pytest.raises(TypeError) as exc_info:
            TicketAdapter()
        assert "abstract" in str(exc_info.value).lower()

    def test_incomplete_subclass_fails(self):
        """Verify incomplete subclass cannot be instantiated."""

        class IncompleteAdapter(TicketAdapter):
            @property
            def adapter_name(self) -> str:
                return "incomplete"

            # Missing other abstract methods

        with pytest.raises(TypeError):
            IncompleteAdapter()


class MockAdapter(TicketAdapter):
    """Complete mock adapter for testing."""

    @property
    def adapter_name(self) -> str:
        return "mock"

    @property
    def display_name(self) -> str:
        return "Mock Adapter"

    def list_projects(self) -> List[Ticket]:
        return [
            Ticket(id="P1", name="Project 1", hierarchy_type=HierarchyType.PROJECT, source_adapter="mock")
        ]

    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        if ticket_id == "P1":
            return Ticket(id="P1", name="Project 1", hierarchy_type=HierarchyType.PROJECT, source_adapter="mock")
        return None

    def list_children(self, parent_id: str) -> List[Ticket]:
        return []

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
        return []

    def create_ticket(self, ticket: Ticket) -> Ticket:
        return ticket

    def update_ticket(self, ticket: Ticket) -> Ticket:
        return ticket

    def update_status(self, ticket_id: str, status: TicketStatus) -> Ticket:
        return Ticket(id=ticket_id, name="Updated", hierarchy_type=HierarchyType.WORK_ITEM, source_adapter="mock", status=status)

    def delete_ticket(self, ticket_id: str) -> bool:
        return True

    def map_to_generic(self, native_item: Any) -> Ticket:
        return Ticket(id="mapped", name="Mapped", hierarchy_type=HierarchyType.WORK_ITEM, source_adapter="mock")

    def map_from_generic(self, ticket: Ticket) -> Any:
        return {"id": ticket.id, "name": ticket.name}


class TestMockAdapter:
    """Test complete mock adapter works correctly."""

    @pytest.fixture
    def adapter(self):
        return MockAdapter()

    def test_adapter_name(self, adapter):
        """Test adapter_name property."""
        assert adapter.adapter_name == "mock"

    def test_display_name(self, adapter):
        """Test display_name property."""
        assert adapter.display_name == "Mock Adapter"

    def test_list_projects(self, adapter):
        """Test list_projects method."""
        projects = adapter.list_projects()
        assert len(projects) == 1
        assert projects[0].id == "P1"

    def test_get_ticket_found(self, adapter):
        """Test get_ticket returns ticket when found."""
        ticket = adapter.get_ticket("P1")
        assert ticket is not None
        assert ticket.id == "P1"

    def test_get_ticket_not_found(self, adapter):
        """Test get_ticket returns None when not found."""
        ticket = adapter.get_ticket("NONEXISTENT")
        assert ticket is None


class TestCapabilityDefaults:
    """Test default capability values."""

    @pytest.fixture
    def adapter(self):
        return MockAdapter()

    def test_supported_hierarchy_types(self, adapter):
        """Test default supported hierarchy types."""
        types = adapter.supported_hierarchy_types
        assert HierarchyType.PROJECT in types
        assert HierarchyType.WORKSTREAM in types
        assert HierarchyType.ITERATION in types
        assert HierarchyType.WORK_ITEM in types

    def test_supports_sprints_default(self, adapter):
        """Test default supports_sprints is True."""
        assert adapter.supports_sprints is True

    def test_supports_bidirectional_sync_default(self, adapter):
        """Test default supports_bidirectional_sync is False."""
        assert adapter.supports_bidirectional_sync is False

    def test_supports_webhooks_default(self, adapter):
        """Test default supports_webhooks is False."""
        assert adapter.supports_webhooks is False

    def test_capabilities_property(self, adapter):
        """Test capabilities property returns PMCapabilities."""
        caps = adapter.capabilities
        assert isinstance(caps, PMCapabilities)
        assert caps.supports_sprints is True
        assert caps.supports_bidirectional_sync is False


class TestCapabilityOverrides:
    """Test capability overrides."""

    def test_override_supports_sprints(self):
        """Test overriding supports_sprints."""

        class NoSprintAdapter(MockAdapter):
            @property
            def supports_sprints(self) -> bool:
                return False

        adapter = NoSprintAdapter()
        assert adapter.supports_sprints is False
        assert adapter.capabilities.supports_sprints is False

    def test_override_supported_hierarchy_types(self):
        """Test overriding supported hierarchy types."""

        class LimitedAdapter(MockAdapter):
            @property
            def supported_hierarchy_types(self) -> List[HierarchyType]:
                return [HierarchyType.PROJECT, HierarchyType.WORK_ITEM]

        adapter = LimitedAdapter()
        types = adapter.supported_hierarchy_types
        assert HierarchyType.PROJECT in types
        assert HierarchyType.WORK_ITEM in types
        assert HierarchyType.ITERATION not in types


class TestSyncDefaults:
    """Test default sync behavior."""

    @pytest.fixture
    def adapter(self):
        return MockAdapter()

    def test_sync_raises_not_implemented(self, adapter):
        """Test default sync raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            adapter.sync()
        assert "mock does not support sync" in str(exc_info.value)

    def test_detect_conflicts_returns_empty(self, adapter):
        """Test default detect_conflicts returns empty list."""
        conflicts = adapter.detect_conflicts(adapter)
        assert conflicts == []


class TestSyncOverrides:
    """Test sync overrides."""

    def test_sync_can_be_overridden(self):
        """Test sync can be overridden in subclass."""

        class SyncableAdapter(MockAdapter):
            @property
            def supports_bidirectional_sync(self) -> bool:
                return True

            def sync(
                self,
                direction: SyncDirection = SyncDirection.IMPORT,
                conflict_resolution: str = "manual",
            ) -> SyncResult:
                from datetime import datetime, timezone
                return SyncResult(
                    success=True,
                    direction=direction,
                    items_imported=5 if direction == SyncDirection.IMPORT else 0,
                    items_exported=3 if direction == SyncDirection.EXPORT else 0,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                )

        adapter = SyncableAdapter()
        result = adapter.sync(direction=SyncDirection.IMPORT)
        assert result.success is True
        assert result.items_imported == 5


class TestUtilityMethods:
    """Test utility methods."""

    @pytest.fixture
    def adapter(self):
        return MockAdapter()

    def test_is_available_default(self, adapter):
        """Test default is_available returns True."""
        assert adapter.is_available() is True

    def test_validate_config_default(self, adapter):
        """Test default validate_config returns empty list."""
        errors = adapter.validate_config()
        assert errors == []

    def test_repr(self, adapter):
        """Test adapter repr."""
        repr_str = repr(adapter)
        assert "MockAdapter" in repr_str
        assert "mock" in repr_str
