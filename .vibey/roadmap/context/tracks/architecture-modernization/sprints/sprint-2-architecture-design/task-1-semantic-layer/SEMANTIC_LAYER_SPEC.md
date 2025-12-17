# Semantic Layer Specification

**Sprint:** Architecture Design (Sprint 2)
**Task:** Define Semantic Layer Boundaries and Responsibilities
**Date:** 2025-12-17
**Status:** Complete

---

## Executive Summary

The Vibey framework follows a three-layer architecture that separates concerns between user interfaces, domain semantics, and storage implementation. This document defines the boundaries and responsibilities of each layer based on analysis of the current codebase.

---

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      USER INTERFACE LAYER                           │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  CLI (Click) │  │  MCP Server  │  │  Unified     │               │
│  │  vibey/cli/  │  │  vibey/mcp/  │  │  vibey/      │               │
│  │              │  │              │  │  unified/    │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│                                                                     │
│  Input: User commands, AI tool calls                                │
│  Output: Formatted responses, JSON results                          │
│  Language: Human-readable / Machine-parseable                       │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SEMANTIC LAYER                                 │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Domain Models (vibey/roadmap/models/ticket/)                 │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ │   │
│  │  │ Completable│ │   Ticket   │ │Hierarchical│ │   Domain   │ │   │
│  │  │  (Layer 0) │ │  (Layer 1) │ │  (Layer 2) │ │  (Layer 3) │ │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘ │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Operations (vibey/operations/roadmap/)                       │   │
│  │  - Business rules (state transitions, validations)            │   │
│  │  - CRUD operations (create, read, update, delete)             │   │
│  │  - Query semantics (status, progress, dependencies)           │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Concepts: Tracks, Sprints, Tasks, Criteria, Artifacts              │
│  Language: Domain vocabulary (semantic terms)                       │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                                  │
│                                                                     │
│  ┌────────────────────────┐  ┌────────────────────────┐             │
│  │  YAML Files (Source)   │  │  SQLite (Query Cache)  │             │
│  │  vibey/roadmap/        │  │  vibey/roadmap/        │             │
│  │  serialization/        │  │  database/             │             │
│  │  yaml_loader.py        │  │  sql_loader.py         │             │
│  │  yaml_dumper.py        │  │  sql_dumper.py         │             │
│  └────────────────────────┘  └────────────────────────┘             │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Filesystem Abstraction (vibey/cli/roadmap_lib/filesystem.py) │   │
│  │  - Path construction                                          │   │
│  │  - File discovery                                             │   │
│  │  - Directory management                                       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Implementation: YAML files, SQLite database, file paths            │
│  Language: Technical (storage terms)                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Semantic Layer Definition

### IS Responsible For

| Category | Responsibilities | Implementation Location |
|----------|------------------|------------------------|
| **Domain Concepts** | Tracks, Sprints, Tasks, Roadmaps | `vibey/roadmap/models/` |
| **Unified Ticket Hierarchy** | Completable → Ticket → HierarchicalTicket → Domain | `vibey/roadmap/models/ticket/` |
| **Criteria System** | Completion conditions, targets, requirements | `vibey/roadmap/models/ticket/targets.py` |
| **State Transitions** | Status lifecycle (not_started → in_progress → completed) | `vibey/operations/roadmap/transitions.py` |
| **Business Rules** | Validation, constraints, invariants | `vibey/operations/roadmap/update.py` |
| **Progress Calculation** | Task counts, completion percentages | `vibey/roadmap/recalculator.py` |
| **Dependencies** | Blocking relationships, dependency ordering | `vibey/cli/roadmap_lib/dependencies.py` |
| **Activity Log** | Semantic events (task_started, sprint_completed) | `vibey/operations/roadmap/activity_log.py` |
| **Artifact Registry** | Deliverables, context files, documentation | `vibey/roadmap/models/ticket/artifact.py` |

### IS NOT Responsible For

| Category | What to Avoid | Belongs To |
|----------|---------------|------------|
| **File Organization** | Directory structure decisions | Storage Layer |
| **Storage Format** | YAML vs JSON vs SQLite choice | Storage Layer |
| **Path Construction** | `.vibey/roadmap/tasks/01KC...yaml` | Filesystem Abstraction |
| **Caching Strategy** | When to rebuild SQLite | Storage Layer |
| **File I/O** | Read/write operations | Serialization Layer |
| **ULID Generation** | ID format, time-sortable IDs | Identity Layer |
| **Command Parsing** | `--filter`, `--format` flags | Interface Layer |
| **Output Formatting** | Tables, JSON, markdown | Interface Layer |
| **Platform Deployment** | Cursor, VS Code, Claude Code configs | Adapters Layer |

---

## Responsibility Matrix

| Operation | Interface Layer | Semantic Layer | Storage Layer |
|-----------|----------------|----------------|---------------|
| `roadmap start <task-id>` | Parse args, format output | Validate transition, update status | Write YAML, sync SQLite |
| `roadmap show <id>` | Format display | Resolve references, compute progress | Read YAML/SQLite |
| `roadmap list tasks` | Handle `--filter`, display table | Query by criteria | Execute SQL query |
| `roadmap complete <id>` | Confirm action, show result | Check criteria, update status | Persist changes |
| `roadmap create-task` | Collect input, validate CLI args | Assign ULID, enforce schema | Create YAML file |

---

## Data Flow Example: `vibey roadmap start 01KCMNY4BENEZBVT9NR20PFY03`

```
1. INTERFACE LAYER (vibey/cli/commands.py)
   ├── Parse command: start
   ├── Parse args: task_id=01KCMNY4BENEZBVT9NR20PFY03
   └── Call operation: start_task(root_dir, task_id)

2. SEMANTIC LAYER (vibey/operations/roadmap/update.py)
   ├── Validate task exists
   ├── Check current status (must be not_started or blocked)
   ├── Apply transition rule: not_started → in_progress
   ├── Set started timestamp
   ├── Recalculate parent progress
   └── Log activity event

3. STORAGE LAYER (vibey/roadmap/serialization/)
   ├── Read task YAML: tasks/01KCMNY4BENEZBVT9NR20PFY03.yaml
   ├── Update fields: status, started
   ├── Write task YAML
   ├── Update SQLite: UPDATE tasks SET status='in_progress'
   └── Sync activity_log table
```

---

## Current Layer Violations

Based on Sprint 1 codebase audit, the following violations were identified:

### 1. Storage Leaks into Interface Layer

| File | Violation | Impact |
|------|-----------|--------|
| `cli/commands.py` | Constructs `.vibey/roadmap/` paths directly | Tight coupling |
| `cli/roadmap_lib/cache.py` | Contains `ROADMAP_DB_PATH` constant | Storage detail exposed |
| `mcp/tools/` | Some tools read YAML paths directly | Bypasses semantic layer |

### 2. Semantic Logic in Storage Layer

| File | Violation | Impact |
|------|-----------|--------|
| `roadmap/serialization/yaml_loader.py` | Contains business validation | Mixed concerns |
| `roadmap/database/sql_loader.py` | Implements progress calculation | Duplication with models |

### 3. Missing Abstractions

| Gap | Description | Recommendation |
|-----|-------------|----------------|
| Unified Query Interface | CLI and MCP use different query patterns | Create `QueryService` |
| Criterion Evaluation | Scattered across operations | Centralize in `CriterionService` |
| Event Bus | Activity log tightly coupled | Extract `EventBus` |

---

## Boundary Enforcement Strategies

### 1. Import Rules

```python
# ALLOWED: Interface → Semantic → Storage
from vibey.operations.roadmap import start_task  # Interface calling Semantic
from vibey.roadmap.serialization import yaml_loader  # Semantic using Storage

# FORBIDDEN: Storage → Semantic (backward dependency)
# In yaml_loader.py, should NOT import from operations/
```

### 2. Module Boundaries

```
vibey/
├── cli/                    # Interface Layer - may import from operations/
├── mcp/                    # Interface Layer - may import from operations/
├── unified/                # Interface Layer - may import from operations/
├── operations/roadmap/     # Semantic Layer - may import from roadmap/
└── roadmap/
    ├── models/             # Semantic Layer - no external imports
    ├── serialization/      # Storage Layer - may import from models/
    └── database/           # Storage Layer - may import from models/
```

### 3. Testing Boundaries

| Test Type | Mocking Strategy |
|-----------|------------------|
| Interface tests | Mock operations layer |
| Semantic tests | Mock storage layer |
| Storage tests | Use test databases/files |
| Integration tests | Real end-to-end |

---

## Alignment with Unified Ticket Architecture

The semantic layer implements the Unified Ticket Architecture (UTA):

```
Unified Ticket Architecture Mapping
===================================

UTA Concept          → Vibey Implementation
───────────────────────────────────────────
Completable          → vibey/roadmap/models/ticket/completable.py
Ticket               → vibey/roadmap/models/ticket/ticket.py
HierarchicalTicket   → vibey/roadmap/models/ticket/hierarchical.py
Criterion            → vibey/roadmap/models/ticket/targets.py
Artifact             → vibey/roadmap/models/ticket/artifact.py

Domain Models:
- RoadmapTicket      → Root completable (top-level project)
- TrackTicket        → Parent ticket (feature/initiative)
- SprintTicket       → Time-boxed child ticket
- TaskTicket         → Leaf ticket (atomic work unit)
```

---

## Success Criteria Validation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Clear IS/IS NOT definitions | ✅ Complete | Tables above |
| Diagram showing layers | ✅ Complete | ASCII diagram |
| No ambiguity about responsibilities | ✅ Complete | Responsibility matrix |
| Boundary violations documented | ✅ Complete | Violations section |

---

## References

- Sprint 1 Audit: `DEAD_CODE_AUDIT.md`, `DIRECTORY_COUPLING_AUDIT.md`
- Unified Ticket Architecture: `sqlite-backend-6/context/architecture/02-CLASS-MODEL.md`
- ADR-0003: Dual Storage (YAML + SQLite)
