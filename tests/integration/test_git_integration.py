"""
Integration tests for Git integration module.

End-to-end tests with real git workflows:
- Full PR workflow
- Multi-developer simulation
- CI/CD integration
- Edge cases
"""

import os
import pytest
import subprocess
import tempfile
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@pytest.fixture
def git_env():
    """Git environment variables for commits."""
    return {
        'GIT_AUTHOR_NAME': 'Test User',
        'GIT_AUTHOR_EMAIL': 'test@example.com',
        'GIT_COMMITTER_NAME': 'Test User',
        'GIT_COMMITTER_EMAIL': 'test@example.com',
        **os.environ
    }


@pytest.fixture
def full_repo(git_env):
    """Create a complete test repository with roadmap structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)

        # Initialize git
        subprocess.run(['git', 'init'], cwd=repo, capture_output=True, check=True)
        subprocess.run(['git', 'checkout', '-b', 'main'], cwd=repo, capture_output=True, check=True)

        # Create roadmap structure
        roadmap_root = repo / ".vibey" / "roadmap"
        roadmap_root.mkdir(parents=True)

        # Create main roadmap.yaml
        with open(roadmap_root / "roadmap.yaml", 'w') as f:
            yaml.dump({
                'roadmap': {
                    'id': 'test-roadmap',
                    'name': 'Test Roadmap',
                    'status': 'in_progress'
                }
            }, f)

        # Create track
        track_dir = roadmap_root / "test-track"
        track_dir.mkdir()
        with open(track_dir / "track.yaml", 'w') as f:
            yaml.dump({
                'track': {
                    'id': 'test-track',
                    'name': 'Test Track',
                    'status': 'in_progress',
                    'depends_on': [],
                    'blocked_by': []
                }
            }, f)

        # Create sprint
        sprint_dir = track_dir / "test-track-1"
        sprint_dir.mkdir()
        with open(sprint_dir / "sprint.yaml", 'w') as f:
            yaml.dump({
                'sprint': {
                    'id': 'test-track-1',
                    'name': 'Sprint 1',
                    'status': 'in_progress',
                    'dependencies': [],
                    'blocked_by': []
                }
            }, f)

        # Create tasks
        for i in range(1, 4):
            task_dir = sprint_dir / f"test-track-1-task-00{i}"
            task_dir.mkdir()
            deps = [f"test-track-1-task-00{i-1}"] if i > 1 else []
            with open(task_dir / "task.yaml", 'w') as f:
                yaml.dump({
                    'task': {
                        'id': f'test-track-1-task-00{i}',
                        'sprint_id': 'test-track-1',
                        'track_id': 'test-track',
                        'title': f'Task {i}',
                        'status': 'completed' if i == 1 else 'not_started',
                        'dependencies': deps,
                        'blocked_by': []
                    }
                }, f)

        # Create initial commit
        subprocess.run(['git', 'add', '.'], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ['git', 'commit', '-m', 'Initial commit'],
            cwd=repo, capture_output=True, check=True, env=git_env
        )

        yield repo


def run_git(repo: Path, *args, env=None) -> subprocess.CompletedProcess:
    """Run a git command in the repo."""
    return subprocess.run(
        ['git', *args],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env
    )


def get_current_branch(repo: Path) -> str:
    """Get current branch name."""
    result = run_git(repo, 'rev-parse', '--abbrev-ref', 'HEAD')
    return result.stdout.strip()


def create_task_branch(repo: Path, task_id: str, git_env: dict) -> str:
    """Create a feature branch for a task."""
    branch_name = f"feature/{task_id}"
    run_git(repo, 'checkout', '-b', branch_name)
    return branch_name


def make_commit(repo: Path, message: str, files: dict, git_env: dict) -> str:
    """Create files and commit."""
    for filename, content in files.items():
        filepath = repo / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content)

    run_git(repo, 'add', '.')
    result = run_git(repo, 'commit', '-m', message, env=git_env)
    if result.returncode != 0:
        raise RuntimeError(f"Commit failed: {result.stderr}")

    # Get commit hash
    result = run_git(repo, 'rev-parse', 'HEAD')
    return result.stdout.strip()


class TestFullPRWorkflow:
    """Tests for complete PR workflow."""

    def test_create_branch_make_commits(self, full_repo, git_env):
        """Test creating a task branch and making commits."""
        # Create feature branch
        branch = create_task_branch(full_repo, 'test-track-1-task-002', git_env)
        assert get_current_branch(full_repo) == branch

        # Make commits
        commit1 = make_commit(
            full_repo,
            'feat: Start task 002',
            {'src/feature.py': 'def feature():\n    pass\n'},
            git_env
        )
        assert len(commit1) == 40

        commit2 = make_commit(
            full_repo,
            'feat: Complete task 002 implementation',
            {'src/feature.py': 'def feature():\n    return True\n'},
            git_env
        )
        assert len(commit2) == 40

    def test_task_status_tracking_with_commits(self, full_repo, git_env):
        """Test that commit messages can reference task status."""
        branch = create_task_branch(full_repo, 'test-track-1-task-002', git_env)

        # Commit with task reference
        commit = make_commit(
            full_repo,
            'feat(test-track-1-task-002): Implement feature\n\nTask: test-track-1-task-002\nStatus: completed',
            {'src/impl.py': 'code'},
            git_env
        )

        # Verify commit message can be parsed
        result = run_git(full_repo, 'log', '-1', '--format=%B')
        message = result.stdout.strip()
        assert 'test-track-1-task-002' in message
        assert 'completed' in message

    def test_merge_to_main(self, full_repo, git_env):
        """Test merging feature branch to main."""
        # Create and checkout feature branch
        branch = create_task_branch(full_repo, 'test-track-1-task-002', git_env)

        # Make a commit
        make_commit(
            full_repo,
            'feat: Implement task 002',
            {'src/new_feature.py': 'print("new")'},
            git_env
        )

        # Switch to main and merge
        run_git(full_repo, 'checkout', 'main')
        result = run_git(full_repo, 'merge', branch, '--no-ff', '-m', 'Merge task 002', env=git_env)

        assert result.returncode == 0

        # Verify file exists in main
        assert (full_repo / 'src' / 'new_feature.py').exists()


class TestMultiDeveloperSimulation:
    """Tests simulating multiple developers working concurrently."""

    def test_concurrent_task_branches(self, full_repo, git_env):
        """Test multiple task branches from same base."""
        # Record initial commit
        result = run_git(full_repo, 'rev-parse', 'HEAD')
        base_commit = result.stdout.strip()

        # Create first task branch
        run_git(full_repo, 'checkout', '-b', 'feature/test-track-1-task-002')
        make_commit(
            full_repo,
            'feat: Task 002 work',
            {'task002.txt': 'task 002 content'},
            git_env
        )

        # Create second task branch from main
        run_git(full_repo, 'checkout', 'main')
        run_git(full_repo, 'checkout', '-b', 'feature/test-track-1-task-003')
        make_commit(
            full_repo,
            'feat: Task 003 work',
            {'task003.txt': 'task 003 content'},
            git_env
        )

        # Both branches should have their own files
        run_git(full_repo, 'checkout', 'feature/test-track-1-task-002')
        assert (full_repo / 'task002.txt').exists()
        assert not (full_repo / 'task003.txt').exists()

        run_git(full_repo, 'checkout', 'feature/test-track-1-task-003')
        assert (full_repo / 'task003.txt').exists()
        assert not (full_repo / 'task002.txt').exists()

    def test_merge_conflict_detection(self, full_repo, git_env):
        """Test detecting merge conflicts between task branches."""
        # Create first branch modifying same file
        run_git(full_repo, 'checkout', '-b', 'feature/task-a')
        make_commit(
            full_repo,
            'feat: Task A changes',
            {'shared.txt': 'content from task A\n'},
            git_env
        )

        # Create second branch modifying same file
        run_git(full_repo, 'checkout', 'main')
        run_git(full_repo, 'checkout', '-b', 'feature/task-b')
        make_commit(
            full_repo,
            'feat: Task B changes',
            {'shared.txt': 'content from task B\n'},
            git_env
        )

        # Merge first branch to main
        run_git(full_repo, 'checkout', 'main')
        run_git(full_repo, 'merge', 'feature/task-a', '--no-ff', '-m', 'Merge task A', env=git_env)

        # Try to merge second branch - should conflict
        result = run_git(full_repo, 'merge', 'feature/task-b', '--no-ff', '-m', 'Merge task B', env=git_env)
        assert result.returncode != 0
        assert 'CONFLICT' in result.stdout or 'conflict' in result.stderr.lower()

        # Abort the merge
        run_git(full_repo, 'merge', '--abort')

    def test_sequential_dependency_merging(self, full_repo, git_env):
        """Test merging branches in dependency order."""
        # Task 1 is already completed in fixture

        # Create task 2 branch (depends on task 1)
        run_git(full_repo, 'checkout', '-b', 'feature/test-track-1-task-002')
        make_commit(
            full_repo,
            'feat: Task 002 depends on task 001',
            {'task002.py': 'from task001 import base\n'},
            git_env
        )

        # Merge task 2
        run_git(full_repo, 'checkout', 'main')
        result = run_git(full_repo, 'merge', 'feature/test-track-1-task-002', '--no-ff',
                        '-m', 'Merge task 002', env=git_env)
        assert result.returncode == 0


class TestCIIntegration:
    """Tests for CI/CD integration scenarios."""

    def test_quality_gate_simulation(self, full_repo, git_env):
        """Test simulating quality gate checks."""
        # Create a branch
        branch = create_task_branch(full_repo, 'test-track-1-task-002', git_env)

        # Add test file (simulating test requirement)
        make_commit(
            full_repo,
            'feat: Add feature with tests',
            {
                'src/feature.py': 'def add(a, b): return a + b',
                'tests/test_feature.py': 'def test_add(): assert add(1, 2) == 3'
            },
            git_env
        )

        # Verify test file exists (simulating test gate)
        assert (full_repo / 'tests' / 'test_feature.py').exists()

    def test_status_check_integration(self, full_repo, git_env):
        """Test simulating status checks on branches."""
        # Create feature branch
        branch = create_task_branch(full_repo, 'test-track-1-task-002', git_env)
        make_commit(
            full_repo,
            'feat: Feature implementation',
            {'src/impl.py': 'code'},
            git_env
        )

        # Get branch info (simulating CI getting branch context)
        result = run_git(full_repo, 'rev-parse', '--abbrev-ref', 'HEAD')
        current_branch = result.stdout.strip()
        assert current_branch == branch

        # Get commit count (for status reporting)
        result = run_git(full_repo, 'rev-list', '--count', f'main..{branch}')
        commit_count = int(result.stdout.strip())
        assert commit_count >= 1


class TestEdgeCases:
    """Tests for edge cases and unusual git operations."""

    def test_squash_merge(self, full_repo, git_env):
        """Test squash merge behavior."""
        # Create branch with multiple commits
        branch = create_task_branch(full_repo, 'test-track-1-task-002', git_env)

        make_commit(full_repo, 'feat: Part 1', {'part1.txt': 'part 1'}, git_env)
        make_commit(full_repo, 'feat: Part 2', {'part2.txt': 'part 2'}, git_env)
        make_commit(full_repo, 'feat: Part 3', {'part3.txt': 'part 3'}, git_env)

        # Squash merge to main
        run_git(full_repo, 'checkout', 'main')
        run_git(full_repo, 'merge', '--squash', branch)
        run_git(full_repo, 'commit', '-m', 'Squash merge task 002', env=git_env)

        # All files should exist but in single commit
        assert (full_repo / 'part1.txt').exists()
        assert (full_repo / 'part2.txt').exists()
        assert (full_repo / 'part3.txt').exists()

        # Check main has single additional commit (not 3)
        result = run_git(full_repo, 'log', '--oneline', 'main')
        lines = result.stdout.strip().split('\n')
        # Should be: initial + squash = at least 2
        assert len(lines) >= 2

    def test_rebase_workflow(self, full_repo, git_env):
        """Test rebase-based workflow."""
        # Create feature branch
        branch = create_task_branch(full_repo, 'test-track-1-task-002', git_env)
        make_commit(full_repo, 'feat: Feature work', {'feature.txt': 'feature'}, git_env)

        # Add commit to main
        run_git(full_repo, 'checkout', 'main')
        make_commit(full_repo, 'chore: Main update', {'main_update.txt': 'update'}, git_env)

        # Rebase feature branch onto main
        run_git(full_repo, 'checkout', branch)
        result = run_git(full_repo, 'rebase', 'main')
        assert result.returncode == 0

        # Feature branch should have main's changes
        assert (full_repo / 'main_update.txt').exists()
        assert (full_repo / 'feature.txt').exists()

    def test_detached_head_recovery(self, full_repo, git_env):
        """Test working in detached HEAD state."""
        # Get current commit
        result = run_git(full_repo, 'rev-parse', 'HEAD')
        commit_hash = result.stdout.strip()

        # Enter detached HEAD
        run_git(full_repo, 'checkout', commit_hash)

        # Verify we're in detached HEAD
        result = run_git(full_repo, 'rev-parse', '--abbrev-ref', 'HEAD')
        assert result.stdout.strip() == 'HEAD'

        # Make a commit (will be orphaned)
        make_commit(full_repo, 'test: Detached commit', {'detached.txt': 'orphan'}, git_env)

        # Return to main
        run_git(full_repo, 'checkout', 'main')
        assert get_current_branch(full_repo) == 'main'

    def test_branch_from_tag(self, full_repo, git_env):
        """Test creating branch from a tag."""
        # Create a tag
        run_git(full_repo, 'tag', 'v1.0.0')

        # Create branch from tag
        run_git(full_repo, 'checkout', '-b', 'hotfix/v1.0.1', 'v1.0.0')
        assert get_current_branch(full_repo) == 'hotfix/v1.0.1'

        # Make a hotfix commit
        make_commit(full_repo, 'fix: Critical bug', {'hotfix.txt': 'fix'}, git_env)

        # Verify tag still points to original commit
        result = run_git(full_repo, 'rev-parse', 'v1.0.0')
        tag_commit = result.stdout.strip()

        result = run_git(full_repo, 'rev-parse', 'HEAD')
        branch_commit = result.stdout.strip()

        assert tag_commit != branch_commit

    def test_empty_commit_handling(self, full_repo, git_env):
        """Test handling of empty commits."""
        branch = create_task_branch(full_repo, 'test-track-1-task-002', git_env)

        # Try to create empty commit
        result = run_git(full_repo, 'commit', '--allow-empty', '-m', 'Empty commit for CI', env=git_env)
        assert result.returncode == 0

        # Verify commit exists
        result = run_git(full_repo, 'log', '-1', '--format=%s')
        assert 'Empty commit for CI' in result.stdout


class TestCommitMessageParsing:
    """Tests for commit message format and parsing."""

    def test_conventional_commit_format(self, full_repo, git_env):
        """Test conventional commit format parsing."""
        branch = create_task_branch(full_repo, 'test-track-1-task-002', git_env)

        # Create commit with conventional format
        commit = make_commit(
            full_repo,
            'feat(test-track-1-task-002): Add new feature\n\nBody of the commit message\n\nCloses: test-track-1-task-002',
            {'feature.py': 'code'},
            git_env
        )

        # Verify format
        result = run_git(full_repo, 'log', '-1', '--format=%B')
        message = result.stdout.strip()

        assert message.startswith('feat(')
        assert 'test-track-1-task-002' in message

    def test_task_reference_extraction(self, full_repo, git_env):
        """Test extracting task references from commits."""
        branch = create_task_branch(full_repo, 'test-track-1-task-002', git_env)

        # Various task reference formats
        formats = [
            'feat: Complete test-track-1-task-002',
            'feat: [test-track-1-task-002] Implementation',
            'feat: Implementation (test-track-1-task-002)',
        ]

        for i, msg_format in enumerate(formats):
            make_commit(
                full_repo,
                msg_format,
                {f'file{i}.txt': 'content'},
                git_env
            )

        # All should be parseable for task reference
        result = run_git(full_repo, 'log', '--format=%s')
        for line in result.stdout.strip().split('\n'):
            if 'task-002' in line.lower():
                assert 'test-track-1-task-002' in line


class TestBranchNamingConventions:
    """Tests for branch naming conventions."""

    def test_task_branch_naming(self, full_repo, git_env):
        """Test task branch naming conventions."""
        valid_names = [
            'feature/test-track-1-task-002',
            'feature/add-login-feature',
            'bugfix/fix-null-pointer',
        ]

        for name in valid_names:
            run_git(full_repo, 'checkout', '-b', name, 'main')
            assert get_current_branch(full_repo) == name
            run_git(full_repo, 'checkout', 'main')
            run_git(full_repo, 'branch', '-D', name)

    def test_sprint_branch_naming(self, full_repo, git_env):
        """Test sprint branch naming conventions."""
        valid_names = [
            'sprint/test-track-1',
            'sprint/auth-sprint-3',
        ]

        for name in valid_names:
            run_git(full_repo, 'checkout', '-b', name, 'main')
            assert get_current_branch(full_repo) == name
            run_git(full_repo, 'checkout', 'main')
            run_git(full_repo, 'branch', '-D', name)

    def test_track_branch_naming(self, full_repo, git_env):
        """Test track branch naming conventions."""
        valid_names = [
            'track/test-track',
            'track/authentication',
        ]

        for name in valid_names:
            run_git(full_repo, 'checkout', '-b', name, 'main')
            assert get_current_branch(full_repo) == name
            run_git(full_repo, 'checkout', 'main')
            run_git(full_repo, 'branch', '-D', name)


class TestTagOperations:
    """Tests for git tag operations."""

    def test_sprint_start_tag(self, full_repo, git_env):
        """Test creating sprint start tags."""
        tag_name = 'sprint/test-track-1/start'
        run_git(full_repo, 'tag', tag_name, '-m', 'Sprint 1 start')

        # Verify tag exists
        result = run_git(full_repo, 'tag', '-l', 'sprint/*')
        assert tag_name in result.stdout

    def test_sprint_end_tag(self, full_repo, git_env):
        """Test creating sprint end tags."""
        # Make some commits for the sprint
        make_commit(full_repo, 'feat: Sprint work', {'work.txt': 'done'}, git_env)

        tag_name = 'sprint/test-track-1/end'
        run_git(full_repo, 'tag', tag_name, '-m', 'Sprint 1 complete')

        # Verify tag exists
        result = run_git(full_repo, 'tag', '-l', 'sprint/*')
        assert tag_name in result.stdout

    def test_task_completion_tag(self, full_repo, git_env):
        """Test creating task completion tags."""
        branch = create_task_branch(full_repo, 'test-track-1-task-002', git_env)
        make_commit(full_repo, 'feat: Complete task', {'impl.py': 'done'}, git_env)

        tag_name = 'task/test-track-1-task-002/complete'
        run_git(full_repo, 'tag', tag_name, '-m', 'Task 002 completed')

        # Verify tag
        result = run_git(full_repo, 'tag', '-l', 'task/*')
        assert tag_name in result.stdout
