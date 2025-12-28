# Task 5.8: Update Stale Documentation Files - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJKTRVZS618BM5ZZTQ3443G |
| Sprint | Sprint 5: Remediation & Reporting |
| Type | documentation |
| Complexity | **medium** |
| Priority | medium |
| Estimated Tokens | 3,000 |
| Dependencies | Sprint 4 (DOCUMENTATION_DRIFT_REPORT.md) |

## Objective

Update documentation files flagged as stale in Sprint 4's documentation audit. Focus on files that are NOT auto-generated (guides, architecture docs, README sections) and require manual updates to reflect current implementation.

## Input Requirements

From Sprint 4 outputs:
1. `DOCUMENTATION_DRIFT_REPORT.md` - List of stale files with drift scores
2. Task 4.1 findings - Audit of documentation accuracy
3. Task 4.2 findings - `vibey docs check-drift` results

### What IS Auto-Generated (excluded from this task)
- `CLI_REFERENCE.md` - Use `vibey docs generate-cli`
- `MCP_REFERENCE.md` - Use `vibey docs generate-mcp`
- Database schema docs (if auto-generated)

### What Requires Manual Updates (focus of this task)
- User guides and journeys
- Architecture Decision Records (ADRs)
- Walkthroughs and tutorials
- README.md sections
- CONTRIBUTING.md
- SETUP.md
- CODING_STANDARDS.md
- CHANGELOG.md (if not auto-maintained)

## Implementation Steps

### Step 1: Load Stale File List

Review Sprint 4 findings:

```bash
# Navigate to Sprint 4 outputs
cd .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-4/outputs/

# Review drift report
cat DOCUMENTATION_DRIFT_REPORT.md
```

Expected format:
```markdown
## Stale Documents (Manual Update Required)

| File | Last Updated | Drift Score | Priority |
|------|--------------|-------------|----------|
| docs/guides/GETTING_STARTED.md | Dec 5 | High | Critical |
| docs/architecture/adr/0003-... | Nov 20 | Medium | High |
| CONTRIBUTING.md | Dec 1 | Low | Medium |
```

### Step 2: Prioritize Updates

Categorize stale files by priority:

#### Critical (Update First)
- Files referenced by CLAUDE.md
- Getting started guides
- Core architecture docs
- Files with outdated commands/examples

#### High Priority
- ADRs for recent decisions
- User journeys and walkthroughs
- Development setup docs

#### Medium Priority
- Contributing guidelines
- Changelog entries
- Style guides

#### Low Priority
- Historical docs
- Deep reference material
- Edge case documentation

### Step 3: Update Each Stale File

For each file, follow this process:

#### A. Analyze Current State
```bash
# Check last modification
git log -1 --format="%ai" -- <file-path>

# Check what's changed in related code since then
git log --oneline --since="<last-modified-date>" -- vibey/
```

#### B. Identify Outdated Sections
- Check command examples still work
- Verify file paths are correct
- Confirm statistics match reality
- Review code snippets for accuracy

#### C. Make Updates
Follow documentation standards:
- Keep same style and voice
- Update examples to current implementation
- Fix any broken links
- Update statistics/counts
- Add new sections if needed

### Step 4: Update Specific Document Types

#### User Guides (docs/guides/)

```markdown
## Common Issues to Fix

1. **Outdated Commands**
   - Before: `vibey task start <id>`
   - After: `vibey roadmap start <id>`

2. **Changed File Paths**
   - Before: `.vibey/tasks/`
   - After: `.vibey/roadmap/tasks/`

3. **New Features Not Documented**
   - Implementation mode
   - Token estimation
   - New CLI commands

4. **Statistics Drift**
   - Commands: 169 -> 203
   - MCP Tools: 76 (verify current)
   - Database Tables: 30 -> 39
```

#### Architecture Decision Records (docs/architecture/adr/)

Check for:
- Decisions that have been superseded
- New decisions needing ADRs
- Status updates (Accepted -> Deprecated)

Template for updates:
```markdown
## Status
[Previous: Accepted]
**Current: Superseded by ADR-00XX** (if applicable)

## Update Notes (Dec 2024)
- [Note about what changed]
- [Why this ADR was updated]
```

#### Walkthroughs (docs/walkthroughs/)

Verify each step:
```bash
# Test walkthrough commands
cd /tmp && mkdir test-walkthrough && cd test-walkthrough

# Follow each step and note failures
# Step 1: Initialize
vibey init  # Does this work? Correct output?

# Step 2: Create track
vibey roadmap create track ...  # Current syntax?
```

#### README.md

Sections to verify:
- Quick start commands
- Feature list
- Installation instructions
- Badge URLs/shields
- Version numbers

#### CONTRIBUTING.md

Verify:
- Branch naming conventions
- PR process
- Required checks
- Code review process

### Step 5: Verify All Commands Work

For each doc with command examples:

```bash
# Extract commands from markdown
grep -E "^vibey |^\$ vibey " <doc-file> | while read cmd; do
  echo "Testing: $cmd"
  # Execute and check for errors
  eval "$cmd" --help 2>&1 || echo "FAILED: $cmd"
done
```

### Step 6: Cross-Reference with CLAUDE.md

Ensure updates are consistent with CLAUDE.md:
- Same statistics
- Same file paths
- Same command syntax
- Same version numbers

### Step 7: Document All Changes

Create update log:

```markdown
# Documentation Update Log

## Date: December 28, 2024

### Files Updated

#### docs/guides/GETTING_STARTED.md
- **Lines Changed:** 45
- **Updates:**
  - Fixed command syntax (old -> new)
  - Updated file paths
  - Added implementation mode section
  - Updated screenshots

#### docs/architecture/adr/0003-dual-storage.md
- **Lines Changed:** 12
- **Updates:**
  - Updated table count (30 -> 39)
  - Added note about new views

[Continue for each file...]

### Verification
- [ ] All updated commands tested
- [ ] All file paths verified
- [ ] Statistics match CLAUDE.md
- [ ] No broken links
```

### Step 8: Run Final Drift Check

```bash
# Verify drift is resolved
vibey docs check-drift

# Compare with pre-update drift score
```

## Validation Checklist

- [ ] Sprint 4 stale file list reviewed
- [ ] Files prioritized by importance
- [ ] All critical files updated
- [ ] All high-priority files updated
- [ ] Commands in docs verified working
- [ ] File paths verified correct
- [ ] Statistics verified current
- [ ] No broken internal links
- [ ] Changes consistent with CLAUDE.md
- [ ] Final drift check shows improvement
- [ ] Update log created

## Deliverables

1. **Updated Documentation Files**
   - All stale files refreshed
   - Commands updated to current syntax
   - Statistics updated to current values

2. **DOCUMENTATION_UPDATE_LOG.md**
   - List of all files updated
   - Summary of changes per file
   - Before/after drift scores

3. **REMAINING_STALENESS.md** (if applicable)
   - Files intentionally not updated
   - Reason for deferral
   - Plan for future updates

## Output Location

Updated files remain in their original locations. Logs go to:
```
.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-5/outputs/
```

## File Update Templates

### For Command Updates
```markdown
<!-- Before -->
```bash
vibey task start <task-id>
```

<!-- After -->
```bash
vibey roadmap start <task-id>
```
```

### For Statistics Updates
```markdown
<!-- Before -->
| CLI Commands | 169 |

<!-- After -->
| CLI Commands | 203 |
```

### For Path Updates
```markdown
<!-- Before -->
All tasks stored in `.vibey/tasks/`

<!-- After -->
All tasks stored in `.vibey/roadmap/tasks/`
```

## Acceptance Criteria

- [ ] All critical stale documents updated
- [ ] All high-priority stale documents updated
- [ ] No command examples fail when executed
- [ ] Documentation drift score improved
- [ ] Update log is complete and accurate
- [ ] Changes are consistent across all docs

## Estimated Time

- Review stale file list: 15 minutes
- Prioritize updates: 15 minutes
- Update critical files: 60 minutes
- Update high-priority files: 45 minutes
- Update medium-priority files: 30 minutes
- Verify commands: 20 minutes
- Cross-reference CLAUDE.md: 15 minutes
- Create update log: 20 minutes
- Final drift check: 10 minutes
- **Total: ~4 hours**

## Notes

- Focus on accuracy over completeness
- Test every command example you update
- When in doubt, check the actual implementation
- Consider creating issues for major doc rewrites needed
- Some docs may need more substantial rewrites - document these for future sprints
- Coordinate with auto-generated doc updates (CLI_REFERENCE, MCP_REFERENCE)
