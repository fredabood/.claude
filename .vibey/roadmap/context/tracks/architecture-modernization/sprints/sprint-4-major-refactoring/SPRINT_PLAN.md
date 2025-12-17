# Sprint 4: Major Refactoring (Updated)

## Overview
- **Track:** Architecture Modernization
- **Sprint ID:** 01KCMTXMWJHPFH7J96KHHZTPB4
- **Tasks:** 5
- **Focus:** Wire up existing unified ticket models to CLI, add planned status workflow

## Current State Assessment

### What Already Exists

| Component | Location | Status |
|-----------|----------|--------|
| **Unified Command System** | `vibey/unified/` | Complete - decorators, registry, adapters, parity checker |
| **18 Unified Commands** | `vibey/unified/commands/` | Migrated - roadmap, docs, deploy commands |
| **Ticket Model** | `vibey/roadmap/models/ticket/ticket.py` | Complete - extends Completable |
| **Completable Base** | `vibey/roadmap/models/ticket/completable.py` | Complete - criteria, can_transition_to() |
| **9 Criterion Targets** | `vibey/roadmap/models/ticket/targets.py` | Complete - see list below |
| **Hierarchy Management** | `vibey/roadmap/models/ticket/hierarchical.py` | Complete |
| **ORM Models** | `vibey/roadmap/models/ticket/orm.py` | Complete |
| **Repository Layer** | `vibey/roadmap/models/ticket/repository.py` | Complete |
| **265 Integration Tests** | `tests/integration/` | Exist but may not cover new models |

**Existing Criterion Target Types:**
1. `CompletableTarget` - Another completable must reach status
2. `FileExistsTarget` - File(s) must exist
3. `TestPassesTarget` - Test command must pass
4. `TestCoverageTarget` - Coverage threshold
5. `ThresholdTarget` - Generic metric threshold
6. `ManualTarget` - Human approval required
7. `ExternalTarget` - External system check
8. `ArtifactTarget` - Artifact state check

### What Does NOT Exist

1. **PlannedCriterion** - Composite criterion for "planned" status
2. **`vibey planned` command group** - CLI commands for planned workflow
3. **Wiring** - New ticket models not integrated with existing CLI
4. **CLI-to-new-model integration tests** - Tests for new architecture

---

## Revised Task Breakdown

### Task 1: Wire Unified Ticket Models to CLI
**ID:** `01KCMMFTTPM8JA1GFD4QQA23VT`
**Priority:** High | **Complexity:** Medium | **Type:** Development

#### Problem
The new `Ticket`, `Completable`, and `Criterion` models exist but aren't used by the CLI. The CLI still uses the old `Track`, `Sprint`, `Task` models directly.

#### Actual Work Required
1. Create adapter layer to bridge old CLI → new models:
   ```python
   # vibey/roadmap/models/ticket/adapters.py (may already exist)

   def task_to_ticket(task: Task) -> Ticket:
       """Convert legacy Task to unified Ticket."""
       ...

   def ticket_to_task(ticket: Ticket) -> Task:
       """Convert unified Ticket back to legacy Task."""
       ...
   ```

2. Update key CLI operations to use new models:
   - `roadmap start` → use `Ticket.start()`
   - `roadmap complete` → use `Ticket.complete()`
   - `roadmap show` → display criteria status

3. Add criterion display to CLI output:
   ```
   Task: 01KCMGZB4G0322MRJZ8VX3KYM8
   Status: in_progress

   Criteria for COMPLETED:
     ✓ Code implementation complete
     ○ Tests passing (3/5 passing)
     ○ Documentation updated
   ```

#### Files to Modify
- `vibey/operations/roadmap/transitions.py` - Use Ticket model
- `vibey/cli/roadmap_lib/formatting.py` - Display criteria
- `vibey/unified/commands/roadmap.py` - Update unified commands

#### Acceptance Criteria
- [ ] `roadmap start` uses `Ticket.can_start()` for blocking checks
- [ ] `roadmap complete` uses `Ticket.can_complete()` for criteria checks
- [ ] `roadmap show` displays criteria status
- [ ] Backward compatible with existing YAML format

---

### Task 2: Implement PlannedCriterion Composite
**ID:** `01KCMNP21ZPJMABMKHJYDQD7RR`
**Priority:** High | **Complexity:** Simple | **Type:** Development

#### Problem
Need a composite criterion that checks if a ticket is "planned" (ready for work).

#### Actual Work Required
The individual targets already exist! Just need to compose them:

```python
# vibey/roadmap/criteria/planned.py (NEW)

from vibey.roadmap.models.ticket.completable import Criterion
from vibey.roadmap.models.ticket.targets import (
    FileExistsTarget,
    ManualTarget,
)
from vibey.roadmap.models.ticket.enums import TicketStatus

def create_planned_criteria(ticket_id: str, paths: RoadmapPaths) -> list[Criterion]:
    """Create standard criteria for 'planned' status."""
    return [
        Criterion(
            id=f"{ticket_id}-yaml-exists",
            description="YAML file exists",
            blocks_transition_to=TicketStatus.IN_PROGRESS,
            target=FileExistsTarget(
                path=str(paths.get_task_path(ticket_id)),
                exists=True,
            ),
        ),
        Criterion(
            id=f"{ticket_id}-context-exists",
            description="Context/task plan exists",
            blocks_transition_to=TicketStatus.IN_PROGRESS,
            target=FileExistsTarget(
                path=str(paths.get_context_path(ticket_id)),
                exists=True,
            ),
            required=False,  # Optional - not all tasks need context
        ),
        Criterion(
            id=f"{ticket_id}-approved",
            description="Planning approved",
            blocks_transition_to=TicketStatus.IN_PROGRESS,
            target=ManualTarget(
                approved=False,
                approver=None,
            ),
            required=False,  # Optional manual approval
        ),
    ]
```

#### Files to Create
- `vibey/roadmap/criteria/__init__.py`
- `vibey/roadmap/criteria/planned.py`

#### Acceptance Criteria
- [ ] PlannedCriterion uses existing target types
- [ ] Configurable which checks are required vs optional
- [ ] Unit tests for criterion composition

---

### Task 3: Update Hierarchical Aggregation for Planned Status
**ID:** `01KCMNPC039DG15PZT0QHMTBCV`
**Priority:** Medium | **Complexity:** Simple | **Type:** Development

#### Problem
The `hierarchical.py` exists but may not aggregate "planned" status up the hierarchy.

#### Actual Work Required
1. Verify `hierarchical.py` handles planned status aggregation
2. Add `is_planned` computed property if missing:
   ```python
   @computed_field
   @property
   def is_planned(self) -> bool:
       """Check if ticket is planned (all planning criteria met)."""
       # For leaf tickets: check planning criteria
       # For parent tickets: all children must be planned
       if self.is_leaf:
           return self._check_planning_criteria()
       return all(child.is_planned for child in self.children)
   ```

3. Add caching via database trigger or computed column

#### Files to Modify
- `vibey/roadmap/models/ticket/ticket.py` - Add is_planned property
- `vibey/roadmap/models/ticket/hierarchical.py` - Aggregation logic

#### Acceptance Criteria
- [ ] `ticket.is_planned` returns correct value for leaf tickets
- [ ] Parent `is_planned` aggregates from children
- [ ] Performance acceptable (caching if needed)

---

### Task 4: Add `planned` CLI Command Group
**ID:** `01KCMNPQQ8ETYF2X4N5WP95ENG`
**Priority:** High | **Complexity:** Medium | **Type:** Development

#### Problem
No CLI commands exist for checking or managing "planned" status.

#### Actual Work Required
Create new unified commands for planned workflow:

```python
# vibey/unified/commands/planned.py (NEW)

@unified_command(
    name="planned_check",
    description="Check if a ticket is fully planned",
    cli_group="planned",
    cli_name="check",
    mcp_name="vibey_planned_check",
)
@param("ticket_id", type=ParamType.STRING, required=True)
def planned_check(ticket_id: str, root_dir=None) -> CommandResult:
    """Check planned status of a ticket."""
    ...

@unified_command(
    name="planned_approve",
    description="Manually approve a ticket's planning",
    cli_group="planned",
    cli_name="approve",
    mcp_name="vibey_planned_approve",
)
@param("ticket_id", type=ParamType.STRING, required=True)
def planned_approve(ticket_id: str, root_dir=None) -> CommandResult:
    """Approve planned status for a ticket."""
    ...

@unified_command(
    name="planned_list_unplanned",
    description="List tickets that are not yet planned",
    cli_group="planned",
    cli_name="list-unplanned",
    mcp_name="vibey_list_unplanned",
)
@param("scope", type=ParamType.STRING, default="all")
def planned_list_unplanned(scope: str = "all", root_dir=None) -> CommandResult:
    """List unplanned tickets in scope."""
    ...

@unified_command(
    name="planned_next_work",
    description="Get next planning work item for a track",
    cli_group="planned",
    cli_name="next",
    mcp_name="vibey_planned_next",
)
@param("track_id", type=ParamType.STRING, required=True)
def planned_next_work(track_id: str, root_dir=None) -> CommandResult:
    """Get next ticket that needs planning work."""
    ...
```

#### Files to Create
- `vibey/unified/commands/planned.py`
- `vibey/operations/roadmap/planned_ops.py`

#### Files to Modify
- `vibey/cli/main.py` - Register planned command group
- `vibey/unified/commands/__init__.py` - Export new commands

#### Acceptance Criteria
- [ ] `vibey planned check <id>` shows criteria status
- [ ] `vibey planned approve <id>` marks manual approval
- [ ] `vibey planned list-unplanned` shows unplanned tickets
- [ ] `vibey planned next <track>` suggests next planning work
- [ ] MCP tools mirror CLI commands

---

### Task 5: Add Integration Tests for New Architecture
**ID:** `01KCMGZTMA1HC7GS44AB9D2VS1`
**Priority:** High | **Complexity:** Medium | **Type:** Testing

#### Problem
265 integration tests exist but may not cover the new unified ticket models.

#### Actual Work Required
Add tests specifically for:
1. Ticket model ↔ YAML serialization round-trip
2. CLI commands using new Ticket model
3. Criteria evaluation during transitions
4. Planned status workflow end-to-end

```python
# tests/integration/test_unified_ticket_flow.py (NEW)

def test_start_task_checks_criteria(roadmap_env):
    """Starting a task should check IN_PROGRESS criteria."""
    # Create task with blocking dependency
    # Attempt to start - should fail
    # Complete dependency
    # Start should now succeed

def test_complete_task_checks_criteria(roadmap_env):
    """Completing a task should check COMPLETED criteria."""
    # Create task with completion criteria
    # Attempt to complete - should fail
    # Satisfy criteria
    # Complete should now succeed

def test_planned_status_aggregation(roadmap_env):
    """Parent planned status should aggregate from children."""
    # Create track with sprints and tasks
    # Check track.is_planned = False
    # Plan all tasks
    # Check track.is_planned = True
```

#### Files to Create
- `tests/integration/test_unified_ticket_flow.py`
- `tests/integration/test_planned_workflow.py`
- `tests/integration/test_criteria_evaluation.py`

#### Acceptance Criteria
- [ ] Tests cover Ticket model serialization
- [ ] Tests cover criteria-based transitions
- [ ] Tests cover planned status aggregation
- [ ] Tests cover planned CLI commands
- [ ] All new tests pass in CI

---

## Sprint Completion Checklist

- [ ] Task 1: CLI wired to use Ticket model for transitions
- [ ] Task 2: PlannedCriterion composite created
- [ ] Task 3: Hierarchical planned aggregation working
- [ ] Task 4: `vibey planned` command group available
- [ ] Task 5: Integration tests for new architecture passing
- [ ] All existing tests still pass
- [ ] MCP tools have parity with CLI commands
- [ ] Documentation updated

## Dependencies

- **Sprint 3 (completed):** Code cleanup, commands.py split
- **Sprint 2 (completed):** Architecture designs

## Risks

1. **Breaking changes** - Wiring new models may break existing functionality
   - Mitigation: Extensive integration tests, feature flags if needed

2. **Performance** - Criteria evaluation may be slow
   - Mitigation: Caching, database triggers for computed values

## Estimated Complexity

| Task | Original Estimate | Revised Estimate | Reason |
|------|-------------------|------------------|--------|
| Task 1 | Complex | Medium | Much exists, just needs wiring |
| Task 2 | Complex | Simple | Targets already exist, just compose |
| Task 3 | Medium | Simple | hierarchical.py exists |
| Task 4 | Medium | Medium | Still needs full implementation |
| Task 5 | Complex | Medium | Test patterns exist, adapt them |
