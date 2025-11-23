# Frontmatter Schema Reference

> **Version:** 1.0.0
> **Last Updated:** 2025-11-22

This document defines the YAML frontmatter schema for Vibey assets (agents, workflows, handoffs). The MCP server dynamically discovers and generates tools from this frontmatter.

## Overview

All Vibey assets use YAML frontmatter at the beginning of markdown files:

```markdown
---
id: asset-id
name: Asset Name
type: asset-type
version: "1.0.0"
# ... additional fields
---

# Asset Content

Instructions, steps, or template content here.
```

## Agent Schema

Agents are specialized AI assistants with specific expertise.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (kebab-case, e.g., `test-engineer`) |
| `name` | string | Human-readable name |
| `type` | enum | Agent category (see Agent Types) |
| `version` | string | Semantic version (e.g., `"1.0.0"`) |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `description` | string | `""` | Brief description of agent's purpose |
| `triggers` | object | `{}` | Trigger patterns for orchestration |
| `inputs` | array | `[]` | Input parameters the agent accepts |
| `outputs` | array | `[]` | Output fields the agent produces |
| `aliases` | array | `[]` | Alternative names for the agent |

### Agent Types

| Type | Description | Examples |
|------|-------------|----------|
| `core` | Framework orchestration | coordinator, vibey-manager |
| `planning` | Sprint and project planning | sprint-planning, researcher |
| `development` | Code implementation | web-developer, backend-engineer |
| `quality` | Testing and review | test-engineer, security-reviewer |
| `documentation` | Documentation writing | docs-writer, diagram-engineer |
| `architecture` | System design | architecture-agent |

### Triggers Object

```yaml
triggers:
  keywords:           # Words/phrases that activate this agent
    - "write tests"
    - "pytest"
    - "coverage"
  contexts:           # Situations where agent is relevant
    - "testing requirements"
    - "quality assurance"
  file_patterns:      # File patterns that suggest this agent
    - "tests/*"
    - "test_*.py"
  priority: high      # Trigger priority: high, medium, low
```

### Inputs Array

```yaml
inputs:
  - name: code_to_test      # Parameter name
    type: string            # Type: string, number, boolean, array, object
    required: true          # Whether parameter is required
    description: "Code to write tests for"
  - name: coverage_target
    type: number
    required: false
    default: 80             # Default value if not provided
```

### Complete Agent Example

```yaml
---
id: test-engineer
name: Test Engineer
type: quality
version: "2.0.0"
description: Write comprehensive automated tests for code quality assurance
triggers:
  keywords:
    - write tests
    - add tests
    - test coverage
    - unit test
    - integration test
    - pytest
  contexts:
    - testing requirements
    - quality assurance
    - CI/CD setup
  file_patterns:
    - tests/*
    - test_*.py
    - __tests__/*
  priority: high
inputs:
  - name: code_to_test
    type: string
    required: true
    description: The code or module to write tests for
  - name: coverage_target
    type: number
    required: false
    default: 80
    description: Target test coverage percentage
  - name: test_framework
    type: string
    required: false
    description: Preferred test framework (pytest, jest, etc.)
outputs:
  - name: test_files
    type: array
    description: List of generated test files
  - name: coverage_report
    type: object
    description: Coverage metrics
aliases:
  - tester
  - qa-engineer
---

# Test Engineer

You are an expert Test Engineer...
```

## Workflow Schema

Workflows define multi-step processes with agent assignments.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (kebab-case) |
| `name` | string | Human-readable name |
| `type` | enum | Workflow category (see Workflow Types) |
| `version` | string | Semantic version |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `description` | string | `""` | Brief description |
| `duration` | string | `""` | Estimated duration (e.g., "2-4 hours") |
| `complexity` | enum | `"medium"` | low, medium, high |
| `steps` | array | `[]` | Workflow steps |
| `quality_gates` | array | `[]` | Quality checkpoints |
| `inputs` | array | `[]` | Workflow inputs |
| `project_types` | array | `[]` | Applicable project types |

### Workflow Types

| Type | Description |
|------|-------------|
| `development` | Feature development workflows |
| `planning` | Sprint and project planning |
| `quality` | Testing and security audits |
| `documentation` | Documentation workflows |
| `deployment` | CI/CD and deployment |
| `infrastructure` | Infrastructure setup |

### Steps Array

```yaml
steps:
  - order: 1
    name: Planning
    agent: sprint-planner       # Agent ID to handle this step
    duration: "1-2 hours"
    description: Create implementation plan
    inputs:
      - requirements
    outputs:
      - implementation_plan
  - order: 2
    name: Implementation
    agent: web-developer
    duration: "4-8 hours"
    description: Implement the feature
```

### Quality Gates Array

```yaml
quality_gates:
  - name: test_coverage
    type: percentage
    threshold: 80
    blocking: true            # Blocks progression if not met
  - name: security_scan
    type: pass_fail
    threshold: 1              # 1 = pass required
    blocking: true
```

### Complete Workflow Example

```yaml
---
id: feature-development
name: Feature Development Workflow
type: development
version: "1.0.0"
description: Complete feature from planning to deployment
duration: "1-3 days"
complexity: medium
steps:
  - order: 1
    name: Requirements Analysis
    agent: researcher
    duration: "1-2 hours"
    description: Analyze and clarify requirements
  - order: 2
    name: Technical Design
    agent: architecture-agent
    duration: "2-4 hours"
    description: Create technical design document
  - order: 3
    name: Implementation
    agent: web-developer
    duration: "4-8 hours"
    description: Implement the feature
  - order: 4
    name: Testing
    agent: test-engineer
    duration: "2-4 hours"
    description: Write and run tests
  - order: 5
    name: Security Review
    agent: security-reviewer
    duration: "1-2 hours"
    description: Security audit
  - order: 6
    name: Documentation
    agent: documentation-engineer
    duration: "1-2 hours"
    description: Update documentation
quality_gates:
  - name: test_coverage
    type: percentage
    threshold: 80
    blocking: true
  - name: security_scan
    type: pass_fail
    threshold: 1
    blocking: true
  - name: documentation
    type: pass_fail
    threshold: 1
    blocking: false
inputs:
  - name: feature_name
    type: string
    required: true
    description: Name of the feature to implement
  - name: requirements
    type: string
    required: true
    description: Feature requirements and acceptance criteria
  - name: project_type
    type: string
    required: false
    default: web-app
    description: Project type for context
project_types:
  - web-app
  - api
  - ml
---

# Feature Development Workflow

This workflow guides the complete development...
```

## Handoff Schema

Handoffs define structured data passed between agents.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `name` | string | Human-readable name |
| `version` | string | Semantic version |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `description` | string | `""` | Brief description |
| `from_agent` | string | `null` | Source agent ID |
| `to_agent` | string | `null` | Destination agent ID |
| `fields` | array | `[]` | Data fields in handoff |

### Fields Array

```yaml
fields:
  - name: summary
    type: string
    required: true
    description: Brief summary of work completed
  - name: files_modified
    type: array
    required: true
    description: List of files that were modified
  - name: test_results
    type: object
    required: false
    description: Test execution results
```

### Complete Handoff Example

```yaml
---
id: implementation-to-testing
name: Implementation to Testing Handoff
version: "1.0.0"
description: Handoff from developer to test engineer
from_agent: web-developer
to_agent: test-engineer
fields:
  - name: feature_summary
    type: string
    required: true
    description: Summary of implemented feature
  - name: files_created
    type: array
    required: true
    description: New files created
  - name: files_modified
    type: array
    required: true
    description: Existing files modified
  - name: api_changes
    type: object
    required: false
    description: API endpoint changes
  - name: testing_notes
    type: string
    required: false
    description: Notes for test engineer
---

# Implementation to Testing Handoff

## Feature Summary
{{ feature_summary }}

## Files Created
{% for file in files_created %}
- {{ file }}
{% endfor %}
...
```

## MCP Tool Generation

The MCP server converts frontmatter to tools automatically:

### Agent → Tool Mapping

| Frontmatter | MCP Tool Field |
|-------------|----------------|
| `id` | `name` (with `vibey_` prefix, underscores) |
| `name` | Used in `description` |
| `description` | `description` |
| `inputs` | `inputSchema.properties` |
| `inputs[].required` | `inputSchema.required` |

**Example:**
```yaml
# Agent frontmatter
id: test-engineer
name: Test Engineer
description: Write tests
inputs:
  - name: code
    type: string
    required: true
```

Becomes:
```json
{
  "name": "vibey_test_engineer",
  "description": "Test Engineer - Write tests",
  "inputSchema": {
    "type": "object",
    "properties": {
      "code": {"type": "string"}
    },
    "required": ["code"]
  }
}
```

### Workflow → Tool Mapping

Workflows get the `vibey_workflow_` prefix:

```yaml
id: feature-development
```

Becomes: `vibey_workflow_feature_development`

## Validation

### Schema Validation Rules

1. **Required fields must be present** - `id`, `name`, `type`, `version`
2. **IDs must be kebab-case** - `my-agent` not `myAgent` or `my_agent`
3. **Version must be semver** - `"1.0.0"` not `1.0` or `"v1"`
4. **Types must be valid** - From predefined enums
5. **Input types must be JSON Schema types** - string, number, boolean, array, object

### Validation Command

```bash
# Validate all frontmatter
python -m vibey.cli.main validate-frontmatter

# Validate specific file
python -m vibey.cli.main validate-frontmatter framework/agents/test-engineer.md
```

## File Locations

| Asset Type | Directory | Pattern |
|------------|-----------|---------|
| Agents | `framework/agents/` | `*.md` |
| Workflows | `framework/workflows/` | `*.md`, `**/*.md` |
| Handoffs | `templates/handoffs/` | `*.md` |

## Best Practices

1. **Use descriptive IDs** - `test-engineer` not `te` or `agent1`
2. **Include triggers** - Help orchestration route requests
3. **Document inputs/outputs** - Clear parameter descriptions
4. **Set appropriate types** - Match agent expertise to type enum
5. **Version your changes** - Bump version on significant changes
6. **Add aliases** - Common alternative names for discoverability

## Migration from Legacy Format

If you have agents without frontmatter:

1. Add `---` delimiters at file start
2. Add required fields (`id`, `name`, `type`, `version`)
3. Extract triggers from prose into structured format
4. Define inputs based on what agent expects
5. Run validation to check schema compliance

See [Migration Guide](../guides/MIGRATION_CLAUDE_TO_GOOSE.md) for detailed steps.
