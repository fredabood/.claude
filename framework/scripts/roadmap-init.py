#!/usr/bin/env python3
"""
Initialize a new roadmap structure.

Creates .vibey/ directory structure and roadmap.yaml file with proper initialization.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add framework to path
framework_root = Path(__file__).parent.parent
sys.path.insert(0, str(framework_root))

# Add roadmap-lib to path
roadmap_lib_path = Path(__file__).parent / "roadmap-lib"
sys.path.insert(0, str(roadmap_lib_path))

from roadmap.models import (
    Roadmap, VersionStrategy, Status, Progress, Metadata,
    ActivityType,
)
from roadmap.serialization import save_roadmap
from roadmap.validation import Validator
from filesystem import FileSystemManager
from activity import ActivityLogger


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
    bump_on_choices = [
        "sprint_completion",
        "track_completion",
        "manual",
    ]
    bump_on = prompt_choice(
        "When should version be bumped?",
        bump_on_choices,
        default="sprint_completion"
    )

    bump_type_choices = ["minor", "patch"]
    bump_type = prompt_choice(
        "What type of version bump?",
        bump_type_choices,
        default="minor"
    )

    initial_version = prompt_input("Initial version", "1.0.0")

    # Create roadmap
    version_strategy = VersionStrategy(
        bump_on=bump_on,
        bump_type=bump_type,
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

    now = datetime.utcnow()

    metadata = Metadata(
        created_by=prompt_input("Created by", "system"),
        last_modified_by="system",
        last_modified=now,
        tags=[],
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
            "bump_on": bump_on,
            "bump_type": bump_type,
        }
    )

    return roadmap


def create_roadmap_from_args(
    roadmap_id: str,
    roadmap_name: str,
    version: str,
    bump_on: str,
    bump_type: str,
    created_by: str,
) -> Roadmap:
    """Create roadmap from command-line arguments."""
    version_strategy = VersionStrategy(
        bump_on=bump_on,
        bump_type=bump_type,
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

    now = datetime.utcnow()

    metadata = Metadata(
        created_by=created_by,
        last_modified_by="system",
        last_modified=now,
        tags=[],
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
            "bump_on": bump_on,
            "bump_type": bump_type,
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
        "--bump-on",
        type=str,
        choices=["sprint_completion", "track_completion", "manual"],
        default="sprint_completion",
        help="When to bump version (default: sprint_completion)"
    )

    parser.add_argument(
        "--bump-type",
        type=str,
        choices=["minor", "patch"],
        default="minor",
        help="Version bump type (default: minor)"
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
    if args.id and args.name:
        # Non-interactive mode
        roadmap = create_roadmap_from_args(
            roadmap_id=args.id,
            roadmap_name=args.name,
            version=args.version,
            bump_on=args.bump_on,
            bump_type=args.bump_type,
            created_by=args.created_by,
        )
    else:
        # Interactive mode
        if args.id or args.name:
            print("❌ Both --id and --name are required for non-interactive mode")
            sys.exit(1)

        roadmap = create_roadmap_interactive(args.dir)

    # Validate roadmap
    validator = Validator()
    roadmap_dict = {
        "roadmap": {
            "id": roadmap.id,
            "name": roadmap.name,
            "version": roadmap.version,
            "version_strategy": {
                "bump_on": roadmap.version_strategy.bump_on,
                "bump_type": roadmap.version_strategy.bump_type,
            },
            "status": roadmap.status.value,
            "blocked": roadmap.blocked,
            "created": roadmap.created.isoformat(),
            "progress": {
                "tracks_total": roadmap.progress.tracks_total,
                "tracks_completed": roadmap.progress.tracks_completed,
                "sprints_total": roadmap.progress.sprints_total,
                "sprints_completed": roadmap.progress.sprints_completed,
                "tasks_total": roadmap.progress.tasks_total,
                "tasks_completed": roadmap.progress.tasks_completed,
                "completion_percent": roadmap.progress.completion_percent,
            },
            "tracks": [],
            "dependencies": [],
            "activity_log": [
                {
                    "timestamp": entry.timestamp.isoformat(),
                    "type": entry.type.value,
                    "description": entry.description,
                    "context": entry.context or {},
                }
                for entry in roadmap.activity_log
            ],
            "metadata": {
                "created_by": roadmap.metadata.created_by,
                "last_modified_by": roadmap.metadata.last_modified_by,
                "last_modified": roadmap.metadata.last_modified.isoformat(),
                "tags": roadmap.metadata.tags,
            }
        }
    }

    result = validator.validate_dict(roadmap_dict, "roadmap")
    if not result.valid:
        print(f"❌ Validation failed:")
        for error in result.errors:
            print(f"   - {error}")
        sys.exit(1)

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
