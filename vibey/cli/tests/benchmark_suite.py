"""
Comprehensive benchmark suite for RoadmapCache.

Tests performance across different roadmap sizes and validates targets.
"""

import sys
from pathlib import Path
import tempfile
import time
from typing import Dict, List

# Add roadmap-lib to path
test_dir = Path(__file__).parent
scripts_dir = test_dir.parent
roadmap_lib_dir = scripts_dir / "roadmap-lib"
sys.path.insert(0, str(roadmap_lib_dir))

from cache import RoadmapCache
from filesystem import FileSystemManager, load_yaml
from generate_synthetic_roadmap import generate_roadmap


class BenchmarkResults:
    """Store and analyze benchmark results."""

    def __init__(self):
        self.results = []

    def add_result(self, name: str, size: str, operation: str, time_ms: float, target_ms: float):
        """Add a benchmark result."""
        passed = time_ms < target_ms
        self.results.append({
            'name': name,
            'size': size,
            'operation': operation,
            'time_ms': time_ms,
            'target_ms': target_ms,
            'passed': passed,
        })

    def print_summary(self):
        """Print summary of results."""
        print("\n" + "="*70)
        print("BENCHMARK SUMMARY")
        print("="*70 + "\n")

        # Group by size
        sizes = {}
        for result in self.results:
            size = result['size']
            if size not in sizes:
                sizes[size] = []
            sizes[size].append(result)

        # Print results by size
        for size, size_results in sizes.items():
            print(f"{size.upper()} ROADMAP:")
            for result in size_results:
                status = "✅" if result['passed'] else "❌"
                print(f"  {status} {result['operation']}: {result['time_ms']:.2f}ms (target: <{result['target_ms']}ms)")
            print()

        # Overall pass/fail
        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"Overall: {passed}/{total} benchmarks passed ({pass_rate:.1f}%)")
        print("="*70 + "\n")


def benchmark_task_lookup(cache: RoadmapCache, task_id: str, iterations: int = 50) -> float:
    """
    Benchmark task lookup operation.

    Args:
        cache: RoadmapCache instance
        task_id: Task ID to look up
        iterations: Number of iterations

    Returns:
        Average time in milliseconds
    """
    times = []

    for _ in range(iterations):
        # Clear object cache but keep indexes (simulates typical usage)
        cache._task_cache.clear()

        start = time.time()
        task = cache.get_task(task_id)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)

    return sum(times) / len(times)


def benchmark_load_all_tasks(cache: RoadmapCache, iterations: int = 10) -> float:
    """
    Benchmark loading all tasks.

    Note: This includes YAML parsing time since tasks are loaded on demand.
    The cache speeds up finding where tasks are, but YAML parsing is still needed.

    Args:
        cache: RoadmapCache instance
        iterations: Number of iterations

    Returns:
        Average time in milliseconds
    """
    times = []

    for _ in range(iterations):
        # Clear object cache to simulate fresh load
        cache._task_cache.clear()

        start = time.time()
        tasks = cache.get_all_tasks()
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)

    return sum(times) / len(times)


def benchmark_dependency_graph(cache: RoadmapCache, iterations: int = 10) -> float:
    """
    Benchmark dependency graph query.

    Args:
        cache: RoadmapCache instance
        iterations: Number of iterations

    Returns:
        Average time in milliseconds
    """
    # Ensure graph is built
    cache.get_dependency_graph()

    times = []

    for _ in range(iterations):
        start = time.time()
        graph = cache.get_dependency_graph()
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)

    return sum(times) / len(times)


def benchmark_cache_initialization(root_dir: Path, iterations: int = 10) -> float:
    """
    Benchmark cache initialization with disk cache.

    This measures loading pre-built cache from disk vs rebuilding from filesystem.

    Args:
        root_dir: Root directory
        iterations: Number of iterations

    Returns:
        Average time in milliseconds
    """
    # Build cache once to create disk cache files
    print("     Building initial cache...")
    cache = RoadmapCache(root_dir, enable_disk_cache=True)
    cache.get_task('task-00001')  # Trigger index build
    cache.get_dependency_graph()  # Trigger graph build

    # Verify cache files were created
    cache_dir = root_dir / '.vibey' / '.cache'
    assert (cache_dir / 'indexes.json').exists(), "Cache files not created"
    print(f"     Cache files created at {cache_dir}")
    del cache

    times = []

    for _ in range(iterations):
        start = time.time()
        cache = RoadmapCache(root_dir, enable_disk_cache=True)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)

        # Verify it loaded from disk
        if cache._disk_loads == 0:
            print(f"     ⚠️  Warning: Cache did not load from disk (disk_loads={cache._disk_loads})")

        del cache

    return sum(times) / len(times)


def run_benchmark_suite(roadmap_size: int, size_name: str, results: BenchmarkResults):
    """
    Run full benchmark suite for a specific roadmap size.

    Args:
        roadmap_size: Number of tasks
        size_name: Name of size (small, medium, large)
        results: BenchmarkResults to store results
    """
    print(f"\n{'='*70}")
    print(f"Benchmarking {size_name.upper()} Roadmap ({roadmap_size} tasks)")
    print(f"{'='*70}\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)

        # Generate synthetic roadmap
        print("Generating synthetic roadmap...")
        num_tracks, num_sprints, num_tasks = generate_roadmap(root_dir, roadmap_size)
        print(f"  Tracks:  {num_tracks}")
        print(f"  Sprints: {num_sprints}")
        print(f"  Tasks:   {num_tasks}")
        print()

        # Create cache
        cache = RoadmapCache(root_dir, enable_disk_cache=True)

        # 1. Cache Initialization (with disk cache)
        print("📊 Benchmarking cache initialization...")
        init_time = benchmark_cache_initialization(root_dir)
        print(f"   Result: {init_time:.2f}ms")
        results.add_result(
            f"{size_name}-init",
            size_name,
            "Cache initialization (from disk)",
            init_time,
            target_ms=10.0
        )

        # 2. Task Lookup
        print("📊 Benchmarking task lookup...")
        lookup_time = benchmark_task_lookup(cache, 'task-00001')
        print(f"   Result: {lookup_time:.2f}ms")
        results.add_result(
            f"{size_name}-lookup",
            size_name,
            "Task lookup",
            lookup_time,
            target_ms=5.0
        )

        # 3. Load All Tasks (includes YAML parsing)
        print("📊 Benchmarking load all tasks (with YAML parsing)...")
        load_all_time = benchmark_load_all_tasks(cache)
        print(f"   Result: {load_all_time:.2f}ms")

        # Scale target based on roadmap size
        # Note: This includes YAML parsing time, not just cache lookups
        if roadmap_size <= 100:
            load_all_target = 100.0   # ~2ms per task for YAML parsing
        elif roadmap_size <= 300:
            load_all_target = 300.0   # ~1.5ms per task
        else:
            load_all_target = 800.0   # ~1.6ms per task

        results.add_result(
            f"{size_name}-load-all",
            size_name,
            "Load all tasks (with YAML parsing)",
            load_all_time,
            target_ms=load_all_target
        )

        # 4. Dependency Graph Query
        print("📊 Benchmarking dependency graph...")
        dep_graph_time = benchmark_dependency_graph(cache)
        print(f"   Result: {dep_graph_time:.2f}ms")
        results.add_result(
            f"{size_name}-dep-graph",
            size_name,
            "Dependency graph query",
            dep_graph_time,
            target_ms=20.0
        )

        # Cache statistics
        stats = cache.get_stats()
        print(f"\nCache Statistics:")
        print(f"  Hits:        {stats['hits']}")
        print(f"  Misses:      {stats['misses']}")
        print(f"  Hit rate:    {stats['hit_rate']}%")
        print(f"  Disk loads:  {stats['disk_loads']}")


def main():
    """Run comprehensive benchmark suite."""
    print("\n" + "="*70)
    print("RoadmapCache Comprehensive Benchmark Suite")
    print("="*70)

    results = BenchmarkResults()

    # Standard benchmark sizes
    benchmark_configs = [
        (53, "small"),     # Current Vibey roadmap size
        (200, "medium"),   # Medium project
        (500, "large"),    # Large project
    ]

    for roadmap_size, size_name in benchmark_configs:
        run_benchmark_suite(roadmap_size, size_name, results)

    # Print summary
    results.print_summary()

    # Determine exit code
    all_passed = all(r['passed'] for r in results.results)
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
