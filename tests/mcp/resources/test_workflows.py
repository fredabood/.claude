"""Tests for WorkflowResourceProvider."""

import json
import pytest
from vibey.mcp.resources.workflows import WorkflowResourceProvider
from vibey.mcp.resources.exceptions import ResourceNotFoundError


class TestWorkflowResourceProvider:
    """Tests for WorkflowResourceProvider class."""

    @pytest.fixture
    def workflow_provider(self, content_root):
        """Create WorkflowResourceProvider with test content."""
        return WorkflowResourceProvider(content_root)

    def test_initialization(self, workflow_provider):
        """Test provider initialization."""
        assert workflow_provider is not None

    def test_get_templates(self, workflow_provider):
        """Test getting resource templates."""
        templates = workflow_provider.get_templates()
        assert len(templates) >= 4
        uri_templates = [t.uriTemplate for t in templates]
        assert "vibey://workflows/{workflow_id}" in uri_templates
        assert "vibey://workflows/{workflow_id}/steps" in uri_templates
        assert "vibey://workflows/{workflow_id}/quality-gates" in uri_templates
        assert "vibey://workflows/{workflow_id}/metadata" in uri_templates

    def test_template_structure(self, workflow_provider):
        """Test that templates have correct structure."""
        templates = workflow_provider.get_templates()
        for template in templates:
            assert hasattr(template, "uriTemplate")
            assert hasattr(template, "name")
            assert hasattr(template, "description")
            assert template.uriTemplate.startswith("vibey://workflows/")

    def test_list_resources_returns_list(self, workflow_provider):
        """Test listing workflow resources returns a list."""
        resources = workflow_provider.list_resources("vibey://workflows/{workflow_id}")
        assert isinstance(resources, list)

    def test_supports_uri_workflow(self, workflow_provider):
        """Test URI support for workflow URIs."""
        assert workflow_provider.supports_uri("vibey://workflows/test")
        assert workflow_provider.supports_uri("vibey://workflows/test/steps")
        assert workflow_provider.supports_uri("vibey://workflows/test/quality-gates")
        assert workflow_provider.supports_uri("vibey://workflows/test/metadata")

    def test_supports_uri_non_workflow(self, workflow_provider):
        """Test URI support for non-workflow URIs."""
        assert not workflow_provider.supports_uri("vibey://handoffs/test")
        assert not workflow_provider.supports_uri("vibey://agents/test")
        assert not workflow_provider.supports_uri("http://example.com")

    @pytest.mark.asyncio
    async def test_read_workflow_not_found(self, workflow_provider):
        """Test reading non-existent workflow."""
        with pytest.raises(ResourceNotFoundError):
            await workflow_provider.read_resource("vibey://workflows/non-existent")

    @pytest.mark.asyncio
    async def test_read_workflow_steps_not_found(self, workflow_provider):
        """Test reading steps for non-existent workflow."""
        with pytest.raises(ResourceNotFoundError):
            await workflow_provider.read_resource("vibey://workflows/non-existent/steps")

    def test_invalidate_cache(self, workflow_provider):
        """Test cache invalidation."""
        # First access
        workflow_provider._get_workflows()
        # Invalidate should not raise
        workflow_provider.invalidate_cache()
        # Cache should be None after invalidation
        assert workflow_provider._cache is None

    def test_get_workflows_method(self, workflow_provider):
        """Test _get_workflows internal method."""
        workflows = workflow_provider._get_workflows()
        assert isinstance(workflows, list)

    def test_find_workflow_not_found(self, workflow_provider):
        """Test _find_workflow returns None for non-existent workflow."""
        result = workflow_provider._find_workflow("non-existent-workflow")
        assert result is None


class TestWorkflowResourceProviderWithRealContent:
    """Tests using real vibey content."""

    @pytest.fixture
    def real_workflow_provider(self, real_content_root):
        """Create WorkflowResourceProvider with real content."""
        return WorkflowResourceProvider(real_content_root)

    def test_discovers_real_workflows(self, real_workflow_provider):
        """Test that real workflows are discovered."""
        workflows = real_workflow_provider._get_workflows()
        # Should have at least some workflows in the real codebase
        assert len(workflows) >= 1

    def test_list_real_resources(self, real_workflow_provider):
        """Test listing real workflow resources."""
        resources = real_workflow_provider.list_resources("vibey://workflows/{workflow_id}")
        assert len(resources) >= 1

    @pytest.mark.asyncio
    async def test_read_real_workflow(self, real_workflow_provider):
        """Test reading a real workflow."""
        workflows = real_workflow_provider._get_workflows()
        if workflows:
            first_workflow = workflows[0]
            uri = f"vibey://workflows/{first_workflow.id}"
            content = await real_workflow_provider.read_resource(uri)
            assert content.mimeType == "text/markdown"
            assert content.text is not None

    @pytest.mark.asyncio
    async def test_read_real_workflow_steps(self, real_workflow_provider):
        """Test reading steps from a real workflow."""
        workflows = real_workflow_provider._get_workflows()
        if workflows:
            first_workflow = workflows[0]
            uri = f"vibey://workflows/{first_workflow.id}/steps"
            content = await real_workflow_provider.read_resource(uri)
            assert content.mimeType == "application/json"
            data = json.loads(content.text)
            assert "workflow_id" in data
            assert "steps" in data
