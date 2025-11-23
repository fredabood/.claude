# Copilot Enterprise Deployment Guide

This guide covers deploying Vibey Agent Framework with GitHub Copilot in enterprise environments.

## Overview

GitHub Copilot Enterprise provides additional features for organizations:
- Organization-level configuration
- Custom knowledge bases
- Policy controls
- Usage analytics
- SSO integration

Vibey integrates with all these features through its zero-drift architecture.

## Prerequisites

- GitHub Copilot Enterprise subscription
- Organization admin access
- Vibey framework installed
- GitHub Enterprise Cloud or Server (3.8+)

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Enterprise                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Organization Level                       │   │
│  │  ┌─────────────────┐  ┌─────────────────────────┐   │   │
│  │  │ Copilot Policy  │  │ Organization Instructions│   │   │
│  │  │ - Model access  │  │ - Vibey framework rules  │   │   │
│  │  │ - Feature flags │  │ - Coding standards       │   │   │
│  │  └─────────────────┘  └─────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                  │
│  ┌────────────────────────┼────────────────────────────┐   │
│  │            Repository Level                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │   │
│  │  │ Repo A       │  │ Repo B       │  │ Repo C   │  │   │
│  │  │ .github/     │  │ .github/     │  │ .github/ │  │   │
│  │  │ - agents/    │  │ - agents/    │  │ - agents/│  │   │
│  │  │ - copilot-   │  │ - copilot-   │  │ - copilot│  │   │
│  │  │   instruc... │  │   instruc... │  │   ins... │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Step 1: Organization Setup

### Enable Copilot for Organization

1. Navigate to Organization Settings
2. Go to Copilot → Policies
3. Enable Copilot for organization members
4. Configure model access (Claude, GPT-4, etc.)

### Configure Organization Policies

```yaml
# Example organization policy
copilot:
  enabled: true
  models:
    - claude-3.5-sonnet
    - gpt-4
  features:
    chat: enabled
    inline: enabled
    agents: enabled
    mcp: enabled
  content_exclusions:
    - "**/*.env"
    - "**/secrets/**"
    - "**/credentials/**"
```

## Step 2: Create Organization Instructions

Create organization-wide instructions that apply to all repositories:

### Location
Organization Settings → Copilot → Custom Instructions

### Content Template

```markdown
# Organization Development Standards

## Vibey Agent Framework

All repositories in this organization use the Vibey Agent Framework for
intelligent workflow management. Developers should:

1. Check roadmap status before starting work
2. Use appropriate specialized agents for tasks
3. Follow structured workflows for complex features
4. Update task status as work progresses

## Available Framework Tools

When Vibey is configured in a repository:

### Roadmap Management
- `vibey_roadmap_status` - View overall progress
- `vibey_start_task` / `vibey_complete_task` - Track work
- `vibey_query_*` - Get detailed information

### Specialized Agents
Reference `@agent-name` in Copilot Chat:
- `@coordinator` - Route complex requests
- `@web-developer` - Frontend development
- `@backend-engineer` - API development
- `@test-engineer` - Testing and QA
- `@security-reviewer` - Security audits

## Code Standards

- Follow repository-specific instructions in `.github/copilot-instructions.md`
- Use custom agents defined in `.github/agents/`
- Adhere to quality gates before task completion
```

## Step 3: Repository Deployment

Deploy Vibey to each repository:

```bash
# Clone repository
git clone https://github.com/org/repo.git
cd repo

# Initialize Vibey (if not already done)
vibey init

# Deploy for Copilot
vibey deploy --platform copilot

# Commit and push
git add .github/
git commit -m "feat: Add Vibey Copilot integration"
git push
```

### Automated Deployment

Create a GitHub Action for automated deployment:

```yaml
# .github/workflows/vibey-deploy.yml
name: Deploy Vibey

on:
  push:
    paths:
      - 'framework/agents/**'
      - 'framework/workflows/**'
      - '.vibey/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Vibey
        run: pip install vibey-framework

      - name: Deploy to Copilot
        run: vibey deploy --platform copilot --clean

      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add .github/
          git diff --staged --quiet || git commit -m "chore: Update Copilot configuration"
          git push
```

## Step 4: Team Onboarding

### Developer Setup

1. **Install Copilot extension** in VS Code or JetBrains IDE
2. **Authenticate** with GitHub (SSO if configured)
3. **Open repository** in IDE
4. **Verify integration** by asking about available tools

### Training Materials

Provide team documentation:

```markdown
## Quick Start for Developers

1. Open any Vibey-configured repository
2. Use Copilot Chat (Cmd/Ctrl + Shift + I)
3. Reference agents: `@web-developer help me with...`
4. Check roadmap: "What's the current roadmap status?"

## Common Commands

- "Show me available Vibey agents"
- "@coordinator What should I work on next?"
- "@test-engineer Write tests for the auth module"
- "Use sprint planning workflow for next iteration"
```

## Step 5: Monitoring & Analytics

### Usage Analytics

Access Copilot usage data:
1. Organization Settings → Copilot → Usage
2. View metrics per repository/user
3. Track agent usage patterns

### Custom Metrics

Track Vibey-specific metrics:

```bash
# Query roadmap progress across repos
for repo in repo1 repo2 repo3; do
  echo "=== $repo ==="
  cd $repo
  vibey roadmap status --format json
  cd ..
done
```

## Security Considerations

### Content Exclusions

Configure what Copilot cannot access:

```yaml
# .github/copilot-content-exclusions.yaml
exclusions:
  - "**/.env*"
  - "**/secrets/**"
  - "**/credentials/**"
  - "**/*.pem"
  - "**/*.key"
```

### MCP Server Security

For MCP tools via Copilot CLI:

1. **Local execution only** - MCP server runs locally
2. **No network exposure** - stdio transport, not HTTP
3. **File access** - Limited to repository directory
4. **No credentials** - MCP server doesn't store secrets

### Audit Logging

Enable audit logging for compliance:

```yaml
# Organization audit log settings
audit:
  copilot_interactions: enabled
  agent_invocations: enabled
  tool_usage: enabled
```

## Scaling Considerations

### Multi-Repository Deployment

For organizations with many repositories:

```bash
#!/bin/bash
# deploy-vibey-org.sh

REPOS=$(gh repo list ORG_NAME --json name -q '.[].name')

for repo in $REPOS; do
  echo "Deploying to $repo..."
  gh repo clone "ORG_NAME/$repo" --depth 1
  cd "$repo"

  if [ -d ".vibey" ]; then
    vibey deploy --platform copilot
    git add .github/
    git commit -m "chore: Update Vibey Copilot config" || true
    git push || true
  fi

  cd ..
  rm -rf "$repo"
done
```

### Template Repository

Create a template with Vibey pre-configured:

1. Create template repository with Vibey setup
2. Include `.github/` Copilot configuration
3. New repositories inherit Vibey integration

## Troubleshooting

### Organization Instructions Not Applied

1. Verify org-level Copilot is enabled
2. Check user has Copilot seat assigned
3. Ensure custom instructions are saved
4. Restart IDE

### Repository Configuration Ignored

1. Verify `.github/copilot-instructions.md` exists
2. Check file is committed to default branch
3. Ensure no syntax errors in markdown
4. Test in Copilot Chat

### MCP Tools Unavailable

1. MCP requires Copilot CLI (not IDE alone)
2. Install: `gh extension install github/gh-copilot`
3. Verify: `gh copilot --version`
4. Test locally first: `python -m framework.mcp.server`

### Agent Mentions Not Working

1. Verify `.github/agents/` directory exists
2. Check agent files have correct format
3. Ensure files are committed
4. Try typing `@` to see available agents

## Cost Management

### Seat Management

- Assign Copilot seats strategically
- Monitor usage per user/team
- Consider team-based assignments

### Token Usage

- Monitor token consumption
- Set usage alerts
- Review high-usage patterns

## Compliance

### Data Residency

- Copilot Enterprise supports data residency
- Configure region in organization settings
- Vibey data stays in repository

### Retention Policies

- Chat history retention configurable
- Audit logs follow org policy
- Repository data follows Git retention

## Support Channels

- GitHub Enterprise Support
- Organization admin contacts
- Vibey documentation and issues

## Resources

- [GitHub Copilot Enterprise Docs](https://docs.github.com/en/enterprise-cloud@latest/copilot)
- [Copilot for Business Admin Guide](https://docs.github.com/en/copilot/copilot-business)
- [Vibey Copilot Integration](./COPILOT_INTEGRATION.md)
- [Migration Guide](./MIGRATION_CLAUDE_TO_COPILOT.md)
