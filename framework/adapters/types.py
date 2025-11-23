"""
Common types for platform adapters.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class ExportResult:
    """Result of exporting assets to a platform format."""

    platform: str
    files: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Export succeeded if no errors."""
        return len(self.errors) == 0

    @property
    def file_count(self) -> int:
        """Number of files exported."""
        return len(self.files)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "platform": self.platform,
            "success": self.success,
            "file_count": self.file_count,
            "files": [str(f) for f in self.files],
            "errors": self.errors,
            "warnings": self.warnings,
        }


@dataclass
class PlatformCapabilities:
    """Capabilities supported by a platform adapter."""

    agents: bool = True
    workflows: bool = True
    handoffs: bool = False
    real_time_discovery: bool = False
    recipes: bool = False
    extension_manifest: bool = False

    def to_dict(self) -> Dict[str, bool]:
        """Convert to dictionary."""
        return {
            "agents": self.agents,
            "workflows": self.workflows,
            "handoffs": self.handoffs,
            "real_time_discovery": self.real_time_discovery,
            "recipes": self.recipes,
            "extension_manifest": self.extension_manifest,
        }


@dataclass
class AdapterInfo:
    """Information about a platform adapter."""

    platform_name: str
    display_name: str
    description: str
    adapter_type: str  # "base" or "composite"
    base_platform: Optional[str] = None  # For composite adapters
    capabilities: PlatformCapabilities = field(default_factory=PlatformCapabilities)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "platform_name": self.platform_name,
            "display_name": self.display_name,
            "description": self.description,
            "adapter_type": self.adapter_type,
            "base_platform": self.base_platform,
            "capabilities": self.capabilities.to_dict(),
        }
