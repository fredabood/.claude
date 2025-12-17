"""
'roadmap add-standard' command - Add a new standard to roadmap/track/sprint.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

from ...roadmap.models import Standard, StandardType, EnforcementMode
from ...roadmap.serialization import (
    load_roadmap,
    save_roadmap,
    load_track,
    save_track,
    load_sprint,
    save_sprint,
)
from ...cli.roadmap_lib.filesystem import FileSystemManager


def handle_add_standard(args):
    """
    Handle 'roadmap add-standard' command.

    Adds a new standard to a roadmap, track, or sprint.

    Args:
        args: Parsed command-line arguments with:
            - level: Where to add (roadmap/track/sprint)
            - target_id: ID of roadmap/track/sprint (optional for roadmap)
            - standard_id: Unique ID for the standard
            - name: Display name
            - description: Description of what this standard enforces
            - type: Standard type (commit_check, file_check, test_run, custom_script)
            - enforcement: Enforcement mode (blocking, warning, audit)
            - validation: JSON string with validation config
            - dir: Optional root directory (defaults to current directory)

    Returns:
        Exit code: 0 for success, 1 for error
    """
    root_dir = Path(args.dir) if args.dir else Path.cwd()
    level = args.level
    target_id = getattr(args, 'target_id', None)
    standard_id = args.standard_id
    name = args.name
    description = args.description
    standard_type = args.type
    enforcement = args.enforcement
    validation_json = args.validation

    # Parse validation JSON
    try:
        validation = json.loads(validation_json)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid validation JSON: {e}")
        print('   Example: {"min_commits": 1}')
        return 1

    # Validate standard type
    try:
        std_type = StandardType(standard_type)
    except ValueError:
        print(f"❌ Invalid standard type: {standard_type}")
        print(f"   Valid types: commit_check, file_check, test_run, custom_script")
        return 1

    # Validate enforcement mode
    try:
        enf_mode = EnforcementMode(enforcement)
    except ValueError:
        print(f"❌ Invalid enforcement mode: {enforcement}")
        print(f"   Valid modes: blocking, warning, audit")
        return 1

    # Create standard
    try:
        standard = Standard(
            id=standard_id,
            name=name,
            description=description,
            type=std_type,
            enforcement=enf_mode,
            validation=validation,
            enabled=True,
            created=datetime.now(timezone.utc),
            overrides=[],
        )
    except Exception as e:
        print(f"❌ Failed to create standard: {e}")
        return 1

    # Add to appropriate level
    print(f"\n➕ Adding standard '{standard_id}' to {level}")
    print(f"   Type: {standard_type}")
    print(f"   Enforcement: {enforcement}")

    try:
        result = _add_standard_to_level(root_dir, level, target_id, standard)
    except Exception as e:
        print(f"\n❌ Failed to add standard: {e}")
        return 1

    if result:
        print(f"\n✅ Standard added successfully")
        print(f"   Location: {level}")
        if target_id:
            print(f"   Target: {target_id}")
        print(f"   ID: {standard_id}")
        print(f"   Status: Enabled")
        return 0
    else:
        print(f"\n❌ Failed to add standard")
        return 1


def _add_standard_to_level(
    root_dir: Path,
    level: str,
    target_id: str,
    standard: Standard
) -> bool:
    """
    Add a standard to the specified level.

    Args:
        root_dir: Root directory containing .vibey/
        level: Where to add (roadmap/track/sprint)
        target_id: ID of track/sprint (None for roadmap)
        standard: Standard object to add

    Returns:
        True if successful, False otherwise

    Raises:
        Exception if operation fails
    """
    fs = FileSystemManager(root_dir)

    if level == "roadmap":
        # Add to roadmap
        roadmap_path = fs.get_roadmap_path()
        if not roadmap_path.exists():
            raise FileNotFoundError(f"Roadmap not found at {roadmap_path}")

        roadmap = load_roadmap(roadmap_path)

        # Check if standard ID already exists
        if roadmap.get_standard(standard.id):
            raise ValueError(f"Standard '{standard.id}' already exists in roadmap")

        roadmap.add_standard(standard)
        save_roadmap(roadmap, roadmap_path)
        return True

    elif level == "track":
        if not target_id:
            raise ValueError("target_id is required for track level")

        track_path = fs.get_track_path(target_id)
        if not track_path.exists():
            raise FileNotFoundError(f"Track '{target_id}' not found")

        track = load_track(track_path)

        # Check if standard ID already exists
        if track.get_standard(standard.id):
            raise ValueError(f"Standard '{standard.id}' already exists in track '{target_id}'")

        track.add_standard(standard)
        save_track(track, track_path)
        return True

    elif level == "sprint":
        if not target_id:
            raise ValueError("target_id is required for sprint level")

        sprint_path = fs.get_sprint_path(target_id)
        if not sprint_path.exists():
            raise FileNotFoundError(f"Sprint '{target_id}' not found")

        sprint = load_sprint(sprint_path)

        # Check if standard ID already exists
        if sprint.get_standard(standard.id):
            raise ValueError(f"Standard '{standard.id}' already exists in sprint '{target_id}'")

        sprint.add_standard(standard)
        save_sprint(sprint, sprint_path)
        return True

    else:
        raise ValueError(f"Invalid level: {level}. Must be roadmap, track, or sprint")
