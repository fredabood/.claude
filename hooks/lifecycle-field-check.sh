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

# Hard gate: require skill execution context for lifecycle transitions
MARKER=".skill-execution-context.json"
if [ -f "$MARKER" ]; then
    # Check if marker is fresh (< 10 minutes old)
    if [ "$(uname)" = "Darwin" ]; then
        MARKER_AGE=$(( $(date +%s) - $(stat -f %m "$MARKER") ))
    else
        MARKER_AGE=$(( $(date +%s) - $(stat -c %Y "$MARKER") ))
    fi

    if [ "$MARKER_AGE" -lt 600 ]; then
        # Skill is actively managing this transition — allow
        if [[ "$TRANSITION_ID" == "81" ]]; then
            echo "LIFECYCLE GATE: $ISSUE_KEY → Implementation Complete (via skill)"
        fi
        if [[ "$TRANSITION_ID" == "91" ]]; then
            echo "LIFECYCLE GATE: $ISSUE_KEY → Review Complete (via skill)"
        fi
        exit 0
    fi
fi

# No fresh skill context — block direct transitions
if [[ "$TRANSITION_ID" == "81" ]]; then
    echo "BLOCKED: Cannot transition $ISSUE_KEY to Implementation Complete without skill context."
    echo "Use /complete-task or /workflow to ensure all lifecycle fields are populated:"
    echo "  - Plan Sections Complete (customfield_10190)"
    echo "  - Verification: Criteria Tested (customfield_10178)"
    echo "  - Post-Mortem: What Went Well (customfield_10180)"
    exit 2
fi

if [[ "$TRANSITION_ID" == "91" ]]; then
    echo "BLOCKED: Cannot transition $ISSUE_KEY to Review Complete without skill context."
    echo "Use /workflow Phase 8 to ensure doc review fields are populated:"
    echo "  - Doc Review: Documentation (customfield_10185)"
    echo "  - Doc Review: Memory Updates (customfield_10186)"
    exit 2
fi
