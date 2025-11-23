# Directory Consolidation Audit

**Date:** 2025-11-23
**Auditor:** Claude Code
**Status:** Sprint 1 - Analysis Complete

---

## Executive Summary

| Metric | vibey/ | framework/ |
|--------|--------|------------|
| Python files | 216 | 143 |
| Markdown files | 0 | 95 |
| Total size | ~2.5MB | ~5.3MB |

**Key Finding:** Massive duplication exists between directories. Approximately 60-70% of framework/ Python code is duplicated in vibey/.

---

## 1. VIBEY/ DIRECTORY ANALYSIS

### 1.1 Core Package Structure (KEEP - This is the authoritative package)

```
vibey/
├── __init__.py           # Package init
├── __main__.py           # Entry point
├── adapters/             # Platform adapters (40 files)
├── cli/                  # CLI commands (140 files)
├── common/               # Shared utilities (3 files)
├── config/               # Configuration (5 files)
├── operations/           # Business logic (22 files)
├── platform/             # Platform detection (5 files)
└── roadmap/              # Roadmap models (35 files)
```

### 1.2 Adapters (vibey/adapters/) - KEEP

| Adapter | Files | Purpose | Status |
|---------|-------|---------|--------|
| base.py | 1 | Base adapter class | Keep |
| aider.py | 1 | Aider platform | Keep |
| amazonq/ | 2 | Amazon Q platform | Keep |
| claude_code.py | 1 | Claude Code platform | Keep |
| cody/ | 2 | Sourcegraph Cody | Keep |
| continuedev/ | 4 | Continue.dev | Keep |
| copilot/ | 2 | GitHub Copilot | Keep |
| cursor/ | 2 | Cursor IDE | Keep |
| gemini/ | 12 | Gemini Code Assist | Keep |
| goose.py | 1 | Goose platform | Keep |
| jetbrains/ | 2 | JetBrains AI | Keep |
| replit/ | 2 | Replit | Keep |
| vscode/ | 2 | VS Code | Keep |
| windsurf/ | 2 | Windsurf | Keep |

### 1.3 CLI (vibey/cli/) - KEEP (with cleanup)

**Core files (KEEP):**
- main.py - Main CLI entry point
- commands.py - Command implementations
- deploy.py - Deployment commands
- formatters.py - Output formatting
- config_migrate.py, config_utils.py - Config helpers
- roadmap_errors.py - Error handling

**Standalone scripts (REVIEW - may be legacy):**
- analyze-project-roadmap.py
- check-version.py
- generate-*.py (4 files)
- migrate-*.py (5 files)
- roadmap-*.py (8 files)
- rollback-framework.py
- update-config.py
- validate-*.py (3 files)

**Subdirectories:**
- roadmap_commands/ (20 files) - KEEP
- roadmap_lib/ (14 files) - KEEP
- roadmap-lib/ (14 files) - **DUPLICATE of roadmap_lib/ - DELETE**
- tests/ (12 files) - KEEP

### 1.4 Operations (vibey/operations/) - KEEP

- config/ - Config operations
- migrations/ - Data migrations
- roadmap/ - Roadmap operations (17 files)
- validate/ - Validation operations (3 files - just added)

### 1.5 Roadmap (vibey/roadmap/) - KEEP

- models/ - Data models (8 files)
- serialization/ - YAML load/save (3 files)
- standards/ - Standards system (8 files)
- validation/ - Validators (3 files)
- Various utilities (12 files)

---

## 2. FRAMEWORK/ DIRECTORY ANALYSIS

### 2.1 Content Files (KEEP IN FRAMEWORK/)

```
framework/
├── agents/           # 20 markdown files - KEEP
│   ├── core/         # coordinator.md, vibey-manager.md
│   ├── planning/     # sprint-planning.md, researcher.md
│   ├── development/  # web-developer.md, ml-engineer.md, etc.
│   ├── quality/      # security-reviewer.md, test-engineer.md, etc.
│   ├── documentation/# docs-writer.md, diagram-engineer.md, etc.
│   └── architecture/ # architecture-agent.md
├── workflows/        # 16 markdown files - KEEP
│   └── planning/     # sprint-planning.md, codebase-audit.md, etc.
└── templates/        # 23 markdown files - KEEP
    └── handoffs/     # Agent handoff templates
```

### 2.2 Python Code (MOVE TO VIBEY/ OR DELETE)

#### 2.2.1 framework/adapters/ - PARTIALLY REDUNDANT

| File | Purpose | Action |
|------|---------|--------|
| __init__.py | Adapter registry exports | MOVE (used by imports) |
| base.py | Base adapter class | REDUNDANT with vibey/adapters/base.py |
| registry.py | Adapter registry | MOVE to vibey/adapters/ |
| types.py | Type definitions | MOVE to vibey/adapters/ |
| goose/ | Goose adapter | CHECK vs vibey/adapters/goose.py |
| mcp/ | MCP adapter | MOVE to vibey/adapters/ |

#### 2.2.2 framework/mcp/ - MOVE TO VIBEY/

**This is actively used and NOT duplicated in vibey/:**

| Path | Purpose | Action |
|------|---------|--------|
| server.py | MCP server implementation | MOVE to vibey/mcp/ |
| discovery/ | Agent/workflow discovery | MOVE to vibey/mcp/ |
| tools/ | MCP tool implementations | MOVE to vibey/mcp/ |
| adapters/ | Roadmap adapter for MCP | MOVE to vibey/mcp/ |
| utils/ | Error handling, validation | MOVE to vibey/mcp/ |
| resources/, prompts/ | Empty/minimal | MOVE or DELETE |
| tests/ | MCP tests | MOVE to tests/mcp/ |

#### 2.2.3 framework/docs/ - MOVE TO VIBEY/

| File | Purpose | Action |
|------|---------|--------|
| generator.py | Doc generation | MOVE to vibey/operations/docs/ |
| sync_engine.py | Doc sync engine | MOVE to vibey/operations/docs/ |
| sync_hooks.py | Sync triggers | MOVE to vibey/operations/docs/ |
| sync_manifest.py | Sync state tracking | MOVE to vibey/operations/docs/ |

#### 2.2.4 framework/roadmap/ - FULLY REDUNDANT

**Every file has a duplicate in vibey/roadmap/:**

| framework/roadmap/ | vibey/roadmap/ | Action |
|--------------------|----------------|--------|
| models/*.py | models/*.py | DELETE framework version |
| serialization/*.py | serialization/*.py | DELETE framework version |
| validation/*.py | validation/*.py | DELETE framework version |
| context_loader.py | context_loader.py | DELETE framework version |
| directory_manager.py | directory_manager.py | DELETE framework version |
| id_generator.py | id_generator.py | DELETE framework version |
| markdown_generator.py | markdown_generator.py | DELETE framework version |
| summary_generator.py | summary_generator.py | DELETE framework version |
| toc_generator.py | toc_generator.py | DELETE framework version |
| test_*.py | test_*.py | DELETE framework version |

#### 2.2.5 framework/platform_adapters/ - REDUNDANT/LEGACY

| File | Purpose | Action |
|------|---------|--------|
| base.py | Legacy base adapter | DELETE (superseded by vibey/adapters/base.py) |
| claude_adapter.py | Legacy Claude adapter | DELETE (superseded) |
| registry.py | Legacy registry | DELETE (superseded) |

#### 2.2.6 framework/scripts/ - FULLY REDUNDANT

**This entire directory (42 files, 1.5MB) duplicates vibey/cli/:**

| framework/scripts/ | vibey/cli/ | Action |
|--------------------|------------|--------|
| roadmap_commands/*.py | roadmap_commands/*.py | DELETE |
| roadmap-lib/*.py | roadmap_lib/*.py | DELETE |
| tests/*.py | tests/*.py | DELETE |
| *.py (standalone) | *.py (standalone) | DELETE |

#### 2.2.7 framework/config/ - KEEP (config templates)

Contains config-templates/ with example YAML files. Keep as reference.

#### 2.2.8 framework/schemas/ - REVIEW

JSON schemas - may be useful for validation. Review necessity.

#### 2.2.9 framework/examples/ - REVIEW

Sample roadmap structure - may be useful for documentation.

---

## 3. REDUNDANCY MATRIX

### 3.1 Exact Duplicates (DELETE framework/ version)

| vibey/ location | framework/ location | Files |
|-----------------|---------------------|-------|
| cli/roadmap_commands/ | scripts/roadmap_commands/ | 20 |
| cli/roadmap_lib/ | scripts/roadmap-lib/ | 14 |
| cli/roadmap-lib/ | scripts/roadmap-lib/ | 14 (also dup in vibey!) |
| roadmap/models/ | roadmap/models/ | 7 |
| roadmap/serialization/ | roadmap/serialization/ | 3 |
| roadmap/*.py | roadmap/*.py | 8 |
| cli/*.py (standalone) | scripts/*.py | ~20 |

**Total redundant files: ~86 files**

### 3.2 Unique to framework/ (MOVE to vibey/)

| framework/ location | Target vibey/ location | Files |
|---------------------|------------------------|-------|
| mcp/server.py | mcp/server.py | 1 |
| mcp/discovery/ | mcp/discovery/ | 5 |
| mcp/tools/ | mcp/tools/ | 4 |
| mcp/adapters/ | mcp/adapters/ | 2 |
| mcp/utils/ | mcp/utils/ | 3 |
| adapters/registry.py | adapters/registry.py | 1 |
| adapters/types.py | adapters/types.py | 1 |
| docs/*.py | operations/docs/ | 4 |

**Total files to move: ~21 files**

### 3.3 Internal vibey/ Duplication

| Location 1 | Location 2 | Action |
|------------|------------|--------|
| cli/roadmap_lib/ | cli/roadmap-lib/ | DELETE roadmap-lib/ |

---

## 4. IMPORT DEPENDENCY ANALYSIS

### 4.1 Files importing from framework.*

```
31 files in vibey/ import from framework
12 files in tests/ import from framework
~15 files in framework/ import from framework (self-references)
```

### 4.2 Critical Import Paths

| Import | Used By | Required Action |
|--------|---------|-----------------|
| framework.mcp.server | tests, CLI | Move to vibey.mcp.server |
| framework.mcp.discovery | adapters, tests | Move to vibey.mcp.discovery |
| framework.adapters | CLI main.py | Move registry to vibey.adapters |
| framework.roadmap.models | framework scripts | Will be deleted with scripts |
| framework.platform_adapters | framework scripts | Will be deleted with scripts |

---

## 5. MIGRATION PLAN

### Phase 1: Internal Cleanup (Low Risk)
1. Delete vibey/cli/roadmap-lib/ (duplicate of roadmap_lib/)
2. Delete framework/scripts/ entirely (1.5MB, 42 files)
3. Delete framework/roadmap/ entirely (redundant)
4. Delete framework/platform_adapters/ (legacy)

### Phase 2: Move Unique Code (Medium Risk)
1. Move framework/mcp/ → vibey/mcp/
2. Move framework/adapters/registry.py → vibey/adapters/
3. Move framework/adapters/types.py → vibey/adapters/
4. Move framework/docs/*.py → vibey/operations/docs/

### Phase 3: Update Imports (High Risk)
1. Update all `from framework.mcp` → `from vibey.mcp`
2. Update all `from framework.adapters` → `from vibey.adapters`
3. Update all `from framework.docs` → `from vibey.operations.docs`
4. Run full test suite after each change

### Phase 4: Final Cleanup
1. Delete framework/adapters/ (after move)
2. Delete framework/docs/ (after move)
3. Verify framework/ only contains content (agents/, workflows/, templates/)
4. Update documentation

---

## 6. RISK ASSESSMENT

| Risk | Severity | Mitigation |
|------|----------|------------|
| Breaking MCP server | HIGH | Move carefully, test thoroughly |
| Breaking CLI | MEDIUM | Most code already in vibey/ |
| Breaking tests | MEDIUM | Update imports incrementally |
| Breaking adapters | LOW | Adapters already in vibey/ |

---

## 7. ESTIMATED EFFORT

| Phase | Files | Estimated Time |
|-------|-------|----------------|
| Phase 1 | ~100 deletions | 1-2 hours |
| Phase 2 | ~25 moves | 2-3 hours |
| Phase 3 | ~50 import updates | 3-4 hours |
| Phase 4 | Cleanup + testing | 2-3 hours |

**Total: 8-12 hours of focused work**

---

## 8. TARGET STATE

### framework/ (Content Only)
```
framework/
├── agents/           # 20 agent definition markdown files
│   ├── core/
│   ├── planning/
│   ├── development/
│   ├── quality/
│   ├── documentation/
│   └── architecture/
├── workflows/        # 16 workflow markdown files
│   └── planning/
├── templates/        # 23 template markdown files
│   └── handoffs/
└── config/           # Config templates (optional)
    └── config-templates/
```

### vibey/ (All Python Code)
```
vibey/
├── adapters/         # All platform adapters + registry
├── cli/              # CLI commands
├── common/           # Shared utilities
├── config/           # Configuration
├── mcp/              # MCP server + discovery (NEW)
├── operations/       # Business logic + docs sync
├── platform/         # Platform detection
└── roadmap/          # Models + serialization
```
