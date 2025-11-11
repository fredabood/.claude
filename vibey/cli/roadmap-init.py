#!/usr/bin/env python3
"""
Initialize a new roadmap structure.

Creates .vibey/ directory structure and roadmap.yaml file with proper initialization.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# Add repository root to path for framework imports
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

# Add scripts dir to path for roadmap_lib package
scripts_path = Path(__file__).parent
sys.path.insert(0, str(scripts_path))

from vibey.roadmap.models import (
    Roadmap, VersionStrategy, Status, Progress, Metadata,
    ActivityType, VersionBumpTrigger,
)
from vibey.roadmap.serialization import save_roadmap
from vibey.roadmap.validation import Validator
from roadmap_lib.filesystem import FileSystemManager
from roadmap_lib.activity import ActivityLogger


def prompt_input(prompt: str, default: Optional[str] = None) -> str:
    """Prompt user for input with optional default."""
    if default:
        prompt = f"{prompt} [{default}]"

    value = input(f"{prompt}: ").strip()
    return value if value else default


def prompt_choice(prompt: str, choices: list[str], default: Optional[str] = None) -> str:
    """Prompt user to choose from a list of options."""
    print(f"\n{prompt}")
    for i, choice in enumerate(choices, 1):
        marker = " (default)" if choice == default else ""
        print(f"  {i}. {choice}{marker}")

    while True:
        value = input(f"Choose [1-{len(choices)}]: ").strip()

        if not value and default:
            return default

        try:
            idx = int(value) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass

        print(f"❌ Invalid choice. Please enter a number between 1 and {len(choices)}.")


def create_roadmap_interactive(root_dir: Path) -> Roadmap:
    """Create roadmap interactively with user prompts."""
    print("\n" + "="*60)
    print("Roadmap Initialization")
    print("="*60)

    # Basic info
    print("\n📋 Basic Information")
    roadmap_id = prompt_input("Roadmap ID", "my-project-roadmap")
    roadmap_name = prompt_input("Roadmap Name", "My Project Roadmap")

    # Version strategy
    print("\n📦 Versioning Strategy")
    print("When should each version component be bumped?")

    trigger_choices = [
        "roadmap_milestone",
        "track_completion",
        "sprint_production_ready",
        "manual",
    ]

    major_on = prompt_choice(
        "Bump MAJOR version on:",
        trigger_choices,
        default="roadmap_milestone"
    )

    minor_on = prompt_choice(
        "Bump MINOR version on:",
        trigger_choices,
        default="track_completion"
    )

    patch_on = prompt_choice(
        "Bump PATCH version on:",
        trigger_choices,
        default="sprint_production_ready"
    )

    initial_version = prompt_input("Initial version", "1.0.0")

    # Create roadmap
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
        created_by=prompt_input("Created by", "system"),
        framework_version="1.3.0",
        schema_version="2.1",
        last_updated=now,
        purpose=None,
        description=None,
    )

    roadmap = Roadmap(
        id=roadmap_id,
        name=roadmap_name,
        version=initial_version,
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
            "version": initial_version,
            "major_on": major_on,
            "minor_on": minor_on,
            "patch_on": patch_on,
        }
    )

    return roadmap


def create_roadmap_from_args(
    roadmap_id: str,
    roadmap_name: str,
    version: str,
    created_by: str,
    major_on: str = "roadmap_milestone",
    minor_on: str = "track_completion",
    patch_on: str = "sprint_production_ready",
) -> Roadmap:
    """Create roadmap from command-line arguments."""
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


def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new roadmap structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python3 roadmap-init.py

  # Non-interactive mode
  python3 roadmap-init.py --id my-roadmap --name "My Project" --version 1.0.0

  # Custom directory
  python3 roadmap-init.py --dir /path/to/project
        """
    )

    parser.add_argument(
        "--dir",
        type=Path,
        default=Path.cwd(),
        help="Root directory (defaults to current working directory)"
    )

    parser.add_argument(
        "--id",
        type=str,
        help="Roadmap ID (required for non-interactive mode)"
    )

    parser.add_argument(
        "--name",
        type=str,
        help="Roadmap name (required for non-interactive mode)"
    )

    parser.add_argument(
        "--version",
        type=str,
        default="1.0.0",
        help="Initial version (default: 1.0.0)"
    )

    parser.add_argument(
        "--major-on",
        type=str,
        choices=["roadmap_milestone", "track_completion", "sprint_production_ready", "manual"],
        default="roadmap_milestone",
        help="Trigger for MAJOR version bump (default: roadmap_milestone)"
    )

    parser.add_argument(
        "--minor-on",
        type=str,
        choices=["roadmap_milestone", "track_completion", "sprint_production_ready", "manual"],
        default="track_completion",
        help="Trigger for MINOR version bump (default: track_completion)"
    )

    parser.add_argument(
        "--patch-on",
        type=str,
        choices=["roadmap_milestone", "track_completion", "sprint_production_ready", "manual"],
        default="sprint_production_ready",
        help="Trigger for PATCH version bump (default: sprint_production_ready)"
    )

    parser.add_argument(
        "--created-by",
        type=str,
        default="system",
        help="Creator name (default: system)"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force initialization even if roadmap already exists"
    )

    args = parser.parse_args()

    # Initialize file system
    fs = FileSystemManager(args.dir)

    # Check if roadmap already exists
    if fs.roadmap_exists() and not args.force:
        print(f"❌ Roadmap already exists at {fs.get_roadmap_path()}")
        print("   Use --force to reinitialize")
        sys.exit(1)

    # Ensure directory structure exists
    fs.ensure_structure()
    print(f"✅ Created directory structure at {fs.vibey_dir}")

    # Create roadmap (interactive or from args)
    if args.name:
        # Non-interactive mode (auto-generate ID from name if not provided)
        roadmap_id = args.id if args.id else args.name.lower().replace(" ", "-")

        # Normalize version to semver format (X.Y.Z)
        version = args.version
        version_parts = version.split('.')
        if len(version_parts) == 2:
            version = f"{version}.0"  # 1.0 → 1.0.0
        elif len(version_parts) == 1:
            version = f"{version}.0.0"  # 1 → 1.0.0

        roadmap = create_roadmap_from_args(
            roadmap_id=roadmap_id,
            roadmap_name=args.name,
            version=version,
            created_by=args.created_by,
            major_on=args.major_on,
            minor_on=args.minor_on,
            patch_on=args.patch_on,
        )
    elif args.id:
        # ID provided but no name - error
        print("❌ --name is required for non-interactive mode")
        sys.exit(1)
    else:
        # Interactive mode (no args provided)
        roadmap = create_roadmap_interactive(args.dir)

    # Skip validation for initialization - empty roadmaps are allowed during init
    # The validator requires at least one track, but that's too strict for initialization

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


if __name__ == "__main__":
    main()
