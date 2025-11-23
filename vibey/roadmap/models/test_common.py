"""
Unit tests for common types and enums.

Tests enums, DependencyStatus, and shared validation logic.
"""

import unittest
from datetime import datetime, timezone
from vibey.roadmap.models.common import (
    Status,
    TaskStatus,
    Priority,
    TaskType,
    GateStatus,
    DependencyType,
    Complexity,
    DeliverableType,
    ActivityType,
    VersionBumpTrigger,
    DependencyStatus,
)


class TestEnums(unittest.TestCase):
    """Test enum definitions."""

    def test_status_enum(self):
        """Test Status enum values."""
        self.assertEqual(Status.NOT_STARTED.value, "not_started")
        self.assertEqual(Status.IN_PROGRESS.value, "in_progress")
        self.assertEqual(Status.PRODUCTION_READY.value, "production_ready")
        self.assertEqual(Status.DEPLOYED.value, "deployed")

    def test_task_status_enum(self):
        """Test TaskStatus enum (restricted set)."""
        self.assertEqual(TaskStatus.NOT_STARTED.value, "not_started")
        self.assertEqual(TaskStatus.COMPLETED.value, "completed")

        # TaskStatus should not have production statuses
        with self.assertRaises(AttributeError):
            _ = TaskStatus.PRODUCTION_READY

    def test_priority_enum(self):
        """Test Priority enum."""
        self.assertEqual(Priority.CRITICAL.value, "critical")
        self.assertEqual(Priority.HIGH.value, "high")
        self.assertEqual(Priority.MEDIUM.value, "medium")
        self.assertEqual(Priority.LOW.value, "low")

    def test_task_type_enum(self):
        """Test TaskType enum."""
        self.assertEqual(TaskType.DEVELOPMENT.value, "development")
        self.assertEqual(TaskType.COMPLETION_GATE.value, "completion_gate")
        self.assertEqual(TaskType.PRODUCTION_GATE.value, "production_gate")

    def test_enum_string_values(self):
        """Test that enums are string-based."""
        # Should be usable as strings
        self.assertIsInstance(Status.IN_PROGRESS, str)
        self.assertIsInstance(TaskType.DEVELOPMENT, str)
        self.assertIsInstance(Priority.HIGH, str)


class TestDependencyStatus(unittest.TestCase):
    """Test DependencyStatus dataclass."""

    def test_dependency_status_creation(self):
        """Test creating DependencyStatus."""
        now = datetime.now(timezone.utc)
        dep = DependencyStatus(
            blocker_id="backend-1-task-001",
            blocker_type="task",
            required_status="completed",
            current_status="in_progress",
            blocks_transition_to="in_progress",
            last_checked=now,
        )

        self.assertEqual(dep.blocker_id, "backend-1-task-001")
        self.assertEqual(dep.blocker_type, "task")
        self.assertEqual(dep.required_status, "completed")
        self.assertEqual(dep.current_status, "in_progress")

    def test_is_satisfied_exact_match(self):
        """Test is_satisfied with exact status match."""
        now = datetime.now(timezone.utc)
        dep = DependencyStatus(
            blocker_id="backend-1-task-001",
            blocker_type="task",
            required_status="completed",
            current_status="completed",
            blocks_transition_to="in_progress",
            last_checked=now,
        )

        self.assertTrue(dep.is_satisfied())

    def test_is_satisfied_progression(self):
        """Test is_satisfied with status progression."""
        now = datetime.now(timezone.utc)

        # Current > Required (satisfied)
        dep = DependencyStatus(
            blocker_id="backend-1-task-001",
            blocker_type="task",
            required_status="completed",
            current_status="production_ready",  # Further along
            blocks_transition_to="in_progress",
            last_checked=now,
        )
        self.assertTrue(dep.is_satisfied())

        # Current < Required (not satisfied)
        dep2 = DependencyStatus(
            blocker_id="backend-1-task-002",
            blocker_type="task",
            required_status="completed",
            current_status="in_progress",  # Not far enough
            blocks_transition_to="in_progress",
            last_checked=now,
        )
        self.assertFalse(dep2.is_satisfied())

    def test_is_satisfied_invalid_status(self):
        """Test is_satisfied with status not in progression."""
        now = datetime.now(timezone.utc)
        dep = DependencyStatus(
            blocker_id="backend-1-task-001",
            blocker_type="task",
            required_status="invalid_status",
            current_status="invalid_status",
            blocks_transition_to="in_progress",
            last_checked=now,
        )

        # Should fall back to exact match
        self.assertTrue(dep.is_satisfied())

        dep2 = DependencyStatus(
            blocker_id="backend-1-task-002",
            blocker_type="task",
            required_status="invalid_status",
            current_status="other_status",
            blocks_transition_to="in_progress",
            last_checked=now,
        )
        self.assertFalse(dep2.is_satisfied())

    def test_blocks_transition_satisfied(self):
        """Test blocks_transition when dependency is satisfied."""
        now = datetime.now(timezone.utc)
        dep = DependencyStatus(
            blocker_id="backend-1-task-001",
            blocker_type="task",
            required_status="completed",
            current_status="completed",  # Satisfied
            blocks_transition_to="in_progress",
            last_checked=now,
        )

        # Should not block any transition when satisfied
        self.assertFalse(dep.blocks_transition("in_progress"))
        self.assertFalse(dep.blocks_transition("completed"))

    def test_blocks_transition_unsatisfied(self):
        """Test blocks_transition when dependency is not satisfied."""
        now = datetime.now(timezone.utc)
        dep = DependencyStatus(
            blocker_id="backend-1-task-001",
            blocker_type="task",
            required_status="completed",
            current_status="in_progress",  # Not satisfied
            blocks_transition_to="in_progress",
            last_checked=now,
        )

        # Should block the specified transition
        self.assertTrue(dep.blocks_transition("in_progress"))
        self.assertTrue(dep.blocks_transition("completed"))

        # Should not block earlier transitions
        self.assertFalse(dep.blocks_transition("not_started"))

    def test_blocks_transition_progression(self):
        """Test blocks_transition with status progression logic."""
        now = datetime.now(timezone.utc)
        dep = DependencyStatus(
            blocker_id="backend-1-task-001",
            blocker_type="task",
            required_status="completed",
            current_status="in_progress",
            blocks_transition_to="completed",  # Blocks completed
            last_checked=now,
        )

        # Should not block earlier transitions
        self.assertFalse(dep.blocks_transition("not_started"))
        self.assertFalse(dep.blocks_transition("in_progress"))

        # Should block transitions >= blocks_transition_to
        self.assertTrue(dep.blocks_transition("completed"))
        self.assertTrue(dep.blocks_transition("production_ready"))
        self.assertTrue(dep.blocks_transition("deployed"))


if __name__ == "__main__":
    unittest.main()
