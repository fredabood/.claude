#!/usr/bin/env bash
# Pre-commit quality gate: runs tests before allowing git commit.
# Exit 0 = allow, Exit 2 = block commit with error message.
#
# This hook is triggered by settings.json PreToolUse on "Bash(git commit)".
# It detects the project's test runner and runs the test suite.

set -euo pipefail

# Modern hook payload arrives as JSON on stdin ({"tool_name":..,"tool_input":{"command":..}}).
# (The legacy TOOL_INPUT env check made this gate a silent no-op — LAB-215, 2026-07-13.)
INPUT=$(cat)
CMD=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('tool_input') or {}).get('command') or '')" 2>/dev/null || echo "")
if [[ "$CMD" != *"git commit"* ]]; then
  exit 0
fi

# Evaluate the PROJECT ROOT, not the shell CWD (which may sit in a submodule)
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

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
