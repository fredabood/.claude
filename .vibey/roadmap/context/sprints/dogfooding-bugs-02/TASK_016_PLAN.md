# Task 016: Add Backward Compatibility for Slug-based IDs

**Task ID:** dogfooding-bugs-02-task-016
**Bug Addressed:** #4 (Track model validation fails for ULID-based sprint IDs)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

The system must support both ULID-based and slug-based IDs during the migration period and potentially forever for legacy projects that don't want to migrate.

---

## Compatibility Requirements

### ID Format Examples

| Entity | Slug Format | ULID Format |
|--------|-------------|-------------|
| Track | `sqlite-backend` | `01KC2D0JKTE7Z4HCNHST8ZVW4R` |
| Sprint | `sqlite-backend-4` | `01KC3AD75P4TW2MAWDWJC4YCMB` |
| Task | `sqlite-backend-4-task-001` | `01KC3AD75P4TW2MAWDWJC4YCMC` |

### Scenarios to Support

1. **Pure ULID** - New projects using flat structure
2. **Pure Slug** - Legacy projects using nested structure
3. **Mixed** - Projects in migration (some ULID, some slug)

---

## Implementation

### ID Format Detection Utility

```python
# vibey/roadmap/id_utils.py

import re
from typing import Literal, Optional, Tuple


# ULID pattern: 26 characters, Crockford base32
ULID_PATTERN = re.compile(r'^[0-9A-HJKMNP-TV-Z]{26}$', re.IGNORECASE)

# Slug patterns
TRACK_SLUG_PATTERN = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
SPRINT_SLUG_PATTERN = re.compile(r'^([a-z0-9]+(-[a-z0-9]+)*)-(\d+|[a-z]+)$')
TASK_SLUG_PATTERN = re.compile(r'^([a-z0-9]+(-[a-z0-9]+)*)-task-(\d+)$')


def detect_id_format(id_value: str) -> Literal["ulid", "slug", "unknown"]:
    """
    Detect the format of an ID.

    Returns:
        "ulid" - Standard ULID format
        "slug" - Slug-based format (kebab-case)
        "unknown" - Unrecognized format
    """
    if ULID_PATTERN.match(id_value):
        return "ulid"
    if TRACK_SLUG_PATTERN.match(id_value):
        return "slug"
    return "unknown"


def parse_slug_sprint_id(sprint_id: str) -> Optional[Tuple[str, str]]:
    """
    Parse a slug sprint ID into (track_id, suffix).

    Args:
        sprint_id: e.g., "sqlite-backend-4"

    Returns:
        Tuple of (track_id, suffix) or None if not a slug format
    """
    match = SPRINT_SLUG_PATTERN.match(sprint_id)
    if match:
        # Everything before the last hyphen-component is track_id
        parts = sprint_id.rsplit('-', 1)
        return (parts[0], parts[1])
    return None


def parse_slug_task_id(task_id: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse a slug task ID into (track_id, sprint_suffix, task_number).

    Args:
        task_id: e.g., "sqlite-backend-4-task-001"

    Returns:
        Tuple of (track_id, sprint_suffix, task_num) or None
    """
    match = TASK_SLUG_PATTERN.match(task_id)
    if match:
        # Parse "sqlite-backend-4-task-001" -> ("sqlite-backend", "4", "001")
        base = match.group(1)
        task_num = match.group(3)
        # Find sprint suffix
        sprint_match = SPRINT_SLUG_PATTERN.match(base)
        if sprint_match:
            track_id = sprint_match.group(1)
            suffix = sprint_match.group(3)
            return (track_id, suffix, task_num)
    return None


def normalize_id_for_comparison(id1: str, id2: str) -> bool:
    """
    Compare two IDs that may be in different formats.

    Handles the case where the same entity might be referenced
    by ULID in one place and slug in another (via mapping).
    """
    # Direct match
    if id1 == id2:
        return True

    # Both should be same format for comparison
    format1 = detect_id_format(id1)
    format2 = detect_id_format(id2)

    # If different formats, use mapping files (.id) to resolve
    # This is handled by FileSystemManager.resolve_id()
    return False
```

### Backward Compatible Loading

```python
# vibey/roadmap/serialization/yaml_loader.py

def load_track_with_sprints(
    track_id: str,
    tracks_dir: Path,
    sprints_dir: Path,
) -> Track:
    """
    Load a track with its sprints, supporting both ID formats.
    """
    id_format = detect_id_format(track_id)

    if id_format == "ulid":
        # ULID: Load from tracks/{ulid}.yaml
        track_path = tracks_dir / f"{track_id}.yaml"

        # Find sprints by track_id reference in sprint files
        sprints = []
        for sprint_file in sprints_dir.glob("*.yaml"):
            sprint_data = yaml.safe_load(sprint_file.read_text())
            if sprint_data.get('sprint', {}).get('track_id') == track_id:
                sprints.append(load_sprint(sprint_file))

    else:
        # Slug: Load from tracks/{slug}.yaml or {slug}/track.yaml
        track_path = tracks_dir / f"{track_id}.yaml"
        if not track_path.exists():
            # Try nested structure
            track_path = tracks_dir.parent / track_id / "track.yaml"

        # Find sprints by ID prefix
        sprints = []
        for sprint_file in sprints_dir.glob("*.yaml"):
            sprint_id = sprint_file.stem
            parsed = parse_slug_sprint_id(sprint_id)
            if parsed and parsed[0] == track_id:
                sprints.append(load_sprint(sprint_file))

    track_data = yaml.safe_load(track_path.read_text())
    track = Track(**track_data['track'])
    track.sprints = sprints

    return track
```

### ID Resolution in FileSystemManager

```python
# vibey/cli/roadmap_lib/filesystem.py

class FileSystemManager:
    def resolve_id(self, entity_type: str, id_or_slug: str) -> str:
        """
        Resolve a slug to ULID or return ULID as-is.

        Uses .id mapping files if available.

        Args:
            entity_type: 'track', 'sprint', or 'task'
            id_or_slug: Either a ULID or a slug

        Returns:
            The canonical ID (ULID if available, else slug)
        """
        if is_ulid_format(id_or_slug):
            return id_or_slug

        # Check for .id mapping file
        id_file = self.roadmap_root / f"{entity_type}s" / ".id"
        if id_file.exists():
            mapping = yaml.safe_load(id_file.read_text())
            if id_or_slug in mapping:
                return mapping[id_or_slug]

        # No mapping, use slug as-is
        return id_or_slug

    def reverse_resolve_id(self, entity_type: str, ulid: str) -> Optional[str]:
        """
        Get the slug for a ULID if a mapping exists.

        Useful for display purposes.
        """
        if not is_ulid_format(ulid):
            return ulid  # Already a slug

        id_file = self.roadmap_root / f"{entity_type}s" / ".id"
        if id_file.exists():
            mapping = yaml.safe_load(id_file.read_text())
            # Reverse lookup
            for slug, mapped_ulid in mapping.items():
                if mapped_ulid == ulid:
                    return slug

        return None  # No slug available
```

---

## Files to Create/Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/id_utils.py` | NEW: ID format detection and parsing |
| `vibey/roadmap/serialization/yaml_loader.py` | Update loading for both formats |
| `vibey/cli/roadmap_lib/filesystem.py` | Add resolve_id/reverse_resolve_id |

---

## Testing Strategy

```python
class TestIdFormatDetection:
    """Test ID format detection."""

    def test_detect_ulid(self):
        assert detect_id_format("01KC2D0JKTE7Z4HCNHST8ZVW4R") == "ulid"

    def test_detect_slug(self):
        assert detect_id_format("sqlite-backend") == "slug"
        assert detect_id_format("sqlite-backend-4") == "slug"

    def test_detect_unknown(self):
        assert detect_id_format("invalid_id!") == "unknown"


class TestSlugParsing:
    """Test slug ID parsing."""

    def test_parse_sprint_slug(self):
        result = parse_slug_sprint_id("sqlite-backend-4")
        assert result == ("sqlite-backend", "4")

    def test_parse_task_slug(self):
        result = parse_slug_task_id("sqlite-backend-4-task-001")
        assert result == ("sqlite-backend", "4", "001")


class TestBackwardCompatibleLoading:
    """Test loading with both ID formats."""

    def test_load_track_ulid_format(self, flat_roadmap):
        """Load track with ULID ID."""
        track = load_track_with_sprints(
            "01KC2D0JKTE7Z4HCNHST8ZVW4R",
            flat_roadmap / "tracks",
            flat_roadmap / "sprints",
        )
        assert track is not None

    def test_load_track_slug_format(self, nested_roadmap):
        """Load track with slug ID."""
        track = load_track_with_sprints(
            "sqlite-backend",
            nested_roadmap,
            nested_roadmap / "sqlite-backend",
        )
        assert track is not None
```

---

## Success Criteria

- [ ] ULID IDs detected correctly
- [ ] Slug IDs detected correctly
- [ ] Sprint/task slugs parsed correctly
- [ ] Loading works for both formats
- [ ] ID resolution via .id files works
- [ ] Mixed format projects work

---

## Dependencies

- Task 015 (validation accepts both formats)

---

## Notes

This backward compatibility layer ensures:
1. Legacy projects continue to work
2. New projects can use ULIDs
3. Migration can be gradual
4. No breaking changes for existing users

The `.id` mapping files are optional but enable slug-based access to ULID entities.
