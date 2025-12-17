# Recipe Development Guide

> **Version:** 1.0.0
> **Last Updated:** 2025-11-22

This guide explains how to create Goose recipes that leverage Vibey tools.

## What Are Recipes?

Goose recipes are reusable automation templates that chain together tool calls. Vibey workflows automatically generate recipes, but you can also create custom ones.

## Recipe Structure

```yaml
name: Recipe Name
description: What this recipe does
version: "1.0.0"

steps:
  - name: Step 1
    tool: vibey_tool_name
    description: What this step does
    inputs:
      param1: value1

  - name: Step 2
    tool: another_tool
    description: Next step
    depends_on: Step 1

quality_gates:
  - name: gate_name
    threshold: 80
    blocking: true
```

## Auto-Generated Recipes

Vibey workflows automatically become recipes. The mapping:

| Workflow Field | Recipe Field |
|---------------|--------------|
| `id` | Recipe filename |
| `name` | `name` |
| `description` | `description` |
| `steps[].agent` | `steps[].tool` (with `vibey_` prefix) |
| `quality_gates` | `quality_gates` |

### Example: Workflow to Recipe

**Workflow** (`framework/workflows/feature-development.md`):
```yaml
---
id: feature-development
name: Feature Development
steps:
  - order: 1
    name: Planning
    agent: sprint-planner
  - order: 2
    name: Implementation
    agent: web-developer
  - order: 3
    name: Testing
    agent: test-engineer
---
```

**Generated Recipe** (`exports/goose/recipes/feature-development.yaml`):
```yaml
name: Feature Development
description: Feature Development workflow
version: "1.0.0"

steps:
  - name: Planning
    tool: vibey_sprint_planner
    order: 1

  - name: Implementation
    tool: vibey_web_developer
    order: 2

  - name: Testing
    tool: vibey_test_engineer
    order: 3
```

## Creating Custom Recipes

### Basic Recipe

```yaml
# recipes/quick-test.yaml
name: Quick Test Suite
description: Run tests with coverage check
version: "1.0.0"

steps:
  - name: Write Tests
    tool: vibey_test_engineer
    inputs:
      task: "Write unit tests for modified files"
      context: "Focus on edge cases"

  - name: Review Security
    tool: vibey_security_reviewer
    inputs:
      task: "Check for security issues in test files"
```

### Recipe with Dependencies

```yaml
name: Full Feature Pipeline
description: Complete feature from idea to deployment
version: "1.0.0"

steps:
  - name: Research
    tool: vibey_researcher
    inputs:
      task: "Research best practices for {{ feature_type }}"

  - name: Design
    tool: vibey_architecture_agent
    depends_on: Research
    inputs:
      task: "Create technical design based on research"

  - name: Implement
    tool: vibey_web_developer
    depends_on: Design
    inputs:
      task: "Implement the designed solution"

  - name: Test
    tool: vibey_test_engineer
    depends_on: Implement
    inputs:
      task: "Write comprehensive tests"

  - name: Document
    tool: vibey_documentation_engineer
    depends_on: Test
    inputs:
      task: "Document the new feature"
```

### Recipe with Quality Gates

```yaml
name: Production-Ready Feature
description: Feature with quality checkpoints
version: "1.0.0"

steps:
  - name: Implement
    tool: vibey_web_developer
    inputs:
      task: "{{ feature_description }}"

  - name: Test
    tool: vibey_test_engineer
    depends_on: Implement

  - name: Security Check
    tool: vibey_security_reviewer
    depends_on: Test

  - name: Performance Check
    tool: vibey_performance_engineer
    depends_on: Security Check

quality_gates:
  - name: test_coverage
    type: percentage
    threshold: 80
    blocking: true
    check_after: Test

  - name: security_passed
    type: pass_fail
    threshold: 1
    blocking: true
    check_after: Security Check

  - name: performance_baseline
    type: percentage
    threshold: 95
    blocking: false
    check_after: Performance Check
```

## Recipe Variables

Use `{{ variable }}` syntax for dynamic values:

```yaml
name: Dynamic Feature Recipe
description: Build {{ feature_name }}

steps:
  - name: Plan {{ feature_name }}
    tool: vibey_sprint_planning
    inputs:
      task: "Plan implementation of {{ feature_name }}"
      context: "Project type: {{ project_type }}"
```

**Invoke with:**
```
> Run the feature recipe with feature_name="User Dashboard" and project_type="React"
```

## Available Tools for Recipes

### Development Tools

| Tool | Best For |
|------|----------|
| `vibey_web_developer` | Frontend features |
| `vibey_backend_engineer` | API development |
| `vibey_database_specialist` | Schema changes |
| `vibey_infrastructure_engineer` | DevOps tasks |
| `vibey_ml_engineer` | ML features |

### Quality Tools

| Tool | Best For |
|------|----------|
| `vibey_test_engineer` | Writing tests |
| `vibey_security_reviewer` | Security audits |
| `vibey_performance_engineer` | Optimization |
| `vibey_observability_engineer` | Logging/monitoring |

### Planning Tools

| Tool | Best For |
|------|----------|
| `vibey_sprint_planning` | Sprint planning |
| `vibey_researcher` | Research tasks |
| `vibey_architecture_agent` | System design |

### Documentation Tools

| Tool | Best For |
|------|----------|
| `vibey_documentation_engineer` | Writing docs |
| `vibey_diagram_engineer` | Creating diagrams |
| `vibey_git_committer` | Git commits |

## Recipe Patterns

### Sequential Pipeline

```yaml
steps:
  - name: Step 1
    tool: tool_a
  - name: Step 2
    tool: tool_b
    depends_on: Step 1
  - name: Step 3
    tool: tool_c
    depends_on: Step 2
```

### Parallel Execution

```yaml
steps:
  - name: Setup
    tool: setup_tool

  - name: Frontend Work
    tool: vibey_web_developer
    depends_on: Setup

  - name: Backend Work
    tool: vibey_backend_engineer
    depends_on: Setup  # Same dependency = parallel

  - name: Integration
    tool: integration_tool
    depends_on:
      - Frontend Work
      - Backend Work  # Waits for both
```

### Conditional Steps

```yaml
steps:
  - name: Check Type
    tool: check_tool
    outputs:
      - project_type

  - name: Web Dev
    tool: vibey_web_developer
    condition: "{{ project_type == 'frontend' }}"

  - name: API Dev
    tool: vibey_backend_engineer
    condition: "{{ project_type == 'backend' }}"
```

## Exporting Recipes

### Export All Recipes

```bash
vibey export --platform goose --output ./exports
```

Creates:
```
exports/
└── goose/
    ├── recipes/
    │   ├── feature-development.yaml
    │   ├── sprint-planning.yaml
    │   ├── security-audit.yaml
    │   └── ...
    └── goose-extension.yaml
```

### Export Specific Recipe

```bash
vibey export --platform goose --workflow feature-development
```

## Using Recipes in Goose

### Run a Recipe

```
> Run the feature-development recipe for a login page
```

### List Available Recipes

```
> What Vibey recipes are available?
```

### Customize Recipe Execution

```
> Run feature-development but skip the documentation step
```

## Best Practices

### 1. Start Simple

Begin with 2-3 steps, add complexity later.

### 2. Use Quality Gates

Add gates to catch issues early:
```yaml
quality_gates:
  - name: tests_pass
    type: pass_fail
    threshold: 1
    blocking: true
```

### 3. Document Steps

Clear descriptions help Goose explain what it's doing:
```yaml
- name: Security Audit
  tool: vibey_security_reviewer
  description: |
    Scan for OWASP Top 10 vulnerabilities.
    Check authentication and authorization.
    Review data validation.
```

### 4. Handle Failures

Use `on_failure` for graceful degradation:
```yaml
- name: Deploy
  tool: deploy_tool
  on_failure:
    - name: Rollback
      tool: rollback_tool
```

### 5. Version Your Recipes

Update version when changing recipes:
```yaml
version: "1.1.0"  # Bumped for new step
```

## Example Recipes

### Code Review Recipe

```yaml
name: Comprehensive Code Review
description: Multi-agent code review
version: "1.0.0"

steps:
  - name: Security Review
    tool: vibey_security_reviewer
    inputs:
      task: "Review for security vulnerabilities"

  - name: Performance Review
    tool: vibey_performance_engineer
    inputs:
      task: "Check for performance issues"

  - name: Test Coverage
    tool: vibey_test_engineer
    inputs:
      task: "Verify test coverage is adequate"

  - name: Documentation Check
    tool: vibey_documentation_engineer
    inputs:
      task: "Ensure code is properly documented"

quality_gates:
  - name: all_reviews_pass
    type: pass_fail
    threshold: 1
    blocking: true
```

### Sprint Kickoff Recipe

```yaml
name: Sprint Kickoff
description: Start a new sprint with proper planning
version: "1.0.0"

steps:
  - name: Review Backlog
    tool: vibey_roadmap_status
    description: Check current roadmap state

  - name: Plan Sprint
    tool: vibey_sprint_planning
    inputs:
      task: "Plan sprint {{ sprint_number }}"
      context: "Team capacity: {{ team_capacity }} story points"

  - name: Create Tasks
    tool: vibey_architecture_agent
    inputs:
      task: "Break down sprint goals into tasks"

  - name: Document Sprint
    tool: vibey_documentation_engineer
    inputs:
      task: "Create sprint documentation"
```

## Related Documentation

- [Goose Integration Guide](./GOOSE_INTEGRATION.md)
- [Frontmatter Schema Reference](../reference/FRONTMATTER_SCHEMA.md)
- [Workflow Reference](../WORKFLOWS.md)
