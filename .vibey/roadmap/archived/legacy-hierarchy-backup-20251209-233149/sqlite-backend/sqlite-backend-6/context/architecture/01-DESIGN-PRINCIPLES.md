# Design Principles

## Design Intent

> The purpose of the system is to put guardrails around the AI's ability to manipulate the roadmap state by implementing a **deterministic interface for calculating whether or not a ticket has been completed**.

This means:
1. **Completion is computed, not declared** - AI cannot mark a ticket complete unless all criteria are satisfied
2. **User controls the criteria** - User defines what "complete" means for each ticket
3. **Single unified interface** - `can_transition_to(status)` is THE check for all state changes

---

## The Unified Blocking Model

**ALL blocking relationships use `Criterion` with `blocks_transition_to`:**

| blocks_transition_to | Meaning | Example |
|---------------------|---------|---------|
| `IN_PROGRESS` | Must be met before starting | Sibling dependency, external blocker |
| `COMPLETED` | Must be met before completing | Success criteria, child completion, tests |
| `PRODUCTION_READY` | Must be met before deploying | Production gates, security reviews |

---

## What This Eliminates

The unified blocking model consolidates multiple legacy concepts:

| Legacy Concept | Unified Replacement |
|----------------|---------------------|
| `Dependency` class | `Criterion` with `blocks_transition_to: IN_PROGRESS` |
| `blocked_by` field | Computed from criteria |
| `depends_on` field | Criteria with `CompletableTarget` |
| `development_gates` | Criteria with `blocks_transition_to: IN_PROGRESS` |
| `quality_gates` | Criteria with `ThresholdTarget` |
| `success_criteria` (separate) | Criteria with `blocks_transition_to: COMPLETED` |

---

## Simplification Summary

| Metric | Before | After |
|--------|--------|-------|
| Concepts for completion | 4 (children, deliverables, criteria, gates) | 1 (criteria) |
| Progress formulas | 3 (per type) | 1 (universal) |
| Parent-child models | Explicit fields | Computed from criteria |
| Completion checks | Multiple functions | One function: `can_transition_to()` |
| Dependency classes | `Dependency`, `DependencyStatus`, `*Blocker` | Criterion with `blocks_transition_to` |

---

## Protection Guarantees

| Protection | Before | After |
|------------|--------|-------|
| AI completion bypass | Multiple scattered checks | Single deterministic check |
| Visibility of blockers | Multiple sources | `can_transition_to()` returns reasons |
| Audit trail | Partial | Every criterion has state |
| Progress tracking | Different per entity type | Same formula everywhere |

---

## Key Design Principle

**SQLite is derived state; Git is source of truth.**

The entire SQLite database must be rebuildable from the git repo via `db rebuild`.
