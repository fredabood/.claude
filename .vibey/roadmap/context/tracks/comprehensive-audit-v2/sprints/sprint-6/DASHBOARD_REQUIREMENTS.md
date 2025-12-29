# Monitoring Dashboard Requirements

## Overview

This document specifies requirements for an ongoing monitoring dashboard to display audit health metrics, track trends, and alert on drift.

**Date**: 2025-12-29
**Track**: Comprehensive Repository Audit V2
**Sprint**: Sprint 6 - Friction & Progress Tracking

---

## Dashboard Sections

### 1. Repository Health Summary

**Purpose**: At-a-glance view of overall repository health

| Metric | Display | Source | Update Frequency |
|--------|---------|--------|------------------|
| Overall Health Score | Gauge (0-100) | Composite | Daily |
| Files Tracked | Number + trend | File inventory | Daily |
| Test Coverage | Percentage + trend | pytest-cov | On commit |
| Documentation Coverage | Percentage | CLI/MCP introspection | Weekly |
| Last Audit Date | Date + staleness | Audit tracker | On update |

**Mockup**:
```
┌─────────────────────────────────────────────────────────────────┐
│  REPOSITORY HEALTH                                    Score: 78 │
├─────────────────────────────────────────────────────────────────┤
│  Files: 847 (+12 this week)    │  Tests: 45% coverage          │
│  Docs: 89% up-to-date          │  Last Audit: 2 days ago       │
└─────────────────────────────────────────────────────────────────┘
```

### 2. File Metrics

**Purpose**: Track file inventory changes over time

| Metric | Visualization | Alert Threshold |
|--------|--------------|-----------------|
| Total file count | Line chart (30 days) | >10% change/day |
| Files by category | Stacked area chart | - |
| New files this week | Bar chart | >50 files |
| Deleted files this week | Bar chart | >20 files |
| Unclassified files | Number (red if >0) | Any |

**Categories to Track**:
- Python source (`vibey/`)
- Tests (`tests/`)
- Documentation (`docs/`)
- Configuration (`.vibey/`, root configs)
- Generated (auto-gen docs, DB)

### 3. Code Quality Metrics

**Purpose**: Monitor code health indicators

| Metric | Source | Target | Alert |
|--------|--------|--------|-------|
| Test coverage | pytest-cov | >70% | <50% |
| Type coverage | mypy | >80% | <60% |
| Linting errors | flake8 | 0 | >10 |
| Cyclomatic complexity | radon | <10 avg | >15 avg |
| Dead code % | vulture | <5% | >10% |

**Trend Charts**:
- Weekly test coverage trend
- Monthly code quality score trend
- PR quality score distribution

### 4. Documentation Health

**Purpose**: Track documentation accuracy and freshness

| Metric | Calculation | Target | Alert |
|--------|-------------|--------|-------|
| CLI Reference Accuracy | Commands documented / actual | 100% | <95% |
| MCP Reference Accuracy | Tools documented / actual | 100% | <95% |
| Walkthrough Freshness | Days since last verification | <30 days | >60 days |
| ADR Coverage | ADRs for major decisions | - | New pattern w/o ADR |

**Drift Indicators**:
- Commands added but not documented (list)
- Commands in docs but not in code (list)
- Documentation files older than 90 days (list)

### 5. Roadmap Progress

**Purpose**: Track development progress across tracks

| Metric | Display | Data Source |
|--------|---------|-------------|
| Active tracks | Count + list | Track YAML status |
| Sprint velocity | Tasks/week trend | Completion dates |
| Blocked items | Count (red) | Blocked flags |
| Overdue tasks | Count (red) | Due dates |

**Progress Bars**:
- Each in-progress track with completion %
- Overall roadmap completion %

### 6. Friction Indicators

**Purpose**: Track developer experience and pain points

| Metric | Source | Update |
|--------|--------|--------|
| CLI command latency | Performance logs | Daily |
| Failed operations rate | Error logs | Daily |
| Database rebuild time | Timing metrics | On rebuild |
| Open friction items | Friction log | Manual |

---

## Technical Requirements

### Data Collection

```yaml
data_sources:
  file_inventory:
    method: Python script scan
    storage: YAML + time-series DB
    frequency: daily

  test_coverage:
    method: pytest-cov JSON output
    storage: time-series DB
    frequency: on commit

  documentation:
    method: CLI introspection + diff
    storage: YAML snapshots
    frequency: weekly

  roadmap:
    method: YAML file parsing
    storage: SQLite (existing)
    frequency: on change
```

### Storage Requirements

| Data Type | Storage | Retention |
|-----------|---------|-----------|
| Daily metrics | Time-series DB | 1 year |
| Weekly snapshots | YAML files | 6 months |
| Trend data | Aggregated | 2 years |
| Alerts history | Log files | 90 days |

### Dashboard Technology Options

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **GitHub Pages + Chart.js** | Free, git-native, simple | Limited interactivity | MVP |
| **Grafana** | Rich visualizations, alerting | Requires hosting | Production |
| **CLI Dashboard** | No hosting, integrated | Limited display | Development |
| **Notion/Confluence** | Easy to share | Manual updates | Documentation |

**Recommended**: Start with CLI dashboard for development, migrate to GitHub Pages for MVP, consider Grafana for production.

### CLI Dashboard Preview

```
vibey dashboard

┌──────────────────── VIBEY HEALTH DASHBOARD ─────────────────────┐
│                                                                  │
│  HEALTH SCORE: 78/100                 Last Updated: 2 min ago   │
│  ═══════════════════════════════════                            │
│                                                                  │
│  FILES          TESTS           DOCS            ROADMAP          │
│  ──────────     ──────────      ──────────      ──────────       │
│  847 total      45% coverage    89% accurate    42% complete    │
│  +12 this week  ▲ 3% trend      ✓ No drift      3 tracks active │
│                                                                  │
│  ALERTS (2)                                                      │
│  ──────────────────────────────────────────────────────────────  │
│  ⚠ Test coverage below 50% threshold                           │
│  ⚠ 2 CLI commands not in documentation                          │
│                                                                  │
│  RECENT CHANGES                                                  │
│  ──────────────────────────────────────────────────────────────  │
│  • Sprint 6 started (Audit V2)                                  │
│  • 3 tasks completed today                                       │
│  • File inventory +12 files                                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Alert Configuration

### Critical Alerts (Immediate)

| Condition | Alert | Channel |
|-----------|-------|---------|
| Test coverage <40% | Critical | Slack, Email |
| CLI startup fails | Critical | Slack, Email |
| Database corruption | Critical | Slack, Email |

### Warning Alerts (Daily Digest)

| Condition | Alert | Channel |
|-----------|-------|---------|
| Documentation drift detected | Warning | Daily email |
| Unclassified files >5 | Warning | Daily email |
| Progress counter stale >7 days | Warning | Daily email |

### Info Alerts (Weekly Report)

| Condition | Alert | Channel |
|-----------|-------|---------|
| File count change >5% | Info | Weekly report |
| New track created | Info | Weekly report |
| Sprint completed | Info | Weekly report |

---

## Implementation Phases

### Phase 1: CLI Dashboard (Week 1)

- [ ] Add `vibey dashboard` command
- [ ] Display basic metrics (files, coverage, roadmap)
- [ ] Add color-coded health indicators

### Phase 2: Data Collection (Week 2)

- [ ] Create metric collection scripts
- [ ] Set up daily cron job
- [ ] Store historical data in YAML

### Phase 3: Web Dashboard (Week 3-4)

- [ ] Generate static HTML from metrics
- [ ] Add Chart.js visualizations
- [ ] Deploy to GitHub Pages

### Phase 4: Alerting (Week 5)

- [ ] Implement threshold checking
- [ ] Add GitHub Action for alerts
- [ ] Configure notification channels

---

## Success Criteria

| Criteria | Measurement | Target |
|----------|-------------|--------|
| Dashboard load time | CLI response time | <2 seconds |
| Data freshness | Time since last update | <24 hours |
| Alert accuracy | False positive rate | <10% |
| User adoption | Weekly views | >5/week |

---

## Dependencies

- pytest-cov (test coverage)
- mypy (type coverage)
- flake8 (linting)
- radon (complexity)
- vulture (dead code)
- rich (CLI display)
- Chart.js (web visualization)

---

## Appendix: Metric Definitions

### Health Score Calculation

```python
health_score = (
    test_coverage * 0.25 +
    doc_accuracy * 0.20 +
    code_quality * 0.20 +
    roadmap_progress * 0.15 +
    file_organization * 0.10 +
    freshness * 0.10
) * 100
```

### Trend Calculation

```python
# 7-day trend
current = metrics[-1]
previous = metrics[-8] if len(metrics) >= 8 else metrics[0]
trend = ((current - previous) / previous) * 100
```
