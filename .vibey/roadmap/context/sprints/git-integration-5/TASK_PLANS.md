# Sprint 5: Roadmap Integrity Protection - Task Plans

**Sprint ID:** git-integration-5
**Track:** Enhanced Git Integration
**Status:** Planning
**Created:** 2025-12-10
**Updated:** 2025-12-10 (Unified Activity Log Architecture)
**Integration Reference:** docs/roadmap/sqlite-backend/sqlite-backend-6/UNIFIED_TICKET_ARCHITECTURE.md

---

## Architecture Decision: Unified Activity Log

**Decision:** Merge manifest functionality INTO the activity log system.

**Key Changes:**
1. Activity log changes from **field-level** to **command-level** granularity
2. One CLI command = one activity log entry
3. Activity log entries include verification fields (hash, signature)
4. No separate manifest file needed

### New Activity Log Entry Format

```jsonl
{
  "id": "evt_01KC...",
  "timestamp": "2025-12-10T15:30:00.000000+00:00",
  "command": "vibey roadmap update task 01KC... --status completed --title 'New title'",
  "object_type": "task",
  "object_id": "01KC2D0JK7READW9KAK1HBX4B3",
  "changes": [
    {"field": "status", "old": "in_progress", "new": "completed"},
    {"field": "title", "old": "Old title", "new": "New title"}
  ],
  "file_path": ".vibey/roadmap/tasks/01KC2D0JK7READW9KAK1HBX4B3.yaml",
  "file_hash_before": "a1b2c3d4e5f6...",
  "file_hash_after": "f6e5d4c3b2a1...",
  "changed_by": "cli",
  "reason": null,
  "signature": null,
  "signer": null
}
```

### Comparison: Old vs New

| Aspect | Old (Field-Level) | New (Command-Level) |
|--------|-------------------|---------------------|
| Granularity | One entry per field | One entry per CLI command |
| `--status X --title Y` | 2 entries | 1 entry |
| Changes stored in | `field`, `old_value`, `new_value` | `changes[]` array |
| File verification | Not included | `file_hash_before/after` |
| Signing | Not included | `signature`, `signer` |
| Manifest | Separate system | **Integrated** |

### Benefits

1. **Single source of truth** - No separate manifest to maintain
2. **Atomic operations** - One command = one entry (intuitive)
3. **Natural 1:1 mapping** - Activity entry = verification entry
4. **Simpler verification** - Git hooks query activity log directly
5. **Field history preserved** - `changes[]` array still allows field queries

---

## Phase 0: Activity Log Refactor (Tasks 000A-000D)

**NEW PHASE** - Refactor existing activity log before adding verification features.

### Task 000A: Design command-level activity log schema
**Complexity:** Medium | **Estimate:** 3 hours

**Description:**
Design the new command-level activity log entry format that unifies audit logging with manifest verification.

**Implementation Steps:**
1. Define new `CommandActivityEvent` dataclass:
   ```python
   @dataclass
   class CommandActivityEvent:
       id: str                          # Unique event ID (ULID)
       timestamp: str                   # ISO8601
       command: str                     # Full CLI command
       object_type: str                 # track, sprint, task, roadmap
       object_id: str                   # ULID of modified object
       changes: List[FieldChange]       # Array of field changes
       file_path: str                   # Relative path to YAML
       file_hash_before: Optional[str]  # SHA256 before change
       file_hash_after: str             # SHA256 after change
       changed_by: str                  # "cli", "migration", etc.
       reason: Optional[str]            # User-provided reason
       signature: Optional[str]         # Ed25519 signature (Phase 4)
       signer: Optional[str]            # Signer identity

   @dataclass
   class FieldChange:
       field: str
       old: Any
       new: Any
   ```
2. Document migration path from old `ActivityEvent`
3. Design backward compatibility layer

**Acceptance Criteria:**
- [ ] New schema documented
- [ ] FieldChange nested type defined
- [ ] Migration strategy documented
- [ ] Backward compatibility approach defined

**Deliverables:**
- `ACTIVITY_LOG_V2_SCHEMA.md` in sprint context

---

### Task 000B: Refactor ActivityEvent to CommandActivityEvent
**Complexity:** High | **Estimate:** 6 hours
**Depends on:** Task 000A

**Description:**
Refactor `vibey/operations/roadmap/jsonl_activity_log.py` to use command-level granularity.

**Implementation Steps:**
1. Create new `CommandActivityEvent` dataclass
2. Create `FieldChange` dataclass
3. Update `ActivityLogWriter`:
   - New method: `log_command(command, object_type, object_id, changes, file_path, ...)`
   - Compute file hashes automatically
   - Generate event ID (ULID)
4. Update `ActivityLogReader`:
   - Parse new format
   - Add `get_changes_for_field()` method for field-level queries
5. Maintain backward compatibility:
   - Reader should handle both old and new formats
   - Old format entries returned with `changes: [single_change]`

**Acceptance Criteria:**
- [ ] `CommandActivityEvent` dataclass implemented
- [ ] Writer logs command-level entries
- [ ] Reader parses both old and new formats
- [ ] File hash computation integrated
- [ ] Unit tests updated

**Deliverables:**
- Updated `jsonl_activity_log.py`
- `FieldChange` dataclass

---

### Task 000C: Update CLI commands to use command-level logging
**Complexity:** High | **Estimate:** 8 hours
**Depends on:** Task 000B

**Description:**
Update all CLI commands to log single command-level entries instead of multiple field-level entries.

**Implementation Steps:**
1. Identify all CLI write operations in `vibey/cli/commands.py`
2. For each command:
   - Capture full command string
   - Collect all field changes into list
   - Compute file hash before change
   - Make change
   - Compute file hash after change
   - Log single `CommandActivityEvent`
3. Create helper decorator or context manager:
   ```python
   @log_command
   def update_task(task_id, status, title, ...):
       # Changes are automatically collected and logged
   ```
4. Update `AuditTrailManager` to use new format

**Acceptance Criteria:**
- [ ] All CLI write commands log command-level entries
- [ ] File hashes computed for each change
- [ ] Single entry per command (not per field)
- [ ] Integration tests pass

**Deliverables:**
- Updated CLI commands
- Command logging helper

---

### Task 000D: Migrate existing activity log entries
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 000C

**Description:**
Migrate existing field-level activity log entries to command-level format where possible.

**Implementation Steps:**
1. Analyze existing entries in `.vibey/roadmap/activity_log/`
2. Group consecutive entries by:
   - Same timestamp (within 1 second)
   - Same object_id
   - Same changed_by
3. Merge grouped entries into single command-level entries:
   ```python
   # Old (2 entries):
   {"field": "status", "old": "a", "new": "b", ...}
   {"field": "title", "old": "x", "new": "y", ...}

   # New (1 entry):
   {"changes": [{"field": "status", ...}, {"field": "title", ...}], ...}
   ```
4. Entries that can't be grouped stay as-is (single-change format)
5. Create backup before migration

**Acceptance Criteria:**
- [ ] Backup created before migration
- [ ] Consecutive entries merged where possible
- [ ] Standalone entries converted to new format
- [ ] Verification: entry count reduced, no data loss
- [ ] Reader still works with migrated data

**Deliverables:**
- Migration script
- Migrated activity log files

---

## Phase 1: Foundation (Tasks 001-004)

### Task 001: Audit existing tracking implementations
**File:** `01KC2D0JK7READW9KAK1HBX4B3.yaml`
**Complexity:** Low | **Estimate:** 2 hours

**Description:**
Review both the old `cli-changes.json` and the new command-level activity log. Document current state and identify remaining gaps for verification.

**Implementation Steps:**
1. Review `.vibey/cli-changes.json` (if still exists)
2. Review new command-level activity log format
3. Verify all CLI operations are being logged
4. Identify any gaps in coverage
5. Document verification requirements not yet met

**Acceptance Criteria:**
- [ ] Current logging coverage documented
- [ ] Gaps identified
- [ ] Verification requirements listed

**Deliverables:**
- `TRACKING_AUDIT.md` in sprint context

---

### Task 002: Add verification fields to activity log
**File:** `01KC2D0JK7READW9KAK1HBX4B4.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 001, Task 000B

**Description:**
Ensure activity log entries have all fields needed for verification. Design the `ActivityVerifiedTarget` criterion type.

**Implementation Steps:**
1. Verify schema includes:
   - `file_hash_before` / `file_hash_after` (SHA256)
   - `signature` (optional, for Phase 4)
   - `signer` (optional, for Phase 4)
2. Define `ActivityVerifiedTarget` criterion type:
   ```python
   class ActivityVerifiedTarget(CriterionTarget):
       """Criterion met when activity log verification succeeds."""
       target_id: str

       def is_satisfied(self) -> bool:
           return verify_activity_entry(self.target_id)
   ```
3. Document verification algorithm:
   - Find entry with `file_hash_after` matching current file
   - Verify entry exists
   - (Phase 4) Verify signature if present

**Acceptance Criteria:**
- [ ] All verification fields present in schema
- [ ] `ActivityVerifiedTarget` criterion type designed
- [ ] Verification algorithm documented

**Deliverables:**
- Schema verification
- `ActivityVerifiedTarget` specification

---

### Task 003: Implement verification logic
**File:** `01KC2D0JK7READW9KAK1HBX4B5.yaml`
**Complexity:** Medium | **Estimate:** 6 hours
**Depends on:** Task 002

**Description:**
Implement core verification logic that checks if a file change has a corresponding activity log entry.

**Implementation Steps:**
1. Create `vibey/operations/roadmap/verification.py`:
   ```python
   class ChangeVerifier:
       def __init__(self, activity_reader: ActivityLogReader):
           self.reader = activity_reader

       def verify_file(self, file_path: Path) -> VerificationResult:
           """Verify file has matching activity log entry."""
           current_hash = compute_file_hash(file_path)
           entry = self.reader.find_by_hash(current_hash)
           if not entry:
               return VerificationResult(False, "No matching activity log entry")
           return VerificationResult(True, f"Verified: {entry.id}")

       def verify_file_at_commit(self, file_path: Path, commit: str) -> VerificationResult:
           """Verify file state at specific commit."""
           # Get file content at commit
           # Find matching entry
   ```
2. Add `find_by_hash()` method to `ActivityLogReader`
3. Create hash index for efficient lookups
4. Handle edge cases: new files, deleted files

**Acceptance Criteria:**
- [ ] `ChangeVerifier` class implemented
- [ ] Hash-based lookup efficient
- [ ] Historical verification supported
- [ ] Edge cases handled
- [ ] Unit tests

**Deliverables:**
- `vibey/operations/roadmap/verification.py`
- Updated `ActivityLogReader`

---

### Task 004: Add vibey verify-change command
**File:** `01KC2D0JK7READW9KAK1HBX4B6.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 003

**Description:**
Create CLI command to verify if a file change was made through CLI.

**Implementation Steps:**
1. Implement `vibey verify-change <file>`:
   ```python
   @roadmap.command('verify-change')
   @click.argument('file_path')
   @click.option('--commit', help='Verify against specific commit')
   @click.option('--json', 'output_json', is_flag=True, help='JSON output')
   def verify_change(file_path: str, commit: Optional[str], output_json: bool):
       """Verify a file change was made through CLI."""
       verifier = ChangeVerifier(get_activity_reader())
       if commit:
           result = verifier.verify_file_at_commit(file_path, commit)
       else:
           result = verifier.verify_file(file_path)

       if output_json:
           click.echo(json.dumps(result.to_dict()))
       else:
           click.echo(result.message)

       sys.exit(0 if result.verified else 1)
   ```
2. Exit codes: 0=verified, 1=unverified, 2=error
3. Human-readable and JSON output modes

**Acceptance Criteria:**
- [ ] `vibey verify-change <file>` works
- [ ] `--commit` flag for historical verification
- [ ] `--json` flag for machine parsing
- [ ] Appropriate exit codes

**Deliverables:**
- `verify-change` command

---

## Phase 2: Local Enforcement (Tasks 005-008)

### Task 005: Update pre-commit hook for verification
**File:** `01KC2D0JK7READW9KAK1HBX4B7.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 004

**Description:**
Modify pre-commit hook to verify staged roadmap files against activity log.

**Implementation Steps:**
1. Update `vibey/operations/git/hooks/pre_commit.py`:
   ```python
   def verify_staged_roadmap_files():
       verifier = ChangeVerifier(get_activity_reader())
       staged = get_staged_files()
       roadmap_files = [f for f in staged if is_roadmap_file(f)]

       failures = []
       for file in roadmap_files:
           result = verifier.verify_file(file)
           if not result.verified:
               failures.append((file, result.message))

       if failures:
           for file, msg in failures:
               print(f"BLOCKED: {file} - {msg}")
           print("\nUse 'vibey roadmap' commands to make changes.")
           sys.exit(1)
   ```
2. Clear error messages with guidance
3. List all failed files before blocking

**Acceptance Criteria:**
- [ ] Hook verifies all staged roadmap files
- [ ] Clear error messages
- [ ] Guidance to use CLI
- [ ] All failures listed (not just first)

**Deliverables:**
- Updated pre-commit hook

---

### Task 006: Add pre-push hook
**File:** `01KC2D0JK7READW9KAK1HBX4B8.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 005

**Description:**
Create pre-push hook that verifies all commits being pushed.

**Implementation Steps:**
1. Create `vibey/operations/git/hooks/pre_push.py`
2. Get commit range being pushed
3. For each commit, verify all roadmap file changes
4. Block push if any verification fails
5. Clear error output with commit hashes

**Acceptance Criteria:**
- [ ] Pre-push hook implemented
- [ ] Verifies all commits in range
- [ ] Blocks on failure
- [ ] Shows which commits/files failed

**Deliverables:**
- `pre_push.py` hook

---

### Task 007: Add bypass detection
**File:** `01KC2D0JK7READW9KAK1HBX4B9.yaml`
**Complexity:** Low | **Estimate:** 2 hours
**Depends on:** Task 005

**Description:**
Detect when pre-commit hook was bypassed via `--no-verify`.

**Implementation Steps:**
1. Pre-commit creates marker: `.vibey/.pre-commit-ran`
2. Post-commit checks for marker
3. If missing + roadmap files changed = bypass detected
4. Log bypass to activity log with special event type:
   ```jsonl
   {
     "id": "evt_...",
     "timestamp": "...",
     "command": "BYPASS_DETECTED",
     "object_type": "system",
     "object_id": "pre-commit",
     "changes": [],
     "file_path": null,
     "file_hash_before": null,
     "file_hash_after": null,
     "changed_by": "git-hook",
     "reason": "Pre-commit hook bypassed",
     "commit": "abc123..."
   }
   ```

**Acceptance Criteria:**
- [ ] Bypass detection works
- [ ] Logged to activity log
- [ ] Includes commit hash

**Deliverables:**
- Post-commit hook
- Bypass event type

---

### Task 008: Hook documentation
**File:** `01KC2D0JK7READW9KAK1HBX4BA.yaml`
**Complexity:** Low | **Estimate:** 2 hours
**Depends on:** Task 007

**Description:**
Document git hook installation and usage.

**Implementation Steps:**
1. Update `vibey roadmap install-hooks` to install all hooks
2. Create `docs/guides/GIT_HOOKS.md`
3. Cover: pre-commit, commit-msg, post-commit, pre-push
4. Troubleshooting section

**Acceptance Criteria:**
- [ ] All hooks in install command
- [ ] Documentation complete
- [ ] Troubleshooting included

**Deliverables:**
- `docs/guides/GIT_HOOKS.md`

---

## Phase 3: Server Enforcement (Tasks 009-012)

### Task 009: GitHub Actions workflow
**File:** `01KC2D0JK7READW9KAK1HBX4BB.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 004

**Description:**
Create GitHub Actions workflow for server-side verification.

**Implementation Steps:**
1. Create `.github/workflows/roadmap-integrity.yml`:
   ```yaml
   name: Roadmap Integrity
   on: [push, pull_request]
   jobs:
     verify:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
           with:
             fetch-depth: 0
         - uses: actions/setup-python@v5
           with:
             python-version: '3.11'
         - run: pip install vibey
         - run: vibey verify-commits ${{ github.event.before }}..${{ github.sha }}
   ```

**Acceptance Criteria:**
- [ ] Workflow runs on push and PR
- [ ] Blocks merge on failure
- [ ] Clear error output

**Deliverables:**
- `.github/workflows/roadmap-integrity.yml`

---

### Task 010: GitLab CI equivalent
**File:** `01KC2D0JK7READW9KAK1HBX4BC.yaml`
**Complexity:** Low | **Estimate:** 2 hours
**Depends on:** Task 009

**Description:**
Create GitLab CI configuration.

**Deliverables:**
- GitLab CI example in docs

---

### Task 011: vibey verify-commits command
**File:** `01KC2D0JK7READW9KAK1HBX4BD.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 004

**Description:**
Create command to verify commit ranges for CI use.

**Implementation Steps:**
1. Implement `vibey verify-commits <range>`:
   ```python
   @roadmap.command('verify-commits')
   @click.argument('range')
   @click.option('--json', is_flag=True)
   def verify_commits(range: str, json: bool):
       """Verify roadmap changes in commit range."""
   ```
2. Parse git revision range
3. Verify each commit's roadmap changes
4. Exit code 0=all pass, 1=failures

**Acceptance Criteria:**
- [ ] Command works with git ranges
- [ ] JSON output option
- [ ] Appropriate exit codes

**Deliverables:**
- `verify-commits` command

---

### Task 012: CI documentation
**File:** `01KC2D0JK7READW9KAK1HBX4BE.yaml`
**Complexity:** Low | **Estimate:** 2 hours
**Depends on:** Task 010, Task 011

**Deliverables:**
- `docs/guides/CI_VERIFICATION.md`

---

## Phase 4: Cryptographic Signing (Tasks 013-018)

### Task 013: Design key management
**File:** `01KC2D0JK7READW9KAK1HBX4BF.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 002

**Description:**
Design key management for signing activity log entries.

**Key Decisions:**
- Private key: `~/.vibey/private.key` (never committed)
- Public keys: `.vibey/authorized-signers/` (committed)
- Algorithm: Ed25519
- Bootstrap: First signer self-authorizes

**Deliverables:**
- `KEY_MANAGEMENT_DESIGN.md`

---

### Task 014: vibey auth setup
**File:** `01KC2D0JK7READW9KAK1HBX4BG.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 013

**Description:**
Generate Ed25519 keypair for signing.

**Acceptance Criteria:**
- [ ] Generates keypair
- [ ] Stores in `~/.vibey/`
- [ ] Displays public key

**Deliverables:**
- `vibey auth setup` command

---

### Task 015: vibey auth add-signer
**File:** `01KC2D0JK7READW9KAK1HBX4BH.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 014

**Description:**
Register authorized signers.

**Deliverables:**
- `vibey auth add-signer` command

---

### Task 016: Integrate signing into activity log
**File:** `01KC2D0JK7READW9KAK1HBX4BJ.yaml`
**Complexity:** High | **Estimate:** 6 hours
**Depends on:** Task 015

**Description:**
Sign activity log entries with user's private key.

**Implementation Steps:**
1. Update `ActivityLogWriter.log_command()`:
   ```python
   def log_command(self, ...):
       event = CommandActivityEvent(...)

       if signing_enabled():
           private_key = load_private_key()
           event.signature = sign(private_key, event.canonical_bytes())
           event.signer = get_signer_identity()

       self.write_event(event)
   ```
2. Define canonical serialization (deterministic JSON)
3. Sign: id, timestamp, command, object_id, changes, file_hashes
4. Graceful degradation if no key

**Acceptance Criteria:**
- [ ] Entries signed when key available
- [ ] Canonical serialization defined
- [ ] Graceful degradation

**Deliverables:**
- Signing integration

---

### Task 017: Signature verification
**File:** `01KC2D0JK7READW9KAK1HBX4BK.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 016

**Description:**
Verify signatures against authorized signers.

**Implementation Steps:**
1. Update `ChangeVerifier.verify_file()`:
   ```python
   def verify_file(self, file_path: Path) -> VerificationResult:
       entry = self.find_entry_for_file(file_path)
       if not entry:
           return VerificationResult(False, "No activity log entry")

       if entry.signature:
           if not self.verify_signature(entry):
               return VerificationResult(False, "Invalid signature")
           if not self.is_authorized_signer(entry.signer):
               return VerificationResult(False, f"Unknown signer: {entry.signer}")

       return VerificationResult(True, "Verified")
   ```

**Acceptance Criteria:**
- [ ] Signature verification works
- [ ] Unknown signers rejected
- [ ] Unsigned entries: warning only

**Deliverables:**
- Signature verification logic

---

### Task 018: Key management docs
**File:** `01KC2D0JK7READW9KAK1HBX4BM.yaml`
**Complexity:** Low | **Estimate:** 4 hours
**Depends on:** Task 017

**Deliverables:**
- `docs/guides/KEY_MANAGEMENT.md`
- `docs/guides/TEAM_ONBOARDING.md`

---

## Phase 5: Polish & Quality (Tasks 019-022)

### Task 019: Error messages
**File:** `01KC2D0JK7READW9KAK1HBX4BN.yaml`
**Complexity:** Low | **Estimate:** 4 hours

**Description:**
Improve error messages throughout the system.

---

### Task 020: Edge cases
**File:** `01KC2D0JK7READW9KAK1HBX4BP.yaml`
**Complexity:** High | **Estimate:** 8 hours

**Description:**
Handle merge conflicts, rebases, cherry-picks, amends.

**Key Insight:** Verify by file content hash, not commit hash.

**Deliverables:**
- `docs/guides/GIT_WORKFLOW_EDGE_CASES.md`

---

### Task 021: Performance
**File:** `01KC2D0JK7READW9KAK1HBX4BQ.yaml`
**Complexity:** Medium | **Estimate:** 4 hours

**Description:**
Optimize verification performance.

**Key Optimization:** Index activity log by `file_hash_after` for O(1) lookups.

---

### Task 022: Testing
**File:** `01KC2D0JK7READW9KAK1HBX4BR.yaml`
**Complexity:** High | **Estimate:** 8 hours

**Description:**
Comprehensive test suite.

**Test Files:**
- `tests/operations/roadmap/test_verification.py`
- `tests/operations/git/test_hooks.py`
- `tests/operations/auth/test_keys.py`
- `tests/integration/test_integrity_workflow.py`

---

## Dependency Graph

```
Phase 0 (Activity Log Refactor):
  000A → 000B → 000C → 000D

Phase 1 (Foundation):
  000B → 001 → 002 → 003 → 004

Phase 2 (Local Enforcement):
  004 → 005 → 006
  005 → 007 → 008

Phase 3 (Server Enforcement):
  004 → 009 → 010
  004 → 011
  010, 011 → 012

Phase 4 (Crypto Signing):
  002 → 013 → 014 → 015 → 016 → 017 → 018

Phase 5 (Polish):
  008, 012, 018 → 019
  017 → 020
  011 → 021
  020, 021 → 022
```

## Estimated Timeline

| Phase | Tasks | Hours |
|-------|-------|-------|
| **Phase 0: Activity Log Refactor** | 000A-000D | 21 |
| Phase 1: Foundation | 001-004 | 16 |
| Phase 2: Local Enforcement | 005-008 | 12 |
| Phase 3: Server Enforcement | 009-012 | 12 |
| Phase 4: Crypto Signing | 013-018 | 26 |
| Phase 5: Polish | 019-022 | 24 |
| **Total** | **26 tasks** | **111h** |

---

## Success Metrics

1. **Single Entry:** One CLI command = one activity log entry
2. **Coverage:** 100% CLI write operations logged with hashes
3. **Verification:** <100ms per file
4. **CI Performance:** <30s for typical PR
5. **Bypass Detection:** 100% logged

---

## Migration Notes

### Existing Activity Log Data

The existing activity log (from dogfooding-bugs Sprint 7) uses field-level entries:
```jsonl
{"field": "status", "old_value": "in_progress", "new_value": "completed", ...}
```

After Phase 0 migration, format will be:
```jsonl
{"command": "...", "changes": [{"field": "status", "old": "in_progress", "new": "completed"}], ...}
```

**Backward Compatibility:**
- Reader supports both formats
- Old entries returned with `changes: [single_change]`
- No data loss during migration
