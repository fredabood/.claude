"""
Tests for Git Hooks functionality.

Task: git-integration-2-task-007
"""

import pytest
import yaml
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timezone

from vibey.operations.git.hooks import PreCommitHook, CommitMsgHook, ValidationIssue, HookConfig
from vibey.operations.git.status_updater import TaskStatusUpdater, StatusUpdate
from vibey.operations.git.branch_linker import BranchLinker, BranchType


class TestPreCommitHook:
    """Tests for pre-commit hook."""

    @pytest.fixture
    def temp_repo(self):
        """Create temporary git repository with vibey structure."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True, capture_output=True)

        # Create .vibey structure
        vibey_dir = repo_path / ".vibey"
        vibey_dir.mkdir()

        config_dir = vibey_dir / "config"
        config_dir.mkdir()

        roadmap_dir = vibey_dir / "roadmap"
        roadmap_dir.mkdir()

        # Create test sprint
        track_dir = roadmap_dir / "test-track"
        track_dir.mkdir()

        sprint_dir = track_dir / "test-sprint-1"
        sprint_dir.mkdir()

        yield repo_path

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_init_hook(self, temp_repo):
        """Test hook initialization."""
        hook = PreCommitHook(repo_path=str(temp_repo))
        assert hook.repo_path == temp_repo
        assert isinstance(hook.config, HookConfig)
        assert isinstance(hook.issues, list)

    def test_yaml_validation_valid(self, temp_repo):
        """Test YAML validation with valid file."""
        sprint_file = temp_repo / ".vibey" / "roadmap" / "test-track" / "test-sprint-1" / "sprint.yaml"

        # Create valid YAML
        sprint_data = {
            "sprint": {
                "id": "test-sprint-1",
                "name": "Test Sprint",
                "status": "not_started",
                "tasks": []
            }
        }

        with open(sprint_file, 'w') as f:
            yaml.dump(sprint_data, f)

        hook = PreCommitHook(repo_path=str(temp_repo))
        is_valid = hook._validate_yaml_syntax(str(sprint_file))

        assert is_valid is True
        assert len(hook.issues) == 0

    def test_yaml_validation_invalid(self, temp_repo):
        """Test YAML validation with invalid file."""
        sprint_file = temp_repo / ".vibey" / "roadmap" / "test-track" / "test-sprint-1" / "sprint.yaml"

        # Create invalid YAML
        with open(sprint_file, 'w') as f:
            f.write("invalid: yaml: content:\n  - bad indentation")

        hook = PreCommitHook(repo_path=str(temp_repo))
        is_valid = hook._validate_yaml_syntax(str(sprint_file))

        assert is_valid is False
        assert len(hook.issues) > 0
        assert any("YAML syntax error" in issue.message for issue in hook.issues)

    def test_config_loading(self, temp_repo):
        """Test configuration loading."""
        config_file = temp_repo / ".vibey" / "config" / "git.yaml"

        config_data = {
            "git": {
                "enforcement": {
                    "mode": "blocking",
                    "rules": {
                        "yaml_integrity": {
                            "enabled": True,
                            "mode": "blocking"
                        }
                    }
                }
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        hook = PreCommitHook(repo_path=str(temp_repo))

        assert hook.config.mode == "blocking"


class TestCommitMsgHook:
    """Tests for commit-msg hook."""

    @pytest.fixture
    def temp_repo(self):
        """Create temporary git repository with vibey structure."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Create .vibey structure
        vibey_dir = repo_path / ".vibey"
        vibey_dir.mkdir()

        roadmap_dir = vibey_dir / "roadmap"
        roadmap_dir.mkdir()

        # Create test track and sprint
        track_dir = roadmap_dir / "test-track"
        track_dir.mkdir()

        sprint_dir = track_dir / "test-sprint-1"
        sprint_dir.mkdir()

        # Create sprint with task
        sprint_file = sprint_dir / "sprint.yaml"
        sprint_data = {
            "sprint": {
                "id": "test-sprint-1",
                "name": "Test Sprint",
                "track_id": "test-track",
                "status": "not_started",
                "tasks": [
                    {
                        "id": "test-task-001",
                        "name": "Test Task",
                        "status": "not_started"
                    }
                ]
            }
        }

        with open(sprint_file, 'w') as f:
            yaml.dump(sprint_data, f)

        yield repo_path

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_init_hook(self, temp_repo):
        """Test hook initialization."""
        commit_msg_file = temp_repo / ".git" / "COMMIT_EDITMSG"
        commit_msg_file.parent.mkdir(parents=True, exist_ok=True)
        commit_msg_file.write_text("feat: test commit")

        hook = CommitMsgHook(str(commit_msg_file), repo_path=str(temp_repo))
        assert hook.commit_msg_file == commit_msg_file
        assert hook.repo_path == temp_repo

    def test_read_commit_message(self, temp_repo):
        """Test reading commit message."""
        commit_msg_file = temp_repo / ".git" / "COMMIT_EDITMSG"
        commit_msg_file.parent.mkdir(parents=True, exist_ok=True)

        message = "feat(test-task-001): implement feature\n\nTask: test-task-001"
        commit_msg_file.write_text(message)

        hook = CommitMsgHook(str(commit_msg_file), repo_path=str(temp_repo))
        read_message = hook._read_commit_message()

        assert read_message == message

    def test_load_roadmap_tasks(self, temp_repo):
        """Test loading tasks from roadmap."""
        commit_msg_file = temp_repo / ".git" / "COMMIT_EDITMSG"
        commit_msg_file.parent.mkdir(parents=True, exist_ok=True)
        commit_msg_file.write_text("feat: test")

        hook = CommitMsgHook(str(commit_msg_file), repo_path=str(temp_repo))
        tasks = hook._load_roadmap_tasks()

        assert "test-task-001" in tasks

    def test_validate_task_exists_valid(self, temp_repo):
        """Test validating existing task."""
        commit_msg_file = temp_repo / ".git" / "COMMIT_EDITMSG"
        commit_msg_file.parent.mkdir(parents=True, exist_ok=True)

        message = "feat(test-task-001): implement feature"
        commit_msg_file.write_text(message)

        hook = CommitMsgHook(str(commit_msg_file), repo_path=str(temp_repo))
        hook._validate_task_exists(message)

        # Should not create issues for valid task
        task_issues = [i for i in hook.issues if "not found" in i.message]
        assert len(task_issues) == 0

    def test_validate_task_exists_invalid(self, temp_repo):
        """Test validating non-existent task."""
        commit_msg_file = temp_repo / ".git" / "COMMIT_EDITMSG"
        commit_msg_file.parent.mkdir(parents=True, exist_ok=True)

        message = "feat(nonexistent-task): implement feature"
        commit_msg_file.write_text(message)

        hook = CommitMsgHook(str(commit_msg_file), repo_path=str(temp_repo))
        hook._validate_task_exists(message)

        # Should create warning for invalid task
        assert len(hook.issues) > 0
        assert any("not found" in issue.message for issue in hook.issues)


class TestTaskStatusUpdater:
    """Tests for automatic task status updates."""

    @pytest.fixture
    def temp_repo(self):
        """Create temporary git repository with test data."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Create .vibey structure
        vibey_dir = repo_path / ".vibey"
        vibey_dir.mkdir()

        roadmap_dir = vibey_dir / "roadmap"
        roadmap_dir.mkdir()

        # Create test track and sprint
        track_dir = roadmap_dir / "test-track"
        track_dir.mkdir()

        sprint_dir = track_dir / "test-sprint-1"
        sprint_dir.mkdir()

        # Create sprint with task
        sprint_file = sprint_dir / "sprint.yaml"
        sprint_data = {
            "sprint": {
                "id": "test-sprint-1",
                "name": "Test Sprint",
                "track_id": "test-track",
                "status": "not_started",
                "progress": {
                    "tasks_total": 1,
                    "tasks_completed": 0,
                    "completion_percent": 0
                },
                "tasks": [
                    {
                        "id": "test-task-001",
                        "name": "Test Task",
                        "status": "not_started"
                    }
                ]
            }
        }

        with open(sprint_file, 'w') as f:
            yaml.dump(sprint_data, f)

        yield repo_path

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_init_updater(self, temp_repo):
        """Test updater initialization."""
        updater = TaskStatusUpdater(repo_path=str(temp_repo))
        assert updater.repo_path == temp_repo
        assert updater.roadmap_dir == temp_repo / ".vibey" / "roadmap"

    def test_find_task_file(self, temp_repo):
        """Test finding task file."""
        updater = TaskStatusUpdater(repo_path=str(temp_repo))
        task_file = updater.find_task_file("test-task-001")

        assert task_file is not None
        assert task_file.name == "sprint.yaml"

    def test_update_task_status(self, temp_repo):
        """Test updating task status."""
        updater = TaskStatusUpdater(repo_path=str(temp_repo))

        # Process commit with status update
        result = updater.process_commit(
            commit_sha="abc1234",
            commit_message="feat(test-task-001): implement\n\nTask: test-task-001\nStatus: completed",
            dry_run=False
        )

        assert result.successful_updates == 1
        assert result.failed_updates == 0

        # Verify task was updated
        sprint_file = temp_repo / ".vibey" / "roadmap" / "test-track" / "test-sprint-1" / "sprint.yaml"
        with open(sprint_file) as f:
            data = yaml.safe_load(f)

        task = data["sprint"]["tasks"][0]
        assert task["status"] == "completed"
        assert "abc1234" in task["commits"]

    def test_dry_run_mode(self, temp_repo):
        """Test dry-run mode doesn't modify files."""
        updater = TaskStatusUpdater(repo_path=str(temp_repo))

        # Process with dry-run
        result = updater.process_commit(
            commit_sha="abc1234",
            commit_message="feat(test-task-001): implement\n\nTask: test-task-001\nStatus: completed",
            dry_run=True
        )

        assert result.successful_updates == 1

        # Verify task was NOT updated
        sprint_file = temp_repo / ".vibey" / "roadmap" / "test-track" / "test-sprint-1" / "sprint.yaml"
        with open(sprint_file) as f:
            data = yaml.safe_load(f)

        task = data["sprint"]["tasks"][0]
        assert task["status"] == "not_started"


class TestBranchLinker:
    """Tests for branch-task linking."""

    @pytest.fixture
    def temp_repo(self):
        """Create temporary git repository."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True, capture_output=True)

        # Create initial commit
        test_file = repo_path / "README.md"
        test_file.write_text("# Test")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True)

        # Create .vibey structure
        vibey_dir = repo_path / ".vibey"
        vibey_dir.mkdir()

        roadmap_dir = vibey_dir / "roadmap"
        roadmap_dir.mkdir()

        # Create test track and sprint
        track_dir = roadmap_dir / "test-track"
        track_dir.mkdir()

        sprint_dir = track_dir / "test-sprint-1"
        sprint_dir.mkdir()

        # Create sprint with task
        sprint_file = sprint_dir / "sprint.yaml"
        sprint_data = {
            "sprint": {
                "id": "test-sprint-1",
                "name": "Test Sprint",
                "track_id": "test-track",
                "status": "not_started",
                "tasks": [
                    {
                        "id": "test-task-001",
                        "name": "Test Task",
                        "status": "not_started"
                    }
                ]
            }
        }

        with open(sprint_file, 'w') as f:
            yaml.dump(sprint_data, f)

        yield repo_path

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_init_linker(self, temp_repo):
        """Test linker initialization."""
        linker = BranchLinker(repo_path=str(temp_repo))
        assert linker.repo_path == temp_repo
        assert linker.is_git_repo()

    def test_parse_branch_name_task(self, temp_repo):
        """Test parsing task branch name."""
        linker = BranchLinker(repo_path=str(temp_repo))
        branch_type, item_id = linker.parse_branch_name("task/test-task-001")

        assert branch_type == BranchType.TASK
        assert item_id == "test-task-001"

    def test_parse_branch_name_sprint(self, temp_repo):
        """Test parsing sprint branch name."""
        linker = BranchLinker(repo_path=str(temp_repo))
        branch_type, item_id = linker.parse_branch_name("sprint/test-sprint-1")

        assert branch_type == BranchType.SPRINT
        assert item_id == "test-sprint-1"

    def test_parse_branch_name_other(self, temp_repo):
        """Test parsing non-vibey branch name."""
        linker = BranchLinker(repo_path=str(temp_repo))
        branch_type, item_id = linker.parse_branch_name("feature/my-feature")

        assert branch_type == BranchType.OTHER
        assert item_id is None

    def test_get_current_branch(self, temp_repo):
        """Test getting current branch."""
        linker = BranchLinker(repo_path=str(temp_repo))
        current = linker.get_current_branch()

        # Should be on main or master
        assert current in ["main", "master"]

    def test_create_branch(self, temp_repo):
        """Test creating a branch."""
        linker = BranchLinker(repo_path=str(temp_repo))

        success, error = linker.create_branch("task/test-task-001")

        assert success is True
        assert error is None
        assert linker.branch_exists("task/test-task-001")

    def test_link_branch_to_task(self, temp_repo):
        """Test linking branch to task."""
        linker = BranchLinker(repo_path=str(temp_repo))

        # Create branch first
        linker.create_branch("task/test-task-001")

        # Link to task
        success, error = linker.link_branch_to_task("test-task-001", "task/test-task-001")

        assert success is True
        assert error is None

        # Verify link was created
        sprint_file = temp_repo / ".vibey" / "roadmap" / "test-track" / "test-sprint-1" / "sprint.yaml"
        with open(sprint_file) as f:
            data = yaml.safe_load(f)

        task = data["sprint"]["tasks"][0]
        assert "branch" in task
        assert task["branch"]["name"] == "task/test-task-001"

    def test_suggest_branch_name(self, temp_repo):
        """Test branch name suggestion."""
        linker = BranchLinker(repo_path=str(temp_repo))
        suggested = linker.suggest_branch_name("test-task-001")

        assert suggested == "task/test-task-001"


class TestValidationIssue:
    """Tests for ValidationIssue dataclass."""

    def test_create_issue(self):
        """Test creating validation issue."""
        issue = ValidationIssue(
            severity="error",
            rule="test_rule",
            message="Test message",
            suggestion="Test suggestion"
        )

        assert issue.severity == "error"
        assert issue.rule == "test_rule"
        assert issue.message == "Test message"
        assert issue.suggestion == "Test suggestion"

    def test_issue_to_dict(self):
        """Test converting issue to dictionary."""
        issue = ValidationIssue(
            severity="warning",
            rule="test_rule",
            message="Test message"
        )

        issue_dict = issue.to_dict()

        assert issue_dict["severity"] == "warning"
        assert issue_dict["rule"] == "test_rule"
        assert issue_dict["message"] == "Test message"


class TestHookConfig:
    """Tests for HookConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = HookConfig()

        assert config.mode == "advisory"
        assert config.audit_log is None

    def test_custom_config(self):
        """Test custom configuration."""
        config = HookConfig(
            mode="blocking",
            audit_log=".vibey/audit.log"
        )

        assert config.mode == "blocking"
        assert config.audit_log == ".vibey/audit.log"
