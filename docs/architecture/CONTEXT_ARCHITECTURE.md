# Context System Architecture

> Comprehensive architecture for AI session context management

**Version:** 1.0.0
**Status:** Approved
**Sprint:** Context System V2 - Sprint 1
**Task:** 01KCMGX0XQSJDP4XBC9G34T1K7

---

## Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [Three-Phase Lifecycle](#three-phase-lifecycle)
4. [Storage Model](#storage-model)
5. [Hybrid YAML + Markdown Architecture](#hybrid-yaml--markdown-architecture)
6. [Integration with Unified Ticket Architecture](#integration-with-unified-ticket-architecture)
7. [API Surface](#api-surface)
8. [Storage Paths](#storage-paths)
9. [Data Flow](#data-flow)
10. [Configuration](#configuration)

---

## Overview

### Purpose

The Context System enables AI assistants to maintain **contextual understanding across sessions and task boundaries**. It captures the full lifecycle of work: planning, execution, and completion.

### Problems Solved

| Problem | Solution |
|---------|----------|
| AI loses context between sessions | Persistent context storage in YAML + Markdown |
| No record of decisions made during work | Runtime context captures decisions and discoveries |
| Can't resume interrupted work | Plan context preserves goals and approach |
| Post-completion knowledge is lost | Post-mortem summaries capture lessons learned |
| Unclear which commits relate to which tasks | Triangle Model links commits, artifacts, and tickets |

### Key Design Principles

1. **Hybrid Storage** - YAML for metadata (always loaded), Markdown for lengthy artifacts (loaded on demand)
2. **Three-Phase Lifecycle** - Plan, Runtime, Post-Mortem stages mirror actual work patterns
3. **Triangle Integration** - Leverages existing Unified Ticket Architecture entities
4. **Git-Native** - Commits are first-class citizens, linked via file overlap and message references
5. **Token Efficiency** - AI sees what exists; decides what to load based on current need

---

## Core Concepts

### Plan Context

Pre-work preparation and design. Created **before** starting a task.

**Contents:**
- Goals and objectives
- Approach and strategy
- Referenced artifacts (analysis documents, design specs)
- Constraints and requirements
- Known files to be modified

**Purpose:** Enable AI to quickly understand the work scope without re-analyzing the codebase.

### Runtime Context

Active session state. Maintained **during** work.

**Contents:**
- Active files being modified
- Decisions made with rationale
- Discoveries and insights
- Blockers encountered
- Token usage tracking

**Purpose:** Enable handoff between AI sessions or recovery from interruption.

### Post-Mortem Context

Completion summary. Created **after** work finishes.

**Contents:**
- Summary of what was accomplished
- Files changed
- Key decisions with rationale
- Lessons learned
- Follow-up items identified
- Commit links

**Purpose:** Preserve institutional knowledge for future similar work.

---

## Three-Phase Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONTEXT LIFECYCLE                                  │
└─────────────────────────────────────────────────────────────────────────────┘

  PLANNING PHASE              EXECUTION PHASE              COMPLETION PHASE
  ─────────────────────────────────────────────────────────────────────────────

  ┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
  │    PLAN CONTEXT     │     │   RUNTIME CONTEXT   │     │    POST-MORTEM      │
  │                     │     │                     │     │                     │
  │  * Goals            │     │  * Active files     │     │  * Summary          │
  │  * Approach         │     │  * Decisions made   │     │  * Files changed    │
  │  * Artifact refs    │ ──▶ │  * Discoveries      │ ──▶ │  * Key decisions    │
  │  * Constraints      │     │  * Blockers         │     │  * Lessons learned  │
  │  * Known files      │     │  * Token usage      │     │  * Follow-up items  │
  │                     │     │                     │     │  * Commit links     │
  └─────────────────────┘     └─────────────────────┘     └─────────────────────┘
          │                           │                           │
          │                           │                           │
          └───────────────────────────┴───────────────────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │       GIT COMMITS         │
                        │                           │
                        │  * File overlap signals   │
                        │  * Message references     │
                        │  * Manual linking         │
                        └───────────────────────────┘
```

### Phase Transitions

| Transition | Trigger | Action |
|------------|---------|--------|
| None → Planning | `vibey task create-plan <task-id>` | Create plan.yaml with goals and approach |
| Planning → Execution | `vibey roadmap start <task-id>` | Initialize runtime context |
| Execution → Completion | `vibey roadmap complete <task-id>` | Generate post-mortem from runtime context |

### State Preservation

Each phase preserves data for the next:

```
Plan Context                Runtime Context              Post-Mortem
────────────────────────────────────────────────────────────────────
goals                  ───▶ (reference)            ───▶ original goals
known_files            ───▶ active_files           ───▶ files_changed
constraints            ───▶ (reference)            ───▶ (archived)
artifact_refs          ───▶ artifacts_loaded       ───▶ artifacts_referenced
                            decisions              ───▶ key_decisions
                            discoveries            ───▶ lessons_learned
                            blockers               ───▶ follow_up_items
```

---

## Storage Model

### Four-Layer Storage

```
┌─────────────────────────────────────────────────────────────────┐
│                         STORAGE LAYERS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LAYER 1: YAML (Metadata)                                       │
│  ─────────────────────────                                      │
│  * Always loaded                                                │
│  * Structured, small                                            │
│  * Indexes artifacts                                            │
│  * Source of truth                                              │
│                                                                 │
│  LAYER 2: Markdown (Artifacts)                                  │
│  ─────────────────────────────                                  │
│  * Loaded on demand                                             │
│  * Long-form content                                            │
│  * Analysis, designs, plans                                     │
│  * Token-efficient                                              │
│                                                                 │
│  LAYER 3: SQLite (Query Cache)                                  │
│  ─────────────────────────────                                  │
│  * Fast queries                                                 │
│  * Regenerable from YAML                                        │
│  * Indexes and relationships                                    │
│                                                                 │
│  LAYER 4: Git (Version Control)                                 │
│  ─────────────────────────────                                  │
│  * Change history                                               │
│  * Commit linking                                               │
│  * Collaboration                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why This Approach

| Format | Purpose | Trade-off |
|--------|---------|-----------|
| YAML | Metadata, always loaded | Small size required |
| Markdown | Long-form artifacts | Loaded on demand |
| SQLite | Fast queries, relationships | Regenerable, not source of truth |
| Git | History, commit linking | Integral to workflow |

---

## Hybrid YAML + Markdown Architecture

### Design Philosophy

YAML files **index** markdown artifacts:
- AI sees what artifacts exist and their purpose
- AI chooses which to load based on current need
- Large analyses preserved without forced token cost
- Artifacts tracked as first-class entities with provenance

### Example Structure

```yaml
# context/plans/01TASK_AUTH/plan.yaml
plan_context:
  ticket_id: 01TASK_AUTH
  created_at: '2025-12-17T10:00:00Z'
  created_by: claude
  approved: true

  goals:
    - "Implement user authentication"
    - "Support JWT and session-based auth"

  approach: |
    Use existing auth library, add middleware pattern.
    See DESIGN_ANALYSIS.md for detailed evaluation.

  constraints:
    - "Must be backwards compatible"
    - "No breaking changes to existing endpoints"

  known_files:
    - path: src/auth.py
      source: plan_reference
      added: '2025-12-17T10:00:00Z'
    - path: src/middleware.py
      source: plan_reference
      added: '2025-12-17T10:00:00Z'

  # References to markdown artifacts (not loaded by default)
  artifacts:
    - file: DESIGN_ANALYSIS.md
      purpose: "Deep dive on existing auth system, 3 options evaluated"
      tokens_estimate: 4500
    - file: IMPLEMENTATION_PLAN.md
      purpose: "Step-by-step implementation approach with code examples"
      tokens_estimate: 3200
    - file: API_DESIGN.md
      purpose: "Endpoint specifications and request/response formats"
      tokens_estimate: 2100
```

### Artifact Loading Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARTIFACT LOADING FLOW                         │
└─────────────────────────────────────────────────────────────────┘

  1. AI requests plan context
     │
     ▼
  ┌─────────────────────────────────────┐
  │  Load plan.yaml (always)            │
  │  ~500 tokens                        │
  └─────────────────────────────────────┘
     │
     ▼
  2. AI sees artifact index:
     ┌─────────────────────────────────────────────────────────────┐
     │  artifacts:                                                 │
     │    - DESIGN_ANALYSIS.md     "3 options evaluated"  ~4500   │
     │    - IMPLEMENTATION_PLAN.md "Step-by-step"         ~3200   │
     │    - API_DESIGN.md          "Endpoint specs"       ~2100   │
     └─────────────────────────────────────────────────────────────┘
     │
     ▼
  3. AI decides based on current task:
     ┌─────────────────────────────────────────────────────────────┐
     │  "I'm implementing the auth endpoint, I need API_DESIGN.md" │
     └─────────────────────────────────────────────────────────────┘
     │
     ▼
  4. AI requests specific artifact
     │
     ▼
  ┌─────────────────────────────────────┐
  │  Load API_DESIGN.md (on demand)     │
  │  ~2100 tokens                       │
  └─────────────────────────────────────┘

  TOTAL: 2600 tokens (vs 9800 if all loaded)
```

---

## Integration with Unified Ticket Architecture

### Critical Design Decision

Context System V2 **integrates with the existing Unified Ticket Architecture** rather than creating standalone entities.

This means:
- **No standalone `CommitLink`** - Use `TicketCommitLink` relationship entity
- **No standalone `KnownFile`** - Use `TicketArtifactAssociation` relationship entity
- **Leverage existing `Artifact`** entity with provenance tracking
- **Leverage existing `GitCommit`** entity
- **Leverage existing `Completable`/`Criterion`** system

### The Triangle Model

Three relationship entities connect the core entities:

```
                              ┌─────────────────┐
                              │                 │
                              │     Ticket      │
                              │   (Completable) │
                              │                 │
                              └─────────────────┘
                             /                   \
                            /                     \
                           /                       \
            TicketCommitLink                 TicketArtifactAssociation
                         /                           \
                        /                             \
                       /                               \
          ┌─────────────────┐                 ┌─────────────────┐
          │                 │                 │                 │
          │   GitCommit     │─────────────────│    Artifact     │
          │                 │                 │                 │
          └─────────────────┘                 └─────────────────┘
                         CommitArtifactChange
```

### Relationship Entities

#### TicketCommitLink

Links a ticket to a git commit. Created when commits reference tasks.

```python
class TicketCommitLink(BaseModel):
    """Ticket <-> GitCommit relationship."""

    ticket_id: str
    commit_sha: str
    reference_type: ReferenceType  # TASK_REFERENCE | COMPLETION_CLAIM
    signals: LinkSignals           # file_overlap, message_ref, manual
    aggregate_confidence: float
    linked_at: datetime
    link_source: str               # pre_commit_hook | post_commit | manual
```

**Reference Types:**

| Type | Commit Message | Meaning |
|------|----------------|---------|
| `TASK_REFERENCE` | `Task: 01TASK_A` | Work was done on this task |
| `COMPLETION_CLAIM` | `Completes: 01TASK_A` | Task is claimed complete |

#### TicketArtifactAssociation

Links a ticket to an artifact. Tracks how artifacts become associated.

```python
class TicketArtifactAssociation(BaseModel):
    """Ticket <-> Artifact relationship."""

    ticket_id: str
    artifact_id: str
    association_source: AssociationSource
    added_at: datetime
    added_by: Optional[str] = None
```

**Association Sources:**

| Source | When | Mechanism |
|--------|------|-----------|
| `plan_reference` | Before work | Plan context references artifact |
| `runtime_tracking` | During work | AI logs files via MCP |
| `commit_bootstrap` | First commit | Message ref + staged files establishes association |
| `manual` | Anytime | CLI command `vibey task add-artifact` |
| `criterion_target` | Criterion defined | FileExistsTarget references artifact |

#### CommitArtifactChange

Links a commit to artifacts it changed. Derived from git diff.

```python
class CommitArtifactChange(BaseModel):
    """GitCommit <-> Artifact relationship."""

    commit_sha: str
    artifact_id: str
    change_type: ChangeType  # ADDED | MODIFIED | DELETED | RENAMED
    previous_path: Optional[str] = None  # For renames
    lines_added: Optional[int] = None
    lines_removed: Optional[int] = None
    recorded_at: datetime
```

### Link Detection Signals

Three signals for detecting commit-ticket relationships:

```python
class LinkSignals(BaseModel):
    """Signals for commit-ticket linking."""

    file_overlap: Optional[FileOverlapSignal] = None
    message_ref: Optional[MessageRefSignal] = None
    manual: Optional[ManualSignal] = None


class FileOverlapSignal(BaseModel):
    """Signal: commit artifacts match ticket associations."""

    matched: bool
    overlapping_artifact_ids: List[str]
    confidence: float  # len(overlap) / len(commit_artifacts)


class MessageRefSignal(BaseModel):
    """Signal: commit message references task ID."""

    matched: bool
    ticket_ids: List[str]
    reference_type: ReferenceType
    confidence: float = 1.0


class ManualSignal(BaseModel):
    """Signal: user explicitly linked commit to ticket."""

    matched: bool
    linked_by: Optional[str] = None
    linked_at: Optional[datetime] = None
    confidence: float = 1.0
```

**Note:** Timestamp-based linking was explicitly **rejected** as it caused ambiguity with parallel tasks.

### Commit Message Format

```
feat(auth): Add JWT validation

Task: 01TASK_A
Task: 01TASK_B

Completes: 01TASK_A

<body>
```

| Marker | Purpose | Creates |
|--------|---------|---------|
| `Task:` | Associates commit with task | `TicketCommitLink` with `TASK_REFERENCE` |
| `Completes:` | Claims task completion | `TicketCommitLink` with `COMPLETION_CLAIM` |

### Triangle Query Examples

| Query | Method |
|-------|--------|
| What commits touched this ticket? | `TicketCommitLink WHERE ticket_id = X` |
| What artifacts are associated with this ticket? | `TicketArtifactAssociation WHERE ticket_id = X` |
| What artifacts did this commit change? | `CommitArtifactChange WHERE commit_sha = X` |
| What tickets were affected by changes to this artifact? | `Artifact -> TicketArtifactAssociation -> Ticket` |
| Did commit X change artifacts outside its referenced tickets? | `CommitArtifactChange NOT IN (TicketCommitLink -> TicketArtifactAssociation)` |
| Full history of this artifact? | `CommitArtifactChange WHERE artifact_id = X ORDER BY recorded_at` |

---

## API Surface

### ContextManager Class

```python
class ContextManager:
    """Manages context lifecycle for tickets."""

    def __init__(self, roadmap_dir: Path):
        self.paths = ContextPaths(roadmap_dir)

    # ─────────────────────────────────────────────────────────────
    # PLAN CONTEXT
    # ─────────────────────────────────────────────────────────────

    def get_plan_context(self, ticket_id: str) -> Optional[PlanContext]:
        """
        Get pre-work planning context for ticket.

        Returns None if no plan exists.
        Always loads YAML; never loads artifacts automatically.
        """
        pass

    def create_plan_context(
        self,
        ticket_id: str,
        goals: List[str],
        approach: str,
        constraints: Optional[List[str]] = None,
        known_files: Optional[List[str]] = None
    ) -> PlanContext:
        """
        Create new plan context for ticket.

        Creates directory structure and plan.yaml.
        """
        pass

    def get_plan_artifacts(self, ticket_id: str) -> List[ArtifactRef]:
        """
        List available artifacts without loading content.

        Returns metadata: filename, purpose, token estimate.
        AI uses this to decide what to load.
        """
        pass

    def load_artifact(self, ticket_id: str, filename: str) -> str:
        """
        Load specific artifact content on demand.

        Returns raw markdown content.
        """
        pass

    def add_plan_artifact(
        self,
        ticket_id: str,
        filename: str,
        content: str,
        purpose: str
    ) -> ArtifactRef:
        """
        Add markdown artifact to plan context.

        Creates file and updates plan.yaml index.
        Estimates token count automatically.
        """
        pass

    # ─────────────────────────────────────────────────────────────
    # RUNTIME CONTEXT
    # ─────────────────────────────────────────────────────────────

    def get_runtime_context(self, ticket_id: str) -> Optional[RuntimeContext]:
        """
        Get current execution context for ticket.

        Returns None if task not started or context not initialized.
        """
        pass

    def init_runtime_context(
        self,
        ticket_id: str,
        session_id: Optional[str] = None
    ) -> RuntimeContext:
        """
        Initialize runtime context when task starts.

        Called automatically by `vibey roadmap start`.
        Copies known_files from plan context to active_files.
        """
        pass

    def update_runtime_context(
        self,
        ticket_id: str,
        active_files: Optional[List[str]] = None,
        decision: Optional[Decision] = None,
        discovery: Optional[str] = None,
        blocker: Optional[str] = None
    ) -> RuntimeContext:
        """
        Update runtime context during execution.

        Appends to lists; does not replace.
        Updates last_updated timestamp.
        """
        pass

    def log_file_access(self, ticket_id: str, file_path: str) -> None:
        """
        Log file access during runtime.

        Adds to active_files if not present.
        Creates TicketArtifactAssociation with source=runtime_tracking.
        """
        pass

    # ─────────────────────────────────────────────────────────────
    # POST-MORTEM CONTEXT
    # ─────────────────────────────────────────────────────────────

    def get_post_mortem(self, ticket_id: str) -> Optional[PostMortem]:
        """
        Get completion summary for ticket.

        Returns None if task not completed.
        """
        pass

    def save_post_mortem(
        self,
        ticket_id: str,
        summary: str,
        key_decisions: Optional[List[str]] = None,
        lessons_learned: Optional[List[str]] = None,
        follow_up_items: Optional[List[str]] = None
    ) -> PostMortem:
        """
        Save completion summary for ticket.

        Auto-populates:
        - files_changed from runtime context and commit links
        - duration_hours from started_at/completed_at
        - commit_links from TicketCommitLink records
        """
        pass

    def generate_post_mortem(self, ticket_id: str) -> PostMortem:
        """
        Auto-generate post-mortem from runtime context.

        Uses decisions, discoveries, blockers to populate fields.
        Requires manual summary and lessons_learned review.
        """
        pass

    # ─────────────────────────────────────────────────────────────
    # COMMIT LINKING
    # ─────────────────────────────────────────────────────────────

    def link_commit(
        self,
        ticket_id: str,
        commit_sha: str,
        reference_type: ReferenceType,
        signals: LinkSignals,
        link_source: str = "manual"
    ) -> TicketCommitLink:
        """
        Create link between ticket and commit.

        Usually called by pre-commit hook or reconciliation.
        """
        pass

    def get_commit_links(self, ticket_id: str) -> List[TicketCommitLink]:
        """
        Get all commits linked to ticket.
        """
        pass

    def validate_commit_consistency(
        self,
        staged_files: List[str],
        message_refs: List[str]
    ) -> ConsistencyReport:
        """
        Validate commit files match referenced ticket associations.

        Returns discrepancies for resolution.
        Used by pre-commit hook.
        """
        pass
```

### Data Models

```python
@dataclass
class PlanContext:
    """Pre-work planning context."""

    ticket_id: str
    created_at: datetime
    created_by: str
    approved: bool

    goals: List[str]
    approach: str
    constraints: List[str]
    known_files: List[KnownFile]
    artifacts: List[ArtifactRef]


@dataclass
class ArtifactRef:
    """Reference to markdown artifact (not loaded)."""

    file: str
    purpose: str
    tokens_estimate: int


@dataclass
class KnownFile:
    """File associated with ticket."""

    path: str
    source: str  # plan_reference | runtime_tracking | etc.
    added: datetime


@dataclass
class RuntimeContext:
    """Active session state."""

    ticket_id: str
    session_id: str
    started_at: datetime
    last_updated: datetime

    active_files: List[str]
    decisions: List[Decision]
    discoveries: List[str]
    blockers: List[str]
    token_usage: int


@dataclass
class Decision:
    """Decision made during execution."""

    decision: str
    rationale: str
    timestamp: datetime


@dataclass
class PostMortem:
    """Completion summary."""

    ticket_id: str
    completed_at: datetime
    duration_hours: float

    summary: str
    files_changed: List[str]
    key_decisions: List[str]
    lessons_learned: List[str]
    follow_up_items: List[str]
    commit_links: List[TicketCommitLink]
```

---

## Storage Paths

### Directory Structure

```
.vibey/roadmap/context/
├── plans/                           # Pre-work artifacts
│   └── {ticket_id}/
│       ├── plan.yaml                # Structured metadata + artifact index
│       ├── DESIGN_ANALYSIS.md       # Artifact: analysis document
│       ├── IMPLEMENTATION_PLAN.md   # Artifact: step-by-step plan
│       └── API_DESIGN.md            # Artifact: specifications
│
├── runtime/                         # Active session state
│   └── {ticket_id}.yaml             # Single file per active task
│
└── post-mortems/                    # Completion summaries
    └── {ticket_id}.yaml             # Single file per completed task
```

### Path Utilities

```python
class ContextPaths:
    """Path utilities for context storage."""

    def __init__(self, roadmap_dir: Path):
        self.base = roadmap_dir / "context"

    def plans_dir(self, ticket_id: Optional[str] = None) -> Path:
        """Get plans directory, optionally for specific ticket."""
        path = self.base / "plans"
        if ticket_id:
            path = path / ticket_id
        return path

    def plan_yaml(self, ticket_id: str) -> Path:
        """Get plan.yaml path for ticket."""
        return self.plans_dir(ticket_id) / "plan.yaml"

    def plan_artifact(self, ticket_id: str, filename: str) -> Path:
        """Get artifact path within plan directory."""
        return self.plans_dir(ticket_id) / filename

    def runtime_dir(self) -> Path:
        """Get runtime context directory."""
        return self.base / "runtime"

    def runtime_yaml(self, ticket_id: str) -> Path:
        """Get runtime context path for ticket."""
        return self.runtime_dir() / f"{ticket_id}.yaml"

    def post_mortems_dir(self) -> Path:
        """Get post-mortems directory."""
        return self.base / "post-mortems"

    def post_mortem_yaml(self, ticket_id: str) -> Path:
        """Get post-mortem path for ticket."""
        return self.post_mortems_dir() / f"{ticket_id}.yaml"
```

### YAML Schemas

#### Plan Context Schema

```yaml
# context/plans/{ticket_id}/plan.yaml
plan_context:
  ticket_id: "01TASK123"
  created_at: "2025-12-17T10:00:00Z"
  created_by: "claude"
  approved: false

  goals:
    - "Implement user authentication"
    - "Support JWT and session-based auth"

  approach: |
    Use existing auth library, add middleware pattern.
    See DESIGN_ANALYSIS.md for detailed evaluation.

  constraints:
    - "Must be backwards compatible"
    - "No breaking changes to existing endpoints"

  known_files:
    - path: "src/auth.py"
      source: "plan_reference"
      added: "2025-12-17T10:00:00Z"
    - path: "src/middleware.py"
      source: "plan_reference"
      added: "2025-12-17T10:00:00Z"

  artifacts:
    - file: "DESIGN_ANALYSIS.md"
      purpose: "Deep dive on existing auth system"
      tokens_estimate: 4500
    - file: "IMPLEMENTATION_PLAN.md"
      purpose: "Step-by-step implementation approach"
      tokens_estimate: 3200
```

#### Runtime Context Schema

```yaml
# context/runtime/{ticket_id}.yaml
runtime_context:
  ticket_id: "01TASK123"
  session_id: "sess_abc123"
  started_at: "2025-12-17T11:00:00Z"
  last_updated: "2025-12-17T14:30:00Z"

  active_files:
    - "src/auth.py"
    - "src/jwt_handler.py"
    - "src/middleware.py"

  decisions:
    - decision: "Chose PyJWT over python-jose"
      rationale: "Better maintained, simpler API"
      timestamp: "2025-12-17T12:15:00Z"
    - decision: "Use decorator pattern for auth"
      rationale: "Cleaner than middleware for granular control"
      timestamp: "2025-12-17T13:45:00Z"

  discoveries:
    - "Existing rate limiter conflicts with auth middleware order"
    - "User model already has token fields from previous implementation"

  blockers:
    - "Need DB migration for user tokens table"

  token_usage: 45000
```

#### Post-Mortem Schema

```yaml
# context/post-mortems/{ticket_id}.yaml
post_mortem:
  ticket_id: "01TASK123"
  completed_at: "2025-12-17T16:00:00Z"
  duration_hours: 5.0

  summary: |
    Implemented JWT authentication with decorator pattern.
    All endpoints now require auth, tests passing.
    Chose PyJWT for token handling after evaluating alternatives.

  files_changed:
    - "src/auth.py"
    - "src/jwt_handler.py"
    - "src/middleware.py"
    - "tests/test_auth.py"

  key_decisions:
    - "PyJWT for token handling (simpler API, better maintained)"
    - "Decorator pattern for auth (granular control per endpoint)"
    - "Middleware order: auth before rate limiting"

  lessons_learned:
    - "Middleware order matters - auth must come before rate limiting"
    - "Check for existing partial implementations before starting"

  follow_up_items:
    - "Add refresh token support"
    - "Document auth flow in API docs"
    - "Add rate limiting per authenticated user"

  commit_links:
    - sha: "abc1234"
      message: "feat(auth): Add JWT validation"
      reference_type: "TASK_REFERENCE"
      signals:
        file_overlap:
          matched: true
          confidence: 1.0
        message_ref:
          matched: true
          confidence: 1.0
    - sha: "def5678"
      message: "feat(auth): Add auth decorator\n\nCompletes: 01TASK123"
      reference_type: "COMPLETION_CLAIM"
      signals:
        file_overlap:
          matched: true
          confidence: 1.0
        message_ref:
          matched: true
          confidence: 1.0
```

---

## Data Flow

### Complete Lifecycle Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE DATA FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────┘

  USER/AI                          CONTEXT SYSTEM                    STORAGE
  ───────                          ──────────────                    ───────

  1. CREATE PLAN
  │
  ├─ vibey task create-plan ─────▶ ContextManager.create_plan_context()
  │                                       │
  │                                       ├───▶ Create plans/{id}/ directory
  │                                       ├───▶ Write plan.yaml
  │                                       └───▶ Create TicketArtifactAssociation
  │                                             (source: plan_reference)
  │
  ├─ Add artifact ───────────────▶ ContextManager.add_plan_artifact()
  │                                       │
  │                                       ├───▶ Write {artifact}.md
  │                                       └───▶ Update plan.yaml index


  2. START TASK
  │
  ├─ vibey roadmap start ────────▶ ContextManager.init_runtime_context()
  │                                       │
  │                                       ├───▶ Load plan context
  │                                       ├───▶ Copy known_files → active_files
  │                                       └───▶ Write runtime/{id}.yaml


  3. DURING EXECUTION
  │
  ├─ Log file access ────────────▶ ContextManager.log_file_access()
  │                                       │
  │                                       ├───▶ Update runtime context
  │                                       └───▶ Create TicketArtifactAssociation
  │                                             (source: runtime_tracking)
  │
  ├─ Log decision ───────────────▶ ContextManager.update_runtime_context()
  │                                       │
  │                                       └───▶ Append to runtime/{id}.yaml


  4. COMMIT CODE
  │
  ├─ git commit ─────────────────▶ Pre-commit hook
  │                                       │
  │                                       ├───▶ Parse Task:/Completes: lines
  │                                       ├───▶ Get staged files
  │                                       ├───▶ Validate triangle consistency
  │                                       │           │
  │                                       │           ├─ Staged ∩ Associations?
  │                                       │           ├─ Staged - Associations?
  │                                       │           └─ Associations - Staged?
  │                                       │
  │                                       ├───▶ Create TicketCommitLink
  │                                       ├───▶ Create CommitArtifactChange
  │                                       └───▶ Update TicketArtifactAssociation
  │                                             (if user approved additions)


  5. COMPLETE TASK
  │
  ├─ vibey roadmap complete ─────▶ ContextManager.save_post_mortem()
  │                                       │
  │                                       ├───▶ Load runtime context
  │                                       ├───▶ Aggregate commit links
  │                                       ├───▶ Calculate duration
  │                                       └───▶ Write post-mortems/{id}.yaml
```

### Pre-Commit Hook Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      UNIFIED PRE-COMMIT HOOK                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 1: Collect Data                                                      │
│  ─────────────────────                                                      │
│    * Parse commit message → Task: and Completes: references                 │
│    * Get staged files → resolve to Artifact IDs (or create new)             │
│    * Build pending CommitArtifactChange records                             │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 2: Triangle Validation                                               │
│  ────────────────────────────                                               │
│    For each Task: ticket_id:                                                │
│                                                                             │
│      A = Artifacts in staged files (CommitArtifactChange)                   │
│      B = Artifacts associated with ticket (TicketArtifactAssociation)       │
│                                                                             │
│      Check 1: A ∩ B — Files in both (expected, good)                        │
│      Check 2: A - B — Staged NOT in ticket associations                     │
│               → Prompt: "Add to ticket associations?"                       │
│      Check 3: B - A — Ticket associations NOT in staged                     │
│               → Info only (not all files change each time)                  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 3: Completion Verification                                           │
│  ────────────────────────────────                                           │
│    For each Completes: ticket_id:                                           │
│                                                                             │
│      * ticket.can_transition_to(COMPLETED) must return True                 │
│      * Block commit if criteria not met                                     │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 4: Persist Relationships                                             │
│  ──────────────────────────────                                             │
│    * Create TicketCommitLink for each Task:/Completes: reference            │
│    * Create CommitArtifactChange for each staged file                       │
│    * Update TicketArtifactAssociation if user approved additions            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Git Hooks Configuration

```yaml
# .vibey/config/git_hooks.yaml
pre_commit:
  enabled: true

  # Phase 2: File/artifact consistency
  artifact_consistency:
    mode: prompt  # off | warn | prompt | strict
    on_mismatch:
      staged_not_in_associations: prompt
      associations_not_in_staged: ignore
      no_task_ref: warn

  # Phase 3: Completion verification
  completion_verification:
    mode: strict  # off | warn | strict
    block_on_unmet_criteria: true

  # Commit message template
  template:
    auto_install: true
    path: .gitmessage
```

### Configuration Modes

| Mode | Behavior |
|------|----------|
| **off** | Check skipped entirely |
| **warn** | Show issues, commit proceeds |
| **prompt** | Show issues, ask for resolution |
| **strict** | Block commit until resolved |

### Resolution Options

When discrepancies are detected:

| Option | Action |
|--------|--------|
| **Update Associations** | Add staged files to ticket's artifact associations |
| **Update Message** | Change task reference in commit message |
| **Add Reference** | Include additional task reference |
| **Proceed** | Override, commit as-is (for warn/prompt modes) |
| **Cancel** | Abort commit |

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| [UNIFIED_TICKET_ARCHITECTURE.md](../roadmap/sqlite-backend/sqlite-backend-6/UNIFIED_TICKET_ARCHITECTURE.md) | Core ticket and criterion system |
| [DESIGN_DECISIONS.md](../../.vibey/roadmap/context/tracks/context-system-v2/sprints/sprint-0-planning-design-review/DESIGN_DECISIONS.md) | Sprint 0 design decisions |
| [ADR-0003](adr/0003-dual-storage-sqlite-yaml.md) | YAML + SQLite dual storage rationale |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-19 | Initial architecture document |
