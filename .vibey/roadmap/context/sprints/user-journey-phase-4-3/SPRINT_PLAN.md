# Sprint 4.3: Documentation Sync (Post-Discovery)

## Sprint Overview

**Goal:** Update documentation after Discovery Output Architecture implementation to keep Phase 1 audit and Phase 2 docs current.

**Theme:** Documentation Checkpoint

**Estimated Duration:** 1-2 sessions

**Prerequisites:** Phase 4.2 (Discovery Output Architecture) completed

---

## Background

Phase 4.2 implemented structured discovery outputs, versioning, and new CLI commands. This checkpoint ensures all documentation reflects these additions before proceeding with Phase 4.4.

**Phase 4.2 Artifacts to Document:**
- Discovery schema (`vibey/operations/discovery/schema.py`)
- Discovery serializers (`vibey/operations/discovery/serializers.py`)
- Discovery analyzers (`vibey/operations/discovery/analyzers/`)
- New CLI commands (`discover show`, `discover diff`, `discover history`, `discover status`, `discover refresh`)
- New storage structure (`.vibey/discovery/`)

---

## Tasks

### Task 1: Update file inventory with Phase 4.2 artifacts

**Objective:** Add discovery output architecture files to Phase 1 file inventory.

**Deliverables:**
- Updated file inventory

**Files to Add:**
- `vibey/operations/discovery/schema.py`
- `vibey/operations/discovery/serializers.py`
- `vibey/operations/discovery/analyzers/project.py`
- `vibey/operations/discovery/analyzers/structure.py`
- `vibey/operations/discovery/analyzers/dependencies.py`
- `vibey/operations/discovery/analyzers/patterns.py`
- `vibey/operations/discovery/analyzers/conventions.py`
- `docs/reference/DISCOVERY_SCHEMA.md`

**Acceptance Criteria:**
- [ ] All new files added to inventory
- [ ] File categories correct
- [ ] Line counts accurate
- [ ] Summary statistics updated

---

### Task 2: Update CLI Reference with discovery commands

**Objective:** Add documentation for new discovery CLI commands.

**Deliverables:**
- Updated `docs/reference/CLI_REFERENCE.md`

**Commands to Document:**

```bash
vibey discover [--output yaml|json|text] [--save]
# Run project discovery

vibey discover show [--format yaml|json|text]
# Display current discovery output

vibey discover diff [VERSION1] [VERSION2]
# Compare two discovery versions

vibey discover history [--limit N]
# Show discovery history

vibey discover status
# Check if discovery is stale

vibey discover refresh [--force]
# Re-run discovery if stale
```

**For Each Command:**
- Synopsis and description
- All options with defaults
- Example usage with sample output
- Related commands

**Acceptance Criteria:**
- [ ] All 6 discovery commands documented
- [ ] Examples accurate
- [ ] Options complete
- [ ] Cross-references added

---

### Task 3: Update User Journeys with discovery workflows

**Objective:** Add discovery output workflows to relevant user journeys.

**Deliverables:**
- Updated journey files

**Journeys to Update:**

| Journey | New Content |
|---------|-------------|
| New User | "Initial project discovery" workflow |
| Active Developer | "Refresh discovery" workflow |
| Project Lead | "Review project evolution via discovery history" |

**Acceptance Criteria:**
- [ ] New User journey includes discovery setup
- [ ] Active Developer includes discovery refresh
- [ ] Project Lead includes discovery analysis
- [ ] All workflows tested

---

### Task 4: Update MCP Reference with discovery tools

**Objective:** Document any discovery-related MCP tools exposed via the MCP server.

**Deliverables:**
- Updated `docs/reference/MCP_REFERENCE.md`

**Tools to Document (if implemented):**

```yaml
vibey_discover:
  description: Run project discovery
  parameters:
    - output: yaml|json|text
    - save: boolean

vibey_discover_show:
  description: Display current discovery output
  parameters:
    - format: yaml|json|text

vibey_discover_diff:
  description: Compare discovery versions
  parameters:
    - version1: string
    - version2: string

vibey_discover_history:
  description: Show discovery history
  parameters:
    - limit: number

# Resources
vibey://discovery/current:
  description: Current discovery output
vibey://discovery/history:
  description: Discovery version history
```

**Acceptance Criteria:**
- [ ] All discovery MCP tools documented (or noted as CLI-only)
- [ ] Request/response schemas included
- [ ] Examples provided
- [ ] Cross-reference to CLI commands

---

### Task 5: Update Walkthroughs with discovery examples

**Objective:** Add practical discovery examples to relevant walkthroughs.

**Deliverables:**
- Updated walkthrough files

**Walkthroughs to Update:**

| Walkthrough | New Content |
|-------------|-------------|
| New User | "Running your first discovery" section |
| Active Developer | "Comparing project changes with discovery diff" section |
| Project Lead | "Tracking project evolution" section |

**Acceptance Criteria:**
- [ ] Discovery sections added to 3 walkthroughs
- [ ] Commands tested and working
- [ ] Output examples accurate
- [ ] Follows existing walkthrough style

---

### Task 6: Update Coverage Matrix with discovery features

**Objective:** Ensure coverage matrix reflects all discovery commands and features.

**Deliverables:**
- Updated `docs/journeys/COVERAGE_MATRIX.md`

**New Features to Map:**

| Feature | CLI Commands | MCP Tools | Relevant Journeys |
|---------|--------------|-----------|-------------------|
| Discovery | discover, discover show, discover diff, discover history, discover status, discover refresh | vibey_discover_* | New User, Active Developer, Project Lead |

**Acceptance Criteria:**
- [ ] All discovery commands in matrix
- [ ] MCP tools mapped
- [ ] Commands mapped to journeys
- [ ] Coverage statistics updated

---

### Task 7: Comprehensive Phase 1 Audit Review

**Objective:** Review and update ALL Phase 1 audit artifacts to ensure they accurately reflect the current state after discovery implementation.

**Deliverables:**
- Updated Phase 1 audit documents as needed

**Review Checklist:**

| Audit | Review Focus |
|-------|--------------|
| 1.1 File Inventory | Already updated in Task 1 ✓ |
| 1.2 Core Library Audit | Add discovery modules, verify existing module descriptions still accurate |
| 1.3 Documentation Audit | Add discovery docs, verify existing doc references still valid |
| 1.4 Test Suite Audit | Note any discovery tests added, verify test patterns still current |
| 1.5 Scripts & Config Audit | Check for discovery-related config changes |
| 1.6 Database Artifact Audit | Check for discovery-related schema changes (if any) |

**Acceptance Criteria:**
- [ ] Core Library Audit includes discovery modules
- [ ] Documentation Audit includes discovery docs
- [ ] Test Suite Audit reflects current test state
- [ ] Scripts & Config Audit current
- [ ] Database Artifact Audit current

---

### Task 8: Comprehensive Phase 2 Documentation Review

**Objective:** Review and update ALL Phase 2 documentation artifacts to ensure they accurately reflect all features including discovery.

**Deliverables:**
- Updated Phase 2 documentation as needed

**Review Checklist:**

| Document | Review Focus |
|----------|--------------|
| 2.1 CLI Reference | Discovery commands added in Task 2 ✓, verify all other commands still accurate |
| 2.2 MCP Reference | Discovery tools added in Task 4 ✓, verify all other tools still accurate |
| 2.3 User Personas | Update personas with discovery capabilities |
| 2.4 User Journeys | Discovery workflows added in Task 3 ✓, verify existing workflows still accurate |
| 2.4 Walkthroughs | Discovery examples added in Task 5 ✓, verify existing examples still work |
| 2.5 Contributor Docs | Update if discovery affects contribution workflow |
| Coverage Matrix | Updated in Task 6 ✓ |

**Acceptance Criteria:**
- [ ] All CLI commands verified accurate
- [ ] All MCP tools verified accurate
- [ ] User Personas include discovery capabilities
- [ ] All User Journeys verified accurate
- [ ] All Walkthroughs verified working
- [ ] Contributor Docs current

---

## Task Dependencies

```
Task 1 (File Inventory) - first
    ↓
Tasks 2-6 - can run in parallel (discovery-specific updates)
    ↓
Tasks 7-8 - comprehensive review (after discovery updates complete)
```

---

## Success Criteria

**Phase 1 Audit Updates (ALL artifacts):**
- [ ] 1.1 File Inventory - updated with discovery files
- [ ] 1.2 Core Library Audit - includes discovery modules
- [ ] 1.3 Documentation Audit - includes discovery docs
- [ ] 1.4 Test Suite Audit - reflects current test state
- [ ] 1.5 Scripts & Config Audit - current
- [ ] 1.6 Database Artifact Audit - current

**Phase 2 Documentation Updates (ALL artifacts):**
- [ ] 2.1 CLI Reference - all commands accurate
- [ ] 2.2 MCP Reference - all tools accurate
- [ ] 2.3 User Personas - includes discovery capabilities
- [ ] 2.4 User Journeys - all workflows accurate
- [ ] 2.4 Walkthroughs - all examples working
- [ ] 2.5 Contributor Docs - current
- [ ] Coverage Matrix - complete

---

## Notes

This is a documentation checkpoint sprint - no new feature development. Focus is on keeping **ALL** documentation current, not just discovery-specific docs. Every checkpoint ensures the entire documentation set is accurate.
