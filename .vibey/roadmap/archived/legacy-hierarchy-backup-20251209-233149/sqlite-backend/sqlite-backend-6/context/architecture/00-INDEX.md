# Unified Ticket Architecture

**Sprint:** sqlite-backend-6
**Status:** AUTHORITATIVE
**Version:** 4.0
**Last Updated:** 2025-12-04

---

## Executive Summary

The Unified Ticket Architecture treats **everything that can be completed** as a `Completable` with **criteria**. The key innovation is the `blocks_transition_to` field on `Criterion`, which unifies:

- **Dependencies** → blocks `IN_PROGRESS`
- **Success criteria** → blocks `COMPLETED`
- **Production gates** → blocks `PRODUCTION_READY`

This **ELIMINATES the separate Dependency class** and creates a single deterministic interface for all state transitions.

### Core Principle

> Completion is computed, not declared. The AI cannot mark a ticket complete unless all criteria are satisfied.

---

## Document Structure

| Document | Description |
|----------|-------------|
| [01-DESIGN-PRINCIPLES.md](01-DESIGN-PRINCIPLES.md) | Core philosophy, unified blocking model, what gets eliminated |
| [02-CLASS-MODEL.md](02-CLASS-MODEL.md) | Complete class hierarchy with layer diagram and relationships |
| [03-ARTIFACT-SYSTEM.md](03-ARTIFACT-SYSTEM.md) | First-class artifacts with provenance and impact analysis |
| [04-IDENTITY-SYSTEM.md](04-IDENTITY-SYSTEM.md) | ULID-based identity decoupled from ordering |
| [05-DATABASE-SCHEMA.md](05-DATABASE-SCHEMA.md) | SQLite tables, views, and entity mapping |
| [06-SERIALIZATION.md](06-SERIALIZATION.md) | YAML format and migration strategy |
| [07-IMPLEMENTATION-PLAN.md](07-IMPLEMENTATION-PLAN.md) | Sprint roadmap and task execution order |
| [08-REFERENCE.md](08-REFERENCE.md) | Enums, status progression, benefits, gap analysis |
| [09-DESIGN-DECISIONS.md](09-DESIGN-DECISIONS.md) | Design phase outputs (directory structure, file format, context) |

---

## Code Samples

All code samples are extracted to [`../sample_code/`](../sample_code/):

| Directory | Contents | Count |
|-----------|----------|-------|
| `models/` | Python class definitions | 76 files |
| `sql/` | Database schema and views | 6 files |
| `yaml/` | YAML format examples | 12 files |

---

## Quick Reference

### Layer Architecture

```
Layer 3: Semantic Layer (PLUGGABLE)
         │
         ├─ Vibey (default):   RoadmapTicket → TrackTicket → SprintTicket → TaskTicket
         └─ Jira (override):   JiraProject → JiraEpic/Sprint → JiraIssue → JiraSubtask
                               (+ GitHub, Linear, others future)
         │
         ▼
Layer 2: HierarchicalTicket → parent_id, sequence, slug, smart accessors
Layer 1: Ticket             → lifecycle (started_at, completed_at), commits, assignments
Layer 0: Completable        → id, name, status, criteria, can_transition_to()
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
              Ticket Branch                      Artifact Branch
            (work items with                   (file entities with
             lifecycle semantics)               verification semantics)
```

### Key Classes

| Class | Purpose |
|-------|---------|
| `Completable` | Base for anything with criteria (Tickets AND Artifacts) |
| `Criterion` | Single blocking condition with `blocks_transition_to` |
| `CriterionTarget` | Polymorphic target (Completable, File, Test, Threshold, Manual, External) |
| `Ticket` | Work item extending Completable with lifecycle |
| `HierarchicalTicket` | Adds parent-child navigation |
| `Artifact` | File entity extending Completable with implicit FileExistsTarget |
| `SemanticLayer` | Abstract interface for pluggable domain models (Layer 3) |
| `SemanticLayerRegistry` | Registry for semantic layers with default selection |

### Unified CompletableTarget

`CompletableTarget` references both Tickets and Artifacts uniformly (no separate ArtifactTarget).

### Key Methods

| Method | Purpose |
|--------|---------|
| `can_transition_to(status)` | Returns `(bool, List[str])` - can transition + blocking reasons |
| `progress_for_transition(status)` | Returns `Progress` toward specific status |
| `start()` / `complete()` | Lifecycle transitions with validation |

---

## Superseded Documents

This architecture consolidates and supersedes:
- `COMPLETABLE_UNIFICATION.md`
- `COMPREHENSIVE_IMPACT_ASSESSMENT.md`
- `DEPENDENCY_SYSTEM_ANALYSIS.md`
- `IMPACT_ANALYSIS.md`
- `REVISED_ARCHITECTURE.md`
- `YAML_MIGRATION_GAP_ANALYSIS.md`
- `CLASS_ARCHITECTURE.md`

---

**Document Version:** 4.0
**Author:** Claude Code
