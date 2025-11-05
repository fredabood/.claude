# Vibey Agent Framework - Repository Context

**Repository:** Vibey Agent Framework
**Version:** 1.1 (Production Ready)
**Purpose:** Agentic orchestration framework for AI coding assistants

---

## Quick Start

Every session working on this repository:

1. ✅ **Read this file** (CLAUDE.md) - Framework repository context
2. 📋 **Check docs/ROADMAP.md** - Multi-platform strategy and compatibility plans
3. 🔍 **Run `git status`** - Understand current state
4. 📚 **Review recent commits** - Context on recent changes

---

## What Is This Repository?

This is the **Vibey Agent Framework** - an intelligent agent orchestration system originally built for Claude Code, designed to transform AI coding assistants into specialized development teams.

### Framework Components

- **12 Specialized Agents** - Planning, development, quality, documentation, core
- **16 Structured Workflows** - Sprint planning, feature development, ML, infrastructure, etc.
- **22 Handoff Templates** - Structured outputs for agent-to-agent communication
- **3 Orchestration Modes** - Simple (keyword), Balanced (pattern), Tiered (intelligent)
- **Quality Gates** - Security, testing, logging, documentation audits
- **Python Tooling** - Config validation, template rendering (Jinja2)

### Framework Statistics

- **Total Lines:** ~50,600 across 68 components
- **Agents:** ~21,375 lines across 12 agents
- **Workflows:** Comprehensive lifecycle coverage
- **Status:** Production-ready for Claude Code

---

## Repository Structure

```
vibey/
├── agents/                       # 12 specialized agents
│   ├── core/                     # Coordinator, Vibey Manager
│   ├── planning/                 # Sprint Planning, Researcher
│   ├── development/              # Web Developer, ML Engineer
│   ├── quality/                  # Security, Performance, Observability
│   ├── documentation/            # Docs, Diagrams, Git Committer
│   └── architecture/             # Architecture reviews
├── workflows/                    # 16 structured workflows
│   ├── planning/                 # Sprint planning, codebase audit
│   ├── development/              # Feature dev, ML, frontend
│   ├── quality/                  # Security, performance, logging
│   └── [others]
├── templates/                    # 22 handoff templates
│   ├── CLAUDE.md.template        # Project context template
│   └── handoffs/                 # Agent handoff templates
├── commands/
│   └── vibey.md                  # /vibey slash command (dual-mode)
├── config/
│   ├── schema.yaml               # Project config schema
│   └── config-templates/         # Example configs (web-app, API, ML)
├── scripts/
│   ├── validate-config.py        # YAML config validator
│   └── render-template.py        # Jinja2 template renderer
├── docs/                         # Framework documentation
│   ├── getting-started/          # Installation, user journey
│   ├── guides/                   # Orchestration, workflow selection
│   ├── reference/                # Component reference
│   └── development/              # Framework development docs
├── tools/                        # Additional utilities
└── README.md                     # Main documentation
```

---

## Current Development State

### Framework Status: ✅ Production Ready (Claude Code)

**Recent Major Enhancements (Nov 2024):**
1. **Documentation Organization** - Moved to docs/ with 4-category taxonomy
2. **Codebase Audit Workflow** - Automated analysis for existing projects
3. **Git History Analysis** - Discover sprint patterns and velocity
4. **Independent Analysis Components** - Users choose code audit, git history, both, or neither
5. **Vibey Manager Agent** - Post-initialization framework management

### Key Files and Their Purposes

**Core Framework Files:**
- `commands/vibey.md` - Dual-mode: initialization for new projects, management for existing
- `agents/core/coordinator.md` - Intelligent routing for complex requests (650 lines)
- `agents/core/vibey-manager.md` - Framework management agent (500 lines)
- `config/schema.yaml` - Project configuration schema (400+ lines)
- `templates/CLAUDE.md.template` - User project context template

**Workflows:**
- `workflows/planning/sprint-planning.md` - Sprint planning process
- `workflows/planning/codebase-audit-discovery.md` - Automated project analysis (1,200 lines)
- `workflows/single-feature-development.md` - Feature development lifecycle
- `workflows/ml-model-development.md` - ML model lifecycle
- `workflows/infrastructure-setup.md` - IaC deployment

**Documentation:**
- `docs/getting-started/QUICK_START.md` - 10-minute quick start (675 lines)
- `docs/getting-started/USER_JOURNEY.md` - Detailed scenarios (1,800+ lines)
- `docs/guides/ORCHESTRATION.md` - Orchestration deep dive (500+ lines)
- `docs/guides/WORKFLOW_SELECTION_GUIDE.md` - Workflow selection guide
- `docs/development/ROADMAP.md` - Multi-platform roadmap and compatibility assessment

---

## Critical Context for Development

### Design Principles

1. **Conversational First** - Natural language interaction, no complex commands
2. **Quality-Driven** - Quality gates prevent shipping incomplete/insecure code
3. **Flexible Orchestration** - Three modes: Simple (explicit) → Balanced (smart) → Tiered (coordinated)
4. **Agent Specialization** - Each agent has specific expertise and trigger patterns
5. **Structured Handoffs** - Templates ensure consistent information flow
6. **Platform Agnostic (Goal)** - Core concepts portable, implementation platform-specific

### Claude Code Dependencies (Important for Porting)

**Hard Dependencies:**
- Slash commands (`/vibey`) - Entry point
- `.claude/` directory - Framework storage location
- Task tool - Subagent launching mechanism
- CLAUDE.md auto-reading - Context loading
- Agent markdown files - Instruction format

**Soft Dependencies (Portable):**
- Conversational discovery - Q&A patterns
- Jinja2 templates - Config rendering
- Python scripts - Validation and rendering
- Git integration - Version control patterns
- Quality gates - Testing/security concepts

### Dual-Mode `/vibey` Command

**Detection Logic:**
```bash
if [ -f ".claude/project-config.yaml" ] && [ -f ".claude/CLAUDE.md" ] && grep -q "VIBEY_FRAMEWORK_MANAGED" .claude/CLAUDE.md; then
  FRAMEWORK_STATE="initialized" → Launch Vibey Manager Agent
else
  FRAMEWORK_STATE="new" → Run Full Initialization
fi
```

**Detection Criteria:**
1. `.claude/project-config.yaml` exists (Vibey project configuration)
2. `.claude/CLAUDE.md` exists (Vibey-managed project context)
3. `.claude/CLAUDE.md` contains `<!-- VIBEY_FRAMEWORK_MANAGED -->` marker

**Why the marker?**
- Prevents false positives if project already has these files
- Ensures CLAUDE.md was generated by Vibey
- The marker is added automatically during initialization
- Safe fallback: missing marker triggers re-initialization

**Two Modes:**
1. **Initialization Mode** - First-time setup (deploy → pre-check → configure → sprint plan)
2. **Management Mode** - Framework config (orchestration mode, quality gates, agents, tech stack)

---

## Platform Compatibility (Strategic Direction)

### Current Roadmap Priorities

**Near-Term (3 months):**
- Default CLAUDE.md file
- Config-driven → Docs-driven migration

**Multi-Platform Strategy:**

**Goose Port:** ✅ **RECOMMENDED** (75-85% compatible)
- Workflows → Recipes (direct mapping)
- Agents → Extensions (direct mapping)
- Effort: 150-225 hours (2.5-3.5 months with 2-3 devs)
- MCP ecosystem access (1000+ tools)
- LLM agnostic

**Cursor Port:** ⚠️ **RISKY** (50-65% compatible)
- Paradigm mismatch: sequential → parallel
- Effort: 265-405 hours (4-5 months with 3-4 devs)
- POC recommended before full commitment

**Long-Term Vision:**
- Platform-agnostic core
- Adapter pattern for each platform
- Unified `vibey` CLI tool
- Timeline: 12 months to multi-platform production

See `docs/development/ROADMAP.md` for complete assessment.

---

## Working on This Repository

### Before Making Changes

1. **Read relevant documentation** - Understand component purpose
2. **Check existing patterns** - Follow established conventions
3. **Consider portability** - Will this work on other platforms?
4. **Test thoroughly** - Validate with real scenarios

### File Modification Guidelines

**Agents (`agents/**/*.md`):**
- Follow agent template structure
- Include trigger patterns for orchestration
- Specify inputs, outputs, and quality criteria
- Keep instructions clear and actionable

**Workflows (`workflows/**/*.md`):**
- Sequential steps with clear handoffs
- Include project type variations (web-app, API, ML)
- Specify durations and complexity
- Reference appropriate handoff templates

**Templates (`templates/**/*.md`):**
- Use Jinja2 syntax for variables
- Include clear section headings
- Provide examples and guidance
- Ensure all referenced config keys exist in schema

**Configuration (`config/schema.yaml`):**
- Document all fields with descriptions
- Provide examples and defaults
- Validate with `validate-config.py`
- Update templates if schema changes

### Testing Changes

**Config Validation:**
```bash
python3 scripts/validate-config.py project-config.yaml
```

**Template Rendering:**
```bash
python3 scripts/render-template.py \
  -c project-config.yaml \
  -t templates/CLAUDE.md.template \
  -o CLAUDE.md
```

**Manual Testing:**
- Deploy to test project
- Run `/vibey` initialization
- Test relevant workflows
- Verify quality gates

---

## Code Standards

### Markdown Files

- Use clear, descriptive headings
- Include examples and code blocks
- Follow existing formatting conventions
- Keep lines under 120 characters where practical

### Python Scripts

- Python 3.7+ compatibility
- Type hints for functions
- Docstrings for modules and functions
- Error handling with clear messages
- Dependencies: PyYAML, Jinja2

### YAML Files

- 2-space indentation
- Clear key naming (snake_case)
- Comments for complex sections
- Validate against schema

---

## Quality Standards

### For Agents

- ✅ Clear role and purpose
- ✅ Specific trigger patterns
- ✅ Defined inputs and outputs
- ✅ Quality criteria and validation steps
- ✅ Handoff template references
- ✅ Example usage scenarios

### For Workflows

- ✅ Step-by-step process
- ✅ Agent recommendations per step
- ✅ Duration estimates
- ✅ Prerequisites documented
- ✅ Expected outputs defined
- ✅ Project type variations

### For Templates

- ✅ All Jinja2 variables documented
- ✅ Conditional sections explained
- ✅ Examples provided
- ✅ Clear section structure
- ✅ Schema alignment verified

---

## Common Development Tasks

### Adding a New Agent

1. Create markdown file in appropriate `agents/` subdirectory
2. Follow agent template structure (see existing agents)
3. Define trigger patterns for orchestration modes
4. Specify quality criteria and validation
5. Create or reference handoff template
6. Update documentation and README
7. Test with relevant workflows

### Adding a New Workflow

1. Create markdown file in appropriate `workflows/` subdirectory
2. Define sequential steps with durations
3. Recommend agents for each step
4. Specify project type variations
5. Reference handoff templates
6. Update WORKFLOW_SELECTION_GUIDE.md
7. Test end-to-end execution

### Adding a New Template

1. Create template in `templates/handoffs/`
2. Use Jinja2 syntax for variables
3. Ensure all variables exist in schema
4. Provide examples and guidance
5. Reference from relevant agents/workflows
6. Test rendering with sample config

### Updating Configuration Schema

1. Edit `config/schema.yaml`
2. Update all affected templates
3. Update config examples in `config/config-templates/`
4. Update documentation
5. Test validation and rendering
6. Update version number if breaking change

---

## Git Workflow

### Branch Strategy

- `main` - Production-ready code
- Feature branches - `feature/description`
- Bugfix branches - `bugfix/description`
- Documentation - `docs/description`

### Commit Messages

Format: `<type>: <description>`

Types:
- `feat:` - New feature (agent, workflow, template)
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code restructuring
- `test:` - Test additions/changes
- `chore:` - Maintenance tasks

Example: `feat: add performance optimization workflow`

### Before Committing

- [ ] Code follows existing patterns
- [ ] Documentation updated
- [ ] Examples provided if applicable
- [ ] Changes tested manually
- [ ] No sensitive data included

---

## Troubleshooting Development Issues

### Python Script Errors

**"PyYAML not found" or "Jinja2 not found":**
```bash
pip install pyyaml jinja2
```

**Config validation fails:**
- Check `config/schema.yaml` for required fields
- Ensure all keys in config match schema
- Validate YAML syntax

**Template rendering fails:**
- Check Jinja2 syntax
- Ensure all variables exist in config
- Check for typos in variable names

### Framework Testing Issues

**Agents not triggering:**
- Check trigger patterns in agent files
- Verify orchestration mode in config
- Review CLAUDE.md generation

**Quality gates failing:**
- Review quality gate requirements
- Check threshold values
- Verify audit scripts work

---

## Release Process

### Version Numbering

Format: `MAJOR.MINOR.PATCH`
- `MAJOR` - Breaking changes (schema, API)
- `MINOR` - New features (agents, workflows)
- `PATCH` - Bug fixes, documentation

### Pre-Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers updated
- [ ] Examples tested
- [ ] README.md current

### Release Steps

1. Update version in relevant files
2. Update CHANGELOG.md
3. Create release branch
4. Final testing
5. Merge to main
6. Tag release
7. Update GitHub release notes

---

## Key Decisions and Rationale

### Why Markdown for Agents?

- Human-readable instructions
- Easy to version control
- Simple to edit and maintain
- Claude Code's native format
- Portable across platforms (with adaptation)

### Why Three Orchestration Modes?

- **Simple** - Easy to learn, predictable behavior
- **Balanced** - Smart defaults, minimal cognitive load
- **Tiered** - Handles complex multi-agent scenarios
- Allows users to choose based on project complexity

### Why Quality Gates?

- Prevent shipping incomplete work
- Enforce best practices
- Catch security issues early
- Improve code quality systematically

### Why Dual-Mode /vibey Command?

- Single entry point for all framework interactions
- Context-aware behavior
- Reduces cognitive load
- Natural progression: initialize → manage

---

## Important Notes

### When Working on Platform Ports

1. **Extract concepts first** - Agents, workflows, quality gates are portable
2. **Adapt implementation** - Platform-specific mechanisms differ
3. **Test thoroughly** - Validate orchestration works
4. **Document differences** - Help users understand platform constraints
5. **Maintain core value** - Specialized agents + structured workflows + quality gates

### When Adding Features

1. **Consider all orchestration modes** - How does this work in Simple/Balanced/Tiered?
2. **Think about project types** - Web-app, API, ML, data platform, infrastructure
3. **Maintain quality standards** - Does this uphold framework principles?
4. **Document thoroughly** - Users should understand purpose and usage
5. **Test with real scenarios** - Validate with actual projects

---

## Resources

### Documentation
- **README.md** - Main framework documentation
- **docs/** - Comprehensive guides and references
- **docs/development/ROADMAP.md** - Multi-platform strategy

### External References
- **Goose Framework:** https://block.github.io/goose/
- **Cursor 2.0:** https://cursor.com/
- **MCP Protocol:** https://github.com/anthropics/mcp
- **Claude Code:** https://docs.claude.com/claude-code

---

## Contact & Contribution

### Reporting Issues

- GitHub Issues for bug reports
- Include framework version
- Provide reproduction steps
- Attach relevant config/logs

### Contributing

- Fork repository
- Create feature branch
- Follow code standards
- Write clear commit messages
- Submit pull request
- Respond to review feedback

---

## Session Context

**Last Major Update:** 2025-11-04
**Phase Completed:** Phase 12 (Vibey Manager)
**Next Milestone:** Default CLAUDE.md + Platform compatibility work

**Recent Changes:**
- Added comprehensive platform compatibility assessment
- Created detailed multi-platform roadmap
- Documented Goose and Cursor port requirements
- Established success metrics and risk assessment

**Current Focus:**
- Maintaining Claude Code production quality
- Planning Goose MVP port (recommended next step)
- Exploring docs-driven architecture migration

---

**Framework Version:** 1.1 (Production Ready)
**Target Platforms:** Claude Code (current), Goose (planned), Cursor (research)
**Status:** Ready for multi-platform expansion
