# Roadmap Management

> **Time Required:** 20 minutes
> **Difficulty:** Intermediate
> **Prerequisites:** Vibey installed, basic familiarity with tracks/sprints/tasks

---

## Overview

This walkthrough covers creating and organizing roadmap structure: tracks, sprints, and tasks. Use this when setting up new projects or planning work.

---

## Understanding the Hierarchy

```
TRACK (Theme)              "Platform Compatibility"
    │
    ├── SPRINT (Period)    "Phase 1: Core Refactor"
    │       │
    │       ├── TASK       "Refactor adapter base"
    │       ├── TASK       "Update tests"
    │       └── TASK       "Update documentation"
    │
    └── SPRINT (Period)    "Phase 2: Platform Updates"
            │
            ├── TASK       "Update Cursor adapter"
            └── TASK       "Update VSCode adapter"
```

### When to Use Each

| Level | Use For | Duration |
|-------|---------|----------|
| **Track** | Major initiative, theme | Weeks to months |
| **Sprint** | Focused work period | Days to weeks |
| **Task** | Individual work item | Hours to days |

---

## Creating a Track

A track represents a major project theme or work stream.

### Basic Creation

```bash
vibey roadmap create-track \
  --name "Platform Compatibility" \
  --description "Ensure all platform adapters work consistently"
```

### With Additional Metadata

```bash
vibey roadmap create-track \
  --name "SQLite Backend Migration" \
  --description "Migrate from YAML-only to SQLite+YAML dual storage" \
  --priority high \
  --owner "backend-team"
```

### View Created Track

```bash
# List all tracks
vibey roadmap list tracks

# Show specific track
vibey roadmap show track <track-id>
```

---

## Creating a Sprint

A sprint is a focused work period within a track.

### Basic Creation

```bash
vibey roadmap create-sprint \
  --track <track-id> \
  --name "Sprint 1: Design" \
  --description "Architecture and design phase"
```

### Sprint Naming Conventions

Good sprint names:
- "Sprint 1: Core Implementation"
- "Phase 2: Testing & Validation"
- "Week 3: Bug Fixes"

Avoid:
- Generic names like "Sprint 1" without context
- Long descriptions in the name (use `--description` instead)

### View Sprint in Context

```bash
# See sprint within track
vibey roadmap show track <track-id>

# Detailed sprint view
vibey roadmap show sprint <sprint-id>
```

---

## Creating Tasks

Tasks are individual work items with clear deliverables.

### Basic Creation

```bash
vibey roadmap create-task \
  --sprint <sprint-id> \
  --title "Create database schema" \
  --description "Design and implement the SQLite schema for tracks, sprints, and tasks"
```

### With Full Metadata

```bash
vibey roadmap create-task \
  --sprint <sprint-id> \
  --title "Implement loader tests" \
  --description "Write unit tests for sql_loader functions" \
  --priority high \
  --complexity medium \
  --estimated-tokens 5000 \
  --task-type development
```

### Task Attributes

| Attribute | Values | Purpose |
|-----------|--------|---------|
| `priority` | low, medium, high, critical | Urgency |
| `complexity` | trivial, simple, medium, complex, epic | Effort estimate |
| `task-type` | research, design, development, testing, documentation | Work category |
| `estimated-tokens` | integer | AI token budget |

### Good Task Titles

| Good | Why |
|------|-----|
| "Create database schema for tracks" | Specific, actionable |
| "Fix null handling in loader" | Clear scope |
| "Write tests for sprint queries" | Defined deliverable |

| Bad | Why |
|-----|-----|
| "Database stuff" | Too vague |
| "Fix bugs" | No specific scope |
| "Make it work" | No clear definition of done |

---

## Bulk Operations

### Create Multiple Tasks at Once

```bash
# Complete a sprint's tasks in bulk
vibey roadmap bulk complete-sprint <sprint-id>
```

### Update Multiple Items

```bash
# Update task status
vibey roadmap update task <task-id> --status in_progress

# Update sprint description
vibey roadmap update sprint <sprint-id> --description "Updated scope"
```

---

## Dependencies and Blockers

### Add a Dependency

```bash
vibey roadmap dependency add \
  --task <task-id> \
  --depends-on <other-task-id>
```

This means `task-id` cannot start until `other-task-id` is completed.

### List Dependencies

```bash
# Show dependencies for a task
vibey roadmap dependency list --task <task-id>

# Show all blocked tasks
vibey roadmap list-blockers
```

### Remove a Dependency

```bash
vibey roadmap dependency remove \
  --task <task-id> \
  --depends-on <other-task-id>
```

---

## Standards and Conventions

### Add a Standard

```bash
vibey roadmap add-standard \
  --type task-naming \
  --description "Task titles should be imperative verbs"
```

### Check Standards Compliance

```bash
vibey roadmap check-standards
```

---

## Querying and Filtering

### List with Filters

```bash
# Tasks by status
vibey roadmap list tasks --status not_started
vibey roadmap list tasks --status in_progress
vibey roadmap list tasks --status completed

# Tasks in a sprint
vibey roadmap list tasks --sprint <sprint-id>

# Sprints in a track
vibey roadmap list sprints --track <track-id>
```

### Show Details

```bash
# Track with all sprints
vibey roadmap show track <track-id>

# Sprint with all tasks
vibey roadmap show sprint <sprint-id>

# Task details
vibey roadmap show task <task-id>
```

---

## Exporting Data

### Export to JSON

```bash
vibey roadmap export --format json > roadmap-export.json
```

### Generate Summary

```bash
vibey roadmap summarize --output summary.md
```

---

## Example: Setting Up a New Project

### Step 1: Create the Track

```bash
vibey roadmap create-track \
  --name "v2.0 Release" \
  --description "Features and fixes for version 2.0"
```

### Step 2: Plan Sprints

```bash
# Design sprint
vibey roadmap create-sprint \
  --track <track-id> \
  --name "Sprint 1: Design & Planning" \
  --description "Architecture decisions and task breakdown"

# Implementation sprint
vibey roadmap create-sprint \
  --track <track-id> \
  --name "Sprint 2: Core Implementation" \
  --description "Build the main features"

# Testing sprint
vibey roadmap create-sprint \
  --track <track-id> \
  --name "Sprint 3: Testing & Polish" \
  --description "Testing, documentation, release prep"
```

### Step 3: Create Tasks

```bash
# Design sprint tasks
vibey roadmap create-task --sprint <sprint-1-id> \
  --title "Write architecture document" --priority high

vibey roadmap create-task --sprint <sprint-1-id> \
  --title "Review with team" --priority medium

# Implementation sprint tasks
vibey roadmap create-task --sprint <sprint-2-id> \
  --title "Implement feature A" --priority high

# Set up dependencies
vibey roadmap dependency add \
  --task <implement-task-id> \
  --depends-on <architecture-doc-task-id>
```

### Step 4: Verify Structure

```bash
vibey roadmap status
vibey roadmap show track <track-id>
```

---

## Command Reference

### Track Commands
```bash
vibey roadmap create-track --name "..." --description "..."
vibey roadmap list tracks
vibey roadmap show track <id>
vibey roadmap update track <id> --name "..."
```

### Sprint Commands
```bash
vibey roadmap create-sprint --track <id> --name "..."
vibey roadmap list sprints --track <id>
vibey roadmap show sprint <id>
vibey roadmap update sprint <id> --description "..."
```

### Task Commands
```bash
vibey roadmap create-task --sprint <id> --title "..."
vibey roadmap list tasks --sprint <id>
vibey roadmap show task <id>
vibey roadmap update task <id> --status <status>
```

### Dependency Commands
```bash
vibey roadmap dependency add --task <id> --depends-on <id>
vibey roadmap dependency list --task <id>
vibey roadmap dependency remove --task <id> --depends-on <id>
vibey roadmap list-blockers
```

---

## See Also

- [Getting Started](./GETTING_STARTED.md) - First-time setup
- [Daily Workflow](./DAILY_WORKFLOW.md) - Task management cycle
- [Reporting & Status](./REPORTING_AND_STATUS.md) - Progress tracking
- [Architecture Overview](../architecture/ARCHITECTURE_OVERVIEW.md) - System concepts
