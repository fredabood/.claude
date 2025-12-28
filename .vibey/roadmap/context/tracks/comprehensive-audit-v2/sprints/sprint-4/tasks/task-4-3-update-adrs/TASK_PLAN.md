# Task 4.3: Update ADRs for Recent Architectural Decisions

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJKTRVZS618BM5ZZTQ3443B |
| Sprint | 4 - Documentation Sync |
| Type | documentation |
| Complexity | medium |
| Priority | medium |
| Estimated Tokens | ~2,500 |
| Dependencies | Task 4.1 (Documentation drift audit) |

---

## Objective

Review git commits since December 12, 2024 for architectural changes. Identify decisions that need new ADRs or updates to existing ones. Focus areas include: database schema changes, CLI refactoring, directory structure changes, and Implementation Mode architecture.

---

## Files to Review

### Existing ADRs

| File | Title | Current Status |
|------|-------|----------------|
| `docs/architecture/adr/0001-ulid-identifiers.md` | ULID Identifiers | Accepted |
| `docs/architecture/adr/0002-flat-directory-structure.md` | Flat Directory Structure | Accepted |
| `docs/architecture/adr/0003-dual-storage-sqlite-yaml.md` | SQLite + YAML Dual Storage | Accepted |
| `docs/architecture/adr/0004-click-cli-framework.md` | Click CLI Framework | Accepted |
| `docs/architecture/adr/0005-mcp-integration.md` | MCP Protocol Integration | Accepted |

### Code Areas to Review for Changes

| Area | Location | Key Changes Since Dec 12 |
|------|----------|-------------------------|
| Database Schema | `vibey/roadmap/database/` | New tables (39 total) |
| CLI Commands | `vibey/cli/` | New implement commands |
| Directory Structure | `.vibey/roadmap/` | Context system |
| Implementation Mode | `vibey/operations/` | New implementation workflow |
| Token Estimation | `vibey/roadmap/` | Token tracking system |

---

## Verification Commands

### 1. Review Git History Since Dec 12

```bash
# List all commits since Dec 12
git log --oneline --since="2024-12-12" | head -50

# Show commits with architectural keywords
git log --oneline --since="2024-12-12" --grep="architecture\|schema\|refactor\|design"

# Show commits affecting database
git log --oneline --since="2024-12-12" -- "vibey/roadmap/database/"

# Show commits affecting CLI
git log --oneline --since="2024-12-12" -- "vibey/cli/"

# Show detailed changes for a specific commit
git show <commit-hash> --stat
```

### 2. Review Database Schema Changes

```bash
# List current tables
sqlite3 .vibey/roadmap/roadmap.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"

# Count tables
sqlite3 .vibey/roadmap/roadmap.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';"

# Review schema file
cat vibey/roadmap/database/schema.py | head -200

# Find new table definitions
grep -n "CREATE TABLE" vibey/roadmap/database/schema.py
```

### 3. Review CLI Changes

```bash
# List CLI command files
ls -la vibey/cli/

# Find new click.command decorators
git diff --since="2024-12-12" -- "vibey/cli/*.py" | grep "@click.command"

# Show implement command structure
vibey implement --help
```

### 4. Review Directory Structure Changes

```bash
# Show current roadmap structure
ls -la .vibey/roadmap/

# Show context directory structure
ls -laR .vibey/roadmap/context/ 2>/dev/null | head -30

# Check for new directories
git log --oneline --since="2024-12-12" --diff-filter=A -- "*/"
```

---

## Analysis Steps

### Step 1: Identify Architectural Changes

Review commits and categorize by type:

| Change Type | Examples | ADR Impact |
|-------------|----------|------------|
| New Feature | Implementation Mode | New ADR |
| Schema Evolution | 12 new tables | Update ADR-0003 |
| Process Change | Token estimation | New ADR |
| Refactoring | CLI reorganization | Update existing |
| New Integration | Context system | New ADR |

### Step 2: Review Existing ADRs for Accuracy

For each existing ADR:

**ADR-0001: ULID Identifiers**
- [ ] Still using ULIDs everywhere?
- [ ] Any exceptions introduced?
- [ ] Format still correct (26 chars)?

**ADR-0002: Flat Directory Structure**
- [ ] Still using flat structure?
- [ ] Context system introduces hierarchy?
- [ ] Update needed for context directories?

**ADR-0003: Dual Storage (SQLite + YAML)**
- [ ] New tables documented?
- [ ] New YAML formats introduced?
- [ ] Sync mechanism unchanged?

**ADR-0004: Click CLI Framework**
- [ ] Still using Click?
- [ ] Any async patterns introduced?
- [ ] Command structure changes?

**ADR-0005: MCP Integration**
- [ ] Protocol version current?
- [ ] New tool patterns?
- [ ] Resource handling unchanged?

### Step 3: Identify New ADR Candidates

Potential new ADRs based on Dec 12+ changes:

| Candidate ADR | Rationale | Priority |
|---------------|-----------|----------|
| Implementation Mode | New workflow architecture | High |
| Token Estimation System | New tracking mechanism | Medium |
| Context System | Hierarchical context storage | Medium |
| Planned Status Criteria | New status handling | Low |

### Step 4: Draft ADR Updates or New ADRs

**ADR Template:**

```markdown
# ADR-XXXX: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
[Why this decision was needed - the problem being solved]

## Decision
[What we decided to do]

## Consequences

### Positive
- [Benefit 1]
- [Benefit 2]

### Negative
- [Tradeoff 1]
- [Tradeoff 2]

## References
- [Related ADRs]
- [Relevant commits]
- [Design documents]
```

---

## Before/After Comparison Approach

### Comparison Matrix

| ADR | Dec 12 Status | Current State | Action Needed |
|-----|---------------|---------------|---------------|
| 0001 | Accepted | [Verify] | None/Update |
| 0002 | Accepted | [Verify] | None/Update |
| 0003 | Accepted | [Verify] | Update (tables) |
| 0004 | Accepted | [Verify] | None/Update |
| 0005 | Accepted | [Verify] | None/Update |
| 0006 | N/A | Needed | Create new |
| 0007 | N/A | Needed | Create new |

### Changes to Document

For each identified change:

```markdown
## Change: [Name]

### Before (Dec 12)
- [Previous state]

### After (Current)
- [Current state]

### ADR Impact
- New ADR needed: [Yes/No]
- Existing ADR update: [ADR number]
- Documentation: [What to add]
```

---

## Output Format

### ADR_UPDATE_REPORT.md Structure

```markdown
# ADR Update Report

**Date:** [Current date]
**Review Period:** Dec 12, 2024 - Dec 28, 2024

## Executive Summary
- Existing ADRs reviewed: 5
- ADRs needing updates: X
- New ADRs recommended: Y

## Existing ADR Review

### ADR-0001: ULID Identifiers
**Status:** Accurate / Needs Update
**Changes:** [None / Description]

### ADR-0002: Flat Directory Structure
**Status:** Accurate / Needs Update
**Changes:** [None / Description]

[... continue for all ADRs ...]

## New ADRs Recommended

### ADR-0006: [Title] (Proposed)
**Rationale:** [Why needed]
**Scope:** [What it covers]
**Priority:** [High/Medium/Low]

[... continue for all new ADRs ...]

## Architectural Changes Summary

| Category | Changes | ADR Impact |
|----------|---------|------------|
| Database | 12 new tables | Update ADR-0003 |
| CLI | Implement mode | New ADR-0006 |
| Context | New system | New ADR-0007 |

## Action Items
1. [ ] Update ADR-0003 with new tables
2. [ ] Create ADR-0006 for Implementation Mode
3. [ ] Create ADR-0007 for Context System
4. [ ] Review and approve new ADRs
```

---

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| `ADR_UPDATE_REPORT.md` | `sprint-4/outputs/` | Analysis of ADR currency |
| Updated ADR files | `docs/architecture/adr/` | Modified existing ADRs |
| New ADR drafts | `docs/architecture/adr/` | New ADR files (0006+) |
| `ADR_INDEX_UPDATE.md` | `sprint-4/outputs/` | Updated ADR index |

---

## Acceptance Criteria

- [ ] All git commits since Dec 12 reviewed for architectural changes
- [ ] Each existing ADR verified for accuracy
- [ ] Database schema changes documented (new tables)
- [ ] CLI refactoring changes identified
- [ ] Implementation Mode architecture documented
- [ ] New ADR candidates identified with rationale
- [ ] Updates made to outdated existing ADRs
- [ ] New ADRs drafted for significant changes
- [ ] ADR index updated with new/modified ADRs

---

## Notes

- Coordinate with Task 4.1 (drift audit) for ADR accuracy findings
- Focus on decisions with broad impact (not minor implementation details)
- ADRs should capture "why" not just "what"
- Consider team review process for new ADRs
- Some changes may be too minor for ADR - document threshold
