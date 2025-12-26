# Task 7: Audit Codebase for Dead Code and Orphaned Files

**Task ID**: `01KDDE9NEKAH3BM9PRFPHNNCN9`
**Type**: research
**Priority**: medium
**Estimated Tokens**: 3,000

## Objective

Run static analysis to identify dead code, unused imports, orphaned files, and migration scripts that were never executed. Generate cleanup recommendations.

## Methodology

### Step 1: Run Vulture for Dead Code Detection

```bash
# Install vulture if needed
pip install vulture

# Run on entire codebase
vulture vibey/ --min-confidence 80 > dead_code_report.txt

# Run with whitelist for false positives
vulture vibey/ vulture_whitelist.py --min-confidence 80
```

### Step 2: Find Unused Imports

```bash
# Using autoflake to detect unused imports
pip install autoflake

autoflake --check --remove-all-unused-imports -r vibey/ 2>&1 | tee unused_imports.txt
```

### Step 3: Find Orphaned Python Files

```bash
# Files not imported anywhere
for f in $(find vibey -name "*.py" -not -name "__init__.py"); do
    module=$(echo $f | sed 's|/|.|g' | sed 's|.py$||')
    if ! grep -r "import.*$module\|from.*$module" vibey/ --include="*.py" -q; then
        echo "ORPHAN: $f"
    fi
done
```

### Step 4: Find Orphaned Test Files

```bash
# Test files with no corresponding source
for test_file in $(find tests -name "test_*.py"); do
    # Extract module name being tested
    module_name=$(basename $test_file | sed 's/^test_//' | sed 's/.py$//')

    # Check if corresponding source exists
    if ! find vibey -name "${module_name}.py" -o -name "${module_name}" -type d | grep -q .; then
        echo "ORPHAN TEST: $test_file (no source: $module_name)"
    fi
done
```

### Step 5: Find Unexecuted Migration Scripts

```bash
# Migration scripts that exist but were never run
find vibey -name "*migrat*.py" -o -name "*migrate*.py" | while read script; do
    echo "=== $script ==="
    # Check if it has a main block
    grep -l "if __name__" "$script" && echo "Has main block"
    # Check git history for execution evidence
    git log --all --oneline --grep="$(basename $script)"
done
```

### Step 6: Find Abandoned Feature Branches

```bash
# Stale branches with unmerged work
git branch -a --no-merged main | grep -v HEAD
```

## Expected Output

```markdown
## Codebase Health Audit Results

### Dead Code (N items)
| File | Line | Code | Confidence |
|------|------|------|------------|
| vibey/foo.py | 42 | unused_function | 90% |

### Unused Imports (N files)
| File | Unused Imports |
|------|----------------|
| vibey/bar.py | os, sys, json |

### Orphaned Files (N files)
| File | Reason | Recommendation |
|------|--------|----------------|
| vibey/legacy/old.py | Not imported anywhere | Delete or archive |

### Orphaned Tests (N files)
| Test File | Missing Source | Recommendation |
|-----------|----------------|----------------|
| tests/test_widget.py | widget.py | Delete test or create source |

### Unexecuted Migrations (N scripts)
| Script | Has Main | Evidence of Execution |
|--------|----------|----------------------|
| migrate_to_v2.py | Yes | None found |

### Stale Branches (N branches)
| Branch | Last Commit | Status |
|--------|-------------|--------|
| feature/old-thing | 2025-10-01 | Abandoned |
```

## Cleanup Recommendations

For each finding, provide:
1. **Severity**: Critical / High / Medium / Low
2. **Action**: Delete / Archive / Review / Keep
3. **Risk**: Impact of removal
4. **Dependencies**: What might break

## Success Criteria

- [ ] Vulture analysis completed
- [ ] Unused imports identified
- [ ] Orphaned source files found
- [ ] Orphaned test files found
- [ ] Migration scripts analyzed
- [ ] Stale branches identified
- [ ] Cleanup recommendations generated

## Tools

- Vulture (dead code detection)
- Autoflake (unused imports)
- Bash/find (file analysis)
- Git (branch analysis)

## Deliverables

1. `codebase-audit-results.json` - Structured findings
2. Cleanup script (optional, for safe items)
3. Summary section for final report
