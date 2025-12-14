# Context Directory Design

## Overview

This document defines the unified context directory structure for the Vibey framework. The design consolidates existing context storage patterns into a coherent, extensible architecture that supports AI agent workflows, session tracking, and decision auditing.

---

## Current State Analysis

### Existing Directories

| Location | Purpose | Format |
|----------|---------|--------|
| `.vibey/discovery/` | Project discovery outputs | YAML (current.yaml, history/) |
| `.vibey/roadmap/context/` | Roadmap-related context | MD files per sprint/track |
| `.vibey/roadmap/sessions/` | Session tracking (empty) | Planned |
| `.vibey/roadmap/activity_log/` | Activity audit trail | JSONL by month |

### Issues with Current Structure

1. **Fragmented storage** - Context spread across multiple directories
2. **No unified index** - Hard to find relevant context
3. **Inconsistent formats** - Mix of YAML, MD, JSONL
4. **No session linkage** - Context not tied to work sessions
5. **Limited retention policy** - No automatic cleanup

---

## Proposed Directory Structure

```
.vibey/context/                        # Root context directory (NEW)
├── index.yaml                         # Master index of all context
├── config.yaml                        # Context system configuration
│
├── sessions/                          # Session context
│   ├── active.yaml                    # Currently active session (symlink)
│   ├── current/                       # Active session directory
│   │   └── {session-ulid}.yaml        # Current session file
│   └── history/                       # Archived sessions
│       └── {YYYY-MM}/                 # Monthly buckets
│           └── {session-ulid}.yaml    # Archived session files
│
├── tasks/                             # Task execution context
│   ├── current/                       # Active task contexts
│   │   └── {task-ulid}.yaml           # Active task context
│   └── completed/                     # Completed task contexts
│       └── {YYYY-MM}/                 # Monthly buckets
│           └── {task-ulid}.yaml       # Completed task context
│
├── decisions/                         # Decision records (ADRs)
│   └── {YYYY-MM}/                     # Monthly buckets
│       └── {sequence}-{slug}.md       # Decision document
│
├── discovery/                         # Project discovery (MOVE from .vibey/discovery/)
│   ├── current.yaml                   # Current discovery output
│   ├── history/                       # Historical discoveries
│   │   └── {timestamp}.yaml           # Timestamped discovery
│   └── diffs/                         # Discovery diffs
│       └── {from}-{to}.yaml           # Diff between versions
│
├── sprints/                           # Sprint context (MOVE from .vibey/roadmap/context/sprints/)
│   └── {sprint-slug}/                 # Per-sprint directory
│       ├── SPRINT_PLAN.md             # Sprint planning doc
│       └── {artifact}.*               # Sprint artifacts
│
├── agents/                            # Agent-specific context
│   └── {agent-name}/                  # Per-agent directory
│       ├── state.yaml                 # Agent state
│       └── history/                   # Agent history
│
└── exports/                           # Exported context bundles
    └── {export-name}.tar.gz           # Context export archive
```

---

## Naming Conventions

### IDs and Identifiers

| Type | Format | Example | Rationale |
|------|--------|---------|-----------|
| Sessions | ULID | `01KC7MN54VXRB3APC5FV5XBDXX` | Sortable, unique, no collision |
| Tasks | ULID | `01KC81GRE7HFXA9J6FYFM7H3BP` | Consistent with roadmap |
| Decisions | Sequence-slug | `0001-adopt-ulid-naming.md` | Human-readable, ordered |
| Sprints | Slug | `user-journey-phase-4-4` | Human-readable, matches existing |
| Agents | Name | `planning-agent` | Descriptive, lowercase |

### File Naming Rules

1. **ULID-based files**: `{ulid}.yaml` - For machine-generated content
2. **Slug-based files**: `{slug}.md` - For human-authored content
3. **Timestamped files**: `{ISO8601}.yaml` - For versioned content
4. **Sequence files**: `{4-digit}-{slug}.md` - For ordered content

### Directory Naming Rules

1. **Date buckets**: `YYYY-MM` format for monthly archival
2. **Sprint directories**: Match sprint slug from roadmap
3. **Agent directories**: Lowercase, hyphenated agent name

---

## Index File Schema

### Master Index (`index.yaml`)

```yaml
# .vibey/context/index.yaml
context:
  version: "1.0"
  created: "2025-12-14T17:00:00Z"
  last_updated: "2025-12-14T17:30:00Z"

  stats:
    sessions_total: 42
    sessions_active: 1
    tasks_total: 156
    decisions_total: 23
    discovery_versions: 8

  current:
    session_id: 01KC7MN54VXRB3APC5FV5XBDXX
    session_path: sessions/current/01KC7MN54VXRB3APC5FV5XBDXX.yaml
    discovery_path: discovery/current.yaml

  recent_tasks:
    - id: 01KC81GRE7HFXA9J6FYFM7H3BP
      title: "Design context directory structure"
      status: in_progress
      context_path: tasks/current/01KC81GRE7HFXA9J6FYFM7H3BP.yaml

  recent_decisions:
    - id: "0001-adopt-ulid-naming"
      title: "Adopt ULID naming convention"
      date: "2025-12-14"
      path: decisions/2025-12/0001-adopt-ulid-naming.md
```

### Configuration (`config.yaml`)

```yaml
# .vibey/context/config.yaml
context_config:
  version: "1.0"

  retention:
    sessions:
      active_max: 1              # Only 1 active session at a time
      history_days: 90           # Keep 90 days of session history
      archive_format: yaml       # Archive format

    tasks:
      completed_days: 180        # Keep 6 months of completed tasks
      archive_monthly: true      # Archive by month

    decisions:
      keep_forever: true         # Never auto-delete decisions

    discovery:
      history_max: 10            # Keep last 10 discoveries
      diff_days: 30              # Keep diffs for 30 days

  cleanup:
    enabled: true
    schedule: "weekly"           # Run cleanup weekly
    dry_run_first: true          # Preview before deleting

  export:
    include_history: false       # Don't include history in exports by default
    compress: true               # Compress exports
```

---

## Context File Schemas

### Session Context

```yaml
# sessions/current/{session-ulid}.yaml
session:
  id: 01KC7MN54VXRB3APC5FV5XBDXX
  type: development                    # development | research | maintenance
  started: "2025-12-14T17:00:00Z"
  ended: null                          # Set on session end
  status: active                       # active | completed | abandoned

  agent: claude-opus-4-5               # AI agent identity
  user: fredabood                      # Human user

  goals:
    - "Complete Phase 4.4 Task 1"
    - "Design context directory structure"

  tasks_worked:
    - id: 01KC81GRE7HFXA9J6FYFM7H3BP
      title: "Design context directory structure"
      started: "2025-12-14T17:00:00Z"
      completed: null

  decisions_made:
    - id: 0001-adopt-ulid-naming
      title: "Adopt ULID naming convention"

  artifacts_created:
    - path: .vibey/context/sprints/user-journey-phase-4-4/CONTEXT_DIRECTORY_DESIGN.md
      type: design_document

  summary: null                        # Set on session end

  metadata:
    git_branch: main
    git_commit_start: af4af190
    git_commits: []                    # Commits made during session
    token_usage: null                  # Track token consumption
```

### Task Context

```yaml
# tasks/current/{task-ulid}.yaml
task_context:
  task_id: 01KC81GRE7HFXA9J6FYFM7H3BP
  sprint_id: 01KC81GRE6NHSPP7X34M5MT22D
  track_id: 01KC2D0JKVT80AFQ6C1PA8CKJT

  title: "Design context directory structure"
  description: "Design the .vibey/context/ directory structure..."

  sessions:
    - session_id: 01KC7MN54VXRB3APC5FV5XBDXX
      started: "2025-12-14T17:00:00Z"
      ended: null

  commands_executed:
    - command: "vibey roadmap start 01KC81GRE7HFXA9J6FYFM7H3BP"
      timestamp: "2025-12-14T17:00:00Z"
      duration_ms: 234
      status: success

  files_modified:
    - path: .vibey/context/sprints/user-journey-phase-4-4/CONTEXT_DIRECTORY_DESIGN.md
      action: created
      timestamp: "2025-12-14T17:10:00Z"

  decisions:
    - "Use ULID for machine IDs, slugs for human content"
    - "Monthly buckets for archival"

  blockers_encountered: []

  notes: |
    Key design decisions:
    - Unified .vibey/context/ directory
    - Migration path from existing structure
    - Index file for quick lookups
```

### Decision Record

```markdown
# decisions/YYYY-MM/NNNN-slug.md

# NNNN. Decision Title

Date: YYYY-MM-DD
Status: proposed | accepted | deprecated | superseded
Deciders: [list of people]
Related Tasks: [task IDs]

## Context

What is the issue that we're seeing that motivates this decision?

## Decision

What is the decision that was made?

## Consequences

What becomes easier or harder as a result of this decision?

## Alternatives Considered

What other options were considered?

## References

- Related documents
- External resources
```

---

## Retention Policies

### Session Retention

| Status | Duration | Action |
|--------|----------|--------|
| Active | Unlimited | Keep in `current/` |
| Completed | 90 days | Move to `history/YYYY-MM/` |
| After 90 days | Archive | Compress and store |
| After 1 year | Delete | Remove compressed archive |

### Task Context Retention

| Status | Duration | Action |
|--------|----------|--------|
| Current (in_progress) | Unlimited | Keep in `current/` |
| Completed | 180 days | Move to `completed/YYYY-MM/` |
| After 180 days | Archive | Compress and store |
| After 1 year | Delete | Remove compressed archive |

### Discovery Retention

| Type | Count | Action |
|------|-------|--------|
| Current | 1 | Always keep `current.yaml` |
| History | 10 max | Keep most recent 10 |
| Diffs | 30 days | Delete diffs older than 30 days |

### Decision Retention

- **Keep forever** - Decisions are permanent records
- No automatic deletion
- Can be manually deprecated/superseded

---

## Migration Plan

### Phase 1: Create New Structure

```bash
# Create new directory structure
mkdir -p .vibey/context/{sessions/current,sessions/history}
mkdir -p .vibey/context/{tasks/current,tasks/completed}
mkdir -p .vibey/context/decisions
mkdir -p .vibey/context/discovery/{history,diffs}
mkdir -p .vibey/context/{sprints,agents,exports}

# Create initial config files
touch .vibey/context/index.yaml
touch .vibey/context/config.yaml
```

### Phase 2: Migrate Existing Content

| Source | Destination | Action |
|--------|-------------|--------|
| `.vibey/discovery/` | `.vibey/context/discovery/` | Move |
| `.vibey/roadmap/context/sprints/` | `.vibey/context/sprints/` | Move |
| `.vibey/roadmap/activity_log/` | Keep (separate system) | No change |
| `.vibey/roadmap/sessions/` | Remove (empty) | Delete |

### Phase 3: Update Code References

1. Update `vibey/operations/discovery/versioning.py` to use new path
2. Update sprint context loaders to use new path
3. Add migration command: `vibey context migrate`

### Phase 4: Deprecation

1. Add warning when old paths are accessed
2. Remove old directories after successful migration
3. Update documentation

---

## CLI Commands (Preview)

```bash
# List contexts
vibey context list [--type session|task|decision|discovery]
vibey context list --type session --status active

# Show context
vibey context show <context-id>
vibey context show --current-session

# Archive context
vibey context archive <context-id>

# Clean old contexts
vibey context clean --older-than 90 --type session --dry-run
vibey context clean --older-than 90 --type session

# Export context
vibey context export <context-id> --output bundle.tar.gz
vibey context export --session --include-history

# Import context
vibey context import bundle.tar.gz

# Search contexts
vibey context search "ULID naming" --type decision
```

---

## Integration Points

### AI Agent Integration

```python
# Agent context loader
class AgentContextLoader:
    def load_for_task(self, task_id: str) -> AgentContext:
        """Load all relevant context for a task."""
        return AgentContext(
            task=self.load_task_context(task_id),
            sprint=self.load_sprint_context(task.sprint_id),
            recent_sessions=self.load_recent_sessions(limit=3),
            recent_decisions=self.load_recent_decisions(limit=10),
            discovery=self.load_current_discovery(),
        )
```

### MCP Server Integration

```python
# MCP tools
@tool("vibey_load_context")
async def load_context(task_id: Optional[str] = None) -> str:
    """Load relevant context for AI agent work."""
    loader = AgentContextLoader()
    if task_id:
        context = loader.load_for_task(task_id)
    else:
        context = loader.load_for_session()
    return context.format_for_claude()
```

### CLI Command Integration

```python
# Context capture decorator
def capture_context(command_func):
    """Decorator to capture command execution context."""
    @wraps(command_func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = command_func(*args, **kwargs)
            if kwargs.get('output_context'):
                write_command_context(command_func, args, kwargs, result, start_time)
            return result
        except Exception as e:
            if kwargs.get('output_context'):
                write_error_context(command_func, args, kwargs, e, start_time)
            raise
    return wrapper
```

---

## Acceptance Criteria Checklist

- [x] Directory structure documented
- [x] Naming conventions defined (ULID for machine, slug for human)
- [x] Index file schema defined (`index.yaml`)
- [x] Retention policies defined (sessions: 90d, tasks: 180d, decisions: forever)
- [x] Migration from existing structure planned (4 phases)

---

## Implementation Notes

1. **Backward Compatibility**: Old paths will continue to work during migration with deprecation warnings
2. **Atomic Operations**: All writes use temp file + rename pattern for atomicity
3. **Index Updates**: Index is updated on every context write/archive operation
4. **Symlinks**: `active.yaml` is a symlink for fast current context lookup
5. **Monthly Buckets**: Reduces directory listing overhead for large histories

---

## Next Steps

1. **Task 2**: Implement context writers (`SessionContextWriter`, `TaskContextWriter`, etc.)
2. **Task 3**: Implement context readers with caching
3. **Task 4**: Add `vibey context` CLI command family
4. **Task 5**: Add `--output-context` flag to relevant CLI commands
5. **Task 6**: Implement agent context loading for MCP
