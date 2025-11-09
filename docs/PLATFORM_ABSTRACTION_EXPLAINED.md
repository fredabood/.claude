# How Vibey Abstracts Multi-Platform Agentic Tooling

**Question:** Claude uses agents/workflows/handoffs, Goose uses recipes/extensions, Cursor has separate terms - how does Vibey abstract all of this in a way that makes it easy to deploy and manage deployments across platforms?

**Answer:** Platform-agnostic metadata + Platform-specific adapters = Write once, deploy everywhere.

---

## The Core Problem

Each AI coding platform has different terminology and file formats:

| Concept | Claude Code | Goose | Cursor |
|---------|-------------|-------|--------|
| **Specialized Agent** | `agents/*.md` | `extensions/*.toml` | `agents/*.md` or inline |
| **Structured Workflow** | `workflows/*.md` | `recipes/*.yaml` | Rules in `.cursorrules` |
| **Agent Handoff** | Templates in Markdown | Recipe steps | Context switching |
| **Main Instructions** | `CLAUDE.md` | `README.md` | `.cursorrules` |
| **Deployment Directory** | `.claude/` | `.goose/` | `.cursor/` |

**Without abstraction:** You'd need to maintain 3 separate codebases!

---

## Vibey's Solution: 3-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Layer 1: Platform-Agnostic Metadata             │
│                  (.vibey/config/)                       │
│                                                         │
│  agent:                                                 │
│    id: web-developer                                    │
│    name: "Web Developer"                                │
│    capabilities: [frontend, backend]                    │
│    trigger_patterns: [...]                              │
│                                                         │
│  ⬆ Generic YAML - No platform-specific details         │
└─────────────────────────────────────────────────────────┘
                          │
                          │ Platform Adapters
                          ▼
┌─────────────┬─────────────────┬──────────────────────┐
│   Layer 2:  │   Platform      │   Transformation      │
│   Adapters  │   Logic         │   Rules              │
├─────────────┼─────────────────┼──────────────────────┤
│ Claude      │ - agents/*.md   │ YAML → Markdown      │
│ Adapter     │ - CLAUDE.md     │ Jinja2 templates     │
│             │ - .claude/      │ Fallback generation  │
├─────────────┼─────────────────┼──────────────────────┤
│ Goose       │ - extensions/   │ YAML → TOML          │
│ Adapter     │ - recipes/      │ Different templates  │
│             │ - .goose/       │ Recipe format        │
├─────────────┼─────────────────┼──────────────────────┤
│ Cursor      │ - .cursorrules  │ YAML → Rules format  │
│ Adapter     │ - agents/       │ Inline instructions  │
│             │ - .cursor/      │ Special formatting   │
└─────────────┴─────────────────┴──────────────────────┘
                          │
                          │ Generate
                          ▼
┌─────────────────────────────────────────────────────────┐
│      Layer 3: Platform-Specific Deployments             │
│              (Generated, Gitignored)                    │
│                                                         │
│  .claude/          .goose/           .cursor/          │
│  ├── CLAUDE.md     ├── README.md     ├── .cursorrules  │
│  ├── agents/       ├── extensions/   └── agents/       │
│  │   └── web-      │   └── web-                        │
│  │      developer  │      developer                    │
│  │      .md        │      .toml                        │
│  └── workflows/    └── recipes/                        │
│                                                         │
│  ⬆ Platform-specific - Never manually edited           │
└─────────────────────────────────────────────────────────┘
```

---

## Layer 1: Platform-Agnostic Metadata

### What It Is
Pure metadata in YAML format that describes agents, workflows, and configurations **without any platform-specific details**.

### Example: Agent Configuration

```yaml
# .vibey/config/agents/web-developer.yaml
agent:
  id: web-developer
  name: "Web Developer"
  role: development
  description: "Full-stack web development agent"

capabilities:
  - frontend_development
  - backend_apis
  - database_design

technologies:
  frameworks: [react, fastapi, express]
  databases: [postgresql, mongodb]

trigger_patterns:
  - pattern: "build.*frontend"
    priority: 80
  - pattern: "api.*endpoint"
    priority: 70

inputs:
  required:
    - name: feature_spec
      type: string
    - name: codebase_path
      type: directory

outputs:
  handoff_template: "feature-implementation-complete"

quality_criteria:
  - name: "Code coverage"
    threshold: 80
    blocking: true
```

### Example: Workflow Configuration

```yaml
# .vibey/config/workflows/feature-development.yaml
workflow:
  id: feature-development
  name: "Single Feature Development"
  type: development

steps:
  - name: "Requirements Analysis"
    agent_recommendations: [researcher, product-manager]
    duration: "30 minutes"

  - name: "Implementation"
    agent_recommendations: [web-developer, backend-specialist]
    duration: "2-4 hours"

  - name: "Testing"
    agent_recommendations: [test-engineer]
    duration: "1 hour"

  - name: "Security Review"
    agent_recommendations: [security-reviewer]
    duration: "30 minutes"
    quality_gate: security_audit
```

**Key Benefits:**
- ✅ Platform-neutral
- ✅ Human-readable
- ✅ Version-controlled
- ✅ Single source of truth

---

## Layer 2: Platform Adapters

### What They Do
Transform generic metadata into platform-specific formats using templates and generation logic.

### Base Adapter Interface

```python
class PlatformAdapter(ABC):
    """
    Abstract base class for all platform adapters.

    Each platform (Claude, Goose, Cursor) implements this interface
    to transform generic configs into platform-specific deployments.
    """

    @abstractmethod
    def get_platform_name(self) -> str:
        """Platform identifier (e.g., 'claude-code', 'goose')"""
        pass

    @abstractmethod
    def get_deployment_dir(self) -> Path:
        """Deployment directory (e.g., .claude/, .goose/)"""
        pass

    @abstractmethod
    def get_instructions_filename(self) -> str:
        """Main instructions file (e.g., CLAUDE.md, README.md)"""
        pass

    @abstractmethod
    def generate_agent_file(self, agent_config: Dict) -> str:
        """Transform agent YAML → platform-specific format"""
        pass

    @abstractmethod
    def generate_workflow_file(self, workflow_config: Dict) -> str:
        """Transform workflow YAML → platform-specific format"""
        pass

    # Utility methods provided by base class
    def load_all_agents(self) -> List[Dict]:
        """Load all agents from .vibey/config/agents/"""
        pass

    def render_template(self, template_name: str, context: Dict) -> str:
        """Render Jinja2 template with context"""
        pass

    def deploy(self, clean=True, validate=True, backup=True):
        """Generate complete deployment"""
        pass
```

### Claude Code Adapter

```python
class ClaudeAdapter(PlatformAdapter):
    """Generates .claude/ deployment for Claude Code"""

    def get_platform_name(self) -> str:
        return "claude-code"

    def get_deployment_dir(self) -> Path:
        return Path(".claude")

    def get_instructions_filename(self) -> str:
        return "CLAUDE.md"

    def get_agents_dirname(self) -> str:
        return "agents"  # .claude/agents/

    def get_workflows_dirname(self) -> str:
        return "workflows"  # .claude/workflows/

    def generate_agent_file(self, agent_config: Dict) -> str:
        """
        Transform agent YAML → Markdown

        Input: .vibey/config/agents/web-developer.yaml
        Output: .claude/agents/web-developer.md (Markdown)
        """
        return self.render_template('agent.md.j2', {
            'agent': agent_config['agent'],
            'platform': 'claude-code'
        })

    def generate_workflow_file(self, workflow_config: Dict) -> str:
        """
        Transform workflow YAML → Markdown

        Input: .vibey/config/workflows/feature-development.yaml
        Output: .claude/workflows/feature-development.md
        """
        return self.render_template('workflow.md.j2', {
            'workflow': workflow_config['workflow']
        })
```

### Goose Adapter (Conceptual)

```python
class GooseAdapter(PlatformAdapter):
    """Generates .goose/ deployment for Goose"""

    def get_platform_name(self) -> str:
        return "goose"

    def get_deployment_dir(self) -> Path:
        return Path(".goose")

    def get_instructions_filename(self) -> str:
        return "README.md"

    def get_agents_dirname(self) -> str:
        return "extensions"  # .goose/extensions/

    def get_workflows_dirname(self) -> str:
        return "recipes"  # .goose/recipes/

    def get_agent_filename(self, agent_id: str) -> str:
        return f"{agent_id}.toml"  # Different format!

    def get_workflow_filename(self, workflow_id: str) -> str:
        return f"{workflow_id}.yaml"  # Different format!

    def generate_agent_file(self, agent_config: Dict) -> str:
        """
        Transform agent YAML → TOML

        Input: .vibey/config/agents/web-developer.yaml
        Output: .goose/extensions/web-developer.toml (TOML)
        """
        return self.render_template('goose_extension.toml.j2', {
            'agent': agent_config['agent'],
            'platform': 'goose'
        })

    def generate_workflow_file(self, workflow_config: Dict) -> str:
        """
        Transform workflow YAML → Goose Recipe YAML

        Input: .vibey/config/workflows/feature-development.yaml
        Output: .goose/recipes/feature-development.yaml (Recipe format)
        """
        return self.render_template('goose_recipe.yaml.j2', {
            'workflow': workflow_config['workflow']
        })
```

### Cursor Adapter (Conceptual)

```python
class CursorAdapter(PlatformAdapter):
    """Generates .cursor/ deployment for Cursor"""

    def get_platform_name(self) -> str:
        return "cursor"

    def get_deployment_dir(self) -> Path:
        return Path(".cursor")

    def get_instructions_filename(self) -> str:
        return ".cursorrules"

    def generate_instructions_file(self) -> str:
        """
        Generate .cursorrules file

        Cursor uses a single file with all rules, unlike Claude/Goose
        which use separate agent files.
        """
        agents = self.load_all_agents()
        workflows = self.load_all_workflows()

        # Combine all into .cursorrules format
        return self.render_template('cursorrules.j2', {
            'agents': agents,
            'workflows': workflows,
            'project': self.load_project_config()
        })

    def generate_agent_file(self, agent_config: Dict) -> str:
        """
        Generate agent-specific rules

        Cursor might inline agents into .cursorrules OR
        use separate agent files - adapter decides!
        """
        return self.render_template('cursor_agent.md.j2', {
            'agent': agent_config['agent']
        })
```

---

## Layer 3: Platform-Specific Deployments

### Generated Artifacts

Each adapter generates platform-specific file structures:

#### Claude Code (.claude/)
```
.claude/
├── CLAUDE.md                    # Main instructions (Markdown)
├── agents/
│   ├── web-developer.md         # Agent instructions (Markdown)
│   ├── security-reviewer.md
│   └── test-engineer.md
├── workflows/
│   ├── feature-development.md   # Workflow instructions (Markdown)
│   └── sprint-planning.md
└── settings.local.json          # Claude-specific settings
```

#### Goose (.goose/)
```
.goose/
├── README.md                    # Main instructions (Markdown)
├── extensions/
│   ├── web-developer.toml       # Agent extensions (TOML)
│   ├── security-reviewer.toml
│   └── test-engineer.toml
└── recipes/
    ├── feature-development.yaml # Workflow recipes (YAML)
    └── sprint-planning.yaml
```

#### Cursor (.cursor/)
```
.cursor/
├── .cursorrules                 # All-in-one rules file
└── agents/
    ├── web-developer.md         # Optional separate agents
    └── security-reviewer.md
```

### Key Properties

✅ **Generated** - Never manually edited
✅ **Gitignored** - Not committed to version control
✅ **Disposable** - Can be regenerated anytime
✅ **Platform-Specific** - Optimized for each platform

---

## The Magic: Template System

### How It Works

1. **Load metadata** from `.vibey/config/`
2. **Render templates** with platform-specific logic
3. **Generate files** in deployment directory

### Example Template: agent.md.j2 (Claude)

```jinja2
# {{ agent.name }}

**Agent ID:** {{ agent.id }}
**Role:** {{ agent.role }}

{{ agent.description }}

---

## Capabilities

{% for capability in agent.capabilities %}
- {{ capability | title | replace('_', ' ') }}
{% endfor %}

---

## Technologies

{% if agent.technologies.frameworks %}
**Frameworks:**
{% for framework in agent.technologies.frameworks %}
- {{ framework }}
{% endfor %}
{% endif %}

{% if agent.technologies.databases %}
**Databases:**
{% for database in agent.technologies.databases %}
- {{ database }}
{% endfor %}
{% endif %}

---

## Trigger Patterns

This agent activates when requests match:

{% for trigger in agent.trigger_patterns %}
- Pattern: `{{ trigger.pattern }}` (Priority: {{ trigger.priority }})
  {{ trigger.description }}
{% endfor %}

---

## Quality Criteria

Before completion, ensure:

{% for criterion in agent.quality_criteria %}
- **{{ criterion.name }}**: {{ criterion.description }}
  - Threshold: {{ criterion.threshold }}%
  - Blocking: {{ "Yes" if criterion.blocking else "No" }}
{% endfor %}

---

*Generated by Vibey Agent Framework for {{ platform }}*
```

### Example Template: goose_extension.toml.j2 (Goose)

```jinja2
[extension]
name = "{{ agent.name }}"
id = "{{ agent.id }}"
version = "{{ agent.version }}"
description = "{{ agent.description }}"

[capabilities]
{% for capability in agent.capabilities %}
{{ capability }} = true
{% endfor %}

[technologies]
frameworks = {{ agent.technologies.frameworks | tojson }}
databases = {{ agent.technologies.databases | tojson }}

[[triggers]]
{% for trigger in agent.trigger_patterns %}
pattern = "{{ trigger.pattern }}"
priority = {{ trigger.priority }}
description = "{{ trigger.description }}"
{% endfor %}

[quality_gates]
{% for criterion in agent.quality_criteria %}
[quality_gates.{{ criterion.name | lower | replace(' ', '_') }}]
threshold = {{ criterion.threshold }}
blocking = {{ criterion.blocking | lower }}
{% endfor %}
```

**Same metadata, different output!** This is the power of the adapter pattern.

---

## Usage: Write Once, Deploy Everywhere

### Single Command Deployment

```bash
# Deploy to Claude Code
./vibey deploy --platform claude-code

# Deploy to Goose
./vibey deploy --platform goose

# Deploy to Cursor
./vibey deploy --platform cursor

# Deploy to ALL platforms
./vibey deploy --platform claude-code
./vibey deploy --platform goose
./vibey deploy --platform cursor
```

### What Happens

```
Input:  .vibey/config/agents/web-developer.yaml (120 lines)

Output: .claude/agents/web-developer.md       (250 lines, Markdown)
        .goose/extensions/web-developer.toml  (180 lines, TOML)
        .cursor/agents/web-developer.md       (200 lines, Rules)
```

**One source → Three deployments!**

---

## Benefits of This Architecture

### 1. **Single Source of Truth**
- Edit `.vibey/config/` once
- Automatically reflected in all platforms
- No drift between deployments

### 2. **Platform Independence**
- Add new platform? Just create an adapter
- No changes to core configs needed
- Future-proof

### 3. **Maintenance Efficiency**
- Update one YAML file
- Regenerate all deployments
- Consistent across platforms

### 4. **Version Control Friendly**
- Only commit `.vibey/config/` (small YAML files)
- Deployments are gitignored (generated artifacts)
- Clean git history

### 5. **Easy Migration**
- Moving from Claude → Goose?
- Just run: `./vibey deploy --platform goose`
- Done!

---

## Real-World Example

### Scenario: Add Security Agent

**Step 1:** Create metadata (once)
```yaml
# .vibey/config/agents/security-reviewer.yaml
agent:
  id: security-reviewer
  name: "Security Reviewer"
  capabilities:
    - owasp_top_10_analysis
    - dependency_scanning
    - secrets_detection
```

**Step 2:** Deploy to all platforms
```bash
./vibey deploy --platform claude-code  # → .claude/agents/security-reviewer.md
./vibey deploy --platform goose        # → .goose/extensions/security-reviewer.toml
./vibey deploy --platform cursor       # → Added to .cursor/.cursorrules
```

**Result:** Agent works identically across all 3 platforms!

---

## Extensibility: Adding New Platforms

### Create Aider Adapter (Hypothetical)

```python
class AiderAdapter(PlatformAdapter):
    """Support for Aider (hypothetical)"""

    def get_platform_name(self) -> str:
        return "aider"

    def get_deployment_dir(self) -> Path:
        return Path(".aider")

    def get_instructions_filename(self) -> str:
        return "AIDER_INSTRUCTIONS.md"

    # Implement generation methods...
```

**Register it:**
```python
# framework/platform_adapters/registry.py
from .aider_adapter import AiderAdapter
AdapterRegistry.register('aider', AiderAdapter)
```

**Use it:**
```bash
./vibey deploy --platform aider
```

**That's it!** No changes to configs, no changes to core framework.

---

## Summary

### How Vibey Abstracts Multi-Platform Tooling

1. **Generic Metadata** - Store concepts (agents, workflows) as pure YAML
2. **Platform Adapters** - Transform metadata to platform-specific formats
3. **Template System** - Jinja2 templates customize output per platform
4. **Registry Pattern** - Easy to add new platforms
5. **CLI Interface** - `./vibey deploy --platform <name>` does everything

### The Result

✅ **Write once** - Single set of configs in `.vibey/config/`
✅ **Deploy anywhere** - Claude, Goose, Cursor, future platforms
✅ **Consistent behavior** - Same agents/workflows across platforms
✅ **Easy maintenance** - Update once, regenerate everywhere
✅ **Future-proof** - New platforms via adapter pattern

**This is how Vibey achieves true platform-agnostic agentic orchestration!** 🚀
