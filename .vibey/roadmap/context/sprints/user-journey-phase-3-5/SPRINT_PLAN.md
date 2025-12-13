# Sprint 3.5: Pre-Phase 4 Documentation Sync

## Sprint Overview

**Goal:** Update Phase 1 audit and Phase 2 documentation to include all artifacts created in Phases 2 and 3 before proceeding with gap analysis.

**Theme:** Documentation Currency & Completeness

**Estimated Duration:** 2-3 sessions

**Prerequisites:** Phases 1, 2, and 3 completed

---

## Background

Phases 2 and 3 created significant new artifacts that are not reflected in the Phase 1 audit or Phase 2 documentation:

**Phase 2 Artifacts (~20 files):**
- CLI Reference Guide (`docs/reference/CLI_REFERENCE.md`)
- MCP Reference Guide (`docs/reference/MCP_REFERENCE.md`)
- User Personas (`docs/personas/USER_PERSONAS.md`)
- Journey Maps (`docs/journeys/JOURNEY_*.md` - 5 files)
- Coverage Matrix (`docs/journeys/COVERAGE_MATRIX.md`)
- Walkthroughs (`docs/walkthroughs/WALKTHROUGH_*.md` - 6 files)
- Development Setup (`docs/development/SETUP.md`)
- Coding Standards (`docs/development/CODING_STANDARDS.md`)
- ADRs (`docs/architecture/adr/*.md` - 6 files)

**Phase 3 Artifacts (~10 files):**
- Session Model (`vibey/roadmap/models/session.py` - 469 lines)
- Session Manager (`vibey/operations/roadmap/session_manager.py` - 803 lines)
- Session Reconstruction (`vibey/operations/roadmap/session_reconstruction.py` - 461 lines)
- Audit Trail (`vibey/operations/roadmap/audit_trail.py` - 625 lines)
- JSONL Activity Log (`vibey/operations/roadmap/jsonl_activity_log.py` - 952 lines)

This sprint ensures Phase 4's gap analysis operates on current, complete data.

---

## Tasks

### Task 1: Update Phase 1 File Inventory with Phase 2-3 artifacts

**Objective:** Add all new files from Phases 2 and 3 to the Phase 1.1 file inventory.

**Deliverables:**
- Updated `FILE_INVENTORY.yaml` with ~30 new files
- Updated file counts and categorization

**Approach:**
1. Locate Phase 1.1 file inventory deliverable
2. Run file discovery to identify all files created after Phase 1
3. Categorize new files (docs, code, tests, config)
4. Add to inventory with creation dates and line counts
5. Update summary statistics

**Acceptance Criteria:**
- [ ] All Phase 2 documentation files added
- [ ] All Phase 3 code files added
- [ ] File categories accurate
- [ ] Line counts current
- [ ] Summary statistics updated

---

### Task 2: Update CLI Reference Guide with audit commands

**Objective:** Document the audit commands added in Phase 3.

**Deliverables:**
- Updated `docs/reference/CLI_REFERENCE.md`

**Commands to Document:**
```bash
vibey roadmap audit log [--limit N]
# Show recent audit trail entries

vibey roadmap audit show <object-id>
# Show audit history for specific object

vibey roadmap audit suspicious
# Detect suspicious changes in audit trail

vibey roadmap audit report [--object-id ID] [--start-date DATE] [--end-date DATE]
# Generate detailed audit report
```

**For Each Command, Include:**
- Synopsis and description
- All options with defaults
- Example usage with sample output
- Related commands cross-reference

**Acceptance Criteria:**
- [ ] All 4 audit commands documented
- [ ] Examples show realistic output
- [ ] Options fully described
- [ ] Cross-references to related commands

---

### Task 3: Update MCP Reference Guide with audit tools

**Objective:** Document any audit/session MCP tools exposed via the MCP server.

**Deliverables:**
- Updated `docs/reference/MCP_REFERENCE.md`

**Approach:**
1. Review `vibey/mcp/server.py` for audit-related tools
2. Document any exposed audit query tools
3. Document any session management tools
4. Include request/response examples

**Acceptance Criteria:**
- [ ] All audit MCP tools documented (if any)
- [ ] All session MCP tools documented (if any)
- [ ] Request/response schemas included
- [ ] Examples provided

---

### Task 4: Update User Journeys with audit workflows

**Objective:** Add audit and transparency workflows to relevant user journeys.

**Deliverables:**
- Updated journey files in `docs/journeys/`

**Journeys to Update:**

| Journey | New Sections |
|---------|--------------|
| Active Developer | "Review session history", "Check audit trail" |
| Project Lead | "Generate audit reports", "Monitor data integrity" |
| Contributor | "Understanding audit logging" |

**For Each New Section:**
- When to use this workflow
- Step-by-step instructions
- Expected outcomes
- CLI commands involved

**Acceptance Criteria:**
- [ ] Active Developer journey updated
- [ ] Project Lead journey updated
- [ ] Contributor journey updated
- [ ] All new sections follow existing format

---

### Task 5: Update Walkthroughs with audit sections

**Objective:** Add practical audit examples to relevant walkthroughs.

**Deliverables:**
- Updated walkthrough files in `docs/walkthroughs/`

**Walkthroughs to Update:**

| Walkthrough | New Content |
|-------------|-------------|
| Active Developer | "Reviewing your work history" section |
| Project Lead | "Generating compliance reports" section |
| Contributor | "How your changes are tracked" section |

**For Each Section:**
- Concrete scenario
- Step-by-step commands
- Expected output (can be simplified)
- Common questions/troubleshooting

**Acceptance Criteria:**
- [ ] Audit sections added to 3 walkthroughs
- [ ] Commands tested and working
- [ ] Output examples accurate
- [ ] Follows existing walkthrough style

---

### Task 6: Update Coverage Matrix with new features

**Objective:** Ensure coverage matrix reflects all Phase 3 features.

**Deliverables:**
- Updated `docs/journeys/COVERAGE_MATRIX.md`

**New Features to Map:**

| Feature | CLI Commands | Relevant Journeys |
|---------|--------------|-------------------|
| Audit Trail | audit log, audit show, audit suspicious, audit report | Active Developer, Project Lead |
| Session Management | (if any CLI exposed) | Active Developer |
| Activity Logging | (internal, but affects audit) | Project Lead, Contributor |

**Approach:**
1. Review current coverage matrix structure
2. Add new CLI commands to command inventory
3. Map commands to user journeys
4. Identify any coverage gaps
5. Update summary statistics

**Acceptance Criteria:**
- [ ] All audit commands in matrix
- [ ] Commands mapped to journeys
- [ ] No unmapped commands
- [ ] Coverage statistics updated

---

## Task Dependencies

```
Task 1 (File Inventory)
    ↓
Tasks 2-6 can run in parallel after Task 1
```

Task 1 should be completed first to establish the complete file inventory that other tasks may reference.

---

## Success Criteria

- [ ] Phase 1 file inventory includes all Phase 2-3 files
- [ ] CLI Reference documents all audit commands
- [ ] MCP Reference documents any audit tools
- [ ] User journeys include audit workflows
- [ ] Walkthroughs include audit examples
- [ ] Coverage matrix maps all new features

---

## File Changes Summary

**Files to Update:**
- Phase 1.1 file inventory deliverable
- `docs/reference/CLI_REFERENCE.md`
- `docs/reference/MCP_REFERENCE.md`
- `docs/journeys/JOURNEY_ACTIVE_DEVELOPER.md`
- `docs/journeys/JOURNEY_PROJECT_LEAD.md`
- `docs/journeys/JOURNEY_CONTRIBUTOR.md`
- `docs/walkthroughs/WALKTHROUGH_ACTIVE_DEVELOPER.md`
- `docs/walkthroughs/WALKTHROUGH_PROJECT_LEAD.md`
- `docs/walkthroughs/WALKTHROUGH_CONTRIBUTOR.md`
- `docs/journeys/COVERAGE_MATRIX.md`

---

## Notes

This sprint is a "documentation refresh checkpoint" - a pattern we're introducing to keep documentation current as implementation progresses. Future phases will have similar checkpoints after significant implementation work.
