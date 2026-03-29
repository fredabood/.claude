# Hooks System Exploration Report

## Executive Summary

The Claude Code hooks system uses a **PreToolUse** pattern to intercept and gate tool calls before execution. Hooks can block execution by exiting with code 2. The system passes structured JSON data about the tool call via stdin, allowing hooks to inspect tool name, parameters, and context.

## 1. Hooks Architecture

### Location
`/Users/fredabood/homelab/.claude/hooks/` contains executable bash scripts.

### Configuration Format (settings.json)
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "ToolName(pattern)",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/script.sh",
            "timeout": <seconds>,
            "statusMessage": "Optional user-facing message"
          }
        ]
      }
    ]
  }
}
```

### Key Properties
- **matcher**: Pattern to identify which tool calls to intercept
  - Bash commands: `"Bash(git commit)"`, `"Bash(docker stop *)"`, `"Bash(cat .env*)"`
  - MCP tools: `"mcp__claude_ai_Atlassian__transitionJiraIssue"`, `"mcp__claude_ai_Atlassian__createJiraIssue"`
  - File operations: `"Read(.env)"`, `"Edit"`, `"Write"`
- **type**: Always `"command"` (executes the hook script)
- **timeout**: Seconds before hook times out (max: 120)
- **statusMessage**: Optional message shown to user during execution

## 2. Hook Execution Flow

### Invocation
1. User requests a tool call (e.g., via Skill or direct MCP invocation)
2. Claude Code matches the tool against registered matchers
3. If matched, ALL hooks in the matching entry are executed sequentially
4. Hook receives tool metadata via stdin as JSON
5. Hook exits with code:
   - **0** = allow (tool executes)
   - **2** = block (tool is prevented, error shown to user)

### JSON Input Structure
Hooks receive stdin containing:
```json
{
  "tool_name": "mcp__claude_ai_Atlassian__createJiraIssue",
  "tool_input": {
    "cloudId": "...",
    "projectKey": "...",
    "issueTypeName": "...",
    "summary": "...",
    // ... all tool parameters
  }
}
```

Key facts:
- `tool_name`: Full MCP function name or tool type (Bash, Read, Edit, Write)
- `tool_input`: Complete parameter dict passed to the tool
- For Bash: `tool_input.command` contains the shell command
- For Read/Edit/Write: `tool_input.file_path` contains the file path

## 3. Existing Hooks

### docker-safety-check.sh
**Matchers**: `Bash(docker stop *)`, `Bash(docker rm *)`, `Bash(docker rmi *)`, `Bash(docker kill *)`
**Function**: Blocks destructive Docker operations on production containers
**Exit 2 if**: Target is not a `-staging` container
**Pattern**: Inspects command string from `tool_input.command`

### env-secret-guard.sh
**Matchers**: `Bash(cat .env*)`, `Bash(grep * .env*)`, `Bash(head * .env*)`, `Read(.env)`, etc.
**Function**: Blocks direct reads of plaintext `.env` files
**Exit 2 if**: Attempting to read `.env` (not `.env.tpl`, `.env.example`, etc.)
**Pattern**: Uses negative lookahead regex `\.env(?!\.\w)` to distinguish `.env` from variants

### label-taxonomy-check.sh
**Matchers**: `mcp__claude_ai_Atlassian__createJiraIssue`, `mcp__claude_ai_Atlassian__editJiraIssue`
**Function**: Validates that tickets include required taxonomy labels
**Exit 2 if**: Missing work pattern label (scraper/agent/workflow/deployment/pipeline/migration/platform) OR missing infrastructure layer label (L1-platform/L2-services/L3-framework/L4-domain)
**Pattern**: Extracts `tool_input.fields.labels` and validates against allowlist

### workflow-gate.sh
**Matchers**: 
- `Bash(git commit)`
- `Edit`, `Write` (file operations)
- `mcp__claude_ai_Atlassian__transitionJiraIssue`

**Function**: Enforces workflow phase gates
- Blocks code edits until Phase 3 (Plan) complete
- Blocks git commits until Phase 4 (Git Setup) complete
- Blocks transition to Done until Phases 6-7 complete
**Exit 2 if**: State file indicates required phase is incomplete
**Pattern**: Reads `.workflow-state.json` to check phase completion timestamps

### lifecycle-field-check.sh
**Matchers**: `mcp__claude_ai_Atlassian__transitionJiraIssue`
**Function**: Validates lifecycle field completeness before status transitions
**Exit 2 if**: Transitioning to Implementation Complete (81) or Review Complete (91) without required fields (currently logged only, not blocking)
**Pattern**: Extracts `tool_input.transition.id` to determine transition type

### label-taxonomy-check.sh
**Matchers**: `mcp__claude_ai_Atlassian__createJiraIssue`, `mcp__claude_ai_Atlassian__editJiraIssue`
**Function**: Validates taxonomy labels on Jira tickets
**Exit 2 if**: Required labels missing/invalid
**Pattern**: Inspects `tool_input.fields.labels`

### memory-frontmatter-check.sh
**Matchers**: `Bash(git commit)`
**Function**: Validates vault frontmatter before commits
**Exit 2 if**: Memory files lack proper YAML frontmatter
**Pattern**: Checks git staged files for .md frontmatter

### pre-commit-tests.sh
**Matchers**: `Bash(git commit)`
**Function**: Runs pre-commit quality gates
**Exit 2 if**: Tests fail
**Pattern**: Runs linters/tests on staged code

### ticket-reference-check.sh
**Matchers**: `Bash(git commit)`
**Function**: Ensures commit references a work item
**Exit 2 if**: Commit message lacks issue reference
**Pattern**: Checks commit message for PROJ-### pattern

## 4. MCP Tool Interception

### Current Coverage
The system already intercepts Atlassian MCP calls:
- `mcp__claude_ai_Atlassian__transitionJiraIssue`
- `mcp__claude_ai_Atlassian__createJiraIssue`
- `mcp__claude_ai_Atlassian__editJiraIssue`

### How to Intercept All Atlassian Calls
Matcher pattern: `mcp__claude_ai_Atlassian__*` (regex/glob matching supported)

The matcher field supports:
- Exact function names
- Wildcards: `Bash(docker *)`, `Read(.env*)`
- Seems to support glob/prefix matching based on existing patterns

## 5. Skill Execution Context

### Current State
**No built-in mechanism exists to detect if an MCP call comes from within a skill.**

Hook scripts receive:
- `tool_name`: The MCP function name
- `tool_input`: The parameters
- **NO metadata** indicating:
  - Which skill is executing (if any)
  - Call stack/context
  - Whether user triggered directly vs. via skill

### Potential Detection Methods

#### Option A: Environment Variables (Would require Claude Code harness support)
If Claude Code sets `CLAUDE_SKILL_NAME` or `CLAUDE_SKILL_CONTEXT` when executing skills:
```bash
if [[ -n "$CLAUDE_SKILL_NAME" ]]; then
  # Called from within a skill — allow
  exit 0
fi
```
**Status**: Not currently implemented (not found in any hooks)

#### Option B: Calling Process Context (Limited, fragile)
Check parent process or inherited env vars, but:
- Unreliable across shells
- Would break if execution model changes
- Not recommended

#### Option C: Call Parameter Inspection
Add a "source" or "context" parameter to MCP calls from skills:
- Skills explicitly add `"callContext": "skill-create-ticket"`
- Hook inspects this parameter
- **Status**: Would require changes to how skills invoke MCP tools

#### Option D: Hook Chain with State File
Skills write to a state file (e.g., `.skill-execution-context.json`) before calling MCP:
```json
{
  "skill_name": "create-ticket",
  "started_at": "2026-03-28T19:35:00Z",
  "pid": 12345
}
```
Hook checks file before blocking:
```bash
if [[ -f ".skill-execution-context.json" ]]; then
  STARTED_AT=$(jq -r .started_at .skill-execution-context.json)
  NOW=$(date -u +%s)
  if (( NOW - $(date -d "$STARTED_AT" +%s) < 300 )); then
    # Called recently from skill context
    exit 0
  fi
fi
```
**Status**: Feasible without harness changes; requires skill coordination

## 6. Exit Codes & Behavior

| Code | Behavior |
|------|----------|
| **0** | Allow tool execution to proceed |
| **2** | Block tool execution; surface hook output as error to user |
| **Non-zero** (other) | Block tool; treated as hook failure |
| **Timeout** | Hook exceeded timeout window; treated as block |

Hook output is captured and shown to user in Claude Code UI.

## 7. Key Limitations

1. **No skill context detection**: Hooks cannot currently determine if a call originates from within a skill
2. **Sequential execution**: Multiple hooks run sequentially; later hooks see same `tool_input` regardless of earlier hook state
3. **No tool parameter modification**: Hooks can only allow/block, not modify parameters
4. **Single stdin stream**: All tool metadata in one JSON object
5. **No access to session state**: Hooks don't inherit Claude Code session variables

## 8. Configuration Matching Rules

Based on observed patterns in settings.json:

- **Exact match**: `"mcp__claude_ai_Atlassian__transitionJiraIssue"` → matches only that tool
- **Prefix match** (wildcards): `"Bash(docker *)"` → matches `Bash(docker stop)`, `Bash(docker rm)`, etc.
- **Literal patterns**: `"Bash(cat .env*)"` → exact string with glob in quotes
- **Broad matchers**: `"Edit"`, `"Write"` → all Edit/Write operations
- **Glob/prefix in tool name**: `"mcp__claude_ai_Atlassian__*"` → likely matches all Atlassian MCP tools (untested)

## 9. Recommendations for Blocking All Direct Atlassian Calls

### Approach 1: Global Matcher + State File (Recommended)

Add to settings.json:
```json
{
  "matcher": "mcp__claude_ai_Atlassian__*",
  "hooks": [
    {
      "type": "command",
      "command": ".claude/hooks/atlassian-skill-gate.sh",
      "timeout": 5,
      "statusMessage": "Checking skill context..."
    }
  ]
}
```

Create `.claude/hooks/atlassian-skill-gate.sh`:
```bash
#!/usr/bin/env bash
# Blocks direct Atlassian MCP calls unless executed from within a skill

if [[ -f ".skill-execution-context.json" ]]; then
  STARTED_AT=$(jq -r .started_at .skill-execution-context.json 2>/dev/null || echo "")
  if [[ -n "$STARTED_AT" ]]; then
    NOW=$(date +%s)
    ELAPSED=$(( NOW - $(date -d "$STARTED_AT" +%s 2>/dev/null || echo 0) ))
    # Allow if called within 5 minutes of skill start
    if (( ELAPSED < 300 )); then
      exit 0
    fi
  fi
fi

echo "Atlassian MCP calls must be made through the appropriate skill:"
echo "  /create-ticket    — Create Jira tickets"
echo "  /complete-task    — Complete tasks"
echo "  /start-task       — Start tasks"
echo "  etc."
echo ""
echo "Direct API calls bypass quality gates and validation."

exit 2
```

Skills would need to manage the context file:
```bash
# In skill execution
echo '{
  "skill_name": "create-ticket",
  "started_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
  "pid": '$$'
}' > .skill-execution-context.json

# ... skill executes MCP calls ...

rm -f .skill-execution-context.json
```

### Approach 2: Check Hook on Specific Tools

Less aggressive: intercept only specific high-risk Atlassian calls:
```json
{
  "matcher": "mcp__claude_ai_Atlassian__createJiraIssue",
  "hooks": [...]
},
{
  "matcher": "mcp__claude_ai_Atlassian__editJiraIssue",
  "hooks": [...]
},
{
  "matcher": "mcp__claude_ai_Atlassian__transitionJiraIssue",
  "hooks": [...]
}
```

## 10. Current Hook Configuration in settings.json

The following MCP hooks are already active:

```json
{
  "matcher": "mcp__claude_ai_Atlassian__transitionJiraIssue",
  "hooks": [
    {
      "type": "command",
      "command": ".claude/hooks/workflow-gate.sh",
      "timeout": 5,
      "statusMessage": "Checking workflow gates..."
    }
  ]
},
{
  "matcher": "mcp__claude_ai_Atlassian__createJiraIssue",
  "hooks": [
    {
      "type": "command",
      "command": ".claude/hooks/label-taxonomy-check.sh",
      "timeout": 10,
      "statusMessage": "Validating taxonomy labels..."
    }
  ]
},
{
  "matcher": "mcp__claude_ai_Atlassian__editJiraIssue",
  "hooks": [
    {
      "type": "command",
      "command": ".claude/hooks/label-taxonomy-check.sh",
      "timeout": 10,
      "statusMessage": "Validating taxonomy labels..."
    }
  ]
}
```

## Summary Table

| Feature | Supported? | Evidence |
|---------|-----------|----------|
| Intercept MCP calls | ✓ YES | Multiple matchers for `mcp__claude_ai_Atlassian__*` |
| Block via exit code 2 | ✓ YES | All hooks use this pattern |
| Wildcard matching | ✓ YES | `Bash(docker *)`, `Bash(cat .env*)` patterns |
| Glob matching for MCP | ? UNTESTED | Likely, but unconfirmed if `mcp__*__*` works |
| Inspect tool parameters | ✓ YES | `tool_input` dict in stdin JSON |
| Detect skill context | ✗ NO | No built-in env vars or metadata |
| Modify tool behavior | ✗ NO | Hooks can only allow/block |
| Sequential execution | ✓ YES | Multiple hooks run in order |

---

**Report Generated**: 2026-03-28  
**Status**: Complete exploration; ready for implementation decisions
