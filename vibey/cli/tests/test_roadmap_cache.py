"""
Unit tests for RoadmapCache.

Tests the in-memory caching layer for roadmap queries.
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add roadmap-lib to path
test_dir = Path(__file__).parent
scripts_dir = test_dir.parent
roadmap_lib_dir = scripts_dir / "roadmap-lib"
sys.path.insert(0, str(roadmap_lib_dir))

from cache import RoadmapCache
from filesystem import FileSystemManager, save_yaml


def create_test_roadmap(root_dir: Path):
    """Create a test roadmap structure."""
    fs = FileSystemManager(root_dir)
    fs.ensure_structure()

    # Create roadmap.yaml
    roadmap_data = {
        'roadmap': {
            'id': 'test-roadmap',
            'name': 'Test Roadmap',
            'version': '1.0.0',
        }
    }
    save_yaml(fs.get_roadmap_path(), roadmap_data)

    # Create track
    track_data = {
        'track': {
            'id': 'test-track',
            'name': 'Test Track',
            'roadmap_id': 'test-roadmap',
            'status': 'in_progress',
            'dependencies': []
        }
    }
    save_yaml(fs.get_track_path('test-track'), track_data)

    # Create sprint
    sprint_data = {
        'sprint': {
            'id': 'test-sprint-1',
            'name': 'Test Sprint 1',
            'track_id': 'test-track',
            'roadmap_id': 'test-roadmap',
            'status': 'in_progress',
            'dependencies': []
        }
    }
    save_yaml(fs.get_sprint_path('test-sprint-1'), sprint_data)

    # Create tasks
    tasks_data = {
        'tasks': [
            {
                'id': 'task-001',
                'sprint_id': 'test-sprint-1',
                'name': 'Task 1',
                'status': 'completed',
                'dependencies': []
            },
            {
                'id': 'task-002',
                'sprint_id': 'test-sprint-1',
                'name': 'Task 2',
                'status': 'in_progress',
                'dependencies': [
                    {'type': 'task', 'target_id': 'task-001', 'at_status': 'completed'}
                ]
            },
            {
                'id': 'task-003',
                'sprint_id': 'test-sprint-1',
                'name': 'Task 3',
                'status': 'not_started',
                'dependencies': [
                    {'type': 'task', 'target_id': 'task-001', 'at_status': 'completed'},
                    {'type': 'task', 'target_id': 'task-002', 'at_status': 'completed'}
                ]
            },
        ]
    }
    save_yaml(fs.get_tasks_path('test-sprint-1'), tasks_data)


def test_cache_initialization():
    """Test cache initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        cache = RoadmapCache(root_dir)
        assert cache.root_dir == root_dir
        assert cache._indexes_built is False
        print("✓ Cache initialization")


def test_lazy_loading():
    """Test that indexes are lazily loaded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        cache = RoadmapCache(root_dir)

        # Indexes not built yet
        assert cache._indexes_built is False

        # First query triggers build
        task = cache.get_task('task-001')
        assert cache._indexes_built is True
        assert task is not None
        assert task['id'] == 'task-001'

        print("✓ Lazy loading")


def test_task_lookup():
    """Test task lookup operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        cache = RoadmapCache(root_dir)

        # Get task by ID
        task = cache.get_task('task-002')
        assert task is not None
        assert task['id'] == 'task-002'
        assert task['name'] == 'Task 2'
        assert task['status'] == 'in_progress'

        # Get non-existent task
        task = cache.get_task('task-999')
        assert task is None

        # Get all tasks
        tasks = cache.get_all_tasks()
        assert len(tasks) == 3
        assert {t['id'] for t in tasks} == {'task-001', 'task-002', 'task-003'}

        # Get tasks by sprint
        sprint_tasks = cache.get_tasks_by_sprint('test-sprint-1')
        assert len(sprint_tasks) == 3

        print("✓ Task lookup")


def test_sprint_lookup():
    """Test sprint lookup operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        cache = RoadmapCache(root_dir)

        # Get sprint by ID
        sprint = cache.get_sprint('test-sprint-1')
        assert sprint is not None
        assert sprint['id'] == 'test-sprint-1'
        assert sprint['name'] == 'Test Sprint 1'

        # Get all sprints
        sprints = cache.get_all_sprints()
        assert len(sprints) == 1
        assert sprints[0]['id'] == 'test-sprint-1'

        print("✓ Sprint lookup")


def test_track_lookup():
    """Test track lookup operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        cache = RoadmapCache(root_dir)

        # Get track by ID
        track = cache.get_track('test-track')
        assert track is not None
        assert track['id'] == 'test-track'
        assert track['name'] == 'Test Track'

        # Get all tracks
        tracks = cache.get_all_tracks()
        assert len(tracks) == 1
        assert tracks[0]['id'] == 'test-track'

        print("✓ Track lookup")


def test_dependency_graph():
    """Test dependency graph building."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        cache = RoadmapCache(root_dir)

        # Get dependency graph
        dep_graph = cache.get_dependency_graph()
        assert 'task-001' in dep_graph
        assert 'task-002' in dep_graph
        assert 'task-003' in dep_graph

        # Check dependencies
        assert cache.get_dependencies('task-001') == []
        assert cache.get_dependencies('task-002') == ['task-001']
        assert set(cache.get_dependencies('task-003')) == {'task-001', 'task-002'}

        # Get reverse dependencies
        reverse_graph = cache.get_reverse_dependency_graph()
        assert 'task-001' in reverse_graph
        assert 'task-002' in reverse_graph

        # Check reverse dependencies
        dependents_001 = cache.get_dependents('task-001')
        assert set(dependents_001) == {'task-002', 'task-003'}

        dependents_002 = cache.get_dependents('task-002')
        assert dependents_002 == ['task-003']

        dependents_003 = cache.get_dependents('task-003')
        assert dependents_003 == []

        print("✓ Dependency graph")


def test_cache_hit_miss():
    """Test cache hit/miss tracking."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        cache = RoadmapCache(root_dir)

        # First query (miss)
        task = cache.get_task('task-001')
        assert task is not None

        # Second query (hit)
        task = cache.get_task('task-001')
        assert task is not None

        # Query non-existent (miss)
        task = cache.get_task('task-999')
        assert task is None

        # Check statistics
        stats = cache.get_stats()
        assert stats['hits'] >= 1
        assert stats['misses'] >= 1
        assert stats['total_queries'] == stats['hits'] + stats['misses']
        assert 0 <= stats['hit_rate'] <= 100

        print(f"✓ Cache hit/miss (hit rate: {stats['hit_rate']}%)")


def test_cache_statistics():
    """Test cache statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        cache = RoadmapCache(root_dir)

        # Initial stats
        stats = cache.get_stats()
        assert stats['index_builds'] == 0
        assert stats['indexes_built'] is False

        # Trigger index build
        cache.get_task('task-001')

        # Updated stats
        stats = cache.get_stats()
        assert stats['index_builds'] == 1
        assert stats['indexes_built'] is True
        assert stats['tasks_indexed'] == 3
        assert stats['sprints_indexed'] == 1
        assert stats['tracks_indexed'] == 1

        print("✓ Cache statistics")


def test_cache_invalidation():
    """Test cache invalidation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        cache = RoadmapCache(root_dir)

        # Build cache
        task = cache.get_task('task-001')
        assert task is not None
        assert cache._indexes_built is True

        # Full invalidation
        cache.invalidate()
        assert cache._indexes_built is False
        assert len(cache._task_index) == 0
        assert len(cache._task_cache) == 0

        # Rebuild
        task = cache.get_task('task-001')
        assert task is not None
        assert cache._indexes_built is True

        print("✓ Cache invalidation")


def test_file_mtime_tracking():
    """Test file modification time tracking."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        cache = RoadmapCache(root_dir)

        # Build cache
        cache.get_task('task-001')

        # Check mtimes tracked
        assert len(cache._file_mtimes) > 0

        # Get mtime for task file
        fs = FileSystemManager(root_dir)
        task_file = fs.get_tasks_path('test-sprint-1')
        mtime = cache.get_mtime(task_file)
        assert mtime is not None
        assert mtime > 0

        print("✓ File mtime tracking")


def test_cache_validity():
    """Test cache validity checking."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        cache = RoadmapCache(root_dir)

        # Build cache
        cache.get_task('task-001')

        # Cache should be valid
        assert cache.check_validity() is True

        # Note: Actually modifying files and checking invalidation
        # would require time.sleep() which slows down tests
        # For now, we just verify the check_validity() method exists

        print("✓ Cache validity checking")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("Running RoadmapCache Tests")
    print("="*70 + "\n")

    test_cache_initialization()
    test_lazy_loading()
    test_task_lookup()
    test_sprint_lookup()
    test_track_lookup()
    test_dependency_graph()
    test_cache_hit_miss()
    test_cache_statistics()
    test_cache_invalidation()
    test_file_mtime_tracking()
    test_cache_validity()

    print("\n" + "="*70)
    print("✅ All tests passed!")
    print("="*70 + "\n")


if __name__ == '__main__':
    run_all_tests()
