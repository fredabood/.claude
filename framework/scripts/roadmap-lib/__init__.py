"""
Roadmap Library - Core utilities for roadmap state management.

This package provides shared utilities for roadmap scripts:
- Dependency resolution
- Blocker computation
- Status progression
- Activity logging
- File system management
- Version management
- Agent routing and recommendations
"""

from dependencies import DependencyResolver, resolve_dependencies, detect_circular_dependencies
from blockers import BlockerComputer, compute_blockers, is_blocked
from status import StatusManager, can_progress_status, progress_status_if_ready
from activity import ActivityLogger, log_activity
from filesystem import FileSystemManager, ensure_roadmap_structure, find_roadmap_root
from versioning import VersionManager, bump_version, parse_version
from agents import AgentRouter, recommend_agent, get_workload, recommend_tasks

__all__ = [
    # Dependencies
    "DependencyResolver",
    "resolve_dependencies",
    "detect_circular_dependencies",
    # Blockers
    "BlockerComputer",
    "compute_blockers",
    "is_blocked",
    # Status
    "StatusManager",
    "can_progress_status",
    "progress_status_if_ready",
    # Activity
    "ActivityLogger",
    "log_activity",
    # Filesystem
    "FileSystemManager",
    "ensure_roadmap_structure",
    "find_roadmap_root",
    # Versioning
    "VersionManager",
    "bump_version",
    "parse_version",
    # Agents
    "AgentRouter",
    "recommend_agent",
    "get_workload",
    "recommend_tasks",
]

__version__ = "2.3"
