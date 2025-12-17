# Task 5: Add Integration Tests for New Architecture

**Task ID:** `01KCMGZTMA1HC7GS44AB9D2VS1`
**Sprint:** Sprint 4: Major Refactoring
**Priority:** High | **Complexity:** Medium | **Type:** Testing

---

## Problem Statement

265 integration tests exist in `tests/integration/` but they don't cover:
1. The new unified `Ticket` model
2. Criteria-based transitions
3. The planned status workflow
4. CLI → Ticket model → YAML round-trip

This task adds targeted integration tests for the new architecture.

---

## Existing Test Infrastructure

### Current Integration Tests

```
tests/integration/
├── test_cli_workflows.py           # CLI command flows
├── test_cross_module.py            # Module interactions
├── test_git_integration.py         # Git operations
├── test_journey*.py                # User journey tests
├── test_mcp_tools.py               # MCP tool tests
├── test_mcp_workflows.py           # MCP workflow tests
└── test_standards_resolution.py    # Standards tests
```

### Existing Fixtures

```python
# tests/integration/conftest.py

@pytest.fixture
def roadmap_env(tmp_path):
    """Create isolated roadmap environment."""
    ...

@pytest.fixture
def sample_track(roadmap_env):
    """Create a sample track."""
    ...
```

---

## Implementation Steps

### Step 1: Create Ticket Model Test Fixtures (30 min)

```python
# tests/integration/conftest.py (additions)

import pytest
from pathlib import Path

from vibey.roadmap.models.ticket import (
    TaskTicket,
    SprintTicket,
    TrackTicket,
    HierarchicalTicket,
    TicketStatus,
)
from vibey.roadmap.models.ticket.completable import Criterion
from vibey.roadmap.models.ticket.targets import (
    CompletableTarget,
    FileExistsTarget,
    ManualTarget,
)


@pytest.fixture
def ticket_env(tmp_path):
    """
    Create isolated environment for ticket model testing.

    Sets up:
    - Roadmap directory structure
    - Database
    - HierarchicalTicket loaders
    """
    roadmap_root = tmp_path / ".vibey" / "roadmap"
    (roadmap_root / "tracks").mkdir(parents=True)
    (roadmap_root / "sprints").mkdir(parents=True)
    (roadmap_root / "tasks").mkdir(parents=True)
    (roadmap_root / "context" / "tasks").mkdir(parents=True)

    # Initialize database
    from vibey.roadmap.database.init import init_database
    db_path = roadmap_root / "roadmap.db"
    init_database(db_path)

    # Configure hierarchical ticket
    from vibey.roadmap.criteria.planned import PlannedCriteriaConfig
    HierarchicalTicket.set_planned_config(PlannedCriteriaConfig(), roadmap_root)

    yield {
        'root': tmp_path,
        'roadmap': roadmap_root,
        'db': db_path,
    }

    # Cleanup
    HierarchicalTicket.clear_planned_cache()
    HierarchicalTicket.clear_loaders()


@pytest.fixture
def task_with_criteria(ticket_env):
    """Create a task with completion criteria."""
    from vibey.roadmap.serialization.yaml_dumper import save_task_ticket

    # Create deliverable file criterion
    deliverable_path = ticket_env['root'] / "output.txt"

    task = TaskTicket(
        id="01TESTTASK001",
        name="Test Task",
        description="A task with criteria",
        status=TicketStatus.IN_PROGRESS,
        criteria=[
            Criterion(
                id="deliverable-1",
                description="Output file exists",
                target=FileExistsTarget(paths=[str(deliverable_path)]),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
        ],
    )

    save_task_ticket(task, ticket_env['roadmap'])

    return {
        'task': task,
        'deliverable_path': deliverable_path,
    }


@pytest.fixture
def sprint_with_tasks(ticket_env):
    """Create a sprint with child tasks."""
    from vibey.roadmap.serialization.yaml_dumper import (
        save_sprint_ticket,
        save_task_ticket,
    )

    # Create tasks
    tasks = []
    for i in range(3):
        task = TaskTicket(
            id=f"01SPRINTTASK{i:03d}",
            name=f"Task {i}",
            parent_ref="01TESTSPRINT01",
            status=TicketStatus.NOT_STARTED,
        )
        save_task_ticket(task, ticket_env['roadmap'])
        tasks.append(task)

    # Create sprint with tasks as criteria
    sprint = SprintTicket(
        id="01TESTSPRINT01",
        name="Test Sprint",
        criteria=[
            Criterion(
                id=f"task-{task.id}",
                description=f"Task {task.name} complete",
                target=CompletableTarget(
                    completable_id=task.id,
                    required_status=TicketStatus.COMPLETED,
                ),
                blocks_transition_to=TicketStatus.COMPLETED,
            )
            for task in tasks
        ],
    )

    save_sprint_ticket(sprint, ticket_env['roadmap'])

    return {
        'sprint': sprint,
        'tasks': tasks,
    }


@pytest.fixture
def blocking_dependency(ticket_env):
    """Create tasks with blocking dependency."""
    from vibey.roadmap.serialization.yaml_dumper import save_task_ticket

    # Task A (no dependencies)
    task_a = TaskTicket(
        id="01TASKA000001",
        name="Task A",
        status=TicketStatus.NOT_STARTED,
    )
    save_task_ticket(task_a, ticket_env['roadmap'])

    # Task B depends on Task A
    task_b = TaskTicket(
        id="01TASKB000001",
        name="Task B",
        status=TicketStatus.NOT_STARTED,
        criteria=[
            Criterion(
                id="dep-task-a",
                description="Task A must complete first",
                target=CompletableTarget(
                    completable_id=task_a.id,
                    required_status=TicketStatus.COMPLETED,
                ),
                blocks_transition_to=TicketStatus.IN_PROGRESS,
            ),
        ],
    )
    save_task_ticket(task_b, ticket_env['roadmap'])

    return {
        'task_a': task_a,
        'task_b': task_b,
    }
```

### Step 2: Create Criteria-Based Transition Tests (45 min)

```python
# tests/integration/test_criteria_transitions.py

"""
Integration tests for criteria-based state transitions.

Tests the full flow: CLI command → transitions.py → Ticket model → YAML
"""

import pytest
from click.testing import CliRunner

from vibey.cli.main import cli
from vibey.operations.roadmap.transitions import (
    TransitionBlockedError,
    transition_task,
    start_item,
    complete_item,
)
from vibey.roadmap.models.ticket import TicketStatus


class TestCriteriaBlocksStart:
    """Test that dependencies block starting."""

    def test_start_blocked_by_incomplete_dependency(self, ticket_env, blocking_dependency):
        """Cannot start task B when task A is not complete."""
        task_a = blocking_dependency['task_a']
        task_b = blocking_dependency['task_b']

        # Task B should be blocked
        with pytest.raises(TransitionBlockedError) as exc:
            start_item(ticket_env['root'], task_b.id)

        assert task_a.id in str(exc.value) or "Task A" in str(exc.value)
        assert len(exc.value.reasons) > 0

    def test_start_allowed_after_dependency_complete(self, ticket_env, blocking_dependency):
        """Can start task B after task A completes."""
        task_a = blocking_dependency['task_a']
        task_b = blocking_dependency['task_b']

        # Complete task A
        transition_task(task_a.id, TicketStatus.IN_PROGRESS, ticket_env['root'])
        transition_task(task_a.id, TicketStatus.COMPLETED, ticket_env['root'])

        # Refresh task B's criteria cache
        from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
        HierarchicalTicket.clear_planned_cache()

        # Now task B should be startable
        result = start_item(ticket_env['root'], task_b.id)
        assert result['status'] == 'in_progress'


class TestCriteriaBlocksComplete:
    """Test that completion criteria block completing."""

    def test_complete_blocked_by_unmet_criteria(self, ticket_env, task_with_criteria):
        """Cannot complete task when deliverable doesn't exist."""
        task = task_with_criteria['task']

        with pytest.raises(TransitionBlockedError) as exc:
            complete_item(ticket_env['root'], task.id)

        assert "Output file" in str(exc.value) or len(exc.value.reasons) > 0

    def test_complete_allowed_after_criteria_met(self, ticket_env, task_with_criteria):
        """Can complete task after deliverable exists."""
        task = task_with_criteria['task']
        deliverable_path = task_with_criteria['deliverable_path']

        # Create the deliverable
        deliverable_path.write_text("output content")

        # Now should be completable
        result = complete_item(ticket_env['root'], task.id)
        assert result['status'] == 'completed'


class TestSprintCompletionRequiresAllTasks:
    """Test that sprint completion requires all child tasks complete."""

    def test_sprint_blocked_with_incomplete_tasks(self, ticket_env, sprint_with_tasks):
        """Cannot complete sprint when tasks are incomplete."""
        sprint = sprint_with_tasks['sprint']

        with pytest.raises(TransitionBlockedError) as exc:
            complete_item(ticket_env['root'], sprint.id)

        assert len(exc.value.reasons) > 0

    def test_sprint_completable_when_all_tasks_done(self, ticket_env, sprint_with_tasks):
        """Can complete sprint when all tasks are complete."""
        sprint = sprint_with_tasks['sprint']
        tasks = sprint_with_tasks['tasks']

        # Complete all tasks
        for task in tasks:
            transition_task(task.id, TicketStatus.IN_PROGRESS, ticket_env['root'])
            transition_task(task.id, TicketStatus.COMPLETED, ticket_env['root'])

        # Start sprint first
        from vibey.operations.roadmap.transitions import transition_sprint
        transition_sprint(sprint.id, TicketStatus.IN_PROGRESS, ticket_env['root'])

        # Now sprint should be completable
        result = complete_item(ticket_env['root'], sprint.id)
        assert result['status'] == 'completed'
```

### Step 3: Create CLI Integration Tests (30 min)

```python
# tests/integration/test_cli_ticket_integration.py

"""
Integration tests for CLI commands using the ticket model.

Tests that CLI commands properly use criteria validation.
"""

import pytest
from click.testing import CliRunner

from vibey.cli.main import cli


class TestRoadmapStartCLI:
    """CLI tests for roadmap start command."""

    def test_start_shows_blocking_reasons(self, ticket_env, blocking_dependency):
        """CLI shows clear blocking reasons."""
        task_b = blocking_dependency['task_b']

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['roadmap', 'start', task_b.id],
            env={'VIBEY_ROOT': str(ticket_env['root'])},
        )

        assert result.exit_code != 0
        assert 'blocked' in result.output.lower() or 'cannot' in result.output.lower()

    def test_start_succeeds_when_unblocked(self, ticket_env):
        """CLI starts task when no blocking criteria."""
        from vibey.roadmap.serialization.yaml_dumper import save_task_ticket
        from vibey.roadmap.models.ticket import TaskTicket, TicketStatus

        task = TaskTicket(
            id="01UNBLOCKED01",
            name="Unblocked Task",
            status=TicketStatus.NOT_STARTED,
        )
        save_task_ticket(task, ticket_env['roadmap'])

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['roadmap', 'start', task.id],
            env={'VIBEY_ROOT': str(ticket_env['root'])},
        )

        assert result.exit_code == 0
        assert 'started' in result.output.lower()


class TestRoadmapCompleteCLI:
    """CLI tests for roadmap complete command."""

    def test_complete_shows_unmet_criteria(self, ticket_env, task_with_criteria):
        """CLI shows which criteria are unmet."""
        task = task_with_criteria['task']

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['roadmap', 'complete', task.id],
            env={'VIBEY_ROOT': str(ticket_env['root'])},
        )

        assert result.exit_code != 0
        # Should mention the blocking criterion
        assert 'output' in result.output.lower() or 'criteria' in result.output.lower()


class TestRoadmapShowCLI:
    """CLI tests for roadmap show command."""

    def test_show_displays_criteria(self, ticket_env, task_with_criteria):
        """Show command displays criteria status."""
        task = task_with_criteria['task']

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['roadmap', 'show', task.id],
            env={'VIBEY_ROOT': str(ticket_env['root'])},
        )

        assert result.exit_code == 0
        # Should show criteria section
        assert 'criteria' in result.output.lower() or 'deliverable' in result.output.lower()
```

### Step 4: Create Planned Workflow Tests (30 min)

```python
# tests/integration/test_planned_workflow.py

"""
Integration tests for the planned status workflow.

Tests the complete agent workflow for planning tickets.
"""

import pytest
from click.testing import CliRunner

from vibey.cli.main import cli


class TestPlannedCheckWorkflow:
    """Test planned check command in workflow."""

    def test_check_unplanned_task(self, ticket_env):
        """Task without YAML shows as unplanned."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['planned', 'check', '01MISSING'],
            env={'VIBEY_ROOT': str(ticket_env['root'])},
        )

        # Should indicate not planned or not found
        assert 'not planned' in result.output.lower() or result.exit_code != 0

    def test_check_planned_task(self, ticket_env):
        """Task with YAML shows as planned."""
        # Create task YAML
        yaml_path = ticket_env['roadmap'] / "tasks" / "01PLANNED01.yaml"
        yaml_path.write_text("task:\n  id: 01PLANNED01\n  name: Planned Task")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['planned', 'check', '01PLANNED01'],
            env={'VIBEY_ROOT': str(ticket_env['root'])},
        )

        assert result.exit_code == 0
        assert 'planned' in result.output.lower()


class TestPlannedApproveWorkflow:
    """Test planned approve command in workflow."""

    def test_approve_updates_metadata(self, ticket_env):
        """Approve command adds metadata to YAML."""
        import yaml

        # Create task YAML
        yaml_path = ticket_env['roadmap'] / "tasks" / "01APPROVE01.yaml"
        yaml_path.write_text("task:\n  id: 01APPROVE01\n  name: Test\n  metadata: {}")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['planned', 'approve', '01APPROVE01', '--approver', 'test-agent'],
            env={'VIBEY_ROOT': str(ticket_env['root'])},
        )

        assert result.exit_code == 0

        # Verify metadata updated
        content = yaml.safe_load(yaml_path.read_text())
        assert content['task']['metadata'].get('planned_approved') is True


class TestPlannedListUnplannedWorkflow:
    """Test list-unplanned command in workflow."""

    def test_list_finds_unplanned_tasks(self, ticket_env):
        """List command finds tasks without YAML."""
        # This test depends on database having tasks
        # May need to seed database first

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ['planned', 'list-unplanned'],
            env={'VIBEY_ROOT': str(ticket_env['root'])},
        )

        assert result.exit_code == 0


class TestFullPlanningWorkflow:
    """Test complete planning workflow."""

    def test_plan_until_done_workflow(self, ticket_env):
        """
        Simulate agent workflow:
        1. Check track planned status
        2. Get next work
        3. Do work (create files)
        4. Approve
        5. Repeat until planned
        """
        runner = CliRunner()
        env = {'VIBEY_ROOT': str(ticket_env['root'])}

        # Create a track with one unplanned task
        from vibey.roadmap.serialization.yaml_dumper import (
            save_track_ticket,
            save_sprint_ticket,
        )
        from vibey.roadmap.models.ticket import (
            TrackTicket,
            SprintTicket,
            TicketStatus,
        )
        from vibey.roadmap.models.ticket.completable import Criterion
        from vibey.roadmap.models.ticket.targets import CompletableTarget

        # Create task (no YAML initially)
        task_id = "01WORKFLOW001"

        # Create sprint with task
        sprint = SprintTicket(
            id="01WORKFLOWSPR",
            name="Workflow Sprint",
            parent_ref="01WORKFLOWTRK",
            criteria=[
                Criterion(
                    id="task-1",
                    description="Task complete",
                    target=CompletableTarget(completable_id=task_id),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        save_sprint_ticket(sprint, ticket_env['roadmap'])

        # Create track
        track = TrackTicket(
            id="01WORKFLOWTRK",
            name="Workflow Track",
            criteria=[
                Criterion(
                    id="sprint-1",
                    description="Sprint complete",
                    target=CompletableTarget(completable_id=sprint.id),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        save_track_ticket(track, ticket_env['roadmap'])

        # Step 1: Check - should be unplanned
        result = runner.invoke(cli, ['planned', 'check', track.id], env=env)
        assert 'not planned' in result.output.lower() or 'unplanned' in result.output.lower()

        # Step 2: Create task YAML (the "work")
        yaml_path = ticket_env['roadmap'] / "tasks" / f"{task_id}.yaml"
        yaml_path.write_text(f"task:\n  id: {task_id}\n  name: Workflow Task")

        # Step 3: Check again - should be planned now
        from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
        HierarchicalTicket.clear_planned_cache()

        result = runner.invoke(cli, ['planned', 'check', task_id], env=env)
        assert result.exit_code == 0
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `tests/integration/test_criteria_transitions.py` | Criteria blocking tests |
| `tests/integration/test_cli_ticket_integration.py` | CLI + ticket model tests |
| `tests/integration/test_planned_workflow.py` | Planned workflow tests |

## Files to Modify

| File | Change |
|------|--------|
| `tests/integration/conftest.py` | Add ticket model fixtures |

---

## Acceptance Criteria

- [ ] `ticket_env` fixture creates proper test environment
- [ ] `task_with_criteria` fixture creates task with completion criteria
- [ ] `blocking_dependency` fixture creates dependency chain
- [ ] Tests verify criteria block start transitions
- [ ] Tests verify criteria block complete transitions
- [ ] Tests verify CLI shows blocking reasons
- [ ] Tests verify planned workflow commands
- [ ] All new tests pass
- [ ] All existing tests still pass
- [ ] CI runs integration tests

---

## Test Coverage Targets

| Area | Tests |
|------|-------|
| Criteria blocking IN_PROGRESS | 3 tests |
| Criteria blocking COMPLETED | 3 tests |
| Sprint completion aggregation | 2 tests |
| CLI error messages | 4 tests |
| Planned workflow | 5 tests |
| **Total new tests** | **~17 tests** |

---

## Dependencies

- **Task 1** must be complete (provides `start_item`, `complete_item`)
- **Task 2** must be complete (provides `check_planned_status`)
- **Task 4** must be complete (provides `planned` CLI commands)

---

## Estimated Effort

| Step | Time |
|------|------|
| Step 1: Create fixtures | 30 min |
| Step 2: Criteria transition tests | 45 min |
| Step 3: CLI integration tests | 30 min |
| Step 4: Planned workflow tests | 30 min |
| **Total** | **~2.25 hours** |
