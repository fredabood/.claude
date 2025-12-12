# Walkthrough Template

This template defines the standard format for all Vibey walkthroughs. Walkthroughs are step-by-step tutorials that guide users through specific tasks with copy-paste ready commands and expected outputs.

---

## Template Structure

```markdown
# [Persona] Walkthrough: [Specific Goal]

> **Time Required:** X minutes
> **Difficulty:** Beginner | Intermediate | Advanced
> **Prerequisites:** [List]

## Overview

Brief description of what this walkthrough accomplishes and who it's for.

### What You'll Learn

- Learning outcome 1
- Learning outcome 2
- Learning outcome 3

### What You'll Build/Achieve

Description of the end result.

---

## Prerequisites

### Required

- [ ] Prerequisite 1
- [ ] Prerequisite 2

### Recommended

- [ ] Optional but helpful item

### Verify Prerequisites

\`\`\`bash
# Command to verify setup
vibey --version
# Expected output: Vibey Agent Framework v2.5.0
\`\`\`

---

## Step 1: [Step Title]

### Goal

What this step accomplishes.

### Instructions

1. Sub-step with explanation

   \`\`\`bash
   # Command to run
   command here
   \`\`\`

   **Expected Output:**
   \`\`\`
   Output the user should see
   \`\`\`

2. Next sub-step

### Checkpoint

> **Verify:** How to confirm this step succeeded

### Troubleshooting

<details>
<summary>Problem: [Common Issue]</summary>

**Symptom:** What the user sees

**Cause:** Why this happens

**Solution:**
\`\`\`bash
# Fix command
\`\`\`
</details>

---

## Step N: [Final Step]

[Same structure as Step 1]

---

## Summary

### What You Accomplished

- Accomplishment 1
- Accomplishment 2

### Commands Used

| Command | Purpose |
|---------|---------|
| \`command\` | Description |

### Next Steps

1. **Continue Learning:** [Link to next walkthrough]
2. **Deep Dive:** [Link to reference]
3. **Get Help:** [Link to support]

---

## Quick Reference

### All Commands

\`\`\`bash
# Copy-paste block
command 1
command 2
\`\`\`

### Related Documentation

- [CLI Reference](../reference/CLI_REFERENCE.md)
- [Journey Map](../journeys/JOURNEY_*.md)
- [User Personas](../personas/USER_PERSONAS.md)
```

---

## Required Components

| Component | Purpose | Required |
|-----------|---------|:--------:|
| Header metadata | Time, difficulty, prereqs | Yes |
| Overview | Context and outcomes | Yes |
| Prerequisites | Setup verification | Yes |
| Steps | Main content | Yes |
| Checkpoints | Verify progress | Yes |
| Troubleshooting | Handle errors | Yes |
| Summary | Recap and next steps | Yes |
| Quick Reference | Copy-paste commands | Yes |
| Related Docs | Cross-links | Yes |

---

## Conventions

### Command Blocks

```bash
# Comment explaining what this does
vibey roadmap status
```

### Expected Output Blocks

```
Vibey Roadmap Status
====================
Tracks: 3 (2 in_progress, 1 completed)
```

### Checkpoint Format

> **Verify:** Description of what to check

### Troubleshooting Format

Use collapsible details for common issues:

```html
<details>
<summary>Problem: Error message X</summary>
Solution content here
</details>
```

---

## Writing Guidelines

1. **Be Specific** - Use exact commands, not placeholders
2. **Show Output** - Include expected output for verification
3. **Explain Why** - Brief context helps understanding
4. **Handle Errors** - Include common troubleshooting
5. **Cross-Link** - Reference related documentation
6. **Test Everything** - Verify all commands work
