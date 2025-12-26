# Task 08: Add tests for explicit scope requirements

**Task ID**: `01KDC7N5Z6BEX8F9V0V8Q5DK40`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: medium
**Estimated Tokens**: 5000

## Description

Write tests for the unified ticket architecture integration: (1) bare command shows help, (2) --all-tickets enables full execution, (3) --ticket uses TicketService, (4) completion detection uses HierarchicalTicket methods, (5) deprecated options still work with warnings.

## Architecture Context

Tests should verify that:
- CLI uses TicketService for ticket resolution (not filesystem)
- TaskSelector uses HierarchicalTicket scope (not track_id/sprint_id)
- Completion detection uses can_transition_to/auto_progress (not type-specific methods)
- No type-specific logic leaks into CLI layer

## Test Structure

```
tests/
├── cli/
│   └── test_implement.py            # CLI behavior tests
└── services/
    └── implementation/
        ├── test_selector.py          # TaskSelector with HierarchicalTicket
        ├── test_completion.py        # ScopeCompletionChecker tests
        └── conftest.py               # Shared fixtures
```

## Implementation Steps

### Step 1: CLI tests (tests/cli/test_implement.py)

```python
"""Tests for vibey implement CLI command with unified architecture."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

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

    def test_all_tickets_shows_confirmation(self, cli_runner, mock_ticket_service):
        """--all-tickets prompts for confirmation."""
        result = cli_runner.invoke(implement, ['--all-tickets'], input='n\n')

        assert "WARNING" in result.output
        assert result.exit_code == 0

    def test_all_tickets_with_yes_skips_confirmation(self, cli_runner, mock_run_implementation):
        """--yes flag skips confirmation prompt."""
        mock_run_implementation.return_value = 0

        result = cli_runner.invoke(implement, ['--all-tickets', '--yes'])

        mock_run_implementation.assert_called_once()


class TestTicketOption:
    """Tests for --ticket ULID option using TicketService."""

    def test_ticket_uses_ticket_service(self, cli_runner, mock_ticket_service, mock_run_implementation):
        """--ticket resolves via TicketService.get_ticket()."""
        ticket_ulid = "01KC2D0JK9JKQXGQW6MQEB0JZP"
        mock_ticket = MagicMock()
        mock_ticket_service.return_value.get_ticket.return_value = mock_ticket
        mock_run_implementation.return_value = 0

        result = cli_runner.invoke(implement, ['--ticket', ticket_ulid])

        # Verify TicketService was used
        mock_ticket_service.return_value.get_ticket.assert_called_once_with(ticket_ulid)

        # Verify scope_ticket was passed (not track_id/sprint_id)
        call_kwargs = mock_run_implementation.call_args.kwargs
        assert 'scope_ticket' in call_kwargs
        assert call_kwargs['scope_ticket'] == mock_ticket

    def test_ticket_not_found_shows_error(self, cli_runner, mock_ticket_service):
        """--ticket with invalid ULID shows error via TicketNotFoundError."""
        from vibey.services.ticket_service import TicketNotFoundError

        mock_ticket_service.return_value.get_ticket.side_effect = TicketNotFoundError("INVALID")

        result = cli_runner.invoke(implement, ['--ticket', 'INVALID'])

        assert result.exit_code == 1
        assert "Ticket not found" in result.output

    def test_no_type_detection_in_cli(self, cli_runner, mock_ticket_service, mock_run_implementation):
        """CLI does not detect ticket type - uses HierarchicalTicket properties."""
        ticket_ulid = "01KC2D0JK9JKQXGQW6MQEB0JZP"
        mock_ticket = MagicMock()
        mock_ticket_service.return_value.get_ticket.return_value = mock_ticket
        mock_run_implementation.return_value = 0

        result = cli_runner.invoke(implement, ['--ticket', ticket_ulid])

        # Verify no type-specific parameters passed
        call_kwargs = mock_run_implementation.call_args.kwargs
        assert 'track_id' not in call_kwargs or call_kwargs.get('track_id') is None
        assert 'sprint_id' not in call_kwargs or call_kwargs.get('sprint_id') is None
        assert 'target_ticket_type' not in call_kwargs


class TestDeprecatedOptions:
    """Tests for deprecated --track and --sprint options."""

    def test_track_shows_deprecation_warning(self, cli_runner, mock_ticket_service, mock_run_implementation):
        """--track shows deprecation warning."""
        mock_ticket = MagicMock()
        mock_ticket_service.return_value.get_ticket.return_value = mock_ticket
        mock_run_implementation.return_value = 0

        result = cli_runner.invoke(implement, ['--track', '01KC...'])

        assert "Warning" in result.output
        assert "--track is deprecated" in result.output
        assert "--ticket" in result.output

    def test_sprint_shows_deprecation_warning(self, cli_runner, mock_ticket_service, mock_run_implementation):
        """--sprint shows deprecation warning."""
        mock_ticket = MagicMock()
        mock_ticket_service.return_value.get_ticket.return_value = mock_ticket
        mock_run_implementation.return_value = 0

        result = cli_runner.invoke(implement, ['--sprint', '01KC...'])

        assert "Warning" in result.output
        assert "--sprint is deprecated" in result.output

    def test_deprecated_options_use_ticket_service(self, cli_runner, mock_ticket_service, mock_run_implementation):
        """Deprecated options still use TicketService (same code path)."""
        mock_ticket = MagicMock()
        mock_ticket_service.return_value.get_ticket.return_value = mock_ticket
        mock_run_implementation.return_value = 0

        result = cli_runner.invoke(implement, ['--track', '01KC...'])

        # Same TicketService call as --ticket
        mock_ticket_service.return_value.get_ticket.assert_called_once()


# Fixtures

@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def mock_run_implementation():
    with patch('vibey.cli.implement.run_implementation_cmd') as mock:
        yield mock


@pytest.fixture
def mock_ticket_service():
    with patch('vibey.cli.implement.TicketService') as mock:
        yield mock
```

### Step 2: TaskSelector tests (tests/services/implementation/test_selector.py)

```python
"""Tests for TaskSelector with HierarchicalTicket scope."""

import pytest
from unittest.mock import MagicMock

from vibey.services.implementation.selector import TaskSelector
from vibey.roadmap.models.ticket.enums import TicketStatus


class TestTaskSelectorWithScope:
    """Tests for scope-based task selection."""

    def test_scope_with_ultimate_child_returns_if_executable(self, selector):
        """Scope that is_ultimate_child returns itself if executable."""
        scope = MagicMock()
        scope.is_ultimate_child = True
        scope.status = TicketStatus.NOT_STARTED
        scope.is_planned = True
        scope.can_transition_to.return_value = (True, [])

        result = selector.get_next_task(scope=scope)

        assert result == scope

    def test_scope_with_parent_searches_descendants(self, selector):
        """Scope that is_parent searches descendants for executable work."""
        child1 = MagicMock()
        child1.is_ultimate_child = True
        child1.status = TicketStatus.COMPLETED  # Not executable

        child2 = MagicMock()
        child2.is_ultimate_child = True
        child2.status = TicketStatus.NOT_STARTED
        child2.is_planned = True
        child2.can_transition_to.return_value = (True, [])

        scope = MagicMock()
        scope.is_ultimate_child = False
        scope.descendants = [child1, child2]

        result = selector.get_next_task(scope=scope)

        assert result == child2

    def test_uses_is_planned_property(self, selector):
        """Selector uses HierarchicalTicket.is_planned for planning check."""
        scope = MagicMock()
        scope.is_ultimate_child = True
        scope.status = TicketStatus.NOT_STARTED
        scope.is_planned = False  # Not planned

        result = selector.get_next_task(scope=scope)

        assert result is None

    def test_uses_can_transition_to_for_dependencies(self, selector):
        """Selector uses can_transition_to(IN_PROGRESS) for dependency check."""
        scope = MagicMock()
        scope.is_ultimate_child = True
        scope.status = TicketStatus.NOT_STARTED
        scope.is_planned = True
        scope.can_transition_to.return_value = (False, ["Dependency not met"])

        result = selector.get_next_task(scope=scope)

        assert result is None
        scope.can_transition_to.assert_called_with(TicketStatus.IN_PROGRESS)


class TestTaskSelectorNoTypeSpecificParams:
    """Tests that TaskSelector doesn't use type-specific parameters."""

    def test_no_track_id_parameter(self, selector):
        """TaskSelector.get_next_task has no track_id parameter."""
        import inspect
        sig = inspect.signature(selector.get_next_task)
        assert 'track_id' not in sig.parameters

    def test_no_sprint_id_parameter(self, selector):
        """TaskSelector.get_next_task has no sprint_id parameter."""
        import inspect
        sig = inspect.signature(selector.get_next_task)
        assert 'sprint_id' not in sig.parameters

    def test_scope_parameter_is_hierarchical_ticket(self, selector):
        """TaskSelector.get_next_task accepts HierarchicalTicket scope."""
        import inspect
        sig = inspect.signature(selector.get_next_task)
        assert 'scope' in sig.parameters


@pytest.fixture
def selector(mock_ticket_service):
    return TaskSelector(mock_ticket_service)


@pytest.fixture
def mock_ticket_service():
    return MagicMock()
```

### Step 3: Completion tests (tests/services/implementation/test_completion.py)

```python
"""Tests for ScopeCompletionChecker using HierarchicalTicket methods."""

import pytest
from unittest.mock import MagicMock, patch

from vibey.services.implementation.completion import ScopeCompletionChecker
from vibey.roadmap.models.ticket.enums import TicketStatus


class TestCompletionWithCanTransitionTo:
    """Tests that completion uses can_transition_to()."""

    def test_uses_can_transition_to_for_completion_check(self, checker):
        """Completion check uses HierarchicalTicket.can_transition_to()."""
        scope = MagicMock()
        scope.can_transition_to.return_value = (True, [])

        is_complete, _ = checker.check_scope_completion(scope)

        scope.can_transition_to.assert_called_with(TicketStatus.COMPLETED)
        assert is_complete is True

    def test_uses_progress_for_transition_for_details(self, checker):
        """Progress details use progress_for_transition()."""
        scope = MagicMock()
        scope.can_transition_to.return_value = (False, ["Child not complete"])
        scope.progress_for_transition.return_value = MagicMock(total=5, completed=3)

        is_complete, message = checker.check_scope_completion(scope)

        scope.progress_for_transition.assert_called_with(TicketStatus.COMPLETED)
        assert is_complete is False
        assert "2" in message  # 5 - 3 = 2 remaining


class TestCompletionWithAutoProgress:
    """Tests that completion uses auto_progress()."""

    def test_try_complete_uses_auto_progress(self, checker, mock_service):
        """try_complete_scope uses auto_progress() for transitions."""
        scope = MagicMock()
        scope.id = "SCOPE_ID"

        refreshed = MagicMock()
        refreshed.status = TicketStatus.COMPLETED
        refreshed.auto_progress.return_value = ["SCOPE_ID: IN_PROGRESS → COMPLETED"]
        mock_service.get_ticket.return_value = refreshed

        context = MagicMock()

        is_complete, transitions = checker.try_complete_scope(scope, context)

        refreshed.auto_progress.assert_called_once_with(context)
        assert is_complete is True


class TestNoTypeSpecificMethods:
    """Tests that completion doesn't have type-specific methods."""

    def test_no_check_track_complete_method(self, checker):
        """ScopeCompletionChecker has no _check_track_complete method."""
        assert not hasattr(checker, '_check_track_complete')

    def test_no_check_sprint_complete_method(self, checker):
        """ScopeCompletionChecker has no _check_sprint_complete method."""
        assert not hasattr(checker, '_check_sprint_complete')

    def test_no_check_task_complete_method(self, checker):
        """ScopeCompletionChecker has no _check_task_complete method."""
        assert not hasattr(checker, '_check_task_complete')


@pytest.fixture
def mock_service():
    return MagicMock()


@pytest.fixture
def checker(mock_service):
    return ScopeCompletionChecker(mock_service)
```

## Files to Create

| File | Description |
|------|-------------|
| `tests/cli/test_implement.py` | CLI behavior tests |
| `tests/services/implementation/test_selector.py` | TaskSelector tests |
| `tests/services/implementation/test_completion.py` | ScopeCompletionChecker tests |

## Test Coverage Requirements

| Component | Tests | Coverage Target |
|-----------|-------|-----------------|
| Bare command behavior | 2 | 100% |
| --all-tickets flag | 2 | 100% |
| --ticket with TicketService | 3 | 100% |
| Deprecated options | 3 | 100% |
| TaskSelector scope | 4 | 100% |
| TaskSelector no type params | 3 | 100% |
| Completion with can_transition | 2 | 100% |
| Completion with auto_progress | 1 | 100% |
| No type-specific methods | 3 | 100% |
| **Total** | **23** | **90%+** |

## Run Tests Command

```bash
pytest tests/cli/test_implement.py tests/services/implementation/ -v \
    --cov=vibey.cli.implement \
    --cov=vibey.services.implementation
```

## Acceptance Criteria

- [ ] All tests pass
- [ ] Coverage >= 90% for affected modules
- [ ] Tests verify TicketService is used (not filesystem)
- [ ] Tests verify HierarchicalTicket properties used (not type-specific logic)
- [ ] Tests verify can_transition_to/auto_progress used (not type-specific methods)
- [ ] No tests reference track_id/sprint_id/task_id directly
- [ ] Tests run in < 30 seconds
