#!/usr/bin/env bash
# Link direction validation hook.
# Fires before createIssueLink to log the direction and warn about potential reversals.
#
# For "Blocks" links, logs the direction for review.
# Jira API convention (empirically verified):
#   inwardIssue  = the blocker (shows "blocks" label when viewed)
#   outwardIssue = the blocked issue (shows "is blocked by" label when viewed)
#
# Exit codes:
#   0 = allow (always — this is advisory, not blocking)

set -euo pipefail

INPUT=$(cat)

# Extract fields from the tool input JSON
LINK_TYPE=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
inp = d.get('input', d)
# Handle both nested and flat structures
lt = inp.get('linkType', inp.get('type', ''))
if isinstance(lt, dict):
    lt = lt.get('name', '')
print(lt)
" 2>/dev/null || echo "")

# Only check Blocks links
if [[ "$LINK_TYPE" != "Blocks" ]]; then
  exit 0
fi

# Extract outward and inward issue keys
read -r OUTWARD INWARD <<< "$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
inp = d.get('input', d)
outward = inp.get('outwardIssue', {})
inward = inp.get('inwardIssue', {})
if isinstance(outward, dict):
    outward = outward.get('key', '')
if isinstance(inward, dict):
    inward = inward.get('key', '')
print(outward, inward)
" 2>/dev/null || echo " ")"

if [[ -z "$OUTWARD" || -z "$INWARD" ]]; then
  exit 0
fi

# Log the link direction clearly
echo "LINK DIRECTION CHECK: ${INWARD} (inward=blocker) blocks ${OUTWARD} (outward=blocked)" >&2

# Advisory: always allow, but log for review
exit 0
