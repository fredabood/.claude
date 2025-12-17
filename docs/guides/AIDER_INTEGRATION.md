# Aider Integration Guide

This guide explains how to use Vibey Agent Framework with [Aider](https://aider.chat/), the popular terminal-based AI coding assistant.

## Overview

Vibey provides seamless integration with Aider through the `vibey deploy --platform aider` command. This generates all necessary configuration files, system prompts, and workflow scripts in the `.aider/` directory.

## Quick Start

```bash
# 1. Install Vibey (if not already installed)
git clone https://github.com/anthropics/vibey.git && cd vibey && python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"

# 2. Initialize Vibey in your project
cd your-project
vibey init

# 3. Deploy to Aider
vibey deploy --platform aider

# 4. Start using Aider with Vibey agents
aider --config .aider/aider.conf.yml
```

## What Gets Generated

When you run `vibey deploy --platform aider`, the following structure is created:

```
.aider/
├── .generated              # Marker file (DO NOT EDIT)
├── aider.conf.yml          # Aider configuration
├── agents/                 # System prompts for each agent
│   ├── web-developer.md
│   ├── test-engineer.md
│   ├── security-reviewer.md
│   └── ...
├── workflows/              # Python scripts for workflows
│   ├── feature_development.py
│   ├── weekly_sprint.py
│   └── ...
└── hooks/                  # Git hooks for quality gates
    ├── pre-commit
    ├── post-commit
    └── README.md
```

## Using Vibey Agents in Aider

### Loading an Agent

To use a Vibey agent as a system prompt in Aider:

```bash
# Use the web developer agent
aider --system .aider/agents/web-developer.md

# Use the security reviewer agent
aider --system .aider/agents/security-reviewer.md

# Use the test engineer agent
aider --system .aider/agents/test-engineer.md
```

### Available Agents

Vibey provides 12 specialized agents:

| Agent | Purpose | Use Case |
|-------|---------|----------|
| `web-developer` | Frontend/fullstack development | Building UI components, React apps |
| `backend-engineer` | API and server development | REST APIs, databases, services |
| `test-engineer` | Testing and QA | Unit tests, integration tests |
| `security-reviewer` | Security audits | Vulnerability scanning, OWASP checks |
| `performance-engineer` | Performance optimization | Profiling, caching, optimization |
| `infrastructure-engineer` | DevOps and IaC | Terraform, Kubernetes, CI/CD |
| `ml-engineer` | Machine learning | Models, training, inference |
| `database-specialist` | Database design | Schema design, queries, migrations |
| `documentation-engineer` | Documentation | README, API docs, guides |
| `coordinator` | Multi-agent orchestration | Complex tasks requiring multiple agents |
| `sprint-planning` | Sprint management | Planning, task breakdown |
| `researcher` | Research and investigation | Codebase analysis, tech research |

## Running Workflows

Vibey workflows are converted to Python scripts that use the Aider API:

```bash
# Run a workflow
python .aider/workflows/feature_development.py

# Run sprint planning workflow
python .aider/workflows/sprint_planning.py
```

### Customizing Workflows

The generated workflow scripts are templates. Edit the source files in `framework/workflows/` and regenerate:

```bash
# Edit the source
vi framework/workflows/feature-development.md

# Regenerate Aider files
vibey deploy --platform aider
```

## Configuration

### aider.conf.yml

The generated `aider.conf.yml` includes sensible defaults:

```yaml
# Model Configuration
# model: claude-3-5-sonnet
# api-key: $ANTHROPIC_API_KEY

# Git Integration
auto-commits: true
attribute-author: true
attribute-committer: true

# Commit Message Template
commit-prompt: |
  Create a concise commit message for these changes.
  Format: <type>(<scope>): <description>
  Types: feat, fix, docs, style, refactor, test, chore
```

### Model Selection

Uncomment and set your preferred model:

```yaml
# Claude (Anthropic)
model: claude-3-5-sonnet
api-key: $ANTHROPIC_API_KEY

# GPT-4 (OpenAI)
# model: gpt-4o
# api-key: $OPENAI_API_KEY

# DeepSeek
# model: deepseek-chat
# api-key: $DEEPSEEK_API_KEY
```

## Git Hooks

Vibey generates git hooks for quality gates:

### Pre-commit Hook

Validates code before commits:
- Python syntax checking
- Custom validation rules

### Installing Hooks

```bash
# Symlink hooks to .git/hooks
ln -sf ../../.aider/hooks/pre-commit .git/hooks/pre-commit
ln -sf ../../.aider/hooks/post-commit .git/hooks/post-commit

# Or copy them
cp .aider/hooks/* .git/hooks/
```

## Source of Truth Architecture

> **Important**: All files in `.aider/` are GENERATED. Never edit them directly.

### How It Works

```
SOURCE OF TRUTH (edit these)              GENERATED OUTPUT (never edit)
────────────────────────────              ────────────────────────────
framework/agents/*.md            ───►     .aider/agents/*.md
framework/workflows/*.md         ───►     .aider/workflows/*.py
.vibey/config/*.yaml             ───►     .aider/aider.conf.yml
```

### Why This Matters

1. **Prevents Drift**: Generated files always match source definitions
2. **Single Update Point**: Change source once, regenerate for all platforms
3. **Consistent Behavior**: Same agent behaves identically across platforms
4. **Version Control**: Source of truth is tracked; generated files can be `.gitignore`d

### Regenerating Files

```bash
# Regenerate all .aider/ files from source
vibey deploy --platform aider

# Force regenerate (clears existing)
vibey deploy --platform aider --clean

# After framework update
vibey upgrade && vibey deploy --platform aider
```

## .gitignore Recommendations

```gitignore
# Generated platform files (regenerate with `vibey deploy`)
.aider/agents/
.aider/workflows/
.aider/hooks/
.aider/.generated

# Keep config if you've customized model/API settings
# !.aider/aider.conf.yml

# Aider chat history
.aider/chat-history.md
```

## Example Workflow

### Feature Development with Aider + Vibey

```bash
# 1. Start Aider with the web developer agent
aider --system .aider/agents/web-developer.md --config .aider/aider.conf.yml

# 2. Add files to work with
/add src/components/Button.tsx tests/Button.test.tsx

# 3. Request changes
# "Add a loading state to the Button component"

# 4. Switch to test engineer for testing
/system .aider/agents/test-engineer.md

# 5. Request tests
# "Add comprehensive tests for the loading state"

# 6. Switch to security reviewer
/system .aider/agents/security-reviewer.md

# 7. Review for security issues
# "Review this component for security vulnerabilities"
```

## Troubleshooting

### Files Not Generating

```bash
# Ensure you have a valid Vibey config
vibey config show

# Check for errors
vibey deploy --platform aider --verbose
```

### Agent Prompts Not Loading

```bash
# Verify the file exists
ls -la .aider/agents/

# Check the content
cat .aider/agents/web-developer.md

# Use absolute path if needed
aider --system $(pwd)/.aider/agents/web-developer.md
```

### Workflow Scripts Failing

```bash
# Ensure aider-chat is installed
pip install aider-chat

# Run with verbose output
python -v .aider/workflows/feature_development.py
```

## Advanced Usage

### Custom Agents

Create custom agents in `framework/agents/custom/`:

```markdown
# framework/agents/custom/my-agent.md

# My Custom Agent

A specialized agent for my specific needs.

## Capabilities
- Custom capability 1
- Custom capability 2

## Instructions
[Your agent instructions here]
```

Then regenerate:

```bash
vibey deploy --platform aider
```

### Combining Agents

Use the coordinator agent for complex tasks:

```bash
aider --system .aider/agents/coordinator.md

# Then in the chat:
# "I need to implement a new API endpoint with tests and documentation.
#  Please coordinate the web-developer, test-engineer, and documentation-engineer
#  to complete this task."
```

## Resources

- [Aider Documentation](https://aider.chat/docs/)
- [Aider YAML Config Reference](https://aider.chat/docs/config/aider_conf.html)
- [Aider Python API](https://aider.chat/docs/scripting.html)
- [Vibey Framework Documentation](../README.md)

---

*Generated by Vibey Agent Framework*
