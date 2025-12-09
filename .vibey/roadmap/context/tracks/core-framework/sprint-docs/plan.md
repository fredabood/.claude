# Sprint Plan: Default CLAUDE.md Auto-Generation

## Goals

1. Auto-generate CLAUDE.md from .vibey/config/ files
2. Simplify initialization process for users
3. Make framework configuration more maintainable

## Features

### 1. Config Structure Design

**What:** Define YAML structure for .vibey/config/
**Why:** Need standardized config format for all Vibey projects
**How:**
- project.yaml - Project metadata, tech stack
- framework.yaml - Framework behavior settings
- agents.yaml - Agent preferences and customization
- quality-gates.yaml - Quality standards and thresholds

### 2. Config Parser

**What:** Python module to read and validate configs
**Why:** Need programmatic access to config data
**How:**
- YAML schema validation
- Type checking
- Default value handling
- Error messages for invalid configs

### 3. Permanent .vibey/ Directory

**What:** Keep .vibey/ after initialization (don't delete)
**Why:** Need persistent home for roadmap state and configs
**How:**
- Modify /vibey command logic
- Update .gitignore handling
- Document new structure

## Success Criteria

- ✅ Config files validate correctly
- ✅ Parser handles all config types
- ✅ .vibey/ persists after init
- ✅ Documentation updated
