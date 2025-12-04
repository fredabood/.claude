# Implementation Plan

## Sprint Roadmap

| Sprint | Name | Focus |
|--------|------|-------|
| **6** | Unified Ticket Architecture | Core model classes, layers 0b-3 |
| **7** | Artifact System Architecture | Layer 0a - first-class artifacts |
| **8** | Serialization Migration | YAML/SQL loaders/dumpers for new model |
| **9** | Operations Migration | Update all operations to use criteria |
| **10** | Interface Migration | CLI/MCP for criteria display |
| **11** | Data Validation | Computed vs declared integrity checks |
| **12** | Production Cutover | Initialize DB, dual-write, git hooks |

---

## Sprint 6 Task Execution Order

```
FOUNDATION (no dependencies)
└── Task 010: Enum Definitions
    - TicketStatus, CriterionTargetType, InheritMode
    - ThresholdComparison, TaskType, Complexity

CORE ABSTRACTIONS (depends on 010)
├── Task 009: Completable, Criterion, CriterionTarget
│   - Completable base class
│   - Criterion with blocks_transition_to
│   - All CriterionTarget types
│   - can_transition_to(), progress_for_transition()
│
└── Task 011: Requirement System
    - Requirement, CriterionTemplate
    - ApplicabilityRules, InheritMode
    - RequirementResolver

TICKET LAYERS (depends on 009, 010, 011)
├── Task 001: Layer 1 Ticket
│   - Extends Completable with work semantics
│   - start(), complete() methods
│   - Hierarchy attributes
│
├── Task 002: Layer 2 HierarchicalTicket
│   - Smart accessors
│   - Convenience accessors by criterion type
│
├── Task 003: RoadmapTicket
├── Task 004: TrackTicket
├── Task 005: SprintTicket
└── Task 006: TaskTicket

ORM & MIGRATION (depends on 001-006)
├── Task 007: SQLAlchemy ORM
│   - tickets table with single-table inheritance
│   - criteria table with polymorphic targets
│
└── Task 008: Migration Adapters
    - Convert legacy models to unified
    - Backward compatibility layer
```

---

## Implementation Sprint Mapping

| Sprint | Classes Implemented |
|--------|---------------------|
| **6** | Enums, Completable, Criterion, CriterionTarget subtypes, Ticket, HierarchicalTicket, Domain Models |
| **7** | Artifact, ArtifactProvenance, ArtifactTarget |
| **8** | YAML/SQL loaders for all models |
| **9** | Operations using criteria |
| **10** | SYMBOL_EXISTS, COMMAND_EXISTS, MCP_TOOL_EXISTS targets |
| **11** | Validation, ImpactAnalyzer |
| **12** | Production cutover, git hooks |

---

## Artifact System Migration (Sprint 7-8)

```
Sprint 6: Unified Ticket Architecture
         └── Core model: Completable, Criterion, Ticket layers
         └── Artifact design documented

Sprint 7: Artifact System Architecture
         ├── Artifact entity (Layer 0a)
         ├── ArtifactProvenance and ArtifactType enums
         ├── ArtifactTarget criterion type
         ├── artifacts table in database schema
         ├── ImpactAnalyzer for documentation staleness
         └── Layer integration (Ticket, HierarchicalTicket, Domain Models)

Sprint 8: Serialization Migration
         ├── Update yaml_loader to create Artifact entities
         ├── Convert FileExistsTarget → ArtifactTarget where appropriate
         ├── Establish documents_artifact_id relationships
         └── Add artifact registry sync (scan filesystem for pre-existing)

Sprint 10: Interface Migration
         ├── Add `vibey artifact list/show/adopt` commands
         ├── Add `vibey artifact orphans` command
         ├── Add `vibey artifact impact <files>` command
         └── MCP tools for artifact queries

Sprint 11: Data Validation
         ├── Validate artifact hashes match file contents
         ├── Validate documentation staleness is accurate
         └── Validate orphan detection works
```

---

## ULID Migration (Sprint 6, 8, 12)

| Phase | Sprint | Actions |
|-------|--------|---------|
| 1 | 6 | Add ULID generation, use existing `id_generator.py` |
| 2 | 6 | Add `parent_id`, `sequence`, `slug` to HierarchicalTicket |
| 3 | 8 | Update YAML loader to generate ULID if not present |
| 4 | 12 | Full migration: generate ULIDs, update refs, create `.id` files |

---

## Data Migration Script

**Code:** [`sample_code/models/func_migrate_task_to_unified.py`](../sample_code/models/func_migrate_task_to_unified.py)
