# Sourcegraph Cody Platform Port - Implementation Plan

**Version:** 1.0
**Date:** 2025-11-23
**Status:** Planning Phase
**Track:** cody-port

---

## Executive Summary

This document outlines the implementation plan for porting Vibey to Sourcegraph Cody. The port leverages Cody's **native MCP support** and **OpenCtx context providers** to deliver zero-drift integration where all Cody artifacts are generated from the same YAML frontmatter used by the MCP server.

### Critical Context: Cody Tier Changes (July 2025)

**Important:** Sourcegraph has announced that [Cody Free and Pro tiers will be discontinued on July 23, 2025](https://sourcegraph.com/blog/changes-to-cody-free-pro-and-enterprise-starter-plans). Only **Cody Enterprise** will continue to be supported.

**Impact on Implementation:**
- Target only Cody Enterprise features
- Enterprise Sourcegraph integration becomes primary use case
- Consider Amp (Sourcegraph's successor) for non-enterprise users
- Timeline adjusted to Q2 2026 (post-July 2025 transition)

### Key Strategic Insights

1. **MCP is the Recommended Path**: Sourcegraph explicitly recommends MCP for adding external context to Cody
2. **Prompt Library Replaces Custom Commands**: Legacy custom commands are deprecated; Prompt Library is the new standard
3. **Enterprise-Only Future**: Implementation should focus on enterprise features
4. **OpenCtx Integration**: Cody uses OpenCtx as the bridge to MCP servers

---

## Table of Contents

1. [Research Findings](#research-findings)
2. [Architecture Decisions](#architecture-decisions)
3. [Integration Approach](#integration-approach)
4. [Adapter Design](#adapter-design)
5. [Sprint Plan](#sprint-plan)
6. [Zero-Drift Implementation](#zero-drift-implementation)
7. [Risk Assessment](#risk-assessment)
8. [Success Metrics](#success-metrics)

---

## Research Findings

### Cody Platform Overview

**Sourcegraph Cody** is an AI coding assistant with deep codebase understanding through Sourcegraph's code intelligence platform.

**Supported IDEs:**
- VS Code (primary)
- JetBrains (limited features)
- Web interface (Sourcegraph instance)

### Extension Points

| Extension Point | Description | Vibey Mapping |
|----------------|-------------|---------------|
| **MCP Servers** | Native support via OpenCtx bridge | Primary integration path |
| **Prompt Library** | Reusable prompts with dynamic context | Agent shortcuts |
| **OpenCtx Providers** | External context sources (experimental) | Workflow state |
| **Context Mentions** | @-mention syntax for dynamic context | Task/Sprint context |

### MCP Integration Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Cody Extension                             │
├──────────────────────────────────────────────────────────────┤
│                    OpenCtx Layer                              │
│  (Bridges external context sources including MCP)            │
├──────────────────────────────────────────────────────────────┤
│                    MCP Protocol                               │
│  (Standardized tool/resource/prompt interface)               │
├──────────────────────────────────────────────────────────────┤
│                  Vibey MCP Server                             │
│  (46 tools, dynamic discovery, agent/workflow execution)     │
└──────────────────────────────────────────────────────────────┘
```

### Configuration Format

Cody MCP servers are configured in VS Code settings:

```json
{
  "openctx.providers": {
    "https://openctx.org/npm/@openctx/provider-mcp": {
      "server": {
        "command": "python",
        "args": ["-m", "framework.mcp.server"]
      }
    }
  },
  "cody.experimental.noodle": true
}
```

### Prompt Library Format

Prompts are created via the Sourcegraph web UI (Enterprise only):
- No programmatic API for prompt creation
- UI-based management only
- Support for dynamic context via @-mentions
- "Chat only" or "Edit code" modes

### Key Limitations

1. **No Public API**: No programmatic way to create/manage prompts
2. **Enterprise-Only Advanced Features**: OpenCtx providers require Enterprise
3. **Sequential Execution**: No parallel subagent spawning like Claude Code
4. **VS Code Primary**: JetBrains and web have limited feature sets

---

## Architecture Decisions

### ADR-001: MCP as Primary Integration Path

**Decision:** Use Vibey's existing MCP server as the primary integration mechanism.

**Rationale:**
- Sourcegraph explicitly recommends MCP for external context
- Vibey already has a production MCP server with 46 tools
- Zero additional development for core functionality
- Follows established pattern from Gemini port

**Consequences:**
- No custom Cody API client needed
- Depends on Cody's MCP support stability
- Enterprise users get immediate access to all Vibey tools

### ADR-002: Leverage Existing Infrastructure

**Decision:** Reuse existing infrastructure from completed ports.

**Existing Components to Reuse:**
| Component | Location | Reuse Strategy |
|-----------|----------|----------------|
| MCP Server | `framework/mcp/server.py` | Direct use |
| Tool Discovery | `framework/mcp/discovery/` | Direct use |
| Base Adapter | `vibey/adapters/base.py` | Inherit |
| Gemini Context Generator | `vibey/adapters/gemini/context_generator.py` | Adapt for CODY.md |
| Gemini Command Generator | `vibey/adapters/gemini/command_generator.py` | Skip (Cody uses Prompt Library) |

### ADR-003: CODY.md Context File

**Decision:** Generate a CODY.md context file similar to GEMINI.md.

**Rationale:**
- Cody can read context files when added to chat
- Provides project-specific instructions
- Zero-drift from same frontmatter source

### ADR-004: Enterprise-Only Focus

**Decision:** Target Cody Enterprise exclusively.

**Rationale:**
- Free/Pro tiers sunset July 2025
- Enterprise has full MCP support
- Cross-repository features require Enterprise
- Sourcegraph code intelligence requires Enterprise instance

---

## Integration Approach

### Phase 1: MCP Server Configuration (Week 1)

Configure Cody to connect to Vibey's MCP server:

```json
// .vscode/settings.json (user project)
{
  "openctx.providers": {
    "https://openctx.org/npm/@openctx/provider-mcp": {
      "name": "Vibey Framework",
      "server": {
        "command": "python",
        "args": ["-m", "framework.mcp.server", "--roadmap-root", ".vibey/roadmap"],
        "cwd": "${workspaceFolder}"
      }
    }
  }
}
```

### Phase 2: Context Generation (Week 2-3)

Generate CODY.md from frontmatter:

```
framework/agents/*.md (frontmatter)
framework/workflows/*.md (frontmatter)
                │
                ▼
┌─────────────────────────────────┐
│  CodyContextGenerator           │
│  (vibey/adapters/cody/)         │
└─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  .cody/                          │
│  ├── CODY.md                    │
│  ├── settings.json              │
│  └── .checksums.json            │
└─────────────────────────────────┘
```

### Phase 3: Sourcegraph Integration (Week 4-5)

Enterprise features:
- Code graph navigation
- Cross-repository context
- Sourcegraph search integration

### Phase 4: Testing & Documentation (Week 6)

- E2E tests with Cody extension
- Enterprise instance testing
- Migration guide from Claude Code

---

## Adapter Design

### Class Hierarchy

```python
# vibey/adapters/cody/__init__.py
from vibey.adapters.base import PlatformAdapter, DeploymentResult

class CodyAdapter(PlatformAdapter):
    """
    Adapter for Sourcegraph Cody platform.

    Exports Vibey framework to Cody's configuration format:
    - CODY.md context file (from agent frontmatter)
    - settings.json (MCP server configuration)
    - Prompt templates for Sourcegraph Prompt Library

    Zero-Drift Guarantee:
    All outputs are generated from frontmatter. The adapter tracks
    checksums for each generated artifact, enabling CI to detect
    and reject manual edits.
    """

    def get_platform_name(self) -> str:
        return "cody"

    def get_deployment_dir(self, project_root: Path = None) -> Path:
        return (project_root or Path.cwd()) / ".cody"

    def deploy(self, source_dir: Path, config: Any,
               target_dir: Path = None, clean: bool = False) -> DeploymentResult:
        """Deploy to Cody (.cody/ directory)."""
        ...

    def generate_context_file(self, config: Any, output_path: Path) -> None:
        """Generate CODY.md context file."""
        ...

    def validate_deployment(self, deployment_dir: Path) -> tuple[bool, list[str]]:
        """Validate Cody deployment."""
        ...
```

### Module Structure

```
vibey/adapters/cody/
├── __init__.py           # CodyAdapter class
├── adapter.py            # Main adapter implementation
├── context_generator.py  # CODY.md generation
├── settings_generator.py # VS Code settings generation
├── prompt_generator.py   # Prompt Library templates
├── enterprise.py         # Sourcegraph Enterprise features
└── tests/
    ├── __init__.py
    ├── test_adapter.py
    ├── test_context_generator.py
    ├── test_settings_generator.py
    └── test_e2e.py
```

### Context Generator Design

```python
# vibey/adapters/cody/context_generator.py
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import hashlib

from framework.mcp.discovery.agents import AgentDiscovery
from framework.mcp.discovery.workflows import WorkflowDiscovery

@dataclass
class GeneratedContext:
    content: str
    checksum: str
    agents_count: int
    workflows_count: int

class CodyContextGenerator:
    """
    Generate CODY.md from Vibey agent/workflow frontmatter.

    Zero-Drift: Content is deterministically generated from source.
    Checksum enables drift detection in CI.
    """

    def __init__(self, root_dir: Path):
        self.root_dir = Path(root_dir)
        self.agent_discovery = AgentDiscovery(root_dir)
        self.workflow_discovery = WorkflowDiscovery(root_dir)

    def generate(self) -> GeneratedContext:
        """Generate CODY.md content from frontmatter."""
        agents = self.agent_discovery.discover()
        workflows = self.workflow_discovery.discover()

        content = self._build_content(agents, workflows)
        checksum = hashlib.sha256(content.encode()).hexdigest()[:16]

        return GeneratedContext(
            content=content,
            checksum=checksum,
            agents_count=len(agents),
            workflows_count=len(workflows),
        )

    def _build_content(self, agents, workflows) -> str:
        """Build CODY.md content."""
        lines = [
            "# Vibey Agent Framework - Cody Context",
            "",
            "This project uses the Vibey Agent Framework for intelligent development workflows.",
            "",
            "## Available Tools (via MCP)",
            "",
            "Use Cody chat to invoke Vibey tools with natural language.",
            "",
        ]

        # Add agent documentation
        lines.extend(self._format_agents(agents))

        # Add workflow documentation
        lines.extend(self._format_workflows(workflows))

        # Add usage instructions
        lines.extend(self._format_usage_guide())

        return "\n".join(lines)
```

---

## Sprint Plan

### Sprint 1: Core Adapter & MCP Configuration (3 weeks)

**ID:** `cody-port-1`
**Duration:** 3 weeks
**Priority:** HIGH

#### Tasks

| ID | Task | Agent | File Path | Priority |
|----|------|-------|-----------|----------|
| `cody-port-1-task-001` | Create CodyAdapter base class | backend-engineer | `vibey/adapters/cody/adapter.py` | critical |
| `cody-port-1-task-002` | Implement CodyContextGenerator | backend-engineer | `vibey/adapters/cody/context_generator.py` | critical |
| `cody-port-1-task-003` | Implement CodySettingsGenerator | backend-engineer | `vibey/adapters/cody/settings_generator.py` | critical |
| `cody-port-1-task-004` | Add `vibey deploy --platform cody` CLI | backend-engineer | `vibey/cli/commands.py` | high |
| `cody-port-1-task-005` | Write unit tests for adapter | test-engineer | `vibey/adapters/cody/tests/test_adapter.py` | high |
| `cody-port-1-task-006` | Write unit tests for generators | test-engineer | `vibey/adapters/cody/tests/test_context_generator.py` | high |

#### Deliverables

```
vibey/adapters/cody/
├── __init__.py
├── adapter.py
├── context_generator.py
├── settings_generator.py
└── tests/
    ├── __init__.py
    ├── test_adapter.py
    ├── test_context_generator.py
    └── test_settings_generator.py
```

#### Quality Gates

- **Unit Tests:** >90% coverage on new code
- **Zero-Drift Validation:** Checksums generated and verified

---

### Sprint 2: Enterprise Features & Documentation (2 weeks)

**ID:** `cody-port-2`
**Duration:** 2 weeks
**Priority:** HIGH

#### Tasks

| ID | Task | Agent | File Path | Priority |
|----|------|-------|-----------|----------|
| `cody-port-2-task-001` | Implement Sourcegraph Enterprise module | backend-engineer | `vibey/adapters/cody/enterprise.py` | high |
| `cody-port-2-task-002` | Create Prompt Library templates | backend-engineer | `templates/cody/prompts/` | high |
| `cody-port-2-task-003` | Write E2E tests with Cody extension | test-engineer | `vibey/adapters/cody/tests/test_e2e.py` | high |
| `cody-port-2-task-004` | Write Cody integration guide | docs-writer | `docs/guides/CODY_INTEGRATION.md` | medium |

#### Deliverables

```
vibey/adapters/cody/
├── enterprise.py           # Sourcegraph Enterprise features
└── tests/
    └── test_e2e.py         # E2E tests

templates/cody/
└── prompts/
    ├── sprint-planning.md
    ├── feature-dev.md
    └── code-review.md

docs/guides/
└── CODY_INTEGRATION.md     # Integration documentation
```

#### Quality Gates

- **E2E Tests:** All tests pass with Cody extension
- **Documentation:** Complete integration guide

---

## Zero-Drift Implementation

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│           SINGLE SOURCE OF TRUTH                             │
│  framework/agents/*.md, framework/workflows/*.md (frontmatter)│
└──────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ MCP Server      │ │ CODY.md         │ │ settings.json   │
│ (from goose)    │ │ Generator       │ │ Generator       │
└─────────────────┘ └─────────────────┘ └─────────────────┘
          │               │               │
          └───────────────┼───────────────┘
                          ▼
             ┌───────────────────────────┐
             │  .cody/                    │
             │  ├── CODY.md              │
             │  ├── settings.json        │
             │  └── .checksums.json      │
             └───────────────────────────┘
```

### Checksum Validation

```python
# .cody/.checksums.json
{
  "version": "1.0.0",
  "generated_at": "2025-11-23T19:00:00Z",
  "generator": "vibey-cody-adapter",
  "checksums": {
    "CODY.md": "a1b2c3d4e5f6g7h8",
    "settings.json": "i9j0k1l2m3n4o5p6"
  },
  "validation_command": "vibey export cody --validate"
}
```

### CI Integration

```yaml
# .github/workflows/cody-drift-check.yml
name: Cody Drift Check

on: [push, pull_request]

jobs:
  validate-cody:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Vibey
        run: pip install -e .

      - name: Validate Cody Export
        run: vibey export cody --validate

      - name: Fail on Drift
        if: failure()
        run: |
          echo "ERROR: Cody artifacts have drifted from source!"
          echo "Regenerate with: vibey deploy --platform cody"
          exit 1
```

---

## Risk Assessment

### High Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Cody MCP support stability | Integration may break | Monitor Sourcegraph changelog, maintain compatibility tests |
| Enterprise-only dependency | Limited user base | Clear documentation on Enterprise requirement |
| July 2025 transition | User confusion | Document Amp migration path |

### Medium Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| No programmatic Prompt Library API | Manual prompt creation | Provide template files for copy/paste |
| OpenCtx experimental status | Feature may change | Isolate OpenCtx-specific code |
| VS Code primary focus | JetBrains users excluded | Document VS Code requirement |

### Low Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Cody extension updates | Minor compatibility issues | Regular testing with latest extension |

---

## Success Metrics

### Quality Gates

| Gate | Threshold | Blocking |
|------|-----------|----------|
| Zero-Drift Validation | 100% | Yes |
| MCP Tool Parity | 100% (all 46 tools) | Yes |
| Unit Test Coverage | >90% | Yes |
| E2E Tests Passing | 100% | Yes |
| Documentation Complete | 100% | No |

### User-Facing Metrics

| Metric | Target |
|--------|--------|
| Deploy time | <30 seconds |
| MCP connection latency | <1 second |
| Context file generation | <5 seconds |
| Tool discovery | <2 seconds |

---

## Timeline

```
┌─────────────────────────────────────────────────────────────────┐
│ Track: cody-port                                                 │
│ Duration: 5 weeks (reduced from original 6)                      │
│ Priority: LOW → MEDIUM (after July 2025 transition)             │
│ Timeline: Q2 2026 (after Cody Enterprise stabilizes)            │
└─────────────────────────────────────────────────────────────────┘

Week 1-3:   Sprint 1 - Core Adapter & MCP Configuration
Week 4-5:   Sprint 2 - Enterprise Features & Documentation

Parallel:   Monitor Cody/Amp transition throughout 2025
```

---

## Dependencies

### Required (Completed)

- [x] `multi-platform` track - Adapter pattern foundation
- [x] `mcp-server` track - MCP server implementation
- [x] `goose-port` track - Frontmatter discovery infrastructure
- [x] `gemini-port` track - Context generator patterns

### Optional

- [ ] `continue-port` track - Similar VS Code extension patterns

---

## Appendix: Key Sources

### Research Sources

1. [Cody MCP Support Announcement](https://sourcegraph.com/blog/cody-supports-anthropic-model-context-protocol)
2. [Cody Commands Documentation](https://sourcegraph.com/docs/cody/capabilities/commands)
3. [OpenCtx Context Providers](https://sourcegraph.com/docs/cody/capabilities/openctx)
4. [Cody Prompts Library](https://sourcegraph.com/docs/cody/capabilities/prompts)
5. [Cody Plan Changes (July 2025)](https://sourcegraph.com/blog/changes-to-cody-free-pro-and-enterprise-starter-plans)
6. [MCP Example Clients](https://modelcontextprotocol.io/clients)

### Related Vibey Documentation

- `/Users/fredabood/Repositories/vibey/framework/mcp/server.py` - MCP server implementation
- `/Users/fredabood/Repositories/vibey/vibey/adapters/base.py` - Base adapter class
- `/Users/fredabood/Repositories/vibey/vibey/adapters/gemini/adapter.py` - Reference implementation
- `/Users/fredabood/Repositories/vibey/vibey/adapters/gemini/context_generator.py` - Context generation patterns

---

**Document Version:** 1.0
**Last Updated:** 2025-11-23
**Author:** Vibey Framework Team
