# Sprint 3: MCP/CLI Parity & Integration Tests

## Overview
- **Track:** Test Suite Rehabilitation
- **Sprint ID:** 01KCMTMZQF4CD2GCV1GCJB8KKE
- **Tasks:** 11
- **Status:** In Progress
- **Focus:** Achieve 100% MCP/CLI parity and comprehensive integration tests

## Success Criteria
- [x] MCP/CLI parity enforcement mechanism in place
- [ ] MCP tool test coverage: 95%+
- [ ] Integration tests for full request/response cycle
- [ ] CI enforces coverage thresholds
- [ ] Documentation complete

---

## Completed Tasks (4/11)

### Task 1: Root Cause Analysis ✅
**ID:** `01KCMKG14YEJT49VVQ7GJQNWBW` | **Status:** Completed

**Resolution:** Root cause identified as independent CLI/MCP code paths with no shared registry. Solution: Unified decorator architecture where commands are defined once.

**Deliverable:** `UNIFIED_DECORATOR_ARCHITECTURE.md`

---

### Task 2: Audit MCP to CLI Mapping ✅
**ID:** `01KCMKFMMSAEC4VFAVXDQRV68Y` | **Status:** Completed (Superseded)

**Resolution:** Manual auditing superseded by automated `vibey parity check` command that programmatically compares CLI commands to MCP tools.

**Deliverable:** `vibey/unified/parity.py`

---

### Task 3: Add Missing MCP Tools ✅
**ID:** `01KCMKGGPPCKATCJ9KMAF5DZE8` | **Status:** Completed (Superseded)

**Resolution:** Manual tool creation superseded by unified decorator approach. Commands defined with `@unified_command` automatically generate both CLI commands and MCP tools. 16 commands migrated, remainder will follow incrementally.

**Deliverable:** `vibey/unified/commands/`

---

### Task 4: Implement MCP/CLI Parity Enforcement ✅
**ID:** `01KCMKG7Z740QY2CCWTFRZ6P2D` | **Status:** Completed

**Deliverables:**
- `vibey/unified/` - Complete unified command framework (15 files)
- `tests/unified/test_unified_command.py` - 39 comprehensive tests
- `.github/workflows/parity-check.yml` - CI enforcement
- `vibey parity check` and `vibey parity report` CLI commands

**Commit:** `b510eaf0`

---

## Remaining Tasks (7/11)

### Task 5: Add MCP Tool Unit Tests
**ID:** `01KCMGW1PRG8ADMD0M4Q83PYQC` | **Priority:** High

**Goal:** 95%+ test coverage for all MCP tools

**Plan:**
1. Create `tests/mcp/test_unified_tools.py` - Test the 16 unified commands via MCP adapter
2. Create `tests/mcp/test_legacy_tools.py` - Test existing 76 MCP tools not yet migrated
3. Test patterns:
   - Tool discovery and registration
   - Parameter validation (required, types, defaults)
   - Return value structure
   - Error responses

**Acceptance Criteria:**
- [ ] All MCP tools have unit tests
- [ ] Coverage ≥95%
- [ ] Error handling tested

---

### Task 6: Add MCP Server Integration Tests
**ID:** `01KCMGW5F2CF5XNFPWBGF9YZH0` | **Priority:** High

**Goal:** Full request/response cycle testing

**Plan:**
1. Create `tests/mcp/test_server_integration.py`
2. Test areas:
   - `tools/list` - Tool discovery
   - `tools/call` - Tool execution
   - Parameter validation errors
   - Timeout handling
   - Concurrent request handling
3. Use async test patterns with `pytest-asyncio`

**Acceptance Criteria:**
- [ ] Full request cycle tested
- [ ] Error handling tested
- [ ] Performance acceptable

---

### Task 7: Add Tests for All Operations Modules
**ID:** `01KCMKCXP4MZHWR7W6S9WZ1CF0` | **Priority:** Medium

**Goal:** 100% coverage for `vibey/operations/`

**Plan:**
1. Audit current coverage gaps in `vibey/operations/`
2. Priority modules:
   - `operations/roadmap/update.py`
   - `operations/roadmap/status_manager.py`
   - `operations/docs/` (new introspectors)
3. Create missing test files in `tests/operations/`

**Acceptance Criteria:**
- [ ] All operations modules tested
- [ ] Coverage ≥100%
- [ ] No untested public functions

---

### Task 8: Add Comprehensive CLI Command Tests
**ID:** `01KCMKD53HSHBCSGAERGW7NVKT` | **Priority:** Medium

**Goal:** 100% CLI command coverage

**Plan:**
1. Test unified commands via Click test runner
2. Verify CLI output formatting
3. Test error messages and exit codes
4. Ensure parity between CLI and MCP outputs

**Acceptance Criteria:**
- [ ] All CLI commands tested
- [ ] Happy path and error paths covered
- [ ] Output formatting verified

---

### Task 9: Implement CI Test Coverage Enforcement
**ID:** `01KCMKDJ7JYGHGSYME2V7EEG6Q` | **Priority:** High

**Goal:** CI fails on coverage drops

**Plan:**
1. Add coverage thresholds to `pyproject.toml`:
   ```toml
   [tool.coverage.report]
   fail_under = 90
   ```
2. Update `.github/workflows/` to run coverage
3. Block PRs that drop coverage below threshold

**Acceptance Criteria:**
- [ ] Coverage threshold configured
- [ ] CI reports coverage
- [ ] PRs blocked on coverage drop

---

### Task 10: Add MCP Error Documentation
**ID:** `01KCMGW9859M6C6VPKKHB5BQMR` | **Priority:** Low

**Goal:** Document all MCP error responses

**Plan:**
1. Create `docs/reference/MCP_ERRORS.md`
2. Catalog error types:
   - Validation errors (invalid parameters)
   - Not found errors (missing tasks/sprints)
   - State errors (invalid transitions)
   - Permission errors
3. Include error codes, messages, and resolution steps

**Acceptance Criteria:**
- [ ] All error types documented
- [ ] Resolution steps provided
- [ ] Examples included

---

### Task 11: Add MCP Workflow Examples
**ID:** `01KCMGWD1SYQYZB676RM0896YR` | **Priority:** Low

**Goal:** Document common MCP tool sequences

**Plan:**
1. Add to `docs/reference/MCP_REFERENCE.md` or create `docs/guides/MCP_WORKFLOWS.md`
2. Example workflows:
   - Sprint planning workflow
   - Task completion workflow
   - Status reporting workflow
   - Deployment workflow
3. Show tool call sequences with sample inputs/outputs

**Acceptance Criteria:**
- [ ] Common workflows documented
- [ ] Sample inputs/outputs included
- [ ] AI agent guidance provided

---

## Execution Order

| Order | Task | Priority | Rationale |
|-------|------|----------|-----------|
| 1 | Task 5 (MCP Unit Tests) | High | Foundation for other tests |
| 2 | Task 6 (Integration Tests) | High | Verify end-to-end |
| 3 | Task 9 (CI Enforcement) | High | Lock in coverage early |
| 4 | Task 7 (Operations Tests) | Medium | Fill coverage gaps |
| 5 | Task 8 (CLI Tests) | Medium | Complement MCP tests |
| 6 | Task 10 (Error Docs) | Low | Document what we tested |
| 7 | Task 11 (Workflow Examples) | Low | User-facing docs |

---

## Sprint Progress

- **Tasks Completed:** 4/11 (36%)
- **Tasks Remaining:** 7
- **Key Achievement:** Unified decorator architecture eliminates manual parity maintenance

## Architecture Decision

The original plan called for manually adding 93 MCP tools to match CLI commands. This was replaced with a superior approach:

**Unified Decorator Pattern:**
```python
@unified_command(
    name="roadmap_status",
    interfaces=["cli", "mcp"],  # Automatically available in both
)
def roadmap_status(...):
    ...
```

Benefits:
- Single source of truth for command definitions
- Automatic parity - no manual synchronization
- CI enforcement via `vibey parity check`
- Type-safe with IDE support

See: `UNIFIED_DECORATOR_ARCHITECTURE.md` for full technical details.
