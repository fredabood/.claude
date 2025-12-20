"""
Vibey Core - Tool-Agnostic Abstractions

This module provides the foundational abstractions that enable Vibey to work with
multiple project management tools. The core concept is the Generic Ticket model,
which serves as a universal representation of work items across different PM tools.

Key Components:
- Ticket: Universal work item abstraction (Task, Issue, Card, etc.)
- HierarchyType: Generic hierarchy levels (Project, Workstream, Iteration, WorkItem)
- TicketStatus: Universal status values

Design Philosophy:
- Vibey is just one adapter among many (Jira, GitHub, Trello, Asana, etc.)
- CLI/MCP talk to generic ticket interface, not Vibey-specific models
- Semantic differences stay in adapters, not in core

See: UNIFIED_ADAPTER_ARCHITECTURE.md for full design documentation.
"""

from vibey.core.ticket import (
    Criterion,
    CriterionStatus,
    CriterionType,
    HierarchyType,
    Ticket,
    TicketPriority,
    TicketStatus,
)

__all__ = [
    "Criterion",
    "CriterionStatus",
    "CriterionType",
    "HierarchyType",
    "Ticket",
    "TicketPriority",
    "TicketStatus",
]
