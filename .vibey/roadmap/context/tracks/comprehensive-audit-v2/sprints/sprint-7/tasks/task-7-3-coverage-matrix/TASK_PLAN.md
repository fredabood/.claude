# Task 7.3: Regenerate COVERAGE_MATRIX with Final File Counts - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJVATAXPPTMVV24CF3E5JXX |
| Sprint | Sprint 7: Final Synchronization |
| Type | documentation |
| Complexity | **medium** |
| Priority | high |
| Estimated Tokens | 1,500 |
| Dependencies | Task 7.2 (classification updates) |

## Objective

Recalculate the COVERAGE_MATRIX.md with final file counts after all audit work is complete, compare with the Sprint 5 version, and document the delta caused by audit-created files.

## Context

This task exists to resolve **artifact drift** in coverage reporting:

- COVERAGE_MATRIX.md was created in Sprint 5 with ~800 files
- Sprints 4-6 created ~15 new files
- The Sprint 5 matrix claims coverage percentages that are now inaccurate

Without this regeneration:
- Coverage percentages would be overstated (calculated against old total)
- Category distributions would be incorrect
- Final audit report would contain stale metrics

By regenerating AFTER all files are created and classified, we ensure the coverage matrix reflects true final state.

## Expected Delta

Based on sprint plans, approximate changes:

| Metric | Sprint 5 | Sprint 7 (Expected) | Delta |
|--------|----------|---------------------|-------|
| Total files | ~800 | ~815 | +15 |
| Classified | ~795 | ~810 | +15 |
| Coverage % | 99.4% | 99.4% | ~0% |
| DOCUMENTATION | ~45 | ~55 | +10 |
| FRAMEWORK | ~120 | ~125 | +5 |

Note: Coverage percentage should remain similar because new files are also classified.

## Implementation Steps

### Step 1: Load Updated Inventory and Classifications

```bash
# From Task 7.1 output
INVENTORY=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/FILE_INVENTORY.yaml"

# From Task 7.2 output
CLASSIFICATION=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/DOCS_FILE_CLASSIFICATION.yaml"

# Sprint 5 coverage matrix (for comparison)
SPRINT5_MATRIX=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-5/outputs/COVERAGE_MATRIX.md"
```

### Step 2: Calculate File Counts by Category

```bash
# Total files in repository
TOTAL_FILES=$(git ls-files | wc -l | tr -d ' ')

# Files in inventory
INVENTORY_COUNT=$(grep "path:" $INVENTORY | wc -l | tr -d ' ')

# Files classified
CLASSIFIED_COUNT=$(grep "path:" $CLASSIFICATION | wc -l | tr -d ' ')
```

```python
#!/usr/bin/env python3
"""Calculate coverage metrics from inventory and classification files."""

import yaml
from collections import defaultdict
from pathlib import Path

def load_yaml(filepath):
    with open(filepath) as f:
        return yaml.safe_load(f)

def calculate_coverage(inventory_file, classification_file):
    """Calculate coverage metrics."""

    inventory = load_yaml(inventory_file)
    classification = load_yaml(classification_file)

    # Count by category
    category_counts = defaultdict(int)
    subcategory_counts = defaultdict(lambda: defaultdict(int))

    for entry in classification.get('files', []):
        category = entry.get('category', 'UNCLASSIFIED')
        subcategory = entry.get('subcategory', 'unknown')
        category_counts[category] += 1
        subcategory_counts[category][subcategory] += 1

    # Total files
    total_files = len(inventory.get('files', []))
    classified_files = sum(category_counts.values())
    coverage_percent = (classified_files / total_files * 100) if total_files > 0 else 0

    return {
        'total_files': total_files,
        'classified_files': classified_files,
        'coverage_percent': round(coverage_percent, 2),
        'by_category': dict(category_counts),
        'by_subcategory': {k: dict(v) for k, v in subcategory_counts.items()},
        'unclassified': total_files - classified_files
    }
```

### Step 3: Compare with Sprint 5 Matrix

Extract Sprint 5 metrics for comparison:

```bash
# Parse Sprint 5 matrix for key metrics
grep -E "Total files|Classified|Coverage" $SPRINT5_MATRIX
```

Create comparison table:

```python
def compare_matrices(sprint5_metrics, sprint7_metrics):
    """Generate comparison between Sprint 5 and Sprint 7 matrices."""

    comparison = {
        'metrics': [],
        'categories': []
    }

    # Overall metrics
    for metric in ['total_files', 'classified_files', 'coverage_percent']:
        sprint5_val = sprint5_metrics.get(metric, 0)
        sprint7_val = sprint7_metrics.get(metric, 0)
        delta = sprint7_val - sprint5_val
        comparison['metrics'].append({
            'metric': metric,
            'sprint5': sprint5_val,
            'sprint7': sprint7_val,
            'delta': delta
        })

    # By category
    all_categories = set(sprint5_metrics.get('by_category', {}).keys()) | \
                     set(sprint7_metrics.get('by_category', {}).keys())

    for category in sorted(all_categories):
        sprint5_val = sprint5_metrics.get('by_category', {}).get(category, 0)
        sprint7_val = sprint7_metrics.get('by_category', {}).get(category, 0)
        comparison['categories'].append({
            'category': category,
            'sprint5': sprint5_val,
            'sprint7': sprint7_val,
            'delta': sprint7_val - sprint5_val
        })

    return comparison
```

### Step 4: Generate Final COVERAGE_MATRIX.md

```markdown
# Coverage Matrix - Final (Sprint 7)

**Generated:** [Date]
**Audit Track:** Comprehensive Repository Audit V2
**Sprint:** 7 - Final Synchronization

## Executive Summary

This matrix represents the **final coverage state** after completing all audit sprints.
Previous version was generated in Sprint 5; this update includes files created in Sprints 4-6.

## Overall Coverage

| Metric | Value |
|--------|-------|
| Total Files | X |
| Classified Files | Y |
| **Coverage Percentage** | Z% |
| Unclassified Files | N |

## Coverage by Category

| Category | File Count | Percentage | Delta from Sprint 5 |
|----------|------------|------------|---------------------|
| CORE-LIB | X | Y% | +N |
| DOCUMENTATION | X | Y% | +N |
| TESTS | X | Y% | +N |
| FRAMEWORK | X | Y% | +N |
| CONFIG | X | Y% | +N |
| SCRIPTS | X | Y% | +N |
| ROADMAP-DATA | X | Y% | +N |
| **Total** | **X** | **100%** | **+N** |

## Documentation Subcategory Breakdown

| Subcategory | Count | Percentage | Delta |
|-------------|-------|------------|-------|
| reference | X | Y% | +N |
| architecture | X | Y% | +N |
| guides | X | Y% | +N |
| operational | X | Y% | +N |
| reports | X | Y% | +N |
| planning | X | Y% | +N |

## Framework Subcategory Breakdown

| Subcategory | Count | Percentage | Delta |
|-------------|-------|------------|-------|
| roadmap-context | X | Y% | +N |
| config | X | Y% | 0 |
| templates | X | Y% | 0 |

## Comparison: Sprint 5 vs Sprint 7

### Overall Metrics

| Metric | Sprint 5 | Sprint 7 | Delta |
|--------|----------|----------|-------|
| Total Files | ~800 | X | +Y |
| Classified Files | ~795 | X | +Y |
| Coverage % | 99.4% | X% | +Y% |

### Category Changes

| Category | Sprint 5 | Sprint 7 | Change |
|----------|----------|----------|--------|
| DOCUMENTATION | A | B | +C |
| FRAMEWORK | D | E | +F |
| (others) | ... | ... | ... |

## Audit-Created Files Impact

Files created by the audit itself contribute to the delta:

| Source Sprint | Files Added | Categories |
|---------------|-------------|------------|
| Sprint 4 | X | DOCUMENTATION (reference, guides) |
| Sprint 5 | Y | FRAMEWORK (roadmap-context) |
| Sprint 6 | Z | FRAMEWORK (roadmap-context) |
| Sprint 7 | W | FRAMEWORK (roadmap-context) |
| **Total** | **~15** | |

## Unclassified Files

[List any remaining unclassified files, if any]

## Notes

- Coverage percentage remains high (~99%) because new files were also classified
- Most additions are FRAMEWORK/roadmap-context (audit artifacts)
- DOCUMENTATION/reference increased due to regenerated CLI/MCP references
```

### Step 5: Create Coverage Delta Summary

A concise summary of what changed:

```markdown
# Coverage Delta Summary: Sprint 5 to Sprint 7

## Quick Stats
- Files added: ~15
- Coverage impact: Negligible (new files classified)
- Primary change: FRAMEWORK category growth

## Key Changes
1. **DOCUMENTATION/reference**: +2 (CLI_REFERENCE.md, MCP_REFERENCE.md regenerated)
2. **FRAMEWORK/roadmap-context**: +10 (Sprint 5-7 outputs)
3. **Other**: +3 (misc audit artifacts)

## Why the Delta?
The audit itself creates artifacts. Sprint 7 exists specifically to capture
these self-referential additions and ensure final metrics are accurate.
```

### Step 6: Validate Coverage Calculations

```bash
# Cross-check: sum of categories should equal total classified
CATEGORY_SUM=$(python3 -c "print(sum([X, Y, Z, ...]))")  # Replace with actual counts
if [ "$CATEGORY_SUM" -eq "$CLASSIFIED_COUNT" ]; then
    echo "SUCCESS: Category counts reconcile"
fi

# Cross-check: total in inventory matches git ls-files
GIT_FILES=$(git ls-files | wc -l | tr -d ' ')
if [ "$INVENTORY_COUNT" -eq "$GIT_FILES" ]; then
    echo "SUCCESS: Inventory matches git"
fi
```

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| COVERAGE_MATRIX.md | `.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-7/outputs/` | Final coverage matrix |
| COVERAGE_DELTA_SUMMARY.md | `.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-7/outputs/` | Concise delta summary |
| coverage_metrics.yaml | `.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-7/outputs/` | Machine-readable metrics |

## Acceptance Criteria

- [ ] COVERAGE_MATRIX.md generated with final file counts
- [ ] All categories and subcategories calculated
- [ ] Comparison with Sprint 5 matrix documented
- [ ] Delta explained (which sprints added which files)
- [ ] Category sums reconcile with total classified
- [ ] Inventory count matches `git ls-files` count
- [ ] Coverage percentage accurately calculated
- [ ] Machine-readable metrics exported (YAML)

## Estimated Time

| Activity | Duration |
|----------|----------|
| Load inventory and classifications | 5 minutes |
| Calculate category counts | 10 minutes |
| Compare with Sprint 5 | 10 minutes |
| Generate COVERAGE_MATRIX.md | 15 minutes |
| Generate delta summary | 10 minutes |
| Validation | 10 minutes |
| **Total** | **~60 minutes** |

## Notes

- This task depends on Tasks 7.1 and 7.2 completing first
- The Sprint 5 matrix should be preserved for comparison (not overwritten)
- New matrix goes in Sprint 7 outputs, not Sprint 5 outputs
- Machine-readable output (YAML) enables future automated comparisons
- Coverage percentage should stay high since new files are classified
