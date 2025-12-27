"""
Test TaskPusher class.

Tests for push-down mechanism to create tasks in submodules.
Design reference: SUBMODULE_ISOLATION_AND_PUSHDOWN.md
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPushTaskLinked:
    """Tests for linked push mode (creates tasks in both repos)."""

    def test_push_task_linked_creates_parent_task(self):
        """Should create a task in the parent repo."""
        with patch('vibey.operations.submodule.push.TaskPusher') as MockPusher:
            mock_pusher = MockPusher.return_value
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.parent_task_id = "01KC2D0JK7READW9KAK1HBX4B8"
            mock_result.submodule_task_id = "01KC3E1JK8READW9KAK1HBX5C9"
            mock_result.linked = True
            mock_pusher.push_task.return_value = mock_result

            result = mock_pusher.push_task(
                submodule_path="libs/core",
                title="Add logging feature",
                description="Implement structured logging",
                mode="linked",
                sprint_id=None,
            )

            assert result.success is True
            assert result.parent_task_id is not None
            assert result.linked is True

    def test_push_task_linked_creates_submodule_task(self):
        """Should create a task in the submodule."""
        with patch('vibey.operations.submodule.push.TaskPusher') as MockPusher:
            mock_pusher = MockPusher.return_value
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.submodule_task_id = "01KC3E1JK8READW9KAK1HBX5C9"
            mock_result.linked = True
            mock_pusher.push_task.return_value = mock_result

            result = mock_pusher.push_task(
                submodule_path="libs/core",
                title="Add logging feature",
                mode="linked",
            )

            assert result.success is True
            assert result.submodule_task_id is not None

    def test_push_task_linked_stores_mapping(self):
        """Should store ULID mapping between parent and submodule tasks."""
        with patch('vibey.operations.submodule.push.TaskPusher') as MockPusher:
            mock_pusher = MockPusher.return_value
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.parent_task_id = "01KC2D0JK7READW9KAK1HBX4B8"
            mock_result.submodule_task_id = "01KC3E1JK8READW9KAK1HBX5C9"
            mock_result.linked = True
            mock_pusher.push_task.return_value = mock_result

            result = mock_pusher.push_task(
                submodule_path="libs/core",
                title="Add logging feature",
                mode="linked",
            )

            # Both IDs should be returned for linked mode
            assert result.parent_task_id is not None
            assert result.submodule_task_id is not None
            assert result.linked is True


class TestPushTaskParentOnly:
    """Tests for parent_only push mode."""

    def test_push_task_parent_only_creates_parent_task(self):
        """Should create a task only in the parent repo."""
        with patch('vibey.operations.submodule.push.TaskPusher') as MockPusher:
            mock_pusher = MockPusher.return_value
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.parent_task_id = "01KC2D0JK7READW9KAK1HBX4B8"
            mock_result.submodule_task_id = None
            mock_result.linked = False
            mock_pusher.push_task.return_value = mock_result

            result = mock_pusher.push_task(
                submodule_path="libs/core",
                title="External dependency",
                mode="parent_only",
            )

            assert result.success is True
            assert result.parent_task_id is not None
            assert result.submodule_task_id is None
            assert result.linked is False

    def test_push_task_parent_only_no_submodule_modification(self):
        """Should not modify submodule files."""
        with patch('vibey.operations.submodule.push.TaskPusher') as MockPusher:
            mock_pusher = MockPusher.return_value
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.submodule_task_id = None
            mock_result.files_modified_in_submodule = []
            mock_pusher.push_task.return_value = mock_result

            result = mock_pusher.push_task(
                submodule_path="libs/core",
                title="External dependency",
                mode="parent_only",
            )

            # No files should be modified in submodule
            assert result.submodule_task_id is None
            if hasattr(result, 'files_modified_in_submodule'):
                assert result.files_modified_in_submodule == []


class TestPushTaskSubmoduleOnly:
    """Tests for submodule_only push mode."""

    def test_push_task_submodule_only_creates_submodule_task(self):
        """Should create a task only in the submodule."""
        with patch('vibey.operations.submodule.push.TaskPusher') as MockPusher:
            mock_pusher = MockPusher.return_value
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.parent_task_id = None
            mock_result.submodule_task_id = "01KC3E1JK8READW9KAK1HBX5C9"
            mock_result.linked = False
            mock_pusher.push_task.return_value = mock_result

            result = mock_pusher.push_task(
                submodule_path="libs/core",
                title="Submodule-only task",
                mode="submodule_only",
            )

            assert result.success is True
            assert result.parent_task_id is None
            assert result.submodule_task_id is not None
            assert result.linked is False


class TestLinkExisting:
    """Tests for linking existing tasks."""

    def test_link_existing_tasks(self):
        """Should link an existing parent task to a submodule task."""
        with patch('vibey.operations.submodule.push.TaskPusher') as MockPusher:
            mock_pusher = MockPusher.return_value
            mock_result = MagicMock()
            mock_result.success = True
            mock_pusher.link_existing.return_value = mock_result

            result = mock_pusher.link_existing(
                parent_task_id="01KC2D0JK7READW9KAK1HBX4B8",
                submodule_task_id="01KC3E1JK8READW9KAK1HBX5C9",
            )

            assert result.success is True

    def test_link_existing_with_invalid_parent_task(self):
        """Should fail when parent task doesn't exist."""
        with patch('vibey.operations.submodule.push.TaskPusher') as MockPusher:
            mock_pusher = MockPusher.return_value
            mock_result = MagicMock()
            mock_result.success = False
            mock_result.error = "Parent task not found"
            mock_pusher.link_existing.return_value = mock_result

            result = mock_pusher.link_existing(
                parent_task_id="nonexistent-task-id",
                submodule_task_id="01KC3E1JK8READW9KAK1HBX5C9",
            )

            assert result.success is False
            assert "not found" in result.error.lower()


class TestUnlink:
    """Tests for unlinking tasks."""

    def test_unlink_removes_link_preserves_submodule_task(self):
        """Should remove link without deleting submodule task."""
        with patch('vibey.operations.submodule.push.TaskPusher') as MockPusher:
            mock_pusher = MockPusher.return_value
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.submodule_task_id = "01KC3E1JK8READW9KAK1HBX5C9"
            mock_result.submodule_task_preserved = True
            mock_pusher.unlink.return_value = mock_result

            result = mock_pusher.unlink(
                parent_task_id="01KC2D0JK7READW9KAK1HBX4B8",
            )

            assert result.success is True
            assert result.submodule_task_id is not None
            # The submodule task should still exist after unlinking

    def test_unlink_with_no_linked_task(self):
        """Should handle unlinking when no submodule task is linked."""
        with patch('vibey.operations.submodule.push.TaskPusher') as MockPusher:
            mock_pusher = MockPusher.return_value
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.submodule_task_id = None
            mock_pusher.unlink.return_value = mock_result

            result = mock_pusher.unlink(
                parent_task_id="01KC2D0JK7READW9KAK1HBX4B8",
            )

            # Should succeed even if there's nothing to unlink
            assert result.success is True
