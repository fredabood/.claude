"""
Version management utilities for roadmap.

Handles semantic versioning and automatic version bumps.
"""

from typing import Optional, Tuple
from pathlib import Path
import sys

# Add framework to path
framework_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_root))

from vibey.roadmap.models import Roadmap, VersionStrategy
from vibey.roadmap.serialization import load_roadmap, save_roadmap
from .filesystem import FileSystemManager


class VersionManager:
    """Manages roadmap versioning."""

    def __init__(self, root_dir: Optional[Path] = None):
        """
        Initialize version manager.

        Args:
            root_dir: Root directory (defaults to current working directory)
        """
        self.fs = FileSystemManager(root_dir)

    def parse_version(self, version: str) -> Tuple[int, int, int]:
        """
        Parse semantic version string.

        Args:
            version: Version string (e.g., "1.2.3")

        Returns:
            Tuple of (major, minor, patch)
        """
        parts = version.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version}")

        try:
            return int(parts[0]), int(parts[1]), int(parts[2])
        except ValueError:
            raise ValueError(f"Invalid version format: {version}")

    def format_version(self, major: int, minor: int, patch: int) -> str:
        """
        Format version tuple as string.

        Args:
            major: Major version
            minor: Minor version
            patch: Patch version

        Returns:
            Version string (e.g., "1.2.3")
        """
        return f"{major}.{minor}.{patch}"

    def bump_version(
        self,
        current_version: str,
        bump_type: str = "minor"
    ) -> str:
        """
        Bump version according to type.

        Args:
            current_version: Current version string
            bump_type: Type of bump (major, minor, patch)

        Returns:
            New version string
        """
        major, minor, patch = self.parse_version(current_version)

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")

        return self.format_version(major, minor, patch)

    def should_auto_bump(self, roadmap: Roadmap) -> bool:
        """
        Check if version should be automatically bumped.

        Args:
            roadmap: Roadmap object

        Returns:
            True if should bump, False otherwise
        """
        strategy = roadmap.version_strategy

        if strategy.bump_on == "manual":
            return False

        elif strategy.bump_on == "sprint_completion":
            # Check if any sprint was recently completed
            # This would need to track last bump timestamp
            # For now, return False (manual trigger needed)
            return False

        elif strategy.bump_on == "track_completion":
            # Check if any track was recently completed
            return False

        return False

    def bump_roadmap_version(
        self,
        bump_type: Optional[str] = None,
        message: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Bump roadmap version.

        Args:
            bump_type: Type of bump (major, minor, patch). If None, uses roadmap strategy.
            message: Optional message for activity log

        Returns:
            Tuple of (old_version, new_version)
        """
        roadmap_path = self.fs.get_roadmap_path()
        if not roadmap_path.exists():
            raise FileNotFoundError("Roadmap not found")

        roadmap = load_roadmap(roadmap_path)
        old_version = roadmap.version

        # Determine bump type
        if bump_type is None:
            bump_type = roadmap.version_strategy.bump_type

        # Bump version
        new_version = self.bump_version(old_version, bump_type)
        roadmap.version = new_version

        # Add activity
        activity_message = message or f"Version bumped from {old_version} to {new_version}"
        roadmap.add_activity(
            "version_bumped",
            activity_message,
            {
                "old_version": old_version,
                "new_version": new_version,
                "bump_type": bump_type,
            }
        )

        # Save roadmap
        save_roadmap(roadmap, roadmap_path)

        return old_version, new_version


def bump_version(
    bump_type: Optional[str] = None,
    message: Optional[str] = None,
    root_dir: Optional[Path] = None
) -> Tuple[str, str]:
    """
    Bump roadmap version (convenience function).

    Args:
        bump_type: Type of bump (major, minor, patch)
        message: Optional message for activity log
        root_dir: Root directory (defaults to current working directory)

    Returns:
        Tuple of (old_version, new_version)
    """
    manager = VersionManager(root_dir)
    return manager.bump_roadmap_version(bump_type, message)


def parse_version(version: str) -> Tuple[int, int, int]:
    """
    Parse version string (convenience function).

    Args:
        version: Version string (e.g., "1.2.3")

    Returns:
        Tuple of (major, minor, patch)
    """
    manager = VersionManager()
    return manager.parse_version(version)
