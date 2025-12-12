# Sprint 1.6: Database Artifact Audit
## Comprehensive Task Plan

**Sprint ID:** Phase 1.6
**Track:** User Journey Audit & Documentation Coverage
**Duration:** 1.5 weeks
**Tasks:** 11
**Total Estimated Tokens:** 110,000

---

## Sprint Overview

This sprint audits the SQLite database schema that tracks roadmap artifacts and their relationships. The goal is to understand what entities are tracked, how they relate to each other, identify gaps between the file-based audits (Sprints 1.1-1.5) and database tracking capabilities, and design improvements to enhance artifact tracking for comprehensive coverage.

### Sprint Goals
1. Document the complete database schema
2. Inventory all artifact tables and their purposes
3. Analyze the relationship model between entities
4. Map file audit outputs to database artifact types
5. Identify missing artifact types and relationships
6. Assess metadata completeness for tracked entities
7. Audit query capabilities via views
8. Design improvements for comprehensive artifact tracking
9. Create cross-reference between audits and database

### Prerequisites
- Sprint 1.1 outputs: `FILE_REGISTRY.yaml`, classification outputs
- Sprint 1.2-1.5 outputs: All audit summaries

### Key Deliverables
- `DATABASE_SCHEMA_DOCUMENTATION.md` - Complete schema documentation
- `ARTIFACT_TABLES_INVENTORY.yaml` - Table-by-table analysis
- `RELATIONSHIP_MODEL_ANALYSIS.yaml` - Entity relationship analysis
- `FILE_AUDIT_TO_ARTIFACT_MAPPING.yaml` - Mapping between file audits and DB
- `MISSING_ARTIFACT_TYPES.yaml` - Gaps in artifact tracking
- `MISSING_RELATIONSHIP_TYPES.yaml` - Gaps in relationship tracking
- `METADATA_COMPLETENESS_ASSESSMENT.yaml` - Metadata field analysis
- `QUERY_CAPABILITIES_AUDIT.yaml` - Views and query analysis
- `ARTIFACT_TRACKING_IMPROVEMENTS.yaml` - Design for enhancements
- `AUDIT_TO_DATABASE_CROSSREF.yaml` - Cross-reference mapping
- `DATABASE_ARTIFACT_AUDIT_SUMMARY.md` - Consolidated summary

---

## Task 1: Document Current Database Schema

**Type:** Documentation
**Complexity:** Medium
**Estimated Tokens:** 15,000
**Duration:** 1 day

### Objective
Create comprehensive documentation of the current database schema including all tables, columns, constraints, triggers, and views.

### Current Database Structure

#### Tables (27 total)
```
Core Entities:
├── roadmaps              # Root container
├── tracks                # Work streams
├── sprints               # Time-boxed iterations
└── tasks                 # Individual work items

Supporting Entities:
├── artifacts             # Generic artifact storage
├── commits               # Git commit references
├── deliverables          # Sprint/task outputs
├── quality_gates         # Quality checkpoints
├── development_gates     # Development checkpoints
├── standards             # Coding/doc standards
├── strategic_value       # Strategic value items
├── assigned_agents       # Agent assignments
├── external_dependencies # External blockers

Relationship Tables:
├── entity_blocks         # A blocks B relationships
├── entity_blocked_by     # A is blocked by B relationships
├── entity_depends_on     # Dependency tracking
├── entity_commits        # Entity-to-commit mapping
├── entity_deliverables   # Entity-to-deliverable mapping

Summary/Cache Tables:
├── task_summaries        # Denormalized task data
├── sprint_summaries      # Denormalized sprint data
├── track_summaries       # Denormalized track data

Operational Tables:
├── activity_log          # Event log
├── audit_trail           # Audit history
├── sync_conflicts        # YAML/DB sync issues
├── yaml_checksums        # File change detection
├── database_state        # DB metadata
└── version_history       # Schema versions
```

#### Views (21 total)
```
Progress Views:
├── v_roadmap_progress
├── v_track_progress
├── v_sprint_progress

Summary Views:
├── v_track_summary_data
├── v_sprint_summary_data
├── v_task_summary_data

Aggregation Views:
├── v_track_commits
├── v_track_deliverables
├── v_track_assigned_agents
├── v_track_sprint_summaries
├── v_sprint_commits
├── v_sprint_deliverables
├── v_sprint_assigned_agents
├── v_sprint_estimated_duration

Status Views:
├── v_blocked_entities
├── v_unblocked_tasks
├── v_dependency_chain
├── v_failing_quality_gates
├── v_quality_gate_summary

Activity Views:
├── v_recent_activity
└── v_velocity_metrics
```

### Schema Documentation Template

```yaml
table_documentation:
  name: string
  purpose: string
  category: core | supporting | relationship | summary | operational

  columns:
    - name: string
      type: TEXT | INTEGER | REAL | BLOB
      constraints:
        primary_key: true | false
        not_null: true | false
        unique: true | false
        foreign_key: string | null  # e.g., "tracks(id)"
        check: string | null  # e.g., "status IN (...)"
        default: value | null
      description: string
      json_structure: string | null  # For JSON columns

  indexes:
    - name: string
      columns: [list]
      unique: true | false

  triggers:
    - name: string
      event: INSERT | UPDATE | DELETE
      timing: BEFORE | AFTER
      purpose: string

  relationships:
    parent_of: [list of tables]
    child_of: [list of tables]
    many_to_many_with: [list of tables via junction]
```

### Output Format
```markdown
# DATABASE_SCHEMA_DOCUMENTATION.md

## Overview
- Database: SQLite 3.x
- Tables: 27
- Views: 21
- Triggers: X

## Entity Relationship Diagram
[ASCII or description of ERD]

## Core Entity Tables

### roadmaps
**Purpose:** Root container for all roadmap data

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PK | ULID identifier |
| name | TEXT | NOT NULL | Roadmap name |
| version | TEXT | NOT NULL | Semantic version |
| status | TEXT | CHECK(...) | Lifecycle status |
| ... | | | |

**Relationships:**
- Parent of: tracks

**Triggers:**
- trg_activity_roadmap_created: Logs creation events

---

### tracks
...

[Continue for all 27 tables]

## Views

### v_roadmap_progress
**Purpose:** Aggregate progress across all tracks

**Query Logic:**
```sql
[The actual view definition]
```

**Use Cases:**
- Dashboard progress display
- Completion percentage calculation

[Continue for all 21 views]

## Triggers

### Blocking System Triggers
- trg_task_blocked_by_insert
- trg_task_blocked_by_delete
...

### Auto-Status Triggers
- trg_auto_start_sprint
- trg_auto_start_track
...

### Activity Logging Triggers
- trg_activity_task_status
- trg_activity_sprint_status
...

### Summary Maintenance Triggers
- trg_task_summary_insert
- trg_task_summary_update
...

### Constraint Enforcement Triggers
- trg_prevent_complete_blocked_task
- trg_prevent_complete_sprint_incomplete
...
```

### Acceptance Criteria
- [ ] All 27 tables documented
- [ ] All 21 views documented
- [ ] All triggers documented
- [ ] Column-level detail for each table
- [ ] Relationships mapped

---

## Task 2: Inventory Existing Artifact Tables

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 12,000
**Duration:** 1 day

### Objective
Create a detailed inventory of all tables that store artifact-related data, analyzing their structure, usage, and completeness.

### Artifact Table Categories

#### Core Artifact Tables
```yaml
core_artifacts:
  - table: roadmaps
    artifact_type: roadmap
    description: "Root planning container"
    record_count: X
    fields_for_artifacts:
      - id, name, version, status, metadata

  - table: tracks
    artifact_type: track
    description: "Work stream container"
    record_count: X
    fields_for_artifacts:
      - id, name, status, priority, dependencies_json, strategic_value_json

  - table: sprints
    artifact_type: sprint
    description: "Time-boxed iteration"
    record_count: X
    fields_for_artifacts:
      - id, name, status, plan_file, deliverables_json, quality_gates_json

  - table: tasks
    artifact_type: task
    description: "Individual work item"
    record_count: X
    fields_for_artifacts:
      - id, title, description, task_type, commits_json, deliverables_json
```

#### Supporting Artifact Tables
```yaml
supporting_artifacts:
  - table: artifacts
    artifact_type: generic_artifact
    description: "Generic artifact storage"
    record_count: X
    schema_analysis:
      columns: [list]
      usage: "How is this table actually used?"

  - table: commits
    artifact_type: git_commit
    description: "Git commit references"
    record_count: X

  - table: deliverables
    artifact_type: deliverable
    description: "Output artifacts from work"
    record_count: X

  - table: quality_gates
    artifact_type: quality_gate
    description: "Quality checkpoints"
    record_count: X

  - table: standards
    artifact_type: standard
    description: "Coding/documentation standards"
    record_count: X
```

### Per-Table Analysis Template
```yaml
table_analysis:
  name: tasks
  category: core_artifact

  structure:
    total_columns: X
    artifact_columns: X
    metadata_columns: X
    json_columns: X

  data_analysis:
    total_records: X
    records_with_metadata: X
    records_with_commits: X
    records_with_deliverables: X

  json_field_analysis:
    commits_json:
      records_with_data: X
      sample_structure: {...}
      schema_consistency: consistent | inconsistent
    deliverables_json:
      records_with_data: X
      sample_structure: {...}
      schema_consistency: consistent | inconsistent

  completeness:
    required_fields_populated: X%
    optional_fields_populated: X%
    metadata_richness: high | medium | low

  issues:
    - "X records missing expected metadata"
    - "Inconsistent JSON structure in Y"
```

### Output Format
```yaml
# ARTIFACT_TABLES_INVENTORY.yaml
inventory:
  generated_at: "2025-12-11T00:00:00Z"
  database_path: .vibey/roadmap.db

  summary:
    total_tables: 27
    artifact_tables: X
    relationship_tables: X
    operational_tables: X
    total_records: X

  core_artifacts:
    roadmaps:
      # ... full analysis
    tracks:
      # ... full analysis
    sprints:
      # ... full analysis
    tasks:
      # ... full analysis

  supporting_artifacts:
    artifacts:
      # ... full analysis
    commits:
      # ... full analysis
    # ... etc

  relationship_tables:
    entity_blocks:
      # ... full analysis
    # ... etc

  operational_tables:
    activity_log:
      # ... full analysis
    # ... etc

  cross_table_analysis:
    orphan_records: [list of records with broken foreign keys]
    unused_tables: [tables with 0 records]
    heavily_used_tables: [tables with most records]
```

### Acceptance Criteria
- [ ] All artifact-related tables inventoried
- [ ] Record counts captured
- [ ] JSON field structures analyzed
- [ ] Completeness assessed
- [ ] Issues identified

---

## Task 3: Analyze Artifact Relationship Model

**Type:** Research
**Complexity:** Complex
**Estimated Tokens:** 15,000
**Duration:** 1 day

### Objective
Analyze how artifacts relate to each other through the database relationship model, including foreign keys, junction tables, and JSON relationships.

### Relationship Categories

#### Hierarchical Relationships
```yaml
hierarchical:
  - parent: roadmaps
    child: tracks
    cardinality: one-to-many
    enforced_by: foreign_key
    cascade_delete: true

  - parent: tracks
    child: sprints
    cardinality: one-to-many
    enforced_by: foreign_key
    cascade_delete: true

  - parent: sprints
    child: tasks
    cardinality: one-to-many
    enforced_by: foreign_key
    cascade_delete: true
```

#### Blocking Relationships
```yaml
blocking:
  - table: entity_blocks
    description: "A blocks B"
    polymorphic: true
    entity_types: [track, sprint, task]
    trigger_maintained: true

  - table: entity_blocked_by
    description: "A is blocked by B"
    polymorphic: true
    entity_types: [track, sprint, task]
    trigger_maintained: true
```

#### Dependency Relationships
```yaml
dependencies:
  - table: entity_depends_on
    description: "A depends on B"
    polymorphic: true
    status_tracking: true

  - table: external_dependencies
    description: "Entity depends on external resource"
    polymorphic: true
    resolution_tracking: true
```

#### Association Relationships
```yaml
associations:
  - table: entity_commits
    connects: [entities, commits]
    cardinality: many-to-many

  - table: entity_deliverables
    connects: [entities, deliverables]
    cardinality: many-to-many

  - table: assigned_agents
    connects: [entities, agents]
    cardinality: many-to-many
```

### Relationship Analysis Template
```yaml
relationship_analysis:
  name: entity_blocks
  type: blocking

  structure:
    blocker_types: [track, sprint, task]
    blocked_types: [track, sprint, task]
    additional_fields: [reason]

  usage_analysis:
    total_relationships: X
    by_blocker_type:
      track: X
      sprint: X
      task: X
    by_blocked_type:
      track: X
      sprint: X
      task: X

  integrity:
    orphan_blockers: X  # References to deleted entities
    orphan_blocked: X
    circular_references: X

  trigger_support:
    auto_update_blocked_flag: true
    auto_clear_on_completion: true

  query_support:
    views_using: [v_blocked_entities, v_dependency_chain]
```

### Output Format
```yaml
# RELATIONSHIP_MODEL_ANALYSIS.yaml
analysis:
  generated_at: "2025-12-11T00:00:00Z"

  summary:
    relationship_tables: X
    total_relationships: X
    hierarchical_relationships: X
    blocking_relationships: X
    dependency_relationships: X
    association_relationships: X

  hierarchical:
    # ... full analysis per relationship

  blocking:
    entity_blocks:
      # ... full analysis
    entity_blocked_by:
      # ... full analysis

  dependencies:
    entity_depends_on:
      # ... full analysis
    external_dependencies:
      # ... full analysis

  associations:
    entity_commits:
      # ... full analysis
    entity_deliverables:
      # ... full analysis
    assigned_agents:
      # ... full analysis

  relationship_graph:
    nodes: [list of entity types]
    edges:
      - from: roadmap
        to: track
        type: contains
        cardinality: 1:N
      # ... all edges

  integrity_issues:
    orphan_records: [list]
    circular_dependencies: [list]
    constraint_violations: [list]
```

### Acceptance Criteria
- [ ] All relationship types identified
- [ ] Cardinalities documented
- [ ] Integrity analysis completed
- [ ] Trigger support documented
- [ ] Relationship graph created

---

## Task 4: Map File Audit Outputs to Artifact Types

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 10,000
**Duration:** 0.5 days

### Objective
Create a mapping between the file audit outputs from Sprints 1.1-1.5 and the artifact types tracked in the database.

### File Audit Outputs (Sprints 1.1-1.5)

```yaml
sprint_1_1_outputs:
  - FILE_REGISTRY.yaml
  - VIBEY_FILE_CLASSIFICATION.yaml
  - DOCS_FILE_CLASSIFICATION.yaml
  - TESTS_FILE_CLASSIFICATION.yaml
  - FILE_DEPENDENCY_GRAPH.yaml

sprint_1_2_outputs:
  - AUDIT_ROOT_FILES.yaml
  - AUDIT_CLI_MODULE.yaml
  - AUDIT_OPERATIONS_MODULE.yaml
  - AUDIT_ROADMAP_MODULE.yaml
  - AUDIT_MCP_ADAPTERS_MODULE.yaml
  - AUDIT_COMMON_MODULE.yaml
  - AUDIT_CONFIG_MODULE.yaml
  - AUDIT_CONTENT_MODULE.yaml
  - AUDIT_PLATFORM_MODULE.yaml
  - OBSOLETE_CODE_REPORT.yaml
  - CORE_LIBRARY_AUDIT_SUMMARY.md

sprint_1_3_outputs:
  - AUDIT_DOCS_ROOT.yaml
  - AUDIT_GETTING_STARTED.yaml
  - AUDIT_GUIDES.yaml
  - AUDIT_REFERENCE.yaml
  - AUDIT_DEVELOPMENT.yaml
  - AUDIT_EXAMPLES.yaml
  - AUDIT_OPERATIONS.yaml
  - AUDIT_ROADMAP_DOCS.yaml
  - AUDIT_SPRINTS.yaml
  - AUDIT_TESTING.yaml
  - AUDIT_VALIDATION.yaml
  - AUDIT_ROOT_DOCS.yaml
  - DOCUMENTATION_AUDIT_SUMMARY.md

sprint_1_4_outputs:
  - COVERAGE_ANALYSIS_REPORT.yaml
  - AUDIT_TESTS_*.yaml (14 files)
  - COVERAGE_GAP_ANALYSIS.yaml
  - TEST_SUITE_AUDIT_SUMMARY.md

sprint_1_5_outputs:
  - SCRIPTS_INVENTORY.yaml
  - AUDIT_PROJECT_CONFIG.yaml
  - AUDIT_*.yaml (4 script audits)
  - CLI_MIGRATION_CANDIDATES.yaml
  - DEPRECATION_CANDIDATES.yaml
  - SCRIPTS_AUDIT_SUMMARY.md
```

### Mapping Template
```yaml
mapping:
  audit_output: FILE_REGISTRY.yaml
  audit_sprint: 1.1

  database_mapping:
    direct_artifact_type: null  # No direct mapping
    indirect_mappings:
      - artifact_type: file_classification
        table: artifacts (proposed)
        notes: "File registry data not currently stored in DB"

    storage_gap:
      identified: true
      description: "File classifications not persisted to database"
      impact: "Cannot query file data via SQL"
      recommendation: "Add file_classifications table"
```

### Output Format
```yaml
# FILE_AUDIT_TO_ARTIFACT_MAPPING.yaml
mapping:
  generated_at: "2025-12-11T00:00:00Z"

  summary:
    total_audit_outputs: X
    mapped_to_existing_tables: X
    requires_new_tables: X
    no_db_storage_needed: X

  mappings:
    - audit_output: FILE_REGISTRY.yaml
      sprint: 1.1
      current_db_support: none | partial | full
      recommended_table: file_registry
      recommended_action: create_table | use_existing | no_action

    - audit_output: AUDIT_CLI_MODULE.yaml
      sprint: 1.2
      current_db_support: partial
      existing_table: artifacts
      gaps:
        - "No quality_score column"
        - "No audit_date column"
      recommended_action: extend_schema

    # ... all audit outputs

  gap_summary:
    audit_data_not_in_db:
      - category: "File Classifications"
        audit_files: [list]
        impact: "Cannot query file relationships"
      - category: "Code Quality Scores"
        audit_files: [list]
        impact: "Cannot track quality trends"

    partially_supported:
      - category: "Test Coverage"
        current_support: "Basic metrics in metadata"
        gaps: "No detailed line coverage storage"
```

### Acceptance Criteria
- [ ] All audit outputs mapped
- [ ] Current DB support assessed
- [ ] Gaps identified
- [ ] Recommendations generated

---

## Task 5: Identify Missing Artifact Types

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 10,000
**Duration:** 0.5 days

### Objective
Based on the file audits and mapping analysis, identify artifact types that should be tracked in the database but currently are not.

### Missing Artifact Type Categories

```yaml
missing_categories:
  file_artifacts:
    description: "Source files, docs, tests not tracked as artifacts"
    examples:
      - source_file
      - documentation_file
      - test_file
      - config_file
    current_state: "Only tracked in YAML audit outputs"
    impact: "Cannot query file-level data"

  quality_artifacts:
    description: "Quality metrics not stored as first-class artifacts"
    examples:
      - code_quality_score
      - documentation_coverage
      - test_coverage_metric
    current_state: "Stored in JSON metadata if at all"
    impact: "Cannot track quality trends over time"

  audit_artifacts:
    description: "Audit results not tracked"
    examples:
      - file_audit_result
      - module_audit_result
      - coverage_analysis
    current_state: "Stored as YAML files only"
    impact: "Cannot query audit history"
```

### Missing Artifact Analysis Template
```yaml
missing_artifact:
  name: source_file
  category: file_artifacts

  definition:
    description: "A source code file in the repository"
    key_attributes:
      - path
      - module
      - category
      - purpose
      - lines
      - last_modified

  current_tracking:
    method: "YAML files from Sprint 1.1"
    location: "FILE_REGISTRY.yaml"
    queryable: false
    persisted: false

  proposed_schema:
    table_name: source_files
    columns:
      - name: id
        type: TEXT
        constraints: PRIMARY KEY
      - name: path
        type: TEXT
        constraints: NOT NULL UNIQUE
      - name: category
        type: TEXT
      - name: subcategory
        type: TEXT
      - name: purpose
        type: TEXT
      - name: module
        type: TEXT
      - name: lines
        type: INTEGER
      - name: size_bytes
        type: INTEGER
      - name: last_modified
        type: TEXT
      - name: quality_score
        type: INTEGER
      - name: test_coverage
        type: REAL
      - name: doc_coverage
        type: REAL
      - name: metadata
        type: TEXT  # JSON

  relationships:
    - to: test_files
      type: tested_by
      junction_table: file_test_coverage
    - to: documentation_files
      type: documented_by
      junction_table: file_documentation

  value_proposition:
    queries_enabled:
      - "Find all untested source files"
      - "Track quality score trends"
      - "Identify documentation gaps"
    integrations:
      - "Link commits to files changed"
      - "Link tasks to files modified"
```

### Output Format
```yaml
# MISSING_ARTIFACT_TYPES.yaml
analysis:
  generated_at: "2025-12-11T00:00:00Z"

  summary:
    missing_artifact_types: X
    high_priority: X
    medium_priority: X
    low_priority: X

  missing_artifacts:
    high_priority:
      - name: source_file
        # ... full analysis
      - name: audit_result
        # ... full analysis

    medium_priority:
      - name: quality_metric
        # ... full analysis
      - name: coverage_data
        # ... full analysis

    low_priority:
      - name: script_artifact
        # ... full analysis

  implementation_roadmap:
    phase_1:
      description: "Core file tracking"
      artifacts: [source_file, test_file, doc_file]
      effort: "X hours"
      tables_to_create: X
    phase_2:
      description: "Quality tracking"
      artifacts: [quality_metric, coverage_data]
      effort: "X hours"
    phase_3:
      description: "Audit persistence"
      artifacts: [audit_result]
      effort: "X hours"
```

### Acceptance Criteria
- [ ] All missing artifact types identified
- [ ] Proposed schemas designed
- [ ] Value propositions documented
- [ ] Implementation prioritized

---

## Task 6: Identify Missing Relationship Types

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 8,000
**Duration:** 0.5 days

### Objective
Identify relationship types between artifacts that are not currently tracked in the database.

### Missing Relationship Categories

```yaml
missing_relationships:
  file_relationships:
    - name: file_imports
      description: "Source file imports another file"
      from: source_file
      to: source_file
      cardinality: many-to-many
      currently_tracked: false
      data_source: "FILE_DEPENDENCY_GRAPH.yaml"

    - name: file_tested_by
      description: "Source file tested by test file"
      from: source_file
      to: test_file
      cardinality: many-to-many
      currently_tracked: false

    - name: file_documented_by
      description: "Source file documented in doc file"
      from: source_file
      to: documentation_file
      cardinality: many-to-many
      currently_tracked: false

  task_file_relationships:
    - name: task_modifies_file
      description: "Task modifies source file(s)"
      from: task
      to: source_file
      cardinality: many-to-many
      currently_tracked: false
      notes: "Could be inferred from commits"

    - name: task_creates_file
      description: "Task creates new file(s)"
      from: task
      to: source_file
      cardinality: many-to-many
      currently_tracked: false

  audit_relationships:
    - name: audit_covers_file
      description: "Audit result covers file"
      from: audit_result
      to: source_file
      cardinality: one-to-many
      currently_tracked: false

    - name: audit_identifies_issue
      description: "Audit identifies issue in file"
      from: audit_result
      to: audit_finding
      cardinality: one-to-many
      currently_tracked: false
```

### Output Format
```yaml
# MISSING_RELATIONSHIP_TYPES.yaml
analysis:
  generated_at: "2025-12-11T00:00:00Z"

  summary:
    missing_relationship_types: X
    would_require_new_tables: X
    would_extend_existing: X

  missing_relationships:
    file_relationships:
      - name: file_imports
        # ... full analysis with proposed junction table
      # ... etc

    task_file_relationships:
      - name: task_modifies_file
        # ... full analysis
      # ... etc

    audit_relationships:
      - name: audit_covers_file
        # ... full analysis
      # ... etc

  proposed_junction_tables:
    - name: file_imports
      columns: [source_file_id, imported_file_id, import_type]
    - name: file_test_coverage
      columns: [source_file_id, test_file_id, coverage_percent]
    # ... etc

  implementation_priority:
    high: [file_imports, file_tested_by]
    medium: [task_modifies_file]
    low: [audit_relationships]
```

### Acceptance Criteria
- [ ] All missing relationship types identified
- [ ] Junction table designs proposed
- [ ] Implementation prioritized

---

## Task 7: Assess Artifact Metadata Completeness

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 10,000
**Duration:** 0.5 days

### Objective
Assess the completeness of metadata fields across all artifact tables, identifying underutilized fields and missing metadata capabilities.

### Metadata Analysis Framework

```yaml
metadata_assessment:
  table: tasks

  standard_columns:
    - column: id
      populated: 100%
      quality: good
    - column: title
      populated: 100%
      quality: good
    - column: description
      populated: 45%
      quality: sparse
      issue: "Many tasks lack descriptions"

  json_metadata_columns:
    - column: metadata
      populated: 85%
      common_keys:
        - sequence: 100%
        - created_by: 20%
        - last_updated: 95%
      missing_useful_keys:
        - estimated_hours
        - actual_hours
        - complexity_notes

    - column: commits_json
      populated: 15%
      issue: "Most tasks don't track commits"
      recommendation: "Improve commit tracking"

    - column: deliverables_json
      populated: 25%
      common_structure: {...}
      consistency: low

  completeness_score:
    required_fields: 95%
    optional_fields: 40%
    metadata_richness: medium
    overall: 65%
```

### Output Format
```yaml
# METADATA_COMPLETENESS_ASSESSMENT.yaml
assessment:
  generated_at: "2025-12-11T00:00:00Z"

  summary:
    tables_assessed: X
    average_completeness: X%
    tables_with_issues: X

  by_table:
    roadmaps:
      completeness_score: X%
      issues: [list]
      recommendations: [list]

    tracks:
      completeness_score: X%
      issues: [list]
      recommendations: [list]

    sprints:
      completeness_score: X%
      json_field_usage:
        deliverables_json: X%
        quality_gates_json: X%
        # ... etc
      issues: [list]
      recommendations: [list]

    tasks:
      completeness_score: X%
      json_field_usage:
        commits_json: X%
        deliverables_json: X%
        # ... etc
      issues: [list]
      recommendations: [list]

  cross_table_patterns:
    underutilized_fields:
      - field: strategic_value_json
        tables: [tracks]
        usage: 10%
        recommendation: "Remove or enforce usage"

    inconsistent_json_schemas:
      - field: metadata
        tables: [tasks, sprints, tracks]
        issue: "Different keys used inconsistently"
        recommendation: "Standardize metadata schema"

  improvement_recommendations:
    schema_changes:
      - "Add NOT NULL to description columns"
      - "Define JSON schema for metadata fields"
    data_quality:
      - "Backfill missing descriptions"
      - "Standardize metadata keys"
```

### Acceptance Criteria
- [ ] All tables assessed for completeness
- [ ] JSON field usage analyzed
- [ ] Patterns identified
- [ ] Recommendations generated

---

## Task 8: Audit Artifact Query Capabilities

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 10,000
**Duration:** 0.5 days

### Objective
Audit the query capabilities provided by existing views and identify missing query patterns.

### Current Views Analysis

```yaml
view_analysis:
  name: v_track_progress
  category: progress

  purpose: "Calculate track completion progress"

  query_capabilities:
    - "Get completion percentage for track"
    - "Count completed vs total sprints"
    - "Count completed vs total tasks"

  columns_exposed:
    - track_id
    - track_name
    - total_sprints
    - completed_sprints
    - total_tasks
    - completed_tasks
    - completion_percent

  usage_frequency: high
  performance: good

  limitations:
    - "Does not include blocked status"
    - "Does not filter by date range"
    - "Does not include velocity"
```

### Missing Query Patterns

```yaml
missing_queries:
  file_queries:
    - name: "Find untested files"
      description: "List source files without corresponding tests"
      current_support: none
      required_tables: [source_files, test_files, file_test_coverage]
      proposed_view: v_untested_files

    - name: "File quality trends"
      description: "Track quality scores over time"
      current_support: none
      required_tables: [source_files, audit_history]
      proposed_view: v_file_quality_trends

  audit_queries:
    - name: "Audit coverage"
      description: "What percentage of files have been audited?"
      current_support: none
      proposed_view: v_audit_coverage

  cross_reference_queries:
    - name: "Task to file mapping"
      description: "Which files were modified by which tasks?"
      current_support: none
      notes: "Could derive from commit data"
```

### Output Format
```yaml
# QUERY_CAPABILITIES_AUDIT.yaml
audit:
  generated_at: "2025-12-11T00:00:00Z"

  summary:
    total_views: 21
    well_designed: X
    needs_improvement: X
    missing_capabilities: X

  existing_views:
    progress_views:
      - name: v_roadmap_progress
        # ... full analysis
      - name: v_track_progress
        # ... full analysis
      - name: v_sprint_progress
        # ... full analysis

    summary_views:
      # ... full analysis for each

    status_views:
      # ... full analysis for each

    activity_views:
      # ... full analysis for each

  missing_query_capabilities:
    high_priority:
      - query: "Untested files"
        proposed_view: v_untested_files
        blocked_by: "Missing source_files table"

    medium_priority:
      - query: "Quality trends"
        proposed_view: v_quality_trends

    low_priority:
      - query: "Audit history"

  view_improvement_recommendations:
    - view: v_track_progress
      improvement: "Add blocked_tasks count"
    - view: v_sprint_progress
      improvement: "Add velocity metrics"
```

### Acceptance Criteria
- [ ] All 21 views analyzed
- [ ] Missing query patterns identified
- [ ] Improvement recommendations generated

---

## Task 9: Design Artifact Tracking Improvements

**Type:** Design
**Complexity:** Complex
**Estimated Tokens:** 15,000
**Duration:** 1 day

### Objective
Based on all analysis, design improvements to the database schema for comprehensive artifact tracking.

### Improvement Categories

#### New Tables Required
```yaml
new_tables:
  - name: source_files
    purpose: "Track source code files"
    priority: high
    columns:
      - id: TEXT PRIMARY KEY
      - path: TEXT NOT NULL UNIQUE
      - category: TEXT
      - subcategory: TEXT
      - module: TEXT
      - purpose: TEXT
      - lines: INTEGER
      - size_bytes: INTEGER
      - last_modified: TEXT
      - quality_score: INTEGER
      - metadata: TEXT
    indexes:
      - [category]
      - [module]
    triggers:
      - activity logging

  - name: file_dependencies
    purpose: "Track file import relationships"
    priority: high
    columns:
      - id: INTEGER PRIMARY KEY
      - source_file_id: TEXT REFERENCES source_files(id)
      - target_file_id: TEXT REFERENCES source_files(id)
      - dependency_type: TEXT  # import, inherit, reference
    indexes:
      - [source_file_id]
      - [target_file_id]

  - name: audit_results
    purpose: "Persist audit findings"
    priority: medium
    columns:
      - id: TEXT PRIMARY KEY
      - audit_type: TEXT  # code, docs, tests, config
      - target_path: TEXT
      - audit_date: TEXT
      - quality_score: INTEGER
      - findings_json: TEXT
      - recommendations_json: TEXT
      - metadata: TEXT
```

#### Schema Modifications
```yaml
schema_modifications:
  - table: tasks
    modification: add_column
    column:
      name: files_modified_json
      type: TEXT
      purpose: "Track files modified by this task"

  - table: commits
    modification: add_column
    column:
      name: files_changed_json
      type: TEXT
      purpose: "List of files in commit"
```

#### New Views Required
```yaml
new_views:
  - name: v_untested_files
    purpose: "Find source files without test coverage"
    query: |
      SELECT sf.*
      FROM source_files sf
      LEFT JOIN file_test_coverage ftc ON sf.id = ftc.source_file_id
      WHERE ftc.id IS NULL
        AND sf.category = 'source'

  - name: v_file_quality_summary
    purpose: "Aggregate file quality metrics"
    query: |
      SELECT
        category,
        COUNT(*) as file_count,
        AVG(quality_score) as avg_quality,
        SUM(CASE WHEN quality_score < 60 THEN 1 ELSE 0 END) as failing_count
      FROM source_files
      GROUP BY category
```

### Output Format
```yaml
# ARTIFACT_TRACKING_IMPROVEMENTS.yaml
design:
  generated_at: "2025-12-11T00:00:00Z"

  summary:
    new_tables: X
    modified_tables: X
    new_views: X
    new_triggers: X
    estimated_effort: "X hours"

  new_tables:
    - name: source_files
      # ... full schema
    - name: file_dependencies
      # ... full schema
    - name: audit_results
      # ... full schema
    # ... etc

  schema_modifications:
    - table: tasks
      # ... modification details
    # ... etc

  new_views:
    - name: v_untested_files
      # ... full definition
    # ... etc

  new_triggers:
    - name: trg_file_activity
      # ... trigger definition
    # ... etc

  migration_plan:
    phase_1:
      description: "Core file tracking"
      changes: [list]
      effort: "X hours"
      risk: low
    phase_2:
      description: "Audit persistence"
      changes: [list]
      effort: "X hours"
      risk: low
    phase_3:
      description: "Advanced relationships"
      changes: [list]
      effort: "X hours"
      risk: medium

  backward_compatibility:
    breaking_changes: [list or none]
    migration_required: true | false
    rollback_plan: string
```

### Acceptance Criteria
- [ ] All new tables designed
- [ ] Schema modifications specified
- [ ] New views defined
- [ ] Migration plan created
- [ ] Backward compatibility addressed

---

## Task 10: Create Artifact-to-Audit Cross-Reference

**Type:** Research
**Complexity:** Simple
**Estimated Tokens:** 8,000
**Duration:** 0.5 days

### Objective
Create a cross-reference mapping between database artifacts and the audit outputs from Phase 1 sprints.

### Cross-Reference Structure

```yaml
cross_reference:
  artifact_type: track
  db_table: tracks
  db_record_id: 01KC2D0JKVT80AFQ6C1PA8CKJT  # User Journey Audit track

  related_audits:
    - audit_file: VIBEY_FILE_CLASSIFICATION.yaml
      sprint: 1.1
      relationship: "Classifies files this track's code touches"
      linkage: indirect

    - audit_file: AUDIT_ROADMAP_MODULE.yaml
      sprint: 1.2
      relationship: "Audits roadmap module used by this track"
      linkage: functional

  files_involved:
    - path: vibey/roadmap/models/track.py
      audit_file: AUDIT_ROADMAP_MODULE.yaml
      audit_score: 85

    - path: tests/roadmap/test_track.py
      audit_file: AUDIT_TESTS_ROADMAP.yaml
      audit_score: 78
```

### Output Format
```yaml
# AUDIT_TO_DATABASE_CROSSREF.yaml
cross_reference:
  generated_at: "2025-12-11T00:00:00Z"

  summary:
    db_artifact_types: X
    audit_output_files: X
    direct_mappings: X
    indirect_mappings: X

  by_db_artifact:
    roadmap:
      table: roadmaps
      records: X
      related_audits: [list]

    track:
      table: tracks
      records: X
      related_audits: [list]
      example_mapping:
        record_id: 01KC2D0JKVT80AFQ6C1PA8CKJT
        name: "User Journey Audit"
        files_audited: X
        avg_quality_score: X

    sprint:
      table: sprints
      records: X
      related_audits: [list]

    task:
      table: tasks
      records: X
      related_audits: [list]

  by_audit_file:
    FILE_REGISTRY.yaml:
      sprint: 1.1
      db_tables_related: [source_files (proposed)]
      records_would_create: X

    AUDIT_CLI_MODULE.yaml:
      sprint: 1.2
      db_tables_related: [artifacts, quality_metrics (proposed)]
      files_covered: X

    # ... all audit files

  gap_analysis:
    audits_without_db_storage:
      - FILE_REGISTRY.yaml
      - FILE_DEPENDENCY_GRAPH.yaml
      - COVERAGE_ANALYSIS_REPORT.yaml
      # ... etc

    db_artifacts_without_audits:
      - table: external_dependencies
        reason: "No audit covers external deps"
      # ... etc

  integration_recommendations:
    - "Load FILE_REGISTRY.yaml into source_files table"
    - "Link audit scores to artifact records"
    - "Create audit_results table for persistence"
```

### Acceptance Criteria
- [ ] All DB artifacts mapped to audits
- [ ] All audit files mapped to DB
- [ ] Gaps identified
- [ ] Integration path defined

---

## Task 11: Generate Database Artifact Audit Summary

**Type:** Documentation
**Complexity:** Medium
**Estimated Tokens:** 12,000
**Duration:** 0.5 days

### Objective
Consolidate all database artifact audit findings into a comprehensive summary.

### Report Structure
```markdown
# Database Artifact Audit Summary

## Executive Summary
- Tables audited: 27
- Views audited: 21
- Missing artifact types: X
- Missing relationship types: X
- Schema improvements proposed: X
- Estimated implementation effort: X hours

## Current Schema Overview

### Entity Counts
| Entity Type | Table | Records | Completeness |
|-------------|-------|---------|--------------|
| Roadmaps | roadmaps | X | X% |
| Tracks | tracks | X | X% |
| Sprints | sprints | X | X% |
| Tasks | tasks | X | X% |

### Relationship Summary
| Relationship | Table | Records | Health |
|--------------|-------|---------|--------|
| Blocking | entity_blocks | X | Good |
| Dependencies | entity_depends_on | X | Good |
| Commits | entity_commits | X | Sparse |

## Gap Analysis

### Missing Artifact Types
| Artifact | Priority | Impact | Effort |
|----------|----------|--------|--------|
| source_file | High | Cannot track file quality | 8h |
| audit_result | Medium | Cannot persist audits | 6h |
| quality_metric | Medium | Cannot track trends | 4h |

### Missing Relationships
| Relationship | Priority | Impact |
|--------------|----------|--------|
| file_imports | High | Cannot query dependencies |
| file_tested_by | High | Cannot find untested code |
| task_modifies_file | Medium | Cannot track task scope |

## File Audit to Database Mapping

### Mapping Status
| Audit Output | DB Support | Gap |
|--------------|------------|-----|
| FILE_REGISTRY.yaml | None | New table needed |
| AUDIT_*.yaml | Partial | Extend artifacts |
| COVERAGE_*.yaml | None | New table needed |

## Metadata Assessment

### Completeness by Table
| Table | Required Fields | Optional Fields | JSON Usage |
|-------|-----------------|-----------------|------------|
| tasks | 95% | 40% | 25% |
| sprints | 90% | 35% | 30% |
| tracks | 85% | 30% | 20% |

## Query Capabilities

### View Health
| Category | Views | Well-Designed | Needs Work |
|----------|-------|---------------|------------|
| Progress | 3 | 3 | 0 |
| Summary | 3 | 2 | 1 |
| Status | 5 | 4 | 1 |
| Activity | 2 | 2 | 0 |

### Missing Queries
- Find untested files
- Track quality trends
- Audit coverage analysis
- Task-to-file mapping

## Improvement Roadmap

### Phase 1: Core File Tracking (High Priority)
- Create source_files table
- Create file_dependencies table
- Add v_untested_files view
- Effort: 16 hours

### Phase 2: Audit Persistence (Medium Priority)
- Create audit_results table
- Create audit_findings table
- Migration scripts for existing audits
- Effort: 12 hours

### Phase 3: Quality Tracking (Medium Priority)
- Create quality_metrics table
- Add quality trend views
- Historical tracking
- Effort: 8 hours

### Phase 4: Advanced Relationships (Low Priority)
- Task-to-file relationships
- Commit-to-file parsing
- Effort: 10 hours

## Recommendations

### Immediate Actions
1. Create source_files table from FILE_REGISTRY.yaml
2. Standardize JSON metadata schemas
3. Add missing indexes for common queries

### Short-term Improvements
1. Implement audit persistence
2. Create file relationship tracking
3. Add quality trend views

### Long-term Strategy
1. Full file-level tracking integration
2. Automated audit result storage
3. Quality dashboard support

## Appendix
- Complete schema documentation
- Proposed table schemas
- Migration scripts
```

### Acceptance Criteria
- [ ] All analyses synthesized
- [ ] Gaps clearly identified
- [ ] Roadmap prioritized
- [ ] Recommendations actionable

---

## Sprint Dependencies

```
Task 1 (Schema Doc) ────> Task 2 (Inventory) ────> Task 3 (Relationships)
                                                          │
Task 4 (File Mapping) <───────────────────────────────────┘
        │
        ├──> Task 5 (Missing Artifacts)
        │
        └──> Task 6 (Missing Relationships)

Task 2 ──> Task 7 (Metadata Assessment)

Task 3 ──> Task 8 (Query Audit)

Tasks 5-8 ──> Task 9 (Design Improvements)

Tasks 4, 9 ──> Task 10 (Cross-Reference)

All Tasks ──> Task 11 (Summary)
```

## Sprint Success Criteria

1. **Completeness**
   - [ ] Full schema documented
   - [ ] All tables inventoried
   - [ ] All relationships analyzed
   - [ ] All gaps identified

2. **Accuracy**
   - [ ] Schema documentation matches actual DB
   - [ ] Record counts accurate
   - [ ] Relationship analysis correct

3. **Actionability**
   - [ ] Clear improvement roadmap
   - [ ] Effort estimates realistic
   - [ ] Implementation path defined

4. **Quality**
   - [ ] Cross-reference enables integration
   - [ ] Recommendations are specific
   - [ ] Priority rankings justified

---

## Output Directory Structure

```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-6/
├── SPRINT_PLAN.md                          # This document
├── DATABASE_SCHEMA_DOCUMENTATION.md        # Task 1 output
├── ARTIFACT_TABLES_INVENTORY.yaml          # Task 2 output
├── RELATIONSHIP_MODEL_ANALYSIS.yaml        # Task 3 output
├── FILE_AUDIT_TO_ARTIFACT_MAPPING.yaml     # Task 4 output
├── MISSING_ARTIFACT_TYPES.yaml             # Task 5 output
├── MISSING_RELATIONSHIP_TYPES.yaml         # Task 6 output
├── METADATA_COMPLETENESS_ASSESSMENT.yaml   # Task 7 output
├── QUERY_CAPABILITIES_AUDIT.yaml           # Task 8 output
├── ARTIFACT_TRACKING_IMPROVEMENTS.yaml     # Task 9 output
├── AUDIT_TO_DATABASE_CROSSREF.yaml         # Task 10 output
├── DATABASE_ARTIFACT_AUDIT_SUMMARY.md      # Task 11 output
└── SPRINT_COMPLETION_REPORT.md             # Final summary
```
