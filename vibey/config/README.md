# Vibey Configuration System

**Version:** 1.0.0
**Created:** 2025-11-10
**Sprint:** directory-migration-2, Task 002

This package provides Pydantic models for the Vibey modular configuration system.

---

## Overview

The Vibey configuration system uses 4 separate YAML files for different concerns:

```
.vibey/config/
├── project.yaml          # Project-specific info
├── framework.yaml         # Framework settings
├── agents.yaml            # Agent configuration
└── quality-gates.yaml     # Quality gate definitions
```

Each file has a corresponding Pydantic model for validation and type safety.

---

## Quick Start

### Loading Individual Configs

```python
from vibey.config import ProjectConfig, FrameworkConfig, AgentsConfig, QualityGatesConfig

# Load project config
project = ProjectConfig.from_yaml(".vibey/config/project.yaml")
print(f"Project: {project.project.name} v{project.project.version}")
print(f"Type: {project.project.type.value}")

# Load framework config
framework = FrameworkConfig.from_yaml(".vibey/config/framework.yaml")
print(f"Orchestration: {framework.framework.orchestration_mode.value}")

# Load agents config
agents = AgentsConfig.from_yaml(".vibey/config/agents.yaml")
print(f"Enabled agents: {len(agents.agents.enabled)}")

# Load quality gates config
qg = QualityGatesConfig.from_yaml(".vibey/config/quality-gates.yaml")
print(f"Security threshold: {qg.gates.security.threshold}%")
```

### Loading All Configs Together

```python
from vibey.config import VibeyConfig

# Load all configs from directory
config = VibeyConfig.from_directory(".vibey/config")

# Access individual configs
print(config.project.project.name)
print(config.framework.framework.orchestration_mode.value)
print(config.agents.agents.enabled)
print(config.quality_gates.gates.security.threshold)
```

### Creating and Saving Configs

```python
from vibey.config import (
    ProjectConfig, Project, TechStack, ProjectType,
    FrameworkConfig, Framework, OrchestrationMode
)

# Create project config
project = ProjectConfig(
    project=Project(
        name="my-app",
        version="1.0.0",
        type=ProjectType.WEB_APP,
        description="My awesome app"
    ),
    tech_stack=TechStack(
        languages=["python", "typescript"],
        frameworks=["fastapi", "react"]
    )
)

# Save to file
project.to_yaml(".vibey/config/project.yaml")

# Create framework config
framework = FrameworkConfig(
    framework=Framework(
        version="2.5.0",
        orchestration_mode=OrchestrationMode.BALANCED
    )
)
framework.to_yaml(".vibey/config/framework.yaml")
```

---

## Configuration Models

### ProjectConfig

**Purpose:** Project-specific information

**Fields:**
- `project.name` - Project name (required)
- `project.version` - Semantic version (required, pattern: `\d+.\d+.\d+`)
- `project.type` - Project type enum (required)
- `project.description` - Description (optional)
- `project.repository` - Git repo URL (optional)
- `tech_stack.languages` - Programming languages (required, min 1)
- `tech_stack.frameworks` - Frameworks/libraries (optional)
- `tech_stack.databases` - Databases (optional)
- `tech_stack.infrastructure` - Infrastructure tools (optional)
- `paths.source` - Source directory (default: "src")
- `paths.tests` - Test directory (default: "tests")
- `paths.docs` - Docs directory (default: "docs")
- `paths.config` - Config directory (default: ".vibey/config")

**Enums:**
- `ProjectType`: web-app, api, library, ml, data-platform, infrastructure

---

### FrameworkConfig

**Purpose:** Vibey framework settings

**Fields:**
- `framework.version` - Framework version (required)
- `framework.orchestration_mode` - Agent orchestration (required)
- `framework.sprint_state_enabled` - Enable sprint tracking (default: true)
- `framework.project_context_enabled` - Enable PROJECT-CONTEXT.md (default: true)
- `deployment.platforms` - Target platforms (default: ["claude-code"])
- `deployment.auto_deploy` - Auto-deploy updates (default: false)
- `deployment.deployment_dir` - Deployment directory (default: ".claude")
- `features.roadmap_system` - Enable roadmap (default: true)
- `features.documentation_generation` - Enable auto docs (default: true)
- `features.codebase_audit` - Enable audit (default: true)
- `features.git_history_analysis` - Enable git analysis (default: true)

**Enums:**
- `OrchestrationMode`: simple, balanced, tiered

---

### AgentsConfig

**Purpose:** Agent selection and preferences

**Fields:**
- `agents.enabled` - List of enabled agents (required, min 1)
- `agents.disabled` - List of disabled agents (optional)
- `agent_preferences.<agent>.priority` - Priority 1-10 (optional)
- `agent_preferences.<agent>.auto_trigger` - Allow auto-trigger (default: true)
- `agent_preferences.<agent>.custom_prompts` - Custom prompts (optional)

---

### QualityGatesConfig

**Purpose:** Quality gate definitions

**Fields:**
- `quality_gates.enabled` - Enable quality gates (required)
- `quality_gates.mode` - Enforcement mode (default: "balanced")
- `gates.security.enabled` - Enable gate (default: true)
- `gates.security.threshold` - Pass threshold 0-100 (default: 95)
- `gates.security.blocking` - Block if failed (default: true)
- `gates.security.checks` - Security checks to run (optional)
- `gates.testing.coverage_threshold` - Min coverage % (default: 80)
- `gates.logging.threshold` - Logging threshold (default: 90)
- `gates.documentation.threshold` - Docs threshold (default: 85)
- `gates.performance.enabled` - Enable performance gate (default: false)

**Enums:**
- `QualityGateMode`: strict, balanced, permissive

---

## Validation

All configs are validated using Pydantic. Invalid data will raise `ValidationError`:

```python
from pydantic import ValidationError
from vibey.config import ProjectConfig

try:
    config = ProjectConfig.from_yaml("invalid.yaml")
except ValidationError as e:
    print(e)
    # ValidationError: 1 validation error for ProjectConfig
    # project.version
    #   String should match pattern '^\d+\.\d+\.\d+$'
```

### Validation Rules

**ProjectConfig:**
- `version` must match pattern `^\d+\.\d+\.\d+$`
- `type` must be valid `ProjectType` enum
- `languages` must have at least 1 item

**FrameworkConfig:**
- `orchestration_mode` must be valid enum
- `platforms` defaults to `["claude-code"]`

**AgentsConfig:**
- `enabled` must have at least 1 agent
- `priority` must be 1-10 (inclusive)

**QualityGatesConfig:**
- `threshold` values must be 0-100
- `mode` must be valid enum

---

## Type Safety

All models provide full type hints:

```python
from vibey.config import ProjectConfig, ProjectType

config: ProjectConfig = ProjectConfig.from_yaml("project.yaml")

# IDE autocomplete and type checking
name: str = config.project.name
version: str = config.project.version
project_type: ProjectType = config.project.type  # Enum
languages: list[str] = config.tech_stack.languages
```

---

## Examples

Complete example configs are available in `vibey/config/examples/`:

- `project.yaml` - Web app example
- `framework.yaml` - Balanced orchestration
- `agents.yaml` - Common agent setup
- `quality-gates.yaml` - Balanced quality gates

Copy and customize these for your project.

---

## Migration from Legacy Config

The old `.claude/project-config.yaml` monolithic file will be split into 4 files:

**project.yaml** ← Legacy fields:
- `project.*` → `project.*`
- `tech_stack.*` → `tech_stack.*`
- `paths.*` → `paths.*`

**framework.yaml** ← Legacy fields:
- `vibey.version` → `framework.version`
- `vibey.orchestration_mode` → `framework.orchestration_mode`
- `vibey.features.*` → `features.*`

**agents.yaml** ← Legacy fields:
- `agents.available` → `agents.enabled`

**quality-gates.yaml** ← Legacy fields:
- `quality_gates.*` → `gates.*`

A migration tool will be available in Sprint 2, Task 004.

---

## API Reference

### VibeyConfig

```python
class VibeyConfig(BaseModel):
    """Unified configuration for all Vibey modules."""

    project: ProjectConfig
    framework: FrameworkConfig
    agents: AgentsConfig
    quality_gates: QualityGatesConfig

    @classmethod
    def from_directory(cls, config_dir: str | Path) -> VibeyConfig:
        """Load all configs from directory."""
        ...

    def to_directory(self, config_dir: str | Path) -> None:
        """Save all configs to directory."""
        ...
```

### Individual Config Models

All config models (ProjectConfig, FrameworkConfig, AgentsConfig, QualityGatesConfig) provide:

```python
@classmethod
def from_yaml(cls, path: str | Path) -> ConfigModel:
    """Load configuration from YAML file."""
    ...

def to_yaml(self, path: str | Path) -> None:
    """Save configuration to YAML file."""
    ...
```

---

## Error Handling

```python
from pathlib import Path
from pydantic import ValidationError
from vibey.config import VibeyConfig

try:
    config = VibeyConfig.from_directory(".vibey/config")
except FileNotFoundError as e:
    print(f"Config file not found: {e}")
except ValidationError as e:
    print(f"Invalid configuration: {e}")
    # Shows which fields are invalid and why
```

---

## See Also

- [Schema Documentation](schemas/README.md) - Detailed schema design
- [Migration Plan](../../docs/development/DIRECTORY_MIGRATION_PLAN.md) - Overall migration strategy
- [Sprint 2 Tasks](.vibey/roadmap/directory-migration/directory-migration-2/) - Implementation roadmap

---

**Last Updated:** 2025-11-10
**Sprint:** directory-migration-2
**Task:** 002 - Create config models (Pydantic/dataclasses)
