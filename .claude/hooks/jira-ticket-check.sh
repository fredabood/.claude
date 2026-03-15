#!/usr/bin/env bash
# Post-commit async hook: warns if commit message lacks a Jira ticket reference.
# Runs asynchronously — never blocks the commit.

set -euo pipefail

# Only run on actual commit commands
if [[ "${TOOL_INPUT:-}" != *"git commit"* ]]; then
  exit 0
fi

# Get the latest commit message
COMMIT_MSG=$(git log -1 --pretty=%B 2>/dev/null || true)

# Check for Jira ticket pattern (e.g., PROJ-123, VIBEY-456)
if ! echo "$COMMIT_MSG" | grep -qE '[A-Z]+-[0-9]+'; then
  echo "WARNING: Commit message does not reference a Jira ticket (e.g., PROJ-123)."
  echo "Consider including a ticket reference for traceability."
fi

exit 0
