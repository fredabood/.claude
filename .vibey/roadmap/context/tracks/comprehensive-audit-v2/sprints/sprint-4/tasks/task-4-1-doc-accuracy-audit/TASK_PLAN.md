# Task 4.1: Audit Documentation Accuracy and Drift

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDDE9NEKAH3BM9PRFPHNNCNB |
| Sprint | 4 - Documentation Sync |
| Type | research |
| Complexity | medium |
| Priority | high |
| Estimated Tokens | ~2,500 |
| Dependencies | Sprints 1-3 (for accurate content understanding) |

---

## Objective

Systematically check documentation against actual implementation to identify documentation drift (outdated content). Verify CLI_REFERENCE.md matches actual commands, MCP_REFERENCE.md matches actual tools, and ADRs reflect current architecture. Identify any documented features that do not exist in the implementation.

---

## Files to Review

### Primary Documentation Files

| File | Purpose | Check Against |
|------|---------|---------------|
| `docs/reference/CLI_REFERENCE.md` | CLI command documentation | Actual CLI output |
| `docs/reference/MCP_REFERENCE.md` | MCP tools documentation | MCP server implementation |
| `docs/architecture/adr/*.md` | Architecture decisions | Current codebase |
| `CLAUDE.md` | Repository context | Actual statistics |
| `README.md` | Project overview | Current features |
| `CONTRIBUTING.md` | Contribution guide | Current workflow |

### Secondary Documentation Files

| Directory | Expected Count | Purpose |
|-----------|----------------|---------|
| `docs/journeys/` | ~5 files | User persona journeys |
| `docs/walkthroughs/` | ~4 files | Step-by-step guides |
| `docs/guides/` | Variable | Feature guides |
| `docs/development/` | ~3 files | Developer setup |

---

## Verification Commands

### 1. Inventory Documentation Files

```bash
# Count all documentation files
find docs -name "*.md" -type f | wc -l

# List all documentation files with dates
find docs -name "*.md" -type f -exec stat -f "%Sm %N" -t "%Y-%m-%d" {} \; | sort

# Count by directory
for dir in docs/*/; do echo "$dir: $(find "$dir" -name "*.md" | wc -l)"; done
```

### 2. Verify CLI_REFERENCE.md Accuracy

```bash
# Count documented commands
grep -c "^### " docs/reference/CLI_REFERENCE.md

# Get actual command count from CLI
vibey --help 2>&1 | grep -c "^\s"

# List all commands from CLI
vibey --help 2>&1

# Compare specific command groups
vibey roadmap --help
vibey deploy --help
vibey docs --help
```

### 3. Verify MCP_REFERENCE.md Accuracy

```bash
# Count documented tools
grep -c "^### " docs/reference/MCP_REFERENCE.md

# Count actual tools (from code)
grep -r "@server.tool" vibey/mcp/ | wc -l

# List tool registrations
grep -r "def .*tool.*" vibey/mcp/ --include="*.py"
```

### 4. Verify ADR Accuracy

```bash
# List all ADRs
ls -la docs/architecture/adr/

# Check ADR references in code
for adr in docs/architecture/adr/*.md; do
    echo "=== $adr ==="
    # Extract key decisions and verify in code
done
```

### 5. Verify CLAUDE.md Statistics

```bash
# Verify CLI command count
vibey --help 2>&1 | grep -E "^\s+\w+" | wc -l

# Verify MCP tool count
grep -r "@server.tool\|register_tool" vibey/mcp/ | wc -l

# Verify database table count
sqlite3 .vibey/roadmap/roadmap.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';"

# Verify adapter count
ls vibey/adapters/*.py | grep -v __init__ | wc -l
```

---

## Analysis Steps

### Step 1: Create Documentation Inventory

1. List all markdown files in `docs/`
2. Record last modified date for each
3. Categorize by type (reference, guide, ADR, journey, walkthrough)

### Step 2: Calculate Drift Score

For each documentation file:

```
Drift Score = (days since last update) * (critical reference count)
```

Where critical reference count = number of references to:
- CLI commands
- MCP tools
- File paths
- Code examples

### Step 3: Verify CLI Reference

For each documented command:
1. Run `vibey <command> --help`
2. Compare documented options vs actual
3. Note discrepancies

Checklist:
- [ ] All 203 documented commands exist
- [ ] Command signatures match
- [ ] Options and flags accurate
- [ ] Examples run successfully

### Step 4: Verify MCP Reference

For each documented tool:
1. Locate tool definition in code
2. Compare documented parameters vs actual
3. Note discrepancies

Checklist:
- [ ] All 76 documented tools exist
- [ ] Parameter names and types match
- [ ] Return types documented correctly
- [ ] Examples accurate

### Step 5: Verify ADR Accuracy

For each ADR:
1. Identify the decision documented
2. Verify implementation matches decision
3. Check if decision has been superseded

ADR Checklist:
- [ ] ADR-0001 (ULIDs): Still using ULIDs everywhere?
- [ ] ADR-0002 (Flat structure): Directory structure unchanged?
- [ ] ADR-0003 (Dual storage): SQLite + YAML still in use?
- [ ] ADR-0004 (Click): CLI still using Click?
- [ ] ADR-0005 (MCP): MCP integration unchanged?

### Step 6: Identify Phantom Features

Find documented features that do not exist:
- Commands in CLI_REFERENCE that fail
- Tools in MCP_REFERENCE not implemented
- Options documented but not functional

---

## Before/After Comparison Approach

### Comparison Method

Create a structured drift report comparing:

| Aspect | Documented | Actual | Status |
|--------|------------|--------|--------|
| CLI Commands | 203 | ? | Match/Drift |
| MCP Tools | 76 | ? | Match/Drift |
| MCP Resources | 8 | ? | Match/Drift |
| MCP Prompts | 4 | ? | Match/Drift |
| Database Tables | 30 | ? | Match/Drift |
| Platform Adapters | 9 | ? | Match/Drift |

### Drift Categories

| Category | Definition | Action Required |
|----------|------------|-----------------|
| Accurate | Doc matches implementation | None |
| Outdated | Implementation changed | Update doc |
| Phantom | Doc exists, feature doesn't | Remove doc |
| Undocumented | Feature exists, no doc | Add doc |

---

## Output Format

### DOCUMENTATION_DRIFT_REPORT.md Structure

```markdown
# Documentation Drift Report

**Date:** [Current date]
**Baseline:** CLAUDE.md v2.5.0

## Executive Summary
- Total documentation files: X
- Files with drift: Y
- Critical drift items: Z

## Drift by Category

### CLI Reference
| Command | Documented | Actual | Status |
|---------|------------|--------|--------|
| ...     | ...        | ...    | ...    |

### MCP Reference
| Tool | Documented | Actual | Status |
|------|------------|--------|--------|
| ...  | ...        | ...    | ...    |

### ADRs
| ADR | Status | Notes |
|-----|--------|-------|
| ... | ...    | ...   |

## Phantom Features (Documented but Missing)
1. [Feature 1] - [Location in docs]
2. ...

## Undocumented Features (Missing from Docs)
1. [Feature 1] - [Location in code]
2. ...

## Priority Updates Needed
1. [High] CLI_REFERENCE.md - X commands outdated
2. [High] MCP_REFERENCE.md - Y tools outdated
3. [Medium] ADR updates needed
4. ...

## Drift Score Summary
| File | Days Since Update | Drift Score |
|------|-------------------|-------------|
| ...  | ...               | ...         |
```

---

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| `DOCUMENTATION_DRIFT_REPORT.md` | `sprint-4/outputs/` | Comprehensive drift analysis |
| `CLI_DRIFT_DETAILS.md` | `sprint-4/outputs/` | CLI-specific drift findings |
| `MCP_DRIFT_DETAILS.md` | `sprint-4/outputs/` | MCP-specific drift findings |
| `ADR_AUDIT_RESULTS.md` | `sprint-4/outputs/` | ADR accuracy assessment |
| Priority update list | Embedded in report | Ranked update recommendations |

---

## Acceptance Criteria

- [ ] All documentation files inventoried with last modified dates
- [ ] CLI_REFERENCE.md verified against actual commands
- [ ] MCP_REFERENCE.md verified against actual tools
- [ ] All ADRs checked for accuracy
- [ ] Phantom features identified and documented
- [ ] Undocumented features identified
- [ ] Drift scores calculated for priority ranking
- [ ] Priority update list generated for Sprint 4 tasks
- [ ] Report includes specific line numbers/sections needing updates

---

## Notes

- This task informs all other Sprint 4 tasks - complete first
- Coordinate with Task 4.2 (check-drift command) for automated verification
- Focus on high-impact drift (user-facing documentation)
- Some drift may be acceptable if clearly marked as "planned features"
