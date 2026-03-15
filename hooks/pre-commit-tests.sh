#!/usr/bin/env bash
# Pre-commit quality gate: runs tests before allowing git commit.
# Exit 0 = allow, Exit 2 = block commit with error message.
#
# This hook is triggered by settings.json PreToolUse on "Bash(git commit)".
# It detects the project's test runner and runs the test suite.

set -euo pipefail

# Only run on actual commit commands (not commit --amend messages, etc.)
if [[ "${TOOL_INPUT:-}" != *"git commit"* ]]; then
  exit 0
fi

# Detect test runner and run tests
if [[ -f "pytest.ini" || -f "pyproject.toml" ]] && command -v pytest &>/dev/null; then
  echo "Running pytest..."
  if ! pytest -x -q 2>&1; then
    echo "ERROR: Tests failed. Fix failing tests before committing."
    exit 2
  fi
elif [[ -f "package.json" ]] && grep -q '"test"' package.json 2>/dev/null; then
  echo "Running npm test..."
  if ! npm test 2>&1; then
    echo "ERROR: Tests failed. Fix failing tests before committing."
    exit 2
  fi
elif [[ -f "Makefile" ]] && grep -q '^test:' Makefile 2>/dev/null; then
  echo "Running make test..."
  if ! make test 2>&1; then
    echo "ERROR: Tests failed. Fix failing tests before committing."
    exit 2
  fi
else
  # No test runner detected — allow commit
  exit 0
fi

echo "All tests passed."
exit 0
