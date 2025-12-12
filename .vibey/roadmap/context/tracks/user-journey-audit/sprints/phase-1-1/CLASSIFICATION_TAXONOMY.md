# File Classification Taxonomy

**Version:** 1.0
**Created:** 2025-12-12
**Sprint:** Phase 1.1 - File Inventory & Classification
**Task:** Task 2 - Define File Classification Taxonomy

---

## Overview

This document defines the comprehensive classification schema used to categorize all files in the Vibey repository. The taxonomy enables:

- Systematic codebase auditing
- Documentation coverage analysis
- Test coverage mapping
- Dependency tracking
- Quality assessment

---

## Primary Categories

### 1. CORE-LIB

**Scope:** `vibey/` package directory
**Purpose:** Production code that implements the Vibey Agent Framework

| Subcategory | ID | Description | Example Files |
|-------------|-----|-------------|---------------|
| **models** | 1.1 | Data models, schemas, Pydantic types, enums | `vibey/roadmap/models/track.py`, `vibey/roadmap/models/common.py` |
| **operations** | 1.2 | Business logic, command implementations, workflows | `vibey/operations/roadmap/query.py`, `vibey/operations/roadmap/update.py` |
| **serialization** | 1.3 | YAML/JSON/SQL loaders, dumpers, converters | `vibey/roadmap/serialization/yaml_loader.py`, `vibey/roadmap/serialization/sql_dumper.py` |
| **cli** | 1.4 | CLI commands, Click groups, entry points | `vibey/cli/main.py`, `vibey/cli/commands.py` |
| **mcp** | 1.5 | MCP server implementation, tools, resources | `vibey/mcp/server.py`, `vibey/mcp/tools.py` |
| **adapters** | 1.6 | Platform adapters for Goose, Cursor, etc. | `vibey/adapters/goose.py`, `vibey/adapters/base.py` |
| **common** | 1.7 | Shared utilities, error classes, helpers | `vibey/common/errors.py`, `vibey/common/utils.py` |
| **config** | 1.8 | Configuration loading, validation, schema | `vibey/operations/config/loader.py`, `vibey/config/schema.py` |
| **content** | 1.9 | Content management, templates, rendering | `vibey/operations/content/templates.py` |
| **platform** | 1.10 | Platform abstraction, detection, capabilities | `vibey/platform/detection.py`, `vibey/platform/capabilities.py` |
| **root** | 1.11 | Package `__init__.py`, `__main__.py`, `py.typed` | `vibey/__init__.py`, `vibey/__main__.py` |
| **audit** | 1.12 | Audit tooling for codebase analysis | `vibey/operations/audit/file_inventory.py` |

### 2. DOCUMENTATION

**Scope:** `docs/` directory and root documentation files
**Purpose:** User guides, reference docs, contributor documentation

| Subcategory | ID | Description | Example Files |
|-------------|-----|-------------|---------------|
| **getting-started** | 2.1 | Onboarding, quickstart, installation | `docs/getting-started/QUICK_START.md` |
| **guides** | 2.2 | How-to guides, tutorials, walkthroughs | `docs/guides/ORCHESTRATION.md`, `docs/guides/WORKFLOW_SELECTION_GUIDE.md` |
| **reference** | 2.3 | API reference, CLI reference, schemas | `docs/reference/CLI_REFERENCE.md`, `docs/reference/ROADMAP_SYSTEM.md` |
| **development** | 2.4 | Contributor docs, development setup | `docs/development/CONTRIBUTING.md`, `docs/development/ROADMAP.md` |
| **architecture** | 2.5 | Design documents, ADRs, system design | `docs/architecture/OVERVIEW.md` |
| **roadmap** | 2.6 | Roadmap documentation, sprint docs | `docs/roadmap/BEST_PRACTICES.md` |
| **operations** | 2.7 | Operational procedures, runbooks | `docs/operations/DEPLOYMENT.md` |
| **root** | 2.8 | Root-level docs: README, CHANGELOG, etc. | `README.md`, `CHANGELOG.md`, `CLAUDE.md`, `CONTRIBUTING.md` |

### 3. TESTS

**Scope:** `tests/` directory
**Purpose:** Test suite for validating code functionality

| Subcategory | ID | Description | Example Files |
|-------------|-----|-------------|---------------|
| **unit** | 3.1 | Unit tests for individual functions/classes | `tests/roadmap/test_models.py`, `tests/cli/test_commands.py` |
| **integration** | 3.2 | Integration tests spanning multiple modules | `tests/integration/test_roadmap_workflow.py` |
| **e2e** | 3.3 | End-to-end tests simulating user workflows | `tests/e2e/test_full_workflow.py` |
| **fixtures** | 3.4 | Test data, sample files, mock objects | `tests/fixtures/sample_roadmap.yaml`, `tests/fixtures/mock_config.json` |
| **utilities** | 3.5 | Test helpers, shared test utilities | `tests/conftest.py`, `tests/utils.py` |

### 4. SCRIPTS

**Scope:** `scripts/` directory
**Purpose:** Standalone scripts for development, migration, automation

| Subcategory | ID | Description | Example Files |
|-------------|-----|-------------|---------------|
| **migration** | 4.1 | Data migration, format conversion scripts | `scripts/migrate_yaml_to_sqlite.py` |
| **tooling** | 4.2 | Development tools, code generation | `scripts/generate_schema.py` |
| **automation** | 4.3 | CI/CD scripts, build automation | `scripts/run_tests.sh` |

### 5. CONFIG

**Scope:** Root configuration files
**Purpose:** Project configuration and build settings

| Subcategory | ID | Description | Example Files |
|-------------|-----|-------------|---------------|
| **python** | 5.1 | Python packaging configuration | `pyproject.toml`, `setup.cfg` |
| **testing** | 5.2 | Test configuration | `pytest.ini`, `.coveragerc` |
| **git** | 5.3 | Git configuration, hooks | `.gitignore`, `.pre-commit-config.yaml` |
| **packaging** | 5.4 | Distribution packaging | `MANIFEST.in` |
| **mcp** | 5.5 | MCP server configuration | `.mcp.json` |

### 6. FRAMEWORK

**Scope:** `framework/` directory
**Purpose:** Framework content files (agents, workflows, templates)

| Subcategory | ID | Description | Example Files |
|-------------|-----|-------------|---------------|
| **agents** | 6.1 | Agent definition files | `framework/agents/planning/sprint-planner.md` |
| **workflows** | 6.2 | Workflow definitions | `framework/workflows/single-feature-development.md` |
| **templates** | 6.3 | Handoff templates, output templates | `framework/templates/handoffs/task-complete.md` |
| **schemas** | 6.4 | YAML/JSON schemas | `framework/schemas/roadmap.schema.yaml` |
| **examples** | 6.5 | Example configurations | `framework/examples/project-config.yaml` |

### 7. ROADMAP-DATA

**Scope:** `.vibey/roadmap/` directory
**Purpose:** Roadmap system data files

| Subcategory | ID | Description | Example Files |
|-------------|-----|-------------|---------------|
| **tracks** | 7.1 | Track definition YAML files | `.vibey/roadmap/tracks/01KC*.yaml` |
| **sprints** | 7.2 | Sprint definition YAML files | `.vibey/roadmap/sprints/01KC*.yaml` |
| **tasks** | 7.3 | Task definition YAML files | `.vibey/roadmap/tasks/01KC*.yaml` |
| **context** | 7.4 | Sprint context, plans, analysis | `.vibey/roadmap/context/tracks/*/SPRINT_PLAN.md` |
| **activity** | 7.5 | Activity logs, audit trails | `.vibey/roadmap/activity_log/` |

---

## Classification Metadata Schema

Each file classification includes the following metadata:

```yaml
file_classification:
  # Identity
  path: string              # Relative file path from repo root
  category: string          # Primary category (e.g., "core-lib", "documentation")
  subcategory: string       # Subcategory ID (e.g., "1.2", "2.3")
  subcategory_name: string  # Subcategory name (e.g., "operations", "reference")

  # Description
  purpose: string           # Brief description of file purpose (1-2 sentences)

  # Code-specific (category 1 only)
  module: string            # Python module path (e.g., "vibey.operations.roadmap")
  exports: list             # Key classes, functions, constants exported

  # Relationships
  dependencies:
    internal: list          # Internal files this file imports
    external: list          # External packages this file imports
  dependents: list          # Files that import/reference this file

  # Coverage
  test_coverage:
    has_tests: boolean      # Does a corresponding test file exist?
    test_files: list        # List of test files covering this file
  doc_coverage:
    has_docs: boolean       # Is this file documented?
    doc_files: list         # Documentation files referencing this

  # Metadata
  size_bytes: integer       # File size in bytes
  lines: integer            # Line count (null for binary)
  last_modified: datetime   # Last modification timestamp
  last_audit: date          # When file was last audited (null if never)
```

---

## Classification Decision Rules

### Rule 1: Category Priority

When a file could belong to multiple categories, use this priority:

1. **TESTS** - If in `tests/` directory, always classify as tests
2. **ROADMAP-DATA** - If in `.vibey/roadmap/`, always classify as roadmap-data
3. **FRAMEWORK** - If in `framework/`, always classify as framework
4. **SCRIPTS** - If in `scripts/`, always classify as scripts
5. **CONFIG** - If a root config file (no directory prefix)
6. **DOCUMENTATION** - If `.md` file in `docs/` or root
7. **CORE-LIB** - If in `vibey/` directory

### Rule 2: Subcategory Assignment

#### For CORE-LIB (vibey/):

| Directory Pattern | Subcategory |
|------------------|-------------|
| `vibey/roadmap/models/` | 1.1 models |
| `vibey/operations/` | 1.2 operations |
| `vibey/roadmap/serialization/` | 1.3 serialization |
| `vibey/cli/` | 1.4 cli |
| `vibey/mcp/` | 1.5 mcp |
| `vibey/adapters/` | 1.6 adapters |
| `vibey/common/` | 1.7 common |
| `vibey/operations/config/`, `vibey/config/` | 1.8 config |
| `vibey/operations/content/`, `vibey/content/` | 1.9 content |
| `vibey/platform/` | 1.10 platform |
| `vibey/__init__.py`, `vibey/__main__.py`, `vibey/py.typed` | 1.11 root |
| `vibey/operations/audit/` | 1.12 audit |

#### For TESTS (tests/):

| Pattern | Subcategory |
|---------|-------------|
| `test_*.py` in module directories | 3.1 unit |
| `tests/integration/` | 3.2 integration |
| `tests/e2e/` | 3.3 e2e |
| `tests/fixtures/`, `*.yaml`, `*.json` in tests | 3.4 fixtures |
| `conftest.py`, `tests/utils.py`, test helpers | 3.5 utilities |

### Rule 3: Edge Cases

| Scenario | Decision |
|----------|----------|
| `conftest.py` at any level | 3.5 utilities (test configuration) |
| `__init__.py` in test directories | 3.5 utilities (package marker) |
| `.md` files in `tests/` | 3.4 fixtures (test documentation) |
| `setup.py` in root | 5.1 python (legacy packaging) |
| Files without extension | Classify by content/location |
| Symlinks | Classify by target file |
| Empty `__init__.py` | 1.11 root or 3.5 utilities (by location) |

### Rule 4: Ambiguous Files

When classification is unclear:

1. Check the file's imports - what does it depend on?
2. Check the file's dependents - what imports it?
3. Consider the file's primary purpose
4. Default to the most specific category that fits

---

## Examples by Category

### 1. CORE-LIB Examples

```yaml
# Example: CLI entry point
- path: vibey/cli/main.py
  category: core-lib
  subcategory: "1.4"
  subcategory_name: cli
  purpose: Main CLI entry point using Click, defines command groups and routing
  module: vibey.cli.main
  exports: [cli, main, __version__]
  dependencies:
    internal: [vibey/cli/commands.py, vibey/operations/roadmap/query.py]
    external: [click, rich]
  test_coverage:
    has_tests: true
    test_files: [tests/cli/test_main.py]

# Example: Data model
- path: vibey/roadmap/models/track.py
  category: core-lib
  subcategory: "1.1"
  subcategory_name: models
  purpose: Track model definition with Pydantic validation and status enums
  module: vibey.roadmap.models.track
  exports: [Track, TrackStatus, TrackProgress]
  dependencies:
    internal: [vibey/roadmap/models/common.py]
    external: [pydantic, datetime]
```

### 2. DOCUMENTATION Examples

```yaml
# Example: Quickstart guide
- path: docs/getting-started/QUICK_START.md
  category: documentation
  subcategory: "2.1"
  subcategory_name: getting-started
  purpose: 10-minute quickstart for new users covering installation and first project
  topic_coverage: [installation, first-project, basic-cli]
  target_audience: [new-users, evaluators]
  references_code: [vibey/cli/main.py, vibey/operations/roadmap/init.py]
  accuracy_status: needs_review

# Example: Root documentation
- path: README.md
  category: documentation
  subcategory: "2.8"
  subcategory_name: root
  purpose: Main repository README with project overview and getting started
  topic_coverage: [overview, installation, quick-start, features]
  target_audience: [all]
```

### 3. TESTS Examples

```yaml
# Example: Unit test
- path: tests/roadmap/test_query.py
  category: tests
  subcategory: "3.1"
  subcategory_name: unit
  purpose: Unit tests for roadmap query operations
  tests_module: vibey.operations.roadmap.query
  test_count: 15
  coverage_scope: [vibey/operations/roadmap/query.py]
  fixtures_used: [tests/fixtures/sample_roadmap.yaml]

# Example: Test fixture
- path: tests/fixtures/sample_roadmap.yaml
  category: tests
  subcategory: "3.4"
  subcategory_name: fixtures
  purpose: Sample roadmap data for testing roadmap operations
  used_by: [tests/roadmap/test_query.py, tests/roadmap/test_update.py]
```

### 4. SCRIPTS Examples

```yaml
# Example: Migration script
- path: scripts/migrate_yaml_to_sqlite.py
  category: scripts
  subcategory: "4.1"
  subcategory_name: migration
  purpose: One-time migration script to convert YAML roadmap to SQLite format
  is_one_time: true
  dependencies: [vibey/roadmap/serialization/yaml_loader.py]
```

### 5. CONFIG Examples

```yaml
# Example: Python packaging
- path: pyproject.toml
  category: config
  subcategory: "5.1"
  subcategory_name: python
  purpose: Python project configuration (dependencies, build settings, tool configs)

# Example: Test configuration
- path: pytest.ini
  category: config
  subcategory: "5.2"
  subcategory_name: testing
  purpose: Pytest configuration with test discovery and plugin settings
```

---

## Usage Guidelines

### For Automated Classification

Use the classification schema to:
1. Generate consistent YAML classification outputs
2. Validate classification data
3. Build dependency graphs
4. Calculate coverage metrics

### For Manual Classification

When classifying files manually:
1. Start with the category decision rules
2. Apply subcategory patterns
3. Check edge case rules
4. Document any unclear decisions

### For Auditing

Use classifications to:
1. Identify untested code files
2. Find undocumented features
3. Detect orphan files (no dependencies or dependents)
4. Track documentation staleness

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-12 | Initial taxonomy definition |

---

*End of Classification Taxonomy Document*
