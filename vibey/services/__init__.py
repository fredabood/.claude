"""
Services Layer - High-level operations for CLI and MCP.

This module provides adapter-agnostic services that enable swapping PM tools
without changing CLI or MCP code.

Core Services:
- TicketService: All ticket CRUD and workflow operations

Usage:
    from vibey.services import TicketService

    # Use default adapter
    service = TicketService()

    # Use specific adapter
    from vibey.adapters.pm import PMAdapterRegistry
    jira_adapter = PMAdapterRegistry.get("jira")
    service = TicketService(adapter=jira_adapter)

    # Operations
    projects = service.list_projects()
    task = service.get_ticket("TASK-123")
    service.start("TASK-123")
    service.complete("TASK-123")
"""

from vibey.services.ticket_service import TicketService, TicketServiceError

__all__ = [
    "TicketService",
    "TicketServiceError",
]
