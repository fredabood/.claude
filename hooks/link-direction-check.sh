#!/usr/bin/env bash
# Dependency (Blocks) link direction validation hook.
# Fires before Bash calls; only inspects `gh api .../dependencies/blocked_by` creates.
#
# GitHub dependency convention (see CLAUDE.md Section 5):
#   POST repos/<owner>/<repo>/issues/<BLOCKED#>/dependencies/blocked_by
#        -F issue_id=<BLOCKER database id>
#   i.e. the BLOCKED issue's endpoint receives the BLOCKER's DATABASE id
#   (get it with: gh api repos/<owner>/<repo>/issues/<BLOCKER#> --jq .id).
#
# Exit codes:
#   0 = allow (non-dependency command, or direction looks correct — advisory log)
#   2 = block (arguments look reversed or malformed: issue_id is an issue NUMBER,
#       or equals the endpoint's own issue number)

set -euo pipefail

INPUT=$(cat)

echo "$INPUT" | python3 -c "
import sys, json, re

try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)

cmd = d.get('tool_input', {}).get('command', '')

# Only inspect gh api calls that touch the dependencies/blocked_by endpoint
if 'gh api' not in cmd or 'dependencies/blocked_by' not in cmd:
    sys.exit(0)

# Reads (GET / no issue_id field) are always fine; DELETE removes a link
has_field = re.search(r'(?:-F|-f|--field|--raw-field)[ =]+[\"\\']?issue_id=', cmd)
is_delete = re.search(r'-X[ =]+[\"\\']?DELETE', cmd, re.IGNORECASE)
if not has_field or is_delete:
    sys.exit(0)

m_path = re.search(r'repos/([^/\s]+)/([^/\s]+)/issues/(\d+)/dependencies/blocked_by', cmd)
m_id = re.search(r'issue_id=(\d+)', cmd)

if not m_path or not m_id:
    # Can't parse — advisory only
    print('LINK DIRECTION CHECK: could not parse blocked_by call — verify direction manually '
          '(endpoint = BLOCKED issue, issue_id = BLOCKER database id).', file=sys.stderr)
    sys.exit(0)

owner, repo, blocked_num = m_path.group(1), m_path.group(2), int(m_path.group(3))
issue_id = int(m_id.group(1))

def explain():
    print()
    print('Expected direction: the BLOCKED issue declares its BLOCKER —')
    print(f'  gh api -X POST repos/{owner}/{repo}/issues/<BLOCKED#>/dependencies/blocked_by \\\\')
    print('    -H \"X-GitHub-Api-Version: 2026-03-10\" -F issue_id=<BLOCKER database id>')
    print(f'Get the blocker database id: gh api repos/{owner}/{repo}/issues/<BLOCKER#> --jq .id')

if issue_id == blocked_num:
    print(f'LINK DIRECTION ERROR: issue_id={issue_id} equals the endpoint issue number '
          f'#{blocked_num}. This is either a self-dependency or a reversed call — you may be '
          f'POSTing to the BLOCKER\'s endpoint while passing the BLOCKED issue\'s number.')
    explain()
    sys.exit(2)

# GitHub issue DATABASE ids are large (10-digit) globals; repo issue NUMBERS are small.
# A small issue_id almost certainly means an issue number was passed instead of a database id.
if issue_id < 1000000:
    print(f'LINK DIRECTION ERROR: issue_id={issue_id} looks like an issue NUMBER, not a '
          f'database id. The API requires the BLOCKER\'s database id, and the endpoint must '
          f'be the BLOCKED issue — passing the blocked issue\'s id while POSTing to the '
          f'blocker\'s endpoint silently reverses the dependency.')
    explain()
    sys.exit(2)

# Direction looks plausible — log for review (advisory)
print(f'LINK DIRECTION CHECK: {repo}#{blocked_num} (endpoint = BLOCKED) will be blocked by '
      f'database id {issue_id} (issue_id = BLOCKER).', file=sys.stderr)
sys.exit(0)
" || exit $?
