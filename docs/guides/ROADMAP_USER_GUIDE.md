# Roadmap System - User Guide

**Version:** 2.1 (Gate Model)
**Last Updated:** 2025-11-09
**Status:** Production Ready

---

## Table of Contents

1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Getting Started](#getting-started)
4. [Object Hierarchy](#object-hierarchy)
5. [Working with Roadmaps](#working-with-roadmaps)
6. [Working with Tracks](#working-with-tracks)
7. [Working with Sprints](#working-with-sprints)
8. [Working with Tasks](#working-with-tasks)
9. [Dependencies & Blockers](#dependencies--blockers)
10. [Quality Gates](#quality-gates)
11. [Version Management](#version-management)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)

---

## Introduction

The Vibey Roadmap System is a comprehensive project management framework designed specifically for AI-assisted development. It provides structured tracking of projects from high-level roadmaps down to individual context-window-sized tasks.

### What is the Roadmap System?

The roadmap system is a **4-tier hierarchy** for managing complex software projects:

```
Roadmap (entire project)
  └─ Track (parallelization boundary - e.g., backend, frontend)
      └─ Sprint (production-deployable unit)
          └─ Task (context-window sized work unit)
```

### Why Use the Roadmap System?

**Benefits:**
- ✅ **Structured Planning** - Clear hierarchy from vision to execution
- ✅ **Parallel Execution** - Tracks enable team/feature parallelization
- ✅ **Quality Gates** - Automated checks prevent shipping incomplete work
- ✅ **Dependency Tracking** - Automatic blocker detection and resolution
- ✅ **Version Management** - Semantic versioning tied to roadmap progress
- ✅ **AI-Optimized** - Tasks sized for LLM context windows
- ✅ **Comprehensive History** - Unified activity log for entire project

### When to Use It

**Good Use Cases:**
- Multi-track projects (backend + frontend + mobile + infra)
- Long-running projects (3+ months)
- Projects with multiple sprints
- Projects requiring quality gates
- Teams using AI coding assistants

**When NOT to Use:**
- Single-file scripts
- Proof-of-concept prototypes
- Projects with <3 tasks
- One-time data analysis

---

## Core Concepts

### The 4-Tier Hierarchy

#### 1. Roadmap (Top Level)

The **Roadmap** is the entire project.

**Characteristics:**
- Unified activity log (all events)
- Version management (semantic versioning)
- Aggregate progress tracking
- External dependencies

**Example:** "Vibey Multi-Platform Agent Framework v2.0"

#### 2. Track (Parallelization Boundary)

A **Track** is a major work stream that can run in parallel with other tracks.

**Characteristics:**
- Parallel execution capability
- Natural team/feature alignment
- Track-level quality gates
- Track-scoped sprint numbering

**Examples:** `backend`, `frontend`, `mobile`, `infrastructure`, `documentation`

#### 3. Sprint (Production-Deployable Unit)

A **Sprint** is a logical unit of work that can be pushed to production.

**Characteristics:**
- Production-deployable
- Has completion gates AND production gates
- Can reach `production_ready` status
- Contains development tasks + quality gate tasks

**Examples:** `backend-1` (User Authentication), `frontend-2` (Dashboard UI)

#### 4. Task (Context-Window Unit)

A **Task** is the smallest unit of work, sized to fit within an LLM's context window.

**Characteristics:**
- Context-window sized (~2K-8K tokens)
- No production concerns (no `production_ready` status)
- Can be development task OR quality gate task
- Highly focused and specific

**Examples:** `backend-1-task-001` (Implement registration endpoint)

---

### ID Convention

IDs follow a strict hierarchical pattern:

```
Roadmap ID:  vibey-framework-v2
Track ID:    backend
Sprint ID:   backend-1  (track-scoped)
Task ID:     backend-1-task-001  (sprint-scoped)
```

**Rules:**
- Lowercase with hyphens
- Sprint IDs start with track ID
- Task IDs start with sprint ID
- Numbers are sequential within scope

---

### Status Progression

Different objects have different status sets:

**Tasks (Limited Set):**
```
not_started → in_progress → paused
                         → completed
                         → won't_do
```

**Sprints & Tracks (Full Set):**
```
not_started → in_progress → paused
                         → completion_gate_check
                         → completed
                         → production_gate_check
                         → production_ready
                         → deployed
                         → won't_do
```

---

### The Gate Model

Quality is enforced through a **3-tier gate system**:

#### 1. Development Gates (External Dependencies)

Dependencies on other sprints/tasks that must complete before starting work.

**Example:**
```yaml
dependencies:
  - type: task
    target_id: "backend-1-task-001"
    target_status: "completed"
    reason: "Requires user schema"
```

#### 2. Completion Gates (Hygiene Checks)

Quality gate tasks that block sprint completion.

**Common Examples:**
- Documentation review
- Git/CI/CD hygiene
- Code formatting
- Linting checks

**Example:**
```yaml
- id: "backend-1-gate-c001"
  task_type: "completion_gate"
  title: "Documentation Review"
  gate_info:
    blocks_status: "completed"
    threshold: 95
    is_blocking: true
```

#### 3. Production Gates (Production Readiness)

Quality gate tasks that block production deployment.

**Common Examples:**
- Unit tests (>90% coverage)
- Security audit
- Performance testing
- Load testing

**Example:**
```yaml
- id: "backend-1-gate-p001"
  task_type: "production_gate"
  title: "Security Audit"
  gate_info:
    blocks_status: "production_ready"
    threshold: 90
    is_blocking: true
```

---

## Getting Started

### Installation

The roadmap system is built into the Vibey framework. No additional installation required.

**Requirements:**
- Python 3.7+
- PyYAML (for YAML I/O)
- Git (for version management)

### Initialize a New Roadmap

```bash
python3 framework/scripts/roadmap-init.py \
  --id "my-project" \
  --name "My Amazing Project" \
  --dir .vibey
```

This creates:
```
.vibey/
├── roadmap.yaml         # Top-level roadmap state
├── roadmap/             # Hierarchical structure
└── roadmap_cache.json   # Performance cache
```

### Basic Workflow

**1. Create a track:**
```bash
python3 framework/scripts/roadmap-update.py \
  --track backend \
  --name "Backend Services" \
  --priority critical
```

**2. Create a sprint:**
```bash
python3 framework/scripts/roadmap-update.py \
  --sprint backend-1 \
  --name "User Authentication" \
  --track backend
```

**3. Add tasks:**
```bash
python3 framework/scripts/roadmap-update.py \
  --task backend-1-task-001 \
  --title "Implement registration endpoint" \
  --sprint backend-1
```

**4. Start work:**
```bash
python3 framework/scripts/roadmap-update.py \
  --start-task backend-1-task-001
```

**5. Complete work:**
```bash
python3 framework/scripts/roadmap-update.py \
  --complete-task backend-1-task-001 \
  --commits abc123
```

**6. Check status:**
```bash
python3 framework/scripts/roadmap-query.py --sprint backend-1
```

---

## Object Hierarchy

### File Structure

The roadmap system uses a **hierarchical directory structure**:

```
.vibey/roadmap/
├── backend/                    # Track directory
│   ├── .id                     # Track ULID
│   ├── track.yaml              # Track state
│   ├── table_of_contents.json  # Navigation
│   ├── context/                # Track research
│   │
│   └── backend-1/              # Sprint directory
│       ├── .id                 # Sprint ULID
│       ├── sprint.yaml         # Sprint state
│       ├── table_of_contents.json
│       ├── context/            # Sprint artifacts
│       │
│       └── backend-1-task-001/ # Task directory
│           ├── .id             # Task ULID
│           ├── task.yaml       # Task state
│           └── context/        # Task artifacts
```

### ULID-Based IDs

Each object has an immutable ULID stored in `.id` files:

```
track_01JB3QVDZ8TRK9XN1FJFHGWPRM
sprint_01JB3QVE2CTYPXM2NKQR5HWVJT
task_01JB3QVEKR9XPWJ4VFZN8TGYHM
```

**Benefits:**
- Immutable (never changes)
- Sortable (by creation time)
- Unique (128-bit collision-free)
- Timestamped (encodes creation time)

---

## Working with Roadmaps

### Query Roadmap Status

```bash
# Show overall progress
python3 framework/scripts/roadmap-query.py --dir .vibey

# JSON output
python3 framework/scripts/roadmap-query.py --json
```

**Output:**
```
Roadmap: Vibey Multi-Platform Framework
Status: in_progress (58% complete)

Tracks: 3/11 complete
Sprints: 12/37 complete
Tasks: 97/166 complete

Current Version: 1.3.0
```

### Version Management

Roadmap versions follow semantic versioning:

```yaml
version: "1.2.0"
version_strategy:
  major_on: "roadmap_milestone"      # Manual
  minor_on: "track_completion"        # Automatic
  patch_on: "sprint_production_ready" # Automatic
```

**Bump version manually:**
```bash
python3 framework/scripts/roadmap-update.py \
  --bump-version major \
  --milestone "Multi-Platform Release"
```

### Activity Log

All events are logged at the roadmap level:

```yaml
activity_log:
  - timestamp: "2025-01-20T09:00:00Z"
    type: "sprint_started"
    description: "Started sprint backend-1"
    context:
      track_id: "backend"
      sprint_id: "backend-1"
```

**Query activity:**
```bash
python3 framework/scripts/roadmap-query.py --activity
```

---

## Working with Tracks

### Create a Track

```bash
python3 framework/scripts/roadmap-update.py \
  --track backend \
  --name "Backend Services Development" \
  --priority critical
```

### List Tracks

```bash
python3 framework/scripts/roadmap-query.py --track
```

### Track Dependencies

Tracks can depend on other tracks:

```yaml
track:
  id: frontend
  dependencies:
    - type: track
      target_id: backend
      target_status: production_ready
      reason: "Frontend needs backend APIs"
```

### Track Status

```bash
python3 framework/scripts/roadmap-query.py --track backend
```

---

## Working with Sprints

### Create a Sprint

```bash
python3 framework/scripts/roadmap-update.py \
  --sprint backend-1 \
  --name "User Authentication System" \
  --track backend \
  --estimated-duration "2 weeks"
```

### Sprint Lifecycle

**1. Start sprint:**
```bash
python3 framework/scripts/roadmap-update.py --start-sprint backend-1
```

**2. Work on tasks** (see Tasks section)

**3. Complete development tasks** → Sprint enters `completion_gate_check`

**4. Pass completion gates** → Sprint reaches `completed`

**5. Pass production gates** → Sprint reaches `production_ready`

**6. Deploy** → Sprint reaches `deployed`

### Sprint Progress

```bash
python3 framework/scripts/roadmap-query.py --sprint backend-1
```

**Output:**
```
Sprint: backend-1 (User Authentication System)
Status: production_ready

Progress:
  Development: 5/5 tasks (100%)
  Completion Gates: 2/2 passed
  Production Gates: 3/3 passed

Total: 10/10 tasks complete
```

---

## Working with Tasks

### Task Types

There are 3 types of tasks:

**1. Development Tasks (`task_type: development`)**
- Build functionality
- Can serve as development gates for external sprints
- Most common task type

**2. Completion Gate Tasks (`task_type: completion_gate`)**
- Hygiene checks (docs, CI/CD)
- Block sprint completion
- Highly isolated

**3. Production Gate Tasks (`task_type: production_gate`)**
- Production readiness (security, testing)
- Block production deployment
- Highly isolated

### Create Development Task

```bash
python3 framework/scripts/roadmap-update.py \
  --task backend-1-task-001 \
  --title "Implement user registration endpoint" \
  --description "Create POST /api/users/register endpoint with validation" \
  --sprint backend-1 \
  --task-type development \
  --assigned-agent web-developer \
  --priority high \
  --estimated-tokens 5000
```

### Create Quality Gate Task

```bash
python3 framework/scripts/roadmap-update.py \
  --task backend-1-gate-p001 \
  --title "Security Audit - Authentication" \
  --sprint backend-1 \
  --task-type production_gate \
  --gate-threshold 90 \
  --gate-blocks production_ready
```

### Task Lifecycle

```bash
# Start task
python3 framework/scripts/roadmap-update.py --start-task backend-1-task-001

# Complete task
python3 framework/scripts/roadmap-update.py \
  --complete-task backend-1-task-001 \
  --commits abc123,def456

# Check status
python3 framework/scripts/roadmap-query.py --task backend-1-task-001
```

---

## Dependencies & Blockers

### Understanding Dependencies

**Development Gates** (on tasks/sprints):
- External dependencies
- Must be satisfied before starting
- Defined in `dependencies` array

**Example:**
```yaml
dependencies:
  - type: task
    target_id: "backend-1-task-001"
    target_status: "completed"
    reason: "Requires database schema"
```

### Check Blockers

```bash
# Show all blockers
python3 framework/scripts/roadmap-query.py --blockers

# Show blockers for specific task
python3 framework/scripts/roadmap-query.py \
  --task backend-1-task-002 \
  --blockers
```

**Output:**
```
Task: backend-1-task-002
Blocked: YES

Blockers:
  1. backend-1-task-001 (task)
     Required: completed
     Current: in_progress
     Blocking since: 2025-01-20
```

### Dependency Visualization

```bash
# Show dependency graph
python3 framework/scripts/roadmap-query.py --dependencies
```

---

## Quality Gates

### Gate Configuration

Quality gates are task objects with special configuration:

```yaml
task:
  id: "backend-1-gate-p001"
  task_type: "production_gate"
  title: "Unit Tests"
  gate_info:
    blocks_status: "production_ready"
    threshold: 90
    score: 92
    is_blocking: true
```

### Running Quality Gates

Quality gates can be automated:

```bash
# Run security audit
python3 framework/scripts/roadmap-update.py \
  --run-gate backend-1-gate-p001 \
  --gate-command "npm run security-scan"
```

### Gate Results

```yaml
audit_results:
  passed: true
  score: 92
  threshold: 90
  output: "Security scan passed with 0 critical issues"
  timestamp: "2025-01-20T15:00:00Z"
```

---

## Version Management

### Semantic Versioning

Versions follow `MAJOR.MINOR.PATCH` format:

- **MAJOR**: Roadmap milestones (manual)
- **MINOR**: Track completions (automatic)
- **PATCH**: Sprint production ready (automatic)

### Version History

```yaml
version_history:
  - version: "1.0.0"
    date: "2025-06-01"
    milestone: "Initial Production Release"
    git_tag: "v1.0.0"

  - version: "1.1.0"
    date: "2025-09-15"
    milestone: "Multi-platform Support"
    git_tag: "v1.1.0"
```

### Git Integration

Versions are automatically tagged:

```bash
git tag v1.2.0
git push origin v1.2.0
```

---

## Best Practices

### 1. Task Sizing

✅ **DO:** Size tasks to fit in LLM context window (2K-8K tokens)
✅ **DO:** Break large features into multiple tasks
❌ **DON'T:** Create tasks >10K tokens

**Good Example:**
```
backend-1-task-001: Create User model
backend-1-task-002: Implement registration endpoint
backend-1-task-003: Write registration tests
```

**Bad Example:**
```
backend-1-task-001: Build entire authentication system
```

### 2. Use Quality Gates

✅ **DO:** Add completion gates for hygiene
✅ **DO:** Add production gates for readiness
✅ **DO:** Set realistic thresholds

**Recommended Gates:**
- Documentation Review (completion, 95%)
- Unit Tests (production, 90%)
- Security Audit (production, 90%)

### 3. Track Dependencies

✅ **DO:** Define dependencies explicitly
✅ **DO:** Use specific status requirements
✅ **DO:** Provide clear reasons

### 4. Keep Context Organized

✅ **DO:** Store research in context/ directories
✅ **DO:** Keep context flat (no subdirectories)
✅ **DO:** Use descriptive filenames

### 5. Commit Regularly

✅ **DO:** Link commits to tasks
✅ **DO:** Update task status after commits
✅ **DO:** Use clear commit messages

---

## Troubleshooting

### Common Issues

#### Issue: Task is blocked but I don't know why

**Solution:**
```bash
python3 framework/scripts/roadmap-query.py \
  --task backend-1-task-002 \
  --blockers
```

#### Issue: Sprint stuck in `completion_gate_check`

**Cause:** Completion gates haven't passed

**Solution:**
```bash
# Check which gates are failing
python3 framework/scripts/roadmap-query.py --sprint backend-1

# Run gates manually
python3 framework/scripts/roadmap-update.py \
  --run-gate backend-1-gate-c001
```

#### Issue: Version not bumping automatically

**Cause:** Version strategy not configured

**Solution:**
```yaml
# Edit roadmap.yaml
version_strategy:
  minor_on: "track_completion"
  patch_on: "sprint_production_ready"
```

#### Issue: Cache out of sync

**Solution:**
```bash
# Rebuild cache
python3 framework/scripts/roadmap-update.py --rebuild-cache
```

#### Issue: Progress calculations are incorrect or stale

**Cause:** Manual YAML edits, interrupted operations, or data migrations

**Solution:**
```bash
# Quick fix: Refresh sprint progress only
python3 framework/scripts/roadmap-update.py --refresh-progress

# Full fix: Recalculate entire hierarchy (bottom-up)
python3 framework/scripts/roadmap-update.py --recalculate-all

# With consistency verification
python3 framework/scripts/roadmap-update.py --recalculate-all --verify
```

**What `--recalculate-all` does:**
1. Recalculates all sprint progress from tasks
2. Recalculates all track progress from sprints
3. Recalculates roadmap progress from tracks
4. Refreshes all dependency caches
5. Optionally verifies consistency

**When to use:**
- After manual YAML file edits
- After data migrations or schema changes
- When debugging progress inconsistencies
- After recovering from interrupted operations
- When aggregate fields don't match actual data

#### Issue: Dependency caches are stale

**Cause:** Blocker status changed but `depends_on.current_status` not updated

**Solution:**
```bash
# Refresh all dependency caches
python3 framework/scripts/roadmap-update.py --recalculate-all
```

This updates `current_status` fields in all `depends_on` lists across tracks, sprints, and tasks.

---

## Next Steps

- **CLI Reference:** See [ROADMAP_CLI_REFERENCE.md](./ROADMAP_CLI_REFERENCE.md) for all commands
- **Tutorial:** Follow [ROADMAP_TUTORIAL.md](./ROADMAP_TUTORIAL.md) for hands-on example
- **Design Docs:** Read [framework/roadmap/DESIGN_DECISIONS.md](../../framework/roadmap/DESIGN_DECISIONS.md) for architecture details

---

**Version:** 2.1 (Gate Model)
**Status:** Production Ready
**Last Updated:** 2025-11-09
