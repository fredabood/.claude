# Context System V2 - Design Decisions

**Sprint:** 0 - Planning & Design Review
**Date:** 2025-12-17 (Updated: 2025-12-18)
**Status:** Approved

---

## Integration with Unified Ticket Architecture

**Critical Decision:** Context System V2 integrates with the existing Unified Ticket Architecture rather than creating standalone entities.

This means:
- **No standalone `CommitLink`** → Use `TicketCommitLink` relationship entity
- **No standalone `KnownFile`** → Use `TicketArtifactAssociation` relationship entity
- **Leverage existing `Artifact`** entity with provenance tracking
- **Leverage existing `GitCommit`** entity
- **Leverage existing `Completable`/`Criterion`** system

Reference: `docs/roadmap/sqlite-backend/sqlite-backend-6/UNIFIED_TICKET_ARCHITECTURE.md`

---

## Part 1: Core Design Decisions

### 1. Storage Structure

**Decision:** Keep `context/` directory, add subdirectories

```
.vibey/roadmap/context/
├── plans/           # Pre-work planning artifacts
├── runtime/         # Active session state
└── post-mortems/    # Completion summaries
```

**Rationale:** Cleaner than renaming; maintains existing context location.

---

### 2. Hybrid YAML + Markdown Approach

**Decision:** Use YAML for structured metadata, reference longer markdown files

```yaml
# context/plans/01TASK123.yaml
plan_context:
  goals: [...]
  approach: "..."

  # References to Artifact entities (not raw files)
  artifact_refs:
    - artifact_id: 01ART_ARCH_ANALYSIS
      purpose: "Deep dive on existing auth system"
    - artifact_id: 01ART_IMPL_OPTIONS
      purpose: "Comparison of 3 approaches with trade-offs"
```

**Rationale:**
- YAML always loaded (small, structured)
- AI sees what artifacts exist and their purpose
- AI chooses which to read based on current need
- Large analyses preserved without forced token cost
- Artifacts tracked as first-class entities with provenance

---

### 3. Commit Message Format

**Decision:** Two distinct markers for different purposes

```
feat(auth): Add JWT validation

Task: 01TASK_A
Task: 01TASK_B

Completes: 01TASK_A

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

| Marker | Purpose | Creates |
|--------|---------|---------|
| `Task:` | Associates commit with task (work was done) | `TicketCommitLink` with `reference_type=TASK_REFERENCE` |
| `Completes:` | Claims task completion (triggers criteria check) | `TicketCommitLink` with `reference_type=COMPLETION_CLAIM` |

**Rationale:** A commit can reference a task without claiming completion. These are different actions.

---

### 4. Three Relationship Entities (Triangle Model)

**Decision:** Define relationships between existing entities, not standalone models

```
                         ┌─────────────┐
                         │   Ticket    │
                         └─────────────┘
                        /               \
                       /                 \
          TicketCommitLink          TicketArtifactAssociation
                     /                     \
                    /                       \
        ┌─────────────┐               ┌─────────────┐
        │  GitCommit  │───────────────│  Artifact   │
        └─────────────┘               └─────────────┘
                    CommitArtifactChange
```

#### 4.1 TicketCommitLink
**Ticket ↔ GitCommit** — "This commit references this ticket"

```python
class TicketCommitLink(BaseModel):
    ticket_id: str
    commit_sha: str
    reference_type: ReferenceType  # TASK_REFERENCE | COMPLETION_CLAIM
    signals: LinkSignals           # file_overlap, message_ref, manual
    aggregate_confidence: float
    linked_at: datetime
    link_source: str               # pre_commit_hook | post_commit | manual
```

#### 4.2 TicketArtifactAssociation
**Ticket ↔ Artifact** — "This ticket is associated with this artifact"

```python
class TicketArtifactAssociation(BaseModel):
    ticket_id: str
    artifact_id: str
    association_source: AssociationSource  # plan_reference | runtime_tracking | commit_bootstrap | manual | criterion_target
    added_at: datetime
    added_by: Optional[str] = None
```

#### 4.3 CommitArtifactChange
**GitCommit ↔ Artifact** — "This commit changed this artifact"

```python
class CommitArtifactChange(BaseModel):
    commit_sha: str
    artifact_id: str
    change_type: ChangeType  # ADDED | MODIFIED | DELETED | RENAMED
    previous_path: Optional[str] = None  # For renames
    lines_added: Optional[int] = None
    lines_removed: Optional[int] = None
    recorded_at: datetime
```

**Rationale:**
- Leverages existing Ticket, GitCommit, and Artifact entities
- Relationships have their own metadata (how established, when, confidence)
- Triangle enables powerful queries and validation
- No duplication of entity data

---

### 5. Link Detection Signals

**Decision:** Three signals for detecting commit-ticket relationships (NO timestamp)

| Signal | Description | Confidence |
|--------|-------------|------------|
| **File overlap** | Commit artifacts matched against ticket's artifact associations | `len(overlap) / len(commit_artifacts)` |
| **Message reference** | Task ID parsed from `Task:` or `Completes:` line | 1.0 if found |
| **Manual link** | Explicit user linking via CLI | 1.0 |

```python
class LinkSignals(BaseModel):
    file_overlap: Optional[FileOverlapSignal] = None
    message_ref: Optional[MessageRefSignal] = None
    manual: Optional[ManualSignal] = None

class FileOverlapSignal(BaseModel):
    matched: bool
    overlapping_artifact_ids: List[str]
    confidence: float

class MessageRefSignal(BaseModel):
    matched: bool
    ticket_ids: List[str]
    reference_type: ReferenceType
    confidence: float = 1.0

class ManualSignal(BaseModel):
    matched: bool
    linked_by: Optional[str] = None
    linked_at: Optional[datetime] = None
    confidence: float = 1.0
```

**Rationale:**
- Timestamp was source of parallel task ambiguity
- File-based linking is deterministic and semantically meaningful
- Pre-commit hook provides real-time validation

---

### 6. Artifact Association Sources

**Decision:** Track HOW artifacts become associated with tickets

| Source | When | Mechanism |
|--------|------|-----------|
| `plan_reference` | Before work | Plan context references artifact |
| `runtime_tracking` | During work | AI logs files via MCP |
| `commit_bootstrap` | First commit | Message ref + staged files establishes association |
| `manual` | Anytime | CLI command `vibey task add-artifact` |
| `criterion_target` | Criterion defined | FileExistsTarget references artifact |

**Rationale:** Understanding provenance helps with validation and debugging.

---

### 7. File/Artifact Ownership Model

**Decision:** Artifacts can be associated with multiple tickets

| Scenario | Valid? |
|----------|--------|
| Artifact in multiple tickets | ✓ |
| Artifact in multiple tickets, same commit | ✓ (commit refs both) |
| Common artifact (utils.py) in many tickets | ✓ |

**Rationale:** Real work isn't cleanly partitioned. Validation is about consistency, not exclusivity.

---

### 8. Unified Pre-Commit Hook with Triangle Validation

**Decision:** Single hook that validates across all three relationship edges

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      UNIFIED PRE-COMMIT HOOK                             │
├─────────────────────────────────────────────────────────────────────────┤
│  PHASE 1: Collect Data                                                   │
│    • Parse commit message → Task: and Completes: references              │
│    • Get staged files → resolve to Artifact IDs (or create new)          │
│    • Build pending CommitArtifactChange records                          │
├─────────────────────────────────────────────────────────────────────────┤
│  PHASE 2: Triangle Validation                                            │
│    For each Task: ticket_id:                                             │
│      A = Artifacts in staged files (CommitArtifactChange)                │
│      B = Artifacts associated with ticket (TicketArtifactAssociation)    │
│                                                                          │
│      Check 1: A ∩ B — Files in both (expected, good)                     │
│      Check 2: A - B — Staged NOT in ticket associations                  │
│               → Prompt: "Add to ticket associations?"                    │
│      Check 3: B - A — Ticket associations NOT in staged                  │
│               → Info only (not all files change each time)               │
├─────────────────────────────────────────────────────────────────────────┤
│  PHASE 3: Completion Verification                                        │
│    For each Completes: ticket_id:                                        │
│      • ticket.can_transition_to(COMPLETED) must return True              │
│      • Block commit if criteria not met                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  PHASE 4: Persist Relationships                                          │
│    • Create TicketCommitLink for each Task:/Completes: reference         │
│    • Create CommitArtifactChange for each staged file                    │
│    • Update TicketArtifactAssociation if user approved additions         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Rationale:**
- Parse message once, not twice
- Staged files analyzed once
- Consistent user experience
- Single configuration location
- Phase 2 can inform Phase 4 (auto-associate staged files with referenced tickets)

---

### 9. Pre-Commit Hook Configuration

**Decision:** Configurable enforcement levels

```yaml
# .vibey/config/git_hooks.yaml
pre_commit:
  enabled: true

  # Phase 2: File/artifact consistency
  artifact_consistency:
    mode: prompt  # off | warn | prompt | strict
    on_mismatch:
      staged_not_in_associations: prompt
      associations_not_in_staged: ignore
      no_task_ref: warn

  # Phase 3: Completion verification
  completion_verification:
    mode: strict  # off | warn | strict
    block_on_unmet_criteria: true
```

| Mode | Behavior |
|------|----------|
| **off** | Check skipped |
| **warn** | Show issues, commit proceeds |
| **prompt** | Show issues, ask for resolution |
| **strict** | Block commit until resolved |

**Rationale:** Different teams/users have different tolerance for friction. Completion verification should generally be strict to maintain integrity.

---

### 10. Commit Message Template

**Decision:** Provide templated commit message format

```
# <type>(<scope>): <subject>
#
# Task: <TASK_ID>
# Completes: <TASK_ID>  # Only if task is actually complete
#
# <body>
```

**Setup:** `vibey git setup-template`

**Multi-task format:**
- `Task: 01TASK_A, 01TASK_B` (multiple on one line)
- Or separate lines for each

**Rationale:** Increases compliance with expected message structure through guided format.

---

### 11. Bidirectional Validation

**Decision:** Pre-commit hook validates consistency in both directions

When commit artifacts ≠ ticket associations for referenced task:
- Don't assume which source is authoritative
- Flag the discrepancy
- Present resolution options to user

**Resolution Options:**
1. Update Associations - Add artifacts to ticket
2. Update Message - Change task reference
3. Add Reference - Include additional task
4. Proceed - Override, commit as-is

**Rationale:** We can't know if associations are incomplete or message ref is wrong. User decides.

---

### 12. Confidence Thresholds

**Decision:** Configurable, not hardcoded

- All link signals tracked with individual confidence scores
- Aggregate confidence calculated
- Filtering/thresholds applied at query time, not storage time
- All relationship data preserved for later analysis

**Rationale:** Let system collect data, decide filtering thresholds based on actual usage patterns.

---

## Part 2: Triangle Query Examples

With all three relationships, powerful queries become possible:

| Query | Method |
|-------|--------|
| What commits touched this ticket? | `TicketCommitLink WHERE ticket_id = X` |
| What artifacts are associated with this ticket? | `TicketArtifactAssociation WHERE ticket_id = X` |
| What artifacts did this commit change? | `CommitArtifactChange WHERE commit_sha = X` |
| What tickets were affected by changes to this artifact? | `Artifact → TicketArtifactAssociation → Ticket` |
| Did commit X change artifacts outside its referenced tickets? | `CommitArtifactChange ⊄ (TicketCommitLink → TicketArtifactAssociation)` |
| Full history of this artifact? | `CommitArtifactChange WHERE artifact_id = X ORDER BY recorded_at` |
| Validate commit integrity | All three edges must be consistent |

---

## Part 3: Integration Points

### With Existing Criterion System

`FileExistsTarget` can reference artifacts:

```python
class FileExistsTarget(CriterionTarget):
    # Reference artifacts by ID (preferred)
    artifact_ids: List[str] = Field(default_factory=list)

    # Or raw paths (backwards compatible)
    paths: List[str] = Field(default_factory=list)

    def get_all_paths(self, artifact_registry) -> List[str]:
        artifact_paths = []
        for art_id in self.artifact_ids:
            artifact = artifact_registry.get(art_id)
            if artifact:
                artifact_paths.extend(artifact.paths)
        return artifact_paths + self.paths
```

### With Existing GitCommit

Extend existing model:

```python
class GitCommit(BaseModel):
    sha: str
    message: str
    date: datetime
    author: str
    platform: str

    # Existing
    completes_tickets: List[str]  # Parsed from "Completes:" lines

    # New (parsed from "Task:" lines)
    references_tickets: List[str] = Field(default_factory=list)
```

### With Existing Artifact Provenance

When artifacts are created via tickets:

```python
class ArtifactProvenance(BaseModel):
    provenance_type: ProvenanceType  # TICKET_CREATED | PRE_EXISTING | etc.
    created_by_ticket_id: Optional[str] = None
    # ... existing fields
```

This creates an implicit `TicketArtifactAssociation` with `source=criterion_target`.

---

## Next Steps

1. ~~Update Sprint 1 & 2 plans to reflect integrated design~~
2. Add relationship entity models to `vibey/roadmap/models/`
3. Add relationship tables to SQLite schema
4. Update pre-commit hook to use triangle validation
5. Add MCP tools for artifact association management
6. Update CLI commands to work with relationship entities

---

## Approval

- [x] Three-phase context model approved
- [x] Storage structure approved (context/plans, context/runtime, context/post-mortems)
- [x] Hybrid YAML + Markdown approach approved
- [x] **Integration with Unified Ticket Architecture approved**
- [x] **Triangle relationship model approved (TicketCommitLink, TicketArtifactAssociation, CommitArtifactChange)**
- [x] Git linking approach approved (file overlap + message ref + manual)
- [x] Bidirectional validation approved
- [x] **Unified pre-commit hook with triangle validation approved**
- [x] Commit message template approved (Task: + Completes:)
