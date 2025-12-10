# Dependency System Analysis & Consolidation Plan

**Created:** 2025-11-29
**Purpose:** Holistic assessment of vibey's dependency, blocking, and gating systems with consolidation proposal aligned to unified ticket architecture (Sprints 6a-6d)

---

## Executive Summary

The vibey roadmap system has **6 overlapping systems** for tracking work prerequisites and quality requirements. This analysis identifies each system, clarifies their intended purposes, documents inconsistencies, and proposes a consolidation path that integrates with the planned unified ticket architecture.

---

## Part 1: Current System Inventory

### 1.1 Your Assessment (Corrected)

| System | Your Interpretation | Actual Purpose | Status |
|--------|---------------------|----------------|--------|
| `dependencies` | External to roadmap | **Partially correct** - Static config of prerequisites (can be internal or external) | Active |
| `blocks`/`blocked_by` | Cross-sprint blockers | **Partially correct** - Forward/reverse index of dependencies | **DEPRECATED** |
| `quality_gates` | Intra-sprint blockers | **Incorrect** - Track/sprint-level validation criteria (not inter-task) | Active |
| `development_gates` | Same as blockers? | **Different** - Sprint's external dependencies (poorly named) | Active |
| `standards` | Parent→child requirements | **Correct** - Cascading quality policies with enforcement modes | Active |

### 1.2 Missing Concepts You Identified

| Concept | Current State | Impact |
|---------|---------------|--------|
| **Success Criteria** | Sprint-only (`success_criteria: List[str]`), no enforcement | No formal assessment |
| **Deliverables Validation** | Task uses typed `Deliverable`, Sprint/Track use `List[str]` | No completion checks |
| **Unit Test Tracking** | Via `test_run` standard type only | No formal test class |
| **Artifact Requirements** | Via deliverables (unvalidated) | No completion enforcement |

---

## Part 2: Detailed System Analysis

### 2.1 Static Dependencies (`dependencies` / `development_gates`)

**Location:**
- Task: `dependencies: List[TaskDependency]` (task.py:221)
- Sprint: `development_gates: List[DevelopmentGate]` (sprint.py:135) **← NAMING INCONSISTENCY**
- Track: `dependencies: List[TrackDependency]` (track.py:128)

**Structure:**
```python
@dataclass
class TaskDependency:
    type: DependencyType      # task, sprint, track, external
    target_id: str            # What this depends on
    target_status: str        # Required status (e.g., "completed")
    reason: str               # Why this dependency exists
```

**Purpose:** Define what must be satisfied before this ticket can progress. This is the **source of truth** for prerequisites.

**Problem:** Sprint uses `development_gates` instead of `dependencies` - confusing naming.

### 2.2 Forward/Reverse Index (`blocks` / `blocked_by` / `depends_on` / `depended_on_by`)

**Three overlapping systems:**

| Field | Type | Purpose | Status |
|-------|------|---------|--------|
| `blocks` | `List[*Dependency]` | Forward index - what this ticket blocks | Active |
| `blocked_by` | `List[*Blocker]` | Computed blockers for display | **DEPRECATED** |
| `depends_on` | `List[DependencyStatus]` | Cached status for O(1) blocking checks | **PRIMARY (NEW)** |
| `depended_on_by` | `List[str]` | Reverse index - who depends on this | Active |

**DependencyStatus (the new primary system):**
```python
@dataclass
class DependencyStatus:
    blocker_id: str           # The dependency's ID
    blocker_type: str         # task/sprint/track/external
    required_status: str      # Status needed to unblock
    current_status: str       # Cached current status of blocker
    blocks_transition_to: str # What status transition this blocks
    last_checked: datetime    # When status was last synced

    def is_satisfied(self) -> bool: ...
    def blocks_transition(self, target_status: str) -> bool: ...
```

**Key insight:** The model validation enforces `blocked == any(not dep.is_satisfied() for dep in depends_on)` - making `depends_on` the authoritative source for blocking state.

### 2.3 Quality Gates (Track/Task Level)

**Track-level gates:** (track.py:72-88)
```python
@dataclass
class QualityGate:
    name: str              # e.g., "Schema Review"
    threshold: int         # 0-100 pass threshold
    blocking: bool         # Does this gate block progress?
    status: GateStatus     # not_run, running, passed, failed
    score: Optional[int]   # Actual score achieved
```

**Task-level gates:** (task.py:15-35)
```python
@dataclass
class GateInfo:
    blocks_status: str     # "completed" or "production_ready"
    threshold: int         # 0-100 pass threshold
    is_blocking: bool      # Does this gate block?
    score: Optional[int]   # Actual score achieved
```

**Sprint-level gates:** (sprint.py:169)
```python
quality_gates: List = field(default_factory=list)  # UNTYPED!
```

**Problem:** Sprint `quality_gates` is `List[Any]` - no type safety.

### 2.4 Standards (Cascading Quality Policies)

**Location:** standard.py (71-277)

**Structure:**
```python
@dataclass
class Standard:
    id: str                        # "commit-required", "test-coverage"
    name: str                      # Human-readable name
    type: StandardType             # commit_check, file_check, test_run, custom_script
    enforcement: EnforcementMode   # blocking, warning, audit
    validation: Dict[str, Any]     # Validator-specific config
    overrides: List[StandardOverride]  # Runtime overrides
```

**Cascade:**
- Roadmap → Track → Sprint → Task
- Child can override parent standards
- `EnforcementMode.BLOCKING` prevents completion

**This is the most well-designed system** - clear cascade, enforcement modes, override support.

### 2.5 Deliverables

**Task:** Typed (task.py:78-82)
```python
@dataclass
class Deliverable:
    type: DeliverableType   # code, test, documentation, config, other
    paths: List[str]        # File paths or glob patterns
```

**Sprint/Track:** Untyped
```python
deliverables: List[str] = field(default_factory=list)
```

**Problem:** No validation that deliverables exist or meet quality criteria.

### 2.6 Success Criteria

**Only on Sprint:** (sprint.py:161)
```python
success_criteria: List[str] = field(default_factory=list)
```

**Problem:**
- Not on Task (where most work happens)
- Not on Track or Roadmap
- No formal assessment mechanism
- No enforcement

---

## Part 3: System Overlap Analysis

### 3.1 Redundant Systems

```
Static Dependencies ──────────────────────────────────────────┐
(dependencies/development_gates)                              │
    │                                                         │
    ├──→ depends_on (NEW - cached status)                    │ ALL REPRESENT
    │        └──→ blocked flag (computed from depends_on)    │ THE SAME CONCEPT:
    │                                                         │ "What blocks this
    ├──→ blocked_by (DEPRECATED - computed for display)      │  ticket from
    │                                                         │  progressing?"
    └──→ blocks (forward index - reverse of dependencies)    │
                                                              │
development_gates (Sprint only - same as dependencies) ───────┘
```

### 3.2 Overlapping Gate Concepts

```
Task.gate_info       ─┐
                      ├──→ "Quality check with pass threshold"
Track.quality_gates  ─┤    (same concept, different implementations)
                      │
Sprint.quality_gates ─┘    (UNTYPED - implementation incomplete)
```

### 3.3 Standards vs Gates Confusion

| Feature | Standards | Quality Gates |
|---------|-----------|---------------|
| Cascade | Yes (Roadmap→Track→Sprint→Task) | No |
| Enforcement modes | blocking/warning/audit | blocking only |
| Override support | Yes (with expiration) | No |
| Validation types | 4 types | Threshold only |
| Location | All levels | Track + Task only |

**These should be unified** - standards are more flexible than gates.

---

## Part 4: Consolidation Proposal

### 4.1 Design Principles

1. **Layer 1 only** - All dependency/blocking logic in base Ticket class
2. **Single source of truth** - One system per concept
3. **Explicit over implicit** - No computed fields that could drift
4. **Typed everywhere** - No `List[Any]`
5. **Standards-first** - Migrate gates to standards pattern

### 4.2 Proposed Unified Model (Layer 1)

```python
@dataclass
class Ticket:
    """Layer 1: Base ticket with ALL dependency/blocking/quality concepts."""

    # === DEPENDENCIES (Single System) ===
    # Static config - what this ticket needs to proceed
    dependencies_local: List[Dependency] = field(default_factory=list)

    # Computed by smart accessor (L2) - flattens from children if parent
    @property
    def dependencies(self) -> List[Dependency]: ...

    # === BLOCKING STATUS (Computed, Not Stored) ===
    # No more: blocked, blocked_by, depends_on
    # Instead: computed from dependencies_local.is_satisfied()
    @property
    def is_blocked(self) -> bool: ...

    @property
    def blocking_dependencies(self) -> List[Dependency]: ...

    # === QUALITY REQUIREMENTS (Unified) ===
    # Replace quality_gates + standards with single system
    requirements_local: List[Requirement] = field(default_factory=list)

    # Computed by smart accessor (L2) - inherits from ancestors
    @property
    def requirements_effective(self) -> List[Requirement]: ...

    # === SUCCESS CRITERIA (New) ===
    success_criteria_local: List[SuccessCriterion] = field(default_factory=list)

    # === DELIVERABLES (Typed + Validated) ===
    deliverables_local: List[Deliverable] = field(default_factory=list)

    # Computed by smart accessor (L2) - aggregates from children if parent
    @property
    def deliverables(self) -> List[Deliverable]: ...
```

### 4.3 Unified Dependency

```python
@dataclass
class Dependency:
    """Single dependency type for all levels."""

    # What is depended on
    target_id: str
    target_type: DependencyType  # ticket, external

    # When is it satisfied
    required_status: Status

    # What does it block
    blocks_transition_to: Status  # in_progress (hard) or completed (soft)

    # Metadata
    reason: str
    optional: bool = False

    # Runtime state (updated by sync operations)
    current_status: Optional[Status] = None
    last_checked: Optional[datetime] = None

    def is_satisfied(self) -> bool:
        """Check if dependency is currently satisfied."""
        if self.current_status is None:
            return False  # Unknown state = blocked
        return status_progression_index(self.current_status) >= \
               status_progression_index(self.required_status)

    def blocks_transition(self, target: Status) -> bool:
        """Check if this dependency blocks a specific transition."""
        if self.is_satisfied():
            return False
        return status_progression_index(target) >= \
               status_progression_index(self.blocks_transition_to)
```

### 4.4 Unified Requirement (Replaces Gates + Standards)

```python
@dataclass
class Requirement:
    """Unified quality requirement (replaces QualityGate + Standard)."""

    # Identity
    id: str
    name: str
    description: str

    # Classification
    type: RequirementType  # commit_check, file_check, test_run, threshold, custom
    enforcement: EnforcementMode  # blocking, warning, audit

    # Validation config
    validation: RequirementValidation  # Type-specific config

    # Threshold (for gate-style requirements)
    threshold: Optional[int] = None  # 0-100
    score: Optional[int] = None

    # State
    status: RequirementStatus = RequirementStatus.NOT_RUN
    enabled: bool = True

    # Overrides
    overrides: List[RequirementOverride] = field(default_factory=list)

    def is_satisfied(self) -> bool:
        """Check if requirement is satisfied."""
        if not self.enabled:
            return True
        if self.status == RequirementStatus.PASSED:
            return True
        if self.threshold is not None and self.score is not None:
            return self.score >= self.threshold
        return False

    def blocks_completion(self) -> bool:
        """Check if this requirement blocks completion."""
        return self.enforcement == EnforcementMode.BLOCKING and not self.is_satisfied()
```

### 4.5 Success Criterion (New)

```python
@dataclass
class SuccessCriterion:
    """Formal success criterion with assessment."""

    id: str
    description: str

    # Assessment
    assessor: Optional[str] = None  # Who should assess
    assessment_type: AssessmentType = AssessmentType.MANUAL

    # Validation (for automated assessment)
    validation: Optional[Dict[str, Any]] = None

    # State
    assessed: bool = False
    met: Optional[bool] = None
    assessed_at: Optional[datetime] = None
    assessed_by: Optional[str] = None
    notes: Optional[str] = None

    def is_met(self) -> bool:
        """Check if criterion is met."""
        return self.assessed and self.met == True
```

### 4.6 Typed Deliverable (Everywhere)

```python
@dataclass
class Deliverable:
    """Typed deliverable with validation."""

    # Identity
    id: str
    name: str
    type: DeliverableType  # code, test, documentation, config, artifact

    # Location
    paths: List[str]  # File paths or patterns

    # Validation
    required: bool = True
    validation: Optional[DeliverableValidation] = None

    # State
    exists: Optional[bool] = None  # Checked at runtime
    validated: Optional[bool] = None
    validated_at: Optional[datetime] = None

    def is_complete(self) -> bool:
        """Check if deliverable is complete."""
        if not self.required:
            return True
        return self.exists == True and (
            self.validation is None or self.validated == True
        )
```

---

## Part 5: Migration Path

### 5.1 Integration with Sprint 6a-6d

| Sprint | Current Focus | Additions Needed |
|--------|---------------|------------------|
| **6a** | Layer 1-3 architecture | Add `Dependency`, `Requirement`, `SuccessCriterion`, `Deliverable` to L1 |
| **6b** | Serialization | Migrate YAML: `dependencies` → `dependencies_local`, remove `blocked_by` |
| **6c** | Operations | Update all operations to use unified types |
| **6d** | Interfaces | Update CLI/MCP to show unified dependency/requirement info |

### 5.2 Deprecation Schedule

| System | Sprint | Action |
|--------|--------|--------|
| `blocked_by` | 6b | Remove from YAML, remove from models |
| `depends_on` | 6b | Merge into `Dependency.current_status` |
| `development_gates` | 6b | Rename to `dependencies_local` |
| `quality_gates` (Track) | 6c | Migrate to `requirements_local` |
| `gate_info` (Task) | 6c | Migrate to `requirements_local` |
| `standards` | 6c | Merge with `requirements_local` |

### 5.3 Backward Compatibility

**YAML v1 → v2 mapping:**
```yaml
# v1 (current)
task:
  dependencies:
    - type: task
      target_id: other-task
      target_status: completed
  blocked_by: [...]  # REMOVE
  depends_on: [...]  # MERGE INTO dependencies

# v2 (unified)
task:
  dependencies_local:
    - target_id: other-task
      target_type: ticket
      required_status: completed
      blocks_transition_to: in_progress
      reason: "Needs other task's output"
      # Runtime fields populated by loader
      current_status: null
      last_checked: null
```

---

## Part 6: Recommendations

### 6.1 Immediate Actions (No Code Changes)

1. **Document the current system** - This analysis serves as the canonical reference
2. **Add to Sprint 6a scope** - Include dependency consolidation in task definitions
3. **Create validation rules** - Define what makes a valid dependency/requirement

### 6.2 Sprint 6a Additions

Add new task to Sprint 6a:
```yaml
task:
  id: sqlite-backend-6a-task-011
  title: Layer 1 - Unified Dependency and Requirement Types
  description: |
    Add consolidated types to Layer 1 base ticket:
    1. Dependency (replaces TaskDependency, TrackDependency, DevelopmentGate, DependencyStatus)
    2. Requirement (replaces QualityGate, Standard, GateInfo)
    3. SuccessCriterion (new)
    4. Deliverable (typed, everywhere)
```

### 6.3 Questions for User Approval

Before proceeding, need clarification on:

1. **External dependencies** - Should `external` type dependencies support different validation (URL health check, service availability)?

2. **Requirement inheritance** - When a sprint inherits requirements from track, should child requirements override or merge?

3. **Success criteria assessment** - Should we support automated assessment types beyond manual?

4. **Test tracking** - Should we add a formal `TestResult` class or keep tests as a requirement type?

---

## Appendix A: Field Inventory by Model

### Task Fields (task.py)
```
dependencies: List[TaskDependency]       # Static config
blocks: List[TaskDependency]             # Forward index
blocked_by: List[TaskBlocker]            # DEPRECATED
depends_on: List[DependencyStatus]       # NEW (primary)
depended_on_by: List[str]                # Reverse index
blocked: bool                            # Computed from depends_on
gate_info: Optional[GateInfo]            # For gate tasks only
audit_results: Optional[AuditResults]    # For gate tasks only
deliverables: List[Deliverable]          # Typed
commits: List[GitCommit]                 # Git tracking
```

### Sprint Fields (sprint.py)
```
development_gates: List[DevelopmentGate] # Static config (BAD NAME)
blocks: List[DevelopmentGate]            # Forward index
blocked_by: List[SprintBlocker]          # DEPRECATED
depends_on: List[DependencyStatus]       # NEW (primary)
depended_on_by: List[str]                # Reverse index
blocked: bool                            # Computed from depends_on
quality_gates: List                      # UNTYPED!
standards: List[Standard]                # Quality policies
success_criteria: List[str]              # Unstructured
deliverables: List[str]                  # UNTYPED!
commits: List[TaskCompletionCommit]      # Git tracking
```

### Track Fields (track.py)
```
dependencies: List[TrackDependency]      # Static config
blocks: List[TrackDependency]            # Forward index
blocked_by: List[TrackBlocker]           # DEPRECATED
depends_on: List[DependencyStatus]       # NEW (primary)
depended_on_by: List[str]                # Reverse index
blocked: bool                            # Computed from depends_on
quality_gates: List[QualityGate]         # Typed
standards: List[Standard]                # Quality policies
deliverables: List[str]                  # UNTYPED!
commits: List[SprintCompletionCommit]    # Git tracking
```

---

## Appendix B: Status Progression

```
not_started
    ↓
in_progress ←─────────────────────────┐
    ↓                                  │
paused ──────────────────────────────→┘
    ↓
completion_gate_check
    ↓
completed
    ↓
production_gate_check (Sprint/Track only)
    ↓
production_ready (Sprint/Track only)
    ↓
deployed (Sprint/Track only)

Terminal states: wont_do, superseded
```

**Blocking thresholds:**
- Hard blocker: blocks `in_progress` (can't start work)
- Soft blocker: blocks `completed` (can start but not finish)
- Gate blocker: blocks `production_ready` (can complete but not release)
