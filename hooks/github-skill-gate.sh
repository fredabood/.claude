#!/usr/bin/env bash
# github-skill-gate.sh — Block raw GitHub MCP lifecycle write calls
# (successor to atlassian-skill-gate.sh after the Jira → GitHub Issues migration)
# Exit 0 = allow, Exit 2 = block

# Read hook payload from stdin
INPUT=$(cat)

# tool_name is in the hook payload JSON; fall back to TOOL_NAME env for legacy callers
TOOL_NAME=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    print(json.load(sys.stdin).get('tool_name', ''))
except Exception:
    print('')
" 2>/dev/null)
if [ -z "$TOOL_NAME" ]; then
  TOOL_NAME="${TOOL_NAME:-}"
fi

# GitHub MCP write (lifecycle-mutating) operations to gate.
# Read tools (issue_read, list_issues, search_issues, projects_get,
# list_issue_fields, list_issue_types) always pass.
WRITE_TOOLS="mcp__github__issue_write mcp__github__add_issue_comment mcp__github__sub_issue_write mcp__github__projects_write"

IS_WRITE=false
for tool in $WRITE_TOOLS; do
  if [ "$TOOL_NAME" = "$tool" ]; then
    IS_WRITE=true
    break
  fi
done

# Non-write (or unidentifiable) operations always pass
if [ "$IS_WRITE" = false ]; then
  exit 0
fi

# Check for skill execution context marker
MARKER="${CLAUDE_PROJECT_DIR:-.}/.skill-execution-context.json"
if [ -f "$MARKER" ]; then
  # Check if marker is fresh (< 10 minutes old)
  if [ "$(uname)" = "Darwin" ]; then
    MARKER_AGE=$(( $(date +%s) - $(stat -f %m "$MARKER") ))
  else
    MARKER_AGE=$(( $(date +%s) - $(stat -c %Y "$MARKER") ))
  fi

  if [ "$MARKER_AGE" -lt 600 ]; then
    exit 0
  fi
fi

# Block with helpful message
echo "[github-skill-gate] BLOCKED: Direct GitHub MCP write calls (issue_write / add_issue_comment / sub_issue_write / projects_write) are not allowed."
echo "Use the appropriate skill instead:"
echo "  - /create-ticket to create issues (labels + acceptance criteria enforced)"
echo "  - /start-task to pick up an issue (board Status -> In Progress + assignment comment)"
echo "  - /complete-task to close issues (state: closed, state_reason: completed)"
echo "  - /review-ticket to post the verification report"
echo "  - /workflow for the full gated lifecycle"
echo ""
echo "If you need to make a raw call, use a skill that sets the execution context marker."
exit 2
