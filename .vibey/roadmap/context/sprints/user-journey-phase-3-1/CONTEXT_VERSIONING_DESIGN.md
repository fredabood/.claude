# Context Versioning Strategy Design

**Sprint:** 3.1 - Context Engineering Research & Landscape
**Task:** 4 - Context Versioning Strategy Design
**Date:** 2025-12-12

---

## Executive Summary

This document designs the strategy for versioning context alongside code changes in vibey. The recommended approach is a **Session-Anchored Versioning** model that creates lightweight context snapshots at session boundaries and commit points, stored using the established YAML + SQLite hybrid pattern.

**Key Design Decisions:**
1. Session-based versioning (not per-commit)
2. Hybrid storage (YAML source of truth, SQLite cache)
3. Git-integrated (tracked in repo, associated with commits)
4. Incremental snapshots (store deltas, not full copies)

---

## Design Goals

| Goal | Priority | Rationale |
|------|----------|-----------|
| **Auditability** | P0 | Must be able to reconstruct what context informed decisions |
| **Git-friendliness** | P0 | Context should be version-controlled alongside code |
| **Low overhead** | P0 | Versioning should not slow down workflow |
| **Reproducibility** | P1 | Must be able to recreate session conditions |
| **Query efficiency** | P1 | Must be able to search/filter context history |
| **Storage efficiency** | P2 | Should not bloat repository significantly |

---

## Design Options

### Option A: Per-Commit Context Snapshots

**Description:** Create a full context snapshot for every git commit, storing the complete state of all context at that point.

**How it works:**
```
commit abc123
├── code changes
└── .vibey/context-snapshots/abc123/
    ├── manifest.yaml        # List of context files
    ├── claude.md.snapshot   # Full copy of CLAUDE.md
    ├── config.snapshot.yaml # Full copy of config
    └── session.snapshot.yaml # Session state at commit
```

**Pros:**
- Simple mental model (1 commit = 1 snapshot)
- Easy to correlate code changes with context
- Complete snapshot enables full reconstruction
- Works with existing git tooling

**Cons:**
- Storage bloat (duplicating context on every commit)
- Many commits may have identical context
- Slow snapshot creation on large contexts
- Merge conflicts in snapshot files

**Implementation Complexity:** Medium

**Storage Impact:** High (~100KB per commit)

---

### Option B: Session-Anchored Versioning (Recommended)

**Description:** Create context snapshots at session boundaries (start/end) and link commits to the active session. Only store incremental changes within a session.

**How it works:**
```
Session 01KC8...
├── start-snapshot.yaml      # Full snapshot at session start
├── events.jsonl             # Incremental changes during session
├── end-snapshot.yaml        # Full snapshot at session end
└── commits: [abc123, def456, ghi789]

Commit abc123 → references Session 01KC8...
```

**Pros:**
- Efficient storage (snapshots only at boundaries)
- Natural alignment with work sessions
- Incremental tracking within sessions
- Reduces duplicate data significantly

**Cons:**
- More complex mental model
- Requires session management
- Mid-session reconstruction requires event replay

**Implementation Complexity:** Medium-High

**Storage Impact:** Low (~10KB per session + ~1KB per event)

---

### Option C: Continuous Context Evolution

**Description:** Track context as a continuous stream of changes, with no explicit snapshots. Reconstruct state at any point by replaying events.

**How it works:**
```
.vibey/context-history/
├── events.jsonl             # All context changes as events
│   ├── {time: T1, type: "file_loaded", file: "CLAUDE.md", hash: "abc"}
│   ├── {time: T2, type: "config_changed", key: "roadmap.backend", value: "sqlite"}
│   ├── {time: T3, type: "session_started", id: "01KC8..."}
│   └── ...
└── index.db                 # SQLite index for fast queries
```

**Pros:**
- Most storage-efficient (only changes stored)
- Fine-grained history available
- No explicit snapshot overhead
- Flexible reconstruction at any point

**Cons:**
- Reconstruction requires full event replay
- Slow reconstruction for distant history
- Complex implementation
- Event log can grow unbounded

**Implementation Complexity:** High

**Storage Impact:** Very Low (events only)

---

### Option D: Git-Native Context Tracking

**Description:** Use git's native mechanisms (branches, tags, notes) to track context without additional files.

**How it works:**
```bash
# Context stored in git notes
git notes --ref=context add -m '{...context json...}' abc123

# Session markers as lightweight tags
git tag session/01KC8.../start abc123
git tag session/01KC8.../end def456

# Context branches for isolation
git branch context/01KC8... # Branch containing only context files
```

**Pros:**
- Uses existing git infrastructure
- No additional file storage
- Native git operations for history
- No merge conflicts (notes are per-commit)

**Cons:**
- Git notes not widely supported in tools
- Complex to query without custom tooling
- Notes not automatically pushed/pulled
- Limited structure in notes

**Implementation Complexity:** Medium

**Storage Impact:** Very Low (git internal storage)

---

## Option Comparison

| Criterion | Option A (Per-Commit) | Option B (Session-Anchored) | Option C (Continuous) | Option D (Git-Native) |
|-----------|----------------------|----------------------------|----------------------|----------------------|
| **Storage Efficiency** | Poor | Good | Excellent | Excellent |
| **Query Speed** | Good | Good | Poor (replay needed) | Poor (needs tooling) |
| **Reconstruction** | Trivial | Easy | Complex | Medium |
| **Git Integration** | Native | Good | Moderate | Excellent |
| **Implementation** | Medium | Medium-High | High | Medium |
| **Mental Model** | Simple | Moderate | Complex | Moderate |
| **Merge Conflicts** | High risk | Low risk | No risk | No risk |

---

## Recommended Approach: Session-Anchored Versioning (Option B)

### Rationale

1. **Aligns with session concept** established in requirements
2. **Balances storage and queryability** - not too much data, not too complex
3. **Matches existing patterns** - similar to roadmap system's YAML + SQLite
4. **Practical reconstruction** - can rebuild context for any session
5. **Git-friendly** - YAML files are human-readable and merge cleanly

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Context Versioning System                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐     ┌─────────────────┐                   │
│  │  Session Start  │────►│  Start Snapshot │                   │
│  └─────────────────┘     └─────────────────┘                   │
│          │                       │                              │
│          ▼                       ▼                              │
│  ┌─────────────────┐     ┌─────────────────┐                   │
│  │  Work Activity  │────►│  Event Stream   │                   │
│  │  - Code edits   │     │  - Context Δ    │                   │
│  │  - Commits      │     │  - Decisions    │                   │
│  │  - Decisions    │     │  - Commits      │                   │
│  └─────────────────┘     └─────────────────┘                   │
│          │                       │                              │
│          ▼                       ▼                              │
│  ┌─────────────────┐     ┌─────────────────┐                   │
│  │  Session End    │────►│  End Snapshot   │                   │
│  └─────────────────┘     └─────────────────┘                   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    SQLite Index                          │   │
│  │  - Session metadata    - Commit associations            │   │
│  │  - Event index         - Context file index             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Design

### What to Version

#### Always Versioned (Automatic)

| Source | Version Trigger | Storage Method |
|--------|-----------------|----------------|
| Session metadata | Session start/end | Full snapshot |
| Git state | Session start/end, each commit | Snapshot + events |
| Active roadmap items | Session start/end | Reference by ID |
| Configuration hashes | Session start/end | Hash + summary |

#### Versioned on Change (Tracked)

| Source | Version Trigger | Storage Method |
|--------|-----------------|----------------|
| CLAUDE.md | Content change detected | Hash + diff |
| Config files | Content change detected | Hash + diff |
| Sprint context files | File access during session | Hash + path |
| MCP tool calls | Each call | Event log |

#### Optionally Versioned (Configurable)

| Source | Default | Storage Method |
|--------|---------|----------------|
| AI prompts | OFF | Full text in events |
| AI responses | OFF | Full text in events |
| Terminal commands | OFF | Command + exit code |
| File contents accessed | OFF | Hash only |

### Snapshot Structure

```yaml
# .vibey/sessions/01KC8.../snapshots/start.yaml
snapshot:
  id: "01KC8SNP..."
  session_id: "01KC8..."
  type: "session_start"
  timestamp: "2025-12-12T10:00:00Z"

  # Context file state
  context_files:
    - path: "CLAUDE.md"
      hash: "sha256:abc..."
      size: 15234
      modified: "2025-12-11T15:30:00Z"

    - path: ".vibey/config/roadmap.yaml"
      hash: "sha256:def..."
      size: 1024
      modified: "2025-12-10T09:00:00Z"

  # Configuration summary (not full content)
  config_state:
    vibey_version: "2.5.0"
    backend: "sqlite"
    tracks_count: 41
    active_track: "user-journey-audit"
    active_sprint: "phase-3-1"
    active_task: "task-004"

  # Git state
  git_state:
    branch: "main"
    commit: "abc123def..."
    dirty: true
    staged:
      - "vibey/roadmap/models/session.py"
    modified:
      - "docs/SESSION_DESIGN.md"
    untracked:
      - "scratch.py"

  # Environment state
  environment:
    python: "3.11.0"
    os: "darwin"
    shell: "zsh"
    cwd: "/Users/fred/repos/vibey"

  # Roadmap context
  roadmap_context:
    track:
      id: "01KC..."
      name: "user-journey-audit"
      status: "in_progress"
    sprint:
      id: "01KC..."
      name: "Phase 3.1: Context Engineering Research"
      status: "in_progress"
    task:
      id: "01KC..."
      title: "Context Versioning Strategy Design"
      status: "in_progress"
```

### Event Stream Structure

```jsonl
{"id":"01KC8E01...","ts":"2025-12-12T10:00:15Z","type":"context_loaded","data":{"file":"CLAUDE.md","hash":"sha256:abc..."}}
{"id":"01KC8E02...","ts":"2025-12-12T10:05:30Z","type":"file_modified","data":{"file":"session.py","action":"created"}}
{"id":"01KC8E03...","ts":"2025-12-12T10:10:45Z","type":"decision_made","data":{"id":"01KC8D01...","summary":"Use YAML+SQLite hybrid"}}
{"id":"01KC8E04...","ts":"2025-12-12T10:15:00Z","type":"commit_made","data":{"hash":"def456...","message":"Add session model"}}
{"id":"01KC8E05...","ts":"2025-12-12T10:20:30Z","type":"task_completed","data":{"task_id":"01KC...","title":"Design session model"}}
```

### Commit Association

```yaml
# .vibey/sessions/01KC8.../commits.yaml
commits:
  - hash: "abc123def456789..."
    short: "abc123d"
    timestamp: "2025-12-12T10:15:00Z"
    message: "Add session model"
    author: "Fred <fred@example.com>"
    files_changed: 3
    insertions: 150
    deletions: 10
    context_snapshot: "01KC8SNP02..."  # Optional mid-session snapshot

  - hash: "def456ghi789012..."
    short: "def456g"
    timestamp: "2025-12-12T10:30:00Z"
    message: "Add session CLI commands"
    author: "Fred <fred@example.com>"
    files_changed: 2
    insertions: 80
    deletions: 5
```

---

## Git Integration Strategy

### Tracked vs Ignored Files

**Tracked in Git:**
- `sessions/*/session.yaml` - Session metadata
- `sessions/*/decisions.yaml` - Decision log
- `sessions/*/snapshots/*.yaml` - Snapshots
- `sessions/index.yaml` - Session index

**Ignored (in .gitignore):**
- `sessions/*/events.jsonl` - High-volume event log
- `sessions.db` - SQLite cache
- `sessions/*/ai-interactions/` - Optional AI capture

### Commit Hooks Integration

```bash
# post-commit hook
#!/bin/bash
# Record commit in active session if one exists
vibey session record-commit "$GIT_COMMIT_HASH"
```

### Branch-Aware Sessions

- Sessions track the branch they started on
- Branch switches during a session are recorded as events
- Sessions can span branches but are warned about

```yaml
# Event when branch changes
{"type": "branch_changed", "from": "main", "to": "feature/sessions"}
```

---

## Storage Format Details

### YAML for Human-Readable Data

- Session metadata
- Snapshots
- Decisions
- Commit associations

**Rationale:** Git-friendly diffs, human review, manual editing possible

### JSONL for Event Streams

- High-volume events
- Append-only pattern
- One event per line

**Rationale:** Efficient append, easy streaming, line-based processing

### SQLite for Query Cache

- Fast session lookup
- Full-text search on decisions
- Aggregate statistics

**Rationale:** Query performance, complex searches, reporting

---

## Diff & Merge Strategy

### Snapshot Diffs

Snapshots are designed to be diffable:

```diff
 context_files:
   - path: "CLAUDE.md"
-    hash: "sha256:abc..."
+    hash: "sha256:xyz..."
     size: 15234
-    modified: "2025-12-11T15:30:00Z"
+    modified: "2025-12-12T10:00:00Z"
```

### Merge Conflict Resolution

| File Type | Merge Strategy |
|-----------|----------------|
| `session.yaml` | Manual (session metadata shouldn't conflict) |
| `snapshots/*.yaml` | Auto-merge (independent snapshots) |
| `decisions.yaml` | Concatenate (decisions are additive) |
| `commits.yaml` | Concatenate (commits are additive) |
| `events.jsonl` | Ignored (not in git) |

### Session Index Merging

The index file (`sessions/index.yaml`) may conflict if multiple sessions are created on different branches:

```yaml
# Merge strategy: combine sessions from both branches
sessions:
  # From branch A
  - id: "01KC8..."
    ...
  # From branch B
  - id: "01KC9..."
    ...
```

---

## Context Reconstruction

### Full Session Reconstruction

```python
def reconstruct_session(session_id: str, point_in_time: datetime = None) -> SessionContext:
    """Reconstruct session context at a point in time."""
    session = load_session(session_id)

    # Start with session start snapshot
    context = load_snapshot(session.start_snapshot_id)

    if point_in_time is None:
        # Return end state
        return load_snapshot(session.end_snapshot_id)

    # Replay events up to point_in_time
    for event in session.events:
        if event.timestamp > point_in_time:
            break
        context = apply_event(context, event)

    return context
```

### Partial Reconstruction (Commit-Based)

```python
def context_at_commit(commit_hash: str) -> SessionContext:
    """Get context that was active when a commit was made."""
    # Find session containing commit
    session = find_session_for_commit(commit_hash)
    if not session:
        return None

    # Find commit timestamp
    commit_time = get_commit_timestamp(commit_hash)

    # Reconstruct to that point
    return reconstruct_session(session.id, commit_time)
```

---

## Configuration

```yaml
# .vibey/config/sessions.yaml
versioning:
  # Snapshot settings
  snapshots:
    on_session_start: true
    on_session_end: true
    on_commit: false           # Mid-session snapshots at commits
    interval_minutes: 0        # Periodic snapshots (0 = disabled)

  # What to include in snapshots
  capture:
    context_files: true        # CLAUDE.md, config files
    git_state: true            # Branch, commit, dirty state
    environment: true          # Python version, OS, etc.
    roadmap_context: true      # Active track/sprint/task

  # Event tracking
  events:
    context_changes: true      # File loads, config changes
    decisions: true            # Decision events
    commits: true              # Git commit events
    ai_interactions: false     # Prompts and responses

  # Storage limits
  limits:
    max_events_per_session: 10000
    max_snapshot_size_kb: 500
    events_retention_days: 90  # JSONL files only
```

---

## Migration Strategy

### For Existing Projects

1. Initialize session tracking (`vibey session init`)
2. Create baseline snapshot of current state
3. Begin tracking from next session
4. No historical reconstruction (future-only)

### For New Projects

1. Session tracking enabled by default
2. First session starts on first `vibey` command
3. Full tracking from project inception

---

## Open Questions

1. **Snapshot Compression**
   - Should snapshots be compressed for storage?
   - Trade-off: storage vs. git-friendliness

2. **Event Stream Rotation**
   - How to handle very long sessions with many events?
   - Should events be rotated/archived?

3. **Cross-Repository Context**
   - How to handle context from external repositories?
   - Store hashes only, or cache content?

4. **Stale Context Detection**
   - How to detect when snapshotted context is outdated?
   - Automatic re-snapshot triggers?

---

## Implementation Sketch

### Phase 1: Core Versioning (Sprint 3.2)

1. Implement Snapshot model and serialization
2. Implement Event model and JSONL logging
3. Add snapshot creation at session start/end
4. Add commit recording in sessions

### Phase 2: Git Integration (Sprint 3.2)

1. Add post-commit hook for commit recording
2. Implement commit-to-session association
3. Add snapshot diffing utilities

### Phase 3: Reconstruction (Sprint 3.3)

1. Implement session reconstruction algorithm
2. Add context-at-commit queries
3. Build reconstruction validation tests

### Phase 4: Advanced Features (Future)

1. Periodic auto-snapshots
2. Snapshot compression
3. Event stream rotation
4. Cross-repository context

---

## Success Criteria

| Criterion | Measurement |
|-----------|-------------|
| Storage overhead < 100KB per session | Measure average session size |
| Snapshot creation < 500ms | Performance benchmarks |
| Full reconstruction < 2s | Performance benchmarks |
| Zero merge conflicts in normal usage | Track conflict reports |
| 100% commit association accuracy | Audit sampling |

---

## Conclusion

Session-Anchored Versioning provides the best balance of:
- **Efficiency:** Snapshots only at boundaries, events for details
- **Auditability:** Full reconstruction capability
- **Git integration:** Human-readable files, clean merges
- **Practicality:** Aligns with existing vibey patterns

This design enables vibey users to answer:
- "What context did the AI have when it made this change?"
- "What decisions were made in this session and why?"
- "Can I recreate the conditions of this past session?"

---

## References

- Task 1: Context Engineering Landscape Research
- Task 2: Current Context State Audit
- Task 3: Session Context Requirements
- Vibey Roadmap System Architecture
