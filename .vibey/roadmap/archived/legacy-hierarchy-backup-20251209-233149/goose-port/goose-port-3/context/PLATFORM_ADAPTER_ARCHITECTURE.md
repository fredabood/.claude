# Platform Adapter Architecture

> **Sprint 3 Design Document**
> **Created:** 2025-11-22
> **Status:** Complete

## Overview

The Platform Adapter Architecture enables zero-drift translation of Vibey assets (agents, workflows, handoffs) to any platform's native format. This design ensures:

1. **Single Source of Truth** - YAML frontmatter in markdown files
2. **Zero Drift** - All platforms read from the same source
3. **Extensibility** - Adding a new platform = implementing one adapter class
4. **Composition** - Composite adapters build on base adapters without duplication
5. **CLI ↔ MCP Parity** - Both interfaces delegate to `vibey.operations.roadmap`

## Critical Architecture Decision: Shared Operations Library

**Problem:** The MCP server originally had its own implementation of roadmap operations,
creating drift risk between CLI and MCP interfaces.

**Solution:** The MCP adapter now delegates ALL operations to `vibey.operations.roadmap`,
the same library used by the CLI:

```
vibey/operations/roadmap/    ← SINGLE SOURCE OF TRUTH
├── query.py                 │
├── update.py                │
├── init.py                  │
└── ...                      │
         ↓                   │
    ┌────┴────┐              │
    ↓         ↓              │
   CLI       MCP Server      │
(vibey/cli)  (framework/mcp) │
```

This guarantees that `vibey roadmap status` and `vibey_roadmap_status` (MCP tool)
produce identical results.

## Architecture Diagram

```
                     Vibey Assets (Source of Truth)
                     ┌────────────────────────────┐
                     │  framework/agents/*.md      │
                     │  framework/workflows/*.md   │
                     │  templates/handoffs/*.md    │
                     │  (with YAML frontmatter)    │
                     └─────────────┬──────────────┘
                                   │
                                   ▼
                     ┌────────────────────────────┐
                     │      Asset Registry         │
                     │  (parsed, validated, cached)│
                     │  - 19 agents                │
                     │  - 16 workflows             │
                     │  - 22 handoffs              │
                     └─────────────┬──────────────┘
                                   │
                                   ▼
                     ┌────────────────────────────┐
                     │   Platform Adapter System   │
                     └─────────────┬──────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              │                                        │
       Base Adapters                          Composite Adapters
    (translate directly)                   (build on base adapters)
              │                                        │
    ┌─────────┼─────────┬─────────┐                    │
    ▼         ▼         ▼         ▼                    ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐         ┌───────────┐
│  MCP  │ │Cursor │ │Claude │ │ Aider │         │   Goose   │
│Adapter│ │Adapter│ │ Code  │ │Adapter│         │  Adapter  │
│       │ │       │ │Adapter│ │       │         │           │
└───┬───┘ └───────┘ └───────┘ └───────┘         └─────┬─────┘
    │                                                  │
    │              ┌───────────────────────────────────┘
    │              │ composes
    │              ▼
    │         ┌─────────┐
    └────────►│MCPAdapter│
              └─────────┘
```

## Adapter Types

### BaseAdapter

Base adapters translate directly from the Asset Registry to platform-specific formats.

```python
class BaseAdapter(ABC):
    """
    Base class for adapters that translate directly from assets.

    Examples: MCPAdapter, CursorAdapter, AiderAdapter
    """

    def __init__(self, registry: AssetRegistry):
        self.registry = registry

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Unique platform identifier."""

    @property
    @abstractmethod
    def platform_display_name(self) -> str:
        """Human-readable platform name."""

    @abstractmethod
    def translate_agent(self, agent: AgentDefinition) -> Any:
        """Convert agent to platform-native format."""

    @abstractmethod
    def translate_workflow(self, workflow: WorkflowDefinition) -> Any:
        """Convert workflow to platform-native format."""

    @abstractmethod
    def export(self, output_dir: Path) -> ExportResult:
        """Export all assets to platform format."""

    def get_capabilities(self) -> Dict[str, bool]:
        """Return what this adapter supports."""
        return {
            "agents": True,
            "workflows": True,
            "handoffs": False,
            "real_time": False,
        }
```

### CompositeAdapter

Composite adapters build on top of base adapters, adding platform-specific features.

```python
class CompositeAdapter(ABC):
    """
    Base class for adapters that compose other adapters.

    Examples: GooseAdapter (uses MCPAdapter), JetBrainsAdapter (uses MCPAdapter)
    """

    def __init__(self, base_adapter: BaseAdapter, registry: AssetRegistry):
        self.base = base_adapter
        self.registry = registry

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Unique platform identifier."""

    @property
    def base_platform(self) -> str:
        """The base adapter this composite uses."""
        return self.base.platform_name

    # Delegate common operations to base adapter
    def get_tools(self) -> List[Dict]:
        """Delegate tool generation to base adapter."""
        if hasattr(self.base, 'get_tools'):
            return self.base.get_tools()
        raise NotImplementedError("Base adapter doesn't support tools")
```

## Adapter Implementations

### MCPAdapter (Base)

The canonical source for MCP tool generation.

**Inputs:** Asset Registry (agents, workflows)
**Outputs:** MCP tool definitions

```python
class MCPAdapter(BaseAdapter):
    platform_name = "mcp"
    platform_display_name = "Model Context Protocol"

    def get_tools(self) -> List[Dict]:
        """Generate MCP tools from all assets."""
        tools = []
        for agent in self.registry.agents:
            tools.append(self._agent_to_tool(agent))
        for workflow in self.registry.workflows:
            tools.append(self._workflow_to_tool(workflow))
        return tools

    def _agent_to_tool(self, agent: AgentDefinition) -> Dict:
        return {
            "name": f"vibey_{agent.id.replace('-', '_')}",
            "description": agent.description,
            "inputSchema": self._build_input_schema(agent.inputs),
            "_metadata": {"asset_type": "agent", "asset_id": agent.id}
        }
```

### GooseAdapter (Composite)

Composes MCPAdapter for tools, adds Goose-specific features.

**Inputs:** MCPAdapter, Asset Registry
**Outputs:** MCP tools (via MCPAdapter), Goose recipes, Extension manifest

```python
class GooseAdapter(CompositeAdapter):
    platform_name = "goose"
    platform_display_name = "Goose (Block)"

    def __init__(self, mcp_adapter: MCPAdapter, registry: AssetRegistry):
        super().__init__(mcp_adapter, registry)
        self.recipe_generator = RecipeGenerator(registry)
        self.manifest_generator = ManifestGenerator()

    def get_tools(self) -> List[Dict]:
        """Delegate to MCPAdapter - no duplication."""
        return self.base.get_tools()

    def get_recipes(self) -> List[Dict]:
        """Generate Goose recipes from workflows."""
        return self.recipe_generator.generate_all()

    def get_extension_manifest(self) -> Dict:
        """Generate Goose extension manifest."""
        return self.manifest_generator.generate(
            tools_count=len(self.get_tools())
        )

    def export(self, output_dir: Path) -> ExportResult:
        """Export Goose-specific files."""
        files = []

        # Export recipes
        recipes_dir = output_dir / "recipes"
        recipes_dir.mkdir(parents=True, exist_ok=True)
        for recipe in self.get_recipes():
            path = recipes_dir / f"{recipe['id']}.yaml"
            path.write_text(yaml.dump(recipe))
            files.append(path)

        # Export extension manifest
        manifest_path = output_dir / "goose-extension.yaml"
        manifest_path.write_text(yaml.dump(self.get_extension_manifest()))
        files.append(manifest_path)

        return ExportResult(platform="goose", files=files)
```

## Recipe Generation

Goose recipes are generated from workflow frontmatter. Each workflow step references an MCP tool.

### Workflow Frontmatter → Goose Recipe

**Input (workflow frontmatter):**
```yaml
---
id: feature-development
name: Feature Development Workflow
type: development
version: "1.0.0"
description: Complete feature from planning to deployment
steps:
  - order: 1
    name: Planning
    agent: sprint-planner
    description: Create implementation plan
  - order: 2
    name: Implementation
    agent: web-developer
    description: Implement the feature
  - order: 3
    name: Testing
    agent: test-engineer
    description: Write and run tests
  - order: 4
    name: Documentation
    agent: docs-writer
    description: Update documentation
quality_gates:
  - name: test_coverage
    type: percentage
    threshold: 80
---
```

**Output (Goose recipe):**
```yaml
name: Feature Development Workflow
description: Complete feature from planning to deployment
version: "1.0.0"

steps:
  - name: Planning
    tool: vibey_sprint_planner
    description: Create implementation plan

  - name: Implementation
    tool: vibey_web_developer
    description: Implement the feature

  - name: Testing
    tool: vibey_test_engineer
    description: Write and run tests

  - name: Documentation
    tool: vibey_docs_writer
    description: Update documentation

quality_gates:
  - name: test_coverage
    threshold: 80
    blocking: true
```

### Key Mapping Rules

| Workflow Field | Recipe Field | Transformation |
|---------------|--------------|----------------|
| `id` | `id` | Direct copy |
| `name` | `name` | Direct copy |
| `description` | `description` | Direct copy |
| `steps[].agent` | `steps[].tool` | `vibey_{agent_id}` |
| `steps[].name` | `steps[].name` | Direct copy |
| `quality_gates` | `quality_gates` | Direct copy |

## Extension Manifest

The extension manifest registers Vibey as a Goose extension.

```yaml
# goose-extension.yaml (auto-generated)
name: vibey
version: "1.0.0"
type: mcp
description: |
  Vibey Agent Framework - Intelligent agent orchestration for AI coding assistants.
  Provides 35 tools covering planning, development, quality, and documentation.

mcp:
  command: python -m framework.mcp.server
  args:
    - --roadmap-root
    - .vibey/roadmap

capabilities:
  tools: 35
  agents: 19
  workflows: 16

categories:
  - development
  - planning
  - quality
  - documentation
```

## Adapter Registry

Central management of all platform adapters.

```python
class AdapterRegistry:
    """Registry for discovering and managing platform adapters."""

    def __init__(self):
        self._adapters: Dict[str, BaseAdapter | CompositeAdapter] = {}

    def register(self, adapter: BaseAdapter | CompositeAdapter) -> None:
        """Register an adapter."""
        self._adapters[adapter.platform_name] = adapter

    def get(self, platform: str) -> Optional[BaseAdapter | CompositeAdapter]:
        """Get adapter by platform name."""
        return self._adapters.get(platform)

    def list_platforms(self) -> List[str]:
        """List all registered platform names."""
        return list(self._adapters.keys())

    def export_all(self, output_dir: Path) -> Dict[str, ExportResult]:
        """Export to all platforms."""
        results = {}
        for name, adapter in self._adapters.items():
            results[name] = adapter.export(output_dir / name)
        return results
```

## CLI Integration

```bash
# Export to specific platform
vibey export --platform goose --output ./exports

# Export to all platforms
vibey export --platform all --output ./exports

# List available platforms
vibey export --list-platforms

# Preview what would be exported (dry run)
vibey export --platform goose --dry-run
```

## Adding a New Platform

To add support for a new platform:

### 1. Determine Adapter Type

- **BaseAdapter**: Platform has its own unique format (e.g., Cursor's .cursorrules)
- **CompositeAdapter**: Platform uses MCP + adds features (e.g., JetBrains)

### 2. Implement the Adapter

```python
# For a new base adapter (e.g., Cursor)
class CursorAdapter(BaseAdapter):
    platform_name = "cursor"
    platform_display_name = "Cursor"

    def translate_agent(self, agent: AgentDefinition) -> str:
        """Convert agent to .cursorrules section."""
        return f"""
## {agent.name}
{agent.description}

Trigger: {', '.join(agent.triggers.get('keywords', []))}
"""

    def export(self, output_dir: Path) -> ExportResult:
        rules = self._generate_cursorrules()
        path = output_dir / ".cursorrules"
        path.write_text(rules)
        return ExportResult(platform="cursor", files=[path])
```

### 3. Register the Adapter

```python
# In framework/adapters/__init__.py
registry = AdapterRegistry()
registry.register(MCPAdapter(asset_registry))
registry.register(GooseAdapter(mcp_adapter, asset_registry))
registry.register(CursorAdapter(asset_registry))  # New!
```

### 4. Test and Document

- Add unit tests for the new adapter
- Add integration tests with the actual platform
- Document platform-specific configuration

## File Structure

```
framework/
├── adapters/
│   ├── __init__.py           # Registry and exports
│   ├── base.py               # BaseAdapter, CompositeAdapter ABCs
│   ├── registry.py           # AdapterRegistry
│   ├── types.py              # ExportResult, common types
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── adapter.py        # MCPAdapter
│   ├── goose/
│   │   ├── __init__.py
│   │   ├── adapter.py        # GooseAdapter
│   │   ├── recipes.py        # RecipeGenerator
│   │   └── manifest.py       # ManifestGenerator
│   └── cursor/               # Future
│       ├── __init__.py
│       └── adapter.py
├── discovery/                # Shared asset discovery
│   ├── __init__.py
│   ├── registry.py           # AssetRegistry
│   ├── parser.py             # FrontmatterParser
│   ├── agents.py             # AgentDefinition
│   └── workflows.py          # WorkflowDefinition
└── mcp/
    └── server.py             # MCP server (uses adapters/mcp/)
```

## Platform Configuration

### Goose Configuration

Add to `~/.config/goose/config.yaml`:

```yaml
extensions:
  vibey:
    args:
    - /path/to/vibey/scripts/run-mcp-server.py
    bundled: null
    cmd: /path/to/vibey/.venv/bin/python
    description: Vibey Agent Framework - 46 tools for planning, development, quality, and documentation
    enabled: true
    env_keys: []
    envs: {}
    name: vibey
    timeout: 300
    type: stdio
```

### Claude Code Configuration

Create `.mcp.json` at project root:

```json
{
  "mcpServers": {
    "vibey": {
      "command": "/path/to/vibey/.venv/bin/python",
      "args": ["/path/to/vibey/scripts/run-mcp-server.py"]
    }
  }
}
```

After adding, restart Claude Code to load the MCP server.

### Testing Integration

Both platforms should see 46 tools:
- 19 agent tools (vibey_web_developer, vibey_test_engineer, etc.)
- 16 workflow tools (vibey_feature_development, vibey_sprint_planning, etc.)
- 11 roadmap management tools (vibey_roadmap_status, vibey_create_task, etc.)

## Benefits

1. **Zero Drift**: All platforms read from same frontmatter source
2. **No Duplication**: Composite adapters delegate to base adapters
3. **Easy Extension**: New platform = one adapter class
4. **Testable**: Each adapter can be unit tested independently
5. **Predictable**: Clear mapping rules from assets to platform formats
6. **Platform Agnostic**: Same MCP server works with Goose, Claude Code, and future clients
