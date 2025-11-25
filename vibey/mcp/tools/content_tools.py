"""
Content Tools.

MCP tools for managing framework content (agents, workflows, templates, handoffs).
"""

from typing import List, Dict, Any, Optional

from vibey.operations.content import (
    ContentType,
    list_content,
    load_content,
    create_content,
    update_content,
    delete_content,
    search_content,
)
from vibey.operations.content.writer import ContentValidator


# Tool Definitions

def get_content_tools() -> List[Dict[str, Any]]:
    """
    Get content tool definitions.

    Returns:
        List of tool definition dicts following MCP spec
    """
    return [
        {
            "name": "vibey_content_list",
            "title": "List Content",
            "description": "List framework content (agents, workflows, templates, handoffs)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "content_type": {
                        "type": "string",
                        "description": "Filter by content type",
                        "enum": ["agent", "workflow", "template", "handoff", "schema", "example"]
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category (subdirectory, e.g., 'core', 'planning')"
                    }
                }
            }
        },
        {
            "name": "vibey_content_show",
            "title": "Show Content",
            "description": "Show details of a specific content item",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "content_id": {
                        "type": "string",
                        "description": "Content ID to show (e.g., 'coordinator', 'sprint-planning')"
                    },
                    "content_type": {
                        "type": "string",
                        "description": "Content type (speeds up lookup)",
                        "enum": ["agent", "workflow", "template", "handoff", "schema", "example"]
                    },
                    "include_body": {
                        "type": "boolean",
                        "description": "Include full body text",
                        "default": False
                    }
                },
                "required": ["content_id"]
            }
        },
        {
            "name": "vibey_content_search",
            "title": "Search Content",
            "description": "Search framework content by keywords",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (keywords)"
                    },
                    "content_type": {
                        "type": "string",
                        "description": "Filter by content type",
                        "enum": ["agent", "workflow", "template", "handoff", "schema", "example"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 20)",
                        "default": 20
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "vibey_content_create",
            "title": "Create Content",
            "description": "Create new framework content (agent, workflow, template, handoff)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "content_type": {
                        "type": "string",
                        "description": "Type of content to create",
                        "enum": ["agent", "workflow", "template", "handoff"]
                    },
                    "content_id": {
                        "type": "string",
                        "description": "ID for the new content (e.g., 'my-agent')"
                    },
                    "name": {
                        "type": "string",
                        "description": "Display name for the content"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category (subdirectory, e.g., 'core', 'planning')"
                    },
                    "subtype": {
                        "type": "string",
                        "description": "Subtype (e.g., 'core', 'development' for agents)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Content description"
                    },
                    "body": {
                        "type": "string",
                        "description": "Body content (markdown)"
                    }
                },
                "required": ["content_type", "content_id", "name"]
            }
        },
        {
            "name": "vibey_content_update",
            "title": "Update Content",
            "description": "Update existing framework content metadata",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "content_id": {
                        "type": "string",
                        "description": "ID of content to update"
                    },
                    "content_type": {
                        "type": "string",
                        "description": "Content type (optional, speeds up lookup)",
                        "enum": ["agent", "workflow", "template", "handoff"]
                    },
                    "updates": {
                        "type": "object",
                        "description": "Field updates (e.g., {'version': '1.1.0', 'type': 'core'})"
                    }
                },
                "required": ["content_id", "updates"]
            }
        },
        {
            "name": "vibey_content_delete",
            "title": "Delete Content",
            "description": "Delete framework content (moves to trash)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "content_id": {
                        "type": "string",
                        "description": "ID of content to delete"
                    },
                    "content_type": {
                        "type": "string",
                        "description": "Content type (optional, speeds up lookup)",
                        "enum": ["agent", "workflow", "template", "handoff"]
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Delete even if referenced by other content",
                        "default": False
                    }
                },
                "required": ["content_id"]
            }
        },
        {
            "name": "vibey_content_validate",
            "title": "Validate Content",
            "description": "Validate content frontmatter",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "content_id": {
                        "type": "string",
                        "description": "ID of specific content to validate (optional)"
                    },
                    "content_type": {
                        "type": "string",
                        "description": "Content type to validate (validates all of this type if no content_id)",
                        "enum": ["agent", "workflow", "template", "handoff"]
                    }
                }
            }
        }
    ]


# Tool Handlers

async def handle_content_tool(
    tool_name: str,
    arguments: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle content tool invocation.

    Routes to appropriate handler based on tool name.

    Args:
        tool_name: Name of tool being invoked
        arguments: Tool input arguments

    Returns:
        MCP tool response dict with content and isError flag
    """
    handlers = {
        "vibey_content_list": handle_content_list,
        "vibey_content_show": handle_content_show,
        "vibey_content_search": handle_content_search,
        "vibey_content_create": handle_content_create,
        "vibey_content_update": handle_content_update,
        "vibey_content_delete": handle_content_delete,
        "vibey_content_validate": handle_content_validate,
    }

    handler = handlers.get(tool_name)
    if handler:
        return await handler(arguments)
    else:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Unknown content tool: {tool_name}"
                }
            ],
            "isError": True
        }


async def handle_content_list(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle vibey_content_list tool invocation."""
    try:
        content_type_str = arguments.get("content_type")
        category = arguments.get("category")

        ctype = ContentType(content_type_str) if content_type_str else None
        items = list_content(ctype, category)

        if not items:
            return {
                "content": [{"type": "text", "text": "No content found"}],
                "isError": False
            }

        # Format as table-like text
        text = f"Content ({len(items)} items)\n\n"
        text += "| Type | Category | ID | Name | Version |\n"
        text += "|------|----------|-----|------|--------|\n"

        for item in sorted(items, key=lambda x: (x.content_type.value, x.category or '', x.id)):
            text += f"| {item.content_type.value} | {item.category or '-'} | {item.id} | {item.name} | {item.metadata.version} |\n"

        return {
            "content": [{"type": "text", "text": text}],
            "isError": False
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error listing content: {e}"}],
            "isError": True
        }


async def handle_content_show(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle vibey_content_show tool invocation."""
    try:
        content_id = arguments["content_id"]
        content_type_str = arguments.get("content_type")
        include_body = arguments.get("include_body", False)

        ctype = ContentType(content_type_str) if content_type_str else None
        item = load_content(content_id, ctype)

        if item is None:
            return {
                "content": [{"type": "text", "text": f"Content not found: {content_id}"}],
                "isError": True
            }

        text = f"# {item.name} ({item.id})\n\n"
        text += f"**Type:** {item.content_type.value}\n"
        text += f"**Category:** {item.category or 'root'}\n"
        text += f"**Version:** {item.metadata.version}\n"
        text += f"**Path:** {item.relative_path}\n"

        if item.metadata.description:
            text += f"\n**Description:**\n{item.metadata.description}\n"

        if item.metadata.tags:
            text += f"\n**Tags:** {', '.join(item.metadata.tags)}\n"

        if item.metadata.extra:
            text += f"\n**Metadata:**\n"
            for key, value in item.metadata.extra.items():
                text += f"- {key}: {value}\n"

        if include_body:
            text += f"\n**Body:**\n```markdown\n{item.body}\n```\n"

        return {
            "content": [{"type": "text", "text": text}],
            "isError": False
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error showing content: {e}"}],
            "isError": True
        }


async def handle_content_search(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle vibey_content_search tool invocation."""
    try:
        query = arguments["query"]
        content_type_str = arguments.get("content_type")
        limit = arguments.get("limit", 20)

        ctype = ContentType(content_type_str) if content_type_str else None
        results = search_content(query, ctype, limit=limit)

        if not results:
            return {
                "content": [{"type": "text", "text": f"No results for '{query}'"}],
                "isError": False
            }

        text = f"Search Results for '{query}' ({len(results)} matches)\n\n"
        text += "| Score | Type | ID | Name | Matched |\n"
        text += "|-------|------|-----|------|--------|\n"

        for result in results:
            text += f"| {result.score:.0f} | {result.item.content_type.value} | {result.item.id} | {result.item.name} | {', '.join(result.matched_fields[:3])} |\n"

        return {
            "content": [{"type": "text", "text": text}],
            "isError": False
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error searching content: {e}"}],
            "isError": True
        }


async def handle_content_create(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle vibey_content_create tool invocation."""
    try:
        content_type_str = arguments["content_type"]
        content_id = arguments["content_id"]
        name = arguments["name"]
        category = arguments.get("category")
        subtype = arguments.get("subtype")
        description = arguments.get("description", "")
        body = arguments.get("body", "")

        ctype = ContentType(content_type_str)

        # Build frontmatter
        frontmatter = {
            "id": content_id,
            "name": name,
            "version": "1.0.0",
        }

        if subtype:
            frontmatter["type"] = subtype
        elif ctype == ContentType.AGENT:
            frontmatter["type"] = "development"
        elif ctype == ContentType.WORKFLOW:
            frontmatter["type"] = "development"

        if description:
            frontmatter["description"] = description

        # Generate default body if not provided
        if not body:
            if ctype == ContentType.AGENT:
                body = f"# {name}\n\n**Role:** [Describe the agent's role]\n\n## Purpose\n\n[Describe what this agent does]\n"
            elif ctype == ContentType.WORKFLOW:
                body = f"# {name}\n\n## Overview\n\n[Describe the workflow]\n\n## Steps\n\n1. [Step 1]\n2. [Step 2]\n"
            else:
                body = f"# {name}\n\n[Content here]\n"

        result = create_content(ctype, frontmatter, body, category)

        if result.success:
            text = f"Created {content_type_str}: {content_id}"
            if result.content:
                text += f"\nPath: {result.content.filepath}"
            return {
                "content": [{"type": "text", "text": text}],
                "isError": False
            }
        else:
            return {
                "content": [{"type": "text", "text": f"Failed to create {content_type_str}: {', '.join(result.errors)}"}],
                "isError": True
            }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error creating content: {e}"}],
            "isError": True
        }


async def handle_content_update(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle vibey_content_update tool invocation."""
    try:
        content_id = arguments["content_id"]
        content_type_str = arguments.get("content_type")
        updates = arguments["updates"]

        ctype = ContentType(content_type_str) if content_type_str else None
        result = update_content(content_id, updates, ctype)

        if result.success:
            text = f"Updated {content_id}"
            if result.backup_path:
                text += f"\nBackup: {result.backup_path}"
            return {
                "content": [{"type": "text", "text": text}],
                "isError": False
            }
        else:
            return {
                "content": [{"type": "text", "text": f"Failed to update {content_id}: {', '.join(result.errors)}"}],
                "isError": True
            }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error updating content: {e}"}],
            "isError": True
        }


async def handle_content_delete(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle vibey_content_delete tool invocation."""
    try:
        content_id = arguments["content_id"]
        content_type_str = arguments.get("content_type")
        force = arguments.get("force", False)

        ctype = ContentType(content_type_str) if content_type_str else None
        result = delete_content(content_id, ctype, force)

        if result.success:
            text = f"Deleted {content_id}"
            if result.backup_path:
                text += f"\nMoved to: {result.backup_path}"
            return {
                "content": [{"type": "text", "text": text}],
                "isError": False
            }
        else:
            return {
                "content": [{"type": "text", "text": f"Failed to delete {content_id}: {', '.join(result.errors)}"}],
                "isError": True
            }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error deleting content: {e}"}],
            "isError": True
        }


async def handle_content_validate(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle vibey_content_validate tool invocation."""
    try:
        content_id = arguments.get("content_id")
        content_type_str = arguments.get("content_type")

        validator = ContentValidator()
        ctype = ContentType(content_type_str) if content_type_str else None

        if content_id:
            # Validate single content
            item = load_content(content_id, ctype)
            if item is None:
                return {
                    "content": [{"type": "text", "text": f"Content not found: {content_id}"}],
                    "isError": True
                }

            result = validator.validate(item.content_type, item._raw_frontmatter, item.body)

            if result.is_valid:
                text = f"{content_id} is valid"
                if result.warnings:
                    text += "\n\nWarnings:\n" + "\n".join(f"- {w}" for w in result.warnings)
            else:
                text = f"{content_id} has errors:\n" + "\n".join(f"- {e}" for e in result.errors)

            return {
                "content": [{"type": "text", "text": text}],
                "isError": not result.is_valid
            }
        else:
            # Validate all content of type
            items = list_content(ctype)
            if not items:
                return {
                    "content": [{"type": "text", "text": "No content to validate"}],
                    "isError": False
                }

            valid_count = 0
            invalid_count = 0
            errors_by_item = {}

            for item in items:
                result = validator.validate(item.content_type, item._raw_frontmatter, item.body)
                if result.is_valid:
                    valid_count += 1
                else:
                    invalid_count += 1
                    errors_by_item[item.id] = result.errors

            text = f"Validation Results\n\nValid: {valid_count}\nInvalid: {invalid_count}\nTotal: {len(items)}"

            if errors_by_item:
                text += "\n\nItems with errors:\n"
                for item_id, errors in list(errors_by_item.items())[:10]:
                    text += f"\n{item_id}:\n" + "\n".join(f"  - {e}" for e in errors[:3])

            return {
                "content": [{"type": "text", "text": text}],
                "isError": invalid_count > 0
            }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error validating content: {e}"}],
            "isError": True
        }
