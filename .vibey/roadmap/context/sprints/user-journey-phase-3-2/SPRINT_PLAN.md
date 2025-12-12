# Sprint 3.2: Git Versioning for Vibe Coding Sessions

## Sprint Overview

**Goal:** Git-integrated session versioning with full reconstruction capability.

**Theme:** Implementation (building on Sprint 3.1 research & design)

**Estimated Duration:** 4-5 sessions

**Prerequisites:** Sprint 3.1 deliverables (CONTEXT_VERSIONING_DESIGN.md, SESSION_CONTEXT_REQUIREMENTS.md)

---

## Background

Sprint 3.1 established the theoretical foundation for context engineering. This sprint implements the core session versioning system that enables:

- Capturing what happened during AI coding sessions
- Versioning session context alongside git commits
- Reconstructing past sessions for audit or continuation
- Creating decision audit trails

The implementation follows vibey's dual-storage pattern (YAML source of truth + SQLite query cache).

---

## Tasks

### Task 1: Session Data Model

**Objective:** Implement the core data models for sessions and session events.

**Deliverables:**
- `vibey/roadmap/models/session.py` - Session and SessionEvent models
- `vibey/roadmap/models/__init__.py` - Updated exports

**Implementation:**

```python
# Session model structure
@dataclass
class Session:
    id: str                          # ULID
    name: str                        # Human-readable name (auto-generated or user-provided)
    started: datetime                # Session start time
    ended: Optional[datetime]        # Session end time (None if active)
    status: SessionStatus            # active, paused, completed, abandoned

    # Associations
    roadmap_id: str                  # Parent roadmap
    track_id: Optional[str]         # Associated track (if any)
    sprint_id: Optional[str]        # Associated sprint (if any)
    task_ids: List[str]             # Tasks worked on during session

    # Git integration
    start_commit: Optional[str]     # Git commit SHA at session start
    end_commit: Optional[str]       # Git commit SHA at session end
    commits: List[str]              # All commits made during session
    branch: Optional[str]           # Git branch name

    # Context snapshot
    context_snapshot: Dict[str, Any]  # Captured context at session start

    # Metadata
    goals: List[str]                # User-stated goals for session
    summary: Optional[str]          # Auto-generated or user summary
    token_usage: Optional[int]      # Estimated tokens used
    metadata: Dict[str, Any]        # Extension point

@dataclass
class SessionEvent:
    id: str                         # ULID
    session_id: str                 # Parent session
    timestamp: datetime             # When event occurred
    event_type: SessionEventType    # Type of event

    # Event data (varies by type)
    data: Dict[str, Any]

    # Optional associations
    task_id: Optional[str]          # Related task
    commit_sha: Optional[str]       # Related commit
    file_path: Optional[str]        # Related file

class SessionEventType(Enum):
    SESSION_START = "session_start"
    SESSION_PAUSE = "session_pause"
    SESSION_RESUME = "session_resume"
    SESSION_END = "session_end"

    GOAL_SET = "goal_set"
    GOAL_ACHIEVED = "goal_achieved"

    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"

    DECISION_MADE = "decision_made"
    QUESTION_ASKED = "question_asked"

    FILE_READ = "file_read"
    FILE_MODIFIED = "file_modified"
    FILE_CREATED = "file_created"

    COMMAND_RUN = "command_run"
    ERROR_ENCOUNTERED = "error_encountered"

    CONTEXT_LOADED = "context_loaded"
    CONTEXT_UPDATED = "context_updated"

    COMMIT_MADE = "commit_made"

    CUSTOM = "custom"

class SessionStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
```

**Acceptance Criteria:**
- [ ] Session model with all fields defined
- [ ] SessionEvent model with typed events
- [ ] Enums for status and event types
- [ ] Models follow existing vibey patterns (ULIDs, dataclasses)
- [ ] Type hints complete

---

### Task 2: Session YAML Serialization

**Objective:** Implement YAML serialization for sessions (source of truth).

**Deliverables:**
- `vibey/roadmap/serialization/session_yaml_loader.py`
- `vibey/roadmap/serialization/session_yaml_dumper.py`
- `.vibey/roadmap/sessions/` directory structure

**File Structure:**
```
.vibey/roadmap/
├── sessions/
│   ├── 01KCXXXX.yaml           # Session file (ULID-named)
│   └── 01KCYYYY.yaml
└── session_events/
    ├── 01KCXXXX/               # Events directory per session
    │   ├── 01KCAAAA.yaml       # Individual event files
    │   └── 01KCBBBB.yaml
    └── 01KCYYYY/
```

**Alternative: Single-file sessions (events embedded)**
```yaml
# .vibey/roadmap/sessions/01KCXXXX.yaml
session:
  id: 01KCXXXX
  name: "Feature implementation session"
  started: '2025-12-12T10:00:00+00:00'
  ended: '2025-12-12T12:30:00+00:00'
  status: completed

  track_id: 01KC2D0JKVT80AFQ6C1PA8CKJT
  sprint_id: 01KC81GRE4ZAJR0ZP9RCQCJ79Z
  task_ids:
    - 01KCAAAA
    - 01KCBBBB

  start_commit: abc123
  end_commit: def456
  commits:
    - abc123
    - def456
  branch: main

  goals:
    - "Complete Task 1"
    - "Fix bug in loader"

  summary: "Implemented session model and serialization"

  events:
    - id: 01KCEVT1
      timestamp: '2025-12-12T10:00:00+00:00'
      event_type: session_start
      data:
        context_files_loaded: 5

    - id: 01KCEVT2
      timestamp: '2025-12-12T10:05:00+00:00'
      event_type: task_start
      data:
        task_id: 01KCAAAA
        task_title: "Implement session model"
```

**Implementation Notes:**
- Follow existing yaml_loader.py patterns
- Handle both load and dump operations
- Support incremental event appending
- Validate against session schema

**Acceptance Criteria:**
- [ ] Load session from YAML file
- [ ] Dump session to YAML file
- [ ] Handle session events (embedded or separate files)
- [ ] Incremental event writing (append without full rewrite)
- [ ] Schema validation

---

### Task 3: Session SQLite Schema & Operations

**Objective:** Add session tables to SQLite database for fast querying.

**Deliverables:**
- Update `vibey/roadmap/serialization/schema.sql` with session tables
- `vibey/roadmap/serialization/session_sql_loader.py`
- `vibey/roadmap/serialization/session_sql_dumper.py`

**Schema:**
```sql
-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    started TEXT NOT NULL,
    ended TEXT,
    status TEXT NOT NULL DEFAULT 'active',

    roadmap_id TEXT NOT NULL,
    track_id TEXT,
    sprint_id TEXT,

    start_commit TEXT,
    end_commit TEXT,
    branch TEXT,

    goals TEXT,  -- JSON array
    summary TEXT,
    token_usage INTEGER,
    context_snapshot TEXT,  -- JSON object
    metadata TEXT,  -- JSON object

    FOREIGN KEY (roadmap_id) REFERENCES roadmaps(id),
    FOREIGN KEY (track_id) REFERENCES tracks(id),
    FOREIGN KEY (sprint_id) REFERENCES sprints(id)
);

-- Session-Task association (many-to-many)
CREATE TABLE IF NOT EXISTS session_tasks (
    session_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    PRIMARY KEY (session_id, task_id),
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Session commits
CREATE TABLE IF NOT EXISTS session_commits (
    session_id TEXT NOT NULL,
    commit_sha TEXT NOT NULL,
    committed_at TEXT,
    message TEXT,
    PRIMARY KEY (session_id, commit_sha),
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Session events
CREATE TABLE IF NOT EXISTS session_events (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    data TEXT,  -- JSON object
    task_id TEXT,
    commit_sha TEXT,
    file_path TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started);
CREATE INDEX IF NOT EXISTS idx_sessions_track ON sessions(track_id);
CREATE INDEX IF NOT EXISTS idx_sessions_sprint ON sessions(sprint_id);
CREATE INDEX IF NOT EXISTS idx_session_events_session ON session_events(session_id);
CREATE INDEX IF NOT EXISTS idx_session_events_type ON session_events(event_type);
CREATE INDEX IF NOT EXISTS idx_session_events_timestamp ON session_events(timestamp);
```

**Query Operations:**
- Load session by ID
- List sessions (with filters: status, track, sprint, date range)
- Get active session
- Get session events (with filters: type, date range)
- Get sessions by commit SHA
- Get sessions by task ID

**Acceptance Criteria:**
- [ ] Schema added to schema.sql
- [ ] SQL loader with all query operations
- [ ] SQL dumper with upsert support
- [ ] Proper indexes for performance
- [ ] Foreign key relationships maintained

---

### Task 4: Session Manager Operations

**Objective:** Implement core session management operations.

**Deliverables:**
- `vibey/operations/roadmap/session_manager.py`

**Operations:**

```python
class SessionManager:
    """Manages session lifecycle and operations."""

    def start_session(
        self,
        name: Optional[str] = None,
        goals: Optional[List[str]] = None,
        track_id: Optional[str] = None,
        sprint_id: Optional[str] = None,
        task_ids: Optional[List[str]] = None,
    ) -> Session:
        """Start a new coding session."""
        # 1. Check for existing active session
        # 2. Capture current git state (commit, branch)
        # 3. Capture context snapshot
        # 4. Create session record
        # 5. Log SESSION_START event
        # 6. Save to YAML and SQLite

    def end_session(
        self,
        session_id: Optional[str] = None,  # None = current active
        summary: Optional[str] = None,
        status: SessionStatus = SessionStatus.COMPLETED,
    ) -> Session:
        """End a coding session."""
        # 1. Find active session (or by ID)
        # 2. Capture end git state
        # 3. Calculate token usage (if possible)
        # 4. Log SESSION_END event
        # 5. Update session record
        # 6. Save to YAML and SQLite

    def pause_session(self, session_id: Optional[str] = None) -> Session:
        """Pause a session for later resumption."""

    def resume_session(self, session_id: str) -> Session:
        """Resume a paused session."""

    def get_active_session(self) -> Optional[Session]:
        """Get the currently active session."""

    def get_session(self, session_id: str) -> Session:
        """Get a session by ID."""

    def list_sessions(
        self,
        status: Optional[SessionStatus] = None,
        track_id: Optional[str] = None,
        sprint_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[Session]:
        """List sessions with optional filters."""

    def log_event(
        self,
        event_type: SessionEventType,
        data: Dict[str, Any],
        session_id: Optional[str] = None,  # None = active session
        task_id: Optional[str] = None,
        commit_sha: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> SessionEvent:
        """Log an event to the session."""

    def get_events(
        self,
        session_id: str,
        event_types: Optional[List[SessionEventType]] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[SessionEvent]:
        """Get events for a session."""

    def associate_task(
        self,
        task_id: str,
        session_id: Optional[str] = None,
    ) -> None:
        """Associate a task with the session."""

    def associate_commit(
        self,
        commit_sha: str,
        message: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Associate a git commit with the session."""
```

**Context Snapshot Capture:**
```python
def capture_context_snapshot(self) -> Dict[str, Any]:
    """Capture current context state for session."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git": {
            "commit": get_current_commit(),
            "branch": get_current_branch(),
            "dirty": is_working_tree_dirty(),
        },
        "roadmap": {
            "active_track": get_active_track_id(),
            "active_sprint": get_active_sprint_id(),
            "active_tasks": get_in_progress_task_ids(),
        },
        "config": {
            "hash": hash_config_files(),  # Detect config changes
        },
        "environment": {
            "python_version": sys.version,
            "vibey_version": get_vibey_version(),
        },
    }
```

**Acceptance Criteria:**
- [ ] All SessionManager methods implemented
- [ ] Proper error handling (no active session, session not found, etc.)
- [ ] Context snapshot capture working
- [ ] Git state capture working
- [ ] Events logged correctly
- [ ] YAML and SQLite sync maintained

---

### Task 5: Session CLI Commands

**Objective:** Add CLI commands for session management.

**Deliverables:**
- Update `vibey/cli/commands.py` with session commands
- Update `vibey/cli/main.py` with session group

**Commands:**

```bash
# Session lifecycle
vibey session start [NAME] [--goal "..."] [--track ID] [--sprint ID] [--task ID]
vibey session end [--summary "..."] [--status completed|abandoned]
vibey session pause
vibey session resume SESSION_ID

# Session queries
vibey session status                    # Show active session
vibey session show SESSION_ID           # Show session details
vibey session list [--status ...] [--track ...] [--since ...] [--limit N]
vibey session events SESSION_ID [--type ...] [--since ...]

# Session context
vibey session context                   # Show current session context
vibey session snapshot                  # Capture context snapshot now

# Session associations
vibey session link-task TASK_ID         # Associate task with active session
vibey session link-commit [COMMIT_SHA]  # Associate commit (default: HEAD)

# Session export
vibey session export SESSION_ID [--format yaml|json|markdown]
```

**Output Formats:**

```bash
$ vibey session status
Active Session: 01KCXXXX
  Name: Feature implementation
  Started: 2025-12-12 10:00:00 (2h 30m ago)
  Branch: main
  Tasks: 2 (1 completed, 1 in progress)
  Events: 15
  Commits: 3

$ vibey session list --limit 5
ID          | Name                      | Status    | Started      | Duration
------------|---------------------------|-----------|--------------|----------
01KCXXXX    | Feature implementation    | active    | 2h ago       | ongoing
01KCWWWW    | Bug fix session           | completed | yesterday    | 1h 15m
01KCVVVV    | Documentation update      | completed | 2 days ago   | 45m
```

**Acceptance Criteria:**
- [ ] All CLI commands implemented
- [ ] Consistent output formatting
- [ ] Proper error messages
- [ ] Help text for all commands
- [ ] Tab completion support

---

### Task 6: Git Hook Integration

**Objective:** Integrate session tracking with git hooks.

**Deliverables:**
- Update `vibey/operations/git/hooks/post_commit.py`
- Update `vibey/operations/git/hooks/pre_push.py`
- `vibey/operations/roadmap/hooks/session_hooks.py`

**Hook Behaviors:**

**Post-commit hook:**
```python
def on_post_commit(commit_sha: str, message: str):
    """Called after each commit."""
    session_manager = SessionManager()
    active_session = session_manager.get_active_session()

    if active_session:
        # Associate commit with session
        session_manager.associate_commit(
            commit_sha=commit_sha,
            message=message,
        )

        # Log commit event
        session_manager.log_event(
            event_type=SessionEventType.COMMIT_MADE,
            data={
                "commit_sha": commit_sha,
                "message": message,
            },
        )
```

**Session-aware commit messages:**
```python
def enhance_commit_message(message: str) -> str:
    """Add session reference to commit message."""
    active_session = get_active_session()
    if active_session:
        return f"{message}\n\nSession: {active_session.id}"
    return message
```

**Pre-push hook:**
```python
def on_pre_push():
    """Warn if pushing with active session."""
    active_session = get_active_session()
    if active_session:
        print(f"[vibey] Active session: {active_session.id}")
        print(f"[vibey] Consider ending session before push: vibey session end")
```

**Acceptance Criteria:**
- [ ] Post-commit automatically associates commits with active session
- [ ] Pre-push warns about active sessions
- [ ] Commit messages optionally include session ID
- [ ] Hooks are non-blocking (failures logged, not fatal)

---

### Task 7: Session Reconstruction

**Objective:** Enable reconstruction/replay of past sessions.

**Deliverables:**
- `vibey/operations/roadmap/session_reconstruction.py`
- `vibey session reconstruct SESSION_ID` command

**Reconstruction Capabilities:**

```python
class SessionReconstructor:
    """Reconstructs session state for audit or continuation."""

    def get_session_timeline(self, session_id: str) -> SessionTimeline:
        """Get chronological timeline of session events."""
        return SessionTimeline(
            session=self.get_session(session_id),
            events=self.get_events(session_id),
            commits=self.get_commits(session_id),
            file_changes=self.get_file_changes(session_id),
        )

    def get_session_context_at(
        self,
        session_id: str,
        timestamp: datetime,
    ) -> Dict[str, Any]:
        """Reconstruct context state at a point in time."""
        # Start with session's initial context snapshot
        # Apply events up to timestamp
        # Return reconstructed state

    def get_decisions_made(self, session_id: str) -> List[Decision]:
        """Extract decisions made during session."""
        events = self.get_events(
            session_id,
            event_types=[SessionEventType.DECISION_MADE],
        )
        return [Decision.from_event(e) for e in events]

    def generate_session_report(
        self,
        session_id: str,
        format: str = "markdown",
    ) -> str:
        """Generate human-readable session report."""

    def export_for_continuation(
        self,
        session_id: str,
    ) -> Dict[str, Any]:
        """Export session state for continuation in new session."""
```

**Session Report Format:**
```markdown
# Session Report: 01KCXXXX

## Summary
- **Name:** Feature implementation
- **Duration:** 2h 30m (10:00 - 12:30)
- **Status:** Completed

## Goals
1. [x] Complete Task 1
2. [x] Fix bug in loader

## Tasks Worked On
- 01KCAAAA: Implement session model (completed)
- 01KCBBBB: Add serialization (completed)

## Commits Made
- abc123: feat: add session model
- def456: feat: add session serialization

## Key Decisions
1. **Decision:** Use embedded events in session YAML
   - **Rationale:** Simpler file structure, atomic updates
   - **Alternatives considered:** Separate event files

## Timeline
| Time  | Event | Details |
|-------|-------|---------|
| 10:00 | Session started | Context loaded |
| 10:05 | Task started | 01KCAAAA |
| 10:45 | Commit | abc123 |
| 11:00 | Task completed | 01KCAAAA |
| ... | ... | ... |
```

**Acceptance Criteria:**
- [ ] Timeline reconstruction working
- [ ] Context-at-time reconstruction working
- [ ] Decision extraction working
- [ ] Report generation in markdown format
- [ ] Export for continuation working

---

### Task 8: Integration Testing

**Objective:** Comprehensive tests for session system.

**Deliverables:**
- `tests/operations/roadmap/test_session_manager.py`
- `tests/roadmap/serialization/test_session_yaml.py`
- `tests/roadmap/serialization/test_session_sql.py`
- `tests/cli/test_session_commands.py`

**Test Scenarios:**

```python
# Session lifecycle tests
def test_start_session():
    """Test starting a new session."""

def test_start_session_with_existing_active():
    """Test error when starting session with active session."""

def test_end_session():
    """Test ending a session."""

def test_pause_resume_session():
    """Test pause and resume flow."""

# Event logging tests
def test_log_event():
    """Test logging events to session."""

def test_log_event_no_active_session():
    """Test error when logging without active session."""

# Association tests
def test_associate_task():
    """Test associating task with session."""

def test_associate_commit():
    """Test associating commit with session."""

# Query tests
def test_list_sessions_with_filters():
    """Test session listing with various filters."""

def test_get_events_with_filters():
    """Test event retrieval with filters."""

# Serialization tests
def test_session_yaml_roundtrip():
    """Test YAML save and load."""

def test_session_sql_roundtrip():
    """Test SQLite save and load."""

# Reconstruction tests
def test_session_timeline():
    """Test timeline reconstruction."""

def test_session_report_generation():
    """Test report generation."""

# CLI tests
def test_cli_session_start():
    """Test vibey session start command."""

def test_cli_session_status():
    """Test vibey session status command."""
```

**Acceptance Criteria:**
- [ ] >90% code coverage for session modules
- [ ] All lifecycle flows tested
- [ ] Edge cases covered (no active session, invalid IDs, etc.)
- [ ] CLI commands tested with CliRunner
- [ ] Integration tests for full flows

---

## Task Dependencies

```
Task 1 (Data Model)
    ↓
Task 2 (YAML Serialization) ←── depends on Task 1
    ↓
Task 3 (SQLite Schema) ←── depends on Task 1, can parallel with Task 2
    ↓
Task 4 (Session Manager) ←── depends on Tasks 2, 3
    ↓
Task 5 (CLI Commands) ←── depends on Task 4
    ↓
Task 6 (Git Hooks) ←── depends on Task 4
    ↓
Task 7 (Reconstruction) ←── depends on Tasks 4, 5
    ↓
Task 8 (Testing) ←── should be written alongside each task
```

**Parallelization:**
- Tasks 2 and 3 can run in parallel after Task 1
- Tasks 5 and 6 can run in parallel after Task 4
- Task 8 should be incremental throughout

---

## Success Criteria

- [ ] Session model fully implemented
- [ ] YAML serialization working with round-trip integrity
- [ ] SQLite schema with all tables and indexes
- [ ] SessionManager with all operations
- [ ] CLI commands for all session operations
- [ ] Git hooks automatically tracking commits
- [ ] Session reconstruction and reports working
- [ ] >90% test coverage
- [ ] Documentation updated

---

## Out of Scope

- MCP tool integration (deferred to Sprint 3.3)
- Session sharing/export to external systems
- Session analytics/insights
- Automatic session start detection

---

## File Changes Summary

**New Files:**
- `vibey/roadmap/models/session.py`
- `vibey/roadmap/serialization/session_yaml_loader.py`
- `vibey/roadmap/serialization/session_yaml_dumper.py`
- `vibey/roadmap/serialization/session_sql_loader.py`
- `vibey/roadmap/serialization/session_sql_dumper.py`
- `vibey/operations/roadmap/session_manager.py`
- `vibey/operations/roadmap/session_reconstruction.py`
- `vibey/operations/roadmap/hooks/session_hooks.py`
- `tests/operations/roadmap/test_session_manager.py`
- `tests/roadmap/serialization/test_session_yaml.py`
- `tests/roadmap/serialization/test_session_sql.py`
- `tests/cli/test_session_commands.py`

**Modified Files:**
- `vibey/roadmap/models/__init__.py`
- `vibey/roadmap/serialization/schema.sql`
- `vibey/cli/main.py`
- `vibey/cli/commands.py`
- `vibey/operations/git/hooks/post_commit.py`
- `vibey/operations/git/hooks/pre_push.py`

**New Directories:**
- `.vibey/roadmap/sessions/`

---

## Notes

This sprint establishes the core session tracking infrastructure. The implementation should be:

1. **Non-intrusive** - Sessions are opt-in, don't break existing workflows
2. **Lightweight** - Minimal overhead for session tracking
3. **Git-native** - Sessions live alongside code in git
4. **Queryable** - SQLite enables fast session lookup and analysis

Focus on getting the core lifecycle (start/end/events) solid before adding advanced features.
