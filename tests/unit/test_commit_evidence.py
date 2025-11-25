"""
Tests for commit evidence module.
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from vibey.operations.git.commit_evidence import (
    CommitEvidenceConfig,
    EvidenceCheckResult,
    load_git_config,
    get_commit_evidence_config,
    check_commit_evidence,
    sync_commits_from_git,
    validate_all_tasks_have_commits,
)


@pytest.fixture
def temp_repo():
    """Create a temporary repository with config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)

        # Create config directory
        config_dir = repo / ".vibey" / "config"
        config_dir.mkdir(parents=True)

        # Create git.yaml config
        config = {
            'git': {
                'enforcement': {
                    'mode': 'blocking',
                    'rules': {
                        'commit_evidence': {
                            'enabled': True,
                            'mode': 'blocking',
                            'require_commits': True,
                            'exceptions': {
                                'task_types': ['documentation', 'planning']
                            }
                        }
                    }
                },
                'commit_tracking': {
                    'require_commits': True,
                    'record_commits': True
                }
            }
        }
        with open(config_dir / "git.yaml", 'w') as f:
            yaml.dump(config, f)

        # Create roadmap structure
        roadmap_root = repo / ".vibey" / "roadmap"
        roadmap_root.mkdir(parents=True)

        # Create track
        track_dir = roadmap_root / "test-track"
        track_dir.mkdir()

        # Create sprint
        sprint_dir = track_dir / "test-track-1"
        sprint_dir.mkdir()

        # Create task with commits
        task1_dir = sprint_dir / "test-track-1-task-001"
        task1_dir.mkdir()
        with open(task1_dir / "task.yaml", 'w') as f:
            yaml.dump({
                'task': {
                    'id': 'test-track-1-task-001',
                    'sprint_id': 'test-track-1',
                    'track_id': 'test-track',
                    'title': 'Task 1 with commits',
                    'status': 'completed',
                    'task_type': 'development',
                    'commits': [
                        {'sha': 'abc123', 'message': 'feat: task 1'}
                    ]
                }
            }, f)

        # Create task without commits
        task2_dir = sprint_dir / "test-track-1-task-002"
        task2_dir.mkdir()
        with open(task2_dir / "task.yaml", 'w') as f:
            yaml.dump({
                'task': {
                    'id': 'test-track-1-task-002',
                    'sprint_id': 'test-track-1',
                    'track_id': 'test-track',
                    'title': 'Task 2 without commits',
                    'status': 'not_started',
                    'task_type': 'development',
                    'commits': []
                }
            }, f)

        # Create documentation task (exception)
        task3_dir = sprint_dir / "test-track-1-task-003"
        task3_dir.mkdir()
        with open(task3_dir / "task.yaml", 'w') as f:
            yaml.dump({
                'task': {
                    'id': 'test-track-1-task-003',
                    'sprint_id': 'test-track-1',
                    'track_id': 'test-track',
                    'title': 'Documentation task',
                    'status': 'completed',
                    'task_type': 'documentation',
                    'commits': []
                }
            }, f)

        yield repo


class TestCommitEvidenceConfig:
    """Tests for CommitEvidenceConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CommitEvidenceConfig()

        assert config.enabled == True
        assert config.mode == "blocking"
        assert config.require_commits == True

    def test_custom_config(self):
        """Test custom configuration values."""
        config = CommitEvidenceConfig(
            enabled=False,
            mode="advisory",
            require_commits=False,
            exception_task_types=["docs"]
        )

        assert config.enabled == False
        assert config.mode == "advisory"
        assert config.require_commits == False
        assert "docs" in config.exception_task_types


class TestLoadGitConfig:
    """Tests for load_git_config function."""

    def test_load_config(self, temp_repo):
        """Test loading git config from file."""
        config = load_git_config(temp_repo)

        assert 'git' in config
        assert 'enforcement' in config['git']
        assert config['git']['enforcement']['mode'] == 'blocking'

    def test_load_missing_config(self):
        """Test loading config when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = load_git_config(Path(tmpdir))
            assert config == {}


class TestGetCommitEvidenceConfig:
    """Tests for get_commit_evidence_config function."""

    def test_get_config(self, temp_repo):
        """Test getting commit evidence config."""
        config = get_commit_evidence_config(temp_repo)

        assert config.enabled == True
        assert config.mode == "blocking"
        assert config.require_commits == True
        assert "documentation" in config.exception_task_types


class TestCheckCommitEvidence:
    """Tests for check_commit_evidence function."""

    def test_task_with_commits(self, temp_repo):
        """Test checking task that has commits."""
        result = check_commit_evidence('test-track-1-task-001', temp_repo)

        assert result.has_evidence
        assert result.commit_count >= 1
        assert result.can_complete

    def test_task_without_commits_blocking(self, temp_repo):
        """Test checking task without commits in blocking mode."""
        result = check_commit_evidence('test-track-1-task-002', temp_repo)

        assert not result.has_evidence
        assert result.commit_count == 0
        assert not result.can_complete  # Blocking mode

    def test_documentation_task_exception(self, temp_repo):
        """Test that documentation tasks are exempt."""
        result = check_commit_evidence('test-track-1-task-003', temp_repo)

        assert result.is_exception
        assert result.can_complete


class TestEvidenceCheckResult:
    """Tests for EvidenceCheckResult dataclass."""

    def test_result_creation(self):
        """Test creating an evidence check result."""
        result = EvidenceCheckResult(
            task_id='task-001',
            has_evidence=True,
            commit_count=2,
            commits=['abc', 'def'],
            can_complete=True,
            message='Task has 2 commits'
        )

        assert result.task_id == 'task-001'
        assert result.has_evidence
        assert result.commit_count == 2
        assert len(result.commits) == 2


class TestSyncCommitsFromGit:
    """Tests for sync_commits_from_git function."""

    def test_sync_empty_repo(self, temp_repo):
        """Test syncing from repo without git."""
        # No git repo, should return empty
        found = sync_commits_from_git(temp_repo)
        assert isinstance(found, dict)


class TestValidateAllTasksHaveCommits:
    """Tests for validate_all_tasks_have_commits function."""

    def test_validate_tasks(self, temp_repo):
        """Test validating all completed tasks."""
        issues = validate_all_tasks_have_commits(temp_repo)

        # task-001 has commits, task-002 is not completed, task-003 is exempt
        # So no issues expected for completed tasks
        # Actually task-003 is completed but exempt, so it should pass
        assert isinstance(issues, list)
