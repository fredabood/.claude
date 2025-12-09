# Roadmap Integrity Protection: Options Analysis Report

**Date:** 2025-11-25
**Context:** AI assistants (Claude, Cursor, Copilot, etc.) can bypass Vibey's roadmap safeguards by directly editing YAML files and using `git commit --no-verify` to skip validation hooks.

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Option 1: Disable --no-verify for AI](#option-1-disable---no-verify-for-ai)
3. [Option 2: Vibey-Specific Signing Mechanism](#option-2-vibey-specific-signing-mechanism)
4. [Option 3: Git's Integrated GPG/SSH Signing](#option-3-gits-integrated-gpgssh-signing)
5. [Option 4: Hook-Based Enforcement](#option-4-hook-based-enforcement)
6. [Option 5: Server-Side Enforcement](#option-5-server-side-enforcement)
7. [Option 6: CLI Manifest Tracking](#option-6-cli-manifest-tracking)
8. [Option 7: Git Submodule Architecture](#option-7-git-submodule-architecture)
9. [Option 8: SQLite Database Backend](#option-8-sqlite-database-backend)
10. [User Onboarding & Key Management](#user-onboarding--key-management)
11. [Comparison Matrix](#comparison-matrix)
12. [Recommended Architecture](#recommended-architecture)
13. [Implementation Roadmap](#implementation-roadmap)

---

## Problem Statement

### Current Vulnerability

```
Intended Flow:                    Actual AI Bypass:

User → vibey CLI → YAML           AI → Edit tool → YAML (direct)
         ↓                                 ↓
CLI records change                 No record created
         ↓                                 ↓
git commit                         git commit --no-verify
         ↓                                 ↓
Pre-commit hook validates          Hook skipped entirely
         ↓                                 ↓
✅ Verified change                 ❌ Unverified change committed
```

### Root Causes

1. **Direct file access**: AI tools have Edit/Write access to all files including `.vibey/roadmap/**/*.yaml`
2. **Hook bypass**: Git's `--no-verify` flag skips all client-side hooks
3. **No authentication**: No way to verify if changes came through CLI vs direct edit
4. **Platform diversity**: Solution must work across Claude, Cursor, Copilot, Goose, etc.

### Requirements for Solution

| Requirement | Description |
|-------------|-------------|
| Platform-agnostic | Must work regardless of which AI tool is used |
| Non-bypassable | AI should not be able to circumvent the protection |
| Team-friendly | Multiple developers must be able to collaborate |
| Auditable | Should be clear when violations occur |
| Low friction | Legitimate workflow should not be impeded |

---

## Option 1: Disable --no-verify for AI

### Description

Prevent AI tools from using the `--no-verify` flag while allowing human users to retain access.

### Sub-Options

#### 1A: Platform-Specific Hook Interception

Each AI platform has its own mechanism to intercept tool calls:

**Claude Code:**
```bash
# .claude/hooks/pre-tool-execution.sh
if [[ "$CLAUDE_TOOL" == "Bash" ]] && [[ "$CLAUDE_TOOL_INPUT" == *"--no-verify"* ]]; then
    echo "ERROR: --no-verify is not allowed"
    exit 1
fi
```

**Cursor:**
```json
// .cursor/settings.json
{ "blockedCommands": ["git commit*--no-verify*"] }
```

#### 1B: Git Wrapper Command

Create `vibey git commit` that doesn't expose `--no-verify`:

```bash
# All platforms instructed to use:
vibey git commit -m "message"  # No --no-verify option available
```

#### 1C: Environment Detection

Detect AI environment and reject `--no-verify`:

```bash
# In git wrapper or alias
if [[ -n "$AI_SESSION" ]] && [[ "$*" == *"--no-verify"* ]]; then
    echo "ERROR: --no-verify not allowed in AI sessions"
    exit 1
fi
```

### Pros

| Pro | Explanation |
|-----|-------------|
| Simple concept | Easy to understand |
| Low implementation effort | Just block a flag |
| No cryptography | No key management needed |

### Cons

| Con | Explanation |
|-----|-------------|
| Platform-specific | Each platform needs custom configuration |
| Bypassable | AI can modify/delete hook files in `.git/hooks/` |
| Incomplete | Doesn't verify changes went through CLI |
| Maintenance burden | Must update for each new AI platform |

### Gaps

- AI can still edit YAML directly; blocking `--no-verify` only forces hooks to run
- AI could potentially disable or modify the hook files themselves
- Doesn't provide cryptographic proof of change origin
- No server-side enforcement

### Verdict: Partial Solution

Useful as one layer but insufficient alone. Adds friction but doesn't prevent determined bypass.

---

## Option 2: Vibey-Specific Signing Mechanism

### Description

Implement custom cryptographic signing where CLI signs each change, and hooks verify signatures.

### Sub-Options

#### 2A: Symmetric Key (HMAC)

Single shared secret signs all changes:

```
~/.vibey/signing-key → HMAC-SHA256 → signature in manifest
```

#### 2B: Asymmetric Keys (Public/Private)

Each user has keypair; public keys registered in repo:

```
~/.vibey/private.key (secret)
.vibey/authorized-signers/alice.pub (in repo)
```

### Architecture

```
CLI Operation
     ↓
Sign change with private key
     ↓
Write YAML + append to manifest with signature
     ↓
git commit
     ↓
Pre-commit hook verifies signature against registered public keys
     ↓
✅ Valid signature → allow
❌ Invalid/missing → reject
```

### Manifest Structure

```yaml
# .vibey/signatures/manifest.yaml
signatures:
  - id: sig_20251125_160000
    timestamp: '2025-11-25T16:00:00Z'
    operation: complete
    target_id: task-001
    file: .vibey/roadmap/.../task.yaml
    content_hash: sha256:abc123...
    signer: alice
    signature: ecdsa:def456...
```

### Pros

| Pro | Explanation |
|-----|-------------|
| Platform-agnostic | Works regardless of AI tool |
| Cryptographically secure | AI cannot forge signatures |
| Fine-grained | Per-file/per-change tracking |
| Auditable | Clear record of who changed what |
| Offline verification | No server needed for local checks |

### Cons

| Con | Explanation |
|-----|-------------|
| Implementation complexity | ~24 hours to build |
| Key management | Must handle key generation, storage, rotation |
| User onboarding | Each user needs keypair setup |
| New system to learn | Not using existing standards |
| Bootstrap problem | First user / new user registration |

### Gaps

- Still relies on hooks for enforcement (bypassable locally)
- Requires server-side verification as final backstop
- Key storage location must be inaccessible to AI
- Doesn't integrate with existing Git tooling

### User Onboarding Implications

```bash
# New user flow
$ vibey auth setup
Generated keypair at ~/.vibey/

# Must be added by existing authorized user
$ vibey auth add-signer carol carol.pub  # Signed by existing user
```

**Problem:** New users cannot self-register. Requires existing user sponsorship.

### Verdict: Strong but Complex

Provides strong guarantees but introduces significant complexity and maintenance burden.

---

## Option 3: Git's Integrated GPG/SSH Signing

### Description

Leverage Git's built-in commit signing (`git commit -S`) with GPG or SSH keys.

### How It Works

```bash
# Developer setup (one-time)
git config --global commit.gpgsign true
git config --global user.signingkey <GPG_KEY_ID>

# Every commit is signed
git commit -m "message"  # Automatically signed with -S
```

### Verification

```bash
# Verify a commit
git verify-commit <commit-hash>

# Show signature in log
git log --show-signature
```

### Pros

| Pro | Explanation |
|-----|-------------|
| Battle-tested | GPG has decades of security review |
| Existing infrastructure | Many devs already have GPG keys |
| Server support | GitHub/GitLab support signature verification |
| No custom crypto | Using established standards |
| Low implementation | ~2 hours to add hooks |

### Cons

| Con | Explanation |
|-----|-------------|
| Per-commit, not per-file | Signs entire commit, not individual changes |
| Proves WHO, not HOW | Signature proves identity, not that CLI was used |
| GPG complexity | GPG setup can be confusing for new users |
| Key availability | If GPG agent unlocked, AI might sign commits |

### Critical Gap

**GPG signing does NOT verify that changes went through CLI:**

```
Scenario: GPG signing enabled, AI in human's session

1. AI edits YAML directly (no CLI)
2. AI runs: git commit -S -m "changes"
3. If GPG agent is unlocked → commit is signed!
4. Signature is valid but change was unauthorized
```

**GPG answers:** "Who made this commit?" (the key holder)
**GPG does NOT answer:** "How were these changes made?" (CLI vs direct edit)

### Verdict: Complementary but Insufficient

Adds authentication layer but doesn't solve the core problem of CLI bypass detection.

---

## Option 4: Hook-Based Enforcement

### Description

Use Git hooks at various stages to validate roadmap changes.

### Hook Types

#### 4A: Pre-Commit Hook

**When:** Before commit is created
**Can block:** Yes
**Bypassable:** Yes (`--no-verify`)

```bash
#!/bin/bash
# .git/hooks/pre-commit

staged_yaml=$(git diff --cached --name-only | grep '.vibey/roadmap.*\.yaml$')
if [[ -n "$staged_yaml" ]]; then
    for file in $staged_yaml; do
        if ! vibey verify-change "$file"; then
            echo "ERROR: Unauthorized roadmap change in $file"
            exit 1
        fi
    done
fi
```

#### 4B: Commit-Msg Hook

**When:** After commit message entered, before commit created
**Can block:** Yes
**Bypassable:** Yes (`--no-verify`)

```bash
#!/bin/bash
# .git/hooks/commit-msg

# Verify task reference in commit message
if git diff --cached --name-only | grep -q '.vibey/roadmap.*\.yaml$'; then
    if ! grep -qE 'Task: [a-z]+-[0-9]+-task-[0-9]+' "$1"; then
        echo "ERROR: Commits with roadmap changes require task reference"
        exit 1
    fi
fi
```

#### 4C: Post-Commit Hook

**When:** After commit created
**Can block:** No (commit already exists)
**Bypassable:** Yes (`--no-verify`)

```bash
#!/bin/bash
# .git/hooks/post-commit

# Audit logging - detect if pre-commit was bypassed
if [[ ! -f ".git/PRECOMMIT_RAN" ]]; then
    echo "$(date -Iseconds) BYPASS commit=$(git rev-parse HEAD)" >> .vibey/audit/bypass.log
fi
rm -f .git/PRECOMMIT_RAN
```

#### 4D: Pre-Push Hook

**When:** Before push to remote
**Can block:** Yes
**Bypassable:** Yes (delete hook file, but no `--no-verify` for push)

```bash
#!/bin/bash
# .git/hooks/pre-push

for commit in $(git rev-list @{u}..HEAD 2>/dev/null); do
    files=$(git diff-tree --no-commit-id --name-only -r $commit | grep '.vibey/roadmap.*\.yaml$')
    for file in $files; do
        if ! vibey verify-change --commit $commit "$file"; then
            echo "ERROR: Commit $commit has unauthorized roadmap changes"
            exit 1
        fi
    done
done
```

### Pros

| Pro | Explanation |
|-----|-------------|
| Native Git integration | Standard mechanism |
| Multiple enforcement points | Defense in depth |
| No external dependencies | Pure shell scripts |
| Immediate feedback | Blocks before bad commits spread |

### Cons

| Con | Explanation |
|-----|-------------|
| Client-side only | Can be bypassed locally |
| `--no-verify` bypass | Single flag defeats pre-commit/commit-msg |
| Hook deletion | AI could remove hook files |
| Not synchronized | Hooks live in `.git/`, not committed |

### Gaps

- All client-side hooks can be bypassed by sufficiently motivated actor
- Hook files are in `.git/hooks/`, which AI has access to
- No cryptographic verification of change origin
- Must be reinstalled on each clone (`vibey install-hooks`)

### Verdict: Necessary but Insufficient

Essential layer for immediate feedback but cannot be the sole enforcement mechanism.

---

## Option 5: Server-Side Enforcement

### Description

Enforce rules at the Git server level where AI has no access.

### Sub-Options

#### 5A: Branch Protection Rules (GitHub/GitLab)

```yaml
# GitHub branch protection
branches:
  main:
    protection:
      required_signatures: true
      required_status_checks:
        - "vibey/roadmap-integrity"
```

#### 5B: CI/CD Verification

```yaml
# .github/workflows/roadmap-integrity.yml
name: Roadmap Integrity Check
on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Install Vibey
        run: pip install vibey

      - name: Verify roadmap changes
        run: |
          vibey roadmap verify-commits ${{ github.event.before }}..${{ github.sha }}
```

#### 5C: Server-Side Hooks (Self-Hosted)

```bash
# On Git server: hooks/pre-receive
while read oldrev newrev refname; do
    for commit in $(git rev-list $oldrev..$newrev); do
        if ! vibey verify-commit $commit; then
            echo "ERROR: Unauthorized roadmap changes in $commit"
            exit 1
        fi
    done
done
```

### Pros

| Pro | Explanation |
|-----|-------------|
| Non-bypassable | AI cannot modify server configuration |
| Centralized | Single enforcement point |
| Works retroactively | Can verify after local bypass |
| Platform support | GitHub/GitLab have built-in features |

### Cons

| Con | Explanation |
|-----|-------------|
| Delayed feedback | Only caught at push/PR time |
| Requires server setup | Must configure CI or server hooks |
| External dependency | Relies on GitHub/GitLab availability |
| Self-hosted complexity | Server hooks require admin access |

### Gaps

- Bad commits exist locally until push fails
- Requires specific CI/CD setup
- May not be available for all Git hosting scenarios
- Doesn't help with local development workflow

### Verdict: Essential Final Layer

Must-have for true enforcement, but should be combined with local checks for faster feedback.

---

## Option 6: CLI Manifest Tracking

### Description

CLI records all changes it makes; hooks verify changes match manifest entries.

### How It Works

```
1. User runs: vibey roadmap complete task-001

2. CLI:
   - Loads current file content
   - Makes the change
   - Records in manifest:
     {
       timestamp: "2025-11-25T16:00:00Z",
       file: ".vibey/roadmap/.../task.yaml",
       operation: "complete",
       before_hash: "sha256:aaa...",
       after_hash: "sha256:bbb...",
       cli_command: "vibey roadmap complete task-001"
     }
   - Writes both file and manifest entry

3. Pre-commit hook:
   - For each staged YAML file
   - Check if manifest has matching entry with correct after_hash
   - If no match → reject
```

### Manifest Location

```
.vibey/
├── cli-changes.json       # Pending (uncommitted) changes
├── audit/
│   └── change-log.yaml    # Historical record
```

### Pros

| Pro | Explanation |
|-----|-------------|
| Answers the right question | Proves change went through CLI |
| Platform-agnostic | Works with any AI tool |
| No cryptography required | Hash comparison is sufficient |
| Simple concept | Easy to understand and debug |
| Already partially implemented | `.vibey/.cli-changes.json` exists |

### Cons

| Con | Explanation |
|-----|-------------|
| Manifest is editable | AI could add fake manifest entries |
| Race conditions | Multiple concurrent CLI operations |
| Storage growth | Manifest grows with each change |
| Verification dependency | Hooks must always check manifest |

### Critical Gap

**AI can forge manifest entries:**

```
1. AI edits YAML directly
2. AI also edits .vibey/cli-changes.json to add matching entry
3. Pre-commit hook sees "valid" manifest entry
4. Change appears legitimate but wasn't through CLI
```

**This is why cryptographic signing is needed** - to prove the manifest entry was created by authorized CLI, not by AI.

### Verdict: Necessary Foundation

Required component but needs cryptographic protection to prevent forgery.

---

## Option 7: Git Submodule Architecture

### Description

Make `.vibey/` a separate Git repository (submodule) with its own stricter access controls and signing requirements. The main repository only tracks a commit hash reference to the submodule.

### How It Works

```
main-repo/
├── .vibey/              ← Git submodule (separate repo)
│   └── roadmap/
├── src/                 ← Code (main repo)
└── .gitmodules          ← Submodule config pointing to .vibey repo
```

**Workflow:**

```
1. Developer makes roadmap change via CLI
2. CLI updates files in .vibey/ submodule
3. Developer commits to submodule: cd .vibey && git commit
4. Developer pushes submodule: git push (to submodule remote)
   ↓
   Submodule remote enforces:
   - Signed commits required
   - PR review required
   - Branch protection rules
   ↓
5. If push succeeds, update parent repo's submodule reference
6. Commit parent repo: git add .vibey && git commit
```

**Why this works against AI bypass:**

```
Current problem:
  AI → edits .vibey/*.yaml → git commit --no-verify → ✅ bypassed

With submodule:
  AI → edits .vibey/*.yaml → git commit --no-verify (submodule) → git push
                                                                      ↓
                                                         ❌ BLOCKED by submodule remote
                                                            (requires signed commits/PR)
```

The enforcement moves to the **submodule's remote server**, which AI cannot bypass locally.

### Pros

| Pro | Explanation |
|-----|-------------|
| Leverages existing Git infrastructure | No custom signing system needed |
| Server-side enforcement built-in | Submodule remote can require signed commits, PR approval |
| Clear audit trail | Submodule has its own git history |
| Different access controls possible | Submodule repo can have stricter permissions than main repo |
| Two-step commit = more friction | AI must commit to submodule AND update parent |
| Industry standard | Submodules are well-understood Git feature |

### Cons

| Con | Explanation |
|-----|-------------|
| Submodules are confusing | Notorious for UX issues (detached HEAD, sync problems) |
| Two-step commit process | Every roadmap change requires two commits |
| Clone complexity | Requires `git clone --recurse-submodules` |
| Merge conflicts in submodule refs | Can be confusing to resolve |
| Submodule sync issues | Easy to forget to push submodule before parent |
| Doesn't prevent local bypass | AI can still commit locally with --no-verify |

### Gaps

- Enforcement only happens at push time to submodule remote
- Local commits can still be made with `--no-verify`
- Adds significant workflow complexity for all users
- Submodule state can get out of sync with parent
- Requires separate repository infrastructure

### Mitigation Strategies

| Challenge | Mitigation |
|-----------|------------|
| UX complexity | `vibey commit` wrapper that handles both repos |
| Forgetting to push submodule | Pre-push hook on parent checks submodule is pushed |
| Clone issues | Document in README, add setup script |
| Detached HEAD | Pre-commit hook warns if submodule is detached |

### Verdict: Viable Alternative

Trades implementation complexity for UX complexity. Best suited for teams already comfortable with submodules who want to leverage existing Git server infrastructure rather than building custom signing.

---

## Option 8: SQLite Database Backend

### Description

Use a local SQLite database as the working state for roadmap operations. YAML files remain in Git for version control, but are only written during commits (dump from DB) and read during pulls (rebuild DB from YAML). The database file is in `.gitignore`.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Git Repository                       │
│  ┌─────────────────┐         ┌─────────────────────────┐    │
│  │ .vibey/roadmap/ │ ◄─────► │ .vibey/roadmap.db       │    │
│  │ *.yaml files    │  sync   │ (SQLite, in .gitignore) │    │
│  │ (versioned)     │         │ (working state)         │    │
│  └─────────────────┘         └─────────────────────────┘    │
│         ▲                              ▲                     │
│         │                              │                     │
│    git pull                      vibey CLI                   │
│    (rebuild DB)                  (all operations)            │
│    git commit                                                │
│    (dump DB → YAML)                                          │
└─────────────────────────────────────────────────────────────┘
```

### How It Works

```
git pull
    ↓
post-merge hook: vibey db rebuild (YAML → DB)
    ↓
User works: vibey roadmap start/complete/edit (DB operations only)
    ↓
git commit
    ↓
pre-commit hook: vibey db dump (DB → YAML)
    ↓
YAML files staged with current DB state
    ↓
commit proceeds
```

### Why This Could Work

**Scenario: AI edits YAML directly, then commits normally**
```
1. AI edits .vibey/roadmap/task.yaml directly
2. AI runs: git add . && git commit
3. Pre-commit hook runs: vibey db dump
4. DB state → OVERWRITES YAML files
5. AI's manual changes are GONE
6. Committed YAML reflects DB state (unchanged by AI)
```

The database becomes the **single source of truth** during work. YAML is just a serialization format for version control.

### Schema Example

```sql
CREATE TABLE tracks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    progress_json TEXT,
    metadata_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sprints (
    id TEXT PRIMARY KEY,
    track_id TEXT REFERENCES tracks(id),
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    progress_json TEXT,
    updated_at TIMESTAMP
);

CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    sprint_id TEXT REFERENCES sprints(id),
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    assigned_agent TEXT,
    priority TEXT,
    updated_at TIMESTAMP
);

-- Optional integrity checking
CREATE TABLE _checksums (
    table_name TEXT,
    record_id TEXT,
    checksum TEXT,  -- HMAC of record data
    PRIMARY KEY (table_name, record_id)
);
```

### Pros

| Pro | Explanation |
|-----|-------------|
| Natural bypass prevention | Manual YAML edits get overwritten on commit |
| Performance | SQLite queries vs YAML file parsing |
| ACID transactions | Atomic operations, rollback support |
| Complex queries | `SELECT * FROM tasks WHERE status='blocked'` trivial |
| Binary format | AI less likely to edit `.db` file directly |
| Recovery | DB corruption → rebuild from YAML |

### Cons

| Con | Explanation |
|-----|-------------|
| Doesn't solve --no-verify | AI can still bypass pre-commit hook |
| Silent data loss risk | If detection not implemented, changes silently discarded |
| Migration effort | Need to build DB schema, sync logic |
| Merge conflict handling | Must rebuild DB after YAML conflict resolution |
| AI could edit DB directly | `sqlite3 .vibey/roadmap.db "UPDATE..."` |

### Critical Limitation

**The `--no-verify` bypass still works:**

```
1. AI edits YAML directly
2. AI runs: git commit --no-verify
3. Pre-commit hook SKIPPED (no DB dump)
4. AI's YAML changes committed directly
5. Next git pull → DB rebuilt with AI's invalid changes!
```

The database approach provides a detection/overwrite mechanism, but doesn't prevent bypass when hooks are skipped.

### Enhanced Version: Detect and Reject

Instead of silent overwrite, detect mismatches and block:

```
git commit
    ↓
pre-commit hook:
    ↓
Compare YAML ↔ DB
    ↓
┌─────────────────────────────────────────────────────────────┐
│ YAML has changes not in DB?                                  │
│                                                              │
│ ❌ ERROR: YAML modified outside CLI                          │
│                                                              │
│ Changed files:                                               │
│   .vibey/roadmap/sprint-1/task-001/task.yaml                │
│                                                              │
│ Diff:                                                        │
│   - status: in_progress                                      │
│   + status: completed                                        │
│                                                              │
│ To track this change properly, run:                          │
│   vibey roadmap complete git-integration-5-task-001          │
│                                                              │
│ Commit aborted.                                              │
└─────────────────────────────────────────────────────────────┘
```

### Hybrid: Database + Checksums

Add integrity protection without full crypto:

```python
import hmac
import hashlib

SECRET_KEY = load_from_home_directory("~/.vibey/secret")  # Outside git

def write_record(db, table, record):
    checksum = hmac.new(SECRET_KEY, serialize(record), hashlib.sha256).hexdigest()
    db.execute(f"INSERT INTO {table} VALUES (?, ?)", (record, checksum))

def read_record(db, table, id):
    record, stored_checksum = db.execute(f"SELECT * FROM {table} WHERE id=?", (id,))
    expected = hmac.new(SECRET_KEY, serialize(record), hashlib.sha256).hexdigest()
    if stored_checksum != expected:
        raise IntegrityError(f"Record {id} was modified outside CLI")
    return record
```

This prevents AI from directly editing the database (it doesn't have the secret key).

### Verdict: Valuable for Performance, Insufficient for Security

The database approach provides:
- ✅ Significant performance benefits
- ✅ Powerful query capabilities
- ✅ Detection mechanism for YAML edits (when hooks run)
- ❌ Does NOT prevent `--no-verify` bypass
- ❌ Requires server-side enforcement as backstop

**Best used in combination with server-side CI verification (Option 5).**

---

## User Onboarding & Key Management

### Scenarios to Handle

| Scenario | Challenge | Solution |
|----------|-----------|----------|
| New repo | No existing signers | First user bootstrap |
| New team member | Can't self-authorize | Existing user sponsors |
| Key rotation | Old signatures still valid? | Timestamp-based validation |
| Lost key | User locked out | Admin recovery process |
| Compromised key | Attacker can sign | Revocation list |

### Onboarding Flow (Asymmetric Keys)

```
New Developer Carol:

1. Install Vibey                    $ pip install vibey

2. Generate keypair                 $ vibey auth setup
                                    Generated:
                                      ~/.vibey/private.key
                                      ~/.vibey/public.key

3. Send public key to admin         $ cat ~/.vibey/public.key
   (out of band: Slack, email)      -----BEGIN PUBLIC KEY-----
                                    ...

4. Admin adds Carol                 $ vibey auth add-signer carol carol.pub
   (admin's commit is signed)       ✅ Added carol to authorized signers

5. Carol can now sign               $ vibey roadmap complete task-001
                                    ✅ Signed with carol's key
```

### Onboarding Flow (GPG-Based)

```
New Developer Carol:

1. Generate GPG key                 $ gpg --gen-key
   (if not existing)

2. Configure Git                    $ git config user.signingkey <KEY_ID>
                                    $ git config commit.gpgsign true

3. Add to GitHub                    GitHub → Settings → SSH and GPG keys
                                    → Add GPG key

4. Done                             Commits are now signed
   (no Vibey-specific setup)
```

### Comparison

| Aspect | Vibey Custom Keys | GPG Keys |
|--------|-------------------|----------|
| Setup complexity | Medium | Medium-High |
| Existing tooling | None | gpg, GitHub, GitLab |
| Key storage | ~/.vibey/ | ~/.gnupg/ |
| Server verification | Must implement | Built into GitHub/GitLab |
| Revocation | Must implement | GPG revocation certificates |
| Team management | vibey auth commands | GitHub team settings |

---

## Comparison Matrix

### Effectiveness Against Attack Vectors

| Attack Vector | Opt 1 (Block flag) | Opt 2 (Signing) | Opt 3 (GPG) | Opt 4 (Hooks) | Opt 5 (Server) | Opt 6 (Manifest) | Opt 7 (Submodule) | Opt 8 (SQLite) |
|--------------|---------------------|-----------------|-------------|---------------|----------------|------------------|-------------------|----------------|
| AI direct YAML edit | ❌ No | ✅ Yes | ❌ No | ⚠️ Partial | ✅ Yes | ⚠️ Partial | ✅ Yes (at push) | ⚠️ Partial |
| AI uses --no-verify | ⚠️ Partial | ✅ Yes | ❌ No | ❌ No | ✅ Yes | ⚠️ Partial | ✅ Yes (at push) | ❌ No |
| AI modifies hooks | ❌ No | ⚠️ Partial | ❌ No | ❌ No | ✅ Yes | ❌ No | ✅ Yes | ❌ No |
| AI forges manifest | N/A | ✅ Yes | N/A | N/A | ✅ Yes | ❌ No | N/A | ⚠️ Partial |
| AI has GPG access | N/A | ✅ Yes | ❌ No | N/A | ⚠️ Partial | N/A | ⚠️ Partial | N/A |
| AI edits DB directly | N/A | N/A | N/A | N/A | N/A | N/A | N/A | ⚠️ (w/ checksum) |

### Implementation Characteristics

| Characteristic | Opt 1 | Opt 2 | Opt 3 | Opt 4 | Opt 5 | Opt 6 | Opt 7 | Opt 8 |
|---------------|-------|-------|-------|-------|-------|-------|-------|-------|
| Platform-agnostic | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Implementation effort | Low | High | Low | Medium | Medium | Medium | Medium | Medium-High |
| Maintenance burden | High | Medium | Low | Low | Low | Low | Medium | Medium |
| User friction | Low | Medium | Medium | Low | Low | Low | High | Low |
| Cryptographic strength | None | Strong | Strong | None | Varies | None | Varies | Optional |
| Requires server | No | No | Optional | No | Yes | No | Yes | No |
| Query performance | N/A | N/A | N/A | N/A | N/A | N/A | N/A | ✅ Excellent |
| Offline capability | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ |

### Summary by Approach

| Approach | Best For | Key Tradeoff |
|----------|----------|--------------|
| **Option 1: Block --no-verify** | Quick friction | Platform-specific, easily bypassed |
| **Option 2: Vibey Signing** | Strong guarantees | Complex implementation, key management |
| **Option 3: GPG Signing** | Identity verification | Doesn't prove CLI usage |
| **Option 4: Hooks** | Developer experience | Bypassable with --no-verify |
| **Option 5: Server CI** | Non-bypassable enforcement | Delayed feedback, requires server |
| **Option 6: Manifest** | Foundation layer | Can be forged without signing |
| **Option 7: Submodule** | Leverage existing Git infra | Poor UX, submodule complexity |
| **Option 8: SQLite** | Performance + queries | Doesn't solve --no-verify bypass |

---

## Recommended Architecture

### Defense in Depth

No single option is sufficient. Combine multiple layers:

```
Layer 1: CLI Manifest (Option 6)
    ↓ Records what changes went through CLI

Layer 2: Cryptographic Signing (Option 2 or 3)
    ↓ Proves manifest entries are authentic

Layer 3: Local Hooks (Option 4)
    ↓ Immediate feedback, catches honest mistakes

Layer 4: Server Enforcement (Option 5)
    ↓ Final non-bypassable verification
```

### Recommended Combination (Primary Path)

| Layer | Implementation | Purpose |
|-------|---------------|---------|
| **Foundation** | CLI manifest tracking | Record CLI operations |
| **Authentication** | GPG commit signing | Prove identity (leverage existing infrastructure) |
| **Integrity** | Manifest entry signing | Prove manifest not forged |
| **Local enforcement** | Pre-commit + pre-push hooks | Fast feedback |
| **Final enforcement** | GitHub Actions CI | Non-bypassable verification |

### Alternative Architectures

#### Alternative A: Submodule-Based (Option 7)

Best for teams comfortable with submodules who want simpler implementation:

```
Layer 1: .vibey/ as Git submodule
    ↓ Separate repository with own history

Layer 2: Submodule remote protection
    ↓ Require signed commits, PR review

Layer 3: Parent repo hooks
    ↓ Verify submodule is pushed before parent commit
```

**Tradeoff:** Simpler server-side enforcement, but worse developer experience.

#### Alternative B: Database + Server CI (Option 8 + Option 5)

Best for teams prioritizing performance and query capabilities:

```
Layer 1: SQLite database (working state)
    ↓ All CLI operations use DB

Layer 2: Pre-commit hook (DB → YAML dump)
    ↓ YAML reflects DB state, detects manual edits

Layer 3: Server CI verification
    ↓ Final enforcement (required because --no-verify bypasses hooks)
```

**Tradeoff:** Excellent performance, but still requires server-side enforcement.

### Minimum Viable Protection

If implementing everything is not feasible, prioritize:

1. **CLI Manifest** (already partially exists)
2. **Server-side CI verification** (non-bypassable)
3. **Pre-push hook** (catches before remote)

This provides:
- Record of CLI changes (manifest)
- Local warning (pre-push)
- Final enforcement (CI)

Without cryptographic signing, AI could forge manifest entries, but CI could use heuristics:
- Timestamp plausibility
- Change size limits
- Pattern detection

### Architecture Decision Matrix

| If you need... | Choose... |
|----------------|-----------|
| Strongest guarantees | Primary path (signing + server CI) |
| Simplest implementation | Submodule (Option 7) + server protection |
| Best performance | Database (Option 8) + server CI |
| Offline-first workflow | Signing (Option 2) without server dependency |
| Minimal changes | Manifest (Option 6) + hooks (Option 4) + server CI |

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1)

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | Audit existing cli-changes.json implementation | 2h |
| 1.2 | Standardize manifest format | 4h |
| 1.3 | Ensure all CLI write operations record to manifest | 8h |
| 1.4 | Add `vibey verify-change` command | 4h |

### Phase 2: Local Enforcement (Week 2)

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | Update pre-commit hook to verify manifest | 4h |
| 2.2 | Add pre-push hook with same verification | 4h |
| 2.3 | Add bypass detection (post-commit audit logging) | 2h |
| 2.4 | Documentation for hook installation | 2h |

### Phase 3: Server Enforcement (Week 2-3)

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | Create GitHub Actions workflow for verification | 4h |
| 3.2 | Create GitLab CI equivalent | 2h |
| 3.3 | Add `vibey verify-commits` command for CI | 4h |
| 3.4 | Documentation for CI setup | 2h |

### Phase 4: Cryptographic Signing (Week 3-4)

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | Design key management system | 4h |
| 4.2 | Implement key generation (`vibey auth setup`) | 4h |
| 4.3 | Implement signer registration (`vibey auth add-signer`) | 4h |
| 4.4 | Integrate signing into CLI manifest writes | 6h |
| 4.5 | Update verification to check signatures | 4h |
| 4.6 | Documentation for key management | 4h |

### Phase 5: Polish (Week 4)

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | Error messages and user guidance | 4h |
| 5.2 | Edge case handling (merge conflicts, rebases) | 8h |
| 5.3 | Performance optimization | 4h |
| 5.4 | Comprehensive testing | 8h |

### Total Estimated Effort

| Phase | Effort |
|-------|--------|
| Phase 1: Foundation | 18h |
| Phase 2: Local Enforcement | 12h |
| Phase 3: Server Enforcement | 12h |
| Phase 4: Cryptographic Signing | 26h |
| Phase 5: Polish | 24h |
| **Total** | **92h (~2.5 weeks FTE)** |

---

## Appendix: Decision Tree

```
Q: Do you need non-bypassable enforcement?
├─► Yes → Must implement server-side (Option 5)
│         │
│         Q: Do you need cryptographic proof?
│         ├─► Yes → Add signing (Option 2 or 3)
│         └─► No → Manifest + CI heuristics may suffice
│
└─► No (trust team, just want friction)
          → Hooks only (Option 4) + Manifest (Option 6)
```

---

## Conclusion

**The core insight:** No local mechanism can fully prevent bypass because AI has access to the local filesystem. Server-side enforcement is the only non-bypassable layer.

**Recommended approach:**
1. **Manifest tracking** as foundation (proves intent)
2. **Cryptographic signing** to prevent manifest forgery
3. **Server-side CI** as final enforcement
4. **Local hooks** for developer experience

**Minimum viable:** Manifest + Server CI + Pre-push hook

**Full protection:** All layers implemented with asymmetric key signing

---

*Report generated during roadmap integrity design session, 2025-11-25*
