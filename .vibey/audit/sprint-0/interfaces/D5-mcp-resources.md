# D5: MCP Resources/Prompts Audit

**Task ID:** 01KFXK0SXXW5EMWV03EM3A1MTA
**Phase:** D5: Interfaces
**Date:** 2026-01-29

## Executive Summary

The Vibey MCP server exposes 8 resources via URI templates and 4 prompts for AI assistant integration. Resources provide content access (handoff templates, workflow definitions) while prompts provide structured instructions for quality gate checks. Key finding: Resources support remote mode via URI delegation - local URIs resolve to local files, remote URIs resolve to Delta Lake queries with caching.

**Key Statistics:**
- 8 MCP resources across 2 providers
- 4 MCP prompts via QualityGatePromptProvider
- 2 resource providers (HandoffResourceProvider, WorkflowResourceProvider)
- 4 URI variants per resource type

## Resource Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      MCP RESOURCE ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────────────┘

  MCP CLIENT                           VIBEY MCP SERVER
  (Claude/Cursor)                      (vibey-roadmap)
  ─────────────                        ────────────────

┌─────────────────┐                 ┌─────────────────┐
│ resources/read  │────── URI ─────▶│ ResourceRouter  │
│ {uri: "..."}    │                 │                 │
└─────────────────┘                 └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ Provider Match  │
                                    │                 │
                                    ├─────────────────┤
                                    │ vibey://handoffs │──▶ HandoffResourceProvider
                                    │ vibey://workflows│──▶ WorkflowResourceProvider
                                    └─────────────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ Content Source  │
                                    │                 │
                                    ├─────────────────┤
                                    │ .vibey/handoffs/│  Jinja2 templates
                                    │ .vibey/workflows│  Markdown + YAML
                                    └─────────────────┘
```

## Resources Inventory Table

| URI Template | Name | MIME Type | Provider |
|--------------|------|-----------|----------|
| `vibey://handoffs/{handoff_id}` | Handoff Template | `text/markdown+jinja2` | HandoffResourceProvider |
| `vibey://handoffs/{handoff_id}/variables` | Handoff Variables | `application/json` | HandoffResourceProvider |
| `vibey://handoffs/{handoff_id}/metadata` | Handoff Metadata | `application/json` | HandoffResourceProvider |
| `vibey://handoffs/{handoff_id}/rendered` | Rendered Handoff | `text/markdown` | HandoffResourceProvider |
| `vibey://workflows/{workflow_id}` | Workflow Definition | `text/markdown` | WorkflowResourceProvider |
| `vibey://workflows/{workflow_id}/steps` | Workflow Steps | `application/json` | WorkflowResourceProvider |
| `vibey://workflows/{workflow_id}/metadata` | Workflow Metadata | `application/json` | WorkflowResourceProvider |
| `vibey://workflows/{workflow_id}/quality-gates` | Workflow Quality Gates | `application/json` | WorkflowResourceProvider |

## Handoff Resources Detail

### Resource Types

| Variant | Purpose | Content |
|---------|---------|---------|
| `/{handoff_id}` | Full template | Jinja2 template with placeholders |
| `/{handoff_id}/variables` | Variable schema | JSON Schema for template variables |
| `/{handoff_id}/metadata` | Template metadata | From/to agents, purpose, tags |
| `/{handoff_id}/rendered` | Sample output | Template rendered with example data |

### Available Handoff Templates (22)

| Handoff ID | From Agent | To Agent(s) | Purpose |
|------------|------------|-------------|---------|
| `api-spec` | backend-engineer | frontend-engineer, documentation-engineer | API specification |
| `application-requirements` | web-developer | test-engineer, documentation-engineer | Application requirements |
| `architecture-review` | architecture-agent | web-developer, backend-engineer | Architecture review report |
| `codebase-audit-report` | researcher | sprint-planning, architecture-agent | Codebase audit report |
| `component-design` | architecture-agent | web-developer, backend-engineer | Component specification |
| `dashboard-specification` | backend-engineer | frontend-engineer, documentation-engineer | Dashboard specification |
| `database-schema-design` | architecture-agent | web-developer, backend-engineer | Database schema design |
| `deployment-checklist` | infrastructure-engineer | documentation-engineer | Deployment checklist |
| `diagram-handoff` | diagram-engineer | documentation-engineer | Diagram handoff |
| `documentation-update` | documentation-engineer | git-committer | Documentation update |
| `infrastructure-design` | architecture-agent | web-developer, backend-engineer | Infrastructure design |
| `integration` | web-developer | test-engineer | Integration complete |
| `logging-audit-report` | observability-engineer | backend-engineer | Logging audit report |
| `ml-design` | architecture-agent | ml-engineer | ML design document |
| `ml-evaluation-report` | ml-engineer | architecture-agent | ML evaluation report |
| `performance-optimization-report` | performance-engineer | web-developer | Performance report |
| `phase-plan` | sprint-planning | web-developer | Phase plan |
| `research-summary` | researcher | sprint-planning | Research summary |
| `security-implementation-report` | security-engineer | documentation-engineer | Security implementation |
| `security-report` | security-reviewer | web-developer | Security review |
| `sprint-plan` | sprint-planning | web-developer | Sprint plan |
| `test-report` | test-engineer | web-developer | Test report |

## Workflow Resources Detail

### Resource Types

| Variant | Purpose | Content |
|---------|---------|---------|
| `/{workflow_id}` | Full definition | Markdown with steps and gates |
| `/{workflow_id}/steps` | Step list | JSON array of workflow steps |
| `/{workflow_id}/metadata` | Workflow metadata | Duration, complexity, agents involved |
| `/{workflow_id}/quality-gates` | Quality gates | Gates defined in the workflow |

### Available Workflows (16)

| Workflow ID | Steps | Duration | Description |
|-------------|-------|----------|-------------|
| `sprint-planning` | 9 | 3-5 days | Sprint planning and roadmap management |
| `single-feature-development` | 7 | 1-3 days | Complete feature from spec to deployment |
| `weekly-sprint` | 1 | 3-5 days | Parallel feature development |
| `bug-triage` | 5 | 1-2 hours | Bug investigation and fix |
| `code-review` | 4 | 30-60 min | Pull request review |
| `deployment` | 6 | 1-2 hours | Production deployment |
| `documentation` | 4 | 2-4 hours | Documentation update |
| `hotfix` | 5 | 1-4 hours | Emergency fix |
| `infrastructure` | 7 | 1-2 days | Infrastructure change |
| `ml-experiment` | 8 | 1-2 weeks | ML experiment cycle |
| `onboarding` | 5 | 1-2 days | New developer onboarding |
| `performance` | 6 | 2-5 days | Performance optimization |
| `refactoring` | 6 | 1-3 days | Code refactoring |
| `security-audit` | 7 | 2-5 days | Security audit |
| `test-improvement` | 5 | 1-2 days | Test coverage improvement |
| `api-development` | 7 | 2-4 days | API endpoint development |

## Prompts Inventory Table

| Prompt | Provider | Required Args | Optional Args |
|--------|----------|---------------|---------------|
| `vibey_quality_gate_check` | QualityGatePromptProvider | `gate_type` | `threshold`, `file_path`, `severity` |
| `vibey_security_scan` | QualityGatePromptProvider | `target` | `focus` |
| `vibey_test_coverage` | QualityGatePromptProvider | `target` | `coverage_type` |
| `vibey_doc_check` | QualityGatePromptProvider | `target` | `doc_type` |

## Prompts Detail

### vibey_quality_gate_check

| Parameter | Type | Required | Values |
|-----------|------|----------|--------|
| `gate_type` | string | Yes | security, testing, logging, documentation, performance, all |
| `threshold` | integer | No | 0-100 (default: 80) |
| `file_path` | string | No | File or directory path |
| `severity` | string | No | critical, high, medium, low |

**Output:** Structured instructions for running quality gate analysis.

### vibey_security_scan

| Parameter | Type | Required | Values |
|-----------|------|----------|--------|
| `target` | string | Yes | File path, directory, or "all" |
| `focus` | string | No | injection, auth, secrets, dependencies, all |

**Output:** Security scan instructions focused on specified area.

### vibey_test_coverage

| Parameter | Type | Required | Values |
|-----------|------|----------|--------|
| `target` | string | Yes | Module or file path |
| `coverage_type` | string | No | line, branch, function, all |

**Output:** Test coverage analysis instructions.

### vibey_doc_check

| Parameter | Type | Required | Values |
|-----------|------|----------|--------|
| `target` | string | Yes | File or module path |
| `doc_type` | string | No | docstrings, readme, api, all |

**Output:** Documentation completeness check instructions.

## Resource Content Sources

| Resource Type | Local Source | Content Format |
|---------------|--------------|----------------|
| Handoff templates | `.vibey/handoffs/{id}.md.j2` | Jinja2 template |
| Handoff variables | `.vibey/handoffs/{id}.json` | JSON Schema |
| Workflow definitions | `.vibey/workflows/{id}.md` | Markdown + YAML frontmatter |
| Workflow steps | `.vibey/workflows/{id}.md` | Extracted from ## Steps section |

## Remote Mode Translation Table

| Local Concept | Remote Equivalent | Transformation |
|---------------|-------------------|----------------|
| `vibey://handoffs/{id}` | `vibey://remote/handoffs/{id}` | Route to Delta Lake |
| Local file read | Delta Lake query | StorageProtocol abstraction |
| Jinja2 template | Stored template | Same format, different storage |
| JSON Schema | Stored schema | Same format, different storage |
| Markdown workflow | Stored workflow | Same format, different storage |
| Resource caching | TTL-based cache | Add cache layer |
| Provider lookup | Provider registry | Same routing logic |

## Remote Resource Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REMOTE RESOURCE ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────────┘

  MCP CLIENT                           REMOTE MODE
  ─────────────                        ───────────

┌─────────────────┐                 ┌─────────────────┐
│ resources/read  │────── URI ─────▶│ ResourceRouter  │
│ {uri: "..."}    │                 │                 │
└─────────────────┘                 └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ Mode Check      │
                                    │ (--remote flag) │
                                    └────────┬────────┘
                                             │
                         ┌───────────────────┼───────────────────┐
                         │                   │                   │
                    LOCAL MODE          REMOTE MODE         HYBRID MODE
                         │                   │                   │
                    ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
                    │ Local   │         │ Delta   │         │ Cache + │
                    │ Files   │         │ Lake    │         │ Remote  │
                    └─────────┘         └─────────┘         └─────────┘
```

## Resource Caching Strategy

| Resource Type | Cache Strategy | TTL | Invalidation |
|---------------|----------------|-----|--------------|
| Handoff templates | Static cache | 24h | On template update |
| Handoff variables | Static cache | 24h | On schema change |
| Workflow definitions | Static cache | 24h | On workflow update |
| Quality gates | Dynamic cache | 1h | On gate evaluation |
| Rendered content | Per-request | None | Always fresh |

## Provider Implementation Pattern

```python
class ResourceProvider(Protocol):
    """MCP Resource Provider interface."""

    def get_uri_patterns(self) -> List[str]:
        """Return URI patterns this provider handles."""
        ...

    def list_resources(self) -> List[Resource]:
        """List all available resources."""
        ...

    def read_resource(self, uri: str) -> ReadResourceResult:
        """Read a specific resource by URI."""
        ...
```

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] Resources inventory with 8 resources: PASS
- [x] Prompts inventory with 4 prompts: PASS
- [x] Resource URI patterns documented: PASS
- [x] Provider implementations identified: PASS
- [x] Remote mode translation documented: PASS

## References

- `docs/reference/MCP_REFERENCE.md:1953-2187` - Resources and Prompts sections
- `vibey/mcp/discovery/` - Resource provider implementations
- `docs/architecture/adr/0005-mcp-integration.md` - MCP integration ADR
