# Sprint 6: Friction & Progress Tracking - Detailed Plan

## Sprint Overview

| Field | Value |
|-------|-------|
| Sprint ID | 01KDJNKE2B2W5NJRTSRZWN4QSR |
| Track | Comprehensive Repository Audit V2 |
| Status | not_started |
| Tasks | 5 |
| Estimated Tokens | ~15,000 |
| Dependencies | Sprint 5 (Remediation complete) |

## Goal

Ensure audit outputs remain accurate and maintainable long-term. Update friction log, validate progress tracking, document automation opportunities, and define maintenance cadence.

---

## Task Details

### Task 6.1: Update FRICTION_LOG.md with Current Pain Points

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QTA`
**Type:** documentation | **Complexity:** simple | **Priority:** medium

#### Description
Update the friction log with pain points discovered during Dec 12-28 development.

#### Known Issues to Document

1. **O(n²) recalculate_all() bug**
   - Severity: High
   - Status: Fixed
   - Root cause: Nested iteration over all tasks
   - Resolution: Optimized to O(n)

2. **v2/v1 YAML format issues**
   - Severity: Medium
   - Status: Fixed
   - Root cause: Mixed format detection
   - Resolution: Standardized on v1 format

3. **Piped input confirmation prompts**
   - Severity: Medium
   - Status: Fixed
   - Root cause: TTY detection not working
   - Resolution: Added `--yes` flag handling

4. **False task completions**
   - Severity: High
   - Status: In progress (this audit)
   - Root cause: No verification on completion
   - Resolution: Add completion criteria

#### Friction Log Template
```markdown
# Development Friction Log

## Entry Format
| ID | Date | Severity | Category | Status |
|----|------|----------|----------|--------|

## Categories
- CLI: Command-line interface issues
- DATA: Data integrity issues
- PERF: Performance issues
- UX: User experience issues
- DEV: Developer experience issues

## Entries

### FRIC-001: O(n²) Performance in recalculate_all()
- **Date:** 2024-12-27
- **Severity:** High
- **Category:** PERF
- **Status:** Resolved
- **Description:** [...]
- **Resolution:** [...]
- **Commit:** [...]
```

#### Deliverables
- Updated `FRICTION_LOG.md`
- Pain point severity matrix
- Resolution status for each

---

### Task 6.2: Validate Progress Tracking Accuracy

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QTB`
**Type:** testing | **Complexity:** medium | **Priority:** high

#### Description
Validate that the roadmap progress tracking (track/sprint/task completion percentages) accurately reflects actual state after all remediation.

#### Implementation Steps

1. **Rebuild database**
   ```bash
   vibey roadmap db rebuild
   ```

2. **Compare CLI output with manual verification**
   ```bash
   # Get CLI progress
   vibey roadmap status > cli_progress.txt

   # Manual calculation
   sqlite3 .vibey/roadmap.db "
     SELECT
       t.name,
       COUNT(CASE WHEN task.status = 'completed' THEN 1 END) as completed,
       COUNT(task.id) as total
     FROM tracks t
     LEFT JOIN sprints s ON s.track_id = t.id
     LEFT JOIN tasks task ON task.sprint_id = s.id
     GROUP BY t.id
   " > manual_progress.txt

   # Compare
   diff cli_progress.txt manual_progress.txt
   ```

3. **Check for discrepancies**
   - Progress counter mismatches
   - Status inconsistencies
   - Orphaned calculations

4. **Document any remaining issues**

#### Deliverables
- `PROGRESS_TRACKING_VALIDATION_REPORT.md`
- List of any discrepancies found
- Recommendations for fixing

---

### Task 6.3: Document Audit Automation Recommendations

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QTC`
**Type:** documentation | **Complexity:** medium | **Priority:** medium

#### Description
Document recommendations for automating audit maintenance. Identify which outputs can be auto-generated vs require manual review.

#### Automation Categories

**Fully Automatable:**
- File counts and inventory
- Test coverage measurements
- Static analysis (ruff, mypy, vulture)
- CLI/MCP reference generation
- Progress percentage calculations

**Partially Automatable:**
- File classification (auto-suggest, human verify)
- Documentation drift detection (detect, human fix)
- Dependency graph generation

**Manual Only:**
- Module quality assessments
- Architectural recommendations
- Friction log entries
- Strategic decisions

#### CI/CD Integration Points
```yaml
# .github/workflows/audit-checks.yml
name: Audit Checks

on:
  push:
    paths:
      - 'vibey/**'
      - 'docs/**'

jobs:
  file-count:
    runs-on: ubuntu-latest
    steps:
      - name: Count files
        run: |
          echo "Python files: $(find vibey -name '*.py' | wc -l)"

  coverage:
    runs-on: ubuntu-latest
    steps:
      - name: Run coverage
        run: pytest --cov=vibey --cov-fail-under=60

  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Ruff check
        run: ruff check vibey/

  docs-drift:
    runs-on: ubuntu-latest
    steps:
      - name: Check drift
        run: vibey docs check-drift --fail-on-drift
```

#### Deliverables
- `AUDIT_AUTOMATION_RECOMMENDATIONS.md`
- Proposed CI/CD workflow files
- Automation priority matrix

---

### Task 6.4: Specify Monitoring Dashboard Requirements

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QTD`
**Type:** documentation | **Complexity:** medium | **Priority:** low

#### Description
Specify requirements for an ongoing monitoring dashboard displaying audit health metrics.

#### Dashboard Metrics

**Code Metrics:**
- File count (by category)
- Test coverage (%)
- Type coverage (%)
- Lint issues (count)
- Dead code items

**Documentation Metrics:**
- Documentation drift (%)
- Stale file count
- Missing documentation

**Roadmap Metrics:**
- Track progress
- Sprint velocity
- Task completion rate
- Orphan count

#### Dashboard Layout
```
┌─────────────────────────────────────────────────────────────┐
│                    AUDIT HEALTH DASHBOARD                   │
├───────────────────┬───────────────────┬─────────────────────┤
│ Code Quality      │ Documentation     │ Roadmap             │
│ ────────────────  │ ────────────────  │ ────────────────    │
│ Coverage: 68% ▲   │ Drift: 3% ▼       │ Progress: 72% ▲     │
│ Types: 45%        │ Stale: 5 files    │ Orphans: 0          │
│ Lint: 12 issues   │ Missing: 2 docs   │ Velocity: 8/week    │
│ Dead code: 3      │                   │                     │
├───────────────────┴───────────────────┴─────────────────────┤
│ Trend (30 days)                                             │
│ [Chart showing metrics over time]                           │
└─────────────────────────────────────────────────────────────┘
```

#### Implementation Options
1. Static HTML generated by script
2. VS Code extension panel
3. Terminal-based (rich library)
4. Web dashboard (future)

#### Deliverables
- `MONITORING_DASHBOARD_SPEC.md`
- Metric definitions
- Update frequency recommendations

---

### Task 6.5: Define Audit Maintenance Cadence and Owners

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QTE`
**Type:** documentation | **Complexity:** simple | **Priority:** medium

#### Description
Define ongoing maintenance cadence for audit outputs. Specify update frequency and ownership.

#### Maintenance Schedule

| Output | Frequency | Owner | Automated? |
|--------|-----------|-------|------------|
| FILE_INVENTORY.yaml | Weekly | AI | Partial |
| FILE_REGISTRY.yaml | Weekly | AI | Partial |
| FILE_DEPENDENCY_GRAPH.yaml | Weekly | AI | Yes |
| Test coverage | Daily | CI | Yes |
| Dead code report | Weekly | CI | Yes |
| CLI_REFERENCE.md | On change | AI | Yes |
| MCP_REFERENCE.md | On change | AI | Yes |
| Module audits | Monthly | AI | No |
| Health scorecard | Monthly | AI | Partial |
| Friction log | On occurrence | Human | No |

#### Ownership Categories
- **AI:** Claude Code or automated agent
- **CI:** Continuous Integration pipeline
- **Human:** Manual human review required

#### Trigger Points
- **On Commit:** File counts, lint checks
- **On Release:** Full documentation regeneration
- **Monthly:** Module quality audits
- **Quarterly:** Comprehensive audit re-run

#### Deliverables
- `AUDIT_MAINTENANCE_SCHEDULE.md`
- Owner assignments
- Trigger definitions

---

## Sprint Execution Order

```
Sprint 5 (complete) ──> Task 6.1 (friction log)
                    ├──> Task 6.2 (validate progress)
                    ├──> Task 6.3 (automation) ──> Task 6.4 (dashboard)
                    └──────────────────────────> Task 6.5 (cadence)
```

## Output Location

```
.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-6/outputs/
```

## Success Criteria

- [ ] All 5 tasks completed
- [ ] Friction log updated with Dec 12-28 issues
- [ ] Progress tracking validated accurate
- [ ] Automation recommendations documented
- [ ] Dashboard requirements specified
- [ ] Maintenance schedule defined
- [ ] Sustainable audit process established
