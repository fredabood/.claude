# Amazon Q Developer Platform Port - Implementation Plan

**Track ID:** `amazonq-port`
**Created:** 2025-11-23
**Priority:** High
**Estimated Duration:** 4-6 weeks (150-200 hours)
**Status:** Planning

---

## Executive Summary

This implementation plan details the port of the Vibey Agent Framework to Amazon Q Developer, AWS's AI-powered coding assistant. Amazon Q Developer has **native MCP (Model Context Protocol) support** as of April 2025, which significantly reduces implementation complexity. The Vibey MCP server can be directly reused with minimal configuration, and Amazon Q's rules-based customization system (`.amazonq/rules/`) provides a clean integration point for agent context.

### Key Advantages

1. **MCP Native Support** - Amazon Q CLI (v1.9.0+) and IDE plugins support MCP protocol directly
2. **Rules-Based Customization** - `.amazonq/rules/` directory for markdown-based context (similar to CLAUDE.md)
3. **Multi-IDE Support** - VS Code, JetBrains, Eclipse, Visual Studio
4. **Enterprise IAM Integration** - AWS IAM Identity Center for authentication
5. **GitHub Integration** - `/dev`, `/doc`, `/test`, `/review` agents built-in

### Estimated Compatibility

**Overall:** 80-90% compatible (HIGH reusability)

---

## Research Findings

### Amazon Q Developer Architecture

#### Core Features (2025)

| Feature | Description | Vibey Compatibility |
|---------|-------------|---------------------|
| **MCP Protocol** | Native support since April 2025 | Direct reuse of `framework/mcp/server.py` |
| **Rules Directory** | `.amazonq/rules/*.md` for context | Generate from agent frontmatter |
| **IDE Plugins** | VS Code, JetBrains, Eclipse, Visual Studio | Use MCP for tool integration |
| **CLI** | Amazon Q Developer CLI (standalone) | Full MCP support |
| **Built-in Agents** | `/dev`, `/doc`, `/test`, `/review`, `/transform` | Map to Vibey workflows |
| **Customizations** | RAG-based on private codebase | Enterprise feature |

#### MCP Implementation Details

Amazon Q Developer supports MCP through:

1. **Amazon Q CLI** - Full stdio-based MCP server support
   - Configuration in `~/.amazon-q/mcp.json`
   - Supports local (stdio) and remote (HTTP) servers
   - OAuth authentication for remote servers
   - Background server loading for immediate interaction

2. **IDE Plugins** - MCP support in VS Code and JetBrains
   - Global scope (all projects) or Workspace scope (current project)
   - Configuration via IDE settings
   - Tool discovery from connected MCP servers

3. **Server Requirements**
   - MCP SDK compatible servers
   - Python-based servers recommended (uvx for execution)
   - Tool definitions follow MCP spec

### AWS Authentication & IAM Requirements

#### Authentication Methods

| Method | Use Case | Configuration |
|--------|----------|---------------|
| **AWS Builder ID** | Free tier, individual use | No AWS account needed |
| **IAM Identity Center** | Enterprise/Pro tier | AWS Organizations integration |
| **Federated Identity** | SSO via SAML 2.0 | Microsoft Entra ID, PingIdentity, etc. |

#### Enterprise Setup Flow

```
1. Enable IAM Identity Center in AWS Organizations
2. Connect identity source (Entra ID, Okta, etc.)
3. Set up Amazon Q Developer Pro subscriptions
4. Assign users via IAM Identity Center
5. Users authenticate in IDE via SSO
```

#### IAM Policies for MCP

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "q:StartConversation",
        "q:SendMessage",
        "q:GetConversation"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Architecture Decisions

### Decision 1: MCP Server Reuse (APPROVED)

**Decision:** Directly reuse the existing Vibey MCP server (`framework/mcp/server.py`) with Amazon Q Developer.

**Rationale:**
- Amazon Q supports MCP protocol natively
- Our MCP server already exposes 46 tools
- Dynamic tool discovery from frontmatter works unchanged
- Zero code changes required for core functionality

**Configuration:**
```json
// ~/.amazon-q/mcp.json or .amazonq/mcp.json
{
  "mcpServers": {
    "vibey": {
      "commandLine": "python -m framework.mcp.server",
      "env": {
        "VIBEY_ROOT": "${workspaceFolder}"
      }
    }
  }
}
```

### Decision 2: Rules Directory Generation (APPROVED)

**Decision:** Generate `.amazonq/rules/` markdown files from agent frontmatter.

**Rationale:**
- Amazon Q reads `.amazonq/rules/*.md` for context (like CLAUDE.md)
- Maintains zero-drift architecture (frontmatter is source of truth)
- Familiar pattern from Gemini adapter

**Generated Structure:**
```
.amazonq/
├── rules/
│   ├── vibey-context.md          # Main context (from agents)
│   ├── coding-standards.md       # From quality agents
│   ├── workflow-guidance.md      # From workflow frontmatter
│   └── security-rules.md         # From security agent
├── mcp.json                      # MCP server configuration
└── .generated                    # Marker file with checksums
```

### Decision 3: Adapter Pattern (APPROVED)

**Decision:** Create `vibey/adapters/amazonq/` following the existing adapter pattern.

**Rationale:**
- Consistent with Goose, Aider, Gemini adapters
- Implements `PlatformAdapter` base class
- Validates deployment, generates context files, handles cleanup

**File Structure:**
```
vibey/adapters/amazonq/
├── __init__.py
├── adapter.py             # Main AmazonQAdapter class
├── rules_generator.py     # Generate .amazonq/rules/ from frontmatter
├── mcp_config.py          # Generate mcp.json configuration
└── auth_helper.py         # AWS authentication utilities (optional)
```

### Decision 4: AWS SDK Integration (DEFERRED)

**Decision:** Defer direct AWS SDK integration to Sprint 3.

**Rationale:**
- MCP server handles all tool interactions
- AWS SDK only needed for advanced features (CloudWatch, CodeGuru)
- Keep MVP simple, add AWS features incrementally

---

## Zero-Drift Architecture

### Source of Truth

All Amazon Q artifacts are generated from existing sources:

| Generated File | Source |
|----------------|--------|
| `.amazonq/rules/*.md` | `framework/agents/*.md` frontmatter |
| `.amazonq/mcp.json` | Configuration templates |
| `.amazonq/settings.json` | `.vibey/config/framework.yaml` |

### Generation Flow

```
framework/agents/*.md ─┬─> .amazonq/rules/vibey-context.md
                       │
                       └─> .amazonq/rules/coding-standards.md

framework/workflows/*.md ─> .amazonq/rules/workflow-guidance.md

.vibey/config/*.yaml ─> .amazonq/settings.json
                     ─> .amazonq/mcp.json
```

### Drift Detection

- Checksums stored in `.amazonq/.checksums.json`
- CI validates no manual edits to generated files
- `vibey deploy amazonq --validate` command

---

## Sprint Planning

### Sprint 1: Core Adapter & MCP Integration (1-2 weeks)

**Goal:** Working Amazon Q integration via MCP server

#### Tasks

| ID | Task | File Path | Hours |
|----|------|-----------|-------|
| AQ-1.1 | Create adapter module structure | `vibey/adapters/amazonq/__init__.py` | 2 |
| AQ-1.2 | Implement AmazonQAdapter base class | `vibey/adapters/amazonq/adapter.py` | 8 |
| AQ-1.3 | Create MCP config generator | `vibey/adapters/amazonq/mcp_config.py` | 4 |
| AQ-1.4 | Test MCP server with Amazon Q CLI | Manual testing | 4 |
| AQ-1.5 | Document Amazon Q CLI setup | `docs/platforms/amazonq-setup.md` | 4 |
| AQ-1.6 | Add amazonq target to deploy command | `vibey/cli/commands.py` | 2 |

**Deliverables:**
- Working `vibey deploy amazonq` command
- MCP server connects to Amazon Q CLI
- Basic documentation

**Acceptance Criteria:**
- [ ] `vibey deploy amazonq` creates `.amazonq/mcp.json`
- [ ] Amazon Q CLI discovers Vibey MCP tools
- [ ] Agent tools callable from Amazon Q chat

### Sprint 2: Rules Generation & Context (1-2 weeks)

**Goal:** Full context generation for Amazon Q

#### Tasks

| ID | Task | File Path | Hours |
|----|------|-----------|-------|
| AQ-2.1 | Create rules generator | `vibey/adapters/amazonq/rules_generator.py` | 8 |
| AQ-2.2 | Generate vibey-context.md from agents | Rules generator | 4 |
| AQ-2.3 | Generate workflow-guidance.md | Rules generator | 4 |
| AQ-2.4 | Generate coding-standards.md from quality agents | Rules generator | 3 |
| AQ-2.5 | Implement checksum tracking | `vibey/adapters/amazonq/adapter.py` | 4 |
| AQ-2.6 | Add drift validation | `vibey/adapters/amazonq/adapter.py` | 4 |
| AQ-2.7 | Test end-to-end with Amazon Q | Manual testing | 6 |

**Deliverables:**
- Complete `.amazonq/rules/` generation
- Zero-drift validation
- Agent context visible in Amazon Q

**Acceptance Criteria:**
- [ ] Rules files generated from frontmatter
- [ ] Amazon Q uses Vibey context for responses
- [ ] `--validate` flag detects manual edits

### Sprint 3: IDE Integration & Enterprise Features (1-2 weeks)

**Goal:** VS Code/JetBrains integration, IAM setup guide

#### Tasks

| ID | Task | File Path | Hours |
|----|------|-----------|-------|
| AQ-3.1 | VS Code settings generation | `vibey/adapters/amazonq/ide_config.py` | 6 |
| AQ-3.2 | JetBrains settings generation | `vibey/adapters/amazonq/ide_config.py` | 6 |
| AQ-3.3 | Create IAM setup guide | `docs/platforms/amazonq-enterprise.md` | 8 |
| AQ-3.4 | Test with IAM Identity Center | Manual testing | 8 |
| AQ-3.5 | Add `--ide` flag to deploy command | `vibey/cli/commands.py` | 2 |
| AQ-3.6 | Create troubleshooting guide | `docs/platforms/amazonq-troubleshooting.md` | 4 |

**Deliverables:**
- IDE-specific configurations
- Enterprise setup documentation
- Troubleshooting resources

**Acceptance Criteria:**
- [ ] MCP works in VS Code with Amazon Q extension
- [ ] MCP works in JetBrains with Amazon Q plugin
- [ ] Enterprise IAM setup documented

### Sprint 4: Testing, Polish & Documentation (1 week)

**Goal:** Production-ready release

#### Tasks

| ID | Task | File Path | Hours |
|----|------|-----------|-------|
| AQ-4.1 | Write unit tests for adapter | `tests/adapters/test_amazonq_adapter.py` | 8 |
| AQ-4.2 | Integration test suite | `tests/integration/test_amazonq.py` | 6 |
| AQ-4.3 | Update FRAMEWORK_ROADMAP.md | `docs/FRAMEWORK_ROADMAP.md` | 2 |
| AQ-4.4 | Create quick start guide | `docs/platforms/amazonq-quickstart.md` | 4 |
| AQ-4.5 | Update README with Amazon Q | `README.md` | 2 |
| AQ-4.6 | Final validation & cleanup | All files | 4 |

**Deliverables:**
- Test suite passing
- Complete documentation
- Production-ready adapter

---

## Enterprise Considerations

### IAM Policy Requirements

For enterprise deployments using Amazon Q Developer Pro:

```yaml
# Required IAM permissions for Vibey MCP server
permissions:
  required:
    - q:StartConversation
    - q:SendMessage
    - q:GetConversation
  optional:
    - codeguru-reviewer:*      # For code review features
    - codewhisperer:*          # Legacy CodeWhisperer permissions
    - cloudwatch:PutMetricData # For observability
```

### Security Considerations

1. **MCP Server Sandboxing**
   - Run Vibey MCP server with minimal permissions
   - No AWS credentials in MCP server by default
   - Separate IAM role for AWS integrations

2. **Secrets Management**
   - No secrets in `.amazonq/` generated files
   - Use AWS Secrets Manager for sensitive config
   - Environment variables for local development

3. **Audit Logging**
   - Amazon Q includes user-agent markers in API calls
   - Track Vibey tool usage via CloudTrail
   - Enterprise governance via user-agent filtering

### Multi-Account Setup

For organizations with multiple AWS accounts:

```
Management Account
├── IAM Identity Center
├── Amazon Q Developer Pro subscriptions
│
├── Development Account
│   └── Developer workstations (Amazon Q IDE)
│
├── Staging Account
│   └── CI/CD pipelines (Amazon Q CLI)
│
└── Production Account
    └── No Amazon Q access (security)
```

---

## Feature Mapping

### Vibey to Amazon Q Mapping

| Vibey Feature | Amazon Q Equivalent | Implementation |
|---------------|---------------------|----------------|
| Agents | MCP Tools + Rules | Tools via MCP, context via rules |
| Workflows | MCP Tools | Workflow tools exposed via MCP |
| Quality Gates | Rules + Tests | Rules for guidance, tests via MCP |
| Roadmap | MCP Tools | Full roadmap management via MCP |
| Templates | Rules | Context files from templates |

### Amazon Q Built-in Agents vs Vibey

| Amazon Q Agent | Vibey Equivalent | Integration |
|----------------|------------------|-------------|
| `/dev` | Sprint Planning + Dev agents | Supplement with Vibey context |
| `/doc` | Documentation Engineer | Use Vibey for detailed docs |
| `/test` | Test Engineer | Vibey provides test patterns |
| `/review` | Security Reviewer | Vibey provides security rules |
| `/transform` | (No equivalent) | Amazon Q exclusive |

---

## Risk Assessment

### Low Risk

- **MCP Integration** - Native support, well-documented
- **Rules Generation** - Simple markdown, familiar pattern
- **CLI Support** - Stable API since April 2025

### Medium Risk

- **IDE Plugin MCP** - Less documented than CLI
- **IAM Complexity** - Enterprise setup requires AWS expertise
- **Regional Availability** - Some features US-only

### Mitigation

1. **IDE Testing** - Test VS Code and JetBrains early in Sprint 3
2. **IAM Documentation** - Detailed guides with screenshots
3. **Regional Guidance** - Document availability limitations

---

## Success Criteria

### MVP (End of Sprint 2)

- [ ] `vibey deploy amazonq` works end-to-end
- [ ] MCP server exposes all 46 tools
- [ ] Rules files generated from frontmatter
- [ ] Amazon Q CLI can execute Vibey workflows
- [ ] Zero-drift validation passes

### Full Release (End of Sprint 4)

- [ ] All MVP criteria
- [ ] VS Code and JetBrains integration tested
- [ ] Enterprise IAM setup documented
- [ ] Test suite with 80%+ coverage
- [ ] Quick start and troubleshooting guides
- [ ] FRAMEWORK_ROADMAP.md updated

---

## Dependencies

### Prerequisites

- Vibey MCP server operational (`framework/mcp/server.py`)
- Existing adapter infrastructure (`vibey/adapters/base.py`)
- Tool discovery working (`framework/mcp/discovery/`)

### External Dependencies

- Amazon Q Developer CLI v1.9.0+
- Amazon Q IDE extensions (VS Code, JetBrains)
- AWS IAM Identity Center (for enterprise)

### Blocked By

- None (all prerequisites met)

### Blocks

- Multi-platform unified deployment (needs amazonq target)

---

## References

### Official Documentation

- [What is Amazon Q Developer?](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/what-is.html)
- [Using MCP with Amazon Q Developer](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/qdev-mcp.html)
- [MCP Overview](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/qdev-mcp-overview.html)
- [Identity and Access Management](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/security-iam.html)
- [Installing Amazon Q in IDE](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/q-in-IDE-setup.html)

### AWS Blog Posts

- [Extend Amazon Q Developer CLI with MCP](https://aws.amazon.com/blogs/devops/extend-the-amazon-q-developer-cli-with-mcp/)
- [Use MCP with Amazon Q Developer for context-aware IDE workflows](https://aws.amazon.com/blogs/devops/use-model-context-protocol-with-amazon-q-developer-for-context-aware-ide-workflows/)
- [Amazon Q Developer IDE plugins now support MCP tools](https://aws.amazon.com/about-aws/whats-new/2025/06/amazon-q-developer-ide-plugins-mcp-tools/)

### Related Vibey Documentation

- [Framework Roadmap](docs/FRAMEWORK_ROADMAP.md)
- [MCP Server Implementation](framework/mcp/server.py)
- [Platform Adapters](vibey/adapters/)

---

## Appendix A: File Templates

### `.amazonq/mcp.json` Template

```json
{
  "mcpServers": {
    "vibey": {
      "commandLine": "python -m framework.mcp.server",
      "args": ["--roadmap-root", ".vibey/roadmap"],
      "env": {
        "VIBEY_ROOT": "${workspaceFolder}",
        "PYTHONPATH": "${workspaceFolder}"
      },
      "timeout": 30000
    }
  }
}
```

### `.amazonq/rules/vibey-context.md` Template

```markdown
# Vibey Agent Framework Context

This project uses the Vibey Agent Framework for intelligent workflow management.

## Available Agents

<!-- Auto-generated from framework/agents/*.md frontmatter -->

### Development Agents
- **Backend Engineer** - Build robust backend APIs and services
- **Frontend Engineer** - Build modern, responsive user interfaces
- **Database Specialist** - Design and optimize database schemas

### Quality Agents
- **Test Engineer** - Write comprehensive automated tests
- **Security Reviewer** - Review code for vulnerabilities
- **Performance Engineer** - Optimize application performance

### Planning Agents
- **Sprint Planning** - Plan and track development sprints
- **Researcher** - Research documentation and APIs

## Workflows

Use MCP tools prefixed with `vibey_workflow_` to execute structured workflows.

---
*Generated by Vibey Agent Framework*
```

---

## Appendix B: Testing Checklist

### MCP Server Tests

- [ ] Server starts without errors
- [ ] All 46 tools discoverable
- [ ] Agent tools return content
- [ ] Workflow tools return steps
- [ ] Query tools return roadmap data

### Amazon Q CLI Tests

- [ ] `q chat` discovers Vibey MCP server
- [ ] Tool invocation works from chat
- [ ] Multiple sequential tool calls work
- [ ] Error handling works correctly

### IDE Tests

- [ ] VS Code: MCP server connects
- [ ] VS Code: Tools visible in chat
- [ ] JetBrains: MCP server connects
- [ ] JetBrains: Tools visible in chat

### Generation Tests

- [ ] `vibey deploy amazonq` creates all files
- [ ] Rules files contain agent context
- [ ] Checksums computed correctly
- [ ] `--validate` detects drift
- [ ] `--clean` removes old files

---

*Implementation plan created: 2025-11-23*
*Last updated: 2025-11-23*
