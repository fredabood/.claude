# State Reconstruction Model Specification

**Task:** git-integration-0-task-006
**Status:** Draft
**Author:** Architecture Agent
**Date:** 2025-11-24

## Executive Summary

This document defines whether and how roadmap state can be reconstructed from Git history. Since YAML is the primary source of truth (see 002-source-of-truth.md), reconstruction primarily means retrieving historical YAML state from Git commits.

## Reconstruction Scenarios

### Scenario 1: Point-in-Time State

**Question:** What was the roadmap state at commit X or date Y?

**Use Cases:**
- Sprint retrospectives
- Progress reporting
- Debugging state issues
- Compliance audits

### Scenario 2: Attribution

**Question:** Who changed task X to status Y, and when?

**Use Cases:**
- Accountability
- Audit trails
- Understanding changes
- Resolving disputes

### Scenario 3: Progress History

**Question:** How did sprint progress change over time?

**Use Cases:**
- Velocity tracking
- Burndown charts
- Trend analysis
- Sprint planning

### Scenario 4: Audit Trail

**Question:** What changes were made to sprint Y between dates A and B?

**Use Cases:**
- Change tracking
- Compliance
- Issue investigation
- Historical review

### Scenario 5: Rollback

**Question:** Can we restore roadmap to a previous state?

**Use Cases:**
- Recovery from mistakes
- State corruption repair
- "Undo" operations
- Branch synchronization

## Reconstruction Methods

### Method 1: Git Checkout (Primary)

Since YAML files are committed to Git, any historical state is retrievable:

```bash
# Get roadmap state at specific commit
git show abc123:.vibey/roadmap/python-package/track.yaml

# Get all roadmap files at specific commit
git archive abc123 .vibey/roadmap/ | tar -xf -

# Get roadmap state at specific date
git log --until="2025-11-01" --format="%H" -1 | xargs git show
```

**Advantages:**
- Simple, uses native Git
- No additional storage
- Full fidelity (exact YAML state)
- Works with any Git client

**Limitations:**
- Requires parsing YAML at that commit
- No semantic understanding
- Can't query across commits efficiently

### Method 2: Commit-Based Derivation (Secondary)

Derive state changes from commit messages:

```bash
# Find all commits affecting task-001
git log --all --oneline --grep="task-001"

# Output:
abc123 feat(task-001): implement content loader
def456 test(task-001): add unit tests
ghi789 docs(task-001): update documentation
```

**Advantages:**
- Semantic understanding
- Cross-commit queries
- Works even if YAML not updated

**Limitations:**
- Depends on commit message quality
- Inference, not explicit state
- May not match YAML state

### Method 3: Audit Log (Supplementary)

Maintain explicit audit log of state changes:

```json
// .vibey/audit/state-changes.jsonl
{"timestamp":"2025-11-24T10:00:00Z","commit":"abc123","type":"task_status","task":"task-001","from":"not_started","to":"in_progress","user":"alice@example.com"}
{"timestamp":"2025-11-24T12:00:00Z","commit":"def456","type":"task_status","task":"task-001","from":"in_progress","to":"completed","user":"alice@example.com"}
```

**Advantages:**
- Explicit, queryable
- Fast retrieval
- Rich metadata

**Limitations:**
- Additional storage
- Must be maintained
- Can diverge from YAML

## Recommended Approach: Hybrid

```
┌─────────────────────────────────────────────────────────────────┐
│                    State Reconstruction                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │  Git History    │    │  Commit Messages │    │  Audit Log   │ │
│  │  (YAML files)   │    │  (Task refs)     │    │  (Optional)  │ │
│  └────────┬────────┘    └────────┬─────────┘    └──────┬───────┘ │
│           │                      │                      │        │
│           └──────────────────────┼──────────────────────┘        │
│                                  │                               │
│                          ┌───────▼───────┐                       │
│                          │  Reconstruction │                      │
│                          │     Engine      │                      │
│                          └───────┬────────┘                       │
│                                  │                               │
│           ┌──────────────────────┼──────────────────────┐        │
│           │                      │                      │        │
│    ┌──────▼──────┐    ┌─────────▼─────────┐    ┌───────▼──────┐ │
│    │ Point-in-   │    │    Attribution    │    │   Progress   │ │
│    │ Time State  │    │                   │    │   History    │ │
│    └─────────────┘    └───────────────────┘    └──────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Implementation Specification

### Point-in-Time State Query

```python
def get_state_at(ref: str) -> RoadmapState:
    """
    Get roadmap state at a specific Git ref (commit, tag, branch, date).

    Args:
        ref: Git reference (SHA, tag, branch, or date like "2025-11-01")

    Returns:
        RoadmapState parsed from YAML files at that ref
    """
    # Resolve date to commit if needed
    if is_date(ref):
        ref = git_rev_parse(f"--until={ref}", "-1")

    # Get all roadmap YAML files at that commit
    yaml_files = git_ls_tree(ref, ".vibey/roadmap/", recursive=True)

    # Parse into state object
    state = RoadmapState()
    for file in yaml_files:
        content = git_show(f"{ref}:{file}")
        state.load_yaml(file, content)

    return state
```

**CLI Command:**

```bash
# Get state at specific commit
vibey git state-at abc123

# Get state at specific date
vibey git state-at --date 2025-11-01

# Get state at tag
vibey git state-at sprint/python-package-3/end

# Compare states
vibey git state-diff abc123 def456
```

**Output:**

```yaml
# vibey git state-at abc123
roadmap:
  id: vibey-framework-v2
  tracks:
    - id: python-package
      status: in_progress
      sprints:
        - id: python-package-3
          status: in_progress
          progress:
            tasks_completed: 5
            tasks_total: 10
            completion_percent: 50
```

### Attribution Query

```python
def get_task_history(task_id: str) -> List[TaskChange]:
    """
    Get history of changes to a specific task.

    Returns list of changes with commit, timestamp, user, and change details.
    """
    changes = []

    # Method 1: Parse commits that reference this task
    commits = git_log(grep=task_id)
    for commit in commits:
        changes.append(TaskChange(
            commit=commit.sha,
            timestamp=commit.timestamp,
            user=commit.author,
            type="commit",
            message=commit.message
        ))

    # Method 2: Find YAML changes affecting this task
    yaml_commits = git_log(path=f".vibey/roadmap/**/*", grep=task_id)
    for commit in yaml_commits:
        diff = parse_yaml_diff(commit, task_id)
        if diff:
            changes.append(TaskChange(
                commit=commit.sha,
                timestamp=commit.timestamp,
                user=commit.author,
                type="yaml_change",
                from_status=diff.old_status,
                to_status=diff.new_status
            ))

    return sorted(changes, key=lambda c: c.timestamp)
```

**CLI Command:**

```bash
# Get task history
vibey git history task-001

# Output:
Task: python-package-3-task-001 (Implement content loader)
History:

  2025-11-24 09:00  alice@example.com
    Status: not_started → in_progress
    Commit: abc123 "feat(task-001): start implementation"

  2025-11-24 10:30  alice@example.com
    Commit: def456 "feat(task-001): add ContentLoader class"

  2025-11-24 11:00  alice@example.com
    Commit: ghi789 "test(task-001): add unit tests"

  2025-11-24 12:00  alice@example.com
    Status: in_progress → completed
    Commit: jkl012 "chore: update sprint.yaml"
```

### Progress History Query

```python
def get_progress_history(
    sprint_id: str,
    since: datetime = None,
    until: datetime = None,
    interval: str = "daily"
) -> List[ProgressSnapshot]:
    """
    Get progress history for a sprint over time.

    Args:
        sprint_id: Sprint to track
        since: Start date (default: sprint start)
        until: End date (default: now)
        interval: Sampling interval (hourly, daily, weekly)

    Returns:
        List of progress snapshots
    """
    snapshots = []

    # Get commits in time range that modified roadmap
    commits = git_log(
        path=".vibey/roadmap/",
        since=since,
        until=until
    )

    # Sample at specified interval
    for sample_time in generate_intervals(since, until, interval):
        # Find closest commit before sample time
        commit = find_commit_before(commits, sample_time)

        # Get state at that commit
        state = get_state_at(commit.sha)
        sprint_state = state.get_sprint(sprint_id)

        snapshots.append(ProgressSnapshot(
            timestamp=sample_time,
            commit=commit.sha,
            tasks_completed=sprint_state.progress.tasks_completed,
            tasks_total=sprint_state.progress.tasks_total,
            completion_percent=sprint_state.progress.completion_percent
        ))

    return snapshots
```

**CLI Command:**

```bash
# Get sprint progress over time
vibey git progress python-package-3 --interval daily

# Output (suitable for charting):
Date        Completed  Total  Percent
2025-11-20  0          10     0%
2025-11-21  2          10     20%
2025-11-22  5          10     50%
2025-11-23  8          10     80%
2025-11-24  10         10     100%

# Burndown data
vibey git burndown python-package-3 --format csv > burndown.csv
```

### State Diff Query

```python
def diff_states(ref1: str, ref2: str) -> StateDiff:
    """
    Compare roadmap states between two Git refs.

    Returns detailed diff of what changed.
    """
    state1 = get_state_at(ref1)
    state2 = get_state_at(ref2)

    diff = StateDiff()

    # Compare tasks
    for task in state2.all_tasks():
        task1 = state1.get_task(task.id)
        if task1 is None:
            diff.tasks_added.append(task)
        elif task1.status != task.status:
            diff.tasks_changed.append(TaskDiff(
                task_id=task.id,
                from_status=task1.status,
                to_status=task.status
            ))

    for task in state1.all_tasks():
        if state2.get_task(task.id) is None:
            diff.tasks_removed.append(task)

    # Compare sprints
    # ... similar logic ...

    return diff
```

**CLI Command:**

```bash
# Compare states
vibey git diff abc123 def456

# Output:
Changes from abc123 to def456:

Tasks:
  + task-010 (added: "Implement backup system")
  ~ task-001: not_started → in_progress
  ~ task-002: in_progress → completed
  - task-005 (removed)

Sprints:
  ~ python-package-3: 50% → 80%

Quality Gates:
  ~ Test Coverage: 85% → 92%
```

### Rollback

```python
def rollback_to(ref: str, dry_run: bool = True) -> RollbackResult:
    """
    Restore roadmap YAML files to state at specified ref.

    Args:
        ref: Git reference to rollback to
        dry_run: If True, show what would change without applying

    Returns:
        List of files that would be/were changed
    """
    # Get current state
    current_files = list_roadmap_files()

    # Get state at target ref
    target_state = get_state_at(ref)

    changes = []
    for file in target_state.files:
        current_content = read_file(file) if file_exists(file) else None
        target_content = git_show(f"{ref}:{file}")

        if current_content != target_content:
            changes.append(FileChange(
                path=file,
                action="modify" if current_content else "create",
                diff=diff(current_content, target_content)
            ))

    if not dry_run:
        for change in changes:
            target_content = git_show(f"{ref}:{change.path}")
            write_file(change.path, target_content)

    return RollbackResult(
        target_ref=ref,
        files_changed=len(changes),
        changes=changes,
        applied=not dry_run
    )
```

**CLI Command:**

```bash
# Preview rollback
vibey git rollback abc123 --dry-run

# Output:
Rollback preview to abc123:

Files to change:
  M .vibey/roadmap/python-package/track.yaml
  M .vibey/roadmap/python-package/python-package-3/sprint.yaml

Changes:
  track.yaml:
    - status: completed
    + status: in_progress

  sprint.yaml:
    - task-001.status: completed
    + task-001.status: in_progress

Run without --dry-run to apply.

# Apply rollback
vibey git rollback abc123
```

## Audit Log (Optional Feature)

### Log Format

```jsonl
{"v":1,"ts":"2025-11-24T10:00:00Z","type":"state_change","commit":"abc123","author":"alice@example.com","entity":"task","id":"task-001","field":"status","old":"not_started","new":"in_progress"}
{"v":1,"ts":"2025-11-24T10:30:00Z","type":"commit","sha":"def456","author":"alice@example.com","message":"feat(task-001): add loader","tasks":["task-001"]}
{"v":1,"ts":"2025-11-24T11:00:00Z","type":"state_change","commit":"ghi789","author":"alice@example.com","entity":"sprint","id":"python-package-3","field":"progress.completion_percent","old":40,"new":50}
```

### Log Management

```yaml
# .vibey/config/git.yaml
git:
  audit:
    enabled: true
    path: .vibey/audit/changes.jsonl
    retention:
      days: 365
      max_size_mb: 100
    include:
      - state_changes
      - commits
      - quality_gates
    exclude:
      - yaml_syntax  # Don't log every YAML parse
```

### Querying Audit Log

```bash
# Query recent changes
vibey git audit --since "1 week ago"

# Query specific task
vibey git audit --task task-001

# Export for analysis
vibey git audit --format json > audit.json
```

## Performance Considerations

### Caching

```yaml
git:
  reconstruction:
    cache:
      enabled: true
      ttl_seconds: 300  # 5 minutes
      max_entries: 100
```

### Lazy Loading

```python
class LazyRoadmapState:
    """Load YAML files only when accessed."""

    def __init__(self, ref: str):
        self.ref = ref
        self._tracks = None

    @property
    def tracks(self):
        if self._tracks is None:
            self._tracks = self._load_tracks()
        return self._tracks
```

### Batch Operations

```bash
# Efficient: single pass through history
vibey git progress sprint-3 --since "2025-11-01" --until "2025-11-30"

# Inefficient: multiple passes (avoid)
for date in dates:
    vibey git state-at --date $date
```

## Configuration

```yaml
# .vibey/config/git.yaml
git:
  reconstruction:
    # Enable/disable features
    enabled: true
    point_in_time: true
    attribution: true
    progress_history: true
    rollback: true

    # Performance
    cache:
      enabled: true
      ttl_seconds: 300

    # Audit log
    audit:
      enabled: false  # Optional
      path: .vibey/audit/changes.jsonl

    # Limits
    max_history_depth: 1000  # Commits to search
    max_progress_samples: 365  # Days of progress history
```

## CLI Commands Summary

| Command | Description |
|---------|-------------|
| `vibey git state-at <ref>` | Show roadmap state at ref |
| `vibey git state-at --date <date>` | Show state at date |
| `vibey git diff <ref1> <ref2>` | Compare two states |
| `vibey git history <task-id>` | Show task change history |
| `vibey git progress <sprint-id>` | Show sprint progress over time |
| `vibey git burndown <sprint-id>` | Generate burndown data |
| `vibey git rollback <ref>` | Restore state from ref |
| `vibey git audit` | Query audit log |

## Decision Log

| Decision | Options Considered | Choice | Rationale |
|----------|-------------------|--------|-----------|
| Primary method | Git checkout, Derivation | Git checkout | YAML is source of truth |
| Audit log | Required, Optional | Optional | Not all teams need it |
| Cache | Always, Configurable | Configurable | Balance speed vs freshness |
| Rollback | Full restore, Selective | Full restore | Simpler, safer |
| Progress sampling | Every commit, Interval | Interval | Performance |
