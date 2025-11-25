#!/usr/bin/env bash
#
# Vibey Commit-Msg Hook
#
# This hook validates commit message format and checks task references.
#
# To bypass this hook temporarily:
#   git commit --no-verify
#
# To disable permanently:
#   vibey git hooks uninstall

# Exit on error
set -e

# Get the repository root
REPO_ROOT=$(git rev-parse --show-toplevel)

# Check if we're in a Vibey project
if [ ! -d "$REPO_ROOT/.vibey" ]; then
    # Not a Vibey project, skip hook
    exit 0
fi

# Check for skip environment variable
if [ -n "$VIBEY_SKIP_HOOKS" ] || [ -n "$VIBEY_OVERRIDE" ]; then
    exit 0
fi

# Find Python (prefer virtual env, then python3, then python)
PYTHON=""
if [ -f "$REPO_ROOT/.venv/bin/python" ]; then
    PYTHON="$REPO_ROOT/.venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
else
    echo "Error: Python not found. Cannot run commit-msg hook."
    exit 1
fi

# Run the Python commit-msg hook
# Pass the commit message file as first argument
exec $PYTHON -m vibey.operations.git.hooks commit-msg "$1"
