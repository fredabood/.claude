# Guides

In-depth guides for using the Vibey framework effectively.

---

## Available Guides

### [Orchestration Guide](ORCHESTRATION.md)
**Length:** ~500 lines
**Topics:** Orchestration modes, agent selection, coordinator agent

**Learn about:**
- **Three orchestration modes:**
  - Simple & Transparent (keyword-based)
  - Balanced & Discoverable (pattern matching, ⭐ recommended)
  - Intelligent & Adaptive (tiered coordination)
- How Claude automatically selects agents
- Agent trigger patterns
- Coordinator agent for complex tasks
- How to change orchestration modes
- Troubleshooting agent selection

**Read this when:**
- You want to understand how Claude picks agents
- You're choosing an orchestration mode
- You want to optimize agent selection for your project
- Agents aren't being triggered as expected

---

### [Workflow Selection Guide](WORKFLOW_SELECTION_GUIDE.md)
**Length:** ~400 lines
**Topics:** Workflows, when to use each, workflow sequences

**Learn about:**
- All 15 available workflows
- When to use each workflow
- How workflows chain together
- Workflow duration estimates
- Input/output artifacts for each workflow

**Available Workflows:**
- Sprint Planning & Roadmap Management
- Single Feature Development
- ML Model Development
- Infrastructure Setup
- Performance Optimization
- Security Audit
- And 9 more...

**Read this when:**
- You're planning a complex task
- You want to know which workflow to use
- You need to estimate time for a workflow
- You're chaining multiple workflows together

---

## Other Resources

### Agents
All 12 specialized agents are documented in the `agents/` directory:
- `agents/planning/` - Sprint Planning, Researcher
- `agents/development/` - Web Developer, ML Engineer
- `agents/quality/` - Security, Observability, Performance
- `agents/documentation/` - Documentation Engineer, Diagram Engineer, Git Committer
- `agents/core/` - Coordinator

### Workflows
All 15 workflows are documented in the `workflows/` directory:
- `workflows/planning/` - Sprint planning, architecture review
- `workflows/execution/` - Feature development, ML model development
- `workflows/operations/` - Infrastructure, performance, security

### Templates
All 22 handoff templates are in the `templates/` directory:
- `templates/handoffs/` - API specs, security reports, research summaries, etc.
- `templates/CLAUDE.md.template` - Project context template

---

## Quick Links

**New user?** Start with [Getting Started](../getting-started/)

**Looking for specific info?** Check [Reference](../reference/)

**Framework developer?** See [Development](../development/)

---

**[← Back to Documentation Index](../README.md)**
