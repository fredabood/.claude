# Vibey Configuration System

**Version:** 2.5.0
**Last Updated:** 2025-11-10

Complete guide to Vibey's modular configuration system.

---

## Overview

Vibey uses a modular configuration system with 4 separate YAML files:

```
.vibey/config/
├── project.yaml          # Project information
├── framework.yaml        # Framework settings
├── agents.yaml           # Agent configuration
└── quality-gates.yaml    # Quality gate rules
```

Each file has a specific purpose, making configuration easier to understand and maintain.

---

## Quick Start

### Creating New Config

```bash
# Initialize new project (creates config automatically)
vibey init

# Or migrate existing config
vibey config migrate
```

### Viewing Config

```bash
# Show current configuration
vibey config show

# Validate configuration
vibey config validate
```

---

## Configuration Files

### 1. project.yaml - Project Information

**Purpose:** Core project metadata and technology stack

**Required fields:**
- `project.name` - Project name
- `project.version` - Semantic version (X.Y.Z)
- `project.type` - Project type
- `tech_stack.languages` - Programming languages (min 1)

**Example:**
```yaml
project:
  name: "my-web-app"
  version: "1.0.0"
  type: "web-app"
  description: "Modern task management application"
  repository: "https://github.com/myorg/my-app"

tech_stack:
  languages:
    - "typescript"
    - "python"
  frameworks:
    - "react"
    - "fastapi"
  databases:
    - "postgresql"
  infrastructure:
    - "docker"

paths:
  source: "src"
  tests: "tests"
  docs: "docs"
```

**Project types:**
- `web-app` - Full-stack web application
- `api` - REST API / microservice
- `library` - Reusable library/package
- `ml` - Machine learning project
- `data-platform` - Data processing platform
- `infrastructure` - Infrastructure as code

---

### 2. framework.yaml - Framework Settings

**Purpose:** Vibey framework configuration

**Required fields:**
- `framework.version` - Framework version
- `framework.orchestration_mode` - Agent orchestration mode

**Example:**
```yaml
framework:
  version: "2.5.0"
  orchestration_mode: "balanced"
  sprint_state_enabled: true
  project_context_enabled: true

deployment:
  platforms:
    - "claude-code"
  auto_deploy: false
  deployment_dir: ".claude"

features:
  roadmap_system: true
  documentation_generation: true
  codebase_audit: true
  git_history_analysis: true
```

**Orchestration modes:**
- `simple` - Explicit agent selection (keyword-based)
- `balanced` - Smart pattern matching (recommended)
- `tiered` - Intelligent coordinator-based routing

---

### 3. agents.yaml - Agent Configuration

**Purpose:** Agent selection and preferences

**Required fields:**
- `agents.enabled` - List of enabled agents (min 1)

**Example:**
```yaml
agents:
  enabled:
    - "coordinator"
    - "web-developer"
    - "test-engineer"
    - "docs-writer"
    - "security-engineer"

  disabled:
    - "ml-engineer"  # Not needed for this project

agent_preferences:
  web-developer:
    priority: 9
    auto_trigger: true

  security-engineer:
    priority: 10
    auto_trigger: false  # Manual review only

  docs-writer:
    priority: 6
    auto_trigger: true
```

**Agent priority:** 1-10 (10 = highest)

**Available agents:**
- `coordinator` - Routes complex requests
- `web-developer` - Full-stack development
- `test-engineer` - Testing and QA
- `security-engineer` - Security audits
- `performance-engineer` - Performance optimization
- `docs-writer` - Documentation
- `ml-engineer` - Machine learning
- `sprint-planner` - Sprint planning

---

### 4. quality-gates.yaml - Quality Gates

**Purpose:** Quality gate rules and thresholds

**Required fields:**
- `quality_gates.enabled` - Enable/disable gates
- `quality_gates.mode` - Enforcement mode

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
    checks:
      - "dependency-scan"
      - "code-scan"
      - "secrets-scan"

  testing:
    enabled: true
    coverage_threshold: 80
    blocking: true

  logging:
    enabled: true
    threshold: 90
    blocking: false

  documentation:
    enabled: true
    threshold: 85
    blocking: false

  performance:
    enabled: false
    threshold: 90
    blocking: false
```

**Quality gate modes:**
- `strict` - All gates must pass
- `balanced` - Critical gates must pass (security, testing)
- `permissive` - Gates are advisory only

**Blocking:**
- `true` - Prevents deployment if gate fails
- `false` - Warning only

---

## Using Configuration

### In Python Scripts

```python
from vibey.config import load_project_config

# Load full config
config = load_project_config()
print(f"Project: {config.project.name}")

# Access nested values
orchestration = config.framework.orchestration_mode
languages = config.tech_stack.languages
```

### In CLI Commands

```bash
# Show configuration
vibey config show

# Validate configuration
vibey config validate

# Update value
vibey config update project.version "2.0.0"
```

---

## Migration from Legacy Config

If you have `.claude/project-config.yaml`, migrate to modular format:

### Auto-Migration Prompt

When you run `vibey config validate` or other config commands with a legacy config, you'll be prompted to migrate:

```
╭───────────────────────────────────────────────────────────────────╮
│ ⚠ Legacy Config Detected                                          │
│                                                                   │
│ You're using the old config format (.claude/project-config.yaml). │
│ The new modular format (.vibey/config/) is recommended.           │
│                                                                   │
│ Benefits of migrating:                                            │
│   • Easier to understand and edit                                 │
│   • Better validation                                             │
│   • Clearer organization                                          │
│                                                                   │
│ Would you like to migrate now? (Backup will be created)           │
╰───────────────────────────────────────────────────────────────────╯

Migrate to modular config? [Y/n]:
```

**Accept (Y):**
- Migration runs automatically
- Backup created in `.vibey/config-backups/`
- Command continues with new config

**Decline (n):**
- Command continues with legacy config
- Marker file created (`.vibey/.migration-declined`)
- Won't prompt again until marker removed

**To see prompt again:**
```bash
rm .vibey/.migration-declined
```

### Manual Migration

```bash
# Dry run (preview only)
vibey config migrate --dry-run

# Migrate with backup (recommended)
vibey config migrate

# Migrate without backup
vibey config migrate --no-backup
```

### Migration Details

The migration tool:
1. ✅ Validates legacy config
2. ✅ Creates backup (`.vibey/config-backups/`)
3. ✅ Splits into 4 modular files
4. ✅ Preserves all settings
5. ✅ Validates migrated config

**Backup location:**
```
.vibey/config-backups/
└── [timestamp]/
    ├── project-config.yaml  # Backup of original
    └── README.md            # Restore instructions
```

### After Migration

```bash
# Verify migration
vibey config validate

# Optional: Remove legacy file
rm .claude/project-config.yaml
```

---

## Validation

### Automatic Validation

All configs are validated automatically when loaded:
- Type checking
- Required fields
- Value constraints
- Pattern matching

### Manual Validation

```bash
# Validate all config files
vibey config validate

# Validate specific file
vibey config validate --file project.yaml
```

### Common Validation Errors

**Invalid version format:**
```
Error: project.version must match pattern ^\d+\.\d+\.\d+$
Fix: Use semantic versioning (e.g., "1.0.0")
```

**Invalid project type:**
```
Error: project.type must be one of: web-app, api, library, ml, data-platform, infrastructure
Fix: Choose a valid project type
```

**Empty languages array:**
```
Error: tech_stack.languages must have at least 1 item
Fix: Add at least one programming language
```

---

## Best Practices

### Organization

✅ **Do:**
- Keep configs in `.vibey/config/`
- Use semantic versioning
- Document custom settings
- Validate after changes

❌ **Don't:**
- Mix project info with framework settings
- Use invalid enum values
- Omit required fields
- Edit without validation

### Version Control

**Include in Git:**
- `.vibey/config/*.yaml` - All config files
- `.gitignore` entry for backups

```gitignore
# Vibey
.vibey/config-backups/
```

### Security

⚠️ **Never commit:**
- Secrets or API keys
- Database passwords
- Private URLs

Use environment variables or separate secrets management instead.

---

## Troubleshooting

### Config Not Found

```
Error: No Vibey configuration found
```

**Solution:**
- Run `vibey init` for new project
- Or `vibey config migrate` for existing project

### Validation Failed

```
Error: Invalid configuration
```

**Solution:**
1. Run `vibey config validate` to see specific errors
2. Fix reported issues
3. Re-validate

### Migration Issues

```
Error: Both configs exist
```

**Solution:**
- Use `--force` to overwrite: `vibey config migrate --force`
- Or manually remove `.claude/project-config.yaml`

---

## Advanced Topics

### Custom Config Locations

```python
from vibey.config import load_config
from pathlib import Path

# Load from specific directory
config = load_config(Path("/path/to/project"))
```

### Programmatic Updates

```python
from vibey.config import ProjectConfig

config = ProjectConfig.from_yaml(".vibey/config/project.yaml")
config.project.version = "2.0.0"
config.to_yaml(".vibey/config/project.yaml")
```

### Config Templates

Example templates available in `vibey/config/examples/`:
- `project.yaml` - Web app example
- `framework.yaml` - Balanced orchestration
- `agents.yaml` - Common agents
- `quality-gates.yaml` - Balanced gates

---

## Reference

### Schema Documentation

- **Schemas:** `vibey/config/schemas/`
- **Models:** `vibey/config/models.py`
- **Examples:** `vibey/config/examples/`

### Related Docs

- [Migration Guide](development/CONFIG_MIGRATION_GUIDE.md)
- [Deprecation Notices](DEPRECATION_NOTICES.md)
- [Design Decisions](../vibey/config/DESIGN_DECISIONS.md)

---

## FAQ

**Q: Can I use both legacy and modular configs?**
A: The system automatically uses modular if it exists, falls back to legacy. Both work but modular is preferred.

**Q: What happens to my legacy config after migration?**
A: It's backed up to `.vibey/config-backups/`. You can optionally delete it after verifying migration.

**Q: Can I customize config locations?**
A: Yes, using the Python API. CLI always uses `.vibey/config/`.

**Q: How do I rollback a migration?**
A: Copy the backup from `.vibey/config-backups/[timestamp]/project-config.yaml` back to `.claude/project-config.yaml`.

**Q: Are there config templates?**
A: Yes, in `vibey/config/examples/` for different project types.

---

**Questions?** See [CONFIG_MIGRATION_GUIDE.md](development/CONFIG_MIGRATION_GUIDE.md) or open a GitHub issue.
