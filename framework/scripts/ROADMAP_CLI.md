# Vibey Roadmap CLI

Command-line interface for managing Vibey roadmap state.

## Quick Start

### Using the Wrapper Script

The easiest way to use roadmap commands:

```bash
# From repository root
./framework/scripts/roadmap-cli.sh query
./framework/scripts/roadmap-cli.sh update --start-task task-id
./framework/scripts/roadmap-cli.sh context task-id
```

### Installation Options

#### Option 1: Create Alias (Recommended)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias vibey-roadmap='/path/to/vibey/framework/scripts/roadmap-cli.sh'
```

Then use anywhere:

```bash
vibey-roadmap query
vibey-roadmap update --complete-task task-id
```

#### Option 2: Symlink to PATH

```bash
# From repository root
sudo ln -s $(pwd)/framework/scripts/roadmap-cli.sh /usr/local/bin/vibey-roadmap
```

Then use anywhere:

```bash
vibey-roadmap query --track infrastructure-fixes
```

#### Option 3: Direct Python Execution

If you prefer calling Python scripts directly:

```bash
# Set PYTHONPATH first
export PYTHONPATH=/path/to/vibey:$PYTHONPATH

# Run scripts
python3 framework/scripts/roadmap-query.py
python3 framework/scripts/roadmap-update.py --help
```

## Available Commands

### `query` - Query Roadmap State

View roadmap, track, sprint, or task information.

```bash
# Show roadmap summary
vibey-roadmap query

# Show specific track
vibey-roadmap query --track infrastructure-fixes

# Show specific sprint
vibey-roadmap query --sprint infrastructure-fixes-1

# Show specific task
vibey-roadmap query --task infrastructure-fixes-1-task-001

# Show blockers
vibey-roadmap query --blockers

# JSON output
vibey-roadmap query --json
```

### `update` - Update Roadmap State

Modify roadmap state (start/complete tasks, update progress).

```bash
# Start a sprint
vibey-roadmap update --start-sprint infrastructure-fixes-1

# Complete a sprint
vibey-roadmap update --complete-sprint infrastructure-fixes-1

# Start a task
vibey-roadmap update --start-task infrastructure-fixes-1-task-001

# Complete a task
vibey-roadmap update --complete-task infrastructure-fixes-1-task-001

# Assign a task to an agent
vibey-roadmap update --assign-task task-id --agent web-developer

# Refresh all progress calculations
vibey-roadmap update --refresh-progress
```

### `context` - Load Task Context

Load task context with dependency-based loading.

```bash
# Load context for a task
vibey-roadmap context infrastructure-fixes-1-task-001

# Customize dependency distance
vibey-roadmap context infrastructure-fixes-1-task-001 --max-distance 2

# JSON output
vibey-roadmap context infrastructure-fixes-1-task-001 --format json

# Hide statistics
vibey-roadmap context infrastructure-fixes-1-task-001 --no-stats
```

### `summarize` - Generate Summaries

Generate markdown summaries for tasks and sprints.

```bash
# Summarize a task
vibey-roadmap summarize task infrastructure-fixes-1-task-001

# Summarize a sprint
vibey-roadmap summarize sprint infrastructure-fixes-1

# JSON output
vibey-roadmap summarize task task-id --format json
```

### `init` - Initialize Roadmap

Create a new roadmap for a project.

```bash
# Initialize roadmap
vibey-roadmap init --name "My Project" --version "1.0.0"

# Specify output location
vibey-roadmap init --name "My Project" --output /path/to/.vibey/roadmap.yaml
```

### `prepare` - Prepare Roadmap from Plan

Extract roadmap structure from sprint plan documents.

```bash
# Prepare roadmap from sprint plan
vibey-roadmap prepare --plan docs/sprints/sprint-1-plan.md

# Specify track
vibey-roadmap prepare --plan plan.md --track backend
```

### `sync-docs` - Synchronize Documentation

Sync roadmap data with markdown documentation.

```bash
# Sync documentation
vibey-roadmap sync-docs

# Dry run (preview changes)
vibey-roadmap sync-docs --dry-run
```

## Common Workflows

### Starting a New Sprint

```bash
# 1. Start the sprint
vibey-roadmap update --start-sprint sprint-id

# 2. View sprint details
vibey-roadmap query --sprint sprint-id

# 3. Start first task
vibey-roadmap update --start-task sprint-id-task-001
```

### Completing Work

```bash
# 1. Complete task
vibey-roadmap update --complete-task task-id

# 2. Check progress
vibey-roadmap query --sprint sprint-id

# 3. Complete sprint when all tasks done
vibey-roadmap update --complete-sprint sprint-id
```

### Checking Status

```bash
# Overall roadmap status
vibey-roadmap query

# Specific track progress
vibey-roadmap query --track track-id

# View blockers
vibey-roadmap query --blockers
```

### Working with Context

```bash
# Load context for current task
vibey-roadmap context current-task-id

# Include more dependencies
vibey-roadmap context current-task-id --max-distance 5

# Export context as JSON
vibey-roadmap context current-task-id --format json > context.json
```

## Troubleshooting

### Command Not Found

If you get "command not found" after installation:

```bash
# Reload shell configuration
source ~/.bashrc  # or source ~/.zshrc

# Or start a new terminal session
```

### Import Errors

If you get Python import errors:

```bash
# Ensure you're using the wrapper script (handles PYTHONPATH automatically)
./framework/scripts/roadmap-cli.sh query

# Or set PYTHONPATH manually
export PYTHONPATH=/path/to/vibey:$PYTHONPATH
python3 framework/scripts/roadmap-query.py
```

### Roadmap Not Found

If you get "roadmap not found":

```bash
# Initialize a roadmap first
vibey-roadmap init --name "Project Name" --version "1.0.0"

# Or ensure you're in a directory with .vibey/roadmap.yaml
```

### Permission Denied

If you get permission errors:

```bash
# Make script executable
chmod +x framework/scripts/roadmap-cli.sh

# For symlink installation, use sudo
sudo ln -s $(pwd)/framework/scripts/roadmap-cli.sh /usr/local/bin/vibey-roadmap
```

## Technical Details

### How the Wrapper Works

The `roadmap-cli.sh` wrapper script:

1. Detects its own location
2. Calculates repository root
3. Sets `PYTHONPATH` automatically
4. Maps command names to Python scripts
5. Executes the appropriate script with arguments

### Script Mapping

| Command | Python Script |
|---------|---------------|
| query | roadmap-query.py |
| update | roadmap-update.py |
| init | roadmap-init.py |
| prepare | roadmap-prepare.py |
| context | roadmap-context.py |
| summarize | roadmap-summarize.py |
| sync-docs | roadmap-sync-docs.py |

### Directory Structure

The wrapper expects this structure:

```
vibey/
├── framework/
│   ├── roadmap/          # Python modules
│   └── scripts/
│       ├── roadmap-cli.sh        # Wrapper script
│       ├── roadmap-query.py      # Query script
│       ├── roadmap-update.py     # Update script
│       └── ...                   # Other scripts
└── .vibey/
    ├── roadmap.yaml              # Roadmap data
    └── roadmap/                  # Hierarchical structure
```

## Contributing

When adding new roadmap scripts:

1. Add Python script to `framework/scripts/`
2. Update `COMMANDS` array in `roadmap-cli.sh`
3. Document the command in this README
4. Add examples and usage information

## See Also

- **Roadmap Object Hierarchy:** `docs/development/ROADMAP_OBJECT_HIERARCHY.md`
- **Implementation Plan:** `docs/development/ROADMAP_IMPLEMENTATION_PLAN.md`
- **Framework Scripts:** `framework/scripts/README.md` (if exists)
