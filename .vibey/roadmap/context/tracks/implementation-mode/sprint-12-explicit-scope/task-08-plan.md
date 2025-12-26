# Task 08: Add tests for explicit scope requirements

**Task ID**: `01KDC7N5Z6BEX8F9V0V8Q5DK40`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: medium
**Estimated Tokens**: 5000

## Description

Write tests for: (1) bare command shows help, (2) --all-tickets enables full execution, (3) --ticket filters correctly by hierarchy, (4) completion detection works for parent tickets, (5) deprecated options still work with warnings.

## Current State

- No tests exist for the `vibey implement` command
- No tests for TaskSelector hierarchy filtering
- No tests for TicketCompletionChecker

## Target State

- Comprehensive test coverage for explicit scope requirements
- Unit tests for helper functions
- Integration tests for CLI behavior
- Tests for backward compatibility

## Implementation Steps

### Step 1: Create test file structure

```
tests/
├── cli/
│   └── test_implement.py            # CLI behavior tests
└── services/
    └── implementation/
        ├── test_selector.py          # TaskSelector tests
        └── test_completion.py        # TicketCompletionChecker tests
```

### Step 2: Create CLI tests (tests/cli/test_implement.py)

```python
"""Tests for vibey implement CLI command."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path

from vibey.cli.implement import implement


class TestImplementBareCommand:
    """Tests for bare command behavior (no options)."""

    def test_bare_command_shows_help(self, cli_runner):
        """Bare command shows scope required help."""
        result = cli_runner.invoke(implement)

        assert result.exit_code == 0
        assert "Explicit Scope Required" in result.output
        assert "--all-tickets" in result.output
        assert "--ticket" in result.output

    def test_bare_command_does_not_execute(self, cli_runner, mock_run_implementation):
        """Bare command does not start implementation."""
        result = cli_runner.invoke(implement)

        mock_run_implementation.assert_not_called()


class TestAllTicketsFlag:
    """Tests for --all-tickets flag."""

    def test_all_tickets_shows_confirmation(self, cli_runner):
        """--all-tickets prompts for confirmation."""
        result = cli_runner.invoke(implement, ['--all-tickets'], input='n\n')

        assert "WARNING: Full Roadmap Execution" in result.output
        assert "Continue with full roadmap execution?" in result.output
        assert result.exit_code == 0  # Aborted cleanly

    def test_all_tickets_confirm_no_aborts(self, cli_runner):
        """Confirming 'n' aborts execution."""
        result = cli_runner.invoke(implement, ['--all-tickets'], input='n\n')

        assert "Aborted" in result.output

    def test_all_tickets_confirm_yes_executes(self, cli_runner, mock_run_implementation):
        """Confirming 'y' proceeds with execution."""
        mock_run_implementation.return_value = 0

        result = cli_runner.invoke(implement, ['--all-tickets'], input='y\n')

        mock_run_implementation.assert_called_once()

    def test_all_tickets_with_yes_skips_confirmation(self, cli_runner, mock_run_implementation):
        """--yes flag skips confirmation prompt."""
        mock_run_implementation.return_value = 0

        result = cli_runner.invoke(implement, ['--all-tickets', '--yes'])

        assert "Continue with full roadmap execution?" not in result.output
        mock_run_implementation.assert_called_once()

    def test_all_tickets_dry_run_skips_confirmation(self, cli_runner, mock_run_implementation):
        """--dry-run skips confirmation (safe operation)."""
        mock_run_implementation.return_value = 0

        result = cli_runner.invoke(implement, ['--all-tickets', '--dry-run'])

        assert "Continue with full roadmap execution?" not in result.output
        mock_run_implementation.assert_called_once()


class TestTicketOption:
    """Tests for --ticket ULID option."""

    def test_ticket_with_track_ulid(self, cli_runner, mock_run_implementation, tmp_roadmap):
        """--ticket with track ULID filters to track."""
        track_id = "01KC2D0JK9JKQXGQW6MQEB0JZP"
        (tmp_roadmap / "tracks" / f"{track_id}.yaml").write_text("id: " + track_id)

        mock_run_implementation.return_value = 0
        result = cli_runner.invoke(implement, ['--ticket', track_id])

        mock_run_implementation.assert_called_once()
        call_kwargs = mock_run_implementation.call_args.kwargs
        assert call_kwargs['target_ticket'] == track_id
        assert call_kwargs['target_ticket_type'] == 'track'

    def test_ticket_with_sprint_ulid(self, cli_runner, mock_run_implementation, tmp_roadmap):
        """--ticket with sprint ULID filters to sprint."""
        sprint_id = "01KC2D0JKVT80AFQ6C1PA8CKJD"
        (tmp_roadmap / "sprints" / f"{sprint_id}.yaml").write_text("id: " + sprint_id)

        mock_run_implementation.return_value = 0
        result = cli_runner.invoke(implement, ['--ticket', sprint_id])

        mock_run_implementation.assert_called_once()
        call_kwargs = mock_run_implementation.call_args.kwargs
        assert call_kwargs['target_ticket'] == sprint_id
        assert call_kwargs['target_ticket_type'] == 'sprint'

    def test_ticket_with_task_ulid(self, cli_runner, mock_run_implementation, tmp_roadmap):
        """--ticket with task ULID targets single task."""
        task_id = "01KC2D0JK7READW9KAK1HBX4B8"
        (tmp_roadmap / "tasks" / f"{task_id}.yaml").write_text("id: " + task_id)

        mock_run_implementation.return_value = 0
        result = cli_runner.invoke(implement, ['--ticket', task_id])

        mock_run_implementation.assert_called_once()
        call_kwargs = mock_run_implementation.call_args.kwargs
        assert call_kwargs['target_ticket'] == task_id
        assert call_kwargs['target_ticket_type'] == 'task'

    def test_ticket_with_invalid_ulid(self, cli_runner):
        """--ticket with invalid ULID shows error."""
        result = cli_runner.invoke(implement, ['--ticket', 'INVALID_ULID'])

        assert result.exit_code == 1
        assert "Ticket not found" in result.output


class TestDeprecatedOptions:
    """Tests for deprecated --track and --sprint options."""

    def test_track_shows_deprecation_warning(self, cli_runner, mock_run_implementation, tmp_roadmap):
        """--track shows deprecation warning."""
        track_id = "01KC2D0JK9JKQXGQW6MQEB0JZP"
        (tmp_roadmap / "tracks" / f"{track_id}.yaml").write_text("id: " + track_id)

        mock_run_implementation.return_value = 0
        result = cli_runner.invoke(implement, ['--track', track_id])

        assert "Warning" in result.output
        assert "--track is deprecated" in result.output
        assert f"--ticket {track_id}" in result.output

    def test_sprint_shows_deprecation_warning(self, cli_runner, mock_run_implementation, tmp_roadmap):
        """--sprint shows deprecation warning."""
        sprint_id = "01KC2D0JKVT80AFQ6C1PA8CKJD"
        (tmp_roadmap / "sprints" / f"{sprint_id}.yaml").write_text("id: " + sprint_id)

        mock_run_implementation.return_value = 0
        result = cli_runner.invoke(implement, ['--sprint', sprint_id])

        assert "Warning" in result.output
        assert "--sprint is deprecated" in result.output
        assert f"--ticket {sprint_id}" in result.output

    def test_deprecated_options_still_execute(self, cli_runner, mock_run_implementation, tmp_roadmap):
        """Deprecated options still execute (backward compatible)."""
        track_id = "01KC2D0JK9JKQXGQW6MQEB0JZP"
        (tmp_roadmap / "tracks" / f"{track_id}.yaml").write_text("id: " + track_id)

        mock_run_implementation.return_value = 0
        result = cli_runner.invoke(implement, ['--track', track_id])

        mock_run_implementation.assert_called_once()

    def test_ticket_takes_precedence_over_deprecated(self, cli_runner, mock_run_implementation, tmp_roadmap):
        """--ticket takes precedence when both provided."""
        track_id = "01KC2D0JK9JKQXGQW6MQEB0JZP"
        task_id = "01KC2D0JK7READW9KAK1HBX4B8"
        (tmp_roadmap / "tracks" / f"{track_id}.yaml").write_text("id: " + track_id)
        (tmp_roadmap / "tasks" / f"{task_id}.yaml").write_text("id: " + task_id)

        mock_run_implementation.return_value = 0
        result = cli_runner.invoke(implement, ['--track', track_id, '--ticket', task_id])

        call_kwargs = mock_run_implementation.call_args.kwargs
        assert call_kwargs['target_ticket'] == task_id  # --ticket wins


# Fixtures

@pytest.fixture
def cli_runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_run_implementation():
    """Mock run_implementation_cmd function."""
    with patch('vibey.cli.implement.run_implementation_cmd') as mock:
        yield mock


@pytest.fixture
def tmp_roadmap(tmp_path, monkeypatch):
    """Create temporary roadmap structure."""
    roadmap = tmp_path / ".vibey" / "roadmap"
    (roadmap / "tracks").mkdir(parents=True)
    (roadmap / "sprints").mkdir(parents=True)
    (roadmap / "tasks").mkdir(parents=True)

    monkeypatch.chdir(tmp_path)
    return roadmap
```

### Step 3: Create TaskSelector tests (tests/services/implementation/test_selector.py)

```python
"""Tests for TaskSelector with hierarchical scope."""

import pytest
from unittest.mock import MagicMock
from pathlib import Path

from vibey.services.implementation.selector import TaskSelector


class TestTaskSelectorTaskIdFilter:
    """Tests for task_id parameter (single task execution)."""

    def test_get_next_task_with_task_id(self, selector, sample_task):
        """get_next_task with task_id returns only that task."""
        result = selector.get_next_task(task_id=sample_task['id'])

        assert result is not None
        assert result.id == sample_task['id']

    def test_get_next_task_blocked_task_returns_none(self, selector, blocked_task):
        """Blocked task returns None."""
        result = selector.get_next_task(task_id=blocked_task['id'])

        assert result is None

    def test_get_next_task_completed_task_returns_none(self, selector, completed_task):
        """Completed task returns None."""
        result = selector.get_next_task(task_id=completed_task['id'])

        assert result is None

    def test_get_next_task_nonexistent_task_returns_none(self, selector):
        """Nonexistent task returns None."""
        result = selector.get_next_task(task_id='NONEXISTENT_TASK_ID')

        assert result is None

    def test_get_all_executable_with_task_id(self, selector, sample_task):
        """get_all_executable with task_id returns list with one task."""
        result = selector.get_all_executable(task_id=sample_task['id'])

        assert len(result) == 1
        assert result[0].id == sample_task['id']

    def test_count_remaining_with_task_id(self, selector, sample_task):
        """count_remaining with task_id returns 1 for executable task."""
        result = selector.count_remaining(task_id=sample_task['id'])

        assert result == 1

    def test_count_remaining_with_blocked_task_id(self, selector, blocked_task):
        """count_remaining with blocked task_id returns 0."""
        result = selector.count_remaining(task_id=blocked_task['id'])

        assert result == 0


class TestTaskSelectorExistingBehavior:
    """Tests that existing track_id/sprint_id filtering unchanged."""

    def test_track_id_filtering_unchanged(self, selector, track_with_tasks):
        """Existing track_id filtering works as before."""
        result = selector.get_all_executable(track_id=track_with_tasks['id'])

        assert len(result) > 0
        for task in result:
            assert task.track_id == track_with_tasks['id']

    def test_sprint_id_filtering_unchanged(self, selector, sprint_with_tasks):
        """Existing sprint_id filtering works as before."""
        result = selector.get_all_executable(sprint_id=sprint_with_tasks['id'])

        assert len(result) > 0
        for task in result:
            assert task.sprint_id == sprint_with_tasks['id']
```

### Step 4: Create TicketCompletionChecker tests (tests/services/implementation/test_completion.py)

```python
"""Tests for TicketCompletionChecker."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from vibey.services.implementation.completion import TicketCompletionChecker


class TestTaskCompletion:
    """Tests for task completion detection."""

    def test_completed_task_returns_true(self, checker, completed_task_id):
        """Completed task returns (True, message)."""
        is_complete, message = checker.check_and_complete(
            completed_task_id, "task"
        )

        assert is_complete is True
        assert completed_task_id in message

    def test_incomplete_task_returns_false(self, checker, incomplete_task_id):
        """Incomplete task returns (False, None)."""
        is_complete, message = checker.check_and_complete(
            incomplete_task_id, "task"
        )

        assert is_complete is False


class TestSprintCompletion:
    """Tests for sprint auto-completion."""

    def test_sprint_with_all_tasks_complete(self, checker, sprint_all_complete):
        """Sprint with all tasks complete auto-completes."""
        is_complete, message = checker.check_and_complete(
            sprint_all_complete['id'], "sprint"
        )

        assert is_complete is True
        assert "completed" in message.lower()

    def test_sprint_with_incomplete_tasks(self, checker, sprint_incomplete):
        """Sprint with incomplete tasks does not complete."""
        is_complete, message = checker.check_and_complete(
            sprint_incomplete['id'], "sprint"
        )

        assert is_complete is False
        assert "remaining" in message

    @patch('vibey.operations.roadmap.status_manager.StatusManager')
    def test_sprint_completion_updates_yaml(self, mock_manager, checker, sprint_all_complete):
        """Sprint completion updates YAML file."""
        checker.check_and_complete(sprint_all_complete['id'], "sprint")

        mock_manager.return_value.complete_sprint.assert_called_with(
            sprint_all_complete['id']
        )


class TestTrackCompletion:
    """Tests for track auto-completion."""

    def test_track_with_all_sprints_complete(self, checker, track_all_complete):
        """Track with all sprints complete auto-completes."""
        is_complete, message = checker.check_and_complete(
            track_all_complete['id'], "track"
        )

        assert is_complete is True
        assert "completed" in message.lower()

    def test_track_with_incomplete_sprints(self, checker, track_incomplete):
        """Track with incomplete sprints does not complete."""
        is_complete, message = checker.check_and_complete(
            track_incomplete['id'], "track"
        )

        assert is_complete is False
        assert "remaining" in message

    @patch('vibey.operations.roadmap.status_manager.StatusManager')
    def test_track_completion_updates_yaml(self, mock_manager, checker, track_all_complete):
        """Track completion updates YAML file."""
        checker.check_and_complete(track_all_complete['id'], "track")

        mock_manager.return_value.complete_track.assert_called_with(
            track_all_complete['id']
        )
```

### Step 5: Add conftest.py fixtures

Create `tests/services/implementation/conftest.py`:

```python
"""Shared fixtures for implementation tests."""

import pytest
import sqlite3
from pathlib import Path

from vibey.services.implementation.selector import TaskSelector
from vibey.services.implementation.completion import TicketCompletionChecker


@pytest.fixture
def test_db(tmp_path):
    """Create test database with sample data."""
    db_path = tmp_path / "roadmap.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Create schema
    conn.executescript("""
        CREATE TABLE tracks (
            id TEXT PRIMARY KEY,
            name TEXT,
            status TEXT
        );
        CREATE TABLE sprints (
            id TEXT PRIMARY KEY,
            track_id TEXT,
            name TEXT,
            status TEXT
        );
        CREATE TABLE tasks (
            id TEXT PRIMARY KEY,
            sprint_id TEXT,
            track_id TEXT,
            title TEXT,
            status TEXT,
            blocked INTEGER DEFAULT 0
        );
    """)

    # Insert test data
    conn.execute(
        "INSERT INTO tracks VALUES (?, ?, ?)",
        ("TRACK01", "Test Track", "in_progress")
    )
    conn.execute(
        "INSERT INTO sprints VALUES (?, ?, ?, ?)",
        ("SPRINT01", "TRACK01", "Test Sprint", "in_progress")
    )
    conn.execute(
        "INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?)",
        ("TASK01", "SPRINT01", "TRACK01", "Test Task", "not_started", 0)
    )
    conn.execute(
        "INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?)",
        ("TASK02", "SPRINT01", "TRACK01", "Blocked Task", "not_started", 1)
    )
    conn.execute(
        "INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?)",
        ("TASK03", "SPRINT01", "TRACK01", "Completed Task", "completed", 0)
    )
    conn.commit()

    yield db_path
    conn.close()


@pytest.fixture
def selector(test_db, tmp_path):
    """Create TaskSelector with test database."""
    roadmap = tmp_path / ".vibey" / "roadmap"
    roadmap.mkdir(parents=True)
    # Copy test db to expected location
    import shutil
    shutil.copy(test_db, roadmap / "roadmap.db")
    return TaskSelector(roadmap)


@pytest.fixture
def checker(test_db, tmp_path):
    """Create TicketCompletionChecker with test database."""
    roadmap = tmp_path / ".vibey" / "roadmap"
    roadmap.mkdir(parents=True)
    import shutil
    shutil.copy(test_db, roadmap / "roadmap.db")
    return TicketCompletionChecker(roadmap)


@pytest.fixture
def sample_task():
    """Return sample executable task data."""
    return {'id': 'TASK01', 'title': 'Test Task', 'status': 'not_started'}


@pytest.fixture
def blocked_task():
    """Return blocked task data."""
    return {'id': 'TASK02', 'title': 'Blocked Task'}


@pytest.fixture
def completed_task():
    """Return completed task data."""
    return {'id': 'TASK03', 'title': 'Completed Task'}
```

## Files to Create

| File | Description |
|------|-------------|
| `tests/cli/test_implement.py` | CLI behavior tests |
| `tests/services/implementation/test_selector.py` | TaskSelector tests |
| `tests/services/implementation/test_completion.py` | TicketCompletionChecker tests |
| `tests/services/implementation/conftest.py` | Shared fixtures |

## Test Coverage Requirements

| Component | Tests | Coverage Target |
|-----------|-------|-----------------|
| Bare command behavior | 2 | 100% |
| --all-tickets flag | 5 | 100% |
| --ticket option | 4 | 100% |
| Deprecated options | 4 | 100% |
| TaskSelector.task_id | 7 | 100% |
| TicketCompletionChecker | 8 | 100% |
| **Total** | **30** | **90%+** |

## Run Tests Command

```bash
pytest tests/cli/test_implement.py tests/services/implementation/ -v --cov=vibey.cli.implement --cov=vibey.services.implementation
```

## Acceptance Criteria

- [ ] All 30 tests pass
- [ ] Coverage >= 90% for affected modules
- [ ] No flaky tests
- [ ] Tests run in < 30 seconds
- [ ] CI pipeline passes
