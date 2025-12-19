"""
Standardized CLI error handling for Vibey Framework.

Provides consistent error handling patterns for CLI commands including:
- @handle_cli_errors decorator for Click commands
- error_context() context manager for scoped error handling
- Consistent exit codes
- Helper functions for CLI output

Exit Codes:
    0: Success
    1: General error
    2: Configuration error
    3: Validation error
    4: Not found error
    5: Blocked/dependency error

Example:
    from vibey.cli.error_handler import handle_cli_errors, error_context

    @click.command()
    @handle_cli_errors
    def my_command():
        with error_context("loading roadmap"):
            # operations that might fail
            pass

    # Or manual error handling:
    from vibey.cli.error_handler import cli_error, cli_success

    cli_success("Task completed successfully")
    cli_error("Something went wrong", exit_code=1)
"""

import sys
import functools
from contextlib import contextmanager
from typing import Optional, Callable, Any, TypeVar, cast

from vibey.common.errors import (
    VibeyError,
    ErrorCategory,
    ErrorSeverity,
    ConfigurationError,
    RoadmapError,
    ValidationError as VibeyValidationError,
    TaskNotFoundError,
    SprintNotFoundError,
    TrackNotFoundError,
    DependencyBlockedError,
)
from vibey.common.renderers import CLIErrorRenderer

# Type variable for decorated functions
F = TypeVar('F', bound=Callable[..., Any])


# ============================================================================
# Exit Codes
# ============================================================================

class ExitCode:
    """Standard CLI exit codes."""
    SUCCESS = 0
    GENERAL_ERROR = 1
    CONFIG_ERROR = 2
    VALIDATION_ERROR = 3
    NOT_FOUND_ERROR = 4
    BLOCKED_ERROR = 5


def get_exit_code(error: VibeyError) -> int:
    """
    Determine appropriate exit code based on error type.

    Args:
        error: VibeyError instance

    Returns:
        Appropriate exit code for the error type
    """
    category = error.context.category

    if category == ErrorCategory.CONFIGURATION:
        return ExitCode.CONFIG_ERROR
    elif category == ErrorCategory.VALIDATION:
        return ExitCode.VALIDATION_ERROR
    elif category == ErrorCategory.ROADMAP:
        # Check for not found errors
        if isinstance(error, (TaskNotFoundError, SprintNotFoundError, TrackNotFoundError)):
            return ExitCode.NOT_FOUND_ERROR
        return ExitCode.GENERAL_ERROR
    elif category == ErrorCategory.DEPENDENCY:
        return ExitCode.BLOCKED_ERROR
    else:
        return ExitCode.GENERAL_ERROR


# ============================================================================
# CLI Error Decorator
# ============================================================================

def handle_cli_errors(func: F) -> F:
    """
    Decorator for CLI commands that standardizes error handling.

    Catches VibeyError exceptions and renders them consistently,
    then exits with appropriate exit codes.

    Example:
        @click.command()
        @handle_cli_errors
        def my_command():
            # If VibeyError is raised, it will be handled consistently
            pass
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except VibeyError as e:
            renderer = CLIErrorRenderer(use_colors=True)
            print(renderer.render(e), file=sys.stderr)
            sys.exit(get_exit_code(e))
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.", file=sys.stderr)
            sys.exit(130)  # Standard exit code for Ctrl+C
        except Exception as e:
            # Wrap unexpected exceptions in VibeyError
            wrapped = VibeyError(
                message=f"Unexpected error: {str(e)}",
                code="UNEXPECTED_ERROR",
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.ERROR,
                suggestions=[
                    "Check the command syntax",
                    "Verify system requirements",
                    "Report this issue if it persists",
                ],
                hint="This may be a bug - please report it",
            )
            renderer = CLIErrorRenderer(use_colors=True)
            print(renderer.render(wrapped), file=sys.stderr)
            sys.exit(ExitCode.GENERAL_ERROR)

    return cast(F, wrapper)


# ============================================================================
# Error Context Manager
# ============================================================================

@contextmanager
def error_context(operation: str, raise_on_error: bool = True):
    """
    Context manager for scoped error handling with context.

    Provides additional context when errors occur within the scope.
    Useful for wrapping operations with descriptive error messages.

    Args:
        operation: Description of the operation being performed
        raise_on_error: If True (default), re-raises errors after logging

    Example:
        with error_context("loading configuration"):
            config = load_config()  # If this fails, error includes context

        # Or suppress errors:
        with error_context("optional operation", raise_on_error=False):
            do_optional_thing()
    """
    try:
        yield
    except VibeyError:
        # VibeyError already has rich context, just re-raise
        if raise_on_error:
            raise
    except Exception as e:
        # Wrap non-Vibey exceptions with context
        wrapped = VibeyError(
            message=f"Error while {operation}: {str(e)}",
            code="OPERATION_FAILED",
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.ERROR,
            suggestions=[
                f"Check prerequisites for {operation}",
                "Verify input parameters",
            ],
            hint=f"The operation '{operation}' failed unexpectedly",
            metadata={"operation": operation, "original_error": str(e)},
        )
        if raise_on_error:
            raise wrapped from e


# ============================================================================
# CLI Output Helpers
# ============================================================================

def cli_error(
    message: str,
    exit_code: int = ExitCode.GENERAL_ERROR,
    suggestions: Optional[list] = None,
    hint: Optional[str] = None,
    fix_command: Optional[str] = None,
) -> None:
    """
    Display a formatted error message and exit.

    Args:
        message: Error message to display
        exit_code: Exit code (default: 1)
        suggestions: Optional list of suggestions
        hint: Optional hint text
        fix_command: Optional command to fix the issue
    """
    error = VibeyError(
        message=message,
        code="CLI_ERROR",
        category=ErrorCategory.UNKNOWN,
        severity=ErrorSeverity.ERROR,
        suggestions=suggestions,
        hint=hint,
        fix_command=fix_command,
    )
    renderer = CLIErrorRenderer(use_colors=True)
    print(renderer.render(error), file=sys.stderr)
    sys.exit(exit_code)


def cli_warning(
    message: str,
    suggestions: Optional[list] = None,
    hint: Optional[str] = None,
) -> None:
    """
    Display a formatted warning message (does not exit).

    Args:
        message: Warning message to display
        suggestions: Optional list of suggestions
        hint: Optional hint text
    """
    error = VibeyError(
        message=message,
        code="CLI_WARNING",
        category=ErrorCategory.UNKNOWN,
        severity=ErrorSeverity.WARNING,
        suggestions=suggestions,
        hint=hint,
    )
    renderer = CLIErrorRenderer(use_colors=True)
    print(renderer.render(error), file=sys.stderr)


def cli_success(message: str) -> None:
    """
    Display a success message.

    Args:
        message: Success message to display
    """
    print(f"\n{message}\n")


def format_cli_error(error: VibeyError, use_colors: bool = True) -> str:
    """
    Format a VibeyError for CLI output without exiting.

    Args:
        error: VibeyError instance to format
        use_colors: Whether to use ANSI colors

    Returns:
        Formatted error string
    """
    renderer = CLIErrorRenderer(use_colors=use_colors)
    return renderer.render(error)


# ============================================================================
# Quick Error Factories
# ============================================================================

def item_not_found_error(item_id: str, item_type: Optional[str] = None) -> VibeyError:
    """
    Create a not-found error for a roadmap item.

    Args:
        item_id: ID of the item that wasn't found
        item_type: Optional type of item (task, sprint, track)

    Returns:
        VibeyError configured for not-found scenario
    """
    type_str = f"{item_type} " if item_type else "item "
    return VibeyError(
        message=f"Cannot find {type_str}with ID: {item_id}",
        code="ITEM_NOT_FOUND",
        category=ErrorCategory.ROADMAP,
        severity=ErrorSeverity.ERROR,
        suggestions=[
            f"Check that the ID '{item_id}' is correct",
            "List available items: vibey roadmap list tracks",
            "Verify the roadmap is initialized: vibey roadmap status",
        ],
        hint="IDs are case-sensitive ULIDs",
        metadata={"item_id": item_id, "item_type": item_type},
    )


def invalid_item_type_error(item_id: str, item_type: str, operation: str) -> VibeyError:
    """
    Create an error for invalid item type for an operation.

    Args:
        item_id: ID of the item
        item_type: Type of the item
        operation: Operation that was attempted

    Returns:
        VibeyError configured for invalid type scenario
    """
    return VibeyError(
        message=f"Cannot {operation} a {item_type}. Only tasks and sprints can be {operation}ed.",
        code="INVALID_ITEM_TYPE",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        suggestions=[
            f"Use vibey roadmap show {item_id} to see item details",
            f"To {operation} tasks, use: vibey roadmap {operation} <task-id>",
            f"To {operation} sprints, use: vibey roadmap {operation} <sprint-id>",
        ],
        hint=f"Tracks cannot be directly {operation}ed",
        metadata={"item_id": item_id, "item_type": item_type, "operation": operation},
    )


def roadmap_not_found_error() -> VibeyError:
    """
    Create a roadmap-not-found error.

    Returns:
        VibeyError configured for missing roadmap scenario
    """
    return VibeyError(
        message="No roadmap found. Run 'vibey roadmap init' first.",
        code="ROADMAP_NOT_FOUND",
        category=ErrorCategory.ROADMAP,
        severity=ErrorSeverity.ERROR,
        suggestions=[
            "Initialize a new roadmap: vibey roadmap init",
            "Check you're in the correct directory",
            "Verify .vibey/roadmap/ directory exists",
        ],
        hint="Roadmap systems require initialization before use",
        fix_command="vibey roadmap init",
    )
