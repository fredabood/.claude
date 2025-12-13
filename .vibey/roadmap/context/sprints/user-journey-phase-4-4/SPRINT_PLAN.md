# Sprint 4.4: Context Directory Writers & CLI Integration

## Sprint Overview

**Goal:** Build infrastructure for writing and reading context files that AI agents can consume, with full CLI support.

**Theme:** Context Management Infrastructure

**Estimated Duration:** 5-6 sessions

**Prerequisites:** Phase 4.2 (Discovery Output Architecture) completed

---

## Background

The context engineering work in Phase 3 established session tracking and audit trails. Phase 4.2 added structured discovery outputs. This sprint completes the context infrastructure by:

1. Designing a unified context directory structure
2. Implementing writers for different context types
3. Implementing readers for loading context
4. Adding CLI commands for context management
5. Enabling AI agents to automatically load relevant context

---

## Tasks

### Task 1: Design context directory structure

**Objective:** Design the `.vibey/context/` directory structure: subdirectories by type, naming conventions, index files, cleanup policies.

**Deliverables:**
- `CONTEXT_DIRECTORY_DESIGN.md` - Design document

**Proposed Structure:**

```
.vibey/context/
├── index.yaml                    # Master index of all context
├── sessions/                     # Session context (from Phase 3)
│   ├── active.yaml              # Currently active session
│   └── history/                 # Historical sessions
├── tasks/                        # Task context
│   ├── current/                 # Active task context
│   └── completed/               # Completed task context
├── decisions/                    # Decision records
│   └── YYYY-MM/                 # Monthly buckets
├── discovery/                    # Discovery outputs (from 4.2)
│   ├── current.yaml
│   └── history/
├── sprints/                      # Sprint context
│   └── {sprint-id}/             # Per-sprint context
└── agents/                       # Agent-specific context
    └── {agent-name}/            # Per-agent context
```

**Design Decisions:**
- Naming conventions (ULIDs vs slugs vs dates)
- Index file structure
- Cleanup/retention policies
- Symlinks for "current" items

**Acceptance Criteria:**
- [ ] Directory structure documented
- [ ] Naming conventions defined
- [ ] Index file schema defined
- [ ] Retention policies defined
- [ ] Migration from existing structure planned

---

### Task 2: Implement context writers

**Objective:** Implement writer classes for each context type: SessionContextWriter, TaskContextWriter, DecisionContextWriter, etc.

**Deliverables:**
- `vibey/operations/context/writers.py`
- Individual writer modules

**Writer Interface:**

```python
class ContextWriter(Protocol):
    def write(self, context: T, path: Optional[Path] = None) -> Path:
        """Write context to storage, return path."""

    def update(self, context_id: str, updates: Dict) -> None:
        """Update existing context."""

    def archive(self, context_id: str) -> Path:
        """Archive context to history."""

class SessionContextWriter(ContextWriter[SessionContext]):
    """Writes session context to .vibey/context/sessions/"""

class TaskContextWriter(ContextWriter[TaskContext]):
    """Writes task context to .vibey/context/tasks/"""

class DecisionContextWriter(ContextWriter[DecisionContext]):
    """Writes decision context to .vibey/context/decisions/"""

class SprintContextWriter(ContextWriter[SprintContext]):
    """Writes sprint context to .vibey/context/sprints/"""
```

**Implementation:**
1. Create base `ContextWriter` class with common logic
2. Implement type-specific writers
3. Handle index file updates
4. Implement atomic writes
5. Add validation before write

**Acceptance Criteria:**
- [ ] Base writer implemented
- [ ] SessionContextWriter implemented
- [ ] TaskContextWriter implemented
- [ ] DecisionContextWriter implemented
- [ ] SprintContextWriter implemented
- [ ] Index updates working
- [ ] Atomic writes working

---

### Task 3: Implement context readers

**Objective:** Implement reader classes for loading context: ContextLoader with type-specific handlers and caching.

**Deliverables:**
- `vibey/operations/context/readers.py`
- `vibey/operations/context/cache.py`

**Reader Interface:**

```python
class ContextReader(Protocol):
    def read(self, context_id: str) -> T:
        """Read context by ID."""

    def read_current(self) -> Optional[T]:
        """Read current/active context."""

    def list(self, filters: Optional[Dict] = None) -> List[T]:
        """List contexts matching filters."""

    def search(self, query: str) -> List[T]:
        """Search contexts by content."""

class ContextLoader:
    """Unified context loader with caching."""

    def __init__(self, root_dir: Path, cache_ttl: int = 300):
        self.root_dir = root_dir
        self.cache = ContextCache(ttl=cache_ttl)
        self.readers = {
            'session': SessionContextReader(root_dir),
            'task': TaskContextReader(root_dir),
            'decision': DecisionContextReader(root_dir),
            'sprint': SprintContextReader(root_dir),
        }

    def load(self, context_type: str, context_id: str) -> Any:
        """Load context with caching."""

    def load_for_agent(self, agent_name: str) -> AgentContext:
        """Load all relevant context for an agent."""
```

**Caching:**
- In-memory cache with TTL
- Cache invalidation on writes
- Cache warm-up for common patterns

**Acceptance Criteria:**
- [ ] Base reader implemented
- [ ] Type-specific readers implemented
- [ ] ContextLoader with caching
- [ ] Search functionality
- [ ] List with filters

---

### Task 4: Implement 'vibey context' command family

**Objective:** Add context management commands: list, show, archive, clean, export. Full lifecycle management.

**Deliverables:**
- Updated `vibey/cli/commands.py`
- New context command group

**Commands:**

```bash
# List contexts
vibey context list [--type session|task|decision|sprint] [--status active|archived]
# List all contexts, optionally filtered

# Show context
vibey context show <context-id> [--format yaml|json|text]
# Display specific context

# Archive context
vibey context archive <context-id>
# Move context to archive

# Clean old contexts
vibey context clean [--older-than DAYS] [--type ...] [--dry-run]
# Remove old archived contexts

# Export context
vibey context export <context-id> [--output FILE]
# Export context to file

# Import context
vibey context import <file>
# Import context from file

# Search contexts
vibey context search <query> [--type ...]
# Search across contexts
```

**Acceptance Criteria:**
- [ ] All commands implemented
- [ ] Help text complete
- [ ] Output formats working
- [ ] Filtering working
- [ ] Search working

---

### Task 5: Add --output-context flag to CLI commands

**Objective:** Add flag to relevant CLI commands to capture command context: inputs, outputs, duration, related entities.

**Deliverables:**
- Updated CLI commands with context capture

**Commands to Update:**

| Command | Context to Capture |
|---------|-------------------|
| `roadmap start` | Task started, session association |
| `roadmap complete` | Task completed, duration, deliverables |
| `roadmap create-sprint` | Sprint created, track association |
| `roadmap create-task` | Task created, sprint association |
| `discover` | Discovery run, results summary |

**Context Capture Format:**

```yaml
command_context:
  command: vibey roadmap start task-001
  timestamp: 2025-12-12T10:00:00Z
  duration_ms: 1234
  inputs:
    task_id: 01KC...
  outputs:
    status: success
    changes:
      - field: status
        old: not_started
        new: in_progress
  related:
    session_id: 01KC...
    sprint_id: 01KC...
```

**Implementation:**
1. Add `--output-context` flag to commands
2. Capture context during command execution
3. Write context using TaskContextWriter
4. Link to current session if active

**Acceptance Criteria:**
- [ ] Flag added to relevant commands
- [ ] Context captured correctly
- [ ] Context written to storage
- [ ] Session linkage working

---

### Task 6: Add context loading for AI agents

**Objective:** Implement automatic context loading when AI agents start work: load relevant task context, recent session context, discovery context.

**Deliverables:**
- `vibey/operations/context/agent_context.py`
- Integration with MCP server

**Agent Context Loading:**

```python
class AgentContextLoader:
    """Loads relevant context for AI agents."""

    def load_for_task(self, task_id: str) -> AgentContext:
        """Load context relevant to a specific task."""
        return AgentContext(
            task=self.load_task_context(task_id),
            sprint=self.load_sprint_context(task.sprint_id),
            recent_sessions=self.load_recent_sessions(limit=3),
            recent_decisions=self.load_recent_decisions(limit=10),
            discovery=self.load_current_discovery(),
        )

    def load_for_session(self, session_id: str) -> AgentContext:
        """Load context for an active session."""

    def format_for_claude(self, context: AgentContext) -> str:
        """Format context for inclusion in CLAUDE.md or prompt."""
```

**MCP Integration:**
- Add `vibey_load_context` MCP tool
- Add `vibey://context/current` resource
- Auto-load context at session start

**Acceptance Criteria:**
- [ ] AgentContextLoader implemented
- [ ] Task context loading working
- [ ] Session context loading working
- [ ] MCP tool implemented
- [ ] Context formatting for Claude

---

## Task Dependencies

```
Task 1 (Design)
    ↓
Tasks 2, 3 (Writers, Readers) - can run in parallel
    ↓
Task 4 (CLI) - needs Tasks 2, 3
    ↓
Task 5 (--output-context) - needs Task 2
    ↓
Task 6 (Agent loading) - needs Tasks 2, 3
```

---

## Success Criteria

- [ ] Context directory structure implemented
- [ ] Writers for all context types
- [ ] Readers with caching
- [ ] CLI commands for context management
- [ ] Context capture on CLI commands
- [ ] Automatic context loading for agents

---

## File Changes Summary

**New Files:**
- `vibey/operations/context/__init__.py`
- `vibey/operations/context/writers.py`
- `vibey/operations/context/readers.py`
- `vibey/operations/context/cache.py`
- `vibey/operations/context/agent_context.py`
- `docs/reference/CONTEXT_MANAGEMENT.md`

**Modified Files:**
- `vibey/cli/commands.py`
- `vibey/cli/main.py`
- `vibey/mcp/server.py`

**New Directories:**
- `.vibey/context/` (created at runtime)

---

## Notes

This sprint completes the context infrastructure. Combined with Phase 3 (session tracking) and Phase 4.2 (discovery), this provides comprehensive context management for AI-assisted development.
