#!/usr/bin/env bash
# Docker production safety gate.
# Blocks destructive docker commands (stop, rm, rmi, kill) on production containers.
# Staging containers (*-staging) are allowed freely.
#
# Exit codes:
#   0 = allow
#   2 = block (Claude Code will surface the message to the user)

set -euo pipefail

# Claude Code passes the full command via stdin as JSON.
# Extract the command field.
INPUT=$(cat)
# Payload shape is {"tool_name":"Bash","tool_input":{"command":...}} on current
# Claude Code; older harnesses passed a top-level "command". Support both —
# the top-level-only parse left this gate silently fail-open (found LAB-215/LAB-961
# verification, 2026-07-13).
CMD=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    print('')
    sys.exit(0)
print((d.get('tool_input') or {}).get('command') or d.get('command') or '')
" 2>/dev/null || echo "")

if [[ -z "$CMD" ]]; then
  exit 0
fi

# Only intercept destructive docker subcommands
if ! echo "$CMD" | grep -qE '^docker (stop|rm|rmi|kill)\b'; then
  exit 0
fi

# Extract all arguments after the subcommand (potential container/image targets)
TARGETS=$(echo "$CMD" | sed -E 's/^docker (stop|rm|rmi|kill)[[:space:]]*//' | tr ' ' '\n' | grep -v '^-')

# Allow if every target ends with -staging
ALL_STAGING=true
for TARGET in $TARGETS; do
  if [[ "$TARGET" != *"-staging"* ]]; then
    ALL_STAGING=false
    break
  fi
done

if [[ "$ALL_STAGING" == "true" && -n "$TARGETS" ]]; then
  exit 0
fi

# Block and explain
echo "[docker-safety-check] Safety gate: '$CMD' targets a production container."
echo ""
echo "Production containers should not be stopped or deleted accidentally."
echo "Staging containers (*-staging) are exempt from this check."
echo ""
echo "If you intend to proceed, re-run the command with an explicit confirmation"
echo "comment explaining why (e.g. 'docker stop n8n  # confirmed: planned maintenance')."
echo "Alternatively, ask Claude to bypass this check for a specific reason."

exit 2
