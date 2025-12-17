# New User Walkthrough: Your First 30 Minutes with Vibey

> **Time Required:** 30 minutes
> **Difficulty:** Beginner
> **Prerequisites:** Python 3.9+, pip, terminal access

## Overview

This walkthrough guides you through installing Vibey, initializing it in a project, and performing your first roadmap operations. By the end, you'll have a working Vibey setup with your first track, sprint, and task.

### What You'll Learn

- How to install Vibey
- How to initialize Vibey in a project
- The track → sprint → task hierarchy
- Basic status and show commands
- How to create and complete your first task

### What You'll Build

A complete Vibey roadmap with:
- 1 track ("Getting Started")
- 1 sprint ("First Sprint")
- 1 task (completed)

---

## Prerequisites

### Required

- [ ] Python 3.9 or higher installed
- [ ] pip (Python package manager)
- [ ] Terminal/command line access
- [ ] A project directory to work in

### Verify Prerequisites

```bash
# Check Python version
python3 --version
# Expected: Python 3.9.x or higher

# Check pip
pip3 --version
# Expected: pip 21.x or higher
```

---

## Step 1: Install Vibey

### Goal

Install the Vibey framework from source using git clone and editable install.

### Instructions

1. Open your terminal

2. Clone the repository:

   ```bash
   git clone https://github.com/anthropics/vibey.git
   cd vibey
   ```

3. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

4. Install in editable mode with dev dependencies:

   ```bash
   pip install -e ".[dev]"
   ```

   **Expected Output:**
   ```
   Successfully installed vibey-X.Y.Z ...
   ```
   *(Version number will reflect current release)*

5. Verify installation:

   ```bash
   vibey --version
   ```

   **Expected Output:**
   ```
   Vibey Agent Framework vX.Y.Z
   ```
   *(Version number will reflect installed version)*

### Checkpoint

> **Verify:** `vibey --version` shows a valid version number

### Troubleshooting

<details>
<summary>Problem: "command not found: vibey"</summary>

**Symptom:** Terminal doesn't recognize `vibey` command

**Cause:** Virtual environment not activated or pip installed to wrong location

**Solution:**
```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# If still not found, try Python module syntax
python3 -m vibey.cli.main --version
```
</details>

<details>
<summary>Problem: "Permission denied"</summary>

**Symptom:** Permission error during installation

**Cause:** Not using a virtual environment

**Solution:**
```bash
# Always use a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```
</details>

---

## Step 2: Explore Available Commands

### Goal

Understand what commands Vibey offers.

### Instructions

1. View top-level help:

   ```bash
   vibey --help
   ```

   **Expected Output:**
   ```
   Usage: vibey [OPTIONS] COMMAND [ARGS]...

   Vibey Agent Framework CLI

   Options:
     --version  Show the version and exit.
     --help     Show this message and exit.

   Commands:
     config   Manage framework configuration
     docs     Documentation commands
     git      Git integration commands
     init     Initialize Vibey in current directory
     roadmap  Roadmap management commands
   ```

2. View roadmap commands:

   ```bash
   vibey roadmap --help
   ```

   **Expected Output:**
   ```
   Usage: vibey roadmap [OPTIONS] COMMAND [ARGS]...

   Roadmap management commands

   Commands:
     status         Show roadmap status
     show           Show track, sprint, or task details
     create-track   Create a new track
     create-sprint  Create a new sprint
     create-task    Create a new task
     start          Start a task
     complete       Complete a task
     ...
   ```

### Checkpoint

> **Verify:** You can see the list of roadmap commands

---

## Step 3: Initialize Vibey in Your Project

### Goal

Set up Vibey in your project directory.

### Instructions

1. Navigate to your project (or create a new directory):

   ```bash
   # Create a test directory
   mkdir vibey-test && cd vibey-test

   # Or use existing project
   cd /path/to/your/project
   ```

2. Initialize Vibey:

   ```bash
   vibey init
   ```

   **Expected Output:**
   ```
   Initialized Vibey in current directory
   Created: .vibey/roadmap/
   Created: .vibey/roadmap.db
   ```

3. Verify initialization:

   ```bash
   ls -la .vibey/
   ```

   **Expected Output:**
   ```
   drwxr-xr-x  .
   drwxr-xr-x  ..
   drwxr-xr-x  roadmap/
   -rw-r--r--  roadmap.db
   ```

### Checkpoint

> **Verify:** `.vibey/` directory exists with `roadmap/` and `roadmap.db`

### Troubleshooting

<details>
<summary>Problem: "Already initialized"</summary>

**Symptom:** Error saying Vibey is already initialized

**Cause:** `.vibey/` directory already exists

**Solution:**
```bash
# Check existing initialization
vibey roadmap status

# If you want to start fresh
rm -rf .vibey/
vibey init
```
</details>

---

## Step 4: Check Initial Status

### Goal

View the current state of your roadmap.

### Instructions

1. View roadmap status:

   ```bash
   vibey roadmap status
   ```

   **Expected Output:**
   ```
   Vibey Roadmap Status
   ====================

   Roadmap: vibey-framework-v2

   Tracks: 0
   Sprints: 0
   Tasks: 0

   No tracks found. Create one with:
     vibey roadmap create-track --name "My Track"
   ```

### Checkpoint

> **Verify:** Status shows 0 tracks, 0 sprints, 0 tasks

---

## Step 5: Create Your First Track

### Goal

Create a track to organize your work.

### Instructions

1. Create a track:

   ```bash
   vibey roadmap create-track --name "Getting Started" --description "Learning Vibey basics"
   ```

   **Expected Output:**
   ```
   Created track: Getting Started
   Track ID: 01KCXXXXXXXXXXXXXX
   ```

2. View the track:

   ```bash
   vibey roadmap status
   ```

   **Expected Output:**
   ```
   Vibey Roadmap Status
   ====================

   Tracks: 1 (1 not_started)

   Getting Started
     Status: not_started
     Progress: 0/0 tasks (0%)
   ```

### Checkpoint

> **Verify:** Status shows 1 track named "Getting Started"

---

## Step 6: Create Your First Sprint

### Goal

Add a sprint to your track.

### Instructions

1. First, get your track ID:

   ```bash
   vibey roadmap show track --all
   ```

   Note the Track ID from the output (e.g., `01KCXXXXXXXXXXXXXX`)

2. Create a sprint:

   ```bash
   vibey roadmap create-sprint \
     --track <track-id> \
     --name "First Sprint" \
     --description "My first Vibey sprint"
   ```

   **Expected Output:**
   ```
   Created sprint: First Sprint
   Sprint ID: 01KCYYYYYYYYYYYY
   ```

3. View updated status:

   ```bash
   vibey roadmap status
   ```

   **Expected Output:**
   ```
   Tracks: 1 (1 not_started)
   Sprints: 1 (1 not_started)

   Getting Started
     First Sprint - not_started (0/0 tasks)
   ```

### Checkpoint

> **Verify:** Status shows 1 sprint under your track

---

## Step 7: Create Your First Task

### Goal

Add a task to your sprint.

### Instructions

1. Get your sprint ID:

   ```bash
   vibey roadmap show track <track-id>
   ```

   Note the Sprint ID from the output.

2. Create a task:

   ```bash
   vibey roadmap create-task \
     --sprint <sprint-id> \
     --title "Complete Vibey walkthrough" \
     --description "Finish the new user walkthrough" \
     --priority medium
   ```

   **Expected Output:**
   ```
   Created task: Complete Vibey walkthrough
   Task ID: 01KCZZZZZZZZZZZZ
   ```

### Checkpoint

> **Verify:** Task appears in status with `not_started` state

---

## Step 8: Start and Complete Your Task

### Goal

Go through the task lifecycle.

### Instructions

1. Start the task:

   ```bash
   vibey roadmap start <task-id>
   ```

   **Expected Output:**
   ```
   Started task: Complete Vibey walkthrough
   Status: in_progress
   Started: 2025-12-12T12:00:00Z
   ```

2. View task details:

   ```bash
   vibey roadmap show task <task-id>
   ```

3. Complete the task:

   ```bash
   vibey roadmap complete <task-id>
   ```

   **Expected Output:**
   ```
   Completed task: Complete Vibey walkthrough
   Status: completed
   Completed: 2025-12-12T12:30:00Z
   ```

4. View final status:

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

### Checkpoint

> **Verify:** Task shows as `completed` and progress is 100%

---

## Summary

### What You Accomplished

- Installed Vibey framework
- Initialized Vibey in a project
- Created your first track, sprint, and task
- Started and completed a task
- Understood the roadmap hierarchy

### Commands Used

| Command | Purpose |
|---------|---------|
| `vibey --version` | Check installation |
| `vibey init` | Initialize in project |
| `vibey roadmap status` | View overall status |
| `vibey roadmap create-track` | Create a track |
| `vibey roadmap create-sprint` | Create a sprint |
| `vibey roadmap create-task` | Create a task |
| `vibey roadmap start <id>` | Start a task |
| `vibey roadmap complete <id>` | Complete a task |
| `vibey roadmap show <type> <id>` | View details |

### Next Steps

1. **Continue Learning:** [Active Developer Walkthrough](./WALKTHROUGH_ACTIVE_DEVELOPER.md) - Daily workflow patterns
2. **Deep Dive:** [CLI Reference](../reference/CLI_REFERENCE.md) - Complete command documentation
3. **Understand Concepts:** [Roadmap System Guide](../reference/ROADMAP_SYSTEM.md) - Data model details
4. **Get Help:** [GitHub Issues](https://github.com/fredabood/vibey/issues) - Report problems or ask questions

---

## Quick Reference

### All Commands from This Walkthrough

```bash
# Installation
pip3 install vibey
vibey --version

# Initialization
vibey init
vibey roadmap status

# Create structure
vibey roadmap create-track --name "Getting Started" --description "Learning Vibey basics"
vibey roadmap create-sprint --track <track-id> --name "First Sprint"
vibey roadmap create-task --sprint <sprint-id> --title "My first task"

# Task lifecycle
vibey roadmap start <task-id>
vibey roadmap complete <task-id>
```

### Related Documentation

- [CLI Reference](../reference/CLI_REFERENCE.md) - All CLI commands
- [New User Journey](../journeys/JOURNEY_NEW_USER.md) - Conceptual overview
- [User Personas](../personas/USER_PERSONAS.md#nina) - Nina persona details
