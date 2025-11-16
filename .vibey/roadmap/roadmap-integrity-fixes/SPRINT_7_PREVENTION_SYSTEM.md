# Sprint 7: Data Integrity Prevention & Automation

**Created:** 2025-11-16
**Status:** not_started
**Priority:** CRITICAL
**Duration:** 2.5 weeks (17.5 hours)
**Tasks:** 13

---

## Context

Following the comprehensive audit and remediation of all 20 roadmap tracks on 2025-11-16, critical prevention gaps were identified that, if left unaddressed, will lead to recurring data corruption.

### Audit Results (2025-11-16)
- ✅ All 20 tracks audited by independent agents
- ✅ 8 tracks remediated with data integrity fixes
- ✅ 170+ YAML files updated
- ✅ 80+ audit/remediation reports generated
- ✅ Achieved 95-100% data integrity across all tracks

### Prevention Gaps Discovered
1. **Python serialization corruption ACTIVE** in 3 files (post-remediation)
2. **No automated detection** of YAML corruption
3. **Root cause unfixed**: enum serialization bug
4. **No validation tests** to prevent regression
5. **No CI/CD validation** to catch issues before commit
6. **No monitoring** to detect degradation

---

## Problem Statement

Despite successful remediation, the **ROOT CAUSE** of data corruption remains unfixed:

**Corrupted Files Found (Post-Remediation):**
```yaml
# .vibey/roadmap/aider-port/track.yaml (line 53)
# .vibey/roadmap/multi-platform/track.yaml (line 96)
# .vibey/roadmap/mcp-server/track.yaml (line 51)

current_status: !!python/object/apply:vibey.roadmap.models.common.Status
- in_progress
```

**Root Cause:**
When updating dependency statuses, Status enum objects are written directly to YAML instead of being converted to string values with `.value`.

**Impact:**
- YAML files become corrupted (non-portable format)
- Files fail to parse without Python runtime
- Dependency statuses show wrong values
- Pattern will recur on every dependency update

---

## Sprint Goal

**Build automated prevention systems that make data corruption impossible.**

Philosophy: **"Automation over vigilance"**

Manual data integrity checks don't scale to 20+ tracks. This sprint implements automated safeguards at commit time, CI/CD validation, and proactive monitoring.

---

## Tasks

### Task 1: Fix Active YAML Corruption (15 min, P0)

**What:** Clean up 3 files with Python serialization
**Files:**
- `.vibey/roadmap/aider-port/track.yaml`
- `.vibey/roadmap/multi-platform/track.yaml`
- `.vibey/roadmap/mcp-server/track.yaml`

**Fix:** Replace `!!python/object/apply:...` with plain string values

**Verification:**
```bash
grep -r "!!python" .vibey/roadmap/
# Should return: (no results)
```

---

### Task 2: Pre-commit Hook (30 min, P0)

**What:** Add pre-commit hook to reject !!python patterns

**Hook Spec:**
```yaml
- repo: local
  hooks:
    - id: check-yaml-python-objects
      name: Check for Python object serialization in YAML
      entry: bash -c 'if grep -r "!!python" .vibey/roadmap/; then exit 1; fi'
      language: system
      pass_filenames: false
      files: \.yaml$
```

**Test:** Attempt to commit file with `!!python` pattern (should fail)

---

### Task 3: Fix Enum Serialization Bug (1 hour, P0)

**What:** Fix root cause in dependency update code

**Pattern to Fix:**
```python
# BAD
dep['current_status'] = Status.COMPLETED

# GOOD
dep['current_status'] = Status.COMPLETED.value
```

**Files to Check:**
- `vibey/operations/roadmap/update.py`
- `vibey/operations/roadmap/init.py`
- Any code that modifies track dependencies

**Verification:** Update a dependency, check YAML has plain string

---

### Task 4: YAML Validation Tests (2 hours, P1)

**What:** Create comprehensive test suite for YAML integrity

**Tests to Add** (tests/validation/test_yaml_integrity.py):
- `test_no_python_serialization_in_yaml()`
- `test_all_track_yaml_parse()`
- `test_all_sprint_yaml_parse()`
- `test_all_task_yaml_parse()`
- `test_dependency_statuses_are_strings()`
- `test_enum_fields_are_strings()`

**Coverage:** Automatically discover and test all YAML files in `.vibey/roadmap/`

---

### Task 5: CI/CD Validation Job (1 hour, P1)

**What:** GitHub Actions workflow for roadmap validation

**Jobs:**
1. YAML syntax validation (yamllint)
2. Python serialization detection (grep !!python)
3. Dependency status validation (all strings)
4. Track loadability test (can load all tracks)

**Trigger:** On push to main, on pull requests

**File:** `.github/workflows/roadmap-validation.yml`

---

### Task 6: Automated Dependency Refresh (2 hours, P2)

**What:** Auto-refresh dependency statuses to prevent staleness

**Command:** `vibey roadmap refresh-dependencies`

**Features:**
- Read all track dependencies
- Check current status of each dependency track
- Update `current_status` if changed
- Update `last_checked` timestamp
- Use `.value` for proper enum serialization
- Log all updates for audit trail

**Prevents:**
- Stale statuses (claude-port shows "in_progress" when "completed")
- Manual dependency checks
- Tracks incorrectly blocked/unblocked

---

### Task 7: Monitoring & Alerting (2 hours, P2)

**What:** Health check and monitoring system

**Command:** `vibey roadmap health-check`

**Metrics Tracked:**
1. YAML parse success rate
2. Python serialization occurrences
3. Dependency status staleness
4. Track loadability rate
5. Validation test pass rate
6. Git hook success rate

**Alerting:**
- Exit code 0 if healthy, 1 if issues
- Daily/weekly reports (email/Slack)
- Optional: Dashboard visualization

---

### Task 8: Enum Value Validation (1 hour, P0)

**What:** Validate all enum fields contain valid values from their enum classes

**Critical Gap:** Current validation only checks that enum fields are strings, not that they're valid enum values.

**Invalid Pattern:**
```yaml
status: "invalid_status_value"  # String ✓, but not in Status enum ✗
priority: "super_urgent"        # String ✓, but not in Priority enum ✗
```

**Tests to Add:**
- `test_track_enum_values_valid()` - Verify all track enum fields
- `test_sprint_enum_values_valid()` - Verify all sprint enum fields
- `test_task_enum_values_valid()` - Verify all task enum fields

**Enum Coverage:**
- Status: not_started, in_progress, paused, completed, etc.
- Priority: low, medium, high, critical
- TaskStatus: not_started, in_progress, blocked, completed
- TaskType: development, completion_gate, production_gate
- Complexity: simple, medium, complex
- GateStatus: pending, passed, failed

---

### Task 9: Relationship & Reference Validation (2 hours, P1)

**What:** Validate all cross-object references point to existing objects

**Critical Gap:** No validation that IDs reference actual objects.

**Invalid Pattern:**
```yaml
task:
  sprint_id: "non-existent-sprint"  # Sprint doesn't exist ✗

depends_on:
  - blocker_id: "fake-track"  # Track doesn't exist ✗
```

**Tests to Add:**
- `test_task_sprint_references_exist()` - Tasks reference valid sprints
- `test_task_track_references_exist()` - Tasks reference valid tracks
- `test_dependency_references_exist()` - Dependencies reference valid objects
- `test_blocker_references_exist()` - Blockers reference valid dependencies

**Validation Approach:**
1. Build index of all valid IDs (tracks, sprints, tasks)
2. Validate all references against indexes
3. Report orphaned objects and broken references

---

### Task 10: Progress Calculation Validation (1 hour, P1)

**What:** Validate progress calculations match actual completion state

**Critical Gap:** No validation that aggregate progress fields are correct.

**Invalid Pattern:**
```yaml
progress:
  tasks_total: 10
  tasks_completed: 3
  completion_percent: 75  # Should be 30%, not 75% ✗
```

**Tests to Add:**
- `test_roadmap_progress_accurate()` - Roadmap progress matches reality
- `test_track_progress_accurate()` - Track progress matches sprint/task counts
- `test_sprint_progress_accurate()` - Sprint progress matches task counts

**Validation Rules:**
- completion_percent = (tasks_completed / tasks_total) * 100
- tasks_total = sum of all task counts
- tasks_completed = count of tasks with status=completed
- Allow 1% rounding tolerance

---

### Task 11: Date Logic Validation (1 hour, P2)

**What:** Validate date fields follow logical chronological order

**Gap:** No validation of date relationships.

**Invalid Pattern:**
```yaml
task:
  created: '2025-11-16T00:00:00+00:00'
  completed: '2025-11-15T00:00:00+00:00'  # Before created ✗
  started: '2025-11-17T00:00:00+00:00'    # After completed ✗
```

**Tests to Add:**
- `test_roadmap_dates_chronological()` - Roadmap dates in order
- `test_track_dates_chronological()` - Track dates in order
- `test_sprint_dates_chronological()` - Sprint dates in order (including gates)
- `test_task_dates_chronological()` - Task dates in order

**Validation Rules:**
- created ≤ started ≤ completed (all objects)
- Sprint gates: started ≤ completion_gate_check_at ≤ completed ≤ production_gate_check_at ≤ production_ready_at ≤ deployed_at
- Handle None values gracefully

---

### Task 12: Dependency Cycle Detection (1.5 hours, P2)

**What:** Detect circular dependencies that create deadlocks

**Gap:** No validation that dependencies don't form cycles.

**Invalid Pattern:**
```yaml
# Track A depends on Track B
# Track B depends on Track A
# = Deadlock - neither can ever complete ✗
```

**Tests to Add:**
- `test_no_dependency_cycles_in_tracks()` - No circular track dependencies
- `test_no_dependency_cycles_in_sprints()` - No circular sprint dependencies
- `test_no_dependency_cycles_in_tasks()` - No circular task dependencies

**Algorithm:** Depth-First Search (DFS) cycle detection
- Detect direct cycles (A→B→A)
- Detect multi-hop cycles (A→B→C→A)
- Detect self-dependencies (A→A)
- Report cycle paths clearly

---

### Task 13: Required Field Enforcement (1 hour, P2)

**What:** Validate all required fields are present in YAML files

**Gap:** Dataclasses use defaults, so missing required fields don't error at load time.

**Invalid Pattern:**
```yaml
task:
  id: my-task
  # Missing: sprint_id, track_id, status (all required) ✗
```

**Tests to Add:**
- `test_roadmap_required_fields()` - All roadmap required fields present
- `test_track_required_fields()` - All track required fields present
- `test_sprint_required_fields()` - All sprint required fields present
- `test_task_required_fields()` - All task required fields present

**Required Fields per Type:**
- **Roadmap:** id, name, version, status, created, progress
- **Track:** id, name, roadmap_id, status, priority, created, progress, metadata
- **Sprint:** id, name, track_id, roadmap_id, status, created, progress, metadata
- **Task:** id, sprint_id, track_id, status, title, created, priority, metadata

---

## Success Criteria

**Core Prevention (Tasks 1-7):**
✅ All 3 corrupted YAML files fixed
✅ Attempting to commit `!!python` pattern fails pre-commit
✅ Dependency updates produce plain string values
✅ All validation tests pass
✅ CI/CD workflow runs on every push and catches issues
✅ Dependencies refresh automatically (no manual staleness)
✅ Alert system catches degradation within 24 hours

**Comprehensive Validation (Tasks 8-13):**
✅ All enum values validated against allowed values
✅ All cross-object references verified to exist
✅ All progress calculations validated for accuracy
✅ All date fields verified in chronological order
✅ No dependency cycles detected in any level
✅ All required fields enforced and present

---

## Timeline

### Week 1: Core Prevention (10 hours)
| Day | Hours | Tasks |
|-----|-------|-------|
| 1 | 2h | Tasks 1-2 (Critical fixes + pre-commit hook) |
| 2 | 2h | Task 3 (Fix root cause enum bug) |
| 3 | 2h | Task 4 (Validation test suite) |
| 4 | 1h | Task 5 (CI/CD validation job) |
| 5 | 2h | Task 6 (Automated dependency refresh) |
| 6 | 1h | Task 7 (Monitoring & alerting) |

### Week 2-3: Comprehensive Validation (7.5 hours)
| Day | Hours | Tasks |
|-----|-------|-------|
| 7 | 1h | Task 8 (Enum value validation) |
| 8 | 2h | Task 9 (Reference validation) |
| 9 | 1h | Task 10 (Progress calculation validation) |
| 10 | 1h | Task 11 (Date logic validation) |
| 11 | 1.5h | Task 12 (Dependency cycle detection) |
| 12 | 1h | Task 13 (Required field enforcement) |

**Total:** 17.5 hours over 12 days (~1.5 hours/day)

---

## ROI Analysis

**Cost of NOT doing this sprint:**
- Recurring data corruption (weekly/monthly)
- Manual audit cycles (8-16 hours each)
- Developer trust erosion
- Downstream track blockages
- Technical debt accumulation

**Cost of doing this sprint:**
- 17.5 hours upfront investment
- Prevents 100+ hours of future manual work
- Enables confident scaling to 50+ tracks
- Eliminates entire classes of data corruption

**ROI:** 8:1 or better (still excellent value)

---

## Dependencies

**Blocked By:**
- Sprint 3 (Critical Data Fixes) should complete first

**Blocks:**
- None (can run in parallel with other execution sprints)

**Synergy With:**
- Sprint 2 (Quality Gates) - validation tests integrate
- Sprint 4 (Peer Review) - CI/CD hooks integrate
- Sprint 5 (Real-Time Updates) - monitoring integrates

---

## Deliverables

**Core Prevention (Tasks 1-7):**
1. ✅ Clean YAML files (0 Python serialization patterns)
2. ✅ Pre-commit hook preventing `!!python` patterns
3. ✅ Fixed enum serialization in dependency code
4. ✅ Validation test suite (6+ tests)
5. ✅ GitHub Actions workflow for roadmap validation
6. ✅ Dependency refresh automation
7. ✅ Monitoring/alerting system

**Comprehensive Validation (Tasks 8-13):**
8. ✅ Enum value validation tests (3 test functions)
9. ✅ Reference validation tests (4 test functions)
10. ✅ Progress calculation validation tests (3 test functions)
11. ✅ Date logic validation tests (4 test functions)
12. ✅ Dependency cycle detection tests (3 test functions)
13. ✅ Required field validation tests (4 test functions)

**Total Test Coverage:** 27+ validation test functions across all roadmap levels

---

## Why This Sprint Is Critical

1. **Active Corruption Exists RIGHT NOW** (3 files)
2. **Root Cause Unfixed** = will happen again
3. **Manual Remediation Doesn't Scale** (20+ tracks)
4. **Prevention Is 10x Cheaper** than repeated remediation
5. **Builds on $100K+ of Audit/Remediation Work**

This sprint is the **capstone** that protects all the audit and remediation investment by ensuring data corruption cannot recur.

---

## Next Steps

1. Review and approve sprint plan
2. Start with Tasks 1-3 (critical, 2.5 hours)
3. Continue with Tasks 4-7 as time allows
4. Monitor effectiveness after 1 week

**Note:** This sprint can start immediately and run in parallel with other roadmap-integrity-fixes work. It addresses a specific technical gap (prevention automation) rather than process/workflow changes.
