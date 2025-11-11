# Roadmap CLI Reference

**Version:** 2.1
**Last Updated:** 2025-11-09

Quick reference for all roadmap CLI commands.

---

## Table of Contents

1. [Core Scripts](#core-scripts)
2. [Query Commands](#query-commands)
3. [Update Commands](#update-commands)
4. [Utility Commands](#utility-commands)
5. [Common Patterns](#common-patterns)

---

## Core Scripts

### roadmap-init.py

Initialize a new roadmap.

```bash
python3 framework/scripts/roadmap-init.py \
  --id PROJECT_ID \
  --name "Project Name" \
  --dir .vibey
```

**Options:**
- `--id` - Roadmap ID (lowercase-with-hyphens)
- `--name` - Human-readable name
- `--dir` - Root directory (default: `.vibey`)

**Example:**
```bash
python3 framework/scripts/roadmap-init.py \
  --id "ecommerce-platform" \
  --name "E-Commerce Platform" \
  --dir .vibey
```

---

### roadmap-query.py

Query roadmap state (read-only).

```bash
python3 framework/scripts/roadmap-query.py [OPTIONS]
```

**Options:**
- `--dir DIR` - Root directory (auto-detected if not specified)
- `--track TRACK` - Show track details
- `--sprint SPRINT` - Show sprint details
- `--task TASK` - Show task details
- `--blockers` - Show blockers
- `--id ID` - Object ID for blockers
- `--dependencies` - Show dependency graph
- `--json` - Output as JSON

**Examples:**
```bash
# Show roadmap summary
python3 framework/scripts/roadmap-query.py

# Show track
python3 framework/scripts/roadmap-query.py --track backend

# Show sprint progress
python3 framework/scripts/roadmap-query.py --sprint backend-1

# Show task details
python3 framework/scripts/roadmap-query.py --task backend-1-task-001

# Show all blockers
python3 framework/scripts/roadmap-query.py --blockers

# Show blockers for specific object
python3 framework/scripts/roadmap-query.py --blockers --id backend-1

# JSON output
python3 framework/scripts/roadmap-query.py --sprint backend-1 --json
```

---

### roadmap-update.py

Update roadmap state.

```bash
python3 framework/scripts/roadmap-update.py [OPTIONS]
```

**Options:**
- `--dir DIR` - Root directory
- `--complete-task TASK_ID` - Mark task completed
- `--start-task TASK_ID` - Start task
- `--assign-task TASK_ID` - Assign task (requires `--agent`)
- `--agent AGENT` - Agent name
- `--start-sprint SPRINT_ID` - Start sprint
- `--complete-sprint SPRINT_ID` - Complete sprint
- `--refresh-progress` - Recalculate all sprint progress
- `--recalculate-all` - Recalculate entire roadmap hierarchy (sprints, tracks, roadmap, dependencies)
- `--verify` - Verify consistency after recalculation (use with `--recalculate-all`)
- `--by USER` - User making update (default: system)

**Examples:**
```bash
# Start task
python3 framework/scripts/roadmap-update.py --start-task backend-1-task-001

# Complete task
python3 framework/scripts/roadmap-update.py --complete-task backend-1-task-001

# Assign task to agent
python3 framework/scripts/roadmap-update.py \
  --assign-task backend-1-task-002 \
  --agent web-developer

# Start sprint
python3 framework/scripts/roadmap-update.py --start-sprint backend-1

# Complete sprint
python3 framework/scripts/roadmap-update.py --complete-sprint backend-1

# Refresh all sprint progress calculations
python3 framework/scripts/roadmap-update.py --refresh-progress

# Recalculate entire roadmap hierarchy (bottom-up)
python3 framework/scripts/roadmap-update.py --recalculate-all

# Recalculate with consistency verification
python3 framework/scripts/roadmap-update.py --recalculate-all --verify
```

---

## Query Commands

All query commands are in `framework/scripts/roadmap_commands/`.

### status.py

Show roadmap/track/sprint/task status.

```bash
# Roadmap status
vibey roadmap status

# Track status
vibey track status backend

# Sprint status
vibey sprint status backend-1

# Task status
vibey task status backend-1-task-001
```

### show.py

Show detailed object information.

```bash
# Show roadmap
vibey roadmap show

# Show track
vibey track show backend

# Show sprint
vibey sprint show backend-1

# Show task
vibey task show backend-1-task-001
```

### list_cmd.py

List objects.

```bash
# List all tracks
vibey track list

# List sprints in track
vibey sprint list --track backend

# List tasks in sprint
vibey task list --sprint backend-1

# List with filters
vibey task list --sprint backend-1 --status in_progress
```

### find.py

Search for objects.

```bash
# Find by pattern
vibey find "authentication"

# Find tasks by agent
vibey task find --agent web-developer

# Find blocked tasks
vibey task find --blocked

# Find tasks by status
vibey task find --status in_progress
```

### deps.py

Dependency visualization and checking.

```bash
# Show dependency graph
vibey deps graph

# Check dependencies for object
vibey deps check backend-1-task-002

# Show dependency tree
vibey deps tree --sprint backend-1
```

---

## Update Commands

### start.py / complete.py

Task lifecycle commands.

```bash
# Start task
vibey task start backend-1-task-001

# Complete task
vibey task complete backend-1-task-001

# Complete with commit
vibey task complete backend-1-task-001 --commit abc123
```

### assign.py

Assign tasks to agents.

```bash
# Assign task
vibey task assign backend-1-task-001 --agent web-developer

# Assign multiple tasks
vibey task assign backend-1-task-001 backend-1-task-002 --agent web-developer
```

### gate.py

Quality gate operations.

```bash
# Run quality gate
vibey gate run backend-1-gate-p001

# Run with command
vibey gate run backend-1-gate-p001 --command "npm test"

# Show gate status
vibey gate status backend-1-gate-p001

# List all gates
vibey gate list --sprint backend-1
```

---

## Utility Commands

### validate.py

Validate roadmap structure.

```bash
# Validate entire roadmap
vibey validate

# Validate specific object
vibey validate --sprint backend-1

# Fix common issues
vibey validate --fix
```

### version.py

Version management.

```bash
# Show version
vibey version

# Bump version
vibey version bump patch
vibey version bump minor
vibey version bump major --milestone "v2.0 Release"

# Show version history
vibey version history
```

### batch.py

Batch operations.

```bash
# Complete multiple tasks
vibey batch complete backend-1-task-001 backend-1-task-002

# Start multiple tasks
vibey batch start backend-1-task-003 backend-1-task-004

# Assign multiple tasks
vibey batch assign --agent web-developer \
  backend-1-task-001 \
  backend-1-task-002
```

### agents.py

Agent operations.

```bash
# List available agents
vibey agents list

# Show agent workload
vibey agents workload

# Find tasks for agent
vibey agents tasks web-developer
```

### recommend.py

Get recommendations.

```bash
# Recommend next task
vibey recommend next

# Recommend task for agent
vibey recommend task --agent web-developer

# Recommend agent for task
vibey recommend agent --task backend-1-task-001
```

### progress.py

Progress tracking.

```bash
# Show overall progress
vibey progress

# Show track progress
vibey progress --track backend

# Show sprint progress
vibey progress --sprint backend-1
```

### context.py

Context management.

```bash
# Show context for object
vibey context show --task backend-1-task-001

# Add context file
vibey context add --task backend-1-task-001 --file research.md

# List context
vibey context list --sprint backend-1
```

### plan.py

Sprint planning.

```bash
# Create sprint plan
vibey plan create --sprint backend-1

# Show plan
vibey plan show --sprint backend-1

# Extract tasks from plan
vibey plan extract --sprint backend-1
```

### summarize.py

Generate summaries.

```bash
# Summarize roadmap
vibey summarize

# Summarize sprint
vibey summarize --sprint backend-1

# Summarize with format
vibey summarize --sprint backend-1 --format markdown
```

### prepare.py

Prepare for work.

```bash
# Prepare sprint context
vibey prepare --sprint backend-1

# Prepare task context
vibey prepare --task backend-1-task-001
```

---

## Common Patterns

### Daily Workflow

```bash
# 1. Check what's blocked
vibey roadmap status --blockers

# 2. Find next task
vibey recommend next

# 3. Start task
vibey task start backend-1-task-001

# 4. Complete task
vibey task complete backend-1-task-001 --commit abc123

# 5. Check progress
vibey sprint status backend-1
```

### Sprint Workflow

```bash
# 1. Create sprint
vibey sprint create backend-1 --track backend

# 2. Plan sprint
vibey plan create --sprint backend-1

# 3. Extract tasks
vibey plan extract --sprint backend-1

# 4. Start sprint
vibey sprint start backend-1

# 5. Work on tasks (see Daily Workflow)

# 6. Run quality gates
vibey gate run backend-1-gate-c001
vibey gate run backend-1-gate-p001

# 7. Complete sprint
vibey sprint complete backend-1
```

### Debugging Workflow

```bash
# 1. Validate structure
vibey validate

# 2. Check dependencies
vibey deps check backend-1-task-002

# 3. Find blockers
vibey task find --blocked

# 4. Refresh sprint progress if stale
python3 framework/scripts/roadmap-update.py --refresh-progress

# 5. Recalculate entire hierarchy (after manual YAML edits or migrations)
python3 framework/scripts/roadmap-update.py --recalculate-all --verify

# 6. View JSON for debugging
python3 framework/scripts/roadmap-query.py --json
```

### Data Recovery Workflow

```bash
# 1. Backup current state
cp -r .vibey .vibey.backup

# 2. Run full hierarchy recalculation
python3 framework/scripts/roadmap-update.py --recalculate-all

# 3. Verify consistency
python3 framework/scripts/roadmap-update.py --recalculate-all --verify

# 4. Check for issues
vibey validate

# 5. Compare with backup if needed
diff -r .vibey .vibey.backup
```

### Reporting Workflow

```bash
# 1. Overall status
vibey roadmap status

# 2. Track progress
vibey track list --with-progress

# 3. Sprint summary
vibey summarize --sprint backend-1

# 4. Version history
vibey version history

# 5. Agent workload
vibey agents workload
```

---

## Environment Variables

```bash
# Set default roadmap directory
export VIBEY_ROADMAP_DIR=/path/to/.vibey

# Disable cache
export VIBEY_NO_CACHE=1

# Enable debug output
export VIBEY_DEBUG=1
```

---

## Output Formats

### Text (Default)

```bash
vibey sprint status backend-1
```

Output:
```
Sprint: backend-1 (User Authentication System)
Status: in_progress (60% complete)

Progress:
  Development: 3/5 tasks (60%)
  Completion Gates: 0/2 passed
  Production Gates: 0/3 passed
```

### JSON

```bash
vibey sprint status backend-1 --json
```

Output:
```json
{
  "id": "backend-1",
  "name": "User Authentication System",
  "status": "in_progress",
  "progress": {
    "development_tasks_completed": 3,
    "development_tasks_total": 5,
    "completion_percent": 60
  }
}
```

---

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Validation error
- `3` - Not found (object doesn't exist)
- `4` - Blocked (dependency not satisfied)

---

## See Also

- [ROADMAP_USER_GUIDE.md](./ROADMAP_USER_GUIDE.md) - Comprehensive user guide
- [ROADMAP_TUTORIAL.md](./ROADMAP_TUTORIAL.md) - Step-by-step tutorial
- [Design Decisions](../../framework/roadmap/DESIGN_DECISIONS.md) - Architecture details

---

**Version:** 2.1
**Last Updated:** 2025-11-09
