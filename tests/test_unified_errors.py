"""
Integration tests for unified error handling system.

Tests error creation, context, and rendering across all platforms.
"""

import pytest
import json
from pathlib import Path

from vibey.common import (
    VibeyError,
    ErrorCategory,
    ErrorSeverity,
    # Configuration errors
    ConfigNotFoundError,
    ConfigValidationError,
    # Roadmap errors
    RoadmapNotFoundError,
    TrackNotFoundError,
    SprintNotFoundError,
    TaskNotFoundError,
    # Dependency errors
    DependencyBlockedError,
    CircularDependencyError,
    # State errors
    InvalidStateTransitionError,
    QualityGateNotPassedError,
    # Validation errors
    ValidationError,
)

from vibey.common.renderers import (
    CLIErrorRenderer,
    MCPErrorRenderer,
    PlainTextRenderer,
    LogErrorRenderer,
)


class TestErrorCreation:
    """Test error creation and context."""

    def test_config_not_found_error(self):
        """Test ConfigNotFoundError creation."""
        error = ConfigNotFoundError(
            searched_paths=["/path1", "/path2"]
        )

        assert error.context.code == "CONFIG_NOT_FOUND"
        assert error.context.category == ErrorCategory.CONFIGURATION
        assert error.context.severity == ErrorSeverity.ERROR
        assert len(error.context.suggestions) > 0
        assert error.context.hint is not None
        assert error.context.fix_command == "vibey init"
        assert "/path1" in error.context.metadata["searched_paths"]

    def test_roadmap_not_found_error(self):
        """Test RoadmapNotFoundError creation."""
        error = RoadmapNotFoundError(searched_dir="/project")

        assert error.context.code == "ROADMAP_NOT_FOUND"
        assert error.context.category == ErrorCategory.ROADMAP
        assert "/project" in error.context.message
        assert "Initialize roadmap" in error.context.suggestions[0]

    def test_track_not_found_error(self):
        """Test TrackNotFoundError creation."""
        error = TrackNotFoundError(
            track_id="backend-api",
            available_tracks=["frontend", "infra"]
        )

        assert error.context.code == "TRACK_NOT_FOUND"
        assert "backend-api" in error.context.message
        assert "frontend" in error.context.metadata["available_tracks"]

    def test_dependency_blocked_error(self):
        """Test DependencyBlockedError creation."""
        error = DependencyBlockedError(
            object_id="sprint-2",
            object_type="sprint",
            blocker_id="sprint-1",
            blocker_type="sprint",
            required_status="completed",
            current_status="in_progress",
        )

        assert error.context.code == "DEPENDENCY_BLOCKED"
        assert error.context.category == ErrorCategory.DEPENDENCY
        assert "sprint-1" in error.context.message
        assert "in_progress" in error.context.message

    def test_quality_gate_not_passed_error(self):
        """Test QualityGateNotPassedError creation."""
        error = QualityGateNotPassedError(
            object_id="sprint-1",
            gate_type="completion",
            incomplete_gates=["Security Audit", "Code Review"],
        )

        assert error.context.code == "QUALITY_GATE_NOT_PASSED"
        assert error.context.category == ErrorCategory.STATE
        assert "Security Audit" in error.context.message


class TestCLIRendering:
    """Test CLI error rendering."""

    def test_cli_renderer_with_colors(self):
        """Test CLI renderer with ANSI colors."""
        error = RoadmapNotFoundError(searched_dir="/test")
        renderer = CLIErrorRenderer(use_colors=True)
        output = renderer.render(error)

        assert "ROADMAP_NOT_FOUND" in output
        assert "/test" in output
        assert "Suggestions:" in output
        assert "vibey roadmap init" in output
        assert "\033[" in output  # Contains ANSI codes

    def test_cli_renderer_without_colors(self):
        """Test CLI renderer without colors."""
        error = RoadmapNotFoundError(searched_dir="/test")
        renderer = CLIErrorRenderer(use_colors=False)
        output = renderer.render(error)

        assert "ROADMAP_NOT_FOUND" in output
        assert "/test" in output
        assert "\033[" not in output  # No ANSI codes

    def test_cli_render_multiple(self):
        """Test rendering multiple errors."""
        errors = [
            RoadmapNotFoundError(searched_dir="/test1"),
            TrackNotFoundError("backend", available_tracks=["frontend"]),
        ]
        renderer = CLIErrorRenderer(use_colors=False)
        output = renderer.render_multiple(errors)

        assert "2 error(s) occurred" in output
        assert "ROADMAP_NOT_FOUND" in output
        assert "TRACK_NOT_FOUND" in output


class TestMCPRendering:
    """Test MCP error rendering."""

    def test_mcp_renderer(self):
        """Test MCP JSON rendering."""
        error = TrackNotFoundError(
            track_id="backend",
            available_tracks=["frontend", "infra"]
        )
        renderer = MCPErrorRenderer()
        output = renderer.render(error)

        assert isinstance(output, dict)
        assert output["error"]["code"] == "TRACK_NOT_FOUND"
        assert output["error"]["category"] == "roadmap"
        assert output["error"]["severity"] == "error"
        assert len(output["details"]["suggestions"]) > 0

    def test_mcp_to_json(self):
        """Test MCP JSON string serialization."""
        error = ConfigNotFoundError(searched_paths=["/path1"])
        renderer = MCPErrorRenderer()
        json_str = renderer.to_json(error)

        # Should be valid JSON
        data = json.loads(json_str)
        assert data["error"]["code"] == "CONFIG_NOT_FOUND"
        assert data["error"]["category"] == "configuration"

    def test_mcp_render_multiple(self):
        """Test rendering multiple errors as JSON."""
        errors = [
            ConfigNotFoundError(searched_paths=["/path1"]),
            ValidationError("sprint", "sprint-1", ["Missing field"]),
        ]
        renderer = MCPErrorRenderer()
        output = renderer.render_multiple(errors)

        assert output["count"] == 2
        assert len(output["errors"]) == 2


class TestPlainTextRendering:
    """Test plain text rendering."""

    def test_plain_text_renderer(self):
        """Test plain text renderer (no colors)."""
        error = RoadmapNotFoundError(searched_dir="/test")
        renderer = PlainTextRenderer()
        output = renderer.render(error)

        assert "ROADMAP_NOT_FOUND" in output
        assert "\033[" not in output  # No ANSI codes
        assert "Suggestions:" in output


class TestLogRendering:
    """Test structured logging renderer."""

    def test_log_renderer(self):
        """Test log renderer output."""
        error = DependencyBlockedError(
            object_id="sprint-2",
            object_type="sprint",
            blocker_id="sprint-1",
            blocker_type="sprint",
            required_status="completed",
            current_status="in_progress",
        )
        renderer = LogErrorRenderer()
        output = renderer.render(error)

        assert output["level"] == "ERROR"
        assert output["error_code"] == "DEPENDENCY_BLOCKED"
        assert output["error_category"] == "dependency"
        assert "sprint-1" in output["message"]

    def test_log_render_multiple(self):
        """Test rendering multiple errors for logging."""
        errors = [
            ConfigNotFoundError(searched_paths=["/path1"]),
            ValidationError("sprint", "sprint-1", ["Missing field"]),
        ]
        renderer = LogErrorRenderer()
        output = renderer.render_multiple(errors)

        assert len(output) == 2
        assert all("level" in entry for entry in output)
        assert all("error_code" in entry for entry in output)


class TestErrorContext:
    """Test error context and metadata."""

    def test_error_to_dict(self):
        """Test error serialization to dictionary."""
        error = TrackNotFoundError("backend", available_tracks=["frontend"])
        data = error.to_dict()

        assert data["code"] == "TRACK_NOT_FOUND"
        assert data["category"] == "roadmap"
        assert data["severity"] == "error"
        assert "suggestions" in data
        assert "metadata" in data

    def test_error_str_representation(self):
        """Test error string representation."""
        error = RoadmapNotFoundError(searched_dir="/test")
        error_str = str(error)

        assert "/test" in error_str
        assert "Roadmap not found" in error_str


class TestConfigLoaderIntegration:
    """Test config loader integration with unified errors."""

    def test_config_loader_uses_unified_errors(self):
        """Test that config loader uses unified error system."""
        from vibey.config.loader import (
            ConfigLoadError,
            ConfigNotFoundError as LoaderConfigNotFoundError,
            ConfigValidationError as LoaderConfigValidationError,
        )
        from vibey.common import ConfigurationError

        # Config loader errors should be unified errors
        error1 = LoaderConfigNotFoundError(searched_paths=["/path"])
        assert error1.context.code == "CONFIG_NOT_FOUND"
        assert isinstance(error1, ConfigurationError)

        error2 = LoaderConfigValidationError(
            validation_errors=["test"],
            config_file="/path/config.yaml"
        )
        assert error2.context.code == "CONFIG_VALIDATION_FAILED"
        assert isinstance(error2, ConfigurationError)


class TestErrorHandling:
    """Test error catching and handling."""

    def test_catch_specific_error(self):
        """Test catching specific error types."""
        with pytest.raises(RoadmapNotFoundError) as exc_info:
            raise RoadmapNotFoundError(searched_dir="/test")

        error = exc_info.value
        assert error.context.code == "ROADMAP_NOT_FOUND"

    def test_catch_base_error(self):
        """Test catching base VibeyError."""
        with pytest.raises(VibeyError) as exc_info:
            raise TrackNotFoundError("backend")

        error = exc_info.value
        assert error.context.category == ErrorCategory.ROADMAP

    def test_error_inheritance(self):
        """Test error inheritance hierarchy."""
        error = ConfigNotFoundError(searched_paths=["/path"])

        assert isinstance(error, VibeyError)
        assert isinstance(error, Exception)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
