# CLI Entry Point vs Unified Ticket Architecture Analysis

**Sprint:** Architecture Design (Sprint 2)
**Task:** Analyze CLI Entry Point vs Unified Ticket Architecture Layers
**Date:** 2025-12-17
**Status:** Complete

---

## Executive Summary

This document maps the current CLI commands to the Unified Ticket Architecture (UTA) and identifies gaps where the CLI structure diverges from the semantic model. The analysis reveals that while the CLI is comprehensive, it uses domain-specific terminology (`track`, `sprint`, `task`) rather than the unified `ticket` abstraction, creating an alignment opportunity.

---

## Unified Ticket Architecture Layers

### Architecture Model

```
┌─────────────────────────────────────────────────────────────────────┐
│                    UNIFIED TICKET ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  TICKETS (Work Units)                                               │
│  ├── Completable (anything with criteria)                           │
│  │   └── Layer 0: Has completion criteria                           │
│  │                                                                  │
│  ├── Ticket (work item with lifecycle)                              │
│  │   └── Layer 1: Adds status, progress, timestamps                 │
│  │                                                                  │
│  ├── HierarchicalTicket (parent-child navigation)                   │
│  │   └── Layer 2: Adds parent/child relationships                   │
│  │                                                                  │
│  └── Domain Tickets (specialized types)                             │
│      └── Layer 3: RoadmapTicket, TrackTicket, SprintTicket, TaskTicket │
│                                                                     │
│  CRITERIA (Completion Conditions)                                   │
│  ├── FileExistsTarget     - File must exist                         │
│  ├── TestPassesTarget     - Tests must pass                         │
│  ├── TestCoverageTarget   - Coverage threshold met                  │
│  ├── ManualTarget         - Manual approval required                │
│  └── CompletableTarget    - Child completable must complete         │
│                                                                     │
│  ARTIFACTS (Deliverables & Evidence)                                │
│  ├── ContextArtifact      - Planning/design documents               │
│  ├── DocumentationArtifact - User-facing docs                       │
│  └── CodeArtifact         - Source code references                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Domain Ticket Mapping

| UTA Concept | Domain Model | CLI Term | Description |
|-------------|--------------|----------|-------------|
| Root Completable | RoadmapTicket | `roadmap` | Top-level project container |
| Parent Ticket | TrackTicket | `track` | Feature area or work stream |
| Time-boxed Ticket | SprintTicket | `sprint` | Iteration milestone |
| Leaf Ticket | TaskTicket | `task` | Atomic work unit |

---

## Current CLI Command Inventory

### Command Groups (13 total)

| Group | Commands | UTA Alignment | Notes |
|-------|----------|---------------|-------|
| `roadmap` | 57 | Partial | Mixed ticket types |
| `artifact` | 5 | Good | Maps to Artifact concept |
| `audit` | 3 | N/A | Meta/tooling |
| `auth` | 4 | N/A | Security |
| `config` | 5 | N/A | Configuration |
| `content` | 4 | Good | Maps to content artifacts |
| `context` | 6 | Good | Session context |
| `deploy` | 5 | N/A | Deployment |
| `discover` | 3 | N/A | Analysis |
| `docs` | 7 | Partial | Documentation artifacts |
| `git` | 4 | Partial | Commit linkage |
| `parity` | 2 | Good | Enforcement |
| `session` | 4 | Good | Session management |
| `validate` | 3 | Good | Validation |

### Roadmap Commands Analysis

#### Lifecycle Commands (Ticket Operations)

| Command | Target | UTA Equivalent | Gap |
|---------|--------|----------------|-----|
| `start` | sprint, task | `ticket start` | Could unify |
| `complete` | track, sprint, task | `ticket complete` | Could unify |
| `revert` | track, sprint, task | `ticket revert` | Could unify |
| `show` | track, sprint, task | `ticket show` | Could unify |
| `status` | all | `ticket status` | Could unify |
| `list` | (missing) | `ticket list` | **Gap** |

#### Creation Commands

| Command | Creates | UTA Equivalent | Gap |
|---------|---------|----------------|-----|
| `create-track` | TrackTicket | `ticket create --type track` | Different pattern |
| `create-sprint` | SprintTicket | `ticket create --type sprint` | Different pattern |
| `create-task` | TaskTicket | `ticket create --type task` | Different pattern |
| `create-from-plan` | Multiple | (complex) | Special case |

#### Query Commands

| Command | Function | UTA Equivalent | Gap |
|---------|----------|----------------|-----|
| `status` | Overview | `ticket status` | Aligned |
| `show` | Details | `ticket show` | Aligned |
| `activity` | History | `ticket activity` | Aligned |
| `context` | AI context | `ticket context` | Aligned |

#### Criteria Commands (Missing from CLI)

| UTA Concept | CLI Command | Status |
|-------------|-------------|--------|
| Add criterion | `criteria add` | **Missing** |
| List criteria | `criteria list` | **Missing** |
| Check criterion | `criteria check` | **Missing** |
| Override criterion | (partial) | Via `override-standard` |

#### Artifact Commands (Existing)

| Command | Function | UTA Alignment |
|---------|----------|---------------|
| `artifact create` | Create artifact | Good |
| `artifact list` | List artifacts | Good |
| `artifact link` | Link to ticket | Good |
| `add-context` | Add context file | Good (via artifact) |
| `link-doc` | Link documentation | Good (via artifact) |

---

## Gap Analysis

### Critical Gaps

#### 1. No Unified `ticket` Command Group

**Current:**
```bash
vibey roadmap start <task-id>
vibey roadmap complete <sprint-id>
vibey roadmap show <track-id>
```

**UTA Aligned:**
```bash
vibey ticket start <id>
vibey ticket complete <id>
vibey ticket show <id>
```

**Impact:** Users must know entity type for some operations
**Severity:** Medium

#### 2. Missing `criteria` Command Group

**Current:** No direct criteria management
```bash
# Must edit YAML directly or use standards
vibey roadmap override-standard
```

**UTA Aligned:**
```bash
vibey criteria list <ticket-id>
vibey criteria add <ticket-id> --type file-exists --path "docs/README.md"
vibey criteria check <ticket-id>
```

**Impact:** Criteria system not first-class in CLI
**Severity:** High

#### 3. Mixed Command Grouping

**Current:** Everything under `roadmap`
```bash
vibey roadmap db rebuild         # Infrastructure
vibey roadmap validate-fast      # Validation
vibey roadmap sync-commits       # Git integration
vibey roadmap start <task>       # Ticket operation
```

**UTA Aligned:**
```bash
vibey db rebuild                 # Infrastructure
vibey validate roadmap           # Validation
vibey git sync-commits           # Git integration
vibey ticket start <id>          # Ticket operation
```

**Impact:** Cognitive load, discovery issues
**Severity:** Low

### Semantic/Storage Leaks

| Command | Leak Type | Details |
|---------|-----------|---------|
| `show --format yaml` | Storage leak | Exposes YAML format |
| `edit file` | Storage leak | Directly edits files |
| `db rebuild` | Storage leak | Exposes database |
| `extract-embedded` | Migration artifact | Legacy structure |
| `migrate-format` | Migration artifact | v1→v2 migration |

### Missing Unified Ticket Commands

| Missing Command | UTA Concept | Priority |
|-----------------|-------------|----------|
| `ticket list` | Query all tickets | High |
| `ticket search` | Full-text search | Medium |
| `ticket tree` | Hierarchy view | Medium |
| `criteria *` | Criterion management | High |
| `artifact verify` | Artifact verification | Low |

---

## CLI to UTA Mapping Table

| CLI Command | Targets | UTA Layer | Notes |
|-------------|---------|-----------|-------|
| **Lifecycle** |
| `roadmap start` | sprint, task | Layer 1 (Ticket) | Status transition |
| `roadmap complete` | track, sprint, task | Layer 1 (Ticket) | Status transition |
| `roadmap revert` | track, sprint, task | Layer 1 (Ticket) | Status transition |
| **Query** |
| `roadmap show` | all | Layer 2 (Hierarchical) | Traverses hierarchy |
| `roadmap status` | roadmap | Layer 3 (Domain) | Aggregates progress |
| `roadmap list-docs` | all | Layer 0 (Completable) | Via artifacts |
| **Creation** |
| `roadmap create-track` | track | Layer 3 (TrackTicket) | Type-specific |
| `roadmap create-sprint` | sprint | Layer 3 (SprintTicket) | Type-specific |
| `roadmap create-task` | task | Layer 3 (TaskTicket) | Type-specific |
| **Infrastructure** |
| `roadmap db *` | database | Storage Layer | **Leak** |
| `roadmap validate-*` | validation | Meta | Tooling |
| `roadmap sync` | sync | Storage Layer | **Leak** |

---

## Entry Point Recommendation

### Current Entry Point

```
vibey
├── roadmap (57 commands)    # Mixed concerns
├── artifact (5 commands)    # Artifact management
├── audit (3 commands)       # Analysis
├── ...
```

### Recommended Entry Point

```
vibey
├── ticket (unified)         # All ticket operations
│   ├── list
│   ├── show <id>
│   ├── start <id>
│   ├── complete <id>
│   ├── create --type <type>
│   └── search <query>
│
├── criteria                 # Criterion management
│   ├── list <ticket-id>
│   ├── add <ticket-id>
│   ├── check <ticket-id>
│   └── remove <ticket-id>
│
├── artifact                 # Artifact management (existing)
│   ├── create
│   ├── list
│   └── link
│
├── db                       # Infrastructure (promote from roadmap)
│   ├── status
│   ├── rebuild
│   └── validate
│
├── roadmap                  # Legacy/alias (deprecation path)
│   └── [backward compat]
│
└── [other groups unchanged]
```

---

## Implementation Priority

| Gap | Priority | Effort | Value |
|-----|----------|--------|-------|
| Add `ticket` command group | High | Medium | Unifies mental model |
| Add `criteria` command group | High | High | First-class criteria |
| Extract `db` commands | Low | Low | Cleaner structure |
| Add `ticket list` | Medium | Low | Common operation |
| Add `ticket search` | Medium | Medium | Discovery |
| Deprecate mixed commands | Low | Low | Long-term cleanup |

---

## Success Criteria Validation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| All CLI commands mapped | ✅ Complete | Tables above |
| Gaps identified | ✅ Complete | 3 critical gaps |
| Entry point recommendation | ✅ Complete | New structure proposed |
| Architecture alignment | ✅ Complete | UTA layers mapped |

---

## References

- Sprint 2 Task 1: SEMANTIC_LAYER_SPEC.md
- Unified Ticket Architecture: `vibey/roadmap/models/ticket/__init__.py`
- CLI Reference: `docs/reference/CLI_REFERENCE.md`
- Plan File: `curried-tinkering-pancake.md` (Unified Decorator Architecture)
