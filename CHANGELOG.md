# Changelog

All notable changes to the Vibey Agent Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- User Journey Audit Phase 2.5 - Contributor documentation
- Development environment setup guide
- Coding standards documentation
- Architectural Decision Records (ADRs)

---

## [2.5.0] - 2025-12-12

### Added - Comprehensive Documentation & MCP Enhancements

**Auto-Generated Documentation:**
- CLI Reference Guide (169 commands) - auto-generated from Click introspection
- MCP Reference Guide (76 tools, 8 resources, 4 prompts) - auto-generated from server
- Documentation drift detection - CI/CD enforcement
- `vibey docs generate-cli` - Generate CLI reference
- `vibey docs generate-mcp` - Generate MCP reference
- `vibey docs check-drift` - Verify CLI docs match implementation
- `vibey docs check-mcp-drift` - Verify MCP docs match implementation

**User Journey Documentation:**
- 5 User Personas (Nina, Alex, Pat, Chris, Sam)
- 5 Journey Maps with stage progression
- 5 Step-by-step Walkthroughs
- Coverage Matrix mapping features to personas

**MCP Server Enhancements:**
- 76 MCP tools (task, sprint, query, content, agent, workflow, handoff)
- 8 Resource templates (workflows, handoffs with sub-resources)
- 4 Prompts (quality gates, security, testing, documentation)
- Complete tool introspection support

**Platform Deployment:**
- 9 platform adapters (Claude Code, Cursor, Copilot, Goose, VS Code, Gemini, Aider, Continue, Windsurf)
- `vibey deploy list` - Show available platforms
- `vibey deploy run --platform <name>` - Deploy to platform

### Changed
- README completely rewritten for accuracy
- Documentation reorganized into guides/, reference/, journeys/, walkthroughs/

---

## [2.0.0] - 2025-11-15

### Added - SQLite Backend & Flat Structure

**SQLite Backend:**
- 26-table database schema for roadmap data
- Fast queries with relationship integrity
- YAML + SQLite dual storage (YAML source of truth)
- Auto-sync between YAML and database
- `vibey roadmap db rebuild` - Rebuild database from YAML
- `vibey roadmap db sync` - Sync YAML changes to database

**Flat Directory Structure:**
- ULID-based file naming (26-character identifiers)
- Flat structure: `tracks/`, `sprints/`, `tasks/` directories
- 98% reduction in directories (3 vs 4,000+)
- Fast git operations

**Activity Logging:**
- Audit trail for all roadmap changes
- `vibey roadmap audit` - View change history
- JSONL activity log format

**Git Integration:**
- Pre-commit hooks for roadmap validation
- Post-commit hooks for status tracking
- Bypass detection and warnings
- `vibey roadmap check-hooks` - Verify hook installation

**CLI Enhancements:**
- Auto-progress for track/sprint/task status
- Batch operations for bulk updates
- Context management commands
- Improved error messages with unified error handling

### Changed
- ID format changed from slugs to ULIDs
- Directory structure from hierarchical to flat
- Backend selection: auto, sqlite, yaml modes

### Fixed
- YAML task status field placement
- Track/sprint/task ID reference consistency
- CLI auto-progress display issues

---

## [1.3.0] - 2025-11-09

### Added - Config-to-Docs Architecture

**Platform-Agnostic Core:**
- Unified `vibey` CLI command
- Platform adapter system
- Claude Code adapter (production-ready)
- Permanent `.vibey/` directory
- Modular config system
- Auto-generated documentation from config
- Context loading strategy
- Deployment generation

**New Commands:**
- `vibey deploy --platform <name>`
- `vibey docs generate`
- `vibey roadmap summarize sprint <id>`
- `vibey roadmap context <task-id>`

**Documentation:**
- Platform-Agnostic Architecture guide
- Platform Adapter Pattern guide
- YAML-Markdown Separation design
- Context Loading Strategy guide

### Changed
- Framework code moved to `framework/` directory
- Config format to YAML-based metadata
- Jinja2 templates for instruction generation

---

## [1.2.0] - 2024-11-05

### Added - Production Readiness

- `generate-config.py` for project configuration
- `update-config.py` for nested config updates
- Sprint state management scripts
- PROJECT-CONTEXT system
- Version checking and rollback
- Pre-flight deployment checks
- Health check system

### Changed
- 100% Claude Code compatibility (no bash prompts)
- Deployment process reordered for fail-fast

---

## [1.1.0] - 2024-11-04

### Added
- Documentation organization (`/docs` structure)
- Codebase audit discovery workflow
- Git history analysis
- Vibey Manager agent
- Dual-mode `/vibey` command

---

## [1.0.0] - 2024-10-28

### Added - Initial Release
- 12 specialized agents
- 16 structured workflows
- 22 handoff templates
- 3 orchestration modes
- YAML configuration with validation
- Quality gates system
- `/vibey` slash command
- Complete documentation

**Statistics:**
- ~50,600 lines across 68 components
- 5 project types supported
- 6+ programming languages
- 20+ frameworks

---

## Version Summary

| Version | Date | Key Features |
|---------|------|-------------|
| 2.5.0 | 2025-12-12 | Auto-generated docs, MCP enhancements, user journeys |
| 2.0.0 | 2025-11-15 | SQLite backend, flat structure, git hooks |
| 1.3.0 | 2025-11-09 | Config-to-docs, platform adapters |
| 1.2.0 | 2024-11-05 | Production readiness, Claude compatibility |
| 1.1.0 | 2024-11-04 | Documentation, audit workflow, Vibey Manager |
| 1.0.0 | 2024-10-28 | Initial release |

---

## Links

[Unreleased]: https://github.com/fredabood/vibey/compare/v2.5.0...HEAD
[2.5.0]: https://github.com/fredabood/vibey/compare/v2.0.0...v2.5.0
[2.0.0]: https://github.com/fredabood/vibey/compare/v1.3.0...v2.0.0
[1.3.0]: https://github.com/fredabood/vibey/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/fredabood/vibey/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/fredabood/vibey/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/fredabood/vibey/releases/tag/v1.0.0
