"""
Unified error handling for Vibey Framework.

Provides platform-agnostic error definitions that work across:
- CLI (text-based output)
- MCP Server (JSON-based responses)
- Direct Python API usage

Error Architecture:
1. VibeyError base class - All errors inherit from this
2. Error categories - Logical grouping of related errors
3. Error context - Rich metadata (codes, suggestions, fix hints)
4. Renderer pattern - Platform-specific error formatting

Example:
    from vibey.common.errors import RoadmapNotFoundError
    from vibey.common.renderers import CLIErrorRenderer

    try:
        load_roadmap()
    except RoadmapNotFoundError as e:
        renderer = CLIErrorRenderer()
        print(renderer.render(e))
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    ERROR = "error"         # Operation failed, user action required
    WARNING = "warning"     # Operation succeeded with caveats
    INFO = "info"          # Informational message


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    CONFIGURATION = "configuration"      # Config loading, validation
    ROADMAP = "roadmap"                 # Roadmap operations
    VALIDATION = "validation"           # Data validation
    DEPENDENCY = "dependency"           # Dependency management
    FILE_SYSTEM = "file_system"         # File operations
    STATE = "state"                     # Invalid state transitions
    CONCURRENCY = "concurrency"         # Concurrent modifications
    NETWORK = "network"                 # Network operations
    AUTHENTICATION = "authentication"   # Auth/permissions
    UNKNOWN = "unknown"                 # Uncategorized errors


@dataclass
class ErrorContext:
    """
    Rich context for errors.

    Provides all information needed to:
    1. Display helpful error messages to users
    2. Log errors for debugging
    3. Programmatically handle errors
    4. Track error patterns
    """
    code: str                           # Error code (e.g., "ROADMAP_NOT_FOUND")
    message: str                        # Human-readable error message
    category: ErrorCategory             # Error category
    severity: ErrorSeverity = ErrorSeverity.ERROR
    suggestions: List[str] = field(default_factory=list)  # Action suggestions
    hint: Optional[str] = None          # Additional guidance
    fix_command: Optional[str] = None   # Command to fix the issue
    related_docs: Optional[str] = None  # Link to relevant documentation
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional context

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "code": self.code,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "suggestions": self.suggestions,
            "hint": self.hint,
            "fix_command": self.fix_command,
            "related_docs": self.related_docs,
            "metadata": self.metadata,
        }


class VibeyError(Exception):
    """
    Base exception for all Vibey errors.

    All Vibey exceptions should inherit from this class to enable:
    1. Consistent error handling
    2. Rich error context
    3. Platform-specific rendering
    4. Error tracking and analytics
    """

    def __init__(
        self,
        message: str,
        code: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        suggestions: Optional[List[str]] = None,
        hint: Optional[str] = None,
        fix_command: Optional[str] = None,
        related_docs: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Vibey error.

        Args:
            message: Human-readable error message
            code: Error code (e.g., "ROADMAP_NOT_FOUND")
            category: Error category
            severity: Error severity level
            suggestions: List of action suggestions
            hint: Additional guidance
            fix_command: Command to fix the issue
            related_docs: Link to relevant documentation
            metadata: Additional context dictionary
        """
        super().__init__(message)
        self.context = ErrorContext(
            code=code,
            message=message,
            category=category,
            severity=severity,
            suggestions=suggestions or [],
            hint=hint,
            fix_command=fix_command,
            related_docs=related_docs,
            metadata=metadata or {},
        )

    def __str__(self) -> str:
        """Default string representation (just the message)."""
        return self.context.message

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization (e.g., for MCP)."""
        return self.context.to_dict()


# ============================================================================
# Configuration Errors
# ============================================================================

class ConfigurationError(VibeyError):
    """Base class for configuration errors."""

    def __init__(self, message: str, code: str, **kwargs):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.CONFIGURATION,
            **kwargs
        )


class ConfigNotFoundError(ConfigurationError):
    """Configuration files not found."""

    def __init__(self, searched_paths: List[str]):
        paths_str = "\n  ".join(f"• {p}" for p in searched_paths)
        super().__init__(
            message=f"Configuration files not found. Searched paths:\n  {paths_str}",
            code="CONFIG_NOT_FOUND",
            suggestions=[
                "Initialize Vibey: vibey init",
                "Check you're in the correct directory",
                "Verify .vibey/ directory exists",
            ],
            hint="Vibey requires initialization before use",
            fix_command="vibey init",
            related_docs="docs/getting-started/QUICK_START.md",
            metadata={"searched_paths": searched_paths},
        )


class ConfigValidationError(ConfigurationError):
    """Configuration validation failed."""

    def __init__(self, validation_errors: List[str], config_file: Optional[str] = None):
        errors_str = "\n  ".join(f"• {e}" for e in validation_errors)
        message = f"Configuration validation failed:\n  {errors_str}"
        if config_file:
            message = f"Configuration validation failed in {config_file}:\n  {errors_str}"

        super().__init__(
            message=message,
            code="CONFIG_VALIDATION_FAILED",
            suggestions=[
                "Fix validation errors in config file",
                "Check config schema: vibey config validate",
                "Reset to defaults: vibey config reset",
            ],
            hint="All config values must pass validation",
            fix_command="vibey config validate",
            metadata={
                "validation_errors": validation_errors,
                "config_file": config_file,
            },
        )


# ============================================================================
# Roadmap Errors
# ============================================================================

class RoadmapError(VibeyError):
    """Base class for roadmap errors."""

    def __init__(self, message: str, code: str, **kwargs):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.ROADMAP,
            **kwargs
        )


class RoadmapNotFoundError(RoadmapError):
    """Roadmap not found."""

    def __init__(self, searched_dir: str):
        super().__init__(
            message=f"Roadmap not found in {searched_dir}",
            code="ROADMAP_NOT_FOUND",
            suggestions=[
                "Initialize roadmap: vibey roadmap init",
                "Check you're in the correct directory",
                "Verify .vibey/roadmap/ directory exists",
            ],
            hint="Roadmap systems require initialization",
            fix_command="vibey roadmap init",
            metadata={"searched_dir": searched_dir},
        )


class TrackNotFoundError(RoadmapError):
    """Track not found."""

    def __init__(self, track_id: str, available_tracks: Optional[List[str]] = None):
        message = f"Track '{track_id}' not found"
        suggestions = [
            "List all tracks: vibey roadmap list-tracks",
            "Check track ID spelling (case-sensitive, kebab-case)",
        ]
        if available_tracks:
            suggestions.append(f"Available tracks: {', '.join(available_tracks)}")

        super().__init__(
            message=message,
            code="TRACK_NOT_FOUND",
            suggestions=suggestions,
            hint="Track IDs use kebab-case (lowercase-with-hyphens)",
            metadata={
                "track_id": track_id,
                "available_tracks": available_tracks,
            },
        )


class SprintNotFoundError(RoadmapError):
    """Sprint not found."""

    def __init__(self, sprint_id: str, track_id: Optional[str] = None):
        message = f"Sprint '{sprint_id}' not found"
        suggestions = [
            "List all sprints: vibey roadmap list-sprints",
            "Check sprint ID spelling",
        ]
        if track_id:
            suggestions.append(f"List sprints in track: vibey roadmap show {track_id}")

        super().__init__(
            message=message,
            code="SPRINT_NOT_FOUND",
            suggestions=suggestions,
            hint="Sprint IDs follow pattern: <track-id>-<number> (e.g., backend-1)",
            metadata={
                "sprint_id": sprint_id,
                "track_id": track_id,
            },
        )


class TaskNotFoundError(RoadmapError):
    """Task not found."""

    def __init__(self, task_id: str, sprint_id: Optional[str] = None):
        message = f"Task '{task_id}' not found"
        suggestions = [
            "Check task ID spelling",
            "Verify sprint exists first",
        ]
        if sprint_id:
            suggestions.insert(0, f"List tasks: vibey roadmap show {sprint_id}")

        super().__init__(
            message=message,
            code="TASK_NOT_FOUND",
            suggestions=suggestions,
            hint="Task IDs follow pattern: <sprint-id>-task-<number>",
            metadata={
                "task_id": task_id,
                "sprint_id": sprint_id,
            },
        )


# ============================================================================
# Dependency Errors
# ============================================================================

class DependencyError(VibeyError):
    """Base class for dependency errors."""

    def __init__(self, message: str, code: str, **kwargs):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.DEPENDENCY,
            **kwargs
        )


class DependencyBlockedError(DependencyError):
    """Operation blocked by unmet dependency."""

    def __init__(
        self,
        object_id: str,
        object_type: str,
        blocker_id: str,
        blocker_type: str,
        required_status: str,
        current_status: str,
    ):
        super().__init__(
            message=(
                f"Cannot start {object_type} '{object_id}': "
                f"blocked by {blocker_type} '{blocker_id}' "
                f"(requires '{required_status}', currently '{current_status}')"
            ),
            code="DEPENDENCY_BLOCKED",
            suggestions=[
                f"Complete {blocker_type} '{blocker_id}' first",
                f"Check blocker status: vibey roadmap show {blocker_id}",
                "View all blockers: vibey roadmap blockers",
            ],
            hint="Dependencies must be satisfied before starting work",
            metadata={
                "object_id": object_id,
                "object_type": object_type,
                "blocker_id": blocker_id,
                "blocker_type": blocker_type,
                "required_status": required_status,
                "current_status": current_status,
            },
        )


class CircularDependencyError(DependencyError):
    """Circular dependency detected."""

    def __init__(self, dependency_chain: List[str]):
        chain = " → ".join(dependency_chain)
        super().__init__(
            message=f"Circular dependency detected: {chain}",
            code="CIRCULAR_DEPENDENCY",
            suggestions=[
                "Remove one dependency to break the cycle",
                "Restructure dependencies to be acyclic",
                "View dependency graph: vibey roadmap dependencies",
            ],
            hint="Circular dependencies prevent progress and must be resolved",
            metadata={"dependency_chain": dependency_chain},
        )


# ============================================================================
# State Errors
# ============================================================================

class StateError(VibeyError):
    """Base class for state transition errors."""

    def __init__(self, message: str, code: str, **kwargs):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.STATE,
            **kwargs
        )


class InvalidStateTransitionError(StateError):
    """Invalid state transition attempted."""

    def __init__(
        self,
        object_id: str,
        current_status: str,
        attempted_status: str,
        valid_transitions: List[str],
    ):
        transitions_str = ", ".join(f"'{t}'" for t in valid_transitions)
        super().__init__(
            message=(
                f"Cannot transition '{object_id}' from '{current_status}' to '{attempted_status}'. "
                f"Valid transitions: {transitions_str}"
            ),
            code="INVALID_STATE_TRANSITION",
            suggestions=[
                f"Valid next states: {transitions_str}",
                f"Check current status: vibey roadmap show {object_id}",
                "Ensure all prerequisites are met",
            ],
            hint="State transitions follow a strict progression",
            metadata={
                "object_id": object_id,
                "current_status": current_status,
                "attempted_status": attempted_status,
                "valid_transitions": valid_transitions,
            },
        )


class QualityGateNotPassedError(StateError):
    """Quality gate requirements not met."""

    def __init__(
        self,
        object_id: str,
        gate_type: str,  # "completion" or "production"
        incomplete_gates: List[str],
    ):
        gates_list = "\n  ".join(f"• {g}" for g in incomplete_gates)
        super().__init__(
            message=(
                f"Cannot complete '{object_id}': {gate_type} gates not passed\n  {gates_list}"
            ),
            code="QUALITY_GATE_NOT_PASSED",
            suggestions=[
                f"Complete all {gate_type} gates",
                f"Check gate status: vibey roadmap show {object_id}",
                "Run gates: vibey roadmap run-gates",
            ],
            hint=f"{gate_type.capitalize()} gates enforce quality standards",
            metadata={
                "object_id": object_id,
                "gate_type": gate_type,
                "incomplete_gates": incomplete_gates,
            },
        )


# ============================================================================
# Validation Errors
# ============================================================================

class ValidationError(VibeyError):
    """Data validation error."""

    def __init__(
        self,
        object_type: str,
        object_id: str,
        errors: List[str],
    ):
        errors_list = "\n  ".join(f"• {e}" for e in errors)
        super().__init__(
            message=f"Validation failed for {object_type} '{object_id}':\n  {errors_list}",
            code="VALIDATION_FAILED",
            category=ErrorCategory.VALIDATION,
            suggestions=[
                "Fix validation errors",
                f"Check schema: vibey roadmap validate {object_id}",
                "View validation rules: vibey roadmap schema",
            ],
            hint="All objects must pass validation to maintain data integrity",
            metadata={
                "object_type": object_type,
                "object_id": object_id,
                "errors": errors,
            },
        )


# ============================================================================
# File System Errors
# ============================================================================

class FileSystemError(VibeyError):
    """Base class for file system errors."""

    def __init__(self, message: str, code: str, **kwargs):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.FILE_SYSTEM,
            **kwargs
        )


class FileNotFoundError(FileSystemError):
    """Expected file not found."""

    def __init__(self, file_path: str, file_type: str):
        super().__init__(
            message=f"{file_type} file not found: {file_path}",
            code="FILE_NOT_FOUND",
            suggestions=[
                "Check file path is correct",
                "Verify initialization completed successfully",
                "Try refreshing: vibey roadmap refresh",
            ],
            hint="Files may be missing if initialization was incomplete",
            metadata={
                "file_path": file_path,
                "file_type": file_type,
            },
        )


# ============================================================================
# Concurrency Errors
# ============================================================================

class ConcurrencyError(VibeyError):
    """Base class for concurrency errors."""

    def __init__(self, message: str, code: str, **kwargs):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.CONCURRENCY,
            **kwargs
        )


class ConcurrentModificationError(ConcurrencyError):
    """Concurrent modification detected."""

    def __init__(
        self,
        object_id: str,
        expected_version: str,
        actual_version: str,
    ):
        super().__init__(
            message=(
                f"Concurrent modification detected for '{object_id}'. "
                f"Expected version {expected_version}, but found {actual_version}."
            ),
            code="CONCURRENT_MODIFICATION",
            suggestions=[
                "Reload the object and retry",
                f"Check current state: vibey roadmap show {object_id}",
                "Coordinate with team members",
            ],
            hint="Another process modified this object - reload and retry",
            metadata={
                "object_id": object_id,
                "expected_version": expected_version,
                "actual_version": actual_version,
            },
        )


# ============================================================================
# Error Renderer Interface
# ============================================================================

class ErrorRenderer(ABC):
    """
    Abstract base class for error renderers.

    Renderers transform VibeyError instances into platform-specific output:
    - CLIErrorRenderer: Text output for terminal
    - MCPErrorRenderer: JSON output for MCP protocol
    - LogErrorRenderer: Structured logging format
    """

    @abstractmethod
    def render(self, error: VibeyError) -> Any:
        """
        Render error for the target platform.

        Args:
            error: VibeyError instance to render

        Returns:
            Platform-specific rendered output
        """
        pass

    @abstractmethod
    def render_multiple(self, errors: List[VibeyError]) -> Any:
        """
        Render multiple errors for the target platform.

        Args:
            errors: List of VibeyError instances

        Returns:
            Platform-specific rendered output
        """
        pass
