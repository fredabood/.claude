#!/usr/bin/env bash
# worktree-gate.sh — PreToolUse worktree-entry gate for fredabood/homelab (LAB-1364).
#
# WHY THIS EXISTS
#   Claude Code already enforces worktree isolation at the kernel level ONCE A SESSION IS
#   INSIDE a worktree (edits to the main checkout, Bash cwd, git redirects, unverifiable
#   command shapes — four checks, none disableable). It does NOT force a session launched in
#   the primary checkout INTO a worktree. That gap is what let concurrent sessions share one
#   HEAD and stack commits onto each other's branches (PR #1355, the rescue/* branches).
#
# WHY IT IS INSTALLED AT USER LEVEL
#   .claude is a git submodule. A fresh worktree checks out the gitlink but does not populate
#   it, so the worktree's .claude/ is EMPTY and zero project hooks fire. A gate registered in
#   the repo's .claude/settings.json would vanish exactly when a session enters a worktree.
#   It therefore lives in ~/.claude/settings.json and self-scopes by origin remote.
#
# THE HONEST GUARANTEE
#   No un-worktreed change reaches main. NOT "no un-worktreed byte can exist in a tree".
#   An agent with a shell can defeat any command-parsing gate; the merge gate (#1370) is the
#   second ring that makes the guarantee hold anyway. Do not chase parser completeness here.
#
# FAIL CLOSED: exit 2 blocks the tool call; stderr names what was blocked and the remedy.
# Parses the STDIN JSON payload (never an env var).

set -u

GATE_NAME="worktree-gate"

command -v jq >/dev/null 2>&1 || {
  echo "[$GATE_NAME] jq is required but not found — gate fails closed. Install jq." >&2
  exit 2
}

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/worktree-facts.sh"
# shellcheck source=lib/worktree-facts.sh
. "$LIB" 2>/dev/null || {
  echo "[$GATE_NAME] cannot source lib/worktree-facts.sh — gate fails closed." >&2
  exit 2
}

PAYLOAD="$(cat)"
TOOL="$(printf '%s' "$PAYLOAD" | jq -r '.tool_name // empty' 2>/dev/null)" || TOOL=""
CWD="$(printf '%s' "$PAYLOAD" | jq -r '.cwd // empty' 2>/dev/null)" || CWD=""

block() {
  echo "[$GATE_NAME] BLOCKED: $1" >&2
  echo "" >&2
  echo "This SESSION is in the primary checkout (${PRIMARY:-unknown})." >&2
  echo "It is a deploy mirror pinned to main: its Caddyfile and stack files are" >&2
  echo "bind-mounted into running containers, and its HEAD is shared by every" >&2
  echo "concurrent session." >&2
  echo "" >&2
  echo "Remedy — move the session into a worktree, then retry:" >&2
  echo "  * ask to work in a worktree (EnterWorktree), or" >&2
  echo "  * relaunch: claude --worktree <KEY>-<slug>" >&2
  echo "" >&2
  echo "Reads, git pull/status/log/diff, docker, and anything outside the repo stay allowed here." >&2
  exit 2
}

# A target under .claude/worktrees/<x> is physically inside the primary checkout but
# belongs to a different working tree. Blocking is correct — the session must MOVE there,
# not reach in from outside, or it never gets Claude Code's own isolation checks. But the
# generic message ("editing X in the primary checkout") reads as wrong when X is plainly a
# worktree file, so that case gets its own remedy.
block_nested_worktree() {
  local target_wt="$1" fp="$2"
  echo "[$GATE_NAME] BLOCKED: $fp belongs to the worktree $target_wt," >&2
  echo "but this SESSION is in the primary checkout, so it is reaching in from outside." >&2
  echo "" >&2
  echo "A session that edits a worktree by path never gets Claude Code's own isolation" >&2
  echo "checks — it only looks isolated. Move into it instead:" >&2
  echo "  EnterWorktree with path: $target_wt" >&2
  exit 2
}

# Verb matching must ignore quoted strings — a commit MESSAGE mentioning "git merge" is not
# a merge. Strips "..." and '...' spans; verb greps run on the stripped text.
strip_quotes() { printf '%s' "$1" | sed -e 's/"[^"]*"//g' -e "s/'[^']*'//g"; }

# ------------------------------------------------- anti-self-tamper (always) ---
# Checked BEFORE the mode short-circuit: the installed gate lives in ~/.claude, which is
# outside any repo, so a mode check would have already exited 0 and let it through.
# Only the edit TOOLS are blocked — the installer writes these paths via Bash by design.
GATE_HOME="$HOME/.claude"
case "$TOOL" in
  Edit | Write | MultiEdit | NotebookEdit)
    FP="$(printf '%s' "$PAYLOAD" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' 2>/dev/null)"
    if [ -n "$FP" ]; then
      ABS="$(wf_abspath "$FP" "${CWD:-$PWD}")"
      case "$ABS" in
        "$GATE_HOME"/settings.json | "$GATE_HOME"/hooks/worktree-gate.sh | \
          "$GATE_HOME"/hooks/session-bootstrap.sh | "$GATE_HOME"/hooks/lib/*)
          echo "[$GATE_NAME] BLOCKED: $FP is the installed gate itself." >&2
          echo "Edit the canonical copy in the repo (.claude/hooks/) from a worktree and" >&2
          echo "re-run internal/scripts/install-claude-user-hooks.sh." >&2
          exit 2
          ;;
      esac
    fi
    ;;
esac

# ------------------------------------------------------------- kill switch ---
# Agent-proof by construction: a PreToolUse hook is spawned by Claude Code with Claude
# Code's OWN environment, before the agent's command runs. A `VAR=x cmd` prefix inside an
# agent Bash call cannot reach the hook deciding on that very call. So this is reachable
# by the human at launch (HOMELAB_WORKTREE_GATE=off claude) and not by the model.
if [ "${HOMELAB_WORKTREE_GATE:-}" = "off" ]; then
  echo "[$GATE_NAME] DISABLED via HOMELAB_WORKTREE_GATE=off — worktree isolation is NOT enforced." >&2
  exit 0
fi

# --------------------------------------------------------------------- mode ---
[ -n "$CWD" ] || {
  echo "[$GATE_NAME] payload carried no cwd — gate fails closed (mode would be a guess)." >&2
  exit 2
}

MODE="$(wf_mode "$CWD")"
case "$MODE" in
  OUT_OF_REPO | OUT_OF_SCOPE | WORKTREE) exit 0 ;;
  UNRESOLVABLE)
    echo "[$GATE_NAME] cwd is inside a git repo but git could not resolve it — fails closed." >&2
    exit 2
    ;;
  PRIMARY) : ;;
  *)
    echo "[$GATE_NAME] unknown mode '$MODE' — fails closed." >&2
    exit 2
    ;;
esac

PRIMARY="$(wf_repo_root "$CWD")"

# ===================================================== PRIMARY CHECKOUT ONLY ===

case "$TOOL" in

  Edit | Write | MultiEdit | NotebookEdit)
    FP="$(printf '%s' "$PAYLOAD" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' 2>/dev/null)"
    [ -n "$FP" ] || exit 0
    ABS="$(wf_abspath "$FP" "$CWD")"
    wf_is_scratch "$ABS" && exit 0
    if wf_path_inside "$ABS" "$PRIMARY"; then
      TARGET_DIR="$(dirname "$ABS")"
      if [ -d "$TARGET_DIR" ] && wf_is_worktree "$TARGET_DIR"; then
        block_nested_worktree "$(wf_repo_root "$TARGET_DIR")" "$FP"
      fi
      block "editing $FP in the primary checkout."
    fi
    exit 0
    ;;

  Bash)
    CMD="$(printf '%s' "$PAYLOAD" | jq -r '.tool_input.command // empty' 2>/dev/null)"
    [ -n "$CMD" ] || exit 0
    CODE="$(strip_quotes "$CMD")"

    # --- git verbs that move HEAD or write history -----------------------------
    # Explicit allowlist-by-omission: pull/fetch/status/log/diff/show/worktree add|list
    # are absent from this pattern and therefore pass. The [^;|&]* idiom scopes the match
    # to one shell command segment, so `git status; echo commit` is not a commit.
    if printf '%s' "$CODE" |
      grep -qE '\bgit[^;|&]*\b(commit|merge|rebase|reset|cherry-pick|stash|push|am|apply|revert)\b'; then
      block "a history-moving git command in the primary checkout."
    fi
    # Branch switching moves the shared HEAD — the exact failure this gate exists to stop.
    if printf '%s' "$CODE" | grep -qE '\bgit[^;|&]*\b(checkout|switch)\b'; then
      # `git checkout -- <path>` and `git checkout <sha> -- <path>` restore files without
      # moving HEAD; they are how a deploy mirror recovers a clobbered bind-mounted config.
      printf '%s' "$CODE" | grep -qE '\bgit[^;|&]*\b(checkout|switch)\b[^;|&]*--[[:space:]]' ||
        block "git checkout/switch moves the shared HEAD for every concurrent session."
    fi

    # --- file-mutating shell verbs --------------------------------------------
    # Redirect pattern excludes fd-dups ([^&]) so `2>&1` and `>&2` never trip it.
    if printf '%s' "$CODE" | grep -qE '>[[:space:]]*[^&[:space:]]|\btee\b|\bsed[^;|&]*-i\b|\brm\b|\bmv\b|\bcp\b|\btruncate\b|\bdd\b'; then
      # Collect candidate targets: redirect operands plus every non-flag token.
      TARGETS="$(printf '%s' "$CODE" |
        tr '|;&' '\n' |
        sed -e 's/^[[:space:]]*//' |
        grep -oE '>>?[[:space:]]*[^[:space:]]+|[^[:space:]]+' |
        sed -e 's/^>>*[[:space:]]*//' |
        grep -vE '^-' || true)"
      VERDICT=allow
      SAW_PATH=no
      for t in $TARGETS; do
        case "$t" in
          # skip the verbs themselves and obvious non-paths
          rm | mv | cp | tee | sed | dd | truncate | echo | cat | printf | git | docker | sudo | env | bash | sh | then | do | fi | done) continue ;;
          *=*) continue ;;
        esac
        # A token carrying an unexpanded variable or glob cannot be resolved statically.
        case "$t" in
          *'$'* | *'`'* | *'*'* | *'?'*)
            SAW_PATH=yes
            VERDICT=block
            break
            ;;
        esac
        case "$t" in
          */* | .* | *.*)
            SAW_PATH=yes
            ABS="$(wf_abspath "$t" "$CWD")"
            wf_is_scratch "$ABS" && continue
            if wf_path_inside "$ABS" "$PRIMARY"; then
              VERDICT=block
              break
            fi
            ;;
        esac
      done
      # No resolvable path at all: relative operands default to cwd, which IS the repo.
      [ "$SAW_PATH" = no ] && VERDICT=block
      [ "$VERDICT" = block ] &&
        block "a file-mutating shell command whose target resolves inside the primary checkout (or could not be resolved statically)."
    fi

    exit 0
    ;;
esac

exit 0
