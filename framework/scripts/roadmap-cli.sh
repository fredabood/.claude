#!/usr/bin/env bash
#
# Vibey Roadmap CLI Wrapper
#
# Provides easy access to roadmap commands from any directory.
# Automatically handles PYTHONPATH setup and script location.
#
# Usage:
#   roadmap-cli.sh <command> [args...]
#
# Available commands:
#   query       - Query roadmap state (roadmap-query.py)
#   update      - Update roadmap state (roadmap-update.py)
#   init        - Initialize new roadmap (roadmap-init.py)
#   prepare     - Prepare roadmap from plan (roadmap-prepare.py)
#   context     - Load task context (roadmap-context.py)
#   summarize   - Generate summaries (roadmap-summarize.py)
#   sync-docs   - Sync documentation (roadmap-sync-docs.py)
#
# Examples:
#   roadmap-cli.sh query
#   roadmap-cli.sh query --track infrastructure-fixes
#   roadmap-cli.sh update --start-task infrastructure-fixes-1-task-001
#   roadmap-cli.sh context infrastructure-fixes-1-task-001
#
# Installation:
#   # Option 1: Add to PATH
#   sudo ln -s $(pwd)/framework/scripts/roadmap-cli.sh /usr/local/bin/vibey-roadmap
#
#   # Option 2: Create shell alias
#   echo "alias vibey-roadmap='$(pwd)/framework/scripts/roadmap-cli.sh'" >> ~/.bashrc
#

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Determine repository root (go up from framework/scripts/)
REPO_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Add framework root to PYTHONPATH for imports
export PYTHONPATH="${REPO_ROOT}:${PYTHONPATH}"

# Command mapping
declare -A COMMANDS=(
    ["query"]="roadmap-query.py"
    ["update"]="roadmap-update.py"
    ["init"]="roadmap-init.py"
    ["prepare"]="roadmap-prepare.py"
    ["context"]="roadmap-context.py"
    ["summarize"]="roadmap-summarize.py"
    ["sync-docs"]="roadmap-sync-docs.py"
)

# Show help if no arguments
if [ $# -eq 0 ]; then
    echo "Vibey Roadmap CLI"
    echo ""
    echo "Usage: $0 <command> [args...]"
    echo ""
    echo "Available commands:"
    echo "  query       - Query roadmap state (default if no command given)"
    echo "  update      - Update roadmap state"
    echo "  init        - Initialize new roadmap"
    echo "  prepare     - Prepare roadmap from sprint plan"
    echo "  context     - Load task context with dependencies"
    echo "  summarize   - Generate task/sprint summaries"
    echo "  sync-docs   - Synchronize documentation"
    echo ""
    echo "Examples:"
    echo "  $0 query"
    echo "  $0 query --track infrastructure-fixes"
    echo "  $0 update --start-task infrastructure-fixes-1-task-001"
    echo "  $0 update --complete-task infrastructure-fixes-1-task-001"
    echo "  $0 context infrastructure-fixes-1-task-001"
    echo ""
    echo "For command-specific help:"
    echo "  $0 <command> --help"
    exit 0
fi

# Get command
COMMAND="$1"
shift  # Remove command from arguments

# Check if command exists in mapping
if [ -z "${COMMANDS[$COMMAND]}" ]; then
    echo "❌ Error: Unknown command '$COMMAND'"
    echo ""
    echo "Available commands: ${!COMMANDS[@]}"
    echo ""
    echo "Run '$0' with no arguments for usage help."
    exit 1
fi

# Get script filename
SCRIPT_FILE="${COMMANDS[$COMMAND]}"
SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_FILE"

# Verify script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Error: Script not found: $SCRIPT_PATH"
    exit 1
fi

# Execute the Python script with remaining arguments
exec python3 "$SCRIPT_PATH" "$@"
