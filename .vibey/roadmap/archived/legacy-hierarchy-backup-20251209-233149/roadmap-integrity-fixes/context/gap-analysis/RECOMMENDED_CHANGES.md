# Recommended Changes to Roadmap Integrity Fixes Track

**Date:** 2025-11-12
**Based on:** Critical Process & Methodology Review
**Priority:** Implement before starting Sprint 0

---

## Critical Changes Required (MUST DO)

### Change #1: Add Three Verification Tasks to Sprint 0

**Current State:** 13 tasks (001-013)
**Recommended:** 16 tasks (001-016)

#### New Task 014: Independent Verification & Accuracy Validation

```yaml
task:
  id: roadmap-integrity-fixes-0-task-014
  title: Independent verification and accuracy validation
  description: |
    Second agent performs independent verification of audit findings to catch
    errors, bias, or misinterpretations before fixes are applied.

    Verification Steps:
    1. Random sample selection (30% of track audits = 3 tracks)
    2. Independent re-audit of selected tracks
    3. Compare findings with original audit
    4. Calculate inter-rater reliability
    5. Identify and resolve disagreements
    6. Assess overall audit accuracy

    Acceptance Criteria:
    - 3 tracks independently re-audited (standards-system, testing-system, one other)
    - Inter-rater reliability calculated (must be ≥90%)
    - All disagreements documented and resolved
    - If accuracy <90%, flag problematic audits for redo
    - Verification report produced

    Deliverables:
    - Independent verification report
    - Inter-rater reliability score
    - Disagreement resolution log
    - Audit accuracy assessment

  depends_on:
    - blocker_id: roadmap-integrity-fixes-0-task-001
      blocker_type: task
      required_status: completed
    - blocker_id: roadmap-integrity-fixes-0-task-002
      blocker_type: task
      required_status: completed
    - blocker_id: roadmap-integrity-fixes-0-task-011
      blocker_type: task
      required_status: completed

  estimated_tokens: 8000
  complexity: high
  assigned_agent: test-engineer  # Different agent than web-developer
```

#### New Task 015: Functional Verification Testing

```yaml
task:
  id: roadmap-integrity-fixes-0-task-015
  title: Functional verification testing of claimed features
  description: |
    Verify that claimed completed work actually functions correctly. Don't just
    trust commits - test that features work.

    Testing Strategy:

    1. standards-system:
       - Verify Standard dataclass exists and has all fields
       - Test CRUD operations on standards
       - Verify Roadmap/Track/Sprint models have standards field
       - Test loading/saving YAML with standards
       - Check if standards filtering works

    2. testing-system:
       - Run full test suite: pytest tests/
       - Measure actual test coverage
       - Count actual test files and test cases
       - Verify tests are passing
       - Check test infrastructure completeness

    3. documentation-system:
       - Verify claimed docs exist
       - Check doc completeness and currency
       - Verify doc links work
       - Assess doc quality vs standards

    4. All "completed" tracks:
       - Test at least one core feature
       - Verify deliverables exist
       - Check quality meets standards

    Acceptance Criteria:
    - Functional tests performed for all tracks claiming completion
    - Features either work (evidence of completion) or don't work (not completed)
    - Test results documented with pass/fail
    - Status recommendations adjusted based on functional tests
    - Working features = strong evidence, broken features = invalid completion claim

    Deliverables:
    - Functional verification report
    - Test results for each track
    - Adjusted status recommendations based on functional testing
    - Feature completeness assessment

  depends_on:
    - blocker_id: roadmap-integrity-fixes-0-task-011
      blocker_type: task
      required_status: completed

  estimated_tokens: 10000
  complexity: very_high
  assigned_agent: test-engineer
```

#### New Task 016: Backup Integrity & Comparison Analysis

```yaml
task:
  id: roadmap-integrity-fixes-0-task-016
  title: Backup integrity verification and comparison
  description: |
    Verify backup data integrity and determine which backup is authoritative.
    Two backups exist 31 seconds apart - why? Which is correct?

    Investigation Steps:

    1. Backup Discovery:
       - List all backups in .vibey/hierarchical-migration-backups/
       - List all backups in .vibey/migration-backups/
       - Document backup timestamps and contents

    2. Backup Comparison:
       - Compare backup_20251109_171311 vs backup_20251109_171342
       - Identify differences in track data
       - Identify differences in sprint data
       - Identify differences in task data
       - Determine why two backups exist 31 seconds apart

    3. Git State Verification:
       - Identify git commit at time of each backup
       - Checkout git state at backup time
       - Compare backup contents vs git state
       - Verify backup accuracy

    4. Backup Completeness Check:
       - Are all tracks backed up?
       - Are all sprints backed up?
       - Are task files included?
       - What's missing from backups?

    5. Reliability Assessment:
       - Which backup is authoritative?
       - Which backup should be trusted?
       - Assign reliability scores (Green/Yellow/Red)
       - Document backup limitations

    6. Pre-Migration State Analysis:
       - What was state before migration?
       - Was data already corrupt before migration?
       - Can we trace back to clean state?

    Acceptance Criteria:
    - Both backups compared and differences documented
    - Git state at backup time verified
    - Backup completeness assessed
    - Authoritative backup determined
    - Reliability scores assigned per track
    - Pre-migration corruption identified

    Deliverables:
    - Backup comparison report
    - Backup reliability matrix (per track)
    - Authoritative backup determination
    - Pre-migration state analysis
    - Backup usage recommendations

  depends_on: []  # Can run in parallel with track audits

  estimated_tokens: 6000
  complexity: medium
  assigned_agent: web-developer
```

**Implementation:**
- Add these 3 tasks to Sprint 0
- Update Task 012 to depend on 014, 015, 016 in addition to 011 and 013
- Update Sprint 0 task count: 13 → 16 tasks

---

### Change #2: Add Approval Gate After Sprint 0

**Current Flow:**
```
Sprint 0 (Audit) → Sprint 1 (Fixes)
```

**Recommended Flow:**
```
Sprint 0 (Audit) → **APPROVAL GATE** → Sprint 1 (Fixes)
```

**Approval Gate Requirements:**

```yaml
sprint:
  id: roadmap-integrity-fixes-0
  # ... existing fields ...

  completion_requirements:
    - All 16 tasks completed
    - Comprehensive report reviewed by stakeholder
    - Human approval obtained before proceeding to Sprint 1
    - Approval especially critical for:
      * Deletion of 81 phantom task claims
      * Status changes for 4 tracks
      * Any irreversible operations

metadata:
  notes: |
    APPROVAL GATE AFTER THIS SPRINT

    After Task 012 completes, DO NOT automatically start Sprint 1.

    Required Process:
    1. Stakeholder reviews comprehensive forensic audit report
    2. Stakeholder reviews verification reports (Tasks 014, 015, 016)
    3. Stakeholder questions assumptions and challenges findings
    4. Stakeholder validates conclusions make sense
    5. Stakeholder explicitly approves proceeding to Sprint 1

    Focus areas for review:
    - Are status change recommendations justified?
    - Is evidence for "not completed" strong enough?
    - Are we confident enough to delete 81 task claims?
    - Did functional testing prove features work/don't work?
    - Did independent verification catch any errors?
    - Are there any ambiguous cases that need discussion?

    Only proceed to Sprint 1 after explicit approval.
```

**Implementation:**
- Update Sprint 0 notes to include approval gate
- Update Sprint 1 depends_on to require "Sprint 0 + approval"
- Add approval checklist to Sprint 0 deliverables

---

### Change #3: Revise Sprint 0 Timeline

**Current:** 4 days (32 hours) for 13 tasks
**Realistic:** 6-7 days (48-56 hours) for 16 tasks

**Option A: Extend Timeline (Recommended)**

```yaml
sprint:
  id: roadmap-integrity-fixes-0
  estimated_duration: 7 days  # Changed from 4 days

  metadata:
    notes: |
      Timeline Rationale:
      - 10 track forensic audits: ~25 hours (2.5 hrs each)
      - Cross-track analysis: ~5 hours
      - Comprehensive report: ~7 hours
      - Standards audit: ~8 hours
      - Independent verification: ~6 hours
      - Functional testing: ~8 hours
      - Backup analysis: ~4 hours
      Total: ~63 hours

      With 7 days @ 8 hours/day = 56 hours capacity
      Includes ~10% buffer for unexpected issues
```

**Option B: Parallelize with 2 Agents**

```yaml
sprint:
  id: roadmap-integrity-fixes-0
  estimated_duration: 5 days  # Achievable with 2 agents

  metadata:
    agent_allocation: |
      Agent 1 (web-developer):
      - Tasks 001-005 (forensic audits)
      - Task 011 (cross-track analysis)
      - Task 012 (comprehensive report)
      - Task 016 (backup analysis)
      Estimated: 28-35 hours

      Agent 2 (test-engineer):
      - Tasks 006-010 (forensic audits)
      - Task 013 (standards audit)
      - Task 014 (independent verification)
      - Task 015 (functional testing)
      Estimated: 30-38 hours

      Both agents work in parallel.
      Calendar time: 5 days (realistic with parallel execution)
```

**Implementation:**
- Update estimated_duration in sprint.yaml
- Add timeline rationale to notes
- If using Option B, assign tasks to specific agents

---

### Change #4: Update Task 012 Dependencies

**Current:**
```yaml
depends_on:
  - blocker_id: roadmap-integrity-fixes-0-task-011
  - blocker_id: roadmap-integrity-fixes-0-task-013
```

**Recommended:**
```yaml
depends_on:
  - blocker_id: roadmap-integrity-fixes-0-task-011  # Cross-track analysis
  - blocker_id: roadmap-integrity-fixes-0-task-013  # Standards audit
  - blocker_id: roadmap-integrity-fixes-0-task-014  # Independent verification
  - blocker_id: roadmap-integrity-fixes-0-task-015  # Functional testing
  - blocker_id: roadmap-integrity-fixes-0-task-016  # Backup analysis
```

**Rationale:** Task 012 (comprehensive report) must synthesize ALL findings, including verification results.

---

### Change #5: Remove Task 013 Dependency on Task 011

**Current:**
```yaml
task:
  id: roadmap-integrity-fixes-0-task-013
  depends_on:
    - blocker_id: roadmap-integrity-fixes-0-task-011  # Unnecessary!
```

**Recommended:**
```yaml
task:
  id: roadmap-integrity-fixes-0-task-013
  depends_on:
    - blocker_id: roadmap-integrity-fixes-0-task-010  # Last track audit
```

**Rationale:** Standards audit can start as soon as track audits complete. Doesn't need cross-track synthesis first. This enables more parallelization.

---

## High-Priority Changes (SHOULD DO)

### Change #6: Add Confidence Scoring

**Update all forensic audit task acceptance criteria:**

```yaml
acceptance_criteria:
  - "Status recommendation includes confidence score (high/medium/low)"
  - "Evidence strength assessed (strong/moderate/weak)"
  - "Conflicting evidence documented"
  - "Human review flag set if confidence < high"

deliverables:
  - Forensic audit report with sections:
    * Status Recommendation: in_progress
    * Confidence Level: medium
    * Evidence Strength: moderate
    * Conflicting Evidence: Yes (backup shows tasks, git shows deletions)
    * Reasoning: "Code exists but was later deleted. Unclear if ever production-ready."
    * Human Review Required: Yes
```

**Implementation:** Update Tasks 001-010 acceptance criteria and deliverable specs.

---

### Change #7: Change Deletion to Archival

**Update Sprint 2 from:**
```yaml
deliverables:
  - "Cleaned phantom task data (81 tasks)"  # Implies deletion
```

**To:**
```yaml
deliverables:
  - "Archived phantom task claims to .vibey/roadmap/archived/"
  - "Documentation of what was archived and why"
  - "Recovery procedure if archival was incorrect"
```

**Update Sprint 2 notes:**
```yaml
metadata:
  notes: |
    ARCHIVAL STRATEGY (NOT DELETION)

    Do not permanently delete phantom task claims. Instead:
    1. Move to .vibey/roadmap/archived/phantom-tasks/
    2. Preserve original YAML structure
    3. Add archival metadata (date, reason, agent)
    4. Document recovery procedure

    Rationale: If audit was wrong, we can restore. Safer than deletion.
```

---

### Change #8: Add Integration Testing Tasks

**Add to Sprint 1:**
```yaml
task:
  id: roadmap-integrity-fixes-1-task-008
  title: Integration test - verify all fixes work together
  description: |
    After applying status fixes and progress recalculation, verify:
    - All tracks still loadable
    - No new errors introduced
    - Progress calculations are accurate
    - Status fields consistent
```

**Add to Sprint 2:**
```yaml
task:
  id: roadmap-integrity-fixes-2-task-006
  title: Integration test - verify cleanup didn't break anything
```

**Add to Sprint 3:**
```yaml
task:
  id: roadmap-integrity-fixes-3-task-007
  title: Integration test - verify all tracks loadable
```

**Add to Sprint 4:**
```yaml
task:
  id: roadmap-integrity-fixes-4-task-009
  title: Integration test - end-to-end validation
```

---

### Change #9: Split Task 013 into 3 Subtasks

**Current:** One massive task reviewing 19 tracks × 10 categories

**Recommended:**

```yaml
task:
  id: roadmap-integrity-fixes-0-task-013a
  title: Automated standards scanning
  description: |
    Use automated tools to find deprecated patterns:
    - rg "datetime\.utcnow" --type py
    - rg "/vibey|/claude" --type md
    - vermin --target=3.10 vibey/
    - markdown-link-check docs/**/*.md
  estimated_tokens: 3000

task:
  id: roadmap-integrity-fixes-0-task-013b
  title: Manual semantic review of flagged issues
  description: |
    Review findings from automated scan.
    Determine which issues are critical vs cosmetic.
  estimated_tokens: 5000

task:
  id: roadmap-integrity-fixes-0-task-013c
  title: Migration effort estimation and priority matrix
  description: |
    For each track with outdated references:
    - Estimate update effort (Small/Medium/Large/XL)
    - Assign priority (Critical/High/Medium/Low)
    - Create modernization roadmap
  estimated_tokens: 4000
```

---

### Change #10: Add Quantitative Acceptance Criteria

**Before (weak):**
```yaml
acceptance_criteria:
  - "Git history documented"
  - "Accurate completion percentage calculated"
```

**After (strong):**
```yaml
acceptance_criteria:
  - "Git history analysis examined minimum 50 commits OR explicitly stated <50 exist"
  - "Git commit table includes: SHA, date, author, message, files changed, LOC added/removed"
  - "Completion percentage calculation documented with formula and evidence"
  - "Status recommendation includes confidence score (high/medium/low)"
  - "Each 'completed' determination backed by 2+ evidence types (commit + working feature OR commit + test)"
  - "Report minimum 1000 lines OR justification why less"
```

**Implementation:** Update acceptance criteria for Tasks 001-010.

---

## Summary of Changes

### Critical (Must Do Before Sprint 0)

| Change | Impact | Effort |
|--------|--------|--------|
| Add Tasks 014-016 | Catches audit errors, verifies features work | 3 new tasks |
| Add approval gate | Prevents acting on flawed audit | Update sprint notes |
| Revise timeline | Enables thorough investigation | Change 4→7 days |
| Update dependencies | Ensures verification before synthesis | Update Task 012 |
| Remove unnecessary dep | Enables parallelization | Update Task 013 |

**Total Effort:** ~2 hours to update YAML files, well worth it for safety

### High Priority (Should Do)

| Change | Impact | Effort |
|--------|--------|--------|
| Add confidence scoring | Flags ambiguous cases | Update 10 task files |
| Change to archival | Prevents data loss | Update Sprint 2 |
| Add integration tests | Catches cascading failures | 4 new tasks |
| Split Task 013 | Better quality standards audit | Split 1 task → 3 |
| Add quantitative criteria | Objective quality bar | Update 10 task files |

**Total Effort:** ~4 hours to update YAML files and create new tasks

---

## Implementation Checklist

### Phase 1: Critical Changes (Do First)

- [ ] Create Task 014: Independent verification
- [ ] Create Task 015: Functional testing
- [ ] Create Task 016: Backup analysis
- [ ] Update Task 012 dependencies (add 014, 015, 016)
- [ ] Remove Task 013 dependency on Task 011
- [ ] Add approval gate to Sprint 0 notes
- [ ] Update Sprint 0 estimated_duration: 4→7 days
- [ ] Update Sprint 0 task count: 13→16

### Phase 2: High Priority Changes (Do Next)

- [ ] Update Tasks 001-010: Add confidence scoring to acceptance criteria
- [ ] Update Tasks 001-010: Add quantitative requirements
- [ ] Update Sprint 2: Change deletion to archival
- [ ] Split Task 013 into 013a, 013b, 013c
- [ ] Add Sprint 1 Task 008: Integration test
- [ ] Add Sprint 2 Task 006: Integration test
- [ ] Add Sprint 3 Task 007: Integration test
- [ ] Add Sprint 4 Task 009: Integration test

### Phase 3: Documentation Updates

- [ ] Update track.yaml deliverables to reflect new approach
- [ ] Update track.yaml timeline: 3 weeks → 3.5-4 weeks
- [ ] Update track.yaml quality gates to include verification
- [ ] Update track.yaml notes with new process

---

## Expected Outcomes

### With Critical Changes:
- ✅ 85% confidence in audit accuracy (vs 60% without)
- ✅ Data loss risk: HIGH → LOW
- ✅ False confidence risk: HIGH → MEDIUM
- ✅ Timeline more realistic (fewer surprises)

### With High Priority Changes:
- ✅ 90% confidence in audit accuracy
- ✅ Better quality deliverables
- ✅ Safer operations (archival vs deletion)
- ✅ Early detection of cascading issues

---

## Conclusion

These changes significantly improve the roadmap integrity fixes methodology without fundamentally redesigning the approach. The core 8-step forensic audit process is sound - we're just adding critical safeguards:

1. **Verification** (Tasks 014-016) - catch errors before they cause damage
2. **Approval gate** - human oversight before destructive changes
3. **Realistic timeline** - quality over speed
4. **Safety measures** - archival, confidence scoring, integration tests

**Total additional effort:** ~6 hours of YAML updates
**Risk reduction:** HIGH → LOW
**Confidence improvement:** 60% → 85-90%

**Recommendation:** Implement all critical changes before starting Sprint 0. The high-priority changes can be added incrementally but are strongly recommended.
