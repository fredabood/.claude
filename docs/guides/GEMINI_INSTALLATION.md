# Gemini Code Assist Installation Guide

This guide walks you through installing the Vibey Agent Framework as a Gemini Code Assist extension.

## Prerequisites

- **Gemini Code Assist** installed (VS Code extension or CLI)
- **Python 3.9+** for MCP server
- **Vibey Framework** cloned locally

## Quick Start

```bash
# 1. Export Vibey to Gemini format
vibey export gemini -o ./vibey-gemini-extension

# 2. Install the extension
./vibey-gemini-extension/install.sh

# 3. Verify installation
# In Gemini, run: /mcp
```

## Installation Methods

### Method 1: Automatic Install Script

The simplest approach uses the generated install script:

```bash
# Export extension
vibey export gemini -o ./dist/gemini

# Run installer
./dist/gemini/install.sh
```

The installer will:
- Copy GEMINI.md to your project root
- Install custom commands to `~/.gemini/commands/vibey/`
- Configure MCP server in `~/.gemini/settings.json`

### Method 2: Manual Installation

For more control, install components individually:

#### 1. Copy Context File

```bash
cp ./dist/gemini/GEMINI.md ./GEMINI.md
```

This file provides Gemini with context about available agents, workflows, and MCP tools.

#### 2. Install Custom Commands

```bash
mkdir -p ~/.gemini/commands
cp -r ./dist/gemini/commands/vibey ~/.gemini/commands/
```

Commands are now available as `/vibey:*` (e.g., `/vibey:status`, `/vibey:sprint`).

#### 3. Configure MCP Server

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "framework.mcp.server"],
      "env": {
        "PYTHONPATH": "/path/to/vibey"
      }
    }
  }
}
```

### Method 3: Project-Local Installation

For project-specific installation (doesn't affect global config):

```bash
# Export to project's .gemini directory
vibey export gemini -o ./.gemini

# The extension will be available only in this project
```

## Verifying Installation

### Check MCP Server

```bash
# Run connectivity test
python -m vibey.adapters.gemini.mcp_test
```

Expected output:
```
MCP Test: PASS (4/4 tests passed)
```

### Check Custom Commands

In Gemini Code Assist, type `/vibey:` and you should see:
- `/vibey:status` - Check roadmap status
- `/vibey:sprint` - Current sprint info
- `/vibey:task` - Task management
- Agent commands (`/vibey:agent-*`)
- Workflow commands

### Check Context Loading

Ask Gemini: "What agents are available in this project?"

It should respond with information from GEMINI.md about available Vibey agents.

## Updating the Extension

When Vibey's agents or workflows change, regenerate the extension:

```bash
# Regenerate with validation
vibey export gemini -o ./dist/gemini --validate

# Reinstall
./dist/gemini/install.sh
```

The `--validate` flag checks for drift between source and existing export.

## Troubleshooting

### MCP Server Not Found

**Symptom:** Gemini shows "MCP server vibey not available"

**Solution:**
1. Ensure Python is in PATH
2. Check `settings.json` path to MCP server
3. Verify PYTHONPATH includes Vibey root

```bash
# Test MCP server directly
python -m framework.mcp.server --help
```

### Commands Not Appearing

**Symptom:** `/vibey:*` commands don't appear

**Solution:**
1. Check commands are in correct directory:
   ```bash
   ls ~/.gemini/commands/vibey/
   ```
2. Restart Gemini Code Assist
3. Verify TOML files are valid:
   ```bash
   cat ~/.gemini/commands/vibey/status.toml
   ```

### GEMINI.md Not Loading

**Symptom:** Gemini doesn't know about agents/workflows

**Solution:**
1. Verify GEMINI.md exists in project root
2. Check file isn't too large (< 100KB recommended)
3. Ensure no syntax errors in file

### Drift Detection Fails

**Symptom:** `vibey export gemini --validate` shows drift

**Solution:**
1. Don't manually edit generated files
2. Regenerate: `vibey export gemini -o ./dist/gemini`
3. Or update source agents/workflows and regenerate

## Extension Structure

After export, your extension contains:

```
vibey-gemini-extension/
├── GEMINI.md              # Context file for Gemini
├── commands/
│   └── vibey/
│       ├── status.toml    # /vibey:status command
│       ├── sprint.toml    # /vibey:sprint command
│       ├── agent-*.toml   # Agent commands
│       └── *.toml         # Workflow commands
├── settings.json          # MCP server config
├── gemini-extension.json  # Extension manifest
├── install.sh             # Installation script
├── README.md              # Extension readme
└── .checksums.json        # Drift detection data
```

## Multi-Project Setup

For teams using multiple projects:

1. **Global agents**: Install to `~/.gemini/` for all projects
2. **Project-specific**: Install to `./.gemini/` per project
3. **Mixed**: Global MCP, project-specific commands

## Security Considerations

- MCP server runs with your user permissions
- Review `settings.json` before adding to global config
- Extension doesn't have network access by default
- Roadmap data stays local

## Next Steps

- [Migration Guide](./GEMINI_MIGRATION.md) - Moving from Claude Code
- [Orchestration Guide](./GEMINI_ORCHESTRATION.md) - Multi-step workflows
- [Troubleshooting](./GEMINI_TROUBLESHOOTING.md) - Common issues
