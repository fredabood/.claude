# Classification Taxonomy V2

**Generated:** 2025-12-28
**Audit Version:** comprehensive-audit-v2

## Overview

This taxonomy defines the file classification system used in the Comprehensive Repository Audit V2. It extends the original V1 taxonomy (Dec 12, 2024) with new subcategories for files added since then.

## Primary Categories (7)

| Category | Description | V1 Files | V2 Files | Change |
|----------|-------------|----------|----------|--------|
| CORE-LIB | Python source code in `vibey/` | 365 | 503 | +138 |
| DOCUMENTATION | Markdown and docs in `docs/` | 187 | 875 | +688 |
| TESTS | Test files in `tests/` | 154 | 243 | +89 |
| SCRIPTS | Automation scripts in `scripts/` | 4 | 4 | 0 |
| CONFIG | Configuration files (root) | ~20 | ~25 | +5 |
| FRAMEWORK | `.vibey/` framework files | N/A | 7,754 | NEW |
| ROADMAP-DATA | `.vibey/roadmap/` data files | N/A | 5,118 | NEW |

## CORE-LIB Subcategories (24)

### CLI (8 subcategories)

| Subcategory | Pattern | Description | Count |
|-------------|---------|-------------|-------|
| `cli-entry` | `vibey/cli/main.py` | CLI entry point | 1 |
| `cli-commands` | `vibey/cli/commands*.py` | Command implementations | 16 |
| `cli-command-modules` | `vibey/cli/command_modules/` | Modular commands | 15 |
| `cli-formatters` | `vibey/cli/formatters/` | Output formatters | 8 |
| `cli-roadmap-lib` | `vibey/cli/roadmap_lib/` | Roadmap utilities | 12 |
| `cli-utilities` | `vibey/cli/*.py` | Other CLI utilities | 74 |
| `cli-legacy` | `vibey/cli/*-legacy*` | Deprecated scripts | ~20 |

### Operations (7 subcategories)

| Subcategory | Pattern | Description | Count |
|-------------|---------|-------------|-------|
| `operations-roadmap` | `vibey/operations/roadmap/` | Roadmap operations | 32 |
| `operations-git` | `vibey/operations/git/` | Git operations | 30 |
| `operations-docs` | `vibey/operations/docs/` | Doc generation | 6 |
| `operations-auth` | `vibey/operations/auth/` | Authentication | 4 |
| `operations-discovery` | `vibey/operations/discovery/` | Discovery | 3 |
| `operations-context` | `vibey/operations/context/` | Context management | 2 |
| `operations-core` | `vibey/operations/*.py` | Core operations | 29 |

### Roadmap (6 subcategories)

| Subcategory | Pattern | Description | Count |
|-------------|---------|-------------|-------|
| `roadmap-models` | `vibey/roadmap/models/` | Data models | 27 |
| `roadmap-serialization` | `vibey/roadmap/serialization/` | YAML/SQL serialization | 12 |
| `roadmap-database` | `vibey/roadmap/database/` | SQLite operations | 27 |
| `roadmap-criteria` | `vibey/roadmap/criteria/` | Acceptance criteria | 8 |
| `roadmap-standards` | `vibey/roadmap/standards/` | Standards validation | 6 |
| `roadmap-core` | `vibey/roadmap/*.py` | Core roadmap | 19 |

### MCP (5 subcategories)

| Subcategory | Pattern | Description | Count |
|-------------|---------|-------------|-------|
| `mcp-core` | `vibey/mcp/*.py` | MCP server core | 8 |
| `mcp-tools` | `vibey/mcp/tools/` | MCP tools | 12 |
| `mcp-resources` | `vibey/mcp/resources/` | MCP resources | 3 |
| `mcp-prompts` | `vibey/mcp/prompts/` | MCP prompts | 3 |
| `mcp-discovery` | `vibey/mcp/discovery/` | Discovery tools | 6 |

### Services (NEW - 2 subcategories)

| Subcategory | Pattern | Description | Count |
|-------------|---------|-------------|-------|
| `services-implementation` | `vibey/services/implementation/` | Implementation mode | 39 |
| `services` | `vibey/services/*.py` | Other services | 5 |

### Other (3 subcategories)

| Subcategory | Pattern | Description | Count |
|-------------|---------|-------------|-------|
| `adapters` | `vibey/adapters/` | Platform adapters | 47 |
| `common` | `vibey/common/` | Shared utilities | 5 |
| `unified` | `vibey/unified/` | Unified arch (NEW) | 8 |
| `root` | `vibey/*.py` | Package root | 4 |

## DOCUMENTATION Subcategories (9)

| Subcategory | Pattern | Description | V1 | V2 |
|-------------|---------|-------------|-----|-----|
| `development` | `docs/development/` | Dev guides | 60 | 63 |
| `architecture` | `docs/architecture/` | Architecture docs | 5 | 15 |
| `adr` | `docs/architecture/adr/` | ADR records | 5 | 10 |
| `guides` | `docs/guides/` | User guides | 43 | 46 |
| `reference` | `docs/reference/` | Reference docs | 6 | 8 |
| `journeys` | `docs/journeys/` | User journeys | 0 | 6 |
| `walkthroughs` | `docs/walkthroughs/` | Tutorials | 0 | 16 |
| `archived` | `docs/archived/` | Old docs | 0 | 50+ |
| `root` | `docs/*.md` | Root docs | ~70 | ~650 |

## TESTS Subcategories (7)

| Subcategory | Pattern | Description | V1 | V2 |
|-------------|---------|-------------|-----|-----|
| `unit` | `tests/*.py`, `tests/unit/` | Unit tests | 113 | ~150 |
| `integration` | `tests/integration/` | Integration tests | 20 | 32 |
| `cli` | `tests/cli/` | CLI tests | 20 | 25 |
| `mcp` | `tests/mcp/` | MCP tests | 12 | 15 |
| `operations` | `tests/operations/` | Operations tests | 5 | 10 |
| `roadmap` | `tests/roadmap/` | Roadmap tests | 12 | 18 |
| `fixtures` | `conftest.py` | Test fixtures | 2 | 5 |

## New Subcategories Added in V2

The following subcategories are new in V2:

### CORE-LIB New Subcategories

1. **`services-implementation`** - Implementation mode loop, completion, task selection
2. **`unified`** - Unified architecture prototype
3. **`cli-command-modules`** - Modular CLI command organization
4. **`cli-formatters`** - Output formatting utilities
5. **`operations-context`** - Context file management
6. **`operations-discovery`** - Discovery operations

### DOCUMENTATION New Subcategories

1. **`journeys`** - Persona-based user journeys (5 personas)
2. **`walkthroughs`** - Step-by-step tutorials
3. **`archived`** - Historical/deprecated documentation

## Taxonomy Validation

### Rules

1. Every file must have exactly one primary category
2. Every file must have exactly one subcategory
3. Subcategories must be unique across primary categories
4. New subcategories require explicit definition here

### Coverage Check

| Category | Files Classified | Coverage |
|----------|------------------|----------|
| CORE-LIB | 503/503 | 100% |
| DOCUMENTATION | 875/875 | 100% |
| TESTS | 243/243 | 100% |
| SCRIPTS | 4/4 | 100% |

---

*Taxonomy Version: 2.0*
*Generated: 2025-12-28*
*Audit: Comprehensive Repository Audit V2*
