# Task 015: Update Validation to Accept ULID-based Sprint IDs

**Task ID:** dogfooding-bugs-02-task-015
**Bug Addressed:** #4 (Track model validation fails for ULID-based sprint IDs)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

The Track model validates that sprint IDs follow the format `{track_id}-{suffix}`. This fails for ULID-based sprint IDs which don't contain the track ID as a prefix.

**Example:**
- **Old format:** `sqlite-backend-4` (track: `sqlite-backend`, suffix: `4`)
- **New format:** `01KC3AD75P4TW2MAWDWJC4YCMB` (ULID, no embedded track ID)

---

## Current Implementation (Problematic)

```python
# vibey/roadmap/models/track.py (hypothetical current implementation)

class Track(BaseModel):
    id: str
    sprints: List[Sprint] = []

    @validator('sprints')
    def validate_sprint_ids(cls, sprints, values):
        track_id = values.get('id')
        for sprint in sprints:
            # This validation fails for ULID sprint IDs
            if not sprint.id.startswith(f"{track_id}-"):
                raise ValueError(
                    f"Sprint ID '{sprint.id}' must start with track ID '{track_id}-'"
                )
        return sprints
```

---

## Implementation

### New Validation Logic

```python
# vibey/roadmap/models/track.py

from vibey.roadmap.id_generator import is_ulid_format


class Track(BaseModel):
    id: str
    sprints: List[Sprint] = []

    @validator('sprints')
    def validate_sprint_ids(cls, sprints, values):
        """
        Validate sprint IDs belong to this track.

        Accepts:
        1. ULID format: 01KC3AD75P4TW2MAWDWJC4YCMB (validated via track_id reference)
        2. Slug format: {track_id}-{suffix} (validated via prefix)
        """
        track_id = values.get('id')

        for sprint in sprints:
            sprint_id = sprint.id

            # ULID format: validate via track_id reference in sprint
            if is_ulid_format(sprint_id):
                # For ULID sprints, trust the track_id reference field
                if hasattr(sprint, 'track_id') and sprint.track_id:
                    if sprint.track_id != track_id:
                        raise ValueError(
                            f"Sprint '{sprint_id}' has track_id '{sprint.track_id}' "
                            f"but is assigned to track '{track_id}'"
                        )
                # If no track_id reference, accept it (backwards compatibility)
                continue

            # Slug format: validate via prefix
            expected_prefix = f"{track_id}-"
            if not sprint_id.startswith(expected_prefix):
                raise ValueError(
                    f"Sprint ID '{sprint_id}' must start with '{expected_prefix}' "
                    f"or be a valid ULID"
                )

        return sprints
```

### Sprint Model Update

```python
# vibey/roadmap/models/sprint.py

class Sprint(BaseModel):
    id: str
    track_id: Optional[str] = None  # Reference to parent track (for ULID sprints)
    name: str
    status: Status = Status.NOT_STARTED
    tasks: List[Task] = []

    @validator('id')
    def validate_id_format(cls, v):
        """
        Validate sprint ID is either ULID or slug format.
        """
        if is_ulid_format(v):
            return v

        # Slug format: should contain at least one hyphen
        if '-' not in v:
            raise ValueError(
                f"Sprint ID '{v}' must be a ULID or slug format (e.g., 'track-1')"
            )

        return v
```

### Task Model Update

```python
# vibey/roadmap/models/task.py

class Task(BaseModel):
    id: str
    sprint_id: Optional[str] = None  # Reference to parent sprint (for ULID tasks)
    title: str
    status: Status = Status.NOT_STARTED

    @validator('id')
    def validate_id_format(cls, v):
        """
        Validate task ID is either ULID or slug format.
        """
        if is_ulid_format(v):
            return v

        # Slug format validation
        if '-task-' not in v and not v.startswith('task-'):
            raise ValueError(
                f"Task ID '{v}' must be a ULID or contain 'task-'"
            )

        return v
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/models/track.py` | Update sprint ID validation |
| `vibey/roadmap/models/sprint.py` | Add track_id reference, update ID validation |
| `vibey/roadmap/models/task.py` | Add sprint_id reference, update ID validation |
| `vibey/roadmap/id_generator.py` | Ensure `is_ulid_format()` is robust |

---

## Testing Strategy

```python
def test_track_accepts_ulid_sprint_ids():
    """Track model accepts ULID sprint IDs."""
    track = Track(
        id="01KC2D0JKTE7Z4HCNHST8ZVW4R",
        name="Test Track",
        sprints=[
            Sprint(
                id="01KC3AD75P4TW2MAWDWJC4YCMB",
                track_id="01KC2D0JKTE7Z4HCNHST8ZVW4R",
                name="Sprint 1",
            )
        ]
    )
    assert len(track.sprints) == 1


def test_track_accepts_slug_sprint_ids():
    """Track model accepts slug sprint IDs."""
    track = Track(
        id="sqlite-backend",
        name="SQLite Backend",
        sprints=[
            Sprint(id="sqlite-backend-1", name="Sprint 1"),
            Sprint(id="sqlite-backend-2", name="Sprint 2"),
        ]
    )
    assert len(track.sprints) == 2


def test_track_rejects_mismatched_slug_sprint():
    """Track model rejects slug sprint with wrong prefix."""
    with pytest.raises(ValidationError):
        Track(
            id="sqlite-backend",
            name="SQLite Backend",
            sprints=[
                Sprint(id="wrong-track-1", name="Sprint 1"),
            ]
        )


def test_track_rejects_mismatched_ulid_sprint():
    """Track model rejects ULID sprint with wrong track_id."""
    with pytest.raises(ValidationError):
        Track(
            id="01KC2D0JKTE7Z4HCNHST8ZVW4R",
            name="Test Track",
            sprints=[
                Sprint(
                    id="01KC3AD75P4TW2MAWDWJC4YCMB",
                    track_id="01KC2D0JKVT80AFQ6C1PA8CKJD",  # Different track!
                    name="Sprint 1",
                )
            ]
        )
```

---

## Success Criteria

- [ ] Track model accepts ULID sprint IDs
- [ ] Track model validates ULID sprints via track_id reference
- [ ] Track model still validates slug sprints via prefix
- [ ] Sprint/Task models have parent ID references
- [ ] All existing tests pass
- [ ] No false positives for valid IDs

---

## Dependencies

- None (can be done independently)

---

## Notes

The validation strategy differs by ID format:
- **ULID IDs**: Trust the `track_id`/`sprint_id` reference field
- **Slug IDs**: Validate via prefix/suffix pattern

This allows the system to work with both old and new formats simultaneously.
