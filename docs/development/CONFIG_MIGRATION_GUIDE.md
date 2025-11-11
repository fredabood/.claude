# Config System Migration Guide

**Version:** 1.0
**Date:** 2025-11-10
**Sprint:** directory-migration-2, Task 009

This guide explains how to update code to use the new modular config system.

---

## Overview

The Vibey framework has migrated from:

**Old (Legacy):**
```
.claude/project-config.yaml  # Monolithic file
```

**New (Modular):**
```
.vibey/config/
├── project.yaml          # Project info
├── framework.yaml        # Framework settings
├── agents.yaml           # Agent configuration
└── quality-gates.yaml    # Quality gates
```

---

## For Python Scripts

### Old Way (Deprecated)

```python
import yaml

# Load legacy config
with open('.claude/project-config.yaml') as f:
    config = yaml.safe_load(f)

project_name = config['project']['name']
orchestration = config['vibey']['orchestration_mode']
```

### New Way (Recommended)

```python
from vibey.cli.config_utils import load_project_config, get_config_value

# Simple value lookup
project_name = get_config_value("project.project.name")
orchestration = get_config_value("framework.framework.orchestration_mode")

# Full config object
config = load_project_config()
if config:
    print(f"Project: {config.project.project.name}")
    print(f"Type: {config.project.project.type.value}")
```

### Config Utilities API

**`load_project_config(project_root=None, quiet=False)`**
- Loads complete config with automatic fallback
- Returns `VibeyConfig` or `None` if error
- Handles both legacy and modular formats

**`get_config_value(key_path, project_root=None, default=None)`**
- Get specific value using dot notation
- Auto-handles enums (returns `.value`)
- Returns default if not found

**`config_exists(project_root=None)`**
- Check if valid config exists
- Returns `bool`

---

## For Framework Agents/Workflows

### Old References

```markdown
Configuration is in `.claude/project-config.yaml`

The project config shows:
- Project name: {{project.name}}
- Tech stack: {{tech_stack.languages}}
```

### New References

```markdown
Configuration is in `.vibey/config/`:
- `project.yaml` - Project information
- `framework.yaml` - Framework settings
- `agents.yaml` - Agent configuration
- `quality-gates.yaml` - Quality gates

The project is configured in `.vibey/config/project.yaml`:
- Project name: {{project.name}}
- Tech stack: {{tech_stack.languages}}

Note: Legacy `.claude/project-config.yaml` still supported for backward compatibility.
Run `vibey config migrate` to upgrade.
```

---

## For Documentation

### Update Instructions

**Find and replace:**

1. **File paths:**
   - `.claude/project-config.yaml` → `.vibey/config/` (with explanation)
   - Add note about `vibey config migrate` for migration

2. **Config access examples:**
   - Show Python examples using new `config_utils`
   - Keep legacy format documented as "deprecated but supported"

3. **Add migration instructions:**
   ```bash
   # Migrate legacy config
   vibey config migrate

   # Verify migration
   vibey config show
   vibey config validate
   ```

---

## Migration Checklist

For updating a script/file:

- [ ] Replace hardcoded `.claude/project-config.yaml` paths
- [ ] Use `vibey.cli.config_utils` for config loading
- [ ] Handle both legacy and modular formats (auto-fallback)
- [ ] Update documentation/help text
- [ ] Add deprecation warnings if loading legacy directly
- [ ] Test with both config formats

---

## Key Files Updated

### Python Scripts

✅ **`vibey/cli/config_utils.py`** (NEW)
- Utility functions for config loading
- Used by all CLI scripts

📋 **Scripts to update:**
- `vibey/cli/render-template.py` - Use config_utils
- `framework/scripts/render-template.py` - Use config_utils
- Any other scripts that load config

### Documentation

📋 **Docs to update:**
- `CLAUDE.md` - Add config migration notes
- `docs/getting-started/*.md` - Update config references
- `framework/docs/getting-started/QUICK_START.md` - Show new config
- `framework/commands/vibey.md` - Update config instructions
- `framework/agents/core/vibey-manager.md` - Update config management

### Tests

📋 **Tests to update:**
- Update fixtures to use modular format
- Add tests for config migration
- Test backward compatibility

---

## Backward Compatibility

**Important:** The system maintains full backward compatibility:

1. **Automatic fallback** - Loader tries modular first, falls back to legacy
2. **Deprecation warnings** - Warns when using legacy format
3. **Migration tool** - `vibey config migrate` for easy upgrade
4. **No breaking changes** - Existing projects continue to work

---

## Common Patterns

### Pattern 1: Check config exists before using

```python
from vibey.cli.config_utils import config_exists

if not config_exists():
    print("No configuration found. Run 'vibey init' to create one.")
    sys.exit(1)
```

### Pattern 2: Get value with fallback

```python
from vibey.cli.config_utils import get_config_value

orchestration = get_config_value(
    "framework.framework.orchestration_mode",
    default="balanced"
)
```

### Pattern 3: Load full config

```python
from vibey.cli.config_utils import load_project_config

config = load_project_config()
if not config:
    print("Error: Could not load configuration")
    sys.exit(1)

# Use config
print(f"Project: {config.project.project.name}")
print(f"Languages: {', '.join(config.project.tech_stack.languages)}")
```

---

## Timeline

**Phase 1: Migration Foundation** (✅ Complete)
- Task 001-004: Config system implementation
- Loader with automatic fallback
- Migration tool (`vibey config migrate`)

**Phase 2: Integration** (🔄 Current - Task 009)
- Update Python scripts to use new system
- Update documentation references
- Add utility functions

**Phase 3: Deprecation** (📋 Upcoming - Task 010)
- Add deprecation warnings
- Encourage migration
- Remove legacy examples from docs

**Phase 4: Testing** (📋 Upcoming - Task 011)
- End-to-end migration testing
- Backward compatibility testing
- Edge case handling

---

## Getting Help

- **Migration:** `vibey config migrate --help`
- **Validation:** `vibey config validate`
- **Show config:** `vibey config show`
- **Documentation:** See `vibey/config/README.md`

---

**Last Updated:** 2025-11-10
**Sprint:** directory-migration-2
**Task:** 009 - Update all config references in codebase
