# MCP Introspection Architecture Design

**Task ID:** `01KC81GRE23T0KSHR4ZCES476X`
**Sprint:** Phase 2.2 - MCP Server Reference Guide (Auto-Generated)
**Status:** In Progress
**Created:** 2025-12-12

---

## 1. Overview

This document specifies the architecture for an MCP server introspection system that extracts structured documentation data from tools, resources, and prompts. The goal is to enable automatic generation of MCP reference documentation that cannot drift from the implementation.

### 1.1 Requirements

| Requirement | Description |
|-------------|-------------|
| **Complete Coverage** | Extract data from all MCP tools, resources, and prompts |
| **Structured Output** | JSON-serializable data model |
| **Schema Extraction** | Parse JSON Schema for tool inputs |
| **Example Support** | Include request/response examples |
| **Category Organization** | Group by component type and category |
| **Deterministic** | Same input always produces same output |

### 1.2 MCP Server Structure

```
vibey/mcp/
├── server.py                    # VibeyMCPServer class
├── tools/                       # Tool definitions
│   ├── task_tools.py            # get_task_tools() → 3 tools
│   ├── sprint_tools.py          # get_sprint_tools() → 4 tools
│   ├── query_tools.py           # get_query_tools() → 5 tools
│   └── content_tools.py         # get_content_tools() → 7 tools
├── resources/                   # MCP resources
│   ├── workflows.py             # WorkflowResourceProvider
│   ├── handoffs.py              # HandoffResourceProvider
│   └── manager.py               # ResourceManager
├── prompts/                     # MCP prompts
│   ├── quality_gates.py         # QualityGatePromptProvider
│   └── manager.py               # PromptManager
└── discovery/                   # Dynamic discovery
    ├── agents.py                # Agent tool generation
    └── workflows.py             # Workflow tool generation

Static Tools: ~19
Dynamic Tools: Variable (from frontmatter)
Resources: ~6 templates
Prompts: ~5 definitions
```

---

## 2. Data Model

### 2.1 Core Types

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Any, Dict
import json


class MCPComponentType(str, Enum):
    """Type of MCP component."""
    TOOL = "tool"
    RESOURCE = "resource"
    PROMPT = "prompt"


@dataclass
class SchemaProperty:
    """
    JSON Schema property definition.

    Attributes:
        name: Property name
        type: JSON Schema type (string, integer, boolean, etc.)
        description: Human-readable description
        required: Whether property is required
        default: Default value if any
        enum: Allowed values for enum types
    """
    name: str
    type: str
    description: Optional[str] = None
    required: bool = False
    default: Any = None
    enum: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
            "default": self.default,
            "enum": self.enum,
        }


@dataclass
class InputSchema:
    """
    Tool input schema (parsed from JSON Schema).

    Attributes:
        properties: List of schema properties
        required: Names of required properties
        raw_schema: Original JSON Schema dict
    """
    properties: List[SchemaProperty] = field(default_factory=list)
    required: List[str] = field(default_factory=list)
    raw_schema: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "properties": [p.to_dict() for p in self.properties],
            "required": self.required,
        }


@dataclass
class ToolExample:
    """
    Example request/response for a tool.

    Attributes:
        description: What this example demonstrates
        request: Example input arguments
        response: Example output (optional)
    """
    description: str
    request: Dict[str, Any]
    response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "description": self.description,
            "request": self.request,
        }
        if self.response:
            result["response"] = self.response
        return result


@dataclass
class ToolInfo:
    """
    Introspected information about an MCP tool.

    Attributes:
        name: Tool name (e.g., "vibey_start_task")
        title: Human-readable title
        description: Full description
        input_schema: Parsed input schema
        category: Tool category (task, sprint, query, content, agent, workflow)
        examples: Usage examples
        source_file: Source file path (relative)
    """
    name: str
    title: Optional[str]
    description: str
    input_schema: InputSchema
    category: str = "unknown"
    examples: List[ToolExample] = field(default_factory=list)
    source_file: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "input_schema": self.input_schema.to_dict(),
            "category": self.category,
            "examples": [e.to_dict() for e in self.examples],
            "source_file": self.source_file,
        }


@dataclass
class ResourceTemplateInfo:
    """
    Introspected information about an MCP resource template.

    Attributes:
        uri_template: URI template (e.g., "vibey://workflows/{workflow_id}")
        name: Resource name
        description: Full description
        mime_type: Content MIME type
        provider: Provider class name
        category: Resource category
    """
    uri_template: str
    name: str
    description: str
    mime_type: str
    provider: str
    category: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uri_template": self.uri_template,
            "name": self.name,
            "description": self.description,
            "mime_type": self.mime_type,
            "provider": self.provider,
            "category": self.category,
        }


@dataclass
class PromptArgument:
    """
    Argument for an MCP prompt.

    Attributes:
        name: Argument name
        description: Argument description
        required: Whether argument is required
    """
    name: str
    description: str
    required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
        }


@dataclass
class PromptInfo:
    """
    Introspected information about an MCP prompt.

    Attributes:
        name: Prompt name (e.g., "vibey_quality_gate_check")
        description: Full description
        arguments: List of prompt arguments
        category: Prompt category
        provider: Provider class name
    """
    name: str
    description: str
    arguments: List[PromptArgument] = field(default_factory=list)
    category: str = "unknown"
    provider: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": [a.to_dict() for a in self.arguments],
            "category": self.category,
            "provider": self.provider,
        }


@dataclass
class MCPStructure:
    """
    Complete introspected MCP server structure.

    Attributes:
        tools: List of tool definitions
        resources: List of resource templates
        prompts: List of prompt definitions
        server_name: MCP server name
        version: Server version
        generated_at: ISO timestamp
    """
    tools: List[ToolInfo] = field(default_factory=list)
    resources: List[ResourceTemplateInfo] = field(default_factory=list)
    prompts: List[PromptInfo] = field(default_factory=list)
    server_name: str = "vibey-roadmap"
    version: str = "unknown"
    generated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tools": [t.to_dict() for t in self.tools],
            "resources": [r.to_dict() for r in self.resources],
            "prompts": [p.to_dict() for p in self.prompts],
            "server_name": self.server_name,
            "version": self.version,
            "total_tools": len(self.tools),
            "total_resources": len(self.resources),
            "total_prompts": len(self.prompts),
            "generated_at": self.generated_at,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
```

### 2.2 JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MCPStructure",
  "type": "object",
  "required": ["tools", "resources", "prompts", "server_name"],
  "properties": {
    "tools": {
      "type": "array",
      "items": { "$ref": "#/definitions/ToolInfo" }
    },
    "resources": {
      "type": "array",
      "items": { "$ref": "#/definitions/ResourceTemplateInfo" }
    },
    "prompts": {
      "type": "array",
      "items": { "$ref": "#/definitions/PromptInfo" }
    },
    "server_name": { "type": "string" },
    "version": { "type": "string" },
    "total_tools": { "type": "integer" },
    "total_resources": { "type": "integer" },
    "total_prompts": { "type": "integer" },
    "generated_at": { "type": "string", "format": "date-time" }
  },
  "definitions": {
    "ToolInfo": {
      "type": "object",
      "required": ["name", "description", "input_schema"],
      "properties": {
        "name": { "type": "string" },
        "title": { "type": ["string", "null"] },
        "description": { "type": "string" },
        "input_schema": { "$ref": "#/definitions/InputSchema" },
        "category": { "type": "string" },
        "examples": {
          "type": "array",
          "items": { "$ref": "#/definitions/ToolExample" }
        },
        "source_file": { "type": ["string", "null"] }
      }
    },
    "InputSchema": {
      "type": "object",
      "properties": {
        "properties": {
          "type": "array",
          "items": { "$ref": "#/definitions/SchemaProperty" }
        },
        "required": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "SchemaProperty": {
      "type": "object",
      "required": ["name", "type"],
      "properties": {
        "name": { "type": "string" },
        "type": { "type": "string" },
        "description": { "type": ["string", "null"] },
        "required": { "type": "boolean" },
        "default": {},
        "enum": {
          "type": ["array", "null"],
          "items": { "type": "string" }
        }
      }
    },
    "ToolExample": {
      "type": "object",
      "required": ["description", "request"],
      "properties": {
        "description": { "type": "string" },
        "request": { "type": "object" },
        "response": { "type": ["object", "null"] }
      }
    },
    "ResourceTemplateInfo": {
      "type": "object",
      "required": ["uri_template", "name", "description", "mime_type"],
      "properties": {
        "uri_template": { "type": "string" },
        "name": { "type": "string" },
        "description": { "type": "string" },
        "mime_type": { "type": "string" },
        "provider": { "type": "string" },
        "category": { "type": "string" }
      }
    },
    "PromptInfo": {
      "type": "object",
      "required": ["name", "description"],
      "properties": {
        "name": { "type": "string" },
        "description": { "type": "string" },
        "arguments": {
          "type": "array",
          "items": { "$ref": "#/definitions/PromptArgument" }
        },
        "category": { "type": "string" },
        "provider": { "type": ["string", "null"] }
      }
    },
    "PromptArgument": {
      "type": "object",
      "required": ["name", "description"],
      "properties": {
        "name": { "type": "string" },
        "description": { "type": "string" },
        "required": { "type": "boolean" }
      }
    }
  }
}
```

---

## 3. Introspection Algorithm

### 3.1 Tool Introspection

```python
def introspect_tools() -> List[ToolInfo]:
    """
    Introspect all MCP tools.

    Sources:
    1. Static tools from get_*_tools() functions
    2. Dynamic tools from ToolDiscovery

    Algorithm:
    1. Import tool getter functions
    2. Call each getter to get tool definitions
    3. Parse each tool's inputSchema
    4. Categorize based on name prefix or source file
    5. Extract examples from tool metadata or docstrings
    """
    tools = []

    # Static tool sources
    tool_sources = [
        ("task_tools", "task", get_task_tools),
        ("sprint_tools", "sprint", get_sprint_tools),
        ("query_tools", "query", get_query_tools),
        ("content_tools", "content", get_content_tools),
    ]

    for source_name, category, getter in tool_sources:
        for tool_def in getter():
            tools.append(parse_tool_definition(tool_def, category, source_name))

    # Dynamic tools (if discovery enabled)
    try:
        discovery = ToolDiscovery(root_dir=Path.cwd())
        dynamic_tools = discovery.discover()
        for tool_def in dynamic_tools:
            category = infer_category(tool_def['name'])
            tools.append(parse_tool_definition(tool_def, category, "discovery"))
    except Exception as e:
        logger.warning(f"Dynamic tool discovery failed: {e}")

    return tools


def parse_tool_definition(
    tool_def: Dict[str, Any],
    category: str,
    source: str
) -> ToolInfo:
    """Parse a tool definition dict into ToolInfo."""
    schema = tool_def.get('inputSchema', {})

    return ToolInfo(
        name=tool_def['name'],
        title=tool_def.get('title'),
        description=tool_def.get('description', ''),
        input_schema=parse_input_schema(schema),
        category=category,
        examples=extract_tool_examples(tool_def),
        source_file=f"vibey/mcp/tools/{source}.py"
    )


def parse_input_schema(schema: Dict[str, Any]) -> InputSchema:
    """Parse JSON Schema into InputSchema."""
    properties = []
    required_names = schema.get('required', [])

    for name, prop_def in schema.get('properties', {}).items():
        properties.append(SchemaProperty(
            name=name,
            type=prop_def.get('type', 'any'),
            description=prop_def.get('description'),
            required=name in required_names,
            default=prop_def.get('default'),
            enum=prop_def.get('enum'),
        ))

    return InputSchema(
        properties=properties,
        required=required_names,
        raw_schema=schema
    )
```

### 3.2 Resource Introspection

```python
def introspect_resources() -> List[ResourceTemplateInfo]:
    """
    Introspect all MCP resource templates.

    Sources:
    1. WorkflowResourceProvider
    2. HandoffResourceProvider
    3. (Future providers)

    Algorithm:
    1. Import resource providers
    2. Instantiate each provider
    3. Call get_templates() method
    4. Parse ResourceTemplate objects
    """
    resources = []

    # Resource providers
    providers = [
        (WorkflowResourceProvider, "workflows"),
        (HandoffResourceProvider, "handoffs"),
    ]

    content_root = find_content_root()

    for provider_class, category in providers:
        try:
            provider = provider_class(content_root)
            templates = provider.get_templates()

            for template in templates:
                resources.append(ResourceTemplateInfo(
                    uri_template=template.uriTemplate,
                    name=template.name,
                    description=template.description,
                    mime_type=template.mimeType,
                    provider=provider_class.__name__,
                    category=category,
                ))
        except Exception as e:
            logger.warning(f"Resource provider {provider_class.__name__} failed: {e}")

    return resources
```

### 3.3 Prompt Introspection

```python
def introspect_prompts() -> List[PromptInfo]:
    """
    Introspect all MCP prompts.

    Sources:
    1. QualityGatePromptProvider
    2. (Future providers)

    Algorithm:
    1. Import prompt providers
    2. Instantiate each provider
    3. Call get_prompts() method
    4. Parse PromptDefinition objects
    """
    prompts = []

    # Prompt providers
    providers = [
        (QualityGatePromptProvider, "quality_gates"),
    ]

    content_root = find_content_root()

    for provider_class, category in providers:
        try:
            provider = provider_class(content_root)
            prompt_defs = provider.get_prompts()

            for prompt_def in prompt_defs:
                arguments = [
                    PromptArgument(
                        name=arg.name,
                        description=arg.description,
                        required=arg.required,
                    )
                    for arg in prompt_def.arguments
                ]

                prompts.append(PromptInfo(
                    name=prompt_def.name,
                    description=prompt_def.description,
                    arguments=arguments,
                    category=category,
                    provider=provider_class.__name__,
                ))
        except Exception as e:
            logger.warning(f"Prompt provider {provider_class.__name__} failed: {e}")

    return prompts
```

---

## 4. Example Extraction

### 4.1 Tool Examples

Examples can come from multiple sources:

#### Source 1: Tool Definition Metadata
```python
{
    "name": "vibey_start_task",
    "description": "Start a task",
    "inputSchema": {...},
    "examples": [
        {
            "description": "Start a specific task",
            "request": {"task_id": "sprint-1-task-001"},
            "response": {"status": "success", "task": {...}}
        }
    ]
}
```

#### Source 2: Docstring Parsing
```python
def extract_examples_from_docstring(func: callable) -> List[ToolExample]:
    """Parse examples from function docstring."""
    docstring = func.__doc__
    if not docstring:
        return []

    examples = []
    # Look for Example: or Examples: section
    # Parse JSON blocks
    return examples
```

#### Source 3: Predefined Examples Dict
```python
TOOL_EXAMPLES = {
    "vibey_start_task": [
        ToolExample(
            description="Start a task in sprint 1",
            request={"task_id": "mcp-server-1-task-001"},
            response={"status": "started", "timestamp": "2025-12-12T10:00:00Z"}
        )
    ],
    # ... more tools
}
```

---

## 5. Error Handling

### 5.1 Graceful Degradation

| Scenario | Handling |
|----------|----------|
| Missing tool module | Skip module, log warning |
| Invalid inputSchema | Return empty schema with warning |
| Provider initialization fails | Skip provider, log warning |
| Dynamic discovery fails | Continue with static tools only |
| Missing examples | Return empty list (not fatal) |

### 5.2 Error Recovery Pattern

```python
def safe_introspect_tools() -> List[ToolInfo]:
    """Introspect with error recovery."""
    tools = []
    errors = []

    for source_name, getter in TOOL_SOURCES.items():
        try:
            tool_defs = getter()
            for tool_def in tool_defs:
                try:
                    tools.append(parse_tool_definition(tool_def))
                except Exception as e:
                    errors.append(f"Tool {tool_def.get('name', 'unknown')}: {e}")
        except Exception as e:
            errors.append(f"Source {source_name}: {e}")

    if errors:
        logger.warning(f"Introspection errors: {errors}")

    return tools
```

---

## 6. Integration Points

### 6.1 Entry Point

```python
# vibey/operations/docs/mcp_introspector.py

def introspect_mcp() -> MCPStructure:
    """
    Introspect the Vibey MCP server.

    Returns:
        MCPStructure with all tools, resources, and prompts

    Usage:
        from vibey.operations.docs.mcp_introspector import introspect_mcp

        structure = introspect_mcp()
        print(f"Total tools: {len(structure.tools)}")
        print(structure.to_json())
    """
    from vibey.cli.main import __version__

    tools = introspect_tools()
    resources = introspect_resources()
    prompts = introspect_prompts()

    return MCPStructure(
        tools=tools,
        resources=resources,
        prompts=prompts,
        server_name="vibey-roadmap",
        version=__version__,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
```

### 6.2 CLI Integration

```python
# In vibey/cli/main.py

@docs.command('generate-mcp')
@click.option('--output', '-o', type=click.Path(),
              default='docs/reference/MCP_REFERENCE.md')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json']))
def docs_generate_mcp(output: str, format: str):
    """Auto-generate MCP server reference documentation."""
    from vibey.operations.docs.mcp_introspector import introspect_mcp
    from vibey.operations.docs.mcp_reference_generator import generate_mcp_reference

    structure = introspect_mcp()

    if format == 'json':
        content = structure.to_json()
    else:
        content = generate_mcp_reference(structure)

    Path(output).write_text(content)
    click.echo(f"Generated: {output}")
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

```python
def test_parse_input_schema():
    """Test JSON Schema parsing."""
    schema = {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "Task ID"},
            "force": {"type": "boolean", "default": False}
        },
        "required": ["task_id"]
    }

    result = parse_input_schema(schema)

    assert len(result.properties) == 2
    assert result.properties[0].name == "task_id"
    assert result.properties[0].required
    assert not result.properties[1].required


def test_introspect_tools_returns_expected_count():
    """Test tool introspection."""
    tools = introspect_tools()

    # Should have at least static tools
    assert len(tools) >= 19  # 3 + 4 + 5 + 7

    # Check categories
    categories = {t.category for t in tools}
    assert "task" in categories
    assert "sprint" in categories
    assert "query" in categories
    assert "content" in categories
```

### 7.2 Integration Tests

```python
def test_full_introspection():
    """Test complete MCP introspection."""
    structure = introspect_mcp()

    assert structure.server_name == "vibey-roadmap"
    assert len(structure.tools) > 0
    assert structure.generated_at

    # Verify JSON serialization
    json_output = structure.to_json()
    parsed = json.loads(json_output)
    assert parsed['total_tools'] == len(structure.tools)
```

---

## 8. Acceptance Criteria Checklist

- [x] Complete data model documented (Section 2)
- [x] Tool introspection algorithm specified (Section 3.1)
- [x] Resource introspection algorithm specified (Section 3.2)
- [x] Prompt introspection algorithm specified (Section 3.3)
- [x] JSON output schema defined (Section 2.2)
- [x] Example extraction strategy documented (Section 4)
- [x] Error handling specified (Section 5)
- [x] Integration points defined (Section 6)
- [x] Testing strategy outlined (Section 7)

---

## 9. Next Steps

1. **Task 2:** Implement `mcp_introspector.py` based on this design
2. **Task 3:** Implement Markdown generator using introspection output
3. **Task 4:** Add examples to MCP tools
4. **Task 5:** Generate initial reference guide
5. **Task 6:** Add `vibey docs generate-mcp` command
6. **Task 7:** Implement drift detection in CI

---

## Appendix A: Known MCP Components

### Tools (~19 static)

| Category | Tool Name | Description |
|----------|-----------|-------------|
| task | vibey_start_task | Start working on a task |
| task | vibey_complete_task | Mark task as completed |
| task | vibey_query_task | Get task details |
| sprint | vibey_start_sprint | Start a sprint |
| sprint | vibey_complete_sprint | Complete a sprint |
| sprint | vibey_refresh_progress | Refresh sprint progress |
| sprint | vibey_query_sprint | Get sprint details |
| query | vibey_query_track | Get track details |
| query | vibey_list_blockers | List blocked items |
| query | vibey_list_dependencies | List dependencies |
| query | vibey_roadmap_status | Get roadmap status |
| query | vibey_query_standards | Query quality standards |
| content | vibey_content_list | List content items |
| content | vibey_content_show | Show content details |
| content | vibey_content_search | Search content |
| content | vibey_content_create | Create content |
| content | vibey_content_update | Update content |
| content | vibey_content_delete | Delete content |
| content | vibey_content_validate | Validate content |

### Resources (~6 templates)

| Provider | URI Template | MIME Type |
|----------|--------------|-----------|
| WorkflowResourceProvider | vibey://workflows/{workflow_id} | text/markdown |
| WorkflowResourceProvider | vibey://workflows/{workflow_id}/steps | application/json |
| WorkflowResourceProvider | vibey://workflows/{workflow_id}/metadata | application/json |
| HandoffResourceProvider | vibey://handoffs/{handoff_id} | text/markdown |
| HandoffResourceProvider | vibey://handoffs/{handoff_id}/schema | application/json |
| HandoffResourceProvider | vibey://handoffs/list | application/json |

### Prompts (~5 definitions)

| Provider | Prompt Name | Description |
|----------|-------------|-------------|
| QualityGatePromptProvider | vibey_quality_gate_check | Run quality gate check |
| QualityGatePromptProvider | vibey_security_audit | Security vulnerability scan |
| QualityGatePromptProvider | vibey_test_coverage | Test coverage analysis |
| QualityGatePromptProvider | vibey_doc_completeness | Documentation check |
| QualityGatePromptProvider | vibey_performance_review | Performance analysis |
