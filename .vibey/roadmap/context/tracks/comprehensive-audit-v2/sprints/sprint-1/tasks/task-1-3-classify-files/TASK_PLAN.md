# Task 1.3: Classify New Files by Category and Subcategory - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJKTRVZS618BM5ZZTQ34431 |
| Sprint | Sprint 1: File Inventory Refresh |
| Type | research |
| Complexity | **medium** |
| Priority | medium |
| Estimated Tokens | 2,500 |
| Dependencies | Task 1.1 (file scan), Task 1.2 (inventory update) |

## Objective

Apply the established 7-category taxonomy from the User Journey Audit to all new files identified in Task 1.1. Ensure classifications are consistent with existing patterns and identify any new subcategories needed for file types not covered by the original taxonomy.

## Taxonomy Reference

```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/CLASSIFICATION_TAXONOMY.md
```

## Primary Categories (7 Total)

| Category | Description | Typical Paths |
|----------|-------------|---------------|
| CORE-LIB | Core Python library code | vibey/ |
| DOCUMENTATION | Documentation files | docs/, *.md |
| TESTS | Test suite | tests/ |
| SCRIPTS | Utility scripts | scripts/ |
| CONFIG | Configuration files | *.yaml, *.toml, *.json (root) |
| FRAMEWORK | Framework-specific | .vibey/config/, adapters/ |
| ROADMAP-DATA | Roadmap data files | .vibey/roadmap/ |

## Subcategory Reference (40+ Subcategories)

### CORE-LIB Subcategories
- `cli` - CLI entry points and command definitions
- `cli-command-modules` - Modular CLI command implementations
- `operations` - Core business logic operations
- `operations-roadmap` - Roadmap-specific operations
- `operations-docs` - Documentation operations
- `mcp` - Model Context Protocol implementation
- `mcp-tools` - MCP tool definitions
- `mcp-resources` - MCP resource definitions
- `adapters` - Platform adapters
- `roadmap` - Roadmap models and serialization
- `roadmap-models` - Data models
- `roadmap-criteria` - Acceptance criteria handling
- `common` - Shared utilities
- `common-errors` - Error definitions
- `services` - Service layer (NEW - may need to add)
- `services-implementation` - Implementation mode services (NEW)

### DOCUMENTATION Subcategories
- `guides` - User guides
- `reference` - Reference documentation
- `architecture` - Architecture docs and ADRs
- `walkthroughs` - Step-by-step tutorials
- `journeys` - User journey documentation
- `development` - Developer documentation

### TESTS Subcategories
- `unit-tests` - Unit tests
- `integration-tests` - Integration tests
- `fixtures` - Test fixtures
- `conftest` - pytest configuration

### SCRIPTS Subcategories
- `audit` - Audit scripts
- `deployment` - Deployment scripts
- `utilities` - Utility scripts

### CONFIG Subcategories
- `python-config` - Python packaging (pyproject.toml, setup.py)
- `git-config` - Git configuration
- `ci-config` - CI/CD configuration
- `editor-config` - Editor settings

### FRAMEWORK Subcategories
- `framework-config` - Vibey framework configuration
- `adapter-configs` - Platform adapter configurations

### ROADMAP-DATA Subcategories
- `tracks` - Track YAML files
- `sprints` - Sprint YAML files
- `tasks` - Task YAML files
- `context` - Context documentation

## Implementation Steps

### Step 1: Load Taxonomy Reference

```bash
# Read existing taxonomy
TAXONOMY_PATH=".vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/CLASSIFICATION_TAXONOMY.md"

# View current subcategories
cat "$TAXONOMY_PATH"

# Extract subcategory list for reference
grep -E "^- \`" "$TAXONOMY_PATH" | sed 's/- `//' | sed 's/`.*//' > /tmp/existing_subcategories.txt
```

### Step 2: Load New Files from Task 1.1

```bash
DELTA_DIR=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs"

# Get all new files
cat "$DELTA_DIR/DELTA_REPORT_FILES_ADDED.txt" > /tmp/files_to_classify.txt

echo "Files to classify: $(wc -l < /tmp/files_to_classify.txt)"
```

### Step 3: Apply Classification Rules

```python
#!/usr/bin/env python3
"""Classify new files using established taxonomy."""

import re
from pathlib import Path
from typing import Tuple, Optional

def classify_file(filepath: str) -> Tuple[str, str, Optional[str]]:
    """
    Classify a file into primary category and subcategory.

    Returns: (primary_category, subcategory, secondary_category)
    """
    path = Path(filepath)
    parts = filepath.split('/')

    # CORE-LIB: vibey/ package
    if filepath.startswith('vibey/'):
        category = 'CORE-LIB'

        if 'cli/command_modules' in filepath:
            subcategory = 'cli-command-modules'
        elif 'cli/' in filepath:
            subcategory = 'cli'
        elif 'operations/roadmap' in filepath:
            subcategory = 'operations-roadmap'
        elif 'operations/docs' in filepath:
            subcategory = 'operations-docs'
        elif 'operations/' in filepath:
            subcategory = 'operations'
        elif 'mcp/tools' in filepath:
            subcategory = 'mcp-tools'
        elif 'mcp/resources' in filepath:
            subcategory = 'mcp-resources'
        elif 'mcp/' in filepath:
            subcategory = 'mcp'
        elif 'adapters/' in filepath:
            subcategory = 'adapters'
        elif 'roadmap/models' in filepath:
            subcategory = 'roadmap-models'
        elif 'roadmap/criteria' in filepath:
            subcategory = 'roadmap-criteria'
        elif 'roadmap/' in filepath:
            subcategory = 'roadmap'
        elif 'common/errors' in filepath:
            subcategory = 'common-errors'
        elif 'common/' in filepath:
            subcategory = 'common'
        elif 'services/implementation' in filepath:
            subcategory = 'services-implementation'
        elif 'services/' in filepath:
            subcategory = 'services'
        else:
            subcategory = 'core-misc'

        return category, subcategory, None

    # DOCUMENTATION: docs/ or *.md files
    if filepath.startswith('docs/') or filepath.endswith('.md'):
        category = 'DOCUMENTATION'

        if filepath.startswith('docs/guides/'):
            subcategory = 'guides'
        elif filepath.startswith('docs/reference/'):
            subcategory = 'reference'
        elif filepath.startswith('docs/architecture/'):
            subcategory = 'architecture'
        elif filepath.startswith('docs/walkthroughs/'):
            subcategory = 'walkthroughs'
        elif filepath.startswith('docs/journeys/'):
            subcategory = 'journeys'
        elif filepath.startswith('docs/development/'):
            subcategory = 'development'
        elif filepath.endswith('.md') and '/' not in filepath:
            subcategory = 'root-docs'
        else:
            subcategory = 'docs-misc'

        return category, subcategory, None

    # TESTS: tests/ directory
    if filepath.startswith('tests/'):
        category = 'TESTS'

        if '/unit/' in filepath:
            subcategory = 'unit-tests'
        elif '/integration/' in filepath:
            subcategory = 'integration-tests'
        elif 'conftest.py' in filepath:
            subcategory = 'conftest'
        elif '/fixtures/' in filepath:
            subcategory = 'fixtures'
        else:
            subcategory = 'tests-misc'

        return category, subcategory, None

    # SCRIPTS: scripts/ directory
    if filepath.startswith('scripts/'):
        category = 'SCRIPTS'

        if '/audit/' in filepath:
            subcategory = 'audit'
        elif '/deploy' in filepath:
            subcategory = 'deployment'
        else:
            subcategory = 'utilities'

        return category, subcategory, None

    # ROADMAP-DATA: .vibey/roadmap/
    if filepath.startswith('.vibey/roadmap/'):
        category = 'ROADMAP-DATA'

        if '/tracks/' in filepath:
            subcategory = 'tracks'
        elif '/sprints/' in filepath:
            subcategory = 'sprints'
        elif '/tasks/' in filepath:
            subcategory = 'tasks'
        elif '/context/' in filepath:
            subcategory = 'context'
        else:
            subcategory = 'roadmap-misc'

        return category, subcategory, None

    # FRAMEWORK: .vibey/ (non-roadmap)
    if filepath.startswith('.vibey/'):
        category = 'FRAMEWORK'

        if '/config/' in filepath:
            subcategory = 'framework-config'
        else:
            subcategory = 'framework-misc'

        return category, subcategory, None

    # CONFIG: Root configuration files
    if path.suffix in ['.yaml', '.yml', '.toml', '.json', '.ini', '.cfg']:
        category = 'CONFIG'

        if path.name in ['pyproject.toml', 'setup.py', 'setup.cfg']:
            subcategory = 'python-config'
        elif path.name in ['.gitignore', '.gitattributes']:
            subcategory = 'git-config'
        elif path.name in ['.pre-commit-config.yaml', '.github']:
            subcategory = 'ci-config'
        else:
            subcategory = 'config-misc'

        return category, subcategory, None

    # Fallback
    return 'UNCATEGORIZED', 'uncategorized', None


# Process all new files
with open('/tmp/files_to_classify.txt') as f:
    files = [line.strip() for line in f if line.strip()]

classifications = []
new_subcategories = set()
existing_subcategories = set()

# Load existing subcategories
with open('/tmp/existing_subcategories.txt') as f:
    existing_subcategories = set(line.strip() for line in f if line.strip())

for filepath in files:
    category, subcategory, secondary = classify_file(filepath)

    # Track potentially new subcategories
    if subcategory not in existing_subcategories:
        new_subcategories.add(subcategory)

    classifications.append({
        'path': filepath,
        'primary_category': category,
        'subcategory': subcategory,
        'secondary_category': secondary
    })

# Output classifications
import yaml

output = {
    'metadata': {
        'total_files_classified': len(classifications),
        'classification_date': '2024-12-28',
        'taxonomy_version': 'v2'
    },
    'new_subcategories': sorted(list(new_subcategories)),
    'classifications': classifications
}

with open('.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/NEW_FILE_CLASSIFICATIONS.yaml', 'w') as f:
    yaml.dump(output, f, default_flow_style=False, sort_keys=False)

print(f"Classified {len(classifications)} files")
print(f"New subcategories identified: {new_subcategories}")
```

### Step 4: Review and Validate Classifications

```bash
OUTPUT_DIR=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs"

# Validate YAML
python -c "import yaml; yaml.safe_load(open('$OUTPUT_DIR/NEW_FILE_CLASSIFICATIONS.yaml'))"

# Count by category
echo "=== Classification Summary ==="
grep "primary_category:" "$OUTPUT_DIR/NEW_FILE_CLASSIFICATIONS.yaml" | sort | uniq -c | sort -rn

# Count by subcategory
echo "=== Subcategory Summary ==="
grep "subcategory:" "$OUTPUT_DIR/NEW_FILE_CLASSIFICATIONS.yaml" | sort | uniq -c | sort -rn

# Check for uncategorized files
grep -A2 "UNCATEGORIZED" "$OUTPUT_DIR/NEW_FILE_CLASSIFICATIONS.yaml"
```

### Step 5: Document New Subcategories

If new subcategories are identified, document them:

```markdown
# TAXONOMY_UPDATES.md

## New Subcategories Proposed

### CORE-LIB

| Subcategory | Description | Example Files |
|-------------|-------------|---------------|
| services | Service layer implementations | vibey/services/*.py |
| services-implementation | Implementation mode services | vibey/services/implementation/*.py |
| cli-command-modules | Modular CLI commands | vibey/cli/command_modules/*.py |

### Rationale

These subcategories are needed because:

1. **services**: New service layer added for implementation mode
2. **services-implementation**: Specific implementation loop services
3. **cli-command-modules**: CLI refactored from monolithic commands.py

### Backward Compatibility

- Existing subcategories unchanged
- New subcategories follow naming convention
- No reclassification of existing files required
```

### Step 6: Cross-Reference with Existing Classifications

```bash
# Compare classification patterns with original files
ORIGINAL_CLASSIFICATIONS=".vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2"

# Check for consistency
echo "Original CORE-LIB subcategories:"
grep "subcategory:" "$ORIGINAL_CLASSIFICATIONS/VIBEY_FILE_CLASSIFICATION.yaml" | sort | uniq -c

echo "New CORE-LIB subcategories:"
grep "subcategory:" NEW_FILE_CLASSIFICATIONS.yaml | grep -A1 "CORE-LIB" | grep "subcategory" | sort | uniq -c
```

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| `NEW_FILE_CLASSIFICATIONS.yaml` | sprint-1/outputs/ | Classifications for all new files |
| `TAXONOMY_UPDATES.md` | sprint-1/outputs/ | Proposed new subcategories (if any) |
| Classification summary | sprint-1/outputs/ | Statistics by category/subcategory |

## Expected Output Format

```yaml
# NEW_FILE_CLASSIFICATIONS.yaml
metadata:
  total_files_classified: 150
  classification_date: "2024-12-28"
  taxonomy_version: "v2"

new_subcategories:
  - services
  - services-implementation
  - cli-command-modules

classifications:
  - path: vibey/services/loop.py
    primary_category: CORE-LIB
    subcategory: services
    secondary_category: null

  - path: vibey/cli/command_modules/roadmap.py
    primary_category: CORE-LIB
    subcategory: cli-command-modules
    secondary_category: null

  - path: docs/guides/implementation-mode.md
    primary_category: DOCUMENTATION
    subcategory: guides
    secondary_category: null
```

## Acceptance Criteria

- [ ] All new files from Task 1.1 assigned a primary category
- [ ] All new files assigned a subcategory
- [ ] Classifications consistent with existing patterns from original audit
- [ ] New subcategories documented with rationale (if any)
- [ ] No files left as UNCATEGORIZED (or documented why)
- [ ] YAML output validates without errors
- [ ] Classification statistics generated
- [ ] Cross-referenced with original classifications for consistency

## Estimated Time

| Activity | Duration |
|----------|----------|
| Load and review taxonomy | 10 minutes |
| Implement classification rules | 20 minutes |
| Apply classifications to files | 15 minutes |
| Review and validate | 15 minutes |
| Document new subcategories | 15 minutes |
| Cross-reference and finalize | 10 minutes |
| **Total** | **85 minutes** |

## Edge Cases

1. **Files in unexpected locations**: May require new subcategory or manual review
2. **Multi-purpose files**: May need secondary category
3. **Generated files**: May need special handling (e.g., __pycache__)
4. **Symlinks**: Classify based on target, not link
5. **Files matching multiple categories**: Use primary category based on path priority

## Notes

- This task refines the preliminary categories assigned in Task 1.2
- New subcategories should be conservative - only add if clearly needed
- Consistency with original audit is important for continuity
- Results feed into Task 1.9 (taxonomy verification)
