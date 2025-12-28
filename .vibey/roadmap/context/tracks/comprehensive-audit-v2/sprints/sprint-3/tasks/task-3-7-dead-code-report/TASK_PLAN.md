# Task 3.7: Update Dead Code Report with New File Coverage

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJNKE2B2W5NJRTSRZWN4QSZ |
| Sprint | 3 - Codebase Health Analysis |
| Type | documentation |
| Complexity | medium |
| Priority | medium |
| Estimated Tokens | ~2,000 |
| Dependencies | Task 3.1 (initial dead code audit), Task 3.6 (updated file classifications) |

---

## Objective

Re-run vulture dead code analysis after file classifications have been updated in Task 3.6. Compare current findings against the December 12, 2024 baseline report (if available) to document new dead code introduced and previously flagged code that has been resolved or is now in use.

---

## Commands

### 1. Run Fresh Vulture Analysis

```bash
# Run vulture with same parameters as Task 3.1
vulture vibey/ --min-confidence 80 > .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-3/outputs/vulture_updated_output.txt

# Run with sorting for comparison
vulture vibey/ --sort-by-size --min-confidence 80 > .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-3/outputs/vulture_sorted_updated.txt

# Run with whitelist from Task 3.1
vulture vibey/ .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-3/outputs/vulture_whitelist.py --min-confidence 80
```

### 2. Compare with Baseline

```bash
# Diff the raw outputs
diff .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-3/outputs/vulture_raw_output.txt \
     .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-3/outputs/vulture_updated_output.txt

# Count baseline vs updated
wc -l .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-3/outputs/vulture_raw_output.txt
wc -l .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-3/outputs/vulture_updated_output.txt
```

### 3. Analyze Changes

```bash
# Find new dead code (in updated but not in baseline)
comm -13 <(sort vulture_raw_output.txt) <(sort vulture_updated_output.txt) > new_dead_code.txt

# Find resolved dead code (in baseline but not in updated)
comm -23 <(sort vulture_raw_output.txt) <(sort vulture_updated_output.txt) > resolved_dead_code.txt
```

### 4. Check Specific Modules

```bash
# Check if previously flagged items are now in use
for file in $(cat resolved_dead_code.txt | cut -d: -f1 | sort -u); do
  echo "=== Checking imports of $file ==="
  grep -r "from $(echo $file | sed 's/\//./g' | sed 's/.py$//')" vibey/ tests/
done
```

---

## Analysis Steps

### Step 1: Establish Comparison Points

| Comparison | Source | Date |
|------------|--------|------|
| Baseline (Task 3.1) | vulture_raw_output.txt | Sprint 3 start |
| Updated | vulture_updated_output.txt | After Task 3.6 |
| Dec 12 Audit | (if exists) | Dec 12, 2024 |

### Step 2: Run Updated Vulture Analysis

1. Execute vulture on current codebase
2. Use same confidence threshold (80%)
3. Apply whitelist from Task 3.1

### Step 3: Generate Comparison Data

Create comparison table:

| Metric | Task 3.1 | Updated | Delta |
|--------|----------|---------|-------|
| Total items flagged | X | Y | +/- Z |
| Unused functions | X | Y | +/- Z |
| Unused classes | X | Y | +/- Z |
| Unused variables | X | Y | +/- Z |
| Unused imports | X | Y | +/- Z |

### Step 4: Categorize Changes

**New Dead Code (Introduced Since Task 3.1):**

| File:Line | Item | Type | Introduced By |
|-----------|------|------|---------------|
| path:123 | func_name | function | commit/PR |

**Resolved Dead Code (No Longer Flagged):**

| File:Line | Item | Type | Resolution |
|-----------|------|------|------------|
| path:456 | old_func | function | Now used by X |

**Unchanged Dead Code (Still Flagged):**

| File:Line | Item | Type | Reason for Retention |
|-----------|------|------|---------------------|
| path:789 | legacy_func | function | Backwards compat |

### Step 5: Compare with Dec 12 Baseline (If Available)

If December 12 dead code report exists:

1. Load Dec 12 findings
2. Compare with current updated findings
3. Calculate trend over ~2 week period

| Metric | Dec 12 | Current | Trend |
|--------|--------|---------|-------|
| Dead code items | X | Y | improving/worsening |

### Step 6: Generate Recommendations

Based on comparison:

1. **Cleanup Candidates**: Confirmed dead code safe to remove
2. **Monitor Items**: New dead code to watch
3. **Keep Items**: Dead code with valid retention reasons

---

## Output Format

### DEAD_CODE_UPDATE_REPORT.md Structure

```markdown
# Dead Code Update Report

**Generated:** [Date]
**Comparison Period:** Task 3.1 to Post-Task 3.6
**Dec 12 Baseline:** [Available/Not Available]

---

## Executive Summary

| Metric | Task 3.1 | Updated | Change |
|--------|----------|---------|--------|
| Total Items | X | Y | +/- Z |
| Net Change | - | - | +/- Z items |

**Overall Status:** [Improved/Worsened/Stable]

---

## Comparison Summary

### By Category

| Category | Task 3.1 | Updated | Delta |
|----------|----------|---------|-------|
| Unused Functions | X | Y | +/- Z |
| Unused Classes | X | Y | +/- Z |
| Unused Variables | X | Y | +/- Z |
| Unused Imports | X | Y | +/- Z |

### By Module

| Module | Task 3.1 | Updated | Delta |
|--------|----------|---------|-------|
| cli | X | Y | +/- Z |
| operations | X | Y | +/- Z |
| roadmap | X | Y | +/- Z |
| mcp | X | Y | +/- Z |
| adapters | X | Y | +/- Z |
| common | X | Y | +/- Z |

---

## New Dead Code (Introduced)

Items flagged in updated scan but not in Task 3.1:

| # | File | Line | Item | Type | Confidence | Notes |
|---|------|------|------|------|------------|-------|
| 1 | path/to/file.py | 123 | new_unused_func | function | 80% | Added in commit X |

**Total New Items:** X

---

## Resolved Dead Code (No Longer Flagged)

Items flagged in Task 3.1 but not in updated scan:

| # | File | Line | Item | Type | Resolution |
|---|------|------|------|------|------------|
| 1 | path/to/file.py | 456 | was_unused | function | Now imported by Y |

**Total Resolved Items:** X

---

## Unchanged Dead Code

Items flagged in both scans:

| # | File | Line | Item | Type | Recommendation |
|---|------|------|------|------|----------------|
| 1 | path/to/file.py | 789 | still_unused | function | Remove |
| 2 | path/to/legacy.py | 101 | compat_func | function | Keep (backwards compat) |

**Total Unchanged Items:** X

---

## Dec 12 Comparison (If Available)

### Trend Analysis

| Metric | Dec 12 | Task 3.1 | Updated | 2-Week Trend |
|--------|--------|----------|---------|--------------|
| Total Items | X | Y | Z | +/- N |
| Functions | X | Y | Z | +/- N |
| Classes | X | Y | Z | +/- N |

### Trend Interpretation

- **Improving**: Dead code count decreasing over time
- **Stable**: Minor fluctuations within normal range
- **Worsening**: Dead code accumulating faster than cleanup

---

## Recommendations

### Immediate Cleanup (Safe to Remove)

| Priority | File | Item | Lines | Impact |
|----------|------|------|-------|--------|
| P0 | path/file.py | unused_large_func | 50 | High |
| P1 | path/file.py | unused_small_func | 10 | Low |

### Monitor (New Dead Code)

| File | Item | Reason to Monitor |
|------|------|-------------------|
| path/file.py | new_func | May be needed for planned feature |

### Keep (Valid Retention)

| File | Item | Retention Reason |
|------|------|------------------|
| path/legacy.py | old_api | Backwards compatibility until v3.0 |

---

## Action Items

1. [ ] Remove X confirmed dead code items
2. [ ] Add Y items to whitelist
3. [ ] Schedule review for Z monitored items
4. [ ] Update DEAD_CODE_REPORT.md baseline

---

## Appendix: Raw Diff

<details>
<summary>View raw diff output</summary>

```diff
[diff output here]
```

</details>
```

---

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| `DEAD_CODE_UPDATE_REPORT.md` | `sprint-3/outputs/` | Comparison report with analysis |
| `vulture_updated_output.txt` | `sprint-3/outputs/` | Raw updated vulture output |
| `new_dead_code.txt` | `sprint-3/outputs/` | List of newly introduced dead code |
| `resolved_dead_code.txt` | `sprint-3/outputs/` | List of resolved dead code |

---

## Acceptance Criteria

- [ ] Vulture re-run completed on updated codebase
- [ ] Results compared with Task 3.1 baseline
- [ ] New dead code items identified and documented
- [ ] Resolved dead code items identified and documented
- [ ] Unchanged items listed with retention recommendations
- [ ] Dec 12 comparison included (if baseline available)
- [ ] Trend analysis provided
- [ ] Actionable cleanup recommendations generated
- [ ] Report ready to update baseline for next audit cycle

---

## Notes

- This task must run AFTER Task 3.6 (scripts classification update)
- Findings feed into Task 3.5 (health scorecard) for final metrics
- Consider automating this comparison for CI/CD integration
- Document any false positive patterns discovered for whitelist improvement
