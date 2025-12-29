# Audit Maintenance Schedule

## Overview

This document defines the ongoing maintenance cadence, ownership, and responsibilities for audit outputs to ensure they remain accurate and valuable over time.

**Date**: 2025-12-29
**Track**: Comprehensive Repository Audit V2
**Sprint**: Sprint 6 - Friction & Progress Tracking

---

## Ownership Categories

| Category | Description | Trigger |
|----------|-------------|---------|
| **Automated** | Fully automated, no human intervention | CI/CD, cron |
| **AI-Assisted** | AI generates, human reviews | PR, scheduled |
| **Manual Review** | Human judgment required | Calendar, event |

---

## Maintenance Cadence Matrix

### Daily (Automated)

| Output | Location | Owner | Automation |
|--------|----------|-------|------------|
| Database rebuild | `.vibey/roadmap.db` | CI/CD | Pre-commit hook |
| Progress sync | Track/Sprint YAML | CI/CD | On task completion |
| File count metrics | Dashboard data | Cron job | Daily at midnight |

### Weekly (AI-Assisted + Review)

| Output | Location | Owner | Review Day |
|--------|----------|-------|------------|
| File Inventory | `FILE_INVENTORY.yaml` | AI + Dev | Monday |
| Dependency Graph | `FILE_DEPENDENCY_GRAPH.yaml` | AI + Dev | Monday |
| CLI Reference | `docs/reference/CLI_REFERENCE.md` | AI + Dev | Tuesday |
| MCP Reference | `docs/reference/MCP_REFERENCE.md` | AI + Dev | Tuesday |
| Quality Metrics | `QUALITY_METRICS_BASELINE.md` | Automated | Wednesday |

**Weekly Process**:
1. Monday AM: AI regenerates inventory and dependency outputs
2. Monday PM: Developer reviews diffs
3. Tuesday: Documentation drift check and update
4. Wednesday: Quality metrics refresh
5. Friday: Weekly summary in activity log

### Monthly (Manual Review)

| Output | Location | Owner | Review Week |
|--------|----------|-------|-------------|
| Friction Log | `FRICTION_LOG.md` | Dev Lead | Week 1 |
| Roadmap Health | Track status review | Project Lead | Week 2 |
| User Journeys | `docs/journeys/` | UX/Docs | Week 3 |
| Walkthroughs | `docs/walkthroughs/` | Dev + Docs | Week 4 |

**Monthly Process**:
1. Week 1: Update friction log with new pain points, close resolved
2. Week 2: Review track progress, adjust priorities
3. Week 3: Verify user journeys match current functionality
4. Week 4: Test all walkthrough steps end-to-end

### Quarterly (Strategic Review)

| Output | Location | Owner | Review Month |
|--------|----------|-------|--------------|
| ADRs | `docs/architecture/adr/` | Tech Lead | Q1, Q2, Q3, Q4 |
| CLAUDE.md | `/CLAUDE.md` | Dev Lead | Quarterly |
| Coverage Matrix | `COVERAGE_MATRIX.md` | QA Lead | Quarterly |
| Architecture Diagrams | `docs/architecture/` | Architect | Quarterly |

**Quarterly Process**:
1. Review all ADRs for relevance, create new ones for major decisions
2. Update CLAUDE.md with new statistics, patterns, guidelines
3. Regenerate coverage matrix with current file counts
4. Validate architecture diagrams match implementation

---

## Ownership Assignments

### Role Definitions

| Role | Responsibilities | Backup |
|------|-----------------|--------|
| **Dev Lead** | Friction log, CLAUDE.md, code quality | Any senior dev |
| **Tech Lead** | ADRs, architecture, major decisions | Dev Lead |
| **Project Lead** | Roadmap health, priorities, track reviews | Dev Lead |
| **QA Lead** | Coverage matrix, test health, quality metrics | Dev Lead |
| **Docs Lead** | User journeys, walkthroughs, references | Dev Lead |

### RACI Matrix

| Output | Responsible | Accountable | Consulted | Informed |
|--------|-------------|-------------|-----------|----------|
| File Inventory | CI/Automation | Dev Lead | - | Team |
| CLI Reference | CI/Automation | Docs Lead | Dev Team | Team |
| Friction Log | Dev Lead | Tech Lead | Team | Stakeholders |
| ADRs | Author | Tech Lead | Team | Stakeholders |
| Roadmap Status | PM | Project Lead | Dev Lead | Stakeholders |

---

## Automation Setup

### Required Cron Jobs

```crontab
# Daily at midnight: Regenerate file metrics
0 0 * * * /path/to/scripts/generate_metrics.py

# Weekly Monday 6am: Regenerate inventory
0 6 * * 1 /path/to/scripts/generate_inventory.py

# Weekly Wednesday 6am: Update quality metrics
0 6 * * 3 /path/to/scripts/update_quality.py
```

### GitHub Actions Triggers

```yaml
# .github/workflows/maintenance.yml
on:
  schedule:
    - cron: '0 6 * * 1'  # Weekly Monday
  push:
    paths:
      - 'vibey/**'
      - 'docs/**'
```

---

## Escalation Procedures

### Staleness Alerts

| Condition | Alert Level | Action Required |
|-----------|-------------|-----------------|
| Output >7 days stale | Warning | Regenerate within 48h |
| Output >14 days stale | Urgent | Escalate to owner |
| Output >30 days stale | Critical | Review for removal |

### Escalation Path

1. **Owner** attempts update
2. **Backup** if owner unavailable (>48h)
3. **Dev Lead** if backup unavailable
4. **Tech Lead** for strategic decisions

---

## Calendar Integration

### Recurring Meetings

| Meeting | Frequency | Attendees | Duration |
|---------|-----------|-----------|----------|
| Audit Review | Weekly (Tue) | Dev Lead, QA | 30 min |
| Documentation Sync | Biweekly (Wed) | Docs Lead, Dev | 30 min |
| Roadmap Review | Monthly (1st Thu) | All Leads | 60 min |
| Architecture Review | Quarterly | Tech Lead, Architect | 90 min |

### Calendar Events to Create

```
Weekly Audit Review
- Every Tuesday 10:00-10:30
- Attendees: Dev Lead, QA Lead
- Agenda: Review weekly audit outputs, address drift

Monthly Friction Review
- 1st Monday of month 14:00-14:30
- Attendees: Dev Lead, Tech Lead
- Agenda: Update friction log, prioritize fixes

Quarterly ADR Review
- Jan/Apr/Jul/Oct 1st week, 60 min
- Attendees: Tech Lead, Architect, Dev Lead
- Agenda: Review ADRs, create new ones, retire obsolete
```

---

## Metrics for Schedule Adherence

| Metric | Target | Measurement |
|--------|--------|-------------|
| Daily automation success rate | 99% | CI pass rate |
| Weekly review completion | 100% | Checklist completion |
| Monthly review completion | 100% | Meeting held |
| Staleness violations | 0 | Alert count |

---

## Continuous Improvement

### Monthly Review Checklist

- [ ] Were all scheduled updates completed?
- [ ] Were any staleness alerts triggered?
- [ ] Are any outputs consistently problematic?
- [ ] Should any cadence be adjusted?
- [ ] Are ownership assignments working?

### Quarterly Adjustment Process

1. Review adherence metrics
2. Collect feedback from owners
3. Identify bottlenecks
4. Propose schedule adjustments
5. Update this document

---

## Appendix: Output File Locations

### Audit Outputs

| Output | Path |
|--------|------|
| File Inventory | `.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/FILE_INVENTORY_V2.yaml` |
| Dependency Graph | `.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/FILE_DEPENDENCY_GRAPH_V2.yaml` |
| Quality Metrics | `.vibey/roadmap/context/tracks/comprehensive-audit-v2/QUALITY_METRICS_BASELINE.md` |
| Coverage Matrix | (to be created in Sprint 7) |
| Friction Log | `.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-6/FRICTION_LOG.md` |

### Documentation Outputs

| Output | Path |
|--------|------|
| CLI Reference | `docs/reference/CLI_REFERENCE.md` |
| MCP Reference | `docs/reference/MCP_REFERENCE.md` |
| ADRs | `docs/architecture/adr/*.md` |
| User Journeys | `docs/journeys/*.md` |
| Walkthroughs | `docs/walkthroughs/*.md` |

---

## Document History

| Date | Author | Change |
|------|--------|--------|
| 2025-12-29 | Claude | Initial creation as part of Sprint 6 |
