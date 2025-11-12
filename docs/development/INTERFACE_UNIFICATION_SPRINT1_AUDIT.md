# Interface Unification Sprint 1 - Pre-Deletion Audit

**Date:** 2025-11-12
**Sprint:** interface-unification-1
**Purpose:** Audit all files before deletion to ensure no unique functionality is lost

---

## Files to Delete

### Slash Commands (framework/commands/)

| File | Lines | Purpose | Unique Functionality? |
|------|-------|---------|----------------------|
| vibey.md | 1,454 | Main menu & initialization | ❌ No - UX design preserved in USER_JOURNEY_DESIGN.md |
| vibey-plan.md | 336 | Sprint planning workflow | ❌ No - UX design preserved, logic in CLI |
| vibey-code.md | 1,095 | Sprint execution workflow | ❌ No - UX design preserved, logic in CLI |
| vibey-think.md | 765 | Discovery mode workflow | ❌ No - UX design preserved, audit tools exist |
| vibey-manage.md | 617 | Framework management | ❌ No - Config management in CLI |
| vibey-audit.md | 122 | Project audit workflow | ❌ No - Audit logic available separately |

**Total:** 4,389 lines
**Decision:** ✅ Safe to delete - all UX design preserved in USER_JOURNEY_DESIGN.md

---

## Standalone Scripts Analysis

### Scripts with CLI Equivalents (Safe to Delete)

| Script | CLI Equivalent | Status |
|--------|----------------|--------|
| roadmap-init.py | `vibey roadmap init` | ✅ CLI complete |
| roadmap-update.py | `vibey roadmap start/complete` | ✅ CLI complete |
| roadmap-query.py | `vibey roadmap show` | ✅ CLI complete |
| roadmap-summarize.py | `vibey roadmap summarize` | ✅ CLI complete |
| roadmap-add-commit.py | `vibey roadmap add-commit` | ✅ CLI complete |
| validate-config.py | `vibey config validate` | ✅ CLI complete |
| config_migrate.py | `vibey config migrate` | ✅ CLI complete |
| rollback-framework.py | `vibey config rollback` | ✅ CLI complete |
| deploy.py | `vibey deploy run` | ✅ CLI complete |
| docs.py | `vibey docs generate` | ✅ CLI complete |

### Scripts Needing Review

Need to check if these have unique functionality not in CLI:

1. **generate-config.py** - Config generation from templates
2. **update-config.py** - Update nested config values
3. **render-template.py** - Jinja2 template rendering
4. **manage-project-context.py** - PROJECT-CONTEXT.md lifecycle
5. **check-version.py** - Version checking
6. **generate-agent.py** - Agent template generation
7. **analyze-project-roadmap.py** - Roadmap analysis
8. **generate-roadmap-docs.py** - Generate roadmap documentation
9. **roadmap-sync-docs.py** - Sync roadmap with docs
10. **roadmap-context.py** - Get task context
11. **roadmap-prepare.py** - Prepare roadmap
12. **roadmap-create-from-plan.py** - Create roadmap from plan
13. **validate-roadmap-format.py** - Validate roadmap YAML
14. **config_utils.py** - Config utility functions
15. **migrate-*.py** (4 files) - Data migration scripts

### Test/Development Scripts (Can Delete)

These are test utilities, not user-facing:
- test_adapter_conceptual.py
- test_claude_adapter.py

---

## Audit Results

### ✅ SAFE TO DELETE (No Unique Functionality)

**All slash commands (4,389 lines):**
- Procedural instructions for AI
- UX design preserved in USER_JOURNEY_DESIGN.md
- No executable logic
- No data transformations

**Standalone scripts with CLI equivalents (10 scripts):**
- roadmap-init.py
- roadmap-update.py
- roadmap-query.py
- roadmap-summarize.py
- roadmap-add-commit.py
- validate-config.py
- config_migrate.py
- rollback-framework.py
- deploy.py
- docs.py

**Test/dev scripts (2 scripts):**
- test_adapter_conceptual.py
- test_claude_adapter.py

**Total safe to delete:** 12 scripts + 6 slash commands

---

## ⚠️ NEEDS INVESTIGATION (Possibly Unique Functionality)

These 15 scripts may have functionality not yet in CLI:

1. **generate-config.py** - Template-based config generation
2. **update-config.py** - Nested config value updates
3. **render-template.py** - Jinja2 rendering
4. **manage-project-context.py** - Context lifecycle
5. **check-version.py** - Version checking
6. **generate-agent.py** - Agent scaffolding
7. **analyze-project-roadmap.py** - Analysis tools
8. **generate-roadmap-docs.py** - Doc generation
9. **roadmap-sync-docs.py** - Doc syncing
10. **roadmap-context.py** - Context extraction
11. **roadmap-prepare.py** - Preparation logic
12. **roadmap-create-from-plan.py** - Plan parsing
13. **validate-roadmap-format.py** - Format validation
14. **config_utils.py** - Shared utilities
15. **migrate-*.py** (4 files) - Migration scripts

**Next Step:** Audit each of these 15 files to determine if functionality exists in CLI or needs to be added.

---

## Investigation Plan

For each of the 15 scripts above:

1. **Read script** - Understand what it does
2. **Check CLI** - Does CLI have this functionality?
3. **Decision:**
   - If CLI has it → Mark for deletion
   - If CLI doesn't → Add to CLI or mark as utility
   - If migration script → Delete (one-time use)
   - If utility function → Move to shared library if needed

---

## REVISED FINDINGS

### Critical Discovery: CLI Uses Standalone Scripts!

The CLI `commands.py` uses `run_script()` to delegate to standalone scripts. This means:
- CLI is a **thin wrapper** around scripts (not duplicate functionality)
- Scripts provide the actual implementation
- Cannot simply delete scripts without breaking CLI

### Scripts Used by CLI (MUST KEEP OR REFACTOR)

| Script | Used By | Command |
|--------|---------|---------|
| roadmap-init.py | CLI | `vibey roadmap init` |
| roadmap-query.py | CLI | `vibey roadmap status/show` |
| roadmap-update.py | CLI | `vibey roadmap start/complete` |
| roadmap-context.py | CLI | `vibey roadmap context` |
| roadmap-summarize.py | CLI | `vibey roadmap summarize` |
| roadmap-add-commit.py | CLI | `vibey roadmap add-commit` |
| validate-roadmap-format.py | CLI | `vibey roadmap validate` |
| deploy.py | CLI | `vibey deploy run` |
| docs.py | CLI | `vibey docs generate` |
| config_migrate.py | CLI | `vibey config migrate` |
| generate-config.py | CLI | `config_generate_cmd()` |
| update-config.py | CLI | `config_update_cmd()` |
| migrate-*.py (3 files) | CLI | Migration commands |

**Total:** 15 scripts actively used by CLI

### Safe to Delete Immediately

1. **Slash commands (6 files, 4,389 lines)** - Just text instructions, no code
2. **Test scripts (2 files)** - Development utilities
   - test_adapter_conceptual.py
   - test_claude_adapter.py

**Total safe to delete now:** 8 files

### Refactoring Strategy for Remaining Scripts

**Option A: Keep Scripts (Quick - This Sprint)**
- Keep 15 scripts as internal implementation
- CLI continues to call via `run_script()`
- Focus on deleting slash commands only
- Document scripts as "internal utilities"

**Option B: Refactor to Functions (Longer - Next Sprint)**
- Convert scripts to importable modules
- CLI calls functions directly (no subprocess)
- Move to `vibey/core/` or `vibey/operations/`
- Better error handling and testing

**Recommendation:** Option A for Sprint 1, Option B for Sprint 2

## Revised Sprint 1 Plan

### What We'll Delete Now

1. ✅ **All slash commands** (framework/commands/*.md) - 4,389 lines
2. ✅ **Test scripts** (2 files)
3. ✅ **Dead code cleanup** (imports, references)

### What We'll Keep (For Now)

1. ⏸️ **Functional standalone scripts** (15 files) - CLI depends on them
2. ⏸️ **Migration scripts** - Used by CLI migrate commands

### What We'll Refactor (Sprint 2)

1. 🔄 Convert `run_script()` calls to function imports
2. 🔄 Move scripts to proper modules (`vibey/operations/`)
3. 🔄 Improve error handling
4. 🔄 Add proper testing

## Status

- ✅ Slash commands audited (safe to delete)
- ✅ Standalone scripts audited (CLI dependencies found)
- ✅ Revised plan created
- ⏳ Ready to execute deletions

**Next:** Delete slash commands and test scripts, update documentation.
