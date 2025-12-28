# Task 4.5: Update MCP_REFERENCE.md with New/Changed Tools

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJKTRVZS618BM5ZZTQ3443A |
| Sprint | 4 - Documentation Sync |
| Type | documentation |
| Complexity | medium |
| Priority | high |
| Estimated Tokens | ~2,500 |
| Dependencies | Task 4.1 (Documentation drift audit) |

---

## Objective

Update the MCP (Model Context Protocol) reference documentation with all new and changed tools, resources, and prompts. Currently documented: 76 tools, 8 resources, 4 prompts. Use the auto-generation tool `vibey docs generate-mcp` and supplement with manual documentation for any MCP items added since December 12, 2024.

---

## Files to Update

### Primary File

| File | Location | Current Stats |
|------|----------|---------------|
| `MCP_REFERENCE.md` | `docs/reference/MCP_REFERENCE.md` | 76 tools, 8 resources, 4 prompts |

### Source Files (for verification)

| Location | Purpose |
|----------|---------|
| `vibey/mcp/server.py` | Main MCP server |
| `vibey/mcp/tools/` | Tool implementations |
| `vibey/mcp/resources/` | Resource implementations |
| `vibey/mcp/prompts/` | Prompt implementations |
| `vibey/mcp/handlers/` | Request handlers |

---

## Verification Commands

### 1. Generate Updated MCP Reference

```bash
# Run the auto-generation command
vibey docs generate-mcp

# Or with explicit output path
vibey docs generate-mcp --output docs/reference/MCP_REFERENCE.md

# Preview without writing
vibey docs generate-mcp --dry-run
```

### 2. Compare Tool Counts

```bash
# Count documented tools (current)
grep -c "^### " docs/reference/MCP_REFERENCE.md

# Count actual tools from code
grep -r "@server.tool\|register_tool" vibey/mcp/ | wc -l

# List tool definitions
grep -r "def.*tool" vibey/mcp/tools/*.py | head -20
```

### 3. Identify New Tools Since Dec 12

```bash
# Find MCP changes in git history
git log --oneline --since="2024-12-12" -- "vibey/mcp/"

# Show new tool registrations
git diff --since="2024-12-12" -- "vibey/mcp/*.py" | grep -A5 "@server.tool"

# List all tool files
ls -la vibey/mcp/tools/
```

### 4. Verify Tool Categories

```bash
# Count tools by category (from code)
grep -r "category=" vibey/mcp/tools/ | cut -d= -f2 | sort | uniq -c

# List resource files
ls -la vibey/mcp/resources/

# List prompt files
ls -la vibey/mcp/prompts/
```

---

## Analysis Steps

### Step 1: Run Auto-Generation

Execute the documentation generator:

```bash
vibey docs generate-mcp --output docs/reference/MCP_REFERENCE.md
```

Capture:
- Total tools generated
- Total resources generated
- Total prompts generated
- Any warnings or errors
- Missing docstrings flagged

### Step 2: Identify Changes Since Last Generation

Compare generated output with previous version:

```bash
# Create backup of current
cp docs/reference/MCP_REFERENCE.md docs/reference/MCP_REFERENCE.md.bak

# Generate new version
vibey docs generate-mcp --output docs/reference/MCP_REFERENCE.md

# Diff to see changes
diff docs/reference/MCP_REFERENCE.md.bak docs/reference/MCP_REFERENCE.md
```

### Step 3: Document New MCP Items Since Dec 12

Known new items to check:

| Category | Items | Purpose |
|----------|-------|---------|
| Token tools | estimate_tokens, track_usage | Token management |
| Implementation tools | start_implementation, get_implementation_status | Implementation mode |
| Context tools | get_context, set_context | Context system |
| Status tools | get_planned_status, set_planned_status | Planned status |

For each new item, document:
- Tool/resource/prompt name
- Description
- Parameters with types
- Return value
- Examples

### Step 4: Verify All Tools Work

Test MCP tools via the server:

```bash
# Start MCP server (if applicable)
vibey mcp serve --port 3000

# Or test via CLI interface
vibey mcp list-tools
vibey mcp describe-tool <tool-name>
```

---

## Before/After Comparison Approach

### Comparison Method

Create a change log tracking:

| Item | Type | Before | After | Change |
|------|------|--------|-------|--------|
| `roadmap_get_status` | Tool | Documented | Documented | Unchanged |
| `estimate_tokens` | Tool | Missing | Documented | Added |
| `implementation_start` | Tool | Missing | Documented | Added |

### Change Categories

| Category | Definition | Example |
|----------|------------|---------|
| Added | New tool/resource/prompt | `estimate_tokens` |
| Updated | Changed parameters/behavior | `roadmap_create_task` |
| Deprecated | Marked for removal | N/A |
| Removed | No longer exists | N/A |
| Unchanged | No changes | Most tools |

---

## Output Format

### MCP_REFERENCE.md Structure

The reference should follow this structure:

```markdown
# MCP Reference

## Overview
- Total Tools: XX
- Total Resources: X
- Total Prompts: X
- Protocol Version: X.X
- Last Updated: [Date]

## Quick Reference

### Tools by Category

| Category | Count | Examples |
|----------|-------|----------|
| Roadmap | X | roadmap_status, roadmap_create_task |
| Implementation | X | implementation_start, implementation_complete |
| Token | X | estimate_tokens, track_usage |

## Tools

### roadmap_status

Get the current roadmap status and progress.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `verbose` | boolean | No | Include details |

**Returns:**
\`\`\`json
{
  "status": "active",
  "progress": 0.75,
  "tasks": [...]
}
\`\`\`

**Example:**
\`\`\`json
{
  "tool": "roadmap_status",
  "arguments": {
    "verbose": true
  }
}
\`\`\`

[... continue for all tools ...]

## Resources

### workflow_template

Access workflow templates for AI assistants.

**URI Pattern:** `vibey://workflow/{name}`

**Available Resources:**
| Name | Description |
|------|-------------|
| `handoff` | Session handoff template |
| `context` | Context summary template |

[... continue for all resources ...]

## Prompts

### quality_gate

Prompt for code quality assessment.

**Arguments:**
| Name | Type | Description |
|------|------|-------------|
| `scope` | string | Assessment scope |

[... continue for all prompts ...]
```

---

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| Updated `MCP_REFERENCE.md` | `docs/reference/` | Complete MCP documentation |
| `MCP_CHANGES_LOG.md` | `sprint-4/outputs/` | Log of all changes made |
| `MCP_VERIFICATION_RESULTS.md` | `sprint-4/outputs/` | Test results for tools |

---

## Acceptance Criteria

- [ ] `vibey docs generate-mcp` executed successfully
- [ ] MCP_REFERENCE.md updated with current tool set
- [ ] All new tools since Dec 12 documented
- [ ] All new resources since Dec 12 documented
- [ ] All new prompts since Dec 12 documented
- [ ] Changed tool signatures updated
- [ ] All documented tools verified to exist in code
- [ ] Parameter types accurately documented
- [ ] Return types accurately documented
- [ ] Total counts updated (76 tools, 8 resources, 4 prompts or current)
- [ ] Change log created listing all updates

---

## Notes

- The `vibey docs generate-mcp` command auto-generates most documentation
- Manual additions may be needed for complex examples
- Ensure examples follow MCP protocol format
- Focus on tools used by AI assistants
- Coordinate with Task 4.1 findings for known drift areas
- Some tools may be internal-only (document accordingly)
