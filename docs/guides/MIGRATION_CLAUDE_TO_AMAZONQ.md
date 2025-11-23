# Migration Guide: Claude Code to Amazon Q Developer

This guide covers migrating your Vibey-powered project from Claude Code to Amazon Q Developer.

## Overview

| Aspect | Claude Code | Amazon Q |
|--------|-------------|----------|
| MCP Support | Full | Full (GA 2025) |
| Config Location | `.claude/` | `.amazonq/` |
| Config Format | JSON dict | JSON dict |
| Context Files | `CLAUDE.md` | `AMAZONQ.md` |
| Auth | API key | AWS credentials |

## Amazon Q Interfaces

Amazon Q Developer is available across:

- **Amazon Q CLI** (`q` command)
- **VS Code Extension** (Amazon Q for VS Code)
- **JetBrains Plugin** (Amazon Q for JetBrains)
- **AWS Console** (browser-based)

## Migration Steps

### 1. Deploy Vibey for Amazon Q

```bash
vibey deploy --platform amazonq
```

This creates:
- `.amazonq/mcp.json` - MCP server configuration
- `.amazonq/AMAZONQ.md` - Context for Amazon Q
- `.amazonq/README.md` - Setup documentation

### 2. Configure AWS Credentials

Amazon Q uses AWS authentication:

```bash
# Option 1: AWS CLI configuration
aws configure

# Option 2: AWS SSO
aws sso login --profile your-profile

# Option 3: Environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

### 3. Install Amazon Q CLI

```bash
# macOS (Homebrew)
brew install amazon-q

# Linux
curl -fsSL https://amazon-q.com/install | bash
```

### 4. Verify MCP Connection

```bash
q chat "What Vibey tools are available?"
```

## Configuration Comparison

### Claude Code

```json
{
  "mcpServers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "framework.mcp.server"]
    }
  }
}
```

### Amazon Q

```json
{
  "mcpServers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "framework.mcp.server"],
      "env": {}
    }
  }
}
```

Both use the same `mcpServers` format, making migration straightforward.

## Feature Mapping

| Claude Code | Amazon Q |
|-------------|----------|
| CLAUDE.md context | AMAZONQ.md context |
| Claude API | AWS Bedrock |
| Task subagents | Agent tools via MCP |
| `/vibey` command | `q chat` CLI |

## Using Vibey Tools

### CLI Usage

```bash
# Check roadmap status
q chat "Use vibey_roadmap_status to show project progress"

# Start a task
q chat "Use vibey_start_task with task_id task-001"

# Query sprint info
q chat "Use vibey_query_sprint for sprint-1"
```

### IDE Usage (VS Code/JetBrains)

1. Open Amazon Q panel
2. Type natural language requests
3. Tools are invoked automatically

```
Check the project roadmap status using the Vibey tools
```

## AWS Integration

Amazon Q provides AWS-native capabilities:

### IAM Policies

Control MCP access via IAM:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "q:InvokeMCPTool",
      "Resource": "arn:aws:q:*:*:mcp-server/vibey"
    }
  ]
}
```

### CloudWatch Logging

Enable logging for audit:

```json
{
  "mcpServers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "framework.mcp.server"],
      "logging": {
        "cloudwatch": true,
        "logGroup": "/aws/q/mcp/vibey"
      }
    }
  }
}
```

## Enterprise Deployment

### Organization-Wide Setup

1. Configure at organization level in AWS Console
2. Use AWS Organizations for policy management
3. Deploy via AWS CloudFormation or Terraform

### Security Controls

- **IAM boundaries**: Limit MCP tool access
- **VPC endpoints**: Keep traffic private
- **Audit trails**: CloudTrail logging
- **Encryption**: KMS for data at rest

## Troubleshooting

### Authentication Errors

```bash
# Check credentials
aws sts get-caller-identity

# Refresh SSO
aws sso login

# Verify Amazon Q access
q whoami
```

### MCP Server Not Found

1. Verify `.amazonq/mcp.json` exists
2. Check Python path is correct
3. Test server manually:
   ```bash
   python -m framework.mcp.server --test
   ```

### Tools Not Available

1. Check MCP config syntax
2. Verify AWS permissions
3. Restart Amazon Q client

## Running Both Platforms

Maintain parallel deployments:

```bash
# Deploy to both
vibey deploy --platform claude-code
vibey deploy --platform amazonq

# Or deploy all at once
vibey deploy --platform all
```

Directories are separate:
- Claude Code: `.claude/`
- Amazon Q: `.amazonq/`

## Migration Checklist

- [ ] Deploy Vibey for Amazon Q
- [ ] Configure AWS credentials
- [ ] Install Amazon Q CLI
- [ ] Test MCP connection
- [ ] Verify all tools work
- [ ] Configure IAM policies (enterprise)
- [ ] Set up logging (optional)
- [ ] Document team workflow

## Best Practices

1. **Use AWS SSO**: Centralized credential management
2. **Enable CloudWatch**: Track tool usage and errors
3. **Apply least privilege**: Restrict MCP access as needed
4. **Test thoroughly**: Verify all workflows before team rollout

## Cost Considerations

Amazon Q pricing:
- **Pro tier**: Per-user monthly subscription
- **AWS Bedrock**: Pay-per-use for model invocations
- **Data transfer**: Standard AWS data charges

MCP servers run locally, so no additional AWS compute costs.

## Next Steps

After migration:

1. Train team on Amazon Q CLI and IDE extensions
2. Configure organization-level policies
3. Set up monitoring and alerting
4. Document team-specific workflows

---

For more information:
- [Amazon Q Developer Documentation](https://docs.aws.amazon.com/amazonq/)
- [AWS MCP Integration Guide](https://docs.aws.amazon.com/amazonq/mcp)
- [Vibey Framework Documentation](../README.md)
