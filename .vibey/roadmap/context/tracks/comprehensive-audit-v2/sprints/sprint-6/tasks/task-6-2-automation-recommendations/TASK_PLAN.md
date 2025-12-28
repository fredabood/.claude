# Task 6.2: Document Audit Automation Recommendations

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJNKE2B2W5NJRTSRZWN4QTC |
| Sprint | 6 - Friction & Progress Tracking |
| Type | documentation |
| Complexity | medium |
| Priority | medium |
| Estimated Tokens | ~2,500 |
| Dependencies | Sprint 5 (Remediation complete) |

---

## Objective

Document recommendations for automating audit maintenance processes. Identify which audit outputs can be fully auto-generated, which require partial automation with human verification, and which must remain manual. Propose CI/CD checks for audit drift detection and provide concrete GitHub Actions workflow examples.

---

## Analysis Approach

### Phase 1: Inventory Audit Outputs

Catalog all audit outputs and deliverables from the Comprehensive Repository Audit V2:

1. **Sprint 1 Outputs**
   - FILE_INVENTORY.yaml
   - FILE_REGISTRY.yaml
   - FILE_DEPENDENCY_GRAPH.yaml

2. **Sprint 1.5 Outputs**
   - Module audit reports (CLI, operations, roadmap, MCP, adapters, common)
   - Cross-module analysis

3. **Sprint 2 Outputs**
   - File creation audit results
   - Migration audit findings
   - Orphan detection results
   - Completion verification data

4. **Sprint 3 Outputs**
   - Dead code analysis reports
   - Test coverage reports
   - Health scorecard

5. **Sprint 5 Outputs**
   - Remediation logs
   - Progress comparison data

6. **Sprint 6 Outputs**
   - Friction log
   - Automation recommendations (this task)
   - Dashboard specifications
   - Maintenance schedule

### Phase 2: Classify Automation Potential

For each output, determine automation classification:

| Classification | Definition | Human Effort |
|----------------|------------|--------------|
| Fully Automatable | Can run unattended on schedule | None |
| Partially Automatable | Auto-generate, human verifies | Review only |
| Manual Only | Requires human judgment | Full effort |

### Phase 3: Design CI/CD Integration

Define triggers, workflows, and failure conditions for automated checks.

---

## Automation Categories

### Fully Automatable Outputs

| Output | Tool/Command | Trigger | Notes |
|--------|--------------|---------|-------|
| File count inventory | `find`, `wc` scripts | On commit | Count Python, YAML, Markdown files |
| Test coverage | `pytest --cov` | On commit/PR | Fail below threshold |
| Static analysis | `ruff check`, `mypy` | On commit/PR | Fail on errors |
| Dead code detection | `vulture` | Weekly | Report unused code |
| CLI reference | `vibey docs generate-cli` | On release | Auto-regenerate |
| MCP reference | `vibey docs generate-mcp` | On release | Auto-regenerate |
| Progress percentages | `vibey roadmap status` | On commit | Track completion |
| Database rebuild | `vibey roadmap db rebuild` | On YAML change | Maintain sync |

### Partially Automatable Outputs

| Output | Auto-Generate | Human Verify | Notes |
|--------|---------------|--------------|-------|
| File classification | Suggest based on path | Confirm categories | ML could improve |
| Documentation drift | Detect with `vibey docs check-drift` | Fix issues | Can auto-fail CI |
| Dependency graph | Parse imports | Validate relationships | Complex deps need review |
| Orphan detection | Query database | Determine action | Some orphans intentional |

### Manual Only Outputs

| Output | Reason | Frequency |
|--------|--------|-----------|
| Module quality assessments | Subjective judgment | Monthly |
| Architectural recommendations | Strategic decisions | Quarterly |
| Friction log entries | Developer experience | On occurrence |
| Priority decisions | Business context | As needed |
| Code review | Semantic understanding | Per change |

---

## CI/CD Integration Design

### GitHub Actions Workflows

#### 1. On Every Commit (Fast Checks)

```yaml
# .github/workflows/audit-fast-checks.yml
name: Audit Fast Checks

on:
  push:
    branches: [main, 'feature/**']
  pull_request:
    branches: [main]

jobs:
  file-inventory:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Count Source Files
        run: |
          echo "## File Counts" >> $GITHUB_STEP_SUMMARY
          echo "| Category | Count |" >> $GITHUB_STEP_SUMMARY
          echo "|----------|-------|" >> $GITHUB_STEP_SUMMARY
          echo "| Python files | $(find vibey -name '*.py' | wc -l) |" >> $GITHUB_STEP_SUMMARY
          echo "| Test files | $(find tests -name '*.py' | wc -l) |" >> $GITHUB_STEP_SUMMARY
          echo "| YAML files | $(find .vibey -name '*.yaml' | wc -l) |" >> $GITHUB_STEP_SUMMARY
          echo "| Markdown files | $(find docs -name '*.md' | wc -l) |" >> $GITHUB_STEP_SUMMARY

  lint-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install ruff mypy

      - name: Run Ruff
        run: ruff check vibey/ --output-format=github

      - name: Run MyPy
        run: mypy vibey/ --ignore-missing-imports

  test-coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run tests with coverage
        run: pytest tests/ --cov=vibey --cov-fail-under=60 --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml
```

#### 2. On Pull Request (Comprehensive Checks)

```yaml
# .github/workflows/audit-pr-checks.yml
name: Audit PR Checks

on:
  pull_request:
    branches: [main]

jobs:
  documentation-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install vibey
        run: pip install -e .

      - name: Check CLI Reference Drift
        run: vibey docs check-drift --target cli --fail-on-drift

      - name: Check MCP Reference Drift
        run: vibey docs check-drift --target mcp --fail-on-drift

  database-integrity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install vibey
        run: pip install -e .

      - name: Validate database
        run: vibey roadmap db validate

      - name: Check YAML/DB sync
        run: vibey roadmap db status --fail-on-drift

  orphan-detection:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install vibey
        run: pip install -e .

      - name: Check for orphaned tasks
        run: |
          ORPHANS=$(vibey roadmap db query "SELECT COUNT(*) FROM tasks WHERE sprint_id IS NULL")
          if [ "$ORPHANS" -gt 0 ]; then
            echo "::warning::Found $ORPHANS orphaned tasks"
          fi
```

#### 3. Weekly Scheduled Checks

```yaml
# .github/workflows/audit-weekly.yml
name: Weekly Audit Checks

on:
  schedule:
    - cron: '0 9 * * 1'  # Monday 9am UTC
  workflow_dispatch:  # Allow manual trigger

jobs:
  dead-code-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install vulture

      - name: Run Vulture
        run: vulture vibey/ --min-confidence 80 > dead_code_report.txt || true

      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: dead-code-report
          path: dead_code_report.txt

  dependency-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install pip-audit

      - name: Run pip-audit
        run: pip-audit

  stale-documentation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Find stale docs
        run: |
          echo "## Stale Documentation" >> $GITHUB_STEP_SUMMARY
          echo "Files not modified in 90+ days:" >> $GITHUB_STEP_SUMMARY
          find docs -name '*.md' -mtime +90 -exec echo "- {}" \; >> $GITHUB_STEP_SUMMARY
```

#### 4. On Release (Full Regeneration)

```yaml
# .github/workflows/audit-release.yml
name: Release Audit Tasks

on:
  release:
    types: [published]

jobs:
  regenerate-documentation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install vibey
        run: pip install -e .

      - name: Regenerate CLI Reference
        run: vibey docs generate-cli --output docs/reference/CLI_REFERENCE.md

      - name: Regenerate MCP Reference
        run: vibey docs generate-mcp --output docs/reference/MCP_REFERENCE.md

      - name: Commit if changed
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add docs/reference/
          git diff --staged --quiet || git commit -m "docs: auto-regenerate references for ${{ github.ref_name }}"
          git push
```

---

## Recommendations Structure

### Priority Matrix

| Priority | Automation | Impact | Effort | ROI |
|----------|------------|--------|--------|-----|
| P1 | Test coverage CI | High | Low | High |
| P1 | Lint/type checks | High | Low | High |
| P2 | Documentation drift | Medium | Medium | High |
| P2 | Database validation | Medium | Low | Medium |
| P3 | Dead code detection | Low | Low | Medium |
| P3 | Weekly inventory | Low | Low | Low |
| P4 | Full audit re-run | High | High | Medium |

### Implementation Phases

**Phase 1: Essential CI/CD (Week 1)**
- Test coverage with threshold
- Lint and type checking
- Basic file counts

**Phase 2: Documentation Automation (Week 2)**
- CLI/MCP reference drift detection
- Auto-regeneration on release
- Stale doc detection

**Phase 3: Database Integrity (Week 3)**
- Database validation checks
- YAML/DB sync verification
- Orphan detection

**Phase 4: Advanced Monitoring (Month 2)**
- Dead code tracking
- Dependency auditing
- Full inventory automation

---

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| `AUDIT_AUTOMATION_RECOMMENDATIONS.md` | `sprint-6/outputs/` | Full automation analysis |
| `audit-fast-checks.yml` | `.github/workflows/` | Fast commit checks |
| `audit-pr-checks.yml` | `.github/workflows/` | PR validation |
| `audit-weekly.yml` | `.github/workflows/` | Weekly scheduled checks |
| `audit-release.yml` | `.github/workflows/` | Release automation |
| `AUTOMATION_PRIORITY_MATRIX.md` | `sprint-6/outputs/` | Prioritized implementation plan |

---

## Acceptance Criteria

- [ ] All audit outputs cataloged with automation classification
- [ ] Fully automatable outputs have scripts/commands documented
- [ ] Partially automatable outputs have auto/manual split defined
- [ ] Manual-only outputs have clear rationale documented
- [ ] CI/CD triggers identified (commit, PR, weekly, release)
- [ ] GitHub Actions workflow files provided for each trigger
- [ ] Workflows tested locally with `act` or similar
- [ ] Priority matrix ranks all automation opportunities
- [ ] Implementation phases defined with timeline
- [ ] Drift detection integrated into CI pipeline design

---

## Notes

- Coordinate with Task 6.4 (dashboard) - automation feeds dashboard data
- Consider existing `vibey docs check-drift` capability
- Ensure workflows don't exceed GitHub Actions free tier limits
- Document secrets/tokens needed for workflows
- Include workflow badge examples for README.md
