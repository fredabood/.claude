# Migration Guide: Claude Code to Gemini

This guide helps you transition from using Vibey with Claude Code to using it with Gemini Code Assist.

## Overview

Both Claude Code and Gemini Code Assist support Vibey, but they have different execution models:

| Feature | Claude Code | Gemini Code Assist |
|---------|-------------|-------------------|
| Execution Model | Parallel subagents | Sequential commands |
| Context File | CLAUDE.md | GEMINI.md |
| MCP Support | Native | Native |
| Custom Commands | Slash commands | TOML commands |
| Workflow Orchestration | Task tool | Command chaining |

## Key Differences

### 1. No Parallel Execution

**Claude Code:**
```
The coordinator can spawn multiple subagents in parallel using the Task tool.
```

**Gemini:**
```
Commands execute sequentially. Use command chains for multi-step workflows.
```

**Migration Strategy:**
- Review GEMINI.md's "Sequential Workflow Execution" section
- Follow suggested command sequences for complex workflows
- Use `/vibey:status` between steps to track progress

### 2. Different Context Files

**Claude Code** reads `CLAUDE.md`
**Gemini** reads `GEMINI.md`

Both are generated from the same source (agent/workflow frontmatter), ensuring feature parity.

**Migration:**
```bash
# Generate both context files
vibey export claude-code   # Creates/updates CLAUDE.md
vibey export gemini        # Creates GEMINI.md
```

### 3. Command Syntax

**Claude Code:**
```
/vibey sprint status
Ask the sprint-planning agent to...
```

**Gemini:**
```
/vibey:status
/vibey:sprint
/vibey:agent-sprint-planning
```

**Mapping:**
| Claude Code | Gemini |
|-------------|--------|
| `/vibey status` | `/vibey:status` |
| `/vibey sprint` | `/vibey:sprint` |
| Ask test-engineer agent | `/vibey:agent-test-engineer` |
| Run sprint-planning workflow | `/vibey:sprint-planning` |

### 4. MCP Tool Names

**Claude Code:** `mcp__vibey__vibey_roadmap_status`
**Gemini:** `vibey_roadmap_status`

The tool functionality is identical; only the naming convention differs.

## Migration Steps

### Step 1: Export Gemini Extension

```bash
# From your Vibey-enabled project
vibey export gemini -o ./vibey-gemini-extension
```

### Step 2: Install Extension

```bash
./vibey-gemini-extension/install.sh
```

### Step 3: Learn Command Equivalents

Your most-used Claude Code interactions map to Gemini commands:

| Task | Claude Code | Gemini |
|------|-------------|--------|
| Check sprint status | "What's the sprint status?" | `/vibey:status` |
| Run tests | "Ask test-engineer to test this" | `/vibey:agent-test-engineer` |
| Security review | "Security review this code" | `/vibey:agent-security-reviewer` |
| Write docs | Ask documentation-engineer | `/vibey:agent-documentation-engineer` |
| Plan feature | Run single-feature-development | `/vibey:single-feature-development` |

### Step 4: Adapt Workflow Patterns

**Claude Code workflow (parallel):**
```
1. Ask coordinator to plan
2. Coordinator spawns: architect → developer → tester (in parallel where possible)
3. Git committer finalizes
```

**Gemini workflow (sequential):**
```
1. /vibey:agent-architecture-agent  (design)
2. /vibey:agent-backend-engineer    (implement)
3. /vibey:agent-test-engineer       (test)
4. /vibey:agent-security-reviewer   (review)
5. /vibey:agent-git-committer       (commit)
```

See GEMINI.md's "Sequential Workflow Execution" for command chains.

## Feature Comparison

### Fully Supported in Gemini

- All 19 agents (via `/vibey:agent-*` commands)
- All 16 workflows (via `/vibey:<workflow>` commands)
- MCP tools (roadmap, sprint, task management)
- Quality gates and standards
- Drift detection

### Different in Gemini

| Feature | Claude Code | Gemini Equivalent |
|---------|-------------|-------------------|
| Task spawning | `Task(agent)` | Sequential commands |
| Tiered orchestration | Automatic | Manual command chaining |
| Agent handoffs | Seamless | Explicit commands |

### Not Available in Gemini

- Parallel subagent execution
- Automatic workflow orchestration
- Real-time agent coordination

## Workflow Migration Examples

### Example 1: Feature Development

**Claude Code:**
```
Me: Build the user authentication feature
Claude: I'll coordinate this with multiple agents...
[Task: architect] [Task: developer] [Task: tester] [Task: security]
```

**Gemini:**
```
/vibey:single-feature-development Build user authentication

# Or step-by-step:
/vibey:agent-architecture-agent Design auth system
/vibey:agent-backend-engineer Implement auth
/vibey:agent-test-engineer Write auth tests
/vibey:agent-security-reviewer Review auth security
```

### Example 2: Sprint Planning

**Claude Code:**
```
Me: Plan the next sprint
Claude: I'll use the sprint-planning agent...
```

**Gemini:**
```
/vibey:sprint-planning

# Or use MCP directly:
Use vibey_roadmap_status to see current state
Use vibey_sprint_planning to create new sprint
```

### Example 3: Code Review

**Claude Code:**
```
Me: Do a comprehensive code review
Claude: I'll coordinate security, performance, and test reviews...
```

**Gemini:**
```
/vibey:agent-security-reviewer Review for vulnerabilities
/vibey:agent-performance-engineer Check for bottlenecks
/vibey:agent-test-engineer Verify test coverage
```

## Tips for Smooth Migration

### 1. Use the Orchestration Guide

GEMINI.md includes a "Sequential Workflow Execution" section with command chains for complex workflows. Refer to it when adapting Claude Code patterns.

### 2. Leverage MCP Tools Directly

Both platforms support MCP. When command syntax confuses you, use MCP tools:
```
Use vibey_roadmap_status to check the roadmap
Use vibey_agent_test_engineer to write tests
```

### 3. Chain Commands Explicitly

Instead of relying on automatic orchestration:
```
/vibey:status           # Check state
/vibey:agent-architect  # Design
/vibey:status           # Verify design
/vibey:agent-developer  # Implement
```

### 4. Keep Both Extensions

Nothing prevents you from having both:
- CLAUDE.md for Claude Code
- GEMINI.md for Gemini

Both are generated from the same source, ensuring consistency.

## Common Migration Issues

### Issue: "Gemini doesn't spawn agents like Claude"

**Solution:** Use explicit command sequences. Gemini's GEMINI.md includes workflow chains showing which commands to run in order.

### Issue: "Workflows feel slower"

**Solution:** This is expected—sequential vs parallel. Focus on the orchestration hints in GEMINI.md to minimize context switches.

### Issue: "Missing automatic handoffs"

**Solution:** Check the workflow's command chain in GEMINI.md. Each step suggests the next command.

### Issue: "Different output format"

**Solution:** Both platforms use the same MCP tools, so data structures are identical. Only presentation differs.

## Maintaining Both Platforms

If your team uses both Claude Code and Gemini:

```bash
# Generate both from single source
vibey export claude-code
vibey export gemini

# Both read from same frontmatter, ensuring consistency
```

Commit both context files to your repo so team members can use their preferred platform.

## Next Steps

- [Installation Guide](./GEMINI_INSTALLATION.md) - Set up Gemini extension
- [Orchestration Reference](./GEMINI_ORCHESTRATION.md) - Command chaining patterns
- [Troubleshooting](./GEMINI_TROUBLESHOOTING.md) - Common issues
