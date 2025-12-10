# Source of Truth Decision Matrix

**Purpose:** Help users choose the appropriate source of truth model for their project

---

## Quick Decision Guide

Answer these questions to determine your ideal mode:

### Question 1: Is this a Git repository?

- **NO** → Use **YAML-Only Mode** (Scenario 1)
- **YES** → Continue to Question 2

### Question 2: Does your team have strong Git discipline?

Strong Git discipline means:
- All commits reference tasks in commit messages
- Branches follow naming conventions
- Sprint boundaries are tagged
- PR/merge processes are followed consistently

- **NO** → Use **Hybrid Mode** (Scenario 2 - Recommended)
- **YES** → Continue to Question 3

### Question 3: Do you want Git to be the authoritative source?

Consider:
- YAML files will be auto-generated from Git state
- Manual YAML edits will be overwritten
- Requires strict enforcement of Git conventions
- Higher automation, less manual intervention

- **NO** → Use **Hybrid Mode** (Scenario 2 - Recommended)
- **YES** → Use **Git-Primary Mode** (Scenario 3)

---

## Detailed Scenario Comparison

### Scenario 1: YAML-Only Mode

| Aspect | Details |
|--------|---------|
| **Best for** | Non-code projects, prototyping, personal planning, no VCS |
| **Git required** | No |
| **Git integration** | None available |
| **State management** | Manual via CLI/MCP |
| **Complexity** | Lowest |
| **Automation** | Manual updates only |
| **Pros** | Simple, no Git knowledge needed, works anywhere |
| **Cons** | No version history, no team collaboration via Git |

**Choose if:**
- ✓ Not using Git
- ✓ Evaluating Vibey
- ✓ Personal/non-code projects
- ✓ Want simplest possible setup

**Don't choose if:**
- ✗ You have a Git repository
- ✗ You want Git integration features

---

### Scenario 2: Hybrid Mode (DEFAULT)

| Aspect | Details |
|--------|---------|
| **Best for** | Most projects, teams learning Vibey, flexible workflows |
| **Git required** | Yes |
| **Git integration** | Optional features available |
| **State management** | Manual YAML editing + Git tracking |
| **Complexity** | Medium |
| **Automation** | Optional (hooks, commit parsing) |
| **Pros** | Flexible, forgiving, gradual adoption, YAML is readable truth |
| **Cons** | Requires manual status updates, potential YAML/Git divergence |

**Choose if:**
- ✓ Using Git but don't want strict enforcement
- ✓ Team has mixed Git discipline
- ✓ Want to adopt Vibey gradually
- ✓ Prefer explicit YAML state over inferred state
- ✓ Want to manually edit roadmap files
- ✓ Default choice for most projects

**Don't choose if:**
- ✗ You want full automation from Git
- ✗ You need compliance/audit from single source
- ✗ You want to eliminate manual updates

---

### Scenario 3: Git-Primary Mode

| Aspect | Details |
|--------|---------|
| **Best for** | Strict Git workflows, compliance needs, high automation |
| **Git required** | Yes |
| **Git integration** | Full, required |
| **State management** | Derived from Git (branches, tags, commits) |
| **Complexity** | Highest |
| **Automation** | Full automation from Git state |
| **Pros** | Single source of truth, no manual updates, audit trail, full traceability |
| **Cons** | Strict requirements, YAML not directly editable, higher setup cost |

**Choose if:**
- ✓ Team has excellent Git discipline
- ✓ Want single source of truth (Git)
- ✓ Need full traceability for compliance
- ✓ Want to eliminate manual status updates
- ✓ Willing to follow strict Git conventions
- ✓ All team members comfortable with Git

**Don't choose if:**
- ✗ Team has inconsistent Git practices
- ✗ Want to manually edit YAML files
- ✗ Need flexibility in workflow
- ✗ Not ready for strict enforcement

---

## Feature Availability Matrix

| Feature | YAML-Only | Hybrid | Git-Primary |
|---------|-----------|--------|-------------|
| **Basic roadmap management** | ✓ | ✓ | ✓ |
| **Manual status updates** | ✓ | ✓ | ✗ (auto) |
| **Git version history** | ✗ | ✓ | ✓ |
| **Commit-task linking** | ✗ | ✓ (optional) | ✓ (required) |
| **Git hooks** | ✗ | ✓ (optional) | ✓ (required) |
| **Branch-task association** | ✗ | ✓ (optional) | ✓ (required) |
| **Sprint tagging** | ✗ | ✓ (optional) | ✓ (required) |
| **Task tags** | ✗ | ✓ (optional) | ✓ (required) |
| **Auto status from Git** | ✗ | ✗ | ✓ |
| **State reconstruction** | ✗ | ✓ (Git-assisted) | ✓ (full) |
| **Audit trail** | ✗ | ✓ (Git commits) | ✓ (Git commits) |
| **Conflict detection** | ✗ | ✓ (warns) | ✓ (blocks) |
| **YAML editable** | ✓ | ✓ | ✗ (derived) |
| **Enforcement modes** | N/A | Advisory default | Blocking required |

---

## Configuration Requirements

### YAML-Only Mode

```yaml
# Minimal config - no Git section needed
# Or explicitly disable Git:
git:
  enabled: false
```

### Hybrid Mode (Default)

```yaml
git:
  enabled: true

  source_of_truth:
    mode: auto  # Will detect: hybrid
    allow_git_primary: false  # Default

  strategy:
    enforce: false  # Optional enforcement

  enforcement:
    mode: advisory  # Warn, don't block
```

### Git-Primary Mode

```yaml
git:
  enabled: true

  source_of_truth:
    mode: auto  # Will detect: git
    allow_git_primary: true  # EXPLICIT OPT-IN REQUIRED

  strategy:
    enforce: true  # Required
    name: gitflow  # Or custom requirements
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
```

---

## Migration Paths

### Path 1: YAML-Only → Hybrid

**Trigger:** Initialize Git repository

**Steps:**
```bash
# In existing YAML-only project
git init
git add .vibey/
git commit -m "chore: initialize Git and Vibey roadmap"

# Mode automatically changes to hybrid
vibey status
# Output: Mode: hybrid (auto-detected)

# Enable optional features
vibey git hooks install
```

**Effort:** Low (automatic)

---

### Path 2: Hybrid → Git-Primary

**Trigger:** Team wants full Git integration

**Steps:**
```bash
# 1. Adopt Git strategy
vibey git strategy adopt gitflow

# 2. Validate current state
vibey git validate --strict

# 3. Fix violations
vibey git repair --auto

# 4. Opt into Git-primary
vibey config set git.source_of_truth.allow_git_primary true

# 5. Sync YAML from Git
vibey git sync
```

**Effort:** Medium-High (requires fixing violations)

---

### Path 3: Git-Primary → Hybrid

**Trigger:** Too strict, need flexibility

**Steps:**
```bash
# Option A: Disable Git-primary opt-in
vibey config set git.source_of_truth.allow_git_primary false

# Option B: Disable strategy enforcement
vibey config set git.strategy.enforce false

# Mode reverts to hybrid
vibey status
# Output: Mode: hybrid
```

**Effort:** Low (configuration change)

---

## Common Scenarios

### Scenario: Solo Developer

**Recommended:** Hybrid Mode

**Rationale:**
- Git for version control
- Flexible workflow
- Manual status updates fine for one person
- Can use Git features when needed

**Configuration:**
```yaml
git:
  enabled: true
  enforcement:
    mode: advisory
  commit:
    require_task_reference: false
```

---

### Scenario: Small Team (2-5)

**Recommended:** Hybrid Mode

**Rationale:**
- Easy coordination
- Mix of Git habits okay
- Advisory warnings help build habits
- Low friction for team adoption

**Configuration:**
```yaml
git:
  enabled: true
  enforcement:
    mode: advisory
  commit:
    require_task_reference: false  # Recommended but not required
  branching:
    model: feature  # Feature branches per task
```

---

### Scenario: Medium Team (6-15)

**Recommended:** Hybrid Mode (default) or Git-Primary (if disciplined)

**Rationale:**
- Need coordination
- Can benefit from stricter conventions
- Evaluate team Git discipline first
- Consider Git-primary if team is ready

**Configuration (Hybrid):**
```yaml
git:
  enabled: true
  enforcement:
    mode: advisory
  strategy:
    name: feature-branch
    enforce: false  # Start with advisory
```

**Configuration (Git-Primary - if ready):**
```yaml
git:
  enabled: true
  enforcement:
    mode: blocking
  strategy:
    name: gitflow
    enforce: true
  source_of_truth:
    allow_git_primary: true
```

---

### Scenario: Large Team (15+) or Enterprise

**Recommended:** Git-Primary Mode

**Rationale:**
- Need strict coordination
- Compliance requirements likely
- Audit trail important
- Can enforce team-wide conventions
- Worth investment in strict setup

**Configuration:**
```yaml
git:
  enabled: true

  enforcement:
    mode: blocking

  strategy:
    name: hierarchical  # Full track/sprint/task branches
    enforce: true
    requirements:
      branches:
        track_branch: {required: true, protected: true}
        sprint_branch: {required: true}
        task_branch: {required: true}
      tags:
        sprint_boundaries: {required: true}
        task_markers: {required: true}
      commits:
        task_reference: {required: true}
      merges:
        require_pr: true
        require_reviews: 2

  source_of_truth:
    mode: auto
    allow_git_primary: true
    fallback:
      enabled: true
```

---

### Scenario: Open Source Project

**Recommended:** Hybrid Mode

**Rationale:**
- Contributors have varying Git habits
- Can't enforce strict requirements on volunteers
- Project maintainers handle roadmap
- Git features help but shouldn't block contributions

**Configuration:**
```yaml
git:
  enabled: true
  enforcement:
    mode: advisory  # Don't block contributors
  commit:
    require_task_reference: false
  branching:
    model: flexible  # Accept any branch naming
```

---

### Scenario: Compliance/Regulated Environment

**Recommended:** Git-Primary Mode

**Rationale:**
- Need full audit trail
- Single source of truth for compliance
- All changes must be traceable
- Can enforce team standards

**Configuration:**
```yaml
git:
  enabled: true

  enforcement:
    mode: blocking

  strategy:
    enforce: true
    # ... strict requirements ...

  source_of_truth:
    allow_git_primary: true

  reconstruction:
    audit:
      enabled: true
      path: .vibey/audit/changes.jsonl
      retention_days: 2555  # 7 years for compliance
```

---

## Troubleshooting

### Problem: "I want Git integration but don't want strict enforcement"

**Solution:** Use Hybrid Mode (default)

This is exactly what Hybrid mode provides - Git features are available but not required.

---

### Problem: "Git-primary mode keeps failing validation"

**Solution:** Either fix violations or fallback to Hybrid

```bash
# Option 1: Fix violations
vibey git repair --auto

# Option 2: Fallback to hybrid
vibey config set git.source_of_truth.allow_git_primary false
```

---

### Problem: "I accidentally enabled Git-primary and YAML is overwritten"

**Solution:** Revert to Hybrid, restore from Git history

```bash
# Disable Git-primary
vibey config set git.source_of_truth.allow_git_primary false

# Restore YAML from previous commit (if needed)
git checkout HEAD~1 -- .vibey/roadmap/

# Or use Vibey rollback
vibey git rollback HEAD~1
```

---

### Problem: "Team wants to try Git-primary but not sure"

**Solution:** Test in branch first

```bash
# Create test branch
git checkout -b test-git-primary

# Enable Git-primary
vibey git strategy adopt gitflow
vibey config set git.source_of_truth.allow_git_primary true

# Test workflow for a sprint
# ...

# If it works: merge to main
# If not: discard branch and stay hybrid
```

---

## Summary Recommendation

**For 90% of projects:** Start with **Hybrid Mode** (Scenario 2)

- Lowest friction
- Auto-detected for Git repos
- Provides Git integration without strict requirements
- Can upgrade to Git-primary later if team is ready

**Only use YAML-only** if you're not using Git at all.

**Only use Git-primary** if your team has excellent Git discipline and wants full automation.

---

## Quick Reference

| Your Situation | Recommended Mode | Config Setting |
|----------------|------------------|----------------|
| No Git repo | YAML-Only | `git.enabled: false` |
| Git repo, any team | Hybrid | (default, no config needed) |
| Strict Git team + want automation | Git-Primary | `allow_git_primary: true` + `strategy.enforce: true` |
| Solo developer | Hybrid | (default) |
| Small team (2-5) | Hybrid | (default) |
| Medium team (6-15) | Hybrid → Git-Primary | Evaluate team readiness |
| Large team (15+) | Git-Primary | Full enforcement |
| Open source | Hybrid | Advisory only |
| Compliance/regulated | Git-Primary | + audit log |

---

**Still unsure?** Default to **Hybrid Mode** - you can always upgrade later.
