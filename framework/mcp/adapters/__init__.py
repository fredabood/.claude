"""
MCP Adapter Layer.

Adapters that bridge the MCP server with Vibey's existing roadmap system.
"""

from .roadmap_adapter import RoadmapAdapter

__all__ = ["RoadmapAdapter"]
