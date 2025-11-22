"""
Platform validation and warnings for Vibey.

Validates platform configuration and provides helpful warnings
when platform detection fails or configuration seems incorrect.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path

from vibey.platform.detector import (
    PlatformInfo,
    PlatformName,
    KNOWN_PLATFORMS,
    detect_platform,
)
from vibey.platform.context import PLATFORM_CONTEXT_WINDOWS


class ValidationLevel(str, Enum):
    """Severity level for validation messages."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationMessage:
    """A validation message with context."""
    level: ValidationLevel
    message: str
    detail: Optional[str] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": self.level.value,
            "message": self.message,
            "detail": self.detail,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationResult:
    """Result of platform validation."""
    valid: bool
    messages: List[ValidationMessage]
    platform_info: Optional[PlatformInfo] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "messages": [m.to_dict() for m in self.messages],
            "platform_info": self.platform_info.to_dict() if self.platform_info else None,
        }

    def has_errors(self) -> bool:
        """Check if there are any error-level messages."""
        return any(m.level == ValidationLevel.ERROR for m in self.messages)

    def has_warnings(self) -> bool:
        """Check if there are any warning-level messages."""
        return any(m.level == ValidationLevel.WARNING for m in self.messages)


def validate_platform_name(platform: str) -> ValidationResult:
    """
    Validate a platform name.

    Args:
        platform: Platform identifier to validate.

    Returns:
        ValidationResult with messages.
    """
    messages = []

    # Check if it's a known platform
    if platform in KNOWN_PLATFORMS:
        messages.append(ValidationMessage(
            level=ValidationLevel.INFO,
            message=f"Platform '{platform}' is recognized",
            detail=f"Known as: {KNOWN_PLATFORMS[platform]['name']}",
        ))
        return ValidationResult(valid=True, messages=messages)

    # Check for common typos/variations
    platform_lower = platform.lower().replace("_", "-").replace(" ", "-")
    for known_id in KNOWN_PLATFORMS:
        if platform_lower == known_id.lower():
            messages.append(ValidationMessage(
                level=ValidationLevel.WARNING,
                message=f"Platform '{platform}' might be a case variation",
                detail=f"Did you mean '{known_id}'?",
                suggestion=f"Use: vibey config platform set {known_id}",
            ))
            return ValidationResult(valid=True, messages=messages)

    # Unknown platform - warn but allow
    messages.append(ValidationMessage(
        level=ValidationLevel.WARNING,
        message=f"Platform '{platform}' is not recognized",
        detail="This platform will use default context window (128K tokens)",
        suggestion="Known platforms: " + ", ".join(KNOWN_PLATFORMS.keys()),
    ))

    return ValidationResult(valid=True, messages=messages)


def validate_context_window(context_window: int, platform: Optional[str] = None) -> ValidationResult:
    """
    Validate a context window size.

    Args:
        context_window: Context window size in tokens.
        platform: Optional platform for comparison.

    Returns:
        ValidationResult with messages.
    """
    messages = []

    # Check minimum (very small context windows are suspicious)
    if context_window < 4_000:
        messages.append(ValidationMessage(
            level=ValidationLevel.WARNING,
            message=f"Context window {context_window:,} tokens seems too small",
            detail="Most modern AI models have at least 4K token context",
            suggestion="Check if this value is correct",
        ))

    # Check maximum (extremely large values might be errors)
    if context_window > 2_000_000:
        messages.append(ValidationMessage(
            level=ValidationLevel.WARNING,
            message=f"Context window {context_window:,} tokens seems unusually large",
            detail="Most AI models have context windows under 2M tokens",
            suggestion="Verify this value is correct for your platform",
        ))

    # Compare to expected for platform
    if platform and platform in PLATFORM_CONTEXT_WINDOWS:
        expected = PLATFORM_CONTEXT_WINDOWS[platform]
        if context_window != expected:
            ratio = context_window / expected
            if ratio < 0.5 or ratio > 2.0:
                messages.append(ValidationMessage(
                    level=ValidationLevel.WARNING,
                    message=f"Context window differs significantly from {platform} default",
                    detail=f"Expected: {expected:,} tokens, Got: {context_window:,} tokens",
                    suggestion="This may be intentional if using a different model tier",
                ))
            else:
                messages.append(ValidationMessage(
                    level=ValidationLevel.INFO,
                    message=f"Context window differs from {platform} default ({expected:,} tokens)",
                ))

    if not messages:
        messages.append(ValidationMessage(
            level=ValidationLevel.INFO,
            message=f"Context window {context_window:,} tokens is within normal range",
        ))

    valid = not any(m.level == ValidationLevel.ERROR for m in messages)
    return ValidationResult(valid=valid, messages=messages)


def validate_platform_config(
    platform: Optional[str] = None,
    context_window: Optional[int] = None,
    project_root: Optional[Path] = None,
) -> ValidationResult:
    """
    Validate complete platform configuration.

    Args:
        platform: Platform identifier.
        context_window: Context window size.
        project_root: Project root for detection.

    Returns:
        ValidationResult with all validation messages.
    """
    messages = []

    # Detect current platform
    detected = detect_platform(project_root)

    # If no platform specified, use detected
    if platform is None:
        platform = detected.name

        if platform == PlatformName.UNKNOWN.value:
            messages.append(ValidationMessage(
                level=ValidationLevel.WARNING,
                message="Platform could not be auto-detected",
                detail="Using default context window (128K tokens)",
                suggestion="Set platform manually: vibey config platform set <platform>",
            ))
        else:
            messages.append(ValidationMessage(
                level=ValidationLevel.INFO,
                message=f"Platform auto-detected as '{platform}'",
                detail=f"Detection method: {detected.detected_by.value}",
            ))

    # Validate platform name
    name_result = validate_platform_name(platform)
    messages.extend(name_result.messages)

    # Validate context window if specified
    if context_window is not None:
        window_result = validate_context_window(context_window, platform)
        messages.extend(window_result.messages)

    # Check for potential issues
    if detected.confidence < 0.5 and platform != PlatformName.UNKNOWN.value:
        messages.append(ValidationMessage(
            level=ValidationLevel.INFO,
            message=f"Detection confidence is low ({detected.confidence:.0%})",
            detail="Platform detection may not be reliable",
        ))

    valid = not any(m.level == ValidationLevel.ERROR for m in messages)
    return ValidationResult(valid=valid, messages=messages, platform_info=detected)


def format_validation_result(result: ValidationResult, show_info: bool = True) -> str:
    """
    Format validation result for CLI display.

    Args:
        result: ValidationResult to format.
        show_info: Whether to show info-level messages.

    Returns:
        Formatted string for display.
    """
    lines = []

    # Status header
    if result.valid:
        if result.has_warnings():
            lines.append("Platform configuration valid with warnings")
        else:
            lines.append("Platform configuration valid")
    else:
        lines.append("Platform configuration has errors")

    lines.append("")

    # Messages by level
    for level in [ValidationLevel.ERROR, ValidationLevel.WARNING, ValidationLevel.INFO]:
        level_messages = [m for m in result.messages if m.level == level]

        if level == ValidationLevel.INFO and not show_info:
            continue

        for msg in level_messages:
            prefix = {
                ValidationLevel.ERROR: "[ERROR]",
                ValidationLevel.WARNING: "[WARN]",
                ValidationLevel.INFO: "[INFO]",
            }[level]

            lines.append(f"{prefix} {msg.message}")
            if msg.detail:
                lines.append(f"        {msg.detail}")
            if msg.suggestion:
                lines.append(f"        Suggestion: {msg.suggestion}")

    return "\n".join(lines)


def get_platform_warnings(project_root: Optional[Path] = None) -> List[str]:
    """
    Get list of warning messages for current platform configuration.

    Useful for displaying warnings in CLI commands.

    Args:
        project_root: Project root directory.

    Returns:
        List of warning message strings.
    """
    result = validate_platform_config(project_root=project_root)

    warnings = []
    for msg in result.messages:
        if msg.level in [ValidationLevel.ERROR, ValidationLevel.WARNING]:
            warning = msg.message
            if msg.detail:
                warning += f" ({msg.detail})"
            warnings.append(warning)

    return warnings
