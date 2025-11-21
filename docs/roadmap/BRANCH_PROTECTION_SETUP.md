# Branch Protection Setup Guide

**Created:** 2025-11-21
**Sprint:** roadmap-integrity-fixes-6
**Task:** roadmap-integrity-fixes-6-task-006
**Related:** CI/CD Validation Pipeline

---

## Overview

This guide shows how to configure GitHub branch protection rules to enforce roadmap validation before merging pull requests. Combined with the pre-commit hook and CI/CD validation, this creates a multi-layered defense against data corruption.

### Protection Layers

1. **Pre-commit Hook** (Local) - Catches issues before commit
2. **CI/CD Validation** (GitHub Actions) - Validates on push/PR
3. **Branch Protection** (GitHub) - Blocks merge if validation fails

---

## Branch Protection Rules

### Required Checks

Configure the following status checks as **required** before merging:

#### Primary Validation (Blocking)
- ✅ `fast-validation` - Fast syntax and schema validation
- ✅ `advanced-validation` - Comprehensive integrity checks

#### Secondary Checks (Optional)
- ⚠️ `auto-repair-check` - Shows what can be auto-fixed (runs only on failure)
- ⚠️ `legacy-validation` - Legacy pytest validation (non-blocking)

---

## Setup Instructions

### Step 1: Access Repository Settings

1. Go to your GitHub repository
2. Click **Settings** tab
3. Click **Branches** in left sidebar
4. Find **Branch protection rules** section

### Step 2: Add Branch Protection Rule

1. Click **Add rule** or **Add branch protection rule**
2. **Branch name pattern:** `main`
3. Configure protection settings (see below)

### Step 3: Configure Protection Settings

#### Require Pull Request Reviews
- ☑ **Require a pull request before merging**
  - **Required approving reviews:** 1 (adjust for your team)
  - ☑ **Dismiss stale pull request approvals when new commits are pushed**
  - ☐ **Require review from Code Owners** (optional)

#### Require Status Checks
- ☑ **Require status checks to pass before merging**
  - ☑ **Require branches to be up to date before merging**
  - **Status checks that are required:**
    - `fast-validation`
    - `advanced-validation`

#### Additional Settings
- ☑ **Require conversation resolution before merging** (recommended)
- ☑ **Require signed commits** (optional, for security)
- ☐ **Require linear history** (optional)
- ☐ **Include administrators** (recommended - enforces rules on everyone)
- ☐ **Allow force pushes** (NOT recommended)
- ☐ **Allow deletions** (NOT recommended)

### Step 4: Save Changes

1. Scroll to bottom
2. Click **Create** (or **Save changes**)
3. Branch protection is now active!

---

## Validation Flow with Branch Protection

### Pull Request Workflow

```
Developer creates PR
    ↓
GitHub Actions triggered
    ↓
Fast Validation runs (5 min timeout)
    ↓
PASS? → Advanced Validation runs (10 min timeout)
    ↓
PASS? → PR can be merged ✅
    ↓
FAIL? → Auto-Repair Check runs
         → Shows fixable issues in PR comment
         → PR blocked until fixed ❌
```

### Example PR Timeline

1. **Developer pushes to PR branch**
   ```
   12:00 PM - Push received
   12:00 PM - Fast validation: Running...
   12:01 PM - Fast validation: ✅ Passed
   12:01 PM - Advanced validation: Running...
   12:02 PM - Advanced validation: ✅ Passed
   12:02 PM - All checks have passed
   ```

2. **Merge Button Status**
   - ✅ **Green "Merge pull request" button** - Ready to merge
   - ❌ **Gray "Merge pull request" button** - Blocked by protection rules

---

## Testing Branch Protection

### Create a Test PR

```bash
# 1. Create test branch
git checkout -b test-branch-protection

# 2. Make a valid change
echo "test: $(date)" >> .vibey/roadmap/README.md
git add .vibey/roadmap/README.md
git commit -m "test: valid roadmap change"

# 3. Push and create PR
git push origin test-branch-protection
gh pr create --title "Test: Branch Protection" --body "Testing validation workflow"
```

### Verify Protection Works

1. **Check PR page on GitHub**
   - Should see "All checks have passed" ✅
   - Merge button should be enabled

2. **Try to merge without checks**
   - If checks haven't run yet, merge button should be disabled
   - Should show "Merging is blocked" with reason

### Test with Invalid Data

```bash
# 1. Make invalid change (corrupt YAML)
echo "invalid: yaml: : syntax:" >> .vibey/roadmap/test/track.yaml
git add .vibey/roadmap/test/track.yaml
git commit -m "test: invalid change"
git push

# 2. Watch validation fail
# - Fast validation should fail
# - Advanced validation won't run (depends on fast)
# - Auto-repair check should run and comment on PR

# 3. Verify merge is blocked
# - Merge button should be disabled
# - Should show "Required status checks have not passed"
```

---

## Troubleshooting

### Issue: Merge Button Still Enabled Despite Failing Checks

**Cause:** Status checks not configured as required

**Solution:**
1. Go to Settings → Branches → Branch protection rules
2. Edit `main` branch rule
3. Ensure checkboxes next to status check names are ✅ checked
4. Save changes

### Issue: Status Checks Not Appearing

**Cause:** Workflow hasn't run yet or status check names don't match

**Solution:**
1. Create a test PR to trigger workflow
2. Wait for checks to complete
3. Check exact names in GitHub Actions tab
4. Update branch protection to use exact names:
   - `fast-validation` (not "Fast Validation")
   - `advanced-validation` (not "Advanced Validation")

### Issue: Checks Pass Locally But Fail in CI

**Cause:** Environment differences

**Solutions:**
```bash
# Run same validation CI uses
pip install -e .
python -m vibey.cli.main roadmap validate-fast --profile standard --verbose
python -m vibey.cli.main roadmap validate-advanced --verbose

# Check Python version matches CI
python --version  # Should be 3.12
```

### Issue: All Checks Required But Want to Merge Anyway

**Temporary Override (Admins Only):**
1. Go to PR page
2. Scroll to merge button
3. Click "Details" next to failing check
4. If you're an admin and "Include administrators" is unchecked:
   - You can bypass protection rules
   - **Not recommended** - fix the validation errors instead

**Permanent Fix:**
- Fix validation errors
- Or remove check from required list (not recommended)

---

## Advanced Configuration

### Multiple Protected Branches

Protect `develop` branch in addition to `main`:

1. Add another branch protection rule
2. **Branch name pattern:** `develop`
3. Use same settings as `main`

### Pattern Matching for Feature Branches

Protect all `release/*` branches:

1. **Branch name pattern:** `release/*`
2. Use same validation requirements

### Different Rules for Different Branches

Example: Stricter rules for `main`:

**For `main` branch:**
- Required reviews: 2
- Required checks: fast-validation, advanced-validation
- Include administrators: Yes

**For `develop` branch:**
- Required reviews: 1
- Required checks: fast-validation only
- Include administrators: No

---

## Status Check Configuration Reference

### Job Names in Workflow

From `.github/workflows/roadmap-validation.yml`:

```yaml
jobs:
  fast-validation:          # Status check name: "fast-validation"
    name: Fast Validation (Syntax & Schema)

  advanced-validation:      # Status check name: "advanced-validation"
    name: Advanced Validation (Integrity Checks)

  auto-repair-check:        # Status check name: "auto-repair-check"
    name: Auto-Repair Feasibility Check

  legacy-validation:        # Status check name: "legacy-validation"
    name: Legacy Validation (Pytest)
```

### Required vs Optional Checks

**Required (Blocking):**
- `fast-validation` - Must pass for merge
- `advanced-validation` - Must pass for merge

**Optional (Informational):**
- `auto-repair-check` - Only runs on failure, shows repair options
- `legacy-validation` - continue-on-error, doesn't block

---

## Integration with Teams

### Code Review Workflow

1. **Developer creates PR**
   - Validation runs automatically
   - Results appear as PR checks

2. **Validation fails**
   - Auto-repair comment shows fixable issues
   - Developer fixes locally
   - Push triggers re-validation

3. **Validation passes**
   - Request review from team member
   - Reviewer approves if changes look good
   - Merge button enables

4. **Merge to main**
   - Protected branch accepts only validated code
   - Roadmap integrity maintained

### Notification Settings

Configure GitHub notifications:

1. **Settings → Notifications**
2. **Participating and @mentions:**
   - ☑ Pull requests
   - ☑ Issues and PRs reviews
3. **Watching repositories:**
   - Choose notification level for roadmap updates

### Slack Integration (Optional)

Get validation results in Slack:

1. Install **GitHub app** for Slack
2. Configure channel: `/github subscribe owner/repo`
3. Enable PR notifications:
   ```
   /github subscribe owner/repo pulls
   /github subscribe owner/repo commits:main
   ```

---

## Maintenance

### Updating Protection Rules

1. **When adding new validation checks:**
   - Add job to workflow
   - Wait for it to run once
   - Add to required checks in branch protection

2. **When removing validations:**
   - Remove from required checks first
   - Then remove from workflow (optional)

3. **Periodic review:**
   - Review protection rules quarterly
   - Ensure they match current validation capabilities
   - Update documentation if rules change

### Monitoring Effectiveness

**Metrics to track:**
- Number of PRs blocked by validation
- Types of issues caught (syntax vs integrity)
- Time to fix validation failures
- False positive rate

**Review questions:**
- Are checks too strict? (too many false positives)
- Are checks too lenient? (issues slipping through)
- Are timeouts appropriate?
- Are developers bypassing validation?

---

## Best Practices

### Do's ✅

- ✅ Require both fast and advanced validation
- ✅ Keep checks up-to-date with validation capabilities
- ✅ Test protection rules with dummy PRs
- ✅ Document bypass procedures for emergencies
- ✅ Include administrators in protection rules
- ✅ Review and update rules quarterly

### Don'ts ❌

- ❌ Don't allow force pushes to protected branches
- ❌ Don't disable checks to "save time"
- ❌ Don't bypass protection without documenting why
- ❌ Don't have different rules for admins/developers
- ❌ Don't ignore failing validation in favor of merging
- ❌ Don't remove checks without team discussion

---

## Emergency Procedures

### When Validation Incorrectly Blocks Valid PR

1. **Verify the issue:**
   ```bash
   # Run validation locally
   vibey roadmap validate-fast --verbose
   vibey roadmap validate-advanced --verbose
   ```

2. **If validation bug confirmed:**
   - Create issue documenting the bug
   - Temporarily remove problematic check from required list
   - Merge PR
   - Fix validation bug
   - Re-add check to required list

3. **If urgent hotfix needed:**
   - Get approval from tech lead
   - Admin temporarily disables protection
   - Merge with `--no-verify`
   - Re-enable protection immediately
   - Document in commit message why protection was bypassed

### When CI/CD System Is Down

1. **Check GitHub Status:** https://www.githubstatus.com/
2. **If GitHub Actions down:**
   - Temporarily remove required checks
   - Use pre-commit hooks only
   - Document all merges during outage
   - Re-validate after system recovery
   - Re-enable protection rules

---

## Related Documentation

- [CI/CD Validation](./CI_CD_VALIDATION.md) - GitHub Actions workflow details
- [Pre-Commit Hooks](./PRE_COMMIT_HOOKS.md) - Local validation setup
- [Validation Rules](./VALIDATION_RULES.md) - What gets validated
- [Auto-Repair Guide](./ADVANCED_VALIDATION_AND_REPAIR.md) - Fixing validation errors

---

**Version:** 1.0.0
**Last Updated:** 2025-11-21
**Maintainer:** Vibey Framework Team
