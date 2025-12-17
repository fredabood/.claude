# Roadmap System Reference

> **Note:** This document references historical `/vibey` slash commands in task names. The slash command interface was removed in v2.5.0. Use `vibey` CLI commands instead. See [CLI_REFERENCE.md](./CLI_REFERENCE.md).

**Version:** 1.0.0
**Last Updated:** November 8, 2025
**Framework Version:** Vibey v1.3.0+

---

## Overview

The Vibey Roadmap System is an advanced multi-sprint state management framework that enables hierarchical project planning, cross-sprint dependencies, agent workload balancing, and intelligent task recommendations.

**Key Capabilities:**
- Multi-sprint planning across tracks
- Cross-sprint dependency management
- Automatic blocker detection
- Agent workload balancing
- Task recommendations
- Quality gates (track/sprint/task levels)
- Activity logging and analytics
- Performance caching

**Architecture:**
```
Roadmap
  ├── Tracks (strategic groupings)
  │     ├── Sprints (time-boxed work periods)
  │     │     ├── Tasks (atomic work units)
  │     │     └── Quality Gates
  │     └── Dependencies
  └── Metadata
```

---

## Table of Contents

1. [Object Hierarchy](#object-hierarchy)
2. [File Structure](#file-structure)
3. [CLI Commands](#cli-commands)
4. [YAML Schemas](#yaml-schemas)
5. [State Transitions](#state-transitions)
6. [Dependencies & Blockers](#dependencies--blockers)
7. [Quality Gates](#quality-gates)
8. [Performance & Caching](#performance--caching)
9. [Best Practices](#best-practices)
10. [API Reference](#api-reference)

---

## Object Hierarchy

### 1. Roadmap (Top Level)

**Purpose:** Top-level container for entire project roadmap

**Key Fields:**
- `id` - Unique roadmap identifier
- `name` - Human-readable name
- `status` - Overall roadmap status
- `tracks` - List of track IDs
- `metadata` - Version, creation info

**Location:** `.vibey/roadmap.yaml`

**Example:**
```yaml
roadmap:
  id: vibey-framework-v2
  name: Vibey Framework V2 Roadmap
  status: in_progress
  tracks:
    - roadmap-integration
    - core-framework
    - goose-port
```

### 2. Track (Strategic Grouping)

**Purpose:** Groups related sprints with shared strategic goal

**Key Fields:**
- `id` - Unique track identifier
- `name` - Track name
- `roadmap_id` - Parent roadmap
- `sprints` - List of sprint summaries
- `progress` - Aggregate progress across sprints
- `dependencies` - Cross-track dependencies
- `quality_gates` - Track-level gates

**Location:** `.vibey/tracks/<track-id>.yaml`

**Example:**
```yaml
track:
  id: roadmap-integration
  name: Roadmap Integration into /vibey Commands
  status: in_progress
  progress:
    sprints_total: 3
    sprints_completed: 2
    completion_percent: 67
  sprints:
    - id: roadmap-integration-1
      name: Foundation & Sprint Planning
      status: production_ready
```

### 3. Sprint (Time-Boxed Work Period)

**Purpose:** Concrete work unit with tasks and deliverables

**Key Fields:**
- `id` - Unique sprint identifier
- `name` - Sprint name
- `track_id` - Parent track
- `status` - Current sprint status
- `tasks` - List of task IDs (references)
- `progress` - Task completion metrics
- `quality_gates` - Sprint-level gates
- `plan_file` - Link to sprint plan markdown

**Location:** `.vibey/sprints/<sprint-id>.yaml`

**Example:**
```yaml
sprint:
  id: roadmap-integration-2
  name: Progress Tracking & Vibey Manager
  track_id: roadmap-integration
  status: production_ready
  progress:
    tasks_total: 6
    tasks_completed: 6
    completion_percent: 100
  quality_gates:
    - name: Unit Testing
      threshold: 80
      status: passed
```

### 4. Task (Atomic Work Unit)

**Purpose:** Individual piece of work with owner and status

**Key Fields:**
- `id` - Unique task identifier
- `sprint_id` - Parent sprint
- `title` - Task name
- `status` - Current task status
- `assigned_agents` - List of responsible agents
- `estimated_hours` - Time estimate
- `depends_on` - Task dependencies
- `blocked_by` - Blocking tasks

**Location:** `.vibey/tasks/<sprint-id>-tasks.yaml`

**Example:**
```yaml
tasks:
  - id: roadmap-integration-2-task-001
    sprint_id: roadmap-integration-2
    title: Update /vibey code dashboard
    status: completed
    priority: high
    estimated_hours: 6
    assigned_agents:
      - web-developer
```

---

## File Structure

### Directory Layout

```
.vibey/
├── roadmap.yaml                    # Top-level roadmap
├── ai-reference.md                 # Quick reference for AI assistants
├── tracks/
│   ├── core-framework.yaml         # Track definitions
│   ├── roadmap-integration.yaml
│   └── goose-port.yaml
├── sprints/
│   ├── roadmap-integration-1.yaml  # Sprint details
│   ├── roadmap-integration-2.yaml
│   └── core-framework-1.yaml
├── tasks/
│   ├── roadmap-integration-1-tasks.yaml  # Task lists
│   ├── roadmap-integration-2-tasks.yaml
│   └── core-framework-1-tasks.yaml
├── sprint_summaries/               # Completion summaries
│   ├── roadmap-integration-1-COMPLETED.md
│   └── roadmap-integration-2-COMPLETED.md
└── track_summaries/                # Track summaries
    └── roadmap-integration-COMPLETED.md
```

### File Naming Conventions

**Tracks:** `<track-id>.yaml`
- Example: `roadmap-integration.yaml`

**Sprints:** `<sprint-id>.yaml`
- Example: `roadmap-integration-2.yaml`

**Tasks:** `<sprint-id>-tasks.yaml`
- Example: `roadmap-integration-2-tasks.yaml`

**Summaries:** `<sprint-id>-COMPLETED.md`
- Example: `roadmap-integration-2-COMPLETED.md`

---

## CLI Commands

### Unified `roadmap` CLI

All roadmap operations use the unified `roadmap` command:

```bash
python3 .claude/scripts/roadmap <subcommand> [options]
```

### Core Commands

#### 1. Initialize Roadmap

```bash
roadmap init --id <project-id> --name "Project Name"
```

**Purpose:** Initialize `.vibey/` structure

**Output:**
- Creates `.vibey/` directory
- Generates `roadmap.yaml`
- Creates subdirectories (tracks, sprints, tasks)

#### 2. View Status

```bash
roadmap status [--json]
```

**Purpose:** Show overall roadmap status

**Output:**
```
📊 Roadmap Status: vibey-framework-v2

📈 Overall Progress: 67% complete

🎯 Tracks (3):
- ✅ roadmap-integration: 2/3 sprints (67%)
- 🔄 core-framework: 1/3 sprints (33%)
- ⏸️  goose-port: 0/3 sprints (0%)
```

#### 3. Show Details

```bash
roadmap show <object-id> [--json]
```

**Purpose:** Display detailed information about any object

**Examples:**
```bash
# Show sprint
roadmap show roadmap-integration-2

# Show track
roadmap show roadmap-integration

# JSON output
roadmap show roadmap-integration-2 --json
```

#### 4. List Objects

```bash
roadmap list {tracks|sprints|tasks} [--json]
```

**Purpose:** List all objects of a type

**Examples:**
```bash
# List all tracks
roadmap list tracks

# List all sprints
roadmap list sprints

# List tasks (with filtering)
roadmap list tasks --status in_progress
roadmap list tasks --sprint roadmap-integration-2
```

### Task Management Commands

#### 5. Start Task

```bash
roadmap start <task-id>
```

**Purpose:** Mark task as in-progress

**Effects:**
- Updates task status to `in_progress`
- Sets `started` timestamp
- Updates sprint progress
- Triggers progress recalculation

#### 6. Complete Task

```bash
roadmap complete <task-id>
```

**Purpose:** Mark task as completed

**Effects:**
- Updates task status to `completed`
- Sets `completed` timestamp
- Updates sprint progress
- Checks for sprint completion

#### 7. Block Task

```bash
roadmap block <task-id> --reason "Reason for block"
```

**Purpose:** Mark task as blocked

**Effects:**
- Updates task status to `blocked`
- Records blocker reason
- Updates dependency graph
- Triggers blocker detection

### Analysis Commands

#### 8. Dependencies

```bash
roadmap deps [<object-id>] [--blockers] [--dependents]
```

**Purpose:** Show dependency graph

**Examples:**
```bash
# Show all dependencies
roadmap deps

# Show dependencies for specific sprint
roadmap deps roadmap-integration-2

# Show only blockers
roadmap deps --blockers

# Show what depends on this
roadmap deps roadmap-integration-1 --dependents
```

#### 9. Recommendations

```bash
roadmap recommend [--agent <agent-id>] [--limit <n>]
```

**Purpose:** Get task recommendations

**Examples:**
```bash
# Get top 5 recommended tasks
roadmap recommend --limit 5

# Get tasks for specific agent
roadmap recommend --agent web-developer

# JSON output for scripting
roadmap recommend --json
```

#### 10. Validate

```bash
roadmap validate [--fix]
```

**Purpose:** Validate roadmap structure

**Checks:**
- YAML validity
- ID uniqueness
- Cross-references
- Circular dependencies
- Orphaned objects

**Output:**
```
✅ Roadmap Validation Complete

Structure:
✓ All YAML files valid
✓ All IDs unique
✓ All cross-references valid

Dependencies:
✓ No circular dependencies
✓ All dependency IDs exist

Summary: Roadmap is valid
```

### Quality Gate Commands

#### 11. Update Gate

```bash
roadmap gate update <sprint-id> <gate-name> --status <status> --score <score>
```

**Purpose:** Update quality gate status

**Example:**
```bash
roadmap gate update roadmap-integration-2 "Unit Testing" \
  --status passed \
  --score 95
```

### Utility Commands

#### 12. Search

```bash
roadmap find <query> [--type {track|sprint|task}]
```

**Purpose:** Search across all objects

**Example:**
```bash
# Search for "authentication"
roadmap find authentication

# Search only in tasks
roadmap find authentication --type task
```

#### 13. Cache Management

```bash
roadmap cache clear
roadmap cache stats
```

**Purpose:** Manage performance cache

---

## YAML Schemas

### Roadmap Schema

```yaml
roadmap:
  id: string                    # Required, unique
  name: string                  # Required
  status: enum                  # in_progress, completed, paused
  created: datetime             # ISO 8601 format
  tracks: list[string]          # List of track IDs
  metadata:
    version: string             # Semantic version
    created_by: string
    last_updated: datetime
```

### Track Schema

```yaml
track:
  id: string                    # Required, unique
  name: string                  # Required
  roadmap_id: string            # Parent roadmap ID
  status: enum                  # not_started, in_progress, completed, blocked
  blocked: boolean
  priority: enum                # low, medium, high, critical
  created: datetime
  started: datetime|null
  completed: datetime|null
  estimated_duration: string    # e.g., "6 weeks"

  progress:
    sprints_total: int
    sprints_completed: int
    tasks_total: int
    tasks_completed: int
    completion_percent: int     # 0-100

  sprints: list[object]         # Sprint summaries
    - id: string
      name: string
      status: enum
      estimated_duration: string
      tasks_count: int
      started: datetime|null

  dependencies: list[string]    # IDs this track needs
  blocks: list[string]          # IDs this track blocks
  blocked_by: list[string]      # IDs blocking this track
  depends_on: list[string]      # IDs this depends on
  depended_on_by: list[string]  # IDs depending on this

  quality_gates: list[object]
    - name: string
      threshold: int            # 0-100
      blocking: boolean
      status: enum              # not_run, passed, failed
      score: int|null

  assigned_agents: list[string]
  deliverables: list[string]
  strategic_value: list[string]

  metadata:
    created_by: string
    last_updated: datetime
    design_doc: string|null
    implementation_plan: string|null
    notes: string|null
```

### Sprint Schema

```yaml
sprint:
  id: string                    # Required, unique
  name: string                  # Required
  track_id: string              # Parent track ID
  roadmap_id: string            # Parent roadmap ID
  status: enum                  # not_started, in_progress, completed, production_ready
  blocked: boolean
  created: datetime
  started: datetime|null
  completed: datetime|null
  completion_gate_check_at: datetime|null
  production_gate_check_at: datetime|null
  production_ready_at: datetime|null
  deployed_at: datetime|null

  progress:
    development_tasks_total: int
    development_tasks_completed: int
    completion_gate_tasks_total: int
    completion_gate_tasks_completed: int
    production_gate_tasks_total: int
    production_gate_tasks_completed: int
    tasks_total: int
    tasks_completed: int
    completion_percent: int

  tasks: list[string]           # Task IDs (references)
  development_gates: list[object]
  quality_gates: list[object]   # Same schema as track gates

  blocks: list[string]
  blocked_by: list[string]
  depends_on: list[string]
  depended_on_by: list[string]

  plan_file: string             # Path to markdown plan
  deliverables: list[string]

  metadata:
    last_updated: datetime
    estimated_duration: string
    actual_duration: string|null
    estimated_tokens: int|null
    actual_tokens: int|null
    agents_used: list[string]|null
```

### Task Schema

```yaml
tasks:
  - id: string                  # Required, unique
    sprint_id: string           # Parent sprint ID
    title: string               # Required
    description: string
    status: enum                # not_started, in_progress, completed, blocked
    priority: enum              # low, medium, high, critical
    estimated_hours: float|null
    actual_hours: float|null
    assigned_agents: list[string]
    depends_on: list[string]    # Task IDs
    blocked_by: list[string]    # Task IDs
    tags: list[string]
    created: datetime
    started: datetime|null
    completed: datetime|null
    metadata: object|null
```

---

## State Transitions

### Sprint Status Flow

```
not_started
    ↓ (start sprint)
in_progress
    ↓ (all dev tasks complete)
completion_gate_check
    ↓ (gates pass)
production_gate_check
    ↓ (gates pass)
production_ready
    ↓ (deploy)
deployed
```

### Task Status Flow

```
not_started
    ↓ (start task)
in_progress
    ↓ (complete task)
completed

# Alternative path
in_progress
    ↓ (encounter blocker)
blocked
    ↓ (blocker resolved)
in_progress
```

### Track Status Flow

```
not_started
    ↓ (first sprint starts)
in_progress
    ↓ (all sprints complete)
completed
```

---

## Dependencies & Blockers

### Dependency Types

**1. Task Dependencies (`depends_on`)**
- Task A depends on Task B
- Task A cannot start until Task B completes
- Within same sprint or cross-sprint

**2. Sprint Dependencies (`depends_on`)**
- Sprint A depends on Sprint B
- Sprint A cannot start until Sprint B completes
- Can be cross-track

**3. Track Dependencies (`depends_on`)**
- Track A depends on Track B
- Track A cannot start until Track B completes

### Blocker Detection

Automatic blocker detection runs when:
- Task status changes
- Sprint status changes
- Dependencies are updated

**Algorithm:**
```python
def detect_blockers(task):
    blockers = []
    for dep_id in task.depends_on:
        dep_task = get_task(dep_id)
        if dep_task.status != 'completed':
            blockers.append(dep_id)
    return blockers
```

**Commands:**
```bash
# Show all blockers
roadmap deps --blockers

# Show what's blocking a specific task
roadmap deps task-123 --blockers
```

---

## Quality Gates

### Gate Levels

**1. Track-Level Gates**
- Apply to entire track
- Must pass before track completion
- Examples: "Integration Testing", "Documentation Complete"

**2. Sprint-Level Gates**
- Apply to specific sprint
- Must pass before sprint production-ready
- Examples: "Unit Testing", "Security Audit"

**3. Task-Level Gates** (future)
- Apply to individual tasks
- Examples: "Code Review", "Test Coverage"

### Gate Configuration

```yaml
quality_gates:
  - name: "Unit Testing"
    threshold: 80           # Minimum passing score
    blocking: true          # Blocks completion if fails
    status: "not_run"       # Current status
    description: "Test coverage must be ≥80%"
    score: null             # Actual score (set when run)
```

### Gate Status Values

- `not_run` - Gate not yet executed
- `passed` - Score ≥ threshold
- `failed` - Score < threshold

### Running Gates

```bash
# Run tests and get coverage
COVERAGE=$(pytest --cov=. --cov-report=json | jq '.totals.percent_covered')

# Update gate
roadmap gate update sprint-id "Unit Testing" \
  --status "passed" \
  --score "$COVERAGE"
```

---

## Performance & Caching

### RoadmapCache System

**Purpose:** Cache frequently accessed data to improve CLI performance

**Cache Location:** `.vibey/.cache/`

**Cached Data:**
- Roadmap structure
- Track listings
- Sprint details
- Task lists
- Dependency graphs

**Cache Invalidation:**
- Automatic on state changes
- Manual: `roadmap cache clear`

**Performance Impact:**
- First load: ~200ms
- Cached load: ~20ms (10x faster)

### Cache Commands

```bash
# Clear all caches
roadmap cache clear

# View cache statistics
roadmap cache stats

# Warm cache (preload common queries)
roadmap cache warm
```

---

## Best Practices

### 1. ID Naming

**Tracks:**
```
<purpose>-<version>
Examples: roadmap-integration, core-framework, goose-port
```

**Sprints:**
```
<track-id>-<number>
Examples: roadmap-integration-1, core-framework-2
```

**Tasks:**
```
<sprint-id>-task-<number>
Examples: roadmap-integration-1-task-001
```

### 2. Status Management

- Update status immediately when state changes
- Use appropriate status for each phase
- Don't skip statuses (follow flow)

### 3. Dependencies

- Document why dependency exists
- Keep dependency chains short (<3 levels)
- Review dependencies regularly
- Resolve blockers quickly

### 4. Quality Gates

- Set realistic thresholds
- Run gates before phase transitions
- Document gate failures
- Don't lower thresholds without discussion

### 5. Progress Tracking

- Update task status as work completes
- Keep estimated_hours realistic
- Track actual_hours for estimation improvement
- Review progress weekly

---

## API Reference

### Python Libraries

The roadmap system provides Python libraries for programmatic access:

```python
from roadmap_lib.cache import RoadmapCache
from roadmap_lib.query import RoadmapQuery
from roadmap_lib.update import RoadmapUpdate

# Initialize cache
cache = RoadmapCache(vibey_dir=Path(".vibey"))

# Query data
query = RoadmapQuery(cache)
sprint = query.get_sprint("roadmap-integration-2")
tasks = query.get_tasks(sprint_id="roadmap-integration-2")

# Update state
update = RoadmapUpdate(cache)
update.start_task("roadmap-integration-2-task-001")
update.complete_task("roadmap-integration-2-task-001")
```

### JSON Output Format

All CLI commands support `--json` flag:

```bash
roadmap show roadmap-integration-2 --json
```

**Output:**
```json
{
  "sprint": {
    "id": "roadmap-integration-2",
    "name": "Progress Tracking & Vibey Manager",
    "status": "production_ready",
    "progress": {
      "tasks_total": 6,
      "tasks_completed": 6,
      "completion_percent": 100
    }
  }
}
```

---

## Troubleshooting

### Common Issues

**1. "Circular dependency detected"**

**Cause:** Task A depends on Task B, Task B depends on Task A

**Solution:**
```bash
# Find circular dependencies
roadmap validate

# Fix by removing one dependency
# Edit task YAML file directly
```

**2. "Cache out of date"**

**Cause:** Manual YAML edits not reflected in CLI output

**Solution:**
```bash
roadmap cache clear
```

**3. "Task not found"**

**Cause:** Task ID doesn't exist or typo

**Solution:**
```bash
# List all tasks
roadmap list tasks

# Search for task
roadmap find <partial-title>
```

---

## Migration & Upgrades

### From v1.2 to v1.3

No migration needed - v1.3 is fully backward compatible.

**New Features Available:**
- AI-powered optimization
- Agent library management
- Real-time progress visualization

**Action Required:**
- None (all automatic)

### Future Versions

Roadmap system follows semantic versioning:
- **Patch** (1.3.x) - Bug fixes, no breaking changes
- **Minor** (1.x.0) - New features, backward compatible
- **Major** (x.0.0) - Breaking changes (with migration path)

---

## Appendix: File Format Versions

### Current Version: 1.0.0

**Roadmap Format:** v1.0
**Track Format:** v1.0
**Sprint Format:** v1.1 (adds production gates)
**Task Format:** v1.0

### Compatibility Matrix

| Framework Version | Roadmap Format | Notes |
|------------------|----------------|-------|
| v1.3.0 | v1.0 - v1.1 | Current |
| v1.2.0 | v1.0 | Legacy |
| v1.1.0 | N/A | Pre-roadmap |

---

## See Also

- [Progress Tracking Guide](../guides/PROGRESS_TRACKING.md)
- [CLI Commands Reference](COMMANDS.md)
- [Roadmap Object Hierarchy](../development/ROADMAP_OBJECT_HIERARCHY.md)
- [Integration Gap Analysis](../development/ROADMAP_INTEGRATION_GAP.md)

---

**Last Updated:** 2025-11-08
**Maintainer:** Vibey Framework Team
**Version:** 1.0.0
