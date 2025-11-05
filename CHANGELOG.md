# Changelog

All notable changes to the Vibey Agent Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2024-11-05

### Added - Phase 1 & 2: Production Readiness
- **Critical Scripts** - Created `generate-config.py` (203 lines) for initializing project configuration from templates
- **Critical Scripts** - Created `update-config.py` (266 lines) for updating nested config values with dot notation
- **Sprint State Management** - Created 4 Python scripts for complete sprint lifecycle tracking:
  - `create-sprint-state.py` (304 lines) - Generate state from sprint plans
  - `query-sprint-state.py` (504 lines) - Query sprint progress and status
  - `update-sprint-state.py` (526 lines) - Track tasks, agents, quality gates
  - `update-sprint-marker.py` (323 lines) - Update CLAUDE.md sprint markers
- **PROJECT-CONTEXT System** - Created `manage-project-context.py` (566 lines) for unified discovery output with archiving
- **Templates** - Created `PROJECT-CONTEXT.md.template` (229 lines) for unified discovery format
- **Templates** - Created `sprint-state.yaml.template` (59 lines) for sprint state structure
- **Templates** - Created `sprint-retrospective.md.template` (162 lines) for post-sprint reviews
- **Config** - Created `sprint-state-schema.yaml` (297 lines) for validation
- **Commands** - Created 5 new command files: vibey-plan.md, vibey-think.md, vibey-code.md, vibey-manage.md, vibey-audit.md

### Added - Phase 3: Production Polish
- **Version Management** - Created `check-version.py` (213 lines) for version checking and upgrade detection
- **Rollback Capability** - Created `rollback-framework.py` (234 lines) for framework rollback to previous backups
- **Deployment** - Pre-flight checks now run before file copying (fail-fast behavior)
- **Health Checks** - Comprehensive 7-category health check system

### Changed - Phase 1 & 2: Claude Code Compatibility
- **Interactive Prompts** - Replaced all 24 bash `read -p` prompts with Claude-native conversational questions:
  - vibey.md: 8 prompts (deployment, state validation, git init)
  - vibey-plan.md: 1 prompt (context usage)
  - vibey-manage.md: 1 prompt (config value input)
  - vibey-code.md: 11 prompts (phase completion, task tracking, sprint management)
  - vibey-think.md: 3 prompts (resume, restore, archive selection)
- **Framework Compatibility** - 100% Claude Code compatible (no hanging prompts)

### Changed - Phase 3: Enhanced Operations
- **Deployment Process** - Reordered steps to check dependencies before copying files
- **Health Checks** - Completely rewritten with 7 categories, issues vs warnings, actionable recommendations
- **Project Structure** - Added `docs/archive/discovery/` directory creation during deployment

### Improved
- **Error Messages** - Clearer, more actionable error messages throughout deployment
- **User Experience** - Better progress indicators and status messages
- **Documentation** - Updated CLAUDE.md with Phase 1-3 changes

### Fixed
- **Missing Scripts** - First-time users were blocked; now have all required scripts
- **Deployment Failures** - Could fail mid-process; now fails fast with clear errors
- **State Tracking** - No sprint state management; now complete lifecycle support

### Removed
- 5 empty placeholder directories (config/examples, workflows/operations, workflows/execution, agents/execution, templates/fragments)

---

## [1.1.0] - 2024-11-04

### Added - Phase 10: Documentation Organization
- Reorganized documentation into `/docs` (framework development) and `/framework/docs` (user documentation)
- Created comprehensive documentation structure with getting-started/, guides/, and reference/ directories
- Added README files for each documentation section

### Added - Phase 11: Codebase Audit Workflow
- **Codebase Audit Discovery Workflow** - Automated project analysis workflow (1,200+ lines)
- **Audit Report Template** - Structured template for audit findings
- **Git History Analysis** - Sprint pattern and velocity discovery
- **Independent Analysis** - Users can choose code audit, git history, both, or neither

### Added - Phase 12: Vibey Manager Agent
- **Vibey Manager Agent** - Post-initialization framework management (500 lines)
- **Framework Management Command** - vibey-manage.md for configuration updates
- **Dual-Mode /vibey** - Detection logic for initialization vs management modes

### Changed
- Framework now detects initialization state and adapts behavior
- Sprint Planning Agent updated with orchestration design
- Templates updated with sprint-driven orchestration support

---

## [1.0.0] - 2024-10-28

### Added - Initial Release
- **12 Specialized Agents:**
  - Planning: Sprint Planning, Researcher
  - Development: Web Developer, ML Engineer
  - Quality: Security Reviewer, Observability Engineer, Performance Engineer
  - Documentation: Documentation Engineer, Diagram Engineer, Git Committer
  - Core: Coordinator, Vibey Manager
- **16 Structured Workflows:**
  - Planning: Sprint Planning, Architecture Review, Codebase Audit
  - Development: Single Feature, ML Model, Frontend Feature, Parallel Features
  - Quality: Security Audit, Performance Optimization, Logging Implementation
  - Operations: Infrastructure Setup, and more
- **22 Handoff Templates** for structured agent-to-agent communication
- **3 Orchestration Modes:** Simple (keyword), Balanced (pattern), Tiered (coordinator)
- **Configuration System:** YAML-based with schema validation
- **Python Tooling:** Config validator, template renderer
- **Quality Gates:** Security, testing, logging, documentation audits
- `/vibey` slash command for framework initialization
- Complete documentation (50+ pages)

### Framework Statistics
- ~50,600 lines across 68 components
- Support for 5 project types
- Support for 6+ programming languages
- Support for 20+ frameworks
- Universal tech stack support via configuration

---

## Version History Summary

| Version | Date | Key Features | Lines Added |
|---------|------|-------------|-------------|
| **1.2.0** | 2024-11-05 | Production readiness, 100% Claude compatibility, version management, rollback | ~7,600 |
| **1.1.0** | 2024-11-04 | Documentation organization, codebase audit, Vibey Manager | ~4,000 |
| **1.0.0** | 2024-10-28 | Initial release with 12 agents, 16 workflows, 22 templates | ~50,600 |

---

## Upgrade Notes

### Upgrading to 1.2.0 from 1.1.0

**What's New:**
- Version checking system (check-version.py)
- Rollback capability (rollback-framework.py)
- 10 Python scripts (was 3)
- Complete sprint state management
- PROJECT-CONTEXT system for discovery
- Enhanced health checks
- 100% Claude Code compatibility

**Breaking Changes:** None - fully backward compatible

**Migration Steps:**
1. Pull latest framework code
2. Run `/vibey` to update deployed files
3. Framework will automatically update to 1.2.0

**New Features to Try:**
```bash
# Check framework version
python3 .claude/scripts/check-version.py

# Run enhanced health check
# /vibey manage → Option 5 (Framework Health Check)

# List backups (if any)
python3 .claude/scripts/rollback-framework.py --list
```

### Upgrading to 1.1.0 from 1.0.0

**What's New:**
- Codebase Audit Discovery workflow
- Git history analysis
- Vibey Manager agent
- Dual-mode /vibey command
- Organized documentation structure

**Breaking Changes:** None - fully backward compatible

**Migration Steps:**
1. Pull latest framework code
2. Run `/vibey` - will detect existing installation
3. Optionally run codebase audit: `/vibey` → Option 4 (Discovery Mode)

---

## Development Roadmap

See [ROADMAP.md](docs/ROADMAP.md) for detailed future plans.

**Upcoming Features:**
- Default CLAUDE.md template
- Docs-driven configuration migration
- Multi-platform support (Goose, Cursor)
- Enhanced workflow selection
- Automated testing framework

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to the Vibey framework.

---

## License

[License information to be added]

---

[1.2.0]: https://github.com/fredabood/vibey/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/fredabood/vibey/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/fredabood/vibey/releases/tag/v1.0.0
