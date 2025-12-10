# Sprint Plan: Roadmap Integrity Protection

**Sprint ID:** git-integration-5
**Sprint Name:** Roadmap Integrity Protection
**Track:** git-integration
**Estimated Duration:** 2.5 weeks

## Overview

Implement defense-in-depth protection for roadmap integrity, preventing AI assistants from bypassing safeguards via direct YAML edits and `--no-verify` commits.

Based on: ROADMAP_INTEGRITY_OPTIONS_REPORT.md

## Tasks

#### Task 1: Audit existing cli-changes.json implementation
**ID:** git-integration-5-task-001
**Description:** Review the current cli-changes.json tracking system to understand its capabilities and limitations. Document current state and identify gaps.
**Acceptance Criteria:**
- Document current manifest format
- Identify what operations are tracked vs not tracked
- List gaps in coverage
**Complexity:** low
**Estimated:** 2 hours

#### Task 2: Design standardized manifest format
**ID:** git-integration-5-task-002
**Description:** Design a comprehensive manifest format that tracks all CLI write operations with sufficient metadata for verification.
**Acceptance Criteria:**
- Manifest schema documented
- Includes: timestamp, operation, target_id, file, before_hash, after_hash, cli_command
- Schema validated against use cases
**Dependencies:** git-integration-5-task-001
**Complexity:** medium
**Estimated:** 4 hours

#### Task 3: Ensure all CLI write operations record to manifest
**ID:** git-integration-5-task-003
**Description:** Update all roadmap CLI commands that modify YAML files to record their changes to the manifest.
**Acceptance Criteria:**
- All write operations recorded: complete, start, edit, create, etc.
- Consistent recording across all commands
- Unit tests for recording
**Dependencies:** git-integration-5-task-002
**Complexity:** high
**Estimated:** 8 hours

#### Task 4: Add vibey verify-change command
**ID:** git-integration-5-task-004
**Description:** Create a new CLI command that verifies if a YAML change was made through CLI by checking the manifest.
**Acceptance Criteria:**
- `vibey verify-change <file>` command implemented
- Returns success/failure with clear message
- Supports --commit flag for historical verification
**Dependencies:** git-integration-5-task-003
**Complexity:** medium
**Estimated:** 4 hours

#### Task 5: Update pre-commit hook to verify manifest
**ID:** git-integration-5-task-005
**Description:** Modify the pre-commit hook to use manifest verification for staged YAML files.
**Acceptance Criteria:**
- Pre-commit calls vibey verify-change for each staged roadmap YAML
- Clear error messages on verification failure
- Hook passes when changes are verified
**Dependencies:** git-integration-5-task-004
**Complexity:** medium
**Estimated:** 4 hours

#### Task 6: Add pre-push hook with manifest verification
**ID:** git-integration-5-task-006
**Description:** Create a pre-push hook that verifies all commits being pushed have valid manifest entries for roadmap changes.
**Acceptance Criteria:**
- Pre-push hook installed alongside pre-commit
- Verifies all commits in push range
- Blocks push if any commit has unverified changes
**Dependencies:** git-integration-5-task-005
**Complexity:** medium
**Estimated:** 4 hours

#### Task 7: Add bypass detection with audit logging
**ID:** git-integration-5-task-007
**Description:** Implement post-commit hook that detects when pre-commit was bypassed and logs to audit trail.
**Acceptance Criteria:**
- Post-commit detects if pre-commit ran
- Logs bypass events to .vibey/audit/bypass.log
- Includes commit hash, timestamp, files changed
**Dependencies:** git-integration-5-task-005
**Complexity:** low
**Estimated:** 2 hours

#### Task 8: Documentation for hook installation
**ID:** git-integration-5-task-008
**Description:** Update documentation for git hook installation, covering all hooks (pre-commit, commit-msg, post-commit, pre-push).
**Acceptance Criteria:**
- Updated vibey roadmap install-hooks command
- Documentation in docs/
- Covers all hook types and their purposes
**Dependencies:** git-integration-5-task-007
**Complexity:** low
**Estimated:** 2 hours

#### Task 9: Create GitHub Actions workflow for verification
**ID:** git-integration-5-task-009
**Description:** Create a GitHub Actions workflow that verifies roadmap integrity on push and PR.
**Acceptance Criteria:**
- .github/workflows/roadmap-integrity.yml created
- Runs on push and pull_request
- Calls vibey verify-commits command
- Blocks merge on failure
**Dependencies:** git-integration-5-task-004
**Complexity:** medium
**Estimated:** 4 hours

#### Task 10: Create GitLab CI equivalent
**ID:** git-integration-5-task-010
**Description:** Create GitLab CI configuration for roadmap integrity verification.
**Acceptance Criteria:**
- .gitlab-ci.yml section for roadmap integrity
- Equivalent functionality to GitHub Actions
- Documentation for setup
**Dependencies:** git-integration-5-task-009
**Complexity:** low
**Estimated:** 2 hours

#### Task 11: Add vibey verify-commits command for CI
**ID:** git-integration-5-task-011
**Description:** Create a CLI command that verifies a range of commits for roadmap integrity, suitable for CI use.
**Acceptance Criteria:**
- `vibey verify-commits <range>` command
- Accepts git revision range (e.g., main..HEAD)
- Returns non-zero exit code on failure
- JSON output option for CI parsing
**Dependencies:** git-integration-5-task-004
**Complexity:** medium
**Estimated:** 4 hours

#### Task 12: Documentation for CI setup
**ID:** git-integration-5-task-012
**Description:** Document how to set up CI verification for GitHub Actions and GitLab CI.
**Acceptance Criteria:**
- Setup guide in docs/
- Copy-paste ready configurations
- Troubleshooting section
**Dependencies:** git-integration-5-task-010, git-integration-5-task-011
**Complexity:** low
**Estimated:** 2 hours

#### Task 13: Design key management system
**ID:** git-integration-5-task-013
**Description:** Design the key management architecture for cryptographic signing of manifest entries.
**Acceptance Criteria:**
- Key storage location defined (~/.vibey/)
- Public key registration mechanism (.vibey/authorized-signers/)
- Key rotation strategy
- Bootstrap problem solution
**Dependencies:** git-integration-5-task-002
**Complexity:** medium
**Estimated:** 4 hours

#### Task 14: Implement key generation (vibey auth setup)
**ID:** git-integration-5-task-014
**Description:** Implement the vibey auth setup command to generate keypairs for signing.
**Acceptance Criteria:**
- `vibey auth setup` generates keypair
- Keys stored in ~/.vibey/private.key and public.key
- Supports Ed25519 or ECDSA
- Prompts for overwrite if exists
**Dependencies:** git-integration-5-task-013
**Complexity:** medium
**Estimated:** 4 hours

#### Task 15: Implement signer registration (vibey auth add-signer)
**ID:** git-integration-5-task-015
**Description:** Implement command to register new signers by adding their public key to the repository.
**Acceptance Criteria:**
- `vibey auth add-signer <name> <pubkey-file>` command
- Adds to .vibey/authorized-signers/
- Commit is signed by existing authorized user
- Handles bootstrap case
**Dependencies:** git-integration-5-task-014
**Complexity:** medium
**Estimated:** 4 hours

#### Task 16: Integrate signing into CLI manifest writes
**ID:** git-integration-5-task-016
**Description:** Update manifest recording to sign entries with user's private key.
**Acceptance Criteria:**
- Each manifest entry includes signature field
- Signature covers: timestamp, operation, file, content_hash
- Uses user's private key from ~/.vibey/
**Dependencies:** git-integration-5-task-015
**Complexity:** high
**Estimated:** 6 hours

#### Task 17: Update verification to check signatures
**ID:** git-integration-5-task-017
**Description:** Update verify-change and verify-commits to validate signatures against authorized signers.
**Acceptance Criteria:**
- Verification checks signature validity
- Checks signer is in authorized-signers
- Clear error messages for invalid/unknown signers
**Dependencies:** git-integration-5-task-016
**Complexity:** medium
**Estimated:** 4 hours

#### Task 18: Documentation for key management
**ID:** git-integration-5-task-018
**Description:** Document the key management system including setup, adding team members, and key rotation.
**Acceptance Criteria:**
- User guide for vibey auth commands
- Team onboarding guide
- Key rotation procedures
- Security considerations
**Dependencies:** git-integration-5-task-017
**Complexity:** low
**Estimated:** 4 hours

#### Task 19: Error messages and user guidance
**ID:** git-integration-5-task-019
**Description:** Improve error messages throughout the integrity system to guide users to correct actions.
**Acceptance Criteria:**
- All error messages actionable
- Suggest correct CLI commands
- Link to documentation
**Dependencies:** git-integration-5-task-008, git-integration-5-task-012, git-integration-5-task-018
**Complexity:** low
**Estimated:** 4 hours

#### Task 20: Edge case handling (merge conflicts, rebases)
**ID:** git-integration-5-task-020
**Description:** Handle edge cases in git workflows: merge conflicts, rebases, cherry-picks, amends.
**Acceptance Criteria:**
- Rebase handling documented
- Merge conflict guidance
- Cherry-pick considerations
- Amend limitations documented
**Dependencies:** git-integration-5-task-017
**Complexity:** high
**Estimated:** 8 hours

#### Task 21: Performance optimization
**ID:** git-integration-5-task-021
**Description:** Optimize verification performance for large repositories with many commits.
**Acceptance Criteria:**
- Manifest lookup is O(1) or O(log n)
- Batch verification efficient
- Caching where appropriate
**Dependencies:** git-integration-5-task-011
**Complexity:** medium
**Estimated:** 4 hours

#### Task 22: Comprehensive testing
**ID:** git-integration-5-task-022
**Description:** Create comprehensive test suite for the entire integrity protection system.
**Acceptance Criteria:**
- Unit tests for all new functions
- Integration tests for CLI commands
- End-to-end tests for complete workflows
- Test bypass detection
**Dependencies:** git-integration-5-task-020, git-integration-5-task-021
**Complexity:** high
**Estimated:** 8 hours

## Deliverables

1. Standardized manifest format and tracking
2. vibey verify-change command
3. Updated pre-commit and pre-push hooks with manifest verification
4. Bypass detection with audit logging
5. GitHub Actions workflow for roadmap integrity
6. GitLab CI equivalent
7. vibey verify-commits command for CI
8. Key management system (vibey auth)
9. Cryptographic signing integration
10. Comprehensive documentation and testing
