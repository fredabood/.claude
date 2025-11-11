# Vibey CLI Usage Guide

**Version:** 2.5.0
**Package:** vibey-framework

This guide covers the `vibey` command-line interface for the Vibey Agent Framework.

---

## Installation

```bash
# Install from source (development)
pip install -e .

# Install from PyPI (when published)
pip install vibey-framework
```

---

## Quick Start

```bash
# Show version
vibey --version

# Show help
vibey --help

# Initialize a new roadmap
vibey roadmap init

# Show roadmap status
vibey roadmap status

# Deploy to Claude Code
vibey deploy run --platform claude-code
```

---

## Global Options

Available on all commands:

```bash
vibey [OPTIONS] COMMAND [ARGS]...

Options:
  --version      Show the version and exit
  -v, --verbose  Enable verbose output
  -q, --quiet    Suppress non-essential output
  --help         Show this message and exit
```

---

## Command Groups

### Roadmap Commands

Manage roadmap system - tracks, sprints, tasks, and dependencies.

```bash
vibey roadmap [COMMAND] [OPTIONS]
```

#### Initialize Roadmap

```bash
vibey roadmap init
vibey roadmap init --name "My Project" --version "1.0.0"
```

#### Show Status

```bash
# Show overall roadmap status
vibey roadmap status

# Show specific track status
vibey roadmap status --track directory-migration

# Show specific sprint status
vibey roadmap status --sprint directory-migration-1
```

#### Show Details

```bash
# Show task details
vibey roadmap show directory-migration-1-task-001

# Show sprint details
vibey roadmap show directory-migration-1

# Show track details
vibey roadmap show directory-migration
```

#### Start Items

```bash
# Start a task
vibey roadmap start directory-migration-1-task-001

# Start a sprint
vibey roadmap start directory-migration-1
```

#### Complete Items

```bash
# Complete a task
vibey roadmap complete directory-migration-1-task-001

# Complete a sprint
vibey roadmap complete directory-migration-1
```

#### Get Context

```bash
# Get AI-optimized context for a task
vibey roadmap context directory-migration-1-task-001
```

#### Summarize

```bash
# Summarize a sprint
vibey roadmap summarize sprint directory-migration-1

# Summarize a task
vibey roadmap summarize task directory-migration-1-task-001

# Summarize a track
vibey roadmap summarize track directory-migration
```

---

### Deploy Commands

Deploy framework to target platforms.

```bash
vibey deploy [COMMAND] [OPTIONS]
```

#### Deploy to Platform

```bash
# Deploy to Claude Code
vibey deploy run --platform claude-code

# Deploy with clean install
vibey deploy run --platform claude-code --clean

# Deploy to Goose (when implemented)
vibey deploy run --platform goose
```

**Available Platforms:**
- `claude-code` - Claude Code (current, fully functional)
- `goose` - Goose by Block (in development)
- `cursor` - Cursor IDE (planned)
- `aider` - Aider CLI (planned)
- `continue` - Continue.dev (planned)

#### List Platforms

```bash
# Show all available platforms
vibey deploy list-platforms
```

---

### Docs Commands

Generate and manage documentation.

```bash
vibey docs [COMMAND] [OPTIONS]
```

#### Generate Documentation

```bash
# Generate all docs from configuration
vibey docs generate

# Overwrite existing docs
vibey docs generate --overwrite
```

---

### Config Commands

Manage framework configuration.

```bash
vibey config [COMMAND] [OPTIONS]
```

#### Show Configuration

```bash
# Display current configuration
vibey config show
```

#### Validate Configuration

```bash
# Validate all config files
vibey config validate
```

---

## Examples

### Complete Workflow

```bash
# 1. Initialize roadmap
vibey roadmap init --name "My Project"

# 2. Check status
vibey roadmap status

# 3. Start first sprint
vibey roadmap start my-project-1

# 4. Start first task
vibey roadmap start my-project-1-task-001

# 5. Complete task when done
vibey roadmap complete my-project-1-task-001

# 6. Complete sprint
vibey roadmap complete my-project-1

# 7. Generate documentation
vibey docs generate

# 8. Deploy to platform
vibey deploy run --platform claude-code
```

### Development Workflow

```bash
# Work on a specific task
vibey roadmap show my-task-001        # Review task details
vibey roadmap context my-task-001     # Get AI context
vibey roadmap start my-task-001       # Start working
# ... do the work ...
vibey roadmap complete my-task-001    # Mark complete

# Review progress
vibey roadmap status                  # Check overall status
vibey roadmap summarize sprint my-sprint  # Get sprint summary
```

---

## Entry Points

The vibey CLI can be invoked in two ways:

### Direct Command

```bash
vibey --version
```

Uses the installed console script at `/usr/local/bin/vibey` (or similar).

### Python Module

```bash
python -m vibey --version
python3 -m vibey --version
```

Runs the package as a module.

Both methods are functionally identical.

---

## Environment

### Working Directory

All commands execute in your current working directory. The vibey CLI will search upward for `.vibey/` directories to find the roadmap root.

```bash
cd /path/to/project
vibey roadmap status  # Finds /path/to/project/.vibey/
```

### Python Version

Requires Python 3.9 or higher.

```bash
python3 --version  # Should be >= 3.9
```

---

## Troubleshooting

### Command Not Found

```bash
vibey: command not found
```

**Solution:** Ensure the package is installed and in your PATH:

```bash
pip install --upgrade vibey-framework
which vibey  # Should show the installation path
```

### Import Errors

```bash
ModuleNotFoundError: No module named 'vibey'
```

**Solution:** Reinstall the package:

```bash
pip uninstall vibey-framework
pip install vibey-framework
```

### Permission Errors

```bash
PermissionError: [Errno 13] Permission denied
```

**Solution:** Use `--user` flag or virtual environment:

```bash
pip install --user vibey-framework
# or
python -m venv .venv
source .venv/bin/activate
pip install vibey-framework
```

---

## Advanced Usage

### Scripting

The vibey CLI can be used in shell scripts:

```bash
#!/bin/bash
set -e

# Start all tasks in a sprint
for task in task-001 task-002 task-003; do
  vibey roadmap start "my-sprint-$task"
done

# Check if roadmap is complete
if vibey roadmap status --sprint my-sprint | grep -q "100%"; then
  echo "Sprint complete!"
fi
```

### Automation

Integrate with CI/CD:

```yaml
# GitHub Actions example
- name: Complete task
  run: |
    vibey roadmap complete ${{ github.event.issue.title }}
```

---

## Getting Help

### Command-Specific Help

```bash
vibey roadmap --help
vibey deploy --help
vibey docs --help
vibey config --help
```

### Subcommand Help

```bash
vibey roadmap start --help
vibey deploy run --help
```

### Documentation

- [README.md](../README.md) - Main documentation
- [CLI_USAGE.md](CLI_USAGE.md) - This file
- [API Reference](reference/) - Full API reference

---

**Version:** 2.5.0
**Last Updated:** 2025-11-10
