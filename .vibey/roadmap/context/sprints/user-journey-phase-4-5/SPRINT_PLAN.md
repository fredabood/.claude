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

## Task Dependencies

```
Task 1 (File Inventory) - first
    ↓
Tasks 2-6 - can run in parallel
```

---

## Success Criteria

**Phase 1 Updates:**
- [ ] File inventory current with context files

**Phase 2 Updates:**
- [ ] CLI Reference includes all context commands
- [ ] MCP Reference includes context tools
- [ ] User Journeys include context workflows
- [ ] Walkthroughs include context examples
- [ ] Coverage Matrix maps context features

---

## Notes

This is the second documentation checkpoint. After this, all Phase 4 work is documented and we proceed to Phase 5 (testing).
