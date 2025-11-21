# CI/CD Validation Pipeline

**Created:** 2025-11-21
**Sprint:** roadmap-integrity-fixes-6
**Task:** roadmap-integrity-fixes-6-task-006
**Status:** ✅ Production Ready

---

## Overview

The CI/CD validation pipeline automatically validates roadmap data on every push and pull request using GitHub Actions. This provides team-wide enforcement of data integrity standards, catching issues before they reach the main branch.

### Key Features

- ✅ **Automated Validation** - Runs on every push/PR
- ✅ **Multi-Level Checks** - Fast syntax + Advanced integrity
- ✅ **PR Comments** - Auto-repair suggestions posted to PRs
- ✅ **Blocking Merges** - Prevents invalid data from being merged
- ✅ **Artifact Storage** - Validation reports saved for 30 days
- ✅ **Performance Optimized** - Fast validation completes in <1 minute

---

## Pipeline Architecture

### Workflow Jobs

```
┌─────────────────────────┐
│  fast-validation        │  (5 min timeout)
│  - YAML syntax          │
│  - Schema compliance    │
│  - Basic integrity      │
└───────────┬─────────────┘
            │ SUCCESS
            ↓
┌─────────────────────────┐
│  advanced-validation    │  (10 min timeout)
│  - Circular dependencies│
│  - Orphaned tasks       │
│  - Broken references    │
│  - Progress counters    │
└───────────┬─────────────┘
            │ FAILURE
            ↓
┌─────────────────────────┐
│  auto-repair-check      │  (5 min timeout)
│  - Dry-run repair       │
│  - Show fixable issues  │
│  - Comment on PR        │
└─────────────────────────┘

Parallel:
┌─────────────────────────┐
│  legacy-validation      │  (non-blocking)
│  - Pytest tests         │
│  - Python serialization │
└─────────────────────────┘
```

### Trigger Conditions

**Runs when:**
- Code pushed to `main` or `develop` branches
- Pull requests targeting `main` or `develop`
- Files in `.vibey/roadmap/**` modified
- Files in `vibey/operations/roadmap/**` modified
- Files in `vibey/cli/**` modified

**Does NOT run when:**
- Changes only to documentation (outside roadmap)
- Changes only to tests
- Changes to other code

---

## Job Details

### Job 1: Fast Validation

**Purpose:** Quick syntax and schema validation

**Runs:** Always (on roadmap changes)

**Steps:**
1. Checkout code
2. Set up Python 3.12
3. Install Vibey framework
4. Run `vibey roadmap validate-fast --profile standard --verbose`
5. Cache validation results

**Success Criteria:**
- All YAML files have valid syntax
- All files load successfully
- Basic schema compliance

**Failure Handling:**
- Job fails immediately
- Subsequent jobs don't run
- PR merge blocked

**Duration:** ~60 seconds (470 files)

### Job 2: Advanced Validation

**Purpose:** Comprehensive integrity checks

**Runs:** After fast-validation succeeds

**Steps:**
1. Checkout code
2. Set up Python 3.12
3. Install Vibey framework
4. Run `vibey roadmap validate-advanced --verbose`
5. Parse output and extract issue counts
6. Create validation summary
7. Upload validation report as artifact
8. Comment on PR if issues found
9. Fail job if issues detected

**Checks:**
- Circular dependency detection
- Orphaned task detection
- Broken reference detection
- Progress counter validation

**Success Criteria:**
- Zero circular dependencies
- Zero orphaned tasks
- Zero broken references
- Zero progress mismatches

**Failure Handling:**
- Creates detailed summary
- Posts comment on PR with issue breakdown
- Triggers auto-repair-check job
- Fails job (blocks merge)

**Duration:** ~120 seconds (387 tasks)

### Job 3: Auto-Repair Check

**Purpose:** Show what can be automatically fixed

**Runs:** Only when advanced-validation fails

**Steps:**
1. Checkout code
2. Set up Python 3.12
3. Install Vibey framework
4. Run `vibey roadmap repair --all --dry-run`
5. Create repair summary
6. Upload repair preview as artifact
7. Comment on PR with repair instructions

**Output:**
- List of auto-fixable issues
- Commands to apply repairs
- Suggestions for manual fixes

**Success Criteria:**
- Always succeeds (informational only)

**Duration:** ~30 seconds

### Job 4: Legacy Validation

**Purpose:** Run legacy pytest-based tests

**Runs:** In parallel with other jobs

**Steps:**
1. Checkout code
2. Set up Python 3.12
3. Install pytest and dependencies
4. Run `pytest tests/validation/test_yaml_integrity.py`
5. Check for Python serialization in YAML

**Success Criteria:**
- Informational only (continue-on-error: true)
- Does not block merge

**Duration:** ~90 seconds

---

## Workflow File

**Location:** `.github/workflows/roadmap-validation.yml`

**Key Configuration:**

```yaml
name: Roadmap Validation

on:
  push:
    branches: [main, develop]
    paths:
      - '.vibey/roadmap/**'
      - 'vibey/operations/roadmap/**'
      - 'vibey/cli/**'
  pull_request:
    branches: [main, develop]
    paths:
      - '.vibey/roadmap/**'
      - 'vibey/operations/roadmap/**'
      - 'vibey/cli/**'

jobs:
  fast-validation:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Run fast validation
        run: python -m vibey.cli.main roadmap validate-fast --profile standard --verbose

  advanced-validation:
    needs: fast-validation
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Run advanced validation
        run: python -m vibey.cli.main roadmap validate-advanced --verbose

  auto-repair-check:
    needs: advanced-validation
    if: failure()
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Check what can be auto-repaired
        run: python -m vibey.cli.main roadmap repair --all --dry-run
```

---

## PR Integration

### Validation Success

When all checks pass:

```
✅ All checks have passed

Fast Validation (Syntax & Schema) — Required
  ✅ Passed in 58s

Advanced Validation (Integrity Checks) — Required
  ✅ Passed in 2m 15s

Merge pull request
```

### Validation Failure

When validation finds issues:

```
❌ Some checks were not successful

Fast Validation (Syntax & Schema) — Required
  ✅ Passed in 1m 02s

Advanced Validation (Integrity Checks) — Required
  ❌ Failed in 2m 30s

Auto-Repair Feasibility Check
  ✅ Passed in 28s

This branch has conflicts that must be resolved
Merging is blocked
```

**PR Comment (Auto-posted):**

```markdown
## 🔍 Advanced Validation Results

**Status:** ❌ Issues detected

### Issue Summary

- 🔄 Circular dependencies: 0
- 👻 Orphaned tasks: 0
- 🔗 Broken references: 3
- 📊 Progress mismatches: 5

### Details

See full validation output below:

\`\`\`
Running advanced validation checks...

⚠️  Issues detected: 8

🔗 Broken References: 3

1. Task roadmap-system-2-task-005 references non-existent task...

📊 Progress Counter Mismatches: 5

1. Sprint platform-context-5: claimed 0/6 but actual 0/0
...
\`\`\`

---

## 🔧 Auto-Repair Preview

The following issues can be automatically repaired:

\`\`\`
Found 5 issues:
  📊 Progress counter mismatches: 5 (auto-fixable)

Would fix 5 progress counter mismatches:
  1. platform-context-management-5
     Claimed: 0/6
     Actual:  0/0
...
\`\`\`

**To apply repairs:**
\`\`\`bash
vibey roadmap repair --progress  # Fix progress counters only
vibey roadmap repair --all       # Fix all issues (with confirmation)
\`\`\`
```

---

## Artifacts

### Validation Reports

**Uploaded on every run:**

1. **advanced-validation-report/**
   - `validation-output.txt` - Full validation output
   - `validation-summary.md` - Formatted summary

2. **auto-repair-preview/** (only on failure)
   - `repair-summary.md` - Auto-repair instructions

**Retention:** 30 days

**Access:**
1. Go to PR or commit page
2. Scroll to checks section
3. Click "Details" on any validation job
4. Click "Summary" tab
5. Download artifacts from "Artifacts" section

---

## Local Reproduction

### Run Exact Same Validation as CI

```bash
# 1. Install Vibey framework
pip install -e .

# 2. Run fast validation (same as CI)
python -m vibey.cli.main roadmap validate-fast --profile standard --verbose

# 3. Run advanced validation (same as CI)
python -m vibey.cli.main roadmap validate-advanced --verbose

# 4. Check auto-repair (same as CI)
python -m vibey.cli.main roadmap repair --all --dry-run
```

### Debug CI Failures

```bash
# Check Python version matches CI
python --version  # Should be 3.12+

# Ensure dependencies installed
pip install -e .

# Run validation with verbose output
python -m vibey.cli.main roadmap validate-advanced --verbose 2>&1 | tee validation.log

# Check for environment differences
env | grep VIBEY
```

---

## Performance Optimization

### Current Performance

| Job | Files | Duration | Target |
|-----|-------|----------|--------|
| Fast validation | 470 | ~60s | <5 min |
| Advanced validation | 387 tasks | ~120s | <10 min |
| Auto-repair check | N/A | ~30s | <5 min |
| Legacy validation | N/A | ~90s | <10 min |

**Total pipeline duration:** ~3-4 minutes (parallel jobs)

### Optimization Strategies

1. **Caching:**
   - Python dependencies cached
   - Validation cache saved (future enhancement)

2. **Incremental Validation:**
   - Only validate changed files (future enhancement)
   - Use `--incremental` flag

3. **Parallel Execution:**
   - Fast and legacy validation run in parallel
   - Advanced waits for fast (dependency chain)

4. **Timeout Management:**
   - Conservative timeouts prevent hung jobs
   - Can be reduced as validation optimizes

---

## Monitoring and Alerts

### GitHub Status Checks

View all validation runs:
1. Repository → Actions tab
2. Filter by "Roadmap Validation"
3. See success/failure history

### Email Notifications

Configure in **Settings → Notifications:**
- ☑ Actions: Enable notifications for failed workflows
- ☑ Pull requests: Get notified when checks complete

### Slack Integration

Post validation results to Slack:

```bash
# Install GitHub app for Slack
/github subscribe owner/repo pulls reviews comments
/github subscribe owner/repo pulls statuses
```

### Metrics to Track

- **Pass rate:** % of PRs passing validation first try
- **Common failures:** Types of issues caught
- **Time to fix:** How long to resolve validation errors
- **False positives:** Incorrect validation failures

---

## Troubleshooting

### Workflow Not Triggering

**Problem:** Push doesn't trigger validation

**Checks:**
```bash
# 1. Verify you changed roadmap files
git diff --name-only HEAD~1 HEAD | grep ".vibey/roadmap"

# 2. Check branch matches trigger condition
git branch --show-current  # Should be 'main' or 'develop' for push triggers

# 3. View workflow file
cat .github/workflows/roadmap-validation.yml
```

**Solutions:**
- Ensure you're pushing to `main` or `develop`
- Ensure roadmap files are modified
- Check workflow paths match your changes

### Validation Passes Locally But Fails in CI

**Common causes:**

1. **Environment differences:**
   ```bash
   # Match CI environment
   python --version  # Use 3.12
   pip install -e .  # Use editable install
   ```

2. **Cached files locally:**
   ```bash
   # Clear local caches
   rm -rf ~/.vibey-validation-cache
   git clean -fdx  # Nuclear option
   ```

3. **Uncommitted changes:**
   ```bash
   # Ensure all changes committed
   git status
   git diff
   ```

### Validation Times Out

**Problem:** Job exceeds timeout (5-10 min)

**Solutions:**

1. **Increase timeout:**
   ```yaml
   # In .github/workflows/roadmap-validation.yml
   timeout-minutes: 15  # Increase from 10
   ```

2. **Optimize roadmap:**
   - Reduce number of tasks
   - Simplify dependency chains
   - Archive completed tracks

3. **Use faster profile:**
   ```yaml
   # Change to quick profile
   run: python -m vibey.cli.main roadmap validate-fast --profile quick
   ```

### Permission Errors

**Problem:** `Permission denied` or `403 Forbidden`

**Solution:**
```yaml
# Add permissions to workflow
permissions:
  contents: read
  pull-requests: write  # For PR comments
  statuses: write       # For status checks
```

---

## Advanced Configuration

### Custom Validation Profiles

Edit workflow to use different profiles:

```yaml
# Quick profile (syntax only, <1 min)
run: python -m vibey.cli.main roadmap validate-fast --profile quick

# Standard profile (recommended, ~1 min)
run: python -m vibey.cli.main roadmap validate-fast --profile standard

# Thorough profile (with git integration, ~2 min)
run: python -m vibey.cli.main roadmap validate-fast --profile thorough
```

### Selective Validation

Validate only specific checks:

```yaml
# Only check for circular dependencies
- name: Check circular dependencies
  run: python -m vibey.cli.main roadmap validate-advanced --check circular

# Only check progress counters
- name: Check progress counters
  run: python -m vibey.cli.main roadmap validate-advanced --check progress
```

### Matrix Testing

Test across multiple Python versions:

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']

steps:
  - uses: actions/setup-python@v5
    with:
      python-version: ${{ matrix.python-version }}
```

### Scheduled Validation

Run validation daily even without changes:

```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight UTC
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
```

---

## Security Considerations

### Secrets and Credentials

- ✅ No secrets required for basic validation
- ✅ GitHub token auto-provided for PR comments
- ✅ No external API calls

### Permissions

Minimal permissions required:

```yaml
permissions:
  contents: read          # Read repository files
  pull-requests: write    # Comment on PRs
  statuses: write         # Update status checks
```

### Dependency Security

```yaml
# Pin action versions for security
- uses: actions/checkout@v4  # Not @main
- uses: actions/setup-python@v5  # Not @latest
```

---

## Best Practices

### Do's ✅

- ✅ Keep validation fast (<5 min)
- ✅ Use specific job names for required checks
- ✅ Upload artifacts for debugging
- ✅ Comment on PRs with actionable feedback
- ✅ Test workflow changes in feature branch first
- ✅ Monitor validation performance regularly

### Don'ts ❌

- ❌ Don't make all jobs blocking (use continue-on-error for optional checks)
- ❌ Don't ignore timeout warnings
- ❌ Don't use `continue-on-error` on critical validation
- ❌ Don't commit workflow changes without testing
- ❌ Don't increase timeouts without investigating root cause
- ❌ Don't bypass failed validation to "save time"

---

## Migration from Legacy Validation

If you have existing pytest-based validation:

1. **Keep legacy validation as non-blocking:**
   ```yaml
   legacy-validation:
     continue-on-error: true
   ```

2. **Add new CLI-based validation:**
   ```yaml
   fast-validation:
     continue-on-error: false  # Blocking
   ```

3. **Monitor both for 2 weeks:**
   - Compare results
   - Fix any discrepancies
   - Ensure new validation is comprehensive

4. **Remove legacy validation:**
   - Once confident in new validation
   - Archive old pytest tests
   - Update documentation

---

## Related Documentation

- [Branch Protection Setup](./BRANCH_PROTECTION_SETUP.md) - Configure required checks
- [Pre-Commit Hooks](./PRE_COMMIT_HOOKS.md) - Local validation
- [Auto-Repair Guide](./ADVANCED_VALIDATION_AND_REPAIR.md) - Fixing validation errors
- [Validation Rules](./VALIDATION_RULES.md) - What gets validated

---

**Version:** 1.0.0
**Last Updated:** 2025-11-21
**Maintainer:** Vibey Framework Team
