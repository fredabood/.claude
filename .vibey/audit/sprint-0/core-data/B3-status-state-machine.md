# B3: Status State Machine Audit

**Task ID:** 01KFXF774FSERKXQS8PE777FKS
**Phase:** B3: Core Data Model
**Date:** 2026-01-29

## Executive Summary

Complete documentation of the status state machine for all entity types in the Vibey roadmap system. The system uses a unified `TicketStatus` enum with 10 values, while Tasks use a restricted `TaskStatus` enum with 6 values (no production statuses). Key finding: transitions are criteria-based, meaning completion is computed not declared - an entity cannot transition unless all criteria blocking that transition are satisfied. This design simplifies remote sync by making state changes deterministic.

## Methodology

**Files Analyzed:**
- `vibey/roadmap/models/common.py:38-62` - Status and TaskStatus enums (legacy)
- `vibey/roadmap/models/ticket/enums.py:19-39` - TicketStatus enum (unified architecture)
- `vibey/roadmap/models/ticket/completable.py:32-230` - Criterion-based transition validation
- `vibey/operations/roadmap/transitions.py:1-590` - Transition logic and entry points

## Findings

### 2. Task Status Values Table

| Status | Description | Terminal | Allowed From |
|--------|-------------|----------|--------------|
| `not_started` | Initial state, work not begun | No | N/A (initial), `in_progress` (reset) |
| `in_progress` | Work actively being done | No | `not_started`, `paused` |
| `paused` | Work temporarily suspended | No | `in_progress` |
| `completion_gate_check` | Awaiting quality gate verification | No | `in_progress` |
| `completed` | Work finished, all criteria met | Yes* | `in_progress`, `completion_gate_check` |
| `wont_do` | Explicitly abandoned | Yes | Any non-terminal |

**Notes:**
- Tasks do NOT have `production_gate_check`, `production_ready`, or `deployed` statuses
- `completed` is terminal for tasks (no production pipeline)
- Terminal states cannot transition to other states except via explicit admin override

### 3. Sprint Status Values Table

| Status | Description | Terminal | Allowed From |
|--------|-------------|----------|--------------|
| `not_started` | Sprint not begun | No | N/A (initial) |
| `in_progress` | Sprint work underway | No | `not_started`, `paused` |
| `paused` | Sprint temporarily suspended | No | `in_progress` |
| `completion_gate_check` | All tasks done, awaiting gate | No | `in_progress` |
| `completed` | Sprint tasks verified complete | No | `completion_gate_check` |
| `production_gate_check` | Awaiting production verification | No | `completed` |
| `production_ready` | Ready for deployment | No | `production_gate_check` |
| `deployed` | Released to production | Yes | `production_ready` |
| `superseded` | Merged into another sprint | Yes | Any non-terminal |
| `wont_do` | Sprint abandoned | Yes | Any non-terminal |

### 4. Track Status Values Table

| Status | Description | Terminal | Allowed From |
|--------|-------------|----------|--------------|
| `not_started` | Track not begun | No | N/A (initial) |
| `in_progress` | Track work underway | No | `not_started`, `paused` |
| `paused` | Track temporarily suspended | No | `in_progress` |
| `completion_gate_check` | All sprints done, awaiting gate | No | `in_progress` |
| `completed` | Track sprints verified complete | No | `completion_gate_check` |
| `production_gate_check` | Awaiting production verification | No | `completed` |
| `production_ready` | Ready for deployment | No | `production_gate_check` |
| `deployed` | Released to production | Yes | `production_ready` |
| `superseded` | Merged into another track | Yes | Any non-terminal |
| `wont_do` | Track abandoned | Yes | Any non-terminal |

### 5. State Transition Diagrams (ASCII)

#### Task State Machine

```
                            ┌──────────────┐
                            │  NOT_STARTED │
                            └──────┬───────┘
                                   │ start()
                                   ▼
               reset()     ┌──────────────┐
           ┌──────────────│  IN_PROGRESS │◄──────────┐
           │               └──────┬───────┘          │
           │                      │                  │
           │          ┌───────────┼───────────┐      │
           │          │           │           │      │ resume()
           │          ▼           ▼           │      │
           │    ┌──────────┐ ┌─────────────────┐    │
           │    │  PAUSED  │ │COMPLETION_GATE_ │    │
           │    │          │ │     CHECK       │    │
           │    └─────┬────┘ └────────┬────────┘    │
           │          │               │             │
           │          └───────┬───────┘             │
           │                  │ complete()          │
           │                  ▼                     │
           │          ┌──────────────┐              │
           └─────────►│  COMPLETED   │◄─────────────┤
                      └──────────────┘              │
                                                    │
                                                    │
     From any non-terminal:                         │
     ┌──────────────┐                              │
     │   WONT_DO    │◄─────────────────────────────┘
     └──────────────┘
```

#### Sprint/Track State Machine

```
                            ┌──────────────┐
                            │  NOT_STARTED │
                            └──────┬───────┘
                                   │ start()
                                   ▼
                           ┌──────────────┐
                           │  IN_PROGRESS │◄────────┐
                           └──────┬───────┘         │
                                  │                 │
              ┌───────────────────┼─────────────────┤ resume()
              │                   │                 │
              ▼                   ▼                 │
        ┌──────────┐    ┌─────────────────┐        │
        │  PAUSED  │───►│COMPLETION_GATE_ │        │
        └──────────┘    │     CHECK       │        │
                        └────────┬────────┘        │
                                 │                 │
                                 ▼                 │
                        ┌──────────────┐           │
                        │  COMPLETED   │───────────┤
                        └──────┬───────┘           │
                               │                   │
                               ▼                   │
                      ┌─────────────────┐          │
                      │PRODUCTION_GATE_ │          │
                      │     CHECK       │          │
                      └────────┬────────┘          │
                               │                   │
                               ▼                   │
                      ┌─────────────────┐          │
                      │PRODUCTION_READY │          │
                      └────────┬────────┘          │
                               │                   │
                               ▼                   │
                        ┌──────────────┐           │
                        │   DEPLOYED   │           │
                        └──────────────┘           │

     From any non-terminal:
     ┌──────────────┐    ┌──────────────┐
     │   WONT_DO    │    │  SUPERSEDED  │
     └──────────────┘    └──────────────┘
```

### 6. Transition Triggers Table

| Entity | Transition | Trigger Type | Command/Event |
|--------|------------|--------------|---------------|
| Task | NOT_STARTED → IN_PROGRESS | User-initiated | `vibey roadmap start <task-id>` |
| Task | IN_PROGRESS → COMPLETED | User-initiated | `vibey roadmap complete <task-id>` |
| Task | IN_PROGRESS → PAUSED | User-initiated | `vibey roadmap update task <id> --status paused` |
| Task | * → WONT_DO | User-initiated | `vibey roadmap update task <id> --status wont_do` |
| Sprint | NOT_STARTED → IN_PROGRESS | User-initiated / Auto | `start_item()` or auto when first task starts |
| Sprint | IN_PROGRESS → COMPLETED | Automatic | All tasks completed + gate criteria met |
| Sprint | COMPLETED → PRODUCTION_READY | User-initiated | `vibey roadmap complete <sprint-id>` with gates |
| Track | NOT_STARTED → IN_PROGRESS | Automatic | First sprint started (`_auto_start_parent_track()`) |
| Track | IN_PROGRESS → COMPLETED | Automatic | All sprints completed + gate criteria met |
| Parent | Child completes | Rollup | Progress updated, may trigger parent completion |

### 7. Validation Rules Table

| Transition | Pre-Validation | Post-Effects | Timestamp Updates |
|------------|----------------|--------------|-------------------|
| → IN_PROGRESS | `can_transition_to(IN_PROGRESS)`: All criteria with `blocks_transition_to=IN_PROGRESS` must be met | None | `started_at = now()` |
| → COMPLETED | `can_transition_to(COMPLETED)`: All criteria with `blocks_transition_to=COMPLETED` must be met | Generate post-mortem (tasks), update parent progress | `completed_at = now()` |
| → PRODUCTION_READY | `can_transition_to(PRODUCTION_READY)`: All production gate criteria must be met | None | `production_ready_at = now()` |
| → DEPLOYED | Status must be PRODUCTION_READY | None | `deployed_at = now()` |
| → PAUSED | Status must be IN_PROGRESS | None | None |
| → WONT_DO | Any non-terminal state | Remove from progress calculations | None |
| → SUPERSEDED | Any non-terminal state | Link to superseding entity | None |

**Criteria-Based Validation:**
```python
def can_transition_to(self, status: TicketStatus) -> Tuple[bool, List[str]]:
    blocking_reasons = [
        c.description
        for c in self.criteria
        if c.blocks_transition_to == status and not c.is_met
    ]
    return (len(blocking_reasons) == 0, blocking_reasons)
```

### 8. Remote Sync Strategy Table

| Scenario | Conflict Type | Resolution Strategy | Locking |
|----------|---------------|---------------------|---------|
| Concurrent task completion | Status divergence | Last-write-wins with timestamp | Optimistic |
| Parent auto-update vs direct update | Progress mismatch | Recompute progress from children | None |
| Task completed locally, not synced | Stale remote state | Push local state (local is source of truth during session) | Optimistic |
| Task completed remotely while offline | Missing remote update | Pull remote, merge commits/metadata | Optimistic |
| Conflicting status changes | Both users changed status | Reject later write, require manual resolution | Pessimistic |
| Criteria changed during transition | Validation drift | Re-validate after sync, rollback if invalid | Optimistic |
| Terminal state reached | No recovery | Terminal states are permanent, no conflict | N/A |

**Sync Strategy Recommendations:**

1. **Optimistic Concurrency**: Use `last_modified` timestamp for conflict detection
2. **Criteria-Based Validation**: Always re-run `can_transition_to()` after sync
3. **Idempotent Transitions**: `start()` and `complete()` produce same result regardless of call count
4. **Event Sourcing**: Store transition events, not just current state
5. **Conflict Resolution UI**: Surface conflicts to users for manual resolution

### Remote Mode Implications

| Finding | Recommendation | Effort | Priority |
|---------|----------------|--------|----------|
| Criteria-based transitions are deterministic | Sync criteria state, not just status | M | Critical |
| 10 status values with clear progression | Store as STRING enum in Delta Lake | S | High |
| Automatic parent updates on child completion | Implement same rollup logic in remote mode | M | Critical |
| Post-mortem generation on task completion | Run post-mortem generation after remote sync | S | Medium |
| Terminal states are permanent | Enforce terminal state immutability in Delta Lake | S | High |
| Timestamps updated on transitions | Use server timestamps for remote transitions | S | High |

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] All 3 entity types have status tables: PASS (Task: 6 statuses, Sprint: 10 statuses, Track: 10 statuses)
- [x] ASCII state diagrams included for each entity: PASS (Task and Sprint/Track diagrams)
- [x] >= 5 transition triggers documented: PASS (10 triggers documented)
- [x] Remote conflict resolution strategy defined: PASS (7 scenarios with strategies)

## References

- `vibey/roadmap/models/common.py:38-62` - Legacy Status and TaskStatus enums
- `vibey/roadmap/models/ticket/enums.py:19-39` - Unified TicketStatus enum
- `vibey/roadmap/models/ticket/completable.py:32-102` - Criterion class definition
- `vibey/roadmap/models/ticket/completable.py:146-168` - can_transition_to() implementation
- `vibey/operations/roadmap/transitions.py:67-128` - TransitionBlockedError and transition_ticket()
- `vibey/operations/roadmap/transitions.py:354-393` - _auto_start_parent_track() implementation
- `vibey/operations/roadmap/transitions.py:395-577` - start_item() and complete_item() entry points
