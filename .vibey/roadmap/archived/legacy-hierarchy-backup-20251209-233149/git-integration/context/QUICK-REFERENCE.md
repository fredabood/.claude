# Vibey-Git Integration Quick Reference

## Commit Message Formats

```bash
# Conventional (recommended)
feat(task-001): description

# Footer reference
feat: description
Task: task-001

# Bracket notation
[task-001] description
```

## Task Status Keywords

| Keyword | Effect |
|---------|--------|
| `Task: task-id` | Links commit to task |
| `Closes: task-id` | Links and marks complete |
| `Completes: task-id` | Links and marks complete |

## Enforcement Modes

| Mode | Behavior |
|------|----------|
| `off` | No hooks, no validation |
| `advisory` | Warnings only (default) |
| `blocking` | Prevents invalid operations |
| `audit` | Logs only, no warnings |

## Essential Commands

```bash
# Setup
vibey git hooks install    # Install git hooks
vibey git hooks uninstall  # Remove hooks

# Validation
vibey git validate         # Check consistency
vibey git repair           # Fix stale refs

# Analysis
vibey git analyze          # Analyze history
vibey git state-at <ref>   # State at commit
vibey git history <task>   # Task history

# Merge checking
vibey git check-merge      # Pre-merge validation
```

## Configuration Essentials

```yaml
# .vibey/config/git.yaml
git:
  enabled: true
  enforcement:
    mode: advisory  # off|advisory|blocking|audit
  commit:
    require_task_reference: false
```

## Override Hooks

```bash
git commit --no-verify -m "emergency fix"
# or
VIBEY_SKIP_HOOKS=1 git commit -m "bypass"
```

## Branch Naming (Optional)

```
feature/<task-id>-description
sprint/<sprint-id>
track/<track-id>
```

## Sprint Tags (Optional)

```bash
git tag sprint/<id>/start
git tag sprint/<id>/end
```

---

*Full documentation: [007-architecture-document.md](./007-architecture-document.md)*
