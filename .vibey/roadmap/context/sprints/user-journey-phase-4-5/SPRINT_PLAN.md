# Sprint 4.5: Documentation Sync (Post-Context)

## Sprint Overview

**Goal:** Update documentation after Context Directory Writers & CLI Integration to keep Phase 1 audit and Phase 2 docs current.

**Theme:** Documentation Checkpoint

**Estimated Duration:** 1-2 sessions

**Prerequisites:** Phase 4.4 (Context Directory Writers) completed

---

## Background

Phase 4.4 implemented context writers, readers, CLI commands, and agent integration. This checkpoint ensures all documentation reflects these additions.

**Phase 4.4 Artifacts to Document:**
- Context writers (`vibey/operations/context/writers.py`)
- Context readers (`vibey/operations/context/readers.py`)
- Context cache (`vibey/operations/context/cache.py`)
- Agent context loader (`vibey/operations/context/agent_context.py`)
- New CLI commands (`context list`, `context show`, `context archive`, etc.)
- New `--output-context` flag on existing commands

---

## Tasks

### Task 1: Update file inventory with Phase 4.4 artifacts

**Objective:** Add context directory writers and CLI integration files to Phase 1 file inventory.

**Deliverables:**
- Updated file inventory

**Files to Add:**
- `vibey/operations/context/__init__.py`
- `vibey/operations/context/writers.py`
- `vibey/operations/context/readers.py`
- `vibey/operations/context/cache.py`
- `vibey/operations/context/agent_context.py`
- `docs/reference/CONTEXT_MANAGEMENT.md`

**Acceptance Criteria:**
- [ ] All new files added to inventory
- [ ] File categories correct
- [ ] Line counts accurate

---

### Task 2: Update CLI Reference with context commands

**Objective:** Add documentation for vibey context command family and --output-context flags.

**Deliverables:**
- Updated `docs/reference/CLI_REFERENCE.md`

**Commands to Document:**

```bash
# Context management commands
vibey context list [--type ...] [--status ...]
vibey context show <context-id> [--format ...]
vibey context archive <context-id>
vibey context clean [--older-than DAYS] [--dry-run]
vibey context export <context-id> [--output FILE]
vibey context import <file>
vibey context search <query> [--type ...]

# Updated commands with --output-context
vibey roadmap start <task> [--output-context]
vibey roadmap complete <task> [--output-context]
vibey discover [--output-context]
```

**Acceptance Criteria:**
- [ ] All context commands documented
- [ ] --output-context flag documented
- [ ] Examples provided
- [ ] Cross-references added

---

### Task 3: Update User Journeys with context workflows

**Objective:** Add context loading and writing workflows to relevant user journeys.

**Deliverables:**
- Updated journey files

**Journeys to Update:**

| Journey | New Content |
|---------|-------------|
| Active Developer | "Capturing context as you work" |
| Project Lead | "Reviewing accumulated context" |
| Platform Integrator | "Accessing context via MCP" |

**Acceptance Criteria:**
- [ ] Context workflows added
- [ ] Commands tested
- [ ] Flows complete

---

### Task 4: Update Walkthroughs with context examples

**Objective:** Add context management examples to relevant walkthroughs.

**Deliverables:**
- Updated walkthrough files

**Walkthroughs to Update:**

| Walkthrough | New Content |
|-------------|-------------|
| Active Developer | "Managing your work context" section |
| Project Lead | "Reviewing team context" section |
| Platform Integrator | "Loading context for agents" section |

**Acceptance Criteria:**
- [ ] Context examples added
- [ ] Commands accurate
- [ ] Output examples included

---

### Task 5: Update MCP Reference with context tools

**Objective:** Document context management MCP tools exposed via the MCP server.

**Deliverables:**
- Updated `docs/reference/MCP_REFERENCE.md`

**Tools to Document (if implemented):**

```yaml
vibey_context_list:
  description: List available context files
  parameters:
    - type: string (optional)
    - status: string (optional)

vibey_context_show:
  description: Display context content
  parameters:
    - context_id: string
    - format: yaml|json|text

vibey_context_search:
  description: Search context files
  parameters:
    - query: string
    - type: string (optional)

vibey_context_export:
  description: Export context to file
  parameters:
    - context_id: string
    - output: string

# Resources
vibey://context/{id}:
  description: Access specific context file
vibey://context/current:
  description: Current active context
vibey://context/types:
  description: Available context types
```

**Acceptance Criteria:**
- [ ] All context MCP tools documented (or noted as CLI-only)
- [ ] Request/response schemas included
- [ ] Examples provided
- [ ] Cross-reference to CLI commands

---

### Task 6: Update Coverage Matrix with context features

**Objective:** Ensure coverage matrix reflects all context management features.

**Deliverables:**
- Updated `docs/journeys/COVERAGE_MATRIX.md`

**New Features to Map:**

| Feature | CLI Commands | MCP Tools | Relevant Journeys |
|---------|--------------|-----------|-------------------|
| Context Management | context list, context show, context archive, context clean, context export, context import, context search | vibey_context_* | Active Developer, Project Lead, Platform Integrator |
| Context Output Flag | --output-context on roadmap start/complete, discover | N/A | Active Developer |

**Acceptance Criteria:**
- [ ] All context commands in matrix
- [ ] MCP tools mapped
- [ ] Commands mapped to journeys
- [ ] Coverage statistics updated

---

### Task 7: Comprehensive Phase 1 Audit Review

**Objective:** Review and update ALL Phase 1 audit artifacts to ensure they accurately reflect the current state after context implementation.

**Deliverables:**
- Updated Phase 1 audit documents as needed

**Review Checklist:**

| Audit | Review Focus |
|-------|--------------|
| 1.1 File Inventory | Already updated in Task 1 ✓ |
| 1.2 Core Library Audit | Add context modules, verify all module descriptions accurate |
| 1.3 Documentation Audit | Add context docs, verify all doc references valid |
| 1.4 Test Suite Audit | Note any context tests, verify test documentation current |
| 1.5 Scripts & Config Audit | Check for context-related config changes |
| 1.6 Database Artifact Audit | Check for context-related schema changes (if any) |

**Acceptance Criteria:**
- [ ] Core Library Audit includes context modules
- [ ] Documentation Audit includes context docs
- [ ] Test Suite Audit reflects current test state
- [ ] Scripts & Config Audit current
- [ ] Database Artifact Audit current

---

### Task 8: Comprehensive Phase 2 Documentation Review

**Objective:** Review and update ALL Phase 2 documentation artifacts to ensure they accurately reflect all features including context management.

**Deliverables:**
- Updated Phase 2 documentation as needed

**Review Checklist:**

| Document | Review Focus |
|----------|--------------|
| 2.1 CLI Reference | Context commands added in Task 2 ✓, verify all commands accurate |
| 2.2 MCP Reference | Context tools added in Task 5 ✓, verify all tools accurate |
| 2.3 User Personas | Update personas with context management capabilities |
| 2.4 User Journeys | Context workflows added in Task 3 ✓, verify all workflows accurate |
| 2.4 Walkthroughs | Context examples added in Task 4 ✓, verify all examples work |
| 2.5 Contributor Docs | Update if context affects contribution workflow |
| Coverage Matrix | Updated in Task 6 ✓ |

**Acceptance Criteria:**
- [ ] All CLI commands verified accurate
- [ ] All MCP tools verified accurate
- [ ] User Personas include context capabilities
- [ ] All User Journeys verified accurate
- [ ] All Walkthroughs verified working
- [ ] Contributor Docs current

---

## Task Dependencies

```
Task 1 (File Inventory) - first
    ↓
Tasks 2-6 - can run in parallel (context-specific updates)
    ↓
Tasks 7-8 - comprehensive review (after context updates complete)
```

---

## Success Criteria

**Phase 1 Audit Updates (ALL artifacts):**
- [ ] 1.1 File Inventory - updated with context files
- [ ] 1.2 Core Library Audit - includes context modules
- [ ] 1.3 Documentation Audit - includes context docs
- [ ] 1.4 Test Suite Audit - reflects current test state
- [ ] 1.5 Scripts & Config Audit - current
- [ ] 1.6 Database Artifact Audit - current

**Phase 2 Documentation Updates (ALL artifacts):**
- [ ] 2.1 CLI Reference - all commands accurate
- [ ] 2.2 MCP Reference - all tools accurate
- [ ] 2.3 User Personas - includes context capabilities
- [ ] 2.4 User Journeys - all workflows accurate
- [ ] 2.4 Walkthroughs - all examples working
- [ ] 2.5 Contributor Docs - current
- [ ] Coverage Matrix - complete

---

## Notes

This is the second documentation checkpoint. After this, all Phase 4 work is documented and we proceed to Phase 5 (testing). Every checkpoint ensures the **entire** documentation set is accurate, not just the newly implemented features.
