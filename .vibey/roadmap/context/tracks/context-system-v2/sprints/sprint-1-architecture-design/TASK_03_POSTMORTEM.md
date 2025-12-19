# Task 3 Post-Mortem: Define Context Directory Structure

**Task ID:** 01KCMMK1MSFBZAM880C9K3BWPB
**Completed:** 2025-12-19
**Duration:** ~45 minutes
**Outcome:** Success

---

## Summary

Created comprehensive directory structure specification for Context System V2, including:
- Complete directory layout for plans, runtime, and post-mortem contexts
- Full YAML schemas for all three context types with required/optional field documentation
- Python path utility class design (ContextPaths)
- Migration strategy for existing context/ content
- Integration notes with Unified Ticket Architecture
- Validation rules and complete file examples

---

## Deliverables

| Deliverable | Location | Status |
|------------|----------|--------|
| Directory Structure Spec | `DIRECTORY_STRUCTURE_SPEC.md` | Complete |
| Plan Context Schema | Section 2 of spec | Complete |
| Runtime Context Schema | Section 3 of spec | Complete |
| Post-Mortem Schema | Section 4 of spec | Complete |
| Path Utility Design | Section 5 of spec | Complete |
| Migration Notes | Section 6 of spec | Complete |

---

## Key Decisions

### 1. Directory per Ticket for Plans
**Decision:** Plans use `plans/{ticket_id}/` directories rather than single files.
**Rationale:** Plans can have multiple markdown artifacts (design docs, implementation plans, API designs). A directory structure allows extensibility while keeping the core `plan.yaml` small and focused on metadata.

### 2. Single YAML for Runtime and Post-Mortem
**Decision:** Runtime uses `runtime/{ticket_id}.yaml` and post-mortems use `post-mortems/{ticket_id}.yaml` as single files.
**Rationale:** These contexts are purely structured data without the need for separate markdown artifacts. Single files are simpler to manage and query.

### 3. Integration with UTA Relationship Entities
**Decision:** `known_files` maps to `TicketArtifactAssociation` and `commit_links` maps to `TicketCommitLink`.
**Rationale:** Leverages existing Unified Ticket Architecture rather than creating standalone models. Ensures consistency across the system.

### 4. Source Tracking for File Associations
**Decision:** Track HOW files become associated with tickets via `source` field.
**Rationale:** Aligns with UTA's `AssociationSource` enum. Enables debugging and understanding of file provenance.

### 5. Signal-Based Commit Linking
**Decision:** Commit links include `signals` object with `file_overlap`, `message_ref`, and `manual` sub-objects.
**Rationale:** Directly maps to Sprint 0 design decisions for triangle validation. Preserves all linking evidence.

---

## Lessons Learned

1. **Read design decisions first** - Sprint 0's DESIGN_DECISIONS.md provided critical context for schema design, especially around UTA integration and the triangle relationship model.

2. **Existing directory structure matters** - The current `context/` directory has track-specific and sprint-specific subdirectories that need migration consideration.

3. **Schema versioning is essential** - Including `version: "1.0"` in all schemas enables future migrations without breaking existing data.

---

## Follow-Up Items

| Item | Priority | Notes |
|------|----------|-------|
| Implement ContextPaths class | High | Python class from Section 5 |
| Create context CLI commands | High | init, migrate, validate commands |
| Add MCP tools for context operations | High | plan_create, runtime_start, etc. |
| Migrate existing context content | Medium | Follow migration strategy in Section 6 |
| Add integration tests | Medium | Validate schemas against real data |

---

## Files Changed

| File | Change Type | Lines |
|------|-------------|-------|
| `DIRECTORY_STRUCTURE_SPEC.md` | Added | ~950 |
| `TASK_03_POSTMORTEM.md` | Added | ~100 |

---

## Acceptance Criteria Status

- [x] Plans directory structure defined
- [x] Runtime directory structure defined
- [x] Post-mortems directory structure defined
- [x] YAML schemas complete for all three types
- [x] Path utilities designed
- [x] Artifact indexing in plan.yaml specified

All acceptance criteria from the Sprint Plan have been met.

---

## References

- [DIRECTORY_STRUCTURE_SPEC.md](./DIRECTORY_STRUCTURE_SPEC.md) - Main deliverable
- [SPRINT_PLAN.md](./SPRINT_PLAN.md) - Task definition
- [DESIGN_DECISIONS.md](../sprint-0-planning-design-review/DESIGN_DECISIONS.md) - Design foundations
