# Vibey Config Schema Design

**Version:** 1.0.0
**Created:** 2025-11-10
**Sprint:** directory-migration-2, Task 001

This directory contains the schema definitions for Vibey's modular configuration system.

---

## Overview

The new modular config system splits the monolithic `.claude/project-config.yaml` into four focused configuration files:

1. **project.yaml** - Project-specific information
2. **framework.yaml** - Vibey framework settings
3. **agents.yaml** - Agent selection and configuration
4. **quality-gates.yaml** - Quality gate definitions

---

## Directory Structure

```
.vibey/
├── config/
│   ├── project.yaml          # Project info (name, type, tech stack)
│   ├── framework.yaml         # Framework settings (orchestration, features)
│   ├── agents.yaml            # Agent configuration (enabled, preferences)
│   └── quality-gates.yaml     # Quality gates (thresholds, checks)
└── roadmap/                   # Roadmap system (unchanged)
```

---

## Configuration Files

### 1. project.yaml

**Purpose:** Core project information and tech stack

**Fields:**
- `project.name` - Project name
- `project.version` - Current version
- `project.type` - Project type (web-app, api, library, ml, etc.)
- `project.description` - Brief description
- `project.repository` - Git repository URL
- `tech_stack.languages` - Programming languages
- `tech_stack.frameworks` - Frameworks and libraries
- `tech_stack.databases` - Databases
- `tech_stack.infrastructure` - Infrastructure tools
- `paths.*` - Important project paths

**Example:**
```yaml
project:
  name: "my-web-app"
  version: "1.0.0"
  type: "web-app"
  description: "Modern task management app"

tech_stack:
  languages: ["typescript", "python"]
  frameworks: ["react", "fastapi"]
  databases: ["postgresql"]
```

---

### 2. framework.yaml

**Purpose:** Vibey framework configuration

**Fields:**
- `framework.version` - Framework version
- `framework.orchestration_mode` - simple | balanced | tiered
- `framework.sprint_state_enabled` - Enable sprint tracking
- `framework.project_context_enabled` - Enable PROJECT-CONTEXT.md
- `deployment.platforms` - Target platforms (claude-code, goose, etc.)
- `deployment.auto_deploy` - Auto-deploy on updates
- `features.*` - Feature flags (roadmap, docs, audit, etc.)

**Example:**
```yaml
framework:
  version: "2.5.0"
  orchestration_mode: "balanced"
  sprint_state_enabled: true

deployment:
  platforms: ["claude-code"]

features:
  roadmap_system: true
  documentation_generation: true
```

---

### 3. agents.yaml

**Purpose:** Agent selection and preferences

**Fields:**
- `agents.enabled` - List of enabled agents
- `agents.disabled` - Explicitly disabled agents
- `agent_preferences.<agent>.priority` - Priority (1-10)
- `agent_preferences.<agent>.auto_trigger` - Allow auto-triggering
- `agent_preferences.<agent>.custom_prompts` - Prompt overrides

**Example:**
```yaml
agents:
  enabled:
    - "coordinator"
    - "web-developer"
    - "test-engineer"
    - "docs-writer"

agent_preferences:
  web-developer:
    priority: 9
    auto_trigger: true

  security-engineer:
    priority: 10
    auto_trigger: false  # Manual only
```

---

### 4. quality-gates.yaml

**Purpose:** Quality gate configuration

**Fields:**
- `quality_gates.enabled` - Enable quality gates
- `quality_gates.mode` - strict | balanced | permissive
- `gates.security.*` - Security gate configuration
- `gates.testing.*` - Testing gate configuration
- `gates.logging.*` - Logging gate configuration
- `gates.documentation.*` - Documentation gate configuration
- `gates.performance.*` - Performance gate configuration

**Example:**
```yaml
quality_gates:
  enabled: true
  mode: "balanced"

gates:
  security:
    enabled: true
    threshold: 95
    blocking: true

  testing:
    enabled: true
    coverage_threshold: 80
    blocking: true
```

---

## Migration Strategy

### From Legacy Config

The legacy `.claude/project-config.yaml` will be split as follows:

**project.yaml ← Legacy Fields:**
- `project.*` → `project.*`
- `tech_stack.*` → `tech_stack.*`
- `paths.*` → `paths.*`

**framework.yaml ← Legacy Fields:**
- `vibey.version` → `framework.version`
- `vibey.orchestration_mode` → `framework.orchestration_mode`
- `vibey.features.*` → `features.*`

**agents.yaml ← Legacy Fields:**
- `agents.available` → `agents.enabled`
- Custom agent config → `agent_preferences.*`

**quality-gates.yaml ← Legacy Fields:**
- `quality_gates.*` → `gates.*`

### Auto-Migration

When Vibey detects `.claude/project-config.yaml` but not `.vibey/config/`, it will:

1. Create `.vibey/config/` directory
2. Parse legacy config
3. Split into modular files
4. Validate all configs
5. Create backup of original
6. Show migration summary

---

## Design Principles

### 1. Separation of Concerns
Each config file has a single, well-defined purpose.

### 2. Backward Compatibility
Legacy config continues to work with deprecation warnings.

### 3. Validation
All configs validated against schemas using Pydantic.

### 4. Progressive Enhancement
Start with minimal config, add fields as needed.

### 5. Clear Defaults
Sensible defaults for all optional fields.

---

## Validation

Configs will be validated using Pydantic models:

```python
from vibey.config.models import ProjectConfig, FrameworkConfig

# Load and validate
config = ProjectConfig.from_yaml('.vibey/config/project.yaml')
```

Validation includes:
- Type checking
- Required field checking
- Enum validation
- Pattern matching (e.g., version format)
- Range validation (e.g., priority 1-10)

---

## Benefits

### For Users
- **Clarity:** Each file has clear purpose
- **Simplicity:** Smaller, focused files easier to edit
- **Flexibility:** Can update parts independently
- **Discoverability:** Clear what options are available

### For Framework
- **Modularity:** Load only needed configs
- **Validation:** Granular validation per component
- **Extensibility:** Easy to add new config types
- **Maintainability:** Changes isolated to relevant files

---

## Future Extensions

Possible additional config files:

- **workflows.yaml** - Custom workflow definitions
- **templates.yaml** - Template configurations
- **integrations.yaml** - Third-party integrations
- **notifications.yaml** - Notification settings

---

## Schema Version

All schemas use semantic versioning:

- **Major:** Breaking changes (require migration)
- **Minor:** New fields (backward compatible)
- **Patch:** Documentation/clarifications only

Current: **1.0.0**

---

## See Also

- [DIRECTORY_MIGRATION_PLAN.md](../../../docs/development/DIRECTORY_MIGRATION_PLAN.md)
- [Migration Tool Implementation](../../cli/migrate-config.py) (Sprint 2, Task 004)
- [Config Models](../models.py) (Sprint 2, Task 002)
- [Config Loader](../loader.py) (Sprint 2, Task 003)

---

**Last Updated:** 2025-11-10
**Sprint:** directory-migration-2
**Task:** 001 - Design modular config schema
