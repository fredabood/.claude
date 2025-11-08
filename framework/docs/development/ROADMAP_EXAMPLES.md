# Roadmap System - Practical Examples

**Version:** 1.0
**Last Updated:** 2025-11-07

This document provides hands-on, practical examples of using the Roadmap system for different types of projects.

---

## Table of Contents

1. [Example 1: REST API Development](#example-1-rest-api-development)
2. [Example 2: Frontend Feature Development](#example-2-frontend-feature-development)
3. [Example 3: Machine Learning Model](#example-3-machine-learning-model)
4. [Example 4: Infrastructure Migration](#example-4-infrastructure-migration)
5. [Example 5: Documentation Sprint](#example-5-documentation-sprint)
6. [Workflow Patterns](#workflow-patterns)

---

## Example 1: REST API Development

### Scenario
You're building a REST API for a task management application. You need authentication, CRUD operations for tasks, and user management.

### Step 1: Initialize Roadmap

```bash
roadmap init \
  --id taskmanager-api \
  --name "Task Manager REST API" \
  --version 0.1.0 \
  --bump-on sprint_completion \
  --bump-type patch
```

### Step 2: Create Track

Create `.vibey/tracks/api.yaml`:

```yaml
track:
  id: "api"
  name: "REST API Development"
  roadmap_id: "taskmanager-api"

  status: "not_started"
  priority: "critical"

  created: "2025-11-07T10:00:00Z"
  estimated_duration: "6 weeks"

  progress:
    sprints_total: 3
    sprints_completed: 0
    tasks_total: 24
    tasks_completed: 0
    completion_percent: 0

  sprints:
    - id: "api-1"
      name: "Authentication & User Management"
      status: "not_started"
      estimated_duration: "2 weeks"
      tasks_count: 8

    - id: "api-2"
      name: "Task CRUD Operations"
      status: "not_started"
      estimated_duration: "2 weeks"
      tasks_count: 10

    - id: "api-3"
      name: "Advanced Features & Polish"
      status: "not_started"
      estimated_duration: "2 weeks"
      tasks_count: 6

  dependencies: []
  blocks: []
```

### Step 3: Create First Sprint

Create `.vibey/sprints/api-1.yaml`:

```yaml
sprint:
  id: "api-1"
  name: "Authentication & User Management"
  track_id: "api"
  roadmap_id: "taskmanager-api"

  status: "not_started"
  priority: "critical"

  created: "2025-11-07T10:00:00Z"
  estimated_duration: "2 weeks"

  quality_gates:
    - name: "Unit Tests"
      threshold: 90
      blocking: true
      status: "not_run"
      description: "Comprehensive unit tests for auth endpoints"

    - name: "Security Review"
      threshold: 95
      blocking: true
      status: "not_run"
      description: "Security audit of authentication implementation"

    - name: "API Documentation"
      threshold: 100
      blocking: true
      status: "not_run"
      description: "Complete OpenAPI/Swagger documentation"

  dependencies: []
  blocks:
    - type: "sprint"
      target_id: "api-2"
      at_status: "completed"
```

### Step 4: Create Tasks

Create `.vibey/tasks/api-1-tasks.yaml`:

```yaml
tasks:
  # Development Tasks
  - id: "api-1-task-001"
    sprint_id: "api-1"
    track_id: "api"
    roadmap_id: "taskmanager-api"

    name: "Design database schema for users"
    description: |
      Create SQLAlchemy models for:
      - User (id, email, password_hash, created_at, updated_at)
      - Session (id, user_id, token, expires_at)
    type: "development"
    status: "not_started"

    estimated_duration: "3 hours"
    dependencies: []

  - id: "api-1-task-002"
    sprint_id: "api-1"
    track_id: "api"
    roadmap_id: "taskmanager-api"

    name: "Implement user registration endpoint"
    description: |
      POST /api/v1/users
      - Email validation
      - Password hashing (bcrypt)
      - Duplicate email check
      - Return 201 with user object
    type: "development"
    status: "not_started"

    estimated_duration: "4 hours"
    dependencies:
      - type: "task"
        target_id: "api-1-task-001"
        at_status: "completed"

  - id: "api-1-task-003"
    sprint_id: "api-1"
    track_id: "api"
    roadmap_id: "taskmanager-api"

    name: "Implement login endpoint"
    description: |
      POST /api/v1/auth/login
      - Email/password validation
      - JWT token generation
      - Refresh token support
      - Return 200 with tokens
    type: "development"
    status: "not_started"

    estimated_duration: "5 hours"
    dependencies:
      - type: "task"
        target_id: "api-1-task-001"
        at_status: "completed"

  - id: "api-1-task-004"
    sprint_id: "api-1"
    track_id: "api"
    roadmap_id: "taskmanager-api"

    name: "Implement logout endpoint"
    description: |
      POST /api/v1/auth/logout
      - Invalidate session token
      - Clear refresh token
      - Return 204
    type: "development"
    status: "not_started"

    estimated_duration: "2 hours"
    dependencies:
      - type: "task"
        target_id: "api-1-task-003"
        at_status: "completed"

  - id: "api-1-task-005"
    sprint_id: "api-1"
    track_id: "api"
    roadmap_id: "taskmanager-api"

    name: "Implement authentication middleware"
    description: |
      JWT verification middleware:
      - Extract token from Authorization header
      - Verify signature
      - Check expiration
      - Attach user to request context
    type: "development"
    status: "not_started"

    estimated_duration: "3 hours"
    dependencies:
      - type: "task"
        target_id: "api-1-task-003"
        at_status: "completed"

  # Gate Tasks
  - id: "api-1-task-gate-001"
    sprint_id: "api-1"
    track_id: "api"
    roadmap_id: "taskmanager-api"

    name: "Write unit tests for authentication"
    description: |
      Test coverage:
      - User registration (valid/invalid)
      - Login (success/failure)
      - Token generation/validation
      - Middleware functionality
      Target: 90%+ coverage
    type: "gate"
    status: "not_started"

    gate_name: "Unit Tests"
    gate_type: "completion"
    estimated_duration: "6 hours"
    dependencies:
      - type: "task"
        target_id: "api-1-task-005"
        at_status: "completed"

  - id: "api-1-task-gate-002"
    sprint_id: "api-1"
    track_id: "api"
    roadmap_id: "taskmanager-api"

    name: "Security audit of authentication"
    description: |
      Review:
      - Password hashing strength
      - Token security (algorithm, expiration)
      - Input validation
      - SQL injection prevention
      - Rate limiting on auth endpoints
    type: "gate"
    status: "not_started"

    gate_name: "Security Review"
    gate_type: "completion"
    estimated_duration: "4 hours"
    dependencies:
      - type: "task"
        target_id: "api-1-task-005"
        at_status: "completed"

  - id: "api-1-task-gate-003"
    sprint_id: "api-1"
    track_id: "api"
    roadmap_id: "taskmanager-api"

    name: "Write API documentation for auth endpoints"
    description: |
      OpenAPI/Swagger docs:
      - POST /api/v1/users
      - POST /api/v1/auth/login
      - POST /api/v1/auth/logout
      - Request/response schemas
      - Error responses
      - Authentication requirements
    type: "gate"
    status: "not_started"

    gate_name: "API Documentation"
    gate_type: "completion"
    estimated_duration: "3 hours"
    dependencies:
      - type: "task"
        target_id: "api-1-task-005"
        at_status: "completed"
```

### Step 5: Daily Workflow

#### Day 1 Morning:
```bash
# Check status
roadmap status

# Start sprint
roadmap start api-1

# Get task recommendation
roadmap recommend --agent web-developer

# Start first task
roadmap start api-1-task-001
roadmap assign api-1-task-001 web-developer
```

#### Day 1 Afternoon:
```bash
# Complete first task
roadmap complete api-1-task-001

# Check what's next (should recommend task-002)
roadmap recommend --agent web-developer

# Start next task
roadmap start api-1-task-002
```

#### Days 2-7:
```bash
# Continue working through tasks
roadmap recommend --agent web-developer
roadmap start <task-id>
roadmap complete <task-id>

# Check progress
roadmap show api-1
```

#### Day 8-9 (Gate Tasks):
```bash
# After completing all dev tasks, sprint auto-progresses to completion_gate_check
roadmap show api-1
# Status: completion_gate_check

# Work on gate tasks
roadmap start api-1-task-gate-001
roadmap assign api-1-task-gate-001 test-engineer

roadmap start api-1-task-gate-002
roadmap assign api-1-task-gate-002 security-auditor

roadmap start api-1-task-gate-003
roadmap assign api-1-task-gate-003 docs-writer
```

#### Day 10 (Sprint Completion):
```bash
# After completing all gates
roadmap complete api-1-task-gate-001
roadmap complete api-1-task-gate-002
roadmap complete api-1-task-gate-003

# Complete sprint
roadmap complete api-1

# Check version (should auto-bump)
roadmap version --show
# Version: 0.1.1 (bumped because bump_on: sprint_completion)

# View overall progress
roadmap status
```

---

## Example 2: Frontend Feature Development

### Scenario
Adding a dashboard feature to an existing React application. This sprint depends on API endpoints from Example 1.

### Step 1: Create Track with Dependency

Create `.vibey/tracks/frontend.yaml`:

```yaml
track:
  id: "frontend"
  name: "Frontend Dashboard Development"
  roadmap_id: "taskmanager-api"

  status: "not_started"
  priority: "high"

  sprints:
    - id: "frontend-1"
      name: "Dashboard UI Components"
      status: "not_started"
      estimated_duration: "2 weeks"
      tasks_count: 12

  dependencies:
    - type: "sprint"
      target_id: "api-1"
      at_status: "completed"
      reason: "Need authentication API before building dashboard"
```

### Step 2: Check Dependencies

```bash
# Check if blocked
roadmap deps frontend-1 --blockers

# Output:
# ⚠️  frontend-1 is BLOCKED by:
#   - api-1 (sprint) - Need authentication API before building dashboard
#     Current status: in_progress (need: completed)
```

### Step 3: Create Sprint Tasks

Create `.vibey/tasks/frontend-1-tasks.yaml`:

```yaml
tasks:
  - id: "frontend-1-task-001"
    sprint_id: "frontend-1"
    track_id: "frontend"
    roadmap_id: "taskmanager-api"

    name: "Create Dashboard layout component"
    description: |
      React component: <DashboardLayout>
      - Sidebar navigation
      - Header with user menu
      - Main content area
      - Responsive design (mobile/desktop)
    type: "development"
    status: "not_started"

    estimated_duration: "6 hours"
    dependencies: []

  - id: "frontend-1-task-002"
    sprint_id: "frontend-1"
    track_id: "frontend"
    roadmap_id: "taskmanager-api"

    name: "Implement task list component"
    description: |
      React component: <TaskList>
      - Display tasks in card format
      - Filter by status (todo/in-progress/done)
      - Sort by due date/priority
      - Pagination
    type: "development"
    status: "not_started"

    estimated_duration: "8 hours"
    dependencies:
      - type: "task"
        target_id: "frontend-1-task-001"
        at_status: "completed"

  - id: "frontend-1-task-003"
    sprint_id: "frontend-1"
    track_id: "frontend"
    roadmap_id: "taskmanager-api"

    name: "Connect to API endpoints"
    description: |
      API integration:
      - axios client setup
      - GET /api/v1/tasks
      - POST /api/v1/tasks
      - PUT /api/v1/tasks/:id
      - DELETE /api/v1/tasks/:id
      - Authentication header injection
    type: "development"
    status: "not_started"

    estimated_duration: "5 hours"
    dependencies:
      - type: "task"
        target_id: "frontend-1-task-002"
        at_status: "completed"
      - type: "sprint"
        target_id: "api-2"
        at_status: "completed"
        reason: "Need task API endpoints"
```

### Step 4: Working Around Blockers

```bash
# Start with tasks that don't depend on API
roadmap start frontend-1
roadmap start frontend-1-task-001  # Layout (no API dependency)
roadmap start frontend-1-task-002  # Task list (no API dependency)

# Monitor blocker status
roadmap deps frontend-1-task-003 --blockers

# Once api-2 completes, task-003 becomes available
roadmap recommend --agent web-developer
```

---

## Example 3: Machine Learning Model

### Scenario
Building an image classification model. Includes data pipeline, model training, and deployment.

### Complete Structure

#### Roadmap
```yaml
# .vibey/roadmap.yaml
roadmap:
  id: "image-classifier"
  name: "Image Classification Model"
  version: "0.1.0"

  version_strategy:
    bump_on: "track_completion"
    bump_type: "minor"

  tracks_total: 3
  tracks_completed: 0
```

#### Track 1: Data Pipeline
```yaml
# .vibey/tracks/data-pipeline.yaml
track:
  id: "data-pipeline"
  name: "Data Pipeline Development"
  roadmap_id: "image-classifier"

  status: "not_started"
  priority: "critical"

  sprints:
    - id: "data-pipeline-1"
      name: "Data Collection & Validation"
      status: "not_started"
      estimated_duration: "1 week"
      tasks_count: 6

    - id: "data-pipeline-2"
      name: "Data Preprocessing & Augmentation"
      status: "not_started"
      estimated_duration: "1 week"
      tasks_count: 8

  dependencies: []
  blocks:
    - type: "track"
      target_id: "model"
      at_status: "completed"
```

#### Sprint Tasks
```yaml
# .vibey/tasks/data-pipeline-1-tasks.yaml
tasks:
  - id: "data-pipeline-1-task-001"
    name: "Set up data collection from source APIs"
    type: "development"
    status: "not_started"
    estimated_duration: "4 hours"

  - id: "data-pipeline-1-task-002"
    name: "Implement data validation pipeline"
    type: "development"
    status: "not_started"
    dependencies:
      - type: "task"
        target_id: "data-pipeline-1-task-001"
        at_status: "completed"

  - id: "data-pipeline-1-task-003"
    name: "Create train/val/test split logic"
    type: "development"
    status: "not_started"
    dependencies:
      - type: "task"
        target_id: "data-pipeline-1-task-002"
        at_status: "completed"

  - id: "data-pipeline-1-task-gate-001"
    name: "Data quality tests"
    type: "gate"
    gate_name: "Data Quality"
    gate_type: "completion"
    status: "not_started"
    description: |
      Verify:
      - No corrupted images
      - Class balance acceptable
      - Train/val/test split ratios correct
      - Labels validated
```

### Workflow with Agent Routing

```bash
# Initialize
roadmap init --id image-classifier --name "Image Classification Model"

# Start data pipeline track
roadmap start data-pipeline-1

# Get ML-specific recommendations
roadmap recommend --agent ml-engineer

# Output:
# 🎯 Task Recommendations for ml-engineer
#
# 1. Set up data collection from source APIs
#    ID: data-pipeline-1-task-001
#    Sprint: Data Collection & Validation (data-pipeline-1)
#    Recommended agents: ml-engineer (85%), web-developer (60%)
#    Priority score: 9.50

# Assign and work
roadmap start data-pipeline-1-task-001
roadmap assign data-pipeline-1-task-001 ml-engineer

# Progress through pipeline
for task in 002 003; do
  roadmap recommend --agent ml-engineer
  roadmap start data-pipeline-1-task-$task
  roadmap complete data-pipeline-1-task-$task
done

# Run quality gates
roadmap start data-pipeline-1-task-gate-001
roadmap assign data-pipeline-1-task-gate-001 test-engineer
```

---

## Example 4: Infrastructure Migration

### Scenario
Migrating from EC2 to Kubernetes. Multiple tracks that must be done sequentially.

### Track Structure with Dependencies

```yaml
# Track 1: Infrastructure Setup
# .vibey/tracks/infra-setup.yaml
track:
  id: "infra-setup"
  name: "Kubernetes Infrastructure Setup"
  status: "not_started"
  priority: "critical"

  sprints:
    - id: "infra-setup-1"
      name: "K8s Cluster Provisioning"
      tasks_count: 8

  dependencies: []
  blocks:
    - type: "track"
      target_id: "app-migration"
      at_status: "completed"

---

# Track 2: Application Migration
# .vibey/tracks/app-migration.yaml
track:
  id: "app-migration"
  name: "Application Containerization & Migration"
  status: "not_started"
  priority: "critical"

  sprints:
    - id: "app-migration-1"
      name: "Containerize Applications"
      tasks_count: 12

  dependencies:
    - type: "track"
      target_id: "infra-setup"
      at_status: "completed"
      reason: "Need K8s cluster before migrating apps"

  blocks:
    - type: "track"
      target_id: "cutover"
      at_status: "completed"

---

# Track 3: Cutover
# .vibey/tracks/cutover.yaml
track:
  id: "cutover"
  name: "Production Cutover"
  status: "not_started"
  priority: "critical"

  sprints:
    - id: "cutover-1"
      name: "Blue-Green Deployment & Switch"
      tasks_count: 10

  dependencies:
    - type: "track"
      target_id: "app-migration"
      at_status: "completed"
      reason: "Must have apps migrated before cutover"

  blocks: []
```

### Managing the Migration

```bash
# Check overall status
roadmap status

# View dependency chain
roadmap deps

# Output:
# 📊 Dependency Graph
#
# infra-setup (track)
#   └─> blocks: app-migration
#
# app-migration (track)
#   ├─> depends on: infra-setup (completed)
#   └─> blocks: cutover
#
# cutover (track)
#   └─> depends on: app-migration (completed)

# Start first track
roadmap start infra-setup
roadmap start infra-setup-1

# Check what's blocked
roadmap list tracks --status not_started
roadmap deps app-migration --blockers

# After completing infra-setup-1
roadmap complete infra-setup-1

# Check if next track is unblocked
roadmap deps app-migration --blockers
# No blockers! infra-setup is complete

# Start next track
roadmap start app-migration
roadmap start app-migration-1

# Batch assign infrastructure tasks
roadmap batch assign track app-migration --agent web-developer
```

---

## Example 5: Documentation Sprint

### Scenario
Creating comprehensive documentation for a completed API.

### Sprint Structure

```yaml
# .vibey/sprints/docs-1.yaml
sprint:
  id: "docs-1"
  name: "API Documentation Sprint"
  track_id: "documentation"
  roadmap_id: "taskmanager-api"

  status: "not_started"
  estimated_duration: "1 week"

  quality_gates:
    - name: "Documentation Review"
      threshold: 95
      blocking: true
      status: "not_run"

    - name: "Code Example Tests"
      threshold: 100
      blocking: true
      status: "not_run"
      description: "All code examples must run successfully"

  dependencies:
    - type: "sprint"
      target_id: "api-2"
      at_status: "completed"
      reason: "Document API after implementation complete"
```

### Tasks

```yaml
# .vibey/tasks/docs-1-tasks.yaml
tasks:
  - id: "docs-1-task-001"
    name: "Write API reference documentation"
    description: |
      Document all endpoints:
      - Request/response schemas
      - Authentication requirements
      - Error codes
      - Rate limits
    type: "documentation"
    assigned_agent: "docs-writer"

  - id: "docs-1-task-002"
    name: "Create getting started guide"
    description: |
      Quick start tutorial:
      - Installation
      - Authentication
      - First API call
      - Common patterns
    type: "documentation"
    assigned_agent: "docs-writer"

  - id: "docs-1-task-003"
    name: "Write code examples"
    description: |
      Example scripts in:
      - Python (requests library)
      - JavaScript (axios)
      - cURL
    type: "documentation"
    assigned_agent: "docs-writer"

  - id: "docs-1-task-gate-001"
    name: "Test all code examples"
    description: "Run every code example, verify output"
    type: "gate"
    gate_name: "Code Example Tests"
    assigned_agent: "test-engineer"
```

### Workflow with Docs-Writer Agent

```bash
# Get recommendations for docs-writer
roadmap recommend --agent docs-writer --limit 10

# Output shows all documentation tasks
# Assign batch
roadmap batch assign sprint docs-1 --agent docs-writer --filter dev

# docs-writer works through tasks
roadmap start docs-1-task-001
roadmap complete docs-1-task-001

roadmap start docs-1-task-002
roadmap complete docs-1-task-002

roadmap start docs-1-task-003
roadmap complete docs-1-task-003

# Sprint auto-progresses to completion_gate_check

# Assign gate task to test-engineer
roadmap start docs-1-task-gate-001
roadmap assign docs-1-task-gate-001 test-engineer

# Complete sprint
roadmap complete docs-1-task-gate-001
roadmap complete docs-1
```

---

## Workflow Patterns

### Pattern 1: Parallel Development

When tasks can be done in parallel:

```yaml
tasks:
  - id: "parallel-1-task-001"
    name: "Build feature A"
    dependencies: []  # No dependencies

  - id: "parallel-1-task-002"
    name: "Build feature B"
    dependencies: []  # No dependencies

  - id: "parallel-1-task-003"
    name: "Integration test A+B"
    dependencies:
      - type: "task"
        target_id: "parallel-1-task-001"
        at_status: "completed"
      - type: "task"
        target_id: "parallel-1-task-002"
        at_status: "completed"
```

```bash
# Start both in parallel
roadmap start parallel-1-task-001
roadmap start parallel-1-task-002

# Assign to different agents
roadmap assign parallel-1-task-001 web-developer
roadmap assign parallel-1-task-002 ml-engineer

# Integration task becomes available when both complete
roadmap recommend
```

### Pattern 2: Sequential Pipeline

When tasks must be done in order:

```yaml
tasks:
  - id: "pipeline-1-task-001"
    name: "Design schema"
    dependencies: []

  - id: "pipeline-1-task-002"
    name: "Implement models"
    dependencies:
      - type: "task"
        target_id: "pipeline-1-task-001"
        at_status: "completed"

  - id: "pipeline-1-task-003"
    name: "Create migrations"
    dependencies:
      - type: "task"
        target_id: "pipeline-1-task-002"
        at_status: "completed"

  - id: "pipeline-1-task-004"
    name: "Write tests"
    dependencies:
      - type: "task"
        target_id: "pipeline-1-task-003"
        at_status: "completed"
```

```bash
# Only one task available at a time
roadmap recommend  # Shows task-001

roadmap start pipeline-1-task-001
roadmap complete pipeline-1-task-001

roadmap recommend  # Now shows task-002
```

### Pattern 3: Multi-Track Dependencies

When tracks have dependencies:

```bash
# View overall dependency graph
roadmap deps

# See what's available to work on
roadmap list sprints --status not_started

# Check specific blocker
roadmap deps frontend-1 --blockers

# Monitor when dependencies complete
watch -n 60 "roadmap deps frontend-1 --blockers"
```

### Pattern 4: Batch Operations for Cleanup

When you need to mass-update:

```bash
# Mark all dev tasks in a completed sprint as complete
roadmap batch complete sprint api-1 --filter dev

# Assign all unassigned tasks to coordinator
roadmap batch assign roadmap --agent coordinator --status not_started

# Complete all documentation tasks
roadmap batch complete track docs --filter documentation
```

### Pattern 5: Agent Workload Balancing

When distributing work across agents:

```bash
# Check current workload
roadmap agents --workload

# Output:
# web-developer    Total: 15  In progress: 3  Completed: 10
# ml-engineer      Total: 8   In progress: 1  Completed: 5
# test-engineer    Total: 12  In progress: 0  Completed: 8

# Get recommendations for underutilized agent
roadmap recommend --agent test-engineer --limit 5

# Batch assign to balance
roadmap batch assign sprint current-sprint --agent test-engineer --status not_started
```

---

## Tips & Tricks

### Tip 1: Use JSON + jq for Advanced Queries

```bash
# Find all in-progress tasks assigned to web-developer
roadmap list tasks --json | jq '.tasks[] | select(.status == "in_progress" and .assigned_agent == "web-developer")'

# Count tasks by agent
roadmap list tasks --json | jq '.tasks | group_by(.assigned_agent) | map({agent: .[0].assigned_agent, count: length})'

# Find blocked tasks
roadmap deps --json | jq '.blockers'
```

### Tip 2: Create Aliases

```bash
# Add to .bashrc or .zshrc
alias rms='roadmap status'
alias rmr='roadmap recommend'
alias rma='roadmap agents --workload'
alias rml='roadmap list tasks --status not_started'
```

### Tip 3: Daily Standup Automation

```bash
#!/bin/bash
# daily-standup.sh

echo "=== Yesterday's Completed Tasks ==="
roadmap list tasks --status completed --json | \
  jq -r '.tasks[] | select(.completed_at > "'$(date -d yesterday +%Y-%m-%d)'") | "- \(.name) (\(.id))"'

echo ""
echo "=== Today's In-Progress Tasks ==="
roadmap list tasks --status in_progress --json | \
  jq -r '.tasks[] | "- \(.name) (\(.id))"'

echo ""
echo "=== Blockers ==="
roadmap deps --blockers
```

### Tip 4: CI/CD Integration

```yaml
# .github/workflows/roadmap-check.yml
name: Roadmap Health Check

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: pip install pyyaml
      - name: Validate roadmap
        run: roadmap validate --verbose
      - name: Check for circular dependencies
        run: roadmap deps --json | jq -e '.circular_dependencies | length == 0'
```

---

**End of Examples**

For more information:
- User Guide: `docs/development/ROADMAP_USER_GUIDE.md`
- CLI Reference: `framework/scripts/CLI.md`
