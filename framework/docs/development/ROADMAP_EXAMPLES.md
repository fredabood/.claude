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
6. [Example 6: Context Loading for Complex Tasks](#example-6-context-loading-for-complex-tasks)
7. [Workflow Patterns](#workflow-patterns)

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

## Example 6: Context Loading for Complex Tasks

### Scenario
You're implementing a complex authentication task (`backend-3-task-015`) that depends on multiple completed sprints. Without context loading, you'd need to read 15+ sprints (40+ files, 100,000+ tokens). With context loading, you get exactly what you need.

### Project State

**Completed Sprints:**
- `core-1`: Core framework (3 tasks completed)
- `core-2`: Configuration system (5 tasks completed)
- `backend-1`: Database layer (8 tasks completed)
- `backend-2`: API endpoints (7 tasks completed)

**Current Sprint:**
- `backend-3`: Authentication & Authorization (in progress)

**Current Task:**
- `backend-3-task-015`: "Implement JWT authentication with refresh tokens"
- Dependencies: 5 tasks across 3 completed sprints

### Step 1: Load Context Before Starting

```bash
# Check context for the task
roadmap context backend-3-task-015
```

**Output:**
```
🔍 Loading context for task: backend-3-task-015

**Task:** Implement JWT authentication with refresh tokens
**Sprint:** backend-3
**Type:** development

📄 Current Sprint Docs: ~5,700 tokens

📚 Dependency Analysis:
   Total dependencies: 5
   🔵 backend-2-task-003 (summary) ~700 tokens
   🔵 backend-2-task-007 (summary) ~700 tokens
   🔵 backend-1-task-002 (summary) ~700 tokens
   ⚪ core-2-task-001 (minimal) ~100 tokens
   ⚪ core-1-task-005 (minimal) ~100 tokens

📊 Context Summary:
   Current sprint: ~5,700 tokens
   Dependencies: ~2,400 tokens
   Total: ~8,100 tokens (78% reduction from full ~37,500 tokens)
```

### Step 2: Review Loaded Context

**Distance 1 (Summary Mode):**
- `backend-2-task-003`: API middleware implementation
  - **Outputs:** Express middleware pattern, error handling utilities
  - **Interfaces:** `middleware/auth.js`, `utils/errors.js`
  - **Gotchas:** Middleware order matters, async error handling

- `backend-2-task-007`: User session management
  - **Outputs:** Session store interface, Redis integration
  - **Interfaces:** `SessionStore` class, `redis-client.js`
  - **Gotchas:** Session TTL must sync with Redis, handle reconnections

- `backend-1-task-002`: User model & database schema
  - **Outputs:** User schema, password hashing utilities
  - **Interfaces:** `models/User.js`, `hashPassword()`, `verifyPassword()`
  - **Gotchas:** Use bcrypt async methods, salt rounds = 12

**Distance 2 (Minimal Mode):**
- `core-2-task-001`: Configuration system
  - **Outputs:** `config/` loader, environment validation

- `core-1-task-005`: Error handling patterns
  - **Outputs:** Custom error classes, error middleware

### Step 3: Task Appears Complex - Use Preparation Mode

```bash
# Generate deep preparation document
roadmap prepare backend-3-task-015
```

**Output:**
```
🔍 Analyzing task dependencies...
   Loading core-1 (full docs)      ✅ ~5,800 tokens
   Loading core-2 (full docs)      ✅ ~6,200 tokens
   Loading backend-1 (full docs)   ✅ ~7,100 tokens
   Loading backend-2 (full docs)   ✅ ~8,400 tokens
   Loading backend-3 (full docs)   ✅ ~5,700 tokens

✅ Preparation document generated
   Path: .vibey/sprint_docs/backend-3/prep/backend-3-task-015.md
   Dependencies analyzed: 5
   Full context loaded: ~37,500 tokens
   Document size: ~4,200 words
```

### Step 4: Review Preparation Document

```bash
roadmap prepare backend-3-task-015 --show
```

**Preparation Document Excerpt:**
```markdown
# Task Preparation: Implement JWT Authentication

## Task Overview
Implement JWT-based authentication with refresh token rotation for the Task Manager API.

## Dependencies Analysis

### backend-2-task-003: API Middleware (CRITICAL)
**What it provides:**
- Express middleware pattern for request processing
- Error handling utilities for API responses
- Request validation framework

**How to integrate:**
- Extend existing middleware chain with auth middleware
- Use `ApiError` class for auth failures
- Follow async middleware pattern from task-003

**Key learnings from backend-2:**
- Middleware order is critical (auth before other middleware)
- Use next() properly to avoid hanging requests
- Centralized error handling prevents code duplication

### backend-2-task-007: Session Management (CRITICAL)
**What it provides:**
- SessionStore interface for persistence
- Redis integration for session storage
- TTL management and cleanup

**How to integrate:**
- Store refresh tokens in Redis via SessionStore
- Implement token rotation using session updates
- Use existing Redis connection pool

**Critical integration points:**
- Session TTL should match refresh token expiry
- Handle Redis connection failures gracefully
- Use SessionStore.invalidate() for logout

### backend-1-task-002: User Model (REQUIRED)
**What it provides:**
- User schema with password fields
- Password hashing utilities (bcrypt)
- Database queries for user lookup

**How to integrate:**
- Use User.findByEmail() for authentication
- Call verifyPassword() for credential checks
- Store tokenVersion in User schema for revocation

**Gotchas:**
- ALWAYS use async bcrypt methods
- Salt rounds set to 12 (don't change)
- Add tokenVersion field to User schema

## Implementation Checklist

### Phase 1: JWT Setup
- [ ] Install jsonwebtoken and dependencies
- [ ] Create JWT signing/verification utilities
- [ ] Implement access token generation (15min TTL)
- [ ] Implement refresh token generation (7 day TTL)

### Phase 2: Auth Middleware
- [ ] Create authMiddleware using backend-2 pattern
- [ ] Verify access token from Authorization header
- [ ] Attach user to req.user
- [ ] Handle token expiration with proper error codes

### Phase 3: Refresh Token System
- [ ] Store refresh tokens in Redis via SessionStore
- [ ] Implement token rotation on refresh
- [ ] Add token version to User model for revocation
- [ ] Create /auth/refresh endpoint

### Phase 4: Security Hardening
- [ ] Implement CSRF protection for refresh
- [ ] Add rate limiting to auth endpoints
- [ ] Log authentication events
- [ ] Add security headers

## Questions to Resolve
1. Should we use HttpOnly cookies or Authorization header for refresh tokens?
2. What's the refresh token rotation strategy (immediate or grace period)?
3. Do we need device tracking for multi-device sessions?
```

### Step 5: Start Implementation

```bash
# Start the task with full context loaded
roadmap start backend-3-task-015
roadmap assign backend-3-task-015 web-developer

# Context already loaded, prep doc available for reference
# Begin implementation following the checklist
```

### Step 6: Complete and Summarize Sprint

```bash
# After completing the task
roadmap complete backend-3-task-015

# Complete remaining tasks...
roadmap complete backend-3

# Generate dependency summary for future sprints
roadmap summarize backend-3

# Generate task summaries
roadmap summarize backend-3 --task backend-3-task-015
```

**Generated Summary (excerpt):**
```yaml
dependency_summary: |
  This sprint implemented: Authentication & Authorization

  **Goals Achieved:**
  1. JWT-based authentication with refresh token rotation
  2. Role-based authorization middleware
  3. Secure session management

  **Key Outputs:**
  - JWT utilities (sign, verify, refresh)
  - Auth middleware for protected routes
  - Refresh token system with Redis storage
  - Role-based access control (RBAC)

  **Critical Learnings:**
  - Token rotation prevents replay attacks
  - Separate access (15min) and refresh (7 day) token lifetimes
  - Store refresh tokens in HttpOnly cookies for XSS protection
  - Use tokenVersion in DB for instant revocation

  **For dependencies:** Use auth middleware and JWT utilities.
  **Full context:** See `.vibey/sprint_docs/backend-3/`

task_summaries:
  backend-3-task-015:
    summary: "Implemented JWT authentication with refresh token rotation"
    outputs:
      - "JWT signing/verification utilities in auth/jwt.js"
      - "Auth middleware in middleware/auth.js"
      - "Refresh token rotation endpoint /auth/refresh"
    interfaces:
      - "authMiddleware(req, res, next)"
      - "generateAccessToken(userId)"
      - "generateRefreshToken(userId)"
      - "verifyToken(token)"
    gotchas:
      - "Refresh tokens MUST be stored in HttpOnly cookies"
      - "Access token expiry should be short (15min max)"
      - "Token rotation invalidates old refresh token immediately"
```

### Step 7: Future Tasks Benefit from Summary

When `backend-4` needs authentication context:

```bash
roadmap context backend-4-task-001
```

Loads:
- **backend-3 summary** (~700 tokens) instead of full docs (~8,400 tokens)
- Gets exactly what's needed: outputs, interfaces, gotchas
- **88% reduction** in context size

### Key Takeaways

**Without Context Loading:**
- Read 15 sprints manually
- 40+ files to scan
- 100,000+ tokens (doesn't fit in context window)
- Easy to miss critical details
- Time-consuming and error-prone

**With Context Loading:**
- `roadmap context` → 8,100 tokens (78% reduction)
- `roadmap prepare` → Deep analysis for complex tasks
- Automatic hierarchical loading
- Critical information preserved
- Future sprints benefit from summaries

**Best Practice:**
1. Always run `roadmap context <task-id>` before starting
2. Use `roadmap prepare <task-id>` for complex/integration tasks
3. Generate summaries after sprint completion
4. Review prep docs to catch integration issues early

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
