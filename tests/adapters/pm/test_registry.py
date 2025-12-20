"""
Tests for vibey/adapters/pm/registry.py - PMAdapterRegistry.

Tests cover:
- Adapter registration
- Adapter retrieval
- Default adapter selection
- Error handling for unknown adapters
- @pm_adapter decorator
"""

import pytest
from typing import Any, List, Optional

from vibey.adapters.pm.base import TicketAdapter
from vibey.adapters.pm.registry import (
    AdapterNotFoundError,
    AdapterRegistrationError,
    PMAdapterRegistry,
    pm_adapter,
)
from vibey.adapters.pm.types import PMCapabilities
from vibey.core.ticket import HierarchyType, Ticket, TicketStatus


class BaseTestAdapter(TicketAdapter):
    """Base test adapter with all abstract methods implemented."""

    @property
    def adapter_name(self) -> str:
        return "base_test"

    @property
    def display_name(self) -> str:
        return "Base Test Adapter"

    def list_projects(self) -> List[Ticket]:
        return []

    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        return None

    def list_children(self, parent_id: str) -> List[Ticket]:
        return []

    def search_tickets(self, **kwargs) -> List[Ticket]:
        return []

    def create_ticket(self, ticket: Ticket) -> Ticket:
        return ticket

    def update_ticket(self, ticket: Ticket) -> Ticket:
        return ticket

    def update_status(self, ticket_id: str, status: TicketStatus) -> Ticket:
        return Ticket(id=ticket_id, name="Test", hierarchy_type=HierarchyType.WORK_ITEM, source_adapter="test", status=status)

    def delete_ticket(self, ticket_id: str) -> bool:
        return True

    def map_to_generic(self, native_item: Any) -> Ticket:
        return Ticket(id="test", name="Test", hierarchy_type=HierarchyType.WORK_ITEM, source_adapter="test")

    def map_from_generic(self, ticket: Ticket) -> Any:
        return {}


class TestAdapter1(BaseTestAdapter):
    @property
    def adapter_name(self) -> str:
        return "test_adapter_1"

    @property
    def display_name(self) -> str:
        return "Test Adapter 1"


class TestAdapter2(BaseTestAdapter):
    @property
    def adapter_name(self) -> str:
        return "test_adapter_2"

    @property
    def display_name(self) -> str:
        return "Test Adapter 2"


@pytest.fixture(autouse=True)
def clean_registry():
    """Clean registry before each test."""
    PMAdapterRegistry.clear()
    yield
    PMAdapterRegistry.clear()


class TestRegistration:
    """Test adapter registration."""

    def test_register_adapter(self):
        """Test registering an adapter."""
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        assert PMAdapterRegistry.is_registered("adapter1")

    def test_register_sets_first_as_default(self):
        """Test first registered adapter becomes default."""
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        assert PMAdapterRegistry.get_default_name() == "adapter1"

    def test_register_with_set_default(self):
        """Test registering with set_default=True."""
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        PMAdapterRegistry.register("adapter2", TestAdapter2, set_default=True)
        assert PMAdapterRegistry.get_default_name() == "adapter2"

    def test_register_duplicate_same_class_ok(self):
        """Test registering same class twice is allowed."""
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        PMAdapterRegistry.register("adapter1", TestAdapter1)  # Should not raise

    def test_register_duplicate_different_class_fails(self):
        """Test registering different class with same name fails."""
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        with pytest.raises(AdapterRegistrationError):
            PMAdapterRegistry.register("adapter1", TestAdapter2)

    def test_register_invalid_name_fails(self):
        """Test registering with invalid name fails."""
        with pytest.raises(AdapterRegistrationError):
            PMAdapterRegistry.register("invalid-name", TestAdapter1)

        with pytest.raises(AdapterRegistrationError):
            PMAdapterRegistry.register("", TestAdapter1)

    def test_register_non_adapter_fails(self):
        """Test registering non-TicketAdapter class fails."""

        class NotAnAdapter:
            pass

        with pytest.raises(AdapterRegistrationError):
            PMAdapterRegistry.register("not_adapter", NotAnAdapter)

    def test_unregister_adapter(self):
        """Test unregistering an adapter."""
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        assert PMAdapterRegistry.is_registered("adapter1")

        result = PMAdapterRegistry.unregister("adapter1")
        assert result is True
        assert not PMAdapterRegistry.is_registered("adapter1")

    def test_unregister_nonexistent(self):
        """Test unregistering nonexistent adapter returns False."""
        result = PMAdapterRegistry.unregister("nonexistent")
        assert result is False

    def test_unregister_clears_default(self):
        """Test unregistering default adapter clears default."""
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        PMAdapterRegistry.unregister("adapter1")
        assert PMAdapterRegistry.get_default_name() is None


class TestRetrieval:
    """Test adapter retrieval."""

    def test_get_adapter(self):
        """Test getting an adapter by name."""
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        adapter = PMAdapterRegistry.get("adapter1")
        assert isinstance(adapter, TestAdapter1)

    def test_get_uses_cache(self):
        """Test get returns cached instance."""
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        adapter1 = PMAdapterRegistry.get("adapter1")
        adapter2 = PMAdapterRegistry.get("adapter1")
        assert adapter1 is adapter2

    def test_get_bypass_cache(self):
        """Test get with use_cache=False creates new instance."""
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        adapter1 = PMAdapterRegistry.get("adapter1")
        adapter2 = PMAdapterRegistry.get("adapter1", use_cache=False)
        assert adapter1 is not adapter2

    def test_get_unknown_adapter_fails(self):
        """Test getting unknown adapter raises error."""
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        with pytest.raises(AdapterNotFoundError) as exc_info:
            PMAdapterRegistry.get("unknown")
        assert "unknown" in str(exc_info.value)
        assert "adapter1" in str(exc_info.value)  # Shows available

    def test_get_default(self):
        """Test getting default adapter."""
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        adapter = PMAdapterRegistry.get_default()
        assert isinstance(adapter, TestAdapter1)

    def test_get_default_no_adapters_fails(self):
        """Test getting default with no adapters raises error."""
        with pytest.raises(AdapterNotFoundError):
            PMAdapterRegistry.get_default()

    def test_set_default(self):
        """Test setting default adapter."""
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        PMAdapterRegistry.register("adapter2", TestAdapter2)
        PMAdapterRegistry.set_default("adapter2")
        assert PMAdapterRegistry.get_default_name() == "adapter2"

    def test_set_default_unknown_fails(self):
        """Test setting unknown adapter as default fails."""
        with pytest.raises(AdapterNotFoundError):
            PMAdapterRegistry.set_default("unknown")


class TestDiscovery:
    """Test adapter discovery."""

    def test_list_adapters(self):
        """Test listing all adapters."""
        PMAdapterRegistry.register("zebra", TestAdapter1)
        PMAdapterRegistry.register("alpha", TestAdapter2)
        adapters = PMAdapterRegistry.list_adapters()
        assert adapters == ["alpha", "zebra"]  # Sorted

    def test_list_adapters_empty(self):
        """Test listing adapters when none registered."""
        adapters = PMAdapterRegistry.list_adapters()
        assert adapters == []

    def test_is_registered(self):
        """Test is_registered check."""
        assert not PMAdapterRegistry.is_registered("adapter1")
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        assert PMAdapterRegistry.is_registered("adapter1")

    def test_get_adapter_info(self):
        """Test getting adapter info."""
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        info = PMAdapterRegistry.get_adapter_info("adapter1")
        assert info.name == "test_adapter_1"
        assert info.display_name == "Test Adapter 1"
        assert info.is_available is True

    def test_list_adapter_info(self):
        """Test listing all adapter info."""
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        PMAdapterRegistry.register("adapter2", TestAdapter2)
        infos = PMAdapterRegistry.list_adapter_info()
        assert len(infos) == 2
        names = {info.name for info in infos}
        assert "test_adapter_1" in names
        assert "test_adapter_2" in names

    def test_get_capabilities(self):
        """Test getting adapter capabilities."""
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        caps = PMAdapterRegistry.get_capabilities("adapter1")
        assert isinstance(caps, PMCapabilities)


class TestDecorator:
    """Test @pm_adapter decorator."""

    def test_pm_adapter_decorator(self):
        """Test @pm_adapter registers adapter."""

        @pm_adapter("decorated")
        class DecoratedAdapter(BaseTestAdapter):
            @property
            def adapter_name(self) -> str:
                return "decorated"

            @property
            def display_name(self) -> str:
                return "Decorated"

        assert PMAdapterRegistry.is_registered("decorated")
        adapter = PMAdapterRegistry.get("decorated")
        assert isinstance(adapter, DecoratedAdapter)

    def test_pm_adapter_decorator_set_default(self):
        """Test @pm_adapter with set_default=True."""
        PMAdapterRegistry.register("existing", TestAdapter1)

        @pm_adapter("new_default", set_default=True)
        class NewDefaultAdapter(BaseTestAdapter):
            @property
            def adapter_name(self) -> str:
                return "new_default"

            @property
            def display_name(self) -> str:
                return "New Default"

        assert PMAdapterRegistry.get_default_name() == "new_default"


class TestClear:
    """Test registry clear."""

    def test_clear_removes_all(self):
        """Test clear removes all adapters."""
        PMAdapterRegistry.register("adapter1", TestAdapter1)
        PMAdapterRegistry.register("adapter2", TestAdapter2)
        PMAdapterRegistry.clear()
        assert PMAdapterRegistry.list_adapters() == []
        assert PMAdapterRegistry.get_default_name() is None
