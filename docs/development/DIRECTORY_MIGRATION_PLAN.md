# Directory Migration Plan: .claude/ → .vibey/

**Version:** 1.0
**Status:** Planning
**Created:** 2025-11-10
**Track:** directory-migration
**Priority:** CRITICAL (blocks multi-platform expansion)

---

## Executive Summary

This document outlines the comprehensive plan to migrate Vibey from a `.claude/`-centric deployment model to a platform-agnostic `.vibey/` source-of-truth architecture. This migration is **critical for multi-platform support** and must be completed before goose-port, cursor-port, and other platform ports can proceed.

**Current Problem:**
- Vibey v1.2.0 deploys framework files to `.claude/` (platform-specific)
- Only roadmap system lives in `.vibey/` (added in v2.0)
- Multi-platform expansion requires platform-agnostic source

**Target Solution:**
- `.vibey/` becomes single source of truth (platform-agnostic)
- `.claude/`, `.goose/`, `.cursor/` become generated deployment artifacts
- Framework portable across all AI coding assistants

**Timeline:** 6-8 weeks (3 sprints)
**Effort:** ~280-350 hours (2-3 developers)

---

## Current State Analysis

### Current Directory Structure (v1.2.0)

```
User's Project after /vibey deployment:
├── .claude/                          # ❌ Platform-specific deployment
│   ├── agents/                       # Framework agents (12 files)
│   ├── workflows/                    # Framework workflows (16 files)
│   ├── templates/                    # Handoff templates (22 files)
│   ├── commands/                     # Slash commands (vibey.md, etc.)
│   ├── scripts/                      # Python tooling (25+ scripts)
│   │   ├── roadmap                   # Roadmap CLI entry point
│   │   ├── roadmap-init.py
│   │   ├── roadmap-update.py
│   │   ├── generate-config.py
│   │   └── ... (20+ more scripts)
│   ├── config/                       # Config templates and schema
│   ├── docs/                         # Framework documentation
│   ├── CLAUDE.md                     # Generated project context
│   └── project-config.yaml           # Project configuration
│
├── .vibey/                           # ✅ Roadmap system (partial)
│   ├── roadmap.yaml                  # Roadmap definition
│   ├── tracks/                       # Track state files
│   ├── sprints/                      # Sprint state files
│   ├── tasks/                        # Task state files
│   ├── activity/                     # Activity logs
│   └── ai-reference.md               # Framework metadata
│
└── docs/                             # Project documentation
    ├── sprints/                      # Sprint plans
    ├── codebase-audit-report.md      # Audit results
    └── PROJECT-CONTEXT.md            # Discovery context
```

### Problems with Current Structure

1. **Platform Coupling**
   - Framework hardcoded to `.claude/` directory
   - Impossible to deploy to Goose (expects `.goose/`)
   - Impossible to deploy to Cursor (expects `.cursor/`)
   - Every platform port requires complete rewrite

2. **Script Location Fragmentation**
   - Scripts in `.claude/scripts/` (platform-specific path)
   - All script invocations use `.claude/scripts/` prefix
   - 50+ references to `.claude/scripts/` across codebase

3. **Config Location Inconsistency**
   - Project config in `.claude/project-config.yaml`
   - Roadmap state in `.vibey/roadmap.yaml`
   - No single source of truth

4. **Generated vs Source Confusion**
   - `.claude/` contains both:
     * Framework source (agents, workflows, templates)
     * Generated files (CLAUDE.md, project-config.yaml)
   - Unclear what should be committed vs gitignored

5. **Multi-Platform Blocker**
   - Cannot deploy to multiple platforms simultaneously
   - No adapter pattern possible with current structure
   - Blocks 6 platform port tracks

---

## Target State Architecture

### Target Directory Structure (v2.5.0)

```
User's Project after vibey init:
├── .vibey/                           # ✅ Single source of truth (platform-agnostic)
│   │
│   ├── config/                       # Platform-agnostic configuration
│   │   ├── project.yaml              # Project metadata
│   │   ├── framework.yaml            # Framework behavior settings
│   │   ├── agents.yaml               # Agent preferences
│   │   └── quality-gates.yaml        # Quality standards
│   │
│   ├── roadmap/                      # Roadmap state (YAML)
│   │   ├── roadmap.yaml              # Roadmap definition
│   │   ├── tracks/                   # Track state files
│   │   │   └── backend.yaml
│   │   ├── sprints/                  # Sprint state files
│   │   │   └── backend-1.yaml
│   │   ├── tasks/                    # Task definitions
│   │   │   └── backend-1-tasks.yaml
│   │   └── activity/                 # Activity logs
│   │       └── 2025-11-10.log
│   │
│   ├── sprint_docs/                  # Sprint context (Markdown)
│   │   └── backend-1/                # Per-sprint documentation
│   │       ├── plan.md               # What to build, why
│   │       ├── architecture.md       # Design decisions
│   │       ├── progress.md           # Daily learnings
│   │       └── lessons.md            # Retrospective
│   │
│   ├── framework/                    # Framework source files (OPTIONAL)
│   │   ├── agents/                   # Custom agent overrides
│   │   ├── workflows/                # Custom workflow overrides
│   │   └── templates/                # Custom templates
│   │
│   ├── .vibey-version                # Framework version marker
│   └── .vibeyignore                  # Files to exclude from framework
│
├── .claude/                          # 🎯 Generated deployment (gitignored)
│   ├── agents/                       # Generated from vibey framework
│   ├── workflows/                    # Generated from vibey framework
│   ├── commands/                     # Generated from vibey framework
│   └── CLAUDE.md                     # Generated from .vibey/config/
│
├── .goose/                           # 🦆 Generated deployment (gitignored)
│   ├── extensions/                   # Generated Python extensions
│   ├── recipes/                      # Generated YAML recipes
│   └── instructions.md               # Generated from .vibey/config/
│
├── .cursor/                          # 🔧 Generated deployment (future)
│   └── .cursorrules                  # Generated from .vibey/config/
│
├── docs/                             # 📚 Project documentation
│   ├── PROJECT_CONTEXT.md            # Generated from .vibey/config/
│   ├── ARCHITECTURE.md               # Generated from .vibey/config/
│   └── sprints/                      # Generated links to .vibey/sprint_docs/
│
└── .gitignore                        # Platform dirs gitignored
```

### Key Principles

1. **Single Source of Truth: `.vibey/`**
   - All configuration in `.vibey/config/`
   - All roadmap state in `.vibey/roadmap/`
   - All sprint docs in `.vibey/sprint_docs/`
   - Committed to git, version controlled

2. **Generated Deployments: `.claude/`, `.goose/`, etc.**
   - Generated by `vibey deploy --platform <name>`
   - Gitignored (not committed)
   - Disposable, can be regenerated at any time
   - Platform-specific transformations

3. **Unified CLI: `vibey` command**
   - Installed globally or in project
   - No platform-specific path dependencies
   - Works from any directory
   - Python package with entry point

4. **Adapter Pattern**
   - Core framework is platform-agnostic
   - Platform adapters transform for each tool
   - New platforms = new adapter, no core changes

---

## Migration Strategy

### Phase 1: Create Unified CLI (Sprint 1 - 2 weeks)

**Goal:** Build standalone `vibey` CLI tool that works independently of `.claude/`

**Tasks:**

1. **Create Python Package Structure**
   ```
   vibey-framework/
   ├── pyproject.toml              # Package definition
   ├── setup.py                    # Setup script
   ├── vibey/                      # Main package
   │   ├── __init__.py
   │   ├── __main__.py             # Entry point
   │   ├── cli/                    # CLI commands
   │   │   ├── init.py             # vibey init
   │   │   ├── deploy.py           # vibey deploy
   │   │   ├── plan.py             # vibey plan
   │   │   └── roadmap.py          # vibey roadmap
   │   ├── core/                   # Core functionality
   │   │   ├── config.py           # Config management
   │   │   ├── template.py         # Template rendering
   │   │   └── platform.py         # Platform detection
   │   ├── adapters/               # Platform adapters
   │   │   ├── base.py             # Base adapter class
   │   │   ├── claude.py           # Claude Code adapter
   │   │   └── goose.py            # Goose adapter (future)
   │   └── roadmap/                # Roadmap system
   │       ├── models.py
   │       ├── serialization.py
   │       └── commands/
   └── tests/                      # Unit tests
   ```

2. **Migrate Existing Scripts**
   - Move `framework/scripts/*.py` → `vibey/cli/`
   - Update imports: `from framework.roadmap` → `from vibey.roadmap`
   - Create unified entry point: `vibey/__main__.py`
   - Register CLI commands with Click/Typer

3. **Create Entry Point**
   ```python
   # pyproject.toml
   [project.scripts]
   vibey = "vibey.__main__:main"
   ```

4. **Testing**
   - Install package: `pip install -e .`
   - Test: `vibey --version`
   - Test: `vibey roadmap status`
   - Ensure all commands work without `.claude/` prefix

**Deliverables:**
- ✅ `vibey` command installed globally
- ✅ All roadmap commands work via `vibey roadmap ...`
- ✅ No dependencies on `.claude/scripts/`
- ✅ Python package structure complete

**Success Criteria:**
- User can run `vibey roadmap status` from any directory
- All existing roadmap functionality preserved
- 100% backward compatibility with current commands

---

### Phase 2: Migrate Configuration (Sprint 2 - 3 weeks)

**Goal:** Move configuration from `.claude/` to `.vibey/config/`

**Tasks:**

1. **Design Config Schema**
   ```yaml
   # .vibey/config/project.yaml
   project:
     id: "my-api"
     name: "My API"
     type: "api"
     description: "FastAPI REST API"
     version: "1.0.0"

   technology_stack:
     backend:
       language: "python"
       framework: "fastapi"
       version: "0.109.0"
     database:
       type: "postgresql"
       orm: "sqlalchemy"
   ```

   ```yaml
   # .vibey/config/framework.yaml
   framework:
     version: "2.5.0"
     orchestration_mode: "balanced"
     auto_commit: false
     context_mode: "summary"
   ```

   ```yaml
   # .vibey/config/agents.yaml
   agents:
     preferences:
       web-developer:
         priority: high
         always_available: true
       security-reviewer:
         priority: medium
   ```

   ```yaml
   # .vibey/config/quality-gates.yaml
   quality_gates:
     test_coverage_minimum: 85
     security_score_minimum: 85
     logging_audit_minimum: 80
     documentation_score_minimum: 75
   ```

2. **Create Config Migration Tool**
   ```bash
   vibey migrate config \
     --from .claude/project-config.yaml \
     --to .vibey/config/
   ```

   - Parse old `.claude/project-config.yaml`
   - Split into modular configs
   - Write to `.vibey/config/` directory
   - Create backup of old config

3. **Update Config Loading**
   - Modify `vibey/core/config.py` to read from `.vibey/config/`
   - Support both locations during transition (deprecation period)
   - Warn users if using old location
   - Auto-migrate on next `vibey` command

4. **Update All Config References**
   - Search for `.claude/project-config.yaml` references
   - Update to `.vibey/config/project.yaml`
   - Update template rendering paths
   - Update validation scripts

**Deliverables:**
- ✅ Modular config system in `.vibey/config/`
- ✅ Migration tool for existing projects
- ✅ Backward compatibility during transition
- ✅ Updated documentation

**Success Criteria:**
- New projects use `.vibey/config/` by default
- Old projects auto-migrate on first `vibey` command
- All config validation passes
- No breaking changes for existing users

---

### Phase 3: Implement Platform Adapters (Sprint 3 - 3 weeks)

**Goal:** Generate `.claude/`, `.goose/` deployments from `.vibey/` source

**Tasks:**

1. **Design Adapter Interface**
   ```python
   # vibey/adapters/base.py
   from abc import ABC, abstractmethod
   from pathlib import Path

   class PlatformAdapter(ABC):
       """Base class for platform adapters."""

       @abstractmethod
       def get_platform_name(self) -> str:
           """Return platform name (e.g., 'claude', 'goose')."""
           pass

       @abstractmethod
       def get_deployment_dir(self) -> Path:
           """Return deployment directory (e.g., '.claude/', '.goose/')."""
           pass

       @abstractmethod
       def deploy(self, source_dir: Path, config: dict) -> None:
           """Deploy framework to platform-specific directory."""
           pass

       @abstractmethod
       def generate_context_file(self, config: dict) -> str:
           """Generate platform context file (CLAUDE.md, instructions.md)."""
           pass

       @abstractmethod
       def validate_deployment(self) -> bool:
           """Validate deployment is correct for platform."""
           pass
   ```

2. **Implement Claude Code Adapter**
   ```python
   # vibey/adapters/claude.py
   from .base import PlatformAdapter
   from pathlib import Path

   class ClaudeAdapter(PlatformAdapter):
       def get_platform_name(self) -> str:
           return "claude"

       def get_deployment_dir(self) -> Path:
           return Path(".claude")

       def deploy(self, source_dir: Path, config: dict) -> None:
           """Deploy framework to .claude/ directory."""
           deployment_dir = self.get_deployment_dir()
           deployment_dir.mkdir(exist_ok=True)

           # Copy framework files
           self._copy_agents(source_dir, deployment_dir)
           self._copy_workflows(source_dir, deployment_dir)
           self._copy_commands(source_dir, deployment_dir)

           # Generate CLAUDE.md
           claude_md = self.generate_context_file(config)
           (deployment_dir / "CLAUDE.md").write_text(claude_md)

       def generate_context_file(self, config: dict) -> str:
           """Generate CLAUDE.md from config."""
           # Load template
           template = self._load_template("CLAUDE.md.template")
           # Render with config
           return self._render_template(template, config)

       def validate_deployment(self) -> bool:
           """Validate .claude/ deployment."""
           required_files = [
               ".claude/CLAUDE.md",
               ".claude/agents/",
               ".claude/workflows/",
           ]
           return all(Path(f).exists() for f in required_files)
   ```

3. **Implement Goose Adapter**
   ```python
   # vibey/adapters/goose.py
   from .base import PlatformAdapter
   from pathlib import Path

   class GooseAdapter(PlatformAdapter):
       def get_platform_name(self) -> str:
           return "goose"

       def get_deployment_dir(self) -> Path:
           return Path(".goose")

       def deploy(self, source_dir: Path, config: dict) -> None:
           """Deploy framework to .goose/ directory."""
           deployment_dir = self.get_deployment_dir()
           deployment_dir.mkdir(exist_ok=True)

           # Transform agents → extensions
           self._generate_extensions(source_dir, deployment_dir, config)

           # Transform workflows → recipes
           self._generate_recipes(source_dir, deployment_dir, config)

           # Generate instructions.md
           instructions = self.generate_context_file(config)
           (deployment_dir / "instructions.md").write_text(instructions)

       def generate_context_file(self, config: dict) -> str:
           """Generate instructions.md from config."""
           # Load template
           template = self._load_template("instructions.md.template")
           # Render with config
           return self._render_template(template, config)

       def validate_deployment(self) -> bool:
           """Validate .goose/ deployment."""
           required_files = [
               ".goose/instructions.md",
               ".goose/extensions/",
               ".goose/recipes/",
           ]
           return all(Path(f).exists() for f in required_files)
   ```

4. **Implement Deployment Command**
   ```bash
   # Deploy to Claude Code
   vibey deploy --platform claude

   # Deploy to Goose
   vibey deploy --platform goose

   # Deploy to all detected platforms
   vibey deploy --all

   # Clean and redeploy
   vibey deploy --platform claude --clean
   ```

5. **Update .gitignore**
   ```gitignore
   # Platform deployment directories (generated)
   .claude/
   .goose/
   .cursor/

   # Exception: Keep .vibey/ (source of truth)
   !.vibey/
   ```

**Deliverables:**
- ✅ Adapter interface and base class
- ✅ Claude Code adapter (full)
- ✅ Goose adapter (basic)
- ✅ `vibey deploy` command
- ✅ Updated .gitignore rules

**Success Criteria:**
- `vibey deploy --platform claude` generates working `.claude/`
- `vibey deploy --platform goose` generates working `.goose/`
- Generated directories can be deleted and regenerated
- All framework functionality preserved

---

## Migration Path for Existing Users

### For Existing Vibey Projects (v1.2.0 → v2.5.0)

**Step 1: Install New vibey CLI**
```bash
pip install --upgrade vibey-framework
vibey --version  # Should show v2.5.0
```

**Step 2: Run Migration**
```bash
cd my-project
vibey migrate
```

**Migration Process:**
1. Detect `.claude/` installation
2. Create `.vibey/` directory structure
3. Migrate config: `.claude/project-config.yaml` → `.vibey/config/`
4. Migrate roadmap (already in `.vibey/`, no changes)
5. Copy custom templates if any
6. Regenerate `.claude/` as deployment
7. Update `.gitignore`

**Step 3: Verify Migration**
```bash
vibey validate
```

**Output:**
```
✅ .vibey/ structure valid
✅ Config migration complete
✅ Roadmap system intact
✅ .claude/ deployment valid
⚠️  .claude/ is now gitignored (generated artifact)

Migration complete! Your project is now v2.5.0 compatible.
```

### Breaking Changes

**None (backward compatible)**
- Old projects continue to work
- Auto-migration on first `vibey` command
- Deprecation warnings for 2 releases
- Full removal of `.claude/`-first approach in v3.0.0

---

## Technical Implementation Details

### Config Loading Priority

```python
def load_config():
    """Load config with fallback for backward compatibility."""

    # Priority 1: .vibey/config/ (new location)
    if Path(".vibey/config/project.yaml").exists():
        return load_modular_config(".vibey/config/")

    # Priority 2: .claude/project-config.yaml (legacy)
    if Path(".claude/project-config.yaml").exists():
        warn("Using legacy config location. Run 'vibey migrate' to update.")
        return load_legacy_config(".claude/project-config.yaml")

    # Priority 3: No config found
    raise ConfigNotFoundError("No Vibey config found. Run 'vibey init'.")
```

### Template Rendering Pipeline

```python
def render_platform_context(platform: str, config: dict) -> str:
    """Render platform-specific context file."""

    # 1. Load adapter
    adapter = get_adapter(platform)

    # 2. Load template
    template_name = adapter.get_context_template_name()
    template = load_template(f"templates/{template_name}")

    # 3. Prepare context
    context = {
        "project": config["project"],
        "framework": config["framework"],
        "agents": config["agents"],
        "quality_gates": config["quality_gates"],
        "platform": platform,
    }

    # 4. Render
    rendered = jinja2.Template(template).render(context)

    return rendered
```

### Framework Source Location

**Option A: Bundle in Package (Recommended)**
```python
# vibey/framework/ directory contains all agents, workflows, templates
# Deployed via pip install
# Extracted to .vibey/framework/ on first run if custom overrides needed
```

**Option B: Remote Repository**
```python
# Download from GitHub on first run
# Cache in ~/.vibey/framework/
# Update with vibey framework update
```

**Decision: Option A** (simpler, faster, works offline)

---

## Risks and Mitigation

### Risk 1: Breaking Existing Installations

**Probability:** Medium
**Impact:** High
**Mitigation:**
- Comprehensive backward compatibility
- Auto-migration on first command
- Clear deprecation warnings
- 2-release deprecation period before removal
- Rollback mechanism if migration fails

### Risk 2: Script Path Dependencies

**Probability:** High
**Impact:** Medium
**Mitigation:**
- Unified CLI eliminates path dependencies
- All scripts invoked via `vibey` command
- Search/replace all `.claude/scripts/` references
- Comprehensive testing of all commands

### Risk 3: User Confusion During Transition

**Probability:** High
**Impact:** Low
**Mitigation:**
- Clear migration guide
- Automated migration process
- Visual indicators (✅ migrated, ⚠️ legacy)
- Detailed documentation

### Risk 4: Platform Adapter Bugs

**Probability:** Medium
**Impact:** Medium
**Mitigation:**
- Extensive testing of each adapter
- Platform-specific test suites
- Validation after deployment
- Easy rollback to previous state

---

## Success Metrics

### Technical Metrics

- ✅ 100% backward compatibility during transition
- ✅ 0 breaking changes for existing users
- ✅ <5 minutes for auto-migration
- ✅ All 200+ tests passing after migration
- ✅ `vibey deploy` generates valid platform directories

### User Experience Metrics

- ✅ Clear migration path documented
- ✅ Auto-migration succeeds >95% of the time
- ✅ Users understand new directory structure
- ✅ No increase in support requests during migration

### Platform Expansion Metrics

- ✅ Unblocks goose-port track
- ✅ Enables multi-platform track
- ✅ New platform adapter in <1 week
- ✅ 90% code reuse across platforms

---

## Timeline and Dependencies

### Sprint 1: Unified CLI (2 weeks)
**Start:** Week 1
**End:** Week 2
**Dependencies:** None
**Deliverables:**
- Python package structure
- `vibey` CLI entry point
- All roadmap commands working

### Sprint 2: Config Migration (3 weeks)
**Start:** Week 3
**End:** Week 5
**Dependencies:** Sprint 1 complete
**Deliverables:**
- Modular config system
- Migration tool
- Auto-migration on first command

### Sprint 3: Platform Adapters (3 weeks)
**Start:** Week 6
**End:** Week 8
**Dependencies:** Sprint 2 complete
**Deliverables:**
- Adapter interface
- Claude adapter
- Goose adapter
- `vibey deploy` command

### Post-Migration (Week 9+)
- Documentation updates
- User communication
- Monitor migration success rate
- Bug fixes and refinements

---

## Dependencies and Blockers

### Blocks These Tracks:
- ✅ goose-port (cannot proceed without adapter pattern)
- ✅ cursor-port (cannot proceed without adapter pattern)
- ✅ multi-platform (depends on this architecture)
- ✅ aider-port, continue-port, windsurf-port, jetbrains-port (all blocked)

### Depends On:
- ✅ testing-system (need comprehensive tests to validate migration)
- ✅ roadmap-system (already in .vibey/, foundation complete)

### Unblocks:
- 6 platform port tracks
- Multi-platform architecture
- Future platform expansions

---

## Open Questions

1. **Q: Should we bundle framework files in the Python package or download on demand?**
   - **A: Bundle in package** (simpler, works offline, faster)

2. **Q: Should `.vibey/framework/` be optional or required?**
   - **A: Optional** (only created if user has custom overrides)

3. **Q: How do we handle custom agents/workflows users may have added?**
   - **A: Migration detects custom files, preserves in `.vibey/framework/`, warns user**

4. **Q: Should old `.claude/` be deleted after migration?**
   - **A: Yes, but only after confirmation and backup created**

5. **Q: How long should we support backward compatibility?**
   - **A: 2 releases (v2.5, v2.6), then fully remove in v3.0**

---

## References

- [PLATFORM_AGNOSTIC_ARCHITECTURE.md](./PLATFORM_AGNOSTIC_ARCHITECTURE.md) - Overall architecture vision
- [ROADMAP_SYSTEM.md](../reference/ROADMAP_SYSTEM.md) - Roadmap system design
- [CONTEXT_LOADING_STRATEGY.md](./CONTEXT_LOADING_STRATEGY.md) - Context management
- Core Framework Track: `.vibey/tracks/core-framework.yaml`
- Multi-Platform Track: `.vibey/tracks/multi-platform.yaml`

---

## Approval and Sign-off

**Status:** Awaiting review
**Next Steps:**
1. Review this plan with team
2. Create directory-migration track in roadmap
3. Begin Sprint 1 (Unified CLI)

**Track ID:** `directory-migration`
**Priority:** CRITICAL
**Estimated Duration:** 6-8 weeks (3 sprints)
