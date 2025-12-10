# Sprint 5: Roadmap Integrity Protection - Task Plans

**Sprint ID:** git-integration-5
**Track:** Enhanced Git Integration
**Status:** Planning
**Created:** 2025-12-10
**Integration Reference:** docs/roadmap/sqlite-backend/sqlite-backend-6/UNIFIED_TICKET_ARCHITECTURE.md

---

## Unified Architecture Integration Summary

Sprint 5 implements **process enforcement** that complements the unified architecture's **requirement validation**:

| System | Purpose | Question |
|--------|---------|----------|
| Unified Architecture | Requirement validation | "Are all criteria met for transition?" |
| Sprint 5 | Process enforcement | "Did this change go through the approved CLI?" |

**Key Integration Points:**
1. `ManifestVerifiedTarget` - New criterion type proving CLI usage
2. `activity_log` linking - Manifest entries sync to ticket activity
3. `ManualTarget.assessed_by` alignment - Signature tracking

---

## Phase 1: Foundation (Tasks 001-004)

### Task 001: Audit existing cli-changes.json implementation
**File:** `01KC2D0JK7READW9KAK1HBX4B3.yaml`
**Complexity:** Low | **Estimate:** 2 hours

**Description:**
Review the current `.vibey/cli-changes.json` tracking system to understand its capabilities and limitations. Document current state, identify gaps, and assess alignment with unified architecture.

**Implementation Steps:**
1. Locate and read current cli-changes.json implementation
2. Document current manifest format (fields, structure)
3. List what CLI operations are tracked vs not tracked
4. Identify coverage gaps
5. Document how manifest could integrate with `Ticket.activity_log`

**Unified Architecture Integration:**
- Review `activity_log` field in ticket models
- Identify overlap with manifest tracking
- Propose dual-write strategy (manifest + activity_log)

**Acceptance Criteria:**
- [ ] Current manifest format documented
- [ ] List of tracked vs untracked operations
- [ ] Gap analysis document
- [ ] Integration proposal with unified architecture

**Deliverables:**
- `CLI_CHANGES_AUDIT.md` in sprint context

---

### Task 002: Design standardized manifest format
**File:** `01KC2D0JK7READW9KAK1HBX4B4.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 001

**Description:**
Design a comprehensive manifest format that tracks all CLI write operations with sufficient metadata for verification. Align with unified ticket architecture concepts.

**Implementation Steps:**
1. Define manifest entry schema:
   ```yaml
   manifest_entry:
     timestamp: ISO8601
     operation: create|update|delete|complete|start
     cli_command: "vibey roadmap update task..."
     target_type: roadmap|track|sprint|task
     target_id: ULID
     file_path: relative path
     before_hash: SHA256 (null for create)
     after_hash: SHA256
     user_id: string (from auth if signed)
     signature: base64 (Phase 4)
   ```
2. Design manifest file structure (`.vibey/manifest.jsonl` - append-only)
3. Define retention/rotation policy
4. Document verification algorithm

**Unified Architecture Integration:**
- Map `operation` to `TicketStatus` transitions
- Define `ManifestVerifiedTarget` criterion type:
  ```python
  class ManifestVerifiedTarget(CriterionTarget):
      """Criterion met when manifest verification succeeds."""
      target_id: str
      operation: str  # Operation type to verify

      def is_satisfied(self) -> bool:
          return verify_manifest_entry(self.target_id, self.operation)
  ```
- Link manifest entries to `Ticket.activity_log` format

**Acceptance Criteria:**
- [ ] Manifest schema documented and validated
- [ ] File format decision (JSONL recommended)
- [ ] ManifestVerifiedTarget design documented
- [ ] Integration with activity_log documented

**Deliverables:**
- `MANIFEST_SCHEMA.md` in sprint context
- `ManifestVerifiedTarget` type specification

---

### Task 003: Ensure all CLI write operations record to manifest
**File:** `01KC2D0JK7READW9KAK1HBX4B5.yaml`
**Complexity:** High | **Estimate:** 8 hours
**Depends on:** Task 002

**Description:**
Update all roadmap CLI commands that modify YAML files to record their changes to the manifest. This ensures complete audit trail of CLI-authorized changes.

**Implementation Steps:**
1. Identify all CLI write operations in `vibey/cli/commands.py`:
   - `roadmap update task`
   - `roadmap update sprint`
   - `roadmap update track`
   - `roadmap create task`
   - `roadmap create sprint`
   - `roadmap create track`
   - etc.
2. Create manifest writer utility:
   ```python
   # vibey/operations/roadmap/manifest.py
   class ManifestWriter:
       def record_change(
           self,
           operation: str,
           target_type: str,
           target_id: str,
           file_path: Path,
           before_content: Optional[str],
           after_content: str,
           cli_command: str
       ) -> ManifestEntry
   ```
3. Integrate manifest writer into each CLI command
4. Add pre-write hash calculation
5. Add post-write verification

**Unified Architecture Integration:**
- Also write to `activity_log` field for each ticket modified
- Use same timestamp for both manifest and activity_log
- Link manifest entry ID in activity_log entry

**Acceptance Criteria:**
- [ ] All write operations recorded to manifest
- [ ] Consistent format across all commands
- [ ] Pre/post hash verification working
- [ ] Unit tests for manifest recording
- [ ] Activity log dual-write implemented

**Deliverables:**
- `vibey/operations/roadmap/manifest.py`
- Updated CLI commands
- Test suite

---

### Task 004: Add vibey verify-change command
**File:** `01KC2D0JK7READW9KAK1HBX4B6.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 003

**Description:**
Create a new CLI command that verifies if a YAML change was made through CLI by checking the manifest.

**Implementation Steps:**
1. Implement `vibey verify-change <file>` command:
   ```python
   @roadmap.command('verify-change')
   @click.argument('file_path')
   @click.option('--commit', help='Verify against specific commit')
   def verify_change(file_path: str, commit: Optional[str]):
       """Verify a file change was made through CLI."""
   ```
2. Verification algorithm:
   - Get current file hash
   - Find manifest entry with matching after_hash
   - Verify entry exists and is valid
   - Return success/failure with details
3. Support `--commit` flag for historical verification
4. JSON output option for machine parsing

**Unified Architecture Integration:**
- This command provides the implementation for `ManifestVerifiedTarget.is_satisfied()`
- Can be called by criterion evaluation system
- Output format compatible with criterion result

**Acceptance Criteria:**
- [ ] `vibey verify-change <file>` command works
- [ ] Clear success/failure messages
- [ ] `--commit` flag for historical checks
- [ ] JSON output option
- [ ] Exit codes suitable for scripting (0=verified, 1=unverified, 2=error)

**Deliverables:**
- `verify-change` command in CLI
- Verification logic in `vibey/operations/roadmap/manifest.py`

---

## Phase 2: Local Enforcement (Tasks 005-008)

### Task 005: Update pre-commit hook to verify manifest
**File:** `01KC2D0JK7READW9KAK1HBX4B7.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 004

**Description:**
Modify the pre-commit hook to use manifest verification for staged YAML files in the roadmap directory.

**Implementation Steps:**
1. Update `vibey/operations/git/hooks/pre_commit.py`:
   ```python
   def verify_staged_roadmap_files():
       staged = get_staged_files()
       roadmap_files = [f for f in staged if is_roadmap_file(f)]
       for file in roadmap_files:
           result = verify_change(file)
           if not result.verified:
               block_commit(f"Unverified change to {file}")
   ```
2. Clear error messages explaining why commit is blocked
3. Guidance on how to make changes correctly (use CLI)
4. Support for `--no-verify` bypass (with audit logging)

**Unified Architecture Integration:**
- Hook enforces process that criterion validates
- Failed verification = criterion would fail
- Prevents invalid state from entering git

**Acceptance Criteria:**
- [ ] Pre-commit verifies all staged roadmap YAML files
- [ ] Clear error messages on failure
- [ ] Commit passes when changes are verified
- [ ] Helpful guidance for users

**Deliverables:**
- Updated pre-commit hook
- Error message templates

---

### Task 006: Add pre-push hook with manifest verification
**File:** `01KC2D0JK7READW9KAK1HBX4B8.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 005

**Description:**
Create a pre-push hook that verifies all commits being pushed have valid manifest entries for roadmap changes.

**Implementation Steps:**
1. Create `vibey/operations/git/hooks/pre_push.py`:
   ```python
   def verify_commits_in_push(remote: str, url: str, local_ref: str, remote_ref: str):
       commits = get_commits_in_range(remote_ref, local_ref)
       for commit in commits:
           roadmap_files = get_changed_files(commit, pattern=".vibey/roadmap/**")
           for file in roadmap_files:
               verify_at_commit(file, commit)
   ```
2. Install alongside pre-commit hook
3. Verify entire commit range being pushed
4. Block push if any commit has unverified changes

**Acceptance Criteria:**
- [ ] Pre-push hook installed with hook installation command
- [ ] Verifies all commits in push range
- [ ] Blocks push on unverified changes
- [ ] Clear error messages with commit hashes

**Deliverables:**
- `pre_push.py` hook implementation
- Hook installer update

---

### Task 007: Add bypass detection with audit logging
**File:** `01KC2D0JK7READW9KAK1HBX4B9.yaml`
**Complexity:** Low | **Estimate:** 2 hours
**Depends on:** Task 005

**Description:**
Implement post-commit hook that detects when pre-commit was bypassed and logs to audit trail.

**Implementation Steps:**
1. Create `vibey/operations/git/hooks/post_commit.py`:
   ```python
   def detect_bypass():
       # Check if pre-commit marker file exists
       if not pre_commit_ran():
           log_bypass_event(
               commit=get_head_commit(),
               timestamp=datetime.now(timezone.utc),
               files=get_changed_roadmap_files()
           )
   ```
2. Marker file approach: pre-commit creates `.vibey/.pre-commit-ran`
3. Post-commit checks and deletes marker
4. Missing marker = bypass detected
5. Log to `.vibey/audit/bypass.log`

**Unified Architecture Integration:**
- Bypass events could create blocking criteria
- `ExternalTarget` pointing to bypass audit status
- Team can require "no recent bypasses" as criterion

**Acceptance Criteria:**
- [ ] Post-commit detects bypass
- [ ] Logs to `.vibey/audit/bypass.log`
- [ ] Includes commit hash, timestamp, files
- [ ] Works with both pre-commit and commit-msg hooks

**Deliverables:**
- `post_commit.py` hook
- Bypass audit log format

---

### Task 008: Documentation for hook installation
**File:** `01KC2D0JK7READW9KAK1HBX4BA.yaml`
**Complexity:** Low | **Estimate:** 2 hours
**Depends on:** Task 007

**Description:**
Update documentation for git hook installation, covering all hooks.

**Implementation Steps:**
1. Update `vibey roadmap install-hooks` command to install all hooks
2. Create `docs/guides/GIT_HOOKS.md`:
   - Pre-commit: YAML validation + manifest verification
   - Commit-msg: Task reference parsing
   - Post-commit: Bypass detection
   - Pre-push: Batch commit verification
3. Troubleshooting section
4. Uninstall instructions

**Acceptance Criteria:**
- [ ] Updated `install-hooks` command
- [ ] Comprehensive hook documentation
- [ ] Troubleshooting guide
- [ ] Uninstall command/instructions

**Deliverables:**
- `docs/guides/GIT_HOOKS.md`
- Updated CLI help text

---

## Phase 3: Server Enforcement (Tasks 009-012)

### Task 009: Create GitHub Actions workflow for verification
**File:** `01KC2D0JK7READW9KAK1HBX4BB.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 004

**Description:**
Create a GitHub Actions workflow that verifies roadmap integrity on push and PR.

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
             fetch-depth: 0  # Full history for commit range
         - uses: actions/setup-python@v5
         - run: pip install vibey
         - run: vibey verify-commits ${{ github.event.before }}..${{ github.sha }}
   ```
2. Block merge on failure
3. Clear status check name
4. Support for base branch comparison on PRs

**Acceptance Criteria:**
- [ ] Workflow file created
- [ ] Runs on push and PR
- [ ] Blocks merge on failure
- [ ] Clear error output

**Deliverables:**
- `.github/workflows/roadmap-integrity.yml`

---

### Task 010: Create GitLab CI equivalent
**File:** `01KC2D0JK7READW9KAK1HBX4BC.yaml`
**Complexity:** Low | **Estimate:** 2 hours
**Depends on:** Task 009

**Description:**
Create GitLab CI configuration for roadmap integrity verification.

**Implementation Steps:**
1. Create `.gitlab-ci.yml` section:
   ```yaml
   roadmap-integrity:
     stage: test
     image: python:3.11
     script:
       - pip install vibey
       - vibey verify-commits $CI_COMMIT_BEFORE_SHA..$CI_COMMIT_SHA
     rules:
       - changes:
           - ".vibey/roadmap/**"
   ```
2. Only run when roadmap files change
3. Block pipeline on failure

**Acceptance Criteria:**
- [ ] GitLab CI config section
- [ ] Equivalent to GitHub Actions
- [ ] Documentation for setup

**Deliverables:**
- GitLab CI example in docs

---

### Task 011: Add vibey verify-commits command for CI
**File:** `01KC2D0JK7READW9KAK1HBX4BD.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 004

**Description:**
Create a CLI command that verifies a range of commits for roadmap integrity, suitable for CI use.

**Implementation Steps:**
1. Implement `vibey verify-commits <range>`:
   ```python
   @roadmap.command('verify-commits')
   @click.argument('range')
   @click.option('--json', is_flag=True, help='JSON output')
   def verify_commits(range: str, json: bool):
       """Verify roadmap changes in a commit range."""
       commits = parse_git_range(range)
       results = []
       for commit in commits:
           result = verify_commit_changes(commit)
           results.append(result)
       # Return appropriate exit code
   ```
2. Accept git revision range (e.g., `main..HEAD`, `abc123..def456`)
3. Non-zero exit code on any failure
4. JSON output for CI parsing
5. Summary output for humans

**Acceptance Criteria:**
- [ ] `vibey verify-commits <range>` command
- [ ] Accepts git revision range
- [ ] Exit code 0=all verified, 1=failures found
- [ ] JSON output option
- [ ] Human-readable summary

**Deliverables:**
- `verify-commits` command
- Batch verification logic

---

### Task 012: Documentation for CI setup
**File:** `01KC2D0JK7READW9KAK1HBX4BE.yaml`
**Complexity:** Low | **Estimate:** 2 hours
**Depends on:** Task 010, Task 011

**Description:**
Document how to set up CI verification for GitHub Actions and GitLab CI.

**Implementation Steps:**
1. Create `docs/guides/CI_VERIFICATION.md`:
   - GitHub Actions setup
   - GitLab CI setup
   - Generic CI setup (any system)
   - Required environment
   - Troubleshooting
2. Copy-paste ready configurations
3. Example output and error messages

**Acceptance Criteria:**
- [ ] Setup guide in docs
- [ ] Copy-paste ready configs
- [ ] Troubleshooting section

**Deliverables:**
- `docs/guides/CI_VERIFICATION.md`

---

## Phase 4: Cryptographic Signing (Tasks 013-018)

### Task 013: Design key management system
**File:** `01KC2D0JK7READW9KAK1HBX4BF.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 002

**Description:**
Design the key management architecture for cryptographic signing of manifest entries.

**Implementation Steps:**
1. Define key storage locations:
   - Private key: `~/.vibey/private.key` (user-local, never committed)
   - Public keys: `.vibey/authorized-signers/` (committed to repo)
2. Key format: Ed25519 (fast, secure, small)
3. Public key registration mechanism:
   - Signer adds their public key via PR
   - Existing authorized signers approve
   - Bootstrap: first signer self-authorizes
4. Key rotation strategy:
   - Old keys remain valid for verification
   - New keys added, old removed after transition period
5. Solve bootstrap problem:
   - Project owner generates first keypair
   - Commits public key as first authorized signer
   - This commit can be unsigned (bootstrap exception)

**Unified Architecture Integration:**
- Signature field aligns with `ManualTarget.assessed_by`
- Signer identity maps to `assessed_by` for audit trail
- Public key registry is source of truth for valid assessors

**Acceptance Criteria:**
- [ ] Key storage locations defined
- [ ] Key format and algorithm chosen
- [ ] Bootstrap problem solved
- [ ] Key rotation documented
- [ ] Security considerations documented

**Deliverables:**
- `KEY_MANAGEMENT_DESIGN.md` in sprint context

---

### Task 014: Implement key generation (vibey auth setup)
**File:** `01KC2D0JK7READW9KAK1HBX4BG.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 013

**Description:**
Implement the vibey auth setup command to generate keypairs for signing.

**Implementation Steps:**
1. Implement `vibey auth setup`:
   ```python
   @click.group()
   def auth():
       """Authentication and signing commands."""

   @auth.command('setup')
   @click.option('--force', is_flag=True, help='Overwrite existing keys')
   def setup(force: bool):
       """Generate signing keypair."""
       key_dir = Path.home() / '.vibey'
       private_key_path = key_dir / 'private.key'
       public_key_path = key_dir / 'public.key'

       if private_key_path.exists() and not force:
           raise click.ClickException("Keys exist. Use --force to overwrite.")

       # Generate Ed25519 keypair
       private_key = Ed25519PrivateKey.generate()
       # Save keys...
   ```
2. Use `cryptography` library for Ed25519
3. Store private key with restrictive permissions (0600)
4. Display public key for registration
5. Prompt before overwriting existing keys

**Acceptance Criteria:**
- [ ] `vibey auth setup` generates keypair
- [ ] Keys stored in `~/.vibey/`
- [ ] Ed25519 algorithm used
- [ ] Prompts for overwrite
- [ ] Displays public key for registration

**Deliverables:**
- `vibey auth setup` command
- `vibey/operations/auth/keys.py`

---

### Task 015: Implement signer registration (vibey auth add-signer)
**File:** `01KC2D0JK7READW9KAK1HBX4BH.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 014

**Description:**
Implement command to register new signers by adding their public key to the repository.

**Implementation Steps:**
1. Implement `vibey auth add-signer`:
   ```python
   @auth.command('add-signer')
   @click.argument('name')
   @click.argument('pubkey_file', type=click.Path(exists=True))
   def add_signer(name: str, pubkey_file: str):
       """Register a new authorized signer."""
       # Validate public key format
       # Create .vibey/authorized-signers/{name}.pub
       # Require existing signer to commit (except bootstrap)
   ```
2. Validate public key format
3. Store in `.vibey/authorized-signers/{name}.pub`
4. Bootstrap detection: if no signers exist, allow self-registration
5. Otherwise, require commit to be signed by existing signer

**Acceptance Criteria:**
- [ ] `vibey auth add-signer` command
- [ ] Validates public key format
- [ ] Creates file in authorized-signers directory
- [ ] Handles bootstrap case
- [ ] Error handling for invalid keys

**Deliverables:**
- `vibey auth add-signer` command
- Authorized signers directory structure

---

### Task 016: Integrate signing into CLI manifest writes
**File:** `01KC2D0JK7READW9KAK1HBX4BJ.yaml`
**Complexity:** High | **Estimate:** 6 hours
**Depends on:** Task 015

**Description:**
Update manifest recording to sign entries with user's private key.

**Implementation Steps:**
1. Update `ManifestWriter.record_change()`:
   ```python
   def record_change(self, ...):
       entry = ManifestEntry(
           timestamp=...,
           operation=...,
           # ... other fields
       )

       # Sign the entry
       if self.signing_enabled:
           private_key = load_private_key()
           signature_data = entry.canonical_bytes()
           entry.signature = sign(private_key, signature_data)
           entry.signer = get_signer_name()

       self.append_entry(entry)
   ```
2. Define canonical serialization for signing (deterministic)
3. Sign: timestamp, operation, target_id, file_path, before_hash, after_hash
4. Optional signing (graceful degradation if no key)
5. Clear message when signing skipped

**Acceptance Criteria:**
- [ ] Manifest entries include signature field
- [ ] Signature covers critical fields
- [ ] Uses user's private key
- [ ] Graceful degradation if no key
- [ ] Signer identity recorded

**Deliverables:**
- Signing integration in ManifestWriter
- Canonical serialization format

---

### Task 017: Update verification to check signatures
**File:** `01KC2D0JK7READW9KAK1HBX4BK.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 016

**Description:**
Update verify-change and verify-commits to validate signatures against authorized signers.

**Implementation Steps:**
1. Update verification logic:
   ```python
   def verify_entry(entry: ManifestEntry) -> VerificationResult:
       # Step 1: Verify hash matches
       if not verify_hash(entry):
           return VerificationResult(False, "Hash mismatch")

       # Step 2: Verify signature (if present)
       if entry.signature:
           signer_key = load_authorized_signer(entry.signer)
           if not signer_key:
               return VerificationResult(False, f"Unknown signer: {entry.signer}")
           if not verify_signature(signer_key, entry):
               return VerificationResult(False, "Invalid signature")

       return VerificationResult(True, "Verified")
   ```
2. Load public keys from `.vibey/authorized-signers/`
3. Clear error for unknown signers
4. Clear error for invalid signatures
5. Support both signed and unsigned entries (transition period)

**Acceptance Criteria:**
- [ ] Verification checks signature validity
- [ ] Checks signer is authorized
- [ ] Clear errors for invalid/unknown signers
- [ ] Supports unsigned entries (warning only)

**Deliverables:**
- Updated verification logic
- Signature validation utilities

---

### Task 018: Documentation for key management
**File:** `01KC2D0JK7READW9KAK1HBX4BM.yaml`
**Complexity:** Low | **Estimate:** 4 hours
**Depends on:** Task 017

**Description:**
Document the key management system including setup, adding team members, and key rotation.

**Implementation Steps:**
1. Create `docs/guides/KEY_MANAGEMENT.md`:
   - Initial setup (`vibey auth setup`)
   - Registering as a signer
   - Adding team members
   - Key rotation procedures
   - Security considerations
   - Troubleshooting
2. Create `docs/guides/TEAM_ONBOARDING.md`:
   - New team member workflow
   - Getting authorized
   - First signed commit

**Acceptance Criteria:**
- [ ] User guide for vibey auth commands
- [ ] Team onboarding guide
- [ ] Key rotation procedures
- [ ] Security considerations documented

**Deliverables:**
- `docs/guides/KEY_MANAGEMENT.md`
- `docs/guides/TEAM_ONBOARDING.md`

---

## Phase 5: Polish & Quality (Tasks 019-022)

### Task 019: Error messages and user guidance
**File:** `01KC2D0JK7READW9KAK1HBX4BN.yaml`
**Complexity:** Low | **Estimate:** 4 hours
**Depends on:** Task 008, Task 012, Task 018

**Description:**
Improve error messages throughout the integrity system to guide users to correct actions.

**Implementation Steps:**
1. Audit all error messages in:
   - Verification commands
   - Git hooks
   - CI output
2. Ensure every error:
   - Explains what went wrong
   - Suggests correct action
   - Links to documentation
3. Create error message catalog
4. Localization-ready format (future)

**Acceptance Criteria:**
- [ ] All error messages actionable
- [ ] Suggest correct CLI commands
- [ ] Link to documentation
- [ ] Consistent format across all components

**Deliverables:**
- Updated error messages
- Error catalog document

---

### Task 020: Edge case handling (merge conflicts, rebases)
**File:** `01KC2D0JK7READW9KAK1HBX4BP.yaml`
**Complexity:** High | **Estimate:** 8 hours
**Depends on:** Task 017

**Description:**
Handle edge cases in git workflows: merge conflicts, rebases, cherry-picks, amends.

**Implementation Steps:**
1. **Merge Conflicts:**
   - Detect when roadmap files have conflicts
   - Require re-running CLI commands after resolution
   - Guidance document
2. **Rebases:**
   - Manifest entries reference original commit
   - After rebase, commit hashes change
   - Design: manifest references parent relationship or file hash
3. **Cherry-picks:**
   - Same issue as rebases
   - Verify by content hash, not commit hash
4. **Amends:**
   - Amended commits change hash
   - Manifest should track logical change, not commit
5. **Force pushes:**
   - Server-side verification catches gaps
   - Clear error message

**Acceptance Criteria:**
- [ ] Merge conflict guidance documented
- [ ] Rebase handling works correctly
- [ ] Cherry-pick handling documented
- [ ] Amend limitations documented
- [ ] Force push detection

**Deliverables:**
- Edge case handling code
- `docs/guides/GIT_WORKFLOW_EDGE_CASES.md`

---

### Task 021: Performance optimization
**File:** `01KC2D0JK7READW9KAK1HBX4BQ.yaml`
**Complexity:** Medium | **Estimate:** 4 hours
**Depends on:** Task 011

**Description:**
Optimize verification performance for large repositories with many commits.

**Implementation Steps:**
1. **Manifest lookup optimization:**
   - Index by file path
   - Index by commit (if needed)
   - Consider SQLite for large manifests
2. **Batch verification:**
   - Process commits in parallel
   - Cache file contents across commits
3. **Incremental verification:**
   - Cache last verified state
   - Only verify new changes
4. **Profile and benchmark:**
   - Measure current performance
   - Identify bottlenecks
   - Document improvements

**Unified Architecture Integration:**
- Consider using SQLite backend (from sqlite-backend track) for manifest storage
- Would align storage mechanism with roadmap data

**Acceptance Criteria:**
- [ ] Manifest lookup is O(1) or O(log n)
- [ ] Batch verification efficient
- [ ] Caching where appropriate
- [ ] Performance benchmarks documented

**Deliverables:**
- Performance optimizations
- Benchmark results

---

### Task 022: Comprehensive testing
**File:** `01KC2D0JK7READW9KAK1HBX4BR.yaml`
**Complexity:** High | **Estimate:** 8 hours
**Depends on:** Task 020, Task 021

**Description:**
Create comprehensive test suite for the entire integrity protection system.

**Implementation Steps:**
1. **Unit tests:**
   - ManifestWriter
   - ManifestReader
   - Verification logic
   - Signature generation/verification
   - Key management
2. **Integration tests:**
   - CLI commands end-to-end
   - Hook execution
   - CI workflow simulation
3. **End-to-end tests:**
   - Complete workflow: edit via CLI -> commit -> verify
   - Bypass scenario: direct edit -> commit -> detect
   - Signature workflow: setup -> sign -> verify
4. **Edge case tests:**
   - Merge conflicts
   - Rebases
   - Missing keys
   - Corrupted manifest

**Acceptance Criteria:**
- [ ] Unit tests for all new functions
- [ ] Integration tests for CLI commands
- [ ] End-to-end workflow tests
- [ ] Bypass detection tests
- [ ] >90% code coverage for new code

**Deliverables:**
- `tests/operations/roadmap/test_manifest.py`
- `tests/operations/git/test_hooks.py`
- `tests/operations/auth/test_keys.py`
- `tests/integration/test_integrity_workflow.py`

---

## Dependency Graph

```
Phase 1 (Foundation):
  001 → 002 → 003 → 004

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

| Phase | Tasks | Hours | Calendar Days (2h/day) |
|-------|-------|-------|------------------------|
| Foundation | 001-004 | 18 | 9 days |
| Local Enforcement | 005-008 | 12 | 6 days |
| Server Enforcement | 009-012 | 12 | 6 days |
| Crypto Signing | 013-018 | 26 | 13 days |
| Polish | 019-022 | 24 | 12 days |
| **Total** | **22** | **92** | **~46 days** |

---

## Success Metrics

1. **Coverage:** 100% of CLI write operations recorded to manifest
2. **Verification:** <100ms to verify single file change
3. **CI Performance:** <30s to verify typical PR (10-20 commits)
4. **Bypass Detection:** 100% of bypasses logged within 1 commit
5. **Documentation:** Zero questions in first week after deployment
