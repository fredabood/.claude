# Vibey CLI Reference

**Version:** 2.5.0
**Status:** Production Ready
**Platform:** Cross-platform (macOS, Linux, Windows)

---

## Overview

The Vibey CLI is the unified command-line interface for the Vibey Agent Framework. It provides platform-agnostic access to all framework functionality including roadmap management, deployment, configuration, and documentation generation.

### Design Philosophy

- **Platform Agnostic**: Works across all AI coding assistant platforms
- **Unified Interface**: Single source of truth for all framework operations
- **Rich Output**: Color-coded, structured output for better readability
- **Error Handling**: Comprehensive error messages with actionable suggestions
- **Composable**: Commands designed to work well in scripts and automation

---

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Git (for commit tracking features)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/your-org/vibey.git
cd vibey

# Install in development mode
pip install -e .

# Verify installation
vibey --version
```

### Install via pip (when published)

```bash
pip install vibey
vibey --version
```

---

## Global Options

These options are available for all commands:

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | | Show version and exit |
| `--help` | `-h` | Show help message and exit |
| `--verbose` | `-v` | Enable verbose output (detailed logging) |
| `--quiet` | `-q` | Suppress non-essential output |

### Examples

```bash
# Check version
vibey --version

# Get help for any command
vibey --help
vibey roadmap --help
vibey roadmap start --help

# Verbose mode for debugging
vibey --verbose roadmap status

# Quiet mode for scripts
vibey --quiet roadmap show sprint-1
```

---

## Command Groups

The CLI is organized into four main command groups:

1. **`roadmap`** - Manage roadmap system (tracks, sprints, tasks, dependencies)
2. **`deploy`** - Deploy framework to target platforms
3. **`docs`** - Generate and manage documentation
4. **`config`** - Manage framework configuration

---

## Roadmap Commands

The roadmap system provides hierarchical project planning with tracks, sprints, tasks, and dependencies.

### `vibey roadmap init`

Initialize a new roadmap in `.vibey/roadmap/`.

**Usage:**
```bash
vibey roadmap init [OPTIONS]
```

**Options:**
| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `--name TEXT` | Name of the roadmap | Yes (prompts if missing) | None |
| `--version TEXT` | Initial semantic version | No | `1.0.0` |

**Examples:**
```bash
# Interactive mode (prompts for name)
vibey roadmap init

# Specify all options
vibey roadmap init --name "My Project Roadmap" --version "1.0.0"
```

**Creates:**
- `.vibey/roadmap/roadmap.yaml` - Main roadmap file
- `.vibey/roadmap/` - Directory structure for tracks and sprints

**Exit Codes:**
- `0` - Success
- `1` - Error (already exists, invalid parameters, etc.)

---

### `vibey roadmap status`

Show roadmap status with track, sprint, and task progress.

**Usage:**
```bash
vibey roadmap status [OPTIONS]
```

**Options:**
| Option | Description | Required |
|--------|-------------|----------|
| `--track TEXT` | Show status for specific track only | No |
| `--sprint TEXT` | Show status for specific sprint only | No |

**Output Format:**

Without options, shows high-level overview:
```
Vibey Framework Roadmap
Status: 🔵 In Progress
Progress: 46% (97/212 tasks completed)

Tracks:
  ✅ core-framework           20/20 tasks
  🔵 roadmap-integration      16/16 tasks
  ⚪ interface-unification    0/17 tasks
```

With `--track`:
```
Track: core-framework
Status: ✅ Completed
Progress: 100% (20/20 tasks)

Sprints:
  ✅ core-framework-1: Foundation (10 tasks)
  ✅ core-framework-2: Integration (10 tasks)
```

With `--sprint`:
```
Sprint: core-framework-1
Status: ✅ Completed
Duration: 2 weeks (actual: 1.5 weeks)
Progress: 100% (10/10 tasks)

Tasks:
  ✅ core-framework-1-task-001: Initialize project structure
  ✅ core-framework-1-task-002: Create base models
  ...
```

**Examples:**
```bash
# Show overall roadmap status
vibey roadmap status

# Show specific track
vibey roadmap status --track core-framework

# Show specific sprint
vibey roadmap status --sprint core-framework-1
```

**Exit Codes:**
- `0` - Success
- `1` - Error (roadmap not found, invalid track/sprint ID)

---

### `vibey roadmap show`

Show detailed information for a specific track, sprint, or task.

**Usage:**
```bash
vibey roadmap show ITEM_ID
```

**Arguments:**
| Argument | Description | Format |
|----------|-------------|--------|
| `ITEM_ID` | ID of track, sprint, or task to show | `track-id`, `sprint-id`, or `task-id` |

**Item ID Formats:**
- **Track:** `core-framework`
- **Sprint:** `core-framework-1`
- **Task:** `core-framework-1-task-001`

**Output Includes:**
- Full details (name, description, status, dates)
- Progress metrics
- Dependencies and blockers
- Quality gates (if applicable)
- Assigned agents
- Deliverables
- Git commits (for tasks)

**Examples:**
```bash
# Show track details
vibey roadmap show core-framework

# Show sprint details
vibey roadmap show core-framework-1

# Show task details
vibey roadmap show core-framework-1-task-001
```

**Exit Codes:**
- `0` - Success
- `1` - Error (item not found, invalid ID format)

---

### `vibey roadmap start`

Start a sprint or task (transitions status to `in_progress`).

**Usage:**
```bash
vibey roadmap start ITEM_ID
```

**Arguments:**
| Argument | Description | Format |
|----------|-------------|--------|
| `ITEM_ID` | ID of sprint or task to start | `sprint-id` or `task-id` |

**Behavior:**
- Sets status to `in_progress`
- Records start timestamp
- Checks for blockers (fails if blocked)
- **Idempotent**: Returns success if already in progress

**Examples:**
```bash
# Start a sprint
vibey roadmap start core-framework-1

# Start a task
vibey roadmap start core-framework-1-task-001
```

**Exit Codes:**
- `0` - Success (started or already in progress)
- `1` - Error (not found, blocked, invalid state transition)

**Error Messages:**
```
❌ Cannot start sprint: blocked by dependencies
   Required: roadmap-system (status: not_started, needs: completed)

✅ Sprint already in progress (idempotent success)
```

---

### `vibey roadmap complete`

Complete a sprint or task (transitions status to `completed`).

**Usage:**
```bash
vibey roadmap complete ITEM_ID
```

**Arguments:**
| Argument | Description | Format |
|----------|-------------|--------|
| `ITEM_ID` | ID of sprint or task to complete | `sprint-id` or `task-id` |

**Behavior:**
- Sets status to `completed`
- Records completion timestamp
- Runs quality gates (if defined)
- Updates parent progress counters
- **Idempotent**: Returns success if already completed

**Quality Gate Validation:**
If quality gates are defined, they must pass before completion:
```
Running quality gates...
  ✅ Test Coverage: 95% (threshold: 90%)
  ✅ Documentation: 100% (threshold: 100%)
  ❌ Security Scan: 75% (threshold: 80%)

❌ Cannot complete: 1 quality gate failed
```

**Examples:**
```bash
# Complete a task
vibey roadmap complete core-framework-1-task-001

# Complete a sprint
vibey roadmap complete core-framework-1
```

**Exit Codes:**
- `0` - Success (completed or already completed)
- `1` - Error (not found, quality gates failed, invalid state)

---

### `vibey roadmap context`

Generate AI-optimized context for a task (dependencies, related code, blockers).

**Usage:**
```bash
vibey roadmap context TASK_ID
```

**Arguments:**
| Argument | Description | Format |
|----------|-------------|--------|
| `TASK_ID` | ID of task to get context for | `task-id` |

**Output Includes:**
- Task description and acceptance criteria
- Dependency chain (what this task depends on)
- Related tasks and sprints
- Blocker information
- Files to modify (if specified)
- Quality requirements
- Git commits associated with task

**Output Format:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Task: Implement unified error handling
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Description:
  Create vibey/common/errors.py with comprehensive
  error types and renderer system.

Dependencies:
  📎 interface-unification-1-task-001 (✅ completed)
  📎 interface-unification-1-task-002 (✅ completed)

📝 Files to modify:
   - vibey/common/errors.py (create new)
   - vibey/cli/commands.py

✅ Quality requirements:
   - All error types inherit from VibeyError
   - Each error has actionable fix_suggestions
   - >90% test coverage for error handling
```

**Use Cases:**
- **AI Agent Context**: Feed this to AI coding assistants
- **Developer Onboarding**: Understand task requirements
- **Dependency Analysis**: See what's blocking or related

**Examples:**
```bash
# Get context for current task
vibey roadmap context core-framework-1-task-003

# Pipe to file for AI agent
vibey roadmap context task-005 > task-context.md
```

**Exit Codes:**
- `0` - Success
- `1` - Error (task not found, invalid ID)

---

### `vibey roadmap summarize`

Generate a summary of a sprint, task, or track (completion report).

**Usage:**
```bash
vibey roadmap summarize ITEM_TYPE ITEM_ID
```

**Arguments:**
| Argument | Description | Values |
|----------|-------------|--------|
| `ITEM_TYPE` | Type of item to summarize | `sprint`, `task`, `track` |
| `ITEM_ID` | ID of the item | ID string |

**Output:**
Generates a markdown summary including:
- What was accomplished
- Key deliverables
- Challenges encountered
- Metrics (duration, task count)
- Next steps

**Summary Location:**
- **Sprint:** `.vibey/roadmap/TRACK/SPRINT/SUMMARY.md`
- **Task:** `.vibey/roadmap/TRACK/SPRINT/tasks/TASK_SUMMARY.md`
- **Track:** `.vibey/roadmap/TRACK/TRACK_SUMMARY.md`

**Examples:**
```bash
# Summarize a completed sprint
vibey roadmap summarize sprint core-framework-1

# Summarize a task
vibey roadmap summarize task core-framework-1-task-001

# Summarize entire track
vibey roadmap summarize track core-framework
```

**Exit Codes:**
- `0` - Success (summary generated)
- `1` - Error (item not found, not completed)

---

### `vibey roadmap add-commit`

Associate a git commit with a task (for tracking implementation).

**Usage:**
```bash
vibey roadmap add-commit TASK_ID [COMMIT_SHA] [OPTIONS]
```

**Arguments:**
| Argument | Description | Required |
|----------|-------------|----------|
| `TASK_ID` | ID of task to add commit to | Yes |
| `COMMIT_SHA` | Git commit SHA (full or short) | No if `--auto` |

**Options:**
| Option | Description |
|--------|-------------|
| `--auto` | Use current HEAD commit automatically |

**Behavior:**
- Validates commit exists in git history
- Stores commit SHA in task metadata
- Supports multiple commits per task
- Used for task completion tracking

**Examples:**
```bash
# Add specific commit
vibey roadmap add-commit task-001 a4f7bc3

# Add current HEAD commit
vibey roadmap add-commit task-001 --auto

# After making changes and committing
git commit -m "Implement feature X"
vibey roadmap add-commit task-001 --auto
```

**Exit Codes:**
- `0` - Success
- `1` - Error (task not found, invalid commit, not a git repo)

---

## Deploy Commands

Deploy the Vibey framework to target AI coding assistant platforms.

### `vibey deploy run`

Deploy framework files to a specific platform.

**Usage:**
```bash
vibey deploy run --platform PLATFORM [OPTIONS]
```

**Options:**
| Option | Description | Required | Values |
|--------|-------------|----------|--------|
| `--platform` | Target platform | Yes | `claude-code`, `goose`, `all` |
| `--clean` | Remove existing deployment first | No | Flag |
| `--no-validate` | Skip post-deployment validation | No | Flag |

**Supported Platforms:**
- **`claude-code`** - Claude Code (`.claude/` directory)
- **`goose`** - Goose by Block (`.goose/` directory)
- **`all`** - Deploy to all supported platforms

**Deployment Process:**
1. **Pre-flight checks** - Validates source files
2. **Backup** - Creates backup of existing deployment (if `--clean`)
3. **Copy files** - Deploys framework files to platform directory
4. **Validation** - Verifies deployment (unless `--no-validate`)
5. **Post-deploy** - Shows deployment summary

**Examples:**
```bash
# Deploy to Claude Code
vibey deploy run --platform claude-code

# Deploy to Goose with clean install
vibey deploy run --platform goose --clean

# Deploy to all platforms
vibey deploy run --platform all

# Deploy without validation (faster)
vibey deploy run --platform claude-code --no-validate
```

**Exit Codes:**
- `0` - Success
- `1` - Error (pre-flight failed, copy failed, validation failed)

**Output:**
```
🚀 Deploying Vibey Framework to claude-code...

Pre-flight checks:
  ✅ Source files valid
  ✅ Configuration valid
  ✅ Target directory writable

Deployment:
  📁 Created .claude/ directory
  📄 Copied 45 files (2.3 MB)
  ✅ Deployment complete

Validation:
  ✅ All files present
  ✅ Configuration valid
  ✅ Framework ready

✨ Deployment successful!
```

---

### `vibey deploy list`

List all available deployment platforms and their status.

**Usage:**
```bash
vibey deploy list
```

**Output:**
```
Available Platforms:

  claude-code       ✅ Ready      .claude/ directory
  goose             ✅ Ready      .goose/ directory
  cursor            🚧 Planned    Coming Q2 2025
  aider             🚧 Planned    Coming Q2 2025
  continue          🚧 Planned    Coming Q3 2025
```

**Exit Codes:**
- `0` - Always succeeds

---

## Docs Commands

Generate and manage framework documentation.

### `vibey docs generate`

Generate documentation from roadmap and configuration.

**Usage:**
```bash
vibey docs generate [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--overwrite` | Overwrite existing documentation | No (skip existing) |

**Generated Documentation:**
- Roadmap documentation (`.vibey/roadmap/roadmap.md`)
- Track summaries (per-track markdown)
- Sprint summaries (per-sprint markdown)
- API documentation (if configured)
- Configuration reference

**Examples:**
```bash
# Generate all docs (skip existing)
vibey docs generate

# Regenerate all docs
vibey docs generate --overwrite
```

**Exit Codes:**
- `0` - Success
- `1` - Error (roadmap not found, permission denied)

**Output:**
```
📚 Generating documentation...

  ✅ Roadmap overview (.vibey/roadmap/roadmap.md)
  ✅ Track documentation (5 tracks)
  ✅ Sprint summaries (12 sprints)
  ⏭️  API docs (3 existing, skipped)

✨ Documentation generated successfully!

To regenerate existing docs, use --overwrite
```

---

## Config Commands

Manage framework configuration files.

### `vibey config show`

Display current configuration (modular format).

**Usage:**
```bash
vibey config show
```

**Output:**
Shows all configuration sections:
- Project configuration (`.vibey/config/project.yaml`)
- Framework configuration (`.vibey/config/framework.yaml`)
- Agent preferences (`.vibey/config/agents.yaml`)
- Quality gates (`.vibey/config/quality-gates.yaml`)

**Example Output:**
```yaml
Project Configuration:
  name: vibey-framework
  version: 2.5.0
  type: python-library

Framework Configuration:
  orchestration_mode: balanced
  default_agent: web-developer

Agent Preferences:
  web-developer: enabled
  test-engineer: enabled

Quality Gates:
  test_coverage: 90%
  security_scan: enabled
```

**Exit Codes:**
- `0` - Success
- `1` - Error (config not found)

---

### `vibey config validate`

Validate all configuration files against schemas.

**Usage:**
```bash
vibey config validate
```

**Validation Checks:**
- YAML syntax validity
- Required fields present
- Value types correct
- Cross-references valid (agent IDs, etc.)

**Example Output:**
```
Validating configuration files...

  ✅ project.yaml (valid)
  ✅ framework.yaml (valid)
  ✅ agents.yaml (valid)
  ❌ quality-gates.yaml (2 errors)
     - Line 12: Invalid threshold value (must be 0-100)
     - Line 18: Unknown gate type 'custom_gate'

❌ Validation failed: 2 errors found
```

**Exit Codes:**
- `0` - All valid
- `1` - Validation errors found

---

### `vibey config migrate`

Migrate legacy monolithic config to modular format.

**Usage:**
```bash
vibey config migrate [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--backup/--no-backup` | Create backup before migration | Yes |
| `--dry-run` | Show what would be migrated | No (actually migrate) |
| `--force` | Overwrite existing modular config | No (fail if exists) |

**Migration Process:**
1. Detects legacy config (`.vibey/project-config.yaml`)
2. Creates backup (unless `--no-backup`)
3. Splits into modular files:
   - `config/project.yaml`
   - `config/framework.yaml`
   - `config/agents.yaml`
   - `config/quality-gates.yaml`
4. Validates migrated config
5. Archives legacy config (moves to `.vibey/config-backups/`)

**Examples:**
```bash
# Dry run to preview migration
vibey config migrate --dry-run

# Migrate with backup (default)
vibey config migrate

# Migrate without backup
vibey config migrate --no-backup

# Force overwrite existing modular config
vibey config migrate --force
```

**Exit Codes:**
- `0` - Success
- `1` - Error (no legacy config, migration failed)

---

### `vibey config rollback`

Rollback to a previous configuration backup.

**Usage:**
```bash
vibey config rollback [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--backup-id TEXT` | Specific backup timestamp to restore | Latest |
| `--list` | List available backups | No (perform rollback) |

**Backup ID Format:** `YYYYMMDD-HHMMSS` (e.g., `20251112-143000`)

**Examples:**
```bash
# List available backups
vibey config rollback --list

# Rollback to latest backup
vibey config rollback

# Rollback to specific backup
vibey config rollback --backup-id 20251112-143000
```

**Example List Output:**
```
Available Configuration Backups:

  20251112-143000  (2 hours ago)  - Latest
  20251111-090000  (1 day ago)
  20251110-153000  (2 days ago)

To rollback: vibey config rollback --backup-id TIMESTAMP
```

**Exit Codes:**
- `0` - Success
- `1` - Error (no backups found, invalid backup ID)

---

## Exit Codes

All Vibey CLI commands follow standard Unix exit code conventions:

| Code | Meaning | Usage |
|------|---------|-------|
| `0` | Success | Command completed successfully |
| `1` | Error | Command failed (see error message) |
| `130` | Interrupted | User interrupted with Ctrl+C |

**In Scripts:**
```bash
#!/bin/bash

# Check exit code
vibey roadmap status
if [ $? -eq 0 ]; then
  echo "Roadmap is healthy"
else
  echo "Roadmap has issues"
  exit 1
fi

# Use with && and ||
vibey roadmap start task-001 && echo "Started successfully"
vibey roadmap complete task-001 || echo "Completion failed"
```

---

## Common Workflows

### Starting a New Project

```bash
# 1. Initialize roadmap
vibey roadmap init --name "My Project" --version "1.0.0"

# 2. Check status
vibey roadmap status

# 3. Deploy to platform
vibey deploy run --platform claude-code

# 4. Validate everything
vibey config validate
```

### Working on a Task

```bash
# 1. Get task context
vibey roadmap context sprint-1-task-001

# 2. Start the task
vibey roadmap start sprint-1-task-001

# 3. Do work, make commits
git commit -m "Implement feature X"

# 4. Link commit to task
vibey roadmap add-commit sprint-1-task-001 --auto

# 5. Complete task
vibey roadmap complete sprint-1-task-001
```

### Sprint Completion

```bash
# 1. Check sprint progress
vibey roadmap status --sprint sprint-1

# 2. Complete all tasks
vibey roadmap complete sprint-1-task-001
vibey roadmap complete sprint-1-task-002
# ... etc

# 3. Complete sprint
vibey roadmap complete sprint-1

# 4. Generate summary
vibey roadmap summarize sprint sprint-1

# 5. Start next sprint
vibey roadmap start sprint-2
```

### Configuration Management

```bash
# 1. Show current config
vibey config show

# 2. Validate config
vibey config validate

# 3. Make changes (edit files)
vim .vibey/config/framework.yaml

# 4. Validate again
vibey config validate

# 5. If issues, rollback
vibey config rollback
```

---

## Troubleshooting

### Command Not Found

**Issue:** `vibey: command not found`

**Solutions:**
```bash
# Ensure installed
pip install -e .

# Check PATH
echo $PATH

# Use python module form
python -m vibey.cli roadmap status
```

---

### Roadmap Not Found

**Issue:** `Error: Roadmap not found`

**Solutions:**
```bash
# Verify you're in project root
pwd
ls .vibey/

# Initialize if missing
vibey roadmap init

# Check .vibey/ structure
tree .vibey/
```

---

### Permission Denied

**Issue:** `Error: Permission denied writing to .vibey/`

**Solutions:**
```bash
# Check permissions
ls -la .vibey/

# Fix ownership
sudo chown -R $USER .vibey/

# Fix permissions
chmod -R u+rw .vibey/
```

---

### Git Commit Not Found

**Issue:** `Error: Commit a4f7bc3 not found in repository`

**Solutions:**
```bash
# Verify commit exists
git log --oneline | grep a4f7bc3

# Use full SHA
git log --format="%H" -n 1
vibey roadmap add-commit task-001 <full-sha>

# Or use --auto for HEAD
vibey roadmap add-commit task-001 --auto
```

---

### Quality Gates Failing

**Issue:** `Cannot complete: quality gate 'Test Coverage' failed (85% < 90%)`

**Solutions:**
```bash
# Check specific gate requirements
vibey roadmap show sprint-1

# Run tests to improve coverage
pytest --cov

# Adjust thresholds if reasonable
vim .vibey/config/quality-gates.yaml

# Re-validate
vibey config validate
```

---

## Environment Variables

The Vibey CLI respects the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `VIBEY_ROOT` | Override project root directory | Current directory |
| `VIBEY_CONFIG_PATH` | Custom config location | `.vibey/config/` |
| `NO_COLOR` | Disable colored output | Not set (colors enabled) |
| `VIBEY_VERBOSE` | Enable verbose logging | Not set |

**Examples:**
```bash
# Custom project root
VIBEY_ROOT=/path/to/project vibey roadmap status

# Disable colors for piping
NO_COLOR=1 vibey roadmap show task-001 | less

# Verbose logging
VIBEY_VERBOSE=1 vibey deploy run --platform goose
```

---

## Shell Completion

### Bash

Add to `~/.bashrc`:
```bash
eval "$(_VIBEY_COMPLETE=bash_source vibey)"
```

### Zsh

Add to `~/.zshrc`:
```bash
eval "$(_VIBEY_COMPLETE=zsh_source vibey)"
```

### Fish

Add to `~/.config/fish/completions/vibey.fish`:
```fish
eval (env _VIBEY_COMPLETE=fish_source vibey)
```

---

## Getting Help

### In-CLI Help

```bash
# Top-level help
vibey --help

# Command group help
vibey roadmap --help
vibey deploy --help

# Specific command help
vibey roadmap start --help
vibey config migrate --help
```

### External Resources

- **Documentation:** https://docs.vibey.dev
- **GitHub Issues:** https://github.com/your-org/vibey/issues
- **Discussions:** https://github.com/your-org/vibey/discussions
- **Changelog:** https://github.com/your-org/vibey/blob/main/CHANGELOG.md

---

## Version History

### 2.5.0 (Current)
- Interface unification (deleted slash commands)
- Unified error handling system
- Modular configuration support
- Improved roadmap CLI commands

### 2.4.0
- Added `roadmap add-commit` command
- Added `roadmap summarize` command
- Improved validation and error messages

### 2.3.0
- Added config migration tools
- Added deployment validation
- Enhanced status output with rich formatting

### 2.0.0
- Initial unified CLI release
- Replaced standalone scripts with CLI commands
- Added Click-based command structure

---

**Last Updated:** 2025-11-12
**Maintained By:** Vibey Framework Team
**License:** MIT
