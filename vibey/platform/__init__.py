"""
Platform detection and context management for Vibey.

This module provides:
- Platform detection (Claude Code, Goose, Cursor, etc.)
- Context window detection
- Platform configuration management
- Platform validation and warnings
"""

from vibey.platform.detector import (
    PlatformInfo,
    PlatformName,
    DetectionMethod,
    detect_platform,
    get_platform_info,
    list_known_platforms,
    KNOWN_PLATFORMS,
)
from vibey.platform.context import (
    get_context_window,
    estimate_token_count,
    check_fits_context,
    format_token_count,
    get_platform_context_summary,
    PLATFORM_CONTEXT_WINDOWS,
)
from vibey.platform.config import (
    PlatformConfig,
    load_platform_config,
    save_platform_config,
    set_platform,
    get_effective_platform,
    clear_platform_config,
    get_platform_config_status,
)
from vibey.platform.validation import (
    ValidationLevel,
    ValidationMessage,
    ValidationResult,
    validate_platform_name,
    validate_context_window,
    validate_platform_config,
    format_validation_result,
    get_platform_warnings,
)

__all__ = [
    # Detector
    "PlatformInfo",
    "PlatformName",
    "DetectionMethod",
    "detect_platform",
    "get_platform_info",
    "list_known_platforms",
    "KNOWN_PLATFORMS",
    # Context
    "get_context_window",
    "estimate_token_count",
    "check_fits_context",
    "format_token_count",
    "get_platform_context_summary",
    "PLATFORM_CONTEXT_WINDOWS",
    # Config
    "PlatformConfig",
    "load_platform_config",
    "save_platform_config",
    "set_platform",
    "get_effective_platform",
    "clear_platform_config",
    "get_platform_config_status",
    # Validation
    "ValidationLevel",
    "ValidationMessage",
    "ValidationResult",
    "validate_platform_name",
    "validate_context_window",
    "validate_platform_config",
    "format_validation_result",
    "get_platform_warnings",
]
