# Enforcement Philosophy Specification

**Task:** git-integration-0-task-005
**Status:** Draft
**Author:** Architecture Agent
**Date:** 2025-11-24

## Executive Summary

This document establishes how strictly Vibey enforces Git integration rules. The philosophy prioritizes developer experience while enabling teams to increase strictness as they mature.

## Core Philosophy

**Principle: Enable, Don't Obstruct**

Vibey should:
- Make the right thing easy
- Make the wrong thing visible
- Never block legitimate work
- Always provide escape hatches

**Default Stance: Advisory**

Out of the box, Vibey:
- Provides guidance and suggestions
- Warns about potential issues
- Never blocks commits or merges
- Trusts developer judgment

## Enforcement Modes

### Mode 1: Off (Disabled)

```yaml
git:
  enforcement:
    mode: off
```

**Behavior:**
- No hooks installed
- No validation runs
- No warnings or errors
- Pure YAML + Git workflow
- Vibey is passive observer

**Use Cases:**
- Initial evaluation
- Legacy project adoption
- Teams preferring manual control
- Minimal Vibey usage

### Mode 2: Advisory (Default)

```yaml
git:
  enforcement:
    mode: advisory
```

**Behavior:**
- Hooks provide suggestions
- Warnings shown but never block
- Recommendations for improvement
- Exit code always 0 (success)

**Example Output:**
```bash
$ git commit -m "fix: resolve bug"

[vibey] Advisory:
  ⚠ Commit does not reference a task
    Suggestion: Use "fix(task-id): resolve bug" or add "Task: task-id" footer

  ⚠ Task task-003 is marked as blocked
    Suggestion: Check if blocker has been resolved

Proceeding with commit... ✓
```

**Use Cases:**
- Default for new projects
- Teams learning Vibey conventions
- Gradual adoption
- Low-ceremony environments

### Mode 3: Blocking (Strict)

```yaml
git:
  enforcement:
    mode: blocking
```

**Behavior:**
- Validation failures prevent operations
- Exit code 1 on violations
- Must fix issues or override
- Highest consistency guarantee

**Example Output:**
```bash
$ git commit -m "fix: resolve bug"

[vibey] Blocking:
  ✗ Commit must reference a task (required)
    Use "fix(task-id): resolve bug" or add "Task: task-id" footer

Commit blocked. Use --no-verify to override.
```

**Override Mechanism:**
```bash
# Skip hooks for emergency
git commit -m "hotfix: critical production fix" --no-verify

# Or use Vibey override
VIBEY_OVERRIDE=true git commit -m "fix: resolve bug"
```

**Use Cases:**
- Mature teams with established conventions
- Compliance requirements
- Maximum traceability needs
- High-stakes projects

### Mode 4: Audit (Logging Only)

```yaml
git:
  enforcement:
    mode: audit
```

**Behavior:**
- All operations allowed
- Violations logged to audit file
- No user-facing warnings
- Compliance tracking without friction

**Audit Log:**
```json
{
  "timestamp": "2025-11-24T10:30:00Z",
  "event": "commit",
  "sha": "abc123",
  "user": "developer@example.com",
  "violations": [
    {
      "rule": "task_reference_required",
      "severity": "warning",
      "message": "Commit does not reference a task"
    }
  ],
  "action": "allowed"
}
```

**Use Cases:**
- Compliance environments
- Metrics collection
- Understanding team patterns
- Non-intrusive monitoring

## Enforcement Points

### 1. Pre-Commit Hook

**When:** Before commit is created

**Checks:**
- YAML syntax validation
- Roadmap integrity (no broken references)
- Task status consistency

**Advisory:**
```bash
[vibey] Pre-commit check:
  ⚠ sprint.yaml has unsaved changes
    Suggestion: Stage sprint.yaml or stash changes
```

**Blocking:**
```bash
[vibey] Pre-commit check:
  ✗ sprint.yaml contains invalid YAML
    Error on line 45: duplicate key 'status'

Commit blocked.
```

### 2. Commit-Msg Hook

**When:** After commit message is written, before commit completes

**Checks:**
- Task reference format
- Task existence in roadmap
- Task status compatibility

**Advisory:**
```bash
[vibey] Commit message check:
  ⚠ Task 'task-999' not found in roadmap
    Did you mean: task-001, task-002?
```

**Blocking:**
```bash
[vibey] Commit message check:
  ✗ Task reference required
  ✗ Invalid commit type 'feature' (use 'feat')

Commit blocked.
```

### 3. Pre-Push Hook

**When:** Before pushing to remote

**Checks:**
- All local commits validated
- Sprint/track status consistency
- Quality gate prerequisites

**Advisory:**
```bash
[vibey] Pre-push check:
  ⚠ Sprint python-package-3 shows 100% complete but quality gates not passed
    Suggestion: Run 'vibey gate update' before marking sprint complete

Proceeding with push...
```

### 4. PR/Merge Check (CI)

**When:** During PR review / merge request

**Checks:**
- Task conflict detection
- Blocker enforcement
- Dependency satisfaction
- Quality gate status

**GitHub Check Output:**
```
vibey/integration-check: Passed ✓

Details:
  Tasks: 3 tasks referenced, all valid
  Conflicts: None detected
  Blockers: No blocked tasks modified
  Dependencies: All dependencies satisfied
```

## Rule Configuration

### Per-Rule Settings

```yaml
# .vibey/config/git.yaml
git:
  enforcement:
    mode: advisory  # Global default

    rules:
      # Task reference requirements
      task_reference:
        enabled: true
        mode: advisory      # Override global mode
        require_in_scope: false
        require_valid_id: true

      # Task status checks
      task_status:
        enabled: true
        mode: advisory
        warn_blocked: true
        warn_completed: true  # Warn if modifying completed task

      # YAML integrity
      yaml_integrity:
        enabled: true
        mode: blocking      # Always block invalid YAML

      # Quality gates
      quality_gates:
        enabled: true
        mode: advisory
        block_below_threshold: false

      # Blocker enforcement
      blockers:
        enabled: true
        mode: advisory
        prevent_work_on_blocked: false
```

### Per-Branch Overrides

```yaml
git:
  enforcement:
    branch_overrides:
      main:
        mode: blocking          # Strict on main
        rules:
          task_reference:
            mode: blocking

      develop:
        mode: advisory          # Relaxed on develop

      "feature/*":
        mode: advisory          # Relaxed on features

      "hotfix/*":
        mode: off              # Emergency bypasses
```

### Per-Track/Sprint Overrides

```yaml
# In sprint.yaml
sprint:
  id: python-package-3
  enforcement:
    mode: blocking           # This sprint requires strict enforcement
    rules:
      quality_gates:
        mode: blocking
```

## Error Messages

### Message Design Principles

1. **Clear** - State what's wrong
2. **Actionable** - Show how to fix
3. **Contextual** - Provide relevant details
4. **Respectful** - Never blame the user

### Error Message Template

```
[vibey] <mode>:
  <symbol> <message>
    <context>
    Suggestion: <how to fix>

<action taken>
```

### Symbols

| Symbol | Meaning | Mode |
|--------|---------|------|
| ✓ | Passed | All |
| ⚠ | Warning | Advisory |
| ✗ | Error | Blocking |
| ℹ | Info | Audit |

### Example Messages

**Good:**
```
[vibey] Advisory:
  ⚠ Task 'task-001' is marked as completed
    You're modifying files associated with a completed task.
    Suggestion: If this is intentional, add "Reopens: task-001" to commit message
```

**Bad:**
```
ERROR: task-001 completed. Cannot modify.
```

## Override Mechanisms

### Emergency Bypass

```bash
# Git native bypass
git commit --no-verify -m "emergency: hotfix"

# Vibey environment variable
VIBEY_SKIP_HOOKS=1 git commit -m "emergency: hotfix"
```

### Explicit Override

```bash
# Override specific rule
git commit -m "feat: implement feature

Override: task_reference (reason: exploratory work)
"
```

### Time-Limited Override

```yaml
# In config
git:
  enforcement:
    overrides:
      - rule: task_reference
        until: "2025-12-01"
        reason: "Migration period"
```

## Adoption Path

### Stage 1: Observation (Week 1-2)

```yaml
git:
  enforcement:
    mode: audit
```

- Install hooks but don't warn
- Collect metrics on current patterns
- Identify common violations
- Prepare team communication

### Stage 2: Guidance (Week 3-4)

```yaml
git:
  enforcement:
    mode: advisory
```

- Enable warnings
- Team learns conventions
- Adjust rules based on feedback
- Document team agreements

### Stage 3: Enforcement (Week 5+)

```yaml
git:
  enforcement:
    mode: blocking
    rules:
      yaml_integrity:
        mode: blocking
      task_reference:
        mode: advisory  # Still advisory for task refs
```

- Block critical violations
- Keep some rules advisory
- Iterate based on friction

### Stage 4: Full Enforcement (Month 2+)

```yaml
git:
  enforcement:
    mode: blocking
```

- All rules enforced
- Team comfortable with conventions
- High consistency achieved
- Escape hatches still available

## Metrics and Reporting

### Enforcement Dashboard

```bash
vibey git metrics

Enforcement Summary (last 30 days):
  Total commits: 150
  Commits with task refs: 142 (95%)
  Commits without task refs: 8 (5%)

  Warnings issued: 23
    - task_reference: 8
    - task_status: 10
    - yaml_integrity: 5

  Blocks issued: 3
    - yaml_integrity: 3 (all resolved)

  Overrides used: 2
    - --no-verify: 2

Trend: Task reference compliance improving (89% → 95%)
```

### Audit Report

```bash
vibey git audit --since "2025-11-01"

Audit Report: November 2025
===========================

Violations by Type:
  task_reference_missing: 8 occurrences
  blocked_task_modified: 2 occurrences
  invalid_yaml: 3 occurrences (all blocked)

Violations by User:
  alice@example.com: 5
  bob@example.com: 8

Recommendations:
  1. Team training on task reference format
  2. Review blocked task workflow
```

## Configuration Schema

```yaml
# Complete enforcement configuration
git:
  enforcement:
    # Global mode
    mode: advisory  # off|advisory|blocking|audit

    # Audit logging
    audit:
      enabled: true
      file: .vibey/audit/enforcement.log
      retention_days: 90

    # Rules
    rules:
      task_reference:
        enabled: true
        mode: null  # Inherit from global
        require_valid_id: true
        require_in_scope: false

      task_status:
        enabled: true
        mode: null
        warn_blocked: true
        warn_completed: true
        prevent_completed_modification: false

      yaml_integrity:
        enabled: true
        mode: blocking  # Always block invalid YAML

      quality_gates:
        enabled: true
        mode: null
        block_below_threshold: false
        warn_failing: true

      blockers:
        enabled: true
        mode: null
        prevent_blocked_work: false
        warn_blocked: true

      dependencies:
        enabled: true
        mode: null
        enforce_order: false
        warn_out_of_order: true

    # Branch overrides
    branch_overrides: {}

    # Override settings
    overrides:
      allow_no_verify: true
      allow_env_skip: true
      require_reason: false
      time_limited: []

    # Messages
    messages:
      prefix: "[vibey]"
      show_suggestions: true
      show_docs_link: false
```

## Decision Log

| Decision | Options Considered | Choice | Rationale |
|----------|-------------------|--------|-----------|
| Default mode | Off, Advisory, Blocking | Advisory | Balance guidance with adoption |
| Override mechanism | None, Flag, Env | Both (flag + env) | Flexibility for emergencies |
| YAML integrity | Advisory, Blocking | Always blocking | Invalid YAML breaks everything |
| Branch overrides | Global only, Per-branch | Per-branch | Different branches need different rules |
| Audit mode | Separate, Combined | Separate mode | Compliance without friction |
