# Platform-Agnostic Architecture Design

**Version:** 1.0
**Status:** Proposed
**Last Updated:** 2025-11-07
**Sprint:** Core Framework Track, Sprint 2

---

## Executive Summary

This document defines Vibey's platform-agnostic architecture where `.vibey/` serves as a permanent, platform-independent source of truth, and platform-specific directories (`.claude/`, `.goose/`, `.cursor/`) are treated as generated deployment artifacts.

**Key Insight:** Keep `.vibey/` permanent, make platform deployments disposable.

---

## Problem Statement

### Current Architecture Issues

**1. Platform Coupling**
- Framework deployed to `.claude/` (Claude Code specific)
- `.vibey/` now persists (as of v2.0) but was historically temporary
- Roadmap system integration complete (Sprint 2, roadmap-integration track)
- Goose and Cursor ports still need architecture work

**2. State Management Resolution** ✅ RESOLVED
- Roadmap state lives in `.vibey/` (persistent)
- `.vibey/` committed to git (never deleted)
- Multi-platform state location now clear: `.vibey/roadmap.yaml`

**3. Docs vs Configs Tension**
- Original vision: "Docs-driven" (move away from configs)
- Reality: Roadmap system proves YAML configs work great
- Need to resolve this contradiction

---

## Proposed Solution

### Three-Layer Architecture

```
┌──────────────────────────────────────────────────────────┐
│ Layer 1: SOURCE OF TRUTH (.vibey/)                       │
│                                                           │
│ A. Configs (YAML)          B. Sprint Docs (Markdown)     │
│    - Platform settings        - What to build            │
│    - Quality gates            - Architecture decisions   │
│    - Project metadata         - Daily learnings          │
│                               - Iterated during dev      │
│                                                           │
│ C. Roadmap State (YAML)                                  │
│    - Sprint status            Links to →  Sprint docs    │
│    - Dependencies                                        │
│    - Progress tracking                                   │
│                                                           │
│ All committed to git                                     │
└──────────────────────────────────────────────────────────┘
                    ↓
        ┌───────────┴────────────┐
        ↓                        ↓
┌────────────────────┐   ┌─────────────────────┐
│ Layer 2: DEPLOY    │   │ Layer 3: DOCS       │
│ - .claude/         │   │ - PROJECT_CONTEXT   │
│ - .goose/          │   │ Generated from      │
│ - .cursor/         │   │ .vibey/config +     │
│ Generated from     │   │ links to sprint_docs│
│ .vibey/config      │   │                     │
│ Gitignored         │   │ Optional commit     │
└────────────────────┘   └─────────────────────┘
```

### Key Principle: Non-Overlapping Purposes

**YAML (Roadmap System):**
- Tracks *state* of development (status, progress, dependencies)
- Machine-readable for CLI tools
- Lightweight, deterministic

**Markdown (Sprint Docs):**
- Provides *context* for AI and humans (what, why, how)
- Iterated during development (accumulates knowledge)
- Never regenerated - only enhanced

**They Reference Each Other:**
```yaml
# .vibey/roadmap/sprints/backend-1.yaml
documentation:
  base_path: "sprint_docs/backend-1"
  files:
    plan: "plan.md"        # ← Links to markdown
```

---

## Directory Structure

### Complete Project Layout

```
my-project/
│
├── .vibey/                           # 🏠 VIBEY HOME (permanent)
│   │
│   ├── config/                       # A. Platform configs (YAML)
│   │   ├── project.yaml              # Project metadata
│   │   ├── framework.yaml            # Framework behavior settings
│   │   ├── agents.yaml               # Agent preferences
│   │   └── quality-gates.yaml        # Quality standards
│   │
│   ├── roadmap/                      # C. Roadmap state (YAML)
│   │   ├── roadmap.yaml              # Links to sprint_docs/
│   │   ├── tracks/
│   │   │   └── backend.yaml          # Links to sprint_docs/
│   │   ├── sprints/
│   │   │   └── backend-1.yaml        # Links to sprint_docs/backend-1/
│   │   ├── tasks/
│   │   │   └── backend-1-tasks.yaml
│   │   └── activity/
│   │       └── 2025-11-07.log
│   │
│   ├── sprint_docs/                  # B. Sprint context (Markdown)
│   │   └── backend-1/                # Per-sprint documentation
│   │       ├── plan.md               # What to build, why
│   │       ├── architecture.md       # Design decisions
│   │       ├── progress.md           # Daily learnings (iterated)
│   │       └── lessons.md            # Post-sprint retrospective
│   │
│   ├── templates/                    # Custom templates (optional)
│   │   ├── agent-template.md
│   │   └── workflow-template.md
│   │
│   └── .vibey-version                # Vibey framework version
│
├── .claude/                          # 🎯 CLAUDE CODE (generated)
│   ├── agents/
│   │   ├── core/
│   │   ├── planning/
│   │   └── development/
│   ├── workflows/
│   ├── templates/
│   ├── commands/
│   └── CLAUDE.md                     # Generated from .vibey/config
│
├── .goose/                           # 🦆 GOOSE (generated)
│   ├── extensions/
│   │   ├── web_developer.py
│   │   └── test_engineer.py
│   ├── recipes/
│   │   ├── sprint_planning.yaml
│   │   └── feature_development.yaml
│   ├── toolkits/
│   └── instructions.md               # Generated from .vibey/config
│
├── .cursor/                          # 🔧 CURSOR (generated, future)
│   ├── rules/
│   └── .cursorrules                  # Generated from .vibey/config
│
├── docs/                             # 📚 DOCUMENTATION (generated)
│   ├── PROJECT_CONTEXT.md            # From .vibey/config/project.yaml
│   ├── ARCHITECTURE.md               # From .vibey/config/project.yaml
│   ├── QUALITY_GATES.md              # From .vibey/config/quality-gates.yaml
│   └── sprints/                      # From .vibey/roadmap/
│       ├── sprint-001-plan.md
│       └── sprint-002-plan.md
│
├── .gitignore                        # Platform dirs gitignored
├── src/                              # Your source code
└── README.md
```

---

## The YAML ↔ Markdown Relationship

### Sprint YAML: State & Links

```yaml
# .vibey/roadmap/sprints/backend-1.yaml
sprint:
  # Identity
  id: "backend-1"
  name: "Authentication & User Management"
  track_id: "backend"
  roadmap_id: "my-project"

  # STATE (what roadmap CLI manages)
  status: "in_progress"
  started: "2025-11-07T10:00:00Z"
  completed: null
  estimated_duration: "2 weeks"

  # Progress tracking (updated by roadmap CLI)
  progress:
    tasks_total: 8
    tasks_completed: 3
    completion_percent: 37

  # Relationships (for dependency management)
  dependencies:
    - type: "sprint"
      target_id: "backend-0"
      at_status: "completed"

  blocks:
    - type: "sprint"
      target_id: "backend-2"

  # Quality gates (metadata only)
  quality_gates:
    - name: "Unit Tests"
      threshold: 90
      blocking: true
      status: "not_run"

  # LINK to documentation (not the content itself!)
  documentation:
    base_path: "sprint_docs/backend-1"
    files:
      plan: "plan.md"              # What to build
      architecture: "architecture.md"  # Design decisions
      progress: "progress.md"      # Daily learnings
      lessons: "lessons.md"        # Retrospective
```

### Sprint Markdown: Context & Knowledge

```markdown
# .vibey/sprint_docs/backend-1/plan.md

# Sprint Plan: Authentication & User Management

<!-- ITERATED during sprint, never regenerated -->

## Status
🔵 In Progress (Day 5 of 14)

## Goals
1. Build secure authentication system
2. Implement user registration
3. JWT token generation with rotation

## Features

### 1. User Registration
**What:** POST /api/users endpoint
**Why:** Need users before authentication
**How:**
- Accept email, password
- Validate email format
- Hash password with bcrypt
- Return user object

**Updated Day 2:** Also added email uniqueness check after
discovering duplicate registration bug.

### 2. Login with JWT
**What:** POST /api/auth/login endpoint
...

**Updated Day 4:** Changed to refresh token rotation based on
security review findings. See architecture.md for details.
```

```markdown
# .vibey/sprint_docs/backend-1/progress.md

# Daily Progress & Learnings

<!-- Updated each day with discoveries -->

## Day 1 (2025-11-07)
✅ Task 1: Design database schema
✅ Task 2: Implement user registration

**Issue discovered:** Forgot email validation initially
**Solution:** Added server-side validation
**Learning:** Always validate server-side even if frontend validates

## Day 2 (2025-11-08)
🔵 Task 3: Implement login endpoint

**Issue:** FastAPI Depends() causing circular import
**Solution:** Created separate auth.py module
**Learning:** Structure FastAPI imports carefully

## Day 3 (2025-11-09)
...
```

---

## Configuration Files

### .vibey/config/project.yaml

```yaml
project:
  id: "my-project"
  name: "My Awesome Project"
  type: "web-app"  # web-app, api, ml, data-platform, infrastructure
  description: "Short description"

technology_stack:
  backend:
    language: "python"
    framework: "fastapi"
    version: "0.104.0"
  frontend:
    language: "typescript"
    framework: "react"
    version: "18.2.0"
  database:
    primary: "postgresql"
    cache: "redis"

infrastructure:
  hosting: "aws"
  container_platform: "kubernetes"
  ci_cd: "github-actions"

team:
  size: "small"  # solo, small, medium, large
  timezone: "America/New_York"
```

### .vibey/config/framework.yaml

```yaml
framework:
  version: "1.2.0"

  orchestration:
    mode: "balanced"  # simple, balanced, tiered
    auto_agent_launch: true
    coordinator_threshold: 3  # Launch coordinator for 3+ agents

  quality_gates:
    enabled: true
    enforcement: "blocking"  # blocking, warning, advisory

  features:
    roadmap_system: true
    sprint_tracking: true
    agent_routing: true

  preferences:
    default_sprint_duration: "2 weeks"
    task_granularity: "4-6 hours"
```

### .vibey/config/agents.yaml

```yaml
agents:
  enabled:
    - web-developer
    - test-engineer
    - docs-writer
    - security-auditor

  disabled:
    - ml-engineer  # Not needed for this project
    - performance-engineer

  custom:
    - name: "database-specialist"
      based_on: "web-developer"
      specialties:
        - "postgresql"
        - "migrations"
        - "query optimization"
      trigger_keywords:
        - "database"
        - "migration"
        - "query"
        - "schema"
```

### .vibey/config/quality-gates.yaml

```yaml
quality_gates:
  test_coverage:
    enabled: true
    threshold: 90
    blocking: true
    tools:
      - "pytest-cov"

  security_audit:
    enabled: true
    threshold: 85
    blocking: true
    tools:
      - "bandit"
      - "safety"

  logging_audit:
    enabled: true
    threshold: 80
    blocking: true
    checks:
      - correlation_ids
      - error_context
      - log_levels

  documentation:
    enabled: true
    threshold: 95
    blocking: true
    checks:
      - api_documentation
      - code_comments
      - readme_current
```

---

## Adapter Pattern

### Deployment Flow

```
1. User runs: vibey deploy --platform claude

2. Vibey reads: .vibey/config/*.yaml

3. Adapter transforms:
   - project.yaml → CLAUDE.md
   - agents.yaml → .claude/agents/*.md
   - workflows.yaml → .claude/workflows/*.md
   - quality-gates.yaml → .claude/config/gates.yaml

4. Generates: .claude/ directory (complete deployment)

5. Platform ready: Claude Code can use .claude/
```

### Multi-Platform Deployment

```bash
# Deploy to Claude Code
vibey deploy --platform claude

# Deploy to Goose
vibey deploy --platform goose

# Deploy to both
vibey deploy --platform all

# List available platforms
vibey platforms
```

---

## Documentation Generation

### Two Types of Documentation

#### 1. Generated Docs (From Configs)
**Purpose:** High-level project overview for AI
**Source:** `.vibey/config/*.yaml`
**Regenerated:** Yes, anytime configs change
**Location:** `docs/PROJECT_CONTEXT.md`, etc.

```bash
vibey docs generate

# Generates:
# - docs/PROJECT_CONTEXT.md (from config/project.yaml)
# - docs/QUALITY_GATES.md (from config/quality-gates.yaml)
# - Includes LINKS to sprint_docs/ (not content)
```

**docs/PROJECT_CONTEXT.md:**
```markdown
# Project Context: My Awesome Project

<!-- AUTO-GENERATED from .vibey/config/project.yaml -->

## Overview
REST API for task management

## Technology Stack
- Backend: Python (FastAPI 0.104.0)
- Frontend: TypeScript (React 18.2.0)
- Database: PostgreSQL + Redis

## Quality Standards
- Test Coverage: ≥90%
- Security Score: ≥85%
- Logging Audit: ≥80%

<!-- END AUTO-GENERATED -->

## Sprint Documentation

For detailed context, architecture decisions, and learnings,
see sprint-specific documentation:

- [Sprint: Authentication](../.vibey/sprint_docs/backend-1/plan.md)
- [Sprint: Core Logic](../.vibey/sprint_docs/backend-2/plan.md)

<!-- These links point to .vibey/sprint_docs/ which contain
     the rich, iterated context that accumulates over time -->
```

#### 2. Sprint Docs (Rich Context)
**Purpose:** Detailed context for AI and developers
**Source:** `.vibey/sprint_docs/`
**Regenerated:** NEVER - iterated during development
**Location:** `.vibey/sprint_docs/sprint-name/`

```bash
# Sprint docs are created and iterated manually or by AI
# They accumulate knowledge over time

# User/Claude edits:
vim .vibey/sprint_docs/backend-1/progress.md
# Adds: "Day 5: Discovered performance issue with N+1 queries"

# This context is NEVER lost - it persists and accumulates
```

---

## Git Strategy

### .gitignore

```gitignore
# Platform deployments (generated, don't commit)
.claude/
.goose/
.cursor/

# Generated docs (optional - could commit for team visibility)
docs/PROJECT_CONTEXT.md
docs/QUALITY_GATES.md

# Keep ALL source of truth in .vibey/
!.vibey/
```

### What to Commit

✅ **MUST Commit:**
- `.vibey/config/` - Platform settings, quality gates
- `.vibey/roadmap/` - Sprint state (status, dependencies, progress)
- **`.vibey/sprint_docs/`** - Sprint context (CRITICAL - accumulated knowledge!)
- `.vibey/templates/` - Custom templates

✅ **Optional Commit:**
- `docs/PROJECT_CONTEXT.md` - Generated overview (for team visibility)

❌ **NEVER Commit:**
- `.claude/` - Generated platform deployment
- `.goose/` - Generated platform deployment
- `.cursor/` - Generated platform deployment

**Critical:** `.vibey/sprint_docs/` contains accumulated context that is NEVER regenerated.
This must be committed to preserve learnings across sprints.

---

## CLI Commands

### New Commands

```bash
# Platform deployment
vibey deploy --platform <name>
vibey deploy --platform all
vibey platforms

# Documentation generation
vibey docs generate
vibey docs validate

# Config management
vibey config show
vibey config validate
vibey config migrate  # Migrate old format to new

# Platform switching
vibey use claude  # Set active platform
vibey use goose
vibey active      # Show current platform
```

---

## Migration Path

### From Current Architecture

**Current:**
```
1. Clone to .vibey/
2. Run /vibey command
3. Deploy to .claude/
4. Delete .vibey/
```

**New:**
```
1. Clone to .vibey-source/
2. Run vibey init
3. Create .vibey/ (permanent)
4. Deploy to .claude/ (generated)
5. Keep both .vibey/ and .claude/
```

### Migration Script

```bash
# For existing Vibey projects
vibey migrate --from-legacy

# What it does:
# 1. Extract configs from .claude/ → .vibey/config/
# 2. Keep .claude/ as-is (for now)
# 3. Add .vibey/ to git
# 4. Update .gitignore
# 5. Generate docs/
```

---

## Sprint Workflow: How YAML & Markdown Work Together

### Planning Phase

```bash
# 1. Create sprint state (YAML)
roadmap start backend-1
# Creates: .vibey/roadmap/sprints/backend-1.yaml

# 2. Create sprint documentation (Markdown)
mkdir -p .vibey/sprint_docs/backend-1
vim .vibey/sprint_docs/backend-1/plan.md

# User/Claude writes:
# - What features to build
# - Why they're needed
# - Architecture approach
# - Success criteria

# 3. YAML automatically links to documentation
# backend-1.yaml:
#   documentation:
#     base_path: "sprint_docs/backend-1"
```

### Development Phase

```bash
# Each day during development
# YAML updated by roadmap CLI:
roadmap start backend-1-task-003
roadmap complete backend-1-task-003
# → Updates status, progress in YAML

# Markdown iterated by user/Claude:
vim .vibey/sprint_docs/backend-1/progress.md
# Adds:
# ## Day 3
# Issue: FastAPI circular import
# Solution: Separate auth.py module
# Learning: Structure imports carefully
```

### How Claude Uses This

```
1. Claude reads: .vibey/roadmap/sprints/backend-1.yaml
   - Sees: status = "in_progress"
   - Sees: 3/8 tasks completed
   - Sees: documentation.files.plan = "plan.md"

2. Claude reads: .vibey/sprint_docs/backend-1/plan.md
   - Understands: What features to build
   - Understands: Why decisions were made
   - Understands: Architecture approach

3. Claude reads: .vibey/sprint_docs/backend-1/progress.md
   - Sees: Day 3 circular import issue
   - Learns: Don't make same mistake
   - Applies: Use separate auth.py module

4. Claude implements task, learns something new
   - Updates: progress.md with new learning
   - Learning: Persists for future sprints
```

### Retrospective Phase

```bash
# End of sprint
vim .vibey/sprint_docs/backend-1/lessons.md

# Capture:
# - What went well
# - What didn't go well
# - Key learnings
# - Recommendations for next sprint

# Complete sprint
roadmap complete backend-1
# → Updates YAML status to "completed"

# The markdown docs persist!
# Future sprints can reference:
# .vibey/sprint_docs/backend-1/lessons.md
```

---

## Context Explosion Mitigation

### The Problem

**Dependencies create exponential context growth.**

When a task has dependencies, the model needs context from:
1. **Current sprint docs** (4 files: plan, architecture, progress, lessons)
2. **Dependency sprint docs** (potentially 12+ files)
3. **Transitive dependencies** (grows exponentially)

**Example:**
```
Task: backend-5-task-007 (Implement payment processing)
  → Depends on: backend-4-task-012 (User authentication)
    → Depends on: backend-3-task-003 (Database schema)
      → Depends on: backend-2-task-001 (Infrastructure setup)

To build payment processing, model needs context from:
- Sprint 5 docs (4 files)
- Sprint 4 docs (4 files)
- Sprint 3 docs (4 files)
- Sprint 2 docs (4 files)

Total: 16 markdown files to read!

With 10 dependencies: 40+ files
With transitive dependencies: 100+ files (exponential explosion)
```

**This is unsustainable for model context windows.**

---

### The Solution: Hybrid Context Loading

**Combine multiple strategies:**
1. **Dependency summaries** - Auto-generated concise overviews in sprint YAML
2. **Task-level summaries** - Granular context at task level
3. **Context loading modes** - Configurable detail levels
4. **Hierarchical context layers** - More detail for closer dependencies
5. **Preparation mode** - User-triggered deep analysis for complex tasks

---

### YAML Schema Additions

#### Sprint-Level Dependency Summary

```yaml
# .vibey/roadmap/sprints/backend-4.yaml
sprint:
  id: "backend-4"
  name: "User Authentication & Authorization"

  # ... existing fields ...

  # NEW: Auto-generated summary for dependencies
  dependency_summary: |
    This sprint implemented secure user authentication with JWT tokens.

    Key Outputs:
    - POST /api/auth/login endpoint (returns JWT + refresh token)
    - POST /api/auth/refresh endpoint (token rotation)
    - Authentication middleware (validateToken function)
    - User model with email/password (bcrypt hashing)

    Key Interfaces:
    - JWT payload: { user_id, email, role, exp }
    - validateToken(token) → User object or throws AuthError

    Critical Learnings:
    - Use refresh token rotation (security requirement)
    - Avoid circular imports (separate auth.py module)
    - Server-side validation always required

    For dependencies: Use validateToken middleware on protected routes.
    See full context: .vibey/sprint_docs/backend-4/

  # NEW: Task-level summaries for granular context
  task_summaries:
    backend-4-task-012:
      summary: "Implemented JWT authentication with refresh token rotation"
      outputs:
        - "POST /api/auth/login endpoint"
        - "validateToken(token) middleware function"
        - "JWT payload structure: { user_id, email, role, exp }"
      interfaces:
        - function: "validateToken"
          signature: "validateToken(token: str) -> User"
          raises: "AuthError (401) if invalid/expired"
      gotchas:
        - "Tokens expire after 15 minutes (use refresh endpoint)"
        - "validateToken requires database access (async function)"
        - "Don't call from auth.py (circular import)"
      full_context: "sprint_docs/backend-4/progress.md#day-8"
```

#### Task-Level Context Mode

```yaml
# .vibey/tasks/backend-5-tasks.yaml
- id: "backend-5-task-007"
  name: "Implement payment processing"

  dependencies:
    - type: "task"
      target_id: "backend-4-task-012"
      at_status: "completed"

      # NEW: Control context loading depth
      context_mode: "summary"  # Options: minimal, summary, full

      reason: "Need authentication to protect payment endpoints"
```

---

### Context Loading Modes

#### 1. Minimal Mode
**When to use:** Weak dependencies, known interfaces
**What's loaded:**
```yaml
- Sprint ID, name, status
- Direct dependency outputs only
- No markdown files read
```

**Example:**
```
backend-5-task-007 depends on backend-4-task-012 (minimal)
  → Loads: task_summaries.backend-4-task-012.outputs
  → Total context: ~100 tokens
```

#### 2. Summary Mode (DEFAULT)
**When to use:** Most dependencies
**What's loaded:**
```yaml
- Sprint dependency_summary
- Task summary for specific dependency
- Key interfaces and gotchas
- No full markdown files
```

**Example:**
```
backend-5-task-007 depends on backend-4-task-012 (summary)
  → Loads: sprint.dependency_summary (500 tokens)
  → Loads: task_summaries.backend-4-task-012 (200 tokens)
  → Total context: ~700 tokens
```

#### 3. Full Mode
**When to use:** Complex dependencies, architectural decisions needed
**What's loaded:**
```yaml
- Sprint dependency_summary
- Task summary
- Full sprint docs (plan, architecture, progress, lessons)
```

**Example:**
```
backend-5-task-007 depends on backend-4-task-012 (full)
  → Loads: dependency_summary (500 tokens)
  → Loads: task_summary (200 tokens)
  → Loads: sprint_docs/backend-4/*.md (5,000 tokens)
  → Total context: ~5,700 tokens
```

---

### Hierarchical Context Layers

**Context detail decreases with dependency distance.**

```
Current Task: backend-5-task-007
  ↓
Direct Dependency: backend-4-task-012 (distance: 1)
  → Load: SUMMARY mode (700 tokens)
  ↓
Transitive Dependency: backend-3-task-003 (distance: 2)
  → Load: MINIMAL mode (100 tokens)
  ↓
Deep Dependency: backend-2-task-001 (distance: 3)
  → Load: MINIMAL mode (50 tokens) - outputs only
```

**Distance-based loading strategy:**
```python
def get_context_mode(distance: int) -> str:
    if distance == 1:
        return "summary"  # Direct dependencies
    elif distance == 2:
        return "minimal"  # One step removed
    else:
        return "none"     # Skip deep dependencies
```

**User override:**
```yaml
# User can force full context for critical dependencies
dependencies:
  - target_id: "backend-2-task-001"
    context_mode: "full"  # Override distance-based default
    reason: "Infrastructure setup critical for payment security"
```

---

### Auto-Generation Strategy

**dependency_summary generation:**
```bash
# When sprint completes
roadmap complete backend-4

# Automatically generates:
# 1. Reads all sprint docs (.vibey/sprint_docs/backend-4/*)
# 2. Extracts key sections (Goals, Key Features, Learnings)
# 3. Generates 500-word summary
# 4. Saves to sprint.dependency_summary field
# 5. Includes links to full docs

# Manual regeneration (if sprint docs updated):
roadmap summarize backend-4
```

**task_summaries generation:**
```bash
# When task completes
roadmap complete backend-4-task-012

# Automatically generates:
# 1. Extracts task details from sprint docs
# 2. Identifies outputs (functions, endpoints, models)
# 3. Captures gotchas from progress.md
# 4. Generates task summary
# 5. Saves to sprint.task_summaries

# Manual update:
roadmap summarize backend-4 --task backend-4-task-012
```

---

### Example: Context Loading in Action

#### Scenario
**Task:** `backend-5-task-007` - Implement payment processing
**Dependencies:**
1. `backend-4-task-012` - JWT authentication (direct)
2. `backend-3-task-008` - Database models (direct)
3. `backend-3-task-003` - Schema design (transitive via task-008)
4. `backend-2-task-001` - Infrastructure (transitive via task-003)

#### Context Loading Process

**Step 1: Load current sprint docs (FULL)**
```
.vibey/sprint_docs/backend-5/plan.md
.vibey/sprint_docs/backend-5/architecture.md
Total: ~3,000 tokens
```

**Step 2: Load direct dependencies (SUMMARY)**
```
backend-4-task-012 (distance: 1, summary mode):
  - dependency_summary: 500 tokens
  - task_summaries.backend-4-task-012: 200 tokens

backend-3-task-008 (distance: 1, summary mode):
  - dependency_summary: 500 tokens
  - task_summaries.backend-3-task-008: 200 tokens

Subtotal: 1,400 tokens
```

**Step 3: Load transitive dependencies (MINIMAL)**
```
backend-3-task-003 (distance: 2, minimal mode):
  - outputs only: 50 tokens

backend-2-task-001 (distance: 3, skip):
  - Not loaded (distance > 2)

Subtotal: 50 tokens
```

**Total Context Loaded:**
```
Current sprint:        3,000 tokens
Direct deps:           1,400 tokens
Transitive deps:          50 tokens
─────────────────────────────────
TOTAL:                 4,450 tokens

vs. Full Context Loading:
Current sprint:        3,000 tokens
All sprint docs:      20,000 tokens (4 sprints × 5,000 tokens)
─────────────────────────────────
TOTAL:                23,000 tokens (5x more!)

Savings: 82% reduction in context size
```

---

### Implementation Details

#### Updated Sprint YAML Template

```yaml
sprint:
  # ... existing fields ...

  # Context loading fields
  dependency_summary: null  # Generated on sprint completion
  task_summaries: {}        # Generated on task completion

  # Auto-generation settings
  summary_config:
    auto_generate: true
    include_sections:
      - "goals"
      - "key_features"
      - "learnings"
      - "interfaces"
    max_length: 500  # words
```

#### CLI Commands

```bash
# Generate summaries
roadmap summarize <sprint-id>
roadmap summarize <sprint-id> --task <task-id>

# Configure context loading
roadmap config set context.default_mode summary
roadmap config set context.max_distance 2

# View context for task
roadmap context <task-id>
roadmap context <task-id> --show-full
```

---

### Trade-offs

#### Benefits
✅ **Scalable** - Context grows linearly, not exponentially
✅ **Configurable** - Users control detail level
✅ **Auto-generated** - No manual summary writing
✅ **Hierarchical** - More detail for closer dependencies
✅ **Fast** - Reading summaries vs. full markdown files

#### Limitations
⚠️ **Summary quality** - Auto-generation may miss nuance
⚠️ **Overhead** - Summary generation adds time to completion
⚠️ **Storage** - Duplicates some info (summaries + full docs)

#### Mitigations
- Allow manual summary editing
- Make generation async (doesn't block completion)
- Summaries are much smaller than full docs (500 words vs 5,000)

---

### Preparation Mode: Deep Analysis for Complex Tasks

For complex tasks with large dependency graphs (5+ dependencies), users can trigger **preparation mode**:

```bash
roadmap prepare backend-5-task-007
```

**How it works:**
1. Model uses **full context window** to analyze ALL dependencies (no limits)
2. Generates task-specific preparation document with:
   - Dependency analysis (what each provides, integration patterns)
   - Critical integration points
   - Key learnings from dependency sprints
   - Potential issues to avoid
   - Implementation checklist
3. Saves to `.vibey/sprint_docs/<sprint>/prep/<task-id>.md`
4. User references prep doc during task execution

**Benefits:**
- Deep understanding before coding
- Proactive issue detection
- Integration patterns with code examples
- One focused document vs. 20+ dependency files

**When to use:**
- Complex integrations (payments, auth, multi-system)
- Critical tasks requiring deep understanding
- Unfamiliar domains
- High-risk implementations

**Cost:** 30-60 seconds, ~45K tokens for analysis
**Savings:** Hours during implementation, fewer bugs

See **CONTEXT_LOADING_STRATEGY.md** for detailed documentation.

---

### Best Practices

#### For Users

**1. Use summary mode by default**
```yaml
# Good - most dependencies don't need full context
dependencies:
  - target_id: "backend-4-task-012"
    context_mode: "summary"
```

**2. Use full mode sparingly**
```yaml
# Only for critical architectural dependencies
dependencies:
  - target_id: "backend-1-task-001"
    context_mode: "full"
    reason: "Core architecture - need full design context"
```

**3. Review auto-generated summaries**
```bash
# After sprint completion, review summary quality
roadmap show backend-4 --summary
vim .vibey/roadmap/sprints/backend-4.yaml  # Edit if needed
```

**4. Distance > 2? Rethink dependency**
```
If dependency distance > 2, ask:
- Is this really a direct dependency?
- Should there be an intermediate sprint?
- Can we reference outputs without dependency?
```

#### For Framework Developers

**1. Generate summaries on completion**
```python
def complete_sprint(sprint_id: str):
    # Update status
    sprint.status = "completed"

    # Generate summary
    sprint.dependency_summary = generate_summary(sprint_id)

    # Generate task summaries
    for task in sprint.tasks:
        sprint.task_summaries[task.id] = generate_task_summary(task)
```

**2. Implement lazy loading**
```python
def load_dependency_context(task: Task, max_distance: int = 2):
    for dep in task.dependencies:
        distance = calculate_distance(task, dep.target_id)
        mode = dep.context_mode or get_default_mode(distance)

        if mode == "summary":
            yield load_summary(dep.target_id)
        elif mode == "full":
            yield load_full_docs(dep.target_id)
        # minimal mode yields minimal data
```

**3. Cache summaries**
```python
# Don't regenerate summaries on every read
summary_cache = {}

def get_summary(sprint_id: str) -> str:
    if sprint_id not in summary_cache:
        summary_cache[sprint_id] = load_summary(sprint_id)
    return summary_cache[sprint_id]
```

---

### Success Metrics

#### Context Size Reduction
- Target: 80-90% reduction in context size for tasks with 5+ dependencies
- Measure: Track average context tokens per task before/after

#### Summary Quality
- Target: 90% of users don't need to edit auto-generated summaries
- Measure: Track manual summary edits

#### Performance
- Target: Summary generation < 2 seconds per sprint
- Target: Context loading < 500ms per task
- Measure: CLI performance metrics

---

## Benefits

### 1. Platform Agnostic
- `.vibey/` works with any platform
- Add Goose, Cursor without changing core
- Future platforms: just add adapter

### 2. Clean Separation
- Source of truth: `.vibey/`
- Deployments: `.claude/`, `.goose/`, etc.
- Documentation: `docs/`
- Each layer has clear purpose

### 3. Context Accumulation (CRITICAL)
- Sprint docs iterated, never regenerated
- Learnings persist across sprints
- "Day 1 mistakes" become "Sprint 5 wisdom"
- AI never loses context
- Knowledge compounds over time

### 4. Roadmap State Permanence
- `.vibey/` directory persists (never deleted as of v2.0)
- Survives platform changes and re-deployments
- Single source of truth for status/progress
- Committed to git for team collaboration

### 5. Clean Separation of Concerns
```
YAML:     "What's done? What's blocked? What's the status?"
Markdown: "What to build? Why? How? What did we learn?"

Non-overlapping, complementary purposes.
```

### 6. Developer Experience
- One command: `vibey deploy --platform <name>`
- Switch platforms easily
- Configs in one place
- Clear mental model
- Sprint docs accumulate naturally

---

## Implementation Plan

### Sprint 2: Config-to-Docs Architecture (3 weeks, 8 tasks)

**Week 1: Restructure**
- Task 1: Design `.vibey/config/` structure
- Task 2: Build config parser/validator
- Task 3: Update initialization to keep `.vibey/`

**Week 2: Generation**
- Task 4: Build doc generator (config → markdown)
- Task 5: Build Claude adapter (config → `.claude/`)
- Task 6: Add `vibey deploy` command
- Task 7: Add `vibey docs generate` command

**Week 3: Polish**
- Task 8: Migration guide for existing projects
- **Gate:** Backward compatibility tests
- **Gate:** Documentation review

---

## Future Enhancements

### Track 3: Goose Port
- Build Goose adapter
- `.vibey/config/` → `.goose/`
- Validate adapter pattern

### Track 4: Multi-Platform
- Extract platform-agnostic core
- Formalize adapter interface
- Unified CLI
- Cursor adapter

---

## Risks & Mitigations

### Risk: Breaking Changes
**Mitigation:**
- Backward compatibility mode
- Migration script for existing projects
- Gradual rollout

### Risk: Increased Complexity
**Mitigation:**
- Clear documentation
- Good defaults
- `vibey migrate` handles complexity

### Risk: Gitignore Mistakes
**Mitigation:**
- Template `.gitignore` with comments
- Warnings if platform dirs committed
- Clear documentation

---

## Success Metrics

✅ `.vibey/` survives across platform changes
✅ Can deploy to multiple platforms from same source
✅ Docs regenerate in <1 second
✅ 100% backward compatible
✅ Migration script success rate >95%
✅ User feedback: "clearer mental model"

---

## Key Takeaways

### 1. Two Complementary Systems

**YAML (Roadmap System):**
- Tracks state, progress, dependencies
- Updated by `roadmap` CLI
- Machine-readable
- Answers: "What's done? What's blocked?"

**Markdown (Sprint Docs):**
- Provides context for AI and humans
- Iterated during development
- Human-readable
- Answers: "What to build? Why? How? What did we learn?"

### 2. Context Never Lost

```
Sprint 1: "Don't use approach A for auth (security issue)"
   ↓ (written to sprint_docs/backend-1/lessons.md)
Sprint 2: Context persists, lesson remembered
   ↓
Sprint 5: Context still there, applied to new features
   ↓
Sprint 10: Full history of learnings available

Sprint docs are NEVER regenerated - they accumulate knowledge.
```

### 3. The Reference Relationship

```yaml
# .vibey/roadmap/sprints/backend-1.yaml
documentation:
  base_path: "sprint_docs/backend-1"
  files:
    plan: "plan.md"          # ← Links to markdown
    progress: "progress.md"  # ← Links to markdown
```

**The YAML points to the markdown.**
**The YAML doesn't contain the content.**

### 4. Platform Deployments are Artifacts

```
.vibey/config/ (source)
    ↓
vibey deploy --platform claude
    ↓
.claude/ (generated, gitignored)

Change platform:
    ↓
vibey deploy --platform goose
    ↓
.goose/ (generated, gitignored)

Same source (.vibey/), different output!
```

---

## Conclusion

This architecture resolves the docs-vs-configs tension by recognizing that:
- **YAML configs** track deterministic state (perfect for roadmap system)
- **Markdown docs** provide rich context (perfect for AI and humans)
- **Both** are needed, non-overlapping purposes
- **Context accumulates** in markdown (never regenerated)
- **State updates** in YAML (managed by CLI)

By keeping `.vibey/` permanent and treating platform directories as build artifacts, we create a clean foundation for multi-platform support while ensuring context is never lost across sprints.

---

## Success Criteria

✅ Sprint docs persist across sprints (context accumulates)
✅ Learnings from Sprint 1 available in Sprint 10
✅ YAML tracks state, Markdown provides context
✅ Platform deployments regeneratable from `.vibey/`
✅ Can switch platforms without losing any data
✅ Model has full context at all times
✅ Context loading scales to 100+ sprint projects (via context explosion mitigation)
✅ 80-90% reduction in context size for tasks with 5+ dependencies

---

## Related Documentation

- **YAML_MARKDOWN_SEPARATION.md** - Design principle for YAML vs Markdown
- **CONTEXT_LOADING_STRATEGY.md** - Detailed implementation of context explosion mitigation
- **ROADMAP_OBJECT_HIERARCHY.md** - Core roadmap system design
- **ROADMAP_IMPLEMENTATION_PLAN.md** - 6-sprint implementation plan

---

**Next Steps:**
1. ✅ Review and approve this design - APPROVED
2. Update roadmap YAML schema to include:
   - `documentation` field (links to sprint docs)
   - `dependency_summary` field (auto-generated summaries)
   - `task_summaries` field (task-level summaries)
   - `context_mode` in dependencies (minimal/summary/full)
3. Plan Sprint 2 tasks in detail:
   - Week 1: Restructure (keep .vibey/, update init)
   - Week 2: Generation (docs generator, adapters, deploy command)
   - Week 3: Context loading (implement CONTEXT_LOADING_STRATEGY.md)
   - Week 4: Polish (migration guide, testing)
4. Begin implementation
5. Test with migration of existing Vibey project

**Questions? Feedback?**
This is a significant architectural change. The context loading strategy is critical for scalability.
Review both this document and CONTEXT_LOADING_STRATEGY.md before implementation begins.
