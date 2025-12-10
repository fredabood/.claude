# Revised Sprint 6a Architecture: Completion Verification System

**Created:** 2025-11-29
**Purpose:** Comprehensive redesign incorporating dependency consolidation, requirement inheritance, deliverable validation, and test result tracking.

---

## Design Intent

> The purpose of the system is to put guardrails around the AI's ability to manipulate the roadmap state by implementing a **deterministic interface for calculating whether or not a ticket has been completed**; and give the user an interface to track their work; but, the system should allow the user flexibility to plan the sprint for the execution they desire.

This means:
1. **Completion is computed, not declared** - AI cannot mark a ticket complete unless all criteria are satisfied
2. **User controls the criteria** - User defines what "complete" means for each ticket
3. **Flexibility in planning** - Not all tickets need the same criteria

---

## Part 1: Deliverable vs Success Criteria Relationship

### The Problem

Currently these are separate concepts with no clear relationship:
- `deliverables` - what artifacts should exist
- `success_criteria` - what conditions should be true

### The Solution: Success Criteria Are Assessments of Deliverables

```
Deliverable          What must be produced (artifact)
    │
    ▼
SuccessCriterion     How we know it's correct (assessment of deliverable)
    │
    ▼
Assessment           The actual evaluation (automated or manual)
```

**Core Insight**: Every success criterion should be traceable to either:
1. A specific deliverable (e.g., "code coverage > 80% for this file")
2. The ticket itself (e.g., "all acceptance tests pass")

### Revised Model

```python
@dataclass
class Deliverable:
    """An artifact that must be produced."""

    # Identity
    id: str                              # Unique within ticket
    name: str                            # Human-readable name
    type: DeliverableType                # code, test, documentation, config, artifact

    # Location (for verifiable deliverables)
    paths: List[str]                     # File paths or glob patterns

    # Metadata
    description: Optional[str] = None
    required: bool = True                # Required for completion?

    # Verification state (computed at runtime)
    exists: Optional[bool] = None        # Do the files exist?
    verified_at: Optional[datetime] = None

    # Success criteria for THIS deliverable
    success_criteria: List[SuccessCriterion] = field(default_factory=list)

    def is_complete(self) -> bool:
        """Deliverable is complete when it exists AND all criteria are met."""
        if not self.required:
            return True
        if self.exists != True:
            return False
        return all(c.is_met() for c in self.success_criteria)


@dataclass
class SuccessCriterion:
    """An assessment that must pass for a deliverable or ticket to be complete."""

    # Identity
    id: str
    description: str                     # What must be true

    # Assessment configuration
    assessment_type: AssessmentType      # automated, manual, hybrid

    # For automated assessment
    validator: Optional[Validator] = None  # How to check automatically

    # State
    assessed: bool = False
    met: Optional[bool] = None           # True if criterion is satisfied
    assessed_at: Optional[datetime] = None
    assessed_by: Optional[str] = None    # Who/what performed assessment
    evidence: Optional[str] = None       # Proof of assessment

    # Override (user can bypass with justification)
    overridden: bool = False
    override_reason: Optional[str] = None
    overridden_by: Optional[str] = None

    def is_met(self) -> bool:
        """Criterion is met if assessed=True and met=True, OR overridden."""
        if self.overridden:
            return True
        return self.assessed and self.met == True
```

### Relationship Diagram

```
Ticket
├── deliverables_local: List[Deliverable]
│   ├── Deliverable (code: "vibey/models/ticket.py")
│   │   └── success_criteria:
│   │       ├── SuccessCriterion (type coverage > 80%)
│   │       └── SuccessCriterion (no linting errors)
│   │
│   ├── Deliverable (test: "tests/test_ticket.py")
│   │   └── success_criteria:
│   │       └── SuccessCriterion (tests pass)
│   │
│   └── Deliverable (docs: "docs/ticket.md")
│       └── success_criteria: []  # No criteria = existence is enough
│
└── success_criteria_local: List[SuccessCriterion]  # Ticket-level (not tied to deliverable)
    ├── SuccessCriterion (integration tests pass)
    └── SuccessCriterion (peer review completed)
```

---

## Part 2: UnitTest and TestResult Classes

### Design

Tests are a **special type of deliverable** with their own success criteria (passing).

```python
@dataclass
class UnitTest(Deliverable):
    """A test file deliverable with execution tracking."""

    # Inherited: id, name, paths, exists, success_criteria
    type: DeliverableType = DeliverableType.TEST  # Always TEST

    # Test-specific
    test_framework: str = "pytest"       # pytest, unittest, etc.
    test_command: Optional[str] = None   # Override default command

    # What this test validates
    tests_deliverable_id: Optional[str] = None  # ID of code deliverable this tests

    # Execution results
    results: List[TestResult] = field(default_factory=list)

    @property
    def latest_result(self) -> Optional[TestResult]:
        """Get most recent test result."""
        return self.results[-1] if self.results else None

    @property
    def is_passing(self) -> bool:
        """Test is passing if latest result passed."""
        return self.latest_result is not None and self.latest_result.passed


@dataclass
class TestResult:
    """Result of running a test."""

    # Identity
    test_id: str                         # Which test was run
    run_at: datetime                     # When test was run

    # Results
    passed: bool                         # Did test pass?
    total_tests: int                     # Number of test cases
    passed_tests: int
    failed_tests: int
    skipped_tests: int

    # Coverage (optional)
    coverage_percent: Optional[float] = None
    covered_lines: Optional[int] = None
    total_lines: Optional[int] = None

    # Execution metadata
    duration_seconds: float = 0.0
    command: Optional[str] = None        # Actual command run
    output: Optional[str] = None         # Test output (truncated)

    # Traceability
    commit_sha: Optional[str] = None     # What code version was tested
    triggered_by: Optional[str] = None   # What triggered the run (commit, manual, CI)
```

### How Tests Relate to Deliverables

```
Deliverable (code: "vibey/models/ticket.py")
    │
    │  tests_deliverable_id
    ▼
UnitTest (test: "tests/test_ticket.py")
    │
    │  results
    ▼
TestResult (run_at: 2025-11-29T10:00:00)
    ├── passed: True
    ├── coverage_percent: 92.5
    └── commit_sha: "abc123"
```

### Completion Check Flow

```python
def is_ticket_complete(ticket: Ticket) -> tuple[bool, list[str]]:
    """
    Deterministic completion check.

    Returns (is_complete, list of reasons if not complete)
    """
    reasons = []

    # 1. Check all deliverables exist and meet criteria
    for d in ticket.deliverables_local:
        if not d.is_complete():
            if not d.exists:
                reasons.append(f"Deliverable '{d.name}' does not exist")
            for c in d.success_criteria:
                if not c.is_met():
                    reasons.append(f"Criterion '{c.description}' not met for '{d.name}'")

    # 2. Check ticket-level success criteria
    for c in ticket.success_criteria_local:
        if not c.is_met():
            reasons.append(f"Ticket criterion '{c.description}' not met")

    # 3. Check all required tests pass
    for d in ticket.deliverables_local:
        if isinstance(d, UnitTest) and d.required:
            if not d.is_passing:
                reasons.append(f"Test '{d.name}' is not passing")

    # 4. Check requirements (inherited + local) are satisfied
    for req in ticket.requirements_effective:
        if req.is_applicable(ticket) and req.blocks_completion():
            reasons.append(f"Requirement '{req.name}' not satisfied")

    return (len(reasons) == 0, reasons)
```

---

## Part 3: Requirement Inheritance (Hybrid Approach)

### The Problem

When a sprint has a unit test pass rate requirement of 85%, and:
- A task has a requirement of 95% → stricter wins
- A task only involves documentation → requirement N/A
- A task has no explicit requirement → inherit from sprint

### The Solution: Applicability + Strictness Resolution

```python
@dataclass
class Requirement:
    """
    A quality requirement that may be inherited down the hierarchy.
    Replaces QualityGate + Standard with unified model.
    """

    # Identity
    id: str
    name: str
    description: str

    # Classification
    type: RequirementType               # test_coverage, code_style, documentation, etc.
    enforcement: EnforcementMode        # blocking, warning, audit

    # Threshold (for measurable requirements)
    threshold: Optional[float] = None   # e.g., 80.0 for 80% coverage
    comparison: ThresholdComparison = ThresholdComparison.GTE  # >=, >, ==, <, <=

    # Current state
    current_value: Optional[float] = None
    status: RequirementStatus = RequirementStatus.NOT_RUN

    # Applicability rules
    applies_to_types: List[DeliverableType] = field(default_factory=list)
    applies_to_task_types: List[TaskType] = field(default_factory=list)
    applicability_expression: Optional[str] = None  # e.g., "has_code_deliverable"

    # Inheritance behavior
    inherit_mode: InheritMode = InheritMode.INHERIT  # inherit, override, skip

    def is_applicable(self, ticket: Ticket) -> bool:
        """
        Determine if this requirement applies to a ticket.

        Examples:
        - test_coverage only applies if ticket has code deliverables
        - documentation requirement only if ticket is type=documentation
        """
        # Check task type applicability
        if self.applies_to_task_types:
            if hasattr(ticket, 'task_type'):
                if ticket.task_type not in self.applies_to_task_types:
                    return False

        # Check deliverable type applicability
        if self.applies_to_types:
            has_applicable_deliverable = any(
                d.type in self.applies_to_types
                for d in ticket.deliverables_local
            )
            if not has_applicable_deliverable:
                return False

        # Custom expression (for complex rules)
        if self.applicability_expression:
            return self._evaluate_expression(ticket)

        return True  # Default: applicable

    def is_satisfied(self) -> bool:
        """Check if requirement is currently satisfied."""
        if self.status == RequirementStatus.PASSED:
            return True
        if self.threshold is not None and self.current_value is not None:
            return self._compare(self.current_value, self.threshold)
        return False

    def blocks_completion(self) -> bool:
        """Check if this requirement blocks ticket completion."""
        return (
            self.enforcement == EnforcementMode.BLOCKING
            and not self.is_satisfied()
        )


class InheritMode(str, Enum):
    """How a requirement interacts with inherited requirements."""
    INHERIT = "inherit"      # Use parent if no local override
    OVERRIDE = "override"    # Replace parent requirement entirely
    SKIP = "skip"            # Explicitly not applicable (with justification)


class ThresholdComparison(str, Enum):
    """How to compare current value to threshold."""
    GTE = "gte"  # >= (most common: at least X%)
    GT = "gt"    # > (more than X)
    EQ = "eq"    # == (exactly X)
    LTE = "lte"  # <= (at most X)
    LT = "lt"    # < (less than X)
```

### Resolution Algorithm

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
    # Start with inherited requirements
    inherited = collect_ancestor_requirements(ticket)
    local = ticket.requirements_local

    effective = []
    processed_types = set()

    # Process local requirements first
    for local_req in local:
        if local_req.inherit_mode == InheritMode.SKIP:
            # Explicitly skip - don't include this type
            processed_types.add(local_req.type)
            continue

        if local_req.inherit_mode == InheritMode.OVERRIDE:
            # Override - use local entirely
            effective.append(local_req)
            processed_types.add(local_req.type)
            continue

        # INHERIT mode - find matching inherited and use stricter
        inherited_match = find_by_type(inherited, local_req.type)
        if inherited_match:
            stricter = resolve_stricter(local_req, inherited_match)
            effective.append(stricter)
        else:
            effective.append(local_req)
        processed_types.add(local_req.type)

    # Add inherited requirements not overridden locally
    for inh_req in inherited:
        if inh_req.type not in processed_types:
            effective.append(inh_req)

    # Filter to applicable requirements
    return [r for r in effective if r.is_applicable(ticket)]


def resolve_stricter(local: Requirement, inherited: Requirement) -> Requirement:
    """Return the stricter of two requirements."""
    if local.threshold is None or inherited.threshold is None:
        return local  # Can't compare, prefer local

    # For "at least X%" comparisons, stricter means higher threshold
    if local.comparison in [ThresholdComparison.GTE, ThresholdComparison.GT]:
        return local if local.threshold > inherited.threshold else inherited

    # For "at most X" comparisons, stricter means lower threshold
    if local.comparison in [ThresholdComparison.LTE, ThresholdComparison.LT]:
        return local if local.threshold < inherited.threshold else inherited

    return local  # Default: prefer local
```

### Example: Test Coverage Inheritance

```yaml
# Sprint level
requirements:
  - id: test-coverage
    name: Test Coverage
    type: test_coverage
    threshold: 85.0
    enforcement: blocking
    applies_to_types: [code]  # Only applies if has code deliverables

# Task A: Development task with code
requirements: []  # Inherits 85% from sprint

# Task B: Stricter requirement
requirements:
  - id: test-coverage
    threshold: 95.0
    inherit_mode: inherit  # Uses stricter: 95%

# Task C: Documentation only
deliverables:
  - type: documentation
    paths: ["docs/api.md"]
requirements: []  # test-coverage N/A (no code deliverables)

# Task D: Explicitly skip (with justification in metadata)
requirements:
  - id: test-coverage
    inherit_mode: skip
metadata:
  requirement_overrides:
    test-coverage: "Legacy code refactor - tests added in separate task"
```

---

## Part 4: Revised Layer 1 Fields

Given the above design, here are the updated L1 fields:

```python
@dataclass
class Ticket(BaseModel):
    """Layer 1: Base ticket with completion verification."""

    # === IDENTITY ===
    id: str
    name: str
    description: Optional[str] = None

    # === STATUS & LIFECYCLE ===
    status: TicketStatus = TicketStatus.NOT_STARTED

    # === TIMESTAMPS ===
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # === HIERARCHY (for L1 attribute computation) ===
    parent_id: Optional[str] = None
    children_ids: List[str] = Field(default_factory=list)

    # === HIERARCHY ATTRIBUTES (computed) ===
    @computed_field
    def is_parent(self) -> bool:
        return len(self.children_ids) > 0

    @computed_field
    def is_child(self) -> bool:
        return self.parent_id is not None

    @computed_field
    def is_ultimate_parent(self) -> bool:
        return self.is_parent and not self.is_child

    @computed_field
    def is_ultimate_child(self) -> bool:
        return self.is_child and not self.is_parent

    @computed_field
    def is_intermediate(self) -> bool:
        return self.is_parent and self.is_child

    # === DEPENDENCIES (consolidated) ===
    dependencies_local: List[Dependency] = Field(default_factory=list)

    # === DELIVERABLES (with success criteria) ===
    deliverables_local: List[Deliverable] = Field(default_factory=list)

    # === SUCCESS CRITERIA (ticket-level) ===
    success_criteria_local: List[SuccessCriterion] = Field(default_factory=list)

    # === REQUIREMENTS (quality policies) ===
    requirements_local: List[Requirement] = Field(default_factory=list)

    # === COMMITS ===
    commits_local: List[GitCommit] = Field(default_factory=list)

    # === METADATA ===
    metadata: Dict[str, Any] = Field(default_factory=dict)
    assigned_agents_local: List[str] = Field(default_factory=list)
    estimated_duration: Optional[str] = None

    # === COMPLETION VERIFICATION ===
    @computed_field
    def is_blocked(self) -> bool:
        """Blocked if any dependency is unsatisfied."""
        return any(not d.is_satisfied() for d in self.dependencies_local)

    @computed_field
    def blocking_reasons(self) -> List[str]:
        """List of reasons this ticket cannot be completed."""
        reasons = []

        # Unsatisfied dependencies
        for d in self.dependencies_local:
            if not d.is_satisfied():
                reasons.append(f"Dependency '{d.target_id}' not satisfied")

        # Incomplete deliverables
        for d in self.deliverables_local:
            if d.required and not d.is_complete():
                if not d.exists:
                    reasons.append(f"Deliverable '{d.name}' does not exist")
                for c in d.success_criteria:
                    if not c.is_met():
                        reasons.append(f"Criterion '{c.description}' not met")

        # Unmet ticket-level criteria
        for c in self.success_criteria_local:
            if not c.is_met():
                reasons.append(f"Criterion '{c.description}' not met")

        return reasons

    @computed_field
    def can_complete(self) -> bool:
        """Ticket can complete if no blocking reasons."""
        return len(self.blocking_reasons) == 0

    def try_complete(self) -> Tuple[bool, List[str]]:
        """
        Attempt to mark ticket as complete.

        Returns (success, reasons_if_failed)

        This is the DETERMINISTIC interface - AI cannot bypass this.
        """
        if self.can_complete:
            return (True, [])
        return (False, self.blocking_reasons)
```

---

## Part 5: Revised Sprint 6a Task Structure

### Current vs Proposed

| Current Task | Status | Proposed Change |
|--------------|--------|-----------------|
| 010: Enums | Keep | Add new enums: AssessmentType, InheritMode, ThresholdComparison, RequirementType |
| 009: Support Classes | **MAJOR REVISION** | Split into multiple focused tasks |
| 001: Layer 1 Base | Keep | Update field list per new design |
| 002: Layer 2 Smart Accessors | Keep | Add `requirements_effective` accessor |
| 003-006: Layer 3 Domain | Keep | Minimal changes |
| 007: ORM Mapping | Keep | Update for new models |
| 008: Migration | Keep | Update for new field names |
| NEW: 011 | Add | Deliverable + SuccessCriterion + Assessment |
| NEW: 012 | Add | UnitTest + TestResult |
| NEW: 013 | Add | Requirement inheritance + applicability |

### Proposed Task Breakdown

```
FOUNDATION LAYER (no dependencies)
├── Task 010: Enum Definitions (expand to include new enums)

SUPPORT CLASSES (depends on 010)
├── Task 009: Core Support Classes
│   └── GitCommit, Progress, TicketSummary, ActivityLogEntry, VersionStrategy
│
├── Task 011: Deliverable & Assessment System (NEW)
│   └── Deliverable, SuccessCriterion, Assessment, Validator
│
├── Task 012: Test Tracking System (NEW)
│   └── UnitTest, TestResult, TestExecution
│
├── Task 013: Requirement System (NEW)
│   └── Requirement, RequirementResolver, InheritanceEngine

TICKET LAYERS (depends on 009-013)
├── Task 001: Layer 1 Base Ticket
├── Task 002: Layer 2 Smart Accessors
├── Tasks 003-006: Layer 3 Domain Models

ORM & MIGRATION (depends on 001-006)
├── Task 007: SQLAlchemy ORM
├── Task 008: Migration from existing models
```

### New Task Count

- Original: 10 tasks
- Proposed: 13 tasks (+3 new tasks for completion verification system)

---

## Part 6: Impact on Sprints 6b-6d

### Sprint 6b (Serialization)

Additional work needed:
- YAML v2 format for `Deliverable.success_criteria`
- YAML v2 format for `UnitTest` and `TestResult`
- YAML v2 format for `Requirement` with inheritance fields
- Database schema for new tables

### Sprint 6c (Operations)

Additional work needed:
- `assess_criterion()` operation
- `run_tests()` operation
- `check_requirement()` operation
- `resolve_requirements()` implementation
- Completion verification in update operations

### Sprint 6d (Interfaces)

Additional work needed:
- CLI commands for assessing criteria
- CLI commands for running tests
- CLI display of requirement inheritance
- MCP tools for completion verification

---

## Summary

### Key Design Decisions

1. **Deliverables have success criteria** - Each deliverable can have zero or more criteria that must be met
2. **UnitTest extends Deliverable** - Tests are special deliverables with execution tracking
3. **TestResult ties test to code** - Traceability from test run to specific commit
4. **Requirements use hybrid inheritance**:
   - INHERIT: use stricter of local vs ancestor
   - OVERRIDE: replace ancestor entirely
   - SKIP: explicitly not applicable
5. **Applicability determines relevance** - Test coverage N/A for docs-only tasks
6. **Completion is computed** - `can_complete` is a deterministic function, not a flag

### Benefits

1. **Guardrails** - AI cannot mark complete unless criteria are met
2. **Flexibility** - Users define what complete means per ticket
3. **Traceability** - Every completion has evidence trail
4. **Inheritance** - Common policies cascade down
5. **Exceptions** - Users can skip/override with justification

---

## Next Steps

1. **Review this document** - Confirm design direction
2. **Update Sprint 6a tasks** - Implement revised task definitions
3. **Update track.yaml** - New task count and timeline
4. **Update Sprints 6b-6d** - Cascade changes to downstream sprints
