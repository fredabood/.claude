"""
Query Tools.

MCP tools for querying roadmap state (track, blockers, dependencies).
"""

from typing import List, Dict, Any

from ..adapters.roadmap_adapter import RoadmapAdapter
from ..utils.errors import VibeyMCPError
from ..utils.validation import validate_track_id


# Tool Definitions

def get_query_tools() -> List[Dict[str, Any]]:
    """
    Get query tool definitions.

    Returns:
        List of tool definition dicts following MCP spec
    """
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
        {
            "name": "vibey_list_blockers",
            "title": "List Blockers",
            "description": "List all current blockers across the roadmap or for a specific object",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "object_id": {
                        "type": "string",
                        "description": "Optional: filter by specific object ID (track, sprint, or task)"
                    }
                }
            }
        },
        {
            "name": "vibey_list_dependencies",
            "title": "List Dependencies",
            "description": "List dependencies for a specific object",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "object_id": {
                        "type": "string",
                        "description": "Object ID to query dependencies for"
                    },
                    "include_satisfied": {
                        "type": "boolean",
                        "description": "Include satisfied dependencies (default: false)",
                        "default": False
                    }
                },
                "required": ["object_id"]
            }
        },
        {
            "name": "vibey_roadmap_status",
            "title": "Roadmap Status",
            "description": "Get overall roadmap status summary",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    ]


# Tool Handlers

async def handle_query_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """
    Handle query tool invocation.

    Routes to appropriate handler based on tool name.

    Args:
        tool_name: Name of tool being invoked
        arguments: Tool input arguments
        adapter: Roadmap adapter instance

    Returns:
        MCP tool response dict with content and isError flag
    """
    if tool_name == "vibey_query_track":
        return await handle_query_track(arguments, adapter)
    elif tool_name == "vibey_list_blockers":
        return await handle_list_blockers(arguments, adapter)
    elif tool_name == "vibey_list_dependencies":
        return await handle_list_dependencies(arguments, adapter)
    elif tool_name == "vibey_roadmap_status":
        return await handle_roadmap_status(arguments, adapter)
    else:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Unknown query tool: {tool_name}"
                }
            ],
            "isError": True
        }


async def handle_query_track(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """
    Handle vibey_query_track tool invocation.

    Args:
        arguments: Tool arguments with track_id
        adapter: Roadmap adapter

    Returns:
        MCP tool response
    """
    track_id = arguments["track_id"]

    try:
        # Validate track ID format
        validate_track_id(track_id)

        # Query track via adapter
        track_info = adapter.query_track(track_id)

        # Format track information
        text = f"🛤️  Track: {track_info['name']}\n\n"
        text += f"**ID:** {track_info['id']}\n"
        text += f"**Status:** {track_info['status']}\n"
        text += f"**Priority:** {track_info.get('priority', 'N/A')}\n"
        text += f"**Blocked:** {'Yes' if track_info['blocked'] else 'No'}\n\n"

        text += "**Timeline:**\n"
        if track_info.get('created'):
            text += f"- Created: {track_info['created']}\n"
        if track_info.get('started'):
            text += f"- Started: {track_info['started']}\n"
        if track_info.get('completed'):
            text += f"- Completed: {track_info['completed']}\n"
        if track_info.get('estimated_duration'):
            text += f"- Estimated Duration: {track_info['estimated_duration']}\n"

        # Progress breakdown - operations library returns string format
        progress = track_info['progress']
        text += "\n**Progress:**\n"
        text += f"- Overall: {progress.get('completion', 'N/A')} ({progress.get('tasks', 'N/A')} tasks)\n"
        text += f"- Sprints: {progress.get('sprints', 'N/A')} complete\n"

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
                    "text": f"❌ Error querying track '{track_id}': {e.message}"
                }
            ],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Unexpected error querying track '{track_id}': {str(e)}"
                }
            ],
            "isError": True
        }


async def handle_list_blockers(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """
    Handle vibey_list_blockers tool invocation.

    Args:
        arguments: Tool arguments with optional object_id
        adapter: Roadmap adapter

    Returns:
        MCP tool response
    """
    object_id = arguments.get("object_id")

    try:
        # List blockers via adapter
        blockers = adapter.list_blockers(object_id)

        if not blockers:
            text = "✅ No blockers found"
            if object_id:
                text += f" for '{object_id}'"
            text += "!"
        else:
            text = f"🚧 Blockers ({len(blockers)} found)\n\n"

            for blocker in blockers:
                text += f"**{blocker['blocked_object_id']}** is blocked by:\n"
                text += f"- Dependency: {blocker['dependency_id']} ({blocker['dependency_type']})\n"
                text += f"- Current Status: {blocker['current_status']}\n"
                text += f"- Required Status: {blocker['required_status']}\n"
                if blocker.get('blocking_since'):
                    text += f"- Blocking Since: {blocker['blocking_since']}\n"
                text += "\n"

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
                    "text": f"❌ Error listing blockers: {e.message}"
                }
            ],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Unexpected error listing blockers: {str(e)}"
                }
            ],
            "isError": True
        }


async def handle_list_dependencies(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """
    Handle vibey_list_dependencies tool invocation.

    Args:
        arguments: Tool arguments with object_id and include_satisfied
        adapter: Roadmap adapter

    Returns:
        MCP tool response
    """
    object_id = arguments["object_id"]
    include_satisfied = arguments.get("include_satisfied", False)

    try:
        # List dependencies via adapter
        dependencies = adapter.list_dependencies(object_id, include_satisfied)

        if not dependencies:
            text = f"ℹ️  No dependencies found for '{object_id}'"
        else:
            text = f"🔗 Dependencies for '{object_id}' ({len(dependencies)} found)\n\n"

            for dep in dependencies:
                satisfied = dep.get('is_satisfied', False)
                icon = "✅" if satisfied else "⏳"

                text += f"{icon} **{dep['dependency_id']}** ({dep['dependency_type']})\n"
                text += f"- Current Status: {dep['current_status']}\n"
                text += f"- Required Status: {dep['required_status']}\n"
                text += f"- Satisfied: {'Yes' if satisfied else 'No'}\n"
                if dep.get('reason'):
                    text += f"- Reason: {dep['reason']}\n"
                text += "\n"

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
                    "text": f"❌ Error listing dependencies for '{object_id}': {e.message}"
                }
            ],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Unexpected error listing dependencies: {str(e)}"
                }
            ],
            "isError": True
        }


async def handle_roadmap_status(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """
    Handle vibey_roadmap_status tool invocation.

    Args:
        arguments: Tool arguments (empty for this tool)
        adapter: Roadmap adapter

    Returns:
        MCP tool response
    """
    try:
        # Get roadmap status via adapter
        status = adapter.get_roadmap_status()

        # Format roadmap status
        text = f"📊 Roadmap: {status['name']}\n\n"
        text += f"**Version:** {status['version']}\n"
        text += f"**Status:** {status['status']}\n"
        text += f"**Blocked:** {'Yes' if status.get('blocked') else 'No'}\n\n"

        # Progress - operations library returns string format (e.g., "13/20", "94%")
        progress = status['progress']
        text += "**Overall Progress:**\n"
        text += f"- Completion: {progress.get('completion', 'N/A')}\n"
        text += f"- Tracks: {progress.get('tracks', 'N/A')} complete\n"
        text += f"- Sprints: {progress.get('sprints', 'N/A')} complete\n"
        text += f"- Tasks: {progress.get('tasks', 'N/A')} complete\n\n"

        # Active tracks summary
        if status.get('tracks'):
            in_progress = [t for t in status['tracks'] if t['status'] == 'in_progress']
            if in_progress:
                text += "**Active Tracks:**\n"
                for track in in_progress:
                    text += f"- {track['id']}: {track['name']}\n"
                text += "\n"

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
                    "text": f"❌ Error getting roadmap status: {e.message}"
                }
            ],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Unexpected error getting roadmap status: {str(e)}"
                }
            ],
            "isError": True
        }
