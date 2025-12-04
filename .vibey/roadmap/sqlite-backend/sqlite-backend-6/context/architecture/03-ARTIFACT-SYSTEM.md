# Artifact System

## Design Rationale

**Problem:** In the criteria-centric model, artifacts only exist inside `Criterion.target`. This means:
- Pre-existing files (README.md) can't be tracked without a ticket
- Generated documentation isn't linked to what it documents
- Framework components (agents, workflows) exist outside the graph
- Impact analysis requires walking all criteria to find affected files

**Solution:** Make `Artifact` a first-class entity that **extends Completable** (sibling to `Ticket`). Both share criteria-based completion semantics.

```
UNIFIED MODEL (Completable-Centric):

                    Completable
                    ├── id, name, status
                    ├── criteria: List[Criterion]
                    └── can_transition_to()
                           │
           ┌───────────────┴───────────────┐
           ▼                               ▼
        Ticket                          Artifact
    (work item)                     (file entity)
    - started_at                    - paths[]
    - completed_at                  - content_hash
    - assigned_agents               - artifact_type
    - commits                       - provenance
                                    - documents_artifact_id

Both referenced via: Criterion → CompletableTarget → completable_id
```

### Key Insight

Artifacts can be **IN_PROGRESS** - for example, when:
- File exists (implicit FileExistsTarget passes)
- But tests are failing (TestPassesTarget not met)
- Or linting errors exist (ThresholdTarget not met)

This enables the same NOT_STARTED → IN_PROGRESS → COMPLETED progression as Tickets.

---

## Artifact Entity

**Code:** [`sample_code/models/artifact.py`](../sample_code/models/artifact.py)

### Key Fields

| Field | Type | Purpose |
|-------|------|---------|
| `id` | str (ULID) | Immutable identity |
| `paths` | List[str] | File paths this artifact represents |
| `content_hash` | str | SHA256 for staleness detection |
| `artifact_type` | ArtifactType | Classification (CODE, DOCUMENTATION, etc.) |
| `provenance` | ArtifactProvenance | How this artifact came to exist |
| `documents_artifact_id` | str? | What this artifact documents |
| `depends_on_artifact_ids` | List[str] | Artifacts this depends on |

### Key Properties

| Property | Returns | Purpose |
|----------|---------|---------|
| `is_orphan` | bool | Not referenced by any criterion |
| `is_stale` | bool | Content hash doesn't match file |
| `is_documentation` | bool | Has `documents_artifact_id` set |
| `referencing_criteria` | List[str] | Which criteria reference this |

---

## Artifact Provenance

**Code:** [`sample_code/models/artifact_provenance.py`](../sample_code/models/artifact_provenance.py)

| Provenance Type | Description | Example |
|-----------------|-------------|---------|
| `TICKET_CREATED` | Created by completing a task | New module from implementation task |
| `PRE_EXISTING` | Existed before roadmap tracking | README.md, existing code |
| `GENERATED` | Auto-generated from sources | API docs from docstrings |
| `EXTERNAL` | From external source | Third-party library |
| `FRAMEWORK` | Vibey framework component | Agent definitions, workflows |

---

## Artifact Type Classification

**Code:** [`sample_code/models/enum_artifact_type.py`](../sample_code/models/enum_artifact_type.py)

| Type | Subtypes |
|------|----------|
| `CODE` | module, class, function, test |
| `DOCUMENTATION` | readme, api_doc, guide, changelog |
| `CONFIGURATION` | yaml, json, toml, env |
| `DATA` | schema, migration, fixture |
| `ASSET` | image, template, static |

---

## Referencing Artifacts (CompletableTarget)

Since Artifact extends Completable, reference it via `CompletableTarget` (same as Tickets):

**Code:** [`sample_code/models/completable_target.py`](../sample_code/models/completable_target.py)

| Field | Purpose |
|-------|---------|
| `completable_id` | ULID of referenced Ticket OR Artifact |
| `blocks_transition_to` | Which status this blocks on parent |

### ArtifactTarget REMOVED

The separate `ArtifactTarget` is no longer needed. Since Artifact is a Completable:
- Use `CompletableTarget` to reference artifacts
- The artifact's own criteria determine its completion
- Parent's `can_transition_to()` checks all CompletableTargets uniformly

### Implicit FileExistsTarget

Every Artifact has an **implicit criterion** that the file must exist:

```python
# Implicit criterion added during Artifact initialization
Criterion(
    name=f"File exists: {artifact.paths[0]}",
    blocks_transition_to=TicketStatus.IN_PROGRESS,
    target=FileExistsTarget(paths=artifact.paths),
    required=True
)
```

This means:
- `NOT_STARTED`: File doesn't exist
- `IN_PROGRESS`: File exists, other criteria not met
- `COMPLETED`: File exists AND all criteria pass

---

## Impact Analysis

The artifact system enables comprehensive impact analysis when code changes:

**Code:** [`sample_code/models/impact_analyzer.py`](../sample_code/models/impact_analyzer.py)

### Capabilities

| Query | Method |
|-------|--------|
| What tickets depend on this file? | `get_affected_tickets(file_path)` |
| What documentation needs updating? | `get_stale_documentation()` |
| What artifacts have no references? | `get_orphan_artifacts()` |
| What would break if I delete this? | `analyze_deletion_impact(artifact_id)` |

---

## Database Schema

**Code:** [`sample_code/sql/table_artifacts.sql`](../sample_code/sql/table_artifacts.sql)

### Key Views

| View | Purpose |
|------|---------|
| `v_orphan_artifacts` | Artifacts not referenced by any criterion |
| `v_documentation_graph` | What documents what |
| `v_stale_documentation` | Docs needing update |
| `v_ticket_artifacts` | All artifacts by ticket |

---

## Benefits Summary

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

## YAML Format

**Code:** [`sample_code/yaml/example_task_1.yaml`](../sample_code/yaml/example_task_1.yaml)
