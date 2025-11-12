"""
Validation utilities for roadmap operations.

This module provides validation functions that require cross-object context,
such as validating commits against roadmap-level platform deployments.
"""

from typing import List, Optional
from pathlib import Path

from ..models import Roadmap, Task, PlatformDeployment
from ..serialization.yaml_loader import load_roadmap


class PlatformValidationError(ValueError):
    """Raised when a platform is not deployed for the roadmap."""
    pass


def validate_commit_platform(
    task: Task,
    platform: str,
    roadmap: Optional[Roadmap] = None,
    roadmap_path: Optional[Path] = None,
) -> None:
    """
    Validate that a platform is deployed for the task's roadmap.

    Args:
        task: Task to validate against
        platform: Platform name to validate
        roadmap: Roadmap object (if already loaded)
        roadmap_path: Path to roadmap.yaml (if roadmap not provided)

    Raises:
        PlatformValidationError: If platform is not deployed for this roadmap
        ValueError: If neither roadmap nor roadmap_path provided

    Example:
        >>> task = load_tasks("tasks.yaml")[0]
        >>> validate_commit_platform(
        ...     task,
        ...     platform="claude-code",
        ...     roadmap_path=Path(".vibey/roadmap.yaml")
        ... )
    """
    # Get roadmap if not provided
    if roadmap is None:
        if roadmap_path is None:
            raise ValueError("Either roadmap or roadmap_path must be provided")
        roadmap = load_roadmap(roadmap_path)

    # Check if platform is deployed
    if not roadmap.is_platform_deployed(platform):
        deployed_platforms = roadmap.get_deployed_platform_names()

        if not deployed_platforms:
            raise PlatformValidationError(
                f"Cannot add commit with platform '{platform}' to task {task.id}.\n"
                f"\n"
                f"No platforms have been deployed for roadmap '{roadmap.id}'.\n"
                f"\n"
                f"To fix:\n"
                f"  1. Deploy Vibey for {platform} first\n"
                f"  2. Or use an already deployed platform"
            )

        raise PlatformValidationError(
            f"Cannot add commit with platform '{platform}' to task {task.id}.\n"
            f"\n"
            f"Platform '{platform}' is not deployed for roadmap '{roadmap.id}'.\n"
            f"Deployed platforms: {', '.join(deployed_platforms)}\n"
            f"\n"
            f"To fix:\n"
            f"  1. Deploy Vibey for {platform} first\n"
            f"  2. Or use one of the deployed platforms: {', '.join(deployed_platforms)}"
        )


def get_deployed_platforms(roadmap: Roadmap) -> List[PlatformDeployment]:
    """
    Get all deployed platforms for a roadmap.

    Args:
        roadmap: Roadmap to get platforms from

    Returns:
        List of PlatformDeployment objects
    """
    return roadmap.deployed_platforms


def get_primary_platform(roadmap: Roadmap) -> Optional[PlatformDeployment]:
    """
    Get the primary platform for a roadmap.

    Args:
        roadmap: Roadmap to get primary platform from

    Returns:
        Primary PlatformDeployment or None if no primary set
    """
    return roadmap.get_primary_platform()


def add_commit_with_validation(
    task: Task,
    sha: str,
    message: str,
    author: str,
    platform: str,
    roadmap: Optional[Roadmap] = None,
    roadmap_path: Optional[Path] = None,
    date: Optional[object] = None,
    submitted_at: Optional[int] = None,
) -> None:
    """
    Add a commit to a task with platform validation.

    This function validates that the platform is deployed for the roadmap
    before adding the commit to the task.

    Args:
        task: Task to add commit to
        sha: Git commit SHA
        message: Commit message
        author: Commit author
        platform: Platform used to submit commit
        roadmap: Roadmap object (if already loaded)
        roadmap_path: Path to roadmap.yaml (if roadmap not provided)
        date: Git commit date, defaults to now
        submitted_at: Unix timestamp, defaults to now

    Raises:
        PlatformValidationError: If platform is not deployed for this roadmap
        ValueError: If neither roadmap nor roadmap_path provided

    Example:
        >>> from pathlib import Path
        >>> task = load_tasks("tasks.yaml")[0]
        >>> add_commit_with_validation(
        ...     task,
        ...     sha="a1b2c3d4",
        ...     message="feat: New feature",
        ...     author="Alice <alice@example.com>",
        ...     platform="claude-code",
        ...     roadmap_path=Path(".vibey/roadmap.yaml")
        ... )
    """
    # Validate platform first
    validate_commit_platform(task, platform, roadmap, roadmap_path)

    # If validation passed, add the commit
    task.add_commit(
        sha=sha,
        message=message,
        author=author,
        platform=platform,
        date=date,
        submitted_at=submitted_at,
    )
