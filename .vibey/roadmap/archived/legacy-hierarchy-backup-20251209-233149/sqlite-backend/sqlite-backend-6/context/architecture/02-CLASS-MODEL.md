# Class Model

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     LAYER 3: SEMANTIC LAYER (PLUGGABLE)                      │
│                                                                              │
│  ┌─────────────────────────────────┐    ┌─────────────────────────────────┐ │
│  │     VIBEY SEMANTIC (default)    │    │     JIRA SEMANTIC (override)    │ │
│  │                                 │    │                                 │ │
│  │  RoadmapTicket                  │    │  JiraProject                    │ │
│  │    └─ TrackTicket               │ OR │    └─ JiraEpic / JiraSprint     │ │
│  │        └─ SprintTicket          │    │        └─ JiraIssue             │ │
│  │            └─ TaskTicket        │    │            └─ JiraSubtask       │ │
│  │                                 │    │                                 │ │
│  │  + version, strategic_value    │    │  + issue_key, story_points      │ │
│  │  + plan_file, task_type        │    │  + components[], labels[]       │ │
│  │  + complexity                   │    │  + fix_versions[], custom_fields│ │
│  └────────────────┬────────────────┘    └────────────────┬────────────────┘ │
│                   │                                      │                   │
│                   └──────────────┬───────────────────────┘                   │
│                                  │                                           │
│                     SemanticLayer interface                                  │
│                   - ticket_types, hierarchy                                  │
│                   - get_ticket_class(type)                                   │
│                   - map_status_to/from_canonical()                           │
│                                  │                                           │
│                                  ▼                                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                         LAYER 2: HIERARCHICAL TICKET                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         HierarchicalTicket                               │ │
│  │  - parent_id: str              - sequence: int           - slug: str    │ │
│  │  + siblings → List[Self]       + next_sibling → Self?    + reorder()    │ │
│  │  + commits → List[GitCommit]   + requirements_effective  + all_criteria │ │
│  │  + deliverables, tests, subtasks, dependencies, success_criteria        │ │
│  │  + production_gates            + effective_priority                     │ │
│  │  + all_referenced_artifacts    + stale_documentation_artifacts          │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                       │
│                                       ▼                                       │
├───────────────────────────────────────────────────────────────────────────────┤
│                              LAYER 1: TICKET                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                              Ticket                                      │ │
│  │  - started_at, completed_at   - production_ready_at, deployed_at        │ │
│  │  - commits_local: List[GitCommit]     - assigned_agents_local: List[str]│ │
│  │  - parent_ref: str?            - requirements_local: List[Requirement]  │ │
│  │  - priority: Priority?         - deferred: bool                         │ │
│  │  - estimated_duration_local    - actual_duration_local                  │ │
│  │  - estimated_tokens: int?      + effective_tokens → int (aggregates)    │ │
│  │  + start() → (bool, List[str])        + complete() → (bool, List[str])  │ │
│  │  + is_parent, is_child, is_ultimate_parent, is_ultimate_child           │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                       │
│                                       ▼                                       │
├───────────────────────────────────────────────────────────────────────────────┤
│                              LAYER 0: COMPLETABLE                            │
│                                                                               │
│                    ┌──────────────────────────────────────┐                  │
│                    │            Completable               │                  │
│                    │  - id: str (ULID)                    │                  │
│                    │  - name: str                         │                  │
│                    │  - description: str                  │                  │
│                    │  - status: CompletableStatus         │                  │
│                    │  - criteria: List[Criterion]         │                  │
│                    │  - created_at: datetime              │                  │
│                    │  + can_transition_to(status)         │                  │
│                    │  + progress_for_transition(status)   │                  │
│                    │  + progress → Progress               │                  │
│                    │  + children → List[str] (computed)   │                  │
│                    └──────────────┬───────────────────────┘                  │
│                                   │                                          │
│                    ┌──────────────┴──────────────┐                           │
│                    ▼                             ▼                           │
│  ┌─────────────────────────────┐   ┌─────────────────────────────────────┐  │
│  │          Ticket             │   │            Artifact                  │  │
│  │  (work item with lifecycle) │   │    (file entity with verification)  │  │
│  │                             │   │                                      │  │
│  │  - started_at               │   │  - paths: List[str]                 │  │
│  │  - completed_at             │   │  - content_hash: str                │  │
│  │  - assigned_agents          │   │  - artifact_type: ArtifactType      │  │
│  │  - commits                  │   │  - provenance: ArtifactProvenance   │  │
│  │  - requirements             │   │  - documents_artifact_id: str?      │  │
│  │  - deferred: bool           │   │  - depends_on_artifact_ids: List    │  │
│  │                             │   │                                      │  │
│  │  + start()                  │   │  + is_stale → bool (computed)       │  │
│  │  + complete()               │   │  + is_orphan → bool (computed)      │  │
│  │                             │   │  + check_staleness()                │  │
│  │        ↓                    │   │                                      │  │
│  │  HierarchicalTicket         │   │  (Implicit FileExistsTarget         │  │
│  │        ↓                    │   │   criterion on all artifacts)       │  │
│  │  Domain Models              │   │                                      │  │
│  └─────────────────────────────┘   └─────────────────────────────────────┘  │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                           Criterion                                      │ │
│  │  - id: str                      - description: str                      │ │
│  │  - blocks_transition_to: CompletableStatus                              │ │
│  │  - target: CriterionTarget      - required: bool                        │ │
│  │  + is_met → bool                + evaluate(context) → bool              │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                      │
│                                       ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                      CriterionTarget Subtypes                            │ │
│  │                                                                          │ │
│  │  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐               │ │
│  │  │CompletableTarget│ │FileExistsTarget│ │TestPassesTarget│               │ │
│  │  │- completable_id │ │- paths: List   │ │- test_command  │               │ │
│  │  │- required_status│ │- all_required  │ │- pass_threshold│               │ │
│  │  │                 │ │- deliverable_  │ │                │               │ │
│  │  │ (works for both │ │  type          │ │                │               │ │
│  │  │  Tickets AND    │ │                │ │                │               │ │
│  │  │  Artifacts!)    │ │                │ │                │               │ │
│  │  └─────────────────┘ └────────────────┘ └────────────────┘               │ │
│  │                                                                          │ │
│  │  ┌──────────────────┐ ┌────────────────┐ ┌────────────────┐             │ │
│  │  │TestCoverageTarget│ │ThresholdTarget │ │  ManualTarget  │             │ │
│  │  │- source_command  │ │- metric_name   │ │- assessor      │             │ │
│  │  │- coverage_type   │ │- threshold     │ │- instructions  │             │ │
│  │  │- overall_thresh  │ │- comparison    │ │- assessed: bool│             │ │
│  │  │- per_file_thresh │ │- current_value │ │- met: bool     │             │ │
│  │  │- exclude_patterns│ │                │ │                │             │ │
│  │  └──────────────────┘ └────────────────┘ └────────────────┘             │ │
│  │                                                                          │ │
│  │  ┌────────────────┐                                                      │ │
│  │  │ ExternalTarget │                                                      │ │
│  │  │- system_name   │                                                      │ │
│  │  │- endpoint      │                                                      │ │
│  │  │- expected_     │                                                      │ │
│  │  │  status        │                                                      │ │
│  │  └────────────────┘                                                      │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Unified Completable Model

The key insight: **Both Tickets and Artifacts are things that can be "completed" via criteria.**

### Completable Base Class

| Field | Type | Description |
|-------|------|-------------|
| `id` | str (ULID) | Immutable identity |
| `name` | str | Human-readable name |
| `description` | str | Detailed description |
| `status` | CompletableStatus | Current state |
| `criteria` | List[Criterion] | Blocking conditions |
| `created_at` | datetime | When created |

| Method | Returns | Description |
|--------|---------|-------------|
| `can_transition_to(status)` | (bool, List[str]) | Can transition + blocking reasons |
| `progress_for_transition(status)` | Progress | Progress toward specific status |
| `progress` | Progress | Default progress (toward COMPLETED) |
| `children` | List[str] | Computed from CompletableTarget criteria |

### Status Progression (Shared)

```
NOT_STARTED     → No criteria met, hasn't begun
    ↓
IN_PROGRESS     → Some criteria met, work ongoing
    ↓
COMPLETED       → All criteria for COMPLETED met
    ↓ (Tickets only)
PRODUCTION_READY → All criteria for PRODUCTION_READY met
    ↓ (Tickets only)
DEPLOYED        → Deployed to production
```

**For Artifacts:** Typically stop at COMPLETED (no deployment lifecycle)

**For Tickets:** Full lifecycle through deployment

---

## Ticket vs Artifact: What's Different

| Aspect | Ticket | Artifact |
|--------|--------|----------|
| **Purpose** | Work to be done | File to be produced/verified |
| **Lifecycle** | Full (NOT_STARTED → DEPLOYED) | Partial (NOT_STARTED → COMPLETED) |
| **Has assigned agents** | Yes | No |
| **Has commits** | Yes | No (but tracked in provenance) |
| **Has parent hierarchy** | Yes (HierarchicalTicket) | No (flat, but has `documents_artifact_id`) |
| **Has requirements** | Yes (cascading) | No |
| **Implicit criterion** | None | FileExistsTarget (file must exist) |

---

## Artifact as Completable

### Implicit FileExistsTarget

Every Artifact has an **implicit** criterion that the file must exist:

```yaml
artifact:
  id: artifact_01JB...
  name: "api.py"
  paths: ["src/api.py"]
  criteria:
    # Implicit - always present:
    - description: "File exists"
      target_type: file_exists
      paths: ["src/api.py"]
      blocks_transition_to: IN_PROGRESS

    # Explicit - user-defined:
    - description: "Type checks pass"
      target_type: test_passes
      test_command: "mypy src/api.py"
      blocks_transition_to: COMPLETED
```

### Artifact Status Progression

```
NOT_STARTED     → File doesn't exist
    ↓              (FileExistsTarget not met)
IN_PROGRESS     → File exists, but criteria not all met
    ↓              (e.g., exists but linting fails)
COMPLETED       → File exists AND all criteria pass
```

### Example: Artifact with Multiple Criteria

```yaml
artifact:
  id: artifact_01JB3QVE5N...
  name: "API Module"
  status: in_progress
  paths: ["src/api.py"]
  criteria:
    - description: "File exists"
      target_type: file_exists
      is_met: true  ✓

    - description: "Type checks pass"
      target_type: test_passes
      test_command: "mypy src/api.py"
      is_met: false  ✗

    - description: "Linting passes"
      target_type: test_passes
      test_command: "ruff check src/api.py"
      is_met: true  ✓

    - description: "Has docstrings"
      target_type: test_passes
      test_command: "pydocstyle src/api.py"
      is_met: false  ✗
```

**Progress:** 2/4 criteria met → 50% → status: `IN_PROGRESS`

---

## TestCoverageTarget

Test coverage is handled by a dedicated `TestCoverageTarget`, separate from `TestPassesTarget`:

| Target | Purpose |
|--------|---------|
| `TestPassesTarget` | Do tests pass? (pass/fail rate) |
| `TestCoverageTarget` | Is code adequately covered? (coverage metrics) |

### Why Separate?

1. **Different concerns** - Pass rate and coverage are independent metrics
2. **Different thresholds** - 100% pass rate is common; 100% coverage is rare
3. **Different granularity** - Coverage has per-file, line vs branch, exclusions
4. **Different blocking** - Tests might block IN_PROGRESS; coverage might block COMPLETED

### TestCoverageTarget Fields

| Field | Type | Description |
|-------|------|-------------|
| `source_command` | str | Command to generate coverage (e.g., `pytest --cov`) |
| `coverage_type` | CoverageType | LINE, BRANCH, or BOTH |
| `overall_threshold` | float | Minimum overall coverage (default: 80.0) |
| `branch_threshold` | float? | Minimum branch coverage (if coverage_type includes BRANCH) |
| `per_file_threshold` | float? | Minimum per-file coverage |
| `exclude_patterns` | List[str] | Files to exclude (e.g., `*/migrations/*`) |
| `include_patterns` | List[str]? | If set, only these files count |

### Example Usage

```yaml
criteria:
  # Tests must pass (separate concern)
  - description: "All tests pass"
    target_type: test_passes
    test_command: "pytest"
    pass_threshold: 100.0
    blocks_transition_to: IN_PROGRESS

  # Coverage must meet threshold (separate concern)
  - description: "80% line coverage, 70% per-file minimum"
    target_type: test_coverage
    source_command: "pytest --cov --cov-report=json"
    coverage_type: line
    overall_threshold: 80.0
    per_file_threshold: 70.0
    exclude_patterns:
      - "*/tests/*"
      - "*/migrations/*"
    blocks_transition_to: COMPLETED
```

**Code:** [`sample_code/models/test_coverage_target.py`](../sample_code/models/test_coverage_target.py)

---

## Token Estimation (Ticket Layer)

Token estimation lives at the **Ticket layer (Layer 1)**, not at the semantic layer (TaskTicket), because:
1. Any ticket level could have a direct estimate OR aggregate from children
2. Artifacts don't need token estimation (they're files, not work)
3. Aggregation logic is consistent across all ticket types

### Fields

| Field | Type | Layer | Description |
|-------|------|-------|-------------|
| `estimated_tokens` | `Optional[int]` | Ticket (L1) | Direct estimate, if provided |
| `effective_tokens` | `int` (computed) | Ticket (L1) | Aggregated or direct value |

### Aggregation Logic

```python
class Ticket(Completable):
    estimated_tokens: Optional[int] = None

    @property
    def effective_tokens(self) -> int:
        """Returns estimated_tokens if set, else aggregates from children."""
        if self.estimated_tokens is not None:
            return self.estimated_tokens

        # Aggregate from child tickets (not artifacts)
        children = [c for c in self.children if isinstance(c, Ticket)]
        if not children:
            return 0
        return sum(child.effective_tokens for child in children)
```

### Usage Patterns

| Ticket Type | Typical Usage |
|-------------|---------------|
| TaskTicket | Set `estimated_tokens` directly (leaf work units) |
| SprintTicket | Usually aggregates, but CAN override |
| TrackTicket | Usually aggregates, but CAN override |
| RoadmapTicket | Always aggregates |

### Why Not at Completable?

Artifacts don't have token estimates because:
- Tokens estimate **AI effort** for work items
- Artifacts are **outputs** of work, not work themselves
- An artifact's "cost" is captured by the task that produces it

---

## CompletableTarget: Unified References

Since both Ticket and Artifact extend Completable, `CompletableTarget` works for both:

```yaml
# Task depending on another task (sibling dependency)
criteria:
  - target_type: completable
    completable_id: task_01JB3QVE5N...   # Points to Ticket
    required_status: COMPLETED
    blocks_transition_to: IN_PROGRESS

# Task depending on an artifact (deliverable)
criteria:
  - target_type: completable
    completable_id: artifact_01JB3QVE...  # Points to Artifact
    required_status: COMPLETED
    blocks_transition_to: COMPLETED
```

**Note:** `ArtifactTarget` is **REMOVED**. Use `CompletableTarget` for both.

---

## Class Relationship Matrix

| Class | Inherits From | Contains | Referenced By |
|-------|--------------|----------|---------------|
| **Completable** | BaseModel | List[Criterion] | CompletableTarget |
| **Ticket** | Completable | List[GitCommit], List[Requirement] | - |
| **Artifact** | Completable | ArtifactProvenance | - |
| **ArtifactProvenance** | BaseModel | - | Artifact |
| **Criterion** | BaseModel | CriterionTarget | Completable |
| **CriterionTarget** | BaseModel (abstract) | - | Criterion |
| **CompletableTarget** | CriterionTarget | - | - |
| **FileExistsTarget** | CriterionTarget | - | - |
| **TestPassesTarget** | CriterionTarget | TestResult | - |
| **TestCoverageTarget** | CriterionTarget | - | - |
| **ThresholdTarget** | CriterionTarget | - | - |
| **ManualTarget** | CriterionTarget | - | - |
| **ExternalTarget** | CriterionTarget | - | - |
| **HierarchicalTicket** | Ticket | - | Self (parent_id) |
| **RoadmapTicket** | HierarchicalTicket | List[ActivityLogEntry] | - |
| **TrackTicket** | HierarchicalTicket | - | - |
| **SprintTicket** | HierarchicalTicket | - | - |
| **TaskTicket** | HierarchicalTicket | - | - |
| **Requirement** | BaseModel | CriterionTemplate, ApplicabilityRules | Ticket |
| **CriterionTemplate** | BaseModel | - | Requirement |
| **ApplicabilityRules** | BaseModel | - | Requirement |
| **Progress** | BaseModel | - | Completable |
| **GitCommit** | BaseModel | - | Ticket, Artifact |
| **ActivityLogEntry** | BaseModel | - | RoadmapTicket |
| **TestResult** | BaseModel | - | TestPassesTarget |

---

## Code References

### Layer 0: Core Abstractions

| Class | Code |
|-------|------|
| Completable | [`sample_code/models/completable.py`](../sample_code/models/completable.py) |
| Criterion | [`sample_code/models/criterion.py`](../sample_code/models/criterion.py) |
| CriterionTarget | [`sample_code/models/criterion_target.py`](../sample_code/models/criterion_target.py) |
| Artifact | [`sample_code/models/artifact.py`](../sample_code/models/artifact.py) |

### Ticket Layers

| Layer | Class | Code |
|-------|-------|------|
| Layer 1 | Ticket | [`sample_code/models/ticket.py`](../sample_code/models/ticket.py) |
| Layer 2 | HierarchicalTicket | [`sample_code/models/hierarchical_ticket.py`](../sample_code/models/hierarchical_ticket.py) |
| Layer 3 | RoadmapTicket | [`sample_code/models/roadmap_ticket.py`](../sample_code/models/roadmap_ticket.py) |

### Supporting Classes

| Class | Code |
|-------|------|
| Requirement | [`sample_code/models/requirement.py`](../sample_code/models/requirement.py) |
| RequirementResolver | [`sample_code/models/func_resolve_requirements.py`](../sample_code/models/func_resolve_requirements.py) |
| ArtifactProvenance | [`sample_code/models/artifact_provenance.py`](../sample_code/models/artifact_provenance.py) |

---

## Implicit Parent-Child Relationships

Children are NOT stored in explicit lists. They are DERIVED from `CompletableTarget` criteria.

### Dependencies vs Children

Both use `CompletableTarget`, but differ in `blocks_transition_to`:

| Relationship | blocks_transition_to | Meaning |
|--------------|---------------------|---------|
| **Dependency** (sibling) | `IN_PROGRESS` | Must complete before I can START |
| **Child** | `COMPLETED` | Must complete before I can COMPLETE |

### Ticket → Artifact Relationships

| Relationship | blocks_transition_to | Meaning |
|--------------|---------------------|---------|
| **Deliverable** | `COMPLETED` | Artifact must be COMPLETED before ticket can complete |
| **Prerequisite** | `IN_PROGRESS` | Artifact must exist before ticket can start |

**Code:** [`sample_code/models/block_008.py`](../sample_code/models/block_008.py), [`sample_code/models/block_009.py`](../sample_code/models/block_009.py)

---

## Requirement System

Requirements cascade down the **Ticket** hierarchy and **generate criteria** when applicable.

**Note:** Requirements apply to Tickets only, not Artifacts. Artifact criteria are defined directly on the artifact.

Requirements act as **criterion templates** that get instantiated based on `ApplicabilityRules`:

| Field | Purpose |
|-------|---------|
| `applies_to_types` | Which ticket types (roadmap, track, sprint, task) |
| `applies_to_phases` | Which phases (design, implementation, testing) |
| `inherit_mode` | How children inherit (INHERIT, OVERRIDE, SKIP) |
| `enforceable` | If true, descendants cannot OVERRIDE or SKIP |
| `skip_justification` | Required when inherit_mode=SKIP |

### InheritMode (Child's Choice)

| Mode | Effect |
|------|--------|
| `INHERIT` | Use stricter of local vs ancestor |
| `OVERRIDE` | Child replaces ancestor's requirement |
| `SKIP` | Child opts out (requires justification) |

### Enforceable Flag (Ancestor's Constraint)

When `enforceable=True` on a requirement, descendants **cannot** use OVERRIDE or SKIP:

```yaml
# Roadmap-level requirement
requirements:
  - id: security-auth-required
    name: "All endpoints require authentication"
    enforceable: true  # Children CANNOT skip or override
    criterion_template:
      target_type: test_passes
      test_command: "pytest tests/security/test_auth.py"
```

This is useful for:
- Security requirements that must apply everywhere
- Compliance requirements that can't be opted out
- Critical quality gates

**Code:** [`sample_code/models/requirement.py`](../sample_code/models/requirement.py), [`sample_code/models/func_resolve_requirements.py`](../sample_code/models/func_resolve_requirements.py)

---

## Git Commit Integration

GitCommit tracks file changes and links to both Tickets and Artifacts.

### GitCommit Fields

| Field | Type | Description |
|-------|------|-------------|
| `sha` | str | Full 40-char git SHA |
| `message` | str | Full commit message |
| `date` | datetime | Commit timestamp |
| `author` | str | Commit author |
| `platform` | str | AI platform (claude-code, goose, etc.) |
| `completes_tickets` | List[str] | Ticket IDs from "Completes:" lines |
| `files_added` | List[str] | Files created by this commit |
| `files_modified` | List[str] | Files modified by this commit |
| `files_deleted` | List[str] | Files deleted by this commit |
| `creates_artifacts` | List[str] | Artifact IDs matched to added files |
| `modifies_artifacts` | List[str] | Artifact IDs matched to modified files |
| `deletes_artifacts` | List[str] | Artifact IDs matched to deleted files |

### Artifact Commit Tracking

Artifacts track which commits created/modified them:

| Field | Type | Description |
|-------|------|-------------|
| `created_by_commit` | str? | SHA of commit that created the file |
| `last_modified_by_commit` | str? | SHA of most recent modifying commit |
| `deleted_by_commit` | str? | SHA of commit that deleted the file |
| `commit_history` | List[str] | All commit SHAs that touched this artifact |
| `documented_source_hash` | str? | For docs: hash of source when documented |

### Commit Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ PRE-COMMIT HOOK                                                  │
│ verify_completion_claims(message) → blocks if criteria not met  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ POST-COMMIT HOOK: process_commit(sha)                            │
│                                                                  │
│ 1. Parse commit → GitCommit.from_git(sha)                        │
│ 2. Extract file changes (added, modified, deleted)              │
│ 3. Link to artifacts → commit.link_to_artifacts(registry)       │
│ 4. Update artifact states:                                       │
│    - created_by_commit, last_modified_by_commit                 │
│    - content_hash (recompute)                                    │
│    - Check documentation staleness                               │
│ 5. Link to tickets → append to ticket.commits_local             │
│ 6. Transition tickets if "Completes:" present                   │
└─────────────────────────────────────────────────────────────────┘
```

### Documentation Staleness Detection

When a commit modifies an artifact, check if any documentation artifacts reference it:

```python
# Artifact A documents Artifact B
artifact_a.documents_artifact_id = artifact_b.id
artifact_a.documented_source_hash = artifact_b.content_hash  # When docs written

# When B is modified by a commit:
if artifact_b.content_hash != artifact_a.documented_source_hash:
    artifact_a.is_stale = True  # Docs need updating
```

**Code:** [`sample_code/models/git_commit.py`](../sample_code/models/git_commit.py), [`sample_code/models/func_process_commit.py`](../sample_code/models/func_process_commit.py)

---

## Commit-Criterion-Artifact Validation

The system allows divergence between criteria and commits, but makes it visible.

### Possible States

| Criterion Link | Commit Link | State | Validity |
|----------------|-------------|-------|----------|
| ✅ Exists | ✅ Exists | Full traceability | ✅ Ideal |
| ✅ Exists | ❌ Missing | Work not yet done | ✅ Normal (in progress) |
| ❌ Missing | ✅ Exists | Incidental change | ⚠️ Warning |
| ❌ Missing | ❌ Missing | No relationship | ✅ N/A |

### Validation Rules

| Rule | Enforced By | Severity | Blocks? |
|------|-------------|----------|---------|
| Can't complete if criteria not met | Pre-commit hook | ERROR | ✅ Yes |
| Commit touches untracked artifact | Post-commit validation | WARNING | ❌ No |
| Criterion artifact has no commit | Ticket completion validation | WARNING | ❌ No |
| Commit modifies artifact for other ticket | Post-commit validation | INFO | ❌ No |

### When Divergence is Acceptable

| Scenario | Criterion? | Commit? | Why OK |
|----------|------------|---------|--------|
| Pre-existing files | ❌ | ✅ | README, existing code |
| Refactoring | ❌ | ✅ | Shared files touched incidentally |
| Planning task | ❌ | ❌ | No code deliverables |
| Research task | ❌ | ❌ | No code deliverables |
| Review task | ❌ | ❌ | No code deliverables |
| Bug fix on existing | ⚠️ Maybe | ✅ | Depends on tracking preference |

### Validator Usage

```python
validator = CommitArtifactValidator(artifact_registry, ticket_registry)

# Validate a commit
result = validator.validate_commit(commit)
if result.warnings:
    print("Warnings:", result.warnings)
    # "Commit touches artifacts not in task-123 criteria: [utils, helpers]"

# Validate ticket completion
result = validator.validate_ticket_completion(ticket)
if not result.has_full_provenance:
    print("Missing provenance:", result.warnings)
    # "Artifact api_module not touched by any commit on this ticket"
```

### Design Principle

> **Criterion is source of truth** for what task *requires*.
> **Commit is record** of what *happened*.
> **Allow divergence, but make it visible.**

**Code:** [`sample_code/models/commit_artifact_validator.py`](../sample_code/models/commit_artifact_validator.py)

---

## Pluggable Semantic Layer

The semantic layer (Layer 3) is **interchangeable**. Different providers can define their own ticket hierarchy while sharing the core Completable → Ticket → HierarchicalTicket foundation.

### SemanticLayer Interface

```python
class SemanticLayer(ABC):
    @property
    def name(self) -> str: ...           # "vibey" or "jira:PROJ"
    @property
    def ticket_types(self) -> List[str]: ...  # ["roadmap", "track", "sprint", "task"]
    @property
    def hierarchy(self) -> Dict[str, Optional[str]]: ...  # {"task": "sprint", ...}

    def get_ticket_class(self, ticket_type: str) -> Type[HierarchicalTicket]: ...
    def get_type_fields(self, ticket_type: str) -> Dict[str, Any]: ...
    def map_status_to_canonical(self, ticket_type: str, external_status: str) -> TicketStatus: ...
    def map_status_from_canonical(self, ticket_type: str, status: TicketStatus) -> str: ...
```

### Available Semantic Layers

| Layer | Name | Hierarchy | Use Case |
|-------|------|-----------|----------|
| **Vibey** (default) | `vibey` | Roadmap → Track → Sprint → Task | Standalone Vibey usage |
| **Jira** | `jira:PROJ` | Project → Epic/Sprint → Issue → Subtask | Atlassian integration |
| **GitHub** (future) | `github:org/repo` | Milestone → Issue | GitHub Projects integration |
| **Linear** (future) | `linear:TEAM` | Project → Cycle → Issue | Linear integration |

### Vibey vs Jira Semantic Layer

| Aspect | Vibey | Jira |
|--------|-------|------|
| **Root type** | RoadmapTicket | JiraProject |
| **Mid-level** | TrackTicket, SprintTicket | JiraEpic, JiraSprint |
| **Work item** | TaskTicket | JiraIssue |
| **Leaf type** | — | JiraSubtask |
| **ID format** | ULID | PROJECT-123 |
| **Status source** | TicketStatus enum | Jira workflow (configurable) |
| **Custom fields** | Defined in code | Loaded from Jira project |

### Jira Semantic Layer Features

When Jira is the semantic layer:

1. **Fields are dynamic** - Custom fields from Jira project are included
2. **Status mapping** - Jira workflow statuses map to canonical TicketStatus
3. **Issue types** - Story, Bug, Task, Epic, Subtask all supported
4. **Hierarchy is flexible** - Epics/Sprints optional based on board configuration

```python
# Jira semantic layer loads project config
jira_layer = JiraSemanticLayer(JiraProjectConfig(
    project_key="PROJ",
    status_map={
        "To Do": "not_started",
        "In Progress": "in_progress",
        "Done": "completed"
    },
    custom_fields={
        "customfield_10001": {"name": "Story Points", "type": "float"},
        "customfield_10002": {"name": "Team", "type": "str"},
    }
))

# Register and set as active
SemanticLayerRegistry.register(jira_layer)
SemanticLayerRegistry.set_default("jira:PROJ")
```

### What Stays Constant (Layers 0-2)

Regardless of semantic layer, these remain unchanged:

| Layer | Class | Provides |
|-------|-------|----------|
| Layer 0 | Completable | `id`, `status`, `criteria`, `can_transition_to()` |
| Layer 0 | Artifact | File tracking, staleness, provenance |
| Layer 0 | Criterion | Blocking conditions, `blocks_transition_to` |
| Layer 1 | Ticket | Lifecycle, commits, assigned_agents |
| Layer 2 | HierarchicalTicket | parent_id, sequence, slug, navigation |

### What Changes (Layer 3)

| Aspect | Vibey Semantic | Jira Semantic |
|--------|---------------|---------------|
| **Type names** | roadmap, track, sprint, task | project, epic, sprint, issue, subtask |
| **Type-specific fields** | version, strategic_value, plan_file, task_type | issue_key, story_points, components, labels |
| **Status values** | TicketStatus enum directly | Mapped from Jira workflow |
| **Validation rules** | Vibey-specific | Jira-specific |

### Configuration

```yaml
# .vibey/config/semantic.yaml
semantic_layer:
  provider: jira  # or "vibey" (default)

  jira:
    site: company.atlassian.net
    project_key: PROJ

    # Status mapping
    status_map:
      "To Do": not_started
      "In Progress": in_progress
      "In Review": in_progress
      "Done": completed
      "Released": deployed

    # Hierarchy configuration
    use_epics: true
    use_sprints: true

    # Field mapping
    field_map:
      story_points: estimated_tokens  # Map Jira field to Vibey concept
```

**Code:** [`sample_code/models/semantic_layer.py`](../sample_code/models/semantic_layer.py)
