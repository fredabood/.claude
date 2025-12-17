# Project Lead Journey

> **Note:** This document has been consolidated into action-oriented walkthroughs.
> See [ROADMAP_MANAGEMENT.md](../walkthroughs/ROADMAP_MANAGEMENT.md) and
> [REPORTING_AND_STATUS.md](../walkthroughs/REPORTING_AND_STATUS.md) for current guides.

> Managing roadmaps and coordinating work across tracks

**Persona:** Pat the Project Lead
**Duration:** 3-5 hours weekly for roadmap management

---

## Journey Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PROJECT LEAD JOURNEY                                 │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┤
│ Planning    │ Setup       │ Monitoring  │ Reporting   │ Adjustment          │
│ (weekly)    │ (as needed) │ (daily)     │ (weekly)    │ (as needed)         │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ - Define    │ - Create    │ - Check     │ - Generate  │ - Reprioritize      │
│   scope     │   tracks    │   progress  │   summaries │ - Resolve blockers  │
│ - Estimate  │ - Create    │ - Review    │ - Share     │ - Restructure       │
│   work      │   sprints   │   blockers  │   status    │   roadmap           │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────────┘
```

---

## Weekly Workflow

### Monday: Planning Session

**Duration:** 1-2 hours
**Goal:** Set the week's priorities and ensure roadmap is current

```bash
# Get comprehensive status
vibey roadmap status --verbose

# Review all tracks
vibey roadmap show track --all

# Check sprint progress
vibey roadmap show sprint <current-sprint> --detailed

# Review project evolution via discovery
vibey discover history --limit 5
# Compare recent changes to understand project growth
vibey discover diff

# Identify blockers
vibey roadmap list-blockers --all-tracks

# Generate planning summary
vibey roadmap summarize --output weekly-planning.md
```

**Project Evolution Tracking:** Use `vibey discover history` to see how the project
has evolved over time. This helps in planning by showing:
- New dependencies added (may need documentation/training)
- Growth in file count (may need architecture review)
- Changes in patterns/conventions (ensure consistency)

### Daily: Quick Check

**Duration:** 15-30 minutes
**Goal:** Monitor progress and catch issues early

```bash
# Quick status check
vibey roadmap status

# Review recent activity
vibey roadmap activity --since yesterday

# Check for new blockers
vibey roadmap list-blockers

# Auto-update progress counters
vibey roadmap auto-progress --check
```

### Friday: Reporting

**Duration:** 30-60 minutes
**Goal:** Generate status reports for stakeholders

```bash
# Generate sprint summary
vibey roadmap summarize --type sprint --format markdown

# Export progress data
vibey roadmap export --format json --output progress.json

# Create checkpoint
vibey roadmap checkpoint --message "Week ending $(date +%Y-%m-%d)"
```

---

## Core Operations

### Creating Roadmap Structure

#### Create a Track

```bash
vibey roadmap create-track \
  --name "Feature X Development" \
  --description "Complete implementation of Feature X" \
  --priority high
```

#### Create Sprints

```bash
vibey roadmap create-sprint \
  --track <track-id> \
  --name "Sprint 1: Foundation" \
  --description "Core infrastructure and data models"
```

#### Bulk Task Creation

```bash
# Create multiple tasks
vibey roadmap create-task --sprint <sprint-id> --title "Design database schema"
vibey roadmap create-task --sprint <sprint-id> --title "Implement API endpoints"
vibey roadmap create-task --sprint <sprint-id> --title "Write unit tests"
```

### Monitoring Progress

#### Track-Level View

```bash
# Show all tracks with progress
vibey roadmap status

# Detailed track view
vibey roadmap show track <track-id> --detailed
```

#### Sprint-Level View

```bash
# Current sprint progress
vibey roadmap show sprint <sprint-id>

# Compare sprint progress
vibey roadmap status --by-sprint
```

#### Task-Level View

```bash
# Tasks in specific state
vibey roadmap list tasks --filter not_started --sprint <sprint-id>
vibey roadmap list tasks --filter in_progress
vibey roadmap list tasks --filter completed --since "2 weeks ago"
```

### Handling Blockers

```bash
# List all blockers
vibey roadmap list-blockers

# View blocker details
vibey roadmap show task <blocked-task-id>

# Resolve blocker
vibey roadmap update task <task-id> --blocked false --blocked-by ""

# Add resolution context
vibey roadmap add-context <task-id> --message "Blocker resolved: API docs now available"
```

---

## Reporting Templates

### Weekly Status Report

```bash
vibey roadmap summarize --output reports/week-$(date +%V).md
```

Output format:
```markdown
# Week 50 Status Report

## Progress Summary
- Tracks: 3 active, 1 completed
- Sprints: 2 in_progress, 1 completed
- Tasks: 15 completed, 8 in_progress, 22 remaining

## Highlights
- Completed Sprint 2 for User Auth track
- Started API Integration track

## Blockers
- Task 001: Waiting on third-party API access

## Next Week
- Complete Sprint 3 of User Auth
- Begin Sprint 1 of API Integration
```

### Sprint Retrospective

```bash
vibey roadmap summarize --type sprint-retro --sprint <sprint-id>
```

### Stakeholder Update

```bash
vibey roadmap summarize --type executive --output stakeholder-update.md
```

---

## Command Reference

### Planning Commands

| Command | Purpose |
|---------|---------|
| `create-track` | Create new work track |
| `create-sprint` | Create sprint in track |
| `create-task` | Create task in sprint |
| `update track/sprint/task` | Modify properties |

### Monitoring Commands

| Command | Purpose |
|---------|---------|
| `status` | Overall progress |
| `status --verbose` | Detailed breakdown |
| `show track/sprint/task` | View specific item |
| `list-blockers` | All blocked items |
| `activity` | Recent changes |

### Reporting Commands

| Command | Purpose |
|---------|---------|
| `summarize` | Generate reports |
| `export` | Export data |
| `checkpoint` | Save state |

### Adjustment Commands

| Command | Purpose |
|---------|---------|
| `update` | Modify items |
| `repair` | Fix data issues |
| `validate` | Check integrity |
| `sync` | Sync YAML/DB |

### Audit Trail Commands

| Command | Purpose |
|---------|---------|
| `audit log` | View recent changes |
| `audit show <id>` | History for item |
| `audit suspicious` | Detect anomalies |
| `audit report` | Detailed audit report |

### Context Management Commands

| Command | Purpose |
|---------|---------|
| `vibey context list` | List all context items |
| `vibey context list --type decision` | List architectural decisions |
| `vibey context list --type sprint` | List sprint planning docs |
| `vibey context show <id>` | View context details |
| `vibey context search "query"` | Search context by content |
| `vibey context export <id> -o file.yaml` | Export context to file |
| `vibey context clean --older-than 90` | Clean old context |

---

## Audit Trail & Data Integrity

### Generate Audit Reports

Track all changes across your roadmap for accountability and compliance:

```bash
# Generate comprehensive audit report
vibey roadmap audit report

# Report for specific time period
vibey roadmap audit report --start 2025-01-01 --end 2025-01-31

# Report for specific object
vibey roadmap audit report --object-id <track-id>

# View recent changes across all objects
vibey roadmap audit log --limit 50
```

**Report Use Cases:**
- Sprint retrospectives - what changed and when
- Stakeholder accountability - who made changes
- Compliance documentation - change history
- Debug unexpected status changes

### Monitor Data Integrity

Ensure roadmap data remains consistent and detect issues early:

```bash
# Detect suspicious changes (status rollbacks, etc.)
vibey roadmap audit suspicious

# Validate roadmap structure
vibey roadmap validate

# Check YAML-SQLite sync status
vibey roadmap db status

# Verify integrity checksums
vibey roadmap checkpoint verify
```

**Integrity Checks:**
- Status rollbacks (completed → not_started)
- Progress decreases
- Manual edits without commits
- YAML/SQLite mismatches

**Weekly Integrity Review:**
```bash
# Comprehensive weekly check
vibey roadmap audit suspicious
vibey roadmap validate --fix
vibey roadmap db sync --dry-run
```

---

## Multi-Track Management

### View All Tracks

```bash
vibey roadmap status
# Shows all tracks with completion %
```

### Cross-Track Dependencies

```bash
# View dependencies
vibey roadmap list-dependencies

# Check blocked by other tracks
vibey roadmap list-blockers --cross-track
```

### Prioritization

```bash
# Update track priority
vibey roadmap update track <id> --priority critical

# Reorder tasks
vibey roadmap update task <id> --priority high
```

---

## Best Practices

### Roadmap Hygiene

1. **Weekly review** - 30 minutes minimum
2. **Keep sprints small** - 1-2 weeks max
3. **Clear task definitions** - Title + description
4. **Regular checkpoints** - At least weekly

### Communication

1. **Share status reports** - Weekly to stakeholders
2. **Document blockers** - With context and expected resolution
3. **Celebrate completions** - Mark milestones

### Data Quality

1. **Validate regularly** - `vibey roadmap validate`
2. **Sync after manual edits** - `vibey roadmap db sync`
3. **Backup before major changes** - Checkpoint first

---

## Documentation Touchpoints

| Activity | Documents |
|----------|-----------|
| Command reference | CLI_REFERENCE.md |
| Roadmap concepts | ROADMAP_SYSTEM.md |
| Data validation | VALIDATION_GUIDE.md |
| Best practices | ROADMAP_BEST_PRACTICES.md |

---

## Hands-On Tutorial

Learn roadmap management with a step-by-step walkthrough:

**📚 [Project Lead Walkthrough: Managing Roadmaps](../walkthroughs/WALKTHROUGH_PROJECT_LEAD.md)**

This walkthrough covers:
- Multi-track project structure
- Progress monitoring
- Dependency management
- Status reporting
