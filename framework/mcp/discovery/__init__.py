"""
Dynamic Discovery Module for Vibey MCP Server.

This module scans agent, workflow, and handoff markdown files,
parses their YAML frontmatter, and generates MCP tool definitions
dynamically. This ensures zero drift between source definitions
and MCP tools.

Usage:
    from framework.mcp.discovery import ToolDiscovery

    discovery = ToolDiscovery(root_dir)
    tools = discovery.discover_all_tools()
"""

from .parser import FrontmatterParser
from .agents import AgentDiscovery, AgentDefinition
from .workflows import WorkflowDiscovery, WorkflowDefinition, WorkflowStep, QualityGate
from .generator import ToolGenerator
from .discovery import ToolDiscovery

__all__ = [
    "FrontmatterParser",
    "AgentDiscovery",
    "AgentDefinition",
    "WorkflowDiscovery",
    "WorkflowDefinition",
    "WorkflowStep",
    "QualityGate",
    "ToolGenerator",
    "ToolDiscovery",
]
