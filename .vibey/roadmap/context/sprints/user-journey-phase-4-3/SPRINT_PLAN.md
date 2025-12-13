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

## Task Dependencies

```
Task 1 (File Inventory) - first
    ↓
Tasks 2-6 - can run in parallel
```

---

## Success Criteria

**Phase 1 Updates:**
- [ ] File inventory current with discovery files

**Phase 2 Updates:**
- [ ] CLI Reference includes all discovery commands
- [ ] MCP Reference includes discovery tools
- [ ] User Journeys include discovery workflows
- [ ] Walkthroughs include discovery examples
- [ ] Coverage Matrix maps discovery features

---

## Notes

This is a documentation checkpoint sprint - no new feature development. Focus is on keeping documentation current with Phase 4.2 implementation.
