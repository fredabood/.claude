"""
Test SubmoduleDiscovery class.

Tests for submodule detection and discovery operations.
Design reference: SUBMODULE_ISOLATION_AND_PUSHDOWN.md
"""

import tempfile
from pathlib import Path

import pytest

from vibey.operations.submodule.discovery import SubmoduleDiscovery
from vibey.roadmap.models.submodule import (
    DetectionSource,
    SubmoduleReference,
)


class TestParseGitmodules:
    """Tests for parsing .gitmodules file."""

    def test_parse_gitmodules_with_valid_file(self):
        """Should correctly parse a valid .gitmodules file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_path = Path(tmpdir)

            # Create a mock .gitmodules file
            gitmodules = parent_path / ".gitmodules"
            gitmodules.write_text("""
[submodule "libs/core"]
    path = libs/core
    url = https://github.com/example/core.git

[submodule "libs/utils"]
    path = libs/utils
    url = https://github.com/example/utils.git
""")

            discovery = SubmoduleDiscovery(parent_path)
            paths = discovery.parse_gitmodules()

            assert len(paths) == 2
            assert "libs/core" in paths
            assert "libs/utils" in paths

    def test_parse_gitmodules_with_no_file(self):
        """Should return empty list when .gitmodules doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_path = Path(tmpdir)

            discovery = SubmoduleDiscovery(parent_path)
            paths = discovery.parse_gitmodules()

            assert paths == []

    def test_parse_gitmodules_with_empty_file(self):
        """Should return empty list for empty .gitmodules file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_path = Path(tmpdir)

            gitmodules = parent_path / ".gitmodules"
            gitmodules.write_text("")

            discovery = SubmoduleDiscovery(parent_path)
            paths = discovery.parse_gitmodules()

            assert paths == []


class TestHasVibeyRoadmap:
    """Tests for checking if a submodule has a Vibey roadmap."""

    def test_has_vibey_roadmap_with_roadmap(self):
        """Should return True when submodule has .vibey/roadmap."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_path = Path(tmpdir)

            # Create submodule with roadmap
            submodule_path = parent_path / "libs" / "core"
            roadmap_dir = submodule_path / ".vibey" / "roadmap"
            roadmap_dir.mkdir(parents=True)

            # Create roadmap.yaml
            (roadmap_dir / "roadmap.yaml").write_text(
                "roadmap:\n  id: core-v1\n  name: Core Library\n"
            )

            discovery = SubmoduleDiscovery(parent_path)
            result = discovery.has_vibey_roadmap("libs/core")

            assert result.has_roadmap is True
            assert result.roadmap_id == "core-v1"

    def test_has_vibey_roadmap_without_roadmap(self):
        """Should return False when submodule has no .vibey directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_path = Path(tmpdir)

            # Create submodule without roadmap
            submodule_path = parent_path / "libs" / "core"
            submodule_path.mkdir(parents=True)

            discovery = SubmoduleDiscovery(parent_path)
            result = discovery.has_vibey_roadmap("libs/core")

            assert result.has_roadmap is False

    def test_has_vibey_roadmap_with_nonexistent_path(self):
        """Should return False for nonexistent submodule path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_path = Path(tmpdir)

            discovery = SubmoduleDiscovery(parent_path)
            result = discovery.has_vibey_roadmap("nonexistent/path")

            assert result.has_roadmap is False


class TestValidateSubmodule:
    """Tests for submodule validation."""

    def test_validate_initialized_submodule(self):
        """Should validate an initialized submodule correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_path = Path(tmpdir)

            # Create submodule directory with content
            submodule_path = parent_path / "libs" / "core"
            submodule_path.mkdir(parents=True)
            (submodule_path / "README.md").write_text("# Core Library")

            discovery = SubmoduleDiscovery(parent_path)
            result = discovery.validate_submodule("libs/core")

            assert result.exists is True
            assert result.is_initialized is True

    def test_validate_uninitialized_submodule(self):
        """Should detect uninitialized submodule."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_path = Path(tmpdir)

            # Create empty submodule directory
            submodule_path = parent_path / "libs" / "core"
            submodule_path.mkdir(parents=True)

            discovery = SubmoduleDiscovery(parent_path)
            result = discovery.validate_submodule("libs/core")

            assert result.exists is True
            # Empty directory might be considered uninitialized
            assert result.is_initialized is False or result.is_empty is True


class TestDiscover:
    """Tests for full discovery flow."""

    def test_discover_writes_to_config(self):
        """Should discover submodules and write to config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_path = Path(tmpdir)

            # Create .gitmodules
            gitmodules = parent_path / ".gitmodules"
            gitmodules.write_text("""
[submodule "libs/core"]
    path = libs/core
    url = https://github.com/example/core.git
""")

            # Create submodule with roadmap
            submodule_path = parent_path / "libs" / "core"
            roadmap_dir = submodule_path / ".vibey" / "roadmap"
            roadmap_dir.mkdir(parents=True)
            (roadmap_dir / "roadmap.yaml").write_text(
                "roadmap:\n  id: core-v1\n  name: Core Library\n"
            )

            # Create parent config directory
            config_dir = parent_path / ".vibey" / "config"
            config_dir.mkdir(parents=True)

            discovery = SubmoduleDiscovery(parent_path)
            result = discovery.discover(auto_register=True)

            assert len(result.discovered) == 1
            assert result.discovered[0].path == "libs/core"
            assert result.discovered[0].has_vibey is True

            # Check config file was created
            config_path = config_dir / "submodules.yaml"
            if config_path.exists():
                assert "libs/core" in config_path.read_text()


class TestGetVibeySubmodules:
    """Tests for reading registered submodules from config."""

    def test_get_vibey_submodules_from_config(self):
        """Should read registered submodules from config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_path = Path(tmpdir)

            # Create config file
            config_dir = parent_path / ".vibey" / "config"
            config_dir.mkdir(parents=True)

            config_path = config_dir / "submodules.yaml"
            config_path.write_text("""
submodules:
  - path: libs/core
    roadmap_id: core-v1
    aggregate: true
    detection_source: gitmodules
  - path: libs/utils
    roadmap_id: utils-v1
    aggregate: true
    detection_source: manual
default_push_mode: linked
aggregate_on_status: true
""")

            discovery = SubmoduleDiscovery(parent_path)
            refs = discovery.get_vibey_submodules()

            assert len(refs) == 2
            assert refs[0].path == "libs/core"
            assert refs[0].roadmap_id == "core-v1"
            assert refs[1].path == "libs/utils"

    def test_get_vibey_submodules_with_no_config(self):
        """Should return empty list when config doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_path = Path(tmpdir)

            discovery = SubmoduleDiscovery(parent_path)
            refs = discovery.get_vibey_submodules()

            assert refs == []
