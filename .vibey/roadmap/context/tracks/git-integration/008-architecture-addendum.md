# Architecture Addendum: Advanced Git Integration Patterns

**Status:** Draft Extension
**Date:** 2025-11-24
**Purpose:** Address advanced integration scenarios and clarifications

---

## 1. Multi-Repo and Submodules

### Question
How does the 1:1 roadmap:repository relationship work with Git submodules? Can parent and child repos each have roadmaps?

### Answer: Hierarchical Roadmaps (v2 Feature)

**Current (v1): Flat Model**
```
repository-a/
  .vibey/roadmap/  # Roadmap for this repo only

repository-b/
  .vibey/roadmap/  # Separate, independent roadmap
```

**Future (v2): Submodule Support**
```
parent-repo/
  .vibey/roadmap/parent.yaml       # Parent roadmap
  .vibey/config/submodules.yaml    # Submodule aggregation config

  submodules/
    service-a/
      .vibey/roadmap/service-a.yaml  # Child roadmap
    service-b/
      .vibey/roadmap/service-b.yaml  # Child roadmap
```

### Aggregation Model (v2)

```yaml
# .vibey/config/submodules.yaml
submodules:
  enabled: true

  modules:
    - path: submodules/service-a
      roadmap: service-a
      aggregate: true  # Include in parent stats

    - path: submodules/service-b
      roadmap: service-b
      aggregate: true

  aggregation:
    # How to combine child stats into parent
    mode: sum  # sum|average|max|manual

    # Parent track depends on child tracks
    dependencies:
      - parent_track: platform-integration
        requires:
          - service-a:api-core
          - service-b:data-pipeline
```

### Query Behavior

```bash
# Query parent roadmap only
vibey roadmap status --local

# Query with aggregation (includes submodules)
vibey roadmap status --aggregate

# Output:
Parent Repo (vibey-platform):
  Tracks: 3/5 (60%)
  Sprints: 8/12 (67%)
  Tasks: 45/80 (56%)

Submodules:
  service-a: 2/3 tracks (67%)
  service-b: 4/4 tracks (100%)

Aggregate:
  Total tracks: 9/12 (75%)
  Total sprints: 15/20 (75%)
  Total tasks: 78/110 (71%)
```

### Decision: v1 = Single Repo, v2 = Submodule Support

**v1 Behavior:**
- Each repository has its own independent roadmap
- No automatic aggregation
- Manual coordination across repos

**v2 Addition:**
- Parent can reference child roadmaps
- Optional aggregation of metrics
- Track dependencies across repos
- Not blocking v1 implementation

---

## 2. Task Tags (Explicit State Markers)

### Question
Should tasks use Git tags in addition to commit messages? What about tag structure?

### Answer: Task Tags are Optional Enhancement

**Tag Naming Convention:**
```
<track-id>/<sprint-id>/<task-id>/<marker>

Where <marker> is:
  start  - Task work begins
  end    - Task work completes
  (none) - Intermediate milestone
```

**Examples:**
```bash
# Task lifecycle with tags
git tag python-package/3/task-001/start abc123
# ... work happens across multiple commits ...
git tag python-package/3/task-001/milestone1 def456
git tag python-package/3/task-001/end ghi789

# Query all commits for a task
git log python-package/3/task-001/start..python-package/3/task-001/end

# Sprint boundary tags (already in architecture)
git tag python-package/3/start
git tag python-package/3/end
```

### Multiple Tags Per Commit

**Git allows multiple tags on the same commit:**

```bash
# A commit that completes task-001 and starts task-002
git tag python-package/3/task-001/end abc123
git tag python-package/3/task-002/start abc123

# A commit that works on multiple tasks simultaneously
git tag python-package/3/task-001 abc123
git tag python-package/3/task-002 abc123
```

This is particularly useful for:
- Commits spanning multiple tasks
- Sprint boundary commits
- Release markers

### Tag vs Commit Message Linkage

| Method | Explicit | Portable | Survives Squash | Query Performance |
|--------|----------|----------|-----------------|-------------------|
| Commit message | No (inferred) | Yes | Partial | Slow (parse all) |
| Git tags | Yes (direct) | Yes | No (requires repair) | Fast (tag refs) |
| YAML commits list | Yes | No (Vibey-specific) | Yes | Fast (direct lookup) |

**Recommended: Hybrid Approach**
- **Commit messages** - Primary linkage (survives squash)
- **Git tags** - Optional explicit markers (fast queries)
- **YAML commits** - Record of truth (source of truth)

### Configuration

```yaml
# .vibey/config/git.yaml
git:
  tags:
    # Sprint tags
    sprint_start: "{track_id}/{sprint_id}/start"
    sprint_end: "{track_id}/{sprint_id}/end"

    # Task tags (optional)
    task_tags:
      enabled: false  # Opt-in for v1
      format: "{track_id}/{sprint_id}/{task_id}/{marker}"
      auto_create: false  # Create tags automatically
      markers:
        - start
        - end
        # Custom markers can be added
```

### CLI Commands

```bash
# Create task start tag
vibey git tag task-start task-001

# Create task end tag
vibey git tag task-end task-001

# List all tags for a task
vibey git tags --task task-001

# Query commits between task tags
git log $(vibey git tag-range task-001)
# Equivalent to: git log python-package/3/task-001/start..python-package/3/task-001/end
```

---

## 3. Cross-Platform Tag Compatibility

### Question
How do Git tags work across GitHub, GitLab, Bitbucket?

### Answer: Tags are Git Native (Fully Portable)

**Git tags are part of the Git data model, not platform-specific:**

```bash
# Create tag locally
git tag sprint/python-package-3/start

# Push to any platform
git push origin sprint/python-package-3/start

# Or push all tags
git push origin --tags

# Works identically on:
# - GitHub
# - GitLab
# - Bitbucket
# - Azure DevOps
# - Self-hosted Git
```

### Platform UI Differences

| Platform | Tag UI | Tag API | Tag Protection |
|----------|--------|---------|----------------|
| GitHub | Releases + Tags | Yes | Yes (via rules) |
| GitLab | Tags page | Yes | Yes (protected tags) |
| Bitbucket | Tags page | Yes | No (branch only) |
| Azure DevOps | Tags | Yes | Yes (via policies) |

**All platforms support:**
- Creating tags via Git push
- Querying tags via API
- Annotated vs lightweight tags
- Tag naming patterns

**Platform-Specific Features:**
- GitHub: Tags can trigger releases
- GitLab: Protected tags (prevent deletion)
- Both: CI triggers on tag push

### Best Practices

```yaml
# Recommend lightweight tags for task markers
git tag task-001/start abc123

# Use annotated tags for releases
git tag -a v1.0.0 -m "Release version 1.0.0"

# Protected tags for sprint boundaries (GitLab)
# Prevents accidental deletion/movement
```

---

## 4. Tag Repair After Squash/Rebase

### Question
How do tags handle squash merges and rebases where commit SHAs change?

### Answer: Automated Tag Repair Process

**Problem:**
```bash
# Before rebase
abc123 [task-001/start] feat: begin work
def456 [task-001] feat: continue work
ghi789 [task-001/end] feat: complete work

# After rebase (new SHAs)
xyz123 feat: begin work        # abc123 is gone
uvw456 feat: continue work      # def456 is gone
rst789 feat: complete work      # ghi789 is gone

# Tags still point to old SHAs (now dangling)
task-001/start → abc123 (doesn't exist)
task-001/end → ghi789 (doesn't exist)
```

### Repair Algorithm

```python
def repair_tags_after_rebase(branch: str):
    """
    Re-apply task tags to new commits after rebase/squash.

    Strategy:
    1. Find dangling tags (point to non-existent commits)
    2. Match by commit message to find new commit
    3. Re-create tag on new commit
    """

    dangling_tags = find_dangling_tags(branch)

    for tag in dangling_tags:
        # Parse tag to get task ID
        task_id = parse_tag_name(tag.name)

        # Get original commit message
        original_message = tag.annotation or get_commit_message(tag.old_sha)

        # Find new commit with matching message
        new_commits = git_log(branch, grep=task_id)
        new_commit = find_best_match(new_commits, original_message)

        if new_commit:
            # Delete old tag
            git_tag_delete(tag.name)

            # Re-create on new commit
            git_tag_create(tag.name, new_commit.sha)

            log(f"Repaired: {tag.name} {tag.old_sha} → {new_commit.sha}")
        else:
            warn(f"Could not repair tag {tag.name}: no matching commit")
```

### Automated Repair Hooks

```bash
# Post-rebase hook
.git/hooks/post-rebase

#!/bin/bash
vibey git repair-tags --branch $(git branch --show-current)

# Post-merge hook (for squash merges)
.git/hooks/post-merge

#!/bin/bash
if [ "$GIT_REFLOG_ACTION" = "merge --squash" ]; then
    vibey git repair-tags --branch $(git branch --show-current)
fi
```

### Manual Repair

```bash
# Detect dangling tags
vibey git validate-tags

# Output:
⚠ Found 3 dangling tags:
  task-001/start → abc123 (commit not found)
  task-001/end → ghi789 (commit not found)
  task-002/start → def456 (commit not found)

# Repair automatically
vibey git repair-tags

# Output:
✓ Repaired task-001/start: abc123 → xyz123
✓ Repaired task-001/end: ghi789 → rst789
✗ Could not repair task-002/start (no matching commit)

# Repair specific tag manually
vibey git tag-move task-002/start <new-sha>
```

### Configuration

```yaml
git:
  tags:
    repair:
      auto: true  # Automatic repair after rebase/squash
      strategy: message_match  # message_match|manual|skip
      confirm: false  # Require confirmation before repair
```

---

## 5. Branch Hierarchy (Full GitFlow Support)

### Question
Can we support track/sprint/task branch hierarchies with explicit merge flows?

### Answer: Full Hierarchical Branching (Optional)

**Branch Hierarchy:**
```
main (production releases)
  ↑
develop (integration branch)
  ↑
track/python-package (track-level integration)
  ↑
sprint/python-package-3 (sprint-level integration)
  ↑
task/python-package-3-task-001 (task-level work)
```

### Merge Flow

```bash
# 1. Create hierarchy
git checkout -b develop main
git checkout -b track/python-package develop
git checkout -b sprint/python-package-3 track/python-package
git checkout -b task/python-package-3-task-001 sprint/python-package-3

# 2. Work on task
# ... commits ...

# 3. Complete task → merge to sprint
git checkout sprint/python-package-3
git merge --no-ff task/python-package-3-task-001
vibey task complete python-package-3-task-001

# 4. Complete sprint → merge to track
git checkout track/python-package
git merge --no-ff sprint/python-package-3
vibey sprint complete python-package-3

# 5. Complete track → merge to develop
git checkout develop
git merge --no-ff track/python-package
vibey track complete python-package

# 6. Release → merge develop to main
git checkout main
git merge --no-ff develop
git tag v1.0.0
```

### Configuration: Hierarchical Branching

```yaml
# .vibey/config/git.yaml
git:
  branching:
    model: hierarchical  # trunk|feature|sprint|track|hierarchical

    hierarchy:
      enabled: true

      # Base branches
      production: main
      integration: develop

      # Branch structure
      levels:
        - name: track
          pattern: "track/{track_id}"
          parent: develop
          required: true  # Must create track branches

        - name: sprint
          pattern: "sprint/{sprint_id}"
          parent: "track/{track_id}"
          required: false  # Optional sprint branches

        - name: task
          pattern: "task/{task_id}"
          parent: "sprint/{sprint_id}"  # Or track, or develop
          required: false

      # Merge requirements
      merge:
        require_pr: true
        require_reviews: 2
        delete_after_merge: true
```

### Enforcement

```bash
# Vibey validates merge target
git checkout develop
git merge track/python-package  # ✓ Valid (track → develop)

git checkout main
git merge sprint/python-package-3  # ✗ Invalid (sprint can't merge to main)

# Error:
[vibey] Invalid merge target:
  Sprint branches must merge to their parent track branch
  Expected: track/python-package
  Actual: main
```

### CLI Helpers

```bash
# Create full hierarchy for new work
vibey git branch create-hierarchy task-001

# Output:
✓ Created track/python-package (from develop)
✓ Created sprint/python-package-3 (from track/python-package)
✓ Created task/python-package-3-task-001 (from sprint/python-package-3)
→ Checked out task/python-package-3-task-001

# Show merge path
vibey git merge-path task/python-package-3-task-001

# Output:
Merge path for task-001:
  task/python-package-3-task-001
    → sprint/python-package-3
      → track/python-package
        → develop
          → main
```

---

## 6. Project-Wide Git Strategy Requirements

### Question
Can Vibey enforce a project's chosen Git strategy with fine-grained requirements?

### Answer: Configurable Strategy Enforcement

**Requirements Configuration:**

```yaml
# .vibey/config/git.yaml
git:
  strategy:
    name: "Company GitFlow"  # Named strategy

    requirements:
      # Branch requirements
      branches:
        track_branch:
          required: true  # Every track MUST have a branch
          pattern: "track/{track_id}"
          protected: true  # Enable branch protection

        sprint_branch:
          required: false  # Sprints may use branches
          pattern: "sprint/{sprint_id}"

        task_branch:
          required: true  # Every task MUST have a branch
          pattern: "task/{task_id}"

      # Tag requirements
      tags:
        sprint_boundaries:
          required: true  # Every sprint MUST have start/end tags
          format: "{sprint_id}/{start|end}"

        task_markers:
          required: false
          format: "{task_id}/{marker}"

      # Commit requirements
      commits:
        task_reference:
          required: true  # Every commit MUST reference a task
          format: conventional  # Must use conventional commits

      # Merge requirements
      merges:
        require_pr: true
        block_direct_push: ["main", "develop"]
        enforce_hierarchy: true  # Can only merge to parent
```

### Strategy Presets

```yaml
# Predefined strategies users can adopt

strategies:
  trunk-based:
    branches:
      track_branch: {required: false}
      sprint_branch: {required: false}
      task_branch: {required: false}
    tags:
      sprint_boundaries: {required: false}
    commits:
      task_reference: {required: false}

  feature-branch:
    branches:
      track_branch: {required: false}
      sprint_branch: {required: false}
      task_branch: {required: true}
    tags:
      sprint_boundaries: {required: true}
    commits:
      task_reference: {required: true}

  gitflow:
    branches:
      track_branch: {required: true}
      sprint_branch: {required: false}
      task_branch: {required: true}
    tags:
      sprint_boundaries: {required: true}
    commits:
      task_reference: {required: true}
    merges:
      require_pr: true
      enforce_hierarchy: true

  hierarchical:
    branches:
      track_branch: {required: true}
      sprint_branch: {required: true}
      task_branch: {required: true}
    tags:
      sprint_boundaries: {required: true}
      task_markers: {required: true}
    commits:
      task_reference: {required: true}
    merges:
      require_pr: true
      enforce_hierarchy: true
```

### Usage

```bash
# Adopt a preset strategy
vibey git strategy adopt gitflow

# Customize a strategy
vibey git strategy adopt feature-branch --customize

# Validate against strategy
vibey git validate --strict

# Output:
Strategy: Company GitFlow
✗ track/python-package: Missing required branch (VIOLATION)
✓ sprint/python-package-3: Has start/end tags
✗ Commit abc123: No task reference (VIOLATION)
✓ All merges follow hierarchy

2 violations found. Run with --fix to auto-correct.
```

---

## 7. Dynamic Source of Truth Model

### Question
If all Git mappings are required, does Git become the source of truth?

### Answer: Three-Tier Model Based on Context

**Scenario-Based Source of Truth:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Source of Truth Decision Tree                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Is this a Git repository?                                       │
│    │                                                             │
│    ├─ NO ──────────────────────────────► YAML-ONLY MODE         │
│    │                                      (Vibey standalone)      │
│    │                                                             │
│    └─ YES ─► Is Git strategy enforced?                          │
│                │                                                 │
│                ├─ NO ───────────────────► HYBRID MODE           │
│                │                          (YAML primary,          │
│                │                           Git supporting)        │
│                │                                                 │
│                └─ YES ─► User opted in? ─┐                      │
│                            │              │                      │
│                            ├─ YES ────────┼──► GIT MODE         │
│                            │              │    (Git is source    │
│                            │              │     of truth)        │
│                            └─ NO ─────────┼──► HYBRID MODE      │
│                                          │    (default safe)     │
│                                          │                       │
└──────────────────────────────────────────┼──────────────────────┘
                                          │
                                          ▼
                              Configuration determines mode
```

**Configuration:**

```yaml
git:
  source_of_truth:
    mode: auto  # auto|yaml|git|hybrid

    # When mode=auto, apply these rules:
    auto_rules:

      # Scenario 1: Not a Git repo
      yaml_only_when:
        - is_git_repo == false
        - git.enabled == false

      # Scenario 2: Git repo + enforced strategy + user opt-in
      git_primary_when:
        - is_git_repo == true
        - git.strategy.enforce == true
        - git.source_of_truth.allow_git_primary == true

      # Scenario 3: Git repo + anything else (DEFAULT)
      hybrid_when:
        - is_git_repo == true
        - (git.strategy.enforce == false OR
           git.source_of_truth.allow_git_primary == false)
```

### Behavior Based on Scenario

| Scenario | Mode | Authoritative | When YAML/Git Disagree | Reconstruction |
|----------|------|---------------|------------------------|----------------|
| **Non-Git project** | yaml-only | YAML files | N/A (no Git) | Not applicable |
| **Git repo (default)** | hybrid | YAML primary | Warn, trust YAML | Git-assisted |
| **Git enforced + opt-in** | git | Git state | Derive/update YAML | Full from Git |

### Scenario 1: Non-Git Project (YAML-Only)

**When:**
- Directory is not a Git repository
- OR `git.enabled: false`

**Behavior:**
```yaml
# .vibey/config/git.yaml
git:
  enabled: false  # Or not in a Git repo

# Result: source_of_truth.mode = yaml-only (auto-detected)
```

**Characteristics:**
- YAML files are the sole source of truth
- No Git integration features available
- Manual roadmap management via CLI/MCP
- Suitable for non-version-controlled projects

**Use Cases:**
- Personal project planning
- Non-code projects (research, writing)
- Evaluation/prototyping Vibey
- Teams without Git

---

### Scenario 2: Git Repository (Hybrid - DEFAULT)

**When:**
- Directory is a Git repository
- Git strategy NOT enforced (`git.strategy.enforce: false`)
- OR User has not opted into Git-primary mode

**Behavior:**
```yaml
# .vibey/config/git.yaml (default for Git repos)
git:
  enabled: true
  strategy:
    enforce: false  # Default: not enforced

  source_of_truth:
    mode: auto  # Auto-detects: hybrid
    allow_git_primary: false  # Default: don't use Git as primary

# Result: source_of_truth.mode = hybrid (auto-detected)
```

**Characteristics:**
- YAML is primary/authoritative source of truth
- Git provides supporting evidence and tracking
- Reconciliation warns about inconsistencies
- Both systems checked, YAML wins conflicts
- Advisory enforcement only (by default)

**Use Cases:**
- Teams adopting Vibey gradually
- Mixed Git discipline (some follow conventions, some don't)
- Flexible workflows
- Default for most projects

**Reconciliation Example:**
```bash
vibey git validate

# Output:
✓ YAML state is consistent
⚠ Advisory warnings:
  - Task task-001: YAML=not_started, Git=3 commits found
    Suggestion: Consider updating YAML status to in_progress

  - Task task-002: YAML=completed, Git=no branch/commits
    This is OK: task may be non-code work

YAML state is trusted. Run 'vibey git sync' to align Git with YAML.
```

---

### Scenario 3: Git Enforced + Opt-In (Git Primary)

**When:**
- Directory is a Git repository
- Git strategy IS enforced (`git.strategy.enforce: true`)
- AND User opted in (`allow_git_primary: true`)

**Behavior:**
```yaml
# .vibey/config/git.yaml (strict Git enforcement)
git:
  enabled: true

  strategy:
    enforce: true  # Enforce Git strategy
    name: gitflow
    requirements:
      branches:
        track_branch: {required: true}
        task_branch: {required: true}
      tags:
        sprint_boundaries: {required: true}
      commits:
        task_reference: {required: true}

  enforcement:
    mode: blocking  # Prevent violations

  source_of_truth:
    mode: auto  # Auto-detects: git
    allow_git_primary: true  # Explicit opt-in

# Result: source_of_truth.mode = git (auto-detected)
```

**Characteristics:**
- Git state is authoritative source of truth
- YAML is derived/cached from Git
- Task status inferred from branches/tags/commits
- Sprint status derived from tags
- YAML auto-generated by `vibey git sync`

**Derivation Rules:**
```yaml
# How Git state maps to Vibey state
derivation:
  # Task status
  task_status:
    not_started: no branch AND no commits
    in_progress: branch exists OR commits exist BUT not merged
    completed: branch merged AND end tag present

  # Sprint status
  sprint_status:
    not_started: no start tag
    in_progress: start tag exists, no end tag
    completed: end tag exists

  # Progress metrics
  progress:
    tasks_completed: count(task end tags)
    sprints_completed: count(sprint end tags)
    completion_percent: (completed / total) * 100
```

**YAML as Cache:**
```yaml
# sprint.yaml in Git-primary mode
# Auto-generated by: vibey git sync
# WARNING: Manual edits will be overwritten

sprint:
  id: python-package-3
  status: in_progress  # Derived: start tag exists, no end tag

  # Synced from Git: 2025-11-24 12:00:00
  _git_sync:
    last_sync: '2025-11-24T12:00:00Z'
    source: git
    mode: auto-generated

  tasks:
    - id: task-001
      status: completed  # Derived: branch merged + end tag
      commits:  # Derived: git log --grep=task-001
        - sha: abc123
          timestamp: '2025-11-24T10:00:00Z'
          author: alice@example.com
        - sha: def456
          timestamp: '2025-11-24T11:00:00Z'
          author: alice@example.com
```

**Use Cases:**
- Teams with strict Git discipline
- Compliance/audit requirements
- Single source of truth desired
- High automation needs
- Advanced Git workflows (GitFlow, hierarchical)

---

### Fallback Mechanism

**Automatic Fallback from Git-Primary to Hybrid:**

When Git-primary mode encounters problems, automatically fallback to hybrid:

```yaml
git:
  source_of_truth:
    mode: auto
    allow_git_primary: true

    fallback:
      enabled: true
      target_mode: hybrid  # Fallback to hybrid (safe default)

      # Conditions that trigger fallback
      triggers:
        - missing_required_tags    # Required tags not found
        - missing_required_branches # Required branches missing
        - dangling_references      # Tags point to missing commits
        - merge_conflicts          # Cannot reconcile Git state
        - reconstruction_failure   # Cannot derive YAML from Git
        - inconsistent_state       # Git state is contradictory
```

**Fallback Example:**
```bash
# Git-primary mode enabled
vibey git sync

# Output:
✗ Error: Cannot derive sprint status
  Sprint python-package-3 has no start tag (required in git-primary mode)

⚠ Falling back to hybrid mode
  Reason: missing_required_tags
  Action: YAML state will be trusted until Git state is fixed

→ Mode switched: git → hybrid
→ Run 'vibey git repair' to fix Git state and retry git-primary mode
```

---

### Migration Between Modes

**Progression Path: YAML-Only → Hybrid → Git-Primary**

```bash
# ============================================================
# Scenario 1: Start without Git (YAML-only)
# ============================================================

vibey init
# Creates .vibey/roadmap/ with YAML files
# Mode: yaml-only (auto-detected: not a Git repo)

# Work with roadmap
vibey task start task-001
vibey task complete task-001

# ============================================================
# Scenario 1 → Scenario 2: Initialize Git repo (Hybrid)
# ============================================================

git init
git add .vibey/
git commit -m "Initial roadmap"

# Mode automatically changes: yaml-only → hybrid
vibey status
# Output: Mode: hybrid (Git repo detected)

# Enable Git integration features
vibey git hooks install

# Commits now can reference tasks
git commit -m "feat(task-002): implement feature"

# Validate consistency
vibey git validate
# Output: ✓ YAML consistent, ⚠ Task task-002: YAML=not_started, Git=1 commit

# ============================================================
# Scenario 2 → Scenario 3: Enforce Git strategy (Git-primary)
# ============================================================

# Step 1: Choose a strategy preset
vibey git strategy adopt gitflow

# This sets:
# - git.strategy.enforce = true
# - git.strategy.requirements = {...}
# - git.enforcement.mode = blocking

# Step 2: Ensure Git state meets requirements
vibey git validate --strict
# Output:
# ✗ 3 violations found:
#   - Task task-001: Missing required branch
#   - Sprint python-package-3: Missing start tag
#   - Commit abc123: No task reference

# Fix violations
vibey git repair --auto
# Creates missing tags/branches based on YAML state

# Step 3: Opt into Git-primary mode
vibey config set git.source_of_truth.allow_git_primary true

# Mode automatically changes: hybrid → git
vibey status
# Output:
# ✓ Mode: git-primary (all requirements met, user opted in)
# ✓ Git is now the source of truth
# ⚠ YAML files will be auto-generated from Git state

# Sync YAML from Git
vibey git sync

# Output:
# Syncing YAML from Git state...
# ✓ Updated track.yaml (derived from branches/tags)
# ✓ Updated sprint.yaml (derived from tags/commits)
# ✓ Updated task statuses (derived from branches/commits)

# ============================================================
# Scenario 3 → Scenario 2: Disable Git-primary (back to Hybrid)
# ============================================================

# If Git-primary is too strict, revert to hybrid
vibey config set git.source_of_truth.allow_git_primary false

# Mode reverts: git → hybrid
vibey status
# Output: Mode: hybrid (user disabled git-primary)

# Or disable strategy enforcement entirely
vibey config set git.strategy.enforce false

# Mode reverts: git → hybrid (strategy not enforced)
```

---

### Mode Comparison Summary

| Aspect | YAML-Only | Hybrid (Default) | Git-Primary |
|--------|-----------|------------------|-------------|
| **Git repo required** | No | Yes | Yes |
| **Git integration** | None | Optional features | Full integration |
| **Source of truth** | YAML only | YAML (Git supports) | Git (YAML derived) |
| **Strategy enforcement** | N/A | Optional | Required |
| **User opt-in required** | No | No | Yes (`allow_git_primary`) |
| **YAML editing** | Manual/CLI | Manual/CLI | Auto-generated |
| **When to use** | No Git, prototyping | Default for Git repos | Strict Git discipline |
| **Adoption effort** | None | Low | High |

---

### Detection Algorithm

```python
def detect_source_of_truth_mode() -> Mode:
    """
    Auto-detect appropriate source of truth mode.
    Implements the three-scenario model.
    """

    # Scenario 1: Not a Git repo
    if not is_git_repo() or not config.git.enabled:
        return Mode.YAML_ONLY

    # We're in a Git repo, check if strategy is enforced
    strategy_enforced = config.git.strategy.enforce

    # Scenario 3: Git repo + enforced strategy + opt-in
    if strategy_enforced and config.git.source_of_truth.allow_git_primary:
        # Validate that Git state meets requirements
        violations = validate_git_strategy()

        if not violations:
            # All requirements met, use Git as source
            return Mode.GIT_PRIMARY
        else:
            # Requirements not met, fallback
            if config.git.source_of_truth.fallback.enabled:
                warn(f"Git-primary requirements not met. Falling back to hybrid.")
                warn(f"Violations: {violations}")
                return Mode.HYBRID
            else:
                raise GitStrategyViolationError(violations)

    # Scenario 2: Git repo, but strategy not enforced or not opted in
    # This is the default for Git repositories
    return Mode.HYBRID
```

---

## Summary of Additions

| Topic | v1 Support | v2 Enhancement | Configuration |
|-------|-----------|----------------|---------------|
| **Submodules** | No | Yes (aggregation) | `submodules.enabled` |
| **Task Tags** | Sprint only | Task markers | `tags.task_tags.enabled` |
| **Tag Repair** | Manual | Automated | `tags.repair.auto` |
| **Branch Hierarchy** | Optional | Enforced | `hierarchy.enabled` |
| **Strategy Requirements** | Presets | Custom rules | `strategy.requirements` |
| **Dynamic Source of Truth** | Fixed hybrid | Auto-switching | `source_of_truth.mode: auto` |

---

## Configuration Impact

These additions require new configuration sections:

```yaml
# .vibey/config/git.yaml (extended)
git:
  enabled: true

  # Submodule support (v2)
  submodules:
    enabled: false
    aggregate: false

  # Enhanced tagging
  tags:
    sprint_boundaries: true
    task_tags:
      enabled: false
      auto_create: false
    repair:
      auto: true
      strategy: message_match

  # Hierarchical branching
  hierarchy:
    enabled: false
    levels: [...]

  # Strategy enforcement
  strategy:
    name: null  # Or: trunk-based|feature-branch|gitflow|hierarchical
    requirements: {...}

  # Dynamic source of truth
  source_of_truth:
    mode: auto  # auto|yaml|git|hybrid
    fallback: hybrid
```

---

## Implementation Priority

**Sprint 1-2 (v1):**
- Commit message parsing (already planned)
- Sprint tags (already planned)
- Hybrid source of truth (already planned)

**Sprint 3-4 (v1.5):**
- Task tags (optional)
- Tag repair automation
- Strategy presets
- Branch hierarchy validation

**Future (v2):**
- Submodule aggregation
- Dynamic source of truth
- Full Git-as-source mode
