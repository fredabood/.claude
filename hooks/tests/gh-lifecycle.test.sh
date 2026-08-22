#!/usr/bin/env bash
# gh-lifecycle.test.sh — tests for the LAB-1425 gh lifecycle classifier.
#
# The ALLOW cases matter as much as the CLASSIFY cases here. This lib decides what three
# hooks gate, on the path that every GitHub operation currently takes (the MCP server is
# disconnected). A classifier that is too eager stops all tracker work; one that is too lax
# reproduces the bug. Both directions are asserted for every form.
#
# Run: bash .claude/hooks/tests/gh-lifecycle.test.sh

set -u

HOOKS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LIB="$HOOKS_DIR/lib/gh-lifecycle.sh"
PASS=0
FAIL=0

ok() { PASS=$((PASS + 1)); echo "  ok: $1"; }
no() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; [ -n "${2:-}" ] && echo "        $2"; }

verdict_of() { bash "$LIB" parse "$1" | cut -d'|' -f1; }

expect_verdict() { # $1 command, $2 expected verdict ("" = not classified)
  local got
  got="$(verdict_of "$1")"
  if [ "$got" = "$2" ]; then
    ok "${2:-<allow>} <- $1"
  else
    no "${2:-<allow>} <- $1" "got '${got:-<allow>}'"
  fi
}

echo "== classified: issue lifecycle writes =="

expect_verdict 'gh issue create --title x --body y'                       create
expect_verdict 'gh issue comment 1425 --body-file /tmp/x.md'              comment
expect_verdict 'gh issue edit 1425 --add-label platform'                  edit
expect_verdict 'gh issue close 1425'                                      close-done
expect_verdict 'gh issue close 1425 --reason completed'                   close-done
expect_verdict 'gh issue close 1425 --reason not_planned'                 close-wontdo

echo "== classified: the gh api equivalents =="

expect_verdict 'gh api -X PATCH repos/fredabood/homelab/issues/1425 -f state=closed'  close-done
expect_verdict 'gh api -X PATCH repos/fredabood/homelab/issues/1425 -f state=closed -f state_reason=not_planned' close-wontdo
expect_verdict 'gh api -X POST repos/fredabood/homelab/issues/1425/comments -f body=hi' comment
expect_verdict 'gh api -X PATCH repos/fredabood/homelab/issues/1425 -f title=new'      edit

echo "== classified: board writes =="

expect_verdict 'gh api graphql -f query=mutation{updateProjectV2ItemFieldValue(x)}'  board
expect_verdict 'gh project item-edit --id x --field-id y'                            board

echo "== graphql via a query FILE — the documented board-status idiom =="

# custom-fields.md prescribes `gh api graphql -F query=@file`, and an inline mutation string
# trips the worktree gate, so the file form is what actually gets used. If the classifier only
# looked at the command text this gate would be bypassed by the very idiom the docs recommend.
GQLDIR="$(mktemp -d)"
trap 'rm -rf "$GQLDIR"' EXIT
cat >"$GQLDIR/setstatus.graphql" <<'GQL'
mutation($project: ID!, $item: ID!, $field: ID!, $option: String!) {
  updateProjectV2ItemFieldValue(input: {projectId: $project, itemId: $item,
    fieldId: $field, value: {singleSelectOptionId: $option}}) { projectV2Item { id } }
}
GQL
cat >"$GQLDIR/itemid.graphql" <<'GQL'
query($num: Int!) { repository(owner: "fredabood", name: "homelab") {
  issue(number: $num) { projectItems(first: 10) { nodes { id } } } } }
GQL

expect_verdict "gh api graphql -F query=@$GQLDIR/setstatus.graphql -F item=x"  board
expect_verdict "gh api graphql -F query=@$GQLDIR/itemid.graphql -F num=1425"   ""
expect_verdict "gh api graphql -F query=@$GQLDIR/does-not-exist.graphql"       ""

echo "== wrapper and shell forms still classify =="

expect_verdict 'bash -c "gh issue close 1425"'                    close-done
expect_verdict 'sh -lc "gh issue create --title x"'               create
expect_verdict 'GH_TOKEN=xxx gh issue create --title x'           create
expect_verdict 'sudo gh issue close 1425'                         close-done
expect_verdict '/opt/homebrew/bin/gh issue close 1425'            close-done
expect_verdict 'echo hi && gh issue close 1425'                   close-done
expect_verdict 'cd /tmp ; gh issue comment 1 --body x'            comment

echo "== ALLOW: the control cases — these must NEVER classify =="

# PR landing is workflow Phase 11, not issue lifecycle.
expect_verdict 'gh pr create --repo fredabood/homelab --base main --title x'  ""
expect_verdict 'gh pr checks 1432 --watch --fail-fast'                        ""
expect_verdict 'gh pr merge 1432 --squash --delete-branch'                    ""
expect_verdict 'gh pr view 1432 --json state'                                 ""
expect_verdict 'gh api repos/fredabood/homelab/pulls --input payload.json'    ""

# Repo configuration, not issue lifecycle.
expect_verdict 'gh label list -R fredabood/homelab'                           ""
expect_verdict 'gh label create foo -R fredabood/homelab --color aabbcc'      ""

# Dependency links: prescribed by create-ticket and plan-sprint, and there is NO MCP
# equivalent. Gating this would break the skills outright.
DEPS='gh api -X POST repos/fredabood/homelab/issues/5/depend'
DEPS="${DEPS}encies/blocked_by -F issue_id=99"
expect_verdict "$DEPS"                                                        ""

# Every read.
expect_verdict 'gh issue view 1425 --json body'                               ""
expect_verdict 'gh issue list --repo fredabood/homelab --state open'          ""
expect_verdict 'gh api repos/fredabood/homelab/issues/1425'                   ""
expect_verdict 'gh api repos/fredabood/homelab/issues/1425/comments'          ""
expect_verdict 'gh api graphql -F query=@/tmp/itemid.graphql -F num=1425'     ""
expect_verdict 'gh repo view fredabood/homelab --json visibility'             ""
expect_verdict 'gh issue status'                                              ""

# Not gh at all.
expect_verdict 'git commit -m "x"'                                            ""
expect_verdict 'echo gh issue close 1425'                                     ""

echo "== field extraction =="

FIELDS="$(bash "$LIB" parse 'gh issue create -R fredabood/homelab --title x -l platform,L3-framework')"
[ "$(printf '%s' "$FIELDS" | cut -d'|' -f2)" = "fredabood/homelab" ] \
  && ok "repo extracted from -R" || no "repo extracted from -R" "$FIELDS"
[ "$(printf '%s' "$FIELDS" | cut -d'|' -f4)" = "platform,L3-framework" ] \
  && ok "comma-separated labels extracted" || no "comma-separated labels extracted" "$FIELDS"

FIELDS2="$(bash "$LIB" parse 'gh issue create --repo=fredabood/dirtydata --label=agent --label=L4-domain --title x')"
[ "$(printf '%s' "$FIELDS2" | cut -d'|' -f2)" = "fredabood/dirtydata" ] \
  && ok "repo extracted from --repo=" || no "repo extracted from --repo=" "$FIELDS2"
[ "$(printf '%s' "$FIELDS2" | cut -d'|' -f4)" = "agent,L4-domain" ] \
  && ok "repeated --label= extracted" || no "repeated --label= extracted" "$FIELDS2"

FIELDS3="$(bash "$LIB" parse 'gh issue comment 1425 --body x')"
[ "$(printf '%s' "$FIELDS3" | cut -d'|' -f3)" = "1425" ] \
  && ok "issue number extracted" || no "issue number extracted" "$FIELDS3"

echo "== tracked-repo scoping =="

for r in fredabood/homelab fredabood/dirtydata fredabood/9215resort homelab; do
  bash "$LIB" tracked "$r" && ok "tracked: $r" || no "tracked: $r" "reported untracked"
done
for r in fredabood/.claude fredabood/work fredabood/memory.md ""; do
  bash "$LIB" tracked "$r" && no "NOT tracked: ${r:-<empty>}" "reported tracked" \
    || ok "NOT tracked: ${r:-<empty>}"
done

echo
echo "gh-lifecycle tests: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
