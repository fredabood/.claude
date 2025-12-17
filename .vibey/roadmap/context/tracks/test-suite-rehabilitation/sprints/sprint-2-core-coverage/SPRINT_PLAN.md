# Sprint 2: Core Test Coverage

## Overview
- **Track:** Test Suite Rehabilitation
- **Sprint ID:** 01KCMTMXX4RRDQWNM4SKBPD95N
- **Tasks:** 10
- **Focus:** Achieve comprehensive test coverage for core modules

## Success Criteria
- [ ] CLI command coverage: 100%
- [ ] Operations modules coverage: 100%
- [ ] Data models coverage: 100%
- [ ] Serialization coverage: 100%
- [ ] Adapter coverage: 100%
- [ ] Overall codebase coverage: ≥90%

---

## Task 1: Add CLI Command Tests for Roadmap Operations
**ID:** `01KCMGTARFDAJ93D2TZ55G0P0P`
**Priority:** High | **Complexity:** Complex | **Type:** Testing

### Problem
CLI commands in `commands.py` have insufficient test coverage (~40%).

### Files to Create/Modify
- `tests/cli/test_commands.py`
- `tests/cli/test_roadmap_commands.py`

### Commands to Test
```python
# High priority commands
- roadmap_status()
- roadmap_start()
- roadmap_complete()
- roadmap_update()
- roadmap_show()
- roadmap_list()
```

### Implementation Steps
1. Create CLI test fixtures:
   ```python
   from click.testing import CliRunner

   @pytest.fixture
   def cli_runner():
       return CliRunner()

   @pytest.fixture
   def mock_roadmap(tmp_path):
       """Create mock roadmap data for testing."""
       # Create .vibey/roadmap structure
       roadmap_dir = tmp_path / ".vibey" / "roadmap"
       roadmap_dir.mkdir(parents=True)
       # ... create test YAML files
   ```

2. Test each command:
   ```python
   def test_roadmap_status(cli_runner, mock_roadmap):
       result = cli_runner.invoke(cli, ["roadmap", "status"])
       assert result.exit_code == 0
       assert "Tracks:" in result.output

   def test_roadmap_start_task(cli_runner, mock_roadmap):
       result = cli_runner.invoke(cli, ["roadmap", "start", "01KC..."])
       assert result.exit_code == 0
       # Verify task status changed

   def test_roadmap_start_invalid_task(cli_runner):
       result = cli_runner.invoke(cli, ["roadmap", "start", "invalid"])
       assert result.exit_code != 0
       assert "not found" in result.output.lower()
   ```

3. Test error paths:
   - Invalid task IDs
   - Missing required arguments
   - Permission errors
   - Blocked tasks

### Acceptance Criteria
- [ ] All roadmap commands tested
- [ ] Happy path and error paths covered
- [ ] Coverage ≥100% for commands.py

---

## Task 2: Add Roadmap Update Operation Tests
**ID:** `01KCMGTEHAB7QW2XPQJ2ERSE45`
**Priority:** High | **Complexity:** Complex | **Type:** Testing

### Files to Test
- `vibey/operations/roadmap/update.py`

### Functions to Test
- `update_task_status()`
- `update_sprint_progress()`
- `batch_update_tasks()`
- Progress recomputation logic

### Implementation Steps
1. Create test fixtures with sample data
2. Test status transitions:
   ```python
   def test_update_task_status_valid_transition():
       # not_started -> in_progress
       result = update_task_status(task_id, "in_progress")
       assert result.status == "in_progress"

   def test_update_task_status_invalid_transition():
       # not_started -> completed (invalid)
       with pytest.raises(InvalidTransitionError):
           update_task_status(task_id, "completed")
   ```

3. Test progress computation:
   ```python
   def test_sprint_progress_updates_on_task_complete():
       # Complete task, verify sprint progress increases
       pass
   ```

### Acceptance Criteria
- [ ] All update functions tested
- [ ] Status transition validation tested
- [ ] Progress computation tested
- [ ] Coverage ≥100%

---

## Task 3: Add Transaction Rollback Tests
**ID:** `01KCMGTJAF0R2H9V4P8M30T3JJ`
**Priority:** High | **Complexity:** Medium | **Type:** Testing

### Problem
Need to verify database state is preserved on error.

### Implementation Steps
1. Test rollback on failure:
   ```python
   def test_rollback_on_update_failure(db_session):
       original_state = get_task(task_id)

       with pytest.raises(SomeError):
           with db_session.begin():
               update_task(task_id, invalid_data)

       current_state = get_task(task_id)
       assert current_state == original_state  # State unchanged
   ```

2. Test YAML + SQLite consistency:
   ```python
   def test_yaml_sqlite_consistency_on_error():
       # Verify YAML and SQLite stay in sync on failure
       pass
   ```

### Acceptance Criteria
- [ ] Rollback tested for all critical operations
- [ ] YAML/SQLite consistency verified
- [ ] No partial state changes on error

---

## Tasks 4-10: Additional Coverage Tasks

### Task 4: Add Database Integrity Tests
**ID:** `01KCMGTP4NSR73CWXNXD1FHTGG`
Test `vibey/roadmap/database/integrity_audit.py` - referential integrity, orphan detection.

### Task 5: Add Advanced Validator Tests
**ID:** `01KCMGTSYMCC7WR55G3PBR1PX3`
Test `vibey/operations/roadmap/advanced_validator.py` - complex validation rules.

### Task 6: Add Tests for Phase 2-3 New Modules
**ID:** `01KCMJNEVTK6BJPTEQG6XAT6T2`
Create: `test_session_manager.py`, `test_session_reconstruction.py`, `test_cli_introspector.py`, `test_mcp_introspector.py`

### Task 7: Add Tests for All Adapter Implementations
**ID:** `01KCMKBHB4KJCACYFZ074KBSG5`
Create test suite for 40 adapter files in `vibey/adapters/`.

### Task 8: Add Tests for Common/Config/Platform/Content Modules
**ID:** `01KCMKCA2J4Z1JENGWQNK6CAEB`
Test utility modules: `vibey/common/`, `vibey/config/`, `vibey/platform/`, `vibey/content/`

### Task 9: Add Tests for Data Models
**ID:** `01KCMKC212WX5QGRGA5HYYC5NQ`
Comprehensive tests for `vibey/roadmap/models/` - all model classes, validation, serialization.

### Task 10: Add Tests for Serialization Layer
**ID:** `01KCMKCHEXNPK9WMG0KP3A4E16`
Test `vibey/roadmap/serialization/` - yaml_loader, yaml_dumper, sql_loader, sql_dumper, round-trip.

---

## Sprint Completion Checklist
- [ ] All 10 tasks completed
- [ ] Core module coverage at 100%
- [ ] No untested public functions
- [ ] All tests passing in CI
