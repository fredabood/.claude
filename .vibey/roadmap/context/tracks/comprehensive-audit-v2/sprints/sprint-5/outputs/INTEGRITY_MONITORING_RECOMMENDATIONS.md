# Ongoing Integrity Monitoring Recommendations

**Task:** 01KDJKTRVZS618BM5ZZTQ3443J
**Sprint:** Sprint 5 - Remediation & Reporting
**Generated:** 2025-12-28T22:55:00+00:00

---

## Executive Summary

This document establishes recommendations for ongoing data integrity monitoring to maintain the health improvements achieved during the Comprehensive Repository Audit V2.

---

## 1. Automated CI/CD Checks

### GitHub Actions Workflows

#### Roadmap Integrity Check (Recommended)

```yaml
# .github/workflows/roadmap-integrity.yml
name: Roadmap Integrity

on:
  push:
    paths:
      - '.vibey/roadmap/**'
  pull_request:
    paths:
      - '.vibey/roadmap/**'

jobs:
  integrity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .
      - name: Rebuild and validate database
        run: vibey roadmap db rebuild
      - name: Check for orphans
        run: |
          count=$(sqlite3 .vibey/roadmap.db "
            SELECT COUNT(*) FROM tasks t
            LEFT JOIN sprints s ON t.sprint_id = s.id
            WHERE s.id IS NULL
          ")
          if [ "$count" -gt 0 ]; then
            echo "ERROR: Found $count orphan tasks"
            exit 1
          fi
```

#### Documentation Drift Check (Existing - Enhance)

```yaml
# .github/workflows/docs-drift.yml
name: Documentation Drift

on:
  push:
    paths:
      - 'vibey/cli/**'
      - 'vibey/mcp/**'
      - 'docs/reference/**'

jobs:
  check-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .
      - name: Check CLI Reference drift
        run: vibey docs check-drift
      - name: Check MCP Reference drift
        run: vibey docs check-mcp-drift
```

#### Static Analysis Check

```yaml
# .github/workflows/static-analysis.yml
name: Static Analysis

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install ruff mypy
      - name: Ruff check (errors only)
        run: ruff check --select=F821,F401 --output-format=github vibey/
      - name: Type check
        run: mypy vibey/ --ignore-missing-imports
```

---

## 2. Pre-commit Hooks

### Recommended .pre-commit-config.yaml

```yaml
repos:
  - repo: local
    hooks:
      - id: roadmap-db-rebuild
        name: Rebuild roadmap database
        entry: vibey roadmap db rebuild --force
        language: system
        files: '\.vibey/roadmap/.*\.yaml$'
        pass_filenames: false

      - id: check-orphans
        name: Check for orphan entities
        entry: bash -c '
          count=$(sqlite3 .vibey/roadmap.db "
            SELECT COUNT(*) FROM (
              SELECT 1 FROM tasks t LEFT JOIN sprints s ON t.sprint_id = s.id WHERE s.id IS NULL
              UNION ALL
              SELECT 1 FROM sprints s LEFT JOIN tracks t ON s.track_id = t.id WHERE t.id IS NULL
            )
          ")
          if [ "$count" -gt 0 ]; then exit 1; fi
        '
        language: system
        files: '\.vibey/roadmap/.*\.yaml$'
        pass_filenames: false

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
```

### Installation

```bash
pip install pre-commit
pre-commit install
```

---

## 3. Periodic Audit Schedule

### Weekly Checks (Automated)
- Roadmap YAML ↔ SQLite sync validation
- Orphan entity detection
- Documentation drift detection

### Monthly Checks (Manual)
- Dead code analysis with vulture
- Test coverage review
- MCP tool coverage assessment

### Quarterly Checks (Manual)
- Full codebase health scorecard regeneration
- ADR review and updates
- User journey verification
- Architecture compliance review

---

## 4. Drift Detection Process

### Documentation Drift

```bash
# Quick check
vibey docs check-drift

# Auto-fix
vibey docs check-drift --fix
vibey docs check-mcp-drift --fix
```

### Database Drift

```bash
# Check sync status
vibey roadmap db status

# Force rebuild from YAML
vibey roadmap db rebuild --force
```

### CLAUDE.md Statistics

Review and update monthly:
- CLI command count
- MCP tool count
- Platform adapter count
- Database table count

---

## 5. Escalation Procedures

### Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| Critical | Data loss, orphaned entities | Immediate |
| High | Broken references, false completions | 24 hours |
| Medium | Documentation drift, missing tests | 1 week |
| Low | Style issues, minor inconsistencies | Next sprint |

### Escalation Path

1. **Automated Alert** (CI fails) → Create issue
2. **Issue Created** → Assign to on-call developer
3. **Critical/High** → Block PR merge until resolved
4. **Medium/Low** → Add to backlog

---

## 6. Monitoring Dashboard Metrics

### Key Health Indicators

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Orphan entities | 0 | 1-5 | >5 |
| YAML/DB sync | 100% | 95-99% | <95% |
| Documentation drift | 0 files | 1-2 files | >2 files |
| F821 errors | 0 | 1-10 | >10 |
| Test pass rate | >99% | 95-99% | <95% |

### Tracking Commands

```bash
# Quick health check
vibey roadmap db status
vibey docs check-drift
pytest tests/ -x -q --tb=no

# Full health scorecard (monthly)
ruff check vibey/ --statistics
mypy vibey/ --ignore-missing-imports | wc -l
vulture vibey/ --min-confidence 80 | wc -l
pytest tests/ --collect-only -q | tail -1
```

---

## 7. CLI Commands for Monitoring

### Existing Commands

```bash
vibey roadmap db status      # Database sync status
vibey roadmap db validate    # Validate integrity
vibey roadmap db rebuild     # Force rebuild
vibey docs check-drift       # CLI reference drift
vibey docs check-mcp-drift   # MCP reference drift
```

### Recommended New Commands

```bash
vibey health check           # Combined health check
vibey health scorecard       # Generate health scorecard
vibey health orphans         # Check for orphan entities
vibey health stale           # Find stale in-progress items
```

---

## 8. Baseline Tracking

Update these baselines quarterly:

| Metric | Baseline (Dec 2025) | Q1 2026 | Q2 2026 |
|--------|---------------------|---------|---------|
| Tracks | 53 | - | - |
| Sprints | 293 | - | - |
| Tasks | 1872 | - | - |
| Tests | 4,754 | - | - |
| Ruff issues | 6,783 | - | - |
| Mypy errors | 133 | - | - |
| MCP coverage | 16% | - | - |

---

## 9. Integration with Development Workflow

### Branch Protection Rules

Configure GitHub branch protection:
- Require status checks: `roadmap-integrity`, `docs-drift`
- Require CI to pass before merge
- Block force push to main

### PR Template Addition

```markdown
## Integrity Checklist
- [ ] Ran `vibey roadmap db rebuild` if YAML changed
- [ ] Verified no orphan entities created
- [ ] Checked documentation drift if CLI/MCP changed
- [ ] Tests pass locally
```

---

## 10. Tool Recommendations

| Tool | Purpose | Current Status |
|------|---------|----------------|
| vibey CLI | Roadmap management | In use |
| ruff | Linting | Configured |
| mypy | Type checking | Configured |
| vulture | Dead code detection | Manual |
| pytest | Testing | In use |
| pre-commit | Git hooks | Recommended |
| GitHub Actions | CI/CD | Partial |

---

## Summary

Implementing these monitoring recommendations will:

1. **Prevent** orphan entities and broken references through pre-commit hooks
2. **Detect** documentation drift automatically in CI/CD
3. **Track** health metrics over time with baseline comparisons
4. **Escalate** issues promptly through defined procedures
5. **Maintain** the B+ health grade achieved in this audit

---

*Report generated: 2025-12-28T22:55:00+00:00*
