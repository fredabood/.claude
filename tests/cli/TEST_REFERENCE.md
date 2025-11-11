# Journey 7 CLI Tests - Quick Reference

**Test File:** `test_roadmap_cli_comprehensive.py`
**Total Tests:** 50 (48 targeted + 2 integration)

---

## Test Index by Command

### 1. `vibey roadmap init` (2 tests)

| Test | Line | Status | Description |
|------|------|--------|-------------|
| `test_roadmap_init_basic` | 234 | ❌ | Basic initialization |
| `test_roadmap_init_with_options` | 258 | ❌ | Custom name/version |

---

### 2. `vibey roadmap status` (5 tests)

| Test | Line | Status | Description |
|------|------|--------|-------------|
| `test_roadmap_status_overall` | 279 | ❌ | Overall status display |
| `test_roadmap_status_filter_by_track` | 294 | ❌ | Filter by --track |
| `test_roadmap_status_filter_by_sprint` | 307 | ❌ | Filter by --sprint |
| `test_roadmap_status_output_format` | 316 | ❌ | Table formatting |
| `test_roadmap_status_empty_roadmap` | 330 | ❌ | Empty roadmap handling |

---

### 3. `vibey roadmap show` (2 tests)

| Test | Line | Status | Description |
|------|------|--------|-------------|
| `test_roadmap_show_track` | 344 | ❌ | Show track details |
| `test_roadmap_show_sprint` | 357 | ❌ | Show sprint details |

---

### 4. `vibey roadmap start` (4 tests)

| Test | Line | Status | Description |
|------|------|--------|-------------|
| `test_roadmap_start_sprint` | 378 | ❌ | Start sprint |
| `test_roadmap_start_task` | 394 | ❌ | Start task |
| `test_roadmap_start_already_started` | 415 | ❌ | Idempotent start |
| `test_roadmap_start_blocked_sprint` | 430 | ❌ | Blocked sprint error |

---

### 5. `vibey roadmap complete` (4 tests)

| Test | Line | Status | Description |
|------|------|--------|-------------|
| `test_roadmap_complete_task` | 444 | ❌ | Complete task |
| `test_roadmap_complete_sprint_with_quality_gates` | 461 | ⏭️ | Sprint + quality gates |
| `test_roadmap_complete_sprint_gates_fail` | 479 | ⏭️ | Gate failure handling |
| `test_roadmap_complete_not_started_item` | 493 | ❌ | Invalid state transition |

---

### 6. `vibey roadmap context` (1 test)

| Test | Line | Status | Description |
|------|------|--------|-------------|
| `test_roadmap_context_task` | 505 | ❌ | AI-optimized context |

---

### 7. `vibey roadmap summarize` (2 tests)

| Test | Line | Status | Description |
|------|------|--------|-------------|
| `test_roadmap_summarize_sprint` | 527 | ❌ | Sprint summary |
| `test_roadmap_summarize_track` | 541 | ❌ | Track summary |

---

## Test Index by Category

### Quality Gate Integration (5 tests) - All ⏭️ SKIPPED

| Test | Line | Reason |
|------|------|--------|
| `test_quality_gates_run_on_sprint_complete` | 558 | Not implemented |
| `test_quality_gate_pass_output` | 564 | Not implemented |
| `test_quality_gate_fail_output` | 572 | Not implemented |
| `test_quality_gates_blocking_completion` | 581 | Not implemented |
| `test_quality_gates_retry_after_fix` | 588 | Not implemented |

---

### State Machine Transitions (6 tests)

| Test | Line | Status | Description |
|------|------|--------|-------------|
| `test_state_not_started_to_in_progress` | 604 | ❌ | Valid transition |
| `test_state_in_progress_to_completion_gate_check` | 620 | ⏭️ | Gate check state |
| `test_state_completion_gate_check_to_completed` | 626 | ⏭️ | Final completion |
| `test_state_completion_gate_check_to_in_progress` | 631 | ⏭️ | Gate failure rollback |
| `test_invalid_state_transition_rejected` | 636 | ✅ | Invalid transitions |
| `test_idempotent_state_operations` | 648 | ❌ | Idempotent ops |

---

### Dependency Management (5 tests)

| Test | Line | Status | Description |
|------|------|--------|-------------|
| `test_blocked_track_shown_in_status` | 667 | ❌ | Blocked indicator |
| `test_blocked_track_details_in_show` | 678 | ✅ | Dependency details |
| `test_cannot_start_blocked_sprint` | 690 | ✅ | Block start attempt |
| `test_ready_to_start_after_dependency_resolves` | 699 | ❌ | Unblock on resolution |
| `test_circular_dependency_detection` | 723 | ⏭️ | Circular dependencies |

---

### AI Context & Summarization (4 tests)

| Test | Line | Status | Description |
|------|------|--------|-------------|
| `test_context_output_format_for_ai` | 737 | ❌ | AI-optimized format |
| `test_context_includes_related_tasks` | 754 | ❌ | Related tasks |
| `test_context_includes_files_to_modify` | 766 | ❌ | Files to modify |
| `test_summarize_output_format` | 778 | ❌ | Summary format |

---

### Dual-Mode Interaction (3 tests) - All ⏭️ SKIPPED

| Test | Line | Reason |
|------|------|--------|
| `test_natural_language_roadmap_init` | 799 | Needs Claude Code |
| `test_cli_and_nl_equivalence` | 806 | Needs Claude Code |
| `test_mode_detection_and_switching` | 812 | Needs framework integration |

---

### Output Formatting (5 tests)

| Test | Line | Status | Description |
|------|------|--------|-------------|
| `test_status_table_formatting` | 826 | ❌ | Table structure |
| `test_status_icons_rendering` | 841 | ❌ | Status icons |
| `test_progress_bar_rendering` | 853 | ❌ | Progress indicators |
| `test_detailed_view_formatting` | 864 | ❌ | Detail view format |
| `test_error_message_formatting` | 878 | ✅ | Error messages |

---

### Integration Tests (2 tests)

| Test | Line | Status | Description |
|------|------|--------|-------------|
| `test_complete_task_workflow` | 898 | ❌ | End-to-end task |
| `test_sprint_lifecycle` | 919 | ❌ | Sprint lifecycle |

---

## Test Fixtures

### Available Fixtures

1. **`temp_repo_dir`** (Line 38)
   - Creates temporary directory
   - Auto-cleanup after test

2. **`sample_roadmap`** (Line 46)
   - 3 tracks, 5 sprints, multiple tasks
   - Dependencies configured
   - Quality gates defined

3. **`empty_roadmap`** (Line 117)
   - Empty roadmap (no tracks)
   - For testing initialization

4. **`mock_quality_gates`** (Line 140)
   - Pass/fail scenarios
   - Gate scores and thresholds

---

## Helper Functions

### `run_cli(*args, cwd=None)` (Line 154)

Run vibey CLI command and capture output.

**Usage:**
```python
result = run_cli("roadmap", "status", cwd=temp_repo_dir)
assert result.returncode == 0
assert "user-management" in result.stdout
```

**Returns:**
- `subprocess.CompletedProcess` with:
  - `returncode` - Exit code
  - `stdout` - Standard output
  - `stderr` - Error output

---

## Common Patterns

### Basic Test Structure

```python
def test_something(self, sample_roadmap):
    """Test description."""
    # Run CLI command
    result = run_cli("roadmap", "status", cwd=sample_roadmap)

    # Verify exit code
    assert result.returncode == 0

    # Verify output
    assert "expected text" in result.stdout.lower()
```

### Testing File Changes

```python
def test_file_updated(self, sample_roadmap):
    """Test that file is updated."""
    # Run command
    run_cli("roadmap", "start", "task-001", cwd=sample_roadmap)

    # Read file
    file_path = sample_roadmap / ".vibey" / "tasks" / "task-001.yaml"
    with open(file_path) as f:
        data = yaml.safe_load(f)

    # Verify change
    assert data["task"]["status"] == "in_progress"
```

### Testing Errors

```python
def test_error_handling(self, sample_roadmap):
    """Test error handling."""
    result = run_cli("roadmap", "show", "nonexistent", cwd=sample_roadmap)

    # Should fail
    assert result.returncode != 0

    # Check error message
    error_output = result.stderr + result.stdout
    assert "not found" in error_output.lower()
```

---

## Running Tests

### All Tests
```bash
pytest tests/cli/test_roadmap_cli_comprehensive.py -v
```

### Single Test
```bash
pytest tests/cli/test_roadmap_cli_comprehensive.py::TestRoadmapInit::test_roadmap_init_basic -v
```

### Single Category
```bash
pytest tests/cli/test_roadmap_cli_comprehensive.py::TestRoadmapStatus -v
```

### Skip Slow Tests
```bash
pytest tests/cli/test_roadmap_cli_comprehensive.py -v -m "not slow"
```

### Show Output
```bash
pytest tests/cli/test_roadmap_cli_comprehensive.py -v -s
```

---

## Quick Stats

- **Total Tests:** 50
- **Passing:** 4 (8%)
- **Failing:** 32 (64%)
- **Skipped:** 14 (28%)

**By Priority:**
- 🔴 P1 (Critical): 25 tests
- 🟡 P2 (Important): 15 tests
- 🟢 P3 (Nice-to-have): 10 tests

---

## Test Markers

Tests can be marked for selective running:

```python
@pytest.mark.slow  # Slow tests
@pytest.mark.integration  # Integration tests
@pytest.mark.unit  # Unit tests
```

---

**Last Updated:** 2025-11-10
