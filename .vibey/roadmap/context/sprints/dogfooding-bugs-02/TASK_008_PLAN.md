# Task 008: Add Integration Tests for ULID File Loading

**Task ID:** dogfooding-bugs-02-task-008
**Bug Addressed:** #10 (Monolithic roadmap.yaml read)
**Complexity:** Medium
**Type:** Testing

---

## Problem Statement

The new ULID file loading strategy needs comprehensive integration tests to verify end-to-end functionality and prevent regressions.

---

## Test Categories

### 1. Track Discovery Tests

```python
# tests/roadmap/serialization/test_ulid_loading.py

class TestTrackDiscovery:
    """Test track discovery from ULID files."""

    def test_discover_tracks_from_ulid_files(self, tmp_path):
        """Tracks are discovered from tracks/*.yaml."""
        self._setup_flat_structure(tmp_path, num_tracks=5)

        roadmap = load_roadmap(tmp_path / ".vibey/roadmap/roadmap.yaml")

        assert len(roadmap.tracks) == 5

    def test_discover_tracks_when_roadmap_yaml_empty(self, tmp_path):
        """Tracks discovered even if roadmap.yaml has empty tracks list."""
        self._setup_flat_structure(tmp_path, num_tracks=3)

        # Clear tracks in roadmap.yaml
        roadmap_path = tmp_path / ".vibey/roadmap/roadmap.yaml"
        data = yaml.safe_load(roadmap_path.read_text())
        data['roadmap']['tracks'] = []
        roadmap_path.write_text(yaml.dump(data))

        roadmap = load_roadmap(roadmap_path)

        assert len(roadmap.tracks) == 3  # Still discovers from files

    def test_merge_yaml_and_ulid_tracks(self, tmp_path):
        """Tracks from both sources are merged."""
        self._setup_flat_structure(tmp_path, num_tracks=2)

        # Add extra track to roadmap.yaml only (legacy)
        roadmap_path = tmp_path / ".vibey/roadmap/roadmap.yaml"
        data = yaml.safe_load(roadmap_path.read_text())
        data['roadmap']['tracks'].append({
            'id': 'legacy-track',
            'name': 'Legacy Track',
            'status': 'completed',
        })
        roadmap_path.write_text(yaml.dump(data))

        roadmap = load_roadmap(roadmap_path)

        assert len(roadmap.tracks) == 3  # 2 ULID + 1 legacy

    def test_ulid_takes_priority_over_yaml(self, tmp_path):
        """ULID file data takes priority over roadmap.yaml."""
        self._setup_flat_structure(tmp_path, num_tracks=1)
        track_id = "01KC2D0JKTE7Z4HCNHST8ZVW4R"

        # Set different status in roadmap.yaml
        roadmap_path = tmp_path / ".vibey/roadmap/roadmap.yaml"
        data = yaml.safe_load(roadmap_path.read_text())
        data['roadmap']['tracks'] = [{
            'id': track_id,
            'name': 'Wrong Name',
            'status': 'completed',
        }]
        roadmap_path.write_text(yaml.dump(data))

        # ULID file has correct data
        track_path = tmp_path / f".vibey/roadmap/tracks/{track_id}.yaml"
        track_data = yaml.safe_load(track_path.read_text())
        track_data['track']['status'] = 'in_progress'
        track_path.write_text(yaml.dump(track_data))

        roadmap = load_roadmap(roadmap_path)

        track = next(t for t in roadmap.tracks if t.id == track_id)
        assert track.status == Status.IN_PROGRESS  # From ULID file
```

### 2. Sprint Discovery Tests

```python
class TestSprintDiscovery:
    """Test sprint discovery from ULID files."""

    def test_discover_sprints_for_track(self, tmp_path):
        """Sprints are discovered by track_id reference."""
        track_id = "01KC2D0JKTE7Z4HCNHST8ZVW4R"
        self._setup_flat_structure_with_sprints(tmp_path, track_id, num_sprints=3)

        track = load_track_details(
            track_id,
            tmp_path / ".vibey/roadmap/tracks",
            tmp_path / ".vibey/roadmap/sprints"
        )

        assert len(track.sprints) == 3

    def test_sprints_filtered_by_track_id(self, tmp_path):
        """Only sprints with matching track_id are included."""
        self._setup_two_tracks_with_sprints(tmp_path)

        track = load_track_details(
            "track_01",
            tmp_path / ".vibey/roadmap/tracks",
            tmp_path / ".vibey/roadmap/sprints"
        )

        # Should only have track_01's sprints, not track_02's
        for sprint in track.sprints:
            assert "track_01" in sprint.id or sprint.track_id == "track_01"
```

### 3. Task Discovery Tests

```python
class TestTaskDiscovery:
    """Test task discovery from ULID files."""

    def test_discover_tasks_for_sprint(self, tmp_path):
        """Tasks are discovered by sprint_id reference."""
        sprint_id = "01KC3AD75P4TW2MAWDWJC4YCMB"
        self._setup_sprint_with_tasks(tmp_path, sprint_id, num_tasks=5)

        sprint = load_sprint_details(
            sprint_id,
            tmp_path / ".vibey/roadmap/sprints",
            tmp_path / ".vibey/roadmap/tasks"
        )

        assert len(sprint.tasks) == 5
```

### 4. End-to-End CLI Tests

```python
class TestCLIWithULIDFiles:
    """Test CLI commands with ULID file structure."""

    def test_roadmap_status_shows_all_tracks(self, tmp_path, cli_runner):
        """vibey roadmap status shows tracks from ULID files."""
        self._setup_full_roadmap(tmp_path)

        result = cli_runner.invoke(cli, ['roadmap', 'status'])

        assert result.exit_code == 0
        assert "Track 1" in result.output
        assert "Track 2" in result.output

    def test_roadmap_list_tracks_complete(self, tmp_path, cli_runner):
        """vibey roadmap list tracks shows all ULID tracks."""
        self._setup_full_roadmap(tmp_path, num_tracks=5)

        result = cli_runner.invoke(cli, ['roadmap', 'list', 'tracks'])

        assert result.exit_code == 0
        # All 5 tracks should be listed
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `tests/roadmap/serialization/test_ulid_loading.py` | Core loading tests |
| `tests/cli/test_roadmap_ulid_integration.py` | CLI integration tests |
| `tests/roadmap/serialization/conftest.py` | Shared fixtures |

---

## Test Fixtures

```python
# conftest.py

@pytest.fixture
def flat_roadmap_structure(tmp_path):
    """Create a complete flat structure for testing."""
    roadmap_dir = tmp_path / ".vibey" / "roadmap"
    (roadmap_dir / "tracks").mkdir(parents=True)
    (roadmap_dir / "sprints").mkdir()
    (roadmap_dir / "tasks").mkdir()

    # Create roadmap.yaml
    (roadmap_dir / "roadmap.yaml").write_text("""
roadmap:
  id: test-roadmap
  name: Test Roadmap
  version: 1.0.0
  status: in_progress
  tracks: []
  progress:
    tracks_total: 0
    sprints_total: 0
    tasks_total: 0
""")

    return roadmap_dir
```

---

## Success Criteria

- [ ] Track discovery tests pass
- [ ] Sprint discovery tests pass
- [ ] Task discovery tests pass
- [ ] CLI integration tests pass
- [ ] Tests cover edge cases (empty, mixed formats)
- [ ] Tests verify Bug #10 is fixed

---

## Dependencies

- Tasks 005, 006, 007 (loading strategy implementation)

---

## Notes

These integration tests serve as:
1. Verification that Bug #10 is fixed
2. Regression prevention
3. Documentation of expected behavior
4. Confidence for refactoring
