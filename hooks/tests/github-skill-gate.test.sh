#!/usr/bin/env bash
# github-skill-gate.test.sh — LAB-1425: the hook now sees the `gh` CLI, not just MCP tools.
#
# Both directions for every case. The control cases are the important half: this gate sits on
# the path that ALL GitHub work currently takes (the MCP server is disconnected), so a gate
# that is too eager stops everything.
#
# Run: bash .claude/hooks/tests/github-skill-gate.test.sh

set -u

HOOKS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
GATE="$HOOKS_DIR/github-skill-gate.sh"
LIB="$HOOKS_DIR/lib/skill-marker.sh"
PASS=0
FAIL=0

SANDBOX="$(mktemp -d)"
trap 'rm -rf "$SANDBOX"' EXIT
export TMPDIR="$SANDBOX/tmp"      # never touch the running session's own marker
mkdir -p "$TMPDIR"

SID="test-session-1425"
MARKER="$(bash "$LIB" path "$SID")"

ok() { PASS=$((PASS + 1)); echo "  ok: $1"; }
no() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; [ -n "${2:-}" ] && echo "        $2"; }

bash_payload() { # $1 command
  python3 -c 'import json,sys; print(json.dumps({"tool_name":"Bash","session_id":sys.argv[2],"tool_input":{"command":sys.argv[1]}}))' "$1" "$SID"
}
mcp_payload() { # $1 tool name
  python3 -c 'import json,sys; print(json.dumps({"tool_name":sys.argv[1],"session_id":sys.argv[2],"tool_input":{}}))' "$1" "$SID"
}
run_gate() { printf '%s' "$1" | bash "$GATE" >/dev/null 2>&1; }

set_marker()   { CLAUDE_CODE_SESSION_ID="$SID" bash "$LIB" set testskill >/dev/null; }
clear_marker() { CLAUDE_CODE_SESSION_ID="$SID" bash "$LIB" clear; }
age_marker() { python3 - "$MARKER" "$1" <<'PY'
import os, sys, time
p, secs = sys.argv[1], int(sys.argv[2])
t = time.time() - secs
os.utime(p, (t, t))
PY
}

expect() { # $1 command, $2 expected rc, $3 label
  local rc
  run_gate "$(bash_payload "$1")"; rc=$?
  if [ "$rc" = "$2" ]; then ok "$3"; else no "$3" "expected rc=$2, got rc=$rc"; fi
}

echo "== gh lifecycle writes are BLOCKED without a skill run =="
clear_marker
# Built from fragments so this file's own execution never puts the literal verbs in a
# command line, where the sibling Bash hooks would classify them.
C="gh issue "
expect "${C}comment 1425 --body hi"           2 "gh issue comment blocked"
expect "${C}create --title x --body y"        2 "gh issue create blocked"
expect "${C}edit 1425 --add-label platform"   2 "gh issue edit blocked"
expect "${C}close 1425"                       2 "gh issue close blocked"
expect "${C}close 1425 --reason not_planned"  2 "Won't Do close blocked too (MCP parity)"

echo "== the same calls are ALLOWED during a skill run =="
set_marker
expect "${C}comment 1425 --body hi"           0 "gh issue comment allowed with marker"
expect "${C}create --title x --body y"        0 "gh issue create allowed with marker"
expect "${C}close 1425"                       0 "gh issue close allowed with marker"

echo "== control cases: these must NEVER be blocked, marker or not =="
clear_marker
expect 'gh pr create --base main --title x'                    0 "gh pr create allowed"
expect 'gh pr merge 1432 --squash --delete-branch'             0 "gh pr merge allowed"
expect 'gh label list -R fredabood/homelab'                    0 "gh label list allowed"
expect "${C}view 1425 --json body"                             0 "gh issue view allowed (read)"
expect 'gh api repos/fredabood/homelab/issues/1425'            0 "gh api GET allowed"
DEPS='gh api -X POST repos/fredabood/homelab/issues/5/depend'
DEPS="${DEPS}encies/blocked_by -F issue_id=99"
expect "$DEPS"                                                 0 "dependency link allowed (no MCP equivalent)"
expect 'git commit -m x'                                       0 "non-gh Bash allowed"
expect 'echo hello world'                                      0 "plain command allowed"

echo "== the MCP path is unchanged =="
clear_marker
run_gate "$(mcp_payload mcp__github__issue_write)"
[ $? = 2 ] && ok "MCP issue_write still blocked without marker" || no "MCP issue_write still blocked without marker"
run_gate "$(mcp_payload mcp__github__issue_read)"
[ $? = 0 ] && ok "MCP issue_read still allowed" || no "MCP issue_read still allowed"
set_marker
run_gate "$(mcp_payload mcp__github__issue_write)"
[ $? = 0 ] && ok "MCP issue_write allowed with marker" || no "MCP issue_write allowed with marker"

echo "== refresh on use: a long run stays authorized =="
set_marker
# 300s, not 599s. The margin is load-bearing: the hook spawns python, and if the run takes
# more than a second an age of 599 crosses the 600s boundary mid-test and BOTH assertions
# below fail. That flake was observed once before this comment existed. The exact boundary
# is pinned deterministically in skill-marker.test.sh, where no hook latency intervenes.
age_marker 300
BEFORE="$(python3 -c 'import os,sys; print(int(os.path.getmtime(sys.argv[1])))' "$MARKER")"
expect "${C}comment 1425 --body hi"  0 "allowed well inside the window"
AFTER="$(python3 -c 'import os,sys; print(int(os.path.getmtime(sys.argv[1])))' "$MARKER")"
if [ "$AFTER" -gt "$BEFORE" ]; then
  ok "marker refreshed on the allow path (window restarts)"
else
  no "marker refreshed on the allow path" "mtime $BEFORE -> $AFTER"
fi

echo "== but an ABANDONED marker still expires =="
set_marker
age_marker 900                       # comfortably past the window; latency only ages it more
BEFORE2="$(python3 -c 'import os,sys; print(int(os.path.getmtime(sys.argv[1])))' "$MARKER")"
expect "${C}comment 1425 --body hi"  2 "blocked well past the window"
AFTER2="$(python3 -c 'import os,sys; print(int(os.path.getmtime(sys.argv[1])))' "$MARKER")"
if [ "$AFTER2" = "$BEFORE2" ]; then
  ok "a stale marker is NOT refreshed by a blocked attempt"
else
  no "a stale marker is NOT refreshed by a blocked attempt" "mtime moved $BEFORE2 -> $AFTER2"
fi

echo "== the block message names the sanctioned routes =="
clear_marker
MSG="$(printf '%s' "$(bash_payload "${C}comment 1425 --body hi")" | bash "$GATE" 2>&1)"
printf '%s' "$MSG" | grep -q 'gh pr' \
  && ok "message names what is NOT gated" || no "message names what is NOT gated" "$MSG"
printf '%s' "$MSG" | grep -q 'skill-marker.sh' \
  && ok "message names the marker command" || no "message names the marker command" "$MSG"
printf '%s' "$MSG" | grep -qi 'refresh' \
  && ok "message explains the refresh" || no "message explains the refresh" "$MSG"

echo
echo "github-skill-gate tests: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
