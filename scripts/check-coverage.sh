#!/bin/bash
# Local coverage check script for Vibey
# Mirrors CI coverage enforcement locally

set -e

echo "Running coverage check..."
echo ""

# Overall coverage (matches CI threshold)
echo "=========================================="
echo "Overall Coverage Check (threshold: 90%)"
echo "=========================================="
pytest tests/ --cov=vibey --cov-fail-under=90 --cov-report=term-missing -q

echo ""
echo "=========================================="
echo "Module-Specific Coverage"
echo "=========================================="

# Unified module
echo ""
echo "Unified module (vibey/unified/):"
pytest tests/unified/ tests/mcp/test_unified_tools.py --cov=vibey/unified --cov-report=term -q 2>/dev/null | grep -E "^(TOTAL|vibey)" || echo "  No unified tests found"

# CLI module
echo ""
echo "CLI module (vibey/cli/):"
pytest tests/cli/ --cov=vibey/cli --cov-report=term -q 2>/dev/null | grep -E "^(TOTAL|vibey)" || echo "  See test results above"

# MCP module
echo ""
echo "MCP module (vibey/mcp/):"
pytest tests/mcp/ --cov=vibey/mcp --cov-report=term -q 2>/dev/null | grep -E "^(TOTAL|vibey)" || echo "  See test results above"

# Operations module
echo ""
echo "Operations module (vibey/operations/):"
pytest tests/operations/ --cov=vibey/operations --cov-report=term -q 2>/dev/null | grep -E "^(TOTAL|vibey)" || echo "  See test results above"

echo ""
echo "=========================================="
echo "Coverage check complete!"
echo ""
echo "For detailed HTML report, run:"
echo "  pytest tests/ --cov=vibey --cov-report=html"
echo "  open htmlcov/index.html"
echo "=========================================="
