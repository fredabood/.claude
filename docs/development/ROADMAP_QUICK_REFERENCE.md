# Roadmap System - Quick Reference

**Version:** 1.0
**Last Updated:** 2025-11-07

One-page reference for the Roadmap Object Hierarchy system.

---

## Installation

```bash
# Add to PATH
export PATH="$PATH:/path/to/vibey/framework/scripts"

# Initialize roadmap
roadmap init --id my-project --name "My Project"
```

---

## Core Commands

### Query
```bash
roadmap status                    # Show overall status
roadmap show <id>                 # Show object details
roadmap list [tracks|sprints|tasks]  # List objects
roadmap find "keyword"            # Search objects
roadmap deps [id]                 # Show dependencies
```

### Update
```bash
roadmap start <id>                # Start sprint/task
roadmap complete <id>             # Complete sprint/task
roadmap assign <task> <agent>     # Assign task
roadmap progress --refresh        # Refresh progress
```

### Agent
```bash
roadmap recommend                 # Get task recommendations
roadmap recommend --task <id>     # Get agent recommendations
roadmap recommend --agent <name>  # Get tasks for agent
roadmap agents --workload         # View agent workload
```

### Management
```bash
roadmap version --show            # Show version
roadmap version --bump            # Bump version
roadmap validate                  # Health check
```

### Context & Summaries
```bash
# Generate summaries
roadmap summarize <sprint-id>              # Generate dependency summary
roadmap summarize <sprint-id> --task <id>  # Generate task summary
roadmap summarize --all --completed        # Summarize all completed sprints
roadmap summarize <sprint-id> --force      # Force regeneration

# Load context
roadmap context <task-id>                  # View context for task
roadmap context <task-id> --mode summary   # Specify mode (minimal/summary/full)
roadmap context <task-id> --show-full      # Display full context details
roadmap context <task-id> --max-distance 3 # Load deeper dependencies

# Preparation mode
roadmap prepare <task-id>                  # Deep analysis (complex tasks)
roadmap prepare <task-id> --show           # View preparation document
roadmap prepare <task-id> --regenerate     # Force regeneration
roadmap prepare --list                     # List tasks with prep docs
```

---

## Context Loading Strategy

### Context Modes

| Mode | Size | Use Case | Content |
|------|------|----------|---------|
| **Minimal** | ~100 tokens | Far dependencies | Outputs only |
| **Summary** | ~700 tokens | Direct dependencies | Sprint & task summaries |
| **Full** | ~5,700 tokens | Current sprint | All documentation |

### Hierarchical Loading

**Distance-based mode selection:**
- **Distance 1** (direct deps) → Summary mode
- **Distance 2** (transitive) → Minimal mode
- **Distance 3+** → Skipped

**Result:** 57-90% reduction in context size while preserving critical information.

### Six-Strategy Approach

1. **Dependency Summaries** - Auto-generated 500-word overviews
2. **Task Summaries** - Granular outputs/interfaces/gotchas
3. **Context Modes** - Configurable detail levels
4. **Hierarchical Loading** - Distance-based mode selection
5. **Lazy Loading** - Caching and on-demand loading
6. **Preparation Mode** - Deep analysis for complex tasks

### Workflow

```bash
# On sprint completion
roadmap summarize <sprint-id>         # Generate dependency summary
roadmap summarize <sprint-id> --task <id>  # Generate task summaries

# When starting a task
roadmap context <task-id>             # Load hierarchical context

# For complex tasks
roadmap prepare <task-id>             # Deep analysis with full context
roadmap prepare <task-id> --show      # Review preparation doc
```

---

## Object Hierarchy

```
Roadmap (project vision)
  └── Track (major feature area)
      └── Sprint (2-week work unit)
          └── Task (atomic work item)
```

---

## File Structure

```
.vibey/
├── roadmap.yaml              # Roadmap root
├── tracks/
│   └── track-id.yaml         # Track definition
├── sprints/
│   └── sprint-id.yaml        # Sprint definition
├── tasks/
│   └── sprint-id-tasks.yaml  # Task definitions
└── activity/
    └── YYYY-MM-DD.log        # Activity logs
```

---

## Status Flow

### Sprint
```
not_started → in_progress → completion_gate_check → completed
```

### Task
```
not_started → in_progress → completed
```

---

## Quality Gates

```yaml
quality_gates:
  - name: "Unit Tests"
    threshold: 90
    blocking: true
    status: "not_run"
```

**Gate Types:**
- `development` - Run during development
- `completion` - Run before sprint completion
- `production` - Run before production deployment

---

## Dependencies

```yaml
dependencies:
  - type: "task"              # or "sprint", "track"
    target_id: "backend-1-task-001"
    at_status: "completed"    # or "in_progress"
    reason: "Need X before Y"
```

---

## Task Types

- `development` - Development work
- `testing` - Testing tasks
- `documentation` - Documentation tasks
- `gate` - Quality gate tasks
- `design` - Design tasks
- `research` - Research tasks

---

## Agent Types

- `web-developer` - Web APIs, full-stack
- `ml-engineer` - ML, data science
- `test-engineer` - Testing, QA
- `docs-writer` - Documentation
- `security-auditor` - Security audits
- `performance-engineer` - Performance
- `observability-engineer` - Monitoring
- `coordinator` - Orchestration

---

## Task Template

```yaml
- id: "sprint-id-task-001"
  sprint_id: "sprint-id"
  track_id: "track-id"
  roadmap_id: "roadmap-id"

  name: "Task name"
  description: "Detailed description"
  type: "development"
  status: "not_started"

  estimated_duration: "4 hours"
  assigned_agent: "web-developer"

  dependencies:
    - type: "task"
      target_id: "sprint-id-task-000"
      at_status: "completed"
```

---

## Sprint Template

```yaml
sprint:
  id: "track-id-1"
  name: "Sprint Name"
  track_id: "track-id"
  roadmap_id: "roadmap-id"

  status: "not_started"
  estimated_duration: "2 weeks"

  quality_gates:
    - name: "Unit Tests"
      threshold: 90
      blocking: true
      status: "not_run"

  dependencies: []
  blocks: []
```

---

## Track Template

```yaml
track:
  id: "track-id"
  name: "Track Name"
  roadmap_id: "roadmap-id"

  status: "not_started"
  priority: "high"

  progress:
    sprints_total: 3
    sprints_completed: 0
    tasks_total: 24
    tasks_completed: 0

  sprints:
    - id: "track-id-1"
      name: "Sprint 1"
      status: "not_started"

  dependencies: []
  blocks: []
```

---

## Daily Workflow

```bash
# Morning
roadmap status                    # Check overall status
roadmap recommend                 # Get next task

# Start work
roadmap start <task-id>
roadmap assign <task-id> <agent>
roadmap context <task-id>         # Load task context

# During work
roadmap deps <task-id> --blockers  # Check blockers
roadmap show <sprint-id>           # Check progress
roadmap prepare <task-id> --show   # Review prep doc (if complex)

# Complete work
roadmap complete <task-id>

# End of sprint
roadmap summarize <sprint-id>      # Generate dependency summary

# End of day
roadmap agents --workload          # Check distribution
roadmap status                     # Overall progress
```

---

## Batch Operations

```bash
# Complete all tasks in sprint
roadmap batch complete sprint backend-1

# Assign all unassigned to agent
roadmap batch assign track backend --agent web-developer

# Complete all dev tasks
roadmap batch complete roadmap --filter dev
```

---

## Common Patterns

### Sequential Tasks
```yaml
Task 1 (no dependencies)
  → Task 2 (depends on Task 1)
    → Task 3 (depends on Task 2)
```

### Parallel Tasks
```yaml
Task A (no dependencies)
Task B (no dependencies)
  ↓
Task C (depends on A + B)
```

### Track Dependencies
```yaml
Track 1
  → Track 2 (depends on Track 1)
    → Track 3 (depends on Track 2)
```

---

## Validation

```bash
roadmap validate              # Run all checks
roadmap validate --verbose    # Detailed output
roadmap validate --fix        # Auto-fix issues
```

**Checks:**
- Circular dependencies
- Orphaned files
- Invalid references
- Progress consistency
- Schema validation

---

## Version Management

```bash
roadmap version --show        # Show current
roadmap version --bump        # Bump using strategy
roadmap version --bump --type minor  # Manual bump
roadmap version --bump --tag  # Create git tag
```

**Strategy:**
```yaml
version_strategy:
  bump_on: "sprint_completion"  # or "track_completion", "manual"
  bump_type: "minor"            # or "patch"
```

---

## JSON Output

Most commands support `--json`:

```bash
roadmap status --json | jq '.progress'
roadmap list tasks --json | jq '.tasks[] | select(.status == "in_progress")'
roadmap deps --json | jq '.blockers'
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "roadmap: command not found" | Add to PATH or create symlink |
| "No roadmap found" | Run `roadmap init` |
| Import errors | `pip install pyyaml` |
| Circular dependencies | `roadmap validate --verbose` |
| Sprint won't complete | Check quality gates pass |

---

## Global Options

```bash
--dir PATH    # Root directory
--json        # JSON output (most commands)
--help        # Command help
```

---

## Examples

```bash
# Get recommendations for ML engineer
roadmap recommend --agent ml-engineer

# Check what's blocking a task
roadmap deps backend-1-task-003 --blockers

# View specific agent workload
roadmap agents --agent web-developer

# Find all authentication tasks
roadmap find "authentication" --type task

# List completed sprints
roadmap list sprints --status completed

# Context loading workflow
roadmap context backend-1-task-003        # Load context for task
roadmap prepare backend-1-task-015        # Complex task preparation
roadmap summarize backend-1               # Generate sprint summary
roadmap summarize backend-1 --task task-001  # Task summary
```

---

## Resources

- **User Guide:** `docs/development/ROADMAP_USER_GUIDE.md`
- **CLI Reference:** `framework/scripts/CLI.md`
- **Examples:** `docs/development/ROADMAP_EXAMPLES.md`
- **Migration Guide:** `docs/development/ROADMAP_MIGRATION_GUIDE.md`

---

**Print this page for quick reference!** 📄
