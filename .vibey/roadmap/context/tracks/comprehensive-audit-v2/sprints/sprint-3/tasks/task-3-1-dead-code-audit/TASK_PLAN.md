# Task 3.1: Audit Codebase for Dead Code and Orphaned Files

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDDE9NEKAH3BM9PRFPHNNCN9 |
| Sprint | 3 - Codebase Health Analysis |
| Type | research |
| Complexity | medium |
| Priority | high |
| Estimated Tokens | ~2,500 |
| Dependencies | Sprint 1 (File classifications, FILE_DEPENDENCY_GRAPH.yaml) |

---

## Objective

Identify dead code (unused functions, classes, variables) and orphaned files (Python modules not imported anywhere) using vulture and custom analysis. Generate actionable cleanup recommendations prioritized by impact and risk.

---

## Commands

### 1. Install and Run Vulture

```bash
# Install vulture if not already installed
pip install vulture

# Run vulture on the vibey package with 80% confidence threshold
vulture vibey/ --min-confidence 80 > .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-3/outputs/vulture_raw_output.txt

# Run with sorting by size (largest dead code first)
vulture vibey/ --sort-by-size --min-confidence 80

# Generate whitelist for false positives (entry points, CLI commands, etc.)
vulture vibey/ --make-whitelist > .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-3/outputs/vulture_whitelist.py

# Run excluding known false positives
vulture vibey/ --ignore-names "cli_*,test_*,main,app" --min-confidence 80
```

### 2. Run Vulture by Module

```bash
# Analyze specific high-priority modules
vulture vibey/cli/ --min-confidence 80
vulture vibey/operations/ --min-confidence 80
vulture vibey/roadmap/ --min-confidence 80
vulture vibey/mcp/ --min-confidence 80
vulture vibey/adapters/ --min-confidence 80
```

### 3. Find Orphaned Files

```bash
# List all Python files
find vibey/ -name "*.py" -type f | sort > all_python_files.txt

# Find files that are never imported (requires manual analysis or script)
# Compare against FILE_DEPENDENCY_GRAPH.yaml from Sprint 1
```

---

## Analysis Steps

### Step 1: Run Initial Vulture Scan

1. Execute vulture with 80% confidence threshold
2. Capture raw output to file
3. Count total items flagged (functions, classes, variables, imports)

### Step 2: Categorize Vulture Results

Group findings into categories:

| Category | Description | Risk Level |
|----------|-------------|------------|
| Unused functions | Defined but never called | Medium |
| Unused classes | Defined but never instantiated | Medium |
| Unused variables | Assigned but never read | Low |
| Unused imports | Imported but never used | Low |
| Unreachable code | Code after return/raise | High |

### Step 3: Identify False Positives

Common false positives to filter:

- **CLI entry points**: Functions decorated with `@click.command()` or `@click.group()`
- **MCP tool handlers**: Functions decorated with `@server.tool()` or registered as tools
- **Test fixtures**: pytest fixtures used by tests
- **Magic methods**: `__init__`, `__str__`, `__repr__`, etc.
- **Dynamic calls**: Functions invoked via getattr or string lookup
- **Adapter methods**: Required by interface but not called in codebase

### Step 4: Find Orphaned Files

Cross-reference with Sprint 1's FILE_DEPENDENCY_GRAPH.yaml:

```python
# Pseudocode for orphan detection
orphaned_files = []
for file in all_python_files:
    if file not in dependency_graph['imported_by']:
        if not is_entry_point(file):  # __main__.py, cli entry
            if not is_test_file(file):  # tests/*
                orphaned_files.append(file)
```

Entry points to exclude from orphan check:
- `vibey/__main__.py`
- `vibey/cli/main.py`
- Files in `tests/`
- Files in `scripts/`
- Configuration files (`conftest.py`)

### Step 5: Generate Cleanup Recommendations

Prioritize by:

1. **High Priority**: Unreachable code, large unused functions (>50 lines)
2. **Medium Priority**: Unused classes, medium functions (10-50 lines)
3. **Low Priority**: Unused imports, small variables

---

## Output Format

### DEAD_CODE_REPORT.md Structure

```markdown
# Dead Code Analysis Report

## Summary
- Total items flagged: X
- True dead code: Y
- False positives filtered: Z
- Orphaned files: N

## By Confidence Level
| Confidence | Count | After Filtering |
|------------|-------|-----------------|
| 100%       | X     | Y               |
| 90%        | X     | Y               |
| 80%        | X     | Y               |

## Dead Code by Module
| Module | Functions | Classes | Variables | Imports |
|--------|-----------|---------|-----------|---------|
| cli    | X         | Y       | Z         | W       |
| ...    | ...       | ...     | ...       | ...     |

## Detailed Findings
### High Priority (Remove Soon)
1. `vibey/path/to/file.py:123` - `unused_function()` - Not called anywhere

### Medium Priority (Review Before Removal)
...

### Low Priority (Cleanup When Convenient)
...

## Orphaned Files
| File | Last Modified | Lines | Recommendation |
|------|---------------|-------|----------------|
| ...  | ...           | ...   | ...            |
```

---

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| `DEAD_CODE_REPORT.md` | `sprint-3/outputs/` | Comprehensive analysis with categorized findings |
| `ORPHANED_FILES_LIST.txt` | `sprint-3/outputs/` | Plain text list of orphaned files |
| `vulture_raw_output.txt` | `sprint-3/outputs/` | Raw vulture output for reference |
| `vulture_whitelist.py` | `sprint-3/outputs/` | Generated whitelist for future runs |

---

## Acceptance Criteria

- [ ] Vulture run completed on entire `vibey/` package
- [ ] Results categorized by confidence level (80%, 90%, 100%)
- [ ] False positives identified and documented
- [ ] Orphaned files list generated using Sprint 1's dependency graph
- [ ] Cleanup recommendations prioritized (High/Medium/Low)
- [ ] Report includes line counts and file locations
- [ ] Baseline established for comparison in Task 3.7

---

## Notes

- This task establishes the baseline for Task 3.7 (dead code update report)
- Coordinate with Task 3.2 (test coverage) to verify test files are not flagged as orphans
- Some "dead code" may be intentionally kept for backwards compatibility - document these
