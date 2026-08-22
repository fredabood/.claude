#!/usr/bin/env bash
# gh-lifecycle.sh — classify a Bash command as a GitHub ISSUE LIFECYCLE operation (LAB-1425).
#
# Three hooks — github-skill-gate.sh, label-taxonomy-check.sh, lifecycle-field-check.sh — were
# registered ONLY on `mcp__github__*` tool matchers, so every one of them was bypassed by the
# `gh` CLI. With the GitHub MCP server disconnected, `gh` is the path everything takes. During
# the LAB-966 audit, 34 issues were closed through it with no gate involvement at all.
#
# This lib answers one question for all three: "what lifecycle operation, if any, is this?"
#
# DELIBERATE DUPLICATION: workflow-gate.sh:115-193 keeps its own inlined copy of the same
# shlex matcher (LAB-1366). Rewriting a working discipline gate to DRY it is how that issue's
# over-block rounds started. If you change the lexing here, consider whether that copy needs
# the same change — but do not merge them casually.
#
# THIS IS A DISCIPLINE GATE FOR A COOPERATIVE AGENT, NOT AN ADVERSARIAL BOUNDARY. It uses a
# real lexer and unwraps `bash -c`, but it does not chase every wrapper form. Known and
# accepted gaps, inherited from LAB-1366:
#   * `xargs`, `timeout`, `nice` are not wrapper-stripped
#   * operators must be whitespace-separated (`a;gh issue close 1` reads as one token)
#   * no command-substitution unwrapping — `$(gh issue close 1)` is inert
#   * GraphQL closes (`mutation{closeIssue…}`) are invisible
# The hardened parser for the security-critical surface is worktree-gate.sh (LAB-1380).
#
# Bash 3.2-compatible (macOS ships 3.2.57).

set -u

# Repos where the work taxonomy exists. Creating an issue in fredabood/.claude or
# fredabood/work must NOT demand labels that do not exist there.
GH_LIFECYCLE_TRACKED_REPOS="${GH_LIFECYCLE_TRACKED_REPOS:-homelab dirtydata 9215resort}"

# gh_lifecycle_parse <command>
#
# Prints ONE line: verdict|repo|issue|labels
#   verdict : create | comment | edit | close-done | close-wontdo | board | (empty)
#   repo    : value of --repo/-R if given, else empty
#   issue   : first bare numeric argument after the subcommand, else empty
#   labels  : comma-separated --label/-l values, else empty
#
# The command is passed through the CMD ENVIRONMENT VARIABLE, never interpolated into the
# python source. That is load-bearing: the command is attacker-adjacent text.
gh_lifecycle_parse() {
  CMD="$1" python3 -c '
import os, shlex, sys

cmd = os.environ.get("CMD", "")

def lex(s):
    try:
        return shlex.split(s)
    except ValueError:
        return s.split()

WRAPPERS = {"sudo", "env", "command", "exec", "time", "nohup", "setsid", "stdbuf"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
WRITE_FLAGS = ("-X", "--method")
WRITE_VERBS = ("POST", "PATCH", "PUT", "DELETE")

def segments(tokens):
    seg, out = [], []
    for t in tokens:
        if t in (";", "&&", "||", "|", "&"):
            if seg:
                out.append(seg)
            seg = []
        else:
            seg.append(t)
    if seg:
        out.append(seg)
    return out

def strip_prefix(seg):
    i = 0
    while i < len(seg):
        t = seg[i]
        if "=" in t and not t.startswith("-") and t.split("=", 1)[0].isidentifier():
            i += 1
        elif os.path.basename(t) in WRAPPERS:
            i += 1
        else:
            break
    return seg[i:]

def opt_value(seg, names):
    """--repo x | --repo=x | -R x, repeatable; returns list of values."""
    out, i = [], 0
    while i < len(seg):
        t = seg[i]
        for n in names:
            if t == n and i + 1 < len(seg):
                out.append(seg[i + 1]); i += 1; break
            if t.startswith(n + "="):
                out.append(t.split("=", 1)[1]); break
        i += 1
    return out

def first_number(seg):
    for t in seg:
        if t.isdigit():
            return t
    return ""

def is_api_write(rest):
    joined = " ".join(rest)
    for f in WRITE_FLAGS:
        for v in WRITE_VERBS:
            if f + " " + v in joined or f + "=" + v in joined:
                return True
    # gh api POSTs implicitly when fields or a body are supplied.
    for t in rest:
        if t in ("-f", "-F", "--field", "--raw-field", "--input"):
            return True
    return False

def classify(seg):
    """Returns (verdict, repo, issue, labels) for ONE already-stripped segment."""
    head = os.path.basename(seg[0])
    if head != "gh":
        return None
    rest = seg[1:]
    if not rest:
        return None
    repo = (opt_value(rest, ["--repo", "-R"]) or [""])[0]
    labels = ",".join(
        l.strip()
        for group in opt_value(rest, ["--label", "-l"])
        for l in group.split(",")
        if l.strip()
    )
    sub = rest[0]

    # --- never classified: the allow-list -------------------------------------
    # gh pr *   — PR landing is workflow Phase 11, not issue lifecycle
    # gh label * — repo configuration, not issue lifecycle
    if sub in ("pr", "label", "repo", "release", "workflow", "run", "auth", "browse"):
        return None

    if sub == "issue":
        verb = rest[1] if len(rest) > 1 else ""
        num = first_number(rest[2:] if len(rest) > 2 else [])
        joined = " ".join(rest)
        if verb == "create":
            return ("create", repo, "", labels)
        if verb == "comment":
            return ("comment", repo, num, labels)
        if verb == "edit":
            return ("edit", repo, num, labels)
        if verb == "close":
            kind = "close-wontdo" if "not_planned" in joined else "close-done"
            return (kind, repo, num, labels)
        # view / list / develop / reopen / status — reads or out of scope
        return None

    if sub == "project":
        # gh project item-edit … is a board write
        verb = rest[1] if len(rest) > 1 else ""
        if verb.startswith("item-") or verb in ("field-create", "edit"):
            return ("board", repo, "", labels)
        return None

    if sub == "api":
        joined = " ".join(rest)
        # Dependency links have NO MCP equivalent — the skills prescribe this exact form
        # (create-ticket, plan-sprint). Never gate it. Scoped the way link-direction-check.sh
        # scopes itself.
        if "/dependencies/" in joined or "dependencies%2F" in joined:
            return None
        if "/pulls" in joined or "pulls%2F" in joined:
            return None
        if "graphql" in joined:
            # The mutation name is often NOT in the command: `-F query=@file.graphql` is the
            # documented board-status form (custom-fields.md), and an inline mutation string
            # trips the worktree gate. So resolve @file references and read them, or this
            # gate is bypassed by the very idiom the docs prescribe.
            hay = joined
            for t in rest:
                ref = ""
                if t.startswith("query=@"):
                    ref = t[len("query=@"):]
                elif t.startswith("-F") and "query=@" in t:
                    ref = t.split("query=@", 1)[1]
                if not ref:
                    continue
                try:
                    if os.path.isfile(ref) and os.path.getsize(ref) <= 100_000:
                        with open(ref, "r", errors="replace") as fh:
                            hay += " " + fh.read()
                except OSError:
                    pass
            if "updateProjectV2ItemFieldValue" in hay:
                return ("board", repo, "", labels)
            return None
        if not is_api_write(rest):
            return None
        touches_issue = "issues/" in joined or "issues%2F" in joined
        if "/comments" in joined and touches_issue:
            return ("comment", repo, "", labels)
        if "state=closed" in joined and touches_issue:
            kind = "close-wontdo" if "not_planned" in joined else "close-done"
            return (kind, repo, "", labels)
        if touches_issue:
            return ("edit", repo, "", labels)
        return None

    return None

def verdict(command, depth=0):
    if depth > 3:
        return None
    for seg in segments(lex(command)):
        seg = strip_prefix(seg)
        if not seg:
            continue
        head = os.path.basename(seg[0])
        if head in SHELLS:
            for j, tok in enumerate(seg[1:], start=1):
                if tok.startswith("-") and "c" in tok.lstrip("-") and j + 1 < len(seg):
                    v = verdict(seg[j + 1], depth + 1)
                    if v:
                        return v
                    break
            continue
        r = classify(seg)
        if r:
            return r
    return None

r = verdict(cmd)
print("|".join(r) if r else "|||")
' 2>/dev/null || echo "|||"
}

# gh_lifecycle_repo_tracked <repo>
# True when the repo carries the work taxonomy. Accepts "owner/name" or a bare name.
# An EMPTY repo means "not specified" — the caller decides; do not assume tracked.
gh_lifecycle_repo_tracked() {
  local repo="${1:-}" name
  [ -n "$repo" ] || return 1
  name="${repo##*/}"
  case " $GH_LIFECYCLE_TRACKED_REPOS " in
    *" $name "*) return 0 ;;
  esac
  return 1
}

# Direct invocation for the test suite and for debugging:
#   gh-lifecycle.sh parse '<command>'
if [ "${BASH_SOURCE[0]:-$0}" = "$0" ]; then
  case "${1:-}" in
    parse) gh_lifecycle_parse "${2:-}" ;;
    tracked) gh_lifecycle_repo_tracked "${2:-}" ;;
    *) echo "usage: gh-lifecycle.sh {parse <command>|tracked <repo>}" >&2; exit 64 ;;
  esac
fi
