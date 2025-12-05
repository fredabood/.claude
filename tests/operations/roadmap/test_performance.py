"""
Performance benchmarks for roadmap operations.

Measures and validates performance of:
- Ticket loading at all hierarchy levels
- Aggregation operations (children, commits, standards)
- Status transition validation
- Full hierarchy traversal

Uses real roadmap data from the project as benchmarks.
"""

import pytest
import time
from pathlib import Path
from typing import Callable, Any
from dataclasses import dataclass

# Get the project root directory (where .vibey/ exists)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    name: str
    duration_ms: float
    iterations: int
    avg_ms: float
    threshold_ms: float
    passed: bool


def benchmark(func: Callable[[], Any], iterations: int = 5) -> float:
    """Run a function multiple times and return average duration in ms."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        times.append(elapsed)
    return sum(times) / len(times)


class TestTicketLoadingPerformance:
    """Benchmark ticket loading performance at each hierarchy level."""

    @pytest.fixture
    def root_dir(self):
        """Use the actual project root as test fixture."""
        return PROJECT_ROOT

    def test_load_task_ticket_benchmark(self, root_dir):
        """Benchmark: Load a single task ticket < 50ms."""
        from vibey.operations.roadmap.query import load_task_ticket

        def load_task():
            return load_task_ticket(root_dir, "sqlite-backend-9-task-001")

        avg_ms = benchmark(load_task, iterations=10)

        # Task loading should be very fast
        assert avg_ms < 50, f"Task loading took {avg_ms:.2f}ms, expected < 50ms"

    def test_load_sprint_ticket_benchmark(self, root_dir):
        """Benchmark: Load a sprint with 8 tasks < 200ms."""
        from vibey.operations.roadmap.query import load_sprint_ticket

        def load_sprint():
            sprint = load_sprint_ticket(root_dir, "sqlite-backend-9")
            # Access children to ensure they're loaded
            _ = sprint.children
            return sprint

        avg_ms = benchmark(load_sprint, iterations=5)

        # Sprint loading includes task enumeration
        assert avg_ms < 200, f"Sprint loading took {avg_ms:.2f}ms, expected < 200ms"

    def test_load_track_ticket_benchmark(self, root_dir):
        """Benchmark: Load a track with 10+ sprints < 1000ms."""
        from vibey.operations.roadmap.query import load_track_ticket

        def load_track():
            track = load_track_ticket(root_dir, "sqlite-backend")
            # Access children to ensure they're loaded
            _ = track.children
            return track

        avg_ms = benchmark(load_track, iterations=3)

        # Track loading is more expensive (many sprints)
        assert avg_ms < 1000, f"Track loading took {avg_ms:.2f}ms, expected < 1000ms"

    def test_load_multiple_tasks_benchmark(self, root_dir):
        """Benchmark: Load 8 tasks sequentially < 300ms."""
        from vibey.operations.roadmap.query import load_task_ticket

        def load_all_tasks():
            tasks = []
            for i in range(1, 9):
                task_id = f"sqlite-backend-9-task-{i:03d}"
                tasks.append(load_task_ticket(root_dir, task_id))
            return tasks

        avg_ms = benchmark(load_all_tasks, iterations=3)

        # Loading 8 tasks should be reasonably fast
        assert avg_ms < 300, f"Loading 8 tasks took {avg_ms:.2f}ms, expected < 300ms"


class TestAggregationPerformance:
    """Benchmark aggregation operations."""

    @pytest.fixture
    def root_dir(self):
        """Use the actual project root as test fixture."""
        return PROJECT_ROOT

    def test_sprint_children_aggregation(self, root_dir):
        """Benchmark: Sprint.children aggregation < 100ms."""
        from vibey.operations.roadmap.query import load_sprint_ticket

        sprint = load_sprint_ticket(root_dir, "sqlite-backend-9")

        def access_children():
            return list(sprint.children)

        avg_ms = benchmark(access_children, iterations=10)

        assert avg_ms < 100, f"Children access took {avg_ms:.2f}ms, expected < 100ms"

    def test_track_children_aggregation(self, root_dir):
        """Benchmark: Track.children aggregation < 500ms."""
        from vibey.operations.roadmap.query import load_track_ticket

        track = load_track_ticket(root_dir, "sqlite-backend")

        def access_children():
            return list(track.children)

        avg_ms = benchmark(access_children, iterations=5)

        assert avg_ms < 500, f"Children access took {avg_ms:.2f}ms, expected < 500ms"


class TestStatusTransitionPerformance:
    """Benchmark status transition validation."""

    @pytest.fixture
    def root_dir(self):
        """Use the actual project root as test fixture."""
        return PROJECT_ROOT

    def test_can_transition_to_benchmark(self, root_dir):
        """Benchmark: can_transition_to check < 20ms."""
        from vibey.operations.roadmap.query import load_task_ticket
        from vibey.roadmap.models.ticket import TicketStatus

        task = load_task_ticket(root_dir, "sqlite-backend-9-task-001")

        def check_transition():
            return task.can_transition_to(TicketStatus.COMPLETED)

        avg_ms = benchmark(check_transition, iterations=20)

        # Transition checks should be very fast
        assert avg_ms < 20, f"Transition check took {avg_ms:.2f}ms, expected < 20ms"

    def test_sprint_completion_check_benchmark(self, root_dir):
        """Benchmark: Sprint completion validation < 100ms."""
        from vibey.operations.roadmap.query import load_sprint_ticket
        from vibey.roadmap.models.ticket import TicketStatus

        sprint = load_sprint_ticket(root_dir, "sqlite-backend-9")

        def check_completion():
            return sprint.can_transition_to(TicketStatus.COMPLETED)

        avg_ms = benchmark(check_completion, iterations=10)

        # Sprint completion checks all task statuses
        assert avg_ms < 100, f"Completion check took {avg_ms:.2f}ms, expected < 100ms"


class TestHierarchyTraversalPerformance:
    """Benchmark hierarchy traversal operations."""

    @pytest.fixture
    def root_dir(self):
        """Use the actual project root as test fixture."""
        return PROJECT_ROOT

    def test_full_hierarchy_traversal(self, root_dir):
        """Benchmark: Full track hierarchy traversal < 2000ms."""
        from vibey.operations.roadmap.query import load_track_ticket, load_sprint_ticket

        def traverse_hierarchy():
            track = load_track_ticket(root_dir, "sqlite-backend")
            sprint_ids = track.children

            total_tasks = 0
            for sprint_id in sprint_ids[:5]:  # First 5 sprints for benchmark
                try:
                    sprint = load_sprint_ticket(root_dir, sprint_id)
                    total_tasks += len(sprint.children)
                except Exception:
                    pass  # Skip sprints that fail to load

            return total_tasks

        avg_ms = benchmark(traverse_hierarchy, iterations=3)

        # Full traversal of 5 sprints
        assert avg_ms < 2000, f"Hierarchy traversal took {avg_ms:.2f}ms, expected < 2000ms"


class TestStandardsEnforcementPerformance:
    """Benchmark standards enforcement operations."""

    @pytest.fixture
    def root_dir(self):
        """Use the actual project root as test fixture."""
        return PROJECT_ROOT

    def test_get_effective_standards_benchmark(self, root_dir):
        """Benchmark: Get effective standards < 100ms."""
        from vibey.operations.roadmap.standards_enforcement import get_effective_standards

        def get_standards():
            return get_effective_standards("sqlite-backend-9-task-001", root_dir)

        avg_ms = benchmark(get_standards, iterations=10)

        # Standards involves hierarchy traversal and file reads
        assert avg_ms < 100, f"Standards lookup took {avg_ms:.2f}ms, expected < 100ms"

    def test_enforce_standards_benchmark(self, root_dir):
        """Benchmark: Enforce standards < 100ms."""
        from vibey.operations.roadmap.standards_enforcement import enforce_standards

        def enforce():
            return enforce_standards("sqlite-backend-9-task-001", root_dir)

        avg_ms = benchmark(enforce, iterations=10)

        assert avg_ms < 100, f"Standards enforcement took {avg_ms:.2f}ms, expected < 100ms"


class TestPerformanceReport:
    """Generate a performance report for all benchmarks."""

    @pytest.fixture
    def root_dir(self):
        """Use the actual project root as test fixture."""
        return PROJECT_ROOT

    def test_generate_performance_summary(self, root_dir):
        """Generate and print a performance summary."""
        from vibey.operations.roadmap.query import (
            load_task_ticket,
            load_sprint_ticket,
            load_track_ticket,
        )
        from vibey.operations.roadmap.standards_enforcement import (
            get_effective_standards,
            enforce_standards,
        )
        from vibey.roadmap.models.ticket import TicketStatus

        results = []

        # Task loading
        avg = benchmark(lambda: load_task_ticket(root_dir, "sqlite-backend-9-task-001"))
        results.append(BenchmarkResult("Load Task", avg, 5, avg, 50, avg < 50))

        # Sprint loading
        def load_sprint():
            s = load_sprint_ticket(root_dir, "sqlite-backend-9")
            _ = s.children
            return s
        avg = benchmark(load_sprint)
        results.append(BenchmarkResult("Load Sprint", avg, 5, avg, 200, avg < 200))

        # Track loading
        def load_track():
            t = load_track_ticket(root_dir, "sqlite-backend")
            _ = t.children
            return t
        avg = benchmark(load_track, iterations=3)
        results.append(BenchmarkResult("Load Track", avg, 3, avg, 1000, avg < 1000))

        # Status transition
        task = load_task_ticket(root_dir, "sqlite-backend-9-task-001")
        avg = benchmark(lambda: task.can_transition_to(TicketStatus.COMPLETED))
        results.append(BenchmarkResult("Transition Check", avg, 5, avg, 20, avg < 20))

        # Standards
        avg = benchmark(lambda: get_effective_standards("sqlite-backend-9-task-001", root_dir))
        results.append(BenchmarkResult("Get Standards", avg, 5, avg, 100, avg < 100))

        avg = benchmark(lambda: enforce_standards("sqlite-backend-9-task-001", root_dir))
        results.append(BenchmarkResult("Enforce Standards", avg, 5, avg, 100, avg < 100))

        # Print summary
        print("\n" + "=" * 60)
        print("PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 60)
        print(f"{'Operation':<25} {'Avg (ms)':<12} {'Threshold':<12} {'Status'}")
        print("-" * 60)

        all_passed = True
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            all_passed = all_passed and r.passed
            print(f"{r.name:<25} {r.avg_ms:>8.2f} ms  {r.threshold_ms:>8.0f} ms  {status}")

        print("=" * 60)
        print(f"Overall: {'ALL BENCHMARKS PASSED' if all_passed else 'SOME BENCHMARKS FAILED'}")
        print("=" * 60 + "\n")

        assert all_passed, "Some benchmarks failed to meet thresholds"
