"""
Benchmark RoadmapCache performance.

Demonstrates the performance improvement from caching.
"""

import sys
from pathlib import Path
import time

# Add roadmap-lib to path
test_dir = Path(__file__).parent
scripts_dir = test_dir.parent
roadmap_lib_dir = scripts_dir / "roadmap-lib"
sys.path.insert(0, str(roadmap_lib_dir))

from cache import RoadmapCache
from filesystem import find_roadmap_root, load_yaml, FileSystemManager


def benchmark_without_cache(root_dir: Path, iterations: int = 10):
    """Benchmark operations without cache."""
    fs = FileSystemManager(root_dir)
    times = []

    for _ in range(iterations):
        start = time.time()

        # Simulate finding a task (linear scan)
        task_id = 'core-framework-3-task-001'
        task_found = None

        tasks_dir = fs.vibey_dir / fs.TASKS_DIR
        if tasks_dir.exists():
            for task_file in tasks_dir.glob("*-tasks.yaml"):
                data = load_yaml(task_file)
                if data and 'tasks' in data:
                    for task in data['tasks']:
                        if task.get('id') == task_id:
                            task_found = task
                            break
                if task_found:
                    break

        elapsed = (time.time() - start) * 1000  # Convert to ms
        times.append(elapsed)

    avg_time = sum(times) / len(times)
    return avg_time, task_found is not None


def benchmark_with_cache(root_dir: Path, iterations: int = 10):
    """Benchmark operations with cache."""
    cache = RoadmapCache(root_dir)
    times = []

    for i in range(iterations):
        start = time.time()

        # First iteration builds index, rest use cache
        task = cache.get_task('core-framework-3-task-001')

        elapsed = (time.time() - start) * 1000  # Convert to ms
        times.append(elapsed)

    avg_time = sum(times) / len(times)
    stats = cache.get_stats()

    return avg_time, task is not None, stats


def main():
    # Find Vibey roadmap
    root_dir = find_roadmap_root()
    if not root_dir:
        print("❌ No roadmap found. Run from Vibey repository root.")
        sys.exit(1)

    print("\n" + "="*70)
    print("RoadmapCache Performance Benchmark")
    print("="*70)
    print(f"Root: {root_dir}")

    # Count objects
    fs = FileSystemManager(root_dir)
    num_tasks = 0
    tasks_dir = fs.vibey_dir / fs.TASKS_DIR
    if tasks_dir.exists():
        for task_file in tasks_dir.glob("*-tasks.yaml"):
            data = load_yaml(task_file)
            if data and 'tasks' in data:
                num_tasks += len(data['tasks'])

    num_sprints = len(list((fs.vibey_dir / fs.SPRINTS_DIR).glob("*.yaml")))
    num_tracks = len(list((fs.vibey_dir / fs.TRACKS_DIR).glob("*.yaml")))

    print(f"\nRoadmap size:")
    print(f"  Tasks:   {num_tasks}")
    print(f"  Sprints: {num_sprints}")
    print(f"  Tracks:  {num_tracks}")

    # Benchmark without cache
    print("\n📊 Benchmarking WITHOUT cache...")
    iterations = 20
    time_without, found_without = benchmark_without_cache(root_dir, iterations)

    # Benchmark with cache
    print("📊 Benchmarking WITH cache...")
    time_with, found_with, stats = benchmark_with_cache(root_dir, iterations)

    # Results
    print("\n" + "-"*70)
    print("RESULTS")
    print("-"*70)

    print(f"\nWithout cache:")
    print(f"  Average time: {time_without:.2f}ms")
    print(f"  Task found:   {found_without}")

    print(f"\nWith cache:")
    print(f"  Average time: {time_with:.2f}ms")
    print(f"  Task found:   {found_with}")
    print(f"  Hit rate:     {stats['hit_rate']}%")
    print(f"  Cache hits:   {stats['hits']}")
    print(f"  Cache misses: {stats['misses']}")

    # Calculate improvement
    if time_with > 0:
        speedup = time_without / time_with
        improvement = ((time_without - time_with) / time_without) * 100

        print(f"\nPerformance Improvement:")
        print(f"  Speedup:      {speedup:.1f}x faster")
        print(f"  Time saved:   {improvement:.1f}% faster")

        # Check if targets met
        print(f"\nTargets:")
        target = 5.0  # 5ms target
        if time_with < target:
            print(f"  ✅ Task lookup < {target}ms (actual: {time_with:.2f}ms)")
        else:
            print(f"  ❌ Task lookup target: < {target}ms (actual: {time_with:.2f}ms)")

    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    main()
