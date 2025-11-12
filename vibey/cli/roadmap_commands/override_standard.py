"""
'roadmap override-standard' command - Override a standard for a specific item.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

from ...roadmap.standards import StandardsResolver
from ...roadmap.serialization import save_roadmap, save_track, save_sprint
from ...cli.roadmap_lib.filesystem import FileSystemManager


def handle_override_standard(args):
    """
    Handle 'roadmap override-standard' command.

    Adds an override to a standard for a specific item, allowing completion
    even if the standard would normally block it. The override is tracked
    with reason and who created it.

    Args:
        args: Parsed command-line arguments with:
            - standard_id: ID of the standard to override
            - item_id: ID of item to apply override to (task/sprint/track)
            - reason: Justification for override
            - dir: Optional root directory (defaults to current directory)
            - overridden_by: Who is creating the override (optional)

    Returns:
        Exit code: 0 for success, 1 for error
    """
    root_dir = Path(args.dir) if args.dir else Path.cwd()
    standard_id = args.standard_id
    item_id = args.item_id
    reason = args.reason
    overridden_by = getattr(args, 'overridden_by', 'system')

    print(f"\n🔓 Creating override for standard '{standard_id}' on item '{item_id}'")
    print(f"   Reason: {reason}")
    print(f"   By: {overridden_by}")

    # Find which level the standard is defined at and add override
    try:
        result = _add_override_to_standard(
            root_dir,
            standard_id,
            item_id,
            reason,
            overridden_by
        )
    except Exception as e:
        print(f"\n❌ Failed to add override: {e}")
        return 1

    if result:
        level, obj_id = result
        print(f"\n✅ Override added successfully")
        print(f"   Standard location: {level} '{obj_id}'")
        print(f"   Applies to: {item_id}")
        print(f"   Status: Active (no expiration)")
        return 0
    else:
        print(f"\n❌ Standard '{standard_id}' not found in roadmap hierarchy")
        return 1


def _add_override_to_standard(
    root_dir: Path,
    standard_id: str,
    item_id: str,
    reason: str,
    overridden_by: str
) -> tuple:
    """
    Find and add override to a standard.

    Searches roadmap, then track, then sprint for the standard.
    Adds override to the first occurrence found.

    Args:
        root_dir: Root directory containing .vibey/
        standard_id: ID of standard to override
        item_id: Target item ID for override
        reason: Justification
        overridden_by: Who is overriding

    Returns:
        Tuple of (level, object_id) if found, None otherwise
        Example: ("roadmap", "my-roadmap") or ("track", "backend")

    Raises:
        Exception if standard not found or save fails
    """
    from ...roadmap.serialization import load_roadmap, load_track, load_sprint

    fs = FileSystemManager(root_dir)

    # Try roadmap level first
    roadmap_path = fs.get_roadmap_path()
    if roadmap_path.exists():
        roadmap = load_roadmap(roadmap_path)

        standard = roadmap.get_standard(standard_id)
        if standard:
            # Add override
            standard.add_override(
                target_id=item_id,
                reason=reason,
                overridden_by=overridden_by
            )
            # Save roadmap
            save_roadmap(roadmap, roadmap_path)
            return ("roadmap", roadmap.id)

    # Extract track/sprint IDs from item_id
    track_id, sprint_id = _extract_ids_from_item(item_id)

    # Try track level
    if track_id:
        track_path = fs.get_track_path(track_id)
        if track_path.exists():
            track = load_track(track_path)

            standard = track.get_standard(standard_id)
            if standard:
                # Add override
                standard.add_override(
                    target_id=item_id,
                    reason=reason,
                    overridden_by=overridden_by
                )
                # Save track
                save_track(track, track_path)
                return ("track", track.id)

    # Try sprint level
    if sprint_id:
        sprint_path = fs.get_sprint_path(sprint_id)
        if sprint_path.exists():
            sprint = load_sprint(sprint_path)

            standard = sprint.get_standard(standard_id)
            if standard:
                # Add override
                standard.add_override(
                    target_id=item_id,
                    reason=reason,
                    overridden_by=overridden_by
                )
                # Save sprint
                save_sprint(sprint, sprint_path)
                return ("sprint", sprint.id)

    # Not found at any level
    return None


def _extract_ids_from_item(item_id: str) -> tuple:
    """
    Extract track_id and sprint_id from item_id.

    Args:
        item_id: Task, sprint, or track ID

    Returns:
        Tuple of (track_id, sprint_id)
        - For tasks: (track_id, sprint_id)
        - For sprints: (track_id, sprint_id)
        - For tracks: (track_id, None)
    """
    if '-task-' in item_id:
        # Task ID format: {sprint-id}-task-{num}
        sprint_id = item_id.split('-task-')[0]
        track_id = sprint_id.rsplit('-', 1)[0]
        return (track_id, sprint_id)
    elif item_id.count('-') >= 1:
        # Sprint ID format: {track-id}-{num}
        sprint_id = item_id
        track_id = item_id.rsplit('-', 1)[0]
        return (track_id, sprint_id)
    else:
        # Track ID
        return (item_id, None)
