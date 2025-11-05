#!/usr/bin/env bash
#
# Vibey Framework Setup Script
#
# This script installs the Vibey agent framework into a new project
# and generates initial documentation from a project config.
#
# Usage:
#   ./scripts/setup.sh
#   ./scripts/setup.sh --config my-config.yaml
#   ./scripts/setup.sh --template web-app
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VIBEY_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
CONFIG_FILE=""
TEMPLATE_TYPE=""
TARGET_DIR="."
SKIP_DOCS=false

# Helper functions
print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --config|-c)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --template|-t)
            TEMPLATE_TYPE="$2"
            shift 2
            ;;
        --target-dir|-d)
            TARGET_DIR="$2"
            shift 2
            ;;
        --skip-docs)
            SKIP_DOCS=true
            shift
            ;;
        --help|-h)
            echo "Vibey Framework Setup Script"
            echo ""
            echo "Usage: ./scripts/setup.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --config, -c FILE       Use existing config file"
            echo "  --template, -t TYPE     Use config template (web-app, api, data-platform, ml, infrastructure)"
            echo "  --target-dir, -d DIR    Target directory (default: current directory)"
            echo "  --skip-docs             Skip documentation generation"
            echo "  --help, -h              Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./scripts/setup.sh"
            echo "  ./scripts/setup.sh --template web-app"
            echo "  ./scripts/setup.sh --config my-config.yaml"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Main setup function
main() {
    print_header "Vibey Framework Setup"
    echo ""

    # Step 1: Check prerequisites
    print_info "Checking prerequisites..."
    check_prerequisites
    echo ""

    # Step 2: Copy framework structure
    print_info "Installing Vibey framework..."
    install_framework
    echo ""

    # Step 3: Setup configuration
    print_info "Configuring project..."
    setup_configuration
    echo ""

    # Step 4: Generate documentation
    if [ "$SKIP_DOCS" = false ]; then
        print_info "Generating documentation..."
        generate_documentation
        echo ""
    fi

    # Step 5: Create directory structure
    print_info "Creating directory structure..."
    create_directories
    echo ""

    # Step 6: Done!
    print_header "Setup Complete! 🎉"
    echo ""
    print_success "Vibey framework installed successfully"
    echo ""
    print_next_steps
}

check_prerequisites() {
    local missing_deps=false

    # Check for Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        missing_deps=true
    else
        print_success "Python 3 found"
    fi

    # Check for PyYAML
    if ! python3 -c "import yaml" 2>/dev/null; then
        print_warning "PyYAML not found (required for config validation)"
        print_info "Install with: pip install pyyaml"
    else
        print_success "PyYAML found"
    fi

    # Check for Jinja2
    if ! python3 -c "import jinja2" 2>/dev/null; then
        print_warning "Jinja2 not found (required for template rendering)"
        print_info "Install with: pip install jinja2"
    else
        print_success "Jinja2 found"
    fi

    if [ "$missing_deps" = true ]; then
        print_error "Missing required dependencies. Please install them and try again."
        exit 1
    fi
}

install_framework() {
    local target_claude_dir="$TARGET_DIR/.claude"

    # Create .claude directory
    mkdir -p "$target_claude_dir"
    print_success "Created .claude/ directory"

    # Copy agents
    if [ -d "$VIBEY_ROOT/agents" ]; then
        cp -r "$VIBEY_ROOT/agents" "$target_claude_dir/"
        print_success "Installed agents (11 agents)"
    fi

    # Copy workflows
    if [ -d "$VIBEY_ROOT/workflows" ]; then
        cp -r "$VIBEY_ROOT/workflows" "$target_claude_dir/"
        print_success "Installed workflows (15 workflows)"
    fi

    # Copy templates
    if [ -d "$VIBEY_ROOT/templates" ]; then
        cp -r "$VIBEY_ROOT/templates" "$target_claude_dir/"
        print_success "Installed templates (21 handoff templates)"
    fi

    # Copy config directory
    if [ -d "$VIBEY_ROOT/config" ]; then
        cp -r "$VIBEY_ROOT/config" "$target_claude_dir/"
        print_success "Installed config schema and templates"
    fi

    # Copy scripts
    if [ -d "$VIBEY_ROOT/scripts" ]; then
        mkdir -p "$TARGET_DIR/scripts"
        cp "$VIBEY_ROOT/scripts/"*.py "$TARGET_DIR/scripts/" 2>/dev/null || true
        print_success "Installed utility scripts"
    fi

    # Copy .claude/README.md
    if [ -f "$VIBEY_ROOT/.claude/README.md" ]; then
        cp "$VIBEY_ROOT/.claude/README.md" "$target_claude_dir/"
        print_success "Installed framework documentation"
    fi
}

setup_configuration() {
    local config_dest="$TARGET_DIR/project-config.yaml"

    # If config file specified, use it
    if [ -n "$CONFIG_FILE" ]; then
        if [ -f "$CONFIG_FILE" ]; then
            cp "$CONFIG_FILE" "$config_dest"
            print_success "Copied config from $CONFIG_FILE"
            return
        else
            print_error "Config file not found: $CONFIG_FILE"
            exit 1
        fi
    fi

    # If template specified, use it
    if [ -n "$TEMPLATE_TYPE" ]; then
        local template_file="$TARGET_DIR/.claude/config/config-templates/${TEMPLATE_TYPE}-config.yaml"
        if [ -f "$template_file" ]; then
            cp "$template_file" "$config_dest"
            print_success "Created config from $TEMPLATE_TYPE template"
            return
        else
            print_error "Template not found: $TEMPLATE_TYPE"
            print_info "Available templates: web-app, api, data-platform, ml, infrastructure"
            exit 1
        fi
    fi

    # Interactive setup
    echo ""
    print_info "Let's set up your project configuration"
    echo ""

    echo "Choose your project type:"
    echo "  1) Web Application (frontend + backend)"
    echo "  2) API Service (backend only)"
    echo "  3) Data Platform (ETL, pipelines)"
    echo "  4) Machine Learning (models, training)"
    echo "  5) Infrastructure (IaC, deployment)"
    echo ""
    read -p "Enter choice (1-5): " project_choice

    case $project_choice in
        1)
            TEMPLATE_TYPE="web-app"
            ;;
        2)
            TEMPLATE_TYPE="api"
            ;;
        3)
            TEMPLATE_TYPE="data-platform"
            ;;
        4)
            TEMPLATE_TYPE="ml"
            ;;
        5)
            TEMPLATE_TYPE="infrastructure"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac

    local template_file="$TARGET_DIR/.claude/config/config-templates/${TEMPLATE_TYPE}-config.yaml"
    if [ -f "$template_file" ]; then
        cp "$template_file" "$config_dest"
        print_success "Created config from $TEMPLATE_TYPE template"
        print_info "Edit project-config.yaml to customize your project"
    else
        print_error "Template not found: $template_file"
        exit 1
    fi
}

generate_documentation() {
    local config_file="$TARGET_DIR/project-config.yaml"
    local template_file="$TARGET_DIR/.claude/templates/CLAUDE.md.template"
    local output_file="$TARGET_DIR/CLAUDE.md"

    if [ ! -f "$config_file" ]; then
        print_warning "No config file found, skipping documentation generation"
        return
    fi

    if [ ! -f "$template_file" ]; then
        print_warning "No CLAUDE.md template found, skipping documentation generation"
        return
    fi

    # Check if render script exists
    if [ -f "$TARGET_DIR/scripts/render-template.py" ]; then
        print_info "Rendering CLAUDE.md from template..."

        if python3 "$TARGET_DIR/scripts/render-template.py" \
            --config "$config_file" \
            --template "$template_file" \
            --output "$output_file" 2>/dev/null; then
            print_success "Generated CLAUDE.md"
        else
            print_warning "Failed to generate CLAUDE.md (missing dependencies?)"
            print_info "You can generate it later with:"
            print_info "  python3 scripts/render-template.py -c project-config.yaml -t .claude/templates/CLAUDE.md.template -o CLAUDE.md"
        fi
    else
        print_warning "Template renderer not found, skipping CLAUDE.md generation"
    fi
}

create_directories() {
    local dirs=(
        "$TARGET_DIR/docs"
        "$TARGET_DIR/docs/sprints"
        "$TARGET_DIR/docs/operations"
        "$TARGET_DIR/docs/reference"
        "$TARGET_DIR/docs/architecture"
    )

    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "Created $(basename "$dir")/ directory"
        fi
    done
}

print_next_steps() {
    echo "Next steps:"
    echo ""
    echo "1. Customize your configuration:"
    echo "   ${GREEN}vim project-config.yaml${NC}"
    echo ""
    echo "2. Generate CLAUDE.md:"
    echo "   ${GREEN}python3 scripts/render-template.py -c project-config.yaml -t .claude/templates/CLAUDE.md.template -o CLAUDE.md${NC}"
    echo ""
    echo "3. Validate your config:"
    echo "   ${GREEN}python3 scripts/validate-config.py project-config.yaml${NC}"
    echo ""
    echo "4. Start planning your first sprint:"
    echo "   ${GREEN}cat .claude/workflows/sprint-planning.md${NC}"
    echo ""
    echo "5. Explore the agent framework:"
    echo "   ${GREEN}cat .claude/README.md${NC}"
    echo ""
    print_info "Happy building! 🚀"
}

# Run main function
main
