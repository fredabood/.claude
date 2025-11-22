"""
Platform detection module for Vibey.

Detects the current AI coding platform through:
- Environment variables
- Process name detection
- File-based detection (config files)
- User agent analysis (when available)

Supported platforms:
- claude-code: Claude Code (Anthropic)
- goose: Goose (Block)
- cursor: Cursor IDE
- aider: Aider CLI
- continue: Continue (VS Code extension)
- copilot: GitHub Copilot
- jetbrains-ai: JetBrains AI Assistant
- windsurf: Windsurf (Codeium)
- unknown: Undetected platform
"""

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any


class DetectionMethod(str, Enum):
    """Methods used to detect the platform."""
    ENVIRONMENT = "environment"
    PROCESS = "process"
    CONFIG_FILE = "config_file"
    USER_AGENT = "user_agent"
    MANUAL = "manual"
    FALLBACK = "fallback"


class PlatformName(str, Enum):
    """Known AI coding platforms."""
    CLAUDE_CODE = "claude-code"
    GOOSE = "goose"
    CURSOR = "cursor"
    AIDER = "aider"
    CONTINUE = "continue"
    COPILOT = "copilot"
    JETBRAINS_AI = "jetbrains-ai"
    WINDSURF = "windsurf"
    VSCODE = "vscode"
    UNKNOWN = "unknown"


# Known platforms with their detection signatures
KNOWN_PLATFORMS: Dict[str, Dict[str, Any]] = {
    PlatformName.CLAUDE_CODE.value: {
        "name": "Claude Code",
        "vendor": "Anthropic",
        "env_vars": ["CLAUDE_CODE", "CLAUDE_CODE_VERSION", "ANTHROPIC_API_KEY"],
        "process_names": ["claude", "claude-code"],
        "config_files": [".claude/settings.json", ".claude/settings.local.json"],
        "context_window": 200_000,
        "description": "Anthropic's CLI for Claude",
    },
    PlatformName.GOOSE.value: {
        "name": "Goose",
        "vendor": "Block",
        "env_vars": ["GOOSE_HOME", "GOOSE_CONFIG"],
        "process_names": ["goose"],
        "config_files": [".goose/config.yaml", "goose.yaml"],
        "context_window": 128_000,
        "description": "Block's open-source AI agent",
    },
    PlatformName.CURSOR.value: {
        "name": "Cursor",
        "vendor": "Cursor Inc",
        "env_vars": ["CURSOR_SESSION", "CURSOR_WORKSPACE"],
        "process_names": ["cursor", "Cursor"],
        "config_files": [".cursorrules", ".cursor/settings.json"],
        "context_window": 128_000,
        "description": "AI-first code editor",
    },
    PlatformName.AIDER.value: {
        "name": "Aider",
        "vendor": "Paul Gauthier",
        "env_vars": ["AIDER_MODEL", "AIDER_CONFIG"],
        "process_names": ["aider"],
        "config_files": [".aider.conf.yml", ".aider/"],
        "context_window": 128_000,  # Depends on model
        "description": "AI pair programming CLI",
    },
    PlatformName.CONTINUE.value: {
        "name": "Continue",
        "vendor": "Continue Dev",
        "env_vars": ["CONTINUE_GLOBAL_DIR"],
        "process_names": [],
        "config_files": [".continue/config.json", ".continuerc.json"],
        "context_window": 128_000,  # Depends on model
        "description": "VS Code/JetBrains AI extension",
    },
    PlatformName.COPILOT.value: {
        "name": "GitHub Copilot",
        "vendor": "GitHub/Microsoft",
        "env_vars": ["GITHUB_COPILOT_TOKEN"],
        "process_names": [],
        "config_files": [".github/copilot-instructions.md"],
        "context_window": 64_000,  # Varies by tier
        "description": "GitHub's AI pair programmer",
    },
    PlatformName.JETBRAINS_AI.value: {
        "name": "JetBrains AI",
        "vendor": "JetBrains",
        "env_vars": ["JETBRAINS_AI_ENABLED"],
        "process_names": ["idea", "pycharm", "webstorm", "goland", "rider", "clion"],
        "config_files": [],
        "context_window": 128_000,
        "description": "JetBrains AI Assistant",
    },
    PlatformName.WINDSURF.value: {
        "name": "Windsurf",
        "vendor": "Codeium",
        "env_vars": ["WINDSURF_SESSION"],
        "process_names": ["windsurf", "Windsurf"],
        "config_files": [".windsurfrules"],
        "context_window": 128_000,
        "description": "Codeium's AI IDE",
    },
    PlatformName.VSCODE.value: {
        "name": "VS Code",
        "vendor": "Microsoft",
        "env_vars": ["VSCODE_PID", "VSCODE_IPC_HOOK"],
        "process_names": ["code", "Code"],
        "config_files": [".vscode/settings.json"],
        "context_window": 128_000,  # Depends on extension
        "description": "Visual Studio Code (with AI extension)",
    },
}


@dataclass
class PlatformInfo:
    """Information about the detected platform."""
    name: str  # Platform identifier (e.g., 'claude-code')
    display_name: str  # Human-readable name (e.g., 'Claude Code')
    vendor: str  # Platform vendor
    version: Optional[str] = None
    detected_by: DetectionMethod = DetectionMethod.FALLBACK
    context_window: int = 128_000  # Default context window
    description: str = ""
    confidence: float = 0.0  # 0.0 to 1.0
    detection_details: Dict[str, Any] = field(default_factory=dict)
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def is_known(self) -> bool:
        """Check if this is a known platform."""
        return self.name != PlatformName.UNKNOWN.value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "vendor": self.vendor,
            "version": self.version,
            "detected_by": self.detected_by.value,
            "context_window": self.context_window,
            "description": self.description,
            "confidence": self.confidence,
            "detection_details": self.detection_details,
            "detected_at": self.detected_at,
        }


def _check_environment_vars(platform_id: str) -> Optional[Dict[str, str]]:
    """Check environment variables for platform indicators."""
    platform_info = KNOWN_PLATFORMS.get(platform_id, {})
    env_vars = platform_info.get("env_vars", [])

    found_vars = {}
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            found_vars[var] = value

    return found_vars if found_vars else None


def _check_process_names() -> Optional[str]:
    """Check if running under a known platform process."""
    try:
        # Get the parent process name
        import psutil
        current = psutil.Process()
        parent = current.parent()

        if parent:
            parent_name = parent.name().lower()
            for platform_id, info in KNOWN_PLATFORMS.items():
                for proc_name in info.get("process_names", []):
                    if proc_name.lower() in parent_name:
                        return platform_id
    except ImportError:
        # psutil not available, try sys.executable
        pass
    except Exception:
        pass

    # Check sys.executable as fallback
    executable = sys.executable.lower()
    for platform_id, info in KNOWN_PLATFORMS.items():
        for proc_name in info.get("process_names", []):
            if proc_name.lower() in executable:
                return platform_id

    return None


def _check_config_files(cwd: Optional[Path] = None) -> Optional[str]:
    """Check for platform-specific config files."""
    if cwd is None:
        cwd = Path.cwd()

    for platform_id, info in KNOWN_PLATFORMS.items():
        for config_file in info.get("config_files", []):
            config_path = cwd / config_file
            if config_path.exists():
                return platform_id

    return None


def detect_platform(cwd: Optional[Path] = None) -> PlatformInfo:
    """
    Detect the current AI coding platform.

    Detection priority:
    1. Environment variables (highest confidence)
    2. Process name detection
    3. Config file detection
    4. Fallback to unknown

    Args:
        cwd: Working directory to check for config files. Defaults to current directory.

    Returns:
        PlatformInfo with detected platform details.
    """
    if cwd is None:
        cwd = Path.cwd()

    # Try environment variable detection first (highest confidence)
    for platform_id in KNOWN_PLATFORMS:
        env_vars = _check_environment_vars(platform_id)
        if env_vars:
            info = KNOWN_PLATFORMS[platform_id]
            return PlatformInfo(
                name=platform_id,
                display_name=info["name"],
                vendor=info["vendor"],
                version=env_vars.get(f"{platform_id.upper().replace('-', '_')}_VERSION"),
                detected_by=DetectionMethod.ENVIRONMENT,
                context_window=info["context_window"],
                description=info["description"],
                confidence=0.95,
                detection_details={"env_vars": env_vars},
            )

    # Try process name detection
    process_platform = _check_process_names()
    if process_platform:
        info = KNOWN_PLATFORMS[process_platform]
        return PlatformInfo(
            name=process_platform,
            display_name=info["name"],
            vendor=info["vendor"],
            detected_by=DetectionMethod.PROCESS,
            context_window=info["context_window"],
            description=info["description"],
            confidence=0.8,
            detection_details={"method": "process_inspection"},
        )

    # Try config file detection
    config_platform = _check_config_files(cwd)
    if config_platform:
        info = KNOWN_PLATFORMS[config_platform]
        return PlatformInfo(
            name=config_platform,
            display_name=info["name"],
            vendor=info["vendor"],
            detected_by=DetectionMethod.CONFIG_FILE,
            context_window=info["context_window"],
            description=info["description"],
            confidence=0.7,
            detection_details={"method": "config_file"},
        )

    # Fallback to unknown
    return PlatformInfo(
        name=PlatformName.UNKNOWN.value,
        display_name="Unknown Platform",
        vendor="Unknown",
        detected_by=DetectionMethod.FALLBACK,
        context_window=128_000,  # Conservative default
        description="Platform could not be detected",
        confidence=0.0,
        detection_details={"reason": "No platform indicators found"},
    )


def get_platform_info(platform_id: Optional[str] = None, cwd: Optional[Path] = None) -> PlatformInfo:
    """
    Get platform info for a specific platform or detect current platform.

    Args:
        platform_id: Optional platform identifier. If not provided, auto-detect.
        cwd: Working directory for config file detection.

    Returns:
        PlatformInfo for the specified or detected platform.
    """
    if platform_id is None:
        return detect_platform(cwd)

    # Look up known platform
    if platform_id in KNOWN_PLATFORMS:
        info = KNOWN_PLATFORMS[platform_id]
        return PlatformInfo(
            name=platform_id,
            display_name=info["name"],
            vendor=info["vendor"],
            detected_by=DetectionMethod.MANUAL,
            context_window=info["context_window"],
            description=info["description"],
            confidence=1.0,
            detection_details={"method": "manual_specification"},
        )

    # Unknown platform ID
    return PlatformInfo(
        name=platform_id,
        display_name=platform_id.replace("-", " ").title(),
        vendor="Unknown",
        detected_by=DetectionMethod.MANUAL,
        context_window=128_000,
        description=f"Custom platform: {platform_id}",
        confidence=0.5,
        detection_details={"method": "manual_specification", "warning": "Unknown platform ID"},
    )


def list_known_platforms() -> List[Dict[str, Any]]:
    """List all known platforms with their details."""
    platforms = []
    for platform_id, info in KNOWN_PLATFORMS.items():
        platforms.append({
            "id": platform_id,
            "name": info["name"],
            "vendor": info["vendor"],
            "context_window": info["context_window"],
            "description": info["description"],
        })
    return platforms
