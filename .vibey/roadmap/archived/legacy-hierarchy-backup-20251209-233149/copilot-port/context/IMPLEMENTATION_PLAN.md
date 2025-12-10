# GitHub Copilot Platform Port - Implementation Plan

> **Track ID:** copilot-port
> **Created:** 2025-11-23
> **Status:** Ready to Implement (MCP Support Available)
> **Priority:** HIGH (revised from MEDIUM)

---

## Executive Summary

**Critical Update:** Research reveals that GitHub Copilot **already has MCP support** as of July 2025 - significantly earlier than the Q1-Q2 2026 estimate in the original track definition. This changes the copilot-port track from "blocked" to "ready to implement."

### Key Findings

1. **MCP Support is GA** - Available in VS Code (July 2025), JetBrains, Eclipse, and Xcode (August 2025)
2. **Custom Agents** - `.github/agents/*.md` configuration with MCP server support
3. **Copilot Extensions Deprecated** - GitHub App-based extensions sunset November 10, 2025 in favor of MCP
4. **Copilot Workspace Sunset** - The technical preview ended May 30, 2025; replaced by Agent Mode

### Strategic Opportunity

- **40M+ Users** - Largest AI coding assistant market
- **Enterprise Integration** - GitHub Enterprise support
- **Zero-Drift Architecture** - Existing MCP server reuse
- **Custom Agents** - Native `.github/agents/` integration

---

## Research Findings

### 1. MCP Timeline Analysis

| Date | Milestone | Impact |
|------|-----------|--------|
| May 2025 | MCP Public Preview | Initial testing available |
| July 14, 2025 | VS Code GA | MCP support generally available |
| August 13, 2025 | JetBrains/Eclipse/Xcode GA | Multi-IDE support |
| September 24, 2025 | Extensions Deprecation Announced | MCP becomes primary integration method |
| October 28, 2025 | Custom Agents Released | `.github/agents/` configuration |
| November 10, 2025 | Extensions Sunset | MCP is now the only integration method |

**Conclusion:** MCP support is fully available. The copilot-port track blocker is resolved.

### 2. GitHub Copilot Architecture (Current)

```
                    GitHub Copilot Ecosystem
                    ========================

    ┌─────────────────────────────────────────────────────────┐
    │                    Copilot Chat                         │
    │   @workspace  @terminal  @vscode  @vibey (custom)       │
    └─────────────────────────────────┬───────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │         Agent Mode                │
                    │  (Multi-step autonomous coding)   │
                    │  - Reads codebase                 │
                    │  - Proposes edits                 │
                    │  - Runs terminal commands         │
                    │  - Auto-corrects from errors      │
                    └─────────────────┬─────────────────┘
                                      │
    ┌─────────────────────────────────┴───────────────────────┐
    │                    MCP Integration                       │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
    │  │  Built-in    │  │  Custom MCP  │  │   Remote     │   │
    │  │  (github,    │  │  Servers     │  │   MCP        │   │
    │  │   playwright)│  │  (stdio)     │  │  (http/sse)  │   │
    │  └──────────────┘  └──────────────┘  └──────────────┘   │
    └─────────────────────────────────────────────────────────┘
                                      │
    ┌─────────────────────────────────┴───────────────────────┐
    │                 Custom Agents                            │
    │         .github/agents/*.md                              │
    │  - Persona definitions                                   │
    │  - Tool selections                                       │
    │  - MCP server configurations                             │
    │  - Enterprise standardization                            │
    └─────────────────────────────────────────────────────────┘
```

### 3. Custom Agents Configuration Format

GitHub Copilot custom agents use YAML frontmatter in Markdown files:

```yaml
---
name: vibey-planner
description: |
  Vibey Sprint Planning Agent - Creates implementation plans,
  breaks down features into tasks, and manages sprint state.
target: github-copilot
tools:
  - read
  - edit
  - search
  - shell
  - custom-agent
  - vibey/vibey_sprint_planning
  - vibey/vibey_roadmap_status
  - vibey/vibey_query_task
mcp-servers:
  vibey:
    type: local
    command: python
    args:
      - -m
      - framework.mcp.server
    tools: ["*"]
    env:
      VIBEY_ROADMAP_ROOT: .vibey/roadmap
---

# Vibey Sprint Planning Agent

You are a specialized sprint planning agent that helps developers
organize and track their development work...
```

### 4. MCP Limitations in Copilot

| Feature | Support | Notes |
|---------|---------|-------|
| Tools | YES | Primary integration method |
| Resources | NO | Not supported by coding agent |
| Prompts | NO | Not supported by coding agent |
| OAuth Remote | NO | Remote servers with OAuth not supported |
| Local Stdio | YES | Full support |
| Remote HTTP | YES | Without OAuth |
| Remote SSE | YES | Without OAuth |

### 5. Key Differences from Original Plan

| Original Assumption | Actual State | Impact |
|---------------------|--------------|--------|
| MCP support Q1-Q2 2026 | Available July 2025 | Track unblocked |
| Copilot Workspace integration | Workspace sunset May 2025 | Use Agent Mode instead |
| @vibey chat participant | Custom agents via `.github/agents/` | Simpler implementation |
| Copilot Extensions | Deprecated November 2025 | MCP is the only path |

---

## Architecture Decisions

### Decision 1: Reuse Existing MCP Server

**Context:** Vibey already has a complete MCP server with 46 tools at `framework/mcp/server.py`.

**Decision:** Reuse the existing MCP server without modification.

**Rationale:**
- Zero code duplication
- Already tested with Claude Code and Goose
- Dynamic tool discovery from frontmatter
- Consistent behavior across all MCP clients

### Decision 2: Custom Agent Profiles via Adapter

**Context:** Copilot uses `.github/agents/*.md` for custom agent configuration.

**Decision:** Create a `CopilotAdapter` that generates custom agent profiles from Vibey agent frontmatter.

**Rationale:**
- Zero-drift architecture (single source of truth)
- Automatic generation ensures consistency
- Follows established adapter pattern (see `GooseAdapter`)

### Decision 3: No Workspace Integration

**Context:** Copilot Workspace (technical preview) was sunset May 30, 2025.

**Decision:** Focus on Agent Mode integration instead.

**Rationale:**
- Workspace no longer exists
- Agent Mode is the current multi-step workflow solution
- MCP tools work seamlessly with Agent Mode

### Decision 4: Repository-Level Configuration

**Context:** Copilot supports configuration at repository, organization, and enterprise levels.

**Decision:** Focus on repository-level configuration first (`.github/agents/`).

**Rationale:**
- Simplest integration path
- Works with all Copilot tiers
- Can expand to org/enterprise later

---

## Integration Approach

### Phase 1: MCP Server Configuration (Sprint 1)

Configure Vibey MCP server for use with Copilot:

**Repository Settings Configuration:**
```json
{
  "mcpServers": {
    "vibey": {
      "type": "local",
      "command": "python",
      "args": ["-m", "framework.mcp.server"],
      "tools": ["*"]
    }
  }
}
```

**Allowlist Recommended Tools:**
```json
{
  "tools": [
    "vibey_roadmap_status",
    "vibey_query_sprint",
    "vibey_query_task",
    "vibey_start_task",
    "vibey_complete_task",
    "vibey_web_developer",
    "vibey_test_engineer",
    "vibey_documentation_engineer"
  ]
}
```

### Phase 2: Custom Agent Profiles (Sprint 1)

Generate `.github/agents/` profiles from Vibey agent frontmatter:

**Example: `.github/agents/vibey-web-developer.md`**
```yaml
---
name: vibey-web-developer
description: |
  Build modern, responsive user interfaces using React, Vue,
  or vanilla JavaScript. Specializes in component architecture,
  state management, and frontend best practices.
tools:
  - read
  - edit
  - search
  - shell
  - vibey/vibey_web_developer
  - vibey/vibey_frontend_engineer
mcp-servers:
  vibey:
    type: local
    command: python
    args: ["-m", "framework.mcp.server"]
    tools:
      - vibey_web_developer
      - vibey_frontend_engineer
      - vibey_test_engineer
---

# Vibey Web Developer

[Generated from framework/agents/development/web-developer.md]
```

### Phase 3: CopilotAdapter Implementation (Sprint 1)

```python
class CopilotAdapter(BaseAdapter):
    """
    Adapter for GitHub Copilot platform.

    Generates:
    - .github/agents/*.md (custom agent profiles)
    - Repository MCP configuration
    """

    platform_name = "copilot"
    platform_display_name = "GitHub Copilot"

    def translate_agent(self, agent: AgentDefinition) -> str:
        """Convert Vibey agent to Copilot custom agent profile."""
        frontmatter = {
            "name": f"vibey-{agent.id}",
            "description": agent.description,
            "tools": self._get_agent_tools(agent),
            "mcp-servers": {
                "vibey": {
                    "type": "local",
                    "command": "python",
                    "args": ["-m", "framework.mcp.server"],
                    "tools": [f"vibey_{agent.id.replace('-', '_')}"]
                }
            }
        }
        return self._render_agent_profile(frontmatter, agent)

    def export(self, output_dir: Path) -> ExportResult:
        """Export to .github/agents/ directory."""
        agents_dir = output_dir / ".github" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        files = []
        for agent in self.registry.agents:
            profile = self.translate_agent(agent)
            path = agents_dir / f"vibey-{agent.id}.md"
            path.write_text(profile)
            files.append(path)

        return ExportResult(platform="copilot", files=files)
```

### Phase 4: Testing & Quality Gates (Sprint 2)

Testing strategy:
1. **Unit Tests** - Adapter generates valid YAML frontmatter
2. **Schema Validation** - Generated profiles match Copilot schema
3. **Integration Tests** - MCP server responds to Copilot tool calls
4. **E2E Tests** - Complete workflow with real Copilot instance

---

## Sprint Structure

### Sprint 1: MCP Integration & Custom Agents (3 weeks)

| Task | Description | Duration |
|------|-------------|----------|
| 1.1 | Research validation - verify MCP configuration format | 2 days |
| 1.2 | Create CopilotAdapter class | 3 days |
| 1.3 | Generate custom agent profiles from frontmatter | 3 days |
| 1.4 | Create repository MCP configuration generator | 2 days |
| 1.5 | Implement `vibey export --platform copilot` | 2 days |
| 1.6 | Unit tests for adapter | 2 days |
| 1.7 | Documentation: Copilot integration guide | 1 day |

**Deliverables:**
- `vibey/adapters/copilot/adapter.py`
- `vibey/adapters/copilot/agent_generator.py`
- `.github/agents/` generation capability
- Unit test suite

### Sprint 2: Testing, Enterprise & Documentation (3 weeks)

| Task | Description | Duration |
|------|-------------|----------|
| 2.1 | Integration tests with Copilot CLI | 3 days |
| 2.2 | E2E tests with VS Code Copilot | 3 days |
| 2.3 | Organization-level configuration guide | 2 days |
| 2.4 | Enterprise deployment documentation | 2 days |
| 2.5 | Migration guide for Copilot users | 2 days |
| 2.6 | Quality gate validation | 2 days |
| 2.7 | Performance benchmarks | 1 day |

**Deliverables:**
- Integration test suite
- E2E test suite
- `docs/platforms/copilot/` documentation
- Enterprise deployment guide
- Migration guide

---

## Dependency Tracking Plan

### Internal Dependencies

| Dependency | Status | Impact |
|------------|--------|--------|
| MCP Server Track | COMPLETED | Vibey MCP server available |
| Goose Port Track | COMPLETED | Adapter pattern established |
| Testing System | COMPLETED | Test infrastructure ready |

### External Dependencies

| Dependency | Status | Tracking Method |
|------------|--------|-----------------|
| Copilot MCP Support | AVAILABLE (GA) | N/A - resolved |
| Custom Agents Feature | AVAILABLE (GA) | N/A - resolved |
| Copilot Workspace | SUNSET | N/A - not using |

---

## Quality Gates

### Gate 1: MCP Integration (100% required)

- [ ] All 46 Vibey MCP tools accessible from Copilot
- [ ] Tool discovery works correctly
- [ ] Tool invocation returns expected results
- [ ] Error handling works correctly

### Gate 2: Custom Agents (95% required)

- [ ] All 19 Vibey agents exported as Copilot custom agents
- [ ] YAML frontmatter validates against Copilot schema
- [ ] Agent descriptions render correctly
- [ ] Tool permissions work as expected

### Gate 3: Documentation (90% required)

- [ ] Integration guide complete
- [ ] Enterprise deployment guide complete
- [ ] Migration guide complete
- [ ] Troubleshooting guide complete

---

## Risk Assessment

### Low Risk

| Risk | Mitigation |
|------|------------|
| Minor schema differences | Validate against official docs |
| Tool naming conflicts | Use `vibey_` prefix consistently |

### Medium Risk

| Risk | Mitigation |
|------|------------|
| 128-tool limit per request | Allowlist recommended tools |
| Enterprise approval delays | Provide org-level docs |

### High Risk

| Risk | Mitigation |
|------|------------|
| None identified | - |

---

## Recommended Track Updates

Based on this research, the `copilot-port/track.yaml` should be updated:

```yaml
track:
  id: copilot-port
  name: GitHub Copilot Platform Port
  status: not_started  # Change from blocked
  blocked: false       # Remove blocker
  priority: high       # Upgrade from medium

  # Update external dependency to reflect resolved status
  dependencies:
  - type: external
    target_id: copilot-mcp-support
    target_status: available
    reason: GitHub Copilot MCP support available since July 2025
    optional: false
    resolved: true  # Mark as resolved

  metadata:
    notes: |
      MCP SUPPORT NOW AVAILABLE (November 2025)

      Research update: GitHub Copilot MCP support went GA July 14, 2025.
      Custom agents feature released October 28, 2025.
      This track is now unblocked and ready to implement.

      See: .vibey/roadmap/copilot-port/context/IMPLEMENTATION_PLAN.md
```

---

## Sources

### Primary Research

- [MCP Support GA in VS Code](https://github.blog/changelog/2025-07-14-model-context-protocol-mcp-support-in-vs-code-is-generally-available/)
- [MCP Support for JetBrains, Eclipse, Xcode](https://github.blog/changelog/2025-08-13-model-context-protocol-mcp-support-for-jetbrains-eclipse-and-xcode-is-now-generally-available/)
- [Copilot Extensions Deprecation](https://github.blog/changelog/2025-09-24-deprecate-github-copilot-extensions-github-apps/)
- [Custom Agents Release](https://github.blog/changelog/2025-10-28-custom-agents-for-github-copilot/)
- [Custom Agents Configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- [Extending Copilot with MCP](https://docs.github.com/copilot/how-tos/agents/copilot-coding-agent/extending-copilot-coding-agent-with-mcp)
- [MCP and Coding Agent](https://docs.github.com/en/copilot/concepts/agents/coding-agent/mcp-and-coding-agent)

### Secondary Research

- [VS Code Chat Participant API](https://code.visualstudio.com/api/extension-guides/ai/chat)
- [About Building Copilot Extensions](https://docs.github.com/en/copilot/concepts/extensions/build-extensions)
- [Copilot Workspace (sunset)](https://githubnext.com/projects/copilot-workspace)
- [Agent Mode Introduction](https://code.visualstudio.com/blogs/2025/02/24/introducing-copilot-agent-mode)

---

## Next Steps

1. **Update track.yaml** - Remove blocked status, upgrade priority
2. **Begin Sprint 1** - MCP integration and custom agents
3. **Create adapter scaffolding** - `vibey/adapters/copilot/`
4. **Implement agent generator** - Frontmatter to Copilot profile conversion

---

*Document generated: 2025-11-23*
*Vibey Framework Version: 2.5.0+*
