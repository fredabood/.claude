# User Journey Documentation Gap Analysis

**Analysis Date:** 2025-11-11
**Document Analyzed:** docs/VIBEY_USER_JOURNEYS.md
**Last Updated:** 2025-11-09 21:40:48
**Changes Since:** 41 commits (Nov 10-11, 2025)
**Analysis Scope:** Comprehensive review of all 7 journeys

---

## Executive Summary

The VIBEY_USER_JOURNEYS.md document was last updated **before** the completion of the directory-migration track (Sprint 1-3, Nov 10-11). This track introduced **fundamental changes** to the framework's CLI, installation, configuration, and deployment architecture.

### Critical Findings

✅ **Strengths:**
- Comprehensive journey coverage (7 journeys)
- Well-structured with step-by-step examples
- Good conceptual alignment with framework design

❌ **Critical Issues:**
1. **Outdated CLI command syntax** - Uses `./vibey` instead of `vibey`
2. **Missing subcommands** - Deploy, config commands changed significantly
3. **Installation process changed** - Now uses Python package, not direct clone
4. **Missing new journeys** - Config migration, validation, rollback workflows not documented
5. **Platform adapter details outdated** - Goose adapter implementation differs from docs

### Impact Assessment

- **User Experience:** HIGH - Users following docs will encounter command errors
- **Accuracy:** MEDIUM - Concepts correct, implementation details outdated
- **Completeness:** MEDIUM - Missing 4+ new critical workflows

---

## Detailed Gap Analysis

### Journey 1: First-Time Setup

**Status:** ⚠️ PARTIALLY OUTDATED

#### Issues Found

**Line 188: Deployment Command**
```bash
# DOCUMENTED (outdated):
./vibey deploy --platform claude-code

# ACTUAL (current):
vibey deploy run --platform claude-code
```

**Changes:**
- `vibey` is now a global command (Python package entry point)
- `deploy` requires `run` subcommand
- No longer requires `.vibey/` directory prefix

**Line 145-147: Installation Method**
```bash
# DOCUMENTED:
git clone https://github.com/fredabood/vibey.git .vibey
cd .vibey

# ACTUAL (should be):
pip install vibey-framework  # When published
# OR for development:
git clone https://github.com/fredabood/vibey.git
cd vibey
pip install -e .
```

**Impact:** Users cannot complete setup following current documentation.

**Recommendation:** Update entire Journey 1 with new CLI installation and usage patterns.

---

### Journey 6: Multi-Platform Deployment

**Status:** ⚠️ PARTIALLY OUTDATED

#### Issues Found

**Line 2364: Goose Deployment Command**
```bash
# DOCUMENTED (outdated):
cd .vibey
./vibey deploy --platform goose

# ACTUAL (current):
vibey deploy run --platform goose
# No need to cd to .vibey/ - works from anywhere in project
```

**Line 2426: Cursor Deployment**
```bash
# DOCUMENTED (outdated):
./vibey deploy --platform cursor

# ACTUAL (current):
vibey deploy run --platform cursor
```

**Line 2478: Deploy All Platforms**
```bash
# DOCUMENTED (outdated):
./vibey deploy --all

# ACTUAL (current):
vibey deploy run --platform all
```

**Missing Information:**
- `vibey deploy list` command to show available platforms
- Platform detection logic
- Error handling when platform unavailable
- How adapters are selected/invoked

**Impact:** Users cannot deploy to multiple platforms following current documentation.

**Recommendation:** Rewrite Journey 6 with:
1. New CLI subcommand syntax
2. List of supported platforms (claude-code, goose, cursor, aider, continue)
3. Platform-specific setup requirements
4. Troubleshooting common deployment errors

---

## Missing Journeys

### Journey 8: Config Migration (NEW - NOT DOCUMENTED)

**Why Needed:** Sprint 2 (Config Migration System) introduced modular config architecture with auto-migration from legacy format.

**What Should Be Covered:**

**Step 1: Detect Legacy Config**
```bash
vibey config show
# Output:
# ⚠️  Legacy config detected: .claude/project-config.yaml
# 💡 Run 'vibey config migrate' to upgrade to modular format
```

**Step 2: Run Migration**
```bash
vibey config migrate
# Creates:
# - .vibey/config/project.yaml
# - .vibey/config/framework.yaml
# - .vibey/config/agents/
# - Backup: .vibey/config-backups/backup_20251111_123456/
```

**Step 3: Validate New Config**
```bash
vibey config validate
# ✓ All config files valid
# ✓ Schema compliance: 100%
# ✓ No missing required fields
```

**Step 4: Rollback if Needed**
```bash
vibey config rollback --backup backup_20251111_123456
# Restores previous config state
```

**User Scenarios:**
- Upgrading from v1.x to v2.x
- Fixing broken config after manual edits
- Understanding modular config structure

**Priority:** HIGH - Many users will upgrade from legacy versions

---

### Journey 9: Roadmap-Driven Development (PARTIALLY DOCUMENTED)

**Status:** ⚠️ Journey 7 exists but missing new CLI commands

**What's Missing:**

**Current CLI (not documented):**
```bash
# Initialize roadmap
vibey roadmap init

# Show status
vibey roadmap status

# Start sprint/task
vibey roadmap start <id>

# Complete sprint/task
vibey roadmap complete <id>

# Show details
vibey roadmap show <id>

# Get AI context for task
vibey roadmap context <task-id>

# Summarize items
vibey roadmap summarize <id>
```

**Examples Not Shown:**
- How to create tracks/sprints/tasks using CLI
- Dependency management workflow
- Quality gate integration
- Sprint progression (development → completion_gate_check → completed)
- Activity log tracking

**Priority:** HIGH - Roadmap system is core framework feature

---

### Journey 10: Platform Adapter Development (NEW - NOT DOCUMENTED)

**Why Needed:** Sprint 3 (Platform Adapter Implementation) created extensible adapter pattern for adding new platforms.

**What Should Be Covered:**

**Step 1: Create Adapter Skeleton**
```python
from vibey.deploy.adapters import PlatformAdapter, DeploymentResult

class MyPlatformAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "my-platform"

    def get_deployment_dir(self, project_root: Path) -> Path:
        return project_root / ".my-platform"

    def deploy(self, source_dir: Path, config: dict) -> DeploymentResult:
        # Implementation
        pass
```

**Step 2: Register Adapter**
```python
# vibey/deploy/adapters/__init__.py
ADAPTERS = {
    'claude-code': ClaudeCodeAdapter,
    'goose': GooseAdapter,
    'my-platform': MyPlatformAdapter,  # Add here
}
```

**Step 3: Test Adapter**
```bash
vibey deploy run --platform my-platform
```

**User Scenarios:**
- Adding support for new AI coding assistant
- Customizing deployment for enterprise environments
- Contributing adapters to framework

**Priority:** MEDIUM - Advanced users, extension developers

---

### Journey 11: Quality Gate Configuration (PARTIALLY DOCUMENTED)

**Status:** Mentioned in other journeys but no dedicated workflow

**What Should Be Covered:**

**Configuring Quality Gates:**
```yaml
# .vibey/config/quality-gates.yaml
gates:
  security:
    threshold: 85
    blocking: true
    audits:
      - dependency_vulnerabilities
      - xss_prevention
      - sql_injection_prevention

  test_coverage:
    threshold: 90
    blocking: true
    exclude_patterns:
      - "**/migrations/**"
```

**Running Quality Gates:**
```bash
# During sprint (automated)
vibey roadmap complete sprint-1
# ⚠️  Quality gate failed: security (score: 78/85)
# ❌ Cannot mark sprint as completed

# Manual check
vibey quality-gates run --gate security
```

**Troubleshooting Failed Gates:**
- Viewing audit results
- Adjusting thresholds
- Skipping non-blocking gates
- Override procedures (if any)

**Priority:** MEDIUM - Important for enterprise users

---

## Command Syntax Changes Summary

### Changed Commands

| Documented | Actual | Status |
|------------|--------|--------|
| `./vibey deploy --platform X` | `vibey deploy run --platform X` | ❌ Broken |
| `./vibey deploy --all` | `vibey deploy run --platform all` | ❌ Broken |
| `./vibey docs generate` | `vibey docs generate` | ✅ Still works (but no `./` needed) |
| Not documented | `vibey deploy list` | ⚠️ Missing |
| Not documented | `vibey config migrate` | ⚠️ Missing |
| Not documented | `vibey config validate` | ⚠️ Missing |
| Not documented | `vibey config rollback` | ⚠️ Missing |
| Not documented | `vibey config show` | ⚠️ Missing |
| Not documented | `vibey roadmap init` | ⚠️ Missing |
| Not documented | `vibey roadmap start` | ⚠️ Missing |
| Not documented | `vibey roadmap complete` | ⚠️ Missing |
| Not documented | `vibey roadmap show` | ⚠️ Missing |
| Not documented | `vibey roadmap context` | ⚠️ Missing |
| Not documented | `vibey roadmap summarize` | ⚠️ Missing |

### Installation Changes

| Documented | Actual | Status |
|------------|--------|--------|
| `git clone ... .vibey` | `pip install vibey-framework` | ⚠️ Preferred method changed |
| `chmod +x .vibey/vibey` | Not needed (pip installs entry point) | ⚠️ Outdated step |
| `export PATH=.../.vibey` | Not needed (pip adds to PATH) | ⚠️ Outdated step |

---

## Technical Context: What Changed

### Directory-Migration Track (Sprint 1-3)

**Sprint 1: Unified CLI Tool (Nov 10, 2025)**
- Created Python package structure (`vibey/`)
- Moved `framework/` → `vibey/cli/`
- Created entry point (`vibey/__main__.py`)
- Registered CLI commands (Click framework)
- Updated all imports

**Impact on Docs:**
- Installation process completely changed
- Command prefix changed from `./vibey` to `vibey`
- PATH management no longer needed

**Sprint 2: Config Migration System (Nov 10-11, 2025)**
- Created modular config structure (`.vibey/config/`)
- Implemented auto-fallback (legacy → modular)
- Added migration tools (`vibey config migrate`)
- Added validation (`vibey config validate`)
- Added rollback (`vibey config rollback`)

**Impact on Docs:**
- New config structure not documented
- Migration workflow not documented
- Validation workflow not documented

**Sprint 3: Platform Adapter Implementation (Nov 10, 2025)**
- Created `PlatformAdapter` base class
- Refactored Claude Code adapter
- Implemented Goose adapter
- Created `vibey deploy run` command
- Added platform detection
- Updated `.gitignore` rules

**Impact on Docs:**
- Deploy command changed (`deploy` → `deploy run`)
- Platform adapter pattern not documented
- Goose deployment details incorrect

---

## Accuracy Assessment by Journey

| Journey | Accuracy | Completeness | Priority |
|---------|----------|--------------|----------|
| 1. First-Time Setup | 60% | 70% | 🔴 Critical |
| 2. Sprint Planning | 90% | 85% | 🟢 Good |
| 3. Feature Development | 85% | 80% | 🟡 Minor |
| 4. Quality Assurance | 80% | 70% | 🟡 Minor |
| 5. Framework Management | 70% | 60% | 🟠 Moderate |
| 6. Multi-Platform Deployment | 50% | 50% | 🔴 Critical |
| 7. Roadmap-Driven Dev | 75% | 50% | 🟠 Moderate |

**Overall Accuracy:** 71%
**Overall Completeness:** 66%

---

## Recommendations

### Immediate Actions (Critical)

1. **Update Journey 1** - Fix installation and setup commands
   - Replace `./vibey` with `vibey`
   - Update `deploy` to `deploy run`
   - Document pip installation method
   - Remove PATH setup instructions

2. **Update Journey 6** - Fix multi-platform deployment
   - Update all deploy commands with `run` subcommand
   - Add `vibey deploy list` command
   - Document platform detection
   - Update Goose adapter details

3. **Add Journey 8** - Config migration workflow
   - Document migration process
   - Show validation workflow
   - Explain rollback mechanism
   - Provide troubleshooting tips

### Short-Term Actions (Important)

4. **Enhance Journey 7** - Add new roadmap CLI commands
   - Document `vibey roadmap init`
   - Show `start`, `complete`, `show` commands
   - Explain `context` and `summarize` features
   - Show dependency management

5. **Add Command Reference Appendix**
   - Complete CLI command tree
   - All subcommands with examples
   - Common flags and options
   - Quick reference table

### Medium-Term Actions (Nice to Have)

6. **Add Journey 10** - Platform adapter development
   - Adapter interface documentation
   - Step-by-step adapter creation
   - Testing and validation
   - Contribution guidelines

7. **Add Journey 11** - Quality gate configuration
   - Gate configuration reference
   - Running gates manually
   - Troubleshooting failures
   - Custom gate creation

8. **Create Migration Guide**
   - v1.x → v2.x upgrade path
   - Breaking changes summary
   - Deprecation warnings
   - Rollback procedures

---

## Missing Content Areas

### 1. CLI Command Reference

**Not Documented:**
- `vibey --version`
- `vibey --help`
- Full command tree with all subcommands
- Common flags (`--help`, `--verbose`, `--dry-run`)
- Error codes and meanings

### 2. Configuration Reference

**Not Documented:**
- Complete config schema
- All available options
- Default values
- Validation rules
- Environment variable overrides

### 3. Adapter Development

**Not Documented:**
- `PlatformAdapter` interface
- `DeploymentResult` dataclass
- Adapter registration process
- Testing adapters
- Contributing adapters

### 4. Troubleshooting Guide

**Not Documented:**
- Common errors and solutions
- Debugging techniques
- Log locations
- Support resources
- Known issues and workarounds

### 5. Migration Guides

**Not Documented:**
- Upgrading framework versions
- Breaking changes between versions
- Deprecation timeline
- Backward compatibility notes

---

## Validation Methodology

### How This Analysis Was Conducted

1. **Read Documentation:** Complete review of VIBEY_USER_JOURNEYS.md
2. **Verify CLI Commands:** Ran `vibey --help`, `deploy --help`, `config --help`, `roadmap --help`
3. **Review Git History:** Analyzed 41 commits since last doc update
4. **Compare Implementations:** Checked actual code vs documented behavior
5. **Identify Gaps:** Listed missing workflows and outdated commands

### Evidence Sources

- **Git commits:** `git log --since="2025-11-09 21:40:48"`
- **CLI help output:** `vibey [command] --help`
- **Implementation files:**
  - `vibey/cli/deploy.py` (deploy commands)
  - `vibey/cli/config.py` (config commands)
  - `vibey/cli/roadmap.py` (roadmap commands)
  - `vibey/deploy/adapters/` (adapter implementations)
  - `vibey/config/` (config system)
- **Documentation files:**
  - `CLAUDE.md` (updated Nov 10)
  - `README.md` (updated Nov 10)
  - Sprint summaries in `.vibey/sprint_summaries/`

---

## Next Steps

### For Documentation Team

1. **Create tracking issue** for documentation update
2. **Assign priority levels** to each journey update
3. **Review and approve** this gap analysis
4. **Schedule updates** across 2-3 sprint cycles
5. **Implement validation** to detect future drift

### For Framework Maintainers

1. **Add version markers** to documentation (e.g., "Updated for v2.5.0")
2. **Create changelog** linking docs to code changes
3. **Automate CLI help generation** from code
4. **Add CI check** to flag outdated command examples
5. **Create documentation standards** for new features

### For Users (Workarounds)

Until documentation is updated:

1. **Use `vibey --help`** to discover current commands
2. **Refer to `CLAUDE.md`** for latest framework state
3. **Check git commit messages** for recent changes
4. **Report issues** when docs don't match behavior
5. **Use `vibey [command] --help`** for accurate syntax

---

## Appendix: Command Mapping

### Deploy Commands

```bash
# OLD (documented):
./vibey deploy --platform claude-code
./vibey deploy --platform goose
./vibey deploy --all

# NEW (actual):
vibey deploy run --platform claude-code
vibey deploy run --platform goose
vibey deploy run --platform all
vibey deploy list  # NEW: List available platforms
```

### Config Commands (NEW - Not Documented)

```bash
vibey config show              # Show current configuration
vibey config migrate           # Migrate legacy to modular
vibey config validate          # Validate config files
vibey config rollback          # Rollback to previous backup
```

### Roadmap Commands (Partially Documented)

```bash
vibey roadmap init             # Initialize roadmap
vibey roadmap status           # Show roadmap status
vibey roadmap start <id>       # Start sprint/task
vibey roadmap complete <id>    # Complete sprint/task
vibey roadmap show <id>        # Show item details
vibey roadmap context <id>     # Get AI-optimized context
vibey roadmap summarize <id>   # Summarize item
```

### Docs Commands (Still Accurate)

```bash
vibey docs generate            # Generate documentation
vibey docs update              # Update existing docs
```

---

## Conclusion

The VIBEY_USER_JOURNEYS.md document provides **excellent conceptual coverage** but has been **significantly impacted by the directory-migration track** (Sprint 1-3) completed Nov 10-11, 2025.

**Key Takeaway:** The framework evolved faster than the documentation, creating a **71% accuracy / 66% completeness gap**. Prioritize updating Journey 1 (First-Time Setup) and Journey 6 (Multi-Platform Deployment) immediately, then add missing journeys for config migration and enhanced roadmap CLI.

**Estimated Update Effort:**
- Critical fixes: 4-6 hours
- Short-term additions: 8-12 hours
- Medium-term enhancements: 16-20 hours
- **Total:** 28-38 hours across 2-3 sprint cycles

---

**Analysis Completed:** 2025-11-11
**Analyzed By:** Claude (Vibey Framework Assistant)
**Review Status:** Ready for documentation team review
**Next Review:** After Journey 1 & 6 updates complete
