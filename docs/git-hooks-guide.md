# Git Hooks Guide

Complete guide to using Vibey's Git hooks for roadmap integration.

**Task:** git-integration-2-task-008

## Table of Contents

- [Quick Start](#quick-start)
- [Hook Reference](#hook-reference)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Examples](#examples)

---

## Quick Start

### Installation

Install Vibey git hooks in your repository:

```bash
vibey git hooks install
```

This installs:
- **pre-commit** - Validates roadmap YAML files before commit
- **commit-msg** - Validates commit message format and task references

### Basic Configuration

Create or edit `.vibey/config/git.yaml`:

```yaml
git:
  enforcement:
    mode: advisory  # Options: off, advisory, blocking, audit

    rules:
      yaml_integrity:
        enabled: true
        mode: blocking  # Always block invalid YAML

      task_reference:
        enabled: true
        require_valid_id: false
        mode: advisory

    audit:
      enabled: false
      file: .vibey/git-audit.log
```

### First Commit

Make a commit with proper task reference:

```bash
git add .
git commit -m "feat(task-001): implement new feature

Task: task-001
Status: in_progress"
```

The commit-msg hook will:
- ✅ Validate commit format
- ✅ Check task exists in roadmap
- ✅ Show task references found

---

## Hook Reference

### Pre-Commit Hook

**Purpose:** Validates roadmap files before allowing commit.

**What it checks:**
- ✅ YAML syntax in all `.vibey/roadmap/**/*.yaml` files
- ✅ Schema validity (sprint structure, task fields)
- ✅ Task status consistency
- ⚠️ CLI usage vs manual YAML edits (advisory)

**Exit behavior:**
- **Blocking mode:** Exit code 1 (blocks commit)
- **Advisory mode:** Exit code 0 (warns, allows commit)
- **Audit mode:** Logs violations, exit code 0

**Example output:**

```
[vibey] Pre-commit validation:
  ✓ All YAML files are valid
  ⚠ Manual YAML edit detected in sprint.yaml
    Suggestion: Use 'vibey roadmap update task task-001 --status completed'
```

### Commit-Msg Hook

**Purpose:** Validates commit message format and task references.

**What it checks:**
- ✅ Conventional commit format: `type(scope): description`
- ✅ Task references (in scope, footer, or brackets)
- ✅ Task exists in roadmap
- ⚠️ Missing task reference (if `require_valid_id: true`)

**Supported commit formats:**

1. **Conventional with task scope:**
   ```
   feat(task-001): implement feature
   ```

2. **With task footer:**
   ```
   feat: implement feature

   Task: task-001
   Status: completed
   ```

3. **With bracket reference:**
   ```
   feat: implement feature [task-001]
   ```

**Status keywords:**
- `Status: completed` → Mark task completed
- `Status: in_progress` → Mark task in progress
- `Status: blocked` → Mark task blocked

**Example output:**

```
[vibey] Commit-msg: ✓ Task references: task-001

⚠ Task 'task-002' not found in roadmap
  Suggestion: Did you mean: task-003, task-004?
```

### Automatic Status Updates

**Command:** `vibey git update-status`

**Purpose:** Automatically update task status based on commit messages.

**Usage:**

```bash
# Process last 10 commits
vibey git update-status

# Process last 50 commits
vibey git update-status --recent 50

# Specific commit
vibey git update-status --commit abc1234 --message "completes task-001"

# Preview changes (dry-run)
vibey git update-status --dry-run

# Force update even if already at status
vibey git update-status --force
```

**What it does:**
- Parses commit messages for status indicators
- Updates task status in YAML
- Records commit SHA in task's commits list
- Updates sprint progress automatically

---

## Configuration

### Enforcement Modes

Four modes control how hooks behave:

#### 1. **Off** - Disable all validation
```yaml
git:
  enforcement:
    mode: off
```
- Hooks exit immediately
- No validation performed
- Use for: Temporary bypass, CI environments

#### 2. **Advisory** (Recommended)
```yaml
git:
  enforcement:
    mode: advisory
```
- Validates and shows warnings
- Never blocks commits (exit code 0)
- Provides helpful suggestions
- **Use for:** Development, learning phase

#### 3. **Blocking** - Strict enforcement
```yaml
git:
  enforcement:
    mode: blocking
```
- Blocks commits on errors (exit code 1)
- Only warnings for advisory rules
- **Use for:** Production branches, release workflows

#### 4. **Audit** - Silent logging
```yaml
git:
  enforcement:
    mode: audit
```
- Logs all violations to audit file
- Never blocks or shows warnings
- **Use for:** Monitoring, analytics

### Per-Rule Configuration

Override mode for specific rules:

```yaml
git:
  enforcement:
    mode: advisory  # Global default

    rules:
      yaml_integrity:
        enabled: true
        mode: blocking  # Always block invalid YAML

      task_reference:
        enabled: true
        require_valid_id: false
        mode: advisory  # Just warn about missing refs

      cli_usage:
        enabled: true
        mode: advisory  # Suggest CLI commands
```

### Commit Tracking

Record commit evidence for tasks:

```yaml
git:
  commit_tracking:
    record_commits: true      # Store commit SHAs in YAML
    require_commits: false    # Require commits before marking complete
```

**When `require_commits: true`:**
- Hooks warn if marking task complete without commits
- Override with `--force` flag
- Useful for ensuring code evidence

### Audit Logging

Enable audit log for compliance:

```yaml
git:
  enforcement:
    audit:
      enabled: true
      file: .vibey/git-audit.log
```

**Log format (JSON lines):**
```json
{
  "timestamp": "2025-11-24T23:30:00Z",
  "hook": "commit-msg",
  "mode": "advisory",
  "task_references": ["task-001"],
  "has_task_reference": true,
  "issues_count": 0,
  "issues": []
}
```

### Bypass Procedures

#### Temporary bypass (one commit):
```bash
git commit --no-verify -m "emergency fix"
```

#### Environment variable bypass:
```bash
VIBEY_SKIP_HOOKS=1 git commit -m "skip hooks"
```

#### Disable hooks:
```bash
vibey git hooks uninstall
```

---

## Troubleshooting

### Common Errors

#### 1. "YAML syntax error in sprint.yaml"

**Cause:** Invalid YAML syntax in roadmap file

**Fix:**
```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('.vibey/roadmap/track/sprint/sprint.yaml'))"

# Or use Vibey validation
vibey roadmap validate
```

**Prevention:** Use CLI commands instead of manual YAML edits

#### 2. "Task 'task-001' not found in roadmap"

**Cause:** Referenced task doesn't exist

**Fix:**
- Check task ID spelling
- Ensure task exists: `vibey roadmap show task-001`
- Create task if needed: `vibey roadmap add task ...`

#### 3. "Could not read commit message"

**Cause:** Commit message file permissions or path issue

**Fix:**
```bash
# Check git hooks directory
ls -la .git/hooks/

# Reinstall hooks
vibey git hooks uninstall
vibey git hooks install
```

#### 4. "Python not found. Cannot run hook"

**Cause:** Python not in PATH or virtual environment not activated

**Fix:**
```bash
# Use system Python
which python3

# Or specify Python path in hook
export PYTHON=/usr/bin/python3
```

### Disabling Hooks Temporarily

#### For one commit:
```bash
git commit --no-verify
```

#### For multiple commits:
```bash
# Disable
export VIBEY_SKIP_HOOKS=1

# Make commits
git commit -m "commit 1"
git commit -m "commit 2"

# Re-enable
unset VIBEY_SKIP_HOOKS
```

#### For entire session:
```bash
vibey git hooks uninstall

# Do your work

vibey git hooks install
```

### Debug Mode

Enable detailed output:

```bash
# Set debug environment variable
export VIBEY_DEBUG=1

# Make commit (shows detailed hook execution)
git commit -m "debug commit"

# View audit log
cat .vibey/git-audit.log | jq .
```

---

## Best Practices

### Recommended Workflow

#### 1. **Development Phase** (Individual developers)

**Configuration:**
```yaml
git:
  enforcement:
    mode: advisory
    rules:
      yaml_integrity:
        mode: blocking  # Always block invalid YAML
```

**Workflow:**
1. Install hooks: `vibey git hooks install`
2. Make commits with task references
3. Review warnings but don't block
4. Learn proper formats gradually

#### 2. **Team Adoption** (Small team)

**Configuration:**
```yaml
git:
  enforcement:
    mode: advisory
    rules:
      yaml_integrity:
        mode: blocking
      task_reference:
        require_valid_id: true
        mode: advisory  # Warn about missing refs
```

**Workflow:**
1. Team installs hooks
2. Require task references (warn only)
3. Weekly review of audit logs
4. Gradually increase enforcement

#### 3. **Production** (Mature team)

**Configuration:**
```yaml
git:
  enforcement:
    mode: blocking
    rules:
      task_reference:
        require_valid_id: true
        mode: blocking
    audit:
      enabled: true
```

**Workflow:**
1. Strict enforcement on main/release branches
2. Advisory mode on feature branches
3. Automated status updates
4. Regular audit log reviews

### Commit Message Best Practices

#### ✅ Good commit messages:

```bash
# Clear task reference with status
git commit -m "feat(task-001): add user authentication

Task: task-001
Status: completed"

# Multiple tasks
git commit -m "refactor: update API endpoints

Tasks: task-001, task-002
Status: in_progress"

# Breaking change
git commit -m "feat(task-003)!: change API response format

BREAKING CHANGE: Response format changed from XML to JSON

Task: task-003"
```

#### ❌ Avoid:

```bash
# No task reference
git commit -m "fix stuff"

# Vague description
git commit -m "updates"

# Wrong task ID
git commit -m "feat(tsk-001): feature"
```

### Team Adoption Guide

#### Phase 1: Introduction (Week 1-2)
- Install hooks in advisory mode
- Team training on commit format
- No blocking, only warnings
- Collect feedback

#### Phase 2: Learning (Week 3-4)
- Require task references (advisory)
- Enable CLI usage suggestions
- Review common mistakes
- Update documentation

#### Phase 3: Enforcement (Week 5-6)
- Enable blocking for YAML integrity
- Advisory mode for task references
- Weekly audit log reviews
- Celebrate good adoption

#### Phase 4: Full Adoption (Week 7+)
- Blocking mode for critical rules
- Automated status updates
- Branch-task linking required
- Regular process improvements

### Branch Naming Strategy

Use consistent branch names for auto-detection:

```bash
# Task branches
git checkout -b task/task-001

# Sprint branches
git checkout -b sprint/sprint-2

# Track branches
git checkout -b track/user-journey-audit

# Benefits:
# - Auto-detect task from branch name
# - Generate PR descriptions automatically
# - Track branch lifecycle in roadmap
```

### PR Description Workflow

```bash
# 1. Create task branch
vibey git branch create task-001

# 2. Make commits
git commit -m "feat(task-001): implement feature

Task: task-001
Status: completed"

# 3. Generate PR description
vibey git pr-description > pr-body.md

# 4. Create PR with description
gh pr create --title "Implement feature" --body-file pr-body.md

# Or in one command:
gh pr create --title "Implement feature" --body "$(vibey git pr-description)"
```

---

## Examples

### Example 1: Feature Development

```bash
# 1. Start task
vibey roadmap update task task-001 --status in_progress

# 2. Create branch
vibey git branch create task-001

# 3. Make changes and commit
git add src/feature.py
git commit -m "feat(task-001): implement user authentication

- Add login endpoint
- Add session management
- Add password hashing

Task: task-001
Status: in_progress"

# Hook validates and shows:
# [vibey] ✓ Task references: task-001

# 4. Update status automatically
vibey git update-status

# 5. Complete task
git commit -m "feat(task-001): complete authentication

Task: task-001
Status: completed"

# 6. Create PR
vibey git pr-description | gh pr create --title "User Authentication" --body-file -
```

### Example 2: Bug Fix

```bash
# 1. Create hotfix branch
git checkout -b task/bug-fix-001

# 2. Fix and commit
git commit -m "fix(bug-fix-001): resolve login timeout issue

Fixed session timeout calculation that was causing
premature logouts.

Task: bug-fix-001
Status: completed"

# 3. Link commit to task
vibey git link-commit bug-fix-001 $(git rev-parse HEAD) --status completed
```

### Example 3: Multi-Task Refactoring

```bash
# Affects multiple tasks
git commit -m "refactor: update API error handling

This refactoring improves error handling across
multiple API endpoints.

Tasks: task-001, task-002, task-003
Status: in_progress"

# Hook validates all task references:
# [vibey] ✓ Task references: task-001, task-002, task-003
```

### Example 4: Emergency Fix (Bypass)

```bash
# Critical production fix
git commit --no-verify -m "hotfix: patch security vulnerability

Emergency fix for CVE-2024-XXXX
Bypassing hooks for immediate deployment"

# Later: Link commits retroactively
vibey git link-commit security-task-001 $(git rev-parse HEAD)
```

---

## Additional Resources

- **CLI Reference:** `vibey git --help`
- **Hook Status:** `vibey git hooks status`
- **Configuration Reference:** `.vibey/config/git.yaml`
- **Audit Logs:** `.vibey/git-audit.log`
- **Troubleshooting:** Run hooks manually for debugging

---

**Last Updated:** 2025-11-24
**Version:** 2.0 (Git Integration Sprint 2)
