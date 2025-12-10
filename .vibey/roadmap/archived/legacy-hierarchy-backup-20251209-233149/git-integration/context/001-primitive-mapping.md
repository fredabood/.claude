# Vibey-Git Primitive Mapping Specification

**Task:** git-integration-0-task-001
**Status:** Draft
**Author:** Architecture Agent
**Date:** 2025-11-24

## Executive Summary

This document establishes how Vibey roadmap primitives map to Git primitives. These mappings form the foundation for all git integration features.

## Primitive Hierarchy

### Vibey Hierarchy
```
Roadmap
  └── Track (1..n)
        └── Sprint (1..n)
              └── Task (1..n)
```

### Git Hierarchy
```
Repository
  └── Branch (1..n)
        └── Commit (1..n)
              └── Tag (0..n)
```

## Mapping Specification

### 1. Roadmap → Repository

| Aspect | Mapping | Rationale |
|--------|---------|-----------|
| **Cardinality** | 1:1 | One roadmap per repository |
| **Location** | `.vibey/roadmap/` | Standard location for roadmap YAML |
| **Identifier** | `roadmap.yaml` → repo name | Roadmap ID matches repo |

**Decision:** A Vibey roadmap is scoped to a single Git repository. Multi-repo roadmaps are not supported in v1.

### 2. Track → Branch Namespace (Optional)

| Aspect | Mapping | Rationale |
|--------|---------|-----------|
| **Cardinality** | 1:0..1 | Track MAY have a dedicated branch |
| **Branch Name** | `track/<track-id>` | Clear namespace separation |
| **Alternative** | No branch | Tracks can exist without branches |

**Options:**

```
Option A: Track branches (long-lived)
─────────────────────────────────────
main
├── track/python-package
├── track/git-integration
└── track/user-journey-audit

Option B: No track branches (trunk-based)
─────────────────────────────────────────
main (all tracks merged here)
└── feature branches for individual work
```

**Decision:** Track branches are OPTIONAL. Vibey supports both models:
- Teams using GitFlow can create track branches
- Teams using trunk-based development work directly on main
- Configuration: `git.branching.track_branches: true|false`

### 3. Sprint → Tag or Commit Range

| Aspect | Mapping | Rationale |
|--------|---------|-----------|
| **Cardinality** | 1:0..n | Sprint MAY have tags/commits |
| **Start Tag** | `sprint/<sprint-id>/start` | Marks sprint beginning |
| **End Tag** | `sprint/<sprint-id>/end` | Marks sprint completion |
| **Commit Range** | `start..end` | All work in sprint |

**Example:**
```bash
# Sprint tags
git tag sprint/python-package-3/start abc123
git tag sprint/python-package-3/end def456

# Query sprint commits
git log sprint/python-package-3/start..sprint/python-package-3/end
```

**Decision:** Sprint tagging is OPTIONAL but recommended for:
- Sprint velocity calculation
- Historical analysis
- Release management

### 4. Task → Commit(s)

| Aspect | Mapping | Rationale |
|--------|---------|-----------|
| **Cardinality** | 1:0..n | Task has zero or more commits |
| **Reference** | Commit message contains task ID | Linkage via convention |
| **Storage** | Task YAML `commits: []` list | Record of associated commits |

**Commit Message Formats (see 003-commit-conventions.md):**
```bash
# Format 1: Conventional commits
feat(python-package-3-task-001): implement content loader

# Format 2: Footer reference
feat: implement content loader

Task: python-package-3-task-001

# Format 3: Bracket notation
[python-package-3-task-001] implement content loader
```

**Decision:** Tasks are linked to commits via commit message references. Multiple commits can reference the same task. One commit can reference multiple tasks.

### 5. Quality Gate → CI Check

| Aspect | Mapping | Rationale |
|--------|---------|-----------|
| **Cardinality** | 1:0..1 | Gate MAY map to CI check |
| **Check Name** | `vibey/gate/<gate-name>` | GitHub/GitLab check namespace |
| **Status** | pass/fail → gate score | CI result updates gate |

**Example:**
```yaml
# Quality gate in sprint.yaml
quality_gates:
  - name: Test Coverage
    threshold: 90
    ci_check: coverage  # Maps to CI job

# GitHub Actions integration
- name: Update quality gate
  run: vibey gate update "Test Coverage" --score ${{ steps.coverage.outputs.percent }}
```

**Decision:** Quality gates optionally integrate with CI. Gates can be:
- Manual: Updated by humans
- Automatic: Updated by CI jobs
- Hybrid: CI suggests, human approves

### 6. Blocker → Branch Protection (Optional)

| Aspect | Mapping | Rationale |
|--------|---------|-----------|
| **Cardinality** | 1:0..1 | Blocker MAY enforce via Git |
| **Mechanism** | Pre-merge check | Block merge if blocker active |
| **Override** | `--force` flag | Emergency bypass |

**Decision:** Blockers can optionally enforce via Git hooks/CI:
- Advisory mode: Warn about blocked items
- Blocking mode: Prevent commits/merges to blocked items
- Configuration: `git.enforcement.blockers: off|advisory|blocking`

### 7. Dependency → Merge Order Suggestion

| Aspect | Mapping | Rationale |
|--------|---------|-----------|
| **Cardinality** | n:n | Dependencies are graph relationships |
| **Enforcement** | Soft suggestion | Recommend merge order |
| **Visualization** | PR description | Show dependency status |

**Decision:** Dependencies inform merge order but don't strictly enforce it:
- `vibey git merge-order` suggests optimal sequence
- PR descriptions show dependency status
- Blocking enforcement available via configuration

## Mapping Summary Table

| Vibey Primitive | Git Primitive | Cardinality | Required? |
|-----------------|---------------|-------------|-----------|
| Roadmap | Repository | 1:1 | Yes |
| Track | Branch namespace | 1:0..1 | No |
| Sprint | Tag range | 1:0..2 | No |
| Task | Commit(s) | 1:0..n | No |
| Quality Gate | CI Check | 1:0..1 | No |
| Blocker | Branch protection | 1:0..1 | No |
| Dependency | Merge order | n:n | No |

## Configuration Schema

```yaml
# .vibey/config/git.yaml
git:
  enabled: true

  branching:
    track_branches: false  # Create track/<id> branches
    sprint_tags: true      # Create sprint start/end tags
    task_branches: false   # Create task/<id> branches

  commit:
    require_task_reference: false  # Require task ID in commits
    format: conventional           # conventional|bracket|footer

  enforcement:
    mode: advisory    # off|advisory|blocking|audit
    blockers: advisory
    dependencies: advisory
    quality_gates: advisory
```

## Examples

### Example 1: Minimal Integration (Trunk-Based)

```
Repository: vibey
├── main (all work)
├── .vibey/roadmap/
│   ├── roadmap.yaml
│   └── python-package/
│       └── track.yaml
└── Commits reference tasks in messages
```

### Example 2: Full Integration (GitFlow-style)

```
Repository: vibey
├── main (releases)
├── develop (integration)
├── track/python-package
│   ├── sprint/python-package-3/start (tag)
│   └── sprint/python-package-3/end (tag)
├── task/python-package-3-task-001 (feature branch)
└── .vibey/roadmap/
```

## Edge Cases

### Multi-Task Commits
A single commit can reference multiple tasks:
```bash
git commit -m "refactor: restructure CLI

Tasks: task-001, task-002
Closes: task-003"
```
All three tasks record this commit SHA.

### Task Without Commits
Tasks can be completed without commits (e.g., documentation review, planning):
- Status updated manually via CLI/MCP
- `commits: []` remains empty
- Valid workflow for non-code tasks

### Orphan Commits
Commits without task references:
- Allowed in all modes except `blocking`
- Warning in `advisory` mode
- Logged in `audit` mode

### Branch Without Track
Feature branches not tied to tracks:
- Fully supported
- No roadmap integration
- Standard Git workflow

## Migration Notes

### Existing Repositories
Adding Vibey to existing repo:
1. `vibey init` creates `.vibey/` structure
2. Existing commits remain unlinked
3. New commits can reference tasks
4. `vibey git backfill` can link historical commits (optional)

### Removing Integration
Disabling git integration:
1. Set `git.enabled: false`
2. Remove hooks: `vibey git hooks uninstall`
3. Roadmap YAML remains intact
4. Tags/branches can be kept or removed

## Appendix: Decision Log

| Decision | Options Considered | Choice | Rationale |
|----------|-------------------|--------|-----------|
| Roadmap scope | 1:1, 1:n repos | 1:1 | Simplicity, clear ownership |
| Track branches | Required, Optional | Optional | Support multiple workflows |
| Task linking | Commit msg, Git notes | Commit msg | Simpler, portable |
| Sprint markers | Tags, Branches | Tags | Lightweight, standard |
| Enforcement default | Blocking, Advisory | Advisory | Gradual adoption |
