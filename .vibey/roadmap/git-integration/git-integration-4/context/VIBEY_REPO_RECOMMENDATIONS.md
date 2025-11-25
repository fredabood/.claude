# Vibey Repository Git Integration Recommendations

**Sprint:** git-integration-4
**Status:** Approved
**Author:** Architecture discussions from Sprint 1, updated Sprint 4
**Date:** 2025-11-25

---

## Executive Summary

This document captures the approved configuration for git integration features in the Vibey repository itself.

**Approved Configuration:** **Blocking Mode** with strict enforcement:

| Rule | Mode | Requirement |
|------|------|-------------|
| Commit → Task | **Blocking** | Every commit must reference a task |
| Task → Commit | **Blocking** | Every task completion requires commits |
| CLI/MCP Usage | **Blocking** | Roadmap updates must use CLI or MCP |
| Track Branches | **Blocking** | Active tracks must have dedicated branches |
| YAML Integrity | **Blocking** | Invalid YAML always blocked |

---

## Background

During Sprint 1 implementation, the following issues were identified:

1. **Manual YAML Edits** - Developer manually edited roadmap YAML files instead of using CLI commands
2. **Missing Evidence** - Tasks marked complete without Git commits as evidence
3. **No Enforcement** - No validation to encourage using the tools we're building

**Question Raised:**
> "What options do I have to guarantee that updates to the roadmap are made with the tools rather than manually?"

This sprint addresses that question by configuring and dogfooding the git integration features in Vibey itself.

---

## Enforcement Modes Comparison

### Mode 1: Off (Not Recommended)
```yaml
git:
  enforcement:
    mode: off
```

**Pros:**
- Zero friction
- No learning curve
- Manual control

**Cons:**
- No guidance or validation
- Easy to make mistakes
- No metrics on compliance
- Defeats purpose of dogfooding

**Recommendation:** ❌ Don't use for Vibey

---

### Mode 2: Advisory (RECOMMENDED)
```yaml
git:
  enforcement:
    mode: advisory
```

**Behavior:**
- Shows warnings but never blocks
- Provides suggestions and guidance
- Exit code always 0 (success)
- Tracks metrics for compliance

**Example:**
```bash
$ git commit -m "feat: Complete Sprint 1"

[vibey] Advisory:
  ⚠ Manual YAML edit detected: sprint.yaml
    Modified: tasks_completed, completion_percent
    Suggestion: vibey roadmap update sprint git-integration-1 --status completed

  ⚠ Task git-integration-1-task-007 marked completed but no commits found
    Suggestion: Add commits or mark as --non-code-task

Proceeding with commit... ✓
```

**Pros:**
- ✅ Guides developers toward best practices
- ✅ Doesn't block legitimate work
- ✅ Collects metrics on actual usage patterns
- ✅ Low friction, high value
- ✅ Identifies UX issues before making them blocking
- ✅ Escape hatch always available

**Cons:**
- Warnings can be ignored
- Lower consistency guarantee
- May not satisfy compliance requirements

**Recommendation:** ✅ **Use for Vibey dogfooding**

---

### Mode 3: Blocking (Future State)
```yaml
git:
  enforcement:
    mode: blocking
```

**Behavior:**
- Validation failures prevent operations
- Exit code 1 on violations
- Must fix issues or use `--no-verify`

**Example:**
```bash
$ git commit -m "feat: Complete Sprint 1"

[vibey] Blocking:
  ✗ Manual YAML edit without CLI command (required)
    Use: vibey roadmap update sprint git-integration-1 --status completed

  ✗ Task marked completed without commits (required)

Commit blocked. Use --no-verify to override.
```

**Pros:**
- Highest consistency
- Enforces best practices
- Good for compliance

**Cons:**
- Can block legitimate work
- Higher friction
- Requires escape hatches
- May frustrate during emergencies

**Recommendation:** ⏰ **Consider after 4-6 weeks of advisory mode success**

---

### Mode 4: Audit (Special Cases)
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

**Use Case:** Metrics collection without any UX impact

**Recommendation:** 🤔 **Useful for silent metrics, but advisory provides more value**

---

## Commit Tracking Configuration

### The `require_commits` Setting

**What it does:**
- When `true`: Tasks cannot be marked `completed` without Git commits as evidence
- When `false`: Tasks can be completed without commits (manual edits trusted)

### Bidirectional Traceability

```yaml
git:
  commit_tracking:
    record_commits: true       # Store commit SHAs in YAML
    require_commits: false     # Start advisory, not blocking
```

**Two directions of validation:**

1. **Commits → Tasks** (already designed)
   - `task_reference` rule requires commits to mention task IDs
   - Helps find which commits belong to which tasks

2. **Tasks → Commits** (new understanding)
   - `require_commits` rule requires tasks to have commits before completion
   - Ensures completed work has evidence

### Recommended Configuration for Vibey

```yaml
git:
  commit_tracking:
    record_commits: true       # YES: Track which commits relate to tasks
    require_commits: false     # START FALSE: Use advisory warnings first

  validation:
    check_completed_tasks: true  # Warn when tasks completed without commits
    suggest_link_commits: true   # Suggest CLI commands to link commits
```

**Enforcement:**
```yaml
git:
  enforcement:
    rules:
      commit_evidence:
        enabled: true
        mode: advisory  # Warn, don't block

        messages:
          no_commits: |
            Task {task_id} marked completed but no commits found.

            Suggestions:
            1. Link existing commits: vibey roadmap link-commits {task_id} <sha>
            2. Mark as non-code task: vibey roadmap update task {task_id} --non-code
            3. Add commits first: git commit -m "feat({task_id}): ..."
```

### Special Cases: Non-Code Tasks

Some tasks don't produce commits:

```yaml
# In sprint.yaml
tasks:
  - id: git-integration-4-task-001
    name: Review and document enforcement mode options
    status: completed
    metadata:
      task_type: documentation  # or: planning, research, review
      commits_required: false
```

**CLI Support:**
```bash
# Mark task as non-code (skips commit check)
vibey roadmap update task task-001 --status completed --non-code
```

---

## CLI Usage Validation

### Problem

Developers manually editing YAML files instead of using CLI commands:

```yaml
# Manual edit to sprint.yaml
tasks_completed: 9  # Changed from 8
completion_percent: 100  # Changed from 89
```

### Solution: Detect and Suggest

**Pre-commit hook detects changes:**

```bash
$ git add .vibey/roadmap/git-integration/git-integration-1/sprint.yaml
$ git commit -m "feat: Complete Sprint 1"

[vibey] Advisory:
  ⚠ Manual YAML edit detected: sprint.yaml
    Changed fields:
      - tasks_completed: 8 → 9
      - completion_percent: 89 → 100

    Suggested CLI command:
      vibey roadmap update sprint git-integration-1 --status completed

    Why use CLI?
      ✓ Validates data consistency
      ✓ Updates dependent fields automatically
      ✓ Provides better error messages
      ✓ Ensures correct calculations

  Continue with manual edit? This commit will proceed.

Proceeding with commit... ✓
```

### Configuration

```yaml
git:
  enforcement:
    rules:
      cli_usage:
        enabled: true
        mode: advisory
        suggest_cli_commands: true
        detect_manual_edits: true

        # Don't warn for these files (expected to be manual)
        exclude_files:
          - context/*.md
          - sprint.yaml (metadata section only)
```

---

## Approved Configuration for Vibey

### Complete Configuration File

```yaml
# .vibey/config/git.yaml
git:
  # Enforcement philosophy - STRICT MODE
  enforcement:
    mode: blocking  # Enforce all rules

    # Audit logging (track compliance)
    audit:
      enabled: true
      file: .vibey/audit/enforcement.log
      retention_days: 90

    # Individual rules - ALL BLOCKING
    rules:
      # BLOCKING: Prevent corruption
      yaml_integrity:
        enabled: true
        mode: blocking
        description: "Invalid YAML is never allowed"

      # BLOCKING: Every commit must reference a task
      task_reference:
        enabled: true
        mode: blocking
        require_valid_id: true
        description: "Every commit must reference a valid task ID"
        patterns:
          - "feat(<task-id>):"
          - "fix(<task-id>):"
          - "Task: <task-id>"
          - "[<task-id>]"

      # BLOCKING: CLI/MCP required for roadmap updates
      cli_usage:
        enabled: true
        mode: blocking
        require_cli_or_mcp: true
        detect_manual_edits: true
        description: "Roadmap YAML updates must use CLI or MCP, not manual edits"
        allowed_manual_files:
          - "context/*.md"  # Context docs can be manual

      # BLOCKING: Tasks require commit evidence
      commit_evidence:
        enabled: true
        mode: blocking
        require_commits: true
        description: "Every task completion requires at least one commit"
        exceptions:
          task_types:
            - documentation  # Pure docs tasks may not have code commits
            - planning
            - review

      # BLOCKING: Track branches required
      track_branches:
        enabled: true
        mode: blocking
        require_branch_for_tracks: true
        branch_pattern: "track/<track-id>"
        description: "Active tracks must have dedicated branches"

      # BLOCKING: Dependency ordering
      merge_ordering:
        enabled: true
        mode: blocking
        enforce_dependency_order: true
        description: "Branches must be merged in dependency order"

  # Commit tracking
  commit_tracking:
    record_commits: true
    require_commits: true  # REQUIRED
    auto_link: true
    bidirectional: true  # Both commit→task and task→commit

  # Branch strategy
  branching:
    strategy: hierarchical
    require_track_branches: true
    branch_patterns:
      track: "track/<track-id>"
      sprint: "sprint/<sprint-id>"
      task: "feature/<task-id>"

  # Validation points
  validation:
    on_commit: true    # Pre-commit hook
    on_push: true      # Pre-push hook
    on_merge: true     # PR merge checks
```

### Why This Configuration?

1. **Every Commit → Task (Blocking)**
   - Full traceability of all changes
   - Audit trail for compliance
   - No orphan commits

2. **Every Task → Commit (Blocking)**
   - Proof of work for all tasks
   - Prevents marking tasks complete without evidence
   - Exception for pure documentation/planning tasks

3. **CLI/MCP Required (Blocking)**
   - Ensures data consistency
   - Proper validation on all updates
   - Prevents calculation errors from manual edits

4. **Track Branches Required (Blocking)**
   - Clear ownership of code changes
   - Better PR organization
   - Supports hierarchical merge strategy

5. **YAML Integrity (Blocking)**
   - Invalid YAML breaks everything
   - Non-negotiable

### Escape Hatches

For emergencies, `--no-verify` bypasses hooks:
```bash
git commit --no-verify -m "emergency: Critical hotfix"
```

All bypasses are logged to the audit file for review.

---

## Adoption Timeline

### Week 1-2: Observation
```yaml
git:
  enforcement:
    mode: audit  # Silent logging only
```

**Goals:**
- Collect baseline metrics
- Identify common patterns
- No user impact

**Metrics:**
- % of commits with task references
- % of manual YAML edits
- % of completed tasks without commits

---

### Week 3-4: Advisory (RECOMMENDED START)
```yaml
git:
  enforcement:
    mode: advisory
    rules:
      yaml_integrity:
        mode: blocking  # Only block corruption
```

**Goals:**
- Enable warnings and suggestions
- Team learns conventions
- Gather feedback on messages

**Metrics:**
- Advisory warning frequency
- Overrides used
- Compliance improvement trends

---

### Week 5-8: Tune and Iterate
```yaml
git:
  enforcement:
    mode: advisory
    rules:
      commit_evidence:
        require_commits: true  # Consider enabling
        mode: advisory  # Still warn, not block
```

**Goals:**
- Refine configurations
- Improve message quality
- Identify blockers

**Evaluation Questions:**
- Are warnings helpful or annoying?
- Do CLI suggestions work?
- Should any rules become blocking?
- What edge cases need handling?

---

### Week 9+: Increase Enforcement (Optional)
```yaml
git:
  enforcement:
    mode: blocking  # Or selective blocking
    rules:
      task_reference:
        mode: blocking  # Main branch only
      commit_evidence:
        mode: advisory  # Keep advisory
```

**Only if:**
- Team comfortable with conventions
- Warnings mostly followed
- Low override rate
- Friction acceptable

---

## CLI Commands for Validation

### Check Consistency
```bash
# Validate YAML vs Git consistency
vibey git validate

# Output:
✓ 15 tasks consistent
⚠ 2 inconsistencies found:

  task-006: Status is 'not_started' but 3 commits reference it
    Commits: abc123, def456, ghi789
    Suggestion: vibey roadmap update task task-006 --status in_progress

  task-007: Marked completed but no commits found
    Suggestion: vibey roadmap link-commits task-007 <sha>
```

### Link Commits to Tasks
```bash
# Manually link commits
vibey roadmap link-commits git-integration-1-task-001 abc123 def456

# Auto-link based on commit message parsing
vibey roadmap sync-commits

# Output:
Scanning commit history...
  Found 12 commits referencing tasks

Linked:
  task-001: 3 commits
  task-002: 5 commits
  task-003: 4 commits
```

### Repair Stale References
```bash
# Fix stale commit references after rebase
vibey git repair

# Output:
Scanning for stale references...
  task-007: commit xyz789 not found
    Found matching commit by message: uvw123
    Updated reference.

1 reference repaired.
```

---

## Metrics Dashboard

```bash
vibey git metrics

# Output:
Enforcement Summary (last 30 days):
  Total commits: 150
  Commits with task refs: 142 (95%)
  Commits without task refs: 8 (5%)

  Manual YAML edits: 23
  CLI commands used: 45
  CLI adoption rate: 66%

  Warnings issued: 45
    - cli_usage: 23 (manual edits)
    - commit_evidence: 12 (missing commits)
    - task_reference: 10 (missing refs)

  Blocks issued: 5
    - yaml_integrity: 5 (all resolved)

  Overrides used: 2
    - --no-verify: 2

Trends:
  ✓ Task reference compliance improving (89% → 95%)
  ✓ CLI usage increasing (50% → 66%)
  ⚠ Commit evidence still low (60%)
```

---

## Success Criteria

### Configuration Success
- ✅ Git hooks installed and working
- ✅ Advisory mode providing helpful warnings
- ✅ YAML integrity blocking prevents corruption
- ✅ CLI suggestions being followed

### Dogfooding Success
- ✅ Team using git integration features daily
- ✅ Compliance rates improving over time
- ✅ Low override/bypass rate (<5%)
- ✅ Positive feedback on UX
- ✅ Configuration feels "right" for workflow

### Product Success
- ✅ UX issues identified and documented
- ✅ Edge cases discovered and handled
- ✅ Configuration examples validated
- ✅ Documentation improved based on real usage
- ✅ Confidence in recommendations for other users

---

## Open Questions

1. **Should require_commits be on for Vibey?**
   - Pros: Ensures all work has evidence
   - Cons: Non-code tasks need overrides
   - Recommendation: Start advisory, evaluate

2. **How strict should CLI usage enforcement be?**
   - Advisory seems right for Vibey
   - Manual edits sometimes necessary (bulk updates)
   - Suggestion: Warn but allow

3. **What about emergency fixes?**
   - Always allow `--no-verify`
   - Log overrides for review
   - Trust developer judgment

4. **Branch-specific rules?**
   - Main branch stricter than feature branches?
   - Worth the complexity?
   - Recommendation: Start simple, add if needed

---

## Next Steps (Sprint 4 Tasks)

1. **Task 001:** Document this comparison for review ✓ (this document)
2. **Task 002:** Implement commit tracking and validation
3. **Task 003:** Build CLI suggestion system
4. **Task 004:** Configure and install advisory mode
5. **Task 005:** Dogfood for 2 weeks, evaluate, iterate

---

## References

- [Sprint 0: Enforcement Philosophy](../context/005-enforcement-philosophy.md)
- [Sprint 0: Source of Truth](../context/002-source-of-truth.md)
- [Sprint 0: Architecture Document](../context/007-architecture-document.md)
- [Sprint 1: Git Analysis Docs](../../../../docs/operations/GIT_ANALYSIS.md)

---

**Status:** Planning
**Review Date:** After Sprint 3 completion
**Implementation:** Sprint 4 (1.5 weeks, 5 tasks)
