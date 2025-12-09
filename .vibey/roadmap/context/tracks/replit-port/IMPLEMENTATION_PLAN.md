# Replit Platform Port - Implementation Plan

**Track ID:** `replit-port`
**Created:** 2025-11-23
**Status:** Planning
**Priority:** Medium-High (Education market potential)

---

## Executive Summary

This document outlines the implementation plan for porting the Vibey Agent Framework to Replit's platform. Replit presents unique opportunities and challenges as a **web-based, cloud-native development environment** targeting education and rapid prototyping markets.

### Compatibility Assessment: 70-80%

**Key Advantages:**
- Native MCP support (Replit has shipped MCP integration)
- Python runtime support in browser
- Extensions API for custom tooling
- Agent 3 architecture with multi-agent capabilities

**Key Challenges:**
- Web-based environment (no local filesystem)
- Different extension paradigm (JavaScript-based Extensions vs. markdown agents)
- Browser sandbox limitations
- No programmatic Agent invocation API (yet)

---

## Research Findings

### 1. Replit Platform Architecture

#### Agent Architecture (Agent 3 - 2025)
Source: [Replit Agent Documentation](https://docs.replit.com/replitai/agent)

Replit uses a **multi-agent architecture** internally:
- **Manager Agent**: Oversees workflow, breaks tasks into steps
- **Editor Agents**: Handle specific coding tasks
- **Verifier Agent**: Checks code and gathers user feedback

Key capabilities:
- Can operate for up to 200 minutes continuously
- Self-testing and debugging loops
- **Can spawn new agents** from natural language descriptions
- Integrates with Slack, email, Telegram for automations

#### MCP Integration
Sources: [Replit MCP Guide](https://blog.replit.com/everything-you-need-to-know-about-mcp), [MCP Tutorial](https://docs.replit.com/tutorials/mcp-in-3)

- Replit has **native MCP support** - one of the first major platforms
- MCP Template available for quick setup (5-minute install)
- Supports Python, TypeScript, Java MCP servers
- Real-time access to project context via MCP

#### Extensions System
Sources: [Replit Extensions Documentation](https://docs.replit.com/extensions/extensions), [Extensions API Reference](https://docs.replit.com/extensions/category/api-reference)

Extensions provide three main capabilities:
1. **Tools**: Custom UI panels/tabs
2. **File Handlers**: Custom file editors
3. **Commands**: Actions in command palette (CLUI)

**API Features:**
- JavaScript library with React bindings and TypeScript support
- Authentication integration
- Background Scripts (persistent while workspace open)
- Filesystem access (create, read, modify files)
- Exec (execute shell commands)
- Repldb (key-value store)
- Data API (GraphQL access)
- Themes integration

**Current Limitation:** No programmatic Agent invocation API - extensions cannot trigger Replit Agent with a prompt (feature request exists).

### 2. Configuration Format

Source: [Replit App Configuration](https://docs.replit.com/replit-app/configuration)

**.replit file (TOML format):**
```toml
# Basic structure
entrypoint = "main.py"
modules = ["python-3.11"]
language = "python"
hidden = [".git", ".config"]

# Run command
run = "python main.py"
# Or with args
run = ["python", "main.py", "--verbose"]

# With environment variables
[run]
args = ["python", "main.py"]

[run.env]
VIBEY_ROOT = ".vibey"

# Extension configuration
[extension]
isExtension = true
extensionID = "vibey-agent-framework"
buildCommand = "npm run build"
outputDirectory = "dist"

# Deployment settings
[deployment]
run = ["python", "-m", "framework.mcp.server"]
build = "pip install -r requirements.txt"
```

**replit.nix:** System dependencies via Nix package manager

### 3. Environment Constraints

**Browser-Based Limitations:**
- No direct local filesystem access outside workspace
- Sandboxed Python execution
- Resource limits on free tier (CPU, RAM, storage)
- No GUI access for desktop applications (Tkinter works via browser)

**Advantages:**
- Virtual environment built-in (no venv needed)
- Environment variables via Secrets sidebar
- Full Python library support (pandas, scikit-learn, etc.)
- Git integration built-in

---

## Architecture Decisions

### ADR-1: MCP-First Integration Strategy

**Context:** Replit has native MCP support, making it a strong candidate for Vibey integration.

**Decision:** Use MCP as the primary integration mechanism, similar to Gemini adapter.

**Rationale:**
- Replit MCP support is production-ready
- Existing Vibey MCP server (46 tools) can be reused with minimal changes
- Zero-drift architecture preserved - MCP tools generated from frontmatter
- No need to reimplement agent/workflow logic

**Consequences:**
- Positive: Fast time to market, shared codebase with other ports
- Positive: Automatic updates when frontmatter changes
- Negative: Limited by MCP protocol capabilities

### ADR-2: Extension for Enhanced UX

**Context:** While MCP provides tool access, Replit Extensions can offer richer UI integration.

**Decision:** Create a Vibey Extension that:
1. Provides dashboard/status panels (Tools)
2. Handles .vibey/ file editing (File Handlers)
3. Adds `/vibey` command palette commands (Commands)

**Rationale:**
- Extensions enhance discoverability
- Custom UI for roadmap visualization
- Better onboarding experience for education market

**Consequences:**
- Positive: Superior UX compared to MCP-only approach
- Positive: Visual roadmap and sprint progress
- Negative: Requires JavaScript/React development (new skillset)
- Negative: Extension maintenance overhead

### ADR-3: Context File Generation (REPLIT.md)

**Context:** Replit reads context files similar to other platforms.

**Decision:** Generate `REPLIT.md` (or place in `.gemini/GEMINI.md` if Replit uses that path) from same frontmatter source.

**Rationale:**
- Zero-drift: Generated from `.vibey/` source
- Consistent with Gemini adapter pattern
- Replit may support hierarchical context loading

### ADR-4: Web Environment Handling

**Context:** Vibey CLI assumes local filesystem access.

**Decision:** Implement adapter with web-aware filesystem operations:
1. All paths relative to Replit workspace
2. Use Replit's filesystem API for extension operations
3. MCP server runs within Replit environment (not local)

**Rationale:**
- Replit provides full Python runtime
- MCP server can run as a background process in Repl
- Workspace is the effective "local" filesystem

---

## Web Environment Challenges

### Challenge 1: No Local Installation
**Problem:** Users cannot run `pip install vibey` globally
**Solution:**
- Package as Replit Template (forkable project)
- MCP server included in template
- Alternative: PyPI install within workspace

### Challenge 2: MCP Server Hosting
**Problem:** MCP servers typically run locally
**Solution:**
- Run MCP server within the Repl itself
- Use Replit's background processes
- Configure in `.replit` with always-on deployment

### Challenge 3: CLI Access
**Problem:** Vibey CLI designed for terminal use
**Solution:**
- CLI works in Replit's shell
- Extension provides graphical alternative
- Commands available via Replit's command palette

### Challenge 4: Filesystem Differences
**Problem:** Different path structure than local development
**Solution:**
- Adapter uses relative paths from workspace root
- Environment variable `REPL_HOME` for path resolution
- All `.vibey/` operations scoped to workspace

### Challenge 5: No Programmatic Agent Invocation
**Problem:** Cannot trigger Replit Agent from extension code
**Solution:**
- Provide prompts/instructions for user to paste to Agent
- Use MCP tools which Agent can discover
- Wait for API availability (feature request exists)

---

## Integration Approach

### Phase 1: MCP Server Deployment (Week 1-2)
Enable Vibey MCP server to run within Replit environment.

```
.vibey/
├── config/
├── roadmap/
└── ...

framework/mcp/
└── server.py (existing, reusable)

.replit (configuration)
replit.nix (dependencies)
```

### Phase 2: Replit Adapter Development (Week 3-4)
Create adapter following established patterns.

```
vibey/adapters/replit/
├── __init__.py
├── adapter.py          # Main ReplitAdapter class
├── context_generator.py # REPLIT.md generation
├── extension_generator.py # Extension package generation
└── tests/
    ├── test_adapter.py
    └── test_context_generator.py
```

### Phase 3: Extension Development (Week 5-7)
Build Replit Extension for enhanced UX.

```
replit-extension/
├── manifest.json       # Extension manifest
├── package.json        # Node.js dependencies
├── src/
│   ├── index.tsx       # Main extension entry
│   ├── components/
│   │   ├── Dashboard.tsx
│   │   ├── RoadmapView.tsx
│   │   └── SprintProgress.tsx
│   ├── hooks/
│   │   └── useVibey.ts # React hooks for MCP
│   └── commands/
│       └── vibey.ts    # CLUI commands
└── dist/               # Build output
```

### Phase 4: Template & Documentation (Week 8)
Create forkable template and documentation.

```
vibey-replit-template/
├── .replit
├── replit.nix
├── .vibey/
├── REPLIT.md
├── README.md
└── setup.py
```

---

## Sprint Tasks with File Paths

### Sprint 1: Research & MCP Validation (1 week)

| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| replit-port-1-001 | Validate MCP server runs in Replit | `framework/mcp/server.py` (no changes expected) | 4h |
| replit-port-1-002 | Test tool discovery in Replit env | `.replit`, `replit.nix` | 4h |
| replit-port-1-003 | Document Replit-specific limitations | `.vibey/roadmap/replit-port/context/REPLIT_CONSTRAINTS.md` | 4h |
| replit-port-1-004 | Create minimal .replit configuration | `.replit` (new) | 2h |
| replit-port-1-005 | Test frontmatter parsing in browser Python | `framework/mcp/discovery/parser.py` (validation) | 2h |

### Sprint 2: Adapter Foundation (1.5 weeks)

| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| replit-port-2-001 | Create ReplitAdapter class | `vibey/adapters/replit/adapter.py` | 8h |
| replit-port-2-002 | Implement get_platform_name/get_deployment_dir | `vibey/adapters/replit/adapter.py` | 2h |
| replit-port-2-003 | Implement deploy() method | `vibey/adapters/replit/adapter.py` | 8h |
| replit-port-2-004 | Implement validate_deployment() | `vibey/adapters/replit/adapter.py` | 4h |
| replit-port-2-005 | Create ReplitContextGenerator | `vibey/adapters/replit/context_generator.py` | 6h |
| replit-port-2-006 | Generate REPLIT.md from frontmatter | `vibey/adapters/replit/context_generator.py` | 4h |
| replit-port-2-007 | Unit tests for adapter | `vibey/adapters/replit/tests/test_adapter.py` | 6h |

### Sprint 3: .replit Configuration Generation (1 week)

| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| replit-port-3-001 | Create ReplitConfigGenerator | `vibey/adapters/replit/config_generator.py` | 6h |
| replit-port-3-002 | Generate .replit TOML from vibey config | `vibey/adapters/replit/config_generator.py` | 4h |
| replit-port-3-003 | Generate replit.nix for dependencies | `vibey/adapters/replit/config_generator.py` | 4h |
| replit-port-3-004 | MCP server configuration in .replit | `vibey/adapters/replit/config_generator.py` | 4h |
| replit-port-3-005 | Checksums for drift detection | `vibey/adapters/replit/adapter.py` | 4h |
| replit-port-3-006 | Integration tests | `vibey/adapters/replit/tests/test_config_generator.py` | 4h |

### Sprint 4: Extension Scaffolding (1.5 weeks)

| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| replit-port-4-001 | Initialize extension project | `replit-extension/package.json`, `manifest.json` | 4h |
| replit-port-4-002 | Setup React/TypeScript build | `replit-extension/tsconfig.json`, `webpack.config.js` | 4h |
| replit-port-4-003 | Create useVibey hook for MCP | `replit-extension/src/hooks/useVibey.ts` | 8h |
| replit-port-4-004 | Implement Dashboard component | `replit-extension/src/components/Dashboard.tsx` | 8h |
| replit-port-4-005 | Add CLUI commands | `replit-extension/src/commands/vibey.ts` | 6h |
| replit-port-4-006 | Extension build and bundle | `replit-extension/scripts/build.sh` | 4h |

### Sprint 5: Extension Features (1.5 weeks)

| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| replit-port-5-001 | RoadmapView component | `replit-extension/src/components/RoadmapView.tsx` | 8h |
| replit-port-5-002 | SprintProgress component | `replit-extension/src/components/SprintProgress.tsx` | 6h |
| replit-port-5-003 | TaskList component | `replit-extension/src/components/TaskList.tsx` | 6h |
| replit-port-5-004 | File handler for .vibey/ files | `replit-extension/src/handlers/vibeyFiles.ts` | 6h |
| replit-port-5-005 | Extension settings UI | `replit-extension/src/components/Settings.tsx` | 4h |
| replit-port-5-006 | End-to-end testing in Replit | Manual testing | 6h |

### Sprint 6: Template & Documentation (1 week)

| Task ID | Description | Files | Effort |
|---------|-------------|-------|--------|
| replit-port-6-001 | Create forkable template | `vibey-replit-template/` (new directory) | 6h |
| replit-port-6-002 | Template README | `vibey-replit-template/README.md` | 4h |
| replit-port-6-003 | Quick start guide | `docs/getting-started/REPLIT_QUICK_START.md` | 4h |
| replit-port-6-004 | Extension installation guide | `docs/guides/REPLIT_EXTENSION.md` | 4h |
| replit-port-6-005 | Publish to Replit Templates | Replit platform | 4h |
| replit-port-6-006 | Update FRAMEWORK_ROADMAP.md | `docs/FRAMEWORK_ROADMAP.md` | 2h |

---

## Zero-Drift Implementation

### Source of Truth

All Replit artifacts are generated from `.vibey/` configuration:

```
.vibey/
├── config/
│   ├── project.yaml      # Project metadata
│   ├── framework.yaml    # Framework settings
│   └── agents.yaml       # Agent preferences
├── roadmap/              # Roadmap state
└── ...

framework/
├── agents/*.md           # Agent definitions (frontmatter)
└── workflows/*.md        # Workflow definitions (frontmatter)
```

### Generated Artifacts

| Artifact | Source | Generator |
|----------|--------|-----------|
| `REPLIT.md` | `framework/agents/*.md`, `framework/workflows/*.md` | `ReplitContextGenerator` |
| `.replit` | `.vibey/config/project.yaml` | `ReplitConfigGenerator` |
| `replit.nix` | `.vibey/config/project.yaml` (tech_stack) | `ReplitConfigGenerator` |
| MCP Tools | `framework/agents/*.md`, `framework/workflows/*.md` | `ToolDiscovery` (existing) |
| Extension manifest | `.vibey/config/framework.yaml` | `ReplitExtensionGenerator` |

### Drift Detection

```python
# In vibey/adapters/replit/adapter.py

def validate_export(self, export_dir: Path) -> tuple[bool, List[str]]:
    """Validate exported artifacts haven't drifted from source."""
    errors = []

    checksums_path = export_dir / ".checksums.json"
    if not checksums_path.exists():
        errors.append("Missing .checksums.json - cannot validate")
        return False, errors

    stored = json.loads(checksums_path.read_text())

    # Regenerate from source and compare
    current_context = self.context_generator.generate()
    if stored.get("REPLIT.md") != current_context.checksum:
        errors.append(f"REPLIT.md has drifted from source!")

    # Check .replit config
    current_config = self.config_generator.generate()
    if stored.get(".replit") != current_config.checksum:
        errors.append(f".replit has drifted from source!")

    return len(errors) == 0, errors
```

### CI Validation

```yaml
# .github/workflows/validate-replit.yml
name: Validate Replit Export
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .
      - run: vibey export replit --validate
```

---

## Estimated Timeline

| Sprint | Duration | Milestone |
|--------|----------|-----------|
| Sprint 1 | 1 week | MCP validated in Replit |
| Sprint 2 | 1.5 weeks | Adapter foundation complete |
| Sprint 3 | 1 week | Configuration generation |
| Sprint 4 | 1.5 weeks | Extension scaffolding |
| Sprint 5 | 1.5 weeks | Extension features |
| Sprint 6 | 1 week | Template & docs |
| **Total** | **8 weeks** | **Production ready** |

---

## Risk Assessment

### High Risk
1. **Replit API Changes**: Platform is actively developing; APIs may change
   - Mitigation: Abstract API calls, maintain version compatibility matrix

2. **Extension Approval**: Replit may have review process for Extensions Store
   - Mitigation: Start review process early, have alternative distribution

### Medium Risk
1. **Performance in Browser**: MCP server may be slower than local
   - Mitigation: Optimize tool caching, lazy loading

2. **Feature Gaps**: No programmatic Agent invocation
   - Mitigation: Design around limitation, update when API available

### Low Risk
1. **Python Compatibility**: Different Python environment
   - Mitigation: Test early, use standard library where possible

---

## Success Metrics

1. **Adoption**: 100+ template forks in first month
2. **User Feedback**: 4+ star rating on Extensions Store
3. **Zero Drift**: 0 manual edit incidents in 3 months
4. **Performance**: Tool invocation < 500ms average
5. **Documentation**: Complete tutorial completion rate > 80%

---

## Dependencies

### Internal Dependencies
- `framework/mcp/server.py` (existing MCP server)
- `framework/mcp/discovery/` (frontmatter parsing)
- `vibey/adapters/base.py` (PlatformAdapter interface)

### External Dependencies
- Replit MCP support (shipped)
- Replit Extensions API (available)
- Replit Templates (available)

### Blocked By
- None (can start immediately)

---

## Open Questions

1. **Extension Store Publishing**: What is the review/approval process?
2. **MCP Server Hosting**: Always-on vs. on-demand in Replit?
3. **Context File Location**: Does Replit prefer specific paths for context?
4. **Agent Invocation API**: When will programmatic Agent invocation be available?

---

## References

- [Replit Agent Documentation](https://docs.replit.com/replitai/agent)
- [Replit MCP Guide](https://blog.replit.com/everything-you-need-to-know-about-mcp)
- [Replit Extensions Documentation](https://docs.replit.com/extensions/extensions)
- [Replit App Configuration](https://docs.replit.com/replit-app/configuration)
- [Replit Extensions API Reference](https://docs.replit.com/extensions/category/api-reference)
- [Replit Agent 3 Announcement](https://blog.replit.com/introducing-agent-3-our-most-autonomous-agent-yet)
- [Vibey Gemini Adapter](vibey/adapters/gemini/adapter.py) (reference implementation)
- [Vibey MCP Server](framework/mcp/server.py) (existing infrastructure)

---

*Document Version: 1.0.0*
*Last Updated: 2025-11-23*
*Author: Claude Code / Vibey Framework Team*
