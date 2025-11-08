# Roadmap State Management Scripts

Python scripts for managing roadmap state through the command line.

## Requirements

- Python 3.7+
- PyYAML: `pip install pyyaml`

## Scripts

### roadmap-init.py

Initialize a new roadmap structure.

**Usage:**
```bash
# Interactive mode
python3 roadmap-init.py

# Non-interactive mode
python3 roadmap-init.py --id my-roadmap --name "My Project" --version 1.0.0

# Custom directory
python3 roadmap-init.py --dir /path/to/project
```

**Options:**
- `--dir PATH` - Root directory (defaults to current working directory)
- `--id ID` - Roadmap ID (required for non-interactive mode)
- `--name NAME` - Roadmap name (required for non-interactive mode)
- `--version VERSION` - Initial version (default: 1.0.0)
- `--bump-on {sprint_completion,track_completion,manual}` - When to bump version
- `--bump-type {minor,patch}` - Version bump type
- `--created-by NAME` - Creator name (default: system)
- `--force` - Force initialization even if roadmap already exists

### roadmap-query.py

Query roadmap state (read operations).

**Usage:**
```bash
# Show roadmap summary
python3 roadmap-query.py

# Show track details
python3 roadmap-query.py --track backend

# Show sprint details
python3 roadmap-query.py --sprint backend-1

# Show task details
python3 roadmap-query.py --task backend-1-task-001

# Show blockers
python3 roadmap-query.py --blockers
python3 roadmap-query.py --blockers --id backend-1

# Show dependency graph
python3 roadmap-query.py --dependencies

# JSON output
python3 roadmap-query.py --json
```

**Options:**
- `--dir PATH` - Root directory (defaults to searching upward for .vibey/)
- `--track ID` - Show track details
- `--sprint ID` - Show sprint details
- `--task ID` - Show task details
- `--blockers` - Show blockers
- `--id ID` - Object ID (for --blockers)
- `--dependencies` - Show dependency graph information
- `--json` - Output as JSON

### roadmap-update.py

Update roadmap state (write operations).

**Usage:**
```bash
# Complete a task
python3 roadmap-update.py --complete-task backend-1-task-001

# Start a task
python3 roadmap-update.py --start-task backend-1-task-002

# Assign a task
python3 roadmap-update.py --assign-task backend-1-task-003 --agent web-developer

# Start a sprint
python3 roadmap-update.py --start-sprint backend-1

# Complete a sprint
python3 roadmap-update.py --complete-sprint backend-1

# Refresh all progress (recompute from tasks)
python3 roadmap-update.py --refresh-progress
```

**Options:**
- `--dir PATH` - Root directory (defaults to searching upward for .vibey/)
- `--complete-task ID` - Mark task as completed
- `--start-task ID` - Mark task as in progress
- `--assign-task ID` - Assign task to agent (requires --agent)
- `--agent NAME` - Agent name for task assignment
- `--start-sprint ID` - Start a sprint
- `--complete-sprint ID` - Mark sprint as completed
- `--refresh-progress` - Refresh all progress calculations
- `--by NAME` - User making the update (default: system)

## Automatic Status Progression

The scripts implement automatic status progression based on completion conditions:

### Sprint Status Progression

- **NOT_STARTED → IN_PROGRESS**: Manual (use `--start-sprint`)
- **IN_PROGRESS → COMPLETION_GATE_CHECK**: Automatic when all development tasks completed
- **COMPLETION_GATE_CHECK → PRODUCTION_GATE_CHECK**: Automatic when all completion gates passed
- **PRODUCTION_GATE_CHECK → PRODUCTION_READY**: Automatic when all production gates passed

### Track Status Progression

- **NOT_STARTED → IN_PROGRESS**: Automatic when first sprint starts
- **IN_PROGRESS → COMPLETED**: Automatic when all sprints completed or beyond
- **COMPLETED → PRODUCTION_READY**: Automatic when all sprints production_ready or deployed

### Roadmap Status Progression

- **NOT_STARTED → IN_PROGRESS**: Automatic when first sprint starts
- **IN_PROGRESS → COMPLETED**: Automatic when all tracks completed
- **COMPLETED → PRODUCTION_READY**: Automatic when all tracks production_ready

## Library Utilities

The `roadmap-lib/` directory contains reusable utilities:

### filesystem.py

File system management for roadmap structure.

- `FileSystemManager` - Manages .vibey/ directory structure
- `find_roadmap_root()` - Searches upward for .vibey/roadmap.yaml
- `ensure_roadmap_structure()` - Creates directory structure

### activity.py

Activity logging to roadmap activity log.

- `ActivityLogger` - Logs activities to roadmap
- `log_activity()` - Convenience function

### dependencies.py

Dependency resolution and circular dependency detection.

- `DependencyResolver` - Builds dependency graph
- `detect_circular_dependencies()` - Detects cycles
- `resolve_dependencies()` - Convenience function

### blockers.py

Automatic blocker computation based on dependency status.

- `BlockerComputer` - Computes blockers for objects
- `compute_blockers()` - Convenience function
- `is_blocked()` - Check if object is blocked

### status.py

Automatic status progression logic.

- `StatusManager` - Manages status progression
- `can_progress_status()` - Check if can progress
- `progress_status_if_ready()` - Auto-progress if ready

## Testing

Run the integration tests:

```bash
cd framework/scripts/tests
export PYTHONPATH=/path/to/vibey/framework
python3 test_roadmap_scripts.py
```

The test suite includes:
- Basic script functionality tests
- Complete workflow tests using example data
- Error handling tests
- Automatic progression tests

## Examples

### Initialize and Start Working

```bash
# Initialize roadmap
python3 roadmap-init.py --id my-project --name "My Project"

# Query roadmap
python3 roadmap-query.py

# Start a sprint (after adding tracks/sprints)
python3 roadmap-update.py --start-sprint backend-1

# Start working on a task
python3 roadmap-update.py --start-task backend-1-task-001
python3 roadmap-update.py --assign-task backend-1-task-001 --agent web-developer

# Complete the task
python3 roadmap-update.py --complete-task backend-1-task-001

# Check sprint status
python3 roadmap-query.py --sprint backend-1
```

### Query Progress

```bash
# View overall roadmap progress
python3 roadmap-query.py

# View specific track
python3 roadmap-query.py --track backend --json

# Check what's blocking progress
python3 roadmap-query.py --blockers

# View dependency graph
python3 roadmap-query.py --dependencies
```

### Refresh Progress

```bash
# Recalculate all progress from tasks
python3 roadmap-update.py --refresh-progress
```

## Architecture

### File Structure

```
.vibey/
├── roadmap.yaml          # Roadmap root
├── tracks/
│   ├── backend.yaml      # Track files
│   └── frontend.yaml
├── sprints/
│   ├── backend-1.yaml    # Sprint files
│   └── frontend-1.yaml
└── tasks/
    ├── backend-1-tasks.yaml     # Task batches
    └── frontend-1-tasks.yaml
```

### Data Flow

1. **Scripts** - Entry points for users
2. **Library Utilities** - Reusable logic (filesystem, activity, dependencies, blockers, status)
3. **Models** - Dataclasses representing roadmap objects
4. **Serialization** - YAML loading/saving
5. **Validation** - Schema validation

### Status Progression Flow

```
Task Completed
    ↓
Update Sprint Progress
    ↓
Check Sprint Auto-Progression (StatusManager)
    ↓
Update Track Progress
    ↓
Check Track Auto-Progression (StatusManager)
    ↓
Update Roadmap Progress
    ↓
Check Roadmap Auto-Progression (StatusManager)
    ↓
Log Activity (ActivityLogger)
```

## Error Handling

All scripts provide clear error messages:

- Missing roadmap: "No roadmap found. Run roadmap-init.py first."
- Invalid task ID: "Task 'xyz' not found"
- Cannot progress: "Cannot complete sprint: Not all development tasks completed"
- Validation errors: Detailed field-level errors from schema validation

## Future Enhancements

- Web UI for visualizing roadmap state
- Git integration for tracking changes
- Slack/Discord notifications
- Export to various formats (PDF, HTML, Markdown)
- Import from project management tools (Jira, Linear, etc.)
