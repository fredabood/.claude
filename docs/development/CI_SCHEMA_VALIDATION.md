# CI/CD Schema Validation

**Status**: ✅ Active and Enforced
**Integration Date**: 2025-11-20
**Workflow**: `.github/workflows/roadmap-validation.yml`

## Overview

Automated schema validation runs on every push and pull request that affects roadmap data, ensuring that all YAML files maintain schema compliance and preventing regressions.

## What Gets Validated

The CI/CD pipeline validates:
- All track files (`.vibey/roadmap/*/track.yaml`)
- All sprint files (`.vibey/roadmap/*/*/sprint.yaml`)
- All task files (`.vibey/roadmap/*/*/*/task.yaml`)

**Total files validated**: 462 files (20 tracks, 55 sprints, 387 tasks)

## Validation Steps

### 1. Schema Validation (BLOCKING)

**Purpose**: Ensure all roadmap YAML files pass comprehensive schema validation

**Tool**: `scripts/validate-roadmap-schema.py`

**Behavior**:
- ✅ **Passes**: All files load successfully and conform to schema
- ❌ **Fails**: Any file fails to load or violates schema constraints
- ⚠️  **Warnings**: Token estimate overruns (informational only, doesn't block)

**Exit codes**:
- `0`: All files passed validation
- `1`: One or more files failed validation

**This step is BLOCKING** - pull requests cannot be merged if schema validation fails.

### 2. Health Score Check (NON-BLOCKING)

**Purpose**: Monitor overall roadmap health and data quality

**Tool**: `scripts/roadmap-health-dashboard.py`

**Metrics checked**:
- Overall health score (target: ≥90)
- Task completion rates
- Dependency health
- Progress tracking accuracy

**Behavior**:
- ⚠️  **Warning**: Health score below 90 (logged but doesn't block)
- ✅ **Passes**: Health score ≥90

**This step is NON-BLOCKING** - currently for monitoring only.

### 3. Supplementary Validations

Additional pytest-based validations run after the main schema validation:
- YAML syntax validation
- Python serialization check
- Dependency integrity check
- Structural integrity check

These provide additional insights but are non-blocking.

## Triggering Conditions

The validation workflow runs on:

**Push events** to `main` or `develop` branches when:
- Roadmap YAML files change (`.vibey/roadmap/**/*.yaml`)
- Validation test files change (`tests/validation/**`)
- Roadmap model files change (`vibey/roadmap/**`)
- Roadmap CLI library changes (`vibey/cli/roadmap_lib/**`)

**Pull requests** targeting `main` or `develop` with the same path filters.

## What Happens on Failure

### Schema Validation Failure

1. **GitHub Actions**: Workflow fails with red X
2. **Error Message**: Clear indication of which files failed
3. **Local Reproduction**: Instructions provided to run validation locally
4. **PR Status**: Marked as "checks failed" - cannot merge

**Example output**:
```
❌ Schema validation failed
Run locally: python scripts/validate-roadmap-schema.py --verbose
```

### Health Score Warning

1. **GitHub Actions**: Step completes with warning (yellow exclamation)
2. **Warning Message**: Health score logged with threshold comparison
3. **PR Status**: Does not block merge

**Example output**:
```
⚠️  Health score below recommended threshold (90): 87
This is a warning - not blocking the build yet
```

## Running Validation Locally

### Before Committing

```bash
# Quick validation (recommended)
python scripts/validate-roadmap-schema.py

# Detailed output with all issues
python scripts/validate-roadmap-schema.py --verbose

# Strict mode (fails on warnings too)
python scripts/validate-roadmap-schema.py --strict
```

### Checking Specific Files

```bash
# Validate specific track
python scripts/validate-roadmap-schema.py

# Use grep to find your changed files first
git diff --name-only | grep "\.yaml$"
```

### Understanding Output

**Success**:
```
================================================================================
SCHEMA VALIDATION SUMMARY
================================================================================
Files validated: 462
✓ Passed: 462 (100.0%)
✗ Failed: 0 (0.0%)

⚠ Warnings: 9
  [warnings listed here - informational only]

================================================================================
✅ All files passed schema validation!
================================================================================
```

**Failure**:
```
================================================================================
SCHEMA VALIDATION SUMMARY
================================================================================
Files validated: 462
✓ Passed: 461 (99.8%)
✗ Failed: 1 (0.2%)

✗ Validation Errors: 1
  /path/to/file.yaml
    Unexpected error: [error details]

================================================================================
❌ 1 file failed schema validation
================================================================================
```

## Common Validation Errors

### 1. Missing Required Field

**Error**: `KeyError: 'field_name'` or `'field_name' is required`

**Cause**: YAML file missing a required field

**Fix**: Add the missing field to your YAML file

**Example**:
```yaml
# ❌ Missing roadmap_id
sprint:
  id: my-sprint-1
  track_id: my-track

# ✅ Fixed
sprint:
  id: my-sprint-1
  track_id: my-track
  roadmap_id: vibey-framework-v2
```

### 2. Invalid Enum Value

**Error**: `'value' is not a valid EnumName`

**Cause**: Field contains value not in allowed enum

**Fix**: Use one of the valid enum values

**Example**:
```yaml
# ❌ Invalid complexity
task:
  complexity: very_high  # Not a valid value

# ✅ Fixed
task:
  complexity: complex  # Valid: simple, medium, complex
```

### 3. Type Mismatch

**Error**: `Expected int, got str` or similar

**Cause**: Field has wrong data type

**Fix**: Correct the field type

**Example**:
```yaml
# ❌ Wrong type
task:
  estimated_tokens: "5000"  # String instead of int

# ✅ Fixed
task:
  estimated_tokens: 5000  # Integer
```

### 4. Python Serialization

**Error**: `Python object serialization found`

**Cause**: Enum objects serialized as `!!python/object` instead of values

**Fix**: Use `.value` when serializing enums

**Example**:
```python
# ❌ Wrong
data = {'status': Status.IN_PROGRESS}  # Serializes as !!python/object

# ✅ Fixed
data = {'status': Status.IN_PROGRESS.value}  # Serializes as 'in_progress'
```

## Backward Compatibility

The validation system supports multiple legacy formats through the YAML loader:

**Supported legacy formats**:
1. Simple string dependencies/blocks (converted to structured format)
2. Missing optional cache fields (defaults provided)
3. Field name variations (e.g., 'name' vs 'title')
4. Legacy enum values (e.g., 'quality_gate' → 'completion_gate')
5. Malformed dict deliverables (converted to string format)
6. Missing metadata fields (defaults to current time)

**See**: `vibey/roadmap/serialization/yaml_loader.py` for implementation details

## Integration Timeline

| Date | Event |
|------|-------|
| 2025-11-20 | Schema validation made blocking in CI/CD |
| 2025-11-20 | 100% validation pass rate achieved (462/462 files) |
| 2025-11-20 | Health score check added (non-blocking) |

## Maintenance

### Updating Validation Rules

When schema requirements change:

1. **Update models** in `vibey/roadmap/models/`
2. **Update loader** in `vibey/roadmap/serialization/yaml_loader.py` for backward compatibility
3. **Test locally**: Ensure 100% pass rate maintained
4. **Update migration script**: Add transformations to `scripts/migrate-roadmap-schema.py`
5. **Update documentation**: Document new requirements

### Monitoring Validation Health

**Check validation status**:
- View GitHub Actions runs: [Actions tab]
- Check latest validation: `python scripts/validate-roadmap-schema.py`
- Monitor health score: `python scripts/roadmap-health-dashboard.py`

**Validation metrics**:
- Target pass rate: 100%
- Current pass rate: 100% (462/462 files)
- Warnings: 9 (token estimate overruns - informational)

## Disabling Validation (Emergency Only)

If validation needs to be temporarily disabled (e.g., during major schema migration):

1. **Comment out the blocking step** in `.github/workflows/roadmap-validation.yml`:
   ```yaml
   # - name: Schema validation (BLOCKING)
   #   run: |
   #     ...
   ```

2. **Create an issue** to re-enable validation
3. **Fix validation errors** as soon as possible
4. **Re-enable validation** by uncommenting the step

⚠️  **Warning**: Only disable validation in emergencies. Merged changes without validation can introduce data quality issues.

## Benefits

### For Development

- ✅ **Early error detection**: Catch schema violations before merge
- ✅ **Prevent regressions**: Ensure changes don't break existing data
- ✅ **Consistent quality**: All files maintain schema compliance
- ✅ **Faster reviews**: Automated validation reduces manual checking

### For Data Quality

- ✅ **100% validation coverage**: All 462 files validated automatically
- ✅ **Schema enforcement**: Models remain strict and well-typed
- ✅ **Backward compatibility**: Legacy formats supported through loader
- ✅ **Migration path**: Clear standards for data improvement

### For Collaboration

- ✅ **Clear expectations**: Validation rules documented and enforced
- ✅ **Quick feedback**: Failures reported immediately in PRs
- ✅ **Local testing**: Developers can validate before pushing
- ✅ **Confidence**: Merges are safe with automated checks

## Troubleshooting

### Validation passes locally but fails in CI

**Possible causes**:
1. Python version difference (local vs CI)
2. Dependency version mismatch
3. File not committed to repository

**Fix**:
```bash
# Ensure file is committed
git status

# Check Python version matches CI (3.12)
python --version

# Reinstall dependencies
pip install -r requirements.txt
```

### CI timeout or hangs

**Possible cause**: Large number of files or slow validation

**Fix**: This shouldn't happen with current file count, but if it does:
- Check GitHub Actions logs for specific slow step
- Consider splitting validation into parallel jobs

### False positives

**Possible cause**: Overly strict validation rules

**Fix**:
- Review the specific error
- If it's a legitimate edge case, update loader for backward compatibility
- Document the decision in a completion report

## Future Enhancements

Potential improvements for validation system:

1. **Parallel validation**: Validate tracks in parallel for faster CI
2. **Incremental validation**: Only validate changed files
3. **Validation caching**: Cache results for unchanged files
4. **Custom rules**: Allow project-specific validation rules
5. **Auto-fix suggestions**: Provide automated fixes for common issues
6. **Health score blocking**: Make health score threshold blocking once baseline established

## Related Documentation

- [Schema Migration Guide](../guides/SCHEMA_MIGRATION.md)
- [Schema Validation Guide](../guides/SCHEMA_VALIDATION.md)
- [Roadmap System Reference](../reference/ROADMAP_SYSTEM.md)
- [YAML Best Practices](../guides/YAML_BEST_PRACTICES.md)

## Support

**Issues with validation?**
1. Run locally with `--verbose` for details
2. Check this documentation for common errors
3. Review recent changes to models or loader
4. Create an issue if you believe validation is incorrect

---

**Status**: ✅ Active and enforced
**Pass rate**: 462/462 files (100%)
**Last updated**: 2025-11-20
