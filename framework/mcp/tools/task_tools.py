"""
Task Management Tools.

MCP tools for managing roadmap tasks (start, complete, query).
"""

from typing import List, Dict, Any

from ..adapters.roadmap_adapter import RoadmapAdapter
from ..utils.errors import VibeyMCPError
from ..utils.validation import validate_task_id


# Tool Definitions

def get_task_tools() -> List[Dict[str, Any]]:
    """
    Get task management tool definitions.

    Returns:
        List of tool definition dicts following MCP spec
    """
    return [
        {
            "name": "vibey_start_task",
            "title": "Start Task",
            "description": "Mark a task as in progress and set start timestamp",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID (e.g., 'mcp-server-1-task-001')"
                    }
                },
                "required": ["task_id"]
            }
        },
        {
            "name": "vibey_complete_task",
            "title": "Complete Task",
            "description": "Mark a task as completed and set completion timestamp",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID (e.g., 'mcp-server-1-task-001')"
                    },
                    "actual_tokens": {
                        "type": "integer",
                        "description": "Actual tokens used (optional)",
                        "minimum": 0
                    }
                },
                "required": ["task_id"]
            }
        },
        {
            "name": "vibey_query_task",
            "title": "Query Task",
            "description": "Get detailed information about a specific task",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to query"
                    }
                },
                "required": ["task_id"]
            }
        }
    ]


# Tool Handlers

async def handle_task_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """
    Handle task tool invocation.

    Routes to appropriate handler based on tool name.

    Args:
        tool_name: Name of tool being invoked
        arguments: Tool input arguments
        adapter: Roadmap adapter instance

    Returns:
        MCP tool response dict with content and isError flag

    Example:
        >>> adapter = RoadmapAdapter()
        >>> result = await handle_task_tool(
        ...     "vibey_start_task",
        ...     {"task_id": "mcp-server-1-task-001"},
        ...     adapter
        ... )
    """
    if tool_name == "vibey_start_task":
        return await handle_start_task(arguments, adapter)
    elif tool_name == "vibey_complete_task":
        return await handle_complete_task(arguments, adapter)
    elif tool_name == "vibey_query_task":
        return await handle_query_task(arguments, adapter)
    else:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Unknown task tool: {tool_name}"
                }
            ],
            "isError": True
        }


async def handle_start_task(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """
    Handle vibey_start_task tool invocation.

    Args:
        arguments: Tool arguments with task_id
        adapter: Roadmap adapter

    Returns:
        MCP tool response
    """
    task_id = arguments["task_id"]

    try:
        # Validate task ID format
        validate_task_id(task_id)

        # Start task via adapter
        result = adapter.start_task(task_id)

        # Format success response
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"✅ Task '{task_id}' started successfully\n\n"
                           f"Status: {result['status']}\n"
                           f"Started: {result['started']}"
                }
            ],
            "isError": False
        }

    except VibeyMCPError as e:
        # Handle known errors
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error starting task '{task_id}': {e.message}"
                }
            ],
            "isError": True
        }
    except Exception as e:
        # Handle unexpected errors
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Unexpected error starting task '{task_id}': {str(e)}"
                }
            ],
            "isError": True
        }


async def handle_complete_task(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """
    Handle vibey_complete_task tool invocation.

    Args:
        arguments: Tool arguments with task_id and optional actual_tokens
        adapter: Roadmap adapter

    Returns:
        MCP tool response
    """
    task_id = arguments["task_id"]
    actual_tokens = arguments.get("actual_tokens")

    try:
        # Validate task ID format
        validate_task_id(task_id)

        # Complete task via adapter
        result = adapter.complete_task(task_id, actual_tokens)

        # Format success response
        if result.get("already_completed"):
            text = f"ℹ️  Task '{task_id}' was already completed\n\n" \
                   f"Status: {result['status']}"
        else:
            text = f"✅ Task '{task_id}' completed successfully\n\n" \
                   f"Status: {result['status']}\n" \
                   f"Completed: {result['completed']}"

            if result.get("actual_tokens"):
                text += f"\nActual Tokens: {result['actual_tokens']}"

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
        # Handle known errors
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error completing task '{task_id}': {e.message}"
                }
            ],
            "isError": True
        }
    except Exception as e:
        # Handle unexpected errors
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Unexpected error completing task '{task_id}': {str(e)}"
                }
            ],
            "isError": True
        }


async def handle_query_task(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """
    Handle vibey_query_task tool invocation.

    Args:
        arguments: Tool arguments with task_id
        adapter: Roadmap adapter

    Returns:
        MCP tool response
    """
    task_id = arguments["task_id"]

    try:
        # Validate task ID format
        validate_task_id(task_id)

        # Query task via adapter
        task_info = adapter.query_task(task_id)

        # Format task information
        text = f"📋 Task: {task_info['title']}\n\n"
        text += f"**ID:** {task_info['id']}\n"
        text += f"**Sprint:** {task_info['sprint_id']}\n"
        text += f"**Track:** {task_info['track_id']}\n"
        text += f"**Type:** {task_info['task_type']}\n"
        text += f"**Status:** {task_info['status']}\n"
        text += f"**Blocked:** {'Yes' if task_info['blocked'] else 'No'}\n\n"

        if task_info.get('description'):
            text += f"**Description:**\n{task_info['description']}\n\n"

        text += "**Timeline:**\n"
        if task_info.get('created'):
            text += f"- Created: {task_info['created']}\n"
        if task_info.get('started'):
            text += f"- Started: {task_info['started']}\n"
        if task_info.get('completed'):
            text += f"- Completed: {task_info['completed']}\n"

        text += "\n**Metadata:**\n"
        if task_info.get('assigned_agent'):
            text += f"- Agent: {task_info['assigned_agent']}\n"
        if task_info.get('priority'):
            text += f"- Priority: {task_info['priority']}\n"
        if task_info.get('complexity'):
            text += f"- Complexity: {task_info['complexity']}\n"
        if task_info.get('estimated_tokens'):
            text += f"- Estimated Tokens: {task_info['estimated_tokens']}\n"
        if task_info.get('actual_tokens'):
            text += f"- Actual Tokens: {task_info['actual_tokens']}\n"

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
        # Handle known errors
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error querying task '{task_id}': {e.message}"
                }
            ],
            "isError": True
        }
    except Exception as e:
        # Handle unexpected errors
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Unexpected error querying task '{task_id}': {str(e)}"
                }
            ],
            "isError": True
        }
