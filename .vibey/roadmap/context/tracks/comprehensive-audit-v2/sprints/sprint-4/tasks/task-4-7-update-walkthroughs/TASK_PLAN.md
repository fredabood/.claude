# Task 4.7: Update Walkthroughs with Current Workflows

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJKTRVZS618BM5ZZTQ3443D |
| Sprint | 4 - Documentation Sync |
| Type | documentation |
| Complexity | medium |
| Priority | medium |
| Estimated Tokens | ~2,500 |
| Dependencies | Tasks 4.4, 4.5, 4.6 (Updated references and journeys) |

---

## Objective

Update step-by-step walkthrough documentation to reflect current workflows. Ensure all command examples work correctly, fix outdated command syntax, and add walkthroughs for new features introduced since December 12, 2024.

---

## Files to Update

### Walkthrough Documents

| File | Focus | Target Audience |
|------|-------|-----------------|
| `WALKTHROUGH_NEW_USER.md` | First 30 minutes | Beginners |
| `WALKTHROUGH_ACTIVE_DEVELOPER.md` | Daily workflow | Regular users |
| `WALKTHROUGH_CONTRIBUTOR.md` | Contributing code | Contributors |
| `WALKTHROUGH_PROJECT_LEAD.md` | Project management | Team leads |

### Location

```
docs/walkthroughs/
├── WALKTHROUGH_NEW_USER.md
├── WALKTHROUGH_ACTIVE_DEVELOPER.md
├── WALKTHROUGH_CONTRIBUTOR.md
└── WALKTHROUGH_PROJECT_LEAD.md
```

---

## Verification Commands

### 1. List Current Walkthrough Files

```bash
# List all walkthrough files
ls -la docs/walkthroughs/

# Check last modified dates
stat -f "%Sm %N" docs/walkthroughs/*.md

# Count walkthrough files
ls docs/walkthroughs/*.md | wc -l
```

### 2. Extract and Test Commands

```bash
# Extract all vibey commands from walkthroughs
grep -h "vibey " docs/walkthroughs/*.md | sort | uniq

# Extract commands with line numbers for reference
grep -n "vibey " docs/walkthroughs/*.md

# Test specific commands
vibey roadmap status
vibey roadmap show --help
vibey deploy list
```

### 3. Check for Outdated Patterns

```bash
# Look for potentially outdated commands
grep -n "vibey task" docs/walkthroughs/*.md  # Old task commands?
grep -n "vibey sprint" docs/walkthroughs/*.md  # Old sprint commands?

# Check for deprecated flags
grep -n "\-\-old\|\-\-deprecated" docs/walkthroughs/*.md
```

### 4. Identify Missing Sections

```bash
# Check for Implementation Mode coverage
grep -l "implement" docs/walkthroughs/*.md

# Check for token estimation coverage
grep -l "token\|estimate" docs/walkthroughs/*.md

# Check for new command coverage
grep -l "context" docs/walkthroughs/*.md
```

---

## Analysis Steps

### Step 1: Test Each Walkthrough End-to-End

For each walkthrough:

1. Create a clean test environment
2. Follow steps exactly as written
3. Execute every command
4. Compare actual output to documented output
5. Note any failures or discrepancies

### Step 2: Identify Outdated Content

Categories of outdated content to find:

| Category | Example | Action |
|----------|---------|--------|
| Wrong command syntax | `vibey task create` vs `vibey roadmap create task` | Fix syntax |
| Missing options | New `--verbose` flag | Add option |
| Wrong output | Output format changed | Update example |
| Broken paths | File moved | Update path |
| Deprecated feature | Old workflow | Remove or update |

### Step 3: Update Each Walkthrough

**WALKTHROUGH_NEW_USER.md**
- [ ] Test installation steps
- [ ] Verify initial setup commands
- [ ] Update first roadmap commands
- [ ] Check expected outputs
- [ ] Add any new getting started content

**WALKTHROUGH_ACTIVE_DEVELOPER.md**
- [ ] Test daily workflow commands
- [ ] Update task management steps
- [ ] Add Implementation Mode workflow
- [ ] Update progress tracking commands
- [ ] Verify all examples work

**WALKTHROUGH_CONTRIBUTOR.md**
- [ ] Verify development setup steps
- [ ] Update testing commands
- [ ] Check PR workflow
- [ ] Update code style commands
- [ ] Verify contribution checklist

**WALKTHROUGH_PROJECT_LEAD.md** (if exists)
- [ ] Update planning workflow
- [ ] Add token estimation steps
- [ ] Update reporting commands
- [ ] Verify team management steps

### Step 4: Add New Workflow Sections

New sections to add based on Dec 12+ features:

| Feature | Walkthrough | Section Title |
|---------|-------------|---------------|
| Implementation Mode | Active Developer | "Starting an Implementation Session" |
| Token Estimation | Project Lead | "Estimating Task Complexity" |
| Planned Status | Active Developer | "Using Planned Status" |
| Context System | Active Developer | "Working with Context" |

---

## Before/After Comparison Approach

### Comparison Method

Track changes to each walkthrough:

| Walkthrough | Step | Before | After | Status |
|-------------|------|--------|-------|--------|
| NEW_USER | Step 3 | `vibey init` | `vibey roadmap init` | Fixed |
| ACTIVE_DEV | Step 5 | Missing | Added impl mode | Added |
| CONTRIBUTOR | Step 8 | Wrong test cmd | `pytest tests/` | Fixed |

### Change Categories

| Category | Definition | Action |
|----------|------------|--------|
| Fixed | Corrected broken command | Update command |
| Updated | Improved existing step | Rewrite section |
| Added | New step/section | Write new content |
| Removed | Obsolete step | Delete content |
| Reordered | Steps in wrong order | Reorganize |

---

## Output Format

### Walkthrough Structure Template

Each walkthrough should follow this structure:

```markdown
# [Title] Walkthrough

## Overview
- **Duration:** [Estimated time]
- **Skill Level:** [Beginner/Intermediate/Advanced]
- **Prerequisites:** [What user needs]
- **Last Updated:** [Date]

## What You'll Learn
- [Learning objective 1]
- [Learning objective 2]
- [Learning objective 3]

## Before You Begin
1. [Prerequisite check 1]
2. [Prerequisite check 2]

## Steps

### Step 1: [Step Title]
**Duration:** [Time estimate]

[Explanation of what this step does]

\`\`\`bash
vibey command example
\`\`\`

**Expected Output:**
\`\`\`
[Example output]
\`\`\`

**Troubleshooting:**
- If you see [error], try [solution]

### Step 2: [Step Title]
...

## Verification
How to verify you completed the walkthrough successfully:
1. [Verification step 1]
2. [Verification step 2]

## Next Steps
- [Link to related walkthrough]
- [Link to relevant documentation]

## Common Issues
| Issue | Solution |
|-------|----------|
| [Issue 1] | [Solution 1] |
| [Issue 2] | [Solution 2] |
```

---

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| Updated `WALKTHROUGH_NEW_USER.md` | `docs/walkthroughs/` | Fixed/updated new user guide |
| Updated `WALKTHROUGH_ACTIVE_DEVELOPER.md` | `docs/walkthroughs/` | Fixed/updated developer guide |
| Updated `WALKTHROUGH_CONTRIBUTOR.md` | `docs/walkthroughs/` | Fixed/updated contributor guide |
| Other updated walkthroughs | `docs/walkthroughs/` | As applicable |
| `WALKTHROUGH_CHANGES_LOG.md` | `sprint-4/outputs/` | Log of all changes made |
| `WALKTHROUGH_TEST_RESULTS.md` | `sprint-4/outputs/` | Test results for each step |

---

## Acceptance Criteria

- [ ] All walkthrough files reviewed for accuracy
- [ ] Every command in WALKTHROUGH_NEW_USER.md tested and working
- [ ] Every command in WALKTHROUGH_ACTIVE_DEVELOPER.md tested and working
- [ ] Every command in WALKTHROUGH_CONTRIBUTOR.md tested and working
- [ ] Outdated command syntax fixed
- [ ] Expected outputs updated to match current behavior
- [ ] New workflow sections added for Dec 12+ features
- [ ] Troubleshooting sections updated
- [ ] Cross-references verified and updated
- [ ] Change log created documenting all updates
- [ ] All walkthroughs follow consistent format

---

## Notes

- Walkthroughs are step-by-step, unlike journeys which are conceptual
- Every command must be copy-paste ready
- Expected outputs should match exactly (or note variability)
- Include timestamps in outputs only if they add value
- Test in clean environment to catch dependency issues
- Coordinate with journey updates (Task 4.6) for consistency
- Consider recording terminal sessions for complex workflows
