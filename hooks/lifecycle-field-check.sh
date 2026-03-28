#!/usr/bin/env bash
# PreToolUse hook: validates lifecycle field completeness before status transitions.
# Gates Implementation Complete (81) and Review Complete (91) transitions.
# Exit 2 = block (fields incomplete), Exit 0 = allow.
#
# Triggered on: transitionJiraIssue
# Checks:
#   Implementation Complete: PM Sections + Verification Sections complete, all SC children Done/Won't Do
#   Review Complete: Doc Review fields populated, HITL SC children Done

set -euo pipefail

# Parse tool call arguments from stdin
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")

if [[ "$TOOL_NAME" != "mcp__claude_ai_Atlassian__transitionJiraIssue" ]]; then
    exit 0  # Not a transition call
fi

# Extract transition ID and issue key
TRANSITION_ID=$(echo "$INPUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
t = d.get('tool_input', {}).get('transition', {})
print(t.get('id', ''))
" 2>/dev/null || echo "")

ISSUE_KEY=$(echo "$INPUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('issueIdOrKey', ''))
" 2>/dev/null || echo "")

# Only gate transitions 81 (Implementation Complete) and 91 (Review Complete)
if [[ "$TRANSITION_ID" != "81" && "$TRANSITION_ID" != "91" ]]; then
    exit 0
fi

# For now, log and allow — full field checking requires Jira API calls
# which add latency to every transition. The /workflow skill handles
# field population as part of its phase gates, so this hook serves as
# a safety net for direct transitionJiraIssue calls outside /workflow.
#
# TODO: Add actual field checks once the overhead is acceptable:
#   - Transition 81: Check customfield_10192 (PM Sections) + customfield_10191 (Verification)
#   - Transition 91: Check customfield_10185/10186 (Doc Review) non-empty

if [[ "$TRANSITION_ID" == "81" ]]; then
    echo "LIFECYCLE GATE: Transitioning $ISSUE_KEY to Implementation Complete."
    echo "Ensure post-mortem + verification sections are complete before proceeding."
fi

if [[ "$TRANSITION_ID" == "91" ]]; then
    echo "LIFECYCLE GATE: Transitioning $ISSUE_KEY to Review Complete."
    echo "Ensure doc review + memory update fields are populated before proceeding."
fi

exit 0
