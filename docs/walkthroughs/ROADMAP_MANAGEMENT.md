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

> **The Unified Ticket Model:** This three-level hierarchy is called the "Unified Ticket Model"
> in Vibey's architecture. Every work item has an assigned status, and progress flows upward
> automatically—completing tasks updates sprint progress, which updates track progress. All
> entities use ULIDs (26-character time-sortable identifiers) and are stored in both YAML files
> (for git version control) and SQLite (for fast queries). See [Architecture Overview](../architecture/ARCHITECTURE_OVERVIEW.md)
> for details on how dual storage works.

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
# Show all tracks via status
vibey roadmap status

# Show specific track details
vibey roadmap show <track-id>
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
vibey roadmap show <track-id>

# Detailed sprint view
vibey roadmap show <sprint-id>
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
vibey roadmap db query blocked
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

## Audit and Inventory

### Inventory Files

```bash
vibey audit inventory
```

Lists all files tracked by the roadmap system.

### Classify Items

```bash
vibey audit classify
```

Automatically classifies roadmap items by type and purpose.

---

## Checkpoints and Restore

### Create a Checkpoint

```bash
vibey roadmap checkpoint --name "before-refactor"
```

Saves the current roadmap state for later restoration.

### List Checkpoints

```bash
vibey roadmap checkpoint --list
```

### Restore from Checkpoint

```bash
vibey roadmap restore --checkpoint "before-refactor"
```

---

## Querying and Filtering

### View Status

```bash
# Overall roadmap status
vibey roadmap status

# Progress grouped by status
vibey roadmap db query progress --by status
```

### Show Details

```bash
# Track with all sprints
vibey roadmap show <track-id>

# Sprint with all tasks
vibey roadmap show <sprint-id>

# Task details
vibey roadmap show <task-id>
```

Note: Use `vibey roadmap status` to see all items, then `vibey roadmap show <id>` for details.

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
vibey roadmap show <track-id>
vibey roadmap status                    # Shows all tracks
```

### Sprint Commands
```bash
vibey roadmap create-sprint --track <id> --name "..."
vibey roadmap show <sprint-id>
vibey roadmap start <sprint-id>
vibey roadmap complete <sprint-id>
```

### Task Commands
```bash
vibey roadmap create-task --sprint <id> --title "..."
vibey roadmap show <task-id>
vibey roadmap start <task-id>
vibey roadmap complete <task-id>
```

### Dependency Commands
```bash
# Note: Dependency commands may vary - check `vibey roadmap --help`
vibey roadmap show <task-id>            # View task dependencies
```

---

## MCP Integration

AI assistants can use MCP tools for roadmap management:

### Query Tools

| MCP Tool | Purpose |
|----------|---------|
| `vibey_query_track` | Query track details and progress |
| `vibey_query_standards` | Query defined standards |
| `vibey_list_blockers` | List blocked tasks |

### Example: Query Track via MCP

```json
{
  "tool": "vibey_query_track",
  "arguments": {
    "track_id": "01KC2D0JK9JKQXGQW6MQEB0JZP"
  }
}
```

Returns track details including sprints and progress.

---

## See Also

- [Getting Started](./GETTING_STARTED.md) - First-time setup
- [Daily Workflow](./DAILY_WORKFLOW.md) - Task management cycle
- [Reporting & Status](./REPORTING_AND_STATUS.md) - Progress tracking
- [Architecture Overview](../architecture/ARCHITECTURE_OVERVIEW.md) - System concepts
