# Task 006: Implement Handoff Discovery and Tool Generation

**Task ID:** 01KC79XW0348EJZBAJ6YPW09FK
**Sprint:** MCP Resources, Prompts & Handoff Discovery
**Complexity:** High
**Type:** Development

## Problem Statement

Handoff templates define structured information exchange between agents. Each template has:
- YAML frontmatter with variable definitions
- Agent routing (from/to agents)
- Jinja2 template body

This task extends the existing tool discovery system to:
1. Discover all handoff templates
2. Parse their variable schemas
3. Generate MCP tools dynamically for each handoff
4. Enable agent-aware handoff routing

## Current State

### Existing Discovery System
```python
# vibey/mcp/discovery/__init__.py
from .parser import FrontmatterParser
from .agents import AgentDiscovery, AgentDefinition
from .workflows import WorkflowDiscovery, WorkflowDefinition
from .generator import ToolGenerator
from .discovery import ToolDiscovery
```

The ToolDiscovery system already:
- Scans agents/ directory for agent definitions
- Scans workflows/ directory for workflow definitions
- Parses YAML frontmatter
- Generates MCP tools dynamically
- Caches results for performance

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
---
# Diagram Handoff: {{ handoff_title }}
...
```

## Implementation Plan

### Phase 1: HandoffDiscovery Module

**1.1 Create HandoffDiscovery Class**
```python
# vibey/mcp/discovery/handoffs.py
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml
import logging

logger = logging.getLogger(__name__)

@dataclass
class HandoffVariable:
    """Variable in handoff template."""
    name: str
    type: str = "string"
    required: bool = False
    description: Optional[str] = None
    default: Optional[Any] = None

@dataclass
class HandoffDefinition:
    """Handoff template definition."""
    id: str
    name: str
    version: str
    from_agent: str
    to_agents: List[str]
    purpose: str
    description: Optional[str] = None
    variables: List[HandoffVariable] = field(default_factory=list)
    filepath: Optional[Path] = None

class HandoffDiscovery:
    """
    Discovers handoff templates from markdown files.

    Scans the templates/handoffs directory, parses YAML frontmatter,
    and builds HandoffDefinition objects.

    Example:
        >>> discovery = HandoffDiscovery(Path("/path/to/vibey"))
        >>> handoffs = discovery.discover()
        >>> print(f"Found {len(handoffs)} handoffs")
    """

    def __init__(self, root_dir: Path):
        """
        Initialize handoff discovery.

        Args:
            root_dir: Root directory of Vibey repository
        """
        self.root_dir = Path(root_dir)
        self.handoffs_dir = self.root_dir / "vibey" / "content" / "templates" / "handoffs"
        self._cache: Optional[List[HandoffDefinition]] = None

    def discover(self, force_refresh: bool = False) -> List[HandoffDefinition]:
        """
        Discover all handoff templates.

        Args:
            force_refresh: Force re-scan of templates

        Returns:
            List of HandoffDefinition objects
        """
        if self._cache is not None and not force_refresh:
            return self._cache

        handoffs = []

        if not self.handoffs_dir.exists():
            logger.warning(f"Handoffs directory not found: {self.handoffs_dir}")
            return handoffs

        for filepath in self.handoffs_dir.glob("*.md"):
            try:
                handoff = self._parse_handoff_file(filepath)
                if handoff:
                    handoffs.append(handoff)
                    logger.debug(f"Discovered handoff: {handoff.id}")
            except Exception as e:
                logger.error(f"Error parsing handoff {filepath}: {e}")

        self._cache = handoffs
        logger.info(f"Discovered {len(handoffs)} handoffs")
        return handoffs

    def _parse_handoff_file(self, filepath: Path) -> Optional[HandoffDefinition]:
        """Parse a single handoff template file."""
        content = filepath.read_text()

        # Extract frontmatter
        if not content.startswith('---'):
            return None

        parts = content.split('---', 2)
        if len(parts) < 3:
            return None

        try:
            frontmatter = yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {filepath}: {e}")
            return None

        if not frontmatter:
            return None

        # Parse variables
        variables = []
        for var_def in frontmatter.get('variables', []):
            variables.append(HandoffVariable(
                name=var_def.get('name'),
                type=var_def.get('type', 'string'),
                required=var_def.get('required', False),
                description=var_def.get('description'),
                default=var_def.get('default')
            ))

        return HandoffDefinition(
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

    def get_handoff_by_id(self, handoff_id: str) -> Optional[HandoffDefinition]:
        """Get a specific handoff by ID."""
        for handoff in self.discover():
            if handoff.id == handoff_id:
                return handoff
        return None

    def get_handoffs_from_agent(self, agent_id: str) -> List[HandoffDefinition]:
        """Get all handoffs originating from an agent."""
        return [h for h in self.discover() if h.from_agent == agent_id]

    def get_handoffs_to_agent(self, agent_id: str) -> List[HandoffDefinition]:
        """Get all handoffs targeting an agent."""
        return [h for h in self.discover() if agent_id in h.to_agents]

    def invalidate_cache(self):
        """Invalidate the discovery cache."""
        self._cache = None
```

### Phase 2: Handoff Tool Generation

**2.1 Update ToolGenerator**
```python
# In vibey/mcp/discovery/generator.py

class ToolGenerator:
    """Generates MCP tool definitions from discovered assets."""

    def generate_handoff_tools(
        self,
        handoffs: List[HandoffDefinition]
    ) -> List[Dict[str, Any]]:
        """
        Generate MCP tools from handoff definitions.

        Each handoff becomes two tools:
        1. vibey_handoff_{id} - Execute the handoff
        2. vibey_handoff_{id}_schema - Get variable schema

        Args:
            handoffs: List of handoff definitions

        Returns:
            List of MCP tool definitions
        """
        tools = []

        for handoff in handoffs:
            # Main handoff tool
            tool_name = f"{self.tool_prefix}_handoff_{handoff.id.replace('-', '_')}"

            # Build input schema from variables
            properties = {}
            required = []
            for var in handoff.variables:
                properties[var.name] = {
                    "type": var.type if var.type in ["string", "number", "boolean", "array"] else "string",
                    "description": var.description or f"Variable: {var.name}"
                }
                if var.default is not None:
                    properties[var.name]["default"] = var.default
                if var.required:
                    required.append(var.name)

            tool_def = {
                "name": tool_name,
                "description": f"{handoff.name}: {handoff.purpose}",
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                },
                "_metadata": {
                    "asset_type": "handoff",
                    "asset_id": handoff.id,
                    "from_agent": handoff.from_agent,
                    "to_agents": handoff.to_agents,
                    "version": handoff.version
                }
            }
            tools.append(tool_def)

        return tools

    def generate_all_tools(
        self,
        agents: List[AgentDefinition],
        workflows: List[WorkflowDefinition],
        handoffs: List[HandoffDefinition] = None
    ) -> List[Dict[str, Any]]:
        """Generate all tools from all asset types."""
        tools = []
        tools.extend(self.generate_agent_tools(agents))
        tools.extend(self.generate_workflow_tools(workflows))
        if handoffs:
            tools.extend(self.generate_handoff_tools(handoffs))
        return tools
```

### Phase 3: Integrate with ToolDiscovery

**3.1 Update ToolDiscovery Class**
```python
# In vibey/mcp/discovery/discovery.py

from .handoffs import HandoffDiscovery, HandoffDefinition

class ToolDiscovery:
    """Main tool discovery orchestrator with caching."""

    def __init__(self, root_dir: Path, cache_ttl: int = 60, tool_prefix: str = "vibey"):
        self.root_dir = Path(root_dir)
        self.cache_ttl = cache_ttl

        # Initialize sub-modules
        self.agent_discovery = AgentDiscovery(root_dir)
        self.workflow_discovery = WorkflowDiscovery(root_dir)
        self.handoff_discovery = HandoffDiscovery(root_dir)  # NEW
        self.generator = ToolGenerator(tool_prefix)

        # Cache storage
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_time: float = 0
        self._cache_hash: str = ""

    def get_handoff_tools(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get only handoff tools."""
        tools = self.get_all_tools(force_refresh)
        return [t for t in tools if t.get('_metadata', {}).get('asset_type') == 'handoff']

    def get_handoffs(self) -> List[HandoffDefinition]:
        """Get all discovered handoff definitions."""
        return self.handoff_discovery.discover()

    def _refresh_cache(self) -> List[Dict[str, Any]]:
        """Refresh the tool cache."""
        logger.info("Refreshing tool cache...")

        # Discover assets
        agents = self.agent_discovery.discover()
        workflows = self.workflow_discovery.discover()
        handoffs = self.handoff_discovery.discover()  # NEW

        # Generate tools
        tools = self.generator.generate_all_tools(agents, workflows, handoffs)

        # Update cache
        self._cache = {
            'tools': tools,
            'agents': agents,
            'workflows': workflows,
            'handoffs': handoffs,  # NEW
        }
        self._cache_time = time.time()
        self._cache_hash = self._compute_source_hash()

        logger.info(f"Cache refreshed: {len(tools)} tools")
        return tools

    def _compute_source_hash(self) -> str:
        """Compute hash of source files for cache invalidation."""
        hash_input = []

        # Agent files
        if self.agent_discovery.agents_dir.exists():
            for f in self.agent_discovery.agents_dir.rglob('*.md'):
                hash_input.append(f"{f}:{os.path.getmtime(f)}")

        # Workflow files
        if self.workflow_discovery.workflows_dir.exists():
            for f in self.workflow_discovery.workflows_dir.rglob('*.md'):
                hash_input.append(f"{f}:{os.path.getmtime(f)}")

        # Handoff files - NEW
        if self.handoff_discovery.handoffs_dir.exists():
            for f in self.handoff_discovery.handoffs_dir.glob('*.md'):
                hash_input.append(f"{f}:{os.path.getmtime(f)}")

        return hashlib.md5('\n'.join(sorted(hash_input)).encode()).hexdigest()
```

### Phase 4: Server Handoff Tool Execution

**4.1 Update Server Handler**
```python
# In vibey/mcp/server.py

async def _handle_dynamic_tool(
    self,
    tool_name: str,
    arguments: Dict[str, Any],
    tool_def: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle invocation of a dynamically discovered tool."""
    metadata = tool_def.get('_metadata', {})
    asset_type = metadata.get('asset_type')
    asset_id = metadata.get('asset_id')

    if asset_type == 'agent':
        return await self._execute_agent_tool(asset_id, arguments, metadata)
    elif asset_type == 'workflow':
        return await self._execute_workflow_tool(asset_id, arguments, metadata)
    elif asset_type == 'handoff':  # NEW
        return await self._execute_handoff_tool(asset_id, arguments, metadata)
    else:
        return {"content": [{"type": "text", "text": f"❌ Unknown asset type: {asset_type}"}], "isError": True}

async def _execute_handoff_tool(
    self,
    handoff_id: str,
    arguments: Dict[str, Any],
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute a handoff tool.

    Renders the handoff template with provided arguments
    and returns the formatted handoff document.
    """
    from jinja2 import Environment, BaseLoader

    handoff = self.tool_discovery.handoff_discovery.get_handoff_by_id(handoff_id)
    if not handoff:
        return {
            "content": [{"type": "text", "text": f"❌ Handoff not found: {handoff_id}"}],
            "isError": True
        }

    # Read template content
    if not handoff.filepath or not handoff.filepath.exists():
        return {
            "content": [{"type": "text", "text": f"❌ Handoff template file not found"}],
            "isError": True
        }

    raw_content = handoff.filepath.read_text()

    # Remove frontmatter
    if raw_content.startswith('---'):
        parts = raw_content.split('---', 2)
        template_content = parts[2].strip() if len(parts) >= 3 else raw_content
    else:
        template_content = raw_content

    # Build template context
    context = {
        "config": {"roles": {}},
        "handoff_title": handoff.name,
        "handoff_date": datetime.now().strftime("%Y-%m-%d"),
        **arguments
    }

    # Render template
    try:
        env = Environment(loader=BaseLoader())
        template = env.from_string(template_content)
        rendered = template.render(**context)
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"❌ Template rendering error: {str(e)}"}],
            "isError": True
        }

    # Build response
    response_parts = [
        f"# Handoff: {handoff.name}",
        "",
        f"**From:** {handoff.from_agent}",
        f"**To:** {', '.join(handoff.to_agents)}",
        f"**Version:** {handoff.version}",
        "",
        "---",
        "",
        rendered
    ]

    return {
        "content": [{"type": "text", "text": "\n".join(response_parts)}],
        "isError": False
    }
```

## Files to Create

| File | Purpose |
|------|---------|
| `vibey/mcp/discovery/handoffs.py` | HandoffDiscovery class |

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/mcp/discovery/__init__.py` | Export HandoffDiscovery, HandoffDefinition |
| `vibey/mcp/discovery/generator.py` | Add generate_handoff_tools method |
| `vibey/mcp/discovery/discovery.py` | Integrate HandoffDiscovery |
| `vibey/mcp/server.py` | Add _execute_handoff_tool method |

## Testing Strategy

### Unit Tests
```python
# tests/mcp/discovery/test_handoffs.py
class TestHandoffDiscovery:
    def test_discover_handoffs(self, discovery):
        handoffs = discovery.discover()
        assert len(handoffs) > 0

    def test_parse_handoff_variables(self, discovery):
        handoffs = discovery.discover()
        # Find handoff with known variables
        diagram = next((h for h in handoffs if h.id == "diagram-handoff"), None)
        assert diagram is not None
        assert len(diagram.variables) > 0
        assert any(v.name == "diagram_count" for v in diagram.variables)

    def test_get_handoffs_from_agent(self, discovery):
        handoffs = discovery.get_handoffs_from_agent("diagram-engineer")
        assert all(h.from_agent == "diagram-engineer" for h in handoffs)

    def test_get_handoffs_to_agent(self, discovery):
        handoffs = discovery.get_handoffs_to_agent("documentation-engineer")
        assert all("documentation-engineer" in h.to_agents for h in handoffs)

class TestHandoffToolGeneration:
    def test_generate_handoff_tools(self, generator, handoffs):
        tools = generator.generate_handoff_tools(handoffs)
        assert len(tools) == len(handoffs)
        assert all("_metadata" in t for t in tools)
        assert all(t["_metadata"]["asset_type"] == "handoff" for t in tools)

    def test_tool_input_schema(self, generator, handoffs):
        tools = generator.generate_handoff_tools(handoffs)
        for tool in tools:
            schema = tool["inputSchema"]
            assert schema["type"] == "object"
            assert "properties" in schema
```

## Success Criteria

1. [ ] HandoffDiscovery class discovers all 23+ handoff templates
2. [ ] Variables parsed correctly from frontmatter
3. [ ] Tool generator creates tools with proper input schemas
4. [ ] Agent routing metadata captured (from/to agents)
5. [ ] Server executes handoff tools with template rendering
6. [ ] Cache invalidation includes handoff files
7. [ ] Unit tests passing

## Dependencies

- Existing ToolDiscovery infrastructure
- Jinja2 for template rendering
- Task 003 (Handoff resources) for data models

## Deliverables

1. HandoffDiscovery class
2. Updated ToolGenerator with handoff support
3. Server handoff tool execution
4. Unit test suite
5. Integration with existing discovery system
