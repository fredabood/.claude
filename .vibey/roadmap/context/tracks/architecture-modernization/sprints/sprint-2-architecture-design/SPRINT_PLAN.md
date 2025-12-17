# Sprint 2: Architecture Design

## Overview
- **Track:** Architecture Modernization
- **Sprint ID:** 01KCMTXH8QFZ64GD4CK7TSDY06
- **Tasks:** 6
- **Focus:** Design decoupled architecture, semantic layer boundaries, and planned status criterion

## Success Criteria
- [ ] Semantic layer boundaries clearly defined
- [ ] Decoupled directory structure designed
- [ ] CLI refactor plan created
- [ ] Planned status criterion specified
- [ ] Go/no-go decision documented

---

## Task 1: Define Semantic Layer Boundaries and Responsibilities
**ID:** `01KCMNY4BENEZBVT9NR20PFY03`
**Priority:** High | **Complexity:** Medium | **Type:** Development

### Problem
Unclear what the "semantic layer" IS and IS NOT responsible for.

### Implementation Steps
1. Define what semantic layer IS:
   ```markdown
   # Semantic Layer Responsibilities

   ## IS responsible for:
   - User-facing concepts (tracks, sprints, tasks)
   - Model-to-human communication vocabulary
   - Source of truth interface (CRUD operations)
   - Query semantics (status, progress, dependencies)
   - Business rules (state transitions, validations)
   ```

2. Define what semantic layer IS NOT:
   ```markdown
   ## IS NOT responsible for:
   - File/directory organization
   - Storage format (YAML vs JSON vs SQLite)
   - Internal configuration
   - Path construction
   - Caching strategy
   ```

3. Create boundary diagram:
   ```
   ┌──────────────────────────────────────────┐
   │           USER INTERFACE LAYER           │
   │     (CLI, MCP, Web - speaks semantic)    │
   └────────────────────┬─────────────────────┘
                        │
   ┌────────────────────▼─────────────────────┐
   │           SEMANTIC LAYER                 │
   │  (Tracks, Sprints, Tasks, Status, etc.)  │
   │  - Domain models                         │
   │  - Business rules                        │
   │  - State management                      │
   └────────────────────┬─────────────────────┘
                        │
   ┌────────────────────▼─────────────────────┐
   │           STORAGE LAYER                  │
   │  (Implementation detail - hidden)        │
   │  - YAML files, SQLite, file paths        │
   └──────────────────────────────────────────┘
   ```

### Deliverables
- `SEMANTIC_LAYER_SPEC.md` - Layer definition document
- Boundary diagram
- Responsibility matrix

### Acceptance Criteria
- [ ] Clear IS/IS NOT definitions
- [ ] Diagram showing layers
- [ ] No ambiguity about responsibilities

---

## Task 2: Design Decoupled Directory Structure
**ID:** `01KCMNXGP9X7P577QCKHF340W5`
**Priority:** High | **Complexity:** Complex | **Type:** Development

### Problem
Current directory structure (tracks/, sprints/, tasks/) mirrors semantic concepts, creating tight coupling.

### Design Principles
1. Directory structure = storage concern only
2. Semantic layer should not dictate file organization
3. Storage should be swappable without semantic changes

### Implementation Steps
1. Design options:

   **Option A: Generic storage directory**
   ```
   .vibey/
   ├── data/
   │   ├── entities/          # All YAML files
   │   └── cache/             # SQLite database
   └── config/
   ```

   **Option B: Type-based but abstract**
   ```
   .vibey/
   ├── store/
   │   ├── type-a/            # Tracks (but name is abstract)
   │   ├── type-b/            # Sprints
   │   └── type-c/            # Tasks
   └── meta/
   ```

   **Option C: Single flat directory**
   ```
   .vibey/
   └── objects/
       ├── 01KC2D0JK9JK...yaml  # Entity type in file
       └── 01KC2D0JKVT8...yaml
   ```

2. Evaluate options:
   ```markdown
   | Criteria              | Option A | Option B | Option C |
   |-----------------------|----------|----------|----------|
   | Decoupling            | High     | Medium   | High     |
   | Human readability     | Low      | Medium   | Low      |
   | Migration complexity  | High     | Medium   | High     |
   | Git friendliness      | Medium   | High     | Medium   |
   ```

3. Recommend approach with rationale

### Deliverables
- `DIRECTORY_DESIGN.md` - Design document
- Option comparison matrix
- Recommended approach with migration plan

### Acceptance Criteria
- [ ] Multiple options evaluated
- [ ] Tradeoffs documented
- [ ] Clear recommendation made

---

## Task 3: Analyze CLI Entry Point vs Unified Ticket Architecture Layers
**ID:** `01KCMMEA6M8VW610NS158G7F1H`
**Priority:** High | **Complexity:** Complex | **Type:** Development

### Problem
CLI commands may reference semantic concepts inconsistently. Need to align with unified ticket architecture.

### Implementation Steps
1. Map current CLI to unified ticket concepts:
   ```markdown
   | CLI Command Group | Current Concept | Unified Ticket Equivalent |
   |-------------------|-----------------|---------------------------|
   | roadmap           | Roadmap         | Root completable          |
   | track             | Track           | Parent ticket             |
   | sprint            | Sprint          | Child ticket (time-boxed) |
   | task              | Task            | Leaf ticket               |
   ```

2. Identify unified ticket architecture layers:
   ```
   TICKETS (work units)
   ├── Completables (things that can be done)
   ├── Criteria (conditions for completion)
   └── Artifacts (deliverables, evidence)
   ```

3. Analyze CLI entry point:
   - What layer does each command target?
   - Are concepts mixed inappropriately?
   - Where are semantic/storage leaks?

4. Document gaps:
   ```markdown
   ## CLI/Architecture Gaps

   1. `roadmap show <id>` - Mixes semantic query with path display
   2. `task create` - Requires path knowledge (storage leak)
   3. Missing: `criteria` commands for completion conditions
   ```

### Deliverables
- `CLI_ARCHITECTURE_ANALYSIS.md`
- Concept mapping table
- Gap inventory

### Acceptance Criteria
- [ ] All CLI commands mapped to architecture
- [ ] Gaps identified
- [ ] Entry point recommendation made

---

## Task 4: Design CLI Refactor for First-Class Semantic Layer
**ID:** `01KCMMEJ1RJJ9JTV98N3SZ88AG`
**Priority:** High | **Complexity:** Complex | **Type:** Development

### Problem
CLI structure should treat semantic layer as first-class, not expose storage details.

### Implementation Steps
1. Design new command hierarchy:
   ```bash
   vibey ticket list          # List all tickets (tracks/sprints/tasks)
   vibey ticket show <id>     # Show ticket details
   vibey ticket start <id>    # Start working on ticket
   vibey ticket complete <id> # Complete ticket

   vibey criteria list <id>   # List completion criteria
   vibey criteria add <id>    # Add criterion

   vibey artifact list <id>   # List artifacts
   vibey artifact add <id>    # Add artifact
   ```

2. Keep backward compatibility aliases:
   ```python
   # Aliases for transition period
   roadmap_group.add_command(ticket_list, name='list')
   track_group.add_command(ticket_show, name='show')
   ```

3. Design migration path:
   ```markdown
   ## Migration Phases

   Phase 1: Add new semantic commands (no breaking changes)
   Phase 2: Deprecation warnings on old commands
   Phase 3: Remove deprecated commands (major version)
   ```

4. Impact on MCP parity:
   - MCP tools should mirror new CLI structure
   - Both should use same semantic vocabulary

### Deliverables
- `CLI_REFACTOR_DESIGN.md`
- New command hierarchy specification
- Migration timeline

### Acceptance Criteria
- [ ] New structure designed
- [ ] Backward compatibility addressed
- [ ] MCP parity maintained

---

## Task 5: Design Planned Status Criterion for Tickets
**ID:** `01KCMNNCSFEY28BZ9XM6X8Y964`
**Priority:** Medium | **Complexity:** Complex | **Type:** Development

### Problem
Need criterion-based calculation for "planned" status, similar to completion status.

### Design
```python
class PlannedStatus(Criterion):
    """
    Ticket is planned when:
    1. YAML file exists (tracked in system)
    2. Database record exists (in query cache)
    3. At least one context file exists (has planning docs)
    4. User has manually approved (explicit sign-off)
    """

    def evaluate(self, ticket: Ticket) -> CriterionResult:
        targets = [
            FileExistsTarget(ticket.yaml_path),
            DatabaseRecordTarget(ticket.id),
            ContextFileExistsTarget(ticket.context_path),
            ManualApprovalTarget(ticket.id),
        ]
        return all(t.evaluate() for t in targets)
```

### Hierarchical Aggregation
```python
def is_planned(ticket: Ticket) -> bool:
    if ticket.is_leaf:
        return evaluate_planned_criterion(ticket)
    else:
        return all(is_planned(child) for child in ticket.children)
```

### Implementation Steps
1. Define PlannedCriterion class
2. Implement target classes:
   - `FileExistsTarget` - Check YAML exists
   - `DatabaseRecordTarget` - Check DB entry
   - `ContextFileExistsTarget` - Check context/ dir
   - `ManualApprovalTarget` - Check approval flag

3. Add planned status to models:
   ```python
   class Ticket(BaseModel):
       # ...existing fields
       planned_approved: bool = False  # Manual approval flag

       @property
       def is_planned(self) -> bool:
           return PlannedCriterion().evaluate(self).passed
   ```

4. Add CLI/MCP commands for planned workflow

### Deliverables
- `PLANNED_STATUS_DESIGN.md`
- Criterion specification
- Target class specifications

### Acceptance Criteria
- [ ] Criterion defined
- [ ] All targets specified
- [ ] Hierarchical aggregation designed

---

## Task 6: Assess Refactor Scope and Migration Path
**ID:** `01KCMNYBX5B7BP79APXR41N0PW`
**Priority:** High | **Complexity:** Medium | **Type:** Development

### Problem
Need to assess full scope before committing to refactor.

### Implementation Steps
1. Quantify scope:
   ```markdown
   ## Refactor Scope Assessment

   Files affected: ~XX
   Lines of code: ~XXXX
   Test updates: ~XX tests
   Documentation updates: XX files
   ```

2. Risk assessment:
   ```markdown
   ## Risks

   | Risk | Likelihood | Impact | Mitigation |
   |------|------------|--------|------------|
   | Data migration failure | Medium | High | Backup + rollback |
   | Breaking changes | High | Medium | Versioning strategy |
   | Performance regression | Low | Medium | Benchmarks |
   ```

3. Migration path:
   ```markdown
   ## Migration Phases

   1. **Preparation** (non-breaking)
      - Add new abstractions
      - Create compatibility layer

   2. **Parallel Run** (transition)
      - Both old and new code paths
      - Validation of equivalence

   3. **Cutover** (breaking)
      - Remove old code paths
      - Update all consumers
   ```

4. Go/no-go decision criteria:
   - Risk acceptable?
   - Resources available?
   - Timeline reasonable?
   - Value justifies effort?

### Deliverables
- `REFACTOR_ASSESSMENT.md`
- Go/no-go recommendation
- Detailed migration plan if go

### Acceptance Criteria
- [ ] Scope quantified
- [ ] Risks documented
- [ ] Clear recommendation made

---

## Sprint Completion Checklist
- [ ] Semantic layer boundaries defined
- [ ] Directory structure designed
- [ ] CLI architecture analyzed
- [ ] CLI refactor designed
- [ ] Planned status criterion specified
- [ ] Go/no-go decision documented
