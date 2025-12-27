"""
Submodule Integration Tools.

MCP tools for git submodule integration with vibey roadmaps.
Supports discovery, push-down, pull-up, and cross-repo dependency management.

Key principle: Submodules have NO knowledge of parent repos.
All cross-repo data lives in the PARENT repo only.
"""

from typing import List, Dict, Any, Optional

from ..utils.errors import VibeyMCPError


# Tool Definitions

def get_submodule_tools() -> List[Dict[str, Any]]:
    """
    Get submodule integration tool definitions.

    Returns:
        List of tool definition dicts following MCP spec
    """
    return [
        # ====================================================================
        # DISCOVERY (3 tools)
        # ====================================================================
        {
            "name": "vibey_submodule_list",
            "title": "List Submodules",
            "description": "List all detected git submodules and their Vibey status",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "show_all": {
                        "type": "boolean",
                        "description": "Show all submodules, including those without Vibey",
                        "default": False
                    }
                },
                "required": []
            }
        },
        {
            "name": "vibey_submodule_discover",
            "title": "Discover Submodules",
            "description": "Auto-discover submodules from .gitmodules and optionally register them",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "auto_register": {
                        "type": "boolean",
                        "description": "Automatically register Vibey-enabled submodules",
                        "default": False
                    }
                },
                "required": []
            }
        },
        {
            "name": "vibey_submodule_roadmap",
            "title": "Get Submodule Roadmap",
            "description": "Get roadmap summary for a Vibey-enabled submodule",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the submodule (e.g., 'libs/core')"
                    }
                },
                "required": ["path"]
            }
        },

        # ====================================================================
        # PUSH-DOWN (3 tools)
        # ====================================================================
        {
            "name": "vibey_submodule_push_requirement",
            "title": "Push Requirement to Submodule",
            "description": "Push a task requirement to a submodule",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "parent_ticket_id": {
                        "type": "string",
                        "description": "Parent ticket ID that needs this requirement"
                    },
                    "submodule_path": {
                        "type": "string",
                        "description": "Path to the target submodule"
                    },
                    "title": {
                        "type": "string",
                        "description": "Title for the submodule task"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description for the submodule task"
                    },
                    "push_mode": {
                        "type": "string",
                        "enum": ["linked", "parent_only", "submodule_only"],
                        "description": "Push mode: linked (both), parent_only, or submodule_only",
                        "default": "linked"
                    }
                },
                "required": ["parent_ticket_id", "submodule_path", "title"]
            }
        },
        {
            "name": "vibey_submodule_requirements",
            "title": "List Cross-repo Requirements",
            "description": "List cross-repo requirements pushed to/from submodules",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["outgoing", "incoming"],
                        "description": "Direction of requirements",
                        "default": "outgoing"
                    },
                    "status_filter": {
                        "type": "string",
                        "description": "Filter by status (pending, accepted, rejected)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "vibey_submodule_accept_requirement",
            "title": "Accept Incoming Requirement",
            "description": "Accept an incoming requirement pushed from parent repo",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "requirement_id": {
                        "type": "string",
                        "description": "ID of the incoming requirement"
                    },
                    "create_ticket": {
                        "type": "boolean",
                        "description": "Create a ticket for this requirement",
                        "default": True
                    }
                },
                "required": ["requirement_id"]
            }
        },

        # ====================================================================
        # PULL-UP (3 tools)
        # ====================================================================
        {
            "name": "vibey_submodule_status",
            "title": "Get Submodule Status",
            "description": "Get aggregated progress from all registered submodules",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "vibey_submodule_blockers",
            "title": "List Submodule Blockers",
            "description": "List blockers from submodules affecting parent tasks",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "severity_filter": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low"],
                        "description": "Filter by severity level"
                    },
                    "submodule_filter": {
                        "type": "string",
                        "description": "Filter by submodule path"
                    }
                },
                "required": []
            }
        },
        {
            "name": "vibey_submodule_refresh",
            "title": "Refresh Submodule Progress",
            "description": "Force refresh progress data from submodules",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to refresh (optional, refreshes all if not specified)"
                    }
                },
                "required": []
            }
        },

        # ====================================================================
        # CROSS-REPO DEPENDENCIES (4 tools)
        # ====================================================================
        {
            "name": "vibey_task_add_cross_dep",
            "title": "Add Cross-repo Dependency",
            "description": "Add a cross-repo dependency from a task to a submodule task",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "Parent ticket ID"
                    },
                    "dependency_ref": {
                        "type": "string",
                        "description": "Dependency reference (format: submodule_path:task_id)"
                    },
                    "dependency_type": {
                        "type": "string",
                        "description": "Type of dependency",
                        "default": "blocks"
                    },
                    "blocking": {
                        "type": "boolean",
                        "description": "Whether this dependency blocks progress",
                        "default": True
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for the dependency"
                    }
                },
                "required": ["ticket_id", "dependency_ref"]
            }
        },
        {
            "name": "vibey_task_cross_deps",
            "title": "List Cross-repo Dependencies",
            "description": "List cross-repo dependencies for a ticket",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "Ticket ID to query"
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["outgoing", "incoming", "both"],
                        "description": "Direction of dependencies",
                        "default": "both"
                    }
                },
                "required": ["ticket_id"]
            }
        },
        {
            "name": "vibey_submodule_dep_graph",
            "title": "Get Dependency Graph",
            "description": "Get the full cross-repo dependency graph",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "enum": ["json", "dot", "text"],
                        "description": "Output format",
                        "default": "json"
                    }
                },
                "required": []
            }
        },
        {
            "name": "vibey_submodule_validate_deps",
            "title": "Validate Dependencies",
            "description": "Validate cross-repo dependencies for cycles and missing targets",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },

        # ====================================================================
        # SYNC (1 tool)
        # ====================================================================
        {
            "name": "vibey_submodule_sync",
            "title": "Sync Submodules",
            "description": "Trigger sync operations across all submodules (aggregate and update blocked_by)",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    ]


# Tool Handlers

async def handle_submodule_tool(
    tool_name: str,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Handle submodule tool invocation.

    Routes to appropriate handler based on tool name.

    Args:
        tool_name: Name of tool being invoked
        arguments: Tool input arguments

    Returns:
        MCP tool response dict with content and isError flag
    """
    try:
        # Discovery tools
        if tool_name == "vibey_submodule_list":
            return await _handle_submodule_list(arguments)
        elif tool_name == "vibey_submodule_discover":
            return await _handle_submodule_discover(arguments)
        elif tool_name == "vibey_submodule_roadmap":
            return await _handle_submodule_roadmap(arguments)

        # Push-down tools
        elif tool_name == "vibey_submodule_push_requirement":
            return await _handle_push_requirement(arguments)
        elif tool_name == "vibey_submodule_requirements":
            return await _handle_requirements(arguments)
        elif tool_name == "vibey_submodule_accept_requirement":
            return await _handle_accept_requirement(arguments)

        # Pull-up tools
        elif tool_name == "vibey_submodule_status":
            return await _handle_submodule_status(arguments)
        elif tool_name == "vibey_submodule_blockers":
            return await _handle_submodule_blockers(arguments)
        elif tool_name == "vibey_submodule_refresh":
            return await _handle_submodule_refresh(arguments)

        # Cross-repo dependency tools
        elif tool_name == "vibey_task_add_cross_dep":
            return await _handle_add_cross_dep(arguments)
        elif tool_name == "vibey_task_cross_deps":
            return await _handle_cross_deps(arguments)
        elif tool_name == "vibey_submodule_dep_graph":
            return await _handle_dep_graph(arguments)
        elif tool_name == "vibey_submodule_validate_deps":
            return await _handle_validate_deps(arguments)

        # Sync tool
        elif tool_name == "vibey_submodule_sync":
            return await _handle_submodule_sync(arguments)

        else:
            raise VibeyMCPError(f"Unknown submodule tool: {tool_name}")

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }


# Private handlers

async def _handle_submodule_list(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """List all detected submodules."""
    from vibey.operations.submodule import SubmoduleDiscovery
    from vibey.config import load_submodule_config

    show_all = arguments.get("show_all", False)

    discovery = SubmoduleDiscovery()
    config = load_submodule_config()

    git_submodules = discovery.parse_gitmodules()
    all_paths = set(git_submodules)
    all_paths.update(s.path for s in config.submodules)

    results = []
    for path in sorted(all_paths):
        has_vibey = discovery.has_vibey_roadmap(path)
        registered = config.get_submodule(path) is not None

        if not show_all and not has_vibey:
            continue

        sub_ref = config.get_submodule(path)
        results.append({
            "path": path,
            "has_vibey": has_vibey,
            "registered": registered,
            "sync_status": sub_ref.sync_status.value if sub_ref else "not_registered"
        })

    return {
        "content": [{"type": "text", "text": _format_json({"submodules": results})}],
        "isError": False
    }


async def _handle_submodule_discover(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Discover submodules from .gitmodules."""
    from vibey.operations.submodule import SubmoduleDiscovery
    from vibey.config import load_submodule_config, save_submodule_config
    from vibey.roadmap.models.submodule import SubmoduleReference, DetectionSource

    auto_register = arguments.get("auto_register", False)

    discovery = SubmoduleDiscovery()
    config = load_submodule_config()

    submodule_paths = discovery.parse_gitmodules()

    results = []
    registered = []

    for path in submodule_paths:
        has_vibey = discovery.has_vibey_roadmap(path)
        results.append({
            "path": path,
            "has_vibey": has_vibey
        })

        if auto_register and has_vibey and config.get_submodule(path) is None:
            ref = SubmoduleReference(
                path=path,
                aggregate=True,
                detection_source=DetectionSource.GITMODULES,
            )
            config.add_submodule(ref)
            registered.append(path)

    if registered:
        save_submodule_config(config)

    return {
        "content": [{"type": "text", "text": _format_json({
            "discovered": results,
            "registered": registered
        })}],
        "isError": False
    }


async def _handle_submodule_roadmap(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Get roadmap summary for a submodule."""
    from vibey.operations.submodule import SubmoduleDiscovery, ProgressAggregator

    path = arguments["path"].replace("\\", "/").strip("/")

    discovery = SubmoduleDiscovery()
    if not discovery.has_vibey_roadmap(path):
        return {
            "content": [{"type": "text", "text": f"Submodule '{path}' does not have a Vibey roadmap"}],
            "isError": True
        }

    aggregator = ProgressAggregator()
    progress = aggregator.aggregate_submodule(path)

    return {
        "content": [{"type": "text", "text": _format_json({
            "path": path,
            "tracks_total": progress.tracks_total,
            "tracks_completed": progress.tracks_completed,
            "sprints_total": progress.sprints_total,
            "sprints_completed": progress.sprints_completed,
            "tasks_total": progress.tasks_total,
            "tasks_completed": progress.tasks_completed,
            "completion_percent": progress.completion_percent
        })}],
        "isError": False
    }


async def _handle_push_requirement(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Push a requirement to a submodule."""
    from vibey.operations.submodule import TaskPusher
    from vibey.config import load_submodule_config

    config = load_submodule_config()
    submodule_path = arguments["submodule_path"].replace("\\", "/").strip("/")

    if config.get_submodule(submodule_path) is None:
        return {
            "content": [{"type": "text", "text": f"Submodule not registered: {submodule_path}"}],
            "isError": True
        }

    pusher = TaskPusher()
    result = pusher.push_task(
        submodule_path=submodule_path,
        title=arguments["title"],
        description=arguments.get("description", ""),
        mode=arguments.get("push_mode", "linked"),
        sprint_id=None,
    )

    if result.success:
        return {
            "content": [{"type": "text", "text": _format_json({
                "success": True,
                "parent_task_id": result.parent_task_id,
                "submodule_task_id": result.submodule_task_id,
                "linked": result.linked
            })}],
            "isError": False
        }
    else:
        return {
            "content": [{"type": "text", "text": f"Failed: {result.error}"}],
            "isError": True
        }


async def _handle_requirements(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """List cross-repo requirements."""
    from vibey.operations.submodule import RequirementTracker

    tracker = RequirementTracker()
    requirements = tracker.list_requirements(
        direction=arguments.get("direction", "outgoing"),
        status_filter=arguments.get("status_filter"),
    )

    results = [
        {
            "id": req.id,
            "title": req.title,
            "submodule_path": req.submodule_path,
            "status": req.status,
            "linked": req.linked
        }
        for req in requirements
    ]

    return {
        "content": [{"type": "text", "text": _format_json({"requirements": results})}],
        "isError": False
    }


async def _handle_accept_requirement(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Accept an incoming requirement."""
    from vibey.operations.submodule import RequirementTracker

    tracker = RequirementTracker()
    result = tracker.accept_requirement(
        requirement_id=arguments["requirement_id"],
        create_ticket=arguments.get("create_ticket", True),
    )

    if result.success:
        return {
            "content": [{"type": "text", "text": _format_json({
                "success": True,
                "ticket_id": result.ticket_id
            })}],
            "isError": False
        }
    else:
        return {
            "content": [{"type": "text", "text": f"Failed: {result.error}"}],
            "isError": True
        }


async def _handle_submodule_status(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Get aggregated progress from all submodules."""
    from vibey.operations.submodule import ProgressAggregator
    from vibey.config import load_submodule_config

    config = load_submodule_config()
    if not config.submodules:
        return {
            "content": [{"type": "text", "text": "No submodules registered"}],
            "isError": False
        }

    aggregator = ProgressAggregator()
    result = aggregator.aggregate_all()

    return {
        "content": [{"type": "text", "text": _format_json({
            "total_tracks": result.total_tracks,
            "completed_tracks": result.completed_tracks,
            "total_tasks": result.total_tasks,
            "completed_tasks": result.completed_tasks,
            "overall_completion_percent": result.overall_completion_percent,
            "active_blockers": len(result.active_blockers),
            "critical_blockers": result.critical_blocker_count,
            "submodules": [
                {
                    "path": prog.submodule_path,
                    "tasks_completed": prog.tasks_completed,
                    "tasks_total": prog.tasks_total,
                    "completion_percent": prog.completion_percent
                }
                for prog in result.submodule_progress
            ]
        })}],
        "isError": False
    }


async def _handle_submodule_blockers(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """List blockers from submodules."""
    from vibey.operations.submodule import ProgressAggregator
    from vibey.config import load_submodule_config

    config = load_submodule_config()
    if not config.submodules:
        return {
            "content": [{"type": "text", "text": "No submodules registered"}],
            "isError": False
        }

    aggregator = ProgressAggregator()
    result = aggregator.aggregate_all()

    blockers = result.active_blockers

    severity_filter = arguments.get("severity_filter")
    if severity_filter:
        blockers = [b for b in blockers if b.severity == severity_filter]

    submodule_filter = arguments.get("submodule_filter")
    if submodule_filter:
        submodule_filter = submodule_filter.replace("\\", "/").strip("/")
        blockers = [b for b in blockers if b.submodule_path == submodule_filter]

    return {
        "content": [{"type": "text", "text": _format_json({
            "blockers": [
                {
                    "submodule_path": b.submodule_path,
                    "task_id": b.task_id,
                    "description": b.blocker_description,
                    "severity": b.severity
                }
                for b in blockers
            ]
        })}],
        "isError": False
    }


async def _handle_submodule_refresh(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Force refresh of submodule progress."""
    from vibey.operations.submodule import ProgressAggregator
    from vibey.config import load_submodule_config, save_submodule_config
    from datetime import datetime, timezone

    config = load_submodule_config()
    aggregator = ProgressAggregator()

    path = arguments.get("path")
    if path:
        path = path.replace("\\", "/").strip("/")
        sub_ref = config.get_submodule(path)
        if sub_ref is None:
            return {
                "content": [{"type": "text", "text": f"Submodule not registered: {path}"}],
                "isError": True
            }

        progress = aggregator.aggregate_submodule(path)
        sub_ref.last_synced = datetime.now(timezone.utc)
        save_submodule_config(config)

        return {
            "content": [{"type": "text", "text": _format_json({
                "path": path,
                "tasks_completed": progress.tasks_completed,
                "tasks_total": progress.tasks_total,
                "completion_percent": progress.completion_percent
            })}],
            "isError": False
        }
    else:
        result = aggregator.aggregate_all()
        for sub in config.submodules:
            sub.last_synced = datetime.now(timezone.utc)
        save_submodule_config(config)

        return {
            "content": [{"type": "text", "text": _format_json({
                "refreshed": len(result.submodule_progress),
                "overall_completion_percent": result.overall_completion_percent
            })}],
            "isError": False
        }


async def _handle_add_cross_dep(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Add a cross-repo dependency."""
    from vibey.operations.submodule import DependencyResolver

    dependency_ref = arguments["dependency_ref"]
    if ":" not in dependency_ref:
        return {
            "content": [{"type": "text", "text": "Invalid dependency_ref format. Use: submodule_path:task_id"}],
            "isError": True
        }

    submodule_path, target_task_id = dependency_ref.split(":", 1)

    resolver = DependencyResolver()
    result = resolver.add_dependency(
        ticket_id=arguments["ticket_id"],
        submodule_path=submodule_path,
        target_task_id=target_task_id,
        dependency_type=arguments.get("dependency_type", "blocks"),
        blocking=arguments.get("blocking", True),
        reason=arguments.get("reason"),
    )

    if result.success:
        return {
            "content": [{"type": "text", "text": _format_json({"success": True})}],
            "isError": False
        }
    else:
        return {
            "content": [{"type": "text", "text": f"Failed: {result.error}"}],
            "isError": True
        }


async def _handle_cross_deps(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """List cross-repo dependencies for a ticket."""
    from vibey.operations.submodule import DependencyResolver

    resolver = DependencyResolver()
    deps = resolver.get_dependencies(
        ticket_id=arguments["ticket_id"],
        direction=arguments.get("direction", "both"),
    )

    return {
        "content": [{"type": "text", "text": _format_json({
            "dependencies": [
                {
                    "direction": dep.direction,
                    "submodule_path": dep.submodule_path,
                    "task_id": dep.task_id,
                    "dependency_type": dep.dependency_type,
                    "blocking": dep.blocking,
                    "status": dep.status
                }
                for dep in deps
            ]
        })}],
        "isError": False
    }


async def _handle_dep_graph(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Get the full cross-repo dependency graph."""
    from vibey.operations.submodule import DependencyResolver

    resolver = DependencyResolver()
    graph = resolver.build_graph()

    output_format = arguments.get("format", "json")

    if output_format == "json":
        return {
            "content": [{"type": "text", "text": _format_json(graph.to_json())}],
            "isError": False
        }
    elif output_format == "dot":
        return {
            "content": [{"type": "text", "text": graph.to_dot()}],
            "isError": False
        }
    elif output_format == "text":
        lines = []
        for node in graph.nodes:
            deps = graph.get_dependencies(node)
            if deps:
                lines.append(f"{node}")
                for dep in deps:
                    arrow = "──▶" if dep.blocking else "──>"
                    lines.append(f"  {arrow} {dep.target} ({dep.submodule_path})")
        return {
            "content": [{"type": "text", "text": "\n".join(lines) if lines else "No dependencies"}],
            "isError": False
        }
    else:
        return {
            "content": [{"type": "text", "text": f"Unknown format: {output_format}"}],
            "isError": True
        }


async def _handle_validate_deps(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Validate cross-repo dependencies."""
    from vibey.operations.submodule import DependencyResolver

    resolver = DependencyResolver()
    result = resolver.validate_all()

    return {
        "content": [{"type": "text", "text": _format_json({
            "is_valid": result.is_valid,
            "cycles": result.cycles if result.cycles else [],
            "missing_targets": [
                {"source": m.source, "target": m.target}
                for m in result.missing_targets
            ] if result.missing_targets else [],
            "stale_references": [
                {"source": s.source, "target": s.target}
                for s in result.stale_references
            ] if result.stale_references else []
        })}],
        "isError": False
    }


async def _handle_submodule_sync(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Trigger sync operations across all submodules."""
    from vibey.operations.submodule import ProgressAggregator
    from vibey.config import load_submodule_config, save_submodule_config
    from datetime import datetime, timezone

    config = load_submodule_config()
    if not config.submodules:
        return {
            "content": [{"type": "text", "text": "No submodules registered"}],
            "isError": False
        }

    aggregator = ProgressAggregator()

    # Aggregate all
    result = aggregator.aggregate_all()

    # Sync blocked_by statuses
    sync_results = aggregator.sync_blocked_by_status()

    total_synced = sum(r.tasks_synced for r in sync_results)
    total_resolved = sum(r.blockers_resolved for r in sync_results)

    # Update last_synced
    for sub in config.submodules:
        sub.last_synced = datetime.now(timezone.utc)
    save_submodule_config(config)

    return {
        "content": [{"type": "text", "text": _format_json({
            "submodules_aggregated": len(result.submodule_progress),
            "tasks_synced": total_synced,
            "blockers_resolved": total_resolved,
            "overall_completion_percent": result.overall_completion_percent
        })}],
        "isError": False
    }


def _format_json(data: Any) -> str:
    """Format data as JSON."""
    import json
    return json.dumps(data, indent=2)
