#!/bin/bash
# CI-friendly performance test runner
#
# Runs performance benchmarks and validates targets.
# Exit code 0 if all benchmarks pass, 1 if any fail.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================================"
echo "Running Performance Test Suite"
echo "======================================================================"
echo ""

# Run unit tests first
echo "1. Running cache unit tests..."
python3 test_roadmap_cache.py
echo ""

# Run integration tests
echo "2. Running cache integration tests..."
python3 test_cli_cache_integration.py
echo ""

# Run persistent cache tests
echo "3. Running persistent cache tests..."
python3 test_persistent_cache.py
echo ""

# Run comprehensive benchmark suite
echo "4. Running comprehensive benchmark suite..."
python3 benchmark_suite.py
EXIT_CODE=$?

echo ""
echo "======================================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All performance tests passed!"
else
    echo "❌ Some performance tests failed!"
fi
echo "======================================================================"
echo ""

exit $EXIT_CODE
