# Getting Started with Vibey

> **Time Required:** 30 minutes
> **Difficulty:** Beginner
> **Prerequisites:** Python 3.9+, pip, terminal access

---

## Overview

This walkthrough guides you from zero to productive with Vibey. By the end, you'll have:
- Vibey installed and working
- Your first roadmap with a track, sprint, and task
- Understanding of the core workflow

---

## Prerequisites

### Required

- Python 3.9 or higher
- pip (Python package manager)
- Terminal access
- A project directory to work in

### Verify Prerequisites

```bash
# Check Python version (need 3.9+)
python3 --version

# Check pip
pip3 --version
```

---

## Step 1: Install Vibey

### From Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/anthropics/vibey.git
cd vibey

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Verify Installation

```bash
vibey --version
# Expected output: vibey, version 2.5.0
```

<details>
<summary>Troubleshooting: "command not found: vibey"</summary>

Make sure your virtual environment is activated:
```bash
source .venv/bin/activate
vibey --version
```
</details>

---

## Step 2: Initialize Vibey in Your Project

Navigate to your project and initialize the roadmap:

```bash
cd /path/to/your/project
vibey roadmap init --name "My Project"
```

This creates the `.vibey/` directory structure:
```
.vibey/
├── roadmap/           # YAML files (source of truth)
│   ├── tracks/
│   ├── sprints/
│   └── tasks/
└── roadmap.db         # SQLite cache (fast queries)
```

---

## Step 3: Check Status

View your empty roadmap:

```bash
vibey roadmap status
```

**Expected Output:**
```
Vibey Roadmap Status
====================

Tracks: 0
Sprints: 0
Tasks: 0

No tracks found. Create one with:
  vibey roadmap create-track --name "My Track"
```

---

## Step 4: Create Your First Track

A **track** is a major theme or work stream:

```bash
vibey roadmap create-track \
  --name "Getting Started" \
  --description "Learning Vibey basics"
```

**Expected Output:**
```
Created track: Getting Started
Track ID: 01KC...
```

Note the Track ID - you'll need it for the next step.

---

## Step 5: Create Your First Sprint

A **sprint** is a focused work period within a track:

```bash
vibey roadmap create-sprint \
  --track <track-id> \
  --name "First Sprint" \
  --description "My first Vibey sprint"
```

---

## Step 6: Create Your First Task

A **task** is an individual work item:

```bash
# First, get your sprint ID
vibey roadmap show track <track-id>

# Create the task
vibey roadmap create-task \
  --sprint <sprint-id> \
  --title "Complete Vibey setup" \
  --description "Finish the getting started guide" \
  --priority medium
```

---

## Step 7: Complete the Task Lifecycle

### Start the Task

```bash
vibey roadmap start <task-id>
```

This marks the task as `in_progress` and records the start time.

### Complete the Task

```bash
vibey roadmap complete <task-id>
```

This marks the task as `completed` and updates sprint/track progress.

### View Final Status

```bash
vibey roadmap status
```

**Expected Output:**
```
Tracks: 1 (1 in_progress)
Sprints: 1 (1 in_progress)
Tasks: 1 (1 completed)

Getting Started
  First Sprint - in_progress (1/1 tasks - 100%)
```

---

## What You've Learned

| Concept | Description |
|---------|-------------|
| **Track** | Major project theme (weeks to months) |
| **Sprint** | Focused work period (days to weeks) |
| **Task** | Individual work item |
| **Status Flow** | not_started → in_progress → completed |
| **Progress** | Computed automatically from completed tasks |

> **Why This Architecture?** Vibey's three-level hierarchy (the "Unified Ticket Model")
> enables automatic progress tracking. When you complete tasks, sprint and track
> progress update automatically. Data is stored in YAML files (for git version control)
> with a SQLite cache (for fast queries). See [Architecture Overview](../architecture/ARCHITECTURE_OVERVIEW.md)
> for the full picture.

---

## Command Reference

| Command | Purpose |
|---------|---------|
| `vibey --version` | Check installation |
| `vibey roadmap init` | Initialize roadmap |
| `vibey roadmap status` | View overall status |
| `vibey roadmap create-track` | Create a track |
| `vibey roadmap create-sprint` | Create a sprint |
| `vibey roadmap create-task` | Create a task |
| `vibey roadmap start <id>` | Start a task |
| `vibey roadmap complete <id>` | Complete a task |
| `vibey roadmap show <id>` | View details |

---

## Optional: Authentication Setup

For team environments with signed commits:

### Initialize Project Authentication

```bash
vibey auth init-project
```

### Check Auth Status

```bash
vibey auth status
```

### Setup Authentication

```bash
vibey auth setup
```

### Add a Signer (Team Member)

```bash
vibey auth add-signer --name "Alice" --email "alice@example.com"
```

### List Authorized Signers

```bash
vibey auth list
```

### Export Auth Configuration

```bash
vibey auth export > auth-config.json
```

### Revoke a Signer

```bash
vibey auth revoke --email "removed@example.com"
```

---

## Next Steps

1. **Daily Workflow** - [DAILY_WORKFLOW.md](./DAILY_WORKFLOW.md) - Task management cycle
2. **Architecture** - [ARCHITECTURE_OVERVIEW.md](../architecture/ARCHITECTURE_OVERVIEW.md) - How Vibey works
3. **CLI Reference** - [CLI_REFERENCE.md](../reference/CLI_REFERENCE.md) - All commands
4. **Help** - [GitHub Issues](https://github.com/anthropics/vibey/issues)

---

## See Also

- [Architecture Overview](../architecture/ARCHITECTURE_OVERVIEW.md) - Core concepts explained
- [Daily Workflow](./DAILY_WORKFLOW.md) - Regular development patterns
- [Roadmap Management](./ROADMAP_MANAGEMENT.md) - Creating and organizing work
