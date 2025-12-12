# Sprint 1.1: File Inventory & Classification
## Comprehensive Task Plan

**Sprint ID:** Phase 1.1
**Track:** User Journey Audit & Documentation Coverage
**Duration:** 2 weeks
**Tasks:** 7
**Total Estimated Tokens:** 110,000

---

## Sprint Overview

This sprint establishes the foundation for all subsequent audits by creating a complete inventory of every file in the repository and classifying them according to a structured taxonomy. The outputs from this sprint will be referenced throughout Phase 1 and inform the building phases that follow.

### Sprint Goals
1. Build tooling to automate file inventory generation
2. Define a comprehensive file classification taxonomy
3. Classify every file in `vibey/`, `docs/`, and `tests/`
4. Map relationships and dependencies between files
5. Produce a consolidated file registry as the source of truth

### Key Deliverables
- `CLASSIFICATION_TAXONOMY.md` - Classification schema definition
- `VIBEY_FILE_CLASSIFICATION.yaml` - Core library file classifications
- `DOCS_FILE_CLASSIFICATION.yaml` - Documentation file classifications
- `TESTS_FILE_CLASSIFICATION.yaml` - Test file classifications
- `FILE_DEPENDENCY_GRAPH.yaml` - Inter-file dependency mapping
- `FILE_REGISTRY.yaml` - Consolidated source of truth

---

## Task 1: Create File Inventory Tooling

**Type:** Development
**Complexity:** Medium
**Estimated Tokens:** 15,000
**Duration:** 2-3 days

### Objective
Build a Python script/module that recursively scans specified directories and outputs a structured inventory of all files.

### Implementation Details

#### Input
- List of directories to scan: `vibey/`, `docs/`, `tests/`, `scripts/`
- Exclusion patterns: `__pycache__/`, `*.pyc`, `.git/`, `node_modules/`

#### Output Format (YAML)
```yaml
inventory:
  generated_at: "2025-12-11T00:00:00Z"
  directories_scanned:
    - vibey/
    - docs/
    - tests/
    - scripts/
  summary:
    total_files: 450
    total_directories: 85
    by_extension:
      .py: 280
      .md: 95
      .yaml: 45
      .json: 20
      other: 10
  files:
    - path: vibey/__init__.py
      type: python
      size_bytes: 335
      last_modified: "2025-11-10T18:44:00Z"
      lines: 12
    - path: vibey/cli/main.py
      type: python
      size_bytes: 12500
      last_modified: "2025-11-24T09:31:00Z"
      lines: 360
    # ... all files
```

#### Implementation Steps
1. Create `vibey/operations/audit/file_inventory.py`
2. Implement recursive directory walker with exclusion support
3. Extract file metadata: path, extension, size, mtime, line count
4. Generate summary statistics
5. Output to YAML format
6. Add CLI command: `vibey audit inventory [--output FILE]`

#### Acceptance Criteria
- [ ] Script successfully scans all target directories
- [ ] Handles symlinks and special files gracefully
- [ ] Excludes specified patterns (pycache, git, etc.)
- [ ] Output is valid YAML
- [ ] Summary statistics are accurate
- [ ] Execution completes in < 30 seconds for full repo

---

## Task 2: Define File Classification Taxonomy

**Type:** Documentation
**Complexity:** Simple
**Estimated Tokens:** 8,000
**Duration:** 1 day

### Objective
Create a comprehensive classification schema that categorizes all files in the repository by purpose, type, and role.

### Taxonomy Structure

#### Primary Categories

```
1. CORE-LIB (vibey/ package code)
   ├── 1.1 models        - Data models, schemas, types
   ├── 1.2 operations    - Business logic, commands
   ├── 1.3 serialization - YAML/JSON/SQL loaders/dumpers
   ├── 1.4 cli           - CLI commands, entry points
   ├── 1.5 mcp           - MCP server, tools, resources
   ├── 1.6 adapters      - Platform adapters
   ├── 1.7 common        - Shared utilities, errors
   ├── 1.8 config        - Configuration loading/validation
   ├── 1.9 content       - Content management
   ├── 1.10 platform     - Platform abstraction
   └── 1.11 root         - Package init, main, type markers

2. DOCUMENTATION (docs/ and root docs)
   ├── 2.1 getting-started - Onboarding, quickstart
   ├── 2.2 guides          - How-to guides, tutorials
   ├── 2.3 reference       - API/CLI reference
   ├── 2.4 development     - Contributor docs
   ├── 2.5 architecture    - Design docs, ADRs
   ├── 2.6 roadmap         - Roadmap documentation
   ├── 2.7 operations      - Operational procedures
   └── 2.8 root            - README, CHANGELOG, etc.

3. TESTS (tests/ directory)
   ├── 3.1 unit        - Unit tests
   ├── 3.2 integration - Integration tests
   ├── 3.3 e2e         - End-to-end tests
   ├── 3.4 fixtures    - Test data, mocks
   └── 3.5 utilities   - Test helpers

4. SCRIPTS (scripts/ directory)
   ├── 4.1 migration   - Data migration scripts
   ├── 4.2 tooling     - Development tools
   └── 4.3 automation  - CI/CD scripts

5. CONFIG (root config files)
   ├── 5.1 python      - pyproject.toml, setup.cfg
   ├── 5.2 testing     - pytest.ini, .coveragerc
   ├── 5.3 git         - .gitignore, .pre-commit
   └── 5.4 packaging   - MANIFEST.in
```

#### Classification Metadata Schema
```yaml
file_classification:
  path: string           # Relative file path
  category: string       # Primary category (1-5)
  subcategory: string    # Subcategory (e.g., 1.2)
  purpose: string        # Brief description of file purpose
  module: string         # For code: parent module name
  dependencies: list     # Files this file imports/references
  dependents: list       # Files that import/reference this file
  test_coverage: boolean # For code: has associated tests?
  doc_coverage: boolean  # For code: is documented?
  last_audit: date       # When file was last audited
```

### Deliverable
Create `CLASSIFICATION_TAXONOMY.md` documenting:
1. Full taxonomy tree with descriptions
2. Classification metadata schema
3. Decision rules for ambiguous cases
4. Examples for each category

### Acceptance Criteria
- [ ] All categories and subcategories defined
- [ ] Clear criteria for each classification
- [ ] Schema documented with all required fields
- [ ] Examples provided for each category
- [ ] Edge cases addressed (e.g., test fixtures vs utilities)

---

## Task 3: Classify All vibey/ Package Files

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 20,000
**Duration:** 2-3 days

### Objective
Apply the classification taxonomy to every file in the `vibey/` directory, producing a complete classification manifest.

### Process

#### Step 1: Generate File List
Use inventory tooling from Task 1 to get complete file list for `vibey/`.

#### Step 2: Classify Each File
For each file, determine:
- Category and subcategory from taxonomy
- Purpose (1-2 sentence description)
- Parent module
- Key exports/functionality

#### Step 3: Document Dependencies
For Python files, extract:
- Import statements (internal and external)
- Files that import this file (reverse lookup)

### Output Format
```yaml
# VIBEY_FILE_CLASSIFICATION.yaml
classification:
  generated_at: "2025-12-11T00:00:00Z"
  taxonomy_version: "1.0"
  directory: vibey/
  summary:
    total_files: 180
    by_category:
      models: 25
      operations: 45
      serialization: 20
      cli: 15
      mcp: 12
      adapters: 18
      common: 8
      config: 10
      content: 8
      platform: 7
      root: 3
  files:
    - path: vibey/__init__.py
      category: core-lib
      subcategory: root
      purpose: Package initialization, version export, public API definition
      module: vibey
      exports:
        - __version__
        - Roadmap
        - Track
      dependencies:
        internal: []
        external: []
      dependents:
        - vibey/cli/main.py
        - vibey/mcp/server.py
      test_coverage: true
      doc_coverage: true

    - path: vibey/cli/main.py
      category: core-lib
      subcategory: cli
      purpose: Main CLI entry point using Click, defines command groups
      module: vibey.cli
      exports:
        - cli (Click group)
        - main
      dependencies:
        internal:
          - vibey/cli/commands.py
          - vibey/operations/roadmap/query.py
        external:
          - click
          - rich
      dependents:
        - vibey/__main__.py
      test_coverage: true
      doc_coverage: true

    # ... continue for all files
```

### Classification Guidelines

#### For Each File, Document:
1. **Category/Subcategory** - Based on taxonomy
2. **Purpose** - What the file does (1-2 sentences)
3. **Module** - Python module path
4. **Exports** - Key classes, functions, constants exported
5. **Dependencies** - What it imports (internal and external)
6. **Dependents** - What imports it
7. **Test Coverage** - Does a corresponding test file exist?
8. **Doc Coverage** - Is it documented (docstrings, external docs)?

### Acceptance Criteria
- [ ] Every file in vibey/ is classified
- [ ] Classifications match taxonomy categories
- [ ] Purpose descriptions are accurate and useful
- [ ] Dependencies are correctly identified
- [ ] Test coverage flags are accurate
- [ ] Output is valid YAML

---

## Task 4: Classify All docs/ Files

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 15,000
**Duration:** 1-2 days

### Objective
Apply the classification taxonomy to every file in the `docs/` directory.

### Output Format
```yaml
# DOCS_FILE_CLASSIFICATION.yaml
classification:
  generated_at: "2025-12-11T00:00:00Z"
  taxonomy_version: "1.0"
  directory: docs/
  summary:
    total_files: 95
    by_category:
      getting-started: 5
      guides: 35
      reference: 12
      development: 15
      architecture: 8
      roadmap: 10
      operations: 5
      root: 5
  files:
    - path: docs/getting-started/QUICK_START.md
      category: documentation
      subcategory: getting-started
      purpose: 10-minute quickstart guide for new users
      topic_coverage:
        - installation
        - first project setup
        - basic CLI usage
      target_audience:
        - new users
        - evaluators
      references_code:
        - vibey/cli/main.py
        - vibey/operations/roadmap/init.py
      last_verified: null
      accuracy_status: unknown

    # ... continue for all files
```

### Documentation-Specific Fields
- **topic_coverage** - What topics the doc covers
- **target_audience** - Who the doc is for
- **references_code** - Code files the doc references
- **last_verified** - When doc accuracy was last verified
- **accuracy_status** - known_accurate | needs_review | outdated | unknown

### Acceptance Criteria
- [ ] Every file in docs/ is classified
- [ ] Topic coverage accurately reflects content
- [ ] Target audience is identified
- [ ] Code references are mapped
- [ ] Output is valid YAML

---

## Task 5: Classify All tests/ Files

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 15,000
**Duration:** 1-2 days

### Objective
Apply the classification taxonomy to every file in the `tests/` directory.

### Output Format
```yaml
# TESTS_FILE_CLASSIFICATION.yaml
classification:
  generated_at: "2025-12-11T00:00:00Z"
  taxonomy_version: "1.0"
  directory: tests/
  summary:
    total_files: 120
    by_category:
      unit: 65
      integration: 25
      e2e: 10
      fixtures: 12
      utilities: 8
  files:
    - path: tests/cli/test_commands.py
      category: tests
      subcategory: unit
      purpose: Unit tests for CLI command implementations
      tests_module: vibey.cli.commands
      test_count: 24
      coverage_scope:
        - vibey/cli/commands.py
      fixtures_used:
        - tests/fixtures/sample_roadmap.yaml
      last_run_status: unknown

    # ... continue for all files
```

### Test-Specific Fields
- **tests_module** - What module/file this tests
- **test_count** - Number of test functions
- **coverage_scope** - Files covered by these tests
- **fixtures_used** - Test fixtures referenced
- **last_run_status** - pass | fail | skip | unknown

### Acceptance Criteria
- [ ] Every file in tests/ is classified
- [ ] Test-to-code mapping is accurate
- [ ] Test counts are documented
- [ ] Fixtures are cross-referenced
- [ ] Output is valid YAML

---

## Task 6: Map File Relationships and Dependencies

**Type:** Research
**Complexity:** Complex
**Estimated Tokens:** 25,000
**Duration:** 3-4 days

### Objective
Analyze import statements and cross-references to build a comprehensive dependency graph showing how files relate to each other.

### Analysis Scope

#### Python Import Analysis
- Parse all `.py` files for import statements
- Resolve relative imports to absolute paths
- Track both `import X` and `from X import Y`
- Identify external vs internal dependencies

#### Documentation Reference Analysis
- Parse Markdown files for code references
- Identify links to other docs
- Track API/CLI documentation coverage

#### Test Coverage Mapping
- Map test files to source files they test
- Identify untested code files

### Output Format
```yaml
# FILE_DEPENDENCY_GRAPH.yaml
dependency_graph:
  generated_at: "2025-12-11T00:00:00Z"
  analysis_scope:
    - vibey/
    - docs/
    - tests/
    - scripts/

  summary:
    total_nodes: 400
    total_edges: 1250
    internal_dependencies: 850
    external_dependencies: 400
    orphan_files: 12  # Files with no dependencies or dependents

  # Nodes (files)
  nodes:
    - id: vibey/cli/main.py
      type: python
      category: core-lib

  # Edges (dependencies)
  edges:
    # Import dependencies
    - source: vibey/cli/main.py
      target: vibey/cli/commands.py
      type: import

    - source: vibey/cli/main.py
      target: click  # external
      type: import_external

    # Documentation references
    - source: docs/reference/CLI_REFERENCE.md
      target: vibey/cli/main.py
      type: documents

    # Test coverage
    - source: tests/cli/test_main.py
      target: vibey/cli/main.py
      type: tests

  # Dependency metrics per file
  file_metrics:
    vibey/cli/main.py:
      imports: 12
      imported_by: 3
      documented_by: 2
      tested_by: 1
      coupling_score: 0.45  # 0-1, lower is better

  # Circular dependencies (anti-pattern)
  circular_dependencies:
    - cycle:
        - vibey/operations/roadmap/query.py
        - vibey/operations/roadmap/update.py
      severity: warning

  # Orphan files (no connections)
  orphan_files:
    - path: vibey/legacy/old_loader.py
      reason: no_imports_or_dependents
```

### Analysis Steps

1. **Build Import Graph**
   - Parse all Python files with AST
   - Extract import statements
   - Resolve to file paths
   - Build directed graph

2. **Build Documentation Graph**
   - Parse Markdown for code references
   - Extract internal links
   - Map to source files

3. **Build Test Coverage Graph**
   - Map test files to source via naming convention
   - Parse test imports
   - Identify coverage relationships

4. **Calculate Metrics**
   - Coupling scores per file
   - Identify circular dependencies
   - Find orphan files
   - Compute dependency depth

### Acceptance Criteria
- [ ] All Python imports are correctly parsed
- [ ] Internal vs external dependencies distinguished
- [ ] Documentation references mapped
- [ ] Test coverage relationships identified
- [ ] Circular dependencies detected
- [ ] Orphan files identified
- [ ] Output is valid YAML
- [ ] Metrics are calculated correctly

---

## Task 7: Generate Consolidated File Registry

**Type:** Development
**Complexity:** Medium
**Estimated Tokens:** 12,000
**Duration:** 1-2 days

### Objective
Merge all classification outputs into a single `FILE_REGISTRY.yaml` that serves as the authoritative source of truth for all file information.

### Input Files
- `VIBEY_FILE_CLASSIFICATION.yaml` (Task 3)
- `DOCS_FILE_CLASSIFICATION.yaml` (Task 4)
- `TESTS_FILE_CLASSIFICATION.yaml` (Task 5)
- `FILE_DEPENDENCY_GRAPH.yaml` (Task 6)

### Output Format
```yaml
# FILE_REGISTRY.yaml
file_registry:
  version: "1.0"
  generated_at: "2025-12-11T00:00:00Z"
  taxonomy_version: "1.0"

  summary:
    total_files: 400
    by_directory:
      vibey/: 180
      docs/: 95
      tests/: 120
      scripts/: 5
    by_category:
      core-lib: 180
      documentation: 95
      tests: 120
      scripts: 5
    coverage_metrics:
      files_with_tests: 145
      files_with_docs: 160
      orphan_files: 12

  # Complete file listing with all metadata
  files:
    - path: vibey/cli/main.py
      # From classification
      category: core-lib
      subcategory: cli
      purpose: Main CLI entry point using Click
      module: vibey.cli
      exports: [cli, main]
      # From dependency graph
      dependencies:
        internal: [vibey/cli/commands.py, ...]
        external: [click, rich]
      dependents: [vibey/__main__.py]
      coupling_score: 0.45
      # Coverage status
      test_coverage:
        has_tests: true
        test_files: [tests/cli/test_main.py]
      doc_coverage:
        has_docs: true
        doc_files: [docs/reference/CLI_REFERENCE.md]
      # Metadata
      size_bytes: 12500
      lines: 360
      last_modified: "2025-11-24T09:31:00Z"

    # ... all other files

  # Cross-reference indexes for fast lookup
  indexes:
    by_category:
      core-lib:
        cli: [vibey/cli/main.py, vibey/cli/commands.py, ...]
        operations: [...]
      documentation: [...]
      tests: [...]

    by_module:
      vibey.cli: [vibey/cli/main.py, ...]
      vibey.operations: [...]

    untested_files:
      - vibey/legacy/old_loader.py
      - vibey/adapters/experimental.py

    undocumented_files:
      - vibey/internal/helper.py
```

### Implementation Steps

1. **Load All Classification Files**
   - Parse each YAML output
   - Validate schema consistency

2. **Merge File Data**
   - Combine classification + dependency data per file
   - Resolve any conflicts

3. **Calculate Summary Statistics**
   - Total counts by category
   - Coverage percentages
   - Quality metrics

4. **Build Indexes**
   - Category index
   - Module index
   - Untested/undocumented lists

5. **Generate Output**
   - Write consolidated YAML
   - Validate output schema

### Acceptance Criteria
- [ ] All source files are merged correctly
- [ ] No data loss during merge
- [ ] Summary statistics are accurate
- [ ] Indexes are correctly built
- [ ] Output is valid YAML
- [ ] Can be loaded and queried efficiently

---

## Sprint Dependencies

```
Task 1 (Tooling) ──┬──> Task 3 (Classify vibey/)
                   ├──> Task 4 (Classify docs/)
                   └──> Task 5 (Classify tests/)

Task 2 (Taxonomy) ─┬──> Task 3 (Classify vibey/)
                   ├──> Task 4 (Classify docs/)
                   └──> Task 5 (Classify tests/)

Task 3 ──┐
Task 4 ──┼──> Task 6 (Dependencies) ──> Task 7 (Registry)
Task 5 ──┘
```

## Sprint Success Criteria

1. **Completeness**
   - [ ] Every file in scope is inventoried
   - [ ] Every file is classified
   - [ ] All dependencies are mapped

2. **Accuracy**
   - [ ] Classifications match actual file purpose
   - [ ] Dependency graph is correct
   - [ ] Metrics calculations are accurate

3. **Usability**
   - [ ] Outputs are valid YAML
   - [ ] Registry is queryable
   - [ ] Documentation is clear

4. **Quality**
   - [ ] No orphan files left unclassified
   - [ ] Circular dependencies identified
   - [ ] Coverage gaps documented

---

## Output Directory Structure

```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/
├── SPRINT_PLAN.md                    # This document
├── CLASSIFICATION_TAXONOMY.md        # Task 2 output
├── VIBEY_FILE_CLASSIFICATION.yaml    # Task 3 output
├── DOCS_FILE_CLASSIFICATION.yaml     # Task 4 output
├── TESTS_FILE_CLASSIFICATION.yaml    # Task 5 output
├── FILE_DEPENDENCY_GRAPH.yaml        # Task 6 output
├── FILE_REGISTRY.yaml                # Task 7 output
└── SPRINT_COMPLETION_REPORT.md       # Final summary
```
