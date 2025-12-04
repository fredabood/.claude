# Completable Unification: Tickets, Deliverables, and Success Criteria

**Created:** 2025-11-29
**Purpose:** Assess unification of Ticket and Deliverable into a single base abstraction

---

## The Insight

> When a ticket has a success criterion that is the completion of a second ticket, the second ticket becomes a child of the first ticket.

This creates a recursive structure:
- A Ticket's completion depends on its success criteria
- A success criterion can be "another ticket is complete"
- Therefore: **child tickets ARE success criteria**

If we also observe:
- Deliverables have success criteria
- A Deliverable's completion = exists + criteria met
- Tests are Deliverables with execution tracking

Then: **Everything that can be "completed" shares the same shape.**

---

## Part 1: The Shared Shape

### What do Tickets, Deliverables, and Tests have in common?

| Property | Ticket | Deliverable | UnitTest |
|----------|--------|-------------|----------|
| Has identity (id, name) | ✓ | ✓ | ✓ |
| Can be complete or incomplete | ✓ | ✓ | ✓ |
| Has success criteria | ✓ | ✓ | ✓ (passing) |
| Completion is computed | ✓ | ✓ | ✓ |
| Can have children | ✓ | ? | ? |
| Has verification evidence | ✓ (commits) | ✓ (exists) | ✓ (results) |

### The Core Abstraction: Completable

```python
class Completable(Protocol):
    """Anything that can be marked complete."""

    id: str
    name: str

    @property
    def is_complete(self) -> bool: ...

    @property
    def completion_criteria(self) -> List[Completable]: ...

    @property
    def blocking_reasons(self) -> List[str]: ...
```

---

## Part 2: Unification Analysis

### Option A: Single Base Class (Maximum Unification)

```python
@dataclass
class Completable:
    """Base class for anything that can be completed."""

    # Identity
    id: str
    name: str
    description: Optional[str] = None

    # Completion criteria (the ONLY way to define what "complete" means)
    criteria: List[CompletionCriterion] = field(default_factory=list)

    # Computed
    @property
    def is_complete(self) -> bool:
        return all(c.is_met() for c in self.criteria)


@dataclass
class CompletionCriterion:
    """A single requirement for completion."""

    id: str
    description: str

    # What satisfies this criterion (polymorphic)
    target: CompletionTarget  # Could be: Completable, FileExists, TestPasses, etc.

    # State
    @property
    def is_met(self) -> bool:
        return self.target.is_satisfied()


# Different target types
class CompletionTarget(Protocol):
    def is_satisfied(self) -> bool: ...

@dataclass
class CompletableTarget(CompletionTarget):
    """Criterion is met when another Completable is complete."""
    completable_id: str

    def is_satisfied(self) -> bool:
        completable = lookup(self.completable_id)
        return completable.is_complete

@dataclass
class FileExistsTarget(CompletionTarget):
    """Criterion is met when file(s) exist."""
    paths: List[str]

    def is_satisfied(self) -> bool:
        return all(Path(p).exists() for p in self.paths)

@dataclass
class TestPassesTarget(CompletionTarget):
    """Criterion is met when test passes."""
    test_command: str
    threshold: float = 100.0

    def is_satisfied(self) -> bool:
        result = get_latest_test_result(self.test_command)
        return result and result.pass_rate >= self.threshold

@dataclass
class ThresholdTarget(CompletionTarget):
    """Criterion is met when a metric meets threshold."""
    metric: str  # e.g., "coverage", "lint_score"
    threshold: float
    comparison: str = "gte"  # gte, gt, eq, lt, lte
```

### What This Enables

```
Ticket (Sprint Planning Feature)
├── criteria[0]: FileExists("docs/sprint-planning.md")
├── criteria[1]: Completable("task-001")  ← Child ticket
├── criteria[2]: Completable("task-002")  ← Child ticket
├── criteria[3]: TestPasses("pytest tests/test_sprint.py")
└── criteria[4]: Threshold("coverage", 85.0)

Progress = 3/5 criteria met = 60%
```

**Key insight**: Children aren't a separate concept - they're just criteria that reference other Completables.

---

## Part 3: Implications of Unification

### 3.1 Parent-Child Relationship

**Before (explicit hierarchy):**
```python
class Ticket:
    parent_id: Optional[str]
    children_ids: List[str]
```

**After (implicit via criteria):**
```python
class Completable:
    criteria: List[CompletionCriterion]

    @property
    def children(self) -> List[Completable]:
        """Children are criteria that reference other Completables."""
        return [
            c.target.completable
            for c in self.criteria
            if isinstance(c.target, CompletableTarget)
        ]

    @property
    def parent(self) -> Optional[Completable]:
        """Find who has us as a criterion."""
        return find_completable_with_criterion(self.id)
```

### 3.2 Progress Calculation

**Universal formula:**
```python
@property
def progress(self) -> Progress:
    """Progress = met criteria / total criteria."""
    total = len(self.criteria)
    met = sum(1 for c in self.criteria if c.is_met())
    return Progress(
        total=total,
        completed=met,
        completion_percent=met / total * 100 if total > 0 else 100
    )
```

### 3.3 Deliverables Become Criteria

**Before:**
```python
class Ticket:
    deliverables: List[Deliverable]
    success_criteria: List[SuccessCriterion]
    children: List[Ticket]
```

**After:**
```python
class Completable:
    criteria: List[CompletionCriterion]
    # That's it. Everything is a criterion.
```

A "deliverable" is just a criterion with a FileExists target:
```python
CompletionCriterion(
    id="deliver-api-docs",
    description="API documentation exists",
    target=FileExistsTarget(paths=["docs/api.md"])
)
```

### 3.4 Tests Become Criteria

A "test requirement" is just a criterion with a TestPasses target:
```python
CompletionCriterion(
    id="unit-tests-pass",
    description="Unit tests pass with 85% coverage",
    target=TestPassesTarget(
        test_command="pytest tests/",
        threshold=85.0
    )
)
```

---

## Part 4: What Remains Ticket-Specific?

Even with unification, Tickets have semantic properties that other Completables don't:

### 4.1 Lifecycle State (not just complete/incomplete)

```python
class Ticket(Completable):
    """A work item with lifecycle beyond just completion."""

    status: TicketStatus  # not_started, in_progress, paused, completed
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
```

A Deliverable doesn't have "in_progress" - it either exists or it doesn't.

### 4.2 Assignment

```python
class Ticket(Completable):
    assigned_agents: List[str]
    priority: Priority
```

You don't assign someone to a file - you assign them to the work that produces the file.

### 4.3 Git Integration

```python
class Ticket(Completable):
    commits: List[GitCommit]  # Work evidence
```

### 4.4 Requirements (Inherited Policies)

```python
class Ticket(Completable):
    requirements_local: List[Requirement]

    @property
    def requirements_effective(self) -> List[Requirement]:
        """Merge with ancestor requirements."""
```

---

## Part 5: Proposed Class Hierarchy

```
Completable (abstract base)
│
├── CompletionCriterion
│   └── target: CompletionTarget (polymorphic)
│
├── CompletionTarget (protocol)
│   ├── CompletableTarget (references another Completable)
│   ├── FileExistsTarget (file must exist)
│   ├── TestPassesTarget (test must pass)
│   ├── ThresholdTarget (metric meets threshold)
│   ├── ManualAssessmentTarget (human verified)
│   └── ExternalTarget (external system check)
│
└── Ticket (extends Completable with work semantics)
    ├── RoadmapTicket (ultimate parent)
    ├── TrackTicket (intermediate)
    ├── SprintTicket (intermediate)
    └── TaskTicket (ultimate child)
```

### What Disappears

| Concept | Fate |
|---------|------|
| `Deliverable` class | → `FileExistsTarget` criterion |
| `UnitTest` class | → `TestPassesTarget` criterion |
| `SuccessCriterion` class | → `CompletionCriterion` (renamed) |
| `children_ids` field | → Computed from `CompletableTarget` criteria |
| `parent_id` field | → Computed via reverse lookup |
| `deliverables_local` field | → `criteria` with `FileExistsTarget` |
| `success_criteria_local` field | → `criteria` (merged) |
| `progress` field | → Computed from `criteria` |

### What Remains

| Concept | Location |
|---------|----------|
| Status lifecycle | `Ticket` only |
| Assignment | `Ticket` only |
| Commits | `Ticket` only |
| Requirements (inherited) | `Ticket` only |
| Priority | `Ticket` only |
| Estimates | `Ticket` only |

---

## Part 6: Examples

### Example 1: Task with Code Deliverable and Tests

```python
TaskTicket(
    id="task-001",
    name="Implement login API",
    status=TicketStatus.IN_PROGRESS,
    criteria=[
        CompletionCriterion(
            id="code-exists",
            description="Login endpoint implementation",
            target=FileExistsTarget(paths=["src/api/login.py"])
        ),
        CompletionCriterion(
            id="tests-exist",
            description="Login endpoint tests",
            target=FileExistsTarget(paths=["tests/test_login.py"])
        ),
        CompletionCriterion(
            id="tests-pass",
            description="Tests pass with 90% coverage",
            target=TestPassesTarget(
                test_command="pytest tests/test_login.py --cov=src/api/login",
                threshold=90.0
            )
        ),
        CompletionCriterion(
            id="docs-updated",
            description="API docs updated",
            target=FileExistsTarget(paths=["docs/api/login.md"])
        ),
    ]
)
# Progress: 2/4 = 50% (assuming code and tests exist but tests not passing yet)
```

### Example 2: Sprint with Child Tasks

```python
SprintTicket(
    id="sprint-1",
    name="Authentication Sprint",
    criteria=[
        # Child tasks (these ARE the success criteria)
        CompletionCriterion(
            id="task-001",
            description="Login API complete",
            target=CompletableTarget(completable_id="task-001")
        ),
        CompletionCriterion(
            id="task-002",
            description="Logout API complete",
            target=CompletableTarget(completable_id="task-002")
        ),
        CompletionCriterion(
            id="task-003",
            description="Session management complete",
            target=CompletableTarget(completable_id="task-003")
        ),
        # Sprint-level requirements (not task-specific)
        CompletionCriterion(
            id="integration-tests",
            description="Integration tests pass",
            target=TestPassesTarget(
                test_command="pytest tests/integration/auth/",
                threshold=100.0
            )
        ),
        CompletionCriterion(
            id="security-review",
            description="Security review completed",
            target=ManualAssessmentTarget(
                assessor="security-team",
                description="Auth implementation reviewed for vulnerabilities"
            )
        ),
    ]
)
# Progress: tasks 0/3 + requirements 0/2 = 0/5 = 0%
```

### Example 3: Documentation-Only Task (No Tests)

```python
TaskTicket(
    id="task-docs",
    name="Write user guide",
    criteria=[
        CompletionCriterion(
            id="guide-exists",
            description="User guide document",
            target=FileExistsTarget(paths=["docs/user-guide.md"])
        ),
        CompletionCriterion(
            id="reviewed",
            description="Reviewed by tech writer",
            target=ManualAssessmentTarget(
                assessor="tech-writer",
                description="Content accuracy and clarity verified"
            )
        ),
    ]
    # Note: No test criteria - doesn't apply to docs
)
```

---

## Part 7: Requirement Inheritance in Unified Model

Requirements still cascade down, but now they're **criterion templates**:

```python
@dataclass
class Requirement:
    """A criterion template that cascades down the hierarchy."""

    id: str
    name: str

    # Template for generating criteria
    criterion_template: CriterionTemplate

    # Applicability
    applies_to: ApplicabilityRules

    # Inheritance behavior
    inherit_mode: InheritMode
```

When a Ticket is created, requirements are **instantiated as criteria**:

```python
def instantiate_requirements(ticket: Ticket) -> List[CompletionCriterion]:
    """Convert applicable requirements to criteria."""
    criteria = []
    for req in ticket.requirements_effective:
        if req.applies_to.matches(ticket):
            criterion = req.criterion_template.instantiate(ticket)
            criteria.append(criterion)
    return criteria
```

---

## Part 8: Implementation Plan

### Phase 1: Core Abstractions (Task 009 revision)

1. Define `Completable` protocol/base class
2. Define `CompletionCriterion` with target types
3. Implement all `CompletionTarget` variants:
   - `CompletableTarget`
   - `FileExistsTarget`
   - `TestPassesTarget`
   - `ThresholdTarget`
   - `ManualAssessmentTarget`
   - `ExternalTarget`

### Phase 2: Ticket Refactor (Task 001 revision)

1. Remove `deliverables_local`, `success_criteria_local`, `children_ids`
2. Add `criteria: List[CompletionCriterion]`
3. Add computed properties:
   - `children` (derived from `CompletableTarget` criteria)
   - `parent` (reverse lookup)
   - `progress` (met/total criteria)
   - `is_complete` (all criteria met)
   - `blocking_reasons` (unmet criteria descriptions)

### Phase 3: Requirement System (Task 013)

1. Requirements become criterion templates
2. Instantiation logic applies templates to tickets
3. Applicability rules filter by ticket type/content

### Phase 4: Migration (Task 008 revision)

1. Convert existing `deliverables` → `FileExistsTarget` criteria
2. Convert existing `children_ids` → `CompletableTarget` criteria
3. Convert existing `success_criteria` → appropriate target types

---

## Part 9: Trade-offs

### Advantages

1. **Single completion model** - Everything uses the same logic
2. **Progress is universal** - Same formula for all Completables
3. **Children are explicit** - You see WHY they're children (they're criteria)
4. **Flexible composition** - Mix file checks, tests, sub-tickets, manual reviews
5. **Simpler mental model** - "What must be true for this to be complete?"

### Disadvantages

1. **More abstract** - "Criterion with CompletableTarget" vs "child ticket"
2. **Lookup overhead** - Parent computed via reverse lookup
3. **Migration complexity** - Existing data needs transformation
4. **Criterion explosion** - Many small criteria vs few structured fields

### Mitigations

1. **Convenience accessors**: `ticket.children`, `ticket.deliverables`, `ticket.tests`
2. **Index for parent lookup**: Maintain reverse index for O(1) parent access
3. **Migration tooling**: Automated conversion in Task 008
4. **Grouping**: Criteria can have categories for display

---

## Part 10: Revised Sprint 6a Structure

```
FOUNDATION (no dependencies)
├── Task 010: Enum Definitions
│   Add: TargetType (completable, file, test, threshold, manual, external)

CORE ABSTRACTIONS (depends on 010)
├── Task 009: Completable & Criterion System (MAJOR REVISION)
│   - Completable base class
│   - CompletionCriterion
│   - All CompletionTarget types
│   - Progress computation

├── Task 011: Requirement Templates (NEW - replaces old 011-013)
│   - Requirement as criterion template
│   - CriterionTemplate
│   - ApplicabilityRules
│   - Instantiation logic

TICKET LAYERS (depends on 009, 011)
├── Task 001: Layer 1 Base Ticket (REVISED)
│   - Uses criteria: List[CompletionCriterion]
│   - Computed: children, parent, progress, is_complete

├── Task 002: Layer 2 Smart Accessors
│   - requirements_effective (criterion template inheritance)

├── Tasks 003-006: Layer 3 Domain Models
│   - Minimal changes (mostly semantic fields)

ORM & MIGRATION (depends on 001-006)
├── Task 007: SQLAlchemy ORM
│   - Schema for criteria and targets

├── Task 008: Migration
│   - Convert deliverables → FileExistsTarget
│   - Convert children → CompletableTarget
│   - Convert success_criteria → appropriate targets
```

**New task count**: 11 tasks (reduced from 13 by unifying)

---

## Conclusion

The unification is **conceptually cleaner** and **more powerful**:

1. **One abstraction**: Everything completable uses criteria
2. **One formula**: Progress = met / total
3. **Explicit relationships**: Children are visible as criteria
4. **Flexible composition**: Any mix of file, test, sub-ticket, manual criteria

The main cost is **abstraction overhead** - but good accessors (`ticket.children`, `ticket.tests`) preserve familiar APIs.

**Recommendation**: Proceed with unification. It simplifies the model significantly and makes progress tracking universal.
