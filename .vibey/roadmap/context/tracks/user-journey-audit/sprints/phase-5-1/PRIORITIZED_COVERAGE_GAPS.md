# Prioritized Coverage Gaps

**Sprint:** Phase 5.1 - Test Coverage Implementation
**Task:** Prioritize coverage gaps
**Generated:** 2025-12-14

---

## Executive Summary

Based on the Phase 1.4 Coverage Gap Analysis, this document prioritizes test coverage work based on:
1. **Code Criticality** - How important is this code to core functionality?
2. **Bug Risk** - How likely is untested code to have bugs?
3. **Complexity** - How complex is the code (effort to test)?

**Current State:**
- Line Coverage: 28.5%
- Branch Coverage: 17.8%
- Failing Tests: 162
- Target: 80% line coverage

---

## Priority 1: Fix Broken Test Infrastructure (CRITICAL)

**Rationale:** Before writing new tests, fix broken tests that are obscuring actual coverage.

### 1.1 ORM/Repository Test Infrastructure
- **Files:** `tests/roadmap/models/ticket/test_orm.py`, `test_repository.py`
- **Error Count:** 37 tests
- **Effort:** 1 day
- **Impact:** Restores 37 tests, reveals true coverage
- **Root Cause:** SQLAlchemy test fixture setup broken

### 1.2 Standards Resolution Tests
- **File:** `tests/integration/test_standards_resolution.py`
- **Failure Count:** 14 tests
- **Effort:** 0.5 days
- **Impact:** Restores integration test coverage

### 1.3 Performance Tests
- **File:** `tests/operations/roadmap/test_performance.py`
- **Failure Count:** 10 tests
- **Effort:** 0.5 days
- **Impact:** Restores performance regression detection

### 1.4 Validators Tests
- **File:** `tests/unit/test_validators.py`
- **Failure Count:** 12 tests
- **Effort:** 1 day
- **Impact:** Restores input validation coverage

### 1.5 Git Hooks Tests
- **File:** `tests/test_git_hooks.py`
- **Failure Count:** 8 tests
- **Effort:** 0.5 days
- **Impact:** Restores git integration coverage

**Priority 1 Total:** 3.5 days, +81 tests restored

---

## Priority 2: Critical Path Coverage (HIGH)

**Rationale:** Test the most important user-facing functionality first.

### 2.1 CLI Commands (`vibey/cli/commands.py`)
- **Lines:** 1,741
- **Current Coverage:** 23.7%
- **Bug Risk:** HIGH (user-facing, many edge cases)
- **Effort:** 3 days
- **Target:** 60% coverage (+15% overall)
- **Focus Areas:**
  - `roadmap_update` function
  - `roadmap_complete` function
  - Error handling paths
  - Input validation

### 2.2 Roadmap Update Operations (`vibey/operations/roadmap/update.py`)
- **Lines:** 794
- **Current Coverage:** 7.4%
- **Bug Risk:** CRITICAL (core business logic)
- **Effort:** 2 days
- **Target:** 50% coverage (+5% overall)
- **Focus Areas:**
  - `update_task_status`
  - `update_sprint_progress`
  - `batch_update_tasks`
  - Rollback on failure
  - Concurrent update handling

### 2.3 Transaction Rollback Tests
- **Currently:** No tests for error recovery
- **Bug Risk:** CRITICAL (data corruption risk)
- **Effort:** 1 day
- **Focus:** Error during update -> Rollback -> State intact

**Priority 2 Total:** 6 days, +20% coverage expected

---

## Priority 3: High-Impact Module Coverage (MEDIUM-HIGH)

### 3.1 Database Integrity (`vibey/roadmap/database/integrity_audit.py`)
- **Lines:** 369
- **Current Coverage:** 0%
- **Bug Risk:** HIGH
- **Effort:** 1.5 days

### 3.2 Advanced Validator (`vibey/operations/roadmap/advanced_validator.py`)
- **Lines:** 317
- **Current Coverage:** 0%
- **Bug Risk:** HIGH
- **Effort:** 1 day

### 3.3 File Classifier (`vibey/operations/audit/file_classifier.py`)
- **Lines:** 438
- **Current Coverage:** 0%
- **Bug Risk:** MEDIUM
- **Effort:** 1 day

### 3.4 Directory Migration (`vibey/roadmap/serialization/directory_migration_v2.py`)
- **Lines:** 363
- **Current Coverage:** 0%
- **Bug Risk:** HIGH (data migration)
- **Effort:** 1.5 days

**Priority 3 Total:** 5 days, +8% coverage expected

---

## Priority 4: Branch Coverage Focus (MEDIUM)

### Focus Areas for Branch Coverage
1. **Error Handling Paths**
   - Exception handling in CLI
   - Validation failure paths
   - File I/O error handling

2. **Conditional Logic**
   - Status transition guards
   - Permission checks
   - Feature flags

3. **Edge Cases**
   - Empty roadmap handling
   - Malformed input handling
   - Concurrent access scenarios

**Effort:** 5 days
**Target:** Branch coverage from 17.8% to 40%

---

## Priority 5: Code Cleanup (LOWER)

### Standalone Scripts to Consolidate/Remove
These scripts have 0% coverage and are candidates for consolidation:

| Script | Lines | Action |
|--------|-------|--------|
| `vibey/cli/roadmap-update.py` | 630 | Consolidate into CLI |
| `vibey/cli/manage-project-context.py` | 307 | Consolidate into CLI |
| `vibey/cli/roadmap-summarize.py` | 274 | Consolidate into CLI |
| 20+ other standalone scripts | ~3000 | Evaluate necessity |

**Effort:** 2 days
**Impact:** Reduces untested code by ~4000 lines

---

## Recommended Execution Order

### Week 1: Fix Infrastructure + Critical Paths
1. Fix ORM test infrastructure (Day 1)
2. Fix remaining broken tests (Day 2)
3. Start CLI command tests (Days 3-5)

### Week 2: Core Business Logic
1. Roadmap update operation tests (Days 1-2)
2. Transaction rollback tests (Day 3)
3. Database integrity tests (Days 4-5)

### Week 3: Module Coverage
1. Advanced validator tests (Day 1)
2. File classifier tests (Day 2)
3. Migration tests (Days 3-4)
4. Branch coverage focus (Day 5)

### Week 4: Polish + Documentation
1. Branch coverage completion (Days 1-3)
2. Code cleanup (Days 4-5)
3. Documentation updates

---

## Success Metrics

| Metric | Current | Week 1 | Week 2 | Week 3 | Week 4 |
|--------|---------|--------|--------|--------|--------|
| Line Coverage | 28.5% | 35% | 50% | 65% | 80% |
| Branch Coverage | 17.8% | 22% | 30% | 38% | 45% |
| Failing Tests | 162 | 80 | 30 | 10 | 0 |
| Passing Tests | 2492 | 2575 | 2650 | 2700 | 2750 |

---

## Risk Factors

1. **ORM Infrastructure Complexity** - May take longer than estimated if issues are deep
2. **Flaky Tests** - Some tests may have intermittent failures
3. **Integration Test Dependencies** - May need external resources (DB, git repos)
4. **Coverage Measurement Accuracy** - Ensure coverage tool is correctly configured

---

## Next Steps

1. Begin with Priority 1.1: Fix ORM test infrastructure
2. Track progress daily in sprint status
3. Adjust estimates as work progresses
4. Document test patterns for consistency
