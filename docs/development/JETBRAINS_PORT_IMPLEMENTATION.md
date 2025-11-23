# JetBrains AI Assistant Platform Port - Implementation Plan

**Track ID:** `jetbrains-port`
**Status:** Not Started
**Priority:** Medium
**Estimated Duration:** 3 weeks (2 sprints) - Reduced due to shared MCP architecture
**Compatibility Score:** 80-85%

---

## Executive Summary

JetBrains AI Assistant offers native MCP (Model Context Protocol) support - the same protocol as Claude Code - enabling seamless integration of Vibey agents and workflows. The platform hosts multiple AI agents (Junie, Claude Agent) in a multi-agent ecosystem, perfect for Vibey's distributed agent architecture.

**Key Decision:** Use shared Vibey MCP server from goose-port instead of building separate implementation. This reduces effort from 5.5 weeks to 3 weeks.

**Key Stats:**
- IDE Coverage: 8+ IDEs (IntelliJ, PyCharm, WebStorm, GoLand, etc.)
- Market Reach: 20M+ professional developers
- MCP Support: Native (same as Claude Code!)
- Multi-Agent: Junie + Claude Agent + AI Assistant

---

## Critical Architecture: Dynamic Generation from Source of Truth

> **All `.junie/` and `.idea/` configuration files are GENERATED, never manually edited.**

### Source of Truth Hierarchy

```
SOURCE OF TRUTH (edit these)              GENERATED OUTPUT (never edit)
────────────────────────────              ────────────────────────────
framework/agents/*.md            ───►     MCP tools (via shared server)
framework/workflows/*.md         ───►     MCP resources (via shared server)
.vibey/config/*.yaml             ───►     .junie/guidelines.md
templates/jetbrains/*.j2         ───►     .junie/mcp.json, .idea/vibey-config.xml
```

### Why This Matters

1. **Prevents Drift**: Generated files always match source definitions
2. **Single Update Point**: Change `framework/agents/web-developer.md` once, all MCP clients see updated tool
3. **Consistent Behavior**: Same agent behaves identically across Claude Code, Goose, Aider, Continue, Windsurf, and JetBrains
4. **Version Control**: Source of truth is tracked; generated config files can be `.gitignore`d

### Regeneration Commands

```bash
# Regenerate all .junie/ and .idea/ files from source
vibey deploy --platform jetbrains

# Force regenerate (clears existing)
vibey deploy --platform jetbrains --force

# Regenerate after framework update
vibey upgrade && vibey deploy --platform jetbrains
```

### .gitignore Recommendation

```gitignore
# Generated platform files (regenerate with `vibey deploy`)
.junie/mcp.json
.junie/guidelines.md
.idea/vibey-config.xml

# Keep IDE settings
# .idea/workspace.xml
```

---

## 1. Platform Architecture

### Core Components

1. **JetBrains AI Assistant**
   - IDE-native AI feature (plugin-based)
   - Available across all JetBrains IDEs
   - Cloud-hosted LLMs by default (AWS Bedrock)
   - Custom local model support

2. **Junie Agent**
   - JetBrains' first-party agentic AI
   - Autonomous task planning and execution
   - Guidelines system (`.junie/guidelines.md`)
   - MCP support via `.junie/mcp.json`

3. **Claude Agent (Sept 2025)**
   - Built on Anthropic's Agent SDK
   - Runs natively in JetBrains AI Chat
   - Accesses IDE via MCP server
   - Included in JetBrains AI subscription

### MCP Integration Points

**AI Assistant MCP Client (v2025.1+):**
- Settings → Tools → AI Assistant → Model Context Protocol (MCP)
- Transport: STDIO only (subprocess-based)

**Junie MCP Configuration (v2025.2+):**
- Global: `~/.junie/mcp.json`
- Project: `.junie/mcp/` directory

**JetBrains IDE as MCP Server (v2025.2+):**
- IDEs can expose MCP server interface
- External clients: Claude Desktop, Claude Code, Cursor, VS Code

---

## 2. Vibey Concept Mapping

| Vibey Component | JetBrains Equivalent | Integration Method |
|-----------------|---------------------|-------------------|
| **Agents** | MCP tools | MCP server tools (shared from goose-port) |
| **Workflows** | MCP resources + prompts | MCP resources + Prompt Library |
| **Config** | `.idea/vibey-config.xml` or `.junie/` | Direct file reference |
| **Quality Gates** | MCP validators | Via MCP server |
| **Agent Instructions** | `.junie/guidelines.md` | Guidelines file |
| **Prompts/Context** | Prompt Library + AI Chat | Custom prompts + @file/@folder refs |

---

## 3. Simplified Architecture (Shared MCP)

### Key Insight: No Custom MCP Server Needed!

The goose-port track provides a shared Vibey MCP server with dynamic tool discovery. JetBrains port only needs IDE configuration.

```
goose-port provides:
├── vibey/mcp/server.py (shared MCP server)
├── Dynamic agent tool discovery
├── Dynamic workflow tool discovery
└── Quality gate validation tools

jetbrains-port provides:
├── .junie/mcp.json (MCP server configuration)
├── .junie/guidelines.md (agent context)
├── .idea/ai/ directory structure
└── Multi-IDE testing and documentation
```

### Directory Structure

```
project/
├── .idea/
│   ├── workspace.xml
│   └── vibey-config.xml      # Vibey IDE integration config
├── .junie/
│   ├── mcp.json              # MCP server configuration
│   ├── guidelines.md         # Vibey coding conventions
│   └── mcp/
│       └── vibey-server.json # Project-level MCP config
└── .vibey/
    ├── config/
    │   ├── project.yaml
    │   ├── framework.yaml
    │   ├── agents.yaml
    │   └── quality-gates.yaml
    └── roadmap/
```

---

## 4. Configuration Templates

### `.junie/mcp.json`

```json
{
  "mcpServers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "vibey.mcp.server"],
      "env": {
        "VIBEY_CONFIG_PATH": ".vibey/config",
        "VIBEY_PROJECT_TYPE": "web-app"
      }
    }
  }
}
```

### `.junie/guidelines.md`

```markdown
# Vibey Framework Guidelines

## Project Context
This project uses the Vibey Agent Framework for AI-assisted development.

## Available Agents
- **web-developer** - Full-stack web development
- **test-engineer** - Testing and QA specialist
- **security-reviewer** - Security audits
- **performance-engineer** - Performance optimization

## Workflows
- **feature-development** - End-to-end feature implementation
- **sprint-planning** - Sprint planning and task breakdown
- **security-audit** - Comprehensive security review

## Quality Gates
- Security threshold: 90%
- Testing threshold: 80%
- Documentation threshold: 75%

## Usage
All Vibey agents and workflows are available as MCP tools.
Use the AI Assistant or Junie to invoke them.
```

### `.idea/vibey-config.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="VibeyFramework">
    <option name="configPath" value=".vibey/config" />
    <option name="mcpServerEnabled" value="true" />
    <option name="agentMode" value="balanced" />
    <option name="projectType" value="web-app" />
  </component>
</project>
```

---

## 5. Sprint Plan

### Sprint 1: MCP Configuration & IDE Setup (1.5 weeks)

#### Task 1: Research JetBrains AI MCP format (1 day)
- Document MCP server registration format
- Identify configuration file locations
- Understand AI Assistant vs Junie differences

#### Task 2: Create .junie/ directory structure template (1-2 days)
- `mcp.json` template with Jinja2
- `guidelines.md` template
- Project-level `mcp/vibey-server.json`

#### Task 3: Create .idea/ai/ configuration (1 day)
- `vibey-config.xml` template
- AI settings integration

#### Task 4: JetBrainsAdapter class (2-3 days)
- Extend `PlatformAdapter` base class
- Generate all configuration files
- Handle multi-IDE differences

#### Task 5: Test MCP server connection (1-2 days)
- Test in IntelliJ IDEA
- Verify tool discovery works
- Debug connection issues

#### Task 6: Verify Vibey tools appear (1 day)
- All agents visible as tools
- All workflows visible as tools
- Quality gates accessible

---

### Sprint 2: Multi-IDE Testing & Documentation (1.5 weeks)

#### Task 1: Test in PyCharm (1 day)
- Python-specific workflows
- Verify tool execution
- Document any differences

#### Task 2: Test in WebStorm (1 day)
- JavaScript/TypeScript workflows
- Frontend agent testing
- Document any differences

#### Task 3: Test in GoLand (1 day)
- Go-specific workflows
- Backend agent testing
- Document any differences

#### Task 4: Test multi-agent coordination (1-2 days)
- Junie + Vibey agents
- Claude Agent + Vibey agents
- Coordination patterns

#### Task 5: Create JetBrains integration guide (1-2 days)
- Setup instructions for each IDE
- Configuration reference
- Troubleshooting guide

#### Task 6: Create IDE-specific examples (1-2 days)
- IntelliJ/Java example
- PyCharm/Python example
- WebStorm/TypeScript example

---

## 6. Technical Decisions

### No Custom Plugin Required!
Vibey does NOT need to create a custom JetBrains plugin. Instead:
- Use MCP server (Python) → JetBrains MCP client (built-in)
- Use guidelines system (`.junie/guidelines.md`)
- Use custom prompts (Prompt Library)

This dramatically reduces implementation complexity!

### Shared MCP Server Architecture
```
Vibey MCP Server (from goose-port)
        ↓
    Exposes as MCP Tools:
    - web-developer (tool)
    - test-engineer (tool)
    - security-auditor (tool)
    - workflows (resources)
    - quality-gates (prompts)
        ↓
    IDE Configuration:
    ~/.junie/mcp.json or
    .junie/mcp/vibey-server.json
        ↓
    Available in:
    - Junie (as tools)
    - Claude Agent (as tools)
    - AI Assistant (via MCP)
```

### IDE Compatibility
All JetBrains IDEs share the same configuration format:
- IntelliJ IDEA (Java, Kotlin, Scala)
- PyCharm (Python)
- WebStorm (JavaScript, TypeScript)
- GoLand (Go)
- PhpStorm (PHP)
- RustRover (Rust)
- RubyMine (Ruby)
- CLion (C, C++)

---

## 7. Quality Gates

### Gate 1: MCP Server Integration (95% threshold)
- Vibey MCP server works with JetBrains AI
- Agents exposed as tools
- Workflows exposed as resources
- Error handling robust
- STDIO communication stable

### Gate 2: Multi-IDE Testing (90% threshold)
- Works in IntelliJ IDEA
- Works in PyCharm
- Works in WebStorm
- Works in GoLand
- Configuration consistent across IDEs

### Gate 3: Enterprise Security (95% threshold)
- No hardcoded credentials
- Environment-based config
- Audit logging available
- On-premise deployment possible

---

## 8. Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Configuration Drift** | High | **Never edit generated files**. All `.junie/` and `.idea/` files regenerated from source on each `vibey deploy`. |
| **User Edits Generated Files** | High | Clear warnings in generated files, `.gitignore` generated configs, documentation emphasizing regeneration workflow |
| **MCP Transport Limitation (STDIO only)** | Medium | Implement robust error handling; plan HTTP workaround for future |
| **Multi-IDE Testing Matrix** | Medium | Create automated test harness; use CI/CD |
| **Enterprise Security Audit** | Medium | Early security review; follow JetBrains guidelines |
| **Agent Coordination Complexity** | Medium | Start simple; iterate based on Junie API maturity |
| **IDE Version Compatibility** | Low | Support 2023.3+; document version matrix |

---

## 9. Deliverables Checklist

### Core Implementation
- [ ] `vibey/adapters/jetbrains.py` - JetBrainsAdapter class
- [ ] `templates/jetbrains/mcp.json.j2` - MCP config template
- [ ] `templates/jetbrains/guidelines.md.j2` - Guidelines template
- [ ] `templates/jetbrains/vibey-config.xml.j2` - IDE config template

### Testing
- [ ] `tests/adapters/test_jetbrains.py` - Unit tests
- [ ] `tests/integration/test_jetbrains_intellij.py` - IntelliJ tests
- [ ] `tests/integration/test_jetbrains_pycharm.py` - PyCharm tests
- [ ] `tests/integration/test_jetbrains_webstorm.py` - WebStorm tests

### Documentation
- [ ] `docs/guides/JETBRAINS_INTEGRATION.md` - User guide
- [ ] `docs/guides/JETBRAINS_MCP_SETUP.md` - MCP setup guide
- [ ] IDE-specific examples (Java, Python, TypeScript, Go)

---

## 10. Success Criteria

1. **Functional Deployment**
   - `vibey deploy --platform jetbrains` creates valid configuration
   - MCP server connects from JetBrains AI
   - All Vibey tools visible in AI Assistant/Junie

2. **Dynamic Regeneration (Critical)**
   - Running `vibey deploy --platform jetbrains` twice produces identical output
   - Modifying `framework/agents/web-developer.md` and restarting MCP server shows updated tool
   - Generated config files contain "DO NOT EDIT - Generated by Vibey" comments
   - Generation timestamp tracked

3. **Multi-IDE Support**
   - Works in IntelliJ IDEA, PyCharm, WebStorm, GoLand
   - Configuration portable across IDEs
   - No IDE-specific bugs

4. **Multi-Agent Integration**
   - Works with Junie
   - Works with Claude Agent
   - Coordination patterns documented

5. **Enterprise Ready**
   - Security requirements met
   - On-premise deployment possible
   - Documentation emphasizing regeneration workflow

---

## 11. Dependencies

### Required (Blocking)
- **goose-port** (completed) - Provides shared MCP server with dynamic tool discovery
- **testing-system** (completed) - Test infrastructure
- **claude-port** (completed) - Reference implementation

### Benefits of Shared Architecture
1. **Reduced Effort:** 3 weeks instead of 5.5 weeks
2. **Consistency:** Same MCP server across all platforms
3. **Maintainability:** Single codebase for MCP tools
4. **Testing:** Shared test infrastructure

---

## References

- [AI Assistant in JetBrains IDEs](https://www.jetbrains.com/help/idea/ai-assistant-in-jetbrains-ides.html)
- [Model Context Protocol (MCP)](https://www.jetbrains.com/help/ai-assistant/mcp.html)
- [Introducing Claude Agent](https://blog.jetbrains.com/ai/2025/09/introducing-claude-agent-in-jetbrains-ides/)
- [Getting started with Junie](https://www.jetbrains.com/help/junie/get-started-with-junie.html)
- [Junie Guidelines](https://www.jetbrains.com/help/junie/customize-guidelines.html)
- [Junie MCP Settings](https://www.jetbrains.com/help/junie/mcp-settings.html)

---

**Last Updated:** 2025-11-23
**Author:** Vibey Framework Team
**Architecture Review:** Dynamic generation from source of truth (prevents drift)
