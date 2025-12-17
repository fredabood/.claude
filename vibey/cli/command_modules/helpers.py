"""
Shared helper functions for CLI commands.

These utilities are used across multiple command modules for:
- ID resolution (slug <-> ULID)
- Path construction
- Type detection
"""

import re
from pathlib import Path
from typing import Optional


def slugify(name: str) -> str:
    """Convert a name to a URL-friendly slug."""
    # Lowercase, replace spaces with hyphens, remove non-alphanumeric
    slug = name.lower().strip()
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug)  # Collapse multiple hyphens
    return slug.strip('-')


def resolve_id(item_type: str, id_or_slug: str, root_dir: Path) -> str:
    """Resolve a slug or ULID to a ULID for the given item type."""
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager

    # If it looks like a ULID (26 chars, alphanumeric), return as-is
    if len(id_or_slug) == 26 and id_or_slug.isalnum() and id_or_slug.isupper():
        return id_or_slug

    # Otherwise, look up in .id file
    fs = FileSystemManager(root_dir)
    roadmap_root = fs.roadmap_root

    type_to_dir = {"track": "tracks", "sprint": "sprints", "task": "tasks"}
    id_file = roadmap_root / type_to_dir[item_type] / ".id"

    if id_file.exists():
        for line in id_file.read_text().strip().split("\n"):
            if "=" in line:
                slug, ulid = line.split("=", 1)
                if slug == id_or_slug:
                    return ulid

    # Not found, return as-is (will fail later if invalid)
    return id_or_slug


def get_roadmap_id(root_dir: Path) -> str:
    """Get the roadmap ID from the roadmap.yaml file."""
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager
    from vibey.roadmap.serialization.yaml_loader import load_roadmap

    fs = FileSystemManager(root_dir)
    roadmap_path = fs.get_roadmap_path()

    if not roadmap_path.exists():
        raise FileNotFoundError("Roadmap not found. Run 'vibey roadmap init' first.")

    roadmap = load_roadmap(roadmap_path)
    return roadmap.id


def update_id_mapping(item_type: str, slug: str, ulid: str, root_dir: Path):
    """Add a slug=ULID mapping to the .id file."""
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager

    fs = FileSystemManager(root_dir)
    roadmap_root = fs.roadmap_root

    type_to_dir = {"track": "tracks", "sprint": "sprints", "task": "tasks"}
    id_file = roadmap_root / type_to_dir[item_type] / ".id"

    # Read existing content
    if id_file.exists():
        content = id_file.read_text()
        if not content.endswith("\n"):
            content += "\n"
    else:
        content = ""

    # Add new mapping
    content += f"{slug}={ulid}\n"
    id_file.write_text(content)


def get_slug_for_ulid(item_type: str, ulid: str, root_dir: Path) -> Optional[str]:
    """Get the slug for a given ULID from .id file."""
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager

    fs = FileSystemManager(root_dir)
    roadmap_root = fs.roadmap_root

    type_to_dir = {"track": "tracks", "sprint": "sprints", "task": "tasks"}
    id_file = roadmap_root / type_to_dir[item_type] / ".id"

    if id_file.exists():
        for line in id_file.read_text().strip().split("\n"):
            if "=" in line:
                slug, file_ulid = line.split("=", 1)
                if file_ulid == ulid:
                    return slug
    return None


def detect_ulid_type(item_id: str, root_dir: Path) -> Optional[str]:
    """
    Detect item type from ULID by checking .id files.

    Returns: "track", "sprint", "task", or None if not found
    """
    roadmap_root = root_dir / ".vibey" / "roadmap"

    # Check each type's .id file for the ULID
    for item_type, subdir in [("task", "tasks"), ("sprint", "sprints"), ("track", "tracks")]:
        id_file = roadmap_root / subdir / ".id"
        if id_file.exists():
            content = id_file.read_text()
            # Check if ULID appears as a value (slug=ULID format)
            if f"={item_id}" in content or f"={item_id}\n" in content:
                return item_type

    return None


# Aliases for backwards compatibility with existing code
_slugify = slugify
_resolve_id = resolve_id
_get_roadmap_id = get_roadmap_id
_update_id_mapping = update_id_mapping
_get_slug_for_ulid = get_slug_for_ulid
_detect_ulid_type = detect_ulid_type
