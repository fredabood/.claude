#!/usr/bin/env bash
# workflow-gate.test.sh — exercises the gh-CLI close gate added in LAB-1366.
#
# Until LAB-1366 the close gate matched mcp__github__issue_write ONLY, so
# `gh issue close` walked straight past Phases 6+7. While the GitHub MCP server is
# disconnected that is the path EVERY close takes, so the gate was fully inert.
#
# Both directions are asserted, deliberately. A gate that blocks everything is as broken
# as one that blocks nothing, so every must-block case is paired with control cases
# proving the gate discriminates: Won't Do still closes, reads and comments pass, and the
# very same close SUCCEEDS once Phases 6+7 are recorded.
#
# Run: bash .claude/hooks/tests/workflow-gate.test.sh

set -u

GATE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/workflow-gate.sh"
[ -f "$GATE" ] || { echo "cannot find workflow-gate.sh at $GATE"; exit 1; }

PASS=0
FAIL=0

# payload <command> — the PreToolUse stdin envelope for a Bash call.
payload() {
  python3 -c 'import json,sys; print(json.dumps({"tool_name":"Bash","tool_input":{"command":sys.argv[1]}}))' "$1"
}

# check <BLOCK|ALLOW> <state-json|""> <label> <command>
check() {
  local expect="$1" state="$2" label="$3" cmd="$4" work rc got
  work="$(mktemp -d)"
  ( cd "$work" || exit 1
    [ -n "$state" ] && printf '%s' "$state" > .workflow-state.json
    payload "$cmd" | bash "$GATE" ) >/dev/null 2>&1
  rc=$?
  rm -rf "$work"
  got=ALLOW
  [ "$rc" = "2" ] && got=BLOCK
  if [ "$got" = "$expect" ]; then
    printf '  ok: %s\n' "$label"
    PASS=$((PASS + 1))
  else
    printf '  FAIL (expected %s, got %s): %s\n' "$expect" "$got" "$label"
    FAIL=$((FAIL + 1))
  fi
}

MID='{"work_item_key":"LAB-1366","phase_3_at":"x","phase_4_at":"x"}'
DONE='{"work_item_key":"LAB-1366","phase_3_at":"x","phase_4_at":"x","phase_6_at":"x","phase_7_at":"x"}'

echo "closing as Done before Phases 6+7 must be blocked:"
check BLOCK "$MID" "plain close"                  'gh issue close 1366 --repo fredabood/homelab'
check BLOCK "$MID" "explicit --reason completed"  'gh issue close 1366 --reason completed'
check BLOCK "$MID" "no repo flag"                 'gh issue close 1366'
check BLOCK "$MID" "hidden in bash -c"            "bash -c 'gh issue close 1366 --reason completed'"
check BLOCK "$MID" "hidden in sh -lc"             'sh -lc "gh issue close 1366"'
check BLOCK "$MID" "absolute interpreter path"    "/bin/bash -c 'gh issue close 1366'"
check BLOCK "$MID" "behind an env assignment"     'GH_TOKEN=x gh issue close 1366'
check BLOCK "$MID" "behind a wrapper word"        'command gh issue close 1366'
check BLOCK "$MID" "second in a && chain"         'echo hi && gh issue close 1366'
check BLOCK "$MID" "raw api PATCH state=closed"   'gh api -X PATCH repos/fredabood/homelab/issues/1366 -f state=closed'

echo "the gate must DISCRIMINATE, not blanket-block:"
check ALLOW "$MID" "Won't Do is never gated"      'gh issue close 1366 --reason not_planned'
check ALLOW "$MID" "Won't Do inside bash -c"      "bash -c 'gh issue close 1366 --reason not_planned'"
check ALLOW "$MID" "reading an issue"             'gh issue view 1366 --repo fredabood/homelab --json state'
check ALLOW "$MID" "commenting"                   'gh issue comment 1366 --body-file /tmp/x.md'
check ALLOW "$MID" "creating an issue"            'gh issue create --title x --body-file /tmp/x.md'
check ALLOW "$MID" "listing issues"               'gh issue list --state closed'
check ALLOW "$MID" "reopening an issue"           'gh api -X PATCH repos/fredabood/homelab/issues/1366 -f state=open'
check ALLOW "$MID" "prose that merely says it"    'echo "do not gh issue close this yet"'
check ALLOW "$MID" "closing a PR, not an issue"   'gh pr close 1422'
check ALLOW "$MID" "unrelated gh api read"        'gh api repos/fredabood/homelab --jq .name'
check ALLOW "$MID" "state=closed on a non-issue"  'gh api -X PATCH repos/fredabood/homelab/pulls/1 -f state=closed'

echo "once Phases 6+7 are recorded, the same closes must succeed:"
check ALLOW "$DONE" "plain close"                 'gh issue close 1366 --repo fredabood/homelab'
check ALLOW "$DONE" "explicit --reason completed" 'gh issue close 1366 --reason completed'
check ALLOW "$DONE" "hidden in bash -c"           "bash -c 'gh issue close 1366'"
check ALLOW "$DONE" "raw api PATCH state=closed"  'gh api -X PATCH repos/fredabood/homelab/issues/1366 -f state=closed'

echo "with no active workflow the gate is inert:"
check ALLOW "" "close with no state file"         'gh issue close 1366 --reason completed'
check ALLOW "" "commit with no state file"        'git commit -m "x"'

echo "the Phase 4 commit gate still works:"
check BLOCK '{"work_item_key":"LAB-1366","phase_3_at":"x"}' "commit before Phase 4" 'git commit -m "x"'
check ALLOW "$MID" "commit after Phase 4"         'git commit -m "x"'

echo
echo "workflow-gate tests: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
