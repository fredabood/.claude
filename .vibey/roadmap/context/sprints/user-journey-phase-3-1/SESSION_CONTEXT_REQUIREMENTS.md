# Session Context Requirements

**Sprint:** 3.1 - Context Engineering Research & Landscape
**Task:** 3 - Session Context Requirements
**Date:** 2025-12-12

---

## Executive Summary

This document defines requirements for vibey's session context system - a mechanism to track, version, and reconstruct AI-assisted coding sessions. Sessions are the fundamental unit of work in vibe coding, and proper session tracking enables auditability, reproducibility, and cross-session continuity.

**Key Design Principle:** Sessions should be lightweight to start but rich in captured context. The system should not impose friction on natural workflows while providing comprehensive audit capability when needed.

---

## Definitions

### Session

A **session** is a bounded period of AI-assisted coding activity within a vibey-managed project. It represents a logical unit of work that can be tracked, versioned, and potentially reproduced.

**Characteristics:**
- Has a unique identifier (ULID)
- Has a clear start point (explicit or implicit)
- Has an end point (explicit, timeout, or inferred)
- May be associated with one or more roadmap items (tasks, sprints)
- May span multiple git commits
- May be paused and resumed

### Session Event

A **session event** is a discrete, timestamped occurrence within a session that may be relevant for audit or reconstruction.

**Event Categories:**
- Lifecycle events (start, pause, resume, end)
- Context events (file loaded, context added/removed)
- Decision events (choice made, alternative considered)
- Work events (task started, commit made, error encountered)
- AI interaction events (prompt sent, response received)

### Session Context

**Session context** is the collection of information that was available to the AI assistant during a session. This includes both explicit context (files, prompts) and implicit context (project state, recent history).

### Session Snapshot

A **session snapshot** is a point-in-time capture of session state, including:
- Active context files
- Configuration state
- Git state (branch, uncommitted changes)
- Environment state (relevant environment variables)
- Active roadmap items

---

## Session Lifecycle

```
                    ┌─────────────────────────────────────────────┐
                    │                                             │
                    ▼                                             │
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│ Created  │───►│ Active   │───►│ Paused   │───►│ Active   │─────┤
└──────────┘    └──────────┘    └──────────┘    └──────────┘     │
    │               │                                             │
    │               │                                             │
    │               ▼                                             │
    │          ┌──────────┐    ┌──────────┐                      │
    └─────────►│ Ended    │───►│ Archived │◄─────────────────────┘
               └──────────┘    └──────────┘
```

### State Definitions

| State | Description | Transitions |
|-------|-------------|-------------|
| `created` | Session initialized but not yet active | → `active`, → `ended` |
| `active` | Session is currently in use | → `paused`, → `ended` |
| `paused` | Session temporarily suspended | → `active`, → `ended` |
| `ended` | Session completed or terminated | → `archived` |
| `archived` | Session preserved for long-term storage | Terminal state |

### Lifecycle Events

| Event | Trigger | Data Captured |
|-------|---------|---------------|
| `session_created` | Explicit start or auto-detection | Session ID, timestamp, initial context |
| `session_started` | First meaningful activity | Timestamp, initial goal (if provided) |
| `session_paused` | User pause or inactivity timeout | Timestamp, reason, snapshot |
| `session_resumed` | Activity after pause | Timestamp, context delta |
| `session_ended` | Explicit end or session timeout | Timestamp, summary, final snapshot |
| `session_archived` | Archive policy triggered | Archive location, retention info |

---

## Functional Requirements

### Session Management

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| SM-1 | System SHALL create sessions with unique ULID identifiers | P0 | Unique identification required for all tracking |
| SM-2 | System SHALL support explicit session start via CLI | P0 | Users need control over session boundaries |
| SM-3 | System SHALL support implicit session start on first activity | P1 | Reduce friction for casual usage |
| SM-4 | System SHALL support session pause with state preservation | P1 | Enable work interruption without data loss |
| SM-5 | System SHALL support session resume with context restoration | P1 | Enable continuity across interruptions |
| SM-6 | System SHALL support explicit session end via CLI | P0 | Users need control over session boundaries |
| SM-7 | System SHALL auto-end sessions after configurable inactivity | P2 | Prevent orphaned sessions |
| SM-8 | System MAY support concurrent sessions with clear boundaries | P3 | Advanced use case for parallel work |

### Context Capture

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| CC-1 | System SHALL capture session start context (files, config) | P0 | Essential for reconstruction |
| CC-2 | System SHALL capture context changes during session | P0 | Track evolution of understanding |
| CC-3 | System SHALL capture decisions with rationale | P0 | Primary audit requirement |
| CC-4 | System SHALL capture roadmap item associations | P0 | Integration with existing system |
| CC-5 | System SHALL capture git commits made during session | P0 | Associate code changes with context |
| CC-6 | System SHALL capture errors encountered | P1 | Important for debugging/learning |
| CC-7 | System SHOULD capture AI prompts and responses (opt-in) | P2 | Full audit capability, privacy consideration |
| CC-8 | System MAY capture terminal commands executed | P3 | Additional audit detail |

### Decision Logging

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| DL-1 | System SHALL support logging decisions with description | P0 | Core audit capability |
| DL-2 | System SHALL support logging alternatives considered | P0 | Understand decision context |
| DL-3 | System SHALL support logging rationale for decisions | P0 | Explain why choices were made |
| DL-4 | System SHOULD support categorizing decisions by type | P1 | Enable filtering and analysis |
| DL-5 | System SHOULD support linking decisions to code changes | P1 | Traceability |
| DL-6 | System MAY support decision confidence levels | P3 | Additional metadata |

### Session Query & Retrieval

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| QR-1 | System SHALL support listing sessions by date range | P0 | Basic discovery |
| QR-2 | System SHALL support filtering sessions by status | P0 | Find active/completed sessions |
| QR-3 | System SHALL support filtering sessions by roadmap item | P0 | Find related work |
| QR-4 | System SHALL support viewing session timeline | P1 | Understand session flow |
| QR-5 | System SHOULD support searching sessions by decision | P2 | Find past decisions |
| QR-6 | System SHOULD support searching sessions by content | P2 | Full-text search |
| QR-7 | System MAY support session comparison (diff) | P3 | Compare related sessions |

### Session Export & Reproducibility

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| ER-1 | System SHALL support exporting session as markdown | P1 | Human-readable format |
| ER-2 | System SHALL support exporting session as structured data | P1 | Machine-readable format |
| ER-3 | System SHOULD support session reconstruction checklist | P2 | Guide reproducibility |
| ER-4 | System MAY support session replay guidance | P3 | Step-by-step reconstruction |

---

## Non-Functional Requirements

### Performance

| ID | Requirement | Target |
|----|-------------|--------|
| PF-1 | Session creation latency | < 100ms |
| PF-2 | Event logging latency | < 50ms |
| PF-3 | Session list query (100 sessions) | < 500ms |
| PF-4 | Session detail retrieval | < 200ms |
| PF-5 | Snapshot creation | < 1s |

### Storage

| ID | Requirement | Target |
|----|-------------|--------|
| ST-1 | Session metadata size | < 10KB per session |
| ST-2 | Event log size (typical session) | < 50KB |
| ST-3 | Snapshot size | < 100KB |
| ST-4 | Full session export size | < 500KB |
| ST-5 | Database growth rate | < 10MB per 100 sessions |

### Scalability

| ID | Requirement | Target |
|----|-------------|--------|
| SC-1 | Sessions per project | 10,000+ |
| SC-2 | Events per session | 1,000+ |
| SC-3 | Concurrent active sessions | 5+ |
| SC-4 | Query performance at scale | O(log n) |

### Security & Privacy

| ID | Requirement | Priority |
|----|-------------|----------|
| SP-1 | Session data SHALL be stored locally only | P0 |
| SP-2 | AI prompt/response capture SHALL be opt-in | P0 |
| SP-3 | Sensitive data (secrets, tokens) SHALL NOT be captured | P0 |
| SP-4 | Session export SHALL redact sensitive patterns | P1 |
| SP-5 | Session data SHOULD support encryption at rest | P2 |
| SP-6 | Session data MAY support integrity verification | P2 |

---

## Data Model

### Session Entity

```yaml
session:
  # Identity
  id: "01KC..."              # ULID, globally unique
  project_id: "vibey-framework-v2"  # Project this session belongs to

  # Lifecycle
  status: "active"           # created | active | paused | ended | archived
  created: "2025-12-12T10:00:00Z"
  started: "2025-12-12T10:00:15Z"
  paused: null               # Timestamp if paused
  ended: null                # Timestamp when ended

  # Context
  goal: "Implement session tracking for Phase 3.2"
  roadmap_items:
    - type: "task"
      id: "01KC..."
    - type: "sprint"
      id: "01KC..."

  # Git association
  git:
    branch: "main"
    start_commit: "abc123"
    commits: ["def456", "ghi789"]
    end_commit: "ghi789"

  # Statistics
  stats:
    duration_seconds: 3600
    events_count: 45
    decisions_count: 3
    commits_count: 2
    files_modified: 8

  # Metadata
  metadata:
    environment: "claude-code"
    model: "claude-opus-4-5"
    agent_version: "2.5.0"
```

### Session Event Entity

```yaml
event:
  id: "01KC..."              # ULID
  session_id: "01KC..."      # Parent session
  timestamp: "2025-12-12T10:15:30Z"

  # Event classification
  category: "decision"       # lifecycle | context | decision | work | ai
  type: "decision_made"      # Specific event type

  # Event data (varies by type)
  data:
    description: "Chose YAML + SQLite hybrid storage"
    alternatives:
      - option: "YAML only"
        reason_rejected: "Query performance concerns"
      - option: "SQLite only"
        reason_rejected: "Git merge conflicts"
    rationale: "Combines human readability with query performance"
    confidence: "high"
    related_commits: ["def456"]
    related_files: ["vibey/roadmap/models/session.py"]
```

### Session Snapshot Entity

```yaml
snapshot:
  id: "01KC..."
  session_id: "01KC..."
  timestamp: "2025-12-12T10:00:15Z"
  type: "session_start"      # session_start | checkpoint | session_end

  # State capture
  context_files:
    - path: "CLAUDE.md"
      hash: "sha256:abc..."
      size: 15234
    - path: ".vibey/config/roadmap.yaml"
      hash: "sha256:def..."
      size: 1024

  git_state:
    branch: "main"
    commit: "abc123"
    dirty: true
    staged_files: ["file1.py"]
    modified_files: ["file2.py", "file3.py"]

  environment:
    python_version: "3.11.0"
    vibey_version: "2.5.0"
    relevant_env_vars:
      - name: "VIBEY_ENV"
        value: "development"

  roadmap_state:
    active_track: "01KC..."
    active_sprint: "01KC..."
    active_task: "01KC..."
```

### Decision Entity (Specialized Event)

```yaml
decision:
  id: "01KC..."
  session_id: "01KC..."
  timestamp: "2025-12-12T10:15:30Z"

  # Decision details
  description: "Selected hybrid YAML + SQLite storage pattern"
  category: "architecture"    # architecture | implementation | design | process

  # Alternatives considered
  alternatives:
    - id: "alt-1"
      description: "YAML files only"
      pros: ["Git-friendly", "Human readable"]
      cons: ["Slow queries at scale"]

    - id: "alt-2"
      description: "SQLite only"
      pros: ["Fast queries", "Compact storage"]
      cons: ["Git merge conflicts", "Binary format"]

    - id: "alt-3"
      description: "Hybrid: YAML source + SQLite cache"
      pros: ["Best of both approaches"]
      cons: ["Sync complexity"]

  # Selected option
  selected: "alt-3"
  rationale: |
    The hybrid approach mirrors the existing roadmap system pattern,
    maintaining consistency in architecture while getting performance
    benefits for queries.

  # Traceability
  related_files: ["vibey/roadmap/models/session.py"]
  related_commits: ["def456"]
  related_tasks: ["01KC..."]

  # Confidence
  confidence: "high"         # low | medium | high
  revisit: false             # Flag if decision should be revisited
```

---

## Storage Design

### File System Layout

```
.vibey/
├── sessions/
│   ├── index.yaml           # Quick lookup index
│   ├── 01KC8.../           # Session directory (by ULID prefix)
│   │   ├── session.yaml     # Session metadata
│   │   ├── events.jsonl     # Event log (append-only)
│   │   ├── decisions.yaml   # Decisions (for easy review)
│   │   └── snapshots/
│   │       ├── start.yaml   # Session start snapshot
│   │       └── end.yaml     # Session end snapshot
│   └── ...
├── sessions.db              # SQLite query cache
└── config/
    └── sessions.yaml        # Session system configuration
```

### Index File Format

```yaml
# .vibey/sessions/index.yaml
sessions:
  - id: "01KC8..."
    status: "ended"
    created: "2025-12-12T10:00:00Z"
    ended: "2025-12-12T12:00:00Z"
    goal: "Implement session tracking"
    tasks: ["01KC..."]
    commits: 3
    decisions: 2

  - id: "01KC9..."
    status: "active"
    created: "2025-12-12T14:00:00Z"
    goal: "Write session requirements"
    tasks: ["01KC..."]
```

### SQLite Schema (Cache)

```sql
-- Sessions table
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    status TEXT NOT NULL,
    goal TEXT,
    created TIMESTAMP NOT NULL,
    started TIMESTAMP,
    paused TIMESTAMP,
    ended TIMESTAMP,
    git_branch TEXT,
    start_commit TEXT,
    end_commit TEXT,
    duration_seconds INTEGER,
    events_count INTEGER DEFAULT 0,
    decisions_count INTEGER DEFAULT 0,
    commits_count INTEGER DEFAULT 0,
    metadata JSON
);

-- Events table
CREATE TABLE session_events (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    timestamp TIMESTAMP NOT NULL,
    category TEXT NOT NULL,
    type TEXT NOT NULL,
    data JSON,
    INDEX idx_session_timestamp (session_id, timestamp)
);

-- Decisions table
CREATE TABLE session_decisions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    timestamp TIMESTAMP NOT NULL,
    description TEXT NOT NULL,
    category TEXT,
    selected_alternative TEXT,
    rationale TEXT,
    confidence TEXT,
    metadata JSON,
    INDEX idx_session_timestamp (session_id, timestamp)
);

-- Session-Task associations
CREATE TABLE session_tasks (
    session_id TEXT NOT NULL REFERENCES sessions(id),
    task_id TEXT NOT NULL,
    PRIMARY KEY (session_id, task_id)
);

-- Session-Commit associations
CREATE TABLE session_commits (
    session_id TEXT NOT NULL REFERENCES sessions(id),
    commit_hash TEXT NOT NULL,
    timestamp TIMESTAMP,
    message TEXT,
    PRIMARY KEY (session_id, commit_hash)
);
```

---

## Integration Requirements

### Roadmap System Integration

| ID | Requirement | Priority |
|----|-------------|----------|
| RI-1 | Sessions SHOULD auto-detect active task from roadmap | P1 |
| RI-2 | Task completion SHOULD trigger session event | P1 |
| RI-3 | Session summary SHOULD be visible in task details | P2 |
| RI-4 | Session filter by task/sprint/track | P1 |

### Git Integration

| ID | Requirement | Priority |
|----|-------------|----------|
| GI-1 | Session SHOULD capture git branch at start | P0 |
| GI-2 | Commits during session SHOULD be associated | P0 |
| GI-3 | Session end SHOULD record final commit | P1 |
| GI-4 | Session MAY be associated with PR | P3 |

### MCP Integration

| ID | Requirement | Priority |
|----|-------------|----------|
| MI-1 | MCP tool: `vibey_session_start` | P0 |
| MI-2 | MCP tool: `vibey_session_end` | P0 |
| MI-3 | MCP tool: `vibey_session_log_decision` | P0 |
| MI-4 | MCP tool: `vibey_session_status` | P1 |
| MI-5 | MCP resource: `vibey://sessions/current` | P1 |
| MI-6 | MCP resource: `vibey://sessions/{id}` | P2 |

### CLI Integration

| ID | Requirement | Priority |
|----|-------------|----------|
| CI-1 | CLI command: `vibey session start` | P0 |
| CI-2 | CLI command: `vibey session end` | P0 |
| CI-3 | CLI command: `vibey session status` | P0 |
| CI-4 | CLI command: `vibey session list` | P0 |
| CI-5 | CLI command: `vibey session show <id>` | P1 |
| CI-6 | CLI command: `vibey session export <id>` | P2 |
| CI-7 | CLI command: `vibey decision log` | P1 |

---

## Configuration

### Session Configuration Schema

```yaml
# .vibey/config/sessions.yaml
sessions:
  # Lifecycle settings
  auto_start: true           # Start session on first activity
  auto_end_timeout: 3600     # End session after N seconds of inactivity (0 = never)
  pause_timeout: 1800        # Pause session after N seconds of inactivity

  # Capture settings
  capture:
    context_changes: true    # Track context file changes
    decisions: true          # Enable decision logging
    ai_interactions: false   # Capture AI prompts/responses (privacy)
    terminal_commands: false # Capture terminal commands

  # Storage settings
  storage:
    retention_days: 365      # Keep sessions for N days (0 = forever)
    archive_after_days: 30   # Archive sessions after N days
    max_events_per_session: 10000  # Limit events (0 = unlimited)

  # Privacy settings
  privacy:
    redact_patterns:         # Patterns to redact from captures
      - "password"
      - "secret"
      - "token"
      - "api[_-]?key"
    exclude_files:           # Files to never capture
      - ".env"
      - "*.pem"
      - "credentials.json"

  # Integration settings
  integrations:
    roadmap: true            # Enable roadmap integration
    git: true                # Enable git integration
    mcp: true                # Enable MCP tools
```

---

## User Experience Scenarios

### Scenario 1: Simple Session Flow

```bash
# Start work explicitly
$ vibey session start --goal "Implement user authentication"
Session started: 01KC8ABC...
Associated with task: 01KC7XYZ... (Add user login endpoint)

# ... work happens ...

# Log a decision
$ vibey decision log \
  --description "Use JWT for authentication" \
  --alternative "Session cookies" \
  --rationale "Better for API consumers, stateless"
Decision logged: 01KC8DEF...

# End session
$ vibey session end
Session ended: 01KC8ABC...
Duration: 1h 23m
Commits: 3
Decisions: 1
```

### Scenario 2: Implicit Session with Auto-Detection

```bash
# Session starts automatically on first roadmap interaction
$ vibey task start 01KC7XYZ
Task started: Add user login endpoint
Session auto-started: 01KC8ABC...

# ... work happens, decisions logged via AI ...

# Context window cleared, session continues in background
# Session auto-pauses after 30 minutes of inactivity
# Session auto-ends after 1 hour of inactivity

# Later: review what happened
$ vibey session show 01KC8ABC
Session: 01KC8ABC...
Status: ended (auto)
Duration: 45m
Task: Add user login endpoint
Commits: 2
  - abc123: Add User model
  - def456: Add login endpoint
Decisions: 1
  - Use JWT for authentication (high confidence)
```

### Scenario 3: Session Resume

```bash
# Check for pausable sessions
$ vibey session list --status paused
01KC8ABC... | paused | "Implement caching" | 2h ago

# Resume session
$ vibey session resume 01KC8ABC
Session resumed: 01KC8ABC...
Restoring context...
  - Last task: Add Redis caching layer
  - Last commit: abc123
  - Pending decision: Cache invalidation strategy
```

---

## Open Questions

1. **Session Boundaries with Context Compaction**
   - How do we handle Claude Code's context compaction?
   - Should a session continue across compaction events?
   - How do we track what was lost in compaction?

2. **Multi-Agent Sessions**
   - When subagents are spawned, are they part of the same session?
   - How do we track context that flows to/from subagents?

3. **Branch-Based Sessions**
   - Should sessions be branch-aware?
   - What happens when a session spans branch switches?

4. **Session Merging**
   - Can related sessions be merged?
   - How do we handle parallel work on the same task?

5. **Privacy vs Auditability Trade-off**
   - What's the right default for AI interaction capture?
   - How do we balance team audit needs with individual privacy?

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Session creation success rate | 99.9% | Automated monitoring |
| Decision capture rate | 80% of significant decisions | User survey |
| Session reconstruction success | 90% of sessions reconstructible | Audit sampling |
| User adoption | 50% of sessions explicitly managed | Usage analytics |
| Performance overhead | < 5% of session time | Timing analysis |
| Storage efficiency | < 100KB per typical session | Storage monitoring |

---

## Conclusion

This requirements document defines a comprehensive session tracking system that:

1. **Captures essential context** without imposing workflow friction
2. **Enables decision auditability** through structured logging
3. **Supports session reconstruction** for reproducibility
4. **Integrates with existing systems** (roadmap, git, MCP)
5. **Respects privacy** with configurable capture and redaction

The design follows vibey's established patterns (YAML + SQLite, ULID identifiers, MCP integration) while introducing new capabilities for session-level tracking.

---

## Next Steps

This requirements document informs:
- **Task 4:** Context Versioning Strategy Design
- **Task 5:** Context Retrieval & Selection Design
- **Sprint 3.2:** Implementation of Session Data Model and CLI
