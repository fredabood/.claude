"""
Unit tests for roadmap verification.

Tests:
- Single file verification
- Batch verification
- Signature verification
- Commit range verification
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

from vibey.operations.roadmap.verification import (
    VerificationResult,
    ChangeVerifier,
    CommitVerificationResult,
    CommitRangeVerifier,
    verify_change,
    verify_commits,
)


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""

    def test_verified_result(self):
        """Test verified file result."""
        result = VerificationResult(
            file_path=Path("test.yaml"),
            verified=True,
            current_hash="abc123",
        )
        assert result.verified
        assert result.error is None

    def test_unverified_result(self):
        """Test unverified file result."""
        result = VerificationResult(
            file_path=Path("test.yaml"),
            verified=False,
            current_hash="abc123",
        )
        assert not result.verified

    def test_to_dict_basic(self):
        """Test basic to_dict conversion."""
        result = VerificationResult(
            file_path=Path("test.yaml"),
            verified=True,
            current_hash="abc123",
        )
        data = result.to_dict()
        assert data["file_path"] == "test.yaml"
        assert data["verified"] is True
        assert data["current_hash"] == "abc123"

    def test_to_dict_with_signature(self):
        """Test to_dict with signature fields."""
        result = VerificationResult(
            file_path=Path("test.yaml"),
            verified=True,
            current_hash="abc123",
            signed=True,
            signer="test@example.com",
            signature_valid=True,
        )
        data = result.to_dict()
        assert data["signed"] is True
        assert data["signer"] == "test@example.com"
        assert data["signature_valid"] is True


class TestChangeVerifier:
    """Tests for ChangeVerifier class."""

    @pytest.fixture
    def project_root(self, tmp_path):
        """Create temporary project with roadmap structure."""
        vibey_dir = tmp_path / ".vibey" / "roadmap"
        vibey_dir.mkdir(parents=True)
        (vibey_dir / "activity_log").mkdir()

        # Create a test task file
        tasks_dir = vibey_dir / "tasks"
        tasks_dir.mkdir()
        task_file = tasks_dir / "test-task.yaml"
        task_file.write_text("task:\n  id: test-task\n  status: pending\n")

        return tmp_path

    @pytest.fixture
    def verifier(self, project_root):
        """Create ChangeVerifier for test project."""
        return ChangeVerifier(project_root)

    def test_verify_nonexistent_file(self, verifier, project_root):
        """Test verification of nonexistent file."""
        result = verifier.verify_file(Path("nonexistent.yaml"))
        assert not result.verified
        assert "not found" in result.error.lower()

    def test_verify_existing_file_no_activity_log(self, verifier, project_root):
        """Test verification when no activity log entry exists."""
        task_file = project_root / ".vibey" / "roadmap" / "tasks" / "test-task.yaml"
        result = verifier.verify_file(task_file)
        assert not result.verified
        assert result.error is None  # File exists, just not in log

    def test_verify_files_batch(self, verifier, project_root):
        """Test batch verification."""
        task_file = project_root / ".vibey" / "roadmap" / "tasks" / "test-task.yaml"
        results = verifier.verify_files([task_file])
        assert len(results) == 1
        assert results[0].file_path == task_file


class TestCommitVerificationResult:
    """Tests for CommitVerificationResult dataclass."""

    def test_verified_commit(self):
        """Test verified commit result."""
        result = CommitVerificationResult(
            commit_hash="abc123",
            verified=True,
            roadmap_files=["test.yaml"],
            unverified_files=[],
        )
        assert result.verified

    def test_unverified_commit(self):
        """Test unverified commit result."""
        result = CommitVerificationResult(
            commit_hash="abc123",
            verified=False,
            roadmap_files=["test.yaml"],
            unverified_files=["test.yaml"],
        )
        assert not result.verified

    def test_to_dict(self):
        """Test to_dict conversion."""
        result = CommitVerificationResult(
            commit_hash="abc123",
            verified=True,
            roadmap_files=["test.yaml"],
            unverified_files=[],
        )
        data = result.to_dict()
        assert data["commit_hash"] == "abc123"
        assert data["verified"] is True


class TestCommitRangeVerifier:
    """Tests for CommitRangeVerifier class."""

    @pytest.fixture
    def project_root(self, tmp_path):
        """Create temporary project."""
        vibey_dir = tmp_path / ".vibey" / "roadmap"
        vibey_dir.mkdir(parents=True)
        (vibey_dir / "activity_log").mkdir()
        return tmp_path

    @pytest.fixture
    def verifier(self, project_root):
        """Create CommitRangeVerifier for test project."""
        return CommitRangeVerifier(project_root)

    def test_get_commits_in_range_invalid(self, verifier):
        """Test getting commits from invalid range."""
        # Should return empty list for invalid range
        commits = verifier._get_commits_in_range("invalid..range")
        assert commits == []

    def test_verify_commit_no_roadmap_files(self, verifier):
        """Test verifying commit with no roadmap files."""
        with patch.object(verifier, '_get_roadmap_files_in_commit', return_value=[]):
            result = verifier.verify_commit("abc123")
            assert result.verified
            assert result.roadmap_files == []


class TestVerifyChange:
    """Tests for verify_change CLI function."""

    @pytest.fixture
    def project_root(self, tmp_path):
        """Create temporary project."""
        vibey_dir = tmp_path / ".vibey" / "roadmap"
        vibey_dir.mkdir(parents=True)
        (vibey_dir / "activity_log").mkdir()
        return tmp_path

    def test_verify_change_nonexistent_file(self, project_root, capsys):
        """Test verify_change with nonexistent file."""
        exit_code = verify_change(project_root, Path("nonexistent.yaml"))
        assert exit_code == 2  # Error

        captured = capsys.readouterr()
        assert "Error" in captured.out or "not found" in captured.out.lower()


class TestVerifyCommits:
    """Tests for verify_commits CLI function."""

    @pytest.fixture
    def project_root(self, tmp_path):
        """Create temporary project."""
        vibey_dir = tmp_path / ".vibey" / "roadmap"
        vibey_dir.mkdir(parents=True)
        (vibey_dir / "activity_log").mkdir()
        return tmp_path

    def test_verify_commits_empty_range(self, project_root, capsys):
        """Test verify_commits with no commits in range."""
        with patch("vibey.operations.roadmap.verification.CommitRangeVerifier") as mock:
            mock.return_value.verify_range.return_value = []
            exit_code = verify_commits(project_root, "main..HEAD")
            assert exit_code == 0

    def test_verify_commits_json_output(self, project_root, capsys):
        """Test verify_commits JSON output."""
        with patch("vibey.operations.roadmap.verification.CommitRangeVerifier") as mock:
            mock.return_value.verify_range.return_value = []
            exit_code = verify_commits(project_root, "main..HEAD", json_output=True)
            assert exit_code == 0

            captured = capsys.readouterr()
            assert "all_verified" in captured.out
