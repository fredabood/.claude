"""
Tests for vibey.operations.roadmap.transitions module.

Tests the unified transition functions: start_item(), complete_item(),
and the supporting transition_* functions.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from vibey.operations.roadmap.transitions import (
    start_item,
    complete_item,
    TransitionBlockedError,
    transition_ticket,
)
from vibey.roadmap.models.ticket.enums import TicketStatus


class TestStartItem:
    """Tests for start_item() function."""

    def test_start_task_success(self, tmp_path):
        """Starting an existing task should succeed."""
        # Create minimal roadmap structure
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        (roadmap_root / "tasks").mkdir(parents=True)
        (roadmap_root / "sprints").mkdir()
        (roadmap_root / "tracks").mkdir()

        # Create task file
        task_id = "01TESTABCDEFGHIJKLMNOPQR"
        task_file = roadmap_root / "tasks" / f"{task_id}.yaml"
        task_file.write_text(f"""task:
  id: {task_id}
  title: Test Task
  status: not_started
  sprint_id: 01TESTSPRINTAAAAAAAAAAAA
  track_id: 01TESTTRACKAAAAAAAAAAAA
  roadmap_id: 01TESTROADMAPAAAAAAAAA
  estimated_tokens: 1000
""")

        # Mock the transition_task function to avoid full execution
        with patch('vibey.operations.roadmap.transitions.transition_task') as mock_transition:
            mock_ticket = MagicMock()
            mock_ticket.id = task_id
            mock_ticket.status = TicketStatus.IN_PROGRESS
            mock_transition.return_value = mock_ticket

            result = start_item(tmp_path, task_id)

            assert result['id'] == task_id
            assert result['status'] == 'in_progress'
            assert result['type'] == 'task'
            mock_transition.assert_called_once_with(task_id, TicketStatus.IN_PROGRESS, tmp_path)

    def test_start_sprint_success(self, tmp_path):
        """Starting an existing sprint should succeed."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        (roadmap_root / "tasks").mkdir(parents=True)
        (roadmap_root / "sprints").mkdir()
        (roadmap_root / "tracks").mkdir()

        sprint_id = "01TESTSPRINTAAAAAAAAAAAA"
        sprint_file = roadmap_root / "sprints" / f"{sprint_id}.yaml"
        sprint_file.write_text(f"""sprint:
  id: {sprint_id}
  name: Test Sprint
  status: not_started
  track_id: 01TESTTRACKAAAAAAAAAAAA
""")

        with patch('vibey.operations.roadmap.transitions.transition_sprint') as mock_transition:
            mock_ticket = MagicMock()
            mock_ticket.id = sprint_id
            mock_ticket.status = TicketStatus.IN_PROGRESS
            mock_transition.return_value = mock_ticket

            result = start_item(tmp_path, sprint_id)

            assert result['id'] == sprint_id
            assert result['status'] == 'in_progress'
            assert result['type'] == 'sprint'

    def test_start_nonexistent_raises_file_not_found(self, tmp_path):
        """Starting non-existent item should raise FileNotFoundError."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        (roadmap_root / "tasks").mkdir(parents=True)
        (roadmap_root / "sprints").mkdir()
        (roadmap_root / "tracks").mkdir()

        with pytest.raises(FileNotFoundError) as exc:
            start_item(tmp_path, "01NONEXISTENTAAAAAAAAAAA")

        assert "Item not found" in str(exc.value)


class TestCompleteItem:
    """Tests for complete_item() function."""

    def test_complete_task_success(self, tmp_path):
        """Completing an in-progress task should succeed."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        (roadmap_root / "tasks").mkdir(parents=True)
        (roadmap_root / "sprints").mkdir()
        (roadmap_root / "tracks").mkdir()

        task_id = "01TESTABCDEFGHIJKLMNOPQR"
        task_file = roadmap_root / "tasks" / f"{task_id}.yaml"
        task_file.write_text(f"""task:
  id: {task_id}
  title: Test Task
  status: in_progress
  sprint_id: 01TESTSPRINTAAAAAAAAAAAA
  track_id: 01TESTTRACKAAAAAAAAAAAA
  roadmap_id: 01TESTROADMAPAAAAAAAAA
  estimated_tokens: 1000
""")

        with patch('vibey.operations.roadmap.transitions.transition_task') as mock_transition:
            mock_ticket = MagicMock()
            mock_ticket.id = task_id
            mock_ticket.status = TicketStatus.COMPLETED
            mock_transition.return_value = mock_ticket

            result = complete_item(tmp_path, task_id, notes="Test completion")

            assert result['id'] == task_id
            assert result['status'] == 'completed'
            assert result['type'] == 'task'
            assert result['notes'] == "Test completion"
            mock_transition.assert_called_once_with(task_id, TicketStatus.COMPLETED, tmp_path)

    def test_complete_nonexistent_raises_file_not_found(self, tmp_path):
        """Completing non-existent item should raise FileNotFoundError."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        (roadmap_root / "tasks").mkdir(parents=True)
        (roadmap_root / "sprints").mkdir()
        (roadmap_root / "tracks").mkdir()

        with pytest.raises(FileNotFoundError) as exc:
            complete_item(tmp_path, "01NONEXISTENTAAAAAAAAAAA")

        assert "Item not found" in str(exc.value)


class TestTransitionBlockedError:
    """Tests for TransitionBlockedError exception."""

    def test_error_message_format(self):
        """Error message should include entity ID, target status, and reasons."""
        error = TransitionBlockedError(
            entity_id="01TESTENTITY",
            target_status=TicketStatus.COMPLETED,
            reasons=["Task has unmet criteria", "Missing deliverable file"]
        )

        message = str(error)
        assert "01TESTENTITY" in message
        assert "completed" in message
        assert "Task has unmet criteria" in message

    def test_error_attributes(self):
        """Error should have accessible attributes."""
        reasons = ["Reason 1", "Reason 2"]
        error = TransitionBlockedError(
            entity_id="01TEST",
            target_status=TicketStatus.IN_PROGRESS,
            reasons=reasons
        )

        assert error.entity_id == "01TEST"
        assert error.target_status == TicketStatus.IN_PROGRESS
        assert error.reasons == reasons

    def test_error_with_empty_reasons(self):
        """Error with no reasons should still be valid."""
        error = TransitionBlockedError(
            entity_id="01TEST",
            target_status=TicketStatus.COMPLETED,
            reasons=[]
        )

        message = str(error)
        assert "01TEST" in message
        assert "completed" in message


class TestTransitionTicket:
    """Tests for transition_ticket() function."""

    def test_transition_to_in_progress(self):
        """Transitioning ticket to IN_PROGRESS should call start()."""
        mock_ticket = MagicMock()
        mock_ticket.can_transition_to.return_value = (True, [])
        mock_ticket.start.return_value = mock_ticket

        result = transition_ticket(mock_ticket, TicketStatus.IN_PROGRESS)

        mock_ticket.can_transition_to.assert_called_once_with(TicketStatus.IN_PROGRESS)
        mock_ticket.start.assert_called_once()

    def test_transition_to_completed(self):
        """Transitioning ticket to COMPLETED should call complete()."""
        mock_ticket = MagicMock()
        mock_ticket.can_transition_to.return_value = (True, [])
        mock_ticket.complete.return_value = mock_ticket

        result = transition_ticket(mock_ticket, TicketStatus.COMPLETED)

        mock_ticket.can_transition_to.assert_called_once_with(TicketStatus.COMPLETED)
        mock_ticket.complete.assert_called_once()

    def test_blocked_transition_raises_error(self):
        """Blocked transition should raise TransitionBlockedError."""
        mock_ticket = MagicMock()
        mock_ticket.id = "01TESTTICKET"
        mock_ticket.can_transition_to.return_value = (False, ["Blocking reason"])

        with pytest.raises(TransitionBlockedError) as exc:
            transition_ticket(mock_ticket, TicketStatus.COMPLETED)

        assert exc.value.entity_id == "01TESTTICKET"
        assert "Blocking reason" in exc.value.reasons
