# Task 3.4: Identify Untested CLI Commands and MCP Tools

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJKTRVZS618BM5ZZTQ34436 |
| Sprint | 3 - Codebase Health Analysis |
| Type | research |
| Complexity | medium |
| Priority | medium |
| Estimated Tokens | ~2,500 |
| Dependencies | CLI_REFERENCE.md, MCP_REFERENCE.md (from docs/) |

---

## Objective

Create a comprehensive cross-reference between all CLI commands (203) and MCP tools (76) documented in the reference files with their corresponding test files. Identify commands and tools lacking tests, prioritize by usage and criticality, and generate a prioritized list of tests to add.

---

## Commands

### 1. Extract CLI Commands

```bash
# Get all CLI commands from help output
vibey --help 2>&1 | grep -E "^\s+\w+"

# List all click command decorators
grep -r "@click.command\|@click.group" vibey/cli/ --include="*.py"

# Count command decorators
grep -r "@click.command" vibey/cli/ --include="*.py" | wc -l

# Extract command names from CLI_REFERENCE.md
grep -E "^### |^## vibey" docs/reference/CLI_REFERENCE.md
```

### 2. Extract MCP Tools

```bash
# Find MCP tool registrations
grep -r "@server.tool\|\.tool(" vibey/mcp/ --include="*.py"

# Count tool registrations
grep -r "@server.tool\|def tool_" vibey/mcp/ --include="*.py" | wc -l

# Extract tool names from MCP_REFERENCE.md
grep -E "^### |^## " docs/reference/MCP_REFERENCE.md | head -100
```

### 3. Find Corresponding Tests

```bash
# List all CLI test files
find tests/ -name "test_*cli*.py" -o -name "*cli*test*.py"

# List all MCP test files
find tests/ -name "test_*mcp*.py" -o -name "*mcp*test*.py"

# Search for specific command tests
grep -r "def test_" tests/cli/ --include="*.py" | wc -l

# Search for specific tool tests
grep -r "def test_" tests/mcp/ --include="*.py" 2>/dev/null | wc -l
```

### 4. Cross-Reference Analysis

```bash
# For each CLI command, check if test exists
for cmd in roadmap deploy docs config; do
  echo "=== $cmd ==="
  grep -r "test_$cmd\|\"$cmd\"\|'$cmd'" tests/ --include="*.py" | head -5
done

# Count tests per CLI subcommand
grep -l "vibey roadmap" tests/**/*.py 2>/dev/null | wc -l
```

---

## Analysis Steps

### Step 1: Build CLI Command Inventory

1. Parse CLI_REFERENCE.md to extract all 203 commands
2. Organize by command group:

| Group | Subcommands | Example |
|-------|-------------|---------|
| roadmap | ~50 | roadmap status, roadmap show |
| deploy | ~20 | deploy run, deploy list |
| docs | ~15 | docs generate-cli |
| config | ~10 | config show, config set |
| ... | ... | ... |

### Step 2: Build MCP Tool Inventory

1. Parse MCP_REFERENCE.md to extract all 76 tools
2. Organize by category:

| Category | Tools | Example |
|----------|-------|---------|
| Task Operations | ~20 | task_create, task_update |
| Query Operations | ~15 | query_tasks, query_sprints |
| Content Access | ~10 | get_file_content |
| ... | ... | ... |

### Step 3: Map Commands to Tests

For each CLI command, search for:

- Direct test: `def test_command_name()`
- Integration test: Tests that invoke the command
- Click testing: Tests using `CliRunner`

```python
# Example test patterns to find
def test_roadmap_status()
def test_roadmap_show()
result = runner.invoke(cli, ['roadmap', 'status'])
```

### Step 4: Map Tools to Tests

For each MCP tool, search for:

- Unit test: `def test_tool_name()`
- Integration test: Tests that call the tool handler
- Mock-based tests: Tests with mocked dependencies

### Step 5: Calculate Coverage Matrices

**CLI Coverage Matrix:**

| Command | Has Unit Test | Has Integration Test | Coverage |
|---------|---------------|----------------------|----------|
| roadmap status | Yes/No | Yes/No | Full/Partial/None |

**MCP Coverage Matrix:**

| Tool | Has Unit Test | Has Handler Test | Coverage |
|------|---------------|------------------|----------|
| task_create | Yes/No | Yes/No | Full/Partial/None |

### Step 6: Prioritize Test Gaps

Criteria for prioritization:

1. **Critical (P0)**: Core functionality, user-facing, data integrity
2. **High (P1)**: Frequently used, important features
3. **Medium (P2)**: Standard functionality
4. **Low (P3)**: Edge cases, rarely used features

---

## Output Format

### CLI_TEST_COVERAGE_MATRIX.md Structure

```markdown
# CLI Command Test Coverage Matrix

## Summary
- Total Commands: 203
- Commands with Unit Tests: X
- Commands with Integration Tests: Y
- Fully Tested Commands: Z
- Untested Commands: N

## Coverage by Group

| Group | Commands | Tested | Untested | Coverage |
|-------|----------|--------|----------|----------|
| roadmap | 50 | 35 | 15 | 70% |
| deploy | 20 | 10 | 10 | 50% |
| docs | 15 | 12 | 3 | 80% |
| ... | ... | ... | ... | ... |

## Fully Tested Commands
| Command | Unit Test | Integration Test | File |
|---------|-----------|------------------|------|
| roadmap status | Yes | Yes | tests/cli/test_roadmap.py |

## Partially Tested Commands
| Command | Unit Test | Integration Test | Missing |
|---------|-----------|------------------|---------|
| roadmap show | Yes | No | Integration |

## Untested Commands (Prioritized)
| Priority | Command | Reason | Recommended Test Type |
|----------|---------|--------|----------------------|
| P0 | critical_command | Core feature | Unit + Integration |
| P1 | important_command | Frequently used | Unit |
| P2 | standard_command | Standard use | Unit |
```

### MCP_TEST_COVERAGE_MATRIX.md Structure

```markdown
# MCP Tool Test Coverage Matrix

## Summary
- Total Tools: 76
- Tools with Tests: X
- Untested Tools: Y
- Coverage: Z%

## Coverage by Category

| Category | Tools | Tested | Coverage |
|----------|-------|--------|----------|
| Task Operations | 20 | 15 | 75% |
| Query Operations | 15 | 10 | 67% |
| ... | ... | ... | ... |

## Tested Tools
| Tool | Test File | Test Count |
|------|-----------|------------|
| task_create | tests/mcp/test_tasks.py | 3 |

## Untested Tools (Prioritized)
| Priority | Tool | Category | Recommended Test |
|----------|------|----------|------------------|
| P0 | critical_tool | Operations | Full coverage |
| P1 | important_tool | Queries | Basic coverage |
```

---

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| `CLI_TEST_COVERAGE_MATRIX.md` | `sprint-3/outputs/` | CLI command test mapping |
| `MCP_TEST_COVERAGE_MATRIX.md` | `sprint-3/outputs/` | MCP tool test mapping |
| `TESTS_TO_ADD.md` | `sprint-3/outputs/` | Prioritized list of tests to create |

---

## Acceptance Criteria

- [ ] All 203 CLI commands inventoried from CLI_REFERENCE.md
- [ ] All 76 MCP tools inventoried from MCP_REFERENCE.md
- [ ] Each command/tool checked against test files
- [ ] Coverage matrix created for CLI commands
- [ ] Coverage matrix created for MCP tools
- [ ] Untested items categorized by priority (P0-P3)
- [ ] Recommended test types specified (unit, integration, e2e)
- [ ] At least top 10 P0 tests identified for immediate action

---

## Priority Criteria

### P0 - Critical (Test Immediately)

- Data-modifying operations (create, update, delete)
- Authentication/authorization
- File system operations
- Database operations
- User-facing commands used daily

### P1 - High (Test Soon)

- Query operations
- Status/display commands
- Configuration management
- Frequently used utilities

### P2 - Medium (Test When Possible)

- Less common operations
- Formatting/display variations
- Optional features

### P3 - Low (Nice to Have)

- Deprecated commands
- Edge case handlers
- Platform-specific adapters

---

## Notes

- This task provides input to Task 3.5 (health scorecard)
- Coordinate with Task 3.2 (test coverage) for overall metrics
- Consider creating a test template for consistent coverage
- Some commands may be tested indirectly through integration tests
