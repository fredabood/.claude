# Vibey Architecture Overview

> A user-friendly guide to how Vibey works

---

## What is Vibey?

Vibey is a **roadmap management framework** designed for AI-assisted software development. It helps teams:

- **Track development work** through a structured hierarchy of tracks, sprints, and tasks
- **Integrate with AI assistants** via the Model Context Protocol (MCP)
- **Deploy configurations** to 9 different AI coding platforms
- **Maintain visibility** into project progress across all work streams

### What Problems Does Vibey Solve?

| Problem | Vibey Solution |
|---------|----------------|
| "What should I work on?" | Task management with status tracking |
| "What's our progress?" | Automatic progress computation |
| "How do I tell Claude about my project?" | MCP server with 76 tools |
| "How do I deploy to Cursor/Copilot/etc?" | Platform adapters |
| "Who changed what, when?" | Activity logging and audit trail |

---

## Core Concepts

### The Unified Ticket Model

Vibey organizes work in a three-level hierarchy:

```
                    ┌─────────────────────────────────────┐
                    │              TRACK                   │
                    │   "Platform Compatibility Refactor"  │
                    │        Status: in_progress           │
                    │      Progress: 8/20 tasks (40%)      │
                    └─────────────────────────────────────┘
                                      │
           ┌──────────────────────────┼──────────────────────────┐
           ▼                          ▼                          ▼
┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
│      SPRINT        │   │      SPRINT        │   │      SPRINT        │
│  "Core Refactor"   │   │  "Adapter Updates" │   │  "Testing Phase"   │
│ Status: completed  │   │ Status: in_progress│   │ Status: not_started│
│   5/5 tasks (100%) │   │   3/8 tasks (38%)  │   │   0/7 tasks (0%)   │
└────────────────────┘   └────────────────────┘   └────────────────────┘
           │                        │
     ┌─────┴─────┐           ┌─────┼─────┐
     ▼           ▼           ▼     ▼     ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ... (tasks)
│  TASK   │ │  TASK   │ │  TASK   │
│completed│ │completed│ │in_progress│
└─────────┘ └─────────┘ └─────────┘
```

#### Tracks

A **track** is a major project theme or work stream. Examples:
- "SQLite Backend Implementation"
- "Documentation Quality Improvements"
- "Platform Compatibility"

Tracks contain multiple sprints and span weeks to months.

#### Sprints

A **sprint** is a focused work period within a track. Examples:
- "Sprint 1: Architecture Design"
- "Sprint 2: Core Implementation"
- "Sprint 3: Testing & Validation"

Sprints contain tasks and typically span days to weeks.

#### Tasks

A **task** is an individual work item with clear deliverables. Examples:
- "Create database schema"
- "Write unit tests for loader"
- "Update CLI help text"

Tasks are the smallest trackable unit of work.

---

### Status Flow

Status changes flow from the bottom up:

```
TASK completes → SPRINT progress updates → TRACK progress updates
```

#### Task Statuses

| Status | Meaning | CLI Command |
|--------|---------|-------------|
| `not_started` | Task hasn't begun | (default) |
| `in_progress` | Currently being worked on | `vibey roadmap start <id>` |
| `completed` | Work is done | `vibey roadmap complete <id>` |
| `blocked` | Waiting on dependencies | Set via `vibey roadmap update` |

#### Progress Computation

Progress is computed automatically, never stored manually:

```
Sprint Progress = (completed tasks / total tasks) × 100%
Track Progress = (completed sprints / total sprints) × 100%
```

When you complete a task, the sprint and track progress update automatically.

---

### Identifiers (ULIDs)

Every track, sprint, and task has a unique identifier:

```
01KC2D0JK7READW9KAK1HBX4B8
└──────┬──────┘└────┬────┘
   Timestamp     Random
   (sortable)   (unique)
```

**Why ULIDs?**
- **Time-sortable**: Older items sort before newer ones
- **Unique**: No collisions even without a central database
- **URL-safe**: No special characters, works in filenames
- **26 characters**: Short enough for CLI use

**Example usage:**
```bash
# Show task details by ID
vibey roadmap show 01KC2D0JK7READW9KAK1HBX4B8

# Start a task
vibey roadmap start 01KC2D0JK7READW9KAK1HBX4B8
```

You don't need to memorize IDs. Use `vibey roadmap list tasks` to see them, or use tab-completion in your shell.

---

## Data Storage

### Dual Storage: YAML + SQLite

Vibey maintains your roadmap data in **two formats**:

```
.vibey/roadmap/
├── tracks/               # YAML files (source of truth)
├── sprints/              # Human-readable, git-friendly
├── tasks/                # Edit with any text editor
└── roadmap.db           # SQLite database (query cache)
```

#### Why Two Formats?

| Purpose | YAML | SQLite |
|---------|------|--------|
| **Version control** | Git diffs, merge, history | Binary, poor diffs |
| **Human editing** | Easy to read and edit | Need SQL or tools |
| **Complex queries** | Must load all files | Instant with indexes |
| **Collaboration** | Merge-friendly | Conflict-prone |
| **Speed** | Slower for queries | Very fast |

**The key insight:** YAML is the **source of truth** (what you commit to git). SQLite is a **regenerable cache** (speeds up queries).

#### When to Use Each

| Scenario | What Happens |
|----------|--------------|
| Normal CLI usage | Both update automatically |
| Edit YAML directly | Run `vibey roadmap db rebuild` |
| Database errors | Delete `.vibey/roadmap/roadmap.db` and rebuild |
| Sharing with team | Only YAML files are committed to git |

#### Common Commands

```bash
# Check if database is in sync
vibey roadmap db status

# Rebuild database from YAML (safe to run anytime)
vibey roadmap db rebuild

# Validate database integrity
vibey roadmap db validate

# Optimize database size
vibey roadmap db vacuum
```

---

### Directory Structure

Vibey uses a **flat directory structure** for performance:

```
.vibey/roadmap/
├── tracks/
│   ├── 01KC2D0JK9JKQXGQW6MQEB0JZP.yaml
│   └── 01KC39XSXJ39N12HWJ93F77KQ9.yaml
├── sprints/
│   ├── 01KC2D0JKVT80AFQ6C1PA8CKJD.yaml
│   └── 01KC4P55YG0C05YSWXR2YCS3C4.yaml
├── tasks/
│   ├── 01KC2D0JK7READW9KAK1HBX4B8.yaml
│   └── 01KC4P92GRAHA428M96MTXWP5T.yaml
├── context/              # Supporting documentation
│   └── tracks/...
└── roadmap.db           # SQLite cache
```

**Why flat?**
- Fast git operations (no deep traversal)
- Simple file lookup (just `tasks/{id}.yaml`)
- Easy to rename things (change content, not paths)

**Relationships** are stored in file contents, not paths:
```yaml
task:
  id: 01KC2D0JK7READW9KAK1HBX4B8
  sprint_id: 01KC2D0JKVT80AFQ6C1PA8CKJD   # ← parent sprint
  track_id: 01KC2D0JK9JKQXGQW6MQEB0JZP    # ← parent track
  title: "Create database schema"
```

---

## Interfaces

### CLI vs MCP: When to Use Which

Vibey provides two interfaces:

| Interface | Use When | Best For |
|-----------|----------|----------|
| **CLI** | Terminal, scripts, automation | Human operators |
| **MCP** | AI assistants, programmatic access | Claude, Cursor, etc. |

#### CLI Examples

```bash
# Check overall status
vibey roadmap status

# Start working on a task
vibey roadmap start 01KC2D0JK7READW9KAK1HBX4B8

# Complete a task
vibey roadmap complete 01KC2D0JK7READW9KAK1HBX4B8

# List all tasks in a sprint
vibey roadmap list tasks --sprint 01KC2D0JKVT80AFQ6C1PA8CKJD
```

#### MCP Tool Examples

When using Claude or another AI assistant:

```
"Start task 01KC2D0JK7READW9KAK1HBX4B8"
→ Calls vibey_start_task MCP tool

"What's the status of the Documentation Quality track?"
→ Calls vibey_query_track MCP tool
```

#### Operation Mapping

| Operation | CLI Command | MCP Tool |
|-----------|-------------|----------|
| Get status | `vibey roadmap status` | `roadmap_status` |
| Start task | `vibey roadmap start <id>` | `task_start` |
| Complete task | `vibey roadmap complete <id>` | `task_complete` |
| Query task | `vibey roadmap show <id>` | `task_query` |
| List sprints | `vibey roadmap list sprints` | `sprint_list` |
| Deploy config | `vibey deploy run --platform X` | N/A (CLI only) |

---

## Platform Deployment

Vibey can deploy configurations to 9 AI coding platforms:

| Platform | Adapter | Command |
|----------|---------|---------|
| Claude Code | `claude` | `vibey deploy run --platform claude` |
| Cursor | `cursor` | `vibey deploy run --platform cursor` |
| VS Code Copilot | `copilot` | `vibey deploy run --platform copilot` |
| Continue | `continue` | `vibey deploy run --platform continue` |
| Windsurf | `windsurf` | `vibey deploy run --platform windsurf` |
| Goose | `goose` | `vibey deploy run --platform goose` |
| Aider | `aider` | `vibey deploy run --platform aider` |
| Gemini | `gemini` | `vibey deploy run --platform gemini` |
| Replit | `replit` | `vibey deploy run --platform replit` |

Each adapter generates platform-specific configuration files.

---

## Activity & Audit

### Activity Logging

Vibey tracks what happens to your roadmap:

```bash
# View recent activity
vibey roadmap activity --limit 10

# Output:
# 2024-12-16 10:30:15  task_completed  01KC2D0JK7READW9KAK1HBX4B8
# 2024-12-16 10:25:02  task_started    01KC2D0JK7READW9KAK1HBX4B8
# 2024-12-16 09:15:33  sprint_started  01KC2D0JKVT80AFQ6C1PA8CKJD
```

### What Gets Logged

| Event | When Logged |
|-------|-------------|
| Task started | `vibey roadmap start` |
| Task completed | `vibey roadmap complete` |
| Sprint started | First task in sprint started |
| Sprint completed | All tasks completed |
| Manual changes | Any `vibey roadmap update` |

---

## Further Reading

### Architectural Decision Records (ADRs)

For the technical reasoning behind design choices:

| ADR | Topic |
|-----|-------|
| [ADR-0001](adr/0001-ulid-identifiers.md) | Why ULIDs for identifiers |
| [ADR-0002](adr/0002-flat-directory-structure.md) | Why flat directories |
| [ADR-0003](adr/0003-dual-storage-sqlite-yaml.md) | Why YAML + SQLite |
| [ADR-0004](adr/0004-click-cli-framework.md) | Why Click for CLI |
| [ADR-0005](adr/0005-mcp-integration.md) | Why MCP protocol |

### Reference Documentation

| Document | Content |
|----------|---------|
| [CLI Reference](../reference/CLI_REFERENCE.md) | All 200 commands |
| [MCP Reference](../reference/MCP_REFERENCE.md) | All 76 tools |
| [CLAUDE.md](../../CLAUDE.md) | Repository context |

### User Guides

| Guide | For |
|-------|-----|
| [Getting Started](../walkthroughs/WALKTHROUGH_NEW_USER.md) | First-time users |
| [Daily Workflow](../walkthroughs/WALKTHROUGH_ACTIVE_DEVELOPER.md) | Regular development |
| [Project Setup](../guides/ROADMAP_TUTORIAL.md) | Creating roadmaps |
