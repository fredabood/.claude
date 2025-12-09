# JetBrains AI Assistant Port - Comprehensive Implementation Plan

**Track ID:** `jetbrains-port`
**Created:** 2025-11-23
**Status:** Ready to Build
**Priority:** Medium
**Estimated Duration:** 2 weeks (reduced due to MCP reuse)
**Compatibility Score:** 85-90% (excellent MCP support)

---

## Executive Summary

JetBrains AI Assistant provides native MCP (Model Context Protocol) support, identical to the protocol used by Claude Code. This enables **direct reuse of our existing MCP server** (`framework/mcp/server.py`) with minimal adapter work.

**Key Insight:** Unlike other platform ports that require significant adaptation, the JetBrains port is primarily a **configuration generation** task. The MCP server already exists and works.

**Effort Comparison:**
| Platform | Custom Server | Adapter Work | Total Effort |
|----------|---------------|--------------|--------------|
| Claude Code | No (MCP) | Minimal | 1 week |
| Goose | Partial | Medium | 3 weeks |
| Aider | No (MCP) | Medium | 2 weeks |
| **JetBrains** | **No (MCP)** | **Config generation** | **2 weeks** |

---

## Research Findings

### 1. JetBrains MCP Support (Verified)

**Official Documentation Sources:**
- [JetBrains AI Assistant MCP Documentation](https://www.jetbrains.com/help/ai-assistant/mcp.html)
- [Configure an MCP Server](https://www.jetbrains.com/help/ai-assistant/configure-an-mcp-server.html)
- [IntelliJ IDEA 2025.1 MCP Support Blog](https://blog.jetbrains.com/idea/2025/05/intellij-idea-2025-1-model-context-protocol/)
- [JetBrains MCP GitHub Repository](https://github.com/JetBrains/mcp-jetbrains)

**Key Facts:**
1. **Transport:** STDIO only (subprocess-based) - matches our server
2. **Version Support:** AI Assistant 2025.1+ (all current IDEs)
3. **Configuration Location:** Settings > Tools > AI Assistant > Model Context Protocol (MCP)
4. **File Storage:** `~/Library/Application Support/JetBrains/<IDE>2025.x/options/llm.mcpServers.xml` (macOS)
5. **JSON Support:** Can configure via JSON in settings dialog

### 2. Configuration Formats

**MCP Server JSON Format (Standard):**
```json
{
  "mcpServers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "framework.mcp.server"],
      "env": {
        "VIBEY_PROJECT_ROOT": "${PROJECT_ROOT}"
      }
    }
  }
}
```

**Junie Configuration (`.junie/mcp.json`):**
```json
{
  "mcpServers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "framework.mcp.server"],
      "env": {
        "VIBEY_CONFIG_PATH": ".vibey/config"
      }
    }
  }
}
```

### 3. AI Assistant Rules System (`.aiassistant/rules/`)

**Discovery:** JetBrains has a rules system similar to Claude Code's CLAUDE.md:
- **Location:** `.aiassistant/rules/*.md`
- **Format:** Markdown files
- **Purpose:** Project-specific guidelines for AI responses
- **Usage:** Rules can be referenced via `@rule:` in chat

This provides a natural place for Vibey context.

### 4. Multi-IDE Coverage

All JetBrains IDEs share identical MCP configuration:
- IntelliJ IDEA (Java, Kotlin, Scala)
- PyCharm (Python)
- WebStorm (JavaScript, TypeScript)
- GoLand (Go)
- PhpStorm (PHP)
- RustRover (Rust)
- RubyMine (Ruby)
- CLion (C, C++)
- Android Studio (Android)

**Market Reach:** 20M+ professional developers

---

## Architecture Decisions

### Decision 1: Direct MCP Server Reuse

**Decision:** Reuse existing MCP server at `framework/mcp/server.py` without modification.

**Rationale:**
- Server already implements STDIO transport (required by JetBrains)
- Dynamic tool discovery from YAML frontmatter already works
- 46 tools already registered
- Zero additional development needed for server

**Implementation:**
```python
# JetBrains adapter just generates config pointing to existing server
mcp_config = {
    "mcpServers": {
        "vibey": {
            "command": sys.executable,
            "args": ["-m", "framework.mcp.server"],
            "env": {"VIBEY_PROJECT_ROOT": str(project_root)}
        }
    }
}
```

### Decision 2: Zero-Drift Config Generation

**Decision:** Generate all JetBrains config files from `.vibey/` source of truth.

**Source Files:**
- `framework/agents/*.md` (YAML frontmatter) -> MCP tools
- `framework/workflows/*.md` (YAML frontmatter) -> MCP resources
- `.vibey/config/*.yaml` -> Project context

**Generated Files:**
- `.junie/mcp.json` - MCP server configuration
- `.aiassistant/rules/vibey-context.md` - Project guidelines
- `.idea/vibey-config.xml` - IDE integration (optional)

**Checksums:** Each generated file includes a checksum for drift detection:
```markdown
<!-- vibey:checksum:sha256:abc123... -->
<!-- DO NOT EDIT - Regenerate with: vibey deploy --platform jetbrains -->
```

### Decision 3: Minimal Adapter Implementation

**Decision:** Create a thin `JetBrainsAdapter` that extends `PlatformAdapter` base class.

**Responsibilities:**
1. Generate `.junie/mcp.json`
2. Generate `.aiassistant/rules/vibey-context.md`
3. Optionally generate `.idea/vibey-config.xml`
4. Validate deployment

**NOT Responsible For:**
- MCP server implementation (reuse existing)
- Tool discovery (reuse existing `ToolDiscovery`)
- Agent definitions (parsed from frontmatter)
- Workflow definitions (parsed from frontmatter)

---

## File Structure

### Generated Output (JetBrains Project)

```
project/
├── .aiassistant/
│   └── rules/
│       └── vibey-context.md     # Generated: Project context for AI
├── .junie/
│   └── mcp.json                 # Generated: MCP server config
├── .idea/
│   └── vibey-config.xml         # Generated (optional): IDE config
└── .vibey/
    ├── config/                  # Source: User config
    ├── roadmap/                 # Source: Roadmap data
    └── ...
```

### Vibey Framework Files (New)

```
vibey/
├── vibey/adapters/
│   └── jetbrains.py             # NEW: JetBrainsAdapter class
├── templates/jetbrains/
│   ├── mcp.json.j2              # NEW: MCP config template
│   ├── vibey-context.md.j2      # NEW: Rules template
│   └── vibey-config.xml.j2      # NEW: IDE config template
├── tests/adapters/
│   └── test_jetbrains.py        # NEW: Unit tests
└── docs/guides/
    └── JETBRAINS_INTEGRATION.md # NEW: User guide
```

---

## Implementation Plan

### Sprint 1: Core Adapter (1 week)

#### Task 1.1: Create JetBrainsAdapter Class
**File:** `vibey/adapters/jetbrains.py`
**Effort:** 4 hours
**Dependencies:** None

```python
class JetBrainsAdapter(PlatformAdapter):
    """JetBrains AI Assistant platform adapter."""

    def get_platform_name(self) -> str:
        return "jetbrains"

    def get_deployment_dir(self, project_root: Path) -> Path:
        return project_root / ".junie"  # Primary config location

    def deploy(self, source_dir: Path, config: Any, ...) -> DeploymentResult:
        # 1. Generate .junie/mcp.json
        # 2. Generate .aiassistant/rules/vibey-context.md
        # 3. Optionally generate .idea/vibey-config.xml
        # 4. Validate deployment
        pass
```

#### Task 1.2: Create MCP Config Template
**File:** `templates/jetbrains/mcp.json.j2`
**Effort:** 2 hours
**Dependencies:** None

```jinja2
{# DO NOT EDIT - Generated by Vibey Framework #}
{# Checksum: {{ checksum }} #}
{# Regenerate with: vibey deploy --platform jetbrains #}
{
  "mcpServers": {
    "vibey": {
      "command": "{{ python_executable }}",
      "args": ["-m", "framework.mcp.server"],
      "env": {
        "VIBEY_PROJECT_ROOT": "{{ project_root }}",
        "VIBEY_CONFIG_PATH": "{{ config_path }}"
      }
    }
  }
}
```

#### Task 1.3: Create Rules Context Template
**File:** `templates/jetbrains/vibey-context.md.j2`
**Effort:** 3 hours
**Dependencies:** None

```jinja2
# Vibey Agent Framework Context

<!-- vibey:checksum:sha256:{{ checksum }} -->
<!-- DO NOT EDIT - Regenerate with: vibey deploy --platform jetbrains -->

## Project Information
- **Name:** {{ project.name }}
- **Type:** {{ project.type }}
- **Orchestration Mode:** {{ framework.orchestration_mode }}

## Available Agents
{% for agent in agents %}
- **{{ agent.name }}** (`{{ agent.id }}`) - {{ agent.description }}
  - Triggers: {{ agent.triggers.keywords | join(', ') }}
{% endfor %}

## Available Workflows
{% for workflow in workflows %}
- **{{ workflow.name }}** (`{{ workflow.id }}`) - {{ workflow.description }}
  - Duration: {{ workflow.duration }}
  - Steps: {{ workflow.steps | length }}
{% endfor %}

## Quality Gates
{% for gate in quality_gates %}
- **{{ gate.name }}**: {{ gate.threshold }}% threshold{% if gate.blocking %} [BLOCKING]{% endif %}
{% endfor %}

## Usage
All agents and workflows are available as MCP tools via the Vibey MCP server.
Use AI Assistant chat to invoke them naturally, e.g., "run security review" or "start sprint planning".
```

#### Task 1.4: Implement generate_mcp_config Method
**File:** `vibey/adapters/jetbrains.py`
**Effort:** 2 hours
**Dependencies:** Task 1.2

```python
def generate_mcp_config(self, project_root: Path) -> Path:
    """Generate .junie/mcp.json for MCP server connection."""
    junie_dir = project_root / ".junie"
    junie_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "mcpServers": {
            "vibey": {
                "command": sys.executable,
                "args": ["-m", "framework.mcp.server"],
                "env": {
                    "VIBEY_PROJECT_ROOT": str(project_root)
                }
            }
        }
    }

    config_path = junie_dir / "mcp.json"
    config_path.write_text(json.dumps(config, indent=2))
    return config_path
```

#### Task 1.5: Implement generate_rules_context Method
**File:** `vibey/adapters/jetbrains.py`
**Effort:** 3 hours
**Dependencies:** Task 1.3

```python
def generate_rules_context(self, config: Any, output_path: Path) -> None:
    """Generate .aiassistant/rules/vibey-context.md."""
    from framework.mcp.discovery import ToolDiscovery

    # Discover agents and workflows from frontmatter
    discovery = ToolDiscovery(self.framework_root)
    agents = discovery.get_agents()
    workflows = discovery.get_workflows()

    # Render template
    template = self.load_template("vibey-context.md.j2")
    content = template.render(
        project=config.project,
        framework=config.framework,
        agents=agents,
        workflows=workflows,
        quality_gates=config.quality_gates,
        checksum=self.compute_checksum(...)
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
```

#### Task 1.6: Implement Drift Detection
**File:** `vibey/adapters/jetbrains.py`
**Effort:** 2 hours
**Dependencies:** Tasks 1.4, 1.5

```python
def check_drift(self, deployment_dir: Path) -> List[str]:
    """Check if generated files have drifted from source."""
    drift_issues = []

    for file_path, expected_checksum in self.get_expected_checksums():
        if file_path.exists():
            actual_checksum = self.extract_checksum(file_path)
            if actual_checksum and actual_checksum != expected_checksum:
                drift_issues.append(
                    f"File {file_path} has been modified. "
                    f"Run 'vibey deploy --platform jetbrains' to regenerate."
                )

    return drift_issues
```

#### Task 1.7: Write Unit Tests
**File:** `tests/adapters/test_jetbrains.py`
**Effort:** 3 hours
**Dependencies:** Tasks 1.1-1.6

```python
class TestJetBrainsAdapter:
    def test_get_platform_name(self):
        adapter = JetBrainsAdapter()
        assert adapter.get_platform_name() == "jetbrains"

    def test_get_deployment_dir(self, tmp_path):
        adapter = JetBrainsAdapter()
        assert adapter.get_deployment_dir(tmp_path) == tmp_path / ".junie"

    def test_generate_mcp_config(self, tmp_path):
        adapter = JetBrainsAdapter()
        config_path = adapter.generate_mcp_config(tmp_path)
        assert config_path.exists()
        config = json.loads(config_path.read_text())
        assert "mcpServers" in config
        assert "vibey" in config["mcpServers"]

    def test_generate_rules_context(self, tmp_path, sample_config):
        adapter = JetBrainsAdapter()
        output = tmp_path / ".aiassistant" / "rules" / "vibey-context.md"
        adapter.generate_rules_context(sample_config, output)
        assert output.exists()
        content = output.read_text()
        assert "Vibey Agent Framework" in content
        assert "vibey:checksum" in content
```

### Sprint 2: Testing & Documentation (1 week)

#### Task 2.1: Integration Test - IntelliJ IDEA
**File:** `tests/integration/test_jetbrains_intellij.md`
**Effort:** 4 hours (manual testing)
**Dependencies:** Sprint 1

**Test Checklist:**
- [ ] Run `vibey deploy --platform jetbrains`
- [ ] Verify `.junie/mcp.json` created
- [ ] Open IntelliJ IDEA
- [ ] Navigate to Settings > Tools > AI Assistant > MCP
- [ ] Import configuration from `.junie/mcp.json`
- [ ] Verify Vibey MCP server connects
- [ ] List tools - verify all 46 tools visible
- [ ] Invoke `vibey_security_reviewer` tool
- [ ] Invoke `vibey_workflow_sprint_planning` tool
- [ ] Verify tool responses are correct

#### Task 2.2: Integration Test - PyCharm
**File:** `tests/integration/test_jetbrains_pycharm.md`
**Effort:** 2 hours (manual testing)
**Dependencies:** Task 2.1

Same checklist as IntelliJ IDEA, with Python-specific workflow tests.

#### Task 2.3: Integration Test - WebStorm
**File:** `tests/integration/test_jetbrains_webstorm.md`
**Effort:** 2 hours (manual testing)
**Dependencies:** Task 2.1

Same checklist as IntelliJ IDEA, with JavaScript/TypeScript-specific workflow tests.

#### Task 2.4: Create User Guide
**File:** `docs/guides/JETBRAINS_INTEGRATION.md`
**Effort:** 4 hours
**Dependencies:** Tasks 2.1-2.3

**Guide Outline:**
1. Prerequisites (JetBrains IDE 2025.1+, AI Assistant plugin)
2. Installation (`vibey deploy --platform jetbrains`)
3. Configuration import in IDE
4. Using Vibey tools in AI Assistant chat
5. Using rules context
6. Troubleshooting common issues
7. Multi-IDE notes

#### Task 2.5: Add CLI Support
**File:** `vibey/cli/commands.py`
**Effort:** 2 hours
**Dependencies:** Sprint 1

```python
@deploy.command(name="jetbrains")
@click.option("--force", is_flag=True, help="Force regeneration")
def deploy_jetbrains(force: bool):
    """Deploy Vibey to JetBrains AI Assistant."""
    adapter = JetBrainsAdapter()
    result = adapter.deploy(
        source_dir=Path(".vibey"),
        config=load_config(),
        clean=force
    )
    if result.success:
        click.echo(f"Deployed to {result.target_dir}")
    else:
        click.echo(f"Deployment failed: {result.errors}", err=True)
```

#### Task 2.6: Update FRAMEWORK_ROADMAP.md
**File:** `docs/FRAMEWORK_ROADMAP.md`
**Effort:** 1 hour
**Dependencies:** All tasks

Update roadmap to reflect JetBrains port completion status.

---

## Zero-Drift Implementation Details

### Checksum Strategy

Each generated file contains an embedded checksum:
```markdown
<!-- vibey:checksum:sha256:abc123def456... -->
```

The checksum is computed from:
1. Source YAML frontmatter content (all agents/workflows)
2. Vibey config files
3. Template version

### Drift Detection Flow

```
User runs: vibey deploy --platform jetbrains
    |
    v
Adapter computes expected checksums from source
    |
    v
Compare with embedded checksums in existing files
    |
    v
If drift detected:
    - Warn user about modified files
    - List specific files with drift
    - Offer to regenerate (default) or preserve
    |
    v
Generate fresh files from source of truth
```

### Regeneration Commands

```bash
# Normal deployment (warns on drift)
vibey deploy --platform jetbrains

# Force regeneration (overwrites modified files)
vibey deploy --platform jetbrains --force

# Check for drift without deploying
vibey deploy --platform jetbrains --check-only

# Show diff between source and generated
vibey deploy --platform jetbrains --diff
```

---

## Quality Gates

### Gate 1: MCP Server Integration (95% threshold)
- [ ] Vibey MCP server starts successfully
- [ ] JetBrains AI Assistant connects via STDIO
- [ ] All 46 tools are discovered
- [ ] Tool invocation works correctly
- [ ] Error responses are properly formatted

### Gate 2: Configuration Generation (100% threshold)
- [ ] `.junie/mcp.json` is valid JSON
- [ ] `.aiassistant/rules/vibey-context.md` is valid Markdown
- [ ] All agents listed in context
- [ ] All workflows listed in context
- [ ] Checksums embedded correctly

### Gate 3: Zero-Drift Validation (100% threshold)
- [ ] Running deploy twice produces identical files
- [ ] Modifying source and redeploying updates generated files
- [ ] Drift detection works correctly
- [ ] Manual edits are detected and warned

### Gate 4: Multi-IDE Compatibility (90% threshold)
- [ ] Works in IntelliJ IDEA 2025.1+
- [ ] Works in PyCharm 2025.1+
- [ ] Works in WebStorm 2025.1+
- [ ] Configuration is portable between IDEs

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| MCP version incompatibility | Low | Medium | Test with multiple JetBrains versions |
| User edits generated files | Medium | Low | Clear warnings, drift detection |
| STDIO communication issues | Low | High | Robust error handling, logging |
| IDE version differences | Low | Low | Document minimum version requirements |

---

## Deliverables Summary

### Code Files (4)
1. `vibey/adapters/jetbrains.py` - JetBrainsAdapter class
2. `templates/jetbrains/mcp.json.j2` - MCP config template
3. `templates/jetbrains/vibey-context.md.j2` - Rules context template
4. `tests/adapters/test_jetbrains.py` - Unit tests

### Documentation Files (2)
1. `docs/guides/JETBRAINS_INTEGRATION.md` - User guide
2. `docs/development/JETBRAINS_PORT_IMPLEMENTATION.md` - Updated implementation doc

### Test Artifacts (3)
1. `tests/integration/test_jetbrains_intellij.md` - IntelliJ test results
2. `tests/integration/test_jetbrains_pycharm.md` - PyCharm test results
3. `tests/integration/test_jetbrains_webstorm.md` - WebStorm test results

---

## Success Criteria

1. **Functional:**
   - `vibey deploy --platform jetbrains` creates valid configuration
   - JetBrains AI Assistant connects to Vibey MCP server
   - All 46 tools visible and invocable

2. **Zero-Drift:**
   - All generated files contain checksums
   - Drift detection identifies modified files
   - Regeneration produces consistent output

3. **Multi-IDE:**
   - Works in at least 3 JetBrains IDEs
   - No IDE-specific configuration needed

4. **Documentation:**
   - Complete user guide with screenshots
   - Troubleshooting section covers common issues

---

## References

### JetBrains Documentation
- [AI Assistant MCP Support](https://www.jetbrains.com/help/ai-assistant/mcp.html)
- [Configure MCP Server](https://www.jetbrains.com/help/ai-assistant/configure-an-mcp-server.html)
- [AI Assistant Rules](https://www.jetbrains.com/help/ai-assistant/settings-reference-rules.html)
- [Junie MCP Settings](https://www.jetbrains.com/help/junie/mcp-settings.html)

### Vibey Infrastructure
- MCP Server: `/Users/fredabood/Repositories/vibey/framework/mcp/server.py`
- Tool Discovery: `/Users/fredabood/Repositories/vibey/framework/mcp/discovery/`
- Base Adapter: `/Users/fredabood/Repositories/vibey/vibey/adapters/base.py`
- Claude Adapter Reference: `/Users/fredabood/Repositories/vibey/vibey/adapters/claude_code.py`

### External Resources
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [IntelliJ IDEA 2025.1 MCP Blog Post](https://blog.jetbrains.com/idea/2025/05/intellij-idea-2025-1-model-context-protocol/)
- [JetBrains MCP GitHub](https://github.com/JetBrains/mcp-jetbrains)

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-23
**Author:** Vibey Framework Team
