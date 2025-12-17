# Sprint 3: User Journey Documentation

## Overview
- **Track:** Documentation Quality
- **Sprint ID:** 01KCMTKY772B0Y6N5ANXZP1CZH
- **Tasks:** 17
- **Focus:** Comprehensive user-facing documentation with action-oriented walkthroughs and full command coverage

## Success Criteria
- [ ] Action-oriented walkthrough structure designed and implemented
- [ ] Persona journeys consolidated into action walkthroughs
- [ ] 100% CLI/MCP command coverage in walkthroughs
- [ ] User-facing architecture overview created
- [ ] All code examples tested and verified
- [ ] Historical docs archived

---

## Task 1: Design Action-Oriented Walkthrough Structure
**ID:** `01KCMKQ50HF978S9140MT3X24H`
**Priority:** High | **Complexity:** Medium | **Type:** Documentation

### Problem
Current persona-based journeys (new user, developer, lead) have redundant content and don't match how users actually search for help.

### Proposed New Structure
```
docs/walkthroughs/
├── GETTING_STARTED.md           # First 30 minutes
├── DAILY_WORKFLOW.md            # Task management cycle
├── ROADMAP_MANAGEMENT.md        # Creating/managing tracks, sprints, tasks
├── DEPLOYMENT.md                # Platform deployment workflows
├── DATABASE_OPERATIONS.md       # DB maintenance and troubleshooting
├── REPORTING_AND_STATUS.md      # Status checks, progress reports
├── EXTENDING_VIBEY.md           # Plugins, adapters, MCP tools
└── TROUBLESHOOTING.md           # Common issues and solutions
```

### Implementation Steps
1. Analyze current documentation:
   ```bash
   ls -la docs/journeys/
   ls -la docs/walkthroughs/
   ```

2. Create mapping from personas to actions:
   | Persona | Primary Actions |
   |---------|-----------------|
   | New User | Getting Started, Daily Workflow |
   | Active Developer | Daily Workflow, Roadmap Management |
   | Project Lead | Reporting, Roadmap Management |
   | Contributor | Extending Vibey, Database Operations |
   | Plugin Developer | Extending Vibey |

3. Create `docs/walkthroughs/STRUCTURE.md` documenting the new organization

4. Plan consolidation (identify what moves where)

### Deliverables
- [ ] STRUCTURE.md documenting new walkthrough organization
- [ ] Mapping table: old docs → new structure
- [ ] List of docs to archive after consolidation

### Acceptance Criteria
- [ ] New structure designed and documented
- [ ] All existing content has a destination in new structure
- [ ] No content loss during consolidation

---

## Task 2: Audit Docs for Architectural Concept Coverage
**ID:** `01KCMM5W5GD14X10YBJJ0VXKQJ`
**Priority:** High | **Complexity:** Medium | **Type:** Documentation

### Problem
User docs don't explain core architectural concepts, leaving users confused about WHY things work.

### Concepts to Audit
1. **Unified Ticket Architecture**
   - Tracks → Sprints → Tasks hierarchy
   - Status transitions
   - Progress computation

2. **Requirements & Criteria System**
   - What are requirements?
   - How criteria are evaluated
   - Completable items

3. **Artifacts & Deliverables**
   - Artifact types
   - Deliverable tracking

4. **Activity Logging**
   - What gets logged
   - Audit trail usage

5. **YAML + SQLite Dual Storage**
   - Why both?
   - When to use each

### Implementation Steps
1. Read internal architecture docs:
   ```bash
   cat docs/architecture/adr/*.md
   ls .vibey/roadmap/context/tracks/*/architecture/
   ```

2. Search user docs for each concept:
   ```bash
   grep -ri "unified ticket\|hierarchy\|track.*sprint.*task" docs/
   grep -ri "requirement\|criteria\|completable" docs/
   ```

3. Create coverage matrix:
   ```markdown
   | Concept | CLI_REF | MCP_REF | Walkthroughs | Architecture |
   |---------|---------|---------|--------------|--------------|
   | Unified Ticket | No | No | Partial | Not exists |
   | Requirements | No | No | No | Not exists |
   ```

4. Document gaps for Task 4 (Create Architecture Overview)

### Deliverables
- [ ] ARCHITECTURE_COVERAGE_AUDIT.md with findings
- [ ] Gap list for architecture overview

### Acceptance Criteria
- [ ] All 5 concept areas audited
- [ ] Coverage matrix completed
- [ ] Gaps clearly identified

---

## Task 3: Audit User Journeys for CLI/MCP Coverage Gaps
**ID:** `01KCMKPY8CVHTZ1SCNQG38YN7T`
**Priority:** High | **Complexity:** Medium | **Type:** Documentation

### Problem
User journeys may not cover all 169 CLI commands and MCP tools.

### Implementation Steps
1. Extract all commands from references:
   ```bash
   grep "^## " docs/reference/CLI_REFERENCE.md | wc -l
   grep "^## " docs/reference/MCP_REFERENCE.md | wc -l
   ```

2. Search journeys/walkthroughs for each command:
   ```bash
   for cmd in $(grep "^## " docs/reference/CLI_REFERENCE.md | sed 's/## //'); do
     count=$(grep -r "$cmd" docs/journeys docs/walkthroughs | wc -l)
     if [ $count -eq 0 ]; then
       echo "MISSING: $cmd"
     fi
   done
   ```

3. Create coverage report:
   ```markdown
   ## CLI Command Coverage

   ### Covered (X/169)
   - vibey roadmap status (GETTING_STARTED.md, DAILY_WORKFLOW.md)
   - vibey roadmap start (DAILY_WORKFLOW.md)
   ...

   ### Missing (Y/169)
   - vibey deploy audit
   - vibey roadmap db vacuum
   ...
   ```

### Deliverables
- [ ] CLI_MCP_COVERAGE_AUDIT.md
- [ ] List of commands to add to walkthroughs

### Acceptance Criteria
- [ ] All 169 CLI commands audited
- [ ] All MCP tools audited
- [ ] Missing commands documented with recommended walkthrough placement

---

## Task 4: Create User-Facing Architecture Overview
**ID:** `01KCMM6939HN97046DKG1TAKC3`
**Priority:** High | **Complexity:** Complex | **Type:** Documentation

### Problem
No user-friendly explanation of Vibey's architecture exists.

### File to Create
`docs/architecture/ARCHITECTURE_OVERVIEW.md`

### Content Structure
```markdown
# Vibey Architecture Overview

## Introduction
What is Vibey and what problems does it solve?

## Core Concepts

### The Unified Ticket Model
[Diagram: Track → Sprint → Task hierarchy]

- **Tracks**: Major project themes (e.g., "Platform Compatibility")
- **Sprints**: Time-boxed work periods within a track
- **Tasks**: Individual work items with clear deliverables

### Status and Progress
How status flows through the hierarchy:
- Task statuses: not_started → in_progress → completed
- Sprint completion: computed from task progress
- Track completion: computed from sprint progress

### Requirements and Criteria
[Explanation of how requirements work]

### Dual Storage: YAML + SQLite
Why we use both and when to use each:
- YAML: Source of truth, human-readable, git-friendly
- SQLite: Fast queries, computed views, local cache

## Architecture Diagrams

### Data Flow
[Diagram showing CLI → Operations → YAML/SQLite]

### Platform Integration
[Diagram showing adapters and MCP]

## Further Reading
- [ADR-0001: ULID Identifiers](adr/0001-ulid-identifiers.md)
- [ADR-0002: Flat Directory Structure](adr/0002-flat-directory-structure.md)
- [ADR-0003: Dual Storage](adr/0003-dual-storage-sqlite-yaml.md)
```

### Implementation Steps
1. Read all ADRs and internal architecture docs
2. Identify key concepts users need to understand
3. Create diagrams (can be ASCII or reference to draw.io/mermaid)
4. Write user-friendly explanations
5. Link to detailed ADRs for deeper reading

### Acceptance Criteria
- [ ] All core concepts explained in user-friendly terms
- [ ] Diagrams illustrate key relationships
- [ ] Links to detailed ADRs included
- [ ] No jargon without explanation

---

## Task 5: Consolidate Persona Journeys into Action Walkthroughs
**ID:** `01KCMKQFF8ZJARPKDJNM3D7M9P`
**Priority:** High | **Complexity:** Complex | **Type:** Documentation

### Problem
Persona journeys and walkthroughs have redundant content organized differently.

### Files to Consolidate
**Source (persona-based):**
- `docs/journeys/JOURNEY_NEW_USER.md`
- `docs/journeys/JOURNEY_ACTIVE_DEVELOPER.md`
- `docs/journeys/JOURNEY_PROJECT_LEAD.md`
- `docs/journeys/JOURNEY_CONTRIBUTOR.md`
- `docs/walkthroughs/WALKTHROUGH_NEW_USER.md`
- `docs/walkthroughs/WALKTHROUGH_ACTIVE_DEVELOPER.md`
- etc.

**Target (action-based):**
- `docs/walkthroughs/GETTING_STARTED.md`
- `docs/walkthroughs/DAILY_WORKFLOW.md`
- `docs/walkthroughs/ROADMAP_MANAGEMENT.md`
- etc.

### Implementation Steps
1. Create empty target files with structure

2. For each source file:
   - Identify content sections
   - Map to appropriate target file
   - Copy and adapt content
   - Track what was migrated

3. Add redirects/notes to old files:
   ```markdown
   > **Note:** This document has been consolidated into action-oriented walkthroughs.
   > See [GETTING_STARTED.md](../walkthroughs/GETTING_STARTED.md) and
   > [DAILY_WORKFLOW.md](../walkthroughs/DAILY_WORKFLOW.md).
   ```

4. Archive old files after verification

### Migration Mapping
| Source Section | Target File |
|----------------|-------------|
| New User: First 30 minutes | GETTING_STARTED.md |
| Active Developer: Daily cycle | DAILY_WORKFLOW.md |
| Project Lead: Status reports | REPORTING_AND_STATUS.md |
| Contributor: Setup | GETTING_STARTED.md |
| Contributor: Contributing code | EXTENDING_VIBEY.md |

### Acceptance Criteria
- [ ] All persona content migrated to action walkthroughs
- [ ] No content lost during migration
- [ ] Old files marked as deprecated with redirects
- [ ] New walkthroughs are comprehensive and well-organized

---

## Task 6: Ensure 100% Command Coverage in Action Walkthroughs
**ID:** `01KCMKSGTDWS2WJQPGMQJT2Y34`
**Priority:** High | **Complexity:** Complex | **Type:** Documentation

### Problem
Users can't find examples of all commands in context.

### Implementation Steps
1. Use coverage audit from Task 3

2. For each missing command, determine best walkthrough:
   | Command Group | Walkthrough |
   |---------------|-------------|
   | roadmap status/show/list | DAILY_WORKFLOW.md |
   | roadmap start/complete | DAILY_WORKFLOW.md |
   | roadmap create/update | ROADMAP_MANAGEMENT.md |
   | deploy * | DEPLOYMENT.md |
   | db * | DATABASE_OPERATIONS.md |
   | docs * | EXTENDING_VIBEY.md |

3. Add contextual examples for each command

4. Create coverage matrix document

### Deliverable Format
```markdown
## Coverage Matrix

| Command | Walkthrough | Section | Status |
|---------|-------------|---------|--------|
| vibey roadmap status | DAILY_WORKFLOW.md | Checking Progress | ✅ |
| vibey deploy audit | DEPLOYMENT.md | Pre-deploy Checks | ✅ |
```

### Acceptance Criteria
- [ ] 100% of 169 CLI commands covered
- [ ] 100% of MCP tools covered
- [ ] Coverage matrix document created
- [ ] Each command shown in relevant context

---

## Task 7: Verify and Update JOURNEY_CONTRIBUTOR.md
**ID:** `01KCMGY56AY2XMMS8BNAAJBE3A`
**Priority:** High | **Complexity:** Medium | **Type:** Documentation

### Implementation Steps
1. Verify file exists:
   ```bash
   ls docs/journeys/JOURNEY_CONTRIBUTOR.md
   ```

2. Review content accuracy:
   - Development setup instructions
   - Testing instructions
   - PR process
   - Code standards

3. Update with current information from:
   - `CONTRIBUTING.md`
   - `docs/development/SETUP.md`
   - `docs/development/CODING_STANDARDS.md`

4. Ensure consistency with consolidated walkthroughs

### Acceptance Criteria
- [ ] File exists and is complete
- [ ] Setup instructions match SETUP.md
- [ ] PR process documented
- [ ] Links to relevant standards docs

---

## Tasks 8-17: Remaining Tasks

### Task 8: Add MCP Integration Sections to Walkthroughs
**ID:** `01KCMGYMMY1HM641G8EA4Y2DA1`
Add parallel MCP workflow sections showing AI assistant usage alongside CLI examples.

### Task 9: Add Option Defaults to CLI Reference
**ID:** `01KCMGY918F6M2ZZFWQCDSCKY9`
Extract and display default values from Click decorators in CLI reference.

### Task 10: Create JOURNEY_PLUGIN_DEVELOPER.md
**ID:** `01KCMJPWGJPSEYZ5KFHYCY2WXW`
Create comprehensive guide for extending Vibey with plugins, adapters, MCP tools.

### Task 11: Document CLI Error Responses
**ID:** `01KCMGYCX56RWNQXPH01ZFMPS5`
Add error documentation with common errors and solutions per command group.

### Task 12: Integrate Architectural Concepts into Action Walkthroughs
**ID:** `01KCMM7YJZ35TW9YDZK0HN6CMD`
Add "Why" explanations referencing architecture where relevant.

### Task 13: Integrate Architectural Concepts into Reference Guides
**ID:** `01KCMM6GGCPFZCY9MTF8RPXMK9`
Update CLI/MCP references with architectural context.

### Task 14: Test and Verify All Code Examples
**ID:** `01KCMJSMEZ6SQ7D3B7P3Z1VQDD`
Run all code examples in documentation, fix any that fail.

### Task 15: Update Expected Output in Walkthroughs
**ID:** `01KCMGYGS6S0H42C36KRPJ5G42`
Regenerate output examples from live system.

### Task 16: Add Documentation to vibey/content/ Module
**ID:** `01KCMK2KMF64SKKNYYJWM8AY0T`
Add module docstrings and usage examples.

### Task 17: Archive Historical Documentation Files
**ID:** `01KCMJQBNWC9ZYM09GHX21CW9A`
Move 23 historical files to docs/archived/.

---

## Sprint Completion Checklist
- [ ] All 17 tasks completed
- [ ] New walkthrough structure implemented
- [ ] 100% command coverage achieved
- [ ] Architecture overview created
- [ ] All code examples verified
- [ ] Historical docs archived
- [ ] All changes committed
