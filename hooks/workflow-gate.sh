#!/usr/bin/env bash
# PreToolUse hook: enforces workflow phase gates.
# Reads .workflow-state.json to determine which phases are complete.
# No state file = no active workflow = allow everything.
#
# Gates:
#   Edit/Write on code files              → blocked until Phase 3 (Plan) complete
#   Bash(git commit)                      → blocked until Phase 4 (Worktree Setup) complete
#   issue_write close (state_reason:completed = Done) → blocked until Phases 6+7 complete
#   Bash(gh issue close / gh api state=closed)        → same gate, via the CLI (LAB-1366)
#   (closing as not_planned = Won't Do is not gated on either path)
#
# On the CLI gate: until LAB-1366 the close gate matched the GitHub MCP tool ONLY, so
# `gh issue close` walked straight past Phases 6+7 — and while the MCP server is
# disconnected that is the path EVERY close takes. This is a DISCIPLINE gate for a
# cooperative agent, not an adversarial boundary: it uses a real lexer (shlex) and
# unwraps `bash -c` payloads, but it does not chase every wrapper form. The hardened
# parser for the security-critical surface is worktree-gate.sh (LAB-1380).

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
      echo "WORKFLOW GATE: Phase 4 (Worktree Setup) is not complete."
      echo "Enter a worktree for this work item before committing —"
      echo "ask to work in a worktree (EnterWorktree), or relaunch:"
      echo "  claude --worktree <KEY>-<slug>"
      echo ""
      echo "To proceed: complete Phase 4 in /workflow, or delete .workflow-state.json to deactivate."
      exit 2
    fi
  fi

  # --- Gate: closing an issue as Done via the gh CLI (LAB-1366) ---
  # Mirrors the mcp__github__issue_write gate below. Won't Do (--reason not_planned)
  # stays ungated, exactly as on the MCP path.
  CLOSE_KIND=$(CMD="$CMD" python3 -c "
import os, shlex, sys

cmd = os.environ.get('CMD', '')

def lex(s):
    try:
        return shlex.split(s)
    except ValueError:
        return s.split()

WRAPPERS = {'sudo', 'env', 'command', 'exec', 'time', 'nohup', 'setsid', 'stdbuf'}
SHELLS = {'bash', 'sh', 'zsh', 'dash', 'ksh'}

def segments(tokens):
    seg, out = [], []
    for t in tokens:
        if t in (';', '&&', '||', '|', '&'):
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
        if '=' in t and not t.startswith('-') and t.split('=', 1)[0].isidentifier():
            i += 1
        elif os.path.basename(t) in WRAPPERS:
            i += 1
        else:
            break
    return seg[i:]

def verdict(command, depth=0):
    if depth > 3:
        return ''
    for seg in segments(lex(command)):
        seg = strip_prefix(seg)
        if not seg:
            continue
        head = os.path.basename(seg[0])
        # Unwrap a shell -c payload and re-scan it.
        if head in SHELLS:
            for j, tok in enumerate(seg[1:], start=1):
                if tok.startswith('-') and 'c' in tok.lstrip('-') and j + 1 < len(seg):
                    v = verdict(seg[j + 1], depth + 1)
                    if v:
                        return v
                    break
            continue
        if head != 'gh':
            continue
        rest = seg[1:]
        closes = False
        if len(rest) >= 2 and rest[0] == 'issue' and rest[1] == 'close':
            closes = True
        elif rest and rest[0] == 'api':
            joined = ' '.join(rest)
            if 'state=closed' in joined and ('issues/' in joined or 'issues%2F' in joined):
                closes = True
        if not closes:
            continue
        joined = ' '.join(rest)
        if 'not_planned' in joined:
            return 'wont_do'
        return 'done'
    return ''

print(verdict(cmd))
" 2>/dev/null || echo "")

  if [[ "$CLOSE_KIND" == "done" ]]; then
    phase6=$(phase_done 6)
    phase7=$(phase_done 7)
    if [[ "$phase6" == "no" || "$phase7" == "no" ]]; then
      echo "WORKFLOW GATE: Cannot close the issue as completed (Done) via the gh CLI."
      echo "Complete these phases first:"
      if [[ "$phase6" == "no" ]]; then
        echo "  Phase 6 (Verification): Post verification report to work item"
      fi
      if [[ "$phase7" == "no" ]]; then
        echo "  Phase 7 (Completion): Post post-mortem to work item"
      fi
      echo ""
      echo "Closing as Won't Do (gh issue close --reason not_planned) is not gated."
      echo "To proceed: complete the required phases in /workflow, or delete .workflow-state.json to deactivate."
      exit 2
    fi
  fi
fi

# --- Gate: closing an issue as Done blocked until Phases 6+7 are complete ---
if [[ "$TOOL_NAME" == "mcp__github__issue_write" ]]; then
  CLOSE_KIND=$(echo "$TOOL_INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
state = d.get('state', '')
reason = d.get('state_reason', '')
if state == 'closed':
    # Won't Do (not_planned) is not gated; completed (or default) = Done
    print('wont_do' if reason == 'not_planned' else 'done')
else:
    print('')
" 2>/dev/null || echo "")

  if [[ "$CLOSE_KIND" == "done" ]]; then
    phase6=$(phase_done 6)
    phase7=$(phase_done 7)
    if [[ "$phase6" == "no" || "$phase7" == "no" ]]; then
      echo "WORKFLOW GATE: Cannot close the issue as completed (Done)."
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
