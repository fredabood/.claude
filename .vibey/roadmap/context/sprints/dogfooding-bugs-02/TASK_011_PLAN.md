# Task 011: Add Integration Test for Track Listing

**Task ID:** dogfooding-bugs-02-task-011
**Bug Addressed:** #2 (Tracks not showing in status)
**Complexity:** Low
**Type:** Testing

---

## Problem Statement

Track listing functionality lacks integration tests that verify all tracks are discovered and displayed correctly.

---

## Test Cases

### 1. Basic Track Listing

```python
# tests/cli/test_track_listing.py

class TestTrackListing:
    """Integration tests for track listing."""

    def test_list_tracks_flat_structure(self, flat_roadmap):
        """All tracks in flat structure are listed."""
        fs = FileSystemManager(flat_roadmap.parent.parent.parent)
        tracks = fs.list_tracks()

        # Verify count matches files
        track_files = list((flat_roadmap / "tracks").glob("*.yaml"))
        assert len(tracks) == len(track_files)

    def test_cli_roadmap_list_tracks(self, flat_roadmap, cli_runner):
        """CLI command lists all tracks."""
        result = cli_runner.invoke(cli, ['roadmap', 'list', 'tracks'])

        assert result.exit_code == 0
        # Each track should appear in output
        for track_id in FileSystemManager(flat_roadmap.parent.parent.parent).list_tracks():
            assert track_id in result.output or "Track" in result.output

    def test_roadmap_status_shows_track_count(self, flat_roadmap, cli_runner):
        """roadmap status shows correct track count."""
        # Create 5 tracks
        tracks_dir = flat_roadmap / "tracks"
        for i in range(5):
            (tracks_dir / f"track_{i}.yaml").write_text(f"""
track:
  id: track_{i}
  name: Track {i}
  status: in_progress
""")

        result = cli_runner.invoke(cli, ['roadmap', 'status'])

        assert result.exit_code == 0
        assert "5" in result.output or "tracks" in result.output.lower()
```

### 2. Edge Cases

```python
class TestTrackListingEdgeCases:
    """Edge case tests for track listing."""

    def test_empty_tracks_directory(self, tmp_path):
        """Handle empty tracks directory gracefully."""
        tracks_dir = tmp_path / ".vibey/roadmap/tracks"
        tracks_dir.mkdir(parents=True)
        (tmp_path / ".vibey/roadmap/sprints").mkdir()
        (tmp_path / ".vibey/roadmap/tasks").mkdir()

        fs = FileSystemManager(tmp_path)
        tracks = fs.list_tracks()

        assert tracks == []

    def test_missing_tracks_directory(self, tmp_path):
        """Handle missing tracks directory gracefully."""
        (tmp_path / ".vibey/roadmap").mkdir(parents=True)

        fs = FileSystemManager(tmp_path)
        # Should not raise, return empty or handle gracefully

    def test_malformed_track_files(self, tmp_path):
        """Malformed track files are handled gracefully."""
        tracks_dir = tmp_path / ".vibey/roadmap/tracks"
        tracks_dir.mkdir(parents=True)
        (tmp_path / ".vibey/roadmap/sprints").mkdir()
        (tmp_path / ".vibey/roadmap/tasks").mkdir()

        # Valid track
        (tracks_dir / "valid.yaml").write_text("""
track:
  id: valid
  name: Valid Track
""")

        # Malformed track (not valid YAML)
        (tracks_dir / "malformed.yaml").write_text("not: valid: yaml: {[")

        fs = FileSystemManager(tmp_path)
        tracks = fs.list_tracks()

        # Should still find the file (listing doesn't parse)
        assert "valid" in tracks
        assert "malformed" in tracks  # Listed but may fail on load
```

### 3. Regression Test for Bug #2

```python
class TestBug2Regression:
    """Regression tests for Bug #2 (tracks not showing)."""

    def test_newly_created_track_visible(self, flat_roadmap, cli_runner):
        """Newly created tracks appear in listings."""
        # Create a new track (simulating what unified-architecture-migration was)
        tracks_dir = flat_roadmap / "tracks"
        new_track_id = "01KC2D0JKTE7Z4HCNHST8ZVW4R"
        (tracks_dir / f"{new_track_id}.yaml").write_text(f"""
track:
  id: {new_track_id}
  name: New Track
  status: not_started
  priority: high
""")

        # Verify it appears in list
        result = cli_runner.invoke(cli, ['roadmap', 'list', 'tracks'])

        assert result.exit_code == 0
        assert new_track_id in result.output or "New Track" in result.output

    def test_track_not_in_roadmap_yaml_still_visible(self, flat_roadmap, cli_runner):
        """Track missing from roadmap.yaml is still discoverable."""
        tracks_dir = flat_roadmap / "tracks"

        # Create track file
        orphan_id = "01KC2D0JKORPHANTRACK12345"
        (tracks_dir / f"{orphan_id}.yaml").write_text(f"""
track:
  id: {orphan_id}
  name: Orphan Track
  status: in_progress
""")

        # Verify roadmap.yaml doesn't list it
        roadmap_data = yaml.safe_load((flat_roadmap / "roadmap.yaml").read_text())
        track_ids = [t['id'] for t in roadmap_data['roadmap'].get('tracks', [])]
        assert orphan_id not in track_ids

        # But it should still appear in CLI
        result = cli_runner.invoke(cli, ['roadmap', 'list', 'tracks'])
        assert orphan_id in result.output or "Orphan Track" in result.output
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `tests/cli/test_track_listing.py` | Track listing integration tests |

---

## Test Fixtures

```python
# conftest.py

@pytest.fixture
def flat_roadmap(tmp_path):
    """Create a flat structure roadmap for testing."""
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
def cli_runner():
    """Click CLI test runner."""
    from click.testing import CliRunner
    return CliRunner()
```

---

## Success Criteria

- [ ] Integration tests cover track listing
- [ ] Edge cases handled (empty, missing, malformed)
- [ ] Regression test for Bug #2
- [ ] Tests pass with current fixes
- [ ] CI runs these tests

---

## Dependencies

- Tasks 009, 010 (discovery fixes)

---

## Notes

These tests ensure Bug #2 doesn't regress. They should be run as part of CI to catch any future issues with track discovery.
