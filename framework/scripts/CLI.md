# Roadmap CLI

Unified command-line interface for roadmap management.

## Installation

Add the `scripts` directory to your PATH or create a symlink:

```bash
# Option 1: Add to PATH
export PATH="$PATH:/path/to/vibey/framework/scripts"

# Option 2: Create symlink
ln -s /path/to/vibey/framework/scripts/roadmap /usr/local/bin/roadmap
```

## Quick Start

```bash
# Initialize a new roadmap
roadmap init --id my-project --name "My Project"

# View status
roadmap status

# List all tracks
roadmap list tracks

# Show sprint details
roadmap show backend-1

# Search for objects
roadmap find "authentication"

# Check dependencies
roadmap deps backend-1

# Start working
roadmap start backend-1
roadmap start backend-1-task-001
roadmap assign backend-1-task-001 web-developer

# Complete work
roadmap complete backend-1-task-001

# Refresh progress
roadmap progress --refresh
```

## Commands

### Query Commands

#### `roadmap status`

Show roadmap status overview with all tracks and sprints.

**Usage:**
```bash
roadmap status [--json]
```

**Options:**
- `--json` - Output as JSON

**Example:**
```bash
$ roadmap status

================================================================================
🗺️  Vibey Multi-Platform Agent Framework
================================================================================
ID:      vibey-framework-v2
Version: 1.2.0
Status:  🔵 in_progress

📊 Overall Progress
  Tracks:   1/4  (8% complete)
  Sprints: 2/16
  Tasks:   18/53

🛤️  Tracks
--------------------------------------------------------------------------------

🔵 in_progress Roadmap Object Hierarchy Implementation
   ID: roadmap-system
   Progress: 18/53 tasks, 2/6 sprints (34% complete)
   Sprints:
     ✅ completed Core Data Model & YAML Schema (roadmap-system-1)
     ✅ completed State Management Scripts (roadmap-system-2)
     ⚪ not_started CLI Commands (Part 1: Query) (roadmap-system-3)
================================================================================
```

#### `roadmap show <id>`

Show detailed information for a track, sprint, or task.

**Usage:**
```bash
roadmap show <id> [--json]
```

**Arguments:**
- `<id>` - Object ID (track, sprint, or task)

**Options:**
- `--json` - Output as JSON

**Examples:**
```bash
# Show track
roadmap show backend

# Show sprint
roadmap show backend-1

# Show task
roadmap show backend-1-task-001

# JSON output
roadmap show backend-1 --json
```

#### `roadmap list [type]`

List objects (tracks, sprints, tasks).

**Usage:**
```bash
roadmap list [tracks|sprints|tasks] [--status STATUS] [--json]
```

**Arguments:**
- `[type]` - Optional: Type to list (tracks, sprints, tasks). Defaults to all.

**Options:**
- `--status STATUS` - Filter by status (not_started, in_progress, completed, etc.)
- `--json` - Output as JSON

**Examples:**
```bash
# List everything
roadmap list

# List only tracks
roadmap list tracks

# List in-progress sprints
roadmap list sprints --status in_progress

# List completed tasks
roadmap list tasks --status completed --json
```

#### `roadmap find <query>`

Search for objects by name or description.

**Usage:**
```bash
roadmap find <query> [--type TYPE] [--json]
```

**Arguments:**
- `<query>` - Search query (searches name, description, ID)

**Options:**
- `--type TYPE` - Filter by type (track, sprint, task)
- `--json` - Output as JSON

**Examples:**
```bash
# Search for "authentication"
roadmap find "authentication"

# Search only tasks
roadmap find "test" --type task

# JSON output
roadmap find "API" --json
```

#### `roadmap deps [id]`

Show dependencies and blockers.

**Usage:**
```bash
roadmap deps [id] [--blockers] [--dependents] [--json]
```

**Arguments:**
- `[id]` - Optional: Object ID. If omitted, shows overall dependency graph.

**Options:**
- `--blockers` - Show only blockers
- `--dependents` - Show only dependents
- `--json` - Output as JSON

**Examples:**
```bash
# Show overall dependency graph
roadmap deps

# Show dependencies for specific sprint
roadmap deps backend-1

# Check what's blocking a task
roadmap deps backend-1-task-002 --blockers
```

### Update Commands

#### `roadmap init`

Initialize a new roadmap.

**Usage:**
```bash
roadmap init [--id ID] [--name NAME] [--version VERSION] [--force]
```

**Options:**
- `--id ID` - Roadmap ID (required for non-interactive)
- `--name NAME` - Roadmap name (required for non-interactive)
- `--version VERSION` - Initial version (default: 1.0.0)
- `--bump-on {sprint_completion,track_completion,manual}` - When to bump version
- `--bump-type {minor,patch}` - Version bump type
- `--force` - Force reinitialize

**Examples:**
```bash
# Interactive mode
roadmap init

# Non-interactive mode
roadmap init --id my-project --name "My Project" --version 1.0.0
```

#### `roadmap start <id>`

Start a sprint or task.

**Usage:**
```bash
roadmap start <id>
```

**Arguments:**
- `<id>` - Sprint or task ID

**Examples:**
```bash
# Start a sprint
roadmap start backend-1

# Start a task
roadmap start backend-1-task-001
```

#### `roadmap complete <id>`

Mark a sprint or task as complete.

**Usage:**
```bash
roadmap complete <id>
```

**Arguments:**
- `<id>` - Sprint or task ID

**Examples:**
```bash
# Complete a task
roadmap complete backend-1-task-001

# Complete a sprint (if all conditions met)
roadmap complete backend-1
```

#### `roadmap assign <task_id> <agent>`

Assign a task to an agent.

**Usage:**
```bash
roadmap assign <task_id> <agent>
```

**Arguments:**
- `<task_id>` - Task ID
- `<agent>` - Agent name

**Examples:**
```bash
roadmap assign backend-1-task-001 web-developer
roadmap assign frontend-2-task-003 ui-designer
```

#### `roadmap progress`

Update progress calculations.

**Usage:**
```bash
roadmap progress --refresh
```

**Options:**
- `--refresh` - Recalculate all progress from tasks

**Examples:**
```bash
# Refresh all progress
roadmap progress --refresh
```

#### `roadmap batch <operation> <scope> [id]`

Batch update operations across multiple tasks.

**Usage:**
```bash
roadmap batch <operation> <scope> [id] [--agent AGENT] [--filter FILTER] [--status STATUS]
```

**Arguments:**
- `<operation>` - Operation to perform (complete, assign)
- `<scope>` - Scope of operation (sprint, track, roadmap)
- `[id]` - Object ID (required for sprint/track scope)

**Options:**
- `--agent AGENT` - Agent name (for assign operation)
- `--filter FILTER` - Task filter (dev, gates)
- `--status STATUS` - Status filter

**Examples:**
```bash
# Complete all tasks in a sprint
roadmap batch complete sprint backend-1

# Assign all unassigned tasks in a track to an agent
roadmap batch assign track backend --agent web-developer

# Complete all development tasks in entire roadmap
roadmap batch complete roadmap --filter dev
```

### Management Commands

#### `roadmap version`

Manage roadmap version.

**Usage:**
```bash
roadmap version {--show | --bump} [--type TYPE] [--message MESSAGE] [--tag]
```

**Options:**
- `--show` - Show current version
- `--bump` - Bump version
- `--type {major,minor,patch}` - Version bump type (uses roadmap strategy if not specified)
- `--message MESSAGE` - Version bump message
- `--tag` - Create git tag

**Examples:**
```bash
# Show current version
roadmap version --show

# Bump version using roadmap strategy
roadmap version --bump

# Manual version bump
roadmap version --bump --type minor --message "Added new features"

# Bump and create git tag
roadmap version --bump --tag
```

#### `roadmap validate`

Validate roadmap structure and health.

**Usage:**
```bash
roadmap validate [--fix] [--verbose]
```

**Options:**
- `--fix` - Attempt to fix issues automatically
- `--verbose` - Show detailed output

**Health Checks:**
- Circular dependency detection
- Orphaned file detection
- Invalid reference detection
- Progress consistency validation
- Schema validation
- Blocker consistency

**Examples:**
```bash
# Run all health checks
roadmap validate

# Run with detailed output
roadmap validate --verbose

# Attempt to fix issues
roadmap validate --fix
```

### Agent Commands

#### `roadmap recommend`

Get task and agent recommendations using intelligent routing.

**Usage:**
```bash
roadmap recommend [--task TASK_ID | --agent AGENT_NAME] [--limit N] [--json]
```

**Options:**
- `--task TASK_ID` - Get agent recommendations for a specific task
- `--agent AGENT_NAME` - Get task recommendations for a specific agent
- `--limit N` - Maximum number of recommendations (default: 5)
- `--json` - Output as JSON

**Examples:**
```bash
# Get recommended tasks to work on (by priority)
roadmap recommend

# Get agent recommendations for a specific task
roadmap recommend --task backend-1-task-003

# Get task recommendations for a specific agent
roadmap recommend --agent web-developer

# Limit recommendations
roadmap recommend --limit 3
```

**Agent Recommendation Algorithm:**
- Task type matching (50% weight)
- Keyword matching (up to 50% weight)
- Confidence scores displayed as percentages

**Task Recommendation Priority:**
- Sprint status (active sprints prioritized)
- Existing assignments (assigned tasks boosted)
- Agent confidence match
- Blocked tasks automatically filtered

#### `roadmap agents`

View agent workload, capabilities, and task assignments.

**Usage:**
```bash
roadmap agents [--workload] [--capabilities] [--agent AGENT_NAME] [--json]
```

**Options:**
- `--workload` - Show agent workload distribution
- `--capabilities` - Show agent capabilities and specialties
- `--agent AGENT_NAME` - Show details for specific agent
- `--json` - Output as JSON

**Examples:**
```bash
# Show agent workload
roadmap agents --workload

# Show agent capabilities
roadmap agents --capabilities

# Show details for specific agent
roadmap agents --agent web-developer

# Combined view
roadmap agents
```

**Available Agents:**
- **web-developer** - Web development, APIs, full-stack
- **ml-engineer** - Machine learning, data science
- **test-engineer** - Testing, QA, test automation
- **docs-writer** - Documentation, technical writing
- **security-auditor** - Security, vulnerability assessment
- **performance-engineer** - Performance optimization, profiling
- **observability-engineer** - Logging, monitoring, tracing
- **coordinator** - Project coordination, orchestration

#### `roadmap context <task_id>`

Load and analyze context for a task with hierarchical dependency loading.

**Usage:**
```bash
roadmap context <task_id> [--mode MODE] [--show-full] [--max-distance N]
```

**Options:**
- `--mode MODE` - Force specific context mode for all dependencies (minimal/summary/full)
- `--show-full` - Display full context details
- `--max-distance N` - Maximum dependency distance to load (default: 2)

**Examples:**
```bash
# Load hierarchical context for task
roadmap context backend-3-task-015

# Override mode for all dependencies
roadmap context backend-3-task-015 --mode summary

# Display full context details
roadmap context backend-3-task-015 --show-full

# Load deeper dependencies
roadmap context backend-3-task-015 --max-distance 3
```

**Context Modes:**
- **Minimal** (~100 tokens) - Outputs only, for far dependencies (distance 2+)
- **Summary** (~700 tokens) - Sprint & task summaries, for direct dependencies (distance 1)
- **Full** (~5,700 tokens) - All documentation, for current sprint

**Hierarchical Loading:**
- Distance 1 (direct deps) → Summary mode
- Distance 2 (transitive) → Minimal mode
- Distance 3+ → Skipped

**Dependency Graph Snapshot:**
Each context load displays a snapshot of the dependency graph at the time of analysis:
```
📊 Dependency Graph Snapshot:
   Direct dependencies: 3
     - backend-1-task-001
     - backend-1-task-002
     - backend-2-task-005
   Branch: feature/new-api
   Total objects in graph: 47
```

This snapshot helps with:
- **Audit trail**: Know exactly what the AI saw when making recommendations
- **Reproducibility**: Recreate the exact context for evaluation
- **Debugging**: Understand why certain dependencies were loaded

**Benefits:** 57-90% reduction in context size while preserving critical information.

#### `roadmap summarize <sprint_id>`

Generate dependency and task summaries for completed sprints.

**Usage:**
```bash
roadmap summarize <sprint_id> [--task TASK_ID] [--all --completed] [--force]
```

**Options:**
- `--task TASK_ID` - Generate summary for specific task
- `--all --completed` - Summarize all completed sprints
- `--force` - Force regeneration of existing summaries

**Examples:**
```bash
# Generate sprint dependency summary
roadmap summarize backend-1

# Generate task summary
roadmap summarize backend-1 --task backend-1-task-001

# Batch: summarize all completed sprints
roadmap summarize --all --completed

# Force regeneration
roadmap summarize backend-1 --force
```

**What gets generated:**
- **Dependency Summary** (~500 words) - Goals, outputs, interfaces, learnings
- **Task Summaries** - Outputs, interfaces, gotchas per task
- Saved to sprint YAML: `dependency_summary` and `task_summaries` fields

**When to use:** After sprint completion, to enable efficient context loading for future tasks.

#### `roadmap prepare <task_id>`

Generate deep preparation document for complex tasks with many dependencies.

**Usage:**
```bash
roadmap prepare <task_id> [--show] [--regenerate] [--list]
```

**Options:**
- `--show` - View existing preparation document
- `--regenerate` - Force regeneration of prep doc
- `--list` - List all tasks with preparation documents

**Examples:**
```bash
# Generate preparation document (loads ALL dependencies)
roadmap prepare backend-3-task-015

# View existing preparation document
roadmap prepare backend-3-task-015 --show

# Regenerate if outdated
roadmap prepare backend-3-task-015 --regenerate

# List all tasks with prep docs
roadmap prepare --list
```

**Preparation document includes:**
- Task overview and goals
- **Dependency graph snapshot** (for reproducibility and audit)
- Dependency analysis (what each provides, how to integrate)
- Key learnings from dependency sprints
- Critical integration points and interfaces
- Implementation checklist
- Questions to resolve before starting

**Dependency Graph Snapshot:**
The preparation document captures the exact dependency graph state:
```markdown
## Dependency Graph Snapshot

**Direct Dependencies:** 5
  - backend-1-task-001
  - backend-1-task-002
  - backend-2-task-005
  - backend-2-task-007
  - shared-task-003

**Transitive Dependencies Loaded:** 12
**Graph Metadata:**
  - Branch: feature/new-api
  - Timestamp: 2025-11-07T15:30:00Z
  - Total dependency objects in graph: 47
```

This enables:
- **Later evaluation**: Did the AI follow the actual dependencies?
- **Reproducibility**: Recreate the exact context that influenced recommendations
- **Audit trail**: Track what information was available at preparation time

**When to use:** Before starting complex tasks with multiple dependencies or integration requirements.

**Saved to:** `.vibey/sprint_docs/<sprint>/prep/<task>.md`

## Global Options

These options work with all commands:

- `--dir PATH` - Root directory (defaults to searching upward for .vibey/)
- `--no-cache` - Disable caching (for debugging)
- `--plain` - Plain output with no colors or formatting (for scripting)
- `--version` - Show version information
- `--help` - Show help

### Plain Mode (`--plain`)

Use plain mode for machine-readable output or when piping to other tools:

```bash
# Plain output (no colors, simple formatting)
roadmap --plain list tracks

# Good for scripting
roadmap --plain status | grep "in_progress"

# Respects NO_COLOR environment variable
NO_COLOR=1 roadmap list tasks
```

**Plain mode features:**
- No ANSI color codes
- Simple text-based formatting
- Status shown as text instead of icons
- Progress shown as ratios (5/10 instead of progress bars)
- Tables use simple borders

## Examples

### Daily Workflow

```bash
# Morning: Check what needs to be done
roadmap status

# Get intelligent task recommendations
roadmap recommend

# Or find tasks for a specific agent
roadmap recommend --agent web-developer

# Before starting: Load context
roadmap context backend-1-task-002

# If task is complex, review preparation doc
roadmap prepare backend-1-task-002 --show

# Start working on recommended task
roadmap start backend-1-task-002
roadmap assign backend-1-task-002 web-developer

# During work: Check dependencies
roadmap deps backend-1-task-002

# Complete the task
roadmap complete backend-1-task-002

# End of sprint: Generate summaries
roadmap complete backend-1
roadmap summarize backend-1

# End of day: Check overall progress
roadmap status
roadmap agents --workload
```

### Agent-Driven Workflow

```bash
# Check agent workload distribution
roadmap agents --workload

# Get task recommendations for an agent
roadmap recommend --agent web-developer --limit 5

# For a specific task, see which agent should handle it
roadmap recommend --task backend-1-task-003

# Assign based on recommendation
roadmap assign backend-1-task-003 web-developer

# Batch assign unassigned tasks to an agent
roadmap batch assign sprint backend-1 --agent web-developer

# Monitor agent progress
roadmap agents --agent web-developer
```

### Sprint Management

```bash
# Start a new sprint
roadmap start backend-2

# View sprint details
roadmap show backend-2

# List all tasks in sprint
roadmap list tasks | grep backend-2

# Check what's blocking the sprint
roadmap deps backend-2 --blockers

# After completing all tasks, sprint auto-progresses to completion_gate_check
# Complete remaining gates...

# Complete the sprint
roadmap complete backend-2
```

### Progress Tracking

```bash
# View overall status
roadmap status

# See all in-progress work
roadmap list tasks --status in_progress

# Check blockers
roadmap deps --blockers

# Find specific work
roadmap find "API endpoint"

# Detailed view
roadmap show api-sprint-1
```

### Debugging Dependencies

```bash
# Check dependency graph health
roadmap deps

# See what depends on a specific object
roadmap deps backend-1 --dependents

# Check what's blocking an object
roadmap deps backend-1 --blockers

# View full dependency chain
roadmap show backend-1-task-003
```

## Status Icons and Formatting

The CLI uses colorful formatting and emoji icons for better readability:

### Status Indicators

- ⚪ **not_started** - Not yet started (white/gray)
- 🔵 **in_progress** - Currently in progress (blue)
- ⏸️ **paused** - Paused/on hold (yellow)
- 🚧 **completion_gate_check** - Checking completion gates (yellow)
- ✅ **completed** - Completed (green)
- 🔍 **production_gate_check** - Checking production gates (cyan)
- 🚀 **production_ready** - Ready for production (bright green)
- 🌟 **deployed** - Deployed to production (bright green)
- ❌ **won't_do** - Won't be done (red)
- ⚠️ **BLOCKED** - Blocked indicator (red warning)

### Progress Bars

Progress bars use color-coded indicators:
- 🟢 Green: 75-100% complete
- 🟡 Yellow: 50-74% complete
- 🔴 Red: 0-49% complete

Example output:
```
████████████████████░░░░░░░░ 65% (13/20)
```

### Table Formatting

List commands display data in formatted tables with:
- Unicode box-drawing characters for borders
- Aligned columns with padding
- Dimmed IDs for reduced visual noise
- Color-coded status and warnings

Example:
```
Status      │ Track Name                  │ ID             │ Sprints │ Completion │ Progress
────────────┼─────────────────────────────┼────────────────┼─────────┼────────────┼─────────
🔵 in_progress │ Core Framework Enhancements │ core-framework │ 0/3     │ 0%         │ ░░░░░░░░ 0%
✅ completed   │ Roadmap System              │ roadmap-system │ 6/6     │ 100%       │ ████████ 100%
```

## JSON Output

Most commands support `--json` for machine-readable output:

```bash
# Get JSON output
roadmap status --json | jq '.progress.completion'

# Pipe to other tools
roadmap list tasks --json | jq '.tasks[] | select(.status == "in_progress")'

# Save to file
roadmap deps --json > dependencies.json
```

## Tips

### Aliases

Add these to your shell RC file (.bashrc, .zshrc):

```bash
alias rms='roadmap status'
alias rml='roadmap list'
alias rmf='roadmap find'
alias rmd='roadmap deps'
```

### Shell Completion

Future versions will support shell completion for bash/zsh.

### Integration with Git

```bash
# Commit with roadmap context
git commit -m "feat: implement auth (closes roadmap:backend-1-task-001)"

# Tag releases with roadmap version
roadmap status --json | jq -r '.version' | xargs -I {} git tag v{}
```

## Troubleshooting

### "No roadmap found"

Run `roadmap init` in your project root to create a roadmap.

### "Object not found"

- Use `roadmap list` to see all objects
- Use `roadmap find <query>` to search
- Check the object ID format (track-id, sprint-id, task-id)

### Permission Errors

Make sure the roadmap CLI is executable:
```bash
chmod +x /path/to/vibey/framework/scripts/roadmap
```

### Import Errors

Ensure PyYAML is installed:
```bash
pip install pyyaml
```

## Architecture

The CLI uses a subcommand architecture:

```
roadmap (main CLI)
  ├── roadmap_commands/
  │   ├── status.py      # Query commands
  │   ├── show.py
  │   ├── list_cmd.py
  │   ├── find.py
  │   ├── deps.py
  │   ├── init.py        # Update commands
  │   ├── start.py
  │   ├── complete.py
  │   ├── assign.py
  │   ├── progress.py
  │   ├── batch.py
  │   ├── version.py     # Management commands
  │   ├── validate.py
  │   ├── recommend.py   # Agent commands
  │   └── agents.py
  ├── roadmap-lib/       # Shared utilities
  │   ├── filesystem.py
  │   ├── activity.py
  │   ├── dependencies.py
  │   ├── blockers.py
  │   ├── status.py
  │   ├── versioning.py
  │   └── agents.py      # Agent routing & recommendations
  └── roadmap-*.py       # Lower-level scripts
```

## Future Enhancements

- Shell completion (bash/zsh/fish)
- Interactive TUI mode
- Watch mode for live updates
- Export commands (PDF, HTML, Markdown)
- Git integration commands
- Notification system
- Web dashboard
- Plugin system for custom commands
