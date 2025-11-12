"""
Roadmap initialization operations.

Provides functionality to initialize a new roadmap structure with proper
directory setup and initial configuration.
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from vibey.roadmap.models import (
    Roadmap, VersionStrategy, Status, Progress, Metadata,
    ActivityType, VersionBumpTrigger,
)
from vibey.roadmap.serialization import save_roadmap
from vibey.roadmap.validation import Validator
from vibey.cli.roadmap_lib.filesystem import FileSystemManager
from vibey.cli.roadmap_lib.activity import ActivityLogger


def init_roadmap(
    root_dir: Path,
    roadmap_id: str,
    roadmap_name: str,
    version: str = "1.0.0",
    created_by: str = "system",
    major_on: str = "roadmap_milestone",
    minor_on: str = "track_completion",
    patch_on: str = "sprint_production_ready",
    force: bool = False,
) -> int:
    """
    Initialize a new roadmap structure.

    Creates .vibey/ directory structure and roadmap.yaml file with proper initialization.

    Args:
        root_dir: Root directory for the roadmap
        roadmap_id: Unique identifier for the roadmap
        roadmap_name: Human-readable name for the roadmap
        version: Initial semantic version (default: "1.0.0")
        created_by: Name of the creator (default: "system")
        major_on: Trigger for MAJOR version bump (default: "roadmap_milestone")
        minor_on: Trigger for MINOR version bump (default: "track_completion")
        patch_on: Trigger for PATCH version bump (default: "sprint_production_ready")
        force: Force initialization even if roadmap already exists (default: False)

    Returns:
        Exit code: 0 for success, 1 for error
    """
    # Initialize file system
    fs = FileSystemManager(root_dir)

    # Check if roadmap already exists
    if fs.roadmap_exists() and not force:
        print(f"❌ Roadmap already exists at {fs.get_roadmap_path()}")
        print("   Use force=True to reinitialize")
        return 1

    # Ensure directory structure exists
    fs.ensure_structure()
    print(f"✅ Created directory structure at {fs.vibey_dir}")

    # Normalize version to semver format (X.Y.Z)
    version_parts = version.split('.')
    if len(version_parts) == 2:
        version = f"{version}.0"  # 1.0 → 1.0.0
    elif len(version_parts) == 1:
        version = f"{version}.0.0"  # 1 → 1.0.0

    # Create roadmap
    roadmap = _create_roadmap(
        roadmap_id=roadmap_id,
        roadmap_name=roadmap_name,
        version=version,
        created_by=created_by,
        major_on=major_on,
        minor_on=minor_on,
        patch_on=patch_on,
    )

    # Save roadmap
    roadmap_path = fs.get_roadmap_path()
    save_roadmap(roadmap, roadmap_path)
    print(f"✅ Roadmap saved to {roadmap_path}")

    # Summary
    print("\n" + "="*60)
    print("Roadmap Initialized Successfully!")
    print("="*60)
    print(f"ID: {roadmap.id}")
    print(f"Name: {roadmap.name}")
    print(f"Version: {roadmap.version}")
    print(f"Status: {roadmap.status.value}")
    print(f"Location: {roadmap_path}")
    print("\n📚 Next steps:")
    print("  1. Use roadmap-update.py to add tracks and sprints")
    print("  2. Use roadmap-query.py to view roadmap status")
    print("  3. Start building!")

    return 0


def _create_roadmap(
    roadmap_id: str,
    roadmap_name: str,
    version: str,
    created_by: str,
    major_on: str = "roadmap_milestone",
    minor_on: str = "track_completion",
    patch_on: str = "sprint_production_ready",
) -> Roadmap:
    """
    Create a roadmap object with initial configuration.

    Args:
        roadmap_id: Unique identifier for the roadmap
        roadmap_name: Human-readable name for the roadmap
        version: Initial semantic version
        created_by: Name of the creator
        major_on: Trigger for MAJOR version bump
        minor_on: Trigger for MINOR version bump
        patch_on: Trigger for PATCH version bump

    Returns:
        Initialized Roadmap object
    """
    version_strategy = VersionStrategy(
        major_on=VersionBumpTrigger(major_on),
        minor_on=VersionBumpTrigger(minor_on),
        patch_on=VersionBumpTrigger(patch_on),
    )

    progress = Progress(
        tracks_total=0,
        tracks_completed=0,
        sprints_total=0,
        sprints_completed=0,
        tasks_total=0,
        tasks_completed=0,
        completion_percent=0,
    )

    now = datetime.now(timezone.utc)

    metadata = Metadata(
        created_by=created_by,
        framework_version="1.3.0",
        schema_version="2.1",
        last_updated=now,
        purpose=None,
        description=None,
    )

    roadmap = Roadmap(
        id=roadmap_id,
        name=roadmap_name,
        version=version,
        version_strategy=version_strategy,
        status=Status.NOT_STARTED,
        blocked=False,
        created=now,
        progress=progress,
        tracks=[],
        dependencies=[],
        activity_log=[],
        metadata=metadata,
    )

    # Add initialization activity
    roadmap.add_activity(
        ActivityType.ROADMAP_INITIALIZED,
        f"Roadmap '{roadmap_name}' initialized",
        {
            "version": version,
            "major_on": major_on,
            "minor_on": minor_on,
            "patch_on": patch_on,
        }
    )

    return roadmap
