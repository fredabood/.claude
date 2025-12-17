# Sprint 1: Test Infrastructure Repair

## Overview
- **Track:** Test Suite Rehabilitation
- **Sprint ID:** 01KCMTMW1Y64VTVEZ7TEJG1R56
- **Tasks:** 5
- **Focus:** Restore broken tests to establish a working test baseline

## Success Criteria
- [ ] All 81 broken tests restored and passing
- [ ] Test infrastructure stable
- [ ] CI pipeline green
- [ ] No regressions in existing passing tests

---

## Task 1: Fix ORM/Repository Test Infrastructure
**ID:** `01KCMGRPB2J6V0QGG9X7JY4WK7`
**Priority:** High | **Complexity:** Complex | **Type:** Testing

### Problem
37 tests in `test_orm.py` and `test_repository.py` are broken due to SQLAlchemy fixture setup issues.

### Files to Fix
- `tests/roadmap/database/test_orm.py`
- `tests/roadmap/database/test_repository.py`
- `tests/conftest.py` (shared fixtures)

### Implementation Steps
1. Identify the fixture failure pattern:
   ```bash
   pytest tests/roadmap/database/test_orm.py -v 2>&1 | head -50
   pytest tests/roadmap/database/test_repository.py -v 2>&1 | head -50
   ```

2. Common SQLAlchemy fixture issues:
   - Session scope mismatch
   - Missing `engine` fixture
   - Database not initialized before tests
   - Foreign key constraints failing

3. Fix typical patterns:
   ```python
   # conftest.py
   @pytest.fixture(scope="function")
   def db_session(tmp_path):
       """Create a fresh database session for each test."""
       db_path = tmp_path / "test.db"
       engine = create_engine(f"sqlite:///{db_path}")
       Base.metadata.create_all(engine)
       Session = sessionmaker(bind=engine)
       session = Session()
       yield session
       session.close()
   ```

4. Run tests incrementally:
   ```bash
   pytest tests/roadmap/database/test_orm.py::test_first_test -v
   ```

### Acceptance Criteria
- [ ] All 37 ORM/Repository tests pass
- [ ] No session leaks between tests
- [ ] Tests run in isolation (order-independent)

---

## Task 2: Fix Standards Resolution Tests
**ID:** `01KCMGRT304F0JAKRDTCB4ZD3R`
**Priority:** High | **Complexity:** Medium | **Type:** Testing

### Problem
14 tests in `test_standards_resolution.py` are broken.

### Files to Fix
- `tests/roadmap/standards/test_standards_resolution.py`
- `vibey/roadmap/standards/resolver.py` (if interface changed)

### Implementation Steps
1. Identify failure pattern:
   ```bash
   pytest tests/roadmap/standards/test_standards_resolution.py -v
   ```

2. Common issues:
   - API changes in resolver not reflected in tests
   - Missing test fixtures for ULID-based IDs
   - Path structure changes (hierarchical → flat)

3. Update tests to match current API:
   ```python
   # Example: Update to ULID format
   def test_resolve_for_task():
       task_id = "01KC2D0JK7READW9KAK1HBX4B8"  # ULID format
       # ... rest of test
   ```

### Acceptance Criteria
- [ ] All 14 standards resolution tests pass
- [ ] Tests use ULID format where applicable
- [ ] Tests reflect current resolver API

---

## Task 3: Fix Performance Tests
**ID:** `01KCMGRXVWGRZV4WTVEJ4VT7W6`
**Priority:** Medium | **Complexity:** Medium | **Type:** Testing

### Problem
10 tests in `test_performance.py` are broken.

### Files to Fix
- `tests/test_performance.py` or `tests/performance/test_performance.py`

### Implementation Steps
1. Locate and run tests:
   ```bash
   find tests -name "*performance*"
   pytest tests/test_performance.py -v 2>&1 | head -50
   ```

2. Common performance test issues:
   - Benchmark fixtures outdated
   - Database size assumptions wrong
   - Timing thresholds too strict

3. Update benchmark expectations:
   ```python
   def test_bulk_task_creation():
       # Update to realistic thresholds
       assert elapsed_time < 5.0  # seconds, was 1.0
   ```

### Acceptance Criteria
- [ ] All 10 performance tests pass
- [ ] Thresholds are realistic for current codebase
- [ ] No flaky tests due to timing

---

## Task 4: Fix Validators Tests
**ID:** `01KCMGS1M99FRKAR6NNTXFZCK7`
**Priority:** Medium | **Complexity:** Medium | **Type:** Testing

### Problem
12 tests in `test_validators.py` are broken.

### Files to Fix
- `tests/roadmap/test_validators.py` or similar
- `vibey/roadmap/validators.py` (if interface changed)

### Implementation Steps
1. Identify failures:
   ```bash
   find tests -name "*validator*"
   pytest tests/roadmap/test_validators.py -v
   ```

2. Common validator test issues:
   - Validation rules changed
   - New required fields added
   - Status enum values updated

3. Update tests to match current validation:
   ```python
   def test_task_validation():
       # Update expected validation errors
       task = Task(status="invalid_status")
       with pytest.raises(ValidationError, match="Invalid status"):
           validate_task(task)
   ```

### Acceptance Criteria
- [ ] All 12 validator tests pass
- [ ] Tests cover current validation rules
- [ ] Edge cases properly tested

---

## Task 5: Fix Git Hooks Tests
**ID:** `01KCMGS5ES6ZAG0TJR717ET4R3`
**Priority:** Medium | **Complexity:** Medium | **Type:** Testing

### Problem
8 tests in `test_git_hooks.py` are broken.

### Files to Fix
- `tests/operations/git/test_git_hooks.py`
- `vibey/operations/git/hooks/` (implementation)

### Implementation Steps
1. Identify failures:
   ```bash
   pytest tests/operations/git/test_git_hooks.py -v
   ```

2. Common git hook test issues:
   - Hook scripts not found
   - Git repo fixtures missing
   - Permission/execution issues in CI

3. Create proper git fixtures:
   ```python
   @pytest.fixture
   def git_repo(tmp_path):
       """Create a temporary git repository."""
       repo_path = tmp_path / "repo"
       repo_path.mkdir()
       subprocess.run(["git", "init"], cwd=repo_path, check=True)
       subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path)
       subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path)
       return repo_path
   ```

### Acceptance Criteria
- [ ] All 8 git hooks tests pass
- [ ] Tests work in CI environment
- [ ] Tests properly clean up git repos

---

## Sprint Completion Checklist
- [ ] All 81 broken tests restored (37 + 14 + 10 + 12 + 8)
- [ ] `pytest tests/` runs green
- [ ] No new test failures introduced
- [ ] CI pipeline passing
- [ ] Test coverage maintained or improved
