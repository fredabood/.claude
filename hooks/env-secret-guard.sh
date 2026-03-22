#!/usr/bin/env bash
# PreToolUse hook: blocks direct reads of .env (plaintext secrets).
# Directs to 1Password CLI or /1password skill instead.
#
# Allows: .env.tpl, .env.example, .env.staging, docker compose --env-file,
#         op inject, inject-secrets.sh, git operations
# Blocks: cat/head/tail/grep/source/sed/awk on .env, Read tool on .env
#
# Exit codes:
#   0 = allow
#   2 = block (Claude Code surfaces the message to the user)

set -euo pipefail

INPUT=$(cat)

# Parse input and determine action — all logic in python for robustness
echo "$INPUT" | python3 -c "
import sys, json, re, os

try:
    data = json.load(sys.stdin)
except (json.JSONDecodeError, ValueError):
    # Malformed input — allow gracefully
    sys.exit(0)

cmd = data.get('tool_input', {}).get('command', '')
file_path = data.get('tool_input', {}).get('file_path', '')

def block(reason=''):
    print('BLOCKED: Direct read of .env detected.' + (f' ({reason})' if reason else ''))
    print()
    print('.env contains plaintext secrets and should not be read directly.')
    print('Use 1Password CLI instead:')
    print()
    print('  Look up a secret:  OP_BIOMETRIC_UNLOCK_ENABLED=true op item get \"<name>\" --vault Homelab --fields password')
    print('  List all secrets:  OP_BIOMETRIC_UNLOCK_ENABLED=true op item list --vault Homelab')
    print('  Inject .env:       ./internal/scripts/inject-secrets.sh')
    print('  Or use:            /1password')
    sys.exit(2)

# --- Handle Read tool ---
if file_path:
    basename = os.path.basename(file_path)
    if basename == '.env':
        block('Read tool')
    # Any other .env.* file is fine
    sys.exit(0)

# --- Handle Bash tool ---
if not cmd:
    sys.exit(0)

# Allowlist: commands that legitimately reference .env
allow_patterns = [
    r'docker compose.*--env-file',
    r'op inject',
    r'inject-secrets\.sh',
    r'\.env\.(tpl|example|staging|age|encrypted|backup|bak)',
    r'git (add|diff|status|log|show|check-ignore)',
    r'\bls\b',
    r'\bwc\b',
    r'\bdiff\b',
]

for pattern in allow_patterns:
    if re.search(pattern, cmd):
        sys.exit(0)

# Blocklist: direct reads of .env (but NOT .env.tpl, .env.example, etc.)
# \.env(?!\.\w) matches .env but not .env.tpl/.env.example via negative lookahead
block_patterns = [
    (r'\bcat\b.*\.env(?!\.\w)', 'cat'),
    (r'\bhead\b.*\.env(?!\.\w)', 'head'),
    (r'\btail\b.*\.env(?!\.\w)', 'tail'),
    (r'\bless\b.*\.env(?!\.\w)', 'less'),
    (r'\bmore\b.*\.env(?!\.\w)', 'more'),
    (r'\bgrep\b.*\.env(?!\.\w)', 'grep'),
    (r'\bsource\b.*\.env(?!\.\w)', 'source'),
    (r'^\.\s+.*\.env(?!\.\w)', 'dot-source'),
    (r'\bsed\b.*\.env(?!\.\w)', 'sed'),
    (r'\bawk\b.*\.env(?!\.\w)', 'awk'),
]

for pattern, label in block_patterns:
    if re.search(pattern, cmd):
        block(label)

# Default: allow
sys.exit(0)
" || exit $?
