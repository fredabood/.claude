# Source of Truth Model Specification

**Task:** git-integration-0-task-002
**Status:** Draft
**Author:** Architecture Agent
**Date:** 2025-11-24

## Executive Summary

This document establishes which system (YAML files or Git history) is authoritative for roadmap state, and how conflicts between them are resolved.

## The Core Question

When YAML files say one thing and Git history implies another, which wins?

**Example Conflict:**
```
YAML says: task-001 status = "not_started"
Git log shows: commit abc123 with message "feat(task-001): implement feature"
```

Who is right? The explicit YAML state or the implicit Git evidence?

## Source of Truth Options

### Option A: YAML-Primary (Explicit State)

```
┌─────────────────────────────────────────────────────┐
│                    YAML Files                        │
│              (Authoritative Source)                  │
│  ┌─────────────────────────────────────────────┐    │
│  │  sprint.yaml                                │    │
│  │    tasks:                                   │    │
│  │      - id: task-001                         │    │
│  │        status: completed  ← This is TRUTH  │    │
│  │        commits: [abc123]                    │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
                        │
                        │ Tracks changes
                        ▼
┌─────────────────────────────────────────────────────┐
│                   Git History                        │
│              (Change Log / Audit Trail)              │
│                                                      │
│  abc123 - "feat(task-001): implement feature"       │
│  def456 - "update sprint.yaml: mark task complete"  │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Characteristics:**
- YAML files contain explicit, current state
- Git tracks how state changed over time
- State is always readable directly from files
- No complex reconstruction needed

**Advantages:**
- Simple to understand and implement
- State is always explicit and visible
- Easy to manually edit/fix state
- No inference or heuristics required
- Works with any Git workflow (squash, rebase, etc.)

**Disadvantages:**
- Requires discipline to update YAML files
- State can diverge from actual work (human error)
- Git history is "just" an audit trail
- Manual status updates feel redundant

### Option B: Git-Primary (Derived State)

```
┌─────────────────────────────────────────────────────┐
│                   Git History                        │
│              (Authoritative Source)                  │
│                                                      │
│  abc123 - "feat(task-001): implement feature"       │
│           ├── Task: task-001                        │
│           └── Status: completed  ← TRUTH derived   │
│                                                      │
└─────────────────────────────────────────────────────┘
                        │
                        │ Derives state
                        ▼
┌─────────────────────────────────────────────────────┐
│                    YAML Files                        │
│              (Cached / Materialized View)            │
│  ┌─────────────────────────────────────────────┐    │
│  │  sprint.yaml                                │    │
│  │    # Auto-generated from Git history        │    │
│  │    tasks:                                   │    │
│  │      - id: task-001                         │    │
│  │        status: completed                    │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

**Characteristics:**
- Git commits are the authoritative record
- YAML files are derived/generated views
- State reconstructed by parsing commit history
- Single source of truth (Git)

**Advantages:**
- No manual status updates needed
- Git is already the developer's source of truth
- Automatic tracking from normal workflow
- Can't have divergence (derived from same source)

**Disadvantages:**
- Complex reconstruction algorithms
- Sensitive to commit message format
- Squash/rebase can lose information
- Performance concerns for large histories
- Harder to make manual corrections

### Option C: Hybrid Model (Recommended)

```
┌─────────────────────────────────────────────────────┐
│              Hybrid Source of Truth                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  YAML Files = Current State (Primary)               │
│  Git History = Change Evidence (Validating)          │
│                                                      │
│  ┌─────────────┐         ┌─────────────┐            │
│  │    YAML     │◄───────►│     Git     │            │
│  │   (State)   │ Sync    │  (Changes)  │            │
│  └─────────────┘         └─────────────┘            │
│         │                       │                    │
│         │    ┌─────────────┐    │                    │
│         └───►│ Reconciler  │◄───┘                    │
│              └─────────────┘                         │
│                     │                                │
│              Detect & Resolve                        │
│               Inconsistencies                        │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Characteristics:**
- YAML is primary for explicit state
- Git provides supporting evidence
- Reconciliation process handles conflicts
- Best of both worlds

**Decision:** We adopt the **Hybrid Model** with YAML-primary semantics.

## Hybrid Model Specification

### Core Principles

1. **YAML is Authoritative for State**
   - Current status of tasks, sprints, tracks is in YAML
   - YAML can be read without parsing Git history
   - Manual edits to YAML are valid and respected

2. **Git is Authoritative for Changes**
   - Git records when and how state changed
   - Commit references in YAML link to Git evidence
   - Git history enables audit and reconstruction

3. **Reconciliation Handles Divergence**
   - `vibey git validate` detects inconsistencies
   - Warnings for mismatches, not automatic overwrites
   - Human decides resolution in ambiguous cases

### State Storage in YAML

```yaml
# sprint.yaml - Primary state storage
sprint:
  id: python-package-3
  status: in_progress  # Authoritative status

  tasks:
    - id: task-001
      status: completed
      completed_at: '2025-11-24T10:30:00Z'
      completed_by: developer@example.com
      commits:           # Links to Git evidence
        - sha: abc123
          message: "feat(task-001): implement content loader"
          timestamp: '2025-11-24T10:25:00Z'
        - sha: def456
          message: "test(task-001): add unit tests"
          timestamp: '2025-11-24T10:28:00Z'
```

### Git Evidence Recording

When a commit references a task, the evidence is optionally recorded:

```yaml
# Task with Git evidence
- id: task-001
  status: completed
  commits:
    - sha: abc123    # Git SHA for traceability
    - sha: def456
```

This is **optional** - tasks can be completed without commits.

### Conflict Detection

**Scenario 1: YAML says incomplete, Git shows work**
```
YAML: status = not_started
Git: commits referencing task-001 exist
```
**Resolution:** Advisory warning. Human decides:
- Update YAML to reflect Git evidence
- Keep YAML (commits were exploratory/abandoned)

**Scenario 2: YAML says complete, Git shows no work**
```
YAML: status = completed
Git: no commits reference task-001
```
**Resolution:** Valid. Task may be non-code (planning, review).

**Scenario 3: YAML and Git agree**
```
YAML: status = completed, commits = [abc123]
Git: commit abc123 references task-001
```
**Resolution:** Consistent state, no action needed.

**Scenario 4: Commit references unknown task**
```
Git: commit with "feat(unknown-task): ..."
YAML: no task with id "unknown-task"
```
**Resolution:** Warning. Options:
- Typo in commit message
- Task was deleted
- Task exists in different sprint/track

### Reconciliation Algorithm

```python
def reconcile(yaml_state, git_history):
    """
    Compare YAML state against Git evidence.
    Returns list of inconsistencies with suggested resolutions.
    """
    issues = []

    for task in yaml_state.tasks:
        git_commits = find_commits_referencing(task.id, git_history)

        # Check for evidence of work on "not started" tasks
        if task.status == 'not_started' and git_commits:
            issues.append(Inconsistency(
                type='work_without_status_update',
                task=task.id,
                evidence=git_commits,
                suggestion='Consider updating task status to in_progress or completed'
            ))

        # Check for missing commit links on completed tasks
        if task.status == 'completed' and task.commits:
            for recorded_sha in task.commits:
                if not commit_exists(recorded_sha, git_history):
                    issues.append(Inconsistency(
                        type='missing_commit',
                        task=task.id,
                        missing_sha=recorded_sha,
                        suggestion='Commit may have been rebased/squashed'
                    ))

    # Check for orphan commits
    for commit in git_history:
        task_refs = parse_task_references(commit.message)
        for task_id in task_refs:
            if not task_exists(task_id, yaml_state):
                issues.append(Inconsistency(
                    type='orphan_commit',
                    commit=commit.sha,
                    referenced_task=task_id,
                    suggestion='Task may have been renamed or deleted'
                ))

    return issues
```

### State Reconstruction (Optional)

For audit and historical queries, state at any point can be reconstructed:

```bash
# What was the roadmap state at commit abc123?
vibey git state-at abc123

# This:
# 1. Checks out roadmap YAML files at that commit
# 2. Parses the YAML state
# 3. Returns historical snapshot
```

This works because YAML is committed to Git, so Git history contains the full state history.

## Merge Behavior

### PR with YAML Changes

When a PR modifies sprint.yaml:

```
main:        task-001.status = not_started
PR branch:   task-001.status = completed
```

**Merge behavior:** Standard Git merge.
- YAML is data, merge like any other file
- Conflicts handled by Git merge mechanisms
- `vibey git check-merge` validates consistency

### Parallel Status Updates

When two branches complete the same task:

```
Branch A: marks task-001 completed (commit abc123)
Branch B: marks task-001 completed (commit def456)
```

**Detection:** `vibey git check-merge` detects this:
```
WARNING: task-001 is marked completed in both branches
  Branch A: completed at abc123 by Alice
  Branch B: completed at def456 by Bob

Resolution required:
  1. Keep A's completion (discard B's claim)
  2. Keep B's completion (discard A's claim)
  3. Merge completions (both contributed)
```

## Rebase and Squash Handling

### Squash Merges

When commits are squashed:

```
Before: abc123, def456, ghi789 (all reference task-001)
After:  squash123 (single commit, references task-001)
```

**Impact:**
- Individual commit SHAs in YAML become invalid
- Squash commit contains task reference (preserved)
- `vibey git validate` flags missing SHAs

**Mitigation:**
- Don't require exact SHA matching
- Task linkage via message parsing survives squash
- `commits` list is informational, not critical

### Rebases

When commits are rebased:

```
Before: abc123 (on feature branch)
After:  xyz789 (same content, new SHA after rebase)
```

**Impact:**
- SHA references in YAML become invalid
- Content and message preserved

**Mitigation:**
- Same as squash handling
- Commit message parsing still works
- `vibey git repair` can update stale SHAs

## Configuration

```yaml
# .vibey/config/git.yaml
git:
  source_of_truth:
    primary: yaml              # yaml|git
    reconciliation: advisory   # off|advisory|blocking

  commit_tracking:
    record_commits: true       # Store commit SHAs in YAML
    require_commits: false     # Require commits for completion

  validation:
    on_commit: false          # Validate on every commit
    on_push: true             # Validate before push
    on_merge: true            # Validate before merge
```

## CLI Commands

### Validate Consistency

```bash
# Check YAML/Git consistency
vibey git validate

# Output:
✓ 15 tasks consistent
⚠ 2 inconsistencies found:

  task-003: Status is 'not_started' but 3 commits reference it
    Commits: abc123, def456, ghi789
    Suggestion: Update status to 'in_progress' or 'completed'

  task-007: Recorded commit xyz789 not found in history
    Suggestion: Commit may have been rebased. Run 'vibey git repair'
```

### Repair Stale References

```bash
# Fix stale commit references
vibey git repair

# Output:
Scanning for stale references...
  task-007: commit xyz789 not found
    Found matching commit by message: uvw123
    Updated reference.

1 reference repaired.
```

### Query Historical State

```bash
# Show roadmap state at specific commit
vibey git state-at abc123

# Show roadmap state at specific date
vibey git state-at --date 2025-11-01
```

## Migration from Existing Projects

### Adding Vibey to Existing Repo

1. Initialize Vibey: `vibey init`
2. Create roadmap structure
3. Historical commits remain unlinked
4. New commits can reference tasks
5. Optional: `vibey git backfill` to link historical commits

### Backfill Command

```bash
# Analyze historical commits and suggest task links
vibey git backfill --dry-run

# Output:
Analyzing 150 commits...
Found 23 commits that may relate to tasks:

  abc123 "add user authentication"
    → Possible match: auth-task-001 (confidence: 85%)

  def456 "fix login bug"
    → Possible match: auth-task-003 (confidence: 72%)

Run without --dry-run to apply suggestions.
```

## Summary

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Primary Source | YAML files | Explicit, readable, manually editable |
| Secondary Source | Git history | Evidence, audit trail, change tracking |
| Conflict Resolution | Advisory warnings | Human judgment for ambiguous cases |
| Commit Recording | Optional | Not all tasks have commits |
| Squash/Rebase | Tolerated | Message-based linking survives |
| Reconstruction | Supported | Via Git history of YAML files |

## Appendix: Decision Log

| Decision | Options Considered | Choice | Rationale |
|----------|-------------------|--------|-----------|
| Primary source | YAML, Git, Hybrid | Hybrid (YAML-primary) | Balance explicit state with Git evidence |
| Commit recording | Required, Optional | Optional | Support non-code tasks |
| Conflict mode | Block, Advisory, Off | Advisory default | Gentle adoption, human oversight |
| SHA tracking | Exact, Message-based | Message-based | Survives squash/rebase |
| Historical query | Required, Optional | Optional | Performance consideration |
