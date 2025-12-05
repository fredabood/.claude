"""
Tests for GitCommit serialization with completion tracking.

Tests the parsing of completes_tickets from:
- YAML data fields
- Commit message patterns
- Platform migration for legacy commits
"""

import pytest
from datetime import datetime, timezone


class TestParseCompletesFromMessage:
    """Tests for _parse_completes_from_message function."""

    def test_completes_colon_single(self):
        """Test 'Completes: task-id' pattern."""
        from vibey.roadmap.serialization.yaml_loader import _parse_completes_from_message

        result = _parse_completes_from_message("feat: Add feature\n\nCompletes: sqlite-backend-8-task-007")
        assert result == ['sqlite-backend-8-task-007']

    def test_completes_colon_multiple(self):
        """Test 'Completes: id1, id2' pattern."""
        from vibey.roadmap.serialization.yaml_loader import _parse_completes_from_message

        result = _parse_completes_from_message(
            "feat: Big feature\n\nCompletes: task-001, task-002, task-003"
        )
        assert 'task-001' in result
        assert 'task-002' in result
        assert 'task-003' in result

    def test_completes_without_colon(self):
        """Test 'Completes task-id' pattern (without colon)."""
        from vibey.roadmap.serialization.yaml_loader import _parse_completes_from_message

        result = _parse_completes_from_message("Completes sprint-1-task-005")
        assert 'sprint-1-task-005' in result

    def test_closes_pattern(self):
        """Test 'Closes: task-id' pattern."""
        from vibey.roadmap.serialization.yaml_loader import _parse_completes_from_message

        result = _parse_completes_from_message("fix: Bug fix\n\nCloses: sqlite-backend-6-task-001")
        assert 'sqlite-backend-6-task-001' in result

    def test_closes_with_hash(self):
        """Test 'Closes #task-id' pattern."""
        from vibey.roadmap.serialization.yaml_loader import _parse_completes_from_message

        result = _parse_completes_from_message("Closes #roadmap-system-3-task-002")
        assert 'roadmap-system-3-task-002' in result

    def test_fixes_pattern(self):
        """Test 'Fixes: task-id' pattern."""
        from vibey.roadmap.serialization.yaml_loader import _parse_completes_from_message

        result = _parse_completes_from_message("Fixes: bug-tracker-1-task-003")
        assert 'bug-tracker-1-task-003' in result

    def test_fixes_with_hash(self):
        """Test 'Fixes #task-id' pattern."""
        from vibey.roadmap.serialization.yaml_loader import _parse_completes_from_message

        result = _parse_completes_from_message("Fixes #core-framework-2-task-001")
        assert 'core-framework-2-task-001' in result

    def test_conventional_commit_chore(self):
        """Test 'chore(task-id): ...' pattern."""
        from vibey.roadmap.serialization.yaml_loader import _parse_completes_from_message

        result = _parse_completes_from_message("chore(sqlite-backend-8-task-006): Mark task complete")
        assert 'sqlite-backend-8-task-006' in result

    def test_conventional_commit_feat(self):
        """Test 'feat(task-id): ...' pattern."""
        from vibey.roadmap.serialization.yaml_loader import _parse_completes_from_message

        result = _parse_completes_from_message("feat(roadmap-system-1-task-003): Add new feature")
        assert 'roadmap-system-1-task-003' in result

    def test_conventional_commit_fix(self):
        """Test 'fix(task-id): ...' pattern."""
        from vibey.roadmap.serialization.yaml_loader import _parse_completes_from_message

        result = _parse_completes_from_message("fix(core-1-task-002): Fix bug in parser")
        assert 'core-1-task-002' in result

    def test_no_task_reference(self):
        """Test message with no task reference returns empty list."""
        from vibey.roadmap.serialization.yaml_loader import _parse_completes_from_message

        result = _parse_completes_from_message("feat: Add new feature without task reference")
        assert result == []

    def test_filters_short_matches(self):
        """Test that short matches are filtered out."""
        from vibey.roadmap.serialization.yaml_loader import _parse_completes_from_message

        # "a-b" is too short
        result = _parse_completes_from_message("Fixes a-b")
        assert 'a-b' not in result

    def test_filters_generic_words(self):
        """Test that generic words are filtered out."""
        from vibey.roadmap.serialization.yaml_loader import _parse_completes_from_message

        result = _parse_completes_from_message("Closes: task")
        assert 'task' not in result

    def test_case_insensitive(self):
        """Test that patterns are case-insensitive."""
        from vibey.roadmap.serialization.yaml_loader import _parse_completes_from_message

        result1 = _parse_completes_from_message("COMPLETES: my-task-001")
        result2 = _parse_completes_from_message("completes: my-task-001")
        result3 = _parse_completes_from_message("Completes: my-task-001")

        assert 'my-task-001' in result1
        assert 'my-task-001' in result2
        assert 'my-task-001' in result3

    def test_multiple_patterns_same_message(self):
        """Test message with multiple patterns extracts all IDs."""
        from vibey.roadmap.serialization.yaml_loader import _parse_completes_from_message

        result = _parse_completes_from_message(
            "chore(task-001): Update task\n\nCompletes: task-002\nAlso Fixes: task-003"
        )
        assert 'task-001' in result
        assert 'task-002' in result
        assert 'task-003' in result


class TestConvertLegacyCommits:
    """Tests for _convert_legacy_commits function."""

    def test_basic_commit_conversion(self):
        """Test basic commit conversion with required fields."""
        from vibey.roadmap.serialization.yaml_loader import _convert_legacy_commits

        commits_data = [{
            'sha': 'abc123def456',
            'message': 'feat: Add feature',
            'date': '2025-01-01T00:00:00+00:00',
            'author': 'test@example.com',
        }]

        result = _convert_legacy_commits(commits_data)

        assert len(result) == 1
        assert result[0].sha == 'abc123def456'
        assert result[0].message == 'feat: Add feature'
        assert result[0].author == 'test@example.com'

    def test_platform_defaults_to_legacy(self):
        """Test that commits without platform get 'legacy'."""
        from vibey.roadmap.serialization.yaml_loader import _convert_legacy_commits

        commits_data = [{
            'sha': 'abc123',
            'message': 'test commit',
        }]

        result = _convert_legacy_commits(commits_data)

        assert result[0].platform == 'legacy'

    def test_platform_preserved_if_present(self):
        """Test that existing platform is preserved."""
        from vibey.roadmap.serialization.yaml_loader import _convert_legacy_commits

        commits_data = [{
            'sha': 'abc123',
            'message': 'test commit',
            'platform': 'claude-code',
        }]

        result = _convert_legacy_commits(commits_data)

        assert result[0].platform == 'claude-code'

    def test_completes_tickets_from_yaml(self):
        """Test that completes_tickets from YAML is used."""
        from vibey.roadmap.serialization.yaml_loader import _convert_legacy_commits

        commits_data = [{
            'sha': 'abc123',
            'message': 'test commit',
            'completes_tickets': ['task-001', 'task-002'],
        }]

        result = _convert_legacy_commits(commits_data)

        assert result[0].completes_tickets == ['task-001', 'task-002']

    def test_completes_tickets_parsed_from_message(self):
        """Test that completes_tickets is parsed from message if not in YAML."""
        from vibey.roadmap.serialization.yaml_loader import _convert_legacy_commits

        commits_data = [{
            'sha': 'abc123',
            'message': 'chore(sqlite-backend-8-task-007): Mark task complete',
        }]

        result = _convert_legacy_commits(commits_data)

        assert 'sqlite-backend-8-task-007' in result[0].completes_tickets

    def test_yaml_completes_takes_priority(self):
        """Test that YAML completes_tickets takes priority over message parsing."""
        from vibey.roadmap.serialization.yaml_loader import _convert_legacy_commits

        commits_data = [{
            'sha': 'abc123',
            'message': 'chore(task-from-message): Complete task',
            'completes_tickets': ['task-from-yaml'],
        }]

        result = _convert_legacy_commits(commits_data)

        # Should use YAML value, not parse from message
        assert result[0].completes_tickets == ['task-from-yaml']

    def test_file_changes_parsed(self):
        """Test that file changes are parsed."""
        from vibey.roadmap.serialization.yaml_loader import _convert_legacy_commits

        commits_data = [{
            'sha': 'abc123',
            'message': 'test commit',
            'files_added': ['new_file.py'],
            'files_modified': ['existing.py'],
            'files_deleted': ['old.py'],
        }]

        result = _convert_legacy_commits(commits_data)

        assert result[0].files_added == ['new_file.py']
        assert result[0].files_modified == ['existing.py']
        assert result[0].files_deleted == ['old.py']

    def test_artifact_links_parsed(self):
        """Test that artifact links are parsed."""
        from vibey.roadmap.serialization.yaml_loader import _convert_legacy_commits

        commits_data = [{
            'sha': 'abc123',
            'message': 'test commit',
            'creates_artifacts': ['artifact-1'],
            'modifies_artifacts': ['artifact-2'],
            'deletes_artifacts': ['artifact-3'],
        }]

        result = _convert_legacy_commits(commits_data)

        assert result[0].creates_artifacts == ['artifact-1']
        assert result[0].modifies_artifacts == ['artifact-2']
        assert result[0].deletes_artifacts == ['artifact-3']

    def test_skips_commits_without_sha(self):
        """Test that commits without sha are skipped."""
        from vibey.roadmap.serialization.yaml_loader import _convert_legacy_commits

        commits_data = [
            {'message': 'no sha'},
            {'sha': 'valid', 'message': 'has sha'},
        ]

        result = _convert_legacy_commits(commits_data)

        assert len(result) == 1
        assert result[0].sha == 'valid'

    def test_skips_commits_without_message(self):
        """Test that commits without message are skipped."""
        from vibey.roadmap.serialization.yaml_loader import _convert_legacy_commits

        commits_data = [
            {'sha': 'abc123'},  # no message
            {'sha': 'def456', 'message': 'has message'},
        ]

        result = _convert_legacy_commits(commits_data)

        assert len(result) == 1
        assert result[0].sha == 'def456'

    def test_default_author(self):
        """Test that author defaults to 'unknown'."""
        from vibey.roadmap.serialization.yaml_loader import _convert_legacy_commits

        commits_data = [{
            'sha': 'abc123',
            'message': 'test commit',
        }]

        result = _convert_legacy_commits(commits_data)

        assert result[0].author == 'unknown'

    def test_submitted_at_parsed(self):
        """Test that submitted_at timestamp is parsed."""
        from vibey.roadmap.serialization.yaml_loader import _convert_legacy_commits

        commits_data = [{
            'sha': 'abc123',
            'message': 'test commit',
            'submitted_at': '2025-01-15T10:30:00+00:00',
        }]

        result = _convert_legacy_commits(commits_data)

        assert result[0].submitted_at is not None
        assert result[0].submitted_at.year == 2025


class TestGitCommitYamlRoundTrip:
    """Tests for GitCommit YAML round-trip serialization."""

    def test_commit_roundtrip_with_all_fields(self):
        """Test that commit with all fields round-trips correctly."""
        from vibey.roadmap.models.ticket.ticket import GitCommit
        from vibey.roadmap.serialization.yaml_dumper import _dump_git_commit
        from vibey.roadmap.serialization.yaml_loader import _convert_legacy_commits

        original = GitCommit(
            sha='abc123def456',
            message='chore(task-001): Complete task\n\nCompletes: task-002',
            date=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            author='test@example.com',
            platform='claude-code',
            submitted_at=datetime(2025, 1, 1, 12, 5, 0, tzinfo=timezone.utc),
            completes_tickets=['task-001', 'task-002'],
            files_added=['new.py'],
            files_modified=['existing.py'],
            files_deleted=['old.py'],
            creates_artifacts=['artifact-1'],
            modifies_artifacts=['artifact-2'],
            deletes_artifacts=['artifact-3'],
        )

        # Dump to dict
        dumped = _dump_git_commit(original)

        # Load back
        loaded_list = _convert_legacy_commits([dumped])
        loaded = loaded_list[0]

        # Verify fields
        assert loaded.sha == original.sha
        assert loaded.message == original.message
        assert loaded.author == original.author
        assert loaded.platform == original.platform
        assert sorted(loaded.completes_tickets) == sorted(original.completes_tickets)
        assert loaded.files_added == original.files_added
        assert loaded.files_modified == original.files_modified
        assert loaded.files_deleted == original.files_deleted
        assert loaded.creates_artifacts == original.creates_artifacts
        assert loaded.modifies_artifacts == original.modifies_artifacts
        assert loaded.deletes_artifacts == original.deletes_artifacts

    def test_legacy_commit_migration(self):
        """Test that legacy commits without platform get migrated."""
        from vibey.roadmap.serialization.yaml_loader import _convert_legacy_commits

        # Simulate v1 format commit (no platform, no completes_tickets)
        v1_commit = {
            'sha': 'old123',
            'message': 'feat(legacy-task-001): Old commit',
            'date': '2024-06-15T08:00:00+00:00',
            'author': 'old@example.com',
        }

        result = _convert_legacy_commits([v1_commit])

        assert result[0].platform == 'legacy'
        assert 'legacy-task-001' in result[0].completes_tickets
