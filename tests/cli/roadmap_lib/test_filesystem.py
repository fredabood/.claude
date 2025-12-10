"""Tests for FileSystemManager path resolution."""

import pytest
from pathlib import Path

from vibey.cli.roadmap_lib.filesystem import FileSystemManager, find_roadmap_root


class TestFileSystemManagerPaths:
    """Test path resolution for flat and nested structures."""

    def test_get_roadmap_path_flat_structure(self, tmp_path):
        """Verify roadmap path is in roadmap/ subdirectory."""
        # Setup flat structure
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        (roadmap_dir / "tracks").mkdir(parents=True)
        (roadmap_dir / "sprints").mkdir()
        (roadmap_dir / "tasks").mkdir()

        fs = FileSystemManager(tmp_path)
        path = fs.get_roadmap_path()

        assert path == roadmap_dir / "roadmap.yaml"
        assert str(path).endswith(".vibey/roadmap/roadmap.yaml")

    def test_get_roadmap_path_nested_structure(self, tmp_path):
        """Verify roadmap path for legacy nested structure."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)
        # No tracks/sprints/tasks subdirs = nested structure

        fs = FileSystemManager(tmp_path)
        path = fs.get_roadmap_path()

        assert path == roadmap_dir / "roadmap.yaml"

    def test_get_track_path_flat_structure(self, tmp_path):
        """Verify track path uses ULID in flat structure."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        (roadmap_dir / "tracks").mkdir(parents=True)
        (roadmap_dir / "sprints").mkdir()
        (roadmap_dir / "tasks").mkdir()

        fs = FileSystemManager(tmp_path)
        path = fs.get_track_path("01KC2D0JKTE7Z4HCNHST8ZVW4R")

        assert str(path).endswith("tracks/01KC2D0JKTE7Z4HCNHST8ZVW4R.yaml")

    def test_get_sprint_path_flat_structure(self, tmp_path):
        """Verify sprint path uses ULID in flat structure."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        (roadmap_dir / "tracks").mkdir(parents=True)
        (roadmap_dir / "sprints").mkdir()
        (roadmap_dir / "tasks").mkdir()

        fs = FileSystemManager(tmp_path)
        path = fs.get_sprint_path("01KC3AD75P4TW2MAWDWJC4YCMB")

        assert str(path).endswith("sprints/01KC3AD75P4TW2MAWDWJC4YCMB.yaml")

    def test_get_task_path_flat_structure(self, tmp_path):
        """Verify task path uses ULID in flat structure."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        (roadmap_dir / "tracks").mkdir(parents=True)
        (roadmap_dir / "sprints").mkdir()
        (roadmap_dir / "tasks").mkdir()

        fs = FileSystemManager(tmp_path)
        path = fs.get_task_path("01KC3B2K4MNPQ2RABC4DEFGHIJ")

        assert str(path).endswith("tasks/01KC3B2K4MNPQ2RABC4DEFGHIJ.yaml")


class TestFindRoadmapRoot:
    """Test find_roadmap_root function."""

    def test_find_roadmap_root_new_location(self, tmp_path):
        """Find roadmap from new canonical location."""
        roadmap_file = tmp_path / ".vibey" / "roadmap" / "roadmap.yaml"
        roadmap_file.parent.mkdir(parents=True)
        roadmap_file.write_text("roadmap:\n  id: test")

        result = find_roadmap_root(tmp_path)
        assert result == tmp_path

    def test_find_roadmap_root_legacy_location(self, tmp_path):
        """Find roadmap from legacy location."""
        roadmap_file = tmp_path / ".vibey" / "roadmap.yaml"
        roadmap_file.parent.mkdir(parents=True)
        roadmap_file.write_text("roadmap:\n  id: test")

        result = find_roadmap_root(tmp_path)
        assert result == tmp_path

    def test_find_roadmap_root_prefers_new_location(self, tmp_path):
        """New location is preferred over legacy."""
        # Create both locations
        (tmp_path / ".vibey" / "roadmap").mkdir(parents=True)
        (tmp_path / ".vibey" / "roadmap" / "roadmap.yaml").write_text("new")
        (tmp_path / ".vibey" / "roadmap.yaml").write_text("legacy")

        result = find_roadmap_root(tmp_path)
        assert result == tmp_path  # Should still find root

    def test_find_roadmap_root_not_found(self, tmp_path):
        """Return None when no roadmap found."""
        result = find_roadmap_root(tmp_path)
        assert result is None

    def test_find_roadmap_root_from_subdirectory(self, tmp_path):
        """Find roadmap from a subdirectory."""
        roadmap_file = tmp_path / ".vibey" / "roadmap" / "roadmap.yaml"
        roadmap_file.parent.mkdir(parents=True)
        roadmap_file.write_text("roadmap:\n  id: test")

        # Create a subdirectory and search from there
        subdir = tmp_path / "src" / "lib"
        subdir.mkdir(parents=True)

        result = find_roadmap_root(subdir)
        assert result == tmp_path


class TestStructureDetection:
    """Test automatic structure detection."""

    def test_detect_flat_structure(self, tmp_path):
        """Detect flat when tracks/sprints/tasks dirs exist."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        (roadmap_dir / "tracks").mkdir(parents=True)
        (roadmap_dir / "sprints").mkdir()
        (roadmap_dir / "tasks").mkdir()

        fs = FileSystemManager(tmp_path)
        assert fs.structure_format == "flat"

    def test_detect_nested_structure(self, tmp_path):
        """Detect nested when no tracks/sprints/tasks dirs."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)

        fs = FileSystemManager(tmp_path)
        assert fs.structure_format == "nested"

    def test_detect_nested_by_default(self, tmp_path):
        """Default to nested when no structure exists."""
        fs = FileSystemManager(tmp_path)
        assert fs.structure_format == "nested"
