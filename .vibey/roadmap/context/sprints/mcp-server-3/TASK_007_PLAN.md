# Task 007: Test and Document MCP Enhancements

**Task ID:** 01KC79XW04BECR363WJ42Y335F
**Sprint:** MCP Resources, Prompts & Handoff Discovery
**Complexity:** Medium
**Type:** Testing/Documentation

## Problem Statement

Sprint 3 introduces significant MCP enhancements:
- MCP Resources for workflows and handoffs
- MCP Prompts for quality gates
- Handoff discovery and tool generation

This task ensures all new functionality is:
1. Thoroughly tested with comprehensive test suites
2. Well documented for users and developers
3. Integrated properly with the existing MCP server
4. Ready for production deployment

## Scope

### Components to Test
| Component | Test Type | Coverage Target |
|-----------|-----------|-----------------|
| ResourceManager | Unit + Integration | 90% |
| WorkflowResourceProvider | Unit | 90% |
| HandoffResourceProvider | Unit | 90% |
| PromptManager | Unit + Integration | 90% |
| QualityGatePromptProvider | Unit | 90% |
| HandoffDiscovery | Unit | 90% |
| ToolGenerator (handoffs) | Unit | 90% |
| Server Integration | Integration | 80% |

### Documentation to Create/Update
1. MCP Resources User Guide
2. MCP Prompts User Guide
3. Handoff Discovery Developer Guide
4. API Reference Updates
5. Platform Integration Guide Updates

## Implementation Plan

### Phase 1: Test Infrastructure

**1.1 Create Test Fixtures**
```python
# tests/mcp/conftest.py
import pytest
from pathlib import Path
import tempfile
import shutil

@pytest.fixture
def content_root(tmp_path):
    """Create temporary content directory with test data."""
    # Create directory structure
    content_dir = tmp_path / "vibey" / "content"
    (content_dir / "workflows").mkdir(parents=True)
    (content_dir / "templates" / "handoffs").mkdir(parents=True)
    (content_dir / "agents").mkdir(parents=True)

    # Create test workflow
    workflow_content = '''---
id: test-workflow
name: Test Workflow
type: development
complexity: medium
duration: 2 hours
steps:
  - order: 1
    name: Step 1
    agent: test-agent
quality_gates:
  - name: Test Coverage
    type: testing
    threshold: 80
    blocking: true
---
# Test Workflow
Test workflow content.
'''
    (content_dir / "workflows" / "test-workflow.md").write_text(workflow_content)

    # Create test handoff
    handoff_content = '''---
id: test-handoff
name: Test Handoff
version: 1.0.0
from_agent: agent-a
to_agents:
  - agent-b
purpose: Test handoff template
variables:
  - name: test_var
    type: string
    required: true
    description: Test variable
---
# Test Handoff: {{ handoff_title }}
Variable value: {{ test_var }}
'''
    (content_dir / "templates" / "handoffs" / "test-handoff.md").write_text(handoff_content)

    return tmp_path

@pytest.fixture
def roadmap_root(tmp_path):
    """Create temporary roadmap directory."""
    roadmap_dir = tmp_path / ".vibey" / "roadmap"
    roadmap_dir.mkdir(parents=True)
    return roadmap_dir

@pytest.fixture
def resource_manager(content_root):
    """Create ResourceManager with test content."""
    from vibey.mcp.resources.manager import ResourceManager
    return ResourceManager(content_root)

@pytest.fixture
def prompt_manager(content_root, roadmap_root):
    """Create PromptManager with test content."""
    from vibey.mcp.prompts.manager import PromptManager
    return PromptManager(content_root, roadmap_root)

@pytest.fixture
def tool_discovery(content_root):
    """Create ToolDiscovery with test content."""
    from vibey.mcp.discovery import ToolDiscovery
    return ToolDiscovery(content_root)
```

### Phase 2: Unit Tests

**2.1 Resource Manager Tests**
```python
# tests/mcp/resources/test_manager.py
import pytest
from vibey.mcp.resources.manager import ResourceManager

class TestResourceManager:
    def test_initialization(self, content_root):
        manager = ResourceManager(content_root)
        assert manager is not None
        assert len(manager.providers) >= 2

    def test_get_all_templates(self, resource_manager):
        templates = resource_manager.get_all_templates()
        assert len(templates) > 0
        assert all(hasattr(t, 'uriTemplate') for t in templates)

    def test_list_all_resources(self, resource_manager):
        resources = resource_manager.list_all_resources()
        assert len(resources) > 0
        assert all(hasattr(r, 'uri') for r in resources)

    @pytest.mark.asyncio
    async def test_read_resource(self, resource_manager):
        resources = resource_manager.list_all_resources()
        if resources:
            content = await resource_manager.read_resource(resources[0].uri)
            assert content is not None
            assert content.text is not None or content.blob is not None

    @pytest.mark.asyncio
    async def test_read_invalid_resource(self, resource_manager):
        with pytest.raises(Exception):  # ResourceNotFoundError
            await resource_manager.read_resource("vibey://invalid/resource")
```

**2.2 Workflow Resource Tests**
```python
# tests/mcp/resources/test_workflows.py
import pytest
import json
from vibey.mcp.resources.workflows import WorkflowResourceProvider

class TestWorkflowResourceProvider:
    def test_get_templates(self, content_root):
        provider = WorkflowResourceProvider(content_root)
        templates = provider.get_templates()
        assert len(templates) >= 4
        uri_templates = [t.uriTemplate for t in templates]
        assert "vibey://workflows/{workflow_id}" in uri_templates
        assert "vibey://workflows/{workflow_id}/steps" in uri_templates

    def test_list_resources(self, content_root):
        provider = WorkflowResourceProvider(content_root)
        resources = provider.list_resources("vibey://workflows/{workflow_id}")
        assert len(resources) >= 1
        assert any("test-workflow" in r.uri for r in resources)

    @pytest.mark.asyncio
    async def test_read_workflow_content(self, content_root):
        provider = WorkflowResourceProvider(content_root)
        content = await provider.read_resource("vibey://workflows/test-workflow")
        assert content.mimeType == "text/markdown"
        assert "Test Workflow" in content.text

    @pytest.mark.asyncio
    async def test_read_workflow_steps(self, content_root):
        provider = WorkflowResourceProvider(content_root)
        content = await provider.read_resource("vibey://workflows/test-workflow/steps")
        assert content.mimeType == "application/json"
        data = json.loads(content.text)
        assert "steps" in data
        assert len(data["steps"]) == 1

    @pytest.mark.asyncio
    async def test_read_workflow_quality_gates(self, content_root):
        provider = WorkflowResourceProvider(content_root)
        content = await provider.read_resource("vibey://workflows/test-workflow/quality-gates")
        data = json.loads(content.text)
        assert "quality_gates" in data
        assert len(data["quality_gates"]) == 1
        assert data["quality_gates"][0]["name"] == "Test Coverage"
```

**2.3 Handoff Resource Tests**
```python
# tests/mcp/resources/test_handoffs.py
import pytest
import json
from vibey.mcp.resources.handoffs import HandoffResourceProvider

class TestHandoffResourceProvider:
    def test_discover_handoffs(self, content_root):
        provider = HandoffResourceProvider(content_root)
        handoffs = provider._discover_handoffs()
        assert len(handoffs) >= 1

    def test_get_templates(self, content_root):
        provider = HandoffResourceProvider(content_root)
        templates = provider.get_templates()
        assert len(templates) >= 4

    @pytest.mark.asyncio
    async def test_read_handoff_content(self, content_root):
        provider = HandoffResourceProvider(content_root)
        content = await provider.read_resource("vibey://handoffs/test-handoff")
        assert content.mimeType == "text/markdown"
        assert "test_var" in content.text  # Jinja2 variable in template

    @pytest.mark.asyncio
    async def test_read_handoff_variables(self, content_root):
        provider = HandoffResourceProvider(content_root)
        content = await provider.read_resource("vibey://handoffs/test-handoff/variables")
        schema = json.loads(content.text)
        assert "properties" in schema
        assert "test_var" in schema["properties"]
        assert "required" in schema
        assert "test_var" in schema["required"]

    @pytest.mark.asyncio
    async def test_read_rendered_handoff(self, content_root):
        provider = HandoffResourceProvider(content_root)
        content = await provider.read_resource("vibey://handoffs/test-handoff/rendered")
        assert content.mimeType == "text/markdown"
        # Should have sample value, not raw Jinja2
        assert "{{" not in content.text or "[test_var]" in content.text
```

**2.4 Prompt Tests**
```python
# tests/mcp/prompts/test_quality_gates.py
import pytest
from vibey.mcp.prompts.quality_gates import QualityGatePromptProvider

class TestQualityGatePromptProvider:
    def test_get_prompts(self, content_root):
        provider = QualityGatePromptProvider(content_root)
        prompts = provider.get_prompts()
        assert len(prompts) >= 4
        names = [p.name for p in prompts]
        assert "vibey_quality_gate_check" in names
        assert "vibey_security_scan" in names
        assert "vibey_test_coverage" in names
        assert "vibey_doc_check" in names

    @pytest.mark.asyncio
    async def test_quality_gate_prompt(self, content_root):
        provider = QualityGatePromptProvider(content_root)
        result = await provider.get_prompt(
            "vibey_quality_gate_check",
            {"gate_type": "security", "threshold": "90"}
        )
        assert result.messages is not None
        assert len(result.messages) >= 2
        # Check user message contains security checklist
        user_msg = result.messages[0].content
        assert "security" in user_msg.lower()
        assert "90" in user_msg

    @pytest.mark.asyncio
    async def test_security_scan_prompt(self, content_root):
        provider = QualityGatePromptProvider(content_root)
        result = await provider.get_prompt(
            "vibey_security_scan",
            {"target": "src/auth.py", "focus": "injection"}
        )
        assert result.messages is not None
        user_msg = result.messages[0].content
        assert "injection" in user_msg.lower()
        assert "src/auth.py" in user_msg

    @pytest.mark.asyncio
    async def test_all_gate_types(self, content_root):
        provider = QualityGatePromptProvider(content_root)
        for gate_type in ["security", "testing", "logging", "documentation", "performance"]:
            result = await provider.get_prompt(
                "vibey_quality_gate_check",
                {"gate_type": gate_type}
            )
            assert result.messages is not None
            assert gate_type in result.messages[0].content.lower()
```

**2.5 Handoff Discovery Tests**
```python
# tests/mcp/discovery/test_handoffs.py
import pytest
from vibey.mcp.discovery.handoffs import HandoffDiscovery

class TestHandoffDiscovery:
    def test_discover(self, content_root):
        discovery = HandoffDiscovery(content_root)
        handoffs = discovery.discover()
        assert len(handoffs) >= 1
        assert any(h.id == "test-handoff" for h in handoffs)

    def test_handoff_variables(self, content_root):
        discovery = HandoffDiscovery(content_root)
        handoffs = discovery.discover()
        test_handoff = next(h for h in handoffs if h.id == "test-handoff")
        assert len(test_handoff.variables) == 1
        assert test_handoff.variables[0].name == "test_var"
        assert test_handoff.variables[0].required is True

    def test_get_handoff_by_id(self, content_root):
        discovery = HandoffDiscovery(content_root)
        handoff = discovery.get_handoff_by_id("test-handoff")
        assert handoff is not None
        assert handoff.name == "Test Handoff"

    def test_get_handoffs_from_agent(self, content_root):
        discovery = HandoffDiscovery(content_root)
        handoffs = discovery.get_handoffs_from_agent("agent-a")
        assert len(handoffs) >= 1
        assert all(h.from_agent == "agent-a" for h in handoffs)

    def test_get_handoffs_to_agent(self, content_root):
        discovery = HandoffDiscovery(content_root)
        handoffs = discovery.get_handoffs_to_agent("agent-b")
        assert len(handoffs) >= 1
        assert all("agent-b" in h.to_agents for h in handoffs)

    def test_cache_invalidation(self, content_root):
        discovery = HandoffDiscovery(content_root)
        handoffs1 = discovery.discover()
        discovery.invalidate_cache()
        handoffs2 = discovery.discover()
        assert len(handoffs1) == len(handoffs2)
```

### Phase 3: Integration Tests

**3.1 Server Integration Tests**
```python
# tests/mcp/test_server_integration.py
import pytest
from vibey.mcp.server import VibeyMCPServer

class TestServerIntegration:
    @pytest.fixture
    def server(self, content_root, roadmap_root):
        return VibeyMCPServer(
            roadmap_root=str(roadmap_root),
            framework_root=str(content_root)
        )

    def test_server_initialization(self, server):
        assert server is not None
        assert server.resource_manager is not None
        assert server.prompt_manager is not None

    def test_get_capabilities(self, server):
        caps = server.get_capabilities()
        assert "resources" in caps
        assert "prompts" in caps
        assert caps["resources"]["subscribe"] is True
        assert caps["prompts"]["listChanged"] is True

    def test_get_tools_includes_handoffs(self, server):
        tools = server.get_tools()
        handoff_tools = [t for t in tools if t.get('_metadata', {}).get('asset_type') == 'handoff']
        assert len(handoff_tools) >= 1

    def test_list_resources(self, server):
        resources = server.list_resources()
        assert len(resources) > 0

    def test_list_prompts(self, server):
        prompts = server.list_prompts()
        assert len(prompts) >= 4

    @pytest.mark.asyncio
    async def test_handle_handoff_tool(self, server):
        tools = server.get_tools()
        handoff_tool = next(
            (t for t in tools if "handoff" in t["name"].lower()),
            None
        )
        if handoff_tool:
            result = await server.handle_tool_call(
                handoff_tool["name"],
                {"test_var": "test value"}
            )
            assert not result.get("isError", False)

    @pytest.mark.asyncio
    async def test_get_prompt(self, server):
        result = await server.get_prompt(
            "vibey_quality_gate_check",
            {"gate_type": "security"}
        )
        assert "messages" in result
        assert len(result["messages"]) >= 2
```

### Phase 4: Documentation

**4.1 MCP Resources User Guide**
```markdown
# MCP Resources User Guide

## Overview
Vibey exposes content as MCP Resources, allowing direct access to:
- Workflows and their components
- Handoff templates and schemas
- Agent definitions

## Resource URI Scheme
- `vibey://workflows/{id}` - Full workflow content
- `vibey://workflows/{id}/steps` - Workflow steps as JSON
- `vibey://workflows/{id}/quality-gates` - Quality gates as JSON
- `vibey://handoffs/{id}` - Full handoff template
- `vibey://handoffs/{id}/variables` - Variable schema

## Usage Examples
### List All Resources
```json
{"method": "resources/list"}
```

### Read a Workflow
```json
{"method": "resources/read", "params": {"uri": "vibey://workflows/sprint-planning"}}
```

### Get Handoff Variable Schema
```json
{"method": "resources/read", "params": {"uri": "vibey://handoffs/code-review/variables"}}
```
```

**4.2 MCP Prompts User Guide**
```markdown
# MCP Prompts User Guide

## Available Prompts
| Prompt | Description | Required Args |
|--------|-------------|---------------|
| vibey_quality_gate_check | Run quality gate | gate_type |
| vibey_security_scan | Security scan | target |
| vibey_test_coverage | Coverage analysis | target |
| vibey_doc_check | Documentation check | target |

## Usage Examples
### Run Security Audit
```json
{
  "method": "prompts/get",
  "params": {
    "name": "vibey_quality_gate_check",
    "arguments": {"gate_type": "security", "threshold": "90"}
  }
}
```
```

**4.3 Update Existing Documentation**
- Update `docs/guides/MCP_INTEGRATION.md` with new capabilities
- Add resource and prompt examples
- Update API reference with new methods

## Files to Create

| File | Purpose |
|------|---------|
| `tests/mcp/conftest.py` | Test fixtures |
| `tests/mcp/resources/test_manager.py` | ResourceManager tests |
| `tests/mcp/resources/test_workflows.py` | Workflow resource tests |
| `tests/mcp/resources/test_handoffs.py` | Handoff resource tests |
| `tests/mcp/prompts/test_manager.py` | PromptManager tests |
| `tests/mcp/prompts/test_quality_gates.py` | Quality gate prompt tests |
| `tests/mcp/discovery/test_handoffs.py` | Handoff discovery tests |
| `tests/mcp/test_server_integration.py` | Server integration tests |
| `docs/guides/MCP_RESOURCES.md` | Resources user guide |
| `docs/guides/MCP_PROMPTS.md` | Prompts user guide |

## Files to Modify

| File | Changes |
|------|---------|
| `docs/guides/MCP_INTEGRATION.md` | Add new capabilities |
| `docs/reference/API.md` | Add resource/prompt methods |

## Success Criteria

1. [ ] All unit tests passing (90%+ coverage)
2. [ ] Integration tests passing
3. [ ] MCP Resources guide created
4. [ ] MCP Prompts guide created
5. [ ] Existing documentation updated
6. [ ] No regressions in existing tests
7. [ ] Manual end-to-end testing successful

## Testing Commands

```bash
# Run all MCP tests
pytest tests/mcp/ -v

# Run with coverage
pytest tests/mcp/ --cov=vibey.mcp --cov-report=html

# Run specific test categories
pytest tests/mcp/resources/ -v
pytest tests/mcp/prompts/ -v
pytest tests/mcp/discovery/ -v

# Integration tests only
pytest tests/mcp/test_server_integration.py -v
```

## Deliverables

1. Comprehensive test suite (50+ tests)
2. Test fixtures for MCP components
3. MCP Resources user guide
4. MCP Prompts user guide
5. Updated integration documentation
6. Coverage report showing 90%+ coverage
