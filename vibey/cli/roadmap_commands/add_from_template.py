"""
'roadmap add-from-template' command - Add a standard from a template.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

from ...roadmap.standards.templates import load_template, get_template_info
from ...roadmap.serialization import (
    load_roadmap,
    save_roadmap,
    load_track,
    save_track,
    load_sprint,
    save_sprint,
)
from ...cli.roadmap_lib.filesystem import FileSystemManager


def handle_add_from_template(args):
    """
    Handle 'roadmap add-from-template' command.

    Adds a standard to roadmap/track/sprint from a pre-built template.

    Args:
        args: Parsed command-line arguments with:
            - template_id: Template ID to load
            - level: Where to add (roadmap/track/sprint)
            - target_id: ID of track/sprint (required for track/sprint level)
            - custom_id: Optional custom standard ID (overrides template ID)
            - enforcement: Optional enforcement override
            - dir: Optional root directory (defaults to current directory)
            - show_info: Optional flag to show template info before adding

    Returns:
        Exit code: 0 for success, 1 for error
    """
    root_dir = Path(args.dir) if args.dir else Path.cwd()
    template_id = args.template_id
    level = args.level
    target_id = getattr(args, 'target_id', None)
    custom_id = getattr(args, 'custom_id', None)
    enforcement_override = getattr(args, 'enforcement', None)
    show_info = getattr(args, 'show_info', False)

    # Show template info if requested
    if show_info:
        _show_template_info(template_id)
        return 0

    print(f"\n➕ Adding standard from template '{template_id}' to {level}")

    # Load template
    try:
        overrides = {}
        if custom_id:
            overrides['id'] = custom_id
        if enforcement_override:
            overrides['enforcement'] = enforcement_override

        standard = load_template(template_id, **overrides)

        if not standard:
            print(f"\n❌ Template '{template_id}' not found")
            print(f"   Use 'vibey roadmap list-templates' to see available templates")
            return 1

    except Exception as e:
        print(f"\n❌ Failed to load template: {e}")
        return 1

    # Add standard to appropriate level
    print(f"\n   Standard ID: {standard.id}")
    print(f"   Name: {standard.name}")
    print(f"   Type: {standard.type.value}")
    print(f"   Enforcement: {standard.enforcement.value}")

    try:
        result = _add_standard_to_level(root_dir, level, target_id, standard)
    except Exception as e:
        print(f"\n❌ Failed to add standard: {e}")
        return 1

    if result:
        print(f"\n✅ Standard added successfully from template")
        print(f"   Location: {level}")
        if target_id:
            print(f"   Target: {target_id}")
        print(f"   Template: {template_id}")
        print(f"   Standard ID: {standard.id}")
        print(f"   Status: Enabled")
        print(f"\n💡 Next steps:")
        print(f"   - Check standards: vibey roadmap check-standards <item-id>")
        print(f"   - View template info: vibey roadmap list-templates --verbose")
        return 0
    else:
        print(f"\n❌ Failed to add standard")
        return 1


def _add_standard_to_level(
    root_dir: Path,
    level: str,
    target_id: str,
    standard
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


def _show_template_info(template_id: str):
    """Show detailed information about a template."""
    info = get_template_info(template_id)

    if not info:
        print(f"\n❌ Template '{template_id}' not found")
        return

    print(f"\n📋 Template: {template_id}")
    print("=" * 80)

    name = info.get('name', 'Unknown')
    description = info.get('description', '')
    template_type = info.get('type', 'unknown')
    enforcement = info.get('enforcement', 'unknown')

    print(f"\nName: {name}")
    print(f"Type: {template_type}")
    print(f"Enforcement: {enforcement}")
    print(f"Description: {description}")

    use_case = info.get('use_case', '').strip()
    if use_case:
        print(f"\nUse Case:")
        for line in use_case.split('\n'):
            if line.strip():
                print(f"  {line.strip()}")

    typical_level = info.get('typical_level', '')
    if typical_level:
        print(f"\nTypical Level: {typical_level}")

    validation = info.get('validation', {})
    if validation:
        print(f"\nDefault Validation Config:")
        for key, value in validation.items():
            print(f"  {key}: {value}")

    examples = info.get('examples', [])
    if examples:
        print(f"\nUsage Examples:")
        for i, example in enumerate(examples, 1):
            print(f"\n  Example {i}:")
            print(f"    Level: {example.get('level', 'unknown')}")
            print(f"    Scenario: {example.get('scenario', '')}")
            print(f"    {example.get('description', '')}")

    override_scenarios = info.get('override_scenarios', [])
    if override_scenarios:
        print(f"\nCommon Override Scenarios:")
        for scenario in override_scenarios:
            reason = scenario.get('reason', '')
            justification = scenario.get('justification', '')
            print(f"  • {reason}")
            print(f"    → {justification}")

    print("\n" + "=" * 80)
