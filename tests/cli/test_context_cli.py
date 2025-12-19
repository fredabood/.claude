"""
Tests for context-related CLI commands.

Tests the git commit template commands and artifact linking commands
that support the context system v2.

Task: 01KCMGX4QAG1SNWA7J7AVGH3NP
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path

import pytest


def run_cli(*args, cwd=None):
    """Run the vibey CLI and return the result."""
    cmd = [sys.executable, "-m", "vibey"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result


class TestGitTemplateCommands:
    """Test git commit template commands."""

    def test_setup_template_help(self):
        """Test git setup-template --help."""
        result = run_cli("git", "setup-template", "--help")
        assert result.returncode == 0
        assert "Install git commit message template" in result.stdout
        assert "--force" in result.stdout
        assert "--repo" in result.stdout

    def test_refresh_template_help(self):
        """Test git refresh-template --help."""
        result = run_cli("git", "refresh-template", "--help")
        assert result.returncode == 0
        assert "Refresh the commit message template" in result.stdout
        assert "--repo" in result.stdout

    def test_setup_template_creates_file(self):
        """Test that setup-template creates the template file."""
        # Use the actual repo since it has .vibey/ directory
        result = run_cli("git", "setup-template", "--force")
        assert result.returncode == 0
        assert "Commit Template Installed" in result.stdout
        assert "commit-template" in result.stdout

    def test_refresh_template_works(self):
        """Test that refresh-template updates the template."""
        result = run_cli("git", "refresh-template")
        assert result.returncode == 0
        assert "Template refreshed" in result.stdout

    def test_template_file_has_task_markers(self):
        """Test that the template file contains Task: and Completes: markers."""
        # Setup template first
        run_cli("git", "setup-template", "--force")

        template_path = Path(".vibey/git/commit-template")
        assert template_path.exists(), "Template file should exist"

        content = template_path.read_text()
        assert "Task:" in content, "Template should contain Task: marker"
        assert "Completes:" in content, "Template should contain Completes: marker"


class TestArtifactCommands:
    """Test artifact CLI commands."""

    def test_artifact_help(self):
        """Test artifact --help."""
        result = run_cli("artifact", "--help")
        assert result.returncode == 0
        assert "Manage artifacts" in result.stdout
        assert "adopt" in result.stdout
        assert "list" in result.stdout
        assert "link" in result.stdout
        assert "unlink" in result.stdout
        assert "for-task" in result.stdout

    def test_artifact_link_help(self):
        """Test artifact link --help."""
        result = run_cli("artifact", "link", "--help")
        assert result.returncode == 0
        assert "Link an artifact to a task" in result.stdout
        assert "--task" in result.stdout

    def test_artifact_unlink_help(self):
        """Test artifact unlink --help."""
        result = run_cli("artifact", "unlink", "--help")
        assert result.returncode == 0
        assert "Unlink an artifact from a task" in result.stdout
        assert "--task" in result.stdout

    def test_artifact_for_task_help(self):
        """Test artifact for-task --help."""
        result = run_cli("artifact", "for-task", "--help")
        assert result.returncode == 0
        assert "List artifacts linked to a specific task" in result.stdout
        assert "--format" in result.stdout

    def test_artifact_list(self):
        """Test artifact list command runs."""
        result = run_cli("artifact", "list")
        # Should succeed (may show empty list)
        assert result.returncode == 0

    def test_artifact_for_task_nonexistent(self):
        """Test artifact for-task with non-existent task."""
        result = run_cli("artifact", "for-task", "nonexistent-task-id")
        assert result.returncode == 0
        # Should show empty or "no artifacts" message
        assert "No artifacts" in result.stdout or "[]" in result.stdout

    def test_artifact_link_requires_task(self):
        """Test that artifact link requires --task option."""
        result = run_cli("artifact", "link", "some-artifact-id")
        assert result.returncode != 0
        assert "Error" in result.stderr or "Missing option" in result.stderr

    def test_artifact_unlink_requires_task(self):
        """Test that artifact unlink requires --task option."""
        result = run_cli("artifact", "unlink", "some-artifact-id")
        assert result.returncode != 0
        assert "Error" in result.stderr or "Missing option" in result.stderr


class TestGitTasksCommand:
    """Test git tasks command (shows commits for a task)."""

    def test_git_tasks_help(self):
        """Test git tasks --help."""
        result = run_cli("git", "tasks", "--help")
        assert result.returncode == 0
        assert "Show commits for a specific task" in result.stdout
        assert "--format" in result.stdout

    def test_git_tasks_requires_id(self):
        """Test that git tasks requires a task ID."""
        result = run_cli("git", "tasks")
        assert result.returncode != 0


class TestGitLinkCommitCommand:
    """Test git link-commit command."""

    def test_git_link_commit_help(self):
        """Test git link-commit --help."""
        result = run_cli("git", "link-commit", "--help")
        assert result.returncode == 0
        assert "Link a commit to a task" in result.stdout
        assert "--status" in result.stdout
        assert "--dry-run" in result.stdout

    def test_git_link_commit_requires_args(self):
        """Test that git link-commit requires task ID and commit SHA."""
        result = run_cli("git", "link-commit")
        assert result.returncode != 0


class TestRoadmapAddCommit:
    """Test roadmap add-commit command."""

    def test_add_commit_help(self):
        """Test roadmap add-commit --help."""
        result = run_cli("roadmap", "add-commit", "--help")
        assert result.returncode == 0
        assert "Add a git commit to a task" in result.stdout
        assert "--auto" in result.stdout

    def test_add_commit_requires_task_id(self):
        """Test that roadmap add-commit requires a task ID."""
        result = run_cli("roadmap", "add-commit")
        assert result.returncode != 0


class TestRoadmapAddContext:
    """Test roadmap add-context command."""

    def test_add_context_help(self):
        """Test roadmap add-context --help."""
        result = run_cli("roadmap", "add-context", "--help")
        assert result.returncode == 0
        assert "Add a context file to a roadmap object" in result.stdout
        assert "--track" in result.stdout
        assert "--sprint" in result.stdout
        assert "--task" in result.stdout

    def test_add_context_requires_file_path(self):
        """Test that roadmap add-context requires a file path."""
        result = run_cli("roadmap", "add-context")
        assert result.returncode != 0
