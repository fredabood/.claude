# Roadmap Validation System

**Created:** 2025-11-21
**Sprint:** roadmap-integrity-fixes-6
**Status:** ✅ Production Ready

---

## Overview

The Vibey roadmap validation system provides comprehensive data integrity checking across all roadmap objects (tracks, sprints, tasks). It prevents data corruption, ensures consistency, and maintains referential integrity through automated validation at multiple stages.

### Purpose

**Primary Goals:**
1. **Prevent Data Corruption** - Catch YAML syntax errors and schema violations
2. **Ensure Consistency** - Validate status/progress alignment and data model compliance
3. **Maintain Integrity** - Detect broken references and circular dependencies
4. **Enable Accountability** - Audit trail for all changes with who/when/why
5. **Support Scale** - Fast validation for 400+ files, 100+ tracks

**Key Benefits:**
- ✅ Early error detection (pre-commit hooks)
- ✅ Team-wide enforcement (CI/CD integration)
- ✅ Automated repair suggestions
- ✅ Comprehensive audit trail
- ✅ Multi-layer validation (fast + advanced)

---

## Architecture

### Validation Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Pre-Commit Hook (Local)                          │
│  - Fast syntax validation (<1s)                             │
│  - Catches errors before commit                             │
│  - Developer-friendly feedback                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: CI/CD Validation (GitHub Actions)                │
│  - Fast validation (syntax + schema)                        │
│  - Advanced validation (integrity)                          │
│  - Auto-repair suggestions                                  │
│  - Blocks PR merge on failure                               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Branch Protection (GitHub)                        │
│  - Requires validation checks to pass                       │
│  - Prevents merge of invalid data                           │
│  - Enforces team-wide compliance                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Audit Trail (Continuous)                          │
│  - Logs all status changes                                  │
│  - Detects suspicious changes                               │
│  - Provides accountability                                  │
└─────────────────────────────────────────────────────────────┘
```

### Validation Categories

**1. Fast Validation** (Syntax & Schema)
- YAML syntax checking
- File loading verification
- Basic schema compliance
- **Duration:** ~1 second for 470 files
- **Profiles:** quick, standard, thorough

**2. Advanced Validation** (Integrity)
- Circular dependency detection
- Orphaned task detection
- Broken reference detection
- Progress counter validation
- **Duration:** ~2 minutes for 387 tasks

**3. Auto-Repair** (Automated Fixes)
- Progress counter corrections
- Reference updates
- Status synchronization
- **Mode:** Dry-run preview + confirmation

---

## System Components

### 1. Fast Validator

**Module:** `vibey/operations/roadmap/optimized_validator.py`

**Profiles:**
```python
QUICK = {
    'check_syntax': True,
    'check_loading': False,
    'check_git': False,
    'verbose': False,
}

STANDARD = {
    'check_syntax': True,
    'check_loading': True,
    'check_git': False,
    'verbose': False,
}

THOROUGH = {
    'check_syntax': True,
    'check_loading': True,
    'check_git': True,
    'verbose': True,
}
```

**Command:**
```bash
vibey roadmap validate-fast --profile standard
```

**Output:**
```
================================================================================
Roadmap Validation Report (STANDARD profile)
================================================================================

Files validated: 470
  ✅ Valid: 470
  ❌ Invalid: 0

Duration: 0.63 seconds

✅ Validation PASSED
```

### 2. Advanced Validator

**Module:** `vibey/operations/roadmap/advanced_validator.py`

**Checks:**
- Circular dependencies
- Orphaned tasks
- Broken references
- Progress counters

**Command:**
```bash
vibey roadmap validate-advanced
```

**Output:**
```
Running advanced validation checks...

Checking for circular dependencies...
  ✅ No circular dependencies found

Checking for orphaned tasks...
  ✅ No orphaned tasks found

Checking for broken references...
  ✅ No broken references found

Checking progress counters...
  ✅ All progress counters match actual values

✅ Advanced validation PASSED
```

### 3. Auto-Repair System

**Module:** `vibey/operations/roadmap/auto_repair.py`

**Features:**
- Detects fixable issues
- Shows preview of changes
- Requires confirmation
- Creates backups

**Command:**
```bash
# Preview what would be fixed
vibey roadmap repair --all --dry-run

# Apply repairs
vibey roadmap repair --all
```

**Output:**
```
Found 5 issues:
  📊 Progress counter mismatches: 5 (auto-fixable)

Would fix 5 progress counter mismatches:
  1. platform-context-management-5
     Claimed: 0/6
     Actual:  0/0

Apply these repairs? [y/N]: y

✅ Repaired 5 issues
```

### 4. Audit Trail

**Module:** `vibey/operations/roadmap/audit_trail.py`

**Features:**
- Automatic status change logging
- Who/when/why/commit tracking
- Suspicious change detection
- Detailed reporting

**Commands:**
```bash
vibey roadmap audit log                # Recent changes
vibey roadmap audit show <object-id>   # Object history
vibey roadmap audit suspicious         # Detect anomalies
vibey roadmap audit report             # Generate report
```

See [AUDIT_TRAIL.md](./AUDIT_TRAIL.md) for complete documentation.

---

## Integration Points

### Pre-Commit Hook

**Installation:**
```bash
vibey roadmap install-hooks
```

**Behavior:**
- Runs on every commit
- Only validates if `.vibey/roadmap/` files changed
- Fast validation (quick profile)
- Blocks commit on failure

**Configuration:**
```bash
# Enable advanced validation
export VIBEY_HOOK_ADVANCED=true
```

See [PRE_COMMIT_HOOKS.md](./PRE_COMMIT_HOOKS.md) for complete guide.

### CI/CD Pipeline

**Workflow:** `.github/workflows/roadmap-validation.yml`

**Jobs:**
1. **fast-validation** (required) - Syntax & schema
2. **advanced-validation** (required) - Integrity checks
3. **auto-repair-check** (on failure) - Repair preview
4. **legacy-validation** (non-blocking) - Pytest tests

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main` or `develop`
- Changes to `.vibey/roadmap/**`

See [CI_CD_VALIDATION.md](./CI_CD_VALIDATION.md) for complete guide.

### Branch Protection

**Required Checks:**
- `fast-validation`
- `advanced-validation`

**Benefits:**
- Blocks merge of invalid data
- Team-wide enforcement
- Visible in PR status

See [BRANCH_PROTECTION_SETUP.md](./BRANCH_PROTECTION_SETUP.md) for setup guide.

---

## Validation Flow

### Developer Workflow

```
1. Developer makes changes to roadmap
   ↓
2. Uses CLI commands (vibey roadmap start, complete)
   ↓
3. Changes logged to audit trail automatically
   ↓
4. Developer commits changes
   ↓
5. Pre-commit hook validates (fast)
   ↓
6. PASS → Commit succeeds
   FAIL → Show errors, block commit
   ↓
7. Developer pushes to remote
   ↓
8. CI/CD runs validation (fast + advanced)
   ↓
9. PASS → PR can be merged
   FAIL → Auto-repair suggestions posted to PR
   ↓
10. Branch protection enforces validation
    ↓
11. Merge only if all checks pass
```

### Validation Decision Tree

```
Commit attempt
    ↓
.vibey/roadmap/ files changed?
    ↓ YES              ↓ NO
    ↓                  Skip validation
    ↓
Run fast validation (quick profile)
    ↓
Syntax valid?
    ↓ YES              ↓ NO
    ↓                  Show errors, block commit
    ↓
VIBEY_HOOK_ADVANCED=true?
    ↓ YES              ↓ NO
    ↓                  Allow commit
    ↓
Run advanced validation
    ↓
Integrity checks pass?
    ↓ YES              ↓ NO
    ↓                  Show errors, block commit
    ↓
Allow commit
```

---

## Performance Characteristics

### Fast Validation

| Files | Profile | Duration | Cache Hit |
|-------|---------|----------|-----------|
| 470   | Quick   | ~0.6s    | 0% (cold) |
| 470   | Standard| ~0.6s    | 0% (cold) |
| 470   | Standard| ~0.03s   | 100% (warm) |

### Advanced Validation

| Tasks | Check Type | Duration |
|-------|------------|----------|
| 387   | Circular deps | ~30s |
| 387   | Orphaned tasks | ~20s |
| 387   | Broken refs | ~40s |
| 387   | Progress counters | ~30s |
| **Total** | **All checks** | **~120s** |

### Optimization Strategies

1. **Caching** - Cache parsed YAML for repeated validation
2. **Incremental** - Only validate changed files (future)
3. **Parallel** - Run checks concurrently (future)
4. **Indexing** - Build ID index for faster lookups (future)

---

## CLI Command Reference

### Validation Commands

**Fast Validation:**
```bash
vibey roadmap validate-fast                  # Standard profile
vibey roadmap validate-fast --profile quick  # Syntax only
vibey roadmap validate-fast --verbose        # Detailed output
```

**Advanced Validation:**
```bash
vibey roadmap validate-advanced              # All checks
vibey roadmap validate-advanced --verbose    # Detailed output
```

**Auto-Repair:**
```bash
vibey roadmap repair --all --dry-run         # Preview repairs
vibey roadmap repair --all                   # Apply repairs
vibey roadmap repair --progress              # Fix progress only
```

### Hook Management

**Install Hooks:**
```bash
vibey roadmap install-hooks                  # Install pre-commit hook
vibey roadmap install-hooks --force          # Overwrite existing
```

**Check Installation:**
```bash
vibey roadmap check-hooks                    # Verify hook installed
```

**Uninstall:**
```bash
vibey roadmap uninstall-hooks                # Remove hook
```

### Audit Commands

**View Changes:**
```bash
vibey roadmap audit log                      # Last 20 changes
vibey roadmap audit log --limit 50           # Last 50 changes
vibey roadmap audit show <object-id>         # Object history
```

**Detect Issues:**
```bash
vibey roadmap audit suspicious               # Find anomalies
```

**Generate Reports:**
```bash
vibey roadmap audit report                   # Full report
vibey roadmap audit report --object-id X     # Filter by object
vibey roadmap audit report --start 2025-01-01 # Filter by date
```

---

## Configuration

### Validation Profiles

**Quick Profile:**
- Syntax checking only
- Fastest (~0.6s)
- Pre-commit hook default

**Standard Profile:**
- Syntax + file loading
- Fast (~0.6s)
- CI/CD default for fast validation

**Thorough Profile:**
- Syntax + loading + git integration
- Slower (~2s)
- Use for comprehensive checks

### Hook Configuration

**Enable Advanced Validation:**
```bash
# In shell profile (~/.bashrc or ~/.zshrc)
export VIBEY_HOOK_ADVANCED=true
```

**Per-Commit Override:**
```bash
VIBEY_HOOK_ADVANCED=true git commit -m "message"
```

**Bypass Hook (Emergency):**
```bash
git commit --no-verify -m "emergency fix"
```

---

## Error Types and Handling

### Syntax Errors

**Type:** Invalid YAML syntax

**Example:**
```
❌ Validation errors found in track.yaml:
  Line 42: Invalid YAML syntax
```

**Fix:** Correct YAML syntax using proper indentation and quoting

### Schema Errors

**Type:** Missing required fields or wrong data types

**Example:**
```
❌ Missing required field 'status' in task roadmap-system-1-task-001
```

**Fix:** Add missing field or correct data type

### Integrity Errors

**Type:** Broken references, circular dependencies, progress mismatches

**Example:**
```
❌ Broken reference: Task roadmap-system-2-task-005 references non-existent task
```

**Fix:** Use auto-repair or manually correct reference

---

## Security Considerations

### Data Integrity

- All changes logged to audit trail
- Git history provides tamper evidence
- Branch protection prevents bypass

### Access Control

- Pre-commit hooks run locally (can be bypassed with `--no-verify`)
- CI/CD validation cannot be bypassed
- Branch protection enforces team-wide compliance

### Sensitive Data

- Validation does not log data values
- Only status changes and metadata tracked
- No secrets in audit trail

---

## Monitoring and Metrics

### Key Metrics

**Validation Health:**
- Pass rate (% of commits passing validation)
- Average validation time
- Most common error types

**Data Quality:**
- Total validation errors per day
- Auto-repair usage frequency
- Suspicious changes detected

**Team Adoption:**
- Hook installation rate
- Manual YAML edits (should be low)
- Audit trail activity

### Dashboards (Future)

- Real-time validation status
- Error trend analysis
- Team compliance metrics
- Data quality scores

---

## Extending the System

### Adding New Validation Rules

**1. Fast Validation Rule:**
```python
# In vibey/operations/roadmap/optimized_validator.py
def check_custom_rule(file_path: Path) -> bool:
    # Add your validation logic
    pass
```

**2. Advanced Validation Rule:**
```python
# In vibey/operations/roadmap/advanced_validator.py
def check_custom_integrity(roadmap_root: Path) -> List[str]:
    # Add your integrity check
    pass
```

**3. Auto-Repair Rule:**
```python
# In vibey/operations/roadmap/auto_repair.py
def repair_custom_issue(issue: Dict) -> bool:
    # Add your repair logic
    pass
```

### Custom Validation Profiles

Create custom profiles in configuration:
```yaml
# .vibey/config/validation.yaml
profiles:
  custom:
    check_syntax: true
    check_loading: true
    check_git: true
    check_custom: true  # Your custom check
```

---

## Related Documentation

- [Validation Rules Reference](./VALIDATION_RULES.md) - Complete rule documentation
- [Best Practices Guide](./BEST_PRACTICES.md) - Recommended workflows
- [Troubleshooting Guide](./TROUBLESHOOTING.md) - Common issues and solutions
- [Pre-Commit Hooks](./PRE_COMMIT_HOOKS.md) - Local validation setup
- [CI/CD Validation](./CI_CD_VALIDATION.md) - GitHub Actions integration
- [Branch Protection](./BRANCH_PROTECTION_SETUP.md) - Merge enforcement
- [Audit Trail](./AUDIT_TRAIL.md) - Change tracking system

---

## Version History

**v1.0.0** (2025-11-21)
- Initial release
- Fast validation with 3 profiles
- Advanced validation with 4 check types
- Auto-repair system
- Audit trail integration
- Pre-commit hooks
- CI/CD pipeline
- Branch protection guide

---

**Version:** 1.0.0
**Last Updated:** 2025-11-21
**Maintainer:** Vibey Framework Team
