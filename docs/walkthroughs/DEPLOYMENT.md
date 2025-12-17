# Deploying Vibey Configurations

> **Time Required:** 15 minutes
> **Difficulty:** Intermediate
> **Prerequisites:** Vibey installed, target platforms available

---

## Overview

This walkthrough covers deploying Vibey configurations to AI assistant platforms. You'll learn to configure platforms and deploy adapter configurations.

---

## Supported Platforms

Vibey deploys to 9 AI assistant platforms:

| Platform | Adapter | Description |
|----------|---------|-------------|
| Claude Code | `claudecode` | Anthropic's CLI-based AI assistant |
| Cursor | `cursor` | AI-powered code editor |
| Copilot | `copilot` | GitHub's AI pair programmer |
| VS Code | `vscode` | VS Code with AI extensions |
| Goose | `goose` | Block's AI assistant |
| Gemini | `gemini` | Google's AI assistant |
| Aider | `aider` | Terminal-based AI coding |
| Continue | `continue` | Open-source AI assistant |
| Windsurf | `windsurf` | Codeium's AI IDE |

---

## Platform Configuration

### Detect Current Platform

```bash
vibey config platform detect
```

Automatically detects which AI platform you're running in.

### List Available Platforms

```bash
vibey config platform list
```

Shows all supported platforms and their status.

### Set Active Platform

```bash
vibey config platform set cursor
```

Sets the active platform for deployment operations.

### Show Platform Configuration

```bash
vibey config platform show
```

Shows current platform configuration details.

### Clear Platform Configuration

```bash
vibey config platform clear
```

Clears the current platform configuration.

---

## Deploying Configurations

### List Deployment Options

```bash
vibey deploy list
```

Shows available deployment targets and their status.

### Run Deployment

```bash
vibey deploy run --platform cursor
```

Deploys Vibey configuration to the specified platform.

### Full Deployment Workflow

```bash
# 1. Check which platforms are available
vibey deploy list

# 2. Set your target platform
vibey config platform set cursor

# 3. Verify configuration
vibey config platform show

# 4. Deploy
vibey deploy run --platform cursor

# 5. Verify deployment
vibey config platform show
```

---

## Configuration Rollback

If a deployment causes issues:

```bash
vibey config rollback
```

Reverts to the previous configuration state.

---

## Platform-Specific Notes

### Claude Code

Claude Code uses CLAUDE.md files for context. Vibey generates and updates this file:

```bash
vibey deploy run --platform claudecode
```

This updates CLAUDE.md with current roadmap context.

### Cursor

Cursor uses `.cursor/` directory for configuration:

```bash
vibey deploy run --platform cursor
```

Deploys rules and context to Cursor's configuration directory.

### VS Code

VS Code deployments configure workspace settings:

```bash
vibey deploy run --platform vscode
```

Updates `.vscode/settings.json` with Vibey integration.

---

## Command Reference

### Platform Configuration
```bash
vibey config platform                # Platform config help
vibey config platform detect         # Detect current platform
vibey config platform list           # List all platforms
vibey config platform set <name>     # Set active platform
vibey config platform show           # Show current config
vibey config platform clear          # Clear config
vibey config rollback                # Rollback to previous config
```

### Deployment
```bash
vibey deploy                         # Deploy help
vibey deploy list                    # List deployment targets
vibey deploy run --platform <name>   # Deploy to platform
```

---

## See Also

- [Getting Started](./GETTING_STARTED.md) - First-time setup
- [Architecture Overview](../architecture/ARCHITECTURE_OVERVIEW.md) - Platform adapter design
- [CLI Reference](../reference/CLI_REFERENCE.md) - All commands
