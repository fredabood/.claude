"""
Unit tests for standard validators.

Tests all validator implementations:
- CommitCheckValidator
- FileCheckValidator
- TestRunValidator
- CustomScriptValidator
- ValidatorRegistry
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import subprocess

from vibey.roadmap.standards import (
    CommitCheckValidator,
    FileCheckValidator,
    TestRunValidator,
    CustomScriptValidator,
    ValidatorRegistry,
    validate_standards,
    create_default_registry,
    ValidationStatus,
)
from vibey.roadmap.models import (
    Standard,
    StandardType,
    EnforcementMode,
    Task,
    TaskType,
    TaskStatus,
    Status,
    Priority,
    Complexity,
    Deliverable,
    DeliverableType,
    TaskMetadata,
    GitCommit,
)


# ==================== Test Helpers ====================


def create_test_task(
    task_id="track-1-task-001",
    commits=None,
    deliverables=None,
):
    """Helper to create a valid Task object for testing."""
    now = datetime.now(timezone.utc)

    return Task(
        id=task_id,
        sprint_id="track-1",
        track_id="track",
        roadmap_id="test-roadmap",
        task_type=TaskType.DEVELOPMENT,
        title="Test Task",
        description="Test description",
        status=TaskStatus.IN_PROGRESS,
        blocked=False,
        created=now,
        started=now,  # IN_PROGRESS tasks require started date
        assigned_agent="test-agent",
        priority=Priority.MEDIUM,
        estimated_tokens=1000,
        complexity=Complexity.MEDIUM,
        dependencies=[],
        blocks=[],
        blocked_by=[],
        depends_on=[],
        depended_on_by=[],
        metadata=TaskMetadata(last_updated=now),
        deliverables=deliverables or [],
        commits=commits or [],
    )


# ==================== CommitCheckValidator Tests ====================


class TestCommitCheckValidator:
    """Tests for CommitCheckValidator."""

    def test_can_validate_commit_check_standard(self, tmp_path):
        """Validator should accept COMMIT_CHECK standards."""
        validator = CommitCheckValidator(str(tmp_path))

        standard = Standard(
            id="test-commit",
            name="Test Commit",
            description="Test",
            type=StandardType.COMMIT_CHECK,
            enforcement=EnforcementMode.BLOCKING,
            validation={"min_commits": 1},
            created=datetime.now(timezone.utc),
        )

        assert validator.can_validate(standard) is True

    def test_cannot_validate_other_standard_types(self, tmp_path):
        """Validator should reject non-COMMIT_CHECK standards."""
        validator = CommitCheckValidator(str(tmp_path))

        standard = Standard(
            id="test-file",
            name="Test File",
            description="Test",
            type=StandardType.FILE_CHECK,
            enforcement=EnforcementMode.BLOCKING,
            validation={"pattern": "*.py"},  # Need non-empty validation
            created=datetime.now(timezone.utc),
        )

        assert validator.can_validate(standard) is False

    def test_validate_passes_with_sufficient_commits(self, tmp_path):
        """Validation should pass when task has enough commits."""
        # Create mock task with 2 commits
        now = datetime.now(timezone.utc)
        commits = [
            GitCommit(sha="abc1234", message="First commit", date=now, author="test", platform="claude-code", submitted_at=int(now.timestamp())),
            GitCommit(sha="def5678", message="Second commit", date=now, author="test", platform="claude-code", submitted_at=int(now.timestamp())),
        ]
        task = create_test_task(commits=commits)

        # Mock load_tasks to return our task
        with patch('vibey.roadmap.standards.validators.commit_check.load_tasks') as mock_load:
            mock_load.return_value = [task]

            # Mock FileSystemManager
            with patch('vibey.cli.roadmap_lib.filesystem.FileSystemManager'):
                validator = CommitCheckValidator(str(tmp_path))

                standard = Standard(
                    id="test-commit",
                    name="Test Commit",
                    description="Test",
                    type=StandardType.COMMIT_CHECK,
                    enforcement=EnforcementMode.BLOCKING,
                    validation={"min_commits": 2},
                    created=datetime.now(timezone.utc),
                )

                result = validator.validate(standard, "track-1-task-001")

                assert result.status == ValidationStatus.PASSED
                assert result.metadata["commit_count"] == 2
                assert result.metadata["min_commits"] == 2

    def test_validate_fails_with_insufficient_commits(self, tmp_path):
        """Validation should fail when task has too few commits."""
        # Create mock task with 1 commit
        now = datetime.now(timezone.utc)
        commits = [
            GitCommit(sha="abc1234", message="First commit", date=now, author="test", platform="claude-code", submitted_at=int(now.timestamp())),
        ]
        task = create_test_task(commits=commits)

        with patch('vibey.roadmap.standards.validators.commit_check.load_tasks') as mock_load:
            mock_load.return_value = [task]

            with patch('vibey.cli.roadmap_lib.filesystem.FileSystemManager'):
                validator = CommitCheckValidator(str(tmp_path))

                standard = Standard(
                    id="test-commit",
                    name="Test Commit",
                    description="Test",
                    type=StandardType.COMMIT_CHECK,
                    enforcement=EnforcementMode.BLOCKING,
                    validation={"min_commits": 3},
                    created=datetime.now(timezone.utc),
                )

                result = validator.validate(standard, "track-1-task-001")

                assert result.status == ValidationStatus.FAILED
                assert len(result.issues) == 1
                assert result.issues[0].severity == "error"
                assert result.metadata["commit_count"] == 1
                assert result.metadata["min_commits"] == 3

    def test_validate_error_when_task_not_found(self, tmp_path):
        """Validation should error when task doesn't exist."""
        with patch('vibey.roadmap.standards.validators.commit_check.load_tasks') as mock_load:
            mock_load.return_value = []

            with patch('vibey.cli.roadmap_lib.filesystem.FileSystemManager'):
                validator = CommitCheckValidator(str(tmp_path))

                standard = Standard(
                    id="test-commit",
                    name="Test Commit",
                    description="Test",
                    type=StandardType.COMMIT_CHECK,
                    enforcement=EnforcementMode.BLOCKING,
                    validation={"min_commits": 1},
                    created=datetime.now(timezone.utc),
                )

                result = validator.validate(standard, "track-1-task-001")

                assert result.status == ValidationStatus.ERROR
                assert "Task not found" in result.message

    def test_extract_sprint_id_from_task_id(self, tmp_path):
        """Should correctly extract sprint ID from task ID."""
        validator = CommitCheckValidator(str(tmp_path))

        # Test various formats
        assert validator._extract_sprint_id("track-1-task-001") == "track-1"
        assert validator._extract_sprint_id("my-track-2-task-abc") == "my-track-2"
        assert validator._extract_sprint_id("core-framework-1-task-005") == "core-framework-1"


# ==================== FileCheckValidator Tests ====================


class TestFileCheckValidator:
    """Tests for FileCheckValidator."""

    def test_can_validate_file_check_standard(self, tmp_path):
        """Validator should accept FILE_CHECK standards."""
        validator = FileCheckValidator(str(tmp_path))

        standard = Standard(
            id="test-file",
            name="Test File",
            description="Test",
            type=StandardType.FILE_CHECK,
            enforcement=EnforcementMode.BLOCKING,
            validation={"pattern": "**/*.md"},
            created=datetime.now(timezone.utc),
        )

        assert validator.can_validate(standard) is True

    def test_validate_pattern_passes_with_matching_files(self, tmp_path):
        """Validation should pass when files match pattern."""
        deliverables = [
            Deliverable(
                type=DeliverableType.CODE,
                paths=["README.md", "docs/API.md", "src/main.py"],
            )
        ]
        task = create_test_task(deliverables=deliverables)

        with patch('vibey.roadmap.standards.validators.file_check.load_tasks') as mock_load:
            mock_load.return_value = [task]

            # Mock FileSystemManager to return our sprint
            mock_fs = Mock()
            mock_fs.list_sprints.return_value = ["track-1"]
            with patch('vibey.cli.roadmap_lib.filesystem.FileSystemManager', return_value=mock_fs):
                validator = FileCheckValidator(str(tmp_path))

                standard = Standard(
                    id="test-file",
                    name="Test File",
                    description="Test",
                    type=StandardType.FILE_CHECK,
                    enforcement=EnforcementMode.BLOCKING,
                    validation={"pattern": "*.md", "min_files": 1},
                    created=datetime.now(timezone.utc),
                )

                result = validator.validate(standard, "track-1-task-001")

                assert result.status == ValidationStatus.PASSED
                # fnmatch's * matches across path separators, so both README.md and docs/API.md match *.md
                assert result.metadata["match_count"] == 2
                assert "README.md" in result.metadata["matched_files"]
                assert "docs/API.md" in result.metadata["matched_files"]

    def test_validate_pattern_fails_with_insufficient_matches(self, tmp_path):
        """Validation should fail when not enough files match."""
        deliverables = [
            Deliverable(
                type=DeliverableType.CODE,
                paths=["src/main.py", "src/utils.py"],
            )
        ]
        task = create_test_task(deliverables=deliverables)

        with patch('vibey.roadmap.standards.validators.file_check.load_tasks') as mock_load:
            mock_load.return_value = [task]

            # Mock FileSystemManager to return our sprint
            mock_fs = Mock()
            mock_fs.list_sprints.return_value = ["track-1"]
            with patch('vibey.cli.roadmap_lib.filesystem.FileSystemManager', return_value=mock_fs):
                validator = FileCheckValidator(str(tmp_path))

                standard = Standard(
                    id="test-file",
                    name="Test File",
                    description="Test",
                    type=StandardType.FILE_CHECK,
                    enforcement=EnforcementMode.BLOCKING,
                    validation={"pattern": "*.md", "min_files": 1},
                    created=datetime.now(timezone.utc),
                )

                result = validator.validate(standard, "track-1-task-001")

                assert result.status == ValidationStatus.FAILED
                assert result.metadata["match_count"] == 0

    def test_validate_paths_passes_with_all_required_paths(self, tmp_path):
        """Validation should pass when all required paths are present."""
        deliverables = [
            Deliverable(
                type=DeliverableType.CODE,
                paths=["README.md", "docs/API.md", "src/main.py"],
            )
        ]
        task = create_test_task(deliverables=deliverables)

        with patch('vibey.roadmap.standards.validators.file_check.load_tasks') as mock_load:
            mock_load.return_value = [task]

            # Mock FileSystemManager to return our sprint
            mock_fs = Mock()
            mock_fs.list_sprints.return_value = ["track-1"]
            with patch('vibey.cli.roadmap_lib.filesystem.FileSystemManager', return_value=mock_fs):
                validator = FileCheckValidator(str(tmp_path))

                standard = Standard(
                    id="test-file",
                    name="Test File",
                    description="Test",
                    type=StandardType.FILE_CHECK,
                    enforcement=EnforcementMode.BLOCKING,
                    validation={"paths": ["README.md", "docs/API.md"]},
                    created=datetime.now(timezone.utc),
                )

                result = validator.validate(standard, "track-1-task-001")

                assert result.status == ValidationStatus.PASSED
                assert len(result.metadata["missing_paths"]) == 0

    def test_validate_paths_fails_with_missing_paths(self, tmp_path):
        """Validation should fail when required paths are missing."""
        deliverables = [
            Deliverable(
                type=DeliverableType.CODE,
                paths=["src/main.py"],
            )
        ]
        task = create_test_task(deliverables=deliverables)

        with patch('vibey.roadmap.standards.validators.file_check.load_tasks') as mock_load:
            mock_load.return_value = [task]

            # Mock FileSystemManager to return our sprint
            mock_fs = Mock()
            mock_fs.list_sprints.return_value = ["track-1"]
            with patch('vibey.cli.roadmap_lib.filesystem.FileSystemManager', return_value=mock_fs):
                validator = FileCheckValidator(str(tmp_path))

                standard = Standard(
                    id="test-file",
                    name="Test File",
                    description="Test",
                    type=StandardType.FILE_CHECK,
                    enforcement=EnforcementMode.BLOCKING,
                    validation={"paths": ["README.md", "docs/API.md"]},
                    created=datetime.now(timezone.utc),
                )

                result = validator.validate(standard, "track-1-task-001")

                assert result.status == ValidationStatus.FAILED
                assert len(result.metadata["missing_paths"]) == 2


# ==================== TestRunValidator Tests ====================


class TestTestRunValidator:
    """Tests for TestRunValidator."""

    def test_can_validate_test_run_standard(self, tmp_path):
        """Validator should accept TEST_RUN standards."""
        validator = TestRunValidator(str(tmp_path))

        standard = Standard(
            id="test-run",
            name="Test Run",
            description="Test",
            type=StandardType.TEST_RUN,
            enforcement=EnforcementMode.BLOCKING,
            validation={"command": "pytest", "threshold": 80},
            created=datetime.now(timezone.utc),
        )

        assert validator.can_validate(standard) is True

    def test_validate_passes_with_sufficient_coverage(self, tmp_path):
        """Validation should pass when coverage meets threshold."""
        validator = TestRunValidator(str(tmp_path))

        standard = Standard(
            id="test-run",
            name="Test Run",
            description="Test",
            type=StandardType.TEST_RUN,
            enforcement=EnforcementMode.BLOCKING,
            validation={"command": "pytest --cov", "threshold": 80.0},
            created=datetime.now(timezone.utc),
        )

        # Mock subprocess to return output with coverage
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "TOTAL                    142     18    85%"
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            result = validator.validate(standard, "track-1-task-001")

            assert result.status == ValidationStatus.PASSED
            assert result.metadata["coverage"] == 85.0
            assert result.metadata["threshold"] == 80.0

    def test_validate_fails_with_insufficient_coverage(self, tmp_path):
        """Validation should fail when coverage below threshold."""
        validator = TestRunValidator(str(tmp_path))

        standard = Standard(
            id="test-run",
            name="Test Run",
            description="Test",
            type=StandardType.TEST_RUN,
            enforcement=EnforcementMode.BLOCKING,
            validation={"command": "pytest --cov", "threshold": 90.0},
            created=datetime.now(timezone.utc),
        )

        # Mock subprocess to return output with lower coverage
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "coverage: 75.5%"
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            result = validator.validate(standard, "track-1-task-001")

            assert result.status == ValidationStatus.FAILED
            assert result.metadata["coverage"] == 75.5
            assert result.metadata["threshold"] == 90.0
            assert len(result.issues) == 1

    def test_validate_fails_when_coverage_not_found(self, tmp_path):
        """Validation should fail when coverage cannot be parsed."""
        validator = TestRunValidator(str(tmp_path))

        standard = Standard(
            id="test-run",
            name="Test Run",
            description="Test",
            type=StandardType.TEST_RUN,
            enforcement=EnforcementMode.BLOCKING,
            validation={"command": "pytest", "threshold": 80.0},
            created=datetime.now(timezone.utc),
        )

        # Mock subprocess to return output without coverage
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "All tests passed"
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            result = validator.validate(standard, "track-1-task-001")

            assert result.status == ValidationStatus.FAILED
            assert "parse coverage" in result.message.lower()

    def test_parse_coverage_pytest_format(self, tmp_path):
        """Should parse pytest-cov TOTAL line format."""
        validator = TestRunValidator(str(tmp_path))

        stdout = """
        src/main.py      50      5    90%
        src/utils.py     30      3    90%
        TOTAL           142     18    87%
        """

        coverage, pattern = validator._parse_coverage(stdout, "")

        assert coverage == 87.0
        assert pattern is not None

    def test_parse_coverage_generic_format(self, tmp_path):
        """Should parse generic 'coverage: XX%' format."""
        validator = TestRunValidator(str(tmp_path))

        stdout = "Tests passed! Coverage: 92.5%"

        coverage, pattern = validator._parse_coverage(stdout, "")

        assert coverage == 92.5
        assert pattern is not None

    def test_validate_error_with_timeout(self, tmp_path):
        """Validation should error when command times out."""
        validator = TestRunValidator(str(tmp_path))

        standard = Standard(
            id="test-run",
            name="Test Run",
            description="Test",
            type=StandardType.TEST_RUN,
            enforcement=EnforcementMode.BLOCKING,
            validation={"command": "pytest", "threshold": 80.0},
            created=datetime.now(timezone.utc),
        )

        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("pytest", 300)):
            result = validator.validate(standard, "track-1-task-001")

            assert result.status == ValidationStatus.ERROR
            assert "timed out" in result.message


# ==================== CustomScriptValidator Tests ====================


class TestCustomScriptValidator:
    """Tests for CustomScriptValidator."""

    def test_can_validate_custom_script_standard(self, tmp_path):
        """Validator should accept CUSTOM_SCRIPT standards."""
        validator = CustomScriptValidator(str(tmp_path))

        standard = Standard(
            id="custom",
            name="Custom",
            description="Test",
            type=StandardType.CUSTOM_SCRIPT,
            enforcement=EnforcementMode.BLOCKING,
            validation={"script": "validate.sh"},
            created=datetime.now(timezone.utc),
        )

        assert validator.can_validate(standard) is True

    def test_validate_passes_with_zero_exit_code(self, tmp_path):
        """Validation should pass when script exits 0."""
        # Create a mock script file
        script_path = tmp_path / "validate.sh"
        script_path.write_text("#!/bin/bash\nexit 0")
        script_path.chmod(0o755)

        validator = CustomScriptValidator(str(tmp_path))

        standard = Standard(
            id="custom",
            name="Custom",
            description="Test",
            type=StandardType.CUSTOM_SCRIPT,
            enforcement=EnforcementMode.BLOCKING,
            validation={"script": "validate.sh"},
            created=datetime.now(timezone.utc),
        )

        # Mock subprocess to return success
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Validation passed"
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            result = validator.validate(standard, "track-1-task-001")

            assert result.status == ValidationStatus.PASSED
            assert result.metadata["exit_code"] == 0

    def test_validate_fails_with_nonzero_exit_code(self, tmp_path):
        """Validation should fail when script exits non-zero."""
        script_path = tmp_path / "validate.sh"
        script_path.write_text("#!/bin/bash\nexit 1")
        script_path.chmod(0o755)

        validator = CustomScriptValidator(str(tmp_path))

        standard = Standard(
            id="custom",
            name="Custom",
            description="Test",
            type=StandardType.CUSTOM_SCRIPT,
            enforcement=EnforcementMode.BLOCKING,
            validation={"script": "validate.sh"},
            created=datetime.now(timezone.utc),
        )

        # Mock subprocess to return failure
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "ERROR: Validation failed"
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            result = validator.validate(standard, "track-1-task-001")

            assert result.status == ValidationStatus.FAILED
            assert result.metadata["exit_code"] == 1

    def test_parse_output_extracts_structured_issues(self, tmp_path):
        """Should parse ERROR:, WARNING:, INFO: prefixes."""
        validator = CustomScriptValidator(str(tmp_path))

        stdout = """
        ERROR: Missing required file
        WARNING: Code style issues found
        INFO: 10 tests passed
        """

        issues = validator._parse_output(stdout, "")

        assert len(issues) == 3
        assert issues[0].severity == "error"
        assert "Missing required file" in issues[0].message
        assert issues[1].severity == "warning"
        assert issues[2].severity == "info"

    def test_validate_error_when_script_not_found(self, tmp_path):
        """Validation should error when script doesn't exist."""
        validator = CustomScriptValidator(str(tmp_path))

        standard = Standard(
            id="custom",
            name="Custom",
            description="Test",
            type=StandardType.CUSTOM_SCRIPT,
            enforcement=EnforcementMode.BLOCKING,
            validation={"script": "nonexistent.sh"},
            created=datetime.now(timezone.utc),
        )

        result = validator.validate(standard, "track-1-task-001")

        assert result.status == ValidationStatus.ERROR
        assert "Script not found" in result.message


# ==================== ValidatorRegistry Tests ====================


class TestValidatorRegistry:
    """Tests for ValidatorRegistry."""

    def test_register_validator(self, tmp_path):
        """Should register validators."""
        registry = ValidatorRegistry()
        validator = CommitCheckValidator(str(tmp_path))

        registry.register(validator)

        assert len(registry.validators) == 1
        assert registry.validators[0] == validator

    def test_get_validator_returns_matching_validator(self, tmp_path):
        """Should return validator that can validate the standard."""
        registry = ValidatorRegistry()
        commit_validator = CommitCheckValidator(str(tmp_path))
        file_validator = FileCheckValidator(str(tmp_path))

        registry.register(commit_validator)
        registry.register(file_validator)

        standard = Standard(
            id="test",
            name="Test",
            description="Test",
            type=StandardType.COMMIT_CHECK,
            enforcement=EnforcementMode.BLOCKING,
            validation={"min_commits": 1},
            created=datetime.now(timezone.utc),
        )

        validator = registry.get_validator(standard)

        assert validator == commit_validator

    def test_get_validator_raises_when_no_match(self, tmp_path):
        """Should raise ValueError when no validator can validate."""
        registry = ValidatorRegistry()

        standard = Standard(
            id="test",
            name="Test",
            description="Test",
            type=StandardType.COMMIT_CHECK,
            enforcement=EnforcementMode.BLOCKING,
            validation={"min_commits": 1},
            created=datetime.now(timezone.utc),
        )

        with pytest.raises(ValueError, match="No validator registered"):
            registry.get_validator(standard)

    def test_create_default_registry_includes_all_validators(self, tmp_path):
        """Default registry should include all validators."""
        registry = create_default_registry(str(tmp_path))

        assert len(registry.validators) == 4

        # Check that each validator type is present
        validator_types = [type(v).__name__ for v in registry.validators]
        assert "CommitCheckValidator" in validator_types
        assert "FileCheckValidator" in validator_types
        assert "TestRunValidator" in validator_types
        assert "CustomScriptValidator" in validator_types
