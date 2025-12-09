# Continue.dev Platform Port - Implementation Plan

**Version:** 1.0
**Date:** 2025-11-23
**Status:** Planning Phase
**Track ID:** `continue-port`

---

## Executive Summary

This document outlines the comprehensive implementation plan for porting the Vibey agent framework to Continue.dev, an open-source AI coding assistant supporting VS Code and JetBrains IDEs.

**Key Finding:** Continue.dev has **native MCP support** (announced December 2024), meaning we can **reuse our existing MCP server directly** with minimal adaptation. This significantly reduces implementation effort.

**Strategic Value:**
- **IDE Integration:** Continue supports both VS Code and JetBrains (IntelliJ, PyCharm, etc.)
- **MCP Native:** Full MCP support maps directly to our existing 46+ tools
- **Open Source:** Community-driven, extensible platform
- **Multi-LLM:** Works with OpenAI, Anthropic, Ollama, and other providers

**Estimated Effort:** 3.5 weeks (reduced from initial estimate due to MCP reuse)
**Priority:** High

---

## Table of Contents

1. [Research Findings](#research-findings)
2. [Architecture Decisions](#architecture-decisions)
3. [MCP Reuse Strategy](#mcp-reuse-strategy)
4. [Adapter Design](#adapter-design)
5. [Zero-Drift Implementation](#zero-drift-implementation)
6. [Sprint Plan](#sprint-plan)
7. [File Paths Reference](#file-paths-reference)
8. [Risk Assessment](#risk-assessment)
9. [Success Metrics](#success-metrics)

---

## Research Findings

### Continue.dev Architecture Overview

**Source:** [Continue.dev Documentation](https://docs.continue.dev/customize/overview)

Continue follows a **core <-> extension <-> GUI** architecture:
- **Core:** Loads configuration, manages models, context providers, and slash commands
- **Extension:** IDE plugin (VS Code TypeScript, JetBrains Kotlin)
- **GUI:** React application with Redux state management

### Configuration System

**Source:** [config.yaml Reference](https://docs.continue.dev/reference)

Continue recently migrated from `config.json` to `config.yaml` format:

```yaml
# ~/.continue/config.yaml (global)
# .continuerc.yaml (workspace-level)
name: "vibey-assistant"
version: "1.0.0"
schema: v1

models:
  - name: Claude Sonnet
    provider: anthropic
    model: claude-sonnet-4-20250514
    roles:
      - chat

mcpServers:
  - name: Vibey Roadmap
    command: python
    args:
      - "-m"
      - "framework.mcp.server"

context:
  - provider: code
  - provider: docs
  - provider: diff

prompts:
  - name: vibey-planning
    description: Start sprint planning workflow
    prompt: |
      You are the Sprint Planning Agent...

rules:
  - Always follow Vibey quality gates
  - Use structured handoffs between agents
```

### MCP Integration (Critical Finding)

**Source:** [MCP Setup Guide](https://docs.continue.dev/customize/deep-dives/mcp)

Continue was the **first client to offer full MCP support** (December 2024):

| MCP Feature | Continue Mapping |
|-------------|------------------|
| **Resources** | Context Providers (@ mentions) |
| **Prompts** | Slash Commands (/ prefix) |
| **Tools** | Tools (function calling) |

**Configuration Example:**
```yaml
mcpServers:
  - name: Vibey
    command: uvx
    args:
      - vibey-mcp-server
    cwd: /path/to/project
```

**JSON Config Compatibility:** Continue can read JSON MCP configs from other tools (Claude Desktop, Cursor) by placing them in `~/.continue/mcpServers/` directory.

### Prompt Files (.prompt format)

**Source:** [Prompt Files Documentation](https://docs.continue.dev/customize/deep-dives/prompts)

Continue supports `.prompt` files with Handlebars syntax:

```markdown
---
name: sprint-planning
description: Start Vibey sprint planning workflow
temperature: 0.7
---
<s>
You are the Sprint Planning Agent from the Vibey framework.
</s>

{{{ input }}}

Current file context:
{{{ currentFile }}}
```

### Continue Hub Blocks

**Source:** [Continue Hub](https://hub.continue.dev/)

Continue Hub allows sharing reusable blocks:
- Models, rules, context providers, prompts, docs, data, MCP servers
- Blocks identified by slug: `owner-slug/block-slug`
- Can be imported using `uses` clause in config.yaml

---

## Architecture Decisions

### ADR-001: Direct MCP Server Reuse

**Status:** Accepted

**Context:**
Continue.dev has native MCP support that maps directly to our existing MCP server at `framework/mcp/server.py`. Our server already exposes:
- 46+ tools (agents, workflows, roadmap operations)
- Dynamic tool discovery from YAML frontmatter
- Caching with TTL for efficient operation

**Decision:**
Reuse the existing Vibey MCP server directly instead of creating Continue-specific tools.

**Consequences:**
- Reduced implementation effort (weeks saved)
- Consistent behavior across platforms
- Single codebase to maintain
- Continue users get access to all Vibey tools immediately

### ADR-002: Dual Configuration Approach

**Status:** Accepted

**Context:**
Continue supports both global (`~/.continue/`) and workspace (`.continuerc.yaml`) configuration.

**Decision:**
Generate two configuration artifacts:
1. **Workspace config** (`.continuerc.yaml`): Project-specific settings, Vibey MCP server
2. **Prompt files** (`.prompts/*.prompt`): Agent instructions and workflow triggers

**Consequences:**
- Users can have global Continue config with Vibey overlay
- Project-specific customization supported
- Follows Continue's hierarchical config model

### ADR-003: Adapter Pattern for Continue

**Status:** Accepted

**Context:**
Vibey already has adapters for Claude Code, Goose, Aider, and Gemini at `vibey/adapters/`.

**Decision:**
Create a new Continue adapter module at `vibey/adapters/continue/` following the established pattern from the Gemini adapter.

**Consequences:**
- Consistent architecture across all platform ports
- Reuse base adapter interfaces
- Zero-drift architecture from frontmatter

### ADR-004: Prompt Files from Agent Frontmatter

**Status:** Accepted

**Context:**
Continue's `.prompt` files map well to Vibey's agent definitions. Agent frontmatter contains triggers, inputs, and descriptions that can populate prompt files.

**Decision:**
Generate `.prompt` files dynamically from agent YAML frontmatter, similar to how Gemini adapter generates TOML commands.

**Consequences:**
- Zero-drift from source of truth (frontmatter)
- All 12 agents automatically available as slash commands
- Consistent with established adapter patterns

---

## MCP Reuse Strategy

### Existing MCP Server Capabilities

The Vibey MCP server at `framework/mcp/server.py` already provides:

```python
# Static roadmap tools
- vibey_start_task
- vibey_complete_task
- vibey_query_task
- vibey_start_sprint
- vibey_complete_sprint
- vibey_query_sprint
- vibey_query_track
- vibey_refresh_progress
- vibey_roadmap_status
- vibey_list_blockers
- vibey_list_dependencies

# Dynamic agent tools (from frontmatter discovery)
- vibey_sprint_planning
- vibey_security_reviewer
- vibey_test_engineer
- vibey_performance_engineer
- vibey_documentation_engineer
- vibey_git_committer
- vibey_coordinator
- ... (12 agents total)

# Dynamic workflow tools (from frontmatter discovery)
- vibey_workflow_sprint_planning
- vibey_workflow_single_feature_development
- vibey_workflow_security_hardening
- vibey_workflow_ml_model_development
- ... (16 workflows total)
```

### Continue MCP Configuration

Generated `mcpServers` block for config.yaml:

```yaml
mcpServers:
  - name: vibey
    command: python
    args:
      - "-m"
      - "framework.mcp.server"
      - "--roadmap-root"
      - ".vibey/roadmap"
    cwd: ${workspaceFolder}
    env:
      PYTHONPATH: ${workspaceFolder}
```

### Tool to Context Provider Mapping

For Continue's `@` mention system, we'll create context providers that surface Vibey data:

| Vibey Data | Continue Context Provider | Usage |
|------------|---------------------------|-------|
| Current sprint status | `@vibey-sprint` | "@vibey-sprint what's the current progress?" |
| Roadmap overview | `@vibey-roadmap` | "@vibey-roadmap show all tracks" |
| Task details | `@vibey-task` | "@vibey-task core-framework-2-task-001" |

---

## Adapter Design

### Directory Structure

```
vibey/adapters/continue/
    __init__.py           # Module exports
    adapter.py            # ContinueAdapter(PlatformAdapter)
    config_generator.py   # Generate config.yaml / .continuerc.yaml
    prompt_generator.py   # Generate .prompt files from frontmatter
    context_generator.py  # Generate CONTINUE.md context file
    hub_generator.py      # (Future) Generate Continue Hub blocks
    tests/
        __init__.py
        test_adapter.py
        test_config_generator.py
        test_prompt_generator.py
```

### ContinueAdapter Class

```python
# vibey/adapters/continue/adapter.py

from vibey.adapters.base import PlatformAdapter, DeploymentResult
from .config_generator import ContinueConfigGenerator
from .prompt_generator import ContinuePromptGenerator
from .context_generator import ContinueContextGenerator

class ContinueAdapter(PlatformAdapter):
    """
    Adapter for Continue.dev platform.

    Generates:
    - .continuerc.yaml (workspace config with MCP server)
    - .prompts/*.prompt (agent slash commands)
    - CONTINUE.md (optional context file)
    - .checksums.json (drift detection)

    Zero-Drift Guarantee:
    All artifacts generated from YAML frontmatter.
    """

    def get_platform_name(self) -> str:
        return "continue"

    def get_deployment_dir(self, project_root: Path = None) -> Path:
        return (project_root or Path.cwd()) / ".continue-vibey"

    def deploy(
        self,
        source_dir: Path,
        config: Any,
        target_dir: Path = None,
        clean: bool = False
    ) -> DeploymentResult:
        """
        Deploy Vibey to Continue.dev.

        Creates:
        1. .continuerc.yaml with mcpServers config
        2. .prompts/ directory with agent .prompt files
        3. CONTINUE.md context file
        4. .checksums.json for drift detection
        """
        ...

    def supports_feature(self, feature: str) -> bool:
        supported = {"agents", "workflows", "mcp", "rules"}
        not_supported = {"subagents", "parallel-tasks"}  # Continue is sequential
        return feature in supported and feature not in not_supported
```

### Prompt Generator

```python
# vibey/adapters/continue/prompt_generator.py

from framework.mcp.discovery.agents import AgentDiscovery, AgentDefinition

class ContinuePromptGenerator:
    """
    Generate .prompt files from Vibey agent frontmatter.

    Each agent becomes a slash command:
    - /vibey-sprint-planning
    - /vibey-security-reviewer
    - /vibey-test-engineer
    """

    def generate_prompt_file(self, agent: AgentDefinition) -> str:
        """Generate .prompt file content for an agent."""

        # Build preamble from agent metadata
        preamble = f"""---
name: vibey-{agent.id}
description: {agent.description}
temperature: 0.7
---"""

        # System message from agent instructions
        system_msg = f"""<s>
You are the {agent.name} from the Vibey Agent Framework.
{agent.description}

Trigger conditions: {', '.join(agent.triggers.keywords)}
</s>"""

        # User input placeholder
        body = """{{{ input }}}

## Context
Current file: {{{ currentFile }}}
"""

        return f"{preamble}\n{system_msg}\n\n{body}"
```

### Config Generator

```python
# vibey/adapters/continue/config_generator.py

import yaml
from pathlib import Path

class ContinueConfigGenerator:
    """
    Generate Continue.dev configuration files.

    Outputs:
    - .continuerc.yaml (workspace config)
    - Optional: ~/.continue/mcpServers/vibey.json (global MCP)
    """

    def generate_workspace_config(
        self,
        mcp_server_path: str = "framework.mcp.server",
        python_command: str = "python",
        include_rules: bool = True
    ) -> str:
        """Generate .continuerc.yaml content."""

        config = {
            "name": "vibey-assistant",
            "version": "1.0.0",
            "schema": "v1",
            "mcpServers": [
                {
                    "name": "vibey",
                    "command": python_command,
                    "args": ["-m", mcp_server_path],
                }
            ],
            "context": [
                {"provider": "code"},
                {"provider": "docs"},
                {"provider": "diff"},
            ]
        }

        if include_rules:
            config["rules"] = [
                "Follow Vibey quality gates for all code changes",
                "Use structured handoffs when transitioning between agents",
                "Document all architecture decisions",
                "Maintain test coverage above 90%"
            ]

        return yaml.dump(config, default_flow_style=False, sort_keys=False)
```

---

## Zero-Drift Implementation

### Checksum-Based Drift Detection

Following the Gemini adapter pattern (`vibey/adapters/gemini/adapter.py`):

```python
def _write_checksums_manifest(
    self,
    output_dir: Path,
    checksums: Dict[str, str],
) -> None:
    """Write checksums manifest for drift detection."""
    manifest = {
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "vibey-continue-adapter",
        "checksums": checksums,
        "validation_command": "vibey export continue --validate",
    }
    manifest_path = output_dir / ".checksums.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding='utf-8'
    )
```

### Validation Flow

```python
def validate_export(self, export_dir: Path) -> tuple[bool, List[str]]:
    """
    Validate an existing export hasn't drifted.

    Compares actual file content with stored checksums
    to detect manual edits.
    """
    errors = []

    checksums_path = export_dir / ".checksums.json"
    if not checksums_path.exists():
        errors.append("Missing .checksums.json - cannot validate")
        return False, errors

    stored = json.loads(checksums_path.read_text())
    stored_checksums = stored.get("checksums", {})

    # Regenerate from frontmatter and compare
    current_config = self.config_generator.generate_workspace_config()
    current_checksum = hashlib.sha256(current_config.encode()).hexdigest()[:16]

    if stored_checksums.get("config") != current_checksum:
        errors.append(
            f"Config has drifted! "
            f"Stored: {stored_checksums.get('config')}, "
            f"Current: {current_checksum}"
        )

    return len(errors) == 0, errors
```

### CI Integration

Add to CI pipeline:

```yaml
# .github/workflows/validate-exports.yml
name: Validate Platform Exports
on: [push, pull_request]

jobs:
  validate-continue:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .
      - run: vibey export continue --validate
```

---

## Sprint Plan

### Sprint 1: Continue Adapter & Configuration (1.5 weeks)

**Sprint ID:** `continue-port-1`
**Goal:** Create the Continue adapter with MCP server configuration

#### Tasks

| ID | Task | File Path | Duration |
|----|------|-----------|----------|
| 1.1 | Create adapter module structure | `vibey/adapters/continue/__init__.py` | 0.5 days |
| 1.2 | Implement ContinueAdapter base class | `vibey/adapters/continue/adapter.py` | 1 day |
| 1.3 | Implement config generator | `vibey/adapters/continue/config_generator.py` | 1 day |
| 1.4 | Implement prompt generator | `vibey/adapters/continue/prompt_generator.py` | 1.5 days |
| 1.5 | Add drift detection with checksums | `vibey/adapters/continue/adapter.py` | 0.5 days |
| 1.6 | Write unit tests | `vibey/adapters/continue/tests/*.py` | 1.5 days |
| 1.7 | Add CLI integration | `vibey/cli/commands.py` (export continue) | 0.5 days |

**Quality Gates:**
- All tests passing
- 90%+ code coverage
- Documentation complete

### Sprint 2: Context Providers & Testing (2 weeks)

**Sprint ID:** `continue-port-2`
**Goal:** Add context providers, multi-IDE support, and comprehensive testing

#### Tasks

| ID | Task | File Path | Duration |
|----|------|-----------|----------|
| 2.1 | Implement context generator (CONTINUE.md) | `vibey/adapters/continue/context_generator.py` | 1 day |
| 2.2 | Create context provider configs | `vibey/adapters/continue/providers/` | 1.5 days |
| 2.3 | Test with VS Code Continue extension | Manual testing | 1 day |
| 2.4 | Test with JetBrains Continue plugin | Manual testing | 1 day |
| 2.5 | Integration tests with real MCP server | `tests/integration/test_continue_mcp.py` | 2 days |
| 2.6 | Create installation documentation | `docs/platforms/CONTINUE.md` | 1 day |
| 2.7 | Create Continue Hub block (optional) | `vibey/adapters/continue/hub_generator.py` | 1.5 days |
| 2.8 | End-to-end workflow validation | Manual testing | 1 day |

**Quality Gates:**
- All tests passing
- VS Code and JetBrains tested
- Documentation complete
- Zero-drift validation passing

---

## File Paths Reference

### Source Files (Read-Only, Single Source of Truth)

| Purpose | Path |
|---------|------|
| Agent definitions | `framework/agents/**/*.md` |
| Workflow definitions | `framework/workflows/**/*.md` |
| MCP server | `framework/mcp/server.py` |
| Tool discovery | `framework/mcp/discovery/*.py` |

### Generated Artifacts (Continue Export)

| Artifact | Path | Source |
|----------|------|--------|
| Workspace config | `.continuerc.yaml` | Generated from adapter |
| Prompt files | `.prompts/vibey-*.prompt` | Generated from agent frontmatter |
| Context file | `CONTINUE.md` | Generated from agents/workflows |
| Checksums | `.checksums.json` | Generated for drift detection |

### Adapter Implementation

| Component | Path |
|-----------|------|
| Main adapter | `vibey/adapters/continue/adapter.py` |
| Config generator | `vibey/adapters/continue/config_generator.py` |
| Prompt generator | `vibey/adapters/continue/prompt_generator.py` |
| Context generator | `vibey/adapters/continue/context_generator.py` |
| Tests | `vibey/adapters/continue/tests/*.py` |

### Documentation

| Document | Path |
|----------|------|
| Platform guide | `docs/platforms/CONTINUE.md` |
| Installation | `docs/getting-started/CONTINUE_QUICKSTART.md` |

---

## Risk Assessment

### Low Risk

| Risk | Mitigation |
|------|------------|
| Continue config format changes | Pin to schema v1, monitor releases |
| JetBrains plugin differences | Test both IDEs in Sprint 2 |

### Medium Risk

| Risk | Mitigation |
|------|------------|
| MCP server compatibility issues | Test stdio transport early |
| Performance with many tools (46+) | Implement tool filtering if needed |

### High Risk

| Risk | Mitigation |
|------|------------|
| Continue removes MCP support | Fallback to prompt files + rules only |
| Breaking changes in Continue 2.0 | Monitor changelog, delay if needed |

---

## Success Metrics

### Sprint 1 Success Criteria

- [ ] ContinueAdapter implements PlatformAdapter interface
- [ ] Config generator produces valid YAML
- [ ] Prompt generator creates all 12 agent prompts
- [ ] Drift detection working with checksums
- [ ] `vibey export continue` CLI command functional
- [ ] All unit tests passing (>90% coverage)

### Sprint 2 Success Criteria

- [ ] MCP server connects successfully in Continue
- [ ] All 46+ tools discoverable via MCP
- [ ] VS Code extension tested end-to-end
- [ ] JetBrains plugin tested end-to-end
- [ ] Context providers surfacing Vibey data
- [ ] Documentation complete and reviewed
- [ ] Zero-drift CI validation passing

### Overall Track Success Criteria

- [ ] Complete feature parity with Claude Code adapter
- [ ] Users can install Vibey in Continue with one command
- [ ] All quality gates passed
- [ ] No manual edits to generated files (zero-drift)
- [ ] Community feedback incorporated

---

## Appendix A: Continue.dev MCP Transport Options

Continue supports multiple MCP transport modes:

### Stdio (Recommended)

```yaml
mcpServers:
  - name: vibey
    command: python
    args: ["-m", "framework.mcp.server"]
```

### SSE (Server-Sent Events)

```yaml
mcpServers:
  - name: vibey-remote
    type: sse
    url: https://api.example.com/vibey-mcp
```

### Streamable HTTP

```yaml
mcpServers:
  - name: vibey-http
    type: streamable-http
    url: https://api.example.com/vibey-mcp/stream
```

**Recommendation:** Use stdio for local development, SSE for team/cloud deployments.

---

## Appendix B: Sample Generated Files

### .continuerc.yaml

```yaml
name: vibey-assistant
version: 1.0.0
schema: v1

mcpServers:
  - name: vibey
    command: python
    args:
      - -m
      - framework.mcp.server
      - --roadmap-root
      - .vibey/roadmap

context:
  - provider: code
  - provider: docs
  - provider: diff
  - provider: folder

rules:
  - Follow Vibey quality gates for all code changes
  - Use structured handoffs when transitioning between agents
  - Document all architecture decisions
  - Maintain test coverage above 90%

prompts:
  - uses: ./.prompts/vibey-sprint-planning.prompt
  - uses: ./.prompts/vibey-security-reviewer.prompt
  - uses: ./.prompts/vibey-test-engineer.prompt
```

### .prompts/vibey-sprint-planning.prompt

```markdown
---
name: vibey-sprint-planning
description: Sprint Planning Agent for roadmap and iteration planning
temperature: 0.7
---
<s>
You are the Sprint Planning Agent from the Vibey Agent Framework.

Your responsibilities:
- Analyzing current project state and collecting requirements
- Creating comprehensive sprint plans with clear objectives
- Ordering sprints based on dependencies and business value
- Tracking progress and updating roadmap documentation

Trigger patterns: sprint planning, plan sprint, roadmap, iteration, backlog
</s>

{{{ input }}}

## Context
Current file: {{{ currentFile }}}
```

---

## Sources

- [Continue.dev Documentation](https://docs.continue.dev/)
- [Continue MCP Setup](https://docs.continue.dev/customize/deep-dives/mcp)
- [config.yaml Reference](https://docs.continue.dev/reference)
- [Prompt Files Documentation](https://docs.continue.dev/customize/deep-dives/prompts)
- [Continue Hub](https://hub.continue.dev/)
- [Model Context Protocol x Continue Blog](https://blog.continue.dev/model-context-protocol/)
- [Continue GitHub Repository](https://github.com/continuedev/continue)

---

*Generated: 2025-11-23*
*Track: continue-port*
*Framework: Vibey Agent Framework v2.5.0*
