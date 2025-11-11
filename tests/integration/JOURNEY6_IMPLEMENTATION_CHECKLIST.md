# Journey 6 Implementation Checklist

## Pre-Implementation Verification

### 1. Review Test File
- [ ] Read `test_journey6_steps_v2.5.0.py` completely
- [ ] Understand all 11 test cases
- [ ] Review critical fix in test_04
- [ ] Understand breaking changes

### 2. Verify Documentation
- [ ] Check `docs/VIBEY_USER_JOURNEYS.md` Journey 6 matches tests
- [ ] Verify `docs/TEST_COVERAGE_GAP_ANALYSIS.md` lines 73-119
- [ ] Confirm no references to old `toolkit.toml` behavior
- [ ] Verify all commands use `vibey deploy run` syntax

---

## Test Implementation

### Phase 1: Setup (10 minutes)

- [ ] Create Python virtual environment
  ```bash
  cd /Users/fredabood/Repositories/vibey
  python3 -m venv .venv
  source .venv/bin/activate
  ```

- [ ] Install dependencies
  ```bash
  pip install pytest pyyaml
  ```

- [ ] Verify test utilities exist
  ```bash
  ls tests/utils/repo_builder.py
  ls tests/utils/state_validator.py
  ls tests/utils/metrics_collector.py
  ```

### Phase 2: Critical Test (test_04) - 15 minutes

**MOST IMPORTANT TEST - Run First**

- [ ] Run test_04 individually
  ```bash
  pytest tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_04_goose_adapter_creates_goosehints -v
  ```

- [ ] Verify test validates:
  - [ ] `.goosehints` exists in project root
  - [ ] `.goose/toolkit.toml` does NOT exist
  - [ ] Environment variable format (KEY=VALUE)
  - [ ] Required variables present (PROJECT_TYPE, TECH_STACK, etc.)

- [ ] If test FAILS:
  - [ ] Check if Goose adapter creates wrong file
  - [ ] Check if file is in wrong location
  - [ ] Check if file has wrong format
  - [ ] **FIX ADAPTER BEFORE CONTINUING**

### Phase 3: Priority 1 Tests - 30 minutes

Run remaining P1 tests:

- [ ] Test 01: deploy list command
  ```bash
  pytest tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_01_deploy_list_command -v
  ```

- [ ] Test 02: deploy run to Claude Code
  ```bash
  pytest tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_02_deploy_run_to_claude_code -v
  ```

- [ ] Test 03: deploy run to Goose
  ```bash
  pytest tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_03_deploy_run_to_goose -v
  ```

- [ ] Test 05: --platform all flag
  ```bash
  pytest tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_05_deploy_run_platform_all -v
  ```

- [ ] Test 06: --clean flag
  ```bash
  pytest tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_06_deploy_run_with_clean_flag -v
  ```

### Phase 4: Priority 2 Tests - 20 minutes

- [ ] Test 07: Goose recipes not YAML
- [ ] Test 08: Redeploy after config change
- [ ] Test 09: Platform detection with multiple
- [ ] Test 10: Cursor experimental

```bash
pytest tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_07_goose_recipes_not_yaml -v
pytest tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_08_redeploy_after_config_change -v
pytest tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_09_platform_detection_with_multiple_present -v
pytest tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_10_deploy_run_to_cursor_experimental -v
```

### Phase 5: Full Suite - 10 minutes

- [ ] Run all Journey 6 tests
  ```bash
  pytest tests/integration/test_journey6_steps_v2.5.0.py -v
  ```

- [ ] Verify all 11 tests pass
- [ ] Check for any warnings or deprecations
- [ ] Review test output for clarity

---

## Mock Adjustments (If Needed)

If tests fail due to mocking issues:

### Issue: subprocess.run not mocked correctly

**Fix:**
```python
# In test file, update MockCompletedProcess if needed
class MockCompletedProcess:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
```

### Issue: vibey command not found

**Fix:** Tests use mocks, should not call actual CLI. If tests try to call real CLI:
```python
# Ensure mock_vibey_command fixture is used in test signature
def test_01_deploy_list_command(self, temp_dir, mock_vibey_command):
    # Test code...
```

### Issue: File paths incorrect

**Fix:** Verify temp_dir fixture is used:
```python
# All file operations should use repo.path
(repo.path / ".goosehints").write_text("...")  # ✅ CORRECT
(Path(".goosehints")).write_text("...")         # ❌ WRONG
```

---

## Expected Test Results

### Success Output

```
tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_01_deploy_list_command PASSED
tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_02_deploy_run_to_claude_code PASSED
tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_03_deploy_run_to_goose PASSED
tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_04_goose_adapter_creates_goosehints PASSED  ← CRITICAL
tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_05_deploy_run_platform_all PASSED
tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_06_deploy_run_with_clean_flag PASSED
tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_07_goose_recipes_not_yaml PASSED
tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_08_redeploy_after_config_change PASSED
tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_09_platform_detection_with_multiple_present PASSED
tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_10_deploy_run_to_cursor_experimental PASSED
tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_11_complete_multi_platform_workflow PASSED

====================================== 11 passed in 2.34s =======================================
```

### Failure Output (Example)

```
FAILED tests/integration/test_journey6_steps_v2.5.0.py::TestJourney6MultiPlatformDeploymentV2::test_04_goose_adapter_creates_goosehints
AssertionError: Goose adapter MUST create .goosehints file in project root
```

**Action if this fails:** The Goose adapter is creating the wrong file. Fix the adapter implementation before proceeding.

---

## Post-Implementation

### 1. Validate Implementation

- [ ] All 11 tests pass
- [ ] No skipped tests
- [ ] No warnings
- [ ] Test output is clear and informative

### 2. Update Documentation

- [ ] Mark `test_journey6_multi_platform.py` as deprecated
- [ ] Update CI/CD to use new test file
- [ ] Update test plan documentation
- [ ] Add entry to CHANGELOG.md

### 3. Code Review

- [ ] Review test code for clarity
- [ ] Review test comments and docstrings
- [ ] Verify test names are descriptive
- [ ] Ensure assertions have helpful messages

### 4. Integration Testing

- [ ] Run full test suite
  ```bash
  pytest tests/ -v
  ```

- [ ] Verify no regressions in other journeys
- [ ] Check test coverage report
- [ ] Validate test performance (should run quickly)

---

## Common Issues & Solutions

### Issue 1: Fixtures Not Found

**Error:**
```
fixture 'clean_platform_dirs' not found
```

**Solution:**
Fixtures are defined in the test file. Ensure the test file is using the correct class structure:
```python
@pytest.mark.integration
class TestJourney6MultiPlatformDeploymentV2:
    def test_01_deploy_list_command(self, temp_dir, mock_vibey_command):
        # temp_dir comes from conftest.py
        # mock_vibey_command is defined in this file
```

### Issue 2: RepoBuilder Not Found

**Error:**
```
ImportError: cannot import name 'RepoBuilder' from 'tests.utils'
```

**Solution:**
Verify test utils exist:
```bash
ls tests/utils/__init__.py
ls tests/utils/repo_builder.py
```

If missing, check imports:
```python
from tests.utils import RepoBuilder  # May need adjustment based on your setup
```

### Issue 3: Mock Not Working

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'vibey'
```

**Solution:**
Test is trying to call real vibey command. Ensure `mock_vibey_command` fixture is in test signature:
```python
def test_01_deploy_list_command(self, temp_dir, mock_vibey_command):
    #                                              ^^^^^^^^^^^^^^^^^^^
```

### Issue 4: Temp Directory Cleanup

**Error:**
Tests interfere with each other.

**Solution:**
Use `clean_platform_dirs` fixture:
```python
def test_XX_something(self, temp_dir, clean_platform_dirs):
    #                                   ^^^^^^^^^^^^^^^^^^^^
```

---

## Rollback Plan

If tests reveal critical issues with v2.5.0:

1. **DO NOT merge tests yet**
2. **Document issues found** in JOURNEY6_TEST_ISSUES.md
3. **Fix adapter/CLI implementation** first
4. **Re-run tests** after fixes
5. **Only merge tests** when all pass

### Critical Issues That Block Merge

- [ ] Goose adapter creates wrong file (toolkit.toml instead of .goosehints)
- [ ] CLI commands don't match documented syntax
- [ ] Platform detection broken
- [ ] --platform all flag doesn't work

---

## Success Criteria

All boxes checked = Ready to merge:

- [ ] ✅ All 11 tests pass
- [ ] ✅ Test 04 (Goose adapter) passes (CRITICAL)
- [ ] ✅ No regressions in other test suites
- [ ] ✅ Documentation matches test behavior
- [ ] ✅ Code review complete
- [ ] ✅ CI/CD pipeline updated
- [ ] ✅ Old test file deprecated

---

## Time Estimates

| Phase | Estimated Time | Notes |
|-------|----------------|-------|
| Setup | 10 minutes | Virtual env + deps |
| Test 04 (Critical) | 15 minutes | Run first, fix if fails |
| P1 Tests (5) | 30 minutes | Core functionality |
| P2 Tests (4) | 20 minutes | Edge cases |
| Full Suite | 10 minutes | Final validation |
| **Total** | **85 minutes** | ~1.5 hours |

---

## Contact & Questions

If you encounter issues during implementation:

1. Check test file comments and docstrings
2. Review JOURNEY6_TEST_UPDATE_SUMMARY.md
3. Check docs/TEST_COVERAGE_GAP_ANALYSIS.md
4. Review Journey 6 documentation (docs/VIBEY_USER_JOURNEYS.md)

---

**Checklist Version:** 1.0
**Last Updated:** 2025-11-11
**Status:** Ready for Use
