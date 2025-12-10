# Task 017: Add Unit Tests for Both ID Formats

**Task ID:** dogfooding-bugs-02-task-017
**Bug Addressed:** #4 (Track model validation fails for ULID-based sprint IDs)
**Complexity:** Medium
**Type:** Testing

---

## Problem Statement

Comprehensive unit tests are needed to verify that the system correctly handles both ULID and slug ID formats across all operations.

---

## Test Categories

### 1. ID Format Detection Tests

```python
# tests/roadmap/test_id_utils.py

import pytest
from vibey.roadmap.id_utils import (
    detect_id_format,
    parse_slug_sprint_id,
    parse_slug_task_id,
    ULID_PATTERN,
)


class TestUlidPattern:
    """Test ULID pattern matching."""

    @pytest.mark.parametrize("valid_ulid", [
        "01KC2D0JKTE7Z4HCNHST8ZVW4R",
        "01KC3AD75P4TW2MAWDWJC4YCMB",
        "01KC3AD76EK6TBPW0GEJD0P4M0",
        "00000000000000000000000000",  # Valid but unlikely
        "7ZZZZZZZZZZZZZZZZZZZZZZZZZ",  # Max ULID
    ])
    def test_valid_ulids(self, valid_ulid):
        assert ULID_PATTERN.match(valid_ulid)

    @pytest.mark.parametrize("invalid_ulid", [
        "01KC2D0JKTE7Z4HCNHST8ZVW4",   # Too short (25 chars)
        "01KC2D0JKTE7Z4HCNHST8ZVW4RX",  # Too long (27 chars)
        "01KC2D0JKTE7Z4HCNHST8ZVW4!",   # Invalid char
        "01KC2D0JKTE7Z4HCNHST8ZVWIR",   # Contains I
        "01KC2D0JKTE7Z4HCNHST8ZVWLR",   # Contains L
        "01KC2D0JKTE7Z4HCNHST8ZVWOR",   # Contains O
        "01KC2D0JKTE7Z4HCNHST8ZVWUR",   # Contains U
        "sqlite-backend-4",              # Slug format
        "",                              # Empty
    ])
    def test_invalid_ulids(self, invalid_ulid):
        assert not ULID_PATTERN.match(invalid_ulid)


class TestIdFormatDetection:
    """Test ID format detection."""

    @pytest.mark.parametrize("ulid_id", [
        "01KC2D0JKTE7Z4HCNHST8ZVW4R",
        "01KC3AD75P4TW2MAWDWJC4YCMB",
    ])
    def test_detects_ulid(self, ulid_id):
        assert detect_id_format(ulid_id) == "ulid"

    @pytest.mark.parametrize("slug_id", [
        "sqlite-backend",
        "sqlite-backend-4",
        "sqlite-backend-4-task-001",
        "my-project",
        "test-track-1",
    ])
    def test_detects_slug(self, slug_id):
        assert detect_id_format(slug_id) == "slug"

    @pytest.mark.parametrize("unknown_id", [
        "invalid_id!",
        "has spaces",
        "UPPERCASE",
        "mixed-CASE-123",
    ])
    def test_detects_unknown(self, unknown_id):
        assert detect_id_format(unknown_id) == "unknown"


class TestSlugParsing:
    """Test slug ID parsing."""

    @pytest.mark.parametrize("sprint_id,expected", [
        ("sqlite-backend-4", ("sqlite-backend", "4")),
        ("my-track-1", ("my-track", "1")),
        ("test-a", ("test", "a")),
        ("a-b-c-d-1", ("a-b-c-d", "1")),
    ])
    def test_parse_sprint_slug(self, sprint_id, expected):
        assert parse_slug_sprint_id(sprint_id) == expected

    @pytest.mark.parametrize("invalid_sprint", [
        "noprefix",
        "01KC2D0JKTE7Z4HCNHST8ZVW4R",  # ULID, not slug
    ])
    def test_parse_sprint_slug_invalid(self, invalid_sprint):
        assert parse_slug_sprint_id(invalid_sprint) is None

    @pytest.mark.parametrize("task_id,expected", [
        ("sqlite-backend-4-task-001", ("sqlite-backend", "4", "001")),
        ("my-track-1-task-012", ("my-track", "1", "012")),
    ])
    def test_parse_task_slug(self, task_id, expected):
        assert parse_slug_task_id(task_id) == expected
```

### 2. Model Validation Tests

```python
# tests/roadmap/models/test_id_validation.py

import pytest
from pydantic import ValidationError
from vibey.roadmap.models import Track, Sprint, Task


class TestTrackIdValidation:
    """Test Track model ID validation."""

    def test_track_ulid_id(self):
        """Track accepts ULID ID."""
        track = Track(
            id="01KC2D0JKTE7Z4HCNHST8ZVW4R",
            name="Test Track",
        )
        assert track.id == "01KC2D0JKTE7Z4HCNHST8ZVW4R"

    def test_track_slug_id(self):
        """Track accepts slug ID."""
        track = Track(
            id="sqlite-backend",
            name="SQLite Backend",
        )
        assert track.id == "sqlite-backend"


class TestSprintIdValidation:
    """Test Sprint model ID validation."""

    def test_sprint_ulid_id(self):
        """Sprint accepts ULID ID."""
        sprint = Sprint(
            id="01KC3AD75P4TW2MAWDWJC4YCMB",
            track_id="01KC2D0JKTE7Z4HCNHST8ZVW4R",
            name="Sprint 1",
        )
        assert sprint.id == "01KC3AD75P4TW2MAWDWJC4YCMB"

    def test_sprint_slug_id(self):
        """Sprint accepts slug ID."""
        sprint = Sprint(
            id="sqlite-backend-4",
            name="Sprint 4",
        )
        assert sprint.id == "sqlite-backend-4"


class TestTaskIdValidation:
    """Test Task model ID validation."""

    def test_task_ulid_id(self):
        """Task accepts ULID ID."""
        task = Task(
            id="01KC3AD75P4TW2MAWDWJC4YCMC",
            sprint_id="01KC3AD75P4TW2MAWDWJC4YCMB",
            title="Test Task",
        )
        assert task.id == "01KC3AD75P4TW2MAWDWJC4YCMC"

    def test_task_slug_id(self):
        """Task accepts slug ID."""
        task = Task(
            id="sqlite-backend-4-task-001",
            title="First Task",
        )
        assert task.id == "sqlite-backend-4-task-001"


class TestTrackSprintAssociation:
    """Test Track-Sprint association validation."""

    def test_ulid_sprint_with_matching_track_id(self):
        """ULID sprint with correct track_id is accepted."""
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

    def test_ulid_sprint_with_wrong_track_id_rejected(self):
        """ULID sprint with wrong track_id is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Track(
                id="01KC2D0JKTE7Z4HCNHST8ZVW4R",
                name="Test Track",
                sprints=[
                    Sprint(
                        id="01KC3AD75P4TW2MAWDWJC4YCMB",
                        track_id="01KC2D0JKVT80AFQ6C1PA8CKJD",  # Wrong!
                        name="Sprint 1",
                    )
                ]
            )
        assert "track_id" in str(exc_info.value)

    def test_slug_sprint_with_matching_prefix(self):
        """Slug sprint with correct prefix is accepted."""
        track = Track(
            id="sqlite-backend",
            name="SQLite Backend",
            sprints=[
                Sprint(id="sqlite-backend-1", name="Sprint 1"),
                Sprint(id="sqlite-backend-2", name="Sprint 2"),
            ]
        )
        assert len(track.sprints) == 2

    def test_slug_sprint_with_wrong_prefix_rejected(self):
        """Slug sprint with wrong prefix is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Track(
                id="sqlite-backend",
                name="SQLite Backend",
                sprints=[
                    Sprint(id="wrong-track-1", name="Sprint 1"),
                ]
            )
        assert "must start with" in str(exc_info.value)


class TestMixedIdFormats:
    """Test mixed ULID and slug ID handling."""

    def test_ulid_track_with_ulid_sprints(self):
        """ULID track with ULID sprints works."""
        track = Track(
            id="01KC2D0JKTE7Z4HCNHST8ZVW4R",
            name="Test Track",
            sprints=[
                Sprint(
                    id="01KC3AD75P4TW2MAWDWJC4YCMB",
                    track_id="01KC2D0JKTE7Z4HCNHST8ZVW4R",
                    name="Sprint 1",
                ),
            ]
        )
        assert len(track.sprints) == 1

    def test_slug_track_with_slug_sprints(self):
        """Slug track with slug sprints works."""
        track = Track(
            id="sqlite-backend",
            name="SQLite Backend",
            sprints=[
                Sprint(id="sqlite-backend-1", name="Sprint 1"),
            ]
        )
        assert len(track.sprints) == 1
```

### 3. FileSystemManager Tests

```python
# tests/cli/roadmap_lib/test_filesystem_ids.py

import pytest
from pathlib import Path
from vibey.cli.roadmap_lib.filesystem import FileSystemManager


class TestIdResolution:
    """Test ID resolution in FileSystemManager."""

    def test_resolve_ulid_returns_ulid(self, flat_roadmap):
        """ULID ID is returned as-is."""
        fs = FileSystemManager(flat_roadmap.parent.parent.parent)
        result = fs.resolve_id("track", "01KC2D0JKTE7Z4HCNHST8ZVW4R")
        assert result == "01KC2D0JKTE7Z4HCNHST8ZVW4R"

    def test_resolve_slug_with_mapping(self, flat_roadmap):
        """Slug is resolved to ULID via .id file."""
        # Create .id mapping file
        id_file = flat_roadmap / "tracks" / ".id"
        id_file.write_text("sqlite-backend: 01KC2D0JKTE7Z4HCNHST8ZVW4R\n")

        fs = FileSystemManager(flat_roadmap.parent.parent.parent)
        result = fs.resolve_id("track", "sqlite-backend")
        assert result == "01KC2D0JKTE7Z4HCNHST8ZVW4R"

    def test_resolve_slug_without_mapping(self, flat_roadmap):
        """Slug without mapping is returned as-is."""
        fs = FileSystemManager(flat_roadmap.parent.parent.parent)
        result = fs.resolve_id("track", "unknown-slug")
        assert result == "unknown-slug"

    def test_reverse_resolve_ulid(self, flat_roadmap):
        """ULID can be resolved back to slug."""
        # Create .id mapping file
        id_file = flat_roadmap / "tracks" / ".id"
        id_file.write_text("sqlite-backend: 01KC2D0JKTE7Z4HCNHST8ZVW4R\n")

        fs = FileSystemManager(flat_roadmap.parent.parent.parent)
        result = fs.reverse_resolve_id("track", "01KC2D0JKTE7Z4HCNHST8ZVW4R")
        assert result == "sqlite-backend"


class TestTrackDiscoveryBothFormats:
    """Test track discovery with both ID formats."""

    def test_list_tracks_ulid_format(self, tmp_path):
        """Discover ULID-named track files."""
        tracks_dir = tmp_path / ".vibey/roadmap/tracks"
        tracks_dir.mkdir(parents=True)
        (tmp_path / ".vibey/roadmap/sprints").mkdir()
        (tmp_path / ".vibey/roadmap/tasks").mkdir()

        # Create ULID-named track files
        for i in range(3):
            ulid = f"01KC2D0JKTE7Z4HCNHST8ZVW4{i}"
            (tracks_dir / f"{ulid}.yaml").write_text(f"""
track:
  id: {ulid}
  name: Track {i}
""")

        fs = FileSystemManager(tmp_path)
        tracks = fs.list_tracks()

        assert len(tracks) == 3
        for track_id in tracks:
            assert len(track_id) == 26  # ULID length

    def test_list_tracks_nested_slug_format(self, tmp_path):
        """Discover slug-named track directories."""
        roadmap_dir = tmp_path / ".vibey/roadmap"
        roadmap_dir.mkdir(parents=True)

        # Create slug-named track directories
        for slug in ["sqlite-backend", "unified-arch", "test-track"]:
            track_dir = roadmap_dir / slug
            track_dir.mkdir()
            (track_dir / "track.yaml").write_text(f"""
track:
  id: {slug}
  name: {slug.replace('-', ' ').title()}
""")

        fs = FileSystemManager(tmp_path)
        # Should detect nested structure and list directories
        tracks = fs.list_tracks()

        assert len(tracks) == 3
        assert "sqlite-backend" in tracks
```

### 4. Integration Tests

```python
# tests/integration/test_id_format_integration.py

import pytest
from click.testing import CliRunner
from vibey.cli.main import cli


class TestCLIWithBothIdFormats:
    """Integration tests for CLI with both ID formats."""

    def test_status_shows_ulid_tracks(self, flat_roadmap_with_tracks):
        """roadmap status shows tracks with ULID IDs."""
        runner = CliRunner()
        result = runner.invoke(cli, ['roadmap', 'status'])

        assert result.exit_code == 0
        # Should show track count matching ULID files

    def test_status_shows_slug_tracks(self, nested_roadmap_with_tracks):
        """roadmap status shows tracks with slug IDs."""
        runner = CliRunner()
        result = runner.invoke(cli, ['roadmap', 'status'])

        assert result.exit_code == 0
        # Should show track count matching directories

    def test_query_track_by_ulid(self, flat_roadmap_with_tracks):
        """Query track by ULID works."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'roadmap', 'query', 'track',
            '01KC2D0JKTE7Z4HCNHST8ZVW4R'
        ])

        assert result.exit_code == 0

    def test_query_track_by_slug(self, flat_roadmap_with_mapping):
        """Query track by slug works via mapping."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'roadmap', 'query', 'track',
            'sqlite-backend'
        ])

        assert result.exit_code == 0
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `tests/roadmap/test_id_utils.py` | ID format detection and parsing tests |
| `tests/roadmap/models/test_id_validation.py` | Model validation tests |
| `tests/cli/roadmap_lib/test_filesystem_ids.py` | FileSystemManager ID tests |
| `tests/integration/test_id_format_integration.py` | End-to-end CLI tests |

---

## Test Fixtures

```python
# conftest.py additions

@pytest.fixture
def flat_roadmap(tmp_path):
    """Create flat structure roadmap."""
    roadmap_dir = tmp_path / ".vibey" / "roadmap"
    (roadmap_dir / "tracks").mkdir(parents=True)
    (roadmap_dir / "sprints").mkdir()
    (roadmap_dir / "tasks").mkdir()

    (roadmap_dir / "roadmap.yaml").write_text("""
roadmap:
  id: test-roadmap
  name: Test
  version: 1.0.0
  status: in_progress
  tracks: []
""")

    return roadmap_dir


@pytest.fixture
def nested_roadmap(tmp_path):
    """Create nested structure roadmap."""
    roadmap_dir = tmp_path / ".vibey" / "roadmap"
    roadmap_dir.mkdir(parents=True)

    (roadmap_dir / "roadmap.yaml").write_text("""
roadmap:
  id: test-roadmap
  name: Test
  version: 1.0.0
  status: in_progress
  tracks: []
""")

    return roadmap_dir


@pytest.fixture
def flat_roadmap_with_tracks(flat_roadmap):
    """Flat roadmap with sample ULID tracks."""
    tracks_dir = flat_roadmap / "tracks"

    for i, ulid in enumerate([
        "01KC2D0JKTE7Z4HCNHST8ZVW4R",
        "01KC2D0JKVT80AFQ6C1PA8CKJD",
    ]):
        (tracks_dir / f"{ulid}.yaml").write_text(f"""
track:
  id: {ulid}
  name: Track {i + 1}
  status: in_progress
""")

    return flat_roadmap


@pytest.fixture
def flat_roadmap_with_mapping(flat_roadmap_with_tracks):
    """Flat roadmap with .id mapping file."""
    id_file = flat_roadmap_with_tracks / "tracks" / ".id"
    id_file.write_text("""
sqlite-backend: 01KC2D0JKTE7Z4HCNHST8ZVW4R
unified-arch: 01KC2D0JKVT80AFQ6C1PA8CKJD
""")

    return flat_roadmap_with_tracks
```

---

## Success Criteria

- [ ] ULID pattern matching is thorough
- [ ] Slug parsing covers edge cases
- [ ] Model validation tests comprehensive
- [ ] FileSystemManager ID tests pass
- [ ] Integration tests verify end-to-end
- [ ] All tests pass for both formats
- [ ] No regressions for existing functionality

---

## Dependencies

- Task 015 (validation implementation)
- Task 016 (backward compatibility implementation)

---

## Notes

These tests serve multiple purposes:
1. **Verification** - Confirm Bug #4 is fixed
2. **Regression Prevention** - Catch future breaks
3. **Documentation** - Show expected behavior
4. **Confidence** - Enable safe refactoring

Test coverage should be >90% for ID-related code paths.
