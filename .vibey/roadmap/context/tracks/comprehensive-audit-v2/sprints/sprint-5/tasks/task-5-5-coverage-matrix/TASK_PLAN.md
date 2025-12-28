# Task 5.5: Update COVERAGE_MATRIX.md with New File Counts - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJNKE2B2W5NJRTSRZWN4QT1 |
| Sprint | Sprint 5: Remediation & Reporting |
| Type | documentation |
| Complexity | **medium** |
| Priority | high |
| Estimated Tokens | 2,000 |
| Dependencies | Sprint 1 (FILE_INVENTORY.yaml updates) |

## Objective

Update the COVERAGE_MATRIX.md document to reflect current file counts and classification coverage. The original User Journey Audit (Dec 12-16) showed 99.4% coverage (720/724 files). The codebase has since grown to 800+ files - recalculate and document current coverage status.

## Input Requirements

1. Original COVERAGE_MATRIX.md from User Journey Audit
   - Location: `.vibey/roadmap/context/tracks/user-journey-audit/COVERAGE_MATRIX.md`
   - Baseline: 720 classified / 724 total files (99.4%)

2. Sprint 1 outputs from V2 Audit
   - Updated FILE_INVENTORY.yaml
   - FILE_INVENTORY_DELTA.yaml (new files since Dec 12)

3. Current file counts
   - Total files in repository
   - Classified files in inventory

## Background

### Coverage Calculation
```
Coverage % = (Classified Files / Total Files) * 100
```

### Target Coverage
- Target: 99%+ coverage
- All significant files should be classified
- Excluded: Generated files, cache, virtualenv, git objects

### Classification Categories (from taxonomy)
1. VIBEY - Core Python package code
2. DOCS - Documentation files
3. TESTS - Test files
4. CONFIG - Configuration files
5. SCRIPTS - Utility scripts
6. DATA - Data files (YAML, JSON)
7. OTHER - Miscellaneous files

## Implementation Steps

### Step 1: Count Total Repository Files

```bash
# Total files (excluding ignored directories)
find . -type f \
  -not -path "./.git/*" \
  -not -path "./.venv/*" \
  -not -path "./venv/*" \
  -not -path "./__pycache__/*" \
  -not -path "*/__pycache__/*" \
  -not -path "./.pytest_cache/*" \
  -not -path "./.mypy_cache/*" \
  -not -path "./.ruff_cache/*" \
  -not -path "./htmlcov/*" \
  -not -path "./*.egg-info/*" \
  -not -name "*.pyc" \
  -not -name "*.pyo" \
  -not -name ".DS_Store" \
  | wc -l

# Save to file for comparison
find . -type f [same exclusions] > current_files.txt
```

### Step 2: Count Files by Category

```bash
# Python files
find . -name "*.py" -not -path "./.venv/*" -not -path "./__pycache__/*" | wc -l

# Documentation
find docs -name "*.md" | wc -l

# Tests
find tests -type f -name "*.py" | wc -l

# YAML files
find . -name "*.yaml" -o -name "*.yml" | wc -l

# Configuration files
ls -la *.toml *.cfg *.ini .* 2>/dev/null | wc -l

# Scripts
find scripts -type f 2>/dev/null | wc -l
```

### Step 3: Count Classified Files

```bash
# Count entries in FILE_INVENTORY.yaml
# From Sprint 1 outputs
wc -l FILE_INVENTORY.yaml  # Approximate - need to parse

# Or parse properly
python3 -c "
import yaml
with open('FILE_INVENTORY.yaml') as f:
    inventory = yaml.safe_load(f)
print(f'Classified files: {len(inventory.get(\"files\", []))}')
"
```

### Step 4: Identify Unclassified Files

```bash
# Create list of classified paths
python3 -c "
import yaml
with open('FILE_INVENTORY.yaml') as f:
    inventory = yaml.safe_load(f)
for f in inventory.get('files', []):
    print(f['path'])
" > classified_files.txt

# Find unclassified
comm -23 <(sort current_files.txt) <(sort classified_files.txt) > unclassified_files.txt

# Count unclassified
wc -l unclassified_files.txt
```

### Step 5: Calculate Coverage Metrics

```python
#!/usr/bin/env python3
"""Calculate file coverage metrics."""

from pathlib import Path
import yaml

def calculate_coverage():
    # Load inventory
    inventory_path = Path('.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/FILE_INVENTORY.yaml')

    with open(inventory_path) as f:
        inventory = yaml.safe_load(f)

    classified = len(inventory.get('files', []))

    # Count total files (mimicking find command)
    total = 0
    excluded_dirs = {'.git', '.venv', 'venv', '__pycache__',
                     '.pytest_cache', '.mypy_cache', '.ruff_cache',
                     'htmlcov', '.egg-info'}
    excluded_exts = {'.pyc', '.pyo'}

    for path in Path('.').rglob('*'):
        if path.is_file():
            # Check exclusions
            if any(excl in path.parts for excl in excluded_dirs):
                continue
            if path.suffix in excluded_exts:
                continue
            if path.name == '.DS_Store':
                continue
            total += 1

    coverage = (classified / total) * 100 if total > 0 else 0

    return {
        'total_files': total,
        'classified_files': classified,
        'unclassified_files': total - classified,
        'coverage_percent': round(coverage, 1)
    }

if __name__ == '__main__':
    metrics = calculate_coverage()
    print(f"Total files: {metrics['total_files']}")
    print(f"Classified: {metrics['classified_files']}")
    print(f"Unclassified: {metrics['unclassified_files']}")
    print(f"Coverage: {metrics['coverage_percent']}%")
```

### Step 6: Compare with Dec 12 Baseline

| Metric | Dec 12 | Dec 28 | Delta |
|--------|--------|--------|-------|
| Total Files | 724 | ? | +? |
| Classified Files | 720 | ? | +? |
| Coverage % | 99.4% | ?% | ?% |

### Step 7: Update COVERAGE_MATRIX.md

Update the coverage matrix with current data:

```markdown
# User Journey Audit Coverage Matrix

## Overview

This document tracks documentation and audit coverage across the User Journey Audit track.

**Last Updated**: December 28, 2024 (Comprehensive Audit V2)

## File Coverage

### Current State (December 28, 2024)

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Files | XXX | 100% |
| Classified Files | XXX | XX.X% |
| Unclassified Files | X | X.X% |

### Coverage by Category

| Category | Files | % of Total |
|----------|-------|------------|
| VIBEY (Python) | XXX | XX% |
| DOCS (Documentation) | XX | X% |
| TESTS (Test files) | XXX | XX% |
| CONFIG (Configuration) | XX | X% |
| SCRIPTS (Utilities) | XX | X% |
| DATA (YAML/JSON) | XXX | XX% |
| OTHER | X | X% |

### Comparison with Baseline

| Metric | Dec 12, 2024 | Dec 28, 2024 | Change |
|--------|--------------|--------------|--------|
| Total Files | 724 | XXX | +XX |
| Classified | 720 | XXX | +XX |
| Coverage | 99.4% | XX.X% | +/-X.X% |

### New Files Added (Dec 12 - Dec 28)

| Category | New Files | Notable |
|----------|-----------|---------|
| VIBEY | +XX | services/, command_modules/ |
| DOCS | +XX | walkthroughs, ADRs |
| TESTS | +XX | integration tests |
| CONFIG | +X | new configs |

### Unclassified Files (if any)

| File Path | Likely Category | Action Needed |
|-----------|-----------------|---------------|
| ... | ... | Add to inventory |

## Audit Coverage

[Rest of existing audit coverage content...]
```

### Step 8: Update V2 Output Location

Copy updated matrix to V2 outputs:

```bash
# Copy to V2 sprint outputs
cp COVERAGE_MATRIX.md \
  .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-5/outputs/

# Also update original location
cp COVERAGE_MATRIX.md \
  .vibey/roadmap/context/tracks/user-journey-audit/
```

## Validation Checklist

- [ ] Total file count calculated (excluding git, venv, cache)
- [ ] Classified file count from FILE_INVENTORY.yaml
- [ ] Coverage percentage calculated
- [ ] Comparison with Dec 12 baseline documented
- [ ] New files identified by category
- [ ] Any unclassified files documented
- [ ] COVERAGE_MATRIX.md updated with current data
- [ ] Output copied to V2 sprint outputs

## Deliverables

1. **Updated COVERAGE_MATRIX.md**
   - Current file counts
   - Coverage percentage (target: 99%+)
   - Category breakdown
   - Baseline comparison table

2. **UNCLASSIFIED_FILES.txt** (if any)
   - List of files needing classification
   - Recommended categories

3. **COVERAGE_METRICS.yaml**
   - Machine-readable coverage data
   ```yaml
   coverage:
     date: 2024-12-28
     total_files: XXX
     classified_files: XXX
     coverage_percent: XX.X
     baseline:
       date: 2024-12-12
       total_files: 724
       classified_files: 720
       coverage_percent: 99.4
     delta:
       new_files: +XX
       new_classified: +XX
   ```

## Output Location

```
.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-5/outputs/
```

## Acceptance Criteria

- [ ] Coverage calculated correctly (classified / total)
- [ ] Coverage percentage is 99%+ (or unclassified files documented)
- [ ] Comparison with Dec 12 baseline is accurate
- [ ] All new files since Dec 12 identified
- [ ] COVERAGE_MATRIX.md is updated and complete
- [ ] Changes are ready for review

## Estimated Time

- Count total files: 10 minutes
- Count classified files: 10 minutes
- Identify unclassified: 15 minutes
- Calculate metrics: 10 minutes
- Update document: 30 minutes
- Review and validate: 15 minutes
- **Total: ~1.5 hours**

## Notes

- Original coverage was 99.4% (720/724) - excellent baseline
- New development (Dec 12-28) added significant files
- Goal is to maintain 99%+ coverage
- Unclassified files should be added to inventory or documented as intentionally excluded
- Consider automating coverage tracking as part of CI
