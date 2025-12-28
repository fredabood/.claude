# Task 6.3: Specify Monitoring Dashboard Requirements

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJNKE2B2W5NJRTSRZWN4QTD |
| Sprint | 6 - Friction & Progress Tracking |
| Type | documentation |
| Complexity | medium |
| Priority | low |
| Estimated Tokens | ~2,500 |
| Dependencies | Task 6.2 (automation recommendations inform data sources) |

---

## Objective

Specify requirements for an ongoing monitoring dashboard that displays audit health metrics. Define the metrics to track, their data sources, refresh intervals, and implementation options. Provide mockups/wireframes to visualize the dashboard layout.

---

## Analysis Approach

### Phase 1: Identify Stakeholders and Use Cases

**Primary Users:**
- Solo developers monitoring project health
- Team leads tracking progress
- AI assistants checking audit status

**Key Use Cases:**
- Quick health check during daily standup
- Identify degradation before it becomes critical
- Track trends over time (weekly/monthly)
- Surface actionable items requiring attention

### Phase 2: Define Metrics

Categorize metrics by domain and importance.

### Phase 3: Specify Data Sources

Map each metric to its data source and collection method.

### Phase 4: Design Dashboard Layout

Create wireframes showing metric organization and visual hierarchy.

---

## Metrics Specification

### Code Quality Metrics

| Metric | Description | Target | Warning | Critical |
|--------|-------------|--------|---------|----------|
| Test Coverage | Percentage of code covered by tests | >= 70% | 60-69% | < 60% |
| Type Coverage | Percentage of code with type hints | >= 50% | 40-49% | < 40% |
| Lint Issues | Count of ruff/flake8 violations | 0 | 1-10 | > 10 |
| Dead Code Items | Vulture-detected unused code | <= 5 | 6-15 | > 15 |
| Cyclomatic Complexity | Average complexity score | <= 10 | 11-15 | > 15 |
| Security Vulnerabilities | pip-audit findings | 0 | 1-2 | > 2 |

### Documentation Metrics

| Metric | Description | Target | Warning | Critical |
|--------|-------------|--------|---------|----------|
| Documentation Drift | CLI/MCP docs out of sync | 0% | 1-5% | > 5% |
| Stale Files | Docs not updated in 90+ days | <= 5 | 6-10 | > 10 |
| Missing Documentation | Modules without docstrings | <= 10% | 11-20% | > 20% |
| README Freshness | Days since README updated | <= 30 | 31-90 | > 90 |

### Roadmap Metrics

| Metric | Description | Target | Warning | Critical |
|--------|-------------|--------|---------|----------|
| Track Progress | Active track completion % | >= 80% | 50-79% | < 50% |
| Sprint Velocity | Tasks completed per week | >= 5 | 3-4 | < 3 |
| Task Completion Rate | Completed / Total tasks | Trending up | Flat | Trending down |
| Orphaned Tasks | Tasks without parent sprint | 0 | 1-3 | > 3 |
| Blocked Items | Tasks marked blocked | 0 | 1-2 | > 2 |

### Repository Metrics

| Metric | Description | Target | Warning | Critical |
|--------|-------------|--------|---------|----------|
| Python File Count | Number of .py files | Stable | +/- 10% | +/- 25% |
| Test File Count | Number of test files | Stable | +/- 10% | +/- 25% |
| Lines of Code | Total LOC in vibey/ | N/A | N/A | N/A |
| Test/Code Ratio | Test files / Source files | >= 0.5 | 0.3-0.49 | < 0.3 |

---

## Data Sources

### Metric Data Collection

| Metric | Data Source | Collection Method | Refresh |
|--------|-------------|-------------------|---------|
| Test Coverage | pytest --cov | CI pipeline | On commit |
| Type Coverage | mypy --stats | CI pipeline | On commit |
| Lint Issues | ruff check --statistics | CI pipeline | On commit |
| Dead Code | vulture output | Weekly job | Weekly |
| Doc Drift | vibey docs check-drift | CI pipeline | On PR |
| Track Progress | vibey roadmap status | CLI query | On demand |
| Sprint Velocity | SQLite: tasks table | Direct query | Daily |
| File Counts | find command | Script | Weekly |

### SQLite Queries for Roadmap Metrics

```sql
-- Track progress
SELECT
  t.name,
  COUNT(CASE WHEN task.status = 'completed' THEN 1 END) * 100.0 / COUNT(task.id) as progress
FROM tracks t
LEFT JOIN sprints s ON s.track_id = t.id
LEFT JOIN tasks task ON task.sprint_id = s.id
WHERE t.status = 'active'
GROUP BY t.id;

-- Sprint velocity (last 7 days)
SELECT COUNT(*) as completed_this_week
FROM tasks
WHERE status = 'completed'
  AND completed >= datetime('now', '-7 days');

-- Orphaned tasks
SELECT COUNT(*) as orphan_count
FROM tasks
WHERE sprint_id IS NULL;

-- Blocked items
SELECT COUNT(*) as blocked_count
FROM tasks
WHERE status = 'blocked';
```

### CLI Commands for Data

```bash
# Test coverage
pytest tests/ --cov=vibey --cov-report=json

# Lint issues count
ruff check vibey/ --statistics 2>&1 | tail -1

# Documentation drift
vibey docs check-drift --json

# Roadmap progress
vibey roadmap status --json

# File counts
find vibey -name '*.py' | wc -l
find tests -name '*.py' | wc -l
```

---

## Refresh Intervals

| Category | Interval | Rationale |
|----------|----------|-----------|
| Code Quality | On commit | Changes frequently, critical feedback |
| Documentation | On PR | Only relevant when docs might change |
| Roadmap | On demand | User initiates when checking progress |
| File Inventory | Weekly | Changes slowly, low urgency |
| Trends | Daily aggregation | Historical tracking |

---

## Dashboard Layout

### Primary Dashboard Wireframe

```
+===========================================================================+
|                        VIBEY AUDIT HEALTH DASHBOARD                        |
|                          Last updated: Dec 28, 2024 10:30 AM              |
+===========================================================================+

+----------------------------+  +----------------------------+  +----------------------------+
|       CODE QUALITY         |  |      DOCUMENTATION         |  |         ROADMAP            |
|----------------------------|  |----------------------------|  |----------------------------|
|                            |  |                            |  |                            |
|  Coverage    [====68%====] |  |  Drift       [===3%====  ] |  |  Progress   [====72%====] |
|  Types       [==45%==    ] |  |  Stale       5 files       |  |  Velocity   8/week         |
|  Lint        12 issues     |  |  Missing     2 modules     |  |  Orphans    0              |
|  Dead Code   3 items       |  |  README      Updated 5d    |  |  Blocked    0              |
|                            |  |                            |  |                            |
|  [View Details]            |  |  [View Details]            |  |  [View Details]            |
+----------------------------+  +----------------------------+  +----------------------------+

+===========================================================================+
|                              TREND (30 DAYS)                               |
+===========================================================================+
|                                                                           |
|  100% |                                                    ___--"""       |
|       |                                           ___--"""               |
|   75% |                                  ___--"""                         |
|       |                         ___--"""                                 |
|   50% |                ___--"""                                          |
|       |       ___--"""                                                   |
|   25% |___--""                                                           |
|       +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+     |
|       Nov28 Dec01 Dec05 Dec08 Dec12 Dec15 Dec18 Dec21 Dec24 Dec28       |
|                                                                           |
|   --- Coverage   --- Progress   --- Drift                                |
+===========================================================================+

+===========================================================================+
|                            ACTION ITEMS                                    |
+===========================================================================+
|                                                                           |
|  [!] CRITICAL: 0 items                                                   |
|                                                                           |
|  [!] WARNING: 2 items                                                    |
|      - Test coverage below 70% target (currently 68%)                    |
|      - 5 documentation files stale (>90 days)                            |
|                                                                           |
|  [i] INFO: 3 items                                                       |
|      - Sprint 6 in progress (3/5 tasks complete)                        |
|      - 12 lint issues to address                                         |
|      - Dead code detected in 3 files                                     |
|                                                                           |
+===========================================================================+
```

### Detail Panel Wireframes

#### Code Quality Detail

```
+===========================================================================+
|                        CODE QUALITY DETAILS                                |
+===========================================================================+

## Test Coverage by Module

| Module     | Statements | Covered | Coverage | Target | Status |
|------------|------------|---------|----------|--------|--------|
| cli        | 2,450      | 1,715   | 70%      | 70%    | OK     |
| operations | 1,890      | 1,512   | 80%      | 80%    | OK     |
| roadmap    | 1,200      | 780     | 65%      | 75%    | WARN   |
| mcp        | 980        | 588     | 60%      | 60%    | OK     |
| adapters   | 640        | 320     | 50%      | 50%    | OK     |
| common     | 380        | 304     | 80%      | 80%    | OK     |
| TOTAL      | 7,540      | 5,219   | 68%      | 70%    | WARN   |

## Lint Issues

| Category          | Count | Severity |
|-------------------|-------|----------|
| Missing docstring | 5     | Low      |
| Line too long     | 4     | Low      |
| Unused import     | 2     | Medium   |
| Type error        | 1     | High     |

## Dead Code (Vulture)

| File                      | Item              | Confidence |
|---------------------------|-------------------|------------|
| vibey/cli/legacy.py       | old_command()     | 90%        |
| vibey/adapters/unused.py  | DeprecatedAdapter | 85%        |
| vibey/common/helpers.py   | temp_function()   | 80%        |
```

#### Roadmap Detail

```
+===========================================================================+
|                          ROADMAP DETAILS                                   |
+===========================================================================+

## Active Tracks

| Track                           | Progress | Sprints | Status     |
|---------------------------------|----------|---------|------------|
| Comprehensive Repository Audit  | 85%      | 6/6     | In Progress|
| Context System V2               | 45%      | 2/4     | In Progress|

## Current Sprint: Sprint 6 - Friction & Progress Tracking

| Task | Title                              | Status      | Priority |
|------|------------------------------------|-------------|----------|
| 6.1  | Update FRICTION_LOG.md             | Completed   | Medium   |
| 6.2  | Document automation recommendations | In Progress | Medium   |
| 6.3  | Specify dashboard requirements      | Not Started | Low      |
| 6.4  | Validate progress tracking          | Not Started | High     |
| 6.5  | Define maintenance cadence          | Not Started | Medium   |

## Velocity Chart (Tasks/Week)

Week     | Completed | Target
---------|-----------|--------
Dec 1-7  | 6         | 5
Dec 8-14 | 8         | 5
Dec 15-21| 7         | 5
Dec 22-28| 4*        | 5

* Current week (in progress)
```

---

## Implementation Options

### Option 1: Terminal-Based (Recommended for MVP)

**Technology:** Python `rich` library

**Pros:**
- No external dependencies beyond Python
- Integrates with existing CLI
- Fast, lightweight
- Works in any terminal

**Cons:**
- Limited interactivity
- No persistent display

**Command:**
```bash
vibey audit dashboard
vibey audit dashboard --watch  # Auto-refresh
```

### Option 2: Static HTML Report

**Technology:** Jinja2 templates + GitHub Pages

**Pros:**
- Shareable via URL
- Browsable history
- Works offline

**Cons:**
- Requires regeneration
- No real-time updates

**Command:**
```bash
vibey audit dashboard --format html --output dashboard.html
```

### Option 3: VS Code Extension Panel

**Technology:** VS Code Webview API

**Pros:**
- Integrated into IDE
- Real-time updates possible
- Interactive

**Cons:**
- VS Code only
- Complex implementation
- Maintenance burden

### Option 4: Web Dashboard (Future)

**Technology:** FastAPI + React/Vue

**Pros:**
- Full interactivity
- Real-time updates
- Rich visualizations

**Cons:**
- Requires server
- Complex deployment
- Overkill for small projects

### Recommendation

Implement in phases:
1. **Phase 1 (MVP):** Terminal-based with `rich` library
2. **Phase 2:** Static HTML for sharing
3. **Phase 3:** VS Code extension (if demand exists)

---

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| `MONITORING_DASHBOARD_SPEC.md` | `sprint-6/outputs/` | Full specification document |
| `dashboard_wireframes.md` | `sprint-6/outputs/` | ASCII wireframes and mockups |
| `METRIC_DEFINITIONS.yaml` | `sprint-6/outputs/` | Machine-readable metric specs |
| `DATA_SOURCE_MAPPING.yaml` | `sprint-6/outputs/` | Metric to data source mapping |

---

## Acceptance Criteria

- [ ] All metrics defined with targets, warnings, and critical thresholds
- [ ] Data sources identified for each metric
- [ ] Refresh intervals specified and justified
- [ ] Primary dashboard wireframe completed
- [ ] Detail panel wireframes for each category
- [ ] At least 3 implementation options evaluated
- [ ] MVP implementation option recommended
- [ ] Trend visualization requirements specified
- [ ] Action items/alerts system designed
- [ ] Integration with existing `vibey` CLI considered

---

## Notes

- Dashboard feeds from Task 6.2 automation outputs
- Consider dark mode support for terminal dashboard
- Keep ASCII art compatible with common monospace fonts
- Metrics should be exportable for external tools (JSON format)
- Consider GitHub Actions badge integration for README
