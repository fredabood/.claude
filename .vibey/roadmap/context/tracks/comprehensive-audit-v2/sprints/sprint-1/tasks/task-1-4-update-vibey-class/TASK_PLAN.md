# Task 1.4: Update VIBEY_FILE_CLASSIFICATION.yaml with New Files - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJNKE2B2W5NJRTSRZWN4QSS |
| Sprint | Sprint 1: File Inventory Refresh |
| Type | documentation |
| Complexity | **medium** |
| Priority | high |
| Estimated Tokens | 3,500 |
| Dependencies | Task 1.1 (file scan), Task 1.3 (classification) |

## Objective

Update the core library classification file (VIBEY_FILE_CLASSIFICATION.yaml) to include all new Python files added to the vibey/ package since December 12, 2024. The original audit classified 365 files in vibey/.

## Source File

```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/VIBEY_FILE_CLASSIFICATION.yaml
```

## Expected Schema

```yaml
vibey_file_classification:
  metadata:
    generated: "2024-12-28T00:00:00Z"
    total_files: 400
    package_version: "2.5.0"
    last_updated: "2024-12-28"

  files:
    - path: vibey/cli/main.py
      module: vibey.cli.main
      subcategory: cli-entry
      description: "CLI entry point"
      exports:
        - main
        - cli
      imports:
        - click
        - vibey.cli.commands
      line_count: 87
      complexity: low

    - path: vibey/services/implementation/loop.py
      module: vibey.services.implementation.loop
      subcategory: services-implementation
      description: "Implementation mode loop controller"
      exports:
        - ImplementationLoop
        - LoopState
      imports:
        - vibey.roadmap.models
        - vibey.operations.roadmap
      line_count: 287
      complexity: high
      added_in_audit: comprehensive-audit-v2
```

## Vibey Package Subcategories

| Subcategory | Path Pattern | Description |
|-------------|--------------|-------------|
| `cli-entry` | vibey/cli/main.py | CLI entry point |
| `cli-commands` | vibey/cli/commands*.py | Command implementations |
| `cli-command-modules` | vibey/cli/command_modules/ | Modular commands |
| `cli-utilities` | vibey/cli/utils*.py | CLI utilities |
| `operations-roadmap` | vibey/operations/roadmap/ | Roadmap operations |
| `operations-docs` | vibey/operations/docs/ | Documentation operations |
| `operations-core` | vibey/operations/*.py | Core operations |
| `mcp-server` | vibey/mcp/server.py | MCP server |
| `mcp-tools` | vibey/mcp/tools/ | MCP tool definitions |
| `mcp-resources` | vibey/mcp/resources/ | MCP resources |
| `adapters` | vibey/adapters/ | Platform adapters |
| `roadmap-models` | vibey/roadmap/models/ | Data models |
| `roadmap-serialization` | vibey/roadmap/serialization/ | YAML/JSON serialization |
| `roadmap-criteria` | vibey/roadmap/criteria/ | Acceptance criteria |
| `common-errors` | vibey/common/errors/ | Error definitions |
| `common-utils` | vibey/common/utils*.py | Shared utilities |
| `services` | vibey/services/ | Service layer |
| `services-implementation` | vibey/services/implementation/ | Implementation mode |

## Implementation Steps

### Step 1: Analyze Current Classification

```bash
# Locate existing classification
CLASSIFICATION_PATH=".vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/VIBEY_FILE_CLASSIFICATION.yaml"

# Count existing entries
grep -c "^  - path:" "$CLASSIFICATION_PATH" || echo "Counting entries..."

# View structure
head -100 "$CLASSIFICATION_PATH"

# Extract classified paths
grep "path:" "$CLASSIFICATION_PATH" | sed 's/.*path: //' | sort > /tmp/already_classified_vibey.txt
echo "Already classified: $(wc -l < /tmp/already_classified_vibey.txt)"
```

### Step 2: Identify Current Python Files in vibey/

```bash
# Find all Python files currently in vibey/
find vibey -name "*.py" -type f | sort > /tmp/current_vibey_python.txt
echo "Current Python files in vibey/: $(wc -l < /tmp/current_vibey_python.txt)"

# Identify unclassified files
comm -23 /tmp/current_vibey_python.txt /tmp/already_classified_vibey.txt > /tmp/unclassified_vibey.txt
echo "Unclassified files: $(wc -l < /tmp/unclassified_vibey.txt)"
```

### Step 3: Cross-Reference with Task 1.1 Delta

```bash
DELTA_DIR=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs"

# Get vibey files from delta report
grep "^vibey/" "$DELTA_DIR/DELTA_REPORT_FILES_ADDED.txt" | grep "\.py$" > /tmp/vibey_files_added.txt
echo "Vibey Python files added since Dec 12: $(wc -l < /tmp/vibey_files_added.txt)"

# Verify overlap with unclassified
comm -12 /tmp/unclassified_vibey.txt /tmp/vibey_files_added.txt > /tmp/new_vibey_to_classify.txt
echo "New files to classify: $(wc -l < /tmp/new_vibey_to_classify.txt)"
```

### Step 4: Generate Classification Entries

```python
#!/usr/bin/env python3
"""Generate classification entries for new vibey Python files."""

import ast
import os
from pathlib import Path
from datetime import datetime

def analyze_python_file(filepath: str) -> dict:
    """Extract metadata from a Python file using AST."""

    path = Path(filepath)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        line_count = len(content.splitlines())

    # Parse AST
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return {
            'path': filepath,
            'error': 'syntax_error',
            'line_count': line_count
        }

    # Extract imports
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    # Extract exports (top-level classes and functions)
    exports = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            exports.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            if not node.name.startswith('_'):
                exports.append(node.name)

    # Determine subcategory
    subcategory = determine_vibey_subcategory(filepath)

    # Determine complexity
    complexity = determine_complexity(line_count, len(exports), len(imports))

    # Convert path to module
    module = filepath.replace('/', '.').replace('.py', '')

    # Get description from module docstring
    description = ""
    if tree.body and isinstance(tree.body[0], ast.Expr):
        if isinstance(tree.body[0].value, ast.Constant):
            description = tree.body[0].value.value
            if description and len(description) > 100:
                description = description[:100] + "..."

    return {
        'path': filepath,
        'module': module,
        'subcategory': subcategory,
        'description': description or f"Module: {path.stem}",
        'exports': exports[:10],  # Limit to 10 exports
        'imports': [i for i in imports if i.startswith('vibey')][:10],
        'line_count': line_count,
        'complexity': complexity,
        'added_in_audit': 'comprehensive-audit-v2'
    }


def determine_vibey_subcategory(filepath: str) -> str:
    """Determine subcategory for vibey package file."""

    if 'cli/command_modules' in filepath:
        return 'cli-command-modules'
    elif 'cli/main.py' in filepath:
        return 'cli-entry'
    elif 'cli/commands' in filepath:
        return 'cli-commands'
    elif 'cli/' in filepath:
        return 'cli-utilities'
    elif 'operations/roadmap' in filepath:
        return 'operations-roadmap'
    elif 'operations/docs' in filepath:
        return 'operations-docs'
    elif 'operations/' in filepath:
        return 'operations-core'
    elif 'mcp/tools' in filepath:
        return 'mcp-tools'
    elif 'mcp/resources' in filepath:
        return 'mcp-resources'
    elif 'mcp/server.py' in filepath:
        return 'mcp-server'
    elif 'mcp/' in filepath:
        return 'mcp-utilities'
    elif 'adapters/' in filepath:
        return 'adapters'
    elif 'roadmap/models' in filepath:
        return 'roadmap-models'
    elif 'roadmap/serialization' in filepath:
        return 'roadmap-serialization'
    elif 'roadmap/criteria' in filepath:
        return 'roadmap-criteria'
    elif 'roadmap/' in filepath:
        return 'roadmap-core'
    elif 'common/errors' in filepath:
        return 'common-errors'
    elif 'common/' in filepath:
        return 'common-utils'
    elif 'services/implementation' in filepath:
        return 'services-implementation'
    elif 'services/' in filepath:
        return 'services'
    else:
        return 'core-misc'


def determine_complexity(line_count: int, num_exports: int, num_imports: int) -> str:
    """Estimate file complexity."""
    score = 0
    score += 1 if line_count > 100 else 0
    score += 1 if line_count > 300 else 0
    score += 1 if num_exports > 5 else 0
    score += 1 if num_imports > 10 else 0

    if score >= 3:
        return 'high'
    elif score >= 1:
        return 'medium'
    else:
        return 'low'


# Process unclassified files
with open('/tmp/unclassified_vibey.txt') as f:
    files = [line.strip() for line in f if line.strip()]

entries = []
for filepath in files:
    if os.path.exists(filepath):
        entry = analyze_python_file(filepath)
        entries.append(entry)

# Output new entries
import yaml

output = {
    'new_vibey_classifications': {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'new_files_count': len(entries),
            'previous_count': 365,
            'updated_count': 365 + len(entries)
        },
        'files': entries
    }
}

output_path = '.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/VIBEY_NEW_CLASSIFICATIONS.yaml'
with open(output_path, 'w') as f:
    yaml.dump(output, f, default_flow_style=False, sort_keys=False)

print(f"Generated classifications for {len(entries)} new files")
print(f"Output: {output_path}")
```

### Step 5: Merge with Existing Classification

```python
#!/usr/bin/env python3
"""Merge new classifications into VIBEY_FILE_CLASSIFICATION.yaml."""

import yaml
from datetime import datetime

# Load existing classification
existing_path = ".vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/VIBEY_FILE_CLASSIFICATION.yaml"
with open(existing_path) as f:
    existing = yaml.safe_load(f)

# Load new entries
new_path = ".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/VIBEY_NEW_CLASSIFICATIONS.yaml"
with open(new_path) as f:
    new_data = yaml.safe_load(f)

# Merge entries
if 'files' not in existing:
    existing['files'] = []

existing_paths = {e.get('path') for e in existing['files']}

for entry in new_data['new_vibey_classifications']['files']:
    if entry['path'] not in existing_paths:
        existing['files'].append(entry)

# Update metadata
existing['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
existing['metadata']['total_files'] = len(existing['files'])
existing['metadata']['audit_version'] = 'comprehensive-audit-v2'

# Sort files by path
existing['files'] = sorted(existing['files'], key=lambda x: x.get('path', ''))

# Write updated classification
output_path = ".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/VIBEY_FILE_CLASSIFICATION_UPDATED.yaml"
with open(output_path, 'w') as f:
    yaml.dump(existing, f, default_flow_style=False, sort_keys=False)

print(f"Updated classification written to {output_path}")
print(f"Total files: {len(existing['files'])}")
```

### Step 6: Validate Updated Classification

```bash
OUTPUT_DIR=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs"

# Validate YAML
python -c "import yaml; yaml.safe_load(open('$OUTPUT_DIR/VIBEY_FILE_CLASSIFICATION_UPDATED.yaml'))"

# Count entries
ENTRY_COUNT=$(grep -c "^  - path:" "$OUTPUT_DIR/VIBEY_FILE_CLASSIFICATION_UPDATED.yaml")
echo "Total entries: $ENTRY_COUNT"

# Count actual Python files
ACTUAL_COUNT=$(find vibey -name "*.py" -type f | wc -l | tr -d ' ')
echo "Actual Python files: $ACTUAL_COUNT"

# Check for discrepancies
if [ "$ENTRY_COUNT" -ne "$ACTUAL_COUNT" ]; then
    echo "WARNING: Entry count ($ENTRY_COUNT) differs from actual file count ($ACTUAL_COUNT)"
fi

# Subcategory distribution
echo "=== Subcategory Distribution ==="
grep "subcategory:" "$OUTPUT_DIR/VIBEY_FILE_CLASSIFICATION_UPDATED.yaml" | sort | uniq -c | sort -rn

# Check for files with errors
grep -A3 "error:" "$OUTPUT_DIR/VIBEY_FILE_CLASSIFICATION_UPDATED.yaml" || echo "No errors found"
```

### Step 7: Generate Update Report

```bash
OUTPUT_DIR=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs"

cat > "$OUTPUT_DIR/VIBEY_CLASSIFICATION_UPDATE_REPORT.md" << 'EOF'
# VIBEY_FILE_CLASSIFICATION.yaml Update Report

## Summary

| Metric | Value |
|--------|-------|
| Original file count | 365 |
| New files added | TBD |
| Updated total | TBD |
| Update date | 2024-12-28 |

## New Files by Subcategory

| Subcategory | Count | Examples |
|-------------|-------|----------|
| TBD | TBD | TBD |

## Notable Additions

### New Modules
- vibey/services/ - Service layer
- vibey/cli/command_modules/ - Modular CLI commands

### New Patterns
- Implementation mode services
- Command module pattern

## Validation Results

- [ ] YAML syntax valid
- [ ] All files have required fields
- [ ] Entry count matches actual file count
- [ ] No duplicate entries
- [ ] All exports correctly identified

## Files Requiring Manual Review

List any files with:
- Syntax errors
- Unusual structure
- Missing docstrings

EOF
```

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| `VIBEY_FILE_CLASSIFICATION_UPDATED.yaml` | sprint-1/outputs/ | Updated full classification |
| `VIBEY_NEW_CLASSIFICATIONS.yaml` | sprint-1/outputs/ | New entries only |
| `VIBEY_CLASSIFICATION_UPDATE_REPORT.md` | sprint-1/outputs/ | Update summary and validation |

## Acceptance Criteria

- [ ] All Python files in vibey/ have classification entries
- [ ] Each entry includes: path, module, subcategory, description, exports, imports, line_count, complexity
- [ ] New entries marked with `added_in_audit: comprehensive-audit-v2`
- [ ] Subcategory assignments consistent with existing patterns
- [ ] Entry count matches actual file count in vibey/
- [ ] YAML validates without syntax errors
- [ ] No duplicate path entries
- [ ] Update report documents all changes

## Estimated Time

| Activity | Duration |
|----------|----------|
| Analyze existing classification | 10 minutes |
| Identify unclassified files | 10 minutes |
| Generate AST-based metadata | 25 minutes |
| Merge with existing | 15 minutes |
| Validate and verify | 15 minutes |
| Generate report | 10 minutes |
| **Total** | **85 minutes** |

## Edge Cases

1. **Syntax errors in Python files**: Mark with error flag, include line count only
2. **Empty __init__.py files**: Valid entries with minimal metadata
3. **Generated files**: Mark as auto-generated if detected
4. **Circular imports**: Will be detected but not cause classification failure
5. **Dynamic imports**: Cannot be captured via AST, note in metadata

## Notes

- This is the most code-heavy file inventory update
- AST parsing provides accurate import/export analysis
- Complexity ratings are estimates based on heuristics
- New subcategories (services, cli-command-modules) should be consistent with Task 1.3 taxonomy updates
