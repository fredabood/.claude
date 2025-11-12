"""
Error renderers for different platforms.

Transforms VibeyError instances into platform-specific output:
- CLIErrorRenderer: Text output for terminal (ANSI colors, formatting)
- MCPErrorRenderer: JSON output for MCP protocol
- PlainTextRenderer: Plain text without colors (for logs, files)

Example:
    from vibey.common.errors import RoadmapNotFoundError
    from vibey.common.renderers import CLIErrorRenderer

    try:
        load_roadmap()
    except RoadmapNotFoundError as e:
        renderer = CLIErrorRenderer()
        print(renderer.render(e))
"""

import json
from typing import Any, Dict, List
from vibey.common.errors import VibeyError, ErrorRenderer, ErrorSeverity


# ============================================================================
# ANSI Color Codes (for CLI rendering)
# ============================================================================

class ANSIColors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground colors
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"

    # Background colors
    BG_RED = "\033[101m"
    BG_YELLOW = "\033[103m"
    BG_BLUE = "\033[104m"


def colorize(text: str, color: str) -> str:
    """Apply ANSI color to text."""
    return f"{color}{text}{ANSIColors.RESET}"


def bold(text: str) -> str:
    """Make text bold."""
    return f"{ANSIColors.BOLD}{text}{ANSIColors.RESET}"


# ============================================================================
# CLI Error Renderer
# ============================================================================

class CLIErrorRenderer(ErrorRenderer):
    """
    Renders errors for CLI output with ANSI colors and formatting.

    Features:
    - Color-coded severity (red for errors, yellow for warnings)
    - Bold headings
    - Bulleted suggestions
    - Hints and fix commands
    - Clean, readable formatting
    """

    def __init__(self, use_colors: bool = True):
        """
        Initialize CLI renderer.

        Args:
            use_colors: Enable ANSI colors (default: True)
        """
        self.use_colors = use_colors

    def render(self, error: VibeyError) -> str:
        """
        Render a single error for CLI output.

        Args:
            error: VibeyError instance to render

        Returns:
            Formatted string ready for terminal output
        """
        ctx = error.context
        lines = []

        # Error header with severity and code
        severity_marker = self._get_severity_marker(ctx.severity)
        if self.use_colors:
            header = f"{severity_marker} {bold(ctx.message)}"
        else:
            header = f"{severity_marker} {ctx.message}"
        lines.append(header)
        lines.append("")

        # Error code and category
        if self.use_colors:
            lines.append(colorize(f"[{ctx.code}]", ANSIColors.GRAY) + f" ({ctx.category.value})")
        else:
            lines.append(f"[{ctx.code}] ({ctx.category.value})")
        lines.append("")

        # Suggestions
        if ctx.suggestions:
            if self.use_colors:
                lines.append(bold("Suggestions:"))
            else:
                lines.append("Suggestions:")
            for suggestion in ctx.suggestions:
                lines.append(f"  • {suggestion}")
            lines.append("")

        # Hint
        if ctx.hint:
            if self.use_colors:
                lines.append(colorize(f"💡 {ctx.hint}", ANSIColors.CYAN))
            else:
                lines.append(f"Hint: {ctx.hint}")
            lines.append("")

        # Fix command
        if ctx.fix_command:
            if self.use_colors:
                lines.append(bold("Quick fix:"))
                lines.append(f"  {colorize(ctx.fix_command, ANSIColors.BLUE)}")
            else:
                lines.append("Quick fix:")
                lines.append(f"  {ctx.fix_command}")
            lines.append("")

        # Related documentation
        if ctx.related_docs:
            if self.use_colors:
                lines.append(colorize(f"📚 Documentation: {ctx.related_docs}", ANSIColors.GRAY))
            else:
                lines.append(f"Documentation: {ctx.related_docs}")
            lines.append("")

        return "\n".join(lines)

    def render_multiple(self, errors: List[VibeyError]) -> str:
        """
        Render multiple errors for CLI output.

        Args:
            errors: List of VibeyError instances

        Returns:
            Formatted string with all errors
        """
        if not errors:
            return ""

        lines = []
        if self.use_colors:
            lines.append(bold(f"❌ {len(errors)} error(s) occurred:"))
        else:
            lines.append(f"❌ {len(errors)} error(s) occurred:")
        lines.append("")

        for i, error in enumerate(errors, 1):
            lines.append(f"--- Error {i} of {len(errors)} ---")
            lines.append("")
            lines.append(self.render(error))
            if i < len(errors):
                lines.append("─" * 60)
                lines.append("")

        return "\n".join(lines)

    def _get_severity_marker(self, severity: ErrorSeverity) -> str:
        """Get severity marker with optional coloring."""
        if not self.use_colors:
            return {
                ErrorSeverity.ERROR: "❌",
                ErrorSeverity.WARNING: "⚠️",
                ErrorSeverity.INFO: "ℹ️",
            }[severity]

        return {
            ErrorSeverity.ERROR: colorize("❌ ERROR", ANSIColors.RED),
            ErrorSeverity.WARNING: colorize("⚠️  WARNING", ANSIColors.YELLOW),
            ErrorSeverity.INFO: colorize("ℹ️  INFO", ANSIColors.BLUE),
        }[severity]


# ============================================================================
# MCP Error Renderer
# ============================================================================

class MCPErrorRenderer(ErrorRenderer):
    """
    Renders errors for MCP protocol (JSON format).

    MCP error format follows the protocol specification:
    - Standard error codes
    - Structured error data
    - Metadata for programmatic handling

    This renderer prepares errors for the future MCP server implementation.
    """

    def render(self, error: VibeyError) -> Dict[str, Any]:
        """
        Render error as JSON-compatible dictionary for MCP.

        Args:
            error: VibeyError instance to render

        Returns:
            Dictionary ready for JSON serialization
        """
        ctx = error.context
        return {
            "error": {
                "code": ctx.code,
                "message": ctx.message,
                "severity": ctx.severity.value,
                "category": ctx.category.value,
            },
            "details": {
                "suggestions": ctx.suggestions,
                "hint": ctx.hint,
                "fix_command": ctx.fix_command,
                "related_docs": ctx.related_docs,
            },
            "metadata": ctx.metadata,
        }

    def render_multiple(self, errors: List[VibeyError]) -> Dict[str, Any]:
        """
        Render multiple errors for MCP.

        Args:
            errors: List of VibeyError instances

        Returns:
            Dictionary with all errors
        """
        return {
            "errors": [self.render(error) for error in errors],
            "count": len(errors),
        }

    def to_json(self, error: VibeyError, indent: int = 2) -> str:
        """
        Render error as JSON string.

        Args:
            error: VibeyError instance to render
            indent: JSON indentation (default: 2)

        Returns:
            JSON string
        """
        return json.dumps(self.render(error), indent=indent)

    def to_json_multiple(self, errors: List[VibeyError], indent: int = 2) -> str:
        """
        Render multiple errors as JSON string.

        Args:
            errors: List of VibeyError instances
            indent: JSON indentation (default: 2)

        Returns:
            JSON string
        """
        return json.dumps(self.render_multiple(errors), indent=indent)


# ============================================================================
# Plain Text Renderer
# ============================================================================

class PlainTextRenderer(CLIErrorRenderer):
    """
    Renders errors as plain text without ANSI colors.

    Useful for:
    - Log files
    - CI/CD output
    - Environments without color support
    - Documentation generation
    """

    def __init__(self):
        """Initialize plain text renderer (colors disabled)."""
        super().__init__(use_colors=False)


# ============================================================================
# Logging Renderer
# ============================================================================

class LogErrorRenderer(ErrorRenderer):
    """
    Renders errors for structured logging.

    Outputs errors in a format suitable for logging systems:
    - Structured fields
    - Machine-readable
    - Optimized for log aggregation
    """

    def render(self, error: VibeyError) -> Dict[str, Any]:
        """
        Render error for logging.

        Args:
            error: VibeyError instance to render

        Returns:
            Dictionary with structured log fields
        """
        ctx = error.context
        return {
            "level": self._severity_to_log_level(ctx.severity),
            "error_code": ctx.code,
            "error_category": ctx.category.value,
            "message": ctx.message,
            "suggestions": ctx.suggestions,
            "hint": ctx.hint,
            "fix_command": ctx.fix_command,
            "related_docs": ctx.related_docs,
            "metadata": ctx.metadata,
        }

    def render_multiple(self, errors: List[VibeyError]) -> List[Dict[str, Any]]:
        """
        Render multiple errors for logging.

        Args:
            errors: List of VibeyError instances

        Returns:
            List of structured log entries
        """
        return [self.render(error) for error in errors]

    def _severity_to_log_level(self, severity: ErrorSeverity) -> str:
        """Convert ErrorSeverity to standard log level."""
        return {
            ErrorSeverity.ERROR: "ERROR",
            ErrorSeverity.WARNING: "WARNING",
            ErrorSeverity.INFO: "INFO",
        }[severity]
