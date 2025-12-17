"""
Integration test for roadmap CLI cache integration.

Tests that the CLI properly initializes and uses RoadmapCache.
"""

import sys
from pathlib import Path
import tempfile

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
            },
            {
                'id': 'task-002',
                'sprint_id': 'test-sprint-1',
                'name': 'Task 2',
                'status': 'in_progress',
            },
        ]
    }
    save_yaml(fs.get_tasks_path('test-sprint-1'), tasks_data)


def test_cache_initialization():
    """Test that cache is properly initialized."""
    print("\n" + "="*70)
    print("Test: Cache Initialization")
    print("="*70)

    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        # Simulate CLI initialization
        cache = RoadmapCache(root_dir)

        # Verify cache is initialized
        assert cache is not None
        assert cache.root_dir == root_dir
        assert cache._indexes_built is False  # Lazy loading

        # Trigger index build
        task = cache.get_task('task-001')
        assert task is not None
        assert cache._indexes_built is True

        print("✓ Cache properly initialized")
        print("✓ Lazy loading works")
        print()


def test_cache_disabled():
    """Test that cache can be disabled."""
    print("="*70)
    print("Test: Cache Disabled (--no-cache)")
    print("="*70)

    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        # Simulate --no-cache flag
        cache = None  # Cache is not initialized

        # Commands should still work without cache
        # (using fallback loading)
        from cache_helpers import get_cached_task

        task = get_cached_task(cache, 'task-001', root_dir)
        assert task is not None
        assert task['id'] == 'task-001'

        print("✓ Commands work without cache (--no-cache)")
        print()


def test_cache_helpers():
    """Test cache helper functions."""
    print("="*70)
    print("Test: Cache Helper Functions")
    print("="*70)

    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        cache = RoadmapCache(root_dir)

        from cache_helpers import (
            get_cached_task,
            get_cached_sprint,
            get_cached_track,
            get_all_cached_tasks,
            get_all_cached_sprints,
            get_all_cached_tracks,
        )

        # Test single object lookups
        task = get_cached_task(cache, 'task-001')
        assert task is not None
        assert task['id'] == 'task-001'
        print("✓ get_cached_task")

        sprint = get_cached_sprint(cache, 'test-sprint-1')
        assert sprint is not None
        assert sprint['id'] == 'test-sprint-1'
        print("✓ get_cached_sprint")

        track = get_cached_track(cache, 'test-track')
        assert track is not None
        assert track['id'] == 'test-track'
        print("✓ get_cached_track")

        # Test bulk lookups
        tasks = get_all_cached_tasks(cache)
        assert len(tasks) == 2
        print("✓ get_all_cached_tasks")

        sprints = get_all_cached_sprints(cache)
        assert len(sprints) == 1
        print("✓ get_all_cached_sprints")

        tracks = get_all_cached_tracks(cache)
        assert len(tracks) == 1
        print("✓ get_all_cached_tracks")

        # Check cache stats
        stats = cache.get_stats()
        print(f"\nCache Stats:")
        print(f"  Hits: {stats['hits']}")
        print(f"  Misses: {stats['misses']}")
        print(f"  Hit rate: {stats['hit_rate']}%")
        print()


def test_cache_invalidation():
    """Test cache invalidation."""
    print("="*70)
    print("Test: Cache Invalidation")
    print("="*70)

    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        cache = RoadmapCache(root_dir)

        # Load data
        task = cache.get_task('task-001')
        assert task is not None
        assert cache._indexes_built is True

        # Simulate state-changing command
        # (e.g., roadmap start, complete, assign)
        cache.invalidate()

        # Verify cache was invalidated
        assert cache._indexes_built is False

        # Re-load should rebuild cache
        task = cache.get_task('task-001')
        assert task is not None
        assert cache._indexes_built is True

        print("✓ Cache invalidation works")
        print("✓ Cache rebuilds after invalidation")
        print()


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*70)
    print("Running CLI Cache Integration Tests")
    print("="*70 + "\n")

    test_cache_initialization()
    test_cache_disabled()
    test_cache_helpers()
    test_cache_invalidation()

    print("="*70)
    print("✅ All CLI cache integration tests passed!")
    print("="*70 + "\n")


if __name__ == '__main__':
    run_all_tests()
