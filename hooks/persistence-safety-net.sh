#!/usr/bin/env bash
# persistence-safety-net.sh — Stop hook to warn on unsaved decisions
# Advisory only — always exits 0, just prints warnings

# Resolve project root from script location (handles cwd being inside submodules)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT" || exit 0

WARNINGS=()

# Check for uncommitted memory/vault changes
if git -C submodules/memory status --porcelain 2>/dev/null | grep -q .; then
    WARNINGS+=("Uncommitted changes in memory vault (submodules/memory/)")
fi

# Check for active workflow state that wasn't completed
if [ -f ".workflow-state.json" ]; then
    PHASE=$(python3 -c "import json; print(json.load(open('.workflow-state.json')).get('phase', 'unknown'))" 2>/dev/null || echo "unknown")
    if [ "$PHASE" != "complete" ] && [ "$PHASE" != "unknown" ]; then
        WARNINGS+=("Active workflow in phase '$PHASE' — consider /handoff before ending session")
    fi
fi

# Check for uncommitted .claude/ submodule changes
if git -C .claude status --porcelain 2>/dev/null | grep -q .; then
    WARNINGS+=("Uncommitted changes in .claude/ submodule")
fi

# Check for uncommitted homelab repo changes
UNSTAGED=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')
if [ "$UNSTAGED" -gt 0 ]; then
    WARNINGS+=("$UNSTAGED unstaged file(s) in homelab repo")
fi

if [ ${#WARNINGS[@]} -gt 0 ]; then
    echo ""
    echo "SESSION PERSISTENCE CHECK:"
    for w in "${WARNINGS[@]}"; do
        echo "  ⚠ $w"
    done
    echo ""
    echo "Consider committing changes or running /handoff before ending."
fi

# Always allow — advisory only
exit 0
