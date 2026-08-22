#!/usr/bin/env bash
# PreToolUse hook: validates lifecycle completeness before closing an issue as Done.
# Successor to the Jira custom-field gate — the Verification/Post-Mortem custom
# fields are now structured issue comments (see .claude/rules/custom-fields.md).
#
# Gates: mcp__github__issue_write with state=closed, state_reason=completed
#        (closing as not_planned / Won't Do is NOT gated).
# Allow paths:
#   1. Fresh skill execution context marker (< 10 min) — a skill manages the close
#   2. A '## Verification Report' comment already exists on the issue (read-only gh api check)
# Exit 2 = block (no verification evidence), Exit 0 = allow.

set -euo pipefail

INPUT=$(cat)

# Parse tool name + close parameters in one pass: "tool|method|state|reason|owner|repo|number"
PARSED=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print('|||||||')
    sys.exit(0)
ti = d.get('tool_input', {})
print('|'.join(str(x) for x in [
    d.get('tool_name', ''),
    ti.get('method', ''),
    ti.get('state', ''),
    ti.get('state_reason', ''),
    ti.get('owner', ''),
    ti.get('repo', ''),
    ti.get('issue_number', ti.get('number', '')),
]))
" 2>/dev/null || echo "|||||||")

IFS='|' read -r TOOL_NAME METHOD STATE REASON OWNER REPO ISSUE_NUM <<< "$PARSED"

if [[ "$TOOL_NAME" != "mcp__github__issue_write" ]]; then
    exit 0  # Not an issue write
fi

# Only gate close-as-completed. Won't Do (not_planned) and non-close updates pass.
if [[ "$STATE" != "closed" || "$REASON" == "not_planned" ]]; then
    exit 0
fi

OWNER="${OWNER:-fredabood}"
ISSUE_REF="${REPO:-?}#${ISSUE_NUM:-?}"

# Allow path 1: fresh skill execution context (skill is managing the lifecycle).
#
# The marker lives under $TMPDIR keyed on the session, not in the repo root (LAB-1426) —
# the root is a deploy mirror the worktree gate blocks, so 14 skills could not write it at
# all from a primary-rooted session. lib/skill-marker.sh owns path resolution and the
# freshness window so this hook and github-skill-gate.sh cannot drift apart.
. "$(dirname "$0")/lib/skill-marker.sh"

SESSION_ID=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    print(json.load(sys.stdin).get('session_id', '') or '')
except Exception:
    print('')
" 2>/dev/null || echo "")

if skill_marker_fresh "$SESSION_ID"; then
    echo "LIFECYCLE GATE: $ISSUE_REF -> closed/completed (via skill)"
    exit 0
fi

# Allow path 2: verification report comment already posted (read-only check)
if [[ -n "$REPO" && -n "$ISSUE_NUM" ]]; then
    COMMENTS=$(gh api "repos/$OWNER/$REPO/issues/$ISSUE_NUM/comments" --paginate --jq '.[].body' 2>/dev/null || echo "")
    if printf '%s' "$COMMENTS" | grep -q '## Verification Report'; then
        echo "LIFECYCLE GATE: $ISSUE_REF -> closed/completed (verification report found)"
        exit 0
    fi
fi

# No skill context and no verification comment — block the close
echo "[lifecycle-field-check] BLOCKED: Cannot close $ISSUE_REF as completed without verification."
echo "Post the structured lifecycle comments first (see .claude/rules/custom-fields.md):"
echo "  - '## Verification Report' comment with '### Criteria Tested' + '### Results Summary'"
echo "  - '## Post-Mortem: <KEY> — <summary>' comment"
echo "Then close via /complete-task or /workflow (which set the skill execution context),"
echo "or re-run the close after the verification comment exists."
echo "To cancel instead of complete, close with state_reason: not_planned (Won't Do)."
exit 2
