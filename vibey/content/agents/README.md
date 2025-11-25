# Vibey Framework Agents

This directory contains specialized agents that form the core of the Vibey Agent Framework. Each agent has specific expertise and responsibilities, working together to handle complex software development tasks.

## Agent Overview

**Total Agents:** 19
**Categories:** Core (2), Planning (2), Development (7), Quality (4), Documentation (3), Architecture (1)

---

## 📂 Agent Categories

### Core Agents (2)

**Location:** `core/`

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **coordinator** | Intelligent routing and orchestration | Complex requests requiring multiple agents |
| **vibey-manager** | Framework management and configuration | Managing Vibey settings, agents, quality gates |

### Planning Agents (2)

**Location:** `planning/`

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **sprint-planning** | Sprint planning and task breakdown | Planning sprints, defining tasks, estimating work |
| **researcher** | Technical research and analysis | Investigating technologies, comparing approaches |

### Development Agents (7)

**Location:** `development/`

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **web-developer** | Full-stack web applications | Building web UIs, APIs, dashboards |
| **backend-engineer** | Backend APIs and services | REST/GraphQL APIs, backend logic, auth |
| **frontend-engineer** | Frontend UI components | React/Vue components, responsive UI, state management |
| **database-specialist** | Database design and optimization | Schema design, SQL queries, migrations, indexing |
| **infrastructure-engineer** | Infrastructure as Code, DevOps | Terraform, Kubernetes, CI/CD, cloud resources |
| **ml-engineer** | Machine learning models | Training models, ML pipelines, model deployment |

### Quality Agents (4)

**Location:** `quality/`

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **test-engineer** | Automated testing | Writing unit/integration/E2E tests, test coverage |
| **security-reviewer** | Security audits | Code security review, vulnerability scanning |
| **performance-engineer** | Performance optimization | Profiling, optimization, scalability |
| **observability-engineer** | Monitoring and logging | APM, logging, metrics, alerting |

**Note:** `security-reviewer` also responds to "security-auditor" trigger patterns.

### Documentation Agents (3)

**Location:** `documentation/`

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **documentation-engineer** | Project documentation | README, API docs, user guides |
| **documentation-maintenance-engineer** | Documentation updates | Keeping docs in sync with code |
| **diagram-engineer** | Architecture diagrams | System diagrams, flowcharts, sequence diagrams |
| **git-committer** | Git commits and PRs | Creating commits, pull requests |

**Note:** `documentation-engineer` also responds to "docs-writer" trigger patterns.

### Architecture Agents (1)

**Location:** `architecture/`

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **architecture-agent** | System architecture and ADRs | System design, ADRs, architecture reviews |

---

## 🎯 Agent Trigger Patterns

Agents are invoked based on:

1. **Keywords** - Specific terms in user requests
2. **Context** - Current phase (planning, development, quality)
3. **File Patterns** - Files being worked on
4. **Priority** - Urgency and importance

### Example Triggers

**"Write tests for the user service"**
→ Triggers: `test-engineer`
- Keywords: "write tests"
- Context: Quality assurance phase

**"Design the system architecture"**
→ Triggers: `architecture-agent`
- Keywords: "system architecture", "design"
- Context: Planning/design phase

**"Build a REST API for users"**
→ Triggers: `backend-engineer`
- Keywords: "REST API", "backend"
- Context: Development phase

**"Create a responsive dashboard"**
→ Triggers: `frontend-engineer`
- Keywords: "dashboard", "responsive"
- Context: Frontend development

---

## 🔄 Agent Orchestration Modes

### Simple Mode (Keyword-based)
- User explicitly names the agent or uses clear keywords
- Direct agent invocation
- Example: "Use test-engineer to write tests"

### Balanced Mode (Pattern matching)
- Framework matches patterns to agents
- Smart routing based on keywords + context
- Example: "Write comprehensive tests" → `test-engineer`

### Tiered Mode (Coordinator-based)
- Complex requests go through `coordinator`
- Coordinator determines which agents to use
- Handles multi-agent workflows
- Example: "Build a new feature with tests and docs"

---

## 📋 Agent Template Structure

Each agent follows a standard structure:

```markdown
# Agent Name

**Role:** Brief description
**Type:** Category (Development, Quality, etc.)
**When to Use:** Clear usage scenarios

**Trigger Patterns:**
- Keywords, contexts, file patterns, priority

## 🎯 Purpose
Core responsibilities and goals

## 📥 Required Inputs
What the agent needs to start work

## 🛠️ Workflow
Step-by-step process

## 📤 Outputs and Deliverables
What the agent produces

## ✅ Quality Criteria
Success metrics and validation

## 🤝 Handoffs
Integration with other agents
```

---

## 🆕 Recently Added Agents (v1.3.0)

### New Agents (5)

1. **test-engineer** (CRITICAL)
   - Most referenced missing agent (67 refs)
   - Essential for quality-first workflows
   - Comprehensive testing capabilities

2. **architecture-agent** (HIGH)
   - System design and ADRs
   - C4 model diagrams
   - Architectural decision documentation

3. **backend-engineer** (MEDIUM)
   - Specialized backend API development
   - Based on web-developer template
   - Focus on server-side logic

4. **frontend-engineer** (MEDIUM)
   - Specialized frontend/UI development
   - Component-based architecture
   - State management expertise

5. **database-specialist** (MEDIUM)
   - Database schema design
   - Query optimization
   - Migration management

6. **infrastructure-engineer** (MEDIUM)
   - Infrastructure as Code (IaC)
   - CI/CD pipelines
   - Container orchestration

### Enhanced Agents (2)

1. **documentation-engineer**
   - Added "docs-writer" alias
   - Additional trigger patterns for compatibility
   - Maintains all existing functionality

2. **security-reviewer**
   - Added "security-auditor" alias
   - Security audit terminology
   - Enhanced trigger patterns

---

## 🚀 Using Agents

### Direct Invocation
```
"Use test-engineer to write unit tests for the user service"
"Ask backend-engineer to create a REST API"
"Have architecture-agent design the system"
```

### Natural Language
```
"Write comprehensive tests for all components"
→ Framework routes to test-engineer

"Design the database schema for our app"
→ Framework routes to database-specialist

"Set up CI/CD pipeline for deployment"
→ Framework routes to infrastructure-engineer
```

### Multi-Agent Workflows
```
"Build a new user authentication feature with tests and docs"
→ Coordinator orchestrates:
  1. architecture-agent: Design auth architecture
  2. backend-engineer: Implement auth API
  3. database-specialist: Design user schema
  4. test-engineer: Write auth tests
  5. security-reviewer: Security audit
  6. documentation-engineer: Document API
```

---

## 📊 Agent Statistics

**Agent Coverage:** 100% (0 missing agents)
- Previously: 13 agents (38% gap)
- Now: 19 agents (gap closed)

**Most Referenced Agents:**
1. test-engineer (67 refs) ✅ Implemented
2. documentation-engineer/docs-writer (55+ refs) ✅ Enhanced
3. security-reviewer/security-auditor (24 refs) ✅ Enhanced
4. backend-engineer (new) ✅ Implemented
5. frontend-engineer (new) ✅ Implemented

**Agent Categories:**
- Development: 7 agents (37%)
- Quality: 4 agents (21%)
- Documentation: 3 agents (16%)
- Planning: 2 agents (11%)
- Core: 2 agents (11%)
- Architecture: 1 agent (5%)

---

## 🛠️ Adding New Agents

To add a new agent:

1. **Choose the right category** - core, planning, development, quality, documentation, architecture
2. **Follow the template structure** - See existing agents for reference
3. **Define clear trigger patterns** - Keywords, contexts, file patterns
4. **Document workflows** - Step-by-step processes
5. **Specify quality criteria** - Success metrics
6. **Test with real scenarios** - Validate agent behavior
7. **Update this README** - Add to the appropriate category

### Agent Naming Conventions

- Use descriptive, role-based names (e.g., `test-engineer`, `database-specialist`)
- Lowercase with hyphens (e.g., `backend-engineer`, not `BackendEngineer`)
- Avoid generic names (use `test-engineer` not `tester`)
- Be consistent with existing agents

---

## 📚 Agent Development Guidelines

### Quality Standards
- ✅ Clear purpose and responsibilities
- ✅ Specific trigger patterns for routing
- ✅ Defined inputs and outputs
- ✅ Step-by-step workflow documentation
- ✅ Quality criteria and validation steps
- ✅ Handoff protocols with other agents
- ✅ Example usage scenarios

### Best Practices
- Keep agents focused on specific domains
- Avoid overlap with existing agents
- Provide clear handoff points
- Include practical examples
- Document common patterns
- Consider multi-agent workflows

---

## 🔗 Related Documentation

- [Agent Development Guide](../docs/guides/AGENT_DEVELOPMENT.md)
- [Orchestration Guide](../docs/guides/ORCHESTRATION.md)
- [Workflow Selection](../docs/guides/WORKFLOW_SELECTION_GUIDE.md)
- [Framework Roadmap](../docs/FRAMEWORK_ROADMAP.md)

---

**Version:** 1.3.0
**Last Updated:** 2025-11-11
**Maintained By:** Vibey Framework Team

**Changelog:**
- v1.3.0 (2025-11-11): Added 6 new agents, enhanced 2 existing agents, closed 38% agent gap
- v1.2.0 (2024-11-05): Added Vibey Manager agent
- v1.1.0 (2024-10-15): Sprint state management integration
- v1.0.0 (2024-09-01): Initial production release with 13 agents
