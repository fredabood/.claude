#!/usr/bin/env bash
# PreToolUse hook: blocks commits without a work item reference.
# Checks both commit message and branch name for pattern [A-Z]+-[0-9]+.
# Allowlist: messages starting with chore:, typo:, docs:, sync: bypass the check.

set -euo pipefail

# Read tool input from stdin and do all logic in python
INPUT=$(cat)
BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

echo "$INPUT" | python3 -c "
import sys, json, re, shlex

data = json.load(sys.stdin)
cmd = data.get('tool_input', {}).get('command', '')
branch = '$BRANCH_NAME'

# Only run on git commit commands
if 'git commit' not in cmd:
    sys.exit(0)

# Extract commit message using shlex
msg = ''
try:
    parts = shlex.split(cmd)
    for i, part in enumerate(parts):
        if part == '-m' and i + 1 < len(parts):
            msg = parts[i + 1]
            break
except ValueError:
    pass

if not msg:
    # Fallback: heredoc pattern
    m = re.search(r'<<.*?EOF.*?\n(.*?)\n.*?EOF', cmd, re.DOTALL)
    if m:
        msg = m.group(1).strip().split('\n')[0]

# Check allowlist — trivial commits bypass
if re.match(r'^\s*(chore|typo|docs|sync):', msg, re.IGNORECASE):
    sys.exit(0)

# Check for work item reference pattern
ticket_re = re.compile(r'[A-Z]+-[0-9]+')
commit_has_ref = bool(ticket_re.search(msg)) if msg else False
branch_has_ref = bool(ticket_re.search(branch)) if branch else False

if not commit_has_ref and not branch_has_ref:
    print('BLOCKED: No work item reference found in commit message or branch name.')
    print()
    print(f'  Commit message: no reference (expected pattern: KEY-123)')
    print(f'  Branch name: \"{branch}\" — no reference')
    print()
    print('To fix:')
    print('  - Include a work item key in the commit message: LAB-123: <description>')
    print('  - Or use an allowlisted prefix: chore: / typo: / docs: / sync:')
    print('  - Or create a tracking ticket with /create-ticket')
    sys.exit(2)

if not commit_has_ref and branch_has_ref:
    print(f'NOTE: Commit message does not include a work item reference.')
    print(f'  Branch \"{branch}\" has a reference, but prefer including it in the commit message too.')
    print(f'  Format: KEY-123: <description>')

sys.exit(0)
"
