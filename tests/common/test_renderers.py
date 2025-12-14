"""
Comprehensive tests for vibey.common.renderers module.

Tests all renderer types and their output formatting.
Focuses on achieving 100% coverage of renderers.py.
"""

import json
import pytest

from vibey.common.errors import (
    VibeyError,
    ErrorCategory,
    ErrorSeverity,
    RoadmapNotFoundError,
    TrackNotFoundError,
    ConfigNotFoundError,
    ValidationError,
    DependencyBlockedError,
)
from vibey.common.renderers import (
    ANSIColors,
    colorize,
    bold,
    CLIErrorRenderer,
    MCPErrorRenderer,
    PlainTextRenderer,
    LogErrorRenderer,
)


class TestANSIColors:
    """Test ANSI color constants."""

    def test_reset_code(self):
        """Test reset code is defined."""
        assert ANSIColors.RESET == "\033[0m"

    def test_bold_code(self):
        """Test bold code is defined."""
        assert ANSIColors.BOLD == "\033[1m"

    def test_foreground_colors(self):
        """Test foreground color codes."""
        assert ANSIColors.RED == "\033[91m"
        assert ANSIColors.YELLOW == "\033[93m"
        assert ANSIColors.BLUE == "\033[94m"
        assert ANSIColors.CYAN == "\033[96m"
        assert ANSIColors.GRAY == "\033[90m"

    def test_background_colors(self):
        """Test background color codes."""
        assert ANSIColors.BG_RED == "\033[101m"
        assert ANSIColors.BG_YELLOW == "\033[103m"


class TestColorFunctions:
    """Test color helper functions."""

    def test_colorize(self):
        """Test colorize applies color and reset."""
        result = colorize("test", ANSIColors.RED)
        assert result == "\033[91mtest\033[0m"

    def test_colorize_with_different_colors(self):
        """Test colorize with various colors."""
        assert "\033[93m" in colorize("warn", ANSIColors.YELLOW)
        assert "\033[94m" in colorize("info", ANSIColors.BLUE)

    def test_bold(self):
        """Test bold applies bold and reset."""
        result = bold("important")
        assert result == "\033[1mimportant\033[0m"


class TestCLIErrorRenderer:
    """Test CLI error renderer."""

    def test_render_with_colors_enabled(self):
        """Test rendering with ANSI colors."""
        error = RoadmapNotFoundError(searched_dir="/project")
        renderer = CLIErrorRenderer(use_colors=True)
        output = renderer.render(error)

        assert "ROADMAP_NOT_FOUND" in output
        assert "/project" in output
        assert "\033[" in output  # Contains ANSI codes

    def test_render_with_colors_disabled(self):
        """Test rendering without ANSI colors."""
        error = RoadmapNotFoundError(searched_dir="/project")
        renderer = CLIErrorRenderer(use_colors=False)
        output = renderer.render(error)

        assert "ROADMAP_NOT_FOUND" in output
        assert "/project" in output
        assert "\033[" not in output  # No ANSI codes

    def test_render_includes_suggestions(self):
        """Test suggestions are included in output."""
        error = ConfigNotFoundError(searched_paths=["/path1", "/path2"])
        renderer = CLIErrorRenderer(use_colors=False)
        output = renderer.render(error)

        assert "Suggestions:" in output
        assert "vibey init" in output

    def test_render_includes_hint(self):
        """Test hint is included in output."""
        error = RoadmapNotFoundError(searched_dir="/test")
        renderer = CLIErrorRenderer(use_colors=False)
        output = renderer.render(error)

        assert "Hint:" in output

    def test_render_includes_fix_command(self):
        """Test fix command is included in output."""
        error = ConfigNotFoundError(searched_paths=["/path"])
        renderer = CLIErrorRenderer(use_colors=False)
        output = renderer.render(error)

        assert "Quick fix:" in output
        assert "vibey init" in output

    def test_render_includes_related_docs(self):
        """Test related docs are included in output."""
        error = ConfigNotFoundError(searched_paths=["/path"])
        renderer = CLIErrorRenderer(use_colors=False)
        output = renderer.render(error)

        assert "Documentation:" in output
        assert "docs/getting-started/QUICK_START.md" in output

    def test_render_related_docs_with_colors(self):
        """Test related docs rendering with colors."""
        error = ConfigNotFoundError(searched_paths=["/path"])
        renderer = CLIErrorRenderer(use_colors=True)
        output = renderer.render(error)

        assert "QUICK_START.md" in output
        # Should have gray color for docs
        assert "\033[90m" in output  # Gray color code

    def test_render_multiple_errors(self):
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
        assert "Error 1 of 2" in output
        assert "Error 2 of 2" in output

    def test_render_multiple_empty_list(self):
        """Test rendering empty error list returns empty string."""
        renderer = CLIErrorRenderer(use_colors=False)
        output = renderer.render_multiple([])
        assert output == ""

    def test_render_multiple_with_colors(self):
        """Test rendering multiple errors with colors enabled."""
        errors = [
            RoadmapNotFoundError(searched_dir="/test1"),
            TrackNotFoundError("backend"),
        ]
        renderer = CLIErrorRenderer(use_colors=True)
        output = renderer.render_multiple(errors)

        assert "2 error(s) occurred" in output
        assert "\033[1m" in output  # Bold code for header

    def test_render_multiple_single_error(self):
        """Test rendering single error in list."""
        errors = [RoadmapNotFoundError(searched_dir="/test")]
        renderer = CLIErrorRenderer(use_colors=False)
        output = renderer.render_multiple(errors)

        assert "1 error(s) occurred" in output
        # Should not have separator after single error
        assert output.count("─" * 60) == 0

    def test_severity_markers_without_colors(self):
        """Test severity markers without colors."""
        renderer = CLIErrorRenderer(use_colors=False)

        # Create errors with different severities
        error = VibeyError(
            message="Error message",
            code="TEST",
            severity=ErrorSeverity.ERROR,
        )
        output = renderer.render(error)
        assert "❌" in output

    def test_warning_severity_marker(self):
        """Test warning severity marker."""
        renderer = CLIErrorRenderer(use_colors=False)
        error = VibeyError(
            message="Warning message",
            code="WARN",
            severity=ErrorSeverity.WARNING,
        )
        output = renderer.render(error)
        assert "⚠️" in output

    def test_info_severity_marker(self):
        """Test info severity marker."""
        renderer = CLIErrorRenderer(use_colors=False)
        error = VibeyError(
            message="Info message",
            code="INFO",
            severity=ErrorSeverity.INFO,
        )
        output = renderer.render(error)
        assert "ℹ️" in output

    def test_severity_markers_with_colors(self):
        """Test colored severity markers."""
        renderer = CLIErrorRenderer(use_colors=True)

        # Error should be red
        error = VibeyError(message="Error", code="ERR", severity=ErrorSeverity.ERROR)
        output = renderer.render(error)
        assert "\033[91m" in output  # Red

        # Warning should be yellow
        warn = VibeyError(message="Warn", code="WARN", severity=ErrorSeverity.WARNING)
        output = renderer.render(warn)
        assert "\033[93m" in output  # Yellow

        # Info should be blue
        info = VibeyError(message="Info", code="INFO", severity=ErrorSeverity.INFO)
        output = renderer.render(info)
        assert "\033[94m" in output  # Blue


class TestMCPErrorRenderer:
    """Test MCP JSON error renderer."""

    def test_render_returns_dict(self):
        """Test render returns dictionary."""
        error = TrackNotFoundError("backend")
        renderer = MCPErrorRenderer()
        output = renderer.render(error)

        assert isinstance(output, dict)
        assert "error" in output
        assert "details" in output
        assert "metadata" in output

    def test_render_error_fields(self):
        """Test error fields in output."""
        error = TrackNotFoundError("backend", available_tracks=["frontend"])
        renderer = MCPErrorRenderer()
        output = renderer.render(error)

        assert output["error"]["code"] == "TRACK_NOT_FOUND"
        assert output["error"]["message"] == "Track 'backend' not found"
        assert output["error"]["severity"] == "error"
        assert output["error"]["category"] == "roadmap"

    def test_render_details_fields(self):
        """Test details fields in output."""
        error = ConfigNotFoundError(searched_paths=["/path"])
        renderer = MCPErrorRenderer()
        output = renderer.render(error)

        assert "suggestions" in output["details"]
        assert "hint" in output["details"]
        assert "fix_command" in output["details"]
        assert "related_docs" in output["details"]

    def test_to_json(self):
        """Test JSON string serialization."""
        error = ConfigNotFoundError(searched_paths=["/path"])
        renderer = MCPErrorRenderer()
        json_str = renderer.to_json(error)

        # Should be valid JSON
        data = json.loads(json_str)
        assert data["error"]["code"] == "CONFIG_NOT_FOUND"

    def test_to_json_with_indent(self):
        """Test JSON with custom indentation."""
        error = RoadmapNotFoundError(searched_dir="/test")
        renderer = MCPErrorRenderer()

        json_4 = renderer.to_json(error, indent=4)
        # 4-space indent should produce more whitespace than 2-space
        json_2 = renderer.to_json(error, indent=2)
        assert len(json_4) > len(json_2)

    def test_render_multiple(self):
        """Test rendering multiple errors."""
        errors = [
            ConfigNotFoundError(searched_paths=["/path1"]),
            ValidationError("sprint", "sprint-1", ["Missing field"]),
        ]
        renderer = MCPErrorRenderer()
        output = renderer.render_multiple(errors)

        assert output["count"] == 2
        assert len(output["errors"]) == 2
        assert output["errors"][0]["error"]["code"] == "CONFIG_NOT_FOUND"
        assert output["errors"][1]["error"]["code"] == "VALIDATION_FAILED"

    def test_to_json_multiple(self):
        """Test JSON serialization of multiple errors."""
        errors = [
            RoadmapNotFoundError(searched_dir="/test1"),
            TrackNotFoundError("backend"),
        ]
        renderer = MCPErrorRenderer()
        json_str = renderer.to_json_multiple(errors)

        data = json.loads(json_str)
        assert data["count"] == 2
        assert len(data["errors"]) == 2

    def test_to_json_multiple_with_indent(self):
        """Test JSON multiple with custom indentation."""
        errors = [RoadmapNotFoundError(searched_dir="/test")]
        renderer = MCPErrorRenderer()

        json_4 = renderer.to_json_multiple(errors, indent=4)
        json_0 = renderer.to_json_multiple(errors, indent=0)
        # More indent = more characters
        assert len(json_4) > len(json_0)


class TestPlainTextRenderer:
    """Test plain text renderer (no colors)."""

    def test_inherits_from_cli_renderer(self):
        """Test PlainTextRenderer inherits from CLIErrorRenderer."""
        renderer = PlainTextRenderer()
        assert isinstance(renderer, CLIErrorRenderer)

    def test_colors_disabled_by_default(self):
        """Test colors are disabled."""
        renderer = PlainTextRenderer()
        assert renderer.use_colors is False

    def test_render_has_no_ansi_codes(self):
        """Test output has no ANSI color codes."""
        error = RoadmapNotFoundError(searched_dir="/test")
        renderer = PlainTextRenderer()
        output = renderer.render(error)

        assert "\033[" not in output


class TestLogErrorRenderer:
    """Test structured logging renderer."""

    def test_render_returns_dict(self):
        """Test render returns dictionary."""
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

        assert isinstance(output, dict)
        assert "level" in output
        assert "error_code" in output
        assert "error_category" in output
        assert "message" in output

    def test_render_log_level_mapping(self):
        """Test severity to log level mapping."""
        renderer = LogErrorRenderer()

        # ERROR -> ERROR
        error = VibeyError(message="Err", code="E", severity=ErrorSeverity.ERROR)
        assert renderer.render(error)["level"] == "ERROR"

        # WARNING -> WARNING
        warn = VibeyError(message="Warn", code="W", severity=ErrorSeverity.WARNING)
        assert renderer.render(warn)["level"] == "WARNING"

        # INFO -> INFO
        info = VibeyError(message="Info", code="I", severity=ErrorSeverity.INFO)
        assert renderer.render(info)["level"] == "INFO"

    def test_render_includes_all_fields(self):
        """Test all context fields are included."""
        error = ConfigNotFoundError(searched_paths=["/path"])
        renderer = LogErrorRenderer()
        output = renderer.render(error)

        assert output["error_code"] == "CONFIG_NOT_FOUND"
        assert output["error_category"] == "configuration"
        assert "not found" in output["message"].lower()
        assert "suggestions" in output
        assert "hint" in output
        assert "fix_command" in output
        assert "related_docs" in output
        assert "metadata" in output

    def test_render_multiple(self):
        """Test rendering multiple errors for logging."""
        errors = [
            ConfigNotFoundError(searched_paths=["/path1"]),
            ValidationError("sprint", "sprint-1", ["Missing field"]),
        ]
        renderer = LogErrorRenderer()
        output = renderer.render_multiple(errors)

        assert isinstance(output, list)
        assert len(output) == 2
        assert all("level" in entry for entry in output)
        assert all("error_code" in entry for entry in output)

    def test_render_multiple_empty_list(self):
        """Test rendering empty error list."""
        renderer = LogErrorRenderer()
        output = renderer.render_multiple([])
        assert output == []
