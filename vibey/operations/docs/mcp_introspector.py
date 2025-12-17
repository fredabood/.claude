"""
MCP Server Introspection Module

Extracts structured documentation data from the Vibey MCP server
including tools, resources, and prompts. Enables auto-generation
of MCP reference documentation that cannot drift from implementation.

Usage:
    from vibey.operations.docs.mcp_introspector import introspect_mcp

    structure = introspect_mcp()
    print(f"Total tools: {len(structure.tools)}")
    print(f"Total resources: {len(structure.resources)}")
    print(f"Total prompts: {len(structure.prompts)}")

    # Export to JSON
    json_output = structure.to_json()

Task: 01KC81GRE23T0KSHR4ZCES476Y
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional, Any, Dict, Tuple
import json
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================


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
        minimum: Minimum value (for numbers)
        maximum: Maximum value (for numbers)
    """
    name: str
    type: str
    description: Optional[str] = None
    required: bool = False
    default: Any = None
    enum: Optional[List[str]] = None
    minimum: Optional[int] = None
    maximum: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
        }
        if self.default is not None:
            result["default"] = self.default
        if self.enum:
            result["enum"] = self.enum
        if self.minimum is not None:
            result["minimum"] = self.minimum
        if self.maximum is not None:
            result["maximum"] = self.maximum
        return result


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
        """Convert to dictionary for JSON serialization."""
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
        """Convert to dictionary for JSON serialization."""
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
        """Convert to dictionary for JSON serialization."""
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
        """Convert to dictionary for JSON serialization."""
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
        """Convert to dictionary for JSON serialization."""
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
        """Convert to dictionary for JSON serialization."""
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

    def __post_init__(self):
        """Set generated_at if not provided."""
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()

    def count_by_category(self) -> Dict[str, Dict[str, int]]:
        """Count components by category."""
        result = {
            "tools": {},
            "resources": {},
            "prompts": {},
        }
        for tool in self.tools:
            result["tools"][tool.category] = result["tools"].get(tool.category, 0) + 1
        for resource in self.resources:
            result["resources"][resource.category] = result["resources"].get(resource.category, 0) + 1
        for prompt in self.prompts:
            result["prompts"][prompt.category] = result["prompts"].get(prompt.category, 0) + 1
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "server_name": self.server_name,
            "version": self.version,
            "generated_at": self.generated_at,
            "total_tools": len(self.tools),
            "total_resources": len(self.resources),
            "total_prompts": len(self.prompts),
            "categories": self.count_by_category(),
            "tools": [t.to_dict() for t in self.tools],
            "resources": [r.to_dict() for r in self.resources],
            "prompts": [p.to_dict() for p in self.prompts],
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# =============================================================================
# Predefined Examples
# =============================================================================

TOOL_EXAMPLES: Dict[str, List[ToolExample]] = {
    "vibey_start_task": [
        ToolExample(
            description="Start a task by ULID",
            request={"task_id": "01KC2D0JK7READW9KAK1HBX4A5"},
        ),
        ToolExample(
            description="Start a task by slug",
            request={"task_id": "mcp-server-1-task-001"},
        ),
    ],
    "vibey_complete_task": [
        ToolExample(
            description="Complete a task with token count",
            request={"task_id": "01KC2D0JK7READW9KAK1HBX4A5", "actual_tokens": 15000},
        ),
    ],
    "vibey_query_task": [
        ToolExample(
            description="Query task details",
            request={"task_id": "01KC2D0JK7READW9KAK1HBX4A5"},
        ),
    ],
    "vibey_start_sprint": [
        ToolExample(
            description="Start a sprint by ULID",
            request={"sprint_id": "01KC2D0JK8CHXNPPB2V3M632C1"},
        ),
    ],
    "vibey_complete_sprint": [
        ToolExample(
            description="Complete a sprint",
            request={"sprint_id": "01KC2D0JK8CHXNPPB2V3M632C1"},
        ),
    ],
    "vibey_refresh_progress": [
        ToolExample(
            description="Refresh all progress counters",
            request={},
        ),
    ],
    "vibey_query_sprint": [
        ToolExample(
            description="Query sprint details",
            request={"sprint_id": "01KC2D0JK8CHXNPPB2V3M632C1"},
        ),
    ],
    "vibey_query_track": [
        ToolExample(
            description="Query track details",
            request={"track_id": "01KC2D0JK6JC6706H9WP2NH5DA"},
        ),
    ],
    "vibey_list_blockers": [
        ToolExample(
            description="List all blocked items",
            request={},
        ),
        ToolExample(
            description="List blockers for a specific track",
            request={"track_id": "01KC2D0JK6JC6706H9WP2NH5DA"},
        ),
    ],
    "vibey_roadmap_status": [
        ToolExample(
            description="Get overall roadmap status",
            request={},
        ),
    ],
    "vibey_content_list": [
        ToolExample(
            description="List all agents",
            request={"content_type": "agents"},
        ),
        ToolExample(
            description="List all workflows",
            request={"content_type": "workflows"},
        ),
    ],
    "vibey_content_show": [
        ToolExample(
            description="Show a workflow definition",
            request={"content_type": "workflows", "item_id": "sprint-planning"},
        ),
    ],
    "vibey_content_search": [
        ToolExample(
            description="Search for security-related content",
            request={"query": "security audit"},
        ),
    ],
}


# =============================================================================
# Introspection Implementation
# =============================================================================


class MCPIntrospector:
    """
    Introspects the Vibey MCP server to extract documentation data.

    This class walks through all tools, resources, and prompts defined
    in the MCP server and extracts structured information for
    documentation generation.

    Example:
        >>> introspector = MCPIntrospector()
        >>> structure = introspector.introspect()
        >>> print(f"Found {len(structure.tools)} tools")
    """

    def __init__(self, content_root: Optional[Path] = None):
        """
        Initialize the introspector.

        Args:
            content_root: Root directory for content discovery.
                         Defaults to current working directory.
        """
        self.content_root = content_root or Path.cwd()
        self._errors: List[str] = []

    def introspect(self) -> MCPStructure:
        """
        Perform full MCP server introspection.

        Returns:
            MCPStructure containing all tools, resources, and prompts.
        """
        self._errors = []

        tools = self._introspect_tools()
        resources = self._introspect_resources()
        prompts = self._introspect_prompts()

        # Get version from CLI
        version = self._get_version()

        if self._errors:
            logger.warning(f"Introspection completed with {len(self._errors)} errors:")
            for error in self._errors:
                logger.warning(f"  - {error}")

        return MCPStructure(
            tools=tools,
            resources=resources,
            prompts=prompts,
            server_name="vibey-roadmap",
            version=version,
        )

    def _get_version(self) -> str:
        """Get the Vibey CLI version."""
        try:
            from vibey.cli.main import __version__
            return __version__
        except ImportError:
            return "unknown"

    def _introspect_tools(self) -> List[ToolInfo]:
        """
        Introspect all MCP tools.

        Returns:
            List of ToolInfo objects.
        """
        tools = []

        # Static tool sources: (module_path, category, getter_name)
        tool_sources: List[Tuple[str, str, str]] = [
            ("vibey.mcp.tools.task_tools", "task", "get_task_tools"),
            ("vibey.mcp.tools.sprint_tools", "sprint", "get_sprint_tools"),
            ("vibey.mcp.tools.query_tools", "query", "get_query_tools"),
            ("vibey.mcp.tools.content_tools", "content", "get_content_tools"),
        ]

        for module_path, category, getter_name in tool_sources:
            try:
                tools.extend(self._introspect_tool_source(
                    module_path, category, getter_name
                ))
            except Exception as e:
                self._errors.append(f"Tool source {module_path}: {e}")

        # Dynamic tools (from discovery)
        try:
            tools.extend(self._introspect_dynamic_tools())
        except Exception as e:
            self._errors.append(f"Dynamic tool discovery: {e}")

        # Sort by category then name
        tools.sort(key=lambda t: (t.category, t.name))

        return tools

    def _introspect_tool_source(
        self,
        module_path: str,
        category: str,
        getter_name: str,
    ) -> List[ToolInfo]:
        """
        Introspect tools from a specific source module.

        Args:
            module_path: Full module path (e.g., "vibey.mcp.tools.task_tools")
            category: Tool category
            getter_name: Name of the getter function

        Returns:
            List of ToolInfo objects from this source.
        """
        import importlib

        module = importlib.import_module(module_path)
        getter = getattr(module, getter_name)
        tool_defs = getter()

        source_file = module_path.replace(".", "/") + ".py"

        tools = []
        for tool_def in tool_defs:
            try:
                tool_info = self._parse_tool_definition(tool_def, category, source_file)
                tools.append(tool_info)
            except Exception as e:
                self._errors.append(f"Tool {tool_def.get('name', 'unknown')}: {e}")

        return tools

    def _introspect_dynamic_tools(self) -> List[ToolInfo]:
        """
        Introspect dynamically discovered tools (agents, workflows).

        Returns:
            List of ToolInfo objects from dynamic discovery.
        """
        try:
            from vibey.mcp.discovery import ToolDiscovery

            discovery = ToolDiscovery(
                root_dir=self.content_root,
                cache_ttl=0,  # No caching for introspection
                tool_prefix="vibey"
            )

            tools = []
            for tool_def in discovery.get_all_tools():
                # Infer category from metadata or name
                metadata = tool_def.get('_metadata', {})
                asset_type = metadata.get('asset_type', 'unknown')

                tool_info = self._parse_tool_definition(
                    tool_def,
                    category=asset_type,
                    source_file="vibey/mcp/discovery/"
                )
                tools.append(tool_info)

            return tools

        except ImportError:
            logger.debug("Dynamic tool discovery not available")
            return []
        except Exception as e:
            self._errors.append(f"Dynamic discovery failed: {e}")
            return []

    def _parse_tool_definition(
        self,
        tool_def: Dict[str, Any],
        category: str,
        source_file: str,
    ) -> ToolInfo:
        """
        Parse a tool definition dict into ToolInfo.

        Args:
            tool_def: Tool definition dictionary
            category: Tool category
            source_file: Source file path

        Returns:
            ToolInfo object.
        """
        name = tool_def.get('name', 'unknown')
        schema = tool_def.get('inputSchema', {})

        # Get predefined examples if available
        examples = TOOL_EXAMPLES.get(name, [])

        return ToolInfo(
            name=name,
            title=tool_def.get('title'),
            description=tool_def.get('description', ''),
            input_schema=self._parse_input_schema(schema),
            category=category,
            examples=examples,
            source_file=source_file,
        )

    def _parse_input_schema(self, schema: Dict[str, Any]) -> InputSchema:
        """
        Parse JSON Schema into InputSchema.

        Args:
            schema: JSON Schema dictionary

        Returns:
            InputSchema object.
        """
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
                minimum=prop_def.get('minimum'),
                maximum=prop_def.get('maximum'),
            ))

        # Sort by required (required first) then name
        properties.sort(key=lambda p: (not p.required, p.name))

        return InputSchema(
            properties=properties,
            required=required_names,
            raw_schema=schema,
        )

    def _introspect_resources(self) -> List[ResourceTemplateInfo]:
        """
        Introspect all MCP resource templates.

        Returns:
            List of ResourceTemplateInfo objects.
        """
        resources = []

        # Resource providers: (module_path, class_name, category)
        providers: List[Tuple[str, str, str]] = [
            ("vibey.mcp.resources.workflows", "WorkflowResourceProvider", "workflows"),
            ("vibey.mcp.resources.handoffs", "HandoffResourceProvider", "handoffs"),
        ]

        for module_path, class_name, category in providers:
            try:
                resources.extend(self._introspect_resource_provider(
                    module_path, class_name, category
                ))
            except Exception as e:
                self._errors.append(f"Resource provider {class_name}: {e}")

        return resources

    def _introspect_resource_provider(
        self,
        module_path: str,
        class_name: str,
        category: str,
    ) -> List[ResourceTemplateInfo]:
        """
        Introspect a resource provider.

        Args:
            module_path: Full module path
            class_name: Provider class name
            category: Resource category

        Returns:
            List of ResourceTemplateInfo from this provider.
        """
        import importlib

        module = importlib.import_module(module_path)
        provider_class = getattr(module, class_name)

        try:
            provider = provider_class(self.content_root)
            templates = provider.get_templates()
        except Exception as e:
            # Provider may need specific paths, try with default
            logger.debug(f"Provider instantiation failed: {e}, using empty templates")
            return []

        resources = []
        for template in templates:
            resources.append(ResourceTemplateInfo(
                uri_template=template.uriTemplate,
                name=template.name,
                description=template.description or "",
                mime_type=template.mimeType or "application/octet-stream",
                provider=class_name,
                category=category,
            ))

        return resources

    def _introspect_prompts(self) -> List[PromptInfo]:
        """
        Introspect all MCP prompts.

        Returns:
            List of PromptInfo objects.
        """
        prompts = []

        # Prompt providers: (module_path, class_name, category)
        providers: List[Tuple[str, str, str]] = [
            ("vibey.mcp.prompts.quality_gates", "QualityGatePromptProvider", "quality_gates"),
        ]

        for module_path, class_name, category in providers:
            try:
                prompts.extend(self._introspect_prompt_provider(
                    module_path, class_name, category
                ))
            except Exception as e:
                self._errors.append(f"Prompt provider {class_name}: {e}")

        return prompts

    def _introspect_prompt_provider(
        self,
        module_path: str,
        class_name: str,
        category: str,
    ) -> List[PromptInfo]:
        """
        Introspect a prompt provider.

        Args:
            module_path: Full module path
            class_name: Provider class name
            category: Prompt category

        Returns:
            List of PromptInfo from this provider.
        """
        import importlib

        module = importlib.import_module(module_path)
        provider_class = getattr(module, class_name)

        try:
            provider = provider_class(self.content_root)
            prompt_defs = provider.get_prompts()
        except Exception as e:
            logger.debug(f"Prompt provider instantiation failed: {e}")
            return []

        prompts = []
        for prompt_def in prompt_defs:
            arguments = [
                PromptArgument(
                    name=arg.name,
                    description=arg.description or "",
                    required=arg.required,
                )
                for arg in prompt_def.arguments
            ]

            prompts.append(PromptInfo(
                name=prompt_def.name,
                description=prompt_def.description or "",
                arguments=arguments,
                category=category,
                provider=class_name,
            ))

        return prompts


# =============================================================================
# Convenience Functions
# =============================================================================


def introspect_mcp(content_root: Optional[Path] = None) -> MCPStructure:
    """
    Introspect the Vibey MCP server.

    This is the main entry point for MCP introspection.

    Args:
        content_root: Root directory for content discovery.
                     Defaults to current working directory.

    Returns:
        MCPStructure containing all tools, resources, and prompts.

    Example:
        >>> structure = introspect_mcp()
        >>> print(f"Total tools: {len(structure.tools)}")
        >>> print(structure.to_json())
    """
    introspector = MCPIntrospector(content_root)
    return introspector.introspect()


def get_tool_count() -> int:
    """Get the total number of MCP tools."""
    structure = introspect_mcp()
    return len(structure.tools)


def get_resource_count() -> int:
    """Get the total number of MCP resource templates."""
    structure = introspect_mcp()
    return len(structure.resources)


def get_prompt_count() -> int:
    """Get the total number of MCP prompts."""
    structure = introspect_mcp()
    return len(structure.prompts)
