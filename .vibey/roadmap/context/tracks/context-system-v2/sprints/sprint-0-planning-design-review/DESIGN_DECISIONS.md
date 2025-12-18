# Context System V2 - Design Decisions

**Sprint:** 0 - Planning & Design Review
**Date:** 2025-12-17
**Status:** Approved

---

## Summary of User Feedback & Decisions

### 1. Storage Structure

**Decision:** Keep `context/` directory, add subdirectories

```
.vibey/roadmap/context/
├── plans/           # Pre-work planning artifacts
├── runtime/         # Active session state
└── post-mortems/    # Completion summaries
```

**Rationale:** Cleaner than renaming; maintains existing context location.

---

### 2. Hybrid YAML + Markdown Approach

**Decision:** Use YAML for structured metadata, reference longer markdown files

```yaml
# context/plans/01TASK123.yaml
plan_context:
  goals: [...]
  approach: "..."

  # References to longer documents
  artifacts:
    - file: ARCHITECTURE_ANALYSIS.md
      purpose: "Deep dive on existing auth system"
      tokens_estimate: 4500
    - file: IMPLEMENTATION_OPTIONS.md
      purpose: "Comparison of 3 approaches with trade-offs"
      tokens_estimate: 3200
```

**Rationale:**
- YAML always loaded (small, structured)
- AI sees what artifacts exist and their purpose
- AI chooses which to read based on current need
- Large analyses preserved without forced token cost
- Maintains benefits of both formats

---

### 3. Git Commit Linking

**Decision:** Drop timestamp-based linking. Use three signals:

| Signal | Description |
|--------|-------------|
| **File overlap** | Commit files matched against task YAML known_files |
| **Message reference** | Task ID parsed from commit message |
| **Manual link** | Explicit user linking via CLI |

**Rationale:**
- Timestamp was source of parallel task ambiguity
- File-based linking is deterministic and semantically meaningful
- Pre-commit hook provides real-time validation

---

### 4. File Ownership Model

**Decision:** Files can belong to multiple tasks

| Scenario | Valid? |
|----------|--------|
| File in multiple tasks | ✓ |
| File in multiple tasks, same commit | ✓ (commit refs both) |
| Common file (utils.py) in task | ✓ |

**Rationale:** Real work isn't cleanly partitioned. Validation is about consistency, not exclusivity.

---

### 5. Bidirectional Validation

**Decision:** Pre-commit hook validates consistency in both directions

When commit files ≠ YAML tracking for referenced task:
- Don't assume which source is authoritative
- Flag the discrepancy
- Present resolution options to user

**Resolution Options:**
1. Update YAML - Add files to task tracking
2. Update Message - Change task reference
3. Add Reference - Include additional task
4. Proceed - Override, commit as-is

**Rationale:** We can't know if YAML is incomplete or message ref is wrong. User decides.

---

### 6. Pre-Commit Hook Configuration

**Decision:** Configurable enforcement levels

```yaml
# .vibey/config/git_hooks.yaml
pre_commit:
  enabled: true
  mode: prompt  # off | warn | prompt | strict

  on_mismatch:
    files_not_in_yaml: prompt
    yaml_files_not_in_commit: ignore
    no_task_ref: warn
```

| Mode | Behavior |
|------|----------|
| **off** | No hook runs |
| **warn** | Show issues, commit proceeds |
| **prompt** | Show issues, ask for resolution |
| **strict** | Block commit until resolved |

**Rationale:** Different teams/users have different tolerance for friction.

---

### 7. Commit Message Template

**Decision:** Provide templated commit message format

```
# <type>(<scope>): <subject>
#
# Task: <TASK_ID or TASK_IDS>
#
# <body>
```

**Setup:** `vibey git setup-template`

**Multi-task format:** `Task: 01TASK_A, 01TASK_B`

**Rationale:** Increases compliance with expected message structure through guided format.

---

### 8. Confidence Thresholds

**Decision:** Configurable, not hardcoded

- All link signals tracked with individual confidence scores
- Aggregate confidence calculated
- Filtering/thresholds applied at query time, not storage time
- All link data preserved for later analysis

**Rationale:** Let system collect data, decide filtering thresholds based on actual usage patterns.

---

### 9. Known Files Population

**Decision:** Multiple sources, accumulated over time

| Source | When | Mechanism |
|--------|------|-----------|
| Plan context | Before work | `references` → initial known files |
| Runtime tracking | During work | AI logs files it reads/writes |
| First commit | Bootstrap | Message ref + files → establishes association |
| Manual | Anytime | CLI command to add files |

---

### 10. Parallel Tasks Resolution

**Decision:** File-based linking eliminates the problem

- No timestamp = no temporal overlap ambiguity
- Files are deterministic
- Pre-commit hook catches discrepancies immediately
- User resolves at commit time, not after

---

## Data Model

### Commit Link Structure

```yaml
commit_links:
  - sha: abc1234
    message: "feat(auth): Add JWT validation"
    files: [src/auth.py, tests/test_auth.py]
    signals:
      file_overlap:
        matched: true
        files: [src/auth.py]
        confidence: 1.0
      message_ref:
        matched: true
        task_ids: [01TASK_A]
        confidence: 1.0
      manual:
        matched: false
    aggregate_confidence: 1.0
    link_source: pre_commit_hook
    linked_at: '2025-12-17T14:30:00Z'
```

### Task Context Structure

```yaml
context:
  known_files:
    - path: src/auth.py
      source: plan_reference
      added: '2025-12-17T10:00:00Z'
    - path: src/jwt.py
      source: commit_bootstrap
      added: '2025-12-17T11:30:00Z'

  artifacts:
    - file: DESIGN_ANALYSIS.md
      purpose: "Architecture evaluation"
      tokens_estimate: 3500
    - file: IMPLEMENTATION_PLAN.md
      purpose: "Step-by-step approach"
      tokens_estimate: 2000
```

---

## Next Steps

1. Update Sprint 1 & 2 plans to reflect these decisions
2. Implement revised data models
3. Build pre-commit hook with configurable modes
4. Create commit message template system
5. Build file tracking accumulation logic

---

## Approval

- [x] Three-phase context model approved
- [x] Storage structure approved (context/plans, context/runtime, context/post-mortems)
- [x] Hybrid YAML + Markdown approach approved
- [x] Git linking approach approved (file overlap + message ref + manual)
- [x] Bidirectional validation approved
- [x] Pre-commit hook design approved
- [x] Commit message template approved
