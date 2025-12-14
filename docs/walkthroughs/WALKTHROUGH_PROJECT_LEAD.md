# Project Lead Walkthrough: Managing Roadmaps

> **Time Required:** 45 minutes
> **Difficulty:** Advanced
> **Prerequisites:** Vibey installed, familiarity with basic commands

## Overview

This walkthrough covers roadmap management tasks: creating multi-track projects, monitoring progress, handling dependencies, and generating reports.

### What You'll Learn

- How to structure multi-track projects
- How to monitor progress effectively
- How to manage dependencies and blockers
- How to generate status reports

### What You'll Build

A complete multi-track project structure with proper organization.

---

## Prerequisites

### Required

- [ ] Vibey installed and initialized
- [ ] Understanding of track/sprint/task hierarchy
- [ ] Administrative access to project

---

## Step 1: Plan Your Roadmap Structure

### Goal

Design a logical organization for your project.

### Instructions

1. Consider your project's workstreams:

   ```
   Example Structure:
   ├── Backend Development (Track)
   │   ├── Sprint 1: API Foundation
   │   ├── Sprint 2: Authentication
   │   └── Sprint 3: Data Layer
   ├── Frontend Development (Track)
   │   ├── Sprint 1: UI Components
   │   └── Sprint 2: Integration
   └── Infrastructure (Track)
       ├── Sprint 1: CI/CD Setup
       └── Sprint 2: Monitoring
   ```

2. Create your tracks:

   ```bash
   vibey roadmap create-track \
     --name "Backend Development" \
     --description "API and server-side development" \
     --priority high

   vibey roadmap create-track \
     --name "Frontend Development" \
     --description "UI and client-side features" \
     --priority high

   vibey roadmap create-track \
     --name "Infrastructure" \
     --description "DevOps and platform" \
     --priority medium
   ```

### Checkpoint

> **Verify:** `vibey roadmap status` shows 3 tracks

---

## Step 2: Create Sprint Structure

### Goal

Add sprints to each track.

### Instructions

1. Get track IDs:

   ```bash
   vibey roadmap show track --all
   ```

2. Create sprints for Backend:

   ```bash
   vibey roadmap create-sprint \
     --track <backend-track-id> \
     --name "Sprint 1: API Foundation" \
     --description "Core API structure and routing"

   vibey roadmap create-sprint \
     --track <backend-track-id> \
     --name "Sprint 2: Authentication" \
     --description "User auth and authorization"
   ```

3. Repeat for other tracks...

### Checkpoint

> **Verify:** Each track has its sprints visible

---

## Step 3: Monitor Progress

### Goal

Track work across all tracks efficiently.

### Instructions

1. Get comprehensive status:

   ```bash
   vibey roadmap status --verbose
   ```

2. View by track:

   ```bash
   vibey roadmap show track <track-id> --detailed
   ```

3. Check blocked items across all tracks:

   ```bash
   vibey roadmap list-blockers --all-tracks
   ```

4. View recent activity:

   ```bash
   vibey roadmap activity --since "7 days ago"
   ```

### Checkpoint

> **Verify:** You can see progress across all workstreams

---

## Step 4: Generate Reports

### Goal

Create status reports for stakeholders.

### Instructions

1. Generate summary report:

   ```bash
   vibey roadmap summarize --output weekly-report.md
   ```

2. Export data for analysis:

   ```bash
   vibey roadmap export --format json --output progress-data.json
   ```

3. Create a checkpoint before sharing:

   ```bash
   vibey roadmap checkpoint --message "Weekly review - $(date +%Y-%m-%d)"
   ```

### Checkpoint

> **Verify:** Report file created successfully

---

## Step 5: Generate Compliance Reports (Optional)

### Goal

Use the audit trail for accountability and compliance documentation.

### Instructions

1. Generate an audit report for a time period:

   ```bash
   vibey roadmap audit report --start 2025-01-01 --end 2025-01-31
   ```

   **Expected Output:**
   ```
   Audit Report: 2025-01-01 to 2025-01-31
   =====================================

   Summary:
   - Total changes: 234
   - Tracks modified: 3
   - Sprints modified: 8
   - Tasks modified: 45
   - Status transitions: 156

   Top Contributors:
   1. dev@example.com - 89 changes
   2. lead@example.com - 45 changes
   ```

2. Check for suspicious changes:

   ```bash
   vibey roadmap audit suspicious
   ```

   **Expected Output:**
   ```
   Suspicious Changes Detected
   ===========================
   ⚠️ Status rollback: Task 01KC2D → completed → not_started (2025-01-15)
   ⚠️ Manual YAML edit: Sprint sprint-3.yaml modified without commit
   ```

3. Get detailed history for a specific track:

   ```bash
   vibey roadmap audit show <track-id>
   ```

### Use Cases

- **Sprint retrospectives:** Who did what, when
- **Stakeholder accountability:** Change attribution
- **Compliance audits:** Full change history
- **Issue debugging:** Track state changes

### Checkpoint

> **Verify:** You can generate and interpret audit reports

---

## Summary

### Commands Used

| Command | Purpose |
|---------|---------|
| `create-track` | Create work tracks |
| `create-sprint` | Create sprints |
| `status --verbose` | Detailed view |
| `list-blockers --all-tracks` | Cross-track blockers |
| `summarize` | Generate reports |
| `export` | Export data |
| `checkpoint` | Save state |
| `vibey context list --type decision` | List decisions |
| `vibey context list --type sprint` | List sprint context |
| `vibey context search "query"` | Search context |
| `vibey context export <id>` | Export context to file |

### Related Documentation

- [CLI Reference](../reference/CLI_REFERENCE.md)
- [Project Lead Journey](../journeys/JOURNEY_PROJECT_LEAD.md)
- [Roadmap System](../reference/ROADMAP_SYSTEM.md)
