"""
Unit tests for bypass detection in post-commit hook.

Tests:
- Bypass detection logic
- Audit logging
- Reporting
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import json

from vibey.operations.git.hooks.post_commit import (
    BypassDetector,
    detect_and_log_bypass,
    main,
)


class TestBypassDetector:
    """Tests for BypassDetector class."""

    @pytest.fixture
    def repo_path(self, tmp_path):
        """Create temporary repository structure."""
        vibey_dir = tmp_path / ".vibey"
        vibey_dir.mkdir()
        (vibey_dir / "roadmap" / "activity_log").mkdir(parents=True)
        (vibey_dir / "audit").mkdir()
        return tmp_path

    @pytest.fixture
    def detector(self, repo_path):
        """Create BypassDetector for test repo."""
        return BypassDetector(repo_path)

    def test_audit_log_path(self, detector, repo_path):
        """Test audit log path is correct."""
        expected = repo_path / ".vibey" / "audit" / "bypass.log"
        assert detector.audit_log_path == expected

    def test_detect_bypass_no_head(self, detector):
        """Test detect_bypass when HEAD doesn't exist."""
        with patch.object(detector, '_get_head_commit_hash', return_value=None):
            events = detector.detect_bypass()
            assert events == []

    def test_detect_bypass_no_roadmap_files(self, detector):
        """Test detect_bypass when no roadmap files in commit."""
        with patch.object(detector, '_get_head_commit_hash', return_value="abc123"):
            with patch.object(detector, '_get_roadmap_files_in_commit', return_value=[]):
                events = detector.detect_bypass()
                assert events == []

    def test_detect_bypass_file_deleted(self, detector):
        """Test detect_bypass when file was deleted (allowed)."""
        with patch.object(detector, '_get_head_commit_hash', return_value="abc123"):
            with patch.object(detector, '_get_roadmap_files_in_commit',
                            return_value=[".vibey/roadmap/tasks/test.yaml"]):
                with patch.object(detector, '_get_file_hash_at_commit', return_value=None):
                    events = detector.detect_bypass()
                    assert events == []

    def test_detect_bypass_file_in_activity_log(self, detector):
        """Test detect_bypass when file is in activity log (no bypass)."""
        with patch.object(detector, '_get_head_commit_hash', return_value="abc123"):
            with patch.object(detector, '_get_roadmap_files_in_commit',
                            return_value=[".vibey/roadmap/tasks/test.yaml"]):
                with patch.object(detector, '_get_file_hash_at_commit', return_value="filehash"):
                    with patch.object(detector, '_check_activity_log_for_hash', return_value=True):
                        events = detector.detect_bypass()
                        assert events == []

    def test_detect_bypass_file_not_in_activity_log(self, detector):
        """Test detect_bypass when file is NOT in activity log (bypass detected)."""
        with patch.object(detector, '_get_head_commit_hash', return_value="abc123"):
            with patch.object(detector, '_get_roadmap_files_in_commit',
                            return_value=[".vibey/roadmap/tasks/test.yaml"]):
                with patch.object(detector, '_get_file_hash_at_commit', return_value="filehash"):
                    with patch.object(detector, '_check_activity_log_for_hash', return_value=False):
                        events = detector.detect_bypass()
                        assert len(events) == 1
                        assert events[0]["type"] == "pre_commit_bypass"
                        assert events[0]["file_path"] == ".vibey/roadmap/tasks/test.yaml"

    def test_log_bypass_events_creates_file(self, detector, repo_path):
        """Test that log_bypass_events creates audit log file."""
        events = [
            {
                "type": "pre_commit_bypass",
                "timestamp": "2025-01-01T00:00:00Z",
                "commit_hash": "abc123",
                "file_path": "test.yaml",
                "file_hash": "hashvalue",
            }
        ]

        detector.log_bypass_events(events)

        assert detector.audit_log_path.exists()
        content = detector.audit_log_path.read_text()
        assert "pre_commit_bypass" in content

    def test_log_bypass_events_appends(self, detector, repo_path):
        """Test that log_bypass_events appends to existing file."""
        events1 = [{"type": "bypass", "id": "1"}]
        events2 = [{"type": "bypass", "id": "2"}]

        detector.log_bypass_events(events1)
        detector.log_bypass_events(events2)

        lines = detector.audit_log_path.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_log_bypass_events_empty(self, detector, repo_path):
        """Test that empty events list doesn't create file."""
        detector.log_bypass_events([])
        assert not detector.audit_log_path.exists()

    def test_report_bypass_empty(self, detector, capsys):
        """Test that empty events produces no output."""
        detector.report_bypass([])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_report_bypass_shows_files(self, detector, capsys):
        """Test that bypass report shows affected files."""
        events = [
            {"file_path": "file1.yaml"},
            {"file_path": "file2.yaml"},
        ]
        detector.report_bypass(events)

        captured = capsys.readouterr()
        assert "file1.yaml" in captured.out
        assert "file2.yaml" in captured.out
        assert "bypass detected" in captured.out.lower()


class TestDetectAndLogBypass:
    """Tests for detect_and_log_bypass function."""

    def test_returns_zero_when_no_bypass(self, tmp_path):
        """Test returns 0 when no bypass detected."""
        vibey_dir = tmp_path / ".vibey"
        vibey_dir.mkdir()
        (vibey_dir / "roadmap" / "activity_log").mkdir(parents=True)

        with patch("vibey.operations.git.hooks.post_commit.BypassDetector") as mock:
            mock.return_value.detect_bypass.return_value = []
            count = detect_and_log_bypass(tmp_path)
            assert count == 0

    def test_returns_count_when_bypass(self, tmp_path):
        """Test returns count when bypass detected."""
        vibey_dir = tmp_path / ".vibey"
        vibey_dir.mkdir()
        (vibey_dir / "roadmap" / "activity_log").mkdir(parents=True)

        with patch("vibey.operations.git.hooks.post_commit.BypassDetector") as mock:
            mock.return_value.detect_bypass.return_value = [{"id": 1}, {"id": 2}]
            count = detect_and_log_bypass(tmp_path)
            assert count == 2


class TestMain:
    """Tests for main function."""

    def test_returns_zero_not_vibey_project(self, tmp_path):
        """Test returns 0 when not a vibey project."""
        with patch("vibey.operations.git.hooks.post_commit.Path") as mock:
            mock.cwd.return_value = tmp_path
            result = main()
            assert result == 0

    def test_handles_exceptions_gracefully(self, tmp_path):
        """Test that exceptions don't cause failure."""
        with patch("vibey.operations.git.hooks.post_commit.Path") as mock:
            mock.cwd.return_value = tmp_path
            (tmp_path / ".vibey").mkdir()

            with patch("vibey.operations.git.hooks.post_commit.detect_and_log_bypass") as detect:
                detect.side_effect = Exception("Test error")
                result = main()
                assert result == 0  # Still succeeds
