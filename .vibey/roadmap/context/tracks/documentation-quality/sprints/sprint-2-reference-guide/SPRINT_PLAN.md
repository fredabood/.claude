# Sprint 2: Reference Guide Improvements

## Overview
- **Track:** Documentation Quality
- **Sprint ID:** 01KCMTKWCX621JWPZZ99DG2M2G
- **Tasks:** 11
- **Focus:** Improve CLI and MCP reference documentation quality, completeness, and usability

## Success Criteria
- [ ] CLI reference matches MCP reference format and quality
- [ ] All 169 CLI commands have complete parameter documentation
- [ ] All commands have at least one usage example
- [ ] Quick start sections added to both references
- [ ] Cross-references between related commands
- [ ] Error documentation added

---

## Task 1: Fix Truncated CLI Descriptions
**ID:** `01KCMGMR8FQJBQAY2YSZ47SAHK`
**Priority:** High | **Complexity:** Simple | **Type:** Development

### Problem
CLI reference generator truncates descriptions with '...' making them incomplete and unhelpful.

### File to Modify
`vibey/operations/docs/cli_reference_generator.py`

### Implementation Steps
1. Find the description truncation logic:
   ```bash
   grep -n "truncat\|max.*len\|\.\.\.\"" vibey/operations/docs/cli_reference_generator.py
   ```

2. Increase or remove the max length:
   ```python
   # Before
   description = description[:100] + "..." if len(description) > 100 else description

   # After - remove truncation or increase significantly
   # Option 1: Remove truncation entirely
   # Option 2: Increase to 500+ characters
   max_description_length = 500
   ```

3. Regenerate CLI reference to verify fix:
   ```bash
   vibey docs generate-cli
   ```

### Acceptance Criteria
- [ ] No descriptions end with '...' unless legitimately part of text
- [ ] Full descriptions visible in CLI_REFERENCE.md
- [ ] Generator passes tests after modification

---

## Task 2: Fix Command Index Organization
**ID:** `01KCMGMVY8VX3RT6E5V5QJ2ST3`
**Priority:** High | **Complexity:** Medium | **Type:** Development

### Problem
CLI reference restarts alphabetical numbering for each command group instead of using continuous ordering.

### File to Modify
`vibey/operations/docs/cli_reference_generator.py`

### Current vs Expected
```markdown
# Current (broken)
## Database Commands
1. db backup
2. db rebuild

## Deploy Commands
1. deploy list      <- Restarts at 1
2. deploy run

# Expected (fixed)
## Database Commands
1. db backup
2. db rebuild

## Deploy Commands
3. deploy list      <- Continues from previous
4. deploy run
```

### Implementation Steps
1. Find the index generation logic:
   ```python
   # Look for list enumeration or numbering reset
   grep -n "enumerate\|index\|\.1\." vibey/operations/docs/cli_reference_generator.py
   ```

2. Implement continuous numbering:
   ```python
   command_index = 0
   for group in command_groups:
       for command in group.commands:
           command_index += 1
           # Use command_index instead of local index
   ```

3. Regenerate and verify ordering

### Acceptance Criteria
- [ ] Single continuous numbering across all command groups
- [ ] Index numbers never restart within document
- [ ] Table of contents links correctly to numbered items

---

## Task 3: Restructure CLI Reference to Match MCP Format
**ID:** `01KCMK8W265T2N76F6ATD3AWX3`
**Priority:** High | **Complexity:** Medium | **Type:** Development

### Problem
CLI_REFERENCE.md has inconsistent format compared to better-organized MCP_REFERENCE.md.

### Files to Modify
- `vibey/operations/docs/cli_reference_generator.py`
- `docs/reference/CLI_REFERENCE.md` (regenerated)

### Target Format (from MCP_REFERENCE.md)
```markdown
## command_name

**Description:** Full description of what the command does.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| --option1 | string | Yes | What this option does |
| --option2 | int | No | Optional parameter (default: 10) |

### Example

```bash
vibey command_name --option1 "value" --option2 20
```

### See Also
- related_command_1
- related_command_2
```

### Implementation Steps
1. Study MCP reference generator format:
   ```bash
   head -100 vibey/operations/docs/mcp_reference_generator.py
   ```

2. Update CLI generator to produce:
   - Parameter tables (not inline lists)
   - Type information for each parameter
   - Required vs optional indicators
   - Default values column
   - Examples section per command
   - See Also section (can be empty initially)

3. Regenerate and compare structure

### Acceptance Criteria
- [ ] CLI commands have parameter tables
- [ ] Type information shown for all parameters
- [ ] Required/optional clearly indicated
- [ ] Default values documented
- [ ] Format visually matches MCP reference

---

## Task 4: Add CLI Quick Start Section
**ID:** `01KCMGMZMXPR76A4HNE5AAH77T`
**Priority:** High | **Complexity:** Medium | **Type:** Documentation

### Problem
Users must read through entire CLI reference to find common workflows. Need quick start at top.

### File to Modify
`docs/reference/CLI_REFERENCE.md` (add manually or via generator)

### Quick Start Content
```markdown
# CLI Reference

## Quick Start

### Most Common Commands

```bash
# Check roadmap status
vibey roadmap status

# Start working on a task
vibey roadmap start <task-id>

# Complete a task
vibey roadmap complete <task-id>

# List tasks in current sprint
vibey roadmap list tasks --sprint <sprint-id>

# Show task details
vibey roadmap show <task-id>

# Deploy to a platform
vibey deploy run --platform cursor
```

### Common Workflows

#### Daily Development Flow
```bash
vibey roadmap status              # See what's in progress
vibey roadmap start 01KC...       # Start your task
# ... do work ...
vibey roadmap complete 01KC...    # Mark complete
```

#### Database Maintenance
```bash
vibey roadmap db status           # Check sync status
vibey roadmap db rebuild          # Rebuild from YAML
vibey roadmap db validate         # Verify integrity
```

---
```

### Implementation Steps
1. Add Quick Start section to CLI reference generator or template
2. Include the 10 most-used commands based on typical workflows
3. Add 2-3 common workflow examples
4. Place at top of document before full command reference

### Acceptance Criteria
- [ ] Quick Start section appears at top of CLI_REFERENCE.md
- [ ] Most common commands listed with brief descriptions
- [ ] Common workflows shown as copy-paste examples
- [ ] Section takes less than 1 screen to read

---

## Task 5: Add MCP Usage Guidance Section
**ID:** `01KCMGN3B3CKCNWSP3V8ZE3EBQ`
**Priority:** High | **Complexity:** Medium | **Type:** Documentation

### Problem
Users don't know when to use CLI commands vs MCP tools. Need guidance.

### File to Modify
`docs/reference/MCP_REFERENCE.md`

### Content to Add
```markdown
## When to Use MCP vs CLI

### Use MCP Tools When:
- **AI Assistant Integration** - Working within Claude, Cursor, or other AI tools
- **Programmatic Access** - Building automation or integrations
- **Structured Data** - Need JSON responses for processing
- **Context Preservation** - AI needs to maintain conversation context

### Use CLI Commands When:
- **Terminal Workflows** - Direct command-line interaction
- **Shell Scripts** - Automation via bash/shell
- **Human Readable** - Want formatted, colorized output
- **Quick Operations** - One-off commands

### Mapping Table

| Operation | CLI Command | MCP Tool |
|-----------|------------|----------|
| Get status | `vibey roadmap status` | `roadmap_status` |
| Start task | `vibey roadmap start <id>` | `task_start` |
| Complete task | `vibey roadmap complete <id>` | `task_complete` |
| List tasks | `vibey roadmap list tasks` | `task_list` |
| Show details | `vibey roadmap show <id>` | `roadmap_show` |

### Integration Examples

#### Using MCP in Claude Code
The MCP server automatically provides tools when connected. Use natural language:
- "Show me the current roadmap status"
- "Start task 01KC2D0JK7READW9KAK1HBX4B8"
- "What tasks are in progress?"
```

### Implementation Steps
1. Add "When to Use MCP vs CLI" section near top of MCP reference
2. Create comparison table for common operations
3. Add integration examples for major AI platforms
4. Link to CLI reference for CLI-specific documentation

### Acceptance Criteria
- [ ] Clear guidance on MCP vs CLI usage
- [ ] Mapping table for common operations
- [ ] Integration examples included
- [ ] Cross-reference to CLI documentation

---

## Task 6: Audit CLI Commands for Complete Parameter Documentation
**ID:** `01KCMK82R7GHN3HHEG6FSDDKG7`
**Priority:** High | **Complexity:** Complex | **Type:** Documentation

### Problem
169 CLI commands may have incomplete parameter documentation - missing types, defaults, or options.

### Audit Process
1. Generate list of all commands:
   ```bash
   vibey --help 2>/dev/null | grep -E "^  [a-z]"
   vibey roadmap --help 2>/dev/null | grep -E "^  [a-z]"
   # ... for each command group
   ```

2. For each command, verify documentation includes:
   - [ ] All parameters listed
   - [ ] Parameter types (string, int, bool, choice)
   - [ ] Required vs optional marked
   - [ ] Default values shown
   - [ ] Valid choices/options listed
   - [ ] At least one example

3. Create audit checklist:
   ```markdown
   | Command | All Params | Types | Defaults | Choices | Example | Status |
   |---------|------------|-------|----------|---------|---------|--------|
   | roadmap status | Yes | Yes | Yes | N/A | Yes | Complete |
   | roadmap start | Yes | No | No | N/A | No | NEEDS WORK |
   ```

### Implementation Steps
1. Run CLI introspector to get actual command signatures:
   ```bash
   vibey docs generate-cli --dry-run --verbose
   ```

2. Compare introspected data against documentation

3. Fix generator to capture missing information

4. Regenerate documentation

### Acceptance Criteria
- [ ] Audit spreadsheet/checklist created
- [ ] All 169 commands reviewed
- [ ] Generator updated to capture full parameter info
- [ ] Regenerated docs pass completeness check

---

## Task 7: Ensure All CLI Commands Have At Least One Example
**ID:** `01KCMJMHRXMRCEXQ0N71R3BWR1`
**Priority:** Medium | **Complexity:** Medium | **Type:** Documentation

### Problem
Some CLI commands lack usage examples, making them harder to use correctly.

### Implementation Steps
1. Identify commands without examples:
   ```bash
   grep -B5 "^## " docs/reference/CLI_REFERENCE.md | grep -A5 "^## " | grep -L "Example"
   ```

2. For each command without examples, add:
   ```markdown
   ### Example

   ```bash
   vibey <command> <required-args> [optional-args]
   ```

   Output:
   ```
   Expected output here
   ```
   ```

3. Examples should show:
   - Basic usage with required parameters
   - Common optional parameter combinations
   - Expected output format

### Acceptance Criteria
- [ ] Every command has at least one example
- [ ] Examples show realistic usage
- [ ] Expected output shown where helpful

---

## Task 8: Add Cross-References Between Related Commands
**ID:** `01KCMGNAV3952EVY80A6GWYBD5`
**Priority:** Medium | **Complexity:** Medium | **Type:** Documentation

### Problem
Related commands aren't linked, requiring users to search for related functionality.

### Implementation Steps
1. Define command relationships:
   ```yaml
   roadmap_status:
     related: [roadmap_show, roadmap_list]

   roadmap_start:
     related: [roadmap_complete, roadmap_show]

   db_rebuild:
     related: [db_status, db_validate]
   ```

2. Add "See Also" section to each command:
   ```markdown
   ### See Also
   - `vibey roadmap show` - Show detailed item information
   - `vibey roadmap list tasks` - List all tasks
   ```

3. Update generator to include relationships or add manually

### Acceptance Criteria
- [ ] Related commands linked in "See Also" sections
- [ ] At least 50% of commands have related command links
- [ ] Links are bidirectional where appropriate

---

## Task 9: Regenerate Reference Documentation
**ID:** `01KCMGN7290RWZE8WHWXNJA4QQ`
**Priority:** Medium | **Complexity:** Simple | **Type:** Documentation

### Problem
After generator fixes, documentation needs regeneration.

### Implementation Steps
1. Ensure all generator fixes are complete (Tasks 1-3)

2. Regenerate documentation:
   ```bash
   vibey docs generate-cli
   vibey docs generate-mcp
   ```

3. Review generated output for quality

4. Commit regenerated documentation

### Acceptance Criteria
- [ ] CLI reference regenerated without errors
- [ ] MCP reference regenerated without errors
- [ ] Generated docs include all improvements from Tasks 1-3
- [ ] No manual edits lost (check for manual sections)

---

## Task 10: Add Error Reference Section to CLI Documentation
**ID:** `01KCMJTM34T53WT7CVH0NQX617`
**Priority:** Low | **Complexity:** Medium | **Type:** Documentation

### Problem
Users encounter errors but have no reference for understanding or resolving them.

### Content to Add
```markdown
## Common Errors

### Roadmap Errors

#### `Error: Task not found: <id>`
**Cause:** The specified task ID doesn't exist in the database.
**Solution:**
1. Verify the task ID is correct: `vibey roadmap show <id>`
2. Rebuild database if recently added: `vibey roadmap db rebuild`

#### `Error: Task is blocked`
**Cause:** Task has unresolved dependencies or blockers.
**Solution:**
1. Check blockers: `vibey roadmap show <id>`
2. Resolve blocking tasks first

### Database Errors

#### `Error: Database out of sync`
**Cause:** YAML files modified outside CLI.
**Solution:** `vibey roadmap db rebuild`

### Validation Errors

#### `Error: Invalid status transition`
**Cause:** Attempted invalid status change (e.g., not_started → completed).
**Solution:** Follow valid transitions: not_started → in_progress → completed
```

### Implementation Steps
1. Collect common error messages from codebase:
   ```bash
   grep -rh "raise.*Error\|Error:" vibey/ --include="*.py" | sort | uniq
   ```

2. Document each error with:
   - Error message
   - Cause
   - Solution steps

3. Organize by command group

### Acceptance Criteria
- [ ] Top 20 most common errors documented
- [ ] Each error has cause and solution
- [ ] Organized by category/command group

---

## Task 11: Add Schema Explanations for Complex MCP Parameters
**ID:** `01KCMJN4MFC7TAG8P01BC7RP5W`
**Priority:** Low | **Complexity:** Medium | **Type:** Documentation

### Problem
MCP tools with complex parameters (arrays, objects) lack schema documentation.

### Implementation Steps
1. Identify complex parameters:
   ```bash
   grep -E "List\[|Dict\[|Optional\[.*\[" vibey/mcp/
   ```

2. For each complex parameter, add schema documentation:
   ```markdown
   ### Parameters

   #### filters (object)
   Filter criteria for task listing.

   ```json
   {
     "status": "in_progress",      // Optional: Filter by status
     "track_id": "01KC...",        // Optional: Filter by track
     "sprint_id": "01KC...",       // Optional: Filter by sprint
     "assigned_agent": "claude"    // Optional: Filter by assignee
   }
   ```

   #### tags (array)
   List of tags to apply.

   ```json
   ["bug", "documentation", "high-priority"]
   ```
   ```

3. Add to MCP reference generator or manually to MCP_REFERENCE.md

### Acceptance Criteria
- [ ] All complex parameters have schema examples
- [ ] JSON examples show valid structure
- [ ] Optional vs required fields noted

---

## Sprint Completion Checklist
- [ ] All 11 tasks completed
- [ ] CLI reference regenerated with improvements
- [ ] MCP reference updated with guidance
- [ ] Quick start sections added
- [ ] Cross-references added
- [ ] Error documentation added
- [ ] All changes committed
