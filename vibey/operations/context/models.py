"""
Context Models for the Three-Phase Context System (V2).

This module defines Pydantic models for managing context across three phases:
- PlanContext: Pre-work planning with artifact references
- RuntimeContext: Active session state and decisions
- PostMortemContext: Completion summaries and lessons learned

Design Reference:
- Sprint 2 Plan: Task 8 - Integrate Context into Three-Phase Model
- Directory Structure Spec: Parts 2-4

Task: 01KCQDE6N5G9NGKHWNBZAY3YGM
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================


class AssociationSource(str, Enum):
    """
    How an artifact became associated with a ticket.

    Aligns with the Unified Ticket Architecture's AssociationSource enum.
    """

    PLAN_REFERENCE = "plan_reference"  # Added during planning phase
    RUNTIME_TRACKING = "runtime_tracking"  # Added during active work via MCP
    COMMIT_BOOTSTRAP = "commit_bootstrap"  # Added when first commit references ticket
    MANUAL = "manual"  # Explicitly added via CLI command
    CRITERION_TARGET = "criterion_target"  # Referenced by a FileExistsTarget criterion


class PostMortemOutcome(str, Enum):
    """Outcome of completed work."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    ABANDONED = "abandoned"


class ImpactLevel(str, Enum):
    """Impact level for discoveries."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BlockerSeverity(str, Enum):
    """Severity level for blockers."""

    BLOCKING = "blocking"
    DEGRADED = "degraded"
    MONITORING = "monitoring"


class FileStatus(str, Enum):
    """Status of an active file during runtime."""

    OPENED = "opened"
    MODIFIED = "modified"
    SAVED = "saved"


# =============================================================================
# ARTIFACT REFERENCE
# =============================================================================


class ArtifactRef(BaseModel):
    """
    Reference to an artifact from a context.

    Used to associate artifacts with tickets without storing raw file paths.
    Token estimates help AI decide whether to load the artifact.
    """

    artifact_id: str = Field(..., description="ULID of the referenced artifact")
    purpose: str = Field(..., description="Why this artifact is relevant")
    tokens_estimate: Optional[int] = Field(
        None, description="Estimated tokens if loaded (helps AI budget context)"
    )


# =============================================================================
# SUPPORTING MODELS
# =============================================================================


class Decision(BaseModel):
    """
    A decision made during implementation.

    Captures the choice, rationale, and alternatives considered.
    """

    decision: str = Field(..., description="What was decided")
    rationale: str = Field(..., description="Why this choice was made")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the decision was made",
    )
    alternatives_considered: List[str] = Field(
        default_factory=list, description="Other options that were evaluated"
    )


class Discovery(BaseModel):
    """
    Something learned during implementation.

    Captures unexpected findings and their resolutions.
    """

    finding: str = Field(..., description="What was discovered")
    impact: ImpactLevel = Field(ImpactLevel.MEDIUM, description="Impact level")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When it was discovered",
    )
    resolution: Optional[str] = Field(None, description="How it was addressed")


class Blocker(BaseModel):
    """
    A current impediment to progress.

    Tracks issues that are blocking or degrading work.
    """

    description: str = Field(..., description="What is blocking progress")
    severity: BlockerSeverity = Field(
        BlockerSeverity.BLOCKING, description="How severe the blocker is"
    )
    identified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the blocker was identified",
    )
    ticket_id: Optional[str] = Field(
        None, description="Ticket created to address this blocker"
    )
    workaround: Optional[str] = Field(None, description="Temporary solution if any")


class ActiveFile(BaseModel):
    """
    A file being actively worked on during runtime.
    """

    path: str = Field(..., description="File path relative to repo root")
    opened_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the file was opened",
    )
    status: FileStatus = Field(FileStatus.OPENED, description="Current file status")


class Checkpoint(BaseModel):
    """
    Progress checkpoint during runtime.
    """

    last_checkpoint: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When checkpoint was taken",
    )
    summary: str = Field("", description="Current progress summary")
    next_steps: List[str] = Field(
        default_factory=list, description="What needs to happen next"
    )
    completion_estimate: int = Field(
        0, ge=0, le=100, description="Percentage complete (0-100)"
    )


class TokenUsage(BaseModel):
    """
    Token usage tracking for a session or post-mortem.
    """

    total_tokens: int = Field(0, ge=0, description="Total tokens used")
    plan_tokens: int = Field(0, ge=0, description="Tokens from loading plan context")
    code_tokens: int = Field(0, ge=0, description="Tokens from reading code files")
    output_tokens: int = Field(0, ge=0, description="Tokens generated as output")


class Risk(BaseModel):
    """
    A known risk identified during planning.
    """

    description: str = Field(..., description="What could go wrong")
    mitigation: str = Field("", description="How to address or avoid the risk")
    likelihood: str = Field("medium", description="low | medium | high")


class RelatedTicket(BaseModel):
    """
    Reference to a related ticket for additional context.
    """

    ticket_id: str = Field(..., description="ULID of the related ticket")
    relationship: str = Field(
        "related_to", description="depends_on | blocks | related_to"
    )
    notes: Optional[str] = Field(None, description="Why this relationship exists")


class PlanArtifact(BaseModel):
    """
    Index entry for a plan artifact file.

    These are markdown files in the plan directory that provide
    detailed analysis beyond the structured plan.yaml.
    """

    file: str = Field(..., description="Filename (e.g., 'DESIGN_ANALYSIS.md')")
    purpose: str = Field(..., description="What this artifact provides")
    tokens_estimate: Optional[int] = Field(
        None, description="Estimated tokens if loaded"
    )
    required_for_start: bool = Field(
        False, description="Must read before starting work"
    )


class KnownFile(BaseModel):
    """
    A file known to be relevant to the ticket.

    Stored in plan context and synced to TicketArtifactAssociation.
    """

    path: str = Field(..., description="File path relative to repo root")
    source: AssociationSource = Field(
        AssociationSource.PLAN_REFERENCE, description="How this file was associated"
    )
    added: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the file was associated",
    )
    notes: Optional[str] = Field(None, description="Optional context about the file")


class FileChange(BaseModel):
    """
    A file changed during work, recorded in post-mortem.
    """

    path: str = Field(..., description="File path")
    change_type: str = Field(
        "modified", description="added | modified | deleted | renamed"
    )
    lines_added: int = Field(0, ge=0)
    lines_removed: int = Field(0, ge=0)


class KeyDecision(BaseModel):
    """
    A key decision recorded in post-mortem.

    Simplified from runtime Decision for summary purposes.
    """

    decision: str = Field(..., description="What was decided")
    rationale: str = Field(..., description="Why this choice was made")
    impact: str = Field("", description="What effect this had")


class LessonLearned(BaseModel):
    """
    A lesson learned during the work.

    Recorded in post-mortem for future reference.
    """

    lesson: str = Field(..., description="What was learned")
    details: str = Field("", description="Additional context")
    applies_to: List[str] = Field(
        default_factory=list, description="Tags for searchability"
    )


class FollowUpItem(BaseModel):
    """
    Work identified but not completed.

    Recorded in post-mortem for future tracking.
    """

    description: str = Field(..., description="What needs to be done")
    priority: str = Field("medium", description="high | medium | low")
    ticket_created: Optional[str] = Field(
        None, description="Ticket ID if follow-up was created"
    )


# =============================================================================
# PLAN CONTEXT
# =============================================================================


class PlanContext(BaseModel):
    """
    Pre-work planning context for a ticket.

    Captures goals, approach, constraints, and references to artifacts
    that provide additional context. When saved with artifact_refs,
    auto-creates TicketArtifactAssociation records with source=PLAN_REFERENCE.

    Storage: .vibey/roadmap/context/plans/{ticket_id}/plan.yaml
    """

    # === IDENTITY ===
    ticket_id: str = Field(..., description="ULID of the ticket")
    version: str = Field("1.0", description="Schema version for migrations")

    # === PLANNING CONTENT ===
    goals: List[str] = Field(default_factory=list, description="What we're achieving")
    approach: str = Field("", description="High-level implementation approach")
    constraints: List[str] = Field(
        default_factory=list, description="Limitations to work within"
    )
    success_criteria: List[str] = Field(
        default_factory=list, description="How we know we're done"
    )
    assumptions: List[str] = Field(
        default_factory=list, description="Things assumed to be true"
    )
    risks: List[Risk] = Field(default_factory=list, description="Known risks")

    # === ARTIFACT ASSOCIATIONS ===
    # Primary method: reference artifacts by ID (preferred)
    artifact_refs: List[ArtifactRef] = Field(
        default_factory=list, description="Referenced artifacts (by ID)"
    )
    # Legacy method: known files by path (for bootstrapping/migration)
    known_files: List[KnownFile] = Field(
        default_factory=list, description="Files expected to be modified"
    )

    # === PLAN ARTIFACTS ===
    # Index of markdown files in the plan directory
    artifacts: List[PlanArtifact] = Field(
        default_factory=list, description="Plan artifact files in directory"
    )

    # === CONTEXT REFERENCES ===
    related_tickets: List[RelatedTicket] = Field(
        default_factory=list, description="Related tickets for context"
    )

    # === LIFECYCLE ===
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When plan was created",
    )
    created_by: Optional[str] = Field(None, description="Who created the plan")
    updated_at: Optional[datetime] = Field(None, description="Last modification")
    approved: bool = Field(False, description="Has plan been reviewed")
    approved_by: Optional[str] = Field(None, description="Who approved")
    approved_at: Optional[datetime] = Field(None, description="When approved")

    # === METADATA ===
    tags: List[str] = Field(default_factory=list, description="Categorization tags")

    def get_all_artifact_ids(self) -> List[str]:
        """Get all artifact IDs referenced in this plan."""
        return [ref.artifact_id for ref in self.artifact_refs]


# =============================================================================
# RUNTIME CONTEXT
# =============================================================================


class RuntimeContext(BaseModel):
    """
    Active session state during ticket execution.

    Tracks files being worked on, decisions made, discoveries,
    blockers, and progress checkpoints.

    Storage: .vibey/roadmap/context/runtime/{ticket_id}.yaml
    """

    # === IDENTITY ===
    ticket_id: str = Field(..., description="ULID of the ticket")
    version: str = Field("1.0", description="Schema version")

    # === SESSION ===
    session_id: str = Field(..., description="Unique session identifier")
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When work began",
    )
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last activity timestamp",
    )
    agent_id: Optional[str] = Field(None, description="Which AI agent is working")

    # === ACTIVE STATE ===
    active_artifacts: List[str] = Field(
        default_factory=list, description="Currently active artifact IDs"
    )
    active_files: List[ActiveFile] = Field(
        default_factory=list, description="Files currently being worked on"
    )

    # === DECISIONS & DISCOVERIES ===
    decisions: List[Decision] = Field(
        default_factory=list, description="Choices made during implementation"
    )
    discoveries: List[str] = Field(
        default_factory=list, description="Simple findings (strings)"
    )
    detailed_discoveries: List[Discovery] = Field(
        default_factory=list, description="Detailed discovery records"
    )

    # === BLOCKERS ===
    blockers: List[Blocker] = Field(
        default_factory=list, description="Current impediments"
    )

    # === PROGRESS ===
    checkpoint: Optional[Checkpoint] = Field(
        None, description="Current progress summary"
    )

    # === TOKEN TRACKING ===
    token_usage: int = Field(0, ge=0, description="Cumulative tokens this session")
    detailed_token_usage: Optional[TokenUsage] = Field(
        None, description="Detailed token breakdown"
    )

    # === TOOL USAGE ===
    tool_invocations: Dict[str, int] = Field(
        default_factory=dict, description="Tool usage counts"
    )

    def add_decision(
        self,
        decision: str,
        rationale: str,
        alternatives: Optional[List[str]] = None,
    ) -> None:
        """Add a decision to the runtime context."""
        self.decisions.append(
            Decision(
                decision=decision,
                rationale=rationale,
                alternatives_considered=alternatives or [],
            )
        )
        self.last_updated = datetime.now(timezone.utc)

    def add_discovery(self, finding: str) -> None:
        """Add a simple discovery string."""
        self.discoveries.append(finding)
        self.last_updated = datetime.now(timezone.utc)

    def add_blocker(
        self,
        description: str,
        severity: BlockerSeverity = BlockerSeverity.BLOCKING,
        workaround: Optional[str] = None,
    ) -> None:
        """Add a blocker to the runtime context."""
        self.blockers.append(
            Blocker(
                description=description,
                severity=severity,
                workaround=workaround,
            )
        )
        self.last_updated = datetime.now(timezone.utc)

    def update_checkpoint(
        self,
        summary: str,
        next_steps: Optional[List[str]] = None,
        completion_estimate: int = 0,
    ) -> None:
        """Update the progress checkpoint."""
        self.checkpoint = Checkpoint(
            summary=summary,
            next_steps=next_steps or [],
            completion_estimate=completion_estimate,
        )
        self.last_updated = datetime.now(timezone.utc)


# =============================================================================
# POST-MORTEM CONTEXT
# =============================================================================


class PostMortemContext(BaseModel):
    """
    Completion summary for a finished ticket.

    Captures what was accomplished, decisions made, lessons learned,
    and follow-up items identified. Generated from runtime context
    and commit history.

    Storage: .vibey/roadmap/context/post-mortems/{ticket_id}.yaml
    """

    # === IDENTITY ===
    ticket_id: str = Field(..., description="ULID of the ticket")
    version: str = Field("1.0", description="Schema version")

    # === COMPLETION ===
    completed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When work finished",
    )
    duration_hours: Optional[float] = Field(None, description="Total time spent")
    session_count: int = Field(1, ge=1, description="Number of sessions")

    # === SUMMARY ===
    summary: str = Field("", description="What was accomplished")
    outcome: PostMortemOutcome = Field(
        PostMortemOutcome.SUCCESS, description="Outcome of the work"
    )

    # === ARTIFACTS ===
    artifacts_changed: List[str] = Field(
        default_factory=list, description="Artifact IDs that were modified"
    )
    files_changed: List[FileChange] = Field(
        default_factory=list, description="Files modified during work"
    )

    # === DECISIONS & LESSONS ===
    key_decisions: List[str] = Field(
        default_factory=list, description="Important choices made (simple strings)"
    )
    detailed_key_decisions: List[KeyDecision] = Field(
        default_factory=list, description="Detailed decision records"
    )
    lessons_learned: List[str] = Field(
        default_factory=list, description="Simple lessons (strings)"
    )
    detailed_lessons: List[LessonLearned] = Field(
        default_factory=list, description="Detailed lesson records"
    )

    # === FOLLOW-UP ===
    follow_up_items: List[str] = Field(
        default_factory=list, description="Work to do later (simple strings)"
    )
    detailed_follow_ups: List[FollowUpItem] = Field(
        default_factory=list, description="Detailed follow-up items"
    )

    # === METRICS ===
    metrics: Optional[Dict[str, Any]] = Field(
        None, description="Quantitative metrics"
    )

    # === METADATA ===
    archived_at: Optional[datetime] = Field(
        None, description="When post-mortem was created"
    )
    archived_by: Optional[str] = Field(None, description="Who created post-mortem")
    runtime_session_ids: List[str] = Field(
        default_factory=list, description="Sessions that contributed"
    )


# =============================================================================
# ASSOCIATION AUTO-CREATION CALLBACK
# =============================================================================

# Type for callback to create associations
CreateAssociationCallback = Callable[[str, str, AssociationSource], None]

# Global callback for auto-creating associations when plan context is saved
_association_callback: Optional[CreateAssociationCallback] = None


def set_association_callback(callback: CreateAssociationCallback) -> None:
    """
    Set the callback for auto-creating TicketArtifactAssociation records.

    When a PlanContext is saved with artifact_refs, this callback will be
    invoked for each reference to create the corresponding association
    with source=PLAN_REFERENCE.

    Args:
        callback: Function(ticket_id, artifact_id, source) -> None
    """
    global _association_callback
    _association_callback = callback


def get_association_callback() -> Optional[CreateAssociationCallback]:
    """Get the current association callback, if set."""
    return _association_callback


def create_associations_from_plan(plan: PlanContext) -> List[tuple]:
    """
    Create associations for all artifact refs in a plan context.

    If a callback is registered, invokes it for each artifact_ref.
    Returns list of (ticket_id, artifact_id) tuples that were processed.

    Args:
        plan: The PlanContext to process

    Returns:
        List of (ticket_id, artifact_id) tuples
    """
    callback = get_association_callback()
    processed = []

    for ref in plan.artifact_refs:
        if callback:
            callback(plan.ticket_id, ref.artifact_id, AssociationSource.PLAN_REFERENCE)
        processed.append((plan.ticket_id, ref.artifact_id))

    return processed


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
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
    # Context models
    "PlanContext",
    "RuntimeContext",
    "PostMortemContext",
    # Association auto-creation
    "CreateAssociationCallback",
    "set_association_callback",
    "get_association_callback",
    "create_associations_from_plan",
]
