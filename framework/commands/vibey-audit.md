# Project Audit - Redirect to Discovery Mode

**Loaded when:** User selects Option 4 (Project Audit) or runs `/vibey audit`

---

## Redirect Notice

```markdown
# 🔍 Project Audit

**Note:** Project audit is now integrated into Discovery Mode for a better experience.

Discovery Mode offers:
- **Start with audit** - Analyze your codebase first (same as before)
- **Continue with Q&A** - Add goals and priorities after audit
- **Skip Q&A** - Go straight to sprint planning if audit is sufficient
- **Unified context** - All findings saved to PROJECT-CONTEXT.md

---

**Redirecting to Discovery Mode...**
```

```bash
# Load Discovery Mode with audit option pre-selected
# Load: .claude/commands/vibey-think.md

# Auto-select Option A (Start with project audit)
DISCOVERY_START="audit"
```

---

## Rationale for Redirect

**Why combine audit with discovery mode?**

1. **Better User Flow**
   - Audit findings naturally lead to "what do we build next?"
   - Users no longer need to run `/vibey audit` then `/vibey plan`
   - Single workflow: Audit → (Optional Q&A) → Sprint Planning

2. **Unified Context Output**
   - Both audit and brainstorming produce PROJECT-CONTEXT.md
   - No more separate audit reports vs brainstorm summaries
   - Sprint planning loads from single context source

3. **Flexibility**
   - Users can skip Q&A if audit is sufficient
   - Or refine with brainstorming if they want to add more
   - Natural progression through discovery

4. **Consistency**
   - Same command interface for all discovery workflows
   - `/vibey think` handles both new and existing projects
   - Reduced cognitive load

---

## What Happens When User Runs `/vibey audit`

**User Experience:**
```
$ /vibey audit

🔍 Project Audit

Note: Project audit is now integrated into Discovery Mode for a better experience.

Discovery Mode offers:
- Start with audit - Analyze your codebase first
- Continue with Q&A - Add goals and priorities after audit
- Skip Q&A - Go straight to sprint planning if audit is sufficient

Redirecting to Discovery Mode...

───────────────────────────────────────

# 🔍 Discovery Mode

Welcome! I'll help you understand your project and plan what to build next.

Since you asked for an audit, I'll start with that:

## Project Audit Options

A. Full Audit (Recommended)
B. Codebase Only
C. Git History Only

Which audit would you like? (A/B/C):
```

**Behind the scenes:**
- Loads `vibey-think.md`
- Sets `DISCOVERY_START="audit"`
- Skips the initial "audit or brainstorm?" question
- Goes directly to audit options

---

## For Users Who Want Direct Audit

If a user specifically wants the old audit-only behavior:

**Option 1:** Use Discovery Mode
```bash
/vibey think
# Choose: A - Start with project audit
# Choose: C - Save context for later (after audit completes)
```

**Option 2:** Run audit workflow directly (advanced)
```bash
# Direct workflow execution
# Load: .claude/workflows/planning/codebase-audit-discovery.md
```

---

**Migration complete!** `/vibey audit` now provides a better integrated experience through Discovery Mode.
