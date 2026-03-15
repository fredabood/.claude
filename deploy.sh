#!/usr/bin/env bash
# Deploy vibey's .claude/ directory and CLAUDE.md template to a target project.
#
# Usage:
#   ./deploy.sh /path/to/project
#   ./deploy.sh /path/to/project --force    # Overwrite existing files
#
# What it does:
#   1. Copies .claude/ directory (skills, agents, rules, hooks, settings)
#   2. Copies CLAUDE.md template (if one doesn't exist, or --force)
#   3. Makes hook scripts executable

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:?Usage: ./deploy.sh /path/to/project [--force]}"
FORCE="${2:-}"

if [[ ! -d "$TARGET" ]]; then
  echo "Error: Target directory does not exist: $TARGET"
  exit 1
fi

# Copy .claude/ directory
if [[ -d "$TARGET/.claude" && "$FORCE" != "--force" ]]; then
  echo "Warning: $TARGET/.claude already exists."
  echo "  Use --force to overwrite, or manually merge."
  echo "  Copying only missing files..."

  # Copy files that don't exist in target
  find "$SCRIPT_DIR/.claude" -type f | while read -r src; do
    rel="${src#$SCRIPT_DIR/}"
    dst="$TARGET/$rel"
    if [[ ! -f "$dst" ]]; then
      mkdir -p "$(dirname "$dst")"
      cp "$src" "$dst"
      echo "  Added: $rel"
    fi
  done
else
  echo "Copying .claude/ directory..."
  cp -r "$SCRIPT_DIR/.claude" "$TARGET/.claude"
fi

# Copy CLAUDE.md template
if [[ ! -f "$TARGET/CLAUDE.md" || "$FORCE" == "--force" ]]; then
  echo "Copying CLAUDE.md template..."
  cp "$SCRIPT_DIR/CLAUDE.md" "$TARGET/CLAUDE.md"
else
  echo "Skipping CLAUDE.md (already exists). Use --force to overwrite."
fi

# Make hooks executable
find "$TARGET/.claude/hooks" -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

echo ""
echo "Done! Vibey deployed to: $TARGET"
echo ""
echo "Next steps:"
echo "  1. Edit $TARGET/CLAUDE.md with your project's CloudId and conventions"
echo "  2. Review $TARGET/.claude/settings.json hook configuration"
echo "  3. Try: /start-task, /status, /implement-feature, /discovery"
