"""Tests for ResourceManager."""

import pytest
from vibey.mcp.resources.manager import ResourceManager
from vibey.mcp.resources.exceptions import ProviderNotFoundError


class TestResourceManager:
    """Tests for ResourceManager class."""

    def test_initialization(self, content_root):
        """Test that ResourceManager initializes correctly."""
        manager = ResourceManager(content_root)
        assert manager is not None
        assert manager.content_root == content_root

    def test_lazy_initialization(self, content_root):
        """Test that providers are registered lazily."""
        manager = ResourceManager(content_root)
        # Providers shouldn't be registered until first access
        assert manager._initialized is False
        # Access triggers initialization
        manager.get_all_templates()
        assert manager._initialized is True

    def test_get_all_templates(self, resource_manager):
        """Test getting all resource templates."""
        templates = resource_manager.get_all_templates()
        assert len(templates) > 0
        # Should have templates from workflows and handoffs providers
        uri_templates = [t.uriTemplate for t in templates]
        assert any("workflows" in t for t in uri_templates)
        assert any("handoffs" in t for t in uri_templates)

    def test_get_all_templates_dict(self, resource_manager):
        """Test getting templates as dictionaries."""
        templates = resource_manager.get_all_templates_dict()
        assert isinstance(templates, list)
        assert len(templates) > 0
        assert all(isinstance(t, dict) for t in templates)
        assert all("uriTemplate" in t for t in templates)

    def test_list_all_resources(self, resource_manager):
        """Test listing all resources."""
        resources = resource_manager.list_all_resources()
        assert isinstance(resources, list)
        # May be empty with test fixtures, but should work
        if resources:
            assert all(hasattr(r, "uri") for r in resources)

    def test_list_all_resources_dict(self, resource_manager):
        """Test listing resources as dictionaries."""
        resources = resource_manager.list_all_resources_dict()
        assert isinstance(resources, list)
        if resources:
            assert all(isinstance(r, dict) for r in resources)
            assert all("uri" in r for r in resources)

    def test_list_resources_by_category_handoffs(self, resource_manager):
        """Test listing resources by handoff category."""
        resources = resource_manager.list_resources_by_category("handoffs")
        assert len(resources) >= 1
        assert all("handoff" in r.uri for r in resources)

    def test_list_resources_by_category_unknown(self, resource_manager):
        """Test listing resources for unknown category."""
        resources = resource_manager.list_resources_by_category("unknown")
        assert len(resources) == 0

    @pytest.mark.asyncio
    async def test_read_resource_handoff(self, resource_manager):
        """Test reading a handoff resource."""
        content = await resource_manager.read_resource("vibey://handoffs/test-handoff")
        assert content is not None
        # MIME type may include +jinja2 suffix
        assert "text/markdown" in content.mimeType
        assert content.text is not None

    @pytest.mark.asyncio
    async def test_read_resource_invalid_uri(self, resource_manager):
        """Test reading an invalid resource URI."""
        with pytest.raises(ProviderNotFoundError):
            await resource_manager.read_resource("vibey://invalid/resource")

    def test_get_provider_for_uri_workflows(self, resource_manager):
        """Test getting provider for workflow URI."""
        provider = resource_manager.get_provider_for_uri("vibey://workflows/test")
        assert provider is not None

    def test_get_provider_for_uri_handoffs(self, resource_manager):
        """Test getting provider for handoff URI."""
        provider = resource_manager.get_provider_for_uri("vibey://handoffs/test")
        assert provider is not None

    def test_get_provider_for_uri_unknown(self, resource_manager):
        """Test getting provider for unknown URI."""
        provider = resource_manager.get_provider_for_uri("vibey://unknown/resource")
        assert provider is None

    def test_invalidate_all_caches(self, resource_manager):
        """Test invalidating all provider caches."""
        # First access to populate caches
        resource_manager.list_all_resources()
        # Invalidate should not raise
        resource_manager.invalidate_all_caches()

    def test_get_stats(self, resource_manager):
        """Test getting manager statistics."""
        stats = resource_manager.get_stats()
        assert "provider_count" in stats
        assert "providers" in stats
        assert "template_count" in stats
        assert "resource_count" in stats
        assert stats["provider_count"] >= 2
        assert "workflows" in stats["providers"]
        assert "handoffs" in stats["providers"]

    def test_register_provider(self, content_root):
        """Test registering a custom provider."""
        from vibey.mcp.resources.handoffs import HandoffResourceProvider

        manager = ResourceManager(content_root)
        custom_provider = HandoffResourceProvider(content_root)
        manager.register_provider("custom-handoffs", custom_provider)

        assert "custom-handoffs" in manager.providers

    def test_providers_registered_after_initialization(self, resource_manager):
        """Test that default providers are registered."""
        # Force initialization
        resource_manager._ensure_initialized()
        assert "workflows" in resource_manager.providers
        assert "handoffs" in resource_manager.providers


class TestResourceManagerWithRealContent:
    """Tests using real vibey content."""

    @pytest.fixture
    def real_resource_manager(self, real_content_root):
        """Create ResourceManager with real content."""
        return ResourceManager(real_content_root)

    def test_list_real_resources(self, real_resource_manager):
        """Test listing real resources."""
        resources = real_resource_manager.list_all_resources()
        assert len(resources) >= 1

    @pytest.mark.asyncio
    async def test_read_real_resource(self, real_resource_manager):
        """Test reading a real resource."""
        resources = real_resource_manager.list_all_resources()
        if resources:
            first_resource = resources[0]
            content = await real_resource_manager.read_resource(first_resource.uri)
            assert content is not None
            assert content.text is not None or content.blob is not None
