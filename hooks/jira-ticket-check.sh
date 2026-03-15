#!/usr/bin/env bash
# Post-commit async hook: warns if commit message lacks a Jira ticket reference.
# Also checks branch name for ticket references.
# Runs asynchronously — never blocks the commit.

set -euo pipefail

# Only run on actual commit commands
if [[ "${TOOL_INPUT:-}" != *"git commit"* ]]; then
  exit 0
fi

# Get the latest commit message
COMMIT_MSG=$(git log -1 --pretty=%B 2>/dev/null || true)

# Get the current branch name
BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)

# Check for Jira ticket pattern (e.g., PROJ-123, VIBEY-456)
COMMIT_HAS_TICKET=false
BRANCH_HAS_TICKET=false

if echo "$COMMIT_MSG" | grep -qE '[A-Z]+-[0-9]+'; then
  COMMIT_HAS_TICKET=true
fi

if echo "$BRANCH_NAME" | grep -qE '[A-Z]+-[0-9]+'; then
  BRANCH_HAS_TICKET=true
fi

if [[ "$COMMIT_HAS_TICKET" == "false" && "$BRANCH_HAS_TICKET" == "false" ]]; then
  echo "⚠️  WARNING: No Jira ticket reference found."
  echo "   Commit message: no ticket key (e.g., PROJ-123)"
  echo "   Branch name: no ticket key"
  echo ""
  echo "   To fix: Run /create-ticket to create a tracking ticket,"
  echo "   or include a ticket reference in the commit message."
elif [[ "$COMMIT_HAS_TICKET" == "false" ]]; then
  echo "NOTE: Commit message does not include a Jira ticket reference."
  echo "   Branch '$BRANCH_NAME' has a reference, but prefer including it in the commit message too."
  echo "   Format: KEY-123: <description>"
fi

exit 0
