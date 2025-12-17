# Planned Status Criterion Design

**Sprint:** Architecture Design (Sprint 2)
**Task:** Design Planned Status Criterion for Tickets
**Date:** 2025-12-17
**Status:** Complete

---

## Executive Summary

This document designs a criterion-based approach to determining whether a ticket is "planned" - ready to be worked on. Like the completion criterion (all children complete → parent complete), the planned criterion evaluates multiple targets to determine readiness.

---

## Problem Statement

Currently, determining if a ticket is "ready to work on" requires subjective judgment:
- Does it have enough context?
- Is it properly specified?
- Are dependencies satisfied?

We need an **objective, computable** way to determine "planned" status that:
1. Aggregates from children (like completion)
2. Can be evaluated programmatically
3. Provides clear guidance on what's missing

---

## Planned vs Completion Status

| Aspect | Completion Status | Planned Status |
|--------|-------------------|----------------|
| Question | "Is this done?" | "Is this ready?" |
| Direction | Bottom-up (children → parent) | Top-down (parent → children) |
| Trigger | Work completed | Work can start |
| Criteria | Deliverables produced | Context exists |
| Inheritance | All children complete → complete | All children planned → planned |

---

## Criterion Architecture

### Base Model (Existing)

```python
# vibey/roadmap/models/ticket/targets.py (existing)

class CriterionTarget(Protocol):
    """Protocol for criterion targets."""

    def evaluate(self, ticket: "Ticket", context: RefreshContext) -> bool:
        """Evaluate whether this target is satisfied."""
        ...

    def get_description(self) -> str:
        """Human-readable description of this target."""
        ...
```

### PlannedCriterion Design

```python
# vibey/roadmap/models/ticket/planned.py (NEW)

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class PlannedTargetType(Enum):
    """Types of planned criterion targets."""
    YAML_EXISTS = "yaml_exists"           # YAML file exists
    DB_RECORD_EXISTS = "db_record_exists" # Database record exists
    CONTEXT_EXISTS = "context_exists"     # Context directory/files exist
    MANUAL_APPROVAL = "manual_approval"   # Human approved
    CHILDREN_PLANNED = "children_planned" # All children are planned
    DEPENDENCY_READY = "dependency_ready" # Dependencies are ready


@dataclass
class PlannedTarget:
    """A single target in the planned criterion."""
    target_type: PlannedTargetType
    required: bool = True
    description: str = ""

    # Target-specific parameters
    path: Optional[str] = None           # For YAML_EXISTS, CONTEXT_EXISTS
    min_files: int = 1                   # For CONTEXT_EXISTS
    approval_key: Optional[str] = None   # For MANUAL_APPROVAL


@dataclass
class PlannedCriterion:
    """
    Criterion for determining if a ticket is planned.

    A ticket is planned when all required targets are satisfied.
    """
    targets: List[PlannedTarget]

    def evaluate(self, ticket: "Ticket", context: RefreshContext) -> "PlannedResult":
        """Evaluate all targets and return result."""
        results = []
        for target in self.targets:
            satisfied = self._evaluate_target(target, ticket, context)
            results.append(TargetResult(
                target=target,
                satisfied=satisfied
            ))

        all_required_satisfied = all(
            r.satisfied for r in results if r.target.required
        )

        return PlannedResult(
            is_planned=all_required_satisfied,
            target_results=results,
            missing_targets=[r.target for r in results if not r.satisfied]
        )

    def _evaluate_target(
        self,
        target: PlannedTarget,
        ticket: "Ticket",
        context: RefreshContext
    ) -> bool:
        """Evaluate a single target."""
        match target.target_type:
            case PlannedTargetType.YAML_EXISTS:
                return self._check_yaml_exists(ticket, context)
            case PlannedTargetType.DB_RECORD_EXISTS:
                return self._check_db_record(ticket, context)
            case PlannedTargetType.CONTEXT_EXISTS:
                return self._check_context_exists(ticket, target, context)
            case PlannedTargetType.MANUAL_APPROVAL:
                return self._check_manual_approval(ticket, target)
            case PlannedTargetType.CHILDREN_PLANNED:
                return self._check_children_planned(ticket, context)
            case PlannedTargetType.DEPENDENCY_READY:
                return self._check_dependency_ready(ticket, context)
        return False
```

---

## Target Specifications

### 1. YAML_EXISTS Target

**Purpose:** Verify ticket has a YAML file (is tracked in system).

```python
def _check_yaml_exists(self, ticket: Ticket, ctx: RefreshContext) -> bool:
    """Check if YAML file exists for this ticket."""
    fs = FileSystemManager(ctx.root_dir)
    yaml_path = fs.get_entity_path(ticket.id, ticket.ticket_type)
    return yaml_path.exists()
```

**Default Behavior:**
- Always required for all tickets
- Automatically satisfied when ticket is created via CLI

### 2. DB_RECORD_EXISTS Target

**Purpose:** Verify ticket exists in SQLite query cache.

```python
def _check_db_record(self, ticket: Ticket, ctx: RefreshContext) -> bool:
    """Check if database record exists."""
    from vibey.roadmap.database import query_ticket
    try:
        record = query_ticket(ctx.db_path, ticket.id)
        return record is not None
    except Exception:
        return False
```

**Default Behavior:**
- Optional (database may not exist)
- Auto-satisfied after `db rebuild`

### 3. CONTEXT_EXISTS Target

**Purpose:** Verify planning documentation exists.

```python
def _check_context_exists(
    self,
    ticket: Ticket,
    target: PlannedTarget,
    ctx: RefreshContext
) -> bool:
    """Check if context files exist."""
    fs = FileSystemManager(ctx.root_dir)
    context_dir = fs.get_context_path(ticket.id, ticket.ticket_type)

    if not context_dir.exists():
        return False

    # Count relevant files
    context_files = list(context_dir.glob("**/*.md"))
    return len(context_files) >= target.min_files
```

**Configuration:**
```yaml
# In ticket YAML
planned_criterion:
  targets:
    - type: context_exists
      min_files: 1  # At least one planning document
      required: true
```

### 4. MANUAL_APPROVAL Target

**Purpose:** Require explicit human approval before work begins.

```python
def _check_manual_approval(
    self,
    ticket: Ticket,
    target: PlannedTarget
) -> bool:
    """Check if manual approval flag is set."""
    approval_key = target.approval_key or "planned_approved"
    return getattr(ticket, approval_key, False)
```

**Workflow:**
```bash
# Approve a ticket for work
vibey ticket approve <id> --reason "Requirements reviewed"

# Or via YAML
planned_approved: true
planned_approved_at: "2025-12-17T12:00:00Z"
planned_approved_by: "alice"
```

### 5. CHILDREN_PLANNED Target

**Purpose:** Aggregation - all children must be planned.

```python
def _check_children_planned(
    self,
    ticket: Ticket,
    ctx: RefreshContext
) -> bool:
    """Check if all children are planned."""
    if not ticket.children:
        return True  # Leaf nodes don't need children

    for child_id in ticket.children:
        child = ctx.ticket_loader(child_id)
        if not child.is_planned:
            return False

    return True
```

**Aggregation Rule:**
- Roadmap is planned when all tracks are planned
- Track is planned when all sprints are planned
- Sprint is planned when all tasks are planned
- Task is planned based on its own targets (no children)

### 6. DEPENDENCY_READY Target

**Purpose:** Ensure blocking dependencies are satisfied.

```python
def _check_dependency_ready(
    self,
    ticket: Ticket,
    ctx: RefreshContext
) -> bool:
    """Check if dependencies are ready (not blocking)."""
    if not ticket.depends_on:
        return True

    for dep_id in ticket.depends_on:
        dep_ticket = ctx.ticket_loader(dep_id)
        # Dependency must be either completed or not blocking
        if dep_ticket.status not in ("completed", "production_ready"):
            if dep_ticket.blocks(ticket.id):
                return False

    return True
```

---

## Model Updates

### Ticket Model Extension

```python
# vibey/roadmap/models/ticket/ticket.py

class Ticket(BaseModel):
    # ... existing fields ...

    # Planned status fields (NEW)
    planned_approved: bool = False
    planned_approved_at: Optional[datetime] = None
    planned_approved_by: Optional[str] = None

    @property
    def is_planned(self) -> bool:
        """Check if ticket is planned and ready to work on."""
        criterion = self._get_planned_criterion()
        result = criterion.evaluate(self, self._get_context())
        return result.is_planned

    @property
    def planned_status(self) -> PlannedResult:
        """Get detailed planned status with missing targets."""
        criterion = self._get_planned_criterion()
        return criterion.evaluate(self, self._get_context())

    def _get_planned_criterion(self) -> PlannedCriterion:
        """Get the planned criterion for this ticket type."""
        # Default criterion - can be overridden per-ticket
        return DEFAULT_PLANNED_CRITERIA.get(
            self.ticket_type,
            DEFAULT_PLANNED_CRITERION
        )
```

### Default Criteria by Type

```python
# vibey/roadmap/models/ticket/planned.py

DEFAULT_PLANNED_CRITERIA = {
    TicketType.ROADMAP: PlannedCriterion(
        targets=[
            PlannedTarget(PlannedTargetType.YAML_EXISTS),
            PlannedTarget(PlannedTargetType.CHILDREN_PLANNED),
        ]
    ),

    TicketType.TRACK: PlannedCriterion(
        targets=[
            PlannedTarget(PlannedTargetType.YAML_EXISTS),
            PlannedTarget(PlannedTargetType.CONTEXT_EXISTS, min_files=1),
            PlannedTarget(PlannedTargetType.CHILDREN_PLANNED),
        ]
    ),

    TicketType.SPRINT: PlannedCriterion(
        targets=[
            PlannedTarget(PlannedTargetType.YAML_EXISTS),
            PlannedTarget(PlannedTargetType.CONTEXT_EXISTS, min_files=1),
            PlannedTarget(PlannedTargetType.CHILDREN_PLANNED),
            PlannedTarget(PlannedTargetType.DEPENDENCY_READY),
        ]
    ),

    TicketType.TASK: PlannedCriterion(
        targets=[
            PlannedTarget(PlannedTargetType.YAML_EXISTS),
            PlannedTarget(PlannedTargetType.DEPENDENCY_READY),
            # Context exists is optional for tasks
            PlannedTarget(
                PlannedTargetType.CONTEXT_EXISTS,
                min_files=0,
                required=False
            ),
        ]
    ),
}
```

---

## CLI/MCP Commands

### Check Planned Status

```bash
# Check if ticket is planned
vibey ticket planned <id>

# Output:
# Ticket: 01KCMNY4BENEZBVT9NR20PFY03
# Status: PLANNED ✅
#
# Targets:
#   ✅ YAML file exists
#   ✅ Database record exists
#   ✅ Context files exist (2 files)
#   ⏳ Dependencies ready (1/1)
```

```bash
# Check with missing targets
vibey ticket planned <id>

# Output:
# Ticket: 01KCMNY4BENEZBVT9NR20PFY03
# Status: NOT PLANNED ❌
#
# Missing Targets:
#   ❌ Context files required (0/1 files)
#   ❌ Manual approval required
#
# To resolve:
#   1. Add context files: vibey context add <id> --file PLAN.md
#   2. Approve ticket: vibey ticket approve <id>
```

### Approve Ticket

```bash
# Approve a ticket for work
vibey ticket approve <id>
vibey ticket approve <id> --reason "Requirements reviewed"
vibey ticket approve <id> --by "alice"

# Unapprove
vibey ticket unapprove <id>
```

### MCP Tools

```python
@unified_command(
    name="ticket_planned",
    interfaces=["cli", "mcp"],
    mcp_name="vibey_ticket_planned"
)
def ticket_planned(ticket_id: str, root_dir=None) -> PlannedResult:
    """Check if a ticket is planned and ready to work on."""
    ...

@unified_command(
    name="ticket_approve",
    interfaces=["cli", "mcp"],
    mcp_name="vibey_ticket_approve"
)
def ticket_approve(ticket_id: str, reason: str = None, root_dir=None):
    """Approve a ticket for work."""
    ...
```

---

## Hierarchical Aggregation

### Evaluation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ROADMAP (is_planned)                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ ✅ YAML exists                                                │   │
│  │ ❓ All tracks planned?                                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│            │                                                        │
│            ▼                                                        │
│  ┌─────────────────────┐  ┌─────────────────────┐                   │
│  │ TRACK A (planned)   │  │ TRACK B (planned)   │                   │
│  │ ✅ YAML exists      │  │ ✅ YAML exists      │                   │
│  │ ✅ Context exists   │  │ ✅ Context exists   │                   │
│  │ ✅ Sprints planned  │  │ ✅ Sprints planned  │                   │
│  └─────────┬───────────┘  └──────────┬──────────┘                   │
│            │                         │                              │
│            ▼                         ▼                              │
│  ┌─────────────────────┐  ┌─────────────────────┐                   │
│  │ SPRINT 1 (planned)  │  │ SPRINT 2 (planned)  │                   │
│  │ ✅ YAML exists      │  │ ✅ YAML exists      │                   │
│  │ ✅ Context exists   │  │ ✅ Context exists   │                   │
│  │ ✅ Tasks planned    │  │ ✅ Tasks planned    │                   │
│  └─────────┬───────────┘  └──────────┬──────────┘                   │
│            │                         │                              │
│            ▼                         ▼                              │
│  ┌──────────────┐ ┌──────────────┐  ┌──────────────┐                │
│  │ Task 1 ✅    │ │ Task 2 ✅    │  │ Task 3 ✅    │                │
│  │ YAML exists  │ │ YAML exists  │  │ YAML exists  │                │
│  │ No deps      │ │ Deps ready   │  │ No deps      │                │
│  └──────────────┘ └──────────────┘  └──────────────┘                │
│                                                                     │
│  Result: ROADMAP IS PLANNED ✅                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Algorithm

```python
def is_planned(ticket: Ticket) -> bool:
    """Recursive planned status check."""
    # Check own targets (YAML, context, etc.)
    own_result = ticket._get_planned_criterion().evaluate(
        ticket,
        ticket._get_context()
    )

    # If own targets not satisfied, not planned
    if not own_result.is_planned:
        return False

    # For non-leaf tickets, check children
    if ticket.children:
        for child_id in ticket.children:
            child = ticket._get_context().ticket_loader(child_id)
            if not child.is_planned:
                return False

    return True
```

---

## Success Criteria Validation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Criterion defined | ✅ Complete | PlannedCriterion class |
| All targets specified | ✅ Complete | 6 target types |
| Hierarchical aggregation | ✅ Complete | CHILDREN_PLANNED target |
| CLI commands designed | ✅ Complete | planned, approve commands |
| MCP parity | ✅ Complete | Unified commands |

---

## Implementation Files

### New Files

| File | Purpose |
|------|---------|
| `vibey/roadmap/models/ticket/planned.py` | PlannedCriterion, targets |
| `vibey/unified/commands/planned.py` | Unified commands |

### Modified Files

| File | Change |
|------|--------|
| `vibey/roadmap/models/ticket/ticket.py` | Add is_planned property |
| `vibey/roadmap/models/ticket/__init__.py` | Export planned types |

---

## References

- Sprint 2 Task 1: SEMANTIC_LAYER_SPEC.md
- Existing Criterion Model: `vibey/roadmap/models/ticket/targets.py`
- Completable Protocol: `vibey/roadmap/models/ticket/completable.py`
