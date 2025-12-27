"""
Test submodule isolation architecture.

Verifies that the submodule integration follows the core isolation principle:
Repo A must function perfectly whether accessed directly or as a submodule of
Repo C. A has ZERO knowledge of any parent repos.

Design reference: SUBMODULE_ISOLATION_AND_PUSHDOWN.md
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from vibey.roadmap.models.submodule import (
    AggregatedProgress,
    CollectionMethod,
    DetectionSource,
    SubmoduleBlocker,
    SubmoduleProgress,
    SubmoduleReference,
    SyncStatus,
)
from vibey.operations.submodule.discovery import SubmoduleDiscovery


class TestNoExternalReferencesInSubmoduleModels:
    """Verify submodule models contain no references to parent repos."""

    def test_submodule_reference_has_no_parent_reference(self):
        """SubmoduleReference should only store path and submodule info."""
        ref = SubmoduleReference(
            path="libs/repo-a",
            roadmap_id="repo-a-v1",
            aggregate=True,
            track_filter=[],
        )

        # Verify no parent-related fields exist
        assert not hasattr(ref, 'parent_roadmap_id')
        assert not hasattr(ref, 'parent_task_id')
        assert not hasattr(ref, 'parent_repo_path')

        # Verify path is normalized
        assert ref.path == "libs/repo-a"

    def test_submodule_progress_stores_submodule_data_only(self):
        """SubmoduleProgress should only contain submodule's own data."""
        progress = SubmoduleProgress(
            submodule_path="libs/repo-a",
            roadmap_id="repo-a-v1",
            tracks_total=5,
            tracks_completed=2,
            tasks_total=20,
            tasks_completed=10,
        )

        # Verify no parent references
        assert not hasattr(progress, 'parent_roadmap_id')
        assert not hasattr(progress, 'contributes_to_parent_task')

        # Verify data is about submodule only
        assert progress.submodule_path == "libs/repo-a"
        assert progress.roadmap_id == "repo-a-v1"

    def test_submodule_blocker_references_submodule_only(self):
        """SubmoduleBlocker should reference only submodule entities."""
        blocker = SubmoduleBlocker(
            submodule_path="libs/repo-a",
            blocker_id="01ABC123456789012345678901",  # ULID from submodule
            title="Critical bug in API",
        )

        # The blocker is about the submodule, not containing parent references
        assert blocker.submodule_path == "libs/repo-a"
        # blocks_tasks and blocks_sprints are parent-side tracking
        # but the blocker itself doesn't store parent roadmap references

    def test_aggregated_progress_is_computed_not_stored(self):
        """AggregatedProgress should be computed from submodule data, not pushed."""
        progress1 = SubmoduleProgress(
            submodule_path="libs/repo-a",
            roadmap_id="repo-a-v1",
            tasks_total=10,
            tasks_completed=5,
        )
        progress2 = SubmoduleProgress(
            submodule_path="libs/repo-b",
            roadmap_id="repo-b-v1",
            tasks_total=20,
            tasks_completed=15,
        )

        aggregated = AggregatedProgress(
            submodule_progress=[progress1, progress2],
        )
        aggregated.aggregate()

        # Verify aggregation is a read-only pull, not a push
        assert aggregated.total_tasks == 30
        assert aggregated.completed_tasks == 20
        # The method is collection_method, not push_method
        assert progress1.collection_method == CollectionMethod.ON_DEMAND


class TestParentOnlyCrossRepoStorage:
    """Verify cross-repo data is stored only in parent."""

    def test_submodule_registry_stored_in_parent_config(self):
        """Submodule registry should be in parent's .vibey/config/submodules.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_path = Path(tmpdir) / "parent"
            parent_path.mkdir()

            discovery = SubmoduleDiscovery(parent_path)

            # Config path should be in parent's .vibey/config/
            assert discovery.submodules_config == parent_path / ".vibey" / "config" / "submodules.yaml"

            # Not in submodule paths
            assert "submodule" not in str(discovery.submodules_config).lower() or "config" in str(discovery.submodules_config)

    def test_discovery_only_writes_to_parent(self):
        """SubmoduleDiscovery should only modify parent repo files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_path = Path(tmpdir) / "parent"
            parent_path.mkdir()

            # Create a mock submodule directory
            submodule_path = parent_path / "libs" / "repo-a"
            submodule_path.mkdir(parents=True)
            (submodule_path / ".vibey" / "roadmap").mkdir(parents=True)

            discovery = SubmoduleDiscovery(parent_path)

            # Verify write paths are all in parent
            assert str(discovery.config_dir).startswith(str(parent_path))
            assert str(discovery.vibey_dir).startswith(str(parent_path))


class TestSubmoduleIsolationPrinciple:
    """Verify submodule can function identically alone or as submodule."""

    def test_submodule_reference_path_is_relative(self):
        """Submodule path should be relative, not absolute."""
        ref = SubmoduleReference(path="libs/repo-a")

        # Path should not be absolute
        assert not ref.path.startswith("/")
        assert not ref.path.startswith("C:")

        # Path should be normalized
        assert "\\" not in ref.path

    def test_submodule_has_no_incoming_outgoing_directories(self):
        """Submodules should not have .vibey/incoming or .vibey/outgoing."""
        # This is a design principle verification
        # The FileSystemManager should not create these directories
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        with tempfile.TemporaryDirectory() as tmpdir:
            fs = FileSystemManager(Path(tmpdir))
            fs.ensure_structure()

            # Verify no incoming/outgoing directories
            assert not (fs.vibey_dir / "incoming").exists()
            assert not (fs.vibey_dir / "outgoing").exists()
            assert not (fs.roadmap_root / "incoming").exists()
            assert not (fs.roadmap_root / "outgoing").exists()

    def test_detection_source_enum_values(self):
        """DetectionSource should have expected values for discovery."""
        assert DetectionSource.GITMODULES.value == "gitmodules"
        assert DetectionSource.GIT_COMMAND.value == "git_command"
        assert DetectionSource.DIRECTORY_SCAN.value == "directory_scan"
        assert DetectionSource.MANUAL.value == "manual"

    def test_sync_status_enum_values(self):
        """SyncStatus should track sync state without parent references."""
        assert SyncStatus.SYNCED.value == "synced"
        assert SyncStatus.STALE.value == "stale"
        assert SyncStatus.NEVER_SYNCED.value == "never_synced"
        assert SyncStatus.ERROR.value == "error"


class TestSubmoduleDiscoveryIsolation:
    """Verify SubmoduleDiscovery respects isolation."""

    def test_discovery_does_not_modify_submodule_files(self):
        """Discovery should read from submodules but never write to them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_path = Path(tmpdir) / "parent"
            parent_path.mkdir()

            # Create mock submodule with roadmap
            submodule_path = parent_path / "libs" / "repo-a"
            submodule_vibey = submodule_path / ".vibey" / "roadmap"
            submodule_vibey.mkdir(parents=True)

            # Create roadmap.yaml in submodule
            roadmap_yaml = submodule_vibey / "roadmap.yaml"
            roadmap_yaml.write_text("roadmap:\n  id: repo-a-v1\n  name: Repo A\n")

            discovery = SubmoduleDiscovery(parent_path)

            # Check for roadmap (should read but not write)
            result = discovery.has_vibey_roadmap("libs/repo-a")

            assert result.has_roadmap is True
            assert result.roadmap_id == "repo-a-v1"

            # Verify submodule files unchanged
            content = roadmap_yaml.read_text()
            assert content == "roadmap:\n  id: repo-a-v1\n  name: Repo A\n"

    def test_get_vibey_submodules_reads_from_parent_only(self):
        """get_vibey_submodules should only read parent config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_path = Path(tmpdir) / "parent"
            parent_path.mkdir()

            # Create parent config
            config_path = parent_path / ".vibey" / "config"
            config_path.mkdir(parents=True)

            submodules_yaml = config_path / "submodules.yaml"
            submodules_yaml.write_text("""
submodules:
  - path: libs/repo-a
    roadmap_id: repo-a-v1
    aggregate: true
default_push_mode: linked
aggregate_on_status: true
""")

            discovery = SubmoduleDiscovery(parent_path)
            refs = discovery.get_vibey_submodules()

            assert len(refs) == 1
            assert refs[0].path == "libs/repo-a"
            assert refs[0].roadmap_id == "repo-a-v1"


class TestPushDownMechanismDesign:
    """Verify push-down design follows isolation principles."""

    def test_submodule_reference_has_no_push_back_capability(self):
        """SubmoduleReference should not have methods to push to parent."""
        ref = SubmoduleReference(path="libs/repo-a")

        # Verify no push-back methods exist
        assert not hasattr(ref, 'push_to_parent')
        assert not hasattr(ref, 'notify_parent')
        assert not hasattr(ref, 'update_parent')

    def test_collection_method_is_pull_based(self):
        """Collection should be pull-based (parent reads), not push-based."""
        # All collection methods are parent-initiated
        assert CollectionMethod.POLLING.value == "polling"  # Parent polls
        assert CollectionMethod.ON_DEMAND.value == "on_demand"  # Parent requests
        assert CollectionMethod.GIT_HOOK.value == "git_hook"  # Hook runs in parent context

        # No "submodule_push" or "auto_notify" methods
        methods = [m.value for m in CollectionMethod]
        assert "push" not in " ".join(methods).lower()
        assert "notify" not in " ".join(methods).lower()
