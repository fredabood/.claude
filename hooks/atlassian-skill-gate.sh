#!/usr/bin/env bash
# atlassian-skill-gate.sh — Block direct Atlassian MCP write calls
# Exit 0 = allow, Exit 2 = block

# Read tool input from stdin
INPUT=$(cat)
TOOL_NAME="${TOOL_NAME:-}"

# If TOOL_NAME not set, try to extract from hook environment
# Claude Code passes tool_name in the hook context

# Write operations to block (only if no fresh marker)
WRITE_TOOLS="createJiraIssue editJiraIssue transitionJiraIssue addCommentToJiraIssue createIssueLink addWorklogToJiraIssue"

# Check if this is a write operation
IS_WRITE=false
for tool in $WRITE_TOOLS; do
  if echo "$TOOL_NAME" | grep -q "$tool"; then
    IS_WRITE=true
    break
  fi
done

# Read operations always pass
if [ "$IS_WRITE" = false ]; then
  exit 0
fi

# Check for skill execution context marker
MARKER=".skill-execution-context.json"
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
echo "BLOCKED: Direct Atlassian MCP write calls are not allowed."
echo "Use the appropriate skill instead:"
echo "  - /create-ticket to create issues"
echo "  - /start-task to transition issues"
echo "  - /complete-task to close issues"
echo "  - /review-ticket to add verification"
echo "  - /workflow for the full lifecycle"
echo ""
echo "If you need to make a raw API call, use a skill that sets the execution context marker."
exit 2
