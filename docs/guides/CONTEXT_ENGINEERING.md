# Context Engineering User Guide

**Version:** 1.0.0
**Last Updated:** 2025-12-19
**Status:** Production Ready
**Track:** Context System V2

---

## Table of Contents

1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Getting Started](#getting-started)
4. [Planning Phase](#planning-phase)
5. [Execution Phase](#execution-phase)
6. [Completion Phase](#completion-phase)
7. [Git Integration](#git-integration)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Reference](#reference)

---

## Introduction

### What is Context Engineering?

Context Engineering is the practice of **preserving and transferring knowledge** across AI assistant sessions and task boundaries. When working with AI coding assistants, context is often lost between conversations. This guide explains how to use Vibey's context system to:

- Maintain continuity across multiple AI sessions
- Capture decisions, discoveries, and lessons learned
- Link code changes to tasks through git commits
- Generate post-mortem summaries automatically

### Why Context Matters for AI-Assisted Development

AI coding assistants have limited context windows and no persistent memory. Without context engineering:

| Problem | Impact |
|---------|--------|
| Session ends mid-task | AI must re-analyze entire codebase |
| Decisions not recorded | Same decisions re-debated repeatedly |
| No handoff documentation | New sessions lack prior context |
| Completion knowledge lost | Future similar tasks start from scratch |

With context engineering:

| Solution | Benefit |
|----------|---------|
| Plan context preserved | AI starts with goals and approach |
| Runtime context tracked | Decisions and discoveries captured |
| Post-mortems generated | Lessons learned preserved |
| Commits linked to tasks | Full traceability maintained |

### The Three-Phase Context Model

Vibey's context system follows the natural lifecycle of work:

```
+-------------------------------------------------------------------------+
|                         CONTEXT LIFECYCLE                                 |
+-------------------------------------------------------------------------+

  PLANNING PHASE              EXECUTION PHASE              COMPLETION PHASE
  --------------              ---------------              ----------------

  +-------------------+     +-------------------+     +-------------------+
  |   PLAN CONTEXT    |     |  RUNTIME CONTEXT  |     |    POST-MORTEM    |
  |                   |     |                   |     |                   |
  |  * Goals          |     |  * Active files   |     |  * Summary        |
  |  * Approach       |     |  * Decisions made |     |  * Files changed  |
  |  * Artifact refs  | --> |  * Discoveries    | --> |  * Key decisions  |
  |  * Constraints    |     |  * Blockers       |     |  * Lessons learned|
  |  * Known files    |     |  * Token usage    |     |  * Follow-up items|
  |                   |     |                   |     |  * Commit links   |
  +-------------------+     +-------------------+     +-------------------+
          |                         |                         |
          |                         |                         |
          +-------------------------+-------------------------+
                                    |
                                    v
                        +------------------------+
                        |      GIT COMMITS       |
                        |                        |
                        |  Task: <TASK_ID>       |
                        |  Completes: <TASK_ID>  |
                        +------------------------+
```

---

## Core Concepts

### Plan Context

Pre-work preparation created **before** starting a task.

**Purpose:** Enable AI to quickly understand work scope without re-analyzing the codebase.

**Contents:**
- **Goals** - What needs to be accomplished
- **Approach** - Strategy and implementation plan
- **Constraints** - Limitations and requirements
- **Known Files** - Files expected to be modified
- **Artifact References** - Links to design docs, analysis documents

**Example:**

```yaml
# .vibey/roadmap/context/plans/01TASK_AUTH/plan.yaml
plan_context:
  ticket_id: 01TASK_AUTH
  created_at: '2025-12-19T10:00:00Z'
  created_by: claude
  approved: true

  goals:
    - "Implement JWT authentication"
    - "Support token refresh flow"

  approach: |
    Use PyJWT library with middleware pattern.
    See DESIGN_ANALYSIS.md for evaluation of options.

  constraints:
    - "Must be backwards compatible"
    - "No breaking changes to existing endpoints"

  known_files:
    - path: src/auth.py
      source: plan_reference
      added: '2025-12-19T10:00:00Z'

  artifacts:
    - file: DESIGN_ANALYSIS.md
      purpose: "Comparison of auth libraries"
      tokens_estimate: 3500
```

### Runtime Context

Active session state maintained **during** work.

**Purpose:** Enable handoff between AI sessions or recovery from interruption.

**Contents:**
- **Active Files** - Files currently being modified
- **Decisions** - Choices made with rationale
- **Discoveries** - Insights and findings
- **Blockers** - Issues encountered
- **Token Usage** - Tracking token consumption

**Example:**

```yaml
# .vibey/roadmap/context/runtime/01TASK_AUTH.yaml
runtime_context:
  ticket_id: 01TASK_AUTH
  session_id: sess_abc123
  started_at: '2025-12-19T11:00:00Z'
  last_updated: '2025-12-19T14:30:00Z'

  active_files:
    - src/auth.py
    - src/jwt_handler.py
    - src/middleware.py

  decisions:
    - decision: "Chose PyJWT over python-jose"
      rationale: "Better maintained, simpler API"
      timestamp: '2025-12-19T12:15:00Z'

  discoveries:
    - "Existing rate limiter conflicts with auth middleware order"

  blockers:
    - "Need DB migration for user tokens table"

  token_usage: 45000
```

### Post-Mortem Context

Completion summary created **after** work finishes.

**Purpose:** Preserve institutional knowledge for future similar work.

**Contents:**
- **Summary** - What was accomplished
- **Files Changed** - List of modified files
- **Key Decisions** - Important choices with rationale
- **Lessons Learned** - Insights for future work
- **Follow-up Items** - Tasks identified for later
- **Commit Links** - Associated git commits

**Example:**

```yaml
# .vibey/roadmap/context/post-mortems/01TASK_AUTH.yaml
post_mortem:
  ticket_id: 01TASK_AUTH
  completed_at: '2025-12-19T16:00:00Z'
  duration_hours: 5.0

  summary: |
    Implemented JWT authentication with decorator pattern.
    All endpoints now require auth, tests passing.

  files_changed:
    - src/auth.py
    - src/jwt_handler.py
    - tests/test_auth.py

  key_decisions:
    - "PyJWT for token handling (simpler API)"
    - "Decorator pattern (granular control per endpoint)"

  lessons_learned:
    - "Middleware order matters - auth before rate limiting"
    - "Check for existing partial implementations first"

  follow_up_items:
    - "Add refresh token support"
    - "Document auth flow in API docs"
```

### The Triangle Model

The context system links three entities through relationship records:

```
                         +-------------+
                         |   Ticket    |
                         |   (Task)    |
                         +-------------+
                        /               \
                       /                 \
          TicketCommitLink          TicketArtifactAssociation
             (Task: marker)              (file tracking)
                     /                     \
                    /                       \
        +-------------+               +-------------+
        |  GitCommit  |---------------|  Artifact   |
        +-------------+               +-------------+
                    CommitArtifactChange
                     (what changed)
```

This enables powerful queries:
- "What commits touched this task?"
- "What files are associated with this task?"
- "What tasks were affected by this file change?"

---

## Getting Started

### Prerequisites

- Vibey installed and configured (`pip install vibey`)
- Git repository initialized
- Roadmap initialized (`vibey roadmap init`)

### Setting Up Commit Message Template

The commit message template helps you use `Task:` and `Completes:` markers correctly.

```bash
# Install the commit message template
vibey git setup-template
```

This creates a `.gitmessage` file and configures git to use it:

```
# <type>(<scope>): <subject>
#
# Task: <TASK_ID>
# Completes: <TASK_ID>  # Only if task is actually complete
#
# <body>
#
# -------------------------------------------------------------------------
# TASK MARKERS:
#   Task: <ULID>              - Associates commit with task (work was done)
#   Completes: <ULID>         - Claims task completion (triggers criteria check)
# -------------------------------------------------------------------------
```

### Understanding Task: and Completes: Markers

| Marker | Purpose | When to Use |
|--------|---------|-------------|
| `Task: <ID>` | Associates commit with task | Every commit related to a task |
| `Completes: <ID>` | Claims task completion | Only when task is fully done |

**Example Commit Messages:**

```bash
# Progress commit (task continues)
git commit -m "feat(auth): Add JWT validation

Task: 01TASK_AUTH

Implements token validation middleware."

# Completion commit (task done)
git commit -m "feat(auth): Add auth tests and documentation

Task: 01TASK_AUTH
Completes: 01TASK_AUTH

All acceptance criteria met. Tests passing."
```

### Viewing Context Status

```bash
# Show task with context information
vibey roadmap show <task-id>

# Load context for a specific task
vibey context show <task-id>

# List all context items
vibey context list
```

---

## Planning Phase

### Creating Plan Context Before Starting Work

Before beginning a task, create plan context to document your approach.

**Why?** Future AI sessions can start with your goals and strategy instead of re-analyzing everything.

### Defining Goals, Approach, and Constraints

When creating a task or starting work, define:

1. **Goals** - Clear, measurable objectives
2. **Approach** - Implementation strategy
3. **Constraints** - Limitations and requirements

```bash
# Start a task (initializes runtime context from plan)
vibey roadmap start <task-id>
```

### Referencing Artifacts (Design Docs, Analysis)

Instead of embedding large documents, reference them:

```yaml
# Good: Reference artifacts
artifacts:
  - file: DESIGN_ANALYSIS.md
    purpose: "Evaluation of 3 auth libraries with trade-offs"
    tokens_estimate: 4500

# Bad: Embed entire document in YAML
approach: |
  [3000 words of analysis...]
```

**Benefits:**
- YAML stays small and always loads fast
- AI sees what artifacts exist and their purpose
- AI chooses which to load based on current need
- Large analyses preserved without forced token cost

### Token Budget Considerations

Plan your context token budget:

| Context Type | Typical Size | Guidance |
|--------------|--------------|----------|
| Plan YAML | 200-500 tokens | Always loaded |
| Artifacts | 1000-5000 each | Load on demand |
| Runtime | 500-2000 tokens | Grows during work |

```yaml
# Token estimates help AI decide what to load
artifacts:
  - file: DESIGN_ANALYSIS.md
    purpose: "Deep dive on auth options"
    tokens_estimate: 4500  # AI may skip if not needed
  - file: API_SPEC.md
    purpose: "Endpoint specifications"
    tokens_estimate: 1200  # Small, likely to load
```

---

## Execution Phase

### Using Runtime Context to Track Progress

As you work, runtime context captures your progress.

```bash
# Start working on a task
vibey roadmap start <task-id>
```

This initializes runtime context:
- Copies `known_files` from plan to `active_files`
- Sets `started_at` timestamp
- Initializes empty `decisions`, `discoveries`, `blockers` lists

### Logging Decisions and Discoveries

During work, record important decisions:

```yaml
decisions:
  - decision: "Chose PyJWT over python-jose"
    rationale: "Better maintained, simpler API, smaller footprint"
    timestamp: '2025-12-19T12:15:00Z'

discoveries:
  - "Existing rate limiter middleware conflicts with auth order"
  - "User model already has token fields from previous implementation"
```

**Via MCP Tools (for AI assistants):**

```python
# AI can log decisions via MCP
associate_artifact(ticket_id="01TASK_AUTH", artifact_id="art_jwt_handler")
```

### Managing Blockers

When you encounter blockers, document them:

```yaml
blockers:
  - "Need DB migration for user tokens table"
  - "Waiting on API team for endpoint specs"
```

### Associating Files with Tasks

Track which files are part of a task:

```bash
# Associate a file with a task
vibey task add-artifact <task-id> <file-path>

# List artifacts for a task
vibey task artifacts <task-id>
```

---

## Completion Phase

### Using the Completes: Marker in Commits

When a task is fully complete, use the `Completes:` marker:

```bash
git commit -m "feat(auth): Complete auth implementation

Task: 01TASK_AUTH
Completes: 01TASK_AUTH

All acceptance criteria met:
- JWT validation working
- Token refresh implemented
- Tests passing (98% coverage)
- Documentation updated"
```

**Important:** The pre-commit hook validates that all completion criteria are met before allowing `Completes:` claims.

### Auto-Generated Post-Mortems

When you complete a task, Vibey can generate a post-mortem from runtime context:

```bash
# Complete task (generates post-mortem)
vibey roadmap complete <task-id>
```

The post-mortem includes:
- Files changed (from commit history)
- Key decisions (from runtime context)
- Duration (from start/complete timestamps)
- Commit links (from `Task:` and `Completes:` markers)

### Lessons Learned and Follow-ups

Review and enhance the auto-generated post-mortem:

```yaml
post_mortem:
  # Auto-generated
  summary: "Completed with 3 commits, 4 files changed"
  files_changed: [...]
  commit_count: 3

  # Add manually for future reference
  lessons_learned:
    - "Middleware order matters - auth must come before rate limiting"
    - "Always check for existing partial implementations"

  follow_up_items:
    - "Add refresh token support in next sprint"
    - "Document auth flow in developer docs"
```

---

## Git Integration

### Pre-Commit Hook Triangle Validation

The pre-commit hook validates consistency across three relationship edges:

```
+-------------------------------------------------------------------------+
|                      PRE-COMMIT HOOK PHASES                               |
+-------------------------------------------------------------------------+
|  PHASE 1: Collect Data                                                   |
|    - Parse commit message for Task: and Completes: markers               |
|    - Get staged files                                                     |
|    - Resolve files to artifact IDs                                        |
+-------------------------------------------------------------------------+
|  PHASE 2: Triangle Validation                                            |
|    - Check: Are staged files associated with referenced tasks?           |
|    - Prompt if files don't match task associations                       |
+-------------------------------------------------------------------------+
|  PHASE 3: Completion Verification                                        |
|    - For Completes: claims, verify all criteria are met                  |
|    - Block commit if criteria not satisfied                              |
+-------------------------------------------------------------------------+
|  PHASE 4: Persist Relationships                                          |
|    - Create TicketCommitLink records                                     |
|    - Create CommitArtifactChange records                                 |
+-------------------------------------------------------------------------+
```

### Installing Git Hooks

```bash
# Install the pre-commit hook
vibey git install-hooks

# Force reinstall (overwrites existing)
vibey git install-hooks --force
```

### Configuration

Configure hook behavior in `.vibey/config/git_hooks.yaml`:

```yaml
pre_commit:
  enabled: true

  artifact_consistency:
    mode: prompt  # off | warn | prompt | strict
    on_mismatch:
      staged_not_in_associations: prompt
      associations_not_in_staged: ignore
      no_task_ref: warn

  completion_verification:
    mode: strict  # off | warn | strict
    block_on_unmet_criteria: true
```

| Mode | Behavior |
|------|----------|
| `off` | Check skipped |
| `warn` | Show issues, commit proceeds |
| `prompt` | Show issues, ask for resolution |
| `strict` | Block commit until resolved |

### Linking Commits Manually

```bash
# Link a commit to a task manually
vibey task link-commit <task-id> <commit-sha>

# View commits for a task
vibey task commits <task-id>

# Add current HEAD commit to task
vibey roadmap add-commit <task-id> --auto
```

---

## Best Practices

### Keep Context Focused and Relevant

**Do:**
- Document decisions that future sessions need
- Record blockers and how they were resolved
- Note discoveries that changed your approach

**Don't:**
- Log every small edit
- Include debug output
- Embed entire file contents

### Reference Artifacts Instead of Embedding Content

```yaml
# Good: Reference with purpose
artifacts:
  - file: DESIGN_ANALYSIS.md
    purpose: "Evaluation of 3 approaches with trade-offs"
    tokens_estimate: 4500

# Bad: Embed content
approach: |
  After analyzing three approaches...
  [3000 words of inline analysis]
```

### Use Meaningful File Associations

Associate files that are **central** to the task:

```bash
# Good: Core implementation files
vibey task add-artifact 01TASK_AUTH src/auth.py
vibey task add-artifact 01TASK_AUTH src/jwt_handler.py

# Unnecessary: Auto-formatted files, lockfiles
# Don't add: package-lock.json, .gitignore changes
```

### Regular Context Checkpoints

During long tasks, periodically update runtime context:

```yaml
# After major decision
decisions:
  - decision: "Switch from middleware to decorator pattern"
    rationale: "Decorators give per-endpoint control"
    timestamp: '2025-12-19T14:00:00Z'

# After discovery
discoveries:
  - "Found existing token validation in legacy auth module"
```

### Write Useful Post-Mortems

Capture knowledge that helps future similar tasks:

```yaml
lessons_learned:
  # Good: Actionable insight
  - "Test auth middleware with mock tokens before integration testing"

  # Bad: Obvious statement
  - "Authentication is important"

follow_up_items:
  # Good: Specific next step
  - "Add token refresh endpoint (design in FOLLOW_UP_DESIGN.md)"

  # Bad: Vague
  - "Improve auth"
```

---

## Troubleshooting

### Common Issues and Solutions

#### "Task not found: 01TASK_XYZ"

**Cause:** Invalid task ID or task doesn't exist in roadmap.

**Solution:**
```bash
# List available tasks
vibey roadmap status

# Use correct ULID format
vibey roadmap show 01KCMJPG8YZKCRSXQDDY7KMW0P
```

#### "Cannot complete task: criteria not met"

**Cause:** `Completes:` marker used but task criteria not satisfied.

**Solution:**
```bash
# Check task criteria status
vibey roadmap show <task-id>

# Complete criteria before claiming completion
# Or use only Task: marker for progress commits
```

#### Pre-commit hook blocking commit

**Cause:** Staged files don't match task associations or completion criteria unmet.

**Solutions:**

1. **Add files to task associations:**
   ```bash
   vibey task add-artifact <task-id> <file-path>
   ```

2. **Change hook mode temporarily:**
   ```yaml
   # .vibey/config/git_hooks.yaml
   artifact_consistency:
     mode: warn  # Instead of strict
   ```

3. **Update commit message:**
   - Add missing `Task:` references
   - Remove `Completes:` if not actually complete

#### Context validation errors

**Cause:** YAML syntax error or missing required fields.

**Solution:**
```bash
# Validate YAML syntax
vibey roadmap db validate

# Rebuild database from YAML
vibey roadmap db rebuild
```

### Pre-Commit Hook Issues

#### Hook not running

```bash
# Check hook is installed
ls -la .git/hooks/pre-commit

# Reinstall hook
vibey git install-hooks --force
```

#### Hook too strict for workflow

```yaml
# .vibey/config/git_hooks.yaml
pre_commit:
  artifact_consistency:
    mode: warn  # Show issues but don't block

  completion_verification:
    mode: warn  # Warn instead of block
```

#### Bypassing hook temporarily

```bash
# Skip hooks for one commit (use sparingly)
git commit --no-verify -m "hotfix: Emergency fix"
```

---

## Reference

### CLI Commands Cheat Sheet

#### Context Commands

| Command | Description |
|---------|-------------|
| `vibey context init` | Initialize context directory |
| `vibey context list` | List context items |
| `vibey context show <id>` | Show context details |
| `vibey context search <query>` | Search context by content |
| `vibey context archive <id>` | Archive context to history |
| `vibey context export <id>` | Export context to file |

#### Task Context Commands

| Command | Description |
|---------|-------------|
| `vibey roadmap start <task-id>` | Start task, init runtime context |
| `vibey roadmap complete <task-id>` | Complete task, generate post-mortem |
| `vibey task add-artifact <task-id> <path>` | Associate file with task |
| `vibey task artifacts <task-id>` | List task artifacts |
| `vibey task commits <task-id>` | List commits linked to task |
| `vibey task link-commit <task-id> <sha>` | Link commit to task |

#### Git Integration Commands

| Command | Description |
|---------|-------------|
| `vibey git setup-template` | Install commit message template |
| `vibey git install-hooks` | Install git hooks |
| `vibey git pre-commit` | Run pre-commit validation |

### MCP Tools Summary

| Tool | Purpose |
|------|---------|
| `associate_artifact` | Associate artifact with ticket |
| `get_ticket_artifacts` | Get all artifacts for ticket |
| `get_ticket_commits` | Get all commits for ticket |
| `get_artifact_history` | Get commit history for artifact |

### YAML Schema Quick Reference

#### Plan Context

```yaml
plan_context:
  ticket_id: string        # Required: ULID
  created_at: datetime     # Required: ISO 8601
  created_by: string       # Required: author
  approved: boolean        # Optional: default false

  goals: [string]          # Required: list of objectives
  approach: string         # Required: implementation strategy
  constraints: [string]    # Optional: limitations
  known_files:             # Optional: files to modify
    - path: string
      source: string       # plan_reference | runtime_tracking
      added: datetime

  artifacts:               # Optional: referenced documents
    - file: string         # filename
      purpose: string      # why it's relevant
      tokens_estimate: int # approximate token count
```

#### Runtime Context

```yaml
runtime_context:
  ticket_id: string        # Required: ULID
  session_id: string       # Optional: session identifier
  started_at: datetime     # Required: when work began
  last_updated: datetime   # Required: last modification

  active_files: [string]   # Files being modified
  decisions:               # Choices made during work
    - decision: string
      rationale: string
      timestamp: datetime
  discoveries: [string]    # Insights and findings
  blockers: [string]       # Issues encountered
  token_usage: int         # Token count tracking
```

#### Post-Mortem Context

```yaml
post_mortem:
  ticket_id: string        # Required: ULID
  completed_at: datetime   # Required: completion time
  duration_hours: float    # Calculated: work duration

  summary: string          # What was accomplished
  files_changed: [string]  # Modified files
  key_decisions: [string]  # Important choices
  lessons_learned: [string]# Insights for future
  follow_up_items: [string]# Tasks for later

  commit_links:            # Associated commits
    - sha: string
      message: string
      reference_type: string  # task_reference | completion_claim
```

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| [CONTEXT_ARCHITECTURE.md](../architecture/CONTEXT_ARCHITECTURE.md) | Technical architecture details |
| [GIT_INTEGRATION.md](GIT_INTEGRATION.md) | Full git integration guide |
| [GIT_COMMIT_TRACKING.md](GIT_COMMIT_TRACKING.md) | Commit tracking details |
| [ROADMAP_USER_GUIDE.md](ROADMAP_USER_GUIDE.md) | Roadmap system guide |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-19 | Initial context engineering guide |
