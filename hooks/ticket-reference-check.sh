#!/usr/bin/env bash
# PreToolUse hook: blocks commits without a work item reference.
# Accepted keys: HL-<n> (homelab), DD-<n> (dirtydata), plus historical
# LAB-<n> / DRTY-<n> / LEGACY-<n> for migrated issues.
# Checks both commit message and branch name.
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

# Check for work item reference pattern (mirror keys + migrated historical keys)
ticket_re = re.compile(r'\b(HL|DD|LAB|DRTY|LEGACY)-[0-9]+\b')
commit_has_ref = bool(ticket_re.search(msg)) if msg else False
branch_has_ref = bool(ticket_re.search(branch)) if branch else False

if not commit_has_ref and not branch_has_ref:
    print('BLOCKED: No work item reference found in commit message or branch name.')
    print()
    print(f'  Commit message: no reference (expected pattern: HL-123 / DD-45, or historical LAB-/DRTY-/LEGACY-)')
    print(f'  Branch name: \"{branch}\" — no reference')
    print()
    print('To fix:')
    print('  - Include the mirror key in the commit message: HL-123: <description> (homelab) or DD-45: <description> (dirtydata)')
    print('  - Historical keys stay valid when touching migrated issues: LAB-123: / DRTY-45: / LEGACY-7:')
    print('  - Or use an allowlisted prefix: chore: / typo: / docs: / sync:')
    print('  - Or create a tracking issue with /create-ticket')
    sys.exit(2)

if not commit_has_ref and branch_has_ref:
    print(f'NOTE: Commit message does not include a work item reference.')
    print(f'  Branch \"{branch}\" has a reference, but prefer including it in the commit message too.')
    print(f'  Format: HL-123: <description>')

sys.exit(0)
"
