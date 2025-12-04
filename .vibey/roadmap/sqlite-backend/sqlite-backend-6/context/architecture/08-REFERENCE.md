# Reference

## Enumerations

### TicketStatus

**Code:** [`sample_code/models/enum_ticket_status.py`](../sample_code/models/enum_ticket_status.py)

### DeliverableType

**Code:** [`sample_code/models/enum_deliverable_type.py`](../sample_code/models/enum_deliverable_type.py), [`sample_code/models/enum_deliverable_type_1.py`](../sample_code/models/enum_deliverable_type_1.py)

### ArtifactType

**Code:** [`sample_code/models/enum_artifact_type.py`](../sample_code/models/enum_artifact_type.py), [`sample_code/models/enum_artifact_type_1.py`](../sample_code/models/enum_artifact_type_1.py)

### CriterionTargetType

**Code:** [`sample_code/models/enum_criterion_target_type.py`](../sample_code/models/enum_criterion_target_type.py)

---

## Status Progression

### Ticket Status Progression

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

### Artifact Status Progression

Since Artifact extends Completable, it uses the same status enum but with artifact-specific semantics:

```
not_started
    │ (File does NOT exist)
    ↓ Implicit FileExistsTarget must pass
in_progress
    │ (File EXISTS but other criteria not met)
    │ Examples: tests failing, linting errors, hash mismatch
    ↓ All criteria must pass
completed
    │ (File exists AND all verification criteria pass)
```

**Key Difference:** Artifacts typically use only 3 states:
- `NOT_STARTED`: File doesn't exist
- `IN_PROGRESS`: File exists, verification incomplete
- `COMPLETED`: File exists and all criteria satisfied

Artifacts generally don't use `PAUSED`, `PRODUCTION_READY`, `DEPLOYED`, `WONT_DO`, or `SUPERSEDED` states.

---

## Gap Analysis Decisions

### Non-Required Criteria Logging

**Decision:** When `required=false` on a Criterion, always log evaluation and emit warning if not met.

**Code:** [`sample_code/models/criterion_1.py`](../sample_code/models/criterion_1.py)

### Reverse Dependency Index via Database View

**Decision:** Compute reverse dependencies via SQL view (never stale, always accessible).

**Code:** [`sample_code/sql/view_v_reverse_dependencies.sql`](../sample_code/sql/view_v_reverse_dependencies.sql)

### Unified Activity Log (Audit Trail Integration)

**Decision:** Merge audit trail into activity log. All entity changes captured at Roadmap level.

**Code:** [`sample_code/models/activity_log_entry.py`](../sample_code/models/activity_log_entry.py)

### Token Estimation (Ticket Layer)

**Decision:** `estimated_tokens` lives on **Ticket (Layer 1)**, not TaskTicket. Any ticket level can have a direct estimate; otherwise `effective_tokens` aggregates from children.

**Rationale:**
- Any ticket level might need a direct override
- Aggregation logic is consistent across all ticket types
- Artifacts don't have tokens (they're outputs, not work)

**Code:** [`sample_code/models/ticket.py`](../sample_code/models/ticket.py)

**SQL View:** `v_effective_tokens` computes aggregated values via recursive CTE

### Auto-Progression with is_automatic Flag

**Decision:** Each CriterionTarget has `is_automatic` property. Parents auto-progress when children complete.

**Code:** [`sample_code/models/criterion_target_1.py`](../sample_code/models/criterion_target_1.py), [`sample_code/models/func_auto_progress.py`](../sample_code/models/func_auto_progress.py)

### GitCommit with File and Artifact Tracking

**Decision:** GitCommit tracks file changes and links to Artifacts, enabling provenance tracking and staleness detection.

**Features:**
- Extract file changes (added, modified, deleted) from `git diff-tree`
- Match file paths to registered Artifacts
- Track which commits created/modified each Artifact
- Detect stale documentation when source Artifacts change

**Code:** [`sample_code/models/git_commit.py`](../sample_code/models/git_commit.py), [`sample_code/models/func_process_commit.py`](../sample_code/models/func_process_commit.py)

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

**Hook integration:**
- Pre-commit: `verify_completion_claims()` blocks if criteria not met
- Post-commit: `process_commit()` links to artifacts, updates hashes, detects staleness

**Code:** [`sample_code/models/func_verify_completion_claims.py`](../sample_code/models/func_verify_completion_claims.py)

### Commit-Criterion-Artifact Validation

**Decision:** Allow divergence between criteria and commits, but make it visible through warnings.

**Rationale:**
- Criterion is source of truth for what task *requires*
- Commit is record of what *happened*
- Strict enforcement would block legitimate workflows (refactoring, pre-existing files)
- Warnings surface potential issues without blocking

**Validation levels:**
| Level | Blocks? | Example |
|-------|---------|---------|
| ERROR | ✅ Yes | Completion claim with unmet criteria |
| WARNING | ❌ No | Commit touches artifact not in criteria |
| INFO | ❌ No | Commit provides N of M required artifacts |

**Code:** [`sample_code/models/commit_artifact_validator.py`](../sample_code/models/commit_artifact_validator.py)

### DeliverableType on FileExistsTarget

**Decision:** Keep type classification for queryability and reporting.

**Code:** [`sample_code/models/enum_deliverable_type.py`](../sample_code/models/enum_deliverable_type.py)

### TestCoverageTarget (Separate from TestPassesTarget)

**Decision:** Create dedicated `TestCoverageTarget` for coverage metrics, separate from `TestPassesTarget`.

**Rationale:**
- Pass rate and coverage are independent concerns
- Coverage has unique semantics: line vs branch, per-file thresholds, exclusions
- Allows different blocking behavior (tests block IN_PROGRESS, coverage blocks COMPLETED)
- `coverage_threshold` removed from TestPassesTarget

**Code:** [`sample_code/models/test_coverage_target.py`](../sample_code/models/test_coverage_target.py)

### Enforceable Requirements (Ancestor Constraint)

**Decision:** Add `enforceable: bool` to Requirement. When true, descendants cannot OVERRIDE or SKIP.

**Rationale:**
- InheritMode (INHERIT, OVERRIDE, SKIP) is the **child's choice**
- `enforceable` is the **ancestor's constraint**
- Keeps concerns separated: child decides how to inherit, ancestor decides if override is allowed

**Use Cases:**
- Security requirements (auth, input validation)
- Compliance requirements (audit logging, data retention)
- Critical quality gates (type checking, test coverage)

**Code:** [`sample_code/models/requirement.py`](../sample_code/models/requirement.py), [`sample_code/models/func_resolve_requirements.py`](../sample_code/models/func_resolve_requirements.py)

### Pluggable Semantic Layer (Layer 3)

**Decision:** Make the semantic layer (Layer 3) interchangeable. Vibey's Roadmap → Track → Sprint → Task is the default, but can be replaced with Jira's Project → Epic/Sprint → Issue → Subtask or other providers.

**Rationale:**
- Layers 0-2 (Completable, Ticket, HierarchicalTicket) are universal
- Layer 3 defines domain-specific ticket types and fields
- External systems (Jira, GitHub, Linear) have their own hierarchies and field sets
- Status mapping allows external workflow states to map to canonical TicketStatus

**Key Components:**
- `SemanticLayer` abstract base class defines the interface
- `SemanticLayerRegistry` manages available layers and default selection
- Each layer defines: ticket_types, hierarchy, type-specific fields, status mappings
- External IDs (e.g., PROJ-123) tracked alongside internal ULIDs

**Available Layers:**
| Layer | Name | Hierarchy |
|-------|------|-----------|
| Vibey (default) | `vibey` | Roadmap → Track → Sprint → Task |
| Jira | `jira:PROJ` | Project → Epic/Sprint → Issue → Subtask |
| GitHub (future) | `github:org/repo` | Milestone → Issue |
| Linear (future) | `linear:TEAM` | Project → Cycle → Issue |

**Code:** [`sample_code/models/semantic_layer.py`](../sample_code/models/semantic_layer.py)

---

## Resolved Gaps

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

---

## New Fields Added to Model

Based on gap analysis:

**Code:** [`sample_code/models/ticket_1.py`](../sample_code/models/ticket_1.py)
