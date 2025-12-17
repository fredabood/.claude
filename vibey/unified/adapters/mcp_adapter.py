"""
MCP adapter for unified commands.

Generates MCP tool definitions and handlers from the unified registry,
enabling automatic MCP tool registration from @unified_command definitions.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..command import CommandSpec, Interface
from ..registry import COMMAND_REGISTRY
from ..types import param_to_json_schema
from ..formatters import DEFAULT_FORMATTER, CommandResult


def generate_mcp_tool_definition(spec: CommandSpec) -> Dict[str, Any]:
    """
    Generate an MCP tool definition from a CommandSpec.

    Creates a tool definition dict with name, description, and inputSchema
    suitable for MCP tool registration.

    Args:
        spec: The command specification

    Returns:
        MCP tool definition dictionary
    """
    # Build input schema properties
    properties: Dict[str, Any] = {}
    required: List[str] = []

    for param in spec.params:
        properties[param.name] = param_to_json_schema(param)
        if param.required and param.default is None:
            required.append(param.name)

    return {
        "name": spec.mcp_tool_name,
        "title": spec.name.replace("_", " ").title(),
        "description": spec.description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
        # Store reference for handler lookup (internal use)
        "_spec": spec,
        "_category": spec.mcp_category,
    }


async def handle_unified_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    root_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Handle an MCP tool call using the unified registry.

    Looks up the command in the registry and executes it with the
    provided arguments, formatting the result for MCP response.

    Args:
        tool_name: The MCP tool name being called
        arguments: The tool arguments
        root_dir: Root directory for operations (defaults to cwd)

    Returns:
        MCP response dict with content and isError fields
    """
    # Find the command spec
    for spec in COMMAND_REGISTRY.list_for_interface(Interface.MCP):
        if spec.mcp_tool_name == tool_name:
            return await _execute_tool(spec, arguments, root_dir)

    # Tool not found
    return {
        "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
        "isError": True,
    }


async def _execute_tool(
    spec: CommandSpec,
    arguments: Dict[str, Any],
    root_dir: Optional[Path],
) -> Dict[str, Any]:
    """
    Execute a tool and format the response.

    Args:
        spec: The command specification
        arguments: The tool arguments
        root_dir: Root directory for operations

    Returns:
        MCP response dict
    """
    try:
        # Add root_dir to arguments
        arguments["root_dir"] = root_dir or Path.cwd()

        # Call the underlying operation
        result = spec.operation(**arguments)

        # Format output for MCP
        formatter = spec.formatter or DEFAULT_FORMATTER

        if isinstance(result, CommandResult):
            text = formatter.format_mcp(result)
            return {
                "content": [{"type": "text", "text": text}],
                "isError": not result.success,
            }
        else:
            # Legacy operations may return other types
            text = str(result) if result is not None else "Operation completed."
            return {
                "content": [{"type": "text", "text": text}],
                "isError": False,
            }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True,
        }


def get_unified_mcp_tools() -> List[Dict[str, Any]]:
    """
    Get all MCP tool definitions from the unified registry.

    Returns:
        List of MCP tool definition dictionaries
    """
    return [
        generate_mcp_tool_definition(spec)
        for spec in COMMAND_REGISTRY.list_for_interface(Interface.MCP)
    ]


def get_unified_mcp_tools_by_category() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get MCP tools organized by category.

    Returns:
        Dictionary mapping category names to lists of tool definitions
    """
    tools_by_category: Dict[str, List[Dict[str, Any]]] = {}

    for spec in COMMAND_REGISTRY.list_for_interface(Interface.MCP):
        tool_def = generate_mcp_tool_definition(spec)
        category = spec.mcp_category or "general"

        if category not in tools_by_category:
            tools_by_category[category] = []
        tools_by_category[category].append(tool_def)

    return tools_by_category


def create_mcp_tool_handler(spec: CommandSpec):
    """
    Create an async handler function for an MCP tool.

    This creates a function suitable for use with FastMCP's @mcp.tool decorator.

    Args:
        spec: The command specification

    Returns:
        Async handler function
    """
    async def handler(**kwargs: Any) -> str:
        """MCP tool handler."""
        root_dir = kwargs.pop("root_dir", None) or Path.cwd()
        result = await _execute_tool(spec, kwargs, root_dir)

        if result["isError"]:
            raise Exception(result["content"][0]["text"])

        return result["content"][0]["text"]

    # Set function metadata
    handler.__name__ = spec.mcp_tool_name
    handler.__doc__ = spec.description

    return handler
