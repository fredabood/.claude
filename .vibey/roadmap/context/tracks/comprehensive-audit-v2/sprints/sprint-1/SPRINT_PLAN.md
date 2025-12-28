# Sprint 1: File Inventory Refresh - Detailed Plan

## Sprint Overview

| Field | Value |
|-------|-------|
| Sprint ID | 01KDJKTRVZS618BM5ZZTQ3442V |
| Track | Comprehensive Repository Audit V2 |
| Status | not_started |
| Tasks | 9 |
| Estimated Tokens | ~20,000 |
| Dependencies | None (first sprint) |

## Goal

Update all User Journey Audit file classification outputs to reflect the current repository state. The original audit (Dec 12-19, 2024) classified 720+ files. Since then, significant development has occurred.

## Context

### Original Audit Outputs Location
```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/
├── phase-1-1/
│   ├── FILE_INVENTORY.yaml          # Master file list
│   ├── CLASSIFICATION_TAXONOMY.md   # 7 categories, 40+ subcategories
│   └── ...
├── phase-1-2/
│   ├── VIBEY_FILE_CLASSIFICATION.yaml    # 365 files in vibey/
│   ├── DOCS_FILE_CLASSIFICATION.yaml     # 187 documentation files
│   ├── TESTS_FILE_CLASSIFICATION.yaml    # 154 test files
│   └── SCRIPTS_FILE_CLASSIFICATION.yaml  # 54 scripts
├── phase-1-3/
│   ├── FILE_REGISTRY.yaml           # File metadata
│   └── FILE_DEPENDENCY_GRAPH.yaml   # Import relationships
└── ...
```

### Key Statistics at Original Audit
- Total files classified: 720
- Python files in vibey/: 365
- Documentation files: 187
- Test files: 154
- Script files: 54
- Coverage: 99.4%

---

## Task Details

### Task 1.1: Scan Repository for New Files Since Dec 12

**Task ID:** `01KDJKTRVZS618BM5ZZTQ3442Z`
**Type:** research | **Complexity:** simple | **Priority:** high

#### Description
Use git to identify all files added, modified, or removed since Dec 12, 2024. Generate comprehensive list categorized by change type.

#### Implementation Steps

1. **Get the commit hash for Dec 12, 2024**
   ```bash
   git log --since="2024-12-12" --until="2024-12-13" --format="%H" | tail -1
   # Or find the first commit of the User Journey Audit
   git log --all --oneline --grep="user-journey" | tail -1
   ```

2. **Generate file change lists**
   ```bash
   # Files added since Dec 12
   git diff --name-only --diff-filter=A <dec12-commit>..HEAD > /tmp/files_added.txt

   # Files modified since Dec 12
   git diff --name-only --diff-filter=M <dec12-commit>..HEAD > /tmp/files_modified.txt

   # Files deleted since Dec 12
   git diff --name-only --diff-filter=D <dec12-commit>..HEAD > /tmp/files_deleted.txt

   # Files renamed since Dec 12
   git diff --name-only --diff-filter=R <dec12-commit>..HEAD > /tmp/files_renamed.txt
   ```

3. **Categorize by file type**
   ```bash
   # Python files
   grep "\.py$" /tmp/files_added.txt > /tmp/python_added.txt

   # Documentation files
   grep -E "\.(md|rst|txt)$" /tmp/files_added.txt > /tmp/docs_added.txt

   # YAML files
   grep "\.yaml$" /tmp/files_added.txt > /tmp/yaml_added.txt
   ```

4. **Generate summary statistics**
   ```bash
   echo "=== File Change Summary Since Dec 12 ==="
   echo "Added: $(wc -l < /tmp/files_added.txt)"
   echo "Modified: $(wc -l < /tmp/files_modified.txt)"
   echo "Deleted: $(wc -l < /tmp/files_deleted.txt)"
   ```

#### Deliverables
- `DELTA_REPORT_FILES_ADDED.txt` - All files added since Dec 12
- `DELTA_REPORT_FILES_MODIFIED.txt` - All files modified since Dec 12
- `DELTA_REPORT_FILES_DELETED.txt` - All files deleted since Dec 12
- `DELTA_SUMMARY.md` - Summary statistics and categorization

#### Acceptance Criteria
- [ ] All file changes since Dec 12 captured
- [ ] Changes categorized by type (added/modified/deleted)
- [ ] Changes categorized by file type (Python/docs/YAML/etc)
- [ ] Summary statistics generated

---

### Task 1.2: Update FILE_INVENTORY.yaml with New Entries

**Task ID:** `01KDJKTRVZS618BM5ZZTQ34430`
**Type:** documentation | **Complexity:** medium | **Priority:** high

#### Description
Update the master file inventory with all new files identified in Task 1.1. Preserve existing entries and add new ones.

#### Source File
```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/FILE_INVENTORY.yaml
```

#### Implementation Steps

1. **Read existing FILE_INVENTORY.yaml**
   - Note the current structure and format
   - Count existing entries (should be ~720)

2. **For each new file from Task 1.1:**
   - Determine primary category (CORE-LIB, DOCUMENTATION, TESTS, etc.)
   - Determine subcategory based on path
   - Add entry with: path, category, subcategory, added_date

3. **For deleted files:**
   - Mark as `status: deleted` or remove from inventory
   - Document in deletion log

4. **Validate completeness**
   ```bash
   # Count all tracked files
   find . -type f -not -path "./.git/*" -not -path "./.venv/*" | wc -l

   # Compare with inventory count
   grep "path:" FILE_INVENTORY.yaml | wc -l
   ```

#### Deliverables
- Updated `FILE_INVENTORY.yaml` with new entries
- `FILE_INVENTORY_CHANGELOG.md` documenting changes made

#### Acceptance Criteria
- [ ] All new files from Task 1.1 added to inventory
- [ ] Deleted files handled appropriately
- [ ] Entry count matches actual file count (±5 for exclusions)
- [ ] YAML validates without errors

---

### Task 1.3: Classify New Files by Category/Subcategory

**Task ID:** `01KDJKTRVZS618BM5ZZTQ34431`
**Type:** research | **Complexity:** medium | **Priority:** medium

#### Description
Apply the established 7-category taxonomy to all new files. Ensure consistent classification with existing entries.

#### Taxonomy Reference
```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/CLASSIFICATION_TAXONOMY.md
```

**Primary Categories:**
1. CORE-LIB - vibey/ package code
2. DOCUMENTATION - docs/, *.md files
3. TESTS - tests/ directory
4. SCRIPTS - scripts/, utility scripts
5. CONFIG - Configuration files
6. FRAMEWORK - Framework-specific files
7. ROADMAP-DATA - .vibey/roadmap/ data files

#### Implementation Steps

1. **Review existing taxonomy** for subcategory definitions

2. **Classify each new file:**
   ```
   vibey/cli/command_modules/*.py → CORE-LIB/cli-commands
   vibey/services/implementation/*.py → CORE-LIB/services
   docs/guides/*.md → DOCUMENTATION/guides
   tests/integration/*.py → TESTS/integration
   ```

3. **Identify any new subcategories needed**
   - If a new file type doesn't fit existing subcategories
   - Document proposed new subcategory with rationale

4. **Create classification mapping file**

#### Deliverables
- `NEW_FILE_CLASSIFICATIONS.yaml` - Classifications for all new files
- `TAXONOMY_UPDATES.md` - Any new subcategories proposed

#### Acceptance Criteria
- [ ] All new files assigned primary category
- [ ] All new files assigned subcategory
- [ ] Classifications consistent with existing patterns
- [ ] New subcategories documented if needed

---

### Task 1.4: Update FILE_REGISTRY.yaml with Dependencies

**Task ID:** `01KDJKTRVZS618BM5ZZTQ34432`
**Type:** documentation | **Complexity:** medium | **Priority:** medium

#### Description
Update the file registry with metadata for new files including size, line count, imports, and last modified date.

#### Source File
```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/FILE_REGISTRY.yaml
```

#### Implementation Steps

1. **For each new Python file, extract:**
   ```python
   # File metadata
   - path: vibey/services/implementation/loop.py
     size_bytes: 12345
     line_count: 287
     created: 2024-12-20
     last_modified: 2024-12-28
     imports:
       - vibey.roadmap.models
       - vibey.operations.roadmap
     exported_symbols:
       - ImplementationLoop
       - LoopState
   ```

2. **Use AST parsing for accurate import detection**
   ```python
   import ast

   with open(filepath) as f:
       tree = ast.parse(f.read())

   imports = []
   for node in ast.walk(tree):
       if isinstance(node, ast.Import):
           imports.extend(alias.name for alias in node.names)
       elif isinstance(node, ast.ImportFrom):
           if node.module:
               imports.append(node.module)
   ```

3. **Generate metadata for non-Python files**
   - YAML: list of top-level keys
   - Markdown: heading structure
   - Config: key configuration values

#### Deliverables
- Updated `FILE_REGISTRY.yaml`
- `REGISTRY_UPDATE_LOG.md` - Files added/updated

#### Acceptance Criteria
- [ ] All new files have registry entries
- [ ] Python imports accurately captured
- [ ] Metadata complete (size, lines, dates)
- [ ] YAML validates without errors

---

### Task 1.5: Update FILE_DEPENDENCY_GRAPH.yaml

**Task ID:** `01KDJKTRVZS618BM5ZZTQ34433`
**Type:** documentation | **Complexity:** complex | **Priority:** medium

**See:** `sprints/sprint-1/tasks/task-1-5-dependency-graph/TASK_PLAN.md`

#### Description
Update the import/dependency graph showing relationships between files. This is the most complex task in Sprint 1.

#### Source File
```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/FILE_DEPENDENCY_GRAPH.yaml
```

#### Key Challenges
- Need to trace both direct and transitive dependencies
- Must handle circular import detection
- Should identify orphaned modules (no dependents)

#### Deliverables
- Updated `FILE_DEPENDENCY_GRAPH.yaml`
- `DEPENDENCY_ANALYSIS.md` - Circular deps, orphans, coupling metrics

#### Acceptance Criteria
- [ ] All new file dependencies mapped
- [ ] Circular dependencies identified
- [ ] Orphaned modules flagged
- [ ] Graph validates for consistency

---

### Task 1.6: Generate Delta Report

**Task ID:** `01KDJKTRVZS618BM5ZZTQ34434`
**Type:** documentation | **Complexity:** simple | **Priority:** medium

#### Description
Generate comprehensive report of all file changes since Dec 12, including classification changes.

#### Implementation Steps

1. **Compile statistics:**
   ```markdown
   ## File Change Summary: Dec 12 - Dec 28, 2024

   ### Additions
   - Total files added: X
   - Python files: Y
   - Documentation: Z
   - Tests: W

   ### Modifications
   - Total files modified: X
   - Significant changes (>50 lines): Y

   ### Deletions
   - Total files deleted: X
   - Reason categories: refactoring, cleanup, etc.
   ```

2. **Create before/after comparison**

3. **Highlight significant changes**
   - New modules added
   - Major refactoring (commands.py split)
   - New directories created

#### Deliverables
- `DELTA_REPORT_DEC12_DEC28.md` - Comprehensive change report
- `CHANGE_STATISTICS.yaml` - Machine-readable statistics

#### Acceptance Criteria
- [ ] All changes documented
- [ ] Statistics accurate and verified
- [ ] Significant changes highlighted
- [ ] Report follows standard format

---

### Task 1.7: Update VIBEY_FILE_CLASSIFICATION.yaml

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QSS`
**Type:** documentation | **Complexity:** medium | **Priority:** high

#### Description
Update the core library classification file to include all new Python files added since Dec 12. Original classified 365 files in vibey/.

#### Source File
```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/VIBEY_FILE_CLASSIFICATION.yaml
```

#### Implementation Steps

1. **Count current Python files in vibey/**
   ```bash
   find vibey -name "*.py" -type f | wc -l
   ```

2. **Identify files not in classification**
   ```bash
   # Extract paths from classification
   grep "path:" VIBEY_FILE_CLASSIFICATION.yaml | sed 's/.*path: //' > classified.txt

   # Compare with actual files
   find vibey -name "*.py" -type f | sort > actual.txt
   comm -23 actual.txt classified.txt > unclassified.txt
   ```

3. **Classify each unclassified file**
   - Determine subcategory from path
   - Add entry with metadata

4. **Apply taxonomy:**
   ```
   vibey/cli/command_modules/ → cli-command-modules
   vibey/services/ → services
   vibey/roadmap/criteria/ → roadmap-criteria
   ```

#### Deliverables
- Updated `VIBEY_FILE_CLASSIFICATION.yaml`
- Count increase documented (365 → X)

#### Acceptance Criteria
- [ ] All Python files in vibey/ classified
- [ ] New subcategories added if needed
- [ ] Count matches actual file count
- [ ] YAML validates without errors

---

### Task 1.8: Update DOCS and TESTS File Classification Files

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QST`
**Type:** documentation | **Complexity:** medium | **Priority:** medium

#### Description
Update DOCS_FILE_CLASSIFICATION.yaml (187 files) and TESTS_FILE_CLASSIFICATION.yaml (154 files) with new entries.

#### Source Files
```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/DOCS_FILE_CLASSIFICATION.yaml
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/TESTS_FILE_CLASSIFICATION.yaml
```

#### Implementation Steps

1. **For DOCS classification:**
   ```bash
   # Find all documentation files
   find docs -name "*.md" -type f | wc -l
   find . -name "*.md" -not -path "./.git/*" -not -path "./.venv/*" | wc -l
   ```

2. **For TESTS classification:**
   ```bash
   # Find all test files
   find tests -name "*.py" -type f | wc -l
   find tests -name "test_*.py" -type f | wc -l
   ```

3. **Add new entries with subcategories**

#### Deliverables
- Updated `DOCS_FILE_CLASSIFICATION.yaml`
- Updated `TESTS_FILE_CLASSIFICATION.yaml`
- Change counts documented

#### Acceptance Criteria
- [ ] All docs files classified
- [ ] All test files classified
- [ ] Counts match actual file counts
- [ ] YAMLs validate without errors

---

### Task 1.9: Verify and Update CLASSIFICATION_TAXONOMY.md

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QSV`
**Type:** documentation | **Complexity:** simple | **Priority:** medium

#### Description
Review taxonomy for completeness. Add new subcategories if new file types require them.

#### Source File
```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/CLASSIFICATION_TAXONOMY.md
```

#### Implementation Steps

1. **Review current taxonomy structure**
   - 7 primary categories
   - 40+ subcategories

2. **Check if new files fit existing subcategories**
   - vibey/services/ - new subcategory needed?
   - vibey/cli/command_modules/ - new subcategory needed?

3. **Propose additions if needed:**
   ```markdown
   ### CORE-LIB Subcategories (Updated)

   - cli-command-modules (NEW) - Modular CLI command implementations
   - services (NEW) - Service layer implementations
   - services-implementation (NEW) - Implementation mode services
   ```

4. **Update taxonomy document**

#### Deliverables
- Updated `CLASSIFICATION_TAXONOMY.md` if needed
- `TAXONOMY_CHANGE_LOG.md` documenting additions

#### Acceptance Criteria
- [ ] All file types have appropriate subcategory
- [ ] New subcategories documented with rationale
- [ ] Taxonomy consistent and complete
- [ ] No orphaned files without classification

---

## Sprint Execution Order

```
Task 1.1 (scan) ──┬──> Task 1.2 (inventory)
                  ├──> Task 1.3 (classify) ──> Task 1.9 (taxonomy)
                  ├──> Task 1.4 (registry)
                  ├──> Task 1.5 (dependency graph)
                  ├──> Task 1.7 (vibey classification)
                  └──> Task 1.8 (docs/tests classification)

Task 1.2-1.8 ────────> Task 1.6 (delta report)
```

## Output Location

All deliverables should be placed in:
```
.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1/outputs/
```

## Success Criteria

- [ ] All 9 tasks completed
- [ ] File counts reconciled (expected: 800+ files total)
- [ ] All classification files updated
- [ ] Delta report generated
- [ ] No validation errors in YAML files
