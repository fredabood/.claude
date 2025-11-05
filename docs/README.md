# Development Documentation

Documentation for Vibey framework developers and contributors.

---

## Strategic Planning

### [Roadmap](ROADMAP.md)
**Length:** ~800 lines
**Topics:** Multi-platform strategy, compatibility assessment, feature roadmap

**Comprehensive roadmap for Vibey's future:**

- **Current Status:** Production ready for Claude Code (v1.1)
- **Platform Compatibility Assessment:** Goose (75-85%), Cursor (50-65%)
- **Near-term Plans:** Default CLAUDE.md, docs-driven migration
- **Multi-platform Strategy:** Goose port → Platform-agnostic core → Unified CLI
- **Timeline:** 12 months to production multi-platform framework

**Recommended Path Forward:**
1. **Goose Port** (3 months) - MVP with 5-7 agents, 3-5 workflows
2. **Platform-Agnostic Core** (6 months) - Extract concepts, build adapters
3. **Unified Framework** (12 months) - Single framework, multiple platforms

**Use this when:**
- Planning framework evolution
- Understanding platform compatibility
- Contributing to multi-platform efforts
- Making strategic decisions

---

## Session Context

### [Session Handoff](SESSION_HANDOFF.md)
**Length:** ~420 lines
**Topics:** Session summaries, recent changes, framework state

**Latest session context (Nov 2024):**

- **Phase 10:** Documentation Organization - Moved docs to organized structure
- **Phase 11:** Codebase Audit Workflow - Automated project analysis
- **Phase 11.1:** Git History Analysis - Sprint pattern discovery
- **Phase 11.2:** Independent Components - Flexible analysis options
- **Phase 12:** Vibey Framework Manager - Post-initialization management

**Framework Status:** v1.1 Production Ready
- 12 specialized agents (added Vibey Manager)
- 16 structured workflows (added Codebase Audit)
- 22 handoff templates (added Audit Report)
- ~50,600 lines across 68 components

**Use this when:**
- Continuing work from previous session
- Understanding recent changes
- Getting context on current framework state
- Learning about latest enhancements

---

## Development History

### [Development History](DEVELOPMENT_HISTORY.md)
**Length:** ~1,200 lines
**Topics:** Framework development phases, session summaries, statistics

**Complete development history across 9 phases:**

- **Phase 1:** Comprehensive Audit (28 agents, 17 workflows, 22 templates)
- **Phase 2:** Framework Design (config schema, Jinja2 templates)
- **Phase 3:** Agent Development (11 specialized agents, 100% complete)
- **Phase 4:** Workflow Development (15 workflows, 88% complete)
- **Phase 5:** Handoff Template Development (21 templates, 91% complete)
- **Phase 6:** Deployment Tooling (validator, renderer, setup scripts)
- **Phase 7:** Claude Code Integration (orchestration modes, `/vibey` command)
- **Phase 8:** Repository Restructuring (simplified installation)
- **Phase 9:** Universal Deployment Flow (single command for all scenarios)

**Total Framework:** ~46,500 lines across 60+ components

**Use this when:**
- Understanding framework evolution
- Tracking development decisions
- Learning why certain patterns were chosen
- Contributing to the framework

---

## Framework Architecture

### Config-Driven Design

**Core Principle:** 80% generic, 20% config-driven

**Pattern:**
```markdown
## Agent Instructions

Use {{ config.testing.backend.framework }} for backend tests
Achieve {{ config.quality_gates.test_coverage_minimum }}% coverage
```

**Benefits:**
- Single codebase supports all tech stacks
- No hardcoded technology references
- Easy customization per project
- Consistent behavior across projects

### Self-Prompting Mechanism

**Pattern:** Planning outputs become execution inputs

```
ROADMAP.md → Sprint Plan → Phase Plans → Implementation → Execution
```

**Documents flow through workflow:**
- Each phase reads previous outputs
- Agents know what to do next
- Self-organizing task management
- No external coordination needed

### Three-Mode Orchestration

**Simple Mode (Explicit):**
- Keyword matching in CLAUDE.md
- Transparent agent selection
- Best for learning

**Balanced Mode (Pattern Matching):**
- Agent trigger patterns
- Context-aware selection
- Recommended for most users

**Tiered Mode (Intelligent):**
- Coordinator agent routes tasks
- Complex task decomposition
- Best for large projects

---

## Contributing

### Adding a New Agent

1. Create agent file in appropriate `agents/` subdirectory
2. Follow existing agent structure:
   - Role & Responsibilities
   - Input/Output
   - Process/Steps
   - Quality Standards
   - Handoff Template
   - Trigger Patterns (if applicable)
3. Use `{{ config.* }}` for all tech-specific references
4. Add agent to orchestration documentation
5. Update agent count in README

### Adding a New Workflow

1. Create workflow file in appropriate `workflows/` subdirectory
2. Follow existing workflow structure:
   - Overview
   - Prerequisites
   - Steps (with agents, duration, deliverables)
   - Workflow Diagram
   - Success Criteria
3. Use config-driven agent references
4. Add workflow to selection guide
5. Update workflow count in README

### Adding a New Template

1. Create template file in `templates/handoffs/`
2. Use Jinja2 template syntax
3. Reference config values: `{{ config.* }}`
4. Include all required sections
5. Add template to reference documentation
6. Update template count in README

---

## Framework Statistics

**Total Lines:** ~50,600+ across 68 components

**Components:**
- 12 specialized agents (including Vibey Manager)
- 16 structured workflows (including Codebase Audit)
- 22 handoff templates (including Audit Report)
- 3 orchestration modes
- 1 coordinator agent
- 5 deployment tools
- Complete documentation

**Supported:**
- 5 project types (web app, API, ML, data platform, infrastructure)
- 6+ programming languages (Python, TypeScript, JavaScript, Java, Go, Rust)
- 20+ frameworks (React, FastAPI, Spring Boot, etc.)
- 3 cloud providers (AWS, Azure, GCP)
- Universal tech stack support via config

---

## Development Tools

### Config Validator
**File:** `scripts/validate-config.py`

Validates `project-config.yaml` against `config/schema.yaml`:
```bash
python3 scripts/validate-config.py project-config.yaml
```

### Template Renderer
**File:** `scripts/render-template.py`

Renders Jinja2 templates with config:
```bash
python3 scripts/render-template.py \
  -c project-config.yaml \
  -t templates/CLAUDE.md.template \
  -o CLAUDE.md
```

---

## Quick Links

**New user?** Start with [Getting Started](../getting-started/)

**Need guidance?** Read the [Guides](../guides/)

**Looking for details?** Check [Reference](../reference/)

---

**[← Back to Documentation Index](../README.md)**
