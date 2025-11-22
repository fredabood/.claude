# Platform Context Management Guide

This guide explains how to use Vibey's platform context management system to work seamlessly across different AI coding platforms with varying context window sizes.

## Overview

Different AI coding platforms have different context window limits:

| Platform | Context Window | Vendor |
|----------|---------------|--------|
| Claude Code | 200,000 tokens | Anthropic |
| Gemini | 1,000,000 tokens | Google |
| Goose | 128,000 tokens | Block |
| Cursor | 128,000 tokens | Anysphere |
| Continue | 100,000 tokens | Continue.dev |
| Aider | 100,000 tokens | Aider |
| Copilot | 64,000 tokens | GitHub |
| JetBrains AI | 64,000 tokens | JetBrains |
| Windsurf | 128,000 tokens | Codeium |
| VS Code | 50,000 tokens | Microsoft |

Vibey's platform context management ensures your sprints and tasks fit within your platform's limits, helping you plan work effectively.

## Quick Start

### 1. Check Current Platform

```bash
vibey config platform show
```

This shows your current platform configuration, including:
- Detected or configured platform
- Context window size
- Auto-detection status

### 2. Detect Platform Automatically

```bash
vibey config platform detect
```

Vibey detects your platform by checking:
1. Environment variables (e.g., `CLAUDE_CODE`, `GOOSE_HOME`)
2. Running processes (e.g., `claude`, `goose`)
3. Configuration files (e.g., `.claude/settings.json`)

### 3. Set Platform Manually

```bash
# Set platform by name
vibey config platform set claude-code

# Set with custom context window
vibey config platform set goose --context-window 150000
```

### 4. Check Sprint Compatibility

```bash
vibey roadmap check-compatibility my-sprint-1
```

This analyzes all incomplete tasks in the sprint against your platform's context window.

## Platform Commands

### `vibey config platform show`

Displays current platform configuration:

```
Platform Configuration:
  Configured: claude-code
  Context Window: 200,000 tokens
  Auto-detect: enabled

Effective Platform:
  Name: Claude Code
  Vendor: Anthropic
  Detection: config file
```

### `vibey config platform detect`

Forces re-detection of platform:

```
Detecting platform...
  ✓ Found environment variable: CLAUDE_CODE_VERSION
  ✓ Found config file: .claude/settings.json

Detected: Claude Code (Anthropic)
Context Window: 200,000 tokens
```

### `vibey config platform set <name>`

Manually sets platform:

```bash
# Set platform with default context window
vibey config platform set gemini

# Set with custom context window (tokens)
vibey config platform set goose --context-window 150000
```

### `vibey config platform clear`

Removes manual configuration, enabling auto-detection:

```bash
vibey config platform clear
```

### `vibey config platform list`

Lists all known platforms:

```
Known Platforms:
  claude-code    Claude Code       200,000 tokens  Anthropic
  gemini         Gemini          1,000,000 tokens  Google
  goose          Goose             128,000 tokens  Block
  cursor         Cursor            128,000 tokens  Anysphere
  continue       Continue          100,000 tokens  Continue.dev
  aider          Aider             100,000 tokens  Aider
  copilot        GitHub Copilot     64,000 tokens  GitHub
  jetbrains-ai   JetBrains AI       64,000 tokens  JetBrains
  windsurf       Windsurf          128,000 tokens  Codeium
  vscode         VS Code            50,000 tokens  Microsoft
```

## Compatibility Checking

### `vibey roadmap check-compatibility <sprint-id>`

Analyzes sprint tasks against current platform context:

```
Sprint: feature-sprint-1
Platform: claude-code (200,000 tokens)

Task Analysis:
  ✓ task-001: 15,000 tokens (7.5%)
  ✓ task-002: 25,000 tokens (12.5%)
  ⚠ task-003: 180,000 tokens (90%) - WARNING
  ✗ task-004: 250,000 tokens (125%) - OVERSIZED

Summary:
  Compatible: 2 tasks
  Warning: 1 task (over 80% of context)
  Oversized: 1 task (exceeds context window)
```

### Understanding Results

- **Compatible** (✓): Task fits comfortably within context window
- **Warning** (⚠): Task uses >80% of context window
- **Oversized** (✗): Task exceeds context window capacity

## Sprint Recalculation

### `vibey roadmap recalculate <sprint-id>`

When tasks don't fit your platform's context window, recalculate the sprint:

```bash
# Interactive mode (default)
vibey roadmap recalculate my-sprint-1

# Dry run (preview changes)
vibey roadmap recalculate my-sprint-1 --dry-run

# Target specific platform
vibey roadmap recalculate my-sprint-1 --platform goose
```

### Recalculation Process

1. **Analysis**: Identifies oversized tasks
2. **Planning**: Calculates how to split tasks
3. **Preview**: Shows proposed changes
4. **Confirmation**: User approves changes
5. **Application**: Updates task files

### Example Recalculation

```
Recalculation Plan for: my-sprint-1
Target Platform: goose (128,000 tokens)

Oversized Tasks:
  task-003 (180,000 tokens) → Split into 2 subtasks:
    - task-003a: Core implementation (90,000 tokens)
    - task-003b: Integration and testing (90,000 tokens)

  task-004 (250,000 tokens) → Split into 3 subtasks:
    - task-004a: API layer (85,000 tokens)
    - task-004b: Business logic (85,000 tokens)
    - task-004c: Data access (80,000 tokens)

Dependencies:
  ✓ task-003a maintains dependency on task-002
  ✓ task-003b depends on task-003a
  ✓ task-004a maintains dependency on task-003b
  ✓ Original dependency chain preserved

Apply these changes? [y/N]
```

## Smart Prompting

When starting a sprint with compatibility issues, Vibey prompts:

```
⚠ Compatibility Warning: my-sprint-1

1 task exceeds your platform's context window (200,000 tokens).
2 tasks are near the limit (>80%).

Options:
  [Y] Recalculate - Split oversized tasks
  [N] Continue - Proceed anyway
  [I] Info - View detailed analysis
  [C] Cancel - Stop and exit

Choice [Y/n/i/c]:
```

### Option Details

- **Y (Recalculate)**: Opens recalculation flow
- **N (Continue)**: Starts sprint with warnings
- **I (Info)**: Shows detailed compatibility report
- **C (Cancel)**: Aborts sprint start

## Best Practices

### 1. Check Compatibility Early

Run compatibility checks before starting sprints:

```bash
vibey roadmap check-compatibility my-sprint-1
```

### 2. Plan for Target Platform

When creating tasks, estimate tokens based on your target platform:

```yaml
task:
  id: my-task-001
  estimated_tokens: 50000  # Keep under 80% of context
```

### 3. Use Buffer for Safety

Vibey uses a 10% buffer by default. A 200K context window effectively becomes 180K for planning.

### 4. Split Large Features

Break large features into smaller tasks that fit within context:

```
# Instead of:
- Build entire authentication system (300K tokens)

# Use:
- Design auth architecture (40K tokens)
- Implement user registration (50K tokens)
- Implement login/logout (50K tokens)
- Add password reset (40K tokens)
- Integration testing (30K tokens)
```

### 5. Review Recalculation Plans

Always review recalculation plans before applying:

```bash
# Preview first
vibey roadmap recalculate sprint-1 --dry-run

# Then apply if satisfied
vibey roadmap recalculate sprint-1
```

## Troubleshooting

### Platform Not Detected

If auto-detection fails:

```bash
# List available platforms
vibey config platform list

# Set manually
vibey config platform set claude-code
```

### Wrong Context Window

Override the default context window:

```bash
vibey config platform set claude-code --context-window 180000
```

### Tasks Still Too Large

If recalculation produces still-large subtasks:

1. Run recalculation again with lower target
2. Manually refine task breakdown
3. Consider architectural changes

## Configuration File

Platform config is stored at `.vibey/config/platform.yaml`:

```yaml
platform: claude-code
context_window: 200000
auto_detect: true
```

## See Also

- [Roadmap CLI Reference](./ROADMAP_CLI_REFERENCE.md)
- [Token Effort Estimation](./TOKEN_EFFORT_ESTIMATION.md)
- [Recalculation Algorithm](../development/RECALCULATION_ALGORITHM.md)
