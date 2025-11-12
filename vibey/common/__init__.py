"""
Vibey common utilities.

Shared code used across CLI, MCP, and core framework.
"""

from vibey.common.errors import (
    VibeyError,
    ErrorSeverity,
    ErrorCategory,
    ErrorContext,
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
    # Renderer interface
    ErrorRenderer,
)

__all__ = [
    # Base
    "VibeyError",
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorContext",
    "ErrorRenderer",
    # Configuration
    "ConfigurationError",
    "ConfigNotFoundError",
    "ConfigValidationError",
    # Roadmap
    "RoadmapError",
    "RoadmapNotFoundError",
    "TrackNotFoundError",
    "SprintNotFoundError",
    "TaskNotFoundError",
    # Dependencies
    "DependencyError",
    "DependencyBlockedError",
    "CircularDependencyError",
    # State
    "StateError",
    "InvalidStateTransitionError",
    "QualityGateNotPassedError",
    # Validation
    "ValidationError",
    # File system
    "FileSystemError",
    "FileNotFoundError",
    # Concurrency
    "ConcurrencyError",
    "ConcurrentModificationError",
]
