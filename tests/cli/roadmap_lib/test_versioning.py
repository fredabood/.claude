"""
Tests for vibey.cli.roadmap_lib.versioning module.

Tests semantic versioning utilities and version bump logic.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from vibey.cli.roadmap_lib.versioning import (
    VersionManager,
    bump_version,
    parse_version,
)


class TestParseVersion:
    """Test version parsing."""

    @pytest.fixture
    def manager(self):
        """Create VersionManager instance."""
        with patch('vibey.cli.roadmap_lib.versioning.FileSystemManager'):
            return VersionManager()

    def test_parse_valid_version(self, manager):
        """Test parsing valid version string."""
        major, minor, patch = manager.parse_version("1.2.3")
        assert major == 1
        assert minor == 2
        assert patch == 3

    def test_parse_zero_version(self, manager):
        """Test parsing version with zeros."""
        major, minor, patch = manager.parse_version("0.0.0")
        assert major == 0
        assert minor == 0
        assert patch == 0

    def test_parse_large_version(self, manager):
        """Test parsing large version numbers."""
        major, minor, patch = manager.parse_version("100.200.300")
        assert major == 100
        assert minor == 200
        assert patch == 300

    def test_parse_invalid_format_too_few_parts(self, manager):
        """Test parsing version with too few parts."""
        with pytest.raises(ValueError) as exc_info:
            manager.parse_version("1.2")
        assert "Invalid version format" in str(exc_info.value)

    def test_parse_invalid_format_too_many_parts(self, manager):
        """Test parsing version with too many parts."""
        with pytest.raises(ValueError) as exc_info:
            manager.parse_version("1.2.3.4")
        assert "Invalid version format" in str(exc_info.value)

    def test_parse_invalid_format_non_numeric(self, manager):
        """Test parsing version with non-numeric parts."""
        with pytest.raises(ValueError) as exc_info:
            manager.parse_version("1.a.3")
        assert "Invalid version format" in str(exc_info.value)

    def test_parse_empty_string(self, manager):
        """Test parsing empty string."""
        with pytest.raises(ValueError):
            manager.parse_version("")

    def test_parse_single_number(self, manager):
        """Test parsing single number."""
        with pytest.raises(ValueError):
            manager.parse_version("1")


class TestFormatVersion:
    """Test version formatting."""

    @pytest.fixture
    def manager(self):
        """Create VersionManager instance."""
        with patch('vibey.cli.roadmap_lib.versioning.FileSystemManager'):
            return VersionManager()

    def test_format_version_basic(self, manager):
        """Test formatting basic version."""
        result = manager.format_version(1, 2, 3)
        assert result == "1.2.3"

    def test_format_version_zeros(self, manager):
        """Test formatting version with zeros."""
        result = manager.format_version(0, 0, 0)
        assert result == "0.0.0"

    def test_format_version_large_numbers(self, manager):
        """Test formatting large version numbers."""
        result = manager.format_version(100, 200, 300)
        assert result == "100.200.300"

    def test_format_version_roundtrip(self, manager):
        """Test format -> parse -> format roundtrip."""
        original = "5.10.15"
        major, minor, patch = manager.parse_version(original)
        result = manager.format_version(major, minor, patch)
        assert result == original


class TestBumpVersion:
    """Test version bumping logic."""

    @pytest.fixture
    def manager(self):
        """Create VersionManager instance."""
        with patch('vibey.cli.roadmap_lib.versioning.FileSystemManager'):
            return VersionManager()

    def test_bump_patch(self, manager):
        """Test patch version bump."""
        result = manager.bump_version("1.2.3", "patch")
        assert result == "1.2.4"

    def test_bump_minor(self, manager):
        """Test minor version bump."""
        result = manager.bump_version("1.2.3", "minor")
        assert result == "1.3.0"

    def test_bump_major(self, manager):
        """Test major version bump."""
        result = manager.bump_version("1.2.3", "major")
        assert result == "2.0.0"

    def test_bump_default_is_minor(self, manager):
        """Test default bump type is minor."""
        result = manager.bump_version("1.2.3")
        assert result == "1.3.0"

    def test_bump_patch_from_zero(self, manager):
        """Test patch bump from zero."""
        result = manager.bump_version("0.0.0", "patch")
        assert result == "0.0.1"

    def test_bump_minor_resets_patch(self, manager):
        """Test minor bump resets patch to zero."""
        result = manager.bump_version("1.2.99", "minor")
        assert result == "1.3.0"

    def test_bump_major_resets_minor_and_patch(self, manager):
        """Test major bump resets minor and patch to zero."""
        result = manager.bump_version("1.99.99", "major")
        assert result == "2.0.0"

    def test_bump_invalid_type(self, manager):
        """Test bump with invalid type raises error."""
        with pytest.raises(ValueError) as exc_info:
            manager.bump_version("1.2.3", "invalid")
        assert "Invalid bump type" in str(exc_info.value)

    def test_bump_empty_type(self, manager):
        """Test bump with empty type raises error."""
        with pytest.raises(ValueError):
            manager.bump_version("1.2.3", "")


class TestShouldAutoBump:
    """Test auto-bump logic."""

    @pytest.fixture
    def manager(self):
        """Create VersionManager instance."""
        with patch('vibey.cli.roadmap_lib.versioning.FileSystemManager'):
            return VersionManager()

    def test_manual_strategy_returns_false(self, manager):
        """Test manual strategy doesn't auto-bump."""
        roadmap = MagicMock()
        roadmap.version_strategy.bump_on = "manual"

        result = manager.should_auto_bump(roadmap)

        assert result is False

    def test_sprint_completion_strategy(self, manager):
        """Test sprint completion strategy."""
        roadmap = MagicMock()
        roadmap.version_strategy.bump_on = "sprint_completion"

        result = manager.should_auto_bump(roadmap)

        # Currently returns False (needs tracking implementation)
        assert result is False

    def test_track_completion_strategy(self, manager):
        """Test track completion strategy."""
        roadmap = MagicMock()
        roadmap.version_strategy.bump_on = "track_completion"

        result = manager.should_auto_bump(roadmap)

        # Currently returns False (needs tracking implementation)
        assert result is False

    def test_unknown_strategy_returns_false(self, manager):
        """Test unknown strategy returns False."""
        roadmap = MagicMock()
        roadmap.version_strategy.bump_on = "unknown_strategy"

        result = manager.should_auto_bump(roadmap)

        assert result is False


class TestBumpRoadmapVersion:
    """Test roadmap version bumping."""

    @pytest.fixture
    def manager(self):
        """Create VersionManager instance with mocked filesystem."""
        with patch('vibey.cli.roadmap_lib.versioning.FileSystemManager') as mock_fs:
            mock_fs_instance = MagicMock()
            mock_fs.return_value = mock_fs_instance
            mgr = VersionManager()
            mgr.fs = mock_fs_instance
            return mgr

    def test_bump_roadmap_not_found(self, manager):
        """Test bumping when roadmap doesn't exist."""
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        manager.fs.get_roadmap_path.return_value = mock_path

        with pytest.raises(FileNotFoundError):
            manager.bump_roadmap_version()

    @patch('vibey.cli.roadmap_lib.versioning.load_roadmap')
    @patch('vibey.cli.roadmap_lib.versioning.save_roadmap')
    def test_bump_roadmap_version_explicit_type(self, mock_save, mock_load, manager):
        """Test bumping with explicit bump type."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        manager.fs.get_roadmap_path.return_value = mock_path

        mock_roadmap = MagicMock()
        mock_roadmap.version = "1.2.3"
        mock_load.return_value = mock_roadmap

        old_version, new_version = manager.bump_roadmap_version(bump_type="patch")

        assert old_version == "1.2.3"
        assert new_version == "1.2.4"
        assert mock_roadmap.version == "1.2.4"
        mock_save.assert_called_once()

    @patch('vibey.cli.roadmap_lib.versioning.load_roadmap')
    @patch('vibey.cli.roadmap_lib.versioning.save_roadmap')
    def test_bump_roadmap_version_from_strategy(self, mock_save, mock_load, manager):
        """Test bumping using roadmap strategy."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        manager.fs.get_roadmap_path.return_value = mock_path

        mock_roadmap = MagicMock()
        mock_roadmap.version = "1.0.0"
        mock_roadmap.version_strategy.bump_type = "minor"
        mock_load.return_value = mock_roadmap

        old_version, new_version = manager.bump_roadmap_version()

        assert old_version == "1.0.0"
        assert new_version == "1.1.0"

    @patch('vibey.cli.roadmap_lib.versioning.load_roadmap')
    @patch('vibey.cli.roadmap_lib.versioning.save_roadmap')
    def test_bump_roadmap_version_adds_activity(self, mock_save, mock_load, manager):
        """Test that bumping adds activity to roadmap."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        manager.fs.get_roadmap_path.return_value = mock_path

        mock_roadmap = MagicMock()
        mock_roadmap.version = "2.0.0"
        mock_load.return_value = mock_roadmap

        manager.bump_roadmap_version(bump_type="major")

        mock_roadmap.add_activity.assert_called_once()
        call_args = mock_roadmap.add_activity.call_args
        assert call_args[0][0] == "version_bumped"

    @patch('vibey.cli.roadmap_lib.versioning.load_roadmap')
    @patch('vibey.cli.roadmap_lib.versioning.save_roadmap')
    def test_bump_roadmap_version_custom_message(self, mock_save, mock_load, manager):
        """Test bumping with custom message."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        manager.fs.get_roadmap_path.return_value = mock_path

        mock_roadmap = MagicMock()
        mock_roadmap.version = "1.0.0"
        mock_load.return_value = mock_roadmap

        manager.bump_roadmap_version(bump_type="patch", message="Custom bump message")

        mock_roadmap.add_activity.assert_called_once()
        call_args = mock_roadmap.add_activity.call_args
        assert call_args[0][1] == "Custom bump message"


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    @patch('vibey.cli.roadmap_lib.versioning.FileSystemManager')
    def test_parse_version_function(self, mock_fs):
        """Test parse_version convenience function."""
        result = parse_version("1.2.3")
        assert result == (1, 2, 3)

    @patch('vibey.cli.roadmap_lib.versioning.FileSystemManager')
    @patch('vibey.cli.roadmap_lib.versioning.load_roadmap')
    @patch('vibey.cli.roadmap_lib.versioning.save_roadmap')
    def test_bump_version_function(self, mock_save, mock_load, mock_fs):
        """Test bump_version convenience function."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_fs_instance.get_roadmap_path.return_value = mock_path

        mock_roadmap = MagicMock()
        mock_roadmap.version = "1.0.0"
        mock_roadmap.version_strategy.bump_type = "patch"
        mock_load.return_value = mock_roadmap

        old_version, new_version = bump_version()

        assert old_version == "1.0.0"
        assert new_version == "1.0.1"

    @patch('vibey.cli.roadmap_lib.versioning.FileSystemManager')
    @patch('vibey.cli.roadmap_lib.versioning.load_roadmap')
    @patch('vibey.cli.roadmap_lib.versioning.save_roadmap')
    def test_bump_version_function_with_root_dir(self, mock_save, mock_load, mock_fs):
        """Test bump_version with custom root_dir."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_fs_instance.get_roadmap_path.return_value = mock_path

        mock_roadmap = MagicMock()
        mock_roadmap.version = "2.0.0"
        mock_load.return_value = mock_roadmap

        custom_root = Path("/custom/root")
        bump_version(bump_type="major", root_dir=custom_root)

        mock_fs.assert_called_with(custom_root)


class TestVersionManagerInit:
    """Test VersionManager initialization."""

    @patch('vibey.cli.roadmap_lib.versioning.FileSystemManager')
    def test_init_default_root(self, mock_fs):
        """Test initialization with default root."""
        manager = VersionManager()

        mock_fs.assert_called_once_with(None)

    @patch('vibey.cli.roadmap_lib.versioning.FileSystemManager')
    def test_init_custom_root(self, mock_fs):
        """Test initialization with custom root."""
        custom_path = Path("/custom/path")
        manager = VersionManager(root_dir=custom_path)

        mock_fs.assert_called_once_with(custom_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
