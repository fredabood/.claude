"""Tests for HandoffResourceProvider."""

import json
import pytest
from vibey.mcp.resources.handoffs import HandoffResourceProvider
from vibey.mcp.resources.exceptions import ResourceNotFoundError


class TestHandoffResourceProvider:
    """Tests for HandoffResourceProvider class."""

    @pytest.fixture
    def handoff_provider(self, content_root):
        """Create HandoffResourceProvider with test content."""
        return HandoffResourceProvider(content_root)

    def test_initialization(self, handoff_provider):
        """Test provider initialization."""
        assert handoff_provider is not None

    def test_get_templates(self, handoff_provider):
        """Test getting resource templates."""
        templates = handoff_provider.get_templates()
        assert len(templates) >= 4
        uri_templates = [t.uriTemplate for t in templates]
        assert "vibey://handoffs/{handoff_id}" in uri_templates
        assert "vibey://handoffs/{handoff_id}/variables" in uri_templates
        assert "vibey://handoffs/{handoff_id}/metadata" in uri_templates
        assert "vibey://handoffs/{handoff_id}/rendered" in uri_templates

    def test_template_structure(self, handoff_provider):
        """Test that templates have correct structure."""
        templates = handoff_provider.get_templates()
        for template in templates:
            assert hasattr(template, "uriTemplate")
            assert hasattr(template, "name")
            assert hasattr(template, "description")
            assert template.uriTemplate.startswith("vibey://handoffs/")

    def test_list_resources(self, handoff_provider):
        """Test listing handoff resources."""
        resources = handoff_provider.list_resources("vibey://handoffs/{handoff_id}")
        assert len(resources) >= 1
        assert any("test-handoff" in r.uri for r in resources)

    def test_list_resources_variables(self, handoff_provider):
        """Test listing handoff variables resources."""
        resources = handoff_provider.list_resources("vibey://handoffs/{handoff_id}/variables")
        assert len(resources) >= 1
        assert any("test-handoff" in r.uri and "variables" in r.uri for r in resources)

    def test_supports_uri_handoff(self, handoff_provider):
        """Test URI support for handoff URIs."""
        assert handoff_provider.supports_uri("vibey://handoffs/test")
        assert handoff_provider.supports_uri("vibey://handoffs/test/variables")
        assert handoff_provider.supports_uri("vibey://handoffs/test/metadata")
        assert handoff_provider.supports_uri("vibey://handoffs/test/rendered")

    def test_supports_uri_non_handoff(self, handoff_provider):
        """Test URI support for non-handoff URIs."""
        assert not handoff_provider.supports_uri("vibey://workflows/test")
        assert not handoff_provider.supports_uri("vibey://agents/test")
        assert not handoff_provider.supports_uri("http://example.com")

    @pytest.mark.asyncio
    async def test_read_handoff_content(self, handoff_provider):
        """Test reading full handoff content."""
        content = await handoff_provider.read_resource("vibey://handoffs/test-handoff")
        # MIME type may include +jinja2 suffix
        assert "text/markdown" in content.mimeType
        assert content.text is not None
        assert content.uri == "vibey://handoffs/test-handoff"

    @pytest.mark.asyncio
    async def test_read_handoff_variables(self, handoff_provider):
        """Test reading handoff variable schema as JSON Schema."""
        content = await handoff_provider.read_resource("vibey://handoffs/test-handoff/variables")
        assert content.mimeType == "application/json"
        schema = json.loads(content.text)
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "test_var" in schema["properties"]
        assert "required" in schema
        assert "test_var" in schema["required"]

    @pytest.mark.asyncio
    async def test_read_handoff_metadata(self, handoff_provider):
        """Test reading handoff metadata as JSON."""
        content = await handoff_provider.read_resource("vibey://handoffs/test-handoff/metadata")
        assert content.mimeType == "application/json"
        data = json.loads(content.text)
        assert "id" in data
        assert data["id"] == "test-handoff"
        assert "name" in data
        assert data["name"] == "Test Handoff"
        assert "from_agent" in data
        assert "to_agents" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_read_handoff_rendered(self, handoff_provider):
        """Test reading rendered handoff with sample values."""
        content = await handoff_provider.read_resource("vibey://handoffs/test-handoff/rendered")
        assert content.mimeType == "text/markdown"
        # Should have sample values, not raw Jinja2 variables
        # The rendered content should show the variable placeholders or sample values

    @pytest.mark.asyncio
    async def test_read_handoff_not_found(self, handoff_provider):
        """Test reading non-existent handoff."""
        with pytest.raises(ResourceNotFoundError):
            await handoff_provider.read_resource("vibey://handoffs/non-existent")

    @pytest.mark.asyncio
    async def test_read_handoff_variables_not_found(self, handoff_provider):
        """Test reading variables for non-existent handoff."""
        with pytest.raises(ResourceNotFoundError):
            await handoff_provider.read_resource("vibey://handoffs/non-existent/variables")

    def test_invalidate_cache(self, handoff_provider):
        """Test cache invalidation."""
        # First discovery
        handoff_provider.list_resources("vibey://handoffs/{handoff_id}")
        # Invalidate should not raise
        handoff_provider.invalidate_cache()

    def test_resource_has_name_and_description(self, handoff_provider):
        """Test that resources have name and description."""
        resources = handoff_provider.list_resources("vibey://handoffs/{handoff_id}")
        for resource in resources:
            assert hasattr(resource, "name")
            assert hasattr(resource, "description")
            assert resource.name is not None


class TestHandoffResourceProviderWithRealContent:
    """Tests using real vibey content."""

    @pytest.fixture
    def real_handoff_provider(self, real_content_root):
        """Create HandoffResourceProvider with real content."""
        return HandoffResourceProvider(real_content_root)

    def test_discovers_real_handoffs(self, real_handoff_provider):
        """Test that real handoffs are discovered."""
        handoffs = real_handoff_provider._discover_handoffs()
        # Should have at least some handoffs in the real codebase
        assert len(handoffs) >= 1

    def test_list_real_resources(self, real_handoff_provider):
        """Test listing real handoff resources."""
        resources = real_handoff_provider.list_resources("vibey://handoffs/{handoff_id}")
        assert len(resources) >= 1

    @pytest.mark.asyncio
    async def test_read_real_handoff(self, real_handoff_provider):
        """Test reading a real handoff."""
        handoffs = real_handoff_provider._discover_handoffs()
        if handoffs:
            first_handoff = handoffs[0]
            uri = f"vibey://handoffs/{first_handoff.id}"
            content = await real_handoff_provider.read_resource(uri)
            assert "text/markdown" in content.mimeType
            assert content.text is not None

    @pytest.mark.asyncio
    async def test_read_real_handoff_variables(self, real_handoff_provider):
        """Test reading variables from a real handoff."""
        handoffs = real_handoff_provider._discover_handoffs()
        if handoffs:
            first_handoff = handoffs[0]
            uri = f"vibey://handoffs/{first_handoff.id}/variables"
            content = await real_handoff_provider.read_resource(uri)
            assert content.mimeType == "application/json"
            data = json.loads(content.text)
            assert "type" in data
            assert data["type"] == "object"
