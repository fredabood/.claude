#!/usr/bin/env bash
#
# Vibey CLI - Unified command-line interface for Vibey Agent Framework
#
# Usage:
#   vibey deploy --platform claude-code
#   vibey docs generate
#   vibey roadmap summarize sprint core-framework-2
#   vibey --help

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FRAMEWORK_DIR="$SCRIPT_DIR/framework"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
print_banner() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  ${GREEN}Vibey Agent Framework${NC} - Platform-Agnostic CLI      ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}  Version 1.2.0                                        ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Show help
show_help() {
    print_banner

    cat << EOF
${GREEN}Available Commands:${NC}

  ${YELLOW}deploy${NC}     Deploy framework to target platform
             vibey deploy --platform claude-code
             vibey deploy --list-platforms

  ${YELLOW}docs${NC}       Generate documentation from configuration
             vibey docs generate
             vibey docs generate --overwrite

  ${YELLOW}roadmap${NC}    Interact with roadmap system
             vibey roadmap summarize sprint <sprint-id>
             vibey roadmap summarize task <task-id>
             vibey roadmap context <task-id>

  ${YELLOW}help${NC}       Show this help message
             vibey help
             vibey --help

${GREEN}Examples:${NC}

  # Deploy to Claude Code
  vibey deploy --platform claude-code

  # Generate documentation
  vibey docs generate

  # Summarize a sprint
  vibey roadmap summarize sprint core-framework-2

  # Get task context
  vibey roadmap context core-framework-2-task-003

${GREEN}For Command-Specific Help:${NC}

  vibey deploy --help
  vibey docs --help
  vibey roadmap --help

EOF
}

# Check Python 3 is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Error: python3 not found${NC}"
        echo "Please install Python 3.7 or higher"
        exit 1
    fi
}

# Main command router
main() {
    # No arguments - show help
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi

    # Check for help flag
    if [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_help
        exit 0
    fi

    # Check Python
    check_python

    # Route to appropriate command
    case "$1" in
        deploy)
            shift
            python3 "$FRAMEWORK_DIR/scripts/deploy.py" "$@"
            ;;
        docs)
            shift
            python3 "$FRAMEWORK_DIR/scripts/docs.py" "$@"
            ;;
        roadmap)
            shift
            python3 "$FRAMEWORK_DIR/scripts/roadmap.py" "$@"
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $1${NC}"
            echo ""
            echo "Run 'vibey help' to see available commands"
            exit 1
            ;;
    esac
}

# Run main with all arguments
main "$@"
