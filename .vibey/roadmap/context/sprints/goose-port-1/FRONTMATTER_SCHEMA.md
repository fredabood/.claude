# Vibey Frontmatter Schema Specification

**Version:** 1.0.0
**Created:** 2025-11-22
**Purpose:** Define YAML frontmatter structure for dynamic MCP tool discovery

---

## Overview

All Vibey assets (agents, workflows, handoffs) include YAML frontmatter that the MCP server parses to dynamically generate tools. This ensures:

1. **Single source of truth** - Markdown file is authoritative
2. **Zero drift** - MCP tools always match definitions
3. **Human + machine readable** - Frontmatter for MCP, body for humans

---

## Agent Frontmatter Schema

```yaml
---
# Required fields
id: string                    # Unique identifier (e.g., "test-engineer")
name: string                  # Display name (e.g., "Test Engineer")
type: enum                    # Category: core|planning|development|quality|documentation|architecture
version: string               # Schema version (e.g., "1.0.0")

# Trigger patterns (for orchestration)
triggers:
  keywords: string[]          # Words that invoke this agent
  contexts: string[]          # Situational triggers
  file_patterns: string[]     # File glob patterns
  priority: enum              # high|medium|low

# MCP tool inputs
inputs:
  - name: string              # Parameter name
    type: enum                # string|integer|boolean|array|object
    required: boolean         # Is this required?
    default: any              # Default value (if optional)
    description: string       # Help text for MCP clients

# MCP tool outputs
outputs:
  - name: string              # Output field name
    type: enum                # string|integer|boolean|array|object
    description: string       # What this output contains

# Optional metadata
aliases: string[]             # Alternative names (e.g., ["security-auditor"])
description: string           # Brief description for MCP tool listing
---
```

### Agent Example

```yaml
---
id: test-engineer
name: Test Engineer
type: quality
version: "1.0.0"

triggers:
  keywords:
    - write tests
    - unit test
    - integration test
    - pytest
    - jest
    - coverage
    - test suite
  contexts:
    - testing requirements
    - quality assurance
    - CI/CD setup
  file_patterns:
    - tests/*
    - test_*.py
    - "*.test.js"
    - "*.spec.ts"
  priority: high

inputs:
  - name: code_to_test
    type: string
    required: true
    description: Code module or file path to write tests for
  - name: test_framework
    type: string
    required: false
    default: auto
    description: Testing framework (pytest, jest, etc.) - auto-detected if not specified
  - name: coverage_target
    type: integer
    required: false
    default: 90
    description: Target test coverage percentage

outputs:
  - name: test_files
    type: array
    description: List of test files created
  - name: coverage_report
    type: string
    description: Coverage summary
  - name: test_results
    type: object
    description: Pass/fail counts and details

description: Write comprehensive automated tests for code quality assurance
---

# Test Engineer

**Role:** Write comprehensive automated tests...
[rest of markdown body]
```

---

## Workflow Frontmatter Schema

```yaml
---
# Required fields
id: string                    # Unique identifier (e.g., "single-feature-development")
name: string                  # Display name
type: enum                    # planning|development|quality|documentation|deployment
version: string               # Schema version

# Workflow metadata
duration: string              # Estimated duration (e.g., "1-3 days")
complexity: enum              # low|medium|high

# Steps define the workflow sequence
steps:
  - order: integer            # Step number (1, 2, 3...)
    name: string              # Step name
    agent: string             # Agent ID to use for this step
    duration: string          # Estimated step duration
    inputs: string[]          # Required inputs for this step
    outputs: string[]         # Outputs produced by this step

# Quality gates to pass
quality_gates:
  - name: string              # Gate name
    type: enum                # security|testing|documentation|performance
    threshold: integer        # Minimum score (0-100)
    blocking: boolean         # Must pass to continue?

# MCP tool inputs (for invoking workflow)
inputs:
  - name: string
    type: enum
    required: boolean
    default: any
    description: string

# Optional
description: string           # Brief description
project_types: string[]       # Applicable project types
---
```

### Workflow Example

```yaml
---
id: single-feature-development
name: Single Feature Development
type: development
version: "1.0.0"

duration: "1-3 days"
complexity: medium

steps:
  - order: 1
    name: Architecture & Design
    agent: architecture-agent
    duration: "0.5-1 day"
    inputs: [feature_requirements]
    outputs: [design_spec]
  - order: 2
    name: Implementation
    agent: web-developer
    duration: "0.5-1.5 days"
    inputs: [design_spec]
    outputs: [implementation, manual_tests]
  - order: 3
    name: Testing
    agent: test-engineer
    duration: "0.25-0.75 days"
    inputs: [implementation]
    outputs: [test_suite, coverage_report]
  - order: 4
    name: Security Review
    agent: security-reviewer
    duration: "0.25-0.5 days"
    inputs: [implementation, test_suite]
    outputs: [security_report]
  - order: 5
    name: Documentation
    agent: documentation-engineer
    duration: "0.25-0.5 days"
    inputs: [implementation, security_report]
    outputs: [documentation]
  - order: 6
    name: Commit
    agent: git-committer
    duration: "0.25 days"
    inputs: [implementation, test_suite, documentation]
    outputs: [commit]

quality_gates:
  - name: Security Review
    type: security
    threshold: 85
    blocking: true
  - name: Test Coverage
    type: testing
    threshold: 90
    blocking: true
  - name: Documentation
    type: documentation
    threshold: 100
    blocking: true

inputs:
  - name: feature_name
    type: string
    required: true
    description: Name of the feature to develop
  - name: requirements
    type: string
    required: true
    description: Feature requirements and acceptance criteria
  - name: project_type
    type: string
    required: false
    default: web-app
    description: Project type (web-app, api, ml, data-platform)

description: Complete feature development from design through deployment
project_types: [web-app, api, ml, data-platform]
---

# Workflow: Single Feature Development

**Purpose:** Complete development of a single feature...
[rest of markdown body]
```

---

## Handoff Template Frontmatter Schema

```yaml
---
# Required fields
id: string                    # Unique identifier (e.g., "security-report")
name: string                  # Display name
version: string               # Schema version

# Handoff metadata
from_agent: string            # Agent ID that produces this handoff
to_agents: string[]           # Agent IDs that consume this handoff
purpose: string               # What this handoff communicates

# Template variables (Jinja2)
variables:
  - name: string              # Variable name in template
    type: enum                # string|integer|boolean|array|object
    required: boolean         # Must be provided?
    description: string       # What this variable contains

# Optional
description: string           # Brief description
---
```

### Handoff Example

```yaml
---
id: security-report
name: Security Review Report
version: "1.0.0"

from_agent: security-reviewer
to_agents:
  - web-developer
  - documentation-engineer
  - git-committer
purpose: Communicate security review findings and approval status

variables:
  - name: component_name
    type: string
    required: true
    description: Name of component reviewed
  - name: review_date
    type: string
    required: true
    description: Date of review (ISO format)
  - name: overall_risk_level
    type: string
    required: true
    description: Risk level (Critical, High, Medium, Low)
  - name: critical_count
    type: integer
    required: true
    description: Number of critical issues
  - name: recommendation_status
    type: string
    required: true
    description: APPROVED, CONDITIONALLY_APPROVED, or REJECTED

description: Security review findings with vulnerability counts and recommendations
---

# Security Review: {{ component_name }}

**Reviewer:** {{ config.roles.security_reviewer or 'Security Reviewer' }}
...
[rest of Jinja2 template body]
```

---

## MCP Tool Generation

The MCP server generates tools from frontmatter as follows:

### Agent → MCP Tool

```python
def agent_to_mcp_tool(frontmatter: dict) -> dict:
    return {
        "name": f"vibey_{frontmatter['id'].replace('-', '_')}",
        "title": frontmatter['name'],
        "description": frontmatter.get('description', ''),
        "inputSchema": {
            "type": "object",
            "properties": {
                inp['name']: {
                    "type": inp['type'],
                    "description": inp.get('description', '')
                }
                for inp in frontmatter.get('inputs', [])
            },
            "required": [
                inp['name']
                for inp in frontmatter.get('inputs', [])
                if inp.get('required', False)
            ]
        }
    }
```

### Workflow → MCP Tool

```python
def workflow_to_mcp_tool(frontmatter: dict) -> dict:
    return {
        "name": f"vibey_workflow_{frontmatter['id'].replace('-', '_')}",
        "title": f"Workflow: {frontmatter['name']}",
        "description": frontmatter.get('description', ''),
        "inputSchema": {
            "type": "object",
            "properties": {
                inp['name']: {
                    "type": inp['type'],
                    "description": inp.get('description', '')
                }
                for inp in frontmatter.get('inputs', [])
            },
            "required": [
                inp['name']
                for inp in frontmatter.get('inputs', [])
                if inp.get('required', False)
            ]
        }
    }
```

---

## Validation Rules

1. **Required fields must be present**
2. **ID must be unique** across all assets of same type
3. **ID must be kebab-case** (lowercase with hyphens)
4. **Type must be valid enum value**
5. **Inputs must have valid type values**
6. **Agent references in workflows must exist**
7. **No circular dependencies** in workflow steps

---

## Migration Notes

When adding frontmatter to existing files:

1. Parse existing markdown header to extract:
   - Role → name
   - Type → type
   - Trigger Patterns → triggers
   - Required Inputs → inputs

2. Generate ID from filename (e.g., `test-engineer.md` → `test-engineer`)

3. Preserve all existing markdown content after frontmatter

4. Validate against schema before committing
