"""
Tests for the Unified Pre-commit Hook with Triangle Validation.

Tests cover all four phases:
1. Collect Data - Parse commit message, resolve artifacts
2. Triangle Validation - Check consistency across relationships
3. Completion Verification - Verify Completes: claims
4. Persist Relationships - Build pending relationship records

Task: 01KCMNDFWS0C2N2FJJBZRR3FC8
Track: Context System V2
Sprint: Sprint 2: Context Implementation
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from datetime import datetime, timezone

from vibey.operations.git.hooks.pre_commit import (
    # Configuration
    PreCommitHookConfig,
    ArtifactConsistencyConfig,
    CompletionVerificationConfig,
    ArtifactConsistencyMode,
    CompletionVerificationMode,
    Resolution,
    # Data models
    CommitData,
    TriangleValidationResult,
    CompletionVerificationResult,
    PendingRelationships,
    HookResult,
    ValidationIssue,
    # Main hook class
    UnifiedPreCommitHook,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def default_config():
    """Create default hook configuration."""
    return PreCommitHookConfig()


@pytest.fixture
def strict_config():
    """Create strict mode configuration."""
    return PreCommitHookConfig(
        artifact_consistency=ArtifactConsistencyConfig(
            mode=ArtifactConsistencyMode.STRICT,
            on_staged_not_associated="block",
            on_no_task_ref="block",
        ),
        completion_verification=CompletionVerificationConfig(
            mode=CompletionVerificationMode.STRICT,
            block_on_unmet_criteria=True,
        ),
    )


@pytest.fixture
def warn_config():
    """Create warn-only configuration."""
    return PreCommitHookConfig(
        artifact_consistency=ArtifactConsistencyConfig(
            mode=ArtifactConsistencyMode.WARN,
            on_staged_not_associated="warn",
            on_no_task_ref="warn",
        ),
        completion_verification=CompletionVerificationConfig(
            mode=CompletionVerificationMode.WARN,
        ),
    )


@pytest.fixture
def mock_hook(tmp_path, default_config):
    """Create a hook with mocked git operations."""
    # Create a fake .git directory
    (tmp_path / ".git").mkdir()

    hook = UnifiedPreCommitHook(str(tmp_path), default_config)
    return hook


# =============================================================================
# PHASE 1: COLLECT DATA TESTS
# =============================================================================


class TestPhase1CollectData:
    """Tests for Phase 1: Data collection."""

    def test_parse_task_reference(self, mock_hook):
        """Test parsing Task: lines from commit message."""
        message = """feat: Add new feature

Task: 01KCMNDFWS0C2N2FJJBZRR3FC8

Implements the new feature."""

        task_refs, completion_claims = mock_hook._parse_commit_message(message)

        assert len(task_refs) == 1
        assert task_refs[0] == "01KCMNDFWS0C2N2FJJBZRR3FC8"
        assert len(completion_claims) == 0

    def test_parse_completes_reference(self, mock_hook):
        """Test parsing Completes: lines from commit message."""
        message = """feat: Complete feature

Task: 01KCMNDFWS0C2N2FJJBZRR3FC8
Completes: 01KCMNDFWS0C2N2FJJBZRR3FC8

Final implementation."""

        task_refs, completion_claims = mock_hook._parse_commit_message(message)

        assert len(task_refs) == 1
        assert len(completion_claims) == 1
        assert completion_claims[0] == "01KCMNDFWS0C2N2FJJBZRR3FC8"

    def test_parse_multiple_task_references(self, mock_hook):
        """Test parsing multiple Task: references."""
        message = """feat: Multi-task commit

Task: 01KCMNDFWS0C2N2FJJBZRR3FC8, 01KCMTJQ3JRRW6CZFC4E63W8D6
Task: 01KCMNCZS970T6MSXDY2CZA2YH

Work spanning multiple tasks."""

        task_refs, completion_claims = mock_hook._parse_commit_message(message)

        assert len(task_refs) == 3
        assert "01KCMNDFWS0C2N2FJJBZRR3FC8" in task_refs
        assert "01KCMTJQ3JRRW6CZFC4E63W8D6" in task_refs
        assert "01KCMNCZS970T6MSXDY2CZA2YH" in task_refs

    def test_parse_ignores_comments(self, mock_hook):
        """Test that comment lines are ignored."""
        message = """feat: Feature

# Task: 01KCMNDFWS0C2N2FJJBZRR3FC8
Task: 01KCMTJQ3JRRW6CZFC4E63W8D6"""

        task_refs, completion_claims = mock_hook._parse_commit_message(message)

        assert len(task_refs) == 1
        assert task_refs[0] == "01KCMTJQ3JRRW6CZFC4E63W8D6"

    def test_validate_ulid_format(self, mock_hook):
        """Test ULID validation."""
        # Valid ULIDs
        valid_ids = [
            "01KCMNDFWS0C2N2FJJBZRR3FC8",
            "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        ]
        assert all(mock_hook.ULID_PATTERN.match(id) for id in valid_ids)

        # Invalid IDs
        invalid_ids = [
            "not-a-ulid",
            "01KCMNDFWS0C2N2F",  # Too short
            "01KCMNDFWS0C2N2FJJBZRR3FC8ABC",  # Too long
        ]
        assert not any(mock_hook.ULID_PATTERN.match(id) for id in invalid_ids)

    def test_case_insensitive_parsing(self, mock_hook):
        """Test that Task: and task: both work."""
        message = """feat: Feature

task: 01KCMNDFWS0C2N2FJJBZRR3FC8
TASK: 01KCMTJQ3JRRW6CZFC4E63W8D6
completes: 01KCMNCZS970T6MSXDY2CZA2YH"""

        task_refs, completion_claims = mock_hook._parse_commit_message(message)

        assert len(task_refs) == 2
        assert len(completion_claims) == 1


# =============================================================================
# PHASE 2: TRIANGLE VALIDATION TESTS
# =============================================================================


class TestPhase2TriangleValidation:
    """Tests for Phase 2: Triangle validation."""

    def test_overlap_detection(self, mock_hook):
        """Test detection of overlapping artifacts."""
        # Mock the ticket artifacts lookup
        mock_hook._get_ticket_artifacts = MagicMock(
            return_value={"artifact_1", "artifact_2", "artifact_3"}
        )

        commit_data = CommitData(
            task_refs=["01KCMNDFWS0C2N2FJJBZRR3FC8"],
            staged_artifacts={
                "file1.py": "artifact_1",
                "file2.py": "artifact_2",
                "file3.py": "artifact_4",  # Not in ticket
            },
        )

        results = mock_hook.phase_2_triangle_validation(commit_data)

        assert len(results) == 1
        result = results[0]

        # Check overlap (A intersection B)
        assert result.overlap == {"artifact_1", "artifact_2"}

        # Check staged_only (A - B)
        assert result.staged_only == {"artifact_4"}

        # Check ticket_only (B - A)
        assert result.ticket_only == {"artifact_3"}

    def test_no_issues_when_perfect_match(self, mock_hook):
        """Test no issues when staged exactly matches ticket artifacts."""
        mock_hook._get_ticket_artifacts = MagicMock(
            return_value={"artifact_1", "artifact_2"}
        )

        commit_data = CommitData(
            task_refs=["01KCMNDFWS0C2N2FJJBZRR3FC8"],
            staged_artifacts={
                "file1.py": "artifact_1",
                "file2.py": "artifact_2",
            },
        )

        results = mock_hook.phase_2_triangle_validation(commit_data)

        assert len(results) == 1
        result = results[0]
        assert result.overlap == {"artifact_1", "artifact_2"}
        assert len(result.staged_only) == 0
        assert len(result.ticket_only) == 0
        assert not result.has_issues

    def test_strict_mode_requires_resolution(self, tmp_path, strict_config):
        """Test that strict mode requires resolution for mismatches."""
        (tmp_path / ".git").mkdir()
        hook = UnifiedPreCommitHook(str(tmp_path), strict_config)

        hook._get_ticket_artifacts = MagicMock(return_value=set())

        commit_data = CommitData(
            task_refs=["01KCMNDFWS0C2N2FJJBZRR3FC8"],
            staged_artifacts={"file.py": "artifact_1"},
        )

        results = hook.phase_2_triangle_validation(commit_data)

        assert len(results) == 1
        result = results[0]
        assert result.staged_only == {"artifact_1"}
        assert result.requires_resolution

    def test_warn_mode_does_not_require_resolution(self, tmp_path, warn_config):
        """Test that warn mode doesn't require resolution."""
        (tmp_path / ".git").mkdir()
        hook = UnifiedPreCommitHook(str(tmp_path), warn_config)

        hook._get_ticket_artifacts = MagicMock(return_value=set())

        commit_data = CommitData(
            task_refs=["01KCMNDFWS0C2N2FJJBZRR3FC8"],
            staged_artifacts={"file.py": "artifact_1"},
        )

        results = hook.phase_2_triangle_validation(commit_data)

        assert len(results) == 1
        result = results[0]
        assert result.is_valid  # Valid in warn mode

    def test_off_mode_skips_validation(self, tmp_path):
        """Test that off mode skips triangle validation."""
        (tmp_path / ".git").mkdir()
        config = PreCommitHookConfig(
            artifact_consistency=ArtifactConsistencyConfig(
                mode=ArtifactConsistencyMode.OFF
            )
        )
        hook = UnifiedPreCommitHook(str(tmp_path), config)

        commit_data = CommitData(
            task_refs=["01KCMNDFWS0C2N2FJJBZRR3FC8"],
            staged_artifacts={"file.py": "artifact_1"},
        )

        results = hook.phase_2_triangle_validation(commit_data)

        assert len(results) == 0


# =============================================================================
# PHASE 3: COMPLETION VERIFICATION TESTS
# =============================================================================


class TestPhase3CompletionVerification:
    """Tests for Phase 3: Completion verification."""

    def test_successful_completion(self, mock_hook):
        """Test successful completion verification."""
        # Mock successful completion check
        mock_ticket = MagicMock()
        mock_ticket.can_transition_to.return_value = (True, [])
        mock_ticket.criteria = []

        with patch(
            "vibey.operations.roadmap.query.load_task_ticket",
            return_value=mock_ticket
        ):
            with patch(
                "vibey.roadmap.models.ticket.TicketStatus"
            ):
                result = mock_hook._verify_ticket_completion("01KCMNDFWS0C2N2FJJBZRR3FC8")

        assert result.can_complete
        assert len(result.blocking_reasons) == 0

    def test_blocked_completion(self, mock_hook):
        """Test blocked completion verification."""
        # Mock blocked completion
        mock_ticket = MagicMock()
        mock_ticket.can_transition_to.return_value = (
            False,
            ["Required tests not passing", "Documentation incomplete"]
        )

        # Mock unmet criteria
        mock_criterion = MagicMock()
        mock_criterion.description = "Tests must pass"
        mock_criterion.blocks_transition_to = "COMPLETED"
        mock_criterion.is_met = False
        mock_ticket.criteria = [mock_criterion]

        with patch(
            "vibey.operations.roadmap.query.load_task_ticket",
            return_value=mock_ticket
        ):
            with patch(
                "vibey.roadmap.models.ticket.TicketStatus"
            ) as mock_status:
                mock_status.COMPLETED = "COMPLETED"
                result = mock_hook._verify_ticket_completion("01KCMNDFWS0C2N2FJJBZRR3FC8")

        assert not result.can_complete
        assert len(result.blocking_reasons) == 2
        assert "Required tests not passing" in result.blocking_reasons

    def test_ticket_not_found(self, mock_hook):
        """Test completion verification with missing ticket."""
        with patch(
            "vibey.operations.roadmap.query.load_task_ticket",
            return_value=None
        ):
            result = mock_hook._verify_ticket_completion("01KCMNDFWS0C2N2FJJBZRR3FC8")

        assert not result.can_complete
        assert "not found" in result.blocking_reasons[0]

    def test_off_mode_skips_verification(self, tmp_path):
        """Test that off mode skips completion verification."""
        (tmp_path / ".git").mkdir()
        config = PreCommitHookConfig(
            completion_verification=CompletionVerificationConfig(
                mode=CompletionVerificationMode.OFF
            )
        )
        hook = UnifiedPreCommitHook(str(tmp_path), config)

        commit_data = CommitData(
            completion_claims=["01KCMNDFWS0C2N2FJJBZRR3FC8"],
        )

        results = hook.phase_3_completion_verification(commit_data)

        assert len(results) == 0


# =============================================================================
# PHASE 4: BUILD PENDING RELATIONSHIPS TESTS
# =============================================================================


class TestPhase4BuildPendingRelationships:
    """Tests for Phase 4: Building pending relationships."""

    def test_builds_ticket_commit_links(self, mock_hook):
        """Test building TicketCommitLink records."""
        mock_hook._get_staged_file_status = MagicMock(return_value={})
        mock_hook._get_line_stats = MagicMock(return_value=(10, 5))

        commit_data = CommitData(
            commit_sha="abc123",
            task_refs=["01KCMNDFWS0C2N2FJJBZRR3FC8"],
            completion_claims=["01KCMTJQ3JRRW6CZFC4E63W8D6"],
            staged_artifacts={},
        )

        pending = mock_hook.phase_4_build_pending_relationships(
            commit_data, [], {}
        )

        assert len(pending.ticket_commit_links) == 2

        # Check task reference link
        task_link = next(
            l for l in pending.ticket_commit_links
            if l["ticket_id"] == "01KCMNDFWS0C2N2FJJBZRR3FC8"
        )
        assert task_link["reference_type"] == "task_reference"
        assert task_link["commit_sha"] == "abc123"

        # Check completion claim link
        complete_link = next(
            l for l in pending.ticket_commit_links
            if l["ticket_id"] == "01KCMTJQ3JRRW6CZFC4E63W8D6"
        )
        assert complete_link["reference_type"] == "completion_claim"

    def test_builds_commit_artifact_changes(self, mock_hook):
        """Test building CommitArtifactChange records."""
        mock_hook._get_staged_file_status = MagicMock(return_value={
            "file1.py": "A",  # Added
            "file2.py": "M",  # Modified
        })
        mock_hook._get_line_stats = MagicMock(return_value=(10, 5))

        commit_data = CommitData(
            commit_sha="abc123",
            task_refs=[],
            staged_artifacts={
                "file1.py": "artifact_1",
                "file2.py": "artifact_2",
            },
        )

        pending = mock_hook.phase_4_build_pending_relationships(
            commit_data, [], {}
        )

        assert len(pending.commit_artifact_changes) == 2

        # Check added file
        added = next(
            c for c in pending.commit_artifact_changes
            if c["artifact_id"] == "artifact_1"
        )
        assert added["change_type"] == "added"

        # Check modified file
        modified = next(
            c for c in pending.commit_artifact_changes
            if c["artifact_id"] == "artifact_2"
        )
        assert modified["change_type"] == "modified"

    def test_builds_associations_on_user_resolution(self, mock_hook):
        """Test building TicketArtifactAssociation on user resolution."""
        mock_hook._get_staged_file_status = MagicMock(return_value={})
        mock_hook._get_line_stats = MagicMock(return_value=(0, 0))

        commit_data = CommitData(
            commit_sha="abc123",
            task_refs=["01KCMNDFWS0C2N2FJJBZRR3FC8"],
            staged_artifacts={"file.py": "artifact_1"},
        )

        triangle_result = TriangleValidationResult(
            ticket_id="01KCMNDFWS0C2N2FJJBZRR3FC8",
            staged_only={"artifact_1"},
        )

        user_resolutions = {
            "01KCMNDFWS0C2N2FJJBZRR3FC8": Resolution.UPDATE_ASSOCIATIONS
        }

        pending = mock_hook.phase_4_build_pending_relationships(
            commit_data, [triangle_result], user_resolutions
        )

        assert len(pending.ticket_artifact_associations) == 1
        assoc = pending.ticket_artifact_associations[0]
        assert assoc["ticket_id"] == "01KCMNDFWS0C2N2FJJBZRR3FC8"
        assert assoc["artifact_id"] == "artifact_1"
        assert assoc["association_source"] == "commit_bootstrap"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIntegration:
    """Integration tests for the full hook flow."""

    def test_full_run_with_no_issues(self, tmp_path):
        """Test full hook run with no issues."""
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "COMMIT_EDITMSG").write_text(
            "feat: Add feature\n\nTask: 01KCMNDFWS0C2N2FJJBZRR3FC8"
        )

        config = PreCommitHookConfig(
            artifact_consistency=ArtifactConsistencyConfig(
                mode=ArtifactConsistencyMode.OFF
            ),
            completion_verification=CompletionVerificationConfig(
                mode=CompletionVerificationMode.OFF
            ),
        )

        hook = UnifiedPreCommitHook(str(tmp_path), config)
        hook._get_staged_files = MagicMock(return_value=[])
        hook._get_current_sha = MagicMock(return_value="abc123")

        result = hook.run()

        assert not result.blocked
        assert len(result.reasons) == 0

    def test_strict_mode_blocks_on_mismatch(self, tmp_path):
        """Test that strict mode blocks on artifact mismatch."""
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "COMMIT_EDITMSG").write_text(
            "feat: Add feature\n\nTask: 01KCMNDFWS0C2N2FJJBZRR3FC8"
        )

        config = PreCommitHookConfig(
            artifact_consistency=ArtifactConsistencyConfig(
                mode=ArtifactConsistencyMode.STRICT
            ),
            completion_verification=CompletionVerificationConfig(
                mode=CompletionVerificationMode.OFF
            ),
        )

        hook = UnifiedPreCommitHook(str(tmp_path), config)
        hook._get_staged_files = MagicMock(return_value=["file.py"])
        hook._get_current_sha = MagicMock(return_value="abc123")
        hook._resolve_to_artifacts = MagicMock(return_value={"file.py": "artifact_1"})
        hook._get_ticket_artifacts = MagicMock(return_value=set())  # No match

        result = hook.run()

        assert result.blocked
        assert any("strict mode" in r.lower() for r in result.reasons)

    def test_disabled_hook_returns_early(self, tmp_path):
        """Test that disabled hook returns immediately."""
        (tmp_path / ".git").mkdir()

        config = PreCommitHookConfig(enabled=False)
        hook = UnifiedPreCommitHook(str(tmp_path), config)

        result = hook.run()

        assert not result.blocked
        assert result.pending_relationships is None


# =============================================================================
# CONFIGURATION TESTS
# =============================================================================


class TestConfiguration:
    """Tests for configuration loading."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PreCommitHookConfig()

        assert config.enabled is True
        assert config.artifact_consistency.mode == ArtifactConsistencyMode.PROMPT
        assert config.completion_verification.mode == CompletionVerificationMode.STRICT

    def test_load_from_yaml(self, tmp_path):
        """Test loading configuration from YAML file."""
        config_content = """
pre_commit:
  enabled: true
  artifact_consistency:
    mode: warn
    on_mismatch:
      staged_not_in_associations: warn
      no_task_ref: ignore
  completion_verification:
    mode: warn
    block_on_unmet_criteria: false
"""
        config_file = tmp_path / "git_hooks.yaml"
        config_file.write_text(config_content)

        config = PreCommitHookConfig.load(config_file)

        assert config.artifact_consistency.mode == ArtifactConsistencyMode.WARN
        assert config.completion_verification.mode == CompletionVerificationMode.WARN
        assert not config.completion_verification.block_on_unmet_criteria


# =============================================================================
# RESOLUTION TESTS
# =============================================================================


class TestResolutions:
    """Tests for user resolution handling."""

    def test_cancel_resolution_blocks_commit(self, tmp_path):
        """Test that cancel resolution blocks the commit."""
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "COMMIT_EDITMSG").write_text(
            "feat: Add feature\n\nTask: 01KCMNDFWS0C2N2FJJBZRR3FC8"
        )

        config = PreCommitHookConfig(
            artifact_consistency=ArtifactConsistencyConfig(
                mode=ArtifactConsistencyMode.PROMPT
            ),
            completion_verification=CompletionVerificationConfig(
                mode=CompletionVerificationMode.OFF
            ),
        )

        hook = UnifiedPreCommitHook(str(tmp_path), config)
        hook._get_staged_files = MagicMock(return_value=["file.py"])
        hook._get_current_sha = MagicMock(return_value="abc123")
        hook._resolve_to_artifacts = MagicMock(return_value={"file.py": "artifact_1"})
        hook._get_ticket_artifacts = MagicMock(return_value=set())

        # Mock user selecting cancel
        hook.prompt_for_resolutions = MagicMock(
            return_value={"01KCMNDFWS0C2N2FJJBZRR3FC8": Resolution.CANCEL}
        )

        result = hook.run()

        assert result.blocked
        assert "User cancelled commit" in result.reasons

    def test_proceed_resolution_allows_commit(self, tmp_path):
        """Test that proceed resolution allows the commit."""
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "COMMIT_EDITMSG").write_text(
            "feat: Add feature\n\nTask: 01KCMNDFWS0C2N2FJJBZRR3FC8"
        )

        config = PreCommitHookConfig(
            artifact_consistency=ArtifactConsistencyConfig(
                mode=ArtifactConsistencyMode.PROMPT
            ),
            completion_verification=CompletionVerificationConfig(
                mode=CompletionVerificationMode.OFF
            ),
        )

        hook = UnifiedPreCommitHook(str(tmp_path), config)
        hook._get_staged_files = MagicMock(return_value=["file.py"])
        hook._get_current_sha = MagicMock(return_value="abc123")
        hook._get_staged_file_status = MagicMock(return_value={"file.py": "M"})
        hook._get_line_stats = MagicMock(return_value=(10, 5))
        hook._resolve_to_artifacts = MagicMock(return_value={"file.py": "artifact_1"})
        hook._get_ticket_artifacts = MagicMock(return_value=set())

        # Mock user selecting proceed
        hook.prompt_for_resolutions = MagicMock(
            return_value={"01KCMNDFWS0C2N2FJJBZRR3FC8": Resolution.PROCEED}
        )

        result = hook.run()

        assert not result.blocked
        assert result.pending_relationships is not None
