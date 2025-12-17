# Task 3: Implement Hierarchical Planned Status Aggregation

**Task ID:** `01KCMNPC039DG15PZT0QHMTBCV`
**Sprint:** Sprint 4: Major Refactoring
**Priority:** Medium | **Complexity:** Simple | **Type:** Development

---

## Problem Statement

Need `is_planned` property on `HierarchicalTicket` that:
- For leaf tickets (tasks): checks planning criteria
- For parent tickets (sprints, tracks): aggregates from children

The aggregation pattern ALREADY EXISTS for commits (`commits_aggregated`), estimated tokens, and other properties. This task adds the same pattern for planned status.

---

## Existing Infrastructure

### HierarchicalTicket Aggregation Pattern

```python
# vibey/roadmap/models/ticket/hierarchical.py

class HierarchicalTicket(Ticket):

    @property
    def commits_aggregated(self) -> List[GitCommit]:
        """
        Commits aggregated from this ticket and all descendants.

        Behavior by ticket type:
        - is_leaf: return local commits only
        - is_parent: aggregate from all children recursively
        """
        if not self.is_parent:
            return self.commits
        return self._aggregate_commits()

    def _aggregate_commits(self) -> List[GitCommit]:
        all_commits = list(self.commits)
        for child_id in self.children:
            child = self._load_child(child_id)
            if hasattr(child, 'commits_aggregated'):
                all_commits.extend(child.commits_aggregated)
        return all_commits
```

### Existing Hierarchy Properties

```python
@property
def is_leaf(self) -> bool:
    """True if no children (Task tickets)."""
    return len(self.children) == 0

@property
def is_parent(self) -> bool:
    """True if has children."""
    return len(self.children) > 0
```

---

## Implementation Steps

### Step 1: Add `is_planned` Property (30 min)

```python
# vibey/roadmap/models/ticket/hierarchical.py

from vibey.roadmap.criteria.planned import (
    check_planned_status,
    PlannedCriteriaConfig,
)

class HierarchicalTicket(Ticket):

    # Class-level config for planned checking
    _planned_config: ClassVar[PlannedCriteriaConfig] = PlannedCriteriaConfig()
    _roadmap_root: ClassVar[Optional[Path]] = None

    @classmethod
    def set_planned_config(cls, config: PlannedCriteriaConfig, roadmap_root: Path) -> None:
        """Configure planned status checking."""
        cls._planned_config = config
        cls._roadmap_root = roadmap_root

    @computed_field
    @property
    def is_planned(self) -> bool:
        """
        Check if ticket is planned (ready for implementation).

        Behavior by ticket type:
        - is_leaf (Task): check planning criteria directly
        - is_parent (Sprint/Track): all children must be planned

        Returns:
            True if ticket is fully planned
        """
        if not self.is_parent:
            return self._check_local_planned()
        return self._aggregate_planned()

    def _check_local_planned(self) -> bool:
        """Check if this leaf ticket is planned."""
        if self._roadmap_root is None:
            # Can't check without roadmap root - assume planned
            return True

        ticket_type = self._infer_ticket_type()
        is_planned, _ = check_planned_status(
            ticket_id=self.id,
            ticket_type=ticket_type,
            roadmap_root=self._roadmap_root,
            config=self._planned_config,
        )
        return is_planned

    def _aggregate_planned(self) -> bool:
        """Aggregate planned status from children."""
        for child_id in self.children:
            child = self._load_child(child_id)
            if child is not None and hasattr(child, 'is_planned'):
                if not child.is_planned:
                    return False
        return True

    def _infer_ticket_type(self) -> str:
        """Infer ticket type from hierarchy position."""
        if self.is_ultimate_child:
            return "task"
        elif self.is_ultimate_parent:
            return "track"
        else:
            return "sprint"

    @property
    def planned_progress(self) -> Progress:
        """
        Progress toward being fully planned.

        Returns:
            Progress with total/completed children or criteria
        """
        if not self.is_parent:
            # Leaf: check criteria
            if self._roadmap_root is None:
                return Progress(total=0, completed=0)

            from vibey.roadmap.criteria.planned import create_planned_criteria
            criteria = create_planned_criteria(
                self.id,
                self._infer_ticket_type(),
                self._roadmap_root,
                self._planned_config,
            )
            total = len([c for c in criteria if c.required])
            completed = len([c for c in criteria if c.required and c.is_met])
            return Progress(total=total, completed=completed)

        # Parent: aggregate from children
        total = len(self.children)
        completed = 0
        for child_id in self.children:
            child = self._load_child(child_id)
            if child is not None and hasattr(child, 'is_planned') and child.is_planned:
                completed += 1
        return Progress(total=total, completed=completed)

    @property
    def unplanned_children(self) -> List[str]:
        """
        Get IDs of children that are not yet planned.

        Only meaningful for parent tickets.
        """
        if not self.is_parent:
            return []

        unplanned = []
        for child_id in self.children:
            child = self._load_child(child_id)
            if child is not None and hasattr(child, 'is_planned') and not child.is_planned:
                unplanned.append(child_id)
        return unplanned
```

### Step 2: Add Caching for Performance (15 min)

```python
# vibey/roadmap/models/ticket/hierarchical.py

from functools import lru_cache

class HierarchicalTicket(Ticket):

    # ... existing code ...

    @staticmethod
    @lru_cache(maxsize=1000)
    def _cached_planned_status(ticket_id: str, roadmap_root_str: str) -> bool:
        """Cached planned status check for performance."""
        from vibey.roadmap.criteria.planned import check_planned_status

        roadmap_root = Path(roadmap_root_str)

        # Determine type from filesystem
        if (roadmap_root / "tasks" / f"{ticket_id}.yaml").exists():
            ticket_type = "task"
        elif (roadmap_root / "sprints" / f"{ticket_id}.yaml").exists():
            ticket_type = "sprint"
        else:
            ticket_type = "track"

        is_planned, _ = check_planned_status(
            ticket_id=ticket_id,
            ticket_type=ticket_type,
            roadmap_root=roadmap_root,
        )
        return is_planned

    @classmethod
    def clear_planned_cache(cls) -> None:
        """Clear the planned status cache."""
        cls._cached_planned_status.cache_clear()

    def _check_local_planned(self) -> bool:
        """Check if this leaf ticket is planned (with caching)."""
        if self._roadmap_root is None:
            return True
        return self._cached_planned_status(self.id, str(self._roadmap_root))
```

### Step 3: Add Unit Tests (30 min)

```python
# tests/roadmap/models/ticket/test_hierarchical_planned.py

import pytest
from pathlib import Path

from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
from vibey.roadmap.models.ticket.enums import TicketStatus
from vibey.roadmap.criteria.planned import PlannedCriteriaConfig


@pytest.fixture
def roadmap_env(tmp_path):
    """Create minimal roadmap environment."""
    roadmap_root = tmp_path / ".vibey" / "roadmap"
    (roadmap_root / "tasks").mkdir(parents=True)
    (roadmap_root / "sprints").mkdir(parents=True)
    (roadmap_root / "tracks").mkdir(parents=True)

    HierarchicalTicket.set_planned_config(
        PlannedCriteriaConfig(),
        roadmap_root,
    )

    yield {'root': tmp_path, 'roadmap': roadmap_root}

    HierarchicalTicket.clear_planned_cache()


class TestIsPlanned:
    """Tests for is_planned property."""

    def test_leaf_planned_when_yaml_exists(self, roadmap_env):
        """Leaf ticket is planned when YAML exists."""
        # Create YAML file
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01TESTLEAF.yaml"
        yaml_path.write_text("task: {id: 01TESTLEAF}")

        ticket = HierarchicalTicket(
            id="01TESTLEAF",
            name="Test Task",
            criteria=[],  # No children = leaf
        )

        assert ticket.is_planned is True

    def test_leaf_not_planned_when_yaml_missing(self, roadmap_env):
        """Leaf ticket is not planned when YAML doesn't exist."""
        ticket = HierarchicalTicket(
            id="01MISSING",
            name="Missing Task",
            criteria=[],
        )

        assert ticket.is_planned is False

    def test_parent_planned_when_all_children_planned(self, roadmap_env, mocker):
        """Parent is planned when all children are planned."""
        # Create YAML for children
        for i in range(3):
            yaml_path = roadmap_env['roadmap'] / "tasks" / f"01CHILD{i}.yaml"
            yaml_path.write_text(f"task: {{id: 01CHILD{i}}}")

        # Mock child loading
        def mock_load(ticket_id):
            return HierarchicalTicket(
                id=ticket_id,
                name=f"Child {ticket_id}",
                criteria=[],
            )

        mocker.patch.object(HierarchicalTicket, '_load_child', mock_load)

        # Create parent with children as criteria
        from vibey.roadmap.models.ticket.completable import Criterion
        from vibey.roadmap.models.ticket.targets import CompletableTarget

        parent = HierarchicalTicket(
            id="01PARENT",
            name="Parent Sprint",
            criteria=[
                Criterion(
                    id=f"child-{i}",
                    description=f"Child {i}",
                    target=CompletableTarget(completable_id=f"01CHILD{i}"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                )
                for i in range(3)
            ],
        )

        assert parent.is_parent is True
        assert parent.is_planned is True

    def test_parent_not_planned_when_child_not_planned(self, roadmap_env, mocker):
        """Parent is not planned when any child is not planned."""
        # Only create YAML for some children
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01CHILD0.yaml"
        yaml_path.write_text("task: {id: 01CHILD0}")
        # 01CHILD1 has no YAML

        def mock_load(ticket_id):
            return HierarchicalTicket(
                id=ticket_id,
                name=f"Child {ticket_id}",
                criteria=[],
            )

        mocker.patch.object(HierarchicalTicket, '_load_child', mock_load)

        from vibey.roadmap.models.ticket.completable import Criterion
        from vibey.roadmap.models.ticket.targets import CompletableTarget

        parent = HierarchicalTicket(
            id="01PARENT",
            name="Parent Sprint",
            criteria=[
                Criterion(
                    id="child-0",
                    description="Child 0",
                    target=CompletableTarget(completable_id="01CHILD0"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="child-1",
                    description="Child 1",
                    target=CompletableTarget(completable_id="01CHILD1"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        assert parent.is_planned is False


class TestPlannedProgress:
    """Tests for planned_progress property."""

    def test_leaf_progress_counts_criteria(self, roadmap_env):
        """Leaf progress counts required criteria."""
        ticket = HierarchicalTicket(
            id="01TEST",
            name="Test",
            criteria=[],
        )

        progress = ticket.planned_progress
        assert progress.total >= 0


class TestUnplannedChildren:
    """Tests for unplanned_children property."""

    def test_leaf_returns_empty(self, roadmap_env):
        """Leaf ticket returns empty list."""
        ticket = HierarchicalTicket(
            id="01TEST",
            name="Test",
            criteria=[],
        )

        assert ticket.unplanned_children == []
```

---

## Files to Modify

| File | Change |
|------|--------|
| `vibey/roadmap/models/ticket/hierarchical.py` | Add `is_planned`, `planned_progress`, `unplanned_children` |
| `tests/roadmap/models/ticket/test_hierarchical_planned.py` | New test file |

---

## Acceptance Criteria

- [ ] `is_planned` property exists on `HierarchicalTicket`
- [ ] Leaf tickets check planning criteria
- [ ] Parent tickets aggregate from children
- [ ] `planned_progress` shows progress toward planned
- [ ] `unplanned_children` lists children needing planning
- [ ] Caching prevents redundant filesystem checks
- [ ] All unit tests pass

---

## Dependencies

- **Task 2** must be complete (provides `check_planned_status`)

---

## Estimated Effort

| Step | Time |
|------|------|
| Step 1: Add is_planned property | 30 min |
| Step 2: Add caching | 15 min |
| Step 3: Add unit tests | 30 min |
| **Total** | **~1.25 hours** |
