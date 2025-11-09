# YAML vs Markdown: Design Principle

**Document Version:** 1.0
**Created:** 2025-11-09
**Sprint:** core-framework-2
**Status:** Active Design Document

---

## Core Question

**Why does Vibey use both YAML and Markdown for sprint/task information?**

**Short Answer:** Because you need both **deterministic state** (YAML) AND **rich context** (Markdown).

---

## The Problem

### What Went Wrong: YAML-Only Approach

**Attempt:** Store everything in YAML

```yaml
sprint:
  id: core-framework-2
  name: Config-to-Docs Architecture
  status: in_progress
  tasks:
    - id: task-001
      title: Design .vibey/ structure
      status: completed
      description: "Design the directory structure..."  # ← Limited
      notes: "We considered X but chose Y because..."   # ← Awkward in YAML
      code_examples: |                                   # ← Ugly in YAML
        ```python
        def example():
            pass
        ```
```

**Problems:**
- ❌ **Awkward Formatting:** Code examples, diagrams, long explanations don't fit YAML
- ❌ **No Rich Formatting:** Can't use Markdown features (headers, lists, code blocks)
- ❌ **Hard to Read:** YAML becomes huge and unreadable
- ❌ **Poor AI Context:** AI assistants struggle with YAML-embedded narrative
- ❌ **Manual Editing:** Humans hate editing long YAML

###

 What Went Wrong: Markdown-Only Approach

**Attempt:** Store everything in Markdown

```markdown
# Sprint: Config-to-Docs Architecture

**Status:** In Progress
**Completed:** 3/13 tasks

## Tasks

### Task 1: Design .vibey/ structure
**Status:** Completed
**Dependencies:** None

[Long description with examples, diagrams, etc...]

### Task 2: Implement config system
**Status:** In Progress
**Dependencies:** Task 1

[Long description...]
```

**Problems:**
- ❌ **Not Queryable:** Can't easily answer "What tasks are blocked?"
- ❌ **No CLI Integration:** Can't programmatically update status
- ❌ **Inconsistent Format:** Every file formats differently
- ❌ **Dependency Tracking:** Hard to maintain dependency graph
- ❌ **Progress Calculation:** Manual counting of completed tasks

---

## The Solution: Dual System

**Use YAML for STATE, Markdown for CONTEXT**

### YAML: Deterministic State

**Purpose:** Machine-readable state that can be queried and updated

**What Goes in YAML:**
```yaml
sprint:
  id: core-framework-2
  name: Config-to-Docs Architecture
  status: in_progress              # ← State
  progress:
    tasks_total: 13                 # ← State
    tasks_completed: 3              # ← State
    completion_percent: 23          # ← State
  tasks:
    - id: task-001
      status: completed             # ← State
      started: '2025-11-09T00:00:00'  # ← State
      completed: '2025-11-09T08:00:00'  # ← State
    - id: task-002
      status: in_progress           # ← State
      dependencies:                  # ← State
        - task-001
  depends_on:                       # ← State
    - blocker_id: core-framework-3
      required_status: production_ready
  documentation:                    # ← Link to Markdown
    files:
      plan: .vibey/sprint_docs/core-framework/core-framework-2/plan.md
```

**Characteristics:**
- ✅ **Queryable:** `roadmap query --sprint core-framework-2`
- ✅ **Updatable:** `roadmap update --complete-task task-001`
- ✅ **Structured:** Consistent schema across all sprints
- ✅ **Dependencies:** First-class support for blockers, dependencies
- ✅ **Progress Tracking:** Automatic calculation

### Markdown: Rich Context

**Purpose:** Human and AI-readable narrative, decisions, examples

**What Goes in Markdown:**
```markdown
# Sprint Plan: Config-to-Docs Architecture

## Sprint Goal

Establish the permanent `.vibey/` directory as the platform-agnostic core...

## Background

### Current State (Problems)

**1. Platform Lock-in:**
- Framework tightly coupled to Claude Code
- No clear separation between core and deployment

[Rich explanations, diagrams, code examples...]

## Tasks

### Task 1: Design .vibey/ directory structure

**Why This Matters:**
We need a platform-agnostic home for configuration...

**Design Decisions:**
- Chose `.vibey/` over `.vibey-config/` because...
- Separated `config/` and `roadmap/` because...

**Architecture:**
```
.vibey/
├── config/
│   ├── project.yaml
...
```

**Key Insights:**
During implementation, we discovered that...

[Long narrative context that would be awful in YAML]
```

**Characteristics:**
- ✅ **Rich Formatting:** Headers, code blocks, diagrams, tables
- ✅ **Human-Readable:** Natural language explanations
- ✅ **AI-Friendly:** LLMs excel at processing Markdown
- ✅ **Evolving:** Iterated during sprint (living document)
- ✅ **Preserved:** Never regenerated, accumulated knowledge

---

## How They Work Together

### 1. YAML References Markdown

**Sprint YAML:**
```yaml
sprint:
  id: core-framework-2
  documentation:
    files:
      plan: .vibey/sprint_docs/core-framework/core-framework-2/plan.md
      architecture: .vibey/sprint_docs/core-framework/core-framework-2/architecture.md
      learnings: .vibey/sprint_docs/core-framework/core-framework-2/learnings.md
```

**Agent Workflow:**
1. Query YAML: "What is the sprint status?"
   ```bash
   roadmap query --sprint core-framework-2
   # → status: in_progress, 3/13 tasks completed
   ```

2. Load Markdown: "What should I build?"
   ```bash
   cat .vibey/sprint_docs/core-framework/core-framework-2/plan.md
   # → [Complete sprint plan with architecture, examples, etc.]
   ```

### 2. CLI Updates YAML, Humans Edit Markdown

**Machine Updates (YAML):**
```bash
# Start a task
roadmap update --start-task core-framework-2-task-002
# → Updates .vibey/sprints/core-framework-2.yaml

# Complete a task
roadmap update --complete-task core-framework-2-task-002
# → Updates YAML with completion timestamp, recalculates progress
```

**Human Updates (Markdown):**
```bash
# Developer adds learnings during sprint
vim .vibey/sprint_docs/core-framework/core-framework-2/learnings.md
```

```markdown
# Learnings: Config-to-Docs Architecture

## Week 1: Foundation

### What Worked
- YAML schema validation caught 5 config errors early
- Template rendering was faster than expected

### What Didn't Work
- Initial context loader design was too complex
- Needed to simplify distance calculation

### Key Insight
The adapter pattern is more powerful than we thought...
```

### 3. Both Committed to Git

**Why Both?**
- **YAML:** Current state, dependencies, progress
- **Markdown:** Why decisions were made, what we learned

**Example:**
```
commit abc123 "Complete Task 1: Design .vibey/ structure"

Modified:
  .vibey/sprints/core-framework-2.yaml     ← YAML updated (task status)
  .vibey/sprint_docs/.../architecture.md   ← Markdown updated (design decisions)
```

**Value:**
- ✅ **Git history shows WHAT changed** (YAML diff)
- ✅ **Git history shows WHY it changed** (Markdown diff)

---

## Real-World Examples

### Example 1: Starting a Sprint

**YAML Update (Automated):**
```bash
roadmap update --start-sprint core-framework-2
```

```yaml
# .vibey/sprints/core-framework-2.yaml
sprint:
  status: in_progress  # ← Changed from not_started
  started: '2025-11-09T00:00:00'  # ← Timestamp added
```

**Markdown Creation (Manual):**
```bash
cp docs/sprints/core-framework-2-plan.md \
   .vibey/sprint_docs/core-framework/core-framework-2/plan.md
```

```markdown
# Sprint Plan: Config-to-Docs Architecture

[Rich sprint plan with architecture, examples, etc.]
```

### Example 2: Completing a Task

**YAML Update (Automated):**
```bash
roadmap update --complete-task core-framework-2-task-001
```

```yaml
# .vibey/sprints/core-framework-2.yaml
tasks:
  - id: task-001
    status: completed  # ← Changed from in_progress
    completed: '2025-11-09T08:00:00'  # ← Timestamp added

progress:
  tasks_completed: 1  # ← Incremented
  completion_percent: 8  # ← Recalculated (1/13 * 100)
```

**Markdown Update (Manual):**
```markdown
# Architecture Decisions

## Task 1: .vibey/ Directory Structure

### Decision: Use `.vibey/` Not `.vibey-config/`

**Rationale:**
- Shorter, cleaner
- Matches `.git/`, `.github/` convention
- No ambiguity (obviously Vibey-related)

**Alternatives Considered:**
- `.vibey-config/` ← Too verbose
- `.vby/` ← Too cryptic
- `vibey/` ← No dot prefix (not hidden)

**Final Choice:** `.vibey/`
```

### Example 3: Dependency Query

**YAML Query:**
```bash
roadmap query --task core-framework-1-task-001 --show-blockers
```

**Output:**
```yaml
task:
  id: core-framework-1-task-001
  title: Auto-generate CLAUDE.md from configs
  status: not_started
  blocked_by:
    - dependency_id: core-framework-2
      dependency_type: sprint
      current_status: in_progress
      required_status: completed
      blocking_since: '2025-11-09T00:00:00'
```

**Markdown Context (Load Automatically):**
```bash
# Framework loads blocking sprint's plan
cat .vibey/sprint_docs/core-framework/core-framework-2/plan.md

# Agent sees: "Sprint 2 builds the config system that Sprint 1 needs..."
```

### Example 4: Sprint Retrospective

**YAML (State at End):**
```yaml
# .vibey/sprints/core-framework-2.yaml
sprint:
  status: completed
  started: '2025-11-09T00:00:00'
  completed: '2025-12-07T00:00:00'
  progress:
    tasks_total: 13
    tasks_completed: 13
    completion_percent: 100
  metadata:
    actual_duration: 28 days  # ← Calculated from dates
```

**Markdown (Retrospective):**
```markdown
# Retrospective: Config-to-Docs Architecture

## What Went Well

1. **YAML/Markdown Separation:** This design worked perfectly!
2. **Adapter Pattern:** More flexible than expected
3. **Context Loading:** Achieved 85% reduction (target was 80-90%)

## What Could Be Better

1. **Task Estimation:** Task 3 took 20h instead of 16h
2. **Testing:** Should have written tests earlier
3. **Migration Script:** More edge cases than anticipated

## Key Learnings

### The Power of Separation of Concerns

Having YAML for state and Markdown for context was transformative...

[Long narrative retrospective that would be awful in YAML]
```

---

## Design Principles

### 1. YAML is the Single Source of Truth for STATE

**State Includes:**
- Sprint/task status (not_started, in_progress, completed)
- Timestamps (started, completed)
- Dependencies (blocks, blocked_by, depends_on)
- Progress (completion %, tasks done/total)
- Assignments (agents, owners)

**Why YAML:**
- ✅ Machine-readable
- ✅ Schema-validated
- ✅ Queryable
- ✅ Updatable by CLI
- ✅ Consistent structure

### 2. Markdown is the Single Source of Truth for CONTEXT

**Context Includes:**
- Why (rationale for decisions)
- How (implementation approaches, architectures)
- What (examples, code snippets, diagrams)
- Learnings (what worked, what didn't)
- Historical (evolution of thinking)

**Why Markdown:**
- ✅ Human-readable
- ✅ Rich formatting
- ✅ AI-friendly
- ✅ Iterative (living document)
- ✅ Git-friendly diffs

### 3. They NEVER Overlap

**Bad:** Duplicating information

```yaml
# ❌ DON'T DO THIS
task:
  description: "Design the .vibey/ directory structure with config/, roadmap/, sprint_docs/, summaries/, and templates/ subdirectories. The config/ directory will contain project.yaml, framework.yaml, agents/, workflows/, and quality-gates.yaml..."
  # ← This belongs in Markdown, not YAML
```

```markdown
<!-- ❌ DON'T DO THIS -->
## Task 1: Design .vibey/ structure

**Status:** completed
**Started:** 2025-11-09T00:00:00
**Completed:** 2025-11-09T08:00:00
<!-- ← This belongs in YAML, not Markdown -->
```

**Good:** Clear separation

```yaml
# ✅ YAML: State only
task:
  id: task-001
  title: Design .vibey/ directory structure  # ← Short title only
  status: completed
  started: '2025-11-09T00:00:00'
  completed: '2025-11-09T08:00:00'
  documentation: .vibey/sprint_docs/.../plan.md  # ← Link to context
```

```markdown
<!-- ✅ Markdown: Rich context only -->
# Task 1: Design .vibey/ Directory Structure

## Goal
Create a platform-agnostic directory structure...

## Architecture
[Diagrams, code examples, rationale, etc.]
```

### 4. YAML Links to Markdown

**Always Include Documentation Links:**
```yaml
sprint:
  id: core-framework-2
  documentation:
    files:
      plan: .vibey/sprint_docs/core-framework/core-framework-2/plan.md
      architecture: .vibey/sprint_docs/core-framework/core-framework-2/architecture.md
      learnings: .vibey/sprint_docs/core-framework/core-framework-2/learnings.md
      retrospective: .vibey/sprint_docs/core-framework/core-framework-2/retrospective.md

task:
  id: task-001
  documentation: .vibey/sprint_docs/core-framework/core-framework-2/plan.md#task-1
```

**Why:**
- ✅ Agents can load both state and context
- ✅ Humans know where to find details
- ✅ Links are version-controlled
- ✅ Context never lost

### 5. Markdown is NEVER Regenerated

**Critical Rule:** Once created, Markdown is edited, NOT regenerated

**Why:**
```markdown
# Initial Plan (Sprint Start)
## Task 1: Design .vibey/ structure
[Initial thoughts...]

# ← DURING SPRINT, DEVELOPER ADDS:
## Design Evolution
Initially we planned X, but discovered Y, so we pivoted to Z.

## Implementation Notes
The adapter pattern turned out to be...

# ← AT END OF SPRINT:
## What We Learned
This design worked because...
```

**If Regenerated:** All those learnings are LOST! ❌

**With Iteration:** Knowledge accumulates, context preserved ✅

---

## When to Use Which

### Use YAML When...

✅ **You need to query programmatically:**
- "What sprints are blocked?"
- "How many tasks are completed?"
- "What dependencies does this task have?"

✅ **You need to update via CLI:**
- Start/complete tasks
- Update progress
- Assign agents

✅ **You need consistent structure:**
- All sprints have same fields
- Schema validation
- Automated processing

### Use Markdown When...

✅ **You need rich formatting:**
- Code examples
- Diagrams
- Tables
- Long explanations

✅ **You need to explain WHY:**
- Design decisions
- Trade-offs
- Rationale

✅ **You need to preserve learnings:**
- What worked/didn't work
- Evolution of thinking
- Historical context

✅ **You need AI-friendly context:**
- LLMs process Markdown naturally
- Rich semantic structure

---

## Migration from Markdown-Only

### Current State (Vibey Framework)

**Existing Files:**
```
docs/sprints/
├── core-framework-2-plan.md         ← Rich Markdown (good!)
├── roadmap-integration-1-plan.md    ← Rich Markdown (good!)
└── ...
```

**Problem:** No YAML state, hard to query

### Target State

**New Structure:**
```
.vibey/
├── sprints/
│   ├── core-framework-2.yaml        ← YAML state (NEW)
│   ├── roadmap-integration-1.yaml   ← YAML state (NEW)
│   └── ...
└── sprint_docs/
    ├── core-framework/
    │   └── core-framework-2/
    │       └── plan.md                ← Markdown context (MOVED)
    └── roadmap-integration/
        └── roadmap-integration-1/
            └── plan.md                ← Markdown context (MOVED)
```

### Migration Steps

**1. Extract State from Markdown → YAML**

Parse existing Markdown:
```markdown
# Sprint Plan: Config-to-Docs Architecture

**Sprint ID:** core-framework-2
**Duration:** 4 weeks
**Priority:** Critical
**Status:** Not Started

## Tasks

### Task 1: Design .vibey/ structure
**Priority:** Critical
**Estimated:** 8 hours
**Dependencies:** None
```

Generate YAML:
```yaml
sprint:
  id: core-framework-2
  name: Config-to-Docs Architecture
  estimated_duration: 4 weeks
  priority: critical
  status: not_started
  tasks:
    - id: task-001
      title: Design .vibey/ structure
      priority: critical
      estimated_hours: 8
      dependencies: []
```

**2. Move Markdown (Preserve Content!)**

```bash
mkdir -p .vibey/sprint_docs/core-framework/core-framework-2/
cp docs/sprints/core-framework-2-plan.md \
   .vibey/sprint_docs/core-framework/core-framework-2/plan.md
```

**3. Link YAML → Markdown**

```yaml
sprint:
  id: core-framework-2
  documentation:
    files:
      plan: .vibey/sprint_docs/core-framework/core-framework-2/plan.md
```

**4. Keep Old Files (Temporarily)**

Don't delete `docs/sprints/` immediately. Migration script can validate equivalence.

---

## Best Practices

### 1. Keep YAML Concise

**❌ Bad:**
```yaml
task:
  description: |
    This task involves designing the .vibey/ directory structure.
    We need to consider platform-agnostic design, separation of
    concerns, and ensure that config/, roadmap/, sprint_docs/,
    summaries/, and templates/ are all properly organized...
    [500 more words]
```

**✅ Good:**
```yaml
task:
  title: Design .vibey/ directory structure  # ← Short and clear
  documentation: .vibey/sprint_docs/.../plan.md  # ← Link to details
```

### 2. Make Markdown Scannable

**✅ Good Structure:**
```markdown
# Task 1: Design .vibey/ Directory Structure

## TL;DR
Create platform-agnostic directory structure with clear separation.

## Goal
[2-3 sentences]

## Approach
- Step 1
- Step 2
- Step 3

## Detailed Design
[Long explanation]

## Examples
[Code, diagrams]

## Decisions
[Rationale]
```

### 3. Update Both Together

**When completing a task:**
```bash
# 1. Update YAML (automated)
roadmap update --complete-task task-001

# 2. Update Markdown (manual)
vim .vibey/sprint_docs/.../learnings.md
# Add: "Task 1 taught us that..."
```

### 4. Use Templates for Consistency

**Sprint Docs Template:**
```markdown
# Sprint Plan: {sprint_name}

## Sprint Goal
[What we're trying to achieve]

## Background
[Why this matters]

## Tasks
[One section per task]

## Success Criteria
[How we know we're done]
```

**Learnings Template:**
```markdown
# Learnings: {sprint_name}

## Week 1
### What Worked
### What Didn't Work
### Key Insights

## Week 2
[Same structure]
```

---

## Summary

**Why Dual System?**
- YAML: Machine-readable state (queryable, updatable)
- Markdown: Human-readable context (rich, narrative)

**Key Rules:**
1. ✅ YAML for state, Markdown for context
2. ✅ Never overlap (clear separation)
3. ✅ YAML links to Markdown
4. ✅ Markdown never regenerated (accumulated knowledge)
5. ✅ Both committed to git

**Benefits:**
- ✅ Best of both worlds
- ✅ Queryable dependencies
- ✅ Rich context preservation
- ✅ CLI automation
- ✅ Human-friendly editing
- ✅ AI-friendly processing

---

**Document Status:** ✅ Active Design Document
**Last Updated:** 2025-11-09
**Next Review:** After Task 1 completion
