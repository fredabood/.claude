#!/usr/bin/env bash
# label-taxonomy-check.test.sh — LAB-1425: the taxonomy gate now sees `gh issue create`.
#
# CLAUDE.md has called this a hard gate for months. It has never run on the `gh` path — the
# four issues created that way on 2026-08-22 carry correct labels only because a human passed
# them. These tests assert it now fires, and just as importantly that it stays out of the way
# where the taxonomy does not apply.
#
# Run: bash .claude/hooks/tests/label-taxonomy-check.test.sh

set -u

HOOKS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HOOK="$HOOKS_DIR/label-taxonomy-check.sh"
PASS=0
FAIL=0

SANDBOX="$(mktemp -d)"
trap 'rm -rf "$SANDBOX"' EXIT

# A sandbox checkout whose origin is a TRACKED repo, for the "no --repo flag" case.
TRACKED="$SANDBOX/homelab"
mkdir -p "$TRACKED"
git -C "$TRACKED" init -q -b main
git -C "$TRACKED" remote add origin https://github.com/fredabood/homelab.git

# ...and one whose origin is NOT tracked.
UNTRACKED="$SANDBOX/dotclaude"
mkdir -p "$UNTRACKED"
git -C "$UNTRACKED" init -q -b main
git -C "$UNTRACKED" remote add origin https://github.com/fredabood/.claude.git

ok() { PASS=$((PASS + 1)); echo "  ok: $1"; }
no() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; [ -n "${2:-}" ] && echo "        $2"; }

bash_payload() { # $1 command, $2 cwd
  python3 -c 'import json,sys; print(json.dumps({"tool_name":"Bash","cwd":sys.argv[2],"tool_input":{"command":sys.argv[1]}}))' "$1" "${2:-$TRACKED}"
}
mcp_payload() { # $1 json for tool_input
  python3 -c 'import json,sys; print(json.dumps({"tool_name":"mcp__github__issue_write","tool_input":json.loads(sys.argv[1])}))' "$1"
}

expect_bash() { # $1 command, $2 rc, $3 label, [$4 cwd]
  local rc
  printf '%s' "$(bash_payload "$1" "${4:-$TRACKED}")" | bash "$HOOK" >/dev/null 2>&1; rc=$?
  if [ "$rc" = "$2" ]; then ok "$3"; else no "$3" "expected rc=$2, got rc=$rc"; fi
}

C="gh issue create"

echo "== gh issue create is now gated in tracked repos =="

expect_bash "$C --repo fredabood/homelab --title x --body y" 2 \
  "create with NO labels is refused"
expect_bash "$C --repo fredabood/homelab --title x -l platform" 2 \
  "create with only a work pattern is refused"
expect_bash "$C --repo fredabood/homelab --title x -l L3-framework" 2 \
  "create with only a layer is refused"
expect_bash "$C --repo fredabood/homelab --title x -l platform -l migration -l L3-framework" 2 \
  "two work patterns are refused"
expect_bash "$C --repo fredabood/homelab --title x -l platform -l L1-platform -l L3-framework" 2 \
  "two layers are refused"

echo "== ...and allowed when the taxonomy is satisfied =="

expect_bash "$C --repo fredabood/homelab --title x -l platform -l L3-framework" 0 \
  "one pattern + one layer is allowed"
expect_bash "$C --repo fredabood/homelab --title x --label platform,L3-framework" 0 \
  "comma-separated form is allowed"
expect_bash "$C --repo fredabood/dirtydata --title x -l agent -l L4-domain --label source:rentcast" 0 \
  "an extra source: label does not upset it"
expect_bash "$C --title x -l platform -l L3-framework" 0 \
  "no --repo: origin resolved from cwd, and it validates"

echo "== repo scoping: the taxonomy does not exist everywhere =="

expect_bash "$C --repo fredabood/.claude --title x --body y" 0 \
  "create in fredabood/.claude is NOT gated"
expect_bash "$C --repo fredabood/work --title x --body y" 0 \
  "create in fredabood/work is NOT gated"
expect_bash "$C --title x --body y" 0 \
  "no --repo in an untracked checkout is NOT gated" "$UNTRACKED"
expect_bash "$C --title x --body y" 0 \
  "unresolvable repo is NOT gated (parse miss must not block)" "$SANDBOX"

echo "== control cases: everything else on the Bash path is untouched =="

expect_bash "gh issue edit 1425 --add-label platform" 0 \
  "gh issue edit is not validated (--add-label has ADD semantics)"
expect_bash "gh issue comment 1425 --body hi" 0 "gh issue comment untouched"
expect_bash "gh issue close 1425" 0 "gh issue close untouched"
expect_bash "gh pr create --title x --base main" 0 "gh pr create untouched"
expect_bash "gh issue list --repo fredabood/homelab" 0 "reads untouched"
expect_bash "git commit -m x" 0 "non-gh commands untouched"

echo "== the MCP path is unchanged =="

printf '%s' "$(mcp_payload '{"method":"create","labels":[]}')" | bash "$HOOK" >/dev/null 2>&1
[ $? = 2 ] && ok "MCP create with no labels still blocked" || no "MCP create with no labels still blocked"
printf '%s' "$(mcp_payload '{"method":"create","labels":["platform","L3-framework"]}')" | bash "$HOOK" >/dev/null 2>&1
[ $? = 0 ] && ok "MCP create with valid labels still allowed" || no "MCP create with valid labels still allowed"
printf '%s' "$(mcp_payload '{"method":"update","issue_number":1425}')" | bash "$HOOK" >/dev/null 2>&1
[ $? = 0 ] && ok "MCP update without labels still allowed" || no "MCP update without labels still allowed"
printf '%s' "$(mcp_payload '{"method":"update","issue_number":1425,"labels":["platform"]}')" | bash "$HOOK" >/dev/null 2>&1
[ $? = 2 ] && ok "MCP update with invalid labels still blocked" || no "MCP update with invalid labels still blocked"

echo "== both paths share ONE validator =="
# The gh path synthesizes an MCP payload rather than reimplementing the rules, so the two
# must agree exactly. Same label set, same verdict, both ways.
mcp_create_payload() { # $@ = label names
  python3 -c 'import json,sys; print(json.dumps({"tool_name":"mcp__github__issue_write","tool_input":{"method":"create","labels":sys.argv[1:]}}))' "$@"
}

for set_ in "platform L3-framework:0" "platform:2" "L3-framework:2" ":2"; do
  labels="${set_%%:*}"; want="${set_##*:}"
  flags=""
  for l in $labels; do flags="$flags -l $l"; done
  printf '%s' "$(bash_payload "$C --repo fredabood/homelab --title x$flags")" | bash "$HOOK" >/dev/null 2>&1
  gh_rc=$?
  # Deliberate word splitting: labels is a space-separated list of label names.
  # shellcheck disable=SC2086
  printf '%s' "$(mcp_create_payload $labels)" | bash "$HOOK" >/dev/null 2>&1
  mcp_rc=$?
  if [ "$gh_rc" = "$want" ] && [ "$mcp_rc" = "$want" ]; then
    ok "gh and MCP agree on [${labels:-<none>}] -> rc=$want"
  else
    no "gh and MCP agree on [${labels:-<none>}]" "gh=$gh_rc mcp=$mcp_rc want=$want"
  fi
done

echo
echo "label-taxonomy-check tests: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
