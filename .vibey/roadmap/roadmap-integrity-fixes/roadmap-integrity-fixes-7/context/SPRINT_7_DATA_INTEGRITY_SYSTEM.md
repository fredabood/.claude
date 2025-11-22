# Sprint 7: Data Integrity & Prevention System

**Status:** Phase 3 Complete
**Created:** 2025-11-16
**Last Updated:** 2025-11-19

## Overview

Sprint 7 implements a comprehensive data integrity system for Vibey roadmap YAML files, ensuring:
- ✅ **Prevention**: Pre-commit hooks + CI/CD validation
- ✅ **Detection**: Automated tests + monitoring dashboard
- ✅ **Remediation**: Cleanup scripts + schema validators
- ✅ **Monitoring**: Health dashboard + metrics tracking

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   DATA INTEGRITY SYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  PREVENTION LAYER (Pre-commit + CI/CD)                      │
│  ├─ Pre-commit hook: Block Python serialization             │
│  ├─ GitHub Actions: Validate on push/PR                     │
│  └─ Continuous monitoring: Track data quality                │
│                                                               │
│  DETECTION LAYER (Tests + Validators)                       │
│  ├─ test_yaml_integrity.py (14 validation tests)            │
│  ├─ validate-roadmap-schema.py (Pydantic validation)        │
│  └─ roadmap-health-dashboard.py (Health scoring)            │
│                                                               │
│  REMEDIATION LAYER (Cleanup + Fixes)                        │
│  ├─ cleanup-roadmap-yaml.py (Automated fixes)               │
│  └─ Manual fix guidelines                                    │
│                                                               │
│  MONITORING LAYER (Metrics + Reporting)                     │
│  ├─ Health dashboard (95/100 score)                         │
│  ├─ CI/CD reports (GitHub Actions artifacts)                │
│  └─ Validation reports (pytest output)                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Tools & Usage

### 1. YAML Validation Tests (`tests/validation/test_yaml_integrity.py`)

**Purpose:** Comprehensive validation test suite
**Test Classes:** 6 classes, 14 validation methods
**Usage:**

```bash
# Run all validation tests
pytest tests/validation/test_yaml_integrity.py -v

# Run specific test class
pytest tests/validation/test_yaml_integrity.py::TestYAMLSyntax -v

# Run with coverage
pytest tests/validation/test_yaml_integrity.py --cov

# Generate HTML report
pytest tests/validation/test_yaml_integrity.py --html=report.html
```

**Test Classes:**
- `TestYAMLSyntax` - YAML parseability with `yaml.safe_load()`
- `TestPythonSerialization` - Detects `!!python` patterns
- `TestSchemaValidation` - Validates enums, types, ranges (8 tests)
- `TestDependencyIntegrity` - Checks dependency status types (2 tests)
- `TestStructuralIntegrity` - Validates loadability (3 tests)

### 2. YAML Cleanup Script (`scripts/cleanup-roadmap-yaml.py`)

**Purpose:** Automated detection and fixing of YAML issues
**Capabilities:**
- Fixes Python object serialization patterns
- Corrects invalid enum values
- Fixes type mismatches (strings → ints/bools)
- Provides detailed reports

**Usage:**

```bash
# Dry-run mode (safe, shows what would change)
python3 scripts/cleanup-roadmap-yaml.py --dry-run

# Verbose output (see each file)
python3 scripts/cleanup-roadmap-yaml.py --dry-run --verbose

# Actually apply fixes
python3 scripts/cleanup-roadmap-yaml.py

# Apply fixes with detailed output
python3 scripts/cleanup-roadmap-yaml.py --verbose
```

**Output:**
```
CLEANUP SUMMARY
================================================================================
Files scanned: 435
Files modified: 3
Total issues fixed: 5
  - Python serialization: 3
  - Invalid enum values: 2
  - Type mismatches: 0
  - Formatting issues: 0

Modified files: 3

.vibey/roadmap/aider-port/track.yaml:
  ✓ Fixed Python serialization for 'current_status' field
  ✓ Fixed invalid status: 'in_progress_old' → 'in_progress'
```

### 3. Schema Validator (`scripts/validate-roadmap-schema.py`)

**Purpose:** Pydantic-based schema validation
**Capabilities:**
- Validates against actual Pydantic models
- Checks data consistency (dates, counts, progress)
- Provides detailed validation errors

**Usage:**

```bash
# Validate all files
python3 scripts/validate-roadmap-schema.py

# Verbose output (see each file)
python3 scripts/validate-roadmap-schema.py --verbose

# Strict mode (warnings = errors)
python3 scripts/validate-roadmap-schema.py --strict
```

**Output:**
```
SCHEMA VALIDATION SUMMARY
================================================================================
Files validated: 123
✓ Passed: 120 (97.6%)
✗ Failed: 3 (2.4%)

⚠ Warnings: 5
  .vibey/roadmap/core-framework/track.yaml
    Progress sprints_total (6) doesn't match sprints list length (5)

✗ Validation Errors: 3
  .vibey/roadmap/claude-port/track.yaml
    'conditionally_passed' is not a valid GateStatus
```

### 4. Health Dashboard (`scripts/roadmap-health-dashboard.py`)

**Purpose:** Real-time data quality metrics and health scoring
**Capabilities:**
- Overall health score (0-100)
- File statistics breakdown
- Data quality metrics
- Issue categorization by severity

**Usage:**

```bash
# Display dashboard
python3 scripts/roadmap-health-dashboard.py

# Export as JSON
python3 scripts/roadmap-health-dashboard.py --json

# Export to file
python3 scripts/roadmap-health-dashboard.py --export metrics.json
```

**Output:**
```
================================================================================
ROADMAP DATA HEALTH DASHBOARD
================================================================================
Generated: 2025-11-19T23:18:47

✨  OVERALL HEALTH SCORE: 95.0/100 🟢 EXCELLENT

FILE STATISTICS:
  Total files: 435
  └─ Tracks: 20
  └─ Sprints: 51
  └─ Tasks: 364

DATA QUALITY METRICS:
  ✓ YAML Syntax: 435/435 (100.0%)
  ✓ Python Serialization: 435/435 (100.0%)
  ✗ Valid Enum Values: 433/435 (99.5%)
  ✓ Correct Types: 435/435 (100.0%)
  ✗ Date Consistency: 434/435 (99.8%)

ISSUES FOUND:
  ⚠️  High: 2
  ℹ️  Low: 1

  Top Issues:
    1. ⚠️ [enum] track.yaml: Invalid status: 'superseded'
    2. ℹ️ [logic] sprint.yaml: Started > completed date
```

### 5. CI/CD Workflow (`.github/workflows/roadmap-validation.yml`)

**Purpose:** Automated validation in GitHub Actions
**Triggers:**
- Pushes to main/develop affecting roadmap data
- Pull requests affecting roadmap data

**Workflow Steps:**
1. **YAML Syntax Validation** (blocking)
2. **Python Serialization Check** (blocking)
3. **Schema Validation** (warning-only)
4. **Dependency Integrity** (warning-only)
5. **Structural Integrity** (warning-only)
6. **Report Generation** (artifacts)
7. **PR Comments** (on failure)

**Artifacts:**
- `validation-report.md` (30-day retention)
- Test output logs

### 6. Pre-commit Hook (`.pre-commit-config.yaml`)

**Purpose:** Block commits with corrupted YAML
**Check:** Searches for `!!python` patterns in `.vibey/roadmap/`

**Installation:**
```bash
pip install pre-commit
pre-commit install
```

**Manual run:**
```bash
pre-commit run --all-files
```

## Integration Workflow

### During Development

1. **Write code** that modifies roadmap YAML
2. **Pre-commit hook** checks for issues
3. **If issues found**: commit is blocked, fix required
4. **If clean**: commit succeeds

### In CI/CD

1. **Push/PR** triggers GitHub Actions
2. **Critical tests run** (syntax, serialization)
3. **If fail**: PR cannot merge, notification sent
4. **Warning tests run** (schema, dependencies)
5. **Reports generated** and uploaded as artifacts

### Monitoring

1. **Run health dashboard** periodically
2. **Check score** (target: 90+)
3. **Review issues** by severity
4. **Run cleanup script** if needed
5. **Validate fixes** with schema validator

## Best Practices

### 1. When Modifying YAML Data

**DO:**
- Always use `.value` when assigning enums:
  ```python
  track.status = Status.IN_PROGRESS.value  # ✓ Correct
  ```
- Run health dashboard before committing:
  ```bash
  python3 scripts/roadmap-health-dashboard.py
  ```
- Test with validation suite:
  ```bash
  pytest tests/validation/test_yaml_integrity.py -v
  ```

**DON'T:**
- Assign enum objects directly:
  ```python
  track.status = Status.IN_PROGRESS  # ✗ Wrong - will serialize as !!python
  ```
- Skip pre-commit checks with `--no-verify`
- Ignore validation warnings

### 2. Fixing Data Integrity Issues

**Step 1: Identify**
```bash
python3 scripts/roadmap-health-dashboard.py
```

**Step 2: Cleanup**
```bash
# Dry-run first
python3 scripts/cleanup-roadmap-yaml.py --dry-run --verbose

# Apply fixes
python3 scripts/cleanup-roadmap-yaml.py --verbose
```

**Step 3: Validate**
```bash
pytest tests/validation/test_yaml_integrity.py -v
python3 scripts/validate-roadmap-schema.py
```

**Step 4: Commit**
```bash
git add .vibey/roadmap/
git commit -m "fix: Cleanup YAML data integrity issues"
```

### 3. Maintaining Health Score

**Target:** 90+ (excellent health)

**If score drops:**
1. Run health dashboard to see issues
2. Check severity (critical > high > medium > low)
3. Run cleanup script for automated fixes
4. Manually fix remaining issues
5. Re-run dashboard to verify

### 4. Adding New Fields

**When adding fields to models:**
1. Update Pydantic models in `vibey/roadmap/models/`
2. Update expected fields in `test_yaml_integrity.py`
3. Update cleanup script if field has special validation
4. Update schema validator for custom checks
5. Run full test suite to verify

## Troubleshooting

### Issue: Pre-commit hook blocks commit

**Symptom:** `ERROR: Python object serialization found`

**Fix:**
```bash
# Find corrupted files
grep -r "!!python" .vibey/roadmap/

# Clean them
python3 scripts/cleanup-roadmap-yaml.py

# Try commit again
git commit -m "..."
```

### Issue: CI/CD validation fails

**Symptom:** GitHub Actions workflow fails

**Fix:**
1. Check workflow logs for specific errors
2. Download validation report artifact
3. Fix issues locally
4. Push again

### Issue: Health score below 90

**Symptom:** Dashboard shows GOOD or FAIR rating

**Fix:**
```bash
# See detailed issues
python3 scripts/roadmap-health-dashboard.py

# Auto-fix what's possible
python3 scripts/cleanup-roadmap-yaml.py --verbose

# Manually fix remaining
# (schema validator will show details)
python3 scripts/validate-roadmap-schema.py --verbose

# Verify improvements
python3 scripts/roadmap-health-dashboard.py
```

### Issue: Schema validator reports model errors

**Symptom:** `'sprint_id' error` or `'SomeField' is not a valid EnumType`

**Cause:** Data model mismatch (YAML doesn't match Pydantic model)

**Fix:**
1. Check the model definition in `vibey/roadmap/models/`
2. Update YAML to match expected schema
3. Or update model if YAML structure is correct

## Metrics & Success Criteria

### Current Status (2025-11-19)

**Health Score:** 95.0/100 🟢 EXCELLENT

**File Statistics:**
- Total files: 435
- Tracks: 20
- Sprints: 51
- Tasks: 364

**Data Quality:**
- YAML Syntax: 100% ✅
- Python Serialization: 100% ✅
- Valid Enum Values: 99.5% ⚠️ (2 invalid values)
- Correct Types: 100% ✅
- Date Consistency: 99.8% ⚠️ (1 inconsistency)

**Issues:**
- Critical: 0
- High: 2 (invalid enum values)
- Medium: 0
- Low: 1 (date logic error)

### Success Criteria (Sprint 7)

- [x] **No Python serialization** in any YAML file
- [x] **Pre-commit hook** installed and active
- [x] **CI/CD workflow** running on all pushes/PRs
- [x] **Health score** above 90
- [x] **Test suite** with 100% YAML syntax pass rate
- [x] **Cleanup script** available and documented
- [x] **Schema validator** catching model violations
- [x] **Monitoring dashboard** showing real-time metrics

## Future Enhancements

1. **Automated daily health reports** via cron job
2. **Slack/email notifications** for health score drops
3. **Historical metrics tracking** (health score over time)
4. **Auto-fix PR bot** that creates PRs for cleanable issues
5. **Custom validators** for business logic rules
6. **Performance benchmarking** for large roadmaps
7. **Data migration tools** for schema changes

## Related Documentation

- `.github/workflows/roadmap-validation.yml` - CI/CD workflow definition
- `.pre-commit-config.yaml` - Pre-commit hook configuration
- `tests/validation/test_yaml_integrity.py` - Validation test suite
- `vibey/roadmap/models/` - Pydantic data models
- `vibey/roadmap/serialization/yaml_dumper.py` - YAML serialization logic

## Contact & Support

For issues or questions about the data integrity system:
1. Check this documentation first
2. Run diagnostic tools (health dashboard, validators)
3. Review GitHub Actions logs for CI/CD issues
4. Check git history for recent changes that may have introduced issues

---

**Last Health Check:** 2025-11-19 23:18:47
**Status:** System operational, health score excellent (95/100)
**Next Review:** Weekly monitoring recommended
