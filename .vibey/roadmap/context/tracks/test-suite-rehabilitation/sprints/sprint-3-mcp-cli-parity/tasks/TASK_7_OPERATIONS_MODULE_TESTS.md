# Task 7: Add Tests for All Operations Modules

## Task Metadata
- **ID:** `01KCMKCXP4MZHWR7W6S9WZ1CF0`
- **Sprint:** Sprint 3: MCP/CLI Parity & Integration Tests
- **Priority:** Medium
- **Complexity:** Complex
- **Type:** Testing
- **Estimated Effort:** 6-8 hours

## Objective
Achieve 100% test coverage for all modules in `vibey/operations/`, ensuring all public functions have comprehensive tests.

## Current State Analysis

### Operations Module Structure
```
vibey/operations/
├── roadmap/
│   ├── update.py           # Status updates, progress computation
│   ├── status_manager.py   # Status transitions, validation
│   ├── advanced_validator.py
│   ├── verification.py
│   ├── audit_trail.py
│   ├── activity_log.py
│   └── ...
├── docs/
│   ├── cli_introspector.py
│   ├── cli_reference_generator.py
│   ├── mcp_introspector.py
│   ├── mcp_reference_generator.py
│   └── drift_checker.py
├── git/
│   ├── hooks/
│   └── commit_parser.py
├── auth/
│   └── ...
└── deploy/
    └── ...
```

### Priority Modules (by usage)
1. `operations/roadmap/update.py` - Core CRUD operations
2. `operations/roadmap/status_manager.py` - Status transitions
3. `operations/docs/` - Documentation generation (new)
4. `operations/git/` - Git integration

## Implementation Steps

### Step 1: Audit Current Coverage
```bash
# Generate coverage report for operations
pytest tests/operations/ --cov=vibey/operations --cov-report=html

# Identify gaps
coverage report --show-missing | grep vibey/operations
```

### Step 2: Test Roadmap Update Operations
**File:** `tests/operations/roadmap/test_update.py`
```python
import pytest
from pathlib import Path
from vibey.operations.roadmap.update import (
    update_task_status,
    update_sprint_progress,
    batch_update_tasks,
)

class TestUpdateTaskStatus:
    def test_valid_status_transition(self, roadmap_fixture):
        result = update_task_status(
            roadmap_fixture.root,
            task_id="01KC...",
            new_status="in_progress"
        )
        assert result.status == "in_progress"

    def test_invalid_status_transition_raises(self, roadmap_fixture):
        # not_started -> completed without in_progress
        with pytest.raises(InvalidTransitionError):
            update_task_status(
                roadmap_fixture.root,
                task_id="01KC...",
                new_status="completed"
            )

    def test_update_triggers_progress_recomputation(self, roadmap_fixture):
        # Complete a task, verify sprint progress increases
        pass

class TestUpdateSprintProgress:
    def test_progress_computed_correctly(self, roadmap_fixture):
        pass

    def test_completion_percentage_rounds_correctly(self, roadmap_fixture):
        pass

class TestBatchUpdateTasks:
    def test_batch_update_atomic(self, roadmap_fixture):
        # All succeed or all fail
        pass

    def test_batch_update_rollback_on_error(self, roadmap_fixture):
        pass
```

### Step 3: Test Status Manager
**File:** `tests/operations/roadmap/test_status_manager.py`
```python
import pytest
from vibey.operations.roadmap.status_manager import StatusManager

class TestStatusManager:
    def test_valid_task_transitions(self):
        sm = StatusManager()
        assert sm.is_valid_transition("not_started", "in_progress")
        assert sm.is_valid_transition("in_progress", "completed")
        assert not sm.is_valid_transition("not_started", "completed")

    def test_valid_sprint_transitions(self):
        sm = StatusManager()
        assert sm.is_valid_transition("not_started", "in_progress", entity_type="sprint")

    def test_blocked_status_handling(self):
        pass
```

### Step 4: Test Documentation Operations
**File:** `tests/operations/docs/test_cli_introspector.py`
```python
import pytest
from vibey.operations.docs.cli_introspector import introspect_cli

class TestCLIIntrospector:
    def test_discovers_all_commands(self):
        commands = introspect_cli()
        assert len(commands) >= 169  # Known command count

    def test_command_has_required_fields(self):
        commands = introspect_cli()
        for cmd in commands:
            assert "name" in cmd
            assert "help" in cmd
            assert "params" in cmd

    def test_subcommand_discovery(self):
        # roadmap start, roadmap complete, etc.
        pass
```

**File:** `tests/operations/docs/test_reference_generators.py`
```python
import pytest
from pathlib import Path
from vibey.operations.docs.cli_reference_generator import generate_cli_reference
from vibey.operations.docs.mcp_reference_generator import generate_mcp_reference

class TestCLIReferenceGenerator:
    def test_generates_valid_markdown(self, tmp_path):
        output = tmp_path / "CLI_REFERENCE.md"
        result = generate_cli_reference(tmp_path, output)
        assert output.exists()
        content = output.read_text()
        assert "# CLI Reference" in content

    def test_includes_all_commands(self, tmp_path):
        output = tmp_path / "CLI_REFERENCE.md"
        generate_cli_reference(tmp_path, output)
        content = output.read_text()
        assert "roadmap status" in content
        assert "roadmap start" in content

class TestMCPReferenceGenerator:
    def test_generates_valid_markdown(self, tmp_path):
        output = tmp_path / "MCP_REFERENCE.md"
        result = generate_mcp_reference(tmp_path, output)
        assert output.exists()

    def test_includes_all_tools(self, tmp_path):
        output = tmp_path / "MCP_REFERENCE.md"
        generate_mcp_reference(tmp_path, output)
        content = output.read_text()
        assert "vibey_roadmap_status" in content
```

**File:** `tests/operations/docs/test_drift_checker.py`
```python
import pytest
from vibey.operations.docs.drift_checker import check_documentation_drift

class TestDriftChecker:
    def test_no_drift_when_docs_current(self, roadmap_with_docs):
        result = check_documentation_drift(roadmap_with_docs.root)
        assert not result["drift_detected"]

    def test_detects_missing_command_docs(self, roadmap_with_outdated_docs):
        result = check_documentation_drift(roadmap_with_outdated_docs.root)
        assert result["drift_detected"]
        assert len(result["drift_items"]) > 0
```

### Step 5: Test Git Operations
**File:** `tests/operations/git/test_commit_parser.py`
```python
import pytest
from vibey.operations.git.commit_parser import parse_commit_message

class TestCommitParser:
    def test_parses_conventional_commit(self):
        message = "feat(roadmap): Add new feature"
        result = parse_commit_message(message)
        assert result["type"] == "feat"
        assert result["scope"] == "roadmap"

    def test_extracts_task_reference(self):
        message = "feat(01KCABC123): Implement feature\n\nTask: 01KCABC123"
        result = parse_commit_message(message)
        assert "01KCABC123" in result["task_ids"]

    def test_handles_invalid_format(self):
        message = "random commit message"
        result = parse_commit_message(message)
        assert result["type"] is None
```

### Step 6: Test Remaining Modules
Create tests for:
- `operations/auth/` - Key management, signing
- `operations/deploy/` - Platform deployment
- `operations/context/` - Context management

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `tests/operations/roadmap/test_update.py` | Create/Expand | Update operations |
| `tests/operations/roadmap/test_status_manager.py` | Create | Status transitions |
| `tests/operations/docs/test_cli_introspector.py` | Create | CLI introspection |
| `tests/operations/docs/test_reference_generators.py` | Create | Doc generation |
| `tests/operations/docs/test_drift_checker.py` | Create | Drift detection |
| `tests/operations/git/test_commit_parser.py` | Create | Commit parsing |

## Acceptance Criteria

- [ ] All `operations/roadmap/` modules have tests
- [ ] All `operations/docs/` modules have tests
- [ ] All `operations/git/` modules have tests
- [ ] Coverage ≥100% for operations modules
- [ ] No untested public functions
- [ ] All tests pass in CI

## Test Execution
```bash
# Run all operations tests
pytest tests/operations/ -v

# Run with coverage
pytest tests/operations/ --cov=vibey/operations --cov-report=term-missing --cov-fail-under=100
```

## Dependencies
- pytest
- pytest-cov

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Large scope | Prioritize by usage frequency |
| File system dependencies | Use tmp_path fixtures |
| Git dependencies | Mock or use test repos |
