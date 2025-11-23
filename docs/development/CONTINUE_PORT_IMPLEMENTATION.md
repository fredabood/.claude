# Continue.dev Platform Port - Implementation Plan

**Track ID:** `continue-port`
**Status:** Not Started
**Priority:** High
**Estimated Duration:** 3.5 weeks (2 sprints)
**Compatibility Score:** 80%

---

## Executive Summary

Continue.dev is an open-source AI coding assistant platform designed for multi-IDE deployment (VS Code + JetBrains). With native slash command support and context provider APIs, Continue offers excellent integration opportunities for Vibey agents and workflows.

**Key Stats:**
- License: Apache 2.0 (open source)
- IDE Support: VS Code + JetBrains (75%+ of developers)
- MCP Support: Full (future-proof)
- Model Support: 30+ LLM providers

---

## Critical Architecture: Dynamic Generation from Source of Truth

> **All `.continue/` files are GENERATED, never manually edited.**

### Source of Truth Hierarchy

```
SOURCE OF TRUTH (edit these)              GENERATED OUTPUT (never edit)
────────────────────────────              ────────────────────────────
framework/agents/*.md            ───►     .continue/config.yaml (slashCommands section)
framework/workflows/*.md         ───►     .continue/config.yaml (workflows section)
.vibey/config/*.yaml             ───►     .continue/config.yaml (models section)
templates/continue/*.j2          ───►     .continue/contextProviders/
```

### Why This Matters

1. **Prevents Drift**: Generated files always match source definitions
2. **Single Update Point**: Change `framework/agents/web-developer.md` once, regenerate for all platforms
3. **Consistent Behavior**: Same agent behaves identically across Claude Code, Goose, Aider, and Continue
4. **Version Control**: Source of truth is tracked; generated files can be `.gitignore`d

### Regeneration Commands

```bash
# Regenerate all .continue/ files from source
vibey deploy --platform continue

# Force regenerate (clears existing)
vibey deploy --platform continue --force

# Regenerate after framework update
vibey upgrade && vibey deploy --platform continue
```

### .gitignore Recommendation

```gitignore
# Generated platform files (regenerate with `vibey deploy`)
.continue/config.yaml
.continue/contextProviders/

# Keep user customizations if needed
# .continue/models/
```

---

## 1. Platform Architecture

### Core Components

1. **VS Code Extension**
   - TypeScript-based VS Code Extension API implementation
   - Full slash command capability
   - Context provider support
   - Sidebar UI integration

2. **JetBrains Extension**
   - Kotlin-based IntelliJ Platform SDK implementation
   - Full slash command capability
   - Context provider support

3. **Terminal CLI**
   - Standalone CLI tool with TUI and headless modes

4. **Configuration System**
   - `config.yaml` or `config.json` (YAML migration supported)
   - `.continuerc.json` for project-level overrides
   - Modular, extensible structure

---

## 2. Vibey Concept Mapping

| Vibey Concept | Continue Equivalent | Implementation Strategy |
|---------------|---------------------|------------------------|
| **Agents** | Custom Slash Commands | Agent → `/agent-name` command with prompt template |
| **Workflows** | Command Sequences/Recipes | Multi-step slash command chains |
| **Handoff Templates** | Context Providers | Custom context provider API |
| **Quality Gates** | Validation Commands | Implement as slash commands |
| **Config** | `config.yaml` | Native Continue configuration |
| **Deployment** | `.continue/` directory | Standard Continue config location |

---

## 3. Integration Points

### Slash Commands (Primary Integration)

**Vibey Agent → Continue Slash Command:**
```yaml
slashCommands:
  - name: "web-developer"
    description: "Full-stack web development assistant"
    prompt: |
      You are a Web Developer specialized in React and Node.js.
      Your role is to build scalable user interfaces and APIs.

      Guidelines:
      - Follow React best practices
      - Use TypeScript for type safety
      - Write comprehensive tests

      Task: {{ input }}

  - name: "test-engineer"
    description: "Testing and QA specialist"
    prompt: |
      You are a Test Engineer focused on comprehensive testing.
      ...
```

### Context Providers (Workflow Context)

**Custom Context Provider:**
```yaml
contextProviders:
  - name: "vibey-workflow-context"
    type: "custom"
    config:
      workflow_id: "{{ workflow.id }}"
      sprint_context: "{{ sprint.context }}"

  - name: "vibey-quality-gates"
    type: "custom"
    config:
      required_gates: "{{ quality_gates }}"
      threshold_scores: "{{ thresholds }}"
```

### MCP Integration

Continue has native MCP support:
```yaml
mcpServers:
  vibey:
    command: "python"
    args:
      - "-m"
      - "vibey.mcp.server"
    env:
      VIBEY_PROJECT_ROOT: "/path/to/project"
```

---

## 4. Implementation Architecture

### Directory Structure

```
.continue/
├── config.yaml                    # Main Continue configuration
├── models/                        # Model configurations
│   └── default-models.yaml
├── mcpServers/                    # MCP server configs
│   └── vibey-mcp.json            # Optional: Vibey MCP adapter
├── agents/                        # Generated agent configs
│   ├── web-developer.yaml
│   ├── test-engineer.yaml
│   └── ...
└── workflows/                     # Generated workflow templates
    ├── sprint-planning.yaml
    └── ...
```

### Adapter Class

```python
class ContinueAdapter(PlatformAdapter):
    """Continue.dev platform deployment adapter."""

    def get_platform_name(self) -> str:
        return "continue"

    def get_deployment_dir(self, project_root: Path) -> Path:
        return project_root / ".continue"

    def deploy(self, source_dir: Path, config: Any) -> DeploymentResult:
        # 1. Create .continue/ structure
        # 2. Generate config.yaml with slash commands
        # 3. Create context providers
        # 4. Configure MCP servers (optional)
        pass
```

---

## 5. Sprint Plan

### Sprint 1: Continue Adapter & Slash Commands (2 weeks)

#### Task 1: Create ContinueAdapter class (2-3 days)
- Extend `PlatformAdapter` base class
- Implement deployment to `.continue/` directory
- Generate config.yaml from Vibey config

#### Task 2: Agent → Slash Command conversion (2-3 days)
- Convert all 12 agents to slash commands
- Create prompt templates with Jinja2
- Handle agent parameters and context

#### Task 3: Workflow → Command sequence mapping (2 days)
- Map workflow steps to prompt templates
- Implement command chaining logic
- Store workflow definitions in config

#### Task 4: config.yaml template (1-2 days)
- Jinja2 template for main config
- Model configuration section
- Slash command definitions
- Context provider setup

#### Task 5: Unit tests (2 days)
- Test adapter deployment logic
- Validate config generation
- Verify slash command syntax

#### Task 6: VS Code integration testing (1-2 days)
- Deploy to test project
- Verify commands appear in VS Code
- Test command execution

#### Task 7: Documentation start (1 day)
- Architecture overview
- Configuration reference

---

### Sprint 2: Context Providers & Multi-IDE Support (1.5 weeks)

#### Task 1: Vibey context provider implementation (2-3 days)
- Workflow context provider
- Quality gates provider
- Sprint/task context provider

#### Task 2: JetBrains integration testing (2 days)
- Test in IntelliJ IDEA
- Test in PyCharm
- Verify feature parity with VS Code

#### Task 3: MCP server integration (optional) (1-2 days)
- Configure Vibey MCP server in Continue
- Test tool discovery
- Verify agent invocation via MCP

#### Task 4: Integration examples (1-2 days)
- Web-app project example
- API project example
- ML project example

#### Task 5: Complete documentation (1-2 days)
- User guide with screenshots
- Multi-IDE setup instructions
- Troubleshooting guide

---

## 6. Technical Decisions

### Configuration Format: YAML
```yaml
# .continue/config.yaml
models:
  - title: "Claude 3.5 Sonnet"
    provider: "anthropic"
    model: "claude-3-5-sonnet-20241022"

slashCommands:
  - name: "web-developer"
    description: "Full-stack web development"
    prompt: "{{ agent_prompt }}"

contextProviders:
  - name: "vibey-context"
    type: "custom"
```

### Slash Command Structure
```yaml
# Each agent becomes a slash command
- name: "{{ agent.id }}"
  description: "{{ agent.description }}"
  prompt: |
    {{ agent.system_prompt }}

    {{ agent.instructions }}

    Task: {{ input }}
```

### Context Provider Implementation
```typescript
// Continue context provider interface
interface ContextProvider {
  name: string;
  description: string;
  getContext(query: string): Promise<ContextItem[]>;
}

// Vibey implementation reads from .vibey/
class VibeyContextProvider implements ContextProvider {
  async getContext(query: string) {
    // Load sprint, workflow, quality gate context
    return [...];
  }
}
```

---

## 7. Quality Gates

### Gate 1: Comprehensive Testing (100% threshold)
- All journey tests pass
- Platform deployment tests pass
- >95% platform parity

### Gate 2: VS Code Integration Testing (95% threshold)
- Slash commands appear correctly
- Commands execute as expected
- Context providers load data

### Gate 3: JetBrains Integration Testing (90% threshold)
- Works in IntelliJ IDEA
- Works in PyCharm
- Works in WebStorm

### Gate 4: Context Provider API (95% threshold)
- Custom context providers work correctly
- Data loads from .vibey/ directory
- No performance issues

---

## 8. Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Configuration Drift** | High | **Never edit generated files**. All `.continue/` files regenerated from source on each `vibey deploy`. Add generation marker comments. |
| **User Edits Generated Files** | High | Clear warnings in generated files, `.gitignore` generated sections, documentation emphasizing regeneration workflow |
| **Slash command limitations** | Medium | Design workflows as command chains; use context providers for state |
| **Context provider learning curve** | Medium | Provide working examples; comprehensive documentation |
| **Multi-IDE testing complexity** | Medium | Automated test suites; separate CI/CD paths |
| **Continue's rapid development** | Low-Medium | Monitor releases; maintain compatibility layer |

---

## 9. Deliverables Checklist

### Core Implementation
- [ ] `vibey/adapters/continue_dev.py` - ContinueAdapter class
- [ ] `templates/continue/config.yaml.j2` - Main config template
- [ ] `templates/continue/slash-command.yaml.j2` - Command template
- [ ] `templates/continue/context-provider.yaml.j2` - Provider template

### Testing
- [ ] `tests/adapters/test_continue.py` - Unit tests
- [ ] `tests/integration/test_continue_vscode.py` - VS Code tests
- [ ] `tests/integration/test_continue_jetbrains.py` - JetBrains tests

### Documentation
- [ ] `docs/guides/CONTINUE_INTEGRATION.md` - User guide
- [ ] `docs/guides/CONTINUE_CONTEXT_PROVIDERS.md` - Provider guide
- [ ] Example projects (web-app, API, ML)

---

## 10. Success Criteria

1. **Functional Deployment**
   - `vibey deploy --platform continue` creates valid `.continue/` directory
   - All 12 agents available as slash commands
   - Config loads without errors in VS Code and JetBrains

2. **Dynamic Regeneration (Critical)**
   - Running `vibey deploy --platform continue` twice produces identical output
   - Modifying `framework/agents/web-developer.md` and regenerating updates slash command
   - Generated config contains header comment with regeneration instructions
   - Generation timestamp tracked

3. **Multi-IDE Support**
   - Works in VS Code
   - Works in IntelliJ IDEA, PyCharm, WebStorm
   - Feature parity across IDEs

4. **Context Integration**
   - Workflow context accessible via providers
   - Quality gate data available
   - Sprint/task context loads

5. **Documentation**
   - Complete setup guide emphasizing regeneration workflow
   - Clear guidance: "Edit source, not generated"
   - Context provider examples
   - 3+ example projects

---

## References

- [Continue.dev Official Site](https://www.continue.dev/)
- [Continue Documentation](https://docs.continue.dev)
- [Continue GitHub Repository](https://github.com/continuedev/continue)
- [Configuration Reference](https://docs.continue.dev/json-reference)
- [YAML Migration Guide](https://docs.continue.dev/customize/yaml-migration)
- [MCP Integration Guide](https://docs.continue.dev/customize/deep-dives/mcp)

---

**Last Updated:** 2025-11-23
**Author:** Vibey Framework Team
**Architecture Review:** Dynamic generation from source of truth (prevents drift)
