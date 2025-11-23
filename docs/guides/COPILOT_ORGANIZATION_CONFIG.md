# Copilot Organization Configuration Guide

This guide covers configuring Vibey Agent Framework at the GitHub organization level for consistent team-wide AI assistance.

## Overview

GitHub Copilot allows organizations to define:
- **Organization instructions** - Apply to all repositories
- **Content exclusions** - Protect sensitive files
- **Policy controls** - Manage Copilot features
- **Custom agents** - Shared agent definitions

Vibey integrates at both organization and repository levels.

## Configuration Hierarchy

```
Organization Level (applies to all repos)
├── Organization Instructions
├── Policy Settings
├── Content Exclusions
└── Seat Assignments

    └── Repository Level (overrides/extends org settings)
        ├── .github/copilot-instructions.md
        ├── .github/agents/*.md
        └── .github/copilot-content-exclusions.yaml
```

## Organization Instructions

### Location

Organization Settings → Copilot → Custom Instructions

### Vibey Organization Template

```markdown
# Organization AI Development Standards

## Framework

This organization uses the **Vibey Agent Framework** for intelligent
workflow management across all projects.

## Core Principles

1. **Roadmap-Driven Development**
   - Check roadmap status before starting work
   - Update task status as work progresses
   - Follow sprint planning workflows

2. **Agent Specialization**
   - Use domain-specific agents for tasks
   - Let the coordinator route complex requests
   - Follow agent quality gates

3. **Structured Workflows**
   - Use predefined workflows for complex tasks
   - Follow workflow steps sequentially
   - Validate deliverables at each stage

## Standard Agents

When Vibey is configured in a repository, these agents are available:

| Agent | Usage | Domain |
|-------|-------|--------|
| `@coordinator` | Route requests | All |
| `@web-developer` | Frontend | UI/UX |
| `@backend-engineer` | APIs | Services |
| `@test-engineer` | Testing | QA |
| `@security-reviewer` | Security | Audits |
| `@infrastructure-engineer` | DevOps | IaC |

## Standard Workflows

| Workflow | Use Case |
|----------|----------|
| Sprint Planning | Iteration planning |
| Single Feature Development | New features |
| Codebase Audit | Project analysis |
| Architecture Review | System design |

## Code Quality Standards

- All code must pass linting
- Tests required for new features
- Security review for auth/data handling
- Documentation for public APIs

## Repository Setup

Each repository should have:
```
.github/
├── copilot-instructions.md    # Repo-specific instructions
├── agents/                     # Custom agent profiles
└── COPILOT.md                  # Context file
```

Generate with: `vibey deploy --platform copilot`
```

## Policy Settings

### Copilot Features

Configure which Copilot features are enabled:

| Feature | Recommended | Notes |
|---------|-------------|-------|
| Chat | Enabled | Primary interaction mode |
| Inline suggestions | Enabled | Code completion |
| Custom agents | Enabled | Required for Vibey agents |
| MCP | Enabled | Required for MCP tools |
| Knowledge bases | Optional | For custom docs |

### Model Access

Configure available models:

```yaml
models:
  allowed:
    - claude-3.5-sonnet    # Recommended for code
    - gpt-4                # Alternative
    - gpt-4-turbo          # Faster alternative
  default: claude-3.5-sonnet
```

## Content Exclusions

### Organization-Level Exclusions

Protect sensitive files across all repositories:

```yaml
# Organization content exclusions
exclusions:
  # Secrets and credentials
  - "**/.env"
  - "**/.env.*"
  - "**/secrets/**"
  - "**/credentials/**"

  # Keys and certificates
  - "**/*.pem"
  - "**/*.key"
  - "**/*.p12"
  - "**/*.pfx"

  # Configuration with secrets
  - "**/config/production.*"
  - "**/config/*.secret.*"

  # Internal documentation
  - "**/internal/**"
  - "**/confidential/**"
```

### Repository Overrides

Repositories can extend (not reduce) exclusions:

```yaml
# .github/copilot-content-exclusions.yaml
exclusions:
  - "**/vendor/**"           # Repo-specific
  - "**/legacy/**"           # Repo-specific
```

## Seat Management

### Assignment Strategies

| Strategy | Best For | Configuration |
|----------|----------|---------------|
| All members | Small orgs (<50) | Assign to all |
| Team-based | Medium orgs | Assign to teams |
| Role-based | Large orgs | Assign by role |
| Request-based | Cost control | Manual approval |

### Team Assignment Example

```yaml
# Copilot seat assignments
teams:
  - name: engineering
    seats: all
  - name: design
    seats: none
  - name: devops
    seats: all
  - name: contractors
    seats: request
```

## Repository Configuration

### Standard Setup

Each repository using Vibey should run:

```bash
vibey deploy --platform copilot
```

### Generated Files

| File | Purpose | Customizable |
|------|---------|--------------|
| `copilot-instructions.md` | AI instructions | Extend only |
| `agents/*.md` | Agent profiles | No (regenerated) |
| `COPILOT.md` | Context | No (regenerated) |
| `.checksums.json` | Drift detection | No |

### Extending Repository Instructions

Add repository-specific guidance after the generated content:

```markdown
<!-- Generated content above -->

---

## Repository-Specific Guidelines

### Project: User Authentication Service

This repository implements OAuth 2.0 and OIDC.

### Key Patterns

- Use `AuthService` for all auth operations
- Token validation via `validateToken()` middleware
- Refresh tokens stored in Redis

### Testing Requirements

- 90% coverage for auth flows
- Integration tests for all OAuth providers
- Security tests for token handling
```

## Shared Agent Definitions

### Creating Org-Wide Agents

For agents used across multiple repositories, create a template repository:

```bash
# Create template repo
gh repo create org-name/vibey-template --template

# Add Vibey configuration
cd vibey-template
vibey init
vibey deploy --platform copilot

# Push
git add .
git commit -m "Initial Vibey setup"
git push
```

### Custom Organization Agents

Add organization-specific agents to the template:

```markdown
<!-- .github/agents/org-security-reviewer.md -->
# Organization Security Reviewer

Security review specialist following [OrgName] security standards.

## Capabilities

- OWASP Top 10 compliance
- SOC 2 requirements
- PCI-DSS (if applicable)
- Internal security policies

## Standards

Follow organization security checklist:
1. Input validation
2. Authentication checks
3. Authorization verification
4. Data encryption
5. Audit logging

## MCP Tool

Invoke via MCP: `vibey_security_reviewer`
```

## Workflow Automation

### Automated Copilot Config Updates

```yaml
# .github/workflows/sync-copilot-config.yml
name: Sync Copilot Config

on:
  workflow_dispatch:
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.ORG_ADMIN_TOKEN }}

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Vibey
        run: pip install vibey-framework

      - name: Regenerate Config
        run: vibey deploy --platform copilot --clean

      - name: Create PR
        uses: peter-evans/create-pull-request@v5
        with:
          title: "chore: Update Copilot configuration"
          body: "Automated Vibey configuration update"
          branch: auto/copilot-config-update
```

## Monitoring Configuration

### Drift Detection

Verify configuration hasn't been manually edited:

```bash
vibey validate --platform copilot
```

### CI Integration

```yaml
# .github/workflows/validate-copilot.yml
name: Validate Copilot Config

on:
  pull_request:
    paths:
      - '.github/copilot-instructions.md'
      - '.github/agents/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Vibey
        run: pip install vibey-framework

      - name: Validate Configuration
        run: vibey validate --platform copilot

      - name: Check for drift
        run: |
          vibey deploy --platform copilot --dry-run
          git diff --exit-code .github/
```

## Troubleshooting

### Organization Instructions Not Visible

1. Check org-level Copilot is enabled
2. Verify user has Copilot seat
3. Ensure instructions are saved (not just drafted)
4. Wait 5 minutes for propagation

### Policy Not Applied

1. Verify policy is enabled at org level
2. Check repository doesn't override
3. Review user's team membership
4. Check for conflicting policies

### Agents Not Available

1. Verify agents feature is enabled in policy
2. Check `.github/agents/` exists in repo
3. Ensure files are valid markdown
4. Restart IDE

## Best Practices

1. **Keep org instructions focused** - General principles only
2. **Let repos extend** - Specific details at repo level
3. **Review regularly** - Update as standards evolve
4. **Automate updates** - Use CI/CD for config sync
5. **Monitor usage** - Review analytics monthly
6. **Train teams** - Ensure developers know how to use

## Resources

- [GitHub Copilot for Organizations](https://docs.github.com/en/copilot/copilot-business)
- [Custom Instructions](https://docs.github.com/en/copilot/customizing-copilot)
- [Vibey Copilot Integration](./COPILOT_INTEGRATION.md)
- [Enterprise Deployment](./COPILOT_ENTERPRISE_DEPLOYMENT.md)
