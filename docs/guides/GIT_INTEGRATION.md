# Git Integration Guide

Comprehensive documentation for Vibey's Git integration system.

## Overview

Vibey's Git integration connects your roadmap to Git workflows, providing:

- **Commit Message Parsing**: Automatically correlate commits to tasks/sprints
- **Branch Linking**: Create and manage task-specific branches
- **Status Updates**: Update roadmap status from Git activity
- **Dependency Enforcement**: Ensure merge order respects dependencies
- **CI/CD Integration**: Connect quality gates to CI checks
- **Strategy Presets**: Adopt standardized Git workflows

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Git Integration                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Commit    │  │   Branch    │  │   Status    │             │
│  │   Parser    │  │   Linker    │  │   Updater   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Merge     │  │   Blocker   │  │     CI      │             │
│  │  Ordering   │  │  Enforcer   │  │ Integration │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Strategy   │  │    Tag      │  │   Error     │             │
│  │  Adoption   │  │  Repairer   │  │  Handler    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Choose a Strategy

```bash
# List available strategies
vibey git strategy list

# Adopt a strategy
vibey git strategy adopt feature-branch
```

### 2. Create Task Branches

```bash
# Create a branch for your task
git checkout -b feature/my-track-1-task-001

# Or use vibey to create it
vibey git branch create my-track-1-task-001
```

### 3. Make Commits

Use conventional commit format with task references:

```bash
git commit -m "feat(my-track-1-task-001): Add new feature

Implements the core functionality for task 001.

Task: my-track-1-task-001"
```

### 4. Check Dependencies Before Merging

```bash
# Check if branch is safe to merge
vibey git dependency-check feature/my-track-1-task-001
```

## Strategy Presets

### Trunk-Based Development

**Best for**: Small teams, continuous deployment, rapid iteration

```yaml
enforcement: advisory
branch_patterns:
  main: ^main$|^master$
hooks_enabled:
  - commit-msg
```

**Workflow**:
1. All work happens on main
2. Feature flags control incomplete work
3. Deploy multiple times per day

### Feature Branch Workflow

**Best for**: Most teams, code review required

```yaml
enforcement: advisory
branch_patterns:
  main: ^main$|^master$
  feature: ^feature/[\w-]+-task-\d+$
  bugfix: ^bugfix/[\w-]+$
hooks_enabled:
  - pre-commit
  - commit-msg
```

**Workflow**:
1. Create branch per task: `feature/track-1-task-001`
2. Make commits, push for review
3. Create PR, pass checks
4. Merge to main

### GitFlow

**Best for**: Scheduled releases, enterprise teams

```yaml
enforcement: blocking
branch_patterns:
  main: ^main$|^master$
  develop: ^develop$
  feature: ^feature/[\w-]+$
  release: ^release/v?\d+\.\d+$
  hotfix: ^hotfix/[\w-]+$
hooks_enabled:
  - pre-commit
  - commit-msg
  - pre-push
```

**Workflow**:
1. Feature branches from develop
2. Release branches for stabilization
3. Hotfix branches from main
4. Merge releases to both main and develop

### Hierarchical

**Best for**: Complex projects, strict audit requirements

```yaml
enforcement: blocking
branch_patterns:
  main: ^main$|^master$
  track: ^track/[\w-]+$
  sprint: ^sprint/[\w-]+-\d+$
  task: ^feature/[\w-]+-task-\d+$
hooks_enabled:
  - pre-commit
  - commit-msg
  - pre-push
```

**Workflow**:
1. Track branches for each track
2. Sprint branches for releases (optional)
3. Task branches for individual work
4. Merge task → track → main

## Commit Message Format

### Conventional Commits

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Scope**: Task ID is recommended

```bash
# Example
git commit -m "feat(track-1-task-002): Add user authentication

Implements JWT-based authentication flow.

Task: track-1-task-002
Status: completed"
```

### Task Reference Patterns

Vibey recognizes these patterns:

```
# In commit message subject
feat(track-1-task-002): Description
[track-1-task-002] Description
feat: Description (track-1-task-002)

# In commit body
Task: track-1-task-002
Closes: track-1-task-002
Related: track-1-task-002
```

## Dependency Management

### Check Dependencies

```bash
# Check if a branch can be merged
vibey git dependency-check feature/track-1-task-002

# Output:
# Dependency Check: track-1-task-002
# ===================================
# Status: SAFE
#
# Satisfied Dependencies:
#   ✓ track-1-task-001 (completed)
#
# Ready to merge!
```

### Merge Order

```bash
# Get recommended merge order
vibey git merge-order

# Output:
# Recommended Merge Order
# =======================
# 1. feature/track-1-task-001 (no dependencies)
# 2. feature/track-1-task-002 (depends on: task-001)
# 3. feature/track-1-task-003 (depends on: task-002)
```

### Override Dependencies

For exceptional cases:

```bash
# Merge with dependency override
vibey git dependency-check feature/track-1-task-003 --allow-override

# Output:
# Dependency Check: track-1-task-003
# ===================================
# Status: OVERRIDE
#
# Unsatisfied Dependencies:
#   ✗ track-1-task-002 (in_progress)
#
# WARNING: Merging out of order may cause issues
```

## Blocker Enforcement

### Enforcement Modes

- **OFF**: No enforcement
- **ADVISORY**: Warn but allow
- **BLOCKING**: Prevent invalid operations
- **AUDIT**: Log all violations

### Configure Enforcement

```yaml
# .vibey/config/git.yaml
git:
  blocker_enforcement:
    mode: advisory
    check_on_commit: true
    check_on_push: true
```

### Check Blockers

```bash
# Check if work is blocked
vibey git blocker-status track-1-task-002

# Output:
# Blocker Status: track-1-task-002
# ================================
# Status: BLOCKED
#
# Blocked by:
#   - track-1-task-001: in_progress → needs: completed
#
# Cannot start until dependencies complete.
```

## CI/CD Integration

### Quality Gate Mapping

```yaml
# .vibey/config/git.yaml
git:
  ci_integration:
    platform: github  # or gitlab, jenkins
    gate_mapping:
      test_coverage:
        ci_job: coverage
        threshold: 80
      test_pass_rate:
        ci_job: tests
        threshold: 100
      documentation:
        ci_job: docs
        required: false
```

### GitHub Actions Integration

```yaml
# .github/workflows/vibey-gates.yml
name: Vibey Quality Gates

on: [pull_request]

jobs:
  check-gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check Quality Gates
        run: |
          pip install vibey
          vibey git ci-status --format github
```

### GitLab CI Integration

```yaml
# .gitlab-ci.yml
vibey-gates:
  stage: validate
  script:
    - pip install vibey
    - vibey git ci-status --format gitlab
  artifacts:
    reports:
      dotenv: vibey-gates.env
```

## Git Hooks

### Pre-commit Hook

Validates commit before creation:

```bash
# Install hook
vibey git hooks install pre-commit

# Hook checks:
# - Task exists in roadmap
# - Task is not blocked
# - Commit message format
```

### Commit-msg Hook

Validates and enhances commit message:

```bash
# Install hook
vibey git hooks install commit-msg

# Hook actions:
# - Validate conventional commit format
# - Extract task reference
# - Add task metadata to footer
```

### Pre-push Hook

Validates before pushing:

```bash
# Install hook
vibey git hooks install pre-push

# Hook checks:
# - All tasks in commits exist
# - No blocked tasks being pushed
# - Branch naming conventions
```

## Troubleshooting

### Common Issues

#### "Task not found in roadmap"

```bash
# Check task exists
vibey roadmap show <task-id>

# If missing, ensure roadmap is synced
vibey roadmap sync
```

#### "Dependency not satisfied"

```bash
# Check what's blocking
vibey git blocker-status <task-id>

# Complete blocking tasks first, or use override
vibey git dependency-check <branch> --allow-override
```

#### "Branch name doesn't match pattern"

```bash
# Check current strategy
vibey git strategy show

# Rename branch to match pattern
git branch -m old-name feature/track-1-task-001
```

#### "Merge conflict with status files"

```bash
# Always accept incoming roadmap changes
git checkout --theirs .vibey/roadmap/
git add .vibey/roadmap/

# Then commit the merge
git commit -m "Merge with roadmap sync"
```

### Debug Mode

```bash
# Enable verbose logging
export VIBEY_DEBUG=1

# Run command with debug output
vibey git dependency-check <branch>
```

## Migration Guide

### From No Git Integration

1. Initialize Vibey in your repo
2. Choose and adopt a strategy
3. Install git hooks
4. Start using task branches

```bash
vibey roadmap init
vibey git strategy adopt feature-branch
vibey git hooks install all
```

### From Custom Git Workflow

1. Map existing conventions to Vibey patterns
2. Update branch naming if needed
3. Configure git.yaml for your patterns

```yaml
# .vibey/config/git.yaml
git:
  strategy:
    preset: feature-branch
    customizations:
      branch_patterns:
        feature: ^feat/.*$  # Your existing pattern
```

### From GitFlow

1. Adopt gitflow preset
2. Configure develop branch
3. Update CI to use Vibey gates

```bash
vibey git strategy adopt gitflow
git checkout -b develop  # If not exists
```

## API Reference

### Python API

```python
from vibey.operations.git import (
    # Commit parsing
    CommitParser,
    analyze_batch,

    # Branch operations
    BranchLinker,
    create_task_branch,

    # Status updates
    TaskStatusUpdater,
    update_from_commit,

    # Dependency checking
    MergeOrderAnalyzer,
    check_branch_dependencies,

    # Blocker enforcement
    BlockerEnforcer,
    check_commit_blockers,

    # CI integration
    CIIntegration,
    check_ci_gates,

    # Strategy adoption
    StrategyAdoption,
    adopt_strategy,
)

# Example: Check if branch can merge
from vibey.operations.git import check_branch_dependencies

result = check_branch_dependencies('feature/task-002')
if result.can_merge:
    print("Safe to merge!")
else:
    print(f"Blocked by: {result.unsatisfied_dependencies}")
```

### CLI Reference

```bash
# Strategy commands
vibey git strategy list         # List presets
vibey git strategy adopt <name> # Adopt a preset
vibey git strategy show         # Show current config
vibey git strategy validate     # Validate requirements

# Dependency commands
vibey git merge-order           # Show recommended order
vibey git dependency-check <branch>  # Check branch

# Blocker commands
vibey git blocker-status <id>   # Check blockers

# CI commands
vibey git ci-status             # Check quality gates
vibey git ci-status --format github  # GitHub format

# Hook commands
vibey git hooks install <hook>  # Install hook
vibey git hooks list            # List hooks
```

## Best Practices

1. **Always use task branches**: Even for small changes
2. **Reference tasks in commits**: Helps with tracking
3. **Check dependencies before merge**: Avoid order issues
4. **Keep tasks small**: Easier to review and merge
5. **Use quality gates**: Catch issues early
6. **Review merge order**: Especially for dependent tasks
7. **Configure CI integration**: Automate gate checks
