# Sprint 4: Major Refactoring

## Overview
- **Track:** Architecture Modernization
- **Sprint ID:** 01KCMTXMWJHPFH7J96KHHZTPB4
- **Tasks:** 5
- **Focus:** Implement CLI refactor, planned status system, and integration tests

## Success Criteria
- [ ] CLI aligned with semantic layer architecture
- [ ] Planned status criterion system operational
- [ ] Integration tests covering CLI-Database flow
- [ ] All refactoring from Sprint 2 designs implemented

---

## Task 1: Implement CLI Refactor for Semantic Layer Alignment
**ID:** `01KCMMFTTPM8JA1GFD4QQA23VT`
**Priority:** High | **Complexity:** Complex | **Type:** Development

### Problem
Execute the CLI refactor designed in Sprint 2 to align with unified ticket architecture.

### Prerequisites
- Sprint 2 Task 4: CLI refactor design complete
- Sprint 3: Code cleanup complete

### Implementation Steps
1. Create new command structure:
   ```python
   # vibey/cli/commands/ticket.py

   import click
   from vibey.operations.roadmap import ticket_ops

   @click.group()
   def ticket():
       """Work item management (unified ticket commands)."""
       pass

   @ticket.command('list')
   @click.option('--type', type=click.Choice(['track', 'sprint', 'task', 'all']))
   @click.option('--status', type=click.Choice(['not_started', 'in_progress', 'completed']))
   def list_tickets(type, status):
       """List tickets (tracks, sprints, tasks)."""
       tickets = ticket_ops.list_tickets(type_filter=type, status_filter=status)
       for t in tickets:
           click.echo(f"{t.id} [{t.type}] {t.title} ({t.status})")

   @ticket.command('show')
   @click.argument('id')
   def show_ticket(id):
       """Show ticket details."""
       ticket = ticket_ops.get_ticket(id)
       click.echo(format_ticket(ticket))

   @ticket.command('start')
   @click.argument('id')
   def start_ticket(id):
       """Start working on a ticket."""
       ticket_ops.start_ticket(id)
       click.echo(f"Started ticket {id}")

   @ticket.command('complete')
   @click.argument('id')
   def complete_ticket(id):
       """Mark a ticket as complete."""
       ticket_ops.complete_ticket(id)
       click.echo(f"Completed ticket {id}")
   ```

2. Create criteria commands:
   ```python
   # vibey/cli/commands/criteria.py

   @click.group()
   def criteria():
       """Completion criteria management."""
       pass

   @criteria.command('list')
   @click.argument('ticket_id')
   def list_criteria(ticket_id):
       """List completion criteria for a ticket."""
       criteria = criteria_ops.list_for_ticket(ticket_id)
       for c in criteria:
           status = "✓" if c.met else "○"
           click.echo(f"{status} {c.description}")

   @criteria.command('check')
   @click.argument('ticket_id')
   def check_criteria(ticket_id):
       """Evaluate all criteria for a ticket."""
       results = criteria_ops.evaluate_all(ticket_id)
       for r in results:
           click.echo(f"{r.criterion}: {r.status}")
   ```

3. Add backward compatibility aliases:
   ```python
   # vibey/cli/main.py

   # Legacy aliases for transition
   cli.add_command(ticket.commands['list'], name='roadmap-list')

   # Deprecation warnings
   def deprecated_command(new_cmd):
       def wrapper(f):
           @functools.wraps(f)
           def inner(*args, **kwargs):
               click.echo(f"Warning: This command is deprecated. Use '{new_cmd}' instead.", err=True)
               return f(*args, **kwargs)
           return inner
       return wrapper
   ```

4. Update MCP tools to match:
   ```python
   # Ensure MCP tools mirror CLI structure
   @mcp_tool
   def ticket_list(type_filter: str = None, status_filter: str = None):
       """List tickets (maps to: vibey ticket list)."""
       return ticket_ops.list_tickets(type_filter, status_filter)
   ```

### Files to Create/Modify
- `vibey/cli/commands/ticket.py` (new)
- `vibey/cli/commands/criteria.py` (new)
- `vibey/cli/commands/artifact.py` (new)
- `vibey/operations/roadmap/ticket_ops.py` (new)
- `vibey/cli/main.py` (modify)
- `vibey/mcp/tools/ticket_tools.py` (new)

### Acceptance Criteria
- [ ] New ticket commands implemented
- [ ] Legacy commands aliased
- [ ] MCP tools updated for parity
- [ ] All tests pass

---

## Task 2: Implement Planned Criterion Targets
**ID:** `01KCMNP21ZPJMABMKHJYDQD7RR`
**Priority:** High | **Complexity:** Complex | **Type:** Development

### Problem
Implement the criterion targets designed in Sprint 2 for planned status evaluation.

### Implementation Steps
1. Create base criterion framework:
   ```python
   # vibey/roadmap/criteria/base.py

   from abc import ABC, abstractmethod
   from dataclasses import dataclass
   from typing import Optional

   @dataclass
   class CriterionResult:
       passed: bool
       message: str
       details: Optional[dict] = None

   class CriterionTarget(ABC):
       """Base class for criterion evaluation targets."""

       @abstractmethod
       def evaluate(self, ticket_id: str) -> CriterionResult:
           """Evaluate if this target is met for the given ticket."""
           pass
   ```

2. Implement FileExistsTarget:
   ```python
   # vibey/roadmap/criteria/targets.py

   class FileExistsTarget(CriterionTarget):
       """Check if YAML file exists for ticket."""

       def __init__(self, paths: RoadmapPaths):
           self.paths = paths

       def evaluate(self, ticket_id: str) -> CriterionResult:
           # Determine entity type from ULID prefix patterns
           yaml_path = self._get_path(ticket_id)
           exists = yaml_path.exists()

           return CriterionResult(
               passed=exists,
               message=f"YAML file {'exists' if exists else 'missing'}",
               details={"path": str(yaml_path)}
           )
   ```

3. Implement DatabaseRecordTarget:
   ```python
   class DatabaseRecordTarget(CriterionTarget):
       """Check if ticket exists in database."""

       def __init__(self, db_path: Path):
           self.db_path = db_path

       def evaluate(self, ticket_id: str) -> CriterionResult:
           exists = self._check_db_record(ticket_id)

           return CriterionResult(
               passed=exists,
               message=f"Database record {'found' if exists else 'missing'}",
               details={"ticket_id": ticket_id}
           )
   ```

4. Implement ContextFileExistsTarget:
   ```python
   class ContextFileExistsTarget(CriterionTarget):
       """Check if context directory/files exist."""

       def evaluate(self, ticket_id: str) -> CriterionResult:
           context_dir = self._get_context_dir(ticket_id)
           has_context = context_dir.exists() and any(context_dir.iterdir())

           return CriterionResult(
               passed=has_context,
               message=f"Context files {'present' if has_context else 'missing'}",
               details={"context_dir": str(context_dir)}
           )
   ```

5. Implement ManualApprovalTarget:
   ```python
   class ManualApprovalTarget(CriterionTarget):
       """Check if user has manually approved planned status."""

       def evaluate(self, ticket_id: str) -> CriterionResult:
           ticket = self._load_ticket(ticket_id)
           approved = ticket.metadata.get('planned_approved', False)

           return CriterionResult(
               passed=approved,
               message=f"Manual approval: {'yes' if approved else 'pending'}",
               details={"ticket_id": ticket_id}
           )
   ```

6. Compose into PlannedCriterion:
   ```python
   # vibey/roadmap/criteria/planned.py

   class PlannedCriterion:
       """Composite criterion for planned status."""

       def __init__(self, paths: RoadmapPaths, db_path: Path):
           self.targets = [
               FileExistsTarget(paths),
               DatabaseRecordTarget(db_path),
               ContextFileExistsTarget(paths),
               ManualApprovalTarget(),
           ]

       def evaluate(self, ticket_id: str) -> CriterionResult:
           results = [t.evaluate(ticket_id) for t in self.targets]
           all_passed = all(r.passed for r in results)

           return CriterionResult(
               passed=all_passed,
               message=f"Planned: {sum(r.passed for r in results)}/{len(results)} targets met",
               details={"targets": [r.message for r in results]}
           )
   ```

### Acceptance Criteria
- [ ] All 4 target types implemented
- [ ] PlannedCriterion composes targets
- [ ] Unit tests for each target
- [ ] Integration with ticket model

---

## Task 3: Implement Hierarchical Planned Status Aggregation
**ID:** `01KCMNPC039DG15PZT0QHMTBCV`
**Priority:** High | **Complexity:** Medium | **Type:** Development

### Problem
Parent ticket planned status should aggregate from children.

### Implementation Steps
1. Add planned property to ticket model:
   ```python
   # vibey/roadmap/models/ticket.py

   class Ticket(BaseModel):
       # ... existing fields

       @property
       def is_planned(self) -> bool:
           """Check if ticket is planned (recursive for parents)."""
           if self.is_leaf:
               return self._evaluate_planned_criterion()
           else:
               return all(child.is_planned for child in self.children)

       def _evaluate_planned_criterion(self) -> bool:
           criterion = PlannedCriterion(self._paths, self._db_path)
           return criterion.evaluate(self.id).passed
   ```

2. Add caching for efficiency:
   ```python
   @functools.lru_cache(maxsize=1000)
   def get_planned_status(ticket_id: str) -> bool:
       """Cached planned status lookup."""
       ticket = load_ticket(ticket_id)
       return ticket.is_planned
   ```

3. Add database trigger for denormalization:
   ```sql
   -- Optional: Store computed planned status
   ALTER TABLE tickets ADD COLUMN planned_status BOOLEAN DEFAULT FALSE;

   -- Update on changes
   CREATE TRIGGER update_planned_status
   AFTER UPDATE ON tickets
   BEGIN
       -- Recalculate for affected tickets
   END;
   ```

4. Add CLI for planned status queries:
   ```python
   @ticket.command('planned')
   @click.argument('id')
   def check_planned(id):
       """Check planned status of ticket."""
       ticket = ticket_ops.get_ticket(id)
       result = ticket.is_planned

       if result:
           click.echo(f"✓ Ticket {id} is fully planned")
       else:
           click.echo(f"○ Ticket {id} is not fully planned")
           # Show which criteria failed
   ```

### Acceptance Criteria
- [ ] Hierarchical aggregation works
- [ ] Caching for performance
- [ ] CLI command available
- [ ] Tests for edge cases

---

## Task 4: Add CLI/MCP Commands for Planned Status Workflow
**ID:** `01KCMNPQQ8ETYF2X4N5WP95ENG`
**Priority:** Medium | **Complexity:** Medium | **Type:** Development

### Problem
Need commands to manage and query planned status for agent workflow.

### Implementation Steps
1. Add planned status commands:
   ```python
   # vibey/cli/commands/planned.py

   @click.group()
   def planned():
       """Planned status workflow commands."""
       pass

   @planned.command('check')
   @click.argument('id')
   def check_planned(id):
       """Check if a ticket is planned."""
       result = planned_ops.check(id)
       click.echo(format_planned_result(result))

   @planned.command('approve')
   @click.argument('id')
   def approve_planned(id):
       """Manually approve planned status for ticket."""
       planned_ops.approve(id)
       click.echo(f"Approved planned status for {id}")

   @planned.command('list-unplanned')
   @click.option('--scope', default='all')
   def list_unplanned(scope):
       """List all unplanned tickets."""
       unplanned = planned_ops.list_unplanned(scope)
       for ticket in unplanned:
           click.echo(f"{ticket.id} {ticket.title}")

   @planned.command('work-until-planned')
   @click.argument('track_id')
   def work_until_planned(track_id):
       """Show work remaining until track is fully planned."""
       remaining = planned_ops.get_planning_work(track_id)
       click.echo(f"Remaining planning work for {track_id}:")
       for item in remaining:
           click.echo(f"  - {item.ticket_id}: {item.missing_criteria}")
   ```

2. Add MCP tools for agent workflow:
   ```python
   # vibey/mcp/tools/planned_tools.py

   @mcp_tool
   def planned_check(ticket_id: str) -> dict:
       """Check planned status of a ticket."""
       result = planned_ops.check(ticket_id)
       return {
           "planned": result.is_planned,
           "criteria_met": result.criteria_met,
           "criteria_total": result.criteria_total,
           "missing": result.missing_criteria,
       }

   @mcp_tool
   def planned_list_unplanned(scope: str = "all") -> list:
       """List all unplanned tickets in scope."""
       return [
           {"id": t.id, "title": t.title, "type": t.type}
           for t in planned_ops.list_unplanned(scope)
       ]

   @mcp_tool
   def planned_get_next_work(track_id: str) -> dict:
       """Get next planning work item for a track."""
       work = planned_ops.get_next_planning_work(track_id)
       return {
           "ticket_id": work.ticket_id,
           "action": work.required_action,
           "details": work.details,
       }
   ```

3. Agent workflow example:
   ```markdown
   ## Agent Workflow: Plan Until Done

   1. Check track planned status: `vibey planned check <track_id>`
   2. If not planned:
      a. Get next work item: `vibey planned work-until-planned <track_id>`
      b. Complete planning task (create context, add details)
      c. Approve if ready: `vibey planned approve <ticket_id>`
      d. Repeat from step 1
   3. Track is fully planned, ready for implementation
   ```

### Acceptance Criteria
- [ ] CLI commands for planned workflow
- [ ] MCP tools mirror CLI
- [ ] Agent can drive planning workflow
- [ ] Documentation with examples

---

## Task 5: Add Integration Tests for CLI-Database Flow
**ID:** `01KCMGZTMA1HC7GS44AB9D2VS1`
**Priority:** High | **Complexity:** Complex | **Type:** Testing

### Problem
Need integration tests for complete user flows: CLI -> Operations -> YAML/SQLite sync.

### Implementation Steps
1. Create integration test fixtures:
   ```python
   # tests/integration/conftest.py

   import pytest
   from pathlib import Path
   import tempfile

   @pytest.fixture
   def roadmap_env(tmp_path):
       """Create isolated roadmap environment for testing."""
       roadmap_dir = tmp_path / ".vibey" / "roadmap"
       roadmap_dir.mkdir(parents=True)

       # Create minimal structure
       (roadmap_dir / "tracks").mkdir()
       (roadmap_dir / "sprints").mkdir()
       (roadmap_dir / "tasks").mkdir()

       # Initialize database
       db_path = roadmap_dir / "roadmap.db"

       yield {
           "root": tmp_path,
           "roadmap": roadmap_dir,
           "db": db_path,
       }
   ```

2. Test CLI -> YAML -> Database flow:
   ```python
   # tests/integration/test_cli_database_flow.py

   from click.testing import CliRunner
   from vibey.cli.main import cli

   def test_create_track_flow(roadmap_env):
       """Test creating track updates both YAML and database."""
       runner = CliRunner()

       # Create track via CLI
       result = runner.invoke(cli, [
           'roadmap', 'create-track',
           '--name', 'Test Track',
           '--roadmap-id', 'test-roadmap'
       ], env={'VIBEY_ROADMAP_PATH': str(roadmap_env['roadmap'])})

       assert result.exit_code == 0
       track_id = extract_id_from_output(result.output)

       # Verify YAML created
       yaml_path = roadmap_env['roadmap'] / 'tracks' / f'{track_id}.yaml'
       assert yaml_path.exists()

       # Verify database record
       result = runner.invoke(cli, ['roadmap', 'db', 'status'])
       assert track_id in result.output

   def test_update_task_flow(roadmap_env, sample_task):
       """Test updating task syncs YAML and database."""
       runner = CliRunner()

       # Update task status
       result = runner.invoke(cli, [
           'roadmap', 'start', sample_task.id
       ])
       assert result.exit_code == 0

       # Verify YAML updated
       yaml_content = load_yaml(roadmap_env['roadmap'] / 'tasks' / f'{sample_task.id}.yaml')
       assert yaml_content['task']['status'] == 'in_progress'

       # Verify database updated
       db_task = query_database(roadmap_env['db'], sample_task.id)
       assert db_task['status'] == 'in_progress'
   ```

3. Test error handling flows:
   ```python
   def test_invalid_id_error(roadmap_env):
       """Test invalid ID produces proper error."""
       runner = CliRunner()

       result = runner.invoke(cli, [
           'roadmap', 'show', 'invalid-id'
       ])

       assert result.exit_code != 0
       assert 'Invalid ID' in result.output or 'not found' in result.output

   def test_database_rebuild_after_yaml_edit(roadmap_env, sample_track):
       """Test database reflects external YAML edits after rebuild."""
       # Edit YAML directly
       yaml_path = roadmap_env['roadmap'] / 'tracks' / f'{sample_track.id}.yaml'
       content = yaml_path.read_text()
       content = content.replace('name: Old Name', 'name: New Name')
       yaml_path.write_text(content)

       # Rebuild database
       runner = CliRunner()
       result = runner.invoke(cli, ['roadmap', 'db', 'rebuild'])
       assert result.exit_code == 0

       # Verify database updated
       result = runner.invoke(cli, ['roadmap', 'show', sample_track.id])
       assert 'New Name' in result.output
   ```

4. Test concurrent operations:
   ```python
   def test_concurrent_updates(roadmap_env, sample_tasks):
       """Test concurrent updates don't corrupt data."""
       import concurrent.futures

       def update_task(task_id):
           runner = CliRunner()
           return runner.invoke(cli, ['roadmap', 'update', task_id, '--priority', 'high'])

       with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
           futures = [executor.submit(update_task, t.id) for t in sample_tasks]
           results = [f.result() for f in futures]

       # All should succeed or fail gracefully
       assert all(r.exit_code in [0, 1] for r in results)

       # Database should be consistent
       runner = CliRunner()
       result = runner.invoke(cli, ['roadmap', 'db', 'validate'])
       assert result.exit_code == 0
   ```

### Files to Create
- `tests/integration/__init__.py`
- `tests/integration/conftest.py`
- `tests/integration/test_cli_database_flow.py`
- `tests/integration/test_cli_error_handling.py`
- `tests/integration/test_yaml_sqlite_sync.py`

### Acceptance Criteria
- [ ] Integration test suite created
- [ ] CLI -> Operations -> Storage flows tested
- [ ] Error handling tested
- [ ] Concurrent operations tested
- [ ] CI runs integration tests

---

## Sprint Completion Checklist
- [ ] CLI refactor implemented
- [ ] Planned criterion targets implemented
- [ ] Hierarchical aggregation working
- [ ] Planned workflow commands added
- [ ] Integration tests passing
- [ ] MCP parity maintained
- [ ] Documentation updated
