"""
PM Adapters - Project Management Tool Integration Layer

This module provides the adapter framework for integrating with various
project management tools (Jira, GitHub, Trello, Asana, etc.) using a
unified interface.

Core Components:
- TicketAdapter: Abstract base class for all PM tool adapters
- PMAdapterRegistry: Registry for discovering and managing adapters
- PMCapabilities: Capability declarations for adapters
- SyncDirection/SyncResult: Types for sync operations

Design Philosophy:
- Vibey is just one adapter among many
- CLI/MCP talk to generic ticket interface
- Tool-specific logic stays in adapters
- Common operations have unified semantics

Usage:
    from vibey.adapters.pm import PMAdapterRegistry, TicketAdapter

    # Get the default adapter
    adapter = PMAdapterRegistry.get_default()

    # List all projects
    projects = adapter.list_projects()

    # Search for tasks
    tasks = adapter.search_tickets(status=TicketStatus.IN_PROGRESS)

Reference: UNIFIED_ADAPTER_ARCHITECTURE.md
"""

from vibey.adapters.pm.base import TicketAdapter
from vibey.adapters.pm.registry import (
    AdapterNotFoundError,
    AdapterRegistrationError,
    PMAdapterRegistry,
    pm_adapter,
)
from vibey.adapters.pm.types import (
    AdapterInfo,
    ConflictResolution,
    PMCapabilities,
    SyncConflict,
    SyncDirection,
    SyncResult,
)

__all__ = [
    # Base class
    "TicketAdapter",
    # Registry
    "AdapterNotFoundError",
    "AdapterRegistrationError",
    "PMAdapterRegistry",
    "pm_adapter",
    # Types
    "AdapterInfo",
    "ConflictResolution",
    "PMCapabilities",
    "SyncConflict",
    "SyncDirection",
    "SyncResult",
]
