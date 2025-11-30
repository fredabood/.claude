# Unified Ticket Architecture Design Document

**Created:** 2025-11-29
**Sprint:** sqlite-backend-6
**Status:** AUTHORITATIVE - Supersedes all previous design documents

---

## Document History

This document consolidates and supersedes the following design documents:
- `COMPLETABLE_UNIFICATION.md` - Superseded (naming updated)
- `COMPREHENSIVE_IMPACT_ASSESSMENT.md` - Superseded (blocking model updated)
- `DEPENDENCY_SYSTEM_ANALYSIS.md` - Superseded (Dependency class ELIMINATED)
- `IMPACT_ANALYSIS.md` - Superseded (sprint numbering updated)
- `REVISED_ARCHITECTURE.md` - Superseded (classes consolidated)

All architectural decisions in this document reflect the **current approved design**.

---

## Executive Summary

The unified ticket architecture treats **everything that can be completed** as a `Completable` with **criteria**. The key innovation is the `blocks_transition_to` field on `Criterion`, which unifies:

- Dependencies (blocks `IN_PROGRESS`)
- Success criteria (blocks `COMPLETED`)
- Production gates (blocks `PRODUCTION_READY`)

This **ELIMINATES the separate Dependency class** and creates a single deterministic interface for all state transitions.

---

## Part 1: Core Design Principles

### 1.1 Design Intent

> The purpose of the system is to put guardrails around the AI's ability to manipulate the roadmap state by implementing a **deterministic interface for calculating whether or not a ticket has been completed**.

This means:
1. **Completion is computed, not declared** - AI cannot mark a ticket complete unless all criteria are satisfied
2. **User controls the criteria** - User defines what "complete" means for each ticket
3. **Single unified interface** - `can_transition_to(status)` is THE check for all state changes

### 1.2 The Unified Blocking Model

**ALL blocking relationships use `Criterion` with `blocks_transition_to`:**

| blocks_transition_to | Meaning | Example |
|---------------------|---------|---------|
| `IN_PROGRESS` | Must be met before starting | Sibling dependency, external blocker |
| `COMPLETED` | Must be met before completing | Success criteria, child completion, tests |
| `PRODUCTION_READY` | Must be met before deploying | Production gates, security reviews |

**What this ELIMINATES:**
- ~~`Dependency` class~~ → `Criterion` with `blocks_transition_to: IN_PROGRESS`
- ~~`blocked_by` field~~ → Computed from criteria
- ~~`depends_on` field~~ → Criteria with `CompletableTarget`
- ~~`development_gates`~~ → Criteria with `blocks_transition_to: IN_PROGRESS`
- ~~`quality_gates`~~ → Criteria with `ThresholdTarget`
- ~~`success_criteria` (separate)~~ → Criteria with `blocks_transition_to: COMPLETED`

---

## Part 2: Core Abstractions

### 2.1 Completable (Base Class)

```python
class Completable(BaseModel):
    """Base class for anything that can be completed."""

    # Identity
    id: str
    name: str
    description: Optional[str] = None

    # THE source of truth for ALL blocking
    criteria: List[Criterion] = Field(default_factory=list)

    # Computed properties
    @computed_field
    def children(self) -> List[str]:
        """Children are derived from CompletableTarget criteria."""
        return [
            c.target.completable_id
            for c in self.criteria
            if isinstance(c.target, CompletableTarget)
        ]

    def can_transition_to(self, status: TicketStatus) -> tuple[bool, List[str]]:
        """
        THE unified interface for checking state transitions.

        Returns (can_transition, blocking_reasons).
        """
        blocking = [
            c.description
            for c in self.criteria
            if c.blocks_transition_to == status and not c.is_met
        ]
        return (len(blocking) == 0, blocking)

    def progress_for_transition(self, status: TicketStatus) -> Progress:
        """Progress computed per transition type."""
        relevant = [c for c in self.criteria if c.blocks_transition_to == status]
        total = len(relevant)
        met = sum(1 for c in relevant if c.is_met)
        return Progress(
            total=total,
            completed=met,
            completion_percent=(met / total * 100) if total > 0 else 100.0
        )

    @property
    def progress(self) -> Progress:
        """Default progress = progress toward COMPLETED."""
        return self.progress_for_transition(TicketStatus.COMPLETED)
```

### 2.2 Criterion

```python
class Criterion(BaseModel):
    """A single requirement for state transition."""

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
        if not self.required:
            return True
        return self.target.is_satisfied()
```

### 2.3 CriterionTarget Types

```python
class CriterionTarget(BaseModel):
    """Base for all criterion targets."""

    @abstractmethod
    def is_satisfied(self) -> bool: ...


class CompletableTarget(CriterionTarget):
    """Criterion met when another Completable reaches required status."""

    completable_id: str
    required_status: TicketStatus = TicketStatus.COMPLETED

    # Cached state (updated by sync)
    current_status: Optional[TicketStatus] = None
    last_checked: Optional[datetime] = None

    def is_satisfied(self) -> bool:
        if self.current_status is None:
            return False
        return status_gte(self.current_status, self.required_status)


class FileExistsTarget(CriterionTarget):
    """Criterion met when file(s) exist."""

    paths: List[str]
    all_required: bool = True

    # Cached state
    existing_paths: List[str] = Field(default_factory=list)
    missing_paths: List[str] = Field(default_factory=list)
    last_checked: Optional[datetime] = None

    def is_satisfied(self) -> bool:
        if self.all_required:
            return len(self.missing_paths) == 0
        return len(self.existing_paths) > 0


class TestPassesTarget(CriterionTarget):
    """Criterion met when test passes with optional thresholds."""

    test_command: str
    pass_threshold: float = 100.0
    coverage_threshold: Optional[float] = None

    # Cached state (latest result)
    last_result: Optional[TestResult] = None

    def is_satisfied(self) -> bool:
        if self.last_result is None:
            return False
        if self.last_result.pass_rate < self.pass_threshold:
            return False
        if self.coverage_threshold and self.last_result.coverage_percent:
            if self.last_result.coverage_percent < self.coverage_threshold:
                return False
        return True


class ThresholdTarget(CriterionTarget):
    """Criterion met when a metric meets a threshold."""

    metric_name: str
    threshold: float
    comparison: ThresholdComparison = ThresholdComparison.GTE

    # Current value
    current_value: Optional[float] = None
    last_checked: Optional[datetime] = None

    def is_satisfied(self) -> bool:
        if self.current_value is None:
            return False
        return compare(self.current_value, self.threshold, self.comparison)


class ManualTarget(CriterionTarget):
    """Criterion met when manually assessed."""

    assessor: Optional[str] = None
    instructions: Optional[str] = None

    # Assessment state
    assessed: bool = False
    met: Optional[bool] = None
    assessed_at: Optional[datetime] = None
    assessed_by: Optional[str] = None
    evidence: Optional[str] = None

    def is_satisfied(self) -> bool:
        return self.assessed and self.met == True


class ExternalTarget(CriterionTarget):
    """Criterion met when external system reports success."""

    system_name: str
    endpoint: Optional[str] = None
    expected_status: str = "success"

    # Cached state
    current_status: Optional[str] = None
    last_checked: Optional[datetime] = None

    def is_satisfied(self) -> bool:
        return self.current_status == self.expected_status
```

---

## Part 3: Layer Architecture

### 3.1 Layer 1: Ticket (Base Work Item)

```python
class Ticket(Completable):
    """Layer 1: Base ticket with work semantics."""

    # === IDENTITY (from Completable) ===
    # id, name, description, criteria

    # === LIFECYCLE ===
    status: TicketStatus = TicketStatus.NOT_STARTED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # === WORK TRACKING ===
    commits_local: List[GitCommit] = Field(default_factory=list)
    assigned_agents_local: List[str] = Field(default_factory=list)

    # === HIERARCHY (denormalized for lookup) ===
    parent_ref: Optional[str] = None

    # === REQUIREMENTS (criterion templates for children) ===
    requirements_local: List[Requirement] = Field(default_factory=list)

    # === DETERMINISTIC STATE TRANSITIONS ===
    def start(self) -> tuple[bool, List[str]]:
        """Start work on this ticket."""
        can, reasons = self.can_transition_to(TicketStatus.IN_PROGRESS)
        if can:
            self.status = TicketStatus.IN_PROGRESS
            self.started_at = datetime.now(timezone.utc)
        return (can, reasons)

    def complete(self) -> tuple[bool, List[str]]:
        """Complete this ticket."""
        can, reasons = self.can_transition_to(TicketStatus.COMPLETED)
        if can:
            self.status = TicketStatus.COMPLETED
            self.completed_at = datetime.now(timezone.utc)
        return (can, reasons)

    # === COMPUTED HIERARCHY ATTRIBUTES ===
    @computed_field
    def is_parent(self) -> bool:
        return len(self.children) > 0

    @computed_field
    def is_child(self) -> bool:
        return self.parent_ref is not None

    @computed_field
    def is_ultimate_parent(self) -> bool:
        return self.is_parent and not self.is_child

    @computed_field
    def is_ultimate_child(self) -> bool:
        return self.is_child and not self.is_parent

    @computed_field
    def is_intermediate(self) -> bool:
        return self.is_parent and self.is_child
```

### 3.2 Layer 2: HierarchicalTicket (Smart Accessors)

```python
class HierarchicalTicket(Ticket):
    """Layer 2: Ticket with hierarchy-aware accessors."""

    # === SMART ACCESSORS ===
    @property
    def commits(self) -> List[GitCommit]:
        """Commits: local if leaf, aggregated if parent."""
        if self.is_ultimate_child:
            return self.commits_local
        return self._aggregate_commits_from_children()

    @property
    def requirements_effective(self) -> List[Requirement]:
        """Requirements: resolved with inheritance modes."""
        return self._resolve_requirements()

    @property
    def all_criteria(self) -> List[Criterion]:
        """All criteria: explicit + instantiated from requirements."""
        return self.criteria + self._instantiate_requirement_criteria()

    # === CONVENIENCE ACCESSORS BY CRITERION TYPE ===
    @property
    def deliverables(self) -> List[Criterion]:
        """Criteria that are file-based."""
        return [c for c in self.criteria if isinstance(c.target, FileExistsTarget)]

    @property
    def tests(self) -> List[Criterion]:
        """Criteria that are test-based."""
        return [c for c in self.criteria if isinstance(c.target, TestPassesTarget)]

    @property
    def subtasks(self) -> List[Criterion]:
        """Criteria that reference other tickets (children)."""
        return [c for c in self.criteria if isinstance(c.target, CompletableTarget)]

    @property
    def dependencies(self) -> List[Criterion]:
        """Criteria that block starting (IN_PROGRESS)."""
        return [
            c for c in self.criteria
            if c.blocks_transition_to == TicketStatus.IN_PROGRESS
        ]

    @property
    def success_criteria(self) -> List[Criterion]:
        """Criteria that block completing (COMPLETED)."""
        return [
            c for c in self.criteria
            if c.blocks_transition_to == TicketStatus.COMPLETED
        ]

    @property
    def production_gates(self) -> List[Criterion]:
        """Criteria that block deployment (PRODUCTION_READY)."""
        return [
            c for c in self.criteria
            if c.blocks_transition_to == TicketStatus.PRODUCTION_READY
        ]
```

### 3.3 Layer 3: Domain Models (Semantic Fields Only)

```python
class RoadmapTicket(HierarchicalTicket):
    """Roadmap-specific semantic fields."""
    version: str
    activity_log: List[ActivityLogEntry] = Field(default_factory=list)
    deployed_platforms: List[str] = Field(default_factory=list)


class TrackTicket(HierarchicalTicket):
    """Track-specific semantic fields."""
    priority: Priority
    strategic_value: Optional[str] = None


class SprintTicket(HierarchicalTicket):
    """Sprint-specific semantic fields."""
    # Extended lifecycle timestamps
    completion_gate_check_at: Optional[datetime] = None
    production_gate_check_at: Optional[datetime] = None
    production_ready_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None

    plan_file: Optional[str] = None


class TaskTicket(HierarchicalTicket):
    """Task-specific semantic fields."""
    task_type: TaskType
    estimated_tokens: Optional[int] = None
    actual_tokens: Optional[int] = None
    complexity: Complexity = Complexity.MEDIUM
    phase_label: Optional[str] = None
```

---

## Part 4: Requirement System

### 4.1 Requirements as Criterion Templates

Requirements cascade down the hierarchy and **generate criteria** when applicable:

```python
class Requirement(BaseModel):
    """A criterion template that cascades down the hierarchy."""

    id: str
    name: str
    description: str

    # What type of criterion this generates
    criterion_template: CriterionTemplate

    # When does this apply?
    applicability: ApplicabilityRules

    # Inheritance behavior
    inherit_mode: InheritMode  # INHERIT, OVERRIDE, SKIP


class CriterionTemplate(BaseModel):
    """Template for generating criteria."""

    target_type: CriterionTargetType
    target_config: Dict[str, Any]
    blocks_transition_to: TicketStatus = TicketStatus.COMPLETED

    def instantiate(self, ticket: Ticket) -> Criterion:
        """Generate a criterion for a specific ticket."""
        target = create_target(self.target_type, self.target_config, ticket)
        return Criterion(
            id=f"{self.id}-{ticket.id}",
            description=self.description,
            target=target,
            blocks_transition_to=self.blocks_transition_to
        )


class ApplicabilityRules(BaseModel):
    """Rules for when a requirement applies."""

    ticket_types: Optional[List[str]] = None
    task_types: Optional[List[TaskType]] = None
    has_criterion_types: Optional[List[CriterionTargetType]] = None

    def matches(self, ticket: Ticket) -> bool:
        """Check if this requirement applies to a ticket."""
        # Implementation checks each rule
        ...


class InheritMode(str, Enum):
    """How a requirement interacts with inherited requirements."""
    INHERIT = "inherit"      # Use stricter of local vs ancestor
    OVERRIDE = "override"    # Replace ancestor requirement entirely
    SKIP = "skip"            # Explicitly not applicable (with justification)
```

### 4.2 Requirement Resolution Algorithm

```python
def resolve_requirements(ticket: Ticket) -> List[Requirement]:
    """
    Resolve effective requirements for a ticket.

    Algorithm:
    1. Gather requirements from ancestors (roadmap → track → sprint)
    2. For each local requirement:
       - If OVERRIDE: replace ancestor requirement with same type
       - If SKIP: mark ancestor requirement as not applicable
       - If INHERIT: use stricter of local vs ancestor
    3. Filter to only applicable requirements
    4. Return final list
    """
    inherited = collect_ancestor_requirements(ticket)
    local = ticket.requirements_local

    effective = []
    processed_types = set()

    for local_req in local:
        if local_req.inherit_mode == InheritMode.SKIP:
            processed_types.add(local_req.id)
            continue

        if local_req.inherit_mode == InheritMode.OVERRIDE:
            effective.append(local_req)
            processed_types.add(local_req.id)
            continue

        # INHERIT mode - find matching inherited and use stricter
        inherited_match = find_by_id(inherited, local_req.id)
        if inherited_match:
            stricter = resolve_stricter(local_req, inherited_match)
            effective.append(stricter)
        else:
            effective.append(local_req)
        processed_types.add(local_req.id)

    # Add inherited requirements not overridden locally
    for inh_req in inherited:
        if inh_req.id not in processed_types:
            effective.append(inh_req)

    # Filter to applicable requirements
    return [r for r in effective if r.applicability.matches(ticket)]
```

---

## Part 5: Implicit Parent-Child Relationships

### 5.1 How Children Are Derived

Children are NOT stored in explicit lists. They are DERIVED from `CompletableTarget` criteria:

```python
# Example: Sprint with 3 child tasks
sprint = SprintTicket(
    id="sprint-1",
    name="Authentication Sprint",
    criteria=[
        Criterion(
            id="task-001-complete",
            description="Login API complete",
            target=CompletableTarget(completable_id="task-001"),
            blocks_transition_to=TicketStatus.COMPLETED  # Child completion
        ),
        Criterion(
            id="task-002-complete",
            description="Logout API complete",
            target=CompletableTarget(completable_id="task-002"),
            blocks_transition_to=TicketStatus.COMPLETED
        ),
        Criterion(
            id="task-003-complete",
            description="Session management complete",
            target=CompletableTarget(completable_id="task-003"),
            blocks_transition_to=TicketStatus.COMPLETED
        ),
        # Sprint-level requirement (not a child)
        Criterion(
            id="integration-tests",
            description="Integration tests pass",
            target=TestPassesTarget(
                test_command="pytest tests/integration/auth/",
                pass_threshold=100.0
            ),
            blocks_transition_to=TicketStatus.COMPLETED
        ),
    ]
)

# Children are derived:
sprint.children  # Returns: ["task-001", "task-002", "task-003"]
```

### 5.2 Dependencies vs Children

Both use `CompletableTarget`, but differ in `blocks_transition_to`:

| Relationship | blocks_transition_to | Meaning |
|--------------|---------------------|---------|
| **Dependency** (sibling) | `IN_PROGRESS` | Must complete before I can START |
| **Child** | `COMPLETED` | Must complete before I can COMPLETE |

```python
# Example: Task with dependency and children
task = TaskTicket(
    id="task-main",
    criteria=[
        # DEPENDENCY: blocks starting
        Criterion(
            id="depends-on-setup",
            description="Setup task must be complete",
            target=CompletableTarget(completable_id="task-setup"),
            blocks_transition_to=TicketStatus.IN_PROGRESS  # <-- Dependency
        ),
        # CHILD: blocks completing
        Criterion(
            id="subtask-1-complete",
            description="Subtask 1 complete",
            target=CompletableTarget(completable_id="subtask-1"),
            blocks_transition_to=TicketStatus.COMPLETED  # <-- Child
        ),
    ]
)

# Only COMPLETED blockers count as children:
task.children  # Returns: ["subtask-1"]
task.dependencies  # Returns criteria with blocks_transition_to=IN_PROGRESS
```

---

## Part 6: YAML Serialization Format

### 6.1 Task YAML Example

```yaml
task:
  id: sqlite-backend-6-task-001
  name: Implement Layer 1 Base Ticket
  status: not_started

  # Unified criteria section
  criteria:
    # Dependency (blocks starting)
    - id: depends-on-enums
      description: Enum definitions must be complete
      blocks_transition_to: in_progress
      target:
        type: completable
        completable_id: sqlite-backend-6-task-010
        required_status: completed

    # Deliverable (blocks completing)
    - id: code-deliverable
      description: Base ticket implementation
      blocks_transition_to: completed
      target:
        type: file_exists
        paths:
          - vibey/roadmap/models/ticket/base.py

    # Test (blocks completing)
    - id: tests-pass
      description: All unit tests pass
      blocks_transition_to: completed
      target:
        type: test_passes
        test_command: pytest tests/roadmap/models/ticket/test_base.py
        pass_threshold: 100.0
        coverage_threshold: 80.0

    # Manual assessment (blocks completing)
    - id: code-review
      description: Code review completed
      blocks_transition_to: completed
      target:
        type: manual
        assessor: senior-engineer

  # Work tracking
  commits_local: []
  assigned_agents_local: [backend-engineer]

  # Task-specific
  task_type: development
  estimated_tokens: 2000
  complexity: medium
```

### 6.2 Sprint YAML Example

```yaml
sprint:
  id: sqlite-backend-6
  name: Unified Ticket Architecture
  status: not_started

  # Sprint's own dependencies
  criteria:
    # Dependency on previous sprint
    - id: depends-on-sprint-5
      description: Column Gap Remediation must be complete
      blocks_transition_to: in_progress
      target:
        type: completable
        completable_id: sqlite-backend-5
        required_status: completed

    # Child tasks (implicit children)
    - id: task-001-complete
      description: Layer 1 Base Ticket complete
      blocks_transition_to: completed
      target:
        type: completable
        completable_id: sqlite-backend-6-task-001

    - id: task-002-complete
      description: HierarchicalTicket complete
      blocks_transition_to: completed
      target:
        type: completable
        completable_id: sqlite-backend-6-task-002

    # ... more child task criteria

    # Sprint-level gate
    - id: integration-tests
      description: All integration tests pass
      blocks_transition_to: completed
      target:
        type: test_passes
        test_command: pytest tests/integration/
        pass_threshold: 100.0

  # Requirement templates (cascade to children)
  requirements_local:
    - id: test-coverage
      name: Test Coverage
      criterion_template:
        target_type: threshold
        target_config:
          metric_name: coverage
          threshold: 80.0
        blocks_transition_to: completed
      applicability:
        has_criterion_types: [file_exists]
      inherit_mode: inherit
```

---

## Part 7: Database Schema

### 7.1 SQLite Schema

```sql
-- Single-table inheritance for all ticket types
CREATE TABLE tickets (
    id TEXT PRIMARY KEY,
    ticket_type TEXT NOT NULL CHECK (ticket_type IN (
        'roadmap', 'track', 'sprint', 'task'
    )),

    -- Common fields
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'not_started',

    -- Hierarchy
    parent_ref TEXT,

    -- Lifecycle timestamps
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    updated_at TEXT NOT NULL,

    -- Type-specific fields (JSON)
    semantic_fields TEXT,  -- JSON object for domain-specific data

    -- Work tracking (JSON arrays)
    commits_local TEXT,
    assigned_agents_local TEXT,
    requirements_local TEXT,

    FOREIGN KEY (parent_ref) REFERENCES tickets(id)
);

-- Unified criteria table with polymorphic target
CREATE TABLE criteria (
    id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL,
    description TEXT NOT NULL,

    -- THE key field for unified blocking
    blocks_transition_to TEXT NOT NULL DEFAULT 'completed',

    -- Optionality
    required INTEGER NOT NULL DEFAULT 1,

    -- Target type discriminator
    target_type TEXT NOT NULL CHECK (target_type IN (
        'completable', 'file_exists', 'test_passes',
        'threshold', 'manual', 'external'
    )),

    -- Target data (JSON for type-specific config and state)
    target_data TEXT NOT NULL,

    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);

-- Index for finding children
CREATE INDEX idx_criteria_children ON criteria(target_type, ticket_id)
WHERE target_type = 'completable';

-- Index for blocking checks
CREATE INDEX idx_criteria_blocking ON criteria(ticket_id, blocks_transition_to);

-- View for progress calculation
CREATE VIEW v_ticket_progress AS
SELECT
    t.id AS ticket_id,
    c.blocks_transition_to,
    COUNT(*) AS total_criteria,
    SUM(CASE WHEN c.is_met THEN 1 ELSE 0 END) AS met_criteria,
    ROUND(100.0 * SUM(CASE WHEN c.is_met THEN 1 ELSE 0 END) / COUNT(*), 1) AS progress
FROM tickets t
LEFT JOIN criteria c ON c.ticket_id = t.id
GROUP BY t.id, c.blocks_transition_to;
```

---

## Part 8: Migration Path

### 8.1 Sprint Sequence

| Sprint | Name | Focus |
|--------|------|-------|
| **6** | Unified Ticket Architecture | Core model classes, layers 0b-3 |
| **7** | Artifact System Architecture | Layer 0a - first-class artifacts |
| **8** | Serialization Migration | YAML/SQL loaders/dumpers for new model |
| **9** | Operations Migration | Update all operations to use criteria |
| **10** | Interface Migration | CLI/MCP for criteria display |
| **11** | Data Validation | Computed vs declared integrity checks |
| **12** | Production Cutover | Initialize DB, dual-write, git hooks |
| **13-deferred** | File Format Analysis | DEFERRED - optional optimization |

### 8.2 Data Migration (Sprint 8)

```python
def migrate_task_to_unified(old_task: dict) -> TaskTicket:
    """Convert legacy task to unified model."""
    criteria = []

    # Convert deliverables → FileExistsTarget criteria
    for d in old_task.get('deliverables', []):
        criteria.append(Criterion(
            id=f"{old_task['id']}-deliv-{len(criteria)}",
            description=f"Deliverable: {d['paths'][0]}",
            target=FileExistsTarget(paths=d['paths']),
            blocks_transition_to=TicketStatus.COMPLETED
        ))

    # Convert blocked_by → CompletableTarget criteria
    for b in old_task.get('blocked_by', []):
        criteria.append(Criterion(
            id=f"{old_task['id']}-dep-{b['blocker_id']}",
            description=f"Depends on: {b['blocker_id']}",
            target=CompletableTarget(
                completable_id=b['blocker_id'],
                required_status=TicketStatus(b.get('required_status', 'completed'))
            ),
            blocks_transition_to=TicketStatus.IN_PROGRESS
        ))

    # Convert dependencies → CompletableTarget criteria
    for d in old_task.get('dependencies', []):
        criteria.append(Criterion(
            id=f"{old_task['id']}-dep-{d['target_id']}",
            description=f"Depends on: {d['target_id']}",
            target=CompletableTarget(
                completable_id=d['target_id'],
                required_status=TicketStatus(d.get('target_status', 'completed'))
            ),
            blocks_transition_to=TicketStatus.IN_PROGRESS
        ))

    # Convert gate_info → ThresholdTarget criterion
    if gate := old_task.get('gate_info'):
        criteria.append(Criterion(
            id=f"{old_task['id']}-gate",
            description="Quality gate",
            target=ThresholdTarget(
                metric_name="gate_score",
                threshold=gate['threshold']
            ),
            blocks_transition_to=TicketStatus.COMPLETED
        ))

    return TaskTicket(
        id=old_task['id'],
        name=old_task.get('title', old_task['id']),
        description=old_task.get('description'),
        status=TicketStatus(old_task.get('status', 'not_started')),
        criteria=criteria,
        commits_local=old_task.get('commits', []),
        task_type=TaskType(old_task.get('task_type', 'development')),
        # ... other fields
    )
```

---

## Part 9: Benefits Summary

### 9.1 Simplification

| Metric | Before | After |
|--------|--------|-------|
| Concepts for completion | 4 (children, deliverables, criteria, gates) | 1 (criteria) |
| Progress formulas | 3 (per type) | 1 (universal) |
| Parent-child models | Explicit fields | Computed from criteria |
| Completion checks | Multiple functions | One function: `can_transition_to()` |
| Dependency classes | `Dependency`, `DependencyStatus`, `*Blocker` | Criterion with `blocks_transition_to` |

### 9.2 Unified Interface

| Protection | Before | After |
|------------|--------|-------|
| AI completion bypass | Multiple scattered checks | Single deterministic check |
| Visibility of blockers | Multiple sources | `can_transition_to()` returns reasons |
| Audit trail | Partial | Every criterion has state |
| Progress tracking | Different per entity type | Same formula everywhere |

---

## Part 10: Task Execution Order (Sprint 6)

```
FOUNDATION (no dependencies)
└── Task 010: Enum Definitions
    - TicketStatus, CriterionTargetType, InheritMode
    - ThresholdComparison, TaskType, Complexity

CORE ABSTRACTIONS (depends on 010)
├── Task 009: Completable, Criterion, CriterionTarget
│   - Completable base class
│   - Criterion with blocks_transition_to
│   - All CriterionTarget types
│   - can_transition_to(), progress_for_transition()
│
└── Task 011: Requirement System
    - Requirement, CriterionTemplate
    - ApplicabilityRules, InheritMode
    - RequirementResolver

TICKET LAYERS (depends on 009, 010, 011)
├── Task 001: Layer 1 Ticket
│   - Extends Completable with work semantics
│   - start(), complete() methods
│   - Hierarchy attributes
│
├── Task 002: Layer 2 HierarchicalTicket
│   - Smart accessors
│   - Convenience accessors by criterion type
│
├── Task 003: RoadmapTicket
├── Task 004: TrackTicket
├── Task 005: SprintTicket
└── Task 006: TaskTicket

ORM & MIGRATION (depends on 001-006)
├── Task 007: SQLAlchemy ORM
│   - tickets table with single-table inheritance
│   - criteria table with polymorphic targets
│
└── Task 008: Migration Adapters
    - Convert legacy models to unified
    - Backward compatibility layer
```

---

## Appendix A: Enum Definitions

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


class CriterionTargetType(str, Enum):
    COMPLETABLE = "completable"
    FILE_EXISTS = "file_exists"
    TEST_PASSES = "test_passes"
    THRESHOLD = "threshold"
    MANUAL = "manual"
    EXTERNAL = "external"


class InheritMode(str, Enum):
    INHERIT = "inherit"
    OVERRIDE = "override"
    SKIP = "skip"


class ThresholdComparison(str, Enum):
    GTE = "gte"
    GT = "gt"
    EQ = "eq"
    LTE = "lte"
    LT = "lt"


class TaskType(str, Enum):
    DEVELOPMENT = "development"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    RESEARCH = "research"
    REVIEW = "review"
    GATE = "gate"


class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

---

## Appendix B: Status Progression

```
not_started
    ↓ can_transition_to(IN_PROGRESS) must pass
in_progress ←─────────────────────────┐
    ↓                                  │
paused ──────────────────────────────→┘
    ↓
completion_gate_check
    ↓ can_transition_to(COMPLETED) must pass
completed
    ↓
production_gate_check
    ↓ can_transition_to(PRODUCTION_READY) must pass
production_ready
    ↓
deployed

Terminal states: wont_do, superseded
```

---

## Part 11: Gap Analysis Decisions (2025-11-30)

This section documents decisions made during gap analysis to ensure complete functionality migration.

### 11.1 Non-Required Criteria Logging

**Decision:** When `required=false` on a Criterion, always log evaluation and emit warning if not met.

```python
class Criterion(BaseModel):
    # ... existing fields ...

    def evaluate(self, activity_log: List[ActivityLogEntry]) -> bool:
        """
        Evaluate criterion and log if non-required.

        Non-required criteria:
        - Always logged to activity_log (met or not)
        - Emit warning if not met
        - Return True regardless (don't block)
        """
        satisfied = self.target.is_satisfied()

        if not self.required:
            activity_log.append(ActivityLogEntry(
                timestamp=datetime.now(timezone.utc),
                type=ActivityType.CRITERION_EVALUATED,
                description=f"Non-required criterion '{self.id}': {'met' if satisfied else 'not met'}",
                entity_type="criterion",
                entity_id=self.id,
                context={"criterion_id": self.id, "met": satisfied, "required": False}
            ))
            if not satisfied:
                logger.warning(f"Non-required criterion not met: {self.description}")
            return True  # Non-required always passes

        return satisfied
```

### 11.2 Reverse Dependency Index via Database View

**Decision:** Compute reverse dependencies via SQL view (never stale, always accessible).

```sql
-- View for reverse dependency lookup ("who depends on ticket X?")
CREATE VIEW v_reverse_dependencies AS
SELECT
    json_extract(c.target_data, '$.completable_id') AS blocked_ticket_id,
    c.ticket_id AS blocking_ticket_id,
    c.blocks_transition_to,
    c.description
FROM criteria c
WHERE c.target_type = 'completable';

-- Index for fast lookups
CREATE INDEX idx_criteria_completable_id ON criteria(
    json_extract(target_data, '$.completable_id')
) WHERE target_type = 'completable';
```

**Python accessor:**
```python
def get_dependents(self, ticket_id: str) -> List[str]:
    """Get tickets that depend on this ticket (reverse lookup)."""
    return self._db.execute("""
        SELECT blocking_ticket_id
        FROM v_reverse_dependencies
        WHERE blocked_ticket_id = ?
    """, (ticket_id,)).fetchall()
```

### 11.3 Unified Activity Log (Audit Trail Integration)

**Decision:** Merge audit trail into activity log. All entity changes captured at Roadmap level.

```python
class ActivityLogEntry(BaseModel):
    """Unified activity/audit entry for all changes."""

    # Core fields
    timestamp: datetime
    type: ActivityType
    description: str

    # Entity tracking (for any entity, not just roadmap)
    entity_type: Optional[str] = None  # roadmap, track, sprint, task, criterion
    entity_id: Optional[str] = None

    # Field change tracking (when type is FIELD_CHANGED or STATUS_CHANGED)
    field: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None

    # Attribution
    changed_by: Optional[str] = None
    commit_sha: Optional[str] = None

    # Additional context
    context: Optional[Dict[str, Any]] = None


class ActivityType(str, Enum):
    # High-level lifecycle events
    ROADMAP_STARTED = "roadmap_started"
    ROADMAP_COMPLETED = "roadmap_completed"
    TRACK_STARTED = "track_started"
    TRACK_COMPLETED = "track_completed"
    SPRINT_STARTED = "sprint_started"
    SPRINT_COMPLETED = "sprint_completed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"

    # Field-level audit events
    FIELD_CHANGED = "field_changed"
    STATUS_CHANGED = "status_changed"

    # Criterion events
    CRITERION_MET = "criterion_met"
    CRITERION_EVALUATED = "criterion_evaluated"  # For non-required
    CRITERION_REFRESHED = "criterion_refreshed"

    # System events
    AUTO_PROGRESSION = "auto_progression"
    VALIDATION_WARNING = "validation_warning"
```

### 11.4 Token Estimation (TaskTicket Only)

**Decision:** `estimated_tokens` lives only on TaskTicket. Parents compute via aggregation.

```python
class TaskTicket(HierarchicalTicket):
    """Task-specific semantic fields."""
    task_type: TaskType
    estimated_tokens: int  # Required for tasks
    actual_tokens: Optional[int] = None
    complexity: Complexity = Complexity.MEDIUM
    phase_label: Optional[str] = None


class HierarchicalTicket(Ticket):
    """Layer 2: Ticket with hierarchy-aware accessors."""

    @computed_field
    def computed_tokens(self) -> int:
        """
        Token estimate for this ticket.

        - Ultimate children (tasks): return estimated_tokens
        - Parents: aggregate from children's computed_tokens
        """
        if self.is_ultimate_child:
            # TaskTicket has estimated_tokens
            return getattr(self, 'estimated_tokens', 0)

        # Aggregate from children
        return sum(
            child.computed_tokens
            for child in self._load_children()
        )
```

**Runtime validation on start():**
```python
def start(self, platform_context_window: Optional[int] = None) -> tuple[bool, List[str]]:
    """Start work on this ticket with optional platform validation."""
    can, reasons = self.can_transition_to(TicketStatus.IN_PROGRESS)

    # Platform fit check (warning, not blocker)
    if platform_context_window and self.computed_tokens > platform_context_window:
        warning = (
            f"Ticket requires ~{self.computed_tokens} tokens but platform "
            f"context window is {platform_context_window}. Consider splitting."
        )
        reasons.append(warning)
        logger.warning(warning)
        # Note: This is a WARNING, not a blocker - can still proceed

    if can:
        self.status = TicketStatus.IN_PROGRESS
        self.started_at = datetime.now(timezone.utc)

    return (can, reasons)
```

### 11.5 Auto-Progression with is_automatic Flag

**Decision:** Each CriterionTarget has `is_automatic` property. Parents auto-progress when children complete.

```python
class CriterionTarget(BaseModel):
    """Base for all criterion targets."""

    @abstractmethod
    def is_satisfied(self) -> bool: ...

    @property
    @abstractmethod
    def is_automatic(self) -> bool:
        """Can this target auto-evaluate without human intervention?"""
        ...

    def refresh(self, context: "RefreshContext") -> None:
        """
        Refresh cached state from external source.

        Override in subclasses that support automatic refresh.
        """
        pass


class CompletableTarget(CriterionTarget):
    @property
    def is_automatic(self) -> bool:
        return True  # Can check referenced ticket's status

    def refresh(self, context: "RefreshContext") -> None:
        ticket = context.ticket_registry.get(self.completable_id)
        self.current_status = ticket.status if ticket else None
        self.last_checked = datetime.now(timezone.utc)


class FileExistsTarget(CriterionTarget):
    @property
    def is_automatic(self) -> bool:
        return True  # Can check filesystem

    def refresh(self, context: "RefreshContext") -> None:
        self.existing_paths = [p for p in self.paths if Path(p).exists()]
        self.missing_paths = [p for p in self.paths if not Path(p).exists()]
        self.last_checked = datetime.now(timezone.utc)


class TestPassesTarget(CriterionTarget):
    @property
    def is_automatic(self) -> bool:
        return True  # Can run test command

    def refresh(self, context: "RefreshContext") -> None:
        # Run test_command, parse results
        result = context.test_runner.run(self.test_command)
        self.last_result = result
        self.last_checked = datetime.now(timezone.utc)


class ManualTarget(CriterionTarget):
    @property
    def is_automatic(self) -> bool:
        return False  # Requires human assessment

    # No refresh() - must be set via assess() method


class ThresholdTarget(CriterionTarget):
    @property
    def is_automatic(self) -> bool:
        return True  # Can query metric source

    def refresh(self, context: "RefreshContext") -> None:
        self.current_value = context.metrics.get(self.metric_name)
        self.last_checked = datetime.now(timezone.utc)


class ExternalTarget(CriterionTarget):
    @property
    def is_automatic(self) -> bool:
        return True  # Can query external system

    def refresh(self, context: "RefreshContext") -> None:
        if self.endpoint:
            self.current_status = context.http_client.get_status(self.endpoint)
        self.last_checked = datetime.now(timezone.utc)
```

**Auto-progression algorithm:**
```python
def auto_progress(self, context: "RefreshContext") -> List[str]:
    """
    Refresh automatic criteria and progress status if possible.

    Returns list of transitions made.
    """
    transitions = []

    # Step 1: Refresh all automatic criteria
    for criterion in self.criteria:
        if criterion.target.is_automatic:
            criterion.target.refresh(context)

    # Step 2: Check each possible transition in order
    status_order = [
        TicketStatus.IN_PROGRESS,
        TicketStatus.COMPLETION_GATE_CHECK,
        TicketStatus.COMPLETED,
        TicketStatus.PRODUCTION_GATE_CHECK,
        TicketStatus.PRODUCTION_READY,
    ]

    for target_status in status_order:
        if self.status.precedes(target_status):
            can, reasons = self.can_transition_to(target_status)
            if can:
                old_status = self.status
                self._transition_to(target_status)
                transitions.append(f"{self.id}: {old_status} → {target_status}")

                # Log the auto-progression
                context.activity_log.append(ActivityLogEntry(
                    timestamp=datetime.now(timezone.utc),
                    type=ActivityType.AUTO_PROGRESSION,
                    description=f"Auto-progressed from {old_status} to {target_status}",
                    entity_type=self.ticket_type,
                    entity_id=self.id,
                    field="status",
                    old_value=old_status.value,
                    new_value=target_status.value
                ))

    return transitions
```

### 11.6 GitCommit with Completion Tracking

**Decision:** Single GitCommit class. Completion data stored in git message. Pre-commit hook verifies criteria.

```python
class GitCommit(BaseModel):
    """A git commit with platform and completion metadata."""

    sha: str  # Full 40-char SHA
    message: str
    date: datetime
    author: str

    # Platform tracking
    platform: str  # claude-code, goose, cursor, etc.
    submitted_at: datetime

    # Extracted from message (parsed on load)
    completes_tickets: List[str] = Field(default_factory=list)

    @classmethod
    def from_git(cls, sha: str, repo_path: Path, platform: str) -> "GitCommit":
        """Parse git commit and extract completion markers."""
        # Get commit data
        result = subprocess.run(
            ["git", "show", "-s", "--format=%H%n%s%n%b%n%aI%n%an", sha],
            cwd=repo_path, capture_output=True, text=True
        )
        lines = result.stdout.strip().split('\n')
        full_sha, subject, *body_lines, date_str, author = lines
        body = '\n'.join(body_lines)

        # Extract "Completes: ticket-id" markers
        completes = []
        for line in body.split('\n'):
            if line.startswith('Completes:'):
                ticket_id = line.replace('Completes:', '').strip()
                completes.append(ticket_id)

        return cls(
            sha=full_sha,
            message=f"{subject}\n\n{body}".strip(),
            date=datetime.fromisoformat(date_str),
            author=author,
            platform=platform,
            submitted_at=datetime.now(timezone.utc),
            completes_tickets=completes
        )
```

**Git message convention:**
```
feat(component): Description of changes

- Bullet point 1
- Bullet point 2

Completes: sqlite-backend-6-task-009
Completes: sqlite-backend-6-task-010

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Pre-commit hook verification:**
```python
def verify_completion_claims(commit_message: str, root_dir: Path) -> List[str]:
    """
    Verify that claimed completions meet all criteria.

    Called by pre-commit hook when commit contains "Completes:" lines.
    Returns list of errors (empty = OK to commit).
    """
    errors = []

    # Extract claimed completions
    claimed = []
    for line in commit_message.split('\n'):
        if line.startswith('Completes:'):
            ticket_id = line.replace('Completes:', '').strip()
            claimed.append(ticket_id)

    for ticket_id in claimed:
        ticket = load_ticket(ticket_id, root_dir)
        if not ticket:
            errors.append(f"Unknown ticket: {ticket_id}")
            continue

        can, reasons = ticket.can_transition_to(TicketStatus.COMPLETED)

        if not can:
            errors.append(
                f"Cannot complete {ticket_id} - criteria not met:\n" +
                "\n".join(f"  - {r}" for r in reasons)
            )

    return errors
```

### 11.7 DeliverableType on FileExistsTarget

**Decision:** Keep type classification for queryability and reporting.

```python
class DeliverableType(str, Enum):
    CODE = "code"
    TEST = "test"
    DOCUMENTATION = "documentation"
    CONFIG = "config"
    OTHER = "other"


class FileExistsTarget(CriterionTarget):
    """Criterion met when file(s) exist."""

    paths: List[str]
    all_required: bool = True
    deliverable_type: DeliverableType = DeliverableType.OTHER  # Classification

    # Cached state
    existing_paths: List[str] = Field(default_factory=list)
    missing_paths: List[str] = Field(default_factory=list)
    last_checked: Optional[datetime] = None

    @property
    def is_automatic(self) -> bool:
        return True

    def is_satisfied(self) -> bool:
        if self.all_required:
            return len(self.missing_paths) == 0
        return len(self.existing_paths) > 0

    def refresh(self, context: "RefreshContext") -> None:
        self.existing_paths = [p for p in self.paths if Path(p).exists()]
        self.missing_paths = [p for p in self.paths if not Path(p).exists()]
        self.last_checked = datetime.now(timezone.utc)
```

**YAML format:**
```yaml
criteria:
  - id: impl-deliverable
    description: Implementation code
    blocks_transition_to: completed
    target:
      type: file_exists
      deliverable_type: code
      paths:
        - vibey/roadmap/models/ticket/base.py
        - vibey/roadmap/models/ticket/__init__.py
```

---

## Appendix C: Updated Enum Definitions

```python
class DeliverableType(str, Enum):
    """Classification for file-based deliverables."""
    CODE = "code"
    TEST = "test"
    DOCUMENTATION = "documentation"
    CONFIG = "config"
    OTHER = "other"


class ActivityType(str, Enum):
    """Types of activity log entries (unified audit trail)."""
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

## Appendix D: Updated Database Schema

```sql
-- Add to existing schema from Part 7

-- Unified activity log table (replaces separate audit_trail)
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT NOT NULL,

    -- Entity tracking
    entity_type TEXT,
    entity_id TEXT,

    -- Field change tracking
    field TEXT,
    old_value TEXT,
    new_value TEXT,

    -- Attribution
    changed_by TEXT,
    commit_sha TEXT,

    -- Additional context (JSON)
    context TEXT
);

CREATE INDEX idx_activity_log_entity ON activity_log(entity_type, entity_id);
CREATE INDEX idx_activity_log_timestamp ON activity_log(timestamp DESC);
CREATE INDEX idx_activity_log_type ON activity_log(type);

-- Reverse dependency view
CREATE VIEW v_reverse_dependencies AS
SELECT
    json_extract(c.target_data, '$.completable_id') AS blocked_ticket_id,
    c.ticket_id AS blocking_ticket_id,
    c.blocks_transition_to,
    c.description
FROM criteria c
WHERE c.target_type = 'completable';

-- Index for reverse dependency lookups
CREATE INDEX idx_criteria_completable_target ON criteria(
    json_extract(target_data, '$.completable_id')
) WHERE target_type = 'completable';
```

---

## Part 12: YAML Migration Strategy

This section documents the complete migration strategy from legacy YAML format to the unified ticket architecture, ensuring zero data loss.

### 12.1 Migration Overview

**YAML File Types:** 4 (roadmap.yaml, track.yaml, sprint.yaml, task.yaml)
**Total Unique Fields:** ~85 across all types
**Fields with Direct Mapping:** ~60 (71%)
**Fields Now Computed (no storage):** ~10 (12%)
**Fields Migrated to Markdown:** ~10 (12%)
**Fields with Transformation Required:** ~5 (5%)
**Fields at Risk of Data Loss:** 0

### 12.2 Field Mapping Tables

#### Roadmap YAML → RoadmapTicket

| Legacy YAML Field | Unified Model | Notes |
|-------------------|---------------|-------|
| `roadmap.id` | `RoadmapTicket.id` | Direct |
| `roadmap.name` | `RoadmapTicket.name` | Direct |
| `roadmap.version` | `RoadmapTicket.version` | Direct |
| `roadmap.status` | `RoadmapTicket.status` | Enum mapping |
| `roadmap.blocked` | Computed from `criteria` | No longer stored |
| `roadmap.created` | `RoadmapTicket.created_at` | Rename |
| `roadmap.started` | `RoadmapTicket.started_at` | Rename |
| `roadmap.completed` | `RoadmapTicket.completed_at` | Rename |
| `roadmap.deployed` | `RoadmapTicket.deployed_at` | Rename |
| `roadmap.deployed_platforms` | `RoadmapTicket.deployed_platforms` | Direct |
| `roadmap.activity_log` | `RoadmapTicket.activity_log` | Direct |
| `roadmap.tracks[]` | `criteria` with `CompletableTarget` | Children become criteria |
| `roadmap.dependencies` | `criteria` with `blocks_transition_to: in_progress` | Deps become criteria |
| `roadmap.progress` | Computed from `criteria` | No longer stored |
| `roadmap.version_strategy` | `VERSIONING_POLICY.md` file | Migrate to markdown |
| `roadmap.version_history` | `CHANGELOG.md` file | Migrate to markdown |
| `roadmap.metadata.notes` | `context/NOTES.md` file | Migrate to markdown |
| `roadmap.standards` | `requirements_local[]` | Transformation |

#### Track YAML → TrackTicket

| Legacy YAML Field | Unified Model | Notes |
|-------------------|---------------|-------|
| `track.id` | `TrackTicket.id` | Direct |
| `track.name` | `TrackTicket.name` | Direct |
| `track.roadmap_id` | `TrackTicket.parent_ref` | Rename |
| `track.status` | `TrackTicket.status` | Enum mapping |
| `track.blocked` | Computed from `criteria` | No longer stored |
| `track.priority` | `TrackTicket.priority` | Direct |
| `track.created` | `TrackTicket.created_at` | Rename |
| `track.started` | `TrackTicket.started_at` | Rename |
| `track.completed` | `TrackTicket.completed_at` | Rename |
| `track.commits` | `TrackTicket.commits_local` | Rename |
| `track.sprints[]` | `criteria` with `CompletableTarget` | Children become criteria |
| `track.dependencies` | `criteria` with `blocks_transition_to: in_progress` | Deps become criteria |
| `track.blocks[]` | `v_reverse_dependencies` view | Computed |
| `track.quality_gates[]` | `criteria` with `ThresholdTarget` | Gates become criteria |
| `track.progress` | Computed from `criteria` | No longer stored |
| `track.deliverables[]` | `criteria` with `FileExistsTarget` | Deliverables become criteria |
| `track.estimated_duration` | `TrackTicket.estimated_duration_local` | New field |
| `track.strategic_value[]` | `TrackTicket.strategic_value` | Direct |
| `track.assigned_agents[]` | `assigned_agents_local` | Direct |
| `track.standards[]` | `requirements_local[]` | Transformation |
| `track.metadata.notes` | `context/NOTES.md` file | Migrate to markdown |

#### Sprint YAML → SprintTicket

| Legacy YAML Field | Unified Model | Notes |
|-------------------|---------------|-------|
| `sprint.id` | `SprintTicket.id` | Direct |
| `sprint.name` | `SprintTicket.name` | Direct |
| `sprint.track_id` | `SprintTicket.parent_ref` | Rename |
| `sprint.roadmap_id` | Computed from hierarchy | Available via parent chain |
| `sprint.status` | `SprintTicket.status` | Enum mapping |
| `sprint.blocked` | Computed from `criteria` | No longer stored |
| `sprint.created` | `SprintTicket.created_at` | Rename |
| `sprint.started` | `SprintTicket.started_at` | Rename |
| `sprint.completed` | `SprintTicket.completed_at` | Rename |
| `sprint.completion_gate_check_at` | `SprintTicket.completion_gate_check_at` | Direct |
| `sprint.production_gate_check_at` | `SprintTicket.production_gate_check_at` | Direct |
| `sprint.production_ready_at` | `SprintTicket.production_ready_at` | Direct |
| `sprint.deployed_at` | `SprintTicket.deployed_at` | Direct |
| `sprint.plan_file` | `SprintTicket.plan_file` | Direct |
| `sprint.commits[]` | `SprintTicket.commits_local` | Rename |
| `sprint.tasks[]` | `criteria` with `CompletableTarget` | Children become criteria |
| `sprint.blocks[]` | `v_reverse_dependencies` view | Computed |
| `sprint.development_gates[]` | `criteria` with `blocks_transition_to: in_progress` | Gates become criteria |
| `sprint.deliverables[]` | `criteria` with `FileExistsTarget` | Deliverables become criteria |
| `sprint.progress` | Computed from `criteria` | No longer stored |
| `sprint.standards[]` | `requirements_local[]` | Transformation |
| `sprint.metadata.estimated_duration` | `SprintTicket.estimated_duration_local` | New field |

#### Task YAML → TaskTicket

| Legacy YAML Field | Unified Model | Notes |
|-------------------|---------------|-------|
| `task.id` | `TaskTicket.id` | Direct |
| `task.title` | `TaskTicket.name` | Rename |
| `task.description` | `TaskTicket.description` | Direct |
| `task.sprint_id` | `TaskTicket.parent_ref` | Rename |
| `task.track_id` | Computed from hierarchy | Available via parent chain |
| `task.roadmap_id` | Computed from hierarchy | Available via parent chain |
| `task.task_type` | `TaskTicket.task_type` | Direct |
| `task.status` | `TaskTicket.status` | Enum mapping |
| `task.blocked` | Computed from `criteria` | No longer stored |
| `task.created` | `TaskTicket.created_at` | Rename |
| `task.started` | `TaskTicket.started_at` | Rename |
| `task.completed` | `TaskTicket.completed_at` | Rename |
| `task.assigned_agent` | `TaskTicket.assigned_agents_local[0]` | Single → List |
| `task.priority` | `TaskTicket.priority` | Direct (inherited from Ticket) |
| `task.estimated_tokens` | `TaskTicket.estimated_tokens` | Direct |
| `task.actual_tokens` | `TaskTicket.actual_tokens` | Direct |
| `task.complexity` | `TaskTicket.complexity` | Direct |
| `task.phase_label` | `TaskTicket.phase_label` | Direct |
| `task.commits[]` | `TaskTicket.commits_local` | Rename |
| `task.dependencies[]` | `criteria` with `CompletableTarget`, `blocks_transition_to: in_progress` | Deps become criteria |
| `task.blocks[]` | `v_reverse_dependencies` view | Computed |
| `task.deliverables[]` | `criteria` with `FileExistsTarget` | Deliverables become criteria |
| `task.gate_info` | `criteria` with `ThresholdTarget` | Gates become criteria |
| `task.audit_results` | `criteria` with `FileExistsTarget` pointing to markdown | Migrate to deliverable |
| `task.metadata.notes` | `{task-id}/NOTES.md` file | Migrate to markdown |

### 12.3 Resolved Gaps

All identified gaps have been resolved with zero data loss:

| Gap ID | Field | Resolution |
|--------|-------|------------|
| GAP-ML-001 | `priority` | Add as `Optional[Priority]` on `Ticket` with `effective_priority` inheritance |
| GAP-ML-002 | `version_strategy`, `metadata.*` | Migrate to markdown files with optional `FileExistsTarget` criteria |
| GAP-ML-003 | `standards[]` | Transform 1:1 to `requirements_local[]` |
| GAP-ML-004 | `estimated_duration` | Add as optional field with parent aggregation |
| GAP-ML-005 | `deferred` | Add as boolean flag on `Ticket`; excluded from completion checks |
| GAP-ML-006 | Audit fields | Migrate to `ThresholdTarget` criteria + markdown deliverables |
| GAP-ML-007 | `gate_info` | Maps directly to `Criterion` + `ThresholdTarget` |

### 12.4 New Fields Added to Model

Based on gap analysis, the following fields are added:

```python
class Ticket(Completable):
    """Layer 1: Base ticket with work semantics."""

    # ... existing fields ...

    # Priority (optional - used by Track and Task)
    priority: Optional[Priority] = None

    # Deferral flag - marks ticket as optional for production
    deferred: bool = False

    # Duration tracking (optional, stored on any level)
    estimated_duration_local: Optional[str] = None
    actual_duration_local: Optional[str] = None


class HierarchicalTicket(Ticket):
    """Layer 2: Ticket with hierarchy-aware accessors."""

    @property
    def effective_priority(self) -> Priority:
        """Priority with inheritance from parent."""
        if self.priority is not None:
            return self.priority
        parent = self._load_parent()
        if parent and hasattr(parent, 'effective_priority'):
            return parent.effective_priority
        return Priority.MEDIUM

    @property
    def estimated_duration(self) -> Optional[str]:
        """Duration with parent aggregation from children."""
        if self.estimated_duration_local:
            return self.estimated_duration_local
        if self.is_parent:
            return self._aggregate_duration_from_children()
        return None

    @property
    def required_children(self) -> List[str]:
        """Children that are not deferred."""
        return [
            c.target.completable_id
            for c in self.criteria
            if isinstance(c.target, CompletableTarget)
            and not self._is_child_deferred(c.target.completable_id)
        ]
```

### 12.5 Standards → Requirements Transformation

The legacy `standards[]` maps 1:1 to `requirements_local[]`:

| Legacy Standard | Unified Requirement |
|-----------------|---------------------|
| `Standard.id` | `Requirement.id` |
| `Standard.name` | `Requirement.name` |
| `Standard.description` | `Requirement.description` |
| `Standard.type` | `CriterionTemplate.target_type` |
| `Standard.enforcement` | `Criterion.required` + behavior |
| `Standard.validation` | `CriterionTemplate.target_config` |
| `Standard.enabled` | `Requirement.enabled` |
| `Standard.overrides[]` | `Requirement.overrides[]` |

**StandardType → CriterionTargetType Mapping:**

| StandardType | CriterionTargetType |
|--------------|---------------------|
| `COMMIT_CHECK` | `threshold` |
| `FILE_CHECK` | `file_exists` |
| `TEST_RUN` | `test_passes` |
| `CUSTOM_SCRIPT` | `external` |

**EnforcementMode → Unified Behavior:**

| EnforcementMode | Unified Behavior |
|-----------------|------------------|
| `BLOCKING` | `Criterion.required = True` |
| `WARNING` | `Criterion.required = False` + log warning |
| `AUDIT` | `Criterion.required = False` + log to activity_log |

### 12.6 GateInfo → Criterion Mapping

| GateInfo Field | Unified Model |
|----------------|---------------|
| `blocks_status: "completed"` | `Criterion.blocks_transition_to: COMPLETED` |
| `blocks_status: "production_ready"` | `Criterion.blocks_transition_to: PRODUCTION_READY` |
| `threshold: 80` | `ThresholdTarget.threshold: 80` |
| `is_blocking: true` | `Criterion.required: true` |
| `score: 85` | `ThresholdTarget.current_value: 85` |

### 12.7 Computed Fields (No Storage)

The following fields are computed and NOT stored:

| Legacy Field | Computed From |
|--------------|---------------|
| `*.blocked` | `criteria` where `is_met=false` |
| `*.progress` | `criteria` completion ratio |
| `*.blocks[]` | `v_reverse_dependencies` SQL view |
| `*.depended_on_by[]` | `v_reverse_dependencies` SQL view |
| `track.sprints[].tasks_count` | Count of child `CompletableTarget` criteria |
| `roadmap.progress.*` | Aggregate from children |

### 12.8 Migration Script Template

```python
def migrate_legacy_yaml_to_unified(legacy: dict, entity_type: str) -> dict:
    """
    Migrate legacy YAML to unified model, preserving all data.
    """
    # Core field mapping
    unified = map_core_fields(legacy, entity_type)

    # Transform relationships to criteria
    unified['criteria'] = []
    unified['criteria'].extend(migrate_dependencies(legacy))
    unified['criteria'].extend(migrate_children(legacy))
    unified['criteria'].extend(migrate_deliverables(legacy))
    unified['criteria'].extend(migrate_gates(legacy))

    # Transform standards to requirements
    unified['requirements_local'] = migrate_standards(legacy)

    # Add new fields
    unified['priority'] = legacy.get('priority')
    unified['deferred'] = legacy.get('deferred', False)
    unified['estimated_duration_local'] = legacy.get('estimated_duration')

    # Validate no data loss
    validate_round_trip(legacy, unified)

    return unified


def migrate_dependencies(legacy: dict) -> List[Criterion]:
    """Convert blocked_by/depends_on to criteria."""
    criteria = []

    for dep in legacy.get('blocked_by', []) + legacy.get('depends_on', []):
        blocker_id = dep.get('blocker_id') or dep.get('target_id')
        criteria.append(Criterion(
            id=f"dep-{blocker_id}",
            description=f"Depends on: {blocker_id}",
            target=CompletableTarget(
                completable_id=blocker_id,
                required_status=TicketStatus(dep.get('required_status', 'completed'))
            ),
            blocks_transition_to=TicketStatus.IN_PROGRESS
        ))

    return criteria


def migrate_deliverables(legacy: dict) -> List[Criterion]:
    """Convert deliverables to FileExistsTarget criteria."""
    criteria = []

    for d in legacy.get('deliverables', []):
        paths = d if isinstance(d, list) else [d]
        criteria.append(Criterion(
            id=f"deliv-{len(criteria)}",
            description=f"Deliverable: {paths[0]}",
            target=FileExistsTarget(paths=paths),
            blocks_transition_to=TicketStatus.COMPLETED
        ))

    return criteria


def migrate_standards(legacy: dict) -> List[Requirement]:
    """Convert standards to requirements."""
    requirements = []

    for std in legacy.get('standards', []):
        target_type_map = {
            'COMMIT_CHECK': CriterionTargetType.THRESHOLD,
            'FILE_CHECK': CriterionTargetType.FILE_EXISTS,
            'TEST_RUN': CriterionTargetType.TEST_PASSES,
            'CUSTOM_SCRIPT': CriterionTargetType.EXTERNAL,
        }

        requirements.append(Requirement(
            id=std['id'],
            name=std['name'],
            description=std.get('description', ''),
            criterion_template=CriterionTemplate(
                target_type=target_type_map.get(std['type'], CriterionTargetType.EXTERNAL),
                target_config=std.get('validation', {}),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
            applicability=ApplicabilityRules(),
            inherit_mode=InheritMode.INHERIT,
            enabled=std.get('enabled', True),
        ))

    return requirements
```

### 12.9 Database Schema Additions

```sql
-- Add new fields to tickets table
ALTER TABLE tickets ADD COLUMN priority TEXT;
ALTER TABLE tickets ADD COLUMN deferred INTEGER DEFAULT 0;
ALTER TABLE tickets ADD COLUMN estimated_duration_local TEXT;
ALTER TABLE tickets ADD COLUMN actual_duration_local TEXT;

-- Index for priority-based queries
CREATE INDEX idx_tickets_priority ON tickets(priority) WHERE priority IS NOT NULL;

-- View for required vs deferred children
CREATE VIEW v_required_children AS
SELECT
    parent.id AS parent_id,
    child.id AS child_id,
    child.deferred
FROM tickets parent
JOIN criteria c ON c.ticket_id = parent.id
JOIN tickets child ON json_extract(c.target_data, '$.completable_id') = child.id
WHERE c.target_type = 'completable';
```

---

## Part 13: Artifact System Architecture

This section introduces **Artifact as a first-class entity**, independent of tickets. This enables tracking of pre-existing files, generated documentation, framework components, and comprehensive impact analysis.

### 13.1 Design Rationale

**Problem:** In the criteria-centric model (Parts 1-12), artifacts only exist inside `Criterion.target`. This means:
- Pre-existing files (README.md) can't be tracked without a ticket
- Generated documentation isn't linked to what it documents
- Framework components (agents, workflows) exist outside the graph
- Impact analysis requires walking all criteria to find affected files

**Solution:** Make `Artifact` a first-class entity that exists independently. Criteria *reference* artifacts rather than *containing* them.

```
BEFORE (Criteria-Centric):
  Criterion → FileExistsTarget → paths[]
              (artifact buried inside target)

AFTER (Artifact-Centric):
  Artifact (independent entity)
      ↑
  Criterion → ArtifactTarget → artifact_id
              (criterion references artifact)
```

### 13.2 Layer Architecture Update

The artifact system adds a new layer between the database and Completable:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     LAYER 0a: ARTIFACT (NEW)                             │
│  First-class entity for any file-based artifact                          │
│  - Exists independently of tickets                                       │
│  - Tracks provenance (ticket-created, pre-existing, generated, etc.)    │
│  - Links documentation to what it documents                              │
├─────────────────────────────────────────────────────────────────────────┤
│                     LAYER 0b: COMPLETABLE                                │
│  Base abstraction - anything that can be completed via criteria          │
│  - Criteria now reference artifacts via ArtifactTarget                   │
├─────────────────────────────────────────────────────────────────────────┤
│                         LAYER 1: TICKET                                  │
│  Adds work semantics - status, lifecycle, commits, assignments           │
├─────────────────────────────────────────────────────────────────────────┤
│                         LAYER 2: HIERARCHICAL TICKET                     │
│  Adds smart accessors - aggregation, inheritance, computed properties    │
│  - New: artifact aggregation across hierarchy                            │
├─────────────────────────────────────────────────────────────────────────┤
│                         LAYER 3: DOMAIN MODELS                           │
│  RoadmapTicket, TrackTicket, SprintTicket, TaskTicket                    │
│  - New: domain-specific artifact accessors                               │
└─────────────────────────────────────────────────────────────────────────┘
```

### 13.3 Artifact Entity

```python
class Artifact(BaseModel):
    """
    A first-class entity representing any file-based artifact in the project.

    Artifacts exist independently of tickets. They may be:
    - Created by a ticket (provenance.type = TICKET_CREATED)
    - Pre-existing (provenance.type = PRE_EXISTING)
    - Generated from other artifacts (provenance.type = GENERATED)
    - From external sources (provenance.type = EXTERNAL)
    - Vibey framework components (provenance.type = FRAMEWORK)
    """

    # ═══════════════════════════════════════════════════════════════
    # IDENTITY
    # ═══════════════════════════════════════════════════════════════
    id: str  # ULID
    name: str
    description: Optional[str] = None

    # ═══════════════════════════════════════════════════════════════
    # FILE LOCATION
    # ═══════════════════════════════════════════════════════════════
    paths: List[str]  # One artifact may span multiple files
    content_hash: Optional[str] = None  # SHA256 of concatenated file contents
    last_verified: Optional[datetime] = None  # When files were last checked

    # ═══════════════════════════════════════════════════════════════
    # CLASSIFICATION
    # ═══════════════════════════════════════════════════════════════
    artifact_type: ArtifactType
    artifact_subtype: Optional[str] = None  # More specific classification

    # ═══════════════════════════════════════════════════════════════
    # PROVENANCE
    # ═══════════════════════════════════════════════════════════════
    provenance: ArtifactProvenance

    # ═══════════════════════════════════════════════════════════════
    # RELATIONSHIPS
    # ═══════════════════════════════════════════════════════════════

    # Documentation relationship: what does this artifact document?
    documents_artifact_id: Optional[str] = None

    # Dependency relationships: what artifacts does this depend on?
    depends_on_artifact_ids: List[str] = Field(default_factory=list)

    # ═══════════════════════════════════════════════════════════════
    # STATE
    # ═══════════════════════════════════════════════════════════════
    exists: bool = True  # False if files were deleted
    is_stale: bool = False  # For docs: source artifact changed since last update

    # ═══════════════════════════════════════════════════════════════
    # TIMESTAMPS
    # ═══════════════════════════════════════════════════════════════
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ═══════════════════════════════════════════════════════════════
    # COMPUTED PROPERTIES
    # ═══════════════════════════════════════════════════════════════

    @computed_field
    def is_orphan(self) -> bool:
        """True if no criteria reference this artifact."""
        # Computed via database query in repository
        return self._check_orphan_status()

    @computed_field
    def referencing_criteria(self) -> List[str]:
        """Criterion IDs that reference this artifact."""
        # Computed via database query in repository
        return self._get_referencing_criteria()

    @computed_field
    def is_documentation(self) -> bool:
        """True if this artifact documents another artifact."""
        return self.documents_artifact_id is not None

    # ═══════════════════════════════════════════════════════════════
    # STALENESS DETECTION
    # ═══════════════════════════════════════════════════════════════

    def check_staleness(self, artifact_registry: "ArtifactRegistry") -> bool:
        """
        Check if this documentation artifact is stale.

        Returns True if the documented artifact has changed since this
        artifact was last updated.
        """
        if not self.documents_artifact_id:
            return False  # Not documentation, can't be stale

        source = artifact_registry.get(self.documents_artifact_id)
        if not source:
            return True  # Source doesn't exist - definitely stale

        # Compare source's current hash to what we documented
        if source.content_hash != self._documented_source_hash:
            self.is_stale = True
            return True

        self.is_stale = False
        return False

    def mark_updated(self, artifact_registry: "ArtifactRegistry") -> None:
        """
        Mark this documentation as updated (no longer stale).

        Captures the current hash of the documented artifact.
        """
        if self.documents_artifact_id:
            source = artifact_registry.get(self.documents_artifact_id)
            if source:
                self._documented_source_hash = source.content_hash

        self.is_stale = False
        self.updated_at = datetime.now(timezone.utc)
```

### 13.4 Artifact Provenance

```python
class ArtifactProvenance(BaseModel):
    """
    How an artifact came to exist.

    Provenance enables:
    - Distinguishing ticket-created vs pre-existing files
    - Tracking generated documentation sources
    - Identifying framework components
    """

    provenance_type: ProvenanceType

    # ═══════════════════════════════════════════════════════════════
    # FOR TICKET_CREATED
    # ═══════════════════════════════════════════════════════════════
    created_by_ticket_id: Optional[str] = None
    created_by_criterion_id: Optional[str] = None

    # ═══════════════════════════════════════════════════════════════
    # FOR PRE_EXISTING
    # ═══════════════════════════════════════════════════════════════
    discovered_at: Optional[datetime] = None
    discovered_by: Optional[str] = None  # User, scan process, or "filesystem_scan"

    # ═══════════════════════════════════════════════════════════════
    # FOR GENERATED
    # ═══════════════════════════════════════════════════════════════
    generator_type: Optional[str] = None  # "sphinx", "pdoc", "typedoc", "mkdocs"
    generator_config: Optional[Dict[str, Any]] = None
    source_artifact_ids: Optional[List[str]] = None  # Artifacts used to generate this

    # ═══════════════════════════════════════════════════════════════
    # FOR EXTERNAL
    # ═══════════════════════════════════════════════════════════════
    external_source: Optional[str] = None  # URL, package name, etc.
    external_version: Optional[str] = None

    # ═══════════════════════════════════════════════════════════════
    # FOR FRAMEWORK
    # ═══════════════════════════════════════════════════════════════
    framework_component_type: Optional[str] = None  # "agent", "workflow", "template"


class ProvenanceType(str, Enum):
    """How an artifact came to exist."""

    TICKET_CREATED = "ticket_created"  # Created by a ticket's work
    PRE_EXISTING = "pre_existing"      # Existed before roadmap system
    GENERATED = "generated"            # Auto-generated from other artifacts
    EXTERNAL = "external"              # From external source (vendored, fetched)
    FRAMEWORK = "framework"            # Vibey framework component
```

### 13.5 Artifact Type Classification

```python
class ArtifactType(str, Enum):
    """Primary classification of artifacts."""

    # ═══════════════════════════════════════════════════════════════
    # CODE ARTIFACTS
    # ═══════════════════════════════════════════════════════════════
    CODE = "code"          # Source code (.py, .js, .ts, etc.)
    TEST = "test"          # Test files
    CONFIG = "config"      # Configuration files (.yaml, .json, .toml)

    # ═══════════════════════════════════════════════════════════════
    # DOCUMENTATION ARTIFACTS
    # ═══════════════════════════════════════════════════════════════
    DOCUMENTATION = "documentation"  # Project docs (describes current state)
    CONTEXT = "context"              # Ticket context (planning, notes, retros)

    # ═══════════════════════════════════════════════════════════════
    # FRAMEWORK ARTIFACTS
    # ═══════════════════════════════════════════════════════════════
    AGENT = "agent"        # Vibey agent definition
    WORKFLOW = "workflow"  # Vibey workflow definition
    TEMPLATE = "template"  # Handoff or rendering template

    # ═══════════════════════════════════════════════════════════════
    # OTHER ARTIFACTS
    # ═══════════════════════════════════════════════════════════════
    DATA = "data"          # Data files, fixtures, samples
    ASSET = "asset"        # Images, diagrams, media
    SCHEMA = "schema"      # API schemas, database schemas
    OTHER = "other"

    @property
    def is_documentation_type(self) -> bool:
        """True if this type represents documentation."""
        return self in {self.DOCUMENTATION, self.CONTEXT}

    @property
    def is_code_type(self) -> bool:
        """True if this type represents code."""
        return self in {self.CODE, self.TEST, self.CONFIG}

    @property
    def is_framework_type(self) -> bool:
        """True if this is a Vibey framework component."""
        return self in {self.AGENT, self.WORKFLOW, self.TEMPLATE}


class ContextArtifactSubtype(str, Enum):
    """Subtypes for CONTEXT artifacts (ticket planning/execution support)."""

    PLANNING_DOC = "planning_doc"           # Pre-work planning (design doc, RFC)
    IMPLEMENTATION_NOTES = "impl_notes"     # During-work notes
    DECISION_RECORD = "decision_record"     # ADR, design decisions
    AUDIT_REPORT = "audit_report"           # Validation/audit results
    RETROSPECTIVE = "retrospective"         # Post-work reflection


class DocumentationSubtype(str, Enum):
    """Subtypes for DOCUMENTATION artifacts (project docs)."""

    README = "readme"                # README files
    API_REFERENCE = "api_reference"  # API documentation
    USER_GUIDE = "user_guide"        # How-to guides
    ARCHITECTURE = "architecture"    # Architecture documentation
    CHANGELOG = "changelog"          # Version history
    TUTORIAL = "tutorial"            # Step-by-step tutorials
```

### 13.6 ArtifactTarget (New CriterionTarget)

```python
class ArtifactTarget(CriterionTarget):
    """
    Criterion target that references a first-class Artifact.

    This replaces FileExistsTarget for artifact-based criteria.
    FileExistsTarget is retained for cases where you want to check
    file existence without creating an Artifact entity.
    """

    artifact_id: str  # References Artifact.id

    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION MODE
    # ═══════════════════════════════════════════════════════════════
    verification: ArtifactVerification = ArtifactVerification.EXISTS

    # ═══════════════════════════════════════════════════════════════
    # CACHED STATE (denormalized from Artifact for performance)
    # ═══════════════════════════════════════════════════════════════
    artifact_exists: bool = False
    artifact_hash: Optional[str] = None
    artifact_is_stale: bool = False
    last_checked: Optional[datetime] = None

    @property
    def is_automatic(self) -> bool:
        return True

    def is_satisfied(self) -> bool:
        """Check if criterion is satisfied based on verification mode."""
        if self.verification == ArtifactVerification.EXISTS:
            return self.artifact_exists

        elif self.verification == ArtifactVerification.NOT_STALE:
            return self.artifact_exists and not self.artifact_is_stale

        elif self.verification == ArtifactVerification.HASH_UNCHANGED:
            # For checking that artifact content hasn't changed
            artifact = self._load_artifact()
            return (
                self.artifact_exists and
                artifact and
                artifact.content_hash == self.artifact_hash
            )

        return False

    def refresh(self, context: "RefreshContext") -> None:
        """Refresh cached state from artifact registry."""
        artifact = context.artifact_registry.get(self.artifact_id)

        if artifact:
            self.artifact_exists = artifact.exists
            self.artifact_hash = artifact.content_hash
            self.artifact_is_stale = artifact.is_stale
        else:
            self.artifact_exists = False
            self.artifact_hash = None
            self.artifact_is_stale = False

        self.last_checked = datetime.now(timezone.utc)


class ArtifactVerification(str, Enum):
    """How to verify an artifact criterion is satisfied."""

    EXISTS = "exists"              # Files exist (default)
    NOT_STALE = "not_stale"        # Exists AND not stale (for documentation)
    HASH_UNCHANGED = "hash_unchanged"  # Content hasn't changed since criterion created
```

### 13.7 Updated CriterionTargetType Enum

```python
class CriterionTargetType(str, Enum):
    """All criterion target types."""

    # ═══════════════════════════════════════════════════════════════
    # EXISTING TYPES (from Part 2)
    # ═══════════════════════════════════════════════════════════════
    COMPLETABLE = "completable"    # References another ticket
    FILE_EXISTS = "file_exists"    # Raw file existence (no artifact entity)
    TEST_PASSES = "test_passes"    # Test execution
    THRESHOLD = "threshold"        # Metric threshold
    MANUAL = "manual"              # Human assessment
    EXTERNAL = "external"          # External system check

    # ═══════════════════════════════════════════════════════════════
    # NEW: ARTIFACT-BASED TYPES
    # ═══════════════════════════════════════════════════════════════
    ARTIFACT = "artifact"          # References an Artifact entity

    # ═══════════════════════════════════════════════════════════════
    # NEW: CODE VERIFICATION TYPES (Sprint 10)
    # ═══════════════════════════════════════════════════════════════
    SYMBOL_EXISTS = "symbol_exists"      # Verify code symbol (class, function)
    COMMAND_EXISTS = "command_exists"    # Verify CLI command
    MCP_TOOL_EXISTS = "mcp_tool_exists"  # Verify MCP tool
```

### 13.8 Layer Integration

#### Layer 1: Ticket with Artifact Tracking

```python
class Ticket(Completable):
    """Layer 1: Base ticket with work semantics."""

    # ... existing fields from Part 3 ...

    # ═══════════════════════════════════════════════════════════════
    # ARTIFACT ACCESSORS (computed via criteria)
    # ═══════════════════════════════════════════════════════════════

    @property
    def artifact_criteria(self) -> List[Criterion]:
        """Criteria that reference artifacts."""
        return [
            c for c in self.criteria
            if isinstance(c.target, ArtifactTarget)
        ]

    @property
    def referenced_artifact_ids(self) -> List[str]:
        """IDs of artifacts referenced by this ticket's criteria."""
        return [
            c.target.artifact_id
            for c in self.artifact_criteria
        ]

    # ═══════════════════════════════════════════════════════════════
    # LIFECYCLE UPDATES FOR ARTIFACTS
    # ═══════════════════════════════════════════════════════════════

    def complete(self) -> tuple[bool, List[str]]:
        """Complete this ticket, capturing artifact state."""
        can, reasons = self.can_transition_to(TicketStatus.COMPLETED)

        # Additional check: all documentation artifacts must be current
        for criterion in self.artifact_criteria:
            if criterion.target.verification == ArtifactVerification.NOT_STALE:
                if criterion.target.artifact_is_stale:
                    reasons.append(
                        f"Documentation artifact is stale: {criterion.description}"
                    )
                    can = False

        if can:
            self.status = TicketStatus.COMPLETED
            self.completed_at = datetime.now(timezone.utc)

            # Capture artifact hashes for future impact analysis
            self._capture_artifact_state()

        return (can, reasons)
```

#### Layer 2: HierarchicalTicket with Artifact Aggregation

```python
class HierarchicalTicket(Ticket):
    """Layer 2: Ticket with hierarchy-aware accessors."""

    # ... existing accessors from Part 3 ...

    # ═══════════════════════════════════════════════════════════════
    # ARTIFACT AGGREGATION
    # ═══════════════════════════════════════════════════════════════

    @property
    def all_referenced_artifacts(self) -> List[str]:
        """
        All artifact IDs referenced by this ticket and descendants.

        Aggregation: Parents see all descendant artifacts.
        """
        if self.is_ultimate_child:
            return self.referenced_artifact_ids

        all_ids = list(self.referenced_artifact_ids)
        for child in self._load_children():
            all_ids.extend(child.all_referenced_artifacts)

        return list(set(all_ids))  # Deduplicate

    @property
    def stale_documentation_artifacts(self) -> List[str]:
        """
        Artifact IDs for stale documentation in this subtree.

        Aggregation: Parents see all stale docs in descendants.
        """
        stale = []

        for criterion in self.artifact_criteria:
            if (criterion.target.verification == ArtifactVerification.NOT_STALE
                and criterion.target.artifact_is_stale):
                stale.append(criterion.target.artifact_id)

        if not self.is_ultimate_child:
            for child in self._load_children():
                stale.extend(child.stale_documentation_artifacts)

        return list(set(stale))

    @property
    def has_stale_documentation(self) -> bool:
        """True if any documentation in this subtree is stale."""
        return len(self.stale_documentation_artifacts) > 0

    @property
    def documentation_health(self) -> "DocumentationHealth":
        """
        Aggregate documentation health status.
        """
        stale_count = len(self.stale_documentation_artifacts)

        if stale_count == 0:
            return DocumentationHealth.HEALTHY

        # Check if any stale docs block completion
        for criterion in self.artifact_criteria:
            if (criterion.target.artifact_is_stale
                and criterion.blocks_transition_to == TicketStatus.COMPLETED
                and criterion.required):
                return DocumentationHealth.CRITICAL

        return DocumentationHealth.DEGRADED


class DocumentationHealth(str, Enum):
    """Documentation health status."""
    HEALTHY = "healthy"      # All docs current
    DEGRADED = "degraded"    # Some docs stale (non-blocking)
    CRITICAL = "critical"    # Stale docs blocking completion
```

#### Layer 3: Domain-Specific Artifact Accessors

```python
class RoadmapTicket(HierarchicalTicket):
    """Roadmap-specific semantic fields."""

    # ... existing fields ...

    @property
    def all_project_documentation(self) -> List[str]:
        """All DOCUMENTATION type artifacts across the roadmap."""
        return [
            aid for aid in self.all_referenced_artifacts
            if self._get_artifact_type(aid) == ArtifactType.DOCUMENTATION
        ]

    @property
    def framework_components(self) -> List[str]:
        """All AGENT, WORKFLOW, TEMPLATE artifacts."""
        return [
            aid for aid in self.all_referenced_artifacts
            if self._get_artifact_type(aid) in {
                ArtifactType.AGENT,
                ArtifactType.WORKFLOW,
                ArtifactType.TEMPLATE
            }
        ]

    @property
    def orphan_artifacts(self) -> List[str]:
        """Artifacts that exist but aren't referenced by any ticket."""
        # Query from artifact registry
        return self._artifact_registry.get_orphans()


class SprintTicket(HierarchicalTicket):
    """Sprint-specific semantic fields."""

    # ... existing fields ...

    @property
    def sprint_context_artifacts(self) -> List[str]:
        """CONTEXT type artifacts for this sprint (planning docs, etc.)."""
        return [
            c.target.artifact_id for c in self.artifact_criteria
            if self._get_artifact_type(c.target.artifact_id) == ArtifactType.CONTEXT
        ]

    @property
    def planning_artifacts(self) -> List[str]:
        """Context artifacts that block IN_PROGRESS (must exist before starting)."""
        return [
            c.target.artifact_id for c in self.artifact_criteria
            if (self._get_artifact_type(c.target.artifact_id) == ArtifactType.CONTEXT
                and c.blocks_transition_to == TicketStatus.IN_PROGRESS)
        ]


class TaskTicket(HierarchicalTicket):
    """Task-specific semantic fields."""

    # ... existing fields ...

    @property
    def code_artifacts(self) -> List[str]:
        """CODE type artifacts created by this task."""
        return [
            c.target.artifact_id for c in self.artifact_criteria
            if self._get_artifact_type(c.target.artifact_id) == ArtifactType.CODE
        ]

    @property
    def documentation_artifacts(self) -> List[str]:
        """DOCUMENTATION type artifacts created by this task."""
        return [
            c.target.artifact_id for c in self.artifact_criteria
            if self._get_artifact_type(c.target.artifact_id) == ArtifactType.DOCUMENTATION
        ]

    @property
    def undocumented_code_artifacts(self) -> List[str]:
        """Code artifacts that have no documentation artifact linking to them."""
        documented = set()
        for aid in self.documentation_artifacts:
            artifact = self._load_artifact(aid)
            if artifact and artifact.documents_artifact_id:
                documented.add(artifact.documents_artifact_id)

        return [aid for aid in self.code_artifacts if aid not in documented]
```

### 13.9 Database Schema

```sql
-- ═══════════════════════════════════════════════════════════════════════════
-- ARTIFACT TABLE (independent of tickets)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,

    -- File location
    paths TEXT NOT NULL,  -- JSON array of file paths
    content_hash TEXT,    -- SHA256 of concatenated contents
    last_verified TEXT,   -- ISO timestamp

    -- Classification
    artifact_type TEXT NOT NULL,
    artifact_subtype TEXT,

    -- Provenance (JSON object)
    provenance TEXT NOT NULL,

    -- Relationships
    documents_artifact_id TEXT,  -- For documentation: what does this document?
    depends_on_artifact_ids TEXT,  -- JSON array

    -- State
    exists INTEGER NOT NULL DEFAULT 1,
    is_stale INTEGER NOT NULL DEFAULT 0,

    -- For staleness tracking (docs only)
    documented_source_hash TEXT,  -- Hash of source when doc was updated

    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (documents_artifact_id) REFERENCES artifacts(id)
);

-- ═══════════════════════════════════════════════════════════════════════════
-- INDEXES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE INDEX idx_artifacts_type ON artifacts(artifact_type);
CREATE INDEX idx_artifacts_subtype ON artifacts(artifact_subtype);
CREATE INDEX idx_artifacts_documents ON artifacts(documents_artifact_id);
CREATE INDEX idx_artifacts_exists ON artifacts(exists);
CREATE INDEX idx_artifacts_stale ON artifacts(is_stale) WHERE is_stale = 1;

-- Provenance-based indexes
CREATE INDEX idx_artifacts_provenance_type ON artifacts(
    json_extract(provenance, '$.provenance_type')
);
CREATE INDEX idx_artifacts_created_by_ticket ON artifacts(
    json_extract(provenance, '$.created_by_ticket_id')
);

-- ═══════════════════════════════════════════════════════════════════════════
-- UPDATED CRITERIA TABLE (add artifact_id column)
-- ═══════════════════════════════════════════════════════════════════════════

-- Add artifact reference to criteria (for ArtifactTarget)
ALTER TABLE criteria ADD COLUMN artifact_id TEXT REFERENCES artifacts(id);
ALTER TABLE criteria ADD COLUMN artifact_verification TEXT;

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEWS
-- ═══════════════════════════════════════════════════════════════════════════

-- Orphan artifacts (not referenced by any criterion)
CREATE VIEW v_orphan_artifacts AS
SELECT a.*
FROM artifacts a
LEFT JOIN criteria c ON c.artifact_id = a.id
WHERE c.id IS NULL
  AND a.exists = 1;

-- Documentation graph (what documents what)
CREATE VIEW v_documentation_graph AS
SELECT
    doc.id AS documentation_id,
    doc.name AS documentation_name,
    doc.paths AS documentation_paths,
    doc.is_stale,
    doc.documented_source_hash,
    src.id AS source_id,
    src.name AS source_name,
    src.paths AS source_paths,
    src.content_hash AS source_current_hash,
    CASE
        WHEN src.content_hash != doc.documented_source_hash THEN 1
        ELSE 0
    END AS needs_update
FROM artifacts doc
JOIN artifacts src ON doc.documents_artifact_id = src.id
WHERE doc.artifact_type IN ('documentation', 'context');

-- Stale documentation needing update
CREATE VIEW v_stale_documentation AS
SELECT *
FROM v_documentation_graph
WHERE needs_update = 1 OR is_stale = 1;

-- Artifact provenance summary
CREATE VIEW v_artifact_provenance AS
SELECT
    json_extract(provenance, '$.provenance_type') AS provenance_type,
    artifact_type,
    COUNT(*) AS count
FROM artifacts
WHERE exists = 1
GROUP BY json_extract(provenance, '$.provenance_type'), artifact_type;

-- Framework components
CREATE VIEW v_framework_components AS
SELECT *
FROM artifacts
WHERE artifact_type IN ('agent', 'workflow', 'template')
  AND exists = 1;

-- Artifacts by ticket (including all descendants)
CREATE VIEW v_ticket_artifacts AS
SELECT
    t.id AS ticket_id,
    t.ticket_type,
    c.artifact_id,
    a.name AS artifact_name,
    a.artifact_type,
    a.is_stale,
    c.blocks_transition_to
FROM tickets t
JOIN criteria c ON c.ticket_id = t.id
JOIN artifacts a ON a.id = c.artifact_id
WHERE c.artifact_id IS NOT NULL;
```

### 13.10 Impact Analysis

The artifact system enables comprehensive impact analysis when code changes:

```python
class ImpactAnalyzer:
    """Analyzes impact of changes across the artifact graph."""

    def __init__(self, artifact_registry: "ArtifactRegistry", db: "Database"):
        self._artifacts = artifact_registry
        self._db = db

    def analyze_file_changes(self, changed_files: List[str]) -> "ImpactReport":
        """
        Analyze which artifacts are impacted by file changes.

        Called by:
        - Pre-commit hooks
        - Post-commit processing
        - Manual impact checks
        """
        # Find artifacts containing changed files
        directly_impacted = self._find_artifacts_by_files(changed_files)

        # Find documentation that documents impacted artifacts
        stale_documentation = []
        for artifact in directly_impacted:
            docs = self._find_documenting_artifacts(artifact.id)
            stale_documentation.extend(docs)

        # Find tickets affected by stale documentation
        affected_tickets = self._find_affected_tickets(stale_documentation)

        return ImpactReport(
            changed_files=changed_files,
            directly_impacted_artifacts=directly_impacted,
            stale_documentation=stale_documentation,
            affected_tickets=affected_tickets
        )

    def _find_artifacts_by_files(self, files: List[str]) -> List[Artifact]:
        """Find artifacts whose paths include any of the given files."""
        results = []
        for artifact in self._artifacts.all():
            if any(f in artifact.paths for f in files):
                results.append(artifact)
        return results

    def _find_documenting_artifacts(self, artifact_id: str) -> List[Artifact]:
        """Find documentation artifacts that document the given artifact."""
        return self._db.query("""
            SELECT * FROM artifacts
            WHERE documents_artifact_id = ?
        """, (artifact_id,))

    def _find_affected_tickets(self, stale_docs: List[Artifact]) -> List[str]:
        """Find tickets with criteria referencing stale documentation."""
        ticket_ids = set()
        for doc in stale_docs:
            criteria = self._db.query("""
                SELECT ticket_id FROM criteria WHERE artifact_id = ?
            """, (doc.id,))
            ticket_ids.update(c.ticket_id for c in criteria)
        return list(ticket_ids)


@dataclass
class ImpactReport:
    """Report of impact from file changes."""

    changed_files: List[str]
    directly_impacted_artifacts: List[Artifact]
    stale_documentation: List[Artifact]
    affected_tickets: List[str]

    @property
    def has_documentation_impact(self) -> bool:
        return len(self.stale_documentation) > 0

    def to_warning_message(self) -> str:
        """Generate warning message for pre-commit hook."""
        if not self.has_documentation_impact:
            return ""

        lines = ["⚠️  Documentation may need updating:"]
        for doc in self.stale_documentation:
            lines.append(f"  - {doc.name} ({', '.join(doc.paths)})")

        if self.affected_tickets:
            lines.append(f"\nAffected tickets: {', '.join(self.affected_tickets)}")

        return "\n".join(lines)
```

### 13.11 YAML Serialization

```yaml
# Example: Task with artifact-based criteria
task:
  id: sqlite-backend-6-task-001
  name: Implement Layer 1 Base Ticket
  status: not_started

  criteria:
    # Context artifact (must exist before starting)
    - id: design-doc
      description: Design document for ticket implementation
      blocks_transition_to: in_progress
      target:
        type: artifact
        artifact_id: art-sqlite-backend-6-design
        verification: exists

    # Code artifact (must exist to complete)
    - id: code-impl
      description: Base ticket implementation
      blocks_transition_to: completed
      target:
        type: artifact
        artifact_id: art-ticket-base-py
        verification: exists

    # Documentation artifact (must exist and not be stale to complete)
    - id: api-docs
      description: API documentation for Ticket model
      blocks_transition_to: completed
      target:
        type: artifact
        artifact_id: art-ticket-api-docs
        verification: not_stale

---
# Artifact definitions (separate file or inline)
artifacts:
  - id: art-sqlite-backend-6-design
    name: Sprint 6 Design Document
    paths:
      - .vibey/roadmap/sqlite-backend/sqlite-backend-6/context/UNIFIED_TICKET_ARCHITECTURE.md
    artifact_type: context
    artifact_subtype: planning_doc
    provenance:
      provenance_type: ticket_created
      created_by_ticket_id: sqlite-backend-6

  - id: art-ticket-base-py
    name: Ticket Base Implementation
    paths:
      - vibey/roadmap/models/ticket/base.py
      - vibey/roadmap/models/ticket/__init__.py
    artifact_type: code
    provenance:
      provenance_type: ticket_created
      created_by_ticket_id: sqlite-backend-6-task-001

  - id: art-ticket-api-docs
    name: Ticket Model API Reference
    paths:
      - docs/reference/api/ticket-model.md
    artifact_type: documentation
    artifact_subtype: api_reference
    documents_artifact_id: art-ticket-base-py  # Links to code artifact
    provenance:
      provenance_type: ticket_created
      created_by_ticket_id: sqlite-backend-6-task-001
```

### 13.12 Migration Path

The artifact system is introduced in **Sprint 7** (Artifact System Architecture):

```
Sprint 6: Unified Ticket Architecture
         └── Core model: Completable, Criterion, Ticket layers
         └── Part 13 documents artifact design (this section)

Sprint 7: Artifact System Architecture (NEW)
         ├── Artifact entity (Layer 0a)
         ├── ArtifactProvenance and ArtifactType enums
         ├── ArtifactTarget criterion type
         ├── artifacts table in database schema
         ├── ImpactAnalyzer for documentation staleness
         └── Layer integration (Ticket, HierarchicalTicket, Domain Models)

Sprint 8: Serialization Migration
         ├── Update yaml_loader to create Artifact entities
         ├── Convert FileExistsTarget → ArtifactTarget where appropriate
         ├── Establish documents_artifact_id relationships
         └── Add artifact registry sync (scan filesystem for pre-existing)

Sprint 10: Interface Migration
         ├── Add `vibey artifact list/show/adopt` commands
         ├── Add `vibey artifact orphans` command
         ├── Add `vibey artifact impact <files>` command
         └── MCP tools for artifact queries

Sprint 11: Data Validation
         ├── Validate artifact hashes match file contents
         ├── Validate documentation staleness is accurate
         └── Validate orphan detection works
```

### 13.13 Benefits Summary

| Capability | Before (Criteria-Centric) | After (Artifact-Centric) |
|------------|---------------------------|--------------------------|
| Pre-existing files | Can't track without ticket | Register with PRE_EXISTING provenance |
| Orphan detection | Impossible | Query `v_orphan_artifacts` |
| Documentation links | Not modeled | `documents_artifact_id` relationship |
| Staleness detection | Not tracked | `is_stale` flag with hash comparison |
| Impact analysis | Walk all criteria | Query artifact graph directly |
| Framework components | Outside the system | Artifacts with FRAMEWORK provenance |
| Generated docs | Not tracked | GENERATED provenance with source links |
| Deduplication | Same file in N criteria = N checks | One artifact, N criteria reference it |

---

## Appendix E: Updated Enum Definitions (Part 13)

```python
class ArtifactType(str, Enum):
    """Primary classification of artifacts."""
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


class ContextArtifactSubtype(str, Enum):
    """Subtypes for CONTEXT artifacts."""
    PLANNING_DOC = "planning_doc"
    IMPLEMENTATION_NOTES = "impl_notes"
    DECISION_RECORD = "decision_record"
    AUDIT_REPORT = "audit_report"
    RETROSPECTIVE = "retrospective"


class DocumentationSubtype(str, Enum):
    """Subtypes for DOCUMENTATION artifacts."""
    README = "readme"
    API_REFERENCE = "api_reference"
    USER_GUIDE = "user_guide"
    ARCHITECTURE = "architecture"
    CHANGELOG = "changelog"
    TUTORIAL = "tutorial"


class ProvenanceType(str, Enum):
    """How an artifact came to exist."""
    TICKET_CREATED = "ticket_created"
    PRE_EXISTING = "pre_existing"
    GENERATED = "generated"
    EXTERNAL = "external"
    FRAMEWORK = "framework"


class ArtifactVerification(str, Enum):
    """How to verify an artifact criterion is satisfied."""
    EXISTS = "exists"
    NOT_STALE = "not_stale"
    HASH_UNCHANGED = "hash_unchanged"


class DocumentationHealth(str, Enum):
    """Documentation health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
```

---

**Document Version:** 2.2
**Last Updated:** 2025-11-30
**Author:** Claude Code (Artifact System Integration)

**Revision History:**
- v2.2: Added Part 13 - Artifact System Architecture (first-class artifacts, documentation links, impact analysis)
- v2.1: Added Part 12 - Complete YAML Migration Strategy (consolidated from YAML_MIGRATION_GAP_ANALYSIS.md)
- v2.0: Added Part 11 - Gap Analysis Decisions
- v1.0: Initial unified ticket architecture
