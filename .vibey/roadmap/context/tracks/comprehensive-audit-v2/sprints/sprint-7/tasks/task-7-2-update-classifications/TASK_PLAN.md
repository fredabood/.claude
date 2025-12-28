# Task 7.2: Update File Classifications with Sprint 4-6 Docs - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJVATAXPPTMVV24CF3E5JXW |
| Sprint | Sprint 7: Final Synchronization |
| Type | research |
| Complexity | **medium** |
| Priority | high |
| Estimated Tokens | 1,500 |
| Dependencies | Task 7.1 (file inventory re-scan) |

## Objective

Update DOCS_FILE_CLASSIFICATION.yaml with all new documentation files created during Sprints 4-6, applying the established classification taxonomy to ensure consistent categorization across all documentation.

## Context

This task exists to resolve **artifact drift** in the documentation classification system:

- DOCS_FILE_CLASSIFICATION.yaml was created during earlier sprints
- Sprints 4-6 created new documentation files (references, guides, logs, reports)
- These new files are not classified, making coverage metrics inaccurate

By updating classifications AFTER all documentation is created, we ensure:
1. Every documentation file has a classification
2. COVERAGE_MATRIX.md (Task 7.3) reflects accurate category counts
3. Future audits have a complete classification baseline

## Classification Taxonomy

### Category Definitions

| Category | Description | File Patterns |
|----------|-------------|---------------|
| DOCUMENTATION | User-facing documentation | `docs/**/*.md` |
| FRAMEWORK | Internal framework files | `.vibey/**/*.md`, `.vibey/**/*.yaml` |
| CORE-LIB | Core Python library | `vibey/**/*.py` |
| TESTS | Test files and fixtures | `tests/**/*` |
| CONFIG | Configuration files | `*.toml`, `*.cfg`, `*.json` |
| SCRIPTS | Utility scripts | `scripts/**/*` |
| ROADMAP-DATA | Roadmap YAML data | `.vibey/roadmap/**/*.yaml` |

### Subcategory Definitions for DOCUMENTATION

| Subcategory | Description | File Patterns |
|-------------|-------------|---------------|
| reference | API/CLI/MCP references | `docs/reference/*.md` |
| architecture | ADRs, design docs | `docs/architecture/**/*.md` |
| guides | User guides, tutorials | `docs/guides/*.md`, `docs/journeys/*.md`, `docs/walkthroughs/*.md` |
| operational | Logs, runbooks | `*_LOG.md`, `*_RUNBOOK.md` |
| reports | Audit reports, summaries | `*_REPORT.md`, `*_SUMMARY.md` |
| planning | Recommendations, requirements | `*_RECOMMENDATIONS.md`, `*_REQUIREMENTS.md` |

### Subcategory Definitions for FRAMEWORK

| Subcategory | Description | File Patterns |
|-------------|-------------|---------------|
| roadmap-context | Audit context, sprint/task plans | `.vibey/roadmap/context/**/*.md` |
| config | Framework configuration | `.vibey/config/**/*` |
| templates | Workflow templates | `.vibey/templates/**/*` |

## Implementation Steps

### Step 1: Load Task 7.1 Output

```bash
# Get list of new files from Task 7.1
NEW_FILES=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-7/outputs/AUDIT_CREATED_FILES.md"

# Extract file paths (documentation files only)
grep -E "^\|.*\.md.*\|" $NEW_FILES | awk -F'|' '{print $2}' | tr -d ' ' > /tmp/new_doc_files.txt
```

### Step 2: Load Current Classification File

```bash
# Locate classification file
CLASSIFICATION_FILE=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/DOCS_FILE_CLASSIFICATION.yaml"

# Backup before modification
cp $CLASSIFICATION_FILE ${CLASSIFICATION_FILE}.pre-sprint7

# Count current entries
grep "path:" $CLASSIFICATION_FILE | wc -l
```

### Step 3: Apply Classification Rules

For each new file from Task 7.1 output, apply classification rules:

```python
#!/usr/bin/env python3
"""Classify new documentation files."""

import re
from pathlib import Path

CLASSIFICATION_RULES = [
    # (pattern, category, subcategory)
    (r'^docs/reference/.*\.md$', 'DOCUMENTATION', 'reference'),
    (r'^docs/architecture/adr/.*\.md$', 'DOCUMENTATION', 'architecture'),
    (r'^docs/journeys/.*\.md$', 'DOCUMENTATION', 'guides'),
    (r'^docs/walkthroughs/.*\.md$', 'DOCUMENTATION', 'guides'),
    (r'^docs/guides/.*\.md$', 'DOCUMENTATION', 'guides'),
    (r'^\.vibey/roadmap/context/.*\.md$', 'FRAMEWORK', 'roadmap-context'),
    (r'.*_LOG\.md$', 'DOCUMENTATION', 'operational'),
    (r'.*_REPORT\.md$', 'DOCUMENTATION', 'reports'),
    (r'.*_SUMMARY\.md$', 'DOCUMENTATION', 'reports'),
    (r'.*_RECOMMENDATIONS\.md$', 'DOCUMENTATION', 'planning'),
    (r'.*_REQUIREMENTS\.md$', 'DOCUMENTATION', 'planning'),
    (r'.*_SCHEDULE\.md$', 'DOCUMENTATION', 'planning'),
    (r'.*_BASELINE\.md$', 'DOCUMENTATION', 'reports'),
    (r'.*_MATRIX\.md$', 'DOCUMENTATION', 'reports'),
]

def classify_file(filepath: str) -> tuple:
    """Return (category, subcategory) for a file path."""
    for pattern, category, subcategory in CLASSIFICATION_RULES:
        if re.match(pattern, filepath):
            return (category, subcategory)
    return ('UNCLASSIFIED', 'unknown')

def classify_new_files(new_files_list: list) -> list:
    """Classify a list of new files."""
    results = []
    for filepath in new_files_list:
        category, subcategory = classify_file(filepath)
        results.append({
            'path': filepath,
            'category': category,
            'subcategory': subcategory
        })
    return results
```

### Step 4: Update Classification YAML

Add new entries to DOCS_FILE_CLASSIFICATION.yaml:

```yaml
# New entries to add (Sprint 4-6 documentation)

# Sprint 4 Documentation
- path: docs/reference/CLI_REFERENCE.md
  category: DOCUMENTATION
  subcategory: reference
  source_sprint: sprint-4
  auto_generated: true

- path: docs/reference/MCP_REFERENCE.md
  category: DOCUMENTATION
  subcategory: reference
  source_sprint: sprint-4
  auto_generated: true

# Sprint 5 Documentation
- path: .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-5/outputs/REMEDIATION_LOG.md
  category: FRAMEWORK
  subcategory: roadmap-context
  source_sprint: sprint-5

- path: .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-5/outputs/INTEGRITY_AUDIT_REPORT.md
  category: FRAMEWORK
  subcategory: roadmap-context
  source_sprint: sprint-5

# Sprint 6 Documentation
- path: .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-6/outputs/FRICTION_LOG.md
  category: FRAMEWORK
  subcategory: roadmap-context
  source_sprint: sprint-6

- path: .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-6/outputs/AUTOMATION_RECOMMENDATIONS.md
  category: FRAMEWORK
  subcategory: roadmap-context
  source_sprint: sprint-6
```

### Step 5: Generate Classification Delta Report

```markdown
# Classification Delta Report

## Summary
- New files classified: X
- By category:
  - DOCUMENTATION: Y
  - FRAMEWORK: Z

## Classification Changes

### New DOCUMENTATION Entries

| File | Subcategory | Source Sprint |
|------|-------------|---------------|
| docs/reference/CLI_REFERENCE.md | reference | Sprint 4 |
| ... | ... | ... |

### New FRAMEWORK Entries

| File | Subcategory | Source Sprint |
|------|-------------|---------------|
| .vibey/roadmap/context/.../REMEDIATION_LOG.md | roadmap-context | Sprint 5 |
| ... | ... | ... |

## Category Counts

| Category | Sprint 5 Count | Sprint 7 Count | Delta |
|----------|----------------|----------------|-------|
| DOCUMENTATION | A | B | +C |
| FRAMEWORK | D | E | +F |
| Total | G | H | +I |
```

### Step 6: Validate Classifications

```bash
# Ensure no unclassified files remain
grep "UNCLASSIFIED" $CLASSIFICATION_FILE && echo "WARNING: Unclassified files found!"

# Ensure all files from inventory have classifications
INVENTORY_DOCS=$(grep "\.md$" FILE_INVENTORY.yaml | wc -l)
CLASSIFIED_DOCS=$(grep "path:.*\.md$" $CLASSIFICATION_FILE | wc -l)

if [ "$INVENTORY_DOCS" -eq "$CLASSIFIED_DOCS" ]; then
    echo "SUCCESS: All documentation files classified"
else
    echo "WARNING: Classification count mismatch"
fi
```

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| Updated DOCS_FILE_CLASSIFICATION.yaml | `.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/` | Classification with ~15 new entries |
| CLASSIFICATION_DELTA_REPORT.md | `.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-7/outputs/` | Delta report showing changes |
| DOCS_FILE_CLASSIFICATION.yaml.pre-sprint7 | `.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/` | Backup of pre-Sprint-7 classification |

## Acceptance Criteria

- [ ] All documentation files from Task 7.1 output classified
- [ ] Classifications follow established taxonomy
- [ ] No UNCLASSIFIED entries in final output
- [ ] Each entry includes: path, category, subcategory, source_sprint
- [ ] CLASSIFICATION_DELTA_REPORT.md generated with before/after counts
- [ ] Classification count matches documentation file count in inventory
- [ ] Backup of pre-Sprint-7 classification preserved

## Estimated Time

| Activity | Duration |
|----------|----------|
| Load Task 7.1 output | 5 minutes |
| Apply classification rules | 15 minutes |
| Update YAML file | 15 minutes |
| Generate delta report | 10 minutes |
| Validation | 10 minutes |
| **Total** | **~55 minutes** |

## Notes

- This task depends on Task 7.1 completing first
- Classification rules should be applied consistently with earlier sprints
- Any ambiguous files should default to the most specific category available
- The `source_sprint` field is new for Sprint 7 entries - helps track audit artifacts
- Output feeds directly into Task 7.3 (COVERAGE_MATRIX regeneration)
