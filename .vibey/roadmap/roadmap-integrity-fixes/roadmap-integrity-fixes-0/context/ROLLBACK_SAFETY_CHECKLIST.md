# Rollback Safety Checklist

**Version:** 1.0
**Last Updated:** 2025-11-20
**Purpose:** Pre-flight and post-flight safety checks for all rollback operations

---

## How to Use This Checklist

1. **Before rollback:** Complete ALL items in Pre-Rollback Checklist
2. **During rollback:** Monitor items in During-Rollback Checklist
3. **After rollback:** Verify ALL items in Post-Rollback Checklist
4. **Document:** Record completion in rollback log

**NEVER skip checklist items.** Each item prevents critical errors.

---

## Pre-Rollback Checklist

Complete BEFORE executing any rollback procedure:

### 1. Current State Backup

- [ ] **Current .vibey/ directory backed up to /tmp/**
  ```bash
  BACKUP_DIR="/tmp/vibey-backup-$(date +%Y%m%d-%H%M%S)"
  cp -r .vibey/ "$BACKUP_DIR/"
  echo "Backup location: $BACKUP_DIR"
  ```

- [ ] **Backup location recorded** (write it down!)
  - Location: `________________________`
  - Size: `________________________`
  - File count: `________________________`

- [ ] **Backup verified readable**
  ```bash
  ls -lah "$BACKUP_DIR/.vibey/roadmap/"
  ```

**Why Critical:** If rollback fails, you can restore from this backup. Without it, you may lose data permanently.

---

### 2. Rollback Source Identification

- [ ] **Rollback source type determined**
  - [ ] Git commit (hash: `________________________`)
  - [ ] Checkpoint backup (path: `________________________`)
  - [ ] Backup archive (path: `________________________`)
  - [ ] Other: `________________________`

- [ ] **Rollback source accessible**
  ```bash
  # For git:
  git show COMMIT_HASH:.vibey/ > /dev/null && echo "✅ Accessible"

  # For checkpoint/archive:
  test -f /path/to/source && echo "✅ Accessible"
  ```

- [ ] **Rollback source date known**
  - Source date: `________________________`
  - Days old: `________________________`
  - Acceptable age? [ ] Yes [ ] No

- [ ] **Rollback source verified**
  ```bash
  # For checkpoint - validate YAML:
  find /path/to/checkpoint/.vibey/roadmap -name "*.yaml" | \
    xargs -I {} python3 -c "import yaml; yaml.safe_load(open('{}'))"
  ```

**Why Critical:** Rolling back to corrupted or wrong source makes problem worse. Always verify source first.

---

### 3. Rollback Scope Definition

- [ ] **Rollback scope clearly defined**
  - [ ] Full restore (entire `.vibey/roadmap/`)
  - [ ] Selective restore (specific files listed below)
  - [ ] Track-specific (which track: `________________________`)
  - [ ] Sprint-specific (which sprint: `________________________`)

- [ ] **For selective rollback: Files listed**
  ```
  Files to rollback:
  1. ________________________
  2. ________________________
  3. ________________________
  4. ________________________
  ```

- [ ] **Files NOT to touch identified**
  ```
  Preserve these files (do not rollback):
  1. ________________________
  2. ________________________
  ```

- [ ] **Impact assessed**
  - Tracks affected: `________________________`
  - Sprints affected: `________________________`
  - Tasks affected: `________________________`
  - Est. file count: `________________________`

**Why Critical:** Knowing exactly what will change prevents accidental overwriting of good data.

---

### 4. Stakeholder Communication

- [ ] **Stakeholders notified** (if rollback affects team)
  - Notification sent: [ ] Yes [ ] No [ ] N/A (solo work)
  - Method: [ ] Slack [ ] Email [ ] In-person [ ] N/A
  - Acknowledged: [ ] Yes [ ] Pending [ ] N/A

- [ ] **Rollback reason documented**
  ```
  Reason for rollback (2-3 sentences):
  ________________________________________
  ________________________________________
  ________________________________________
  ```

- [ ] **Expected downtime communicated** (if applicable)
  - Rollback will take: `________` minutes
  - Roadmap unavailable during rollback: [ ] Yes [ ] No

**Why Critical:** Prevents confusion when teammates see unexpected state changes.

---

### 5. Rollback Procedure Selected

- [ ] **Rollback procedure chosen**
  - [ ] Selective File Rollback (Procedure 3)
  - [ ] Git-Based Rollback (Procedure 1)
  - [ ] Checkpoint Restoration (Procedure 2)
  - [ ] Backup Archive Restoration (Procedure 4)

- [ ] **Procedure steps reviewed**
  - [ ] Read procedure step-by-step
  - [ ] Understand each command
  - [ ] Ready to execute

- [ ] **Required tools available**
  - [ ] `git` command available
  - [ ] `python3` command available
  - [ ] `cp` / `tar` / `unzip` available
  - [ ] Sufficient disk space (check: `df -h`)

**Why Critical:** Using wrong procedure or missing tools causes rollback failure.

---

### 6. Test Plan Ready

- [ ] **Post-rollback verification plan defined**
  ```
  Will verify by:
  1. ________________________
  2. ________________________
  3. ________________________
  ```

- [ ] **Success criteria defined**
  ```
  Rollback successful if:
  1. ________________________
  2. ________________________
  ```

- [ ] **Fallback plan if rollback fails**
  ```
  If rollback fails:
  1. ________________________
  2. ________________________
  ```

**Why Critical:** Knowing how to verify success and what to do if rollback fails prevents panic.

---

## Pre-Rollback Sign-Off

**I confirm all pre-rollback checklist items are complete:**

- Date: `________________________`
- Time: `________________________`
- Operator: `________________________`
- Ready to proceed: [ ] Yes [ ] No

**If ANY item unchecked, DO NOT proceed with rollback.**

---

## During-Rollback Checklist

Monitor DURING rollback execution:

### 1. Execution Monitoring

- [ ] **Commands executing as expected**
  - No unexpected errors
  - Progress visible
  - No warnings ignored

- [ ] **File operations verified**
  - Files copying to correct locations
  - No permission errors
  - No disk space errors

- [ ] **Git operations clean** (if using git)
  - No merge conflicts
  - No detached HEAD warnings (or expected)
  - Checkout successful

### 2. Immediate Validation

- [ ] **YAML syntax validated**
  ```bash
  find .vibey/roadmap -name "*.yaml" | \
    xargs -I {} python3 -c "import yaml; yaml.safe_load(open('{}'))" && \
    echo "✅ All YAML valid"
  ```

- [ ] **File count matches expectation**
  ```bash
  find .vibey/roadmap -name "*.yaml" | wc -l
  # Expected: ________ files
  ```

- [ ] **Directory structure intact**
  ```bash
  ls -lah .vibey/roadmap/
  # Verify expected tracks present
  ```

### 3. Issue Response

- [ ] **If errors occur:**
  - [ ] STOP immediately
  - [ ] Document error message
  - [ ] Restore from current-state backup
  - [ ] Escalate / review procedure

**Why Critical:** Catching errors mid-rollback allows recovery before damage spreads.

---

## Post-Rollback Checklist

Verify AFTER rollback completes:

### 1. Roadmap Functionality

- [ ] **Roadmap status command works**
  ```bash
  python3 vibey/cli/main.py roadmap status
  # Should show tracks without errors
  ```
  - Output: [ ] Success [ ] Errors found

- [ ] **Show commands work for key tracks**
  ```bash
  python3 vibey/cli/main.py roadmap show roadmap-integrity-fixes
  python3 vibey/cli/main.py roadmap show roadmap-system
  ```
  - Track 1: [ ] Loads [ ] Errors
  - Track 2: [ ] Loads [ ] Errors

- [ ] **Complete command works (test mode)**
  ```bash
  # Don't actually complete, just verify command runs
  python3 vibey/cli/main.py roadmap complete --help
  ```
  - CLI functional: [ ] Yes [ ] No

**Why Critical:** Ensures rollback achieved goal of restoring functionality.

---

### 2. Data Integrity

- [ ] **YAML validation passes for all files**
  ```bash
  python3 scripts/validate-roadmap-schema.py
  ```
  - Files validated: `________________________`
  - Pass rate: `________________________%`
  - Errors: `________________________`

- [ ] **Track data loads without errors**
  - Tracks loaded: `________` / `________` expected
  - Sprints loaded: `________` / `________` expected
  - Tasks loaded: `________` / `________` expected

- [ ] **Progress calculations reasonable**
  - Completion percentages: [ ] Make sense [ ] Suspicious
  - Task counts: [ ] Reasonable [ ] Incorrect

- [ ] **Timestamps logical**
  - `started` before `completed`: [ ] Yes [ ] No
  - No future dates: [ ] Confirmed
  - Chronological order: [ ] Confirmed

**Why Critical:** Validates that rolled-back state is actually good, not just "different."

---

### 3. Git Status

- [ ] **Git status checked**
  ```bash
  git status
  ```
  - Status: [ ] Clean [ ] Staged changes [ ] Unstaged [ ] Issues

- [ ] **Changes are expected**
  - Changed files count: `________________________`
  - All changes are rollback-related: [ ] Yes [ ] No

- [ ] **No unexpected deletions**
  ```bash
  git status | grep deleted
  ```
  - Unexpected deletions: [ ] None [ ] Found (list: _____________)

**Why Critical:** Ensures rollback didn't accidentally modify unrelated files.

---

### 4. Rollback Documentation

- [ ] **Rollback log created**
  - File: `.vibey/roadmap/ROLLBACK_LOG_YYYY-MM-DD.md`
  - Template used: [ ] Yes
  - All sections completed: [ ] Yes

- [ ] **Rollback log contains:**
  - [ ] Timestamp and operator
  - [ ] Reason for rollback
  - [ ] Rollback type and scope
  - [ ] Source information
  - [ ] Verification results
  - [ ] Lessons learned
  - [ ] Prevention recommendations

- [ ] **Changes committed to git**
  ```bash
  git add .vibey/
  git commit -m "rollback: [description]

  Reason: [why]
  Source: [commit/checkpoint/archive]
  Verified: [verification summary]

  Rollback performed: $(date)
  "
  ```

**Why Critical:** Documentation prevents repeating same mistake and helps team understand changes.

---

### 5. Stakeholder Communication

- [ ] **Stakeholders notified of completion** (if applicable)
  - Notification sent: [ ] Yes [ ] N/A
  - Rollback successful: [ ] Confirmed
  - Services resumed: [ ] Yes [ ] N/A

- [ ] **Issues communicated** (if any)
  - [ ] Any warnings or issues documented
  - [ ] Follow-up actions identified
  - [ ] Team aware of any limitations

**Why Critical:** Closes communication loop and prevents confusion.

---

### 6. Verification Tests

Run comprehensive verification tests:

- [ ] **Test 1: Load all tracks**
  ```bash
  for track in .vibey/roadmap/*/track.yaml; do
    track_id=$(basename $(dirname $track))
    python3 vibey/cli/main.py roadmap show $track_id > /dev/null && \
      echo "✅ $track_id" || echo "❌ $track_id FAILED"
  done
  ```
  - All tracks load: [ ] Yes [ ] No (failures: _____________)

- [ ] **Test 2: Progress calculations**
  ```bash
  python3 vibey/cli/main.py roadmap status | grep "Progress:"
  ```
  - Progress numbers reasonable: [ ] Yes [ ] No

- [ ] **Test 3: Task operations**
  - Can mark task complete (test mode): [ ] Yes [ ] No
  - Can start sprint (test mode): [ ] Yes [ ] No
  - Can query tasks: [ ] Yes [ ] No

- [ ] **Test 4: No error messages**
  ```bash
  python3 vibey/cli/main.py roadmap status 2>&1 | grep -i error
  ```
  - No errors found: [ ] Confirmed
  - Errors found: [ ] Yes (investigate: _____________)

**Why Critical:** Comprehensive testing ensures rollback truly restored working state.

---

## Post-Rollback Sign-Off

**I confirm all post-rollback checklist items are complete:**

- Date: `________________________`
- Time: `________________________`
- Operator: `________________________`
- Rollback verified successful: [ ] Yes [ ] No

**If ANY critical item failed, investigate before considering rollback complete.**

---

## Checklist Compliance Tracking

### Mandatory vs. Optional Items

**Mandatory (NEVER skip):**
- ✅ Current state backup
- ✅ Rollback source verification
- ✅ Scope definition
- ✅ Post-rollback YAML validation
- ✅ Post-rollback functionality test
- ✅ Rollback documentation

**Optional (situational):**
- Stakeholder notification (if solo work)
- Git operations (if not using git)
- Some verification tests (if confidence high)

### Checklist Violations

**If you must skip a mandatory item:**

1. Document WHY in rollback log
2. Document RISK accepted
3. Document MITIGATION plan
4. Get stakeholder approval if possible

**Example:**
```markdown
## Checklist Violation

**Item Skipped:** Current state backup
**Reason:** Disk space critically low, backup would fail
**Risk Accepted:** If rollback fails, current state lost
**Mitigation:** Alternative backup to remote server completed
**Approved By:** [stakeholder]
```

---

## Quick Reference Checklist (Emergency)

If emergency rollback needed, MINIMUM checks:

1. [ ] Current state backed up somewhere (even if broken)
2. [ ] Know rollback source (git/checkpoint/archive)
3. [ ] Source verified accessible
4. [ ] Post-rollback: Commands work
5. [ ] Post-rollback: YAML valid
6. [ ] Document rollback event

**Time:** 5 minutes minimum for safety

---

## Checklist Usage Examples

### Example 1: Selective File Rollback

**Scenario:** Sprint 8 sprint.yaml incorrectly updated

**Pre-Rollback:**
- ✅ Backed up current sprint.yaml to /tmp
- ✅ Source: Git commit abc123 (verified accessible)
- ✅ Scope: 1 file only
- ✅ No stakeholder notification needed (solo work)
- ✅ Procedure 3 selected (Selective File Rollback)
- ✅ Test plan: Load sprint, verify status matches expected

**During:**
- ✅ Git checkout executed successfully
- ✅ File restored to correct location
- ✅ YAML syntax valid

**Post-Rollback:**
- ✅ `roadmap show sprint-8` works
- ✅ Sprint status shows expected value
- ✅ YAML validation passed
- ✅ Git status shows 1 file modified (expected)
- ✅ Rollback documented
- ✅ Changes committed

**Result:** ✅ Rollback successful, all checks passed

---

### Example 2: Emergency Full Rollback

**Scenario:** Roadmap completely broken, nothing loads

**Pre-Rollback:**
- ✅ Backed up current .vibey/ to /tmp (even though broken)
- ✅ Source: Checkpoint /tmp/vibey-checkpoint-20251115
- ✅ Checkpoint verified (YAML valid)
- ✅ Scope: Full .vibey/roadmap/
- ⚠️ Stakeholders notified: "Emergency rollback in progress"
- ✅ Procedure 2 selected (Checkpoint Restoration)
- ✅ Test plan: Roadmap status command must work

**During:**
- ✅ Checkpoint copied successfully
- ✅ All files restored
- ✅ Directory structure intact

**Post-Rollback:**
- ✅ `roadmap status` works! 20 tracks loaded
- ✅ Random track queries work
- ✅ YAML validation: 462/462 files pass
- ✅ Git status: Staged changes (expected)
- ✅ Rollback log created
- ✅ Changes committed
- ✅ Stakeholders notified: "Rollback complete, services restored"

**Result:** ✅ Emergency rollback successful, 5 minutes total time

---

## Appendix: Validation Commands

### Quick YAML Validation

```bash
# Validate all roadmap YAML files
find .vibey/roadmap -name "*.yaml" | while read f; do
  python3 -c "import yaml; yaml.safe_load(open('$f'))" 2>/dev/null || echo "❌ $f"
done
```

### Quick Functionality Test

```bash
# Test roadmap commands
python3 vibey/cli/main.py roadmap status && \
  echo "✅ Status works" || echo "❌ Status broken"
```

### Quick File Count

```bash
# Count YAML files (should match expected)
find .vibey/roadmap -name "*.yaml" | wc -l
```

---

## Checklist Maintenance

**This checklist should be updated when:**

- New rollback procedures added
- New validation tools created
- Rollback failures reveal missing checks
- Team feedback identifies gaps

**Review Schedule:** After each rollback event or quarterly

**Last Reviewed:** 2025-11-20
**Next Review:** 2026-02-20 or after next rollback

---

**Checklist Version:** 1.0
**Last Updated:** 2025-11-20
**Companion Documents:**
- ROLLBACK_PROCEDURES.md - Detailed procedures
- ROLLBACK_DECISION_TREE.md - Procedure selection guide
