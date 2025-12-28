# Task 1.6: Update FILE_REGISTRY.yaml with Dependencies - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJKTRVZS618BM5ZZTQ34432 |
| Sprint | Sprint 1: File Inventory Refresh |
| Type | documentation |
| Complexity | **medium** |
| Priority | medium |
| Estimated Tokens | 3,000 |
| Dependencies | Task 1.1 (file scan), Task 1.3 (classification), Task 1.4 (vibey classification) |

## Objective

Update the FILE_REGISTRY.yaml with comprehensive metadata for all new and modified files since December 12, 2024. This includes file purpose, key functions/classes, exports, dependencies, and cross-references with existing entries.

## Source File

```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/FILE_REGISTRY.yaml
```

## Expected Schema

```yaml
file_registry:
  metadata:
    generated: "2024-12-28T00:00:00Z"
    total_entries: 800
    version: "2.0"
    last_updated: "2024-12-28"

  entries:
    # Python file entry
    - path: vibey/services/implementation/loop.py
      type: python
      purpose: "Manages the implementation mode execution loop"
      size_bytes: 12345
      line_count: 287
      created: "2024-12-20"
      last_modified: "2024-12-28"
      category: CORE-LIB
      subcategory: services-implementation
      functions:
        - name: start_loop
          description: "Initiates the implementation loop"
          parameters: ["config", "context"]
          returns: "LoopResult"
        - name: pause_loop
          description: "Pauses execution"
      classes:
        - name: ImplementationLoop
          description: "Main loop controller class"
          methods: ["start", "pause", "resume", "stop"]
        - name: LoopState
          description: "State management for loop"
      imports:
        internal:
          - vibey.roadmap.models
          - vibey.operations.roadmap
        external:
          - asyncio
          - dataclasses
      exports:
        - ImplementationLoop
        - LoopState
        - start_loop
      dependencies:
        depends_on:
          - vibey/roadmap/models/task.py
          - vibey/operations/roadmap/crud.py
        depended_by: []
      added_in_audit: comprehensive-audit-v2

    # YAML file entry
    - path: .vibey/roadmap/tracks/01KC2D0JK9.yaml
      type: yaml
      purpose: "Track definition for user-journey-audit"
      size_bytes: 2345
      line_count: 87
      created: "2024-12-12"
      last_modified: "2024-12-28"
      category: ROADMAP-DATA
      subcategory: tracks
      top_level_keys:
        - track
        - metadata
        - sprints
      references:
        - .vibey/roadmap/sprints/01KC2D0JKV.yaml

    # Markdown file entry
    - path: docs/guides/implementation-mode.md
      type: markdown
      purpose: "User guide for implementation mode"
      size_bytes: 8765
      line_count: 234
      created: "2024-12-22"
      last_modified: "2024-12-27"
      category: DOCUMENTATION
      subcategory: guides
      headings:
        - level: 1
          text: "Implementation Mode Guide"
        - level: 2
          text: "Getting Started"
        - level: 2
          text: "Configuration"
      links_to:
        - docs/reference/CLI_REFERENCE.md
        - docs/guides/roadmap-basics.md
```

## Implementation Steps

### Step 1: Analyze Existing Registry Structure

```bash
# Locate existing registry
REGISTRY_PATH=".vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/FILE_REGISTRY.yaml"

# View structure
head -100 "$REGISTRY_PATH"

# Count existing entries
grep -c "^  - path:" "$REGISTRY_PATH" || echo "Counting..."

# Extract existing paths
grep "path:" "$REGISTRY_PATH" | sed 's/.*path: //' | sort > /tmp/existing_registry_paths.txt
echo "Existing registry entries: $(wc -l < /tmp/existing_registry_paths.txt)"
```

### Step 2: Identify Files Needing Registry Entries

```bash
DELTA_DIR=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs"

# New files from Task 1.1
cat "$DELTA_DIR/DELTA_REPORT_FILES_ADDED.txt" > /tmp/files_for_registry.txt

# Also include significantly modified files
cat "$DELTA_DIR/DELTA_REPORT_FILES_MODIFIED.txt" >> /tmp/files_for_registry.txt

# Remove duplicates
sort -u /tmp/files_for_registry.txt > /tmp/files_for_registry_unique.txt

# Exclude already registered files (for new entries only)
comm -23 /tmp/files_for_registry_unique.txt /tmp/existing_registry_paths.txt > /tmp/new_registry_files.txt

echo "Files needing new registry entries: $(wc -l < /tmp/new_registry_files.txt)"
```

### Step 3: Generate Registry Entries for Python Files

```python
#!/usr/bin/env python3
"""Generate detailed registry entries for Python files."""

import ast
import os
from pathlib import Path
from datetime import datetime
import subprocess

def get_file_dates(filepath: str) -> tuple:
    """Get creation and modification dates from git or filesystem."""
    try:
        # Get first commit date (creation)
        created = subprocess.check_output(
            ['git', 'log', '--follow', '--format=%aI', '--reverse', filepath],
            text=True, stderr=subprocess.DEVNULL
        ).strip().split('\n')[0][:10]
    except:
        created = datetime.fromtimestamp(Path(filepath).stat().st_ctime).strftime('%Y-%m-%d')

    try:
        # Get last commit date (modification)
        modified = subprocess.check_output(
            ['git', 'log', '-1', '--format=%aI', filepath],
            text=True, stderr=subprocess.DEVNULL
        ).strip()[:10]
    except:
        modified = datetime.fromtimestamp(Path(filepath).stat().st_mtime).strftime('%Y-%m-%d')

    return created, modified


def analyze_python_file_detailed(filepath: str) -> dict:
    """Extract detailed metadata from a Python file."""

    path = Path(filepath)
    stat = path.stat()

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        line_count = len(content.splitlines())

    # Parse AST
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return {
            'path': filepath,
            'type': 'python',
            'error': 'syntax_error',
            'size_bytes': stat.st_size,
            'line_count': line_count
        }

    # Get module docstring for purpose
    purpose = ast.get_docstring(tree) or f"Python module: {path.stem}"
    if len(purpose) > 150:
        purpose = purpose[:150] + "..."

    # Extract functions
    functions = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            func_doc = ast.get_docstring(node) or ""
            if len(func_doc) > 100:
                func_doc = func_doc[:100] + "..."
            functions.append({
                'name': node.name,
                'description': func_doc,
                'parameters': [arg.arg for arg in node.args.args if arg.arg != 'self'],
                'returns': get_return_annotation(node)
            })

    # Extract classes
    classes = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            class_doc = ast.get_docstring(node) or ""
            if len(class_doc) > 100:
                class_doc = class_doc[:100] + "..."
            methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef) and not n.name.startswith('_')]
            classes.append({
                'name': node.name,
                'description': class_doc,
                'methods': methods[:10]  # Limit to 10 methods
            })

    # Extract imports
    internal_imports = []
    external_imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith('vibey'):
                    internal_imports.append(alias.name)
                else:
                    external_imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                if node.module.startswith('vibey'):
                    internal_imports.append(node.module)
                else:
                    external_imports.append(node.module)

    # Determine exports (public names)
    exports = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            if not node.name.startswith('_'):
                exports.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            if not node.name.startswith('_'):
                exports.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith('_'):
                    if target.id.isupper():  # Constants
                        exports.append(target.id)

    created, modified = get_file_dates(filepath)

    return {
        'path': filepath,
        'type': 'python',
        'purpose': purpose,
        'size_bytes': stat.st_size,
        'line_count': line_count,
        'created': created,
        'last_modified': modified,
        'category': 'CORE-LIB' if filepath.startswith('vibey/') else 'TESTS' if filepath.startswith('tests/') else 'SCRIPTS',
        'subcategory': determine_subcategory(filepath),
        'functions': functions[:10],
        'classes': classes[:10],
        'imports': {
            'internal': list(set(internal_imports))[:15],
            'external': list(set(external_imports))[:15]
        },
        'exports': exports[:15],
        'dependencies': {
            'depends_on': [],  # Will be filled by dependency graph
            'depended_by': []
        },
        'added_in_audit': 'comprehensive-audit-v2'
    }


def get_return_annotation(node: ast.FunctionDef) -> str:
    """Get return type annotation if present."""
    if node.returns:
        if isinstance(node.returns, ast.Name):
            return node.returns.id
        elif isinstance(node.returns, ast.Constant):
            return str(node.returns.value)
    return ""


def determine_subcategory(filepath: str) -> str:
    """Determine subcategory from path."""
    # Reuse logic from Task 1.4
    if 'cli/command_modules' in filepath:
        return 'cli-command-modules'
    elif 'cli/' in filepath:
        return 'cli'
    elif 'operations/roadmap' in filepath:
        return 'operations-roadmap'
    elif 'operations/' in filepath:
        return 'operations'
    elif 'services/implementation' in filepath:
        return 'services-implementation'
    elif 'services/' in filepath:
        return 'services'
    elif 'mcp/' in filepath:
        return 'mcp'
    elif 'adapters/' in filepath:
        return 'adapters'
    elif 'roadmap/' in filepath:
        return 'roadmap'
    elif 'common/' in filepath:
        return 'common'
    elif 'tests/' in filepath:
        return 'tests'
    return 'misc'


# Process Python files
python_entries = []
with open('/tmp/new_registry_files.txt') as f:
    files = [line.strip() for line in f if line.strip()]

for filepath in files:
    if filepath.endswith('.py') and os.path.exists(filepath):
        entry = analyze_python_file_detailed(filepath)
        python_entries.append(entry)
        print(f"Processed: {filepath}")

print(f"\nGenerated {len(python_entries)} Python file entries")
```

### Step 4: Generate Registry Entries for YAML Files

```python
#!/usr/bin/env python3
"""Generate registry entries for YAML files."""

import yaml
import os
from pathlib import Path
from datetime import datetime

def analyze_yaml_file(filepath: str) -> dict:
    """Extract metadata from a YAML file."""

    path = Path(filepath)
    stat = path.stat()

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        line_count = len(content.splitlines())

    # Parse YAML
    try:
        data = yaml.safe_load(content)
        top_level_keys = list(data.keys()) if isinstance(data, dict) else []
    except:
        top_level_keys = []

    # Determine purpose from path
    if '.vibey/roadmap/tracks' in filepath:
        purpose = "Track definition file"
        subcategory = 'tracks'
    elif '.vibey/roadmap/sprints' in filepath:
        purpose = "Sprint definition file"
        subcategory = 'sprints'
    elif '.vibey/roadmap/tasks' in filepath:
        purpose = "Task definition file"
        subcategory = 'tasks'
    elif '.vibey/config' in filepath:
        purpose = "Framework configuration file"
        subcategory = 'framework-config'
    else:
        purpose = f"YAML configuration: {path.stem}"
        subcategory = 'config'

    return {
        'path': filepath,
        'type': 'yaml',
        'purpose': purpose,
        'size_bytes': stat.st_size,
        'line_count': line_count,
        'created': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d'),
        'last_modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d'),
        'category': 'ROADMAP-DATA' if '.vibey/roadmap' in filepath else 'CONFIG',
        'subcategory': subcategory,
        'top_level_keys': top_level_keys[:10],
        'references': [],
        'added_in_audit': 'comprehensive-audit-v2'
    }
```

### Step 5: Generate Registry Entries for Markdown Files

```python
#!/usr/bin/env python3
"""Generate registry entries for Markdown files."""

import re
import os
from pathlib import Path
from datetime import datetime

def analyze_markdown_file(filepath: str) -> dict:
    """Extract metadata from a Markdown file."""

    path = Path(filepath)
    stat = path.stat()

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        line_count = len(content.splitlines())

    # Extract headings
    headings = []
    for match in re.finditer(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE):
        level = len(match.group(1))
        text = match.group(2).strip()
        headings.append({'level': level, 'text': text[:50]})

    # Extract links to other docs
    links = []
    for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content):
        link_target = match.group(2)
        if link_target.startswith('docs/') or link_target.endswith('.md'):
            links.append(link_target)

    # Determine purpose from first heading
    purpose = headings[0]['text'] if headings else f"Documentation: {path.stem}"

    # Determine subcategory
    if 'docs/guides/' in filepath:
        subcategory = 'guides'
    elif 'docs/reference/' in filepath:
        subcategory = 'reference'
    elif 'docs/architecture/' in filepath:
        subcategory = 'architecture'
    elif 'docs/walkthroughs/' in filepath:
        subcategory = 'walkthroughs'
    elif 'docs/journeys/' in filepath:
        subcategory = 'journeys'
    elif 'docs/development/' in filepath:
        subcategory = 'development'
    else:
        subcategory = 'docs-misc'

    return {
        'path': filepath,
        'type': 'markdown',
        'purpose': purpose[:100],
        'size_bytes': stat.st_size,
        'line_count': line_count,
        'created': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d'),
        'last_modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d'),
        'category': 'DOCUMENTATION',
        'subcategory': subcategory,
        'headings': headings[:10],
        'links_to': list(set(links))[:10],
        'added_in_audit': 'comprehensive-audit-v2'
    }
```

### Step 6: Combine All Entries and Merge

```python
#!/usr/bin/env python3
"""Combine all entries and merge with existing registry."""

import yaml
from datetime import datetime

# Load existing registry
existing_path = ".vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/FILE_REGISTRY.yaml"
with open(existing_path) as f:
    existing = yaml.safe_load(f)

# Load new entries (from previous steps)
# Assume these are stored in temporary files

# Merge entries
if 'entries' not in existing:
    existing['entries'] = []

existing_paths = {e.get('path') for e in existing['entries']}

# Add Python entries
for entry in python_entries:
    if entry['path'] not in existing_paths:
        existing['entries'].append(entry)

# Add YAML entries
for entry in yaml_entries:
    if entry['path'] not in existing_paths:
        existing['entries'].append(entry)

# Add Markdown entries
for entry in markdown_entries:
    if entry['path'] not in existing_paths:
        existing['entries'].append(entry)

# Update metadata
existing['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
existing['metadata']['total_entries'] = len(existing['entries'])
existing['metadata']['audit_version'] = 'comprehensive-audit-v2'

# Sort entries by path
existing['entries'] = sorted(existing['entries'], key=lambda x: x.get('path', ''))

# Write updated registry
output_path = ".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/FILE_REGISTRY_UPDATED.yaml"
with open(output_path, 'w') as f:
    yaml.dump(existing, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f"Updated registry: {len(existing['entries'])} entries")
```

### Step 7: Cross-Reference Dependencies

```python
#!/usr/bin/env python3
"""Cross-reference dependencies between files."""

import yaml

# Load the updated registry
with open('FILE_REGISTRY_UPDATED.yaml') as f:
    registry = yaml.safe_load(f)

# Build dependency map
path_to_entry = {e['path']: e for e in registry['entries']}

for entry in registry['entries']:
    if entry.get('type') == 'python' and 'imports' in entry:
        internal_imports = entry['imports'].get('internal', [])

        for imp in internal_imports:
            # Convert import to potential file paths
            # vibey.cli.main -> vibey/cli/main.py
            potential_path = imp.replace('.', '/') + '.py'

            if potential_path in path_to_entry:
                # Add to depends_on
                if 'dependencies' not in entry:
                    entry['dependencies'] = {'depends_on': [], 'depended_by': []}
                if potential_path not in entry['dependencies']['depends_on']:
                    entry['dependencies']['depends_on'].append(potential_path)

                # Add to depended_by of the target
                target = path_to_entry[potential_path]
                if 'dependencies' not in target:
                    target['dependencies'] = {'depends_on': [], 'depended_by': []}
                if entry['path'] not in target['dependencies']['depended_by']:
                    target['dependencies']['depended_by'].append(entry['path'])

# Write with dependencies
with open('FILE_REGISTRY_UPDATED.yaml', 'w') as f:
    yaml.dump(registry, f, default_flow_style=False, sort_keys=False)
```

### Step 8: Validate and Generate Update Log

```bash
OUTPUT_DIR=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs"

# Validate YAML
python -c "import yaml; yaml.safe_load(open('$OUTPUT_DIR/FILE_REGISTRY_UPDATED.yaml'))"

# Generate update log
cat > "$OUTPUT_DIR/REGISTRY_UPDATE_LOG.md" << 'EOF'
# FILE_REGISTRY.yaml Update Log

## Update Summary

| Metric | Before | After |
|--------|--------|-------|
| Total entries | TBD | TBD |
| Python files | TBD | TBD |
| YAML files | TBD | TBD |
| Markdown files | TBD | TBD |
| Other files | TBD | TBD |

## New Entries Added

### By Category

| Category | Count |
|----------|-------|
| CORE-LIB | TBD |
| DOCUMENTATION | TBD |
| TESTS | TBD |
| ROADMAP-DATA | TBD |

### Notable New Files

1. **vibey/services/implementation/** - New service layer
2. **vibey/cli/command_modules/** - Modular CLI commands
3. **docs/guides/** - New user guides

## Dependencies Mapped

- Total dependency relationships: TBD
- Files with most dependents: TBD
- Orphaned files (no dependencies): TBD

## Validation Results

- [ ] YAML syntax valid
- [ ] All required fields present
- [ ] No duplicate entries
- [ ] Dependencies cross-referenced
- [ ] Dates in correct format

EOF
```

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| `FILE_REGISTRY_UPDATED.yaml` | sprint-1/outputs/ | Updated complete registry |
| `REGISTRY_UPDATE_LOG.md` | sprint-1/outputs/ | Documentation of changes |
| `registry_new_entries.yaml` | sprint-1/outputs/ | New entries only (reference) |

## Acceptance Criteria

- [ ] All new files from Task 1.1 have registry entries
- [ ] Python files include: functions, classes, imports, exports
- [ ] YAML files include: top_level_keys, references
- [ ] Markdown files include: headings, links_to
- [ ] All entries include: path, type, purpose, size_bytes, line_count, dates, category, subcategory
- [ ] Dependencies cross-referenced (depends_on, depended_by)
- [ ] Entries for modified files updated with new metadata
- [ ] YAML validates without errors
- [ ] No duplicate entries
- [ ] Update log documents all changes

## Estimated Time

| Activity | Duration |
|----------|----------|
| Analyze existing registry | 10 minutes |
| Identify files needing entries | 10 minutes |
| Generate Python file entries | 25 minutes |
| Generate YAML file entries | 15 minutes |
| Generate Markdown file entries | 15 minutes |
| Cross-reference dependencies | 20 minutes |
| Validate and generate log | 10 minutes |
| **Total** | **105 minutes** |

## Edge Cases

1. **Binary files**: Minimal metadata (path, size, type only)
2. **Syntax errors**: Mark with error flag, include available metadata
3. **Very large files**: May need to limit extracted data
4. **Circular dependencies**: Will be captured in both directions
5. **Dynamic imports**: Cannot be captured statically, note in metadata
6. **Renamed files**: Old entry should be marked deleted, new entry created

## Notes

- This task produces the most detailed file metadata
- Cross-referencing with Task 1.5 (dependency graph) provides complete picture
- Registry entries support both human reading and programmatic queries
- Consider memory usage when processing many large files
