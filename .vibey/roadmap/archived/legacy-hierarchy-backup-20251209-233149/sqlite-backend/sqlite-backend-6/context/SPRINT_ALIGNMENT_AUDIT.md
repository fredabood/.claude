# Sprint Alignment Audit

**Date:** 2025-12-04
**Reference:** sqlite-backend-6/context/architecture/
**Tracks Reviewed:** sqlite-backend, git-integration, atlassian-integration

---

## Executive Summary

This audit compares the sprint plans across three tracks against the authoritative system design in `sqlite-backend-6/context/architecture/`. The audit identifies gaps, misalignments, and required updates to ensure all tracks reflect the unified ticket architecture.

### Overall Assessment

| Track | Sprints Reviewed | Alignment Status | Priority |
|-------|------------------|------------------|----------|
| **sqlite-backend** | 7-12 | 🟡 Partial | HIGH |
| **git-integration** | 5 | 🔴 Needs Major Update | HIGH |
| **atlassian-integration** | 1-4 | 🔴 Needs Major Update | CRITICAL |

---

## 1. sqlite-backend Track

### Sprint 6 (Current) ✅ AUTHORITATIVE
The system design in `sqlite-backend-6/context/architecture/` is the source of truth.

### Sprint 7 (Artifact System Architecture) 🟡 NEEDS UPDATE

**Current State:**
- References "Layer 0a: ARTIFACT" as separate from Completable
- References "ArtifactTarget criterion type"
- Layer diagram shows outdated architecture

**Required Alignment:**
| Issue | Current | Should Be |
|-------|---------|-----------|
| Layer position | "Layer 0a: ARTIFACT (NEW)" | Artifact extends Completable at Layer 0 |
| Criterion type | "ArtifactTarget criterion type" | **REMOVED** - use `CompletableTarget` for both Tickets and Artifacts |
| Status handling | Not specified | Artifact uses same `TicketStatus` enum, typically NOT_STARTED → IN_PROGRESS → COMPLETED |
| Implicit criterion | Not mentioned | FileExistsTarget is implicit on all Artifacts |

**Recommended Deliverables Update:**
```yaml
deliverables:
  - Artifact entity class (extends Completable at Layer 0)
  - ArtifactProvenance with provenance types
  - ArtifactType enum with subtypes
  - CompletableTarget works for Artifacts (no separate ArtifactTarget)
  - Implicit FileExistsTarget for artifact existence
  - artifacts rows in completables table (single-table inheritance)
  - v_orphan_artifacts and v_documentation_graph views
  - ImpactAnalyzer for documentation staleness
  - Comprehensive test suite for artifact system
```

### Sprint 8 (Serialization Migration) 🟡 NEEDS UPDATE

**Current State:**
- References "commits vs commits_local" field naming
- Mentions backward compatibility for existing YAML
- No mention of semantic layer header

**Required Alignment:**
| Issue | Current | Should Be |
|-------|---------|-----------|
| YAML format | Field renaming only | Must include `meta.semantic_layer` header |
| Directory structure | Not mentioned | Must reference flat structure: `tracks/`, `sprints/`, `tasks/`, `artifacts/` |
| Type-specific fields | Not mentioned | Must handle `type_fields` JSON for Layer 3 fields |
| External IDs | Not mentioned | Must handle `external_id` for Jira integration |

**Recommended Notes Update:**
```yaml
notes: |
  Sprint 8: Serialization Migration

  YAML FORMAT UPDATE:
  - All files get `meta:` header with `semantic_layer` and `schema_version`
  - Layer 3 fields stored in `type_fields` for extensibility
  - External IDs (e.g., Jira issue key) in `external_id` field

  DIRECTORY STRUCTURE:
  - Migrate to flat structure: tracks/, sprints/, tasks/, artifacts/
  - Files named by ULID: 01JD4EXAMPLE.yaml
  - Context in: context/tracks/<id>/, context/sprints/<id>/, etc.
```

### Sprint 9 (Operations Migration) 🟡 NEEDS UPDATE

**Current State:**
- References "standards_enforcement.py with inheritance"
- Mentions "Smart accessors" for aggregation

**Required Alignment:**
| Issue | Current | Should Be |
|-------|---------|-----------|
| Standards | "standards_enforcement.py" | Should be **Requirements** system with `enforceable` flag |
| Criteria | Not mentioned | Operations must use `can_transition_to()` for status checks |
| Commit tracking | "unified GitCommit" | Must integrate `process_commit()` and `verify_completion_claims()` |

**Recommended Deliverables Update:**
```yaml
deliverables:
  - Updated query.py with hierarchy-aware queries
  - Updated update.py with criteria-based status transitions
  - Updated requirements.py (renamed from standards_enforcement.py)
  - Updated commit_mapper.py with GitCommit file tracking
  - process_commit() integration for post-commit hooks
  - verify_completion_claims() integration for pre-commit hooks
  - Integration tests for all operations
  - Performance benchmarks
```

### Sprints 10-12 ✅ MOSTLY ALIGNED
Minor updates may be needed for terminology (standards → requirements, criteria-based completion).

---

## 2. git-integration Track

### Sprint 5 (Roadmap Integrity Protection) 🔴 NEEDS MAJOR UPDATE

**Current State:**
- Blocked waiting for SQLite backend
- 22 tasks with empty deliverables
- Plan file referenced but architecture outdated
- References "manifest system" which is superseded

**Required Alignment:**

The sprint design **must** reference the new architecture:

| Concept | Old Approach | New Approach (Architecture) |
|---------|--------------|---------------------------|
| Commit parsing | Custom parsing | `GitCommit.from_git()` with file tracking |
| Pre-commit validation | "Manifest validation" | `verify_completion_claims()` |
| Post-commit processing | "Update manifest" | `process_commit()` → links to artifacts, updates hashes |
| Ticket completion | "Manual status update" | Criteria-based via `can_transition_to()` |
| Artifact tracking | Not specified | `files_added/modified/deleted` → `creates/modifies/deletes_artifacts` |
| Staleness detection | Not specified | `documented_source_hash` comparison |

**Recommended Sprint Redesign:**

```yaml
sprint:
  id: git-integration-5
  name: Roadmap Integrity Protection (SQLite-Based)

  deliverables:
    # Pre-commit Hook
    - verify_completion_claims() function
    - Pre-commit hook using GitCommit.from_git()
    - Completion claim validation against criteria

    # Post-commit Hook
    - process_commit() function
    - Artifact linking (file paths → artifact IDs)
    - Content hash updates for modified artifacts
    - Documentation staleness detection

    # Validation
    - CommitArtifactValidator class integration
    - Warning vs blocking enforcement (per architecture)
    - Commit-Criterion-Artifact consistency checks

    # CLI Integration
    - vibey git hooks install (with new hooks)
    - vibey git validate-commit <sha>
    - vibey git show-provenance <artifact-id>

  notes: |
    ARCHITECTURE REFERENCE: sqlite-backend-6/context/architecture/

    KEY FILES:
    - 02-CLASS-MODEL.md: GitCommit Integration section
    - sample_code/models/git_commit.py
    - sample_code/models/func_process_commit.py
    - sample_code/models/func_verify_completion_claims.py
    - sample_code/models/commit_artifact_validator.py

    VALIDATION PHILOSOPHY:
    - Criteria is source of truth for what task REQUIRES
    - Commit is record of what HAPPENED
    - Allow divergence, make it visible via warnings
    - Only block on completion claim with unmet criteria
```

---

## 3. atlassian-integration Track

### ALL SPRINTS 🔴 NEED MAJOR UPDATE

The atlassian-integration track was designed **before** the pluggable semantic layer architecture. All four sprints must be updated to leverage the new architecture.

### Key Architecture Alignment Required

| Concept | Current Sprint Design | New Architecture |
|---------|----------------------|------------------|
| Data model | "Jira Project → Track mapping" | `JiraSemanticLayer` with `JiraProject`, `JiraEpic`, `JiraIssue`, `JiraSubtask` classes |
| Status mapping | "Jira Status → Task Status (configurable)" | `map_status_to_canonical()` / `map_status_from_canonical()` |
| Field mapping | "Custom field mappings" | `type_fields` JSON + `get_type_fields()` |
| ID tracking | "Preserve Jira issue key reference" | `external_id` field on Ticket |
| Type hierarchy | Manual mapping | `SemanticLayer.ticket_types` and `hierarchy` properties |
| Registration | Not specified | `SemanticLayerRegistry.register(JiraSemanticLayer(...))` |

### Sprint 1 (Jira Core Integration) - Required Updates

**Task 001 (Data Mapping) - CRITICAL UPDATE:**
```yaml
- id: atlassian-integration-1-task-001
  name: Design Jira to Vibey data model mapping
  description: |
    Implement JiraSemanticLayer per architecture:

    REFERENCE: sqlite-backend-6/context/architecture/02-CLASS-MODEL.md
    CODE: sample_code/models/semantic_layer.py

    DELIVERABLES:
    1. JiraSemanticLayer class implementing SemanticLayer interface
    2. JiraProjectConfig for loading project settings
    3. Jira ticket classes:
       - JiraProject (extends HierarchicalTicket)
       - JiraEpic (extends HierarchicalTicket)
       - JiraSprint (extends HierarchicalTicket)
       - JiraIssue (extends HierarchicalTicket)
       - JiraSubtask (extends HierarchicalTicket)
    4. Status mapping configuration (Jira workflow → TicketStatus)
    5. Custom field handling via type_fields
    6. External ID tracking (PROJ-123 → external_id)

    SEMANTIC LAYER INTERFACE:
    - name: "jira:PROJ"
    - ticket_types: ["project", "epic", "sprint", "issue", "subtask"]
    - hierarchy: {"issue": "sprint" or "epic", "subtask": "issue", ...}
    - get_ticket_class(type) → JiraIssue, etc.
    - map_status_to_canonical("In Progress") → TicketStatus.IN_PROGRESS
    - map_status_from_canonical(TicketStatus.COMPLETED) → "Done"
```

**Task 004-006 (Import) - Required Updates:**
- Must use `SemanticLayerRegistry.register()` when connecting to Jira
- Must set semantic layer in YAML files: `meta.semantic_layer: jira:PROJ`
- Must populate `external_id` with Jira issue key
- Must populate `type_fields` with Jira-specific fields

### Sprint 2 (Bidirectional Sync) - Required Updates

**Sync State Tracking:**
- Current: ".vibey/atlassian/sync-state.yaml"
- New: Can use `external_status` field for round-trip status preservation
- External changes detected via `external_id` + Jira API

**Status Mapping in Sync:**
```python
# On pull from Jira:
jira_status = issue['fields']['status']['name']  # "In Review"
canonical = jira_layer.map_status_to_canonical("issue", jira_status)
# → TicketStatus.IN_PROGRESS

# On push to Jira:
canonical = ticket.status  # TicketStatus.COMPLETED
jira_status = jira_layer.map_status_from_canonical("issue", canonical)
# → "Done"
```

### Sprint 3 (Confluence Integration) - Minimal Changes

Confluence integration is **separate** from the ticket semantic layer. However:
- Confluence pages could become `Artifact` entities with `artifact_type: DOCUMENTATION`
- Staleness detection via `documents_artifact_id` could track if source code changed

### Sprint 4 (Polish) - Required Updates

**Configuration Update:**
```yaml
# .vibey/config/semantic.yaml (NEW FILE)
semantic_layer:
  provider: jira

  jira:
    site: company.atlassian.net
    project_key: PROJ

    type_mapping:
      project: roadmap
      epic: tracks
      sprint: sprints
      issue: tasks
      subtask: tasks

    status_map:
      "To Do": not_started
      "In Progress": in_progress
      "In Review": in_progress
      "Done": completed
      "Released": deployed
```

---

## 4. Dependency Graph Updates

### Current Dependencies (Correct)
```
sqlite-backend-6 (Unified Architecture) ←── AUTHORITATIVE
       ↓
sqlite-backend-7 (Artifacts)
       ↓
sqlite-backend-8 (Serialization)
       ↓
sqlite-backend-9 (Operations)
       ↓
sqlite-backend-10 (Interface)
       ↓
sqlite-backend-11 (Validation)
       ↓
sqlite-backend-12 (Production)
```

### Missing Dependencies (Should Add)
```
sqlite-backend-6 ──────────────────────────────────────┐
       ↓                                               ↓
git-integration-5 (must reference architecture)    atlassian-integration-1
                                                       ↓
                                                   atlassian-integration-2
                                                       ↓
                                                   atlassian-integration-3
                                                       ↓
                                                   atlassian-integration-4
```

**Recommendation:** Add explicit dependency:
```yaml
# In atlassian-integration track.yaml
depends_on:
  - sqlite-backend-6  # Requires unified ticket architecture
```

---

## 5. Recommended Actions

### Immediate (Before Sprint 7 Starts)

1. **Update sqlite-backend-7 sprint.yaml:**
   - Change "Layer 0a" to "Layer 0 (extends Completable)"
   - Remove "ArtifactTarget" → use "CompletableTarget"
   - Add implicit FileExistsTarget deliverable

2. **Update sqlite-backend-8 sprint.yaml:**
   - Add semantic layer header requirement
   - Add directory structure migration
   - Add type_fields handling

3. **Update sqlite-backend-9 sprint.yaml:**
   - Rename standards_enforcement → requirements
   - Add criteria-based completion references

### Before git-integration-5 Unblocks

4. **Redesign git-integration-5:**
   - Reference architecture documents
   - Use GitCommit class with file tracking
   - Implement verify_completion_claims() and process_commit()
   - Reference CommitArtifactValidator

### Before atlassian-integration Starts

5. **Add sqlite-backend-6 as dependency:**
   - Add to atlassian-integration track.yaml

6. **Redesign atlassian-integration-1 Task 001:**
   - Implement JiraSemanticLayer
   - Reference semantic_layer.py sample code

7. **Update all atlassian-integration sprints:**
   - Add semantic layer configuration references
   - Update status mapping to use SemanticLayer interface
   - Add external_id tracking

---

## 6. Files to Reference

All sprints should reference these architecture documents:

| Document | Key Content |
|----------|-------------|
| `02-CLASS-MODEL.md` | Layer architecture, class relationships, GitCommit integration |
| `03-ARTIFACT-SYSTEM.md` | Artifact as Completable, implicit FileExistsTarget |
| `05-DATABASE-SCHEMA.md` | completables table, type_fields column |
| `06-SERIALIZATION.md` | YAML format, migration strategy |
| `08-REFERENCE.md` | Design decisions, gap resolutions |

Sample code to reference:

| File | Purpose |
|------|---------|
| `semantic_layer.py` | SemanticLayer interface, VibeySemanticLayer, JiraSemanticLayer |
| `git_commit.py` | GitCommit with file tracking |
| `func_process_commit.py` | Post-commit processing |
| `func_verify_completion_claims.py` | Pre-commit validation |
| `commit_artifact_validator.py` | Commit-Criterion-Artifact validation |

---

**Audit Complete**

Next Steps:
1. Review this audit with stakeholders
2. Create tasks to update each sprint plan
3. Update track dependencies
4. Ensure all developers reference the architecture before implementation
