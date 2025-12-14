# Discovery Output Schema Documentation

**Version:** 1.0.0
**Sprint:** Phase 4.2 - Discovery Output Architecture
**Task:** Task 2 - Design discovery output schema

---

## Overview

The Discovery Output Schema defines the structured format for project discovery results. When `vibey discover` analyzes a project, it produces output conforming to this schema.

### Design Goals

1. **Comprehensive** - Capture all relevant project metadata
2. **Versioned** - Support schema evolution and backward compatibility
3. **Machine-readable** - Enable programmatic access (YAML/JSON)
4. **Human-readable** - Clear structure for manual inspection
5. **Extensible** - Allow custom fields without breaking consumers

---

## Schema Structure

```
DiscoveryOutput
├── metadata          # Execution metadata (when, where, git state)
├── project           # High-level project info (name, type, languages)
├── structure         # Directory/file structure analysis
├── dependencies      # Runtime and dev dependencies
├── patterns          # Detected code patterns
├── conventions       # Naming and organization conventions
├── quality           # Quality metrics (tests, docs, security)
├── recommendations   # Improvement suggestions
└── git_history       # Git analysis (optional)
```

---

## Section Details

### 1. Metadata

**Purpose:** Track discovery execution context for reproducibility.

```yaml
metadata:
  schema_version: "1.0.0"
  discovered_at: "2025-12-14T10:30:00Z"
  project_root: "/Users/dev/my-project"
  git_commit: "abc123def456..."
  git_branch: "main"
  discovery_duration_ms: 5432
  previous_discovery_id: "01KC..."
```

| Field | Required | Description |
|-------|----------|-------------|
| `schema_version` | Yes | Semver version of this schema |
| `discovered_at` | Yes | ISO 8601 timestamp |
| `project_root` | Yes | Absolute path to project |
| `git_commit` | No | SHA of HEAD at discovery time |
| `git_branch` | No | Current branch name |
| `discovery_duration_ms` | No | Execution time in milliseconds |
| `previous_discovery_id` | No | ULID of previous discovery for diff |

### 2. Project

**Purpose:** High-level project classification.

```yaml
project:
  name: "my-api"
  type: "api"
  type_confidence: 95
  description: "FastAPI-based REST API"
  languages:
    - name: "python"
      percentage: 85
      version: "3.11"
    - name: "javascript"
      percentage: 15
  frameworks:
    - name: "fastapi"
      category: "backend"
      version: "0.109.0"
      confidence: 100
    - name: "sqlalchemy"
      category: "orm"
      version: "2.0.25"
```

**Project Types:**
- `web-app` - Full-stack web application
- `api` - Backend API service
- `cli` - Command-line tool
- `library` - Reusable library/package
- `ml-model` - Machine learning project
- `data-pipeline` - Data processing pipeline
- `infrastructure` - IaC project (Terraform, etc.)
- `monorepo` - Multi-project repository
- `unknown` - Could not classify

### 3. Structure

**Purpose:** Understand codebase organization.

```yaml
structure:
  total_files: 127
  total_lines: 15420
  directories:
    - path: "src/api"
      purpose: "source"
      file_count: 45
      line_count: 8200
      primary_language: "python"
    - path: "tests"
      purpose: "tests"
      file_count: 32
  key_files:
    - path: "src/main.py"
      role: "entry_point"
      lines: 45
    - path: "pyproject.toml"
      role: "manifest"
  entry_points:
    - "src/main.py"
    - "src/cli.py"
  architecture_pattern: "layered"
  architecture_confidence: 80
```

**Directory Purposes:**
- `source` - Main source code
- `tests` - Test files
- `docs` - Documentation
- `config` - Configuration files
- `scripts` - Build/utility scripts
- `assets` - Static assets
- `generated` - Auto-generated code
- `vendor` - Third-party code
- `unknown` - Unclassified

**Key File Roles:**
- `entry_point` - Application entry point
- `config` - Configuration file
- `readme` - README documentation
- `changelog` - CHANGELOG file
- `license` - License file
- `manifest` - Package manifest (package.json, pyproject.toml)
- `schema` - Schema definition
- `migration` - Database migration
- `test_config` - Test configuration
- `ci_config` - CI/CD configuration
- `docker` - Docker-related file

### 4. Dependencies

**Purpose:** Track project dependencies and their health.

```yaml
dependencies:
  runtime:
    - name: "fastapi"
      version: "0.109.0"
      latest_version: "0.110.0"
      is_outdated: true
      has_vulnerability: false
    - name: "sqlalchemy"
      version: "2.0.25"
      has_vulnerability: true
      vulnerability_severity: "medium"
  development:
    - name: "pytest"
      version: "8.0.0"
  system:
    - name: "postgresql"
      category: "database"
      version: "16"
      detected_from: "requirements.txt:psycopg2"
    - name: "redis"
      category: "cache"
  outdated_count: 5
  vulnerable_count: 1
```

**System Dependency Categories:**
- `database` - PostgreSQL, MySQL, MongoDB, etc.
- `cache` - Redis, Memcached
- `queue` - RabbitMQ, Kafka, SQS
- `storage` - S3, GCS, MinIO
- `search` - Elasticsearch, Algolia
- `other` - Other services

### 5. Patterns

**Purpose:** Document detected code patterns.

```yaml
patterns:
  architectural:
    - name: "dependency_injection"
      description: "Uses FastAPI Depends() for DI"
      locations:
        - "src/api/deps.py"
        - "src/api/routes/*.py"
      confidence: 95
    - name: "repository_pattern"
      description: "Data access abstracted through repositories"
      locations:
        - "src/repositories/"
      confidence: 85
  coding:
    - name: "async_await"
      description: "Async/await for I/O operations"
      confidence: 100
  testing:
    - name: "fixtures"
      description: "pytest fixtures for test setup"
      confidence: 90
```

### 6. Conventions

**Purpose:** Document project coding conventions.

```yaml
conventions:
  naming:
    files: "snake_case"
    functions: "snake_case"
    classes: "PascalCase"
    variables: "snake_case"
  organization:
    module_structure: "domain-driven"
    test_location: "separate"
    import_style: "absolute with grouping"
  commit_convention: "conventional_commits"
  code_style:
    formatter: "black"
    linter: "ruff"
    type_checker: "mypy"
```

**Naming Conventions:**
- `snake_case` - lowercase with underscores
- `kebab-case` - lowercase with hyphens
- `PascalCase` - capitalized words
- `camelCase` - lowercase first, then capitalized
- `mixed` - inconsistent

**Test Locations:**
- `alongside` - Tests next to source (src/foo.py, src/foo_test.py)
- `separate` - Tests in separate directory (src/foo.py, tests/test_foo.py)
- `both` - Mixed approach

### 7. Quality

**Purpose:** Code quality metrics summary.

```yaml
quality:
  test_coverage: 78.5
  test_count: 127
  documentation_score: 65
  security_score: 72
  overall_health: 75
```

| Metric | Range | Description |
|--------|-------|-------------|
| `test_coverage` | 0-100 | Percentage of code covered by tests |
| `test_count` | 0+ | Number of test cases |
| `documentation_score` | 0-100 | Documentation completeness |
| `security_score` | 0-100 | Security assessment |
| `overall_health` | 0-100 | Weighted aggregate score |

### 8. Recommendations

**Purpose:** Actionable improvement suggestions.

```yaml
recommendations:
  immediate:
    - category: "security"
      title: "Add rate limiting"
      description: "API endpoints lack rate limiting"
      priority: "high"
      effort: "small"
      files:
        - "src/api/main.py"
    - category: "testing"
      title: "Increase test coverage"
      description: "Coverage is 78%, target 85%+"
      priority: "medium"
      effort: "medium"
  suggested:
    - category: "documentation"
      title: "Add API documentation"
      description: "Generate OpenAPI docs"
      priority: "low"
      effort: "small"
```

**Categories:**
- `security` - Security vulnerabilities
- `testing` - Test coverage gaps
- `documentation` - Missing documentation
- `performance` - Performance improvements
- `maintainability` - Code quality
- `dependencies` - Dependency updates
- `architecture` - Architectural improvements

**Priority Levels:**
- `critical` - Must fix immediately
- `high` - Should fix soon
- `medium` - Plan to address
- `low` - Nice to have

**Effort Estimates:**
- `trivial` - < 1 hour
- `small` - 1-4 hours
- `medium` - 1-3 days
- `large` - 1-2 weeks
- `epic` - > 2 weeks

### 9. Git History (Optional)

**Purpose:** Development history analysis.

```yaml
git_history:
  total_commits: 234
  contributors:
    - name: "Alice"
      commits: 120
    - name: "Bob"
      commits: 84
  recent_sprints:
    - name: "Sprint 8: Auth Overhaul"
      start_date: "2024-10-01"
      end_date: "2024-10-15"
      commits: 47
      summary: "OAuth2, 2FA, token-based auth"
    - name: "Sprint 7: Payments"
      start_date: "2024-09-15"
      end_date: "2024-09-30"
      commits: 38
  velocity:
    commits_per_week: 45
    lines_per_month: 3500
  sprint_cadence: "bi-weekly"
```

---

## Example Output

Complete discovery output example:

```yaml
metadata:
  schema_version: "1.0.0"
  discovered_at: "2025-12-14T10:30:00Z"
  project_root: "/Users/dev/my-api"
  git_commit: "abc123def456789..."
  git_branch: "main"
  discovery_duration_ms: 5432

project:
  name: "my-api"
  type: "api"
  type_confidence: 95
  description: "FastAPI REST API for user management"
  languages:
    - name: "python"
      percentage: 100
      version: "3.11"
  frameworks:
    - name: "fastapi"
      category: "backend"
      version: "0.109.0"
      confidence: 100
    - name: "sqlalchemy"
      category: "orm"
      version: "2.0.25"
      confidence: 100
    - name: "pytest"
      category: "testing"
      version: "8.0.0"
      confidence: 100

structure:
  total_files: 127
  total_lines: 15420
  directories:
    - path: "src"
      purpose: "source"
      file_count: 85
      line_count: 12000
    - path: "tests"
      purpose: "tests"
      file_count: 32
      line_count: 2800
    - path: "docs"
      purpose: "docs"
      file_count: 10
      line_count: 620
  key_files:
    - path: "src/main.py"
      role: "entry_point"
      lines: 45
    - path: "pyproject.toml"
      role: "manifest"
      lines: 120
    - path: "README.md"
      role: "readme"
      lines: 200
  entry_points:
    - "src/main.py"
  architecture_pattern: "layered"
  architecture_confidence: 85

dependencies:
  runtime:
    - name: "fastapi"
      version: "0.109.0"
      is_outdated: false
    - name: "sqlalchemy"
      version: "2.0.25"
      is_outdated: false
    - name: "psycopg2-binary"
      version: "2.9.9"
      is_outdated: false
  development:
    - name: "pytest"
      version: "8.0.0"
    - name: "black"
      version: "24.1.0"
    - name: "ruff"
      version: "0.1.14"
  system:
    - name: "postgresql"
      category: "database"
      detected_from: "requirements.txt:psycopg2-binary"
  outdated_count: 0
  vulnerable_count: 0

patterns:
  architectural:
    - name: "dependency_injection"
      description: "FastAPI Depends() for DI"
      confidence: 95
    - name: "repository_pattern"
      description: "Data access via repositories"
      confidence: 85
  coding:
    - name: "async_await"
      description: "Async functions for I/O"
      confidence: 100
    - name: "type_hints"
      description: "Full type annotations"
      confidence: 90
  testing:
    - name: "fixtures"
      description: "pytest fixtures"
      confidence: 95

conventions:
  naming:
    files: "snake_case"
    functions: "snake_case"
    classes: "PascalCase"
    variables: "snake_case"
  organization:
    module_structure: "layered"
    test_location: "separate"
  commit_convention: "conventional_commits"
  code_style:
    formatter: "black"
    linter: "ruff"
    type_checker: "mypy"

quality:
  test_coverage: 78.5
  test_count: 127
  documentation_score: 65
  security_score: 85
  overall_health: 78

recommendations:
  immediate:
    - category: "testing"
      title: "Increase test coverage"
      description: "Coverage is 78.5%, target 85%+"
      priority: "medium"
      effort: "medium"
  suggested:
    - category: "documentation"
      title: "Add OpenAPI examples"
      description: "Add request/response examples to API docs"
      priority: "low"
      effort: "small"

git_history:
  total_commits: 234
  contributors:
    - name: "Alice"
      commits: 120
    - name: "Bob"
      commits: 84
    - name: "Charlie"
      commits: 30
  velocity:
    commits_per_week: 45
    lines_per_month: 3500
  sprint_cadence: "bi-weekly"
```

---

## Serialization

### YAML (Default)

Discovery outputs are stored as YAML for human readability:

```yaml
# .vibey/discovery/current.yaml
metadata:
  schema_version: "1.0.0"
  ...
```

### JSON

For programmatic access, JSON serialization is supported:

```bash
vibey discover --output json
```

### Text (Human-Friendly)

For CLI display, a formatted text output:

```bash
vibey discover show

Project: my-api (api)
Languages: Python 100%
Frameworks: FastAPI, SQLAlchemy, pytest

Structure: 127 files, 15,420 lines
  src/     - 85 files (source)
  tests/   - 32 files (tests)

Quality: 78/100 overall
  Test Coverage: 78.5%
  Security: 85/100

Recommendations:
  [MEDIUM] Increase test coverage to 85%+
```

---

## Versioning

### Schema Versioning

The schema follows semantic versioning:
- **Major** - Breaking changes (field removals, type changes)
- **Minor** - Backward-compatible additions
- **Patch** - Documentation, clarifications

### Discovery Versioning

Each discovery run can be versioned:
```
.vibey/discovery/
├── current.yaml                    # Latest discovery
├── history/
│   ├── 2025-12-14T10-30-00.yaml   # Previous discoveries
│   └── 2025-12-13T15-00-00.yaml
└── diffs/
    └── 2025-12-14T10-30-00.diff.yaml  # Changes from previous
```

---

## Integration Points

### Context Management

Discovery feeds into context management:
- Auto-seed context on project init
- Link discovery to sessions
- Include discovery in agent context

### Session Tracking

Link discovery versions to sessions:
```yaml
session:
  id: "01KC..."
  discovery_version: "2025-12-14T10-30-00"
```

### MCP Resources

Expose discovery as MCP resources:
```
vibey://discovery/current     # Current discovery
vibey://discovery/project     # Project section only
vibey://discovery/quality     # Quality metrics only
```

---

## Future Extensions

Potential additions in future schema versions:
- `cicd` - CI/CD pipeline analysis
- `deployment` - Deployment configuration
- `api_schema` - OpenAPI/GraphQL schema analysis
- `database_schema` - Database schema analysis
- `performance` - Performance baseline metrics
