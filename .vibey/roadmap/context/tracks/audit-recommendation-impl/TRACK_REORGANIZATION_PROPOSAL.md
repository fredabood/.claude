# Audit Recommendation Implementation - Track Reorganization Proposal

**Date:** 2025-12-17
**Purpose:** Frontload all audit/review/design work; ensure logical dependency ordering

---

## Current State Analysis

### Problems with Current Structure

1. **Design tasks scattered** - Sprint 7, 8, 10, 11 all have design tasks
2. **Audit mixed with implementation** - Sprint 3, 7, 10 mix audits with code changes
3. **Architecture sprint too late** - Sprint 10 has critical design work but comes after implementation
4. **Git submodule design last** - Sprint 11 is pure research/design but scheduled last
5. **No clear phases** - Hard to know when "discovery" ends and "doing" begins

### Task Classification (107 total)

| Category | Count | Description |
|----------|-------|-------------|
| Research/Audit | 14 | Investigate current state |
| Design/Planning | 14 | Define solutions |
| Documentation | 32 | Fix/improve docs |
| Test Infrastructure | 7 | Fix broken tests |
| Test Coverage | 17 | Add new tests |
| Implementation - Cleanup | 9 | Remove/consolidate code |
| Implementation - Refactor | 6 | Restructure code |
| Implementation - Features | 8 | New functionality |

---

## Proposed New Structure

### Phase 1: Research & Audit (Sprint 1-2)
*Understand current state before making decisions*

### Phase 2: Design & Architecture (Sprint 3-4)
*Define solutions based on audit findings*

### Phase 3: Documentation Quick Wins (Sprint 5)
*Low-risk fixes that unblock users*

### Phase 4: Test Infrastructure (Sprint 6)
*Fix broken tests to enable safe changes*

### Phase 5: Test Coverage (Sprint 7-8)
*Add tests before major refactoring*

### Phase 6: Implementation - Cleanup (Sprint 9)
*Remove obsolete code, consolidate utilities*

### Phase 7: Implementation - Refactoring (Sprint 10)
*Major code restructuring*

### Phase 8: Implementation - Features (Sprint 11)
*New functionality*

### Phase 9: Documentation Finalization (Sprint 12)
*Update docs to reflect changes*

---

## Detailed Sprint Breakdown

### Sprint 1: Codebase Audit
**Focus:** Understand current code state
**Tasks:** 8 | **Effort:** 12h

| Task | Type | Priority | Current Sprint |
|------|------|----------|----------------|
| Run dead code analysis with vulture | audit | low | Sprint 10 |
| Audit CLI commands for existence | audit | critical | Sprint 3 |
| Audit CLI commands for complete parameter documentation | audit | high | Sprint 2 |
| Audit MCP to CLI command mapping for gaps | audit | critical | Sprint 7 |
| Root cause analysis: MCP/CLI drift | audit | critical | Sprint 7 |
| Audit YAML schema versions before cleanup | audit | medium | Sprint 10 |
| Audit current directory structure coupling to semantic layer | audit | critical | Sprint 10 |
| Audit docs for architectural concept coverage | audit | high | Sprint 9 |

**Dependencies:** None - this is the starting point

---

### Sprint 2: User Experience Audit
**Focus:** Understand documentation/UX gaps
**Tasks:** 4 | **Effort:** 6h

| Task | Type | Priority | Current Sprint |
|------|------|----------|----------------|
| Audit user journeys for CLI/MCP coverage gaps | audit | high | Sprint 9 |
| Test and verify all code examples in documentation | testing | medium | Sprint 9 |
| Test and document context CLI commands | testing | high | Sprint 8 |
| Research git submodule integration patterns | research | high | Sprint 11 |

**Dependencies:** None

---

### Sprint 3: Architecture Design
**Focus:** Core architectural decisions
**Tasks:** 8 | **Effort:** 20h

| Task | Type | Priority | Current Sprint |
|------|------|----------|----------------|
| Analyze CLI entry point vs unified ticket architecture layers | design | critical | Sprint 10 |
| Define semantic layer boundaries and responsibilities | design | high | Sprint 10 |
| Design CLI refactor for first-class semantic layer | design | critical | Sprint 10 |
| Design decoupled directory structure | design | critical | Sprint 10 |
| Assess refactor scope and migration path | design | high | Sprint 10 |
| Design planned status criterion for tickets | design | critical | Sprint 10 |
| Create CONTEXT_ARCHITECTURE.md | design | high | Sprint 8 |
| Design action-oriented walkthrough structure | design | high | Sprint 9 |

**Dependencies:** Sprint 1 (audits inform design)

---

### Sprint 4: Feature & Integration Design
**Focus:** New feature and integration planning
**Tasks:** 6 | **Effort:** 14h

| Task | Type | Priority | Current Sprint |
|------|------|----------|----------------|
| Design hybrid context management with git integration | design | critical | Sprint 8 |
| Define submodule detection and discovery | design | high | Sprint 11 |
| Design cross-repo dependency tracking | design | high | Sprint 11 |
| Design requirements pull-up from submodules to parent | design | critical | Sprint 11 |
| Design requirements push-down from parent to submodules | design | critical | Sprint 11 |
| Produce git submodule integration design document | design | high | Sprint 11 |

**Dependencies:** Sprint 3 (architecture defines integration points)

---

### Sprint 5: Critical Documentation Fixes
**Focus:** Unblock users with doc fixes
**Tasks:** 12 | **Effort:** 10h

| Task | Type | Priority | Current Sprint |
|------|------|----------|----------------|
| Fix installation documentation | doc | critical | Sprint 1 |
| Update path references to flat ULID structure | doc | critical | Sprint 1 |
| Fix broken documentation links | doc | high | Sprint 1 |
| Fix version hardcoding in examples | doc | medium | Sprint 1 |
| Update deprecated /vibey slash command references | doc | high | Sprint 1 |
| Fix truncated CLI descriptions | doc | high | Sprint 2 |
| Fix command index organization | doc | high | Sprint 2 |
| Add CLI quick start section | doc | high | Sprint 2 |
| Add MCP usage guidance section | doc | high | Sprint 2 |
| Regenerate reference documentation | doc | medium | Sprint 2 |
| Add cross-references between related commands | doc | medium | Sprint 2 |
| Standardize command syntax across documentation | doc | medium | Sprint 3 |

**Dependencies:** None (documentation is independent)

---

### Sprint 6: Test Infrastructure Repair
**Focus:** Fix broken tests
**Tasks:** 5 | **Effort:** 14h

| Task | Type | Priority | Current Sprint |
|------|------|----------|----------------|
| Fix ORM/Repository test infrastructure | testing | critical | Sprint 5 |
| Fix standards resolution tests | testing | high | Sprint 5 |
| Fix performance tests | testing | high | Sprint 5 |
| Fix validators tests | testing | high | Sprint 5 |
| Fix git hooks tests | testing | high | Sprint 5 |

**Dependencies:** None (tests fix existing infrastructure)

---

### Sprint 7: Core Test Coverage
**Focus:** CLI and operations tests
**Tasks:** 10 | **Effort:** 24h

| Task | Type | Priority | Current Sprint |
|------|------|----------|----------------|
| Add CLI command tests for roadmap operations | testing | high | Sprint 6 |
| Add roadmap update operation tests | testing | high | Sprint 6 |
| Add transaction rollback tests | testing | high | Sprint 6 |
| Add database integrity tests | testing | medium | Sprint 6 |
| Add advanced validator tests | testing | medium | Sprint 6 |
| Add tests for Phase 2-3 new modules | testing | high | Sprint 6 |
| Add tests for all adapter implementations | testing | high | Sprint 6 |
| Add tests for common, config, platform, content modules | testing | medium | Sprint 6 |
| Add tests for data models | testing | high | Sprint 6 |
| Add tests for serialization layer | testing | high | Sprint 6 |

**Dependencies:** Sprint 6 (test infrastructure must work first)

---

### Sprint 8: MCP & Integration Test Coverage
**Focus:** MCP and integration tests
**Tasks:** 6 | **Effort:** 16h

| Task | Type | Priority | Current Sprint |
|------|------|----------|----------------|
| Add MCP tool unit tests | testing | high | Sprint 7 |
| Add MCP server integration tests | testing | high | Sprint 7 |
| Add comprehensive CLI command tests | testing | high | Sprint 7 |
| Add tests for all operations modules | testing | high | Sprint 7 |
| Add integration tests for CLI-Database flow | testing | high | Sprint 10 |
| Implement CI test coverage enforcement | impl | high | Sprint 7 |

**Dependencies:** Sprint 7 (core tests first)

---

### Sprint 9: Code Cleanup
**Focus:** Remove obsolete code, consolidate utilities
**Tasks:** 9 | **Effort:** 12h

| Task | Type | Priority | Current Sprint |
|------|------|----------|----------------|
| Clean up commented code blocks | cleanup | low | Sprint 1 |
| Remove unused imports | cleanup | low | Sprint 4 |
| Remove hierarchical directory support | cleanup | medium | Sprint 10 |
| Remove slug-based ID handling | cleanup | low | Sprint 10 |
| Remove old activity log format handlers | cleanup | low | Sprint 10 |
| Remove identified obsolete functions | cleanup | low | Sprint 10 |
| Consolidate ID validation functions | cleanup | medium | Sprint 4 |
| Consolidate path construction utilities | cleanup | medium | Sprint 4 |
| Implement backup file cleanup policy | cleanup | low | Sprint 10 |

**Dependencies:** Sprint 8 (tests protect against regressions)

---

### Sprint 10: Major Refactoring
**Focus:** Structural code changes
**Tasks:** 6 | **Effort:** 20h

| Task | Type | Priority | Current Sprint |
|------|------|----------|----------------|
| Split commands.py into logical modules | refactor | medium | Sprint 10 |
| Standardize error handling in CLI commands | refactor | high | Sprint 4 |
| Fix activity log integration gaps | refactor | high | Sprint 4 |
| Implement CLI refactor for semantic layer alignment | refactor | high | Sprint 10 |
| Implement missing CLI command options | refactor | high | Sprint 3 |
| Update documentation for CLI command variations | refactor | high | Sprint 3 |

**Dependencies:** Sprint 9 (cleanup before refactoring)

---

### Sprint 11: New Features
**Focus:** New functionality
**Tasks:** 12 | **Effort:** 24h

| Task | Type | Priority | Current Sprint |
|------|------|----------|----------------|
| Add CLI/MCP commands for planned status workflow | feature | high | Sprint 10 |
| Implement planned criterion targets | feature | high | Sprint 10 |
| Implement hierarchical planned status aggregation | feature | high | Sprint 10 |
| Implement token budget enforcement | feature | medium | Sprint 8 |
| Add context freshness tracking | feature | medium | Sprint 8 |
| Add context management MCP tools | feature | medium | Sprint 8 |
| Rename context directory to plans, add post-mortem structure | feature | high | Sprint 8 |
| Add post-mortem generation for completed tasks | feature | high | Sprint 8 |
| Integrate context into ticket-level data structure | feature | critical | Sprint 8 |
| Implement timestamp-based context linking with git commits | feature | critical | Sprint 8 |
| Add missing MCP tools to achieve CLI parity | feature | high | Sprint 7 |
| Implement MCP/CLI parity enforcement | feature | critical | Sprint 7 |

**Dependencies:** Sprint 10 (refactoring creates stable base for features)

---

### Sprint 12: Documentation Finalization
**Focus:** Update all docs for changes
**Tasks:** 16 | **Effort:** 14h

| Task | Type | Priority | Current Sprint |
|------|------|----------|----------------|
| Add option defaults to CLI reference | doc | medium | Sprint 9 |
| Document CLI error responses | doc | medium | Sprint 9 |
| Add MCP error documentation | doc | medium | Sprint 7 |
| Add MCP workflow examples | doc | medium | Sprint 7 |
| Document all context output formats | doc | low | Sprint 8 |
| Create context engineering user guide | doc | medium | Sprint 8 |
| Verify and update JOURNEY_CONTRIBUTOR.md | doc | high | Sprint 9 |
| Add documentation to vibey/content/ module | doc | low | Sprint 9 |
| Archive historical documentation files | doc | low | Sprint 9 |
| Add MCP integration sections to walkthroughs | doc | medium | Sprint 9 |
| Update expected output in walkthroughs | doc | medium | Sprint 9 |
| Create user-facing architecture overview | doc | high | Sprint 9 |
| Integrate architectural concepts into action walkthroughs | doc | medium | Sprint 9 |
| Integrate architectural concepts into reference guides | doc | medium | Sprint 9 |
| Consolidate persona journeys into action walkthroughs | doc | high | Sprint 9 |
| Ensure 100% command coverage in action walkthroughs | doc | high | Sprint 9 |
| Create JOURNEY_PLUGIN_DEVELOPER.md | doc | medium | Sprint 9 |

**Dependencies:** Sprint 11 (document final state)

---

## Dependency Graph

```
[Sprint 1: Codebase Audit] ──────────────────────┐
                                                 │
[Sprint 2: UX Audit] ────────────────────────────┤
                                                 ▼
                              [Sprint 3: Architecture Design]
                                                 │
                                                 ▼
                              [Sprint 4: Feature & Integration Design]
                                                 │
[Sprint 5: Critical Doc Fixes] ──────────────────┤ (parallel)
                                                 │
[Sprint 6: Test Infrastructure] ─────────────────┤ (parallel)
                                                 │
                                                 ▼
                              [Sprint 7: Core Test Coverage]
                                                 │
                                                 ▼
                              [Sprint 8: MCP & Integration Tests]
                                                 │
                                                 ▼
                              [Sprint 9: Code Cleanup]
                                                 │
                                                 ▼
                              [Sprint 10: Major Refactoring]
                                                 │
                                                 ▼
                              [Sprint 11: New Features]
                                                 │
                                                 ▼
                              [Sprint 12: Documentation Finalization]
```

---

## Summary of Changes

### Sprint Renaming

| Old Sprint | New Sprint | Rationale |
|------------|------------|-----------|
| Sprint 1: Critical Blockers | Sprint 5: Critical Doc Fixes | Doc fixes moved after design |
| Sprint 2: Reference Guide Improvements | Sprint 5: Critical Doc Fixes | Merged with doc fixes |
| Sprint 3: CLI Command Verification | Sprint 1: Codebase Audit | Audit first, implement later |
| Sprint 4: Code Consistency | Sprint 9: Code Cleanup | After tests protect code |
| Sprint 5: Test Infrastructure Repair | Sprint 6: Test Infrastructure | Unchanged position |
| Sprint 6: Core Test Coverage | Sprint 7: Core Test Coverage | Unchanged position |
| Sprint 7: MCP Test Coverage | Sprint 8: MCP Test Coverage | Split audit from tests |
| Sprint 8: Context System Enhancement | Sprint 4 + 11 | Split design from impl |
| Sprint 9: Documentation Completion | Sprint 12: Doc Finalization | After all changes |
| Sprint 10: Architecture & Cleanup | Sprint 3 + 9 | Split design from cleanup |
| Sprint 11: Git Submodule Scoping | Sprint 4: Feature Design | Moved to design phase |

### Key Principle: Design → Test → Implement → Document

1. **Audit/Research first** - Know what you're dealing with
2. **Design second** - Decide what to do before coding
3. **Tests third** - Safety net before changes
4. **Implementation fourth** - Execute the plan
5. **Documentation last** - Capture final state

---

## Implementation Notes

To apply this reorganization:

1. Create new sprints with proposed names
2. Move tasks to appropriate sprints (task IDs unchanged)
3. Archive old sprint YAML files
4. Update track progress tracking
5. Rebuild database

This reorganization ensures that:
- All discovery work happens before implementation
- Tests protect against regressions during refactoring
- Documentation reflects final state, not intermediate states
- Dependencies flow naturally from understanding → design → execute → document
