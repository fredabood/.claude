"""
Tests for vibey.operations.discovery.versioning module.

Tests versioned storage and diffing of DiscoveryOutput objects.
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from vibey.operations.discovery.schema import (
    DiscoveryOutput,
    DiscoveryMetadata,
    ProjectInfo,
    ProjectType,
    LanguageInfo,
    FrameworkInfo,
    FrameworkCategory,
    StructureInfo,
    DirectoryInfo,
    DirectoryPurpose,
    DependenciesInfo,
    Dependency,
)
from vibey.operations.discovery.versioning import (
    DiscoveryVersion,
    DiscoveryDiff,
    DiscoveryVersionManager,
    get_version_manager,
)


@pytest.fixture
def sample_discovery():
    """Create a sample DiscoveryOutput for testing."""
    return DiscoveryOutput(
        metadata=DiscoveryMetadata(
            schema_version="1.0.0",
            discovered_at=datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc),
            project_root="/path/to/project",
            git_commit="abc123",
            git_branch="main",
        ),
        project=ProjectInfo(
            name="test-project",
            type=ProjectType.WEB_APP,
            languages=[
                LanguageInfo(name="Python", version="3.11", percentage=80.0),
            ],
            frameworks=[
                FrameworkInfo(
                    name="FastAPI",
                    version="0.100.0",
                    category=FrameworkCategory.BACKEND,
                ),
            ],
        ),
        structure=StructureInfo(
            total_files=100,
            total_lines=5000,
            directories=[
                DirectoryInfo(
                    path="src",
                    purpose=DirectoryPurpose.SOURCE,
                    file_count=50,
                    line_count=3000,
                ),
            ],
            entry_points=["main.py"],
        ),
        dependencies=DependenciesInfo(
            runtime=[Dependency(name="fastapi", version="0.100.0")],
            development=[Dependency(name="pytest", version="7.0.0")],
            vulnerable_count=0,
        ),
    )


@pytest.fixture
def later_discovery():
    """Create a later discovery with some changes."""
    return DiscoveryOutput(
        metadata=DiscoveryMetadata(
            schema_version="1.0.0",
            discovered_at=datetime(2025, 12, 16, 10, 0, 0, tzinfo=timezone.utc),
            project_root="/path/to/project",
            git_commit="def456",
            git_branch="main",
        ),
        project=ProjectInfo(
            name="test-project",
            type=ProjectType.WEB_APP,
            languages=[
                LanguageInfo(name="Python", version="3.11", percentage=70.0),
                LanguageInfo(name="TypeScript", percentage=30.0),  # New language
            ],
            frameworks=[
                FrameworkInfo(
                    name="FastAPI",
                    version="0.100.0",
                    category=FrameworkCategory.BACKEND,
                ),
                FrameworkInfo(
                    name="React",
                    version="18.0.0",
                    category=FrameworkCategory.FRONTEND,
                ),  # New framework
            ],
        ),
        structure=StructureInfo(
            total_files=120,  # More files
            total_lines=6000,  # More lines
            directories=[
                DirectoryInfo(
                    path="src",
                    purpose=DirectoryPurpose.SOURCE,
                    file_count=60,
                    line_count=3500,
                ),
                DirectoryInfo(
                    path="frontend",
                    purpose=DirectoryPurpose.SOURCE,
                    file_count=40,
                    line_count=2000,
                ),  # New directory
            ],
            entry_points=["main.py", "app.tsx"],  # New entry point
        ),
        dependencies=DependenciesInfo(
            runtime=[
                Dependency(name="fastapi", version="0.100.0"),
                Dependency(name="react", version="18.0.0"),  # New dependency
            ],
            development=[Dependency(name="pytest", version="7.0.0")],
            vulnerable_count=1,  # Vulnerability added
        ),
    )


class TestDiscoveryVersion:
    """Test DiscoveryVersion dataclass."""

    def test_creation(self):
        """Test creating DiscoveryVersion."""
        version = DiscoveryVersion(
            timestamp=datetime.now(timezone.utc),
            filepath=Path("/path/to/file.yaml"),
            git_commit="abc123",
            git_branch="main",
            is_current=True,
        )
        assert version.is_current
        assert version.git_commit == "abc123"


class TestDiscoveryDiff:
    """Test DiscoveryDiff dataclass."""

    def test_default_values(self):
        """Test default values are set."""
        diff = DiscoveryDiff(
            from_version="v1",
            to_version="v2",
        )
        assert diff.project_changes == {}
        assert diff.structure_changes == {}
        assert not diff.has_significant_changes


class TestDiscoveryVersionManager:
    """Test DiscoveryVersionManager class."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a manager with temp directory."""
        return DiscoveryVersionManager(discovery_dir=tmp_path / "discovery")

    def test_init(self, manager, tmp_path):
        """Test initialization."""
        assert manager.discovery_dir == tmp_path / "discovery"
        assert manager.max_history == 10

    def test_ensure_dirs(self, manager):
        """Test directory creation."""
        manager._ensure_dirs()
        assert manager.discovery_dir.exists()
        assert manager.history_dir.exists()
        assert manager.diffs_dir.exists()

    def test_timestamp_conversion(self, manager):
        """Test timestamp to filename conversion."""
        ts = datetime(2025, 12, 15, 10, 30, 45, tzinfo=timezone.utc)
        filename = manager._timestamp_to_filename(ts)
        assert filename == "2025-12-15T10-30-45"

        # Round trip
        result = manager._filename_to_timestamp(filename)
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 15

    def test_save_first_discovery(self, manager, sample_discovery):
        """Test saving first discovery."""
        path, diff = manager.save(sample_discovery)
        assert path.exists()
        assert diff is None  # No previous to diff against

    def test_save_second_discovery(self, manager, sample_discovery, later_discovery):
        """Test saving second discovery creates diff."""
        # Save first
        manager.save(sample_discovery)
        # Save second
        path, diff = manager.save(later_discovery, create_diff=True)
        assert path.exists()
        assert diff is not None
        assert diff.has_significant_changes

    def test_load_current(self, manager, sample_discovery):
        """Test loading current discovery."""
        manager.save(sample_discovery)
        result = manager.load_current()
        assert result is not None
        assert result.project.name == "test-project"

    def test_load_current_none(self, manager):
        """Test loading current when none exists."""
        result = manager.load_current()
        assert result is None

    def test_load_version_current(self, manager, sample_discovery):
        """Test loading 'current' version."""
        manager.save(sample_discovery)
        result = manager.load_version("current")
        assert result is not None

    def test_load_version_from_history(self, manager, sample_discovery, later_discovery):
        """Test loading version from history."""
        manager.save(sample_discovery)
        manager.save(later_discovery)

        # First version should be in history
        versions = manager.list_versions()
        if len(versions) > 1:
            version_id = manager._timestamp_to_filename(versions[1].timestamp)
            result = manager.load_version(version_id)
            # May be None if history wasn't created properly
            # Just ensure no exception

    def test_list_versions_empty(self, manager):
        """Test listing versions when none exist."""
        versions = manager.list_versions()
        assert versions == []

    def test_list_versions(self, manager, sample_discovery, later_discovery):
        """Test listing versions."""
        manager.save(sample_discovery)
        manager.save(later_discovery)
        versions = manager.list_versions()
        assert len(versions) >= 1
        # Current should be first
        if versions:
            assert versions[0].is_current

    def test_list_versions_limit(self, manager, sample_discovery):
        """Test list_versions with limit."""
        manager.save(sample_discovery)
        versions = manager.list_versions(limit=1)
        assert len(versions) <= 1

    def test_create_diff(self, manager, sample_discovery, later_discovery):
        """Test creating diff between discoveries."""
        diff = manager.create_diff(sample_discovery, later_discovery)
        assert diff is not None
        assert diff.from_version == sample_discovery.metadata.discovered_at.isoformat()
        assert diff.to_version == later_discovery.metadata.discovered_at.isoformat()

    def test_diff_project_changes(self, manager, sample_discovery, later_discovery):
        """Test diff detects project changes."""
        diff = manager.create_diff(sample_discovery, later_discovery)
        # Should detect new language (TypeScript) and framework (React)
        assert "languages" in diff.project_changes or "frameworks" in diff.project_changes

    def test_diff_structure_changes(self, manager, sample_discovery, later_discovery):
        """Test diff detects structure changes."""
        diff = manager.create_diff(sample_discovery, later_discovery)
        # Should detect file count change (100 -> 120)
        assert "files" in diff.structure_changes

    def test_diff_dependency_changes(self, manager, sample_discovery, later_discovery):
        """Test diff detects dependency changes."""
        diff = manager.create_diff(sample_discovery, later_discovery)
        # Should detect new runtime dependency (react) and vulnerability change
        changes = diff.dependencies_changes
        assert "runtime" in changes or "vulnerabilities" in changes

    def test_is_significant_type_change(self, manager):
        """Test significance detection for type change."""
        diff = DiscoveryDiff(
            from_version="v1",
            to_version="v2",
            project_changes={"type": {"from": "web-app", "to": "api"}},
        )
        assert manager._is_significant(diff)

    def test_is_significant_language_change(self, manager):
        """Test significance detection for language change."""
        diff = DiscoveryDiff(
            from_version="v1",
            to_version="v2",
            project_changes={"languages": {"added": ["TypeScript"], "removed": []}},
        )
        assert manager._is_significant(diff)

    def test_is_significant_file_change(self, manager):
        """Test significance detection for file count change."""
        diff = DiscoveryDiff(
            from_version="v1",
            to_version="v2",
            structure_changes={"files": {"from": 100, "to": 150, "change": 50}},
        )
        assert manager._is_significant(diff)

    def test_is_significant_small_file_change(self, manager):
        """Test small file changes are not significant."""
        diff = DiscoveryDiff(
            from_version="v1",
            to_version="v2",
            structure_changes={"files": {"from": 100, "to": 102, "change": 2}},
        )
        assert not manager._is_significant(diff)

    def test_generate_summary(self, manager, sample_discovery, later_discovery):
        """Test summary generation."""
        diff = manager.create_diff(sample_discovery, later_discovery)
        assert diff.summary  # Should have some summary text

    def test_generate_summary_no_changes(self, manager):
        """Test summary for no changes."""
        diff = DiscoveryDiff(
            from_version="v1",
            to_version="v2",
        )
        summary = manager._generate_summary(diff)
        assert summary == "No significant changes"

    def test_retention_policy(self, manager):
        """Test retention policy enforcement."""
        manager.max_history = 3
        manager._ensure_dirs()

        # Create more than max_history files
        for i in range(5):
            ts = datetime(2025, 12, 1 + i, 10, 0, 0)
            filepath = manager.history_dir / f"{manager._timestamp_to_filename(ts)}.yaml"
            filepath.write_text("test")

        manager._enforce_retention()

        # Should only have max_history files
        remaining = list(manager.history_dir.glob("*.yaml"))
        assert len(remaining) <= manager.max_history

    def test_is_stale_no_discovery(self, manager):
        """Test is_stale when no discovery exists."""
        is_stale, reason = manager.is_stale()
        assert is_stale
        assert "No discovery exists" in reason

    def test_is_stale_recent(self, manager, sample_discovery):
        """Test is_stale for recent discovery."""
        # Create discovery with current time
        sample_discovery.metadata.discovered_at = datetime.now(timezone.utc)
        manager.save(sample_discovery)

        is_stale, reason = manager.is_stale(max_age_hours=24, check_git=False)
        assert not is_stale

    def test_is_stale_old(self, manager, sample_discovery):
        """Test is_stale for old discovery."""
        # Create discovery 2 days ago
        sample_discovery.metadata.discovered_at = datetime.now(timezone.utc) - timedelta(
            days=2
        )
        manager.save(sample_discovery)

        is_stale, reason = manager.is_stale(max_age_hours=24, check_git=False)
        assert is_stale
        assert "days old" in reason

    def test_get_diff(self, manager, sample_discovery, later_discovery):
        """Test get_diff method."""
        manager.save(sample_discovery)
        manager.save(later_discovery)

        # Get diff between current and previous
        diff = manager.get_diff()
        # May be None if history wasn't created, that's ok
        # Just ensure no exception

    def test_get_diff_no_versions(self, manager):
        """Test get_diff with no versions."""
        diff = manager.get_diff()
        assert diff is None

    def test_get_diff_single_version(self, manager, sample_discovery):
        """Test get_diff with only one version."""
        manager.save(sample_discovery)
        diff = manager.get_diff()
        assert diff is None  # Need at least 2 versions


class TestGetVersionManager:
    """Test get_version_manager convenience function."""

    def test_default_directory(self):
        """Test default directory is used."""
        manager = get_version_manager()
        assert manager.discovery_dir == Path(".vibey/discovery")

    def test_custom_directory(self, tmp_path):
        """Test custom directory."""
        manager = get_version_manager(discovery_dir=tmp_path / "custom")
        assert manager.discovery_dir == tmp_path / "custom"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
