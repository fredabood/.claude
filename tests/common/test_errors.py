"""
Comprehensive tests for vibey.common.errors module.

Tests all error types, their creation, context, and serialization.
Focuses on achieving 100% coverage of errors.py.
"""

import pytest

from vibey.common.errors import (
    # Base classes and enums
    VibeyError,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    ErrorRenderer,
    # Configuration errors
    ConfigurationError,
    ConfigNotFoundError,
    ConfigValidationError,
    # Roadmap errors
    RoadmapError,
    RoadmapNotFoundError,
    TrackNotFoundError,
    SprintNotFoundError,
    TaskNotFoundError,
    # Dependency errors
    DependencyError,
    DependencyBlockedError,
    CircularDependencyError,
    # State errors
    StateError,
    InvalidStateTransitionError,
    QualityGateNotPassedError,
    # Validation errors
    ValidationError,
    # File system errors
    FileSystemError,
    FileNotFoundError,
    # Concurrency errors
    ConcurrencyError,
    ConcurrentModificationError,
)


class TestErrorSeverity:
    """Test ErrorSeverity enum."""

    def test_error_severity_values(self):
        """Test all severity values exist."""
        assert ErrorSeverity.ERROR.value == "error"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.INFO.value == "info"

    def test_severity_is_string_enum(self):
        """Test severity can be used as string."""
        assert str(ErrorSeverity.ERROR) == "ErrorSeverity.ERROR"
        assert ErrorSeverity.ERROR == "error"


class TestErrorCategory:
    """Test ErrorCategory enum."""

    def test_all_categories_exist(self):
        """Test all error categories are defined."""
        categories = [
            ErrorCategory.CONFIGURATION,
            ErrorCategory.ROADMAP,
            ErrorCategory.VALIDATION,
            ErrorCategory.DEPENDENCY,
            ErrorCategory.FILE_SYSTEM,
            ErrorCategory.STATE,
            ErrorCategory.CONCURRENCY,
            ErrorCategory.NETWORK,
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.UNKNOWN,
        ]
        assert len(categories) == 10

    def test_category_values(self):
        """Test category string values."""
        assert ErrorCategory.CONFIGURATION.value == "configuration"
        assert ErrorCategory.ROADMAP.value == "roadmap"
        assert ErrorCategory.UNKNOWN.value == "unknown"


class TestErrorContext:
    """Test ErrorContext dataclass."""

    def test_context_creation_minimal(self):
        """Test creating context with minimal fields."""
        ctx = ErrorContext(
            code="TEST_ERROR",
            message="Test error message",
            category=ErrorCategory.UNKNOWN,
        )
        assert ctx.code == "TEST_ERROR"
        assert ctx.message == "Test error message"
        assert ctx.category == ErrorCategory.UNKNOWN
        assert ctx.severity == ErrorSeverity.ERROR  # default
        assert ctx.suggestions == []  # default empty list
        assert ctx.hint is None
        assert ctx.fix_command is None
        assert ctx.related_docs is None
        assert ctx.metadata == {}  # default empty dict

    def test_context_creation_full(self):
        """Test creating context with all fields."""
        ctx = ErrorContext(
            code="FULL_ERROR",
            message="Full error message",
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.WARNING,
            suggestions=["Suggestion 1", "Suggestion 2"],
            hint="This is a hint",
            fix_command="vibey fix",
            related_docs="docs/guide.md",
            metadata={"key": "value"},
        )
        assert ctx.severity == ErrorSeverity.WARNING
        assert len(ctx.suggestions) == 2
        assert ctx.hint == "This is a hint"
        assert ctx.fix_command == "vibey fix"
        assert ctx.related_docs == "docs/guide.md"
        assert ctx.metadata["key"] == "value"

    def test_context_to_dict(self):
        """Test context serialization to dictionary."""
        ctx = ErrorContext(
            code="DICT_TEST",
            message="Dict test",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.INFO,
            suggestions=["Try this"],
            hint="A hint",
            fix_command="vibey cmd",
            related_docs="docs/ref.md",
            metadata={"extra": "data"},
        )
        data = ctx.to_dict()

        assert data["code"] == "DICT_TEST"
        assert data["message"] == "Dict test"
        assert data["category"] == "validation"
        assert data["severity"] == "info"
        assert data["suggestions"] == ["Try this"]
        assert data["hint"] == "A hint"
        assert data["fix_command"] == "vibey cmd"
        assert data["related_docs"] == "docs/ref.md"
        assert data["metadata"]["extra"] == "data"


class TestVibeyError:
    """Test base VibeyError class."""

    def test_error_creation_minimal(self):
        """Test creating error with minimal args."""
        error = VibeyError(
            message="Test error",
            code="TEST_CODE",
        )
        assert str(error) == "Test error"
        assert error.context.code == "TEST_CODE"
        assert error.context.category == ErrorCategory.UNKNOWN

    def test_error_creation_full(self):
        """Test creating error with all args."""
        error = VibeyError(
            message="Full error",
            code="FULL_CODE",
            category=ErrorCategory.ROADMAP,
            severity=ErrorSeverity.WARNING,
            suggestions=["Do this", "Or that"],
            hint="Helpful hint",
            fix_command="vibey fix",
            related_docs="docs/help.md",
            metadata={"id": 123},
        )
        assert error.context.category == ErrorCategory.ROADMAP
        assert error.context.severity == ErrorSeverity.WARNING
        assert len(error.context.suggestions) == 2
        assert error.context.metadata["id"] == 123

    def test_error_to_dict(self):
        """Test error serialization."""
        error = VibeyError(
            message="Serializable",
            code="SERIAL",
            metadata={"test": True},
        )
        data = error.to_dict()
        assert data["code"] == "SERIAL"
        assert data["metadata"]["test"] is True

    def test_error_inheritance(self):
        """Test error inherits from Exception."""
        error = VibeyError(message="Test", code="TEST")
        assert isinstance(error, Exception)


class TestSprintNotFoundError:
    """Test SprintNotFoundError with track_id parameter."""

    def test_without_track_id(self):
        """Test error without track_id."""
        error = SprintNotFoundError(sprint_id="sprint-1")
        assert error.context.code == "SPRINT_NOT_FOUND"
        assert "sprint-1" in error.context.message
        assert error.context.metadata["track_id"] is None

    def test_with_track_id(self):
        """Test error with track_id provides specific suggestion."""
        error = SprintNotFoundError(sprint_id="sprint-1", track_id="backend")
        assert "sprint-1" in error.context.message
        assert error.context.metadata["track_id"] == "backend"
        # Should have suggestion referencing the track
        suggestions_str = " ".join(error.context.suggestions)
        assert "backend" in suggestions_str


class TestTaskNotFoundError:
    """Test TaskNotFoundError with sprint_id parameter."""

    def test_without_sprint_id(self):
        """Test error without sprint_id."""
        error = TaskNotFoundError(task_id="task-1")
        assert error.context.code == "TASK_NOT_FOUND"
        assert "task-1" in error.context.message
        assert error.context.metadata["sprint_id"] is None

    def test_with_sprint_id(self):
        """Test error with sprint_id provides specific suggestion."""
        error = TaskNotFoundError(task_id="task-1", sprint_id="sprint-1")
        assert "task-1" in error.context.message
        assert error.context.metadata["sprint_id"] == "sprint-1"
        # Should have suggestion referencing the sprint
        suggestions_str = " ".join(error.context.suggestions)
        assert "sprint-1" in suggestions_str


class TestCircularDependencyError:
    """Test CircularDependencyError."""

    def test_circular_dependency_creation(self):
        """Test creating circular dependency error."""
        chain = ["task-a", "task-b", "task-c", "task-a"]
        error = CircularDependencyError(dependency_chain=chain)

        assert error.context.code == "CIRCULAR_DEPENDENCY"
        assert error.context.category == ErrorCategory.DEPENDENCY
        assert "task-a → task-b → task-c → task-a" in error.context.message
        assert error.context.metadata["dependency_chain"] == chain
        assert len(error.context.suggestions) > 0

    def test_short_chain(self):
        """Test with minimal circular chain."""
        chain = ["a", "b", "a"]
        error = CircularDependencyError(dependency_chain=chain)
        assert "a → b → a" in error.context.message


class TestInvalidStateTransitionError:
    """Test InvalidStateTransitionError."""

    def test_invalid_transition(self):
        """Test invalid state transition error."""
        error = InvalidStateTransitionError(
            object_id="task-1",
            current_status="not_started",
            attempted_status="completed",
            valid_transitions=["in_progress"],
        )

        assert error.context.code == "INVALID_STATE_TRANSITION"
        assert error.context.category == ErrorCategory.STATE
        assert "task-1" in error.context.message
        assert "not_started" in error.context.message
        assert "completed" in error.context.message
        assert "'in_progress'" in error.context.message
        assert error.context.metadata["valid_transitions"] == ["in_progress"]

    def test_multiple_valid_transitions(self):
        """Test with multiple valid transitions."""
        error = InvalidStateTransitionError(
            object_id="sprint-1",
            current_status="in_progress",
            attempted_status="not_started",
            valid_transitions=["completed", "blocked"],
        )
        assert "'completed'" in error.context.message
        assert "'blocked'" in error.context.message


class TestFileNotFoundError:
    """Test custom FileNotFoundError (not built-in)."""

    def test_file_not_found(self):
        """Test file not found error creation."""
        error = FileNotFoundError(
            file_path="/path/to/file.yaml",
            file_type="Configuration",
        )

        assert error.context.code == "FILE_NOT_FOUND"
        assert error.context.category == ErrorCategory.FILE_SYSTEM
        assert "/path/to/file.yaml" in error.context.message
        assert "Configuration" in error.context.message
        assert error.context.metadata["file_path"] == "/path/to/file.yaml"
        assert error.context.metadata["file_type"] == "Configuration"

    def test_different_file_types(self):
        """Test with different file types."""
        for file_type in ["YAML", "Task", "Sprint", "Database"]:
            error = FileNotFoundError(file_path="/test", file_type=file_type)
            assert file_type in error.context.message


class TestConcurrentModificationError:
    """Test ConcurrentModificationError."""

    def test_concurrent_modification(self):
        """Test concurrent modification error."""
        error = ConcurrentModificationError(
            object_id="task-123",
            expected_version="v1",
            actual_version="v2",
        )

        assert error.context.code == "CONCURRENT_MODIFICATION"
        assert error.context.category == ErrorCategory.CONCURRENCY
        assert "task-123" in error.context.message
        assert "v1" in error.context.message
        assert "v2" in error.context.message
        assert error.context.metadata["object_id"] == "task-123"
        assert error.context.metadata["expected_version"] == "v1"
        assert error.context.metadata["actual_version"] == "v2"


class TestConfigValidationError:
    """Test ConfigValidationError with optional config_file parameter."""

    def test_without_config_file(self):
        """Test error without config_file."""
        error = ConfigValidationError(
            validation_errors=["Error 1", "Error 2"]
        )
        assert error.context.code == "CONFIG_VALIDATION_FAILED"
        assert "Error 1" in error.context.message
        assert "Error 2" in error.context.message
        assert error.context.metadata["config_file"] is None

    def test_with_config_file(self):
        """Test error with config_file includes it in message."""
        error = ConfigValidationError(
            validation_errors=["Missing field"],
            config_file="/path/to/config.yaml"
        )
        assert "config.yaml" in error.context.message
        assert error.context.metadata["config_file"] == "/path/to/config.yaml"


class TestBaseErrorClasses:
    """Test base error class categories."""

    def test_configuration_error_category(self):
        """Test ConfigurationError sets correct category."""
        error = ConfigurationError(
            message="Config error",
            code="CONFIG_TEST",
        )
        assert error.context.category == ErrorCategory.CONFIGURATION

    def test_roadmap_error_category(self):
        """Test RoadmapError sets correct category."""
        error = RoadmapError(
            message="Roadmap error",
            code="ROADMAP_TEST",
        )
        assert error.context.category == ErrorCategory.ROADMAP

    def test_dependency_error_category(self):
        """Test DependencyError sets correct category."""
        error = DependencyError(
            message="Dependency error",
            code="DEP_TEST",
        )
        assert error.context.category == ErrorCategory.DEPENDENCY

    def test_state_error_category(self):
        """Test StateError sets correct category."""
        error = StateError(
            message="State error",
            code="STATE_TEST",
        )
        assert error.context.category == ErrorCategory.STATE

    def test_file_system_error_category(self):
        """Test FileSystemError sets correct category."""
        error = FileSystemError(
            message="File error",
            code="FILE_TEST",
        )
        assert error.context.category == ErrorCategory.FILE_SYSTEM

    def test_concurrency_error_category(self):
        """Test ConcurrencyError sets correct category."""
        error = ConcurrencyError(
            message="Concurrency error",
            code="CONC_TEST",
        )
        assert error.context.category == ErrorCategory.CONCURRENCY


class TestErrorRenderer:
    """Test ErrorRenderer abstract base class."""

    def test_renderer_is_abstract(self):
        """Test that ErrorRenderer cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ErrorRenderer()

    def test_concrete_renderer_implementation(self):
        """Test implementing a custom renderer."""
        class TestRenderer(ErrorRenderer):
            def render(self, error):
                return f"Rendered: {error.context.code}"

            def render_multiple(self, errors):
                return [self.render(e) for e in errors]

        renderer = TestRenderer()
        error = VibeyError(message="Test", code="TEST")
        assert renderer.render(error) == "Rendered: TEST"
        assert renderer.render_multiple([error]) == ["Rendered: TEST"]
