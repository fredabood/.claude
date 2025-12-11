# Task 002: Implement MCP Resources for Workflows

**Task ID:** 01KC79XW008MN6KHT4S4AVS7VH
**Sprint:** MCP Resources, Prompts & Handoff Discovery
**Complexity:** High
**Type:** Development

## Problem Statement

Workflows are one of Vibey's core content types. They define structured processes with steps, agents, and quality gates. Currently, workflows are only accessible via tool invocation. This task implements MCP Resources for workflows, enabling:
- Direct workflow content access via URI
- Workflow step enumeration
- Quality gate extraction
- Workflow metadata queries

## Current State

### Workflow Location
```
vibey/content/workflows/
├── planning/
│   ├── sprint-planning.md
│   └── codebase-audit-discovery.md
├── development/
│   ├── single-feature-development.md
│   └── multi-feature-development.md
├── infrastructure/
│   └── infrastructure-setup.md
└── ... (16+ workflow files)
```

### Existing Workflow Discovery
```python
# vibey/mcp/discovery/workflows.py
@dataclass
class WorkflowDefinition:
    id: str
    name: str
    type: str
    description: str
    steps: List[WorkflowStep]
    quality_gates: List[QualityGate]
    complexity: str
    duration: Optional[str]
    filepath: Optional[Path]

class WorkflowDiscovery:
    def discover(self) -> List[WorkflowDefinition]:
        """Scan workflows directory and parse frontmatter."""
        pass
```

## Implementation Plan

### Phase 1: WorkflowResourceProvider Implementation

**1.1 Create Provider Class**
```python
# vibey/mcp/resources/workflows.py
from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml

from .provider import ResourceProvider, Resource, ResourceContent, ResourceTemplate
from ..discovery.workflows import WorkflowDiscovery, WorkflowDefinition

class WorkflowResourceProvider(ResourceProvider):
    """Provides MCP Resources for workflow content."""

    def __init__(self, content_root: Path):
        self.content_root = content_root
        self.workflows_dir = content_root / "vibey" / "content" / "workflows"
        self.discovery = WorkflowDiscovery(content_root)
        self._cache: Optional[List[WorkflowDefinition]] = None

    def get_templates(self) -> List[ResourceTemplate]:
        """Return workflow resource templates."""
        return [
            ResourceTemplate(
                uriTemplate="vibey://workflows/{workflow_id}",
                name="Workflow Definition",
                description="Full workflow definition with steps and gates",
                mimeType="text/markdown"
            ),
            ResourceTemplate(
                uriTemplate="vibey://workflows/{workflow_id}/steps",
                name="Workflow Steps",
                description="Workflow steps as structured JSON",
                mimeType="application/json"
            ),
            ResourceTemplate(
                uriTemplate="vibey://workflows/{workflow_id}/metadata",
                name="Workflow Metadata",
                description="Workflow frontmatter metadata",
                mimeType="application/json"
            ),
            ResourceTemplate(
                uriTemplate="vibey://workflows/{workflow_id}/quality-gates",
                name="Workflow Quality Gates",
                description="Quality gates defined in this workflow",
                mimeType="application/json"
            ),
        ]

    def list_resources(self, uri_template: str) -> List[Resource]:
        """List all workflows as resources."""
        workflows = self._get_workflows()
        resources = []

        for wf in workflows:
            if "metadata" in uri_template:
                resources.append(Resource(
                    uri=f"vibey://workflows/{wf.id}/metadata",
                    name=f"{wf.name} - Metadata",
                    description=f"Metadata for {wf.name}",
                    mimeType="application/json",
                    metadata={"type": wf.type, "complexity": wf.complexity}
                ))
            elif "steps" in uri_template:
                resources.append(Resource(
                    uri=f"vibey://workflows/{wf.id}/steps",
                    name=f"{wf.name} - Steps",
                    description=f"{len(wf.steps)} steps",
                    mimeType="application/json",
                    metadata={"step_count": len(wf.steps)}
                ))
            elif "quality-gates" in uri_template:
                resources.append(Resource(
                    uri=f"vibey://workflows/{wf.id}/quality-gates",
                    name=f"{wf.name} - Quality Gates",
                    description=f"{len(wf.quality_gates)} quality gates",
                    mimeType="application/json",
                    metadata={"gate_count": len(wf.quality_gates)}
                ))
            else:
                resources.append(Resource(
                    uri=f"vibey://workflows/{wf.id}",
                    name=wf.name,
                    description=wf.description,
                    mimeType="text/markdown",
                    metadata={
                        "type": wf.type,
                        "complexity": wf.complexity,
                        "duration": wf.duration,
                        "steps": len(wf.steps),
                        "gates": len(wf.quality_gates)
                    }
                ))

        return resources

    async def read_resource(self, uri: str) -> ResourceContent:
        """Read workflow resource content."""
        # Parse URI: vibey://workflows/{id}[/subresource]
        parts = uri.replace("vibey://workflows/", "").split("/")
        workflow_id = parts[0]
        subresource = parts[1] if len(parts) > 1 else None

        workflow = self._find_workflow(workflow_id)
        if not workflow:
            raise ResourceNotFoundError(f"Workflow not found: {workflow_id}")

        if subresource == "steps":
            return await self._read_steps(workflow, uri)
        elif subresource == "metadata":
            return await self._read_metadata(workflow, uri)
        elif subresource == "quality-gates":
            return await self._read_quality_gates(workflow, uri)
        else:
            return await self._read_full_workflow(workflow, uri)

    async def _read_full_workflow(self, wf: WorkflowDefinition, uri: str) -> ResourceContent:
        """Read full workflow markdown content."""
        if wf.filepath and wf.filepath.exists():
            content = wf.filepath.read_text()
        else:
            content = self._generate_workflow_markdown(wf)

        return ResourceContent(
            uri=uri,
            mimeType="text/markdown",
            text=content
        )

    async def _read_steps(self, wf: WorkflowDefinition, uri: str) -> ResourceContent:
        """Read workflow steps as JSON."""
        import json
        steps_data = [
            {
                "order": step.order,
                "name": step.name,
                "description": step.description,
                "agent": step.agent,
                "duration": step.duration,
                "inputs": step.inputs,
                "outputs": step.outputs
            }
            for step in wf.steps
        ]

        return ResourceContent(
            uri=uri,
            mimeType="application/json",
            text=json.dumps({"workflow_id": wf.id, "steps": steps_data}, indent=2)
        )

    async def _read_metadata(self, wf: WorkflowDefinition, uri: str) -> ResourceContent:
        """Read workflow metadata as JSON."""
        import json
        metadata = {
            "id": wf.id,
            "name": wf.name,
            "type": wf.type,
            "description": wf.description,
            "complexity": wf.complexity,
            "duration": wf.duration,
            "step_count": len(wf.steps),
            "quality_gate_count": len(wf.quality_gates)
        }

        return ResourceContent(
            uri=uri,
            mimeType="application/json",
            text=json.dumps(metadata, indent=2)
        )

    async def _read_quality_gates(self, wf: WorkflowDefinition, uri: str) -> ResourceContent:
        """Read workflow quality gates as JSON."""
        import json
        gates_data = [
            {
                "name": gate.name,
                "type": gate.type,
                "threshold": gate.threshold,
                "blocking": gate.blocking,
                "description": gate.description
            }
            for gate in wf.quality_gates
        ]

        return ResourceContent(
            uri=uri,
            mimeType="application/json",
            text=json.dumps({"workflow_id": wf.id, "quality_gates": gates_data}, indent=2)
        )

    def supports_uri(self, uri: str) -> bool:
        """Check if this provider handles workflow URIs."""
        return uri.startswith("vibey://workflows/")

    def _get_workflows(self) -> List[WorkflowDefinition]:
        """Get all workflows (cached)."""
        if self._cache is None:
            self._cache = self.discovery.discover()
        return self._cache

    def _find_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Find workflow by ID."""
        for wf in self._get_workflows():
            if wf.id == workflow_id:
                return wf
        return None

    def _generate_workflow_markdown(self, wf: WorkflowDefinition) -> str:
        """Generate markdown from workflow definition."""
        lines = [
            f"# {wf.name}",
            "",
            f"**Type:** {wf.type}",
            f"**Complexity:** {wf.complexity}",
        ]
        if wf.duration:
            lines.append(f"**Duration:** {wf.duration}")

        if wf.description:
            lines.extend(["", wf.description, ""])

        if wf.steps:
            lines.extend(["", "## Steps", ""])
            for step in wf.steps:
                lines.append(f"{step.order}. **{step.name}**")
                if step.agent:
                    lines.append(f"   - Agent: {step.agent}")
                if step.duration:
                    lines.append(f"   - Duration: {step.duration}")

        if wf.quality_gates:
            lines.extend(["", "## Quality Gates", ""])
            for gate in wf.quality_gates:
                blocking = " [BLOCKING]" if gate.blocking else ""
                lines.append(f"- **{gate.name}** ({gate.type}){blocking}")

        return "\n".join(lines)

    def invalidate_cache(self):
        """Invalidate workflow cache."""
        self._cache = None
```

### Phase 2: Integration with ResourceManager

**2.1 Register WorkflowResourceProvider**
```python
# In vibey/mcp/resources/manager.py
from .workflows import WorkflowResourceProvider

class ResourceManager:
    def _register_providers(self):
        self.providers['workflows'] = WorkflowResourceProvider(self.content_root)
        # ... other providers
```

### Phase 3: Add Workflow-Specific Features

**3.1 Workflow List Resource**
```python
# Additional resource for listing all workflows
ResourceTemplate(
    uriTemplate="vibey://workflows",
    name="All Workflows",
    description="List of all available workflows",
    mimeType="application/json"
)
```

**3.2 Workflow Search by Type**
```python
ResourceTemplate(
    uriTemplate="vibey://workflows?type={workflow_type}",
    name="Workflows by Type",
    description="Filter workflows by type (planning, development, etc.)",
    mimeType="application/json"
)
```

## Files to Create

| File | Purpose |
|------|---------|
| `vibey/mcp/resources/workflows.py` | WorkflowResourceProvider implementation |

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/mcp/resources/manager.py` | Register WorkflowResourceProvider |
| `vibey/mcp/resources/__init__.py` | Export WorkflowResourceProvider |

## Testing Strategy

### Unit Tests
```python
# tests/mcp/resources/test_workflows.py
import pytest
from vibey.mcp.resources.workflows import WorkflowResourceProvider

class TestWorkflowResourceProvider:
    def test_get_templates(self, provider):
        templates = provider.get_templates()
        assert len(templates) >= 4
        assert any("workflow_id" in t.uriTemplate for t in templates)

    def test_list_resources(self, provider):
        resources = provider.list_resources("vibey://workflows/{workflow_id}")
        assert len(resources) > 0
        assert all(r.uri.startswith("vibey://workflows/") for r in resources)

    @pytest.mark.asyncio
    async def test_read_workflow_content(self, provider):
        resources = provider.list_resources("vibey://workflows/{workflow_id}")
        if resources:
            content = await provider.read_resource(resources[0].uri)
            assert content.mimeType == "text/markdown"
            assert content.text is not None

    @pytest.mark.asyncio
    async def test_read_workflow_steps(self, provider):
        resources = provider.list_resources("vibey://workflows/{workflow_id}/steps")
        if resources:
            content = await provider.read_resource(resources[0].uri)
            assert content.mimeType == "application/json"
            data = json.loads(content.text)
            assert "steps" in data
```

## Success Criteria

1. [ ] WorkflowResourceProvider class implemented
2. [ ] All 4 resource templates supported (full, steps, metadata, gates)
3. [ ] Workflow content readable as markdown
4. [ ] Steps and gates extractable as JSON
5. [ ] Provider integrated with ResourceManager
6. [ ] Unit tests passing with >90% coverage
7. [ ] Manual testing with MCP client successful

## Dependencies

- Task 001 (Resource architecture) must be complete
- Existing WorkflowDiscovery module

## Deliverables

1. WorkflowResourceProvider implementation
2. Resource template definitions
3. Unit test suite
4. Integration with ResourceManager
