# Vibey-Git Integration Architecture

**Version:** 1.0.0
**Status:** Draft
**Sprint:** git-integration-0 (Integration Architecture & Design)
**Date:** 2025-11-24

---

## Executive Summary

This document establishes the architectural foundation for integrating Vibey roadmap management with Git version control. The integration enables:

- **Traceability:** Link commits to roadmap tasks
- **Automation:** Update task status from Git activity
- **Visibility:** Track progress through Git history
- **Quality:** Enforce roadmap conventions via hooks

### Three-Scenario Source of Truth Model

Vibey adapts to your project context with three distinct modes:

1. **YAML-Only (Scenario 1):** For non-Git projects — Vibey standalone
2. **Hybrid (Scenario 2 - DEFAULT):** For Git repos — YAML primary, Git supporting
3. **Git-Primary (Scenario 3):** For strict Git teams — Git authoritative, YAML derived

The design prioritizes flexibility, allowing teams to adopt features incrementally while supporting various Git workflows. Most teams use Hybrid mode (90%), which provides Git integration without strict requirements.

---

## 1. Design Principles

### 1.1 Core Values

| Principle | Description |
|-----------|-------------|
| **Adapt, Don't Impose** | Vibey adapts to existing Git workflows |
| **Enable, Don't Obstruct** | Guidance over blocking; escape hatches always available |
| **Explicit over Implicit** | YAML state is authoritative; commits provide evidence |
| **Gradual Adoption** | Features can be adopted incrementally |
| **Developer Experience** | Minimize friction, maximize value |

### 1.2 Non-Goals

- Replacing Git as version control
- Enforcing a single branching strategy
- Requiring task references in every commit
- Breaking existing Git workflows

---

## 2. Primitive Mapping

*Full specification: [001-primitive-mapping.md](./001-primitive-mapping.md)*

### 2.1 Hierarchy Comparison

```
Vibey Hierarchy              Git Hierarchy
─────────────────           ─────────────────
Roadmap                     Repository
  └── Track (1..n)            └── Branch (1..n)
        └── Sprint (1..n)           └── Commit (1..n)
              └── Task (1..n)             └── Tag (0..n)
```

### 2.2 Mapping Summary

| Vibey Primitive | Git Primitive | Cardinality | Required |
|-----------------|---------------|-------------|----------|
| Roadmap | Repository | 1:1 | Yes |
| Track | Branch namespace | 1:0..1 | No |
| Sprint | Tag range | 1:0..2 | No |
| Task | Commit(s) | 1:0..n | No |
| Quality Gate | CI Check | 1:0..1 | No |
| Blocker | Branch protection | 1:0..1 | No |
| Dependency | Merge order | n:n | No |

### 2.3 Key Decisions

1. **Roadmap:Repository = 1:1** — One roadmap per repository (multi-repo not supported in v1)
2. **Track branches are optional** — Works with trunk-based and GitFlow equally
3. **Tasks link to commits via messages** — Convention over configuration
4. **Sprint tags are optional** — Lightweight markers for velocity tracking

---

## 3. Source of Truth Model

*Full specifications: [002-source-of-truth.md](./002-source-of-truth.md) | [008-architecture-addendum.md](./008-architecture-addendum.md) | [009-decision-matrix.md](./009-source-of-truth-decision-matrix.md)*

### 3.1 Three-Scenario Model

Vibey's source of truth adapts to your project context:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Source of Truth Decision Tree                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Is this a Git repository?                                       │
│    │                                                             │
│    ├─ NO ──────────────────────────► YAML-ONLY MODE             │
│    │                                  (Scenario 1)               │
│    │                                  Vibey standalone           │
│    │                                                             │
│    └─ YES ─► Is Git strategy enforced?                          │
│                │                                                 │
│                ├─ NO ───────────────────► HYBRID MODE           │
│                │                          (Scenario 2 - DEFAULT) │
│                │                          YAML primary           │
│                │                                                 │
│                └─ YES ─► User opted in? ─┐                      │
│                            │              │                      │
│                            ├─ YES ────────┼──► GIT-PRIMARY MODE │
│                            │              │    (Scenario 3)      │
│                            │              │    Git authoritative │
│                            │              │                      │
│                            └─ NO ─────────┼──► HYBRID MODE      │
│                                          │    (safe default)     │
│                                          │                       │
└──────────────────────────────────────────┼──────────────────────┘
```

### 3.2 Scenario Comparison

| Scenario | Git Repo? | Source of Truth | When to Use |
|----------|-----------|-----------------|-------------|
| **1. YAML-Only** | No | YAML files only | Non-Git projects, prototyping |
| **2. Hybrid** | Yes | YAML (Git supports) | **Most projects (DEFAULT)** |
| **3. Git-Primary** | Yes | Git (YAML derived) | Strict Git discipline teams |

### 3.3 Scenario 1: YAML-Only Mode

**When:**
- Not a Git repository
- OR `git.enabled: false`

**Behavior:**
```yaml
# No Git integration
git:
  enabled: false
```

- YAML files are sole source of truth
- No Git features available
- Manual roadmap management

**Use Cases:**
- Personal project planning
- Non-code projects
- Vibey evaluation

---

### 3.4 Scenario 2: Hybrid Mode (DEFAULT)

**When:**
- Git repository exists
- Strategy NOT enforced OR user hasn't opted into Git-primary

**Behavior:**
```yaml
# Default for Git repositories
git:
  enabled: true
  strategy:
    enforce: false  # Default
  source_of_truth:
    mode: auto  # Auto-detects: hybrid
    allow_git_primary: false  # Default
```

**Characteristics:**
- **YAML is authoritative** — Current state in YAML files
- **Git provides evidence** — Commits support/validate
- **Advisory warnings** — Inconsistencies shown, not blocking
- **Manual control** — YAML can be edited directly

**Conflict Handling:**

| Scenario | Resolution |
|----------|------------|
| YAML=incomplete, Git=work exists | Advisory warning |
| YAML=complete, Git=no commits | Valid (non-code task) |
| Both agree | Consistent state |
| Commit references unknown task | Warning (typo or deleted) |

**Use Cases:**
- **Most projects** (90% of users)
- Teams learning Vibey
- Mixed Git discipline
- Flexible workflows

---

### 3.5 Scenario 3: Git-Primary Mode

**When:**
- Git repository exists
- Strategy IS enforced (`strategy.enforce: true`)
- AND User opted in (`allow_git_primary: true`)

**Behavior:**
```yaml
# Explicit opt-in required
git:
  enabled: true
  strategy:
    enforce: true  # Must enforce strategy
    requirements:
      branches:
        task_branch: {required: true}
      tags:
        sprint_boundaries: {required: true}
      commits:
        task_reference: {required: true}

  enforcement:
    mode: blocking  # Prevent violations

  source_of_truth:
    mode: auto  # Auto-detects: git
    allow_git_primary: true  # EXPLICIT OPT-IN
```

**Characteristics:**
- **Git is authoritative** — State derived from branches/tags/commits
- **YAML is cached** — Auto-generated from Git state
- **Manual edits overwritten** — YAML not directly editable
- **Full automation** — Task status inferred from Git

**Derivation Rules:**
```
Task Status:
  not_started: no branch AND no commits
  in_progress: branch exists OR commits exist BUT not merged
  completed: branch merged AND end tag present

Sprint Status:
  not_started: no start tag
  in_progress: start tag exists, no end tag
  completed: end tag exists
```

**Use Cases:**
- Large teams (15+)
- Strict Git discipline
- Compliance/audit needs
- High automation desired

---

### 3.6 Key Decisions

1. **Three scenarios, not one** — Source of truth adapts to context
2. **Hybrid is default** — Lowest friction for Git repos
3. **Git-primary requires opt-in** — Prevents accidental mode switches
4. **Automatic fallback** — Git-primary falls back to hybrid on violations

---

## 4. Commit Conventions

*Full specification: [003-commit-conventions.md](./003-commit-conventions.md)*

### 4.1 Supported Formats

**Format 1: Conventional Commits (Recommended)**
```
feat(task-001): implement content loader
```

**Format 2: Footer Reference**
```
feat: implement content loader

Task: task-001
```

**Format 3: Bracket Notation**
```
[task-001] implement content loader
```

### 4.2 Task Reference Patterns

```regex
# Conventional scope
^(?P<type>\w+)\((?P<task_id>[\w-]+)\):

# Footer
^Task:\s*(?P<task_id>[\w-]+)$

# Bracket
^\[(?P<task_id>[\w-]+)\]
```

### 4.3 Key Decisions

1. **Multiple formats supported** — Teams choose their preference
2. **Conventional Commits compatible** — Industry standard integration
3. **Multi-task commits allowed** — One commit can reference multiple tasks
4. **Status keywords** — `Closes:`, `Completes:` indicate completion

---

## 5. Branching Strategy

*Full specification: [004-branching-strategy.md](./004-branching-strategy.md)*

### 5.1 Supported Models

| Model | Description | Team Size |
|-------|-------------|-----------|
| **Trunk-Based** | Single main branch, task refs in commits | 1-5 |
| **Feature Branch** | Branch per task, PR-based | 5-15 |
| **Sprint Branch** | Branch per sprint, merged at sprint end | 10-20 |
| **Track Branch** | Full GitFlow with track branches | 20+ |
| **Flexible** | No enforcement, Vibey adapts | Any |

### 5.2 Branch Naming Conventions

```
feature/<task-id>-<description>
sprint/<sprint-id>
track/<track-id>
bugfix/<task-id>-<description>
```

### 5.3 Key Decisions

1. **No enforced branching model** — Teams use existing workflows
2. **Branch-task association is optional** — Detected from naming or explicit config
3. **Sprint tags recommended** — Lightweight, high value
4. **Default: Feature branch model** — Balance of structure and simplicity

---

## 6. Enforcement Philosophy

*Full specification: [005-enforcement-philosophy.md](./005-enforcement-philosophy.md)*

### 6.1 Enforcement Modes

| Mode | Behavior | Default |
|------|----------|---------|
| **Off** | No hooks, no validation | No |
| **Advisory** | Warnings only, never blocks | **Yes** |
| **Blocking** | Prevents invalid operations | No |
| **Audit** | Logs violations, doesn't warn | No |

### 6.2 Enforcement Points

```
Pre-Commit ─────► Commit-Msg ─────► Pre-Push ─────► CI/PR Check
     │                │                │                │
     ▼                ▼                ▼                ▼
  YAML valid?    Task ref valid?   All OK?        Conflicts?
                 Task exists?                    Blockers?
                                                 Gates passed?
```

### 6.3 Key Decisions

1. **Advisory is default** — Enable don't obstruct
2. **Per-rule configuration** — Different rules can have different modes
3. **Per-branch overrides** — Stricter on main, relaxed on feature
4. **Override mechanisms** — `--no-verify`, `VIBEY_SKIP_HOOKS`

### 6.4 Adoption Path

```
Week 1-2: Audit mode (observe)
Week 3-4: Advisory mode (guide)
Week 5+:  Selective blocking (enforce critical rules)
Month 2+: Full blocking (if desired)
```

---

## 7. State Reconstruction

*Full specification: [006-state-reconstruction.md](./006-state-reconstruction.md)*

### 7.1 Capabilities

| Capability | Method | Use Case |
|------------|--------|----------|
| Point-in-time state | Git checkout YAML | Retrospectives |
| Attribution | Git log + YAML diff | Accountability |
| Progress history | Sample states over time | Burndown charts |
| Rollback | Restore YAML from ref | Recovery |

### 7.2 CLI Commands

```bash
vibey git state-at <ref>          # State at commit/tag/date
vibey git diff <ref1> <ref2>      # Compare states
vibey git history <task-id>       # Task change history
vibey git progress <sprint-id>    # Progress over time
vibey git rollback <ref>          # Restore state
```

### 7.3 Key Decisions

1. **YAML in Git enables reconstruction** — No separate storage needed
2. **Audit log is optional** — Extra detail for compliance needs
3. **Caching for performance** — Frequently accessed states cached
4. **Rollback is full restore** — Simpler than selective

---

## 8. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Vibey-Git Integration Architecture                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                           User Interface                              │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐     │   │
│  │  │    CLI     │  │    MCP     │  │    IDE     │  │    CI/CD   │     │   │
│  │  │  Commands  │  │   Tools    │  │ Extensions │  │  Checks    │     │   │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘     │   │
│  └────────┼───────────────┼───────────────┼───────────────┼─────────────┘   │
│           │               │               │               │                  │
│           └───────────────┴───────────────┴───────────────┘                  │
│                                   │                                          │
│  ┌────────────────────────────────▼────────────────────────────────────┐    │
│  │                         Core Library                                 │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐        │    │
│  │  │    Roadmap     │  │      Git       │  │  Reconciler    │        │    │
│  │  │   Operations   │  │   Operations   │  │                │        │    │
│  │  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘        │    │
│  └──────────┼───────────────────┼───────────────────┼──────────────────┘    │
│             │                   │                   │                        │
│  ┌──────────▼───────────────────▼───────────────────▼──────────────────┐    │
│  │                         Data Layer                                   │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐        │    │
│  │  │   YAML Files   │  │  Git History   │  │   Audit Log    │        │    │
│  │  │ (.vibey/       │  │  (Commits,     │  │  (Optional)    │        │    │
│  │  │  roadmap/)     │  │   Tags)        │  │                │        │    │
│  │  └────────────────┘  └────────────────┘  └────────────────┘        │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                          Git Hooks                                    │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐     │   │
│  │  │ Pre-Commit │  │ Commit-Msg │  │  Pre-Push  │  │  Post-*    │     │   │
│  │  │  (YAML     │  │  (Task     │  │  (Final    │  │  (Status   │     │   │
│  │  │  validate) │  │   refs)    │  │   check)   │  │   update)  │     │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Configuration Reference

### 9.1 Complete Configuration Schema

```yaml
# .vibey/config/git.yaml
git:
  enabled: true

  # Source of truth settings
  source_of_truth:
    primary: yaml              # yaml|git
    reconciliation: advisory   # off|advisory|blocking

  # Commit conventions
  commit:
    preferred_formats:
      - conventional
      - footer
      - bracket
    require_task_reference: false
    validate_task_exists: true
    parse_inline: false

  # Branching configuration
  branching:
    model: feature             # trunk|feature|sprint|track|flexible
    track_branches: false
    sprint_tags: true
    auto_create: false

  # Enforcement settings
  enforcement:
    mode: advisory             # off|advisory|blocking|audit
    rules:
      task_reference:
        enabled: true
        mode: null             # Inherit from global
      yaml_integrity:
        enabled: true
        mode: blocking         # Always block invalid YAML
      task_status:
        enabled: true
        warn_blocked: true
      quality_gates:
        enabled: true
        block_below_threshold: false
      blockers:
        enabled: true
        prevent_blocked_work: false

    branch_overrides:
      main:
        mode: blocking
      "feature/*":
        mode: advisory

  # State reconstruction
  reconstruction:
    enabled: true
    cache:
      enabled: true
      ttl_seconds: 300
    audit:
      enabled: false
      path: .vibey/audit/changes.jsonl
```

---

## 10. CLI Commands Reference

### 10.1 Git Integration Commands

| Command | Description |
|---------|-------------|
| `vibey git init` | Initialize git integration |
| `vibey git hooks install` | Install git hooks |
| `vibey git hooks uninstall` | Remove git hooks |
| `vibey git validate` | Check YAML/Git consistency |
| `vibey git repair` | Fix stale references |

### 10.2 Analysis Commands

| Command | Description |
|---------|-------------|
| `vibey git analyze` | Analyze commit history |
| `vibey git state-at <ref>` | Show state at commit |
| `vibey git diff <a> <b>` | Compare states |
| `vibey git history <task>` | Show task history |
| `vibey git progress <sprint>` | Show progress over time |

### 10.3 Branch Commands

| Command | Description |
|---------|-------------|
| `vibey git branches` | List branches with tasks |
| `vibey git branch create <task>` | Create task branch |
| `vibey git branch link <branch> <task>` | Associate branch with task |

### 10.4 Merge Commands

| Command | Description |
|---------|-------------|
| `vibey git check-merge` | Validate before merge |
| `vibey git merge-order` | Suggest merge sequence |
| `vibey git conflicts` | Show task conflicts |

---

## 11. Implementation Roadmap

### Phase 1: Foundation (Sprint 1)

- Commit message parsing
- Task-commit correlation
- Git history analysis
- `vibey git analyze` command

### Phase 2: Hooks (Sprint 2)

- Pre-commit validation
- Commit-msg parsing
- Auto status updates
- Hook install/uninstall

### Phase 3: Advanced (Sprint 3)

- PR merge conflict detection
- Quality gate CI integration
- Blocker enforcement
- Dependency ordering
- Error handling

---

## 12. Migration Guide

### 12.1 Adding to Existing Repository

```bash
# 1. Initialize Vibey (if not already)
vibey init

# 2. Enable git integration
vibey config set git.enabled true

# 3. Install hooks (optional)
vibey git hooks install

# 4. Validate current state
vibey git validate

# 5. Start using task references in commits
git commit -m "feat(task-001): first integrated commit"
```

### 12.2 Gradual Adoption

1. **Week 1:** Enable audit mode, observe patterns
2. **Week 2:** Enable advisory mode, team learns conventions
3. **Week 3:** Enable hooks for new work
4. **Week 4+:** Increase strictness as team matures

### 12.3 Removing Integration

```bash
# 1. Uninstall hooks
vibey git hooks uninstall

# 2. Disable integration
vibey config set git.enabled false

# 3. Roadmap YAML files remain intact
# 4. Tags/branches can be kept or removed manually
```

---

## 13. FAQ

### Q: Which source of truth mode should I use?

**For 90% of projects:** Use **Hybrid mode** (Scenario 2) - the default for Git repositories. It provides Git integration without strict requirements.

- **YAML-Only:** Only if not using Git
- **Hybrid:** Default for Git repos (recommended)
- **Git-Primary:** Only if team has strict Git discipline and wants full automation

See [009-decision-matrix.md](./009-source-of-truth-decision-matrix.md) for detailed guidance.

### Q: Can I use Vibey without Git?

Yes. Vibey works standalone (YAML-Only mode). All roadmap features available without Git integration.

### Q: What happens when I initialize Git in a YAML-only project?

Mode automatically upgrades from YAML-only to Hybrid. Git integration features become available.

### Q: Do I have to use task references in every commit?

No. Task references are optional by default in Hybrid mode. Enable `require_task_reference: true` only if your team wants strict enforcement.

### Q: What happens if I use `--no-verify`?

The commit proceeds without Vibey hooks running. This is an intentional escape hatch for emergencies.

### Q: Can I use this with GitFlow?

Yes. Vibey supports any branching strategy. Use track branches, sprint branches, or no special branches at all.

### Q: Will this slow down my commits?

Minimal impact. Hooks run in <100ms for most operations. YAML validation is fast.

### Q: How does this work with squash merges?

Task references in commit messages are preserved through squash. Specific SHA links in YAML may become stale but can be repaired with `vibey git repair`.

### Q: Can multiple people complete the same task?

The merge conflict detection will flag this. Resolution options: keep first completion, keep second, or merge (both contributed).

### Q: Can I switch from Hybrid to Git-Primary mode later?

Yes. Use `vibey git strategy adopt <strategy>` to enforce requirements, then opt in with `allow_git_primary: true`. See migration guide in the addendum.

---

## 14. Glossary

| Term | Definition |
|------|------------|
| **Primitive** | Basic building block (Roadmap, Track, Sprint, Task) |
| **Task Reference** | Mention of task ID in commit message |
| **Advisory Mode** | Warn but don't block |
| **Blocking Mode** | Prevent invalid operations |
| **Reconciliation** | Process of comparing YAML and Git state |
| **Sprint Tag** | Git tag marking sprint boundary |
| **Track Branch** | Long-lived branch for entire track |

---

## 15. Decision Log

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Roadmap scope | 1:1 with repo (v1) | Simplicity, clear ownership; submodules in v2 |
| 2 | **Source of truth model** | **Three scenarios** | **Adapts to project context** |
| 2a | Non-Git projects | YAML-only | No Git available |
| 2b | Git repos (default) | Hybrid (YAML-primary) | Flexible, gradual adoption |
| 2c | Strict Git + opt-in | Git-primary | Full automation, compliance |
| 3 | Default for Git repos | Hybrid mode | Lowest friction, 90% use case |
| 4 | Git-primary opt-in | Explicit required | Prevent accidental mode switch |
| 5 | Default enforcement | Advisory | Enable, don't obstruct |
| 6 | Branching model | Flexible (no enforcement) | Support all workflows |
| 7 | Task references | Optional (hybrid), Required (git-primary) | Context-dependent |
| 8 | Commit format | Multiple supported | Team preference |
| 9 | YAML integrity | Always blocking | Invalid YAML breaks everything |
| 10 | State reconstruction | Git checkout based | Simple, no extra storage |
| 11 | Task tags | Optional | Enhancement for fast queries |
| 12 | Tag repair | Automated | Survive squash/rebase |
| 13 | Branch hierarchy | Optional | Support GitFlow if desired |
| 14 | Strategy enforcement | Configurable presets | Team choice |

---

## 16. References

### Core Design Documents

1. [001-primitive-mapping.md](./001-primitive-mapping.md) — Vibey-Git primitive mapping
2. [002-source-of-truth.md](./002-source-of-truth.md) — Source of truth model (hybrid)
3. [003-commit-conventions.md](./003-commit-conventions.md) — Commit message conventions
4. [004-branching-strategy.md](./004-branching-strategy.md) — Branching strategy
5. [005-enforcement-philosophy.md](./005-enforcement-philosophy.md) — Enforcement philosophy
6. [006-state-reconstruction.md](./006-state-reconstruction.md) — State reconstruction model

### Extended Design Documents

7. [008-architecture-addendum.md](./008-architecture-addendum.md) — Advanced patterns (submodules, task tags, hierarchical branching, three-scenario model)
8. [009-source-of-truth-decision-matrix.md](./009-source-of-truth-decision-matrix.md) — Decision guide for choosing source of truth mode
9. [QUICK-REFERENCE.md](./QUICK-REFERENCE.md) — One-page command reference

### External References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)
- [GitFlow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Trunk-Based Development](https://trunkbaseddevelopment.com/)

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-24
**Status:** Draft — Pending Architecture Review
