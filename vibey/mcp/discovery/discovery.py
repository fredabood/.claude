"""
Main Tool Discovery Module.

Orchestrates agent and workflow discovery, generates MCP tools,
and provides caching for efficient tool lookup.
"""

import hashlib
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from .agents import AgentDiscovery, AgentDefinition
from .workflows import WorkflowDiscovery, WorkflowDefinition
from .generator import ToolGenerator

logger = logging.getLogger(__name__)


class ToolDiscovery:
    """
    Main tool discovery orchestrator with caching.

    Discovers agents and workflows, generates MCP tools, and caches
    results for efficient repeated access. Cache is invalidated when
    source files change.

    Example:
        >>> discovery = ToolDiscovery(Path("/path/to/vibey"))
        >>> tools = discovery.get_all_tools()
        >>> print(f"Found {len(tools)} tools")

        # Cache is used on subsequent calls
        >>> tools = discovery.get_all_tools()  # Fast, uses cache
    """

    def __init__(
        self,
        root_dir: Path,
        cache_ttl: int = 60,
        tool_prefix: str = "vibey"
    ):
        """
        Initialize tool discovery.

        Args:
            root_dir: Root directory of Vibey repository
            cache_ttl: Cache time-to-live in seconds (default: 60)
            tool_prefix: Prefix for generated tool names
        """
        self.root_dir = Path(root_dir)
        self.cache_ttl = cache_ttl

        # Initialize sub-modules
        self.agent_discovery = AgentDiscovery(root_dir)
        self.workflow_discovery = WorkflowDiscovery(root_dir)
        self.generator = ToolGenerator(tool_prefix)

        # Cache storage
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_time: float = 0
        self._cache_hash: str = ""

    def get_all_tools(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get all MCP tools (agents + workflows).

        Uses cache if available and not expired.

        Args:
            force_refresh: Force cache refresh

        Returns:
            List of MCP tool definitions
        """
        if not force_refresh and self._is_cache_valid():
            logger.debug("Using cached tools")
            return self._cache['tools']

        # Refresh cache
        return self._refresh_cache()

    def get_agent_tools(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get only agent tools."""
        tools = self.get_all_tools(force_refresh)
        return [t for t in tools if t.get('_metadata', {}).get('asset_type') == 'agent']

    def get_workflow_tools(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get only workflow tools."""
        tools = self.get_all_tools(force_refresh)
        return [t for t in tools if t.get('_metadata', {}).get('asset_type') == 'workflow']

    def get_tool_by_name(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific tool by name.

        Args:
            tool_name: MCP tool name

        Returns:
            Tool definition or None
        """
        tools = self.get_all_tools()
        for tool in tools:
            if tool['name'] == tool_name:
                return tool
        return None

    def get_agents(self) -> List[AgentDefinition]:
        """Get all discovered agent definitions."""
        return self.agent_discovery.discover()

    def get_workflows(self) -> List[WorkflowDefinition]:
        """Get all discovered workflow definitions."""
        return self.workflow_discovery.discover()

    def invalidate_cache(self):
        """Manually invalidate the cache."""
        self._cache = None
        self._cache_time = 0
        self._cache_hash = ""
        logger.debug("Cache invalidated")

    def _is_cache_valid(self) -> bool:
        """Check if cache is valid."""
        if self._cache is None:
            return False

        # Check TTL
        if time.time() - self._cache_time > self.cache_ttl:
            logger.debug("Cache expired (TTL)")
            return False

        # Check file hash
        current_hash = self._compute_source_hash()
        if current_hash != self._cache_hash:
            logger.debug("Cache expired (files changed)")
            return False

        return True

    def _refresh_cache(self) -> List[Dict[str, Any]]:
        """Refresh the tool cache."""
        logger.info("Refreshing tool cache...")

        # Discover assets
        agents = self.agent_discovery.discover()
        workflows = self.workflow_discovery.discover()

        # Generate tools
        tools = self.generator.generate_all_tools(agents, workflows)

        # Update cache
        self._cache = {
            'tools': tools,
            'agents': agents,
            'workflows': workflows,
        }
        self._cache_time = time.time()
        self._cache_hash = self._compute_source_hash()

        logger.info(f"Cache refreshed: {len(tools)} tools")
        return tools

    def _compute_source_hash(self) -> str:
        """
        Compute hash of source files for cache invalidation.

        Uses modification times for efficiency.
        """
        hash_input = []

        # Get mod times for agent files
        agents_dir = self.root_dir / 'framework' / 'agents'
        if agents_dir.exists():
            for f in agents_dir.rglob('*.md'):
                try:
                    mtime = os.path.getmtime(f)
                    hash_input.append(f"{f}:{mtime}")
                except OSError:
                    pass

        # Get mod times for workflow files
        workflows_dir = self.root_dir / 'framework' / 'workflows'
        if workflows_dir.exists():
            for f in workflows_dir.rglob('*.md'):
                try:
                    mtime = os.path.getmtime(f)
                    hash_input.append(f"{f}:{mtime}")
                except OSError:
                    pass

        # Compute hash
        hash_str = '\n'.join(sorted(hash_input))
        return hashlib.md5(hash_str.encode()).hexdigest()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get discovery statistics.

        Returns:
            Dict with counts and cache status
        """
        tools = self.get_all_tools()
        agent_tools = [t for t in tools if t.get('_metadata', {}).get('asset_type') == 'agent']
        workflow_tools = [t for t in tools if t.get('_metadata', {}).get('asset_type') == 'workflow']

        return {
            'total_tools': len(tools),
            'agent_tools': len(agent_tools),
            'workflow_tools': len(workflow_tools),
            'cache_valid': self._is_cache_valid(),
            'cache_age_seconds': time.time() - self._cache_time if self._cache_time else None,
            'cache_ttl': self.cache_ttl,
        }
