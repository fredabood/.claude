# Sprint 1.5: Module Quality Re-Audit - Detailed Plan

## Sprint Overview

| Field | Value |
|-------|-------|
| Sprint ID | 01KDJNKE2B2W5NJRTSRZWN4QSQ |
| Track | Comprehensive Repository Audit V2 |
| Status | not_started |
| Tasks | 6 |
| Estimated Tokens | ~18,000 |
| Dependencies | Sprint 1 (File Inventory Refresh) |

## Goal

Re-audit module quality for all 7 primary module categories after file classifications are updated. The original module audits (Dec 12-16) are now 2+ weeks stale. Re-run quality checks and update audit documents with current findings.

## Context

### Original Module Audit Outputs
```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/
├── CORE_LIBRARY_AUDIT_SUMMARY.md
├── MODULE_QUALITY_AUDIT_CLI.md
├── MODULE_QUALITY_AUDIT_OPERATIONS.md
├── MODULE_QUALITY_AUDIT_ROADMAP.md
├── MODULE_QUALITY_AUDIT_MCP.md
├── MODULE_QUALITY_AUDIT_ADAPTERS.md
├── MODULE_QUALITY_AUDIT_COMMON.md
└── CROSS_MODULE_DEPENDENCY_ANALYSIS.md (if exists)
```

### Module Categories
1. **CLI** (vibey/cli/) - Command-line interface
2. **Operations** (vibey/operations/) - Business logic
3. **Roadmap** (vibey/roadmap/) - Models, serialization, database
4. **MCP** (vibey/mcp/) - Model Context Protocol server
5. **Adapters** (vibey/adapters/) - Platform adapters
6. **Common** (vibey/common/) - Shared utilities
7. **Services** (vibey/services/) - Service implementations (NEW)

### Key Changes Since Dec 12
- CLI: commands.py split into command_modules/
- Roadmap: New database schema (27→39 tables), new serialization
- Services: New implementation mode services
- Operations: New context, docs operations

---

## Task Details

### Task 1.5.1: Re-audit CLI Module Quality

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QT4`
**Type:** research | **Complexity:** medium | **Priority:** high

#### Description
Re-audit the CLI module which has seen significant changes including the split of commands.py into command_modules/.

#### Scope
```
vibey/cli/
├── __init__.py
├── main.py              # Entry point
├── commands.py          # Legacy (being deprecated?)
├── commands_legacy.py   # Legacy commands
├── formatters.py        # Output formatting
├── command_modules/     # NEW: Modular commands
│   ├── __init__.py
│   ├── roadmap.py
│   ├── deploy.py
│   └── ...
└── roadmap_lib/         # Roadmap CLI utilities
    ├── activity.py
    ├── cache.py
    └── ...
```

#### Audit Checklist

**Structure Analysis:**
- [ ] Count total Python files in vibey/cli/
- [ ] Count lines of code per file
- [ ] Identify largest files (>500 lines)
- [ ] Check for circular imports

**Quality Metrics:**
- [ ] Docstring coverage (% of functions with docstrings)
- [ ] Type hint coverage (% of functions with type hints)
- [ ] Test coverage (if available)
- [ ] Cyclomatic complexity of key functions

**Architecture Review:**
- [ ] Is commands.py still used or fully migrated?
- [ ] Are command_modules properly structured?
- [ ] Is there code duplication between legacy and new?

#### Deliverables
- Updated `MODULE_QUALITY_AUDIT_CLI.md`
- Comparison with Dec 12 findings
- Recommendations for improvement

#### Output Template
```markdown
# CLI Module Quality Audit (Updated Dec 28, 2024)

## Summary
| Metric | Dec 12 | Dec 28 | Change |
|--------|--------|--------|--------|
| Files | 45 | X | +Y |
| Lines of Code | 3,500 | X | +Y |
| Docstring Coverage | 65% | X% | +Y% |
| Type Hint Coverage | 40% | X% | +Y% |

## Structure Changes
- commands.py split into command_modules/
- [Other changes]

## Quality Issues
1. [Issue 1]
2. [Issue 2]

## Recommendations
1. [Recommendation 1]
2. [Recommendation 2]
```

---

### Task 1.5.2: Re-audit Operations Module Quality

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QT5`
**Type:** research | **Complexity:** medium | **Priority:** high

#### Description
Re-audit the operations module which contains core business logic. This module has grown significantly with new roadmap, docs, and context operations.

#### Scope
```
vibey/operations/
├── __init__.py
├── roadmap/           # Roadmap CRUD
│   ├── update.py
│   ├── query.py
│   ├── status_manager.py
│   └── ...
├── docs/              # Documentation generation
│   ├── cli_introspector.py
│   ├── cli_reference_generator.py
│   └── ...
├── context/           # Context system (NEW?)
├── discovery/         # Discovery operations
├── git/               # Git integration
│   ├── hooks/
│   └── ...
└── auth/              # Authentication (if exists)
```

#### Audit Checklist

**Structure Analysis:**
- [ ] Count subdirectories and their purpose
- [ ] Identify new subdirectories since Dec 12
- [ ] Check for orphaned files

**Quality Metrics:**
- [ ] Function complexity analysis
- [ ] Error handling patterns
- [ ] Logging consistency
- [ ] Input validation patterns

**Business Logic Review:**
- [ ] Are operations properly separated from CLI?
- [ ] Is there business logic in CLI that should be here?
- [ ] Are there duplicate operations?

#### Deliverables
- Updated `MODULE_QUALITY_AUDIT_OPERATIONS.md`
- New subdirectory documentation
- Refactoring recommendations

---

### Task 1.5.3: Re-audit Roadmap Module Quality

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QT6`
**Type:** research | **Complexity:** complex | **Priority:** high

**See:** `sprints/sprint-1.5/tasks/task-1.5.3-roadmap-audit/TASK_PLAN.md`

#### Description
Re-audit the roadmap module including models, serialization, database, and criteria submodules. This is the most changed module with new database schema, serialization formats, and model extensions.

#### Scope
```
vibey/roadmap/
├── __init__.py
├── models/              # Data models
│   ├── common.py
│   ├── task.py
│   ├── ticket/
│   │   ├── base.py
│   │   ├── enums.py
│   │   └── hierarchical.py
│   └── ...
├── serialization/       # YAML/SQL serialization
│   ├── yaml_loader.py
│   ├── yaml_dumper.py
│   ├── sql_loader.py
│   └── sql_dumper.py
├── database/            # SQLite integration
│   ├── schema.py
│   ├── connection.py
│   └── crud/
├── criteria/            # Completion criteria
│   ├── planned.py
│   └── ...
└── standards/           # Standards enforcement
```

#### Key Changes to Audit
- Database schema: 27 → 39 tables
- New views: 21 → 25
- YAML format standardization (v1/v2)
- New criteria system

#### Deliverables
- Updated `MODULE_QUALITY_AUDIT_ROADMAP.md`
- Schema evolution documentation
- Model consistency analysis

---

### Task 1.5.4: Re-audit MCP and Adapters Modules

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QT7`
**Type:** research | **Complexity:** medium | **Priority:** medium

#### Description
Re-audit the MCP server module and platform adapters. Check for new tools, resources, and prompts added since Dec 12.

#### Scope - MCP
```
vibey/mcp/
├── __init__.py
├── server.py           # Main MCP server
├── tools/              # MCP tools (76 total)
├── resources/          # MCP resources (8)
├── prompts/            # MCP prompts (4)
└── handlers/
```

#### Scope - Adapters
```
vibey/adapters/
├── __init__.py
├── base.py             # Base adapter
├── claude_code.py
├── cursor.py
├── copilot.py
├── vscode.py
├── goose.py
├── gemini.py
├── aider.py
├── continue_adapter.py
└── windsurf.py
```

#### Audit Checklist - MCP

**Tool Inventory:**
- [ ] Count current tools (should be ~76)
- [ ] Identify new tools since Dec 12
- [ ] Check tool documentation completeness
- [ ] Verify tool input/output schemas

**Resource Inventory:**
- [ ] Count current resources
- [ ] Verify resource content accuracy

**Prompt Inventory:**
- [ ] Count current prompts
- [ ] Review prompt quality

#### Audit Checklist - Adapters

**Adapter Consistency:**
- [ ] All 9 adapters present?
- [ ] Consistent interface implementation?
- [ ] Consistent error handling?

#### Deliverables
- Updated `MODULE_QUALITY_AUDIT_MCP.md`
- Updated `MODULE_QUALITY_AUDIT_ADAPTERS.md`
- Tool/resource inventory update

---

### Task 1.5.5: Re-audit Common and Services Modules

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QT8`
**Type:** research | **Complexity:** medium | **Priority:** medium

#### Description
Re-audit the common utilities module and any new services modules. Check for new error types, shared utilities, and service implementations.

#### Scope - Common
```
vibey/common/
├── __init__.py
├── errors.py           # Custom exceptions
├── config.py           # Configuration
├── utils.py            # Utilities
└── ...
```

#### Scope - Services (NEW)
```
vibey/services/
├── __init__.py
├── implementation/     # Implementation mode
│   ├── __init__.py
│   ├── loop.py
│   ├── selector.py
│   └── completion.py
└── ...
```

#### Audit Checklist

**Common Module:**
- [ ] Error hierarchy completeness
- [ ] Utility function documentation
- [ ] Configuration management patterns

**Services Module:**
- [ ] New module structure documentation
- [ ] Service interface patterns
- [ ] Integration with operations layer

#### Deliverables
- Updated `MODULE_QUALITY_AUDIT_COMMON.md`
- New `MODULE_QUALITY_AUDIT_SERVICES.md`
- Error catalog update

---

### Task 1.5.6: Generate Cross-Module Dependency Analysis

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QT9`
**Type:** research | **Complexity:** complex | **Priority:** medium

**See:** `sprints/sprint-1.5/tasks/task-1.5.6-cross-module/TASK_PLAN.md`

#### Description
Generate an updated cross-module dependency analysis showing how modules depend on each other. Create a coupling matrix and identify any circular dependencies or tight coupling issues.

#### Expected Output

**Coupling Matrix:**
```
            cli  ops  roadmap  mcp  adapters  common  services
cli          -    H      H      L      L        M        M
operations   L    -      H      L      L        H        M
roadmap      L    M      -      L      L        H        L
mcp          M    H      H      -      L        M        L
adapters     L    L      L      L      -        M        L
common       L    L      L      L      L        -        L
services     M    H      H      L      L        M        -

H = High coupling (>10 imports)
M = Medium coupling (5-10 imports)
L = Low coupling (<5 imports)
```

#### Analysis Points
- Identify modules with highest coupling
- Find circular dependency chains
- Detect layering violations (e.g., common importing cli)
- Compare with Dec 12 coupling metrics

#### Deliverables
- `CROSS_MODULE_DEPENDENCY_ANALYSIS.md`
- Coupling matrix visualization
- Architectural recommendations

---

## Sprint Execution Order

```
Sprint 1 (complete) ─────> Task 1.5.1 (CLI)
                     ├──> Task 1.5.2 (Operations)
                     ├──> Task 1.5.3 (Roadmap)
                     ├──> Task 1.5.4 (MCP/Adapters)
                     └──> Task 1.5.5 (Common/Services)

Tasks 1.5.1-1.5.5 ──────> Task 1.5.6 (Cross-Module Analysis)
```

## Output Location

All deliverables should be placed in:
```
.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-1.5/outputs/
```

## Success Criteria

- [ ] All 6 tasks completed
- [ ] All 7 module categories audited (CLI, Ops, Roadmap, MCP, Adapters, Common, Services)
- [ ] Quality metrics compared with Dec 12 baseline
- [ ] Cross-module coupling analyzed
- [ ] Recommendations documented
- [ ] No blocking issues found or documented
