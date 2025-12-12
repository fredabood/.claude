# Sprint 1.5: Scripts & Project Config Audit
## Comprehensive Task Plan

**Sprint ID:** Phase 1.5
**Track:** User Journey Audit & Documentation Coverage
**Duration:** 1 week
**Tasks:** 10
**Total Estimated Tokens:** 85,000

---

## Sprint Overview

This sprint audits the standalone scripts directory and project configuration files. Scripts often represent one-off utilities, migration tools, or operations that may need to be integrated into the CLI or deprecated. Project configuration files define the build, test, and development environment. This audit will identify scripts that should be migrated to the CLI, deprecated, or documented, and ensure project configuration is consistent and well-documented.

### Sprint Goals
1. Define audit criteria for scripts and configuration files
2. Inventory and classify all scripts
3. Audit each script for quality, relevance, and migration potential
4. Audit all project configuration files
5. Identify CLI migration candidates
6. Identify deprecation candidates
7. Produce actionable recommendations

### Prerequisites
- Sprint 1.1 outputs: `FILE_REGISTRY.yaml`
- Sprint 1.2 outputs: `CORE_LIBRARY_AUDIT_SUMMARY.md` (for understanding CLI capabilities)

### Key Deliverables
- `SCRIPTS_AUDIT_CRITERIA.md` - Scripts and config audit criteria
- `SCRIPTS_INVENTORY.yaml` - Complete scripts inventory
- `AUDIT_PROJECT_CONFIG.yaml` - Project configuration audit
- `AUDIT_CONSOLIDATE_DOGFOODING.yaml` - Script-specific audit
- `AUDIT_CREATE_DOGFOODING.yaml` - Script-specific audit
- `AUDIT_EXECUTE_MIGRATION.yaml` - Script-specific audit
- `AUDIT_RUN_MIGRATION_STANDALONE.yaml` - Script-specific audit
- `CLI_MIGRATION_CANDIDATES.yaml` - Scripts to migrate to CLI
- `DEPRECATION_CANDIDATES.yaml` - Scripts/configs to deprecate
- `SCRIPTS_AUDIT_SUMMARY.md` - Consolidated summary

---

## Task 1: Define Scripts Audit Criteria

**Type:** Documentation
**Complexity:** Simple
**Estimated Tokens:** 8,000
**Duration:** 0.5 days

### Objective
Document the audit criteria for standalone scripts and project configuration files.

### Scripts Audit Criteria Framework

#### 1. Purpose & Relevance
- **Clear Purpose**: Does the script have a clear, documented purpose?
- **Current Relevance**: Is the script still needed?
- **Frequency of Use**: How often is this script used?
- **Alternatives**: Are there CLI commands that do the same thing?

```yaml
purpose_relevance:
  purpose_documented: true | false
  purpose_description: string
  still_relevant: true | false | unknown
  usage_frequency: daily | weekly | monthly | rarely | never | unknown
  alternatives:
    cli_equivalent: string | null
    library_function: string | null
  relevance_score: 0-100
```

#### 2. Code Quality
- **Documentation**: Is the script documented (docstrings, comments)?
- **Error Handling**: Does it handle errors gracefully?
- **Arguments**: Does it accept command-line arguments properly?
- **Logging**: Does it provide appropriate output/logging?
- **Testing**: Does the script have tests?

```yaml
code_quality:
  documentation:
    module_docstring: present | missing
    function_docstrings: X / Y
    inline_comments: adequate | sparse | none
    usage_instructions: present | missing
  error_handling:
    try_except_blocks: true | false
    error_messages: helpful | cryptic | none
    exit_codes: proper | improper | none
  arguments:
    uses_argparse: true | false
    arguments_documented: true | false
    help_text: present | missing
  logging:
    uses_logging: true | false
    output_level: verbose | normal | quiet | none
  testing:
    has_tests: true | false
    test_file: string | null
  quality_score: 0-100
```

#### 3. Integration Potential
- **CLI Candidate**: Should this become a CLI command?
- **Library Candidate**: Should this become a library function?
- **Standalone Justified**: Is there a reason it must be standalone?
- **Dependencies**: What does it depend on?

```yaml
integration_potential:
  cli_candidate: true | false
  cli_candidate_reason: string
  suggested_command: string | null  # e.g., "vibey roadmap migrate"
  library_candidate: true | false
  library_candidate_reason: string
  suggested_location: string | null  # e.g., "vibey/operations/roadmap/migrate.py"
  standalone_justified: true | false
  justification: string | null
  dependencies:
    internal: [list of vibey modules used]
    external: [list of external packages]
  integration_score: 0-100  # Higher = more suitable for integration
```

#### 4. Maintenance Status
- **Last Modified**: When was the script last updated?
- **Author**: Who wrote/maintains the script?
- **Active Development**: Is it actively maintained?
- **Technical Debt**: Any obvious technical debt?

```yaml
maintenance_status:
  last_modified: date
  author: string | unknown
  active_development: true | false
  technical_debt:
    present: true | false
    items: [list]
  maintenance_score: 0-100
```

### Project Config Audit Criteria Framework

#### 1. Completeness
- **Required Fields**: Are all required fields present?
- **Optional Fields**: Which optional fields are used?
- **Documentation**: Are settings documented?

```yaml
completeness:
  required_fields:
    present: X / Y
    missing: [list]
  optional_fields:
    used: [list]
    available_unused: [list]
  settings_documented: true | false
  completeness_score: 0-100
```

#### 2. Correctness
- **Valid Syntax**: Is the config syntactically valid?
- **Valid Values**: Are all values valid?
- **Consistency**: Are settings consistent with each other?

```yaml
correctness:
  syntax_valid: true | false
  values_valid: true | false
  invalid_values: [list]
  consistency_issues: [list]
  correctness_score: 0-100
```

#### 3. Best Practices
- **Standard Format**: Does it follow community standards?
- **Security**: Any security concerns?
- **Maintainability**: Easy to maintain?

```yaml
best_practices:
  follows_standard: true | false
  standard_name: string  # e.g., "PEP 621", "pytest best practices"
  security_concerns: [list]
  maintainability_issues: [list]
  best_practices_score: 0-100
```

### Quality Score Calculation

```yaml
quality_score:
  # For Scripts
  purpose_relevance: 0-25      # 25% weight
  code_quality: 0-30           # 30% weight
  integration_potential: 0-25  # 25% weight
  maintenance_status: 0-20     # 20% weight
  total: 0-100
  grade: A | B | C | D | F

  # For Config Files
  completeness: 0-35           # 35% weight
  correctness: 0-40            # 40% weight
  best_practices: 0-25         # 25% weight
  total: 0-100
  grade: A | B | C | D | F
```

### Deliverable
Create `SCRIPTS_AUDIT_CRITERIA.md` documenting:
1. Scripts audit criteria with descriptions
2. Config files audit criteria with descriptions
3. Scoring methodology
4. YAML schema for audit outputs
5. Decision framework for CLI migration vs deprecation

### Acceptance Criteria
- [ ] Scripts audit criteria documented
- [ ] Config audit criteria documented
- [ ] Scoring methodology clear
- [ ] Migration decision framework defined

---

## Task 2: Inventory All Scripts

**Type:** Research
**Complexity:** Simple
**Estimated Tokens:** 5,000
**Duration:** 0.5 days

### Objective
Create a complete inventory of all scripts in the scripts/ directory with basic metadata.

### Current Scripts Directory
```
scripts/
├── consolidate_dogfooding_track.py   # 25,762 bytes
├── create_dogfooding_track.py        # 25,107 bytes
├── execute_migration.py              # 4,729 bytes
└── run_migration_standalone.py       # 4,725 bytes
```

### Inventory Template
```yaml
# SCRIPTS_INVENTORY.yaml
inventory:
  generated_at: "2025-12-11T00:00:00Z"
  directory: scripts/

  summary:
    total_scripts: 4
    total_lines: X
    total_bytes: 60,323
    by_category:
      migration: 2
      roadmap_management: 2
      utilities: 0

  scripts:
    - path: scripts/consolidate_dogfooding_track.py
      size_bytes: 25762
      lines: X
      last_modified: "2025-12-10T00:05:00Z"
      category: roadmap_management
      brief_purpose: "Consolidates dogfooding track data"
      executable: false
      shebang: present | missing

    - path: scripts/create_dogfooding_track.py
      size_bytes: 25107
      lines: X
      last_modified: "2025-12-09T23:57:00Z"
      category: roadmap_management
      brief_purpose: "Creates dogfooding track structure"
      executable: false
      shebang: present | missing

    - path: scripts/execute_migration.py
      size_bytes: 4729
      lines: X
      last_modified: "2025-12-09T15:29:00Z"
      category: migration
      brief_purpose: "Executes database migrations"
      executable: true
      shebang: present

    - path: scripts/run_migration_standalone.py
      size_bytes: 4725
      lines: X
      last_modified: "2025-12-09T15:31:00Z"
      category: migration
      brief_purpose: "Runs migrations without dependencies"
      executable: true
      shebang: present

  historical_scripts:
    note: "Scripts that previously existed but were moved/deleted"
    items: []  # Populate from git history if relevant

  related_scripts_elsewhere:
    note: "Script-like files in other locations"
    items:
      - path: tests/conftest.py
        reason: "Test configuration, not a script"
      # Any other script-like files found
```

### Inventory Process
1. List all files in scripts/
2. Extract basic metadata (size, mtime, executable flag)
3. Read first 50 lines to determine purpose
4. Categorize by function
5. Check git history for removed scripts

### Acceptance Criteria
- [ ] All scripts inventoried
- [ ] Metadata extracted
- [ ] Categories assigned
- [ ] Output is valid YAML

---

## Task 3: Audit Project Configuration Files

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 15,000
**Duration:** 1 day

### Objective
Audit all project configuration files in the repository root.

### Configuration Files to Audit

```
Root Configuration Files:
├── .coveragerc          # 1,012 bytes - Coverage.py configuration
├── .gitignore           # 1,400 bytes - Git ignore patterns
├── .mcp.json            # 200 bytes - MCP server configuration
├── .pre-commit-config.yaml  # 2,241 bytes - Pre-commit hooks
├── MANIFEST.in          # 86 bytes - Package manifest
├── pyproject.toml       # 2,406 bytes - Python project configuration
└── pytest.ini           # 1,044 bytes - Pytest configuration
```

### Per-File Audit Templates

#### pyproject.toml
```yaml
file: pyproject.toml
purpose: Python project configuration (PEP 621)
size_bytes: 2406
config_type: python_project

sections_audit:
  build_system:
    present: true | false
    backend: string  # e.g., "setuptools"
    valid: true | false

  project:
    name: string
    version: string
    description: present | missing
    authors: present | missing
    license: present | missing
    readme: present | missing
    requires_python: string
    dependencies: [list]
    optional_dependencies: [dict]

  tool_sections:
    - tool: setuptools
      configured: true | false
      valid: true | false
    - tool: black
      configured: true | false
    - tool: isort
      configured: true | false
    - tool: mypy
      configured: true | false

pep621_compliance:
  compliant: true | false
  missing_required: [list]
  deprecated_fields: [list]

dependency_audit:
  runtime_deps: [list with versions]
  dev_deps: [list with versions]
  version_pinning: pinned | ranges | unpinned
  outdated: [list]  # If can be determined

quality_score:
  completeness: X
  correctness: X
  best_practices: X
  total: X
  grade: X
```

#### pytest.ini
```yaml
file: pytest.ini
purpose: Pytest configuration
size_bytes: 1044
config_type: testing

settings_audit:
  testpaths: [list]
  python_files: pattern
  python_classes: pattern
  python_functions: pattern
  addopts: string
  markers: [list]
  filterwarnings: [list]

coverage_integration:
  coverage_configured: true | false
  coverage_options: [list]

best_practices:
  strict_markers: true | false
  warning_filters: appropriate | missing | excessive
  parallel_execution: configured | not_configured

quality_score:
  completeness: X
  correctness: X
  best_practices: X
  total: X
  grade: X
```

#### .coveragerc
```yaml
file: .coveragerc
purpose: Coverage.py configuration
size_bytes: 1012
config_type: coverage

settings_audit:
  run:
    source: [list]
    branch: true | false
    omit: [list]
  report:
    exclude_lines: [list]
    fail_under: number | null
    show_missing: true | false
  html:
    directory: string

coverage_targets:
  line_target: X% | not_set
  branch_target: X% | not_set

quality_score:
  completeness: X
  correctness: X
  best_practices: X
  total: X
  grade: X
```

#### .pre-commit-config.yaml
```yaml
file: .pre-commit-config.yaml
purpose: Pre-commit hooks configuration
size_bytes: 2241
config_type: pre_commit

hooks_audit:
  repos:
    - repo: url
      hooks:
        - id: hook_name
          purpose: string
          stages: [list]

  hook_categories:
    formatting: [list of hooks]
    linting: [list of hooks]
    security: [list of hooks]
    testing: [list of hooks]
    other: [list of hooks]

coverage:
  python_formatting: true | false
  python_linting: true | false
  yaml_validation: true | false
  security_scanning: true | false
  commit_message: true | false

quality_score:
  completeness: X
  correctness: X
  best_practices: X
  total: X
  grade: X
```

#### .gitignore
```yaml
file: .gitignore
purpose: Git ignore patterns
size_bytes: 1400
config_type: git

patterns_audit:
  categories:
    python:
      patterns: [__pycache__, *.pyc, *.pyo, etc.]
      complete: true | false
    ide:
      patterns: [.idea/, .vscode/, etc.]
      complete: true | false
    build:
      patterns: [dist/, build/, *.egg-info/]
      complete: true | false
    testing:
      patterns: [.coverage, htmlcov/, .pytest_cache/]
      complete: true | false
    environment:
      patterns: [.env, .venv/, venv/]
      complete: true | false
    project_specific:
      patterns: [list]
      documented: true | false

missing_patterns:
  recommended: [list of patterns that should be added]

over_ignoring:
  patterns: [list of patterns that might be too broad]

quality_score:
  completeness: X
  correctness: X
  best_practices: X
  total: X
  grade: X
```

#### MANIFEST.in
```yaml
file: MANIFEST.in
purpose: Package distribution manifest
size_bytes: 86
config_type: packaging

directives_audit:
  include: [list]
  exclude: [list]
  recursive_include: [list]
  recursive_exclude: [list]
  graft: [list]
  prune: [list]

package_completeness:
  includes_all_needed: true | false
  missing: [list]
  unnecessary: [list]

quality_score:
  completeness: X
  correctness: X
  best_practices: X
  total: X
  grade: X
```

#### .mcp.json
```yaml
file: .mcp.json
purpose: MCP server configuration
size_bytes: 200
config_type: mcp

settings_audit:
  server_configured: true | false
  tools_configured: [list]
  resources_configured: [list]

security:
  sensitive_data: true | false
  should_be_gitignored: true | false

quality_score:
  completeness: X
  correctness: X
  best_practices: X
  total: X
  grade: X
```

### Output Format
```yaml
# AUDIT_PROJECT_CONFIG.yaml
audit:
  scope: project_configuration_files
  generated_at: "2025-12-11T00:00:00Z"
  criteria_version: "1.0"

  files:
    - path: pyproject.toml
      # ... full audit per template
    - path: pytest.ini
      # ... full audit
    - path: .coveragerc
      # ... full audit
    - path: .pre-commit-config.yaml
      # ... full audit
    - path: .gitignore
      # ... full audit
    - path: MANIFEST.in
      # ... full audit
    - path: .mcp.json
      # ... full audit

  cross_file_analysis:
    consistency:
      python_version_consistent: true | false
      versions_found: [list by file]
    redundancy:
      duplicated_settings: [list]
    gaps:
      missing_configs: [list]  # e.g., missing mypy.ini

  summary:
    files_audited: 7
    average_quality_score: X
    grade_distribution:
      A: X
      B: X
      C: X
      D: X
      F: X
    critical_issues: [list]
    recommendations: [list]
```

### Acceptance Criteria
- [ ] All 7 config files audited
- [ ] Cross-file consistency checked
- [ ] Best practices assessed
- [ ] Recommendations generated

---

## Task 4: Audit consolidate_dogfooding_track.py

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 12,000
**Duration:** 0.5 days

### Objective
Deep audit of the consolidate_dogfooding_track.py script.

### Script Profile
```
File: scripts/consolidate_dogfooding_track.py
Size: 25,762 bytes
Purpose: Consolidates dogfooding track data
Category: Roadmap Management
```

### Audit Template
```yaml
# AUDIT_CONSOLIDATE_DOGFOODING.yaml
audit:
  file: scripts/consolidate_dogfooding_track.py
  generated_at: "2025-12-11T00:00:00Z"

  metadata:
    size_bytes: 25762
    lines: X
    last_modified: "2025-12-10"
    executable: false

  purpose_analysis:
    stated_purpose: string  # From docstring
    actual_purpose: string  # From code analysis
    use_case: "One-time migration | Recurring task | Development utility"
    frequency: "Used once | Used occasionally | Used regularly"

  code_analysis:
    structure:
      functions: [list with line counts]
      classes: [list with line counts]
      main_block: true | false

    imports:
      standard_library: [list]
      third_party: [list]
      internal: [list]  # vibey.* imports

    complexity:
      cyclomatic_complexity_avg: X
      cyclomatic_complexity_max: X
      high_complexity_functions: [list]

    code_patterns:
      uses_argparse: true | false
      uses_logging: true | false
      uses_pathlib: true | false
      hardcoded_paths: [list]
      hardcoded_values: [list]

  documentation:
    module_docstring:
      present: true | false
      content: string
      describes_usage: true | false
    function_docstrings:
      total: X
      documented: X
      coverage: X%
    inline_comments:
      count: X
      quality: adequate | sparse | excessive
    usage_example:
      present: true | false
      location: string | null

  error_handling:
    try_except_blocks: X
    specific_exceptions: [list]
    generic_exceptions: X
    error_messages: helpful | cryptic | none
    exit_codes: [list]

  testing:
    has_tests: true | false
    test_file: string | null
    test_coverage: X% | unknown

  integration_assessment:
    cli_candidate:
      recommended: true | false
      reason: string
      suggested_command: string | null
      migration_effort: low | medium | high

    library_candidate:
      recommended: true | false
      reason: string
      suggested_location: string | null

    current_alternatives:
      cli_commands: [list of existing commands that overlap]
      library_functions: [list of existing functions that overlap]

  maintenance:
    last_modified: date
    modification_history: X commits
    technical_debt:
      items: [list]
      severity: low | medium | high

  security:
    file_operations: [list]
    database_operations: [list]
    external_calls: [list]
    concerns: [list]

  quality_score:
    purpose_relevance: X
    code_quality: X
    integration_potential: X
    maintenance_status: X
    total: X
    grade: X

  recommendations:
    immediate: [list]
    short_term: [list]
    decision: migrate_to_cli | keep_as_script | deprecate
    decision_rationale: string
```

### Key Questions to Answer
1. What does this script do exactly?
2. Is this a one-time script or ongoing utility?
3. Should this be a CLI command?
4. Is there existing CLI functionality that overlaps?
5. Are there hardcoded values that should be configurable?
6. Is the script tested?

### Acceptance Criteria
- [ ] Full code analysis completed
- [ ] Integration potential assessed
- [ ] Recommendation generated
- [ ] Quality score calculated

---

## Task 5: Audit create_dogfooding_track.py

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 12,000
**Duration:** 0.5 days

### Objective
Deep audit of the create_dogfooding_track.py script.

### Script Profile
```
File: scripts/create_dogfooding_track.py
Size: 25,107 bytes
Purpose: Creates dogfooding track structure
Category: Roadmap Management
```

### Audit Template
```yaml
# AUDIT_CREATE_DOGFOODING.yaml
audit:
  file: scripts/create_dogfooding_track.py
  generated_at: "2025-12-11T00:00:00Z"

  # Same structure as Task 4
  metadata: ...
  purpose_analysis: ...
  code_analysis: ...
  documentation: ...
  error_handling: ...
  testing: ...
  integration_assessment: ...
  maintenance: ...
  security: ...
  quality_score: ...
  recommendations: ...
```

### Key Questions to Answer
1. What does this script create?
2. Is this functionality needed in the CLI?
3. Does `vibey roadmap create track` do the same thing?
4. Are there hardcoded track-specific values?
5. Should this be generalized?

### Acceptance Criteria
- [ ] Full code analysis completed
- [ ] Comparison with existing CLI commands
- [ ] Recommendation generated
- [ ] Quality score calculated

---

## Task 6: Audit execute_migration.py

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 8,000
**Duration:** 0.5 days

### Objective
Deep audit of the execute_migration.py script.

### Script Profile
```
File: scripts/execute_migration.py
Size: 4,729 bytes
Purpose: Executes database migrations
Category: Migration
Executable: Yes
```

### Audit Template
```yaml
# AUDIT_EXECUTE_MIGRATION.yaml
audit:
  file: scripts/execute_migration.py
  generated_at: "2025-12-11T00:00:00Z"

  # Same structure as Task 4
  metadata: ...
  purpose_analysis: ...
  code_analysis: ...
  documentation: ...
  error_handling: ...
  testing: ...
  integration_assessment: ...
  maintenance: ...
  security: ...
  quality_score: ...
  recommendations: ...
```

### Key Questions to Answer
1. What migrations does this execute?
2. Is this a critical production script?
3. Should migration be a CLI command?
4. Is there proper backup/rollback handling?
5. Are migrations idempotent?

### Acceptance Criteria
- [ ] Migration functionality analyzed
- [ ] Safety assessment completed
- [ ] CLI integration potential assessed
- [ ] Quality score calculated

---

## Task 7: Audit run_migration_standalone.py

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 8,000
**Duration:** 0.5 days

### Objective
Deep audit of the run_migration_standalone.py script.

### Script Profile
```
File: scripts/run_migration_standalone.py
Size: 4,725 bytes
Purpose: Runs migrations without dependencies
Category: Migration
Executable: Yes
```

### Audit Template
```yaml
# AUDIT_RUN_MIGRATION_STANDALONE.yaml
audit:
  file: scripts/run_migration_standalone.py
  generated_at: "2025-12-11T00:00:00Z"

  # Same structure as Task 4
  metadata: ...
  purpose_analysis: ...
  code_analysis: ...
  documentation: ...
  error_handling: ...
  testing: ...
  integration_assessment: ...
  maintenance: ...
  security: ...
  quality_score: ...
  recommendations: ...
```

### Key Questions to Answer
1. How does this differ from execute_migration.py?
2. Why is "standalone" needed?
3. Is there duplication between the two migration scripts?
4. Should these be consolidated?

### Comparison with execute_migration.py
```yaml
comparison:
  execute_migration:
    size: 4729
    dependencies: [list]
    use_case: string
  run_migration_standalone:
    size: 4725
    dependencies: [list]
    use_case: string
  differences:
    - description: string
  overlap:
    percentage: X%
    shared_code: [list of shared functions/patterns]
  consolidation_recommended: true | false
  consolidation_approach: string
```

### Acceptance Criteria
- [ ] Script analyzed
- [ ] Comparison with execute_migration.py completed
- [ ] Consolidation potential assessed
- [ ] Quality score calculated

---

## Task 8: Identify CLI Migration Candidates

**Type:** Research
**Complexity:** Simple
**Estimated Tokens:** 6,000
**Duration:** 0.5 days

### Objective
Based on all script audits, identify scripts that should be migrated to CLI commands.

### Migration Decision Framework

```yaml
migration_decision_matrix:
  migrate_if:
    - "Script is used regularly (weekly or more)"
    - "Script functionality is generally useful"
    - "Script aligns with existing CLI patterns"
    - "Migration effort is justified by value"

  keep_as_script_if:
    - "Script is one-time use"
    - "Script is development/debugging only"
    - "Script requires special permissions/environment"
    - "Script is temporary/experimental"

  deprecate_if:
    - "Script duplicates existing CLI functionality"
    - "Script is obsolete"
    - "Script is broken and unfixable"
```

### Output Format
```yaml
# CLI_MIGRATION_CANDIDATES.yaml
migration_candidates:
  generated_at: "2025-12-11T00:00:00Z"

  summary:
    total_scripts: 4
    migrate_to_cli: X
    keep_as_script: X
    deprecate: X

  candidates:
    - script: scripts/consolidate_dogfooding_track.py
      decision: migrate | keep | deprecate

      migration_details:
        suggested_command: "vibey roadmap consolidate"
        command_group: roadmap
        options:
          - name: --track
            type: string
            required: true
            description: "Track to consolidate"
          - name: --dry-run
            type: flag
            description: "Show what would be done"

        implementation_notes:
          - "Extract core logic to vibey/operations/roadmap/consolidate.py"
          - "Add CLI wrapper in vibey/cli/commands.py"
          - "Add tests in tests/cli/test_consolidate.py"

        effort_estimate: "4-6 hours"
        priority: high | medium | low

    - script: scripts/create_dogfooding_track.py
      decision: migrate | keep | deprecate
      # ... similar structure

    - script: scripts/execute_migration.py
      decision: migrate | keep | deprecate
      # ... similar structure

    - script: scripts/run_migration_standalone.py
      decision: migrate | keep | deprecate
      # ... similar structure

  implementation_roadmap:
    phase_1:
      description: "High-priority migrations"
      scripts: [list]
      effort: "X hours"
    phase_2:
      description: "Medium-priority migrations"
      scripts: [list]
      effort: "X hours"
```

### Acceptance Criteria
- [ ] All scripts assessed for migration
- [ ] CLI command designs proposed
- [ ] Effort estimates provided
- [ ] Implementation roadmap created

---

## Task 9: Identify Deprecation Candidates

**Type:** Research
**Complexity:** Simple
**Estimated Tokens:** 5,000
**Duration:** 0.5 days

### Objective
Identify scripts and configuration settings that should be deprecated or removed.

### Deprecation Categories

```yaml
deprecation_categories:
  obsolete_scripts:
    description: "Scripts that are no longer needed"
    criteria:
      - "Functionality moved to CLI"
      - "One-time task completed"
      - "Superseded by newer implementation"

  redundant_scripts:
    description: "Scripts that duplicate existing functionality"
    criteria:
      - "CLI command does same thing"
      - "Library function does same thing"
      - "Multiple scripts do same thing"

  broken_scripts:
    description: "Scripts that no longer work"
    criteria:
      - "Import errors"
      - "API changes broke functionality"
      - "Dependencies removed"

  obsolete_config:
    description: "Configuration settings no longer needed"
    criteria:
      - "Tool no longer used"
      - "Setting deprecated by tool"
      - "Redundant with pyproject.toml"
```

### Output Format
```yaml
# DEPRECATION_CANDIDATES.yaml
deprecation_candidates:
  generated_at: "2025-12-11T00:00:00Z"

  summary:
    scripts_to_deprecate: X
    config_settings_to_remove: X
    config_files_to_remove: X

  scripts:
    - path: scripts/example_obsolete.py
      category: obsolete | redundant | broken
      reason: string
      replacement: string | null
      safe_to_delete: true | false
      deletion_blockers: [list]

  config_settings:
    - file: pyproject.toml
      setting: "tool.old_tool"
      reason: "Tool no longer used"
      safe_to_remove: true | false

  config_files:
    - file: .old_config
      reason: "Superseded by pyproject.toml"
      safe_to_delete: true | false

  deprecation_plan:
    immediate:
      description: "Safe to remove now"
      items: [list]
    after_verification:
      description: "Remove after confirming no usage"
      items: [list]
      verification_steps: [list]
    deferred:
      description: "Keep for now, revisit later"
      items: [list]
      revisit_date: date
```

### Acceptance Criteria
- [ ] All deprecation candidates identified
- [ ] Reasons documented
- [ ] Safety assessment completed
- [ ] Deprecation plan created

---

## Task 10: Generate Scripts Audit Summary

**Type:** Documentation
**Complexity:** Medium
**Estimated Tokens:** 10,000
**Duration:** 0.5 days

### Objective
Consolidate all script and configuration audits into a comprehensive summary.

### Report Structure
```markdown
# Scripts & Project Config Audit Summary

## Executive Summary
- Scripts audited: 4
- Config files audited: 7
- CLI migration candidates: X
- Deprecation candidates: X
- Average quality score: X/100

## Scripts Overview

### Script Inventory
| Script | Size | Purpose | Decision | Priority |
|--------|------|---------|----------|----------|
| consolidate_dogfooding_track.py | 25KB | Consolidate track | Migrate | High |
| create_dogfooding_track.py | 25KB | Create track | Migrate | Medium |
| execute_migration.py | 5KB | Run migrations | Migrate | High |
| run_migration_standalone.py | 5KB | Standalone migrations | Deprecate | - |

### Quality Scores
| Script | Quality | Code | Docs | Integration |
|--------|---------|------|------|-------------|
| ... | X | X | X | X |

## Configuration Files Overview

### Config Inventory
| File | Purpose | Quality | Issues |
|------|---------|---------|--------|
| pyproject.toml | Project config | A | None |
| pytest.ini | Test config | B | Minor |
| ... | | | |

### Cross-File Analysis
- Python version consistency: Yes/No
- Redundant settings: [list]
- Missing configurations: [list]

## CLI Migration Plan

### Phase 1: High Priority
| Script | New Command | Effort |
|--------|-------------|--------|
| ... | `vibey roadmap ...` | X hours |

### Phase 2: Medium Priority
| Script | New Command | Effort |
|--------|-------------|--------|
| ... | | |

## Deprecation Plan

### Immediate Removal
- [items safe to remove now]

### After Verification
- [items to verify before removal]

## Recommendations

### Immediate Actions
1. [action 1]
2. [action 2]

### Short-term Improvements
1. [improvement 1]
2. [improvement 2]

### Long-term Strategy
1. [strategy 1]
2. [strategy 2]

## Appendix
- Individual script audits
- Configuration file details
- Migration implementation notes
```

### Acceptance Criteria
- [ ] All audits synthesized
- [ ] Migration plan complete
- [ ] Deprecation plan complete
- [ ] Recommendations actionable

---

## Sprint Dependencies

```
Task 1 (Criteria) ──┬──> Task 2 (Inventory)
                    └──> Task 3 (Config Audit)

Task 2 (Inventory) ─┬──> Task 4 (Consolidate)
                    ├──> Task 5 (Create)
                    ├──> Task 6 (Execute)
                    └──> Task 7 (Standalone)

Task 4-7 ───────────┬──> Task 8 (CLI Candidates)
                    └──> Task 9 (Deprecation)

Task 3, 8, 9 ───────────> Task 10 (Summary)
```

## Sprint Success Criteria

1. **Completeness**
   - [ ] All scripts audited
   - [ ] All config files audited
   - [ ] Migration candidates identified
   - [ ] Deprecation candidates identified

2. **Accuracy**
   - [ ] Script purposes correctly identified
   - [ ] Config settings accurately assessed
   - [ ] Quality scores objective

3. **Actionability**
   - [ ] Clear migration plan
   - [ ] Clear deprecation plan
   - [ ] Effort estimates realistic

4. **Quality**
   - [ ] Consistent audit criteria
   - [ ] Useful recommendations
   - [ ] Decision rationale documented

---

## Output Directory Structure

```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-5/
├── SPRINT_PLAN.md                        # This document
├── SCRIPTS_AUDIT_CRITERIA.md             # Task 1 output
├── SCRIPTS_INVENTORY.yaml                # Task 2 output
├── AUDIT_PROJECT_CONFIG.yaml             # Task 3 output
├── AUDIT_CONSOLIDATE_DOGFOODING.yaml     # Task 4 output
├── AUDIT_CREATE_DOGFOODING.yaml          # Task 5 output
├── AUDIT_EXECUTE_MIGRATION.yaml          # Task 6 output
├── AUDIT_RUN_MIGRATION_STANDALONE.yaml   # Task 7 output
├── CLI_MIGRATION_CANDIDATES.yaml         # Task 8 output
├── DEPRECATION_CANDIDATES.yaml           # Task 9 output
├── SCRIPTS_AUDIT_SUMMARY.md              # Task 10 output
└── SPRINT_COMPLETION_REPORT.md           # Final summary
```
