# Task 4.6: Update User Journeys with New Features

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJKTRVZS618BM5ZZTQ3443C |
| Sprint | 4 - Documentation Sync |
| Type | documentation |
| Complexity | medium |
| Priority | medium |
| Estimated Tokens | ~2,500 |
| Dependencies | Tasks 4.4, 4.5 (Updated CLI/MCP references) |

---

## Objective

Update persona-based user journey documentation to include new features and workflows introduced since December 12, 2024. Ensure journeys accurately represent current user experiences with Implementation Mode, token estimation, and new CLI commands.

---

## Files to Update

### Journey Documents

| File | Persona | Focus Areas |
|------|---------|-------------|
| `JOURNEY_NEW_USER.md` | New User | First-time setup, basic commands |
| `JOURNEY_ACTIVE_DEVELOPER.md` | Active Developer | Daily workflows, task management |
| `JOURNEY_PROJECT_LEAD.md` | Project Lead | Planning, tracking, reporting |
| `JOURNEY_AI_ASSISTANT.md` | AI Assistant | MCP integration, tool usage |
| `JOURNEY_CONTRIBUTOR.md` | Contributor | Code contribution, PR workflow |

### Location

```
docs/journeys/
├── JOURNEY_NEW_USER.md
├── JOURNEY_ACTIVE_DEVELOPER.md
├── JOURNEY_PROJECT_LEAD.md
├── JOURNEY_AI_ASSISTANT.md
└── JOURNEY_CONTRIBUTOR.md
```

---

## Verification Commands

### 1. List Current Journey Files

```bash
# List all journey files
ls -la docs/journeys/

# Check last modified dates
stat -f "%Sm %N" docs/journeys/*.md

# Count journey files
ls docs/journeys/*.md | wc -l
```

### 2. Check for Outdated Commands

```bash
# Extract commands from journeys
grep -h "vibey " docs/journeys/*.md | sort | uniq

# Verify each extracted command works
# (manual verification needed)
```

### 3. Identify Missing Features

```bash
# Check if Implementation Mode is documented
grep -l "implement" docs/journeys/*.md

# Check if token estimation is documented
grep -l "token" docs/journeys/*.md

# Check if context system is documented
grep -l "context" docs/journeys/*.md
```

---

## Analysis Steps

### Step 1: Review Each Journey for Accuracy

For each journey document:

1. Read through entire document
2. Test each command/example
3. Note outdated sections
4. Identify missing features

### Step 2: Identify New Features to Add

Features added since Dec 12 to include in journeys:

| Feature | Relevant Personas | Integration Point |
|---------|-------------------|-------------------|
| Implementation Mode | Active Developer, AI Assistant | Task workflow |
| Token Estimation | Project Lead, AI Assistant | Planning/tracking |
| Planned Status | All | Task lifecycle |
| Context System | AI Assistant | MCP workflow |
| New CLI Commands | All | Command examples |

### Step 3: Update Journey Documents

For each journey, update:

**JOURNEY_NEW_USER.md**
- [ ] Update getting started commands
- [ ] Add Implementation Mode overview
- [ ] Verify setup instructions current
- [ ] Check example outputs

**JOURNEY_ACTIVE_DEVELOPER.md**
- [ ] Add Implementation Mode workflow
- [ ] Update task management sections
- [ ] Include token estimation usage
- [ ] Add context system if relevant

**JOURNEY_PROJECT_LEAD.md**
- [ ] Add token tracking/reporting
- [ ] Update planning workflows
- [ ] Include Implementation Mode oversight
- [ ] Update progress tracking commands

**JOURNEY_AI_ASSISTANT.md** (if exists)
- [ ] Update MCP tool list
- [ ] Add new tool examples
- [ ] Include context system usage
- [ ] Update resource references

**JOURNEY_CONTRIBUTOR.md** (if exists)
- [ ] Verify PR workflow current
- [ ] Update testing instructions
- [ ] Check code style references

### Step 4: Verify All Examples Work

Test every command example in each journey:

```bash
# Create test environment
# Execute each command from journey
# Verify expected output matches
```

---

## Before/After Comparison Approach

### Comparison Method

Track changes to each journey:

| Journey | Section | Before | After | Change Type |
|---------|---------|--------|-------|-------------|
| NEW_USER | Setup | Old commands | Updated | Updated |
| ACTIVE_DEV | Workflow | Missing impl mode | Added | Added |
| PROJECT_LEAD | Tracking | Old reports | Token reports | Updated |

### Change Categories

| Category | Definition | Example |
|----------|------------|---------|
| Added | New section/feature | Implementation Mode section |
| Updated | Modified existing content | Updated command syntax |
| Fixed | Corrected errors | Fixed typos, wrong outputs |
| Removed | Obsolete content removed | Deprecated commands |
| Unchanged | No changes needed | N/A |

---

## Output Format

### Journey Update Template

Each journey should follow this structure:

```markdown
# [Persona] User Journey

## Overview
- **Persona:** [Name and role]
- **Goals:** [What they want to accomplish]
- **Time:** [Typical session length]
- **Last Updated:** [Date]

## Prerequisites
- [What they need before starting]

## Journey Stages

### Stage 1: [Name]
**Goal:** [Stage objective]
**Duration:** [Estimated time]

#### Steps
1. [Step 1 with command]
   \`\`\`bash
   vibey command example
   \`\`\`

2. [Step 2 with command]
   ...

#### Expected Outcome
- [What user achieves]

### Stage 2: [Name]
...

## New Features (Since Dec 2024)

### Implementation Mode
[How this persona uses Implementation Mode]

### Token Estimation
[How this persona uses token estimation]

## Common Issues
| Issue | Solution |
|-------|----------|
| ... | ... |

## Next Steps
- [Where to go from here]
```

---

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| Updated `JOURNEY_NEW_USER.md` | `docs/journeys/` | Updated new user journey |
| Updated `JOURNEY_ACTIVE_DEVELOPER.md` | `docs/journeys/` | Updated developer journey |
| Updated `JOURNEY_PROJECT_LEAD.md` | `docs/journeys/` | Updated lead journey |
| Other updated journeys | `docs/journeys/` | As applicable |
| `JOURNEY_CHANGES_LOG.md` | `sprint-4/outputs/` | Log of all changes made |

---

## Acceptance Criteria

- [ ] All journey files reviewed for accuracy
- [ ] JOURNEY_NEW_USER.md updated with current commands
- [ ] JOURNEY_ACTIVE_DEVELOPER.md includes Implementation Mode
- [ ] JOURNEY_PROJECT_LEAD.md includes token tracking features
- [ ] All command examples verified working
- [ ] New features since Dec 12 integrated appropriately
- [ ] Screenshots updated (if any exist)
- [ ] Cross-references to other docs updated
- [ ] Change log created documenting all updates
- [ ] All journeys follow consistent format

---

## Notes

- Journeys are persona-focused, not feature-focused
- Each journey should tell a coherent story
- Commands should be copy-paste ready
- Include realistic outputs where helpful
- Coordinate with walkthrough updates (Task 4.7)
- Consider whether new personas are needed
