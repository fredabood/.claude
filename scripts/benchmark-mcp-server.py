#!/usr/bin/env python3
"""
MCP Server Performance Benchmarks.

Measures performance of the Vibey MCP server for:
- Tool discovery time
- Tool invocation latency
- Throughput under load
- Memory usage

Usage:
    python scripts/benchmark-mcp-server.py
    python scripts/benchmark-mcp-server.py --iterations 100
    python scripts/benchmark-mcp-server.py --output results.json
"""

import argparse
import asyncio
import json
import statistics
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from framework.mcp.server import VibeyMCPServer
from framework.mcp.discovery import ToolDiscovery


@dataclass
class BenchmarkResult:
    """Result of a single benchmark."""
    name: str
    iterations: int
    min_ms: float
    max_ms: float
    mean_ms: float
    median_ms: float
    stddev_ms: float
    p95_ms: float
    p99_ms: float
    total_seconds: float
    ops_per_second: float


@dataclass
class BenchmarkSuite:
    """Complete benchmark results."""
    timestamp: str
    python_version: str
    results: List[BenchmarkResult]
    summary: Dict[str, Any]


def percentile(data: List[float], p: float) -> float:
    """Calculate the p-th percentile of data."""
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * p / 100
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_data) else f
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def run_benchmark(
    name: str,
    func,
    iterations: int = 100,
    warmup: int = 5
) -> BenchmarkResult:
    """Run a benchmark and collect metrics."""
    print(f"  Running {name}...", end=" ", flush=True)

    # Warmup runs
    for _ in range(warmup):
        func()

    # Timed runs
    times_ms = []
    start_total = time.perf_counter()

    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        times_ms.append(elapsed)

    total_seconds = time.perf_counter() - start_total

    result = BenchmarkResult(
        name=name,
        iterations=iterations,
        min_ms=min(times_ms),
        max_ms=max(times_ms),
        mean_ms=statistics.mean(times_ms),
        median_ms=statistics.median(times_ms),
        stddev_ms=statistics.stdev(times_ms) if len(times_ms) > 1 else 0,
        p95_ms=percentile(times_ms, 95),
        p99_ms=percentile(times_ms, 99),
        total_seconds=total_seconds,
        ops_per_second=iterations / total_seconds
    )

    print(f"done ({result.mean_ms:.2f}ms avg, {result.ops_per_second:.1f} ops/s)")
    return result


async def run_async_benchmark(
    name: str,
    func,
    iterations: int = 100,
    warmup: int = 5
) -> BenchmarkResult:
    """Run an async benchmark and collect metrics."""
    print(f"  Running {name}...", end=" ", flush=True)

    # Warmup runs
    for _ in range(warmup):
        await func()

    # Timed runs
    times_ms = []
    start_total = time.perf_counter()

    for _ in range(iterations):
        start = time.perf_counter()
        await func()
        elapsed = (time.perf_counter() - start) * 1000
        times_ms.append(elapsed)

    total_seconds = time.perf_counter() - start_total

    result = BenchmarkResult(
        name=name,
        iterations=iterations,
        min_ms=min(times_ms),
        max_ms=max(times_ms),
        mean_ms=statistics.mean(times_ms),
        median_ms=statistics.median(times_ms),
        stddev_ms=statistics.stdev(times_ms) if len(times_ms) > 1 else 0,
        p95_ms=percentile(times_ms, 95),
        p99_ms=percentile(times_ms, 99),
        total_seconds=total_seconds,
        ops_per_second=iterations / total_seconds
    )

    print(f"done ({result.mean_ms:.2f}ms avg, {result.ops_per_second:.1f} ops/s)")
    return result


class MCPServerBenchmarks:
    """Benchmark suite for MCP server."""

    def __init__(self, iterations: int = 100):
        self.iterations = iterations
        self.server = VibeyMCPServer(
            roadmap_root=".vibey/roadmap",
            framework_root=str(PROJECT_ROOT)
        )
        self.discovery = ToolDiscovery(
            root_dir=PROJECT_ROOT,
            tool_prefix='vibey'
        )

    def benchmark_tool_discovery(self) -> BenchmarkResult:
        """Benchmark tool discovery (with cache clear)."""
        def func():
            self.discovery.get_all_tools(force_refresh=True)
        return run_benchmark("Tool Discovery (cold)", func, self.iterations)

    def benchmark_tool_discovery_cached(self) -> BenchmarkResult:
        """Benchmark tool discovery (cached)."""
        # Prime the cache
        self.discovery.get_all_tools()

        def func():
            self.discovery.get_all_tools()
        return run_benchmark("Tool Discovery (cached)", func, self.iterations)

    def benchmark_get_tools(self) -> BenchmarkResult:
        """Benchmark server.get_tools()."""
        def func():
            self.server.get_tools()
        return run_benchmark("Server get_tools()", func, self.iterations)

    def benchmark_get_capabilities(self) -> BenchmarkResult:
        """Benchmark server.get_capabilities()."""
        def func():
            self.server.get_capabilities()
        return run_benchmark("Server get_capabilities()", func, self.iterations)

    async def benchmark_roadmap_status(self) -> BenchmarkResult:
        """Benchmark vibey_roadmap_status tool."""
        async def func():
            await self.server.handle_tool_call('vibey_roadmap_status', {})
        return await run_async_benchmark(
            "vibey_roadmap_status",
            func,
            self.iterations
        )

    async def benchmark_query_track(self) -> BenchmarkResult:
        """Benchmark vibey_query_track tool."""
        async def func():
            await self.server.handle_tool_call('vibey_query_track', {
                'track_id': 'goose-port'
            })
        return await run_async_benchmark(
            "vibey_query_track",
            func,
            self.iterations
        )

    async def benchmark_unknown_tool(self) -> BenchmarkResult:
        """Benchmark error handling for unknown tool."""
        async def func():
            await self.server.handle_tool_call('unknown_tool_xyz', {})
        return await run_async_benchmark(
            "Unknown tool (error path)",
            func,
            self.iterations
        )

    async def benchmark_agent_tool(self) -> BenchmarkResult:
        """Benchmark an agent tool invocation."""
        # Find first agent tool
        tools = self.server.get_tools()
        agent_tool = None
        for tool in tools:
            if tool.get('_metadata', {}).get('asset_type') == 'agent':
                agent_tool = tool['name']
                break

        if not agent_tool:
            print("  Skipping agent tool benchmark (no agents found)")
            return None

        async def func():
            await self.server.handle_tool_call(agent_tool, {
                'task': 'test task',
                'context': 'test context'
            })
        return await run_async_benchmark(
            f"Agent tool ({agent_tool})",
            func,
            self.iterations
        )

    def benchmark_frontmatter_parsing(self) -> BenchmarkResult:
        """Benchmark frontmatter parsing."""
        from framework.mcp.discovery.parser import FrontmatterParser

        parser = FrontmatterParser()
        content = """---
id: test-agent
name: Test Agent
type: quality
version: 1.0.0
description: A test agent for benchmarking
triggers:
  keywords:
    - test
    - benchmark
inputs:
  - name: code
    type: string
    required: true
---

# Test Agent

Instructions here.
"""

        def func():
            parser.parse_content(content)
        return run_benchmark("Frontmatter parsing", func, self.iterations)

    async def run_all(self) -> BenchmarkSuite:
        """Run all benchmarks."""
        import datetime
        import platform

        print("\n" + "=" * 60)
        print("Vibey MCP Server Benchmarks")
        print("=" * 60)
        print(f"Iterations per benchmark: {self.iterations}")
        print()

        results = []

        # Synchronous benchmarks
        print("Discovery Benchmarks:")
        results.append(self.benchmark_frontmatter_parsing())
        results.append(self.benchmark_tool_discovery())
        results.append(self.benchmark_tool_discovery_cached())
        print()

        print("Server Benchmarks:")
        results.append(self.benchmark_get_tools())
        results.append(self.benchmark_get_capabilities())
        print()

        print("Tool Invocation Benchmarks:")
        results.append(await self.benchmark_roadmap_status())
        results.append(await self.benchmark_query_track())
        results.append(await self.benchmark_unknown_tool())
        agent_result = await self.benchmark_agent_tool()
        if agent_result:
            results.append(agent_result)
        print()

        # Filter out None results
        results = [r for r in results if r is not None]

        # Create summary
        summary = {
            'total_benchmarks': len(results),
            'fastest_operation': min(results, key=lambda r: r.mean_ms).name,
            'fastest_ms': min(r.mean_ms for r in results),
            'slowest_operation': max(results, key=lambda r: r.mean_ms).name,
            'slowest_ms': max(r.mean_ms for r in results),
            'total_tool_count': len(self.server.get_tools()),
        }

        suite = BenchmarkSuite(
            timestamp=datetime.datetime.now().isoformat(),
            python_version=platform.python_version(),
            results=results,
            summary=summary
        )

        return suite


def print_results(suite: BenchmarkSuite):
    """Print benchmark results in a table."""
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)

    # Header
    print(f"{'Benchmark':<35} {'Mean':>10} {'Median':>10} {'P95':>10} {'P99':>10} {'Ops/s':>10}")
    print("-" * 80)

    # Results
    for result in suite.results:
        print(f"{result.name:<35} {result.mean_ms:>9.2f}ms {result.median_ms:>9.2f}ms "
              f"{result.p95_ms:>9.2f}ms {result.p99_ms:>9.2f}ms {result.ops_per_second:>9.1f}")

    print("-" * 80)
    print(f"\nSummary:")
    print(f"  Total benchmarks: {suite.summary['total_benchmarks']}")
    print(f"  Fastest: {suite.summary['fastest_operation']} ({suite.summary['fastest_ms']:.2f}ms)")
    print(f"  Slowest: {suite.summary['slowest_operation']} ({suite.summary['slowest_ms']:.2f}ms)")
    print(f"  Total tools: {suite.summary['total_tool_count']}")


def save_results(suite: BenchmarkSuite, output_path: Path):
    """Save benchmark results to JSON."""
    data = {
        'timestamp': suite.timestamp,
        'python_version': suite.python_version,
        'summary': suite.summary,
        'results': [asdict(r) for r in suite.results]
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\nResults saved to: {output_path}")


async def main():
    parser = argparse.ArgumentParser(description="Benchmark MCP server performance")
    parser.add_argument(
        '--iterations', '-n',
        type=int,
        default=100,
        help='Number of iterations per benchmark (default: 100)'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output JSON file for results'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick benchmarks (10 iterations)'
    )

    args = parser.parse_args()

    iterations = 10 if args.quick else args.iterations

    benchmarks = MCPServerBenchmarks(iterations=iterations)
    suite = await benchmarks.run_all()

    print_results(suite)

    if args.output:
        save_results(suite, args.output)


if __name__ == '__main__':
    asyncio.run(main())
