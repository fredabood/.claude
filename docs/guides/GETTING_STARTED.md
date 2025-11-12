# Getting Started with Vibey

**Welcome to Vibey!** This guide will help you set up the Vibey Agent Framework and create your first roadmap in under 15 minutes.

---

## Table of Contents

1. [What is Vibey?](#what-is-vibey)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Your First Roadmap](#your-first-roadmap)
5. [Working with Tasks](#working-with-tasks)
6. [Using the MCP Server](#using-the-mcp-server)
7. [Common Workflows](#common-workflows)
8. [Next Steps](#next-steps)

---

## What is Vibey?

Vibey is an AI-native project management framework that helps you:

- **Plan Projects** - Organize work into tracks, sprints, and tasks
- **Track Progress** - Monitor completion with automatic metrics
- **Manage Dependencies** - Define and resolve task blockers
- **Integrate with AI** - Let AI assistants manage your roadmap via MCP
- **Enforce Quality** - Define quality gates for completion criteria

### Key Concepts

- **Roadmap** - Your entire project plan
- **Track** - Major work stream (e.g., "Backend", "Frontend", "Testing")
- **Sprint** - Time-boxed iteration within a track (typically 1-2 weeks)
- **Task** - Specific work item within a sprint
- **Quality Gates** - Completion criteria (test coverage, security scans, etc.)

### Architecture

```
Roadmap
├── Track 1: Backend Development
│   ├── Sprint 1: API Foundation
│   │   ├── Task 001: Design API schema
│   │   ├── Task 002: Implement endpoints
│   │   └── Task 003: Write tests
│   └── Sprint 2: Authentication
│       └── ...
├── Track 2: Frontend Development
│   └── ...
└── Track 3: Infrastructure
    └── ...
```

---

## Prerequisites

Before starting, ensure you have:

### Required

- **Python 3.7 or higher**
  ```bash
  python3 --version
  # Should show: Python 3.7+
  ```

- **pip** (Python package manager)
  ```bash
  pip --version
  ```

- **Git** (for commit tracking)
  ```bash
  git --version
  ```

### Optional (for MCP integration)

- **Claude Desktop** (or other MCP-compatible client)
- **MCP Python SDK**
  ```bash
  pip install mcp
  ```

---

## Installation

### Step 1: Clone Repository

```bash
# Clone the Vibey repository
git clone https://github.com/your-org/vibey.git
cd vibey
```

### Step 2: Install Vibey

```bash
# Install in development mode (editable)
pip install -e .

# Or install with MCP support
pip install -e ".[mcp]"
```

### Step 3: Verify Installation

```bash
# Check Vibey CLI
vibey --version
# Should show: Vibey CLI v2.5.0

# Check help
vibey --help
```

**Expected Output:**
```
Vibey Agent Framework - Platform-agnostic agentic orchestration.

Usage: vibey [OPTIONS] COMMAND [ARGS]...

Commands:
  roadmap  Manage roadmap system - tracks, sprints, tasks
  deploy   Deploy framework to target platforms
  docs     Generate and manage documentation
  config   Manage framework configuration
```

### Step 4: Verify Python Module

```bash
# Test Python import
python3 -c "from vibey.roadmap.models import Roadmap; print('✅ Vibey installed correctly')"
```

If all commands succeed, you're ready to go! 🎉

---

## Your First Roadmap

Let's create a simple roadmap for a web application project.

### Step 1: Create Project Directory

```bash
# Create project directory
mkdir my-webapp
cd my-webapp

# Initialize git (required for commit tracking)
git init
```

### Step 2: Initialize Roadmap

```bash
# Initialize roadmap (interactive)
vibey roadmap init

# Or specify options directly
vibey roadmap init --name "My Web App" --version "1.0.0"
```

**Output:**
```
✅ Roadmap initialized: My Web App
   Version: 1.0.0
   Location: .vibey/roadmap/

Next steps:
  1. Create tracks (edit .vibey/roadmap/roadmap.yaml)
  2. Define sprints and tasks
  3. Start working: vibey roadmap start <item-id>
```

### Step 3: Examine Structure

```bash
# View created structure
tree .vibey/

# Output:
.vibey/
├── roadmap/
│   └── roadmap.yaml
└── config/
    ├── project.yaml
    ├── framework.yaml
    ├── agents.yaml
    └── quality-gates.yaml
```

### Step 4: View Roadmap

```bash
# Check roadmap status
vibey roadmap status
```

**Output:**
```
My Web App Roadmap
Status: ⚪ Not Started
Version: 1.0.0
Progress: 0/0 tasks (0%)

No tracks defined yet.

To add tracks, edit .vibey/roadmap/roadmap.yaml
```

---

## Creating Your First Track and Sprint

### Step 1: Create Track Structure

```bash
# Create track directory
mkdir -p .vibey/roadmap/backend-api
```

### Step 2: Create Track Definition

Create `.vibey/roadmap/backend-api/track.yaml`:

```yaml
track:
  id: backend-api
  name: Backend API Development
  roadmap_id: my-web-app
  status: not_started
  priority: high
  estimated_duration: 4 weeks

  progress:
    sprints_total: 2
    sprints_completed: 0
    tasks_total: 0
    tasks_completed: 0
    completion_percent: 0

  sprints:
    - id: backend-api-1
      name: API Foundation
      status: not_started
      estimated_duration: 2 weeks

    - id: backend-api-2
      name: Authentication & Authorization
      status: not_started
      estimated_duration: 2 weeks

  dependencies: []
  quality_gates:
    - name: Test Coverage
      threshold: 80
      blocking: true
      description: "Unit and integration tests with >80% coverage"
```

### Step 3: Create Sprint

Create `.vibey/roadmap/backend-api/backend-api-1/sprint.yaml`:

```yaml
sprint:
  id: backend-api-1
  name: API Foundation
  track_id: backend-api
  roadmap_id: my-web-app
  status: not_started
  estimated_duration: 2 weeks

  progress:
    tasks_total: 3
    tasks_completed: 0
    completion_percent: 0

  development_gates: []
  quality_gates:
    - name: All Tests Pass
      threshold: 100
      blocking: true
```

### Step 4: Create Tasks

Create `.vibey/roadmap/backend-api/backend-api-1/tasks.yaml`:

```yaml
tasks:
  - id: backend-api-1-task-001
    title: Design API schema and routes
    description: |
      Define RESTful API schema using OpenAPI/Swagger.
      Document all endpoints, request/response formats, and error codes.

    task_type: development
    status: not_started
    estimated_tokens: 5000

    files_to_modify:
      - api/schema.yaml
      - docs/API.md

    quality_requirements:
      - OpenAPI 3.0 compliant schema
      - All endpoints documented
      - Example requests and responses provided

    dependencies: []

  - id: backend-api-1-task-002
    title: Implement core API endpoints
    description: |
      Implement CRUD endpoints for main resources.
      Use FastAPI/Flask with proper error handling.

    task_type: development
    status: not_started
    estimated_tokens: 12000

    files_to_modify:
      - api/routes.py
      - api/models.py
      - api/validators.py

    quality_requirements:
      - All endpoints return proper HTTP status codes
      - Input validation on all POST/PUT requests
      - Error responses include helpful messages

    dependencies:
      - type: task
        target_id: backend-api-1-task-001
        target_status: completed

  - id: backend-api-1-task-003
    title: Write API tests
    description: |
      Write unit and integration tests for all endpoints.
      Aim for >80% code coverage.

    task_type: development
    status: not_started
    estimated_tokens: 8000

    files_to_modify:
      - tests/test_api.py
      - tests/test_models.py

    quality_requirements:
      - Test coverage >80%
      - All happy paths tested
      - Error cases tested
      - Edge cases covered

    dependencies:
      - type: task
        target_id: backend-api-1-task-002
        target_status: completed
```

### Step 5: Verify Setup

```bash
# Check roadmap status
vibey roadmap status

# Should show:
# Track: backend-api (not_started)
# Sprint: backend-api-1 (not_started, 0/3 tasks)

# View track details
vibey roadmap show backend-api

# View sprint details
vibey roadmap show backend-api-1
```

---

## Working with Tasks

Now that you have a roadmap, let's work through the task lifecycle.

### Step 1: View Task Details

```bash
# Get detailed task information
vibey roadmap show backend-api-1-task-001
```

**Output:**
```
📋 Task: Design API schema and routes
   ID: backend-api-1-task-001
   Status: ⚪ not_started
   Estimated: 5,000 tokens

Description:
  Define RESTful API schema using OpenAPI/Swagger.
  Document all endpoints, request/response formats, and error codes.

Files to Modify:
  - api/schema.yaml
  - docs/API.md

Quality Requirements:
  ✅ OpenAPI 3.0 compliant schema
  ✅ All endpoints documented
  ✅ Example requests and responses provided

Dependencies: None
```

### Step 2: Get AI Context

```bash
# Get AI-optimized context for the task
vibey roadmap context backend-api-1-task-001
```

This outputs comprehensive context perfect for feeding to an AI assistant.

### Step 3: Start the Task

```bash
# Mark task as in progress
vibey roadmap start backend-api-1-task-001
```

**Output:**
```
✅ Task started: backend-api-1-task-001
   Status: in_progress
   Started: 2025-11-12 14:30:00

You can now work on this task. When finished:
  vibey roadmap complete backend-api-1-task-001
```

### Step 4: Do the Work

```bash
# Create API schema file
mkdir -p api
cat > api/schema.yaml << 'EOF'
openapi: 3.0.0
info:
  title: My Web App API
  version: 1.0.0
paths:
  /api/users:
    get:
      summary: List users
      responses:
        '200':
          description: Successful response
EOF

# Create documentation
mkdir -p docs
cat > docs/API.md << 'EOF'
# API Documentation

## Endpoints

### GET /api/users
Returns list of all users.
EOF

# Commit your changes
git add .
git commit -m "Design API schema and document endpoints"
```

### Step 5: Link Commit to Task

```bash
# Add commit to task (automatically uses HEAD)
vibey roadmap add-commit backend-api-1-task-001 --auto
```

**Output:**
```
✅ Commit added to task: backend-api-1-task-001
   Commit: a4f7bc3 - Design API schema and document endpoints
   Date: 2025-11-12 14:45:00
```

### Step 6: Complete the Task

```bash
# Mark task as complete
vibey roadmap complete backend-api-1-task-001
```

**Output:**
```
✅ Task completed: backend-api-1-task-001
   Duration: 15 minutes
   Commits: 1

Sprint Progress: 33% (1/3 tasks completed)
```

### Step 7: Work Through Remaining Tasks

```bash
# Start next task
vibey roadmap start backend-api-1-task-002

# Do work, commit, complete
# ... (repeat for each task)
```

---

## Completing a Sprint

Once all tasks are done, complete the sprint.

### Step 1: Check Sprint Status

```bash
vibey roadmap status --sprint backend-api-1
```

**Output:**
```
Sprint: backend-api-1
Status: 🔵 in_progress
Progress: 100% (3/3 tasks)

Tasks:
  ✅ backend-api-1-task-001: Design API schema
  ✅ backend-api-1-task-002: Implement endpoints
  ✅ backend-api-1-task-003: Write tests
```

### Step 2: Complete Sprint

```bash
vibey roadmap complete backend-api-1
```

**Output:**
```
Running quality gates...
  ✅ All Tests Pass: 100% (100/100 tests passing)

✅ Sprint completed: backend-api-1
   Duration: 2 weeks (estimated: 2 weeks)
   Tasks: 3/3 completed

Track Progress: 50% (1/2 sprints completed)
```

### Step 3: Generate Summary

```bash
# Create sprint summary
vibey roadmap summarize sprint backend-api-1
```

This creates `.vibey/roadmap/backend-api/backend-api-1/SUMMARY.md` with a detailed report.

---

## Using the MCP Server

Enable AI assistants (like Claude) to manage your roadmap conversationally.

### Step 1: Install MCP SDK

```bash
pip install mcp
```

### Step 2: Configure Claude Desktop

**macOS:**
```bash
# Edit config file
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Add Vibey server:**
```json
{
  "mcpServers": {
    "vibey-roadmap": {
      "command": "python",
      "args": [
        "-m",
        "framework.mcp.server",
        "--roadmap-root",
        "/Users/yourname/projects/my-webapp/.vibey/roadmap"
      ]
    }
  }
}
```

### Step 3: Restart Claude Desktop

Completely quit and reopen Claude Desktop (Cmd+Q, then reopen).

### Step 4: Test in Claude

Open a new chat in Claude Desktop and try:

**You:** "What tools do you have access to for roadmap management?"

**Claude:** "I have access to the following Vibey roadmap tools:
- vibey_start_task - Start a task
- vibey_complete_task - Complete a task
- vibey_query_task - Get task details
- ... (and 8 more)"

**You:** "Start task backend-api-1-task-001"

**Claude:** "[calls vibey_start_task]
✅ I've started task backend-api-1-task-001 (Design API schema and routes). The task is now in progress..."

### Step 5: AI-Driven Workflow

Now you can manage your roadmap conversationally:

- "What's the status of sprint backend-api-1?"
- "Complete task-001 and start task-002"
- "Show me all in-progress tasks"
- "What are the quality requirements for task-003?"

See the [MCP Integration Guide](MCP_INTEGRATION.md) for complete documentation.

---

## Common Workflows

### Daily Development Flow

```bash
# Morning: Check what's in progress
vibey roadmap status

# Start today's task
vibey roadmap context <task-id>  # Get context
vibey roadmap start <task-id>    # Mark started

# Work, commit frequently
git add .
git commit -m "Implement feature X"
vibey roadmap add-commit <task-id> --auto

# End of day: Complete if done
vibey roadmap complete <task-id>
```

### Sprint Planning

```bash
# Review roadmap
vibey roadmap status

# Create new sprint
# (Edit YAML files as shown above)

# View sprint details
vibey roadmap show <sprint-id>

# Start sprint
vibey roadmap start <sprint-id>

# Generate docs
vibey docs generate
```

### Quality Gate Checking

```bash
# Before completing, check requirements
vibey roadmap show <task-id>

# Run tests
pytest --cov

# If gates pass, complete
vibey roadmap complete <task-id>

# If gates fail, fix issues first
# ... fix issues ...
vibey roadmap complete <task-id>  # Retry
```

### Team Collaboration

```bash
# Commit roadmap changes
git add .vibey/
git commit -m "Update roadmap: complete sprint 1"
git push

# Pull latest roadmap state
git pull

# View changes
vibey roadmap status

# Continue work
vibey roadmap start <next-task>
```

---

## Next Steps

### Learn More

- **[CLI Reference](../reference/CLI_REFERENCE.md)** - Complete command documentation
- **[MCP Integration Guide](MCP_INTEGRATION.md)** - Set up AI assistant integration
- **[Developer Guide](../development/CONTRIBUTING.md)** - Contribute to Vibey

### Advanced Topics

- **Quality Gates** - Define custom completion criteria
- **Dependencies** - Model complex task relationships
- **Custom Agents** - Configure AI agent preferences
- **Deployment** - Deploy to multiple platforms

### Get Help

- **GitHub Issues:** https://github.com/your-org/vibey/issues
- **Discussions:** https://github.com/your-org/vibey/discussions
- **Documentation:** https://docs.vibey.dev

### Example Projects

Check out example roadmaps:

```bash
# View examples
ls examples/

# Copy example to your project
cp -r examples/web-app-roadmap/.vibey/ .
vibey roadmap status
```

---

## Tips & Best Practices

### Task Sizing

- **Small tasks:** 1-4 hours, 5k-10k tokens
- **Medium tasks:** 4-8 hours, 10k-20k tokens
- **Large tasks:** 1-2 days, 20k-50k tokens

Break large tasks into smaller ones for better tracking.

### Sprint Duration

- **1 week:** 3-5 small tasks
- **2 weeks:** 5-10 mixed tasks
- **3 weeks:** 10-15 tasks (max recommended)

Shorter sprints provide faster feedback.

### Quality Gates

Start with basic gates:
- Test coverage (>80%)
- All tests passing (100%)
- Documentation updated

Add more as needed:
- Security scans
- Performance benchmarks
- Code review approval

### Commit Hygiene

```bash
# Good: Atomic, descriptive commits
git commit -m "Implement user authentication endpoint"
vibey roadmap add-commit task-002 --auto

git commit -m "Add tests for auth endpoint"
vibey roadmap add-commit task-002 --auto

# Better: One logical change per commit, link to tasks
```

### File Organization

```
my-project/
├── .vibey/
│   ├── roadmap/          # Roadmap YAML files
│   │   ├── roadmap.yaml
│   │   └── backend-api/
│   │       ├── track.yaml
│   │       └── backend-api-1/
│   │           ├── sprint.yaml
│   │           └── tasks.yaml
│   └── config/           # Framework config
│       ├── project.yaml
│       ├── framework.yaml
│       ├── agents.yaml
│       └── quality-gates.yaml
├── src/                  # Your application code
├── tests/                # Test suite
└── docs/                 # Project documentation
```

Keep roadmap files version-controlled with your code.

---

## Troubleshooting

### "Roadmap not found"

```bash
# Ensure you're in project root
pwd
ls .vibey/

# Re-initialize if needed
vibey roadmap init
```

### "Task already started"

This is OK - Vibey operations are idempotent:
```bash
vibey roadmap start task-001
# Returns success even if already started
```

### "Quality gate failed"

```bash
# Check requirements
vibey roadmap show <task-id>

# Fix issues
pytest --cov  # Example: improve test coverage

# Retry
vibey roadmap complete <task-id>
```

### "Permission denied"

```bash
# Fix permissions
chmod -R u+rw .vibey/
```

---

## Quick Reference

### Essential Commands

```bash
# Initialize
vibey roadmap init

# Status
vibey roadmap status
vibey roadmap status --track <track-id>
vibey roadmap status --sprint <sprint-id>

# Details
vibey roadmap show <item-id>
vibey roadmap context <task-id>

# Lifecycle
vibey roadmap start <item-id>
vibey roadmap complete <item-id>

# Git integration
vibey roadmap add-commit <task-id> --auto

# Documentation
vibey docs generate
vibey roadmap summarize sprint <sprint-id>

# Configuration
vibey config show
vibey config validate
```

### File Locations

- **Roadmap:** `.vibey/roadmap/roadmap.yaml`
- **Tracks:** `.vibey/roadmap/<track-id>/track.yaml`
- **Sprints:** `.vibey/roadmap/<track-id>/<sprint-id>/sprint.yaml`
- **Tasks:** `.vibey/roadmap/<track-id>/<sprint-id>/tasks.yaml`
- **Config:** `.vibey/config/project.yaml`

---

## Congratulations! 🎉

You now know how to:
- ✅ Install Vibey
- ✅ Create a roadmap
- ✅ Define tracks, sprints, and tasks
- ✅ Work through the task lifecycle
- ✅ Use quality gates
- ✅ Integrate with AI assistants via MCP

Start building your project roadmap and let Vibey help you stay organized!

**Next:** Read the [MCP Integration Guide](MCP_INTEGRATION.md) to enable conversational roadmap management with Claude.

---

**Last Updated:** 2025-11-12
**Version:** 2.5.0
**Maintained By:** Vibey Framework Team
**License:** MIT
