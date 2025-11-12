# Git Commit Tracking in Roadmap System

**Purpose:** Associate git commits with roadmap tasks for traceability and history tracking.

**Status:** ✅ Implemented (2025-11-11)

---

## Overview

The roadmap system now supports tracking git commits associated with each task. This enables:

- **Traceability**: See which code changes are related to which tasks
- **History**: Track the evolution of work through git history
- **Auditing**: Verify that tasks have been completed with actual code changes
- **Context**: Understand what was done for a task by reviewing commit messages

---

## Data Model

Each task has a `commits` field containing an array of git commit objects:

```yaml
task:
  id: infrastructure-fixes-1-task-005
  # ... other fields ...
  commits:
    - sha: 40c760091cb87cb8afc2edbd291469766d942858
      message: 'fix: Phase 2 - Parallel agent deployment resolves all test and doc issues'
      author: '@fredabood <fredabood@gmail.com>'
      date: '2025-11-11T16:15:17-05:00'
    - sha: f0711771465374cabeac87f4809e005f07ac7aa1
      message: 'fix: Comprehensive audit and critical fixes - eliminate deprecated API usage'
      author: '@fredabood <fredabood@gmail.com>'
      date: '2025-11-11T16:01:52-05:00'
```

### Commit Object Fields

- **sha** (string): Full git commit SHA (40 characters)
- **message** (string): Commit message (first line only)
- **author** (string): Author name and email in git format: `Name <email>`
- **date** (ISO 8601 string): Commit date in ISO 8601 format with timezone

---

## CLI Usage

### Add Current Commit to Task

Associate the current HEAD commit with a task:

```bash
vibey roadmap add-commit <task-id> --auto
```

**Example:**
```bash
vibey roadmap add-commit infrastructure-fixes-1-task-005 --auto
```

**Output:**
```
🔍 Auto-detected current commit: 40c76009
✅ Successfully added commit to task infrastructure-fixes-1-task-005
   Commit: 40c76009
   Message: fix: Phase 2 - Parallel agent deployment resolves all test and doc issues
   Author: @fredabood <fredabood@gmail.com>
   Date: 2025-11-11 16:15:17
   Total commits for this task: 1
```

### Add Specific Commit by SHA

Associate a specific commit (full or short SHA):

```bash
vibey roadmap add-commit <task-id> <commit-sha>
```

**Examples:**
```bash
# Using short SHA
vibey roadmap add-commit infrastructure-fixes-1-task-005 f071177

# Using full SHA
vibey roadmap add-commit infrastructure-fixes-1-task-005 f0711771465374cabeac87f4809e005f07ac7aa1
```

**Output:**
```
✅ Successfully added commit to task infrastructure-fixes-1-task-005
   Commit: f0711771
   Message: fix: Comprehensive audit and critical fixes - eliminate deprecated API usage
   Author: @fredabood <fredabood@gmail.com>
   Date: 2025-11-11 16:01:52
   Total commits for this task: 2
```

### Duplicate Detection

The system automatically detects if a commit is already associated with a task:

```bash
vibey roadmap add-commit infrastructure-fixes-1-task-005 40c7600
```

**Output:**
```
⚠️  Warning: Commit 40c76009 already associated with task infrastructure-fixes-1-task-005
   Message: fix: Phase 2 - Parallel agent deployment resolves all test and doc issues
```

---

## Command Reference

### `vibey roadmap add-commit`

**Syntax:**
```
vibey roadmap add-commit <task-id> [<commit-sha>] [--auto]
```

**Arguments:**
- `task-id` (required): Task ID in format `<track>-<sprint>-task-<number>`
- `commit-sha` (optional): Git commit SHA (full or short form)

**Options:**
- `--auto`: Use current HEAD commit (alternative to passing `commit-sha`)
- `--vibey-dir PATH`: Path to .vibey directory (auto-detected if not provided)

**Requirements:**
- Must be run from within a Vibey-managed project (has `.vibey/` directory)
- Must be run from within a git repository
- Commit SHA must exist in the repository

**Exit Codes:**
- `0`: Success
- `1`: Error (invalid arguments, task not found, commit not found, etc.)

---

## Workflow Examples

### Scenario 1: Complete a Task and Track the Commit

```bash
# 1. Make code changes
vim vibey/cli/roadmap-add-commit.py

# 2. Commit changes
git add vibey/cli/roadmap-add-commit.py
git commit -m "feat: Implement git commit tracking for roadmap tasks"

# 3. Associate commit with task
vibey roadmap add-commit roadmap-system-1-task-012 --auto

# 4. Complete the task
vibey roadmap complete roadmap-system-1-task-012
```

### Scenario 2: Retroactively Add Commits to Tasks

```bash
# Review git history
git log --oneline -10

# Add relevant commits to tasks
vibey roadmap add-commit infrastructure-fixes-1-task-001 4367bc8
vibey roadmap add-commit infrastructure-fixes-1-task-002 e58208d
vibey roadmap add-commit infrastructure-fixes-1-task-003 495592a
```

### Scenario 3: Track Multiple Commits for One Task

```bash
# Add first commit
vibey roadmap add-commit feature-dev-1-task-005 abc1234

# Make more changes
vim src/feature.py
git add src/feature.py
git commit -m "feat: Additional feature improvements"

# Add second commit
vibey roadmap add-commit feature-dev-1-task-005 --auto
```

---

## Implementation Details

### File Location

- **Script:** `vibey/cli/roadmap-add-commit.py`
- **Command wrapper:** `vibey/cli/commands.py::roadmap_add_commit_cmd()`
- **CLI entry point:** `vibey/cli/main.py::roadmap_add_commit()`

### How It Works

1. **Commit Detection:** Uses `git rev-parse` to resolve short SHAs to full SHAs
2. **Commit Info Extraction:** Uses `git log` to extract commit message, author, and date
3. **Task Location:** Searches `.vibey/roadmap/{track}/{sprint}/{task}/task.yaml`
4. **Atomic Update:** Reads task YAML, appends commit, updates metadata, writes back
5. **Duplicate Prevention:** Checks existing commits array before adding

### Data Storage

Commits are stored in the task's `task.yaml` file in the `commits` array field. The file maintains the full task data structure with the commits array appended/updated.

---

## Future Enhancements

### Potential Features

1. **Automatic Tracking**: Git hooks to automatically associate commits with tasks
2. **Commit Parsing**: Extract task IDs from commit messages (e.g., `[task-005]`)
3. **Bulk Operations**: Add multiple commits at once
4. **Commit Removal**: Remove incorrectly associated commits
5. **Statistics**: Show commit statistics per task/sprint/track
6. **Integration with `vibey roadmap show`**: Display associated commits when showing task details

### Git Hook Example (Future)

```bash
# .git/hooks/commit-msg
#!/bin/bash
# Extract task ID from commit message
TASK_ID=$(grep -oE 'task-[0-9]+' $1 | head -1)

if [ -n "$TASK_ID" ]; then
  # Associate commit with task (after commit is created)
  git log -1 --format="%H" | xargs vibey roadmap add-commit "$TASK_ID"
fi
```

---

## Troubleshooting

### Error: "Could not find .vibey/roadmap.yaml"

**Cause:** Not in a Vibey-managed project or not in project root

**Solution:**
```bash
# Navigate to project root
cd /path/to/vibey/project

# Or specify vibey-dir
vibey roadmap add-commit task-005 abc1234 --vibey-dir /path/to/.vibey
```

### Error: "Could not find commit 'abc1234'"

**Cause:** Commit SHA doesn't exist in repository

**Solution:**
```bash
# Check git history
git log --oneline

# Use correct SHA
vibey roadmap add-commit task-005 <correct-sha>
```

### Error: "Task file not found: task-005"

**Cause:** Invalid task ID or task doesn't exist

**Solution:**
```bash
# List available tasks
vibey roadmap status

# Use correct task ID format: <track>-<sprint>-task-<number>
vibey roadmap add-commit infrastructure-fixes-1-task-005 abc1234
```

---

## Related Commands

- `vibey roadmap status` - Show roadmap status (could display commits in future)
- `vibey roadmap show <task-id>` - Show task details (could display commits in future)
- `vibey roadmap complete <task-id>` - Complete a task
- `git log` - View git commit history

---

**Documentation Version:** 1.0
**Last Updated:** 2025-11-11
**Status:** ✅ Feature implemented and tested
