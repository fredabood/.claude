# E2: Task Selection Algorithm Audit

**Task ID:** 01KFXGJRC46RDTPM304RVJCY2J
**Phase:** E2: Advanced
**Date:** 2026-01-29

## Executive Summary

Complete audit of the Vibey Task Selection Algorithm in `vibey/services/implementation/selector.py`. The TaskSelector class finds executable tasks using a 6-step selection criteria: status=not_started, blocked=False, no incomplete dependencies, is_planned=True, priority ordering, and creation date tie-breaking. Key finding: Selection is deterministic with clear priority ordering (critical > high > medium > low), making it suitable for distributed scheduling with proper locking. Remote mode requires atomic task claiming to prevent race conditions.

## Methodology

**Files Analyzed:**
- `vibey/services/implementation/selector.py:1-433` - TaskSelector class
- `vibey/roadmap/criteria/planned.py:1-251` - Planned criteria system
- `vibey/roadmap/models/ticket/enums.py` - Priority/Status enums

## Findings

### 2. Selection Criteria Table

| Criterion | Check | Weight | Disqualifying |
|-----------|-------|--------|---------------|
| Status | `status = 'not_started'` | Required | Yes - must equal not_started |
| Blocked | `blocked = 0` | Required | Yes - blocked tasks excluded |
| Dependencies | No incomplete deps in entity_blocked_by | Required | Yes - incomplete deps block selection |
| Planned Status | `is_planned = True` (planning criteria met) | Required | Yes - unplanned tasks excluded |
| Priority | critical > high > medium > low > None | Ordering | No - used for ranking |
| Age | Creation timestamp | Tie-break | No - oldest first within priority |

### 3. Scoring Algorithm Table

| Factor | Formula | Weight | Range |
|--------|---------|--------|-------|
| Priority Score | `CASE priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 ELSE 4 END` | Primary | 0-4 (lower = higher priority) |
| Age Score | `ORDER BY created ASC` | Secondary | ISO timestamp (older = earlier) |
| Combined | `ORDER BY priority_score ASC, created ASC` | Final | N/A |

**Scoring Logic (SQL):**
```sql
ORDER BY
    CASE t.priority
        WHEN 'critical' THEN 0
        WHEN 'high' THEN 1
        WHEN 'medium' THEN 2
        WHEN 'low' THEN 3
        ELSE 4
    END ASC,
    t.created ASC
```

### 4. Readiness Checks Table

| Check | Condition | Failure Action | Priority |
|-------|-----------|----------------|----------|
| YAML Exists | File at `{type}s/{id}.yaml` exists | Mark not planned | Required (default) |
| Context Exists | Context files at `context/{type}s/{id}/` | Mark not planned | Optional (default) |
| Manual Approval | `approved = True` in ManualTarget | Mark not planned | Disabled (default) |
| Token Estimate | `estimated_tokens` set | Mark not planned | Optional (default) |
| Dependency Check | All deps in `entity_blocked_by` have status=completed | Exclude from candidates | Required |
| Blocked Flag | `blocked = False` in task record | Exclude from candidates | Required |

**PlannedCriteriaConfig Defaults:**
```python
check_yaml_exists: bool = True      # Required
check_context_exists: bool = True   # Optional
check_manual_approval: bool = False # Disabled
check_token_estimate: bool = False  # Disabled
```

### 5. Selection Flow Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       TASK SELECTION ALGORITHM                               │
└─────────────────────────────────────────────────────────────────────────────┘

                        ┌───────────────────┐
                        │ get_next_task()   │
                        │ or get_all_exec() │
                        └─────────┬─────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ _query_candidate_tasks  │
                    │  (SQLite Query)         │
                    └─────────────┬───────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│ Filter:       │       │ Filter:       │       │ Filter:       │
│ status =      │       │ blocked = 0   │       │ No incomplete │
│ 'not_started' │       │               │       │ dependencies  │
└───────┬───────┘       └───────┬───────┘       └───────┬───────┘
        │                       │                       │
        └───────────────────────┴───────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ Order by:               │
                    │  1. Priority (0-4)      │
                    │  2. Created ASC         │
                    └─────────────┬───────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ For each candidate:     │
                    │ _is_task_planned()      │
                    └─────────────┬───────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
           ┌───────────────┐           ┌───────────────┐
           │ is_planned    │           │ NOT planned   │
           │ = True        │           │               │
           └───────┬───────┘           └───────┬───────┘
                   │                           │
                   │                           │ Skip, try next
                   ▼                           │
           ┌───────────────┐                   │
           │ SELECTED!     │◄──────────────────┘
           │ Return task   │    (until found or exhausted)
           └───────────────┘
```

### 6. Selection Modes Table

| Mode | Scope | Batch Size | Use Case |
|------|-------|------------|----------|
| `get_next_task()` | All tasks | 1 | Sequential execution, single worker |
| `get_next_task(scope_ulid=track)` | Track only | 1 | Track-scoped execution |
| `get_next_task(scope_ulid=sprint)` | Sprint only | 1 | Sprint-scoped execution |
| `get_all_executable()` | All tasks | Up to 100 (configurable) | Parallel execution, batch workers |
| `get_all_executable(limit=N)` | All tasks | Up to N | Limited batch selection |
| `count_remaining()` | All tasks | Count only | Progress estimation |

**Scope Resolution:**
```python
# scope_ulid takes precedence over deprecated params
effective_track_id = scope_ulid or track_id
effective_sprint_id = sprint_id if not scope_ulid else None
```

### 7. Remote Scheduling Strategy Table

| Challenge | Pattern | Implementation | Trade-offs |
|-----------|---------|----------------|------------|
| Race Conditions | Optimistic Locking | Add `selected_at` timestamp, check before execution | Requires DB transaction support |
| Distributed Selection | Task Claiming | `SELECT FOR UPDATE` or atomic claim endpoint | Central coordinator required |
| Stale Candidates | Cache Invalidation | TTL on candidate lists, refresh on claim failure | More DB queries |
| Load Balancing | Work Stealing | Allow idle workers to claim from other scopes | Complexity vs utilization |
| Priority Drift | Periodic Re-ranking | Re-query every N tasks or T seconds | Stale rankings between refresh |
| Network Partition | Local Fallback | Cache candidate list, work offline | May duplicate work |
| Duplicate Execution | Idempotency Keys | Track execution attempts by task+worker | Storage overhead |
| Worker Failure | Lease/Heartbeat | Task lease expires after timeout, re-select | Delayed failure detection |

**Remote Selection Architecture:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      REMOTE TASK SCHEDULING                                  │
└─────────────────────────────────────────────────────────────────────────────┘

  LOCAL WORKERS                              CENTRAL COORDINATOR
  ─────────────────                          ─────────────────────

┌─────────────────┐     1. Request Task     ┌─────────────────┐
│ Worker A        │───────────────────────▶│ Task Selector   │
│ (Databricks)    │                         │ (Remote API)    │
└─────────────────┘                         └────────┬────────┘
                                                     │
┌─────────────────┐     2. Claim Task              │ SELECT
│ Worker B        │───────────────────────▶        │ FOR UPDATE
│ (Databricks)    │                                 │
└─────────────────┘                                 ▼
                                            ┌────────────────┐
┌─────────────────┐     3. Claim Task      │ SQLite/Postgres │
│ Worker C        │───────────────────────▶│ (Shared DB)     │
│ (Databricks)    │                         └────────────────┘
└─────────────────┘
        │
        │ 4. Execute locally
        ▼
┌─────────────────┐
│ Claude Agent    │
│ (subprocess)    │
└─────────────────┘
        │
        │ 5. Report completion
        ▼
┌─────────────────┐
│ Central State   │
│ (Delta Lake)    │
└─────────────────┘
```

**Recommended Remote API:**
```
POST /api/tasks/claim
  - Atomically selects and claims next available task
  - Returns task ID and lease expiry
  - Sets claimed_by, claimed_at, lease_expires

POST /api/tasks/{id}/complete
  - Marks task complete
  - Releases lease

POST /api/tasks/{id}/release
  - Releases lease without completion
  - Task returns to pool
```

## Remote Mode Implications

| Finding | Recommendation | Effort | Priority |
|---------|----------------|--------|----------|
| Selection is deterministic | Easy to replicate remotely | S | High |
| SQLite queries are local-only | Add remote query API | M | Critical |
| is_planned checks filesystem | Cache planned status in DB | M | High |
| No locking mechanism | Add atomic claim endpoint | M | Critical |
| Priority order is static | Works well for distributed | - | N/A |
| Scope filtering built-in | Pass scope to remote API | S | Medium |
| count_remaining() is estimate | Add accurate remote count | S | Low |
| No worker affinity | Add optional worker routing | M | Low |

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] >= 5 selection criteria documented: PASS (6 criteria: status, blocked, dependencies, planned, priority, age)
- [x] Scoring formula documented with weights: PASS (priority 0-4, age tie-break)
- [x] ASCII selection flow diagram included: PASS
- [x] Remote scheduling addresses race conditions: PASS (optimistic locking, atomic claims, leases)

## References

- `vibey/services/implementation/selector.py:62-424` - TaskSelector class
- `vibey/services/implementation/selector.py:109-156` - get_next_task() method
- `vibey/services/implementation/selector.py:252-348` - _query_candidate_tasks() SQL
- `vibey/services/implementation/selector.py:324-334` - Priority ordering SQL
- `vibey/roadmap/criteria/planned.py:30-52` - PlannedCriteriaConfig
- `vibey/roadmap/criteria/planned.py:180-207` - check_planned_status()
