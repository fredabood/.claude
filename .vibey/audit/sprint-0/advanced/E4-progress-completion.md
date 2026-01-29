# E4: Progress/Completion Flow Audit

**Task ID:** 01KFXGP643VEBH931RT7RQ195H
**Phase:** E4: Advanced
**Date:** 2026-01-29

## Executive Summary

The Vibey progress and completion flow uses a criteria-based transition system where status changes require validation via `can_transition_to()`. The `transitions.py` module provides centralized status transition logic using the unified ticket architecture, while `StatusManager` handles optional auto-progression. Key finding: Progress tracking translates cleanly to remote mode - criteria evaluation can be delegated to Delta Lake queries, and status changes can be queued for offline scenarios.

**Key Statistics:**
- 6 supported ticket statuses
- 4 entity types (task, sprint, track, roadmap)
- 3 transition functions (transition_task, transition_sprint, transition_track)
- Auto-progression with 2 modes (check, apply)

## Progress Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PROGRESS/COMPLETION FLOW                          │
└─────────────────────────────────────────────────────────────────────┘

  USER ACTION                          SYSTEM RESPONSE
  ───────────                          ───────────────

┌─────────────────┐                 ┌─────────────────┐
│ vibey roadmap   │────────────────▶│ transition_*()  │
│ complete <id>   │                 │                 │
└─────────────────┘                 └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ load_*_ticket() │
                                    │ (Query module)  │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ can_transition_ │
                                    │ to(status)      │
                                    │ - Check criteria │
                                    │ - Return blockers │
                                    └────────┬────────┘
                                             │
                               ┌─────────────┼─────────────┐
                               │             │             │
                           BLOCKED       ALLOWED      PARTIAL
                               │             │             │
                               ▼             ▼             ▼
                          ┌─────────┐  ┌─────────┐  ┌─────────┐
                          │ Raise   │  │ Apply   │  │ Show    │
                          │ Blocked │  │ ticket  │  │ Missing │
                          │ Error   │  │ .start()│  │ Criteria│
                          └─────────┘  │ .compl()│  └─────────┘
                                       └────┬────┘
                                            │
                                    ┌───────▼────────┐
                                    │ save_*_ticket()│
                                    │ (YAML dumper)  │
                                    └────────────────┘
```

## Status Transition Table

| From Status | To Status | Validation | Method |
|-------------|-----------|------------|--------|
| `not_started` | `in_progress` | `can_transition_to()` | `ticket.start()` |
| `in_progress` | `completed` | `can_transition_to()` | `ticket.complete()` |
| `in_progress` | `blocked` | None | `model_copy(status=BLOCKED)` |
| `any` | `deferred` | None | `model_copy(status=DEFERRED)` |
| `completed` | `not_started` | Admin override | `model_copy(status=NOT_STARTED)` |

## Transition Functions Table

| Function | Entity Type | File | Parameters |
|----------|-------------|------|------------|
| `transition_ticket()` | Any HierarchicalTicket | transitions.py | ticket, target_status |
| `transition_task()` | TaskTicket | transitions.py | task_id, target_status, root_dir, save |
| `transition_sprint()` | SprintTicket | transitions.py | sprint_id, target_status, root_dir, save |
| `transition_track()` | TrackTicket | transitions.py | track_id, target_status, root_dir, save |

## TransitionBlockedError

| Attribute | Type | Purpose |
|-----------|------|---------|
| `entity_id` | str | ID of entity that couldn't transition |
| `target_status` | TicketStatus | Target status that was blocked |
| `reasons` | List[str] | Human-readable blocking reasons |

## Criteria-Based Blocking

### can_transition_to() Method

```python
def can_transition_to(self, target_status: TicketStatus) -> Tuple[bool, List[str]]:
    """
    Check if ticket can transition to target status.

    Returns:
        (can_transition, blocking_reasons)
        - can_transition: True if all criteria met
        - blocking_reasons: List of reasons why blocked
    """
```

### Blocking Criteria Types

| Criteria Type | blocks_transition_to | Description |
|---------------|---------------------|-------------|
| `in_progress` | Cannot start | Dependencies must complete first |
| `completed` | Cannot complete | Success criteria must be met |
| `production_ready` | Cannot deploy | Production gates must pass |

## Auto-Progression Configuration

### Config File: `.vibey/config/roadmap.yaml`

```yaml
auto_progression:
  enabled: true/false
  mode: check/apply
  transitions:
    - from: not_started
      to: in_progress
      when: all_start_criteria_met
    - from: in_progress
      to: completed
      when: all_completion_criteria_met
  propagate_up: true
  log_to_audit: true
```

## StatusManager Class

| Method | Purpose | Parameters |
|--------|---------|------------|
| `__init__()` | Initialize with root_dir | root_dir: Path |
| `is_enabled()` | Check if auto-progression enabled | None |
| `get_mode()` | Get mode (check/apply) | None |
| `check_progressions()` | Dry-run check | ticket_ids: Optional[List] |
| `apply_progressions()` | Apply auto-progressions | ticket_ids: Optional[List] |

### ProgressionResult

| Attribute | Type | Purpose |
|-----------|------|---------|
| `ticket_id` | str | Ticket ULID |
| `ticket_type` | str | task, sprint, track |
| `ticket_name` | str | Human-readable name |
| `old_status` | str | Status before change |
| `new_status` | str | Status after change |
| `applied` | bool | True if actually changed |
| `reason` | str | Why progression triggered |

## Progress Rollup Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PROGRESS ROLLUP FLOW                            │
└─────────────────────────────────────────────────────────────────────┘

  TASK                    SPRINT                   TRACK
  ────                    ──────                   ─────

┌──────────┐           ┌──────────┐           ┌──────────┐
│ Task 1   │──────────▶│          │           │          │
│ COMPLETED│           │ Sprint   │──────────▶│ Track    │
├──────────┤           │          │           │          │
│ Task 2   │──────────▶│ Progress │           │ Progress │
│ COMPLETED│           │ = 66%    │           │ = 50%    │
├──────────┤           │          │           │          │
│ Task 3   │──────────▶│          │           │          │
│ IN_PROG  │           │          │           │          │
└──────────┘           └──────────┘           └──────────┘

Progress Calculation:
- Sprint: completed_tasks / total_tasks * 100
- Track: completed_sprints / total_sprints * 100
- Roadmap: completed_tracks / total_tracks * 100
```

## Completion Validation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                   COMPLETION VALIDATION FLOW                         │
└─────────────────────────────────────────────────────────────────────┘

1. User: vibey roadmap complete task-123

2. System: Load TaskTicket from YAML
   └── task_ticket = load_task_ticket(root_dir, task_id)

3. System: Check transition criteria
   └── can_transition, blockers = task_ticket.can_transition_to(COMPLETED)

4. If blocked:
   └── raise TransitionBlockedError(task_id, COMPLETED, blockers)
       │
       └── Display: "Cannot complete: [blockers]"

5. If allowed:
   ├── updated_ticket = task_ticket.complete()
   │   └── Sets status=COMPLETED, completed=datetime.now()
   ├── save_task_ticket_yaml(updated_ticket, task_path)
   └── auto_generate_on_complete(task_id)  # Post-mortem
```

## Post-Completion Actions

| Action | Trigger | Module | Optional |
|--------|---------|--------|----------|
| **Post-Mortem Generation** | Task completion | `context.post_mortem` | Yes |
| **Parent Progress Update** | Child completion | Computed views | Automatic |
| **Activity Log Entry** | Any transition | `activity_log.py` | Configurable |
| **Audit Trail Entry** | Status change | `audit_trail.py` | Configurable |

## Remote Mode Translation Table

| Local Concept | Remote Equivalent | Transformation |
|---------------|-------------------|----------------|
| `can_transition_to()` | Remote criteria query | Delta Lake SQL |
| `transition_task()` | Remote status update | REST API call |
| Auto-progression | Server-side scheduler | Databricks job |
| Progress rollup | Delta Lake view | Aggregation view |
| Blocking criteria | Remote criteria table | Delta table query |
| Post-mortem | Remote artifact storage | Delta + blob storage |

## Remote Progress Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                   REMOTE PROGRESS ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────────────┘

  LOCAL                                REMOTE (DATABRICKS)
  ─────                                ───────────────────

┌─────────────────┐                 ┌─────────────────┐
│ complete_task() │────── HTTPS ───▶│ /api/transition │
│                 │                 │                 │
└─────────────────┘                 └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ Check Criteria  │
                                    │ (Delta Query)   │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ Update Status   │
                                    │ (Delta MERGE)   │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ Refresh Views   │
                                    │ (Progress)      │
                                    └─────────────────┘

  OFFLINE MODE:
  ┌─────────────────┐
  │ Offline Queue   │
  │ - action: COMPLETE
  │ - task_id: xxx  │
  │ - timestamp     │
  └────────┬────────┘
           │ On reconnect
           ▼
  ┌─────────────────┐
  │ Sync + Resolve  │
  │ Conflicts       │
  └─────────────────┘
```

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] Progress flow architecture documented: PASS
- [x] Status transition table documented: PASS
- [x] Transition functions documented: PASS
- [x] Criteria-based blocking documented: PASS
- [x] Auto-progression documented: PASS
- [x] Remote mode translation documented: PASS

## References

- `vibey/operations/roadmap/transitions.py` - Centralized transition logic
- `vibey/operations/roadmap/status_manager.py` - Auto-progression
- `vibey/roadmap/models/ticket.py` - Ticket models with can_transition_to()
- `.vibey/audit/sprint-0/core-data/B5-progress-rollup.md` - Progress rollup details
- `.vibey/audit/sprint-0/core-data/B3-status-state-machine.md` - Status states
