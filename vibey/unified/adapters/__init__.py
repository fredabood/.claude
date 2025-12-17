"""
Adapters for generating CLI commands and MCP tools from unified registry.
"""

from .click_adapter import (
    generate_click_command,
    register_unified_commands_to_click,
    get_unified_click_groups,
)

from .mcp_adapter import (
    generate_mcp_tool_definition,
    handle_unified_tool_call,
    get_unified_mcp_tools,
    get_unified_mcp_tools_by_category,
    create_mcp_tool_handler,
)

__all__ = [
    # Click adapter
    "generate_click_command",
    "register_unified_commands_to_click",
    "get_unified_click_groups",
    # MCP adapter
    "generate_mcp_tool_definition",
    "handle_unified_tool_call",
    "get_unified_mcp_tools",
    "get_unified_mcp_tools_by_category",
    "create_mcp_tool_handler",
]
