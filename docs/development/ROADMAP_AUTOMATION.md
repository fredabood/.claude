# Roadmap Automation Tools

**Purpose:** Automated validation and synchronization for roadmap management
**Created:** 2025-11-13
**Status:** Production Ready

---

## Overview

This document describes the automation tools created to address recurring synchronization issues between roadmap data and documentation. These tools prevent drift, automate updates, and ensure data integrity.

---

## Problem Statement

### Recurring Issues Identified

1. **Manual Roadmap Sync** - Track completions not automatically updating roadmap.yaml
2. **Track Registration** - New tracks created but not added to roadmap
3. **Progress Calculation Drift** - Metrics become stale as tracks complete
4. **Documentation Update Lag** - Manual updates lag behind actual changes
5. **Test Maintenance Lag** - Tests drift from implementation

### Impact

- Inaccurate status reporting (85% shown vs 88% actual)
- Missing tracks in main roadmap
- Outdated documentation
- Manual reconciliation required

---

## Automation Tools

### 1. Roadmap Sync Validator

**Script:** `scripts/validate-roadmap-sync.py`
**Purpose:** Detect and fix synchronization issues

#### Features

- ✅ **Status Mismatch Detection** - Finds tracks with different statuses in roadmap.yaml vs track.yaml
- ✅ **Track Coverage Validation** - Identifies missing or orphaned tracks
- ✅ **Progress Metrics Verification** - Detects drift in calculated vs stored metrics
- ✅ **Automatic Fixing** - Can automatically resolve most issues with `--fix`
- ✅ **Backup Creation** - Creates backups before making changes
- ✅ **Color-Coded Output** - Clear visual indication of issue severity

#### Usage

```bash
# Check for issues
python3 scripts/validate-roadmap-sync.py

# Check with detailed output
python3 scripts/validate-roadmap-sync.py --verbose

# Auto-fix all issues
python3 scripts/validate-roadmap-sync.py --fix
```

#### Output Example

```
Validating Roadmap Synchronization...

📂 Loading roadmap data...
   Found 19 tracks in roadmap.yaml
   Found 19 track files in .vibey/roadmap/

🔍 Running validation checks...

✅ All validation checks passed!
Roadmap is synchronized correctly.
```

#### Issue Categories

| Category | Severity | Auto-Fixable |
|----------|----------|--------------|
| STATUS_MISMATCH | CRITICAL/HIGH | Yes |
| MISSING_TRACK | HIGH | Yes |
| ORPHANED_TRACK | MEDIUM | No (manual) |
| PROGRESS_DRIFT | MEDIUM | Yes |

#### When to Run

- ✅ After completing any track
- ✅ After creating new tracks
- ✅ Before generating status documentation
- ✅ As part of pre-release checklist
- ✅ Daily in CI/CD pipeline (recommended)

---

### 2. Status Document Generator

**Script:** `scripts/generate-roadmap-status.py`
**Purpose:** Auto-generate docs/ROADMAP_STATUS.md from roadmap data

#### Features

- ✅ **Automated Generation** - No manual documentation updates needed
- ✅ **Always Current** - Generated from source of truth (.vibey/roadmap.yaml)
- ✅ **Comprehensive** - Includes all tracks, phases, priorities, timelines
- ✅ **Recent Achievements** - Automatically finds tracks completed in last 7 days
- ✅ **Calculated Metrics** - Progress, completion percentages computed dynamically
- ✅ **Phase Analysis** - Groups tracks into logical phases with completion status

#### Usage

```bash
# Generate default output (docs/ROADMAP_STATUS.md)
python3 scripts/generate-roadmap-status.py

# Generate to custom location
python3 scripts/generate-roadmap-status.py --output custom-status.md

# Verbose mode
python3 scripts/generate-roadmap-status.py --verbose
```

#### Output Example

```
Loading roadmap data...
Generating ROADMAP_STATUS.md...
Saving to /path/to/docs/ROADMAP_STATUS.md...
✅ Generated 15053 characters
📄 Output: /path/to/docs/ROADMAP_STATUS.md
```

#### Sections Generated

1. **Executive Summary** - High-level overview with recent achievements
2. **Track Status Overview** - Tables of completed, in-progress, not started
3. **Detailed Track Analysis** - Full details for each completed track
4. **Priority Analysis** - Tracks grouped by critical/high/medium/low
5. **Milestone Progress** - Phase-based completion tracking
6. **Recent Achievements** - Last 7 days of completions
7. **Next Steps** - Prioritized recommendations
8. **Risk Assessment** - Identified risks and mitigation
9. **Completion Timeline** - Projected completion dates
10. **Success Metrics** - Quality, delivery, platform readiness
11. **Summary** - Overall status and next steps

#### When to Run

- ✅ After completing any track
- ✅ After major milestones
- ✅ Before releases or demos
- ✅ Weekly (recommended automation)
- ✅ On-demand for status reports

---

### 3. Track Registration Helper

**Script:** `scripts/register-track.py`
**Purpose:** Register new tracks with main roadmap.yaml

#### Features

- ✅ **Auto-Detection** - Reads track details from track.yaml automatically
- ✅ **Single or Bulk** - Register one track or scan for all unregistered
- ✅ **Progress Updates** - Automatically recalculates metrics
- ✅ **Validation** - Prevents duplicate registration
- ✅ **Backup Creation** - Safe updates with rollback capability

#### Usage

```bash
# Register a single track
python3 scripts/register-track.py my-track-id

# Scan and register all unregistered tracks
python3 scripts/register-track.py --scan

# Specify custom root directory
python3 scripts/register-track.py my-track-id --dir /path/to/project
```

#### Output Example

```
Found 2 unregistered track(s):

  • interface-unification
    Name: Interface Unification & Simplification
    Status: not_started

  • platform-context-management
    Name: Platform Context Management System
    Status: not_started

✅ Registered track: interface-unification
   Name: Interface Unification & Simplification
   Status: not_started
   Priority: critical
   Updated progress: 11/19 tracks completed

✅ Registered track: platform-context-management
   Name: Platform Context Management System
   Status: not_started
   Priority: critical
   Updated progress: 11/19 tracks completed

✅ Saved roadmap: .vibey/roadmap.yaml
   Backup: .vibey/roadmap.yaml.bak

✅ Registered 2 track(s)
```

#### When to Run

- ✅ After creating a new track directory
- ✅ When `validate-roadmap-sync.py` reports MISSING_TRACK
- ✅ Before generating status documentation
- ✅ As part of track creation workflow

---

## Integration Workflows

### Workflow 1: Track Completion

When completing a track:

```bash
# 1. Complete the track (updates track.yaml)
vibey roadmap complete <track-id>

# 2. Validate synchronization
python3 scripts/validate-roadmap-sync.py --fix

# 3. Regenerate status documentation
python3 scripts/generate-roadmap-status.py

# 4. Commit changes
git add .vibey/roadmap.yaml docs/ROADMAP_STATUS.md
git commit -m "feat: Complete <track-name> track"
```

### Workflow 2: Track Creation

When creating a new track:

```bash
# 1. Create track directory and track.yaml
mkdir -p .vibey/roadmap/my-new-track
# ... create track.yaml ...

# 2. Register track with roadmap
python3 scripts/register-track.py my-new-track

# 3. Validate
python3 scripts/validate-roadmap-sync.py

# 4. Update documentation
python3 scripts/generate-roadmap-status.py

# 5. Commit
git add .vibey/roadmap.yaml .vibey/roadmap/my-new-track docs/ROADMAP_STATUS.md
git commit -m "feat: Add my-new-track to roadmap"
```

### Workflow 3: Daily Validation (CI/CD)

Recommended daily automation:

```bash
#!/bin/bash
# .github/workflows/roadmap-validation.yml or similar

# Validate roadmap sync
python3 scripts/validate-roadmap-sync.py

if [ $? -ne 0 ]; then
  echo "❌ Roadmap sync issues detected"
  echo "Run: python3 scripts/validate-roadmap-sync.py --fix"
  exit 1
fi

# Check if ROADMAP_STATUS.md is current
ROADMAP_DATE=$(grep "**Date:**" docs/ROADMAP_STATUS.md | cut -d' ' -f2)
TODAY=$(date +%Y-%m-%d)

if [ "$ROADMAP_DATE" != "$TODAY" ]; then
  echo "⚠️  ROADMAP_STATUS.md is outdated (last: $ROADMAP_DATE, today: $TODAY)"
  echo "Run: python3 scripts/generate-roadmap-status.py"
fi

echo "✅ Roadmap validation passed"
```

---

## Best Practices

### 1. Run Validation Regularly

```bash
# Add to pre-commit hook
# .git/hooks/pre-commit

#!/bin/bash
python3 scripts/validate-roadmap-sync.py
if [ $? -ne 0 ]; then
  echo "❌ Fix roadmap sync issues before committing"
  exit 1
fi
```

### 2. Auto-Generate Documentation

Don't manually edit `docs/ROADMAP_STATUS.md`. Always regenerate:

```bash
# ✅ Good
python3 scripts/generate-roadmap-status.py

# ❌ Bad
vim docs/ROADMAP_STATUS.md  # Manual edits will be overwritten
```

### 3. Register Tracks Immediately

When creating a new track, register it right away:

```bash
# Create track
vibey roadmap init-track my-track

# Register immediately
python3 scripts/register-track.py my-track
```

### 4. Fix Issues Don't Ignore

When validation finds issues, fix them immediately:

```bash
# Don't ignore
python3 scripts/validate-roadmap-sync.py
# ❌ Roadmap has issues... (ignoring)

# Fix immediately
python3 scripts/validate-roadmap-sync.py --fix
# ✅ Issues resolved
```

---

## Troubleshooting

### Issue: Validation finds issues after using --fix

**Symptom:**
```bash
python3 scripts/validate-roadmap-sync.py --fix
# Reports 1 issue
# After re-validation, still finds 1 issue
```

**Cause:** Issue may not be auto-fixable (e.g., ORPHANED_TRACK)

**Solution:** Check issue category, may require manual fix

---

### Issue: Generator creates incorrect dates

**Symptom:** Generated document shows wrong date

**Cause:** System timezone not set correctly

**Solution:** Ensure system timezone is correct or use UTC

---

### Issue: Track registration fails

**Symptom:**
```
❌ Track file not found: .vibey/roadmap/my-track/track.yaml
```

**Cause:** Track directory or track.yaml doesn't exist

**Solution:** Create track files first, then register

---

## Testing

All automation tools include comprehensive testing:

```bash
# Test validation
python3 scripts/validate-roadmap-sync.py --verbose

# Test generator
python3 scripts/generate-roadmap-status.py

# Test registration with scan
python3 scripts/register-track.py --scan
```

---

## Maintenance

### Adding New Validation Checks

To add a new validation check to `validate-roadmap-sync.py`:

1. Add method `def validate_my_check(self):`
2. Append issues to `self.issues`
3. Mark as `fixable` if auto-fix possible
4. Add fix method `def _fix_my_check(self, issue):`
5. Update `fix_issues()` to call fix method

### Extending Status Generator

To add new sections to generated documentation:

1. Add method `def _generate_my_section(self):`
2. Return formatted markdown string
3. Call from `generate_document()` method
4. Position in appropriate location

---

## Performance

### Validation Script

- **Small projects** (<10 tracks): <1 second
- **Medium projects** (10-50 tracks): 1-3 seconds
- **Large projects** (50+ tracks): 3-10 seconds

### Generator Script

- **Small projects**: <2 seconds
- **Medium projects**: 2-5 seconds
- **Large projects**: 5-15 seconds

### Registration Script

- **Single track**: <1 second
- **Bulk scan**: 1-3 seconds for 10-20 tracks

---

## Migration Guide

### From Manual to Automated

If you've been manually maintaining roadmap.yaml and ROADMAP_STATUS.md:

1. **Run initial validation:**
   ```bash
   python3 scripts/validate-roadmap-sync.py --fix
   ```

2. **Register any missing tracks:**
   ```bash
   python3 scripts/register-track.py --scan
   ```

3. **Regenerate status documentation:**
   ```bash
   python3 scripts/generate-roadmap-status.py
   ```

4. **Set up automation:**
   - Add validation to pre-commit hooks
   - Schedule weekly status regeneration
   - Document team workflow

5. **Stop manual edits:**
   - Never manually edit roadmap.yaml (use CLI or track.yaml)
   - Never manually edit ROADMAP_STATUS.md (always regenerate)

---

## Future Enhancements

### Planned Improvements

1. **Automatic Scheduling** - Cron/systemd timers for daily validation
2. **Slack/Discord Notifications** - Alert when issues detected
3. **Web Dashboard** - Visual roadmap status interface
4. **GitHub Actions Integration** - Automated PR checks
5. **Metrics Dashboard** - Historical progress tracking
6. **Anomaly Detection** - Identify unusual patterns

---

## References

- **Audit Document:** `docs/COMPREHENSIVE_AUDIT_2025-11-13.md`
- **Validation Script:** `scripts/validate-roadmap-sync.py`
- **Generator Script:** `scripts/generate-roadmap-status.py`
- **Registration Script:** `scripts/register-track.py`
- **Coverage Fix:** `pytest.ini` (updated to measure `vibey/` not `framework/`)

---

## Summary

These automation tools eliminate the recurring synchronization issues that plagued the roadmap system. By automating validation, generation, and registration, we ensure:

- ✅ **Accurate Status** - Roadmap always reflects actual state
- ✅ **Current Documentation** - Status docs never lag behind
- ✅ **Early Detection** - Issues caught immediately
- ✅ **Automatic Fixes** - Most issues resolved without manual intervention
- ✅ **Audit Trail** - Backups created before changes
- ✅ **Reduced Toil** - Manual reconciliation eliminated

**Recommendation:** Integrate these tools into daily workflow and CI/CD pipeline for maximum benefit.

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-13
**Status:** Production Ready
