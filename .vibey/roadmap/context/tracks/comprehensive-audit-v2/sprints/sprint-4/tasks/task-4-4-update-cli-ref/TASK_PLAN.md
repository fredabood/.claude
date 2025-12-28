# Task 4.4: Update CLI_REFERENCE.md with New/Changed Commands

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJKTRVZS618BM5ZZTQ34439 |
| Sprint | 4 - Documentation Sync |
| Type | documentation |
| Complexity | medium |
| Priority | high |
| Estimated Tokens | ~2,500 |
| Dependencies | Task 4.1 (Documentation drift audit) |

---

## Objective

Update the CLI reference documentation with all new and changed commands. Currently documented: 203 commands. Use the auto-generation tool `vibey docs generate-cli` and supplement with manual documentation for any commands added since December 12, 2024.

---

## Files to Update

### Primary File

| File | Location | Current Size |
|------|----------|--------------|
| `CLI_REFERENCE.md` | `docs/reference/CLI_REFERENCE.md` | ~203 commands |

### Source Files (for verification)

| Location | Purpose |
|----------|---------|
| `vibey/cli/main.py` | CLI entry point |
| `vibey/cli/commands.py` | Main command implementations |
| `vibey/cli/roadmap/` | Roadmap command group |
| `vibey/cli/deploy/` | Deploy command group |
| `vibey/cli/docs/` | Docs command group |
| `vibey/cli/implement/` | Implement command group |

---

## Verification Commands

### 1. Generate Updated CLI Reference

```bash
# Run the auto-generation command
vibey docs generate-cli

# Or with explicit output path
vibey docs generate-cli --output docs/reference/CLI_REFERENCE.md

# Preview without writing
vibey docs generate-cli --dry-run
```

### 2. Compare Command Counts

```bash
# Count documented commands (current)
grep -c "^### " docs/reference/CLI_REFERENCE.md

# Count actual commands
vibey --help 2>&1 | wc -l

# List all command groups
vibey --help

# Count commands per group
vibey roadmap --help | grep -c "^\s"
vibey deploy --help | grep -c "^\s"
vibey docs --help | grep -c "^\s"
vibey implement --help | grep -c "^\s" 2>/dev/null
```

### 3. Identify New Commands Since Dec 12

```bash
# Find CLI changes in git history
git log --oneline --since="2024-12-12" -- "vibey/cli/"

# Show new command registrations
git diff --since="2024-12-12" -- "vibey/cli/*.py" | grep "@click.command"

# List implement commands (new)
vibey implement --help
```

### 4. Verify Command Documentation

```bash
# Check specific command documentation
vibey roadmap status --help
vibey roadmap show --help
vibey roadmap start --help
vibey implement start --help 2>/dev/null
vibey implement complete --help 2>/dev/null
```

---

## Analysis Steps

### Step 1: Run Auto-Generation

Execute the documentation generator:

```bash
vibey docs generate-cli --output docs/reference/CLI_REFERENCE.md
```

Capture:
- Total commands generated
- Any warnings or errors
- Missing docstrings flagged

### Step 2: Identify Changes Since Last Generation

Compare generated output with previous version:

```bash
# Create backup of current
cp docs/reference/CLI_REFERENCE.md docs/reference/CLI_REFERENCE.md.bak

# Generate new version
vibey docs generate-cli --output docs/reference/CLI_REFERENCE.md

# Diff to see changes
diff docs/reference/CLI_REFERENCE.md.bak docs/reference/CLI_REFERENCE.md
```

### Step 3: Document New Commands Since Dec 12

Known new command groups to check:

| Group | Commands | Added |
|-------|----------|-------|
| `vibey implement` | start, status, complete, pause, resume | Dec 12+ |
| `vibey roadmap` | New subcommands | Dec 12+ |
| `vibey context` | Context management | Dec 12+ |

For each new command, document:
- Command name and path
- Description
- Options and flags
- Arguments
- Examples

### Step 4: Verify All Commands Work

Test each documented command:

```bash
# Test roadmap commands
vibey roadmap status
vibey roadmap show --help

# Test deploy commands
vibey deploy list
vibey deploy --help

# Test docs commands
vibey docs check-drift
vibey docs --help

# Test implement commands
vibey implement --help
```

---

## Before/After Comparison Approach

### Comparison Method

Create a change log tracking:

| Command | Before | After | Change Type |
|---------|--------|-------|-------------|
| `vibey roadmap status` | Documented | Documented | Unchanged |
| `vibey implement start` | Missing | Documented | Added |
| `vibey roadmap show` | Old options | New options | Updated |

### Change Categories

| Category | Definition | Example |
|----------|------------|---------|
| Added | New command | `vibey implement start` |
| Updated | Changed options/behavior | `vibey roadmap status` |
| Deprecated | Marked for removal | N/A |
| Removed | No longer exists | N/A |
| Unchanged | No changes | Most commands |

---

## Output Format

### CLI_REFERENCE.md Structure

The reference should follow this structure:

```markdown
# CLI Reference

## Overview
- Total Commands: XXX
- Command Groups: Y
- Last Updated: [Date]

## Quick Reference

| Command | Description |
|---------|-------------|
| `vibey roadmap status` | Show roadmap overview |
| `vibey roadmap show` | Display item details |
| ... | ... |

## Command Groups

### vibey roadmap

#### vibey roadmap status
Display roadmap status and progress.

**Usage:**
\`\`\`bash
vibey roadmap status [OPTIONS]
\`\`\`

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--verbose` | Show detailed output | False |
| ... | ... | ... |

**Examples:**
\`\`\`bash
# Show current status
vibey roadmap status

# Show with details
vibey roadmap status --verbose
\`\`\`

[... continue for all commands ...]
```

---

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| Updated `CLI_REFERENCE.md` | `docs/reference/` | Complete CLI documentation |
| `CLI_CHANGES_LOG.md` | `sprint-4/outputs/` | Log of all changes made |
| `CLI_VERIFICATION_RESULTS.md` | `sprint-4/outputs/` | Test results for commands |

---

## Acceptance Criteria

- [ ] `vibey docs generate-cli` executed successfully
- [ ] CLI_REFERENCE.md updated with current command set
- [ ] All new commands since Dec 12 documented
- [ ] Changed command signatures updated
- [ ] All documented commands verified to work
- [ ] Examples tested and working
- [ ] Total command count updated (203 or current)
- [ ] Change log created listing all updates
- [ ] No broken command references

---

## Notes

- The `vibey docs generate-cli` command auto-generates most documentation
- Manual additions may be needed for complex examples
- Focus on user-facing commands (skip internal/debug commands)
- Ensure examples don't require specific data state
- Coordinate with Task 4.1 findings for known drift areas
