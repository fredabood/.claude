#!/usr/bin/env bash
# PreToolUse hook: validates taxonomy labels on Jira ticket create/edit.
# Hard gate: blocks createJiraIssue/editJiraIssue when taxonomy labels are missing.
# Exit 2 = block (labels missing or invalid), Exit 0 = allow (labels valid or non-label edit).
#
# Intercepts:
#   mcp__claude_ai_Atlassian__createJiraIssue
#   mcp__claude_ai_Atlassian__editJiraIssue
#
# Exit codes:
#   0 = allow (labels valid, or edit doesn't touch labels)
#   2 = block (taxonomy labels missing or invalid)

set -euo pipefail

INPUT=$(cat)

echo "$INPUT" | python3 -c "
import sys, json

try:
    data = json.load(sys.stdin)
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

tool_input = data.get('tool_input', {})

# Extract labels from create payload (fields.labels) or edit payload (update.labels)
fields = tool_input.get('fields', {})
labels = fields.get('labels', [])

if not labels:
    update = tool_input.get('update', {})
    if update:
        label_ops = update.get('labels', [])
        labels = [op.get('add', '') for op in label_ops if isinstance(op, dict) and 'add' in op]

# No labels in payload — edit doesn't touch labels, allow silently
if 'labels' not in fields and not labels:
    sys.exit(0)

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
    print('Add the required labels to proceed.')
    sys.exit(2)

sys.exit(0)
" || exit $?
