# Git History Analysis & Commit Correlation

**Version:** 1.0
**Status:** Complete
**Sprint:** git-integration-1 (Sprint 1: Git History & Commit Analysis)

---

## Overview

The Vibey Git Analysis system provides comprehensive tools for analyzing Git history, correlating commits with roadmap tasks, calculating sprint velocity, and reconstructing historical roadmap states. This enables:

- **Automatic Progress Tracking** - Link commits to tasks automatically
- **Sprint Velocity Metrics** - Calculate team productivity from Git history
- **Historical Analysis** - Reconstruct roadmap state at any point in time
- **Tag-Based Milestones** - Use Git tags for explicit sprint/task markers
- **Contributor Analytics** - Analyze contributor activity and velocity

---

## Table of Contents

- [CLI Commands](#cli-commands)
  - [vibey git analyze](#vibey-git-analyze)
  - [vibey git tasks](#vibey-git-tasks)
  - [vibey git velocity](#vibey-git-velocity)
  - [vibey git contributors](#vibey-git-contributors)
  - [vibey git tags](#vibey-git-tags)
  - [vibey git tag-range](#vibey-git-tag-range)
  - [vibey git state-at](#vibey-git-state-at)
  - [vibey git history](#vibey-git-history)
  - [vibey git progress](#vibey-git-progress)
  - [vibey git rollback](#vibey-git-rollback)
- [Commit Message Formats](#commit-message-formats)
- [Tag Formats](#tag-formats)
- [Python API](#python-api)
- [Use Cases](#use-cases)
- [Best Practices](#best-practices)

---

## CLI Commands

### vibey git analyze

Analyze commit history for task references and generate summary statistics.

**Usage:**
```bash
vibey git analyze [OPTIONS]
```

**Options:**
- `--max <N>` - Limit to N most recent commits (default: all)
- `--since <date>` - Only commits after date (YYYY-MM-DD or ISO format)
- `--until <date>` - Only commits before date
- `--author <name>` - Filter by author name/email
- `--format <format>` - Output format: `summary` (default), `table`, `json`
- `--repo <path>` - Repository path (default: current directory)

**Examples:**
```bash
# Analyze all commits
vibey git analyze

# Analyze last 100 commits
vibey git analyze --max 100

# Analyze commits from last sprint
vibey git analyze --since 2025-11-01 --until 2025-11-15

# Analyze commits by specific author
vibey git analyze --author "john@example.com"

# Get detailed table view
vibey git analyze --format table

# Export to JSON
vibey git analyze --format json > analysis.json
```

**Output:**
```
Git Commit Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Overall Statistics
─────────────────────────────────────────────────
Total commits analyzed:        150
Commits with task references:   89 (59%)
Commits without references:     61 (41%)

🎯 Task References
─────────────────────────────────────────────────
Unique tasks referenced:        23
Unique sprints referenced:       3
Unique tracks referenced:        2

📋 Task List
─────────────────────────────────────────────────
• git-integration-1-task-001 (12 commits)
• git-integration-1-task-002 (15 commits)
• git-integration-1-task-003 (8 commits)
[...]
```

---

### vibey git tasks

Show all commits for a specific task.

**Usage:**
```bash
vibey git tasks <task-id> [OPTIONS]
```

**Options:**
- `--format <format>` - Output format: `summary`, `table` (default), `json`
- `--show-files` - Include files changed in each commit
- `--repo <path>` - Repository path

**Examples:**
```bash
# Show commits for a task
vibey git tasks git-integration-1-task-001

# Show with files changed
vibey git tasks git-integration-1-task-001 --show-files

# Export to JSON
vibey git tasks git-integration-1-task-001 --format json
```

**Output:**
```
Commits for Task: git-integration-1-task-001
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ SHA    ┃ Date            ┃ Author     ┃ Message                 ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ abc123 │ 2025-11-24 10:00│ John Doe   │ feat(task-001): Start   │
│ def456 │ 2025-11-24 11:00│ John Doe   │ feat(task-001): Impl... │
│ ghi789 │ 2025-11-24 12:00│ Jane Smith │ test(task-001): Add ... │
└────────┴─────────────────┴────────────┴─────────────────────────┘

📊 Summary: 12 commits, 3 contributors, 45 files changed
```

---

### vibey git velocity

Calculate sprint velocity metrics from Git history.

**Usage:**
```bash
vibey git velocity <sprint-id> [OPTIONS]
```

**Options:**
- `--start-ref <ref>` - Starting commit/tag (default: auto-detect from sprint tags)
- `--end-ref <ref>` - Ending commit/tag (default: HEAD)
- `--start-date <date>` - Starting date (alternative to --start-ref)
- `--end-date <date>` - Ending date
- `--format <format>` - Output format: `summary` (default), `detailed`, `json`
- `--repo <path>` - Repository path

**Examples:**
```bash
# Calculate velocity for sprint (auto-detect boundaries)
vibey git velocity git-integration-1

# Calculate velocity between specific dates
vibey git velocity git-integration-1 \
  --start-date 2025-11-01 \
  --end-date 2025-11-15

# Calculate velocity between tags
vibey git velocity git-integration-1 \
  --start-ref sprint/git-integration-1/start \
  --end-ref sprint/git-integration-1/end

# Get detailed breakdown
vibey git velocity git-integration-1 --format detailed
```

**Output:**
```
Sprint Velocity: git-integration-1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Time Period
─────────────────────────────────────────────────
Start:    2025-11-01 00:00:00
End:      2025-11-15 23:59:59
Duration: 15.0 days (2.1 weeks)

📊 Commit Metrics
─────────────────────────────────────────────────
Total commits:      147
Commits per day:    9.8
Commits per week:   68.6

🎯 Task Metrics
─────────────────────────────────────────────────
Tasks worked on:     9
Tasks completed:     7
Completion rate:    78%

👥 Contributor Metrics
─────────────────────────────────────────────────
Unique contributors: 3
Avg commits/person:  49.0

💾 Code Volume
─────────────────────────────────────────────────
Files changed:      125
Insertions:      +3,450
Deletions:       -1,200
Net change:      +2,250 lines
```

---

### vibey git contributors

Analyze contributor activity and productivity.

**Usage:**
```bash
vibey git contributors [OPTIONS]
```

**Options:**
- `--since <date>` - Only commits after date
- `--until <date>` - Only commits before date
- `--min-commits <N>` - Only show contributors with N+ commits
- `--format <format>` - Output format: `table` (default), `summary`, `json`
- `--repo <path>` - Repository path

**Examples:**
```bash
# Show all contributors
vibey git contributors

# Contributors from last month
vibey git contributors --since 2025-11-01

# Active contributors (10+ commits)
vibey git contributors --min-commits 10
```

**Output:**
```
Contributor Activity
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Contributor  ┃ Commits┃ Tasks  ┃ Files     ┃ Lines     ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━┩
│ John Doe     │    87  │   15   │    245    │ +4,521    │
│ Jane Smith   │    45  │    8   │    123    │ +2,134    │
│ Bob Johnson  │    15  │    3   │     45    │   +678    │
└──────────────┴────────┴────────┴───────────┴───────────┘
```

---

### vibey git tags

List and analyze Vibey roadmap tags (sprint/task markers).

**Usage:**
```bash
vibey git tags [OPTIONS]
```

**Options:**
- `--task <task-id>` - Filter to specific task
- `--sprint <sprint-id>` - Filter to specific sprint
- `--type <type>` - Filter by type: `sprint`, `task`, `all` (default)
- `--format <format>` - Output format: `table` (default), `list`, `json`
- `--repo <path>` - Repository path

**Examples:**
```bash
# List all Vibey tags
vibey git tags

# List tags for specific sprint
vibey git tags --sprint git-integration-1

# List task tags only
vibey git tags --type task

# List tags for specific task
vibey git tags --task git-integration-1-task-001
```

**Output:**
```
Vibey Roadmap Tags
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sprint Tags (4)
─────────────────────────────────────────────────
• sprint/git-integration-0/start    (abc123)
• sprint/git-integration-0/end      (def456)
• sprint/git-integration-1/start    (ghi789)
• sprint/git-integration-1/end      (jkl012)

Task Tags (8)
─────────────────────────────────────────────────
• git-integration/git-integration-1/task-001/start     (mno345)
• git-integration/git-integration-1/task-001/completed (pqr678)
• git-integration/git-integration-1/task-002/start     (stu901)
• git-integration/git-integration-1/task-002/completed (vwx234)
[...]
```

---

### vibey git tag-range

Get commits between task/sprint start and end tags.

**Usage:**
```bash
vibey git tag-range <task-or-sprint-id> [OPTIONS]
```

**Options:**
- `--format <format>` - Output format: `summary` (default), `table`, `json`
- `--show-files` - Include files changed
- `--repo <path>` - Repository path

**Examples:**
```bash
# Get commits for task (using tags)
vibey git tag-range git-integration-1-task-001

# Get commits for sprint (using tags)
vibey git tag-range git-integration-1
```

**Output:**
```
Commits between tags for: git-integration-1-task-001
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Start tag: git-integration/git-integration-1/task-001/start
End tag:   git-integration/git-integration-1/task-001/completed

Found 12 commits between tags

[Shows commit list similar to 'vibey git tasks']
```

---

### vibey git state-at

Show roadmap state at a specific point in time.

**Usage:**
```bash
vibey git state-at <ref> [OPTIONS]
```

**Arguments:**
- `<ref>` - Git ref (commit SHA, tag, branch, or date like "2025-11-01")

**Options:**
- `--item <item-id>` - Show specific task/sprint/track only
- `--format <format>` - Output format: `summary` (default), `detailed`, `json`
- `--repo <path>` - Repository path

**Examples:**
```bash
# Show state at specific commit
vibey git state-at abc123

# Show state at tag
vibey git state-at sprint/git-integration-1/end

# Show state at date
vibey git state-at 2025-11-01

# Show specific task state
vibey git state-at HEAD --item git-integration-1-task-001

# Get detailed view
vibey git state-at abc123 --format detailed
```

**Output:**
```
Roadmap State at: abc123 (2025-11-15 14:30:00)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Commit: abc123
Author: John Doe
Message: feat: Complete Sprint 1 tasks

📊 Tracks (2)
─────────────────────────────────────────────────
• git-integration (in_progress, 36% complete)
• user-journey-audit (not_started, 0% complete)

📋 Sprints (4)
─────────────────────────────────────────────────
• git-integration-0 (completed, 100%)
• git-integration-1 (in_progress, 67%)
• git-integration-2 (not_started, 0%)
• git-integration-3 (not_started, 0%)

🎯 Tasks (36 total, 13 completed)
─────────────────────────────────────────────────
Completed (13):
  ✓ git-integration-0-task-001
  ✓ git-integration-0-task-002
  [...]

In Progress (3):
  ◐ git-integration-1-task-006
  ◐ git-integration-1-task-007
  ◐ git-integration-1-task-008

Not Started (20):
  ○ git-integration-2-task-001
  [...]
```

---

### vibey git history

Show complete change history for a task, sprint, or track.

**Usage:**
```bash
vibey git history <item-id> [OPTIONS]
```

**Arguments:**
- `<item-id>` - Task, sprint, or track ID

**Options:**
- `--type <type>` - Item type: `task` (default), `sprint`, `track`
- `--format <format>` - Output format: `summary` (default), `detailed`, `json`
- `--max-commits <N>` - Limit history depth (default: 1000)
- `--repo <path>` - Repository path

**Examples:**
```bash
# Show task history
vibey git history git-integration-1-task-001

# Show sprint history
vibey git history git-integration-1 --type sprint

# Show track history
vibey git history git-integration --type track
```

**Output:**
```
Change History: git-integration-1-task-001
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2025-11-24 10:00:00 (abc123)
  • existence: None → created

2025-11-24 10:30:00 (def456)
  • status: not_started → in_progress

2025-11-24 14:00:00 (ghi789)
  • assigned_agent: None → backend-engineer

2025-11-24 18:00:00 (jkl012)
  • status: in_progress → completed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Summary: 4 changes across 4 commits
Duration: 8 hours
```

---

### vibey git progress

Show sprint progress over time (for burndown charts).

**Usage:**
```bash
vibey git progress <sprint-id> [OPTIONS]
```

**Options:**
- `--interval <N>` - Sample every N commits (default: 10)
- `--format <format>` - Output format: `chart` (default), `table`, `json`
- `--repo <path>` - Repository path

**Examples:**
```bash
# Show progress chart
vibey git progress git-integration-1

# Sample more frequently
vibey git progress git-integration-1 --interval 5

# Export data for external charting
vibey git progress git-integration-1 --format json > progress.json
```

**Output:**
```
Sprint Progress: git-integration-1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tasks Completion Over Time
100% ┤                                            ╭──
 90% ┤                                         ╭──╯
 80% ┤                                      ╭──╯
 70% ┤                                   ╭──╯
 60% ┤                                ╭──╯
 50% ┤                            ╭───╯
 40% ┤                        ╭───╯
 30% ┤                    ╭───╯
 20% ┤               ╭────╯
 10% ┤          ╭────╯
  0% ┼──────────╯
     └────┬────┬────┬────┬────┬────┬────┬────┬
       Nov 1  Nov 3  Nov 5  Nov 7  Nov 9  Nov 11  Nov 13  Nov 15

📊 Progress Points (sampled every 10 commits)
─────────────────────────────────────────────────
2025-11-01: 0/9 tasks (0%)
2025-11-03: 1/9 tasks (11%)
2025-11-05: 2/9 tasks (22%)
2025-11-07: 4/9 tasks (44%)
2025-11-09: 5/9 tasks (56%)
2025-11-11: 6/9 tasks (67%)
2025-11-13: 7/9 tasks (78%)
2025-11-15: 8/9 tasks (89%)
```

---

### vibey git rollback

Rollback roadmap YAML files to state at specific ref.

**Usage:**
```bash
vibey git rollback <ref> [OPTIONS]
```

**Arguments:**
- `<ref>` - Git ref to rollback to

**Options:**
- `--dry-run` - Show what would be restored (default: true)
- `--execute` - Actually perform the rollback
- `--repo <path>` - Repository path

**Examples:**
```bash
# Preview rollback (dry run)
vibey git rollback abc123

# Actually rollback
vibey git rollback abc123 --execute

# Rollback to tag
vibey git rollback sprint/git-integration-0/end --execute
```

**Output (dry run):**
```
Rollback to: abc123 (2025-11-10 14:00:00)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  DRY RUN - No files will be modified

Files to restore:
─────────────────────────────────────────────────
✓ .vibey/roadmap/git-integration/track.yaml
✓ .vibey/roadmap/git-integration/git-integration-1/sprint.yaml
✓ .vibey/roadmap/user-journey-audit/track.yaml
[...]

Total: 15 files would be restored

Run with --execute to perform rollback
```

---

## Commit Message Formats

The parser supports multiple commit message formats for task references.

### 1. Conventional Commits Format

Use task ID as the scope in conventional commit format.

**Syntax:**
```
<type>(<task-id>): <description>

[optional body]

[optional footers]
```

**Examples:**
```bash
git commit -m "feat(git-integration-1-task-001): Implement commit parser"
git commit -m "fix(api-task-042): Fix authentication bug"
git commit -m "test(ml-sprint-2-task-005): Add unit tests"
```

**Parsed Fields:**
- Type: `feat`, `fix`, `test`, etc.
- Task ID: `git-integration-1-task-001`
- Sprint ID: `git-integration-1` (auto-extracted)
- Track ID: `git-integration` (auto-extracted)

### 2. Footer Format

Reference tasks in commit message footers.

**Syntax:**
```
<subject>

[body]

Task: <task-id>
Status: <status>
```

**Examples:**
```bash
git commit -m "Implement authentication

Task: auth-sprint-1-task-003
Status: completed"

git commit -m "Fix login bug

Fixes: api-task-042
Completes: api-task-042"
```

**Status Keywords:**
- `starts`, `addresses`, `wip` → `in_progress`
- `completes`, `closes`, `finishes`, `fixes`, `resolves` → `completed`
- `blocks`, `blocked` → `blocked`
- `reverts` → `reverted`

### 3. Bracket Format

Use brackets to reference tasks.

**Syntax:**
```
[<task-id>] <description>
```

**Examples:**
```bash
git commit -m "[git-integration-1-task-001] Implement parser"
git commit -m "[TASK-042] Fix bug in API"
```

### 4. Inline Format (Optional)

Reference tasks anywhere in the message (requires enabling in config).

**Syntax:**
```
Any message with task-id-pattern embedded
```

**Examples:**
```bash
git commit -m "Working on git-integration-1-task-001 implementation"
```

**Note:** Inline format has lower confidence and is disabled by default. Enable in parser config if needed.

---

## Tag Formats

Use Git tags as explicit milestones for sprints and tasks.

### Sprint Tags

**Format:**
```
sprint/<sprint-id>/start
sprint/<sprint-id>/end
```

**Examples:**
```bash
# Tag sprint start
git tag sprint/git-integration-1/start

# Tag sprint end
git tag sprint/git-integration-1/end
```

**Usage:**
- Velocity calculation uses sprint tags for automatic boundary detection
- State reconstruction can query at sprint boundaries
- Tag-based commit range queries

### Task Tags

**Format:**
```
<track-id>/<sprint-id>/<task-id>/<marker>
```

**Markers:**
- `start` - Task started
- `completed` - Task completed
- `blocked` - Task blocked
- `<custom>` - Any custom marker

**Examples:**
```bash
# Tag task start
git tag git-integration/git-integration-1/task-001/start

# Tag task completion
git tag git-integration/git-integration-1/task-001/completed

# Custom marker
git tag git-integration/git-integration-1/task-001/reviewed
```

**Benefits:**
- Explicit, immutable milestones
- Fast commit range queries (better than grepping all commits)
- Clear audit trail
- Integration with state reconstruction

---

## Python API

Use the git analysis modules programmatically.

### Commit Parser

```python
from vibey.operations.git import CommitParser, ParserConfig

# Create parser with default config
parser = CommitParser()

# Parse commit message
result = parser.parse("feat(task-123): Add feature")

# Check for task references
if result.has_task_reference:
    primary_task = result.primary_task
    print(f"Task: {primary_task.task_id}")
    print(f"Status: {primary_task.status}")
    print(f"Confidence: {primary_task.confidence}")

# Access all references
for task in result.tasks:
    print(f"- {task.task_id} ({task.format.value})")

# Check conventional commit fields
print(f"Type: {result.type}")
print(f"Scope: {result.scope}")
print(f"Breaking: {result.breaking}")

# Custom parser config
config = ParserConfig(
    parse_inline=True,  # Enable inline parsing
    case_sensitive=True,
    preferred_formats=[CommitFormat.FOOTER, CommitFormat.CONVENTIONAL]
)
parser = CommitParser(config=config)
```

### Git Log Analyzer

```python
from vibey.operations.git import GitLogAnalyzer

# Create analyzer
analyzer = GitLogAnalyzer(repo_path=".")

# Get commits with filters
commits = analyzer.get_commits(
    since="2025-11-01",
    until="2025-11-15",
    author="john@example.com",
    max_count=100
)

# Iterate commits
for commit in commits:
    print(f"{commit.sha[:7]} {commit.author_name}: {commit.message}")

    # Access parsed roadmap references
    if commit.parsed and commit.parsed.has_task_reference:
        print(f"  → Task: {commit.parsed.primary_task.task_id}")

# Get branches
branches = analyzer.get_branches()
for branch in branches:
    print(f"{'*' if branch.is_current else ' '} {branch.name}")

# Get tags
tags = analyzer.get_tags()
for tag in tags:
    print(f"{tag.name} ({tag.sha[:7]})")

# Get commit by SHA
commit = analyzer.get_commit_by_sha("abc123")
```

### Velocity Calculator

```python
from vibey.operations.git import VelocityCalculator

# Create calculator
calc = VelocityCalculator(repo_path=".")

# Calculate sprint velocity
velocity = calc.calculate_sprint_velocity(
    sprint_id="git-integration-1",
    start_date="2025-11-01",
    end_date="2025-11-15"
)

print(f"Total commits: {velocity.total_commits}")
print(f"Commits/day: {velocity.commits_per_day:.1f}")
print(f"Tasks worked: {velocity.tasks_worked}")
print(f"Tasks completed: {velocity.tasks_completed}")
print(f"Contributors: {velocity.unique_contributors}")

# Calculate velocity trend
trend = calc.calculate_velocity_trend(
    sprint_ids=["sprint-1", "sprint-2", "sprint-3"]
)

print(f"Average velocity: {trend.average_commits_per_day:.1f}")
print(f"Trend: {trend.trend}")  # "increasing", "decreasing", "stable"

# Calculate contributor velocity
contrib_velocity = calc.calculate_contributor_velocity(
    since="2025-11-01",
    until="2025-11-15"
)

for name, metrics in contrib_velocity.items():
    print(f"{name}: {metrics['commits']} commits, {metrics['tasks']} tasks")
```

### Tag Parser

```python
from vibey.operations.git import TagParser

# Create parser
parser = TagParser(repo_path=".")

# Get sprint boundary tags
start_tag, end_tag = parser.get_sprint_boundary_tags("git-integration-1")
if start_tag and end_tag:
    print(f"Sprint: {start_tag.tag_info.sha[:7]}..{end_tag.tag_info.sha[:7]}")

# Get commits for sprint (using tags)
commits = parser.get_commits_for_sprint_by_tags("git-integration-1")
if commits:
    print(f"Sprint has {len(commits)} commits")

# Get task tags
task_tags = parser.get_task_tags("git-integration-1-task-001")
for tag in task_tags:
    print(f"{tag.marker}: {tag.tag_info.sha[:7]}")

# Parse all Vibey tags
all_tags = parser.get_all_vibey_tags()
sprint_tags = [t for t in all_tags if t.tag_type.name.startswith("SPRINT")]
task_tags = [t for t in all_tags if t.tag_type.name.startswith("TASK")]
```

### State Reconstructor

```python
from vibey.operations.git import StateReconstructor

# Create reconstructor
reconstructor = StateReconstructor(repo_path=".")

# Get state at ref
state = reconstructor.get_state_at("abc123")
print(f"State at {state.sha[:7]} by {state.author}")
print(f"Tracks: {len(state.tracks)}")
print(f"Sprints: {len(state.sprints)}")
print(f"Tasks: {len(state.tasks)}")

# Access state data
for track_id, track_data in state.tracks.items():
    print(f"Track: {track_id} ({track_data['status']})")

for task_id, task_data in state.tasks.items():
    print(f"Task: {task_id} - {task_data['status']}")

# Compare states
changes = reconstructor.diff_states("abc123", "def456")
for item_id, item_changes in changes.items():
    print(f"\n{item_id}:")
    for change in item_changes:
        print(f"  {change.field}: {change.old_value} → {change.new_value}")

# Get item history
history = reconstructor.get_history("git-integration-1-task-001", item_type="task")
for change in history:
    print(f"{change.commit_date}: {change.field} = {change.new_value}")

# Get progress timeline
timeline = reconstructor.get_progress_timeline("git-integration-1", sample_interval=10)
for point in timeline:
    print(f"{point.date}: {point.tasks_completed}/{point.tasks_total} ({point.completion_percent}%)")

# Rollback (dry run by default)
status = reconstructor.rollback("abc123", dry_run=True)
for file, message in status.items():
    print(f"{file}: {message}")

# Actually rollback
status = reconstructor.rollback("abc123", dry_run=False)
```

### Batch Analysis

```python
from vibey.operations.git import analyze_batch

# Prepare commits
commits = [
    {"message": "feat(task-1): Add feature", "sha": "abc123"},
    {"message": "fix(task-2): Fix bug", "sha": "def456"},
    {"message": "chore: Update deps", "sha": "ghi789"},
]

# Analyze batch
result = analyze_batch(commits)

print(f"Total: {result.total_commits}")
print(f"With tasks: {result.commits_with_tasks}")
print(f"Without tasks: {result.commits_without_tasks}")
print(f"Unique tasks: {len(result.unique_tasks)}")
print(f"Unique sprints: {len(result.unique_sprints)}")

# Access unique references
for task_id in result.unique_tasks:
    print(f"Task: {task_id}")
```

---

## Use Cases

### 1. Sprint Retrospective

Analyze what was accomplished during a sprint:

```bash
# Calculate sprint velocity
vibey git velocity git-integration-1

# Show task progress over time
vibey git progress git-integration-1

# See contributor activity
vibey git contributors --since 2025-11-01 --until 2025-11-15

# Review all tasks worked on
vibey git analyze --since 2025-11-01 --until 2025-11-15 --format table
```

### 2. Task Audit Trail

Track complete history of a task:

```bash
# See all commits for task
vibey git tasks git-integration-1-task-001 --show-files

# See state changes over time
vibey git history git-integration-1-task-001

# Check task state at specific point
vibey git state-at abc123 --item git-integration-1-task-001
```

### 3. Burndown Chart Generation

Export data for burndown charts:

```bash
# Get progress data
vibey git progress git-integration-1 --format json > burndown.json

# Use in external charting tool
python scripts/generate_burndown_chart.py burndown.json
```

### 4. Contributor Analysis

Analyze team productivity:

```bash
# Overall contributor stats
vibey git contributors

# Active contributors this month
vibey git contributors --since 2025-11-01 --min-commits 5

# Contributor velocity by sprint
vibey git velocity git-integration-1 --format detailed
```

### 5. Historical State Queries

Investigate roadmap state at different points:

```bash
# State at sprint end
vibey git state-at sprint/git-integration-1/end

# State 2 weeks ago
vibey git state-at 2025-11-01

# Compare two states
vibey git state-at abc123 > state1.json
vibey git state-at def456 > state2.json
diff state1.json state2.json
```

### 6. Rollback After Mistake

Undo incorrect roadmap updates:

```bash
# Preview rollback
vibey git rollback HEAD~5

# Execute rollback
vibey git rollback HEAD~5 --execute

# Commit the rollback
git add .vibey/roadmap/
git commit -m "chore: Rollback roadmap to correct state"
```

---

## Best Practices

### Commit Message Conventions

1. **Always reference tasks** in commits that implement work
   ```bash
   # Good
   git commit -m "feat(task-001): Implement user auth"

   # Bad
   git commit -m "Add auth"
   ```

2. **Use status keywords** in footers for explicit state changes
   ```bash
   git commit -m "Final tests passing

   Completes: task-001"
   ```

3. **Prefer conventional commits** for consistency
   ```bash
   feat(task-id): Add new feature
   fix(task-id): Fix bug
   test(task-id): Add tests
   docs(task-id): Update docs
   ```

4. **Include sprint/track context** in task IDs
   ```bash
   # Good (full context)
   git commit -m "feat(git-integration-1-task-001): ..."

   # Acceptable (task ID only)
   git commit -m "feat(task-001): ..."
   ```

### Tagging Strategy

1. **Tag sprint boundaries** for accurate velocity
   ```bash
   git tag sprint/git-integration-1/start
   # ... do sprint work ...
   git tag sprint/git-integration-1/end
   ```

2. **Tag task milestones** for important events
   ```bash
   git tag git-integration/git-integration-1/task-001/start
   git tag git-integration/git-integration-1/task-001/completed
   ```

3. **Use annotated tags** for important milestones
   ```bash
   git tag -a sprint/git-integration-1/end -m "Sprint 1 complete: 9/9 tasks"
   ```

### Analysis Workflow

1. **Regular velocity checks** after each sprint
   ```bash
   vibey git velocity <sprint-id> > velocity-report.txt
   ```

2. **Weekly contributor reports**
   ```bash
   vibey git contributors --since 7.days.ago --format json > weekly-stats.json
   ```

3. **State snapshots** at key milestones
   ```bash
   vibey git state-at HEAD --format json > state-$(date +%Y%m%d).json
   ```

4. **Automated analysis** in CI/CD
   ```yaml
   # .github/workflows/roadmap-analysis.yml
   - name: Analyze roadmap
     run: vibey git analyze --format json > analysis.json

   - name: Check velocity
     run: vibey git velocity ${{ github.ref_name }}
   ```

### State Management

1. **Backup before rollback**
   ```bash
   cp -r .vibey/roadmap .vibey/roadmap.backup
   vibey git rollback <ref> --execute
   ```

2. **Use tags for rollback points**
   ```bash
   git tag roadmap/checkpoint/before-major-update
   # ... make updates ...
   # If needed:
   vibey git rollback roadmap/checkpoint/before-major-update --execute
   ```

3. **Regular state validation**
   ```bash
   vibey roadmap validate
   vibey git analyze --format json | jq '.commits_with_tasks'
   ```

---

## Troubleshooting

### Issue: No tasks detected in commits

**Cause:** Task IDs not matching parser patterns

**Solution:**
```bash
# Check what was parsed
vibey git analyze --format detailed

# Verify task ID format
# Must match: <track>-<sprint>-task-<number> or similar

# Use footer format as fallback
git commit -m "Implement feature

Task: git-integration-1-task-001"
```

### Issue: Velocity calculation incorrect

**Cause:** Missing or incorrect sprint boundary tags

**Solution:**
```bash
# Check existing tags
vibey git tags --sprint <sprint-id>

# Add missing tags
git tag sprint/<sprint-id>/start <start-commit>
git tag sprint/<sprint-id>/end <end-commit>

# Recalculate
vibey git velocity <sprint-id>
```

### Issue: State reconstruction missing data

**Cause:** Roadmap files not committed at that point in history

**Solution:**
```bash
# Verify file exists at ref
git show <ref>:.vibey/roadmap/<track>/track.yaml

# Check commit history
git log --all -- .vibey/roadmap/

# Use earlier/later ref
vibey git state-at <different-ref>
```

### Issue: Rollback doesn't restore all files

**Cause:** Files added after the rollback point

**Solution:**
```bash
# Preview what will be restored
vibey git rollback <ref>

# Manual cleanup if needed
git checkout <ref> -- .vibey/roadmap/
```

---

## Related Documentation

- **[Roadmap System Reference](../reference/ROADMAP_SYSTEM.md)** - Roadmap data model
- **[CLI Reference](../reference/CLI_REFERENCE.md)** - All CLI commands
- **[Workflow Guide](../guides/WORKFLOW_GUIDE.md)** - Development workflows

---

## Implementation Details

**Module:** `vibey.operations.git`
**Entry Point:** `vibey.cli.git_commands`
**Tests:** `tests/unit/test_git_operations.py` (44 tests)

**Components:**
- `commit_parser_schema.py` - Data structures and interfaces
- `commit_parser.py` - Multi-format commit message parser
- `log_analyzer.py` - Git log analysis and querying
- `velocity_calculator.py` - Sprint velocity metrics
- `tag_parser.py` - Vibey roadmap tag parsing
- `state_reconstructor.py` - Time-travel state queries

**Coverage:**
- Commit parser: 88.2%
- Log analyzer: 59.4%
- Velocity calculator: 41.3%
- Tag parser: 36.7%
- State reconstructor: 25.0%
- CLI commands: 15.9%

---

**Last Updated:** 2025-11-24
**Sprint:** git-integration-1
**Task:** git-integration-1-task-007
