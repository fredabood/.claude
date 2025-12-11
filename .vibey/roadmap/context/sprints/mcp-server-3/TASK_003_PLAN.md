# Task 003: Implement MCP Resources for Handoffs

**Task ID:** 01KC79XW01GARBZYRXEFX766K6
**Sprint:** MCP Resources, Prompts & Handoff Discovery
**Complexity:** High
**Type:** Development

## Problem Statement

Handoff templates are Jinja2-based markdown templates that define structured information exchange between agents. They include:
- YAML frontmatter with metadata (variables, from/to agents, purpose)
- Markdown body with Jinja2 placeholders
- Variable definitions with types and requirements

Currently, handoff templates are only accessible by reading files directly. MCP Resources will enable:
- Listing available handoff templates
- Accessing template metadata (variables, agents)
- Reading template content
- Variable schema extraction for tool generation

## Current State

### Handoff Template Location
```
vibey/content/templates/handoffs/
├── diagram-handoff-template.md
├── code-review-handoff.md
├── deployment-handoff.md
├── testing-handoff.md
└── ... (23+ handoff templates)
```

### Handoff Template Structure
```yaml
---
id: diagram-handoff
name: Diagram Handoff
version: 1.0.0
from_agent: diagram-engineer
to_agents:
  - documentation-engineer
purpose: Template for diagram handoff
variables:
  - name: diagram_count
    type: string
    required: true
    description: Diagram Count value
  - name: diagram_tool
    type: string
    required: true
    description: Diagram Tool value
---
# Diagram Handoff: {{ handoff_title }}
... Jinja2 markdown content ...
```

## Implementation Plan

### Phase 1: HandoffResourceProvider Implementation

**1.1 Create Handoff Data Model**
```python
# vibey/mcp/resources/handoffs.py
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml
import re

@dataclass
class HandoffVariable:
    """Variable definition from handoff template."""
    name: str
    type: str
    required: bool
    description: Optional[str] = None
    default: Optional[Any] = None

@dataclass
class HandoffDefinition:
    """Parsed handoff template definition."""
    id: str
    name: str
    version: str
    from_agent: str
    to_agents: List[str]
    purpose: str
    description: Optional[str]
    variables: List[HandoffVariable]
    filepath: Optional[Path] = None

    @classmethod
    def from_frontmatter(cls, frontmatter: Dict, filepath: Path) -> "HandoffDefinition":
        """Parse handoff from YAML frontmatter."""
        variables = [
            HandoffVariable(
                name=v.get('name'),
                type=v.get('type', 'string'),
                required=v.get('required', False),
                description=v.get('description'),
                default=v.get('default')
            )
            for v in frontmatter.get('variables', [])
        ]

        return cls(
            id=frontmatter.get('id', filepath.stem),
            name=frontmatter.get('name', filepath.stem),
            version=frontmatter.get('version', '1.0.0'),
            from_agent=frontmatter.get('from_agent', 'unknown'),
            to_agents=frontmatter.get('to_agents', []),
            purpose=frontmatter.get('purpose', ''),
            description=frontmatter.get('description'),
            variables=variables,
            filepath=filepath
        )
```

**1.2 Create HandoffResourceProvider**
```python
class HandoffResourceProvider(ResourceProvider):
    """Provides MCP Resources for handoff templates."""

    def __init__(self, content_root: Path):
        self.content_root = content_root
        self.handoffs_dir = content_root / "vibey" / "content" / "templates" / "handoffs"
        self._cache: Optional[List[HandoffDefinition]] = None

    def get_templates(self) -> List[ResourceTemplate]:
        """Return handoff resource templates."""
        return [
            ResourceTemplate(
                uriTemplate="vibey://handoffs/{handoff_id}",
                name="Handoff Template",
                description="Full handoff template with Jinja2 content",
                mimeType="text/markdown"
            ),
            ResourceTemplate(
                uriTemplate="vibey://handoffs/{handoff_id}/variables",
                name="Handoff Variables",
                description="Variable schema for the handoff template",
                mimeType="application/json"
            ),
            ResourceTemplate(
                uriTemplate="vibey://handoffs/{handoff_id}/metadata",
                name="Handoff Metadata",
                description="Handoff template metadata (agents, purpose)",
                mimeType="application/json"
            ),
            ResourceTemplate(
                uriTemplate="vibey://handoffs/{handoff_id}/rendered",
                name="Rendered Handoff",
                description="Handoff template rendered with sample data",
                mimeType="text/markdown"
            ),
        ]

    def list_resources(self, uri_template: str) -> List[Resource]:
        """List all handoffs as resources."""
        handoffs = self._discover_handoffs()
        resources = []

        for hf in handoffs:
            if "variables" in uri_template:
                resources.append(Resource(
                    uri=f"vibey://handoffs/{hf.id}/variables",
                    name=f"{hf.name} - Variables",
                    description=f"{len(hf.variables)} variables defined",
                    mimeType="application/json",
                    metadata={
                        "variable_count": len(hf.variables),
                        "required_count": sum(1 for v in hf.variables if v.required)
                    }
                ))
            elif "metadata" in uri_template:
                resources.append(Resource(
                    uri=f"vibey://handoffs/{hf.id}/metadata",
                    name=f"{hf.name} - Metadata",
                    description=hf.purpose,
                    mimeType="application/json",
                    metadata={
                        "from_agent": hf.from_agent,
                        "to_agents": hf.to_agents
                    }
                ))
            elif "rendered" in uri_template:
                resources.append(Resource(
                    uri=f"vibey://handoffs/{hf.id}/rendered",
                    name=f"{hf.name} - Rendered",
                    description="Template rendered with sample values",
                    mimeType="text/markdown"
                ))
            else:
                resources.append(Resource(
                    uri=f"vibey://handoffs/{hf.id}",
                    name=hf.name,
                    description=hf.purpose,
                    mimeType="text/markdown",
                    metadata={
                        "version": hf.version,
                        "from_agent": hf.from_agent,
                        "to_agents": hf.to_agents,
                        "variables": len(hf.variables)
                    }
                ))

        return resources

    async def read_resource(self, uri: str) -> ResourceContent:
        """Read handoff resource content."""
        # Parse URI: vibey://handoffs/{id}[/subresource]
        parts = uri.replace("vibey://handoffs/", "").split("/")
        handoff_id = parts[0]
        subresource = parts[1] if len(parts) > 1 else None

        handoff = self._find_handoff(handoff_id)
        if not handoff:
            raise ResourceNotFoundError(f"Handoff not found: {handoff_id}")

        if subresource == "variables":
            return await self._read_variables(handoff, uri)
        elif subresource == "metadata":
            return await self._read_metadata(handoff, uri)
        elif subresource == "rendered":
            return await self._read_rendered(handoff, uri)
        else:
            return await self._read_full_template(handoff, uri)

    async def _read_full_template(self, hf: HandoffDefinition, uri: str) -> ResourceContent:
        """Read full handoff template content."""
        if hf.filepath and hf.filepath.exists():
            content = hf.filepath.read_text()
        else:
            content = f"# {hf.name}\n\nTemplate file not found."

        return ResourceContent(
            uri=uri,
            mimeType="text/markdown",
            text=content
        )

    async def _read_variables(self, hf: HandoffDefinition, uri: str) -> ResourceContent:
        """Read handoff variables as JSON schema."""
        import json

        # Build JSON Schema for variables
        schema = {
            "type": "object",
            "handoff_id": hf.id,
            "handoff_name": hf.name,
            "properties": {},
            "required": []
        }

        for var in hf.variables:
            schema["properties"][var.name] = {
                "type": var.type,
                "description": var.description or f"Variable: {var.name}"
            }
            if var.default is not None:
                schema["properties"][var.name]["default"] = var.default
            if var.required:
                schema["required"].append(var.name)

        return ResourceContent(
            uri=uri,
            mimeType="application/json",
            text=json.dumps(schema, indent=2)
        )

    async def _read_metadata(self, hf: HandoffDefinition, uri: str) -> ResourceContent:
        """Read handoff metadata as JSON."""
        import json

        metadata = {
            "id": hf.id,
            "name": hf.name,
            "version": hf.version,
            "from_agent": hf.from_agent,
            "to_agents": hf.to_agents,
            "purpose": hf.purpose,
            "description": hf.description,
            "variable_count": len(hf.variables),
            "required_variables": [v.name for v in hf.variables if v.required]
        }

        return ResourceContent(
            uri=uri,
            mimeType="application/json",
            text=json.dumps(metadata, indent=2)
        )

    async def _read_rendered(self, hf: HandoffDefinition, uri: str) -> ResourceContent:
        """Render handoff template with sample data."""
        from jinja2 import Template, Environment, BaseLoader

        if not hf.filepath or not hf.filepath.exists():
            return ResourceContent(
                uri=uri,
                mimeType="text/markdown",
                text="# Template Not Found"
            )

        # Read template content (remove frontmatter)
        raw_content = hf.filepath.read_text()
        if raw_content.startswith('---'):
            parts = raw_content.split('---', 2)
            if len(parts) >= 3:
                template_content = parts[2].strip()
            else:
                template_content = raw_content
        else:
            template_content = raw_content

        # Generate sample data for variables
        sample_data = self._generate_sample_data(hf)

        # Render template
        try:
            env = Environment(loader=BaseLoader())
            template = env.from_string(template_content)
            rendered = template.render(**sample_data)
        except Exception as e:
            rendered = f"# Rendering Error\n\nError: {str(e)}\n\n## Raw Template\n\n{template_content}"

        return ResourceContent(
            uri=uri,
            mimeType="text/markdown",
            text=rendered
        )

    def _generate_sample_data(self, hf: HandoffDefinition) -> Dict[str, Any]:
        """Generate sample data for template rendering."""
        sample = {
            "config": {"roles": {}},
            "handoff_title": f"Sample {hf.name}",
            "handoff_date": "2025-01-01",
        }

        for var in hf.variables:
            if var.default is not None:
                sample[var.name] = var.default
            elif var.type == "string":
                sample[var.name] = f"[{var.name}]"
            elif var.type == "number":
                sample[var.name] = 0
            elif var.type == "boolean":
                sample[var.name] = True
            elif var.type == "array":
                sample[var.name] = []
            else:
                sample[var.name] = f"<{var.name}>"

        return sample

    def supports_uri(self, uri: str) -> bool:
        """Check if this provider handles handoff URIs."""
        return uri.startswith("vibey://handoffs/")

    def _discover_handoffs(self) -> List[HandoffDefinition]:
        """Discover all handoff templates."""
        if self._cache is not None:
            return self._cache

        handoffs = []
        if not self.handoffs_dir.exists():
            return handoffs

        for filepath in self.handoffs_dir.glob("*.md"):
            try:
                content = filepath.read_text()
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1])
                        if frontmatter:
                            handoff = HandoffDefinition.from_frontmatter(frontmatter, filepath)
                            handoffs.append(handoff)
            except Exception as e:
                # Log error but continue discovery
                pass

        self._cache = handoffs
        return handoffs

    def _find_handoff(self, handoff_id: str) -> Optional[HandoffDefinition]:
        """Find handoff by ID."""
        for hf in self._discover_handoffs():
            if hf.id == handoff_id:
                return hf
        return None

    def invalidate_cache(self):
        """Invalidate handoff cache."""
        self._cache = None
```

### Phase 2: Agent Flow Resources

**2.1 Handoff by Agent Pair**
```python
# Additional resource templates
ResourceTemplate(
    uriTemplate="vibey://handoffs?from={from_agent}",
    name="Handoffs from Agent",
    description="All handoffs originating from a specific agent",
    mimeType="application/json"
),
ResourceTemplate(
    uriTemplate="vibey://handoffs?to={to_agent}",
    name="Handoffs to Agent",
    description="All handoffs targeting a specific agent",
    mimeType="application/json"
),
```

## Files to Create

| File | Purpose |
|------|---------|
| `vibey/mcp/resources/handoffs.py` | HandoffResourceProvider implementation |

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/mcp/resources/manager.py` | Register HandoffResourceProvider |
| `vibey/mcp/resources/__init__.py` | Export HandoffResourceProvider |

## Testing Strategy

### Unit Tests
```python
# tests/mcp/resources/test_handoffs.py
class TestHandoffResourceProvider:
    def test_discover_handoffs(self, provider):
        handoffs = provider._discover_handoffs()
        assert len(handoffs) > 0

    def test_get_templates(self, provider):
        templates = provider.get_templates()
        assert len(templates) >= 4

    @pytest.mark.asyncio
    async def test_read_variables_schema(self, provider):
        resources = provider.list_resources("vibey://handoffs/{id}/variables")
        if resources:
            content = await provider.read_resource(resources[0].uri)
            schema = json.loads(content.text)
            assert "properties" in schema
            assert "required" in schema

    @pytest.mark.asyncio
    async def test_read_rendered_template(self, provider):
        resources = provider.list_resources("vibey://handoffs/{id}/rendered")
        if resources:
            content = await provider.read_resource(resources[0].uri)
            assert content.mimeType == "text/markdown"
            # Should not have raw Jinja2 syntax
            assert "{{" not in content.text or "Rendering Error" in content.text
```

## Success Criteria

1. [ ] HandoffDefinition dataclass complete with parsing
2. [ ] HandoffResourceProvider implements all 4 resource types
3. [ ] Variable schema exported as JSON Schema format
4. [ ] Template rendering with sample data works
5. [ ] Agent-based filtering supported
6. [ ] Unit tests passing with >90% coverage
7. [ ] All 23+ handoff templates discoverable

## Dependencies

- Task 001 (Resource architecture) must be complete
- Jinja2 library for template rendering

## Deliverables

1. HandoffResourceProvider implementation
2. HandoffDefinition data model
3. Variable schema extraction
4. Template rendering with samples
5. Unit test suite
