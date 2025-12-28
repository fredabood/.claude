# Task 7.1: Re-scan File Inventory for Audit-Created Files - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJVATAXPPTMVV24CF3E5JXV |
| Sprint | Sprint 7: Final Synchronization |
| Type | research |
| Complexity | **medium** |
| Priority | high |
| Estimated Tokens | 2,000 |
| Dependencies | Sprint 6 complete |

## Objective

Add all files created in Sprints 4-6 to FILE_INVENTORY.yaml to ensure the inventory reflects the complete state of the repository after all audit work is completed.

## Context

This task exists to resolve **artifact drift** identified during dependency analysis. The problem:

- Sprint 1 created FILE_INVENTORY.yaml capturing ~800 files
- Sprints 4-6 created ~15 new files (documentation, logs, reports)
- FILE_INVENTORY.yaml is now stale, missing these audit-created files

By re-scanning AFTER all other sprints complete, we ensure FILE_INVENTORY.yaml accurately reflects the final repository state.

## Files Expected to be Missing

### From Sprint 4 (Documentation Sync)

- `docs/reference/CLI_REFERENCE.md` (if regenerated)
- `docs/reference/MCP_REFERENCE.md` (if regenerated)
- Any new ADRs in `docs/architecture/adr/`
- Updated user journeys in `docs/journeys/`
- Updated walkthroughs in `docs/walkthroughs/`

### From Sprint 5 (Remediation & Reporting)

- `REMEDIATION_LOG.md`
- `INTEGRITY_AUDIT_REPORT.md`
- `MONITORING_RECOMMENDATIONS.md`
- Updated `COVERAGE_MATRIX.md`
- Updated `QUALITY_METRICS_BASELINE.md`
- Updated `AUDIT_PROGRESS_TRACKER.yaml`

### From Sprint 6 (Friction & Progress Tracking)

- `FRICTION_LOG.md` (updated)
- `AUDIT_MAINTENANCE_SCHEDULE.md`
- `AUTOMATION_RECOMMENDATIONS.md`
- `DASHBOARD_REQUIREMENTS.md`
- `PROGRESS_VALIDATION_REPORT.md`

### From Sprint 7 (This Sprint)

- Sprint 7 SPRINT_PLAN.md
- Sprint 7 task directories and TASK_PLAN.md files
- Any outputs created by this sprint

## Implementation Steps

### Step 1: Identify Sprint 1 Completion Baseline

```bash
# Find the commit when Sprint 1 inventory was created
git log --oneline --all -- ".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/" | head -5

# Store baseline for comparison
SPRINT1_COMPLETION=$(git log --format="%H" -1 -- ".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/FILE_INVENTORY.yaml")
```

### Step 2: Generate List of New Files Since Sprint 1

```bash
# Files added since Sprint 1 completion
git diff --name-only --diff-filter=A $SPRINT1_COMPLETION..HEAD

# Files in audit context directory created after Sprint 1
find .vibey/roadmap/context/tracks/comprehensive-audit-v2/ -type f -newer \
  .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/FILE_INVENTORY.yaml

# New markdown files since Sprint 1
find . -type f -name "*.md" -newer \
  .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/FILE_INVENTORY.yaml \
  -not -path "./.git/*" -not -path "./.venv/*"
```

### Step 3: Cross-Reference with Current FILE_INVENTORY.yaml

```bash
# Load current inventory
INVENTORY_FILE=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/FILE_INVENTORY.yaml"

# List files in current inventory
grep "path:" $INVENTORY_FILE | awk '{print $2}' > /tmp/current_inventory.txt

# List all current files
git ls-files > /tmp/current_files.txt

# Find files not in inventory
comm -23 <(sort /tmp/current_files.txt) <(sort /tmp/current_inventory.txt) > /tmp/missing_from_inventory.txt
```

### Step 4: Categorize Missing Files

For each missing file, determine:

1. **Category**: CORE-LIB, DOCUMENTATION, TESTS, SCRIPTS, CONFIG, FRAMEWORK, ROADMAP-DATA
2. **Subcategory**: Based on file location and type
3. **Source Sprint**: Which sprint created this file

```yaml
# Template for new inventory entries
- path: docs/reference/CLI_REFERENCE.md
  category: DOCUMENTATION
  subcategory: reference
  added_by: sprint-4
  file_type: markdown
  description: Auto-generated CLI command reference
```

### Step 5: Update FILE_INVENTORY.yaml

```bash
# Backup current inventory
cp $INVENTORY_FILE ${INVENTORY_FILE}.pre-sprint7

# Add new entries (manually or via script)
# Each entry should follow the established schema
```

### Step 6: Generate Audit-Created Files Report

Create a separate report listing all files created by the audit itself:

```markdown
# Audit-Created Files Report

## Summary
- Files created by audit: X
- Sprints that created files: 4, 5, 6, 7

## By Sprint

### Sprint 4 Files (Documentation Sync)
| File | Category | Description |
|------|----------|-------------|
| ... | ... | ... |

### Sprint 5 Files (Remediation & Reporting)
| File | Category | Description |
|------|----------|-------------|
| ... | ... | ... |

### Sprint 6 Files (Friction & Progress Tracking)
| File | Category | Description |
|------|----------|-------------|
| ... | ... | ... |

### Sprint 7 Files (Final Synchronization)
| File | Category | Description |
|------|----------|-------------|
| ... | ... | ... |
```

### Step 7: Validate Inventory Completeness

```bash
# Re-run comparison
git ls-files > /tmp/current_files.txt
grep "path:" $INVENTORY_FILE | awk '{print $2}' > /tmp/updated_inventory.txt
comm -23 <(sort /tmp/current_files.txt) <(sort /tmp/updated_inventory.txt)

# Should return empty or only expected exclusions (e.g., generated files)
```

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| Updated FILE_INVENTORY.yaml | `.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/` | Inventory with ~15 new entries |
| AUDIT_CREATED_FILES.md | `.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-7/outputs/` | Report of files created by audit |
| FILE_INVENTORY.yaml.pre-sprint7 | `.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/` | Backup of pre-Sprint-7 inventory |

## Acceptance Criteria

- [ ] All files created in Sprints 4-6 identified
- [ ] All Sprint 7 files (including this task's outputs) identified
- [ ] FILE_INVENTORY.yaml updated with all missing files
- [ ] Each new entry includes: path, category, subcategory, source sprint
- [ ] AUDIT_CREATED_FILES.md report generated
- [ ] Inventory file count reconciles with `git ls-files` count
- [ ] No legitimate files missing from inventory
- [ ] Backup of pre-Sprint-7 inventory preserved

## Estimated Time

| Activity | Duration |
|----------|----------|
| Identify baseline commit | 5 minutes |
| Generate new file list | 10 minutes |
| Cross-reference with inventory | 10 minutes |
| Categorize missing files | 15 minutes |
| Update FILE_INVENTORY.yaml | 15 minutes |
| Generate audit-created files report | 10 minutes |
| Validation | 10 minutes |
| **Total** | **~75 minutes** |

## Notes

- This task is the foundation for Tasks 7.2, 7.3, and 7.4
- Accuracy is critical - the updated inventory feeds into classification and coverage tasks
- Expected to find approximately 15 missing files, but actual count may vary
- Some files may have been created and then modified - track only the most recent version
