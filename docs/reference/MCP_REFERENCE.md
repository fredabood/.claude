# MCP Server Reference

**Server:** vibey-roadmap
**Version:** 2.5.0

**Generated:** 2025-12-29T00:19:51.895947+00:00

This document provides comprehensive reference documentation for the Vibey MCP (Model Context Protocol) server, including all tools, resources, and prompts available for AI assistant integration.

| Component | Count |
|-----------|-------|
| Tools | 76 |
| Resources | 8 |
| Prompts | 4 |

---

## When to Use MCP vs CLI

### Use MCP Tools When:

- **AI Assistant Integration** - Working within Claude, Cursor, or other AI tools
- **Programmatic Access** - Building automation or integrations
- **Structured Data** - Need JSON responses for processing
- **Context Preservation** - AI needs to maintain conversation context

### Use CLI Commands When:

- **Terminal Workflows** - Direct command-line interaction
- **Shell Scripts** - Automation via bash/shell
- **Human Readable** - Want formatted, colorized output
- **Quick Operations** - One-off commands

### Common Operations Mapping

| Operation | CLI Command | MCP Tool |
|-----------|-------------|----------|
| Get status | `vibey roadmap status` | `roadmap_status` |
| Start task | `vibey roadmap start <id>` | `task_start` |
| Complete task | `vibey roadmap complete <id>` | `task_complete` |
| Query task | `vibey roadmap show <id>` | `task_query` |
| List sprints | `vibey roadmap list sprints` | `sprint_list` |
| Deploy config | `vibey deploy run --platform X` | N/A (CLI only) |

---

## Table of Contents

- [Quick Reference](#quick-reference)
- [Tools](#tools)
  - [Task Tools](#task-tools)
  - [Sprint Tools](#sprint-tools)
  - [Query Tools](#query-tools)
  - [Content Tools](#content-tools)
  - [Agent Tools](#agent-tools)
  - [Workflow Tools](#workflow-tools)
  - [Handoff Tools](#handoff-tools)
- [Resources](#resources)
  - [Handoffs Resources](#handoffs-resources)
  - [Workflows Resources](#workflows-resources)
- [Prompts](#prompts)

---

## Quick Reference

### Tools by Category

| Category | Count | Description |
|----------|-------|-------------|
| Agent | 19 | Agent invocation tools |
| Content | 7 | Content management (list, show, search) |
| Handoff | 22 | Handoff template tools |
| Query | 5 | Roadmap queries and status checks |
| Sprint | 4 | Sprint management and progress tracking |
| Task | 3 | Task lifecycle management (start, complete, query) |
| Workflow | 16 | Workflow execution tools |

### Resources by Provider

| Provider | Templates | URI Pattern |
|----------|-----------|-------------|
| HandoffResourceProvider | 4 | `vibey://handoffs/...` |
| WorkflowResourceProvider | 4 | `vibey://workflows/...` |

---

## Tools

MCP tools enable AI assistants to interact with the Vibey roadmap system. Each tool has a defined input schema and produces structured output.

### Task Tools

Task tools manage individual task lifecycle - starting, completing, and querying tasks.

| Tool | Description |
|------|-------------|
| [`vibey_complete_task`](#vibey-complete-task) | Mark a task as completed and set completion timestamp |
| [`vibey_query_task`](#vibey-query-task) | Get detailed information about a specific task |
| [`vibey_start_task`](#vibey-start-task) | Mark a task as in progress and set start timestamp |

#### `vibey_complete_task`

**Complete Task**

Mark a task as completed and set completion timestamp

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task_id` | `string` | Yes | Task ID (e.g., 'mcp-server-1-task-001') |
| `actual_tokens` | `integer` | No | Actual tokens used (optional) |

**Examples:**

*Complete a task with token count:*

```json
{
  "task_id": "01KC2D0JK7READW9KAK1HBX4A5",
  "actual_tokens": 15000
}
```

*Source: `vibey/mcp/tools/task_tools.py`*

---

#### `vibey_query_task`

**Query Task**

Get detailed information about a specific task

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task_id` | `string` | Yes | Task ID to query |

**Examples:**

*Query task details:*

```json
{
  "task_id": "01KC2D0JK7READW9KAK1HBX4A5"
}
```

*Source: `vibey/mcp/tools/task_tools.py`*

---

#### `vibey_start_task`

**Start Task**

Mark a task as in progress and set start timestamp

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task_id` | `string` | Yes | Task ID (e.g., 'mcp-server-1-task-001') |

**Examples:**

*Start a task by ULID:*

```json
{
  "task_id": "01KC2D0JK7READW9KAK1HBX4A5"
}
```

*Start a task by slug:*

```json
{
  "task_id": "mcp-server-1-task-001"
}
```

*Source: `vibey/mcp/tools/task_tools.py`*

---

### Sprint Tools

Sprint tools handle sprint management including starting, completing, and progress tracking.

| Tool | Description |
|------|-------------|
| [`vibey_complete_sprint`](#vibey-complete-sprint) | Mark a sprint as completed (requires all tasks complete) |
| [`vibey_query_sprint`](#vibey-query-sprint) | Get detailed information about a specific sprint |
| [`vibey_refresh_progress`](#vibey-refresh-progress) | Recalculate all progress metrics and trigger status auto-progression |
| [`vibey_start_sprint`](#vibey-start-sprint) | Mark a sprint as in progress and set start timestamp |

#### `vibey_complete_sprint`

**Complete Sprint**

Mark a sprint as completed (requires all tasks complete)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `sprint_id` | `string` | Yes | Sprint ID (e.g., 'mcp-server-1') |

**Examples:**

*Complete a sprint:*

```json
{
  "sprint_id": "01KC2D0JK8CHXNPPB2V3M632C1"
}
```

*Source: `vibey/mcp/tools/sprint_tools.py`*

---

#### `vibey_query_sprint`

**Query Sprint**

Get detailed information about a specific sprint

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `sprint_id` | `string` | Yes | Sprint ID to query |

**Examples:**

*Query sprint details:*

```json
{
  "sprint_id": "01KC2D0JK8CHXNPPB2V3M632C1"
}
```

*Source: `vibey/mcp/tools/sprint_tools.py`*

---

#### `vibey_refresh_progress`

**Refresh Progress**

Recalculate all progress metrics and trigger status auto-progression

**Parameters:** None

**Examples:**

*Refresh all progress counters:*

```json
{}
```

*Source: `vibey/mcp/tools/sprint_tools.py`*

---

#### `vibey_start_sprint`

**Start Sprint**

Mark a sprint as in progress and set start timestamp

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `sprint_id` | `string` | Yes | Sprint ID (e.g., 'mcp-server-1') |

**Examples:**

*Start a sprint by ULID:*

```json
{
  "sprint_id": "01KC2D0JK8CHXNPPB2V3M632C1"
}
```

*Source: `vibey/mcp/tools/sprint_tools.py`*

---

### Query Tools

Query tools provide read-only access to roadmap data including tracks, blockers, and status.

| Tool | Description |
|------|-------------|
| [`vibey_list_blockers`](#vibey-list-blockers) | List all current blockers across the roadmap or for a specific object |
| [`vibey_list_dependencies`](#vibey-list-dependencies) | List dependencies for a specific object |
| [`vibey_query_standards`](#vibey-query-standards) | Get effective standards for a roadmap item with inheritance chain |
| [`vibey_query_track`](#vibey-query-track) | Get detailed information about a specific track |
| [`vibey_roadmap_status`](#vibey-roadmap-status) | Get overall roadmap status summary |

#### `vibey_list_blockers`

**List Blockers**

List all current blockers across the roadmap or for a specific object

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `object_id` | `string` | No | Optional: filter by specific object ID (track, sprint, or task) |

**Examples:**

*List all blocked items:*

```json
{}
```

*List blockers for a specific track:*

```json
{
  "track_id": "01KC2D0JK6JC6706H9WP2NH5DA"
}
```

*Source: `vibey/mcp/tools/query_tools.py`*

---

#### `vibey_list_dependencies`

**List Dependencies**

List dependencies for a specific object

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `object_id` | `string` | Yes | Object ID to query dependencies for |
| `include_satisfied` | `boolean` | No | Include satisfied dependencies (default: false) (default: `False`) |

*Source: `vibey/mcp/tools/query_tools.py`*

---

#### `vibey_query_standards`

**Query Standards**

Get effective standards for a roadmap item with inheritance chain

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `item_id` | `string` | Yes | Item ID (track, sprint, or task) |
| `show_inheritance` | `boolean` | No | Show inheritance source breakdown (default: true) (default: `True`) |

*Source: `vibey/mcp/tools/query_tools.py`*

---

#### `vibey_query_track`

**Query Track**

Get detailed information about a specific track

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `track_id` | `string` | Yes | Track ID (e.g., 'mcp-server') |

**Examples:**

*Query track details:*

```json
{
  "track_id": "01KC2D0JK6JC6706H9WP2NH5DA"
}
```

*Source: `vibey/mcp/tools/query_tools.py`*

---

#### `vibey_roadmap_status`

**Roadmap Status**

Get overall roadmap status summary

**Parameters:** None

**Examples:**

*Get overall roadmap status:*

```json
{}
```

*Source: `vibey/mcp/tools/query_tools.py`*

---

### Content Tools

Content tools manage framework content including agents, workflows, and handoffs.

| Tool | Description |
|------|-------------|
| [`vibey_content_create`](#vibey-content-create) | Create new framework content (agent, workflow, template, handoff) |
| [`vibey_content_delete`](#vibey-content-delete) | Delete framework content (moves to trash) |
| [`vibey_content_list`](#vibey-content-list) | List framework content (agents, workflows, templates, handoffs) |
| [`vibey_content_search`](#vibey-content-search) | Search framework content by keywords |
| [`vibey_content_show`](#vibey-content-show) | Show details of a specific content item |
| [`vibey_content_update`](#vibey-content-update) | Update existing framework content metadata |
| [`vibey_content_validate`](#vibey-content-validate) | Validate content frontmatter |

#### `vibey_content_create`

**Create Content**

Create new framework content (agent, workflow, template, handoff)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `content_id` | `string` | Yes | ID for the new content (e.g., 'my-agent') |
| `content_type` | `string` | Yes | Type of content to create (enum: `agent`, `workflow`, `template`, `handoff`) |
| `name` | `string` | Yes | Display name for the content |
| `body` | `string` | No | Body content (markdown) |
| `category` | `string` | No | Category (subdirectory, e.g., 'core', 'planning') |
| `description` | `string` | No | Content description |
| `subtype` | `string` | No | Subtype (e.g., 'core', 'development' for agents) |

*Source: `vibey/mcp/tools/content_tools.py`*

---

#### `vibey_content_delete`

**Delete Content**

Delete framework content (moves to trash)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `content_id` | `string` | Yes | ID of content to delete |
| `content_type` | `string` | No | Content type (optional, speeds up lookup) (enum: `agent`, `workflow`, `template`, `handoff`) |
| `force` | `boolean` | No | Delete even if referenced by other content (default: `False`) |

*Source: `vibey/mcp/tools/content_tools.py`*

---

#### `vibey_content_list`

**List Content**

List framework content (agents, workflows, templates, handoffs)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `category` | `string` | No | Filter by category (subdirectory, e.g., 'core', 'planning') |
| `content_type` | `string` | No | Filter by content type (enum: `agent`, `workflow`, `template`, `handoff`, `schema`, `example`) |

**Examples:**

*List all agents:*

```json
{
  "content_type": "agents"
}
```

*List all workflows:*

```json
{
  "content_type": "workflows"
}
```

*Source: `vibey/mcp/tools/content_tools.py`*

---

#### `vibey_content_search`

**Search Content**

Search framework content by keywords

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | `string` | Yes | Search query (keywords) |
| `content_type` | `string` | No | Filter by content type (enum: `agent`, `workflow`, `template`, `handoff`, `schema`, `example`) |
| `limit` | `integer` | No | Maximum results (default: 20) (default: `20`) |

**Examples:**

*Search for security-related content:*

```json
{
  "query": "security audit"
}
```

*Source: `vibey/mcp/tools/content_tools.py`*

---

#### `vibey_content_show`

**Show Content**

Show details of a specific content item

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `content_id` | `string` | Yes | Content ID to show (e.g., 'coordinator', 'sprint-planning') |
| `content_type` | `string` | No | Content type (speeds up lookup) (enum: `agent`, `workflow`, `template`, `handoff`, `schema`, `example`) |
| `include_body` | `boolean` | No | Include full body text (default: `False`) |

**Examples:**

*Show a workflow definition:*

```json
{
  "content_type": "workflows",
  "item_id": "sprint-planning"
}
```

*Source: `vibey/mcp/tools/content_tools.py`*

---

#### `vibey_content_update`

**Update Content**

Update existing framework content metadata

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `content_id` | `string` | Yes | ID of content to update |
| `updates` | `object` | Yes | Field updates (e.g., {'version': '1.1.0', 'type': 'core'}) |
| `content_type` | `string` | No | Content type (optional, speeds up lookup) (enum: `agent`, `workflow`, `template`, `handoff`) |

*Source: `vibey/mcp/tools/content_tools.py`*

---

#### `vibey_content_validate`

**Validate Content**

Validate content frontmatter

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `content_id` | `string` | No | ID of specific content to validate (optional) |
| `content_type` | `string` | No | Content type to validate (validates all of this type if no content_id) (enum: `agent`, `workflow`, `template`, `handoff`) |

*Source: `vibey/mcp/tools/content_tools.py`*

---

### Agent Tools

Agent tools invoke specialized AI agents defined in the framework.

| Tool | Description |
|------|-------------|
| [`vibey_architecture_agent`](#vibey-architecture-agent) | Design system architecture and create architectural decision records (triggers: ... |
| [`vibey_backend_engineer`](#vibey-backend-engineer) | Build robust backend APIs and services (triggers: api endpoint, backend logic, r... |
| [`vibey_coordinator`](#vibey-coordinator) | Intelligent request router for complex, multi-step workflows (triggers: N/A (coo... |
| [`vibey_database_specialist`](#vibey-database-specialist) | Design and optimize database schemas and queries (triggers: database schema, sql... |
| [`vibey_diagram_engineer`](#vibey-diagram-engineer) | Mermaid diagram generation specialist for architecture documentation (triggers: ... |
| [`vibey_documentation_engineer`](#vibey-documentation-engineer) | Update all project documentation after completing features or tasks (triggers: d... |
| [`vibey_documentation_maintenance_engineer`](#vibey-documentation-maintenance-engineer) | Documentation Maintenance Engineer agent (triggers: update .claude/CLAUDE.md, ma... |
| [`vibey_frontend_engineer`](#vibey-frontend-engineer) | Build modern, responsive user interfaces (triggers: frontend, ui component, reac... |
| [`vibey_git_committer`](#vibey-git-committer) | Create clean, descriptive commits following project conventions (triggers: commi... |
| [`vibey_infrastructure_engineer`](#vibey-infrastructure-engineer) | Build and manage infrastructure using Infrastructure as Code (triggers: infrastr... |
| [`vibey_ml_engineer`](#vibey-ml-engineer) | Machine learning model development, training, evaluation, and deployment (trigge... |
| [`vibey_observability_engineer`](#vibey-observability-engineer) | Logging, monitoring, and observability specialist (triggers: logging, log, monit... |
| [`vibey_performance_engineer`](#vibey-performance-engineer) | Performance optimization specialist for applications, databases, and APIs (trigg... |
| [`vibey_researcher`](#vibey-researcher) | Researcher Agent agent (triggers: research, documentation, API docs, library doc... |
| [`vibey_security_reviewer`](#vibey-security-reviewer) | Review code for security vulnerabilities and best practices (triggers: security,... |
| [`vibey_sprint_planning`](#vibey-sprint-planning) | Sprint Planning Agent agent (triggers: sprint planning, plan sprint, roadmap, it... |
| [`vibey_test_engineer`](#vibey-test-engineer) | Write comprehensive automated tests for code quality assurance (triggers: write ... |
| [`vibey_vibey_manager`](#vibey-vibey-manager) | Agent: Vibey Framework Manager agent |
| [`vibey_web_developer`](#vibey-web-developer) | Build and maintain web applications for user-facing interfaces (triggers: fronte... |

#### `vibey_architecture_agent`

**Architecture Agent**

Design system architecture and create architectural decision records (triggers: architecture, system design, design architecture, technical design, adr)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Architecture Agent |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_backend_engineer`

**Backend Engineer**

Build robust backend APIs and services (triggers: api endpoint, backend logic, rest api, graphql, database query)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Backend Engineer |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_coordinator`

**Coordinator Agent**

Intelligent request router for complex, multi-step workflows (triggers: N/A (coordinator is triggered by complexity, not keywords))

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Coordinator Agent |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_database_specialist`

**Database Specialist**

Design and optimize database schemas and queries (triggers: database schema, sql query, optimize database, database migration, index)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Database Specialist |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_diagram_engineer`

**Diagram Engineer**

Mermaid diagram generation specialist for architecture documentation (triggers: diagram, architecture diagram, flow diagram, sequence diagram, ERD)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Diagram Engineer |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_documentation_engineer`

**Documentation Engineer**

Update all project documentation after completing features or tasks (triggers: documentation, docs, update docs, document, README)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Documentation Engineer |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_documentation_maintenance_engineer`

**Documentation Maintenance Engineer**

Documentation Maintenance Engineer agent (triggers: update .claude/CLAUDE.md, maintain docs, refresh documentation, sync docs, archive sprint)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Documentation Maintenance Engineer |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_frontend_engineer`

**Frontend Engineer**

Build modern, responsive user interfaces (triggers: frontend, ui component, react component, user interface, responsive design)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Frontend Engineer |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_git_committer`

**Git Committer Agent**

Create clean, descriptive commits following project conventions (triggers: commit, git commit, save changes, check in, version control)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Git Committer Agent |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_infrastructure_engineer`

**Infrastructure Engineer**

Build and manage infrastructure using Infrastructure as Code (triggers: infrastructure, terraform, kubernetes, ci/cd pipeline, deployment)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Infrastructure Engineer |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_ml_engineer`

**ML Engineer**

Machine learning model development, training, evaluation, and deployment (triggers: machine learning, ML, model, training, prediction)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the ML Engineer |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_observability_engineer`

**Observability Engineer**

Logging, monitoring, and observability specialist (triggers: logging, log, monitoring, observability, telemetry)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Observability Engineer |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_performance_engineer`

**Performance Engineer**

Performance optimization specialist for applications, databases, and APIs (triggers: performance, slow, optimization, optimize, bottleneck)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Performance Engineer |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_researcher`

**Researcher Agent**

Researcher Agent agent (triggers: research, documentation, API docs, library documentation, investigate)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Researcher Agent |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_security_reviewer`

**Security Reviewer**

Review code for security vulnerabilities and best practices (triggers: security, vulnerability, exploit, OWASP, authentication)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Security Reviewer |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_sprint_planning`

**Sprint Planning Agent**

Sprint Planning Agent agent (triggers: sprint planning, plan sprint, roadmap, iteration, backlog)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Sprint Planning Agent |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_test_engineer`

**Test Engineer**

Write comprehensive automated tests for code quality assurance (triggers: write tests, add tests, test coverage, unit test, integration test)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Test Engineer |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_vibey_manager`

**Agent: Vibey Framework Manager**

Agent: Vibey Framework Manager agent

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Agent: Vibey Framework Manager |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_web_developer`

**Web Developer**

Build and maintain web applications for user-facing interfaces (triggers: frontend, UI, user interface, web app, dashboard)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | `string` | Yes | Task or request for the Web Developer |
| `context` | `string` | No | Additional context about the project or codebase |

*Source: `vibey/mcp/discovery/`*

---

### Workflow Tools

Workflow tools execute predefined development workflows.

| Tool | Description |
|------|-------------|
| [`vibey_workflow_architecture_review`](#vibey-workflow-architecture-review) | Systematic architecture review for sprints, code, infrastructure, and system des... |
| [`vibey_workflow_claude_md_auto_update`](#vibey-workflow-claude-md-auto-update) | Automatically keep .claude/CLAUDE.md up to date as the project evolves (6 steps,... |
| [`vibey_workflow_codebase_audit_discovery`](#vibey-workflow-codebase-audit-discovery) | Comprehensive analysis of existing codebase before first sprint planning (11 ste... |
| [`vibey_workflow_dashboard_visualization_creation`](#vibey-workflow-dashboard-visualization-creation) | Create and deploy dashboards/visualizations with version control and automation ... |
| [`vibey_workflow_documentation_diagrams`](#vibey-workflow-documentation-diagrams) | Create comprehensive technical documentation with professional Mermaid diagrams |
| [`vibey_workflow_documentation_research`](#vibey-workflow-documentation-research) | Research and summarize verbose documentation to prevent context window waste (6 ... |
| [`vibey_workflow_frontend_production_deployment`](#vibey-workflow-frontend-production-deployment) | Package, test, and deploy frontend application to production (9 steps, 1-2 days) |
| [`vibey_workflow_frontend_security_hardening`](#vibey-workflow-frontend-security-hardening) | Comprehensive security implementation and audit for frontend applications (8 ste... |
| [`vibey_workflow_infrastructure_setup`](#vibey-workflow-infrastructure-setup) | End-to-end infrastructure provisioning using Infrastructure-as-Code across multi... |
| [`vibey_workflow_integration_only`](#vibey-workflow-integration-only) | Integrate completed and tested components into the main system (5 steps, 30 minu... |
| [`vibey_workflow_logging_audit`](#vibey-workflow-logging-audit) | Conduct comprehensive logging audit to ensure production readiness (9 steps, 2-3... |
| [`vibey_workflow_ml_model_development`](#vibey-workflow-ml-model-development) | End-to-end machine learning model lifecycle from requirements to production depl... |
| [`vibey_workflow_performance_optimization`](#vibey-workflow-performance-optimization) | Systematic performance optimization cycle for applications, services, and data p... |
| [`vibey_workflow_single_feature_development`](#vibey-workflow-single-feature-development) | Complete development of a single feature from specification to deployment (7 ste... |
| [`vibey_workflow_sprint_planning`](#vibey-workflow-sprint-planning) | Orchestrate sprint planning, prioritization, dependency analysis, and roadmap up... |
| [`vibey_workflow_weekly_sprint`](#vibey-workflow-weekly-sprint) | Execute parallel feature development for weekly sprint completion (1 steps, 3-5 ... |

#### `vibey_workflow_architecture_review`

**Workflow: Architecture Review**

Systematic architecture review for sprints, code, infrastructure, and system design (7 steps, 2-3 days)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `feature_name` | `string` | Yes | Name of the feature or task |
| `requirements` | `string` | Yes | Requirements and acceptance criteria |
| `project_type` | `string` | No | Project type (web-app, api, ml, data-platform) (default: `web-app`) |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_workflow_claude_md_auto_update`

**Workflow: .claude/CLAUDE.md Auto-Update Workflow**

Automatically keep .claude/CLAUDE.md up to date as the project evolves (6 steps, 20-30 minutes)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `feature_name` | `string` | Yes | Name of the feature or task |
| `requirements` | `string` | Yes | Requirements and acceptance criteria |
| `project_type` | `string` | No | Project type (web-app, api, ml, data-platform) (default: `web-app`) |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_workflow_codebase_audit_discovery`

**Workflow: Codebase Audit & Discovery**

Comprehensive analysis of existing codebase before first sprint planning (11 steps, 60-105 minutes (code audit only) OR 10-20 minutes (git history only) OR 70-125 minutes (both))

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `feature_name` | `string` | Yes | Name of the feature or task |
| `requirements` | `string` | Yes | Requirements and acceptance criteria |
| `project_type` | `string` | No | Project type (web-app, api, ml, data-platform) (default: `web-app`) |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_workflow_dashboard_visualization_creation`

**Workflow: Dashboard & Visualization Creation Workflow**

Create and deploy dashboards/visualizations with version control and automation (6 steps, 2-5 days)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `feature_name` | `string` | Yes | Name of the feature or task |
| `requirements` | `string` | Yes | Requirements and acceptance criteria |
| `project_type` | `string` | No | Project type (web-app, api, ml, data-platform) (default: `web-app`) |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_workflow_documentation_diagrams`

**Workflow: Documentation & Diagrams Workflow**

Create comprehensive technical documentation with professional Mermaid diagrams

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `feature_name` | `string` | Yes | Name of the feature or task |
| `requirements` | `string` | Yes | Requirements and acceptance criteria |
| `project_type` | `string` | No | Project type (web-app, api, ml, data-platform) (default: `web-app`) |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_workflow_documentation_research`

**Workflow: Documentation Research & Preprocessing Workflow**

Research and summarize verbose documentation to prevent context window waste (6 steps, 1-2 days)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `feature_name` | `string` | Yes | Name of the feature or task |
| `requirements` | `string` | Yes | Requirements and acceptance criteria |
| `project_type` | `string` | No | Project type (web-app, api, ml, data-platform) (default: `web-app`) |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_workflow_frontend_production_deployment`

**Workflow: Frontend Production Deployment Workflow**

Package, test, and deploy frontend application to production (9 steps, 1-2 days)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `feature_name` | `string` | Yes | Name of the feature or task |
| `requirements` | `string` | Yes | Requirements and acceptance criteria |
| `project_type` | `string` | No | Project type (web-app, api, ml, data-platform) (default: `web-app`) |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_workflow_frontend_security_hardening`

**Workflow: Frontend Security Hardening Workflow**

Comprehensive security implementation and audit for frontend applications (8 steps, 3-5 days)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `feature_name` | `string` | Yes | Name of the feature or task |
| `requirements` | `string` | Yes | Requirements and acceptance criteria |
| `project_type` | `string` | No | Project type (web-app, api, ml, data-platform) (default: `web-app`) |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_workflow_infrastructure_setup`

**Workflow: Infrastructure Setup & Deployment**

End-to-end infrastructure provisioning using Infrastructure-as-Code across multiple environments (12 steps, 12-18 days (2.5-3.5 weeks))

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `feature_name` | `string` | Yes | Name of the feature or task |
| `requirements` | `string` | Yes | Requirements and acceptance criteria |
| `project_type` | `string` | No | Project type (web-app, api, ml, data-platform) (default: `web-app`) |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_workflow_integration_only`

**Workflow: Integration Only**

Integrate completed and tested components into the main system (5 steps, 30 minutes - 2 hours per component)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `feature_name` | `string` | Yes | Name of the feature or task |
| `requirements` | `string` | Yes | Requirements and acceptance criteria |
| `project_type` | `string` | No | Project type (web-app, api, ml, data-platform) (default: `web-app`) |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_workflow_logging_audit`

**Workflow: Logging Audit**

Conduct comprehensive logging audit to ensure production readiness (9 steps, 2-3 days)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `feature_name` | `string` | Yes | Name of the feature or task |
| `requirements` | `string` | Yes | Requirements and acceptance criteria |
| `project_type` | `string` | No | Project type (web-app, api, ml, data-platform) (default: `web-app`) |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_workflow_ml_model_development`

**Workflow: ML Model Development**

End-to-end machine learning model lifecycle from requirements to production deployment (11 steps, 15-25 days (3-5 weeks))

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `feature_name` | `string` | Yes | Name of the feature or task |
| `requirements` | `string` | Yes | Requirements and acceptance criteria |
| `project_type` | `string` | No | Project type (web-app, api, ml, data-platform) (default: `web-app`) |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_workflow_performance_optimization`

**Workflow: Performance Optimization**

Systematic performance optimization cycle for applications, services, and data pipelines (8 steps, 5-8 days (1-1.5 weeks))

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `feature_name` | `string` | Yes | Name of the feature or task |
| `requirements` | `string` | Yes | Requirements and acceptance criteria |
| `project_type` | `string` | No | Project type (web-app, api, ml, data-platform) (default: `web-app`) |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_workflow_single_feature_development`

**Workflow: Single Feature Development**

Complete development of a single feature from specification to deployment (7 steps, 1-3 days (depending on complexity))

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `feature_name` | `string` | Yes | Name of the feature or task |
| `requirements` | `string` | Yes | Requirements and acceptance criteria |
| `project_type` | `string` | No | Project type (web-app, api, ml, data-platform) (default: `web-app`) |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_workflow_sprint_planning`

**Workflow: Sprint Planning & Roadmap Management**

Orchestrate sprint planning, prioritization, dependency analysis, and roadmap updates (9 steps, 3-5 days (ongoing sprints) | 20-40 minutes (first sprint with framework initialization))

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `feature_name` | `string` | Yes | Name of the feature or task |
| `requirements` | `string` | Yes | Requirements and acceptance criteria |
| `project_type` | `string` | No | Project type (web-app, api, ml, data-platform) (default: `web-app`) |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_workflow_weekly_sprint`

**Workflow: Weekly Sprint**

Execute parallel feature development for weekly sprint completion (1 steps, 3-5 days (3-7 features/components))

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `feature_name` | `string` | Yes | Name of the feature or task |
| `requirements` | `string` | Yes | Requirements and acceptance criteria |
| `project_type` | `string` | No | Project type (web-app, api, ml, data-platform) (default: `web-app`) |

*Source: `vibey/mcp/discovery/`*

---

### Handoff Tools

Handoff tools generate structured handoff documents between agents.

| Tool | Description |
|------|-------------|
| [`vibey_handoff_api_spec`](#vibey-handoff-api-spec) | API Specification: Template for api specification (from: backend-engineer, to: f... |
| [`vibey_handoff_application_requirements`](#vibey-handoff-application-requirements) | Application Requirements: Template for application requirements (from: web-devel... |
| [`vibey_handoff_architecture_review`](#vibey-handoff-architecture-review) | Architecture Review Report: Template for architecture review report (from: archi... |
| [`vibey_handoff_codebase_audit_report`](#vibey-handoff-codebase-audit-report) | Codebase Audit Report: Template for codebase audit report (from: researcher, to:... |
| [`vibey_handoff_component_design`](#vibey-handoff-component-design) | Component/Feature Specification: Template for component/feature specification (f... |
| [`vibey_handoff_dashboard_specification`](#vibey-handoff-dashboard-specification) | Dashboard Specification: Template for dashboard specification (from: backend-eng... |
| [`vibey_handoff_database_schema_design`](#vibey-handoff-database-schema-design) | Database Schema Design: Template for database schema design (from: architecture-... |
| [`vibey_handoff_deployment_checklist`](#vibey-handoff-deployment-checklist) | Deployment Checklist: Template for deployment checklist (from: infrastructure-en... |
| [`vibey_handoff_diagram_handoff`](#vibey-handoff-diagram-handoff) | Diagram Handoff: Template for diagram handoff (from: diagram-engineer, to: docum... |
| [`vibey_handoff_documentation_update`](#vibey-handoff-documentation-update) | Documentation Update Handoff: Template for documentation update handoff (from: d... |
| [`vibey_handoff_infrastructure_design`](#vibey-handoff-infrastructure-design) | Infrastructure Design Document: Template for infrastructure design document (fro... |
| [`vibey_handoff_integration`](#vibey-handoff-integration) | Integration Complete: Template for integration complete (from: web-developer, to... |
| [`vibey_handoff_logging_audit_report`](#vibey-handoff-logging-audit-report) | Logging Audit Report: Template for logging audit report (from: observability-eng... |
| [`vibey_handoff_ml_design`](#vibey-handoff-ml-design) | ML Design Document: Template for ml design document (from: architecture-agent, t... |
| [`vibey_handoff_ml_evaluation_report`](#vibey-handoff-ml-evaluation-report) | ML Evaluation Report: Template for ml evaluation report (from: ml-engineer, to: ... |
| [`vibey_handoff_performance_optimization_report`](#vibey-handoff-performance-optimization-report) | Performance Optimization Report: Template for performance optimization report (f... |
| [`vibey_handoff_phase_plan`](#vibey-handoff-phase-plan) | Phase Plan:  -: Template for phase plan:  - (from: sprint-planning, to: web-deve... |
| [`vibey_handoff_research_summary`](#vibey-handoff-research-summary) | Research Summary: Template for research summary (from: researcher, to: sprint-pl... |
| [`vibey_handoff_security_implementation_report`](#vibey-handoff-security-implementation-report) | Security Implementation Report: Template for security implementation report (fro... |
| [`vibey_handoff_security_report`](#vibey-handoff-security-report) | Security Review: Template for security review (from: security-reviewer, to: web-... |
| [`vibey_handoff_sprint_plan`](#vibey-handoff-sprint-plan) | Sprint Plan: Template for sprint plan (from: sprint-planning, to: web-developer,... |
| [`vibey_handoff_test_report`](#vibey-handoff-test-report) | Test Report: Template for test report (from: test-engineer, to: web-developer, s... |

#### `vibey_handoff_api_spec`

**Handoff: API Specification**

API Specification: Template for api specification (from: backend-engineer, to: frontend-engineer, documentation-engineer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `api_base_url` | `string` | Yes | Api Base Url value |
| `api_category` | `string` | Yes | Api Category value |
| `api_class_name` | `string` | Yes | Api Class Name value |
| `api_cost` | `string` | Yes | Api Cost value |
| `api_description` | `string` | Yes | Api Description value |
| `api_detailed_description` | `string` | Yes | Api Detailed Description value |
| `api_documentation_url` | `string` | Yes | Api Documentation Url value |
| `api_full_name` | `string` | Yes | Api Full Name value |
| `api_key_description` | `string` | Yes | Api Key Description value |
| `api_key_registration_url` | `string` | Yes | Api Key Registration Url value |
| `api_name` | `string` | Yes | Api Name value |
| `api_production_url` | `string` | Yes | Api Production Url value |
| `api_provider` | `string` | Yes | Api Provider value |
| `api_purpose` | `string` | Yes | Api Purpose value |
| `api_sandbox_url` | `string` | Yes | Api Sandbox Url value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_application_requirements`

**Handoff: Application Requirements**

Application Requirements: Template for application requirements (from: web-developer, to: test-engineer, documentation-engineer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `acceptance_criterion` | `string` | Yes | Acceptance Criterion value |
| `accessibility_compliance_level` | `string` | Yes | Accessibility Compliance Level value |
| `accessibility_requirement` | `string` | Yes | Accessibility Requirement value |
| `alerting_channels` | `string` | Yes | Alerting Channels value |
| `alt_flow` | `string` | Yes | Alt Flow value |
| `api_architecture` | `string` | Yes | Api Architecture value |
| `api_auth_method` | `string` | Yes | Api Auth Method value |
| `api_style` | `string` | Yes | Api Style value |
| `application_name` | `string` | Yes | Application Name value |
| `application_type` | `string` | Yes | Application Type value |
| `architecture_type` | `string` | Yes | Architecture Type value |
| `assumption` | `string` | Yes | Assumption value |
| `auth_requirements` | `string` | Yes | Auth Requirements value |
| `authentication_method` | `string` | Yes | Authentication Method value |
| `author_name` | `string` | Yes | Author Name value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_architecture_review`

**Handoff: Architecture Review Report**

Architecture Review Report: Template for architecture review report (from: architecture-agent, to: web-developer, backend-engineer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `api_design_notes` | `string` | Yes | Api Design Notes value |
| `api_versioning_notes` | `string` | Yes | Api Versioning Notes value |
| `approval_date_1` | `string` | Yes | Approval Date 1 value |
| `approver_1_name` | `string` | Yes | Approver 1 Name value |
| `approver_1_role` | `string` | Yes | Approver 1 Role value |
| `auth_notes` | `string` | Yes | Auth Notes value |
| `cicd_notes` | `string` | Yes | Cicd Notes value |
| `code_organization_notes` | `string` | Yes | Code Organization Notes value |
| `component_architecture_notes` | `string` | Yes | Component Architecture Notes value |
| `cost_notes` | `string` | Yes | Cost Notes value |
| `cost_risk_impact` | `string` | Yes | Cost Risk Impact value |
| `cost_risk_mitigation` | `string` | Yes | Cost Risk Mitigation value |
| `cost_risk_prob` | `string` | Yes | Cost Risk Prob value |
| `critical_action_1` | `string` | Yes | Critical Action 1 value |
| `critical_issue_1_category` | `string` | Yes | Critical Issue 1 Category value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_codebase_audit_report`

**Handoff: Codebase Audit Report**

Codebase Audit Report: Template for codebase audit report (from: researcher, to: sprint-planning, architecture-agent)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `accomplishment` | `string` | Yes | Accomplishment value |
| `adr_count` | `string` | Yes | Adr Count value |
| `api_endpoints_documented` | `string` | Yes | Api Endpoints Documented value |
| `api_style` | `string` | Yes | Api Style value |
| `api_test_count` | `string` | Yes | Api Test Count value |
| `architecture_pattern` | `string` | Yes | Architecture Pattern value |
| `audit_commands_used` | `string` | Yes | Audit Commands Used value |
| `audit_date` | `string` | Yes | Audit Date value |
| `audit_duration` | `string` | Yes | Audit Duration value |
| `auth_method` | `string` | Yes | Auth Method value |
| `avg_commits_per_month` | `string` | Yes | Avg Commits Per Month value |
| `avg_commits_per_week` | `string` | Yes | Avg Commits Per Week value |
| `avg_dependency_age` | `string` | Yes | Avg Dependency Age value |
| `avg_file_size` | `string` | Yes | Avg File Size value |
| `avg_function_size` | `string` | Yes | Avg Function Size value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_component_design`

**Handoff: Component/Feature Specification**

Component/Feature Specification: Template for component/feature specification (from: architecture-agent, to: web-developer, backend-engineer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `a11y_test` | `string` | Yes | A11Y Test value |
| `action_logic` | `string` | Yes | Action Logic value |
| `action_name` | `string` | Yes | Action Name value |
| `action_payload_type` | `string` | Yes | Action Payload Type value |
| `all_props_example` | `string` | Yes | All Props Example value |
| `api_method` | `string` | Yes | Api Method value |
| `api_params` | `string` | Yes | Api Params value |
| `api_test` | `string` | Yes | Api Test value |
| `api_validation_description` | `string` | Yes | Api Validation Description value |
| `aria_label` | `string` | Yes | Aria Label value |
| `aria_role` | `string` | Yes | Aria Role value |
| `author_name` | `string` | Yes | Author Name value |
| `background_color` | `string` | Yes | Background Color value |
| `border_color` | `string` | Yes | Border Color value |
| `button_label` | `string` | Yes | Button Label value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_dashboard_specification`

**Handoff: Dashboard Specification**

Dashboard Specification: Template for dashboard specification (from: backend-engineer, to: frontend-engineer, documentation-engineer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `aggregation_strategy` | `string` | Yes | Aggregation Strategy value |
| `author_name` | `string` | Yes | Author Name value |
| `body_font` | `string` | Yes | Body Font value |
| `body_size` | `string` | Yes | Body Size value |
| `caching_strategy` | `string` | Yes | Caching Strategy value |
| `categorical_scale` | `string` | Yes | Categorical Scale value |
| `company_colors` | `string` | Yes | Company Colors value |
| `creation_date` | `string` | Yes | Creation Date value |
| `criterion` | `string` | Yes | Criterion value |
| `cross_filter_behavior` | `string` | Yes | Cross Filter Behavior value |
| `custom_css` | `string` | Yes | Custom Css value |
| `dashboard_name` | `string` | Yes | Dashboard Name value |
| `dashboard_platform` | `string` | Yes | Dashboard Platform value |
| `dashboard_purpose` | `string` | Yes | Dashboard Purpose value |
| `data_refresh_target` | `string` | Yes | Data Refresh Target value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_database_schema_design`

**Handoff: Database Schema Design**

Database Schema Design: Template for database schema design (from: architecture-agent, to: web-developer, backend-engineer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_control_model` | `string` | Yes | Access Control Model value |
| `architecture_pattern` | `string` | Yes | Architecture Pattern value |
| `ascii_erd` | `string` | Yes | Ascii Erd value |
| `author_name` | `string` | Yes | Author Name value |
| `backup_frequency` | `string` | Yes | Backup Frequency value |
| `backup_location` | `string` | Yes | Backup Location value |
| `backup_retention` | `string` | Yes | Backup Retention value |
| `backup_tool` | `string` | Yes | Backup Tool value |
| `business_context` | `string` | Yes | Business Context value |
| `cache_layer` | `string` | Yes | Cache Layer value |
| `cache_ttl` | `string` | Yes | Cache Ttl value |
| `check` | `string` | Yes | Check value |
| `compression_algorithm` | `string` | Yes | Compression Algorithm value |
| `connection_pool_config` | `string` | Yes | Connection Pool Config value |
| `creation_date` | `string` | Yes | Creation Date value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_deployment_checklist`

**Handoff: Deployment Checklist**

Deployment Checklist: Template for deployment checklist (from: infrastructure-engineer, to: documentation-engineer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `app_label` | `string` | Yes | App Label value |
| `app_name` | `string` | Yes | App Name value |
| `artifact_bucket` | `string` | Yes | Artifact Bucket value |
| `artifact_name` | `string` | Yes | Artifact Name value |
| `backend_image_name` | `string` | Yes | Backend Image Name value |
| `backup_bucket` | `string` | Yes | Backup Bucket value |
| `bucket_name` | `string` | Yes | Bucket Name value |
| `build_command` | `string` | Yes | Build Command value |
| `cdn_distribution` | `string` | Yes | Cdn Distribution value |
| `cloud_region` | `string` | Yes | Cloud Region value |
| `custom_deploy_command` | `string` | Yes | Custom Deploy Command value |
| `custom_rollback_command` | `string` | Yes | Custom Rollback Command value |
| `custom_rollback_criteria` | `string` | Yes | Custom Rollback Criteria value |
| `dependency_install_command` | `string` | Yes | Dependency Install Command value |
| `deployer_name` | `string` | Yes | Deployer Name value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_diagram_handoff`

**Handoff: Diagram Handoff**

Diagram Handoff: Template for diagram handoff (from: diagram-engineer, to: documentation-engineer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `a11y_check` | `string` | Yes | A11Y Check value |
| `all_verified` | `string` | Yes | All Verified value |
| `body_text_size` | `string` | Yes | Body Text Size value |
| `content_check` | `string` | Yes | Content Check value |
| `deliverable` | `string` | Yes | Deliverable value |
| `dependency` | `string` | Yes | Dependency value |
| `desktop_app_version` | `string` | Yes | Desktop App Version value |
| `diagram_count` | `string` | Yes | Diagram Count value |
| `diagram_directory_structure` | `string` | Yes | Diagram Directory Structure value |
| `diagram_font` | `string` | Yes | Diagram Font value |
| `diagram_index_path` | `string` | Yes | Diagram Index Path value |
| `diagram_index_preview` | `string` | Yes | Diagram Index Preview value |
| `diagram_tool` | `string` | Yes | Diagram Tool value |
| `doc_check` | `string` | Yes | Doc Check value |
| `dpi` | `string` | Yes | Dpi value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_documentation_update`

**Handoff: Documentation Update Handoff**

Documentation Update Handoff: Template for documentation update handoff (from: documentation-engineer, to: git-committer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `achievement` | `string` | Yes | Achievement value |
| `additional_notes` | `string` | Yes | Additional Notes value |
| `archival_schedule` | `string` | Yes | Archival Schedule value |
| `archive_count` | `string` | Yes | Archive Count value |
| `archive_date` | `string` | Yes | Archive Date value |
| `archive_file_path` | `string` | Yes | Archive File Path value |
| `archive_format_example` | `string` | Yes | Archive Format Example value |
| `archive_location` | `string` | Yes | Archive Location value |
| `archive_structure_description` | `string` | Yes | Archive Structure Description value |
| `auto_archival_enabled` | `string` | Yes | Auto Archival Enabled value |
| `auto_check` | `string` | Yes | Auto Check value |
| `auto_update_metric` | `string` | Yes | Auto Update Metric value |
| `auto_update_sprint_completion` | `string` | Yes | Auto Update Sprint Completion value |
| `automation_enabled` | `string` | Yes | Automation Enabled value |
| `automation_status` | `string` | Yes | Automation Status value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_infrastructure_design`

**Handoff: Infrastructure Design Document**

Infrastructure Design Document: Template for infrastructure design document (from: architecture-agent, to: web-developer, backend-engineer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `alert` | `string` | Yes | Alert value |
| `architecture_diagram` | `string` | Yes | Architecture Diagram value |
| `audit_logging_configuration` | `string` | Yes | Audit Logging Configuration value |
| `author_name` | `string` | Yes | Author Name value |
| `aws_secrets_manager_config` | `string` | Yes | Aws Secrets Manager Config value |
| `azure_app_service_plan` | `string` | Yes | Azure App Service Plan value |
| `azure_functions_count` | `string` | Yes | Azure Functions Count value |
| `azure_functions_runtime` | `string` | Yes | Azure Functions Runtime value |
| `azure_key_vault_config` | `string` | Yes | Azure Key Vault Config value |
| `backup_storage_configuration` | `string` | Yes | Backup Storage Configuration value |
| `change_sets_policy` | `string` | Yes | Change Sets Policy value |
| `cost_tracking_strategy` | `string` | Yes | Cost Tracking Strategy value |
| `creation_date` | `string` | Yes | Creation Date value |
| `database_encryption` | `string` | Yes | Database Encryption value |
| `dev_backend_config` | `string` | Yes | Dev Backend Config value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_integration`

**Handoff: Integration Complete**

Integration Complete: Template for integration complete (from: web-developer, to: test-engineer, security-reviewer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `api_endpoint` | `string` | Yes | Api Endpoint value |
| `api_key_cost` | `string` | Yes | Api Key Cost value |
| `api_key_env_var` | `string` | Yes | Api Key Env Var value |
| `api_key_how_to_obtain` | `string` | Yes | Api Key How To Obtain value |
| `api_key_registration_url` | `string` | Yes | Api Key Registration Url value |
| `auth_method` | `string` | Yes | Auth Method value |
| `auth_required` | `string` | Yes | Auth Required value |
| `change_1_code_snippet` | `string` | Yes | Change 1 Code Snippet value |
| `change_1_description` | `string` | Yes | Change 1 Description value |
| `change_1_file` | `string` | Yes | Change 1 File value |
| `change_1_line` | `string` | Yes | Change 1 Line value |
| `change_1_title` | `string` | Yes | Change 1 Title value |
| `change_2_code_snippet` | `string` | Yes | Change 2 Code Snippet value |
| `change_2_description` | `string` | Yes | Change 2 Description value |
| `change_2_file` | `string` | Yes | Change 2 File value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_logging_audit_report`

**Handoff: Logging Audit Report**

Logging Audit Report: Template for logging audit report (from: observability-engineer, to: web-developer, documentation-engineer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `audit_date` | `string` | Yes | Audit Date value |
| `audit_result` | `string` | Yes | Audit Result value |
| `audit_status` | `string` | Yes | Audit Status value |
| `auditor_notes` | `string` | Yes | Auditor Notes value |
| `component_name` | `string` | Yes | Component Name value |
| `critical_issues_count` | `string` | Yes | Critical Issues Count value |
| `deployment_milestone` | `string` | Yes | Deployment Milestone value |
| `error_context_score` | `string` | Yes | Error Context Score value |
| `error_context_status` | `string` | Yes | Error Context Status value |
| `high_priority_issues_count` | `string` | Yes | High Priority Issues Count value |
| `last_updated_date` | `string` | Yes | Last Updated Date value |
| `log_accessibility_score` | `string` | Yes | Log Accessibility Score value |
| `log_accessibility_status` | `string` | Yes | Log Accessibility Status value |
| `logging_audit_checklist_path` | `string` | Yes | Logging Audit Checklist Path value |
| `logging_standards_path` | `string` | Yes | Logging Standards Path value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_ml_design`

**Handoff: ML Design Document**

ML Design Document: Template for ml design document (from: architecture-agent, to: web-developer, backend-engineer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `additional_hyperparameters` | `string` | Yes | Additional Hyperparameters value |
| `algorithm_selection_rationale` | `string` | Yes | Algorithm Selection Rationale value |
| `api_authentication` | `string` | Yes | Api Authentication value |
| `api_framework` | `string` | Yes | Api Framework value |
| `api_rate_limiting` | `string` | Yes | Api Rate Limiting value |
| `api_sla` | `string` | Yes | Api Sla value |
| `author_name` | `string` | Yes | Author Name value |
| `base_model` | `string` | Yes | Base Model value |
| `baseline_improvement_target` | `string` | Yes | Baseline Improvement Target value |
| `batch_size` | `string` | Yes | Batch Size value |
| `bias_detection_plan` | `string` | Yes | Bias Detection Plan value |
| `business_impact_description` | `string` | Yes | Business Impact Description value |
| `business_problem_description` | `string` | Yes | Business Problem Description value |
| `creation_date` | `string` | Yes | Creation Date value |
| `criterion` | `string` | Yes | Criterion value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_ml_evaluation_report`

**Handoff: ML Evaluation Report**

ML Evaluation Report: Template for ml evaluation report (from: ml-engineer, to: test-engineer, documentation-engineer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `accuracy_status` | `string` | Yes | Accuracy Status value |
| `accuracy_target` | `string` | Yes | Accuracy Target value |
| `accuracy_value` | `string` | Yes | Accuracy Value value |
| `algorithm_name` | `string` | Yes | Algorithm Name value |
| `api_endpoint` | `string` | Yes | Api Endpoint value |
| `artifacts_description` | `string` | Yes | Artifacts Description value |
| `auc_status` | `string` | Yes | Auc Status value |
| `auc_target` | `string` | Yes | Auc Target value |
| `auc_value` | `string` | Yes | Auc Value value |
| `author_name` | `string` | Yes | Author Name value |
| `baseline_accuracy` | `string` | Yes | Baseline Accuracy value |
| `baseline_auc` | `string` | Yes | Baseline Auc value |
| `baseline_comparison_conclusion` | `string` | Yes | Baseline Comparison Conclusion value |
| `baseline_f1` | `string` | Yes | Baseline F1 value |
| `baseline_fps` | `string` | Yes | Baseline Fps value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_performance_optimization_report`

**Handoff: Performance Optimization Report**

Performance Optimization Report: Template for performance optimization report (from: performance-engineer, to: web-developer, documentation-engineer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `analysis_date` | `string` | Yes | Analysis Date value |
| `annual_benefit` | `string` | Yes | Annual Benefit value |
| `annual_savings` | `string` | Yes | Annual Savings value |
| `api_calls_count` | `string` | Yes | Api Calls Count value |
| `api_endpoint` | `string` | Yes | Api Endpoint value |
| `api_load_time` | `string` | Yes | Api Load Time value |
| `api_requests_count` | `string` | Yes | Api Requests Count value |
| `apm_tool_url` | `string` | Yes | Apm Tool Url value |
| `author_name` | `string` | Yes | Author Name value |
| `backward_pass_duration` | `string` | Yes | Backward Pass Duration value |
| `backward_pass_percentage` | `string` | Yes | Backward Pass Percentage value |
| `backward_pass_status` | `string` | Yes | Backward Pass Status value |
| `batch_size` | `string` | Yes | Batch Size value |
| `batch_size_recommendation` | `string` | Yes | Batch Size Recommendation value |
| `benchmark_after_expected` | `string` | Yes | Benchmark After Expected value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_phase_plan`

**Handoff: Phase Plan:  -**

Phase Plan:  -: Template for phase plan:  - (from: sprint-planning, to: web-developer, test-engineer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `api_authentication_method` | `string` | Yes | Api Authentication Method value |
| `api_endpoints_list` | `string` | Yes | Api Endpoints List value |
| `api_endpoints_summary` | `string` | Yes | Api Endpoints Summary value |
| `api_rate_limiting` | `string` | Yes | Api Rate Limiting value |
| `api_versioning_strategy` | `string` | Yes | Api Versioning Strategy value |
| `assigned_workflow` | `string` | Yes | Assigned Workflow value |
| `components_list` | `string` | Yes | Components List value |
| `components_to_create` | `string` | Yes | Components To Create value |
| `consideration` | `string` | Yes | Consideration value |
| `coverage_tool` | `string` | Yes | Coverage Tool value |
| `criterion` | `string` | Yes | Criterion value |
| `daily_targets_description` | `string` | Yes | Daily Targets Description value |
| `deliverable` | `string` | Yes | Deliverable value |
| `deployment_scripts_list` | `string` | Yes | Deployment Scripts List value |
| `detail` | `string` | Yes | Detail value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_research_summary`

**Handoff: Research Summary**

Research Summary: Template for research summary (from: researcher, to: sprint-planning, web-developer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `api_key_env_var` | `string` | Yes | Api Key Env Var value |
| `architecture_diagram` | `string` | Yes | Architecture Diagram value |
| `artifact_id` | `string` | Yes | Artifact Id value |
| `auth_header_format` | `string` | Yes | Auth Header Format value |
| `auth_header_name` | `string` | Yes | Auth Header Name value |
| `auth_method` | `string` | Yes | Auth Method value |
| `base_url` | `string` | Yes | Base Url value |
| `basic_configuration_code` | `string` | Yes | Basic Configuration Code value |
| `compression_ratio` | `string` | Yes | Compression Ratio value |
| `con` | `string` | Yes | Con value |
| `difference` | `string` | Yes | Difference value |
| `endpoint` | `string` | Yes | Endpoint value |
| `error_handling_example_python` | `string` | Yes | Error Handling Example Python value |
| `error_handling_example_typescript` | `string` | Yes | Error Handling Example Typescript value |
| `fact` | `string` | Yes | Fact value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_security_implementation_report`

**Handoff: Security Implementation Report**

Security Implementation Report: Template for security implementation report (from: security-reviewer, to: web-developer, documentation-engineer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `achievement` | `string` | Yes | Achievement value |
| `approval_status` | `string` | Yes | Approval Status value |
| `auth_checklist_status` | `string` | Yes | Auth Checklist Status value |
| `auth_context_path` | `string` | Yes | Auth Context Path value |
| `auth_test_coverage` | `string` | Yes | Auth Test Coverage value |
| `authentication_test_evidence` | `string` | Yes | Authentication Test Evidence value |
| `authorization_test_evidence` | `string` | Yes | Authorization Test Evidence value |
| `authz_test_coverage` | `string` | Yes | Authz Test Coverage value |
| `cookie_settings` | `string` | Yes | Cookie Settings value |
| `cors_allow_credentials` | `string` | Yes | Cors Allow Credentials value |
| `cors_allowed_headers` | `string` | Yes | Cors Allowed Headers value |
| `cors_allowed_methods` | `string` | Yes | Cors Allowed Methods value |
| `cors_configuration_code` | `string` | Yes | Cors Configuration Code value |
| `critical_issues_fixed` | `string` | Yes | Critical Issues Fixed value |
| `critical_issues_found` | `string` | Yes | Critical Issues Found value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_security_report`

**Handoff: Security Review**

Security Review: Template for security review (from: security-reviewer, to: web-developer, documentation-engineer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `api_mocking_status` | `string` | Yes | Api Mocking Status value |
| `approval_decision` | `string` | Yes | Approval Decision value |
| `approval_summary` | `string` | Yes | Approval Summary value |
| `areas_for_improvement` | `string` | Yes | Areas For Improvement value |
| `auth_findings` | `string` | Yes | Auth Findings value |
| `auth_recommendations` | `string` | Yes | Auth Recommendations value |
| `auth_status` | `string` | Yes | Auth Status value |
| `component_name` | `string` | Yes | Component Name value |
| `conditional_approval_summary` | `string` | Yes | Conditional Approval Summary value |
| `critical_count` | `string` | Yes | Critical Count value |
| `critical_issues_list` | `string` | Yes | Critical Issues List value |
| `critical_issues_section` | `string` | Yes | Critical Issues Section value |
| `cve_check_output` | `string` | Yes | Cve Check Output value |
| `database_security_findings` | `string` | Yes | Database Security Findings value |
| `database_security_recommendations` | `string` | Yes | Database Security Recommendations value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_sprint_plan`

**Handoff: Sprint Plan**

Sprint Plan: Template for sprint plan (from: sprint-planning, to: web-developer, test-engineer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `api_availability_measurement` | `string` | Yes | Api Availability Measurement value |
| `api_availability_target` | `string` | Yes | Api Availability Target value |
| `api_deployment_timeline` | `string` | Yes | Api Deployment Timeline value |
| `api_design_timeline` | `string` | Yes | Api Design Timeline value |
| `api_documentation_timeline` | `string` | Yes | Api Documentation Timeline value |
| `api_error_rate_measurement` | `string` | Yes | Api Error Rate Measurement value |
| `api_error_rate_target` | `string` | Yes | Api Error Rate Target value |
| `api_implementation_timeline` | `string` | Yes | Api Implementation Timeline value |
| `api_response_time_measurement` | `string` | Yes | Api Response Time Measurement value |
| `api_response_time_target` | `string` | Yes | Api Response Time Target value |
| `api_security_timeline` | `string` | Yes | Api Security Timeline value |
| `api_testing_timeline` | `string` | Yes | Api Testing Timeline value |
| `api_throughput_measurement` | `string` | Yes | Api Throughput Measurement value |
| `api_throughput_target` | `string` | Yes | Api Throughput Target value |
| `architecture_design_path` | `string` | Yes | Architecture Design Path value |

*Source: `vibey/mcp/discovery/`*

---

#### `vibey_handoff_test_report`

**Handoff: Test Report**

Test Report: Template for test report (from: test-engineer, to: web-developer, security-reviewer)

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `api_mocking_strategy` | `string` | Yes | Api Mocking Strategy value |
| `boundary_condition_tests` | `string` | Yes | Boundary Condition Tests value |
| `branch_coverage` | `string` | Yes | Branch Coverage value |
| `browser_compatibility_tests` | `string` | Yes | Browser Compatibility Tests value |
| `ci_test_command` | `string` | Yes | Ci Test Command value |
| `class_name` | `string` | Yes | Class Name value |
| `coverage_report_output` | `string` | Yes | Coverage Report Output value |
| `coverage_reporting_method` | `string` | Yes | Coverage Reporting Method value |
| `coverage_status` | `string` | Yes | Coverage Status value |
| `data_loading_mocking_strategy` | `string` | Yes | Data Loading Mocking Strategy value |
| `data_source_mocking_strategy` | `string` | Yes | Data Source Mocking Strategy value |
| `database_mocking_strategy` | `string` | Yes | Database Mocking Strategy value |
| `e2e_tests_count` | `string` | Yes | E2E Tests Count value |
| `e2e_tests_status` | `string` | Yes | E2E Tests Status value |
| `error_scenario_tests` | `string` | Yes | Error Scenario Tests value |

*Source: `vibey/mcp/discovery/`*

---

## Resources

MCP resources provide access to Vibey framework content via URI patterns. Resources support both direct access and template-based discovery.

### Handoffs Resources

Handoff resources provide access to handoff templates and variable schemas.

| URI Template | Name | MIME Type |
|--------------|------|-----------|
| `vibey://handoffs/{handoff_id}` | Handoff Template | `text/markdown+jinja2` |
| `vibey://handoffs/{handoff_id}/variables` | Handoff Variables | `application/json` |
| `vibey://handoffs/{handoff_id}/metadata` | Handoff Metadata | `application/json` |
| `vibey://handoffs/{handoff_id}/rendered` | Rendered Handoff | `text/markdown` |

#### `vibey://handoffs/{handoff_id}`

**Handoff Template**

Full handoff template with Jinja2 content

- **MIME Type:** `text/markdown+jinja2`
- **Provider:** `HandoffResourceProvider`

**Example:**

```
GET vibey://handoffs/diagram-handoff
```

#### `vibey://handoffs/{handoff_id}/variables`

**Handoff Variables**

Variable schema for the handoff template (JSON Schema)

- **MIME Type:** `application/json`
- **Provider:** `HandoffResourceProvider`

**Example:**

```
GET vibey://handoffs/diagram-handoff/variables
```

#### `vibey://handoffs/{handoff_id}/metadata`

**Handoff Metadata**

Handoff template metadata (agents, purpose)

- **MIME Type:** `application/json`
- **Provider:** `HandoffResourceProvider`

**Example:**

```
GET vibey://handoffs/diagram-handoff/metadata
```

#### `vibey://handoffs/{handoff_id}/rendered`

**Rendered Handoff**

Handoff template rendered with sample data

- **MIME Type:** `text/markdown`
- **Provider:** `HandoffResourceProvider`

**Example:**

```
GET vibey://handoffs/diagram-handoff/rendered
```

### Workflows Resources

Workflow resources provide access to workflow definitions, steps, and metadata.

| URI Template | Name | MIME Type |
|--------------|------|-----------|
| `vibey://workflows/{workflow_id}` | Workflow Definition | `text/markdown` |
| `vibey://workflows/{workflow_id}/steps` | Workflow Steps | `application/json` |
| `vibey://workflows/{workflow_id}/metadata` | Workflow Metadata | `application/json` |
| `vibey://workflows/{workflow_id}/quality-gates` | Workflow Quality Gates | `application/json` |

#### `vibey://workflows/{workflow_id}`

**Workflow Definition**

Full workflow definition with steps and gates

- **MIME Type:** `text/markdown`
- **Provider:** `WorkflowResourceProvider`

**Example:**

```
GET vibey://workflows/sprint-planning
```

#### `vibey://workflows/{workflow_id}/steps`

**Workflow Steps**

Workflow steps as structured JSON

- **MIME Type:** `application/json`
- **Provider:** `WorkflowResourceProvider`

**Example:**

```
GET vibey://workflows/sprint-planning/steps
```

#### `vibey://workflows/{workflow_id}/metadata`

**Workflow Metadata**

Workflow frontmatter metadata

- **MIME Type:** `application/json`
- **Provider:** `WorkflowResourceProvider`

**Example:**

```
GET vibey://workflows/sprint-planning/metadata
```

#### `vibey://workflows/{workflow_id}/quality-gates`

**Workflow Quality Gates**

Quality gates defined in this workflow

- **MIME Type:** `application/json`
- **Provider:** `WorkflowResourceProvider`

**Example:**

```
GET vibey://workflows/sprint-planning/quality-gates
```

## Prompts

MCP prompts provide structured prompt templates for common tasks. Each prompt accepts arguments to customize the generated instructions.

| Prompt | Description | Required Args |
|--------|-------------|---------------|
| `vibey_quality_gate_check` | Run a comprehensive quality gate check on code or documentat... | `gate_type` |
| `vibey_security_scan` | Quick security vulnerability scan | `target` |
| `vibey_test_coverage` | Analyze test coverage and suggest improvements | `target` |
| `vibey_doc_check` | Check documentation completeness | `target` |

### `vibey_quality_gate_check`

Run a comprehensive quality gate check on code or documentation

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `gate_type` | Yes | Type of gate: security, testing, logging, documentation, performance, or all |
| `threshold` | No | Pass threshold percentage (default: 80) |
| `file_path` | No | Specific file or directory to check |
| `severity` | No | Minimum severity to report: critical, high, medium, low |

*Provider: `QualityGatePromptProvider`*

---

### `vibey_security_scan`

Quick security vulnerability scan

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `target` | Yes | File, directory, or 'all' to scan |
| `focus` | No | Focus area: injection, auth, secrets, dependencies, or all |

*Provider: `QualityGatePromptProvider`*

---

### `vibey_test_coverage`

Analyze test coverage and suggest improvements

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `target` | Yes | Module or file to analyze |
| `coverage_type` | No | Coverage type: line, branch, function, or all |

*Provider: `QualityGatePromptProvider`*

---

### `vibey_doc_check`

Check documentation completeness

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `target` | Yes | File or module to check |
| `doc_type` | No | Documentation type: docstrings, readme, api, or all |

*Provider: `QualityGatePromptProvider`*

---

## About This Document

This reference was auto-generated from the Vibey MCP server implementation. It cannot drift from the actual implementation because it is generated directly from the source code.

To regenerate this document:

```bash
vibey docs generate-mcp
```

To check for drift:

```bash
vibey docs check-mcp-drift
```
