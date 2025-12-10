# Comprehensive Impact Assessment: Completable Unification

**Created:** 2025-11-29
**Scope:** Full system analysis of transitioning to criteria-based completion model

---

## Executive Summary

The proposed unification treats **everything that can be completed** as a `Completable` with **completion criteria**. This is a fundamental architectural change that:

1. **Simplifies the mental model** - One abstraction instead of three
2. **Unifies progress tracking** - Same formula everywhere
3. **Makes relationships explicit** - Children are visible criteria
4. **Requires significant migration** - All layers affected

**Impact Level: HIGH** - Touches models, serialization, database, operations, CLI, MCP

---

## Part 1: Conceptual Model Change

### Before: Three Separate Systems

```
┌─────────────────────────────────────────────────────────────────┐
│                         CURRENT MODEL                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Ticket                                                         │
│  ├── children_ids: List[str]     ← Explicit parent-child        │
│  ├── parent_id: str              ← Explicit parent-child        │
│  ├── deliverables: List[Deliv]   ← Separate concept             │
│  ├── success_criteria: List[SC]  ← Separate concept             │
│  ├── progress: Progress          ← Computed from children       │
│  └── blocked: bool               ← Computed from dependencies   │
│                                                                 │
│  Deliverable                                                    │
│  ├── paths: List[str]                                           │
│  ├── exists: bool                                               │
│  └── success_criteria: List[SC]  ← Deliverable-specific         │
│                                                                 │
│  SuccessCriterion                                               │
│  ├── description: str                                           │
│  ├── met: bool                                                  │
│  └── assessed_by: str                                           │
│                                                                 │
│  PROGRESS CALCULATION:                                          │
│  - Ticket: completed_children / total_children                  │
│  - Deliverable: exists AND all criteria met                     │
│  - No unified formula                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### After: Unified Criteria Model

```
┌─────────────────────────────────────────────────────────────────┐
│                         UNIFIED MODEL                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Completable (base)                                             │
│  ├── id: str                                                    │
│  ├── name: str                                                  │
│  ├── criteria: List[Criterion]   ← THE source of truth          │
│  │                                                              │
│  ├── is_complete: bool           ← all(c.is_met for c in crit)  │
│  ├── progress: float             ← met_count / total_count      │
│  ├── children: List[Completable] ← derived from criteria        │
│  └── blocking_reasons: List[str] ← unmet criteria descriptions  │
│                                                                 │
│  Criterion                                                      │
│  ├── id: str                                                    │
│  ├── description: str                                           │
│  ├── target: CriterionTarget     ← polymorphic                  │
│  │   ├── CompletableTarget       → child ticket                 │
│  │   ├── FileExistsTarget        → deliverable                  │
│  │   ├── TestPassesTarget        → test requirement             │
│  │   ├── ThresholdTarget         → metric check                 │
│  │   ├── ManualTarget            → human assessment             │
│  │   └── ExternalTarget          → external system              │
│  │                                                              │
│  └── is_met: bool                ← target.is_satisfied()        │
│                                                                 │
│  Ticket (extends Completable)                                   │
│  ├── status: TicketStatus        ← lifecycle (not in base)      │
│  ├── assigned_agents: List[str]  ← work assignment              │
│  ├── commits: List[GitCommit]    ← work evidence                │
│  └── requirements: List[Req]     ← inherited policies           │
│                                                                 │
│  PROGRESS CALCULATION (universal):                              │
│  - Any Completable: met_criteria / total_criteria               │
│  - Same formula for Task, Sprint, Track, Roadmap                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 2: Layer-by-Layer Impact

### Layer 1: Base Ticket

**Current Fields (task.py lines 182-244):**
```python
class Task:
    # Identity
    id, sprint_id, track_id, roadmap_id, title, description

    # Status
    status, blocked

    # Timestamps
    created, started, completed

    # Dependencies (KEEP - sibling relationships)
    dependencies: List[TaskDependency]
    blocks: List[TaskDependency]
    depends_on: List[DependencyStatus]

    # Content (REMOVE - becomes criteria)
    deliverables: List[Deliverable]        # → FileExistsTarget criteria
    commits: List[GitCommit]               # KEEP - work evidence

    # Gate info (REMOVE - becomes criteria)
    gate_info: Optional[GateInfo]          # → ThresholdTarget criteria
    audit_results: Optional[AuditResults]  # → assessment state in criteria
```

**Proposed Layer 1 Fields:**
```python
class Ticket(Completable):
    # From Completable
    id: str
    name: str
    description: Optional[str]
    criteria: List[Criterion]              # THE source of truth

    # Ticket-specific identity
    parent_ref: Optional[str]              # For fast parent lookup (denormalized)

    # Ticket-specific lifecycle
    status: TicketStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    # Ticket-specific work tracking
    commits: List[GitCommit]               # Work evidence
    assigned_agents: List[str]

    # Ticket-specific blocking (sibling dependencies)
    dependencies: List[Dependency]         # Sibling blockers (not children)

    # Ticket-specific policies
    requirements_local: List[Requirement]  # Criterion templates

    # Computed from criteria
    @computed_field
    def children(self) -> List[str]:
        return [c.target.completable_id for c in self.criteria
                if isinstance(c.target, CompletableTarget)]

    @computed_field
    def is_complete(self) -> bool:
        return all(c.is_met() for c in self.criteria)

    @computed_field
    def progress(self) -> Progress:
        total = len(self.criteria)
        met = sum(1 for c in self.criteria if c.is_met())
        return Progress(total=total, completed=met)
```

**Key Changes:**
| Field | Change | Reason |
|-------|--------|--------|
| `deliverables` | REMOVED | → `criteria` with `FileExistsTarget` |
| `success_criteria` | REMOVED | → `criteria` (merged) |
| `children_ids` | REMOVED | → computed from `CompletableTarget` criteria |
| `parent_id` | RENAMED | → `parent_ref` (denormalized for lookup) |
| `gate_info` | REMOVED | → `criteria` with `ThresholdTarget` |
| `blocked` | REMOVED | → computed from `dependencies` |
| `progress` | COMPUTED | → from `criteria` met/total |

### Layer 2: HierarchicalTicket (Smart Accessors)

**Current Design:**
```python
class HierarchicalTicket(Ticket):
    # Smart accessors
    @property
    def commits(self) -> List[GitCommit]:
        if self.is_ultimate_child:
            return self.commits_local
        return self.commits_aggregated  # from children

    @property
    def standards(self) -> List[Standard]:
        if self.is_ultimate_parent:
            return self.standards_local
        return self.standards_effective  # inherited
```

**Revised Design:**
```python
class HierarchicalTicket(Ticket):
    # Hierarchy attributes (unchanged)
    @computed_field
    def is_parent(self) -> bool:
        return len(self.children) > 0

    @computed_field
    def is_child(self) -> bool:
        return self.parent_ref is not None

    # Smart accessors (simplified)
    @property
    def commits(self) -> List[GitCommit]:
        """Commits: local if leaf, aggregated if parent."""
        if self.is_ultimate_child:
            return self.commits_local
        return self._aggregate_commits_from_children()

    @property
    def requirements_effective(self) -> List[Requirement]:
        """Requirements: inherited from ancestors, instantiated as criteria."""
        return self._resolve_requirements()

    # NEW: Convenience accessors for criteria types
    @property
    def deliverables(self) -> List[Criterion]:
        """Criteria that are file-based."""
        return [c for c in self.criteria
                if isinstance(c.target, FileExistsTarget)]

    @property
    def tests(self) -> List[Criterion]:
        """Criteria that are test-based."""
        return [c for c in self.criteria
                if isinstance(c.target, TestPassesTarget)]

    @property
    def subtasks(self) -> List[Criterion]:
        """Criteria that reference other tickets (children)."""
        return [c for c in self.criteria
                if isinstance(c.target, CompletableTarget)]
```

**Key Changes:**
| Accessor | Change | Reason |
|----------|--------|--------|
| `children` | COMPUTED | From `CompletableTarget` criteria |
| `progress` | SIMPLIFIED | Universal formula: met/total |
| `deliverables` | CONVENIENCE | Filters criteria by target type |
| `tests` | NEW | Filters criteria by target type |
| `subtasks` | NEW | Filters criteria by target type |

### Layer 3: Domain Models

**Current L3 Fields:**

| Model | Semantic Fields |
|-------|----------------|
| RoadmapTicket | version, activity_log, deployed_platforms |
| TrackTicket | priority, strategic_value |
| SprintTicket | plan_file, development_gates, lifecycle timestamps |
| TaskTicket | task_type, estimated_tokens, gate_info, complexity |

**Changes Needed:**

| Model | Change |
|-------|--------|
| RoadmapTicket | No changes (semantic fields only) |
| TrackTicket | No changes (semantic fields only) |
| SprintTicket | `development_gates` → REMOVE (becomes `Dependency` blockers) |
| TaskTicket | `gate_info` → REMOVE (becomes `ThresholdTarget` criteria) |

**TaskTicket Simplification:**
```python
class TaskTicket(HierarchicalTicket):
    # Semantic fields only
    task_type: TaskType
    estimated_tokens: int
    actual_tokens: Optional[int]
    complexity: Complexity
    phase_label: Optional[str]

    # REMOVED: gate_info, audit_results
    # These become criteria:
    # - ThresholdTarget for pass/fail thresholds
    # - ManualTarget for audit assessments
```

---

## Part 3: Criterion Target Types

### Complete Target Type Hierarchy

```python
class CriterionTarget(BaseModel):
    """Base for all criterion targets."""

    @abstractmethod
    def is_satisfied(self) -> bool: ...

    @abstractmethod
    def get_status_description(self) -> str: ...


@dataclass
class CompletableTarget(CriterionTarget):
    """Criterion met when another Completable is complete."""

    completable_id: str
    required_status: TicketStatus = TicketStatus.COMPLETED

    # Cached state (updated by sync)
    current_status: Optional[TicketStatus] = None
    last_checked: Optional[datetime] = None

    def is_satisfied(self) -> bool:
        if self.current_status is None:
            return False
        return status_gte(self.current_status, self.required_status)


@dataclass
class FileExistsTarget(CriterionTarget):
    """Criterion met when file(s) exist."""

    paths: List[str]  # File paths or glob patterns
    all_required: bool = True  # True = all must exist, False = any

    # Cached state
    existing_paths: List[str] = field(default_factory=list)
    missing_paths: List[str] = field(default_factory=list)
    last_checked: Optional[datetime] = None

    def is_satisfied(self) -> bool:
        if self.all_required:
            return len(self.missing_paths) == 0
        return len(self.existing_paths) > 0


@dataclass
class TestPassesTarget(CriterionTarget):
    """Criterion met when test passes with optional coverage threshold."""

    test_command: str
    threshold: float = 100.0  # Pass rate threshold
    coverage_threshold: Optional[float] = None  # Optional coverage requirement

    # Cached state (latest result)
    last_result: Optional[TestResult] = None

    def is_satisfied(self) -> bool:
        if self.last_result is None:
            return False
        if self.last_result.pass_rate < self.threshold:
            return False
        if self.coverage_threshold and self.last_result.coverage_percent:
            if self.last_result.coverage_percent < self.coverage_threshold:
                return False
        return True


@dataclass
class TestResult:
    """Result of a test execution."""

    run_at: datetime
    passed: bool
    pass_rate: float  # 0-100
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    coverage_percent: Optional[float] = None
    duration_seconds: float = 0.0
    output: Optional[str] = None
    commit_sha: Optional[str] = None


@dataclass
class ThresholdTarget(CriterionTarget):
    """Criterion met when a metric meets a threshold."""

    metric_name: str  # e.g., "coverage", "lint_score", "performance"
    threshold: float
    comparison: ThresholdComparison = ThresholdComparison.GTE

    # Current value
    current_value: Optional[float] = None
    last_checked: Optional[datetime] = None

    def is_satisfied(self) -> bool:
        if self.current_value is None:
            return False
        return compare(self.current_value, self.threshold, self.comparison)


@dataclass
class ManualTarget(CriterionTarget):
    """Criterion met when manually assessed."""

    assessor: Optional[str] = None  # Who should assess
    instructions: Optional[str] = None  # How to assess

    # Assessment state
    assessed: bool = False
    met: Optional[bool] = None
    assessed_at: Optional[datetime] = None
    assessed_by: Optional[str] = None
    evidence: Optional[str] = None  # Notes, links, etc.

    def is_satisfied(self) -> bool:
        return self.assessed and self.met == True


@dataclass
class ExternalTarget(CriterionTarget):
    """Criterion met when external system reports success."""

    system_name: str  # e.g., "CI", "Security Scanner", "Dependency Check"
    endpoint: Optional[str] = None  # API endpoint to check
    expected_status: str = "success"

    # Cached state
    current_status: Optional[str] = None
    last_checked: Optional[datetime] = None
    response_data: Optional[Dict[str, Any]] = None

    def is_satisfied(self) -> bool:
        return self.current_status == self.expected_status
```

---

## Part 4: Serialization Impact

### YAML Format Changes

**Current Task YAML:**
```yaml
task:
  id: sqlite-backend-6a-task-001
  title: Implement Layer 1
  status: not_started
  blocked: false

  # Separate sections
  deliverables:
    - vibey/roadmap/models/ticket/base.py
    - tests/roadmap/models/ticket/test_base.py

  success_criteria:
    - description: All validators pass
      met: false

  blocked_by:
    - sqlite-backend-6a-task-009

  gate_info:
    threshold: 80
    score: null
```

**Proposed Task YAML:**
```yaml
task:
  id: sqlite-backend-6a-task-001
  name: Implement Layer 1
  status: not_started

  # Unified criteria section
  criteria:
    - id: code-deliverable
      description: Base ticket implementation
      target:
        type: file_exists
        paths:
          - vibey/roadmap/models/ticket/base.py
      state:
        existing: []
        missing: [vibey/roadmap/models/ticket/base.py]

    - id: test-deliverable
      description: Test file for base ticket
      target:
        type: file_exists
        paths:
          - tests/roadmap/models/ticket/test_base.py

    - id: tests-pass
      description: All tests pass
      target:
        type: test_passes
        test_command: pytest tests/roadmap/models/ticket/test_base.py
        threshold: 100.0

    - id: coverage
      description: Coverage meets threshold
      target:
        type: threshold
        metric_name: coverage
        threshold: 80.0
        comparison: gte
      state:
        current_value: null

    - id: depends-on-enums
      description: Enum definitions complete
      target:
        type: completable
        completable_id: sqlite-backend-6a-task-010
        required_status: completed
      state:
        current_status: not_started

  # Sibling dependencies (blockers, not children)
  dependencies:
    - target_id: sqlite-backend-6a-task-009
      required_status: completed
      blocks_transition_to: in_progress
      reason: Needs support classes
```

**Key YAML Changes:**
| Section | Change |
|---------|--------|
| `deliverables` | → `criteria` with `type: file_exists` |
| `success_criteria` | → `criteria` (merged) |
| `blocked_by` | → `criteria` with `type: completable` OR `dependencies` |
| `gate_info` | → `criteria` with `type: threshold` |
| `children` | REMOVED (computed from completable criteria) |
| `progress` | REMOVED (computed from criteria) |

### SQLite Schema Changes

**Current Tables:**
```sql
-- Separate tables for each concept
CREATE TABLE tasks (...);
CREATE TABLE deliverables (task_id, path, exists, ...);
CREATE TABLE success_criteria (task_id, description, met, ...);
CREATE TABLE task_blockers (task_id, blocker_id, ...);
CREATE TABLE quality_gates (entity_id, threshold, score, ...);
```

**Proposed Tables:**
```sql
-- Unified criteria table with polymorphic target
CREATE TABLE criteria (
    id TEXT PRIMARY KEY,
    completable_id TEXT NOT NULL,  -- Which ticket/completable owns this
    description TEXT NOT NULL,

    -- Target type discriminator
    target_type TEXT NOT NULL CHECK (target_type IN (
        'completable', 'file_exists', 'test_passes',
        'threshold', 'manual', 'external'
    )),

    -- Common target fields (nullable based on type)
    target_completable_id TEXT,     -- For completable type
    target_paths TEXT,              -- JSON array for file_exists
    target_test_command TEXT,       -- For test_passes
    target_threshold REAL,          -- For threshold/test
    target_metric_name TEXT,        -- For threshold
    target_comparison TEXT,         -- For threshold

    -- State fields
    state_satisfied INTEGER,        -- Boolean: criterion met?
    state_last_checked TEXT,        -- ISO timestamp
    state_data TEXT,                -- JSON for type-specific state

    FOREIGN KEY (completable_id) REFERENCES tickets(id)
);

-- Index for finding children (completable targets)
CREATE INDEX idx_criteria_completable_target
ON criteria(target_completable_id)
WHERE target_type = 'completable';

-- Index for finding parent from child
CREATE INDEX idx_criteria_parent_lookup
ON criteria(target_completable_id, completable_id)
WHERE target_type = 'completable';
```

**Migration SQL:**
```sql
-- Migrate deliverables to criteria
INSERT INTO criteria (id, completable_id, description, target_type, target_paths)
SELECT
    task_id || '-deliv-' || rowid,
    task_id,
    'Deliverable: ' || path,
    'file_exists',
    json_array(path)
FROM deliverables;

-- Migrate success_criteria to criteria
INSERT INTO criteria (id, completable_id, description, target_type, state_satisfied)
SELECT
    task_id || '-crit-' || rowid,
    task_id,
    description,
    'manual',
    met
FROM success_criteria;

-- Migrate blocked_by to criteria (as child references)
INSERT INTO criteria (id, completable_id, description, target_type, target_completable_id)
SELECT
    entity_id || '-child-' || blocker_id,
    entity_id,
    'Depends on: ' || blocker_id,
    'completable',
    blocker_id
FROM entity_blocked_by
WHERE blocker_type = 'task';
```

---

## Part 5: Operations Impact

### Query Operations

**Current (query.py):**
```python
def query_task_details(task_id: str) -> Dict:
    task = load_task(task_id)
    return {
        "id": task.id,
        "status": task.status,
        "progress": compute_progress(task),  # Different per type
        "deliverables": task.deliverables,
        "blocked_by": task.blocked_by,
        "children": get_children(task),  # Explicit lookup
    }
```

**Proposed:**
```python
def query_completable_details(completable_id: str) -> Dict:
    comp = load_completable(completable_id)
    return {
        "id": comp.id,
        "status": comp.status if hasattr(comp, 'status') else None,
        "progress": comp.progress,  # Universal formula
        "criteria": [
            {
                "id": c.id,
                "description": c.description,
                "type": c.target.type,
                "met": c.is_met(),
            }
            for c in comp.criteria
        ],
        "children": comp.children,  # Computed from criteria
        "blocking_reasons": comp.blocking_reasons,
    }
```

### Update Operations

**Current (update.py):**
```python
def complete_task(task_id: str) -> Result:
    task = load_task(task_id)

    # Multiple checks
    if task.blocked:
        return Error("Task is blocked")
    if not all_deliverables_exist(task):
        return Error("Deliverables missing")
    if not all_criteria_met(task):
        return Error("Criteria not met")
    if task.gate_info and not task.gate_info.has_passed():
        return Error("Gate not passed")

    task.status = TaskStatus.COMPLETED
    save_task(task)
```

**Proposed:**
```python
def complete_ticket(ticket_id: str) -> Result:
    ticket = load_ticket(ticket_id)

    # Single check - THE deterministic interface
    if not ticket.can_complete:
        return Error(
            "Cannot complete ticket",
            reasons=ticket.blocking_reasons
        )

    ticket.status = TicketStatus.COMPLETED
    ticket.completed_at = datetime.now(timezone.utc)
    save_ticket(ticket)
```

### Criterion Assessment Operations

**New operations needed:**
```python
def assess_criterion(
    completable_id: str,
    criterion_id: str,
    assessment: CriterionAssessment
) -> Result:
    """Assess a criterion (manual or automated)."""
    comp = load_completable(completable_id)
    criterion = comp.get_criterion(criterion_id)

    if isinstance(criterion.target, ManualTarget):
        criterion.target.assessed = True
        criterion.target.met = assessment.met
        criterion.target.assessed_by = assessment.assessor
        criterion.target.evidence = assessment.evidence

    elif isinstance(criterion.target, TestPassesTarget):
        criterion.target.last_result = run_tests(criterion.target.test_command)

    elif isinstance(criterion.target, FileExistsTarget):
        criterion.target.check_files()

    elif isinstance(criterion.target, ThresholdTarget):
        criterion.target.current_value = get_metric(criterion.target.metric_name)

    save_completable(comp)
    return Success(criterion.is_met())


def sync_completable_criteria(completable_id: str) -> Result:
    """Refresh all criterion states."""
    comp = load_completable(completable_id)

    for criterion in comp.criteria:
        if isinstance(criterion.target, CompletableTarget):
            child = load_completable(criterion.target.completable_id)
            criterion.target.current_status = child.status

        elif isinstance(criterion.target, FileExistsTarget):
            criterion.target.check_files()

        elif isinstance(criterion.target, TestPassesTarget):
            # Don't auto-run tests, just refresh cached result
            criterion.target.last_result = get_cached_test_result(
                criterion.target.test_command
            )

    save_completable(comp)
```

---

## Part 6: Interface Impact

### CLI Changes

**Current Commands:**
```bash
vibey roadmap show task-001
# Shows: status, deliverables, blockers, progress

vibey roadmap update task-001 --status completed
# Checks: blocked, deliverables exist, criteria met

vibey roadmap add-deliverable task-001 "src/api.py"
# Adds to deliverables list
```

**Proposed Commands:**
```bash
vibey roadmap show task-001
# Shows: status, criteria (grouped by type), progress, blocking reasons

vibey roadmap complete task-001
# Checks: all criteria met, shows blocking reasons if not

vibey roadmap add-criterion task-001 \
  --type file_exists \
  --description "API implementation" \
  --path "src/api.py"
# Adds criterion with FileExistsTarget

vibey roadmap add-criterion task-001 \
  --type completable \
  --description "Depends on schema task" \
  --target task-002
# Adds criterion with CompletableTarget (creates parent-child)

vibey roadmap assess task-001 criterion-id \
  --met true \
  --evidence "Reviewed in PR #123"
# Assesses manual criterion

vibey roadmap sync task-001
# Refreshes all criterion states
```

**New Display Format:**
```
Task: sqlite-backend-6a-task-001
Name: Implement Layer 1
Status: in_progress
Progress: 3/5 (60%)

Criteria:
  ✓ [file] Base ticket implementation
    Path: vibey/roadmap/models/ticket/base.py

  ✓ [file] Test file
    Path: tests/roadmap/models/ticket/test_base.py

  ✗ [test] Tests pass with coverage
    Command: pytest tests/roadmap/models/ticket/
    Last run: 2025-11-29 10:00 (FAILED: 2 failures)

  ✓ [completable] Enum definitions complete
    Target: sqlite-backend-6a-task-010 (completed)

  ✗ [manual] Code review completed
    Assessor: senior-engineer
    Status: Not assessed

Blocking Reasons:
  - Tests pass with coverage: 2 test failures
  - Code review completed: Not yet assessed
```

### MCP Changes

**Current Tools:**
```python
@tool
def get_task(task_id: str) -> TaskResponse:
    """Get task details including deliverables and blockers."""

@tool
def update_task_status(task_id: str, status: str) -> Result:
    """Update task status with validation."""

@tool
def add_deliverable(task_id: str, path: str) -> Result:
    """Add deliverable to task."""
```

**Proposed Tools:**
```python
@tool
def get_completable(completable_id: str) -> CompletableResponse:
    """
    Get completable details including criteria and progress.

    Returns:
        id, name, status, progress, criteria[], blocking_reasons[]
    """

@tool
def complete_ticket(ticket_id: str) -> CompleteResult:
    """
    Attempt to complete a ticket.

    Returns success if all criteria met, otherwise returns
    blocking_reasons explaining why completion is blocked.

    This is the DETERMINISTIC interface - AI cannot bypass criteria.
    """

@tool
def add_criterion(
    completable_id: str,
    criterion_type: str,  # file_exists, test_passes, completable, threshold, manual
    description: str,
    target_config: Dict[str, Any]
) -> Result:
    """Add a completion criterion."""

@tool
def assess_criterion(
    completable_id: str,
    criterion_id: str,
    met: bool,
    evidence: Optional[str] = None
) -> Result:
    """Assess a manual criterion."""

@tool
def sync_criteria(completable_id: str) -> SyncResult:
    """
    Refresh all criterion states.

    Checks file existence, child completion status, etc.
    Returns updated progress.
    """

@tool
def run_test_criterion(
    completable_id: str,
    criterion_id: str
) -> TestResult:
    """
    Run tests for a test_passes criterion.

    Returns test results and updates criterion state.
    """
```

---

## Part 7: Requirement System Integration

### Requirements as Criterion Templates

Requirements cascade down the hierarchy and **generate criteria** when applicable:

```python
@dataclass
class Requirement:
    """A criterion template that cascades down the hierarchy."""

    id: str
    name: str
    description: str

    # What type of criterion this generates
    criterion_template: CriterionTemplate

    # When does this apply?
    applicability: ApplicabilityRules

    # Inheritance behavior
    inherit_mode: InheritMode  # inherit, override, skip


@dataclass
class CriterionTemplate:
    """Template for generating criteria."""

    target_type: str  # test_passes, threshold, file_exists, etc.
    target_config: Dict[str, Any]  # Type-specific config

    def instantiate(self, ticket: Ticket) -> Criterion:
        """Generate a criterion for a specific ticket."""
        target = create_target(self.target_type, self.target_config, ticket)
        return Criterion(
            id=f"{self.id}-{ticket.id}",
            description=self.description,
            target=target
        )


@dataclass
class ApplicabilityRules:
    """Rules for when a requirement applies."""

    # Apply to these ticket types
    ticket_types: Optional[List[TicketType]] = None

    # Apply to these task types
    task_types: Optional[List[TaskType]] = None

    # Apply if ticket has these criterion types
    has_criterion_types: Optional[List[str]] = None

    # Custom expression
    expression: Optional[str] = None

    def matches(self, ticket: Ticket) -> bool:
        """Check if this requirement applies to a ticket."""
        if self.ticket_types and ticket.ticket_type not in self.ticket_types:
            return False

        if self.task_types and hasattr(ticket, 'task_type'):
            if ticket.task_type not in self.task_types:
                return False

        if self.has_criterion_types:
            ticket_criterion_types = {c.target.type for c in ticket.criteria}
            if not any(t in ticket_criterion_types for t in self.has_criterion_types):
                return False

        return True
```

### Example: Test Coverage Requirement

```yaml
# Sprint-level requirement
requirements:
  - id: test-coverage
    name: Test Coverage
    description: Code must have test coverage

    criterion_template:
      target_type: threshold
      target_config:
        metric_name: coverage
        threshold: 85.0
        comparison: gte

    applicability:
      has_criterion_types: [file_exists]  # Only if has code deliverables
      task_types: [development]            # Only for dev tasks

    inherit_mode: inherit  # Use stricter of local vs ancestor
```

When a task is created with a `file_exists` criterion for a `.py` file:
1. Requirement resolver checks applicability → matches
2. Template instantiates → adds `threshold` criterion for coverage
3. Task now has auto-generated coverage criterion

---

## Part 8: Migration Path

### Phase 1: New Models (Sprint 6a)

1. Implement `Completable`, `Criterion`, all `CriterionTarget` types
2. Implement `Ticket` extending `Completable`
3. Implement `Requirement` as criterion template
4. All new code, no migration yet

### Phase 2: Dual-Write Serialization (Sprint 6b)

1. YAML loader reads both old and new format
2. YAML dumper writes new format
3. SQL loader/dumper updated for new schema
4. Database migration script

### Phase 3: Operations Migration (Sprint 6c)

1. Update all operations to use criteria-based model
2. Remove old progress calculation code
3. Remove old deliverable/blocker checking code
4. Add criterion assessment operations

### Phase 4: Interface Migration (Sprint 6d)

1. Update CLI commands for criteria model
2. Update MCP tools for criteria model
3. Update displays to show criteria grouped by type
4. Add new assessment commands

### Phase 5: Cleanup (Sprint 7)

1. Remove old model code
2. Remove dual-format support
3. Remove deprecated fields
4. Final schema optimization

---

## Part 9: Breaking Changes Summary

### Model Layer

| Change | Impact | Migration |
|--------|--------|-----------|
| `deliverables` → `criteria[file_exists]` | HIGH | Automated conversion |
| `success_criteria` → `criteria[manual]` | HIGH | Automated conversion |
| `children_ids` → computed from criteria | MEDIUM | Logic change |
| `parent_id` → `parent_ref` (denormalized) | LOW | Rename |
| `blocked` → computed from dependencies | MEDIUM | Remove storage |
| `progress` → computed from criteria | HIGH | Formula change |
| `gate_info` → `criteria[threshold]` | MEDIUM | Automated conversion |

### Serialization Layer

| Change | Impact | Migration |
|--------|--------|-----------|
| YAML structure | HIGH | Dual-read, write-new |
| SQL schema | HIGH | Migration script |
| JSON API response | MEDIUM | Version bump |

### Operations Layer

| Change | Impact | Migration |
|--------|--------|-----------|
| Completion check logic | HIGH | Single function |
| Progress calculation | HIGH | Universal formula |
| New assessment operations | MEDIUM | New code |

### Interface Layer

| Change | Impact | Migration |
|--------|--------|-----------|
| CLI commands | HIGH | New command structure |
| MCP tools | HIGH | New tool structure |
| Display format | MEDIUM | New rendering |

---

## Part 10: Benefits Summary

### Simplification

| Metric | Before | After |
|--------|--------|-------|
| Concepts for completion | 3 (children, deliverables, criteria) | 1 (criteria) |
| Progress formulas | 3 (per type) | 1 (universal) |
| Parent-child models | Explicit fields | Computed from criteria |
| Completion checks | Multiple functions | One function |

### Flexibility

| Capability | Before | After |
|------------|--------|-------|
| Mix file + test + subtask requirements | Separate sections | Unified criteria list |
| Custom completion logic | Per-type code | Pluggable targets |
| Progress for any entity | Type-specific | Universal |
| Visibility of why blocked | Multiple sources | Single list |

### Guardrails

| Protection | Before | After |
|------------|--------|-------|
| AI completion bypass | Multiple checks | Single deterministic check |
| Visibility of blockers | Scattered | `blocking_reasons` list |
| Audit trail | Partial | Every criterion has state |

---

## Conclusion

The unification is a **significant but worthwhile change**:

1. **Conceptual simplification** - One model instead of three
2. **Universal progress** - Same formula everywhere
3. **Explicit relationships** - Children visible as criteria
4. **Strong guardrails** - Single completion check
5. **High migration cost** - All layers affected

**Recommendation**: Proceed with unification. The long-term simplicity justifies the migration effort.

**Revised Sprint 6a scope**:
- 11 tasks (down from 13)
- Core focus on `Completable` + `Criterion` + targets
- Requirements as criterion templates
- Migration adapters for existing data
