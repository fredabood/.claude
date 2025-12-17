"""
Tests for vibey.common.errors module.

Tests the unified error handling system.
"""

import pytest
from abc import ABC

from vibey.common.errors import (
    ErrorSeverity,
    ErrorCategory,
    ErrorContext,
    VibeyError,
    ConfigurationError,
    ConfigNotFoundError,
    ConfigValidationError,
    RoadmapError,
    RoadmapNotFoundError,
    TrackNotFoundError,
    SprintNotFoundError,
    TaskNotFoundError,
    DependencyError,
    DependencyBlockedError,
    CircularDependencyError,
    StateError,
    InvalidStateTransitionError,
    QualityGateNotPassedError,
    ValidationError,
    FileSystemError,
    FileNotFoundError as VibeyFileNotFoundError,
    ConcurrencyError,
    ConcurrentModificationError,
    ErrorRenderer,
)


class TestErrorSeverity:
    """Test ErrorSeverity enum."""

    def test_error_value(self):
        """Test ERROR has correct value."""
        assert ErrorSeverity.ERROR.value == "error"

    def test_warning_value(self):
        """Test WARNING has correct value."""
        assert ErrorSeverity.WARNING.value == "warning"

    def test_info_value(self):
        """Test INFO has correct value."""
        assert ErrorSeverity.INFO.value == "info"

    def test_is_string_enum(self):
        """Test ErrorSeverity is str subclass."""
        assert isinstance(ErrorSeverity.ERROR, str)


class TestErrorCategory:
    """Test ErrorCategory enum."""

    def test_configuration_value(self):
        """Test CONFIGURATION has correct value."""
        assert ErrorCategory.CONFIGURATION.value == "configuration"

    def test_roadmap_value(self):
        """Test ROADMAP has correct value."""
        assert ErrorCategory.ROADMAP.value == "roadmap"

    def test_validation_value(self):
        """Test VALIDATION has correct value."""
        assert ErrorCategory.VALIDATION.value == "validation"

    def test_dependency_value(self):
        """Test DEPENDENCY has correct value."""
        assert ErrorCategory.DEPENDENCY.value == "dependency"

    def test_file_system_value(self):
        """Test FILE_SYSTEM has correct value."""
        assert ErrorCategory.FILE_SYSTEM.value == "file_system"

    def test_state_value(self):
        """Test STATE has correct value."""
        assert ErrorCategory.STATE.value == "state"

    def test_concurrency_value(self):
        """Test CONCURRENCY has correct value."""
        assert ErrorCategory.CONCURRENCY.value == "concurrency"

    def test_network_value(self):
        """Test NETWORK has correct value."""
        assert ErrorCategory.NETWORK.value == "network"

    def test_authentication_value(self):
        """Test AUTHENTICATION has correct value."""
        assert ErrorCategory.AUTHENTICATION.value == "authentication"

    def test_unknown_value(self):
        """Test UNKNOWN has correct value."""
        assert ErrorCategory.UNKNOWN.value == "unknown"

    def test_is_string_enum(self):
        """Test ErrorCategory is str subclass."""
        assert isinstance(ErrorCategory.ROADMAP, str)


class TestErrorContext:
    """Test ErrorContext dataclass."""

    def test_basic_construction(self):
        """Test basic ErrorContext construction."""
        ctx = ErrorContext(
            code="TEST_ERROR",
            message="Test error message",
            category=ErrorCategory.UNKNOWN,
        )
        assert ctx.code == "TEST_ERROR"
        assert ctx.message == "Test error message"
        assert ctx.category == ErrorCategory.UNKNOWN

    def test_default_severity(self):
        """Test default severity is ERROR."""
        ctx = ErrorContext(
            code="TEST",
            message="Test",
            category=ErrorCategory.UNKNOWN,
        )
        assert ctx.severity == ErrorSeverity.ERROR

    def test_default_suggestions(self):
        """Test default suggestions is empty list."""
        ctx = ErrorContext(
            code="TEST",
            message="Test",
            category=ErrorCategory.UNKNOWN,
        )
        assert ctx.suggestions == []

    def test_default_hint(self):
        """Test default hint is None."""
        ctx = ErrorContext(
            code="TEST",
            message="Test",
            category=ErrorCategory.UNKNOWN,
        )
        assert ctx.hint is None

    def test_default_fix_command(self):
        """Test default fix_command is None."""
        ctx = ErrorContext(
            code="TEST",
            message="Test",
            category=ErrorCategory.UNKNOWN,
        )
        assert ctx.fix_command is None

    def test_default_related_docs(self):
        """Test default related_docs is None."""
        ctx = ErrorContext(
            code="TEST",
            message="Test",
            category=ErrorCategory.UNKNOWN,
        )
        assert ctx.related_docs is None

    def test_default_metadata(self):
        """Test default metadata is empty dict."""
        ctx = ErrorContext(
            code="TEST",
            message="Test",
            category=ErrorCategory.UNKNOWN,
        )
        assert ctx.metadata == {}

    def test_full_construction(self):
        """Test ErrorContext with all fields."""
        ctx = ErrorContext(
            code="FULL_ERROR",
            message="Full error message",
            category=ErrorCategory.ROADMAP,
            severity=ErrorSeverity.WARNING,
            suggestions=["Try this", "Or this"],
            hint="Additional hint",
            fix_command="vibey fix",
            related_docs="docs/help.md",
            metadata={"key": "value"},
        )
        assert ctx.code == "FULL_ERROR"
        assert ctx.severity == ErrorSeverity.WARNING
        assert len(ctx.suggestions) == 2
        assert ctx.hint == "Additional hint"
        assert ctx.fix_command == "vibey fix"
        assert ctx.related_docs == "docs/help.md"
        assert ctx.metadata == {"key": "value"}

    def test_to_dict(self):
        """Test to_dict serialization."""
        ctx = ErrorContext(
            code="DICT_ERROR",
            message="Dict error",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.INFO,
            suggestions=["Suggestion 1"],
            hint="A hint",
            fix_command="vibey validate",
            related_docs="docs/validation.md",
            metadata={"count": 5},
        )
        result = ctx.to_dict()

        assert result["code"] == "DICT_ERROR"
        assert result["message"] == "Dict error"
        assert result["category"] == "validation"
        assert result["severity"] == "info"
        assert result["suggestions"] == ["Suggestion 1"]
        assert result["hint"] == "A hint"
        assert result["fix_command"] == "vibey validate"
        assert result["related_docs"] == "docs/validation.md"
        assert result["metadata"] == {"count": 5}

    def test_to_dict_with_none_values(self):
        """Test to_dict includes None values."""
        ctx = ErrorContext(
            code="MIN_ERROR",
            message="Minimal",
            category=ErrorCategory.UNKNOWN,
        )
        result = ctx.to_dict()

        assert result["hint"] is None
        assert result["fix_command"] is None
        assert result["related_docs"] is None


class TestVibeyError:
    """Test VibeyError base class."""

    def test_basic_construction(self):
        """Test basic VibeyError construction."""
        error = VibeyError(
            message="Test error",
            code="TEST_ERROR",
        )
        assert str(error) == "Test error"
        assert error.context.code == "TEST_ERROR"

    def test_default_category(self):
        """Test default category is UNKNOWN."""
        error = VibeyError(
            message="Test",
            code="TEST",
        )
        assert error.context.category == ErrorCategory.UNKNOWN

    def test_default_severity(self):
        """Test default severity is ERROR."""
        error = VibeyError(
            message="Test",
            code="TEST",
        )
        assert error.context.severity == ErrorSeverity.ERROR

    def test_inherits_from_exception(self):
        """Test VibeyError inherits from Exception."""
        error = VibeyError(
            message="Test",
            code="TEST",
        )
        assert isinstance(error, Exception)

    def test_can_be_raised(self):
        """Test VibeyError can be raised and caught."""
        with pytest.raises(VibeyError) as exc_info:
            raise VibeyError(message="Raised", code="RAISED")
        assert str(exc_info.value) == "Raised"

    def test_full_construction(self):
        """Test VibeyError with all parameters."""
        error = VibeyError(
            message="Full error",
            code="FULL_ERROR",
            category=ErrorCategory.ROADMAP,
            severity=ErrorSeverity.WARNING,
            suggestions=["Try this"],
            hint="Hint",
            fix_command="vibey fix",
            related_docs="docs/",
            metadata={"key": "value"},
        )
        ctx = error.context
        assert ctx.category == ErrorCategory.ROADMAP
        assert ctx.severity == ErrorSeverity.WARNING
        assert ctx.suggestions == ["Try this"]
        assert ctx.hint == "Hint"
        assert ctx.fix_command == "vibey fix"
        assert ctx.related_docs == "docs/"
        assert ctx.metadata == {"key": "value"}

    def test_str_returns_message(self):
        """Test __str__ returns message."""
        error = VibeyError(message="Message text", code="TEST")
        assert str(error) == "Message text"

    def test_to_dict(self):
        """Test to_dict delegates to context."""
        error = VibeyError(
            message="Dict test",
            code="DICT_TEST",
            category=ErrorCategory.VALIDATION,
        )
        result = error.to_dict()
        assert result["code"] == "DICT_TEST"
        assert result["category"] == "validation"


class TestConfigurationError:
    """Test ConfigurationError class."""

    def test_sets_configuration_category(self):
        """Test category is set to CONFIGURATION."""
        error = ConfigurationError(
            message="Config error",
            code="CONFIG_ERROR",
        )
        assert error.context.category == ErrorCategory.CONFIGURATION

    def test_inherits_from_vibey_error(self):
        """Test inherits from VibeyError."""
        error = ConfigurationError(message="Test", code="TEST")
        assert isinstance(error, VibeyError)


class TestConfigNotFoundError:
    """Test ConfigNotFoundError class."""

    def test_construction(self):
        """Test ConfigNotFoundError construction."""
        error = ConfigNotFoundError(
            searched_paths=["/path/1", "/path/2"]
        )
        assert "Configuration files not found" in str(error)
        assert error.context.code == "CONFIG_NOT_FOUND"

    def test_includes_paths_in_message(self):
        """Test searched paths are in message."""
        error = ConfigNotFoundError(
            searched_paths=["/config/one", "/config/two"]
        )
        assert "/config/one" in str(error)
        assert "/config/two" in str(error)

    def test_has_suggestions(self):
        """Test has helpful suggestions."""
        error = ConfigNotFoundError(searched_paths=[])
        assert len(error.context.suggestions) > 0
        assert any("init" in s.lower() for s in error.context.suggestions)

    def test_has_fix_command(self):
        """Test has fix command."""
        error = ConfigNotFoundError(searched_paths=[])
        assert error.context.fix_command == "vibey init"

    def test_metadata_contains_paths(self):
        """Test metadata contains searched_paths."""
        paths = ["/a", "/b"]
        error = ConfigNotFoundError(searched_paths=paths)
        assert error.context.metadata["searched_paths"] == paths


class TestConfigValidationError:
    """Test ConfigValidationError class."""

    def test_construction(self):
        """Test ConfigValidationError construction."""
        error = ConfigValidationError(
            validation_errors=["Error 1", "Error 2"]
        )
        assert "validation failed" in str(error).lower()
        assert error.context.code == "CONFIG_VALIDATION_FAILED"

    def test_includes_errors_in_message(self):
        """Test validation errors in message."""
        error = ConfigValidationError(
            validation_errors=["Invalid field", "Missing value"]
        )
        assert "Invalid field" in str(error)
        assert "Missing value" in str(error)

    def test_with_config_file(self):
        """Test with config_file parameter."""
        error = ConfigValidationError(
            validation_errors=["Error"],
            config_file="config.yaml"
        )
        assert "config.yaml" in str(error)

    def test_metadata_contains_errors(self):
        """Test metadata contains validation_errors."""
        errors = ["E1", "E2"]
        error = ConfigValidationError(validation_errors=errors)
        assert error.context.metadata["validation_errors"] == errors


class TestRoadmapError:
    """Test RoadmapError class."""

    def test_sets_roadmap_category(self):
        """Test category is set to ROADMAP."""
        error = RoadmapError(
            message="Roadmap error",
            code="ROADMAP_ERROR",
        )
        assert error.context.category == ErrorCategory.ROADMAP


class TestRoadmapNotFoundError:
    """Test RoadmapNotFoundError class."""

    def test_construction(self):
        """Test RoadmapNotFoundError construction."""
        error = RoadmapNotFoundError(searched_dir="/project")
        assert "Roadmap not found" in str(error)
        assert error.context.code == "ROADMAP_NOT_FOUND"

    def test_includes_dir_in_message(self):
        """Test searched directory in message."""
        error = RoadmapNotFoundError(searched_dir="/my/project")
        assert "/my/project" in str(error)

    def test_has_fix_command(self):
        """Test has fix command."""
        error = RoadmapNotFoundError(searched_dir="/")
        assert error.context.fix_command == "vibey roadmap init"


class TestTrackNotFoundError:
    """Test TrackNotFoundError class."""

    def test_construction(self):
        """Test TrackNotFoundError construction."""
        error = TrackNotFoundError(track_id="my-track")
        assert "my-track" in str(error)
        assert error.context.code == "TRACK_NOT_FOUND"

    def test_with_available_tracks(self):
        """Test with available_tracks parameter."""
        error = TrackNotFoundError(
            track_id="missing",
            available_tracks=["backend", "frontend"]
        )
        suggestions = error.context.suggestions
        assert any("backend" in s for s in suggestions)

    def test_metadata_contains_track_id(self):
        """Test metadata contains track_id."""
        error = TrackNotFoundError(track_id="test-track")
        assert error.context.metadata["track_id"] == "test-track"


class TestSprintNotFoundError:
    """Test SprintNotFoundError class."""

    def test_construction(self):
        """Test SprintNotFoundError construction."""
        error = SprintNotFoundError(sprint_id="sprint-1")
        assert "sprint-1" in str(error)
        assert error.context.code == "SPRINT_NOT_FOUND"

    def test_with_track_id(self):
        """Test with track_id parameter."""
        error = SprintNotFoundError(
            sprint_id="sprint-1",
            track_id="backend"
        )
        suggestions = error.context.suggestions
        assert any("backend" in s for s in suggestions)


class TestTaskNotFoundError:
    """Test TaskNotFoundError class."""

    def test_construction(self):
        """Test TaskNotFoundError construction."""
        error = TaskNotFoundError(task_id="task-001")
        assert "task-001" in str(error)
        assert error.context.code == "TASK_NOT_FOUND"

    def test_with_sprint_id(self):
        """Test with sprint_id parameter."""
        error = TaskNotFoundError(
            task_id="task-001",
            sprint_id="sprint-1"
        )
        suggestions = error.context.suggestions
        assert any("sprint-1" in s for s in suggestions)


class TestDependencyError:
    """Test DependencyError class."""

    def test_sets_dependency_category(self):
        """Test category is set to DEPENDENCY."""
        error = DependencyError(
            message="Dep error",
            code="DEP_ERROR",
        )
        assert error.context.category == ErrorCategory.DEPENDENCY


class TestDependencyBlockedError:
    """Test DependencyBlockedError class."""

    def test_construction(self):
        """Test DependencyBlockedError construction."""
        error = DependencyBlockedError(
            object_id="task-002",
            object_type="task",
            blocker_id="task-001",
            blocker_type="task",
            required_status="completed",
            current_status="in_progress",
        )
        assert error.context.code == "DEPENDENCY_BLOCKED"
        assert "task-002" in str(error)
        assert "task-001" in str(error)

    def test_metadata_contains_all_info(self):
        """Test metadata contains all parameters."""
        error = DependencyBlockedError(
            object_id="obj",
            object_type="task",
            blocker_id="blocker",
            blocker_type="sprint",
            required_status="completed",
            current_status="pending",
        )
        meta = error.context.metadata
        assert meta["object_id"] == "obj"
        assert meta["blocker_id"] == "blocker"
        assert meta["required_status"] == "completed"
        assert meta["current_status"] == "pending"


class TestCircularDependencyError:
    """Test CircularDependencyError class."""

    def test_construction(self):
        """Test CircularDependencyError construction."""
        error = CircularDependencyError(
            dependency_chain=["A", "B", "C", "A"]
        )
        assert error.context.code == "CIRCULAR_DEPENDENCY"
        assert "A" in str(error)
        assert "B" in str(error)
        assert "C" in str(error)

    def test_shows_chain_with_arrows(self):
        """Test dependency chain shown with arrows."""
        error = CircularDependencyError(
            dependency_chain=["X", "Y", "Z"]
        )
        assert "→" in str(error)


class TestStateError:
    """Test StateError class."""

    def test_sets_state_category(self):
        """Test category is set to STATE."""
        error = StateError(
            message="State error",
            code="STATE_ERROR",
        )
        assert error.context.category == ErrorCategory.STATE


class TestInvalidStateTransitionError:
    """Test InvalidStateTransitionError class."""

    def test_construction(self):
        """Test InvalidStateTransitionError construction."""
        error = InvalidStateTransitionError(
            object_id="task-001",
            current_status="pending",
            attempted_status="completed",
            valid_transitions=["in_progress"],
        )
        assert error.context.code == "INVALID_STATE_TRANSITION"
        assert "task-001" in str(error)
        assert "pending" in str(error)
        assert "completed" in str(error)

    def test_shows_valid_transitions(self):
        """Test valid transitions shown in message."""
        error = InvalidStateTransitionError(
            object_id="obj",
            current_status="a",
            attempted_status="c",
            valid_transitions=["b", "d"],
        )
        msg = str(error)
        assert "b" in msg or "d" in msg


class TestQualityGateNotPassedError:
    """Test QualityGateNotPassedError class."""

    def test_construction(self):
        """Test QualityGateNotPassedError construction."""
        error = QualityGateNotPassedError(
            object_id="task-001",
            gate_type="completion",
            incomplete_gates=["tests", "review"],
        )
        assert error.context.code == "QUALITY_GATE_NOT_PASSED"
        assert "task-001" in str(error)

    def test_shows_incomplete_gates(self):
        """Test incomplete gates shown in message."""
        error = QualityGateNotPassedError(
            object_id="obj",
            gate_type="production",
            incomplete_gates=["security", "performance"],
        )
        msg = str(error)
        assert "security" in msg
        assert "performance" in msg


class TestValidationError:
    """Test ValidationError class."""

    def test_construction(self):
        """Test ValidationError construction."""
        error = ValidationError(
            object_type="task",
            object_id="task-001",
            errors=["Missing title", "Invalid status"],
        )
        assert error.context.code == "VALIDATION_FAILED"
        assert error.context.category == ErrorCategory.VALIDATION

    def test_shows_errors_in_message(self):
        """Test errors shown in message."""
        error = ValidationError(
            object_type="sprint",
            object_id="sprint-1",
            errors=["Error A", "Error B"],
        )
        msg = str(error)
        assert "Error A" in msg
        assert "Error B" in msg


class TestFileSystemError:
    """Test FileSystemError class."""

    def test_sets_file_system_category(self):
        """Test category is set to FILE_SYSTEM."""
        error = FileSystemError(
            message="FS error",
            code="FS_ERROR",
        )
        assert error.context.category == ErrorCategory.FILE_SYSTEM


class TestVibeyFileNotFoundError:
    """Test Vibey FileNotFoundError class."""

    def test_construction(self):
        """Test FileNotFoundError construction."""
        error = VibeyFileNotFoundError(
            file_path="/path/to/file.yaml",
            file_type="Track",
        )
        assert error.context.code == "FILE_NOT_FOUND"
        assert "/path/to/file.yaml" in str(error)
        assert "Track" in str(error)


class TestConcurrencyError:
    """Test ConcurrencyError class."""

    def test_sets_concurrency_category(self):
        """Test category is set to CONCURRENCY."""
        error = ConcurrencyError(
            message="Concurrency error",
            code="CONC_ERROR",
        )
        assert error.context.category == ErrorCategory.CONCURRENCY


class TestConcurrentModificationError:
    """Test ConcurrentModificationError class."""

    def test_construction(self):
        """Test ConcurrentModificationError construction."""
        error = ConcurrentModificationError(
            object_id="task-001",
            expected_version="v1",
            actual_version="v2",
        )
        assert error.context.code == "CONCURRENT_MODIFICATION"
        assert "task-001" in str(error)
        assert "v1" in str(error)
        assert "v2" in str(error)

    def test_metadata_contains_versions(self):
        """Test metadata contains version info."""
        error = ConcurrentModificationError(
            object_id="obj",
            expected_version="1.0",
            actual_version="2.0",
        )
        meta = error.context.metadata
        assert meta["expected_version"] == "1.0"
        assert meta["actual_version"] == "2.0"


class TestErrorRenderer:
    """Test ErrorRenderer abstract base class."""

    def test_is_abstract(self):
        """Test ErrorRenderer is abstract."""
        assert issubclass(ErrorRenderer, ABC)

    def test_has_render_method(self):
        """Test has abstract render method."""
        assert hasattr(ErrorRenderer, "render")

    def test_has_render_multiple_method(self):
        """Test has abstract render_multiple method."""
        assert hasattr(ErrorRenderer, "render_multiple")

    def test_cannot_instantiate(self):
        """Test cannot instantiate abstract class."""
        with pytest.raises(TypeError):
            ErrorRenderer()


class TestErrorHierarchy:
    """Test error class hierarchy."""

    def test_all_errors_inherit_from_vibey_error(self):
        """Test all error classes inherit from VibeyError."""
        error_classes = [
            ConfigurationError,
            ConfigNotFoundError,
            ConfigValidationError,
            RoadmapError,
            RoadmapNotFoundError,
            TrackNotFoundError,
            SprintNotFoundError,
            TaskNotFoundError,
            DependencyError,
            DependencyBlockedError,
            CircularDependencyError,
            StateError,
            InvalidStateTransitionError,
            QualityGateNotPassedError,
            ValidationError,
            FileSystemError,
            VibeyFileNotFoundError,
            ConcurrencyError,
            ConcurrentModificationError,
        ]
        for cls in error_classes:
            assert issubclass(cls, VibeyError)

    def test_config_errors_inherit_from_configuration_error(self):
        """Test config errors inherit from ConfigurationError."""
        assert issubclass(ConfigNotFoundError, ConfigurationError)
        assert issubclass(ConfigValidationError, ConfigurationError)

    def test_roadmap_errors_inherit_from_roadmap_error(self):
        """Test roadmap errors inherit from RoadmapError."""
        assert issubclass(RoadmapNotFoundError, RoadmapError)
        assert issubclass(TrackNotFoundError, RoadmapError)
        assert issubclass(SprintNotFoundError, RoadmapError)
        assert issubclass(TaskNotFoundError, RoadmapError)

    def test_dependency_errors_inherit_from_dependency_error(self):
        """Test dependency errors inherit from DependencyError."""
        assert issubclass(DependencyBlockedError, DependencyError)
        assert issubclass(CircularDependencyError, DependencyError)

    def test_state_errors_inherit_from_state_error(self):
        """Test state errors inherit from StateError."""
        assert issubclass(InvalidStateTransitionError, StateError)
        assert issubclass(QualityGateNotPassedError, StateError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
