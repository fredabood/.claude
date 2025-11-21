# Roadmap Validation Best Practices

**Created:** 2025-11-21
**Sprint:** roadmap-integrity-fixes-6
**Status:** ✅ Production Ready

---

## Overview

This guide provides recommended workflows and best practices for maintaining roadmap data quality using the Vibey validation system. Following these practices ensures high data integrity, prevents common errors, and maximizes team productivity.

---

## Core Principles

### 1. **Use CLI Commands, Not Manual YAML Edits**

**✅ DO:**
```bash
# Start a task
vibey roadmap start roadmap-system-1-task-001

# Complete a task
vibey roadmap complete roadmap-system-1-task-001
```

**❌ DON'T:**
```bash
# Manually edit YAML
vim .vibey/roadmap/roadmap-system/roadmap-system-1/task-001/task.yaml
# Change status: in_progress → completed
```

**Why:**
- CLI commands log to audit trail automatically
- CLI ensures data consistency
- CLI validates changes before saving
- Manual edits bypass all safety checks

**Exception:**
- Bulk operations not yet supported by CLI
- Emergency fixes (document in commit message)

---

### 2. **Validate Before Commit**

**✅ DO:**
```bash
# Make changes
vibey roadmap complete task-001

# Validate before committing
vibey roadmap validate-fast --profile standard

# If validation passes, commit
git add .vibey/roadmap/
git commit -m "Complete task-001"
```

**❌ DON'T:**
```bash
# Make changes and commit without validating
git add .vibey/roadmap/
git commit -m "Update roadmap"  # Might fail pre-commit hook!
```

**Why:**
- Catches errors early (before hook)
- Faster feedback than waiting for hook
- Allows fixing issues before commit

---

### 3. **Review Audit Trail Regularly**

**✅ DO:**
```bash
# Daily: Check recent changes
vibey roadmap audit log

# Weekly: Check for suspicious changes
vibey roadmap audit suspicious

# Monthly: Generate full report
vibey roadmap audit report --start $(date -d '30 days ago' +%Y-%m-%d)
```

**❌ DON'T:**
- Never check audit trail
- Ignore suspicious change warnings
- Assume all changes are valid

**Why:**
- Detects manual edits
- Catches status rollbacks
- Provides accountability
- Identifies patterns of errors

---

## Development Workflow

### Starting Work

```bash
# 1. Pull latest changes
git pull origin main

# 2. Validate current state
vibey roadmap validate-fast --profile standard

# 3. Start your task
vibey roadmap start <task-id>

# 4. Verify task started
vibey roadmap show <task-id>
```

### During Work

```bash
# 1. Make code changes
# ... write code, tests, docs ...

# 2. Add commits to task (optional)
vibey roadmap add-commit <task-id> --sha $(git rev-parse HEAD)

# 3. Validate frequently
vibey roadmap validate-fast --profile quick
```

### Completing Work

```bash
# 1. Ensure all changes committed
git status

# 2. Run full validation
vibey roadmap validate-fast --profile standard
vibey roadmap validate-advanced

# 3. Complete task
vibey roadmap complete <task-id>

# 4. Commit roadmap updates
git add .vibey/roadmap/
git commit -m "Complete <task-id>"

# 5. Push
git push origin <branch>
```

---

## Pre-Commit Hook Workflow

### Installation (One-Time Setup)

```bash
# Install hook
vibey roadmap install-hooks

# Verify installation
vibey roadmap check-hooks

# Optional: Enable advanced validation
echo 'export VIBEY_HOOK_ADVANCED=true' >> ~/.bashrc
source ~/.bashrc
```

### Daily Usage

**Normal commits (no roadmap changes):**
```bash
git commit -m "Update README"
# Hook doesn't run - no roadmap files changed
```

**Roadmap commits:**
```bash
git add .vibey/roadmap/
git commit -m "Complete task-001"
# Hook runs automatically, validates, allows commit if valid
```

**When validation fails:**
```bash
git commit -m "Update sprint"
# ❌ Fast validation failed!
# Fix the validation errors above before committing.

# Fix errors
vibey roadmap repair --all

# Retry commit
git commit -m "Update sprint"
# ✅ Validation passed, commit succeeds
```

**Emergency bypass (rare):**
```bash
# Only use when validation has a bug or urgent hotfix needed
git commit --no-verify -m "Emergency: bypass validation"

# Document why in commit message
# File issue for validation bug
# Fix data after emergency
```

---

## CI/CD Workflow

### Pull Request Process

**1. Create feature branch:**
```bash
git checkout -b feature/add-new-track
```

**2. Make changes using CLI:**
```bash
vibey roadmap start my-track-1-task-001
# ... do work ...
vibey roadmap complete my-track-1-task-001
```

**3. Validate locally:**
```bash
vibey roadmap validate-fast --profile standard
vibey roadmap validate-advanced
```

**4. Commit and push:**
```bash
git add .vibey/roadmap/
git commit -m "feat: Complete task-001"
git push origin feature/add-new-track
```

**5. Create PR:**
```bash
gh pr create --title "Complete task-001" --body "..."
```

**6. Wait for CI/CD:**
- Fast validation runs (~1 min)
- Advanced validation runs (~2 min)
- If failures, auto-repair suggestions posted

**7. Fix validation errors if needed:**
```bash
# Pull latest (may have auto-suggestions)
git pull origin feature/add-new-track

# Apply repairs
vibey roadmap repair --all

# Commit fixes
git add .vibey/roadmap/
git commit -m "fix: Apply validation repairs"
git push
```

**8. Merge when green:**
- All validation checks passed ✅
- Merge button enabled
- Data integrity guaranteed

---

## Team Collaboration

### Shared Roadmap Updates

**✅ DO:**
```bash
# Before making changes
git pull origin main
vibey roadmap validate-fast

# Make atomic changes
vibey roadmap start task-001
git add .vibey/roadmap/
git commit -m "Start task-001"
git push

# After teammate's changes
git pull origin main
vibey roadmap validate-fast  # Verify their changes didn't break anything
```

**❌ DON'T:**
```bash
# Making large batch changes without pulling
# ... edit 50 files ...
git commit -m "Update all roadmap"
git push  # Likely to conflict!
```

**Why:**
- Prevents merge conflicts
- Catches errors early
- Maintains team awareness

### Code Review Checklist

**Reviewer should verify:**

- [ ] All validation checks passed in CI/CD
- [ ] Audit trail shows CLI operations (not manual edits)
- [ ] Status changes have clear reasons
- [ ] No suspicious changes flagged
- [ ] Progress counters accurate
- [ ] No manual YAML edits without justification

**Review command:**
```bash
# Check what changed
vibey roadmap audit show <object-id>

# Verify validation passed
# (Check GitHub PR checks)

# Look for manual edits
git log --oneline .vibey/roadmap/
```

---

## Maintenance Tasks

### Daily Maintenance

```bash
# Check recent changes
vibey roadmap audit log

# Quick validation
vibey roadmap validate-fast --profile quick
```

### Weekly Maintenance

```bash
# Full validation
vibey roadmap validate-advanced

# Check for suspicious changes
vibey roadmap audit suspicious

# Review audit trail
vibey roadmap audit log --limit 100
```

### Monthly Maintenance

```bash
# Generate audit report
vibey roadmap audit report --start $(date -d '30 days ago' +%Y-%m-%d)

# Archive old audit entries (if large)
# (Future feature)

# Review validation metrics
# - How many PRs failed validation?
# - What are common error types?
# - Is team following best practices?
```

---

## Error Prevention Checklist

### Pre-Work Checklist

- [ ] Pulled latest changes (`git pull`)
- [ ] Validated current state (`vibey roadmap validate-fast`)
- [ ] Identified task to work on
- [ ] Started task via CLI (`vibey roadmap start <task-id>`)

### During-Work Checklist

- [ ] Using CLI commands for status changes
- [ ] Validating frequently (`vibey roadmap validate-fast`)
- [ ] Committing atomic changes
- [ ] Adding meaningful commit messages

### Post-Work Checklist

- [ ] Ran full validation (`vibey roadmap validate-advanced`)
- [ ] Completed task via CLI (`vibey roadmap complete <task-id>`)
- [ ] Committed roadmap updates
- [ ] Pushed to remote
- [ ] Verified CI/CD checks pass

### Code Review Checklist

- [ ] Validation checks passed in CI/CD
- [ ] Audit trail shows proper CLI usage
- [ ] No suspicious changes detected
- [ ] Progress counters accurate
- [ ] Manual edits justified (if any)

---

## Common Pitfalls

### Pitfall 1: Editing YAML Directly

**Problem:**
```bash
vim .vibey/roadmap/track-1/sprint.yaml
# Manually change status
git commit -m "Update status"
```

**Why it's bad:**
- No audit trail
- No validation
- Easy to introduce errors
- Flagged as suspicious change

**Solution:**
```bash
# Use CLI instead
vibey roadmap complete track-1
```

---

### Pitfall 2: Skipping Validation

**Problem:**
```bash
# Make changes
git add .
git commit --no-verify -m "Quick fix"
```

**Why it's bad:**
- Bypasses all checks
- May introduce invalid data
- Breaks CI/CD later
- No safety net

**Solution:**
```bash
# Let validation run
git add .
git commit -m "Fix issue"
# Hook validates automatically
```

---

### Pitfall 3: Ignoring Suspicious Changes

**Problem:**
```bash
vibey roadmap audit suspicious
# ⚠️  Status rollback detected
# ... ignore warning ...
```

**Why it's bad:**
- May indicate data corruption
- Could be malicious activity
- Patterns of errors

**Solution:**
```bash
# Investigate immediately
vibey roadmap audit show <object-id>
# Understand why rollback happened
# Fix root cause
```

---

### Pitfall 4: Batching Too Many Changes

**Problem:**
```bash
# Complete 20 tasks at once
# ... edit many files ...
git commit -m "Complete sprint"
```

**Why it's bad:**
- Hard to review
- Difficult to debug
- Merge conflicts likely
- Audit trail unclear

**Solution:**
```bash
# Complete tasks one at a time
vibey roadmap complete task-001
git commit -m "Complete task-001"

vibey roadmap complete task-002
git commit -m "Complete task-002"

# Smaller, atomic commits
```

---

### Pitfall 5: Not Reviewing Audit Trail

**Problem:**
- Never running `vibey roadmap audit log`
- Never checking for suspicious changes
- Assuming all changes are valid

**Why it's bad:**
- Miss manual edits
- Don't catch errors
- No accountability

**Solution:**
```bash
# Daily audit check
vibey roadmap audit log

# Weekly suspicious change check
vibey roadmap audit suspicious
```

---

## Performance Tips

### Fast Validation

**Optimize local validation:**
```bash
# Use quick profile for rapid iteration
vibey roadmap validate-fast --profile quick

# Use standard profile before commit
vibey roadmap validate-fast --profile standard

# Use thorough profile rarely (CI/CD handles this)
vibey roadmap validate-fast --profile thorough
```

### Incremental Validation (Future)

```bash
# Only validate changed files
vibey roadmap validate-fast --incremental

# Validates in <1s instead of ~1s
```

### Caching

```bash
# Validation results cached automatically
# First run: ~1s
# Subsequent runs with no changes: ~0.03s
```

---

## Emergency Procedures

### When Validation Blocks Valid Change

**Scenario:** Pre-commit hook rejects valid change due to validation bug

**Steps:**
1. **Verify it's actually valid:**
   ```bash
   vibey roadmap validate-fast --profile standard --verbose
   # Review error carefully
   ```

2. **File issue:**
   ```bash
   # Document the validation bug
   gh issue create --title "Validation false positive: ..." --body "..."
   ```

3. **Bypass hook (with documentation):**
   ```bash
   git commit --no-verify -m "Bypass validation bug #123"
   # Reference issue number in commit message
   ```

4. **Fix validation bug:**
   - Prioritize fixing the validator
   - Once fixed, re-enable hook

---

### When CI/CD System Is Down

**Scenario:** GitHub Actions unavailable, need to merge urgent fix

**Steps:**
1. **Check GitHub Status:** https://www.githubstatus.com/
2. **Validate locally:**
   ```bash
   vibey roadmap validate-fast --profile thorough
   vibey roadmap validate-advanced
   ```
3. **Document in PR:**
   - Note that CI/CD is down
   - Show local validation results
   - Get manual approval from maintainer
4. **Temporarily disable branch protection:**
   - Admin temporarily removes required checks
   - Merge PR
   - Re-enable protection immediately
5. **After recovery:**
   - Re-run validation on merged commits
   - Fix any issues found

---

## Quality Metrics

### Target Metrics

**Validation Pass Rate:**
- Target: >95% of commits pass first time
- Measure: PRs passing validation without fixes
- Improve: Training, better tooling, clearer docs

**Manual Edit Rate:**
- Target: <5% of changes via manual edits
- Measure: Audit trail suspicious change rate
- Improve: Add missing CLI commands

**Audit Trail Activity:**
- Target: 100% of status changes logged
- Measure: Compare git commits to audit entries
- Improve: Enforce CLI usage, reduce manual edits

**CI/CD Performance:**
- Target: <5 min total pipeline time
- Measure: GitHub Actions duration
- Improve: Optimize validators, caching

---

## Team Adoption

### Onboarding New Team Members

**Day 1:**
```bash
# Install pre-commit hook
vibey roadmap install-hooks

# Verify installation
vibey roadmap check-hooks

# Run validation to see current state
vibey roadmap validate-fast --profile standard
```

**Week 1:**
- Use CLI commands only
- Review audit trail daily
- Ask questions about errors

**Month 1:**
- Understand all validation rules
- Know when to use each validation profile
- Help others with validation issues

### Training Materials

**Recommended reading order:**
1. [Validation System Overview](./VALIDATION_SYSTEM.md)
2. [Best Practices (this document)](./BEST_PRACTICES.md)
3. [Validation Rules](./VALIDATION_RULES.md)
4. [Troubleshooting Guide](./TROUBLESHOOTING.md)
5. [Pre-Commit Hooks](./PRE_COMMIT_HOOKS.md)
6. [CI/CD Validation](./CI_CD_VALIDATION.md)

**Hands-on exercises:**
1. Install pre-commit hook
2. Start and complete a task via CLI
3. Trigger validation error intentionally
4. Fix error using auto-repair
5. Review audit trail
6. Create PR and watch CI/CD

---

## Advanced Practices

### Custom Validation Scripts

**Create team-specific checks:**
```bash
#!/bin/bash
# .git/hooks/custom-roadmap-check

# Ensure all completed tasks have commits
python3 -c "
from vibey.roadmap.serialization import load_tasks

tasks = load_tasks('.vibey/roadmap/track-1/sprint-1/tasks.yaml')
for task in tasks:
    if task.status == 'completed' and not task.commits:
        print(f'❌ Task {task.id} completed but has no commits')
        exit(1)
"
```

### Automated Reporting

**Daily validation report:**
```bash
#!/bin/bash
# scripts/daily-validation-report.sh

echo "Daily Validation Report - $(date)"
echo "=================================="

# Run validation
vibey roadmap validate-advanced > validation.log 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Validation PASSED"
else
    echo "❌ Validation FAILED"
    cat validation.log
fi

# Check suspicious changes
vibey roadmap audit suspicious

# Send to Slack/email
# (integrate with notification service)
```

---

## Related Documentation

- [Validation System Overview](./VALIDATION_SYSTEM.md) - Architecture and components
- [Validation Rules](./VALIDATION_RULES.md) - Complete rule reference
- [Troubleshooting Guide](./TROUBLESHOOTING.md) - Common issues and solutions
- [Pre-Commit Hooks](./PRE_COMMIT_HOOKS.md) - Local validation
- [CI/CD Validation](./CI_CD_VALIDATION.md) - GitHub Actions
- [Audit Trail](./AUDIT_TRAIL.md) - Change tracking

---

**Version:** 1.0.0
**Last Updated:** 2025-11-21
**Maintainer:** Vibey Framework Team
