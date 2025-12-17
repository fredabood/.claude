# Architecture Concept Coverage Audit

> Audit of user-facing documentation coverage for core architectural concepts

**Date:** 2024-12-16
**Task:** Sprint 3 Task 2 (01KCMM5W5GD14X10YBJJ0VXKQJ)

---

## Executive Summary

This audit examines how well user-facing documentation explains Vibey's core architectural concepts. The finding is that **most concepts are mentioned but not explained in user context** - they appear in internal design docs and ADRs but lack user-friendly explanations.

---

## Coverage Matrix

| Concept | CLI Reference | MCP Reference | Walkthroughs | User Journeys | Architecture Overview | ADRs |
|---------|:------------:|:-------------:|:------------:|:-------------:|:--------------------:|:----:|
| **Unified Ticket Architecture** | Partial | Partial | Brief mention | Brief mention | Does Not Exist | - |
| **Track/Sprint/Task Hierarchy** | Listed | Listed | Brief | Partial | Does Not Exist | - |
| **Status Transitions** | Commands only | Tools only | Examples | Workflow | Does Not Exist | - |
| **Progress Computation** | No | No | No | No | Does Not Exist | - |
| **Requirements & Criteria** | No | No | No | No | Does Not Exist | - |
| **Artifacts & Deliverables** | Partial | Partial | No | No | Does Not Exist | - |
| **Activity Logging** | Commands | Tools | Brief | Mentioned | Does Not Exist | - |
| **Audit Trail** | Commands | No | No | No | Does Not Exist | - |
| **Dual Storage (YAML + SQLite)** | DB commands | No | No | Project Lead | Does Not Exist | **Yes** |
| **ULID Identifiers** | Used in output | Used in output | No | No | Does Not Exist | **Yes** |
| **Flat Directory Structure** | No | No | No | No | Does Not Exist | **Yes** |

**Legend:**
- Listed = Mentioned as available commands/tools
- Commands only = How to use, not why
- Partial = Some coverage but incomplete
- Brief = One-sentence mention
- Does Not Exist = No user-facing architecture overview exists

---

## Concept Analysis

### 1. Unified Ticket Architecture

**What it is:** The hierarchical structure of Tracks → Sprints → Tasks with shared properties (status, progress, dates, etc.)

**Current Coverage:**
- CLI Reference: Lists `roadmap list tracks/sprints/tasks` commands but doesn't explain relationship
- MCP Reference: Lists tools but no conceptual explanation
- Walkthroughs: WALKTHROUGH_NEW_USER.md mentions "track → sprint → task hierarchy" once
- User Journeys: Brief workflow descriptions

**Gap:** No user-friendly explanation of:
- Why this hierarchy exists
- How progress flows up the hierarchy
- How status changes propagate
- What properties are shared vs unique

**Files mentioning but not explaining:**
- docs/walkthroughs/WALKTHROUGH_NEW_USER.md:15 - brief mention
- docs/guides/ROADMAP_TUTORIAL.md:1411-1412 - brief mention

### 2. Requirements & Criteria System

**What it is:** System for defining task requirements and evaluation criteria for completables.

**Current Coverage:**
- CLI Reference: No
- MCP Reference: No
- Walkthroughs: No
- User Journeys: No

**Gap:** This is an internal system with NO user-facing documentation. Users have no way to:
- Understand what requirements are
- Know how criteria are defined
- Use the completable system

**Internal docs that exist but aren't user-facing:**
- docs/roadmap/context/sprints/unified-arch-2/CRITERIA_SCHEMA.md
- docs/roadmap/context/sprints/unified-arch-2/COMPLETABLES_SCHEMA.md

### 3. Artifacts & Deliverables

**What it is:** Tracking of work outputs associated with tasks.

**Current Coverage:**
- CLI Reference: Mentions artifact-related commands
- MCP Reference: Mentions artifact tools
- Walkthroughs: No
- User Journeys: No

**Gap:** No explanation of:
- What counts as an artifact
- How to track deliverables
- Artifact types and usage

**Internal docs:**
- docs/roadmap/context/sprints/unified-arch-2/ARTIFACTS_SCHEMA.md
- docs/roadmap/context/tracks/user-journey-audit/sprints/phase-1-6/ARTIFACT_RELATIONSHIP_MODEL.md

### 4. Activity Logging

**What it is:** System for tracking all roadmap activity (task starts, completions, etc.)

**Current Coverage:**
- CLI Reference: `vibey roadmap activity` command documented
- MCP Reference: Activity tools listed
- Walkthroughs: WALKTHROUGH_ACTIVE_DEVELOPER.md mentions checking activity
- User Journeys: JOURNEY_ACTIVE_DEVELOPER.md shows `vibey roadmap activity --limit 10`

**Gap:** No explanation of:
- What gets logged automatically
- How to use activity log for project management
- Activity log schema and structure
- Retention and querying

### 5. YAML + SQLite Dual Storage

**What it is:** System using YAML as source of truth with SQLite as query cache.

**Current Coverage:**
- CLI Reference: `vibey roadmap db` commands documented
- ADR-0003: Full technical explanation
- User Journeys: JOURNEY_PROJECT_LEAD.md mentions `vibey roadmap db rebuild`

**Gap:** No user-friendly explanation of:
- Why both formats exist
- When to use each
- How sync works
- What "source of truth" means for users
- When to rebuild database

**What exists (technical only):**
- docs/architecture/adr/0003-dual-storage-sqlite-yaml.md - excellent but too technical

---

## Gap Summary for Architecture Overview (Task 4)

The proposed `docs/architecture/ARCHITECTURE_OVERVIEW.md` should cover:

### Must Have (No Coverage)
1. **Unified Ticket Model** - Visual diagram and explanation
2. **Progress Computation** - How task completion flows to sprints to tracks
3. **Requirements/Criteria** - If exposing to users, needs explanation
4. **When to Use What** - YAML vs SQLite, CLI vs MCP

### Should Have (Partial Coverage)
1. **Status Transitions** - Currently shown only as commands, needs lifecycle view
2. **Artifacts** - Currently mentioned but not explained
3. **Activity Logging** - Purpose and value explanation

### Nice to Have (Technical Details)
1. **ULID Identifiers** - Why 26-character IDs, how generated
2. **Flat Directory** - Why files are organized this way

---

## User-Facing Documentation Locations

Documents that users are likely to access:

### Primary (should have architecture)
| Document | Purpose | Architecture Needed |
|----------|---------|---------------------|
| CLAUDE.md | Project context | Brief overview |
| README.md | Project introduction | Conceptual intro |
| docs/walkthroughs/*.md | Learning | Contextual explanations |
| docs/reference/CLI_REFERENCE.md | Command reference | Link to concepts |

### Secondary (detailed reference)
| Document | Purpose | Architecture Needed |
|----------|---------|---------------------|
| docs/architecture/ARCHITECTURE_OVERVIEW.md | **Proposed** | Full coverage |
| docs/guides/ROADMAP_TUTORIAL.md | Deep tutorial | Integrated explanations |

---

## Recommendations

### Immediate (Task 4: Architecture Overview)

Create `docs/architecture/ARCHITECTURE_OVERVIEW.md` with:

1. **Introduction section** - What is Vibey, what problems it solves
2. **Core Concepts** - Tracks, Sprints, Tasks with diagram
3. **Status and Progress** - How status flows, progress computation
4. **Dual Storage** - User-friendly explanation with examples
5. **When to Use What** - CLI vs MCP, YAML vs SQLite decision tree
6. **Links to ADRs** - For readers who want technical depth

### Follow-up (Task 12: Integrate into Walkthroughs)

Add "Why" sections to walkthroughs linking to architecture:

```markdown
> **Why?** Vibey uses a track → sprint → task hierarchy...
> See [Architecture Overview](../architecture/ARCHITECTURE_OVERVIEW.md) for details.
```

### Future (Beyond Sprint 3)

1. Add architecture diagrams (Mermaid or ASCII)
2. Create concept glossary
3. Add architecture section to CLAUDE.md

---

## Audit Methodology

### Search Terms Used
- `track.*sprint.*task`, `hierarchy`, `unified ticket`
- `requirement`, `criteria`, `completable`
- `artifact`, `deliverable`
- `activity log`, `audit trail`
- `yaml.*sqlite`, `dual storage`, `source of truth`

### Documents Examined
- All files in docs/reference/
- All files in docs/walkthroughs/
- All files in docs/journeys/
- docs/architecture/adr/*.md
- CLAUDE.md, README.md

### Coverage Criteria
- **Full**: Concept explained with user context and examples
- **Partial**: Mentioned/used without explanation
- **None**: Not present in user-facing docs
