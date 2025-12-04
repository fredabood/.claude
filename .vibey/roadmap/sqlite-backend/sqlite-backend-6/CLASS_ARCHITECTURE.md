# Unified Ticket Architecture - Class Reference

**Created:** 2025-12-02
**Sprint:** sqlite-backend-6
**Source:** UNIFIED_TICKET_ARCHITECTURE.md
**Status:** AUTHORITATIVE

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Layer Diagram](#layer-diagram)
3. [Layer 0a: Artifact System](#layer-0a-artifact-system)
4. [Layer 0b: Core Abstractions](#layer-0b-core-abstractions)
5. [Layer 1: Ticket](#layer-1-ticket)
6. [Layer 2: HierarchicalTicket](#layer-2-hierarchicalticket)
7. [Layer 3: Domain Models](#layer-3-domain-models)
8. [Supporting Classes](#supporting-classes)
9. [Enumerations](#enumerations)
10. [Class Relationship Matrix](#class-relationship-matrix)
11. [Database Entity Mapping](#database-entity-mapping)

---

## Architecture Overview

The Unified Ticket Architecture implements a **layered class hierarchy** where:

- **Everything completable** derives from `Completable`
- **All blocking relationships** are expressed through `Criterion` with `blocks_transition_to`
- **Artifacts exist independently** of tickets as first-class entities
- **Identity is immutable** (ULID-based), separate from ordering and display

### Design Principles

| Principle | Implementation |
|-----------|----------------|
| Completion is computed, not declared | `can_transition_to(status)` checks all criteria |
| User controls criteria | Criteria define what "complete" means |
| Single unified interface | One method for all state transitions |
| Deterministic AI guardrails | AI cannot bypass criteria checks |

---

## Layer Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LAYER 3: DOMAIN MODELS                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────┐│
│  │  RoadmapTicket  │ │   TrackTicket   │ │  SprintTicket   │ │ TaskTicket  ││
│  │  - version      │ │  - priority     │ │  - plan_file    │ │ - task_type ││
│  │  - activity_log │ │  - strategic_   │ │  - gate checks  │ │ - tokens    ││
│  │  - deployed_    │ │    value        │ │  - deploy times │ │ - complexity││
│  │    platforms    │ │                 │ │                 │ │ - phase     ││
│  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘ └──────┬──────┘│
│           │                   │                   │                  │       │
│           └───────────────────┴───────────────────┴──────────────────┘       │
│                                       │                                       │
│                                       ▼                                       │
├───────────────────────────────────────────────────────────────────────────────┤
│                         LAYER 2: HIERARCHICAL TICKET                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         HierarchicalTicket                               │ │
│  │  - parent_id: str              - sequence: int           - slug: str    │ │
│  │  + siblings → List[Self]       + next_sibling → Self?    + reorder()    │ │
│  │  + commits → List[GitCommit]   + requirements_effective  + all_criteria │ │
│  │  + deliverables, tests, subtasks, dependencies, success_criteria        │ │
│  │  + production_gates            + computed_tokens          + effective_  │ │
│  │  + all_referenced_artifacts    + stale_documentation_artifacts priority │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                       │
│                                       ▼                                       │
├───────────────────────────────────────────────────────────────────────────────┤
│                              LAYER 1: TICKET                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                              Ticket                                      │ │
│  │  - status: TicketStatus        - created_at, started_at, completed_at   │ │
│  │  - commits_local: List[GitCommit]     - assigned_agents_local: List[str]│ │
│  │  - parent_ref: str?            - requirements_local: List[Requirement]  │ │
│  │  - priority: Priority?         - deferred: bool                         │ │
│  │  - estimated_duration_local    - actual_duration_local                  │ │
│  │  + start() → (bool, List[str])        + complete() → (bool, List[str])  │ │
│  │  + is_parent, is_child, is_ultimate_parent, is_ultimate_child           │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                       │
│                                       ▼                                       │
├───────────────────────────────────────────────────────────────────────────────┤
│                          LAYER 0b: COMPLETABLE                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                            Completable                                   │ │
│  │  - id: str (ULID)              - name: str             - description    │ │
│  │  - criteria: List[Criterion]                                            │ │
│  │  + children → List[str]        (computed from CompletableTarget criteria)│ │
│  │  + can_transition_to(status) → (bool, List[str])                        │ │
│  │  + progress_for_transition(status) → Progress                           │ │
│  │  + progress → Progress         (default: toward COMPLETED)              │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                       │
│                    ┌──────────────────┴──────────────────┐                   │
│                    ▼                                     ▼                   │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐  │
│  │           Criterion             │   │       CriterionTarget           │  │
│  │  - id: str                      │   │       (abstract base)           │  │
│  │  - description: str             │   │  + is_satisfied() → bool        │  │
│  │  - blocks_transition_to: Status │   │  + is_automatic → bool          │  │
│  │  - target: CriterionTarget      │   │  + refresh(context)             │  │
│  │  - required: bool               │   └─────────────┬───────────────────┘  │
│  │  + is_met → bool                │                 │                      │
│  │  + evaluate(log) → bool         │                 │                      │
│  └─────────────────────────────────┘                 │                      │
│                                                      ▼                      │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      CriterionTarget Subtypes                         │   │
│  │  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐            │   │
│  │  │CompletableTarget│ │FileExistsTarget│ │TestPassesTarget│            │   │
│  │  │- completable_id │ │- paths: List   │ │- test_command  │            │   │
│  │  │- required_status│ │- all_required  │ │- pass_threshold│            │   │
│  │  │- current_status │ │- deliverable_  │ │- coverage_     │            │   │
│  │  │                 │ │  type          │ │  threshold     │            │   │
│  │  └─────────────────┘ └────────────────┘ └────────────────┘            │   │
│  │  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐            │   │
│  │  │ThresholdTarget │ │  ManualTarget  │ │ ExternalTarget │            │   │
│  │  │- metric_name   │ │- assessor      │ │- system_name   │            │   │
│  │  │- threshold     │ │- instructions  │ │- endpoint      │            │   │
│  │  │- comparison    │ │- assessed: bool│ │- expected_     │            │   │
│  │  │- current_value │ │- met: bool     │ │  status        │            │   │
│  │  └────────────────┘ └────────────────┘ └────────────────┘            │   │
│  │  ┌────────────────┐                                                   │   │
│  │  │ ArtifactTarget │  (References Layer 0a Artifact)                   │   │
│  │  │- artifact_id   │                                                   │   │
│  │  │- verification  │                                                   │   │
│  │  └────────────────┘                                                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
├───────────────────────────────────────────────────────────────────────────────┤
│                          LAYER 0a: ARTIFACT                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                             Artifact                                     │ │
│  │  - id: str (ULID)              - name: str             - description    │ │
│  │  - paths: List[str]            - content_hash          - last_verified  │ │
│  │  - artifact_type: ArtifactType - artifact_subtype                       │ │
│  │  - provenance: ArtifactProvenance                                       │ │
│  │  - documents_artifact_id       - depends_on_artifact_ids                │ │
│  │  - exists: bool                - is_stale: bool                         │ │
│  │  + is_orphan → bool            + referencing_criteria → List[str]       │ │
│  │  + is_documentation → bool     + check_staleness()    + mark_updated()  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        ArtifactProvenance                                │ │
│  │  - provenance_type: ProvenanceType                                      │ │
│  │  - created_by_ticket_id        - created_by_criterion_id                │ │
│  │  - discovered_at, discovered_by  (PRE_EXISTING)                         │ │
│  │  - generator_type, generator_config, source_artifact_ids (GENERATED)    │ │
│  │  - external_source, external_version (EXTERNAL)                         │ │
│  │  - framework_component_type (FRAMEWORK)                                 │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Layer 0a: Artifact System

### Artifact

**Purpose:** First-class entity for any file-based artifact in the project.

```python
class Artifact(BaseModel):
    # Identity
    id: str                              # ULID format
    name: str
    description: Optional[str]

    # File Location
    paths: List[str]                     # One artifact may span multiple files
    content_hash: Optional[str]          # SHA256 of concatenated contents
    last_verified: Optional[datetime]

    # Classification
    artifact_type: ArtifactType
    artifact_subtype: Optional[str]

    # Provenance
    provenance: ArtifactProvenance

    # Relationships
    documents_artifact_id: Optional[str] # What this artifact documents
    depends_on_artifact_ids: List[str]

    # State
    exists: bool = True
    is_stale: bool = False

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Computed Properties
    @computed_field
    def is_orphan(self) -> bool: ...

    @computed_field
    def referencing_criteria(self) -> List[str]: ...

    @computed_field
    def is_documentation(self) -> bool: ...

    # Methods
    def check_staleness(self, registry) -> bool: ...
    def mark_updated(self, registry) -> None: ...
```

**Relationships:**
- `documents_artifact_id` → references another `Artifact`
- `depends_on_artifact_ids` → references multiple `Artifact` entities
- Referenced by `ArtifactTarget.artifact_id`

---

### ArtifactProvenance

**Purpose:** Tracks how an artifact came to exist.

```python
class ArtifactProvenance(BaseModel):
    provenance_type: ProvenanceType

    # TICKET_CREATED
    created_by_ticket_id: Optional[str]
    created_by_criterion_id: Optional[str]

    # PRE_EXISTING
    discovered_at: Optional[datetime]
    discovered_by: Optional[str]

    # GENERATED
    generator_type: Optional[str]        # "sphinx", "pdoc", "typedoc"
    generator_config: Optional[Dict]
    source_artifact_ids: Optional[List[str]]

    # EXTERNAL
    external_source: Optional[str]
    external_version: Optional[str]

    # FRAMEWORK
    framework_component_type: Optional[str]  # "agent", "workflow", "template"
```

---

## Layer 0b: Core Abstractions

### Completable

**Purpose:** Base class for anything that can be completed via criteria.

```python
class Completable(BaseModel):
    # Identity (ULID-based, immutable)
    id: str                              # Format: {type}_{ulid}
    name: str                            # Display name (mutable)
    description: Optional[str]

    # THE source of truth for ALL blocking
    criteria: List[Criterion] = []

    # Computed Properties
    @computed_field
    def children(self) -> List[str]:
        """Derived from CompletableTarget criteria."""
        ...

    # Core Methods
    def can_transition_to(self, status: TicketStatus) -> tuple[bool, List[str]]:
        """THE unified interface for checking state transitions."""
        ...

    def progress_for_transition(self, status: TicketStatus) -> Progress:
        """Progress computed per transition type."""
        ...

    @property
    def progress(self) -> Progress:
        """Default: progress toward COMPLETED."""
        ...
```

**Relationships:**
- Contains `List[Criterion]`
- Extended by `Ticket`

---

### Criterion

**Purpose:** A single requirement for state transition.

```python
class Criterion(BaseModel):
    # Identity
    id: str
    description: str

    # THE key field for unified blocking
    blocks_transition_to: TicketStatus = TicketStatus.COMPLETED

    # What satisfies this criterion (polymorphic)
    target: CriterionTarget

    # Optionality
    required: bool = True

    # Computed
    @property
    def is_met(self) -> bool:
        """Criterion is met when target is satisfied."""
        ...

    def evaluate(self, activity_log: List[ActivityLogEntry]) -> bool:
        """Evaluate with logging for non-required criteria."""
        ...
```

**Relationships:**
- Contained by `Completable.criteria`
- Contains one `CriterionTarget` (polymorphic)

---

### CriterionTarget (Abstract Base)

**Purpose:** Base for all criterion targets - defines what satisfies a criterion.

```python
class CriterionTarget(BaseModel):
    @abstractmethod
    def is_satisfied(self) -> bool: ...

    @property
    @abstractmethod
    def is_automatic(self) -> bool:
        """Can this target auto-evaluate without human intervention?"""
        ...

    def refresh(self, context: RefreshContext) -> None:
        """Refresh cached state from external source."""
        pass
```

---

### CriterionTarget Subtypes

#### CompletableTarget

**Purpose:** Criterion met when another Completable reaches required status.

```python
class CompletableTarget(CriterionTarget):
    completable_id: str
    required_status: TicketStatus = TicketStatus.COMPLETED

    # Cached state
    current_status: Optional[TicketStatus]
    last_checked: Optional[datetime]

    @property
    def is_automatic(self) -> bool:
        return True
```

**Use Cases:**
- `blocks_transition_to: IN_PROGRESS` → **Dependency** (must complete before I start)
- `blocks_transition_to: COMPLETED` → **Child** (must complete before I complete)

---

#### FileExistsTarget

**Purpose:** Criterion met when file(s) exist.

```python
class FileExistsTarget(CriterionTarget):
    paths: List[str]
    all_required: bool = True
    deliverable_type: DeliverableType = DeliverableType.OTHER

    # Cached state
    existing_paths: List[str] = []
    missing_paths: List[str] = []
    last_checked: Optional[datetime]

    @property
    def is_automatic(self) -> bool:
        return True
```

---

#### TestPassesTarget

**Purpose:** Criterion met when test passes with optional thresholds.

```python
class TestPassesTarget(CriterionTarget):
    test_command: str
    pass_threshold: float = 100.0
    coverage_threshold: Optional[float]

    # Cached state
    last_result: Optional[TestResult]

    @property
    def is_automatic(self) -> bool:
        return True
```

---

#### ThresholdTarget

**Purpose:** Criterion met when a metric meets a threshold.

```python
class ThresholdTarget(CriterionTarget):
    metric_name: str
    threshold: float
    comparison: ThresholdComparison = ThresholdComparison.GTE

    # Cached state
    current_value: Optional[float]
    last_checked: Optional[datetime]

    @property
    def is_automatic(self) -> bool:
        return True
```

---

#### ManualTarget

**Purpose:** Criterion met when manually assessed by human.

```python
class ManualTarget(CriterionTarget):
    assessor: Optional[str]
    instructions: Optional[str]

    # Assessment state
    assessed: bool = False
    met: Optional[bool]
    assessed_at: Optional[datetime]
    assessed_by: Optional[str]
    evidence: Optional[str]

    @property
    def is_automatic(self) -> bool:
        return False  # Requires human
```

---

#### ExternalTarget

**Purpose:** Criterion met when external system reports success.

```python
class ExternalTarget(CriterionTarget):
    system_name: str
    endpoint: Optional[str]
    expected_status: str = "success"

    # Cached state
    current_status: Optional[str]
    last_checked: Optional[datetime]

    @property
    def is_automatic(self) -> bool:
        return True
```

---

#### ArtifactTarget

**Purpose:** Criterion that references a first-class Artifact.

```python
class ArtifactTarget(CriterionTarget):
    artifact_id: str                     # References Artifact.id
    verification: ArtifactVerification = ArtifactVerification.EXISTS

    # Cached state (denormalized from Artifact)
    artifact_exists: bool = False
    artifact_hash: Optional[str]
    artifact_is_stale: bool = False
    last_checked: Optional[datetime]

    @property
    def is_automatic(self) -> bool:
        return True
```

---

## Layer 1: Ticket

### Ticket

**Purpose:** Adds work semantics to Completable - status, lifecycle, commits.

```python
class Ticket(Completable):
    # === LIFECYCLE ===
    status: TicketStatus = TicketStatus.NOT_STARTED
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime

    # === WORK TRACKING ===
    commits_local: List[GitCommit] = []
    assigned_agents_local: List[str] = []

    # === HIERARCHY ===
    parent_ref: Optional[str]

    # === REQUIREMENTS ===
    requirements_local: List[Requirement] = []

    # === NEW FIELDS (from gap analysis) ===
    priority: Optional[Priority]
    deferred: bool = False
    estimated_duration_local: Optional[str]
    actual_duration_local: Optional[str]

    # === STATE TRANSITIONS ===
    def start(self) -> tuple[bool, List[str]]:
        """Start work - checks can_transition_to(IN_PROGRESS)."""
        ...

    def complete(self) -> tuple[bool, List[str]]:
        """Complete work - checks can_transition_to(COMPLETED)."""
        ...

    # === COMPUTED HIERARCHY ===
    @computed_field
    def is_parent(self) -> bool: ...

    @computed_field
    def is_child(self) -> bool: ...

    @computed_field
    def is_ultimate_parent(self) -> bool: ...

    @computed_field
    def is_ultimate_child(self) -> bool: ...

    @computed_field
    def is_intermediate(self) -> bool: ...
```

**Relationships:**
- Extends `Completable`
- Contains `List[GitCommit]`
- Contains `List[Requirement]`
- Extended by `HierarchicalTicket`

---

## Layer 2: HierarchicalTicket

### HierarchicalTicket

**Purpose:** Adds hierarchy-aware smart accessors, sibling navigation, aggregation.

```python
class HierarchicalTicket(Ticket):
    # === HIERARCHY & ORDERING ===
    parent_id: Optional[str]             # ULID reference (not slug)
    sequence: int = 0                    # Explicit ordering among siblings
    slug: str = ""                       # Human-readable path segment

    # === SIBLING NAVIGATION ===
    @property
    def siblings(self) -> List['HierarchicalTicket']: ...

    @property
    def next_sibling(self) -> Optional['HierarchicalTicket']: ...

    @property
    def prev_sibling(self) -> Optional['HierarchicalTicket']: ...

    def reorder(self, new_sequence: int) -> None:
        """Change position without changing identity."""
        ...

    # === SMART ACCESSORS ===
    @property
    def commits(self) -> List[GitCommit]:
        """Local if leaf, aggregated if parent."""
        ...

    @property
    def requirements_effective(self) -> List[Requirement]:
        """Resolved with inheritance modes."""
        ...

    @property
    def all_criteria(self) -> List[Criterion]:
        """Explicit + instantiated from requirements."""
        ...

    # === CONVENIENCE BY CRITERION TYPE ===
    @property
    def deliverables(self) -> List[Criterion]: ...

    @property
    def tests(self) -> List[Criterion]: ...

    @property
    def subtasks(self) -> List[Criterion]: ...

    @property
    def dependencies(self) -> List[Criterion]:
        """Criteria blocking IN_PROGRESS."""
        ...

    @property
    def success_criteria(self) -> List[Criterion]:
        """Criteria blocking COMPLETED."""
        ...

    @property
    def production_gates(self) -> List[Criterion]:
        """Criteria blocking PRODUCTION_READY."""
        ...

    # === ARTIFACT AGGREGATION ===
    @property
    def all_referenced_artifacts(self) -> List[str]: ...

    @property
    def stale_documentation_artifacts(self) -> List[str]: ...

    @property
    def has_stale_documentation(self) -> bool: ...

    @property
    def documentation_health(self) -> DocumentationHealth: ...

    # === INHERITED COMPUTED FIELDS ===
    @property
    def effective_priority(self) -> Priority: ...

    @computed_field
    def computed_tokens(self) -> int: ...

    @property
    def estimated_duration(self) -> Optional[str]: ...

    @property
    def required_children(self) -> List[str]:
        """Children that are not deferred."""
        ...
```

**Relationships:**
- Extends `Ticket`
- Self-references via `parent_id`, `siblings`, `next_sibling`, `prev_sibling`
- Extended by all Layer 3 domain models

---

## Layer 3: Domain Models

### RoadmapTicket

**Purpose:** Top-level roadmap with version and deployment tracking.

```python
class RoadmapTicket(HierarchicalTicket):
    # Semantic Fields
    version: str
    activity_log: List[ActivityLogEntry] = []
    deployed_platforms: List[str] = []

    # Artifact Accessors
    @property
    def all_project_documentation(self) -> List[str]: ...

    @property
    def framework_components(self) -> List[str]: ...

    @property
    def orphan_artifacts(self) -> List[str]: ...
```

---

### TrackTicket

**Purpose:** Strategic track grouping related sprints.

```python
class TrackTicket(HierarchicalTicket):
    # Semantic Fields
    priority: Priority
    strategic_value: Optional[str]
```

---

### SprintTicket

**Purpose:** Time-boxed sprint with extended lifecycle.

```python
class SprintTicket(HierarchicalTicket):
    # Extended Lifecycle Timestamps
    completion_gate_check_at: Optional[datetime]
    production_gate_check_at: Optional[datetime]
    production_ready_at: Optional[datetime]
    deployed_at: Optional[datetime]

    # Sprint-specific
    plan_file: Optional[str]

    # Artifact Accessors
    @property
    def sprint_context_artifacts(self) -> List[str]: ...

    @property
    def planning_artifacts(self) -> List[str]: ...
```

---

### TaskTicket

**Purpose:** Atomic work item with complexity and token estimation.

```python
class TaskTicket(HierarchicalTicket):
    # Semantic Fields
    task_type: TaskType
    estimated_tokens: int                # Required for tasks
    actual_tokens: Optional[int]
    complexity: Complexity = Complexity.MEDIUM
    phase_label: Optional[str]

    # Artifact Accessors
    @property
    def code_artifacts(self) -> List[str]: ...

    @property
    def documentation_artifacts(self) -> List[str]: ...

    @property
    def undocumented_code_artifacts(self) -> List[str]: ...
```

---

## Supporting Classes

### Requirement

**Purpose:** Criterion template that cascades down the hierarchy.

```python
class Requirement(BaseModel):
    id: str
    name: str
    description: str

    criterion_template: CriterionTemplate
    applicability: ApplicabilityRules
    inherit_mode: InheritMode           # INHERIT, OVERRIDE, SKIP
    enabled: bool = True
    overrides: List[str] = []
```

---

### CriterionTemplate

**Purpose:** Template for generating criteria at runtime.

```python
class CriterionTemplate(BaseModel):
    target_type: CriterionTargetType
    target_config: Dict[str, Any]
    blocks_transition_to: TicketStatus = TicketStatus.COMPLETED

    def instantiate(self, ticket: Ticket) -> Criterion: ...
```

---

### ApplicabilityRules

**Purpose:** Rules for when a requirement applies to a ticket.

```python
class ApplicabilityRules(BaseModel):
    ticket_types: Optional[List[str]]
    task_types: Optional[List[TaskType]]
    has_criterion_types: Optional[List[CriterionTargetType]]

    def matches(self, ticket: Ticket) -> bool: ...
```

---

### Progress

**Purpose:** Progress tracking with completion percentage.

```python
class Progress(BaseModel):
    total: int
    completed: int
    completion_percent: float
```

---

### GitCommit

**Purpose:** Git commit with platform and completion metadata.

```python
class GitCommit(BaseModel):
    sha: str                             # Full 40-char SHA
    message: str
    date: datetime
    author: str

    platform: str                        # claude-code, goose, cursor
    submitted_at: datetime
    completes_tickets: List[str] = []    # Extracted from message

    @classmethod
    def from_git(cls, sha: str, repo_path: Path, platform: str) -> 'GitCommit': ...
```

---

### ActivityLogEntry

**Purpose:** Unified activity/audit entry for all changes.

```python
class ActivityLogEntry(BaseModel):
    timestamp: datetime
    type: ActivityType
    description: str

    # Entity tracking
    entity_type: Optional[str]           # roadmap, track, sprint, task, criterion
    entity_id: Optional[str]

    # Field change tracking
    field: Optional[str]
    old_value: Optional[Any]
    new_value: Optional[Any]

    # Attribution
    changed_by: Optional[str]
    commit_sha: Optional[str]

    # Additional context
    context: Optional[Dict[str, Any]]
```

---

### TestResult

**Purpose:** Result of test execution.

```python
class TestResult(BaseModel):
    pass_rate: float
    coverage_percent: Optional[float]
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
```

---

### ImpactAnalyzer

**Purpose:** Analyzes impact of changes across the artifact graph.

```python
class ImpactAnalyzer:
    def __init__(self, artifact_registry, db): ...

    def analyze_file_changes(self, changed_files: List[str]) -> ImpactReport: ...
```

---

### ImpactReport

**Purpose:** Report of impact from file changes.

```python
@dataclass
class ImpactReport:
    changed_files: List[str]
    directly_impacted_artifacts: List[Artifact]
    stale_documentation: List[Artifact]
    affected_tickets: List[str]

    @property
    def has_documentation_impact(self) -> bool: ...

    def to_warning_message(self) -> str: ...
```

---

### RefreshContext

**Purpose:** Context passed to CriterionTarget.refresh() for state updates.

```python
class RefreshContext(BaseModel):
    ticket_registry: TicketRegistry
    artifact_registry: ArtifactRegistry
    test_runner: TestRunner
    metrics: MetricsCollector
    http_client: HttpClient
    activity_log: List[ActivityLogEntry]
```

---

## Enumerations

### TicketStatus

```python
class TicketStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETION_GATE_CHECK = "completion_gate_check"
    COMPLETED = "completed"
    PRODUCTION_GATE_CHECK = "production_gate_check"
    PRODUCTION_READY = "production_ready"
    DEPLOYED = "deployed"
    WONT_DO = "wont_do"
    SUPERSEDED = "superseded"
```

**Status Progression:**
```
not_started → in_progress ↔ paused → completion_gate_check → completed
→ production_gate_check → production_ready → deployed

Terminal: wont_do, superseded
```

---

### CriterionTargetType

```python
class CriterionTargetType(str, Enum):
    COMPLETABLE = "completable"
    FILE_EXISTS = "file_exists"
    TEST_PASSES = "test_passes"
    THRESHOLD = "threshold"
    MANUAL = "manual"
    EXTERNAL = "external"
    ARTIFACT = "artifact"
    SYMBOL_EXISTS = "symbol_exists"      # Sprint 10
    COMMAND_EXISTS = "command_exists"    # Sprint 10
    MCP_TOOL_EXISTS = "mcp_tool_exists"  # Sprint 10
```

---

### InheritMode

```python
class InheritMode(str, Enum):
    INHERIT = "inherit"      # Use stricter of local vs ancestor
    OVERRIDE = "override"    # Replace ancestor requirement
    SKIP = "skip"            # Not applicable (with justification)
```

---

### ThresholdComparison

```python
class ThresholdComparison(str, Enum):
    GTE = "gte"
    GT = "gt"
    EQ = "eq"
    LTE = "lte"
    LT = "lt"
```

---

### TaskType

```python
class TaskType(str, Enum):
    DEVELOPMENT = "development"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    RESEARCH = "research"
    REVIEW = "review"
    GATE = "gate"
```

---

### Complexity

```python
class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

---

### Priority

```python
class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

---

### DeliverableType

```python
class DeliverableType(str, Enum):
    CODE = "code"
    TEST = "test"
    DOCUMENTATION = "documentation"
    CONFIG = "config"
    OTHER = "other"
```

---

### ActivityType

```python
class ActivityType(str, Enum):
    # Lifecycle events
    ROADMAP_STARTED = "roadmap_started"
    ROADMAP_COMPLETED = "roadmap_completed"
    ROADMAP_DEPLOYED = "roadmap_deployed"
    TRACK_STARTED = "track_started"
    TRACK_COMPLETED = "track_completed"
    SPRINT_STARTED = "sprint_started"
    SPRINT_COMPLETED = "sprint_completed"
    SPRINT_PRODUCTION_READY = "sprint_production_ready"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"

    # Field-level audit
    FIELD_CHANGED = "field_changed"
    STATUS_CHANGED = "status_changed"

    # Criterion events
    CRITERION_MET = "criterion_met"
    CRITERION_EVALUATED = "criterion_evaluated"
    CRITERION_REFRESHED = "criterion_refreshed"

    # System events
    AUTO_PROGRESSION = "auto_progression"
    VALIDATION_WARNING = "validation_warning"
    COMMIT_LINKED = "commit_linked"
```

---

### ArtifactType

```python
class ArtifactType(str, Enum):
    CODE = "code"
    TEST = "test"
    CONFIG = "config"
    DOCUMENTATION = "documentation"
    CONTEXT = "context"
    AGENT = "agent"
    WORKFLOW = "workflow"
    TEMPLATE = "template"
    DATA = "data"
    ASSET = "asset"
    SCHEMA = "schema"
    OTHER = "other"
```

---

### ContextArtifactSubtype

```python
class ContextArtifactSubtype(str, Enum):
    PLANNING_DOC = "planning_doc"
    IMPLEMENTATION_NOTES = "impl_notes"
    DECISION_RECORD = "decision_record"
    AUDIT_REPORT = "audit_report"
    RETROSPECTIVE = "retrospective"
```

---

### DocumentationSubtype

```python
class DocumentationSubtype(str, Enum):
    README = "readme"
    API_REFERENCE = "api_reference"
    USER_GUIDE = "user_guide"
    ARCHITECTURE = "architecture"
    CHANGELOG = "changelog"
    TUTORIAL = "tutorial"
```

---

### ProvenanceType

```python
class ProvenanceType(str, Enum):
    TICKET_CREATED = "ticket_created"
    PRE_EXISTING = "pre_existing"
    GENERATED = "generated"
    EXTERNAL = "external"
    FRAMEWORK = "framework"
```

---

### ArtifactVerification

```python
class ArtifactVerification(str, Enum):
    EXISTS = "exists"
    NOT_STALE = "not_stale"
    HASH_UNCHANGED = "hash_unchanged"
```

---

### DocumentationHealth

```python
class DocumentationHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
```

---

## Class Relationship Matrix

| Class | Inherits From | Contains | Referenced By |
|-------|--------------|----------|---------------|
| **Artifact** | BaseModel | ArtifactProvenance | ArtifactTarget |
| **ArtifactProvenance** | BaseModel | - | Artifact |
| **Completable** | BaseModel | List[Criterion] | - |
| **Criterion** | BaseModel | CriterionTarget | Completable |
| **CriterionTarget** | BaseModel (abstract) | - | Criterion |
| **CompletableTarget** | CriterionTarget | - | - |
| **FileExistsTarget** | CriterionTarget | - | - |
| **TestPassesTarget** | CriterionTarget | TestResult | - |
| **ThresholdTarget** | CriterionTarget | - | - |
| **ManualTarget** | CriterionTarget | - | - |
| **ExternalTarget** | CriterionTarget | - | - |
| **ArtifactTarget** | CriterionTarget | - | - |
| **Ticket** | Completable | List[GitCommit], List[Requirement] | - |
| **HierarchicalTicket** | Ticket | - | Self (parent_id) |
| **RoadmapTicket** | HierarchicalTicket | List[ActivityLogEntry] | - |
| **TrackTicket** | HierarchicalTicket | - | - |
| **SprintTicket** | HierarchicalTicket | - | - |
| **TaskTicket** | HierarchicalTicket | - | - |
| **Requirement** | BaseModel | CriterionTemplate, ApplicabilityRules | Ticket |
| **CriterionTemplate** | BaseModel | - | Requirement |
| **ApplicabilityRules** | BaseModel | - | Requirement |
| **Progress** | BaseModel | - | Completable |
| **GitCommit** | BaseModel | - | Ticket |
| **ActivityLogEntry** | BaseModel | - | RoadmapTicket |
| **TestResult** | BaseModel | - | TestPassesTarget |
| **ImpactReport** | dataclass | List[Artifact] | ImpactAnalyzer |

---

## Database Entity Mapping

### Tables

| Class | Table | Notes |
|-------|-------|-------|
| Ticket + subtypes | `tickets` | Single-table inheritance via `ticket_type` |
| Criterion | `criteria` | Polymorphic target via `target_type` + `target_data` JSON |
| Artifact | `artifacts` | Provenance stored as JSON |
| ActivityLogEntry | `activity_log` | Context stored as JSON |

### Key Views

| View | Purpose |
|------|---------|
| `v_ticket_progress` | Progress calculation per transition type |
| `v_reverse_dependencies` | "Who depends on ticket X?" |
| `v_required_children` | Non-deferred children for completion |
| `v_orphan_artifacts` | Artifacts not referenced by any criterion |
| `v_documentation_graph` | What documents what |
| `v_stale_documentation` | Docs needing update |
| `v_ticket_siblings` | Sibling navigation with prev/next |
| `v_ticket_artifacts` | All artifacts by ticket |

---

## Implementation Sprint Mapping

| Sprint | Classes Implemented |
|--------|---------------------|
| **6** | Enums, Completable, Criterion, CriterionTarget subtypes, Ticket, HierarchicalTicket, Domain Models |
| **7** | Artifact, ArtifactProvenance, ArtifactTarget |
| **8** | YAML/SQL loaders for all models |
| **9** | Operations using criteria |
| **10** | SYMBOL_EXISTS, COMMAND_EXISTS, MCP_TOOL_EXISTS targets |
| **11** | Validation, ImpactAnalyzer |
| **12** | Production cutover, git hooks |

---

**Document Version:** 1.0
**Last Updated:** 2025-12-02
**Author:** Claude Code
