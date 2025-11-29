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
| **6** | Unified Ticket Architecture | This sprint - core model classes |
| **7** | Serialization Migration | YAML/SQL loaders/dumpers for new model |
| **8** | Operations Migration | Update all operations to use criteria |
| **9** | Interface Migration | CLI/MCP for criteria display |
| **10** | Data Validation | Computed vs declared integrity checks |
| **11** | Production Cutover | Initialize DB, dual-write, git hooks |
| **12** | File Format Analysis | DEFERRED - optional optimization |

### 8.2 Data Migration (Sprint 7)

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

**Document Version:** 1.0
**Last Updated:** 2025-11-29
**Author:** Claude Code (Sprint Restructuring)
