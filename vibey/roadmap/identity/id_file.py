"""
.id File Format - Slug ↔ ULID Bidirectional Mapping

This module handles .id files that map human-readable slugs to immutable ULIDs.

File Format:
    # Vibey Roadmap ID Mapping File
    # Format: slug=ulid
    # Generated: 2025-12-09T20:31:58.079378+00:00

    aider-port=01KC2D0JK06MN77ZHAGAHF5VKB
    documentation-system=01KC2D0JK49XGJV84YRRHEASMG

Key Concepts:
    - Slug: Human-readable identifier (mutable, used in directory/URL paths)
    - ULID: Universally Unique Lexicographically Sortable Identifier (immutable)
    - Bidirectional: Can lookup by slug OR by ULID
    - Rename Support: Updating slug doesn't change ULID (preserves references)

Usage:
    # Load existing mapping
    mapping = IdMappingFile(Path('.vibey/roadmap/tracks/.id'))

    # Get ULID for a slug
    ulid = mapping.get_ulid('documentation-system')

    # Get slug for a ULID
    slug = mapping.get_slug('01KC2D0JK49XGJV84YRRHEASMG')

    # Register new mapping
    mapping.register('new-track', '01KC2VTQ2JNFQJ2XYXHFPG2SS7')
    mapping.save()

    # Rename slug (ULID preserved)
    mapping.rename_slug('old-name', 'new-name')
    mapping.save()
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, List, Tuple


class IdMappingFile:
    """
    Manages .id files for slug ↔ ULID bidirectional mapping.

    The .id file format is a simple text file with one mapping per line:
        slug=ulid

    Both directions are indexed for O(1) lookups.
    """

    def __init__(self, file_path: Path):
        """
        Initialize ID mapping file.

        Args:
            file_path: Path to .id file (will be created if doesn't exist)
        """
        self.file_path = file_path
        self.slug_to_ulid: Dict[str, str] = {}
        self.ulid_to_slug: Dict[str, str] = {}

        if file_path.exists():
            self.load()

    def load(self) -> None:
        """
        Load mappings from .id file.

        File format:
            # Comments start with #
            slug=ulid
        """
        with open(self.file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if '=' in line:
                    slug, ulid = line.split('=', 1)
                    self.slug_to_ulid[slug] = ulid
                    self.ulid_to_slug[ulid] = slug

    def save(self) -> None:
        """
        Save mappings to .id file.

        Creates parent directories if needed.
        Writes sorted by slug for consistent output.
        """
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.file_path, 'w') as f:
            f.write("# Vibey Roadmap ID Mapping File\n")
            f.write("# Format: slug=ulid\n")
            f.write(f"# Generated: {datetime.now(timezone.utc).isoformat()}\n")
            f.write("\n")

            for slug in sorted(self.slug_to_ulid.keys()):
                f.write(f"{slug}={self.slug_to_ulid[slug]}\n")

    def register(self, slug: str, ulid: str) -> None:
        """
        Register a new slug ↔ ULID mapping.

        Args:
            slug: Human-readable identifier
            ulid: ULID identifier

        Note: Does not automatically save. Call save() after registering.
        """
        self.slug_to_ulid[slug] = ulid
        self.ulid_to_slug[ulid] = slug

    def unregister(self, slug: str) -> Optional[str]:
        """
        Remove a mapping by slug.

        Args:
            slug: Slug to remove

        Returns:
            The ULID that was mapped to this slug, or None if not found
        """
        if slug in self.slug_to_ulid:
            ulid = self.slug_to_ulid.pop(slug)
            self.ulid_to_slug.pop(ulid, None)
            return ulid
        return None

    def get_ulid(self, slug: str) -> Optional[str]:
        """
        Get ULID for a slug.

        Args:
            slug: Human-readable identifier

        Returns:
            ULID string or None if not found
        """
        return self.slug_to_ulid.get(slug)

    def get_slug(self, ulid: str) -> Optional[str]:
        """
        Get slug for a ULID.

        Args:
            ulid: ULID identifier

        Returns:
            Slug string or None if not found
        """
        return self.ulid_to_slug.get(ulid)

    def rename_slug(self, old_slug: str, new_slug: str) -> bool:
        """
        Rename a slug while preserving the ULID.

        This is the key benefit of the ULID system - renaming doesn't
        break references because the ULID remains the same.

        Args:
            old_slug: Current slug
            new_slug: New slug

        Returns:
            True if rename succeeded, False if old_slug not found

        Note: Does not automatically save. Call save() after renaming.
        """
        if old_slug not in self.slug_to_ulid:
            return False

        ulid = self.slug_to_ulid.pop(old_slug)
        self.slug_to_ulid[new_slug] = ulid
        self.ulid_to_slug[ulid] = new_slug
        return True

    def has_slug(self, slug: str) -> bool:
        """Check if a slug exists in the mapping."""
        return slug in self.slug_to_ulid

    def has_ulid(self, ulid: str) -> bool:
        """Check if a ULID exists in the mapping."""
        return ulid in self.ulid_to_slug

    def all_slugs(self) -> List[str]:
        """Get all registered slugs."""
        return list(self.slug_to_ulid.keys())

    def all_ulids(self) -> List[str]:
        """Get all registered ULIDs."""
        return list(self.ulid_to_slug.keys())

    def all_mappings(self) -> List[Tuple[str, str]]:
        """Get all (slug, ulid) pairs."""
        return [(slug, self.slug_to_ulid[slug]) for slug in sorted(self.slug_to_ulid.keys())]

    def __len__(self) -> int:
        """Number of mappings."""
        return len(self.slug_to_ulid)

    def __contains__(self, key: str) -> bool:
        """Check if key exists as either slug or ULID."""
        return key in self.slug_to_ulid or key in self.ulid_to_slug

    def __repr__(self) -> str:
        return f"IdMappingFile({self.file_path}, {len(self)} mappings)"


# Convenience functions for common operations

def load_id_mapping(roadmap_dir: Path, entity_type: str) -> IdMappingFile:
    """
    Load ID mapping file for a specific entity type.

    Args:
        roadmap_dir: Path to .vibey/roadmap directory
        entity_type: 'tracks', 'sprints', or 'tasks'

    Returns:
        IdMappingFile instance

    Example:
        mapping = load_id_mapping(Path('.vibey/roadmap'), 'tracks')
        ulid = mapping.get_ulid('documentation-system')
    """
    id_file = roadmap_dir / entity_type / '.id'
    return IdMappingFile(id_file)


def get_ulid_for_slug(roadmap_dir: Path, entity_type: str, slug: str) -> Optional[str]:
    """
    Quick lookup of ULID for a slug.

    Args:
        roadmap_dir: Path to .vibey/roadmap directory
        entity_type: 'tracks', 'sprints', or 'tasks'
        slug: Human-readable identifier

    Returns:
        ULID string or None if not found

    Example:
        ulid = get_ulid_for_slug(Path('.vibey/roadmap'), 'tracks', 'documentation-system')
    """
    mapping = load_id_mapping(roadmap_dir, entity_type)
    return mapping.get_ulid(slug)


def get_slug_for_ulid(roadmap_dir: Path, entity_type: str, ulid: str) -> Optional[str]:
    """
    Quick lookup of slug for a ULID.

    Args:
        roadmap_dir: Path to .vibey/roadmap directory
        entity_type: 'tracks', 'sprints', or 'tasks'
        ulid: ULID identifier

    Returns:
        Slug string or None if not found

    Example:
        slug = get_slug_for_ulid(Path('.vibey/roadmap'), 'tracks', '01KC2D0JK49XGJV84YRRHEASMG')
    """
    mapping = load_id_mapping(roadmap_dir, entity_type)
    return mapping.get_slug(ulid)


if __name__ == "__main__":
    # Demo usage
    print("=== .id File Format Demo ===\n")

    # Create a temporary mapping
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        id_file = Path(tmpdir) / "tracks" / ".id"

        # Create mapping
        mapping = IdMappingFile(id_file)
        mapping.register("documentation-system", "01KC2D0JK49XGJV84YRRHEASMG")
        mapping.register("sqlite-backend", "01KC2D0JK7READW9KAK1HBX4BS")
        mapping.save()

        print(f"Created {len(mapping)} mappings")
        print(f"File: {id_file}")
        print()

        # Read file contents
        print("File contents:")
        print("-" * 40)
        print(id_file.read_text())
        print("-" * 40)
        print()

        # Lookups
        print("Lookups:")
        print(f"  documentation-system -> {mapping.get_ulid('documentation-system')}")
        print(f"  01KC2D0JK49XGJV84YRRHEASMG -> {mapping.get_slug('01KC2D0JK49XGJV84YRRHEASMG')}")
        print()

        # Rename
        mapping.rename_slug("documentation-system", "docs-system")
        mapping.save()
        print("After rename (documentation-system -> docs-system):")
        print(f"  docs-system -> {mapping.get_ulid('docs-system')}")
        print(f"  (ULID unchanged, references still valid)")
