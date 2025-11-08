"""
Test persistent disk cache functionality.

Tests that cache saves to disk and loads on subsequent initializations.
"""

import sys
from pathlib import Path
import tempfile
import time
import json

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
                'dependencies': [
                    {'target_id': 'task-002', 'type': 'blocks'}
                ]
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


def test_disk_cache_creation():
    """Test that cache saves to disk after building."""
    print("\n" + "="*70)
    print("Test: Disk Cache Creation")
    print("="*70)

    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        # Create cache with disk cache enabled
        cache = RoadmapCache(root_dir, enable_disk_cache=True)

        # Trigger index build
        task = cache.get_task('task-001')
        assert task is not None

        # Check that cache files were created
        cache_dir = root_dir / '.vibey' / '.cache'
        assert cache_dir.exists()
        assert (cache_dir / 'indexes.json').exists()
        assert (cache_dir / 'mtimes.json').exists()

        print("✓ Cache directory created")
        print("✓ indexes.json created")
        print("✓ mtimes.json created")

        # Trigger dependency graph build
        deps = cache.get_dependencies('task-001')
        assert len(deps) == 1

        # Check that graphs file was created
        assert (cache_dir / 'graphs.json').exists()
        print("✓ graphs.json created")

        print()


def test_disk_cache_loading():
    """Test that cache loads from disk on subsequent initializations."""
    print("="*70)
    print("Test: Disk Cache Loading")
    print("="*70)

    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        # First cache: build and save
        cache1 = RoadmapCache(root_dir, enable_disk_cache=True)
        task = cache1.get_task('task-001')
        deps = cache1.get_dependencies('task-001')
        stats1 = cache1.get_stats()

        print(f"First cache:")
        print(f"  Index builds: {stats1['index_builds']}")
        print(f"  Disk loads: {stats1['disk_loads']}")
        assert stats1['index_builds'] == 1
        assert stats1['disk_loads'] == 0

        # Second cache: should load from disk
        cache2 = RoadmapCache(root_dir, enable_disk_cache=True)
        stats2 = cache2.get_stats()

        print(f"\nSecond cache (loaded from disk):")
        print(f"  Index builds: {stats2['index_builds']}")
        print(f"  Disk loads: {stats2['disk_loads']}")
        assert stats2['index_builds'] == 0  # No rebuild needed
        assert stats2['disk_loads'] == 1    # Loaded from disk

        # Verify data is correct
        task2 = cache2.get_task('task-001')
        assert task2 is not None
        assert task2['id'] == 'task-001'

        deps2 = cache2.get_dependencies('task-001')
        assert deps2 == deps

        print("✓ Cache loaded from disk successfully")
        print("✓ Data matches original cache")
        print()


def test_disk_cache_invalidation():
    """Test that disk cache invalidates when files are modified."""
    print("="*70)
    print("Test: Disk Cache Invalidation")
    print("="*70)

    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        # First cache: build and save
        cache1 = RoadmapCache(root_dir, enable_disk_cache=True)
        task = cache1.get_task('task-001')

        # Modify a file
        fs = FileSystemManager(root_dir)
        tasks_file = fs.get_tasks_path('test-sprint-1')
        time.sleep(0.01)  # Ensure mtime changes
        tasks_file.touch()  # Update mtime

        # Second cache: should detect stale cache and rebuild
        cache2 = RoadmapCache(root_dir, enable_disk_cache=True)
        stats2 = cache2.get_stats()

        print(f"Cache after file modification:")
        print(f"  Index builds: {stats2['index_builds']}")
        print(f"  Disk loads: {stats2['disk_loads']}")
        assert stats2['disk_loads'] == 0  # Disk cache was invalid

        print("✓ Stale cache detected")
        print("✓ Cache rebuilt from filesystem")
        print()


def test_disk_cache_disabled():
    """Test that cache works with disk cache disabled."""
    print("="*70)
    print("Test: Disk Cache Disabled")
    print("="*70)

    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        # Create cache with disk cache disabled
        cache = RoadmapCache(root_dir, enable_disk_cache=False)

        # Trigger index build
        task = cache.get_task('task-001')
        assert task is not None

        # Check that cache files were NOT created
        cache_dir = root_dir / '.vibey' / '.cache'
        assert not (cache_dir / 'indexes.json').exists()

        print("✓ Disk cache disabled")
        print("✓ No cache files created")
        print("✓ In-memory cache still works")
        print()


def test_disk_cache_performance():
    """Test that disk cache loading is fast (< 10ms target)."""
    print("="*70)
    print("Test: Disk Cache Performance")
    print("="*70)

    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        # First cache: build and save
        cache1 = RoadmapCache(root_dir, enable_disk_cache=True)
        cache1.get_task('task-001')
        cache1.get_dependencies('task-001')

        # Second cache: measure load time
        start = time.time()
        cache2 = RoadmapCache(root_dir, enable_disk_cache=True)
        load_time = (time.time() - start) * 1000  # Convert to ms

        stats = cache2.get_stats()
        print(f"Cache load from disk:")
        print(f"  Time: {load_time:.2f}ms")
        print(f"  Disk loads: {stats['disk_loads']}")

        # Verify it loaded from disk
        assert stats['disk_loads'] == 1

        # Check performance target
        target = 10.0  # 10ms target
        if load_time < target:
            print(f"✓ Performance target met: < {target}ms (actual: {load_time:.2f}ms)")
        else:
            print(f"⚠️ Performance target missed: < {target}ms (actual: {load_time:.2f}ms)")

        print()


def test_cache_file_format():
    """Test that cache files are valid JSON."""
    print("="*70)
    print("Test: Cache File Format")
    print("="*70)

    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        create_test_roadmap(root_dir)

        # Create cache
        cache = RoadmapCache(root_dir, enable_disk_cache=True)
        cache.get_task('task-001')
        cache.get_dependencies('task-001')

        # Load and validate cache files
        cache_dir = root_dir / '.vibey' / '.cache'

        # Validate indexes.json
        with open(cache_dir / 'indexes.json', 'r') as f:
            indexes = json.load(f)
            assert 'tasks' in indexes
            assert 'sprints' in indexes
            assert 'tracks' in indexes
            print("✓ indexes.json is valid JSON")
            print(f"  Tasks indexed: {len(indexes['tasks'])}")
            print(f"  Sprints indexed: {len(indexes['sprints'])}")
            print(f"  Tracks indexed: {len(indexes['tracks'])}")

        # Validate graphs.json
        with open(cache_dir / 'graphs.json', 'r') as f:
            graphs = json.load(f)
            assert 'dependencies' in graphs
            assert 'reverse_dependencies' in graphs
            print("✓ graphs.json is valid JSON")

        # Validate mtimes.json
        with open(cache_dir / 'mtimes.json', 'r') as f:
            mtimes = json.load(f)
            assert len(mtimes) > 0
            print("✓ mtimes.json is valid JSON")
            print(f"  Files tracked: {len(mtimes)}")

        print()


def run_all_tests():
    """Run all persistent cache tests."""
    print("\n" + "="*70)
    print("Running Persistent Disk Cache Tests")
    print("="*70 + "\n")

    test_disk_cache_creation()
    test_disk_cache_loading()
    test_disk_cache_invalidation()
    test_disk_cache_disabled()
    test_disk_cache_performance()
    test_cache_file_format()

    print("="*70)
    print("✅ All persistent cache tests passed!")
    print("="*70 + "\n")


if __name__ == '__main__':
    run_all_tests()
