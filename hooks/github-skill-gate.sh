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

# The same operations via the `gh` CLI (LAB-1425). Until now this hook matched MCP tool names
# only, so every one of these walked straight past it — and with the MCP server disconnected,
# `gh` is the path everything takes. During the LAB-966 audit 34 issues were closed this way
# with no gate involvement.
#
# Gated at parity with the MCP path: any issue lifecycle write, including a Won't Do close
# (mcp__github__issue_write covers those too). What is NOT gated is decided in
# lib/gh-lifecycle.sh — `gh pr *`, `gh label *`, dependency links and every read.
GH_VERDICT=""
if [ "$TOOL_NAME" = "Bash" ]; then
  . "$(dirname "$0")/lib/gh-lifecycle.sh"
  GH_CMD=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    print((json.load(sys.stdin).get('tool_input') or {}).get('command', '') or '')
except Exception:
    print('')
" 2>/dev/null)
  if [ -n "$GH_CMD" ]; then
    GH_VERDICT="$(gh_lifecycle_parse "$GH_CMD" | cut -d'|' -f1)"
    [ -n "$GH_VERDICT" ] && IS_WRITE=true
  fi
fi

# Non-write (or unidentifiable) operations always pass
if [ "$IS_WRITE" = false ]; then
  exit 0
fi

# Allow while a sanctioned skill run is in progress.
#
# The marker no longer lives in the repo root (LAB-1426): 14 skills could not write it at
# all from the primary checkout, because the worktree gate blocks writes to a deploy mirror.
# It now lives under $TMPDIR, keyed on the session. Path resolution and the freshness
# window are owned by lib/skill-marker.sh so this hook and lifecycle-field-check.sh cannot
# drift apart.
. "$(dirname "$0")/lib/skill-marker.sh"

# Prefer the session id from the hook payload; skill_marker_fresh falls back to the
# environment, and then to a project-scoped name, when it is absent.
SESSION_ID=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    print(json.load(sys.stdin).get('session_id', '') or '')
except Exception:
    print('')
" 2>/dev/null)

if skill_marker_fresh "$SESSION_ID"; then
  # Refresh on use (LAB-1425): the window becomes 600s since the last SANCTIONED operation
  # rather than 600s since `set`. Without this, any pass longer than ten minutes — a
  # /workflow run, or the 34-issue audit cleanup — expires mid-run and the gate starts
  # refusing a skill that is legitimately still working. Widening the TTL instead would
  # weaken the gate for everyone; a `bulk` escape hatch would just be a bigger hole.
  skill_marker_touch "$SESSION_ID"
  exit 0
fi

# Block. Name what is actually gated and what the sanctioned routes are — the previous
# message listed only skills, which read as "there is no other way". That was true when this
# hook saw the MCP path alone; it is not true now (LAB-1425).
if [ -n "$GH_VERDICT" ]; then
  echo "[github-skill-gate] BLOCKED: raw \`gh\` issue lifecycle write ($GH_VERDICT) with no active skill run."
else
  echo "[github-skill-gate] BLOCKED: raw GitHub MCP lifecycle write (issue_write / add_issue_comment / sub_issue_write / projects_write) with no active skill run."
fi
echo ""
echo "Lifecycle writes are skill-mediated so that labels, acceptance criteria, verification"
echo "reports and board status are enforced. Use the skill that owns the operation:"
echo "  - /create-ticket   create issues (labels + acceptance criteria enforced)"
echo "  - /start-task      pick up an issue (board Status -> In Progress + assignment comment)"
echo "  - /complete-task   close issues (state: closed, state_reason: completed)"
echo "  - /review-ticket   post the verification report"
echo "  - /workflow        the full gated lifecycle"
echo ""
echo "Both the MCP tools and the equivalent \`gh\` commands are gated. NOT gated, deliberately:"
echo "  gh pr *, gh label *, gh api .../dependencies/blocked_by (no MCP equivalent), all reads."
echo ""
echo "A skill run sets an execution marker that exempts these calls, and the marker refreshes"
echo "on each sanctioned operation, so a long or bulk pass stays authorized while it works:"
echo "  bash \"\${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/lib/skill-marker.sh\" set <skill>"
exit 2
