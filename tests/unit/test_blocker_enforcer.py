"""
Tests for blocker enforcement module.
"""

import pytest
import tempfile
import yaml
from datetime import datetime, timezone
from pathlib import Path

from vibey.operations.git.blocker_enforcer import (
    EnforcementMode,
    BlockerInfo,
    BlockedItem,
    BlockerViolation,
    EnforcementResult,
    BlockerStatus,
    BlockerEnforcer,
    check_commit_blockers,
    get_blocker_status,
    format_blocker_status,
)


@pytest.fixture
def temp_repo():
    """Create a temporary repository structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)

        # Create roadmap directory structure
        roadmap_root = repo / ".vibey" / "roadmap"
        roadmap_root.mkdir(parents=True)

        # Create a track
        track_dir = roadmap_root / "test-track"
        track_dir.mkdir()

        track_yaml = {
            'track': {
                'id': 'test-track',
                'name': 'Test Track',
                'status': 'in_progress',
                'blocked': False,
                'blocked_by': []
            }
        }
        with open(track_dir / "track.yaml", 'w') as f:
            yaml.dump(track_yaml, f)

        # Create a sprint
        sprint_dir = track_dir / "test-sprint-1"
        sprint_dir.mkdir()

        sprint_yaml = {
            'sprint': {
                'id': 'test-sprint-1',
                'name': 'Test Sprint 1',
                'status': 'in_progress',
                'blocked': False,
                'blocked_by': []
            }
        }
        with open(sprint_dir / "sprint.yaml", 'w') as f:
            yaml.dump(sprint_yaml, f)

        # Create tasks
        task1_dir = sprint_dir / "test-sprint-1-task-001"
        task1_dir.mkdir()

        task1_yaml = {
            'task': {
                'id': 'test-sprint-1-task-001',
                'name': 'Task 1 - No Blockers',
                'status': 'not_started',
                'blocked': False,
                'blocked_by': []
            }
        }
        with open(task1_dir / "task.yaml", 'w') as f:
            yaml.dump(task1_yaml, f)

        task2_dir = sprint_dir / "test-sprint-1-task-002"
        task2_dir.mkdir()

        task2_yaml = {
            'task': {
                'id': 'test-sprint-1-task-002',
                'name': 'Task 2 - Blocked',
                'status': 'not_started',
                'blocked': True,
                'blocked_by': ['test-sprint-1-task-001']
            }
        }
        with open(task2_dir / "task.yaml", 'w') as f:
            yaml.dump(task2_yaml, f)

        # Initialize git repo
        import subprocess
        subprocess.run(['git', 'init'], cwd=repo, capture_output=True)
        subprocess.run(['git', 'add', '.'], cwd=repo, capture_output=True)
        subprocess.run(
            ['git', 'commit', '-m', 'Initial commit'],
            cwd=repo,
            capture_output=True,
            env={'GIT_AUTHOR_NAME': 'Test', 'GIT_AUTHOR_EMAIL': 'test@test.com',
                 'GIT_COMMITTER_NAME': 'Test', 'GIT_COMMITTER_EMAIL': 'test@test.com'}
        )

        yield repo


class TestBlockerEnforcer:
    """Tests for BlockerEnforcer class."""

    def test_init_default_mode(self, temp_repo):
        """Test default initialization."""
        enforcer = BlockerEnforcer(str(temp_repo))
        assert enforcer.mode == EnforcementMode.ADVISORY

    def test_init_custom_mode(self, temp_repo):
        """Test initialization with custom mode."""
        enforcer = BlockerEnforcer(str(temp_repo), EnforcementMode.BLOCKING)
        assert enforcer.mode == EnforcementMode.BLOCKING

    def test_get_blocker_status_no_blockers(self, temp_repo):
        """Test getting blocker status with no blocked items."""
        enforcer = BlockerEnforcer(str(temp_repo))
        status = enforcer.get_blocker_status()

        # Task 2 is marked as blocked
        assert status.total_blocked == 1
        assert len(status.blocked_tasks) == 1
        assert status.blocked_tasks[0].item_id == 'test-sprint-1-task-002'

    def test_get_task_blockers(self, temp_repo):
        """Test extracting blockers from task YAML."""
        enforcer = BlockerEnforcer(str(temp_repo))

        task_path = temp_repo / ".vibey" / "roadmap" / "test-track" / "test-sprint-1" / "test-sprint-1-task-002" / "task.yaml"
        blockers = enforcer._get_task_blockers(task_path)

        assert len(blockers) == 1
        assert blockers[0].blocker_id == 'test-sprint-1-task-001'

    def test_check_commit_off_mode(self, temp_repo):
        """Test commit check with OFF mode."""
        enforcer = BlockerEnforcer(str(temp_repo), EnforcementMode.OFF)
        result = enforcer.check_commit("Test commit")

        assert result.allowed
        assert result.mode == EnforcementMode.OFF
        assert len(result.violations) == 0

    def test_check_commit_advisory_mode(self, temp_repo):
        """Test commit check with ADVISORY mode."""
        enforcer = BlockerEnforcer(str(temp_repo), EnforcementMode.ADVISORY)
        result = enforcer.check_commit("Task: test-sprint-1-task-002")

        # Advisory mode allows but warns
        assert result.allowed
        assert result.mode == EnforcementMode.ADVISORY

    def test_check_commit_blocking_mode_no_violations(self, temp_repo):
        """Test commit check with BLOCKING mode and no violations."""
        enforcer = BlockerEnforcer(str(temp_repo), EnforcementMode.BLOCKING)
        result = enforcer.check_commit("Task: test-sprint-1-task-001")

        assert result.allowed
        assert len(result.violations) == 0

    def test_extract_task_ids_from_commit_msg(self, temp_repo):
        """Test task ID extraction from commit messages."""
        enforcer = BlockerEnforcer(str(temp_repo))

        # Test various formats
        msg1 = "Task: test-sprint-1-task-001"
        ids1 = enforcer._extract_task_ids_from_commit_msg(msg1)
        assert 'test-sprint-1-task-001' in ids1

        msg2 = "[test-sprint-1-task-002] Fix bug"
        ids2 = enforcer._extract_task_ids_from_commit_msg(msg2)
        assert 'test-sprint-1-task-002' in ids2

        msg3 = "Completes test-sprint-1-task-003"
        ids3 = enforcer._extract_task_ids_from_commit_msg(msg3)
        assert 'test-sprint-1-task-003' in ids3


class TestEnforcementMode:
    """Tests for EnforcementMode enum."""

    def test_mode_values(self):
        """Test enforcement mode values."""
        assert EnforcementMode.OFF.value == "off"
        assert EnforcementMode.ADVISORY.value == "advisory"
        assert EnforcementMode.BLOCKING.value == "blocking"
        assert EnforcementMode.AUDIT.value == "audit"


class TestBlockerInfo:
    """Tests for BlockerInfo dataclass."""

    def test_blocker_info_creation(self):
        """Test creating a BlockerInfo."""
        info = BlockerInfo(
            blocker_id='task-001',
            blocker_type='task',
            blocker_name='Task 1',
            blocker_status='in_progress',
            required_status='completed'
        )

        assert info.blocker_id == 'task-001'
        assert info.blocker_type == 'task'
        assert info.required_status == 'completed'


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_blocker_status(self, temp_repo):
        """Test get_blocker_status convenience function."""
        status = get_blocker_status(str(temp_repo))

        assert isinstance(status, BlockerStatus)
        assert status.checked_at is not None

    def test_format_blocker_status_no_blockers(self, temp_repo):
        """Test format_blocker_status with some blocked items."""
        status = get_blocker_status(str(temp_repo))
        formatted = format_blocker_status(status)

        assert "Blocker Status Report" in formatted
        # Should show the blocked task
        assert "blocked" in formatted.lower()

    def test_format_blocker_status_empty(self):
        """Test format_blocker_status with no blocked items."""
        status = BlockerStatus(
            blocked_tasks=[],
            blocked_sprints=[],
            blocked_tracks=[],
            total_blocked=0,
            checked_at=datetime.now(timezone.utc)
        )
        formatted = format_blocker_status(status)

        assert "No blocked items found" in formatted


class TestBlockedItem:
    """Tests for BlockedItem dataclass."""

    def test_blocked_item_creation(self):
        """Test creating a BlockedItem."""
        item = BlockedItem(
            item_id='task-001',
            item_type='task',
            item_name='Test Task',
            blockers=[
                BlockerInfo(
                    blocker_id='task-000',
                    blocker_type='task',
                    blocker_name='Blocker Task',
                    blocker_status='in_progress',
                    required_status='completed'
                )
            ]
        )

        assert item.item_id == 'task-001'
        assert len(item.blockers) == 1


class TestEnforcementResult:
    """Tests for EnforcementResult dataclass."""

    def test_enforcement_result_allowed(self):
        """Test creating an allowed result."""
        result = EnforcementResult(
            allowed=True,
            mode=EnforcementMode.ADVISORY,
            violations=[],
            warnings=[]
        )

        assert result.allowed
        assert result.mode == EnforcementMode.ADVISORY

    def test_enforcement_result_blocked(self):
        """Test creating a blocked result."""
        result = EnforcementResult(
            allowed=False,
            mode=EnforcementMode.BLOCKING,
            violations=[
                BlockerViolation(
                    item_id='task-001',
                    item_type='task',
                    operation='commit',
                    blockers=[],
                    severity='error',
                    message='Task is blocked'
                )
            ],
            warnings=[]
        )

        assert not result.allowed
        assert len(result.violations) == 1
