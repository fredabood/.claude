# Task 1.1: Scan Repository for New Files Since Dec 12 - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJKTRVZS618BM5ZZTQ3442Z |
| Sprint | Sprint 1: File Inventory Refresh |
| Type | research |
| Complexity | **medium** |
| Priority | high |
| Estimated Tokens | 2,000 |
| Dependencies | None (first task) |

## Objective

Use git commands to identify all files added, modified, or deleted since December 12, 2024. Generate a comprehensive categorized list that will serve as the foundation for all subsequent Sprint 1 tasks.

## Context

The original User Journey Audit was conducted December 12-19, 2024, classifying 720+ files. Since then, significant development has occurred. This task establishes the baseline delta for the entire sprint.

## Source Reference

The baseline commit should be identified from the User Journey Audit start date (December 12, 2024).

## Implementation Steps

### Step 1: Identify the Baseline Commit

```bash
# Find commits from Dec 12, 2024
git log --since="2024-12-12" --until="2024-12-13" --format="%H %s" | head -5

# Alternative: Find first User Journey Audit commit
git log --all --oneline --grep="user-journey" | tail -3

# Or get the commit hash for the first commit on Dec 12
git rev-list --after="2024-12-11" --before="2024-12-13" HEAD | tail -1
```

Store the baseline commit hash for subsequent operations:
```bash
BASELINE_COMMIT=$(git rev-list --after="2024-12-11" --before="2024-12-13" HEAD | tail -1)
echo "Baseline commit: $BASELINE_COMMIT"
```

### Step 2: Generate File Change Lists

```bash
# Create output directory
mkdir -p .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs

# Files added since Dec 12
git diff --name-only --diff-filter=A $BASELINE_COMMIT..HEAD > \
  .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/DELTA_REPORT_FILES_ADDED.txt

# Files modified since Dec 12
git diff --name-only --diff-filter=M $BASELINE_COMMIT..HEAD > \
  .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/DELTA_REPORT_FILES_MODIFIED.txt

# Files deleted since Dec 12
git diff --name-only --diff-filter=D $BASELINE_COMMIT..HEAD > \
  .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/DELTA_REPORT_FILES_DELETED.txt

# Files renamed since Dec 12 (with rename details)
git diff --name-status --diff-filter=R $BASELINE_COMMIT..HEAD > \
  .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/DELTA_REPORT_FILES_RENAMED.txt
```

### Step 3: Categorize Changes by File Type

```bash
OUTPUT_DIR=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs"

# Python files added
grep "\.py$" "$OUTPUT_DIR/DELTA_REPORT_FILES_ADDED.txt" > "$OUTPUT_DIR/python_files_added.txt" 2>/dev/null || true

# Documentation files added (markdown, rst, txt)
grep -E "\.(md|rst|txt)$" "$OUTPUT_DIR/DELTA_REPORT_FILES_ADDED.txt" > "$OUTPUT_DIR/docs_files_added.txt" 2>/dev/null || true

# YAML files added
grep "\.yaml$" "$OUTPUT_DIR/DELTA_REPORT_FILES_ADDED.txt" > "$OUTPUT_DIR/yaml_files_added.txt" 2>/dev/null || true

# Test files added
grep "^tests/" "$OUTPUT_DIR/DELTA_REPORT_FILES_ADDED.txt" > "$OUTPUT_DIR/test_files_added.txt" 2>/dev/null || true

# Core library files added (vibey/)
grep "^vibey/" "$OUTPUT_DIR/DELTA_REPORT_FILES_ADDED.txt" > "$OUTPUT_DIR/vibey_files_added.txt" 2>/dev/null || true

# Config files added
grep -E "\.(json|toml|ini|cfg)$" "$OUTPUT_DIR/DELTA_REPORT_FILES_ADDED.txt" > "$OUTPUT_DIR/config_files_added.txt" 2>/dev/null || true
```

### Step 4: Generate Summary Statistics

```bash
OUTPUT_DIR=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs"

echo "=== File Change Summary Since Dec 12, 2024 ===" > "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "## Overview" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "| Change Type | Count |" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "|-------------|-------|" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "| Added | $(wc -l < "$OUTPUT_DIR/DELTA_REPORT_FILES_ADDED.txt" | tr -d ' ') |" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "| Modified | $(wc -l < "$OUTPUT_DIR/DELTA_REPORT_FILES_MODIFIED.txt" | tr -d ' ') |" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "| Deleted | $(wc -l < "$OUTPUT_DIR/DELTA_REPORT_FILES_DELETED.txt" | tr -d ' ') |" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "| Renamed | $(wc -l < "$OUTPUT_DIR/DELTA_REPORT_FILES_RENAMED.txt" | tr -d ' ') |" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "## By File Type (Added)" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "| Category | Count |" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "|----------|-------|" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "| Python (.py) | $(wc -l < "$OUTPUT_DIR/python_files_added.txt" 2>/dev/null | tr -d ' ' || echo 0) |" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "| Documentation (.md/.rst/.txt) | $(wc -l < "$OUTPUT_DIR/docs_files_added.txt" 2>/dev/null | tr -d ' ' || echo 0) |" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "| YAML (.yaml) | $(wc -l < "$OUTPUT_DIR/yaml_files_added.txt" 2>/dev/null | tr -d ' ' || echo 0) |" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "| Tests (tests/) | $(wc -l < "$OUTPUT_DIR/test_files_added.txt" 2>/dev/null | tr -d ' ' || echo 0) |" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
echo "| Core Library (vibey/) | $(wc -l < "$OUTPUT_DIR/vibey_files_added.txt" 2>/dev/null | tr -d ' ' || echo 0) |" >> "$OUTPUT_DIR/DELTA_SUMMARY.md"
```

### Step 5: Detailed Change Analysis

For significant files, extract additional context:

```bash
# Show files with most changes (by diff size)
git diff --stat $BASELINE_COMMIT..HEAD | head -30

# Identify major refactoring (files with significant line changes)
git diff --numstat $BASELINE_COMMIT..HEAD | \
  awk '$1+$2 > 100 {print $3, "additions:", $1, "deletions:", $2}' | \
  sort -t: -k2 -nr | head -20
```

### Step 6: Validate Completeness

```bash
# Cross-check: current file count
echo "Current tracked files: $(git ls-files | wc -l | tr -d ' ')"

# Files in working tree (excluding .git and .venv)
echo "Working tree files: $(find . -type f -not -path "./.git/*" -not -path "./.venv/*" | wc -l | tr -d ' ')"

# Expected: original 720 + added - deleted = current
```

## Deliverables

All outputs should be placed in:
```
.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/
```

| Deliverable | Description |
|-------------|-------------|
| `DELTA_REPORT_FILES_ADDED.txt` | Complete list of files added since Dec 12 |
| `DELTA_REPORT_FILES_MODIFIED.txt` | Complete list of files modified since Dec 12 |
| `DELTA_REPORT_FILES_DELETED.txt` | Complete list of files deleted since Dec 12 |
| `DELTA_REPORT_FILES_RENAMED.txt` | Files renamed with old/new names |
| `DELTA_SUMMARY.md` | Summary statistics and categorization |
| `python_files_added.txt` | Python files added (subset) |
| `docs_files_added.txt` | Documentation files added (subset) |
| `yaml_files_added.txt` | YAML files added (subset) |
| `vibey_files_added.txt` | Core library files added (subset) |

## Acceptance Criteria

- [ ] Baseline commit from Dec 12, 2024 identified and documented
- [ ] All file additions since Dec 12 captured in DELTA_REPORT_FILES_ADDED.txt
- [ ] All file modifications since Dec 12 captured in DELTA_REPORT_FILES_MODIFIED.txt
- [ ] All file deletions since Dec 12 captured in DELTA_REPORT_FILES_DELETED.txt
- [ ] File renames tracked with source/destination paths
- [ ] Changes categorized by file type (Python, docs, YAML, etc.)
- [ ] Changes categorized by directory (vibey/, tests/, docs/, etc.)
- [ ] Summary statistics generated and verified
- [ ] File counts reconciled (original + added - deleted = current)
- [ ] Output files created in designated outputs/ directory

## Estimated Time

| Activity | Duration |
|----------|----------|
| Baseline commit identification | 5 minutes |
| Git diff operations | 5 minutes |
| File categorization | 10 minutes |
| Summary generation | 10 minutes |
| Validation and cross-checking | 10 minutes |
| **Total** | **40 minutes** |

## Edge Cases

1. **Binary files**: May appear in diff but won't have line-based stats
2. **Submodules**: If present, may need special handling
3. **Large renames**: Git may not detect renames if files changed significantly
4. **Files in .gitignore**: Won't appear in git operations but may exist in working tree

## Notes

- This task is the foundation for all other Sprint 1 tasks
- The delta lists generated here will be referenced by Tasks 1.2 through 1.9
- Accuracy is critical - errors propagate to all downstream tasks
- Consider storing the baseline commit hash in a file for reference by other tasks
