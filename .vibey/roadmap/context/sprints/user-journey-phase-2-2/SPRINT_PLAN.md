# Sprint 2.2: MCP Server Reference Guide (Auto-Generated)

**Sprint ID:** `01KC81GRE23T0KSHR4ZCES476W`
**Track:** User Journey Audit & Documentation Coverage
**Status:** Not Started
**Tasks:** 7

## Overview

This sprint implements an auto-generated MCP (Model Context Protocol) reference documentation system. The goal is to introspect the MCP server's tools, resources, and prompts to generate comprehensive, always-current documentation.

## Success Criteria

1. 100% MCP tool coverage in generated documentation
2. All resources and prompts documented
3. Automated drift detection in CI pipeline
4. Single command to regenerate all MCP docs
5. All tools have example request/response pairs

---

## MCP Server Architecture Analysis

### Current Structure

```
vibey/mcp/
├── server.py                    # Main MCP server (VibeyMCPServer class)
├── adapters/
│   └── roadmap_adapter.py       # Roadmap operations adapter
├── tools/                       # Tool definitions
│   ├── task_tools.py            # Task management tools (~8 tools)
│   ├── sprint_tools.py          # Sprint management tools (~4 tools)
│   ├── query_tools.py           # Query/status tools (~5 tools)
│   └── content_tools.py         # Content management tools (~7 tools)
├── resources/                   # MCP resources
│   ├── provider.py              # Base ResourceProvider class
│   ├── workflows.py             # Workflow resources
│   ├── handoffs.py              # Handoff template resources
│   └── manager.py               # ResourceManager aggregator
├── prompts/                     # MCP prompts
│   ├── provider.py              # Base PromptProvider class
│   ├── quality_gates.py         # Quality gate prompts
│   └── manager.py               # PromptManager aggregator
├── discovery/                   # Dynamic tool discovery
│   ├── discovery.py             # ToolDiscovery class
│   ├── parser.py                # YAML frontmatter parser
│   ├── agents.py                # Agent tool generation
│   └── workflows.py             # Workflow tool generation
└── utils/
    ├── errors.py                # MCP error types
    └── validation.py            # Input validation
```

### Tool Definition Pattern

```python
def get_query_tools() -> List[Dict[str, Any]]:
    return [
        {
            "name": "vibey_query_track",
            "title": "Query Track",
            "description": "Get detailed information about a specific track",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "track_id": {
                        "type": "string",
                        "description": "Track ID (e.g., 'mcp-server')"
                    }
                },
                "required": ["track_id"]
            }
        },
        # ... more tools
    ]
```

### Known Tools (~24 static + dynamic)

| Category | Tools | File |
|----------|-------|------|
| Task | `vibey_start_task`, `vibey_complete_task`, `vibey_update_task`, etc. | `task_tools.py` |
| Sprint | `vibey_start_sprint`, `vibey_complete_sprint`, `vibey_refresh_progress`, `vibey_query_sprint` | `sprint_tools.py` |
| Query | `vibey_query_track`, `vibey_list_blockers`, `vibey_list_dependencies`, `vibey_roadmap_status`, `vibey_query_standards` | `query_tools.py` |
| Content | `vibey_content_list`, `vibey_content_show`, `vibey_content_search`, `vibey_content_create`, `vibey_content_update`, `vibey_content_delete`, `vibey_content_validate` | `content_tools.py` |
| Dynamic | Agent tools, workflow tools (from frontmatter) | `discovery/` |

---

## Task Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  [Task 1] Design MCP Introspection Architecture                 │
│      │                                                          │
│      ▼                                                          │
│  [Task 2] Build MCP Introspection Module ◄─────────────────┐    │
│      │                                                     │    │
│      │                            [Task 4] Add Usage       │    │
│      ▼                            Examples to MCP ─────────┘    │
│  [Task 3] Build MCP Reference Markdown Generator                │
│      │                                                          │
│      ▼                                                          │
│  [Task 5] Generate Initial MCP Reference Guide                  │
│      │                                                          │
│      ├──────────────────────────┐                               │
│      ▼                          ▼                               │
│  [Task 6] Implement           [Task 7] Implement                │
│  'vibey docs generate mcp'    MCP Drift Detection               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Task 1: Design MCP Introspection Architecture

**ID:** `01KC81GRE23T0KSHR4ZCES476X`
**Type:** Design
**Priority:** Medium
**Estimated Tokens:** 15,000

### Objective

Design a system that introspects MCP server components to extract structured documentation data.

### MCP Components to Introspect

#### 1. Tools

Tools are the primary MCP interaction mechanism. Extract:

| Field | Source | Example |
|-------|--------|---------|
| `name` | `tool["name"]` | `"vibey_start_task"` |
| `title` | `tool.get("title")` | `"Start Task"` |
| `description` | `tool["description"]` | `"Start working on a task"` |
| `inputSchema` | `tool["inputSchema"]` | JSON Schema object |
| `category` | Computed from prefix/file | `"task"` |
| `examples` | Custom attribute or docstring | Request/response pairs |

#### 2. Resources

Resources provide read-only data access. Extract:

| Field | Source | Example |
|-------|--------|---------|
| `uriTemplate` | `template.uriTemplate` | `"vibey://workflows/{category}/{name}"` |
| `name` | `template.name` | `"Workflow"` |
| `description` | `template.description` | `"Access workflow definitions"` |
| `mimeType` | `template.mimeType` | `"text/markdown"` |
| `provider` | Provider class name | `"WorkflowResourceProvider"` |

#### 3. Prompts

Prompts are parameterized message templates. Extract:

| Field | Source | Example |
|-------|--------|---------|
| `name` | `prompt.name` | `"quality_gate_security"` |
| `description` | `prompt.description` | `"Security audit checklist"` |
| `arguments` | `prompt.arguments` | List of PromptArgument |
| `category` | Provider category | `"quality_gates"` |

### Data Model Design

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class MCPComponentType(Enum):
    TOOL = "tool"
    RESOURCE = "resource"
    PROMPT = "prompt"


@dataclass
class SchemaProperty:
    """JSON Schema property definition."""
    name: str
    type: str
    description: Optional[str] = None
    required: bool = False
    default: Any = None
    enum: Optional[List[str]] = None


@dataclass
class InputSchema:
    """Tool input schema."""
    properties: List[SchemaProperty] = field(default_factory=list)
    required: List[str] = field(default_factory=list)


@dataclass
class ToolExample:
    """Tool usage example with request and response."""
    description: str
    request: Dict[str, Any]
    response: Dict[str, Any]


@dataclass
class ToolInfo:
    """Introspected MCP tool information."""
    name: str
    title: Optional[str]
    description: str
    category: str
    input_schema: InputSchema
    examples: List[ToolExample] = field(default_factory=list)
    source_file: Optional[str] = None
    is_dynamic: bool = False


@dataclass
class ResourceTemplateInfo:
    """Introspected MCP resource template."""
    uri_template: str
    name: str
    description: Optional[str]
    mime_type: str
    provider: str
    examples: List[str] = field(default_factory=list)


@dataclass
class PromptArgumentInfo:
    """Prompt argument definition."""
    name: str
    description: Optional[str]
    required: bool = False


@dataclass
class PromptInfo:
    """Introspected MCP prompt information."""
    name: str
    description: str
    category: str
    arguments: List[PromptArgumentInfo] = field(default_factory=list)
    example_output: Optional[str] = None


@dataclass
class MCPIntrospectionResult:
    """Complete introspection result."""
    server_name: str
    server_version: str
    tools: List[ToolInfo] = field(default_factory=list)
    resources: List[ResourceTemplateInfo] = field(default_factory=list)
    prompts: List[PromptInfo] = field(default_factory=list)
    capabilities: Dict[str, Any] = field(default_factory=dict)
```

### Introspection Strategy

1. **Static Tools:** Call `get_*_tools()` functions from each tool module
2. **Dynamic Tools:** Use `ToolDiscovery.discover_tools()` to get agent/workflow tools
3. **Resources:** Iterate `ResourceManager.providers` and call `get_templates()`
4. **Prompts:** Iterate `PromptManager.providers` and call `get_prompts()`

### Output

**File:** `.vibey/roadmap/context/sprints/user-journey-phase-2-2/MCP_INTROSPECTION_DESIGN.md`

### Acceptance Criteria

- [ ] Complete data model for tools, resources, prompts
- [ ] Introspection strategy documented
- [ ] JSON output schema defined
- [ ] Example extraction strategy specified
- [ ] Dynamic tool handling planned

---

## Task 2: Build MCP Introspection Module

**ID:** `01KC81GRE23T0KSHR4ZCES476Y`
**Type:** Development
**Priority:** Medium
**Estimated Tokens:** 30,000

### Objective

Implement the introspection module that extracts structured data from all MCP components.

### Implementation

**File:** `vibey/operations/docs/mcp_introspector.py`

```python
"""
MCP Server Introspection Module.

Extracts structured documentation data from MCP tools, resources, and prompts.
"""

import importlib
import inspect
import json
import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable


class MCPComponentType(Enum):
    TOOL = "tool"
    RESOURCE = "resource"
    PROMPT = "prompt"


@dataclass
class SchemaProperty:
    """JSON Schema property definition."""
    name: str
    type: str
    description: Optional[str] = None
    required: bool = False
    default: Any = None
    enum: Optional[List[str]] = None


@dataclass
class InputSchema:
    """Tool input schema."""
    properties: List[SchemaProperty] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)

    @classmethod
    def from_json_schema(cls, schema: Dict[str, Any]) -> 'InputSchema':
        """Parse from JSON Schema dict."""
        properties = []
        props = schema.get("properties", {})
        required = schema.get("required", [])

        for name, prop_schema in props.items():
            properties.append(SchemaProperty(
                name=name,
                type=prop_schema.get("type", "string"),
                description=prop_schema.get("description"),
                required=name in required,
                default=prop_schema.get("default"),
                enum=prop_schema.get("enum")
            ))

        return cls(properties=properties, required_fields=required)


@dataclass
class ToolExample:
    """Tool usage example."""
    description: str
    request: Dict[str, Any]
    response: Dict[str, Any]


@dataclass
class ToolInfo:
    """Introspected MCP tool information."""
    name: str
    title: Optional[str]
    description: str
    category: str
    input_schema: InputSchema
    examples: List[ToolExample] = field(default_factory=list)
    source_file: Optional[str] = None
    is_dynamic: bool = False


@dataclass
class ResourceTemplateInfo:
    """Introspected MCP resource template."""
    uri_template: str
    name: str
    description: Optional[str]
    mime_type: str
    provider: str
    examples: List[str] = field(default_factory=list)


@dataclass
class PromptArgumentInfo:
    """Prompt argument definition."""
    name: str
    description: Optional[str]
    required: bool = False


@dataclass
class PromptInfo:
    """Introspected MCP prompt information."""
    name: str
    description: str
    category: str
    arguments: List[PromptArgumentInfo] = field(default_factory=list)
    example_output: Optional[str] = None


@dataclass
class MCPIntrospectionResult:
    """Complete introspection result."""
    server_name: str
    server_version: str
    tools: List[ToolInfo] = field(default_factory=list)
    resources: List[ResourceTemplateInfo] = field(default_factory=list)
    prompts: List[PromptInfo] = field(default_factory=list)
    capabilities: Dict[str, Any] = field(default_factory=dict)


class MCPIntrospector:
    """
    Introspects MCP server to extract documentation data.

    Discovers and analyzes:
    - Static tools from tool modules
    - Dynamic tools from agent/workflow discovery
    - Resources from resource providers
    - Prompts from prompt providers

    Usage:
        >>> introspector = MCPIntrospector()
        >>> result = introspector.introspect()
        >>> introspector.to_json("mcp_structure.json")
    """

    # Tool modules to introspect
    TOOL_MODULES = [
        ("vibey.mcp.tools.task_tools", "get_task_tools", "task"),
        ("vibey.mcp.tools.sprint_tools", "get_sprint_tools", "sprint"),
        ("vibey.mcp.tools.query_tools", "get_query_tools", "query"),
        ("vibey.mcp.tools.content_tools", "get_content_tools", "content"),
    ]

    def __init__(self, framework_root: Optional[Path] = None):
        """
        Initialize MCP introspector.

        Args:
            framework_root: Root path for dynamic tool discovery
        """
        self.framework_root = framework_root or Path.cwd()
        self._result: Optional[MCPIntrospectionResult] = None

    def introspect(self) -> MCPIntrospectionResult:
        """
        Perform full introspection of MCP server.

        Returns:
            MCPIntrospectionResult with all components
        """
        self._result = MCPIntrospectionResult(
            server_name="vibey-roadmap",
            server_version=self._get_server_version(),
            capabilities=self._get_capabilities()
        )

        # Introspect all components
        self._introspect_static_tools()
        self._introspect_dynamic_tools()
        self._introspect_resources()
        self._introspect_prompts()

        return self._result

    def _get_server_version(self) -> str:
        """Get MCP server version."""
        try:
            from vibey.cli.main import __version__
            return __version__
        except ImportError:
            return "unknown"

    def _get_capabilities(self) -> Dict[str, Any]:
        """Get server capabilities."""
        try:
            from vibey.mcp.server import VibeyMCPServer
            server = VibeyMCPServer.__new__(VibeyMCPServer)
            return server.get_capabilities()
        except Exception:
            return {
                "tools": {"listChanged": True},
                "resources": {"subscribe": False},
                "prompts": {"listChanged": False}
            }

    def _introspect_static_tools(self) -> None:
        """Introspect statically defined tools."""
        for module_name, func_name, category in self.TOOL_MODULES:
            try:
                module = importlib.import_module(module_name)
                get_tools_func = getattr(module, func_name)
                tools = get_tools_func()

                for tool_def in tools:
                    tool_info = self._parse_tool_definition(
                        tool_def,
                        category,
                        source_file=module_name.replace(".", "/") + ".py"
                    )
                    self._result.tools.append(tool_info)

            except Exception as e:
                print(f"Warning: Failed to introspect {module_name}: {e}")

    def _introspect_dynamic_tools(self) -> None:
        """Introspect dynamically discovered tools."""
        try:
            from vibey.mcp.discovery import ToolDiscovery

            discovery = ToolDiscovery(
                root_dir=self.framework_root,
                cache_ttl=0,
                tool_prefix="vibey"
            )

            # Get agent tools
            agent_tools = discovery.discover_agent_tools()
            for tool_def in agent_tools:
                tool_info = self._parse_tool_definition(
                    tool_def,
                    category="agent",
                    is_dynamic=True
                )
                self._result.tools.append(tool_info)

            # Get workflow tools
            workflow_tools = discovery.discover_workflow_tools()
            for tool_def in workflow_tools:
                tool_info = self._parse_tool_definition(
                    tool_def,
                    category="workflow",
                    is_dynamic=True
                )
                self._result.tools.append(tool_info)

        except Exception as e:
            print(f"Warning: Failed to introspect dynamic tools: {e}")

    def _parse_tool_definition(
        self,
        tool_def: Dict[str, Any],
        category: str,
        source_file: Optional[str] = None,
        is_dynamic: bool = False
    ) -> ToolInfo:
        """Parse a tool definition dict into ToolInfo."""
        input_schema = InputSchema.from_json_schema(
            tool_def.get("inputSchema", {})
        )

        # Extract examples if present
        examples = []
        if "examples" in tool_def:
            for ex in tool_def["examples"]:
                examples.append(ToolExample(
                    description=ex.get("description", ""),
                    request=ex.get("request", {}),
                    response=ex.get("response", {})
                ))

        return ToolInfo(
            name=tool_def["name"],
            title=tool_def.get("title"),
            description=tool_def.get("description", ""),
            category=category,
            input_schema=input_schema,
            examples=examples,
            source_file=source_file,
            is_dynamic=is_dynamic
        )

    def _introspect_resources(self) -> None:
        """Introspect resource providers."""
        try:
            from vibey.mcp.resources.manager import ResourceManager
            from vibey.mcp.resources.workflows import WorkflowResourceProvider
            from vibey.mcp.resources.handoffs import HandoffResourceProvider

            # Create providers
            providers = [
                WorkflowResourceProvider(self.framework_root / "framework"),
                HandoffResourceProvider(self.framework_root / "framework"),
            ]

            for provider in providers:
                templates = provider.get_templates()
                for template in templates:
                    self._result.resources.append(ResourceTemplateInfo(
                        uri_template=template.uriTemplate,
                        name=template.name,
                        description=getattr(template, 'description', None),
                        mime_type=getattr(template, 'mimeType', 'text/plain'),
                        provider=provider.__class__.__name__
                    ))

        except Exception as e:
            print(f"Warning: Failed to introspect resources: {e}")

    def _introspect_prompts(self) -> None:
        """Introspect prompt providers."""
        try:
            from vibey.mcp.prompts.quality_gates import QualityGatePromptProvider

            providers = [
                QualityGatePromptProvider(self.framework_root / "framework"),
            ]

            for provider in providers:
                prompts = provider.get_prompts()
                for prompt in prompts:
                    arguments = []
                    for arg in getattr(prompt, 'arguments', []):
                        arguments.append(PromptArgumentInfo(
                            name=arg.name,
                            description=getattr(arg, 'description', None),
                            required=getattr(arg, 'required', False)
                        ))

                    self._result.prompts.append(PromptInfo(
                        name=prompt.name,
                        description=getattr(prompt, 'description', ''),
                        category=provider.CATEGORY,
                        arguments=arguments
                    ))

        except Exception as e:
            print(f"Warning: Failed to introspect prompts: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        if not self._result:
            self.introspect()

        def convert(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return {k: convert(v) for k, v in asdict(obj).items()}
            elif isinstance(obj, list):
                return [convert(item) for item in obj]
            elif isinstance(obj, Enum):
                return obj.value
            return obj

        return convert(self._result)

    def to_json(self, path: str, indent: int = 2) -> None:
        """Write introspection data to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=indent, default=str)

    def get_tool_count(self) -> Dict[str, int]:
        """Get tool count by category."""
        if not self._result:
            self.introspect()

        counts = {}
        for tool in self._result.tools:
            counts[tool.category] = counts.get(tool.category, 0) + 1
        return counts


def introspect_mcp() -> MCPIntrospectionResult:
    """
    Convenience function to introspect the Vibey MCP server.

    Returns:
        MCPIntrospectionResult with all components
    """
    introspector = MCPIntrospector()
    return introspector.introspect()
```

### Test Cases

```python
# tests/operations/docs/test_mcp_introspector.py

import pytest
from vibey.operations.docs.mcp_introspector import (
    MCPIntrospector,
    introspect_mcp,
    InputSchema,
    ToolInfo,
)


def test_introspect_static_tools():
    """Test introspecting static tool modules."""
    introspector = MCPIntrospector()
    result = introspector.introspect()

    # Should have tools from all categories
    categories = {t.category for t in result.tools}
    assert "task" in categories
    assert "sprint" in categories
    assert "query" in categories
    assert "content" in categories


def test_tool_schema_parsing():
    """Test JSON Schema parsing."""
    schema = {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "Task identifier"
            },
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed"]
            }
        },
        "required": ["task_id"]
    }

    parsed = InputSchema.from_json_schema(schema)
    assert len(parsed.properties) == 2
    assert parsed.properties[0].name == "task_id"
    assert parsed.properties[0].required is True
    assert parsed.properties[1].enum == ["pending", "in_progress", "completed"]


def test_tool_count_by_category():
    """Test tool counting."""
    introspector = MCPIntrospector()
    introspector.introspect()
    counts = introspector.get_tool_count()

    assert counts.get("task", 0) >= 3
    assert counts.get("sprint", 0) >= 3
    assert counts.get("query", 0) >= 4


def test_to_json(tmp_path):
    """Test JSON export."""
    introspector = MCPIntrospector()
    introspector.introspect()

    output_path = tmp_path / "mcp_structure.json"
    introspector.to_json(str(output_path))

    assert output_path.exists()
    import json
    with open(output_path) as f:
        data = json.load(f)
    assert "tools" in data
    assert "resources" in data
    assert "prompts" in data


def test_capabilities():
    """Test capability extraction."""
    result = introspect_mcp()
    assert "tools" in result.capabilities
    assert result.capabilities["tools"]["listChanged"] is True
```

### Acceptance Criteria

- [ ] Module implemented at `vibey/operations/docs/mcp_introspector.py`
- [ ] Static tools from all modules extracted
- [ ] Dynamic tools (agents, workflows) discovered
- [ ] Resources from all providers extracted
- [ ] Prompts from all providers extracted
- [ ] JSON Schema properly parsed
- [ ] JSON export working
- [ ] Unit tests passing

---

## Task 3: Build MCP Reference Markdown Generator

**ID:** `01KC81GRE23T0KSHR4ZCES476Z`
**Type:** Development
**Priority:** Medium
**Estimated Tokens:** 25,000

### Objective

Implement a generator that produces comprehensive Markdown documentation from MCP introspection data.

### Implementation

**File:** `vibey/operations/docs/mcp_reference_generator.py`

```python
"""
MCP Reference Markdown Generator.

Generates comprehensive MCP reference documentation from introspection data.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from vibey.operations.docs.mcp_introspector import (
    MCPIntrospector,
    MCPIntrospectionResult,
    ToolInfo,
    ResourceTemplateInfo,
    PromptInfo,
    SchemaProperty,
)


class MCPReferenceGenerator:
    """
    Generates Markdown MCP reference documentation.

    Output structure:
    - Overview and capabilities
    - Tools by category
    - Resources by provider
    - Prompts by category
    - JSON Schema appendix
    """

    def __init__(self, data: Optional[MCPIntrospectionResult] = None):
        self.data = data
        self._lines: List[str] = []

    def generate(self) -> str:
        """Generate complete MCP reference documentation."""
        if not self.data:
            introspector = MCPIntrospector()
            self.data = introspector.introspect()

        self._lines = []

        self._add_header()
        self._add_overview()
        self._add_tools_section()
        self._add_resources_section()
        self._add_prompts_section()
        self._add_schema_appendix()
        self._add_footer()

        return "\n".join(self._lines)

    def _add_header(self) -> None:
        """Add document header."""
        self._lines.extend([
            "# Vibey MCP Server Reference",
            "",
            f"> Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "> Do not edit manually - regenerate with `vibey docs generate mcp`",
            "",
            f"**Server:** `{self.data.server_name}`",
            f"**Version:** `{self.data.server_version}`",
            "",
        ])

    def _add_overview(self) -> None:
        """Add overview section with capabilities."""
        tool_count = len(self.data.tools)
        resource_count = len(self.data.resources)
        prompt_count = len(self.data.prompts)

        self._lines.extend([
            "## Overview",
            "",
            "The Vibey MCP Server exposes roadmap management operations through the",
            "[Model Context Protocol](https://modelcontextprotocol.io/).",
            "",
            "### Statistics",
            "",
            f"| Component | Count |",
            f"|-----------|-------|",
            f"| Tools | {tool_count} |",
            f"| Resources | {resource_count} |",
            f"| Prompts | {prompt_count} |",
            "",
            "### Capabilities",
            "",
            "```json",
            f"{self._format_json(self.data.capabilities)}",
            "```",
            "",
            "---",
            "",
        ])

    def _add_tools_section(self) -> None:
        """Add tools documentation."""
        self._lines.extend([
            "## Tools",
            "",
            "Tools are the primary interaction mechanism. Each tool accepts JSON input",
            "and returns structured results.",
            "",
        ])

        # Group tools by category
        categories = {}
        for tool in self.data.tools:
            cat = tool.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tool)

        # Add TOC
        self._lines.append("### Tool Categories")
        self._lines.append("")
        for cat in sorted(categories.keys()):
            count = len(categories[cat])
            self._lines.append(f"- [{cat.title()} Tools](#{cat}-tools) ({count})")
        self._lines.extend(["", "---", ""])

        # Document each category
        for cat in sorted(categories.keys()):
            self._add_tool_category(cat, categories[cat])

    def _add_tool_category(self, category: str, tools: List[ToolInfo]) -> None:
        """Add documentation for a tool category."""
        self._lines.extend([
            f"### {category.title()} Tools",
            "",
        ])

        for tool in sorted(tools, key=lambda t: t.name):
            self._add_tool_doc(tool)

    def _add_tool_doc(self, tool: ToolInfo) -> None:
        """Add documentation for a single tool."""
        # Header
        title = tool.title or tool.name.replace("vibey_", "").replace("_", " ").title()
        self._lines.extend([
            f"#### `{tool.name}`",
            "",
            f"**{title}**",
            "",
        ])

        # Dynamic badge
        if tool.is_dynamic:
            self._lines.extend([
                "> 🔄 **Dynamic Tool** - Generated from framework content",
                "",
            ])

        # Description
        if tool.description:
            self._lines.extend([
                tool.description,
                "",
            ])

        # Input Schema
        if tool.input_schema.properties:
            self._lines.extend([
                "**Parameters:**",
                "",
                "| Name | Type | Required | Description |",
                "|------|------|----------|-------------|",
            ])

            for prop in tool.input_schema.properties:
                req = "✓" if prop.required else ""
                type_str = prop.type
                if prop.enum:
                    type_str = f"enum: `{prop.enum}`"
                desc = prop.description or "-"
                if prop.default is not None:
                    desc += f" (default: `{prop.default}`)"

                self._lines.append(f"| `{prop.name}` | {type_str} | {req} | {desc} |")

            self._lines.append("")
        else:
            self._lines.extend([
                "**Parameters:** None",
                "",
            ])

        # Examples
        if tool.examples:
            self._lines.extend([
                "**Examples:**",
                "",
            ])
            for i, ex in enumerate(tool.examples, 1):
                self._lines.extend([
                    f"*{ex.description}*" if ex.description else f"*Example {i}*",
                    "",
                    "Request:",
                    "```json",
                    self._format_json(ex.request),
                    "```",
                    "",
                    "Response:",
                    "```json",
                    self._format_json(ex.response),
                    "```",
                    "",
                ])

        # Source file
        if tool.source_file:
            self._lines.extend([
                f"*Source: `{tool.source_file}`*",
                "",
            ])

        self._lines.extend(["---", ""])

    def _add_resources_section(self) -> None:
        """Add resources documentation."""
        if not self.data.resources:
            return

        self._lines.extend([
            "## Resources",
            "",
            "Resources provide read-only access to framework content.",
            "",
            "### Resource Templates",
            "",
            "| URI Template | Name | MIME Type | Provider |",
            "|--------------|------|-----------|----------|",
        ])

        for res in self.data.resources:
            self._lines.append(
                f"| `{res.uri_template}` | {res.name} | {res.mime_type} | {res.provider} |"
            )

        self._lines.extend(["", "---", ""])

        # Detailed docs
        for res in self.data.resources:
            self._add_resource_doc(res)

    def _add_resource_doc(self, resource: ResourceTemplateInfo) -> None:
        """Add documentation for a single resource."""
        self._lines.extend([
            f"### {resource.name}",
            "",
            f"**URI Template:** `{resource.uri_template}`",
            "",
            f"**MIME Type:** `{resource.mime_type}`",
            "",
            f"**Provider:** `{resource.provider}`",
            "",
        ])

        if resource.description:
            self._lines.extend([resource.description, ""])

        if resource.examples:
            self._lines.extend([
                "**Example URIs:**",
                "",
            ])
            for ex in resource.examples:
                self._lines.append(f"- `{ex}`")
            self._lines.append("")

        self._lines.extend(["---", ""])

    def _add_prompts_section(self) -> None:
        """Add prompts documentation."""
        if not self.data.prompts:
            return

        self._lines.extend([
            "## Prompts",
            "",
            "Prompts are parameterized message templates for common operations.",
            "",
            "### Available Prompts",
            "",
            "| Name | Category | Arguments |",
            "|------|----------|-----------|",
        ])

        for prompt in self.data.prompts:
            args = ", ".join(a.name for a in prompt.arguments) or "None"
            self._lines.append(f"| `{prompt.name}` | {prompt.category} | {args} |")

        self._lines.extend(["", "---", ""])

        # Detailed docs
        for prompt in self.data.prompts:
            self._add_prompt_doc(prompt)

    def _add_prompt_doc(self, prompt: PromptInfo) -> None:
        """Add documentation for a single prompt."""
        self._lines.extend([
            f"### `{prompt.name}`",
            "",
            f"**Category:** {prompt.category}",
            "",
        ])

        if prompt.description:
            self._lines.extend([prompt.description, ""])

        if prompt.arguments:
            self._lines.extend([
                "**Arguments:**",
                "",
                "| Name | Required | Description |",
                "|------|----------|-------------|",
            ])
            for arg in prompt.arguments:
                req = "✓" if arg.required else ""
                desc = arg.description or "-"
                self._lines.append(f"| `{arg.name}` | {req} | {desc} |")
            self._lines.append("")

        if prompt.example_output:
            self._lines.extend([
                "**Example Output:**",
                "",
                "```",
                prompt.example_output,
                "```",
                "",
            ])

        self._lines.extend(["---", ""])

    def _add_schema_appendix(self) -> None:
        """Add JSON Schema appendix."""
        self._lines.extend([
            "## Appendix: Common Schemas",
            "",
            "### Task Status Values",
            "",
            "```",
            "not_started | in_progress | blocked | completed | wont_do",
            "```",
            "",
            "### Sprint Status Values",
            "",
            "```",
            "not_started | in_progress | paused | completed | production_ready",
            "```",
            "",
            "### Track Status Values",
            "",
            "```",
            "not_started | in_progress | paused | completed | production_ready | deployed | wont_do",
            "```",
            "",
        ])

    def _add_footer(self) -> None:
        """Add document footer."""
        self._lines.extend([
            "---",
            "",
            "*This reference was auto-generated. For the latest version, run:*",
            "",
            "```bash",
            "vibey docs generate mcp",
            "```",
        ])

    def _format_json(self, obj) -> str:
        """Format object as JSON string."""
        import json
        return json.dumps(obj, indent=2, default=str)

    def write(self, path: str) -> None:
        """Write generated documentation to file."""
        content = self.generate()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content)


def generate_mcp_reference(
    output_path: str = "docs/reference/MCP_REFERENCE.md"
) -> str:
    """
    Generate MCP reference and write to file.

    Args:
        output_path: Where to write the generated documentation

    Returns:
        The generated Markdown content
    """
    generator = MCPReferenceGenerator()
    generator.write(output_path)
    return generator.generate()
```

### Output Structure

**File:** `docs/reference/MCP_REFERENCE.md`

```markdown
# Vibey MCP Server Reference

> Auto-generated on YYYY-MM-DD HH:MM:SS

**Server:** `vibey-roadmap`
**Version:** `2.5.0`

## Overview
- Statistics table
- Capabilities JSON

## Tools
### Task Tools
- vibey_start_task
- vibey_complete_task
- ...

### Sprint Tools
- vibey_start_sprint
- ...

### Query Tools
- vibey_query_track
- ...

### Content Tools
- vibey_content_list
- ...

### Agent Tools (Dynamic)
- vibey_invoke_agent_*
- ...

### Workflow Tools (Dynamic)
- vibey_run_workflow_*
- ...

## Resources
- Workflow resources
- Handoff resources

## Prompts
- Quality gate prompts

## Appendix
- Status value schemas
```

### Acceptance Criteria

- [ ] Generator implemented at `vibey/operations/docs/mcp_reference_generator.py`
- [ ] Tools documented by category
- [ ] Parameters shown in tables
- [ ] Examples rendered properly
- [ ] Resources and prompts documented
- [ ] Dynamic tools flagged with badge
- [ ] JSON Schema appendix included

---

## Task 4: Add Usage Examples to MCP Tools

**ID:** `01KC81GRE23T0KSHR4ZCES4770`
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 25,000

### Objective

Ensure every MCP tool has example request/response pairs for documentation.

### Example Format

Add `examples` key to tool definitions:

```python
{
    "name": "vibey_start_task",
    "title": "Start Task",
    "description": "Mark a task as in-progress",
    "inputSchema": {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "Task ID or slug"
            }
        },
        "required": ["task_id"]
    },
    "examples": [
        {
            "description": "Start a task by ID",
            "request": {
                "task_id": "01KC2D0JK7READW9KAK1HBX4B8"
            },
            "response": {
                "success": True,
                "task": {
                    "id": "01KC2D0JK7READW9KAK1HBX4B8",
                    "title": "Implement login form",
                    "status": "in_progress",
                    "started": "2025-01-15T10:30:00Z"
                }
            }
        },
        {
            "description": "Start a task by slug",
            "request": {
                "task_id": "auth-sprint-1-task-001"
            },
            "response": {
                "success": True,
                "task": {
                    "id": "01KC2D0JK7READW9KAK1HBX4B8",
                    "title": "Implement login form",
                    "status": "in_progress",
                    "started": "2025-01-15T10:30:00Z"
                }
            }
        }
    ]
}
```

### Files to Modify

| File | Tools | Examples Needed |
|------|-------|-----------------|
| `vibey/mcp/tools/task_tools.py` | ~8 | 16 |
| `vibey/mcp/tools/sprint_tools.py` | ~4 | 8 |
| `vibey/mcp/tools/query_tools.py` | ~5 | 10 |
| `vibey/mcp/tools/content_tools.py` | ~7 | 14 |

**Total:** ~24 tools, ~48 examples

### Example Templates by Category

#### Task Tools
- `vibey_start_task`: Start by ID, start by slug
- `vibey_complete_task`: Complete with deliverables, complete minimal
- `vibey_update_task`: Update status, update description
- `vibey_add_context`: Add file reference, add URL

#### Sprint Tools
- `vibey_start_sprint`: Start sprint, start with compatibility check
- `vibey_complete_sprint`: Complete with summary, complete with blockers
- `vibey_refresh_progress`: Refresh all, refresh single sprint
- `vibey_query_sprint`: Query by ID, query with tasks

#### Query Tools
- `vibey_query_track`: Query full track, query with filters
- `vibey_list_blockers`: All blockers, blockers for object
- `vibey_list_dependencies`: All deps, satisfied only
- `vibey_roadmap_status`: Full status summary
- `vibey_query_standards`: Standards with inheritance

#### Content Tools
- `vibey_content_list`: List agents, list workflows
- `vibey_content_show`: Show agent, show workflow
- `vibey_content_search`: Search by keyword
- `vibey_content_create`: Create agent
- `vibey_content_update`: Update agent
- `vibey_content_delete`: Delete agent
- `vibey_content_validate`: Validate agent

### Acceptance Criteria

- [ ] All tools have at least 2 examples
- [ ] Examples follow consistent format
- [ ] Request parameters are realistic
- [ ] Response structures match actual returns
- [ ] Introspector extracts all examples

---

## Task 5: Generate Initial MCP Reference Guide

**ID:** `01KC81GRE3GXVPVSCMD19FC4YP`
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 10,000

### Objective

Run the generator and verify 100% tool/resource coverage.

### Steps

1. Run introspection:
   ```bash
   python -c "
   from vibey.operations.docs.mcp_introspector import introspect_mcp
   result = introspect_mcp()
   print(f'Tools: {len(result.tools)}')
   print(f'Resources: {len(result.resources)}')
   print(f'Prompts: {len(result.prompts)}')
   "
   ```

2. Generate reference:
   ```bash
   python -c "
   from vibey.operations.docs.mcp_reference_generator import generate_mcp_reference
   generate_mcp_reference()
   "
   ```

3. Verify coverage:
   - Count tools in generated doc
   - Compare against `server.get_tools()` output
   - Ensure no tools missing

4. Review output:
   - Check formatting
   - Verify tables render correctly
   - Confirm examples are present

### Verification Checklist

- [ ] All static tools documented (~24)
- [ ] All dynamic tools documented (variable)
- [ ] All resource templates documented
- [ ] All prompts documented
- [ ] Parameters documented with types
- [ ] Examples render in code blocks
- [ ] Categories properly organized

### Output

**File:** `docs/reference/MCP_REFERENCE.md`

Expected size: ~1,500-2,500 lines

### Acceptance Criteria

- [ ] Reference generated successfully
- [ ] 100% component coverage verified
- [ ] Output committed to repository
- [ ] No formatting issues

---

## Task 6: Implement 'vibey docs generate mcp' Command

**ID:** `01KC81GRE23T0KSHR4ZCES4771`
**Type:** Development
**Priority:** Medium
**Estimated Tokens:** 8,000

### Objective

Add MCP reference generation to the `vibey docs generate` command.

### Implementation

Update `vibey/cli/docs.py`:

```python
@docs.command("generate")
@click.argument("doc_type", type=click.Choice(["cli", "mcp", "all"]))
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Custom output path"
)
@click.option(
    "--check", is_flag=True,
    help="Check if docs are up-to-date without regenerating"
)
@click.option(
    "--verbose", "-v", is_flag=True,
    help="Show detailed generation progress"
)
def generate(doc_type: str, output: Optional[str], check: bool, verbose: bool):
    """
    Generate reference documentation from code.

    Introspects the codebase and generates up-to-date reference
    documentation. Use --check to verify docs match code.

    Examples:

      vibey docs generate mcp          # Generate MCP reference
      vibey docs generate mcp --check  # Check if up-to-date
      vibey docs generate all          # Generate all docs
    """
    from vibey.operations.docs.cli_reference_generator import (
        CLIReferenceGenerator,
        generate_cli_reference
    )
    from vibey.operations.docs.mcp_reference_generator import (
        MCPReferenceGenerator,
        generate_mcp_reference
    )

    results = []

    # Generate CLI docs
    if doc_type in ("cli", "all"):
        cli_output = output if doc_type == "cli" else "docs/reference/CLI_REFERENCE.md"
        if check:
            result = _check_doc_drift(
                CLIReferenceGenerator, cli_output, "CLI", verbose
            )
        else:
            if verbose:
                click.echo("🔍 Introspecting CLI commands...")
            generate_cli_reference(cli_output)
            click.echo(f"✅ Generated CLI reference: {cli_output}")
            result = True
        results.append(("CLI", result))

    # Generate MCP docs
    if doc_type in ("mcp", "all"):
        mcp_output = output if doc_type == "mcp" else "docs/reference/MCP_REFERENCE.md"
        if check:
            result = _check_doc_drift(
                MCPReferenceGenerator, mcp_output, "MCP", verbose
            )
        else:
            if verbose:
                click.echo("🔍 Introspecting MCP server...")
            generate_mcp_reference(mcp_output)
            click.echo(f"✅ Generated MCP reference: {mcp_output}")
            result = True
        results.append(("MCP", result))

    # Report results
    if check:
        all_pass = all(r[1] for r in results)
        if not all_pass:
            raise SystemExit(1)


def _check_doc_drift(
    generator_class,
    output_path: str,
    name: str,
    verbose: bool
) -> bool:
    """Check if generated docs match committed version."""
    generator = generator_class()
    new_content = generator.generate()

    try:
        with open(output_path) as f:
            existing = f.read()

        if new_content == existing:
            click.echo(f"✅ {name} reference is up-to-date")
            return True
        else:
            click.echo(f"❌ {name} reference is out of date")
            if verbose:
                # Show diff summary
                new_lines = len(new_content.splitlines())
                old_lines = len(existing.splitlines())
                click.echo(f"   Current: {old_lines} lines, Generated: {new_lines} lines")
            click.echo(f"   Run 'vibey docs generate {name.lower()}' to update")
            return False
    except FileNotFoundError:
        click.echo(f"❌ {name} reference not found at {output_path}")
        return False
```

### Usage

```bash
# Generate MCP reference
vibey docs generate mcp

# Check if MCP docs are current
vibey docs generate mcp --check

# Generate all reference docs
vibey docs generate all

# Check all docs
vibey docs generate all --check
```

### Acceptance Criteria

- [ ] `mcp` option added to generate command
- [ ] Generate mode works correctly
- [ ] Check mode compares and reports drift
- [ ] `all` option generates both CLI and MCP
- [ ] Help text and examples included

---

## Task 7: Implement MCP Drift Detection

**ID:** `01KC81GRE23T0KSHR4ZCES4772`
**Type:** Development
**Priority:** Medium
**Estimated Tokens:** 10,000

### Objective

Integrate MCP documentation drift detection into CI.

### Implementation

Update `.github/workflows/docs-drift.yml`:

```yaml
name: Documentation Drift Check

on:
  push:
    paths:
      - 'vibey/cli/**'
      - 'vibey/mcp/**'
      - 'docs/reference/CLI_REFERENCE.md'
      - 'docs/reference/MCP_REFERENCE.md'
  pull_request:
    paths:
      - 'vibey/cli/**'
      - 'vibey/mcp/**'

jobs:
  check-docs-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .

      - name: Check CLI reference drift
        run: |
          vibey docs generate cli --check

      - name: Check MCP reference drift
        run: |
          vibey docs generate mcp --check

      - name: Report drift
        if: failure()
        run: |
          echo "::error::Documentation is out of date!"
          echo "Run 'vibey docs generate all' locally and commit the changes."
```

### Makefile Targets

```makefile
.PHONY: check-docs
check-docs:
	vibey docs generate all --check

.PHONY: generate-docs
generate-docs:
	vibey docs generate all

.PHONY: docs
docs: generate-docs
	@echo "Documentation generated successfully"
```

### Pre-commit Hook (Optional)

```yaml
# .pre-commit-config.yaml
  - repo: local
    hooks:
      - id: check-mcp-docs
        name: Check MCP docs drift
        entry: vibey docs generate mcp --check
        language: system
        files: ^vibey/mcp/.*\.py$
        pass_filenames: false
```

### Acceptance Criteria

- [ ] CI workflow updated for MCP
- [ ] Both CLI and MCP checked
- [ ] Clear error messages
- [ ] Makefile targets available
- [ ] Optional pre-commit hook documented

---

## File Structure After Sprint

```
vibey/
├── operations/
│   └── docs/
│       ├── __init__.py
│       ├── cli_introspector.py       # Sprint 2.1
│       ├── cli_reference_generator.py # Sprint 2.1
│       ├── mcp_introspector.py       # Task 2
│       └── mcp_reference_generator.py # Task 3
├── mcp/
│   └── tools/
│       ├── task_tools.py             # Task 4 (examples added)
│       ├── sprint_tools.py           # Task 4 (examples added)
│       ├── query_tools.py            # Task 4 (examples added)
│       └── content_tools.py          # Task 4 (examples added)
│
docs/
├── reference/
│   ├── CLI_REFERENCE.md              # Sprint 2.1
│   └── MCP_REFERENCE.md              # Task 5 (generated)
│
.github/
└── workflows/
    └── docs-drift.yml                # Task 7 (updated)

.vibey/roadmap/context/sprints/user-journey-phase-2-2/
├── SPRINT_PLAN.md                    # This document
└── MCP_INTROSPECTION_DESIGN.md       # Task 1 output
```

---

## Dependencies on Sprint 2.1

This sprint builds on Sprint 2.1 (CLI Reference Guide):

| Dependency | Type | Notes |
|------------|------|-------|
| `vibey docs generate` command | Hard | Base command exists from 2.1 |
| Generator architecture pattern | Soft | Follow same patterns |
| CI workflow structure | Hard | Extend existing workflow |
| Documentation structure | Soft | Same `docs/reference/` location |

**Recommended:** Complete Sprint 2.1 before starting Sprint 2.2.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| MCP SDK API changes | Medium | High | Pin version, abstract SDK calls |
| Dynamic tool discovery fails | Medium | Medium | Graceful degradation, skip dynamic |
| Resource providers not initialized | Low | Medium | Lazy initialization, mock data |
| Large number of dynamic tools | Medium | Low | Category grouping, TOC navigation |
| Example data becomes stale | High | Low | Use realistic but generic examples |

---

## Definition of Done

- [ ] All 7 tasks completed
- [ ] 100% MCP tool coverage in generated docs
- [ ] All resources and prompts documented
- [ ] CI drift detection passing
- [ ] Examples present for all tools
- [ ] Documentation reviewed for accuracy
- [ ] No regressions in MCP server functionality
- [ ] Sprint summary written
