"""
Tests for vibey.cli.roadmap_lib.cache module.

Tests the roadmap caching layer for performance optimization.
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import json

from vibey.cli.roadmap_lib.cache import RoadmapCache


class TestRoadmapCacheInit:
    """Test RoadmapCache initialization."""

    @patch('vibey.cli.roadmap_lib.cache.FileSystemManager')
    @patch.object(RoadmapCache, '_get_current_branch')
    @patch.object(RoadmapCache, '_try_load_from_disk')
    def test_init_default_settings(self, mock_load, mock_branch, mock_fs):
        """Test initialization with default settings."""
        mock_branch.return_value = "main"
        mock_fs_instance = MagicMock()
        mock_fs_instance.vibey_dir = Path("/tmp/.vibey")
        mock_fs.return_value = mock_fs_instance

        cache = RoadmapCache(Path("/tmp/project"))

        assert cache.root_dir == Path("/tmp/project")
        assert cache.enable_disk_cache is True
        assert cache._indexes_built is False

    @patch('vibey.cli.roadmap_lib.cache.FileSystemManager')
    @patch.object(RoadmapCache, '_get_current_branch')
    @patch.object(RoadmapCache, '_try_load_from_disk')
    def test_init_disable_disk_cache(self, mock_load, mock_branch, mock_fs):
        """Test initialization with disk cache disabled."""
        mock_branch.return_value = "main"
        mock_fs_instance = MagicMock()
        mock_fs_instance.vibey_dir = Path("/tmp/.vibey")
        mock_fs.return_value = mock_fs_instance

        cache = RoadmapCache(Path("/tmp/project"), enable_disk_cache=False)

        assert cache.enable_disk_cache is False
        mock_load.assert_not_called()


class TestGetTask:
    """Test task retrieval."""

    @pytest.fixture
    def cache(self):
        """Create RoadmapCache with mocks."""
        with patch('vibey.cli.roadmap_lib.cache.FileSystemManager') as mock_fs:
            with patch.object(RoadmapCache, '_get_current_branch', return_value='main'):
                with patch.object(RoadmapCache, '_try_load_from_disk'):
                    mock_fs_instance = MagicMock()
                    mock_fs_instance.vibey_dir = Path("/tmp/.vibey")
                    mock_fs.return_value = mock_fs_instance
                    c = RoadmapCache(Path("/tmp/project"), enable_disk_cache=False)
                    c.fs = mock_fs_instance
                    return c

    def test_get_task_from_cache(self, cache):
        """Test getting task from object cache."""
        cache._task_cache["task-001"] = {"id": "task-001", "title": "Test Task"}

        result = cache.get_task("task-001")

        assert result["id"] == "task-001"
        assert cache._hits == 1

    def test_get_task_not_found(self, cache):
        """Test getting task that doesn't exist."""
        cache._indexes_built = True
        cache._task_index = {}

        result = cache.get_task("nonexistent")

        assert result is None
        assert cache._misses == 1

    @patch('vibey.cli.roadmap_lib.cache.load_yaml')
    def test_get_task_from_index(self, mock_load_yaml, cache):
        """Test getting task from file via index."""
        cache._indexes_built = True
        task_path = Path("/tmp/.vibey/roadmap/tasks/task-001.yaml")
        cache._task_index = {"task-001": task_path}

        mock_load_yaml.return_value = {"task": {"id": "task-001", "title": "Test"}}

        result = cache.get_task("task-001")

        assert result["id"] == "task-001"
        assert "task-001" in cache._task_cache


class TestGetSprint:
    """Test sprint retrieval."""

    @pytest.fixture
    def cache(self):
        """Create RoadmapCache with mocks."""
        with patch('vibey.cli.roadmap_lib.cache.FileSystemManager') as mock_fs:
            with patch.object(RoadmapCache, '_get_current_branch', return_value='main'):
                with patch.object(RoadmapCache, '_try_load_from_disk'):
                    mock_fs_instance = MagicMock()
                    mock_fs_instance.vibey_dir = Path("/tmp/.vibey")
                    mock_fs.return_value = mock_fs_instance
                    c = RoadmapCache(Path("/tmp/project"), enable_disk_cache=False)
                    c.fs = mock_fs_instance
                    return c

    def test_get_sprint_from_cache(self, cache):
        """Test getting sprint from object cache."""
        cache._sprint_cache["sprint-001"] = {"id": "sprint-001", "name": "Sprint 1"}

        result = cache.get_sprint("sprint-001")

        assert result["id"] == "sprint-001"
        assert cache._hits == 1

    def test_get_sprint_not_found(self, cache):
        """Test getting sprint that doesn't exist."""
        cache._indexes_built = True
        cache._sprint_index = {}

        result = cache.get_sprint("nonexistent")

        assert result is None
        assert cache._misses == 1


class TestGetTrack:
    """Test track retrieval."""

    @pytest.fixture
    def cache(self):
        """Create RoadmapCache with mocks."""
        with patch('vibey.cli.roadmap_lib.cache.FileSystemManager') as mock_fs:
            with patch.object(RoadmapCache, '_get_current_branch', return_value='main'):
                with patch.object(RoadmapCache, '_try_load_from_disk'):
                    mock_fs_instance = MagicMock()
                    mock_fs_instance.vibey_dir = Path("/tmp/.vibey")
                    mock_fs.return_value = mock_fs_instance
                    c = RoadmapCache(Path("/tmp/project"), enable_disk_cache=False)
                    c.fs = mock_fs_instance
                    return c

    def test_get_track_from_cache(self, cache):
        """Test getting track from object cache."""
        cache._track_cache["track-001"] = {"id": "track-001", "name": "Track 1"}

        result = cache.get_track("track-001")

        assert result["id"] == "track-001"
        assert cache._hits == 1

    def test_get_track_not_found(self, cache):
        """Test getting track that doesn't exist."""
        cache._indexes_built = True
        cache._track_index = {}

        result = cache.get_track("nonexistent")

        assert result is None
        assert cache._misses == 1


class TestDependencyGraph:
    """Test dependency graph operations."""

    @pytest.fixture
    def cache(self):
        """Create RoadmapCache with mocks."""
        with patch('vibey.cli.roadmap_lib.cache.FileSystemManager') as mock_fs:
            with patch.object(RoadmapCache, '_get_current_branch', return_value='main'):
                with patch.object(RoadmapCache, '_try_load_from_disk'):
                    mock_fs_instance = MagicMock()
                    mock_fs_instance.vibey_dir = Path("/tmp/.vibey")
                    mock_fs.return_value = mock_fs_instance
                    c = RoadmapCache(Path("/tmp/project"), enable_disk_cache=False)
                    c.fs = mock_fs_instance
                    return c

    def test_get_dependencies(self, cache):
        """Test getting dependencies for an object."""
        cache._dep_graph = {
            "task-002": ["task-001"],
            "task-003": ["task-001", "task-002"],
        }

        result = cache.get_dependencies("task-003")

        assert result == ["task-001", "task-002"]

    def test_get_dependencies_none(self, cache):
        """Test getting dependencies when none exist."""
        cache._dep_graph = {}

        result = cache.get_dependencies("task-001")

        assert result == []

    def test_get_dependents(self, cache):
        """Test getting objects that depend on an object."""
        cache._reverse_dep_graph = {
            "task-001": ["task-002", "task-003"],
        }

        result = cache.get_dependents("task-001")

        assert result == ["task-002", "task-003"]

    def test_get_dependents_none(self, cache):
        """Test getting dependents when none exist."""
        cache._reverse_dep_graph = {}

        result = cache.get_dependents("task-003")

        assert result == []


class TestCacheInvalidation:
    """Test cache invalidation."""

    @pytest.fixture
    def cache(self):
        """Create RoadmapCache with mocks."""
        with patch('vibey.cli.roadmap_lib.cache.FileSystemManager') as mock_fs:
            with patch.object(RoadmapCache, '_get_current_branch', return_value='main'):
                with patch.object(RoadmapCache, '_try_load_from_disk'):
                    mock_fs_instance = MagicMock()
                    mock_fs_instance.vibey_dir = Path("/tmp/.vibey")
                    mock_fs.return_value = mock_fs_instance
                    c = RoadmapCache(Path("/tmp/project"), enable_disk_cache=False)
                    c.fs = mock_fs_instance
                    return c

    def test_full_invalidation(self, cache):
        """Test full cache invalidation."""
        # Populate cache
        cache._task_index = {"task-001": Path("/tmp/task.yaml")}
        cache._task_cache = {"task-001": {"id": "task-001"}}
        cache._dep_graph = {"task-001": []}
        cache._indexes_built = True

        cache.invalidate()

        assert cache._task_index == {}
        assert cache._task_cache == {}
        assert cache._dep_graph is None
        assert cache._indexes_built is False

    def test_partial_invalidation(self, cache):
        """Test partial invalidation for specific file."""
        file_path = Path("/tmp/.vibey/roadmap/tasks/task-001.yaml")
        cache._file_mtimes = {file_path: 1234567890.0}
        cache._task_cache = {"task-001": {"id": "task-001"}}

        cache.invalidate(file_path)

        assert file_path not in cache._file_mtimes
        assert cache._task_cache == {}


class TestCacheStatistics:
    """Test cache statistics."""

    @pytest.fixture
    def cache(self):
        """Create RoadmapCache with mocks."""
        with patch('vibey.cli.roadmap_lib.cache.FileSystemManager') as mock_fs:
            with patch.object(RoadmapCache, '_get_current_branch', return_value='main'):
                with patch.object(RoadmapCache, '_try_load_from_disk'):
                    mock_fs_instance = MagicMock()
                    mock_fs_instance.vibey_dir = Path("/tmp/.vibey")
                    mock_fs.return_value = mock_fs_instance
                    c = RoadmapCache(Path("/tmp/project"), enable_disk_cache=False)
                    c.fs = mock_fs_instance
                    return c

    def test_get_stats_initial(self, cache):
        """Test initial statistics."""
        stats = cache.get_stats()

        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['hit_rate'] == 0.0
        assert stats['indexes_built'] is False

    def test_get_stats_with_queries(self, cache):
        """Test statistics after queries."""
        cache._hits = 8
        cache._misses = 2
        cache._builds = 1
        cache._indexes_built = True
        cache._task_index = {"a": None, "b": None}

        stats = cache.get_stats()

        assert stats['hits'] == 8
        assert stats['misses'] == 2
        assert stats['total_queries'] == 10
        assert stats['hit_rate'] == 80.0
        assert stats['index_builds'] == 1
        assert stats['tasks_indexed'] == 2


class TestCacheValidity:
    """Test cache validity checking."""

    @pytest.fixture
    def cache(self):
        """Create RoadmapCache with mocks."""
        with patch('vibey.cli.roadmap_lib.cache.FileSystemManager') as mock_fs:
            with patch.object(RoadmapCache, '_get_current_branch', return_value='main'):
                with patch.object(RoadmapCache, '_try_load_from_disk'):
                    mock_fs_instance = MagicMock()
                    mock_fs_instance.vibey_dir = Path("/tmp/.vibey")
                    mock_fs.return_value = mock_fs_instance
                    c = RoadmapCache(Path("/tmp/project"), enable_disk_cache=False)
                    c.fs = mock_fs_instance
                    return c

    def test_validity_no_files(self, cache):
        """Test validity with no tracked files."""
        cache._file_mtimes = {}

        result = cache.check_validity()

        assert result is True

    def test_validity_files_unchanged(self, cache):
        """Test validity when files unchanged."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_stat = MagicMock()
        mock_stat.st_mtime = 1000.0
        mock_path.stat.return_value = mock_stat

        cache._file_mtimes = {mock_path: 1000.0}

        result = cache.check_validity()

        assert result is True

    def test_validity_file_modified(self, cache):
        """Test validity when file was modified."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_stat = MagicMock()
        mock_stat.st_mtime = 2000.0  # Modified
        mock_path.stat.return_value = mock_stat

        cache._file_mtimes = {mock_path: 1000.0}  # Cached old mtime

        result = cache.check_validity()

        assert result is False

    def test_validity_file_deleted(self, cache):
        """Test validity when file was deleted."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False  # File deleted

        cache._file_mtimes = {mock_path: 1000.0}

        result = cache.check_validity()

        assert result is False


class TestBranchDetection:
    """Test git branch detection."""

    @patch('vibey.cli.roadmap_lib.cache.FileSystemManager')
    @patch('subprocess.run')
    def test_get_current_branch_success(self, mock_run, mock_fs):
        """Test successful branch detection."""
        mock_fs_instance = MagicMock()
        mock_fs_instance.vibey_dir = Path("/tmp/.vibey")
        mock_fs.return_value = mock_fs_instance

        mock_run.return_value = MagicMock(returncode=0, stdout="feature-branch\n")

        with patch.object(RoadmapCache, '_try_load_from_disk'):
            cache = RoadmapCache(Path("/tmp/project"), enable_disk_cache=False)

        assert cache.current_branch == "feature-branch"
        assert cache.is_main_branch is False

    @patch('vibey.cli.roadmap_lib.cache.FileSystemManager')
    @patch('subprocess.run')
    def test_get_current_branch_main(self, mock_run, mock_fs):
        """Test main branch detection."""
        mock_fs_instance = MagicMock()
        mock_fs_instance.vibey_dir = Path("/tmp/.vibey")
        mock_fs.return_value = mock_fs_instance

        mock_run.return_value = MagicMock(returncode=0, stdout="main\n")

        with patch.object(RoadmapCache, '_try_load_from_disk'):
            cache = RoadmapCache(Path("/tmp/project"), enable_disk_cache=False)

        assert cache.current_branch == "main"
        assert cache.is_main_branch is True


class TestGetMtime:
    """Test mtime retrieval."""

    @pytest.fixture
    def cache(self):
        """Create RoadmapCache with mocks."""
        with patch('vibey.cli.roadmap_lib.cache.FileSystemManager') as mock_fs:
            with patch.object(RoadmapCache, '_get_current_branch', return_value='main'):
                with patch.object(RoadmapCache, '_try_load_from_disk'):
                    mock_fs_instance = MagicMock()
                    mock_fs_instance.vibey_dir = Path("/tmp/.vibey")
                    mock_fs.return_value = mock_fs_instance
                    c = RoadmapCache(Path("/tmp/project"), enable_disk_cache=False)
                    c.fs = mock_fs_instance
                    return c

    def test_get_mtime_cached(self, cache):
        """Test getting cached mtime."""
        file_path = Path("/tmp/test.yaml")
        cache._file_mtimes = {file_path: 1234567890.0}

        result = cache.get_mtime(file_path)

        assert result == 1234567890.0

    def test_get_mtime_not_cached(self, cache):
        """Test getting mtime for uncached file."""
        file_path = Path("/tmp/uncached.yaml")
        cache._file_mtimes = {}

        result = cache.get_mtime(file_path)

        assert result is None


class TestGetTasksBySprint:
    """Test getting tasks by sprint."""

    @pytest.fixture
    def cache(self):
        """Create RoadmapCache with mocks."""
        with patch('vibey.cli.roadmap_lib.cache.FileSystemManager') as mock_fs:
            with patch.object(RoadmapCache, '_get_current_branch', return_value='main'):
                with patch.object(RoadmapCache, '_try_load_from_disk'):
                    mock_fs_instance = MagicMock()
                    mock_fs_instance.vibey_dir = Path("/tmp/.vibey")
                    mock_fs.return_value = mock_fs_instance
                    c = RoadmapCache(Path("/tmp/project"), enable_disk_cache=False)
                    c.fs = mock_fs_instance
                    return c

    def test_get_tasks_by_sprint(self, cache):
        """Test filtering tasks by sprint ID."""
        cache._indexes_built = True
        cache._task_index = {}
        cache._task_cache = {
            "task-001": {"id": "task-001", "sprint_id": "sprint-001"},
            "task-002": {"id": "task-002", "sprint_id": "sprint-001"},
            "task-003": {"id": "task-003", "sprint_id": "sprint-002"},
        }

        # Override get_all_tasks to return cached tasks
        cache.get_all_tasks = lambda: list(cache._task_cache.values())

        result = cache.get_tasks_by_sprint("sprint-001")

        assert len(result) == 2
        assert all(t["sprint_id"] == "sprint-001" for t in result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
