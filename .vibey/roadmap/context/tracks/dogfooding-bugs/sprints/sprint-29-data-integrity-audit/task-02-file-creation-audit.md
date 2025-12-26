# Task 2: Audit Completed File Creation Tasks Against Filesystem

**Task ID**: `01KDC9293X9AMMB8XRXQ7TJB1M`
**Type**: research
**Priority**: high
**Estimated Tokens**: 3,000

## Objective

Verify that all completed tasks claiming to create files, directories, or artifacts actually resulted in those files existing in the repository.

## Methodology

### Step 1: Query Completed File Creation Tasks

```sql
SELECT t.id, t.title, t.description, s.name as sprint_name, tr.name as track_name
FROM tasks t
JOIN sprints s ON t.sprint_id = s.id
JOIN tracks tr ON s.track_id = tr.id
WHERE t.status = 'completed'
AND (
    LOWER(t.title) LIKE '%create %'
    OR LOWER(t.title) LIKE '%add %'
    OR LOWER(t.title) LIKE '%implement %'
    OR LOWER(t.title) LIKE '%write %'
    OR LOWER(t.description) LIKE '%create file%'
    OR LOWER(t.description) LIKE '%new file%'
    OR LOWER(t.description) LIKE '%.py%'
    OR LOWER(t.description) LIKE '%.md%'
    OR LOWER(t.description) LIKE '%.yaml%'
)
ORDER BY tr.name, s.name;
```

### Step 2: Extract Expected File Paths

Parse task titles and descriptions for:
- Explicit file paths (e.g., `vibey/operations/foo.py`)
- File patterns (e.g., "create migration script")
- Directory references (e.g., "add to vibey/adapters/")

Common patterns to match:
```regex
# Python files
vibey/[\w/]+\.py
tests/[\w/]+\.py

# Markdown files
docs/[\w/]+\.md
\.vibey/roadmap/context/[\w/]+\.md

# YAML files
\.vibey/[\w/]+\.yaml

# Config files
\.github/[\w/]+\.yml
```

### Step 3: Verify File Existence

```bash
# For each extracted path
test -f "$path" && echo "EXISTS: $path" || echo "MISSING: $path"
```

### Step 4: Check Git for Historical Existence

For missing files, check if they ever existed:
```bash
git log --all --full-history -- "$path"
```

This distinguishes between:
- Never created (phantom completion)
- Created then deleted (intentional removal vs accidental)

## Expected Output

```markdown
## File Creation Audit Results

### Verified Creations (N tasks)
| Task ID | Title | Files Verified |
|---------|-------|----------------|
| ... | ... | vibey/foo.py, tests/test_foo.py |

### Missing Files (N tasks)
| Task ID | Title | Expected Files | Status |
|---------|-------|----------------|--------|
| ... | ... | migrate_to_v2.py | Never existed |
| ... | ... | schema_v2.sql | Deleted in abc123 |

### Recommendations
- Revert N tasks to not_started
- Investigate N deletions for intentionality
```

## Key Files to Verify

Focus areas based on preliminary analysis:
- `vibey/roadmap/database/migrate_to_v2.py` - execution script
- `vibey/roadmap/database/schema_v2.sql` - applied schema
- `docs/architecture/adr/` - claimed ADRs
- `vibey/operations/context/` - context system files

## Success Criteria

- [ ] All completed file creation tasks queried
- [ ] File paths extracted from task descriptions
- [ ] Each path verified against filesystem
- [ ] Missing files checked in git history
- [ ] Categorization: never existed vs deleted
- [ ] Recommendations generated

## Tools

- SQLite CLI for task queries
- Bash for file existence checks
- Git for history verification
- Python regex for path extraction

## Deliverables

1. `file-creation-audit-results.json` - Structured audit data
2. Summary section for final audit report
