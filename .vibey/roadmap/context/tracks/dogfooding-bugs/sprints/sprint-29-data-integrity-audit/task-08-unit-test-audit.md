# Task 8: Audit Unit Test Coverage and Health

**Task ID**: `01KDDE9NEKAH3BM9PRFPHNNCNA`
**Type**: research
**Priority**: high
**Estimated Tokens**: 4,000

## Objective

Assess test suite health including coverage, skipped tests, failing tests, and missing tests for claimed functionality. Compare test coverage against completed task claims.

## Methodology

### Step 1: Run Full Test Suite with Coverage

```bash
# Run pytest with coverage
pytest tests/ --cov=vibey --cov-report=html --cov-report=json -v 2>&1 | tee test_results.txt

# Generate coverage report
coverage report --show-missing > coverage_report.txt
```

### Step 2: Identify Modules with No Coverage

```bash
# Parse coverage JSON for 0% modules
python3 -c "
import json
with open('coverage.json') as f:
    data = json.load(f)
    for file, info in data['files'].items():
        if info['summary']['percent_covered'] == 0:
            print(f'NO COVERAGE: {file}')
"
```

### Step 3: Find Skipped and XFail Tests

```bash
# Run pytest to collect skipped tests
pytest tests/ --collect-only -q 2>&1 | grep -E "skip|xfail"

# Count by reason
pytest tests/ -v 2>&1 | grep -E "SKIPPED|XFAIL" | sort | uniq -c
```

### Step 4: Identify Failing Tests

```bash
# Run tests and capture failures
pytest tests/ -x --tb=short 2>&1 | tee test_failures.txt

# List all failures
pytest tests/ --tb=no 2>&1 | grep FAILED
```

### Step 5: Cross-Reference with CLI Commands

```bash
# Get all CLI commands
vibey --help 2>&1 | grep -E "^\s+\w+" | awk '{print $1}' > cli_commands.txt

# Check for corresponding tests
while read cmd; do
    if ! find tests -name "*${cmd}*" -o -name "*$(echo $cmd | tr '-' '_')*" | grep -q .; then
        echo "NO TEST: $cmd"
    fi
done < cli_commands.txt
```

### Step 6: Cross-Reference with MCP Tools

```bash
# Get all MCP tools
sqlite3 .vibey/roadmap.db "SELECT DISTINCT tool_name FROM some_mcp_table" > mcp_tools.txt

# Or extract from code
grep -r "def tool_" vibey/mcp/ --include="*.py" | sed 's/.*def //' | sed 's/(.*$//' > mcp_tools.txt

# Check for corresponding tests
while read tool; do
    if ! grep -r "$tool" tests/ --include="*.py" -q; then
        echo "NO TEST: MCP tool $tool"
    fi
done < mcp_tools.txt
```

### Step 7: Compare Against Completed Tasks

```sql
-- Get completed tasks that should have tests
SELECT t.id, t.title
FROM tasks t
WHERE t.status = 'completed'
AND t.task_type = 'development'
AND (
    LOWER(t.title) LIKE '%implement%'
    OR LOWER(t.title) LIKE '%add %'
    OR LOWER(t.title) LIKE '%create %'
)
AND NOT EXISTS (
    SELECT 1 FROM tasks t2
    WHERE t2.title LIKE '%test%'
    AND t2.sprint_id = t.sprint_id
    AND t2.status = 'completed'
);
```

## Expected Output

```markdown
## Unit Test Audit Results

### Coverage Summary
| Metric | Value |
|--------|-------|
| Total Lines | X |
| Covered Lines | Y |
| Coverage % | Z% |
| Modules with 0% | N |

### Modules with No Coverage (N modules)
| Module | Lines | Reason |
|--------|-------|--------|
| vibey/foo.py | 150 | No tests exist |

### Skipped Tests (N tests)
| Test | Reason |
|------|--------|
| test_widget | "Pending implementation" |

### Failing Tests (N tests)
| Test | Error | Last Passed |
|------|-------|-------------|
| test_bar | AssertionError | 2025-12-01 |

### CLI Commands Without Tests (N commands)
| Command | Subcommands | Priority |
|---------|-------------|----------|
| vibey foo | bar, baz | High |

### MCP Tools Without Tests (N tools)
| Tool | Category |
|------|----------|
| get_task | roadmap |

### Completed Tasks Missing Tests (N tasks)
| Task ID | Title | Should Test |
|---------|-------|-------------|
| 01K... | Implement feature X | feature_x.py |
```

## Success Criteria

- [ ] Full test suite executed
- [ ] Coverage report generated
- [ ] Zero-coverage modules identified
- [ ] Skipped/xfail tests catalogued
- [ ] Failing tests documented
- [ ] CLI commands vs tests compared
- [ ] MCP tools vs tests compared
- [ ] Task claims vs tests compared

## Tools

- pytest (test execution)
- coverage (coverage analysis)
- Bash (cross-referencing)
- SQLite (task queries)

## Deliverables

1. `test-audit-results.json` - Structured findings
2. `coverage.html` - Visual coverage report
3. Priority list of missing tests
4. Summary section for final report
