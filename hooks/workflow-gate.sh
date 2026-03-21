#!/usr/bin/env bash
# PreToolUse hook: enforces workflow phase gates.
# Reads .workflow-state.json to determine which phases are complete.
# No state file = no active workflow = allow everything.
#
# Gates:
#   Edit/Write on code files → blocked until Phase 3 (Plan) complete
#   Bash(git commit)         → blocked until Phase 4 (Git Setup) complete
#   transitionJiraIssue(Done)→ blocked until Phases 6+7 complete

set -euo pipefail

STATE_FILE=".workflow-state.json"

# No state file = no workflow active = allow everything
if [[ ! -f "$STATE_FILE" ]]; then
  exit 0
fi

# Read tool info from stdin
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('tool_name', ''))
" 2>/dev/null || echo "")

TOOL_INPUT=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(json.dumps(data.get('tool_input', {})))
" 2>/dev/null || echo "{}")

# Read state file
STATE=$(python3 -c "
import json
print(json.dumps(json.load(open('$STATE_FILE'))))
" 2>/dev/null || echo "{}")

phase_done() {
  local phase_num="$1"
  echo "$STATE" | python3 -c "
import sys, json
s = json.load(sys.stdin)
print('yes' if s.get('phase_${phase_num}_at') else 'no')
" 2>/dev/null || echo "no"
}

# --- Gate: Edit/Write blocked until Phase 3 (Plan) is complete ---
if [[ "$TOOL_NAME" == "Edit" || "$TOOL_NAME" == "Write" ]]; then
  FILE_PATH=$(echo "$TOOL_INPUT" | python3 -c "
import sys, json
print(json.load(sys.stdin).get('file_path', ''))
" 2>/dev/null || echo "")

  # Allow edits to non-code files without Phase 3
  # Allowlist: .claude/ configs, docs/, markdown, state files, gitignore, env
  if [[ "$FILE_PATH" == *".claude/"* \
     || "$FILE_PATH" == *".workflow-state"* \
     || "$FILE_PATH" == *"docs/"* \
     || "$FILE_PATH" == *".gitignore"* \
     || "$FILE_PATH" == *".env"* \
     || "$FILE_PATH" == *"CLAUDE.md"* \
     || "$FILE_PATH" == *"README.md"* \
     || "$FILE_PATH" == *"homelab-data/"* ]]; then
    exit 0
  fi

  if [[ "$(phase_done 3)" == "no" ]]; then
    echo "WORKFLOW GATE: Phase 3 (Plan) is not complete."
    echo "Post your implementation plan to the work item before editing code."
    echo ""
    echo "Completed phases:"
    for i in 1 2 3; do
      if [[ "$(phase_done "$i")" == "yes" ]]; then
        echo "  Phase $i: ✓"
      else
        echo "  Phase $i: ✗"
      fi
    done
    echo ""
    echo "To proceed: complete Phases 1-3 in /workflow, or delete .workflow-state.json to deactivate."
    exit 2
  fi
fi

# --- Gate: git commit blocked until Phase 4 (Git Setup) is complete ---
if [[ "$TOOL_NAME" == "Bash" ]]; then
  CMD=$(echo "$TOOL_INPUT" | python3 -c "
import sys, json
print(json.load(sys.stdin).get('command', ''))
" 2>/dev/null || echo "")

  if [[ "$CMD" == *"git commit"* ]]; then
    if [[ "$(phase_done 4)" == "no" ]]; then
      echo "WORKFLOW GATE: Phase 4 (Git Setup) is not complete."
      echo "Create your feature branch before committing."
      echo ""
      echo "To proceed: complete Phase 4 in /workflow, or delete .workflow-state.json to deactivate."
      exit 2
    fi
  fi
fi

# --- Gate: Done transition blocked until Phases 6+7 are complete ---
if [[ "$TOOL_NAME" == "mcp__claude_ai_Atlassian__transitionJiraIssue" ]]; then
  TRANSITION_ID=$(echo "$TOOL_INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
# Handle both {transition: {id: '31'}} and flat {transitionId: '31'}
t = d.get('transition', {})
if isinstance(t, dict):
    print(t.get('id', ''))
else:
    print(d.get('transitionId', ''))
" 2>/dev/null || echo "")

  if [[ "$TRANSITION_ID" == "31" ]]; then
    phase6=$(phase_done 6)
    phase7=$(phase_done 7)
    if [[ "$phase6" == "no" || "$phase7" == "no" ]]; then
      echo "WORKFLOW GATE: Cannot transition to Done."
      echo "Complete these phases first:"
      if [[ "$phase6" == "no" ]]; then
        echo "  Phase 6 (Verification): Post verification report to work item"
      fi
      if [[ "$phase7" == "no" ]]; then
        echo "  Phase 7 (Completion): Post post-mortem to work item"
      fi
      echo ""
      echo "To proceed: complete the required phases in /workflow, or delete .workflow-state.json to deactivate."
      exit 2
    fi
  fi
fi

exit 0
