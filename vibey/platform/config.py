"""
Platform configuration management for Vibey.

Stores and loads platform configuration from .vibey/config/platform.yaml.
Supports auto-detection with user overrides.
"""

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

import yaml

from vibey.platform.detector import (
    PlatformInfo,
    PlatformName,
    DetectionMethod,
    detect_platform,
    get_platform_info,
)
from vibey.platform.context import PLATFORM_CONTEXT_WINDOWS


# Default config path
DEFAULT_CONFIG_DIR = ".vibey/config"
DEFAULT_CONFIG_FILE = "platform.yaml"


@dataclass
class PlatformConfig:
    """Platform configuration stored in .vibey/config/platform.yaml."""
    # Platform identification
    platform: Optional[str] = None  # Platform ID (e.g., 'claude-code')
    context_window: Optional[int] = None  # Override context window

    # Auto-detection settings
    auto_detect: bool = True  # Whether to auto-detect platform
    prefer_detected: bool = False  # Prefer detected over configured

    # Metadata
    last_detected: Optional[str] = None
    last_detection_method: Optional[str] = None
    configured_at: Optional[str] = None
    configured_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "platform": {
                "name": self.platform,
                "context_window": self.context_window,
            },
            "detection": {
                "auto_detect": self.auto_detect,
                "prefer_detected": self.prefer_detected,
                "last_detected": self.last_detected,
                "last_detection_method": self.last_detection_method,
            },
            "metadata": {
                "configured_at": self.configured_at,
                "configured_by": self.configured_by,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlatformConfig":
        """Create from dictionary (loaded from YAML)."""
        platform_data = data.get("platform", {})
        detection_data = data.get("detection", {})
        metadata = data.get("metadata", {})

        return cls(
            platform=platform_data.get("name"),
            context_window=platform_data.get("context_window"),
            auto_detect=detection_data.get("auto_detect", True),
            prefer_detected=detection_data.get("prefer_detected", False),
            last_detected=detection_data.get("last_detected"),
            last_detection_method=detection_data.get("last_detection_method"),
            configured_at=metadata.get("configured_at"),
            configured_by=metadata.get("configured_by"),
        )


def get_config_path(project_root: Optional[Path] = None) -> Path:
    """Get the platform config file path."""
    if project_root is None:
        project_root = Path.cwd()
    return project_root / DEFAULT_CONFIG_DIR / DEFAULT_CONFIG_FILE


def load_platform_config(project_root: Optional[Path] = None) -> PlatformConfig:
    """
    Load platform configuration from file.

    Args:
        project_root: Project root directory. Defaults to current directory.

    Returns:
        PlatformConfig object (defaults if file doesn't exist).
    """
    config_path = get_config_path(project_root)

    if not config_path.exists():
        return PlatformConfig()

    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}
        return PlatformConfig.from_dict(data)
    except Exception as e:
        # Return defaults if config is invalid
        return PlatformConfig()


def save_platform_config(config: PlatformConfig, project_root: Optional[Path] = None) -> Path:
    """
    Save platform configuration to file.

    Args:
        config: PlatformConfig to save.
        project_root: Project root directory. Defaults to current directory.

    Returns:
        Path to saved config file.
    """
    config_path = get_config_path(project_root)

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write config with nice formatting
    with open(config_path, "w") as f:
        yaml.dump(
            config.to_dict(),
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    return config_path


def set_platform(
    platform: str,
    context_window: Optional[int] = None,
    project_root: Optional[Path] = None,
) -> PlatformConfig:
    """
    Set the platform configuration.

    Args:
        platform: Platform identifier (e.g., 'claude-code').
        context_window: Optional context window override.
        project_root: Project root directory.

    Returns:
        Updated PlatformConfig.
    """
    config = load_platform_config(project_root)

    # Update platform settings
    config.platform = platform
    if context_window is not None:
        config.context_window = context_window
    elif platform in PLATFORM_CONTEXT_WINDOWS:
        # Use default for known platform if not specified
        config.context_window = PLATFORM_CONTEXT_WINDOWS[platform]

    # Update metadata
    config.configured_at = datetime.now(timezone.utc).isoformat()
    config.configured_by = os.environ.get("USER", "unknown")

    # Save and return
    save_platform_config(config, project_root)
    return config


def get_effective_platform(project_root: Optional[Path] = None) -> PlatformInfo:
    """
    Get the effective platform, considering config and detection.

    Priority:
    1. If config.prefer_detected and auto_detect, use detected
    2. If config.platform is set, use configured
    3. If auto_detect, use detected
    4. Fall back to unknown

    Args:
        project_root: Project root directory.

    Returns:
        PlatformInfo with effective platform.
    """
    config = load_platform_config(project_root)
    detected = detect_platform(project_root)

    # Update detection info in config
    config.last_detected = detected.name
    config.last_detection_method = detected.detected_by.value

    # Determine effective platform
    if config.prefer_detected and config.auto_detect:
        # Prefer detected even if configured
        platform_info = detected
        if config.context_window is not None:
            # But still apply context window override
            platform_info.context_window = config.context_window
    elif config.platform is not None:
        # Use configured platform
        platform_info = get_platform_info(config.platform)
        platform_info.detected_by = DetectionMethod.MANUAL
        if config.context_window is not None:
            platform_info.context_window = config.context_window
    elif config.auto_detect:
        # Use detected platform
        platform_info = detected
        if config.context_window is not None:
            platform_info.context_window = config.context_window
    else:
        # No config, no detection - return unknown
        platform_info = PlatformInfo(
            name=PlatformName.UNKNOWN.value,
            display_name="Unknown Platform",
            vendor="Unknown",
            detected_by=DetectionMethod.FALLBACK,
            context_window=config.context_window or 128_000,
        )

    return platform_info


def clear_platform_config(project_root: Optional[Path] = None) -> bool:
    """
    Clear the platform configuration file.

    Args:
        project_root: Project root directory.

    Returns:
        True if file was deleted, False if it didn't exist.
    """
    config_path = get_config_path(project_root)

    if config_path.exists():
        config_path.unlink()
        return True
    return False


def get_platform_config_status(project_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get comprehensive platform configuration status.

    Args:
        project_root: Project root directory.

    Returns:
        Dict with configured, detected, and effective platform info.
    """
    config = load_platform_config(project_root)
    detected = detect_platform(project_root)
    effective = get_effective_platform(project_root)

    return {
        "configured": {
            "platform": config.platform,
            "context_window": config.context_window,
            "auto_detect": config.auto_detect,
            "prefer_detected": config.prefer_detected,
        },
        "detected": detected.to_dict(),
        "effective": effective.to_dict(),
        "config_file": str(get_config_path(project_root)),
        "config_exists": get_config_path(project_root).exists(),
    }
