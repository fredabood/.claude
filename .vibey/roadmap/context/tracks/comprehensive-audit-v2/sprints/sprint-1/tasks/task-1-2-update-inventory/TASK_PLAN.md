# Task 1.2: Update FILE_INVENTORY.yaml with New Entries - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJKTRVZS618BM5ZZTQ34430 |
| Sprint | Sprint 1: File Inventory Refresh |
| Type | documentation |
| Complexity | **medium** |
| Priority | high |
| Estimated Tokens | 3,000 |
| Dependencies | Task 1.1 (file scan) |

## Objective

Update the master FILE_INVENTORY.yaml to include all new files identified in Task 1.1. Preserve existing entries, add new ones following the established schema, and properly handle deleted files.

## Source File

```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/FILE_INVENTORY.yaml
```

## Expected Schema

Based on the original inventory structure:

```yaml
file_inventory:
  metadata:
    generated: "2024-12-28T00:00:00Z"
    total_files: 800
    coverage_percentage: 99.5
    last_updated: "2024-12-28"

  files:
    - path: vibey/cli/main.py
      size_bytes: 2345
      line_count: 87
      last_modified: "2024-12-15"
      category: CORE-LIB
      subcategory: cli-entry
      status: active

    - path: vibey/services/new_module.py
      size_bytes: 5678
      line_count: 234
      last_modified: "2024-12-25"
      category: CORE-LIB
      subcategory: services
      status: active
      added_in_audit: comprehensive-audit-v2
```

## Implementation Steps

### Step 1: Read and Analyze Existing Inventory

```bash
# Locate the existing inventory
INVENTORY_PATH=".vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/FILE_INVENTORY.yaml"

# Count existing entries
grep -c "^  - path:" "$INVENTORY_PATH" || echo "File not found or no entries"

# View structure (first 50 lines)
head -50 "$INVENTORY_PATH"

# Extract existing paths for comparison
grep "path:" "$INVENTORY_PATH" | sed 's/.*path: //' | sort > /tmp/existing_inventory_paths.txt
```

### Step 2: Load New Files from Task 1.1

```bash
# Get the list of added files from Task 1.1 output
DELTA_DIR=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs"

# Load added files
cat "$DELTA_DIR/DELTA_REPORT_FILES_ADDED.txt" | sort > /tmp/files_to_add.txt

# Identify files not yet in inventory
comm -23 /tmp/files_to_add.txt /tmp/existing_inventory_paths.txt > /tmp/new_files_for_inventory.txt

echo "New files to add to inventory: $(wc -l < /tmp/new_files_for_inventory.txt)"
```

### Step 3: Generate Metadata for Each New File

```python
#!/usr/bin/env python3
"""Generate inventory entries for new files."""

import os
import yaml
from datetime import datetime
from pathlib import Path

def get_file_metadata(filepath: str) -> dict:
    """Extract metadata for a single file."""
    path = Path(filepath)

    if not path.exists():
        return None

    stat = path.stat()

    # Get line count for text files
    line_count = 0
    if path.suffix in ['.py', '.md', '.yaml', '.yml', '.txt', '.rst', '.json']:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = sum(1 for _ in f)
        except Exception:
            line_count = 0

    # Determine category placeholder (will be refined in Task 1.3)
    category = determine_primary_category(filepath)
    subcategory = determine_subcategory(filepath)

    return {
        'path': filepath,
        'size_bytes': stat.st_size,
        'line_count': line_count,
        'last_modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d'),
        'category': category,
        'subcategory': subcategory,
        'status': 'active',
        'added_in_audit': 'comprehensive-audit-v2'
    }

def determine_primary_category(filepath: str) -> str:
    """Determine primary category from path."""
    if filepath.startswith('vibey/'):
        return 'CORE-LIB'
    elif filepath.startswith('docs/') or filepath.endswith('.md'):
        return 'DOCUMENTATION'
    elif filepath.startswith('tests/'):
        return 'TESTS'
    elif filepath.startswith('scripts/'):
        return 'SCRIPTS'
    elif filepath.startswith('.vibey/roadmap/'):
        return 'ROADMAP-DATA'
    elif filepath.startswith('.vibey/'):
        return 'FRAMEWORK'
    else:
        return 'CONFIG'

def determine_subcategory(filepath: str) -> str:
    """Determine subcategory from path."""
    parts = filepath.split('/')

    if filepath.startswith('vibey/cli/'):
        if 'command_modules' in filepath:
            return 'cli-command-modules'
        return 'cli'
    elif filepath.startswith('vibey/operations/'):
        return 'operations'
    elif filepath.startswith('vibey/services/'):
        return 'services'
    elif filepath.startswith('vibey/mcp/'):
        return 'mcp'
    elif filepath.startswith('vibey/adapters/'):
        return 'adapters'
    elif filepath.startswith('vibey/roadmap/'):
        return 'roadmap'
    elif filepath.startswith('vibey/common/'):
        return 'common'
    elif filepath.startswith('tests/unit/'):
        return 'unit-tests'
    elif filepath.startswith('tests/integration/'):
        return 'integration-tests'
    elif filepath.startswith('docs/guides/'):
        return 'guides'
    elif filepath.startswith('docs/reference/'):
        return 'reference'
    elif filepath.startswith('docs/architecture/'):
        return 'architecture'

    return 'uncategorized'

# Process all new files
with open('/tmp/new_files_for_inventory.txt') as f:
    new_files = [line.strip() for line in f if line.strip()]

new_entries = []
for filepath in new_files:
    metadata = get_file_metadata(filepath)
    if metadata:
        new_entries.append(metadata)

# Output new entries
with open('/tmp/new_inventory_entries.yaml', 'w') as f:
    yaml.dump({'new_entries': new_entries}, f, default_flow_style=False, sort_keys=False)

print(f"Generated {len(new_entries)} new inventory entries")
```

### Step 4: Handle Deleted Files

```bash
# Get deleted files from Task 1.1
DELTA_DIR=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs"

# Load deleted file list
cat "$DELTA_DIR/DELTA_REPORT_FILES_DELETED.txt" > /tmp/files_deleted.txt

echo "Files to mark as deleted: $(wc -l < /tmp/files_deleted.txt)"
```

Options for handling deleted files:
1. **Mark as deleted**: Add `status: deleted` to existing entries
2. **Remove entries**: Delete from inventory entirely
3. **Archive**: Move to a separate `deleted_files` section

Recommended approach: Mark as deleted with deletion date:

```yaml
- path: vibey/old_module.py
  # ... existing metadata ...
  status: deleted
  deleted_date: "2024-12-20"
  deleted_in_audit: comprehensive-audit-v2
```

### Step 5: Merge Updates into Inventory

```python
#!/usr/bin/env python3
"""Merge new entries into FILE_INVENTORY.yaml."""

import yaml
from pathlib import Path

# Load existing inventory
inventory_path = ".vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/FILE_INVENTORY.yaml"

with open(inventory_path) as f:
    inventory = yaml.safe_load(f)

# Load new entries
with open('/tmp/new_inventory_entries.yaml') as f:
    new_data = yaml.safe_load(f)

# Load deleted files
with open('/tmp/files_deleted.txt') as f:
    deleted_files = set(line.strip() for line in f if line.strip())

# Mark deleted files
for entry in inventory.get('files', []):
    if entry.get('path') in deleted_files:
        entry['status'] = 'deleted'
        entry['deleted_date'] = '2024-12-28'
        entry['deleted_in_audit'] = 'comprehensive-audit-v2'

# Add new entries
inventory['files'].extend(new_data.get('new_entries', []))

# Update metadata
inventory['metadata']['last_updated'] = '2024-12-28'
inventory['metadata']['total_files'] = len([f for f in inventory['files'] if f.get('status') != 'deleted'])

# Write updated inventory
output_path = ".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/FILE_INVENTORY_UPDATED.yaml"
with open(output_path, 'w') as f:
    yaml.dump(inventory, f, default_flow_style=False, sort_keys=False)

print(f"Updated inventory written to {output_path}")
print(f"Total entries: {len(inventory['files'])}")
print(f"Active files: {inventory['metadata']['total_files']}")
```

### Step 6: Validate Updated Inventory

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/FILE_INVENTORY_UPDATED.yaml'))"

# Count entries
grep -c "^  - path:" FILE_INVENTORY_UPDATED.yaml

# Compare with actual file count
find . -type f -not -path "./.git/*" -not -path "./.venv/*" | wc -l

# Check for duplicates
grep "path:" FILE_INVENTORY_UPDATED.yaml | sed 's/.*path: //' | sort | uniq -d
```

### Step 7: Generate Changelog

```bash
OUTPUT_DIR=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs"

cat > "$OUTPUT_DIR/FILE_INVENTORY_CHANGELOG.md" << 'EOF'
# FILE_INVENTORY.yaml Changelog

## Update: Comprehensive Audit V2 - Sprint 1

**Date:** 2024-12-28
**Audit Period:** Dec 12, 2024 - Dec 28, 2024

### Summary

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total Entries | 720 | TBD | +X |
| Active Files | 720 | TBD | +X |
| Deleted Files | 0 | TBD | +X |

### Files Added

See: `DELTA_REPORT_FILES_ADDED.txt`

### Files Marked Deleted

See: `DELTA_REPORT_FILES_DELETED.txt`

### Schema Changes

- Added `added_in_audit` field for new entries
- Added `deleted_date` and `deleted_in_audit` for deleted entries
- Added `status` field (active/deleted)

### Validation

- [ ] YAML syntax validated
- [ ] No duplicate paths
- [ ] All new files have required fields
- [ ] Deleted files properly marked

EOF
```

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| `FILE_INVENTORY_UPDATED.yaml` | sprint-1/outputs/ | Updated master inventory |
| `FILE_INVENTORY_CHANGELOG.md` | sprint-1/outputs/ | Documentation of changes |
| `new_inventory_entries.yaml` | sprint-1/outputs/ | New entries only (for reference) |

## Acceptance Criteria

- [ ] All new files from Task 1.1 added to inventory
- [ ] Each new entry includes: path, size_bytes, line_count, last_modified, category, subcategory
- [ ] Category placeholders assigned (refined in Task 1.3)
- [ ] Deleted files marked with status: deleted
- [ ] Existing entries preserved unchanged
- [ ] Entry count matches: original + added - deleted = actual files (within tolerance)
- [ ] YAML validates without syntax errors
- [ ] No duplicate path entries
- [ ] Changelog documents all changes made

## Estimated Time

| Activity | Duration |
|----------|----------|
| Read and analyze existing inventory | 10 minutes |
| Process new files from Task 1.1 | 15 minutes |
| Generate metadata for new files | 20 minutes |
| Handle deleted files | 10 minutes |
| Merge and validate | 15 minutes |
| Generate changelog | 10 minutes |
| **Total** | **80 minutes** |

## Edge Cases

1. **Missing files**: Some files in delta may have been added then deleted
2. **Binary files**: Cannot determine line count; set to 0
3. **Symlinks**: May point to files outside repository
4. **Empty files**: Valid entries with line_count: 0 and size_bytes: 0
5. **Unicode filenames**: Ensure proper encoding in YAML output

## Notes

- The category assignments in this task are preliminary
- Task 1.3 will refine classifications using the full taxonomy
- Preserve the original inventory file; create updated version in outputs/
- Consider creating a backup before any modifications
