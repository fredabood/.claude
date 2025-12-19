# Context Output Formats

> Complete YAML schema reference for all context system output formats

**Version:** 1.0.0
**Status:** Active
**Task:** 01KCMJNWJYZFK331MSDEKJN7FJ
**Track:** Context System V2
**Sprint:** Sprint 2: Context Implementation

---

## Table of Contents

1. [Overview](#overview)
2. [Directory Structure](#directory-structure)
3. [Plan Context Format](#plan-context-format)
4. [Runtime Context Format](#runtime-context-format)
5. [Post-Mortem Context Format](#post-mortem-context-format)
6. [Git Hooks Configuration Format](#git-hooks-configuration-format)
7. [Context Index Format](#context-index-format)
8. [Context Configuration Format](#context-configuration-format)
9. [Relationship Entity Formats](#relationship-entity-formats)
10. [Validation Rules](#validation-rules)
11. [Versioning and Migration](#versioning-and-migration)

---

## Overview

### Purpose

The Context System maintains AI session context across three lifecycle phases:

| Phase | Purpose | Storage Location |
|-------|---------|------------------|
| **Plan** | Pre-work preparation and design | `context/plans/{ticket_id}/plan.yaml` |
| **Runtime** | Active session state during execution | `context/runtime/{ticket_id}.yaml` |
| **Post-Mortem** | Completion summary and lessons learned | `context/post-mortems/{ticket_id}.yaml` |

### Design Principles

1. **YAML as Source of Truth** - Human-readable, git-friendly, versioned
2. **Hybrid Storage** - YAML metadata indexes Markdown artifacts (loaded on demand)
3. **Token Efficiency** - AI sees what exists; loads only what's needed
4. **Triangle Integration** - Links tickets, commits, and artifacts

### Common Field Types

| Type | Format | Example |
|------|--------|---------|
| `ticket_id` | 26-character ULID | `01KCMJNWJYZFK331MSDEKJN7FJ` |
| `timestamp` | ISO 8601 with timezone | `2025-12-17T10:00:00+00:00` |
| `session_id` | Prefixed identifier | `sess_abc123` |
| `commit_sha` | Git SHA (7-40 chars) | `abc1234` or full 40-char |

---

## Directory Structure

```
.vibey/
├── context/
│   ├── config.yaml                    # Global context configuration
│   ├── index.yaml                     # Context system index
│   │
│   ├── plans/                         # Pre-work artifacts
│   │   └── {ticket_id}/
│   │       ├── plan.yaml              # Structured metadata + artifact index
│   │       ├── DESIGN_ANALYSIS.md     # Artifact: analysis document
│   │       ├── IMPLEMENTATION_PLAN.md # Artifact: step-by-step plan
│   │       └── API_DESIGN.md          # Artifact: specifications
│   │
│   ├── runtime/                       # Active session state
│   │   └── {ticket_id}.yaml           # Single file per active task
│   │
│   └── post-mortems/                  # Completion summaries
│       └── {ticket_id}.yaml           # Single file per completed task
│
└── config/
    └── git_hooks.yaml                 # Git hooks configuration
```

---

## Plan Context Format

**Location:** `context/plans/{ticket_id}/plan.yaml`

**Purpose:** Pre-work preparation created before starting a task. Enables AI to quickly understand work scope without re-analyzing the codebase.

### Full Schema

```yaml
# context/plans/{ticket_id}/plan.yaml
plan_context:
  # ─────────────────────────────────────────────────────────────
  # METADATA (Required)
  # ─────────────────────────────────────────────────────────────

  ticket_id: "01TASK123"              # ULID of the associated ticket
                                      # Format: 26-character ULID
                                      # Required: yes

  created_at: "2025-12-17T10:00:00Z"  # When plan was created
                                      # Format: ISO 8601 timestamp
                                      # Required: yes

  created_by: "claude"                # Who/what created the plan
                                      # Values: "claude" | "human" | "<username>"
                                      # Required: yes

  approved: false                     # Whether plan has been approved
                                      # Type: boolean
                                      # Required: yes
                                      # Default: false

  # ─────────────────────────────────────────────────────────────
  # PLANNING CONTENT (Required)
  # ─────────────────────────────────────────────────────────────

  goals:                              # List of objectives for this work
    - "Implement user authentication" # Clear, actionable goals
    - "Support JWT and session-based auth"
                                      # Type: list of strings
                                      # Required: yes (at least one)

  approach: |                         # High-level strategy for the work
    Use existing auth library, add middleware pattern.
    See DESIGN_ANALYSIS.md for detailed evaluation.
                                      # Type: string (multi-line supported)
                                      # Required: yes

  # ─────────────────────────────────────────────────────────────
  # CONSTRAINTS (Optional)
  # ─────────────────────────────────────────────────────────────

  constraints:                        # Limitations and requirements
    - "Must be backwards compatible"
    - "No breaking changes to existing endpoints"
    - "Must pass existing test suite"
                                      # Type: list of strings
                                      # Required: no
                                      # Default: []

  success_criteria:                   # How to determine if work is complete
    - "All endpoints require authentication"
    - "JWT tokens properly validated"
    - "Tests cover happy path and error cases"
                                      # Type: list of strings
                                      # Required: no
                                      # Default: []

  # ─────────────────────────────────────────────────────────────
  # FILE REFERENCES (Optional)
  # ─────────────────────────────────────────────────────────────

  known_files:                        # Files expected to be modified
    - path: "src/auth.py"             # Relative path from repo root
      source: "plan_reference"        # How file was identified
                                      # Values: plan_reference | runtime_tracking |
                                      #         commit_bootstrap | manual | criterion_target
      added: "2025-12-17T10:00:00Z"   # When file was added to plan

    - path: "src/middleware.py"
      source: "plan_reference"
      added: "2025-12-17T10:00:00Z"
                                      # Type: list of objects
                                      # Required: no
                                      # Default: []

  # ─────────────────────────────────────────────────────────────
  # ARTIFACT REFERENCES (Optional)
  # ─────────────────────────────────────────────────────────────

  artifacts:                          # Markdown artifacts (not loaded by default)
    - file: "DESIGN_ANALYSIS.md"      # Filename (in same directory as plan.yaml)
      purpose: "Deep dive on existing auth system, 3 options evaluated"
                                      # Brief description for AI to decide if needed
      tokens_estimate: 4500           # Estimated token count (for budget decisions)

    - file: "IMPLEMENTATION_PLAN.md"
      purpose: "Step-by-step implementation approach with code examples"
      tokens_estimate: 3200

    - file: "API_DESIGN.md"
      purpose: "Endpoint specifications and request/response formats"
      tokens_estimate: 2100
                                      # Type: list of objects
                                      # Required: no
                                      # Default: []
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticket_id` | string | Yes | 26-character ULID linking to task/ticket |
| `created_at` | timestamp | Yes | ISO 8601 creation timestamp |
| `created_by` | string | Yes | Creator identifier ("claude", "human", or username) |
| `approved` | boolean | Yes | Whether the plan has been reviewed and approved |
| `goals` | list[string] | Yes | Clear, actionable objectives (minimum 1) |
| `approach` | string | Yes | High-level strategy description |
| `constraints` | list[string] | No | Limitations and requirements |
| `success_criteria` | list[string] | No | Completion verification criteria |
| `known_files` | list[object] | No | Files expected to be modified |
| `known_files[].path` | string | Yes | Relative path from repository root |
| `known_files[].source` | string | Yes | How file was identified |
| `known_files[].added` | timestamp | Yes | When file was added to plan |
| `artifacts` | list[object] | No | Markdown artifacts for on-demand loading |
| `artifacts[].file` | string | Yes | Filename in plan directory |
| `artifacts[].purpose` | string | Yes | Brief description for AI decision-making |
| `artifacts[].tokens_estimate` | integer | Yes | Estimated token count |

### Example

```yaml
plan_context:
  ticket_id: "01KCMJNWJYZFK331MSDEKJN7FJ"
  created_at: "2025-12-19T10:00:00+00:00"
  created_by: "claude"
  approved: true

  goals:
    - "Document all context output formats"
    - "Provide complete YAML schemas with examples"
    - "Include validation rules and migration notes"

  approach: |
    Review existing context files and architecture documentation.
    Create comprehensive reference document with all formats.
    Include practical examples from actual system usage.

  constraints:
    - "Must align with existing CONTEXT_ARCHITECTURE.md"
    - "Examples must be valid YAML"

  success_criteria:
    - "All five context formats documented"
    - "Each format has full schema and example"
    - "Validation rules clearly specified"

  known_files:
    - path: "docs/architecture/CONTEXT_OUTPUT_FORMATS.md"
      source: "plan_reference"
      added: "2025-12-19T10:00:00+00:00"

  artifacts:
    - file: "FORMAT_ANALYSIS.md"
      purpose: "Analysis of existing context files and patterns"
      tokens_estimate: 2000
```

---

## Runtime Context Format

**Location:** `context/runtime/{ticket_id}.yaml`

**Purpose:** Active session state maintained during work execution. Enables handoff between AI sessions and recovery from interruption.

### Full Schema

```yaml
# context/runtime/{ticket_id}.yaml
runtime_context:
  # ─────────────────────────────────────────────────────────────
  # METADATA (Required)
  # ─────────────────────────────────────────────────────────────

  ticket_id: "01TASK123"              # ULID of the associated ticket
                                      # Format: 26-character ULID
                                      # Required: yes

  session_id: "sess_abc123"           # Current AI session identifier
                                      # Format: prefixed string
                                      # Required: yes

  started_at: "2025-12-17T11:00:00Z"  # When work began on this task
                                      # Format: ISO 8601 timestamp
                                      # Required: yes

  last_updated: "2025-12-17T14:30:00Z" # Most recent context update
                                       # Format: ISO 8601 timestamp
                                       # Required: yes

  # ─────────────────────────────────────────────────────────────
  # ACTIVE STATE (Required)
  # ─────────────────────────────────────────────────────────────

  active_files:                       # Files currently being worked on
    - "src/auth.py"                   # Relative paths from repo root
    - "src/jwt_handler.py"
    - "src/middleware.py"
    - "tests/test_auth.py"
                                      # Type: list of strings
                                      # Required: yes
                                      # Default: [] (empty on init)

  # ─────────────────────────────────────────────────────────────
  # DECISIONS LOG (Optional)
  # ─────────────────────────────────────────────────────────────

  decisions:                          # Decisions made during execution
    - decision: "Chose PyJWT over python-jose"
      rationale: "Better maintained, simpler API, more stars on GitHub"
      timestamp: "2025-12-17T12:15:00Z"

    - decision: "Use decorator pattern for auth"
      rationale: "Cleaner than middleware for granular per-endpoint control"
      timestamp: "2025-12-17T13:45:00Z"

    - decision: "Store tokens in httpOnly cookies"
      rationale: "More secure than localStorage, prevents XSS attacks"
      timestamp: "2025-12-17T14:20:00Z"
                                      # Type: list of objects
                                      # Required: no
                                      # Default: []

  # ─────────────────────────────────────────────────────────────
  # DISCOVERIES (Optional)
  # ─────────────────────────────────────────────────────────────

  discoveries:                        # Insights found during work
    - "Existing rate limiter conflicts with auth middleware order"
    - "User model already has token fields from previous implementation"
    - "Legacy endpoint /api/v1/login bypasses middleware chain"
                                      # Type: list of strings
                                      # Required: no
                                      # Default: []

  # ─────────────────────────────────────────────────────────────
  # BLOCKERS (Optional)
  # ─────────────────────────────────────────────────────────────

  blockers:                           # Issues preventing progress
    - "Need DB migration for user tokens table"
    - "Waiting for security team review of token expiry policy"
                                      # Type: list of strings
                                      # Required: no
                                      # Default: []

  # ─────────────────────────────────────────────────────────────
  # METRICS (Optional)
  # ─────────────────────────────────────────────────────────────

  token_usage: 45000                  # Approximate tokens consumed this session
                                      # Type: integer
                                      # Required: no
                                      # Default: 0
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticket_id` | string | Yes | 26-character ULID linking to task/ticket |
| `session_id` | string | Yes | Current AI session identifier |
| `started_at` | timestamp | Yes | When work began |
| `last_updated` | timestamp | Yes | Most recent update timestamp |
| `active_files` | list[string] | Yes | Files currently being modified |
| `decisions` | list[object] | No | Decisions made with rationale |
| `decisions[].decision` | string | Yes | What was decided |
| `decisions[].rationale` | string | Yes | Why this decision was made |
| `decisions[].timestamp` | timestamp | Yes | When decision was made |
| `discoveries` | list[string] | No | Insights found during work |
| `blockers` | list[string] | No | Issues preventing progress |
| `token_usage` | integer | No | Approximate tokens consumed |

### Example

```yaml
runtime_context:
  ticket_id: "01KCMJNWJYZFK331MSDEKJN7FJ"
  session_id: "sess_doc_formats_001"
  started_at: "2025-12-19T14:00:00+00:00"
  last_updated: "2025-12-19T15:30:00+00:00"

  active_files:
    - "docs/architecture/CONTEXT_OUTPUT_FORMATS.md"
    - "docs/architecture/CONTEXT_ARCHITECTURE.md"

  decisions:
    - decision: "Include relationship entity formats in documentation"
      rationale: "Provides complete reference for triangle model integration"
      timestamp: "2025-12-19T14:15:00+00:00"

    - decision: "Use inline field comments in schema examples"
      rationale: "Makes documentation self-explanatory without separate tables"
      timestamp: "2025-12-19T14:30:00+00:00"

  discoveries:
    - "Existing post-mortem uses 'artifacts_changed' instead of 'files_changed'"
    - "Context index file provides global stats tracking"

  blockers: []

  token_usage: 12000
```

---

## Post-Mortem Context Format

**Location:** `context/post-mortems/{ticket_id}.yaml`

**Purpose:** Completion summary created after work finishes. Preserves institutional knowledge for future similar work.

### Full Schema

```yaml
# context/post-mortems/{ticket_id}.yaml
post_mortem:
  # ─────────────────────────────────────────────────────────────
  # METADATA (Required)
  # ─────────────────────────────────────────────────────────────

  ticket_id: "01TASK123"              # ULID of the completed ticket
                                      # Format: 26-character ULID
                                      # Required: yes

  completed_at: "2025-12-17T16:00:00Z" # When work was completed
                                       # Format: ISO 8601 timestamp
                                       # Required: yes

  duration_hours: 5.0                 # Total hours spent on task
                                      # Type: float (nullable)
                                      # Required: no
                                      # Computed: (completed_at - started_at)

  # ─────────────────────────────────────────────────────────────
  # SUMMARY (Required)
  # ─────────────────────────────────────────────────────────────

  summary: |                          # Brief description of what was accomplished
    Implemented JWT authentication with decorator pattern.
    All endpoints now require auth, tests passing.
    Chose PyJWT for token handling after evaluating alternatives.
                                      # Type: string (multi-line supported)
                                      # Required: yes

  # ─────────────────────────────────────────────────────────────
  # ARTIFACTS (Optional)
  # ─────────────────────────────────────────────────────────────

  artifacts_changed:                  # Files that were modified
    - "src/auth.py"                   # Relative paths from repo root
    - "src/jwt_handler.py"
    - "src/middleware.py"
    - "tests/test_auth.py"
                                      # Type: list of strings
                                      # Required: no
                                      # Default: []
                                      # Note: Auto-populated from runtime context

  # ─────────────────────────────────────────────────────────────
  # KNOWLEDGE CAPTURE (Optional)
  # ─────────────────────────────────────────────────────────────

  key_decisions:                      # Important decisions from runtime context
    - "PyJWT for token handling (simpler API, better maintained)"
    - "Decorator pattern for auth (granular control per endpoint)"
    - "Middleware order: auth before rate limiting"
    - "httpOnly cookies for token storage (XSS protection)"
                                      # Type: list of strings
                                      # Required: no
                                      # Default: []

  lessons_learned:                    # Insights for future similar work
    - "Middleware order matters - auth must come before rate limiting"
    - "Check for existing partial implementations before starting"
    - "Legacy endpoints may bypass middleware - audit all routes"
    - "Token expiry needs security team sign-off"
                                      # Type: list of strings
                                      # Required: no
                                      # Default: []

  follow_up_items:                    # Tasks identified but not completed
    - "Add refresh token support"
    - "Document auth flow in API docs"
    - "Add rate limiting per authenticated user"
    - "Migrate legacy /api/v1/login endpoint"
                                      # Type: list of strings
                                      # Required: no
                                      # Default: []

  # ─────────────────────────────────────────────────────────────
  # COMMIT LINKS (Optional)
  # ─────────────────────────────────────────────────────────────

  commits:                            # Git commits associated with this task
    - sha: "abc1234"                  # Git commit SHA (short or full)
      message: "feat(auth): Add JWT validation"
                                      # Commit message (first line)
      reference_type: "TASK_REFERENCE"
                                      # Type: TASK_REFERENCE | COMPLETION_CLAIM
      linked_at: "2025-12-17T14:00:00Z"
                                      # When link was created

    - sha: "def5678"
      message: "feat(auth): Add auth decorator"
      reference_type: "COMPLETION_CLAIM"
      linked_at: "2025-12-17T16:00:00Z"
                                      # Type: list of objects
                                      # Required: no
                                      # Default: []
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticket_id` | string | Yes | 26-character ULID of completed ticket |
| `completed_at` | timestamp | Yes | Completion timestamp |
| `duration_hours` | float | No | Total hours spent (computed) |
| `summary` | string | Yes | Brief accomplishment description |
| `artifacts_changed` | list[string] | No | Files that were modified |
| `key_decisions` | list[string] | No | Important decisions made |
| `lessons_learned` | list[string] | No | Insights for future work |
| `follow_up_items` | list[string] | No | Tasks identified but not done |
| `commits` | list[object] | No | Associated git commits |
| `commits[].sha` | string | Yes | Git commit SHA |
| `commits[].message` | string | Yes | Commit message (first line) |
| `commits[].reference_type` | string | Yes | TASK_REFERENCE or COMPLETION_CLAIM |
| `commits[].linked_at` | timestamp | Yes | When link was created |

### Example

```yaml
post_mortem:
  ticket_id: "01KCMJNWJYZFK331MSDEKJN7FJ"
  completed_at: "2025-12-19T16:00:00+00:00"
  duration_hours: 2.0

  summary: |
    Created comprehensive documentation for all context output formats.
    Document includes five main format specifications with full schemas,
    field descriptions, examples, and validation rules.

  artifacts_changed:
    - "docs/architecture/CONTEXT_OUTPUT_FORMATS.md"

  key_decisions:
    - "Used inline comments in YAML schemas for self-documentation"
    - "Included relationship entities for complete triangle model reference"
    - "Organized by lifecycle phase (plan -> runtime -> post-mortem)"

  lessons_learned:
    - "Existing implementations may use slightly different field names"
    - "Cross-reference with CONTEXT_ARCHITECTURE.md for consistency"

  follow_up_items:
    - "Update CLI commands to generate context files matching these formats"
    - "Add format validation to context operations"

  commits:
    - sha: "abc1234"
      message: "docs: Add context output formats documentation"
      reference_type: "COMPLETION_CLAIM"
      linked_at: "2025-12-19T16:00:00+00:00"
```

---

## Git Hooks Configuration Format

**Location:** `.vibey/config/git_hooks.yaml`

**Purpose:** Configure the unified pre-commit hook with triangle validation for commit-ticket-artifact consistency.

### Full Schema

```yaml
# .vibey/config/git_hooks.yaml
pre_commit:
  # ─────────────────────────────────────────────────────────────
  # MASTER SWITCH
  # ─────────────────────────────────────────────────────────────

  enabled: true                       # Enable/disable pre-commit hook
                                      # Type: boolean
                                      # Required: yes

  # ─────────────────────────────────────────────────────────────
  # PHASE 2: ARTIFACT CONSISTENCY (Triangle Validation)
  # ─────────────────────────────────────────────────────────────

  artifact_consistency:
    mode: prompt                      # Overall mode for artifact checks
                                      # Values:
                                      #   off    - Check skipped entirely
                                      #   warn   - Show issues, commit proceeds
                                      #   prompt - Show issues, ask for resolution
                                      #   strict - Block commit until resolved
                                      # Required: yes

    on_mismatch:                      # Specific behaviors for different mismatches
      staged_not_in_associations: prompt
                                      # Files in commit but not in ticket associations
                                      # Values: ignore | warn | prompt | block
                                      # Action: Prompt to add files to associations

      associations_not_in_staged: ignore
                                      # Files in ticket associations but not in commit
                                      # Values: ignore | warn
                                      # Note: Normal - not all files change each time

      no_task_ref: warn               # Staged files not associated with ANY task
                                      # Values: ignore | warn | prompt | block
                                      # Suggests commit needs Task: references

  # ─────────────────────────────────────────────────────────────
  # PHASE 3: COMPLETION VERIFICATION
  # ─────────────────────────────────────────────────────────────

  completion_verification:
    mode: strict                      # Mode for Completes: claims verification
                                      # Values:
                                      #   off    - Skip verification (not recommended)
                                      #   warn   - Show warnings only
                                      #   strict - Block commit if criteria unmet
                                      # Required: yes

    block_on_unmet_criteria: true     # Block if Completes: claimed but criteria fail
                                      # Type: boolean
                                      # Required: yes

    show_criteria_progress: true      # Show progress for each unmet criterion
                                      # Type: boolean
                                      # Required: no
                                      # Default: true

  # ─────────────────────────────────────────────────────────────
  # COMMIT MESSAGE TEMPLATE
  # ─────────────────────────────────────────────────────────────

  template:
    auto_install: true                # Automatically install .gitmessage
                                      # Type: boolean
                                      # Required: no
                                      # Default: false

    path: .gitmessage                 # Path to template file
                                      # Type: string
                                      # Required: if auto_install is true

    configure_git: true               # Configure git to use template
                                      # Type: boolean
                                      # Required: no
                                      # Default: false

  # ─────────────────────────────────────────────────────────────
  # OUTPUT FORMATTING
  # ─────────────────────────────────────────────────────────────

  output:
    use_colors: true                  # Use colors in terminal output
                                      # Type: boolean
                                      # Default: true

    show_artifact_paths: true         # Show detailed paths in validation
                                      # Type: boolean
                                      # Default: true

    verbosity: normal                 # Output verbosity level
                                      # Values: quiet | normal | verbose
                                      # Default: normal
```

### Configuration Modes Reference

| Mode | Behavior | Use Case |
|------|----------|----------|
| `off` | Check skipped entirely | Disabled during migrations |
| `warn` | Show issues, commit proceeds | Informational only |
| `prompt` | Show issues, ask for resolution | Interactive development |
| `strict` | Block commit until resolved | Enforced consistency |

### Mismatch Actions Reference

| Action | Effect | Typical Use |
|--------|--------|-------------|
| `ignore` | Silently skip | Non-critical checks |
| `warn` | Display warning, continue | Advisory information |
| `prompt` | Ask user for resolution | Interactive decision |
| `block` | Prevent commit | Required consistency |

### Example

```yaml
pre_commit:
  enabled: true

  artifact_consistency:
    mode: prompt
    on_mismatch:
      staged_not_in_associations: prompt
      associations_not_in_staged: ignore
      no_task_ref: warn

  completion_verification:
    mode: strict
    block_on_unmet_criteria: true
    show_criteria_progress: true

  template:
    auto_install: true
    path: .gitmessage
    configure_git: true

  output:
    use_colors: true
    show_artifact_paths: true
    verbosity: normal
```

---

## Context Index Format

**Location:** `.vibey/context/index.yaml`

**Purpose:** Global index tracking context system state and statistics.

### Full Schema

```yaml
# .vibey/context/index.yaml
context:
  # ─────────────────────────────────────────────────────────────
  # VERSION INFO
  # ─────────────────────────────────────────────────────────────

  version: "1.0"                      # Context system version
                                      # Type: string
                                      # Required: yes

  created: "2025-12-14T16:19:12+00:00"
                                      # When context system was initialized
                                      # Format: ISO 8601 timestamp
                                      # Required: yes

  last_updated: "2025-12-14T16:19:12+00:00"
                                      # Most recent system update
                                      # Format: ISO 8601 timestamp
                                      # Required: yes

  # ─────────────────────────────────────────────────────────────
  # STATISTICS
  # ─────────────────────────────────────────────────────────────

  stats:
    sessions_active: 0                # Currently active sessions
                                      # Type: integer

    sessions_total: 0                 # Total sessions ever created
                                      # Type: integer

    tasks_active: 0                   # Tasks currently in progress
                                      # Type: integer

    tasks_total: 0                    # Total tasks with context
                                      # Type: integer

    decisions_total: 0                # Total decisions recorded
                                      # Type: integer

  # ─────────────────────────────────────────────────────────────
  # CURRENT STATE
  # ─────────────────────────────────────────────────────────────

  current:
    session_id: null                  # Active session ID (null if none)
                                      # Type: string | null

  # ─────────────────────────────────────────────────────────────
  # RECENT ACTIVITY
  # ─────────────────────────────────────────────────────────────

  recent_tasks: []                    # Recently accessed tasks
                                      # Type: list of ticket_id strings
                                      # Max: configurable (default 10)

  recent_decisions: []                # Recent decisions across all tasks
                                      # Type: list of objects
                                      # Max: configurable (default 20)
```

### Example

```yaml
context:
  version: "1.0"
  created: "2025-12-14T16:19:12+00:00"
  last_updated: "2025-12-19T15:30:00+00:00"

  stats:
    sessions_active: 1
    sessions_total: 15
    tasks_active: 2
    tasks_total: 47
    decisions_total: 123

  current:
    session_id: "sess_doc_formats_001"

  recent_tasks:
    - "01KCMJNWJYZFK331MSDEKJN7FJ"
    - "01KCMNEG4CXW4NK7W55VDMBXXM"

  recent_decisions:
    - ticket_id: "01KCMJNWJYZFK331MSDEKJN7FJ"
      decision: "Include relationship entities"
      timestamp: "2025-12-19T14:15:00+00:00"
```

---

## Context Configuration Format

**Location:** `.vibey/context/config.yaml`

**Purpose:** Global configuration for context system retention and cleanup policies.

### Full Schema

```yaml
# .vibey/context/config.yaml
context_config:
  # ─────────────────────────────────────────────────────────────
  # VERSION
  # ─────────────────────────────────────────────────────────────

  version: "1.0"                      # Configuration version
                                      # Type: string
                                      # Required: yes

  # ─────────────────────────────────────────────────────────────
  # RETENTION POLICIES
  # ─────────────────────────────────────────────────────────────

  retention:
    sessions:
      active_max: 1                   # Maximum concurrent active sessions
                                      # Type: integer
                                      # Default: 1

      history_days: 90                # Days to retain session history
                                      # Type: integer
                                      # Default: 90

      archive_format: yaml            # Format for archived sessions
                                      # Values: yaml | json
                                      # Default: yaml

    tasks:
      completed_days: 180             # Days to retain completed task context
                                      # Type: integer
                                      # Default: 180

      archive_monthly: true           # Archive old tasks by month
                                      # Type: boolean
                                      # Default: true

    decisions:
      keep_forever: true              # Never delete decision history
                                      # Type: boolean
                                      # Default: true

  # ─────────────────────────────────────────────────────────────
  # CLEANUP SETTINGS
  # ─────────────────────────────────────────────────────────────

  cleanup:
    enabled: true                     # Enable automatic cleanup
                                      # Type: boolean
                                      # Default: true

    schedule: weekly                  # Cleanup frequency
                                      # Values: daily | weekly | monthly | manual
                                      # Default: weekly

    dry_run_first: true               # Preview cleanup before executing
                                      # Type: boolean
                                      # Default: true
```

### Example

```yaml
context_config:
  version: "1.0"

  retention:
    sessions:
      active_max: 1
      history_days: 90
      archive_format: yaml
    tasks:
      completed_days: 180
      archive_monthly: true
    decisions:
      keep_forever: true

  cleanup:
    enabled: true
    schedule: weekly
    dry_run_first: true
```

---

## Relationship Entity Formats

These formats define the triangle model relationships between tickets, commits, and artifacts. While stored in the SQLite database for fast queries, they may also appear in YAML exports or API responses.

### TicketCommitLink

Links a ticket to a git commit.

```yaml
ticket_commit_link:
  ticket_id: "01TASK123"              # ULID of associated ticket
  commit_sha: "abc1234def5678"        # Git commit SHA
  reference_type: "TASK_REFERENCE"    # Type of reference
                                      # Values:
                                      #   TASK_REFERENCE - Work done on task
                                      #   COMPLETION_CLAIM - Task claimed complete

  signals:                            # Detection signals
    file_overlap:                     # Commit files match ticket associations
      matched: true
      overlapping_artifact_ids:
        - "artifact_001"
        - "artifact_002"
      confidence: 0.85                # len(overlap) / len(commit_artifacts)

    message_ref:                      # Commit message references task
      matched: true
      ticket_ids:
        - "01TASK123"
      reference_type: "TASK_REFERENCE"
      confidence: 1.0

    manual:                           # User explicitly linked
      matched: false
      linked_by: null
      linked_at: null
      confidence: 1.0

  aggregate_confidence: 0.925         # Combined signal confidence
  linked_at: "2025-12-17T14:00:00Z"   # When link was created
  link_source: "pre_commit_hook"      # How link was created
                                      # Values: pre_commit_hook | post_commit | manual
```

### TicketArtifactAssociation

Links a ticket to an artifact (file).

```yaml
ticket_artifact_association:
  ticket_id: "01TASK123"              # ULID of associated ticket
  artifact_id: "artifact_001"         # Artifact identifier
  artifact_path: "src/auth.py"        # File path

  association_source: "plan_reference"
                                      # How association was created
                                      # Values:
                                      #   plan_reference - Listed in plan context
                                      #   runtime_tracking - AI logged during work
                                      #   commit_bootstrap - First commit established
                                      #   manual - CLI command added
                                      #   criterion_target - Criterion references file

  added_at: "2025-12-17T10:00:00Z"    # When association was created
  added_by: "claude"                  # Who/what created association
```

### CommitArtifactChange

Links a commit to artifacts it changed.

```yaml
commit_artifact_change:
  commit_sha: "abc1234def5678"        # Git commit SHA
  artifact_id: "artifact_001"         # Artifact identifier
  artifact_path: "src/auth.py"        # File path

  change_type: "MODIFIED"             # Type of change
                                      # Values: ADDED | MODIFIED | DELETED | RENAMED

  previous_path: null                 # For RENAMED: original path
  lines_added: 45                     # Lines added (if available)
  lines_removed: 12                   # Lines removed (if available)
  recorded_at: "2025-12-17T14:00:00Z" # When change was recorded
```

---

## Validation Rules

### Common Rules (All Formats)

| Rule | Description |
|------|-------------|
| **Valid ULID** | `ticket_id` must be 26-character ULID |
| **ISO 8601 Timestamps** | All timestamps must be valid ISO 8601 |
| **Required Fields** | Fields marked required must be present |
| **Non-Empty Lists** | Lists with minimum requirements must not be empty |

### Plan Context Validation

| Rule | Validation |
|------|------------|
| `goals` minimum | At least one goal required |
| `approach` length | Must be non-empty string |
| `known_files[].source` | Must be valid source enum |
| `artifacts[].tokens_estimate` | Must be positive integer |

### Runtime Context Validation

| Rule | Validation |
|------|------------|
| `session_id` format | Should start with `sess_` prefix |
| `started_at` <= `last_updated` | Start must not be after last update |
| `decisions[].timestamp` | Must be between started_at and last_updated |
| `token_usage` | Must be non-negative integer |

### Post-Mortem Context Validation

| Rule | Validation |
|------|------------|
| `summary` length | Must be non-empty string |
| `duration_hours` | Must be non-negative if present |
| `commits[].reference_type` | Must be TASK_REFERENCE or COMPLETION_CLAIM |

### Git Hooks Configuration Validation

| Rule | Validation |
|------|------------|
| `mode` values | Must be one of: off, warn, prompt, strict |
| `on_mismatch` values | Must be one of: ignore, warn, prompt, block |
| `verbosity` values | Must be one of: quiet, normal, verbose |

---

## Versioning and Migration

### Version Format

All context formats include a version field for compatibility tracking:

```yaml
version: "1.0"  # Major.Minor
```

| Version Part | When Incremented |
|--------------|------------------|
| **Major** | Breaking changes requiring migration |
| **Minor** | New optional fields, backward compatible |

### Current Versions

| Format | Current Version | Last Updated |
|--------|-----------------|--------------|
| Plan Context | 1.0 | 2025-12-19 |
| Runtime Context | 1.0 | 2025-12-19 |
| Post-Mortem Context | 1.0 | 2025-12-19 |
| Git Hooks Config | 1.0 | 2025-12-19 |
| Context Index | 1.0 | 2025-12-14 |
| Context Config | 1.0 | 2025-12-14 |

### Migration Guidelines

When version changes require migration:

1. **Check current version** in existing files
2. **Back up** existing context data
3. **Run migration** via CLI: `vibey context migrate`
4. **Validate** migrated files
5. **Update index** version number

### Backward Compatibility

The context system maintains backward compatibility by:

- Reading files without version as "1.0"
- Ignoring unknown fields (forward compatible)
- Providing default values for new optional fields
- Preserving original data during migration

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| [CONTEXT_ARCHITECTURE.md](CONTEXT_ARCHITECTURE.md) | Full architecture design |
| [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) | System overview |
| [ADR-0003](adr/0003-dual-storage-sqlite-yaml.md) | YAML + SQLite rationale |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-19 | Initial documentation release |
