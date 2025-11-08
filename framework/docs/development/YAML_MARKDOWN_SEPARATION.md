# YAML vs Markdown: Non-Overlapping Purposes

**Version:** 1.0
**Date:** 2025-11-07
**Status:** Design Principle

---

## The Key Insight

**YAML and Markdown serve completely different, non-overlapping purposes in the Vibey roadmap system.**

They are **not** alternatives - they are **complementary**.

---

## YAML: State Tracking

### Purpose
Track the **deterministic state** of development cycles.

### Managed By
`roadmap` CLI tool

### Contains
- Sprint status (not_started, in_progress, completed)
- Progress metrics (tasks completed, %)
- Dependencies and relationships
- Timing (started, completed dates)
- **Links to documentation** (not the content itself!)

### Example
```yaml
# .vibey/roadmap/sprints/backend-1.yaml
sprint:
  id: "backend-1"
  name: "Authentication & User Management"

  # STATE
  status: "in_progress"
  started: "2025-11-07T10:00:00Z"
  progress:
    tasks_completed: 3
    tasks_total: 8

  # RELATIONSHIPS
  dependencies:
    - type: "sprint"
      target_id: "backend-0"
      at_status: "completed"

  # LINKS (not content!)
  documentation:
    base_path: "sprint_docs/backend-1"
    files:
      plan: "plan.md"
      architecture: "architecture.md"
      progress: "progress.md"
```

### What It Answers
- "What's done?"
- "What's in progress?"
- "What's blocked?"
- "What depends on what?"
- "When was it started/completed?"

---

## Markdown: Rich Context

### Purpose
Provide **accumulated knowledge and context** for AI and humans.

### Managed By
User and AI during development (iterated, not regenerated)

### Contains
- What features to build
- Why decisions were made
- Architecture and design choices
- Daily learnings and discoveries
- Issues encountered and solutions
- Lessons learned
- **Context that accumulates over time**

### Example
```markdown
# .vibey/sprint_docs/backend-1/plan.md

# Sprint Plan: Authentication & User Management

## Goals
Build secure authentication with JWT and refresh token rotation.

## Features

### 1. User Registration
**What:** POST /api/users endpoint
**Why:** Need user accounts before authentication
**How:** Email/password with bcrypt hashing

**Updated Day 2:** Added email uniqueness check after
discovering duplicate registration bug.

### 2. Login with JWT
**What:** POST /api/auth/login
**Why:** Users need to authenticate

**Updated Day 4:** Changed to refresh token rotation
based on security review. See architecture.md for details.
```

```markdown
# .vibey/sprint_docs/backend-1/progress.md

# Daily Progress & Learnings

## Day 1 (2025-11-07)
✅ Task 1: Design schema
✅ Task 2: Implement registration

**Issue:** Forgot email validation
**Learning:** Always validate server-side

## Day 2 (2025-11-08)
🔵 Task 3: Login endpoint

**Issue:** FastAPI Depends() circular import
**Solution:** Separate auth.py module
**Learning:** Structure imports carefully

## Day 3 (2025-11-09)
...
```

### What It Answers
- "What should I build?"
- "Why did we make this decision?"
- "How should I implement this?"
- "What mistakes should I avoid?"
- "What did we learn yesterday/last sprint?"
- "What patterns should I follow?"

---

## The Relationship

### YAML Links to Markdown

```yaml
# backend-1.yaml
documentation:
  files:
    plan: "plan.md"  # ← Points to sprint_docs/backend-1/plan.md
```

**The YAML doesn't contain the plan - it points to it.**

### How They Work Together

```
1. User runs: roadmap start backend-1
   → Creates: .vibey/roadmap/sprints/backend-1.yaml (YAML state)

2. User creates: .vibey/sprint_docs/backend-1/plan.md
   → Writes: What to build, why, how (Markdown context)

3. YAML links to Markdown:
   → documentation.files.plan = "plan.md"

4. During development:
   → roadmap CLI updates YAML (status, progress)
   → User/AI updates Markdown (learnings, issues)

5. Claude reads both:
   → YAML tells Claude: "Sprint is 37% complete, 3/8 tasks done"
   → Markdown tells Claude: "Build JWT auth, avoid circular imports"
```

---

## Critical Difference: Regeneration

### YAML: Updated (Not Regenerated)

```bash
# CLI updates specific fields
roadmap start backend-1-task-003
# → Updates: backend-1.yaml status field

roadmap complete backend-1-task-003
# → Updates: backend-1.yaml progress field

# YAML is precise updates to state
```

### Markdown: Iterated (NEVER Regenerated)

```bash
# Day 1: User writes initial plan
vim .vibey/sprint_docs/backend-1/plan.md

# Day 2: User adds discovery
# "Updated Day 2: Added email uniqueness check"

# Day 5: User adds another update
# "Updated Day 5: Performance optimization needed"

# Day 10: Full history of evolution preserved
# All updates accumulated, nothing lost

# Markdown grows richer over time
```

---

## Why This Matters: Context Accumulation

### The Problem This Solves

**Sprint 1:**
```markdown
# sprint_docs/backend-1/lessons.md
Don't use simple JWT without rotation - security issue
FastAPI Depends() causes circular imports - use separate module
```

**Sprint 5:**
```markdown
# sprint_docs/backend-5/plan.md
Building new feature with authentication

# Claude reads backend-1/lessons.md
# Remembers: Use JWT rotation, avoid circular imports
# Applies learnings from 4 sprints ago!
```

**Sprint 10:**
```markdown
# All previous learnings still available
# Context compounds over time
# AI never forgets past mistakes
```

### If Markdown Were Regenerated

```
Sprint 1: Learn "Don't use approach A"
   ↓
Regenerate docs from config
   ↓
Sprint 5: Lesson lost, tries approach A again ❌

This is what we're avoiding!
```

---

## Git Strategy

### Both Committed

```bash
git add .vibey/roadmap/           # YAML state
git add .vibey/sprint_docs/       # Markdown context
git commit -m "Sprint 1 progress"

# Both are source of truth
# Both must be versioned
# Both must be preserved
```

### Why Both?

**YAML:**
- Team sees sprint status
- Dependency tracking works
- Progress visible

**Markdown:**
- Team sees why decisions made
- Future sprints learn from past
- Context preserved for onboarding

---

## Common Misconceptions

### ❌ Wrong: "Choose YAML OR Markdown"
✅ Right: "Use YAML AND Markdown for different purposes"

### ❌ Wrong: "Duplicate info in both"
✅ Right: "Non-overlapping - YAML has state, Markdown has context"

### ❌ Wrong: "Generate markdown from YAML"
✅ Right: "YAML links to markdown, doesn't generate it"

### ❌ Wrong: "Regenerate docs to keep them current"
✅ Right: "Iterate docs - add new learnings without losing old ones"

---

## Decision Matrix

| Need | Use |
|------|-----|
| Track sprint status | YAML |
| Track dependencies | YAML |
| Track progress metrics | YAML |
| Explain what to build | Markdown |
| Document why decision made | Markdown |
| Record daily learnings | Markdown |
| Preserve lessons learned | Markdown |
| Link state to context | YAML → Markdown |

---

## Real-World Example

### Sprint Planning

**User writes (Markdown):**
```markdown
# .vibey/sprint_docs/backend-1/plan.md

Build authentication with:
- User registration
- JWT login
- Refresh token rotation (for security)

Why refresh rotation: Security review found simple JWT
allows stolen tokens to be used indefinitely.
```

**CLI creates (YAML):**
```yaml
# .vibey/roadmap/sprints/backend-1.yaml
sprint:
  id: "backend-1"
  status: "not_started"
  documentation:
    files:
      plan: "plan.md"  # ← Links to markdown
```

### During Development

**CLI updates (YAML):**
```bash
roadmap start backend-1
# → status: "in_progress"

roadmap complete backend-1-task-001
# → progress.tasks_completed: 1
```

**User iterates (Markdown):**
```markdown
# .vibey/sprint_docs/backend-1/progress.md

## Day 1
Completed task 1: Database schema

Issue: Almost forgot to add email uniqueness constraint
Learning: Review schema carefully for uniqueness requirements
```

### End of Sprint

**CLI updates (YAML):**
```bash
roadmap complete backend-1
# → status: "completed"
# → completed: "2025-11-21T18:00:00Z"
```

**User captures (Markdown):**
```markdown
# .vibey/sprint_docs/backend-1/lessons.md

## What Went Well
- JWT implementation smooth
- Security review caught issues early

## What Didn't Go Well
- Underestimated token rotation complexity

## Key Learnings
1. Always do security review BEFORE implementation
2. Circular imports: use separate auth module
3. Test token expiration edge cases

## For Next Sprint
- Allocate more time for security-critical features
- Document architectural decisions as we go
```

---

## Conclusion

**YAML = State (what's done)**
**Markdown = Context (what to build, why, what we learned)**

Both are essential. Both are permanent. Both committed to git.

Neither is regenerated. Both are updated:
- YAML: Precise field updates by CLI
- Markdown: Iterative enrichment by user/AI

Together, they provide:
- Machine-readable state tracking (YAML)
- Human/AI-readable context (Markdown)
- Complete project history (both)
- Context that never gets lost (Markdown accumulation)

---

**This separation is fundamental to the Vibey roadmap system.**
