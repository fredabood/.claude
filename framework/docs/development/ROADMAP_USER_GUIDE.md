# Roadmap System User Guide

**Version:** 1.0
**Last Updated:** 2025-11-07
**Status:** Production Ready

---

## Table of Contents

1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Getting Started](#getting-started)
4. [Daily Workflows](#daily-workflows)
5. [Advanced Features](#advanced-features)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Reference](#reference)

---

## Introduction

### What is the Roadmap System?

The Roadmap Object Hierarchy is a comprehensive project management system built into the Vibey framework. It provides structured tracking of development work through a four-tier hierarchy:

```
Roadmap
  └── Track (major feature area)
      └── Sprint (time-boxed work unit)
          └── Task (atomic work item)
```

**Key Features:**
- ✅ **Structured Hierarchy** - Clear organization from vision to tasks
- ✅ **Intelligent Agent Routing** - Automatic task-to-agent matching
- ✅ **Automatic Status Progression** - Smart state transitions
- ✅ **Dependency Management** - Graph-based dependency tracking
- ✅ **Quality Gates** - Three-tier gate system (development, completion, production)
- ✅ **Version Management** - Semantic versioning with strategy-based bumping
- ✅ **Batch Operations** - Mass updates across multiple tasks
- ✅ **Health Validation** - Comprehensive roadmap health checks

### Why Use the Roadmap System?

**For Solo Developers:**
- Track complex projects with multiple workstreams
- Never lose track of dependencies
- Automatic progress calculation
- Clear visibility into what's next

**For Teams:**
- Intelligent agent/developer assignment recommendations
- Workload distribution tracking
- Structured handoffs between team members
- Quality gates ensure completeness

**For AI-Assisted Development:**
- Agents know exactly what to work on
- Automatic routing to specialized agents
- Context preservation across sessions
- Dogfooding: Vibey uses this system to manage itself!

---

## Core Concepts

### 1. The Four-Tier Hierarchy

#### Roadmap
The top-level container representing your entire project or product.

**Properties:**
- ID and name
- Version (semantic versioning)
- Strategy (how it progresses)
- Contains: Multiple tracks

**Example:**
```yaml
roadmap:
  id: "vibey-framework-v2"
  name: "Vibey Multi-Platform Agent Framework"
  version: "1.2.0"
  version_strategy:
    bump_on: "track_completion"
    bump_type: "minor"
```

#### Track
A major feature area or workstream that spans multiple sprints.

**Properties:**
- ID and name
- Status and progress
- Priority level
- Dependencies and blockers
- Contains: Multiple sprints

**Example:**
```yaml
track:
  id: "roadmap-system"
  name: "Roadmap Object Hierarchy Implementation"
  priority: "critical"
  sprints_total: 6
  sprints_completed: 5
```

#### Sprint
A time-boxed work unit (typically 1-2 weeks) focused on specific deliverables.

**Properties:**
- ID and name (format: `track-id-N`)
- Status and timing
- Estimated duration
- Quality gates
- Contains: Multiple tasks

**Example:**
```yaml
sprint:
  id: "roadmap-system-5"
  name: "Agent Integration & Auto-routing"
  status: "completed"
  estimated_duration: "2 weeks"
  tasks_count: 9
```

#### Task
An atomic work item that can be completed in one session.

**Properties:**
- ID (format: `sprint-id-task-NNN`)
- Type (development, testing, documentation, gate)
- Status and timing
- Assigned agent
- Dependencies

**Example:**
```yaml
task:
  id: "roadmap-system-5-task-001"
  name: "Create agent routing library"
  type: "development"
  status: "completed"
  assigned_agent: "web-developer"
```

### 2. Status Lifecycle

#### Sprint Status Flow
```
not_started
    ↓
in_progress (start working)
    ↓
completion_gate_check (all dev tasks done)
    ↓
completed (all gates passed)
    ↓
production_gate_check (ready for release)
    ↓
production_ready
    ↓
deployed
```

#### Task Status Flow
```
not_started
    ↓
in_progress
    ↓
completed
```

**Automatic Progression:**
The system automatically progresses sprints to `completion_gate_check` when all development tasks are complete. This ensures quality gates are enforced.

### 3. Quality Gates

Three types of gates ensure work quality:

#### Development Gates
Run during active development. Examples:
- Unit tests
- Code review
- Linting/formatting

#### Completion Gates
Run before marking sprint complete. Examples:
- Integration tests
- Documentation review
- Security audit

#### Production Gates
Run before production deployment. Examples:
- Performance testing
- Load testing
- Final security review

**Gate Properties:**
```yaml
quality_gates:
  - name: "Unit Tests"
    threshold: 90
    blocking: true
    status: "passed"
```

### 4. Dependencies and Blockers

#### Dependency Types
- **Track dependencies** - One track depends on another
- **Sprint dependencies** - One sprint depends on another
- **Task dependencies** - One task depends on another

#### Dependency Format
```yaml
dependencies:
  - type: "sprint"
    target_id: "backend-1"
    at_status: "completed"
    reason: "Need backend API before frontend"
```

#### Automatic Blocker Computation
The system automatically computes blockers based on:
- Dependency status (is the dependency satisfied?)
- Circular dependency detection
- Status satisfaction rules

### 5. Agent Routing

The system includes intelligent agent routing for task assignment.

#### Available Agents
- **web-developer** - Web development, APIs, full-stack
- **ml-engineer** - Machine learning, data science
- **test-engineer** - Testing, QA, test automation
- **docs-writer** - Documentation, technical writing
- **security-auditor** - Security, vulnerability assessment
- **performance-engineer** - Performance optimization
- **observability-engineer** - Logging, monitoring, tracing
- **coordinator** - Project coordination, orchestration

#### Recommendation Algorithm
```
Confidence Score = Task Type Match (50%) + Keyword Match (50%)
```

The system analyzes:
- Task name and description
- Task type (development, testing, documentation, etc.)
- Keywords in task text
- Agent specialties and capabilities

---

## Getting Started

### Prerequisites

- Python 3.7 or higher
- PyYAML library (`pip install pyyaml`)
- Git (optional, for version tagging)

### Installation

1. **Add CLI to PATH:**
```bash
export PATH="$PATH:/path/to/vibey/framework/scripts"
```

Or create a symlink:
```bash
ln -s /path/to/vibey/framework/scripts/roadmap /usr/local/bin/roadmap
```

2. **Verify installation:**
```bash
roadmap --version
```

### Creating Your First Roadmap

#### Option 1: Interactive Mode
```bash
roadmap init
```

The CLI will ask you:
- Roadmap ID (e.g., "my-project")
- Roadmap name (e.g., "My Awesome Project")
- Initial version (default: 1.0.0)
- Version bump strategy
- Version bump type

#### Option 2: Non-Interactive Mode
```bash
roadmap init \
  --id my-project \
  --name "My Awesome Project" \
  --version 1.0.0 \
  --bump-on sprint_completion \
  --bump-type minor
```

#### What Gets Created
```
.vibey/
├── roadmap.yaml           # Roadmap root
├── tracks/               # Track definitions
├── sprints/              # Sprint definitions
├── tasks/                # Task definitions
└── activity/             # Activity logs
```

### Creating Your First Track

Create a file: `.vibey/tracks/backend.yaml`

```yaml
track:
  id: "backend"
  name: "Backend API Development"
  roadmap_id: "my-project"
  status: "not_started"
  priority: "high"

  sprints:
    - id: "backend-1"
      name: "Authentication & User Management"
      status: "not_started"
      estimated_duration: "2 weeks"
      tasks_count: 8

    - id: "backend-2"
      name: "Core Business Logic"
      status: "not_started"
      estimated_duration: "3 weeks"
      tasks_count: 12

  dependencies: []
  blocks: []
```

### Creating Your First Sprint

Create a file: `.vibey/sprints/backend-1.yaml`

```yaml
sprint:
  id: "backend-1"
  name: "Authentication & User Management"
  track_id: "backend"
  roadmap_id: "my-project"

  status: "not_started"
  estimated_duration: "2 weeks"

  quality_gates:
    - name: "Unit Tests"
      threshold: 90
      blocking: true
      status: "not_run"

    - name: "Security Review"
      threshold: 95
      blocking: true
      status: "not_run"

  dependencies: []
  blocks: []
```

### Creating Your First Tasks

Create a file: `.vibey/tasks/backend-1-tasks.yaml`

```yaml
tasks:
  - id: "backend-1-task-001"
    sprint_id: "backend-1"
    track_id: "backend"
    roadmap_id: "my-project"

    name: "Design authentication schema"
    description: "Create database schema for users, sessions, and tokens"
    type: "development"
    status: "not_started"

    estimated_duration: "4 hours"
    dependencies: []

  - id: "backend-1-task-002"
    sprint_id: "backend-1"
    track_id: "backend"
    roadmap_id: "my-project"

    name: "Implement user registration endpoint"
    description: "POST /api/users endpoint with validation"
    type: "development"
    status: "not_started"

    estimated_duration: "6 hours"
    dependencies:
      - type: "task"
        target_id: "backend-1-task-001"
        at_status: "completed"

  # Add gate tasks
  - id: "backend-1-task-gate-001"
    sprint_id: "backend-1"
    track_id: "backend"
    roadmap_id: "my-project"

    name: "Unit Tests - Authentication"
    description: "Write comprehensive unit tests for auth endpoints"
    type: "gate"
    status: "not_started"

    gate_name: "Unit Tests"
    gate_type: "completion"
```

### Verify Your Setup

```bash
# View roadmap status
roadmap status

# List all tracks
roadmap list tracks

# Show sprint details
roadmap show backend-1
```

---

## Daily Workflows

### Morning: What Should I Work On?

```bash
# Check overall status
roadmap status

# Get intelligent task recommendations
roadmap recommend

# Get recommendations for a specific agent
roadmap recommend --agent web-developer

# See what tasks are available
roadmap list tasks --status not_started
```

### Starting Work

```bash
# Start a sprint (if not started)
roadmap start backend-1

# Get the best task to work on
roadmap recommend --agent web-developer --limit 3

# Start a task
roadmap start backend-1-task-002

# Assign to yourself (or an agent)
roadmap assign backend-1-task-002 web-developer
```

### During Work

```bash
# Check if task is blocked
roadmap deps backend-1-task-002 --blockers

# View task details
roadmap show backend-1-task-002

# Check sprint progress
roadmap show backend-1
```

### Completing Work

```bash
# Complete a task
roadmap complete backend-1-task-002

# Refresh progress calculations
roadmap progress --refresh

# Check if sprint is ready to complete
roadmap show backend-1
```

### End of Day

```bash
# Check overall progress
roadmap status

# View agent workload
roadmap agents --workload

# See what's in progress
roadmap list tasks --status in_progress
```

---

## Advanced Features

### 1. Intelligent Task Recommendations

#### Get Recommended Tasks
```bash
# Priority-based recommendations
roadmap recommend

# Limit results
roadmap recommend --limit 3

# For specific agent
roadmap recommend --agent test-engineer
```

**Priority Factors:**
- Sprint status (active sprints prioritized)
- Existing assignments (assigned tasks boosted)
- Agent confidence match
- Blocked tasks filtered out

#### Get Agent Recommendations for a Task
```bash
roadmap recommend --task backend-1-task-003
```

Output shows confidence scores:
```
1. web-developer          ████████████████████░░░░░░░░ 85%
2. ml-engineer            ████████░░░░░░░░░░░░░░░░░░░░ 40%
3. coordinator            ██████░░░░░░░░░░░░░░░░░░░░░░ 30%
```

### 2. Agent Workload Management

#### View Overall Workload
```bash
roadmap agents --workload
```

Shows:
- Total tasks per agent
- In progress count
- Not started count
- Completed count
- Completion rate
- Active tasks

#### View Specific Agent Details
```bash
roadmap agents --agent web-developer
```

Shows all tasks assigned to that agent with full details.

#### View Agent Capabilities
```bash
roadmap agents --capabilities
```

Lists all available agents with their:
- Specialties
- Task types they handle
- Keywords they match

### 3. Batch Operations

#### Batch Complete Tasks
```bash
# Complete all tasks in a sprint
roadmap batch complete sprint backend-1

# Complete all dev tasks in a track
roadmap batch complete track backend --filter dev

# Complete all tasks in entire roadmap
roadmap batch complete roadmap
```

#### Batch Assign Tasks
```bash
# Assign all unassigned tasks in sprint
roadmap batch assign sprint backend-1 --agent web-developer

# Assign all dev tasks in track
roadmap batch assign track backend --agent web-developer --filter dev

# Assign by status
roadmap batch assign sprint backend-1 --agent web-developer --status not_started
```

### 4. Version Management

#### Show Current Version
```bash
roadmap version --show
```

#### Bump Version
```bash
# Use roadmap's configured strategy
roadmap version --bump

# Manual bump
roadmap version --bump --type minor --message "Added agent routing"

# Bump and create git tag
roadmap version --bump --tag
```

**Version Strategy Options:**
- `bump_on`: `sprint_completion`, `track_completion`, or `manual`
- `bump_type`: `minor` or `patch` (for automatic bumps)

### 5. Validation and Health Checks

#### Run All Health Checks
```bash
roadmap validate
```

Checks for:
- ✅ Circular dependencies
- ✅ Orphaned files
- ✅ Invalid references
- ✅ Progress consistency
- ✅ Schema validation
- ✅ Blocker consistency

#### Verbose Output
```bash
roadmap validate --verbose
```

#### Attempt Auto-Fix
```bash
roadmap validate --fix
```

### 6. Dependency Management

#### View Overall Dependency Graph
```bash
roadmap deps
```

Shows all dependencies and any circular dependencies detected.

#### Check Specific Object Dependencies
```bash
# Show all dependencies for an object
roadmap deps backend-1

# Show only blockers
roadmap deps backend-1 --blockers

# Show only dependents (what depends on this)
roadmap deps backend-1 --dependents
```

#### Understanding Blockers
Blockers are automatically computed. An object is blocked if:
- It has dependencies that aren't satisfied
- It's part of a circular dependency chain

```bash
# See what's blocking a task
roadmap deps backend-1-task-005 --blockers

# See everything that's blocked
roadmap list tasks --status not_started | xargs -I {} roadmap deps {} --blockers
```

### 7. Context Loading & Summaries

#### The Context Explosion Problem

As projects grow, tasks accumulate dependencies. A task with 5 direct dependencies, each with 3 dependencies of their own, creates 15+ sprints worth of documentation to read - potentially 40+ files and 100,000+ tokens!

**Solution:** Six-strategy hybrid approach with 57-90% context reduction.

#### Strategy Overview

| Strategy | Purpose | When to Use |
|----------|---------|-------------|
| **Dependency Summaries** | 500-word sprint overviews | After sprint completion |
| **Task Summaries** | Granular outputs/interfaces | After sprint completion |
| **Context Modes** | Configurable detail levels | When starting tasks |
| **Hierarchical Loading** | Distance-based mode selection | When starting tasks |
| **Lazy Loading** | Caching & on-demand loading | Automatic |
| **Preparation Mode** | Deep analysis for complex tasks | Before complex tasks |

#### Context Modes

| Mode | Size | Use Case | Content |
|------|------|----------|---------|
| **Minimal** | ~100 tokens | Far dependencies (distance 2+) | Outputs only |
| **Summary** | ~700 tokens | Direct dependencies (distance 1) | Sprint & task summaries |
| **Full** | ~5,700 tokens | Current sprint | All documentation |

#### Generate Summaries (After Sprint Completion)

```bash
# Generate sprint dependency summary
roadmap summarize backend-1

# Generate task summaries
roadmap summarize backend-1 --task backend-1-task-001
roadmap summarize backend-1 --task backend-1-task-002

# Batch: summarize all completed sprints
roadmap summarize --all --completed

# Force regeneration
roadmap summarize backend-1 --force
```

**What gets generated:**
- **Dependency Summary** (~500 words) - Goals, outputs, interfaces, learnings
- **Task Summaries** - Outputs, interfaces, gotchas per task
- Saved to sprint YAML: `dependency_summary` and `task_summaries` fields

#### Load Context (When Starting a Task)

```bash
# Load hierarchical context for a task
roadmap context backend-1-task-015

# Output:
🔍 Loading context for task: backend-1-task-015
**Task:** Implement user authentication
**Sprint:** backend-1
**Type:** development

📄 Current Sprint Docs: ~5,700 tokens

📚 Dependency Analysis:
   Total dependencies: 5
   🔵 backend-1-task-001 (summary) ~700 tokens
   🔵 backend-1-task-002 (summary) ~700 tokens
   ⚪ core-1-task-003 (minimal) ~100 tokens
   ⚪ core-1-task-005 (minimal) ~100 tokens
   ⚪ core-2-task-001 (minimal) ~100 tokens

📊 Context Summary:
   Current sprint: ~5,700 tokens
   Dependencies: ~1,700 tokens
   Total: ~7,400 tokens (78% reduction from full ~34,200 tokens)
```

**Hierarchical Loading:**
- Distance 1 (direct deps) → Summary mode (~700 tokens)
- Distance 2 (transitive) → Minimal mode (~100 tokens)
- Distance 3+ → Skipped

```bash
# Override mode for all dependencies
roadmap context backend-1-task-015 --mode full

# Display full context details
roadmap context backend-1-task-015 --show-full

# Load deeper dependencies
roadmap context backend-1-task-015 --max-distance 3
```

#### Preparation Mode (Complex Tasks)

For tasks with many dependencies or complex integration requirements, use preparation mode:

```bash
# Generate preparation document (loads ALL dependencies)
roadmap prepare backend-1-task-015

# Output:
✅ Preparation document generated
   Path: .vibey/sprint_docs/backend-1/prep/backend-1-task-015.md
   Dependencies analyzed: 5
   Full context loaded: ~34,200 tokens
```

**Preparation document includes:**
- Task overview and goals
- Dependency analysis (what each provides, how to integrate)
- Key learnings from dependency sprints
- Critical integration points and interfaces
- Implementation checklist
- Questions to resolve before starting

```bash
# View existing preparation document
roadmap prepare backend-1-task-015 --show

# Regenerate if outdated
roadmap prepare backend-1-task-015 --regenerate

# List all tasks with prep docs
roadmap prepare --list
```

#### Recommended Workflow

```bash
# 1. After completing a sprint
roadmap complete backend-1
roadmap summarize backend-1              # Generate dependency summary
# (Task summaries can be generated individually or in batch)

# 2. Before starting a new task
roadmap recommend                         # Get next task
roadmap context backend-1-task-015        # Load context

# 3. If task is complex
roadmap prepare backend-1-task-015        # Deep analysis
roadmap prepare backend-1-task-015 --show # Review prep doc

# 4. During implementation
roadmap start backend-1-task-015
# (Context already loaded, prep doc available for reference)
```

#### Benefits

**Without context loading:**
- Task with 5 dependencies → 15 sprints → 40+ files → 100,000+ tokens
- Manual reading and synthesis required
- Easy to miss critical integration details
- Context doesn't fit in LLM window

**With context loading:**
- Same task → 7,400 tokens (78% reduction)
- Automatic hierarchical loading
- Critical information preserved
- Fits comfortably in context window
- Preparation docs for deep dives when needed

---

## Best Practices

### 1. Project Structure

**Track Organization:**
- Keep tracks focused on major feature areas
- Typical project has 3-8 tracks
- Use priority levels: `critical`, `high`, `medium`, `low`

**Sprint Sizing:**
- 1-2 weeks per sprint
- 5-12 tasks per sprint
- Mix development and gate tasks

**Task Granularity:**
- 2-8 hours per task
- Atomic and testable
- Clear acceptance criteria

### 2. Status Management

**Let the System Work:**
- Don't manually set sprint status to `completion_gate_check`
- Complete all dev tasks → system auto-progresses
- Complete all gate tasks → system allows completion

**Progress Updates:**
- Run `roadmap progress --refresh` after batch changes
- System usually auto-updates, but refresh ensures accuracy

### 3. Dependencies

**Dependency Guidelines:**
- Use `at_status: completed` for most dependencies
- Use `at_status: in_progress` for parallel work
- Keep dependency chains shallow (2-3 levels max)

**Avoid Circular Dependencies:**
- Design tracks/sprints to flow linearly
- Use `roadmap validate` to catch circles early
- Break circles by removing unnecessary dependencies

### 4. Quality Gates

**Gate Design:**
- 2-4 gates per sprint
- Use `blocking: true` for critical gates
- Set realistic thresholds (80-95%)

**Gate Types:**
- Development: Ongoing checks (unit tests, linting)
- Completion: Pre-completion checks (integration tests, docs)
- Production: Pre-deployment checks (load tests, security)

### 5. Agent Assignment

**Use Recommendations:**
```bash
# Get best match for a task
roadmap recommend --task backend-1-task-003

# Let system suggest next task
roadmap recommend --agent web-developer
```

**Manual Assignment When:**
- Task requires specific expertise
- Balancing workload manually
- Training/knowledge transfer

**Check Workload:**
```bash
roadmap agents --workload
```

### 6. Version Management

**Automatic Versioning:**
- Use `bump_on: sprint_completion` for frequent releases
- Use `bump_on: track_completion` for milestone releases
- Use `bump_on: manual` for controlled releases

**Git Tagging:**
```bash
roadmap version --bump --tag
```

### 7. Daily Habits

**Morning:**
1. `roadmap status` - See big picture
2. `roadmap recommend` - Find next task
3. `roadmap start <task>` - Begin work

**During Work:**
1. `roadmap deps <task> --blockers` - Check blockers
2. `roadmap show <sprint>` - Monitor progress

**End of Day:**
1. `roadmap complete <task>` - Mark work done
2. `roadmap agents --workload` - Check distribution
3. `roadmap status` - See progress

---

## Troubleshooting

### Common Issues

#### "No roadmap found"
```bash
# Solution: Initialize roadmap
roadmap init
```

#### "Object not found"
```bash
# Find correct ID
roadmap list tracks
roadmap list sprints
roadmap find "keyword"
```

#### "Cannot progress sprint status"
```bash
# Check what's blocking progression
roadmap show backend-1

# Common causes:
# - Development tasks not complete
# - Blocking gates failed
# - Dependencies not satisfied
```

#### Import Errors
```bash
# Install dependencies
pip install pyyaml

# Or use pip3
pip3 install pyyaml
```

#### Permission Errors
```bash
# Make CLI executable
chmod +x /path/to/vibey/framework/scripts/roadmap
```

### Validation Errors

#### Circular Dependencies Detected
```bash
# Run validation
roadmap validate --verbose

# Review dependency chains
roadmap deps

# Fix: Remove unnecessary dependencies or restructure
```

#### Orphaned Files
```bash
# Run validation with auto-fix
roadmap validate --fix

# Or manually clean up unreferenced files in .vibey/
```

#### Progress Inconsistency
```bash
# Refresh all progress
roadmap progress --refresh

# Validate again
roadmap validate
```

### Performance Issues

#### Slow Commands
```bash
# For large roadmaps, use filters
roadmap list tasks --status in_progress

# Use JSON + jq for processing
roadmap list tasks --json | jq '.tasks[] | select(.assigned_agent == "web-developer")'
```

### Getting Help

```bash
# General help
roadmap --help

# Command-specific help
roadmap status --help
roadmap recommend --help
```

---

## Reference

### Quick Command Reference

**Query:**
- `roadmap status` - Overall status
- `roadmap show <id>` - Object details
- `roadmap list [type]` - List objects
- `roadmap find <query>` - Search objects
- `roadmap deps [id]` - Dependencies & blockers

**Update:**
- `roadmap init` - Initialize roadmap
- `roadmap start <id>` - Start sprint/task
- `roadmap complete <id>` - Complete sprint/task
- `roadmap assign <task> <agent>` - Assign task
- `roadmap progress --refresh` - Refresh progress
- `roadmap batch <op> <scope> [id]` - Batch operations

**Management:**
- `roadmap version {--show|--bump}` - Version management
- `roadmap validate [--fix]` - Health checks

**Agent:**
- `roadmap recommend` - Task/agent recommendations
- `roadmap agents [--workload]` - Agent workload

### File Structure Reference

```
.vibey/
├── roadmap.yaml                      # Roadmap root
├── tracks/
│   ├── backend.yaml                  # Track definition
│   ├── frontend.yaml
│   └── infrastructure.yaml
├── sprints/
│   ├── backend-1.yaml                # Sprint definition
│   ├── backend-2.yaml
│   └── frontend-1.yaml
├── tasks/
│   ├── backend-1-tasks.yaml          # Tasks for sprint
│   ├── backend-2-tasks.yaml
│   └── frontend-1-tasks.yaml
└── activity/
    ├── 2025-11-07.log                # Daily activity logs
    └── 2025-11-08.log
```

### Status Reference

**Sprint Statuses:**
- `not_started` - Not yet started
- `in_progress` - Currently in progress
- `paused` - Paused/on hold
- `completion_gate_check` - Checking completion gates
- `completed` - Completed
- `production_gate_check` - Checking production gates
- `production_ready` - Ready for production
- `deployed` - Deployed to production
- `won't_do` - Won't be done

**Task Statuses:**
- `not_started` - Not yet started
- `in_progress` - Currently in progress
- `completed` - Completed

### Priority Levels

- `critical` - Must be done, highest priority
- `high` - Should be done soon
- `medium` - Normal priority
- `low` - Can be deferred

### Agent Types

1. **web-developer** - Web APIs, full-stack, backend
2. **ml-engineer** - ML models, data science, training
3. **test-engineer** - Testing, QA, test automation
4. **docs-writer** - Documentation, technical writing
5. **security-auditor** - Security, vulnerability assessment
6. **performance-engineer** - Performance, optimization
7. **observability-engineer** - Logging, monitoring, tracing
8. **coordinator** - Coordination, orchestration

---

## Appendix: Example Roadmaps

### Example 1: Web Application

```yaml
# .vibey/roadmap.yaml
roadmap:
  id: "webapp-v1"
  name: "SaaS Web Application"
  version: "1.0.0"
  version_strategy:
    bump_on: "sprint_completion"
    bump_type: "minor"

# .vibey/tracks/backend.yaml
track:
  id: "backend"
  name: "Backend API Development"
  priority: "critical"
  sprints:
    - id: "backend-1"
      name: "Authentication & User Management"
    - id: "backend-2"
      name: "Core Business Logic"
    - id: "backend-3"
      name: "Third-Party Integrations"
```

### Example 2: Machine Learning Project

```yaml
# .vibey/roadmap.yaml
roadmap:
  id: "ml-classifier"
  name: "Image Classification Model"
  version: "0.1.0"
  version_strategy:
    bump_on: "track_completion"
    bump_type: "minor"

# .vibey/tracks/data-pipeline.yaml
track:
  id: "data-pipeline"
  name: "Data Pipeline Development"
  priority: "critical"
  sprints:
    - id: "data-pipeline-1"
      name: "Data Collection & Validation"
    - id: "data-pipeline-2"
      name: "Data Preprocessing & Augmentation"

# .vibey/tracks/model.yaml
track:
  id: "model"
  name: "Model Development"
  priority: "high"
  dependencies:
    - type: "track"
      target_id: "data-pipeline"
      at_status: "completed"
  sprints:
    - id: "model-1"
      name: "Baseline Model"
    - id: "model-2"
      name: "Model Optimization"
```

### Example 3: Infrastructure Project

```yaml
# .vibey/roadmap.yaml
roadmap:
  id: "k8s-migration"
  name: "Kubernetes Migration"
  version: "1.0.0"
  version_strategy:
    bump_on: "manual"
    bump_type: "minor"

# .vibey/tracks/infra-setup.yaml
track:
  id: "infra-setup"
  name: "Infrastructure Setup"
  priority: "critical"
  sprints:
    - id: "infra-setup-1"
      name: "Kubernetes Cluster Setup"
    - id: "infra-setup-2"
      name: "CI/CD Pipeline"
    - id: "infra-setup-3"
      name: "Monitoring & Observability"
```

---

**End of User Guide**

For more information:
- CLI Reference: `framework/scripts/CLI.md`
- Implementation Details: `docs/development/ROADMAP_OBJECT_HIERARCHY.md`
- Implementation Plan: `docs/development/ROADMAP_IMPLEMENTATION_PLAN.md`
