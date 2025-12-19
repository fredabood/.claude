"""Context management operations for the Vibey framework.

This module provides infrastructure for managing context across different
types of AI-assisted development work: sessions, tasks, decisions, and
sprint planning documents.

Storage Structure (Legacy):
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

Storage Structure (Context System V2):
    .vibey/roadmap/context/
    ├── plans/                     # Pre-work planning artifacts
    │   └── {ticket_id}/           # Directory per ticket (ULID)
    │       ├── plan.yaml          # Structured metadata + artifact index
    │       └── *.md               # Optional artifact documents
    ├── runtime/                   # Active session state
    │   └── {ticket_id}.yaml       # Single file per ticket
    └── post-mortems/              # Completion summaries
        └── {ticket_id}.yaml       # Single file per ticket

Usage (Legacy):
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

Usage (V2 Context Models - Three-Phase Model):
    from vibey.operations.context import (
        PlanContext,
        RuntimeContext,
        PostMortemContextV2,  # V2 model, distinct from legacy PostMortemContext
        ArtifactRef,
    )

    # Create a plan context with artifact references
    plan = PlanContext(
        ticket_id="01KCMMK1MSFBZAM880C9K3BWPB",
        goals=["Implement feature X"],
        approach="Use pattern Y",
        artifact_refs=[
            ArtifactRef(artifact_id="01ART123", purpose="Main module")
        ],
    )

    # Auto-create associations when plan is saved
    from vibey.operations.context import create_associations_from_plan
    associations = create_associations_from_plan(plan)
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

from .post_mortem import (
    PostMortemContext,
    generate_post_mortem,
    save_post_mortem,
    auto_generate_on_complete,
    load_post_mortem,
)

# V2 Context Models (Three-Phase Model with Artifact References)
# These models integrate with the Unified Ticket Architecture
from .models import (
    # Enums
    AssociationSource,
    PostMortemOutcome,
    ImpactLevel,
    BlockerSeverity,
    FileStatus,
    # Core reference
    ArtifactRef,
    # Supporting models
    Decision,
    Discovery,
    Blocker,
    ActiveFile,
    Checkpoint,
    TokenUsage,
    Risk,
    RelatedTicket,
    PlanArtifact,
    KnownFile,
    FileChange,
    KeyDecision,
    LessonLearned,
    FollowUpItem,
    # Context models (V2)
    PlanContext,
    RuntimeContext,
    PostMortemContext as PostMortemContextV2,  # Renamed to avoid conflict with legacy
    # Association auto-creation
    CreateAssociationCallback,
    set_association_callback,
    get_association_callback,
    create_associations_from_plan,
)

__all__ = [
    # Data classes (Legacy)
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
    # Post-Mortem (Legacy)
    "PostMortemContext",
    "generate_post_mortem",
    "save_post_mortem",
    "auto_generate_on_complete",
    "load_post_mortem",
    # === V2 Context Models (Three-Phase Model) ===
    # Enums
    "AssociationSource",
    "PostMortemOutcome",
    "ImpactLevel",
    "BlockerSeverity",
    "FileStatus",
    # Core reference
    "ArtifactRef",
    # Supporting models
    "Decision",
    "Discovery",
    "Blocker",
    "ActiveFile",
    "Checkpoint",
    "TokenUsage",
    "Risk",
    "RelatedTicket",
    "PlanArtifact",
    "KnownFile",
    "FileChange",
    "KeyDecision",
    "LessonLearned",
    "FollowUpItem",
    # Context models (V2)
    "PlanContext",
    "RuntimeContext",
    "PostMortemContextV2",
    # Association auto-creation
    "CreateAssociationCallback",
    "set_association_callback",
    "get_association_callback",
    "create_associations_from_plan",
]
