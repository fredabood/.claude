"""Context management operations for the Vibey framework.

This module provides infrastructure for managing context across different
types of AI-assisted development work: sessions, tasks, decisions, and
sprint planning documents.

Storage Structure:
    .vibey/context/
    ├── index.yaml                 # Master index
    ├── config.yaml                # Configuration
    ├── sessions/                  # Session context
    │   ├── current/               # Active sessions
    │   └── history/               # Archived sessions
    ├── tasks/                     # Task context
    │   ├── current/               # Active tasks
    │   └── completed/             # Completed tasks
    ├── decisions/                 # Decision records
    ├── discovery/                 # Discovery outputs
    └── sprints/                   # Sprint context

Usage:
    from vibey.operations.context import (
        ContextManager,
        SessionContextWriter,
        TaskContextWriter,
        DecisionContextWriter,
    )

    # Get context manager
    manager = ContextManager()

    # Write session context
    session_writer = SessionContextWriter(manager.context_dir)
    session_path = session_writer.write(session_context)

    # Read and update
    session_context = session_writer.read(session_id)
    session_writer.update(session_id, {"status": "completed"})
"""

from .writers import (
    ContextWriter,
    SessionContextWriter,
    TaskContextWriter,
    DecisionContextWriter,
    SprintContextWriter,
    ContextManager,
    get_context_manager,
    SessionContext,
    TaskContext,
    DecisionContext,
    SprintContext,
)

from .readers import (
    ContextCache,
    ContextReader,
    SessionContextReader,
    TaskContextReader,
    DecisionContextReader,
    SprintContextReader,
    ContextLoader,
    AgentContext,
    get_context_loader,
)

from .capture import (
    CommandContext,
    CommandContextCapture,
    capture_command_context,
    get_recent_command_contexts,
)

from .agent_context import (
    EnhancedAgentContext,
    AgentContextLoader,
    get_agent_context_loader,
    load_agent_context,
    format_context_for_prompt,
)

__all__ = [
    # Data classes
    "SessionContext",
    "TaskContext",
    "DecisionContext",
    "SprintContext",
    "AgentContext",
    "CommandContext",
    # Writers
    "ContextWriter",
    "SessionContextWriter",
    "TaskContextWriter",
    "DecisionContextWriter",
    "SprintContextWriter",
    # Readers
    "ContextCache",
    "ContextReader",
    "SessionContextReader",
    "TaskContextReader",
    "DecisionContextReader",
    "SprintContextReader",
    # Loaders
    "ContextManager",
    "ContextLoader",
    "get_context_manager",
    "get_context_loader",
    # Capture
    "CommandContextCapture",
    "capture_command_context",
    "get_recent_command_contexts",
    # Agent Context
    "EnhancedAgentContext",
    "AgentContextLoader",
    "get_agent_context_loader",
    "load_agent_context",
    "format_context_for_prompt",
]
