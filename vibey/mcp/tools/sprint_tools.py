"""
Sprint Management Tools.

MCP tools for managing roadmap sprints (start, complete, refresh progress).
"""

from typing import List, Dict, Any

from ..adapters.roadmap_adapter import RoadmapAdapter
from ..utils.errors import VibeyMCPError
from ..utils.validation import validate_sprint_id


# Tool Definitions

def get_sprint_tools() -> List[Dict[str, Any]]:
    """
    Get sprint management tool definitions.

    Returns:
        List of tool definition dicts following MCP spec
    """
    return [
        {
            "name": "vibey_start_sprint",
            "title": "Start Sprint",
            "description": "Mark a sprint as in progress and set start timestamp",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sprint_id": {
                        "type": "string",
                        "description": "Sprint ID (e.g., 'mcp-server-1')"
                    }
                },
                "required": ["sprint_id"]
            }
        },
        {
            "name": "vibey_complete_sprint",
            "title": "Complete Sprint",
            "description": "Mark a sprint as completed (requires all tasks complete)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sprint_id": {
                        "type": "string",
                        "description": "Sprint ID (e.g., 'mcp-server-1')"
                    }
                },
                "required": ["sprint_id"]
            }
        },
        {
            "name": "vibey_refresh_progress",
            "title": "Refresh Progress",
            "description": "Recalculate all progress metrics and trigger status auto-progression",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "vibey_query_sprint",
            "title": "Query Sprint",
            "description": "Get detailed information about a specific sprint",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sprint_id": {
                        "type": "string",
                        "description": "Sprint ID to query"
                    }
                },
                "required": ["sprint_id"]
            }
        }
    ]


# Tool Handlers

async def handle_sprint_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """
    Handle sprint tool invocation.

    Routes to appropriate handler based on tool name.

    Args:
        tool_name: Name of tool being invoked
        arguments: Tool input arguments
        adapter: Roadmap adapter instance

    Returns:
        MCP tool response dict with content and isError flag
    """
    if tool_name == "vibey_start_sprint":
        return await handle_start_sprint(arguments, adapter)
    elif tool_name == "vibey_complete_sprint":
        return await handle_complete_sprint(arguments, adapter)
    elif tool_name == "vibey_refresh_progress":
        return await handle_refresh_progress(arguments, adapter)
    elif tool_name == "vibey_query_sprint":
        return await handle_query_sprint(arguments, adapter)
    else:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Unknown sprint tool: {tool_name}"
                }
            ],
            "isError": True
        }


async def handle_start_sprint(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """
    Handle vibey_start_sprint tool invocation.

    Args:
        arguments: Tool arguments with sprint_id
        adapter: Roadmap adapter

    Returns:
        MCP tool response
    """
    sprint_id = arguments["sprint_id"]

    try:
        # Validate sprint ID format
        validate_sprint_id(sprint_id)

        # Start sprint via adapter
        result = adapter.start_sprint(sprint_id)

        # Format success response
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"✅ Sprint '{sprint_id}' started successfully\n\n"
                           f"Status: {result['status']}\n"
                           f"Started: {result['started']}"
                }
            ],
            "isError": False
        }

    except VibeyMCPError as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error starting sprint '{sprint_id}': {e.message}"
                }
            ],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Unexpected error starting sprint '{sprint_id}': {str(e)}"
                }
            ],
            "isError": True
        }


async def handle_complete_sprint(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """
    Handle vibey_complete_sprint tool invocation.

    Args:
        arguments: Tool arguments with sprint_id
        adapter: Roadmap adapter

    Returns:
        MCP tool response
    """
    sprint_id = arguments["sprint_id"]

    try:
        # Validate sprint ID format
        validate_sprint_id(sprint_id)

        # Complete sprint via adapter
        result = adapter.complete_sprint(sprint_id)

        # Format success response
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"✅ Sprint '{sprint_id}' completed successfully\n\n"
                           f"Status: {result['status']}\n"
                           f"Completed: {result['completed']}\n"
                           f"Tasks Completed: {result['tasks_completed']}/{result['tasks_total']}"
                }
            ],
            "isError": False
        }

    except VibeyMCPError as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error completing sprint '{sprint_id}': {e.message}"
                }
            ],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Unexpected error completing sprint '{sprint_id}': {str(e)}"
                }
            ],
            "isError": True
        }


async def handle_refresh_progress(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """
    Handle vibey_refresh_progress tool invocation.

    Args:
        arguments: Tool arguments (empty for this tool)
        adapter: Roadmap adapter

    Returns:
        MCP tool response
    """
    try:
        # Refresh progress via adapter
        result = adapter.refresh_progress()

        # Format success response
        text = "✅ Progress refreshed successfully\n\n"

        if result.get('progressions'):
            text += "**Status Progressions:**\n"
            for progression in result['progressions']:
                text += f"- {progression['object_id']}: {progression['from_status']} → {progression['to_status']}\n"

        if result.get('updates'):
            text += f"\n**Updates:**\n"
            text += f"- Sprints updated: {result['updates'].get('sprints', 0)}\n"
            text += f"- Tracks updated: {result['updates'].get('tracks', 0)}\n"

        return {
            "content": [
                {
                    "type": "text",
                    "text": text
                }
            ],
            "isError": False
        }

    except VibeyMCPError as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error refreshing progress: {e.message}"
                }
            ],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Unexpected error refreshing progress: {str(e)}"
                }
            ],
            "isError": True
        }


async def handle_query_sprint(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """
    Handle vibey_query_sprint tool invocation.

    Args:
        arguments: Tool arguments with sprint_id
        adapter: Roadmap adapter

    Returns:
        MCP tool response
    """
    sprint_id = arguments["sprint_id"]

    try:
        # Validate sprint ID format
        validate_sprint_id(sprint_id)

        # Query sprint via adapter
        sprint_info = adapter.query_sprint(sprint_id)

        # Format sprint information
        text = f"🏃 Sprint: {sprint_info['name']}\n\n"
        text += f"**ID:** {sprint_info['id']}\n"
        text += f"**Track:** {sprint_info['track_id']}\n"
        text += f"**Status:** {sprint_info['status']}\n"
        text += f"**Blocked:** {'Yes' if sprint_info['blocked'] else 'No'}\n\n"

        text += "**Timeline:**\n"
        if sprint_info.get('created'):
            text += f"- Created: {sprint_info['created']}\n"
        if sprint_info.get('started'):
            text += f"- Started: {sprint_info['started']}\n"
        if sprint_info.get('completed'):
            text += f"- Completed: {sprint_info['completed']}\n"

        # Progress breakdown
        progress = sprint_info['progress']
        text += "\n**Progress:**\n"
        text += f"- Overall: {progress['completion_percent']}% ({progress['tasks_completed']}/{progress['tasks_total']} tasks)\n"
        text += f"- Development: {progress['development_tasks_completed']}/{progress['development_tasks_total']} tasks\n"

        if progress['completion_gate_tasks_total'] > 0:
            text += f"- Completion Gates: {progress['completion_gate_tasks_completed']}/{progress['completion_gate_tasks_total']} passed\n"

        if progress['production_gate_tasks_total'] > 0:
            text += f"- Production Gates: {progress['production_gate_tasks_completed']}/{progress['production_gate_tasks_total']} passed\n"

        return {
            "content": [
                {
                    "type": "text",
                    "text": text
                }
            ],
            "isError": False
        }

    except VibeyMCPError as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error querying sprint '{sprint_id}': {e.message}"
                }
            ],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Unexpected error querying sprint '{sprint_id}': {str(e)}"
                }
            ],
            "isError": True
        }
