"""
Token Metrics Tools.

MCP tools for querying and managing token metrics across the roadmap.
Provides tools for:
- Querying token estimates, budgets, and usage
- Updating token estimates and budgets
- Recording token usage
- Running estimation algorithms
- Generating token usage reports

Sprint 4: CLI & Reporting - Token Estimation System
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..adapters.roadmap_adapter import RoadmapAdapter
from ..utils.errors import TaskNotFoundError, SprintNotFoundError, TrackNotFoundError, VibeyMCPError


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================


def get_token_tools() -> List[Dict[str, Any]]:
    """
    Get token metrics tool definitions.

    Returns:
        List of tool definition dicts following MCP spec
    """
    return [
        # -----------------------------------------------------------------
        # Query Tools
        # -----------------------------------------------------------------
        {
            "name": "vibey_get_task_tokens",
            "title": "Get Task Tokens",
            "description": "Get token estimates, budgets, and usage for a specific task",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID (ULID format)"
                    }
                },
                "required": ["task_id"]
            }
        },
        {
            "name": "vibey_get_sprint_token_summary",
            "title": "Get Sprint Token Summary",
            "description": "Get aggregated token metrics for all tasks in a sprint",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sprint_id": {
                        "type": "string",
                        "description": "Sprint ID (ULID format)"
                    }
                },
                "required": ["sprint_id"]
            }
        },
        {
            "name": "vibey_get_track_token_summary",
            "title": "Get Track Token Summary",
            "description": "Get aggregated token metrics for all tasks across all sprints in a track",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "track_id": {
                        "type": "string",
                        "description": "Track ID (ULID format)"
                    }
                },
                "required": ["track_id"]
            }
        },
        {
            "name": "vibey_get_remaining_budget",
            "title": "Get Remaining Budget",
            "description": "Calculate remaining token budget for a task based on usage",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID (ULID format)"
                    }
                },
                "required": ["task_id"]
            }
        },
        # -----------------------------------------------------------------
        # Update Tools
        # -----------------------------------------------------------------
        {
            "name": "vibey_set_task_token_estimate",
            "title": "Set Task Token Estimate",
            "description": "Set the token estimate (min/max/target) for a task's input or output",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID (ULID format)"
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["input", "output"],
                        "description": "Token direction (input or output)"
                    },
                    "min": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Minimum expected tokens"
                    },
                    "max": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Maximum expected tokens"
                    },
                    "target": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Target token count"
                    }
                },
                "required": ["task_id", "direction", "min", "max", "target"]
            }
        },
        {
            "name": "vibey_set_task_token_budget",
            "title": "Set Task Token Budget",
            "description": "Set token budgets for a task",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID (ULID format)"
                    },
                    "input_budget": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Input token budget"
                    },
                    "output_budget": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Output token budget"
                    },
                    "total_budget": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Total token budget (optional override)"
                    }
                },
                "required": ["task_id"]
            }
        },
        {
            "name": "vibey_record_token_usage",
            "title": "Record Token Usage",
            "description": "Record token usage for a task (adds to existing usage)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID (ULID format)"
                    },
                    "input_tokens": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Input tokens to add"
                    },
                    "output_tokens": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Output tokens to add"
                    }
                },
                "required": ["task_id", "input_tokens", "output_tokens"]
            }
        },
        # -----------------------------------------------------------------
        # Estimation Tools
        # -----------------------------------------------------------------
        {
            "name": "vibey_estimate_task_tokens",
            "title": "Estimate Task Tokens",
            "description": "Run token estimation algorithm for an existing task based on its metadata",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID (ULID format)"
                    },
                    "apply": {
                        "type": "boolean",
                        "description": "Apply the estimate to the task (default: false, just preview)",
                        "default": False
                    }
                },
                "required": ["task_id"]
            }
        },
        {
            "name": "vibey_estimate_from_description",
            "title": "Estimate From Description",
            "description": "Estimate tokens from a description without requiring an existing task",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Task description text"
                    },
                    "task_type": {
                        "type": "string",
                        "enum": ["development", "documentation", "testing", "research", "review", "infrastructure", "design", "gate"],
                        "description": "Type of task",
                        "default": "development"
                    },
                    "complexity": {
                        "type": "string",
                        "enum": ["simple", "low", "medium", "complex", "high", "very_complex", "critical"],
                        "description": "Task complexity level",
                        "default": "medium"
                    }
                },
                "required": ["description"]
            }
        },
        # -----------------------------------------------------------------
        # Report Tools
        # -----------------------------------------------------------------
        {
            "name": "vibey_get_token_usage_report",
            "title": "Get Token Usage Report",
            "description": "Generate a token usage report for a track, sprint, or the entire roadmap",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "track_id": {
                        "type": "string",
                        "description": "Filter by track ID (optional)"
                    },
                    "sprint_id": {
                        "type": "string",
                        "description": "Filter by sprint ID (optional)"
                    },
                    "include_completed": {
                        "type": "boolean",
                        "description": "Include completed tasks in report",
                        "default": True
                    },
                    "include_in_progress": {
                        "type": "boolean",
                        "description": "Include in-progress tasks in report",
                        "default": True
                    }
                }
            }
        }
    ]


# =============================================================================
# TOOL HANDLERS
# =============================================================================


async def handle_token_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """
    Handle token tool invocation.

    Routes to appropriate handler based on tool name.

    Args:
        tool_name: Name of tool being invoked
        arguments: Tool input arguments
        adapter: Roadmap adapter instance

    Returns:
        MCP tool response dict with content and isError flag
    """
    handlers = {
        # Query tools
        "vibey_get_task_tokens": handle_get_task_tokens,
        "vibey_get_sprint_token_summary": handle_get_sprint_token_summary,
        "vibey_get_track_token_summary": handle_get_track_token_summary,
        "vibey_get_remaining_budget": handle_get_remaining_budget,
        # Update tools
        "vibey_set_task_token_estimate": handle_set_task_token_estimate,
        "vibey_set_task_token_budget": handle_set_task_token_budget,
        "vibey_record_token_usage": handle_record_token_usage,
        # Estimation tools
        "vibey_estimate_task_tokens": handle_estimate_task_tokens,
        "vibey_estimate_from_description": handle_estimate_from_description,
        # Report tools
        "vibey_get_token_usage_report": handle_get_token_usage_report,
    }

    handler = handlers.get(tool_name)
    if handler:
        return await handler(arguments, adapter)

    return {
        "content": [
            {
                "type": "text",
                "text": f"Unknown token tool: {tool_name}"
            }
        ],
        "isError": True
    }


# =============================================================================
# QUERY HANDLERS
# =============================================================================


async def handle_get_task_tokens(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """Get token information for a specific task."""
    task_id = arguments["task_id"]

    try:
        task_info = adapter.query_task(task_id)

        # Extract token data from task
        tokens_data = _extract_token_data_from_task(task_info)

        # Format response
        text = f"Token Information for Task: {task_info.get('title', task_id)}\n"
        text += f"ID: {task_id}\n\n"

        # Input tokens
        text += "**Input Tokens:**\n"
        input_tokens = tokens_data.get("input_tokens", {})
        text += _format_tokens_section(input_tokens)

        # Output tokens
        text += "\n**Output Tokens:**\n"
        output_tokens = tokens_data.get("output_tokens", {})
        text += _format_tokens_section(output_tokens)

        # Total budget
        if tokens_data.get("total_budget"):
            text += f"\n**Total Budget:** {tokens_data['total_budget']:,} tokens\n"

        return {
            "content": [{"type": "text", "text": text}],
            "isError": False
        }

    except TaskNotFoundError:
        return {
            "content": [{"type": "text", "text": f"Task not found: {task_id}"}],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error getting task tokens: {str(e)}"}],
            "isError": True
        }


async def handle_get_sprint_token_summary(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """Get aggregated token summary for a sprint."""
    sprint_id = arguments["sprint_id"]

    try:
        sprint_info = adapter.query_sprint(sprint_id)
        tasks = _get_sprint_tasks(adapter, sprint_id)

        # Aggregate token data
        summary = _aggregate_token_data(tasks)

        text = f"Token Summary for Sprint: {sprint_info.get('name', sprint_id)}\n"
        text += f"ID: {sprint_id}\n"
        text += f"Status: {sprint_info.get('status', 'unknown')}\n"
        text += f"Tasks: {len(tasks)}\n\n"

        text += _format_token_summary(summary)

        return {
            "content": [{"type": "text", "text": text}],
            "isError": False
        }

    except SprintNotFoundError:
        return {
            "content": [{"type": "text", "text": f"Sprint not found: {sprint_id}"}],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error getting sprint token summary: {str(e)}"}],
            "isError": True
        }


async def handle_get_track_token_summary(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """Get aggregated token summary for a track."""
    track_id = arguments["track_id"]

    try:
        track_info = adapter.query_track(track_id)
        tasks = _get_track_tasks(adapter, track_id)

        # Aggregate token data
        summary = _aggregate_token_data(tasks)

        text = f"Token Summary for Track: {track_info.get('name', track_id)}\n"
        text += f"ID: {track_id}\n"
        text += f"Status: {track_info.get('status', 'unknown')}\n"
        text += f"Tasks: {len(tasks)}\n\n"

        text += _format_token_summary(summary)

        return {
            "content": [{"type": "text", "text": text}],
            "isError": False
        }

    except TrackNotFoundError:
        return {
            "content": [{"type": "text", "text": f"Track not found: {track_id}"}],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error getting track token summary: {str(e)}"}],
            "isError": True
        }


async def handle_get_remaining_budget(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """Calculate remaining token budget for a task."""
    task_id = arguments["task_id"]

    try:
        task_info = adapter.query_task(task_id)
        tokens_data = _extract_token_data_from_task(task_info)

        remaining = {
            "input": None,
            "output": None,
            "total": None
        }

        # Calculate input remaining
        input_tokens = tokens_data.get("input_tokens", {})
        if input_tokens.get("budget") is not None:
            usage = input_tokens.get("usage", 0) or 0
            remaining["input"] = input_tokens["budget"] - usage

        # Calculate output remaining
        output_tokens = tokens_data.get("output_tokens", {})
        if output_tokens.get("budget") is not None:
            usage = output_tokens.get("usage", 0) or 0
            remaining["output"] = output_tokens["budget"] - usage

        # Calculate total remaining
        if tokens_data.get("total_budget") is not None:
            total_usage = (
                (input_tokens.get("usage") or 0) +
                (output_tokens.get("usage") or 0)
            )
            remaining["total"] = tokens_data["total_budget"] - total_usage

        text = f"Remaining Budget for Task: {task_info.get('title', task_id)}\n"
        text += f"ID: {task_id}\n\n"

        if remaining["input"] is not None:
            text += f"**Input Remaining:** {remaining['input']:,} tokens\n"
        else:
            text += "**Input Remaining:** No budget set\n"

        if remaining["output"] is not None:
            text += f"**Output Remaining:** {remaining['output']:,} tokens\n"
        else:
            text += "**Output Remaining:** No budget set\n"

        if remaining["total"] is not None:
            text += f"**Total Remaining:** {remaining['total']:,} tokens\n"
        else:
            text += "**Total Remaining:** No total budget set\n"

        # Warning if over budget
        for key, value in remaining.items():
            if value is not None and value < 0:
                text += f"\nWARNING: {key.title()} budget exceeded by {abs(value):,} tokens!\n"

        return {
            "content": [{"type": "text", "text": text}],
            "isError": False
        }

    except TaskNotFoundError:
        return {
            "content": [{"type": "text", "text": f"Task not found: {task_id}"}],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error getting remaining budget: {str(e)}"}],
            "isError": True
        }


# =============================================================================
# UPDATE HANDLERS
# =============================================================================


async def handle_set_task_token_estimate(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """Set token estimate for a task."""
    task_id = arguments["task_id"]
    direction = arguments["direction"]
    min_tokens = arguments["min"]
    max_tokens = arguments["max"]
    target = arguments["target"]

    try:
        # Validate min <= target <= max
        if not (min_tokens <= target <= max_tokens):
            return {
                "content": [{
                    "type": "text",
                    "text": f"Invalid estimate range: min ({min_tokens}) <= target ({target}) <= max ({max_tokens}) must hold"
                }],
                "isError": True
            }

        # Load and update the task YAML
        result = _update_task_token_estimate(
            adapter.root,
            task_id,
            direction,
            min_tokens,
            max_tokens,
            target
        )

        if result.get("error"):
            return {
                "content": [{"type": "text", "text": result["error"]}],
                "isError": True
            }

        text = f"Updated {direction} token estimate for task {task_id}\n\n"
        text += f"**Min:** {min_tokens:,} tokens\n"
        text += f"**Target:** {target:,} tokens\n"
        text += f"**Max:** {max_tokens:,} tokens\n"

        return {
            "content": [{"type": "text", "text": text}],
            "isError": False
        }

    except TaskNotFoundError:
        return {
            "content": [{"type": "text", "text": f"Task not found: {task_id}"}],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error setting token estimate: {str(e)}"}],
            "isError": True
        }


async def handle_set_task_token_budget(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """Set token budgets for a task."""
    task_id = arguments["task_id"]
    input_budget = arguments.get("input_budget")
    output_budget = arguments.get("output_budget")
    total_budget = arguments.get("total_budget")

    try:
        result = _update_task_token_budget(
            adapter.root,
            task_id,
            input_budget,
            output_budget,
            total_budget
        )

        if result.get("error"):
            return {
                "content": [{"type": "text", "text": result["error"]}],
                "isError": True
            }

        text = f"Updated token budgets for task {task_id}\n\n"
        if input_budget is not None:
            text += f"**Input Budget:** {input_budget:,} tokens\n"
        if output_budget is not None:
            text += f"**Output Budget:** {output_budget:,} tokens\n"
        if total_budget is not None:
            text += f"**Total Budget:** {total_budget:,} tokens\n"

        return {
            "content": [{"type": "text", "text": text}],
            "isError": False
        }

    except TaskNotFoundError:
        return {
            "content": [{"type": "text", "text": f"Task not found: {task_id}"}],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error setting token budget: {str(e)}"}],
            "isError": True
        }


async def handle_record_token_usage(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """Record token usage for a task (adds to existing)."""
    task_id = arguments["task_id"]
    input_tokens = arguments["input_tokens"]
    output_tokens = arguments["output_tokens"]

    try:
        result = _add_task_token_usage(
            adapter.root,
            task_id,
            input_tokens,
            output_tokens
        )

        if result.get("error"):
            return {
                "content": [{"type": "text", "text": result["error"]}],
                "isError": True
            }

        text = f"Recorded token usage for task {task_id}\n\n"
        text += f"**Added Input:** {input_tokens:,} tokens\n"
        text += f"**Added Output:** {output_tokens:,} tokens\n"
        text += f"**Total Added:** {input_tokens + output_tokens:,} tokens\n\n"
        text += f"**New Input Total:** {result.get('new_input_usage', 0):,} tokens\n"
        text += f"**New Output Total:** {result.get('new_output_usage', 0):,} tokens\n"

        return {
            "content": [{"type": "text", "text": text}],
            "isError": False
        }

    except TaskNotFoundError:
        return {
            "content": [{"type": "text", "text": f"Task not found: {task_id}"}],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error recording token usage: {str(e)}"}],
            "isError": True
        }


# =============================================================================
# ESTIMATION HANDLERS
# =============================================================================


async def handle_estimate_task_tokens(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """Run token estimation for an existing task."""
    task_id = arguments["task_id"]
    apply_estimate = arguments.get("apply", False)

    try:
        # Import the token estimator
        from vibey.services.token_estimator import TokenEstimator, EstimationResult

        task_info = adapter.query_task(task_id)

        # Create estimator
        estimator = TokenEstimator()

        # Get task details
        description = task_info.get("description", "")
        task_type = task_info.get("task_type", "development")
        complexity = task_info.get("complexity", "medium")

        # Run estimation
        result = estimator.estimate_from_description(
            description=description,
            task_type=task_type,
            complexity=complexity
        )

        # Apply if requested
        if apply_estimate:
            _update_task_token_estimate(
                adapter.root, task_id, "input",
                result.input_estimate.min or 0,
                result.input_estimate.max or 0,
                result.input_estimate.target or 0
            )
            _update_task_token_estimate(
                adapter.root, task_id, "output",
                result.output_estimate.min or 0,
                result.output_estimate.max or 0,
                result.output_estimate.target or 0
            )

        # Format response
        text = f"Token Estimation for Task: {task_info.get('title', task_id)}\n\n"
        text += f"**Task Type:** {task_type}\n"
        text += f"**Complexity:** {complexity}\n"
        text += f"**Confidence:** {result.confidence:.0%} ({result.confidence_label})\n\n"

        text += "**Input Estimate:**\n"
        text += f"  - Min: {result.input_estimate.min:,} tokens\n"
        text += f"  - Target: {result.input_estimate.target:,} tokens\n"
        text += f"  - Max: {result.input_estimate.max:,} tokens\n\n"

        text += "**Output Estimate:**\n"
        text += f"  - Min: {result.output_estimate.min:,} tokens\n"
        text += f"  - Target: {result.output_estimate.target:,} tokens\n"
        text += f"  - Max: {result.output_estimate.max:,} tokens\n\n"

        total = result.total_estimate
        text += "**Total Estimate:**\n"
        text += f"  - Min: {total.min:,} tokens\n"
        text += f"  - Target: {total.target:,} tokens\n"
        text += f"  - Max: {total.max:,} tokens\n"

        if apply_estimate:
            text += "\nEstimates have been applied to the task."
        else:
            text += "\n(Preview only - use apply=true to save these estimates)"

        return {
            "content": [{"type": "text", "text": text}],
            "isError": False
        }

    except TaskNotFoundError:
        return {
            "content": [{"type": "text", "text": f"Task not found: {task_id}"}],
            "isError": True
        }
    except ImportError:
        return {
            "content": [{
                "type": "text",
                "text": "Token estimation service not available. Check that vibey.services.token_estimator is installed."
            }],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error estimating task tokens: {str(e)}"}],
            "isError": True
        }


async def handle_estimate_from_description(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """Estimate tokens from a description without requiring an existing task."""
    description = arguments["description"]
    task_type = arguments.get("task_type", "development")
    complexity = arguments.get("complexity", "medium")

    try:
        from vibey.services.token_estimator import TokenEstimator

        estimator = TokenEstimator()
        result = estimator.estimate_from_description(
            description=description,
            task_type=task_type,
            complexity=complexity
        )

        # Format response
        text = f"Token Estimation from Description\n\n"
        text += f"**Task Type:** {task_type}\n"
        text += f"**Complexity:** {complexity}\n"
        text += f"**Confidence:** {result.confidence:.0%} ({result.confidence_label})\n"
        text += f"**Description Factor:** {result.description_factor:.2f}x\n\n"

        text += "**Input Estimate:**\n"
        text += f"  - Min: {result.input_estimate.min:,} tokens\n"
        text += f"  - Target: {result.input_estimate.target:,} tokens\n"
        text += f"  - Max: {result.input_estimate.max:,} tokens\n\n"

        text += "**Output Estimate:**\n"
        text += f"  - Min: {result.output_estimate.min:,} tokens\n"
        text += f"  - Target: {result.output_estimate.target:,} tokens\n"
        text += f"  - Max: {result.output_estimate.max:,} tokens\n\n"

        total = result.total_estimate
        text += "**Total Estimate:**\n"
        text += f"  - Min: {total.min:,} tokens\n"
        text += f"  - Target: {total.target:,} tokens\n"
        text += f"  - Max: {total.max:,} tokens\n"

        if result.calibration_applied:
            text += f"\n(Calibration applied: input={result.calibration_input_factor:.2f}x, "
            text += f"output={result.calibration_output_factor:.2f}x, "
            text += f"samples={result.calibration_sample_count})"

        return {
            "content": [{"type": "text", "text": text}],
            "isError": False
        }

    except ImportError:
        return {
            "content": [{
                "type": "text",
                "text": "Token estimation service not available. Check that vibey.services.token_estimator is installed."
            }],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error estimating tokens: {str(e)}"}],
            "isError": True
        }


# =============================================================================
# REPORT HANDLERS
# =============================================================================


async def handle_get_token_usage_report(
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """Generate a token usage report."""
    track_id = arguments.get("track_id")
    sprint_id = arguments.get("sprint_id")
    include_completed = arguments.get("include_completed", True)
    include_in_progress = arguments.get("include_in_progress", True)

    try:
        # Collect tasks based on filters
        tasks = []

        if sprint_id:
            tasks = _get_sprint_tasks(adapter, sprint_id)
            scope = f"Sprint: {sprint_id}"
        elif track_id:
            tasks = _get_track_tasks(adapter, track_id)
            scope = f"Track: {track_id}"
        else:
            # Get all tasks across roadmap
            tasks = _get_all_tasks(adapter)
            scope = "Entire Roadmap"

        # Filter by status
        filtered_tasks = []
        for task in tasks:
            status = task.get("status", "")
            if status in ["completed", "production_ready"] and include_completed:
                filtered_tasks.append(task)
            elif status == "in_progress" and include_in_progress:
                filtered_tasks.append(task)
            elif status not in ["completed", "production_ready", "in_progress"]:
                filtered_tasks.append(task)  # Include other statuses by default

        # Aggregate data
        summary = _aggregate_token_data(filtered_tasks)

        # Calculate efficiency metrics
        efficiency = _calculate_efficiency_metrics(filtered_tasks)

        # Format report
        text = f"Token Usage Report\n"
        text += f"{'=' * 50}\n\n"
        text += f"**Scope:** {scope}\n"
        text += f"**Tasks Analyzed:** {len(filtered_tasks)}\n"
        text += f"**Generated:** {datetime.now(timezone.utc).isoformat()}\n\n"

        text += "## Summary\n\n"
        text += _format_token_summary(summary)

        text += "\n## Efficiency Metrics\n\n"
        if efficiency.get("accuracy_available"):
            text += f"**Estimate Accuracy:** {efficiency.get('estimate_accuracy', 0):.1%}\n"
            text += f"**Budget Utilization:** {efficiency.get('budget_utilization', 0):.1%}\n"
            text += f"**Over Budget Tasks:** {efficiency.get('over_budget_count', 0)}\n"
        else:
            text += "(Insufficient data for efficiency metrics)\n"

        # Task breakdown by type
        if filtered_tasks:
            text += "\n## By Task Type\n\n"
            by_type = _group_tasks_by_type(filtered_tasks)
            for task_type, type_tasks in by_type.items():
                type_summary = _aggregate_token_data(type_tasks)
                text += f"**{task_type}** ({len(type_tasks)} tasks):\n"
                text += f"  - Estimated: {type_summary.get('total_estimated', 0):,} tokens\n"
                text += f"  - Used: {type_summary.get('total_used', 0):,} tokens\n\n"

        return {
            "content": [{"type": "text", "text": text}],
            "isError": False
        }

    except (TrackNotFoundError, SprintNotFoundError) as e:
        return {
            "content": [{"type": "text", "text": str(e)}],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error generating report: {str(e)}"}],
            "isError": True
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _extract_token_data_from_task(task_info: Dict[str, Any]) -> Dict[str, Any]:
    """Extract token data from a task info dict."""
    return {
        "input_tokens": task_info.get("input_tokens", {}),
        "output_tokens": task_info.get("output_tokens", {}),
        "total_budget": task_info.get("total_budget"),
    }


def _format_tokens_section(tokens: Dict[str, Any]) -> str:
    """Format a tokens section (input or output)."""
    text = ""

    estimate = tokens.get("estimate", {})
    if estimate:
        text += f"  Estimate: {estimate.get('min', 'N/A')} - {estimate.get('target', 'N/A')} - {estimate.get('max', 'N/A')}\n"
    else:
        text += "  Estimate: Not set\n"

    budget = tokens.get("budget")
    if budget is not None:
        text += f"  Budget: {budget:,}\n"
    else:
        text += "  Budget: Not set\n"

    usage = tokens.get("usage")
    if usage is not None:
        text += f"  Usage: {usage:,}\n"
    else:
        text += "  Usage: None recorded\n"

    return text


def _get_sprint_tasks(adapter: RoadmapAdapter, sprint_id: str) -> List[Dict[str, Any]]:
    """Get all tasks for a sprint."""
    import yaml

    tasks = []
    tasks_dir = adapter.root / ".vibey" / "roadmap" / "tasks"

    if not tasks_dir.exists():
        return tasks

    for task_file in tasks_dir.glob("*.yaml"):
        try:
            with open(task_file, "r") as f:
                data = yaml.safe_load(f)
            task_data = data.get("task", data)
            if task_data.get("sprint_id") == sprint_id:
                tasks.append(task_data)
        except Exception:
            continue

    return tasks


def _get_track_tasks(adapter: RoadmapAdapter, track_id: str) -> List[Dict[str, Any]]:
    """Get all tasks for a track (across all sprints)."""
    import yaml

    tasks = []
    tasks_dir = adapter.root / ".vibey" / "roadmap" / "tasks"

    if not tasks_dir.exists():
        return tasks

    for task_file in tasks_dir.glob("*.yaml"):
        try:
            with open(task_file, "r") as f:
                data = yaml.safe_load(f)
            task_data = data.get("task", data)
            if task_data.get("track_id") == track_id:
                tasks.append(task_data)
        except Exception:
            continue

    return tasks


def _get_all_tasks(adapter: RoadmapAdapter) -> List[Dict[str, Any]]:
    """Get all tasks in the roadmap."""
    import yaml

    tasks = []
    tasks_dir = adapter.root / ".vibey" / "roadmap" / "tasks"

    if not tasks_dir.exists():
        return tasks

    for task_file in tasks_dir.glob("*.yaml"):
        try:
            with open(task_file, "r") as f:
                data = yaml.safe_load(f)
            task_data = data.get("task", data)
            tasks.append(task_data)
        except Exception:
            continue

    return tasks


def _aggregate_token_data(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate token data across multiple tasks."""
    summary = {
        "total_estimated": 0,
        "total_budgeted": 0,
        "total_used": 0,
        "input_estimated": 0,
        "input_budgeted": 0,
        "input_used": 0,
        "output_estimated": 0,
        "output_budgeted": 0,
        "output_used": 0,
        "tasks_with_estimates": 0,
        "tasks_with_budgets": 0,
        "tasks_with_usage": 0,
    }

    for task in tasks:
        input_tokens = task.get("input_tokens", {})
        output_tokens = task.get("output_tokens", {})

        # Input tokens
        input_estimate = input_tokens.get("estimate", {})
        if input_estimate and input_estimate.get("target"):
            summary["input_estimated"] += input_estimate["target"]
            summary["total_estimated"] += input_estimate["target"]

        if input_tokens.get("budget"):
            summary["input_budgeted"] += input_tokens["budget"]
            summary["total_budgeted"] += input_tokens["budget"]

        if input_tokens.get("usage"):
            summary["input_used"] += input_tokens["usage"]
            summary["total_used"] += input_tokens["usage"]

        # Output tokens
        output_estimate = output_tokens.get("estimate", {})
        if output_estimate and output_estimate.get("target"):
            summary["output_estimated"] += output_estimate["target"]
            summary["total_estimated"] += output_estimate["target"]

        if output_tokens.get("budget"):
            summary["output_budgeted"] += output_tokens["budget"]
            summary["total_budgeted"] += output_tokens["budget"]

        if output_tokens.get("usage"):
            summary["output_used"] += output_tokens["usage"]
            summary["total_used"] += output_tokens["usage"]

        # Count tasks
        has_estimate = (
            input_estimate.get("target") or
            output_estimate.get("target")
        )
        if has_estimate:
            summary["tasks_with_estimates"] += 1

        has_budget = (
            input_tokens.get("budget") or
            output_tokens.get("budget")
        )
        if has_budget:
            summary["tasks_with_budgets"] += 1

        has_usage = (
            input_tokens.get("usage") or
            output_tokens.get("usage")
        )
        if has_usage:
            summary["tasks_with_usage"] += 1

    return summary


def _format_token_summary(summary: Dict[str, Any]) -> str:
    """Format aggregated token summary."""
    text = "**Input Tokens:**\n"
    text += f"  - Estimated: {summary.get('input_estimated', 0):,}\n"
    text += f"  - Budgeted: {summary.get('input_budgeted', 0):,}\n"
    text += f"  - Used: {summary.get('input_used', 0):,}\n\n"

    text += "**Output Tokens:**\n"
    text += f"  - Estimated: {summary.get('output_estimated', 0):,}\n"
    text += f"  - Budgeted: {summary.get('output_budgeted', 0):,}\n"
    text += f"  - Used: {summary.get('output_used', 0):,}\n\n"

    text += "**Total Tokens:**\n"
    text += f"  - Estimated: {summary.get('total_estimated', 0):,}\n"
    text += f"  - Budgeted: {summary.get('total_budgeted', 0):,}\n"
    text += f"  - Used: {summary.get('total_used', 0):,}\n\n"

    text += "**Coverage:**\n"
    text += f"  - Tasks with estimates: {summary.get('tasks_with_estimates', 0)}\n"
    text += f"  - Tasks with budgets: {summary.get('tasks_with_budgets', 0)}\n"
    text += f"  - Tasks with usage data: {summary.get('tasks_with_usage', 0)}\n"

    return text


def _calculate_efficiency_metrics(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate efficiency metrics from tasks with usage data."""
    metrics = {
        "accuracy_available": False,
        "estimate_accuracy": 0.0,
        "budget_utilization": 0.0,
        "over_budget_count": 0,
    }

    tasks_with_data = []
    for task in tasks:
        input_tokens = task.get("input_tokens", {})
        output_tokens = task.get("output_tokens", {})

        input_estimate = input_tokens.get("estimate", {}).get("target")
        output_estimate = output_tokens.get("estimate", {}).get("target")
        input_usage = input_tokens.get("usage")
        output_usage = output_tokens.get("usage")

        if (input_estimate and input_usage) or (output_estimate and output_usage):
            tasks_with_data.append({
                "input_estimate": input_estimate or 0,
                "output_estimate": output_estimate or 0,
                "input_usage": input_usage or 0,
                "output_usage": output_usage or 0,
                "input_budget": input_tokens.get("budget"),
                "output_budget": output_tokens.get("budget"),
            })

    if not tasks_with_data:
        return metrics

    metrics["accuracy_available"] = True

    # Calculate estimate accuracy (usage / estimate)
    total_estimated = sum(t["input_estimate"] + t["output_estimate"] for t in tasks_with_data)
    total_used = sum(t["input_usage"] + t["output_usage"] for t in tasks_with_data)

    if total_estimated > 0:
        metrics["estimate_accuracy"] = min(total_used / total_estimated, 2.0)

    # Calculate budget utilization
    total_budgeted = 0
    for t in tasks_with_data:
        if t["input_budget"]:
            total_budgeted += t["input_budget"]
        if t["output_budget"]:
            total_budgeted += t["output_budget"]

    if total_budgeted > 0:
        metrics["budget_utilization"] = total_used / total_budgeted

    # Count over budget tasks
    for t in tasks_with_data:
        over = False
        if t["input_budget"] and t["input_usage"] > t["input_budget"]:
            over = True
        if t["output_budget"] and t["output_usage"] > t["output_budget"]:
            over = True
        if over:
            metrics["over_budget_count"] += 1

    return metrics


def _group_tasks_by_type(tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group tasks by task type."""
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for task in tasks:
        task_type = task.get("task_type", "unknown")
        if task_type not in groups:
            groups[task_type] = []
        groups[task_type].append(task)
    return groups


def _update_task_token_estimate(
    root: Path,
    task_id: str,
    direction: str,
    min_tokens: int,
    max_tokens: int,
    target: int
) -> Dict[str, Any]:
    """Update token estimate in task YAML file."""
    import yaml

    task_file = root / ".vibey" / "roadmap" / "tasks" / f"{task_id}.yaml"
    if not task_file.exists():
        return {"error": f"Task file not found: {task_id}"}

    try:
        with open(task_file, "r") as f:
            data = yaml.safe_load(f)

        # Navigate to task data
        if "task" in data:
            task_data = data["task"]
        else:
            task_data = data

        # Update the appropriate direction
        tokens_key = f"{direction}_tokens"
        if tokens_key not in task_data or task_data[tokens_key] is None:
            task_data[tokens_key] = {}

        task_data[tokens_key]["estimate"] = {
            "min": min_tokens,
            "max": max_tokens,
            "target": target
        }

        # Write back
        with open(task_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        return {"success": True}

    except Exception as e:
        return {"error": str(e)}


def _update_task_token_budget(
    root: Path,
    task_id: str,
    input_budget: Optional[int],
    output_budget: Optional[int],
    total_budget: Optional[int]
) -> Dict[str, Any]:
    """Update token budgets in task YAML file."""
    import yaml

    task_file = root / ".vibey" / "roadmap" / "tasks" / f"{task_id}.yaml"
    if not task_file.exists():
        return {"error": f"Task file not found: {task_id}"}

    try:
        with open(task_file, "r") as f:
            data = yaml.safe_load(f)

        if "task" in data:
            task_data = data["task"]
        else:
            task_data = data

        if input_budget is not None:
            if "input_tokens" not in task_data or task_data["input_tokens"] is None:
                task_data["input_tokens"] = {}
            task_data["input_tokens"]["budget"] = input_budget

        if output_budget is not None:
            if "output_tokens" not in task_data or task_data["output_tokens"] is None:
                task_data["output_tokens"] = {}
            task_data["output_tokens"]["budget"] = output_budget

        if total_budget is not None:
            task_data["total_budget"] = total_budget

        with open(task_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        return {"success": True}

    except Exception as e:
        return {"error": str(e)}


def _add_task_token_usage(
    root: Path,
    task_id: str,
    input_tokens: int,
    output_tokens: int
) -> Dict[str, Any]:
    """Add token usage to task (accumulates with existing)."""
    import yaml

    task_file = root / ".vibey" / "roadmap" / "tasks" / f"{task_id}.yaml"
    if not task_file.exists():
        return {"error": f"Task file not found: {task_id}"}

    try:
        with open(task_file, "r") as f:
            data = yaml.safe_load(f)

        if "task" in data:
            task_data = data["task"]
        else:
            task_data = data

        # Add to input usage
        if "input_tokens" not in task_data or task_data["input_tokens"] is None:
            task_data["input_tokens"] = {}
        current_input = task_data["input_tokens"].get("usage", 0) or 0
        new_input = current_input + input_tokens
        task_data["input_tokens"]["usage"] = new_input

        # Add to output usage
        if "output_tokens" not in task_data or task_data["output_tokens"] is None:
            task_data["output_tokens"] = {}
        current_output = task_data["output_tokens"].get("usage", 0) or 0
        new_output = current_output + output_tokens
        task_data["output_tokens"]["usage"] = new_output

        with open(task_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        return {
            "success": True,
            "new_input_usage": new_input,
            "new_output_usage": new_output
        }

    except Exception as e:
        return {"error": str(e)}
