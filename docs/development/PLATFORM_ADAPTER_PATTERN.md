# Platform Adapter Pattern

**Document Version:** 1.0
**Created:** 2025-11-09
**Sprint:** core-framework-2, Task 5
**Status:** Active Design Document

---

## Overview

The Platform Adapter Pattern enables Vibey to support multiple AI coding platforms (Claude Code, Goose, Cursor) from a single platform-agnostic codebase.

**Key Concept:** `.vibey/` is the source of truth → Adapters generate platform-specific deployments

```
.vibey/config/          Platform Adapters          Platform Deployments
├── project.yaml   ──→  ClaudeAdapter  ──→  .claude/CLAUDE.md
├── framework.yaml  ──→  GooseAdapter   ──→  .goose/README.md
├── agents/         ──→  CursorAdapter  ──→  .cursor/.cursorrules
└── workflows/
```

---

## Design Rationale

### Problem

Each AI coding platform has unique requirements:

**Claude Code:**
- Main file: `CLAUDE.md`
- Agents: `agents/*.md` (Markdown)
- Workflows: `workflows/*.md` (Markdown)
- Location: `.claude/` directory

**Goose:**
- Main file: `README.md`
- Agents: `extensions/*.toml` (TOML)
- Workflows: `recipes/*.yaml` (YAML)
- Location: `.goose/` directory

**Cursor:**
- Main file: `.cursorrules` (special format)
- Agents: `agents/*.md` (Markdown)
- Location: `.cursor/` directory

**Without adapters:** Would need separate codebases or massive if/else branching.

### Solution

**Adapter Pattern:**
1. Define common `PlatformAdapter` interface
2. Each platform implements the interface
3. Core framework unchanged
4. Add new platforms easily

---

## PlatformAdapter Interface

### Base Class

```python
from framework.platform_adapters.base import PlatformAdapter

class MyPlatformAdapter(PlatformAdapter):
    """Adapter for MyPlatform"""

    def get_platform_name(self) -> str:
        return "myplatform"

    def get_deployment_dir(self) -> Path:
        return Path(".myplatform")

    def get_instructions_filename(self) -> str:
        return "INSTRUCTIONS.md"

    def generate_instructions_file(self) -> str:
        # Load configs
        project = self.load_project_config()
        framework = self.load_framework_config()
        agents = self.load_all_agents()
        workflows = self.load_all_workflows()

        # Render template
        return self.render_template("myplatform.md.j2", {
            "project": project,
            "framework": framework,
            "agents": agents,
            "workflows": workflows
        })

    def generate_agent_file(self, agent_config: Dict) -> str:
        return self.render_template("agent.md.j2", {
            "agent": agent_config
        })

    def generate_workflow_file(self, workflow_config: Dict) -> str:
        return self.render_template("workflow.md.j2", {
            "workflow": workflow_config
        })
```

### Required Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `get_platform_name()` | Platform identifier | String (e.g., "claude-code") |
| `get_deployment_dir()` | Deployment directory | Path (e.g., `.claude/`) |
| `get_instructions_filename()` | Main instructions file | String (e.g., "CLAUDE.md") |
| `generate_instructions_file()` | Generate main instructions | String (file content) |
| `generate_agent_file(config)` | Generate agent file | String (file content) |
| `generate_workflow_file(config)` | Generate workflow file | String (file content) |

### Optional Methods (Can Override)

| Method | Default | Override For |
|--------|---------|--------------|
| `get_agent_filename(agent_id)` | `{agent_id}.md` | Different naming (e.g., `.toml`) |
| `get_workflow_filename(workflow_id)` | `{workflow_id}.md` | Different naming (e.g., `.yaml`) |
| `get_agents_dirname()` | `"agents"` | Different directory name (e.g., `"extensions"`) |
| `get_workflows_dirname()` | `"workflows"` | Different directory name (e.g., `"recipes"`) |

### Utility Methods (Provided)

| Method | Purpose |
|--------|---------|
| `load_project_config()` | Load `.vibey/config/project.yaml` |
| `load_framework_config()` | Load `.vibey/config/framework.yaml` |
| `load_agent_config(agent_id)` | Load specific agent config |
| `load_all_agents()` | Load all agent configs |
| `load_workflow_config(workflow_id)` | Load specific workflow config |
| `load_all_workflows()` | Load all workflow configs |
| `load_quality_gates()` | Load quality gates config |
| `render_template(name, context)` | Render Jinja2 template |
| `deploy(clean, validate, backup)` | Generate complete deployment |
| `validate_config()` | Validate configuration |

---

## Usage

### Basic Deployment

```python
from framework.platform_adapters import ClaudeAdapter

# Create adapter
adapter = ClaudeAdapter()

# Generate deployment
adapter.deploy()

# Output:
# 📝 Generating CLAUDE.md...
# 🤖 Generating 12 agent(s)...
# 📋 Generating 16 workflow(s)...
# ✅ Deployment generated at: .claude/
```

### Advanced Options

```python
# Don't clean existing deployment
adapter.deploy(clean=False)

# Skip validation
adapter.deploy(validate=False)

# Don't backup before overwriting
adapter.deploy(backup=False)

# All options
adapter.deploy(clean=True, validate=True, backup=True)
```

### Multi-Platform Deployment

```python
from framework.platform_adapters import ClaudeAdapter, GooseAdapter

# Deploy to Claude Code
claude = ClaudeAdapter()
claude.deploy()

# Deploy to Goose
goose = GooseAdapter()
goose.deploy()

# Now you have both .claude/ and .goose/ deployments!
```

---

## Platform-Specific Examples

### Claude Code Adapter

```python
class ClaudeAdapter(PlatformAdapter):
    """Adapter for Claude Code platform"""

    def get_platform_name(self) -> str:
        return "claude-code"

    def get_deployment_dir(self) -> Path:
        return Path(".claude")

    def get_instructions_filename(self) -> str:
        return "CLAUDE.md"

    def generate_instructions_file(self) -> str:
        """Generate CLAUDE.md from template"""
        project = self.load_project_config()
        framework = self.load_framework_config()
        agents = self.load_all_agents()
        workflows = self.load_all_workflows()
        quality_gates = self.load_quality_gates()

        return self.render_template("claude.md.j2", {
            "project": project,
            "framework": framework,
            "agents": agents,
            "workflows": workflows,
            "quality_gates": quality_gates,
            # Claude-specific context
            "platform": "claude-code",
            "instructions_type": "markdown"
        })

    def generate_agent_file(self, agent_config: Dict) -> str:
        """Generate agent/*.md file"""
        return self.render_template("agent.md.j2", {
            "agent": agent_config
        })

    def generate_workflow_file(self, workflow_config: Dict) -> str:
        """Generate workflow/*.md file"""
        return self.render_template("workflow.md.j2", {
            "workflow": workflow_config
        })

    # Uses default naming: agents/*.md, workflows/*.md
```

### Goose Adapter

```python
class GooseAdapter(PlatformAdapter):
    """Adapter for Goose platform"""

    def get_platform_name(self) -> str:
        return "goose"

    def get_deployment_dir(self) -> Path:
        return Path(".goose")

    def get_instructions_filename(self) -> str:
        return "README.md"

    def get_agents_dirname(self) -> str:
        return "extensions"  # Goose uses "extensions" not "agents"

    def get_workflows_dirname(self) -> str:
        return "recipes"  # Goose uses "recipes" not "workflows"

    def get_agent_filename(self, agent_id: str) -> str:
        return f"{agent_id}.toml"  # Goose uses TOML for extensions

    def get_workflow_filename(self, workflow_id: str) -> str:
        return f"{workflow_id}.yaml"  # Goose uses YAML for recipes

    def generate_instructions_file(self) -> str:
        """Generate README.md for Goose"""
        project = self.load_project_config()
        framework = self.load_framework_config()
        agents = self.load_all_agents()
        workflows = self.load_all_workflows()

        return self.render_template("goose.md.j2", {
            "project": project,
            "framework": framework,
            "agents": agents,
            "workflows": workflows,
            # Goose-specific context
            "platform": "goose",
            "mcp_enabled": True  # Goose supports MCP
        })

    def generate_agent_file(self, agent_config: Dict) -> str:
        """Generate extension TOML file"""
        # Convert agent config to TOML format
        import toml

        agent = agent_config.get('agent', {})
        toml_config = {
            "extension": {
                "name": agent.get('name'),
                "id": agent.get('id'),
                "description": agent.get('description'),
                "version": agent.get('version', '1.0.0')
            },
            "capabilities": agent_config.get('capabilities', []),
            "technologies": agent_config.get('technologies', {})
        }

        return toml.dumps(toml_config)

    def generate_workflow_file(self, workflow_config: Dict) -> str:
        """Generate recipe YAML file"""
        import yaml

        # Goose recipes are already YAML
        return yaml.dump(workflow_config, default_flow_style=False)
```

### Cursor Adapter

```python
class CursorAdapter(PlatformAdapter):
    """Adapter for Cursor platform"""

    def get_platform_name(self) -> str:
        return "cursor"

    def get_deployment_dir(self) -> Path:
        return Path(".cursor")

    def get_instructions_filename(self) -> str:
        return ".cursorrules"

    def generate_instructions_file(self) -> str:
        """Generate .cursorrules file"""
        project = self.load_project_config()
        framework = self.load_framework_config()
        agents = self.load_all_agents()

        # Cursor uses a special format
        return self.render_template("cursor.rules.j2", {
            "project": project,
            "framework": framework,
            "agents": agents,
            # Cursor-specific
            "format": "cursorrules"
        })

    def generate_agent_file(self, agent_config: Dict) -> str:
        """Generate agent markdown"""
        # Cursor uses Markdown like Claude
        return self.render_template("agent.md.j2", {
            "agent": agent_config
        })

    def generate_workflow_file(self, workflow_config: Dict) -> str:
        """Cursor doesn't have explicit workflows"""
        # Workflows embedded in .cursorrules
        return ""
```

---

## Template System

### Template Structure

```
.vibey/templates/                 # User-customizable templates
├── claude.md.j2                  # Claude Code instructions
├── goose.md.j2                   # Goose instructions
├── cursor.rules.j2               # Cursor instructions
├── agent.md.j2                   # Agent (Markdown platforms)
└── workflow.md.j2                # Workflow (Markdown platforms)

framework/templates/              # Framework default templates (fallback)
├── claude.md.j2
├── goose.md.j2
├── cursor.rules.j2
├── agent.md.j2
└── workflow.md.j2
```

**Template Resolution:**
1. Look in `.vibey/templates/` (user customizations)
2. Fall back to `framework/templates/` (defaults)

### Template Variables

All templates receive:

```python
{
    "project": {
        "name": "My Project",
        "type": "web-app",
        "description": "...",
        "repository": "...",
        # ... from project.yaml
    },
    "framework": {
        "version": "1.2.0",
        "platform": "claude-code",
        "orchestration": { ... },
        # ... from framework.yaml
    },
    "agents": [
        {
            "agent": {
                "id": "web-developer",
                "name": "Web Developer",
                # ...
            },
            "capabilities": [...],
            "technologies": {...},
            # ... from agents/*.yaml
        },
        # ... all agents
    ],
    "workflows": [
        # ... all workflows
    ],
    "quality_gates": {
        # ... from quality-gates.yaml
    }
}
```

### Example Template

**`.vibey/templates/claude.md.j2`:**
```jinja2
# {{ project.project.name }} - Vibey Framework

**Version:** {{ framework.framework.version }}
**Platform:** Claude Code
**Project Type:** {{ project.project.type }}

## Project Description

{{ project.project.description }}

## Agents Available

{% for agent_config in agents %}
### {{ agent_config.agent.name }}

**ID:** {{ agent_config.agent.id }}
**Role:** {{ agent_config.agent.role }}

**Capabilities:**
{% for capability in agent_config.capabilities %}
- {{ capability }}
{% endfor %}

{% endfor %}

## Workflows

{% for workflow_config in workflows %}
### {{ workflow_config.workflow.name }}

{{ workflow_config.workflow.description }}

{% endfor %}

## Quality Gates

{% if quality_gates.quality_gates %}
{% for gate in quality_gates.quality_gates %}
- **{{ gate.name }}:** {{ gate.description }} (threshold: {{ gate.threshold }}%)
{% endfor %}
{% endif %}
```

---

## Adding a New Platform

### Step 1: Create Adapter Class

```python
# framework/platform_adapters/myplatform.py

from .base import PlatformAdapter
from pathlib import Path
from typing import Dict

class MyPlatformAdapter(PlatformAdapter):
    """Adapter for MyPlatform"""

    def get_platform_name(self) -> str:
        return "myplatform"

    def get_deployment_dir(self) -> Path:
        return Path(".myplatform")

    def get_instructions_filename(self) -> str:
        return "INSTRUCTIONS.md"

    def generate_instructions_file(self) -> str:
        # Implementation
        pass

    def generate_agent_file(self, agent_config: Dict) -> str:
        # Implementation
        pass

    def generate_workflow_file(self, workflow_config: Dict) -> str:
        # Implementation
        pass
```

### Step 2: Create Templates

Create `.vibey/templates/myplatform.md.j2` (or use framework defaults)

### Step 3: Register Adapter

```python
# framework/platform_adapters/__init__.py

from .base import PlatformAdapter
from .myplatform import MyPlatformAdapter

__all__ = ['PlatformAdapter', 'MyPlatformAdapter']
```

### Step 4: Test

```python
from framework.platform_adapters import MyPlatformAdapter

adapter = MyPlatformAdapter()
adapter.deploy()
```

### Step 5: Document

Add platform-specific documentation to `docs/platforms/myplatform.md`

---

## Benefits

### 1. Platform Agnostic Core

**✅ Benefit:** Core framework unchanged when adding platforms

```python
# Core framework code never mentions specific platforms
# It only knows about PlatformAdapter interface
def deploy_to_platform(platform_name: str):
    adapter = get_adapter_for_platform(platform_name)
    adapter.deploy()
```

### 2. Easy Platform Addition

**✅ Benefit:** New platforms = implement interface + create template

**Lines of code to add platform:**
- Adapter class: ~100-200 lines
- Template: ~50-100 lines
- **Total:** ~150-300 lines

Compare to: Forking entire codebase or massive if/else branching

### 3. User Customization

**✅ Benefit:** Users can customize templates without touching code

```bash
# User creates custom template
cp framework/templates/claude.md.j2 .vibey/templates/claude.md.j2

# Edit .vibey/templates/claude.md.j2
# Custom template now used automatically!
```

### 4. Multi-Platform Support

**✅ Benefit:** Deploy to multiple platforms simultaneously

```bash
vibey deploy --all
# or
vibey deploy --platforms claude-code,goose,cursor
```

### 5. Testability

**✅ Benefit:** Each adapter independently testable

```python
def test_claude_adapter():
    adapter = ClaudeAdapter()
    assert adapter.get_platform_name() == "claude-code"
    assert adapter.get_deployment_dir() == Path(".claude")
    # ...
```

---

## Design Patterns Used

### 1. Adapter Pattern (Primary)

**Purpose:** Convert `.vibey/config/` interface to platform-specific interface

**Participants:**
- **Target:** Platform-specific deployment structure
- **Adaptee:** `.vibey/config/` (platform-agnostic configs)
- **Adapter:** `ClaudeAdapter`, `GooseAdapter`, etc.
- **Client:** Deployment system

### 2. Template Method Pattern

**Purpose:** Define deployment algorithm, let subclasses customize steps

**In `PlatformAdapter.deploy()`:**
1. Backup (if requested)
2. Clean (if requested)
3. Create deployment directory
4. Generate instructions file ← **subclass customizes**
5. Generate agents ← **subclass customizes**
6. Generate workflows ← **subclass customizes**

### 3. Strategy Pattern

**Purpose:** Choose deployment strategy at runtime

```python
# Strategy selected based on platform
adapters = {
    "claude-code": ClaudeAdapter,
    "goose": GooseAdapter,
    "cursor": CursorAdapter
}

adapter_class = adapters[platform_name]
adapter = adapter_class()
adapter.deploy()
```

---

## Future Extensions

### 1. Plugin System

Allow third-party platform adapters:

```python
# User's custom adapter
# ~/.vibey/plugins/myplatform.py

from vibey.platform_adapters import PlatformAdapter

class MyPlatformAdapter(PlatformAdapter):
    # ...
```

```bash
vibey plugin register ~/.vibey/plugins/myplatform.py
vibey deploy --platform myplatform
```

### 2. Validation Framework

```python
class PlatformAdapter(ABC):
    def validate_deployment(self) -> bool:
        """Validate generated deployment"""
        pass

# Each platform defines validation
class ClaudeAdapter(PlatformAdapter):
    def validate_deployment(self) -> bool:
        # Check CLAUDE.md exists
        # Check agents/*.md exist
        # Validate Markdown syntax
        # ...
```

### 3. Deployment Diffing

```python
adapter.deploy_preview()  # Show what would change
adapter.deploy_diff()     # Show diff vs existing deployment
```

### 4. Incremental Deployment

```python
# Only regenerate changed files
adapter.deploy(incremental=True)
```

---

## Summary

**Platform Adapter Pattern enables:**

✅ **Multi-platform support** from single codebase
✅ **Easy platform addition** (implement interface + template)
✅ **User customization** via templates
✅ **Platform agnostic core** (no if/else branching)
✅ **Independent testing** of each adapter
✅ **Future extensibility** (plugins, validation, diffing)

**Next Steps:**
- Task 6: Implement Claude Code adapter
- Task 7: Implement `vibey deploy` command
- Task 8: Implement `vibey docs generate` command

---

**Document Status:** ✅ Active Design Document
**Last Updated:** 2025-11-09
**Next Review:** After Task 6 completion
