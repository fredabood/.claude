#!/usr/bin/env bash
# PreToolUse hook: validates taxonomy labels on GitHub issue create/update.
# Hard gate: blocks mcp__github__issue_write creates when taxonomy labels are missing.
# Exit 2 = block (labels missing or invalid), Exit 0 = allow (labels valid or non-label update).
#
# Intercepts:
#   mcp__github__issue_write   (method: create — labels required;
#                               method: update — validated only when labels are present)
#
# Exit codes:
#   0 = allow (labels valid, or update doesn't touch labels)
#   2 = block (taxonomy labels missing or invalid)

set -euo pipefail

INPUT=$(cat)

# --- the `gh` CLI path (LAB-1425) --------------------------------------------------------
# This hook was registered on mcp__github__issue_write only, so `gh issue create` never once
# ran it — including for #1417, #1420, #1421 and #1424, all created on 2026-08-22. They carry
# correct labels because a human passed them, not because this "hard gate" fired.
#
# Rather than write a second validator, the gh path SYNTHESIZES the MCP payload and falls
# through to the same python below. One implementation, so the two paths cannot drift.
#
# Scope, deliberately narrow:
#   * `create` only. `gh issue edit --add-label` is NOT validated: --add-label has ADD
#     semantics while the MCP `labels` field REPLACES, so requiring a complete pattern+layer
#     pair on an add would block the legitimate act of supplying a single missing label.
#     Creation is where taxonomy is established, and that is what is enforced.
#   * Tracked repos only. The taxonomy does not exist in fredabood/.claude or fredabood/work,
#     so demanding it there would be a constant, immediate over-block.
TOOL_NAME_RAW=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    print(json.load(sys.stdin).get('tool_name', '') or '')
except Exception:
    print('')
" 2>/dev/null || echo "")

if [ "$TOOL_NAME_RAW" = "Bash" ]; then
  . "$(dirname "$0")/lib/gh-lifecycle.sh"
  GH_CMD=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    print((json.load(sys.stdin).get('tool_input') or {}).get('command', '') or '')
except Exception:
    print('')
" 2>/dev/null || echo "")
  GH_CWD=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    print(json.load(sys.stdin).get('cwd', '') or '')
except Exception:
    print('')
" 2>/dev/null || echo "")

  [ -n "$GH_CMD" ] || exit 0
  GH_PARSED="$(gh_lifecycle_parse "$GH_CMD")"
  GH_VERDICT="$(printf '%s' "$GH_PARSED" | cut -d'|' -f1)"
  [ "$GH_VERDICT" = "create" ] || exit 0

  GH_REPO="$(printf '%s' "$GH_PARSED" | cut -d'|' -f2)"
  GH_LABELS="$(printf '%s' "$GH_PARSED" | cut -d'|' -f4)"

  # No --repo means gh infers it from the working directory; do the same rather than guess.
  if [ -z "$GH_REPO" ] && [ -n "$GH_CWD" ]; then
    GH_REPO="$(git -C "$GH_CWD" remote get-url origin 2>/dev/null || echo "")"
    GH_REPO="${GH_REPO%.git}"
  fi
  # Cannot resolve the repo at all: allow. A gate that blocks on a parse miss over-blocks,
  # and this is a taxonomy check, not a security boundary.
  gh_lifecycle_repo_tracked "$GH_REPO" || exit 0

  INPUT="$(LABELS="$GH_LABELS" python3 -c "
import json, os
labels = [l for l in os.environ.get('LABELS', '').split(',') if l]
print(json.dumps({'tool_name': 'mcp__github__issue_write',
                  'tool_input': {'method': 'create', 'labels': labels}}))
")"
fi

echo "$INPUT" | python3 -c "
import sys, json

try:
    data = json.load(sys.stdin)
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

tool_name = data.get('tool_name', '')
# Only gate the GitHub issue write tool (allow silently if invoked on anything else)
if tool_name and 'issue_write' not in tool_name:
    sys.exit(0)

tool_input = data.get('tool_input', {})
method = str(tool_input.get('method', '')).lower()
is_create = method == 'create' or (not method and not tool_input.get('issue_number'))

labels = tool_input.get('labels', []) or []

# No labels in payload — update doesn't touch labels, allow silently
if not labels and not is_create:
    sys.exit(0)

# For create: labels are required, block if missing
if not labels and is_create:
    print('[label-taxonomy-check] TAXONOMY ERROR: New issues require taxonomy labels.')
    print('Add exactly one work pattern + one infrastructure layer label to the labels array.')
    print('See .claude/rules/label-taxonomy.md for valid labels.')
    sys.exit(2)

# Normalize — handle both string and dict {'name': '...'} formats
label_values = []
for l in labels:
    if isinstance(l, dict):
        label_values.append(l.get('name', ''))
    elif isinstance(l, str):
        label_values.append(l)

WORK_PATTERNS = {'scraper', 'agent', 'workflow', 'deployment', 'pipeline', 'migration', 'platform'}
INFRA_LAYERS = {'L1-platform', 'L2-services', 'L3-framework', 'L4-domain'}

found_patterns = [l for l in label_values if l in WORK_PATTERNS]
found_layers = [l for l in label_values if l in INFRA_LAYERS]

warnings = []
if len(found_patterns) == 0:
    warnings.append('Missing work pattern label (one of: scraper, agent, workflow, deployment, pipeline, migration, platform)')
elif len(found_patterns) > 1:
    warnings.append(f'Multiple work pattern labels found: {found_patterns} — exactly one required')

if len(found_layers) == 0:
    warnings.append('Missing infrastructure layer label (one of: L1-platform, L2-services, L3-framework, L4-domain)')
elif len(found_layers) > 1:
    warnings.append(f'Multiple layer labels found: {found_layers} — exactly one required')

if warnings:
    print('TAXONOMY ERROR: Labels do not satisfy taxonomy requirements:')
    for w in warnings:
        print(f'  - {w}')
    print()
    print('See .claude/rules/label-taxonomy.md for taxonomy conventions.')
    print('Add the required labels to proceed (optional source:* labels are also allowed).')
    sys.exit(2)

sys.exit(0)
" || exit $?
