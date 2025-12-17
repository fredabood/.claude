# Task 2: Implement PlannedCriterion Composite

**Task ID:** `01KCMNP21ZPJMABMKHJYDQD7RR`
**Sprint:** Sprint 4: Major Refactoring
**Priority:** High | **Complexity:** Simple | **Type:** Development

---

## Problem Statement

Need a way to check if a ticket is "planned" (ready for implementation work). A ticket is planned when:
1. YAML file exists
2. Database record exists
3. Context files exist (optional)
4. Manual approval given (optional)

All the individual criterion target types ALREADY EXIST in `vibey/roadmap/models/ticket/targets.py`. This task is about composing them into a reusable "planned" criterion factory.

---

## Existing Infrastructure

### Available Target Types

```python
# vibey/roadmap/models/ticket/targets.py

class FileExistsTarget(CriterionTarget):
    """Check if file(s) exist."""
    paths: List[str]
    exists: bool = True  # If True, check files exist; if False, check they don't

class ManualTarget(CriterionTarget):
    """Human approval required."""
    approved: bool = False
    approver: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None

class CompletableTarget(CriterionTarget):
    """Check another ticket's status."""
    completable_id: str
    required_status: TicketStatus = TicketStatus.COMPLETED
```

### Criterion Model

```python
# vibey/roadmap/models/ticket/completable.py

class Criterion(BaseModel):
    id: str                                    # Unique ID
    description: str                           # Human-readable
    blocks_transition_to: TicketStatus         # Which transition this guards
    target: AnyTarget                          # Polymorphic target
    required: bool = True                      # If False, doesn't block
```

---

## Implementation Steps

### Step 1: Create Criteria Module (15 min)

```python
# vibey/roadmap/criteria/__init__.py

"""
Criterion composition utilities.

This module provides factory functions for creating common criterion patterns.
"""

from .planned import (
    create_planned_criteria,
    PlannedCriteriaConfig,
    DEFAULT_PLANNED_CONFIG,
)

__all__ = [
    "create_planned_criteria",
    "PlannedCriteriaConfig",
    "DEFAULT_PLANNED_CONFIG",
]
```

### Step 2: Implement PlannedCriterion Factory (45 min)

```python
# vibey/roadmap/criteria/planned.py

"""
Planned criterion factory.

Creates criteria that determine if a ticket is "planned" (ready for work).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from vibey.roadmap.models.ticket.completable import Criterion
from vibey.roadmap.models.ticket.enums import TicketStatus
from vibey.roadmap.models.ticket.targets import FileExistsTarget, ManualTarget


@dataclass
class PlannedCriteriaConfig:
    """Configuration for planned criteria."""

    # Which checks to include
    check_yaml_exists: bool = True
    check_context_exists: bool = True
    check_manual_approval: bool = False

    # Which checks are required vs optional
    yaml_required: bool = True
    context_required: bool = False
    approval_required: bool = False


DEFAULT_PLANNED_CONFIG = PlannedCriteriaConfig()


def create_planned_criteria(
    ticket_id: str,
    ticket_type: str,  # 'task', 'sprint', 'track'
    roadmap_root: Path,
    config: PlannedCriteriaConfig = DEFAULT_PLANNED_CONFIG,
) -> List[Criterion]:
    """
    Create criteria for determining if a ticket is "planned".

    Args:
        ticket_id: The ticket's ULID
        ticket_type: Type of ticket ('task', 'sprint', 'track')
        roadmap_root: Path to .vibey/roadmap directory
        config: Configuration for which checks to include

    Returns:
        List of Criterion objects that block IN_PROGRESS transition
    """
    criteria = []

    # 1. YAML file exists
    if config.check_yaml_exists:
        yaml_path = roadmap_root / f"{ticket_type}s" / f"{ticket_id}.yaml"
        criteria.append(
            Criterion(
                id=f"{ticket_id}-yaml-exists",
                description=f"YAML file exists at {ticket_type}s/{ticket_id}.yaml",
                blocks_transition_to=TicketStatus.IN_PROGRESS,
                target=FileExistsTarget(paths=[str(yaml_path)]),
                required=config.yaml_required,
            )
        )

    # 2. Context directory/files exist
    if config.check_context_exists:
        # Context can be in multiple locations depending on ticket type
        context_paths = _get_context_paths(ticket_id, ticket_type, roadmap_root)
        if context_paths:
            criteria.append(
                Criterion(
                    id=f"{ticket_id}-context-exists",
                    description="Context files exist (task plan, design docs, etc.)",
                    blocks_transition_to=TicketStatus.IN_PROGRESS,
                    target=FileExistsTarget(paths=context_paths),
                    required=config.context_required,
                )
            )

    # 3. Manual approval
    if config.check_manual_approval:
        criteria.append(
            Criterion(
                id=f"{ticket_id}-planning-approved",
                description="Planning has been reviewed and approved",
                blocks_transition_to=TicketStatus.IN_PROGRESS,
                target=ManualTarget(
                    approved=False,
                    approver=None,
                ),
                required=config.approval_required,
            )
        )

    return criteria


def _get_context_paths(
    ticket_id: str,
    ticket_type: str,
    roadmap_root: Path,
) -> List[str]:
    """
    Get potential context file paths for a ticket.

    Context can be in:
    - .vibey/roadmap/context/tasks/<id>/
    - .vibey/roadmap/context/sprints/<slug>/
    - .vibey/roadmap/context/tracks/<slug>/sprints/<sprint-slug>/task-<n>/
    """
    paths = []

    # Direct context path (new flat structure)
    direct_path = roadmap_root / "context" / f"{ticket_type}s" / ticket_id
    if direct_path.exists():
        # Look for TASK_PLAN.md or any .md files
        task_plan = direct_path / "TASK_PLAN.md"
        if task_plan.exists():
            paths.append(str(task_plan))
        else:
            # Any markdown file counts as context
            md_files = list(direct_path.glob("*.md"))
            paths.extend(str(f) for f in md_files[:1])  # Just need one

    return paths


def check_planned_status(
    ticket_id: str,
    ticket_type: str,
    roadmap_root: Path,
    config: PlannedCriteriaConfig = DEFAULT_PLANNED_CONFIG,
) -> tuple[bool, List[str]]:
    """
    Check if a ticket is planned (all planning criteria met).

    Args:
        ticket_id: The ticket's ULID
        ticket_type: Type of ticket
        roadmap_root: Path to .vibey/roadmap
        config: Criteria configuration

    Returns:
        Tuple of (is_planned: bool, unmet_criteria: List[str])
    """
    criteria = create_planned_criteria(ticket_id, ticket_type, roadmap_root, config)

    unmet = []
    for c in criteria:
        if c.required and not c.is_met:
            unmet.append(c.description)

    return (len(unmet) == 0, unmet)


def get_planning_work_needed(
    ticket_id: str,
    ticket_type: str,
    roadmap_root: Path,
    config: PlannedCriteriaConfig = DEFAULT_PLANNED_CONFIG,
) -> List[dict]:
    """
    Get list of planning work items needed for a ticket.

    Returns:
        List of dicts: [{'criterion': str, 'action': str, 'details': str}]
    """
    criteria = create_planned_criteria(ticket_id, ticket_type, roadmap_root, config)

    work_items = []
    for c in criteria:
        if not c.is_met:
            work_items.append({
                'criterion': c.id,
                'description': c.description,
                'required': c.required,
                'action': _suggest_action(c),
            })

    return work_items


def _suggest_action(criterion: Criterion) -> str:
    """Suggest action to satisfy a criterion."""
    if isinstance(criterion.target, FileExistsTarget):
        paths = criterion.target.paths
        if paths:
            return f"Create file: {paths[0]}"
        return "Create required file"
    elif isinstance(criterion.target, ManualTarget):
        return "Get planning approval via 'vibey planned approve <id>'"
    return "Satisfy criterion"
```

### Step 3: Add Unit Tests (30 min)

```python
# tests/roadmap/criteria/test_planned.py

import pytest
from pathlib import Path
import tempfile

from vibey.roadmap.criteria.planned import (
    create_planned_criteria,
    check_planned_status,
    get_planning_work_needed,
    PlannedCriteriaConfig,
)
from vibey.roadmap.models.ticket.enums import TicketStatus


class TestCreatePlannedCriteria:
    """Tests for create_planned_criteria()."""

    def test_default_config_creates_two_criteria(self, tmp_path):
        """Default config creates YAML and context criteria."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        roadmap_root.mkdir(parents=True)

        criteria = create_planned_criteria(
            ticket_id="01TEST",
            ticket_type="task",
            roadmap_root=roadmap_root,
        )

        assert len(criteria) == 2  # YAML + context
        assert all(c.blocks_transition_to == TicketStatus.IN_PROGRESS for c in criteria)

    def test_yaml_criterion_required_by_default(self, tmp_path):
        """YAML criterion should be required by default."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        roadmap_root.mkdir(parents=True)

        criteria = create_planned_criteria(
            ticket_id="01TEST",
            ticket_type="task",
            roadmap_root=roadmap_root,
        )

        yaml_crit = next(c for c in criteria if "yaml" in c.id.lower())
        assert yaml_crit.required is True

    def test_context_criterion_optional_by_default(self, tmp_path):
        """Context criterion should be optional by default."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        roadmap_root.mkdir(parents=True)

        criteria = create_planned_criteria(
            ticket_id="01TEST",
            ticket_type="task",
            roadmap_root=roadmap_root,
        )

        context_crit = next((c for c in criteria if "context" in c.id.lower()), None)
        if context_crit:
            assert context_crit.required is False

    def test_manual_approval_when_configured(self, tmp_path):
        """Manual approval criterion created when configured."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        roadmap_root.mkdir(parents=True)

        config = PlannedCriteriaConfig(check_manual_approval=True)
        criteria = create_planned_criteria(
            ticket_id="01TEST",
            ticket_type="task",
            roadmap_root=roadmap_root,
            config=config,
        )

        approval_crit = next((c for c in criteria if "approved" in c.id.lower()), None)
        assert approval_crit is not None


class TestCheckPlannedStatus:
    """Tests for check_planned_status()."""

    def test_returns_false_when_yaml_missing(self, tmp_path):
        """Should return False when YAML file doesn't exist."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        roadmap_root.mkdir(parents=True)
        (roadmap_root / "tasks").mkdir()

        is_planned, unmet = check_planned_status(
            ticket_id="01TEST",
            ticket_type="task",
            roadmap_root=roadmap_root,
        )

        assert is_planned is False
        assert len(unmet) > 0

    def test_returns_true_when_yaml_exists(self, tmp_path):
        """Should return True when YAML file exists."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        (roadmap_root / "tasks").mkdir(parents=True)

        # Create YAML file
        yaml_path = roadmap_root / "tasks" / "01TEST.yaml"
        yaml_path.write_text("task: {}")

        is_planned, unmet = check_planned_status(
            ticket_id="01TEST",
            ticket_type="task",
            roadmap_root=roadmap_root,
        )

        assert is_planned is True
        assert len(unmet) == 0
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `vibey/roadmap/criteria/__init__.py` | Package exports |
| `vibey/roadmap/criteria/planned.py` | PlannedCriterion factory and utilities |
| `tests/roadmap/criteria/__init__.py` | Test package |
| `tests/roadmap/criteria/test_planned.py` | Unit tests |

---

## Acceptance Criteria

- [ ] `create_planned_criteria()` creates criteria using existing target types
- [ ] `check_planned_status()` returns (bool, reasons) tuple
- [ ] `get_planning_work_needed()` suggests actions
- [ ] Configuration allows customizing which checks are required
- [ ] All unit tests pass
- [ ] No new dependencies required

---

## Design Decisions

1. **Factory function, not class** - `create_planned_criteria()` returns a list of `Criterion` objects rather than a new class. This keeps the system simpler.

2. **Configurable requirements** - Use `PlannedCriteriaConfig` to customize which checks are required vs optional.

3. **Reuse existing targets** - No new target types created; just compose `FileExistsTarget` and `ManualTarget`.

4. **Block IN_PROGRESS** - Planned criteria block starting work (IN_PROGRESS), not completion.

---

## Estimated Effort

| Step | Time |
|------|------|
| Step 1: Create module structure | 15 min |
| Step 2: Implement factory | 45 min |
| Step 3: Add unit tests | 30 min |
| **Total** | **~1.5 hours** |
