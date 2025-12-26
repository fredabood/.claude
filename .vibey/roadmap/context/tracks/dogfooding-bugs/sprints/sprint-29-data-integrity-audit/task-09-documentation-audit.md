# Task 9: Audit Documentation Accuracy and Drift

**Task ID**: `01KDDE9NEKAH3BM9PRFPHNNCNB`
**Type**: research
**Priority**: high
**Estimated Tokens**: 3,000

## Objective

Check documentation against actual implementation. Identify documented features that don't exist and implemented features missing from documentation.

## Methodology

### Step 1: Run Built-in Drift Detection

```bash
# Use vibey's built-in drift detection
vibey docs check-drift 2>&1 | tee drift_report.txt
```

### Step 2: Verify CLI Reference Accuracy

```bash
# Generate fresh CLI reference
vibey docs generate-cli --output /tmp/fresh_cli_reference.md

# Compare with existing
diff docs/reference/CLI_REFERENCE.md /tmp/fresh_cli_reference.md > cli_drift.diff

# Count documented vs actual commands
actual_commands=$(vibey --help 2>&1 | grep -cE "^\s+\w+")
documented_commands=$(grep -c "^### " docs/reference/CLI_REFERENCE.md)
echo "Actual: $actual_commands, Documented: $documented_commands"
```

### Step 3: Verify MCP Reference Accuracy

```bash
# Generate fresh MCP reference
vibey docs generate-mcp --output /tmp/fresh_mcp_reference.md

# Compare with existing
diff docs/reference/MCP_REFERENCE.md /tmp/fresh_mcp_reference.md > mcp_drift.diff

# Count documented vs actual tools
actual_tools=$(grep -r "def tool_" vibey/mcp/ --include="*.py" | wc -l)
documented_tools=$(grep -c "^### " docs/reference/MCP_REFERENCE.md)
echo "Actual: $actual_tools, Documented: $documented_tools"
```

### Step 4: Audit ADRs for Accuracy

For each ADR in `docs/architecture/adr/`:

```bash
# List all ADRs
ls docs/architecture/adr/*.md

# For each ADR, verify the decision was implemented
# Example: ADR-0001 (ULID identifiers)
# Check: Are all IDs actually ULIDs?
sqlite3 .vibey/roadmap.db "SELECT id FROM tasks LIMIT 5"
# Verify they match ULID pattern: 26 chars, alphanumeric
```

ADRs to verify:
- ADR-0001: ULID identifiers - Check all IDs are ULIDs
- ADR-0002: Flat directory structure - Check no hierarchical dirs
- ADR-0003: Dual storage SQLite+YAML - Check both exist and sync
- ADR-0004: Click CLI framework - Check Click is used
- ADR-0005: MCP integration - Check MCP server exists

### Step 5: Check README Accuracy

```bash
# Extract claims from README
grep -E "^\*\*|^- \[" README.md > readme_claims.txt

# Verify each claim
# Example: "203 CLI Commands" - count actual
vibey --help 2>&1 | grep -cE "^\s+\w+"

# Example: "76 MCP Tools" - count actual
grep -r "def tool_" vibey/mcp/ --include="*.py" | wc -l
```

### Step 6: Find Undocumented Features

```bash
# CLI commands not in reference
for cmd in $(vibey --help 2>&1 | grep -oE "^\s+\w+" | tr -d ' '); do
    if ! grep -q "### .*$cmd" docs/reference/CLI_REFERENCE.md; then
        echo "UNDOCUMENTED CLI: $cmd"
    fi
done

# MCP tools not in reference
for tool in $(grep -r "def tool_" vibey/mcp/ --include="*.py" -h | sed 's/.*def tool_//' | sed 's/(.*//'); do
    if ! grep -q "$tool" docs/reference/MCP_REFERENCE.md; then
        echo "UNDOCUMENTED MCP: $tool"
    fi
done
```

### Step 7: Find Documented But Missing Features

```bash
# Commands in docs but not in CLI
for cmd in $(grep -oE "^### \w+" docs/reference/CLI_REFERENCE.md | sed 's/### //'); do
    if ! vibey $cmd --help 2>&1 | grep -q "Usage:"; then
        echo "PHANTOM DOCS: $cmd"
    fi
done
```

## Expected Output

```markdown
## Documentation Audit Results

### CLI Reference Drift
| Status | Count |
|--------|-------|
| Documented & Exists | N |
| Documented, Missing | N |
| Exists, Undocumented | N |

### MCP Reference Drift
| Status | Count |
|--------|-------|
| Documented & Exists | N |
| Documented, Missing | N |
| Exists, Undocumented | N |

### ADR Accuracy
| ADR | Decision | Status |
|-----|----------|--------|
| 0001 | ULID identifiers | IMPLEMENTED |
| 0002 | Flat directory | PARTIAL |

### README Accuracy
| Claim | Actual | Status |
|-------|--------|--------|
| 203 CLI Commands | 198 | OUTDATED |
| 76 MCP Tools | 76 | ACCURATE |

### Documentation Gaps
| Feature | Location | Missing From |
|---------|----------|--------------|
| vibey foo | CLI | CLI_REFERENCE.md |

### Phantom Documentation
| Documented Feature | Status |
|--------------------|--------|
| vibey bar | Does not exist |
```

## Success Criteria

- [ ] Drift detection run
- [ ] CLI reference verified
- [ ] MCP reference verified
- [ ] ADRs verified against implementation
- [ ] README claims verified
- [ ] Undocumented features listed
- [ ] Phantom documentation identified

## Tools

- vibey docs check-drift
- diff
- grep
- Bash

## Deliverables

1. `documentation-audit-results.json` - Structured findings
2. Updated documentation recommendations
3. Summary section for final report
