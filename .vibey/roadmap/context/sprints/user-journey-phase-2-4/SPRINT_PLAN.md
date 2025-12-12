# Sprint 2.4: User Journey Walkthroughs

**Sprint ID:** `01KC81GRE3GXVPVSCMD19FC4YZ`
**Track:** User Journey Audit & Documentation Coverage
**Status:** Not Started
**Tasks:** 7

## Overview

This sprint transforms the persona journey maps from Sprint 2.3 into hands-on, step-by-step walkthroughs. Unlike journey maps (which describe *what* users do), walkthroughs show *exactly how* to do it with real commands, expected outputs, and troubleshooting guidance.

## Success Criteria

1. Standardized walkthrough template established
2. 5 complete walkthroughs (one per persona)
3. All walkthroughs tested and verified working
4. Bidirectional links between walkthroughs and reference docs
5. Copy-paste ready commands throughout

---

## Walkthrough vs Journey Map

| Aspect | Journey Map (Sprint 2.3) | Walkthrough (Sprint 2.4) |
|--------|--------------------------|--------------------------|
| Purpose | Understand user goals/stages | Execute specific tasks |
| Format | Narrative, conceptual | Step-by-step instructions |
| Commands | Listed, described | Copy-paste ready with outputs |
| Depth | Breadth-first overview | Depth-first tutorial |
| Audience | Product/design planning | End users following along |

---

## Task Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  [Task 1] Create Walkthrough Template                           │
│      │                                                          │
│      ├──────────────┬──────────────┬──────────────┬────────┐    │
│      ▼              ▼              ▼              ▼        ▼    │
│  [Task 2]       [Task 3]       [Task 4]       [Task 5]  [Task 6]│
│  New User       Active Dev     Project Lead   Contrib   Platform│
│  Walkthrough    Walkthrough    Walkthrough    Walkthru  Walkthru│
│      │              │              │              │        │    │
│      └──────────────┴──────────────┴──────────────┴────────┘    │
│                              │                                  │
│                              ▼                                  │
│                    [Task 7] Cross-Link to References            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Task 1: Create Walkthrough Template

**ID:** `01KC81GRE3GXVPVSCMD19FC4Z0`
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 10,000

### Objective

Design a standardized template that ensures consistency across all walkthroughs.

### Template Design

**File:** `docs/walkthroughs/WALKTHROUGH_TEMPLATE.md`

```markdown
# [Persona Name] Walkthrough: [Specific Goal]

> **Time Required:** X minutes
> **Difficulty:** Beginner | Intermediate | Advanced
> **Prerequisites:** [List]

## Overview

Brief description of what this walkthrough accomplishes and who it's for.

### What You'll Learn

- Learning outcome 1
- Learning outcome 2
- Learning outcome 3

### What You'll Build/Achieve

Description of the end result.

---

## Prerequisites

### Required

- [ ] Prerequisite 1
- [ ] Prerequisite 2

### Recommended

- [ ] Optional but helpful item

### Verify Prerequisites

```bash
# Command to verify setup
vibey --version
# Expected output: Vibey Agent Framework v2.5.0
```

---

## Step 1: [Step Title]

### Goal

What this step accomplishes.

### Instructions

1. Sub-step with explanation

   ```bash
   # Command to run
   command here
   ```

   **Expected Output:**
   ```
   Output the user should see
   ```

2. Next sub-step

### Checkpoint

✅ **Verify:** How to confirm this step succeeded

### Troubleshooting

<details>
<summary>Problem: [Common Issue]</summary>

**Symptom:** What the user sees

**Cause:** Why this happens

**Solution:**
```bash
# Fix command
```
</details>

---

## Step 2: [Step Title]

[Same structure as Step 1]

---

## Step N: [Final Step]

[Same structure]

---

## Summary

### What You Accomplished

- Accomplishment 1
- Accomplishment 2
- Accomplishment 3

### Commands Used

| Command | Purpose |
|---------|---------|
| `vibey roadmap init` | Initialize roadmap |
| `vibey roadmap status` | Check status |

### Next Steps

1. **Continue Learning:** [Link to next walkthrough]
2. **Deep Dive:** [Link to reference documentation]
3. **Get Help:** [Link to community/support]

---

## Quick Reference

### All Commands from This Walkthrough

```bash
# Copy-paste block of all commands
command 1
command 2
command 3
```

### Related Documentation

- [CLI Reference: relevant-command](../reference/CLI_REFERENCE.md#relevant-command)
- [Journey Map: persona](../journeys/JOURNEY_PERSONA.md)
- [User Personas](../personas/USER_PERSONAS.md#persona)

---

## Feedback

Was this walkthrough helpful? [Yes/No]

Found an issue? [Report it](link-to-issues)
```

### Template Components

| Component | Purpose | Required |
|-----------|---------|----------|
| Header metadata | Time, difficulty, prereqs | ✓ |
| Overview | Context and outcomes | ✓ |
| Prerequisites | Setup verification | ✓ |
| Steps | Main content | ✓ |
| Checkpoints | Verify progress | ✓ |
| Troubleshooting | Handle errors | ✓ |
| Summary | Recap and next steps | ✓ |
| Quick Reference | Copy-paste commands | ✓ |
| Related Docs | Cross-links | ✓ |

### Acceptance Criteria

- [ ] Template created and documented
- [ ] All required sections defined
- [ ] Formatting conventions established
- [ ] Troubleshooting pattern defined
- [ ] Cross-linking pattern defined

---

## Task 2: Write New User Walkthrough

**ID:** `01KC81GRE3GXVPVSCMD19FC4Z1`
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 35,000

### Objective

Create a complete, hands-on walkthrough for new users to install Vibey and create their first roadmap.

### Output

**File:** `docs/walkthroughs/NEW_USER.md`

### Walkthrough Outline

```markdown
# New User Walkthrough: Your First Vibey Roadmap

> **Time Required:** 30-45 minutes
> **Difficulty:** Beginner
> **Prerequisites:** Python 3.8+, Terminal access

## Overview

This walkthrough guides you through installing Vibey and creating your
first project roadmap. By the end, you'll have a working roadmap with
tracks, sprints, and tasks.

### What You'll Learn

- How to install Vibey
- How to initialize a roadmap
- How to create tracks, sprints, and tasks
- How to track progress on tasks

### What You'll Build

A roadmap for a sample "Todo App" project with:
- 1 track: "Core Features"
- 1 sprint: "MVP Sprint"
- 3 tasks: Design, Implement, Test

---

## Prerequisites

### Required

- [ ] Python 3.8 or higher installed
- [ ] Terminal/command line access
- [ ] A project directory (existing or new)

### Verify Prerequisites

```bash
# Check Python version
python3 --version
# Expected: Python 3.8.x or higher

# Check pip
pip3 --version
# Expected: pip X.X.X from ...
```

---

## Step 1: Install Vibey

### Goal

Get Vibey installed and verify it works.

### Instructions

1. **Install via pip** (recommended for most users)

   ```bash
   pip3 install vibey
   ```

   **Expected Output:**
   ```
   Collecting vibey
     Downloading vibey-2.5.0-py3-none-any.whl (XXX kB)
   ...
   Successfully installed vibey-2.5.0
   ```

2. **Verify installation**

   ```bash
   vibey --version
   ```

   **Expected Output:**
   ```
   Vibey Agent Framework v2.5.0
   ```

3. **Explore available commands**

   ```bash
   vibey --help
   ```

   **Expected Output:**
   ```
   Usage: vibey [OPTIONS] COMMAND [ARGS]...

   Vibey Agent Framework - Platform-agnostic agentic orchestration.
   ...
   Commands:
     roadmap   Manage roadmap system - tracks, sprints, tasks...
     ...
   ```

### Checkpoint

✅ **Verify:** Running `vibey --version` shows version 2.5.0 or higher

### Troubleshooting

<details>
<summary>Problem: "command not found: vibey"</summary>

**Symptom:** Terminal says vibey is not found

**Cause:** Python scripts directory not in PATH

**Solution:**
```bash
# Option 1: Use full path
python3 -m vibey --version

# Option 2: Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Option 3: Reinstall with --user
pip3 install --user vibey
```
</details>

<details>
<summary>Problem: Permission denied</summary>

**Symptom:** Permission errors during install

**Cause:** Trying to install system-wide without sudo

**Solution:**
```bash
# Install for current user only
pip3 install --user vibey
```
</details>

---

## Step 2: Initialize Your Roadmap

### Goal

Create a new roadmap in your project directory.

### Instructions

1. **Navigate to your project** (or create a new directory)

   ```bash
   # Option A: Use existing project
   cd /path/to/your/project

   # Option B: Create new project
   mkdir my-todo-app && cd my-todo-app
   ```

2. **Initialize the roadmap**

   ```bash
   vibey roadmap init
   ```

   **Expected Output:**
   ```
   🚀 Initializing Vibey roadmap...

   Created:
     - .vibey/config/roadmap.yaml
     - .vibey/roadmap/ (directory structure)
     - .vibey/roadmap.db (SQLite database)

   ✅ Roadmap initialized successfully!

   Next steps:
     vibey roadmap create-track --name "My First Track"
     vibey roadmap status
   ```

3. **Verify the structure was created**

   ```bash
   ls -la .vibey/
   ```

   **Expected Output:**
   ```
   total 16
   drwxr-xr-x  5 user  staff   160 Dec 12 10:00 .
   drwxr-xr-x  4 user  staff   128 Dec 12 10:00 ..
   drwxr-xr-x  3 user  staff    96 Dec 12 10:00 config
   drwxr-xr-x  6 user  staff   192 Dec 12 10:00 roadmap
   -rw-r--r--  1 user  staff  8192 Dec 12 10:00 roadmap.db
   ```

### Checkpoint

✅ **Verify:** `.vibey/` directory exists with `roadmap/` subdirectory

### Troubleshooting

<details>
<summary>Problem: "Roadmap already exists"</summary>

**Symptom:** Error saying roadmap is already initialized

**Cause:** `.vibey/` directory already exists

**Solution:**
```bash
# View existing roadmap
vibey roadmap status

# Or start fresh (WARNING: deletes existing roadmap)
rm -rf .vibey/
vibey roadmap init
```
</details>

---

## Step 3: Create Your First Track

### Goal

Create a track to organize a major work area.

### Instructions

1. **Create the track**

   ```bash
   vibey roadmap create-track \
     --name "Core Features" \
     --priority high
   ```

   **Expected Output:**
   ```
   ✅ Created track: Core Features
      ID: 01KCXXXXXXXXXXXXXXXXXX
      Priority: high
      Status: not_started
   ```

2. **View your track**

   ```bash
   vibey roadmap status
   ```

   **Expected Output:**
   ```
   📊 Roadmap Status

   Tracks (1):
   ┌─────────────────┬──────────┬──────────┬──────────┐
   │ Track           │ Status   │ Sprints  │ Progress │
   ├─────────────────┼──────────┼──────────┼──────────┤
   │ Core Features   │ not_started │ 0/0   │ 0%       │
   └─────────────────┴──────────┴──────────┴──────────┘
   ```

### Checkpoint

✅ **Verify:** `vibey roadmap status` shows your "Core Features" track

---

## Step 4: Create a Sprint

### Goal

Create a sprint within your track for time-boxed work.

### Instructions

1. **Get your track ID**

   ```bash
   vibey roadmap status
   # Note the track ID from the output
   ```

2. **Create a sprint**

   ```bash
   vibey roadmap create-sprint \
     --track <your-track-id> \
     --name "MVP Sprint"
   ```

   **Expected Output:**
   ```
   ✅ Created sprint: MVP Sprint
      ID: 01KCYYYYYYYYYYYYYYYY
      Track: Core Features
      Status: not_started
   ```

### Checkpoint

✅ **Verify:** Status shows sprint under your track

---

## Step 5: Create Tasks

### Goal

Add specific work items to your sprint.

### Instructions

1. **Create Task 1: Design**

   ```bash
   vibey roadmap create-task \
     --sprint <your-sprint-id> \
     --title "Design todo list UI" \
     --type design
   ```

2. **Create Task 2: Implementation**

   ```bash
   vibey roadmap create-task \
     --sprint <your-sprint-id> \
     --title "Implement todo CRUD operations" \
     --type development
   ```

3. **Create Task 3: Testing**

   ```bash
   vibey roadmap create-task \
     --sprint <your-sprint-id> \
     --title "Write unit tests" \
     --type testing
   ```

4. **View your tasks**

   ```bash
   vibey roadmap show <your-sprint-id>
   ```

   **Expected Output:**
   ```
   📋 Sprint: MVP Sprint

   Status: not_started
   Track: Core Features

   Tasks (3):
   ┌─────┬──────────────────────────────┬─────────────┬────────────┐
   │ #   │ Title                        │ Type        │ Status     │
   ├─────┼──────────────────────────────┼─────────────┼────────────┤
   │ 001 │ Design todo list UI          │ design      │ not_started│
   │ 002 │ Implement todo CRUD operations│ development │ not_started│
   │ 003 │ Write unit tests             │ testing     │ not_started│
   └─────┴──────────────────────────────┴─────────────┴────────────┘
   ```

### Checkpoint

✅ **Verify:** Sprint shows 3 tasks

---

## Step 6: Work on a Task

### Goal

Start a task, work on it, and mark it complete.

### Instructions

1. **Start the design task**

   ```bash
   vibey roadmap start <task-001-id>
   ```

   **Expected Output:**
   ```
   ✅ Started task: Design todo list UI
      Status: in_progress
      Started: 2025-12-12T10:30:00Z
   ```

2. **Check status**

   ```bash
   vibey roadmap status
   ```

   *Notice the task is now "in_progress"*

3. **Complete the task**

   ```bash
   vibey roadmap complete <task-001-id>
   ```

   **Expected Output:**
   ```
   ✅ Completed task: Design todo list UI
      Status: completed
      Duration: 5 minutes
   ```

### Checkpoint

✅ **Verify:** Task shows as completed, progress updated

---

## Summary

### What You Accomplished

- ✅ Installed Vibey
- ✅ Initialized a roadmap
- ✅ Created a track for organizing work
- ✅ Created a sprint for time-boxed iteration
- ✅ Created tasks for specific work items
- ✅ Tracked progress on a task

### Commands Used

| Command | Purpose |
|---------|---------|
| `vibey roadmap init` | Initialize roadmap |
| `vibey roadmap status` | View overall status |
| `vibey roadmap create-track` | Create a track |
| `vibey roadmap create-sprint` | Create a sprint |
| `vibey roadmap create-task` | Create a task |
| `vibey roadmap show` | View item details |
| `vibey roadmap start` | Start working on task |
| `vibey roadmap complete` | Mark task complete |

### Next Steps

1. **Active Developer Walkthrough:** Learn daily workflow patterns
2. **CLI Reference:** Explore all available commands
3. **Add Context:** Use `vibey roadmap context` for AI integration

---

## Quick Reference

### All Commands from This Walkthrough

```bash
# Install
pip3 install vibey
vibey --version

# Initialize
cd /path/to/project
vibey roadmap init

# Create structure
vibey roadmap create-track --name "Core Features" --priority high
vibey roadmap create-sprint --track <track-id> --name "MVP Sprint"
vibey roadmap create-task --sprint <sprint-id> --title "Task name" --type development

# Track progress
vibey roadmap status
vibey roadmap show <item-id>
vibey roadmap start <task-id>
vibey roadmap complete <task-id>
```
```

### Acceptance Criteria

- [ ] All 6 steps complete with commands and outputs
- [ ] Troubleshooting for common issues
- [ ] Checkpoints at each step
- [ ] Commands tested and verified working
- [ ] Cross-links to reference docs

---

## Task 3: Write Active Developer Walkthrough

**ID:** `01KC81GRE3GXVPVSCMD19FC4Z2`
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 35,000

### Objective

Create a walkthrough showing efficient daily workflows for active developers.

### Output

**File:** `docs/walkthroughs/ACTIVE_DEVELOPER.md`

### Walkthrough Outline

```markdown
# Active Developer Walkthrough: Daily Workflow Mastery

> **Time Required:** 20-30 minutes
> **Difficulty:** Intermediate
> **Prerequisites:** Vibey installed, existing roadmap

## Overview

Learn efficient daily workflows for maximum productivity with Vibey.

### What You'll Learn

- How to start each work session
- How to use context for AI assistance
- How to track progress efficiently
- How to end sessions cleanly

---

## Step 1: Morning Session Start

### Goal

Quickly get context on what you were doing and what's next.

### Instructions

1. **Check recent activity**

   ```bash
   vibey roadmap activity
   ```

   **Expected Output:**
   ```
   📅 Recent Activity (last 24 hours)

   Yesterday:
   • 16:30 - Completed: Implement login form
   • 15:00 - Started: Write authentication tests
   • 14:00 - Created: 3 tasks in Auth Sprint

   In Progress:
   • Write authentication tests (started 15:00)
   ```

2. **View current status**

   ```bash
   vibey roadmap status
   ```

3. **Resume in-progress task or pick new one**

   ```bash
   # View task details
   vibey roadmap show <task-id>

   # Or start a new task
   vibey roadmap start <new-task-id>
   ```

---

## Step 2: Get Context for AI Assistant

### Goal

Generate optimized context for your AI coding assistant.

### Instructions

1. **Get task context**

   ```bash
   vibey roadmap context <task-id>
   ```

   **Expected Output:**
   ```markdown
   # Task Context: Write authentication tests

   ## Task Details
   - Sprint: Auth Sprint
   - Type: testing
   - Status: in_progress
   - Started: 2025-12-12T15:00:00Z

   ## Related Files
   - src/auth/login.py
   - tests/test_auth.py

   ## Dependencies
   - Depends on: Implement login form ✅

   ## Acceptance Criteria
   - Unit tests for login/logout
   - Integration tests for auth flow
   - Coverage > 80%
   ```

2. **Copy context to AI assistant**

   The context output is formatted for direct paste into AI assistants.

---

## Step 3: Add Context as You Work

### Goal

Keep task context updated as you discover things.

### Instructions

1. **Add a file reference**

   ```bash
   vibey roadmap add-context <task-id> \
     --file src/auth/middleware.py \
     --note "Key file for auth flow"
   ```

2. **Add a URL reference**

   ```bash
   vibey roadmap add-context <task-id> \
     --url "https://docs.example.com/auth" \
     --note "Reference documentation"
   ```

3. **Add a note**

   ```bash
   vibey roadmap add-context <task-id> \
     --note "Discovered edge case: expired tokens need special handling"
   ```

---

## Step 4: Complete Work and Link Commits

### Goal

Properly close out completed work with git integration.

### Instructions

1. **Commit your changes** (normal git workflow)

   ```bash
   git add .
   git commit -m "feat(auth): Add authentication tests

   Task: 01KCXXXXXXXXX"
   ```

2. **Link commit to task** (if not in commit message)

   ```bash
   vibey roadmap add-commit <task-id> --sha HEAD
   ```

3. **Complete the task**

   ```bash
   vibey roadmap complete <task-id>
   ```

---

## Step 5: End of Day Wrap-up

### Goal

Leave clean state for next session.

### Instructions

1. **Review progress**

   ```bash
   vibey roadmap summarize <sprint-id>
   ```

2. **Create checkpoint** (optional but recommended)

   ```bash
   vibey roadmap checkpoint create "EOD Dec 12"
   ```

3. **Check what's next**

   ```bash
   vibey roadmap status --track <track-id>
   ```
```

### Key Workflows Covered

| Workflow | Commands |
|----------|----------|
| Session start | `activity`, `status`, `show` |
| Get context | `context` |
| Add context | `add-context` |
| Complete work | `add-commit`, `complete` |
| End session | `summarize`, `checkpoint` |

### Acceptance Criteria

- [ ] Morning routine documented
- [ ] Context workflow complete
- [ ] Git integration explained
- [ ] End of day process included
- [ ] Efficiency tips throughout

---

## Task 4: Write Project Lead Walkthrough

**ID:** `01KC81GRE3GXVPVSCMD19FC4Z3`
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 35,000

### Objective

Create a walkthrough for project leads managing roadmaps and teams.

### Output

**File:** `docs/walkthroughs/PROJECT_LEAD.md`

### Walkthrough Outline

```markdown
# Project Lead Walkthrough: Roadmap Management

> **Time Required:** 45-60 minutes
> **Difficulty:** Intermediate
> **Prerequisites:** Vibey installed, basic familiarity

## Overview

Learn to create, manage, and maintain roadmaps for your team.

### What You'll Learn

- How to structure multi-track roadmaps
- How to create sprints from planning documents
- How to monitor progress across tracks
- How to maintain roadmap integrity

---

## Step 1: Design Your Roadmap Structure

### Goal

Plan track organization before creating.

### Instructions

1. **Consider your work areas**

   Tracks should represent major work areas:
   - Feature areas (Auth, Payments, UI)
   - Team areas (Backend, Frontend, DevOps)
   - Project phases (MVP, V2, Scale)

2. **Create tracks**

   ```bash
   # Create multiple tracks
   vibey roadmap create-track --name "Authentication" --priority critical
   vibey roadmap create-track --name "Core Features" --priority high
   vibey roadmap create-track --name "Infrastructure" --priority medium
   ```

---

## Step 2: Create Sprints from Plans

### Goal

Convert planning documents to roadmap sprints.

### Instructions

1. **Create a plan document** (`sprint-plan.md`)

   ```markdown
   # Sprint: Authentication MVP

   ## Goals
   - Basic login/logout working
   - Session management

   ## Tasks
   - [ ] Design auth flow
   - [ ] Implement login endpoint
   - [ ] Implement logout endpoint
   - [ ] Add session middleware
   - [ ] Write tests
   ```

2. **Generate sprint from plan**

   ```bash
   vibey roadmap create-from-plan sprint-plan.md \
     --track <auth-track-id>
   ```

---

## Step 3: Monitor Progress

### Goal

Track progress across all tracks and sprints.

### Instructions

1. **Overall status**

   ```bash
   vibey roadmap status
   ```

2. **Detailed track view**

   ```bash
   vibey roadmap show <track-id> --verbose
   ```

3. **Find blockers**

   ```bash
   vibey roadmap show blockers
   ```

4. **Generate summary**

   ```bash
   vibey roadmap summarize --all
   ```

---

## Step 4: Maintain Roadmap Integrity

### Goal

Keep roadmap data clean and consistent.

### Instructions

1. **Run validation**

   ```bash
   vibey roadmap validate-fast
   ```

2. **Repair issues**

   ```bash
   vibey roadmap repair --all --dry-run  # Preview
   vibey roadmap repair --all            # Apply
   ```

3. **Create checkpoints**

   ```bash
   vibey roadmap checkpoint create "Pre-restructure backup"
   vibey roadmap checkpoint list
   ```
```

### Key Workflows Covered

| Workflow | Commands |
|----------|----------|
| Structure planning | `create-track` |
| Sprint creation | `create-from-plan`, `create-sprint` |
| Progress monitoring | `status`, `show`, `summarize` |
| Maintenance | `validate-fast`, `repair`, `checkpoint` |

### Acceptance Criteria

- [ ] Multi-track management explained
- [ ] Plan-to-sprint workflow documented
- [ ] Monitoring and reporting covered
- [ ] Maintenance procedures included
- [ ] Team coordination patterns

---

## Task 5: Write Contributor Walkthrough

**ID:** `01KC81GRE3GXVPVSCMD19FC4Z4`
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 30,000

### Objective

Create a walkthrough for contributing to the Vibey framework.

### Output

**File:** `docs/walkthroughs/CONTRIBUTOR.md`

### Walkthrough Outline

```markdown
# Contributor Walkthrough: From Clone to PR

> **Time Required:** 30-45 minutes
> **Difficulty:** Intermediate
> **Prerequisites:** Git, Python 3.8+, GitHub account

## Overview

Learn how to set up a development environment and contribute to Vibey.

### What You'll Learn

- How to set up local development
- How to run tests and validation
- How to follow contribution guidelines
- How to submit a pull request

---

## Step 1: Fork and Clone

### Instructions

1. **Fork on GitHub**

   Visit https://github.com/fredabood/vibey and click "Fork"

2. **Clone your fork**

   ```bash
   git clone https://github.com/YOUR-USERNAME/vibey.git
   cd vibey
   ```

3. **Add upstream remote**

   ```bash
   git remote add upstream https://github.com/fredabood/vibey.git
   ```

---

## Step 2: Set Up Development Environment

### Instructions

1. **Create virtual environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```

2. **Install in development mode**

   ```bash
   pip install -e ".[dev]"
   ```

3. **Install git hooks**

   ```bash
   vibey roadmap install-hooks
   ```

4. **Verify setup**

   ```bash
   vibey --version
   pytest tests/ -v --tb=short
   ```

---

## Step 3: Make Changes

### Instructions

1. **Create feature branch**

   ```bash
   git checkout -b feature/my-improvement
   ```

2. **Make your changes**

   - Follow existing code patterns
   - Add type hints
   - Include docstrings
   - Write tests

3. **Run validation**

   ```bash
   vibey validate
   pytest tests/ -v
   ```

---

## Step 4: Commit and Push

### Instructions

1. **Stage changes**

   ```bash
   git add .
   ```

2. **Commit with proper format**

   ```bash
   git commit -m "feat(component): Add feature description

   - Detail 1
   - Detail 2

   Task: 01KCXXXXXXXXX"  # If linked to roadmap task
   ```

3. **Push to your fork**

   ```bash
   git push origin feature/my-improvement
   ```

---

## Step 5: Submit Pull Request

### Instructions

1. **Open PR on GitHub**

2. **Fill out PR template**

   - Description of changes
   - Testing done
   - Related issues/tasks

3. **Respond to review feedback**
```

### Key Workflows Covered

| Workflow | Commands/Actions |
|----------|------------------|
| Setup | Fork, clone, venv, install |
| Development | Branch, edit, validate, test |
| Git integration | `install-hooks`, commit format |
| Submission | Push, PR, review |

### Acceptance Criteria

- [ ] Complete setup instructions
- [ ] Testing requirements clear
- [ ] Commit message format specified
- [ ] PR process documented
- [ ] Review expectations set

---

## Task 6: Write Platform Integrator Walkthrough

**ID:** `01KC81GRE3GXVPVSCMD19FC4Z5`
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 35,000

### Objective

Create a walkthrough for integrating with Vibey via MCP.

### Output

**File:** `docs/walkthroughs/PLATFORM_INTEGRATOR.md`

### Walkthrough Outline

```markdown
# Platform Integrator Walkthrough: MCP Integration

> **Time Required:** 45-60 minutes
> **Difficulty:** Advanced
> **Prerequisites:** Vibey installed, MCP understanding, Python

## Overview

Learn to connect your AI assistant or tool to Vibey via MCP.

### What You'll Learn

- How MCP protocol works with Vibey
- How to start and connect to the MCP server
- How to call tools and access resources
- How to build custom integrations

---

## Step 1: Understand MCP Architecture

### Vibey MCP Components

```
┌─────────────────────────────────────────────┐
│              Your Application               │
│           (AI Assistant, IDE, etc.)         │
└─────────────────┬───────────────────────────┘
                  │ MCP Protocol (stdio/SSE)
                  ▼
┌─────────────────────────────────────────────┐
│            Vibey MCP Server                 │
├─────────────────────────────────────────────┤
│  Tools        │ Resources    │ Prompts      │
│  - Task ops   │ - Workflows  │ - Quality    │
│  - Sprint ops │ - Handoffs   │   gates      │
│  - Queries    │ - Agents     │              │
└─────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│           Roadmap Data Store                │
│         (.vibey/roadmap.db)                 │
└─────────────────────────────────────────────┘
```

---

## Step 2: Start MCP Server

### Instructions

1. **Start server (stdio mode)**

   ```bash
   vibey mcp start
   ```

   Or directly:

   ```bash
   python -m vibey.mcp.server
   ```

2. **Server output**

   ```
   Vibey MCP Server starting...
   Registered 24 tools
   Listening on stdio...
   ```

---

## Step 3: Connect from Client

### Python Client Example

```python
import asyncio
from mcp import Client

async def main():
    # Connect to Vibey MCP server
    client = Client()
    await client.connect_stdio(["vibey", "mcp", "start"])

    # List available tools
    tools = await client.list_tools()
    print(f"Available tools: {len(tools)}")
    for tool in tools:
        print(f"  - {tool.name}")

    # Call a tool
    result = await client.call_tool(
        "vibey_roadmap_status",
        arguments={}
    )
    print(f"Status: {result}")

    await client.close()

asyncio.run(main())
```

---

## Step 4: Use Tools

### Common Tool Examples

1. **Get roadmap status**

   ```python
   result = await client.call_tool("vibey_roadmap_status", {})
   ```

2. **Start a task**

   ```python
   result = await client.call_tool(
       "vibey_start_task",
       {"task_id": "01KCXXXXXXXXX"}
   )
   ```

3. **Query a track**

   ```python
   result = await client.call_tool(
       "vibey_query_track",
       {"track_id": "01KCYYYYYYYYY"}
   )
   ```

---

## Step 5: Access Resources

### Instructions

```python
# List resource templates
templates = await client.list_resource_templates()

# Read a workflow
content = await client.read_resource(
    "vibey://workflows/planning/sprint-planning"
)
print(content.text)
```

---

## Step 6: Use Prompts

### Instructions

```python
# Get available prompts
prompts = await client.list_prompts()

# Generate a prompt
result = await client.get_prompt(
    "quality_gate_security",
    arguments={"task_id": "01KCXXXXXXXXX"}
)

for message in result.messages:
    print(f"{message.role}: {message.content}")
```
```

### Key Components Covered

| Component | Examples |
|-----------|----------|
| Server startup | `vibey mcp start` |
| Tools | `vibey_roadmap_status`, `vibey_start_task` |
| Resources | Workflows, handoffs, agents |
| Prompts | Quality gates |
| Client code | Python examples |

### Acceptance Criteria

- [ ] MCP architecture explained
- [ ] Server startup documented
- [ ] Client connection examples
- [ ] All tool categories shown
- [ ] Resources and prompts covered

---

## Task 7: Cross-Link Walkthroughs to Reference Guides

**ID:** `01KC81GRE3GXVPVSCMD19FC4Z6`
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 15,000

### Objective

Add bidirectional hyperlinks between walkthroughs and reference documentation.

### Link Types

#### 1. Walkthrough → Reference

In each walkthrough, add links to relevant reference sections:

```markdown
## Related Documentation

- [CLI Reference: `roadmap init`](../reference/CLI_REFERENCE.md#roadmap-init)
- [CLI Reference: `roadmap status`](../reference/CLI_REFERENCE.md#roadmap-status)
- [MCP Reference: `vibey_roadmap_status`](../reference/MCP_REFERENCE.md#vibey_roadmap_status)
```

#### 2. Reference → Walkthrough

In CLI_REFERENCE.md and MCP_REFERENCE.md, add walkthrough links:

```markdown
#### `roadmap init`

Initialize a new roadmap...

**See Also:**
- [New User Walkthrough: Step 2](../walkthroughs/NEW_USER.md#step-2-initialize-your-roadmap)
```

### Link Matrix

| Command | Walkthroughs |
|---------|--------------|
| `roadmap init` | New User |
| `roadmap status` | New User, Active Developer, Project Lead |
| `roadmap start` | New User, Active Developer |
| `roadmap complete` | New User, Active Developer |
| `roadmap context` | Active Developer |
| `roadmap create-track` | New User, Project Lead |
| `roadmap create-sprint` | New User, Project Lead |
| `roadmap create-task` | New User, Project Lead |
| `roadmap create-from-plan` | Project Lead |
| `roadmap add-commit` | Active Developer, Contributor |
| `roadmap install-hooks` | Contributor |
| `roadmap validate-*` | Contributor, Project Lead |
| MCP tools | Platform Integrator |

### Implementation Steps

1. **Update each walkthrough** with "Related Documentation" section
2. **Update CLI_REFERENCE.md** with "See Also" links per command
3. **Update MCP_REFERENCE.md** with walkthrough links
4. **Verify all links work** (no 404s)

### Acceptance Criteria

- [ ] All walkthroughs have reference links
- [ ] CLI Reference has walkthrough links
- [ ] MCP Reference has walkthrough links
- [ ] All links verified working
- [ ] Consistent formatting

---

## File Structure After Sprint

```
docs/
├── walkthroughs/
│   ├── WALKTHROUGH_TEMPLATE.md      # Task 1
│   ├── NEW_USER.md                  # Task 2
│   ├── ACTIVE_DEVELOPER.md          # Task 3
│   ├── PROJECT_LEAD.md              # Task 4
│   ├── CONTRIBUTOR.md               # Task 5
│   └── PLATFORM_INTEGRATOR.md       # Task 6
├── reference/
│   ├── CLI_REFERENCE.md             # Task 7 (updated)
│   └── MCP_REFERENCE.md             # Task 7 (updated)
│
.vibey/roadmap/context/sprints/user-journey-phase-2-4/
└── SPRINT_PLAN.md                   # This document
```

---

## Dependencies

| Sprint | Dependency Type | Notes |
|--------|-----------------|-------|
| 2.1 CLI Reference | Hard | Link target must exist |
| 2.2 MCP Reference | Hard | Link target must exist |
| 2.3 Journey Maps | Soft | Walkthroughs expand on journey maps |

**Recommended Order:** Complete 2.1 and 2.2 before Task 7.

---

## Quality Checklist

For each walkthrough:

- [ ] All commands tested on fresh environment
- [ ] Expected outputs match actual outputs
- [ ] Troubleshooting covers common issues
- [ ] Checkpoints allow progress verification
- [ ] Cross-links are valid
- [ ] No placeholder text remains
- [ ] Time estimates are accurate
- [ ] Difficulty rating is appropriate

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Commands change | Medium | High | Link to versioned docs |
| Outputs differ | High | Medium | Use approximate outputs |
| Links break | Medium | Medium | Automated link checking |
| Too long | Medium | Low | Clear sections, TOC |
| Missing steps | Low | High | Fresh environment testing |

---

## Definition of Done

- [ ] All 7 tasks completed
- [ ] Template established and used consistently
- [ ] All 5 walkthroughs complete
- [ ] All walkthroughs tested on fresh environment
- [ ] Bidirectional cross-links working
- [ ] No broken links
- [ ] Documentation reviewed for accuracy
- [ ] Sprint summary written
