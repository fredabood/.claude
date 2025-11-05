# Reference Documentation

Detailed reference for all Vibey framework components.

---

## Framework Components

### Agents (12 Total)

**Planning Agents**
- `agents/planning/sprint-planning.md` - Sprint planning and roadmap management
- `agents/planning/researcher.md` - Technology research and API documentation

**Development Agents**
- `agents/development/web-developer.md` - Frontend and backend development
- `agents/development/ml-engineer.md` - ML model development and training

**Quality Agents**
- `agents/quality/security-reviewer.md` - Security audits and OWASP compliance
- `agents/quality/observability-engineer.md` - Logging, monitoring, alerting
- `agents/quality/performance-engineer.md` - Performance optimization

**Documentation Agents**
- `agents/documentation/documentation-engineer.md` - Technical documentation
- `agents/documentation/diagram-engineer.md` - Architecture and sequence diagrams
- `agents/documentation/git-committer.md` - Git operations and commits

**Core Agents**
- `agents/core/coordinator.md` - Intelligent task coordination (Tiered mode)
- `agents/core/vibey-manager.md` - Framework management and configuration

**Architecture Agent**
- `agents/architecture/architecture-specialist.md` - Architecture review and design

---

### Workflows (16 Total)

**Planning Workflows**
- `workflows/planning/sprint-planning.md` - Sprint planning process
- `workflows/planning/architecture-review.md` - Architecture review process
- `workflows/planning/codebase-audit-discovery.md` - Automated project analysis

**Execution Workflows**
- `workflows/execution/single-feature-development.md` - Feature development lifecycle
- `workflows/execution/ml-model-development.md` - ML model training lifecycle
- `workflows/execution/parallel-feature-development.md` - Multiple features simultaneously

**Operations Workflows**
- `workflows/operations/infrastructure-setup.md` - IaC deployment
- `workflows/operations/performance-optimization.md` - Performance tuning
- `workflows/operations/security-audit.md` - Security review process
- `workflows/operations/logging-audit.md` - Logging audit process

**Special Workflows**
- `workflows/framework-initialization.md` - `/vibey` initialization process
- And 5 more...

---

### Templates (22 Total)

**Handoff Templates**
Located in `templates/handoffs/`:
- API specifications
- Security reports
- Research summaries
- Architecture decision records
- ML evaluation reports
- Test plans
- Deployment plans
- Performance reports
- And 13 more...

**Project Templates**
- `templates/CLAUDE.md.template` - Project context template
- `templates/PROJECT-CONTEXT.md.template` - Discovery context template
- `templates/sprint-state.yaml.template` - Sprint state structure
- `templates/sprint-retrospective.md.template` - Sprint retrospective format

---

## Configuration Reference

### Config Schema
**File:** `config/schema.yaml` (400+ lines)

**Sections:**
- `project` - Project metadata (name, type, description)
- `technology_stack` - Tech stack configuration
- `framework` - Framework settings (orchestration mode, quality gates)
- `quality_gates` - Quality gate thresholds
- `testing`, `logging`, `deployment` - Tool-specific configuration

### Config Templates
**Directory:** `config/config-templates/`

**Available Templates:**
- `web-app-config.yaml` - Full-stack web application
- `api-config.yaml` - API service
- `ml-.claude/project-config.yaml` - ML project
- `data-platform-config.yaml` - Data platform
- `infrastructure-config.yaml` - Infrastructure project

---

## Directory Structure

```
.claude/                              # Framework root
├── agents/                           # 12 specialized agents
│   ├── core/
│   ├── planning/
│   ├── development/
│   ├── quality/
│   ├── documentation/
│   └── architecture/
├── workflows/                        # 16 structured workflows
│   ├── planning/
│   ├── execution/
│   └── operations/
├── templates/                        # 22 handoff templates
│   ├── handoffs/
│   ├── CLAUDE.md.template
│   ├── PROJECT-CONTEXT.md.template
│   ├── sprint-state.yaml.template
│   └── sprint-retrospective.md.template
├── commands/                         # Slash commands
│   └── vibey.md
├── config/                           # Configuration
│   ├── schema.yaml
│   └── config-templates/
└── scripts/                          # 10 Python utilities
    ├── generate-config.py
    ├── update-config.py
    ├── manage-project-context.py
    ├── create-sprint-state.py
    ├── query-sprint-state.py
    ├── update-sprint-state.py
    ├── update-sprint-marker.py
    ├── check-version.py
    ├── rollback-framework.py
    ├── validate-config.py
    └── render-template.py
```

---

## Usage

### Agents
Agents are automatically selected by Claude based on:
- Orchestration mode (Simple/Balanced/Tiered)
- Trigger patterns (keywords, contexts, file patterns)
- Current workflow phase
- Project type

**Manual invocation:** Name the agent explicitly
```
"Run a security review using the security reviewer agent"
```

### Workflows
Workflows guide multi-step processes. Claude follows workflows automatically based on the task.

**Manual selection:** Specify the workflow
```
"Follow the single-feature-development workflow for user authentication"
```

### Templates
Templates structure communication between agents. Claude uses templates automatically during workflows.

**Manual generation:** Reference the template
```
"Generate an API specification using the API spec template"
```

---

## Quick Links

**New user?** Start with [Getting Started](../getting-started/)

**Need guidance?** Read the [Guides](../guides/)

**Framework developer?** See [Development](../development/)

---

**[← Back to Documentation Index](../README.md)**
