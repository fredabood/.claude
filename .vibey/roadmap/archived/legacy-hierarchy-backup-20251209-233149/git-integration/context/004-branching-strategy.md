# Branching Strategy Specification

**Task:** git-integration-0-task-004
**Status:** Draft
**Author:** Architecture Agent
**Date:** 2025-11-24

## Executive Summary

This document defines how Vibey roadmap structure optionally maps to Git branches. Vibey supports multiple branching strategies without enforcing any particular approach.

## Design Philosophy

**Key Principle:** Vibey adapts to your Git workflow, not the other way around.

Vibey provides optional branch conventions that can enhance traceability, but teams are free to use:
- Trunk-based development
- GitFlow
- GitHub Flow
- Any custom branching strategy

## Branching Models

### Model A: Trunk-Based Development (Default)

```
main (trunk)
│
├── All commits with task references
├── Feature flags for incomplete work
└── Continuous integration/deployment
```

**Characteristics:**
- Single long-lived branch (main/master)
- Short-lived feature branches (optional, < 1 day)
- Task references in commit messages only
- No branch naming conventions required

**Roadmap Mapping:**
- Tracks: No branch representation
- Sprints: No branch representation (tags optional)
- Tasks: Commits on main, not branches

**Example Workflow:**
```bash
# Work directly on main
git checkout main
git pull

# Make changes
# ... edit files ...

# Commit with task reference
git commit -m "feat(task-001): implement feature"

# Push
git push origin main
```

**Best For:**
- Small teams (1-5 developers)
- Continuous deployment environments
- High-trust, experienced teams
- Projects requiring fast iteration

### Model B: Feature Branch Development

```
main
│
├── feature/task-001-content-loader
│   └── commits for task-001
│
├── feature/task-002-cli-commands
│   └── commits for task-002
│
└── feature/task-003-tests
    └── commits for task-003
```

**Characteristics:**
- Long-lived main branch
- Short-lived feature branches per task
- PR-based merging
- Branch name contains task ID

**Branch Naming Convention:**
```
feature/<task-id>-<description>
bugfix/<task-id>-<description>
docs/<task-id>-<description>
refactor/<task-id>-<description>
```

**Example:**
```bash
# Create feature branch
git checkout -b feature/task-001-content-loader

# Make commits
git commit -m "feat(task-001): add ContentLoader class"
git commit -m "test(task-001): add unit tests"

# Push and create PR
git push -u origin feature/task-001-content-loader
gh pr create --title "feat(task-001): implement content loader"

# After merge, delete branch
git branch -d feature/task-001-content-loader
```

**Best For:**
- Medium teams (5-15 developers)
- Code review culture
- PR-based workflows
- Projects needing isolation

### Model C: Sprint Branch Development

```
main
│
├── sprint/python-package-3
│   ├── All tasks for Sprint 3
│   └── Merged to main at sprint end
│
└── sprint/git-integration-1
    ├── All tasks for Git Integration Sprint 1
    └── Merged to main at sprint end
```

**Characteristics:**
- Integration branches per sprint
- Tasks developed on sprint branch
- Sprint branch merged to main at completion
- Good for release coordination

**Branch Naming Convention:**
```
sprint/<sprint-id>
```

**Example:**
```bash
# Start sprint
git checkout -b sprint/python-package-3 main

# Work on tasks
git commit -m "feat(task-001): implement content loader"
git commit -m "feat(task-002): add CLI commands"
# ... more task commits ...

# Sprint complete - create release
git tag sprint/python-package-3/end
git checkout main
git merge --no-ff sprint/python-package-3

# Optional: delete sprint branch
git branch -d sprint/python-package-3
```

**Best For:**
- Teams with defined sprint cycles
- Release coordination needs
- Larger teams wanting sprint isolation
- Projects with scheduled releases

### Model D: Track Branch Development (GitFlow-style)

```
main (production)
│
├── develop (integration)
│   │
│   ├── track/python-package
│   │   ├── sprint/python-package-3
│   │   │   └── feature/task-001
│   │   └── Merged to develop at track completion
│   │
│   └── track/git-integration
│       └── Merged to develop at track completion
│
└── Releases cut from develop → main
```

**Characteristics:**
- Full hierarchy: main → develop → track → sprint → feature
- Maximum isolation
- Complex but controlled
- Good for enterprise/regulated environments

**Branch Naming Convention:**
```
develop               # Integration branch
track/<track-id>      # Track integration
sprint/<sprint-id>    # Sprint integration (optional)
feature/<task-id>     # Task feature branch
```

**Best For:**
- Large teams (15+ developers)
- Multiple tracks in parallel
- Regulated environments
- Complex release management

### Model E: Flexible/Hybrid

```
main
│
├── developer-1/experiment
├── feature/cool-thing
├── sprint/q4-release
├── task-001-quick-fix
└── (any naming convention)
```

**Characteristics:**
- No enforced conventions
- Vibey parses branch names for task IDs
- Works with existing team practices
- Maximum flexibility

**Vibey Behavior:**
- Scans branch names for task ID patterns
- Associates branches with tasks when found
- No enforcement or requirements
- Suggestions only

**Best For:**
- Teams with established conventions
- Gradual Vibey adoption
- Mixed workflows
- Transitioning teams

## Branch-Task Association

### Automatic Detection

Vibey can detect task associations from branch names:

```yaml
# .vibey/config/git.yaml
git:
  branch:
    auto_detect: true
    patterns:
      # Patterns to extract task ID from branch name
      - "feature/(?P<task_id>[\\w-]+-task-\\d+)"
      - ".*(?P<task_id>[\\w-]+-\\d+-task-\\d+)"
      - "task-(?P<task_id>\\d+)"
```

### Manual Association

Tasks can explicitly reference branches:

```yaml
# sprint.yaml
tasks:
  - id: task-001
    branch: feature/task-001-content-loader
    status: in_progress
```

### Association Commands

```bash
# Link current branch to task
vibey git link-branch task-001

# Show branch associations
vibey git branches

# Output:
task-001: feature/task-001-content-loader (active)
task-002: feature/task-002-cli-commands (merged)
task-003: (no branch)
```

## Sprint Tagging

Regardless of branching model, sprints can be marked with tags:

### Sprint Boundary Tags

```bash
# Mark sprint start
git tag sprint/python-package-3/start

# Mark sprint end
git tag sprint/python-package-3/end

# Query sprint commits
git log sprint/python-package-3/start..sprint/python-package-3/end
```

### Automatic Tagging

```bash
# Vibey command to create sprint tags
vibey sprint start python-package-3
# Creates: sprint/python-package-3/start tag

vibey sprint complete python-package-3
# Creates: sprint/python-package-3/end tag
```

## Merge Strategies

### Feature to Main (Trunk-Based)

```bash
# Fast-forward or squash merge
git checkout main
git merge feature/task-001 --ff-only
# or
git merge feature/task-001 --squash
```

### Sprint to Main

```bash
# Merge commit preserving history
git checkout main
git merge sprint/python-package-3 --no-ff -m "chore: complete Sprint 3"
```

### Track to Develop (GitFlow)

```bash
# Merge commit
git checkout develop
git merge track/python-package --no-ff -m "chore: complete Python Package track"
```

### Merge Commit Messages

```bash
# Sprint merge
Merge sprint/python-package-3 into main

Sprint: python-package-3
Status: completed
Tasks: 10/10 completed

# Track merge
Merge track/python-package into develop

Track: python-package
Status: completed
Sprints: 3/3 completed
Tasks: 24/24 completed
```

## Configuration

```yaml
# .vibey/config/git.yaml
git:
  branching:
    # Branching model preference
    model: feature  # trunk|feature|sprint|track|flexible

    # Branch naming
    prefixes:
      feature: "feature/"
      bugfix: "bugfix/"
      sprint: "sprint/"
      track: "track/"
      docs: "docs/"

    # Auto-create branches
    auto_create: false  # Create branch when starting task

    # Branch cleanup
    delete_merged: true  # Delete branches after merge
    stale_days: 30       # Warn about branches older than this

  # Tag conventions
  tags:
    sprint_start: "sprint/{sprint_id}/start"
    sprint_end: "sprint/{sprint_id}/end"
    track_complete: "track/{track_id}/complete"

  # Branch-task association
  association:
    auto_detect: true
    require_branch: false  # Require branch for tasks
```

## CLI Commands

### Branch Management

```bash
# Create task branch
vibey git branch create task-001
# Creates: feature/task-001-<task-name>

# List branches with task associations
vibey git branches
# Output:
# Branch                           Task         Status
# feature/task-001-content-loader  task-001     in_progress
# feature/task-002-cli-commands    task-002     not_started
# main                             -            -

# Link existing branch to task
vibey git branch link feature/my-branch task-001

# Check branch task association
vibey git branch info feature/task-001-content-loader
```

### Sprint Tags

```bash
# Create sprint start tag
vibey git tag sprint-start python-package-3

# Create sprint end tag
vibey git tag sprint-end python-package-3

# List sprint tags
vibey git tags
```

## Team Size Recommendations

| Team Size | Recommended Model | Rationale |
|-----------|-------------------|-----------|
| 1-2 | Trunk-based | Minimal overhead |
| 3-5 | Trunk or Feature | PR reviews helpful |
| 6-10 | Feature | Isolation important |
| 11-20 | Sprint or Feature | Sprint coordination |
| 20+ | Track (GitFlow) | Full hierarchy needed |

## Migration Paths

### From No Convention to Feature Branches

1. Start creating feature branches for new tasks
2. Link branches to tasks: `vibey git branch link`
3. Gradually adopt naming convention
4. Enable `auto_detect: true`

### From Feature to Sprint Branches

1. Create sprint branch at sprint start
2. Merge feature branches to sprint branch
3. Merge sprint branch to main at completion
4. Enable sprint tagging

### From Sprint to Track Branches

1. Create track branches for each track
2. Merge sprint branches to track branch
3. Merge track branch to develop
4. Cut releases from develop to main

## Workflow Examples

### Solo Developer (Trunk-Based)

```bash
# Start of day
git pull origin main

# Work on task
# ... make changes ...
git commit -m "feat(task-001): implement feature"
git commit -m "test(task-001): add tests"

# Push
git push origin main

# Mark task complete
vibey task complete task-001
```

### Team with PRs (Feature Branch)

```bash
# Start task
vibey task start task-001
git checkout -b feature/task-001-content-loader

# Work on task
# ... make changes ...
git commit -m "feat(task-001): implement feature"
git push -u origin feature/task-001-content-loader

# Create PR
gh pr create

# After review and merge
vibey task complete task-001
```

### Sprint Team (Sprint Branch)

```bash
# Sprint start
vibey sprint start python-package-3
git checkout -b sprint/python-package-3

# Work on tasks (directly or via feature branches)
git commit -m "feat(task-001): implement feature"
git commit -m "feat(task-002): add CLI commands"

# Sprint complete
vibey sprint complete python-package-3
git checkout main
git merge --no-ff sprint/python-package-3
git push origin main
```

## Appendix: Branch Name Patterns

```python
# Pattern to extract task ID from branch names
BRANCH_PATTERNS = [
    # feature/task-001-description
    r"^(?:feature|bugfix|docs|refactor)/(?P<task_id>[\w-]+-task-\d+)",

    # feature/python-package-3-task-001-description
    r"^(?:feature|bugfix|docs|refactor)/(?P<task_id>[\w-]+-\d+-task-\d+)",

    # task-001/description
    r"^(?P<task_id>task-\d+)/",

    # sprint/sprint-id
    r"^sprint/(?P<sprint_id>[\w-]+-\d+)$",

    # track/track-id
    r"^track/(?P<track_id>[\w-]+)$",

    # Flexible: any branch containing task ID
    r"(?P<task_id>[\w-]+-\d+-task-\d+)",
]
```

## Decision Log

| Decision | Options Considered | Choice | Rationale |
|----------|-------------------|--------|-----------|
| Default model | Trunk, Feature, None | Feature-based default | Balance of simplicity and structure |
| Enforcement | Required, Optional | Optional | Support diverse workflows |
| Auto-create branches | Yes, No | No (configurable) | Don't surprise users |
| Sprint tags | Required, Optional | Optional but recommended | Lightweight, high value |
| Track branches | Required, Optional | Optional | Only for large teams |
